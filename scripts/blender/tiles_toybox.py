# -*- coding: utf-8 -*-
"""메인 타일 9종 — "레트로 장난감 진열장" (2026-09-24 운영자 요청으로 신설).

운영자: "메인페이지 PC 에서 게임 상자의 아이콘·그림이 찰떡같이 맞는 느낌이 아니고 통일성이 없다.
레트로 느낌이 나면서도 고퀄리티, 게임의 성격까지 포함한 컨셉으로."

이전에는 평면 SVG(룰렛·사다리·빙고) · OS 이모지(카레이싱·주사위·풍선·아케이드) · 3D 렌더(팀·브롤)가
섞여 있었다. 지금은 **9종 모두 이 스크립트 하나**가 같은 스튜디오에서 찍는다.

## 스타일 문법 (새 타일도 이것만 쓴다)
- 소재: 70~80년대 플라스틱·틴 장난감 — 반들반들한 코팅 플라스틱(Coat), 둥근 베벨, 크롬 약간
- 팔레트: 크림·토마토·머스터드·틸·코발트 + 타일 고유 색(GAME_TINT)을 장난감 주색으로
- 잉크 외곽선(Freestyle, 실루엣·경계만) — 레트로 인쇄물 느낌이 통일감을 만든다
- 같은 카메라(3/4 위), 같은 조명(웜 키·쿨 림·프런트 필), 그림자 캐처로 접지 그림자만
- 모든 장난감은 대략 가로 2.4 × 높이 2.4 상자 안에 들어오게 만든다(크기 일관)

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P tiles_toybox.py -- [id ...]
출력: scripts/og-assets/tiles3d/<id>.png (1000x1000 투명) → scripts/build_tiles.py 가 webp 로.
"""
import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "..", "og-assets", "tiles3d")
os.makedirs(OUTDIR, exist_ok=True)

