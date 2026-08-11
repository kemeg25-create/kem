from pathlib import Path

index_path = Path('index.html')
functions_path = Path('functions/index.js')

h = index_path.read_text()

# 1) Permanently apply the proven mobile About/stats containment fix while preserving
# the already-committed dashboard responsive rules.
responsive_old = """            .section-title { font-size:2.5rem; }
            .dashboard { padding-left:1rem; padding-right:1rem; }
            .dashboard-header { flex-direction:column; align-items:stretch; gap:1rem; }
            .dashboard-header h1 { min-width:0; overflow-wrap:anywhere; }
            .dashboard-header-actions { width:100%; min-width:0; flex-wrap:wrap; justify-content:flex-start; }

            .hero-title {
"""
responsive_new = """            .section-title { font-size:2.5rem; }
            .about-content, .about-content > * { min-width:0; }
            .stats { grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; }
            .stat-item { padding:1rem; }
            .dashboard { padding-left:1rem; padding-right:1rem; }
            .dashboard-header { flex-direction:column; align-items:stretch; gap:1rem; }
            .dashboard-header h1 { min-width:0; overflow-wrap:anywhere; }
            .dashboard-header-actions { width:100%; min-width:0; flex-wrap:wrap; justify-content:flex-start; }

            .hero-title {
"""
if h.count(responsive_old) != 1:
    raise SystemExit(f'About responsive anchor expected once, found {h.count(responsive_old)}')
h = h.replace(responsive_old, responsive_new, 1)

# 2) Permanently replace generated inline onclick handlers with event listeners.
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
if h.count(filter_old) != 1:
    raise SystemExit(f'Category filter anchor expected once, found {h.count(filter_old)}')
h = h.replace(filter_old, filter_new, 1)

product_old = """            const gallery=document.getElementById('detailGallery'); gallery.innerHTML=images.length>1?images.map((src,i)=>`<button type=\"button\" class=\"product-gallery-thumb ${i===0?'active':''}\" onclick=\"selectProductImage(${JSON.stringify(src)},this)\" aria-label=\"View image ${i+1} of ${images.length}\"><img src=\"${escapeHTML(src)}\" alt=\"\" loading=\"lazy\" style=\"width:100%;height:100%;object-fit:cover;\"></button>`).join(''):'';
            document.getElementById('detailCategory').textContent=product.category||''; document.getElementById('detailName').textContent=product.name||''; document.getElementById('detailPrice').textContent=`EGP ${Number(product.price).toFixed(2)}`; document.getElementById('detailDescription').textContent=product.description||''; document.getElementById('detailStock').textContent=Number(product.stock)<10?`⚠️ Only ${Number(product.stock)} left in stock!`:`✓ ${Number(product.stock)} in stock`;
            const sizes=Array.isArray(product.sizes)?product.sizes.filter(Boolean):[], colors=Array.isArray(product.colors)?product.colors.filter(Boolean):[];
            document.getElementById('detailSizesGroup').style.display=sizes.length?'block':'none'; document.getElementById('detailColorsGroup').style.display=colors.length?'block':'none';
            document.getElementById('detailSizes').innerHTML=sizes.map(v=>`<button type=\"button\" class=\"variant-option\" onclick=\"selectProductVariant('size',${JSON.stringify(v)},this)\">${escapeHTML(v)}</button>`).join(''); document.getElementById('detailColors').innerHTML=colors.map(v=>`<button type=\"button\" class=\"variant-option\" onclick=\"selectProductVariant('color',${JSON.stringify(v)},this)\">${escapeHTML(v)}</button>`).join('');
"""
product_new = """            const gallery=document.getElementById('detailGallery'); gallery.innerHTML=images.length>1?images.map((src,i)=>`<button type=\"button\" class=\"product-gallery-thumb ${i===0?'active':''}\" data-image-index=\"${i}\" aria-label=\"View image ${i+1} of ${images.length}\"><img src=\"${escapeHTML(src)}\" alt=\"\" loading=\"lazy\" style=\"width:100%;height:100%;object-fit:cover;\"></button>`).join(''):'';
            gallery.querySelectorAll('button[data-image-index]').forEach(button => button.addEventListener('click', () => selectProductImage(images[Number(button.dataset.imageIndex)], button)));
            document.getElementById('detailCategory').textContent=product.category||''; document.getElementById('detailName').textContent=product.name||''; document.getElementById('detailPrice').textContent=`EGP ${Number(product.price).toFixed(2)}`; document.getElementById('detailDescription').textContent=product.description||''; document.getElementById('detailStock').textContent=Number(product.stock)<10?`⚠️ Only ${Number(product.stock)} left in stock!`:`✓ ${Number(product.stock)} in stock`;
            const sizes=Array.isArray(product.sizes)?product.sizes.filter(Boolean):[], colors=Array.isArray(product.colors)?product.colors.filter(Boolean):[];
            const sizesEl=document.getElementById('detailSizes'), colorsEl=document.getElementById('detailColors');
            document.getElementById('detailSizesGroup').style.display=sizes.length?'block':'none'; document.getElementById('detailColorsGroup').style.display=colors.length?'block':'none';
            sizesEl.innerHTML=sizes.map((v,i)=>`<button type=\"button\" class=\"variant-option\" data-variant-index=\"${i}\">${escapeHTML(v)}</button>`).join('');
            colorsEl.innerHTML=colors.map((v,i)=>`<button type=\"button\" class=\"variant-option\" data-variant-index=\"${i}\">${escapeHTML(v)}</button>`).join('');
            sizesEl.querySelectorAll('button[data-variant-index]').forEach(button => button.addEventListener('click', () => selectProductVariant('size', sizes[Number(button.dataset.variantIndex)], button)));
            colorsEl.querySelectorAll('button[data-variant-index]').forEach(button => button.addEventListener('click', () => selectProductVariant('color', colors[Number(button.dataset.variantIndex)], button)));
"""
if h.count(product_old) != 1:
    raise SystemExit(f'Product gallery/variant anchor expected once, found {h.count(product_old)}')
h = h.replace(product_old, product_new, 1)

# 3) Permanently include the employee login modal in the existing dialog keyboard handler.
dialog_old = "const dialog = document.querySelector('.form-modal.active,.auth-modal.active,.product-detail-modal.active');"
dialog_new = "const dialog = document.querySelector('#employeeModal.active,.form-modal.active,.auth-modal.active,.product-detail-modal.active');"
if h.count(dialog_old) != 1:
    raise SystemExit(f'Employee dialog keyboard anchor expected once, found {h.count(dialog_old)}')
h = h.replace(dialog_old, dialog_new, 1)

index_path.write_text(h)

# 4) Permanently preserve the authoritative root RTDB transaction while making the
# Admin transaction callback robust to its documented initial null invocation.
f = functions_path.read_text()
tx_old = "  const transaction = await db.ref('/').transaction((root) => {"
tx_new = """  const orderRootRef = db.ref('/');
  const initialOrderRoot = (await orderRootRef.once('value')).val();
  const transaction = await orderRootRef.transaction((root) => {
    if (root === null && initialOrderRoot !== null) {
      root = JSON.parse(JSON.stringify(initialOrderRoot));
    }"""
if f.count(tx_old) != 1:
    raise SystemExit(f'Authoritative order transaction anchor expected once, found {f.count(tx_old)}')
f = f.replace(tx_old, tx_new, 1)
functions_path.write_text(f)

print('Applied exactly four P1 baseline reconciliation changes')
