from pathlib import Path

old_sha='053968b477852c14569998ef9f5e1eb575d44437'
new_sha='eedbf94257b21436f27c281f18c813583333a8b8'
wf=Path('.github/workflows/p2-4-validation.yml')
s=wf.read_text()
assert old_sha in s
s=s.replace(old_sha,new_sha)
wf.write_text(s)

test=Path('validation/p2_4_product_detail_targeted.cjs')
t=test.read_text()
old="""      await page.locator('#productDetailModal .add-to-cart-btn').focus();
      const focus = await page.locator('#productDetailModal .add-to-cart-btn').evaluate(el => { const s=getComputedStyle(el); return {width:s.outlineWidth,style:s.outlineStyle,color:s.outlineColor}; });
      check(focus.width === '3px' && focus.style === 'solid', `P2.1 3px visible keyboard focus remains intact in product detail at ${width}px`, JSON.stringify(focus));"""
new="""      await page.getByRole('button', { name: 'Increase quantity' }).focus();
      await page.keyboard.press('Tab');
      const focus = await page.locator('#productDetailModal .add-to-cart-btn').evaluate(el => { const s=getComputedStyle(el); return {active:document.activeElement===el,width:s.outlineWidth,style:s.outlineStyle,color:s.outlineColor}; });
      check(focus.active && focus.width === '3px' && focus.style === 'solid', `P2.1 3px visible keyboard focus remains intact in product detail at ${width}px`, JSON.stringify(focus));"""
assert old in t
test.write_text(t.replace(old,new,1))
print('Repinned P2.4 validation and corrected keyboard-focus harness sequence')
