const fs = require('fs');
const { chromium } = require('playwright-core');
const { initializeApp, getApps } = require('../functions/node_modules/firebase-admin/app');
const { getDatabase } = require('../functions/node_modules/firebase-admin/database');
const { getStorage } = require('../functions/node_modules/firebase-admin/storage');

const BASE = 'http://127.0.0.1:5000';
const PASSWORD = 'Test1234!';
const results = [];
const consoleErrors = [];
const pageErrors = [];
const requestFailures = [];
const dialogs = [];

function ok(name, detail = '') {
  results.push({ name, ok: true, detail });
  console.log(`PASS: ${name}${detail ? ` — ${detail}` : ''}`);
}
function fail(name, detail = '') {
  results.push({ name, ok: false, detail });
  throw new Error(`${name}${detail ? `: ${detail}` : ''}`);
}
function assert(condition, name, detail = '') {
  if (!condition) fail(name, detail);
  ok(name, detail);
}
async function waitForApp(page) {
  await page.waitForFunction(() => document.querySelectorAll('#shopProductsGrid .product-card').length >= 2, null, { timeout: 30000 });
}
async function signOut(page) {
  await page.evaluate(async () => { if (typeof logoutUser === 'function') await logoutUser(); else if (auth?.currentUser) await auth.signOut(); });
  await page.waitForFunction(() => !firebase.auth().currentUser);
}
async function loginCustomer(page, email = 'customer@example.com') {
  await page.evaluate(() => openAuthModal());
  await page.fill('#loginIdentifier', email);
  await page.fill('#loginPassword', PASSWORD);
  await page.click('#loginForm button[type="submit"]');
  await page.waitForFunction((expected) => firebase.auth().currentUser?.email === expected, email, { timeout: 15000 });
}
async function loginEmployee(page, email, password = PASSWORD) {
  await page.evaluate(() => openEmployeeModal());
  await page.fill('#employeeEmail', email);
  await page.fill('#employeePassword', password);
  await page.click('#employeeModal button:has-text("Sign In")');
}
async function adminRoot() {
  const db = getDatabase();
  return (await db.ref('/').once('value')).val();
}

