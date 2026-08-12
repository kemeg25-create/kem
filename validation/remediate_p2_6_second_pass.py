from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'index.html')
h=p.read_text()
assert 'P2.6 — ACCOUNT / AUTHENTICATION' in h
assert "await openAccountModal();" in h[h.index('async function handleLogin'):h.index('async function handleSignup')]
assert 'lockCustomerDialogScroll()' in h and 'unlockCustomerDialogScroll()' in h

# 1. Preserve factual title case for the real saved-address default state.
old=".account-address-default{color:var(--color-success);font:600 var(--type-metadata)/1.2 var(--font-ui);text-transform:uppercase;letter-spacing:.05em}"
new=".account-address-default{color:var(--color-success);font:600 var(--type-metadata)/1.2 var(--font-ui);letter-spacing:.05em}"
assert old in h
h=h.replace(old,new,1)

# 2. Make the existing account close control satisfy the 3px solid focus contract even for deterministic programmatic entry focus.
anchor="#authModal :is(button,input):focus-visible,#accountModal :is(button,input):focus-visible{outline:3px solid var(--color-kem-pink);outline-offset:3px}"
assert anchor in h
h=h.replace(anchor,anchor+"\n        #accountModal .close-modal:focus{outline:3px solid var(--color-kem-pink);outline-offset:3px}",1)

# 3/5. Remove frame-dependent customer-dialog entry and return focus timing.
replacements={
"switchAuthTab('login');requestAnimationFrame(()=>document.getElementById('loginIdentifier')?.focus());":"switchAuthTab('login');document.getElementById('loginIdentifier')?.focus();",
"if(t?.isConnected)requestAnimationFrame(()=>t.focus())":"if(t?.isConnected)t.focus()",
"lockCustomerDialogScroll();requestAnimationFrame(()=>m.querySelector('.close-modal')?.focus());await loadCustomerOrders()":"lockCustomerDialogScroll();m.querySelector('.close-modal')?.focus();await loadCustomerOrders()"
}
for old,new in replacements.items():
    assert old in h, old
    h=h.replace(old,new,1)
# closeAccountModal has a second restoration occurrence.
old="if(t?.isConnected)requestAnimationFrame(()=>t.focus())"
assert old in h
h=h.replace(old,"if(t?.isConnected)t.focus()",1)

# 4. Keep only the account composition single-column through 768px; other phase breakpoints remain untouched.
media="@media(max-width:768px){#accountModal .account-layout{grid-template-columns:1fr;gap:var(--space-32)}#accountModal .account-actions{flex-direction:column-reverse}#accountModal .account-actions button{width:100%}}"
assert media not in h
h=h.replace("        @media(max-width:420px){",f"        {media}\n        @media(max-width:420px){{",1)

# 6. Keep visible header UI unchanged while giving the unauthenticated trigger an unambiguous accessible name.
old="button.setAttribute('aria-label', 'Log in or create account');"
assert old in h
h=h.replace(old,"button.setAttribute('aria-label', 'Account');",1)

# Frozen authority / structural guards.
for required in [
    "auth.signInWithEmailAndPassword(email, password)",
    "auth.createUserWithEmailAndPassword(email, password)",
    "credential.user.sendEmailVerification()",
    "auth.sendPasswordResetEmail(email)",
    "cloudFunctions.httpsCallable('getCustomerOrders')",
    "async function logoutEmployee()",
    "P2.5 — CART / CHECKOUT","P2.4 — PRODUCT DETAIL","P2.3 — COLLECTION / SHOP","P2.2 — HOMEPAGE","P2.1 — HEADER / NAVIGATION"
]: assert required in h, required
assert "body { overflow-x: hidden; }" not in h
assert "text-transform:uppercase" not in h[h.index('.account-address-default'):h.index('.account-address-default')+220]
assert "button.setAttribute('aria-label', 'Account');" in h
p.write_text(h)
print('Applied P2.6 second remediation pass')
