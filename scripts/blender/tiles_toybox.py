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


def _racer(col, num, helmet, loc, parent):
    """틴토이 경주차 한 대 — 번호판·헬멧 드라이버·크롬 휠. 로컬 +x 가 진행 방향."""
    g = group("racer", 0, loc=loc)
    g.parent = parent
    C = P(col)
    cyl(0.36, 1.55, (0, 0, 0.62), C, rot=(0, math.radians(90), 0), bevel=0.0, parent=g)
    sph(0.36, (0.78, 0, 0.62), C, scale=(1.55, 1, 1), parent=g)
    sph(0.36, (-0.78, 0, 0.62), C, scale=(0.7, 1, 1), parent=g)
    cyl(0.372, 0.16, (0.25, 0, 0.62), P('cream'), rot=(0, math.radians(90), 0), bevel=0.0, parent=g)
    cyl(0.372, 0.06, (0.42, 0, 0.62), P('tomato' if col != 'tomato' else 'white'), rot=(0, math.radians(90), 0), bevel=0.0, parent=g)
    cyl(0.19, 0.03, (-0.2, -0.36, 0.64), P('white'), rot=(math.radians(90), 0, 0), bevel=0.005, parent=g)
    text(num, 0.26, (-0.2, -0.385, 0.62), DARK(), extrude=0.012, parent=g)
    sph(0.25, (-0.28, 0, 0.9), DARK(), scale=(1.2, 1, 0.45), parent=g)
    sph(0.17, (-0.3, 0, 1.08), P(helmet), parent=g)
    box((0.07, 0.26, 0.07), (-0.16, 0, 1.1), DARK(), bevel=0.02, parent=g)
    glass = mat('glass', (0.7, 0.85, 1.0), rough=0.05, coat=0, trans=0.9)
    box((0.03, 0.34, 0.16), (-0.02, 0, 0.98), glass, rot=(0, math.radians(-28), 0), bevel=0.01, parent=g)
    box((0.14, 0.05, 0.36), (-0.95, 0, 0.95), C, bevel=0.03, parent=g)
    for x, r in ((0.62, 0.26), (-0.55, 0.30)):
        for s in (-1, 1):
            cyl(r, 0.2, (x, s * 0.44, r), RUBBER(), rot=(math.radians(90), 0, 0), bevel=0.05, parent=g)
            cyl(r * 0.52, 0.215, (x, s * 0.44, r), CHROME(), rot=(math.radians(90), 0, 0), bevel=0.02, parent=g)
            sph(0.05, (x, s * 0.56, r), P('tomato'), parent=g, seg=16)
    for s in (-1, 1):
        cyl(0.05, 0.3, (-1.02, s * 0.16, 0.5), CHROME(), rot=(0, math.radians(90), 0), parent=g)
    return g


