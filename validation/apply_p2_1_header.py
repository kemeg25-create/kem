from pathlib import Path
import re

path = Path('index.html')
s = path.read_text()


def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one match, found {count}')
    s = s.replace(old, new, 1)


nav_old = '''    <nav id="mainNav">
        <div class="logo">
            <img src="logo-240.png" alt="KEM" onerror="this.style.display='none'">
            <span class="logo-text">KEM</span>
        </div>
        <button type="button" class="mobile-nav-toggle" id="mobileNavToggle" aria-expanded="false" aria-controls="primaryNav" aria-label="Open navigation" onclick="toggleMobileNav()">☰</button>
        <ul class="nav-links" id="primaryNav">
            <li><a href="#home">Home</a></li>
            <li class="nav-dropdown">
                <button class="nav-dropdown-btn" onclick="toggleCategoriesDropdown()">
                    Categories <span>▼</span>
                </button>
                <div class="nav-dropdown-content" id="categoriesDropdown">
                    <!-- Categories will be rendered here -->
                </div>
            </li>
            <li><a href="#collections">Collections</a></li>
            <li><a href="#shop">Shop</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#contact">Contact</a></li>
        </ul>
    </nav>
'''

nav_new = '''    <nav id="mainNav" aria-label="Primary navigation">
        <div class="nav-shell">
            <button type="button" class="mobile-nav-toggle" id="mobileNavToggle" aria-expanded="false" aria-controls="primaryNav" aria-label="Open navigation" onclick="toggleMobileNav()">Menu</button>
            <a class="logo" href="#home" aria-label="KEM home">
                <img src="logo-240.png" alt="" onerror="this.style.display='none'">
                <span class="logo-text" aria-hidden="true">KEM</span>
            </a>
            <ul class="nav-links" id="primaryNav" aria-label="Store navigation">
                <li class="mobile-header-search">
                    <label class="visually-hidden" for="mobileHeaderSearch">Search products</label>
                    <input type="search" id="mobileHeaderSearch" placeholder="Search products" autocomplete="off" oninput="setShopSearch(this.value)">
                </li>
                <li><a href="#shop" onclick="toggleMobileNav(false)">Shop</a></li>
                <li class="nav-dropdown">
                    <button type="button" class="nav-dropdown-btn" aria-expanded="false" aria-controls="categoriesDropdown" onclick="toggleCategoriesDropdown()">
                        Categories <span class="nav-dropdown-caret" aria-hidden="true"></span>
                    </button>
                    <div class="nav-dropdown-content" id="categoriesDropdown">
                        <!-- Categories will be rendered here -->
                    </div>
                </li>
                <li><a href="#collections" onclick="toggleMobileNav(false)">Collections</a></li>
                <li><a href="#about" onclick="toggleMobileNav(false)">About</a></li>
                <li><a href="#contact" onclick="toggleMobileNav(false)">Contact</a></li>
            </ul>
        </div>
    </nav>
'''
replace_once(nav_old, nav_new, 'navigation markup')

utilities_old = '''        <!-- Auth Button -->
        <button class="auth-button" id="authButton" onclick="openAuthModal()">
            <span id="authButtonText">Login</span>
        </button>

        <!-- Cart Badge -->
        <button class="cart-badge empty" id="cartBadge" onclick="openCart()">
            <span class="cart-icon">🛒</span>
            <span>Cart</span>
            <span class="cart-count" id="cartCount">0</span>
        </button>
'''

utilities_new = '''        <!-- Header utilities remain inside mainSite so existing cart/category page visibility behavior is preserved. -->
        <div class="header-actions" aria-label="Store utilities">
            <div class="header-search">
                <label class="visually-hidden" for="headerSearch">Search products</label>
                <input type="search" id="headerSearch" placeholder="Search products" autocomplete="off" oninput="setShopSearch(this.value)">
            </div>
            <button type="button" class="auth-button" id="authButton" aria-label="Customer account" onclick="openAuthModal()">
                <span id="authButtonText">Login</span>
            </button>
            <button type="button" class="cart-badge empty" id="cartBadge" onclick="openCart()">
                <span class="header-action-label">Cart</span>
                <span class="cart-count" id="cartCount" aria-live="polite">0</span>
            </button>
        </div>
'''
replace_once(utilities_old, utilities_new, 'header utilities markup')

replace_once(
    "        function filterByCategory(name) { shopCategoryFilter=name||'all'; renderShopFilters(); renderShopProducts(); document.getElementById('categoriesDropdown')?.classList.remove('active'); }\n",
    "        function filterByCategory(name) { shopCategoryFilter=name||'all'; renderShopFilters(); renderShopProducts(); setCategoriesDropdownOpen(false); }\n",
    'filter category dropdown close',
)

