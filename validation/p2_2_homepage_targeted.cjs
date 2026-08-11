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
  return rect.left >= -tolerance && rect.right <= width + tolerance && rect.width >= 0;
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
  }, 'p2-2-homepage-targeted');
  const adminDb = getDatabase(adminApp);

  // Exercise the known legacy homepage placeholder directly. P2.2 must sanitize it
  // at presentation time without mutating the authoritative stored settings.
  await adminDb.ref('storeSettings/aboutSection').set({
    title: 'Who We Are',
    content: "KEM isn't just a clothing brand—it's a movement. We're redefining streetwear for the next generation, blending bold aesthetics with sustainable practices. Every piece tells a story, every design challenges conventions.",
    stats: [
      { number: '10K+', label: 'Community Members' },
      { number: '500+', label: 'Unique Pieces' },
      { number: '100%', label: 'Sustainable' },
      { number: '24/7', label: 'Support' },
    ],
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

      await page.goto(BASE, { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => document.querySelectorAll('#homeFeaturedProducts .home-product-card').length === 2, null, { timeout: 20000 });
      await page.waitForFunction(() => document.querySelectorAll('#homeCategoryGrid .home-category-card').length === 2, null, { timeout: 10000 });
      await page.waitForTimeout(80);

      const state = await page.evaluate(() => {
        const rect = el => {
          const r = el.getBoundingClientRect();
          return { left:r.left, right:r.right, top:r.top, bottom:r.bottom, width:r.width, height:r.height };
        };
        const hero = document.querySelector('#home');
        const heroShell = document.querySelector('#homeHeroShell');
        const heroCopy = document.querySelector('.home-hero-copy');
        const title = document.querySelector('#home .hero-title');
        const cta = document.querySelector('#home .cta-button');
        const heroProduct = document.querySelector('#homeHeroProduct');
        const heroMedia = document.querySelector('.home-hero-media');
        const heroImg = document.querySelector('.home-hero-media img');
        const featured = [...document.querySelectorAll('#homeFeaturedProducts .home-product-card')];
        const featuredLinks = [...document.querySelectorAll('#homeFeaturedProducts .home-product-link')];
        const categoryCards = [...document.querySelectorAll('#homeCategoryGrid .home-category-card')];
        const categorySection = document.querySelector('#collections');
        const about = document.querySelector('#about');
        const main = document.querySelector('#mainSite');
        const rootStyle = getComputedStyle(document.documentElement);
        const productImgStyle = getComputedStyle(document.querySelector('.home-product-media img'));
        return {
          htmlWidth: document.documentElement.scrollWidth,
          bodyWidth: document.body.scrollWidth,
          bodyOverflowX: getComputedStyle(document.body).overflowX,
          hero: rect(hero), heroShell: rect(heroShell), heroCopy: rect(heroCopy), title: rect(title), cta: rect(cta),
          heroBackgroundImage: getComputedStyle(hero).backgroundImage,
          heroColumns: getComputedStyle(heroShell).gridTemplateColumns,
          heroProductHidden: heroProduct.hidden,
          heroProduct: rect(heroProduct),
          heroMedia: heroMedia ? rect(heroMedia) : null,
          heroImage: heroImg ? {
            src: heroImg.getAttribute('src'), alt: heroImg.getAttribute('alt'), loading: heroImg.getAttribute('loading'),
            fetchPriority: heroImg.getAttribute('fetchpriority'), objectFit: getComputedStyle(heroImg).objectFit,
          } : null,
          heroName: document.querySelector('.home-hero-name')?.textContent.trim(),
          heroPrice: document.querySelector('.home-hero-price')?.textContent.trim(),
          featured: featured.map(card => rect(card)),
          featuredNames: [...document.querySelectorAll('.home-product-name')].map(el => el.textContent.trim()),
          featuredPrices: [...document.querySelectorAll('.home-product-price')].map(el => el.textContent.trim()),
          featuredHrefs: featuredLinks.map(el => el.getAttribute('href')),
          featuredImageLoading: [...document.querySelectorAll('.home-product-media img')].map(el => el.getAttribute('loading')),
          categorySectionHidden: categorySection.hidden,
          categoryCards: categoryCards.map(card => ({ tag:card.tagName, href:card.getAttribute('href'), ...rect(card) })),
          categoryNames: [...document.querySelectorAll('.home-category-name')].map(el => el.textContent.trim()),
          categoryImageLoading: [...document.querySelectorAll('.home-category-media img')].map(el => el.getAttribute('loading')),
          about: rect(about),
          aboutTitle: document.querySelector('#aboutSectionTitle')?.textContent.trim(),
          aboutContent: document.querySelector('#aboutSectionContent')?.textContent.trim(),
          aboutStatsChildren: document.querySelector('#aboutStatsContainer')?.children.length,
          visibleMainText: main.innerText,
          floatingShapeCount: document.querySelectorAll('#home .floating-shapes, #home .shape').length,
          embeddedPlaceholderImages: [...main.querySelectorAll('img')].filter(img => String(img.getAttribute('src') || '').startsWith('data:image/svg+xml')).length,
          rootTokens: {
            ink: rootStyle.getPropertyValue('--color-ink').trim(),
            pink: rootStyle.getPropertyValue('--color-kem-pink').trim(),
            space: rootStyle.getPropertyValue('--space-128').trim(),
            motion: rootStyle.getPropertyValue('--motion-standard').trim(),
          },
          productImageTransition: productImgStyle.transitionDuration,
          videoCount: main.querySelectorAll('video').length,
          iframeCount: main.querySelectorAll('iframe').length,
        };
      });

      check(state.htmlWidth <= width && state.bodyWidth <= width, `Homepage has no page-level overflow at ${width}px`, `${state.htmlWidth}/${state.bodyWidth}/${width}`);
      check(state.bodyOverflowX !== 'hidden', `Body overflow remains visible at ${width}px`, state.bodyOverflowX);
      check(inside(state.hero, width), `Hero fits viewport at ${width}px`, JSON.stringify(state.hero));
      check(inside(state.heroShell, width) && inside(state.heroCopy, width), `Hero shell and copy stay contained at ${width}px`, JSON.stringify({shell:state.heroShell,copy:state.heroCopy}));
      check(inside(state.title, width) && state.title.height > 0, `Hero title wraps without clipping at ${width}px`, JSON.stringify(state.title));
      check(state.cta.width >= 44 && state.cta.height >= 44 && inside(state.cta, width), `Hero Shop CTA is usable at ${width}px`, JSON.stringify(state.cta));
      check(state.heroBackgroundImage === 'none', `Hero has no decorative gradient at ${width}px`, state.heroBackgroundImage);
      check(state.floatingShapeCount === 0, `Hero decorative geometry is removed at ${width}px`, String(state.floatingShapeCount));
      check(!state.heroProductHidden && state.heroMedia && inside(state.heroProduct, width) && inside(state.heroMedia, width), `Real hero product media is visible and contained at ${width}px`, JSON.stringify({product:state.heroProduct,media:state.heroMedia}));
      check(state.heroImage && state.heroImage.src === 'logo-240.png' && state.heroImage.alt === 'Validation Alpha Tee' && state.heroImage.objectFit === 'contain', `Hero uses authoritative product imagery at ${width}px`, JSON.stringify(state.heroImage));
      check(state.heroImage && state.heroImage.loading !== 'lazy' && state.heroImage.fetchPriority === 'high', `Above-fold hero image is not lazy-loaded at ${width}px`, JSON.stringify(state.heroImage));
      check(state.heroName === 'Validation Alpha Tee' && state.heroPrice === 'EGP 500.00', `Hero product name and price come from catalogue data at ${width}px`, `${state.heroName}/${state.heroPrice}`);

      const columnCount = state.heroColumns.trim().split(/\s+/).filter(Boolean).length;
      if (width < 1024) check(columnCount === 1, `Mobile/tablet hero uses intentional single-column composition at ${width}px`, state.heroColumns);
      else check(columnCount === 2, `Desktop hero uses balanced two-column composition at ${width}px`, state.heroColumns);

      check(state.featured.length === 2, `Homepage shows actual product count without duplication at ${width}px`, String(state.featured.length));
      check(state.featured.every(r => inside(r, width) && r.width > 0 && r.height > 0), `Featured product cards fit at ${width}px`, JSON.stringify(state.featured));
      check(JSON.stringify(state.featuredNames) === JSON.stringify(['Validation Alpha Tee','Validation Beta Hoodie']), `Featured product names are real at ${width}px`, JSON.stringify(state.featuredNames));
      check(JSON.stringify(state.featuredPrices) === JSON.stringify(['EGP 500.00','EGP 900.00']), `Featured product prices are real at ${width}px`, JSON.stringify(state.featuredPrices));
      check(JSON.stringify(state.featuredHrefs) === JSON.stringify(['?product=1','?product=2']), `Featured product links use existing deep-link architecture at ${width}px`, JSON.stringify(state.featuredHrefs));
      check(state.featuredImageLoading.length === 2 && state.featuredImageLoading.every(value => value === 'lazy'), `Below-fold featured images are lazy-loaded at ${width}px`, JSON.stringify(state.featuredImageLoading));

      check(!state.categorySectionHidden && state.categoryCards.length === 2, `Real category section renders at ${width}px`, JSON.stringify(state.categoryNames));
      check(state.categoryCards.every(card => card.tag === 'A' && card.href === '#shop' && card.height >= 44 && inside(card, width)), `Category destinations are semantic navigation links at ${width}px`, JSON.stringify(state.categoryCards));
      check(JSON.stringify(state.categoryNames) === JSON.stringify(['Tees','Hoodies']), `Homepage category names come from Firebase at ${width}px`, JSON.stringify(state.categoryNames));
      check(state.categoryImageLoading.length === 2 && state.categoryImageLoading.every(value => value === 'lazy'), `Category imagery is lazy-loaded at ${width}px`, JSON.stringify(state.categoryImageLoading));

      check(state.aboutTitle === 'KEM' && state.aboutContent === 'KEM is an Egyptian streetwear brand. Explore the current clothing collection.', `Known legacy About placeholder is replaced by restrained truthful presentation at ${width}px`, `${state.aboutTitle}: ${state.aboutContent}`);
      check(state.aboutStatsChildren === 0, `Unverifiable About statistics do not render at ${width}px`, String(state.aboutStatsChildren));
      check(!/10K\+|500\+|100% Sustainable|24\/7 Support|not just a clothing brand|sustainable practices/i.test(state.visibleMainText), `Visible homepage contains no legacy fake claims at ${width}px`);
      check(!/Urban Core|Neon Nights|Minimal Edge/i.test(state.visibleMainText), `Visible homepage contains no fake collection campaigns at ${width}px`);
      check(state.embeddedPlaceholderImages === 0, `Homepage contains no placeholder SVG campaign images at ${width}px`, String(state.embeddedPlaceholderImages));
      check(state.videoCount === 0 && state.iframeCount === 0, `Homepage adds no video or embedded third-party media at ${width}px`, `${state.videoCount}/${state.iframeCount}`);

      check(state.rootTokens.ink === '#0A0A0A' && state.rootTokens.pink === '#FF3366' && state.rootTokens.space === '128px' && state.rootTokens.motion === '200ms', `P2.0 tokens remain intact at ${width}px`, JSON.stringify(state.rootTokens));
      const transition = durationSeconds(state.productImageTransition);
      check(Number.isFinite(transition) && transition <= 0.001, `Reduced motion removes nonessential homepage transitions at ${width}px`, state.productImageTransition);
      check(pageErrors.length === 0, `No uncaught browser errors at ${width}px`, JSON.stringify(pageErrors));
      check(failedLocal.length === 0, `No failed local application requests at ${width}px`, JSON.stringify(failedLocal));

      if (width === 390) {
        const ctaContract = await page.locator('#home .cta-button').evaluate(el => ({ tag:el.tagName, href:el.getAttribute('href') }));
        await page.click('#home .cta-button');
        await page.waitForFunction(() => {
          const target=document.querySelector('#shop');
          return target && target.getBoundingClientRect().top < innerHeight;
        }, null, { timeout: 3000 });
        const shopDestination = await page.locator('#shop').evaluate(el => {
          const r=el.getBoundingClientRect();
          return { top:r.top, bottom:r.bottom, viewport:innerHeight, scrollY:window.scrollY };
        });
        check(ctaContract.tag === 'A' && ctaContract.href === '#shop' && shopDestination.scrollY > 0 && shopDestination.top < shopDestination.viewport, 'Hero CTA uses existing Shop destination', JSON.stringify({ctaContract,shopDestination}));

        await page.evaluate(() => window.scrollTo(0, 0));
        await page.click('#homeFeaturedProducts a[data-home-product-id="1"]');
        await page.waitForSelector('#productDetailModal.active');
        check(/\?product=1(?:&|$)/.test(await page.evaluate(() => location.search)), 'Featured product opens existing ?product=<id> deep link');
        check((await page.locator('#detailGallery button.product-gallery-thumb[data-image-index]').count()) >= 2, 'Featured product opens existing gallery');

        await page.goBack();
        await page.waitForFunction(() => !document.querySelector('#productDetailModal').classList.contains('active'));
        check(!(await page.locator('#productDetailModal').evaluate(el => el.classList.contains('active'))), 'Browser Back closes featured product detail');
        await page.goForward();
        await page.waitForSelector('#productDetailModal.active');
        check(await page.locator('#productDetailModal').evaluate(el => el.classList.contains('active')), 'Browser Forward restores featured product detail');

        const size = page.locator('#detailSizes button[data-variant-index]').first();
        const color = page.locator('#detailColors button[data-variant-index]').first();
        await size.focus(); await page.keyboard.press('Space');
        await color.focus(); await page.keyboard.press('Enter');
        check(await size.evaluate(el => el.classList.contains('selected')) && await color.evaluate(el => el.classList.contains('selected')), 'Product variants remain keyboard functional from homepage product flow');

        let addDialog = '';
        page.once('dialog', async dialog => { addDialog = dialog.message(); await dialog.dismiss(); });
        await page.locator('#productDetailModal .add-to-cart-btn').click();
        await page.waitForTimeout(80);
        check(/added to cart/i.test(addDialog) && Number(await page.locator('#cartCount').textContent()) >= 1, 'Cart addition remains functional from homepage product flow', `${addDialog} / ${await page.locator('#cartCount').textContent()}`);
        await page.keyboard.press('Escape');

        await page.evaluate(() => {
          if (document.querySelector('#productDetailModal').classList.contains('active')) closeProductDetail();
          window.scrollTo(0, 0);
        });
        await page.locator('#homeCategoryGrid a[data-home-category-id="1"]').click();
        await page.waitForFunction(() => getComputedStyle(document.querySelector('#categoryPage')).display !== 'none');
        check((await page.locator('#categoryPageTitle').textContent()).trim() === 'Tees', 'Homepage category control opens existing category destination');
        await page.evaluate(() => closeCategoryPage());
        check(await page.locator('#mainSite').evaluate(el => getComputedStyle(el).display !== 'none'), 'Existing category close behavior returns to homepage');

        await page.evaluate(() => {
          const body=document.body;
          body.setAttribute('tabindex','-1');
          body.focus();
          window.scrollTo(0,0);
        });
        await page.keyboard.press('Tab');
        const focus = await page.evaluate(() => {
          const el=document.activeElement, s=getComputedStyle(el);
          document.body.removeAttribute('tabindex');
          return { id:el.id, outline:s.outlineStyle, width:s.outlineWidth };
        });
        check(focus.id === 'mobileNavToggle' && focus.outline !== 'none' && Number.parseFloat(focus.width) >= 3, 'Frozen P2.1 visible keyboard focus remains intact', JSON.stringify(focus));
      }

      await context.close();
    }
  } finally {
    await browser.close();
    try { adminDb.goOffline(); } catch (_) {}
    await deleteApp(adminApp);
  }

  console.log(`P2_2_HOMEPAGE_RESULT ${passes} passed, ${failures.length} failed`);
  if (failures.length) {
    console.error('P2_2_HOMEPAGE_FAILURES');
    failures.forEach(item => console.error(`- ${item}`));
    process.exit(1);
  }
  console.log('P2_2_HOMEPAGE_COMPLETE');
})().catch(error => {
  console.error(error);
  process.exit(1);
});
