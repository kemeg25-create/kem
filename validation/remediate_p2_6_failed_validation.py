from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'index.html')
h=p.read_text()
assert 'P2.6 — ACCOUNT / AUTHENTICATION' in h
old="""        let authDialogReturnFocus=null,accountDialogReturnFocus=null;
        function setAuthFeedback"""
new="""        let authDialogReturnFocus=null,accountDialogReturnFocus=null,customerDialogScrollY=0,customerDialogScrollDepth=0;
        function lockCustomerDialogScroll(){if(customerDialogScrollDepth++>0)return;customerDialogScrollY=window.scrollY;const b=document.body;b.style.position='fixed';b.style.top=`-${customerDialogScrollY}px`;b.style.width='100%'}
        function unlockCustomerDialogScroll(){if(customerDialogScrollDepth===0)return;if(--customerDialogScrollDepth>0)return;const b=document.body;b.style.position='';b.style.top='';b.style.width='';window.scrollTo(0,customerDialogScrollY);customerDialogScrollY=0}
        function setAuthFeedback"""
assert old in h
h=h.replace(old,new,1)
h=h.replace("m.classList.add('active');m.setAttribute('aria-hidden','false');document.body.style.overflow='hidden';switchAuthTab('login');", "m.classList.add('active');m.setAttribute('aria-hidden','false');lockCustomerDialogScroll();switchAuthTab('login');",1)
h=h.replace("m.classList.remove('active');m.setAttribute('aria-hidden','true');document.body.style.overflow='auto';setAuthFeedback('');", "m.classList.remove('active');m.setAttribute('aria-hidden','true');unlockCustomerDialogScroll();setAuthFeedback('');",1)
h=h.replace("m.classList.add('active');m.setAttribute('aria-hidden','false');document.body.style.overflow='hidden';requestAnimationFrame(()=>m.querySelector('.close-modal')?.focus());await loadCustomerOrders()", "m.classList.add('active');m.setAttribute('aria-hidden','false');lockCustomerDialogScroll();requestAnimationFrame(()=>m.querySelector('.close-modal')?.focus());await loadCustomerOrders()",1)
h=h.replace("m.classList.remove('active');m.setAttribute('aria-hidden','true');document.body.style.overflow='auto';const t=accountDialogReturnFocus;", "m.classList.remove('active');m.setAttribute('aria-hidden','true');unlockCustomerDialogScroll();const t=accountDialogReturnFocus;",1)
old_login="""                closeAuthModal();
                document.getElementById('loginForm').reset();"""
new_login="""                const accountReturnFocus=authDialogReturnFocus||document.getElementById('authButton');
                closeAuthModal();
                document.getElementById('loginForm').reset();
                await openAccountModal();
                accountDialogReturnFocus=accountReturnFocus;"""
assert old_login in h
h=h.replace(old_login,new_login,1)
assert "document.body.style.overflow='hidden'" not in h[h.index('// Auth Modal Functions (Global)'):h.index('// Custom Cursor')]
assert "await openAccountModal();" in h[h.index('async function handleLogin'):h.index('async function handleSignup')]
p.write_text(h)
print('Applied P2.6 failed-validation remediation')
