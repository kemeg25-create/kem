from pathlib import Path
import sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else 'index.html')
h = p.read_text()
assert 'P2.6 — ACCOUNT / AUTHENTICATION' in h

old_logout = """        async function logoutUser() {
            closeAccountModal();
            currentUser = null;
            currentEmployee = null;
            if (auth) await auth.signOut();
            updateAuthButton();
        }"""
new_logout = """        async function logoutUser() {
            closeAccountModal();
            currentUser = null;
            currentEmployee = null;
            updateAuthButton();
            if (auth) await auth.signOut();
            updateAuthButton();
        }"""
assert old_logout in h
h = h.replace(old_logout, new_logout, 1)

old_cart = """        function openCart() {
            document.getElementById('mainSite').style.display = 'none';
            document.getElementById('cartPage').classList.add('active');
            renderCart();
            window.scrollTo(0, 0);
        }"""
new_cart = """        function openCart() {
            const accountModal = document.getElementById('accountModal');
            if (accountModal?.classList.contains('active')) closeAccountModal();
            document.getElementById('mainSite').style.display = 'none';
            document.getElementById('cartPage').classList.add('active');
            renderCart();
            window.scrollTo(0, 0);
        }"""
assert old_cart in h
h = h.replace(old_cart, new_cart, 1)

# Preserve all six already-green P2.6 fixes and authority anchors.
assert '<span class="account-address-default">Default</span>' in h
p26 = h[h.index('P2.6 — ACCOUNT / AUTHENTICATION'):]
assert 'text-transform:uppercase' not in p26[p26.index('.account-address-default'):p26.index('.account-address-default') + 220]
assert '#accountModal .close-modal:focus{outline:3px solid var(--color-kem-pink);outline-offset:3px}' in h
assert "switchAuthTab('login');document.getElementById('loginIdentifier')?.focus();" in h
assert "if(t?.isConnected)t.focus()" in h
assert '@media(max-width:768px){#accountModal .account-layout{grid-template-columns:1fr' in h
assert "button.setAttribute('aria-label', 'Account');" in h
assert "document.body.style.overflow='hidden'" not in h[h.index('// Auth Modal Functions (Global)'):h.index('// Custom Cursor')]
assert "auth.signInWithEmailAndPassword(email, password)" in h
assert "auth.createUserWithEmailAndPassword(email, password)" in h
assert 'credential.user.sendEmailVerification()' in h
assert "auth.sendPasswordResetEmail(email)" in h
assert "await openAccountModal();" in h[h.index('async function handleLogin'):h.index('async function handleSignup')]
assert "cloudFunctions.httpsCallable('getCustomerOrders')" in h
assert 'async function logoutEmployee()' in h

p.write_text(h)
print('Applied P2.6 third remediation pass')
