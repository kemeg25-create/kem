#!/usr/bin/env bash
set -euo pipefail
P25="$1"
P26="$2"

# Load exact committed production source plus frozen suite versions.
git checkout "$P26" -- index.html functions database.rules.json firebase.json payment-success.html payment-failed.html robots.txt sitemap.xml apple-touch-icon.png favicon-64.png logo-240.png
git show a4faeca2d0e7663e5230a1997ad777a9ba58c8e3:validation/p2_5_cart_checkout_targeted.cjs > /tmp/p2_5.cjs
git show 411e5fc1ef75e19de360f1bf224d297c89968d4c:validation/p2_4_product_detail_targeted.cjs > /tmp/p2_4.cjs
git show a43242d59f8c258de698f4770d6e732b9ac00283:validation/p2_3_shop_targeted.cjs > /tmp/p2_3.cjs
git show b49e760e0df1fba774d9a8e332a67dc1b84d568a:validation/p2_1_header_targeted.cjs > /tmp/p2_1.cjs
python3 - <<'PY'
from pathlib import Path
p=Path('/tmp/p2_4.cjs');src=p.read_text()
old="""      await page.locator('#productDetailModal .add-to-cart-btn').focus();
      const focus = await page.locator('#productDetailModal .add-to-cart-btn').evaluate(el => { const s=getComputedStyle(el); return {width:s.outlineWidth,style:s.outlineStyle,color:s.outlineColor}; });
      check(focus.width === '3px' && focus.style === 'solid', `P2.1 3px visible keyboard focus remains intact in product detail at ${width}px`, JSON.stringify(focus));"""
new="""      await page.getByRole('button', { name: 'Increase quantity' }).focus();
      await page.keyboard.press('Tab');
      const focus = await page.locator('#productDetailModal .add-to-cart-btn').evaluate(el => { const s=getComputedStyle(el); return {active:document.activeElement===el,width:s.outlineWidth,style:s.outlineStyle,color:s.outlineColor}; });
      check(focus.active && focus.width === '3px' && focus.style === 'solid', `P2.1 3px visible keyboard focus remains intact in product detail at ${width}px`, JSON.stringify(focus));"""
if old in src: p.write_text(src.replace(old,new,1))
PY

node --check functions/index.js
node --check validation/p2_6_auth_account_targeted.cjs
node --check /tmp/p2_5.cjs
node --check /tmp/p2_4.cjs
node --check /tmp/p2_3.cjs
node --check validation/p2_2_homepage_targeted.cjs
node --check /tmp/p2_1.cjs
node --check validation/p1_reconciliation_targeted.cjs
node --check validation/dashboard_targeted.cjs
node --check validation/smoke.cjs

python3 validation/prepare_emulator.py
python3 validation/patch_functions_runtime.py
python3 validation/full_runtime_patch.py
node --check functions/index.js
node --check validation/smoke.cjs

git diff -U0 "$P26" -- index.html functions/index.js > /tmp/runtime-app.diff || true
if grep -E 'P2\.6|authModal|accountModal|loginForm|signupForm|resetPassword|handleLogin|handleSignup|handleForgotPassword|openAccountModal|logoutUser|openCart|cartPage|checkoutPage|quoteOrder|createOrder|P2\.5|P2\.4|product-detail|P2\.3|kem-shop|P2\.2|home-hero|P2\.1|nav-shell|employeeModal|logoutEmployee' /tmp/runtime-app.diff; then
  cat /tmp/runtime-app.diff
  echo 'Runtime preparation altered committed application behavior'
  exit 1
fi
echo 'RUNTIME_APPLICATION_PATCH=none'

export CHROME_PATH="$(node -e "console.log(require('playwright').chromium.executablePath())")"
export NODE_PATH="${GITHUB_WORKSPACE}/functions/node_modules:${GITHUB_WORKSPACE}/node_modules"
export FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099
export FIREBASE_DATABASE_EMULATOR_HOST=127.0.0.1:9000
export FIREBASE_STORAGE_EMULATOR_HOST=127.0.0.1:9199
export GCLOUD_PROJECT=demo-kem-validation

run_suite() {
  local label="$1" timeout_s="$2" testfile="$3"
  echo "=== BEGIN ${label} ==="
  npx firebase emulators:exec --project demo-kem-validation --only auth,database,functions,hosting,storage --log-verbosity=INFO "node validation/seed.cjs && timeout ${timeout_s}s node ${testfile}"
  echo "=== PASS ${label} ==="
}

run_suite 'P2.6 TARGETED' 240 validation/p2_6_auth_account_targeted.cjs
run_suite 'P2.5 CART CHECKOUT 288' 240 /tmp/p2_5.cjs
run_suite 'P2.4 PRODUCT DETAIL 173' 180 /tmp/p2_4.cjs
run_suite 'P2.3 COLLECTION SHOP 196' 180 /tmp/p2_3.cjs
run_suite 'P2.2 HOMEPAGE 241' 160 validation/p2_2_homepage_targeted.cjs
run_suite 'P2.1 HEADER NAVIGATION 166' 130 /tmp/p2_1.cjs
run_suite 'P1 RECONCILIATION' 100 validation/p1_reconciliation_targeted.cjs
run_suite 'EMPLOYEE DASHBOARD SEVEN WIDTHS' 100 validation/dashboard_targeted.cjs
run_suite 'FULL P0 P1 INTEGRATION 79' 200 validation/smoke.cjs

echo 'ALL_BROWSER_GATES=green'