def car():
    """카레이싱 — 세 대가 나란히 코를 맞대고 달린다(2026-09-25 운영자: '자동차 3개가 경쟁적으로 레이스').
    가운데 초록(타일색)이 코 하나 앞서고, 좌우가 바짝 붙어 추격. 뒤로 속도선·흙먼지."""
    g = group("car", math.radians(-20))
    S = 0.68
    lanes = [('cobalt', '1', 'cream', (0.10, 0.98)),     # 뒤 차선
             ('green', '7', 'mustard', (0.34, 0.0)),     # 가운데 — 코 하나 앞
             ('tomato', '3', 'white', (-0.06, -0.98))]   # 앞 차선
    for col, num, hel, (x, y) in lanes:
        r = _racer(col, num, hel, (x, y, 0), g)
        r.scale = (S, S, S)
    spd = mat('speed', (0.97, 0.95, 0.9), emit=(1.0, 0.98, 0.9), estr=0.25, coat=0)
    for (x0, y, z, L) in ((-0.78, 0.98, 0.95, 0.55), (-0.62, 0.3, 1.05, 0.5), (-0.95, -0.98, 0.72, 0.6),
                          (-0.9, -0.5, 1.02, 0.42), (-0.6, 1.4, 0.5, 0.4)):
        capsule((x0, y, z), (x0 - L, y, z + 0.02), 0.022, spd, parent=g)
    dust = mat('dust', (0.78, 0.63, 0.46), rough=0.95, coat=0)
    for (x, y, z, r) in ((-0.95, -1.25, 0.14, 0.17), (-1.18, -1.15, 0.22, 0.12), (-1.36, -1.08, 0.14, 0.09),
                         (-0.7, -0.3, 0.14, 0.13), (-0.9, -0.2, 0.2, 0.09), (-0.9, 0.7, 0.14, 0.13), (-1.1, 0.8, 0.2, 0.09)):
        sph(r, (x, y, z), dust, parent=g, seg=20)
    g.location = (0.22, 0.4, 0)   # 앞 차선이 프레임 아래·왼쪽으로 잘리지 않게
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
    """빙고 — 황동 추첨 케이지(손잡이·번호공) + 앞에 기대 세운 B-I-N-G-O 카드(대각선 한 줄 도장 = 빙고!).
    2026-09-25 운영자: '빙고 느낌이 바로 전달되게 — 숫자 뽑는 머신과 빙고 체크 종이까지 같이'."""
    g = group("bingo", 0)
    VI = P('violet')
    # ── 추첨 케이지(뒤 왼쪽) ──
    m = group("machine", math.radians(-26), loc=(-0.52, 0.5, 0))
    m.parent = g
    box((1.62, 0.86, 0.16), (0, 0, 0.08), VI, bevel=0.06, parent=m)
    box((1.46, 0.7, 0.05), (0, 0, 0.18), P('wood', rough=0.5, coat=0.3), bevel=0.02, parent=m)
    Cz = 1.2
    R = 0.62
    for s in (-1, 1):
        box((0.1, 0.2, 1.06), (s * 0.76, 0, 0.7), VI, bevel=0.035, parent=m)
        cyl(0.14, 0.07, (s * 0.73, 0, Cz), GOLD(), rot=(0, math.radians(90), 0), bevel=0.015, parent=m)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=R, location=(0, 0, Cz), segments=16, ring_count=10,
                                         rotation=(0, math.radians(90), 0))
    cage = bpy.context.object
    wf = cage.modifiers.new("wf", 'WIREFRAME')
    wf.thickness = 0.026
    _fin(cage, GOLD(), parent=m)
    torus(R + 0.01, 0.035, (0, 0, Cz), GOLD(), rot=(0, math.radians(90), 0), parent=m)
    for s in (-1, 1):
        torus(math.sqrt(R * R - 0.38 ** 2) + 0.01, 0.028, (s * 0.38, 0, Cz), GOLD(), rot=(0, math.radians(90), 0), parent=m)
    cyl(0.045, 1.72, (0, 0, Cz), CHROME(), rot=(0, math.radians(90), 0), parent=m)
    # 손잡이 크랭크(오른쪽)
    capsule((0.86, 0, Cz), (0.86, -0.1, Cz - 0.36), 0.04, CHROME(), parent=m)
    capsule((0.86, -0.1, Cz - 0.36), (1.02, -0.1, Cz - 0.36), 0.03, CHROME(), parent=m)
    cyl(0.06, 0.2, (1.1, -0.1, Cz - 0.36), P('tomato'), rot=(0, math.radians(90), 0), bevel=0.02, parent=m)
    # 안쪽 번호공
    cols = ['tomato', 'teal', 'mustard', 'cobalt', 'pink', 'green', 'orange', 'cream']
    spots = [(-0.3, 0.05, -0.36), (-0.02, 0.15, -0.44), (0.28, 0.0, -0.36), (-0.14, -0.2, -0.3),
             (0.14, -0.24, -0.28), (0.0, 0.1, -0.16), (-0.34, -0.05, -0.12), (0.33, 0.15, -0.14)]
    for (x, y, z), cn in zip(spots, cols):
        sph(0.14, (x, y, Cz + z), P(cn, coat=0.9), parent=m, seg=24)
    # 뽑혀 나온 공 — 받침 접시 위
    cyl(0.24, 0.06, (0.42, -0.3, 0.23), GOLD(), bevel=0.02, parent=m)
    Bp = (0.42, -0.3, 0.46)
    sph(0.22, Bp, P('white', coat=0.9), parent=m, seg=32)
    torus(0.2, 0.03, Bp, P('tomato'), rot=(0, math.radians(90), 0), parent=m)
    # ── 빙고 카드(앞 오른쪽, 뒤로 살짝 기대 세움) ──
    cd = group("card", 0, loc=(0.5, -0.42, 0))
    cd.parent = g
    cd.rotation_euler = (math.radians(-20), 0, math.radians(14))
    Wd, Ht = 1.34, 1.66
    box((Wd, 0.07, Ht), (0, 0, Ht / 2), VI, bevel=0.035, parent=cd)
    paper = P('ivory', rough=0.45, coat=0.15)
    box((Wd - 0.1, 0.02, Ht - 0.1), (0, -0.04, Ht / 2), paper, bevel=0.01, parent=cd)
    cw, gap = 0.226, 0.02
    xs = [(i - 2) * (cw + gap) for i in range(5)]
    ztop = Ht - 0.2
    head = ['tomato', 'orange', 'mustard', 'green', 'cobalt']
    WT = P('white', coat=0.6)
    for i, L in enumerate("BINGO"):
        box((cw, 0.03, 0.24), (xs[i], -0.06, ztop), P(head[i]), bevel=0.02, parent=cd)
        text(L, 0.21, (xs[i], -0.085, ztop - 0.005), WT, extrude=0.01, parent=cd)
    nums = [[3, 19, 34, 52, 67], [11, 24, 41, 48, 70], [7, 17, 0, 55, 62], [14, 29, 38, 59, 73], [1, 22, 44, 46, 65]]
    daub = {(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (0, 3), (3, 1)}
    ink = mat('daub', (0.95, 0.12, 0.42), rough=0.3, coat=0.3, emit=(1.0, 0.1, 0.4), estr=0.15)
    cell = P('cream', rough=0.5, coat=0.1)
    D = DARK()

    def noline(o):
        # 작은 숫자에 잉크 외곽선이 붙으면 까만 얼룩이 된다 → TOY 컬렉션 밖으로
        for c in list(o.users_collection):
            c.objects.unlink(o)
        bpy.context.scene.collection.objects.link(o)
    for r in range(5):
        z = ztop - 0.29 - r * (cw + gap)
        for c in range(5):
            x = xs[c]
            box((cw, 0.02, cw), (x, -0.055, z), cell, bevel=0.008, parent=cd)
            if (r, c) == (2, 2):
                prism(star_pts(0.11, 0.05), 0.03, (x, -0.075, z), GOLD(), parent=cd)
                continue
            if (r, c) in daub:
                cyl(0.098, 0.02, (x, -0.072, z), ink, rot=(math.radians(90), 0, 0), bevel=0.006, parent=cd)
                noline(text(str(nums[r][c]), 0.11, (x, -0.086, z - 0.003), WT, extrude=0.004, parent=cd))
            else:
                noline(text(str(nums[r][c]), 0.11, (x, -0.07, z - 0.003), D, extrude=0.004, parent=cd))
    # 도장 펜(대버) — 카드 앞에 세워 둠
    dp = group("dauber", 0, loc=(1.28, -0.72, 0))
    dp.parent = g
    dp.rotation_euler = (0, math.radians(-8), 0)
    cyl(0.13, 0.5, (0, 0, 0.25), mat('dauberbody', (0.95, 0.12, 0.42), rough=0.15, coat=0.9), bevel=0.03, parent=dp)
    cyl(0.1, 0.18, (0, 0, 0.58), P('white', coat=0.6), bevel=0.02, parent=dp)
    sph(0.1, (0, 0, 0.67), P('white', coat=0.6), scale=(1, 1, 0.6), parent=dp, seg=24)
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
    """팀뽑기 — 빨강 다섯 vs 파랑 다섯 팔짱 대치 + 금색 VS (2026-09-25 운영자: '5명이 대치, 최대한 오버랩되어 붙어 서게').
    단체사진 대형: 앞줄 둘이 팔짱 끼고 버티고, 뒷줄 셋은 앞줄 어깨 사이로 얼굴을 들이민다.
    뒷줄은 조금 크게 — 원근으로 작아지는 만큼 상쇄해야 110px 폰 타일에서도 얼굴 열 개가 다 읽힌다."""
    g = group("team", 0)
    # (|x|, y, scale, yaw°) — 뒷줄 → 앞줄
    slots = [(0.27, 0.74, 0.70, 30), (0.74, 0.80, 0.70, 30), (1.2, 0.74, 0.70, 26),
             (0.52, 0.0, 0.64, 38), (0.98, 0.12, 0.64, 34)]
    for side, col in ((-1, 'tomato'), (1, 'cobalt')):
        for (ax, y, s, yaw) in slots:
            f = figure(col, (side * ax, y), math.radians(-side * yaw), 'cross', 'angry', parent=g)
            f.scale = (s, s, s)
    text("VS", 0.56, (0, -0.62, 0.62), mat('vs', PAL['mustard'], emit=(1.0, 0.6, 0.1), estr=0.3, coat=0.8), extrude=0.1, parent=g)
    return g


def _brawl_face(e, H, HR, mood):
    """브롤런 전용 얼굴 — B급 표정. angry(부릅+이빨) / hit(질끈 >< + 쩍 벌린 입 + 혀)"""
    D = DARK()
    W = P('white', coat=0.6)
    fy = H.y - HR * 0.93
    if mood == 'angry':
        for s in (-1, 1):
            sph(0.1, (s * 0.15, fy + 0.03, H.z + 0.04), W, scale=(1, 0.5, 0.85), parent=e, seg=24)
            sph(0.05, (s * 0.12, fy - 0.02, H.z + 0.03), D, scale=(1, 0.5, 1), parent=e, seg=16)
            box((0.22, 0.05, 0.065), (s * 0.15, fy + 0.0, H.z + 0.17), D, rot=(0, math.radians(-30 * s), 0), bevel=0.02, parent=e)
        box((0.3, 0.06, 0.11), (0, fy + 0.04, H.z - 0.18), W, bevel=0.025, parent=e)
        for k in (-0.075, 0, 0.075):
            box((0.006, 0.07, 0.11), (k, fy + 0.02, H.z - 0.18), D, bevel=0.0, parent=e)
        box((0.3, 0.07, 0.006), (0, fy + 0.02, H.z - 0.18), D, bevel=0.0, parent=e)
    else:
        # 질끈 감은 눈 > < — 두 막대로 꺾쇠
        for s in (-1, 1):
            cx, cz = s * 0.15, H.z + 0.07
            box((0.13, 0.05, 0.045), (cx, fy + 0.01, cz + 0.035), D, rot=(0, math.radians(28 * s), 0), bevel=0.015, parent=e)
            box((0.13, 0.05, 0.045), (cx, fy + 0.01, cz - 0.035), D, rot=(0, math.radians(-28 * s), 0), bevel=0.015, parent=e)
        # 쩍 벌린 입 + 혀
        sph(0.13, (0.02, fy + 0.03, H.z - 0.19), D, scale=(1.05, 0.45, 0.85), parent=e, seg=24)
        sph(0.07, (0.03, fy - 0.0, H.z - 0.25), mat('tongue', (0.95, 0.35, 0.42), rough=0.3, coat=0.4), scale=(1, 0.5, 0.6), parent=e, seg=20)
        # 볼 빨개짐(맞은 쪽)
        sph(0.07, (-0.27, fy + 0.07, H.z - 0.06), mat('blush', (1.0, 0.42, 0.40), rough=0.4, coat=0.2), scale=(1, 0.4, 0.7), parent=e, seg=16)


def _runner(col, loc, yaw, tilt, mood, parent, head_yaw=None, s=0.9):
    """전력 질주 피규어 — 앞다리 무릎이 올라가고 뒷다리는 뒤로 차올린 한 순간. 몸통은 앞으로 기운다.
    로컬 정면 = -y. 팔은 호출하는 쪽에서 월드 좌표로 붙인다(상대에게 뻗어야 해서)."""
    e = group("run", 0, loc=(loc[0], loc[1], 0.1 * s / 0.9))
    e.rotation_euler = (math.radians(tilt), 0, yaw)
    e.parent = parent
    e.scale = (s, s, s)
    C = P(col)
    N = P('navy')
    capsule((0, 0, 0.55), (0, 0, 0.8), 0.28, C, parent=e)
    capsule((-0.12, 0, 0.42), (-0.13, -0.36, 0.42), 0.1, N, parent=e)
    capsule((-0.13, -0.36, 0.42), (-0.13, -0.46, 0.14), 0.095, N, parent=e)
    sph(0.12, (-0.13, -0.53, 0.1), DARK(), scale=(1, 1.4, 0.7), parent=e)
    capsule((0.12, 0, 0.42), (0.13, 0.26, 0.22), 0.1, N, parent=e)
    capsule((0.13, 0.26, 0.22), (0.13, 0.56, 0.44), 0.095, N, parent=e)
    sph(0.12, (0.13, 0.63, 0.47), DARK(), scale=(1, 0.75, 1.3), parent=e)
    H = Vector((0, 0, 1.38))
    HR = 0.42
    if head_yaw is None:
        hd = e
    else:
        bpy.context.view_layer.update()
        hp = e.matrix_world @ Vector((0, -0.05, 1.38))
        hd = group("head", 0, loc=(hp.x, hp.y, hp.z - 1.38 * s))
        hd.rotation_euler = (0, 0, head_yaw)
        hd.parent = parent
        hd.scale = (s, s, s)
    sph(HR, H, P('cream'), parent=hd)
    _brawl_face(hd, H, HR, mood)
    return e, hd


def brawl():
    """브롤런 — 다섯이 한 덩어리로 부대끼며 달린다(2026-09-25 운영자: '5명이 경쟁적으로, 최대한 부대끼며').
    앞줄: 빨강 주먹이 노랑 뺨에 꽂히고, 노랑은 손바닥으로 빨강 얼굴을 밀어낸다.
    뒷줄: 파랑이 초록 등판을 붙잡아 끌고, 초록은 선두 분홍 등을 떠민다. 수위는 톰과 제리(피·상처 없음)."""
    g = group("brawl", 0)
    S = 0.72
    k = S / 0.9
    rad = math.radians
    # 뒷줄 → 앞줄
    (C, CH) = _runner('cobalt', (-1.02, 0.5), rad(76), 22, 'angry', g, head_yaw=rad(30), s=S)
    (D, DH) = _runner('green', (-0.12, 0.56), rad(72), 18, 'angry', g, head_yaw=rad(26), s=S)
    (E, EH) = _runner('pink', (0.98, 0.4), rad(66), 12, 'hit', g, head_yaw=rad(14), s=S)
    (A, AH) = _runner('tomato', (-0.52, -0.2), rad(74), 21, 'angry', g, head_yaw=rad(34), s=S)
    (B, BH) = _runner('mustard', (0.4, -0.28), rad(70), 16, 'hit', g, head_yaw=rad(18), s=S)
    bpy.context.view_layer.update()
    W = lambda e, p: e.matrix_world @ Vector(p)
    SK = P('cream')

    def arm(sh, end, col, bend=None, hand=0.12, squash=None):
        if bend is not None:
            el = (sh + end) / 2 + Vector(bend) * k
            capsule(sh, el, 0.085 * k, P(col), parent=g)
            capsule(el, end, 0.085 * k, P(col), parent=g)
        else:
            capsule(sh, end, 0.085 * k, P(col), parent=g)
        sph(hand * k, end, SK, scale=squash or (1, 1, 1), parent=g, seg=20)

    def swing(e, col, a, b):
        arm(W(e, a), W(e, b), col)

    hot = mat('impact', (1.0, 0.82, 0.15), emit=(1.0, 0.7, 0.1), estr=0.4, coat=0)
    # 빨강(앞줄 뒤) → 노랑 뺨에 주먹
    cheek = W(BH, (-0.3, -0.12, 1.3))
    sh = W(A, (0.27, 0.02, 0.84))
    arm(sh, sh + (cheek - sh) * 0.86, 'tomato', hand=0.135)
    swing(A, 'tomato', (-0.27, 0.02, 0.84), (-0.36, 0.3, 0.6))
    # 노랑(앞줄 앞) → 손바닥으로 빨강 이마를 밀기 + 한 팔 허우적
    sh = W(B, (-0.27, 0.02, 0.84))
    face = W(AH, (0.16, -0.3, 1.66))
    arm(sh, sh + (face - sh) * 0.93, 'mustard', bend=(0.05, -0.12, 0.22), hand=0.13, squash=(0.75, 1.0, 1.15))
    swing(B, 'mustard', (0.27, 0.02, 0.84), (0.52, 0.05, 1.28))
    # 초록(뒷줄 가운데) → 분홍 등판 떠밀기
    sh = W(D, (0.27, 0.02, 0.84))
    back_e = W(E, (0.0, 0.3, 0.85))
    arm(sh, sh + (back_e - sh) * 0.92, 'green', hand=0.13, squash=(0.75, 1.0, 1.15))
    swing(D, 'green', (-0.27, 0.02, 0.84), (-0.3, -0.35, 1.05))
    # 파랑(뒷줄 꼴찌) → 초록 등판 움켜쥐기 + 주먹 휘두르기
    sh = W(C, (0.27, 0.02, 0.84))
    back_d = W(D, (0.0, 0.3, 0.8))
    arm(sh, sh + (back_d - sh) * 0.94, 'cobalt', bend=(0.0, 0.0, 0.12), hand=0.13)
    swing(C, 'cobalt', (-0.27, 0.02, 0.84), (-0.2, -0.1, 1.5))
    # 분홍(선두) → 떠밀려 두 팔 허우적
    swing(E, 'pink', (-0.27, 0.02, 0.84), (-0.5, 0.3, 1.95))    # 만세 — 얼굴을 가리지 않게 머리 위로
    swing(E, 'pink', (0.27, 0.02, 0.84), (0.55, 0.2, 1.9))
    # 충돌 별 — 노랑 뺨(크게), 분홍 등(작게)
    prism(star_pts(0.2, 0.09, 8), 0.06, (cheek.x - 0.14, cheek.y - 0.3, cheek.z + 0.16), hot, parent=g)
    prism(star_pts(0.13, 0.06, 8), 0.05, (back_e.x - 0.05, back_e.y - 0.35, back_e.z + 0.25), hot, parent=g)
    # 속도선 — 뒤쪽(-x)
    spd = mat('speed', (0.97, 0.95, 0.9), emit=(1.0, 0.98, 0.9), estr=0.25, coat=0)
    for (x0, y, z, L) in ((-1.32, 0.6, 1.5, 0.32), (-1.4, 0.6, 1.15, 0.4), (-1.35, 0.6, 0.8, 0.3),
                          (-0.9, -0.2, 0.55, 0.3)):
        capsule((x0, y, z), (x0 - L, y + 0.1, z - 0.04), 0.022, spd, parent=g)
    dust = mat('dust', (0.78, 0.63, 0.46), rough=0.95, coat=0)
    for (x, y, z, r) in ((-1.4, 0.85, 0.18, 0.16), (-1.6, 0.9, 0.25, 0.11), (-1.74, 0.92, 0.17, 0.07),
                         (-0.9, 0.05, 0.13, 0.13), (-1.08, 0.1, 0.2, 0.09), (0.0, 0.1, 0.12, 0.1)):
        sph(r, (x, y, z), dust, parent=g, seg=20)
    sweat = mat('sweat', (0.45, 0.8, 1.0), rough=0.05, coat=1.0)
    for hh, pts in ((EH, ((0.46, 0.3, 0.06), (0.6, 0.1, 0.05), (0.34, 0.52, 0.045))),):
        hb = W(hh, (0, 0, 1.38))
        for (dx, dz, s) in pts:
            sph(s, (hb.x + dx, hb.y - 0.2, hb.z + dz), sweat, scale=(0.8, 0.8, 1.3), parent=g, seg=18)
    g.location = (-0.06, 0.1, 0)   # 프레임 양옆에 닿지 않게 — 팔은 월드 좌표로 붙였으니 마지막에 통째로 민다
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
    """풍선 룰렛 — 바닥 펌프(T 손잡이·발판·압력 게이지 빨간 구간) + 호스로 물린 광택 라텍스 풍선.
    2026-09-25 운영자: '더 정교하고 리얼하게'. 풍선은 회전체(아래가 좁은 물방울형)로 깎고 목·말린 입구를 노즐에 물린다."""
    g = group("balloon", math.radians(-16))
    PX = -0.66
    MU = P('mustard')
    # 발판 + 고무 트레드
    for s in (-1, 1):
        box((0.36, 0.5, 0.08), (PX + s * 0.36, -0.02, 0.04), P('cobalt'), bevel=0.03, parent=g)
        for k2 in range(3):
            box((0.3, 0.05, 0.025), (PX + s * 0.38, -0.2 + k2 * 0.17, 0.09), RUBBER(), bevel=0.01, parent=g)
    cyl(0.3, 0.12, (PX, 0, 0.1), CHROME(), bevel=0.03, parent=g)
    # 몸통 실린더 + 크롬 밴드 + 빨간 띠
    cyl(0.22, 1.0, (PX, 0, 0.66), MU, bevel=0.02, parent=g)
    for z in (0.2, 1.12):
        cyl(0.235, 0.07, (PX, 0, z), CHROME(), bevel=0.015, parent=g)
    cyl(0.226, 0.08, (PX, 0, 0.98), P('tomato'), bevel=0.005, parent=g)
    sph(0.2, (PX, 0, 1.16), CHROME(), scale=(1, 1, 0.45), parent=g, seg=32)
    cyl(0.035, 0.44, (PX, 0, 1.4), CHROME(), parent=g)
    # T 손잡이 + 고무 그립
    capsule((PX - 0.2, 0, 1.62), (PX + 0.2, 0, 1.62), 0.05, P('tomato'), parent=g)
    for s in (-1, 1):
        cyl(0.07, 0.24, (PX + s * 0.32, 0, 1.62), RUBBER(), rot=(0, math.radians(90), 0), bevel=0.03, parent=g)
    # 압력 게이지 — 크롬 베젤, 흰 판, 초록·노랑·빨강 눈금 호, 빨강으로 넘어간 바늘
    G = Vector((PX, -0.27, 0.62))
    gy = G.y
    cyl(0.2, 0.08, (G.x, gy + 0.02, G.z), CHROME(), rot=(math.radians(90), 0, 0), bevel=0.02, parent=g)
    cyl(0.17, 0.02, (G.x, gy - 0.025, G.z), P('white', coat=0.6), rot=(math.radians(90), 0, 0), bevel=0.004, parent=g)

    def arc(r0, r1, a0, a1, m_):
        me = bpy.data.meshes.new("arc")
        bm = bmesh.new()
        n = 12
        ring = []
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            ring.append((bm.verts.new((math.cos(a) * r0, 0, math.sin(a) * r0)),
                         bm.verts.new((math.cos(a) * r1, 0, math.sin(a) * r1))))
        for i in range(n):
            bm.faces.new((ring[i][0], ring[i + 1][0], ring[i + 1][1], ring[i][1]))
        bm.normal_update()
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("arc", me)
        bpy.context.collection.objects.link(o)
        o.location = (G.x, gy - 0.04, G.z)
        md = o.modifiers.new("sol", 'SOLIDIFY')
        md.thickness = 0.01
        _fin(o, m_, parent=g)
    arc(0.1, 0.15, 150, 90, P('green'))
    arc(0.1, 0.15, 90, 50, P('mustard'))
    arc(0.1, 0.15, 50, 20, P('tomato'))
    na = math.radians(38)
    capsule((G.x, gy - 0.05, G.z), (G.x + math.cos(na) * 0.13, gy - 0.05, G.z + math.sin(na) * 0.13), 0.014, P('tomato'), parent=g)
    sph(0.03, (G.x, gy - 0.06, G.z), DARK(), parent=g, seg=16)
    torus(0.18, 0.02, (G.x, gy - 0.03, G.z), CHROME(), rot=(math.radians(90), 0, 0), parent=g)
    # 호스 — 몸통 아래 배출구에서 바닥을 기어 풍선 노즐로
    cyl(0.06, 0.16, (PX + 0.27, 0, 0.26), CHROME(), rot=(0, math.radians(90), 0), bevel=0.01, parent=g)
    NZ = Vector((0.36, -0.06, 0.5))   # 노즐 끝(풍선 입구)
    hose_pts = [(PX + 0.35, 0, 0.26), (-0.05, -0.2, 0.08), (0.3, -0.18, 0.1), (NZ.x - 0.02, NZ.y, NZ.z - 0.26)]
    cu = bpy.data.curves.new("hose", 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 0.05
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
    cyl(0.06, 0.1, (NZ.x - 0.02, NZ.y, NZ.z - 0.22), CHROME(), bevel=0.01, parent=g)
    cyl(0.035, 0.2, (NZ.x - 0.01, NZ.y, NZ.z - 0.1), CHROME(), bevel=0.005, parent=g)
    # 풍선 — 회전체. 아래(목)가 좁고 위가 둥근 물방울형
    bl = group("bln", 0, loc=(NZ.x, NZ.y, NZ.z - 0.02))
    bl.parent = g
    bl.rotation_euler = (math.radians(-6), math.radians(9), 0)
    NECK = 0.22
    HB = 1.52
    RM = 0.68
    prof = [(0.05, 0.0), (0.052, 0.08), (0.058, 0.16), (0.07, NECK)]
    M = 44
    for i in range(1, M + 1):
        s_ = i / M
        r = RM * math.sin(math.pi * (s_ ** 1.35)) ** 0.62
        r = max(r, 0.07 * (1 - s_) ** 2)
        prof.append((r, NECK + s_ * HB))
    me = bpy.data.meshes.new("latex")
    bm = bmesh.new()
    NV = 48
    rings = []
    for (r, z) in prof[:-1]:
        rings.append([bm.verts.new((math.cos(2 * math.pi * j / NV) * r, math.sin(2 * math.pi * j / NV) * r, z)) for j in range(NV)])
    top = bm.verts.new((0, 0, prof[-1][1]))
    for a, b in zip(rings, rings[1:]):
        for j in range(NV):
            j2 = (j + 1) % NV
            bm.faces.new((a[j], a[j2], b[j2], b[j]))
    for j in range(NV):
        bm.faces.new((rings[-1][j], rings[-1][(j + 1) % NV], top))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    lo = bpy.data.objects.new("latex", me)
    bpy.context.collection.objects.link(lo)
    ss = lo.modifiers.new("ss", 'SUBSURF')
    ss.levels = ss.render_levels = 2
    latex = mat('latex', (0.93, 0.07, 0.2), rough=0.14, coat=1.0)
    _fin(lo, latex, parent=bl)
    # 말린 입구(립) — 노즐에 물림
    torus(0.07, 0.03, (0, 0, 0.02), latex, parent=bl)
    torus(0.068, 0.022, (0, 0, 0.1), CHROME(), parent=bl)   # 고정 클립
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
    """테트로미노 쌓기 — 쌓인 테트로미노 + 위에서 떨어지는 T 블록."""
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


# ════════════ 홈 카테고리 버튼 아이콘 4종 (2026-09-25) ════════════
# 40~56px 로 작게 쓰인다 → 부품 적게, 굵은 실루엣, 카테고리 색 하나로 몰아 준다.
# 게임 타일(룰렛·주사위·로또·레트로)과 같은 그림이 되지 않게 조합을 바꿨다.
def cat_random():
    """랜덤뽑기 — 주황·노랑 6칸 돌림판 + 앞에 주사위 두 개(뽑기 도구 한 벌의 문장)."""
    g = group("cat-random", math.radians(-12))
    w = group("wheel", 0, loc=(-0.32, 0.3, 0))
    w.parent = g
    box((1.1, 0.5, 0.18), (0, 0, 0.09), P('orange'), bevel=0.07, parent=w)
    for s in (-1, 1):
        capsule((s * 0.4, 0.0, 0.18), (s * 0.12, 0.0, 1.0), 0.075, P('mustard'), parent=w)
    C = Vector((0, -0.05, 1.22))
    R = 0.9
    cols = ['orange', 'mustard', 'tomato', 'orange', 'mustard', 'cream']
    n = len(cols)
    for i, cn in enumerate(cols):
        me = bpy.data.meshes.new("wedge")
        bm = bmesh.new()
        a0, a1 = i * 2 * math.pi / n + 0.3, (i + 1) * 2 * math.pi / n + 0.3
        th = 0.08
        cf, cb = bm.verts.new((0, -th, 0)), bm.verts.new((0, th, 0))
        arcf, arcb = [], []
        for k in range(11):
            a = a0 + (a1 - a0) * k / 10
            arcf.append(bm.verts.new((math.cos(a) * R, -th, math.sin(a) * R)))
            arcb.append(bm.verts.new((math.cos(a) * R, th, math.sin(a) * R)))
        bm.faces.new([cf] + arcf)
        bm.faces.new([cb] + list(reversed(arcb)))
        for k in range(10):
            bm.faces.new((arcf[k], arcb[k], arcb[k + 1], arcf[k + 1]))
        bm.faces.new((cf, cb, arcb[0], arcf[0]))
        bm.faces.new((cf, arcf[-1], arcb[-1], cb))
        bm.normal_update()
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("wedge", me)
        bpy.context.collection.objects.link(o)
        o.location = C
        _fin(o, P(cn), parent=w)
    torus(R + 0.05, 0.09, C, GOLD(), rot=(math.radians(90), 0, 0), parent=w)
    cyl(0.17, 0.24, (C.x, C.y - 0.05, C.z), GOLD(), rot=(math.radians(90), 0, 0), parent=w)
    sph(0.1, (C.x, C.y - 0.18, C.z), P('tomato'), parent=w, seg=24)
    cone(0.18, 0.0, 0.38, (C.x, C.y - 0.12, C.z + R + 0.24), P('tomato'), rot=(math.pi, 0, 0), parent=w)
    # 주사위 두 개 — 앞 오른쪽
    IV = P('ivory', rough=0.2, coat=0.8)
    RED = mat('pipred', (0.75, 0.05, 0.05), rough=0.35)
    L = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (-1, 1), (1, -1), (1, 1)],
         5: [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)], 6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)]}

    def die(loc, size, rot, faces):
        e = group("die", 0, loc=loc)
        e.parent = g
        e.rotation_euler = rot
        box((size, size, size), (0, 0, 0), IV, bevel=size * 0.16, seg=5, parent=e)
        h = size / 2
        off = size * 0.26
        for axis, sign, k in faces:
            for u, v in L[k]:
                p = [0, 0, 0]
                p[axis] = sign * (h - 0.012)
                o1, o2 = [a for a in (0, 1, 2) if a != axis]
                p[o1] = u * off
                p[o2] = v * off
                sc = [1.0, 1.0, 1.0]
                sc[axis] = 0.32
                sph(size * 0.1, tuple(p), RED if k == 1 else DARK(), scale=tuple(sc), parent=e, seg=20)
    die((0.42, -0.62, 0.36), 0.72, (0, 0, math.radians(24)), [(2, 1, 5), (1, -1, 1), (0, 1, 3)])
    die((0.95, -0.2, 0.62), 0.6, (math.radians(28), math.radians(18), math.radians(-20)), [(2, 1, 6), (1, -1, 2), (0, 1, 4)])
    return g


