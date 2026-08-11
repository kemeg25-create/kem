from pathlib import Path
import re

path = Path('index.html')
h = path.read_text()

BASELINE = 'P2.3 — COLLECTION / SHOP'
assert BASELINE in h
assert 'P2.4 — PRODUCT DETAIL' not in h
assert "function openProductDetail(productId, options = {})" in h
assert "function addToCartFromDetail()" in h
assert "id=\"productDetailModal\"" in h

style_anchor = '''        @media (prefers-reduced-motion: reduce) {
            .shop-product-image,
            #shop .filter-btn { transition: none !important; }
        }


    </style>'''
assert style_anchor in h

p24_css = r'''

        /* P2.4 — PRODUCT DETAIL */
        #productDetailModal.product-detail-modal {
            padding: 0;
            background: rgba(10, 10, 10, 0.78);
        }

        #productDetailModal .product-detail-content {
            width: min(calc(100% - (2 * var(--page-gutter))), var(--container-customer));
            max-width: var(--container-customer);
            margin: var(--space-32) auto;
            background: var(--color-white);
            color: var(--color-ink);
            box-shadow: none;
        }

        .product-detail-topbar {
            min-height: 64px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: var(--space-16);
            padding: var(--space-12) var(--space-24);
            border-bottom: 1px solid var(--color-neutral-200);
        }

        #productDetailModal .product-detail-back,
        #productDetailModal .product-detail-close {
            min-width: 44px;
            min-height: 44px;
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            background: var(--color-white);
            color: var(--color-ink);
            font: 600 var(--type-ui)/1 var(--font-ui);
            text-transform: none;
            letter-spacing: 0;
            transition: background-color var(--motion-fast) var(--ease-standard), color var(--motion-fast) var(--ease-standard), border-color var(--motion-fast) var(--ease-standard);
        }

        #productDetailModal .product-detail-back {
            padding: var(--space-12) var(--space-16);
        }

        #productDetailModal .product-detail-close {
            position: static;
            width: 44px;
            height: 44px;
            padding: 0;
            font-size: 1.5rem;
        }

        #productDetailModal .product-detail-back:hover,
        #productDetailModal .product-detail-close:hover {
            border-color: var(--color-ink);
            background: var(--color-ink);
            color: var(--color-white);
        }

        #productDetailModal .product-detail-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.35fr) minmax(340px, 0.75fr);
            gap: var(--space-64);
            align-items: start;
            padding: var(--space-48);
        }

        .product-detail-media-panel,
        #productDetailModal .product-detail-info {
            min-width: 0;
        }

        .product-detail-main-media {
            width: 100%;
            aspect-ratio: 4 / 5;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid var(--color-neutral-200);
            background: var(--color-neutral-50);
        }

        #productDetailModal .product-detail-image {
            width: 100%;
            height: 100%;
            aspect-ratio: auto;
            display: block;
            padding: var(--space-24);
            background: transparent;
            object-fit: contain;
        }

        #productDetailModal .product-gallery-thumbs {
            display: flex;
            flex-wrap: wrap;
            gap: var(--space-8);
            margin-top: var(--space-12);
        }

        #productDetailModal .product-gallery-thumbs[hidden] { display: none; }

        #productDetailModal .product-gallery-thumb {
            width: 72px;
            height: 90px;
            min-width: 44px;
            min-height: 44px;
            padding: var(--space-4);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            background: var(--color-white);
            transition: border-color var(--motion-fast) var(--ease-standard), background-color var(--motion-fast) var(--ease-standard);
        }

        #productDetailModal .product-gallery-thumb.active,
        #productDetailModal .product-gallery-thumb[aria-pressed="true"] {
            border-color: var(--color-ink);
            box-shadow: inset 0 0 0 1px var(--color-ink);
        }

        #productDetailModal .product-gallery-thumb img {
            width: 100%;
            height: 100%;
            display: block;
            object-fit: contain !important;
        }

        #productDetailModal .product-detail-info {
            width: 100%;
            max-width: 480px;
        }

        #productDetailModal .product-detail-category {
            margin: 0 0 var(--space-12);
            color: var(--color-neutral-600);
            font: 600 var(--type-metadata)/1.35 var(--font-ui);
            letter-spacing: 0.08em;
            text-transform: uppercase;
            overflow-wrap: anywhere;
        }

        #productDetailModal .product-detail-info h2 {
            min-width: 0;
            margin: 0;
            color: var(--color-ink);
            font-family: var(--font-display);
            font-size: clamp(2.75rem, 5vw, 4.75rem);
            font-weight: 400;
            line-height: 0.94;
            letter-spacing: 0.01em;
            overflow-wrap: anywhere;
        }

        #productDetailModal .product-detail-price {
            min-width: 0;
            display: flex;
            flex-wrap: wrap;
            align-items: baseline;
            gap: var(--space-8) var(--space-12);
            margin: var(--space-16) 0 var(--space-24);
            color: var(--color-ink);
            font: 600 clamp(1.35rem, 2.2vw, 1.75rem)/1.2 var(--font-ui);
            overflow-wrap: anywhere;
        }

        .product-detail-original-price {
            color: var(--color-neutral-400);
            font-weight: 400;
            text-decoration: line-through;
        }

        .product-detail-sale-price { color: var(--color-ink); }

        .product-detail-sale-label {
            color: var(--color-kem-pink);
            font: 600 var(--type-metadata)/1.35 var(--font-ui);
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        #productDetailModal .product-detail-description {
            min-width: 0;
            margin: 0 0 var(--space-24);
            padding: var(--space-24) 0;
            border-top: 1px solid var(--color-neutral-200);
            border-bottom: 1px solid var(--color-neutral-200);
            color: var(--color-neutral-600);
            font: 400 var(--type-body)/1.65 var(--font-ui);
            overflow-wrap: anywhere;
        }

        #productDetailModal .product-detail-stock {
            margin: 0 0 var(--space-24);
            padding: 0;
            border: 0;
            background: transparent;
            color: var(--color-neutral-600);
            font: 600 var(--type-metadata)/1.35 var(--font-ui);
        }

        #productDetailModal .product-detail-stock.is-unavailable {
            color: var(--color-error);
        }

        #productDetailModal .variant-group {
            margin: 0 0 var(--space-24);
        }

        #productDetailModal .variant-group-label,
        .product-detail-quantity-label {
            display: block;
            margin-bottom: var(--space-8);
            color: var(--color-ink);
            font: 600 var(--type-ui)/1.3 var(--font-ui);
        }

        #productDetailModal .variant-options {
            display: flex;
            flex-wrap: wrap;
            gap: var(--space-8);
        }

        #productDetailModal .variant-option {
            min-width: 44px;
            min-height: 44px;
            padding: var(--space-8) var(--space-16);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            background: var(--color-white);
            color: var(--color-ink);
            font: 600 var(--type-ui)/1.2 var(--font-ui);
            transition: background-color var(--motion-fast) var(--ease-standard), color var(--motion-fast) var(--ease-standard), border-color var(--motion-fast) var(--ease-standard);
        }

        #productDetailModal .variant-option:hover {
            border-color: var(--color-neutral-600);
        }

        #productDetailModal .variant-option.selected,
        #productDetailModal .variant-option[aria-pressed="true"] {
            border-color: var(--color-ink);
            background: var(--color-ink);
            color: var(--color-white);
        }

        #productDetailModal .variant-option:disabled,
        #productDetailModal .variant-option[aria-disabled="true"] {
            border-color: var(--color-neutral-200);
            background: var(--color-neutral-100);
            color: var(--color-neutral-400);
            text-decoration: line-through;
            cursor: not-allowed !important;
        }

        .product-detail-quantity {
            margin: 0 0 var(--space-32);
        }

        #productDetailModal .quantity-selector {
            display: inline-flex;
            align-items: center;
            gap: 0;
            margin: 0;
        }

        #productDetailModal .quantity-selector button,
        #productDetailModal .quantity-selector input {
            min-height: 44px;
            height: 44px;
        }

        #productDetailModal .quantity-selector button {
            width: 44px;
            min-width: 44px;
            border: 1px solid var(--color-neutral-200);
            background: var(--color-white);
            color: var(--color-ink);
            font: 600 1.1rem/1 var(--font-ui);
            transition: background-color var(--motion-fast) var(--ease-standard), color var(--motion-fast) var(--ease-standard), border-color var(--motion-fast) var(--ease-standard);
        }

        #productDetailModal .quantity-selector button:hover {
            border-color: var(--color-ink);
            background: var(--color-ink);
            color: var(--color-white);
        }

        #productDetailModal .quantity-selector input {
            width: 64px;
            border: 1px solid var(--color-neutral-200);
            border-left: 0;
            border-right: 0;
            border-radius: 0;
            background: var(--color-white);
            color: var(--color-ink);
            text-align: center;
            font: 600 var(--type-ui)/1 var(--font-ui);
        }

        #productDetailModal .add-to-cart-btn {
            width: 100%;
            min-height: 56px;
            margin: 0;
            padding: var(--space-16) var(--space-24);
            border: 1px solid var(--color-ink);
            border-radius: var(--radius-xs);
            background: var(--color-ink);
            color: var(--color-white);
            font: 600 var(--type-ui)/1.2 var(--font-ui);
            letter-spacing: 0.04em;
            text-transform: uppercase;
            transform: none;
            box-shadow: none;
            transition: background-color var(--motion-fast) var(--ease-standard), border-color var(--motion-fast) var(--ease-standard);
        }

        #productDetailModal .add-to-cart-btn:hover {
            border-color: var(--color-kem-pink);
            background: var(--color-kem-pink);
            transform: none;
            box-shadow: none;
        }

        #productDetailModal .recommended-section {
            margin: 0;
            padding: var(--space-48);
            border-top: 1px solid var(--color-neutral-200);
            background: var(--color-off-white);
        }

        #productDetailModal .recommended-section[hidden] { display: none; }

        #productDetailModal .recommended-section h3 {
            margin: 0 0 var(--space-24);
            color: var(--color-ink);
            font-family: var(--font-display);
            font-size: var(--type-section-title);
            font-weight: 400;
            line-height: 1;
            letter-spacing: 0.02em;
        }

        #productDetailModal .recommended-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: var(--space-24);
            overflow: visible;
            padding: 0;
            scroll-snap-type: none;
        }

        #productDetailModal .recommended-product {
            min-width: 0;
            max-width: none;
            display: block;
            padding: 0;
            border: 0;
            background: transparent;
            color: var(--color-ink);
            text-decoration: none;
            box-shadow: none;
            transform: none;
        }

        #productDetailModal .recommended-product:hover {
            box-shadow: none;
            transform: none;
        }

        #productDetailModal .recommended-product img {
            width: 100%;
            aspect-ratio: 4 / 5;
            display: block;
            margin: 0 0 var(--space-12);
            padding: var(--space-8);
            border: 1px solid var(--color-neutral-200);
            background: var(--color-white);
            object-fit: contain;
        }

        #productDetailModal .recommended-product-name {
            margin: 0 0 var(--space-4);
            color: var(--color-ink);
            font: 600 var(--type-ui)/1.35 var(--font-ui);
            overflow-wrap: anywhere;
        }

        #productDetailModal .recommended-product-price {
            color: var(--color-neutral-600);
            font: 400 var(--type-ui)/1.35 var(--font-ui);
            overflow-wrap: anywhere;
        }

        @media (max-width: 1023px) {
            #productDetailModal .product-detail-content {
                width: min(calc(100% - (2 * var(--page-gutter))), 760px);
            }

            #productDetailModal .product-detail-grid {
                grid-template-columns: minmax(0, 1fr);
                gap: var(--space-32);
                padding: var(--space-32);
            }

            #productDetailModal .product-detail-info {
                max-width: none;
            }

            #productDetailModal .product-detail-main-media {
                max-width: 620px;
                margin-inline: auto;
            }

            #productDetailModal .product-gallery-thumbs {
                max-width: 620px;
                margin-inline: auto;
                margin-top: var(--space-12);
            }

            #productDetailModal .recommended-grid {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }
        }

        @media (max-width: 767px) {
            #productDetailModal.product-detail-modal {
                background: var(--color-white);
            }

            #productDetailModal .product-detail-content {
                width: 100%;
                min-height: 100%;
                margin: 0;
            }

            .product-detail-topbar {
                min-height: 64px;
                padding: var(--space-8) var(--space-16);
            }

            #productDetailModal .product-detail-grid {
                gap: var(--space-32);
                padding: var(--space-24) var(--space-16) var(--space-48);
            }

            #productDetailModal .product-detail-image {
                padding: var(--space-16);
            }

            #productDetailModal .product-detail-info h2 {
                font-size: clamp(2.5rem, 14vw, 4rem);
            }

            #productDetailModal .recommended-section {
                padding: var(--space-32) var(--space-16) var(--space-48);
            }

            #productDetailModal .recommended-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: var(--space-24) var(--space-12);
            }
        }

        @media (prefers-reduced-motion: reduce) {
            #productDetailModal .product-detail-back,
            #productDetailModal .product-detail-close,
            #productDetailModal .product-gallery-thumb,
            #productDetailModal .variant-option,
            #productDetailModal .quantity-selector button,
            #productDetailModal .add-to-cart-btn { transition: none !important; }
        }
'''
h = h.replace(style_anchor, style_anchor.replace('\n\n\n    </style>', p24_css + '\n\n    </style>'))

