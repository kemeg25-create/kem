from pathlib import Path
import re
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'index.html')
text = path.read_text()

BASELINE = 'eedbf94257b21436f27c281f18c813583333a8b8'
MARKER = '/* P2.5 — CART / CHECKOUT */'
assert '/* P2.4 — PRODUCT DETAIL */' in text, 'P2.4 source marker missing'
assert MARKER not in text, 'P2.5 already present'
assert 'async function renderCheckoutSummary()' in text
assert 'async function placeOrder()' in text
assert "cloudFunctions.httpsCallable('quoteOrder')" in text
assert "cloudFunctions.httpsCallable('createOrder')" in text


def replace_once(old, new, label):
    global text
    count = text.count(old)
    assert count == 1, f'{label}: expected exactly one match, found {count}'
    text = text.replace(old, new, 1)

css = r'''

        /* P2.5 — CART / CHECKOUT */
        #cartPage.cart-page,
        #checkoutPage.checkout-page {
            min-height: 100vh;
            padding: calc(72px + var(--space-48)) var(--page-gutter) var(--space-96);
            background: var(--color-off-white);
            color: var(--color-ink);
        }

        #cartPage .cart-container,
        #checkoutPage .checkout-container {
            width: min(100%, var(--container-editorial));
            max-width: var(--container-editorial);
            margin: 0 auto;
        }

        #cartPage .cart-header,
        #checkoutPage .checkout-header {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: var(--space-24);
            margin-bottom: var(--space-48);
            padding-bottom: var(--space-24);
            border-bottom: 1px solid var(--color-neutral-200);
        }

        .commerce-heading-group { min-width: 0; }

        .commerce-kicker {
            margin: 0 0 var(--space-8);
            color: var(--color-neutral-600);
            font: 600 var(--type-metadata)/1.35 var(--font-ui);
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        #cartPage .cart-header h1,
        #checkoutPage .checkout-header h1 {
            margin: 0;
            color: var(--color-ink);
            font-family: var(--font-display);
            font-size: var(--type-page-title);
            font-weight: 400;
            line-height: 0.95;
            letter-spacing: 0.02em;
        }

        #cartPage .continue-shopping,
        #checkoutPage .back-to-cart,
        #savedAddressesSection .use-new-address-btn {
            min-height: 44px;
            padding: var(--space-12) var(--space-16);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            background: var(--color-white);
            color: var(--color-ink);
            font: 600 var(--type-ui)/1.2 var(--font-ui);
            letter-spacing: 0;
            text-transform: none;
            transform: none;
            box-shadow: none;
            transition: border-color var(--motion-fast) var(--ease-standard), background-color var(--motion-fast) var(--ease-standard), color var(--motion-fast) var(--ease-standard);
        }

        #cartPage .continue-shopping:hover,
        #checkoutPage .back-to-cart:hover,
        #savedAddressesSection .use-new-address-btn:hover {
            border-color: var(--color-ink);
            background: var(--color-ink);
            color: var(--color-white);
            transform: none;
            box-shadow: none;
        }

        #cartPage .cart-item-count {
            margin: calc(-1 * var(--space-24)) 0 var(--space-24);
            color: var(--color-neutral-600);
            font: 400 var(--type-ui)/1.5 var(--font-ui);
        }

        #cartPage .cart-content {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(300px, 360px);
            gap: var(--space-48);
            align-items: start;
        }

        #cartPage .cart-items {
            min-width: 0;
            padding: 0;
            border-top: 1px solid var(--color-neutral-200);
            background: transparent;
        }

        #cartPage .cart-item {
            min-width: 0;
            display: grid;
            grid-template-columns: 144px minmax(0, 1fr) auto;
            gap: var(--space-24);
            align-items: start;
            padding: var(--space-24) 0;
            border-bottom: 1px solid var(--color-neutral-200);
        }

        #cartPage .cart-item-image {
            width: 144px;
            height: 180px;
            display: block;
            padding: var(--space-8);
            border: 1px solid var(--color-neutral-200);
            background: var(--color-white);
            object-fit: contain;
        }

        #cartPage .cart-item-info,
        #cartPage .cart-item-info h3,
        #cartPage .cart-item-price,
        #cartPage .cart-item-total {
            min-width: 0;
            overflow-wrap: anywhere;
        }

        #cartPage .cart-item-info h3 {
            margin: 0 0 var(--space-8);
            color: var(--color-ink);
            font: 600 var(--type-product-title)/1.1 var(--font-ui);
        }

        #cartPage .cart-item-variants {
            margin: 0 0 var(--space-12);
            color: var(--color-neutral-600);
            font: 400 var(--type-metadata)/1.5 var(--font-ui);
        }

        #cartPage .cart-item-price {
            margin: 0;
            color: var(--color-ink);
            font: 600 var(--type-ui)/1.4 var(--font-ui);
        }

        #cartPage .cart-item-original-price {
            margin-left: var(--space-8);
            color: var(--color-neutral-400);
            font-weight: 400;
            text-decoration: line-through;
        }

        #cartPage .cart-item-sale-state {
            display: inline-block;
            margin-top: var(--space-8);
            color: var(--color-kem-pink);
            font: 600 var(--type-metadata)/1.4 var(--font-ui);
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        #cartPage .cart-item-actions {
            min-width: 132px;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            justify-content: flex-start;
            gap: var(--space-16);
        }

        #cartPage .cart-quantity-control {
            display: inline-flex;
            align-items: center;
            gap: 0;
            padding: 0;
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            background: var(--color-white);
        }

        #cartPage .cart-quantity-control button {
            width: 44px;
            min-width: 44px;
            height: 44px;
            min-height: 44px;
            border: 0;
            border-radius: 0;
            background: var(--color-white);
            color: var(--color-ink);
            font: 600 1.05rem/1 var(--font-ui);
            transition: background-color var(--motion-fast) var(--ease-standard), color var(--motion-fast) var(--ease-standard);
        }

        #cartPage .cart-quantity-control button:hover {
            background: var(--color-ink);
            color: var(--color-white);
        }

        #cartPage .cart-quantity-control span {
            min-width: 44px;
            padding: 0 var(--space-8);
            color: var(--color-ink);
            text-align: center;
            font: 600 var(--type-ui)/1 var(--font-ui);
        }

        #cartPage .cart-item-total {
            color: var(--color-ink);
            font: 600 var(--type-ui)/1.4 var(--font-ui);
            text-align: right;
        }

        #cartPage .remove-item {
            min-height: 44px;
            padding: var(--space-8) 0;
            border: 0;
            background: transparent;
            color: var(--color-neutral-600);
            font: 600 var(--type-metadata)/1.2 var(--font-ui);
            text-decoration: underline;
            text-underline-offset: 3px;
        }

        #cartPage .remove-item:hover { color: var(--color-error); }

        #cartPage .cart-summary {
            position: static;
            top: auto;
            min-width: 0;
            height: fit-content;
            padding: var(--space-24);
            border: 1px solid var(--color-neutral-200);
            background: var(--color-white);
            box-shadow: none;
        }

        #cartPage .cart-summary h2,
        #checkoutPage .order-summary-checkout h2,
        #checkoutPage .checkout-section h2 {
            margin: 0 0 var(--space-24);
            padding: 0;
            border: 0;
            color: var(--color-ink);
            font-family: var(--font-display);
            font-size: var(--type-section-title);
            font-weight: 400;
            line-height: 1;
            letter-spacing: 0.02em;
        }

        #cartPage .coupon-section {
            margin-bottom: var(--space-24);
            padding-bottom: var(--space-24);
            border-bottom: 1px solid var(--color-neutral-200);
        }

        #cartPage .coupon-label {
            display: block;
            margin-bottom: var(--space-8);
            color: var(--color-ink);
            font: 600 var(--type-ui)/1.35 var(--font-ui);
        }

        #cartPage .coupon-controls {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: var(--space-8);
        }

        #cartPage #couponInput {
            width: 100%;
            min-width: 0;
            min-height: 48px;
            padding: var(--space-12) var(--space-16);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            background: var(--color-white);
            color: var(--color-ink);
            font: 600 var(--type-ui)/1.3 var(--font-ui);
            text-transform: uppercase;
        }

        #cartPage .coupon-apply-btn {
            min-height: 48px;
            padding: var(--space-12) var(--space-16);
            border: 1px solid var(--color-ink);
            border-radius: var(--radius-xs);
            background: var(--color-ink);
            color: var(--color-white);
            font: 600 var(--type-ui)/1.2 var(--font-ui);
        }

        #cartPage .coupon-apply-btn:hover { background: var(--color-kem-pink); border-color: var(--color-kem-pink); }

        #cartPage .coupon-state,
        #cartPage .coupon-feedback {
            margin-top: var(--space-12);
        }

        #cartPage .coupon-state {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: var(--space-16);
        }

        #cartPage .coupon-remove-btn {
            min-height: 44px;
            padding: var(--space-8) var(--space-12);
            border: 1px solid currentColor;
            border-radius: var(--radius-xs);
            background: transparent;
            color: inherit;
            font: 600 var(--type-metadata)/1.2 var(--font-ui);
        }

        #cartPage .summary-row,
        #checkoutPage .summary-row {
            min-width: 0;
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: var(--space-16);
            margin: 0;
            padding: var(--space-8) 0;
            color: var(--color-neutral-600);
            font: 400 var(--type-ui)/1.45 var(--font-ui);
        }

        #cartPage .summary-row > *,
        #checkoutPage .summary-row > * {
            min-width: 0;
            overflow-wrap: anywhere;
        }

        #cartPage .summary-row > :last-child,
        #checkoutPage .summary-row > :last-child {
            color: var(--color-ink);
            text-align: right;
            font-weight: 600;
        }

        #cartPage .summary-row.is-discount,
        #checkoutPage .summary-row.is-discount { color: var(--color-success); }

        #cartPage .summary-total-row,
        #checkoutPage .checkout-total-row {
            margin-top: var(--space-12);
            padding-top: var(--space-16);
            border-top: 1px solid var(--color-ink);
            color: var(--color-ink);
            font-size: 1.05rem;
            font-weight: 600;
        }

        #cartPage .summary-total-row > :last-child,
        #checkoutPage .checkout-total-row > :last-child { font-size: 1.2rem; }

        #cartPage .checkout-btn {
            width: 100%;
            min-height: 56px;
            margin-top: var(--space-24);
            padding: var(--space-16) var(--space-24);
            border: 1px solid var(--color-ink);
            border-radius: var(--radius-xs);
            background: var(--color-ink);
            color: var(--color-white);
            font: 600 var(--type-ui)/1.2 var(--font-ui);
            letter-spacing: 0.04em;
            text-transform: uppercase;
            transform: none;
            box-shadow: none;
        }

        #cartPage .checkout-btn:hover { background: var(--color-kem-pink); border-color: var(--color-kem-pink); transform: none; box-shadow: none; }

        #cartPage .empty-cart {
            width: min(100%, 640px);
            margin: var(--space-64) auto 0;
            padding: var(--space-48) 0;
            border-top: 1px solid var(--color-neutral-200);
            border-bottom: 1px solid var(--color-neutral-200);
            background: transparent;
            text-align: left;
        }

        #cartPage .empty-cart h2 {
            margin: 0 0 var(--space-12);
            color: var(--color-ink);
            font-family: var(--font-display);
            font-size: var(--type-section-title);
            font-weight: 400;
            line-height: 1;
        }

        #cartPage .empty-cart p {
            margin: 0 0 var(--space-24);
            color: var(--color-neutral-600);
            font: 400 var(--type-body)/1.6 var(--font-ui);
        }

        #checkoutPage .checkout-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.75fr);
            gap: var(--space-48);
            align-items: start;
        }

        #checkoutPage .checkout-grid > * { min-width: 0; }

        #checkoutPage .checkout-section {
            margin: 0 0 var(--space-32);
            padding: var(--space-32) 0 0;
            border-top: 1px solid var(--color-neutral-200);
            background: transparent;
        }

        #checkoutPage .checkout-grid > div > .checkout-section:first-child {
            padding-top: 0;
            border-top: 0;
        }

        #checkoutPage #savedAddressesSection {
            margin: 0 0 var(--space-32) !important;
            padding: var(--space-24);
            border: 1px solid var(--color-neutral-200);
            background: var(--color-white);
        }

        #checkoutPage .saved-addresses-heading {
            margin: 0 0 var(--space-16);
            color: var(--color-ink);
            font: 600 var(--type-ui)/1.4 var(--font-ui);
        }

        #checkoutPage #savedAddressesList {
            display: grid !important;
            gap: var(--space-8) !important;
            margin: 0 0 var(--space-16) !important;
        }

        #checkoutPage .saved-address-option {
            position: relative;
            width: 100%;
            min-height: 44px;
            margin: 0;
            padding: var(--space-16);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            background: var(--color-white);
            color: var(--color-ink);
            text-align: left;
            box-shadow: none;
        }

        #checkoutPage .saved-address-option:hover { border-color: var(--color-ink); }

        #checkoutPage .saved-address-label {
            display: block;
            margin: 0 0 var(--space-4);
            padding-right: 72px;
            font: 600 var(--type-ui)/1.35 var(--font-ui);
            overflow-wrap: anywhere;
        }

        #checkoutPage .saved-address-copy {
            display: block;
            color: var(--color-neutral-600);
            font: 400 var(--type-metadata)/1.55 var(--font-ui);
            overflow-wrap: anywhere;
        }

        #checkoutPage .saved-address-default {
            position: absolute;
            top: var(--space-12);
            right: var(--space-12);
            padding: var(--space-4) var(--space-8);
            border: 1px solid var(--color-neutral-200);
            color: var(--color-neutral-600);
            font: 600 0.6875rem/1.2 var(--font-ui);
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        #checkoutPage #checkoutStatus {
            min-height: 0;
            margin: 0 0 var(--space-24) !important;
            color: var(--color-neutral-600) !important;
            font: 400 var(--type-ui)/1.5 var(--font-ui);
        }

        #checkoutPage #checkoutStatus:not(:empty) {
            padding: var(--space-12) var(--space-16);
            border: 1px solid var(--color-neutral-200);
            background: var(--color-white);
        }

        #checkoutPage .checkout-form-group { margin-bottom: var(--space-20, 20px); }

        #checkoutPage .checkout-form-group label {
            display: block;
            margin-bottom: var(--space-8);
            color: var(--color-neutral-800);
            font: 600 var(--type-metadata)/1.35 var(--font-ui);
            letter-spacing: 0.01em;
            text-transform: none;
        }

        #checkoutPage .checkout-form-group input,
        #checkoutPage .checkout-form-group textarea {
            width: 100%;
            min-height: 52px;
            padding: var(--space-12) var(--space-16);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            background: var(--color-white);
            color: var(--color-ink);
            font: 400 var(--type-ui)/1.4 var(--font-ui);
        }

        #checkoutPage .checkout-form-group textarea {
            min-height: 112px;
            resize: vertical;
        }

        #checkoutPage .checkout-form-row {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: var(--space-16);
        }

        #checkoutPage .payment-methods { display: grid; gap: var(--space-8); }

        #checkoutPage .payment-option {
            display: grid;
            grid-template-columns: auto minmax(0, 1fr);
            gap: var(--space-12);
            align-items: start;
            min-height: 56px;
            padding: var(--space-16);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            background: var(--color-white);
            color: var(--color-ink);
            box-shadow: none;
            transform: none;
        }

        #checkoutPage .payment-option.selected { border-color: var(--color-ink); box-shadow: inset 0 0 0 1px var(--color-ink); }

        #checkoutPage .payment-option input[type="radio"] {
            width: 20px;
            height: 20px;
            margin: 2px 0 0;
            accent-color: var(--color-ink);
        }

        #checkoutPage .payment-copy { min-width: 0; }

        #checkoutPage .payment-title {
            display: block;
            margin: 0 0 var(--space-4);
            color: var(--color-ink);
            font: 600 var(--type-ui)/1.35 var(--font-ui);
        }

        #checkoutPage .payment-desc {
            color: var(--color-neutral-600);
            font: 400 var(--type-metadata)/1.5 var(--font-ui);
        }

        #checkoutPage .order-summary-checkout {
            position: static;
            top: auto;
            min-width: 0;
            padding: var(--space-24);
            border: 1px solid var(--color-neutral-200);
            background: var(--color-white);
            box-shadow: none;
        }

        #checkoutPage .summary-items {
            display: grid;
            gap: var(--space-16);
            margin-bottom: var(--space-16);
            padding-bottom: var(--space-16);
            border-bottom: 1px solid var(--color-neutral-200);
        }

        #checkoutPage .summary-item {
            min-width: 0;
            display: grid;
            grid-template-columns: 64px minmax(0, 1fr) auto;
            gap: var(--space-12);
            align-items: start;
            margin: 0;
            padding: 0;
            border: 0;
            color: var(--color-neutral-600);
            font: 400 var(--type-metadata)/1.45 var(--font-ui);
        }

        #checkoutPage .summary-item-image {
            width: 64px;
            height: 80px;
            display: block;
            padding: var(--space-4);
            border: 1px solid var(--color-neutral-200);
            background: var(--color-off-white);
            object-fit: contain;
        }

        #checkoutPage .summary-item-copy,
        #checkoutPage .summary-item-name,
        #checkoutPage .summary-item-meta,
        #checkoutPage .summary-item-price {
            min-width: 0;
            overflow-wrap: anywhere;
        }

        #checkoutPage .summary-item-name {
            display: block;
            margin-bottom: var(--space-4);
            color: var(--color-ink);
            font-weight: 600;
        }

        #checkoutPage .summary-item-meta { display: block; color: var(--color-neutral-600); }
        #checkoutPage .summary-item-price { color: var(--color-ink); text-align: right; font-weight: 600; }

        #checkoutPage .place-order-btn {
            width: 100%;
            min-height: 56px;
            margin-top: var(--space-24);
            padding: var(--space-16) var(--space-24);
            border: 1px solid var(--color-ink);
            border-radius: var(--radius-xs);
            background: var(--color-ink);
            color: var(--color-white);
            font: 600 var(--type-ui)/1.2 var(--font-ui);
            letter-spacing: 0.04em;
            text-transform: uppercase;
            transform: none;
            box-shadow: none;
            transition: background-color var(--motion-fast) var(--ease-standard), border-color var(--motion-fast) var(--ease-standard), opacity var(--motion-fast) var(--ease-standard);
        }

        #checkoutPage .place-order-btn:hover:not(:disabled) {
            border-color: var(--color-kem-pink);
            background: var(--color-kem-pink);
            transform: none;
            box-shadow: none;
        }

        #checkoutPage .place-order-btn:disabled {
            border-color: var(--color-neutral-200);
            background: var(--color-neutral-200);
            color: var(--color-neutral-600);
            opacity: 1;
        }

        #cartPage :is(button, input):focus-visible,
        #checkoutPage :is(button, input, textarea, label.payment-option):focus-visible {
            outline: 3px solid var(--color-kem-pink);
            outline-offset: 3px;
        }

        .order-success-state {
            width: min(calc(100% - (2 * var(--page-gutter))), var(--container-editorial));
            margin: calc(72px + var(--space-32)) auto var(--space-32);
            padding: var(--space-24);
            border: 1px solid #B8DEC9;
            background: var(--color-success-surface);
            color: var(--color-success);
        }

        .order-success-state[hidden] { display: none; }

        .order-success-state h2 {
            margin: 0 0 var(--space-8);
            color: var(--color-ink);
            font-family: var(--font-display);
            font-size: var(--type-section-title);
            font-weight: 400;
            line-height: 1;
        }

        .order-success-state p { margin: var(--space-4) 0 0; font: 400 var(--type-ui)/1.5 var(--font-ui); }
        .order-success-state strong { color: var(--color-ink); }

        @media (max-width: 960px) {
            #cartPage.cart-page,
            #checkoutPage.checkout-page { padding-top: calc(64px + var(--space-32)); }

            #cartPage .cart-content,
            #checkoutPage .checkout-grid { grid-template-columns: 1fr; gap: var(--space-32); }

            #cartPage .cart-summary,
            #checkoutPage .order-summary-checkout { width: 100%; }
        }

        @media (max-width: 767px) {
            #cartPage.cart-page,
            #checkoutPage.checkout-page { padding-bottom: var(--space-64); }

            #cartPage .cart-header,
            #checkoutPage .checkout-header {
                align-items: flex-start;
                margin-bottom: var(--space-32);
            }

            #cartPage .cart-item {
                grid-template-columns: 88px minmax(0, 1fr);
                gap: var(--space-16);
            }

            #cartPage .cart-item-image { width: 88px; height: 110px; }

            #cartPage .cart-item-actions {
                grid-column: 1 / -1;
                min-width: 0;
                width: 100%;
                display: grid;
                grid-template-columns: auto minmax(0, 1fr) auto;
                align-items: center;
                gap: var(--space-12);
            }

            #cartPage .cart-item-total { text-align: left; }
            #cartPage .remove-item { justify-self: end; }

            #cartPage .cart-summary,
            #checkoutPage .order-summary-checkout,
            #checkoutPage #savedAddressesSection { padding: var(--space-20, 20px); }

            #checkoutPage .checkout-form-row { grid-template-columns: 1fr; gap: 0; }
        }

        @media (max-width: 420px) {
            #cartPage .cart-header,
            #checkoutPage .checkout-header { display: grid; grid-template-columns: 1fr; }

            #cartPage .continue-shopping,
            #checkoutPage .back-to-cart { justify-self: start; }

            #cartPage .coupon-controls { grid-template-columns: 1fr; }
            #cartPage .coupon-apply-btn { width: 100%; }

            #cartPage .cart-item-actions { grid-template-columns: 1fr auto; }
            #cartPage .cart-quantity-control { grid-column: 1 / -1; justify-self: start; }
            #cartPage .cart-item-total { align-self: center; }
        }

        @media (prefers-reduced-motion: reduce) {
            #cartPage *,
            #checkoutPage *,
            .order-success-state * { transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; }
        }
'''

