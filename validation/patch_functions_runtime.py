from pathlib import Path

p = Path('functions/index.js')
f = p.read_text()

init_old = 'initializeApp();'
init_new = "initializeApp({ databaseURL: 'https://demo-kem-validation-default-rtdb.firebaseio.com' });"
if f.count(init_old) != 1:
    raise SystemExit('Functions initializeApp validation anchor not unique')
f = f.replace(init_old, init_new, 1)

tx_anchor = "  const transaction = await db.ref('/').transaction((root) => {"
if f.count(tx_anchor) != 1:
    raise SystemExit('createOrder root transaction anchor not unique')

seeded = """  const orderRootRef = db.ref('/');
  const initialOrderRoot = (await orderRootRef.once('value')).val();
  const transaction = await orderRootRef.transaction((root) => {
    if (root === null && initialOrderRoot !== null) {
      root = JSON.parse(JSON.stringify(initialOrderRoot));
    }"""
f = f.replace(tx_anchor, seeded, 1)

p.write_text(f)
print('Patched Functions runtime for isolated emulator and seeded initial transaction state')
