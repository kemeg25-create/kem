from pathlib import Path

START_SHA = '4d5b4fcc188577551feec0d61d4d11e185906c72'
path = Path('index.html')
h = path.read_text()

if 'P2.2 — HOMEPAGE' in h:
    raise SystemExit('P2.2 marker already present; refusing to reapply')

for anchor in [
    'P2.1 — HEADER / NAVIGATION',
    'class="nav-shell"',
    'id="headerSearch"',
    'id="mobileHeaderSearch"',
    'id="authButton"',
    'id="cartBadge"',
    '<!-- Hero Section -->',
    '<!-- Shop Section -->',
    '<!-- About -->',
    '<!-- Footer -->',
    'function renderShopProducts()',
    'function goToShop(category)',
    'function applyAboutSectionData(data)',
    'function renderAboutStats()',
]:
    if anchor not in h:
        raise SystemExit(f'Missing required anchor: {anchor}')

css = r'''
        /* P2.2 — HOMEPAGE */
        #home.home-hero {
            min-height: 0;
            display: block;
            overflow: visible;
            padding: calc(72px + var(--space-48)) var(--page-gutter) var(--space-64);
            background: var(--color-off-white);
        }

        .home-hero-shell,
        .home-section-shell {
            width: 100%;
            max-width: var(--container-customer);
            margin-inline: auto;
        }

        .home-hero-shell {
            display: grid;
            grid-template-columns: minmax(0, 0.88fr) minmax(360px, 1.12fr);
            gap: var(--space-64);
            align-items: center;
        }

        .home-hero-shell.hero-without-image {
            grid-template-columns: minmax(0, 760px);
            min-height: 520px;
            align-content: center;
        }

        .home-hero-copy { min-width: 0; max-width: 680px; }

        .home-eyebrow,
        .home-section-kicker {
            margin: 0 0 var(--space-12);
            font-family: var(--font-ui);
            font-size: var(--type-metadata);
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--color-neutral-600);
        }

        #home .hero-title {
            margin: 0 0 var(--space-24);
            font-family: var(--font-display);
            font-size: var(--type-display);
            font-weight: 400;
            line-height: 0.86;
            letter-spacing: 0.01em;
            color: var(--color-ink);
        }

        #home .hero-title span { display: block; }

        #home .hero-subtitle {
            max-width: 36rem;
            margin: 0 0 var(--space-32);
            font-family: var(--font-ui);
            font-size: var(--type-body);
            font-weight: 400;
            line-height: 1.65;
            letter-spacing: 0;
            text-transform: none;
            color: var(--color-neutral-600);
            animation: none;
        }

        #home .cta-button {
            min-height: 48px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: var(--space-12) var(--space-24);
            border: 1px solid var(--color-kem-pink);
            border-radius: var(--radius-xs);
            background: var(--color-kem-pink);
            color: var(--color-ink);
            font-family: var(--font-ui);
            font-size: var(--type-ui);
            font-weight: 600;
            letter-spacing: 0;
            text-transform: none;
            text-decoration: none;
            box-shadow: none;
            animation: none;
            transition: background-color var(--motion-fast) var(--ease-standard), color var(--motion-fast) var(--ease-standard), border-color var(--motion-fast) var(--ease-standard);
        }

        #home .cta-button:hover {
            background: var(--color-ink);
            border-color: var(--color-ink);
            color: var(--color-white);
            transform: none;
            box-shadow: none;
        }

        #home .floating-shapes { display: none; }

        .home-hero-product { min-width: 0; }
        .home-hero-product[hidden] { display: none; }

        .home-hero-media,
        .home-product-media,
        .home-category-media {
            border: 1px solid var(--color-neutral-200);
            background: var(--color-white);
            overflow: hidden;
        }

        .home-hero-media {
            aspect-ratio: 4 / 5;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .home-hero-media img,
        .home-product-media img,
        .home-category-media img {
            width: 100%;
            height: 100%;
            display: block;
            object-fit: contain;
        }

        .home-hero-media img { padding: var(--space-24); }

        .home-hero-meta {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: var(--space-16);
            margin-top: var(--space-12);
            font-family: var(--font-ui);
        }

        .home-hero-name {
            min-width: 0;
            font-size: var(--type-ui);
            font-weight: 600;
            line-height: 1.35;
        }

        .home-hero-price {
            flex: 0 0 auto;
            font-size: var(--type-metadata);
            color: var(--color-neutral-600);
        }

        .home-featured,
        #collections.home-categories,
        .about.home-about {
            padding: var(--space-96) var(--page-gutter);
        }

        .home-featured { background: var(--color-white); }
        #collections.home-categories { background: var(--color-off-white); }

        .home-section-header {
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: var(--space-24);
            margin-bottom: var(--space-32);
        }

        .home-section-title {
            margin: 0;
            font-family: var(--font-display);
            font-size: var(--type-section-title);
            font-weight: 400;
            line-height: 0.95;
            letter-spacing: 0.01em;
            color: var(--color-ink);
        }

        .home-text-link {
            min-height: 44px;
            display: inline-flex;
            align-items: center;
            flex: 0 0 auto;
            color: var(--color-ink);
            font-family: var(--font-ui);
            font-size: var(--type-ui);
            font-weight: 600;
            text-decoration: none;
            border-bottom: 1px solid var(--color-ink);
        }

        .home-text-link:hover { color: var(--color-kem-pink); border-color: var(--color-kem-pink); }

        .home-featured-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: var(--space-24);
        }

        .home-product-card { min-width: 0; }

        .home-product-link {
            display: block;
            color: var(--color-ink);
            text-decoration: none;
        }

        .home-product-media {
            aspect-ratio: 4 / 5;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .home-product-media img {
            padding: var(--space-12);
            transition: opacity var(--motion-fast) var(--ease-standard);
        }

        .home-product-link:hover .home-product-media img { opacity: 0.88; }

        .home-product-image-fallback,
        .home-category-image-fallback {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--color-neutral-100);
            color: var(--color-neutral-600);
            font-family: var(--font-display);
            font-size: clamp(2rem, 5vw, 4rem);
            letter-spacing: 0.04em;
        }

        .home-product-info {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: var(--space-8) var(--space-12);
            align-items: start;
            padding-top: var(--space-12);
        }

        .home-product-name {
            min-width: 0;
            margin: 0;
            font-family: var(--font-ui);
            font-size: var(--type-ui);
            font-weight: 600;
            line-height: 1.4;
            overflow-wrap: anywhere;
        }

        .home-product-price {
            font-family: var(--font-ui);
            font-size: var(--type-ui);
            font-weight: 400;
            white-space: nowrap;
        }

        .home-product-meta {
            grid-column: 1 / -1;
            margin: 0;
            font-family: var(--font-ui);
            font-size: var(--type-metadata);
            line-height: 1.4;
            color: var(--color-neutral-600);
        }

        .home-empty-state {
            grid-column: 1 / -1;
            padding: var(--space-48) 0;
            border-top: 1px solid var(--color-neutral-200);
            border-bottom: 1px solid var(--color-neutral-200);
            color: var(--color-neutral-600);
            font-family: var(--font-ui);
            font-size: var(--type-body);
        }

        .home-category-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: var(--space-24);
        }

        .home-category-card {
            width: 100%;
            min-width: 0;
            min-height: 44px;
            padding: 0;
            border: 0;
            border-radius: 0;
            background: transparent;
            color: var(--color-ink);
            text-align: left;
            font: inherit;
        }

        .home-category-media {
            aspect-ratio: 4 / 3;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .home-category-media img { padding: var(--space-16); }

        .home-category-copy { padding-top: var(--space-12); }

        .home-category-name {
            margin: 0;
            font-family: var(--font-ui);
            font-size: var(--type-product-title);
            font-weight: 600;
            line-height: 1.2;
        }

        .home-category-desc {
            margin: var(--space-8) 0 0;
            max-width: 34rem;
            font-family: var(--font-ui);
            font-size: var(--type-metadata);
            line-height: 1.5;
            color: var(--color-neutral-600);
        }

        .home-category-card:hover .home-category-name { color: var(--color-kem-pink); }

        .about.home-about {
            background: var(--color-ink);
            color: var(--color-white);
        }

        .home-about .about-content {
            display: block;
            max-width: var(--container-editorial);
            margin-inline: auto;
        }

        .home-about .about-text { max-width: 760px; }

        .home-about .about-text h2 {
            margin: 0 0 var(--space-24);
            font-family: var(--font-display);
            font-size: var(--type-section-title);
            font-weight: 400;
            line-height: 0.95;
            letter-spacing: 0.01em;
            color: var(--color-white);
            background: none;
            -webkit-background-clip: border-box;
            -webkit-text-fill-color: currentColor;
            background-clip: border-box;
        }

        .home-about .about-text p {
            margin: 0;
            font-family: var(--font-ui);
            font-size: clamp(1rem, 1.5vw, 1.2rem);
            line-height: 1.7;
            color: var(--color-neutral-200);
            opacity: 1;
        }

        .home-about .stats { display: none !important; }

        @media (max-width: 1023px) {
            #home.home-hero { padding-top: calc(64px + var(--space-48)); }
            .home-hero-shell { grid-template-columns: minmax(0, 1fr); gap: var(--space-32); }
            .home-hero-shell.hero-without-image { min-height: 460px; }
            .home-hero-product { width: min(100%, 560px); }
            .home-featured-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .home-category-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }

        @media (max-width: 767px) {
            #home.home-hero {
                padding-top: calc(64px + var(--space-32));
                padding-bottom: var(--space-48);
            }

            .home-hero-shell.hero-without-image { min-height: 380px; }
            #home .hero-title { font-size: clamp(4rem, 22vw, 6rem); }
            .home-hero-media img { padding: var(--space-16); }
            .home-featured,
            #collections.home-categories,
            .about.home-about { padding-block: var(--space-64); }
            .home-section-header { align-items: flex-start; flex-direction: column; gap: var(--space-16); }
            .home-featured-grid { gap: var(--space-24) var(--space-12); }
            .home-product-info { grid-template-columns: minmax(0, 1fr); gap: var(--space-4); }
            .home-product-price { white-space: normal; }
            .home-product-meta { grid-column: 1; }
            .home-category-grid { grid-template-columns: minmax(0, 1fr); gap: var(--space-32); }
        }

        @media (prefers-reduced-motion: reduce) {
            #home .cta-button,
            .home-product-media img { transition: none !important; }
        }
'''

