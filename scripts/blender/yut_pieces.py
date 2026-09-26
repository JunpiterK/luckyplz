# -*- coding: utf-8 -*-
"""윷놀이 말 4종 — 사막여우 · 수달 · 랫서팬더 · 랙돌 고양이.

2026-09-25 신설 → 2026-09-27 v2 '캐릭터성 강화' 전면 재설계.
운영자: "말들의 캐릭터들이 더 귀엽고 캐릭터성이 강하게." v1 은 머리가 몸과 비슷한 크기의 '앉은 인형'이라
폰(말 ≈58px)에서 얼굴이 점 몇 개로만 보였다. v2 원칙:
  - 치비 비율 — 머리 ≈ 전체 키의 60%, 머리가 몸보다 훨씬 넓다(정사각 셀도 더 꽉 찬다)
  - 큰 유광 눈 — 홍채색 + 아래쪽 밝은 홍채 반사 + 흰 하이라이트 2~3개. 눈을 얼굴 아래쪽에 둔다(아기 도식)
  - 종마다 실루엣 하나로 알아보는 표식 — 여우: 거대한 V 귀 + 볼 털 + 끝이 검은 큰 꼬리 /
    수달: 동글 귀 + 통통한 볼 + 수염 패드 + 조개 / 랫서팬더: 흰 얼굴 마스크 + 눈물 줄무늬 + 줄무늬 꼬리 /
    랙돌: 흰 목 갈기 + 파란 눈 + 포인트 컬러(귀·마스크·꼬리) + 흰 장갑
  - 표정마다 몸짓도 바꾼다(귀가 처지고 팔이 올라간다) — 표정만 바꾸면 58px 에서 차이가 안 읽힌다

홈 타일 '레트로 장난감 진열장'(tiles_toybox.py)과 같은 문법 —
코팅 플라스틱 + 잉크 외곽선(Freestyle) + Standard 뷰 변환(AgX 는 원색을 파스텔로 누른다).
tiles_toybox.py 는 다른 작업이 소유하므로 **이 파일은 독립 스크립트**다(헬퍼 복사본 포함).

표정 8종 — 표정마다 장면을 새로 짓는다(팔·귀 자세가 표정과 함께 바뀌므로 숨김 토글로는 안 된다).
  n 기본 · b 깜빡 · h 행복(^^) · s 울먹 · x 신남(별눈 + 두 손 번쩍) · o 놀람(작은 눈동자 + 손 벌림)
  c 엉엉(>< 눈 + 눈물 줄기 + 귀 축 처짐 — 잡혔을 때) · w 성격 포즈
    여우 = 윙크 + 메롱 + 손 흔들기(장난꾸러기) / 수달 = 두 손으로 볼 부비부비 /
    랫서팬더 = 두 팔 활짝 '크게 보이기' 위협(귀엽게) / 랙돌 = 하품 + 앞발

실행:
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/yut_pieces.py              # 말 32장
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/yut_pieces.py -- fox:n,w   # 일부만
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/yut_pieces.py -- tile      # 홈 타일용 장난감
출력: scripts/og-assets/yut/<sp>-<ex>.png (투명) → scripts/build_yut_atlas.py 가
      public/assets/yut/pieces.webp (4행 × 8열 아틀라스)로 묶는다.
"""
import bpy
import math
import os
import sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "..", "og-assets", "yut")
TILEDIR = os.path.join(HERE, "..", "og-assets", "tiles3d")
os.makedirs(OUTDIR, exist_ok=True)
RES = int(os.environ.get('YP_RES', '560'))
SAMPLES = int(os.environ.get('YP_SAMPLES', '96'))

SPECIES = ['fox', 'otter', 'panda', 'cat']
EXPRS = ['n', 'b', 'h', 's', 'x', 'o', 'c', 'w']
_MATS = {}
_DANCE = None        # 군무 자세 렌더 중이면 DPOSE 항목(dict), 보드 말이면 None
_HEAD_MARK = None    # Head() 를 만든 순간의 오브젝트 집합 — 그 뒤에 생긴 것 = 머리 묶음(고개 기울이기)


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
    th = 2.4 if tile else 2.2
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
    area((4.5, 4.0, 4.5), 560 * k, 4, (0.72, 0.82, 1.0))     # 림 — 치비 머리 윤곽을 살린다
    area((1.0, -7.5, 1.8), 170 * k, 6, (1.0, 1.0, 1.0))
    area((0.0, 0.0, 9.0), 140 * k, 6, (1.0, 1.0, 1.0))
    if tile:
        bpy.ops.object.camera_add(location=(0, -7.6, 4.0))
        cam = bpy.context.object
        cam.data.lens = 78
        tgt = Vector((0, 0, 1.12))
    else:
        # 말은 보드 위에서 정면 약간 위(≈22°)에서 본다 — 얼굴이 가장 잘 읽히는 각
        bpy.ops.object.camera_add(location=(0, -9.2, 4.9))
        cam = bpy.context.object
        cam.data.lens = 80
        tgt = Vector((0, 0, 1.3))
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