def cat_draw():
    """추첨게임 — 분홍 받침 유리 추첨기, 위 관으로 공이 튀어나오고 앞에 번호 복권 한 장."""
    g = group("cat-draw", math.radians(-18))
    MG = mat('magenta', (0.86, 0.10, 0.52), rough=0.26, coat=0.7)
    cyl(0.72, 0.4, (-0.15, 0, 0.2), MG, bevel=0.08, parent=g)
    cyl(0.76, 0.06, (-0.15, 0, 0.42), CHROME(), bevel=0.01, parent=g)
    cyl(0.34, 0.14, (-0.15, 0, 0.47), P('pink'), bevel=0.03, parent=g)
    C = Vector((-0.15, 0, 1.22))
    sph(0.74, C, GLASS(), parent=g, seg=48)
    # 자홍 테 두 줄 — 유리만 있으면 작은 크기에서 창백하게 날아간다
    torus(0.76, 0.05, (C.x, C.y, C.z), MG, parent=g)
    torus(0.76, 0.045, (C.x, C.y, C.z), MG, rot=(math.radians(90), 0, 0), parent=g)
    cols = ['pink', 'mustard', 'teal', 'cream', 'tomato', 'violet', 'pink', 'cobalt']
    spots = [(-0.32, 0.1, -0.38), (0.05, 0.2, -0.46), (0.35, 0.0, -0.36), (-0.12, -0.2, -0.3),
             (0.2, -0.22, -0.12), (-0.34, 0.05, 0.02), (0.06, 0.1, 0.16), (0.36, 0.12, 0.22)]
    for (x, y, z), cn in zip(spots, cols):
        sph(0.16, (C.x + x, C.y + y, C.z + z), P(cn, coat=0.9), parent=g, seg=24)
    cyl(0.13, 0.4, (C.x, 0, 2.08), GLASS(), bevel=0.0, parent=g)
    torus(0.13, 0.03, (C.x, 0, 2.28), CHROME(), parent=g)
    # 튀어나오는 공 — 관 위로 떠 있다
    Bp = (C.x + 0.22, -0.1, 2.52)
    sph(0.22, Bp, P('pink', coat=0.9), parent=g, seg=32)
    cyl(0.13, 0.03, (Bp[0], Bp[1] - 0.205, Bp[2]), P('white'), rot=(math.radians(90), 0, 0), bevel=0.01, parent=g)
    text("7", 0.17, (Bp[0], Bp[1] - 0.228, Bp[2] - 0.004), DARK(), extrude=0.008, parent=g)
    spd = mat('speed', (0.97, 0.95, 0.9), emit=(1.0, 0.98, 0.9), estr=0.25, coat=0)
    for dx in (-0.1, 0.06):
        capsule((Bp[0] + dx - 0.05, Bp[1], Bp[2] - 0.3), (Bp[0] + dx - 0.1, Bp[1], Bp[2] - 0.5), 0.02, spd, parent=g)
    # 복권 — 앞 오른쪽에 비스듬히 기대 세움
    t = group("ticket", 0, loc=(0.62, -0.62, 0))
    t.parent = g
    t.rotation_euler = (math.radians(-24), 0, math.radians(18))
    box((0.9, 0.05, 0.62), (0, 0, 0.31), P('ivory', rough=0.45, coat=0.15), bevel=0.025, parent=t)
    box((0.9, 0.06, 0.16), (0, -0.005, 0.54), MG, bevel=0.02, parent=t)
    for i, cn in enumerate(['pink', 'mustard', 'teal']):
        cyl(0.11, 0.03, (-0.26 + i * 0.26, -0.035, 0.26), P(cn), rot=(math.radians(90), 0, 0), bevel=0.008, parent=t)
    return g