# ════════════ 스튜디오 ════════════
def studio():
    bpy.ops.wm.read_factory_settings(use_empty=True)
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
    sc.render.resolution_x = sc.render.resolution_y = 1000
    sc.render.film_transparent = True
    # AgX 는 밝은 원색을 파스텔로 눌러 장난감 원색이 죽는다 → Standard + 낮은 조명
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    sc.cycles.samples = int(os.environ.get('TB_SAMPLES', '160'))
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.20, 0.22, 0.30, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.35
    # 월드광은 반사(광택) 광선에만 — 확산까지 받으면 그림자 캐처에 월드 가림이 찍혀
    # 바닥 전체에 옅은 알파가 남고, 타일에서 네모난 얼룩으로 보인다
    nt = w.node_tree
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMixShader')
    tr = nt.nodes.new('ShaderNodeBackground')
    tr.inputs[1].default_value = 0.0
    out = nt.nodes['World Output']
    nt.links.new(lp.outputs['Is Glossy Ray'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(nt.nodes['Background'].outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    sc.world = w
    # 잉크 외곽선 — 장난감 컬렉션만, 실루엣·경계·외곽만(크리스 선은 베벨 때문에 지저분해진다)
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = 'ABSOLUTE'
    sc.render.line_thickness = 2.4
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
    ls.linestyle.color = (0.06, 0.05, 0.10)
    ls.linestyle.thickness = 2.4
    # 그림자 캐처(바닥) — 장난감 컬렉션 밖에 둬서 외곽선이 안 그려지게
    bpy.ops.mesh.primitive_plane_add(size=9, location=(0, 0, 0))
    fl = bpy.context.object
    fl.is_shadow_catcher = True
    # 조명
    def area(loc, power, size, color):
        bpy.ops.object.light_add(type='AREA', location=loc)
        L = bpy.context.object
        L.data.energy = power
        L.data.size = size
        L.data.color = color
        d = Vector((0, 0, 1.0)) - Vector(loc)
        L.rotation_mode = 'QUATERNION'
        L.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    area((-4.5, -5.0, 6.5), 700, 5, (1.0, 0.93, 0.84))
    area((4.5, 4.0, 4.5), 520, 4, (0.72, 0.82, 1.0))
    area((1.0, -7.5, 1.8), 120, 6, (1.0, 1.0, 1.0))
    area((0.0, 0.0, 9.0), 140, 6, (1.0, 1.0, 1.0))
    # 카메라 — 모든 타일 동일
    bpy.ops.object.camera_add(location=(0, -7.6, 4.0))
    cam = bpy.context.object
    cam.data.lens = 78
    d = Vector((0, 0, 1.12)) - cam.location
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    sc.camera = cam
    # 새 오브젝트는 전부 TOY 컬렉션으로
    lc = vl.layer_collection.children["TOY"]
    vl.active_layer_collection = lc
    global _MATS
    _MATS = {}
    return sc


# ════════════ 재질 ════════════
def mat(name, color, rough=0.28, metal=0.0, coat=0.5, emit=None, estr=0.0, trans=0.0):
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
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = estr
    if trans > 0:
        b.inputs["Transmission Weight"].default_value = trans
    _MATS[name] = m
    return m


PAL = {
    'cream': (0.93, 0.85, 0.70), 'tomato': (0.86, 0.14, 0.09), 'orange': (1.0, 0.40, 0.10),
    'mustard': (0.98, 0.66, 0.10), 'teal': (0.04, 0.58, 0.55), 'cobalt': (0.09, 0.26, 0.78),
    'green': (0.10, 0.70, 0.40), 'pink': (0.95, 0.30, 0.60), 'violet': (0.52, 0.32, 0.95),
    'navy': (0.05, 0.06, 0.13), 'white': (0.95, 0.95, 0.93), 'ivory': (0.96, 0.93, 0.84),
    'black': (0.035, 0.035, 0.045), 'wood': (0.70, 0.45, 0.24), 'slate': (0.30, 0.36, 0.46),
    'rose': (1.0, 0.25, 0.38),
}


def P(name, **kw):
    return mat(name, PAL[name], **kw)


CHROME = lambda: mat('chrome', (0.85, 0.86, 0.9), rough=0.12, metal=1.0, coat=0.0)
GOLD = lambda: mat('gold', (0.95, 0.70, 0.20), rough=0.22, metal=1.0, coat=0.0)
RUBBER = lambda: mat('rubber', (0.04, 0.04, 0.05), rough=0.65, coat=0.0)
DARK = lambda: mat('dark', (0.03, 0.035, 0.07), rough=0.45, coat=0.0)


# ════════════ 도형 ════════════
def _fin(o, m, bevel=0.0, seg=3, smooth=True, parent=None):
    if m:
        o.data.materials.append(m)
    if bevel > 0:
        md = o.modifiers.new("bev", 'BEVEL')
        md.width = bevel
        md.segments = seg
        md.limit_method = 'ANGLE'
    if smooth and hasattr(o.data, "polygons"):
        for p in o.data.polygons:
            p.use_smooth = True
        if bevel > 0:
            try:
                bpy.ops.object.select_all(action='DESELECT')
                o.select_set(True)
                bpy.context.view_layer.objects.active = o
                bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
            except Exception:
                pass
    if parent:
        o.parent = parent
    return o


def box(size, loc, m, rot=(0, 0, 0), bevel=0.04, seg=3, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return _fin(o, m, bevel, seg, parent=parent)


def cyl(r, depth, loc, m, rot=(0, 0, 0), bevel=0.02, verts=48, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    return _fin(bpy.context.object, m, bevel, 3, parent=parent)


def sph(r, loc, m, scale=(1, 1, 1), parent=None, seg=40):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.object
    o.scale = scale
    return _fin(o, m, parent=parent)


def cone(r1, r2, depth, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot, vertices=40)
    return _fin(bpy.context.object, m, parent=parent)


def torus(R, r, loc, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot,
                                     major_segments=64, minor_segments=16)
    return _fin(bpy.context.object, m, parent=parent)


def capsule(a, b, r, m, parent=None):
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=L, location=(a + b) / 2, vertices=32)
    o = bpy.context.object
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    _fin(o, m, parent=parent)
    sph(r, a, m, parent=parent, seg=24)
    sph(r, b, m, parent=parent, seg=24)
    return o


def text(s, size, loc, m, rot=(math.radians(90), 0, 0), extrude=0.03, parent=None):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.data.body = s
    o.data.size = size
    o.data.extrude = extrude
    o.data.bevel_depth = min(0.012, extrude * 0.4)
    o.data.align_x = 'CENTER'
    o.data.align_y = 'CENTER'
    try:
        o.data.font = bpy.data.fonts.load("C:/Windows/Fonts/ariblk.ttf")
    except Exception:
        pass
    o.data.materials.append(m)
    if parent:
        o.parent = parent
    return o


def prism(points2d, depth, loc, m, rot=(math.radians(90), 0, 0), parent=None):
    """2D 다각형(XY) 을 depth 만큼 돌출. rot 기본값은 화면(-y)을 보게 세운다."""
    me = bpy.data.meshes.new("prism")
    bm = bmesh.new()
    top = [bm.verts.new((x, y, depth / 2)) for x, y in points2d]
    bot = [bm.verts.new((x, y, -depth / 2)) for x, y in points2d]
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    n = len(points2d)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("prism", me)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    return _fin(o, m, bevel=min(0.02, depth * 0.3), seg=2, parent=parent)


def star_pts(r_out, r_in, n=5, rot=math.pi / 2):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / n
        pts.append((math.cos(a) * r, math.sin(a) * r))
    return pts


def group(name, rot_z=0.0, loc=(0, 0, 0)):
    bpy.ops.object.empty_add(location=loc)
    e = bpy.context.object
    e.name = name
    e.rotation_euler = (0, 0, rot_z)
    return e


# ════════════ 장난감 ════════════
def roulette():
    """룰렛 — 전구 테두리 카니발 휠 + 금색 핀 + 나무 받침."""
    g = group("roulette", math.radians(-22))
    box((1.7, 0.7, 0.2), (0, 0, 0.1), P('cobalt'), bevel=0.07, parent=g)
    for s in (-1, 1):
        capsule((s * 0.55, 0.0, 0.2), (s * 0.16, 0.0, 1.25), 0.07, P('cream'), parent=g)
    C = Vector((0, -0.05, 1.33))
    R = 0.95
    cols = ['orange', 'cream', 'teal', 'mustard', 'tomato', 'cream', 'cobalt', 'mustard']
    for i, cn in enumerate(cols):
        me = bpy.data.meshes.new("wedge")
        bm = bmesh.new()
        a0, a1 = i * 2 * math.pi / 8, (i + 1) * 2 * math.pi / 8
        th = 0.07
        cf, cb = bm.verts.new((0, -th, 0)), bm.verts.new((0, th, 0))
        arcf, arcb = [], []
        for k in range(9):
            a = a0 + (a1 - a0) * k / 8
            arcf.append(bm.verts.new((math.cos(a) * R, -th, math.sin(a) * R)))
            arcb.append(bm.verts.new((math.cos(a) * R, th, math.sin(a) * R)))
        bm.faces.new([cf] + arcf)
        bm.faces.new([cb] + list(reversed(arcb)))
        for k in range(8):
            bm.faces.new((arcf[k], arcb[k], arcb[k + 1], arcf[k + 1]))
        bm.faces.new((cf, cb, arcb[0], arcf[0]))
        bm.faces.new((cf, arcf[-1], arcb[-1], cb))
        bm.normal_update()
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("wedge", me)
        bpy.context.collection.objects.link(o)
        o.location = C
        _fin(o, P(cn), parent=g)
    torus(R + 0.04, 0.075, C, GOLD(), rot=(math.radians(90), 0, 0), parent=g)
    bulb = mat('bulb', (1, 0.9, 0.6), emit=(1.0, 0.82, 0.45), estr=8, coat=0)
    for k in range(16):
        a = k * 2 * math.pi / 16
        sph(0.045, (C.x + math.cos(a) * (R + 0.04), C.y - 0.07, C.z + math.sin(a) * (R + 0.04)), bulb, parent=g, seg=16)
    cyl(0.16, 0.22, (C.x, C.y - 0.05, C.z), GOLD(), rot=(math.radians(90), 0, 0), parent=g)
    sph(0.09, (C.x, C.y - 0.17, C.z), P('tomato'), parent=g, seg=24)
    cone(0.16, 0.0, 0.34, (C.x, C.y - 0.12, C.z + R + 0.22), P('tomato'), rot=(math.pi, 0, 0), parent=g)
    return g


def car():
    """카레이싱 — 초록 틴토이 경주차 + 번호 7 + 헬멧 드라이버."""
    g = group("car", math.radians(-28), loc=(0, 0, 0))
    GR = P('green')
    cyl(0.36, 1.55, (0, 0, 0.62), GR, rot=(0, math.radians(90), 0), bevel=0.0, parent=g)
    sph(0.36, (0.78, 0, 0.62), GR, scale=(1.55, 1, 1), parent=g)
    sph(0.36, (-0.78, 0, 0.62), GR, scale=(0.7, 1, 1), parent=g)
    cyl(0.372, 0.16, (0.25, 0, 0.62), P('cream'), rot=(0, math.radians(90), 0), bevel=0.0, parent=g)
    cyl(0.372, 0.06, (0.42, 0, 0.62), P('tomato'), rot=(0, math.radians(90), 0), bevel=0.0, parent=g)
    # 번호 원판
    cyl(0.19, 0.03, (-0.2, -0.36, 0.64), P('white'), rot=(math.radians(90), 0, 0), bevel=0.005, parent=g)
    text("7", 0.26, (-0.2, -0.385, 0.62), DARK(), extrude=0.012, parent=g)
    # 조종석·드라이버
    sph(0.25, (-0.28, 0, 0.9), DARK(), scale=(1.2, 1, 0.45), parent=g)
    sph(0.17, (-0.3, 0, 1.08), P('mustard'), parent=g)
    box((0.07, 0.26, 0.07), (-0.16, 0, 1.1), DARK(), bevel=0.02, parent=g)
    glass = mat('glass', (0.7, 0.85, 1.0), rough=0.05, coat=0, trans=0.9)
    box((0.03, 0.34, 0.16), (-0.02, 0, 0.98), glass, rot=(0, math.radians(-28), 0), bevel=0.01, parent=g)
    box((0.14, 0.05, 0.36), (-0.95, 0, 0.95), GR, bevel=0.03, parent=g)
    # 바퀴
    for x, r in ((0.62, 0.26), (-0.55, 0.30)):
        for s in (-1, 1):
            cyl(r, 0.2, (x, s * 0.44, r), RUBBER(), rot=(math.radians(90), 0, 0), bevel=0.05, parent=g)
            cyl(r * 0.52, 0.215, (x, s * 0.44, r), CHROME(), rot=(math.radians(90), 0, 0), bevel=0.02, parent=g)
            sph(0.05, (x, s * 0.56, r), P('tomato'), parent=g, seg=16)
    for s in (-1, 1):
        cyl(0.05, 0.3, (-1.02, s * 0.16, 0.5), CHROME(), rot=(0, math.radians(90), 0), parent=g)
    g.scale = (1.15, 1.15, 1.15)
    return g


def dice():
    """주사위 — 상아색 주사위 두 개, 하나는 굴러가는 중(공중)."""
    g = group("dice", 0)
    IV = P('ivory', rough=0.2, coat=0.8)
    PIP = DARK()
    RED = mat('pipred', (0.75, 0.05, 0.05), rough=0.35)

    def die(loc, size, rot, faces):
        e = group("die", 0, loc=loc)
        e.rotation_euler = rot
        box((size, size, size), (0, 0, 0), IV, bevel=size * 0.16, seg=5, parent=e)
        h = size / 2
        L = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)],
             4: [(-1, -1), (-1, 1), (1, -1), (1, 1)], 5: [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)],
             6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)]}
        off = size * 0.26
        for axis, sign, n in faces:
            for u, v in L[n]:
                p = [0, 0, 0]
                p[axis] = sign * (h - 0.012)
                o1, o2 = [a for a in (0, 1, 2) if a != axis]
                p[o1] = u * off
                p[o2] = v * off
                sc = [1.0, 1.0, 1.0]
                sc[axis] = 0.32
                sph(size * 0.095, tuple(p), RED if n == 1 else PIP, scale=tuple(sc), parent=e, seg=20)
        return e
    die((-0.45, 0.2, 0.46), 0.92, (0, 0, math.radians(28)), [(2, 1, 5), (1, -1, 3), (0, 1, 2)])
    die((0.62, -0.35, 1.05), 0.8, (math.radians(32), math.radians(22), math.radians(-18)), [(2, 1, 1), (1, -1, 4), (0, 1, 6), (0, -1, 3)])
    return g


