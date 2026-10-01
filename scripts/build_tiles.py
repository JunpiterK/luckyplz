# -*- coding: utf-8 -*-
"""Blender 장난감 렌더(scripts/og-assets/tiles3d/*.png) → 홈 타일 webp(public/assets/tiles/toy-<id>.webp).

- 그림자 캐처가 프레임 가장자리 바닥까지 옅은 알파(10~30)를 남긴다. 그대로 자르면 타일 위에
  네모난 얼룩이 생기므로, 장난감 불투명 영역 밖의 알파는 거리 기반으로 부드럽게 지운다
- 자른 뒤 정사각 여백을 똑같이 줘서 9종의 시각 크기를 맞춘다
- 축소판(s160·s256·s384/) 도 함께 만든다 — 홈·아케이드가 srcset 으로 화면에 맞는 크기만 받는다.
  모바일 3열 타일 아이콘은 ~80px(DPR 2.6 → ~210px) 인데 560px 원본을 9장 받으면 첫 화면 이미지가
  500KB 를 넘어 LCP 를 끌었다(2026-10-02 CWV 측정). 원본 560px 은 그대로 두고 그 webp 에서 줄인다
실행: python scripts/build_tiles.py [id ...]
      python scripts/build_tiles.py --sizes      # 이미 있는 toy-*.webp 전부의 축소판만 다시 만든다
타일 webp 를 다른 방법으로 바꿨다면 반드시 --sizes 를 다시 돌릴 것 — 축소판이 옛 그림으로 남는다
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
SIZES = (160, 256, 384)   # srcset 축소판 폭 — public/assets/tiles/s<N>/toy-<id>.webp


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
    build_sizes("toy-%s" % gid)


def build_sizes(name):
    """public/assets/tiles/<name>.webp(560 원본) → s<N>/<name>.webp. 알파 가장자리 번짐을 막으려고
    premultiplied(RGBa) 상태에서 줄인다."""
    src = os.path.join(DST, name + ".webp")
    im = Image.open(src).convert("RGBA").convert("RGBa")
    out = []
    for n in SIZES:
        d = os.path.join(DST, "s%d" % n)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, name + ".webp")
        im.resize((n, n), Image.LANCZOS).convert("RGBA").save(p, "WEBP", quality=88, method=6)
        out.append("%d:%dKB" % (n, (os.path.getsize(p) + 512) // 1024))
    print(name, "sizes", " ".join(out))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--sizes"]:
        for f in sorted(os.listdir(DST)):
            if f.startswith("toy-") and f.endswith(".webp"):
                build_sizes(f[:-5])
    else:
        for gid in (sys.argv[1:] or IDS):
            build(gid)
