# -*- coding: utf-8 -*-
"""구미 체인 아틀라스 — scripts/og-assets/gummy/<frame>.png (gummy_blobs.py 렌더) → public/assets/gummy/

- gummy.webp : 젤리 5색 × 표정 6컷 + 설탕 블록 · 물방울 · 포장 사탕 · 별사탕 (gummy_blobs.ORDER 순서, 6열)
- panda.webp : 마스코트 레서판다 컷인용 5컷(cheer·happy·dance1·dance2·cry) — mascot_panda.py 가 이미 찍어 둔
               scripts/og-assets/mascot/*.png 를 그대로 줄여 담는다(판다 모델·렌더는 건드리지 않는다)
- 렌더 프레임을 **자르지 않고** 셀 크기로만 줄인다 → 프레임 정규 좌표가 게임 좌표와 선형으로 맞는다
- 알파는 premultiplied 로 줄인다(투명 픽셀 RGB 가 테두리에 번지는 것 방지)
- 끝에 게임 JS 에 붙일 상수(몸 bbox · 젤리 가장자리 평균색)를 출력한다 → public/games/gummy/index.html 의
  '/*GA:start*/ … /*GA:end*/' 사이에 붙인다

실행: python scripts/build_gummy_atlas.py [--cell 192] [--q 84]
"""
import os
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts", "og-assets", "gummy")
PSRC = os.path.join(ROOT, "scripts", "og-assets", "mascot")
DST = os.path.join(ROOT, "public", "assets", "gummy")
EXPRS = ['n', 'b', 'h', 's', 'w', 'p']
ORDER = ['%d%s' % (c, e) for c in range(1, 6) for e in EXPRS] + ['g', 'd', 'k', 't']
PANDA = ['cheer', 'happy', 'dance1', 'dance2', 'cry']
COLS = 6


def arg(name, dflt):
    if name in sys.argv:
        return type(dflt)(sys.argv[sys.argv.index(name) + 1])
    return dflt


def shrink(im, cell):
    return im.convert("RGBa").resize((cell, cell), Image.LANCZOS).convert("RGBA")


def main():
    cell = arg('--cell', 192)
    q = arg('--q', 84)
    os.makedirs(DST, exist_ok=True)
    rows = (len(ORDER) + COLS - 1) // COLS
    atlas = Image.new("RGBA", (cell * COLS, cell * rows), (0, 0, 0, 0))
    bbox = None
    edge = {}
    for i, n in enumerate(ORDER):
        im = Image.open(os.path.join(SRC, n + ".png")).convert("RGBA")
        W, H = im.size
        bb = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        if bb[0] <= 1 or bb[1] <= 1 or bb[2] >= W - 1 or bb[3] >= H - 1:
            print("WARN clipped", n, bb)
        if n[1:] == 'b':
            # 몸 bbox — 깜빡 컷은 장식이 같고 얼굴이 몸 안이라 몸 윤곽 = 알파 bbox(잎·거품은 위로 삐져나온다 →
            # 좌우·아래만 쓴다)
            a = im.getchannel("A")
            # 몸통 가로폭: 세로 60% 높이에서 잰다
            y = int(H * 0.6)
            xs = [x for x in range(W) if a.getpixel((x, y)) > 128]
            bottom = max(yy for yy in range(H) if a.getpixel((W // 2, yy)) > 128)
            b = (xs[0] / W, xs[-1] / W, bottom / H)
            bbox = b if bbox is None else (min(bbox[0], b[0]), max(bbox[1], b[1]), max(bbox[2], b[2]))
            # 가장자리 평균색 — 몸 윤곽 안쪽 4~9% 띠(목·다리 셰이더 색을 스프라이트 테두리에 맞춘다)
            px = im.load()
            acc = [0, 0, 0, 0]
            for yy in range(int(H * 0.35), int(H * 0.8), 2):
                row = [x for x in range(W) if px[x, yy][3] > 200]
                if not row:
                    continue
                for x in (row[0] + int(W * 0.03), row[-1] - int(W * 0.03)):
                    r, g, bb2, _ = px[x, yy]
                    acc[0] += r
                    acc[1] += g
                    acc[2] += bb2
                    acc[3] += 1
            edge[int(n[0])] = tuple(round(c / acc[3]) for c in acc[:3])
        atlas.paste(shrink(im, cell), ((i % COLS) * cell, (i // COLS) * cell))
    out = os.path.join(DST, "gummy.webp")
    atlas.save(out, "WEBP", quality=q, method=6, alpha_quality=88)
    print("atlas", out, os.path.getsize(out) // 1024, "KB", atlas.size)

    pc = 256
    pa = Image.new("RGBA", (pc * len(PANDA), pc), (0, 0, 0, 0))
    for i, n in enumerate(PANDA):
        pa.paste(shrink(Image.open(os.path.join(PSRC, n + ".png")).convert("RGBA"), pc), (i * pc, 0))
    pout = os.path.join(DST, "panda.webp")
    pa.save(pout, "WEBP", quality=82, method=6, alpha_quality=88)
    print("panda", pout, os.path.getsize(pout) // 1024, "KB", pa.size)

    r4 = lambda v: '%.4f' % v
    print("/*GA:start*/")
    print("const GA_COLS=%d, GA_ORDER='%s'.split(','), GA_BODY={l:%s,r:%s,b:%s}, GA_PANDA='%s'.split(',');" % (
        COLS, ','.join(ORDER), r4(bbox[0]), r4(bbox[1]), r4(bbox[2]), ','.join(PANDA)))
    print("const GA_EDGE=[null,%s];" % ','.join('[%d,%d,%d]' % edge[c] for c in range(1, 6)))
    print("/*GA:end*/")


if __name__ == "__main__":
    main()