replace_once(
    "        function setShopSearch(value) { shopSearchTerm=String(value||''); renderShopProducts(); }\n",
    '''        function setShopSearch(value) {
            shopSearchTerm=String(value||'');
            ['shopSearch','headerSearch','mobileHeaderSearch'].forEach(id=>{const input=document.getElementById(id);if(input&&input.value!==shopSearchTerm)input.value=shopSearchTerm;});
            renderShopProducts();
        }
''',
    'search synchronization',
)

mobile_old = '''        function toggleMobileNav(forceOpen) {
            const nav=document.getElementById('primaryNav'), btn=document.getElementById('mobileNavToggle'); if(!nav||!btn)return;
            const open=typeof forceOpen==='boolean'?forceOpen:!nav.classList.contains('mobile-open');
            nav.classList.toggle('mobile-open',open); btn.setAttribute('aria-expanded',String(open)); btn.setAttribute('aria-label',open?'Close navigation':'Open navigation'); btn.textContent=open?'×':'☰';
        }
'''
mobile_new = '''        function toggleMobileNav(forceOpen) {
            const nav=document.getElementById('primaryNav'), btn=document.getElementById('mobileNavToggle'); if(!nav||!btn)return;
            const open=typeof forceOpen==='boolean'?forceOpen:!nav.classList.contains('mobile-open');
            nav.classList.toggle('mobile-open',open);
            btn.setAttribute('aria-expanded',String(open));
            btn.setAttribute('aria-label',open?'Close navigation':'Open navigation');
            btn.textContent=open?'Close':'Menu';
            if(!open)setCategoriesDropdownOpen(false);
        }
'''
replace_once(mobile_old, mobile_new, 'mobile navigation state')

category_pattern = re.compile(
    r"        function toggleCategoriesDropdown\(\) \{.*?\n        \}\n\n        function renderCategoriesDropdown\(\) \{.*?\n        \}\n\n        function showCategoryPage",
    re.S,
)
category_replacement = '''        function setCategoriesDropdownOpen(open) {
            const dropdown=document.getElementById('categoriesDropdown');
            const button=document.querySelector('.nav-dropdown-btn');
            if(!dropdown||!button)return;
            dropdown.classList.toggle('active',Boolean(open));
            button.setAttribute('aria-expanded',String(Boolean(open)));
        }

        function toggleCategoriesDropdown() {
            const dropdown=document.getElementById('categoriesDropdown');
            setCategoriesDropdownOpen(!dropdown?.classList.contains('active'));
        }

        function renderCategoriesDropdown() {
            const dropdown = document.getElementById('categoriesDropdown');
            const visibleCategories = categories.filter(c => c.visible);

            if (visibleCategories.length === 0) {
                dropdown.innerHTML = '<p class="nav-dropdown-empty">No categories available</p>';
                return;
            }

            dropdown.innerHTML = visibleCategories.map(cat => `
                <button type="button" class="nav-dropdown-item" data-category-id="${Number(cat.id)}">
                    <span class="nav-dropdown-item-name">${escapeHTML(cat.name)}</span>
                    <span class="nav-dropdown-item-desc">${escapeHTML(cat.description)}</span>
                </button>
            `).join('');
            dropdown.querySelectorAll('button[data-category-id]').forEach(button => button.addEventListener('click', () => showCategoryPage(Number(button.dataset.categoryId))));
        }

        function showCategoryPage'''
s, count = category_pattern.subn(category_replacement, s, count=1)
if count != 1:
    raise SystemExit(f'categories navigation functions: expected one match, found {count}')

replace_once(
    '''            // Close dropdown
            document.getElementById('categoriesDropdown').classList.remove('active');

            // Hide main site, show category page
''',
    '''            // Close navigation surfaces before opening the category view.
            setCategoriesDropdownOpen(false);
            toggleMobileNav(false);

            // Hide main site, show category page
''',
    'category page navigation close',
)

