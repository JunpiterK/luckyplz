# -*- coding: utf-8 -*-
"""테트로미노 쌓기 — 마스코트 레서판다 리액션 포즈 세트 (2026-09-27 아케이드 임팩트 개편).

운영자: "아케이드는 손맛, 비주얼 효과, 캐릭터성, 이펙트가 어우러져 주는 임팩트가 핵심이야."
판다는 보드 왼쪽(HOLD 아래) 기둥에 서서 판을 지켜보는 응원단이다 — 보드를 절대 가리지 않는다.

모델·스튜디오는 버블 버스트 판다(scripts/blender/mascot_panda.py)를 **import 해서 그대로** 쓴다.
mascot_panda.py · yut_pieces.py 는 수정하지 않는다. 여기서는 포즈 표만 새로 정의한다.
- YAW = +0.3 : 보드(화면 오른쪽)를 향해 몸을 튼다. 정면 = (sinθ, −cosθ)
- 표정 코드는 mascot_panda.face() 의 것(n b h x c s o k p v u l y w)

## 포즈 (ORDER 순서 = 아틀라스 셀 순서 — 게임의 TP 표와 같아야 한다)
  stand · blink · look(판을 올려다봄) · swish(꼬리) · yawn          — 한가할 때
  happy(별눈·트리플/콤보) · cheer(만세·쿼드) · wow(T-스핀·퍼펙트 — 볼 감싸고 놀람)
  clap(박수·줄 지움) · point(시작 — 윙크하며 보드를 가리킴)
  nervous(스택 높음·식은땀) · worry(더 높음·올려다봄) · cry(탑아웃)
  dance1 · dance2(레벨업·스프린트 클리어)

실행 (Blender):
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_tetris.py           # 전부
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_tetris.py -- cheer  # 일부
  MP_SAMPLES=24 ... 로 시안 확인
출력: scripts/og-assets/mascot-tetris/<frame>.png + meta.json
아틀라스 (일반 파이썬, PIL):
  python scripts/blender/mascot_tetris.py atlas
  → public/assets/tetris/panda.webp + 게임에 붙일 JS 좌표표(/*TP:start*/ … /*TP:end*/) 출력
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUTDIR = os.path.join(HERE, "..", "og-assets", "mascot-tetris")
ATLAS = os.path.join(ROOT, "public", "assets", "tetris", "panda.webp")
ORDER = ['stand', 'blink', 'look', 'swish', 'yawn', 'happy', 'cheer', 'wow', 'clap', 'point',
         'nervous', 'worry', 'cry', 'dance1', 'dance2']
COLS = 5

try:
    import bpy  # noqa: F401
except ImportError:
    bpy = None


def build_atlas(cell=256, q=84):
    from PIL import Image
    with open(os.path.join(OUTDIR, "meta.json"), encoding='utf-8') as f:
        meta = json.load(f)
    rows = (len(ORDER) + COLS - 1) // COLS
    atlas = Image.new("RGBA", (cell * COLS, cell * rows), (0, 0, 0, 0))
    for i, n in enumerate(ORDER):
        im = Image.open(os.path.join(OUTDIR, n + ".png")).convert("RGBA")
        a = im.getchannel("A").point(lambda v: 255 if v > 8 else 0)
        bb = a.getbbox()
        W, H = im.size
        if bb and (bb[0] <= 1 or bb[1] <= 1 or bb[2] >= W - 1 or bb[3] >= H - 1):
            print("WARN clipped", n, bb)
        # premultiplied 로 줄여 투명 픽셀 RGB 가 외곽선에 번지지 않게
        sm = im.convert("RGBa").resize((cell, cell), Image.LANCZOS).convert("RGBA")
        atlas.paste(sm, ((i % COLS) * cell, (i // COLS) * cell))
    os.makedirs(os.path.dirname(ATLAS), exist_ok=True)
    atlas.save(ATLAS, "WEBP", quality=q, method=6, alpha_quality=90)
    print("atlas", ATLAS, os.path.getsize(ATLAS) // 1024, "KB", atlas.size)
    r = lambda v: '%.4f' % v
    m0 = meta[ORDER[0]]
    print("/*TP:start*/")
    print("const TP_COLS=%d, TP_FEET=[%s,%s], TP_HEADR=%s;" % (COLS, r(m0['feet'][0]), r(m0['feet'][1]), r(m0['headR'])))
    parts = []
    for i, n in enumerate(ORDER):
        m = meta[n]
        parts.append("%s:{i:%d,h:[%s,%s]}" % (n, i, r(m['head'][0]), r(m['head'][1])))
    print("const TP={" + ",\n".join(parts) + "};")
    print("/*TP:end*/")


if bpy is None:
    if __name__ == "__main__":
        build_atlas()
    sys.exit(0)

# ════════════ Blender 쪽 ════════════
sys.path.insert(0, HERE)
import mascot_panda as mp  # noqa: E402  (모델 원본 — 수정하지 않고 헬퍼만 쓴다)

os.makedirs(OUTDIR, exist_ok=True)
mp.OUTDIR = OUTDIR          # render_frame 이 모듈 전역을 읽는다
mp.YAW = 0.3                # 보드(화면 오른쪽)를 본다
fr = mp.fr

UP = ((0.98, -0.34, 1.22), (-0.98, -0.34, 1.22))
HIGH = ((1.06, -0.3, 1.62), (-1.06, -0.3, 1.62))
CHEEK = ((0.8, -0.36, 1.16), (-0.8, -0.36, 1.16))
CLAP = ((0.07, -0.78, 1.02), (-0.07, -0.78, 1.02))
_hip = mp.yp.DPOSE['hip']
_m = lambda v: (-v[0], v[1], v[2])

FR = {
    'stand': fr('n'),
    'blink': fr('b'),
    'look': fr('l', hfwd=-0.22, hroll=0.1),
    'swish': fr('n', tail=0.55, hroll=0.05),
    'yawn': fr('y', ((0.1, -0.84, 1.1), (-0.2, -0.48, 0.5)), hfwd=-0.12, roll=0.04),
    'happy': fr('x', UP, hfwd=-0.05),
    'cheer': fr('h', HIGH, hfwd=-0.08, feet=((0.32, -0.06, 0.07), (-0.32, -0.06, 0.07))),
    'wow': fr('o', CHEEK, hfwd=-0.06, droop=0.1),
    'clap': fr('h', CLAP, fwd=0.05, hfwd=-0.04),
    'point': fr('w', ((1.04, -0.42, 1.08), (-0.2, -0.48, 0.5)), roll=0.07, hroll=0.08),
    'nervous': fr('v', mp.CHIN, droop=0.4, fwd=0.04),
    'worry': fr('u', ((0.3, -0.6, 0.72), (-0.3, -0.6, 0.72)), hfwd=-0.2, droop=0.3),
    'cry': fr('c', mp.CHIN, droop=1.0, hfwd=0.08),
    'dance1': fr('h', (_hip['R'], _hip['L']), feet=_hip['feet'], roll=_hip['roll'], hroll=_hip['hroll']),
    'dance2': fr('x', (_m(_hip['L']), _m(_hip['R'])), feet=(_m(_hip['feet'][1]), _m(_hip['feet'][0])),
                 roll=-_hip['roll'], hroll=-_hip['hroll']),
}
for k, v in FR.items():
    mp.FRAMES['t_' + k] = v

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = argv[0].split(',') if argv else ORDER
    mpath = os.path.join(OUTDIR, "meta.json")
    meta = {}
    if os.path.exists(mpath):
        with open(mpath, encoding='utf-8') as f:
            meta = json.load(f)
    for n in names:
        mm = mp.render_frame('t_' + n)
        src = os.path.join(OUTDIR, 't_' + n + '.png')
        dst = os.path.join(OUTDIR, n + '.png')
        if os.path.exists(dst):
            os.remove(dst)
        os.rename(src, dst)
        meta[n] = mm
        with open(mpath, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=1)
