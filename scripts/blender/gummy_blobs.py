# -*- coding: utf-8 -*-
"""구미 체인 — 젤리 캐릭터 5종 × 표정 6컷 + 설탕 블록 · 물방울 · 예고 트레이 사탕 (2026-09-27).

운영자: "구미체인은 … 30년 전 게임보다 그래픽이 더 안 좋아. … 질감과 애니메이션 효과까지 매우
훌륭해서 사람으로 하여금 귀엽고도 이펙트가 찰지게 느껴지고 임팩트가 확실히 느껴지게 해야 해."

캐릭터는 전부 이 사이트의 오리지널 — 과일 젤리 사탕 다섯 친구(딸기·라임·소다·레몬·포도).
장르 원조 게임의 캐릭터·이름과 닮지 않게: 둥근 '젤리 사탕' 몸 + 과일 장식(잎·꼭지·기포) + 색마다
다른 눈 모양(색약 사용자도 모양으로 구분).

## 렌더 문법
- 몸 = 눌린 타원체 + Principled **Subsurface 1.0**(속에서 빛이 번지는 젤리) + **Coat 1.0**(사탕 코팅
  반사) + 약한 자체발광(속광). 뒤·아래 림라이트가 SSS 를 통과해 가장자리가 밝게 비친다
- 잉크 외곽선(Freestyle)은 **넣지 않는다** — 같은 색끼리 붙은 덩어리를 게임 셰이더가 하나의 외곽선으로
  두르기 때문(칸마다 외곽선이 있으면 한 덩어리로 안 읽힌다)
- 표정 기관(눈·입·눈썹·볼)은 윷놀이 말(yut_pieces.py)의 Face 헬퍼를 import 해서 쓴다 — 사이트 장난감
  화풍과 같은 눈. yut_pieces.py 는 수정하지 않는다
- Standard 뷰 변환(AgX 는 원색을 파스텔로 누른다 — art_pipeline 메모)
- 직교 카메라, 셀 한 변 = 월드 1.0, 프레임 = 1.3 셀(장식·찌그러짐 여유). 프레임 중심 = 셀 중심,
  몸 바닥 = 프레임 위에서 GA_BODY.b(빌더가 알파로 재서 게임 JS 상수로 출력)

## 프레임 (ORDER 순서 = 아틀라스 순서, build_gummy_atlas.py 와 게임 JS 가 같은 순서를 쓴다)
  <c><e>  c = 1 딸기 · 2 라임 · 3 소다 · 4 레몬 · 5 포도
          e = n 평소 · b 깜빡 · h 기쁨(연쇄 중·세 개째) · s 놀람(착지 찌그러짐·회전)
              w 걱정(판이 높을 때) · p 비명(터지기 직전 부풀 때)
  g   설탕 블록(방해) — 각진 결정 사탕 + 설탕 알갱이
  d   물방울(무채색 — 게임이 색을 입힌다)
  k   포장 사탕(예고 30개) · t 별사탕(예고 180개)

실행:
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/gummy_blobs.py            # 전부
  ... -P scripts/blender/gummy_blobs.py -- 1n,3s,g                                                # 일부
  GB_SAMPLES=32 GB_RES=256 ... 로 시안 확인
출력: scripts/og-assets/gummy/<frame>.png → python scripts/build_gummy_atlas.py → public/assets/gummy/
"""
import bpy
import math
import os
import sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yut_pieces as yp  # noqa: E402  (헬퍼만 쓴다 — 수정하지 않는다)
from yut_pieces import sph, feat, arc, line, capsule, cone, torus, Head, Face  # noqa: E402


def blush(H, x, dz, strength=1.0):
    """볼 — yut 의 blush 보다 작게(몸 대비 얼굴이 크다)"""
    m = yp.mat('blush%.1f' % strength, (1.0, 0.42 - 0.1 * strength, 0.5 - 0.1 * strength), rough=0.5, coat=0.1)
    for s in (-1, 1):
        feat(H, s * x, dz, 0.085, m, scale=(1.3, 0.22, 0.7), lift=0.012)

OUTDIR = os.path.join(HERE, "..", "og-assets", "gummy")
os.makedirs(OUTDIR, exist_ok=True)
RES = int(os.environ.get('GB_RES', '384'))
SAMPLES = int(os.environ.get('GB_SAMPLES', '128'))
ORTHO = 1.3
TILT = math.radians(9)
CAM_Z = 0.62                             # 프레임 중심 높이 — 0.5 에서는 딸기 잎 왕관이 위로 잘렸다(bbox 실측)
BODY_C = Vector((0, 0, 0.5))
BA, BB, BC = 0.49, 0.41, 0.5          # 몸 반축(좌우·앞뒤·위아래)

