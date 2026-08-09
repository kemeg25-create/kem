from pathlib import Path
import re
p=Path('index.html'); s=p.read_text()

def replace_fn(name,new):
    global s
    m=re.search(r'^[ \t]*(?:async\s+)?function\s+'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',s,re.M)
    if not m: raise SystemExit('fn '+name)
    start=m.start(); brace=s.find('{',m.start()); i=brace+1; d=1; st='code'; esc=False
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

# Inline checkout status region.
if 'id="checkoutStatus"' not in s:
    s=s.replace('<form id="checkoutForm"','<div id="checkoutStatus" role="status" aria-live="polite" style="margin-bottom:1rem;color:#666;"></div>\n                        <form id="checkoutForm"',1)

# Guest users should learn auth requirement before filling the checkout form.
new_checkout='''        async function checkout() {\n            if(cart.length===0){alert('Your cart is empty');return;}\n            if(!auth?.currentUser){alert('Please sign in before checkout so your order can be linked to your account.');openAuthModal();return;}\n            try{await auth.currentUser.reload();await auth.currentUser.getIdToken(true);}catch(error){console.error('Unable to refresh account:',error);alert('Please sign in again before checkout.');return;}\n            if(!auth.currentUser.emailVerified){alert('Please verify your email before checkout.');return;}\n            document.getElementById('cartPage').classList.remove('active'); document.getElementById('checkoutPage').classList.add('active');\n            const userData=currentUser?.uid?users[currentUser.uid]:null; document.getElementById('checkoutName').value=userData?.name||currentUser?.name||''; document.getElementById('checkoutEmail').value=auth.currentUser.email||''; document.getElementById('checkoutPhone').value=userData?.phone||currentUser?.phone||'';\n            if(userData?.savedAddresses?.length)renderSavedAddresses(userData.savedAddresses);else document.getElementById('savedAddressesSection').style.display='none';\n            renderPaymentMethodsCheckout(); await renderCheckoutSummary(); window.scrollTo(0,0);\n        }\n'''
replace_fn('checkout',new_checkout)

new_summary='''        async function renderCheckoutSummary() {\n            const itemsContainer=document.getElementById('checkoutSummaryItems'); const status=document.getElementById('checkoutStatus'); const orderButton=document.querySelector('.place-order-btn');\n            itemsContainer.innerHTML=cart.map(item=>`<div class="summary-item"><span>${escapeHTML(item.name)}${item.size?` · ${escapeHTML(item.size)}`:''}${item.color?` · ${escapeHTML(item.color)}`:''} x${item.quantity}</span><span>EGP ${(Number(item.price)*item.quantity).toFixed(2)}</span></div>`).join('');\n            if(status)status.textContent='Calculating your order total…'; if(orderButton)orderButton.disabled=true; document.getElementById('checkoutTotal').textContent='Calculating…';\n            try{const quoteOrder=cloudFunctions.httpsCallable('quoteOrder');const response=await quoteOrder({items:cart.map(item=>({id:item.id,quantity:item.quantity,size:item.size||'',color:item.color||''})),couponCode:appliedCoupon?.code||null});const q=response.data;\n                document.getElementById('checkoutSubtotal').textContent=`EGP ${Number(q.subtotal).toFixed(2)}`;document.getElementById('checkoutShipping').textContent=Number(q.shipping)===0?'Free':`EGP ${Number(q.shipping).toFixed(2)}`;document.getElementById('checkoutTotal').textContent=`EGP ${Number(q.total).toFixed(2)}`;\n                const threshold=document.getElementById('checkoutThresholdRow');threshold.style.display=Number(q.thresholdDiscount)>0?'flex':'none';threshold.querySelector('span:last-child').textContent=`-EGP ${Number(q.thresholdDiscount).toFixed(2)}`;const coupon=document.getElementById('checkoutCouponRow');coupon.style.display=Number(q.couponDiscount)>0?'flex':'none';coupon.querySelector('span:last-child').textContent=`-EGP ${Number(q.couponDiscount).toFixed(2)}`;\n                const processing=document.getElementById('checkoutProcessingRow');processing.style.display=Number(q.processingFee)>0?'flex':'none';document.getElementById('checkoutProcessing').textContent=`EGP ${Number(q.processingFee).toFixed(2)}`;const service=document.getElementById('checkoutServiceRow');service.style.display=Number(q.serviceFee)>0?'flex':'none';document.getElementById('checkoutService').textContent=`EGP ${Number(q.serviceFee).toFixed(2)}`;const tax=document.getElementById('checkoutTaxRow');tax.style.display=Number(q.tax)>0?'flex':'none';document.getElementById('checkoutTax').textContent=`EGP ${Number(q.tax).toFixed(2)}`;const savings=Number(q.thresholdDiscount)+Number(q.couponDiscount);const saveRow=document.getElementById('checkoutSavingsRow');saveRow.style.display=savings>0?'flex':'none';saveRow.querySelector('span:last-child').textContent=`EGP ${savings.toFixed(2)}`;\n                if(status)status.textContent='Order total is ready.';if(orderButton)orderButton.disabled=false;return true;\n            }catch(error){console.error('Unable to quote order:',error);document.getElementById('checkoutTotal').textContent='Unable to calculate';if(status)status.textContent=error?.message||'Unable to calculate the order. Review your cart and try again.';if(orderButton)orderButton.disabled=true;return false;}\n        }\n'''
replace_fn('renderCheckoutSummary',new_summary)

# Escape saved-address content and make each card keyboard usable.
new_saved='''        function renderSavedAddresses(addresses) {\n            const section=document.getElementById('savedAddressesSection'),list=document.getElementById('savedAddressesList');if(!addresses?.length){section.style.display='none';return;}section.style.display='block';\n            list.innerHTML=addresses.map(addr=>`<button type="button" style="text-align:left;width:100%;border:2px solid var(--border);padding:1.5rem;border-radius:8px;background:white;position:relative;margin-bottom:.75rem;" onclick="selectSavedAddress(${Number(addr.id)})">${addr.isDefault?'<span style="position:absolute;top:.5rem;right:.5rem;background:var(--accent);color:white;padding:.3rem .8rem;border-radius:4px;font-size:.75rem;font-weight:600;">DEFAULT</span>':''}<span style="display:block;font-weight:700;font-size:1.1rem;margin-bottom:.5rem;">📍 ${escapeHTML(addr.label||'Saved address')}</span><span style="display:block;color:#666;line-height:1.6;">${escapeHTML(addr.address||'')}<br>Building: ${escapeHTML(addr.houseNumber||'')}${addr.floor?`, Floor: ${escapeHTML(addr.floor)}`:''}<br>${escapeHTML(addr.city||'')}${addr.postal?` - ${escapeHTML(addr.postal)}`:''}</span></button>`).join('');\n        }\n'''
replace_fn('renderSavedAddresses',new_saved)

# Improve place-order progress text without changing transaction behavior.
s=s.replace("if (button) button.disabled = true;","if (button) { button.disabled = true; button.dataset.originalText = button.textContent; button.textContent = 'Placing order…'; }",1)
s=s.replace("if (button) button.disabled = false;","if (button) { button.disabled = false; button.textContent = button.dataset.originalText || 'Place Order'; }",1)

# Runtime semantic cleanup: associate labels, modal semantics, missing image alt, and Escape behavior.
helper='''        function enhanceAccessibility() {\n            document.querySelectorAll('label:not([for])').forEach(label=>{const control=label.parentElement?.querySelector('input[id],select[id],textarea[id]');if(control)label.htmlFor=control.id;});\n            document.querySelectorAll('img:not([alt])').forEach(img=>img.alt='');\n            document.querySelectorAll('.form-modal,.auth-modal,.product-detail-modal').forEach(modal=>{if(!modal.hasAttribute('role'))modal.setAttribute('role','dialog');modal.setAttribute('aria-modal','true');if(!modal.hasAttribute('aria-hidden'))modal.setAttribute('aria-hidden',modal.classList.contains('active')?'false':'true');});\n            document.querySelectorAll('.close-modal').forEach(button=>{button.type='button';if(!button.getAttribute('aria-label'))button.setAttribute('aria-label','Close dialog');});\n        }\n\n'''
if 'function enhanceAccessibility()' not in s:
    s=s.replace("        window.addEventListener('DOMContentLoaded', async () => {",helper+"        window.addEventListener('DOMContentLoaded', async () => {",1)
    s=s.replace('makeDashboardTablesResponsive();','makeDashboardTablesResponsive();\n            enhanceAccessibility();',1)

# Escape closes active modal/nav; simple focus containment for active dialog.
if "event.key === 'Escape'" not in s:
    s=s.replace('</script>','''        document.addEventListener('keydown', event => {\n            const dialog=document.querySelector('.form-modal.active,.auth-modal.active,.product-detail-modal.active');\n            if(event.key==='Escape'&&dialog){dialog.querySelector('.close-modal')?.click();return;}\n            if(event.key==='Tab'&&dialog){const focusable=[...dialog.querySelectorAll('button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')].filter(el=>el.offsetParent!==null);if(!focusable.length)return;const first=focusable[0],last=focusable[focusable.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}\n        });\n    </script>''',1)

p.write_text(s);print('checkout/accessibility batch applied')
