from pathlib import Path
import re
hp=Path('index.html'); bp=Path('functions/index.js'); h=hp.read_text(); b=bp.read_text()

def one(old,new,label):
    global h
    if old not in h: raise SystemExit('missing '+label)
    h=h.replace(old,new,1)

def fn(src,name,new):
    m=re.search(r'^[ \t]*(?:async\s+)?function\s+'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',src,re.M)
    if not m: raise SystemExit('fn '+name)
    start=m.start(); brace=src.find('{',m.start()); i=brace+1; d=1; st='code'; esc=False
    while i<len(src) and d:
        c=src[i]; n=src[i+1] if i+1<len(src) else ''
        if st=='line':
            if c=='\n': st='code'
        elif st=='block':
            if c=='*' and n=='/': st='code'; i+=1
        elif st in ('sq','dq','tpl'):
            if esc: esc=False
            elif c=='\\': esc=True
            elif st=='sq' and c=="'": st='code'
            elif st=='dq' and c=='"': st='code'
            elif st=='tpl' and c=='`': st='code'
        else:
            if c=='/' and n=='/': st='line'; i+=1
            elif c=='/' and n=='*': st='block'; i+=1
            elif c=="'": st='sq'
            elif c=='"': st='dq'
            elif c=='`': st='tpl'
            elif c=='{': d+=1
            elif c=='}': d-=1
        i+=1
    if d: raise SystemExit('unbalanced '+name)
    return src[:start]+new+src[i:]

# Product form fields.
anchor='''                <div class="form-group">\n                    <label>Status</label>'''
fields='''                <div class="form-group">\n                    <label for="productSizes">Available Sizes</label>\n                    <input type="text" id="productSizes" placeholder="XS, S, M, L, XL">\n                    <p style="font-size:.8rem;color:#666;margin-top:.4rem;">Comma-separated; leave blank if size does not apply.</p>\n                </div>\n                <div class="form-group">\n                    <label for="productColors">Available Colors</label>\n                    <input type="text" id="productColors" placeholder="Black, White, Sand">\n                    <p style="font-size:.8rem;color:#666;margin-top:.4rem;">Comma-separated; leave blank if color does not apply.</p>\n                </div>\n                <div class="form-group">\n                    <label for="productGalleryUrls">Additional Image URLs</label>\n                    <textarea id="productGalleryUrls" rows="3" placeholder="One HTTPS image URL per line"></textarea>\n                    <p style="font-size:.8rem;color:#666;margin-top:.4rem;">Up to five additional images.</p>\n                </div>\n\n'''
if 'id="productSizes"' not in h: one(anchor,fields+anchor,'product fields')

# Product detail controls.
h=h.replace('<div class="product-detail-modal" id="productDetailModal">','<div class="product-detail-modal" id="productDetailModal" role="dialog" aria-modal="true" aria-labelledby="detailName" aria-hidden="true">',1)
h=h.replace('<button class="close-modal" onclick="closeProductDetail()" style="position: absolute; top: 1rem; right: 1rem; z-index: 1;">×</button>','<button type="button" class="close-modal" onclick="closeProductDetail()" aria-label="Close product details" style="position: absolute; top: 1rem; right: 1rem; z-index: 1;">×</button>',1)
h=h.replace('<img id="detailImage" class="product-detail-image" src="" alt="">','<img id="detailImage" class="product-detail-image" src="" alt="">\n                    <div class="product-gallery-thumbs" id="detailGallery"></div>',1)
h=h.replace('<div class="product-detail-stock" id="detailStock"></div>','''<div class="product-detail-stock" id="detailStock"></div>\n                    <div class="variant-group" id="detailSizesGroup" style="display:none;"><span class="variant-group-label">Size</span><div class="variant-options" id="detailSizes"></div></div>\n                    <div class="variant-group" id="detailColorsGroup" style="display:none;"><span class="variant-group-label">Color</span><div class="variant-options" id="detailColors"></div></div>''',1)

# CSS.
css='''        .shop-filters { display:flex; justify-content:center; gap:.75rem; flex-wrap:wrap; }\n'''
if '.product-gallery-thumbs {' not in h:
    one(css,css+'''        .product-gallery-thumbs { display:flex; gap:.6rem; flex-wrap:wrap; margin-top:.75rem; }\n        .product-gallery-thumb { width:68px; height:68px; object-fit:cover; border:2px solid var(--border); background:white; }\n        .product-gallery-thumb.active { border-color:var(--accent); }\n        .variant-group { margin:1rem 0; }\n        .variant-group-label { display:block; font-weight:700; margin-bottom:.5rem; }\n        .variant-options { display:flex; gap:.5rem; flex-wrap:wrap; }\n        .variant-option { min-width:44px; min-height:44px; padding:.55rem .8rem; border:2px solid var(--border); background:white; font-weight:600; }\n        .variant-option.selected { border-color:var(--primary); background:var(--primary); color:white; }\n''','gallery css')

h=h.replace("let currentProductDetail = null;","let currentProductDetail = null;\n        let currentProductSelection = { size: '', color: '' };\n        let lastModalFocus = null;",1)

helper='''        function selectProductImage(src, button) { document.getElementById('detailImage').src=src; document.querySelectorAll('.product-gallery-thumb').forEach(el=>el.classList.remove('active')); button?.classList.add('active'); }\n        function selectProductVariant(type,value,button) { currentProductSelection[type]=value; button?.parentElement?.querySelectorAll('.variant-option').forEach(el=>el.classList.remove('selected')); button?.classList.add('selected'); }\n\n'''
one('        // Product Detail Modal Functions\n',helper+'        // Product Detail Modal Functions\n','detail marker')

new_open='''        function openProductDetail(productId) {\n            const product=products.find(p=>Number(p.id)===Number(productId)); if(!product)return;\n            currentProductDetail=product; currentProductSelection={size:'',color:''}; lastModalFocus=document.activeElement;\n            const images=(Array.isArray(product.images)?product.images:[]).filter(Boolean); if(!images.length&&product.image)images.push(product.image);\n            const main=document.getElementById('detailImage'); main.src=images[0]||''; main.alt=product.name||'Product image';\n            const gallery=document.getElementById('detailGallery'); gallery.innerHTML=images.length>1?images.map((src,i)=>`<button type="button" class="product-gallery-thumb ${i===0?'active':''}" onclick="selectProductImage(${JSON.stringify(src)},this)" aria-label="View image ${i+1} of ${images.length}"><img src="${escapeHTML(src)}" alt="" loading="lazy" style="width:100%;height:100%;object-fit:cover;"></button>`).join(''):'';\n            document.getElementById('detailCategory').textContent=product.category||''; document.getElementById('detailName').textContent=product.name||''; document.getElementById('detailPrice').textContent=`EGP ${Number(product.price).toFixed(2)}`; document.getElementById('detailDescription').textContent=product.description||''; document.getElementById('detailStock').textContent=Number(product.stock)<10?`⚠️ Only ${Number(product.stock)} left in stock!`:`✓ ${Number(product.stock)} in stock`;\n            const sizes=Array.isArray(product.sizes)?product.sizes.filter(Boolean):[], colors=Array.isArray(product.colors)?product.colors.filter(Boolean):[];\n            document.getElementById('detailSizesGroup').style.display=sizes.length?'block':'none'; document.getElementById('detailColorsGroup').style.display=colors.length?'block':'none';\n            document.getElementById('detailSizes').innerHTML=sizes.map(v=>`<button type="button" class="variant-option" onclick="selectProductVariant('size',${JSON.stringify(v)},this)">${escapeHTML(v)}</button>`).join(''); document.getElementById('detailColors').innerHTML=colors.map(v=>`<button type="button" class="variant-option" onclick="selectProductVariant('color',${JSON.stringify(v)},this)">${escapeHTML(v)}</button>`).join('');\n            const qty=document.getElementById('quantityInput'); qty.value=1; qty.max=Math.max(1,Number(product.stock)||1); loadRecommendedProducts(product.category,product.id);\n            const modal=document.getElementById('productDetailModal'); modal.classList.add('active'); modal.setAttribute('aria-hidden','false'); document.body.style.overflow='hidden'; modal.querySelector('.close-modal')?.focus();\n        }\n'''
h=fn(h,'openProductDetail',new_open)
new_close='''        function closeProductDetail() { const modal=document.getElementById('productDetailModal'); modal.classList.remove('active'); modal.setAttribute('aria-hidden','true'); document.body.style.overflow='auto'; currentProductDetail=null; currentProductSelection={size:'',color:''}; if(lastModalFocus&&document.contains(lastModalFocus))lastModalFocus.focus(); lastModalFocus=null; }\n'''
h=fn(h,'closeProductDetail',new_close)

new_detail_add='''        function addToCartFromDetail() {\n            if(!currentProductDetail)return; const p=currentProductDetail; const sizes=Array.isArray(p.sizes)?p.sizes.filter(Boolean):[], colors=Array.isArray(p.colors)?p.colors.filter(Boolean):[];\n            if(sizes.length&&!currentProductSelection.size){alert('Please select a size.');return;} if(colors.length&&!currentProductSelection.color){alert('Please select a color.');return;}\n            const quantity=Math.max(1,parseInt(document.getElementById('quantityInput').value,10)||1); if(quantity>Number(p.stock)){alert('Selected quantity is no longer available.');return;}\n            const d=productDiscounts.find(x=>Number(x.productId)===Number(p.id)&&x.status==='active'); let price=Number(p.price); if(d)price=d.type==='percentage'?price*(1-Number(d.value)/100):price-Number(d.value); price=Math.max(0,price);\n            const size=currentProductSelection.size||'', color=currentProductSelection.color||''; const existing=cart.find(x=>Number(x.id)===Number(p.id)&&(x.size||'')===size&&(x.color||'')===color);\n            if(existing){if(existing.quantity+quantity>Number(p.stock)){alert('Not enough stock.');return;} existing.quantity+=quantity;} else cart.push({id:p.id,name:p.name,price,originalPrice:Number(p.price),image:p.images?.[0]||p.image,quantity,size,color});\n            updateCartBadge(); alert(`${quantity}x ${p.name} added to cart!`); closeProductDetail();\n        }\n'''
h=fn(h,'addToCartFromDetail',new_detail_add)

# Product form edit fields.
h=h.replace("document.getElementById('productImageData').value = product.image;","document.getElementById('productImageData').value = product.image || product.images?.[0] || '';\n                document.getElementById('productSizes').value = Array.isArray(product.sizes) ? product.sizes.join(', ') : '';\n                document.getElementById('productColors').value = Array.isArray(product.colors) ? product.colors.join(', ') : '';\n                document.getElementById('productGalleryUrls').value = Array.isArray(product.images) ? product.images.slice(1).join('\\n') : '';",1)

new_save='''        async function saveProduct(event) {\n            event.preventDefault(); const button=document.querySelector('#productForm button[type="submit"]'); const id=Number(document.getElementById('productId').value)||null; const existing=id?products.find(p=>Number(p.id)===id):null; const split=v=>[...new Set(String(v||'').split(',').map(x=>x.trim()).filter(Boolean))]; const main=document.getElementById('productImageData').value||existing?.image||existing?.images?.[0]||''; const extras=String(document.getElementById('productGalleryUrls').value||'').split(/\\r?\\n/).map(x=>x.trim()).filter(Boolean);\n            const data={name:document.getElementById('productName').value.trim(),category:document.getElementById('productCategory').value,description:document.getElementById('productDescription').value.trim(),price:parseFloat(document.getElementById('productPrice').value),stock:parseInt(document.getElementById('productStock').value,10),status:document.getElementById('productStatus').value==='Active'?'Active':'Inactive',image:main,images:[main,...extras].filter(Boolean).slice(0,6),sizes:split(document.getElementById('productSizes').value).slice(0,12),colors:split(document.getElementById('productColors').value).slice(0,12)};\n            if(!data.name||!data.category||!Number.isFinite(data.price)||!Number.isInteger(data.stock)||data.stock<0){alert('Please complete all product fields with valid values.');return;} const next=products.map(p=>({...p})); if(id){const i=next.findIndex(p=>Number(p.id)===id);if(i<0){alert('Product no longer exists.');return;}next[i]={...next[i],...data};}else next.push({id:nextProductId,...data});\n            try{if(button){button.disabled=true;button.textContent='Saving…';}await saveToFirebase('products',next);products=next;if(!id)nextProductId++;loadProducts();renderShopProducts();closeProductForm();updateInventoryOverview();alert('Product saved successfully.');}catch(error){console.error('Product save failed:',error);alert(error?.message||'Unable to save product.');}finally{if(button){button.disabled=false;button.textContent='Save Product';}}\n        }\n'''
h=fn(h,'saveProduct',new_save)

# Carry variant selection into server quote/order payload; prices remain omitted.
h=h.replace("({ id: item.id, quantity: item.quantity })","({ id: item.id, quantity: item.quantity, size: item.size || '', color: item.color || '' })")
h=h.replace("<span>${escapeHTML(item.name)} x${item.quantity}</span>","<span>${escapeHTML(item.name)}${item.size ? ` · ${escapeHTML(item.size)}` : ''}${item.color ? ` · ${escapeHTML(item.color)}` : ''} x${item.quantity}</span>",1)

# Backend sanitizer + authoritative variant validation.
old="""      image: cleanImageSource(product.image)\n    };"""
new="""      image: cleanImageSource(product.image),\n      images: normalizeList(product.images).map(cleanImageSource).filter(Boolean).slice(0, 6),\n      sizes: normalizeList(product.sizes).map((v) => cleanMarkupText(v, 40)).filter(Boolean).slice(0, 12),\n      colors: normalizeList(product.colors).map((v) => cleanMarkupText(v, 40)).filter(Boolean).slice(0, 12)\n    };\n    if (!safe.images.length && safe.image) safe.images = [safe.image];\n    if (!safe.image && safe.images.length) safe.image = safe.images[0];"""
if old not in b: raise SystemExit('backend product schema')
b=b.replace(old,new,1)
needle="""    const unitPrice = getDiscountedUnitPrice(product, productDiscounts);\n    normalizedItems.push({\n      storageKey,\n      id: product.id,\n      name: cleanText(product.name, 120),\n      quantity,\n      unitPrice,\n      lineTotal: unitPrice * quantity\n    });"""
repl="""    const requestedSize = cleanText(requested?.size, 40);\n    const requestedColor = cleanText(requested?.color, 40);\n    const sizes = normalizeList(product.sizes).map((v) => cleanText(v, 40));\n    const colors = normalizeList(product.colors).map((v) => cleanText(v, 40));\n    if (sizes.length && !sizes.includes(requestedSize)) throw new HttpsError('failed-precondition', `Choose a valid size for ${cleanText(product.name, 100)}.`);\n    if (colors.length && !colors.includes(requestedColor)) throw new HttpsError('failed-precondition', `Choose a valid color for ${cleanText(product.name, 100)}.`);\n    const unitPrice = getDiscountedUnitPrice(product, productDiscounts);\n    normalizedItems.push({ storageKey, id: product.id, name: cleanText(product.name, 120), quantity, size: sizes.length ? requestedSize : '', color: colors.length ? requestedColor : '', unitPrice, lineTotal: unitPrice * quantity });"""
if needle not in b: raise SystemExit('backend quote item')
b=b.replace(needle,repl,1)
b=b.replace("price: item.unitPrice\n      }))","price: item.unitPrice,\n        size: item.size || '',\n        color: item.color || ''\n      }))",1)

hp.write_text(h); bp.write_text(b); print('variants/gallery batch applied')
