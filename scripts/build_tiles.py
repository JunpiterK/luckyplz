# -*- coding: utf-8 -*-
"""Blender 장난감 렌더(scripts/og-assets/tiles3d/*.png) → 홈 타일 webp(public/assets/tiles/toy-<id>.webp).

- 그림자 캐처가 프레임 가장자리 바닥까지 옅은 알파(10~30)를 남긴다. 그대로 자르면 타일 위에
  네모난 얼룩이 생기므로, 장난감 불투명 영역 밖의 알파는 거리 기반으로 부드럽게 지운다
- 자른 뒤 정사각 여백을 똑같이 줘서 9종의 시각 크기를 맞춘다
실행: python scripts/build_tiles.py [id ...]
"""
import os
import sys
from PIL import Image, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts", "og-assets", "tiles3d")
DST = os.path.join(ROOT, "public", "assets", "tiles")
IDS = ['roulette', 'car-racing', 'glory-racing', 'dice', 'ladder', 'bingo', 'team', 'retro', 'balloon']
OUT = 560      # 4K 3열에서 아이콘 ≈150px × DPR 2 + 여유
PAD = 0.04


def build(gid):
    im = Image.open(os.path.join(SRC, gid + ".png")).convert("RGBA")
    a = im.getchannel("A")
    solid = a.point(lambda v: 255 if v >= 200 else 0)
    bb = solid.getbbox()
    # 장난감 상자에서 멀어질수록 알파를 줄이는 마스크 (상자 안 = 1)
    m = Image.new("L", im.size, 0)
    m.paste(255, (bb[0] - 6, bb[1], bb[2] + 6, bb[3] + 10))
    m = m.filter(ImageFilter.GaussianBlur(22))
    a2 = ImageChops.multiply(a, m)
    a2 = ImageChops.lighter(a2, solid)   # 장난감 본체는 절대 깎지 않는다
    im.putalpha(a2)
    bb2 = a2.point(lambda v: 255 if v > 12 else 0).getbbox()
    im = im.crop(bb2)
    w, h = im.size
    s = int(max(w, h) * (1 + PAD * 2))
    sq = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    # 세로는 바닥 쪽을 약간 더 붙인다(그림자가 아래에 있어 시각 중심이 위로 뜬다)
    sq.paste(im, ((s - w) // 2, (s - h) // 2 + int((s - h) * 0.08)))
    sq = sq.resize((OUT, OUT), Image.LANCZOS)
    os.makedirs(DST, exist_ok=True)
    out = os.path.join(DST, "toy-%s.webp" % gid)
    sq.save(out, "WEBP", quality=88, method=6)
    print(gid, "src", bb, "->", os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    for gid in (sys.argv[1:] or IDS):
        build(gid)
