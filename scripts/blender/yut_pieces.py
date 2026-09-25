# -*- coding: utf-8 -*-
"""윷놀이 말 4종 — 사막여우 · 수달 · 랫서팬더 · 랙돌 고양이 (2026-09-25 신설).

홈 타일 '레트로 장난감 진열장'(tiles_toybox.py)과 같은 문법을 쓴다 —
코팅 플라스틱 + 잉크 외곽선(Freestyle) + Standard 뷰 변환(AgX 는 원색을 파스텔로 누른다).
단 tiles_toybox.py 는 다른 작업이 소유하므로 **이 파일은 독립 스크립트**다(헬퍼 복사본 포함).

말 = 팀 색 받침(보드게임 폰) 위에 앉은 2등신 동물. 팀 색은 받침·목도리에만 쓴다 —
털색과 겹치지 않아 네 팀이 한눈에 구분된다(빨강·파랑·노랑·보라).

표정 6종을 같은 카메라로 찍어 아틀라스로 묶는다. 게임은 표정을 바꿔 끼우고
눈물·별·반짝이 같은 움직이는 효과만 캔버스로 얹는다.
  n 기본 · b 눈 깜빡 · h 행복(^^) · s 슬픔(울먹) · x 신남(반짝 눈 + 활짝) · o 놀람/삐죽

실행:
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/yut_pieces.py            # 말 24장
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/yut_pieces.py -- tile    # 홈 타일용 장난감
출력: scripts/og-assets/yut/<sp>-<ex>.png (투명) → scripts/build_yut_atlas.py 가
      public/assets/yut/pieces.webp (4행 × 6열 아틀라스)로 묶는다.
"""
import bpy
import math
import os
import sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "..", "og-assets", "yut")
TILEDIR = os.path.join(HERE, "..", "og-assets", "tiles3d")
os.makedirs(OUTDIR, exist_ok=True)
RES = int(os.environ.get('YP_RES', '560'))
SAMPLES = int(os.environ.get('YP_SAMPLES', '96'))

SPECIES = ['fox', 'otter', 'panda', 'cat']
EXPRS = ['n', 'b', 'h', 's', 'x', 'o']
_MATS = {}


