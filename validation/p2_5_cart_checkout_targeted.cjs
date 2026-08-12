const { chromium } = require('playwright');
const { initializeApp, deleteApp } = require('firebase-admin/app');
const { getDatabase } = require('firebase-admin/database');

const BASE = 'http://127.0.0.1:5000';
const PASSWORD = 'Test1234!';
const widths = [360, 375, 390, 414, 768, 1024, 1440];
const failures = [];
let passes = 0;

function check(ok, label, detail = '') {
  if (ok) { passes += 1; console.log(`PASS: ${label}${detail ? ` — ${detail}` : ''}`); }
  else { failures.push(`${label}${detail ? ` — ${detail}` : ''}`); console.error(`FAIL: ${label}${detail ? ` — ${detail}` : ''}`); }
}
function inside(rect, width, tolerance = 1) {
  return rect && rect.left >= -tolerance && rect.right <= width + tolerance && rect.width >= 0;
}
function money(text) { return Number(String(text || '').replace(/[^0-9.-]/g, '')); }
async function waitForShop(page) {
  await page.waitForFunction(() => document.querySelectorAll('#shopProductsGrid .product-card').length >= 2, null, { timeout: 25000 });
}
async function loginCustomer(page, email = 'customer@example.com') {
  await page.evaluate(() => openAuthModal());
  await page.fill('#loginIdentifier', email);
  await page.fill('#loginPassword', PASSWORD);
  await page.click('#loginForm button[type="submit"]');
  await page.waitForFunction(expected => firebase.auth().currentUser?.email === expected, email, { timeout: 15000 });
}
async function addAlpha(page, quantity = 1) {
  await page.goto(`${BASE}/#shop`, { waitUntil: 'domcontentloaded' });
  await waitForShop(page);
  await page.locator('#shopProductsGrid a[data-shop-product-id="1"]').click();
  await page.waitForSelector('#productDetailModal.active');
  await page.locator('#detailSizes .variant-option').filter({ hasText: 'M' }).click();
  await page.locator('#detailColors .variant-option').filter({ hasText: 'Black' }).click();
  for (let i = 1; i < quantity; i++) await page.getByRole('button', { name: 'Increase quantity' }).click();
  await page.getByRole('button', { name: 'Add to Cart', exact: true }).click();
  await page.waitForFunction(expected => cart.length === 1 && cart[0].quantity === expected, quantity);
  await page.evaluate(() => { closeProductDetail(); openCart(); });
  await page.waitForSelector('#cartPage.active');
}
async function openCheckoutReady(page) {
  await page.getByRole('button', { name: /checkout/i, exact: true }).click();
  await page.waitForSelector('#checkoutPage.active');
  await page.waitForFunction(() => document.querySelector('#checkoutStatus')?.textContent !== 'Calculating your order total…', null, { timeout: 20000 });
}
async function tabFocusStyle(page, locator) {
  return locator.evaluate(el => { const s = getComputedStyle(el); return { active: document.activeElement === el, width: s.outlineWidth, style: s.outlineStyle, color: s.outlineColor }; });
}

