# -*- coding: utf-8 -*-
"""진행자 레서판다 렌더(scripts/og-assets/mascot_mc/<frame>.png, mascot_mc.py 출력)
→ 아틀라스 public/assets/roulette/panda-mc.webp + public/assets/dice/panda-mc.webp (같은 그림 — 게임은 서로 독립).

- 5열 × 2행, 셀은 정사각(기본 240px). 순서 = ORDER — 게임 안 MC 표(룰렛 RX_MC / 주사위 DX_MC)와 같아야 한다
- 프레임을 자르지 않고 줄이기만 한다(직교 카메라라 발 위치가 모든 셀에서 같다 → 포즈를 바꿔도 발이 안 흔들린다)
- 알파는 premultiplied 로 줄인다(외곽선 주변 밝은 테두리 방지)

실행: python scripts/blender/build_flagship_mascot.py [--cell 240] [--q 82]
"""
import os
import shutil
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "scripts", "og-assets", "mascot_mc")
ORDER = ['mc_idle', 'mc_blink', 'mc_talk', 'mc_watch', 'mc_tense', 'mc_gasp', 'mc_win', 'mc_cheer', 'mc_aww', 'mc_point']
COLS = 5


def arg(name, dflt):
    if name in sys.argv:
        return type(dflt)(sys.argv[sys.argv.index(name) + 1])
    return dflt


def main():
    cell = arg('--cell', 240)
    q = arg('--q', 82)
    rows = (len(ORDER) + COLS - 1) // COLS
    atlas = Image.new("RGBA", (cell * COLS, cell * rows), (0, 0, 0, 0))
    for i, n in enumerate(ORDER):
        im = Image.open(os.path.join(SRC, n + ".png")).convert("RGBA")
        bb = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        W, H = im.size
        if bb[0] <= 1 or bb[1] <= 1 or bb[2] >= W - 1 or bb[3] >= H - 1:
            print("WARN clipped", n, bb)
        sm = im.convert("RGBa").resize((cell, cell), Image.LANCZOS).convert("RGBA")
        atlas.paste(sm, ((i % COLS) * cell, (i // COLS) * cell))
    first = None
    for g in ('roulette', 'dice'):
        d = os.path.join(ROOT, "public", "assets", g)
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, "panda-mc.webp")
        if first is None:
            atlas.save(out, "WEBP", quality=q, method=6, alpha_quality=88)
            first = out
        else:
            shutil.copyfile(first, out)
        print("atlas", out, os.path.getsize(out) // 1024, "KB", atlas.size)


if __name__ == "__main__":
    main()
