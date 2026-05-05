"""
Bulk-apply mobile CSS improvements to all paper-theme blog posts.

Updates the @media(max-width:600px) block to add:
- Tighter page padding (gets content closer to edges)
- Smaller h1 on mobile + auto-hide manual <br> in titles
- Smaller subtitle / h2 / box / person / quote padding
- Reduced line-height for more compact reading

Run from repo root:
    python scripts/mobile-css-upgrade.py
"""
import glob

OLD = '.page{padding:40px 18px 60px}.meta{flex-wrap:wrap;gap:10px;font-size:12px}.series-nav-grid{grid-template-columns:1fr}'

NEW = (
    '.page{padding:24px 14px 48px}'
    'body{line-height:1.7}'
    'h1{font-size:clamp(22px,6.5vw,28px);line-height:1.22}'
    'h1 br{display:none}'
    '.subtitle{font-size:15.5px;line-height:1.65;margin-bottom:18px}'
    'h2{font-size:20px;margin:36px 0 12px}'
    '.meta{flex-wrap:wrap;gap:8px;font-size:11.5px;padding:8px 14px;margin-bottom:32px}'
    '.box{padding:14px 16px;font-size:14.5px;margin:18px 0}'
    '.person{padding:14px 16px;margin:16px 0}'
    '.person-name{font-size:16.5px}'
    '.person p{font-size:14px}'
    '.quote{padding:14px 18px;margin:18px 0}'
    '.quote p{font-size:15.5px}'
    '.bimg{margin:20px 0}'
    '.bimg figcaption{padding:10px 14px;font-size:12.5px}'
    '.bvideo{margin:20px 0}'
    '.bvideo figcaption{padding:10px 14px;font-size:12.5px}'
    '.series-nav{padding:18px;margin-top:32px}'
    '.series-nav-grid{grid-template-columns:1fr;gap:10px}'
    '.series-nav-cell{padding:12px 14px}'
)

files = sorted(glob.glob('public/blog/*/index.html'))
updated = []
skipped = []
for f in files:
    with open(f, 'r', encoding='utf-8') as fp:
        content = fp.read()
    if OLD in content:
        content = content.replace(OLD, NEW)
        with open(f, 'w', encoding='utf-8') as fp:
            fp.write(content)
        updated.append(f)
    else:
        skipped.append(f)

print(f'\n[Updated {len(updated)}]')
for f in updated:
    print(f'  + {f}')
print(f'\n[Skipped {len(skipped)}] (no matching pattern, likely different theme)')
for f in skipped:
    print(f'  - {f}')