def cat_arcade():
    """아케이드 — 코발트 조작반 위 빨간 알 조이스틱 + 둥근 버튼 둘(캐비닛 없이 손맛만)."""
    g = group("cat-arcade", math.radians(-22))
    box((2.1, 1.25, 0.46), (0, 0, 0.23), P('cobalt'), bevel=0.08, parent=g)
    box((2.14, 0.08, 0.1), (0, -0.62, 0.4), P('mustard'), bevel=0.03, parent=g)
    d = group("deck", 0, loc=(0, 0, 0.5))
    d.parent = g
    d.rotation_euler = (math.radians(10), 0, 0)
    box((2.0, 1.15, 0.1), (0, 0, 0.0), P('teal'), bevel=0.04, parent=d)
    # 조이스틱
    J = (-0.5, 0.02, 0.05)
    cyl(0.26, 0.06, J, CHROME(), bevel=0.02, parent=d)
    sph(0.17, (J[0], J[1], J[2] + 0.06), RUBBER(), scale=(1, 1, 0.55), parent=d, seg=24)
    top = (J[0] + 0.1, J[1] - 0.06, J[2] + 0.85)
    capsule((J[0], J[1], J[2] + 0.05), top, 0.055, CHROME(), parent=d)
    sph(0.32, (top[0] + 0.02, top[1] - 0.01, top[2] + 0.2), mat('stickball', PAL['tomato'], rough=0.14, coat=1.0), parent=d, seg=40)
    # 버튼 둘
    for (x, y, cn) in ((0.28, -0.12, 'mustard'), (0.78, 0.08, 'tomato')):
        cyl(0.26, 0.07, (x, y, 0.06), CHROME(), bevel=0.02, parent=d)
        cyl(0.2, 0.14, (x, y, 0.12), P(cn, coat=1.0, rough=0.15), bevel=0.02, parent=d)
        sph(0.2, (x, y, 0.19), P(cn, coat=1.0, rough=0.15), scale=(1, 1, 0.35), parent=d, seg=32)
    return g