def ear(tip_dir, base, length, r, m, flat=0.42):
    """원뿔 귀 — base 에서 tip_dir(단위벡터) 방향으로 뻗는다. 납작하게(flat) 눌러 앞면이 카메라를 본다."""
    d = Vector(tip_dir).normalized()
    c = Vector(base) + d * (length / 2)
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r * 0.12, depth=length, location=c, vertices=40)
    o = bpy.context.object
    o.scale = (1, flat, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # 납작한 축(로컬 Y)이 항상 앞뒤(월드 Y)를 향하게 직접 축을 세운다 — to_track_quat 은 귀가 옆으로
    # 누우면 로컬 Y 를 위로 돌려, 처진 귀가 위아래로 납작한 가시가 되고 머리에서 떨어져 보였다(실측)
    y = Vector((0, 1, 0))
    y = (y - d * y.dot(d)).normalized()
    x = y.cross(d)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Matrix((x, y, d)).transposed().to_quaternion()
    return _fin(o, m)


# ════════════ 머리 좌표 — 타원체 표면 위에 이목구비를 붙인다 ════════════
class Head:
    def __init__(self, c, a, b, cc):
        global _HEAD_MARK
        _HEAD_MARK = set(bpy.data.objects)
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
    pts = []
    for i in range(n):
        u = -1 + 2 * i / (n - 1)
        pts.append(H.pt(cx + u * w / 2, cz + h * (1 - u * u), lift)[0])
    for i in range(n - 1):
        capsule(pts[i], pts[i + 1], t, m)


def line(H, x0, z0, x1, z1, t, m, lift=0.015):
    capsule(H.pt(x0, z0, lift)[0], H.pt(x1, z1, lift)[0], t, m)


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


# ════════════ 공통 몸 ════════════
TEAM = {
    'fox': (0.98, 0.62, 0.05),     # 사막 햇볕 노랑
    'otter': (0.08, 0.36, 0.95),   # 물빛 파랑
    'panda': (0.88, 0.10, 0.12),   # 단풍 빨강
    'cat': (0.50, 0.26, 0.95),     # 라벤더 보라
}
HEAD_C = (0, 0, 1.5)
HA, HB, HC = 0.86, 0.72, 0.70      # 치비 머리 — 몸통(반지름 .42)의 두 배 폭
SHOULDER = (0.32, -0.08, 0.76)
# 손 위치(오른쪽 = +x = 화면 오른쪽). 왼손은 x 부호만 뒤집는다
HANDS = {
    'rest': ((0.15, -0.44, 0.5), (-0.15, -0.44, 0.5)),       # 배 앞에 모은 손
    'up': ((0.52, -0.56, 0.98), (-0.52, -0.56, 0.98)),       # 턱 옆으로 번쩍(만세)
    'out': ((0.6, -0.48, 0.84), (-0.6, -0.48, 0.84)),        # 놀라서 벌린 손
    'big': ((0.94, -0.3, 1.1), (-0.94, -0.3, 1.1)),          # 머리 옆으로 활짝(크게 보이기)
    'cheek': ((0.66, -0.46, 1.2), (-0.66, -0.46, 1.2)),      # 볼 부비부비
    'chin': ((0.26, -0.62, 0.86), (-0.26, -0.62, 0.86)),     # 엉엉 — 턱 밑 주먹
    'wave': ((0.84, -0.4, 1.06), (-0.15, -0.44, 0.5)),       # 한 손 흔들기
    'yawn': ((0.3, -0.74, 1.15), (-0.15, -0.44, 0.5)),       # 앞발로 입가 가리기
}


def base(sp):
    tc = mat('team_' + sp, TEAM[sp], rough=0.25, coat=0.8)
    if _DANCE is not None:      # 군무 자세는 받침 없이 두 발로 선다
        return tc
    gold = mat('gold', (0.95, 0.70, 0.22), rough=0.2, metal=1.0, coat=0.0)
    cyl(0.62, 0.2, (0, 0, 0.1), tc, bevel=0.06)
    torus(0.6, 0.035, (0, 0, 0.2), gold)
    cyl(0.48, 0.04, (0, 0, 0.215), mat('team_lt_' + sp, tuple(min(1, c * 0.55 + 0.45) for c in TEAM[sp]), rough=0.3), bevel=0.01)
    return tc


def body(sp, fur, belly, limb, pose, tc, mitt=None):
    # 몸통 — 작게(치비). 머리 밑에 반쯤 숨는다
    sph(0.42, (0, 0.06, 0.56), fur, scale=(1.0, 0.92, 0.92))
    sph(0.3, (0, -0.2, 0.54), belly, scale=(1.0, 0.5, 1.0))
    if _DANCE is None:          # 앉은 발 — 군무 자세는 dance_legs() 가 몸을 기울인 뒤 다리를 따로 붙인다
        for s in (-1, 1):
            sph(0.15, (s * 0.22, -0.34, 0.3), mitt or limb, scale=(1.0, 1.35, 0.7))
    else:
        _DANCE['_limb'] = mitt or limb
        _DANCE['_leg'] = limb
    # 팀 색 목 리본 — 턱 아래로 보이는 매듭만
    sph(0.075, (0, -0.44, 0.8), tc, scale=(1, 0.7, 0.9))
    for s in (-1, 1):
        sph(0.1, (s * 0.12, -0.42, 0.8), tc, scale=(1.25, 0.55, 0.8))
    hr, hl = (_DANCE['R'], _DANCE['L']) if _DANCE is not None else HANDS[pose]
    for s, h in ((1, hr), (-1, hl)):
        sh = (s * SHOULDER[0], SHOULDER[1], SHOULDER[2]) if _DANCE is None else (s * 0.36, -0.08, 0.86)
        capsule(sh, h, 0.12 if _DANCE is None else 0.105, limb, rb=0.11 if _DANCE is None else 0.095)
        sph(0.14 if _DANCE is None else 0.155, h, mitt or limb, scale=(1.0, 0.9, 0.95))
    return hr, hl


# ════════════ 표정 ════════════
def blush(H, x, dz, strength=1.0):
    m = mat('blush%.1f' % strength, (1.0, 0.46 - 0.1 * strength, 0.52 - 0.1 * strength), rough=0.5, coat=0.1)
    for s in (-1, 1):
        feat(H, s * x, dz, 0.12, m, scale=(1.3, 0.22, 0.72), lift=0.014)


class Face:
    """종별 눈 위치·홍채색만 다르고 표정 로직은 공통."""

    def __init__(self, H, ex, ez, er, iris, mouth, blush_x=None, blush_dz=None):
        self.H, self.ex, self.ez, self.er, self.mouth = H, ex, ez, er, mouth
        self.bx = blush_x if blush_x is not None else ex + 0.14
        self.bz = blush_dz if blush_dz is not None else ez - er * 1.05
        self.D = mat('eye', (0.02, 0.02, 0.035), rough=0.1, coat=1.0)
        self.IRd = mat('iris_d', tuple(c * 0.42 for c in iris), rough=0.12, coat=1.0)
        self.IR = mat('iris', iris, rough=0.15, coat=1.0, emit=iris, estr=0.25)
        self.W = mat('hl', (1, 1, 1), rough=0.2, emit=(1, 1, 1), estr=2.5, coat=0)
        self.K = mat('ink', (0.05, 0.03, 0.04), rough=0.5, coat=0)
        self.MO = mat('mouth', (0.30, 0.05, 0.08), rough=0.4, coat=0.3)
        self.TG = mat('tongue', (0.98, 0.42, 0.50), rough=0.35, coat=0.4)
        self.TEAR = mat('tear', (0.45, 0.80, 1.0), rough=0.05, coat=1.0, emit=(0.4, 0.75, 1.0), estr=0.5)
        self.STAR = mat('star', (1.0, 0.85, 0.3), rough=0.2, emit=(1.0, 0.8, 0.25), estr=1.3, coat=0)
        self.WH = mat('eyewhite', (0.98, 0.98, 0.96), rough=0.2)

    # ── 눈 ──
    def eye(self, s, scale=1.0, big=False, wet=False, star=False):
        H, er = self.H, self.er * scale
        x, ez = s * self.ex, self.ez
        feat(H, x, ez, er, self.IRd, scale=(0.86, 0.42, 1.1))                        # 짙은 홍채 바탕
        feat(H, x, ez - er * 0.38, er * 0.66, self.IR, scale=(0.95, 0.4, 0.62), lift=0.012)   # 아래쪽 밝은 홍채
        feat(H, x, ez + er * 0.08, er * 0.5, self.D, scale=(0.9, 0.4, 1.05), lift=0.022)     # 동공
        if star:
            p, n = H.pt(x, ez + er * 0.02, 0.05)
            sph(er * 0.62, p, self.STAR, scale=(0.2, 0.3, 1.0), rot=H.rot(n))
            sph(er * 0.62, p, self.STAR, scale=(1.0, 0.3, 0.2), rot=H.rot(n))
        hr = er * (0.4 if big else 0.34)
        feat(H, x - er * 0.3, ez + er * 0.4, hr, self.W, scale=(1, 0.4, 1), lift=0.045, seg=20)
        feat(H, x + er * 0.34, ez - er * 0.34, hr * 0.46, self.W, scale=(1, 0.4, 1), lift=0.045, seg=16)
        if big:
            feat(H, x + er * 0.1, ez + er * 0.52, hr * 0.3, self.W, scale=(1, 0.4, 1), lift=0.05, seg=12)
        if wet:   # 아랫눈꺼풀에 고인 눈물
            feat(H, x, ez - er * 0.86, er * 0.78, self.TEAR, scale=(1.15, 0.34, 0.34), lift=0.02)

    def eyes(self, **kw):
        for s in (-1, 1):
            self.eye(s, **kw)

    def eye_small(self, s):
        H, er, x, ez = self.H, self.er, s * self.ex, self.ez
        feat(H, x, ez, er * 1.02, self.WH, scale=(0.9, 0.36, 1.12))
        feat(H, x, ez, er * 0.5, self.IRd, scale=(0.9, 0.42, 1.1), lift=0.05)
        feat(H, x, ez, er * 0.3, self.D, scale=(0.9, 0.42, 1.1), lift=0.066)
        feat(H, x - er * 0.14, ez + er * 0.16, er * 0.13, self.W, scale=(1, 0.4, 1), lift=0.085, seg=12)

    def closed(self, s, up):
        """up=True ^ (행복), False ‿ (평온한 감은 눈)"""
        arc(self.H, s * self.ex, self.ez - (0.02 if up else 0.0), self.er * 2.0, 0.085 if up else -0.06,
            0.026, self.K, lift=0.02)

    def squeeze(self, s):
        """> < — 꼭 감은 눈. 안쪽(코 쪽)이 꼭짓점"""
        H, er, x, ez = self.H, self.er, s * self.ex, self.ez
        tip = x - s * er * 0.55
        for dz in (er * 0.62, -er * 0.62):
            line(H, x + s * er * 0.75, ez + dz, tip, ez, 0.028, self.K, lift=0.02)

    # ── 눈썹 ──
    def brows(self, kind):
        if getattr(self, 'no_brows', False):
            return
        H, er, ex, ez = self.H, self.er, self.ex, self.ez
        for s in (-1, 1):
            if kind == 'worry':      # 안쪽이 올라간 八
                line(H, s * (ex - er * 0.7), ez + er * 1.75, s * (ex + er * 0.75), ez + er * 1.3, 0.022, self.K)
            elif kind == 'up':       # 치켜뜬 둥근 눈썹
                arc(H, s * ex, ez + er * 1.75, er * 1.5, 0.035, 0.02, self.K, n=5, lift=0.015)
            elif kind == 'mad':      # 안쪽이 내려간 V (귀엽게 화남)
                line(H, s * (ex - er * 0.75), ez + er * 1.3, s * (ex + er * 0.7), ez + er * 1.72, 0.026, self.K)

    # ── 입 ──
    def mouth_w(self):
        H, mz = self.H, self.mouth
        arc(H, -0.05, mz, 0.1, -0.035, 0.017, self.K, lift=0.02)
        arc(H, 0.05, mz, 0.1, -0.035, 0.017, self.K, lift=0.02)

    def mouth_open(self, w=0.1, h=0.75, tongue=True):
        H, mz = self.H, self.mouth
        p, n = H.pt(0, mz - 0.04 - (h - 0.75) * 0.06, 0.005)
        sph(w, p, self.MO, scale=(1.15, 0.4, h), rot=H.rot(n))
        if tongue:
            feat(H, 0, mz - 0.05 - w * h * 0.55, w * 0.58, self.TG, scale=(1.2, 0.35, 0.6), lift=0.03)

    def mouth_o(self):
        H, mz = self.H, self.mouth
        p, n = H.pt(0, mz - 0.03, 0.012)
        t = torus(0.045, 0.018, p, self.MO, scale=(1, 1, 1.25))
        t.rotation_mode = 'QUATERNION'
        t.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(n)
        sph(0.042, p, self.MO, scale=(0.9, 0.3, 1.1), rot=H.rot(n))

    def mouth_frown(self):
        arc(self.H, 0, self.mouth - 0.035, 0.14, 0.045, 0.018, self.K, lift=0.02)

    def mouth_bleh(self):
        """메롱 — 살짝 웃는 입 + 한쪽으로 삐죽 나온 혀"""
        H, mz = self.H, self.mouth
        arc(H, 0, mz, 0.16, -0.04, 0.017, self.K, lift=0.02)
        feat(H, 0.035, mz - 0.07, 0.058, self.TG, scale=(1.0, 0.5, 1.2), lift=0.03)

    def tears_stream(self):
        """엉엉 — 눈 밑에서 볼을 타고 흐르는 두 줄기 + 떨어지는 방울"""
        H, er, ex, ez = self.H, self.er, self.ex, self.ez
        for s in (-1, 1):
            pts = [H.pt(s * (ex + er * 0.2 + 0.05 * k), ez - er * 0.7 - 0.09 * k, 0.03)[0] for k in range(5)]
            for i in range(4):
                capsule(pts[i], pts[i + 1], 0.034 + 0.006 * i, self.TEAR)
            p, n = H.pt(s * (ex + er * 0.2 + 0.26), ez - er * 0.7 - 0.5, 0.05)
            sph(0.05, p, self.TEAR, scale=(0.85, 0.6, 1.3), rot=H.rot(n))

    def build(self, ex, sp):
        E = ex
        if E == 'n':
            self.eyes()
            self.mouth_w()
            blush(self.H, self.bx, self.bz, 0.6)
        elif E == 'b':
            for s in (-1, 1):
                self.closed(s, False)
            self.mouth_w()
            blush(self.H, self.bx, self.bz, 0.7)
        elif E == 'h':
            for s in (-1, 1):
                self.closed(s, True)
            self.mouth_open(0.1, 0.75)
            blush(self.H, self.bx, self.bz, 1.1)
        elif E == 's':
            self.eyes(scale=1.06, big=True, wet=True)
            self.brows('worry')
            self.mouth_frown()
            p, n = self.H.pt(-(self.ex + 0.03), self.ez - self.er * 1.9, 0.035)
            sph(0.05, p, self.TEAR, scale=(0.85, 0.6, 1.3), rot=self.H.rot(n))
            blush(self.H, self.bx, self.bz, 0.5)
        elif E == 'x':
            self.eyes(scale=1.1, big=True, star=True)
            self.mouth_open(0.13, 0.95)
            blush(self.H, self.bx, self.bz, 1.4)
        elif E == 'o':
            for s in (-1, 1):
                self.eye_small(s)
            self.brows('up')
            self.mouth_o()
            blush(self.H, self.bx, self.bz, 0.5)
        elif E == 'c':
            for s in (-1, 1):
                self.squeeze(s)
            self.brows('worry')
            self.mouth_open(0.12, 1.25, tongue=True)
            self.tears_stream()
            blush(self.H, self.bx, self.bz, 1.2)
        elif E == 'f':
            # 군무 'BAD' 표정 — 치켜 V 눈썹 + 한쪽 입꼬리만 씩. 무섭지 않게 눈은 그대로 크고 반짝인다
            self.eyes(scale=0.97)
            self.brows('mad')
            H, mz = self.H, self.mouth
            arc(H, 0.015, mz, 0.12, -0.022, 0.017, self.K, n=5, lift=0.02)
            line(H, 0.075, mz - 0.004, 0.105, mz + 0.03, 0.017, self.K, lift=0.02)
            blush(self.H, self.bx, self.bz, 0.7)
        elif E == 'w':
            if sp == 'fox':          # 윙크 + 메롱
                self.eye(-1, big=True)
                arc(self.H, self.ex, self.ez, self.er * 2.0, 0.085, 0.028, self.K, lift=0.02)
                self.brows_one_up()
                self.mouth_bleh()
                blush(self.H, self.bx, self.bz, 1.2)
            elif sp == 'otter':      # 볼 부비부비 — 행복하게 감은 눈 + 진한 볼
                for s in (-1, 1):
                    self.closed(s, True)
                self.mouth_open(0.085, 0.7)
                blush(self.H, self.bx, self.bz, 1.6)
            elif sp == 'panda':      # 크게 보이기 — 부릅뜬(그래도 귀여운) 눈 + '와앙' 입
                self.eyes(scale=1.05)
                self.brows('mad')
                self.mouth_open(0.12, 1.0, tongue=False)
                fang = mat('fang', (1, 1, 1), rough=0.3)
                for s in (-1, 1):
                    p, n = self.H.pt(s * 0.06, self.mouth - 0.02, 0.035)
                    cone(0.022, 0.002, 0.05, p, fang, rot=(math.pi, 0, 0))
                blush(self.H, self.bx, self.bz, 1.0)
            else:                    # 하품 — 꼭 감은 눈 + 크게 벌린 입
                for s in (-1, 1):
                    arc(self.H, s * self.ex, self.ez - 0.01, self.er * 1.9, -0.03, 0.026, self.K, lift=0.02)
                self.mouth_open(0.13, 1.35)
                blush(self.H, self.bx, self.bz, 0.8)

    def brows_one_up(self):
        arc(self.H, -self.ex, self.ez + self.er * 1.75, self.er * 1.5, 0.05, 0.02, self.K, n=5, lift=0.015)


def nose(H, dz, m, w=0.07):
    return feat(H, 0, dz, w, m, scale=(1.25, 0.6, 0.8), lift=0.02)


def whiskers(H, x0, dz, n, m, span=0.34, t=0.009):
    for s in (-1, 1):
        for k in range(n):
            a, _ = H.pt(s * x0, dz - k * 0.045, 0.02)
            capsule(a, a + Vector((s * span, 0.1, 0.05 - k * 0.06)), t, m)


# 표정별 자세 — 몸짓이 표정을 58px 에서도 읽히게 한다
POSE = {'n': 'rest', 'b': 'rest', 'h': 'rest', 's': 'rest', 'x': 'up', 'o': 'out', 'c': 'chin', 'f': 'rest'}
PERSONA = {'fox': 'wave', 'otter': 'cheek', 'panda': 'big', 'cat': 'yawn'}
DROOP = {'s': 0.55, 'c': 1.0}   # 귀 처짐 정도


# ════════════ 네 캐릭터 ════════════
def fox(ex):
    fur = mat('fox_fur', (0.86, 0.56, 0.26), rough=0.45, coat=0.3, sheen=0.3)
    cream = mat('fox_cream', (0.99, 0.94, 0.84), rough=0.45, coat=0.3)
    pink = mat('fox_ear', (1.0, 0.6, 0.58), rough=0.5, coat=0.2)
    dark = mat('fox_dark', (0.22, 0.11, 0.05), rough=0.45)
    tc = base('fox')
    pose = PERSONA['fox'] if ex == 'w' else POSE[ex]
    body('fox', fur, cream, fur, pose, tc)
    # 꼬리 — 크고 폭신하게 옆으로 휘어 올라가고, 끝은 검다(사막여우 표식)
    sph(0.3, (0.56, 0.3, 0.52), fur, scale=(0.9, 1.0, 1.3))
    sph(0.27, (0.8, 0.24, 0.9), fur, scale=(0.95, 1.0, 1.1))
    sph(0.2, (0.92, 0.18, 1.2), dark, scale=(1, 1, 1.1))
    H = Head(HEAD_C, HA, HB, HC)
    sph(1.0, H.c, fur, scale=(H.a, H.b, H.cc), seg=128)
    # 머리만 한 V 귀 — 처지면 옆으로 눕는다
    dr = DROOP.get(ex, 0.0)
    for s in (-1, 1):
        ang = math.radians(30 + 32 * dr)
        d = (s * math.sin(ang), 0.05, math.cos(ang))
        b0 = (s * (0.48 + 0.1 * dr), 0.1, 1.9 - 0.1 * dr)
        ear(d, b0, 1.02 - 0.12 * dr, 0.47, fur, flat=0.42)
        ear(d, (b0[0], b0[1] - 0.14, b0[2] + 0.06), 0.8 - 0.1 * dr, 0.32, pink, flat=0.25)
    # 볼 털 — 옆으로 삐죽(실루엣 표식)
    for s in (-1, 1):
        for k, (dz, ln) in enumerate(((-0.12, 0.3), (-0.28, 0.24))):
            cone(0.11, 0.01, ln, (s * (HA - 0.02), -0.12, H.c.z + dz), cream,
                 rot=(0, math.radians(s * (100 + 18 * k)), 0), scale=(1, 0.6, 1))
    patch(H, 0, -0.33, 0.3, cream, sx=1.4, sz=0.8)          # 흰 주둥이
    for s in (-1, 1):
        patch(H, s * 0.5, -0.22, 0.22, cream)
    nose(H, -0.2, mat('nose', (0.03, 0.02, 0.03), rough=0.15, coat=1.0), w=0.065)
    F = Face(H, 0.31, -0.02, 0.19, (0.78, 0.44, 0.1), mouth=-0.29)
    F.build(ex, 'fox')


def otter(ex):
    fur = mat('ot_fur', (0.47, 0.28, 0.15), rough=0.4, coat=0.4, sheen=0.2)
    face = mat('ot_face', (0.95, 0.85, 0.70), rough=0.45, coat=0.3)
    limb = mat('ot_limb', (0.28, 0.15, 0.08), rough=0.4, coat=0.4)
    tc = base('otter')
    pose = PERSONA['otter'] if ex == 'w' else POSE[ex]
    hr, hl = body('otter', fur, face, limb, pose, tc)
    capsule((0.3, 0.32, 0.33), (0.66, -0.06, 0.3), 0.15, fur, rb=0.07)     # 납작한 꼬리
    # 조개 — 손을 모았을 때는 배 앞, 만세일 때는 오른손에 번쩍
    shell = mat('shell', (1.0, 0.68, 0.58), rough=0.25, coat=0.9)
    sln = mat('shell_ln', (0.82, 0.36, 0.32), rough=0.4)
    sp_ = None
    if _DANCE is not None:
        pass                     # 군무 중엔 조개를 내려놓는다(두 손이 춤을 춘다)
    elif pose == 'rest':
        sp_ = Vector((0, -0.56, 0.58))
    elif pose in ('up', 'out'):
        sp_ = Vector(hr) + Vector((0.02, -0.12, 0.1))
    if sp_ is not None:
        sph(0.15, sp_, shell, scale=(1.1, 0.5, 0.9))
        for k in (-1, 0, 1):
            capsule(sp_ + Vector((k * 0.07, -0.075, -0.07)), sp_ + Vector((k * 0.035, -0.075, 0.09)), 0.013, sln)
    H = Head(HEAD_C, HA, HB, HC - 0.02)
    sph(1.0, H.c, fur, scale=(H.a, H.b, H.cc), seg=128)
    # 통통한 볼 — 머리 실루엣이 아래로 둥글게 부푼다
    for s in (-1, 1):
        sph(0.3, (s * 0.58, -0.22, 1.2), face, scale=(1.0, 0.8, 0.85))
    patch(H, 0, -0.08, 0.5, face, sx=1.12, sz=0.95)
    # 동글 귀
    dr = DROOP.get(ex, 0.0)
    for s in (-1, 1):
        z = 1.98 - 0.12 * dr
        sph(0.14, (s * (0.74 + 0.04 * dr), 0.08, z), fur, scale=(1, 0.6, 0.9))
        sph(0.075, (s * (0.74 + 0.04 * dr), 0.0, z), limb, scale=(1, 0.4, 0.9))
    # 수염 패드 두 개 + 큰 코
    pad = mat('ot_pad', (0.99, 0.93, 0.82), rough=0.45, coat=0.3)
    for s in (-1, 1):
        feat(H, s * 0.085, -0.3, 0.11, pad, scale=(1.0, 0.6, 0.85), lift=0.03)
    nose(H, -0.22, mat('nose', (0.03, 0.02, 0.03), rough=0.15, coat=1.0), w=0.085)
    whiskers(H, 0.18, -0.28, 3, mat('whisker', (0.97, 0.95, 0.9), rough=0.4), span=0.34)
    F = Face(H, 0.3, 0.02, 0.18, (0.42, 0.24, 0.1), mouth=-0.37, blush_x=0.5, blush_dz=-0.2)
    F.build(ex, 'otter')


def panda(ex):
    fur = mat('rp_fur', (0.86, 0.30, 0.07), rough=0.42, coat=0.35, sheen=0.25)
    white = mat('rp_white', (0.99, 0.96, 0.91), rough=0.45, coat=0.3)
    dark = mat('rp_dark', (0.2, 0.07, 0.03), rough=0.4, coat=0.4)
    ring = mat('rp_ring', (0.98, 0.74, 0.46), rough=0.45)
    tc = base('panda')
    pose = PERSONA['panda'] if ex == 'w' else POSE[ex]
    body('panda', fur, dark, dark, pose, tc)
    # 줄무늬 꼬리 — 옆으로 크게 말려 올라간다
    for i in range(7):
        t = i / 6
        sph(0.21 - 0.018 * i, (0.5 + 0.34 * math.sin(t * 1.5), 0.3 - 0.12 * t, 0.42 + 0.85 * t),
            fur if i % 2 == 0 else ring)
    H = Head(HEAD_C, HA + 0.02, HB, HC - 0.02)
    sph(1.0, H.c, fur, scale=(H.a, H.b, H.cc), seg=128)
    # 흰 얼굴 마스크 — 볼 · 주둥이 · 눈썹 점 (랫서팬더 표식)
    for s in (-1, 1):
        patch(H, s * 0.5, -0.26, 0.27, white)
        feat(H, s * 0.3, 0.3, 0.09, white, scale=(1.25, 0.3, 0.8), lift=-0.004)
    patch(H, 0, -0.34, 0.24, white, sx=1.35, sz=0.85)
    # 눈물 줄무늬 — 눈 아래에서 주둥이 옆으로
    stripe = mat('rp_stripe', (0.45, 0.13, 0.04), rough=0.45)
    for s in (-1, 1):
        line(H, s * 0.34, -0.2, s * 0.3, -0.42, 0.04, stripe, lift=0.03)
    # 귀 — 흰 테두리 둥근 삼각
    dr = DROOP.get(ex, 0.0)
    for s in (-1, 1):
        ang = math.radians(28 + 32 * dr)
        d = (s * math.sin(ang), 0.05, math.cos(ang))
        b0 = (s * (0.52 + 0.08 * dr), 0.08, 1.96 - 0.08 * dr)
        ear(d, b0, 0.5, 0.3, white, flat=0.45)
        ear(d, (b0[0], b0[1] - 0.12, b0[2] + 0.03), 0.36, 0.2, dark, flat=0.25)
    nose(H, -0.24, mat('nose', (0.03, 0.02, 0.03), rough=0.15, coat=1.0), w=0.068)
    F = Face(H, 0.31, 0.0, 0.185, (0.62, 0.28, 0.08), mouth=-0.33)
    F.no_brows = True      # 흰 눈썹 점이 곧 눈썹 — 선을 겹치면 지저분하다(실측)
    F.build(ex, 'panda')


def cat(ex):
    cream = mat('rd_cream', (0.95, 0.9, 0.8), rough=0.45, coat=0.3, sheen=0.4)
    point = mat('rd_point', (0.33, 0.21, 0.14), rough=0.45, coat=0.3)
    mask = mat('rd_mask', (0.74, 0.6, 0.48), rough=0.45, coat=0.3)
    white = mat('rd_white', (1.0, 0.99, 0.97), rough=0.45, coat=0.3, sheen=0.4)
    tc = base('cat')
    pose = PERSONA['cat'] if ex == 'w' else POSE[ex]
    body('cat', cream, white, cream, pose, tc, mitt=white)       # 흰 장갑(미티드 랙돌)
    # 꼬리 — 포인트 색 깃털 꼬리
    sph(0.24, (0.52, 0.3, 0.5), point, scale=(0.9, 1, 1.35))
    sph(0.21, (0.72, 0.24, 0.84), point, scale=(0.95, 1, 1.2))
    sph(0.16, (0.8, 0.18, 1.1), point, scale=(1, 1, 1.1))
    H = Head(HEAD_C, HA, HB, HC)
    sph(1.0, H.c, cream, scale=(H.a, H.b, H.cc), seg=128)
    # 갈기 — 볼 옆으로 삐져나온 복슬 털 + 가슴 흰 턱받이(랙돌 표식)
    for s in (-1, 1):
        for k, (dx, dz, r) in enumerate(((-0.02, 0.0, 0.15), (0.04, -0.17, 0.13), (-0.14, -0.3, 0.12))):
            sph(r, (s * (HA - 0.08 + dx), -0.1, H.c.z - 0.28 + dz), white, scale=(1, 0.8, 0.9))
    sph(0.3, (0, -0.3, 0.66), white, scale=(1.15, 0.6, 0.8))
    patch(H, 0, -0.06, 0.38, mask, sx=1.15, sz=1.0)       # 얼굴 마스크(포인트)
    patch(H, 0, -0.3, 0.2, white, t=0.034, sx=1.35, sz=0.85)   # 주둥이 흰 블레이즈
    feat(H, 0, -0.08, 0.06, white, scale=(0.7, 0.3, 1.9), lift=0.012)   # 콧등 흰 줄
    dr = DROOP.get(ex, 0.0)
    for s in (-1, 1):
        ang = math.radians(24 + 32 * dr)
        d = (s * math.sin(ang), 0.05, math.cos(ang))
        b0 = (s * (0.46 + 0.1 * dr), 0.08, 1.98 - 0.08 * dr)
        ear(d, b0, 0.62, 0.3, point, flat=0.5)
        ear(d, (b0[0], b0[1] - 0.14, b0[2] + 0.04), 0.46, 0.19, mat('rd_ear', (1.0, 0.66, 0.66), rough=0.5), flat=0.3)
    nose(H, -0.22, mat('rd_nose', (0.95, 0.48, 0.52), rough=0.25, coat=0.8), w=0.055)
    whiskers(H, 0.2, -0.27, 2, mat('whisker', (0.97, 0.95, 0.9), rough=0.4), span=0.36, t=0.008)
    F = Face(H, 0.31, -0.01, 0.195, (0.12, 0.48, 1.0), mouth=-0.32)
    F.build(ex, 'cat')


BUILD = {'fox': fox, 'otter': otter, 'panda': panda, 'cat': cat}


def render_one(sp, ex):
    sc = studio()
    BUILD[sp](ex)
    sc.render.filepath = os.path.join(OUTDIR, "%s-%s.png" % (sp, ex))
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sp, ex)