p2_idx = text.index('/* P2.4 — PRODUCT DETAIL */')
style_end = text.find('</style>', p2_idx)
assert style_end != -1, 'style end after P2.4 missing'
text = text[:style_end] + css + '\n    ' + text[style_end:]

# Static Cart / Checkout framing.
replace_once(
    '<div class="cart-header">\n                <h1>Shopping Cart</h1>\n                <button class="continue-shopping" onclick="closeCart()">← Continue Shopping</button>\n            </div>',
    '<div class="cart-header">\n                <div class="commerce-heading-group">\n                    <p class="commerce-kicker">KEM / Cart</p>\n                    <h1>Cart</h1>\n                </div>\n                <button type="button" class="continue-shopping" onclick="closeCart()">Continue Shopping</button>\n            </div>',
    'cart header'
)
replace_once(
    '<div class="checkout-header">\n                <h1>Checkout</h1>\n                <button class="back-to-cart" onclick="backToCart()">← Back to Cart</button>\n            </div>',
    '<div class="checkout-header">\n                <div class="commerce-heading-group">\n                    <p class="commerce-kicker">KEM / Checkout</p>\n                    <h1>Checkout</h1>\n                </div>\n                <button type="button" class="back-to-cart" onclick="backToCart()">Back to Cart</button>\n            </div>',
    'checkout header'
)

