from pathlib import Path
import re

path = Path('index.html')
text = path.read_text(encoding='utf-8')
original = text


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {count}')
    text = text.replace(old, new, 1)


def replace_region(start, end, replacement, label, last=False):
    global text
    start_pos = text.rfind(start) if last else text.find(start)
    if start_pos < 0:
        raise SystemExit(f'{label}: start marker not found')
    end_pos = text.find(end, start_pos)
    if end_pos < 0:
        raise SystemExit(f'{label}: end marker not found')
    text = text[:start_pos] + replacement + '\n\n        ' + end + text[end_pos + len(end):]


# Customer login must use Firebase Authentication rather than client-side plaintext records.
text = text.replace('<label>Email or Phone</label>', '<label>Email</label>')
text = text.replace('placeholder="your@email.com or +20123456789"', 'placeholder="your@email.com"')

replace_once(
    '        let db, auth, storage;\n        let firebaseInitialized = false;',
    '        let db, auth, storage, cloudFunctions;\n        let firebaseInitialized = false;',
    'firebase declarations'
)

firebase_runtime = r'''        async function initializeFirebase() {
            try {
                if (firebaseConfig.apiKey === "YOUR_API_KEY_HERE") {
                    console.error("Firebase is not configured. Secure production mode cannot start.");
                    return false;
                }

                if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
                db = firebase.database();
                auth = firebase.auth();
                storage = firebase.storage();
                cloudFunctions = firebase.functions();
                firebaseInitialized = true;

                await loadPublicData();
                setupPublicListeners();
                setupAuthStateListener();
                console.log("Firebase secure runtime initialized");
                return true;
            } catch (error) {
                console.error("Firebase initialization error:", error);
                return false;
            }
        }

        // Firebase Data Operations
        function firebaseList(value) {
            if (!value) return [];
            return Array.isArray(value) ? value.filter(Boolean) : Object.values(value).filter(Boolean);
        }

        function escapeHTML(value) {
            return String(value ?? '')
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }

        async function saveToFirebase(path, data) {
            if (!firebaseInitialized || !cloudFunctions) throw new Error('Secure backend is unavailable.');
            if (!currentEmployee) throw new Error('Employee authentication is required.');
            const adminWrite = cloudFunctions.httpsCallable('adminWrite');
            await adminWrite({ path, data });
        }

        async function readPublicPath(path) {
            if (!firebaseInitialized) return null;
            const snapshot = await db.ref(path).once('value');
            return snapshot.val();
        }

        async function loadPublicData() {
            const [productsData, categoriesData, announcementsData, couponsData, productDiscountsData,
                orderDiscountsData, storeSettingsData, paymentMethodsData, socialLinksData] = await Promise.all([
                readPublicPath('products'),
                readPublicPath('categories'),
                readPublicPath('announcements'),
                readPublicPath('coupons'),
                readPublicPath('productDiscounts'),
                readPublicPath('orderDiscounts'),
                readPublicPath('storeSettings'),
                readPublicPath('paymentMethods'),
                readPublicPath('socialLinks')
            ]);

            if (productsData) products = firebaseList(productsData);
            if (categoriesData) categories = firebaseList(categoriesData);
            if (announcementsData) announcements = firebaseList(announcementsData);
            if (couponsData) coupons = firebaseList(couponsData);
            if (productDiscountsData) productDiscounts = firebaseList(productDiscountsData);
            if (orderDiscountsData) thresholdDiscounts = firebaseList(orderDiscountsData);
            if (storeSettingsData) storeSettings = storeSettingsData;
            if (paymentMethodsData) paymentMethods = firebaseList(paymentMethodsData);
            if (socialLinksData) socialLinks = firebaseList(socialLinksData);

            nextProductId = Math.max(...products.map(p => Number(p.id) || 0), 0) + 1;
            nextCategoryId = Math.max(...categories.map(c => Number(c.id) || 0), 0) + 1;
            nextPaymentMethodId = Math.max(...paymentMethods.map(p => Number(p.id) || 0), 0) + 1;
            nextSocialLinkId = Math.max(...socialLinks.map(s => Number(s.id) || 0), 0) + 1;
        }

        function setupPublicListeners() {
            if (!firebaseInitialized) return;
            const bindings = [
                ['products', data => { products = firebaseList(data); renderShopProducts(); }],
                ['categories', data => { categories = firebaseList(data); renderCategoriesDropdown(); }],
                ['announcements', data => { announcements = firebaseList(data); }],
                ['coupons', data => { coupons = firebaseList(data); }],
                ['productDiscounts', data => { productDiscounts = firebaseList(data); renderShopProducts(); }],
                ['orderDiscounts', data => { thresholdDiscounts = firebaseList(data); }],
                ['storeSettings', data => { storeSettings = data || storeSettings; }],
                ['paymentMethods', data => { paymentMethods = firebaseList(data); }],
                ['socialLinks', data => { socialLinks = firebaseList(data); renderFooterSocialLinks(); }]
            ];

            bindings.forEach(([path, apply]) => {
                db.ref(path).on('value', snapshot => {
                    const value = snapshot.val();
                    if (value !== null) apply(value);
                });
            });
        }

        async function loadAdminData() {
            if (!cloudFunctions || !currentEmployee) return;
            const getAdminData = cloudFunctions.httpsCallable('getAdminData');
            const response = await getAdminData();
            orders = firebaseList(response.data.orders);
            users = response.data.users || {};
            employeeRoles = {};
            Object.values(response.data.employeeRoles || {}).forEach(profile => {
                if (profile?.email) employeeRoles[profile.email] = profile;
            });
            nextOrderNum = orders.length + 1;
        }

        function setupAuthStateListener() {
            auth.onAuthStateChanged(async user => {
                if (!user) {
                    currentUser = null;
                    users = {};
                    updateAuthButton();
                    return;
                }

                try {
                    const snapshot = await db.ref(`users/${user.uid}`).once('value');
                    const profile = snapshot.val() || {};
                    users = { [user.uid]: profile };
                    currentUser = {
                        uid: user.uid,
                        name: profile.name || user.displayName || user.email?.split('@')[0] || 'Customer',
                        email: user.email || profile.email || '',
                        phone: profile.phone || '',
                        picture: user.photoURL || profile.picture || null
                    };
                    updateAuthButton();
                } catch (error) {
                    console.error('Unable to load customer profile:', error);
                }
            });
        }

        async function saveCurrentUserProfile(profile) {
            const user = auth?.currentUser;
            if (!user) throw new Error('Customer authentication is required.');
            const safeProfile = { ...profile };
            delete safeProfile.password;
            await db.ref(`users/${user.uid}`).update(safeProfile);
        }'''