keydown_pattern = re.compile(
    r"        document\.addEventListener\('keydown', event => \{.*?\n        \}\);\n\n        // Close dropdown when clicking outside",
    re.S,
)
keydown_replacement = '''        document.addEventListener('keydown', event => {
            const dialog = document.querySelector('#employeeModal.active,.form-modal.active,.auth-modal.active,.product-detail-modal.active');
            if (!dialog) {
                if (event.key === 'Escape') {
                    const dropdown = document.getElementById('categoriesDropdown');
                    const mobileNav = document.getElementById('primaryNav');
                    if (dropdown?.classList.contains('active')) {
                        event.preventDefault();
                        setCategoriesDropdownOpen(false);
                        document.querySelector('.nav-dropdown-btn')?.focus();
                    } else if (mobileNav?.classList.contains('mobile-open')) {
                        event.preventDefault();
                        toggleMobileNav(false);
                        document.getElementById('mobileNavToggle')?.focus();
                    }
                }
                return;
            }
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

        // Close dropdown when clicking outside'''
s, count = keydown_pattern.subn(keydown_replacement, s, count=1)
if count != 1:
    raise SystemExit(f'global keydown handler: expected one match, found {count}')

outside_old = '''        document.addEventListener('click', function(event) {
            const dropdown = document.querySelector('.nav-dropdown');
            if (dropdown && !dropdown.contains(event.target)) {
                document.getElementById('categoriesDropdown').classList.remove('active');
            }
        });
'''
outside_new = '''        document.addEventListener('click', function(event) {
            const dropdown = document.querySelector('.nav-dropdown');
            if (dropdown && !dropdown.contains(event.target)) {
                setCategoriesDropdownOpen(false);
            }
        });
'''
replace_once(outside_old, outside_new, 'outside dropdown close')

