const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 360, height: 900 } });
  await page.goto('http://127.0.0.1:5000', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.querySelectorAll('#shopProductsGrid .product-card').length >= 2, null, { timeout: 30000 });
  const report = await page.evaluate(() => {
    const vw = innerWidth;
    const visible = el => {
      const s = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
    };
    const selector = el => {
      if (el.id) return `#${el.id}`;
      let s = el.tagName.toLowerCase();
      if (el.classList.length) s += '.' + [...el.classList].slice(0, 3).join('.');
      return s;
    };
    const offenders = [...document.querySelectorAll('body *')].filter(visible).map(el => {
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return {
        selector: selector(el),
        text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80),
        left: Math.round(r.left * 10) / 10,
        right: Math.round(r.right * 10) / 10,
        width: Math.round(r.width * 10) / 10,
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth,
        position: cs.position,
        minWidth: cs.minWidth,
        widthCss: cs.width,
        padding: cs.padding,
        margin: cs.margin,
      };
    }).filter(x => x.left < -1 || x.right > vw + 1 || x.scrollWidth > x.clientWidth + 1)
      .sort((a, b) => Math.max(b.right - vw, b.scrollWidth - b.clientWidth) - Math.max(a.right - vw, a.scrollWidth - a.clientWidth));
    return { viewport: vw, rootScrollWidth: document.documentElement.scrollWidth, bodyScrollWidth: document.body.scrollWidth, offenders: offenders.slice(0, 30) };
  });
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
  if (report.rootScrollWidth > report.viewport + 2) process.exit(2);
})().catch(e => { console.error(e); process.exit(1); });
