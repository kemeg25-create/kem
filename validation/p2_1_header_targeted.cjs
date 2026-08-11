const { chromium } = require('playwright');
const { initializeApp, deleteApp } = require('../functions/node_modules/firebase-admin/app');
const { getDatabase } = require('../functions/node_modules/firebase-admin/database');

const BASE = 'http://127.0.0.1:5000';
const widths = [360, 375, 390, 414, 768, 1024, 1440];
const failures = [];
let passes = 0;

function check(ok, label, detail = '') {
  if (!ok) {
    failures.push(`${label}${detail ? ` — ${detail}` : ''}`);
    console.error(`FAIL: ${label}${detail ? ` — ${detail}` : ''}`);
  } else {
    passes += 1;
    console.log(`PASS: ${label}${detail ? ` — ${detail}` : ''}`);
  }
}

function intersects(a, b, allowance = 0) {
  return Math.max(a.left, b.left) < Math.min(a.right, b.right) - allowance &&
         Math.max(a.top, b.top) < Math.min(a.bottom, b.bottom) - allowance;
}

function seconds(value) {
  const first = String(value || '').split(',')[0].trim();
  if (first.endsWith('ms')) return Number.parseFloat(first) / 1000;
  if (first.endsWith('s')) return Number.parseFloat(first);
  return Number.NaN;
}