old_detail = '''    <!-- Product Detail Modal -->
    <div class="product-detail-modal" id="productDetailModal" role="dialog" aria-modal="true" aria-labelledby="detailName" aria-hidden="true">
        <div class="product-detail-content">
            <button type="button" class="close-modal" onclick="closeProductDetail()" aria-label="Close product details" style="position: absolute; top: 1rem; right: 1rem; z-index: 1;">×</button>
            
            <div class="product-detail-grid">
                <div>
                    <img id="detailImage" class="product-detail-image" src="" alt="">
                    <div class="product-gallery-thumbs" id="detailGallery"></div>
                </div>
                <div class="product-detail-info">
                    <div class="product-detail-category" id="detailCategory"></div>
                    <h2 id="detailName"></h2>
                    <div class="product-detail-price" id="detailPrice"></div>
                    <div class="product-detail-description" id="detailDescription"></div>
                    <div class="product-detail-stock" id="detailStock"></div>
                    <div class="variant-group" id="detailSizesGroup" style="display:none;"><span class="variant-group-label">Size</span><div class="variant-options" id="detailSizes"></div></div>
                    <div class="variant-group" id="detailColorsGroup" style="display:none;"><span class="variant-group-label">Color</span><div class="variant-options" id="detailColors"></div></div>
                    
                    <div class="quantity-selector">
                        <button onclick="decreaseQuantity()">-</button>
                        <input type="number" id="quantityInput" value="1" min="1" max="99" readonly style="cursor: text !important;">
                        <button onclick="increaseQuantity()">+</button>
                    </div>
                    
                    <button class="add-to-cart-btn" onclick="addToCartFromDetail()" style="cursor: pointer;">Add to Cart</button>
                </div>
            </div>

            <div class="recommended-section">
                <h3>You May Also Like</h3>
                <div class="recommended-grid" id="recommendedGrid">
                    <!-- Recommended products will be rendered here -->
                </div>
            </div>
        </div>
    </div>'''

