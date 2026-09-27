# -*- coding: utf-8 -*-
"""벽돌깨기 — 마스코트 레서판다 '패들 카트 운전수' 포즈 세트 (2026-09-27 아케이드 임팩트 개편).

운영자: "아케이드는 손맛, 비주얼 효과, 캐릭터성, 이펙트가 어우러져 주는 임팩트가 핵심이야."
판다가 호버 카트(욕조 모양 범퍼카)에 타고 두 앞발로 테두리를 잡은 채 좌우로 달린다.
패들은 카트 위 두 기둥이 받치는 범퍼 바다. 카트·기둥·패들·분사 불꽃은 게임 캔버스가 그리고,
이 스크립트는 **판다만** 렌더한다(허리 아래는 카트 앞판에 가려진다).

모델·스튜디오는 버블 버스트 판다(scripts/blender/mascot_panda.py)를 **import 해서 그대로** 쓴다.
mascot_panda.py · yut_pieces.py 는 수정하지 않는다. 여기서는 포즈 표만 새로 정의한다.
- YAW = 0 : 정면. 공이 위에서 오므로 판다는 정면으로 판을 올려다본다
- 손 = 카트 테두리(RIM). meta 의 'rim' = 두 손 가운데의 셀 좌표 → 게임이 카트 테두리를 여기에 맞춘다

## 포즈 (ORDER 순서 = 아틀라스 셀 순서 — 게임의 BP 표와 같아야 한다)
  drive · blink · leanL · leanR(패들 이동 방향으로 몸이 쏠림) · look(공을 올려다봄)
  strain(>< — 공 받는 순간) · happy(별눈 — 콤보) · cheer(만세 — 스테이지 클리어·큰 연쇄)
  wow(놀람 — 파워업) · nervous(마지막 목숨) · worry(공이 떨어질 듯) · pout(함정 '축소')
  cry(목숨 잃음·게임 오버) · dance1 · dance2(스테이지 클리어)

실행 (Blender):
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_brick.py            # 전부
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_brick.py -- drive   # 일부
출력: scripts/og-assets/mascot-brick/<frame>.png + meta.json
아틀라스 (일반 파이썬, PIL):
  python scripts/blender/mascot_brick.py atlas
  → public/assets/brick/panda.webp + 게임에 붙일 JS 좌표표(/*BP:start*/ … /*BP:end*/) 출력
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUTDIR = os.path.join(HERE, "..", "og-assets", "mascot-brick")
ATLAS = os.path.join(ROOT, "public", "assets", "brick", "panda.webp")
ORDER = ['drive', 'blink', 'leanL', 'leanR', 'look', 'strain', 'happy', 'cheer', 'wow',
         'nervous', 'worry', 'pout', 'cry', 'dance1', 'dance2']
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
        sm = im.convert("RGBa").resize((cell, cell), Image.LANCZOS).convert("RGBA")
        atlas.paste(sm, ((i % COLS) * cell, (i // COLS) * cell))
    os.makedirs(os.path.dirname(ATLAS), exist_ok=True)
    atlas.save(ATLAS, "WEBP", quality=q, method=6, alpha_quality=90)
    print("atlas", ATLAS, os.path.getsize(ATLAS) // 1024, "KB", atlas.size)
    r = lambda v: '%.4f' % v
    m0 = meta[ORDER[0]]
    print("/*BP:start*/")
    print("const BP_COLS=%d, BP_FEET=[%s,%s], BP_HEADR=%s;" % (COLS, r(m0['feet'][0]), r(m0['feet'][1]), r(m0['headR'])))
    parts = []
    for i, n in enumerate(ORDER):
        m = meta[n]
        s = "%s:{i:%d,h:[%s,%s]" % (n, i, r(m['head'][0]), r(m['head'][1]))
        if 'rim' in m:
            s += ",r:[%s,%s]" % (r(m['rim'][0]), r(m['rim'][1]))
        parts.append(s + "}")
    print("const BP={" + ",\n".join(parts) + "};")
    print("/*BP:end*/")


if bpy is None:
    if __name__ == "__main__":
        build_atlas()
    sys.exit(0)

# ════════════ Blender 쪽 ════════════
from mathutils import Vector  # noqa: E402
sys.path.insert(0, HERE)
import mascot_panda as mp  # noqa: E402  (모델 원본 — 수정하지 않고 헬퍼만 쓴다)

os.makedirs(OUTDIR, exist_ok=True)
mp.OUTDIR = OUTDIR
mp.YAW = 0.0
fr = mp.fr

RIM = ((0.47, -0.66, 0.66), (-0.47, -0.66, 0.66))       # 카트 테두리를 쥔 두 앞발
UP = ((0.98, -0.34, 1.22), (-0.98, -0.34, 1.22))
HIGH = ((1.06, -0.3, 1.62), (-1.06, -0.3, 1.62))
_hip = mp.yp.DPOSE['hip']
_m = lambda v: (-v[0], v[1], v[2])

FR = {
    'drive': fr('n', RIM, fwd=0.08),
    'blink': fr('b', RIM, fwd=0.08),
    'leanL': fr('n', RIM, fwd=0.1, roll=-0.24, hroll=-0.14),
    'leanR': fr('n', RIM, fwd=0.1, roll=0.24, hroll=0.14),
    'look': fr('l', RIM, fwd=0.04, hfwd=-0.24),
    'strain': fr('k', RIM, fwd=0.2, hfwd=0.05, droop=0.1),
    'happy': fr('x', UP, hfwd=-0.05),
    'cheer': fr('h', HIGH, hfwd=-0.08),
    'wow': fr('o', RIM, fwd=0.02, hfwd=-0.12),
    'nervous': fr('v', RIM, droop=0.4, fwd=0.06),
    'worry': fr('u', RIM, hfwd=-0.22, droop=0.3),
    'pout': fr('p', RIM, hroll=0.14, droop=0.25, fwd=0.06),
    'cry': fr('c', mp.CHIN, droop=1.0, hfwd=0.08),
    'dance1': fr('h', (_hip['R'], _hip['L']), feet=_hip['feet'], roll=_hip['roll'], hroll=_hip['hroll']),
    'dance2': fr('x', (_m(_hip['L']), _m(_hip['R'])), feet=(_m(_hip['feet'][1]), _m(_hip['feet'][0])),
                 roll=-_hip['roll'], hroll=-_hip['hroll']),
}
for k, v in FR.items():
    mp.FRAMES['b_' + k] = v

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = argv[0].split(',') if argv else ORDER
    mpath = os.path.join(OUTDIR, "meta.json")
    meta = {}
    if os.path.exists(mpath):
        with open(mpath, encoding='utf-8') as f:
            meta = json.load(f)
    for n in names:
        mm = mp.render_frame('b_' + n)
        # 카트 테두리 = 기본 운전 자세(RIM)의 두 손 가운데 — 몸을 기울여도 테두리는 카트에 붙어 있으므로
        # 기울지 않은 RIM 기준 한 점을 쓴다(발 기준 오프셋)
        sc = bpy.context.scene
        rim = (Vector(RIM[0]) + Vector(RIM[1])) / 2
        mm['rim'] = mp.proj(sc, rim + Vector((0, 0, -0.02)))
        src = os.path.join(OUTDIR, 'b_' + n + '.png')
        dst = os.path.join(OUTDIR, n + '.png')
        if os.path.exists(dst):
            os.remove(dst)
        os.rename(src, dst)
        meta[n] = mm
        with open(mpath, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=1)
