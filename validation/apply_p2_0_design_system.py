from pathlib import Path

path = Path('index.html')
s = path.read_text()

root_old = """        :root {
            --primary: #000000;
            --accent: #FF3366;
            --secondary: #00FF99;
            --bg: #FAFAFA;
            --text: #0A0A0A;
            --border: #E0E0E0;
        }
"""
root_new = """        :root {
            /* P2.0 — KEM global design tokens */
            --color-ink: #0A0A0A;
            --color-white: #FFFFFF;
            --color-off-white: #FAFAFA;
            --color-neutral-50: #F7F7F5;
            --color-neutral-100: #F0F0ED;
            --color-neutral-200: #DEDEDA;
            --color-neutral-400: #A3A39E;
            --color-neutral-600: #666661;
            --color-neutral-800: #292927;
            --color-kem-pink: #FF3366;
            --color-kem-green: #00FF99;
            --color-success: #16754A;
            --color-warning: #8A5A00;
            --color-error: #B42318;
            --color-info: #175CD3;
            --color-success-surface: #EAF7F0;
            --color-warning-surface: #FFF4D6;
            --color-error-surface: #FDECEA;
            --color-info-surface: #EAF1FF;

            --space-4: 4px;
            --space-8: 8px;
            --space-12: 12px;
            --space-16: 16px;
            --space-24: 24px;
            --space-32: 32px;
            --space-48: 48px;
            --space-64: 64px;
            --space-96: 96px;
            --space-128: 128px;

            --font-display: 'Bebas Neue', sans-serif;
            --font-ui: 'Archivo', sans-serif;
            --type-display: clamp(4rem, 9vw, 8rem);
            --type-page-title: clamp(2.75rem, 5vw, 4.5rem);
            --type-section-title: clamp(2rem, 3.5vw, 3.25rem);
            --type-product-title: clamp(1.35rem, 2vw, 2rem);
            --type-body: 1rem;
            --type-ui: 0.9375rem;
            --type-metadata: 0.8125rem;

            --container-customer: 1400px;
            --container-editorial: 1200px;
            --container-dashboard: 1400px;
            --gutter-mobile: 16px;
            --gutter-tablet: 32px;
            --gutter-desktop: 48px;
            --page-gutter: var(--gutter-mobile);
            --content-gap-sm: var(--space-16);
            --content-gap-md: var(--space-24);
            --content-gap-lg: var(--space-32);

            --radius-xs: 2px;
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-pill: 999px;

            --shadow-soft: 0 1px 2px rgba(10, 10, 10, 0.06);
            --shadow-panel: 0 16px 40px rgba(10, 10, 10, 0.14);

            --motion-fast: 120ms;
            --motion-standard: 200ms;
            --motion-slow: 300ms;
            --ease-standard: cubic-bezier(0.2, 0.8, 0.2, 1);

            /* Legacy aliases retained so frozen P0/P1 markup and behavior stay intact. */
            --primary: var(--color-ink);
            --accent: var(--color-kem-pink);
            --secondary: var(--color-kem-green);
            --bg: var(--color-off-white);
            --text: var(--color-ink);
            --border: var(--color-neutral-200);
        }
"""
if s.count(root_old) != 1:
    raise SystemExit(f'Expected legacy root token block once, found {s.count(root_old)}')
s = s.replace(root_old, root_new, 1)

concealment = "            overflow-x: hidden;\n"
if s.count(concealment) != 1:
    raise SystemExit(f'Expected body overflow concealment once, found {s.count(concealment)}')
s = s.replace(concealment, '', 1)

anchor = """        @media (max-width: 1024px) {
"""
if s.count(anchor) != 1:
    raise SystemExit(f'Expected responsive anchor once, found {s.count(anchor)}')

