"""Inject SpaceX IPO banner into space-evo posts (KR series)."""
import os

SPACEX_BANNER = '''<!-- SPACEX IPO 2026 PROMO (cross-funnel from space-evo series) -->
<aside style="margin:32px auto;max-width:680px;padding:18px 16px;background:linear-gradient(135deg,#0a1224 0%,#050810 100%);border:1px solid rgba(93,193,255,0.4);border-radius:12px;color:#e8eef7;font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
  <div style="font-size:10px;letter-spacing:0.22em;color:#5dc1ff;font-weight:700;text-transform:uppercase;margin-bottom:8px;">&#127881; SPACEX IPO &middot; 2026.06 LIVE</div>
  <h3 style="font-size:17px;font-weight:800;color:#fff;margin-bottom:6px;letter-spacing:-0.01em;">$1.75T 머스크 제국 IPO — 종합 분석</h3>
  <p style="font-size:13px;color:#8c9cb6;line-height:1.6;margin-bottom:12px;">xAI 합병&middot;Starship V3&middot;Orbital AI 세 축으로 재무장한 머스크 제국. 5대 사업부문, Bull/Bear 시나리오, 7가지 위험, 라이브 D-day 카운트다운.</p>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
    <a href="/blog/spacex-ipo-2026/" style="display:block;padding:10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-decoration:none;color:inherit;font-size:12px;font-weight:600;"><span style="color:#5dc1ff;">&#128202;</span> 심층분석</a>
    <a href="/tools/spacex-countdown/" style="display:block;padding:10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-decoration:none;color:inherit;font-size:12px;font-weight:600;"><span style="color:#5dc1ff;">&#9203;</span> 카운트다운</a>
    <a href="/blog/how-to-buy-spacex-stock/" style="display:block;padding:10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-decoration:none;color:inherit;font-size:12px;font-weight:600;"><span style="color:#5dc1ff;">&#128176;</span> 한국에서 사는 법</a>
    <a href="/blog/spacex-ipo-risks/" style="display:block;padding:10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-decoration:none;color:inherit;font-size:12px;font-weight:600;"><span style="color:#5dc1ff;">&#9888;&#65039;</span> 위험 7가지</a>
  </div>
</aside>

<!-- AD SLOT -->'''

base = 'public/blog'
posts = sorted([d for d in os.listdir(base) if d.startswith('space-evo-') and os.path.isdir(os.path.join(base, d))])
print('Found', len(posts), 'posts')
modified = 0
for p in posts:
    fp = os.path.join(base, p, 'index.html')
    with open(fp, 'r', encoding='utf-8') as f:
        html = f.read()
    if 'SPACEX IPO 2026 PROMO' in html:
        print('  [skip] already done:', p)
        continue
    if '<!-- AD SLOT -->' not in html:
        print('  [skip] no anchor:', p)
        continue
    new_html = html.replace('<!-- AD SLOT -->', SPACEX_BANNER, 1)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(new_html)
    modified += 1
    print('  [done]', p)
print('\\nModified', modified, '/', len(posts))
