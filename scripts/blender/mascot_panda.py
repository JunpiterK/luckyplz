# -*- coding: utf-8 -*-
"""luckyplz 마스코트 레서판다 — 버블 버스트 발사대 조작 포즈 세트 (2026-09-27).

운영자: "luckyplz 의 마스코트로 귀여운 레서팬더를 지정할 거야. 지금 버블버스트에서도
랫서팬더가 버블 쏘는 기구부를 움직이는 걸로 표현해줘."

모델 원본은 윷놀이 말(scripts/blender/yut_pieces.py)의 랫서팬더다 — 같은 얼굴이어야 사이트 마스코트로
기억된다. 헬퍼(Head·Face·patch·body·재질)는 **import 해서 그대로 쓰고**, 몸 조립만 여기서 한다
(꼬리 흔들기·귀 처짐·조이스틱 손 위치가 필요해서). yut_pieces.py 는 수정하지 않는다 —
표정 추가는 이 파일 안의 face() 에서만 한다.

## 무대
- 두 발로 선 치비(윷 군무 자세와 같은 _DANCE 경로) + 살짝 왼쪽(발사대 쪽)으로 몸을 튼다(YAW)
- 조작 = 바닥 조이스틱. 발 앞 PIVOT 에서 올라온 막대 끝 빨간 공 손잡이를 두 앞발로 쥔다.
  잡는 프레임(aim*·push*)만 막대·손잡이가 스프라이트에 들어 있고, 받침(베이스)과 기계로 가는 케이블은
  게임 캔버스가 그린다 — 손을 놓은 포즈에서는 캔버스가 같은 자리에 막대를 그린다
- 카메라는 **직교(ortho)** — 스프라이트 셀 좌표가 월드와 선형이라 발·받침·손잡이·머리 위치를
  meta.json 으로 뽑아 게임 좌표표에 그대로 옮긴다(build_mascot_atlas.py 가 JS 표를 출력)

## 포즈 (FRAMES)
  aim0..4   조준 — 막대 기울기 T[i], 몸이 같은 쪽으로 기운다(0 = 가장 왼쪽)
  push0..4  발사 — 손잡이를 눌러 막대가 짧아지고 몸을 숙인다, 힘주는 >< 얼굴
  stand · swish(꼬리 흔듦) · blink · look(버블 올려다보기) · yawn        — 한가할 때
  reload(다음 버블을 두 손에 들고) · swap(윙크하며 왼쪽 가리키기)          — 장전·교체
  happy(별눈 · 콤보) · cheer(만세 · 큰 낙하) · pout(헛방) · nervous(새 줄 · 식은땀)
  worry(위험선 · 걱정스레 올려다봄) · cry(게임 오버) · dance1/2(스테이지 클리어)

실행:
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_panda.py              # 전부
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_panda.py -- aim2,cheer # 일부
  MP_SAMPLES=24 ... 로 시안 확인
출력: scripts/og-assets/mascot/<frame>.png + meta.json → python scripts/build_mascot_atlas.py
      → public/assets/mascot/panda-bubble.webp
"""
import bpy
import json
import math
import os
import sys
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yut_pieces as yp  # noqa: E402  (모델 원본 — 수정하지 않고 헬퍼만 쓴다)

OUTDIR = os.path.join(HERE, "..", "og-assets", "mascot")
os.makedirs(OUTDIR, exist_ok=True)
RES = int(os.environ.get('MP_RES', '512'))
SAMPLES = int(os.environ.get('MP_SAMPLES', '72'))
ORTHO = 3.0                 # 셀 한 변 = 월드 3.0 — 만세 팔(±1.3)·귀 끝(2.45)까지 들어간다
CAM_TGT = Vector((0.0, 0.0, 1.08))
CAM_DIR = Vector((0.0, -9.2, 3.6)).normalized()   # 윷 말과 같은 ≈21° 내려다보기
YAW = -0.2                  # 발사대(화면 왼쪽)로 살짝 몸을 튼다. 정면 = (sinθ, −cosθ)

NECK = Vector((0, -0.05, 0.92))
PIV_BODY = Vector((0, -0.02, 0.3))
HIP = (0.18, -0.02, 0.3)
FEET = ((0.26, -0.06, 0.07), (-0.26, -0.06, 0.07))

# 조이스틱 — 최종 월드 좌표(YAW 뒤). 받침 중심 = 막대 아래 끝
PIVOT = Vector((-0.1, -0.8, 0.06))
STICK = 0.72
KNOB_R = 0.16
T = [-0.5, -0.25, 0.0, 0.25, 0.5]