(async () => {
  const adminApp = initializeApp({
    projectId: 'demo-kem-validation',
    databaseURL: 'http://127.0.0.1:9000?ns=demo-kem-validation-default-rtdb',
  }, 'p2-5-cart-checkout-targeted');
  const db = getDatabase(adminApp);

  // Isolated edge fixtures only. Never production catalogue data.
  await db.ref('products/2').set({
    id: 3,
    name: 'KEM Extremely Long Cart Product Name For Narrow Layout Validation Without Horizontal Overflow',
    category: 'Tees',
    description: 'P2.5 isolated edge fixture.',
    price: 123456.78,
    stock: 0,
    status: 'Active',
    image: 'logo-240.png',
    images: ['logo-240.png'],
    sizes: [],
    colors: [],
  });
  await db.ref('productDiscounts/0').set({ id: 1, productId: 1, type: 'percentage', value: 10, status: 'active' });

  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  try {
    for (const width of widths) {
      const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const pageErrors = [];
      const failedLocal = [];
      const dialogs = [];
      page.on('pageerror', err => pageErrors.push(String(err)));
      page.on('requestfailed', req => { if (req.url().startsWith(BASE)) failedLocal.push(`${req.method()} ${req.url()} ${req.failure()?.errorText || ''}`); });
      page.on('dialog', async dialog => { dialogs.push(`${dialog.type()}: ${dialog.message()}`); await dialog.accept(); });

      await addAlpha(page);
      const cartState = await page.evaluate(() => {
        const rect = el => { const r = el.getBoundingClientRect(); return { left:r.left, right:r.right, top:r.top, bottom:r.bottom, width:r.width, height:r.height }; };
        const pageEl = document.querySelector('#cartPage');
        const container = document.querySelector('#cartPage .cart-container');
        const content = document.querySelector('#cartPage .cart-content');
        const item = document.querySelector('#cartPage .cart-item');
        const image = document.querySelector('#cartPage .cart-item-image');
        const name = document.querySelector('#cartPage .cart-item-info h3');
        const variant = document.querySelector('#cartPage .cart-item-variants');
        const price = document.querySelector('#cartPage .cart-item-price');
        const itemTotal = document.querySelector('#cartPage .cart-item-total');
        const summary = document.querySelector('#cartPage .cart-summary');
        const checkout = document.querySelector('#cartPage .checkout-btn');
        const qty = [...document.querySelectorAll('#cartPage .cart-quantity-control button')];
        const remove = document.querySelector('#cartPage .remove-item');
        const continueBtn = document.querySelector('#cartPage .continue-shopping');
        const coupon = document.querySelector('#couponInput');
        const apply = document.querySelector('.coupon-apply-btn');
        return {
          htmlWidth: document.documentElement.scrollWidth,
          bodyWidth: document.body.scrollWidth,
          bodyOverflowX: getComputedStyle(document.body).overflowX,
          page: rect(pageEl), container: rect(container), content: rect(content), item: rect(item), image: rect(image), name: rect(name), price: rect(price), itemTotal: rect(itemTotal), summary: rect(summary), checkout: rect(checkout),
          columns: getComputedStyle(content).gridTemplateColumns.trim().split(/\s+/).filter(Boolean).length,
          imageFit: getComputedStyle(image).objectFit,
          imageAlt: image.getAttribute('alt'),
          imageSrc: image.getAttribute('src'),
          nameText: name.textContent.trim(),
          variantText: variant?.textContent.trim() || '',
          priceText: price.textContent.replace(/\s+/g,' ').trim(),
          itemTotalText: itemTotal.textContent.trim(),
          itemCount: document.querySelector('.cart-item-count')?.textContent.trim(),
          qty: qty.map(b => ({ rect:rect(b), tag:b.tagName, type:b.getAttribute('type'), label:b.getAttribute('aria-label') })),
          remove: { rect:rect(remove), tag:remove.tagName, type:remove.getAttribute('type'), label:remove.getAttribute('aria-label'), text:remove.textContent.trim() },
          continueBtn: { rect:rect(continueBtn), tag:continueBtn.tagName, type:continueBtn.getAttribute('type'), text:continueBtn.textContent.trim() },
          coupon: { rect:rect(coupon), tag:coupon.tagName, disabled:coupon.disabled },
          apply: { rect:rect(apply), tag:apply.tagName, type:apply.getAttribute('type') },
          summaryPosition: getComputedStyle(summary).position,
          checkoutPosition: getComputedStyle(checkout).position,
          checkoutTag: checkout.tagName,
          checkoutHeight: rect(checkout).height,
          saleState: document.querySelector('.cart-item-sale-state')?.textContent.trim() || '',
          originalPrice: document.querySelector('.cart-item-original-price')?.textContent.trim() || '',
          reducedTransition: getComputedStyle(checkout).transitionDuration,
        };
      });

      const expectedColumns = width >= 1024 ? 2 : 1;
      check(cartState.htmlWidth <= width && cartState.bodyWidth <= width, `Cart has no page-level overflow at ${width}px`, `${cartState.htmlWidth}/${cartState.bodyWidth}/${width}`);
      check(cartState.bodyOverflowX !== 'hidden', `Body overflow remains visible in Cart at ${width}px`, cartState.bodyOverflowX);
      check(inside(cartState.page,width) && inside(cartState.container,width) && inside(cartState.content,width) && inside(cartState.item,width), `Cart shell and item remain contained at ${width}px`);
      check(cartState.columns === expectedColumns, `Cart uses intended ${expectedColumns}-column composition at ${width}px`, String(cartState.columns));
      check(inside(cartState.image,width) && cartState.imageFit === 'contain' && /logo-240\.png/.test(cartState.imageSrc || '') && cartState.imageAlt === 'Validation Alpha Tee', `Cart uses contained authoritative product imagery at ${width}px`, `${cartState.imageFit}/${cartState.imageAlt}`);
      check(cartState.nameText === 'Validation Alpha Tee' && inside(cartState.name,width), `Cart product identity is authoritative and contained at ${width}px`, cartState.nameText);
      check(/Size: M/.test(cartState.variantText) && /Color: Black/.test(cartState.variantText), `Cart shows selected size and color at ${width}px`, cartState.variantText);
      check(/EGP 450\.00 each/.test(cartState.priceText) && /EGP 500\.00/.test(cartState.priceText) && cartState.saleState === 'Sale price applied', `Cart presents genuine product discount without invented claim at ${width}px`, `${cartState.priceText}/${cartState.saleState}`);
      check(/EGP 450\.00/.test(cartState.itemTotalText) && inside(cartState.itemTotal,width), `Per-item total is contained at ${width}px`, cartState.itemTotalText);
      check(cartState.itemCount === '1 item', `Cart item count uses existing cart quantity at ${width}px`, cartState.itemCount);
      check(cartState.qty.length === 2 && cartState.qty.every(b => b.tag === 'BUTTON' && b.type === 'button' && b.rect.width >= 44 && b.rect.height >= 44 && b.label), `Cart quantity controls are semantic labelled 44px targets at ${width}px`, JSON.stringify(cartState.qty));
      check(cartState.remove.tag === 'BUTTON' && cartState.remove.type === 'button' && cartState.remove.rect.height >= 44 && /Remove Validation Alpha Tee/.test(cartState.remove.label || '') && cartState.remove.text === 'Remove', `Remove control is restrained, semantic and labelled at ${width}px`, JSON.stringify(cartState.remove));
      check(cartState.continueBtn.tag === 'BUTTON' && cartState.continueBtn.type === 'button' && cartState.continueBtn.rect.height >= 44 && cartState.continueBtn.text === 'Continue Shopping', `Continue Shopping is semantic and usable at ${width}px`, JSON.stringify(cartState.continueBtn));
      check(cartState.coupon.tag === 'INPUT' && cartState.coupon.rect.height >= 44 && cartState.apply.tag === 'BUTTON' && cartState.apply.type === 'button' && cartState.apply.rect.height >= 44, `Coupon input and Apply control are usable at ${width}px`);
      check(inside(cartState.summary,width) && cartState.summaryPosition === 'static', `Cart summary is contained and non-sticky at ${width}px`, `${cartState.summaryPosition}/${JSON.stringify(cartState.summary)}`);
      check(cartState.checkoutTag === 'BUTTON' && cartState.checkoutHeight >= 44 && !['fixed','sticky'].includes(cartState.checkoutPosition), `Checkout CTA is semantic, prominent and unobstructed at ${width}px`, `${cartState.checkoutHeight}/${cartState.checkoutPosition}`);
      check(parseFloat(cartState.reducedTransition || '0') <= 0.001 || /ms/.test(cartState.reducedTransition), `Reduced motion suppresses nonessential Cart transition at ${width}px`, cartState.reducedTransition);

      // Keyboard path through cart action controls.
      await page.locator('#cartPage .continue-shopping').focus();
      await page.keyboard.press('Tab');
      let active = await page.evaluate(() => ({ tag:document.activeElement?.tagName, label:document.activeElement?.getAttribute('aria-label'), id:document.activeElement?.id, cls:document.activeElement?.className }));
      check(active.tag === 'BUTTON' && /Decrease quantity/.test(active.label || ''), `Tab navigation reaches cart quantity control at ${width}px`, JSON.stringify(active));
      const focusCart = await tabFocusStyle(page, page.locator('#cartPage .cart-quantity-control button').first());
      check(focusCart.active && focusCart.width === '3px' && focusCart.style === 'solid', `Cart quantity control retains 3px visible keyboard focus at ${width}px`, JSON.stringify(focusCart));

      await loginCustomer(page);
      await page.waitForTimeout(100);
      await page.evaluate(() => openCart());
      await page.fill('#couponInput', 'SMOKE10');
      await page.getByRole('button', { name:'Apply', exact:true }).click();
      await page.waitForFunction(() => appliedCoupon?.code === 'SMOKE10' && appliedCoupon?.serverValidated === true, null, { timeout:20000 });
      check(await page.locator('.coupon-state.kem-state-success').isVisible(), `Valid server-backed coupon exposes success state at ${width}px`);

      await openCheckoutReady(page);
      const checkoutState = await page.evaluate(() => {
        const rect = el => { const r=el.getBoundingClientRect(); return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}; };
        const grid=document.querySelector('#checkoutPage .checkout-grid'); const summary=document.querySelector('#checkoutPage .order-summary-checkout'); const button=document.querySelector('.place-order-btn');
        const fields=[...document.querySelectorAll('#checkoutForm input,#checkoutForm textarea')]; const payment=document.querySelector('.payment-option'); const radio=document.querySelector('#paymentCod');
        return {
          htmlWidth:document.documentElement.scrollWidth, bodyWidth:document.body.scrollWidth, bodyOverflowX:getComputedStyle(document.body).overflowX,
          grid:rect(grid), summary:rect(summary), columns:getComputedStyle(grid).gridTemplateColumns.trim().split(/\s+/).filter(Boolean).length,
          fields:fields.map(f=>({id:f.id,rect:rect(f),label:document.querySelector(`label[for="${f.id}"]`)?.textContent.trim()||''})),
          payment:{rect:rect(payment),tag:payment.tagName,selected:payment.classList.contains('selected')}, radio:{checked:radio.checked,value:radio.value,describedby:radio.getAttribute('aria-describedby')},
          paymentText:payment.textContent.replace(/\s+/g,' ').trim(), summaryPosition:getComputedStyle(summary).position,
          button:{rect:rect(button),tag:button.tagName,type:button.getAttribute('type'),disabled:button.disabled,position:getComputedStyle(button).position,describedby:button.getAttribute('aria-describedby')},
          status:document.querySelector('#checkoutStatus').textContent.trim(), subtotal:document.querySelector('#checkoutSubtotal').textContent.trim(), coupon:document.querySelector('#checkoutCouponRow').textContent.replace(/\s+/g,' ').trim(), shipping:document.querySelector('#checkoutShipping').textContent.trim(), total:document.querySelector('#checkoutTotal').textContent.trim(),
          summaryItems:[...document.querySelectorAll('#checkoutSummaryItems .summary-item')].map(i=>({rect:rect(i),name:i.querySelector('.summary-item-name')?.textContent.trim(),meta:i.querySelector('.summary-item-meta')?.textContent.trim(),price:i.querySelector('.summary-item-price')?.textContent.trim(),fit:getComputedStyle(i.querySelector('img')).objectFit,alt:i.querySelector('img').getAttribute('alt')})),
        };
      });
      check(checkoutState.htmlWidth <= width && checkoutState.bodyWidth <= width && checkoutState.bodyOverflowX !== 'hidden', `Checkout has no page-level overflow or concealment at ${width}px`, `${checkoutState.htmlWidth}/${checkoutState.bodyWidth}/${checkoutState.bodyOverflowX}`);
      check(inside(checkoutState.grid,width) && inside(checkoutState.summary,width), `Checkout grid and summary remain contained at ${width}px`);
      check(checkoutState.columns === expectedColumns, `Checkout uses intended ${expectedColumns}-column composition at ${width}px`, String(checkoutState.columns));
      check(checkoutState.fields.length >= 8 && checkoutState.fields.every(f => inside(f.rect,width) && f.rect.height >= 44 && f.label), `Checkout fields are contained, labelled and usable at ${width}px`, JSON.stringify(checkoutState.fields));
      check(checkoutState.payment.tag === 'LABEL' && checkoutState.payment.rect.height >= 44 && checkoutState.payment.selected && checkoutState.radio.checked && checkoutState.radio.value === 'cod' && checkoutState.radio.describedby === 'paymentCodDescription', `COD is the selected accessible payment method at ${width}px`, JSON.stringify({payment:checkoutState.payment,radio:checkoutState.radio}));
      check(/Cash on Delivery/.test(checkoutState.paymentText) && !/[💵💳]/u.test(checkoutState.paymentText), `Payment presentation is factual and emoji-free at ${width}px`, checkoutState.paymentText);
      check(checkoutState.summaryPosition === 'static', `Checkout order summary is non-sticky at ${width}px`, checkoutState.summaryPosition);
      check(checkoutState.summaryItems.length === 1 && checkoutState.summaryItems[0].name === 'Validation Alpha Tee' && /Size: M/.test(checkoutState.summaryItems[0].meta) && /Color: Black/.test(checkoutState.summaryItems[0].meta) && /Qty: 1/.test(checkoutState.summaryItems[0].meta) && checkoutState.summaryItems[0].fit === 'contain' && checkoutState.summaryItems[0].alt === 'Validation Alpha Tee', `Checkout summary preserves authoritative item, variant, quantity and image at ${width}px`, JSON.stringify(checkoutState.summaryItems));
      check(/ready/i.test(checkoutState.status) && !checkoutState.button.disabled, `Authoritative quote reaches ready state before order submission at ${width}px`, checkoutState.status);
      check(checkoutState.button.tag === 'BUTTON' && checkoutState.button.type === 'button' && checkoutState.button.rect.height >= 44 && checkoutState.button.describedby === 'checkoutStatus' && !['fixed','sticky'].includes(checkoutState.button.position), `Place Order CTA is semantic, labelled by state and unobstructed at ${width}px`, JSON.stringify(checkoutState.button));
      check(money(checkoutState.subtotal) === 450 && /SMOKE10/.test(await page.evaluate(() => appliedCoupon?.code || '')) && /45\.00/.test(checkoutState.coupon) && money(checkoutState.total) > 0, `Checkout quote displays real server-derived subtotal/coupon/total at ${width}px`, `${checkoutState.subtotal}/${checkoutState.coupon}/${checkoutState.total}`);

      await page.locator('#checkoutName').focus();
      const fieldFocus = await tabFocusStyle(page, page.locator('#checkoutName'));
      check(fieldFocus.active && fieldFocus.width === '3px' && fieldFocus.style === 'solid', `Checkout field retains 3px visible keyboard focus at ${width}px`, JSON.stringify(fieldFocus));
      await page.locator('#checkoutNotes').focus();
      await page.keyboard.press('Tab');
      const paymentFocus = await tabFocusStyle(page, page.locator('#paymentCod'));
      check(paymentFocus.active && paymentFocus.width === '3px' && paymentFocus.style === 'solid', `Payment choice retains 3px visible keyboard focus at ${width}px`, JSON.stringify(paymentFocus));
      let reachedOrder = false;
      for (let i = 0; i < 8; i++) {
        await page.keyboard.press('Tab');
        if (await page.locator('.place-order-btn').evaluate(el => document.activeElement === el)) { reachedOrder = true; break; }
      }
      const orderFocus = await tabFocusStyle(page, page.locator('.place-order-btn'));
      check(reachedOrder && orderFocus.active && orderFocus.width === '3px' && orderFocus.style === 'solid', `Place Order retains 3px visible keyboard focus at ${width}px`, JSON.stringify(orderFocus));
      check(pageErrors.length === 0, `No uncaught browser errors in Cart/Checkout at ${width}px`, JSON.stringify(pageErrors));
      check(failedLocal.length === 0, `No failed local application requests in Cart/Checkout at ${width}px`, JSON.stringify(failedLocal));
      await context.close();
    }

    // Interaction/security matrix at 390px.
    const context = await browser.newContext({ viewport:{width:390,height:1000} });
    const page = await context.newPage();
    const dialogs = [];
    const pageErrors = [];
    const failedLocal = [];
    page.on('dialog', async dialog => { dialogs.push(`${dialog.type()}: ${dialog.message()}`); await dialog.accept(); });
    page.on('pageerror', err => pageErrors.push(String(err)));
    page.on('requestfailed', req => { if(req.url().startsWith(BASE)) failedLocal.push(`${req.method()} ${req.url()} ${req.failure()?.errorText || ''}`); });

    await addAlpha(page);
    check((await page.evaluate(() => cart.length === 1 && cart[0].id === 1 && cart[0].size === 'M' && cart[0].color === 'Black')), 'Shop → product detail → Add to Cart preserves real product and selected variant');
    await page.getByRole('button',{name:/Increase quantity for Validation Alpha Tee/}).click();
    check(await page.evaluate(() => cart[0].quantity === 2), 'Cart quantity increase uses existing mutation path');
    await page.getByRole('button',{name:/Decrease quantity for Validation Alpha Tee/}).click();
    check(await page.evaluate(() => cart[0].quantity === 1), 'Cart quantity decrease uses existing mutation path');
    await page.getByRole('button',{name:'Continue Shopping'}).click();
    check(!(await page.locator('#cartPage').evaluate(el=>el.classList.contains('active'))) && await page.locator('#mainSite').isVisible(), 'Continue Shopping returns to the storefront');
    await page.evaluate(() => openCart());
    check(await page.evaluate(() => cart.length === 1), 'Cart state is preserved across existing in-app navigation');

    await page.reload({waitUntil:'domcontentloaded'}); await waitForShop(page);
    check(await page.evaluate(() => cart.length === 0), 'Full refresh preserves existing in-memory cart behavior (cart initializes empty)');
    await page.evaluate(() => openCart());
    check(await page.locator('.empty-cart').isVisible() && /There are no products in your cart/.test(await page.locator('.empty-cart').innerText()) && /Shop KEM/.test(await page.locator('.empty-cart').innerText()), 'Empty Cart is factual, useful and promotion-free');
    await page.getByRole('button',{name:'Shop KEM'}).click();
    check(await page.locator('#mainSite').isVisible(), 'Empty-cart Shop KEM action returns to Shop flow');

    await addAlpha(page);
    await page.getByRole('button',{name:/Remove Validation Alpha Tee/}).click();
    await page.waitForFunction(() => cart.length === 0);
    check(await page.locator('.empty-cart').isVisible(), 'Remove uses existing cart mutation path and reaches empty state');

    // Authentication requirement. Earlier width matrix already proves Shop → Cart; use the existing deep link here to avoid stale section visibility state.
    await page.goto(`${BASE}/?product=1`, { waitUntil:'domcontentloaded' });
    await page.waitForSelector('#productDetailModal.active');
    await page.locator('#detailSizes .variant-option').filter({hasText:'M'}).click();
    await page.locator('#detailColors .variant-option').filter({hasText:'Black'}).click();
    await page.getByRole('button',{name:'Add to Cart',exact:true}).click();
    await page.evaluate(()=>{closeProductDetail();openCart();});
    await page.waitForSelector('#cartPage.active');
    const d0 = dialogs.length;
    await page.getByRole('button',{name:/checkout/i,exact:true}).click();
    await page.waitForTimeout(150);
    check(dialogs.slice(d0).some(d=>/sign in before checkout/i.test(d)) && await page.locator('#authModal').evaluate(el=>el.classList.contains('active')), 'Checkout preserves authentication requirement');
    await page.keyboard.press('Escape');

    // Unverified requirement.
    await loginCustomer(page,'unverified@example.com');
    await page.evaluate(() => openCart());
    const d1=dialogs.length;
    await page.getByRole('button',{name:/checkout/i,exact:true}).click();
    await page.waitForTimeout(150);
    check(dialogs.slice(d1).some(d=>/verify your email/i.test(d)) && !(await page.locator('#checkoutPage').evaluate(el=>el.classList.contains('active'))), 'Checkout preserves verified-email requirement');
    await page.evaluate(async()=>{ if(auth.currentUser) await auth.signOut(); });
    await page.waitForFunction(()=>!firebase.auth().currentUser);

    await loginCustomer(page);
    await page.evaluate(() => openCart());

    // Invalid coupon remains server-backed and now has inline error state while preserving alert.
    await page.fill('#couponInput','USEDUP');
    const d2=dialogs.length;
    await page.getByRole('button',{name:'Apply',exact:true}).click();
    await page.waitForTimeout(250);
    check(await page.evaluate(() => appliedCoupon === null), 'Invalid/exhausted coupon is not accepted client-side');
    check(dialogs.slice(d2).some(d=>/usage limit|coupon/i.test(d)) && await page.locator('#couponFeedback.kem-state-error').isVisible(), 'Invalid coupon surfaces the actual backend failure state');

    await page.fill('#couponInput','SMOKE10');
    await page.getByRole('button',{name:'Apply',exact:true}).click();
    await page.waitForFunction(()=>appliedCoupon?.serverValidated===true);
    check(await page.evaluate(()=>appliedCoupon.code==='SMOKE10'), 'Valid coupon is accepted only after server-backed quote validation');
    await page.getByRole('button',{name:'Remove',exact:true}).last().click();
    check(await page.evaluate(()=>appliedCoupon===null), 'Coupon removal uses existing coupon mutation path');
    await page.fill('#couponInput','SMOKE10');
    await page.getByRole('button',{name:'Apply',exact:true}).click();
    await page.waitForFunction(()=>appliedCoupon?.serverValidated===true);

    await openCheckoutReady(page);
    check(await page.locator('#savedAddressesSection').isVisible(), 'Authenticated checkout displays existing saved addresses');
    await page.locator('#savedAddressesList .saved-address-option').first().click();
    check((await page.inputValue('#checkoutAddress'))==='1 Validation Street' && (await page.inputValue('#checkoutHouseNumber'))==='10' && (await page.inputValue('#checkoutCity'))==='Cairo', 'Saved-address selection fills the existing checkout fields');
    await page.getByRole('button',{name:'Use New Address'}).click();
    check((await page.inputValue('#checkoutAddress'))==='' && (await page.inputValue('#checkoutHouseNumber'))==='', 'Use New Address preserves existing address reset behavior');
    await page.locator('#checkoutName').fill('');
    await page.getByRole('button',{name:/place order/i}).click();
    check(await page.locator('#checkoutName').evaluate(el=>!el.checkValidity()), 'Native form validation still blocks missing required customer information');
    await page.locator('#savedAddressesList .saved-address-option').first().click();

    // Server quote is source of truth: compare UI with a direct quote response using same authoritative callable.
    const authoritative = await page.evaluate(async()=>{
      const quote=cloudFunctions.httpsCallable('quoteOrder');
      const r=await quote({items:cart.map(item=>({id:item.id,quantity:item.quantity,size:item.size||'',color:item.color||''})),couponCode:appliedCoupon?.code||null});
      return r.data;
    });
    check(money(await page.locator('#checkoutSubtotal').textContent()) === Number(authoritative.subtotal) && money(await page.locator('#checkoutTotal').textContent()) === Number(authoritative.total), 'Displayed checkout subtotal and total match authoritative server quote exactly');
    await page.evaluate(()=>{document.getElementById('checkoutTotal').textContent='EGP 1.00';});
    await page.evaluate(()=>renderCheckoutSummary());
    await page.waitForFunction(()=>/ready/i.test(document.querySelector('#checkoutStatus')?.textContent||''));
    check(money(await page.locator('#checkoutTotal').textContent()) === Number(authoritative.total), 'Re-quote overwrites presentation tampering; UI does not establish total authority');

    const invalidCalls=await page.evaluate(async()=>{
      const quote=cloudFunctions.httpsCallable('quoteOrder'); const out={};
      try{await quote({items:[{id:1,quantity:1,size:'FAKE',color:'Black'}]});out.variant=false;}catch(e){out.variant=/valid size/i.test(e.message);}
      try{await quote({items:[{id:1,quantity:99,size:'M',color:'Black'}]});out.stock=false;}catch(e){out.stock=/available/i.test(e.message);}
      try{await quote({items:[{id:1,quantity:1,size:'M',color:'Black'}],couponCode:'USEDUP'});out.coupon=false;}catch(e){out.coupon=/usage limit|coupon/i.test(e.message);}
      return out;
    });
    check(invalidCalls.variant,'Server quote rejects invalid variant manipulation');
    check(invalidCalls.stock,'Server quote rejects invalid stock/quantity manipulation');
    check(invalidCalls.coupon,'Server quote rejects invalid coupon manipulation');

    await page.evaluate(async()=>{cart[0].quantity=99;await renderCheckoutSummary();});
    check(await page.locator('.place-order-btn').isDisabled() && /Unable/.test(await page.locator('#checkoutTotal').textContent()) && !/ready/i.test(await page.locator('#checkoutStatus').textContent()), 'Quote failure remains visible and disables Place Order');
    await page.evaluate(async()=>{cart[0].quantity=1;await renderCheckoutSummary();});
    await page.waitForFunction(()=>!document.querySelector('.place-order-btn').disabled);

    // Out-of-stock fixture through real product-detail path.
    await page.evaluate(()=>backToCart());
    await page.getByRole('button',{name:'Continue Shopping'}).click();
    await page.goto(`${BASE}/?product=3`,{waitUntil:'domcontentloaded'}); await page.waitForSelector('#productDetailModal.active');
    const outOfStockBefore = await page.evaluate(() => cart.length);
      const outOfStockDialogs = dialogs.length;
      check(/Out of stock/i.test(await page.locator('#detailStock').textContent()), 'Out-of-stock product exposes the frozen availability state');
      await page.getByRole('button',{name:'Add to Cart',exact:true}).click();
      await page.waitForTimeout(100);
      check(dialogs.slice(outOfStockDialogs).some(d=>/Selected quantity is no longer available/i.test(d)) && await page.evaluate(before => cart.length === before, outOfStockBefore), 'Out-of-stock Add to Cart follows the existing stock-rejection path without cart mutation');
    await page.goto(`${BASE}/?product=999999`,{waitUntil:'domcontentloaded'}); await page.waitForTimeout(200);
    check(!(await page.locator('#productDetailModal').evaluate(el=>el.classList.contains('active'))), 'Invalid/missing product deep link retains existing safe handling');

    // Successful order: seed reset is not used again; exactly one intended test order is created here.
    await page.goto(`${BASE}/#shop`,{waitUntil:'domcontentloaded'}); await waitForShop(page);
    await page.waitForFunction(()=>firebase.auth().currentUser?.email==='customer@example.com');
    await page.locator('#shopProductsGrid a[data-shop-product-id="1"]').click(); await page.waitForSelector('#productDetailModal.active');
    await page.locator('#detailSizes .variant-option').filter({hasText:'M'}).click(); await page.locator('#detailColors .variant-option').filter({hasText:'Black'}).click(); await page.getByRole('button',{name:'Add to Cart',exact:true}).click();
    await page.evaluate(()=>{closeProductDetail();openCart();});
    await page.fill('#couponInput','SMOKE10'); await page.getByRole('button',{name:'Apply',exact:true}).click(); await page.waitForFunction(()=>appliedCoupon?.serverValidated===true);
    await openCheckoutReady(page); await page.locator('#savedAddressesList .saved-address-option').first().click();
    const before=(await db.ref('/').once('value')).val(); const beforeStock=before.products[0].stock; const beforeUsed=before.coupons[0].used; const beforeOrderCount=Object.keys(before.orders||{}).length;
    await page.getByRole('button',{name:/place order/i}).click();
    await page.waitForFunction(()=>document.querySelector('#orderSuccessState') && !document.querySelector('#orderSuccessState').hidden,{timeout:20000});
    const after=(await db.ref('/').once('value')).val();
    const successText=await page.locator('#orderSuccessState').innerText();
    check(/Order placed successfully/.test(successText) && /Order ID: KEM-/.test(successText) && /Payment: Cash on Delivery/.test(successText), 'Successful COD order shows factual returned order confirmation');
    check(Object.keys(after.orders||{}).length===beforeOrderCount+1,'Exactly one intended successful test order is created');
    check(after.products[0].stock===beforeStock-1,'Successful COD order preserves atomic inventory decrement');
    check(after.coupons[0].used===beforeUsed+1,'Successful COD order preserves coupon usage increment');
    check(await page.evaluate(()=>cart.length===0 && appliedCoupon===null),'Successful order preserves cart/coupon clearing');
    check(!(await page.locator('#checkoutPage').evaluate(el=>el.classList.contains('active'))) && await page.locator('#mainSite').isVisible(),'Successful order returns to the existing storefront state');
    check(pageErrors.length===0,'No uncaught browser errors in targeted Cart/Checkout interaction flow',JSON.stringify(pageErrors));
    check(failedLocal.length===0,'No failed local application requests in targeted Cart/Checkout interaction flow',JSON.stringify(failedLocal));
    await context.close();
  } finally {
    await browser.close();
    await deleteApp(adminApp);
  }

  console.log(`P2_5_CART_CHECKOUT_RESULT ${passes} passed, ${failures.length} failed`);
  if (failures.length) { console.error('P2_5_CART_CHECKOUT_FAILURES', JSON.stringify(failures,null,2)); process.exit(1); }
  console.log('P2_5_CART_CHECKOUT_COMPLETE');
})().catch(async error => { console.error(error); console.log(`P2_5_CART_CHECKOUT_RESULT ${passes} passed, ${failures.length + 1} failed`); process.exit(1); });