def tile():
    """홈 타일용 장난감 — 작은 윷판 위 윷가락 넷 + 여우·랫서팬더 말 (tiles_toybox 와 같은 스튜디오)."""
    sc = studio(tile=True)
    wood = mat('mat_wood', (0.72, 0.46, 0.24), rough=0.35, coat=0.6)
    paper = mat('hanji', (0.95, 0.88, 0.72), rough=0.6, coat=0.2)
    ink = mat('ink2', (0.10, 0.07, 0.06), rough=0.5, coat=0)
    red = mat('dot_red', (0.86, 0.14, 0.09), rough=0.3, coat=0.6)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.3, 0.07))
    o = bpy.context.object
    o.scale = (2.3, 2.3, 0.14)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _fin(o, wood, bevel=0.06)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.3, 0.15))
    o = bpy.context.object
    o.scale = (2.0, 2.0, 0.02)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _fin(o, paper, bevel=0.005)
    cx, cy, S = 0.0, 0.3, 0.84
    pts = []
    for k in range(5):
        t = -S + 2 * S * k / 4
        pts += [(t, cy - S), (t, cy + S), (-S, cy + t), (S, cy + t)]
    for k in (1, 2, 4, 5):
        t = -S + 2 * S * k / 6
        pts += [(t, cy + t), (t, cy - t)]
    pts.append((0, cy))

    def seg(x0, y0, x1, y1):
        L = math.hypot(x1 - x0, y1 - y0)
        bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, 0.165))
        o = bpy.context.object
        o.scale = (L, 0.03, 0.01)
        o.rotation_euler = (0, 0, math.atan2(y1 - y0, x1 - x0))
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        _fin(o, ink, smooth=False)
    for (x0, y0, x1, y1) in ((-S, cy - S, S, cy - S), (-S, cy + S, S, cy + S), (-S, cy - S, -S, cy + S), (S, cy - S, S, cy + S),
                             (-S, cy - S, S, cy + S), (-S, cy + S, S, cy - S)):
        seg(x0, y0, x1, y1)
    for (x, y) in set((round(a, 3), round(b, 3)) for a, b in pts):
        big = abs(abs(x) - S) < 1e-3 and abs(abs(y - cy) - S) < 1e-3 or (x == 0 and y == cy)
        cyl(0.11 if big else 0.07, 0.03, (x, y, 0.175), red if big else ink, bevel=0.01)
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


