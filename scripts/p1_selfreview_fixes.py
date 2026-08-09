from pathlib import Path
import re
p=Path('index.html'); s=p.read_text()

def replace_fn(name,new,occ=0):
    global s
    ms=list(re.finditer(r'^[ \t]*(?:async\s+)?function\s+'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',s,re.M))
    if len(ms)<=occ: raise SystemExit(f'function {name} occurrence {occ} missing')
    m=ms[occ]; start=m.start(); brace=s.find('{',m.start()); i=brace+1; d=1; st='code'; esc=False
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
    if d: raise SystemExit('unbalanced '+name)
    s=s[:start]+new+s[i:]

# Avoid fake category state when Firebase is empty.
s=s.replace("""        let categories = [
            { id: 1, name: 'Urban Core', description: 'Essential streetwear pieces', visible: true },
            { id: 2, name: 'Neon Nights', description: 'Electric colorways', visible: true },
            { id: 3, name: 'Minimal Edge', description: 'Clean lines', visible: true }
        ];
        let nextCategoryId = 4;""", """        let categories = [];
        let nextCategoryId = 1;""", 1)

replace_fn('saveCategory', '''        async function saveCategory() {
            const id=document.getElementById('editCategoryId').value; const name=document.getElementById('categoryName').value.trim(); const description=document.getElementById('categoryDescription').value.trim(); const displayType=document.getElementById('categoryDisplayType').value; const link=document.getElementById('categoryLink').value.trim(); const visible=document.getElementById('categoryVisible').checked; const selectedItems=Array.from(document.querySelectorAll('.category-item-checkbox:checked')).map(cb=>cb.value);
            if(!name){alert('Please enter a category name');return;} if(displayType!=='filter'&&!selectedItems.length){alert('Please select at least one item to display');return;}
            const next=categories.map(c=>({...c})); if(id){const i=next.findIndex(c=>c.id==id);if(i<0){alert('Category no longer exists.');return;}next[i]={...next[i],name,description,displayType,selectedItems,link,visible};}else next.push({id:nextCategoryId,name,description,displayType,selectedItems,link,visible});
            try{await saveToFirebase('categories',next);categories=next;if(!id)nextCategoryId++;loadCategoriesTable();renderCategoriesDropdown();renderShopFilters();renderShopProducts();closeCategoryModal();updateProductCategoryDropdown();}catch(error){console.error('Category save failed:',error);alert(error?.message||'Unable to save category.');}
        }
''')
replace_fn('deleteCategory', '''        async function deleteCategory(id) { if(!confirm('Delete this category?'))return; const next=categories.filter(c=>Number(c.id)!==Number(id)); try{await saveToFirebase('categories',next);categories=next;loadCategoriesTable();renderCategoriesDropdown();renderShopFilters();renderShopProducts();updateProductCategoryDropdown();}catch(error){console.error('Category delete failed:',error);alert(error?.message||'Unable to delete category.');} }
''')

replace_fn('savePaymentMethod', '''        async function savePaymentMethod() { const id=document.getElementById('editPaymentMethodId').value; const data={name:document.getElementById('paymentMethodName').value.trim(),icon:document.getElementById('paymentMethodIconUrl').value.trim(),instructions:document.getElementById('paymentMethodInstructions').value.trim(),link:document.getElementById('paymentMethodLink').value.trim()}; if(!data.name){alert('Please enter a payment method name');return;} const next=paymentMethods.map(x=>({...x})); if(id){const i=next.findIndex(x=>x.id==id);if(i<0)return;next[i]={...next[i],...data};}else next.push({id:nextPaymentMethodId,...data}); try{await saveToFirebase('paymentMethods',next);paymentMethods=next;if(!id)nextPaymentMethodId++;renderPaymentMethods();closePaymentMethodModal();}catch(error){console.error('Payment method save failed:',error);alert(error?.message||'Unable to save payment method.');} }
''')
replace_fn('deletePaymentMethod', '''        async function deletePaymentMethod(id) { if(!confirm('Delete this payment method?'))return; const next=paymentMethods.filter(x=>Number(x.id)!==Number(id)); try{await saveToFirebase('paymentMethods',next);paymentMethods=next;renderPaymentMethods();}catch(error){console.error('Payment method delete failed:',error);alert(error?.message||'Unable to delete payment method.');} }
''')

# Persist theme and About content through existing protected storeSettings path.
helpers='''        function applyThemeValues(theme) {
            if(!theme)return; const safe={primary:theme.primary||'#0a0a0a',accent:theme.accent||'#ff3366',secondary:theme.secondary||'#00ff88',bg:theme.bg||'#fafafa'}; colorTheme=safe; Object.entries(safe).forEach(([key,value])=>document.documentElement.style.setProperty(`--${key}`,value));
            const map={primary:'primaryColor',accent:'accentColor',secondary:'secondaryColor',bg:'bgColor'}; Object.entries(map).forEach(([key,id])=>{const el=document.getElementById(id);if(el)el.value=safe[key];});
        }

        function applyAboutSectionData(data) {
            if(!data||typeof data!=='object')return; aboutSectionData={title:String(data.title||aboutSectionData.title),content:String(data.content||aboutSectionData.content),stats:Array.isArray(data.stats)?data.stats.slice(0,8):aboutSectionData.stats}; const title=document.getElementById('aboutSectionTitle'),content=document.getElementById('aboutSectionContent'); if(title)title.textContent=aboutSectionData.title;if(content)content.textContent=aboutSectionData.content;renderAboutStats();
        }

'''
anchor='        // Color Theme Functions\n'
if 'function applyThemeValues' not in s:
    if anchor not in s: raise SystemExit('theme anchor')
    s=s.replace(anchor,helpers+anchor,1)
replace_fn('applyColorTheme', '''        async function applyColorTheme() { const theme={primary:document.getElementById('primaryColor').value,accent:document.getElementById('accentColor').value,secondary:document.getElementById('secondaryColor').value,bg:document.getElementById('bgColor').value}; const previous={...colorTheme}; const next={...storeSettings,colorTheme:theme}; try{await saveToFirebase('storeSettings',next);storeSettings=next;applyThemeValues(theme);alert('Color theme saved successfully.');}catch(error){applyThemeValues(previous);console.error('Theme save failed:',error);alert(error?.message||'Unable to save color theme.');} }
''')
replace_fn('resetColorTheme', '''        async function resetColorTheme() { const defaults={primary:'#0a0a0a',accent:'#ff3366',secondary:'#00ff88',bg:'#fafafa'}; Object.entries({primary:'primaryColor',accent:'accentColor',secondary:'secondaryColor',bg:'bgColor'}).forEach(([key,id])=>{document.getElementById(id).value=defaults[key];}); await applyColorTheme(); }
''')
replace_fn('updateAboutSection', '''        async function updateAboutSection() { const title=document.getElementById('aboutTitle').value.trim(),content=document.getElementById('aboutContent').value.trim(); if(!title||!content){alert('Please fill in both title and content');return;} const nextAbout={title,content,stats:(aboutSectionData.stats||[]).map(x=>({number:String(x.number||''),label:String(x.label||'')})).slice(0,8)}; const next={...storeSettings,aboutSection:nextAbout}; try{await saveToFirebase('storeSettings',next);storeSettings=next;applyAboutSectionData(nextAbout);alert('About section saved successfully.');}catch(error){console.error('About section save failed:',error);alert(error?.message||'Unable to save About section.');} }
''')

# Hydrate persisted presentation settings on startup and live changes.
s=s.replace('''            if (storeSettingsData) storeSettings = storeSettingsData;''','''            if (storeSettingsData) { storeSettings = storeSettingsData; applyThemeValues(storeSettings.colorTheme); applyAboutSectionData(storeSettings.aboutSection); }''',1)
s=s.replace("['storeSettings', data => { storeSettings = data || storeSettings; }],","['storeSettings', data => { storeSettings = data || storeSettings; applyThemeValues(storeSettings.colorTheme); applyAboutSectionData(storeSettings.aboutSection); }],",1)

# Employee edits: copy, persist, then expose locally.
replace_fn('saveEmployee', '''        async function saveEmployee() { const oldEmail=document.getElementById('editEmployeeEmail').value; const name=document.getElementById('employeeName').value.trim(); const email=document.getElementById('employeeEmailInput').value.trim().toLowerCase(); const role=document.getElementById('employeeRole').value; if(!name||!email||!role){alert('Please fill in all required fields');return;} if(!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)){alert('Please enter a valid email address');return;} const next={...employeeRoles}; if(oldEmail&&oldEmail!==email)delete next[oldEmail]; next[email]={email,name,role,specialAccess:{promotions:document.getElementById('specialAccessPromotions').checked,settings:document.getElementById('specialAccessSettings').checked}}; try{await saveToFirebase('employeeRoles',next);employeeRoles=next;await loadAdminData();loadEmployees();closeAddEmployeeModal();alert('Employee access updated. The employee must use a verified Firebase Authentication account with this email.');}catch(error){console.error('Employee save failed:',error);alert(error?.message||'Unable to save employee access.');} }
''')

# Cart must show selected variants and escape catalog text.
s=s.replace('''                                <img src="${item.image}" alt="${item.name}" class="cart-item-image">
                                <div class="cart-item-info">
                                    <div class="cart-item-category">KEM Collection</div>
                                    <h3>${item.name}</h3>''','''                                <img src="${escapeHTML(item.image || '')}" alt="${escapeHTML(item.name)}" class="cart-item-image" loading="lazy">
                                <div class="cart-item-info">
                                    <div class="cart-item-category">KEM Collection</div>
                                    <h3>${escapeHTML(item.name)}</h3>
                                    ${(item.size || item.color) ? `<div style="font-size:.85rem;color:#666;">${item.size ? `Size: ${escapeHTML(item.size)}` : ''}${item.size && item.color ? ' · ' : ''}${item.color ? `Color: ${escapeHTML(item.color)}` : ''}</div>` : ''}''',1)

replace_fn('loadRecommendedProducts', '''        function loadRecommendedProducts(category, excludeId) { const grid=document.getElementById('recommendedGrid'); let recommended=products.filter(p=>p.category===category&&Number(p.id)!==Number(excludeId)&&p.status==='Active'); if(recommended.length<4)recommended=[...recommended,...products.filter(p=>p.category!==category&&Number(p.id)!==Number(excludeId)&&p.status==='Active')]; recommended=recommended.slice(0,4); if(!recommended.length){grid.innerHTML='<p style="grid-column:1/-1;color:#666;">No recommendations available yet.</p>';return;} grid.innerHTML=recommended.map(product=>`<article class="recommended-product" tabindex="0" onclick="openProductDetail(${Number(product.id)})" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();openProductDetail(${Number(product.id)})}"><img src="${escapeHTML(product.images?.[0]||product.image||'')}" alt="${escapeHTML(product.name)}" loading="lazy"><div class="recommended-product-name">${escapeHTML(product.name)}</div><div class="recommended-product-price">EGP ${Number(product.price).toFixed(2)}</div></article>`).join(''); }
''')

# Escape employee/category/payment admin renderers so legacy records cannot break the dashboard.
s=s.replace('<td>${emp.name}</td>\n                    <td>${emp.email}</td>\n                    <td><span class="status-badge" style="background: var(--accent); color: white;">${emp.role}</span></td>','<td>${escapeHTML(emp.name)}</td>\n                    <td>${escapeHTML(emp.email)}</td>\n                    <td><span class="status-badge" style="background: var(--accent); color: white;">${escapeHTML(emp.role)}</span></td>',1)
s=s.replace('<td>${cat.name}</td>\n                    <td>${cat.description}</td>','<td>${escapeHTML(cat.name)}</td>\n                    <td>${escapeHTML(cat.description)}</td>',1)
s=s.replace('<h4 style="font-weight: 700;">${pm.name}</h4>','<h4 style="font-weight: 700;">${escapeHTML(pm.name)}</h4>',1)
s=s.replace('<p style="color: #666; white-space: pre-wrap;">${pm.instructions}</p>','<p style="color: #666; white-space: pre-wrap;">${escapeHTML(pm.instructions)}</p>',1)

p.write_text(s)
print('P1 self-review fixes applied')
