from pathlib import Path
import re

p = Path('functions/index.js')
s = p.read_text(encoding='utf-8')

pattern = re.compile(
    r"(async function getEmployeeForRequest\(request, minimumRole = 1\) \{\n"
    r"\s*if \(!request\.auth\?\.uid \|\| !request\.auth\?\.token\?\.email\) \{\n"
    r"\s*throw new HttpsError\('unauthenticated', 'Employee authentication is required\.'\);\n"
    r"\s*\}\n)(\n\s*const email = String\(request\.auth\.token\.email\)\.toLowerCase\(\);)"
)
replacement = r"\1  if (request.auth.token.email_verified !== true) {\n    throw new HttpsError('permission-denied', 'A verified employee email is required.');\n  }\n\2"
s, count = pattern.subn(replacement, s, count=1)
if count != 1:
    raise SystemExit(f'employee verified-email patch expected 1 match, found {count}')

pattern = re.compile(
    r"(\s*if \(!employee \|\| !ROLE_LEVEL\[employee\.role\] \|\| ROLE_LEVEL\[employee\.role\] < minimumRole\) \{\n"
    r"\s*throw new HttpsError\('permission-denied', 'You do not have permission to perform this action\.'\);\n"
    r"\s*\}\n)(\n\s*return \{)"
)
replacement = r"\1\n  if (Object.prototype.hasOwnProperty.call(employee, 'password')) {\n    await snap.ref.child('password').remove();\n  }\2"
s, count = pattern.subn(replacement, s, count=1)
if count != 1:
    raise SystemExit(f'legacy employee-password cleanup expected 1 match, found {count}')

needle = """  const root = snap.val() || {};

  const response = {"""
replacement = """  const root = snap.val() || {};

  if (ROLE_LEVEL[employee.role] >= 5) {
    const cleanup = {};
    for (const [key, value] of Object.entries(root.employeeRoles || {})) {
      if (value && Object.prototype.hasOwnProperty.call(value, 'password')) {
        cleanup[`employeeRoles/${key}/password`] = null;
      }
    }
    for (const [key, value] of Object.entries(root.users || {})) {
      if (value && Object.prototype.hasOwnProperty.call(value, 'password')) {
        cleanup[`users/${key}/password`] = null;
      }
    }
    if (Object.keys(cleanup).length) await db.ref('/').update(cleanup);
  }

  const response = {"""
if s.count(needle) != 1:
    raise SystemExit(f'legacy global-password cleanup expected 1 match, found {s.count(needle)}')
s = s.replace(needle, replacement, 1)

required = [
    "request.auth.token.email_verified !== true",
    "await snap.ref.child('password').remove()",
    "cleanup[`users/${key}/password`] = null"
]
for item in required:
    if item not in s:
        raise SystemExit(f'backend hardening invariant missing: {item}')

p.write_text(s, encoding='utf-8')
print('Backend hardening patch applied.')
