from pathlib import Path
import json
import re


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Missing marker: {label}")
    return text.replace(old, new, 1)


# ---------------- backend ----------------
p = Path("functions/index.js")
s = p.read_text()

clean_phone = """function cleanPhone(value) {
  return cleanText(value, 30).replace(/[^0-9+()\\-\\s]/g, '');
}
"""
if "function cleanMarkupText(" not in s:
    helpers = clean_phone + r'''

function cleanMarkupText(value, maxLength = 500) {
  return cleanText(value, maxLength).replace(/[<>"']/g, '');
}

function cleanImageSource(value) {
  const source = cleanText(value, 5 * 1024 * 1024);
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
    const safe = {
      id: idNumber > 0 ? idNumber : cleanMarkupText(product.id, 80),
      name: cleanMarkupText(product.name, 120),
      category: cleanMarkupText(product.category, 100),
      description: cleanMarkupText(product.description, 2000),
      price: Math.max(0, normalizeNumber(product.price)),
      stock: Math.max(0, Math.floor(normalizeNumber(product.stock))),
      status: product.status === 'Active' ? 'Active' : 'Inactive',
      image: cleanImageSource(product.image)
    };
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
'''
    s = replace_once(s, clean_phone, helpers, "backend helper insertion")

old = """  if (request.auth.token.email_verified !== true) {
    throw new HttpsError('permission-denied', 'A verified employee email is required.');
  }

  const email = String(request.auth.token.email).toLowerCase();
"""
new = """  if (request.auth.token.email_verified !== true) {
    throw new HttpsError('permission-denied', 'A verified employee email is required.');
  }

  const userRecord = await auth.getUser(request.auth.uid);
  const tokensValidAfterMs = userRecord.tokensValidAfterTime ? Date.parse(userRecord.tokensValidAfterTime) : 0;
  const authTimeMs = Math.max(0, normalizeNumber(request.auth.token.auth_time)) * 1000;
  if (tokensValidAfterMs && authTimeMs < tokensValidAfterMs) {
    throw new HttpsError('unauthenticated', 'This employee session has been revoked. Sign in again.');
  }

  const email = String(request.auth.token.email).toLowerCase();
"""
if "This employee session has been revoked" not in s:
    s = replace_once(s, old, new, "employee token revocation check")

marker = """exports.getEmployeeProfile = onCall(async (request) => {
  return getEmployeeForRequest(request, 1);
});
"""
if "exports.revokeEmployeeSession" not in s:
    s = replace_once(s, marker, marker + """

exports.revokeEmployeeSession = onCall(async (request) => {
  const employee = await getEmployeeForRequest(request, 1);
  await auth.revokeRefreshTokens(employee.uid);
  return { ok: true };
});
""", "employee revocation callable")

old = """  const response = {
    orders: normalizeList(root.orders),
    employeeRoles: {},
    users: {}
  };
"""
if "coupons: []" not in s:
    s = replace_once(s, old, """  const response = {
    orders: normalizeList(root.orders),
    employeeRoles: {},
    users: {},
    coupons: []
  };
""", "admin coupon response")

old = """  if (ROLE_LEVEL[employee.role] >= 5) {
    for (const [key, value] of Object.entries(root.employeeRoles || {})) {
      response.employeeRoles[key] = {
        email: cleanText(value.email, 254),
        name: cleanText(value.name, 100),
        role: value.role,
        specialAccess: value.specialAccess || {}
      };
    }
  }

  for (const [key, value] of Object.entries(root.users || {})) {
"""
if "response.coupons = normalizeList(sanitizeCoupons" not in s:
    new = old.replace("\n\n  for (const [key, value]", """

  if (ROLE_LEVEL[employee.role] >= 3 || employee.specialAccess?.promotions) {
    response.coupons = normalizeList(sanitizeCoupons(root.coupons));
  }

  for (const [key, value]""")
    s = replace_once(s, old, new, "secure admin coupon load")

old = """  const minimumRole = permissions[path];
  if (!minimumRole) throw new HttpsError('permission-denied', 'This data path cannot be written from the client.');
  await getEmployeeForRequest(request, minimumRole);

  let dataToSave = data;
"""
if "const specialAllowed =" not in s:
    new = """  const minimumRole = permissions[path];
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
"""
    s = replace_once(s, old, new, "admin write sanitization")

