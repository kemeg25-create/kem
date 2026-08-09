from pathlib import Path

p = Path('scripts/p0_harden.py')
s = p.read_text()
old = '''start = h.index("async function logoutEmployee()")
end = h.index("\\n        }", start) + len("\\n        }")
logout = h[start:end]
'''
new = '''start = h.index("async function logoutEmployee()")
brace_start = h.index("{", start)
depth = 0
end = None
for pos in range(brace_start, len(h)):
    if h[pos] == "{":
        depth += 1
    elif h[pos] == "}":
        depth -= 1
        if depth == 0:
            end = pos + 1
            break
if end is None:
    raise SystemExit("Could not find logoutEmployee closing brace")
logout = h[start:end]
'''
if old not in s:
    raise SystemExit('hardener logout matcher marker missing')
p.write_text(s.replace(old, new, 1))
print('temporary hardener matcher fixed')