new_detail = '''    <!-- Product Detail Modal -->
    <div class="product-detail-modal" id="productDetailModal" role="dialog" aria-modal="true" aria-labelledby="detailName" aria-describedby="detailDescription" aria-hidden="true">
        <div class="product-detail-content">
            <div class="product-detail-topbar">
                <button type="button" class="product-detail-back" onclick="closeProductDetail()">Back to browsing</button>
                <button type="button" class="close-modal product-detail-close" onclick="closeProductDetail()" aria-label="Close product details">×</button>
            </div>
            
            <div class="product-detail-grid">
                <section class="product-detail-media-panel" aria-label="Product images">
                    <div class="product-detail-main-media">
                        <img id="detailImage" class="product-detail-image" src="" alt="" decoding="async">
                    </div>
                    <div class="product-gallery-thumbs" id="detailGallery" aria-label="Product image gallery"></div>
                </section>
                <section class="product-detail-info" aria-label="Product information and purchase options">
                    <div class="product-detail-category" id="detailCategory"></div>
                    <h2 id="detailName"></h2>
                    <div class="product-detail-price" id="detailPrice"></div>
                    <div class="product-detail-description" id="detailDescription"></div>
                    <div class="product-detail-stock" id="detailStock" role="status" aria-live="polite"></div>
                    <div class="variant-group" id="detailSizesGroup" style="display:none;" role="group" aria-labelledby="detailSizesLabel"><span class="variant-group-label" id="detailSizesLabel">Size</span><div class="variant-options" id="detailSizes"></div></div>
                    <div class="variant-group" id="detailColorsGroup" style="display:none;" role="group" aria-labelledby="detailColorsLabel"><span class="variant-group-label" id="detailColorsLabel">Color</span><div class="variant-options" id="detailColors"></div></div>
                    
                    <div class="product-detail-quantity">
                        <span class="product-detail-quantity-label" id="detailQuantityLabel">Quantity</span>
                        <div class="quantity-selector" role="group" aria-labelledby="detailQuantityLabel">
                            <button type="button" onclick="decreaseQuantity()" aria-label="Decrease quantity">−</button>
                            <input type="number" id="quantityInput" value="1" min="1" max="99" readonly aria-label="Quantity" inputmode="numeric">
                            <button type="button" onclick="increaseQuantity()" aria-label="Increase quantity">+</button>
                        </div>
                    </div>
                    
                    <button type="button" class="add-to-cart-btn" onclick="addToCartFromDetail()" aria-describedby="detailStock">Add to Cart</button>
                </section>
            </div>

            <section class="recommended-section" aria-labelledby="recommendedTitle">
                <h3 id="recommendedTitle">Related products</h3>
                <div class="recommended-grid" id="recommendedGrid">
                    <!-- Recommended products will be rendered here -->
                </div>
            </section>
        </div>
    </div>'''

