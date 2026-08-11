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

async function openProduct(page, id) {
  await page.goto(`${BASE}/?product=${id}`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#productDetailModal.active', { timeout: 20000 });
  await page.waitForFunction(() => document.querySelector('#detailName')?.textContent.trim().length > 0, null, { timeout: 20000 });
}

(async () => {
  const adminApp = initializeApp({
    projectId: 'demo-kem-validation',
    databaseURL: 'http://127.0.0.1:9000?ns=demo-kem-validation-default-rtdb',
  }, 'p2-4-product-detail-targeted');
  const adminDb = getDatabase(adminApp);

  await adminDb.ref('products/2').set({
    id: 3,
    name: 'KEM Extremely Long Product Detail Name For Narrow Mobile Layout Validation Without Horizontal Overflow',
    category: 'Tees',
    description: 'Long-name product detail validation fixture.',
    price: 123456.78,
    stock: 0,
    status: 'Active',
    image: 'logo-240.png',
    images: ['logo-240.png'],
    sizes: [],
    colors: [],
  });
  await adminDb.ref('products/3').set({
    id: 4,
    name: 'Validation Variantless Tee',
    category: 'Tees',
    description: 'Variantless product detail validation fixture.',
    price: 650,
    stock: 4,
    status: 'Active',
    image: 'logo-240.png',
    images: ['logo-240.png'],
    sizes: [],
    colors: [],
  });
  await adminDb.ref('productDiscounts/0').set({ id: 1, productId: 1, type: 'percentage', value: 10, status: 'active' });

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
      await page.waitForFunction(() => document.querySelectorAll('#shopProductsGrid .product-card').length === 4, null, { timeout: 20000 });
      const preOpen = await page.evaluate(() => ({
        htmlWidth: document.documentElement.scrollWidth,
        bodyWidth: document.body.scrollWidth,
        bodyOverflowX: getComputedStyle(document.body).overflowX,
      }));
      check(preOpen.htmlWidth <= width && preOpen.bodyWidth <= width, `P2.4 pre-open storefront has no page-level overflow at ${width}px`, `${preOpen.htmlWidth}/${preOpen.bodyWidth}/${width}`);
      check(preOpen.bodyOverflowX !== 'hidden', `Body overflow remains visible before detail opens at ${width}px`, preOpen.bodyOverflowX);

      await page.locator('#shopProductsGrid a[data-shop-product-id="1"]').click();
      await page.waitForSelector('#productDetailModal.active');
      await page.waitForTimeout(50);

      const state = await page.evaluate(() => {
        const rect = el => { const r = el.getBoundingClientRect(); return { left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height }; };
        const modal = document.querySelector('#productDetailModal');
        const content = document.querySelector('#productDetailModal .product-detail-content');
        const grid = document.querySelector('#productDetailModal .product-detail-grid');
        const media = document.querySelector('.product-detail-main-media');
        const image = document.querySelector('#detailImage');
        const info = document.querySelector('#productDetailModal .product-detail-info');
        const name = document.querySelector('#detailName');
        const price = document.querySelector('#detailPrice');
        const desc = document.querySelector('#detailDescription');
        const stock = document.querySelector('#detailStock');
        const add = document.querySelector('#productDetailModal .add-to-cart-btn');
        const qtyInput = document.querySelector('#quantityInput');
        const qtyButtons = [...document.querySelectorAll('#productDetailModal .quantity-selector button')];
        const variants = [...document.querySelectorAll('#productDetailModal .variant-option')];
        const thumbs = [...document.querySelectorAll('#detailGallery .product-gallery-thumb')];
        const back = document.querySelector('.product-detail-back');
        const close = document.querySelector('.product-detail-close');
        const recs = [...document.querySelectorAll('#recommendedGrid .recommended-product')];
        const root = getComputedStyle(document.documentElement);
        return {
          htmlWidth: document.documentElement.scrollWidth,
          bodyWidth: document.body.scrollWidth,
          modal: rect(modal), content: rect(content), grid: rect(grid), media: rect(media), image: rect(image), info: rect(info), name: rect(name), price: rect(price), desc: rect(desc), stock: rect(stock), add: rect(add), qtyInput: rect(qtyInput),
          gridColumns: getComputedStyle(grid).gridTemplateColumns.trim().split(/\s+/).filter(Boolean).length,
          imageFit: getComputedStyle(image).objectFit,
          imageAlt: image.getAttribute('alt'),
          imageSrc: image.getAttribute('src'),
          nameText: name.textContent.trim(), priceText: price.textContent.replace(/\s+/g,' ').trim(), categoryText: document.querySelector('#detailCategory').textContent.trim(), descText: desc.textContent.trim(), stockText: stock.textContent.trim(),
          stockUnavailable: stock.classList.contains('is-unavailable'),
          addTag: add.tagName, addType: add.getAttribute('type'), addPosition: getComputedStyle(add).position,
          qtyLabel: document.querySelector('#detailQuantityLabel')?.textContent.trim(), qtyAria: qtyInput.getAttribute('aria-label'), qtyButtons: qtyButtons.map(b => ({rect:rect(b), label:b.getAttribute('aria-label'), type:b.getAttribute('type')})),
          variants: variants.map(v => ({rect:rect(v), pressed:v.getAttribute('aria-pressed'), tag:v.tagName, type:v.getAttribute('type')})),
          thumbs: thumbs.map(t => ({rect:rect(t), pressed:t.getAttribute('aria-pressed'), tag:t.tagName, type:t.getAttribute('type'), fit:getComputedStyle(t.querySelector('img')).objectFit})),
          back: {rect:rect(back), tag:back.tagName, type:back.getAttribute('type')}, close: {rect:rect(close), tag:close.tagName, type:close.getAttribute('type')},
          recs: recs.map(r => ({tag:r.tagName, href:r.getAttribute('href'), rect:rect(r), transform:getComputedStyle(r).transform, shadow:getComputedStyle(r).boxShadow})),
          addTransition: getComputedStyle(add).transitionDuration,
          tokens: {ink:root.getPropertyValue('--color-ink').trim(), pink:root.getPropertyValue('--color-kem-pink').trim(), motion:root.getPropertyValue('--motion-standard').trim()},
        };
      });

      const expectedColumns = width >= 1024 ? 2 : 1;
      check(state.htmlWidth <= width && state.bodyWidth <= width, `Open product detail has no page-level overflow at ${width}px`, `${state.htmlWidth}/${state.bodyWidth}/${width}`);
      check(inside(state.modal,width) && inside(state.content,width) && inside(state.grid,width), `Product detail shell stays contained at ${width}px`, JSON.stringify({modal:state.modal,content:state.content,grid:state.grid}));
      check(state.gridColumns === expectedColumns, `Product detail uses intended ${expectedColumns}-column composition at ${width}px`, String(state.gridColumns));
      check(inside(state.media,width) && inside(state.image,width) && state.imageFit === 'contain', `Product media is contained without destructive crop at ${width}px`, JSON.stringify({media:state.media,image:state.image,fit:state.imageFit}));
      check(state.imageAlt === 'Validation Alpha Tee' && /logo-240\.png/.test(state.imageSrc || ''), `Product image and alt come from authoritative product data at ${width}px`, `${state.imageAlt}/${state.imageSrc}`);
      check(state.nameText === 'Validation Alpha Tee' && inside(state.name,width), `Product name is authoritative and contained at ${width}px`, state.nameText);
      check(/EGP 500\.00/.test(state.priceText) && /EGP 450\.00/.test(state.priceText) && /Sale/i.test(state.priceText) && inside(state.price,width), `Genuine active discount is presented from existing discount data at ${width}px`, state.priceText);
      check(state.categoryText === 'Tees' && state.descText === 'Integration smoke test product alpha', `Category and description remain authoritative at ${width}px`, `${state.categoryText}/${state.descText}`);
      check(state.stockText === 'In stock' && !/[⚠✓]|Only \d+/i.test(state.stockText) && !state.stockUnavailable, `Availability is useful and restrained at ${width}px`, state.stockText);
      check(state.variants.length === 4 && state.variants.every(v => v.tag === 'BUTTON' && v.type === 'button' && v.rect.height >= 44 && v.rect.width >= 44 && v.pressed === 'false'), `Variant controls are semantic 44px targets with explicit unselected state at ${width}px`, JSON.stringify(state.variants));
      check(state.qtyLabel === 'Quantity' && state.qtyAria === 'Quantity' && state.qtyButtons.length === 2 && state.qtyButtons.every(b => b.rect.height >= 44 && b.rect.width >= 44 && b.type === 'button' && b.label), `Quantity controls are labelled and at least 44px at ${width}px`, JSON.stringify(state.qtyButtons));
      check(state.addTag === 'BUTTON' && state.addType === 'button' && state.add.height >= 44 && inside(state.add,width) && !['fixed','sticky'].includes(state.addPosition), `Add to Cart is prominent, semantic and unobstructed at ${width}px`, JSON.stringify({rect:state.add,position:state.addPosition}));
      check(state.back.tag === 'BUTTON' && state.close.tag === 'BUTTON' && state.back.rect.height >= 44 && state.close.rect.height >= 44 && inside(state.back.rect,width) && inside(state.close.rect,width), `Back and close controls remain usable at ${width}px`, JSON.stringify({back:state.back,close:state.close}));
      check(state.thumbs.length === 2 && state.thumbs.every(t => t.tag === 'BUTTON' && t.type === 'button' && t.rect.height >= 44 && t.rect.width >= 44 && t.fit === 'contain') && state.thumbs.filter(t => t.pressed === 'true').length === 1, `Gallery thumbnails are semantic, contained and expose selected state at ${width}px`, JSON.stringify(state.thumbs));
      check(state.recs.length === 3 && state.recs.every(r => r.tag === 'A' && /^\?product=\d+$/.test(r.href || '') && r.transform === 'none' && r.shadow === 'none'), `Related products are restrained semantic product links at ${width}px`, JSON.stringify(state.recs));
      check(state.tokens.ink === '#0A0A0A' && state.tokens.pink === '#FF3366' && state.tokens.motion === '200ms', `P2.0 design tokens remain intact in product detail at ${width}px`, JSON.stringify(state.tokens));
      const addTransition = durationSeconds(state.addTransition);
      check(Number.isFinite(addTransition) && addTransition <= 0.001, `Reduced motion suppresses nonessential product-detail transitions at ${width}px`, state.addTransition);

      await page.locator('#productDetailModal .add-to-cart-btn').focus();
      const focus = await page.locator('#productDetailModal .add-to-cart-btn').evaluate(el => { const s=getComputedStyle(el); return {width:s.outlineWidth,style:s.outlineStyle,color:s.outlineColor}; });
      check(focus.width === '3px' && focus.style === 'solid', `P2.1 3px visible keyboard focus remains intact in product detail at ${width}px`, JSON.stringify(focus));
      check(pageErrors.length === 0, `No uncaught browser errors in product detail at ${width}px`, JSON.stringify(pageErrors));
      check(failedLocal.length === 0, `No failed local application requests in product detail at ${width}px`, JSON.stringify(failedLocal));

      await context.close();
    }

    const context = await browser.newContext({ viewport: { width: 390, height: 1000 } });
    const page = await context.newPage();
    const pageErrors = [];
    const failedLocal = [];
    page.on('pageerror', err => pageErrors.push(String(err)));
    page.on('requestfailed', req => { if(req.url().startsWith(BASE)) failedLocal.push(`${req.method()} ${req.url()} ${req.failure()?.errorText || ''}`); });

    await page.goto(`${BASE}/#shop`, { waitUntil:'domcontentloaded' });
    await page.waitForFunction(() => document.querySelectorAll('#shopProductsGrid .product-card').length === 4, null, {timeout:20000});
    await page.locator('#shopProductsGrid a[data-shop-product-id="1"]').click();
    await page.waitForSelector('#productDetailModal.active');
    check(new URL(page.url()).searchParams.get('product') === '1', 'Opening a real Shop product preserves existing ?product=<id> deep link');
    check((await page.locator('#detailName').textContent()).trim() === 'Validation Alpha Tee' && /EGP 500\.00/.test(await page.locator('#detailPrice').innerText()) && /logo-240\.png/.test(await page.locator('#detailImage').getAttribute('src')), 'Name, price and image are sourced from actual product data');

    const secondThumb = page.locator('#detailGallery .product-gallery-thumb').nth(1);
    await secondThumb.focus();
    await page.keyboard.press('Enter');
    check(/favicon-64\.png/.test(await page.locator('#detailImage').getAttribute('src')) && await secondThumb.getAttribute('aria-pressed') === 'true', 'Gallery image switches through keyboard interaction with selected semantics');

    const size = page.locator('#detailSizes .variant-option').first();
    const color = page.locator('#detailColors .variant-option').first();
    await size.focus(); await page.keyboard.press('Space');
    await color.focus(); await page.keyboard.press('Enter');
    check(await size.getAttribute('aria-pressed') === 'true' && await color.getAttribute('aria-pressed') === 'true' && await size.evaluate(el=>el.classList.contains('selected')) && await color.evaluate(el=>el.classList.contains('selected')), 'Size and color variants preserve keyboard selection and explicit selected state');

    await page.getByRole('button', {name:'Increase quantity'}).click();
    check(await page.inputValue('#quantityInput') === '2', 'Quantity increase preserves existing quantity behavior');
    await page.getByRole('button', {name:'Decrease quantity'}).click();
    check(await page.inputValue('#quantityInput') === '1', 'Quantity decrease preserves existing quantity behavior');

    await page.goBack();
    await page.waitForFunction(() => !document.querySelector('#productDetailModal').classList.contains('active'));
    check(new URL(page.url()).searchParams.get('product') === null, 'Browser Back closes product detail and removes product query state');
    await page.goForward();
    await page.waitForSelector('#productDetailModal.active');
    check(new URL(page.url()).searchParams.get('product') === '1' && (await page.locator('#detailName').textContent()).trim() === 'Validation Alpha Tee', 'Browser Forward restores the same product detail');

    await page.locator('#detailSizes .variant-option').first().click();
    await page.locator('#detailColors .variant-option').first().click();
    let addDialog = '';
    page.once('dialog', async dialog => { addDialog = dialog.message(); await dialog.dismiss(); });
    await page.locator('#productDetailModal .add-to-cart-btn').click();
    await page.waitForTimeout(60);
    check(/added to cart/i.test(addDialog) && Number(await page.locator('#cartCount').textContent()) === 1, 'Existing product-detail Add to Cart path mutates cart state');
    check(!(await page.locator('#productDetailModal').evaluate(el=>el.classList.contains('active'))), 'Successful Add to Cart preserves existing detail-close behavior');

    await openProduct(page, 2);
    check((await page.locator('#detailGallery .product-gallery-thumb').count()) === 0 && await page.locator('#detailGallery').getAttribute('hidden') !== null, 'Single-image product gracefully omits fake gallery thumbnails');

    await openProduct(page, 4);
    check(await page.locator('#detailSizesGroup').evaluate(el=>getComputedStyle(el).display) === 'none' && await page.locator('#detailColorsGroup').evaluate(el=>getComputedStyle(el).display) === 'none', 'Product without variants does not render fake variant controls');
    let variantlessDialog = '';
    page.once('dialog', async dialog => { variantlessDialog = dialog.message(); await dialog.dismiss(); });
    await page.locator('#productDetailModal .add-to-cart-btn').click();
    await page.waitForTimeout(50);
    check(/added to cart/i.test(variantlessDialog), 'Variantless product preserves direct Add to Cart behavior without invented requirements');

    await openProduct(page, 3);
    const narrow = await page.evaluate(() => ({
      html:document.documentElement.scrollWidth,
      body:document.body.scrollWidth,
      name:document.querySelector('#detailName').getBoundingClientRect().right,
      price:document.querySelector('#detailPrice').getBoundingClientRect().right,
      stock:document.querySelector('#detailStock').textContent.trim(),
      galleryHidden:document.querySelector('#detailGallery').hidden,
      sizes:getComputedStyle(document.querySelector('#detailSizesGroup')).display,
      colors:getComputedStyle(document.querySelector('#detailColorsGroup')).display,
    }));
    check(narrow.html <= 390 && narrow.body <= 390 && narrow.name <= 390.75 && narrow.price <= 390.75, 'Long product name and large price remain contained on narrow mobile fixture', JSON.stringify(narrow));
    check(narrow.stock === 'Out of stock' && narrow.galleryHidden && narrow.sizes === 'none' && narrow.colors === 'none', 'Out-of-stock single-image variantless fixture presents only real availability/data');
    let stockDialog = '';
    page.once('dialog', async dialog => { stockDialog = dialog.message(); await dialog.dismiss(); });
    await page.locator('#productDetailModal .add-to-cart-btn').click();
    await page.waitForTimeout(50);
    check(/no longer available/i.test(stockDialog), 'Existing stock validation still rejects unavailable product quantity');

    await page.goto(`${BASE}/?product=999999`, {waitUntil:'domcontentloaded'});
    await page.waitForTimeout(600);
    check(!(await page.locator('#productDetailModal').evaluate(el=>el.classList.contains('active'))), 'Invalid product deep link preserves existing missing-product behavior');
    check(pageErrors.length === 0, 'Functional P2.4 flow has no uncaught browser errors', JSON.stringify(pageErrors));
    check(failedLocal.length === 0, 'Functional P2.4 flow has no failed local application requests', JSON.stringify(failedLocal));
    await context.close();
  } finally {
    await browser.close();
    await deleteApp(adminApp);
  }

  console.log(`P2_4_PRODUCT_DETAIL_RESULT ${passes} passed, ${failures.length} failed`);
  if (failures.length) {
    console.error('P2_4_PRODUCT_DETAIL_FAILURES');
    failures.forEach((failure,index)=>console.error(`${index+1}. ${failure}`));
    process.exit(1);
  }
  console.log('P2_4_PRODUCT_DETAIL_COMPLETE');
})().catch(error => { console.error(error); process.exit(1); });
