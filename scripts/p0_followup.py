from pathlib import Path
import json


def rep(s, old, new, label):
    if old not in s:
        raise SystemExit(f'missing marker: {label}')
    return s.replace(old, new, 1)

p = Path('functions/index.js')
s = p.read_text()

# Product ids flow into inline event handlers; never preserve a non-numeric id.
old = """    const idNumber = Math.floor(normalizeNumber(product.id));
    const safe = {
      id: idNumber > 0 ? idNumber : cleanMarkupText(product.id, 80),
"""
if 'if (idNumber < 1) continue;' not in s:
    s = rep(s, old, """    const idNumber = Math.floor(normalizeNumber(product.id));
    if (idNumber < 1) continue;
    const safe = {
      id: idNumber,
""", 'strict product id')

# Coupon-code validation must not be an unauthenticated oracle.
old = """exports.quoteOrder = onCall(async (request) => {
  const snap = await db.ref('/').once('value');
  const quote = calculateQuote(snap.val() || {}, request.data?.items, request.data?.couponCode);
"""
if 'Coupon validation requires a verified account.' not in s:
    s = rep(s, old, """exports.quoteOrder = onCall(async (request) => {
  const couponCode = cleanText(request.data?.couponCode, 50);
  if (couponCode) {
    try {
      await requireVerifiedCustomer(request);
    } catch (error) {
      throw new HttpsError('permission-denied', 'Coupon validation requires a verified account.');
    }
  }
  const snap = await db.ref('/').once('value');
  const quote = calculateQuote(snap.val() || {}, request.data?.items, couponCode);
""", 'authenticated coupon quote')

# Add server-controlled anti-abuse state for stock-affecting COD orders.
old = """  let committedOrder = null;
  const year = new Date().getUTCFullYear();

  const transaction = await db.ref('/').transaction((root) => {
    root = root || {};
    const quote = calculateQuote(root, request.data?.items, request.data?.couponCode);

    root.counters = root.counters || {};
"""
if 'const orderRequestTime = Date.now();' not in s:
    s = rep(s, old, """  let committedOrder = null;
  let abortReason = null;
  const year = new Date().getUTCFullYear();
  const orderRequestTime = Date.now();

  const transaction = await db.ref('/').transaction((root) => {
    root = root || {};
    abortReason = null;
    const quote = calculateQuote(root, request.data?.items, request.data?.couponCode);

    root.orders = root.orders || {};
    root.security = root.security || {};
    root.security.orderRate = root.security.orderRate || {};
    const uid = authenticatedCustomer.uid;
    const rateState = root.security.orderRate[uid] || {};
    const lastOrderAt = Math.max(0, normalizeNumber(rateState.lastOrderAt));
    if (lastOrderAt && orderRequestTime - lastOrderAt < 30000) {
      abortReason = 'Please wait at least 30 seconds before placing another order.';
      return;
    }
    const pendingOrders = Object.values(root.orders).filter((existingOrder) =>
      existingOrder && existingOrder.customerUid === uid && ['pending', 'processing'].includes(String(existingOrder.status).toLowerCase())
    ).length;
    if (pendingOrders >= 5) {
      abortReason = 'This account already has too many pending orders. Please contact KEM before placing another order.';
      return;
    }
    root.security.orderRate[uid] = { lastOrderAt: orderRequestTime };

    root.counters = root.counters || {};
""", 'order abuse controls')

old = """      id: orderId,
      customer: customer.name,
"""
if 'customerUid: authenticatedCustomer.uid' not in s:
    s = rep(s, old, """      id: orderId,
      customerUid: authenticatedCustomer.uid,
      customer: customer.name,
""", 'order uid binding')

old = """  if (!transaction.committed || !committedOrder) {
    throw new HttpsError('aborted', 'The order could not be committed because stock changed. Please review your cart and try again.');
  }
"""
if 'if (abortReason)' not in s:
    s = rep(s, old, """  if (!transaction.committed || !committedOrder) {
    if (abortReason) throw new HttpsError('failed-precondition', abortReason);
    throw new HttpsError('aborted', 'The order could not be committed because stock changed. Please review your cart and try again.');
  }
""", 'order abort reason')

# Full customer-profile directory is CEO-only; normal employees use order records for fulfillment.
old = """  for (const [key, value] of Object.entries(root.users || {})) {
    response.users[key] = {
      email: cleanText(value.email, 254),
      name: cleanText(value.name, 100),
      phone: cleanPhone(value.phone),
      orderHistory: Array.isArray(value.orderHistory) ? value.orderHistory.slice(-50) : [],
      registeredDate: value.registeredDate || null,
      lastLogin: value.lastLogin || null
    };
  }
"""
if 'if (ROLE_LEVEL[employee.role] >= 5) {\n    for (const [key, value] of Object.entries(root.users || {}))' not in s:
    s = rep(s, old, """  if (ROLE_LEVEL[employee.role] >= 5) {
    for (const [key, value] of Object.entries(root.users || {})) {
      response.users[key] = {
        email: cleanText(value.email, 254),
        name: cleanText(value.name, 100),
        phone: cleanPhone(value.phone),
        orderHistory: Array.isArray(value.orderHistory) ? value.orderHistory.slice(-50) : [],
        registeredDate: value.registeredDate || null,
        lastLogin: value.lastLogin || null
      };
    }
  }
""", 'CEO-only user directory')

# Preserve legitimate 5 MB uploads after base64 expansion while keeping strict source parsing.
s = s.replace("cleanText(value, 5 * 1024 * 1024)", "cleanText(value, 8 * 1024 * 1024)", 1)

p.write_text(s)

rp = Path('database.rules.json')
rules = json.loads(rp.read_text())
rules['rules']['security'] = {'.read': False, '.write': False}
rp.write_text(json.dumps(rules, indent=2) + '\n')
print('P0 follow-up patch complete')
