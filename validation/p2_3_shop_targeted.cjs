const { chromium } = require('playwright');
const { initializeApp, deleteApp } = require('firebase-admin/app');
const { getDatabase } = require('firebase-admin/database');

const BASE = 'http://127.0.0.1:5000';
const widths = [360, 375, 390, 414, 768, 1024, 1440];
const failures = [];
let passes = 0;

function check(ok, label, detail = '') {
  if (ok) {
    passes += 1;
    console.log(`PASS: ${label}${detail ? ` — ${detail}` : ''}`);
  } else {
    failures.push(`${label}${detail ? ` — ${detail}` : ''}`);
    console.error(`FAIL: ${label}${detail ? ` — ${detail}` : ''}`);
  }
}

function inside(rect, width, tolerance = 0.75) {
  return rect && rect.left >= -tolerance && rect.right <= width + tolerance && rect.width >= 0;
}

function durationSeconds(value) {
  const first = String(value || '').split(',')[0].trim();
  if (first.endsWith('ms')) return Number.parseFloat(first) / 1000;
  if (first.endsWith('s')) return Number.parseFloat(first);
  return Number.NaN;
}

(async () => {
  const adminApp = initializeApp({
    projectId: 'demo-kem-validation',
    databaseURL: 'http://127.0.0.1:9000?ns=demo-kem-validation-default-rtdb',
  }, 'p2-3-shop-targeted');
  const adminDb = getDatabase(adminApp);

  await adminDb.ref('products/2').set({
    id: 3,
    name: 'KEM Extremely Long Catalogue Product Name For Narrow Mobile Validation',
    category: 'Tees',
    description: 'Long-name catalogue validation product',
    price: 123456.78,
    stock: 0,
    status: 'Active',
    image: 'logo-240.png',
    images: ['logo-240.png'],
    sizes: ['S'],
    colors: ['Black'],
  });

  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  try {
    for (const width of widths) {
      const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const pageErrors = [];
      const failedLocal = [];
      page.on('pageerror', err => pageErrors.push(String(err)));
      page.on('requestfailed', req => {
        if (req.url().startsWith(BASE)) failedLocal.push(`${req.method()} ${req.url()} ${req.failure()?.errorText || ''}`);
      });

      await page.goto(`${BASE}/#shop`, { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => document.querySelectorAll('#shopProductsGrid .product-card').length === 3, null, { timeout: 20000 });
      await page.waitForTimeout(100);

      const state = await page.evaluate(() => {
        const rect = el => {
          const r = el.getBoundingClientRect();
          return { left:r.left, right:r.right, top:r.top, bottom:r.bottom, width:r.width, height:r.height };
        };
        const shop = document.querySelector('#shop');
        const shell = document.querySelector('.shop-shell');
        const toolbar = document.querySelector('.shop-toolbar');
        const search = document.querySelector('#shopSearch');
        const sort = document.querySelector('#shopSort');
        const grid = document.querySelector('#shopProductsGrid');
        const cards = [...grid.querySelectorAll('.product-card')];
        const cardImages = [...grid.querySelectorAll('.shop-product-image-primary')];
        const filterButtons = [...document.querySelectorAll('#shopFilterButtons .filter-btn')];
        const root = getComputedStyle(document.documentElement);
        const firstImage = grid.querySelector('.shop-product-image');
        const firstCardStyle = getComputedStyle(cards[0]);
        const searchLabel = document.querySelector('label[for="shopSearch"]');
        const sortLabel = document.querySelector('label[for="shopSort"]');
        const template = getComputedStyle(grid).gridTemplateColumns;
        return {
          htmlWidth: document.documentElement.scrollWidth,
          bodyWidth: document.body.scrollWidth,
          bodyOverflowX: getComputedStyle(document.body).overflowX,
          shop: rect(shop), shell: rect(shell), toolbar: rect(toolbar), search: rect(search), sort: rect(sort),
          grid: rect(grid), gridColumns: template.trim().split(/\s+/).filter(Boolean).length,
          cards: cards.map(card => ({ tag:card.tagName, href:card.getAttribute('href'), rect:rect(card) })),
          cardNames: [...grid.querySelectorAll('.shop-product-name')].map(el => el.textContent.trim()),
          cardPrices: [...grid.querySelectorAll('.shop-product-price')].map(el => el.textContent.trim()),
          cardCategories: [...grid.querySelectorAll('.shop-product-category')].map(el => el.textContent.trim()),
          availability: [...grid.querySelectorAll('.shop-product-availability')].map(el => el.textContent.trim()),
          cardText: grid.innerText,
          imageCount: cardImages.length,
          imageLoading: cardImages.map(img => img.getAttribute('loading')),
          imageDecoding: cardImages.map(img => img.getAttribute('decoding')),
          imageAlt: cardImages.map(img => img.getAttribute('alt')),
          objectFit: cardImages.map(img => getComputedStyle(img).objectFit),
          altCount: grid.querySelectorAll('.shop-product-image-alt').length,
          firstImageTransition: firstImage ? getComputedStyle(firstImage).transitionDuration : '',
          filterButtons: filterButtons.map(btn => ({ text:btn.textContent.trim(), pressed:btn.getAttribute('aria-pressed'), rect:rect(btn) })),
          resultText: document.querySelector('#shopResultsStatus')?.textContent.trim(),
          searchLabel: searchLabel?.textContent.trim(), sortLabel: sortLabel?.textContent.trim(),
          cardShadow: firstCardStyle.boxShadow,
          cardTransform: firstCardStyle.transform,
          rootTokens: {
            ink: root.getPropertyValue('--color-ink').trim(),
            pink: root.getPropertyValue('--color-kem-pink').trim(),
            space: root.getPropertyValue('--space-128').trim(),
            motion: root.getPropertyValue('--motion-standard').trim(),
          },
        };
      });

      const expectedColumns = width < 768 ? 2 : width < 1200 ? 3 : 4;
      check(state.htmlWidth <= width && state.bodyWidth <= width, `Shop has no page-level overflow at ${width}px`, `${state.htmlWidth}/${state.bodyWidth}/${width}`);
      check(state.bodyOverflowX !== 'hidden', `Body overflow remains visible at ${width}px`, state.bodyOverflowX);
      check(inside(state.shop, width) && inside(state.shell, width), `Shop and max-width shell stay contained at ${width}px`, JSON.stringify({shop:state.shop,shell:state.shell}));
      check(inside(state.toolbar, width) && inside(state.search, width) && inside(state.sort, width), `Catalogue controls stay contained at ${width}px`, JSON.stringify({toolbar:state.toolbar,search:state.search,sort:state.sort}));
      check(state.search.height >= 44 && state.sort.height >= 44, `Search and sort targets remain usable at ${width}px`, `${state.search.height}/${state.sort.height}`);
      check(state.searchLabel === 'Search products' && state.sortLabel === 'Sort', `Search and sort have accessible visible labels at ${width}px`, `${state.searchLabel}/${state.sortLabel}`);
      check(state.gridColumns === expectedColumns, `Product grid uses intended ${expectedColumns}-column layout at ${width}px`, String(state.gridColumns));
      check(inside(state.grid, width) && state.cards.every(card => inside(card.rect, width) && card.rect.width > 0), `Product grid and cards stay contained at ${width}px`, JSON.stringify(state.cards.map(x => x.rect)));
      check(state.cards.length === 3 && state.cards.every(card => card.tag === 'A' && /^\?product=\d+$/.test(card.href || '')), `Product cards are semantic deep links at ${width}px`, JSON.stringify(state.cards.map(x => ({tag:x.tag,href:x.href}))));
      check(state.cardNames.includes('Validation Alpha Tee') && state.cardNames.includes('Validation Beta Hoodie') && state.cardNames.some(name => name.startsWith('KEM Extremely Long')), `Shop renders authoritative product names at ${width}px`, JSON.stringify(state.cardNames));
      check(state.cardPrices.includes('EGP 500.00') && state.cardPrices.includes('EGP 900.00') && state.cardPrices.includes('EGP 123456.78'), `Shop renders authoritative prices at ${width}px`, JSON.stringify(state.cardPrices));
      check(state.cardCategories.filter(Boolean).every(value => ['Tees','Hoodies'].includes(value)), `Shop metadata comes from real categories at ${width}px`, JSON.stringify(state.cardCategories));
      check(!/\b\d+\s+in stock\b/i.test(state.cardText) && state.availability.length === 1 && state.availability[0] === 'Out of stock', `Availability is restrained to useful unavailable state at ${width}px`, JSON.stringify(state.availability));
      check(state.imageCount === 3 && state.imageLoading.every(v => v === 'lazy') && state.imageDecoding.every(v => v === 'async'), `Catalogue images use efficient lazy async loading at ${width}px`, JSON.stringify({loading:state.imageLoading,decoding:state.imageDecoding}));
      check(state.objectFit.every(v => v === 'contain') && state.imageAlt.includes('Validation Alpha Tee') && state.imageAlt.some(v => v.startsWith('KEM Extremely Long')), `Product imagery preserves aspect and meaningful alt text at ${width}px`, JSON.stringify({fits:state.objectFit,alts:state.imageAlt}));
      check(state.altCount === 1, `Alternate image is only rendered for a product with genuine second image at ${width}px`, String(state.altCount));
      check(state.filterButtons.length >= 3 && state.filterButtons.every(btn => btn.rect.height >= 44), `Category controls are at least 44px at ${width}px`, JSON.stringify(state.filterButtons));
      check(state.filterButtons.filter(btn => btn.pressed === 'true').length === 1 && state.filterButtons.find(btn => btn.pressed === 'true')?.text === 'All Products', `Category selected state is explicit at ${width}px`, JSON.stringify(state.filterButtons.map(x => ({text:x.text,pressed:x.pressed}))));
      check(state.resultText === '3 products', `Result count is clear at ${width}px`, state.resultText);
      check(state.cardShadow === 'none' && state.cardTransform === 'none', `Product cards remain restrained without lift or shadow at ${width}px`, `${state.cardShadow}/${state.cardTransform}`);
      check(state.rootTokens.ink === '#0A0A0A' && state.rootTokens.pink === '#FF3366' && state.rootTokens.space === '128px' && state.rootTokens.motion === '200ms', `P2.0 tokens remain intact at ${width}px`, JSON.stringify(state.rootTokens));
      const transition = durationSeconds(state.firstImageTransition);
      check(Number.isFinite(transition) && transition <= 0.001, `Reduced motion suppresses catalogue image transitions at ${width}px`, state.firstImageTransition);

      await page.locator('#shopProductsGrid .product-card').first().focus();
      const focus = await page.locator('#shopProductsGrid .product-card').first().evaluate(el => {
        const s = getComputedStyle(el); return { width:s.outlineWidth, style:s.outlineStyle, color:s.outlineColor };
      });
      check(focus.width === '3px' && focus.style === 'solid', `P2.1 strong visible focus remains intact at ${width}px`, JSON.stringify(focus));
      check(pageErrors.length === 0, `No uncaught browser errors at ${width}px`, JSON.stringify(pageErrors));
      check(failedLocal.length === 0, `No failed local application requests at ${width}px`, JSON.stringify(failedLocal));

      if (width === 390) {
        await page.fill('#shopSearch', 'Beta');
        await page.waitForTimeout(40);
        check((await page.locator('#shopProductsGrid .product-card').count()) === 1 && (await page.locator('.shop-product-name').first().textContent()).trim() === 'Validation Beta Hoodie', 'Existing product-name search remains correct');
        check(await page.inputValue('#headerSearch') === 'Beta' && await page.inputValue('#mobileHeaderSearch') === 'Beta', 'P2.1 header searches remain synchronized with Shop search');

        await page.fill('#shopSearch', 'Long-name catalogue');
        await page.waitForTimeout(40);
        check((await page.locator('#shopProductsGrid .product-card').count()) === 1, 'Existing description search field remains supported');

        await page.fill('#shopSearch', '');
        await page.getByRole('button', { name: 'Tees', exact: true }).click();
        check((await page.locator('#shopProductsGrid .product-card').count()) === 2, 'Existing category filtering remains correct');
        check((await page.getByRole('button', { name: 'Tees', exact: true }).getAttribute('aria-pressed')) === 'true', 'Category active state follows existing filter state');
        await page.getByRole('button', { name: 'All Products', exact: true }).click();

        await page.selectOption('#shopSort', 'price-desc');
        let names = await page.locator('#shopProductsGrid .shop-product-name').allTextContents();
        check(names[0].startsWith('KEM Extremely Long') && names[1] === 'Validation Beta Hoodie' && names[2] === 'Validation Alpha Tee', 'Price high-to-low sort is correct');
        await page.selectOption('#shopSort', 'price-asc');
        names = await page.locator('#shopProductsGrid .shop-product-name').allTextContents();
        check(JSON.stringify(names) === JSON.stringify(['Validation Alpha Tee','Validation Beta Hoodie','KEM Extremely Long Catalogue Product Name For Narrow Mobile Validation']), 'Price low-to-high sort is correct');
        await page.selectOption('#shopSort', 'name-asc');
        names = await page.locator('#shopProductsGrid .shop-product-name').allTextContents();
        check(names[0].startsWith('KEM Extremely Long') && names[1] === 'Validation Alpha Tee' && names[2] === 'Validation Beta Hoodie', 'Name A-to-Z sort is correct');
        await page.selectOption('#shopSort', 'default');

        await page.fill('#shopSearch', 'no-such-kem-product');
        await page.waitForSelector('#clearShopFilters');
        const empty = await page.locator('.shop-empty-state').innerText();
        const clearSize = await page.locator('#clearShopFilters').evaluate(el => { const r=el.getBoundingClientRect(); return {w:r.width,h:r.height}; });
        check(/No products found/.test(empty) && clearSize.h >= 44, 'No-results state is semantic and actionable', `${empty} / ${JSON.stringify(clearSize)}`);
        await page.click('#clearShopFilters');
        check((await page.locator('#shopProductsGrid .product-card').count()) === 3 && await page.inputValue('#shopSearch') === '', 'Clear search and filters restores catalogue');

        await page.locator('#shopProductsGrid .product-card').first().click();
        await page.waitForSelector('#productDetailModal.active');
        check(new URL(page.url()).searchParams.get('product') === '1', 'Shop card opens existing ?product=<id> detail URL');
        check((await page.locator('#detailGallery .product-gallery-thumb').count()) === 2, 'Existing product gallery remains functional from Shop');
        await page.goBack();
        await page.waitForFunction(() => !document.querySelector('#productDetailModal').classList.contains('active'));
        check(!(await page.locator('#productDetailModal').evaluate(el => el.classList.contains('active'))), 'Browser Back closes Shop product detail');
        await page.goForward();
        await page.waitForSelector('#productDetailModal.active');
        check(new URL(page.url()).searchParams.get('product') === '1', 'Browser Forward restores Shop product detail');
        const size = page.locator('#detailSizes .variant-option').first();
        const color = page.locator('#detailColors .variant-option').first();
        await size.focus(); await page.keyboard.press('Space');
        await color.focus(); await page.keyboard.press('Enter');
        check(await size.evaluate(el => el.classList.contains('selected')) && await color.evaluate(el => el.classList.contains('selected')), 'Existing variant keyboard behavior remains functional');
        let addDialog = '';
        page.once('dialog', async dialog => { addDialog = dialog.message(); await dialog.dismiss(); });
        await page.locator('#productDetailModal .add-to-cart-btn').click();
        await page.waitForTimeout(60);
        check(/added to cart/i.test(addDialog) && Number(await page.locator('#cartCount').textContent()) >= 1, 'Existing Add to Cart remains functional from Shop flow', `${addDialog} / ${await page.locator('#cartCount').textContent()}`);
        if (await page.locator('#productDetailModal.active').count()) await page.keyboard.press('Escape');

        await page.evaluate(() => {
          if (document.querySelector('#productDetailModal').classList.contains('active')) closeProductDetail();
          showCategoryPage(1);
        });
        await page.waitForFunction(() => getComputedStyle(document.querySelector('#categoryPage')).display !== 'none');
        const categoryState = await page.evaluate(() => {
          const grid=document.querySelector('#categoryProductsGrid');
          const links=[...grid.querySelectorAll('.product-card')];
          const buttons=[...grid.querySelectorAll('button[data-category-add-id]')];
          return {
            title:document.querySelector('#categoryPageTitle').textContent.trim(),
            description:document.querySelector('#categoryPageDescription').textContent.trim(),
            columns:getComputedStyle(grid).gridTemplateColumns.trim().split(/\s+/).filter(Boolean).length,
            links:links.map(el=>({tag:el.tagName,href:el.getAttribute('href')})),
            buttonHeights:buttons.map(el=>el.getBoundingClientRect().height),
            text:grid.innerText,
            sw:document.documentElement.scrollWidth,
            iw:innerWidth,
          };
        });
        check(categoryState.title === 'Tees' && categoryState.links.length === 2, 'Existing category destination renders the real collection products', JSON.stringify(categoryState));
        check(categoryState.columns === 2 && categoryState.sw <= categoryState.iw, 'Collection page keeps the intentional 2-column mobile catalogue without overflow', `${categoryState.columns}/${categoryState.sw}/${categoryState.iw}`);
        check(categoryState.links.every(link => link.tag === 'A' && /^\?product=\d+$/.test(link.href || '')), 'Collection product cards use semantic deep links');
        check(categoryState.buttonHeights.every(h => h >= 44), 'Existing collection Add to Cart controls remain usable', JSON.stringify(categoryState.buttonHeights));
        check(!/🔥|ON SALE/i.test(categoryState.text), 'Collection catalogue removes emoji/demo sale treatment');
        await page.evaluate(() => closeCategoryPage());
      }

      await context.close();
    }
  } finally {
    await browser.close();
    adminDb.goOffline();
    await deleteApp(adminApp);
  }

  console.log(`P2_3_SHOP_RESULT ${passes} passed, ${failures.length} failed`);
  if (failures.length) {
    console.error(failures.join('\n'));
    process.exit(1);
  }
  console.log('P2_3_SHOP_COMPLETE');
})();