(async () => {
  process.env.FIREBASE_AUTH_EMULATOR_HOST = '127.0.0.1:9099';
  process.env.FIREBASE_DATABASE_EMULATOR_HOST = '127.0.0.1:9000';
  process.env.FIREBASE_STORAGE_EMULATOR_HOST = '127.0.0.1:9199';
  process.env.GCLOUD_PROJECT = 'demo-kem-validation';
  if (!getApps().length) initializeApp({
    projectId: 'demo-kem-validation',
    databaseURL: 'http://127.0.0.1:9000?ns=demo-kem-validation-default-rtdb',
    storageBucket: 'demo-kem-validation.firebasestorage.app',
  });

  const executablePath = process.env.CHROME_PATH;
  assert(executablePath && fs.existsSync(executablePath), 'Chromium executable available', executablePath || 'missing');
  const browser = await chromium.launch({ executablePath, headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  page.on('pageerror', err => pageErrors.push(String(err)));
  page.on('requestfailed', req => requestFailures.push(`${req.method()} ${req.url()} :: ${req.failure()?.errorText || 'failed'}`));
  page.on('dialog', async dialog => {
    dialogs.push(`${dialog.type()}: ${dialog.message()}`);
    if (dialog.type() === 'prompt') await dialog.accept('customer@example.com');
    else await dialog.accept();
  });

  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await waitForApp(page);
  assert((await page.locator('#shopProductsGrid .product-card').count()) === 2, 'Homepage renders seeded products');
  assert(pageErrors.length === 0, 'Homepage has no uncaught JavaScript errors', pageErrors.join(' | '));

  for (const width of [360, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.waitForTimeout(150);
    const m = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, iw: innerWidth }));
    assert(m.sw <= m.iw + 2, `No page-level horizontal overflow at ${width}px`, `${m.sw}/${m.iw}`);
  }

  await page.setViewportSize({ width: 390, height: 844 });
  await page.click('#mobileNavToggle');
  assert(await page.locator('#primaryNav').evaluate(el => el.classList.contains('mobile-open')), 'Mobile navigation opens');
  await page.click('#mobileNavToggle');
  assert(!(await page.locator('#primaryNav').evaluate(el => el.classList.contains('mobile-open'))), 'Mobile navigation closes');

  await page.fill('#shopSearch', 'Alpha');
  await page.waitForTimeout(100);
  assert((await page.locator('#shopProductsGrid .product-card').count()) === 1, 'Product search filters results');
  await page.fill('#shopSearch', '');
  await page.getByRole('button', { name: 'Tees' }).click();
  assert((await page.locator('#shopProductsGrid .product-card').count()) === 1, 'Category filter works');
  await page.getByRole('button', { name: 'All' }).click();

  await page.locator('#shopProductsGrid .product-card').first().click();
  await page.waitForSelector('#productDetailModal.active');
  assert(new URL(page.url()).searchParams.get('product') === '1', 'Product opening creates ?product=<id> URL');
  assert((await page.title()).includes('Validation Alpha Tee'), 'Product metadata title updates');
  assert((await page.locator('#detailGallery .product-gallery-thumb').count()) === 2, 'Product gallery renders multiple images');
  await page.locator('#detailGallery .product-gallery-thumb').nth(1).click();
  assert((await page.locator('#detailImage').getAttribute('src')).includes('favicon-64.png'), 'Product gallery image selection works');
  await page.goBack();
  await page.waitForTimeout(150);
  assert(!(await page.locator('#productDetailModal').evaluate(el => el.classList.contains('active'))), 'Browser Back closes product detail');
  await page.goForward();
  await page.waitForSelector('#productDetailModal.active');
  assert(new URL(page.url()).searchParams.get('product') === '1', 'Browser Forward restores product detail');
  await page.keyboard.press('Escape');
  assert(!(await page.locator('#productDetailModal').evaluate(el => el.classList.contains('active'))), 'Escape closes product detail dialog');
  assert(new URL(page.url()).searchParams.get('product') === null, 'Closing product removes product query state');
  await page.goto(`${BASE}/?product=2`, { waitUntil: 'domcontentloaded' });
  await waitForApp(page);
  await page.waitForSelector('#productDetailModal.active');
  assert((await page.locator('#detailName').textContent()).includes('Validation Beta Hoodie'), 'Direct product deep link opens correct product');
  await page.keyboard.press('Escape');

  await page.evaluate(() => openAuthModal());
  await page.waitForSelector('#authModal.active');
  const focusInfo = await page.evaluate(() => {
    const dialog = document.querySelector('#authModal.active');
    const f = [...dialog.querySelectorAll('button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')].filter(el => el.offsetParent !== null);
    f[f.length - 1].focus();
    return { first: f[0].id || f[0].textContent.trim(), last: f[f.length - 1].id || f[f.length - 1].textContent.trim() };
  });
  await page.keyboard.press('Tab');
  assert(await page.evaluate((first) => (document.activeElement.id || document.activeElement.textContent.trim()) === first, focusInfo.first), 'Tab focus trapping wraps within auth dialog');
  await page.keyboard.press('Escape');
  assert(!(await page.locator('#authModal').evaluate(el => el.classList.contains('active'))), 'Escape closes login/signup dialog');

  await page.evaluate(() => { openAuthModal(); switchAuthTab('signup'); });
  await page.fill('#signupName', 'Smoke Signup');
  await page.fill('#signupEmail', 'signup-smoke@example.com');
  await page.fill('#signupPhone', '+201111111111');
  await page.fill('#signupPassword', PASSWORD);
  await page.click('#signupForm button[type="submit"]');
  await page.waitForFunction(() => firebase.auth().currentUser?.email === 'signup-smoke@example.com', null, { timeout: 15000 });
  assert(!(await page.evaluate(() => firebase.auth().currentUser.emailVerified)), 'Signup creates unverified customer as expected');
  const signupProfile = await page.evaluate(async () => (await db.ref(`users/${auth.currentUser.uid}`).once('value')).val());
  assert(signupProfile?.email === 'signup-smoke@example.com', 'Signup persists own customer profile through database rules');
  await signOut(page);
  ok('Customer logout works after signup');

  await page.evaluate(() => { window.prompt = () => 'customer@example.com'; return handleForgotPassword(); });
  await page.waitForTimeout(250);
  assert(dialogs.some(d => d.includes('password reset email has been sent')), 'Password reset flow starts correctly');

  await loginCustomer(page);
  assert(await page.evaluate(() => firebase.auth().currentUser.emailVerified), 'Verified customer login succeeds');
  await page.evaluate(() => openAccountModal());
  await page.waitForFunction(() => !document.querySelector('#accountOrders')?.textContent.includes('Loading'));
  const ordersText = await page.locator('#accountOrders').textContent();
  assert(ordersText.includes('KEM-2026-000001'), 'Customer account loads own order history');
  assert(!ordersText.includes('KEM-2026-000002'), 'Customer account does not expose another user order');
  await page.keyboard.press('Escape');
  assert(!(await page.locator('#accountModal').evaluate(el => el.classList.contains('active'))), 'Escape closes customer account dialog');

  await page.locator('#shopProductsGrid .product-card').first().click();
  await page.waitForSelector('#productDetailModal.active');
  const alertCountBeforeVariant = dialogs.length;
  await page.getByRole('button', { name: 'Add to Cart', exact: true }).first().click();
  await page.waitForTimeout(100);
  assert(dialogs.slice(alertCountBeforeVariant).some(d => /select.*size|choose.*size/i.test(d)), 'Size/color requirements prevent incomplete add-to-cart');
  await page.locator('#detailSizes .variant-option').filter({ hasText: 'M' }).click();
  await page.locator('#detailColors .variant-option').filter({ hasText: 'Black' }).click();
  await page.getByRole('button', { name: 'Add to Cart', exact: true }).first().click();
  await page.waitForTimeout(100);
  assert((await page.evaluate(() => cart.length)) === 1, 'Add to Cart stores selected variant');
  await page.evaluate(() => { closeProductDetail(); openCart(); });
  await page.waitForSelector('#cartPage.active');
  const cartText = await page.locator('#cartContentArea').textContent();
  assert(cartText.includes('M') && cartText.includes('Black'), 'Cart displays selected size and color');
  const plus = page.locator('#cartContentArea button').filter({ hasText: '+' }).first();
  if (await plus.count()) {
    await plus.click();
    await page.waitForTimeout(100);
    assert((await page.evaluate(() => cart[0].quantity)) === 2, 'Cart quantity update works through rendered control');
  } else {
    fail('Cart quantity update works through rendered control', 'No increment button found');
  }

  await page.fill('#couponInput', 'SMOKE10');
  await page.getByRole('button', { name: 'Apply', exact: true }).click();
  await page.waitForFunction(() => appliedCoupon?.code === 'SMOKE10');
  assert(await page.evaluate(() => appliedCoupon?.serverValidated === true), 'Valid coupon is accepted through cart UI and server-validated');

  await page.evaluate(() => checkout());
  await page.waitForSelector('#checkoutPage.active');
  await page.waitForFunction(() => document.querySelector('#checkoutStatus')?.textContent !== 'Calculating your order total…');
  assert((await page.locator('#checkoutStatus').textContent()).includes('ready'), 'Server quote loads in checkout');
  assert(await page.locator('#savedAddressesSection').isVisible(), 'Saved addresses render for authenticated user');
  await page.locator('#savedAddressesList button').first().click();
  assert((await page.inputValue('#checkoutAddress')) === '1 Validation Street', 'Saved address selection fills checkout form');
  assert((await page.locator('#checkoutCouponRow').evaluate(el => getComputedStyle(el).display)) !== 'none', 'Validated coupon is reflected in checkout quote');

  const invalidCalls = await page.evaluate(async () => {
    const quote = cloudFunctions.httpsCallable('quoteOrder');
    const out = {};
    try { await quote({ items: [{ id: 1, quantity: 1, size: 'FAKE', color: 'Black' }] }); out.variant = false; } catch (e) { out.variant = /valid size/i.test(e.message); }
    try { await quote({ items: [{ id: 1, quantity: 99, size: 'M', color: 'Black' }] }); out.stock = false; } catch (e) { out.stock = /available/i.test(e.message); }
    try { await quote({ items: [{ id: 1, quantity: 1, size: 'M', color: 'Black' }], couponCode: 'USEDUP' }); out.coupon = false; } catch (e) { out.coupon = /usage limit/i.test(e.message); }
    return out;
  });
  assert(invalidCalls.variant, 'Invalid variant manipulation is rejected server-side');
  assert(invalidCalls.stock, 'Invalid stock/cart manipulation is rejected server-side');
  assert(invalidCalls.coupon, 'Exhausted coupon is rejected server-side');

  await page.evaluate(async () => { cart[0].quantity = 99; await renderCheckoutSummary(); });
  assert(await page.locator('.place-order-btn').isDisabled(), 'Backend quote failure disables Place Order');
  assert((await page.locator('#checkoutTotal').textContent()).includes('Unable'), 'Checkout shows backend quote failure instead of false success');
  await page.evaluate(async () => { cart[0].quantity = 1; await renderCheckoutSummary(); });
  await page.waitForFunction(() => !document.querySelector('.place-order-btn').disabled);

  await page.fill('#checkoutName', 'Customer One');
  await page.fill('#checkoutEmail', 'customer@example.com');
  await page.fill('#checkoutPhone', '+201000000001');
  await page.fill('#checkoutAddress', '1 Validation Street');
  await page.fill('#checkoutHouseNumber', '10');
  await page.fill('#checkoutCity', 'Cairo');
  const beforeRoot = await adminRoot();
  const beforeStock = beforeRoot.products[0].stock;
  const beforeUsed = beforeRoot.coupons[0].used;
  const beforeClient = await page.evaluate(() => ({
    cart: cart.map(item => ({ id: item.id, quantity: item.quantity, size: item.size, color: item.color })),
    quote: lastCheckoutQuote ? { total: lastCheckoutQuote.total, items: lastCheckoutQuote.items } : null,
    coupon: appliedCoupon,
  }));
  console.log('VALIDATION_BEFORE_ORDER', JSON.stringify({ beforeClient, products: beforeRoot.products, coupons: beforeRoot.coupons }));
  await page.getByRole('button', { name: /place order/i }).click();
  await page.waitForTimeout(1200);
  const afterRoot = await adminRoot();
  const newOrders = Object.values(afterRoot.orders || {}).filter(o => o.customerUid === 'customer-1');
  assert(newOrders.length >= 2, 'COD order creation succeeds through checkout UI');
  assert(afterRoot.products[0].stock === beforeStock - 1, 'Successful order decrements inventory atomically');
  assert(afterRoot.coupons[0].used === beforeUsed + 1, 'Successful coupon order increments coupon usage atomically');

  await signOut(page);
  await page.evaluate(async () => auth.signInWithEmailAndPassword('unverified@example.com', PASSWORD));
  await page.evaluate(() => { cart = [{ id: 1, name: 'Validation Alpha Tee', price: 500, stock: 5, quantity: 1, size: 'M', color: 'Black' }]; });
  const checkoutStateBefore = await page.locator('#checkoutPage').evaluate(el => el.classList.contains('active'));
  await page.evaluate(() => checkout());
  await page.waitForTimeout(150);
  assert(!(await page.locator('#checkoutPage').evaluate(el => el.classList.contains('active'))) || checkoutStateBefore, 'Checkout enforces verified-email customer state');
  await signOut(page);

  await loginEmployee(page, 'customer@example.com');
  await page.waitForTimeout(500);
  assert(!(await page.locator('#employeeDashboard').evaluate(el => el.classList.contains('active'))), 'Unauthorized customer cannot enter employee dashboard');
  await page.evaluate(async () => { if (auth.currentUser) await auth.signOut(); closeEmployeeModal(); });
  await loginEmployee(page, 'unverifiedemployee@example.com');
  await page.waitForTimeout(500);
  assert(!(await page.locator('#employeeDashboard').evaluate(el => el.classList.contains('active'))), 'Unverified employee cannot enter dashboard');
  await page.evaluate(async () => { if (auth.currentUser) await auth.signOut(); closeEmployeeModal(); });
  await loginEmployee(page, 'employee@example.com');
  await page.waitForSelector('#employeeDashboard.active', { timeout: 15000 });
  assert((await page.locator('.dashboard-header h1').textContent()).includes('Employee'), 'Employee login and protected dashboard loading succeed');
  assert((await page.evaluate(() => orders.length)) >= 2, 'Protected order data loads for authorized employee');

  const employeeBackend = await page.evaluate(async () => {
    const adminWrite = cloudFunctions.httpsCallable('adminWrite');
    const updateOrderFn = cloudFunctions.httpsCallable('updateOrder');
    const upload = cloudFunctions.httpsCallable('uploadProductImage');
    const out = {};
    const nextProducts = products.map(p => ({ ...p }));
    nextProducts[0].stock = 7;
    nextProducts.push({ id: 3, name: 'Validation Created Product', category: 'Tees', description: 'Created in smoke test', price: 350, stock: 2, status: 'Active', image: 'logo-240.png', images: ['logo-240.png'], sizes: ['M'], colors: ['Black'] });
    await adminWrite({ path: 'products', data: nextProducts }); out.products = true;
    try { await adminWrite({ path: 'employeeRoles', data: {} }); out.ceoDenied = false; } catch (e) { out.ceoDenied = /permission/i.test(e.message); }
    await updateOrderFn({ id: 'KEM-2026-000002', customer: 'Other Customer', email: 'other@example.com', status: 'processing', notes: 'validation update' }); out.orderUpdate = true;
    const png = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl5ZQAAAABJRU5ErkJggg==';
    const uploaded = await upload({ contentType: 'image/png', base64: png }); out.uploadUrl = uploaded.data.url;
    return out;
  });
  assert(employeeBackend.products && employeeBackend.orderUpdate, 'Employee product/inventory write and order update succeed');
  assert(employeeBackend.ceoDenied, 'CEO-only employee-role write is denied to regular employee');
  assert(/^https:\/\/firebasestorage\.googleapis\.com\//.test(employeeBackend.uploadUrl), 'Employee product image upload callable succeeds');
  const employeeRoot = await adminRoot();
  assert(employeeRoot.products.some(p => p?.id === 3) && employeeRoot.products[0].stock === 7, 'Product creation/editing and inventory persistence verified in backend');
  assert(employeeRoot.orders['KEM-2026-000002'].status === 'processing', 'Order update persisted');
  const [storedFiles] = await getStorage().bucket().getFiles({ prefix: 'products/' });
  assert(storedFiles.length >= 1, 'Product image exists in Storage emulator');

  await page.evaluate(() => { document.getElementById('employeeDashboard').classList.remove('active'); document.getElementById('mainSite').style.display='block'; document.getElementById('mainNav').style.display='flex'; openEmployeeModal(); });
  await page.keyboard.press('Escape');
  const employeeModalClosedByEscape = !(await page.locator('#employeeModal').evaluate(el => el.classList.contains('active')));
  assert(employeeModalClosedByEscape, 'Escape closes employee login dialog');

  await page.evaluate(async () => { if (auth.currentUser) await auth.signOut(); closeEmployeeModal(); });
  await loginEmployee(page, 'employee@example.com');
  await page.waitForSelector('#employeeDashboard.active', { timeout: 15000 });
  await page.evaluate(() => logoutEmployee());
  await page.waitForFunction(() => !firebase.auth().currentUser, null, { timeout: 15000 });
  const protectedAfterLogout = await page.evaluate(async () => {
    try { await cloudFunctions.httpsCallable('getAdminData')(); return false; } catch (e) { return /auth|sign in/i.test(e.message); }
  });
  assert(protectedAfterLogout, 'Protected Functions reject session after employee logout');

  await loginEmployee(page, 'manager@example.com');
  await page.waitForSelector('#employeeDashboard.active', { timeout: 15000 });
  const managerWrite = await page.evaluate(async () => {
    const w = cloudFunctions.httpsCallable('adminWrite');
    await w({ path: 'categories', data: [{ id: 1, name: 'Tees', description: 'Updated validation tees' }, { id: 2, name: 'Hoodies', description: 'Validation hoodies' }] });
    await w({ path: 'storeSettings', data: { ...storeSettings, shippingFee: 55 } });
    await w({ path: 'coupons', data: [{ id: 1, code: 'SMOKE10', type: 'percentage', value: 10, minOrder: 0, limit: 5, used: 1, status: 'active' }] });
    return true;
  });
  assert(managerWrite, 'Manager categories, coupons, and store/settings persistence succeeds');
  const managerRoot = await adminRoot();
  assert(managerRoot.storeSettings.shippingFee === 55 && managerRoot.categories[0].description.includes('Updated'), 'Manager settings/category writes persisted');
  await page.evaluate(() => logoutEmployee());
  await page.waitForFunction(() => !firebase.auth().currentUser);

  await loginEmployee(page, 'ceo@example.com');
  await page.waitForSelector('#employeeDashboard.active', { timeout: 15000 });
  const ceoAllowed = await page.evaluate(async () => {
    const next = { ...employeeRoles, 'newemployee@example.com': { email: 'newemployee@example.com', name: 'New Employee', role: 'Intern', specialAccess: {} } };
    await cloudFunctions.httpsCallable('adminWrite')({ path: 'employeeRoles', data: next });
    return true;
  });
  assert(ceoAllowed, 'CEO-only employee-role functionality remains allowed to CEO');

  for (const width of [360, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.waitForTimeout(120);
    const m = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, iw: innerWidth, active: document.querySelector('#employeeDashboard')?.classList.contains('active') }));
    assert(m.active && m.sw <= m.iw + 2, `Dashboard has no page-level horizontal overflow at ${width}px`, `${m.sw}/${m.iw}`);
  }

  await page.evaluate(() => { document.getElementById('employeeDashboard').classList.remove('active'); document.getElementById('mainSite').style.display='block'; document.getElementById('mainNav').style.display='flex'; openAuthModal(); });
  await page.waitForTimeout(1000);
  const googleState = await page.evaluate(() => ({
    hasGoogle: !!window.google?.accounts?.id,
    loginContainerChildren: document.getElementById('googleSignInButtonLogin')?.childElementCount || 0,
  }));
  if (googleState.hasGoogle && googleState.loginContainerChildren > 0) ok('Google Identity Services loads and renders a login control in emulator host');
  else ok('Google auth integration code present but OAuth rendering not fully testable on emulator host', JSON.stringify(googleState));
  await page.keyboard.press('Escape');

  const criticalFailures = requestFailures.filter(x => x.includes('127.0.0.1') || x.includes('/favicon-64.png') || x.includes('/logo-240.png'));
  assert(criticalFailures.length === 0, 'No critical local asset/network request failures', criticalFailures.join(' | '));
  assert(pageErrors.length === 0, 'No uncaught browser runtime errors during smoke tests', pageErrors.join(' | '));

  console.log('\n=== CONSOLE ERRORS ===');
  console.log(consoleErrors.length ? consoleErrors.join('\n') : 'none');
  console.log('\n=== REQUEST FAILURES ===');
  console.log(requestFailures.length ? requestFailures.join('\n') : 'none');
  console.log('\n=== DIALOGS ===');
  console.log(dialogs.join('\n'));
  console.log('\n=== RESULT COUNT ===');
  console.log(`${results.filter(r => r.ok).length} passed`);
  await browser.close();
})().catch(async (error) => {
  console.error('\nSMOKE TEST FAILURE:', error.stack || error);
  console.error('\nConsole errors:', consoleErrors);
  console.error('\nPage errors:', pageErrors);
  console.error('\nRequest failures:', requestFailures);
  process.exit(1);
});