s = s.replace("const allowedStatuses = new Set(['pending', 'paid', 'fulfilled', 'cancelled']);",
              "const allowedStatuses = new Set(['pending', 'processing', 'shipped', 'delivered', 'paid', 'fulfilled', 'cancelled']);")

old = """exports.createOrder = onCall(async (request) => {
  const paymentMethod = cleanText(request.data?.paymentMethod, 40).toLowerCase();
"""
if "const authenticatedCustomer = await requireVerifiedCustomer(request);" not in s:
    s = replace_once(s, old, """exports.createOrder = onCall(async (request) => {
  const authenticatedCustomer = await requireVerifiedCustomer(request);
  const paymentMethod = cleanText(request.data?.paymentMethod, 40).toLowerCase();
""", "verified customer order gate")

old = """  const customer = {
    name: cleanText(request.data?.customer?.name, 120),
    email: cleanEmail(request.data?.customer?.email),
"""
if "Order email must match the authenticated account." not in s:
    s = replace_once(s, old, """  const submittedEmail = cleanEmail(request.data?.customer?.email);
  if (submittedEmail !== authenticatedCustomer.email) {
    throw new HttpsError('permission-denied', 'Order email must match the authenticated account.');
  }

  const customer = {
    name: cleanText(request.data?.customer?.name, 120),
    email: authenticatedCustomer.email,
""", "order email binding")

old = """    if (request.auth?.uid) {
      root.users = root.users || {};
      const uid = request.auth.uid;
      const existing = root.users[uid] || {};
"""
if old in s:
    s = s.replace(old, """    {
      root.users = root.users || {};
      const uid = authenticatedCustomer.uid;
      const existing = root.users[uid] || {};
""", 1)

p.write_text(s)

# ---------------- rules ----------------
rp = Path("database.rules.json")
rules = json.loads(rp.read_text())
rr = rules["rules"]
rr["coupons"][".read"] = False
u = rr["users"]["$uid"]
u["email"] = {".validate": "newData.isString() && newData.val() === auth.token.email"}
u["name"] = {".validate": "!newData.exists() || (newData.isString() && newData.val().length <= 120)"}
u["phone"] = {".validate": "!newData.exists() || (newData.isString() && newData.val().length <= 30)"}
u["picture"] = {".validate": "!newData.exists() || (newData.isString() && newData.val().length <= 2048)"}
u["googleId"] = {".validate": "!newData.exists() || (newData.isString() && newData.val().length <= 200)"}
u["savedAddresses"] = {".validate": "!newData.exists() || newData.hasChildren()"}
u["orderHistory"] = {".validate": "newData.val() === data.val()"}
u["registeredDate"] = {".validate": "!data.exists() || newData.val() === data.val()"}
u["lastLogin"] = {".validate": "!newData.exists() || (newData.isString() && newData.val().length <= 40)"}
u["$other"] = {".validate": False}
rp.write_text(json.dumps(rules, indent=2) + "\n")

# ---------------- frontend ----------------
hp = Path("index.html")
h = hp.read_text()

h = h.replace(
    "const [productsData, categoriesData, announcementsData, couponsData, productDiscountsData,\n                orderDiscountsData, storeSettingsData, paymentMethodsData, socialLinksData] = await Promise.all([",
    "const [productsData, categoriesData, announcementsData, productDiscountsData,\n                orderDiscountsData, storeSettingsData, paymentMethodsData, socialLinksData] = await Promise.all([",
    1,
)
h = h.replace("                readPublicPath('coupons'),\n", "", 1)
h = h.replace("            if (couponsData) coupons = firebaseList(couponsData);\n", "", 1)
h = h.replace("                ['coupons', data => { coupons = firebaseList(data); }],\n", "", 1)

old = """            orders = firebaseList(response.data.orders);
            users = response.data.users || {};
"""
if "if (Array.isArray(response.data.coupons)) coupons = response.data.coupons;" not in h:
    h = replace_once(h, old, old + "            if (Array.isArray(response.data.coupons)) coupons = response.data.coupons;\n", "frontend admin coupons")

