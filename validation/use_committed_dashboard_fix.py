from pathlib import Path

p = Path('validation/prepare_emulator.py')
s = p.read_text()

old = '''# Candidate P1 regression fix under validation: keep the existing two-column stats layout,
# but allow grid tracks/items to shrink within narrow phone viewports. Also keep the
# employee dashboard header/actions inside the mobile content box without changing desktop.
responsive_anchor = """            .section-title { font-size:2.5rem; }

            .hero-title {
"""
responsive_fix = """            .section-title { font-size:2.5rem; }
            .about-content, .about-content > * { min-width:0; }
            .stats { grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; }
            .stat-item { padding:1rem; }
            .dashboard { padding-left:1rem; padding-right:1rem; }
            .dashboard-header { flex-direction:column; align-items:stretch; gap:1rem; }
            .dashboard-header h1 { min-width:0; overflow-wrap:anywhere; }
            .dashboard-header-actions { width:100%; min-width:0; flex-wrap:wrap; justify-content:flex-start; }

            .hero-title {
"""
if responsive_anchor not in h:
    raise SystemExit('Mobile responsive anchor not found')
h = h.replace(responsive_anchor, responsive_fix, 1)
'''

new = '''# Candidate P1 regression fix under validation: keep the existing two-column stats layout,
# but allow grid tracks/items to shrink within narrow phone viewports. The employee
# dashboard rules below must already come from the committed application fix; this
# harness preserves them verbatim rather than injecting them.
responsive_anchor = """            .section-title { font-size:2.5rem; }
            .dashboard { padding-left:1rem; padding-right:1rem; }
            .dashboard-header { flex-direction:column; align-items:stretch; gap:1rem; }
            .dashboard-header h1 { min-width:0; overflow-wrap:anywhere; }
            .dashboard-header-actions { width:100%; min-width:0; flex-wrap:wrap; justify-content:flex-start; }

            .hero-title {
"""
responsive_fix = """            .section-title { font-size:2.5rem; }
            .about-content, .about-content > * { min-width:0; }
            .stats { grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; }
            .stat-item { padding:1rem; }
            .dashboard { padding-left:1rem; padding-right:1rem; }
            .dashboard-header { flex-direction:column; align-items:stretch; gap:1rem; }
            .dashboard-header h1 { min-width:0; overflow-wrap:anywhere; }
            .dashboard-header-actions { width:100%; min-width:0; flex-wrap:wrap; justify-content:flex-start; }

            .hero-title {
"""
if h.count(responsive_anchor) != 1:
    raise SystemExit(f'Committed dashboard responsive block missing or duplicated: {h.count(responsive_anchor)}')
h = h.replace(responsive_anchor, responsive_fix, 1)
'''

if s.count(old) != 1:
    raise SystemExit(f'prepare_emulator dashboard injection block not found exactly once: {s.count(old)}')
p.write_text(s.replace(old, new, 1))
print('Adjusted emulator prep to require and preserve the committed dashboard fix')
