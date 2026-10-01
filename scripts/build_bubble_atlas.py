# -*- coding: utf-8 -*-
"""버블 버스트 버블 아틀라스 빌더 (2026-10-01).

scripts/og-assets/bubble/<frame>.png (scripts/blender/bubble_orbs.py 렌더) → public/assets/bubble/orbs.webp

- 순서 = bubble_orbs.ORDER (게임 JS 의 BA_ORDER 와 같아야 한다 — 아래가 JS 상수를 같이 찍는다)
- 렌더 잘림 검사: 알파 bbox 가 프레임 가장자리에 닿으면 실패(art_pipeline 메모의 규칙)
실행: python scripts/build_bubble_atlas.py
"""
import os
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'scripts', 'og-assets', 'bubble')
OUT = os.path.join(ROOT, 'public', 'assets', 'bubble', 'orbs.webp')
ORDER = ['c%d' % i for i in range(6)] + ['k%d' % i for i in range(6)] + ['rb', 'bm', 'ln', 'gy', 'ice', 'ice2']
COLS = 5
CELL = int(os.environ.get('BA_CELL', '160'))


def main():
    rows = (len(ORDER) + COLS - 1) // COLS
    atlas = Image.new('RGBA', (COLS * CELL, rows * CELL), (0, 0, 0, 0))
    bad = []
    for i, n in enumerate(ORDER):
        im = Image.open(os.path.join(SRC, n + '.png')).convert('RGBA')
        a = im.getchannel('A').point(lambda v: 255 if v > 8 else 0)
        bb = a.getbbox()
        if not bb or bb[0] <= 0 or bb[1] <= 0 or bb[2] >= im.width or bb[3] >= im.height:
            bad.append((n, bb))
        im = im.resize((CELL, CELL), Image.LANCZOS)
        atlas.alpha_composite(im, ((i % COLS) * CELL, (i // COLS) * CELL))
    if bad:
        print('CLIPPED', bad)
        sys.exit(1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    atlas.save(OUT, 'WEBP', quality=90, method=6)
    print('wrote', OUT, os.path.getsize(OUT), 'bytes', atlas.size)
    print('/*BA:start*/const BA_ORDER=%s, BA_COLS=%d;/*BA:end*/' % (str(ORDER).replace(' ', ''), COLS))


if __name__ == '__main__':
    main()
