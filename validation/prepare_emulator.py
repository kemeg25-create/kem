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
if needle not in h:
    raise SystemExit('Firebase initialization anchor not found')
if 'demo-kem-validation-default-rtdb' not in h:
    raise SystemExit('Validation databaseURL rewrite failed')
h = h.replace(needle, replacement, 1)

# Candidate P1 regression fix under validation: keep the existing two-column stats layout,
# but allow grid tracks/items to shrink within narrow phone viewports.
responsive_anchor = """            .section-title { font-size:2.5rem; }

            .hero-title {
"""
responsive_fix = """            .section-title { font-size:2.5rem; }
            .about-content, .about-content > * { min-width:0; }
            .stats { grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; }
            .stat-item { padding:1rem; }

            .hero-title {
"""
if responsive_anchor not in h:
    raise SystemExit('Mobile responsive anchor not found')
h = h.replace(responsive_anchor, responsive_fix, 1)

# Candidate P1 regression fix under validation: JSON.stringify emits double quotes that
# break the double-quoted inline onclick attribute. Bind click listeners to the rendered
# buttons instead, so arbitrary category names cannot create malformed executable markup.
filter_old = """        function renderShopFilters() {
            const el=document.getElementById('shopFilterButtons'); if(!el)return;
            const names=[...new Set(categories.map(getCategoryName).filter(Boolean))];
            el.innerHTML=['all',...names].map(name=>`<button type=\"button\" class=\"filter-btn ${shopCategoryFilter===name?'active':''}\" data-category=\"${escapeHTML(name)}\" onclick=\"filterByCategory(${JSON.stringify(name)})\">${escapeHTML(name==='all'?'All Products':name)}</button>`).join('');
        }
"""
filter_new = """        function renderShopFilters() {
            const el=document.getElementById('shopFilterButtons'); if(!el)return;
            const names=[...new Set(categories.map(getCategoryName).filter(Boolean))];
            el.innerHTML=['all',...names].map(name=>`<button type=\"button\" class=\"filter-btn ${shopCategoryFilter===name?'active':''}\" data-category=\"${escapeHTML(name)}\">${escapeHTML(name==='all'?'All Products':name)}</button>`).join('');
            el.querySelectorAll('button[data-category]').forEach(button => button.addEventListener('click', () => filterByCategory(button.dataset.category)));
        }
"""
if filter_old not in h:
    raise SystemExit('Category filter rendering anchor not found')
h = h.replace(filter_old, filter_new, 1)
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
print('Prepared isolated demo-kem-validation emulator runtime with candidate P1 fixes')