CHARS = {
    1: dict(name='berry', col=(1.0, 0.035, 0.085), sss=(1.0, 0.25, 0.25), iris=(1.0, 0.35, 0.4)),
    2: dict(name='lime', col=(0.10, 0.62, 0.035), sss=(0.5, 1.0, 0.3), iris=(0.35, 0.85, 0.3)),
    3: dict(name='soda', col=(0.03, 0.26, 1.0), sss=(0.3, 0.6, 1.0), iris=(0.35, 0.65, 1.0)),
    4: dict(name='lemon', col=(1.0, 0.56, 0.012), sss=(1.0, 0.8, 0.3), iris=(1.0, 0.7, 0.2)),
    5: dict(name='grape', col=(0.36, 0.07, 0.95), sss=(0.8, 0.45, 1.0), iris=(0.75, 0.45, 1.0)),
}
EXPRS = ['n', 'b', 'h', 's', 'w', 'p']
ORDER = ['%d%s' % (c, e) for c in range(1, 6) for e in EXPRS] + ['g', 'd', 'k', 't']


# ════════════ 스튜디오 ════════════
def studio():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    yp._MATS.clear()
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try:
        sc.cycles.device = 'GPU'
        pr = bpy.context.preferences.addons['cycles'].preferences
        pr.compute_device_type = 'CUDA'
        pr.get_devices()
        for d in pr.devices:
            d.use = True
    except Exception:
        pass
    sc.cycles.use_denoising = True
    sc.cycles.samples = SAMPLES
    sc.cycles.max_bounces = 16
    sc.cycles.transmission_bounces = 12
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.use_freestyle = False
    # 월드광은 반사에만 — 확산으로 들어오면 색이 뿌옇게 뜬다
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.5, 0.62, 1)
    bg.inputs[1].default_value = 0.7
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMixShader')
    tr = nt.nodes.new('ShaderNodeBackground')
    tr.inputs[1].default_value = 0.12
    nt.links.new(lp.outputs['Is Glossy Ray'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes['World Output'].inputs[0])
    sc.world = w

    def area(loc, power, size, color, target=(0, 0, 0.46)):
        bpy.ops.object.light_add(type='AREA', location=loc)
        L = bpy.context.object
        L.data.energy = power
        L.data.size = size
        L.data.color = color
        d = Vector(target) - Vector(loc)
        L.rotation_mode = 'QUATERNION'
        L.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    area((-2.4, -3.2, 3.6), 260, 2.2, (1.0, 0.95, 0.88))      # 키 — 왼쪽 위(사이트 공통 광원 방향)
    area((2.2, 2.6, 2.4), 420, 2.4, (1.0, 0.96, 1.0))        # 뒤 림 — SSS 로 가장자리가 비친다
    area((0.0, -1.6, -2.2), 70, 2.5, (1.0, 0.9, 0.95))       # 아래 반사광 — 사탕 속광
    area((0.4, -4.5, 0.9), 90, 3.5, (1.0, 1.0, 1.0))         # 정면 채움
    bpy.ops.object.camera_add(location=(0, -8.0, CAM_Z + 8.0 * math.tan(TILT)))
    cam = bpy.context.object
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ORTHO
    d = Vector((0, 0, CAM_Z)) - cam.location
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    sc.camera = cam
    return sc


# ════════════ 재질 ════════════
def gummy_mat(name, col, sss, glow=0.10, rough=0.2):
    if name in yp._MATS:
        return yp._MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Subsurface Weight"].default_value = 1.0
    b.inputs["Subsurface Radius"].default_value = sss
    b.inputs["Subsurface Scale"].default_value = 0.22
    try:
        b.inputs["Subsurface Method"].default_value = 'RANDOM_WALK'
    except Exception:
        pass
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.035
    b.inputs["Coat IOR"].default_value = 1.55
    b.inputs["Specular IOR Level"].default_value = 0.6
    b.inputs["Emission Color"].default_value = (*col, 1)
    b.inputs["Emission Strength"].default_value = glow
    yp._MATS[name] = m
    return m


def body(ch):
    C = CHARS[ch]
    m = gummy_mat('gum%d' % ch, C['col'], C['sss'])
    o = sph(1.0, BODY_C, m, scale=(BA, BB, BC), seg=96)
    # 바닥을 살짝 눌러 '놓인' 젤리로 — 아래 20% 를 납작하게
    for v in o.data.vertices:
        if v.co.z < -0.55:
            v.co.z = -0.55 - (v.co.z + 0.55) * 0.55
    return m


def leaf(base, direction, length, width, m, flat=0.28, bend=0.0):
    d = Vector(direction).normalized()
    c = Vector(base) + d * (length / 2)
    o = sph(1.0, c, m, scale=(width, width * flat, length / 2), seg=32)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    return o


def ornament(ch, H):
    LEAF = yp.mat('leaf', (0.10, 0.55, 0.08), rough=0.3, coat=0.8)
    top = BODY_C.z + BC
    if ch == 1:      # 딸기 — 잎 왕관 + 노란 씨(얼굴을 피해 아래·옆에)
        for i in range(5):
            a = -1.0 + 0.5 * i
            leaf((0.06 * math.sin(a), 0.02, top - 0.03), (math.sin(a) * 1.4, -0.25, 0.9), 0.2, 0.07, LEAF)
        sph(0.035, (0, 0.02, top + 0.06), LEAF, scale=(1, 1, 2.0))
        seed = yp.mat('seed', (1.0, 0.8, 0.25), rough=0.25, coat=0.6, emit=(1.0, 0.75, 0.2), estr=0.4)
        for (x, z) in [(-0.38, -0.1), (0.38, -0.12), (-0.26, -0.24), (0.27, -0.25),
                       (-0.41, 0.12), (0.42, 0.1), (-0.15, 0.36), (0.17, 0.37)]:
            feat(H, x, z, 0.022, seed, scale=(0.7, 0.5, 1.1), lift=-0.004)
    elif ch == 2:    # 라임 — 비스듬한 잎 두 장
        leaf((0.02, 0.02, top - 0.02), (0.9, -0.2, 0.8), 0.24, 0.085, LEAF)
        leaf((-0.02, 0.02, top - 0.02), (-0.5, -0.1, 0.9), 0.16, 0.06, LEAF)
        sph(0.03, (0, 0.02, top + 0.02), yp.mat('stem', (0.25, 0.14, 0.05), rough=0.4), scale=(1, 1, 1.6))
    elif ch == 3:    # 소다 — 몸속에 비치는 기포 + 머리 위로 올라가는 거품 셋
        fizz = yp.mat('fizz', (0.85, 0.95, 1.0), rough=0.05, coat=1.0, emit=(0.7, 0.9, 1.0), estr=0.9)
        for (x, z, r) in [(-0.3, 0.26, 0.035), (0.33, 0.2, 0.03), (0.25, -0.3, 0.028), (-0.33, -0.22, 0.024),
                          (0.0, 0.35, 0.022)]:
            feat(H, x, z, r, fizz, scale=(1, 0.6, 1), lift=-0.01)
        for (x, z, r) in [(0.14, top + 0.05, 0.045), (0.24, top + 0.13, 0.032), (0.18, top + 0.2, 0.022)]:
            sph(r, (x, -0.1, z), fizz)
    elif ch == 4:    # 레몬 — 꼭지 돌기 + 잎 하나
        sph(0.07, (0, 0.0, top - 0.015), yp._MATS['gum4'], scale=(1, 0.9, 1.1))
        leaf((0.03, 0.02, top + 0.02), (1.0, -0.2, 0.55), 0.2, 0.07, LEAF)
    elif ch == 5:    # 포도 — 말린 꼭지 + 작은 잎
        stem = yp.mat('stem', (0.25, 0.14, 0.05), rough=0.4)
        pts = [Vector((0.0, 0.02, top - 0.03)), Vector((0.01, 0.02, top + 0.06)),
               Vector((0.06, 0.02, top + 0.11)), Vector((0.12, 0.02, top + 0.1))]
        for i in range(3):
            capsule(pts[i], pts[i + 1], 0.022, stem)
        leaf((-0.01, 0.02, top + 0.03), (-1.0, -0.25, 0.5), 0.18, 0.065, LEAF)


# ════════════ 얼굴 ════════════
def face(ch, ex):
    H = Head(BODY_C, BA, BB, BC)
    C = CHARS[ch]
    ez, er = 0.05, 0.13
    F = Face(H, 0.185, ez, er, C['iris'], mouth=-0.15, blush_x=0.33, blush_dz=-0.1)
    # 크고 까만 유리알 눈 — Face 기본(홍채색 × 0.42 바탕)은 밝은 몸색 위에서 흐려 보였다(시안 실측)
    F.IRd = yp.mat('irisd%d' % ch, tuple(0.02 + c * 0.05 for c in C['iris']), rough=0.06, coat=1.0)
    F.IR = yp.mat('irisl%d' % ch, C['iris'], rough=0.1, coat=1.0, emit=C['iris'], estr=0.9)
    F.D = yp.mat('pupil', (0.004, 0.003, 0.008), rough=0.05, coat=1.0)
    K = F.K
    sweat = yp.mat('sweat', (0.55, 0.85, 1.0), rough=0.05, coat=1.0, emit=(0.5, 0.8, 1.0), estr=0.6)

    def idle_eyes():
        if ch == 3:      # 소다 — 졸린 반눈(위 눈꺼풀 선)
            for s in (-1, 1):
                F.eye(s, scale=0.95)
                x = s * F.ex
                lid = gummy_mat('lid3', C['col'], C['sss'], glow=0.12)
                feat(H, x, ez + er * 0.6, er * 1.0, lid, scale=(1.0, 0.32, 0.6), lift=0.012)
                line(H, x - er * 0.95, ez + er * 0.28, x + er * 0.95, ez + er * 0.28, 0.018, K, lift=0.05)
        elif ch == 4:    # 레몬 — 별빛 눈
            F.eyes(scale=1.02, big=True, star=True)
        elif ch == 5:    # 포도 — 속눈썹
            F.eyes()
            for s in (-1, 1):
                x = s * F.ex
                for k in range(2):
                    line(H, x + s * er * (0.55 + 0.25 * k), ez + er * (0.8 - 0.3 * k),
                         x + s * er * (0.95 + 0.25 * k), ez + er * (1.1 - 0.3 * k), 0.013, K, lift=0.02)
        else:
            F.eyes(big=(ch == 1))

    def idle_mouth():
        if ch == 1:
            arc(H, 0, F.mouth, 0.1, -0.04, 0.016, K, lift=0.02)
        elif ch == 2:
            F.mouth_w()
        elif ch == 3:
            arc(H, 0, F.mouth - 0.01, 0.07, -0.025, 0.015, K, n=5, lift=0.02)
        elif ch == 4:
            F.mouth_open(0.075, 0.6)
        else:
            F.mouth_bleh()

    if ex == 'n':
        idle_eyes()
        idle_mouth()
        blush(H, F.bx, F.bz, 0.7)
    elif ex == 'b':
        for s in (-1, 1):
            F.closed(s, False)
        idle_mouth()
        blush(H, F.bx, F.bz, 0.7)
    elif ex == 'h':
        for s in (-1, 1):
            F.closed(s, True)
        F.mouth_open(0.085, 0.8)
        blush(H, F.bx, F.bz, 1.3)
    elif ex == 's':
        for s in (-1, 1):
            F.eye_small(s)
        F.brows('up')
        F.mouth_o()
        blush(H, F.bx, F.bz, 0.6)
    elif ex == 'w':
        F.eyes(scale=0.92, wet=True)
        F.brows('worry')
        arc(H, 0, F.mouth - 0.02, 0.1, 0.03, 0.015, K, n=5, lift=0.02)
        p, n = H.pt(-(BA * 0.72), 0.22, 0.03)
        sph(0.04, p, sweat, scale=(0.85, 0.6, 1.35), rot=H.rot(n))
        blush(H, F.bx, F.bz, 0.4)
    elif ex == 'p':
        for s in (-1, 1):
            F.squeeze(s)
        F.brows('worry')
        F.mouth_open(0.1, 1.2, tongue=True)
        blush(H, F.bx, F.bz, 1.5)
    return H


def gummy(ch, ex):
    body(ch)
    H = face(ch, ex)
    ornament(ch, H)


# ════════════ 설탕 블록 · 물방울 · 트레이 사탕 ════════════
def sugar_block():
    m = yp._MATS.get('sugar')
    if m is None:
        m = bpy.data.materials.new('sugar')
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.5, 0.48, 0.64, 1)
        b.inputs["Roughness"].default_value = 0.12
        b.inputs["Subsurface Weight"].default_value = 0.5
        b.inputs["Subsurface Radius"].default_value = (0.8, 0.8, 1.0)
        b.inputs["Subsurface Scale"].default_value = 0.1
        b.inputs["Coat Weight"].default_value = 1.0
        b.inputs["Coat Roughness"].default_value = 0.02
        b.inputs["Specular IOR Level"].default_value = 0.8
        yp._MATS['sugar'] = m
    # 각진 결정 — 베벨 큰 육면체에 비대칭 절단면(평면 셰이딩으로 면이 반짝인다)
    bpy.ops.mesh.primitive_cube_add(size=0.88, location=(0, 0, 0.47))
    o = bpy.context.object
    o.rotation_euler = (0.0, 0.0, 0.18)       # 살짝 틀어 옆면 한 장이 보이게 — 두께·결정면이 읽힌다
    o.data.materials.append(m)
    md = o.modifiers.new("bev", 'BEVEL')
    md.width = 0.13
    md.segments = 1
    bpy.ops.object.modifier_apply(modifier="bev")
    import random
    rnd = random.Random(5)
    for v in o.data.vertices:
        v.co.x += rnd.uniform(-0.02, 0.02)
        v.co.z += rnd.uniform(-0.02, 0.02)
    for p in o.data.polygons:
        p.use_smooth = False
    grain = yp.mat('grain', (1, 1, 1), rough=0.1, coat=1.0, emit=(1, 1, 1), estr=0.5)
    for i in range(22):
        x = rnd.uniform(-0.38, 0.38)
        z = rnd.uniform(0.08, 0.82)
        s = rnd.uniform(0.018, 0.034)
        bpy.ops.mesh.primitive_cube_add(size=s, location=(x * 0.9, -0.47, z + 0.03),
                                        rotation=(rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(0, 1)))
        bpy.context.object.data.materials.append(grain)
    # 윗면 알갱이
    for i in range(10):
        bpy.ops.mesh.primitive_cube_add(size=rnd.uniform(0.02, 0.035),
                                        location=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0.915),
                                        rotation=(rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(0, 1)))
        bpy.context.object.data.materials.append(grain)