# ════════════ 승리 군무 자세 (2026-09-27) ════════════
# 운영자: "보이그룹 최신 타이틀곡의 시그니처 춤을 윷놀이 캐릭터들이 — 다 이겼을 때 V자 대열 군무."
# 참고 원곡(코드 주석에만 둔다 — 화면·본문에 곡명·가수명 표기 금지): ATEEZ 'BAD'(2026-06-26, GOLDEN HOUR : Part.5,
# 브라질리언 펑크). 공개 문헌에서 확인되는 핵심 = 후반부 킬링파트의 '가슴 튕기기'(비트에 맞춰 가슴을 튕기는
# 절제된 동작 + 표정), 날카로운 팔 뻗기·폭발적 점프·대형 전환, 컨셉 키워드 '끌림과 통제 · 동기화'.
# 세부 카운트는 글로 정리된 자료가 없어 **근사 재구성**이다 — 스프라이트 11컷을 게임의 박자표가 잇는다.
#
# 좌표: 손 R/L = 화면 오른쪽/왼쪽(+x/-x). feet = 발 위치(바닥 z≈0.07).
# roll = 몸 전체 좌우 기울기(+ = 화면 오른쪽으로), fwd = 앞뒤(+ = 카메라 쪽으로 숙임, - = 젖혀 가슴 내밀기),
# hroll/hfwd = 고개만. 머리가 몸보다 커서 손을 머리 옆(|x|≥0.95)에 두지 않으면 얼굴에 묻힌다(실측 규칙).
DPOSES = ['ready', 'point', 'pull', 'cross', 'wave', 'hip', 'slash', 'chest', 'chestB', 'jump', 'finale']
_F = 0.07
DPOSE = {
    # 인트로 — 고개 숙이고 주먹 쥔 채 넓게 서기
    'ready':  dict(ex='f', R=(0.5, -0.3, 0.36), L=(-0.5, -0.3, 0.36), feet=((0.34, -0.08, _F), (-0.34, -0.08, _F)),
                   roll=0.0, fwd=0.1, hroll=0.0, hfwd=0.16),
    # '나쁘다 불러도' — 오른팔 대각선 위로 쭉, 왼손 허리
    'point':  dict(ex='f', R=(1.1, -0.4, 1.22), L=(-0.5, -0.2, 0.46), feet=((0.3, -0.1, _F), (-0.32, 0.0, _F)),
                   roll=0.07, fwd=0.0, hroll=0.1, hfwd=0.0),
    # 끌림 — 두 주먹을 가슴으로 당기며 젖힘
    'pull':   dict(ex='f', R=(0.26, -0.66, 0.64), L=(-0.26, -0.66, 0.64), feet=((0.26, -0.06, _F), (-0.26, -0.06, _F)),
                   roll=0.0, fwd=-0.12, hroll=0.0, hfwd=-0.04),
    # 통제 — 가슴 앞 X 자 팔짱(턱 아래)
    'cross':  dict(ex='f', R=(-0.2, -0.66, 0.8), L=(0.2, -0.62, 0.7), feet=((0.18, -0.06, _F), (-0.18, -0.06, _F)),
                   roll=0.0, fwd=0.05, hroll=-0.06, hfwd=0.04),
    # 파도 — 두 팔 수평으로 활짝(물결 구간)
    'wave':   dict(ex='h', R=(0.98, -0.25, 0.86), L=(-0.98, -0.25, 0.86), feet=((0.3, -0.06, _F), (-0.3, -0.06, _F)),
                   roll=0.0, fwd=0.0, hroll=0.12, hfwd=0.0),
    # 골반 튕기기 — 한 손 허리, 반대 팔 위로, 한쪽 무릎 들기
    'hip':    dict(ex='h', R=(0.58, -0.26, 0.42), L=(-1.02, -0.3, 1.46), feet=((0.3, -0.24, 0.2), (-0.3, 0.0, _F)),
                   roll=-0.1, fwd=0.0, hroll=0.16, hfwd=0.0),
    # 칼각 — 오른팔 위 오른쪽, 왼팔 아래 왼쪽 대각선
    'slash':  dict(ex='f', R=(1.14, -0.34, 1.46), L=(-0.95, -0.3, 0.22), feet=((0.42, -0.06, _F), (-0.42, -0.06, _F)),
                   roll=-0.05, fwd=0.0, hroll=0.08, hfwd=0.0),
    # 시그니처 가슴 튕기기 — 튕김(젖혀 가슴 내밀기) / 거둠(움츠림) 두 컷을 박자마다 번갈아
    'chest':  dict(ex='f', R=(0.86, -0.08, 0.92), L=(-0.86, -0.08, 0.92), feet=((0.32, -0.06, _F), (-0.32, -0.06, _F)),
                   roll=0.0, fwd=-0.3, hroll=0.0, hfwd=0.12),
    'chestB': dict(ex='f', R=(0.3, -0.56, 0.34), L=(-0.3, -0.56, 0.34), feet=((0.3, -0.06, _F), (-0.3, -0.06, _F)),
                   roll=0.0, fwd=0.2, hroll=0.0, hfwd=0.1),
    # 폭발 점프 — 두 팔 V, 발 접기
    'jump':   dict(ex='x', R=(1.08, -0.3, 1.55), L=(-1.08, -0.3, 1.55), feet=((0.22, -0.22, 0.24), (-0.22, -0.22, 0.24)),
                   roll=0.0, fwd=-0.05, hroll=0.0, hfwd=-0.04),
    # 엔딩 — 오른팔 하늘 찌르기, 왼손 가슴, 넓은 자세
    'finale': dict(ex='x', R=(1.14, -0.34, 1.52), L=(0.02, -0.62, 0.66), feet=((0.42, -0.06, _F), (-0.34, -0.06, _F)),
                   roll=-0.07, fwd=0.0, hroll=0.1, hfwd=0.0),
}
HIP = (0.18, -0.02, 0.3)


