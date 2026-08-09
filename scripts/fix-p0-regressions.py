from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')
old = "const userData = users[currentUser.email];"
new = "const userData = currentUser?.uid ? users[currentUser.uid] : null;"
count = text.count(old)
if count != 1:
    raise SystemExit(f'Expected exactly one legacy saved-address lookup, found {count}')
text = text.replace(old, new, 1)

if old in text:
    raise SystemExit('Legacy email-keyed saved-address lookup remains')
if text.count(new) < 2:
    raise SystemExit('UID-keyed customer profile lookup is not consistently used')

path.write_text(text, encoding='utf-8')
print('Saved-address UID regression fixed.')
