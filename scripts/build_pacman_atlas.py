# -*- coding: utf-8 -*-
"""닷 러너 레서판다 머리 렌더(scripts/og-assets/dotrunner/<frame>.png) → public/assets/pacman/runner.webp

- 순서 = scripts/blender/mascot_pacman.py 의 ORDER = 게임의 PMF 표 (행 우선, COLS 열)
- 프레임은 자르지 않고 셀 크기로만 줄인다 — 머리 중심·반지름(meta.json 정규 좌표)이 그대로 맞는다
- premultiplied 로 줄여 투명 가장자리 RGB 가 외곽선에 번지지 않게 한다

실행: python scripts/build_pacman_atlas.py [--cell 128] [--q 86]
"""
import json
import os
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts", "og-assets", "dotrunner")
DST = os.path.join(ROOT, "public", "assets", "pacman")
ORDER = ['r0', 'r1', 'r2', 'u0', 'u1', 'u2', 'd0', 'd1', 'd2',
         'pr0', 'pr1', 'pr2', 'pu0', 'pu1', 'pu2', 'pd0', 'pd1', 'pd2',
         'ready', 'shock', 'dizzy', 'happy']
COLS = 6


def arg(name, dflt):
    if name in sys.argv:
        return type(dflt)(sys.argv[sys.argv.index(name) + 1])
    return dflt


def shrink(im, cell):
    im = im.convert("RGBA")
    pm = im.convert("RGBa").resize((cell, cell), Image.LANCZOS)
    return pm.convert("RGBA")


def main():
    cell = arg('--cell', 128)
    q = arg('--q', 86)
    with open(os.path.join(SRC, "meta.json"), encoding='utf-8') as f:
        meta = json.load(f)
    rows = (len(ORDER) + COLS - 1) // COLS
    atlas = Image.new("RGBA", (cell * COLS, cell * rows), (0, 0, 0, 0))
    for i, n in enumerate(ORDER):
        im = Image.open(os.path.join(SRC, n + ".png"))
        atlas.paste(shrink(im, cell), ((i % COLS) * cell, (i // COLS) * cell))
    os.makedirs(DST, exist_ok=True)
    out = os.path.join(DST, "runner.webp")
    atlas.save(out, "WEBP", quality=q, method=6)
    m = meta[ORDER[0]]
    print("wrote", out, atlas.size, os.path.getsize(out), "bytes")
    print("/*PMF*/ const PM_CELL=%d, PM_COLS=%d, PM_HEAD=[%s,%s], PM_HEADR=%s;" % (
        cell, COLS, m['head'][0], m['head'][1], m['headR']))
    print("const PMF={" + ",".join("%s:%d" % (n, i) for i, n in enumerate(ORDER)) + "};")


if __name__ == "__main__":
    main()
