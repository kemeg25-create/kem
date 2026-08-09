from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

# apply-p0.py deliberately strips known legacy secrets. A few duplicate legacy
# functions use those secrets inside conditions; replacing only the literal
# secret would leave an empty condition. Disable those obsolete branches
# explicitly so the document remains valid JavaScript while the secure,
# server-authorized implementations remain the active definitions.
text = text.replace('if (/* removed P0 client-side secret */) {', 'if (false) {')

# These forms are syntactically valid but are made explicit to prevent old
# duplicate functions from granting access even if invoked directly.
text = text.replace('correctPin = /* removed P0 client-side secret */;', 'correctPin = null;')
text = text.replace('const /* removed P0 client-side secret */;', 'const CORRECT_PASSCODE = null;')

if 'if (/* removed P0 client-side secret */)' in text:
    raise SystemExit('Unsafe empty legacy condition remains')

path.write_text(text, encoding='utf-8')
print('Legacy P0 remnants normalized safely.')
