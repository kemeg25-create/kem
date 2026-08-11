from pathlib import Path

p = Path('validation/smoke.cjs')
h = p.read_text()

# Resolve Admin SDK from NODE_PATH in Actions.
h = h.replace("require('../functions/node_modules/firebase-admin/app')", "require('firebase-admin/app')")
h = h.replace("require('../functions/node_modules/firebase-admin/database')", "require('firebase-admin/database')")
h = h.replace("require('../functions/node_modules/firebase-admin/storage')", "require('firebase-admin/storage')")

# Import deleteApp so the harness can explicitly release its Admin SDK resources.
old_import = "const { initializeApp, getApps } = require('firebase-admin/app');"
new_import = "const { initializeApp, getApps, deleteApp } = require('firebase-admin/app');"
if old_import not in h:
    raise SystemExit('firebase-admin app import anchor not found')
h = h.replace(old_import, new_import, 1)

# Existing integration-harness corrections (test-only; no production source changes).
old = "await page.evaluate(() => openAuthModal());\n  await page.fill('#loginIdentifier', email);"
new = "await page.evaluate(() => { openAuthModal(); switchAuthTab('login'); });\n  await page.fill('#loginIdentifier', email);"
if old not in h:
    raise SystemExit('loginCustomer harness anchor not found')
h = h.replace(old, new, 1)

old_quote = "    quote: lastCheckoutQuote ? { total: lastCheckoutQuote.total, items: lastCheckoutQuote.items } : null,"
new_quote = "    quoteTotalText: document.getElementById('checkoutTotal')?.textContent || null,"
if old_quote not in h:
    raise SystemExit('checkout instrumentation anchor not found')
h = h.replace(old_quote, new_quote, 1)

old_password = "await page.evaluate(async () => auth.signInWithEmailAndPassword('unverified@example.com', PASSWORD));"
new_password = "await page.evaluate(async (password) => auth.signInWithEmailAndPassword('unverified@example.com', password), PASSWORD);"
if old_password not in h:
    raise SystemExit('unverified customer login harness anchor not found')
h = h.replace(old_password, new_password, 1)

widths_old = '[360, 390, 768, 1024, 1440]'
widths_new = '[360, 375, 390, 414, 768, 1024, 1440]'
if h.count(widths_old) != 2:
    raise SystemExit(f'expected two viewport loops, found {h.count(widths_old)}')
h = h.replace(widths_old, widths_new)

# Explicitly verify client cart clearing after the successful COD transaction.
order_anchor = """  assert(newOrders.length >= 2, 'COD order creation succeeds through checkout UI');
  assert(afterRoot.products[0].stock === beforeStock - 1, 'Successful order decrements inventory atomically');
  assert(afterRoot.coupons[0].used === beforeUsed + 1, 'Successful coupon order increments coupon usage atomically');
"""
order_replacement = order_anchor + """  assert(await page.evaluate(() => cart.length === 0), 'Cart clears after successful COD order');
"""
if order_anchor not in h:
    raise SystemExit('successful order assertion anchor not found')
h = h.replace(order_anchor, order_replacement, 1)

# Track local Hosting HTTP errors separately from intentionally exercised Function errors.
array_anchor = """const requestFailures = [];
const dialogs = [];
"""
array_replacement = """const requestFailures = [];
const localHttpErrors = [];
const dialogs = [];
"""
if array_anchor not in h:
    raise SystemExit('request arrays anchor not found')
h = h.replace(array_anchor, array_replacement, 1)

listener_anchor = """  page.on('requestfailed', req => requestFailures.push(`${req.method()} ${req.url()} :: ${req.failure()?.errorText || 'failed'}`));
  page.on('dialog', async dialog => {
"""
listener_replacement = """  page.on('requestfailed', req => requestFailures.push(`${req.method()} ${req.url()} :: ${req.failure()?.errorText || 'failed'}`));
  page.on('response', response => {
    if (response.url().startsWith(BASE) && response.status() >= 400) localHttpErrors.push(`${response.status()} ${response.url()}`);
  });
  page.on('dialog', async dialog => {
"""
if listener_anchor not in h:
    raise SystemExit('request listener anchor not found')