# ════════════ 스튜디오 ════════════
def studio(tile=False):
    global _MATS
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS = {}
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
    sc.render.resolution_x = sc.render.resolution_y = (1000 if tile else RES)
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.cycles.samples = SAMPLES
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes["Background"].inputs[0].default_value = (0.22, 0.24, 0.32, 1)
    nt.nodes["Background"].inputs[1].default_value = 0.45
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMixShader')
    tr = nt.nodes.new('ShaderNodeBackground')
    tr.inputs[1].default_value = 0.0 if tile else 0.18
    nt.links.new(lp.outputs['Is Glossy Ray'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(nt.nodes['Background'].outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes['World Output'].inputs[0])
    sc.world = w
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = 'ABSOLUTE'
    th = 2.4 if tile else 2.0
    sc.render.line_thickness = th
    toy = bpy.data.collections.new("TOY")
    sc.collection.children.link(toy)
    vl = bpy.context.view_layer
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("L")
    ls.select_by_collection = True
    ls.collection = toy
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = False
    ls.select_external_contour = True
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("ink")
    ls.linestyle.color = (0.07, 0.05, 0.09)
    ls.linestyle.thickness = th
    if tile:
        bpy.ops.mesh.primitive_plane_add(size=9, location=(0, 0, 0))
        bpy.context.object.is_shadow_catcher = True

    def area(loc, power, size, color, target=(0, 0, 1.0)):
        bpy.ops.object.light_add(type='AREA', location=loc)
        L = bpy.context.object
        L.data.energy = power
        L.data.size = size
        L.data.color = color
        d = Vector(target) - Vector(loc)
        L.rotation_mode = 'QUATERNION'
        L.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    k = 1.0 if tile else 0.72   # 말은 밝은 털이 많아 조명을 낮춘다(워시 방지)
    area((-4.5, -5.0, 6.5), 700 * k, 5, (1.0, 0.93, 0.84))
    area((4.5, 4.0, 4.5), 520 * k, 4, (0.72, 0.82, 1.0))
    area((1.0, -7.5, 1.8), 150 * k, 6, (1.0, 1.0, 1.0))
    area((0.0, 0.0, 9.0), 140 * k, 6, (1.0, 1.0, 1.0))
    if tile:
        bpy.ops.object.camera_add(location=(0, -7.6, 4.0))
        cam = bpy.context.object
        cam.data.lens = 78
        tgt = Vector((0, 0, 1.12))
    else:
        # 말은 보드 위에서 정면 약간 위(≈22°)에서 본다 — 얼굴이 가장 잘 읽히는 각
        bpy.ops.object.camera_add(location=(0, -9.2, 4.6))
        cam = bpy.context.object
        cam.data.lens = 80
        tgt = Vector((0, 0, 1.12))
    d = tgt - cam.location
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    sc.camera = cam
    vl.active_layer_collection = vl.layer_collection.children["TOY"]
    return sc


# ════════════ 재질 · 도형 ════════════
def mat(name, color, rough=0.3, metal=0.0, coat=0.5, emit=None, estr=0.0, sheen=0.0):
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    try:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.08
    except Exception:
        pass
    if sheen:
        try:
            b.inputs["Sheen Weight"].default_value = sheen
        except Exception:
            pass
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = estr
    _MATS[name] = m
    return m


def _fin(o, m, bevel=0.0, smooth=True):
    if m:
        o.data.materials.append(m)
    if bevel > 0:
        md = o.modifiers.new("bev", 'BEVEL')
        md.width = bevel
        md.segments = 3
        md.limit_method = 'ANGLE'
    if smooth and hasattr(o.data, "polygons"):
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def sph(r, loc, m, scale=(1, 1, 1), seg=40, rot=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.object
    o.scale = scale
    if rot is not None:
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = rot
    return _fin(o, m)


def cyl(r, depth, loc, m, rot=(0, 0, 0), bevel=0.03, verts=64):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    return _fin(bpy.context.object, m, bevel)


def cone(r1, r2, depth, loc, m, rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot, vertices=40)
    o = bpy.context.object
    o.scale = scale
    return _fin(o, m)


def torus(R, r, loc, m, rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot,
                                     major_segments=64, minor_segments=16)
    o = bpy.context.object
    o.scale = scale
    return _fin(o, m)


def capsule(a, b, r, m, rb=None):
    a, b = Vector(a), Vector(b)
    d = b - a
    rb = r if rb is None else rb
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=rb, depth=max(d.length, 1e-4), location=(a + b) / 2, vertices=24)
    o = bpy.context.object
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    _fin(o, m)
    s1 = sph(r, a, m, seg=20)
    s2 = sph(rb, b, m, seg=20)
    return [o, s1, s2]


# ════════════ 머리 좌표 — 타원체 표면 위에 이목구비를 붙인다 ════════════
class Head:
    def __init__(self, c, a, b, cc):
        self.c = Vector(c)
        self.a, self.b, self.cc = a, b, cc

    def pt(self, x, dz, lift=0.0):
        """정면(-y) 표면 위 점. x = 좌우, dz = 머리 중심 기준 높이."""
        k = 1 - (x / self.a) ** 2 - (dz / self.cc) ** 2
        y = -self.b * math.sqrt(max(0.0, k))
        p = Vector((x, y, self.c.z + dz))
        n = Vector((x / self.a ** 2, y / self.b ** 2, dz / self.cc ** 2)).normalized()
        return p + n * lift, n

    def rot(self, n):
        return Vector((0, -1, 0)).rotation_difference(n)


def feat(H, x, dz, r, m, scale=(1, 0.45, 1), lift=0.0, seg=28):
    p, n = H.pt(x, dz, lift)
    return sph(r, p, m, scale=scale, seg=seg, rot=H.rot(n))


def arc(H, cx, cz, w, h, t, m, n=7, lift=0.012):
    """얼굴 위 호(곡선) — 감은 눈·입. h>0 이면 ∩ (^), h<0 이면 ∪ (‿)."""
    objs = []
    pts = []
    for i in range(n):
        u = -1 + 2 * i / (n - 1)
        pts.append(H.pt(cx + u * w / 2, cz + h * (1 - u * u), lift)[0])
    for i in range(n - 1):
        objs += capsule(pts[i], pts[i + 1], t, m)
    return objs


# ════════════ 공통 몸 ════════════
TEAM = {
    'fox': (0.98, 0.62, 0.05),     # 사막 햇볕 노랑
    'otter': (0.08, 0.36, 0.95),   # 물빛 파랑
    'panda': (0.88, 0.10, 0.12),   # 단풍 빨강
    'cat': (0.50, 0.26, 0.95),     # 라벤더 보라
}
HEAD_C = (0, 0, 1.56)


def base_and_body(sp, fur, belly, limb):
    tc = mat('team_' + sp, TEAM[sp], rough=0.25, coat=0.8)
    gold = mat('gold', (0.95, 0.70, 0.22), rough=0.2, metal=1.0, coat=0.0)
    cyl(0.64, 0.2, (0, 0, 0.1), tc, bevel=0.06)
    torus(0.62, 0.035, (0, 0, 0.2), gold)
    cyl(0.5, 0.04, (0, 0, 0.215), mat('team_lt_' + sp, tuple(min(1, c * 0.55 + 0.45) for c in TEAM[sp]), rough=0.3), bevel=0.01)
    # 몸통(앉은 자세 — 아래가 넓은 달걀). 머리가 커 보이도록 몸은 작게
    sph(0.44, (0, 0.04, 0.62), fur, scale=(1.0, 0.92, 0.98))
    sph(0.31, (0, -0.2, 0.6), belly, scale=(1.0, 0.5, 1.05))
    # 발
    for s in (-1, 1):
        sph(0.14, (s * 0.2, -0.32, 0.3), limb, scale=(1.0, 1.3, 0.72))
    # 팔 — 짧은 팔 + 배 앞에 모은 동그란 손
    for s in (-1, 1):
        capsule((s * 0.34, -0.06, 0.84), (s * 0.17, -0.36, 0.66), 0.1, limb, rb=0.1)
        sph(0.11, (s * 0.12, -0.4, 0.64), limb, scale=(1.0, 0.9, 0.9))
    # 목도리(팀 색) + 짧은 매듭
    torus(0.33, 0.08, (0, 0.02, 1.0), tc, rot=(math.radians(-8), 0, 0), scale=(1.05, 0.98, 1))
    sph(0.09, (0.2, -0.33, 0.95), tc, scale=(1, 0.7, 1))
    capsule((0.22, -0.36, 0.9), (0.28, -0.4, 0.76), 0.06, tc, rb=0.05)
    return tc


def patch(H, x, dz, rho, m, t=0.026, sx=1.0, sz=1.0):
    """머리 표면에 얇게 덮이는 무늬(주둥이·볼·마스크).
    납작한 타원체를 붙이면 가장자리가 머리 곡면 밖으로 떠서 '가면'처럼 보인다(실측).
    그래서 머리 안쪽에 묻힌 작은 구의 '뚜껑'만 t 만큼 내민다 — 보이는 반경이 rho 가 되도록 구 반지름을 푼다."""
    p, n = H.pt(x, dz)
    r = (H.a + H.b + H.cc) / 3

    def vis(rp):
        D = r + t - rp
        xx = (D * D + r * r - rp * rp) / (2 * D)
        return math.sqrt(max(0.0, r * r - xx * xx))
    lo, hi = rho * 0.5, r * 0.999
    for _ in range(40):
        mid = (lo + hi) / 2
        if vis(mid) < rho:
            lo = mid
        else:
            hi = mid
    rp = (lo + hi) / 2
    return sph(rp, p + n * (t - rp), m, scale=(sx, 1, sz), rot=H.rot(n), seg=128)


def cheeks(H, x, dz, strength=1.0):
    blush = mat('blush%.1f' % strength, (1.0, 0.45 - 0.1 * strength, 0.5 - 0.1 * strength), rough=0.5, coat=0.1)
    return [feat(H, s * x, dz, 0.09, blush, scale=(1.25, 0.22, 0.72), lift=-0.004) for s in (-1, 1)]


# ════════════ 표정 — 공통 로직, 종마다 눈 색·위치만 다르다 ════════════
def build_expressions(H, ex, ez, er, iris=None, mouth_dz=-0.26):
    """ex,ez = 눈 위치(좌우, 높이) / er = 눈 반지름. 반환 {expr: [objs]}"""
    D = mat('eye', (0.02, 0.02, 0.035), rough=0.12, coat=1.0)
    W = mat('hl', (1, 1, 1), rough=0.2, emit=(1, 1, 1), estr=2.5, coat=0)
    DK = mat('ink', (0.05, 0.03, 0.04), rough=0.5, coat=0)
    MO = mat('mouth', (0.30, 0.05, 0.08), rough=0.4, coat=0.3)
    TG = mat('tongue', (0.98, 0.42, 0.50), rough=0.35, coat=0.4)
    TEAR = mat('tear', (0.45, 0.80, 1.0), rough=0.05, coat=1.0, emit=(0.4, 0.75, 1.0), estr=0.4)
    STAR = mat('star', (1.0, 0.85, 0.3), rough=0.2, emit=(1.0, 0.8, 0.25), estr=1.2, coat=0)
    IR = mat('iris', iris, rough=0.15, coat=1.0) if iris else None
    E = {k: [] for k in EXPRS}

    def open_eyes(key, scale=1.0, big_hl=False, wet=False, pupil_small=False):
        for s in (-1, 1):
            x = s * ex
            if pupil_small:
                E[key].append(feat(H, x, ez, er * 1.02, mat('eyewhite', (0.98, 0.98, 0.96), rough=0.2), scale=(0.9, 0.34, 1.12)))
                E[key].append(feat(H, x, ez, er * 0.42, D, scale=(0.9, 0.42, 1.1), lift=0.03))
                E[key].append(feat(H, x - er * 0.12, ez + er * 0.14, er * 0.14, W, scale=(1, 0.4, 1), lift=0.055, seg=12))
                continue
            if IR is not None:
                E[key].append(feat(H, x, ez, er * scale, IR, scale=(0.9, 0.42, 1.12)))
                E[key].append(feat(H, x, ez - 0.01, er * 0.55 * scale, D, scale=(0.9, 0.4, 1.1), lift=0.012))
            else:
                E[key].append(feat(H, x, ez, er * scale, D, scale=(0.9, 0.42, 1.12)))
            hr = er * (0.42 if big_hl else 0.32) * scale
            E[key].append(feat(H, x - er * 0.32, ez + er * 0.42, hr, W, scale=(1, 0.4, 1), lift=0.03, seg=20))
            E[key].append(feat(H, x + er * 0.35, ez - er * 0.4, hr * 0.5, W, scale=(1, 0.4, 1), lift=0.03, seg=16))
            if big_hl:
                E[key].append(feat(H, x + er * 0.12, ez + er * 0.05, hr * 0.35, W, scale=(1, 0.4, 1), lift=0.035, seg=12))
            if wet:
                E[key].append(feat(H, x, ez - er * 0.82, er * 0.75, TEAR, scale=(1.2, 0.35, 0.38), lift=0.018))

    def mouth_w(key):
        E[key] += arc(H, -0.05, mouth_dz, 0.1, -0.035, 0.016, DK, lift=0.02)
        E[key] += arc(H, 0.05, mouth_dz, 0.1, -0.035, 0.016, DK, lift=0.02)

    # n 기본
    open_eyes('n')
    mouth_w('n')
    E['n'] += cheeks(H, ex + 0.08, ez - 0.16, 0.6)
    # b 깜빡 — 살짝 웃는 ‿ 감은 눈
    for s in (-1, 1):
        E['b'] += arc(H, s * ex, ez - 0.01, er * 1.9, -0.05, 0.02, DK, lift=0.02)
    mouth_w('b')
    E['b'] += cheeks(H, ex + 0.08, ez - 0.16, 0.6)
    # h 행복 — ^^ 눈 + 벌린 웃음
    for s in (-1, 1):
        E['h'] += arc(H, s * ex, ez - 0.03, er * 2.0, 0.08, 0.024, DK, lift=0.02)
    p, n = H.pt(0, mouth_dz - 0.04, 0.005)
    E['h'].append(sph(0.1, p, MO, scale=(1.1, 0.4, 0.75), rot=H.rot(n)))
    E['h'].append(feat(H, 0, mouth_dz - 0.075, 0.055, TG, scale=(1.2, 0.35, 0.6), lift=0.03))
    E['h'] += cheeks(H, ex + 0.07, ez - 0.15, 1.0)
    # s 슬픔 — 촉촉한 눈 + 걱정 눈썹 + ∩ 입 + 눈물 한 방울
    open_eyes('s', 1.05, big_hl=True, wet=True)
    for s in (-1, 1):
        a, _ = H.pt(s * (ex - 0.09), ez + er * 1.6, 0.015)
        b, _ = H.pt(s * (ex + 0.1), ez + er * 1.15, 0.015)
        E['s'] += capsule(a, b, 0.02, DK)
    E['s'] += arc(H, 0, mouth_dz - 0.03, 0.14, 0.045, 0.017, DK, lift=0.02)
    tp, tn = H.pt(-(ex + 0.02), ez - er * 1.75, 0.035)
    E['s'].append(sph(0.045, tp, TEAR, scale=(0.85, 0.6, 1.3), rot=H.rot(tn)))
    E['s'] += cheeks(H, ex + 0.08, ez - 0.19, 0.4)
    # x 신남 — 별 반짝 눈 + 활짝 입 + 진한 볼
    open_eyes('x', 1.12, big_hl=True)
    for s in (-1, 1):
        sp_, sn = H.pt(s * ex - er * 0.05, ez + er * 0.05, 0.045)
        E['x'].append(sph(er * 0.55, sp_, STAR, scale=(0.22, 0.3, 1.0), rot=H.rot(sn)))
        E['x'].append(sph(er * 0.55, sp_, STAR, scale=(1.0, 0.3, 0.22), rot=H.rot(sn)))
    p, n = H.pt(0, mouth_dz - 0.045, 0.005)
    E['x'].append(sph(0.125, p, MO, scale=(1.15, 0.4, 0.9), rot=H.rot(n)))
    E['x'].append(feat(H, 0.0, mouth_dz - 0.095, 0.07, TG, scale=(1.2, 0.35, 0.6), lift=0.03))
    E['x'] += cheeks(H, ex + 0.07, ez - 0.15, 1.4)
    # o 놀람·삐죽 — 작은 눈동자 + 치켜뜬 둥근 눈썹 + o 입
    open_eyes('o', pupil_small=True)
    for s in (-1, 1):
        E['o'] += arc(H, s * ex, ez + er * 1.75, er * 1.6, 0.03, 0.018, DK, n=5, lift=0.015)
    p, n = H.pt(0, mouth_dz - 0.03, 0.012)
    t = torus(0.045, 0.018, p, MO, scale=(1, 1, 1.25))
    t.rotation_mode = 'QUATERNION'
    t.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(n)
    E['o'].append(t)
    E['o'].append(sph(0.042, p, MO, scale=(0.9, 0.3, 1.1), rot=H.rot(n)))
    E['o'] += cheeks(H, ex + 0.08, ez - 0.17, 0.5)
    return E


def nose(H, dz, m, w=0.07):
    return feat(H, 0, dz, w, m, scale=(1.25, 0.6, 0.8), lift=0.02)


# ════════════ 네 캐릭터 ════════════
def fox():
    fur = mat('fox_fur', (0.80, 0.50, 0.22), rough=0.45, coat=0.3, sheen=0.3)
    cream = mat('fox_cream', (0.98, 0.92, 0.80), rough=0.45, coat=0.3)
    pink = mat('fox_ear', (1.0, 0.55, 0.55), rough=0.5, coat=0.2)
    dark = mat('fox_dark', (0.25, 0.13, 0.06), rough=0.45)
    base_and_body('fox', fur, cream, fur)
    # 꼬리 — 크고 폭신, 끝은 진한 갈색
    sph(0.24, (0.46, 0.25, 0.5), fur, scale=(0.9, 1.0, 1.35))
    sph(0.19, (0.6, 0.2, 0.82), fur, scale=(0.95, 1.0, 1.1))
    sph(0.13, (0.68, 0.14, 1.04), dark, scale=(1, 1, 1.1))
    H = Head(HEAD_C, 0.68, 0.58, 0.56)
    sph(1.0, H.c, fur, scale=(H.a, H.b, H.cc), seg=128)
    # 사막여우의 상징 — 머리만 한 귀(바깥으로 벌어짐)
    for s in (-1, 1):
        rot = (0, math.radians(34 * s), 0)
        cone(0.34, 0.035, 1.05, (s * 0.52, 0.06, 2.2), fur, rot=rot, scale=(1, 0.4, 1))
        cone(0.24, 0.025, 0.82, (s * 0.5, -0.03, 2.16), pink, rot=rot, scale=(1, 0.28, 1))
    patch(H, 0, -0.2, 0.26, cream, sx=1.35, sz=0.85)        # 흰 주둥이·볼
    for s in (-1, 1):
        patch(H, s * 0.36, -0.12, 0.17, cream)
    nose(H, -0.13, mat('nose', (0.03, 0.02, 0.03), rough=0.15, coat=1.0))
    return H, build_expressions(H, 0.25, 0.02, 0.125, mouth_dz=-0.24)


def otter():
    fur = mat('ot_fur', (0.40, 0.23, 0.12), rough=0.4, coat=0.4, sheen=0.2)
    face = mat('ot_face', (0.90, 0.78, 0.60), rough=0.45, coat=0.3)
    limb = mat('ot_limb', (0.26, 0.14, 0.07), rough=0.4, coat=0.4)
    base_and_body('otter', fur, face, limb)
    capsule((0.28, 0.3, 0.33), (0.6, -0.05, 0.3), 0.14, fur, rb=0.07)
    # 손에 든 조개
    shell = mat('shell', (1.0, 0.66, 0.55), rough=0.25, coat=0.9)
    sph(0.13, (0, -0.5, 0.74), shell, scale=(1.1, 0.5, 0.9))
    for k in (-1, 0, 1):
        capsule((k * 0.06, -0.565, 0.68), (k * 0.03, -0.565, 0.82), 0.012, mat('shell_ln', (0.8, 0.35, 0.3), rough=0.4))
    H = Head(HEAD_C, 0.68, 0.58, 0.54)
    sph(1.0, H.c, fur, scale=(H.a, H.b, H.cc), seg=128)
    patch(H, 0, -0.08, 0.38, face, sx=1.15, sz=0.95)
    patch(H, 0, -0.2, 0.2, face, t=0.07, sx=1.3, sz=0.8)   # 볼록한 주둥이
    for s in (-1, 1):
        sph(0.12, (s * 0.6, 0.05, 1.86), fur, scale=(1, 0.6, 0.9))
        sph(0.065, (s * 0.6, -0.02, 1.86), limb, scale=(1, 0.4, 0.9))
    nose(H, -0.12, mat('nose', (0.03, 0.02, 0.03), rough=0.15, coat=1.0), w=0.08)
    wh = mat('whisker', (0.97, 0.95, 0.9), rough=0.4)
    for s in (-1, 1):
        for k in range(2):
            a, _ = H.pt(s * 0.2, -0.17 - k * 0.05, 0.02)
            b = a + Vector((s * 0.3, 0.1, 0.04 - k * 0.07))
            capsule(a, b, 0.009, wh)
    return H, build_expressions(H, 0.23, 0.07, 0.115, mouth_dz=-0.25)


def panda():
    fur = mat('rp_fur', (0.80, 0.25, 0.06), rough=0.42, coat=0.35, sheen=0.25)
    white = mat('rp_white', (0.98, 0.95, 0.90), rough=0.45, coat=0.3)
    dark = mat('rp_dark', (0.18, 0.06, 0.03), rough=0.4, coat=0.4)
    ring = mat('rp_ring', (0.95, 0.70, 0.42), rough=0.45)
    base_and_body('panda', fur, dark, dark)
    for i in range(5):
        t = i / 4
        sph(0.18 - 0.02 * i, (0.42 + 0.24 * math.sin(t * 1.6), 0.28 - 0.1 * t, 0.42 + 0.6 * t), fur if i % 2 == 0 else ring)
    H = Head(HEAD_C, 0.7, 0.58, 0.54)
    sph(1.0, H.c, fur, scale=(H.a, H.b, H.cc), seg=128)
    for s in (-1, 1):
        patch(H, s * 0.3, -0.16, 0.19, white)
        feat(H, s * 0.24, 0.27, 0.075, white, scale=(1.2, 0.3, 0.8), lift=-0.004)   # 눈썹 점
        a, _ = H.pt(s * 0.23, -0.06, 0.0)
        b, _ = H.pt(s * 0.26, -0.24, 0.0)
        capsule(a, b, 0.034, mat('rp_stripe', (0.50, 0.16, 0.05), rough=0.45))      # 눈물 줄무늬(털색 계열로 은은하게)
        rot = (0, math.radians(24 * s), 0)
        cone(0.24, 0.08, 0.36, (s * 0.5, 0.04, 2.02), white, rot=rot, scale=(1, 0.45, 1))
        cone(0.17, 0.06, 0.28, (s * 0.49, -0.01, 2.0), fur, rot=rot, scale=(1, 0.35, 1))
    patch(H, 0, -0.21, 0.16, white, sx=1.3, sz=0.85)
    nose(H, -0.13, mat('nose', (0.03, 0.02, 0.03), rough=0.15, coat=1.0))
    return H, build_expressions(H, 0.25, 0.06, 0.115, mouth_dz=-0.25)


def cat():
    cream = mat('rd_cream', (0.94, 0.88, 0.78), rough=0.45, coat=0.3, sheen=0.4)
    point = mat('rd_point', (0.30, 0.19, 0.12), rough=0.45, coat=0.3)
    mask = mat('rd_mask', (0.55, 0.40, 0.30), rough=0.45, coat=0.3)
    white = mat('rd_white', (1.0, 0.99, 0.97), rough=0.45, coat=0.3, sheen=0.4)
    base_and_body('cat', cream, white, cream)
    sph(0.27, (0, -0.24, 0.88), white, scale=(1.1, 0.6, 0.9))   # 가슴 갈기
    sph(0.2, (0.48, 0.25, 0.48), point, scale=(0.9, 1, 1.4))
    sph(0.16, (0.6, 0.2, 0.8), point, scale=(0.95, 1, 1.2))
    H = Head(HEAD_C, 0.7, 0.58, 0.56)
    sph(1.0, H.c, cream, scale=(H.a, H.b, H.cc), seg=128)
    patch(H, 0, 0.0, 0.36, mask, sx=1.2, sz=0.95)          # 얼굴 마스크
    patch(H, 0, -0.21, 0.18, white, t=0.03, sx=1.35, sz=0.85)
    for s in (-1, 1):
        rot = (0, math.radians(22 * s), 0)
        cone(0.23, 0.035, 0.5, (s * 0.44, 0.05, 2.08), point, rot=rot, scale=(1, 0.55, 1))
        cone(0.14, 0.025, 0.36, (s * 0.43, -0.03, 2.05), mat('rd_ear', (1.0, 0.65, 0.65), rough=0.5), rot=rot, scale=(1, 0.3, 1))
    nose(H, -0.12, mat('rd_nose', (0.95, 0.48, 0.52), rough=0.25, coat=0.8), w=0.055)
    wh = mat('whisker', (0.97, 0.95, 0.9), rough=0.4)
    for s in (-1, 1):
        for k in range(2):
            a, _ = H.pt(s * 0.24, -0.16 - k * 0.05, 0.01)
            capsule(a, a + Vector((s * 0.3, 0.1, 0.03 - k * 0.06)), 0.008, wh)
    return H, build_expressions(H, 0.25, 0.04, 0.13, iris=(0.10, 0.42, 1.0), mouth_dz=-0.23)



BUILD = {'fox': fox, 'otter': otter, 'panda': panda, 'cat': cat}


def render_species(sp):
    sc = studio()
    H, E = BUILD[sp]()
    for ex in EXPRS:
        for k, objs in E.items():
            for o in objs:
                o.hide_render = (k != ex)
        sc.render.filepath = os.path.join(OUTDIR, "%s-%s.png" % (sp, ex))
        bpy.ops.render.render(write_still=True)
        print("RENDERED", sp, ex)


def tile():
    """홈 타일용 장난감 — 작은 윷판 위 윷가락 넷 + 여우·수달 말 (tiles_toybox 와 같은 스튜디오)."""
    sc = studio(tile=True)
    wood = mat('mat_wood', (0.72, 0.46, 0.24), rough=0.35, coat=0.6)
    paper = mat('hanji', (0.95, 0.88, 0.72), rough=0.6, coat=0.2)
    ink = mat('ink2', (0.10, 0.07, 0.06), rough=0.5, coat=0)
    red = mat('dot_red', (0.86, 0.14, 0.09), rough=0.3, coat=0.6)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.3, 0.07))
    o = bpy.context.object
    o.scale = (2.3, 2.3, 0.14)
    bpy.ops.object.transform_apply(scale=True)
    _fin(o, wood, bevel=0.06)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.3, 0.15))
    o = bpy.context.object
    o.scale = (2.0, 2.0, 0.02)
    bpy.ops.object.transform_apply(scale=True)
    _fin(o, paper, bevel=0.005)
    # 말밭 점
    cx, cy, S = 0.0, 0.3, 0.84
    pts = []
    for k in range(5):
        t = -S + 2 * S * k / 4
        pts += [(t, cy - S), (t, cy + S), (-S, cy + t), (S, cy + t)]
    for k in (1, 2, 4, 5):
        t = -S + 2 * S * k / 6
        pts += [(t, cy + t), (t, cy - t)]
    pts.append((0, cy))
    # 먹선 — 네모 둘레 + 대각선 둘
    def seg(x0, y0, x1, y1):
        L = math.hypot(x1 - x0, y1 - y0)
        bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, 0.165))
        o = bpy.context.object
        o.scale = (L, 0.03, 0.01)
        o.rotation_euler = (0, 0, math.atan2(y1 - y0, x1 - x0))
        bpy.ops.object.transform_apply(scale=True)
        _fin(o, ink, smooth=False)
    for (x0, y0, x1, y1) in ((-S, cy - S, S, cy - S), (-S, cy + S, S, cy + S), (-S, cy - S, -S, cy + S), (S, cy - S, S, cy + S),
                             (-S, cy - S, S, cy + S), (-S, cy + S, S, cy - S)):
        seg(x0, y0, x1, y1)
    for (x, y) in set((round(a, 3), round(b, 3)) for a, b in pts):
        big = abs(abs(x) - S) < 1e-3 and abs(abs(y - cy) - S) < 1e-3 or (x == 0 and y == cy)
        cyl(0.11 if big else 0.07, 0.03, (x, y, 0.175), red if big else ink, bevel=0.01)
    # 윷가락 넷 — 공중에 흩날린다
    flat = mat('stick_flat', (0.96, 0.86, 0.62), rough=0.35, coat=0.6)
    back = mat('stick_back', (0.62, 0.34, 0.14), rough=0.35, coat=0.6)
    for i, (x, y, z, rz, rx) in enumerate(((-0.95, -0.1, 2.05, 20, 30), (-0.2, 0.1, 2.45, -35, 150),
                                           (0.5, 0.0, 2.25, 60, -20), (1.05, -0.2, 1.75, -10, 190))):
        e = bpy.data.objects.new("stk", None)
        bpy.context.collection.objects.link(e)
        e.location = (x, y, z)
        e.rotation_euler = (math.radians(rx), math.radians(70), math.radians(rz))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.95, vertices=32, location=(0, 0, 0))
        c = bpy.context.object
        c.scale = (1, 0.55, 1)
        _fin(c, back)
        c.parent = e
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.045, 0))
        f = bpy.context.object
        f.scale = (0.19, 0.02, 0.92)
        _fin(f, flat, bevel=0.01)
        f.parent = e
    return sc


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if argv and argv[0] == 'tile':
        sc = tile()
        # 말 둘(사막여우·랫서팬더)을 작게 줄여 판 위에 세운다 — 새로 생긴 오브젝트만 빈 부모에 묶어 축소
        for sp, ex, loc, rz in (('fox', 'h', (-0.5, 0.05), 18), ('panda', 'x', (0.55, 0.35), -16)):
            before = set(bpy.data.objects)
            H, E = BUILD[sp]()
            for k, objs in E.items():
                for o in objs:
                    o.hide_render = (k != ex)
            new = [o for o in bpy.data.objects if o not in before]
            bpy.ops.object.empty_add(location=(0, 0, 0))
            root = bpy.context.object
            for o in new:
                if o.parent is None:
                    o.parent = root
            root.scale = (0.52, 0.52, 0.52)
            root.location = (loc[0], loc[1], 0.16)
            root.rotation_euler = (0, 0, math.radians(rz))
        sc.render.filepath = os.path.join(TILEDIR, "yut.png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED tile")
    else:
        for sp in (argv or SPECIES):
            render_species(sp)
