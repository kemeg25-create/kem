const fs = require('fs');
const { chromium } = require('playwright-core');

const BASE = 'http://127.0.0.1:5000';
const PASSWORD = 'Test1234!';
const started = Date.now();
const consoleErrors = [];
const pageErrors = [];
const requestFailures = [];
let browser;
let context;
let page;

function stamp(message, detail = '') {
  const elapsed = ((Date.now() - started) / 1000).toFixed(3);
  console.log(`[${elapsed}s] ${message}${detail ? ` — ${detail}` : ''}`);
}

function assert(condition, name, detail = '') {
  if (!condition) throw new Error(`${name}${detail ? `: ${detail}` : ''}`);
  stamp(`PASS: ${name}`, detail);
}

async function settleLayout() {
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

async function snapshot(width) {
  return page.evaluate(() => {
    const rect = selector => {
      const el = document.querySelector(selector);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width, height: r.height };
    };
    const style = selector => {
      const el = document.querySelector(selector);
      if (!el) return null;
      const s = getComputedStyle(el);
      return { display: s.display, flexDirection: s.flexDirection, flexWrap: s.flexWrap, overflowX: s.overflowX, minWidth: s.minWidth, width: s.width };
    };
    const visibleTableWraps = [...document.querySelectorAll('.data-table-wrap')]
      .filter(el => el.offsetParent !== null)
      .map(el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return { left: r.left, right: r.right, width: r.width, clientWidth: el.clientWidth, scrollWidth: el.scrollWidth, overflowX: s.overflowX };
      });
    const tabs = document.querySelector('.dashboard-tabs');
    return {
      innerWidth,
      rootScrollWidth: document.documentElement.scrollWidth,
      bodyScrollWidth: document.body.scrollWidth,
      dashboard: rect('#employeeDashboard'),
      header: rect('.dashboard-header'),
      title: rect('.dashboard-header h1'),
      actions: rect('.dashboard-header-actions'),
      logout: rect('.dashboard-header-actions .logout-btn'),
      tabs: rect('.dashboard-tabs'),
      dashboardStyle: style('#employeeDashboard'),
      headerStyle: style('.dashboard-header'),
      actionsStyle: style('.dashboard-header-actions'),
      tabsStyle: style('.dashboard-tabs'),
      tabsClientWidth: tabs?.clientWidth || 0,
      tabsScrollWidth: tabs?.scrollWidth || 0,
      visibleTableWraps,
    };
  });
}

async function verifyTabInteractions(width) {
  const visibleTabs = await page.locator('.dashboard-tabs .tab-btn').evaluateAll(buttons => buttons
    .filter(button => button.offsetParent !== null)
    .map(button => button.textContent.trim()));
  assert(visibleTabs.length >= 3, `Dashboard navigation remains usable at ${width}px`, visibleTabs.join(', '));

  for (const label of visibleTabs) {
    const button = page.locator('.dashboard-tabs .tab-btn').filter({ hasText: label }).first();
    await button.click();
    await page.waitForFunction(expected => {
      const active = document.querySelector('.dashboard-tabs .tab-btn.active');
      return active?.textContent.trim() === expected && document.querySelector('.tab-content.active');
    }, label, { timeout: 5000 });
    const activeId = await page.locator('.tab-content.active').getAttribute('id');
    assert(Boolean(activeId), `Dashboard tab ${label} works at ${width}px`, activeId || 'missing active content');

    const m = await snapshot(width);
    assert(m.rootScrollWidth <= m.innerWidth + 2 && m.bodyScrollWidth <= m.innerWidth + 2,
      `Tab ${label} has no page-level overflow at ${width}px`,
      `${m.rootScrollWidth}/${m.bodyScrollWidth}/${m.innerWidth}`);

    for (const wrap of m.visibleTableWraps) {
      assert(wrap.right <= m.innerWidth + 2 && wrap.left >= -2,
        `Visible table container stays inside viewport at ${width}px`,
        JSON.stringify(wrap));
      if (wrap.scrollWidth > wrap.clientWidth + 2) {
        assert(['auto', 'scroll'].includes(wrap.overflowX),
          `Wide table uses intentional internal scrolling at ${width}px`,
          `${wrap.scrollWidth}/${wrap.clientWidth} overflow-x=${wrap.overflowX}`);
      }
    }
  }
}

