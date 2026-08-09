from pathlib import Path
import re

hp=Path('index.html'); h=hp.read_text()

def replace_fn(name,new):
    global h
    m=re.search(r'^[ \t]*(?:async\s+)?function\s+'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',h,re.M)
    if not m: raise SystemExit('function not found '+name)
    start=m.start(); brace=h.find('{',m.start()); i=brace+1; depth=1; state='code'; esc=False
    while i<len(h) and depth:
        c=h[i]; n=h[i+1] if i+1<len(h) else ''
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
    h=h[:start]+new+h[i:]

def remove_fn(name):
    while re.search(r'^[ \t]*(?:async\s+)?function\s+'+re.escape(name)+r'\s*\(',h,re.M): replace_fn(name,'')

h=h.replace('https://buykem.com/og-image.jpg','https://buykem.com/icon%20enhanced.png')
h=h.replace('"telephone": "+20-XXX-XXXX-XXX",\n      ', '')
h=h.replace('"logo": "https://buykem.com/logo.png",','"logo": "https://buykem.com/icon%20enhanced.png",')
h=h.replace('"image": "https://buykem.com/og-image.jpg",','"image": "https://buykem.com/icon%20enhanced.png",')
h=h.replace('''      "acceptedPaymentMethod": [\n        "Cash",\n        "CreditCard",\n        "DebitCard"\n      ],''','''      "acceptedPaymentMethod": ["Cash"],''')
h=h.replace('"paymentAccepted": "Cash on Delivery, Credit Card, Debit Card",','"paymentAccepted": "Cash on Delivery",')

h=re.sub(r'\s*<script src="https://js\.stripe\.com/v3/"></script>','',h,count=1)
remove_fn('initializeStripe')
remove_fn('processStripePayment')
h=re.sub(r"\n\s*const stripeConfig = \{.*?\};\n\s*let stripe, stripeInitialized = false;\n",'\n',h,count=1,flags=re.S)

h=re.sub(r'\s*<script src="https://www\.gstatic\.com/firebasejs/[^\"]+/firebase-storage\.js"></script>','',h,count=1)
h=h.replace('let db, auth, storage, cloudFunctions;','let db, auth, cloudFunctions;')
h=h.replace('                storage = firebase.storage();\n','')
remove_fn('parseJwt')

meta_helpers='''        const homeSeo = {\n            title: document.title,\n            description: document.querySelector('meta[name="description"]')?.content || '',\n            canonical: document.querySelector('link[rel="canonical"]')?.href || 'https://buykem.com/'\n        };\n\n        function updateProductSeo(product) {\n            if (!product) return;\n            const title = `${product.name} — KEM`;\n            const description = String(product.description || `Shop ${product.name} from KEM.`).slice(0, 160);\n            const url = new URL(window.location.href);\n            url.searchParams.set('product', product.id);\n            document.title = title;\n            document.querySelector('meta[name="description"]')?.setAttribute('content', description);\n            document.querySelector('link[rel="canonical"]')?.setAttribute('href', url.href);\n            document.querySelector('meta[property="og:title"]')?.setAttribute('content', title);\n            document.querySelector('meta[property="og:description"]')?.setAttribute('content', description);\n            document.querySelector('meta[property="og:url"]')?.setAttribute('content', url.href);\n            document.querySelector('meta[name="twitter:title"]')?.setAttribute('content', title);\n            document.querySelector('meta[name="twitter:description"]')?.setAttribute('content', description);\n            const image = product.images?.[0] || product.image;\n            if (image) { document.querySelector('meta[property="og:image"]')?.setAttribute('content', image); document.querySelector('meta[name="twitter:image"]')?.setAttribute('content', image); }\n        }\n\n        function restoreHomeSeo() {\n            document.title = homeSeo.title;\n            document.querySelector('meta[name="description"]')?.setAttribute('content', homeSeo.description);\n            document.querySelector('link[rel="canonical"]')?.setAttribute('href', homeSeo.canonical);\n            document.querySelector('meta[property="og:title"]')?.setAttribute('content', 'KEM — Premium Egyptian Streetwear | Urban Fashion Online Store');\n            document.querySelector('meta[property="og:description"]')?.setAttribute("content", "Shop KEM's exclusive collection of streetwear clothing in Egypt. Premium hoodies, t-shirts, cargo pants & urban fashion. Free shipping over EGP 1000.");\n            document.querySelector('meta[property="og:url"]')?.setAttribute('content', 'https://buykem.com');\n            document.querySelector('meta[property="og:image"]')?.setAttribute('content', 'https://buykem.com/icon%20enhanced.png');\n            document.querySelector('meta[name="twitter:title"]')?.setAttribute('content', 'KEM — Premium Egyptian Streetwear');\n            document.querySelector('meta[name="twitter:description"]')?.setAttribute('content', 'Shop exclusive streetwear collections. Free shipping over EGP 1000. Cash on delivery available.');\n            document.querySelector('meta[name="twitter:image"]')?.setAttribute('content', 'https://buykem.com/icon%20enhanced.png');\n        }\n\n'''
marker='        // Product Detail Modal Functions\n'
if 'function updateProductSeo' not in h:
    if marker not in h: raise SystemExit('detail marker missing')
    h=h.replace(marker,meta_helpers+marker,1)

h=h.replace('function openProductDetail(productId) {','function openProductDetail(productId, options = {}) {',1)
needle="""            const modal=document.getElementById('productDetailModal'); modal.classList.add('active'); modal.setAttribute('aria-hidden','false'); document.body.style.overflow='hidden'; modal.querySelector('.close-modal')?.focus();"""
repl=needle+"""\n            updateProductSeo(product);\n            if (!options.fromHistory) { const url=new URL(window.location.href); url.searchParams.set('product', product.id); history.pushState({productId: product.id}, '', url); }"""
if needle not in h: raise SystemExit('open detail tail missing')
h=h.replace(needle,repl,1)

replace_fn('closeProductDetail', '''        function closeProductDetail(options = {}) {\n            const modal=document.getElementById('productDetailModal'); modal.classList.remove('active'); modal.setAttribute('aria-hidden','true'); document.body.style.overflow='auto'; currentProductDetail=null; currentProductSelection={size:'',color:''};\n            if (!options.fromHistory) { const url=new URL(window.location.href); if(url.searchParams.has('product')){url.searchParams.delete('product');history.pushState({},'',url);} }\n            restoreHomeSeo(); if(lastModalFocus&&document.contains(lastModalFocus))lastModalFocus.focus(); lastModalFocus=null;\n        }\n''')

old='<h3>${escapeHTML(p.name)}</h3><div class="product-price">'
new='<h3><a href="?product=${Number(p.id)}" onclick="event.preventDefault();event.stopPropagation();openProductDetail(${Number(p.id)})" style="color:inherit;text-decoration:none;">${escapeHTML(p.name)}</a></h3><div class="product-price">'
if old not in h: raise SystemExit('product title card marker')
h=h.replace(old,new,1)

startup='''            renderFooterSocialLinks();\n            makeDashboardTablesResponsive();\n            enhanceAccessibility();'''
if startup in h and 'initialProductId' not in h:
    h=h.replace(startup,startup+'''\n            const initialProductId=Number(new URL(window.location.href).searchParams.get('product'));\n            if(initialProductId) openProductDetail(initialProductId,{fromHistory:true});''',1)
if "window.addEventListener('popstate'" not in h:
    h=h.replace("        document.addEventListener('keydown', event => {",'''        window.addEventListener('popstate', () => {\n            const id=Number(new URL(window.location.href).searchParams.get('product'));\n            if(id) openProductDetail(id,{fromHistory:true}); else if(document.getElementById('productDetailModal')?.classList.contains('active')) closeProductDetail({fromHistory:true});\n        });\n\n        document.addEventListener('keydown', event => {''',1)

hp.write_text(h)

Path('sitemap.xml').write_text('''<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url>\n    <loc>https://buykem.com/</loc>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n</urlset>\n''')
Path('robots.txt').write_text('''User-agent: *\nAllow: /\n\nSitemap: https://buykem.com/sitemap.xml\n''')

for name in ['payment-success.html','payment-failed.html']:
    pp=Path(name)
    text=pp.read_text()
    if 'name="robots"' not in text:
        text=text.replace('<head>','<head>\n    <meta name="robots" content="noindex, nofollow">',1)
    pp.write_text(text)

print('SEO/performance batch applied')