assert old_detail in h
h = h.replace(old_detail, new_detail, 1)

old_select = "        function selectProductImage(src, button) { document.getElementById('detailImage').src=src; document.querySelectorAll('.product-gallery-thumb').forEach(el=>el.classList.remove('active')); button?.classList.add('active'); }\n        function selectProductVariant(type,value,button) { currentProductSelection[type]=value; button?.parentElement?.querySelectorAll('.variant-option').forEach(el=>el.classList.remove('selected')); button?.classList.add('selected'); }"
new_select = "        function selectProductImage(src, button) { document.getElementById('detailImage').src=src; document.querySelectorAll('#detailGallery .product-gallery-thumb').forEach(el=>{el.classList.remove('active');el.setAttribute('aria-pressed','false');}); if(button){button.classList.add('active');button.setAttribute('aria-pressed','true');} }\n        function selectProductVariant(type,value,button) { currentProductSelection[type]=value; button?.parentElement?.querySelectorAll('.variant-option').forEach(el=>{el.classList.remove('selected');el.setAttribute('aria-pressed','false');}); if(button){button.classList.add('selected');button.setAttribute('aria-pressed','true');} }"
assert old_select in h
h = h.replace(old_select, new_select, 1)

open_start = h.index('        // Product Detail Modal Functions\n        function openProductDetail(productId, options = {})')
open_end = h.index('\n\n\n        function closeProductDetail', open_start)
old_open = h[open_start:open_end]
new_open = '''        // Product Detail Modal Functions
        function openProductDetail(productId, options = {}) {
            const product=products.find(p=>Number(p.id)===Number(productId)); if(!product)return;
            currentProductDetail=product; currentProductSelection={size:'',color:''}; lastModalFocus=document.activeElement;
            const images=getShopProductImages(product);
            const main=document.getElementById('detailImage'); main.src=images[0]||''; main.alt=product.name||'Product image';
            const gallery=document.getElementById('detailGallery'); gallery.hidden=images.length<=1; gallery.innerHTML=images.length>1?images.map((src,i)=>`<button type="button" class="product-gallery-thumb ${i===0?'active':''}" data-image-index="${i}" aria-label="View image ${i+1} of ${images.length}" aria-pressed="${i===0?'true':'false'}"><img src="${escapeHTML(src)}" alt="" loading="lazy" decoding="async"></button>`).join(''):'';
            gallery.querySelectorAll('button[data-image-index]').forEach(button => button.addEventListener('click', () => selectProductImage(images[Number(button.dataset.imageIndex)], button)));
            document.getElementById('detailCategory').textContent=product.category||''; document.getElementById('detailName').textContent=product.name||'';
            const discount=productDiscounts.find(d=>Number(d.productId)===Number(product.id)&&d.status==='active'); let displayPrice=Number(product.price); if(discount)displayPrice=discount.type==='percentage'?displayPrice-(displayPrice*Number(discount.value)/100):displayPrice-Number(discount.value); displayPrice=Math.max(0,displayPrice);
            const priceEl=document.getElementById('detailPrice'); if(discount){priceEl.innerHTML=`<span class="product-detail-original-price">EGP ${Number(product.price).toFixed(2)}</span><span class="product-detail-sale-price">EGP ${displayPrice.toFixed(2)}</span><span class="product-detail-sale-label">Sale</span>`;}else{priceEl.textContent=`EGP ${Number(product.price).toFixed(2)}`;}
            document.getElementById('detailDescription').textContent=product.description||'';
            const stock=Number(product.stock)||0; const stockEl=document.getElementById('detailStock'); const unavailable=stock<=0||product.status==='Out of Stock'; stockEl.textContent=unavailable?'Out of stock':'In stock'; stockEl.classList.toggle('is-unavailable',unavailable);
            const sizes=Array.isArray(product.sizes)?product.sizes.filter(Boolean):[], colors=Array.isArray(product.colors)?product.colors.filter(Boolean):[];
            const sizesEl=document.getElementById('detailSizes'), colorsEl=document.getElementById('detailColors');
            document.getElementById('detailSizesGroup').style.display=sizes.length?'block':'none'; document.getElementById('detailColorsGroup').style.display=colors.length?'block':'none';
            sizesEl.innerHTML=sizes.map((v,i)=>`<button type="button" class="variant-option" data-variant-index="${i}" aria-pressed="false">${escapeHTML(v)}</button>`).join('');
            colorsEl.innerHTML=colors.map((v,i)=>`<button type="button" class="variant-option" data-variant-index="${i}" aria-pressed="false">${escapeHTML(v)}</button>`).join('');
            sizesEl.querySelectorAll('button[data-variant-index]').forEach(button => button.addEventListener('click', () => selectProductVariant('size', sizes[Number(button.dataset.variantIndex)], button)));
            colorsEl.querySelectorAll('button[data-variant-index]').forEach(button => button.addEventListener('click', () => selectProductVariant('color', colors[Number(button.dataset.variantIndex)], button)));
            const qty=document.getElementById('quantityInput'); qty.value=1; qty.max=Math.max(1,stock||1); loadRecommendedProducts(product.category,product.id);
            const modal=document.getElementById('productDetailModal'); modal.classList.add('active'); modal.setAttribute('aria-hidden','false'); document.body.style.overflow='hidden'; modal.querySelector('.product-detail-close')?.focus();
            updateProductSeo(product);
            if (!options.fromHistory) { const url=new URL(window.location.href); url.searchParams.set('product', product.id); history.pushState({productId: product.id}, '', url); }
        }'''