replace_region(
    '        async function initializeFirebase() {',
    '        // Sample Data Storage',
    firebase_runtime,
    'secure firebase runtime'
)

# Remove the public default employee password from source.
text = re.sub(
    r"        let employeeRoles = \{.*?\n        \};\n        let currentEmployee = null;",
    "        let employeeRoles = {};\n        let currentEmployee = null;",
    text,
    count=1,
    flags=re.S
)

# Employee login must authenticate through Firebase Auth and then obtain a server-authorized role.
replace_region(
    '        function verifyPasscode() {',
    '        function showDashboard() {',
    r'''        async function verifyPasscode() {
            const email = document.getElementById('employeeEmail').value.trim().toLowerCase();
            const password = document.getElementById('employeePassword').value;
            const errorMsg = document.getElementById('errorMessage');
            errorMsg.textContent = '';

            if (!email || !password) {
                errorMsg.textContent = 'Please enter both email and password';
                return;
            }

            try {
                const credential = await auth.signInWithEmailAndPassword(email, password);
                await credential.user.reload();
                if (!credential.user.emailVerified) {
                    await credential.user.sendEmailVerification();
                    throw new Error('Verify your email first. A verification email has been sent.');
                }

                const getEmployeeProfile = cloudFunctions.httpsCallable('getEmployeeProfile');
                const response = await getEmployeeProfile();
                currentEmployee = response.data;
                closeEmployeeModal();
                await showDashboard();
            } catch (error) {
                currentEmployee = null;
                errorMsg.textContent = error?.message || 'Invalid employee credentials';
            }
        }''',
    'employee authentication'
)

