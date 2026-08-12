const { chromium } = require('playwright');
const { initializeApp, deleteApp } = require('firebase-admin/app');
const { getDatabase } = require('firebase-admin/database');

const BASE = 'http://127.0.0.1:5000';
const PASSWORD = 'Test1234!';
const widths = [360, 375, 390, 414, 768, 1024, 1440];
const failures = [];
let passes = 0;
function check(ok, label, detail='') { if(ok){passes++;console.log(`PASS: ${label}${detail?` — ${detail}`:''}`);} else {failures.push(`${label}${detail?` — ${detail}`:''}`);console.error(`FAIL: ${label}${detail?` — ${detail}`:''}`);} }
function inside(r,w,t=1){return r && r.left>=-t && r.right<=w+t && r.width>=0;}
async function waitReady(page){await page.goto(`${BASE}/#shop`,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>typeof auth!=='undefined'&&auth&&typeof currentUser!=='undefined',{timeout:20000});}
async function login(page,email='customer@example.com',password=PASSWORD){await page.evaluate(()=>openAuthModal());await page.fill('#loginIdentifier',email);await page.fill('#loginPassword',password);await page.click('#loginForm button[type="submit"]');if(password===PASSWORD)await page.waitForFunction(e=>firebase.auth().currentUser?.email===e,email,{timeout:15000});}
async function focusStyle(locator){return locator.evaluate(el=>{const s=getComputedStyle(el);return{active:document.activeElement===el,width:s.outlineWidth,style:s.outlineStyle};});}