style_close = '\n    </style>'
if h.count(style_close) != 1:
    raise SystemExit('Expected exactly one style closing tag anchor')
h = h.replace(style_close, css + style_close, 1)

home_start = h.index('        <!-- Hero Section -->')
shop_start = h.index('        <!-- Shop Section -->', home_start)
h = h[:home_start] + r'''        <!-- Hero Section -->
        <section class="hero home-hero" id="home">
            <div class="home-hero-shell hero-without-image" id="homeHeroShell">
                <div class="home-hero-copy">
                    <p class="home-eyebrow">KEM / Clothing</p>
                    <h1 class="hero-title"><span>KEM</span><span>CLOTHING</span></h1>
                    <p class="hero-subtitle">Streetwear from KEM. Shop the current collection.</p>
                    <a href="#shop" class="cta-button">Shop KEM</a>
                </div>
                <div class="home-hero-product" id="homeHeroProduct" aria-live="polite" hidden></div>
            </div>
        </section>

        <!-- Featured Products -->
        <section class="home-featured" id="featuredProducts" aria-labelledby="featuredProductsTitle">
            <div class="home-section-shell">
                <div class="home-section-header">
                    <div>
                        <p class="home-section-kicker">KEM / Shop</p>
                        <h2 class="home-section-title" id="featuredProductsTitle">Featured Products</h2>
                    </div>
                    <a class="home-text-link" href="#shop">Shop all products</a>
                </div>
                <div class="home-featured-grid" id="homeFeaturedProducts" aria-live="polite"></div>
            </div>
        </section>

        <!-- Real Categories -->
        <section class="collections home-categories" id="collections" aria-labelledby="homeCategoriesTitle" hidden>
            <div class="home-section-shell">
                <div class="home-section-header">
                    <div>
                        <p class="home-section-kicker">KEM / Categories</p>
                        <h2 class="home-section-title" id="homeCategoriesTitle">Shop by Category</h2>
                    </div>
                </div>
                <div class="home-category-grid" id="homeCategoryGrid"></div>
            </div>
        </section>

''' + h[shop_start:]

