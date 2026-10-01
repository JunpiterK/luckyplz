# -*- coding: utf-8 -*-
"""board_pals.py 렌더 → 게임 아틀라스 (Blender 가 아니라 일반 파이썬 + Pillow 로 돈다).

  python scripts/blender/board_pals_atlas.py ludo      → public/assets/ludo/pals.webp
  python scripts/blender/board_pals_atlas.py reversi   → public/assets/reversi/pals.webp

- 한 게임의 32장 전체 합집합 bbox 로 **똑같이** 자른다 → 표정을 바꿔 끼워도 받침이 1px 도 안 움직인다
- 열 = 표정 n b h s x o c w (yut_pieces 와 같은 순서 — 게임의 EXC 표와 맞아야 한다)
- 행 = 루도: 판 자리 순서 빨강(panda) · 초록(cat) · 노랑(fox) · 파랑(otter)
       리버시: 난이도 순서 kong · dan · dad · guru
- 받침 중심의 셀 내 높이(FOOT)를 출력한다 — 게임이 칸 중심에 이 점을 맞춘다
환경: BP_OUT(렌더 폴더, 기본 scripts/og-assets)
"""
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.environ.get('BP_OUT') or os.path.join(ROOT, "scripts", "og-assets")
EXPRS = ['n', 'b', 'h', 's', 'x', 'o', 'c', 'w']
SETS = {
    'ludo': (['panda', 'cat', 'fox', 'otter'], 128, 82),
    'reversi': (['kong', 'dan', 'dad', 'guru'], 160, 80),
}


def build(game):
    rows, cell, q = SETS[game]
    src = os.path.join(SRC, game)
    ims = {(r, e): Image.open(os.path.join(src, "%s-%s.png" % (r, e))).convert("RGBA") for r in rows for e in EXPRS}
    box = None
    for im in ims.values():
        b = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    w, h = box[2] - box[0], box[3] - box[1]
    side = int(max(w, h) * 1.04)
    cx = (box[0] + box[2]) / 2
    left = int(cx - side / 2)
    bottom = box[3] + int(side * 0.02)
    top = bottom - side
    atlas = Image.new("RGBA", (cell * len(EXPRS), cell * len(rows)), (0, 0, 0, 0))
    for r, s in enumerate(rows):
        for c, e in enumerate(EXPRS):
            sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            sq.paste(ims[(s, e)].crop((left, top, left + side, bottom)), (0, 0))
            atlas.paste(sq.resize((cell, cell), Image.LANCZOS), (c * cell, r * cell))
    dst = os.path.join(ROOT, "public", "assets", game)
    os.makedirs(dst, exist_ok=True)
    out = os.path.join(dst, "pals.webp")
    atlas.save(out, "WEBP", quality=q, method=6)
    a = ims[(rows[0], 'n')].getchannel("A")
    col = int(cx)
    ys = [y for y in range(a.size[1]) if a.getpixel((col, y)) > 200]
    print(game, "atlas", out, "%.1f KB" % (os.path.getsize(out) / 1024), atlas.size, "cell", cell, "side", side, "box", box)
    print("  base bottom rel = %.3f  suggested FOOT = %.3f" % ((max(ys) - top) / side, (max(ys) - top) / side - 0.045))


if __name__ == "__main__":
    for g in (sys.argv[1:] or ['ludo', 'reversi']):
        build(g)
