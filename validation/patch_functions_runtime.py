from pathlib import Path

p = Path('functions/index.js')
f = p.read_text()

# Validation environment only: initialize Admin SDK with the isolated emulator demo
# database URL. Do not alter createOrder, transaction behavior, pricing, stock, coupons,
# authentication, authorization, or any other application logic.
init_old = 'initializeApp();'
init_new = "initializeApp({ databaseURL: 'https://demo-kem-validation-default-rtdb.firebaseio.com' });"
if f.count(init_old) != 1:
    raise SystemExit(f'Functions initializeApp validation anchor expected once, found {f.count(init_old)}')
f = f.replace(init_old, init_new, 1)

# Assert that the reconciled authoritative transaction logic is already committed before
# this environment-only rewrite runs.
required = [
    "const orderRootRef = db.ref('/');",
    "const initialOrderRoot = (await orderRootRef.once('value')).val();",
    'const transaction = await orderRootRef.transaction((root) => {',
    'if (root === null && initialOrderRoot !== null)',
]
for text in required:
    if f.count(text) != 1:
        raise SystemExit(f'Committed transaction requirement missing or duplicated: {text!r} -> {f.count(text)}')

p.write_text(f)
print('Patched Functions database URL for isolated emulator only; committed transaction logic unchanged')