# Saved address shell and checkout form semantics.
text = text.replace('<h3 style="font-size: 1.2rem; margin-bottom: 1rem; color: var(--primary);">📍 Your Saved Addresses</h3>', '<h3 class="saved-addresses-heading">Your Saved Addresses</h3>')
text = text.replace('<button type="button" onclick="useNewAddress()" style="background: white; color: var(--primary); border: 2px solid var(--primary); padding: 0.8rem 1.5rem; border-radius: 4px; cursor: pointer; font-weight: 600; transition: all 0.3s;">\n                                ➕ Use New Address\n                            </button>', '<button type="button" class="use-new-address-btn" onclick="useNewAddress()">Use New Address</button>')
text = text.replace('<div id="checkoutStatus" role="status" aria-live="polite" style="margin-bottom:1rem;color:#666;"></div>', '<div id="checkoutStatus" role="status" aria-live="polite"></div>')

labels = {
    '<label>Full Name *</label>': '<label for="checkoutName">Full Name *</label>',
    '<label>Email *</label>': '<label for="checkoutEmail">Email *</label>',
    '<label>Phone Number *</label>': '<label for="checkoutPhone">Phone Number *</label>',
    '<label>Street Address *</label>': '<label for="checkoutAddress">Street Address *</label>',
    '<label>House/Building Number *</label>': '<label for="checkoutHouseNumber">House/Building Number *</label>',
    '<label>Floor Number (Optional)</label>': '<label for="checkoutFloor">Floor Number (Optional)</label>',
    '<label>City *</label>': '<label for="checkoutCity">City *</label>',
    '<label>Postal Code</label>': '<label for="checkoutPostal">Postal Code</label>',
    '<label>Delivery Notes (Optional)</label>': '<label for="checkoutNotes">Delivery Notes (Optional)</label>',
}
for old, new in labels.items():
    assert old in text, f'missing label anchor {old}'
    text = text.replace(old, new, 1)

