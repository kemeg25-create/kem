from pathlib import Path
import re
p=Path('index.html'); s=p.read_text()

def one(old,new,label):
    global s
    if old not in s: raise SystemExit('missing '+label)
    s=s.replace(old,new,1)

def replace_fn(name,new,which=0):
    global s
    ms=list(re.finditer(r'^[ \t]*(?:async\s+)?function\s+'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',s,re.M))
    if not ms: raise SystemExit('fn '+name)
    m=ms[which]; start=m.start(); brace=s.find('{',m.start()); i=brace+1; depth=1; state='code'; esc=False
    while i<len(s) and depth:
        c=s[i]; n=s[i+1] if i+1<len(s) else ''
        if state=='line':
            if c=='\n': state='code'
        elif state=='block':
            if c=='*' and n=='/': state='code'; i+=1
        elif state in ('sq','dq','tpl'):
            if esc: esc=False
            elif c=='\\': esc=True
            elif state=='sq' and c=="'": state='code'
            elif state=='dq' and c=='"': state='code'
            elif state=='tpl' and c=='`': state='code'
        else:
            if c=='/' and n=='/': state='line'; i+=1
            elif c=='/' and n=='*': state='block'; i+=1
            elif c=="'": state='sq'
            elif c=='"': state='dq'
            elif c=='`': state='tpl'
            elif c=='{': depth+=1
            elif c=='}': depth-=1
        i+=1
    s=s[:start]+new+s[i:]

def remove_fn(name):
    while re.search(r'^[ \t]*(?:async\s+)?function\s+'+re.escape(name)+r'\s*\(',s,re.M): replace_fn(name,'',0)

css='''        .nav-links a:hover::after {\n            width: 100%;\n        }\n'''
if '.mobile-nav-toggle {' not in s:
    one(css,css+'''\n        .mobile-nav-toggle { display:none; width:44px; height:44px; border:2px solid var(--primary); background:white; font-size:1.35rem; align-items:center; justify-content:center; }\n        .shop-tools { max-width:1400px; margin:0 auto 2rem; display:grid; gap:1rem; }\n        .shop-search { width:min(100%,560px); margin:auto; padding:.9rem 1rem; border:2px solid var(--border); font:inherit; background:white; }\n        .shop-filters { display:flex; justify-content:center; gap:.75rem; flex-wrap:wrap; }\n        :focus-visible { outline:3px solid var(--accent); outline-offset:3px; }\n        .data-table-wrap { width:100%; overflow-x:auto; -webkit-overflow-scrolling:touch; }\n''','css')

old='''        @media (max-width: 768px) {\n            .nav-links {\n                display: none;\n            }\n'''
new='''        @media (max-width: 1024px) {\n            nav { padding:1rem 10rem 1rem 1.25rem; }\n            .dashboard-tabs { overflow-x:auto; white-space:nowrap; }\n            .data-table { min-width:720px; }\n        }\n\n        @media (max-width: 768px) {\n            nav { padding:.75rem 1rem; min-height:72px; }\n            .logo { font-size:2rem; }\n            .logo img { height:38px; }\n            .mobile-nav-toggle { display:inline-flex; margin-left:auto; }\n            .nav-links { display:none; position:absolute; top:100%; left:0; right:0; background:white; border-bottom:1px solid var(--border); padding:1rem; flex-direction:column; align-items:stretch; gap:0; max-height:calc(100vh - 72px); overflow-y:auto; }\n            .nav-links.mobile-open { display:flex; }\n            .nav-links > li, .nav-links a, .nav-dropdown-btn { width:100%; }\n            .nav-links a, .nav-dropdown-btn { padding:.85rem .5rem; display:flex; }\n            .nav-dropdown-content { position:static; box-shadow:none; margin-top:0; width:100%; }\n            .shop { padding:4rem 1rem !important; }\n            .collections { padding:4rem 1rem; }\n            .section-title { font-size:2.5rem; }\n'''
if old in s: s=s.replace(old,new,1)

one('<ul class="nav-links">','<button type="button" class="mobile-nav-toggle" id="mobileNavToggle" aria-expanded="false" aria-controls="primaryNav" aria-label="Open navigation" onclick="toggleMobileNav()">☰</button>\n        <ul class="nav-links" id="primaryNav">','nav markup')

pat=re.compile(r'\s*<!-- Filter Buttons -->\s*<div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 3rem;">.*?</div>\s*\n\s*<!-- Products Grid -->',re.S)
s,n=pat.subn('''\n            <div class="shop-tools">\n                <label for="shopSearch" style="position:absolute;left:-9999px;">Search products</label>\n                <input class="shop-search" type="search" id="shopSearch" placeholder="Search products or collections" autocomplete="off" oninput="setShopSearch(this.value)">\n                <div class="shop-filters" id="shopFilterButtons" aria-label="Filter products by collection"></div>\n                <p id="shopResultsStatus" style="text-align:center;color:#666;margin:0;" aria-live="polite"></p>\n            </div>\n\n            <!-- Products Grid -->''',s,count=1)
if n!=1: raise SystemExit('shop markup')

s=s.replace("let cart = [];\n        let currentProductDetail = null;","let cart = [];\n        let shopCategoryFilter = 'all';\n        let shopSearchTerm = '';\n        let currentProductDetail = null;",1)

remove_fn('filterByCategory')
helpers='''        function getCategoryName(category) { return typeof category === 'string' ? category : String(category?.name || ''); }\n\n        function renderShopFilters() {\n            const el=document.getElementById('shopFilterButtons'); if(!el)return;\n            const names=[...new Set(categories.map(getCategoryName).filter(Boolean))];\n            el.innerHTML=['all',...names].map(name=>`<button type="button" class="filter-btn ${shopCategoryFilter===name?'active':''}" data-category="${escapeHTML(name)}" onclick="filterByCategory(${JSON.stringify(name)})">${escapeHTML(name==='all'?'All Products':name)}</button>`).join('');\n        }\n\n        function filterByCategory(name) { shopCategoryFilter=name||'all'; renderShopFilters(); renderShopProducts(); document.getElementById('categoriesDropdown')?.classList.remove('active'); }\n        function setShopSearch(value) { shopSearchTerm=String(value||''); renderShopProducts(); }\n        function toggleMobileNav(forceOpen) {\n            const nav=document.getElementById('primaryNav'), btn=document.getElementById('mobileNavToggle'); if(!nav||!btn)return;\n            const open=typeof forceOpen==='boolean'?forceOpen:!nav.classList.contains('mobile-open');\n            nav.classList.toggle('mobile-open',open); btn.setAttribute('aria-expanded',String(open)); btn.setAttribute('aria-label',open?'Close navigation':'Open navigation'); btn.textContent=open?'×':'☰';\n        }\n\n'''
marker='        // Product Detail Modal Functions\n'
one(marker,helpers+marker,'helper marker')

new_render='''        function renderShopProducts() {\n            const grid=document.getElementById('shopProductsGrid'); if(!grid)return;\n            const q=String(shopSearchTerm||'').trim().toLowerCase();\n            const shown=products.filter(p=>p.status==='Active'&&(shopCategoryFilter==='all'||p.category===shopCategoryFilter)&&(!q||String(p.name||'').toLowerCase().includes(q)||String(p.category||'').toLowerCase().includes(q)||String(p.description||'').toLowerCase().includes(q)));\n            const status=document.getElementById('shopResultsStatus'); if(status)status.textContent=`${shown.length} product${shown.length===1?'':'s'} found`;\n            if(!shown.length){grid.innerHTML='<div style="grid-column:1/-1;text-align:center;padding:3rem 1rem;"><h3>No products found</h3><p style="color:#666;margin-top:.5rem;">Try another search or collection.</p></div>';return;}\n            grid.innerHTML=shown.map(p=>`<article class="product-card" tabindex="0" onclick="openProductDetail(${Number(p.id)})" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();openProductDetail(${Number(p.id)})}"><img src="${escapeHTML(p.images?.[0]||p.image||'')}" alt="${escapeHTML(p.name)}" loading="lazy" decoding="async"><div class="product-info"><div class="product-category">${escapeHTML(p.category)}</div><h3>${escapeHTML(p.name)}</h3><div class="product-price">EGP ${Number(p.price).toFixed(2)}</div><div class="product-stock">${Number(p.stock)>0?`${Number(p.stock)} in stock`:'Out of stock'}</div></div></article>`).join('');\n        }\n'''
replace_fn('renderShopProducts',new_render,0)

s=s.replace("['categories', data => { categories = firebaseList(data); renderCategoriesDropdown(); }],","['categories', data => { categories = firebaseList(data); renderCategoriesDropdown(); renderShopFilters(); renderShopProducts(); }],",1)
s=s.replace('renderCategoriesDropdown();\n            renderFooterSocialLinks();','renderCategoriesDropdown();\n            renderShopFilters();\n            renderFooterSocialLinks();',1)
s=s.replace("target.scrollIntoView({ behavior: 'smooth' });","target.scrollIntoView({ behavior: 'smooth' });\n                    toggleMobileNav(false);",1)

p.write_text(s)
print('mobile/search batch applied')
