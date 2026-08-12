from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'index.html')
h=p.read_text()
assert 'P2.6 — ACCOUNT / AUTHENTICATION' in h

old="                await credential.user.sendEmailVerification();\n                closeAuthModal();\n                document.getElementById('signupForm').reset();"
new="                await credential.user.sendEmailVerification();\n                const loginIdentifier=document.getElementById('loginIdentifier');\n                if(loginIdentifier)loginIdentifier.value=email;\n                closeAuthModal();\n                document.getElementById('signupForm').reset();"
assert old in h
h=h.replace(old,new,1)

old="                function handleForgotPassword(){showPasswordReset()}"
new="                async function handleForgotPassword(){const m=document.getElementById('authModal');if(m?.classList.contains('active')){showPasswordReset();return}const email=document.getElementById('loginIdentifier')?.value.trim().toLowerCase();if(!email){openAuthModal();showPasswordReset();return}try{await auth.sendPasswordResetEmail(email);alert('If the account exists, a password reset email has been sent.')}catch(error){console.error('Password reset failed:',error);openAuthModal();showPasswordReset();setAuthFeedback('Unable to start password reset. Please check the address and try again.','error')}}"
assert old in h
h=h.replace(old,new,1)

# Preserve every previously-green P2.6 and frozen-regression correction.
for x in [
    '<span class="account-address-default">Default</span>',
    '#accountModal .close-modal:focus{outline:3px solid var(--color-kem-pink);outline-offset:3px}',
    "switchAuthTab('login');document.getElementById('loginIdentifier')?.focus();",
    "if(t?.isConnected)t.focus()",
    '@media(max-width:768px){#accountModal .account-layout{grid-template-columns:1fr',
    "button.setAttribute('aria-label', 'Account');",
    "currentUser = null;\n            currentEmployee = null;\n            updateAuthButton();\n            if (auth) await auth.signOut();",
    "if (accountModal?.classList.contains('active')) closeAccountModal();",
    "openAccountModal(){if(document.getElementById('cartPage')?.classList.contains('active')||document.getElementById('checkoutPage')?.classList.contains('active'))return;",
    "auth.signInWithEmailAndPassword(email, password)",
    "auth.createUserWithEmailAndPassword(email, password)",
    'credential.user.sendEmailVerification()',
    "auth.sendPasswordResetEmail(email)",
    "cloudFunctions.httpsCallable('getCustomerOrders')",
    'async function logoutEmployee()'
]: assert x in h,x
assert "prompt('Enter your email address to reset your password:')" not in h
p.write_text(h)
print('Applied P2.6 P0/P1 reset compatibility remediation')
