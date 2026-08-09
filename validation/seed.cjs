const { initializeApp } = require('firebase-admin/app');
const { getAuth } = require('firebase-admin/auth');
const { getDatabase } = require('firebase-admin/database');

const projectId = 'demo-kem-validation';
initializeApp({
  projectId,
  databaseURL: `http://127.0.0.1:9000?ns=${projectId}-default-rtdb`,
  storageBucket: `${projectId}.firebasestorage.app`,
});

const auth = getAuth();
const db = getDatabase();
const password = 'Test1234!';

async function ensureUser(uid, email, emailVerified = true, displayName = '') {
  try { await auth.deleteUser(uid); } catch (_) {}
  return auth.createUser({ uid, email, emailVerified, password, displayName });
}

(async () => {
  await Promise.all([
    ensureUser('customer-1', 'customer@example.com', true, 'Customer One'),
    ensureUser('customer-2', 'other@example.com', true, 'Other Customer'),
    ensureUser('customer-unverified', 'unverified@example.com', false, 'Unverified Customer'),
    ensureUser('employee-1', 'employee@example.com', true, 'Employee One'),
    ensureUser('manager-1', 'manager@example.com', true, 'Manager One'),
    ensureUser('ceo-1', 'ceo@example.com', true, 'CEO One'),
    ensureUser('employee-unverified', 'unverifiedemployee@example.com', false, 'Unverified Employee'),
  ]);

  const seed = {
    products: [
      {
        id: 1,
        name: 'Validation Alpha Tee',
        category: 'Tees',
        description: 'Integration smoke test product alpha',
        price: 500,
        stock: 5,
        status: 'Active',
        image: 'logo-240.png',
        images: ['logo-240.png', 'favicon-64.png'],
        sizes: ['M', 'L'],
        colors: ['Black', 'White'],
      },
      {
        id: 2,
        name: 'Validation Beta Hoodie',
        category: 'Hoodies',
        description: 'Integration smoke test product beta',
        price: 900,
        stock: 3,
        status: 'Active',
        image: 'logo-240.png',
        images: ['logo-240.png'],
        sizes: ['L'],
        colors: ['Black'],
      },
    ],
    categories: [
      { id: 1, name: 'Tees', description: 'Validation tees' },
      { id: 2, name: 'Hoodies', description: 'Validation hoodies' },
    ],
    coupons: [
      { id: 1, code: 'SMOKE10', type: 'percentage', value: 10, minOrder: 0, limit: 5, used: 0, status: 'active' },
      { id: 2, code: 'USEDUP', type: 'fixed', value: 50, minOrder: 0, limit: 1, used: 1, status: 'active' },
    ],
    storeSettings: {
      storeName: 'KEM Validation',
      shippingFee: 50,
      freeShippingThreshold: 1000,
      taxRate: 14,
      taxEnabled: true,
      processingFee: 0,
      serviceFee: 0,
      colorTheme: { primary: '#000000', accent: '#FF3366', secondary: '#00FF99', background: '#FAFAFA' },
      aboutSection: { title: 'Validation About', content: 'Validation environment only.', stats: [] },
    },
    paymentMethods: [
      { id: 1, name: 'Cash on Delivery', type: 'cod', enabled: true, instructions: 'Pay on delivery.' },
    ],
    productDiscounts: [],
    orderDiscounts: [],
    announcements: [],
    socialLinks: [],
    employeeRoles: {
      'employee@example,com': { email: 'employee@example.com', name: 'Employee One', role: 'Employee', specialAccess: {} },
      'manager@example,com': { email: 'manager@example.com', name: 'Manager One', role: 'Manager', specialAccess: { promotions: true, settings: true } },
      'ceo@example,com': { email: 'ceo@example.com', name: 'CEO One', role: 'CEO', specialAccess: { promotions: true, settings: true } },
      'unverifiedemployee@example,com': { email: 'unverifiedemployee@example.com', name: 'Unverified Employee', role: 'Employee', specialAccess: {} },
    },
    users: {
      'customer-1': {
        email: 'customer@example.com',
        name: 'Customer One',
        phone: '+201000000001',
        savedAddresses: [
          { id: 1, label: 'Home', address: '1 Validation Street', houseNumber: '10', floor: '2', city: 'Cairo', postal: '11511', isDefault: true },
        ],
        orderHistory: [],
        registeredDate: new Date().toISOString(),
        lastLogin: new Date().toISOString(),
      },
      'customer-2': { email: 'other@example.com', name: 'Other Customer', phone: '+201000000002', savedAddresses: [], orderHistory: [] },
    },
    orders: {
      'KEM-2026-000001': {
        id: 'KEM-2026-000001', customerUid: 'customer-1', customer: 'Customer One', email: 'customer@example.com', status: 'pending', total: 620, createdAt: '2026-08-09T20:00:00.000Z', items: [{ id: 1, name: 'Validation Alpha Tee', qty: 1, size: 'M', color: 'Black' }],
      },
      'KEM-2026-000002': {
        id: 'KEM-2026-000002', customerUid: 'customer-2', customer: 'Other Customer', email: 'other@example.com', status: 'pending', total: 1000, createdAt: '2026-08-09T21:00:00.000Z', items: [{ id: 2, name: 'Validation Beta Hoodie', qty: 1, size: 'L', color: 'Black' }],
      },
    },
    counters: { orderNumbers: { '2026': 2 } },
    security: { orderRate: {} },
  };

  await db.ref('/').set(seed);
  console.log('Seeded isolated auth/database emulator data');
})().catch((error) => { console.error(error); process.exit(1); });