def ladder():
    """사다리 — 세워 둔 사다리타기 판. 분홍 당첨 경로가 빛나고 끝에 금별."""
    g = group("ladder", math.radians(-18))
    board = group("board", 0, loc=(0, 0.1, 0))
    board.parent = g
    board.rotation_euler = (math.radians(-8), 0, 0)
    box((2.0, 0.16, 2.25), (0, 0, 1.2), P('wood', rough=0.5, coat=0.3), bevel=0.08, parent=board)
    box((1.2, 0.5, 0.12), (0, 0.05, 0.06), P('cobalt'), bevel=0.04, parent=g)
    xs = [-0.66, -0.22, 0.22, 0.66]
    z0, z1 = 0.4, 1.95
    for x in xs:
        cyl(0.04, z1 - z0, (x, -0.1, (z0 + z1) / 2), P('cream'), parent=board)
    rungs = [(0, 0.62), (2, 0.78), (1, 1.0), (0, 1.22), (2, 1.42), (1, 1.66)]
    for i, z in rungs:
        cyl(0.035, xs[i + 1] - xs[i], ((xs[i] + xs[i + 1]) / 2, -0.1, z), P('cream'), rot=(0, math.radians(90), 0), parent=board)
    # 당첨 경로: 1번 기둥 위에서 출발, 가로선을 만나면 건넌다
    col = 1
    pts = [(xs[col], z1)]
    for i, z in sorted(rungs, key=lambda t: -t[1]):
        if i == col:
            pts += [(xs[col], z), (xs[col + 1], z)]
            col += 1
        elif i + 1 == col:
            pts += [(xs[col], z), (xs[col - 1], z)]
            col -= 1
    pts.append((xs[col], z0))
    hot = mat('hot', PAL['pink'], emit=(1.0, 0.2, 0.55), estr=0.35, coat=0.6)
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        capsule((ax, -0.14, az), (bx, -0.14, bz), 0.055, hot, parent=board)
    cols = ['tomato', 'pink', 'teal', 'mustard']
    for x, cn in zip(xs, cols):
        cone(0.1, 0.04, 0.2, (x, -0.13, z1 + 0.13), P(cn), parent=board)
        sph(0.08, (x, -0.13, z1 + 0.28), P(cn), parent=board, seg=24)
    prism(star_pts(0.2, 0.09), 0.08, (xs[col], -0.16, z0 - 0.13), GOLD(), parent=board)
    return g


def bingo():
    """빙고 — 보라 받침의 금색 추첨 케이지 + 손잡이 + 번호공."""
    g = group("bingo", math.radians(-20))
    VI = P('violet')
    cyl(0.75, 0.18, (0, 0, 0.09), VI, bevel=0.05, parent=g)
    for s in (-1, 1):
        box((0.1, 0.16, 1.1), (s * 0.92, 0, 0.7), VI, bevel=0.03, parent=g)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.72, location=(0, 0, 1.28), segments=12, ring_count=8)
    cage = bpy.context.object
    wf = cage.modifiers.new("wf", 'WIREFRAME')
    wf.thickness = 0.035
    _fin(cage, GOLD(), parent=g)
    cyl(0.05, 2.0, (0, 0, 1.28), CHROME(), rot=(0, math.radians(90), 0), parent=g)
    capsule((1.02, 0, 1.28), (1.02, 0, 0.92), 0.04, CHROME(), parent=g)
    sph(0.09, (1.12, 0, 0.92), P('tomato'), parent=g, seg=24)
    for i, cn in enumerate(['tomato', 'teal', 'mustard', 'cream', 'pink', 'cobalt']):
        a = i * 1.05
        sph(0.15, (math.cos(a) * 0.3, math.sin(a) * 0.25, 0.8 + (i % 2) * 0.12), P(cn), parent=g, seg=24)
    for (x, y, num, cn) in ((0.5, -0.85, "7", 'tomato'), (-0.42, -0.8, "42", 'teal')):
        sph(0.25, (x, y, 0.25), P('white', coat=0.8), parent=g, seg=32)
        cyl(0.15, 0.03, (x, y - 0.235, 0.25), P(cn), rot=(math.radians(90), 0, 0), bevel=0.01, parent=g)
        text(num, 0.15 if len(num) > 1 else 0.19, (x, y - 0.262, 0.245), P('white', coat=0.8), extrude=0.008, parent=g)
    return g