def stick_tip(t, L=1.0):
    return PIVOT + STICK * L * Vector((math.sin(t), 0.0, math.cos(t)))


# ════════════ 스튜디오 — 윷 말 스튜디오 + 직교 카메라 ════════════
def studio():
    sc = yp.studio()
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.cycles.samples = SAMPLES
    th = 3.3 * RES / 512.0     # 셀(224px)로 줄였을 때 윷 말과 비슷한 잉크 굵기
    sc.render.line_thickness = th
    ls = bpy.context.view_layer.freestyle_settings.linesets[0]
    ls.linestyle.thickness = th
    # 게임 배경이 짙은 남색이라 윷판용 보랏빛 잉크(sRGB≈76,64,86)는 밝은 테두리로 떠 보인다 →
    # 버블 스프라이트의 잉크(rgba 14,8,30)와 같은 먹색
    ls.linestyle.color = (0.004, 0.0025, 0.012)
    # 얼굴 이목구비(눈·입·볼)는 선을 긋지 않는다 — 하이라이트마다 먹선 고리가 생겨 폰 크기(머리 ≈30px)에서
    # 눈이 뭉개진다. face() 가 만든 오브젝트를 이 컬렉션으로 옮긴다
    fc = bpy.data.collections.new("FACE")
    sc.collection.children.link(fc)
    cam = sc.camera
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ORTHO
    cam.location = CAM_TGT + CAM_DIR * 14.0
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (-CAM_DIR).to_track_quat('-Z', 'Y')
    cam.data.clip_end = 60
    return sc


def body_matrix(fwd, roll):
    p = PIV_BODY
    return Matrix.Translation(p) @ Matrix.Rotation(roll, 4, 'Y') @ Matrix.Rotation(fwd, 4, 'X') @ Matrix.Translation(-p)


def head_matrix(hfwd, hroll):
    p = NECK
    return Matrix.Translation(p) @ Matrix.Rotation(hroll, 4, 'Y') @ Matrix.Rotation(hfwd, 4, 'X') @ Matrix.Translation(-p)


def apply(objs, M):
    bpy.context.view_layer.update()
    for o in objs:
        if o.parent is None:
            o.matrix_world = M @ o.matrix_world


# ════════════ 얼굴 — 윷 표정 + 버블 전용 표정 ════════════
def eyes_up(F):
    """올려다보는 눈 — 동공·하이라이트를 위로, 밝은 홍채는 가운데로"""
    H, er = F.H, F.er
    for s in (-1, 1):
        x, ez = s * F.ex, F.ez
        yp.feat(H, x, ez, er, F.IRd, scale=(0.86, 0.42, 1.1))
        yp.feat(H, x, ez - er * 0.05, er * 0.6, F.IR, scale=(0.95, 0.4, 0.6), lift=0.012)
        yp.feat(H, x, ez + er * 0.42, er * 0.46, F.D, scale=(0.9, 0.4, 1.0), lift=0.022)
        yp.feat(H, x - er * 0.28, ez + er * 0.62, er * 0.32, F.W, scale=(1, 0.4, 1), lift=0.045, seg=20)
        yp.feat(H, x + er * 0.32, ez - er * 0.12, er * 0.15, F.W, scale=(1, 0.4, 1), lift=0.045, seg=16)


def sweat(H, big=1.0):
    """식은땀 — 이마 왼쪽 옆(화면 왼쪽)에 큰 물방울"""
    m = yp.mat('tear', (0.45, 0.80, 1.0), rough=0.05, coat=1.0, emit=(0.4, 0.75, 1.0), estr=0.5)
    p, n = H.pt(-0.62, 0.26, 0.07)
    yp.sph(0.1 * big, p, m, scale=(0.8, 0.5, 1.15), rot=H.rot(n))
    yp.cone(0.075 * big, 0.004, 0.13 * big, p + Vector((0.012, -0.01, 0.12 * big)), m, rot=(0, math.radians(-8), 0))


def mouth_wavy(F):
    H, mz = F.H, F.mouth - 0.02
    pts = [(-0.1, 0), (-0.05, 0.025), (0.0, 0), (0.05, 0.025), (0.1, 0)]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        yp.line(H, x0, mz + z0, x1, mz + z1, 0.016, F.K, lift=0.02)


def lids(F, fur):
    """시큰둥한 반쯤 감은 눈 — 털색 눈꺼풀이 위를 덮고 아래 잉크 선"""
    H, er = F.H, F.er
    for s in (-1, 1):
        x, ez = s * F.ex, F.ez
        yp.feat(H, x, ez + er * 0.62, er * 1.06, fur, scale=(0.98, 0.5, 0.62), lift=0.05)
        yp.line(H, x - er * 0.9, ez + er * (0.22 if s < 0 else 0.1), x + er * 0.9, ez + er * (0.1 if s < 0 else 0.22),
                0.022, F.K, lift=0.075)


