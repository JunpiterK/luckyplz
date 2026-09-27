# -*- coding: utf-8 -*-
"""마스코트 레서판다 렌더(scripts/og-assets/mascot/<frame>.png + meta.json)
→ 아틀라스 public/assets/mascot/panda-bubble.webp + 게임에 붙여 넣을 JS 좌표표 출력.

- 렌더 프레임(직교 카메라, 정사각)을 **자르지 않고** 셀 크기로만 줄인다 → meta.json 의 정규 좌표(0~1)가
  셀 좌표에 그대로 맞는다(발·조이스틱 받침·손잡이·머리)
- 순서 = mascot_panda.ORDER. 게임의 PD 표와 같은 순서여야 한다 — 이 스크립트가 표를 같이 찍으니
  렌더를 다시 하면 출력된 표를 public/games/bubble/index.html 의 '/*PD:start*/ … /*PD:end*/' 사이에 붙인다
- 알파는 premultiplied 로 줄인다(투명 픽셀의 RGB 가 외곽선에 번지는 테두리 방지)

실행: python scripts/build_mascot_atlas.py [--cell 256] [--q 82]
"""
import json
import os
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts", "og-assets", "mascot")
DST = os.path.join(ROOT, "public", "assets", "mascot")
ORDER = ['aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'push0', 'push1', 'push2', 'push3', 'push4',
         'stand', 'swish', 'blink', 'look', 'yawn', 'reload', 'swap', 'happy', 'cheer', 'pout',
         'nervous', 'worry', 'cry', 'dance1', 'dance2']
COLS = 5


def arg(name, dflt):
    if name in sys.argv:
        return type(dflt)(sys.argv[sys.argv.index(name) + 1])
    return dflt


def main():
    cell = arg('--cell', 256)
    q = arg('--q', 82)
    with open(os.path.join(SRC, "meta.json"), encoding='utf-8') as f:
        meta = json.load(f)
    rows = (len(ORDER) + COLS - 1) // COLS
    atlas = Image.new("RGBA", (cell * COLS, cell * rows), (0, 0, 0, 0))
    for i, n in enumerate(ORDER):
        im = Image.open(os.path.join(SRC, n + ".png")).convert("RGBA")
        a = im.getchannel("A").point(lambda v: 255 if v > 8 else 0)
        bb = a.getbbox()
        W, H = im.size
        if bb[0] <= 1 or bb[1] <= 1 or bb[2] >= W - 1 or bb[3] >= H - 1:
            print("WARN clipped", n, bb)
        sm = im.convert("RGBa").resize((cell, cell), Image.LANCZOS).convert("RGBA")
        atlas.paste(sm, ((i % COLS) * cell, (i // COLS) * cell))
    os.makedirs(DST, exist_ok=True)
    out = os.path.join(DST, "panda-bubble.webp")
    atlas.save(out, "WEBP", quality=q, method=6, alpha_quality=90)
    print("atlas", out, os.path.getsize(out) // 1024, "KB", atlas.size)
    m0 = meta[ORDER[0]]
    r = lambda v: '%.4f' % v
    print("/*PD:start*/")
    print("const PD_COLS=%d, PD_N=%d, PD_FEET=[%s,%s], PD_PIV=[%s,%s], PD_REST=[%s,%s], PD_KNOBR=%s, PD_HEADR=%s;" % (
        COLS, len(ORDER), r(m0['feet'][0]), r(m0['feet'][1]), r(m0['pivot'][0]), r(m0['pivot'][1]),
        r(m0['rest'][0]), r(m0['rest'][1]), r(m0['knobR']), r(m0['headR'])))
    parts = []
    for i, n in enumerate(ORDER):
        m = meta[n]
        s = "%s:{i:%d,h:[%s,%s]" % (n, i, r(m['head'][0]), r(m['head'][1]))
        if 'knob' in m:
            s += ",k:[%s,%s]" % (r(m['knob'][0]), r(m['knob'][1]))
        if 'hold' in m:
            s += ",o:[%s,%s]" % (r(m['hold'][0]), r(m['hold'][1]))
        parts.append(s + "}")
    print("const PD={" + ",\n".join(parts) + "};")
    print("/*PD:end*/")


if __name__ == "__main__":
    main()