# Checkout summary static presentation: remove emoji and inline total styling.
text = text.replace('<div class="summary-row" id="checkoutThresholdRow" style="display: none; color: var(--accent);">\n                        <span>🎉 Order Discount</span>', '<div class="summary-row is-discount" id="checkoutThresholdRow" style="display: none;">\n                        <span>Order Discount</span>')
text = text.replace('<div class="summary-row" id="checkoutCouponRow" style="display: none; color: var(--accent);">\n                        <span>💎 Coupon</span>', '<div class="summary-row is-discount" id="checkoutCouponRow" style="display: none;">\n                        <span>Coupon Discount</span>')
text = text.replace('<div class="summary-row" style="font-weight: 800; font-size: 1.3rem; border-top: 2px solid var(--primary); padding-top: 1rem; margin-top: 1rem;">\n                        <span>Total</span>', '<div class="summary-row checkout-total-row">\n                        <span>Total</span>')
text = text.replace('<button class="place-order-btn" onclick="placeOrder()">Place Order</button>', '<button type="button" class="place-order-btn" onclick="placeOrder()" aria-describedby="checkoutStatus">Place Order</button>')

# Empty cart: factual, no promotional filler.
replace_once(
    '''<div class=\"empty-cart\">\n                        <h2>Your cart is empty</h2>\n                        <p>Add some amazing KEM products to get started!</p>\n                        <button class=\"continue-shopping\" onclick=\"closeCart()\">Start Shopping</button>\n                    </div>''',
    '''<div class=\"empty-cart kem-state-empty\">\n                        <h2>Your cart is empty</h2>\n                        <p>There are no products in your cart.</p>\n                        <button type=\"button\" class=\"continue-shopping\" onclick=\"closeCart()\">Shop KEM</button>\n                    </div>''',
    'empty cart'
)