def cat_mission():
    """미션게임 — 초록 과녁 옆을 스치며 솟는 보라 로켓 + 명중 별(도전·목표 달성)."""
    g = group("cat-mission", math.radians(-10))
    t = group("tgt", 0, loc=(0.42, 0.45, 0))
    t.parent = g
    for s in (-1, 1):
        capsule((s * 0.4, 0.2, 0.0), (s * 0.18, 0.05, 1.0), 0.06, P('wood'), parent=t)
    Z = 1.3
    for r, cn, dy in ((0.9, 'green', 0.0), (0.7, 'cream', -0.03), (0.5, 'green', -0.06), (0.3, 'cream', -0.09), (0.14, 'tomato', -0.12)):
        cyl(r, 0.08, (0, dy, Z), P(cn), rot=(math.radians(90), 0, 0), bevel=0.02, parent=t)
    prism(star_pts(0.24, 0.1), 0.07, (0.02, -0.3, Z + 0.02), GOLD(), parent=t)
    # 로켓 — 앞 왼쪽에서 오른쪽 위로
    r = group("rkt", 0, loc=(-0.55, -0.35, 1.05))
    r.parent = g
    r.rotation_euler = (0, math.radians(30), 0)
    VI = P('violet')
    GR = P('green')
    cyl(0.28, 0.95, (0, 0, 0), VI, bevel=0.02, parent=r)
    cone(0.28, 0.0, 0.6, (0, 0, 0.77), P('white', coat=0.8), parent=r)
    cyl(0.285, 0.08, (0, 0, 0.44), GR, bevel=0.0, parent=r)
    cyl(0.12, 0.04, (0, -0.27, 0.12), GLASS(), rot=(math.radians(90), 0, 0), bevel=0.01, parent=r)
    torus(0.12, 0.03, (0, -0.28, 0.12), CHROME(), rot=(math.radians(90), 0, 0), parent=r)
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 2
        fin = prism([(0, 0), (0.32, -0.1), (0.32, -0.4), (0, -0.2)], 0.06, (0, 0, -0.24), GR,
                    rot=(math.radians(90), 0, a), parent=r)
        fin.location = (math.cos(a) * 0.26, math.sin(a) * 0.26, -0.24)
        fin.rotation_euler = (math.radians(90), 0, a)
    cyl(0.17, 0.12, (0, 0, -0.53), CHROME(), bevel=0.02, parent=r)
    flame = mat('flame', (1.0, 0.7, 0.25), emit=(1.0, 0.55, 0.15), estr=2.2, coat=0)
    cone(0.2, 0.0, 0.6, (0, 0, -0.88), flame, rot=(math.pi, 0, 0), parent=r)
    core = mat('flamecore', (1.0, 0.95, 0.7), emit=(1.0, 0.9, 0.6), estr=3.0, coat=0)
    cone(0.1, 0.0, 0.34, (0, -0.02, -0.74), core, rot=(math.pi, 0, 0), parent=r)
    return g


