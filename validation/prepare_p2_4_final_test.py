from pathlib import Path
src=Path('validation/p2_4_product_detail_targeted.cjs').read_text()
old="""      await page.locator('#productDetailModal .add-to-cart-btn').focus();
      const focus = await page.locator('#productDetailModal .add-to-cart-btn').evaluate(el => { const s=getComputedStyle(el); return {width:s.outlineWidth,style:s.outlineStyle,color:s.outlineColor}; });
      check(focus.width === '3px' && focus.style === 'solid', `P2.1 3px visible keyboard focus remains intact in product detail at ${width}px`, JSON.stringify(focus));"""
new="""      await page.getByRole('button', { name: 'Increase quantity' }).focus();
      await page.keyboard.press('Tab');
      const focus = await page.locator('#productDetailModal .add-to-cart-btn').evaluate(el => { const s=getComputedStyle(el); return {active:document.activeElement===el,width:s.outlineWidth,style:s.outlineStyle,color:s.outlineColor}; });
      check(focus.active && focus.width === '3px' && focus.style === 'solid', `P2.1 3px visible keyboard focus remains intact in product detail at ${width}px`, JSON.stringify(focus));"""
assert old in src
Path('/tmp/p2_4_product_detail_targeted.cjs').write_text(src.replace(old,new,1))
print('Prepared keyboard-accurate P2.4 targeted test copy')