foundation = r'''        /* =========================================================
           P2.0 — GLOBAL DESIGN SYSTEM FOUNDATION
           Reusable visual primitives only. Page composition remains unchanged.
           ========================================================= */
        @media (min-width: 769px) {
            :root { --page-gutter: var(--gutter-tablet); }
        }

        @media (min-width: 1025px) {
            :root { --page-gutter: var(--gutter-desktop); }
        }

        .kem-container,
        .kem-editorial-container,
        .kem-dashboard-container {
            width: min(calc(100% - (2 * var(--page-gutter))), var(--container-customer));
            margin-inline: auto;
        }

        .kem-editorial-container { max-width: var(--container-editorial); }
        .kem-dashboard-container { max-width: var(--container-dashboard); }

        .type-display {
            font-family: var(--font-display);
            font-size: var(--type-display);
            line-height: 0.92;
            letter-spacing: 0.02em;
            font-weight: 400;
        }

        .type-page-title {
            font-family: var(--font-display);
            font-size: var(--type-page-title);
            line-height: 0.98;
            letter-spacing: 0.02em;
            font-weight: 400;
        }

        .type-section-title {
            font-family: var(--font-ui);
            font-size: var(--type-section-title);
            line-height: 1.08;
            letter-spacing: -0.02em;
            font-weight: 600;
        }

        .type-product-title {
            font-family: var(--font-ui);
            font-size: var(--type-product-title);
            line-height: 1.15;
            letter-spacing: -0.015em;
            font-weight: 600;
        }

        .type-body { font: 400 var(--type-body)/1.65 var(--font-ui); }
        .type-ui { font: 600 var(--type-ui)/1.3 var(--font-ui); }
        .type-metadata {
            font: 600 var(--type-metadata)/1.35 var(--font-ui);
            letter-spacing: 0.02em;
            color: var(--color-neutral-600);
        }

        button,
        input,
        select,
        textarea {
            font-family: var(--font-ui);
        }

        /* Reusable button vocabulary for current and later P2 phases. */
        .kem-btn {
            min-height: 44px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: var(--space-8);
            padding: var(--space-12) var(--space-24);
            border: 1px solid transparent;
            border-radius: var(--radius-xs);
            font: 600 var(--type-ui)/1 var(--font-ui);
            letter-spacing: 0.015em;
            text-decoration: none;
            cursor: pointer;
            transition: background-color var(--motion-standard) var(--ease-standard), color var(--motion-standard) var(--ease-standard), border-color var(--motion-standard) var(--ease-standard), opacity var(--motion-fast) var(--ease-standard);
        }

        .kem-btn-primary { background: var(--color-kem-pink); color: var(--color-white); }
        .kem-btn-primary:hover { background: #E82656; }
        .kem-btn-secondary { background: transparent; color: var(--color-ink); border-color: var(--color-ink); }
        .kem-btn-secondary:hover { background: var(--color-ink); color: var(--color-white); }
        .kem-btn-ghost { background: transparent; color: var(--color-ink); padding-inline: var(--space-8); }
        .kem-btn-ghost:hover { background: var(--color-neutral-100); }
        .kem-btn-destructive { background: var(--color-error); color: var(--color-white); }
        .kem-btn-destructive:hover { background: #912018; }
        .kem-icon-btn { width: 44px; min-width: 44px; height: 44px; padding: 0; }
        .kem-btn:active { opacity: 0.82; }
        .kem-btn:disabled,
        .kem-btn[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }

        /* Normalize repeated existing action controls without changing handlers. */
        .auth-submit,
        .add-to-cart-btn,
        .checkout-btn,
        .place-order-btn,
        .add-btn,
        .btn-save,
        .btn-cancel,
        .back-to-cart,
        .continue-shopping,
        .add-category-btn,
        .btn-edit,
        .btn-delete,
        .btn-view,
        .change-image-btn,
        .employee-btn {
            min-height: 44px;
            border-radius: var(--radius-xs);
            font-family: var(--font-ui);
            letter-spacing: 0.015em;
            transition: background-color var(--motion-standard) var(--ease-standard), color var(--motion-standard) var(--ease-standard), border-color var(--motion-standard) var(--ease-standard), opacity var(--motion-fast) var(--ease-standard);
        }

        .btn-delete { background: var(--color-error); color: var(--color-white); }
        .btn-delete:hover { background: #912018; }

        :is(.auth-submit, .add-to-cart-btn, .checkout-btn, .place-order-btn, .add-btn, .btn-save, .btn-cancel, .back-to-cart, .continue-shopping, .add-category-btn, .btn-edit, .btn-delete, .btn-view, .change-image-btn, .employee-btn):disabled {
            opacity: 0.45;
            cursor: not-allowed;
            transform: none;
        }

        /* Form system */
        .kem-field { display: grid; gap: var(--space-8); }
        .kem-label,
        .form-group label,
        .auth-input-group label,
        .checkout-form-group label {
            font: 600 var(--type-metadata)/1.35 var(--font-ui);
            text-transform: none;
            letter-spacing: 0.01em;
            color: var(--color-neutral-800);
        }

        .kem-input,
        .kem-select,
        .kem-textarea,
        .shop-search,
        .search-box,
        .form-group input,
        .form-group textarea,
        .form-group select,
        .auth-input-group input,
        .checkout-form-group input,
        .checkout-form-group textarea,
        .modal input {
            width: 100%;
            min-height: 48px;
            padding: var(--space-12) var(--space-16);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            background: var(--color-white);
            color: var(--color-ink);
            font: 400 var(--type-ui)/1.4 var(--font-ui);
            transition: border-color var(--motion-standard) var(--ease-standard), box-shadow var(--motion-standard) var(--ease-standard), background-color var(--motion-standard) var(--ease-standard);
        }

        :is(.kem-input, .kem-select, .kem-textarea, .shop-search, .search-box, .form-group input, .form-group textarea, .form-group select, .auth-input-group input, .checkout-form-group input, .checkout-form-group textarea, .modal input):focus {
            outline: none;
            border-color: var(--color-ink);
            box-shadow: 0 0 0 1px var(--color-ink);
        }

        :is(.kem-input, .kem-select, .kem-textarea, .shop-search, .search-box, .form-group input, .form-group textarea, .form-group select, .auth-input-group input, .checkout-form-group input, .checkout-form-group textarea, .modal input):disabled {
            background: var(--color-neutral-100);
            color: var(--color-neutral-600);
            cursor: not-allowed !important;
        }

        .kem-help { font: 400 var(--type-metadata)/1.5 var(--font-ui); color: var(--color-neutral-600); }
        .kem-field-error { font: 600 var(--type-metadata)/1.5 var(--font-ui); color: var(--color-error); }
        .error-message { color: var(--color-error); }

        /* Choice / variant primitives */
        .variant-option,
        .kem-choice {
            min-width: 44px;
            min-height: 44px;
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            background: var(--color-white);
            color: var(--color-ink);
            font: 600 var(--type-ui)/1 var(--font-ui);
            transition: background-color var(--motion-standard) var(--ease-standard), color var(--motion-standard) var(--ease-standard), border-color var(--motion-standard) var(--ease-standard);
        }

        .variant-option:hover,
        .kem-choice:hover { border-color: var(--color-neutral-600); }
        .variant-option.selected,
        .kem-choice[aria-pressed="true"] { background: var(--color-ink); border-color: var(--color-ink); color: var(--color-white); }
        .variant-option:disabled,
        .kem-choice:disabled { opacity: 0.4; cursor: not-allowed; }

        /* Card families stay intentionally distinct. */
        .kem-product-card,
        .product-card {
            background: var(--color-white);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            box-shadow: none;
            transition: border-color var(--motion-standard) var(--ease-standard);
        }

        .product-card:hover {
            transform: none;
            box-shadow: none;
            border-color: var(--color-neutral-400);
        }

        .kem-content-card {
            background: var(--color-white);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-sm);
            box-shadow: var(--shadow-soft);
            padding: var(--space-24);
        }

        .kem-dashboard-card,
        .dashboard-card {
            background: var(--color-white);
            border: 1px solid var(--color-neutral-200);
            border-left: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-sm);
            box-shadow: none;
        }

        /* Semantic feedback and status system. */
        .kem-state {
            padding: var(--space-16);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-sm);
            background: var(--color-white);
            color: var(--color-neutral-800);
            font: 400 var(--type-ui)/1.55 var(--font-ui);
        }
        .kem-state-loading,
        .kem-state-info { border-color: #B8CCF4; background: var(--color-info-surface); color: var(--color-info); }
        .kem-state-success { border-color: #B8DEC9; background: var(--color-success-surface); color: var(--color-success); }
        .kem-state-warning { border-color: #E8D08B; background: var(--color-warning-surface); color: var(--color-warning); }
        .kem-state-error { border-color: #F0B8B4; background: var(--color-error-surface); color: var(--color-error); }
        .kem-state-empty { color: var(--color-neutral-600); }

        .status-badge,
        .kem-status {
            display: inline-flex;
            align-items: center;
            min-height: 28px;
            padding: var(--space-4) var(--space-12);
            border-radius: var(--radius-pill);
            font: 600 var(--type-metadata)/1 var(--font-ui);
            letter-spacing: 0;
            text-transform: none;
        }
        .status-paid { background: var(--color-success-surface); color: var(--color-success); }
        .status-pending { background: var(--color-warning-surface); color: var(--color-warning); }
        .status-fulfilled { background: var(--color-info-surface); color: var(--color-info); }
        .status-cancelled { background: var(--color-error-surface); color: var(--color-error); }

        /* Shared panel/modal surface; behavior, sizing logic and dialog semantics remain frozen. */
        .modal,
        .form-modal,
        .auth-modal,
        .product-detail-modal {
            background: rgba(10, 10, 10, 0.76);
        }

        .modal-content,
        .form-modal-content,
        .auth-modal-content,
        .product-detail-content {
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-sm);
            box-shadow: var(--shadow-panel);
        }

        .modal .close-modal,
        .form-modal .close-modal,
        .auth-modal .close-modal,
        .product-detail-modal .close-modal {
            width: 44px;
            min-width: 44px;
            height: 44px;
            min-height: 44px;
            padding: 0;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 0;
            border-radius: var(--radius-xs);
            background: transparent;
            color: var(--color-ink);
            line-height: 1;
        }

        .modal .close-modal:hover,
        .form-modal .close-modal:hover,
        .auth-modal .close-modal:hover,
        .product-detail-modal .close-modal:hover {
            background: var(--color-neutral-100);
            color: var(--color-ink);
        }

        /* Preserve the strong P1 focus indicator globally. */
        :focus-visible {
            outline: 3px solid var(--color-kem-pink);
            outline-offset: 3px;
        }

        img,
        video,
        svg { max-width: 100%; }

        @media (prefers-reduced-motion: reduce) {
            html:focus-within { scroll-behavior: auto; }
            *,
            *::before,
            *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        }

'''
s = s.replace(anchor, foundation + anchor, 1)

path.write_text(s)
print('Applied P2.0 global design system to index.html only')