def _xform(objs, pivot, rx=0.0, ry=0.0):
    """오브젝트들을 pivot 기준으로 돌린다. rx = X축(앞뒤 숙임), ry = Y축(화면 평면 좌우 기울기)."""
    if abs(rx) < 1e-6 and abs(ry) < 1e-6:
        return
    bpy.context.view_layer.update()
    p = Vector(pivot)
    M = Matrix.Translation(p) @ Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(rx, 4, 'X') @ Matrix.Translation(-p)
    for o in objs:
        if o.parent is None:
            o.matrix_world = M @ o.matrix_world
    return M


def render_dance(sp, pose):
    global _DANCE
    sc = studio()
    _DANCE = dict(DPOSE[pose])
    try:
        BUILD[sp](_DANCE['ex'])
        objs = [o for o in bpy.data.objects if o.type == 'MESH']
        head = [o for o in objs if _HEAD_MARK is not None and o not in _HEAD_MARK]
        # 고개 — 목(머리 아래) 기준
        _xform(head, (0, -0.05, 0.92), rx=_DANCE['hfwd'], ry=_DANCE['hroll'])
        # 몸 전체 — 골반 기준. 다리는 기울인 뒤에 골반 → 발로 새로 잇는다(발은 바닥에 남는다)
        M = _xform(objs, (0, -0.02, 0.3), rx=_DANCE['fwd'], ry=_DANCE['roll'])
        leg, foot = _DANCE['_leg'], _DANCE['_limb']
        for s, f in ((1, _DANCE['feet'][0]), (-1, _DANCE['feet'][1])):
            h = Vector((s * HIP[0], HIP[1], HIP[2]))
            if M is not None:
                h = M @ h
            capsule(h, Vector(f) + Vector((0, 0.02, 0.05)), 0.1, leg, rb=0.09)
            sph(0.15, f, foot, scale=(1.0, 1.35, 0.7))
    finally:
        _DANCE = None
    sc.render.filepath = os.path.join(OUTDIR, "dance", "%s-%s.png" % (sp, pose))
    bpy.ops.render.render(write_still=True)
    print("RENDERED dance", sp, pose)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if argv and argv[0] == 'dance':
        # -- dance                 → 4종 × 11자세 = 44장 (scripts/og-assets/yut/dance/<sp>-<pose>.png)
        # -- dance fox:chest,jump  → 일부만
        os.makedirs(os.path.join(OUTDIR, "dance"), exist_ok=True)
        for a in (argv[1:] or SPECIES):
            sp, _, ps = a.partition(':')
            for pose in (ps.split(',') if ps else DPOSES):
                render_dance(sp, pose)
    elif argv and argv[0] == 'tile':
        sc = tile()
        # 말 둘(사막여우 만세 · 랫서팬더 크게 보이기)을 작게 줄여 판 위에 세운다 — 새로 생긴 오브젝트만 빈 부모에 묶어 축소
        for sp, ex, loc, rz in (('fox', 'x', (-0.55, 0.05), 16), ('panda', 'w', (0.6, 0.35), -14)):
            before = set(bpy.data.objects)
            BUILD[sp](ex)
            new = [o for o in bpy.data.objects if o not in before]
            bpy.ops.object.empty_add(location=(0, 0, 0))
            root = bpy.context.object
            for o in new:
                if o.parent is None:
                    o.parent = root
            root.scale = (0.5, 0.5, 0.5)
            root.location = (loc[0], loc[1], 0.16)
            root.rotation_euler = (0, 0, math.radians(rz))
        sc.render.filepath = os.path.join(TILEDIR, "yut.png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED tile")
    else:
        jobs = []
        for a in (argv or SPECIES):
            sp, _, exs = a.partition(':')
            for ex in (exs.split(',') if exs else EXPRS):
                jobs.append((sp, ex))
        for sp, ex in jobs:
            render_one(sp, ex)
