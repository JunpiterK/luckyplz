# -*- coding: utf-8 -*-
"""우주 조종사 레서판다 흉상 렌더 → 게임 아틀라스 (2026-09-27).

scripts/og-assets/pilot_<game>/<frame>.png (mascot_spacez.py / mascot_lander.py 출력)
→ public/assets/<game>/pilot.webp  (셀 정사각, 4열, 순서 = mascot_spacez.ORDER)

- 렌더 프레임을 자르지 않고 셀 크기로만 줄인다(직교 카메라라 모든 프레임의 머리 위치가 같다 — 게임은
  셀 하나를 원형 창에 그대로 그린다)
- 알파는 premultiplied 로 줄인다(투명 픽셀 RGB 가 외곽선에 번지는 테두리 방지)
- 게임 코드의 PILOT 프레임 순서 표와 ORDER 가 같아야 한다

실행: python scripts/build_pilot_atlas.py dodge|starship-lander [--cell 256] [--q 84]
"""
import os
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ['focus', 'blink', 'lookL', 'lookR', 'scared', 'cheer', 'happy', 'dizzy', 'worry', 'cry', 'salute', 'ouch']
COLS = 4


def arg(name, dflt):
    if name in sys.argv:
        return type(dflt)(sys.argv[sys.argv.index(name) + 1])
    return dflt


def main():
    game = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'dodge'
    cell = arg('--cell', 256)
    q = arg('--q', 84)
    src = os.path.join(ROOT, "scripts", "og-assets", "pilot_" + game)
    rows = (len(ORDER) + COLS - 1) // COLS
    atlas = Image.new("RGBA", (cell * COLS, cell * rows), (0, 0, 0, 0))
    for i, n in enumerate(ORDER):
        im = Image.open(os.path.join(src, n + ".png")).convert("RGBA")
        a = im.getchannel("A").point(lambda v: 255 if v > 8 else 0)
        bb = a.getbbox()
        W, H = im.size
        if bb and (bb[0] <= 1 or bb[1] <= 1 or bb[2] >= W - 1):
            print("note: touches edge", n, bb)
        sm = im.convert("RGBa").resize((cell, cell), Image.LANCZOS).convert("RGBA")
        atlas.paste(sm, ((i % COLS) * cell, (i // COLS) * cell))
    dst = os.path.join(ROOT, "public", "assets", game)
    os.makedirs(dst, exist_ok=True)
    out = os.path.join(dst, "pilot.webp")
    atlas.save(out, "WEBP", quality=q, method=6, alpha_quality=90)
    print("atlas", out, os.path.getsize(out) // 1024, "KB", atlas.size)


if __name__ == "__main__":
    main()
