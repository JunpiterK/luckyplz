# -*- coding: utf-8 -*-
"""요트 다이스 — 마스코트 레서판다 '진행자' 포즈 세트 + 가족 봇 2명 + 주사위 컵 (2026-09-30).

게임(public/games/yacht)에서 판다는 트레이 옆에 앉아 굴림을 지켜보고(peek), 좋은 패에 기뻐하고(happy·cheer),
0점에 울고(cry), 세 번째 굴림에 긴장한다(nervous). 봇 차례에는 컵을 직접 흔든다(shakeA/B).
봇 가족: 럭키(본체) · 루비(분홍 리본) · 캡틴(세일러 모자 — yacht 말장난).

모델·스튜디오는 버블 버스트 판다(scripts/blender/mascot_panda.py)를 **import 해서 그대로** 쓴다.
mascot_panda.py · yut_pieces.py 는 수정하지 않는다. 여기서는 포즈 표와 소품(컵·리본·모자)만 정의한다.

## 셀 순서 (ORDER = 아틀라스 셀 순서 — 게임의 YP 표와 같아야 한다)
  idle · blink · peek(트레이를 내려다봄) · happy(별눈) · cheer(만세) · wow(놀람) · nervous(세 번째 굴림)
  worry · pout(아깝다) · cry(0점) · dance1 · dance2(요트!) · wink · wave(첫 화면 인사)
  shakeA · shakeB(컵 흔들기) · ruby(리본) · cap(세일러 모자) · cupUp(세운 컵) · cupPour(쏟는 컵)

실행 (Blender):
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_yacht.py            # 전부
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_yacht.py -- cheer,cry
  MP_SAMPLES=24 로 시안 확인
출력: scripts/og-assets/mascot-yacht/<frame>.png + meta.json   (중간 산출물 — 저장소에 올리지 않는다)
아틀라스 (일반 파이썬, PIL):
  python scripts/blender/mascot_yacht.py atlas
  → public/assets/yacht/panda.webp + 게임에 붙일 JS 좌표표(/*YP:start*/ … /*YP:end*/) 출력
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUTDIR = os.path.join(HERE, "..", "og-assets", "mascot-yacht")
ATLAS = os.path.join(ROOT, "public", "assets", "yacht", "panda.webp")
ORDER = ['idle', 'blink', 'peek', 'happy', 'cheer', 'wow', 'nervous',
         'worry', 'pout', 'cry', 'dance1', 'dance2', 'wink', 'wave',
         'shakeA', 'shakeB', 'ruby', 'cap', 'cupUp', 'cupPour']
COLS = 7

try:
    import bpy  # noqa: F401
except ImportError:
    bpy = None


def build_atlas(cell=256, q=82):
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
    parts = []
    for i, n in enumerate(ORDER):
        m = meta[n]
        s = "%s:{i:%d" % (n, i)
        if 'head' in m:
            s += ",h:[%s,%s]" % (r(m['head'][0]), r(m['head'][1]))
        if 'box' in m:
            s += ",b:[%s]" % ",".join(r(v) for v in m['box'])
        parts.append(s + "}")
    print("/*YP:start*/")
    print("const YP_COLS=%d,YP_HEADR=%s;" % (COLS, r(meta['idle']['headR'])))
    print("const YP={" + ",".join(parts) + "};")
    print("/*YP:end*/")


if bpy is None:
    if __name__ == "__main__":
        build_atlas()
    sys.exit(0)

# ════════════ Blender 쪽 ════════════
from mathutils import Vector, Matrix  # noqa: E402
sys.path.insert(0, HERE)
import mascot_panda as mp  # noqa: E402  (모델 원본 — 수정하지 않고 헬퍼만 쓴다)

yp = mp.yp
os.makedirs(OUTDIR, exist_ok=True)
mp.OUTDIR = OUTDIR
mp.YAW = 0.0
fr = mp.fr

REST = mp.REST
CHIN = mp.CHIN
UP = ((0.98, -0.34, 1.22), (-0.98, -0.34, 1.22))
HIGH = ((1.06, -0.3, 1.62), (-1.06, -0.3, 1.62))
EDGE = ((0.42, -0.62, 0.58), (-0.42, -0.62, 0.58))          # 트레이 테두리에 올린 두 앞발
HOLD = ((0.36, -0.6, 0.74), (-0.36, -0.6, 0.74))            # 컵을 양옆에서 쥔 앞발
_hip = yp.DPOSE['hip']
_m = lambda v: (-v[0], v[1], v[2])

FR = {
    'idle': fr('n', REST),
    'blink': fr('b', REST),
    'peek': fr('n', EDGE, fwd=0.2, hfwd=0.2),
    'happy': fr('x', UP, hfwd=-0.05),
    'cheer': fr('h', HIGH, hfwd=-0.08, feet=((0.32, -0.06, 0.07), (-0.32, -0.06, 0.07))),
    'wow': fr('o', ((0.62, -0.5, 0.9), (-0.62, -0.5, 0.9)), hfwd=-0.06),
    'nervous': fr('v', CHIN, droop=0.4, fwd=0.06),
    'worry': fr('u', ((0.3, -0.6, 0.72), (-0.3, -0.6, 0.72)), hfwd=-0.16, droop=0.3),
    'pout': fr('p', ((-0.22, -0.64, 0.66), (0.22, -0.6, 0.6)), hroll=0.14, droop=0.25),
    'cry': fr('c', CHIN, droop=1.0, hfwd=0.08),
    'dance1': fr('h', (_hip['R'], _hip['L']), feet=_hip['feet'], roll=_hip['roll'], hroll=_hip['hroll']),
    'dance2': fr('x', (_m(_hip['L']), _m(_hip['R'])), feet=(_m(_hip['feet'][1]), _m(_hip['feet'][0])),
                 roll=-_hip['roll'], hroll=-_hip['hroll']),
    'wink': fr('w', ((0.2, -0.48, 0.5), (-1.02, -0.42, 1.08)), roll=-0.07, hroll=-0.08),
    'wave': fr('h', ((0.96, -0.36, 1.36), (-0.15, -0.44, 0.5)), roll=0.05, hroll=0.1, tail=0.4),
    'shakeA': fr('k', HOLD, roll=-0.13, hroll=-0.1, fwd=0.06),
    'shakeB': fr('h', HOLD, roll=0.13, hroll=0.1, fwd=0.06, tail=0.45),
    'ruby': fr('h', ((0.62, -0.5, 1.12), (-0.15, -0.44, 0.5)), hroll=0.08),
    'cap': fr('n', ((0.2, -0.48, 0.5), (-0.62, -0.52, 1.16)), hroll=-0.06),
}
for k, v in FR.items():
    mp.FRAMES['y_' + k] = v


# ── 소품 ─────────────────────────────────────────────────────────
def lathe(profile, m, seg=56):
    """(r, z) 단면을 z 축으로 돌린 회전체."""
    import bmesh
    me = bpy.data.meshes.new("lathe")
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r <= 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), z))
                          for i in range(seg)])
    for ra, rb in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            if len(ra) == 1 and len(rb) == 1:
                break
            if len(ra) == 1:
                bm.faces.new((ra[0], rb[i], rb[j]))
            elif len(rb) == 1:
                bm.faces.new((ra[i], ra[j], rb[0]))
            else:
                bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("lathe", me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    try:
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    except Exception:
        pass
    return o


def cup(center, tilt_y=0.0, tilt_x=0.0, s=1.0):
    """가죽 주사위 컵 — 진한 빨강 원뿔대(속이 빈 회전체) + 금테 + 크림 스티치 띠 + 어두운 안감. center = 바닥 중심."""
    red = yp.mat('cup_red', (0.60, 0.05, 0.04), rough=0.42, coat=0.55)
    gold = yp.mat('cup_gold', (0.95, 0.70, 0.22), rough=0.2, metal=1.0, coat=0.0)
    cream = yp.mat('cup_cream', (0.96, 0.90, 0.76), rough=0.5, coat=0.2)
    inn = yp.mat('cup_in', (0.07, 0.015, 0.02), rough=0.8, coat=0.0)
    before = set(bpy.data.objects)
    h, r0, r1 = 0.62 * s, 0.25 * s, 0.34 * s
    t = 0.035 * s
    lathe([(r0, 0.012 * s), (r1, h)], red)          # 바닥은 금색 받침 원판이 맡는다(같은 높이에 두 면이 겹치면 얼룩진다)
    lathe([(r1 - 0.004 * s, h - 0.002 * s), (r0 - t * 0.4, t * 1.6), (0, t * 1.6)], inn)
    yp.cyl(r0 * 1.03, 0.05 * s, (0, 0, 0.025 * s), gold, bevel=0.015)
    yp.torus(r1 - 0.004 * s, 0.034 * s, (0, 0, h), gold)
    yp.torus((r0 + (r1 - r0) * 0.36) * 1.01, 0.02 * s, (0, 0, h * 0.36), cream)
    new = [o for o in bpy.data.objects if o not in before]
    M = Matrix.Translation(Vector(center)) @ Matrix.Rotation(tilt_y, 4, 'Y') @ Matrix.Rotation(tilt_x, 4, 'X')
    mp.apply(new, M)
    return new


def bow(H):
    """루비 — 오른쪽 귀 밑 분홍 리본(머리 표면에 붙인다)."""
    pink = yp.mat('bow', (1.0, 0.28, 0.52), rough=0.25, coat=0.9)
    dpk = yp.mat('bow_d', (0.85, 0.12, 0.36), rough=0.3, coat=0.8)
    x, dz = 0.47, 0.5
    for s, rz in ((-1, 0.35), (1, -0.15)):
        yp.feat(H, x + s * 0.17, dz + (0.03 if s < 0 else -0.04), 0.17, pink, scale=(1.0, 0.5, 0.78), lift=0.07)
    yp.feat(H, x, dz, 0.085, dpk, scale=(1.0, 0.7, 1.0), lift=0.13)


def sailor(H):
    """캡틴 — 두 귀 사이 작은 세일러 모자(흰 윗판 + 남색 띠 + 챙 + 금 닻 점)."""
    white = yp.mat('hat_w', (0.97, 0.97, 0.95), rough=0.4, coat=0.4)
    navy = yp.mat('hat_n', (0.05, 0.10, 0.32), rough=0.35, coat=0.6)
    gold = yp.mat('cup_gold', (0.95, 0.70, 0.22), rough=0.2, metal=1.0, coat=0.0)
    before = set(bpy.data.objects)
    top = 1.5 + (yp.HC - 0.02)
    yp.cyl(0.3, 0.12, (0, 0, 0.06), navy, bevel=0.03)
    yp.sph(0.4, (0, 0, 0.2), white, scale=(1.0, 1.0, 0.42))
    yp.sph(0.26, (0, -0.27, 0.03), navy, scale=(1.0, 0.75, 0.16))
    yp.sph(0.055, (0, -0.3, 0.12), gold, scale=(1, 0.6, 1))
    new = [o for o in bpy.data.objects if o not in before]
    M = Matrix.Translation(Vector((-0.04, -0.12, top - 0.07))) @ Matrix.Rotation(0.2, 4, 'X') @ Matrix.Rotation(-0.1, 4, 'Y')
    mp.apply(new, M)


def render_pose(name):
    sc = mp.studio()
    before0 = set(bpy.data.objects)
    spec, ZM, Hm, knob = mp.build_frame('y_' + name)
    before = set(bpy.data.objects)
    if name in ('shakeA', 'shakeB'):
        t = -0.42 if name == 'shakeA' else 0.42
        cup((0.0 + (0.05 if t > 0 else -0.05), -0.66, 0.4), tilt_y=t, s=1.12)
        mp.apply([o for o in bpy.data.objects if o not in before], ZM)
    elif name in ('ruby', 'cap'):
        H = yp.Head(yp.HEAD_C, yp.HA + 0.02, yp.HB, yp.HC - 0.02)
        (bow if name == 'ruby' else sailor)(H)
        mp.apply([o for o in bpy.data.objects if o not in before], ZM @ Hm)
    sc.render.filepath = os.path.join(OUTDIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    head_c = ZM @ (Hm @ Vector(yp.HEAD_C))
    print("RENDERED", name)
    return dict(feet=mp.proj(sc, (0, 0, 0)), head=mp.proj(sc, head_c), headR=round(yp.HA / mp.ORTHO, 5))


def render_cup(name):
    """컵만 — 위에서 내려다본 각(트레이와 같은 시점에 가깝게). cupUp=세움, cupPour=왼쪽 아래로 쏟는 중."""
    sc = mp.studio()
    cam = sc.camera
    cam.data.ortho_scale = 2.1
    d = Vector((0.0, -6.2, 7.4)).normalized()
    tgt = Vector((0, 0, 0.5))
    cam.location = tgt + d * 14.0
    cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
    if name == 'cupUp':
        cup((0, 0, 0.0), s=1.75)
        box = [(-0.62, 0, 0), (0.62, 0, 1.12)]
    else:
        # 입이 왼쪽 아래 앞(트레이 쪽)을 향해 기운다 — 어두운 안쪽이 보여야 '쏟는 컵'으로 읽힌다.
        # 게임에서 컵은 트레이 위쪽 띠(판다 옆)에 있고 주사위는 아래로 쏟아진다
        new = cup((0, 0, 0.0), s=1.75)
        hh = 0.62 * 1.75 / 2
        q = Vector((-0.5, -0.62, -0.46)).to_track_quat('Z', 'Y')
        M = Matrix.Translation(Vector((0.1, 0.0, 0.62))) @ q.to_matrix().to_4x4() @ Matrix.Translation(Vector((0, 0, -hh)))
        mp.apply(new, M)
    sc.render.filepath = os.path.join(OUTDIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)
    return dict(base=mp.proj(sc, (0, 0, 0)))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = argv[0].split(',') if argv else ORDER
    mpath = os.path.join(OUTDIR, "meta.json")
    meta = {}
    if os.path.exists(mpath):
        with open(mpath, encoding='utf-8') as f:
            meta = json.load(f)
    for n in names:
        mm = render_cup(n) if n.startswith('cup') else render_pose(n)
        # mascot_panda.build_frame 은 'y_<name>' 으로 짓지만 파일은 <name>.png 로 바로 저장한다
        meta[n] = mm
        with open(mpath, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=1)
