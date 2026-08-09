from pathlib import Path
import re
s=Path('index.html').read_text().splitlines()
patterns=['<nav id="mainNav"','@media (max-width: 768px)','id="shop"','shopProductsGrid','function renderShopProducts','function filterByCategory','function openProductDetail','productDetailModal','id="productForm"','function handleImageUpload','function saveProduct','function renderOrders','function loadOrders','function loadOverview','orderHistory','authModal','form-modal','dashboard-content','<table']
for pat in patterns:
    print('\n###',pat)
    hits=[i for i,l in enumerate(s) if pat in l]
    print('hits', [i+1 for i in hits])
    for i in hits[:4]:
        lo=max(0,i-12); hi=min(len(s),i+45)
        for n in range(lo,hi): print(f'{n+1:05d}: {s[n]}')
        print('---')