# ════════════ 보드게임 (2026-09-25) — 카테고리 아이콘 + 윷놀이·루도·리버시 ════════════
def _ivory_die(loc, size, rot, faces, parent):
    """상아 주사위 — 보드게임 4종 공용. faces = [(축, 부호, 눈)]"""
    IV = P('ivory', rough=0.2, coat=0.8)
    RED = mat('pipred', (0.75, 0.05, 0.05), rough=0.35)
    L = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (-1, 1), (1, -1), (1, 1)],
         5: [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)], 6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)]}
    e = group("die", 0, loc=loc)
    e.parent = parent
    e.rotation_euler = rot
    box((size, size, size), (0, 0, 0), IV, bevel=size * 0.16, seg=5, parent=e)
    h = size / 2
    off = size * 0.26
    for axis, sign, k in faces:
        for u, v in L[k]:
            p = [0, 0, 0]
            p[axis] = sign * (h - 0.012)
            o1, o2 = [a for a in (0, 1, 2) if a != axis]
            p[o1] = u * off
            p[o2] = v * off
            sc = [1.0, 1.0, 1.0]
            sc[axis] = 0.32
            sph(size * 0.1, tuple(p), RED if k == 1 else DARK(), scale=tuple(sc), parent=e, seg=20)
    return e


def _pawn(col, loc, parent, s=1.0):
    """광택 말 — 넓은 받침 + 원뿔 몸 + 목 칼라 + 둥근 머리."""
    e = group("pawn", 0, loc=loc)
    e.parent = parent
    e.scale = (s, s, s)
    C = P(col, coat=1.0, rough=0.14)
    cyl(0.24, 0.1, (0, 0, 0.05), C, bevel=0.04, parent=e)
    cone(0.2, 0.08, 0.5, (0, 0, 0.35), C, parent=e)
    cyl(0.14, 0.05, (0, 0, 0.6), C, bevel=0.02, parent=e)
    sph(0.16, (0, 0, 0.76), C, parent=e, seg=32)
    return e


def cat_board():
    """보드게임 — 나무 판(청록·크림 칸 테두리) 위에 빨간 말 + 상아 주사위."""
    g = group("cat-board", math.radians(-20))
    WD = P('wood', rough=0.45, coat=0.4)
    box((2.0, 1.6, 0.2), (0, 0.1, 0.1), WD, bevel=0.07, parent=g)
    box((1.7, 1.3, 0.04), (0, 0.1, 0.21), P('teal'), bevel=0.02, parent=g)
    n = 6
    cs = 1.7 / n
    for i in range(n):
        for (x, y) in ((-0.85 + cs * (i + 0.5), 0.1 - 0.65 + cs * 0.4), (-0.85 + cs * (i + 0.5), 0.1 + 0.65 - cs * 0.4)):
            box((cs * 0.86, cs * 0.7, 0.03), (x, y, 0.24), P('cream' if i % 2 else 'mustard'), bevel=0.012, parent=g)
    _pawn('tomato', (-0.45, -0.3, 0.2), g, s=1.25)
    _ivory_die((0.5, -0.1, 0.52), 0.62, (0, 0, math.radians(28)), [(2, 1, 5), (1, -1, 3), (0, 1, 2)], g)
    return g


def _fennec(loc, parent, s=1.0):
    """페넥여우 말 — 큰 귀가 실루엣의 전부. 받침 원판 위 머리+몸."""
    e = group("fennec", 0, loc=loc)
    e.parent = parent
    e.scale = (s, s, s)
    FUR = mat('fennec', (0.95, 0.66, 0.34), rough=0.35, coat=0.6)
    CR = P('cream')
    cyl(0.28, 0.1, (0, 0, 0.05), P('teal', coat=1.0), bevel=0.04, parent=e)
    sph(0.22, (0, 0.02, 0.32), FUR, scale=(1, 0.95, 1.05), parent=e, seg=32)
    H = Vector((0, 0, 0.66))
    sph(0.24, H, FUR, scale=(1.08, 1, 0.95), parent=e, seg=40)
    for sd in (-1, 1):
        ear = cone(0.12, 0.01, 0.42, (sd * 0.17, 0.02, H.z + 0.3), FUR, rot=(0, math.radians(sd * 24), 0), parent=e)
        cone(0.07, 0.005, 0.3, (sd * 0.165, -0.03, H.z + 0.28), mat('earin', (1.0, 0.72, 0.7), rough=0.4, coat=0.3),
             rot=(0, math.radians(sd * 24), 0), parent=e)
        sph(0.045, (sd * 0.09, H.y - 0.2, H.z + 0.03), DARK(), scale=(1, 0.6, 1.2), parent=e, seg=16)
    sph(0.11, (0, H.y - 0.18, H.z - 0.08), CR, scale=(1.2, 1, 0.8), parent=e, seg=24)
    sph(0.035, (0, H.y - 0.28, H.z - 0.05), DARK(), parent=e, seg=12)
    return e


def yut():
    """윷놀이 — 빨간 멍석 위로 윷가락 넷이 공중에서 뒤집히는 순간 + 페넥여우 말.
    가락은 반원 단면(둥근 등 = 나무, 평평한 배 = 밝은 속살에 X 표시)."""
    g = group("yut", math.radians(-14))
    MAT_ = mat('mat', (0.80, 0.12, 0.10), rough=0.55, coat=0.2)
    cyl(1.12, 0.08, (0, 0.2, 0.04), MAT_, bevel=0.03, verts=64, parent=g)
    torus(1.1, 0.045, (0, 0.2, 0.08), GOLD(), parent=g)
    WD = mat('yutwood', (0.50, 0.24, 0.08), rough=0.3, coat=0.7)
    IN = mat('yutin', (0.97, 0.86, 0.62), rough=0.4, coat=0.4)

    def stick(loc, rot, belly_up):
        e = group("stick", 0, loc=loc)
        e.parent = g
        e.rotation_euler = rot
        Lh, r = 0.64, 0.16
        me = bpy.data.meshes.new("half")
        bm = bmesh.new()
        n = 14
        ends = []
        for x in (-Lh, Lh):
            ring = [bm.verts.new((x, math.cos(math.pi * i / n) * r, math.sin(math.pi * i / n) * r)) for i in range(n + 1)]
            ends.append(ring)
        a, b = ends
        for i in range(n):
            bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
        bm.faces.new((a[n], a[0], b[0], b[n]))
        bm.faces.new(list(reversed(a)))
        bm.faces.new(b)
        bm.normal_update()
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("half", me)
        bpy.context.collection.objects.link(o)
        _fin(o, WD, bevel=0.025, seg=3, parent=e)
        # 배(평평한 면, 로컬 -z 쪽 0) — 밝은 속살 + X 세 개
        box((Lh * 2 - 0.04, r * 2 - 0.03, 0.015), (0, 0, -0.008), IN, bevel=0.005, parent=e)
        for xm in (-0.3, 0.0, 0.3):
            for sg in (-1, 1):
                box((0.12, 0.022, 0.01), (xm, 0, -0.018), DARK(), rot=(0, 0, math.radians(45 * sg)), bevel=0.0, parent=e)
        if belly_up:
            e.rotation_euler = (rot[0] + math.pi, rot[1], rot[2])
        return e
    # 공중의 셋 + 멍석에 떨어진 하나(배가 위 = 도)
    stick((-0.55, 0.0, 1.55), (math.radians(20), math.radians(-38), math.radians(8)), True)
    stick((0.1, 0.25, 2.0), (math.radians(35), math.radians(18), math.radians(-12)), False)
    stick((0.66, -0.05, 1.3), (math.radians(-40), math.radians(-62), math.radians(20)), False)
    stick((-0.1, -0.35, 0.22), (0, 0, math.radians(-18)), True)
    _fennec((0.72, -0.5, 0.08), g, s=1.0)
    return g