css = r'''

        /* =========================================================
           P2.1 — HEADER / NAVIGATION
           Visual integration only; existing storefront state and handlers remain.
           ========================================================= */
        #mainNav {
            height: 72px;
            min-height: 72px;
            padding: 0;
            display: block;
            background: var(--color-off-white);
            backdrop-filter: none;
            border-bottom: 1px solid var(--color-neutral-200);
            animation: none;
        }

        .nav-shell {
            width: min(calc(100% - (2 * var(--page-gutter))), var(--container-customer));
            height: 100%;
            margin-inline: auto;
            padding-right: 420px;
            display: flex;
            align-items: center;
            gap: var(--space-24);
            position: relative;
        }

        #mainNav .logo {
            flex: 0 0 auto;
            display: inline-flex;
            align-items: center;
            gap: var(--space-8);
            color: var(--color-ink);
            text-decoration: none;
            font-family: var(--font-display);
            font-size: 2rem;
            font-weight: 400;
            letter-spacing: 0.04em;
            line-height: 1;
        }

        #mainNav .logo img {
            height: 34px;
            width: auto;
            max-width: 44px;
            object-fit: contain;
            filter: none;
        }

        #mainNav .logo-text {
            background: none;
            color: var(--color-ink);
            -webkit-text-fill-color: currentColor;
        }

        #mainNav .nav-links {
            flex: 1 1 auto;
            min-width: 0;
            margin: 0 0 0 var(--space-8);
            gap: var(--space-24);
            justify-content: flex-start;
        }

        #mainNav .nav-links a,
        #mainNav .nav-dropdown-btn {
            min-height: 44px;
            padding: 0 var(--space-4);
            display: inline-flex;
            align-items: center;
            gap: var(--space-8);
            color: var(--color-ink);
            font: 600 var(--type-ui)/1 var(--font-ui);
            text-transform: none;
            letter-spacing: 0.01em;
            white-space: nowrap;
            transition: color var(--motion-standard) var(--ease-standard), background-color var(--motion-standard) var(--ease-standard);
        }

        #mainNav .nav-links a::after {
            bottom: 3px;
            height: 1px;
            background: var(--color-kem-pink);
            transition: width var(--motion-standard) var(--ease-standard);
        }

        #mainNav .nav-links a:hover,
        #mainNav .nav-dropdown-btn:hover,
        #mainNav .nav-dropdown-btn[aria-expanded="true"] {
            color: var(--color-kem-pink);
        }

        .nav-dropdown-caret {
            width: 7px;
            height: 7px;
            border-right: 1px solid currentColor;
            border-bottom: 1px solid currentColor;
            transform: rotate(45deg) translateY(-2px);
            transition: transform var(--motion-standard) var(--ease-standard);
        }

        .nav-dropdown-btn[aria-expanded="true"] .nav-dropdown-caret {
            transform: rotate(225deg) translate(-2px, -2px);
        }

        #mainNav .nav-dropdown-content {
            top: calc(100% + var(--space-8));
            left: 0;
            min-width: 280px;
            margin-top: 0;
            padding: var(--space-8);
            background: var(--color-white);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            box-shadow: var(--shadow-soft);
            animation: none;
        }

        #mainNav .nav-dropdown-item {
            width: 100%;
            min-height: 44px;
            padding: var(--space-12);
            display: block;
            text-align: left;
            background: var(--color-white);
            border: 0;
            border-bottom: 1px solid var(--color-neutral-100);
            border-radius: 0;
            color: var(--color-ink);
            font-family: var(--font-ui);
            cursor: pointer;
            transition: background-color var(--motion-standard) var(--ease-standard);
        }

        #mainNav .nav-dropdown-item:last-child { border-bottom: 0; }
        #mainNav .nav-dropdown-item:hover { padding-left: var(--space-12); background: var(--color-neutral-50); }
        #mainNav .nav-dropdown-item-name { display: block; margin: 0; font-size: var(--type-ui); font-weight: 600; }
        #mainNav .nav-dropdown-item-desc { display: block; margin-top: var(--space-4); color: var(--color-neutral-600); font-size: var(--type-metadata); line-height: 1.4; }
        #mainNav .nav-dropdown-empty { padding: var(--space-12); color: var(--color-neutral-600); font: 400 var(--type-ui)/1.4 var(--font-ui); }

        .header-actions {
            position: fixed;
            top: 0;
            right: max(var(--page-gutter), calc((100vw - var(--container-customer)) / 2));
            height: 72px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: var(--space-8);
            z-index: 1001;
        }

        .header-search {
            width: 220px;
            flex: 0 0 auto;
        }

        .header-search input,
        .mobile-header-search input {
            width: 100%;
            min-height: 44px;
            height: 44px;
            padding: 0 var(--space-12);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-xs);
            background: var(--color-white);
            color: var(--color-ink);
            font: 400 var(--type-ui)/1.3 var(--font-ui);
            transition: border-color var(--motion-standard) var(--ease-standard), background-color var(--motion-standard) var(--ease-standard);
        }

        .header-search input:focus,
        .mobile-header-search input:focus {
            border-color: var(--color-ink);
        }

        .visually-hidden {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }

        .header-actions .auth-button,
        .header-actions .cart-badge {
            position: static;
            top: auto;
            right: auto;
            min-height: 44px;
            height: 44px;
            width: auto;
            padding: 0 var(--space-12);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: var(--space-8);
            background: transparent;
            color: var(--color-ink);
            border: 1px solid transparent;
            border-radius: var(--radius-xs);
            box-shadow: none;
            font: 600 var(--type-ui)/1 var(--font-ui);
            text-transform: none;
            letter-spacing: 0.01em;
            transition: background-color var(--motion-standard) var(--ease-standard), border-color var(--motion-standard) var(--ease-standard), color var(--motion-standard) var(--ease-standard);
        }

        .header-actions .auth-button:hover,
        .header-actions .cart-badge:hover {
            transform: none;
            box-shadow: none;
            background: var(--color-neutral-100);
            border-color: var(--color-neutral-200);
            color: var(--color-ink);
        }

        .header-actions .auth-button.logged-in {
            background: transparent;
            border-color: var(--color-neutral-200);
            color: var(--color-ink);
        }

        .header-actions .cart-badge.empty { display: inline-flex; }
        .header-actions .cart-count {
            width: auto;
            min-width: 18px;
            height: 18px;
            padding: 0 var(--space-4);
            border-radius: var(--radius-pill);
            background: var(--color-ink);
            color: var(--color-white);
            font-size: 0.6875rem;
            line-height: 18px;
            font-weight: 600;
        }

        .mobile-header-search { display: none; }
        section[id], footer[id] { scroll-margin-top: calc(72px + var(--space-16)); }

        @media (max-width: 1180px) and (min-width: 961px) {
            .nav-shell { padding-right: 334px; gap: var(--space-12); }
            #mainNav .nav-links { gap: var(--space-12); margin-left: 0; }
            #mainNav .nav-links a,
            #mainNav .nav-dropdown-btn { font-size: 0.8125rem; padding-inline: 2px; }
            .header-search { width: 150px; }
            .header-actions .auth-button,
            .header-actions .cart-badge { padding-inline: var(--space-8); font-size: 0.8125rem; }
        }

        @media (max-width: 960px) {
            #mainNav {
                height: 64px;
                min-height: 64px;
            }

            .nav-shell {
                width: calc(100% - (2 * var(--page-gutter)));
                padding-right: 132px;
                gap: var(--space-8);
            }

            #mainNav .mobile-nav-toggle {
                order: 0;
                flex: 0 0 56px;
                width: 56px;
                height: 44px;
                min-height: 44px;
                margin-left: 0;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background: transparent;
                color: var(--color-ink);
                border: 1px solid var(--color-neutral-200);
                border-radius: var(--radius-xs);
                font: 600 0.75rem/1 var(--font-ui);
                letter-spacing: 0.01em;
            }

            #mainNav .mobile-nav-toggle[aria-expanded="true"] {
                background: var(--color-ink);
                border-color: var(--color-ink);
                color: var(--color-white);
            }

            #mainNav .logo {
                order: 1;
                min-width: 0;
                margin-left: 0;
                gap: var(--space-4);
                font-size: 1.75rem;
                letter-spacing: 0.03em;
            }

            #mainNav .logo img {
                height: 30px;
                max-width: 36px;
            }

            #mainNav .nav-links {
                display: none;
                position: fixed;
                top: 64px;
                left: 0;
                right: 0;
                width: 100%;
                max-height: calc(100dvh - 64px);
                margin: 0;
                padding: var(--space-16) var(--page-gutter) var(--space-24);
                flex-direction: column;
                align-items: stretch;
                gap: 0;
                overflow-y: auto;
                background: var(--color-white);
                border-bottom: 1px solid var(--color-neutral-200);
                z-index: 1000;
            }

            #mainNav .nav-links.mobile-open { display: flex; }
            #mainNav .nav-links > li { width: 100%; }
            #mainNav .nav-links a,
            #mainNav .nav-dropdown-btn {
                width: 100%;
                min-height: 48px;
                padding: var(--space-12) var(--space-4);
                justify-content: space-between;
                font-size: var(--type-ui);
            }

            .mobile-header-search {
                display: block;
                padding-bottom: var(--space-12);
                margin-bottom: var(--space-8);
                border-bottom: 1px solid var(--color-neutral-100);
            }

            #mainNav .nav-dropdown-content {
                position: static;
                width: 100%;
                min-width: 0;
                margin: 0 0 var(--space-8);
                padding: var(--space-4) 0 var(--space-8) var(--space-12);
                border: 0;
                border-left: 1px solid var(--color-neutral-200);
                box-shadow: none;
            }

            #mainNav .nav-dropdown-item { min-height: 48px; }

            .header-actions {
                right: var(--page-gutter);
                height: 64px;
                gap: var(--space-4);
            }

            .header-search { display: none; }

            .header-actions .auth-button,
            .header-actions .cart-badge {
                min-height: 44px;
                height: 44px;
                padding-inline: var(--space-8);
                font-size: 0.75rem;
            }

            .header-actions .auth-button {
                max-width: 64px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .header-actions .cart-badge { gap: var(--space-4); }
            .header-actions .cart-count {
                min-width: 16px;
                height: 16px;
                line-height: 16px;
                font-size: 0.625rem;
            }

            section[id], footer[id] { scroll-margin-top: calc(64px + var(--space-12)); }
        }
'''