# Protected tabs are now UX gates only; authorization is enforced by Cloud Functions.
replace_region(
    '        function switchTab(tabName) {',
    '        // ============================================\n        // FIREBASE CONFIGURATION',
    r'''        function switchTab(tabName) {
            if (!currentEmployee) {
                alert('Employee authentication is required.');
                return;
            }

            const roleLevel = roleHierarchy[currentEmployee.role] || 0;
            const specialAccess = currentEmployee.specialAccess || {};
            const allowed = {
                overview: roleLevel >= 1,
                products: roleLevel >= 1,
                orders: roleLevel >= 1,
                promotions: roleLevel >= 3 || specialAccess.promotions,
                settings: roleLevel >= 3 || specialAccess.settings,
                employees: roleLevel === 5,
                security: roleLevel === 5
            };

            if (!allowed[tabName]) {
                alert('You do not have permission to access this section.');
                return;
            }

            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            const button = document.querySelector(`.tab-btn[onclick="switchTab('${tabName}')"]`);
            if (button) button.classList.add('active');
            const content = document.getElementById(tabName);
            if (content) content.classList.add('active');

            if (tabName === 'promotions') {
                promotionsUnlocked = true;
                document.getElementById('promotionsLocked').style.display = 'none';
                document.getElementById('promotionsContent').style.display = 'block';
                loadPromotions();
            }
        }''',
    'secure tab gating'
)

# Customer Google credential is verified by Firebase instead of merely decoding a JWT in the browser.
replace_region(
    '        async function handleGoogleCredentialResponse(response) {',
    '        // Parse JWT token',
    r'''        async function handleGoogleCredentialResponse(response) {
            try {
                const googleCredential = firebase.auth.GoogleAuthProvider.credential(response.credential);
                const result = await auth.signInWithCredential(googleCredential);
                const user = result.user;
                const profile = {
                    email: user.email || '',
                    name: user.displayName || user.email?.split('@')[0] || 'Customer',
                    phone: user.phoneNumber || '',
                    picture: user.photoURL || null,
                    googleId: user.providerData?.[0]?.uid || null,
                    lastLogin: new Date().toISOString()
                };
                const existing = await db.ref(`users/${user.uid}`).once('value');
                if (!existing.exists()) profile.registeredDate = new Date().toISOString();
                await saveCurrentUserProfile(profile);
                closeAuthModal();
                alert(`Welcome, ${profile.name}!`);
            } catch (error) {
                console.error('Google sign-in failed:', error);
                alert('Google sign-in failed. Please try again.');
            }
        }''',
    'google auth verification'
)

replace_region(
    '        async function handleLogin(event) {',
    '        async function handleSignup(event) {',
    r'''        async function handleLogin(event) {
            event.preventDefault();
            const email = document.getElementById('loginIdentifier').value.trim().toLowerCase();
            const password = document.getElementById('loginPassword').value;
            if (!email || !password) {
                alert('Please fill in all fields');
                return;
            }
            try {
                const credential = await auth.signInWithEmailAndPassword(email, password);
                await saveCurrentUserProfile({
                    email: credential.user.email,
                    name: credential.user.displayName || currentUser?.name || email.split('@')[0],
                    lastLogin: new Date().toISOString()
                });
                closeAuthModal();
                document.getElementById('loginForm').reset();
            } catch (error) {
                console.error('Login failed:', error);
                alert('Unable to sign in with those credentials.');
            }
        }''',
    'customer login'
)

