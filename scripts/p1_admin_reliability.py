from pathlib import Path
import re
p=Path('index.html'); s=p.read_text()

def replace_fn(name,new,which=0):
    global s
    ms=list(re.finditer(r'^[ \t]*(?:async\s+)?function\s+'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',s,re.M))
    if not ms: raise SystemExit('fn '+name)
    m=ms[which]; start=m.start(); brace=s.find('{',m.start()); i=brace+1; d=1; st='code'; esc=False
    while i<len(s) and d:
        c=s[i]; n=s[i+1] if i+1<len(s) else ''
        if st=='line':
            if c=='\n': st='code'
        elif st=='block':
            if c=='*' and n=='/': st='code'; i+=1
        elif st in ('sq','dq','tpl'):
            if esc: esc=False
            elif c=='\\': esc=True
            elif st=='sq' and c=="'": st='code'
            elif st=='dq' and c=='"': st='code'
            elif st=='tpl' and c=='`': st='code'
        else:
            if c=='/' and n=='/': st='line'; i+=1
            elif c=='/' and n=='*': st='block'; i+=1
            elif c=="'": st='sq'
            elif c=='"': st='dq'
            elif c=='`': st='tpl'
            elif c=='{': d+=1
            elif c=='}': d-=1
        i+=1
    s=s[:start]+new+s[i:]

def remove_all(name):
    while re.search(r'^[ \t]*(?:async\s+)?function\s+'+re.escape(name)+r'\s*\(',s,re.M): replace_fn(name,'',0)

# Remove fake dashboard commerce data; Firebase now supplies real data or an empty collection.
s=re.sub(r"        let products = \[.*?\n        \];\n\n        let orders = \[.*?\n        \];", "        let products = [];\n\n        let orders = [];", s, count=1, flags=re.S)

# Canonical category dropdown for object-backed categories.
replace_fn('updateProductCategoryDropdown', '''        function updateProductCategoryDropdown() {\n            const dropdown=document.getElementById('productCategory'); if(!dropdown)return; const current=dropdown.value;\n            const names=[...new Set(categories.map(getCategoryName).filter(Boolean))]; dropdown.innerHTML='<option value="">Select Category</option>';\n            names.forEach(name=>{const option=document.createElement('option');option.value=name;option.textContent=name;dropdown.appendChild(option);});\n            if(current&&names.includes(current))dropdown.value=current;\n        }\n''')

# Reliable product delete.
replace_fn('deleteProduct', '''        async function deleteProduct(id) {\n            if(!confirm('Are you sure you want to delete this product?'))return; const next=products.filter(p=>Number(p.id)!==Number(id));\n            try{await saveToFirebase('products',next);products=next;loadProducts();renderShopProducts();updateInventoryOverview();}\n            catch(error){console.error('Product delete failed:',error);alert(error?.message||'Unable to delete product.');}\n        }\n''')

# Store settings must persist before confirming.
replace_fn('updateStoreSetting', '''        async function updateStoreSetting(settingName) {\n            const input=document.getElementById(settingName); let value=input.value;\n            if(settingName==='taxEnabled') value=value==='true'; else {value=parseFloat(value);if(!Number.isFinite(value)||value<0){alert('Please enter a valid non-negative number');return;}}\n            const previous={...storeSettings}; const next={...storeSettings,[settingName]:value};\n            try{await saveToFirebase('storeSettings',next);storeSettings=next;updateStoreSettingsPreview();alert('Setting saved successfully.');}\n            catch(error){storeSettings=previous;loadStoreSettings();console.error('Setting save failed:',error);alert(error?.message||'Unable to save setting.');}\n        }\n''')

replace_fn('saveSocialLinks', '''        async function saveSocialLinks() {\n            try{await saveToFirebase('socialLinks',socialLinks);renderFooterSocialLinks();alert('Social links saved successfully.');}\n            catch(error){console.error('Social link save failed:',error);alert(error?.message||'Unable to save social links.');}\n        }\n''')

# Promotion CRUD helpers use copy-then-commit so failed writes do not lie to the employee.
replace_fn('saveAnnouncement', '''        async function saveAnnouncement() {\n            const id=document.getElementById('announcementId').value; const data={title:document.getElementById('announcementTitle').value.trim(),message:document.getElementById('announcementMessage').value.trim(),button:document.getElementById('announcementButton').value.trim(),link:document.getElementById('announcementLink').value.trim(),status:document.getElementById('announcementStatus').value}; if(!data.title||!data.message){alert('Title and message are required.');return;} const next=announcements.map(x=>({...x})); if(id){const i=next.findIndex(x=>x.id==id);if(i<0)return;next[i]={...next[i],...data};}else next.push({id:nextAnnouncementId,...data}); try{await saveToFirebase('announcements',next);announcements=next;if(!id)nextAnnouncementId++;loadAnnouncements();closeAnnouncementModal();showActiveAnnouncements();alert('Announcement saved successfully.');}catch(error){console.error(error);alert(error?.message||'Unable to save announcement.');}\n        }\n''')
replace_fn('deleteAnnouncement', '''        async function deleteAnnouncement(id) { const next=announcements.filter(x=>x.id!==id); try{await saveToFirebase('announcements',next);announcements=next;loadAnnouncements();}catch(error){console.error(error);alert(error?.message||'Unable to delete announcement.');} }\n''')

replace_fn('saveCoupon', '''        async function saveCoupon() {\n            const id=document.getElementById('couponId').value; const existing=id?coupons.find(c=>c.id==id):null; const data={code:document.getElementById('couponCode').value.trim().toUpperCase(),type:document.getElementById('couponType').value,value:parseFloat(document.getElementById('couponValue').value),minOrder:parseFloat(document.getElementById('couponMinOrder').value)||0,limit:parseInt(document.getElementById('couponLimit').value,10)||0,status:document.getElementById('couponStatus').value,used:existing?.used||0}; if(!data.code||!Number.isFinite(data.value)||data.value<0){alert('Enter a valid coupon code and value.');return;} const next=coupons.map(c=>({...c})); if(id){const i=next.findIndex(c=>c.id==id);if(i<0)return;next[i]={...next[i],...data};}else next.push({id:nextCouponId,...data}); try{await saveToFirebase('coupons',next);coupons=next;if(!id)nextCouponId++;loadCoupons();closeCouponModal();alert('Coupon saved successfully.');}catch(error){console.error(error);alert(error?.message||'Unable to save coupon.');}\n        }\n''')
replace_fn('deleteCoupon', '''        async function deleteCoupon(id) { const next=coupons.filter(c=>c.id!==id); try{await saveToFirebase('coupons',next);coupons=next;loadCoupons();}catch(error){console.error(error);alert(error?.message||'Unable to delete coupon.');} }\n''')

replace_fn('saveProductDiscount', '''        async function saveProductDiscount() { const id=document.getElementById('productDiscountId').value; const data={productId:parseInt(document.getElementById('discountProductId').value,10),type:document.getElementById('productDiscountType').value,value:parseFloat(document.getElementById('productDiscountValue').value),status:document.getElementById('productDiscountStatus').value}; if(!data.productId||!Number.isFinite(data.value)||data.value<0){alert('Select a product and valid discount.');return;} const next=productDiscounts.map(d=>({...d})); if(id){const i=next.findIndex(d=>d.id==id);if(i<0)return;next[i]={...next[i],...data};}else next.push({id:nextProductDiscountId,...data}); try{await saveToFirebase('productDiscounts',next);productDiscounts=next;if(!id)nextProductDiscountId++;loadProductDiscounts();closeProductDiscountModal();renderShopProducts();alert('Product discount saved.');}catch(error){console.error(error);alert(error?.message||'Unable to save product discount.');} }\n''')
replace_fn('deleteProductDiscount', '''        async function deleteProductDiscount(id) { const next=productDiscounts.filter(d=>d.id!==id); try{await saveToFirebase('productDiscounts',next);productDiscounts=next;loadProductDiscounts();renderShopProducts();}catch(error){console.error(error);alert(error?.message||'Unable to delete product discount.');} }\n''')

replace_fn('saveThresholdDiscount', '''        async function saveThresholdDiscount() { const id=document.getElementById('thresholdDiscountId').value; const data={threshold:parseFloat(document.getElementById('thresholdAmount').value),type:document.getElementById('thresholdDiscountType').value,value:parseFloat(document.getElementById('thresholdDiscountValue').value),status:document.getElementById('thresholdDiscountStatus').value}; if(!Number.isFinite(data.threshold)||data.threshold<0||!Number.isFinite(data.value)||data.value<0){alert('Enter valid threshold values.');return;} const next=thresholdDiscounts.map(d=>({...d})); if(id){const i=next.findIndex(d=>d.id==id);if(i<0)return;next[i]={...next[i],...data};}else next.push({id:nextThresholdDiscountId,...data}); try{await saveToFirebase('orderDiscounts',next);thresholdDiscounts=next;if(!id)nextThresholdDiscountId++;loadThresholdDiscounts();closeThresholdDiscountModal();alert('Threshold discount saved.');}catch(error){console.error(error);alert(error?.message||'Unable to save threshold discount.');} }\n''')
replace_fn('deleteThresholdDiscount', '''        async function deleteThresholdDiscount(id) { const next=thresholdDiscounts.filter(d=>d.id!==id); try{await saveToFirebase('orderDiscounts',next);thresholdDiscounts=next;loadThresholdDiscounts();}catch(error){console.error(error);alert(error?.message||'Unable to delete threshold discount.');} }\n''')

replace_fn('deleteEmployee', '''        async function deleteEmployee(email) { if(email==='kem.eg25@gmail.com'){alert('Cannot delete the CEO account');return;} const next={...employeeRoles}; delete next[email]; try{await saveToFirebase('employeeRoles',next);employeeRoles=next;loadEmployees();}catch(error){console.error(error);alert(error?.message||'Unable to delete employee access.');} }\n''')

# Exactly one secure showDashboard, protected data loads before dashboard appears.
remove_all('showDashboard')
secure='''        async function showDashboard() {\n            if(!currentEmployee)return; try{await loadAdminData();}catch(error){console.error('Unable to load secure employee data:',error);alert('Unable to load the employee dashboard securely.');return;}\n            document.getElementById('mainSite').style.display='none';document.getElementById('mainNav').style.display='none';document.getElementById('employeeDashboard').classList.add('active');\n            const roleLevel=roleHierarchy[currentEmployee.role]||0,special=currentEmployee.specialAccess||{}; const promo=document.getElementById('promotionsTabBtn'),settings=document.querySelector('.tab-btn[onclick="switchTab(\\'settings\\')"]'),employees=document.getElementById('employeesTabBtn'),security=document.getElementById('securityTabBtn'); if(promo)promo.style.display=(roleLevel>=3||special.promotions)?'inline-block':'none';if(settings)settings.style.display=(roleLevel>=3||special.settings)?'inline-block':'none';if(employees)employees.style.display=roleLevel===5?'inline-block':'none';if(security)security.style.display=roleLevel===5?'inline-block':'none';\n            const header=document.querySelector('.dashboard-header h1');if(header)header.innerHTML=`Employee Dashboard <span style="font-size:1rem;font-weight:600;color:var(--accent);margin-left:1rem;">${escapeHTML(currentEmployee.role)} • ${escapeHTML(currentEmployee.email)}</span>`; updateProductCategoryDropdown();loadProducts();loadOrders();updateInventoryOverview();updateSalesMetrics();if(roleLevel>=3||special.settings){loadFooterSettings();loadStoreSettings();loadAboutSection();}if(roleLevel===5)loadEmployees();\n        }\n\n'''
pos=re.search(r'^[ \t]*async function logoutEmployee\s*\(',s,re.M)
if not pos: raise SystemExit('logout marker')
s=s[:pos.start()]+secure+s[pos.start():]

# Wrap data tables once for horizontal scrolling on smaller screens.
insert="""        window.addEventListener('DOMContentLoaded', async () => {\n"""
if 'function makeDashboardTablesResponsive' not in s:
    helper="""        function makeDashboardTablesResponsive() { document.querySelectorAll('.data-table').forEach(table=>{if(table.parentElement?.classList.contains('data-table-wrap'))return;const wrap=document.createElement('div');wrap.className='data-table-wrap';table.parentNode.insertBefore(wrap,table);wrap.appendChild(table);}); }\n\n"""
    s=s.replace(insert,helper+insert,1)
    s=s.replace("renderFooterSocialLinks();\n            const initialProductId", "renderFooterSocialLinks();\n            makeDashboardTablesResponsive();\n            const initialProductId",1) if 'const initialProductId' in s else s.replace('renderFooterSocialLinks();\n            // Clear coupon','renderFooterSocialLinks();\n            makeDashboardTablesResponsive();\n            // Clear coupon',1)

p.write_text(s);print('admin reliability batch applied')