about_start = h.index('        <!-- About -->')
footer_start = h.index('        <!-- Footer -->', about_start)
h = h[:about_start] + r'''        <!-- About -->
        <section class="about home-about" id="about">
            <div class="about-content">
                <div class="about-text">
                    <p class="home-section-kicker">About KEM</p>
                    <h2 id="aboutSectionTitle">KEM</h2>
                    <p id="aboutSectionContent">KEM is an Egyptian streetwear brand. Explore the current clothing collection.</p>
                </div>
                <div class="stats" id="aboutStatsContainer" hidden></div>
            </div>
        </section>

''' + h[footer_start:]

homepage_js = r'''
        function getHomepageProductImage(product) {
            return String(product?.images?.[0] || product?.image || '').trim();
        }

        function getHomepageActiveProducts() {
            return products.filter(product => product && product.status === 'Active');
        }

        function formatHomepagePrice(value) {
            const amount = Number(value);
            return Number.isFinite(amount) ? `EGP ${amount.toFixed(2)}` : '';
        }

        function renderHomeHeroProduct() {
            const shell = document.getElementById('homeHeroShell');
            const container = document.getElementById('homeHeroProduct');
            if (!shell || !container) return;

            const active = getHomepageActiveProducts();
            const heroProduct = active.find(product => Number(product.stock) > 0 && getHomepageProductImage(product)) || active.find(product => getHomepageProductImage(product));
            if (!heroProduct) {
                container.hidden = true;
                container.replaceChildren();
                shell.classList.add('hero-without-image');
                return;
            }

            const image = getHomepageProductImage(heroProduct);
            container.innerHTML = `
                <div class="home-hero-media">
                    <img src="${escapeHTML(image)}" alt="${escapeHTML(heroProduct.name || 'KEM product')}" decoding="async" fetchpriority="high">
                </div>
                <div class="home-hero-meta">
                    <span class="home-hero-name">${escapeHTML(heroProduct.name || 'KEM')}</span>
                    <span class="home-hero-price">${escapeHTML(formatHomepagePrice(heroProduct.price))}</span>
                </div>`;
            container.hidden = false;
            shell.classList.remove('hero-without-image');
        }

        function renderHomepageFeaturedProducts() {
            const grid = document.getElementById('homeFeaturedProducts');
            if (!grid) return;
            const featured = getHomepageActiveProducts().slice(0, 4);
            if (!featured.length) {
                grid.innerHTML = '<div class="home-empty-state">No products are available right now.</div>';
                return;
            }

            grid.innerHTML = featured.map(product => {
                const id = Number(product.id);
                const image = getHomepageProductImage(product);
                const media = image
                    ? `<img src="${escapeHTML(image)}" alt="${escapeHTML(product.name || 'KEM product')}" loading="lazy" decoding="async">`
                    : '<div class="home-product-image-fallback" aria-hidden="true">KEM</div>';
                const category = String(product.category || '').trim();
                return `<article class="home-product-card">
                    <a class="home-product-link" href="?product=${id}" data-home-product-id="${id}">
                        <div class="home-product-media">${media}</div>
                        <div class="home-product-info">
                            <h3 class="home-product-name">${escapeHTML(product.name || 'KEM product')}</h3>
                            <span class="home-product-price">${escapeHTML(formatHomepagePrice(product.price))}</span>
                            ${category ? `<p class="home-product-meta">${escapeHTML(category)}</p>` : ''}
                        </div>
                    </a>
                </article>`;
            }).join('');

            grid.querySelectorAll('a[data-home-product-id]').forEach(link => {
                link.addEventListener('click', event => {
                    event.preventDefault();
                    openProductDetail(Number(link.dataset.homeProductId));
                });
            });
        }

        function getHomepageCategoryProducts(category) {
            const active = getHomepageActiveProducts();
            if (category?.displayType === 'products') {
                const selected = new Set((category.selectedItems || []).map(String));
                return active.filter(product => selected.has(String(product.id)));
            }
            if (category?.displayType === 'collections') {
                const selected = new Set((category.selectedItems || []).map(String));
                return active.filter(product => selected.has(String(product.category || '')));
            }
            return active.filter(product => String(product.category || '') === String(category?.name || ''));
        }

        function renderHomepageCategories() {
            const section = document.getElementById('collections');
            const grid = document.getElementById('homeCategoryGrid');
            if (!section || !grid) return;

            const realCategories = categories
                .filter(category => category && String(category.name || '').trim() && category.visible !== false)
                .map(category => ({ category, matchingProducts: getHomepageCategoryProducts(category) }))
                .filter(entry => entry.matchingProducts.length > 0)
                .slice(0, 3);

            if (!realCategories.length) {
                grid.replaceChildren();
                section.hidden = true;
                return;
            }

            grid.innerHTML = realCategories.map(({ category, matchingProducts }) => {
                const imageProduct = matchingProducts.find(product => getHomepageProductImage(product));
                const image = imageProduct ? getHomepageProductImage(imageProduct) : '';
                const media = image
                    ? `<img src="${escapeHTML(image)}" alt="" loading="lazy" decoding="async">`
                    : '<div class="home-category-image-fallback" aria-hidden="true">KEM</div>';
                const description = String(category.description || '').trim();
                return `<button type="button" class="home-category-card" data-home-category-id="${Number(category.id)}">
                    <span class="home-category-media">${media}</span>
                    <span class="home-category-copy">
                        <span class="home-category-name">${escapeHTML(category.name)}</span>
                        ${description ? `<span class="home-category-desc">${escapeHTML(description)}</span>` : ''}
                    </span>
                </button>`;
            }).join('');

            grid.querySelectorAll('button[data-home-category-id]').forEach(button => {
                button.addEventListener('click', () => showCategoryPage(Number(button.dataset.homeCategoryId)));
            });
            section.hidden = false;
        }

        function renderHomepage() {
            renderHomeHeroProduct();
            renderHomepageFeaturedProducts();
            renderHomepageCategories();
        }

'''
js_anchor = '        function goToShop(category) {'
if h.count(js_anchor) != 1:
    raise SystemExit('Expected one goToShop anchor')