style_anchor = '\n    </style>\n    <!-- Firebase SDK -->'
if s.count(style_anchor) != 1:
    raise SystemExit(f'style close anchor: expected one match, found {s.count(style_anchor)}')
s = s.replace(style_anchor, css + style_anchor, 1)

required = [
    'P2.1 — HEADER / NAVIGATION',
    'class="nav-shell"',
    'id="headerSearch"',
    'id="mobileHeaderSearch"',
    'aria-label="KEM home"',
    'setCategoriesDropdownOpen(false);',
    "btn.textContent=open?'Close':'Menu';",
    '.header-actions .cart-badge.empty { display: inline-flex; }',
]
for item in required:
    if item not in s:
        raise SystemExit(f'missing P2.1 anchor: {item}')

for selector_id in ['mainNav','mobileNavToggle','primaryNav','categoriesDropdown','shopSearch','authButton','authButtonText','cartBadge','cartCount']:
    count = len(re.findall(rf'id=["\']{re.escape(selector_id)}["\']', s))
    if count != 1:
        raise SystemExit(f'{selector_id}: expected one id occurrence, found {count}')

header_slice = s[s.index('<!-- Navigation -->'):s.index('<!-- Hero Section -->')]
for glyph in ['🛒','☰','▼']:
    if glyph in header_slice:
        raise SystemExit(f'header still contains prohibited interface glyph {glyph}')

if s.count("document.addEventListener('keydown', event => {") != 1:
    raise SystemExit('global P1 keydown listener count changed')
if 'overflow-x: hidden' in re.search(r'body\s*\{(.*?)\}', s, re.S).group(1):
    raise SystemExit('body overflow concealment returned')

path.write_text(s)
print('Applied contained P2.1 header/navigation patch to index.html')