h = h.replace(listener_anchor, listener_replacement, 1)

network_anchor = """  const criticalFailures = requestFailures.filter(x => x.includes('127.0.0.1') || x.includes('/favicon-64.png') || x.includes('/logo-240.png'));
  assert(criticalFailures.length === 0, 'No critical local asset/network request failures', criticalFailures.join(' | '));
  assert(pageErrors.length === 0, 'No uncaught browser runtime errors during smoke tests', pageErrors.join(' | '));
"""
network_replacement = network_anchor + """  assert(localHttpErrors.length === 0, 'No broken local Hosting links/assets/HTTP responses', localHttpErrors.join(' | '));
  const internalHrefs = await page.locator('a[href]').evaluateAll(links => [...new Set(links.map(a => a.getAttribute('href')).filter(Boolean))]);
  const brokenInternalLinks = [];
  for (const href of internalHrefs) {
    if (href.startsWith('#') || href.startsWith('javascript:') || href.startsWith('mailto:') || href.startsWith('tel:')) continue;
    const target = new URL(href, BASE);
    if (target.origin !== new URL(BASE).origin) continue;
    const response = await context.request.get(target.toString(), { failOnStatusCode: false, timeout: 10000 });
    if (!response.ok()) brokenInternalLinks.push(`${response.status()} ${target.toString()}`);
  }
  assert(brokenInternalLinks.length === 0, 'No broken internal links', brokenInternalLinks.join(' | '));
"""
if network_anchor not in h:
    raise SystemExit('network assertions anchor not found')
h = h.replace(network_anchor, network_replacement, 1)

# Instrument the exact shutdown boundary, prove which handles remain after Chromium closes,
# then release the Admin RTDB connection instead of force-exiting the Node process.
shutdown_anchor = """  console.log('\\n=== RESULT COUNT ===');
  console.log(`${results.filter(r => r.ok).length} passed`);
  await browser.close();
"""
shutdown_replacement = """  console.log('\\n=== RESULT COUNT ===');
  console.log(`${results.filter(r => r.ok).length} passed`);

  const shutdownStarted = Date.now();
  const summarizeHandles = () => process._getActiveHandles().map((handle, index) => ({
    index,
    type: handle?.constructor?.name || typeof handle,
    localAddress: handle?.localAddress,
    localPort: handle?.localPort,
    remoteAddress: handle?.remoteAddress,
    remotePort: handle?.remotePort,
    destroyed: handle?.destroyed,
    connecting: handle?.connecting,
    readable: handle?.readable,
    writable: handle?.writable,
    hasRef: typeof handle?.hasRef === 'function' ? handle.hasRef() : undefined,
  }));
  const summarizeRequests = () => process._getActiveRequests().map((request, index) => ({
    index,
    type: request?.constructor?.name || typeof request,
  }));
  const shutdownLog = (label) => console.log(`SHUTDOWN_DIAGNOSTIC ${Date.now() - shutdownStarted}ms ${label}`, JSON.stringify({ handles: summarizeHandles(), requests: summarizeRequests() }));

  shutdownLog('before-browser-close');
  await browser.close();
  shutdownLog('after-browser-close-before-admin-cleanup');
  getDatabase().goOffline();
  await Promise.all(getApps().map(app => deleteApp(app)));
  await new Promise(resolve => setTimeout(resolve, 100));
  shutdownLog('after-admin-cleanup');
  console.log(`FULL_SMOKE_COMPLETE ${Date.now() - shutdownStarted}ms shutdown`);
"""
if shutdown_anchor not in h:
    raise SystemExit('smoke shutdown anchor not found')
h = h.replace(shutdown_anchor, shutdown_replacement, 1)

p.write_text(h)
print('Patched full smoke with bounded diagnostics, cart-clear coverage, internal-link checks, and Admin cleanup')