replace_region(
    '        async function handleSignup(event) {',
    '        function handleForgotPassword() {',
    r'''        async function handleSignup(event) {
            event.preventDefault();
            const name = document.getElementById('signupName').value.trim();
            const email = document.getElementById('signupEmail').value.trim().toLowerCase();
            const phone = document.getElementById('signupPhone').value.trim();
            const password = document.getElementById('signupPassword').value;

            if (!name || !email || !password) {
                alert('Please fill in all required fields');
                return;
            }
            if (password.length < 6) {
                alert('Password must be at least 6 characters');
                return;
            }

            try {
                const credential = await auth.createUserWithEmailAndPassword(email, password);
                await credential.user.updateProfile({ displayName: name });
                await saveCurrentUserProfile({
                    email,
                    name,
                    phone,
                    picture: null,
                    savedAddresses: [],
                    orderHistory: [],
                    registeredDate: new Date().toISOString(),
                    lastLogin: new Date().toISOString()
                });
                await credential.user.sendEmailVerification();
                closeAuthModal();
                document.getElementById('signupForm').reset();
                alert(`Welcome to KEM, ${name}! A verification email has been sent.`);
            } catch (error) {
                console.error('Signup failed:', error);
                alert(error?.message || 'Unable to create your account.');
            }
        }''',
    'customer signup'
)

replace_region(
    '        function handleForgotPassword() {',
    '        function updateAuthButton() {',
    r'''        async function handleForgotPassword() {
            const email = prompt('Enter your email address to reset your password:');
            if (!email) return;
            try {
                await auth.sendPasswordResetEmail(email.trim().toLowerCase());
                alert('If the account exists, a password reset email has been sent.');
            } catch (error) {
                console.error('Password reset failed:', error);
                alert('Unable to start password reset. Please check the address and try again.');
            }
        }''',
    'password reset'
)

text = re.sub(
    r"        function logoutUser\(\) \{.*?\n        \}",
    r'''        async function logoutUser() {
            currentUser = null;
            currentEmployee = null;
            if (auth) await auth.signOut();
            updateAuthButton();
        }''',
    text,
    count=1,
    flags=re.S
)

# Client-side security secrets are no longer meaningful or stored.
text = text.replace("        let passwordMode = 'universal';\n        let universalPassword = '270913';\n        let promotionsPasscode = '200616';",
                    "        let passwordMode = 'firebase-auth';\n        let universalPassword = null;\n        let promotionsPasscode = null;")

replace_region(
    '        function updateUniversalPassword() {',
    '        // Update unlockPromotions to use the variable and handle individual mode',
    r'''        function updateUniversalPassword() {
            alert('Employee passwords are managed securely through Firebase Authentication.');
        }

        function updatePromotionsPasscode() {
            alert('Promotions access is controlled by authenticated employee roles.');
        }

        function clearAllTestData() {
            alert('Bulk data deletion is disabled from the public browser. Use an authenticated administrative backend operation instead.');
        }''',
    'remove client security secrets'
)

replace_region(
    '        // Update unlockPromotions to use the variable and handle individual mode',
    '        // About Section Functions',
    r'''        // Promotions access is controlled by the authenticated employee role.
        function unlockPromotions() {
            if (!currentEmployee) return;
            const roleLevel = roleHierarchy[currentEmployee.role] || 0;
            const specialAccess = currentEmployee.specialAccess || {};
            if (roleLevel < 3 && !specialAccess.promotions) {
                alert('You do not have permission to access Promotions.');
                return;
            }
            promotionsUnlocked = true;
            document.getElementById('promotionsLocked').style.display = 'none';
            document.getElementById('promotionsContent').style.display = 'block';
            loadPromotions();
        }''',
    'promotions authorization'
)