h = h.replace(js_anchor, homepage_js + js_anchor, 1)

old_init = '''            renderShopProducts();\n            renderCategoriesDropdown();\n            renderShopFilters();'''
new_init = '''            renderHomepage();\n            renderShopProducts();\n            renderCategoriesDropdown();\n            renderShopFilters();'''
if h.count(old_init) != 1:
    raise SystemExit('Expected one initial storefront render block')
h = h.replace(old_init, new_init, 1)

old_products_binding = "['products', data => { products = firebaseList(data); renderShopProducts(); }],"
new_products_binding = "['products', data => { products = firebaseList(data); renderHomepage(); renderShopProducts(); }],"
if h.count(old_products_binding) != 1:
    raise SystemExit('Expected one products listener binding')
h = h.replace(old_products_binding, new_products_binding, 1)

old_categories_binding = "['categories', data => { categories = firebaseList(data); renderCategoriesDropdown(); renderShopFilters(); renderShopProducts(); }],"
new_categories_binding = "['categories', data => { categories = firebaseList(data); renderHomepageCategories(); renderCategoriesDropdown(); renderShopFilters(); renderShopProducts(); }],"
if h.count(old_categories_binding) != 1:
    raise SystemExit('Expected one categories listener binding')
h = h.replace(old_categories_binding, new_categories_binding, 1)