def droplet():
    m = gummy_mat('drop', (0.92, 0.92, 0.92), (1.0, 1.0, 1.0), glow=0.15, rough=0.15)
    sph(0.3, (0, 0, 0.5), m, scale=(1, 0.9, 1), seg=64)


def wrapped_candy():
    body_m = yp.mat('candy', (1.0, 0.22, 0.45), rough=0.18, coat=1.0)
    stripe = yp.mat('candy_w', (1.0, 0.9, 0.95), rough=0.18, coat=1.0)
    wrap = yp.mat('wrap', (1.0, 0.75, 0.2), rough=0.25, coat=0.8, metal=0.3)
    sph(0.26, (0, 0, 0.5), body_m, scale=(1.1, 0.8, 0.85), seg=64)
    torus(0.2, 0.035, (0, -0.02, 0.5), stripe, rot=(math.pi / 2, 0, 0.5), scale=(1.1, 1, 0.85))
    for s in (-1, 1):
        cone(0.2, 0.03, 0.26, (s * 0.37, 0, 0.5), wrap, rot=(0, s * math.pi / 2, 0), scale=(1, 0.5, 1))


def star_candy():
    m = yp.mat('konpeito', (1.0, 0.72, 0.1), rough=0.2, coat=1.0, emit=(1.0, 0.6, 0.1), estr=0.35)
    sph(0.24, (0, 0, 0.5), m, seg=48)
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        d = Vector((math.cos(a), -0.15, -math.sin(a))).normalized()
        c = Vector((0, 0, 0.5)) + d * 0.3
        o = cone(0.12, 0.03, 0.22, c, m)
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)


def render(name):
    sc = studio()
    if name == 'g':
        sugar_block()
    elif name == 'd':
        droplet()
    elif name == 'k':
        wrapped_candy()
    elif name == 't':
        star_candy()
    else:
        gummy(int(name[0]), name[1])
    sc.render.filepath = os.path.join(OUTDIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)


if __name__ == "__main__":
    want = ORDER
    if '--' in sys.argv:
        rest = sys.argv[sys.argv.index('--') + 1:]
        if rest:
            want = [w for w in rest[0].split(',') if w]
    for n in want:
        render(n)