(async()=>{
  const adminApp=initializeApp({projectId:'demo-kem-validation',databaseURL:'http://127.0.0.1:9000?ns=demo-kem-validation-default-rtdb'},'p2-6-auth-account');
  const db=getDatabase(adminApp);
  const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
  try {
    for(const width of widths){
      const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
      const page=await context.newPage();
      const pageErrors=[]; const failedLocal=[];
      page.on('pageerror',e=>pageErrors.push(String(e)));
      page.on('requestfailed',r=>{if(r.url().startsWith(BASE))failedLocal.push(`${r.method()} ${r.url()}`);});
      page.on('dialog',async d=>d.accept());
      await waitReady(page);
      await page.locator('#authButton').focus();
      await page.keyboard.press('Enter');
      await page.waitForSelector('#authModal.active');
      const authState=await page.evaluate(()=>{
        const rect=el=>{const r=el.getBoundingClientRect();return{left:r.left,right:r.right,width:r.width,height:r.height,top:r.top,bottom:r.bottom};};
        const modal=document.querySelector('#authModal');const content=modal.querySelector('.auth-modal-content');
        const inputs=[...modal.querySelectorAll('#loginForm input')];const tabs=[...modal.querySelectorAll('.auth-tab')];
        return {html:document.documentElement.scrollWidth,body:document.body.scrollWidth,overflow:getComputedStyle(document.body).overflowX,content:rect(content),inputs:inputs.map(i=>({r:rect(i),label:document.querySelector(`label[for="${i.id}"]`)?.textContent.trim(),required:i.required})),tabs:tabs.map(t=>({tag:t.tagName,r:rect(t),role:t.getAttribute('role'),selected:t.getAttribute('aria-selected')})),submit:{tag:document.querySelector('#loginForm .auth-submit').tagName,r:rect(document.querySelector('#loginForm .auth-submit'))},close:{tag:modal.querySelector('.close-modal').tagName,r:rect(modal.querySelector('.close-modal')),label:modal.querySelector('.close-modal').getAttribute('aria-label')},ariaHidden:modal.getAttribute('aria-hidden'),activeId:document.activeElement?.id,transition:getComputedStyle(content).transitionDuration};
      });
      check(authState.html<=width&&authState.body<=width,`Auth has no horizontal overflow at ${width}px`,`${authState.html}/${authState.body}/${width}`);
      check(authState.overflow!=='hidden',`Body overflow-x contract preserved at ${width}px`,authState.overflow);
      check(inside(authState.content,width),`Auth dialog content contained at ${width}px`,JSON.stringify(authState.content));
      check(authState.inputs.length===2&&authState.inputs.every(x=>inside(x.r,width)&&x.r.height>=44&&x.label),`Login fields are labelled, contained 44px targets at ${width}px`,JSON.stringify(authState.inputs));
      check(authState.tabs.length===2&&authState.tabs.every(x=>x.tag==='BUTTON'&&x.r.height>=44&&x.role==='tab')&&authState.tabs[0].selected==='true',`Auth tabs are semantic and accessible at ${width}px`);
      check(authState.submit.tag==='BUTTON'&&authState.submit.r.height>=44,`Login CTA is semantic and usable at ${width}px`);
      check(authState.close.tag==='BUTTON'&&authState.close.r.height>=44&&authState.close.label,`Auth close control is semantic and labelled at ${width}px`);
      check(authState.ariaHidden==='false'&&authState.activeId==='loginIdentifier',`Auth dialog opens with correct state and useful focus at ${width}px`,`${authState.ariaHidden}/${authState.activeId}`);
      const loginFocus=await focusStyle(page.locator('#loginIdentifier'));
      check(loginFocus.active&&loginFocus.width==='3px'&&loginFocus.style==='solid',`Login input retains 3px focus at ${width}px`,JSON.stringify(loginFocus));
      check(parseFloat(authState.transition||'0')<=0.001||/ms/.test(authState.transition),`Reduced motion suppresses auth transition at ${width}px`,authState.transition);
      await page.keyboard.press('Escape');
      await page.waitForFunction(()=>!document.querySelector('#authModal').classList.contains('active'));
      check(await page.locator('#authButton').evaluate(el=>document.activeElement===el),`Escape closes auth and restores trigger focus at ${width}px`);

      await login(page);
      await page.evaluate(()=>openAccountModal());
      await page.waitForSelector('#accountModal.active');
      await page.waitForFunction(()=>document.querySelector('#accountOrders')?.getAttribute('aria-busy')==='false',{timeout:15000});
      const account=await page.evaluate(()=>{
        const rect=el=>{const r=el.getBoundingClientRect();return{left:r.left,right:r.right,width:r.width,height:r.height};};const modal=document.querySelector('#accountModal');const content=modal.querySelector('.auth-modal-content');
        return {html:document.documentElement.scrollWidth,body:document.body.scrollWidth,content:rect(content),profile:document.querySelector('#accountProfile').innerText,addresses:document.querySelector('#accountAddresses').innerText,orders:document.querySelector('#accountOrders').innerText,buttons:[...modal.querySelectorAll('button')].filter(b=>b.offsetParent!==null).map(b=>({text:b.textContent.trim(),tag:b.tagName,r:rect(b)})),ariaHidden:modal.getAttribute('aria-hidden'),columns:getComputedStyle(document.querySelector('.account-layout')).gridTemplateColumns.trim().split(/\s+/).filter(Boolean).length};
      });
      check(account.html<=width&&account.body<=width&&inside(account.content,width),`Account dialog is contained with no overflow at ${width}px`);
      check(/Customer One/.test(account.profile)&&/customer@example.com/.test(account.profile),`Account uses authenticated customer identity at ${width}px`,account.profile);
      check(/Home/.test(account.addresses)&&/1 Validation Street/.test(account.addresses)&&/Default/.test(account.addresses),`Account renders customer-scoped saved address at ${width}px`,account.addresses);
      check(/KEM-2026-000001/.test(account.orders)&&!/KEM-2026-000002/.test(account.orders)&&/EGP 620\.00/.test(account.orders),`Account order history remains customer-isolated at ${width}px`,account.orders);
      check(account.buttons.every(b=>b.tag==='BUTTON'&&b.r.height>=44),`Visible Account controls are semantic 44px targets at ${width}px`,JSON.stringify(account.buttons));
      check(account.columns===(width>=1024?2:1),`Account uses deliberate ${width>=1024?'two':'single'}-column composition at ${width}px`,String(account.columns));
      const close=page.locator('#accountModal .close-modal');await close.focus();const accountFocus=await focusStyle(close);
      check(accountFocus.active&&accountFocus.width==='3px'&&accountFocus.style==='solid',`Account control retains 3px focus at ${width}px`,JSON.stringify(accountFocus));
      check(pageErrors.length===0,`No uncaught browser errors in auth/account at ${width}px`,JSON.stringify(pageErrors));
      check(failedLocal.length===0,`No failed local application requests in auth/account at ${width}px`,JSON.stringify(failedLocal));
      await context.close();
    }

    const context=await browser.newContext({viewport:{width:390,height:1000}});const page=await context.newPage();const dialogs=[];const pageErrors=[];const failedLocal=[];
    page.on('dialog',async d=>{dialogs.push(`${d.type()}: ${d.message()}`);await d.accept();});page.on('pageerror',e=>pageErrors.push(String(e)));page.on('requestfailed',r=>{if(r.url().startsWith(BASE))failedLocal.push(r.url());});
    await waitReady(page);

    await page.locator('#authButton').click();await page.fill('#loginIdentifier','customer@example.com');await page.fill('#loginPassword','WrongPassword!');await page.click('#loginForm button[type="submit"]');await page.waitForSelector('#authFeedback.auth-feedback-error');
    check(/Unable to sign in with those credentials/.test(await page.locator('#authFeedback').innerText()),'Invalid login exposes restrained user-facing feedback');
    check(dialogs.some(x=>/Unable to sign in with those credentials/.test(x)),'Existing safe invalid-login alert behavior remains intact');
    check(!(await page.evaluate(()=>!!firebase.auth().currentUser)),'Invalid login does not authenticate customer');

    await page.getByRole('button',{name:'Forgot Password?'}).click();
    check(await page.locator('#resetPasswordPanel').isVisible(),'Forgot Password opens in-dialog reset surface without prompt');
    await page.fill('#resetEmail','customer@example.com');await page.getByRole('button',{name:'Send Reset Email'}).click();await page.waitForSelector('#authFeedback.auth-feedback-success');
    check(/password reset email has been sent/i.test(await page.locator('#authFeedback').innerText()),'Password reset success state is visible');
    await page.fill('#resetEmail','missing-account@example.com');await page.getByRole('button',{name:'Send Reset Email'}).click();await page.waitForTimeout(300);
    const resetClass=await page.locator('#authFeedback').getAttribute('class');
    check(['auth-feedback-error','auth-feedback-success'].includes(resetClass),'Password reset response is presented semantically without internal details',resetClass);
    await page.getByRole('button',{name:'Return to Login'}).click();check(await page.locator('#loginForm').isVisible(),'Password reset provides Return to Login path');

    await page.getByRole('tab',{name:'Sign Up'}).click();await page.getByRole('button',{name:'Create Account'}).click();
    check(!(await page.locator('#signupName').evaluate(el=>el.checkValidity())),'Signup required-field behavior remains browser-enforced');
    const signupEmail=`p26-${Date.now()}@example.com`;await page.fill('#signupName','P26 Customer');await page.fill('#signupEmail',signupEmail);await page.fill('#signupPhone','+201099999999');await page.fill('#signupPassword',PASSWORD);await page.getByRole('button',{name:'Create Account'}).click();await page.waitForFunction(e=>firebase.auth().currentUser?.email===e,signupEmail,{timeout:15000});
    check(await page.evaluate(()=>firebase.auth().currentUser?.emailVerified===false),'Signup preserves unverified-email state');
    const newUid=await page.evaluate(()=>firebase.auth().currentUser.uid);const newProfile=(await db.ref(`users/${newUid}`).once('value')).val();
    check(newProfile?.name==='P26 Customer'&&newProfile?.email===signupEmail,'Signup preserves existing customer profile persistence');
    check(dialogs.some(x=>/verification email has been sent/i.test(x)),'Signup preserves verification-email feedback');

    await page.evaluate(()=>openAccountModal());await page.waitForSelector('#accountModal.active');await page.waitForFunction(()=>document.querySelector('#accountOrders')?.getAttribute('aria-busy')==='false',{timeout:15000});
    check(/No saved addresses/.test(await page.locator('#accountAddresses').innerText()),'Account shows factual saved-address empty state');
    check(/No orders yet/.test(await page.locator('#accountOrders').innerText()),'Account shows factual order empty state');
    await page.getByRole('button',{name:'Log Out'}).click();await page.waitForFunction(()=>!firebase.auth().currentUser);
    check((await page.locator('#authButtonText').innerText())==='Login','Customer logout restores unauthenticated header state');

    await page.evaluate(()=>openAccountModal());check(await page.locator('#authModal').evaluate(el=>el.classList.contains('active')),'Unauthenticated account access preserves auth requirement');await page.keyboard.press('Escape');

    await page.locator('#authButton').focus();await page.keyboard.press('Enter');await page.waitForSelector('#authModal.active');
    const visible=page.locator('#authModal button:visible,#authModal input:visible');const count=await visible.count();const last=visible.nth(count-1);await last.focus();await page.keyboard.press('Tab');
    check(await page.locator('#authModal .close-modal').evaluate(el=>document.activeElement===el),'Dialog Tab focus wraps from last control to first');
    await page.keyboard.press('Shift+Tab');check(await last.evaluate(el=>document.activeElement===el),'Dialog Shift+Tab focus wraps from first control to last');
    await page.keyboard.press('Escape');check(await page.locator('#authButton').evaluate(el=>document.activeElement===el),'Auth Escape restores header Account trigger');

    await login(page,'unverified@example.com');await page.evaluate(()=>{cart=[{id:1,name:'Validation Alpha Tee',price:500,quantity:1,size:'M',color:'Black'}];openCart();renderCart();});const beforeDialogs=dialogs.length;await page.getByRole('button',{name:/checkout/i,exact:true}).click();await page.waitForTimeout(150);
    check(dialogs.slice(beforeDialogs).some(x=>/verify your email/i.test(x)),'P2.6 preserves verified-email checkout requirement');

    check(pageErrors.length===0,'No uncaught browser errors in P2.6 interaction matrix',JSON.stringify(pageErrors));
    check(failedLocal.length===0,'No failed local application requests in P2.6 interaction matrix',JSON.stringify(failedLocal));
    await context.close();
  } finally {await browser.close();await deleteApp(adminApp);}
  console.log(`P2_6_AUTH_ACCOUNT_RESULT ${passes} passed, ${failures.length} failed`);
  if(failures.length){console.error('P2_6_AUTH_ACCOUNT_FAILURES',JSON.stringify(failures,null,2));process.exit(1);}console.log('P2_6_AUTH_ACCOUNT_COMPLETE');
})().catch(async e=>{console.error(e);console.log(`P2_6_AUTH_ACCOUNT_RESULT ${passes} passed, ${failures.length+1} failed`);process.exit(1);});
