from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
index_path = root / 'index.html'
firebase_path = root / 'firebase.json'

# Validation branch runtime only: point the browser and Firebase CLI at an isolated demo project.
h = index_path.read_text()
h = h.replace('projectId: "kem-store"', 'projectId: "demo-kem-validation"', 1)
h = h.replace('authDomain: "kem-store.firebaseapp.com"', 'authDomain: "demo-kem-validation.firebaseapp.com"', 1)
h = h.replace('storageBucket: "kem-store.firebasestorage.app"', 'storageBucket: "demo-kem-validation.firebasestorage.app"', 1)
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
if needle not in h:
    raise SystemExit('Firebase initialization anchor not found')
h = h.replace(needle, replacement, 1)
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
print('Prepared isolated demo-kem-validation emulator runtime')
