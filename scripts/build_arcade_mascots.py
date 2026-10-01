# -*- coding: utf-8 -*-
"""버거 셰프 · 행성 키우기 스프라이트 아틀라스 (2026-09-27 아케이드 임팩트 개편).

렌더(scripts/blender/mascot_burger.py · mascot_lucky_merge.py) → public/assets/<game>/*.webp
+ 게임 코드에 붙일 좌표표(JSON 한 줄)를 출력한다.
- 셀은 **자르지 않고** 줄이기만 한다 → meta.json 의 정규 좌표(0~1)가 셀 좌표에 그대로 맞는다
- 알파는 premultiplied 로 줄인다(투명 픽셀 RGB 가 외곽선에 번지는 테두리 방지)

실행: python scripts/build_arcade_mascots.py burger|merge
"""
import json
import os
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OG = os.path.join(ROOT, "scripts", "og-assets")


def atlas(src_dir, names, cols, cw, ch, out, q=84):
    rows = (len(names) + cols - 1) // cols
    A = Image.new("RGBA", (cw * cols, ch * rows), (0, 0, 0, 0))
    for i, n in enumerate(names):
        im = Image.open(os.path.join(src_dir, n + ".png")).convert("RGBA")
        bb = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        W, H = im.size
        if bb and (bb[0] <= 1 or bb[1] <= 1 or bb[2] >= W - 1 or bb[3] >= H - 1):
            print("WARN clipped", n, bb, file=sys.stderr)
        sm = im.convert("RGBa").resize((cw, ch), Image.LANCZOS).convert("RGBA")
        A.paste(sm, ((i % cols) * cw, (i // cols) * ch))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    A.save(out, "WEBP", quality=q, method=6, alpha_quality=90)
    print("atlas", os.path.relpath(out, ROOT), os.path.getsize(out) // 1024, "KB", A.size, file=sys.stderr)


def icon_atlas(src_dir, names, cols, cell, out, q=84, pad=0.03):
    """아이콘 — 알파 bbox 로 잘라 정사각 가운데 정렬(셀을 꽉 채운다). 셀 중심 = 아이콘 중심"""
    rows = (len(names) + cols - 1) // cols
    A = Image.new("RGBA", (cell * cols, cell * rows), (0, 0, 0, 0))
    for i, n in enumerate(names):
        im = Image.open(os.path.join(src_dir, n + ".png")).convert("RGBA")
        bb = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        W, H = im.size
        if bb[0] <= 1 or bb[1] <= 1 or bb[2] >= W - 1 or bb[3] >= H - 1:
            print("WARN clipped", n, bb, file=sys.stderr)
        im = im.crop(bb)
        s = int(max(im.size) * (1 + 2 * pad))
        sq = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        sq.paste(im, ((s - im.width) // 2, (s - im.height) // 2))
        sm = sq.convert("RGBa").resize((cell, cell), Image.LANCZOS).convert("RGBA")
        A.paste(sm, ((i % cols) * cell, (i // cols) * cell))
    A.save(out, "WEBP", quality=q, method=6, alpha_quality=90)
    print("atlas", os.path.relpath(out, ROOT), os.path.getsize(out) // 1024, "KB", A.size, file=sys.stderr)


def r4(v):
    if isinstance(v, list):
        return [r4(x) for x in v]
    if isinstance(v, dict):
        return {k: r4(x) for k, x in v.items()}
    if isinstance(v, float):
        return round(v, 4)
    return v


def burger():
    dst = os.path.join(ROOT, "public", "assets", "burger")
    chef = ['idle', 'blink', 'placeA', 'placeB', 'flip', 'cheer', 'serve', 'panic', 'oops', 'sad', 'cry', 'wave']
    d = os.path.join(OG, "burger", "chef")
    atlas(d, chef, 4, 320, 320, os.path.join(dst, "chef.webp"))
    cm = json.load(open(os.path.join(d, "meta.json"), encoding='utf-8'))
    sp, ex = ['fox', 'otter', 'cat'], ['n', 'b', 'h', 'x', 's', 'o']
    g = os.path.join(OG, "burger", "guest")
    atlas(g, ['%s-%s' % (s, e) for s in sp for e in ex], 6, 176, 176, os.path.join(dst, "guests.webp"))
    gm = json.load(open(os.path.join(g, "meta.json"), encoding='utf-8'))
    food = ['bunBottom', 'bunTop', 'patty', 'cheese', 'lettuce', 'tomato', 'onion']
    f = os.path.join(OG, "burger", "food")
    atlas(f, food, 4, 384, 240, os.path.join(dst, "food.webp"), q=86)
    fm = json.load(open(os.path.join(f, "meta.json"), encoding='utf-8'))
    # 2026-09-30 v3 — 접시·주문서용 60° 아이콘 (mascot_burger.py -- icon)
    icon_atlas(os.path.join(OG, "burger", "icon"), food, 4, 192, os.path.join(dst, "icons.webp"))
    out = dict(chef=dict(cols=4, order=chef, meta={k: r4(cm[k]) for k in chef}),
               guest=dict(cols=6, sp=sp, ex=ex, head=r4(gm['fox-n']['head']), headR=r4(gm['fox-n']['headR'])),
               food=dict(cols=4, order=food, o=r4(fm['patty']['o']), ux=r4(fm['patty']['ux'])),
               icon=dict(cols=4, cell=192))
    print(json.dumps(out, separators=(',', ':')))


def merge():
    dst = os.path.join(ROOT, "public", "assets", "lucky-merge")
    order = ['idle', 'blink', 'drop', 'happy', 'cheer', 'wow', 'nervous', 'cry', 'wink']
    d = os.path.join(OG, "lucky-merge", "ufo")
    atlas(d, order, 5, 256, 256, os.path.join(dst, "ufo.webp"))
    m = json.load(open(os.path.join(d, "meta.json"), encoding='utf-8'))
    i0 = m['idle']
    out = dict(cols=5, order=order, head={k: r4(m[k]['head']) for k in order}, headR=r4(i0['headR']),
               emit=r4(i0['emit']), rimL=r4(i0['rimL']), rimR=r4(i0['rimR']), bulbs=r4(i0['bulbs']))
    print(json.dumps(out, separators=(',', ':')))


if __name__ == "__main__":
    {'burger': burger, 'merge': merge}[sys.argv[1]]()