def face(F, ex, fur):
    H = F.H
    if ex in ('n', 'b', 'h', 'x', 'c', 's', 'o'):
        F.build(ex, 'panda')
    elif ex == 'k':            # 힘주기 — 꼭 감은 >< + '읏!' 입
        for s in (-1, 1):
            F.squeeze(s)
        F.mouth_open(0.09, 0.7, tongue=False)
        yp.blush(H, F.bx, F.bz, 1.3)
    elif ex == 'p':            # 뾰로통 — 반쯤 감은 눈 + 삐죽 입 + 진한 볼
        F.eyes(scale=0.98)
        lids(F, fur)
        yp.arc(H, 0.02, F.mouth - 0.03, 0.1, 0.03, 0.017, F.K, n=5, lift=0.02)
        yp.blush(H, F.bx, F.bz, 1.5)
    elif ex == 'v':            # 긴장 — 작아진 눈동자 + 물결 입 + 식은땀
        for s in (-1, 1):
            F.eye_small(s)
        mouth_wavy(F)
        sweat(H)
        yp.blush(H, F.bx, F.bz, 0.4)
    elif ex == 'u':            # 걱정스레 올려다봄 — 위로 뜬 눈 + 작은 o 입 + 식은땀
        eyes_up(F)
        F.mouth_o()
        sweat(H, 0.85)
        yp.blush(H, F.bx, F.bz, 0.5)
    elif ex == 'l':            # 궁금 — 위로 뜬 눈 + 고양이 입
        eyes_up(F)
        F.mouth_w()
        yp.blush(H, F.bx, F.bz, 0.7)
    elif ex == 'y':            # 하품 — 감은 눈 + 크게 벌린 입
        for s in (-1, 1):
            yp.arc(H, s * F.ex, F.ez - 0.01, F.er * 1.9, -0.03, 0.026, F.K, lift=0.02)
        F.mouth_open(0.13, 1.35)
        yp.blush(H, F.bx, F.bz, 0.8)
    elif ex == 'w':            # 윙크 + 메롱 (교체)
        F.eye(-1, big=True)
        yp.arc(H, F.ex, F.ez, F.er * 2.0, 0.085, 0.028, F.K, lift=0.02)
        F.mouth_bleh()
        yp.blush(H, F.bx, F.bz, 1.2)
    else:
        raise ValueError(ex)


# ════════════ 몸 — yut_pieces.panda() 와 같은 조립 + 꼬리·귀 매개변수 ════════════
def build_panda(ex, droop=0.0, tail=0.0):
    fur = yp.mat('rp_fur', (0.86, 0.30, 0.07), rough=0.42, coat=0.35, sheen=0.25)
    white = yp.mat('rp_white', (0.99, 0.96, 0.91), rough=0.45, coat=0.3)
    dark = yp.mat('rp_dark', (0.2, 0.07, 0.03), rough=0.4, coat=0.4)
    ring = yp.mat('rp_ring', (0.98, 0.74, 0.46), rough=0.45)
    tc = yp.base('panda')                 # _DANCE 모드 → 받침 없이 팀색만
    yp.body('panda', fur, dark, dark, 'rest', tc)
    b0 = Vector((0.5, 0.3, 0.42))
    Rt = Matrix.Rotation(tail, 3, 'Y')    # + = 꼬리가 바깥(오른쪽 아래)으로 휜다
    for i in range(7):
        t = i / 6
        p = Vector((0.5 + 0.34 * math.sin(t * 1.5), 0.3 - 0.12 * t, 0.42 + 0.85 * t))
        p = b0 + Rt @ (p - b0)
        yp.sph(0.21 - 0.018 * i, p, fur if i % 2 == 0 else ring)
    H = yp.Head(yp.HEAD_C, yp.HA + 0.02, yp.HB, yp.HC - 0.02)
    yp.sph(1.0, H.c, fur, scale=(H.a, H.b, H.cc), seg=128)
    for s in (-1, 1):
        yp.patch(H, s * 0.5, -0.26, 0.27, white)
        yp.feat(H, s * 0.3, 0.3, 0.09, white, scale=(1.25, 0.3, 0.8), lift=-0.004)
    yp.patch(H, 0, -0.34, 0.24, white, sx=1.35, sz=0.85)
    stripe = yp.mat('rp_stripe', (0.45, 0.13, 0.04), rough=0.45)
    for s in (-1, 1):
        yp.line(H, s * 0.34, -0.2, s * 0.3, -0.42, 0.04, stripe, lift=0.03)
    dr = droop
    for s in (-1, 1):
        ang = math.radians(28 + 32 * dr)
        d = (s * math.sin(ang), 0.05, math.cos(ang))
        e0 = (s * (0.52 + 0.08 * dr), 0.08, 1.96 - 0.08 * dr)
        yp.ear(d, e0, 0.5, 0.3, white, flat=0.45)
        yp.ear(d, (e0[0], e0[1] - 0.12, e0[2] + 0.03), 0.36, 0.2, dark, flat=0.25)
    yp.nose(H, -0.24, yp.mat('nose', (0.03, 0.02, 0.03), rough=0.15, coat=1.0), w=0.068)
    F = yp.Face(H, 0.31, 0.0, 0.185, (0.62, 0.28, 0.08), mouth=-0.33)
    F.no_brows = True
    before = set(bpy.data.objects)
    face(F, ex, fur)
    fc = bpy.data.collections["FACE"]
    for o in bpy.data.objects:
        if o not in before:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            fc.objects.link(o)
    return F