def figure(col, loc, yaw, pose='cross', mood='angry', parent=None):
    """캡슐 피규어 — 팀·브롤 공용. 머리가 큰 2등신이어야 타일 크기에서 표정이 읽힌다.
    yaw θ 일 때 정면 = (sinθ, -cosθ). 0 = 카메라(-y) 쪽."""
    e = group("fig", yaw, loc=(loc[0], loc[1], 0))
    if parent:
        e.parent = parent
    C = P(col)
    capsule((0, 0, 0.55), (0, 0, 0.8), 0.28, C, parent=e)
    for s in (-1, 1):
        capsule((s * 0.12, 0, 0.36), (s * 0.14, -0.02, 0.1), 0.1, P('navy'), parent=e)
        sph(0.12, (s * 0.14, -0.08, 0.07), DARK(), scale=(1, 1.4, 0.7), parent=e)
    H = Vector((0, 0, 1.38))
    HR = 0.42
    sph(HR, H, P('cream'), parent=e)
    D = DARK()
    W = P('white', coat=0.6)
    fy = H.y - HR * 0.93
    if mood == 'angry':
        # 부릅뜬 눈 + 팔자 눈썹 + 악문 이빨 — B급 성난 얼굴
        for s in (-1, 1):
            sph(0.1, (s * 0.15, fy + 0.03, H.z + 0.04), W, scale=(1, 0.5, 0.85), parent=e, seg=24)
            sph(0.05, (s * 0.13, fy - 0.02, H.z + 0.03), D, scale=(1, 0.5, 1), parent=e, seg=16)
            box((0.2, 0.05, 0.06), (s * 0.15, fy + 0.0, H.z + 0.17), D, rot=(0, math.radians(-26 * s), 0), bevel=0.02, parent=e)
        box((0.26, 0.06, 0.1), (0, fy + 0.04, H.z - 0.17), W, bevel=0.025, parent=e)
        box((0.005, 0.07, 0.1), (0, fy + 0.02, H.z - 0.17), D, bevel=0.0, parent=e)
        box((0.26, 0.07, 0.006), (0, fy + 0.02, H.z - 0.17), D, bevel=0.0, parent=e)
    else:
        # 동그랗게 뜬 눈 + 벌린 입 + 땀방울 — 당황한 얼굴
        for s in (-1, 1):
            sph(0.12, (s * 0.15, fy + 0.04, H.z + 0.06), W, scale=(1, 0.5, 1.1), parent=e, seg=24)
            sph(0.045, (s * 0.15, fy - 0.02, H.z + 0.06), D, scale=(1, 0.5, 1), parent=e, seg=16)
            box((0.14, 0.05, 0.05), (s * 0.16, fy + 0.02, H.z + 0.25), D, rot=(0, math.radians(20 * s), 0), bevel=0.02, parent=e)
        sph(0.09, (0, fy + 0.03, H.z - 0.17), D, scale=(1, 0.5, 1.3), parent=e, seg=24)
        sweat = mat('sweat', (0.45, 0.8, 1.0), rough=0.05, coat=1.0)
        sph(0.07, (0.36, fy + 0.2, H.z + 0.2), sweat, scale=(0.8, 0.8, 1.3), parent=e, seg=20)
    if pose == 'cross':
        capsule((-0.26, -0.12, 0.8), (0.18, -0.28, 0.72), 0.09, C, parent=e)
        capsule((0.26, -0.12, 0.8), (-0.18, -0.28, 0.68), 0.09, C, parent=e)
    elif pose == 'shove':
        for s in (-1, 1):
            capsule((s * 0.26, 0, 0.82), (s * 0.2, -0.62, 0.9), 0.09, C, parent=e)
            sph(0.11, (s * 0.2, -0.66, 0.9), P('cream'), parent=e, seg=20)
    else:  # flail
        capsule((-0.28, 0, 0.82), (-0.58, 0.1, 1.2), 0.09, C, parent=e)
        capsule((0.28, 0, 0.82), (0.6, 0.05, 1.15), 0.09, C, parent=e)
    return e


def team():
    """팀뽑기 — 빨강 둘 vs 파랑 둘 팔짱 대치 + 금색 VS."""
    g = group("team", 0)
    sc = 0.78
    for (x, y, col, yaw) in ((-0.6, 0.0, 'tomato', 40), (-1.12, 0.5, 'tomato', 35),
                             (0.6, 0.0, 'cobalt', -40), (1.12, 0.5, 'cobalt', -35)):
        f = figure(col, (x, y), math.radians(yaw), 'cross', 'angry', parent=g)
        f.scale = (sc, sc, sc)
    text("VS", 0.5, (0, -0.5, 0.75), mat('vs', PAL['mustard'], emit=(1.0, 0.6, 0.1), estr=0.3, coat=0.8), extrude=0.09, parent=g)
    return g


def brawl():
    """브롤런 — 빨강이 앞선 파랑을 두 손으로 밀친다 + 충돌 별 + 흙먼지."""
    g = group("brawl", 0)
    a = figure('tomato', (-0.78, 0.2), 0, 'shove', 'angry', parent=g)
    a.rotation_euler = (0, math.radians(10), math.radians(38))
    b = figure('cobalt', (0.72, -0.2), 0, 'flail', 'panic', parent=g)
    b.rotation_euler = (0, math.radians(-24), math.radians(12))
    for f in (a, b):
        f.scale = (0.9, 0.9, 0.9)
    hot = mat('impact', (1.0, 0.82, 0.15), emit=(1.0, 0.7, 0.1), estr=0.4, coat=0)
    prism(star_pts(0.3, 0.13, 8), 0.07, (0.02, -0.5, 1.02), hot, parent=g)
    dust = mat('dust', (0.72, 0.58, 0.42), rough=0.95, coat=0)
    for (x, y, z, r) in ((-1.2, 0.35, 0.16, 0.2), (-1.42, 0.45, 0.24, 0.15), (-1.0, 0.5, 0.12, 0.14)):
        sph(r, (x, y, z), dust, parent=g, seg=20)
    return g


