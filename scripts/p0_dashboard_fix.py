from pathlib import Path

p = Path('index.html')
s = p.read_text()
old = """                function showDashboard() {
            if (!currentEmployee) return;

            document.getElementById('mainSite').style.display = 'none';
"""
new = """                async function showDashboard() {
            if (!currentEmployee) return;

            try {
                await loadAdminData();
            } catch (error) {
                console.error('Unable to load secure employee data:', error);
                alert('Unable to load the employee dashboard securely. Please try again.');
                return;
            }

            document.getElementById('mainSite').style.display = 'none';
"""
if old not in s:
    if 'async function showDashboard()' in s and 'await loadAdminData();' in s:
        print('already fixed')
    else:
        raise SystemExit('showDashboard marker missing')
else:
    p.write_text(s.replace(old,new,1))
    print('dashboard regression fixed')