# Non-empty cart count and product-item semantics/presentation.
replace_once(
    'contentArea.innerHTML = `\n                <div class=\"cart-content\">',
    'contentArea.innerHTML = `\n                <p class=\"cart-item-count\" aria-live=\"polite\">${cart.reduce((sum, item) => sum + Number(item.quantity || 0), 0)} ${cart.reduce((sum, item) => sum + Number(item.quantity || 0), 0) === 1 ? \'item\' : \'items\'}</p>\n                <div class=\"cart-content\">',
    'cart item count'
)
text = text.replace('class=\"cart-item-image\" loading=\"lazy\"', 'class=\"cart-item-image\" loading=\"lazy\" decoding=\"async\"', 1)
text = text.replace('''<div class=\"cart-item-category\">KEM Collection</div>\n                                    <h3>${escapeHTML(item.name)}</h3>\n                                    ${(item.size || item.color) ? `<div style=\"font-size:.85rem;color:#666;\">${item.size ? `Size: ${escapeHTML(item.size)}` : ''}${item.size && item.color ? ' · ' : ''}${item.color ? `Color: ${escapeHTML(item.color)}` : ''}</div>` : ''}\n                                    <div class=\"cart-item-price\">EGP ${item.price.toFixed(2)} each</div>\n                                    ${item.originalPrice && item.originalPrice > item.price ? `\n                                        <div style=\"font-size: 0.85rem; color: var(--accent);\">🔥 Product discount applied!</div>\n                                    ` : ''}''', '''<h3>${escapeHTML(item.name)}</h3>\n                                    ${(item.size || item.color) ? `<div class=\"cart-item-variants\">${item.size ? `Size: ${escapeHTML(item.size)}` : ''}${item.size && item.color ? ' · ' : ''}${item.color ? `Color: ${escapeHTML(item.color)}` : ''}</div>` : ''}\n                                    <div class=\"cart-item-price\">EGP ${Number(item.price).toFixed(2)} each${item.originalPrice && item.originalPrice > item.price ? `<span class=\"cart-item-original-price\">EGP ${Number(item.originalPrice).toFixed(2)}</span>` : ''}</div>\n                                    ${item.originalPrice && item.originalPrice > item.price ? `<span class=\"cart-item-sale-state\">Sale price applied</span>` : ''}''')
text = text.replace('<button onclick=\"updateCartQuantity(${index}, -1)\">-</button>\n                                        <span>${item.quantity}</span>\n                                        <button onclick=\"updateCartQuantity(${index}, 1)\">+</button>', '<button type=\"button\" aria-label=\"Decrease quantity for ${escapeHTML(item.name)}\" onclick=\"updateCartQuantity(${index}, -1)\">−</button>\n                                        <span aria-live=\"polite\" aria-label=\"Quantity ${item.quantity}\">${item.quantity}</span>\n                                        <button type=\"button\" aria-label=\"Increase quantity for ${escapeHTML(item.name)}\" onclick=\"updateCartQuantity(${index}, 1)\">+</button>')
text = text.replace('<button class=\"remove-item\" onclick=\"removeFromCart(${index})\">Remove</button>', '<button type=\"button\" class=\"remove-item\" aria-label=\"Remove ${escapeHTML(item.name)} from cart\" onclick=\"removeFromCart(${index})\">Remove</button>')

