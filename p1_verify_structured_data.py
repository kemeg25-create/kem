from pathlib import Path
from html.parser import HTMLParser
import json
import os
import re
import subprocess
import tempfile

h = Path('index.html').read_text()
b = Path('functions/index.js').read_text()
rules = json.loads(Path('database.rules.json').read_text())['rules']

# 1) Every JSON-LD block must be JSON only and parse successfully.
jsonld_pattern = re.compile(r'<script\s+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
jsonld_blocks = jsonld_pattern.findall(h)
assert jsonld_blocks, 'No JSON-LD blocks found'
parsed_jsonld = []
for i, body in enumerate(jsonld_blocks, 1):
    obj = json.loads(body)
    parsed_jsonld.append(obj)
    for forbidden in ('addEventListener', 'document.', 'window.', '=>'):
        assert forbidden not in body, f'Executable JavaScript found in JSON-LD block {i}'
    print(f'JSON-LD block {i} parses: type={obj.get("@type")}')

# Current site has one grounded static business/store schema. Do not fabricate separate
# Organization/WebSite/Product entities or unsupported reviews/contact/social data.
assert len(parsed_jsonld) == 1, f'Unexpected JSON-LD block count: {len(parsed_jsonld)}'
store = parsed_jsonld[0]
assert store.get('@context') == 'https://schema.org'
assert store.get('@type') == 'ClothingStore'
assert store.get('name') == 'KEM Streetwear'
assert store.get('url') == 'https://buykem.com'
assert store.get('address', {}).get('addressCountry') == 'EG'
assert store.get('acceptedPaymentMethod') == ['Cash']
assert store.get('currenciesAccepted') == 'EGP'
assert store.get('paymentAccepted') == 'Cash on Delivery'
for unsupported in ('telephone', 'email', 'sameAs', 'aggregateRating', 'review', 'ratingValue', 'priceRange'):
    assert unsupported not in store, f'Unsupported structured-data claim remains: {unsupported}'

# 2) Every normal inline JavaScript block must parse successfully.
script_pattern = re.compile(r'<script([^>]*)>(.*?)</script>', re.S | re.I)
normal_blocks = []
for attrs, body in script_pattern.findall(h):
    if re.search(r'type\s*=\s*["\']application/ld\+json["\']', attrs, re.I):
        continue
    # External script elements have no inline code.
    if 'src=' in attrs.lower() and not body.strip():
        continue
    if not body.strip():
        continue
    normal_blocks.append(body)
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f:
        f.write(body)
        name = f.name
    try:
        subprocess.run(['node', '--check', name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    finally:
        os.unlink(name)
print(f'Normal inline JavaScript blocks parsed: {len(normal_blocks)}')

executable = '\n'.join(normal_blocks)
pop_marker = "window.addEventListener('popstate'"
key_marker = "document.addEventListener('keydown', event => {"
assert executable.count(pop_marker) == 1, f'popstate listener count={executable.count(pop_marker)}'
assert executable.count(key_marker) == 1, f'critical keydown listener count={executable.count(key_marker)}'
assert all(pop_marker not in body and key_marker not in body for body in jsonld_blocks)

# 3) Product browser-history/deep-link/metadata invariants.
for token in (
    'function openProductDetail(productId, options = {})',
    'function closeProductDetail(options = {})',
    "url.searchParams.set('product', product.id)",
    "url.searchParams.delete('product')",
    'openProductDetail(id, { fromHistory: true })',
    'closeProductDetail({ fromHistory: true })',
    "searchParams.get('product')",
    'function updateProductSeo',
    'function restoreHomeSeo',
):
    assert token in h, f'Missing product/history invariant: {token}'
assert h.count('function updateProductSeo') == 1
assert h.count('function restoreHomeSeo') == 1

# 4) Escape/focus trap applies to active form/auth/product dialogs exactly once.
for token in (
    ".form-modal.active,.auth-modal.active,.product-detail-modal.active",
    "event.key === 'Escape'",
    "event.key !== 'Tab'",
    'event.shiftKey && document.activeElement === first',
    'document.activeElement === last',
):
    assert token in executable, f'Missing dialog keyboard invariant: {token}'
for dialog_id in ('accountModal', 'authModal', 'employeeModal', 'productDetailModal'):
    assert f'id="{dialog_id}"' in h, f'Missing dialog: {dialog_id}'

# 5) No duplicate DOM IDs.
class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
    def handle_starttag(self, tag, attrs):
        value = dict(attrs).get('id')
        if value:
            self.ids.append(value)

parser = IdParser()
parser.feed(h)
seen = set()
duplicates = set()
for value in parser.ids:
    if value in seen:
        duplicates.add(value)
    seen.add(value)
assert not duplicates, 'Duplicate IDs: ' + ', '.join(sorted(duplicates))

# 6) Core P1 storefront/account/admin functionality remains present.
for token in (
    'id="mobileNavToggle"',
    'id="shopSearch"',
    'function renderShopProducts',
    'function filterByCategory',
    'function renderCart',
    'function openCheckout',
    'function openAccountModal',
    'id="checkoutStatus"',
    ':focus-visible',
    'logo-240.png',
):
    assert token in h, f'Missing P1 frontend invariant: {token}'
assert len(re.findall(r'function\s+renderShopProducts\s*\(', h)) == 1
assert len(re.findall(r'function\s+filterByCategory\s*\(', h)) == 1
for token in ('productSizes', 'productColors', 'detailGallery', 'detailSizes', 'detailColors'):
    assert token in h
for token in ('exports.getCustomerOrders', 'exports.uploadProductImage', 'requestedSize', 'requestedColor'):
    assert token in b
assert 'order?.customerUid === uid' in b

# 7) P0 security/commerce guardrails remain intact.
for token in ('revokeEmployeeSession', 'await auth.signOut()'):
    assert token in h
for token in (
    'exports.revokeEmployeeSession',
    'auth.revokeRefreshTokens',
    'tokensValidAfterTime',
    'auth_time',
    'requireVerifiedCustomer',
    'email_verified',
    "paymentMethod !== 'cod'",
    "db.ref('/').transaction",
    'product.stock = currentStock - item.quantity',
    'root.counters.orderNumbers',
    'root.coupons[key].used',
):
    assert token in b, f'Missing P0 guardrail: {token}'
assert 'request.data?.price' not in b
assert rules['orders']['.read'] is False and rules['orders']['.write'] is False
assert rules['employeeRoles']['.read'] is False and rules['employeeRoles']['.write'] is False
assert rules['coupons']['.read'] is False and rules['coupons']['.write'] is False

# 8) P1 dead/unsafe client paths remain absent.
assert 'js.stripe.com' not in h
assert 'firebase-storage.js' not in h

print('Focused structured-data/P0/P1 verification passed')