def ludo():
    """루도 — 네 색 십자판(홈 네 칸·가운데 삼각형) 위 광택 말 넷 + 주사위."""
    g = group("ludo", math.radians(-18))
    WD = P('wood', rough=0.45, coat=0.4)
    S = 2.0
    box((S + 0.12, S + 0.12, 0.16), (0, 0.15, 0.08), WD, bevel=0.06, parent=g)
    box((S, S, 0.03), (0, 0.15, 0.17), P('cream', rough=0.5, coat=0.2), bevel=0.01, parent=g)
    q = S / 2
    hs = S * 0.4    # 홈 사각 한 변
    cols = [('tomato', -1, 1), ('green', 1, 1), ('mustard', 1, -1), ('cobalt', -1, -1)]
    for cn, sx, sy in cols:
        cx, cy = sx * (q - hs / 2), 0.15 + sy * (q - hs / 2)
        box((hs, hs, 0.04), (cx, cy, 0.19), P(cn), bevel=0.015, parent=g)
        box((hs * 0.62, hs * 0.62, 0.03), (cx, cy, 0.215), P('white', coat=0.4), bevel=0.012, parent=g)
    # 가운데 삼각형 넷
    c = S * 0.1
    tri = {'tomato': [(-c, -c), (-c, c), (0, 0)], 'green': [(-c, c), (c, c), (0, 0)],
           'mustard': [(c, c), (c, -c), (0, 0)], 'cobalt': [(c, -c), (-c, -c), (0, 0)]}
    for cn, pts in tri.items():
        prism(pts, 0.04, (0, 0.15, 0.2), P(cn), rot=(0, 0, 0), parent=g)
    # 홈 기둥(색 칸 줄)
    cw = S * 0.2 / 3
    for cn, (dx, dy) in (('tomato', (-1, 0)), ('green', (0, 1)), ('mustard', (1, 0)), ('cobalt', (0, -1))):
        for k in range(1, 4):
            d = c + (k - 0.5) * cw * 1.25
            box((cw * 0.9, cw * 0.9, 0.03), (dx * d, 0.15 + dy * d, 0.2), P(cn), bevel=0.008, parent=g)
    # 말 — 홈에서 하나씩 나와 판 위에
    for cn, (x, y) in (('tomato', (-0.62, 0.72)), ('green', (0.66, 0.78)), ('cobalt', (-0.55, -0.35)), ('mustard', (0.25, -0.2))):
        _pawn(cn, (x, y, 0.19), g, s=1.05)
    _ivory_die((0.95, -0.72, 0.3), 0.5, (math.radians(8), 0, math.radians(30)), [(2, 1, 6), (1, -1, 5), (0, 1, 3)], g)
    return g


def reversi():
    """리버시 — 비스듬히 세운 초록 자석판(6×6)에 흑백 돌, 앞에서 한 알이 뒤집히는 중."""
    g = group("reversi", math.radians(-12))
    b = group("board", 0, loc=(-0.08, 0.3, 0))
    b.parent = g
    b.rotation_euler = (math.radians(-24), 0, 0)
    S = 1.86
    box((S + 0.16, 0.12, S + 0.16), (0, 0, S / 2 + 0.08), P('wood', rough=0.45, coat=0.4), bevel=0.06, parent=b)
    felt = mat('felt', (0.05, 0.50, 0.25), rough=0.55, coat=0.2)
    box((S, 0.03, S), (0, -0.07, S / 2 + 0.08), felt, bevel=0.01, parent=b)
    n = 6
    cs = S / n
    line = mat('gridline', (0.02, 0.22, 0.1), rough=0.6, coat=0)
    z0 = 0.08
    for i in range(1, n):
        box((0.018, 0.01, S), (-S / 2 + i * cs, -0.087, z0 + S / 2), line, bevel=0.0, parent=b)
        box((S, 0.01, 0.018), (0, -0.087, z0 + i * cs), line, bevel=0.0, parent=b)
    BK = mat('discblack', (0.02, 0.02, 0.025), rough=0.4, coat=0.0)
    try:   # 넓은 광택이 검은 돌을 회색으로 띄운다 → 반사 세기를 낮춰 '검정'으로
        BK.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.12
    except Exception:
        pass
    WH = P('white', coat=1.0, rough=0.15)

    def disc(x, z, black_up, par, y=-0.1, rot=(math.radians(90), 0, 0)):
        top, bot = (BK, WH) if black_up else (WH, BK)
        e = group("disc", 0, loc=(x, y, z))
        e.parent = par
        e.rotation_euler = rot
        # 로컬 +z = 보이는 면 쪽이 되도록 rot 을 준다
        cyl(cs * 0.4, 0.05, (0, 0, 0.025), top, bevel=0.02, parent=e)
        cyl(cs * 0.4, 0.05, (0, 0, -0.025), bot, bevel=0.02, parent=e)
        return e
    layout = {(2, 2): 0, (2, 3): 1, (3, 2): 1, (3, 3): 1, (1, 2): 1, (2, 4): 0, (4, 3): 0, (1, 1): 0, (4, 4): 1, (3, 1): 1}
    for (c, r), wb in layout.items():
        disc(-S / 2 + (c + 0.5) * cs, z0 + (r + 0.5) * cs, wb == 1, b, y=-0.13, rot=(math.radians(90), 0, 0))
    # 뒤집히는 돌 — 판 앞 공중, 옆으로 세워져 흑·백 두 면이 다 보인다
    f = disc(0, 0, False, g, y=0, rot=(math.radians(25), math.radians(-68), 0))
    f.location = (0.98, -0.78, 0.72)
    f.scale = (1.7, 1.7, 1.7)
    return g


TOYS = {'roulette': roulette, 'car-racing': car, 'glory-racing': brawl, 'dice': dice, 'ladder': ladder,
        'bingo': bingo, 'team': team, 'retro': arcade, 'balloon': balloon,
        'lotto': lotto, 'lucky-merge': planet, 'orbit': engine, 'dodge': rocket, 'tetris': blocks,
        'starship-lander': lander, 'brick': bricks, 'snake': snake, 'pacman': ghosts, 'burger': burger, 'quiz': quiz}
# 홈 카테고리 버튼 아이콘(toy-cat-*.webp) + 보드게임 3종 (2026-09-25)
TOYS.update({'cat-random': cat_random, 'cat-draw': cat_draw, 'cat-arcade': cat_arcade, 'cat-mission': cat_mission,
             'cat-board': cat_board, 'yut': yut, 'ludo': ludo, 'reversi': reversi})


def bubble_toy():
    """버블 버스트 (2026-09-25) — 황동 천장 틀에 벌집으로 매달린 광택 버블 + 아래 장난감 대포가 쏜 초록 버블 + 터지는 별."""
    g = group("bubble", math.radians(-16))
    box((2.3, 0.72, 0.12), (0, 0.05, 0.06), P('navy'), bevel=0.05, parent=g)
    for s in (-1, 1):
        box((0.12, 0.12, 2.12), (s * 1.08, 0.12, 1.14), P('cream'), bevel=0.03, parent=g)
    box((2.34, 0.22, 0.16), (0, 0.12, 2.26), GOLD(), bevel=0.04, parent=g)
    for k in range(5):
        sph(0.035, (-0.84 + k * 0.42, 0.0, 2.26), CHROME(), parent=g, seg=12)
    R = 0.22
    RH = 2 * R * 0.866
    z1 = 2.26 - 0.08 - R
    for x, cn in ((-0.66, 'tomato'), (-0.22, 'mustard'), (0.22, 'cobalt'), (0.66, 'green')):
        sph(R, (x, 0.08, z1), P(cn, coat=0.9, rough=0.18), parent=g, seg=32)
    for x, cn in ((-0.44, 'violet'), (0.44, 'tomato')):
        sph(R, (x, 0.08, z1 - RH), P(cn, coat=0.9, rough=0.18), parent=g, seg=32)
    sph(R, (-0.66, 0.08, z1 - 2 * RH), P('cobalt', coat=0.9, rough=0.18), parent=g, seg=32)
    # 날아오르는 초록 버블 + 잔상
    sph(R, (0.12, -0.06, 1.2), P('green', coat=0.9, rough=0.18), parent=g, seg=32)
    trail = mat('trail', (1, 1, 1), emit=(0.7, 1.0, 0.8), estr=0.3, coat=0)
    for k, (x, z, r) in enumerate(((0.08, 0.93, 0.07), (0.05, 0.8, 0.05))):
        sph(r, (x, -0.06, z), trail, parent=g, seg=16)
    # 장난감 대포 — 크림 돔 + 토마토 포신 + 금 링
    sph(0.44, (0, -0.02, 0.12), P('cream'), scale=(1, 1, 0.72), parent=g, seg=40)
    cyl(0.46, 0.06, (0, -0.02, 0.15), P('cobalt'), bevel=0.02, parent=g)
    capsule((0, -0.04, 0.34), (0.03, -0.05, 0.66), 0.11, P('tomato'), parent=g)
    torus(0.12, 0.035, (0.03, -0.05, 0.68), GOLD(), parent=g)
    # 터지는 별 (오른쪽 매달린 붉은 버블 옆)
    star = mat('popstar', PAL['mustard'], emit=(1.0, 0.75, 0.2), estr=0.4, coat=0.6)
    prism(star_pts(0.2, 0.09), 0.05, (0.86, -0.1, 1.55), star, parent=g)
    return g


TOYS['bubble'] = bubble_toy