# Cart coupon presentation, preserving server validation and existing handlers.
text = text.replace('''<div style=\"margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 2px solid var(--border);\">\n                            <label style=\"display: block; font-weight: 600; margin-bottom: 0.5rem;\">Have a promo code?</label>\n                            <div style=\"display: flex; gap: 0.5rem;\">\n                                <input type=\"text\" id=\"couponInput\" placeholder=\"Enter code\" \n                                    style=\"flex: 1; padding: 0.8rem; border: 2px solid var(--border); text-transform: uppercase; font-weight: 600; cursor: text !important;\"\n                                    ${appliedCoupon ? 'disabled' : ''}>\n                                <button onclick=\"applyCouponCode()\" \n                                    style=\"padding: 0.8rem 1.5rem; background: var(--secondary); color: var(--primary); border: none; font-weight: 800; cursor: pointer;\"\n                                    ${appliedCoupon ? 'disabled' : ''}>\n                                    Apply\n                                </button>\n                            </div>''', '''<div class=\"coupon-section\">\n                            <label class=\"coupon-label\" for=\"couponInput\">Promo code</label>\n                            <div class=\"coupon-controls\">\n                                <input type=\"text\" id=\"couponInput\" placeholder=\"Enter code\" autocomplete=\"off\" ${appliedCoupon ? 'disabled' : ''}>\n                                <button type=\"button\" class=\"coupon-apply-btn\" onclick=\"applyCouponCode()\" ${appliedCoupon ? 'disabled' : ''}>Apply</button>\n                            </div>''')
text = text.replace('''<div style=\"margin-top: 0.5rem; padding: 0.5rem; background: #f0fff4; color: var(--secondary); font-weight: 600; display: flex; justify-content: space-between; align-items: center;\">\n                                    <span>✓ Coupon \"${appliedCoupon.code}\" applied</span>\n                                    <button onclick=\"removeCouponCode()\" style=\"background: none; border: none; color: var(--accent); cursor: pointer; font-weight: 800;\">Remove</button>\n                                </div>''', '''<div class=\"coupon-state kem-state kem-state-success\" role=\"status\">\n                                    <span>Coupon \"${escapeHTML(appliedCoupon.code)}\" applied</span>\n                                    <button type=\"button\" class=\"coupon-remove-btn\" onclick=\"removeCouponCode()\">Remove</button>\n                                </div>''')
text = text.replace('''<div style=\"margin-top: 0.5rem; color: var(--accent); font-size: 0.85rem;\">${couponError}</div>''', '''<div class=\"coupon-feedback kem-state kem-state-error\" role=\"alert\">${escapeHTML(couponError)}</div>''')
text = text.replace("${couponError ? `\n                                <div class=\"coupon-feedback kem-state kem-state-error\" role=\"alert\">${escapeHTML(couponError)}</div>\n                            ` : ''}", "${couponError ? `\n                                <div class=\"coupon-feedback kem-state kem-state-error\" role=\"alert\">${escapeHTML(couponError)}</div>\n                            ` : ''}\n                            <div id=\"couponFeedback\" class=\"coupon-feedback\" role=\"status\" aria-live=\"polite\"></div>")