# Employee metadata no longer contains passwords. Authentication identities live in Firebase Auth.
replace_region(
    '        function saveEmployee() {',
    '        function editEmployee(email) {',
    r'''        async function saveEmployee() {
            const oldEmail = document.getElementById('editEmployeeEmail').value;
            const name = document.getElementById('employeeName').value.trim();
            const email = document.getElementById('employeeEmailInput').value.trim().toLowerCase();
            const role = document.getElementById('employeeRole').value;
            if (!name || !email || !role) {
                alert('Please fill in all required fields');
                return;
            }
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                alert('Please enter a valid email address');
                return;
            }
            if (oldEmail && oldEmail !== email) delete employeeRoles[oldEmail];
            employeeRoles[email] = {
                email,
                name,
                role,
                specialAccess: {
                    promotions: document.getElementById('specialAccessPromotions').checked,
                    settings: document.getElementById('specialAccessSettings').checked
                }
            };
            try {
                await saveToFirebase('employeeRoles', employeeRoles);
                await loadAdminData();
                loadEmployees();
                closeAddEmployeeModal();
                alert('Employee access updated. The employee must use a verified Firebase Authentication account with this email.');
            } catch (error) {
                console.error('Employee save failed:', error);
                alert('Unable to save employee access.');
            }
        }''',
    'employee metadata'
)

# Order edits go through an authorized server function instead of writing the complete orders collection.
replace_region(
    '        function saveOrder(event) {',
    '        // Update Overview Metrics',
    r'''        async function saveOrder(event) {
            event.preventDefault();
            const orderId = document.getElementById('orderId').value;
            const existing = orders.find(o => o.id === orderId);
            if (!existing) {
                alert('Error: Order not found');
                return;
            }
            const oldStatus = existing.status;
            const payload = {
                id: orderId,
                customer: document.getElementById('orderCustomer').value,
                email: document.getElementById('orderEmail').value,
                status: document.getElementById('orderStatus').value,
                notes: document.getElementById('orderNotes').value
            };
            try {
                const updateOrder = cloudFunctions.httpsCallable('updateOrder');
                await updateOrder(payload);
                await loadAdminData();
                loadOrders();
                closeOrderForm();
                updateSalesMetrics();
                if (oldStatus !== payload.status) {
                    const updated = orders.find(o => o.id === orderId);
                    if (updated) sendOrderStatusEmail(updated, payload.status);
                }
                alert('Order updated successfully!');
            } catch (error) {
                console.error('Error updating order:', error);
                alert(error?.message || 'Error updating order. Please try again.');
            }
        }''',
    'secure order update'
)

# Escape all customer-controlled order/notification strings that are inserted into admin HTML.
text = text.replace('<td><strong>${order.id}</strong></td>', '<td><strong>${escapeHTML(order.id)}</strong></td>')
text = text.replace('<td>${order.customer}</td>', '<td>${escapeHTML(order.customer)}</td>')
text = text.replace('<span>${item.product} (x${item.qty})</span>', '<span>${escapeHTML(item.product)} (x${item.qty})</span>')
text = text.replace("const formattedMessage = notif.message.replace(/\\n/g, '<br>');", "const formattedMessage = escapeHTML(notif.message).replace(/\\n/g, '<br>');")
text = text.replace('<div class="notification-title">${notif.title}</div>', '<div class="notification-title">${escapeHTML(notif.title)}</div>')
text = text.replace("${currentEmployee.role} • ${currentEmployee.email}", "${escapeHTML(currentEmployee.role)} • ${escapeHTML(currentEmployee.email)}")

# Checkout payment UI is COD-only until a verified server-side payment integration exists.
replace_region(
    '        function selectPaymentMethod(method) {',
    '        function renderPaymentMethodsCheckout() {',
    r'''        function selectPaymentMethod(method) {
            if (method !== 'cod') {
                alert('Online payment is temporarily unavailable while secure server-side payment verification is being configured.');
                return;
            }
            selectedPaymentMethod = 'cod';
            document.querySelectorAll('.payment-option').forEach(option => option.classList.remove('selected'));
            const cod = document.querySelector('input[name="payment"][value="cod"]');
            if (cod) {
                cod.checked = true;
                cod.closest('.payment-option')?.classList.add('selected');
            }
        }''',
    'payment selection'
)