about_fn_start = h.index('        function applyAboutSectionData(data) {')
about_fn_end = h.index('\n\n        // Color Theme Functions', about_fn_start)
about_fn = r'''        function getHomepageAboutPresentation(titleValue, contentValue) {
            const rawContent = String(contentValue || '').trim();
            const normalized = rawContent.toLowerCase().replaceAll('’', "'");
            const legacyPlaceholder = normalized.includes("isn't just a clothing brand") && normalized.includes('movement') && normalized.includes('sustainable practices');
            if (!rawContent || legacyPlaceholder) {
                return {
                    title: 'KEM',
                    content: 'KEM is an Egyptian streetwear brand. Explore the current clothing collection.'
                };
            }
            return { title: String(titleValue || 'KEM'), content: rawContent };
        }

        function applyAboutSectionData(data) {
            if (!data || typeof data !== 'object') return;
            aboutSectionData = {
                title: String(data.title || aboutSectionData.title),
                content: String(data.content || aboutSectionData.content),
                stats: Array.isArray(data.stats) ? data.stats.slice(0, 8) : aboutSectionData.stats
            };
            const presentation = getHomepageAboutPresentation(aboutSectionData.title, aboutSectionData.content);
            const title = document.getElementById('aboutSectionTitle');
            const content = document.getElementById('aboutSectionContent');
            if (title) title.textContent = presentation.title;
            if (content) content.textContent = presentation.content;
            renderAboutStats();
        }'''
