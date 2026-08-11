const { chromium } = require('playwright');

const BASE = 'http://127.0.0.1:5000';
const PASSWORD = 'Test1234!';

(async () => {
  const executablePath = process.env.CHROME_PATH || chromium.executablePath();
  const browser = await chromium.launch({ executablePath, headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const page = await browser.newPage({ viewport: { width: 360, height: 900 } });
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForFunction(() => document.querySelectorAll('#shopProductsGrid .product-card').length >= 2, null, { timeout: 30000 });
  await page.evaluate(() => openEmployeeModal());
  await page.fill('#employeeEmail', 'ceo@example.com');
  await page.fill('#employeePassword', PASSWORD);
  await page.click('#employeeModal button:has-text("Sign In")');
  await page.waitForSelector('#employeeDashboard.active', { timeout: 15000 });
  await page.waitForTimeout(200);

  const diagnostic = await page.evaluate(() => {
    const vw = innerWidth;
    const dashboard = document.querySelector('#employeeDashboard');
    const visible = [...dashboard.querySelectorAll('*')].filter(el => el.offsetParent !== null);
    const offenders = visible.map(el => {
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const parent = el.parentElement;
      return {
        tag: el.tagName.toLowerCase(),
        id: el.id || '',
        classes: typeof el.className === 'string' ? el.className.slice(0, 120) : '',
        parent: parent ? `${parent.tagName.toLowerCase()}#${parent.id || ''}.${typeof parent.className === 'string' ? parent.className.split(/\s+/).slice(0, 3).join('.') : ''}` : '',
        text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 100),
        left: Math.round(r.left),
        right: Math.round(r.right),
        width: Math.round(r.width),
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth,
        minWidth: cs.minWidth,
        widthCss: cs.width,
        display: cs.display,
        overflowX: cs.overflowX,
        whiteSpace: cs.whiteSpace,
      };
    }).filter(x => x.right > vw + 2 || x.left < -2 || x.scrollWidth > x.clientWidth + 2)
      .sort((a, b) => Math.max(b.right - vw, b.scrollWidth - b.clientWidth) - Math.max(a.right - vw, a.scrollWidth - a.clientWidth))
      .slice(0, 30);

    return {
      viewport: vw,
      rootScrollWidth: document.documentElement.scrollWidth,
      bodyScrollWidth: document.body.scrollWidth,
      dashboardRect: dashboard.getBoundingClientRect().toJSON(),
      offenders,
    };
  });

  console.log('DASHBOARD_OVERFLOW_DIAGNOSTIC');
  console.log(JSON.stringify(diagnostic, null, 2));
  await browser.close();
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