replace_region(
    '        function renderPaymentMethodsCheckout() {',
    '        function renderCheckoutSummary() {',
    r'''        function renderPaymentMethodsCheckout() {
            const container = document.getElementById('checkoutPaymentMethods');
            if (!container) return;
            selectedPaymentMethod = 'cod';
            container.innerHTML = `
                <label class="payment-option selected" onclick="selectPaymentMethod('cod')">
                    <input type="radio" name="payment" value="cod" checked>
                    <div class="payment-header">
                        <span class="payment-icon">💵</span>
                        <span class="payment-title">Cash on Delivery</span>
                    </div>
                    <div class="payment-desc">Pay with cash when your order arrives</div>
                </label>
            `;
        }''',
    'COD-only checkout UI'
)

# Checkout totals are now quoted by the same server code that creates the order.
replace_region(
    '        function renderCheckoutSummary() {',
    '        // ============================================\n        // EMAIL NOTIFICATION SYSTEM',
    r'''        async function renderCheckoutSummary() {
            const itemsContainer = document.getElementById('checkoutSummaryItems');
            itemsContainer.innerHTML = cart.map(item => `
                <div class="summary-item">
                    <span>${escapeHTML(item.name)} x${item.quantity}</span>
                    <span>EGP ${(item.price * item.quantity).toFixed(2)}</span>
                </div>
            `).join('');

            try {
                const quoteOrder = cloudFunctions.httpsCallable('quoteOrder');
                const response = await quoteOrder({
                    items: cart.map(item => ({ id: item.id, quantity: item.quantity })),
                    couponCode: appliedCoupon?.code || null
                });
                const q = response.data;
                document.getElementById('checkoutSubtotal').textContent = `EGP ${Number(q.subtotal).toFixed(2)}`;
                document.getElementById('checkoutShipping').textContent = Number(q.shipping) === 0 ? 'Free' : `EGP ${Number(q.shipping).toFixed(2)}`;
                document.getElementById('checkoutTotal').textContent = `EGP ${Number(q.total).toFixed(2)}`;

                const thresholdRow = document.getElementById('checkoutThresholdRow');
                thresholdRow.style.display = Number(q.thresholdDiscount) > 0 ? 'flex' : 'none';
                thresholdRow.querySelector('span:last-child').textContent = `-EGP ${Number(q.thresholdDiscount).toFixed(2)}`;

                const couponRow = document.getElementById('checkoutCouponRow');
                couponRow.style.display = Number(q.couponDiscount) > 0 ? 'flex' : 'none';
                couponRow.querySelector('span:last-child').textContent = `-EGP ${Number(q.couponDiscount).toFixed(2)}`;

                const processingRow = document.getElementById('checkoutProcessingRow');
                processingRow.style.display = Number(q.processingFee) > 0 ? 'flex' : 'none';
                document.getElementById('checkoutProcessing').textContent = `EGP ${Number(q.processingFee).toFixed(2)}`;

                const serviceRow = document.getElementById('checkoutServiceRow');
                serviceRow.style.display = Number(q.serviceFee) > 0 ? 'flex' : 'none';
                document.getElementById('checkoutService').textContent = `EGP ${Number(q.serviceFee).toFixed(2)}`;

                const taxRow = document.getElementById('checkoutTaxRow');
                taxRow.style.display = Number(q.tax) > 0 ? 'flex' : 'none';
                document.getElementById('checkoutTax').textContent = `EGP ${Number(q.tax).toFixed(2)}`;

                const savings = Number(q.thresholdDiscount) + Number(q.couponDiscount);
                const savingsRow = document.getElementById('checkoutSavingsRow');
                savingsRow.style.display = savings > 0 ? 'flex' : 'none';
                savingsRow.querySelector('span:last-child').textContent = `EGP ${savings.toFixed(2)}`;
            } catch (error) {
                console.error('Unable to quote order:', error);
                document.getElementById('checkoutTotal').textContent = 'Unable to calculate';
            }
        }''',
    'server checkout quote'
)