def gummy_toy():
    """구미 체인 (2026-09-25) — 크림 기둥 진열 틀에 쌓인 말랑한 젤리 큐브(같은 색끼리 쫀득하게 이어짐)
    + 위에서 떨어지는 한 쌍 + 터지는 별과 방울. 둥근 큐브·얼굴은 이 사이트 고유 캐릭터."""
    g = group("gummy", math.radians(-18))
    box((2.3, 0.8, 0.14), (0, 0.06, 0.07), P('navy'), bevel=0.06, parent=g)
    for s in (-1, 1):
        box((0.12, 0.42, 2.05), (s * 1.08, 0.08, 1.12), P('cream'), bevel=0.04, parent=g)
    box((2.3, 0.44, 0.14), (0, 0.08, 2.18), P('pink'), bevel=0.05, parent=g)
    box((2.04, 0.05, 1.98), (0, 0.3, 1.12), mat('gum_back', (0.16, 0.07, 0.26), rough=0.45, coat=0.2), bevel=0.01, parent=g)
    CS, ST = 0.3, 0.335            # 큐브 크기, 칸 간격
    COLS = {'R': 'tomato', 'G': 'green', 'B': 'cobalt', 'Y': 'mustard', 'V': 'violet'}
    jm = lambda k: mat('gum_' + k, PAL[COLS[k]], rough=0.12, coat=1.0, trans=0.18,
                       emit=PAL[COLS[k]], estr=0.12)
    D = DARK()
    W = mat('gum_eye_hi', (1, 1, 1), rough=0.1, coat=0)

    def cube(k, cx, cz, face=True, sq=1.0):
        box((CS * 1.02, CS, CS * sq), (cx, 0.02, cz), jm(k), bevel=0.1, seg=4, parent=g)
        if face:
            fy = 0.02 - CS / 2 - 0.004
            for s in (-1, 1):
                sph(0.032, (cx + s * 0.062, fy, cz + 0.02), D, scale=(0.8, 0.5, 1.15), parent=g, seg=14)
                sph(0.011, (cx + s * 0.062 + 0.01, fy - 0.012, cz + 0.035), W, parent=g, seg=10)
            sph(0.018, (cx, fy + 0.002, cz - 0.05), D, scale=(1.3, 0.5, 0.7), parent=g, seg=12)

    # 쌓인 판 (아래 행부터) — 같은 색 이웃은 '목'으로 이어 붙인다
    grid = ["RRBYVV",
            "GRBYYV",
            "GG.BY.",
            ".G...."]
    x0 = -2.5 * ST
    zb = 0.14 + CS / 2 + 0.01
    cells = {}
    for r, row in enumerate(grid):
        for c, k in enumerate(row):
            if k != '.':
                cells[(c, r)] = k
    for (c, r), k in cells.items():
        for dc, dr in ((1, 0), (0, 1)):
            if cells.get((c + dc, r + dr)) == k:
                a = (x0 + c * ST, 0.02, zb + r * ST)
                b = (x0 + (c + dc) * ST, 0.02, zb + (r + dr) * ST)
                capsule(a, b, CS * 0.33, jm(k), parent=g)
    for (c, r), k in cells.items():
        cube(k, x0 + c * ST, zb + r * ST, sq=0.9 if (c, r) == (3, 1) else 1.0)
    # 떨어지는 한 쌍
    px, pz = x0 + 2 * ST, 1.52
    cube('Y', px, pz)
    cube('V', px, pz + ST)
    # 터지는 별 + 튀는 방울
    star = mat('gum_star', PAL['mustard'], emit=(1.0, 0.75, 0.2), estr=0.4, coat=0.6)
    prism(star_pts(0.2, 0.09), 0.05, (0.72, -0.14, 1.28), star, parent=g)
    for dx, dz, k in ((0.98, 1.02, 'R'), (0.5, 1.58, 'B'), (1.0, 1.6, 'G')):
        sph(0.05, (dx, -0.12, dz), jm(k), parent=g, seg=16)
    return g


TOYS['gummy'] = gummy_toy


def _gem_mat(name, col, estr=0.22):
    """보석 — 투명(투과) + 코팅 광택 + 같은 색 약한 발광(어두운 판 위에서 색이 죽지 않게)."""
    m = mat('gem_' + name, col, rough=0.03, coat=1.0, emit=col, estr=estr, trans=0.72)
    try:
        m.node_tree.nodes["Principled BSDF"].inputs["IOR"].default_value = 1.62
    except Exception:
        pass
    return m


def _gem_cell(cx, cy, z0, r, h, m, parent, crown=0.055):
    """육각 보석 한 칸 — 옆면 6 + 크라운 면 6 + 테이블(윗면)로 깎인 면이 빛을 나눠 반사한다."""
    me = bpy.data.meshes.new("gem")
    bm = bmesh.new()
    ang = [k * math.pi / 3 for k in range(6)]
    bot = [bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z0)) for a in ang]
    top = [bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z0 + h)) for a in ang]
    ri = r * 0.5
    tab = [bm.verts.new((cx + ri * math.cos(a), cy + ri * math.sin(a), z0 + h + crown)) for a in ang]
    bm.faces.new(list(reversed(bot)))
    for k in range(6):
        j = (k + 1) % 6
        bm.faces.new((bot[k], bot[j], top[j], top[k]))
        bm.faces.new((top[k], top[j], tab[j], tab[k]))
    bm.faces.new(tab)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("gem", me)
    bpy.context.collection.objects.link(o)
    return _fin(o, m, bevel=0.005, seg=1, smooth=False, parent=parent)


def prism_hex_toy():
    """프리즘 헥스 (2026-09-25) — 흑요석 육각판(금 테) 위 깎인 보석 블록들 + 위에서 내려앉는 토파즈 5칸 + 반짝 별.
    칸은 flat-top 육각(axial q,r): x = 1.5q·s, y = √3(r+q/2)·s."""
    g = group("prism-hex", math.radians(-8))
    s = 0.2
    sq3 = math.sqrt(3)
    XY = lambda q, r: (1.5 * q * s, sq3 * (r + q / 2) * s + 0.12)
    # 판 — 금 테 + 흑요석 + 홈
    cyl(1.46, 0.12, (0, 0.12, 0.06), GOLD(), rot=(0, 0, math.radians(30)), bevel=0.03, verts=6, parent=g)
    obs = mat('obsidian', (0.05, 0.04, 0.10), rough=0.18, coat=0.9)
    cyl(1.36, 0.06, (0, 0.12, 0.14), obs, rot=(0, 0, math.radians(30)), bevel=0.012, verts=6, parent=g)
    slot = mat('slot', (0.12, 0.09, 0.22), rough=0.4, coat=0.3)
    cells = [(q, r) for q in range(-3, 4) for r in range(-3, 4) if max(abs(q), abs(r), abs(q + r)) <= 3]
    for q, r in cells:
        x, y = XY(q, r)
        cyl(s * 0.86, 0.02, (x, y, 0.178), slot, bevel=0.004, verts=6, parent=g)
    # 놓인 보석 블록
    H = 0.1
    pieces = [('ruby', (0.86, 0.06, 0.17), [(-3, 1), (-3, 2), (-2, 2), (-1, 1)]),
              ('sapph', (0.10, 0.28, 0.95), [(1, -3), (2, -3), (3, -3), (2, -2)]),
              ('emer', (0.03, 0.72, 0.42), [(0, 2), (1, 1)]),
              ('ame', (0.55, 0.22, 0.95), [(-2, -1), (-1, -2), (-1, -1)]),
              ('dia', (0.80, 0.93, 1.0), [(3, 0)])]
    for nm, col, cs in pieces:
        m = _gem_mat(nm, col, estr=0.12 if nm == 'dia' else 0.22)
        for q, r in cs:
            x, y = XY(q, r)
            _gem_cell(x, y, 0.19, s * 0.97, H, m, g)
    # 내려앉는 토파즈 5칸 — 살짝 기울어 공중에
    f = group("fall", 0, loc=(0.02, 0.0, 0.95))
    f.parent = g
    f.rotation_euler = (math.radians(22), math.radians(-10), math.radians(6))
    tz = _gem_mat('topaz', (1.0, 0.62, 0.05), estr=0.3)
    for q, r in [(-1, 0), (0, 0), (1, 0), (-2, 1), (-3, 2)]:
        x, y = 1.5 * q * s, sq3 * (r + q / 2) * s
        _gem_cell(x + 0.35, y - 0.05, 0.0, s * 0.97, H, tz, f)
    # 반짝 별(4갈래) — 흰 발광
    spark = mat('spark', (1, 1, 1), emit=(1.0, 0.95, 0.8), estr=2.2, coat=0)
    for (x, y, z, r) in ((0.95, -0.35, 1.28, 0.16), (-0.62, -0.2, 0.55, 0.1), (0.2, -0.5, 1.45, 0.07)):
        prism(star_pts(r, r * 0.22, n=4), 0.02, (x, y, z), spark, parent=g)
    return g


TOYS['prism-hex'] = prism_hex_toy
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