def arcade():
    """레트로 아케이드 — 오락기 캐비닛 + 픽셀 외계인 화면 + 조이스틱."""
    g = group("arcade", math.radians(-28))
    CO = P('slate')
    box((1.15, 0.9, 2.25), (0, 0.1, 1.125), CO, bevel=0.05, parent=g)
    for s in (-1, 1):
        box((0.04, 0.95, 0.12), (s * 0.59, 0.1, 1.55), P('tomato'), bevel=0.01, parent=g)
        box((0.04, 0.95, 0.08), (s * 0.59, 0.1, 1.4), P('mustard'), bevel=0.01, parent=g)
    box((1.0, 0.1, 0.72), (0, -0.36, 1.62), DARK(), rot=(math.radians(-10), 0, 0), bevel=0.03, parent=g)
    scr = mat('screen', (0.02, 0.06, 0.06), emit=(0.02, 0.12, 0.10), estr=1.0, coat=0.2)
    box((0.84, 0.04, 0.58), (0, -0.41, 1.63), scr, rot=(math.radians(-10), 0, 0), bevel=0.01, parent=g)
    pix = mat('pix', (0.3, 1.0, 0.4), emit=(0.25, 1.0, 0.35), estr=4, coat=0)
    inv = ["00100100", "00011000", "00111100", "01011010", "11111111", "10111101", "10100101", "00011000"]
    ps = 0.05
    for r, row in enumerate(inv):
        for c, ch in enumerate(row):
            if ch == '1':
                x = (c - 3.5) * ps
                z = 1.63 + (3.5 - r) * ps * math.cos(math.radians(10))
                y = -0.44 - (3.5 - r) * ps * math.sin(math.radians(10))
                box((ps * 0.9, 0.02, ps * 0.9), (x, y, z), pix, rot=(math.radians(-10), 0, 0), bevel=0.0, parent=g)
    mq = mat('marquee', (1.0, 0.85, 0.5), emit=(1.0, 0.62, 0.25), estr=3, coat=0)
    box((1.15, 0.3, 0.28), (0, -0.2, 2.16), mq, bevel=0.03, parent=g)
    text("PLAY", 0.2, (0, -0.36, 2.15), DARK(), extrude=0.015, parent=g)
    box((1.15, 0.55, 0.14), (0, -0.46, 1.08), P('mustard'), rot=(math.radians(18), 0, 0), bevel=0.04, parent=g)
    capsule((-0.25, -0.55, 1.14), (-0.25, -0.58, 1.33), 0.025, CHROME(), parent=g)
    sph(0.075, (-0.25, -0.58, 1.36), P('tomato'), parent=g, seg=24)
    for i, cn in enumerate(['tomato', 'teal', 'cobalt']):
        cyl(0.05, 0.06, (0.08 + i * 0.16, -0.6, 1.16), P(cn), rot=(math.radians(18), 0, 0), bevel=0.01, parent=g)
    box((0.3, 0.04, 0.34), (0, -0.37, 0.45), DARK(), bevel=0.02, parent=g)
    slot = mat('slot', (1, 0.5, 0.1), emit=(1.0, 0.45, 0.1), estr=4, coat=0)
    box((0.04, 0.02, 0.1), (0, -0.4, 0.5), slot, bevel=0.0, parent=g)
    return g


def balloon():
    """풍선 룰렛 — 레트로 펌프에 연결된 빨간 풍선 + 위험 게이지."""
    g = group("balloon", math.radians(-18))
    MU = P('mustard')
    box((0.8, 0.6, 0.12), (-0.6, 0, 0.06), P('cobalt'), bevel=0.04, parent=g)
    cyl(0.25, 0.95, (-0.6, 0, 0.6), MU, bevel=0.03, parent=g)
    cyl(0.27, 0.06, (-0.6, 0, 1.08), CHROME(), bevel=0.01, parent=g)
    cyl(0.04, 0.45, (-0.6, 0, 1.3), CHROME(), parent=g)
    capsule((-0.9, 0, 1.52), (-0.3, 0, 1.52), 0.07, P('tomato'), parent=g)
    cyl(0.14, 0.04, (-0.6, -0.26, 0.72), P('white'), rot=(math.radians(90), 0, 0), bevel=0.01, parent=g)
    box((0.02, 0.01, 0.1), (-0.57, -0.285, 0.75), P('tomato'), rot=(0, math.radians(-40), 0), bevel=0.0, parent=g)
    hose_pts = [(-0.35, 0, 0.3), (0.0, -0.1, 0.2), (0.35, -0.05, 0.45), (0.45, 0, 0.72)]
    cu = bpy.data.curves.new("hose", 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 0.045
    cu.bevel_resolution = 6
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(hose_pts) - 1)
    for i, p in enumerate(hose_pts):
        bp = sp.bezier_points[i]
        bp.co = Vector(p)
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    ho = bpy.data.objects.new("hose", cu)
    bpy.context.collection.objects.link(ho)
    ho.data.materials.append(RUBBER())
    ho.parent = g
    RB = mat('balloonred', (0.92, 0.08, 0.2), rough=0.12, coat=1.0)
    sph(0.66, (0.45, 0, 1.5), RB, scale=(1, 1, 1.12), parent=g)
    cone(0.07, 0.02, 0.14, (0.45, 0, 0.78), RB, parent=g)
    return g


# ════════════ 아케이드 11종 (2026-09-24) ════════════
# 운영자: "아케이드 들어간 화면도 메인 UI 와 결이 같게". 이모지 11개를 같은 진열장 장난감으로.
GLASS = lambda: mat('glass', (0.7, 0.85, 1.0), rough=0.05, coat=0, trans=0.9)


def lotto():
    """로또 — 유리 추첨기 안에 색색 공, 앞에 뽑혀 나온 공 하나."""
    g = group("lotto", math.radians(-20))
    cyl(0.62, 0.34, (0, 0, 0.17), P('mustard'), bevel=0.06, parent=g)
    cyl(0.66, 0.06, (0, 0, 0.36), CHROME(), bevel=0.01, parent=g)
    cyl(0.36, 0.14, (0, 0, 0.45), P('tomato'), bevel=0.03, parent=g)
    C = Vector((0, 0, 1.2))
    sph(0.76, C, GLASS(), parent=g, seg=48)
    torus(0.3, 0.04, (0, 0, 0.5), GOLD(), parent=g)
    cols = ['tomato', 'teal', 'mustard', 'cobalt', 'pink', 'green', 'orange', 'cream', 'violet']
    spots = [(-0.32, 0.1, -0.38), (0.05, 0.2, -0.46), (0.36, 0.0, -0.36), (-0.12, -0.2, -0.3), (0.2, -0.22, -0.12),
             (-0.35, 0.05, 0.02), (0.05, 0.1, 0.18), (0.38, 0.12, 0.25), (-0.18, -0.1, 0.36)]
    for (x, y, z), cn in zip(spots, cols):
        sph(0.15, (C.x + x, C.y + y, C.z + z), P(cn, coat=0.9), parent=g, seg=24)
    cyl(0.12, 0.42, (0, 0, 2.1), GLASS(), bevel=0.0, parent=g)
    sph(0.16, (0, 0, 2.33), CHROME(), scale=(1, 1, 0.6), parent=g, seg=24)
    # 뽑혀 나온 공 — 흰 원판 + 번호
    B = (0.78, -0.5, 0.26)
    sph(0.26, B, P('tomato', coat=0.9), parent=g, seg=32)
    cyl(0.15, 0.03, (B[0], B[1] - 0.245, B[2]), P('white'), rot=(math.radians(90), 0, 0), bevel=0.01, parent=g)
    text("7", 0.2, (B[0], B[1] - 0.27, B[2] - 0.005), DARK(), extrude=0.008, parent=g)
    return g