h = h[:about_fn_start] + about_fn + h[about_fn_end:]

stats_start = h.index('        function renderAboutStats() {')
stats_end = h.index('\n\n        async function updateAboutSection()', stats_start)
stats_fn = r'''        function renderAboutStats() {
            const container = document.getElementById('aboutStatsContainer');
            if (container) container.replaceChildren();
        }'''
h = h[:stats_start] + stats_fn + h[stats_end:]

home_markup = h[h.index('<div id="mainSite">'):h.index('<!-- Category Page -->')]
for forbidden in [
    '<div class="floating-shapes">',
    'URBAN CORE',
    'NEON NIGHTS',
    'MINIMAL EDGE',
    '10K+',
    '500+',
    '100% Sustainable',
    "isn't just a clothing brand—it’s a movement",
    "isn't just a clothing brand—it's a movement",
]:
    if forbidden in home_markup:
        raise SystemExit(f'Homepage still contains forbidden placeholder content: {forbidden}')

required = [
    'P2.2 — HOMEPAGE',
    'id="homeHeroProduct"',
    'id="homeFeaturedProducts"',
    'id="homeCategoryGrid"',
    'Streetwear from KEM. Shop the current collection.',
    'KEM is an Egyptian streetwear brand. Explore the current clothing collection.',
    'renderHomepage();',
    'renderHomepageCategories();',
    'loading="lazy" decoding="async"',
    'fetchpriority="high"',
    'category.visible !== false',
    'container.replaceChildren();',
    'P2.1 — HEADER / NAVIGATION',
    'class="nav-shell"',
    'id="headerSearch"',
    'id="mobileHeaderSearch"',
    'id="authButton"',
    'id="cartBadge"',
]
for item in required:
    if item not in h:
        raise SystemExit(f'Missing post-patch requirement: {item}')

if h.count("window.addEventListener('popstate'") != 1:
    raise SystemExit('History handler count changed')
if h.count("document.addEventListener('keydown', event => {") != 1:
    raise SystemExit('Global keydown handler count changed')

path.write_text(h)
print('Applied P2.2 homepage-only production patch')
