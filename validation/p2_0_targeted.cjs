const { chromium } = require('playwright');

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

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
  try {
    for (const width of widths) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const errors = [];
      const failedLocal = [];
      page.on('pageerror', err => errors.push(String(err)));
      page.on('requestfailed', req => {
        if (req.url().startsWith(BASE)) failedLocal.push(`${req.method()} ${req.url()} ${req.failure()?.errorText || ''}`);
      });
      await page.goto(BASE, { waitUntil: 'domcontentloaded' });
      await page.waitForSelector('.product-card', { timeout: 10000 });
      await page.waitForTimeout(120);

      const metrics = await page.evaluate(() => ({
        inner: innerWidth,
        html: document.documentElement.scrollWidth,
        body: document.body.scrollWidth,
        overflowX: getComputedStyle(document.body).overflowX,
        gutter: getComputedStyle(document.documentElement).getPropertyValue('--page-gutter').trim(),
      }));
      check(metrics.html <= width && metrics.body <= width, `No page-level overflow at ${width}px`, `${metrics.html}/${metrics.body}/${metrics.inner}`);
      check(metrics.overflowX !== 'hidden', `Body does not conceal overflow at ${width}px`, metrics.overflowX);

      const expectedGutter = width <= 768 ? '16px' : width <= 1024 ? '32px' : '48px';
      check(metrics.gutter === expectedGutter, `Responsive design-system gutter at ${width}px`, metrics.gutter);

      if (width === 390) {
        const tokens = await page.evaluate(() => {
          const s = getComputedStyle(document.documentElement);
          return {
            ink: s.getPropertyValue('--color-ink').trim(),
            pink: s.getPropertyValue('--color-kem-pink').trim(),
            green: s.getPropertyValue('--color-kem-green').trim(),
            success: s.getPropertyValue('--color-success').trim(),
            spacing: s.getPropertyValue('--space-128').trim(),
            customer: s.getPropertyValue('--container-customer').trim(),
            motion: s.getPropertyValue('--motion-standard').trim(),
          };
        });
        check(tokens.ink === '#0A0A0A', 'Ink token is centralized', tokens.ink);
        check(tokens.pink === '#FF3366', 'KEM pink token is centralized', tokens.pink);
        check(tokens.green === '#00FF99', 'KEM green token is centralized', tokens.green);
        check(tokens.success === '#16754A', 'Semantic success token is distinct', tokens.success);
        check(tokens.spacing === '128px', 'Spacing scale reaches 128px', tokens.spacing);
        check(tokens.customer === '1400px', 'Customer max-width token is present', tokens.customer);
        check(tokens.motion === '200ms', 'Motion token is present', tokens.motion);

        const card = await page.locator('.product-card').first().evaluate(el => {
          const s = getComputedStyle(el);
          return { transform: s.transform, shadow: s.boxShadow, radius: s.borderRadius, border: s.borderTopColor };
        });
        check(card.transform === 'none', 'Product card default has no decorative transform', JSON.stringify(card));
        check(card.shadow === 'none', 'Product card default has no decorative shadow', card.shadow);

        await page.locator('.product-card').first().hover();
        await page.waitForTimeout(40);
        const hover = await page.locator('.product-card').first().evaluate(el => ({ transform: getComputedStyle(el).transform, shadow: getComputedStyle(el).boxShadow }));
        check(hover.transform === 'none' && hover.shadow === 'none', 'Product card hover stays restrained', JSON.stringify(hover));

        const shapeMotion = await page.locator('.shape').first().evaluate(el => ({ duration: getComputedStyle(el).animationDuration, iterations: getComputedStyle(el).animationIterationCount }));
        check(shapeMotion.duration === '0.00001s' || shapeMotion.duration === '0s', 'Reduced motion suppresses decorative animation', JSON.stringify(shapeMotion));

        await page.locator('#authButton').click();
        await page.waitForSelector('#authModal.active');
        const authUi = await page.evaluate(() => {
          const modal = document.querySelector('#authModal');
          const input = modal.querySelector('input');
          const label = modal.querySelector('label');
          const close = modal.querySelector('.close-modal');
          const ir = input.getBoundingClientRect();
          const cr = close.getBoundingClientRect();
          return {
            inputHeight: ir.height,
            inputBorder: getComputedStyle(input).borderTopWidth,
            labelTransform: getComputedStyle(label).textTransform,
            closeW: cr.width,
            closeH: cr.height,
            closeBg: getComputedStyle(close).backgroundColor,
          };
        });
        check(authUi.inputHeight >= 48, 'Shared form control meets 48px field foundation', JSON.stringify(authUi));
        check(authUi.labelTransform === 'none', 'Shared form label is not forced uppercase', authUi.labelTransform);
        check(authUi.closeW >= 44 && authUi.closeH >= 44, 'Shared modal close target is at least 44px', `${authUi.closeW}x${authUi.closeH}`);
        await page.keyboard.press('Escape');
        check(!(await page.locator('#authModal').evaluate(el => el.classList.contains('active'))), 'Escape behavior preserved after modal styling');

        await page.locator('.product-card').first().click();
        await page.waitForSelector('#productDetailModal.active');
        const variantSizes = await page.locator('.variant-option').evaluateAll(items => items.map(el => {
          const r = el.getBoundingClientRect(); return [r.width, r.height];
        }));
        check(variantSizes.length > 0 && variantSizes.every(([w,h]) => w >= 44 && h >= 44), 'Variant controls retain 44px minimum targets', JSON.stringify(variantSizes));
        await page.keyboard.press('Escape');
      }

      check(errors.length === 0, `No uncaught browser errors at ${width}px`, JSON.stringify(errors));
      check(failedLocal.length === 0, `No failed local requests at ${width}px`, JSON.stringify(failedLocal));
      await context.close();
    }
  } finally {
    await browser.close();
  }

  console.log(`P2_0_TARGETED_RESULT ${passes} passed, ${failures.length} failed`);
  if (failures.length) process.exit(1);
  console.log('P2_0_TARGETED_COMPLETE');
})().catch(err => { console.error(err); process.exit(1); });