def planet():
    """행성 키우기 — 띠무늬 행성 + 기운 고리 + 달 + 꼬리 달린 운석."""
    g = group("planet", math.radians(-15))
    cyl(0.42, 0.12, (0, 0, 0.06), P('navy'), bevel=0.04, parent=g)
    capsule((0, 0, 0.1), (0, 0, 0.55), 0.06, CHROME(), parent=g)
    C = (0, 0, 1.25)
    R = 0.68
    sph(R, C, P('violet'), parent=g, seg=48)
    for dz, cn in ((-0.34, 'pink'), (0.02, 'mustard'), (0.34, 'pink')):
        torus(math.sqrt(R * R - dz * dz) - 0.01, 0.055, (C[0], C[1], C[2] + dz), P(cn), parent=g)
    ring = torus(1.08, 0.07, C, P('cream'), rot=(math.radians(-16), math.radians(14), 0), parent=g)
    ring.scale = (1, 1, 0.5)
    sph(0.16, (0.92, -0.35, 2.02), P('cream', rough=0.6), parent=g, seg=24)
    sph(0.13, (-0.98, -0.25, 2.0), P('orange'), parent=g, seg=24)
    tail = mat('tail', (1.0, 0.6, 0.2), emit=(1.0, 0.55, 0.15), estr=1.2, coat=0)
    cone(0.11, 0.0, 0.5, (-1.16, -0.25, 2.18), tail, rot=(0, math.radians(-45), 0), parent=g)
    return g


def engine():
    """델타-브이 — 시험대에 매달린 로켓 엔진(구리 노즐 + 불꽃) + 스패너."""
    g = group("orbit", math.radians(-24))
    box((1.9, 1.0, 0.16), (0, 0, 0.08), P('slate'), bevel=0.05, parent=g)
    for s in (-1, 1):
        box((0.12, 0.12, 2.0), (s * 0.72, 0.1, 1.1), P('teal'), bevel=0.03, parent=g)
    box((1.56, 0.14, 0.14), (0, 0.1, 2.08), P('teal'), bevel=0.03, parent=g)
    cyl(0.26, 0.42, (0, 0, 1.78), P('cream'), bevel=0.04, parent=g)
    sph(0.26, (0, 0, 1.99), P('cream'), scale=(1, 1, 0.5), parent=g)
    for s in (-1, 1):
        capsule((s * 0.2, 0, 1.8), (s * 0.66, 0.1, 1.8), 0.05, CHROME(), parent=g)
        capsule((s * 0.14, -0.1, 1.62), (s * 0.3, -0.12, 1.35), 0.045, P('tomato'), parent=g)
    copper = mat('copper', (0.85, 0.45, 0.25), rough=0.25, metal=1.0, coat=0)
    cone(0.42, 0.17, 0.72, (0, 0, 1.2), copper, parent=g)
    flame = mat('flame', (1.0, 0.7, 0.25), emit=(1.0, 0.55, 0.15), estr=2.2, coat=0)
    cone(0.32, 0.03, 0.6, (0, 0, 0.55), flame, parent=g)
    core = mat('flamecore', (1.0, 0.95, 0.7), emit=(1.0, 0.9, 0.6), estr=3.0, coat=0)
    cone(0.16, 0.02, 0.4, (0, -0.02, 0.66), core, parent=g)
    w = group("wrench", 0, loc=(0.98, -0.42, 0.18))
    w.parent = g
    w.rotation_euler = (math.radians(-10), math.radians(28), 0)
    box((0.1, 0.05, 0.9), (0, 0, 0.45), CHROME(), bevel=0.02, parent=w)
    torus(0.12, 0.05, (0, 0, 0.98), CHROME(), rot=(math.radians(90), 0, 0), parent=w)
    return g


def rocket():
    """스페이스-Z — 빨강·흰 틴 로켓이 소행성 사이를 비스듬히 뚫고 오른다."""
    g = group("dodge", math.radians(-12))
    r = group("rkt", 0, loc=(0.05, 0, 1.2))
    r.parent = g
    r.rotation_euler = (0, math.radians(32), 0)
    W = P('white', coat=0.8)
    cyl(0.3, 1.0, (0, 0, 0), W, bevel=0.02, parent=r)
    cone(0.3, 0.0, 0.62, (0, 0, 0.81), P('tomato'), parent=r)
    cyl(0.305, 0.08, (0, 0, 0.36), P('tomato'), bevel=0.0, parent=r)
    cyl(0.13, 0.04, (0, -0.29, 0.12), GLASS(), rot=(math.radians(90), 0, 0), bevel=0.01, parent=r)
    torus(0.13, 0.03, (0, -0.3, 0.12), CHROME(), rot=(math.radians(90), 0, 0), parent=r)
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 2
        fin = prism([(0, 0), (0.34, -0.1), (0.34, -0.42), (0, -0.22)], 0.06, (0, 0, -0.26), P('tomato'),
                    rot=(math.radians(90), 0, a), parent=r)
        fin.location = (math.cos(a) * 0.28, math.sin(a) * 0.28, -0.26)
        fin.rotation_euler = (math.radians(90), 0, a)
    cyl(0.18, 0.14, (0, 0, -0.56), CHROME(), bevel=0.02, parent=r)
    flame = mat('flame', (1.0, 0.7, 0.25), emit=(1.0, 0.55, 0.15), estr=2.2, coat=0)
    cone(0.2, 0.0, 0.55, (0, 0, -0.9), flame, rot=(math.pi, 0, 0), parent=r)
    rock = P('slate', rough=0.7, coat=0.1)
    for (x, y, z, s, sc) in ((-0.9, -0.1, 1.85, 0.26, (1.2, 1, 0.8)), (0.95, 0.1, 0.55, 0.2, (1, 0.9, 1.2)),
                              (-0.75, -0.3, 0.45, 0.15, (1, 1, 0.8)), (1.0, -0.2, 1.95, 0.12, (1.1, 1, 1))):
        sph(s, (x, y, z), rock, scale=sc, parent=g, seg=14)
    return g


