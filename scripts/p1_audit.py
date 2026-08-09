from pathlib import Path
import re
import os

html = Path('index.html').read_text()
files = ['index.html','icon enhanced.png','payment-success.html','payment-failed.html','robots.txt','sitemap.xml']
print('P1 AUDIT SUMMARY')
print('index bytes', Path('index.html').stat().st_size)
for f in files:
    p=Path(f)
    if p.exists(): print(f'{f}: {p.stat().st_size} bytes')

checks = {
 'mobile_menu_markup': bool(re.search(r'mobile[-_ ]?(menu|nav|toggle|hamburger)', html, re.I)),
 'nav_hidden_mobile': '.nav-links {\n                display: none;' in html,
 'search_ui': bool(re.search(r'(shopSearch|productSearch|searchProducts|type="search")', html, re.I)),
 'wishlist_ui': bool(re.search(r'wishlist', html, re.I)),
 'size_model': bool(re.search(r'\b(sizes|sizeOptions|selectedSize)\b', html)),
 'color_model': bool(re.search(r'\b(colors|colorOptions|selectedColor)\b', html)),
 'gallery_model': bool(re.search(r'\b(images|gallery|thumbnails)\b', html, re.I)),
 'product_detail_modal': 'openProductDetail' in html,
 'product_url_routing': bool(re.search(r'(history\.pushState|URLSearchParams|/product/|product=)', html)),
 'account_ui': bool(re.search(r'(accountModal|userAccount|profileModal|orderHistory)', html, re.I)),
 'loading_state_words': len(re.findall(r'loading', html, re.I)),
 'empty_state_words': len(re.findall(r'empty', html, re.I)),
 'aria_modal': len(re.findall(r'aria-modal', html, re.I)),
 'role_dialog': len(re.findall(r'role=["\']dialog', html, re.I)),
 'focus_visible_css': ':focus-visible' in html,
 'lazy_images': len(re.findall(r'loading=["\']lazy', html, re.I)),
}
for k,v in checks.items(): print(k, v)

for fn in ['renderShopProducts','filterProducts','filterByCategory','openProductDetail','renderProducts','renderOrders','loadOrders','renderCustomers','loadStoreSettings','saveStoreSettings','logout','logoutEmployee']:
    print('function', fn, 'defs', len(re.findall(r'function\\s+'+re.escape(fn)+r'\\s*\\(', html)))

print('media queries', len(re.findall(r'@media', html)))
print('innerHTML assignments', len(re.findall(r'\.innerHTML\\s*=', html)))
print('direct onclick attrs', len(re.findall(r'onclick=', html, re.I)))
print('tables', len(re.findall(r'<table\\b', html, re.I)))
print('images', len(re.findall(r'<img\\b', html, re.I)), 'images without alt', len(re.findall(r'<img(?![^>]*\\balt=)[^>]*>', html, re.I)))
print('buttons', len(re.findall(r'<button\\b', html, re.I)), 'buttons without type', len(re.findall(r'<button(?![^>]*\\btype=)[^>]*>', html, re.I)))
print('inputs', len(re.findall(r'<input\\b', html, re.I)), 'inputs without id', len(re.findall(r'<input(?![^>]*\\bid=)[^>]*>', html, re.I)))
print('labels', len(re.findall(r'<label\\b', html, re.I)), 'labels with for', len(re.findall(r'<label[^>]*\\bfor=', html, re.I)))
print('h1', len(re.findall(r'<h1\\b', html, re.I)), 'h2', len(re.findall(r'<h2\\b', html, re.I)))
print('renderShopProducts mentions', html.count('renderShopProducts('))
print('filterByCategory mentions', html.count('filterByCategory('))
print('product image field mentions', len(re.findall(r'product\.image\\b', html)))
print('product images field mentions', len(re.findall(r'product\.images\\b', html)))

# P0 guardrails
for token in ["await auth.signOut()", "revokeEmployeeSession", "requireVerifiedCustomer", "paymentMethod !== 'cod'", "getEmployeeForRequest(request", "readPublicPath('coupons')"]:
    print('P0', token, token in html or token in Path('functions/index.js').read_text())
