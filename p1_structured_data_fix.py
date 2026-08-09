from pathlib import Path
import json
import re

p = Path('index.html')
h = p.read_text()

pattern = re.compile(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I)
blocks = list(pattern.finditer(h))
if not blocks:
    raise SystemExit('No JSON-LD blocks found')

invalid = []
for i, m in enumerate(blocks, 1):
    try:
        json.loads(m.group(1))
    except Exception as exc:
        invalid.append(i)
        print(f'JSON-LD block {i} invalid before repair: {exc}')

if invalid != [1]:
    raise SystemExit(f'Expected only block 1 to be contaminated, got {invalid}')

first = blocks[0]
body = first.group(1)
pop_marker = "window.addEventListener('popstate'"
key_marker = "document.addEventListener('keydown', event => {"
if pop_marker not in body or key_marker not in body:
    raise SystemExit('Expected inert popstate/keydown handlers not found in JSON-LD')

json_text = body[:body.index(pop_marker)].strip()
store = json.loads(json_text)

# Preserve only claims grounded by the current storefront configuration.
for key in ('email', 'sameAs', 'priceRange'):
    store.pop(key, None)
store.pop('telephone', None)
store['acceptedPaymentMethod'] = ['Cash']
store['currenciesAccepted'] = 'EGP'
store['paymentAccepted'] = 'Cash on Delivery'

clean_block = '<script type="application/ld+json">\n' + json.dumps(store, indent=2, ensure_ascii=False) + '\n    </script>'
h = h[:first.start()] + clean_block + h[first.end():]

# The contaminated listeners were not executable. Ensure there are no live copies before insertion.
if h.count(pop_marker) != 0:
    raise SystemExit('Unexpected executable popstate listener already present')
if h.count(key_marker) != 0:
    raise SystemExit('Unexpected executable keydown listener already present')

handlers = '''        window.addEventListener('popstate', () => {
            const id = Number(new URL(window.location.href).searchParams.get('product'));
            if (id) {
                openProductDetail(id, { fromHistory: true });
            } else if (document.getElementById('productDetailModal')?.classList.contains('active')) {
                closeProductDetail({ fromHistory: true });
            }
        });

        document.addEventListener('keydown', event => {
            const dialog = document.querySelector('.form-modal.active,.auth-modal.active,.product-detail-modal.active');
            if (!dialog) return;
            if (event.key === 'Escape') {
                dialog.querySelector('.close-modal')?.click();
                return;
            }
            if (event.key !== 'Tab') return;
            const focusable = [...dialog.querySelectorAll('button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')]
                .filter(el => el.offsetParent !== null);
            if (!focusable.length) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        });

'''
anchor = '        // Close dropdown when clicking outside\n'
if anchor not in h:
    raise SystemExit('Normal executable event-wiring anchor not found')
h = h.replace(anchor, handlers + anchor, 1)

p.write_text(h)
print('Repaired JSON-LD and restored popstate/keyboard handlers exactly once')