h = h[:open_start] + new_open + h[open_end:]

recommended_pattern = re.compile(r"        function loadRecommendedProducts\(category, excludeId\) \{.*?\n\n\n        // Close product detail on outside click", re.S)
match = recommended_pattern.search(h)
assert match
new_recommended = '''        function loadRecommendedProducts(category, excludeId) {
            const grid=document.getElementById('recommendedGrid'); const section=grid?.closest('.recommended-section'); if(!grid)return;
            let recommended=products.filter(p=>p.category===category&&Number(p.id)!==Number(excludeId)&&p.status==='Active');
            if(recommended.length<4)recommended=[...recommended,...products.filter(p=>p.category!==category&&Number(p.id)!==Number(excludeId)&&p.status==='Active')];
            recommended=recommended.slice(0,4); if(section)section.hidden=!recommended.length;
            if(!recommended.length){grid.replaceChildren();return;}
            grid.innerHTML=recommended.map(product=>{const id=Number(product.id);const image=getShopProductImages(product)[0]||'';return `<a class="recommended-product" href="?product=${id}" data-recommended-product-id="${id}">${image?`<img src="${escapeHTML(image)}" alt="${escapeHTML(product.name||'KEM product')}" loading="lazy" decoding="async">`:''}<span class="recommended-product-name">${escapeHTML(product.name||'KEM product')}</span><span class="recommended-product-price">EGP ${Number(product.price).toFixed(2)}</span></a>`;}).join('');
            grid.querySelectorAll('a[data-recommended-product-id]').forEach(link=>link.addEventListener('click',event=>{if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;event.preventDefault();openProductDetail(Number(link.dataset.recommendedProductId));}));
        }


        // Close product detail on outside click'''
h = h[:match.start()] + new_recommended + h[match.end():]

for required in [
    'P2.4 — PRODUCT DETAIL',
    'class="product-detail-topbar"',
    'aria-label="Decrease quantity"',
    'aria-pressed="${i===0?',
    "stockEl.textContent=unavailable?'Out of stock':'In stock'",
    'product-detail-sale-label',
    'data-recommended-product-id',
    'function addToCartFromDetail()',
    "'0 products found'",
]:
    assert required in h, required

assert 'Only ${Number(product.stock)} left in stock!' not in h
assert h.count("window.addEventListener('popstate'") == 1
assert h.count("document.addEventListener('keydown', event => {") == 1

path.write_text(h)
print('Applied contained P2.4 product-detail redesign to index.html')