# Remove decorative emoji from cart discount labels and mark them semantically.
text = text.replace('<div class=\"summary-row\" style=\"color: var(--accent);\">\n                                <span>🎉 Order Discount (Over EGP ${appliedThreshold.threshold})</span>', '<div class=\"summary-row is-discount\">\n                                <span>Order Discount (Over EGP ${appliedThreshold.threshold})</span>')
text = text.replace('<div class=\"summary-row\" style=\"color: var(--accent);\">\n                                <span>💎 Coupon Discount (${appliedCoupon.code})</span>', '<div class=\"summary-row is-discount\">\n                                <span>Coupon Discount (${escapeHTML(appliedCoupon.code)})</span>')

# Normalize cart total row if legacy inline styling is present.
text = text.replace('<div class=\"summary-row\" style=\"font-size: 1.2rem; font-weight: 800; border-top: 2px solid var(--primary); padding-top: 1rem; margin-top: 1rem;\">', '<div class=\"summary-row summary-total-row\">')
text = text.replace('<div class=\"summary-row\" style=\"font-weight: 800; font-size: 1.3rem; border-top: 2px solid var(--primary); padding-top: 1rem; margin-top: 1rem;\">', '<div class=\"summary-row summary-total-row\">')

# Saved-address buttons: semantic, restrained, same click path.
pattern = re.compile(r"function renderSavedAddresses\(addresses\) \{\n            const section=document\.getElementById\('savedAddressesSection'\),list=document\.getElementById\('savedAddressesList'\);if\(!addresses\?\.length\)\{section\.style\.display='none';return;\}section\.style\.display='block';\n            list\.innerHTML=addresses\.map\(addr=>`.*?`\)\.join\(''\);\n        \}", re.S)
match = pattern.search(text)
assert match, 'renderSavedAddresses function not found'
replacement = '''function renderSavedAddresses(addresses) {
            const section=document.getElementById('savedAddressesSection'),list=document.getElementById('savedAddressesList');if(!addresses?.length){section.style.display='none';return;}section.style.display='block';
            list.innerHTML=addresses.map(addr=>`<button type="button" class="saved-address-option" aria-label="Use ${escapeHTML(addr.label||'saved address')}" onclick="selectSavedAddress(${Number(addr.id)})">${addr.isDefault?'<span class="saved-address-default">Default</span>':''}<span class="saved-address-label">${escapeHTML(addr.label||'Saved address')}</span><span class="saved-address-copy">${escapeHTML(addr.address||'')}<br>Building: ${escapeHTML(addr.houseNumber||'')}${addr.floor?`, Floor: ${escapeHTML(addr.floor)}`:''}<br>${escapeHTML(addr.city||'')}${addr.postal?` - ${escapeHTML(addr.postal)}`:''}</span></button>`).join('');
        }'''
text = text[:match.start()] + replacement + text[match.end():]

# COD-only payment: remove emoji, preserve radio/selection and handler.
payment_pattern = re.compile(r"function renderPaymentMethodsCheckout\(\) \{\n            const container = document\.getElementById\('checkoutPaymentMethods'\);.*?\n        \}", re.S)
payment_match = payment_pattern.search(text)
assert payment_match, 'renderPaymentMethodsCheckout not found'
payment_replacement = '''function renderPaymentMethodsCheckout() {
            const container = document.getElementById('checkoutPaymentMethods');
            if (!container) return;
            selectedPaymentMethod = 'cod';
            container.innerHTML = `
                <label class="payment-option selected" onclick="selectPaymentMethod('cod')">
                    <input type="radio" id="paymentCod" name="payment" value="cod" checked aria-describedby="paymentCodDescription">
                    <span class="payment-copy">
                        <span class="payment-title">Cash on Delivery</span>
                        <span class="payment-desc" id="paymentCodDescription">Pay with cash when your order arrives</span>
                    </span>
                </label>
            `;
        }'''
