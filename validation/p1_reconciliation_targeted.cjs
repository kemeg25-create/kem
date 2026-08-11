const fs = require('fs');
const { chromium } = require('playwright-core');
const BASE='http://127.0.0.1:5000';
const PASSWORD='Test1234!';
const widths=[360,375,390,414,768,1024,1440];
let browser,context,page;
const pageErrors=[]; const localFailures=[];
function ok(v,n,d=''){if(!v)throw new Error(`${n}${d?`: ${d}`:''}`);console.log(`PASS: ${n}${d?` — ${d}`:''}`)}
(async()=>{
 const executablePath=process.env.CHROME_PATH; ok(executablePath&&fs.existsSync(executablePath),'Chromium executable available',executablePath||'missing');
 browser=await chromium.launch({executablePath,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 context=await browser.newContext({viewport:{width:1440,height:1000}}); page=await context.newPage();
 page.on('pageerror',e=>pageErrors.push(String(e)));
 page.on('requestfailed',r=>{if(/127\.0\.0\.1|localhost/.test(r.url()))localFailures.push(`${r.method()} ${r.url()} ${r.failure()?.errorText||''}`)});
 await page.goto(BASE,{waitUntil:'domcontentloaded',timeout:30000});
 await page.waitForFunction(()=>document.querySelectorAll('#shopProductsGrid .product-card').length>=2,null,{timeout:30000});
 for(const width of widths){
  await page.setViewportSize({width,height:900});
  const m=await page.evaluate(()=>{const box=s=>{const e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();return{left:r.left,right:r.right,width:r.width}};return{iw:innerWidth,root:document.documentElement.scrollWidth,body:document.body.scrollWidth,about:box('.about-content'),stats:box('.stats'),items:[...document.querySelectorAll('.stats .stat-item')].map(e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,width:r.width}})}});
  ok(m.root<=m.iw+2&&m.body<=m.iw+2,`Homepage has no page-level overflow at ${width}px`,`${m.root}/${m.body}/${m.iw}`);
  ok(!m.about||(m.about.left>=-2&&m.about.right<=m.iw+2),`About content fits at ${width}px`,JSON.stringify(m.about));
  ok(!m.stats||(m.stats.left>=-2&&m.stats.right<=m.iw+2),`About stats fit at ${width}px`,JSON.stringify(m.stats));
  ok(m.items.every(x=>x.left>=-2&&x.right<=m.iw+2),`About stat items fit at ${width}px`,JSON.stringify(m.items));
 }
 await page.setViewportSize({width:390,height:900});
 const filters=page.locator('#shopFilterButtons .filter-btn'); ok(await filters.count()>=2,'Category filters render');
 await filters.nth(1).focus(); await page.keyboard.press('Enter');
 ok(await filters.nth(1).evaluate(e=>e.classList.contains('active')),'Category filter activates by keyboard Enter');
 await filters.nth(0).focus(); await page.keyboard.press('Space');
 ok(await filters.nth(0).evaluate(e=>e.classList.contains('active')),'All Products filter activates by keyboard Space');
 await page.locator('#shopProductsGrid .product-card').first().click(); await page.waitForSelector('#productDetailModal.active');
 const thumbs=page.locator('#detailGallery .product-gallery-thumb'); if(await thumbs.count()>1){await thumbs.nth(1).focus();await page.keyboard.press('Enter');ok(await thumbs.nth(1).evaluate(e=>e.classList.contains('active')),'Gallery thumbnail activates by keyboard Enter');}
 const sizes=page.locator('#detailSizes .variant-option'); if(await sizes.count()){await sizes.first().focus();await page.keyboard.press('Space');ok(await sizes.first().evaluate(e=>e.classList.contains('selected')),'Size variant activates by keyboard Space');}
 const colors=page.locator('#detailColors .variant-option'); if(await colors.count()){await colors.first().focus();await page.keyboard.press('Enter');ok(await colors.first().evaluate(e=>e.classList.contains('selected')),'Color variant activates by keyboard Enter');}
 await page.keyboard.press('Escape'); await page.waitForFunction(()=>!document.querySelector('#productDetailModal')?.classList.contains('active'));
 await page.evaluate(()=>openEmployeeModal()); await page.waitForSelector('#employeeModal.active'); ok(await page.locator('#employeeModal').isVisible(),'Employee login opens');
 const focusables=page.locator('#employeeModal input,#employeeModal button'); const count=await focusables.count(); ok(count>=3,'Employee login has focusable controls');
 await focusables.nth(count-1).focus(); await page.keyboard.press('Tab');
 ok(await focusables.first().evaluate(e=>document.activeElement===e),'Employee login Tab focus trap wraps');
 await page.keyboard.press('Escape'); await page.waitForFunction(()=>!document.querySelector('#employeeModal')?.classList.contains('active')); ok(true,'Escape closes employee login');
 await page.evaluate(()=>openEmployeeModal()); await page.fill('#employeeEmail','employee@example.com'); await page.fill('#employeePassword',PASSWORD); await page.click('#employeeModal button:has-text("Sign In")');
 await page.waitForSelector('#employeeDashboard.active',{timeout:15000}); ok(true,'Employee login reaches dashboard');
 ok(pageErrors.length===0,'No uncaught browser runtime errors',pageErrors.join(' | ')); ok(localFailures.length===0,'No failed local application requests',localFailures.join(' | '));
 await page.close(); await context.close(); await browser.close(); console.log('P1 RECONCILIATION TARGETED COMPLETE');
})().catch(async e=>{console.error(e.stack||e);try{if(page&&!page.isClosed())await page.screenshot({path:'validation/p1-reconciliation-targeted-failure.png',fullPage:true})}catch(_){};try{if(page&&!page.isClosed())await page.close()}catch(_){};try{if(context)await context.close()}catch(_){};try{if(browser)await browser.close()}catch(_){};process.exit(1)});