def blocks():
    """블록 스택 — 쌓인 테트로미노 + 위에서 떨어지는 T 블록."""
    g = group("blocks", math.radians(-22))
    s = 0.36
    cells = {
        'cobalt': [(0, 0), (1, 0), (2, 0), (0, 1)],
        'mustard': [(3, 0), (4, 0), (3, 1), (4, 1)],
        'green': [(1, 1), (2, 1), (2, 2), (3, 2)],
        'teal': [(0, 2), (0, 3), (1, 2), (0, 4)],
    }
    for cn, cs in cells.items():
        for (cx, cz) in cs:
            box((s * 0.95, s * 0.95, s * 0.95), ((cx - 2) * s, 0, cz * s + s / 2), P(cn), bevel=0.05, parent=g)
    t = group("T", 0, loc=(0.45, -0.05, 2.1))
    t.parent = g
    t.rotation_euler = (0, math.radians(-12), 0)
    for (cx, cz) in ((-1, 0), (0, 0), (1, 0), (0, -1)):
        box((s * 0.95, s * 0.95, s * 0.95), (cx * s, 0, cz * s), P('tomato'), bevel=0.05, parent=t)
    for k in range(3):
        box((0.03, 0.03, 0.22), (0.45 + (k - 1) * 0.3, -0.05, 1.55 - k * 0.05), mat('spd', (1, 1, 1), coat=0, emit=(1, 1, 1), estr=0.5), bevel=0.0, parent=g)
    return g


def lander():
    """스타십 착륙 — 다리 셋 달린 착륙선이 H 패드 위로 불꽃을 뿜으며 내려온다."""
    g = group("lander", math.radians(-20))
    cyl(1.0, 0.12, (0, 0, 0.06), P('slate'), bevel=0.04, parent=g)
    torus(0.86, 0.03, (0, 0, 0.13), mat('padlight', (1, 0.8, 0.3), emit=(1, 0.75, 0.2), estr=1.5, coat=0), parent=g)
    text("H", 0.7, (0, 0, 0.14), P('mustard'), rot=(0, 0, 0), extrude=0.02, parent=g)
    Z = 1.5
    cyl(0.5, 0.3, (0, 0, Z - 0.25), P('cream'), bevel=0.05, parent=g)
    sph(0.5, (0, 0, Z), P('violet'), scale=(1, 1, 0.78), parent=g)
    sph(0.17, (0, -0.4, Z + 0.1), GLASS(), scale=(1, 0.5, 1), parent=g, seg=24)
    torus(0.17, 0.03, (0, -0.43, Z + 0.1), CHROME(), rot=(math.radians(90), 0, 0), parent=g)
    capsule((0, 0, Z + 0.35), (0.12, 0, Z + 0.72), 0.025, CHROME(), parent=g)
    sph(0.06, (0.12, 0, Z + 0.74), P('tomato'), parent=g, seg=16)
    for k in range(3):
        a = k * 2 * math.pi / 3 - math.pi / 2
        c, s = math.cos(a), math.sin(a)
        capsule((c * 0.4, s * 0.4, Z - 0.3), (c * 0.85, s * 0.85, 0.55), 0.05, CHROME(), parent=g)
        cyl(0.13, 0.05, (c * 0.86, s * 0.86, 0.52), CHROME(), bevel=0.01, parent=g)
    cone(0.22, 0.14, 0.2, (0, 0, Z - 0.5), CHROME(), parent=g)
    flame = mat('flame', (1.0, 0.7, 0.25), emit=(1.0, 0.55, 0.15), estr=2.2, coat=0)
    cone(0.2, 0.0, 0.62, (0, 0, Z - 0.9), flame, rot=(math.pi, 0, 0), parent=g)
    return g


def bricks():
    """벽돌깨기 — 세운 판에 색 벽돌 줄(몇 개 빠짐) + 튀는 공 + 패들."""
    g = group("bricks", math.radians(-18))
    box((2.2, 0.16, 2.2), (0, 0.12, 1.12), P('navy'), bevel=0.07, parent=g)
    box((1.3, 0.55, 0.12), (0, 0.1, 0.06), P('slate'), bevel=0.04, parent=g)
    rows = ['tomato', 'orange', 'mustard', 'green']
    missing = {(1, 1), (2, 3), (3, 2), (3, 3)}
    for ri, cn in enumerate(rows):
        for ci in range(4):
            if (ri, ci) in missing:
                continue
            box((0.42, 0.14, 0.2), (-0.72 + ci * 0.48, -0.02, 1.95 - ri * 0.25), P(cn), bevel=0.035, parent=g)
    box((0.62, 0.16, 0.14), (0.15, -0.05, 0.4), P('cobalt'), bevel=0.06, parent=g)
    ball = mat('ballglow', (1, 1, 1), emit=(1.0, 0.95, 0.8), estr=0.4, coat=0.8)
    sph(0.1, (0.42, -0.1, 1.02), ball, parent=g, seg=24)
    trail = mat('trail', (1, 1, 1), emit=(1, 0.9, 0.7), estr=0.3, coat=0)
    for k, (x, z, r) in enumerate(((0.3, 0.84, 0.06), (0.2, 0.68, 0.045), (0.12, 0.55, 0.03))):
        sph(r, (x, -0.1, z), trail, parent=g, seg=16)
    return g


def snake():
    """스네이크 — 줄무늬 구슬 뱀이 S 자로 기어 와서 고개를 들고 사과를 노린다."""
    g = group("snake", math.radians(-10))
    pts = []
    n = 16
    for i in range(n):
        u = i / (n - 1)
        x = -1.05 + u * 1.55
        y = 0.4 * math.sin(u * 2.4 * math.pi) + 0.1
        r = 0.12 + 0.08 * u
        pts.append((x, y, r))
    for i, (x, y, r) in enumerate(pts):
        sph(r, (x, y, r), P('green' if i % 3 else 'mustard', coat=0.8), parent=g, seg=24)
    neck = [(0.58, -0.08, 0.32, 0.2), (0.62, -0.16, 0.52, 0.2)]
    for (x, y, z, r) in neck:
        sph(r, (x, y, z), P('green', coat=0.8), parent=g, seg=24)
    H = Vector((0.66, -0.26, 0.78))
    sph(0.3, H, P('green', coat=0.8), scale=(1.15, 1.05, 0.85), parent=g, seg=32)
    W = P('white', coat=0.6)
    for s in (-1, 1):
        sph(0.1, (H.x + s * 0.13, H.y - 0.2, H.z + 0.12), W, scale=(1, 0.6, 1), parent=g, seg=20)
        sph(0.05, (H.x + s * 0.13 + 0.02, H.y - 0.26, H.z + 0.11), DARK(), scale=(1, 0.5, 1), parent=g, seg=16)
    for s in (-1, 1):
        capsule((H.x + 0.25, H.y - 0.22, H.z - 0.1), (H.x + 0.44, H.y - 0.3 + s * 0.05, H.z - 0.12), 0.018, P('tomato'), parent=g)
    A = (1.05, -0.5, 0.24)
    sph(0.24, A, P('tomato', coat=0.9), scale=(1, 1, 0.92), parent=g, seg=32)
    capsule((A[0], A[1], A[2] + 0.18), (A[0] + 0.03, A[1], A[2] + 0.34), 0.025, P('wood'), parent=g)
    sph(0.09, (A[0] + 0.12, A[1], A[2] + 0.32), P('green'), scale=(1.4, 0.4, 0.7), parent=g, seg=16)
    return g


