# -*- coding: utf-8 -*-
"""윷놀이 말 렌더(scripts/og-assets/yut/<sp>-<ex>.png) → 아틀라스 public/assets/yut/pieces.webp.

- 24장 전체의 합집합 bbox 로 **똑같이** 자른다 → 표정을 바꿔 끼워도 몸이 1px 도 안 움직인다
- 행 = 종(fox·otter·panda·cat), 열 = 표정(n b h s x o). 셀 CELL px 정사각
- 받침 원판 중심의 셀 내 위치(FOOT_Y)를 출력한다 — 게임이 말밭 점에 이 점을 맞춘다
실행: python scripts/build_yut_atlas.py
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts", "og-assets", "yut")
DST = os.path.join(ROOT, "public", "assets", "yut")
SPECIES = ['fox', 'otter', 'panda', 'cat']
EXPRS = ['n', 'b', 'h', 's', 'x', 'o']
CELL = 256


def main():
    ims = {(s, e): Image.open(os.path.join(SRC, "%s-%s.png" % (s, e))).convert("RGBA") for s in SPECIES for e in EXPRS}
    box = None
    for im in ims.values():
        b = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    w, h = box[2] - box[0], box[3] - box[1]
    side = int(max(w, h) * 1.04)
    cx = (box[0] + box[2]) / 2
    # 좌우 가운데, 아래는 여백 2%
    left = int(cx - side / 2)
    bottom = box[3] + int(side * 0.02)
    top = bottom - side
    atlas = Image.new("RGBA", (CELL * len(EXPRS), CELL * len(SPECIES)), (0, 0, 0, 0))
    for r, s in enumerate(SPECIES):
        for c, e in enumerate(EXPRS):
            src = ims[(s, e)]
            sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            sq.paste(src.crop((left, top, left + side, bottom)), (0, 0))
            atlas.paste(sq.resize((CELL, CELL), Image.LANCZOS), (c * CELL, r * CELL))
    os.makedirs(DST, exist_ok=True)
    out = os.path.join(DST, "pieces.webp")
    atlas.save(out, "WEBP", quality=90, method=6)
    # 받침 원판: 이미지 맨 아래 불투명 행에서 원판 두께의 절반쯤 위가 중심
    a = ims[('fox', 'n')].getchannel("A")
    W, H = a.size
    col = int(cx)
    ys = [y for y in range(H) if a.getpixel((col, y)) > 200]
    print("atlas", out, os.path.getsize(out) // 1024, "KB", "side", side, "box", box)
    print("base bottom rel = %.3f" % ((max(ys) - top) / side))


if __name__ == "__main__":
    main()