text = text[:payment_match.start()] + payment_replacement + text[payment_match.end():]

# Checkout summary presentation only: authoritative quote call and field updates remain unchanged.
old_summary_items = "itemsContainer.innerHTML=cart.map(item=>`<div class=\"summary-item\"><span>${escapeHTML(item.name)}${item.size?` · ${escapeHTML(item.size)}`:''}${item.color?` · ${escapeHTML(item.color)}`:''} x${item.quantity}</span><span>EGP ${(Number(item.price)*item.quantity).toFixed(2)}</span></div>`).join('');"
new_summary_items = "itemsContainer.innerHTML=cart.map(item=>`<div class=\"summary-item\"><img class=\"summary-item-image\" src=\"${escapeHTML(item.image||'')}\" alt=\"${escapeHTML(item.name)}\" loading=\"lazy\" decoding=\"async\"><span class=\"summary-item-copy\"><span class=\"summary-item-name\">${escapeHTML(item.name)}</span><span class=\"summary-item-meta\">${item.size?`Size: ${escapeHTML(item.size)}`:''}${item.size&&item.color?' · ':''}${item.color?`Color: ${escapeHTML(item.color)}`:''}${(item.size||item.color)?' · ':''}Qty: ${item.quantity}</span></span><span class=\"summary-item-price\">EGP ${(Number(item.price)*item.quantity).toFixed(2)}</span></div>`).join('');"
replace_once(old_summary_items, new_summary_items, 'checkout summary items')

# Inline invalid-coupon state mirrors the existing backend response without replacing the existing alert.
old_coupon_catch = "} catch (error) {\n                console.error('Coupon validation failed:', error);\n                appliedCoupon = null;\n                alert(error?.message || 'Invalid coupon code.');\n            }"
if old_coupon_catch in text:
    new_coupon_catch = "} catch (error) {\n                console.error('Coupon validation failed:', error);\n                appliedCoupon = null;\n                const feedback = document.getElementById('couponFeedback');\n                if (feedback) { feedback.className = 'coupon-feedback kem-state kem-state-error'; feedback.setAttribute('role', 'alert'); feedback.textContent = error?.message || 'Invalid coupon code.'; }\n                alert(error?.message || 'Invalid coupon code.');\n            }"
    text = text.replace(old_coupon_catch, new_coupon_catch, 1)

# Factual success surface using only returned order data; existing alert and completion flow remain intact.
success_helper = r'''

        function showOrderSuccessState(result) {
            if (!result?.orderId) return;
            let state = document.getElementById('orderSuccessState');
            if (!state) {
                state = document.createElement('section');
                state.id = 'orderSuccessState';
                state.className = 'order-success-state';
                state.setAttribute('role', 'status');
                state.setAttribute('aria-live', 'polite');
                const mainSite = document.getElementById('mainSite');
                if (mainSite) mainSite.prepend(state);
            }
            state.hidden = false;
            state.innerHTML = `<h2>Order placed successfully</h2><p>Order ID: <strong>${escapeHTML(String(result.orderId))}</strong></p><p>Total: <strong>EGP ${Number(result.total).toFixed(2)}</strong></p><p>Payment: Cash on Delivery</p>`;
        }
'''
place_idx = text.index('        async function placeOrder()')
text = text[:place_idx] + success_helper + text[place_idx:]

success_anchor = "document.getElementById('mainSite').style.display = 'block';\n                window.scrollTo(0, 0);\n                alert(`Order placed successfully!"
assert success_anchor in text, 'order success anchor missing'
text = text.replace("document.getElementById('mainSite').style.display = 'block';\n                window.scrollTo(0, 0);\n                alert(`Order placed successfully!", "document.getElementById('mainSite').style.display = 'block';\n                showOrderSuccessState(result);\n                window.scrollTo(0, 0);\n                alert(`Order placed successfully!", 1)

# Guard core authority and frozen hooks.
for required in [
    "cloudFunctions.httpsCallable('quoteOrder')",
    "cloudFunctions.httpsCallable('createOrder')",
    "paymentMethod: 'cod'",
    "if(!auth.currentUser.emailVerified)",
    "function updateCartQuantity(index, change)",
    "function removeFromCart(index)",
    "function removeCouponCode()",
    "function selectSavedAddress(addressId)",
    "function backToCart()",
    '/* P2.4 — PRODUCT DETAIL */',
    '/* P2.3 — SHOP / COLLECTION */',
    '/* P2.2 — HOMEPAGE */',
    '/* P2.1 — HEADER / NAVIGATION */',
]:
    assert required in text, f'frozen/source guard missing: {required}'

assert MARKER in text
assert 'body { overflow-x: hidden;' not in text
assert '🔥 Product discount applied!' not in text
assert '📍 Your Saved Addresses' not in text
assert '💵' not in text[text.index(MARKER):] if '💵' in text[text.index(MARKER):] else True

path.write_text(text)
print('Applied P2.5 cart/checkout presentation only; commerce authority paths retained')