# Fawaterak cannot be initialized from a browser-held secret.
replace_region(
    '        // ============================================\n        // FAWATERAK PAYMENT GATEWAY (Egypt)',
    '        // ============================================\n        // STRIPE PAYMENT GATEWAY (Disabled for Egypt)',
    r'''        // ============================================
        // ONLINE PAYMENT GATEWAY
        // ============================================
        // P0 security: online payment is disabled until payment-session creation and
        // provider verification are implemented in a trusted backend. No provider
        // secret or bearer credential may be stored in this public file.
        async function initializeFawaterakPayment() {
            return false;
        }''',
    'disable insecure online payment'
)

# Order creation, pricing, coupon usage and stock decrement are one server-side transaction.
replace_region(
    '        async function placeOrder() {',
    '        // Notification Functions',
    r'''        async function placeOrder() {
            const form = document.getElementById('checkoutForm');
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }
            if (cart.length === 0) {
                alert('Your cart is empty');
                return;
            }

            const customer = {
                name: document.getElementById('checkoutName').value,
                email: document.getElementById('checkoutEmail').value,
                phone: document.getElementById('checkoutPhone').value,
                address: document.getElementById('checkoutAddress').value,
                houseNumber: document.getElementById('checkoutHouseNumber').value,
                floor: document.getElementById('checkoutFloor').value,
                city: document.getElementById('checkoutCity').value,
                postal: document.getElementById('checkoutPostal').value,
                notes: document.getElementById('checkoutNotes').value
            };
            const cartSnapshot = cart.map(item => ({ ...item }));
            const button = document.querySelector('.place-order-btn');
            if (button) button.disabled = true;

            try {
                const createOrder = cloudFunctions.httpsCallable('createOrder');
                const response = await createOrder({
                    customer,
                    items: cartSnapshot.map(item => ({ id: item.id, quantity: item.quantity })),
                    couponCode: appliedCoupon?.code || null,
                    paymentMethod: 'cod'
                });
                const result = response.data;

                const emailOrderData = {
                    customer,
                    items: cartSnapshot,
                    paymentMethod: 'cod',
                    totals: { total: Number(result.total) }
                };
                sendOrderConfirmationEmail(emailOrderData, result.orderId).catch(error => console.error('Email notification failed:', error));

                addNotification({
                    title: 'New Order Received',
                    message: `Order ${result.orderId} - EGP ${Number(result.total).toFixed(2)}\n${customer.name}\n${customer.email}\n${customer.phone}`,
                    orderId: result.orderId,
                    timestamp: new Date().toISOString()
                });

                cart = [];
                appliedCoupon = null;
                updateCartBadge();
                form.reset();
                document.getElementById('checkoutPage').classList.remove('active');
                document.getElementById('mainSite').style.display = 'block';
                window.scrollTo(0, 0);
                alert(`Order placed successfully!\n\nOrder ID: ${result.orderId}\nTotal: EGP ${Number(result.total).toFixed(2)}\nPayment: Cash on Delivery`);
            } catch (error) {
                console.error('Order creation failed:', error);
                alert(error?.message || 'Your order could not be completed. Nothing was charged or deducted.');
                await renderCheckoutSummary();
            } finally {
                if (button) button.disabled = false;
            }
        }''',
    'atomic order creation'
)

