const { onCall, HttpsError } = require('firebase-functions/v2/https');
const { initializeApp } = require('firebase-admin/app');
const { getAuth } = require('firebase-admin/auth');
const { getDatabase } = require('firebase-admin/database');

initializeApp();

const db = getDatabase();
const auth = getAuth();

const ROLE_LEVEL = {
  Intern: 1,
  Employee: 2,
  Senior: 3,
  Manager: 4,
  CEO: 5
};

function sanitizeEmail(email = '') {
  return String(email).trim().toLowerCase().replace(/\./g, ',').replace(/[#$\/\[\]]/g, '_');
}

function normalizeList(value) {
  if (!value) return [];
  return Array.isArray(value) ? value.filter(Boolean) : Object.values(value).filter(Boolean);
}

function normalizeNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function cleanText(value, maxLength = 500) {
  if (value === null || value === undefined) return '';
  return String(value).replace(/[\u0000-\u001F\u007F]/g, ' ').trim().slice(0, maxLength);
}

function cleanEmail(value) {
  const email = cleanText(value, 254).toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    throw new HttpsError('invalid-argument', 'A valid email address is required.');
  }
  return email;
}

function cleanPhone(value) {
  return cleanText(value, 30).replace(/[^0-9+()\-\s]/g, '');
}


function cleanMarkupText(value, maxLength = 500) {
  return cleanText(value, maxLength).replace(/[<>"']/g, '');
}

function cleanImageSource(value) {
  const source = cleanText(value, 8 * 1024 * 1024);
  if (!source) return '';
  if (/^https:\/\/[^\s"'<>]+$/i.test(source)) return source;
  if (/^data:image\/(?:png|jpe?g|webp|gif);base64,[a-z0-9+/=]+$/i.test(source)) return source;
  if (/^[a-z0-9_./() -]+\.(?:png|jpe?g|webp|gif)(?:\?[^"'<>]*)?$/i.test(source)) return source;
  return '';
}

function sanitizeNestedAdminData(value, key = '', depth = 0) {
  if (depth > 8) return null;
  if (Array.isArray(value)) return value.map((item) => sanitizeNestedAdminData(item, key, depth + 1));
  if (value && typeof value === 'object') {
    const result = {};
    for (const [childKey, childValue] of Object.entries(value)) {
      result[childKey] = sanitizeNestedAdminData(childValue, childKey, depth + 1);
    }
    return result;
  }
  if (typeof value !== 'string') return value;
  const lowerKey = String(key).toLowerCase();
  if (['image', 'icon', 'iconurl'].includes(lowerKey)) return cleanImageSource(value);
  if (['url', 'link'].includes(lowerKey)) {
    const url = cleanText(value, 2048).replace(/[<>"']/g, '');
    return /^https:\/\//i.test(url) ? url : '';
  }
  return cleanMarkupText(value, 5000);
}

function sanitizeProducts(value) {
  const isArray = Array.isArray(value);
  const entries = isArray ? value.map((item, index) => [String(index), item]) : Object.entries(value || {});
  const result = isArray ? [] : {};
  for (const [key, product] of entries) {
    if (!product || typeof product !== 'object') continue;
    const idNumber = Math.floor(normalizeNumber(product.id));
    if (idNumber < 1) continue;
    const safe = {
      id: idNumber,
      name: cleanMarkupText(product.name, 120),
      category: cleanMarkupText(product.category, 100),
      description: cleanMarkupText(product.description, 2000),
      price: Math.max(0, normalizeNumber(product.price)),
      stock: Math.max(0, Math.floor(normalizeNumber(product.stock))),
      status: product.status === 'Active' ? 'Active' : 'Inactive',
      image: cleanImageSource(product.image),
      images: normalizeList(product.images).map(cleanImageSource).filter(Boolean).slice(0, 6),
      sizes: normalizeList(product.sizes).map((v) => cleanMarkupText(v, 40)).filter(Boolean).slice(0, 12),
      colors: normalizeList(product.colors).map((v) => cleanMarkupText(v, 40)).filter(Boolean).slice(0, 12)
    };
    if (!safe.images.length && safe.image) safe.images = [safe.image];
    if (!safe.image && safe.images.length) safe.image = safe.images[0];
    if (isArray) result.push(safe); else result[key] = safe;
  }
  return result;
}

function sanitizeCoupons(value) {
  const isArray = Array.isArray(value);
  const entries = isArray ? value.map((item, index) => [String(index), item]) : Object.entries(value || {});
  const result = isArray ? [] : {};
  for (const [key, coupon] of entries) {
    if (!coupon || typeof coupon !== 'object') continue;
    const safe = {
      id: Math.max(0, Math.floor(normalizeNumber(coupon.id))),
      code: cleanText(coupon.code, 50).toUpperCase().replace(/[^A-Z0-9_-]/g, ''),
      type: coupon.type === 'percentage' ? 'percentage' : 'fixed',
      value: Math.max(0, normalizeNumber(coupon.value)),
      minOrder: Math.max(0, normalizeNumber(coupon.minOrder)),
      limit: Math.max(0, Math.floor(normalizeNumber(coupon.limit))),
      used: Math.max(0, Math.floor(normalizeNumber(coupon.used))),
      status: coupon.status === 'active' ? 'active' : 'inactive'
    };
    if (isArray) result.push(safe); else result[key] = safe;
  }
  return result;
}

async function requireVerifiedCustomer(request) {
  if (!request.auth?.uid || !request.auth?.token?.email) {
    throw new HttpsError('unauthenticated', 'Sign in before placing an order.');
  }
  if (request.auth.token.email_verified !== true) {
    throw new HttpsError('permission-denied', 'Verify your email before placing an order.');
  }
  return { uid: request.auth.uid, email: cleanEmail(request.auth.token.email) };
}

async function getEmployeeForRequest(request, minimumRole = 1) {
  if (!request.auth?.uid || !request.auth?.token?.email) {
    throw new HttpsError('unauthenticated', 'Employee authentication is required.');
  }
  if (request.auth.token.email_verified !== true) {
    throw new HttpsError('permission-denied', 'A verified employee email is required.');
  }

  const userRecord = await auth.getUser(request.auth.uid);
  const tokensValidAfterMs = userRecord.tokensValidAfterTime ? Date.parse(userRecord.tokensValidAfterTime) : 0;
  const authTimeMs = Math.max(0, normalizeNumber(request.auth.token.auth_time)) * 1000;
  if (tokensValidAfterMs && authTimeMs < tokensValidAfterMs) {
    throw new HttpsError('unauthenticated', 'This employee session has been revoked. Sign in again.');
  }

  const email = String(request.auth.token.email).toLowerCase();
  const snap = await db.ref(`employeeRoles/${sanitizeEmail(email)}`).once('value');
  const employee = snap.val();

  if (!employee || !ROLE_LEVEL[employee.role] || ROLE_LEVEL[employee.role] < minimumRole) {
    throw new HttpsError('permission-denied', 'You do not have permission to perform this action.');
  }

  if (Object.prototype.hasOwnProperty.call(employee, 'password')) {
    await snap.ref.child('password').remove();
  }
  return {
    uid: request.auth.uid,
    email,
    name: cleanText(employee.name || email, 100),
    role: employee.role,
    specialAccess: employee.specialAccess || {}
  };
}

function getProductEntries(productsRaw) {
  if (!productsRaw) return [];
  return Object.entries(productsRaw).filter(([, value]) => value && typeof value === 'object');
}

function getDiscountedUnitPrice(product, productDiscounts) {
  let price = Math.max(0, normalizeNumber(product.price));
  const discount = productDiscounts.find((d) =>
    String(d.productId) === String(product.id) && d.status === 'active'
  );

  if (!discount) return price;
  const value = Math.max(0, normalizeNumber(discount.value));
  if (discount.type === 'percentage') {
    price -= price * Math.min(value, 100) / 100;
  } else {
    price -= value;
  }
  return Math.max(0, price);
}

function calculateQuote(root, requestedItems, couponCode) {
  if (!Array.isArray(requestedItems) || requestedItems.length === 0) {
    throw new HttpsError('invalid-argument', 'Your cart is empty.');
  }

  const productEntries = getProductEntries(root.products);
  const productDiscounts = normalizeList(root.productDiscounts);
  const thresholdDiscounts = normalizeList(root.orderDiscounts);
  const coupons = normalizeList(root.coupons);
  const settings = root.storeSettings || {};
  const normalizedItems = [];

  for (const requested of requestedItems) {
    const productId = requested?.id;
    const quantity = Math.floor(normalizeNumber(requested?.quantity));
    if (!productId || quantity < 1 || quantity > 99) {
      throw new HttpsError('invalid-argument', 'Invalid cart quantity.');
    }

    const entry = productEntries.find(([, p]) => String(p.id) === String(productId));
    if (!entry) throw new HttpsError('not-found', 'A product in your cart is no longer available.');

    const [storageKey, product] = entry;
    if (product.status !== 'Active') {
      throw new HttpsError('failed-precondition', `${cleanText(product.name, 100)} is not available for sale.`);
    }

    const stock = Math.max(0, Math.floor(normalizeNumber(product.stock)));
    if (quantity > stock) {
      throw new HttpsError('failed-precondition', `Only ${stock} of ${cleanText(product.name, 100)} are available.`);
    }

    const requestedSize = cleanText(requested?.size, 40);
    const requestedColor = cleanText(requested?.color, 40);
    const sizes = normalizeList(product.sizes).map((v) => cleanText(v, 40));
    const colors = normalizeList(product.colors).map((v) => cleanText(v, 40));
    if (sizes.length && !sizes.includes(requestedSize)) throw new HttpsError('failed-precondition', `Choose a valid size for ${cleanText(product.name, 100)}.`);
    if (colors.length && !colors.includes(requestedColor)) throw new HttpsError('failed-precondition', `Choose a valid color for ${cleanText(product.name, 100)}.`);
    const unitPrice = getDiscountedUnitPrice(product, productDiscounts);
    normalizedItems.push({ storageKey, id: product.id, name: cleanText(product.name, 120), quantity, size: sizes.length ? requestedSize : '', color: colors.length ? requestedColor : '', unitPrice, lineTotal: unitPrice * quantity });
  }

  const subtotal = normalizedItems.reduce((sum, item) => sum + item.lineTotal, 0);
  const activeThresholds = thresholdDiscounts
    .filter((d) => d.status === 'active' && subtotal >= normalizeNumber(d.threshold))
    .sort((a, b) => normalizeNumber(b.threshold) - normalizeNumber(a.threshold));

  let thresholdDiscount = 0;
  const appliedThreshold = activeThresholds[0] || null;
  if (appliedThreshold) {
    const value = Math.max(0, normalizeNumber(appliedThreshold.value));
    thresholdDiscount = appliedThreshold.type === 'percentage'
      ? subtotal * Math.min(value, 100) / 100
      : value;
  }

  thresholdDiscount = Math.min(subtotal, thresholdDiscount);
  const afterThreshold = Math.max(0, subtotal - thresholdDiscount);

  let appliedCoupon = null;
  let couponDiscount = 0;
  const normalizedCouponCode = cleanText(couponCode, 50).toUpperCase();
  if (normalizedCouponCode) {
    appliedCoupon = coupons.find((c) => cleanText(c.code, 50).toUpperCase() === normalizedCouponCode && c.status === 'active') || null;
    if (!appliedCoupon) throw new HttpsError('failed-precondition', 'Invalid coupon code.');

    const minOrder = Math.max(0, normalizeNumber(appliedCoupon.minOrder));
    if (afterThreshold < minOrder) {
      throw new HttpsError('failed-precondition', `This coupon requires a minimum order of EGP ${minOrder.toFixed(2)}.`);
    }

    const limit = normalizeNumber(appliedCoupon.limit, 0);
    const used = normalizeNumber(appliedCoupon.used, 0);
    if (limit > 0 && used >= limit) {
      throw new HttpsError('failed-precondition', 'This coupon has reached its usage limit.');
    }

    const value = Math.max(0, normalizeNumber(appliedCoupon.value));
    couponDiscount = appliedCoupon.type === 'percentage'
      ? afterThreshold * Math.min(value, 100) / 100
      : value;
    couponDiscount = Math.min(afterThreshold, couponDiscount);
  }

  const discountedSubtotal = Math.max(0, afterThreshold - couponDiscount);
  const shippingFee = Math.max(0, normalizeNumber(settings.shippingFee, 50));
  const freeShippingThreshold = Math.max(0, normalizeNumber(settings.freeShippingThreshold, 1000));
  const shipping = discountedSubtotal >= freeShippingThreshold ? 0 : shippingFee;
  const processingFee = Math.max(0, normalizeNumber(settings.processingFee));
  const serviceFee = Math.max(0, normalizeNumber(settings.serviceFee));
  const taxableAmount = discountedSubtotal + shipping + processingFee + serviceFee;
  const taxRate = Math.max(0, Math.min(100, normalizeNumber(settings.taxRate, 14)));
  const tax = settings.taxEnabled === false ? 0 : taxableAmount * taxRate / 100;
  const total = taxableAmount + tax;

  return {
    items: normalizedItems,
    subtotal,
    thresholdDiscount,
    couponDiscount,
    discountedSubtotal,
    shipping,
    processingFee,
    serviceFee,
    tax,
    total,
    taxRate,
    coupon: appliedCoupon ? cleanText(appliedCoupon.code, 50).toUpperCase() : null
  };
}

exports.getEmployeeProfile = onCall(async (request) => {
  return getEmployeeForRequest(request, 1);
});


exports.revokeEmployeeSession = onCall(async (request) => {
  const employee = await getEmployeeForRequest(request, 1);
  await auth.revokeRefreshTokens(employee.uid);
  return { ok: true };
});

exports.getAdminData = onCall(async (request) => {
  const employee = await getEmployeeForRequest(request, 1);
  const snap = await db.ref('/').once('value');
  const root = snap.val() || {};

  if (ROLE_LEVEL[employee.role] >= 5) {
    const cleanup = {};
    for (const [key, value] of Object.entries(root.employeeRoles || {})) {
      if (value && Object.prototype.hasOwnProperty.call(value, 'password')) {
        cleanup[`employeeRoles/${key}/password`] = null;
      }
    }
    for (const [key, value] of Object.entries(root.users || {})) {
      if (value && Object.prototype.hasOwnProperty.call(value, 'password')) {
        cleanup[`users/${key}/password`] = null;
      }
    }
    if (Object.keys(cleanup).length) await db.ref('/').update(cleanup);
  }

  const response = {
    orders: normalizeList(root.orders),
    employeeRoles: {},
    users: {},
    coupons: []
  };

  if (ROLE_LEVEL[employee.role] >= 5) {
    for (const [key, value] of Object.entries(root.employeeRoles || {})) {
      response.employeeRoles[key] = {
        email: cleanText(value.email, 254),
        name: cleanText(value.name, 100),
        role: value.role,
        specialAccess: value.specialAccess || {}
      };
    }
  }

  if (ROLE_LEVEL[employee.role] >= 3 || employee.specialAccess?.promotions) {
    response.coupons = normalizeList(sanitizeCoupons(root.coupons));
  }

  if (ROLE_LEVEL[employee.role] >= 5) {
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

  return response;
});

exports.adminWrite = onCall(async (request) => {
  const path = cleanText(request.data?.path, 100);
  const data = request.data?.data;

  const permissions = {
    products: 1,
    categories: 3,
    announcements: 3,
    coupons: 3,
    productDiscounts: 3,
    orderDiscounts: 3,
    storeSettings: 3,
    paymentMethods: 3,
    socialLinks: 3,
    employeeRoles: 5
  };

  const minimumRole = permissions[path];
  if (!minimumRole) throw new HttpsError('permission-denied', 'This data path cannot be written from the client.');
  const employee = await getEmployeeForRequest(request, 1);
  const roleLevel = ROLE_LEVEL[employee.role] || 0;
  const specialAllowed = ['announcements', 'coupons', 'productDiscounts', 'orderDiscounts'].includes(path) && employee.specialAccess?.promotions;
  const settingsAllowed = ['categories', 'storeSettings', 'paymentMethods', 'socialLinks'].includes(path) && employee.specialAccess?.settings;
  if (roleLevel < minimumRole && !specialAllowed && !settingsAllowed) {
    throw new HttpsError('permission-denied', 'You do not have permission to modify this data.');
  }

  let dataToSave = data;
  if (path === 'products') dataToSave = sanitizeProducts(data);
  else if (path === 'coupons') dataToSave = sanitizeCoupons(data);
  else if (path !== 'employeeRoles') dataToSave = sanitizeNestedAdminData(data);
  if (path === 'employeeRoles' && data && typeof data === 'object') {
    dataToSave = {};
    for (const [email, profile] of Object.entries(data)) {
      const normalizedEmail = cleanEmail(profile.email || email.replace(/,/g, '.'));
      dataToSave[sanitizeEmail(normalizedEmail)] = {
        email: normalizedEmail,
        name: cleanText(profile.name, 100),
        role: ROLE_LEVEL[profile.role] ? profile.role : 'Employee',
        specialAccess: profile.specialAccess || {}
      };
    }
  }

  await db.ref(path).set(dataToSave);
  return { ok: true };
});

exports.updateOrder = onCall(async (request) => {
  await getEmployeeForRequest(request, 1);
  const orderId = cleanText(request.data?.id, 80);
  if (!orderId) throw new HttpsError('invalid-argument', 'Order ID is required.');

  const snap = await db.ref(`orders/${orderId}`).once('value');
  if (!snap.exists()) throw new HttpsError('not-found', 'Order not found.');

  const allowedStatuses = new Set(['pending', 'processing', 'shipped', 'delivered', 'paid', 'fulfilled', 'cancelled']);
  const status = cleanText(request.data?.status, 30).toLowerCase();
  if (!allowedStatuses.has(status)) throw new HttpsError('invalid-argument', 'Invalid order status.');

  await db.ref(`orders/${orderId}`).update({
    customer: cleanText(request.data?.customer, 120),
    email: cleanEmail(request.data?.email),
    status,
    notes: cleanText(request.data?.notes, 2000),
    updatedAt: new Date().toISOString(),
    updatedBy: request.auth.token.email || request.auth.uid
  });

  return { ok: true };
});

exports.quoteOrder = onCall(async (request) => {
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
  return {
    subtotal: quote.subtotal,
    thresholdDiscount: quote.thresholdDiscount,
    couponDiscount: quote.couponDiscount,
    shipping: quote.shipping,
    processingFee: quote.processingFee,
    serviceFee: quote.serviceFee,
    tax: quote.tax,
    taxRate: quote.taxRate,
    total: quote.total,
    coupon: quote.coupon
  };
});

exports.getCustomerOrders = onCall(async (request) => {
  if (!request.auth?.uid) throw new HttpsError('unauthenticated', 'Customer authentication is required.');
  const uid = request.auth.uid;
  const snap = await db.ref('orders').once('value');
  const orders = normalizeList(snap.val()).filter((order) => order?.customerUid === uid).sort((a, z) => String(z.createdAt || z.date || '').localeCompare(String(a.createdAt || a.date || ''))).slice(0, 50).map((order) => ({
    id: cleanText(order.id, 80),
    createdAt: order.createdAt || order.date || null,
    status: cleanText(order.status, 30),
    total: Math.max(0, normalizeNumber(order.total)),
    itemCount: normalizeList(order.items).reduce((sum, item) => sum + Math.max(0, Math.floor(normalizeNumber(item.qty))), 0)
  }));
  return { orders };
});

exports.createOrder = onCall(async (request) => {
  const authenticatedCustomer = await requireVerifiedCustomer(request);
  const paymentMethod = cleanText(request.data?.paymentMethod, 40).toLowerCase();
  if (paymentMethod !== 'cod') {
    throw new HttpsError('failed-precondition', 'Online payment is temporarily disabled until server-side payment verification is configured.');
  }

  const submittedEmail = cleanEmail(request.data?.customer?.email);
  if (submittedEmail !== authenticatedCustomer.email) {
    throw new HttpsError('permission-denied', 'Order email must match the authenticated account.');
  }

  const customer = {
    name: cleanText(request.data?.customer?.name, 120),
    email: authenticatedCustomer.email,
    phone: cleanPhone(request.data?.customer?.phone),
    address: cleanText(request.data?.customer?.address, 250),
    houseNumber: cleanText(request.data?.customer?.houseNumber, 80),
    floor: cleanText(request.data?.customer?.floor, 80),
    city: cleanText(request.data?.customer?.city, 100),
    postal: cleanText(request.data?.customer?.postal, 30),
    notes: cleanText(request.data?.customer?.notes, 1000)
  };

  if (!customer.name || !customer.phone || !customer.address || !customer.houseNumber || !customer.city) {
    throw new HttpsError('invalid-argument', 'Complete shipping information is required.');
  }

  let committedOrder = null;
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
    root.counters.orderNumbers = root.counters.orderNumbers || {};
    const nextNumber = Math.max(0, Math.floor(normalizeNumber(root.counters.orderNumbers[year]))) + 1;
    root.counters.orderNumbers[year] = nextNumber;
    const orderId = `KEM-${year}-${String(nextNumber).padStart(6, '0')}`;

    for (const item of quote.items) {
      const product = root.products[item.storageKey];
      const currentStock = Math.max(0, Math.floor(normalizeNumber(product.stock)));
      if (item.quantity > currentStock) return;
      product.stock = currentStock - item.quantity;
    }

    if (quote.coupon) {
      for (const [key, coupon] of Object.entries(root.coupons || {})) {
        if (cleanText(coupon?.code, 50).toUpperCase() === quote.coupon) {
          root.coupons[key].used = normalizeNumber(coupon.used, 0) + 1;
          break;
        }
      }
    }

    root.orders = root.orders || {};
    const order = {
      id: orderId,
      customerUid: authenticatedCustomer.uid,
      customer: customer.name,
      email: customer.email,
      phone: customer.phone,
      date: new Date().toISOString().split('T')[0],
      createdAt: new Date().toISOString(),
      items: quote.items.map((item) => ({
        productId: item.id,
        product: item.name,
        qty: item.quantity,
        price: item.unitPrice,
        size: item.size || '',
        color: item.color || ''
      })),
      subtotal: quote.subtotal,
      thresholdDiscount: quote.thresholdDiscount,
      couponDiscount: quote.couponDiscount,
      shipping: quote.shipping,
      processingFee: quote.processingFee,
      serviceFee: quote.serviceFee,
      tax: quote.tax,
      total: quote.total,
      coupon: quote.coupon,
      status: 'pending',
      paymentMethod: 'cod',
      paymentStatus: 'cod_pending',
      notes: cleanText(`Address: ${customer.address}, House/Building: ${customer.houseNumber}${customer.floor ? `, Floor: ${customer.floor}` : ''}, ${customer.city}${customer.postal ? ` - ${customer.postal}` : ''}\nPhone: ${customer.phone}\nEmail: ${customer.email}\nCustomer notes: ${customer.notes}`, 2500)
    };

    root.orders[orderId] = order;

    {
      root.users = root.users || {};
      const uid = authenticatedCustomer.uid;
      const existing = root.users[uid] || {};
      const orderHistory = Array.isArray(existing.orderHistory) ? existing.orderHistory.slice(-49) : [];
      orderHistory.push(orderId);
      root.users[uid] = {
        ...existing,
        email: customer.email,
        name: customer.name,
        phone: customer.phone,
        orderHistory,
        lastLogin: existing.lastLogin || new Date().toISOString(),
        registeredDate: existing.registeredDate || new Date().toISOString()
      };
    }

    committedOrder = order;
    return root;
  }, undefined, false);

  if (!transaction.committed || !committedOrder) {
    if (abortReason) throw new HttpsError('failed-precondition', abortReason);
    throw new HttpsError('aborted', 'The order could not be committed because stock changed. Please review your cart and try again.');
  }

  return {
    orderId: committedOrder.id,
    total: committedOrder.total,
    subtotal: committedOrder.subtotal,
    thresholdDiscount: committedOrder.thresholdDiscount,
    couponDiscount: committedOrder.couponDiscount,
    shipping: committedOrder.shipping,
    tax: committedOrder.tax,
    paymentMethod: committedOrder.paymentMethod,
    status: committedOrder.status
  };
});

exports.createEmployeeResetLink = onCall(async (request) => {
  await getEmployeeForRequest(request, 5);
  const email = cleanEmail(request.data?.email);
  try {
    await auth.getUserByEmail(email);
  } catch (error) {
    if (error.code === 'auth/user-not-found') {
      await auth.createUser({ email, emailVerified: false });
    } else {
      throw error;
    }
  }
  const link = await auth.generatePasswordResetLink(email);
  return { link };
});