# ════════════ 프레임 정의 ════════════
REST = ((0.2, -0.48, 0.5), (-0.2, -0.48, 0.5))
CHIN = ((0.26, -0.62, 0.86), (-0.26, -0.62, 0.86))


def fr(ex, hands=REST, **kw):
    d = dict(ex=ex, R=hands[0], L=hands[1], fwd=0.0, roll=0.0, hfwd=0.0, hroll=0.0, droop=0.0, tail=0.0,
             feet=FEET, grip=None, L_=1.0)
    d.update(kw)
    return d


FRAMES = {}
for i, t in enumerate(T):
    FRAMES['aim%d' % i] = fr('n', grip=t, roll=0.3 * t, fwd=0.1, hroll=0.14 * t, hfwd=-0.03)
for i, t in enumerate(T):
    FRAMES['push%d' % i] = fr('k', grip=t, L_=0.74, roll=0.3 * t, fwd=0.22, hroll=0.14 * t, hfwd=0.05)
FRAMES.update({
    'stand': fr('n'),
    'swish': fr('n', tail=0.55, hroll=0.05),
    'blink': fr('b'),
    'look': fr('l', hfwd=-0.2, hroll=-0.1),
    'yawn': fr('y', ((0.1, -0.84, 1.1), (-0.2, -0.48, 0.5)), hfwd=-0.12, roll=0.04),
    'reload': fr('h', ((0.12, -0.72, 0.92), (-0.46, -0.66, 0.92)), roll=-0.06, hroll=-0.06),
    'swap': fr('w', ((0.2, -0.48, 0.5), (-1.02, -0.42, 1.08)), roll=-0.07, hroll=-0.08),
    'happy': fr('x', ((0.98, -0.34, 1.22), (-0.98, -0.34, 1.22)), hfwd=-0.05),
    'cheer': fr('h', ((1.06, -0.3, 1.62), (-1.06, -0.3, 1.62)), hfwd=-0.08,
                feet=((0.32, -0.06, 0.07), (-0.32, -0.06, 0.07))),
    'pout': fr('p', ((-0.22, -0.64, 0.66), (0.22, -0.6, 0.6)), hroll=0.14, droop=0.25),
    'nervous': fr('v', CHIN, droop=0.4, fwd=0.04),
    'worry': fr('u', ((0.3, -0.6, 0.72), (-0.3, -0.6, 0.72)), hfwd=-0.2, droop=0.3),
    'cry': fr('c', CHIN, droop=1.0, hfwd=0.08),
})
_hip = yp.DPOSE['hip']
FRAMES['dance1'] = fr('h', (_hip['R'], _hip['L']), feet=_hip['feet'], roll=_hip['roll'], hroll=_hip['hroll'])
_m = lambda v: (-v[0], v[1], v[2])
FRAMES['dance2'] = fr('x', (_m(_hip['L']), _m(_hip['R'])), feet=(_m(_hip['feet'][1]), _m(_hip['feet'][0])),
                      roll=-_hip['roll'], hroll=-_hip['hroll'])
ORDER = ['aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'push0', 'push1', 'push2', 'push3', 'push4',
         'stand', 'swish', 'blink', 'look', 'yawn', 'reload', 'swap', 'happy', 'cheer', 'pout',
         'nervous', 'worry', 'cry', 'dance1', 'dance2']