# Final dashboard implementation must load protected data only after employee authorization.
replace_region(
    '        // Update showDashboard to handle all tabs',
    '        // Close auth modal on outside click',
    r'''        // Employee dashboard data is fetched only after server-authorized authentication.
        async function showDashboard() {
            if (!currentEmployee) return;

            document.getElementById('mainSite').style.display = 'none';
            document.getElementById('mainNav').style.display = 'none';
            document.getElementById('employeeDashboard').classList.add('active');

            const roleLevel = roleHierarchy[currentEmployee.role] || 0;
            const specialAccess = currentEmployee.specialAccess || {};
            const promotionsBtn = document.getElementById('promotionsTabBtn');
            const settingsBtn = document.querySelector('.tab-btn[onclick="switchTab(\'settings\')"]');
            const employeesBtn = document.getElementById('employeesTabBtn');
            const securityBtn = document.getElementById('securityTabBtn');
            if (promotionsBtn) promotionsBtn.style.display = (roleLevel >= 3 || specialAccess.promotions) ? 'inline-block' : 'none';
            if (settingsBtn) settingsBtn.style.display = (roleLevel >= 3 || specialAccess.settings) ? 'inline-block' : 'none';
            if (employeesBtn) employeesBtn.style.display = roleLevel === 5 ? 'inline-block' : 'none';
            if (securityBtn) securityBtn.style.display = roleLevel === 5 ? 'inline-block' : 'none';

            const dashboardHeader = document.querySelector('.dashboard-header h1');
            if (dashboardHeader) {
                dashboardHeader.innerHTML = `Employee Dashboard <span style="font-size: 1rem; font-weight: 600; color: var(--accent); margin-left: 1rem;">${escapeHTML(currentEmployee.role)} • ${escapeHTML(currentEmployee.email)}</span>`;
            }

            await loadAdminData();
            updateProductCategoryDropdown();
            loadProducts();
            loadOrders();
            if (roleLevel >= 3 || specialAccess.settings) {
                loadFooterSettings();
                loadStoreSettings();
                loadAboutSection();
            }
            if (roleLevel === 5) loadEmployees();
        }''',
    'authorized dashboard load',
    last=True
)

# Checkout profile lookup must use the authenticated UID, never a global email-keyed user database.
text = text.replace('const userData = users[userEmail];', 'const userData = currentUser?.uid ? users[currentUser.uid] : null;')

# No known P0 secrets should remain in the public document.
for forbidden in ["const CORRECT_PASSCODE = '270913'", "correctPin = '1987'", "passcode === '200616'", "pin !== '1978'", "password: '270913'"]:
    if forbidden in text:
        text = text.replace(forbidden, "/* removed P0 client-side secret */")

# Verification assertions: these fail the workflow before any commit if a P0 pattern survives.
checks_absent = [
    "Your current password is:",
    "const CORRECT_PASSCODE = '270913'",
    "correctPin = '1987'",
    "passcode === '200616'",
    "pin !== '1978'",
    "password: '270913'",
    "saveToFirebase('orders', orders);",
    "saveToFirebase('users', users);",
    "saveToFirebase('products', products);\n\n            // Send email notifications",
    "Authorization': `Bearer ${fawaterakConfig.apiKey}`"
]
for needle in checks_absent:
    if needle in text:
        raise SystemExit(f'P0 verification failed: forbidden pattern remains: {needle}')

checks_present = [
    "cloudFunctions.httpsCallable('createOrder')",
    "cloudFunctions.httpsCallable('quoteOrder')",
    "cloudFunctions.httpsCallable('getEmployeeProfile')",
    "auth.signInWithEmailAndPassword",
    "auth.createUserWithEmailAndPassword",
    "auth.sendPasswordResetEmail",
    "firebase.auth.GoogleAuthProvider.credential",
    "escapeHTML(notif.message)",
    "await loadAdminData()"
]
for needle in checks_present:
    if needle not in text:
        raise SystemExit(f'P0 verification failed: expected secure pattern missing: {needle}')

if text == original:
    raise SystemExit('No changes were produced')

path.write_text(text, encoding='utf-8')
print('P0 storefront patch applied and static assertions passed.')
