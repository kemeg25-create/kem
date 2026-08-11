from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
index_path = root / 'index.html'
firebase_path = root / 'firebase.json'

# Validation environment only: point the browser Firebase configuration at the isolated
# demo project and connect each client SDK to its local emulator. This script must not
# change application behavior, responsive CSS, event handlers, accessibility logic, or
# commerce/order logic.
h = index_path.read_text()
h = h.replace('projectId: "kem-store"', 'projectId: "demo-kem-validation"', 1)
h = h.replace('authDomain: "kem-store.firebaseapp.com"', 'authDomain: "demo-kem-validation.firebaseapp.com"', 1)
h = h.replace('storageBucket: "kem-store.firebasestorage.app"', 'storageBucket: "demo-kem-validation.firebasestorage.app"', 1)
h = h.replace(
    'databaseURL: "https://kem-store-default-rtdb.europe-west1.firebasedatabase.app"',
    'databaseURL: "https://demo-kem-validation-default-rtdb.firebaseio.com"',
    1,
)
needle = """                db = firebase.database();
                auth = firebase.auth();
                cloudFunctions = firebase.functions();
"""
replacement = needle + """                if (location.hostname === '127.0.0.1' || location.hostname === 'localhost') {
                    auth.useEmulator('http://127.0.0.1:9099', { disableWarnings: true });
                    db.useEmulator('127.0.0.1', 9000);
                    cloudFunctions.useEmulator('127.0.0.1', 5001);
                }
"""
if h.count(needle) != 1:
    raise SystemExit(f'Firebase initialization anchor expected once, found {h.count(needle)}')
h = h.replace(needle, replacement, 1)
if 'demo-kem-validation-default-rtdb' not in h:
    raise SystemExit('Validation databaseURL rewrite failed')

# Guard against accidentally reintroducing application-level validation patches.
for forbidden in (
    '.about-content, .about-content > * { min-width:0; }',
    "onclick=\"filterByCategory(${JSON.stringify(name)})\"",
    "onclick=\"selectProductImage(${JSON.stringify(src)},this)\"",
    "#employeeModal.active,.form-modal.active,.auth-modal.active,.product-detail-modal.active",
):
    # These may legitimately exist in the committed source; this script simply must not
    # synthesize them. The source-presence assertions are performed by the workflow.
    pass

index_path.write_text(h)

config = json.loads(firebase_path.read_text())
config['storage'] = {'rules': 'validation/storage.rules'}
config['emulators'] = {
    'auth': {'port': 9099},
    'database': {'port': 9000},
    'functions': {'port': 5001},
    'hosting': {'port': 5000},
    'storage': {'port': 9199},
    'ui': {'enabled': False},
    'singleProjectMode': True,
}
firebase_path.write_text(json.dumps(config, indent=2) + '\n')
print('Prepared isolated demo-kem-validation emulator routing only; no application fixes injected')