def proj(sc, p):
    v = world_to_camera_view(sc, sc.camera, Vector(p))
    return [round(v.x, 5), round(1.0 - v.y, 5)]     # 셀 정규 좌표, y 아래로


def build_frame(name):
    """씬에 프레임 하나를 짓는다(스튜디오·렌더 없이) — 타일(tiles_toybox 의 bubble)도 이걸로 판다를 세운다."""
    spec = FRAMES[name]
    if "FACE" not in bpy.data.collections:
        fc = bpy.data.collections.new("FACE")
        bpy.context.scene.collection.children.link(fc)
    before = set(bpy.data.objects)       # 이 판다가 만든 것만 움직인다(타일 무대 소품은 그대로)
    Z = Matrix.Rotation(YAW, 4, 'Z')
    M = body_matrix(spec['fwd'], spec['roll'])
    ZM = Z @ M
    R, L = Vector(spec['R']), Vector(spec['L'])
    knob = None
    if spec['grip'] is not None:
        # 손잡이를 양쪽에서 감싸 쥔다 — 최종 월드 위치에서 몸 변환을 거꾸로 풀어 어깨 기준 손 좌표를 얻는다
        knob = stick_tip(spec['grip'], spec['L_'])
        inv = ZM.inverted()
        # 앞발은 공 바로 아래 막대를 양옆에서 쥔다 — 빨간 공이 앞발 위로 보여야 '손잡이'로 읽힌다
        g = stick_tip(spec['grip'], spec['L_'] - 0.3)
        R = inv @ (g + Vector((0.13, -0.05, 0.0)))
        L = inv @ (g + Vector((-0.13, -0.05, 0.0)))
    yp._DANCE = dict(R=tuple(R), L=tuple(L))
    try:
        build_panda(spec['ex'], spec['droop'], spec['tail'])
        objs = [o for o in bpy.data.objects if o.type == 'MESH' and o not in before]
        head = [o for o in objs if o not in yp._HEAD_MARK]
        Hm = head_matrix(spec['hfwd'], spec['hroll'])
        apply(head, Hm)
        apply(objs, M)
        leg, foot = yp._DANCE['_leg'], yp._DANCE['_limb']
        for s, f in ((1, spec['feet'][0]), (-1, spec['feet'][1])):
            h = M @ Vector((s * HIP[0], HIP[1], HIP[2]))
            yp.capsule(h, Vector(f) + Vector((0, 0.02, 0.05)), 0.1, leg, rb=0.09)
            yp.sph(0.15, f, foot, scale=(1.0, 1.35, 0.7))
        allm = [o for o in bpy.data.objects if o.type == 'MESH' and o not in before]
        apply(allm, Z)
        if knob is not None:
            steel = yp.mat('stick', (0.80, 0.83, 0.90), rough=0.22, metal=0.25, coat=0.6)
            red = yp.mat('knob', (0.93, 0.13, 0.12), rough=0.18, coat=1.0)
            yp.capsule(PIVOT, knob, 0.06, steel)
            yp.sph(KNOB_R, knob, red, seg=40)
    finally:
        yp._DANCE = None
    return spec, ZM, Hm, knob


def render_frame(name):
    sc = studio()
    spec, ZM, Hm, knob = build_frame(name)
    sc.render.filepath = os.path.join(OUTDIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    head_c = ZM @ (Hm @ Vector(yp.HEAD_C))
    meta = dict(feet=proj(sc, (0, 0, 0)), pivot=proj(sc, PIVOT), head=proj(sc, head_c),
                headR=round(yp.HA / ORTHO, 5))
    if knob is not None:
        meta['knob'] = proj(sc, knob)
    if name == 'reload':        # 두 앞발 사이 = 캔버스가 다음 버블을 그릴 자리
        mid = ZM @ ((Vector(spec['R']) + Vector(spec['L'])) / 2 + Vector((0, -0.08, 0.02)))
        meta['hold'] = proj(sc, mid)
    # 손을 놓은 포즈에서 캔버스가 그릴 막대 끝(기울기 0) — 잡은 막대와 같은 길이
    meta['rest'] = proj(sc, stick_tip(0.0))
    meta['knobR'] = round(KNOB_R / ORTHO, 5)
    print("RENDERED", name)
    return meta


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = argv[0].split(',') if argv else ORDER
    mp = os.path.join(OUTDIR, "meta.json")
    meta = {}
    if os.path.exists(mp):
        with open(mp, encoding='utf-8') as f:
            meta = json.load(f)
    for n in names:
        meta[n] = render_frame(n)
        with open(mp, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=1)
