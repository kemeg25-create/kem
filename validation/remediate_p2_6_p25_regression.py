from pathlib import Path
import sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else 'index.html')
h = p.read_text()
assert 'P2.6 — ACCOUNT / AUTHENTICATION' in h

old = "async function openAccountModal(){if(!auth?.currentUser||!currentUser){openAuthModal();return}"
new = "async function openAccountModal(){if(document.getElementById('cartPage')?.classList.contains('active')||document.getElementById('checkoutPage')?.classList.contains('active'))return;if(!auth?.currentUser||!currentUser){openAuthModal();return}"
assert old in h
h = h.replace(old, new, 1)

# Preserve the complete previously-green P2.6 behavior and the two third-pass fixes.
assert '<span class="account-address-default">Default</span>' in h
assert '#accountModal .close-modal:focus{outline:3px solid var(--color-kem-pink);outline-offset:3px}' in h
assert "switchAuthTab('login');document.getElementById('loginIdentifier')?.focus();" in h
assert "if(t?.isConnected)t.focus()" in h
assert '@media(max-width:768px){#accountModal .account-layout{grid-template-columns:1fr' in h
assert "button.setAttribute('aria-label', 'Account');" in h
assert "currentUser = null;\n            currentEmployee = null;\n            updateAuthButton();\n            if (auth) await auth.signOut();" in h
assert "if (accountModal?.classList.contains('active')) closeAccountModal();" in h
assert "auth.signInWithEmailAndPassword(email, password)" in h
assert "auth.createUserWithEmailAndPassword(email, password)" in h
assert 'credential.user.sendEmailVerification()' in h
assert "auth.sendPasswordResetEmail(email)" in h
assert "cloudFunctions.httpsCallable('getCustomerOrders')" in h
assert 'async function logoutEmployee()' in h

p.write_text(h)
print('Applied P2.6 P2.5 regression remediation')