pat = re.compile(r"^[ \t]*function applyCouponCode\(\) \{.*?^[ \t]*\}\n\n[ \t]*function removeCouponCode", re.M | re.S)
ms = list(pat.finditer(h))
if len(ms) != 1:
    raise SystemExit(f"applyCouponCode targets={len(ms)}")
coupon_fn = """        async function applyCouponCode() {
            const code = document.getElementById('couponInput').value.trim().toUpperCase();
            if (!code) return;
            if (!auth?.currentUser) {
                alert('Please sign in and verify your email before applying a coupon.');
                openAuthModal();
                return;
            }
            try {
                await auth.currentUser.reload();
                await auth.currentUser.getIdToken(true);
                if (!auth.currentUser.emailVerified) {
                    alert('Please verify your email before applying a coupon.');
                    return;
                }
                const quoteOrder = cloudFunctions.httpsCallable('quoteOrder');
                const response = await quoteOrder({
                    items: cart.map(item => ({ id: item.id, quantity: item.quantity })),
                    couponCode: code
                });
                if (!response.data.coupon) throw new Error('Invalid coupon code.');
                appliedCoupon = {
                    code: response.data.coupon,
                    type: 'fixed',
                    value: Number(response.data.couponDiscount) || 0,
                    minOrder: 0,
                    serverValidated: true
                };
                renderCart();
            } catch (error) {
                console.error('Coupon validation failed:', error);
                alert(error?.message || 'Invalid coupon code.');
            }
        }

        function removeCouponCode"""
h = h[: ms[0].start()] + coupon_fn + h[ms[0].end() :]

old = """        function updateCartQuantity(index, change) {
            const item = cart[index];
"""
if old in h and "const item = cart[index];\n            if (appliedCoupon) appliedCoupon = null;" not in h:
    h = h.replace(old, """        function updateCartQuantity(index, change) {
            const item = cart[index];
            if (appliedCoupon) appliedCoupon = null;
""", 1)

old = """        async function placeOrder() {
            const form = document.getElementById('checkoutForm');
"""
if "Please sign in before placing an order." not in h:
    h = replace_once(h, old, """        async function placeOrder() {
            if (!auth?.currentUser) {
                alert('Please sign in before placing an order.');
                openAuthModal();
                return;
            }
            await auth.currentUser.reload();
            await auth.currentUser.getIdToken(true);
            if (!auth.currentUser.emailVerified) {
                alert('Please verify your email before placing an order.');
                return;
            }

            const form = document.getElementById('checkoutForm');
""", "frontend verified checkout")

start = h.index("async function logoutEmployee()")
end = h.index("\n        }", start) + len("\n        }")
logout = h[start:end]
if "revokeEmployeeSession" not in logout:
    logout_new = """async function logoutEmployee() {
              const dashboard = document.getElementById('employeeDashboard');
              const mainSite = document.getElementById('mainSite');
              const mainNav = document.getElementById('mainNav');
              currentEmployee = null;
              promotionsUnlocked = false;
              orders = [];
              users = {};
              employeeRoles = {};
              notifications = [];
              unreadNotifications = 0;
              if (dashboard) dashboard.classList.remove('active');
              if (mainSite) mainSite.style.display = 'block';
              if (mainNav) mainNav.style.display = 'flex';
              updateNotificationBadge();

              let revokeError = null;
              try {
                  if (auth?.currentUser && cloudFunctions) {
                      const revokeEmployeeSession = cloudFunctions.httpsCallable('revokeEmployeeSession');
                      await revokeEmployeeSession();
                  }
              } catch (error) {
                  revokeError = error;
                  console.error('Employee server-session revocation failed:', error);
              }

              try {
                  if (auth?.currentUser) await auth.signOut();
                  if (auth?.currentUser) throw new Error('Firebase Authentication session is still active after sign-out.');
                  currentUser = null;
                  updateAuthButton();
              } catch (error) {
                  console.error('Employee logout failed:', error);
                  alert('Unable to securely sign out. Please try again.');
                  throw error;
              }

              if (revokeError) {
                  alert('You are signed out locally, but server-session revocation could not be confirmed. Sign in again before using employee tools.');
              }
          }"""
    h = h[:start] + logout_new + h[end:]

hp.write_text(h)
print("P0 hardening patch complete")