(async () => {
  const executablePath = process.env.CHROME_PATH;
  assert(executablePath && fs.existsSync(executablePath), 'Chromium executable available', executablePath || 'missing');

  stamp('Launching Chromium');
  browser = await chromium.launch({ executablePath, headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  page = await context.newPage();

  page.on('console', msg => {
    if (msg.type() === 'error') {
      const entry = { text: msg.text(), location: msg.location() };
      consoleErrors.push(entry);
      stamp('BROWSER CONSOLE ERROR', JSON.stringify(entry));
    }
  });
  page.on('pageerror', err => {
    pageErrors.push(String(err));
    stamp('BROWSER PAGE ERROR', String(err));
  });
  page.on('requestfailed', req => {
    const entry = `${req.method()} ${req.url()} :: ${req.failure()?.errorText || 'failed'}`;
    requestFailures.push(entry);
    stamp('REQUEST FAILED', entry);
  });

  stamp('Navigating to emulator hosting');
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForFunction(() => document.querySelectorAll('#shopProductsGrid .product-card').length >= 2, null, { timeout: 30000 });
  stamp('Application storefront ready');

  stamp('Opening employee login');
  await page.evaluate(() => openEmployeeModal());
  await page.fill('#employeeEmail', 'employee@example.com');
  await page.fill('#employeePassword', PASSWORD);
  await page.click('#employeeModal button:has-text("Sign In")');
  await page.waitForSelector('#employeeDashboard.active', { timeout: 15000 });
  await page.waitForFunction(() => firebase.auth().currentUser?.email === 'employee@example.com' && firebase.auth().currentUser.emailVerified === true, null, { timeout: 15000 });
  assert((await page.locator('.dashboard-header h1').textContent()).includes('Employee'), 'Employee login succeeds');
  assert((await page.evaluate(() => orders.length)) >= 2, 'Employee dashboard data loads');

  const widths = [360, 375, 390, 414, 768, 1024, 1440];
  for (const width of widths) {
    stamp(`Testing dashboard viewport ${width}px`);
    await page.setViewportSize({ width, height: 900 });
    await settleLayout();
    const m = await snapshot(width);

    assert(m.rootScrollWidth <= m.innerWidth + 2 && m.bodyScrollWidth <= m.innerWidth + 2,
      `Dashboard has no page-level horizontal overflow at ${width}px`,
      `${m.rootScrollWidth}/${m.bodyScrollWidth}/${m.innerWidth}`);
    assert(m.dashboard && m.dashboard.right <= m.innerWidth + 2 && m.dashboard.left >= -2,
      `Dashboard container fits at ${width}px`, JSON.stringify(m.dashboard));
    assert(m.header && m.header.right <= m.innerWidth + 2,
      `Dashboard header fits at ${width}px`, JSON.stringify(m.header));
    assert(m.actions && m.actions.right <= m.innerWidth + 2,
      `Dashboard header actions fit at ${width}px`, JSON.stringify(m.actions));
    assert(m.logout && m.logout.right <= m.innerWidth + 2 && m.logout.left >= -2,
      `Logout button remains inside viewport at ${width}px`, JSON.stringify(m.logout));
    assert(await page.locator('.dashboard-header-actions .logout-btn').isVisible() && await page.locator('.dashboard-header-actions .logout-btn').isEnabled(),
      `Logout button remains usable at ${width}px`);
    assert(m.tabs && m.tabs.right <= m.innerWidth + 2 && m.tabs.left >= -2,
      `Dashboard tabs container fits at ${width}px`, JSON.stringify(m.tabs));

    if (width <= 768) {
      assert(m.headerStyle?.flexDirection === 'column', `Dashboard header stacks on mobile at ${width}px`, m.headerStyle?.flexDirection || 'missing');
      assert(m.actionsStyle?.flexWrap === 'wrap' && m.actionsStyle?.width !== 'auto',
        `Dashboard header actions wrap full-width at ${width}px`, JSON.stringify(m.actionsStyle));
    }
    if (width <= 1024 && m.tabsScrollWidth > m.tabsClientWidth + 2) {
      assert(['auto', 'scroll'].includes(m.tabsStyle?.overflowX),
        `Dashboard tabs use intentional internal scroll at ${width}px`,
        `${m.tabsScrollWidth}/${m.tabsClientWidth} overflow-x=${m.tabsStyle?.overflowX}`);
    }

    await verifyTabInteractions(width);
  }

  stamp('Testing employee logout');
  await page.setViewportSize({ width: 360, height: 900 });
  await page.locator('.dashboard-header-actions .logout-btn').click();
  await page.waitForFunction(() => !firebase.auth().currentUser, null, { timeout: 15000 });
  assert(!(await page.locator('#employeeDashboard').evaluate(el => el.classList.contains('active'))), 'Employee logout exits dashboard');

  const applicationConsoleErrors = consoleErrors.filter(entry => {
    const url = entry.location?.url || '';
    return url.startsWith(BASE) || /localhost|127\.0\.0\.1/.test(url);
  });
  const localRequestFailures = requestFailures.filter(entry => /127\.0\.0\.1|localhost/.test(entry));
  assert(pageErrors.length === 0, 'No uncaught browser runtime errors', pageErrors.join(' | '));
  assert(applicationConsoleErrors.length === 0, 'No application-origin console errors', JSON.stringify(applicationConsoleErrors));
  assert(localRequestFailures.length === 0, 'No failed local application requests', localRequestFailures.join(' | '));

  stamp('Closing browser page/context');
  await page.close();
  await context.close();
  await browser.close();
  stamp('TARGETED DASHBOARD VALIDATION COMPLETE');
})().catch(async error => {
  console.error(`TARGETED DASHBOARD VALIDATION FAILURE: ${error.stack || error}`);
  try {
    if (page && !page.isClosed()) await page.screenshot({ path: 'validation/dashboard-targeted-failure.png', fullPage: true });
  } catch (screenshotError) {
    console.error('Screenshot capture failed:', screenshotError);
  }
  try { if (page && !page.isClosed()) await page.close(); } catch (_) {}
  try { if (context) await context.close(); } catch (_) {}
  try { if (browser) await browser.close(); } catch (_) {}
  process.exit(1);
});