def ghost(col, loc, look=(0.0, -1.0), parent=None, scale=1.0):
    e = group("ghost", 0, loc=(loc[0], loc[1], 0))
    if parent:
        e.parent = parent
    C = P(col, coat=0.8)
    sph(0.42, (0, 0, 1.0), C, parent=e, seg=40)
    cyl(0.42, 0.5, (0, 0, 0.75), C, bevel=0.0, parent=e)
    for k in range(8):
        a = k * 2 * math.pi / 8
        sph(0.11, (math.cos(a) * 0.33, math.sin(a) * 0.33, 0.5), C, scale=(1, 1, 1.3), parent=e, seg=20)
    W = P('white', coat=0.6)
    for s in (-1, 1):
        sph(0.12, (s * 0.15, -0.34, 1.02), W, scale=(0.9, 0.6, 1.15), parent=e, seg=24)
        sph(0.06, (s * 0.15 + look[0] * 0.05, -0.41, 1.0 + look[1] * 0.0), P('cobalt'), scale=(1, 0.5, 1), parent=e, seg=16)
    e.scale = (scale, scale, scale)
    return e


def ghosts():
    """닷 러너 — 도망치는 금색 점 줄을 유령 둘이 쫓아온다."""
    g = group("dots", math.radians(-14))
    ghost('tomato', (-0.55, 0.35), look=(1.0, 0), parent=g, scale=1.0)
    ghost('teal', (0.45, 0.55), look=(-1.0, 0), parent=g, scale=0.85)
    dot = mat('dot', PAL['mustard'], emit=(1.0, 0.7, 0.2), estr=0.35, coat=0.8)
    for k in range(5):
        sph(0.07, (-0.9 + k * 0.42, -0.55, 0.08), dot, parent=g, seg=16)
    sph(0.15, (1.05, -0.5, 0.16), dot, parent=g, seg=24)
    return g


def burger():
    """버거 셰프 — 참깨빵 치즈버거 + 이쑤시개 깃발."""
    g = group("burger", math.radians(-18))
    bun = mat('bun', (0.93, 0.58, 0.22), rough=0.35, coat=0.6)
    cyl(0.62, 0.12, (0, 0, 0.06), P('cream'), bevel=0.04, parent=g)  # 접시
    cyl(0.78, 0.24, (0, 0, 0.26), bun, bevel=0.1, parent=g)
    cyl(0.86, 0.22, (0, 0, 0.5), mat('patty', (0.33, 0.16, 0.08), rough=0.7, coat=0.2), bevel=0.08, parent=g)
    box((1.3, 1.3, 0.05), (0, 0, 0.64), mat('cheese', (1.0, 0.75, 0.15), rough=0.3, coat=0.5), rot=(0, 0, math.radians(45)), bevel=0.02, parent=g)
    cyl(0.8, 0.09, (0, 0, 0.72), P('tomato'), bevel=0.03, parent=g)
    let = mat('lettuce', (0.35, 0.8, 0.25), rough=0.4, coat=0.5)
    for k in range(10):
        a = k * 2 * math.pi / 10
        sph(0.2, (math.cos(a) * 0.72, math.sin(a) * 0.72, 0.8), let, scale=(1.2, 1.2, 0.3), parent=g, seg=20)
    cyl(0.8, 0.06, (0, 0, 0.8), let, bevel=0.02, parent=g)
    sph(0.84, (0, 0, 0.84), bun, scale=(1, 1, 0.62), parent=g, seg=48)
    seed = P('ivory')
    for k in range(9):
        a = k * 2.4
        rr = 0.25 + (k % 3) * 0.17
        x, y = math.cos(a) * rr, math.sin(a) * rr
        z = 0.84 + 0.52 * math.sqrt(max(0, 1 - (x * x + y * y) / 0.7))
        sph(0.045, (x, y, z), seed, scale=(1.4, 0.8, 0.5), parent=g, seg=12)
    capsule((0.08, 0, 1.3), (0.1, 0, 2.05), 0.018, P('wood'), parent=g)
    prism([(0, 0), (0.42, -0.1), (0, -0.24)], 0.02, (0.1, 0, 2.05), P('tomato'), parent=g)
    return g


def quiz():
    """라이브 퀴즈 — 큰 빨간 부저 + 금색 물음표 팻말."""
    g = group("quiz", math.radians(-20))
    box((1.2, 0.95, 0.46), (0.3, 0, 0.23), P('violet'), bevel=0.08, parent=g)
    box((1.22, 0.1, 0.12), (0.3, -0.45, 0.34), P('mustard'), bevel=0.03, parent=g)
    cyl(0.44, 0.1, (0.3, 0, 0.51), CHROME(), bevel=0.02, parent=g)
    btn = mat('buzz', PAL['tomato'], emit=(1.0, 0.15, 0.1), estr=0.35, coat=1.0, rough=0.15)
    sph(0.4, (0.3, 0, 0.56), btn, scale=(1, 1, 0.62), parent=g, seg=40)
    bulb = mat('bulb', (1, 0.9, 0.6), emit=(1.0, 0.82, 0.45), estr=8, coat=0)
    for k in range(5):
        sph(0.035, (-0.14 + k * 0.22, -0.48, 0.2), bulb, parent=g, seg=12)
    q = group("q", 0, loc=(-0.62, 0.15, 0))
    q.parent = g
    q.rotation_euler = (0, 0, math.radians(14))
    capsule((0, 0, 0.1), (0, 0, 0.9), 0.04, CHROME(), parent=q)
    cyl(0.25, 0.08, (0, 0, 0.04), P('slate'), bevel=0.02, parent=q)
    cyl(0.48, 0.1, (0, -0.02, 1.35), P('cobalt'), rot=(math.radians(90), 0, 0), bevel=0.03, parent=q)
    torus(0.48, 0.04, (0, -0.02, 1.35), GOLD(), rot=(math.radians(90), 0, 0), parent=q)
    text("?", 0.72, (0, -0.1, 1.35), GOLD(), extrude=0.05, parent=q)
    return g


TOYS = {'roulette': roulette, 'car-racing': car, 'glory-racing': brawl, 'dice': dice, 'ladder': ladder,
        'bingo': bingo, 'team': team, 'retro': arcade, 'balloon': balloon,
        'lotto': lotto, 'lucky-merge': planet, 'orbit': engine, 'dodge': rocket, 'tetris': blocks,
        'starship-lander': lander, 'brick': bricks, 'snake': snake, 'pacman': ghosts, 'burger': burger, 'quiz': quiz}
HOME_IDS = ['roulette', 'car-racing', 'glory-racing', 'dice', 'ladder', 'bingo', 'team', 'retro', 'balloon']

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ids = argv or HOME_IDS
    for tid in ids:
        sc = studio()
        TOYS[tid]()
        sc.render.filepath = os.path.join(OUTDIR, tid + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", tid)