(async () => {
  // The permanent smoke fixture intentionally omits `visible` because P1 tests do not
  // require the dynamic navigation dropdown. P2.1 specifically must exercise visible
  // category destinations, so enrich only this isolated emulator fixture, not app code.
  const adminApp = initializeApp({
    projectId: 'demo-kem-validation',
    databaseURL: 'http://127.0.0.1:9000?ns=demo-kem-validation-default-rtdb',
  }, 'p2-1-header-targeted');
  const adminDb = getDatabase(adminApp);
  await adminDb.ref('categories/0/visible').set(true);
  await adminDb.ref('categories/1/visible').set(true);

  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  try {
    for (const width of widths) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const pageErrors = [];
      const failedLocal = [];
      page.on('pageerror', err => pageErrors.push(String(err)));
      page.on('requestfailed', req => {
        if (req.url().startsWith(BASE)) failedLocal.push(`${req.method()} ${req.url()} ${req.failure()?.errorText || ''}`);
      });

      await page.goto(BASE, { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => document.querySelectorAll('#shopProductsGrid .product-card').length >= 2, null, { timeout: 20000 });
      await page.waitForFunction(() => document.querySelectorAll('#categoriesDropdown .nav-dropdown-item').length >= 2, null, { timeout: 10000 });
      await page.waitForTimeout(100);

      const base = await page.evaluate(() => {
        const rect = el => {
          const r = el.getBoundingClientRect();
          return { left:r.left, right:r.right, top:r.top, bottom:r.bottom, width:r.width, height:r.height };
        };
        const style = el => getComputedStyle(el);
        const header = document.querySelector('#mainNav');
        const shell = document.querySelector('.nav-shell');
        const logo = document.querySelector('#mainNav .logo');
        const actions = document.querySelector('.header-actions');
        const auth = document.querySelector('#authButton');
        const cart = document.querySelector('#cartBadge');
        const toggle = document.querySelector('#mobileNavToggle');
        const desktopSearch = document.querySelector('#headerSearch');
        const desktopSearchWrap = desktopSearch.closest('.header-search');
        const navLinks = document.querySelector('#primaryNav');
        return {
          viewport: innerWidth,
          htmlWidth: document.documentElement.scrollWidth,
          bodyWidth: document.body.scrollWidth,
          bodyOverflowX: style(document.body).overflowX,
          header: rect(header), shell: rect(shell), logo: rect(logo), actions: rect(actions), auth: rect(auth), cart: rect(cart), toggle: rect(toggle),
          toggleDisplay: style(toggle).display,
          desktopSearchWrapDisplay: style(desktopSearchWrap).display,
          desktopSearch: rect(desktopSearch),
          navDisplay: style(navLinks).display,
          cartDisplay: style(cart).display,
        };
      });

      check(base.htmlWidth <= width && base.bodyWidth <= width, `No page-level overflow at ${width}px`, `${base.htmlWidth}/${base.bodyWidth}/${width}`);
      check(base.bodyOverflowX !== 'hidden', `Body overflow remains visible at ${width}px`, base.bodyOverflowX);
      check(base.header.left >= -0.5 && base.header.right <= width + 0.5, `Header fits viewport at ${width}px`, JSON.stringify(base.header));
      check(base.logo.width > 0 && base.logo.left >= 0 && base.logo.right <= width, `KEM logo visible and unclipped at ${width}px`, JSON.stringify(base.logo));
      check(base.auth.width >= 44 && base.auth.height >= 44, `Account target is at least 44px at ${width}px`, `${base.auth.width}x${base.auth.height}`);
      check(base.cart.width >= 44 && base.cart.height >= 44 && base.cartDisplay !== 'none', `Cart target is visible and at least 44px at ${width}px`, `${base.cart.width}x${base.cart.height} ${base.cartDisplay}`);
      check(base.header.height <= 80, `Header remains restrained at ${width}px`, `${base.header.height}px`);

      const destinations = await page.evaluate(() => ({
        home: document.querySelector('#mainNav .logo')?.getAttribute('href'),
        shop: document.querySelector('#primaryNav a[href="#shop"]')?.getAttribute('href'),
        collections: document.querySelector('#primaryNav a[href="#collections"]')?.getAttribute('href'),
        about: document.querySelector('#primaryNav a[href="#about"]')?.getAttribute('href'),
        contact: document.querySelector('#primaryNav a[href="#contact"]')?.getAttribute('href'),
        categoryButton: Boolean(document.querySelector('.nav-dropdown-btn')),
        targets: ['home','shop','collections','about','contact'].every(id => Boolean(document.getElementById(id))),
      }));
      check(destinations.home === '#home' && destinations.shop === '#shop' && destinations.collections === '#collections' && destinations.about === '#about' && destinations.contact === '#contact' && destinations.categoryButton && destinations.targets, `Real navigation destinations are preserved at ${width}px`, JSON.stringify(destinations));

      if (width <= 960) {
        check(base.toggleDisplay !== 'none' && base.toggle.width >= 44 && base.toggle.height >= 44, `Mobile menu target is usable at ${width}px`, `${base.toggleDisplay} ${base.toggle.width}x${base.toggle.height}`);
        check(base.desktopSearchWrapDisplay === 'none' && base.desktopSearch.width === 0, `Desktop search yields to mobile menu at ${width}px`, `${base.desktopSearchWrapDisplay}/${base.desktopSearch.width}px`);
        check(!intersects(base.toggle, base.logo, 0.5), `Menu and logo do not overlap at ${width}px`, JSON.stringify({toggle:base.toggle,logo:base.logo}));
        check(!intersects(base.logo, base.actions, 0.5), `Logo and account/cart do not overlap at ${width}px`, JSON.stringify({logo:base.logo,actions:base.actions}));

        await page.focus('#mobileNavToggle');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(30);
        const openState = await page.evaluate(() => {
          const nav=document.querySelector('#primaryNav'), toggle=document.querySelector('#mobileNavToggle'), search=document.querySelector('#mobileHeaderSearch');
          const r=nav.getBoundingClientRect(), sr=search.getBoundingClientRect();
          const labels=[...nav.children].filter(li=>!li.classList.contains('mobile-header-search')).map(li=>li.querySelector('a,.nav-dropdown-btn')?.textContent.trim()).filter(Boolean);
          return { open:nav.classList.contains('mobile-open'), expanded:toggle.getAttribute('aria-expanded'), nav:{left:r.left,right:r.right,width:r.width}, search:{width:sr.width,height:sr.height}, labels, scrollWidth:document.documentElement.scrollWidth };
        });
        check(openState.open && openState.expanded === 'true', `Mobile menu opens by keyboard at ${width}px`, JSON.stringify(openState));
        check(openState.nav.left >= -0.5 && openState.nav.right <= width + 0.5 && openState.scrollWidth <= width, `Open mobile menu stays contained at ${width}px`, JSON.stringify(openState.nav));
        check(openState.search.width > 0 && openState.search.height >= 44, `Mobile search is usable at ${width}px`, JSON.stringify(openState.search));
        check(JSON.stringify(openState.labels) === JSON.stringify(['Shop','Categories','Collections','About','Contact']), `Mobile shopping hierarchy is correct at ${width}px`, JSON.stringify(openState.labels));

        await page.fill('#mobileHeaderSearch', 'Alpha');
        await page.waitForTimeout(80);
        check((await page.inputValue('#shopSearch')) === 'Alpha' && (await page.locator('#shopProductsGrid .product-card').count()) === 1, `Mobile header search uses existing filtering at ${width}px`);
        await page.fill('#mobileHeaderSearch', '');

        await page.focus('.nav-dropdown-btn');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(30);
        const categoryOpen = await page.evaluate(() => ({
          active: document.querySelector('#categoriesDropdown').classList.contains('active'),
          expanded: document.querySelector('.nav-dropdown-btn').getAttribute('aria-expanded'),
          buttons: [...document.querySelectorAll('#categoriesDropdown .nav-dropdown-item')].map(el => ({tag:el.tagName,h:el.getBoundingClientRect().height})),
          width: document.documentElement.scrollWidth,
        }));
        check(categoryOpen.active && categoryOpen.expanded === 'true', `Categories opens accessibly at ${width}px`, JSON.stringify(categoryOpen));
        check(categoryOpen.buttons.length >= 2 && categoryOpen.buttons.every(x => x.tag === 'BUTTON' && x.h >= 44), `Category choices are semantic 44px buttons at ${width}px`, JSON.stringify(categoryOpen.buttons));
        check(categoryOpen.width <= width, `Categories dropdown creates no overflow at ${width}px`, `${categoryOpen.width}/${width}`);
        await page.keyboard.press('Escape');
        check(!(await page.locator('#categoriesDropdown').evaluate(el => el.classList.contains('active'))) && await page.locator('.nav-dropdown-btn').evaluate(el => document.activeElement === el), `Escape closes categories and restores focus at ${width}px`);
        await page.keyboard.press('Escape');
        check(!(await page.locator('#primaryNav').evaluate(el => el.classList.contains('mobile-open'))) && await page.locator('#mobileNavToggle').evaluate(el => document.activeElement === el), `Escape closes mobile menu and restores focus at ${width}px`);
      } else {
        check(base.toggleDisplay === 'none', `Desktop header hides mobile trigger at ${width}px`, base.toggleDisplay);
        check(base.desktopSearchWrapDisplay !== 'none' && base.desktopSearch.width > 0 && base.desktopSearch.height >= 44, `Desktop search is integrated at ${width}px`, JSON.stringify(base.desktopSearch));
        const desktopLayout = await page.evaluate(() => {
          const action=document.querySelector('.header-actions').getBoundingClientRect();
          const navEls=[...document.querySelectorAll('#primaryNav > li:not(.mobile-header-search)')].filter(el=>getComputedStyle(el).display!=='none');
          const last=navEls.at(-1).getBoundingClientRect();
          const labels=navEls.map(li=>li.querySelector('a,.nav-dropdown-btn')?.textContent.trim()).filter(Boolean);
          return { action:{left:action.left,right:action.right}, last:{left:last.left,right:last.right}, labels };
        });
        check(desktopLayout.last.right <= desktopLayout.action.left + 0.5, `Desktop navigation does not collide with utilities at ${width}px`, JSON.stringify(desktopLayout));
        check(JSON.stringify(desktopLayout.labels) === JSON.stringify(['Shop','Categories','Collections','About','Contact']), `Desktop shopping hierarchy is correct at ${width}px`, JSON.stringify(desktopLayout.labels));

        await page.fill('#headerSearch', 'Alpha');
        await page.waitForTimeout(80);
        check((await page.inputValue('#shopSearch')) === 'Alpha' && (await page.locator('#shopProductsGrid .product-card').count()) === 1, `Desktop header search uses existing filtering at ${width}px`);
        await page.fill('#headerSearch', 'NoSuchKEMProduct');
        await page.waitForTimeout(80);
        check((await page.locator('#shopProductsGrid .product-card').count()) === 0 && /0 products found/i.test(await page.locator('#shopResultsStatus').textContent()), `Header search preserves no-results state at ${width}px`);
        await page.fill('#headerSearch', '');

        await page.focus('.nav-dropdown-btn');
        await page.keyboard.press('Enter');
        const categoryDesktop = await page.evaluate(() => ({
          active:document.querySelector('#categoriesDropdown').classList.contains('active'),
          expanded:document.querySelector('.nav-dropdown-btn').getAttribute('aria-expanded'),
          buttons:[...document.querySelectorAll('#categoriesDropdown .nav-dropdown-item')].map(el=>({tag:el.tagName,h:el.getBoundingClientRect().height}))
        }));
        check(categoryDesktop.active && categoryDesktop.expanded === 'true', `Desktop categories opens by keyboard at ${width}px`);
        check(categoryDesktop.buttons.length >= 2 && categoryDesktop.buttons.every(x=>x.tag==='BUTTON'&&x.h>=44), `Desktop category choices are semantic buttons at ${width}px`, JSON.stringify(categoryDesktop.buttons));
        await page.keyboard.press('Escape');
        check(!(await page.locator('#categoriesDropdown').evaluate(el=>el.classList.contains('active'))) && await page.locator('.nav-dropdown-btn').evaluate(el=>document.activeElement===el), `Desktop categories closes with Escape at ${width}px`);
      }

      if (width === 390) {
        const p20 = await page.evaluate(() => {
          const root=getComputedStyle(document.documentElement);
          const card=getComputedStyle(document.querySelector('.product-card'));
          const toggle=getComputedStyle(document.querySelector('#mobileNavToggle'));
          return {
            ink:root.getPropertyValue('--color-ink').trim(), pink:root.getPropertyValue('--color-kem-pink').trim(), space:root.getPropertyValue('--space-128').trim(), motion:root.getPropertyValue('--motion-standard').trim(),
            cardTransform:card.transform, cardShadow:card.boxShadow, toggleTransition:toggle.transitionDuration,
          };
        });
        check(p20.ink==='#0A0A0A' && p20.pink==='#FF3366' && p20.space==='128px' && p20.motion==='200ms', 'P2.0 tokens remain intact', JSON.stringify(p20));
        check(p20.cardTransform==='none' && p20.cardShadow==='none', 'P2.0 quiet product-card foundation remains intact', JSON.stringify(p20));
        check(Number.isFinite(seconds(p20.toggleTransition)) && seconds(p20.toggleTransition) <= 0.001, 'Reduced motion remains effective in header', p20.toggleTransition);

        await page.click('#authButton');
        await page.waitForSelector('#authModal.active');
        const authFieldHeight = await page.locator('#authModal input').first().evaluate(el=>el.getBoundingClientRect().height);
        check(authFieldHeight >= 48, 'P2.0 form foundation remains intact', `${authFieldHeight}px`);
        await page.keyboard.press('Escape');
        check(!(await page.locator('#authModal').evaluate(el=>el.classList.contains('active'))), 'Account dialog Escape behavior remains intact');

        await page.click('#cartBadge');
        await page.waitForSelector('#cartPage.active');
        check(await page.locator('#cartPage').evaluate(el=>el.classList.contains('active')), 'Header cart opens existing cart view');
        await page.evaluate(() => closeCart());
        check(!(await page.locator('#cartPage').evaluate(el=>el.classList.contains('active'))), 'Existing cart close behavior remains intact');

        await page.evaluate(() => { document.activeElement?.blur(); window.scrollTo(0, 0); });
        await page.keyboard.press('Tab');
        const focusStyle = await page.evaluate(() => {
          const el=document.activeElement, s=getComputedStyle(el);
          return { id:el.id, outline:s.outlineStyle, width:s.outlineWidth, color:s.outlineColor };
        });
        check(focusStyle.id === 'mobileNavToggle' && focusStyle.outline !== 'none' && Number.parseFloat(focusStyle.width) >= 3, 'Header retains strong visible keyboard focus', JSON.stringify(focusStyle));
      }

      check(pageErrors.length === 0, `No uncaught browser errors at ${width}px`, JSON.stringify(pageErrors));
      check(failedLocal.length === 0, `No failed local requests at ${width}px`, JSON.stringify(failedLocal));
      await context.close();
    }
  } finally {
    await browser.close();
    adminDb.goOffline();
    await deleteApp(adminApp);
  }

  console.log(`P2_1_HEADER_RESULT ${passes} passed, ${failures.length} failed`);
  if (failures.length) process.exit(1);
  console.log('P2_1_HEADER_COMPLETE');
})().catch(err => { console.error(err); process.exit(1); });
