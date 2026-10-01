# -*- coding: utf-8 -*-
"""버거 셰프 — 마스코트 레서판다 셰프 · 손님 3종 · 재료 7종 (2026-09-27 아케이드 임팩트 개편).

운영자: "아케이드는 손맛, 비주얼 효과, 캐릭터성, 이펙트가 어우러져 주는 임팩트가 핵심."
버거 셰프의 캔버스 손그림 재료·빈 주방을 같은 장난감 스튜디오 렌더로 바꾼다.

- 셰프 = 사이트 마스코트 레서판다(scripts/blender/mascot_panda.py 의 build_frame 을 **import 해서** 그대로 쓴다).
  몸·얼굴은 원본 그대로, 이 파일은 요리사 모자·앞치마·뒤집개만 얹는다. 원본 두 파일은 수정하지 않는다.
- 손님 = 윷놀이 말(사막여우·수달·랙돌) 흉상. yut_pieces.BUILD 를 그대로 부르고 카메라만 흉상으로 좁힌다.
- 재료 = 같은 스튜디오(코팅 플라스틱 + 잉크 외곽선)의 정사영 20° 부감. 모든 재료가 **같은 카메라·같은
  해상도**라 셀 안에서 월드 원점(재료 바닥 중심)과 1 월드 단위의 픽셀 길이가 같다 → 게임은 재료마다
  '바닥 중심에 놓고 같은 배율로 그리기'만 하면 층이 정확히 포개진다.
  두께 T 는 게임의 LAYER_H(반지름 62px 기준) 에서 역산했다: T = LAYER_H / 62 / cos(20°)

실행:
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_burger.py -- chef
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_burger.py -- guest
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_burger.py -- food
  (-- chef:idle,cheer 처럼 일부만) · MB_SAMPLES=24 로 시안
출력: scripts/og-assets/burger/{chef,guest,food}/*.png + meta.json → python scripts/build_arcade_mascots.py burger
"""
import bpy
import bmesh
import json
import math
import os
import random
import sys
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yut_pieces as yp      # noqa: E402  (모델 원본 — 수정하지 않는다)
import mascot_panda as mp    # noqa: E402  (마스코트 원본 — 수정하지 않는다)

OUT = os.path.join(HERE, "..", "og-assets", "burger")
SAMPLES = int(os.environ.get('MB_SAMPLES', '64'))


def proj(sc, p):
    v = world_to_camera_view(sc, sc.camera, Vector(p))
    return [round(v.x, 5), round(1.0 - v.y, 5)]


def xform_new(before, M):
    """before 이후 새로 생긴(부모 없는) 오브젝트를 M 으로 옮긴다."""
    bpy.context.view_layer.update()
    for o in bpy.data.objects:
        if o not in before and o.parent is None:
            o.matrix_world = M @ o.matrix_world


def noline_collection():
    if "NOLINE" not in bpy.data.collections:
        c = bpy.data.collections.new("NOLINE")
        bpy.context.scene.collection.children.link(c)
    return bpy.data.collections["NOLINE"]


def to_noline(objs):
    c = noline_collection()
    for o in objs:
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        c.objects.link(o)


# ════════════════════════ 셰프 ════════════════════════
fr = mp.fr
REST_C = ((0.34, -0.62, 0.66), (-0.34, -0.62, 0.66))        # 조리대 위에 얹은 두 손
CHEF = {
    'idle':   fr('n', REST_C),
    'blink':  fr('b', REST_C),
    'placeA': fr('h', ((-0.02, -0.9, 0.98), (-0.66, -0.62, 0.98)), roll=-0.08, hroll=-0.08, fwd=0.08),
    'placeB': fr('x', ((0.12, -0.92, 0.8), (-0.56, -0.72, 0.84)), roll=-0.05, hroll=-0.1, fwd=0.1),
    'flip':   fr('h', ((0.62, -0.42, 1.42), (-0.52, -0.3, 0.55)), roll=0.06, hroll=0.06, tail=0.5),
    'cheer':  fr('x', ((1.06, -0.3, 1.62), (-1.06, -0.3, 1.62)), hfwd=-0.08),
    'serve':  fr('w', ((0.5, -0.3, 0.52), (-1.02, -0.42, 1.08)), roll=-0.07, hroll=-0.08),
    'panic':  fr('v', ((0.64, -0.5, 1.2), (-0.64, -0.5, 1.2)), droop=0.45, fwd=0.04),
    'oops':   fr('o', ((0.6, -0.5, 0.86), (-0.6, -0.5, 0.86)), droop=0.2, hfwd=-0.04),
    'sad':    fr('s', mp.CHIN, droop=0.6, hfwd=0.06),
    'cry':    fr('c', mp.CHIN, droop=1.0, hfwd=0.08),
    'wave':   fr('h', ((0.86, -0.4, 1.1), (-0.34, -0.62, 0.66)), tail=0.55, hroll=0.06),
}
CHEF_ORDER = ['idle', 'blink', 'placeA', 'placeB', 'flip', 'cheer', 'serve', 'panic', 'oops', 'sad', 'cry', 'wave']


def chef_hat(ZMH):
    """요리사 모자 — 머리 좌표(기울기 전)로 짓고 머리 변환을 얹는다. 귀는 모자 양옆으로 삐져나온다."""
    before = set(bpy.data.objects)
    white = yp.mat('chef_hat', (0.97, 0.97, 0.95), rough=0.55, coat=0.25, sheen=0.3)
    red = yp.mat('chef_band', (0.88, 0.10, 0.12), rough=0.3, coat=0.8)
    yp.cyl(0.42, 0.36, (0, 0.04, 2.16), white, bevel=0.05)
    band = yp.torus(0.425, 0.035, (0, 0.04, 2.1), red)
    for i in range(6):
        a = i / 6 * math.tau + 0.3
        yp.sph(0.25, (0.22 * math.cos(a), 0.04 + 0.2 * math.sin(a), 2.5), white)
    yp.sph(0.3, (0, 0.04, 2.62), white)
    to_noline([band])
    tilt = Matrix.Translation((0, 0, 2.1)) @ Matrix.Rotation(-0.13, 4, 'Y') @ Matrix.Translation((0, 0, -2.1))
    xform_new(before, ZMH @ tilt)


def chef_apron(ZM):
    before = set(bpy.data.objects)
    white = yp.mat('apron', (0.98, 0.97, 0.94), rough=0.5, coat=0.2)
    red = yp.mat('chef_band', (0.88, 0.10, 0.12), rough=0.3, coat=0.8)
    yp.sph(0.33, (0, -0.24, 0.5), white, scale=(1.05, 0.42, 1.0))
    yp.sph(0.06, (0, -0.39, 0.62), red, scale=(1.2, 0.5, 0.9))    # 가슴 단추 한 알
    xform_new(before, ZM)


def spatula(hand):
    wood = yp.mat('sp_wood', (0.45, 0.22, 0.08), rough=0.4, coat=0.5)
    steel = yp.mat('sp_steel', (0.82, 0.85, 0.9), rough=0.2, metal=0.5, coat=0.6)
    h = Vector(hand)
    yp.capsule(h + Vector((-0.06, 0.0, -0.1)), h + Vector((0.3, -0.06, 0.42)), 0.045, wood)
    bpy.ops.mesh.primitive_cube_add(size=1, location=h + Vector((0.46, -0.08, 0.66)))
    b = bpy.context.object
    b.scale = (0.3, 0.035, 0.26)
    b.rotation_euler = (0, math.radians(-30), 0)
    yp._fin(b, steel, bevel=0.03)


def render_chef(name):
    mp.ORTHO = 3.2
    mp.CAM_TGT = Vector((0.0, 0.0, 1.46))
    mp.YAW = -0.3                 # 화면 왼쪽(버거)으로 몸을 튼다
    mp.RES = 512
    mp.SAMPLES = SAMPLES
    mp.FRAMES['chef_' + name] = CHEF[name]
    sc = mp.studio()
    spec, ZM, Hm, _ = mp.build_frame('chef_' + name)
    chef_hat(ZM @ Hm)
    chef_apron(ZM)
    if name == 'flip':
        spatula(ZM @ Vector(spec['R']))
    d = os.path.join(OUT, "chef")
    os.makedirs(d, exist_ok=True)
    sc.render.filepath = os.path.join(d, name + ".png")
    bpy.ops.render.render(write_still=True)
    head_c = ZM @ (Hm @ Vector(yp.HEAD_C))
    meta = dict(head=proj(sc, head_c), headR=round(yp.HA / mp.ORTHO, 5),
                waist=proj(sc, ZM @ Vector((0, -0.3, 0.62))),
                R=proj(sc, ZM @ Vector(spec['R'])), L=proj(sc, ZM @ Vector(spec['L'])))
    print("RENDERED chef", name)
    return meta


# ════════════════════════ 손님 ════════════════════════
GUEST_SP = ['fox', 'otter', 'cat']
GUEST_EX = ['n', 'b', 'h', 'x', 's', 'o']


def render_guest(sp, ex):
    yp.RES = 384
    yp.SAMPLES = max(24, int(SAMPLES * 0.75))
    sc = yp.studio()
    sc.render.resolution_x = sc.render.resolution_y = 384
    th = 2.2 * 384 / 560 * 1.15
    sc.render.line_thickness = th
    bpy.context.view_layer.freestyle_settings.linesets[0].linestyle.thickness = th
    yp.BUILD[sp](ex)
    cam = sc.camera
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 2.75
    d = Vector((0.0, -9.2, 3.2)).normalized()
    tgt = Vector((0.0, 0.0, 1.62))
    cam.location = tgt + d * 14.0
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
    cam.data.clip_end = 60
    dd = os.path.join(OUT, "guest")
    os.makedirs(dd, exist_ok=True)
    sc.render.filepath = os.path.join(dd, "%s-%s.png" % (sp, ex))
    bpy.ops.render.render(write_still=True)
    print("RENDERED guest", sp, ex)
    return dict(head=proj(sc, yp.HEAD_C), headR=round(yp.HA / 2.75, 5), neck=proj(sc, (0, -0.3, 0.8)))


# ════════════════════════ 재료 ════════════════════════
ELEV = math.radians(20)
R_PX = 62.0                       # 게임의 버거 반지름(px) — LAYER_H 와 짝


def T_of(layer_h):
    return layer_h / R_PX / math.cos(ELEV)


FOOD = ['bunBottom', 'bunTop', 'patty', 'cheese', 'lettuce', 'tomato', 'onion']
LAYER_H = dict(bunBottom=16, bunTop=26, patty=22, cheese=12, lettuce=16, tomato=10, onion=8)


def ramp_mat(name, lo, hi, rough=0.35, coat=0.6):
    """법선 z 로 색이 바뀌는 재질 — 빵 윗면은 짙게 구워지고 옆은 밝다"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    try:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.1
    except Exception:
        pass
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].position = 0.25
    cr.color_ramp.elements[0].color = (*lo, 1)
    cr.color_ramp.elements[1].position = 0.95
    cr.color_ramp.elements[1].color = (*hi, 1)
    nt.links.new(geo.outputs['Normal'], sep.inputs[0])
    nt.links.new(sep.outputs['Z'], cr.inputs[0])
    nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    return m


def half_ellipsoid(r, h, z0, m, upper=True, seg=64):
    """위(또는 아래) 반쪽 타원체 — 자른 면은 z0"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=seg, ring_count=seg // 2, location=(0, 0, 0))
    o = bpy.context.object
    bm = bmesh.new()
    bm.from_mesh(o.data)
    kill = [v for v in bm.verts if (v.co.z < -1e-4 if upper else v.co.z > 1e-4)]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    o.scale = (r, r, h)
    o.location = (0, 0, z0)
    return yp._fin(o, m)


def polar_sheet(R, rings, segs, zf, m, thick=0.04):
    bm = bmesh.new()
    center = bm.verts.new((0, 0, zf(0.0, 0.0)))
    grid = []
    for i in range(1, rings + 1):
        r = R * i / rings
        row = []
        for j in range(segs):
            th = j / segs * math.tau
            row.append(bm.verts.new((r * math.cos(th), r * math.sin(th), zf(r, th))))
        grid.append(row)
    for j in range(segs):
        bm.faces.new((center, grid[0][j], grid[0][(j + 1) % segs]))
    for i in range(rings - 1):
        for j in range(segs):
            a, b = grid[i][j], grid[i][(j + 1) % segs]
            c, d = grid[i + 1][(j + 1) % segs], grid[i + 1][j]
            bm.faces.new((a, d, c, b))
    me = bpy.data.meshes.new("sheet")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("sheet", me)
    bpy.context.collection.objects.link(o)
    md = o.modifiers.new("sol", 'SOLIDIFY')
    md.thickness = thick
    md.offset = -1
    return yp._fin(o, m)


def f_bunBottom():
    T = T_of(16)
    crust = ramp_mat('bun_heel', (0.62, 0.3, 0.08), (0.9, 0.62, 0.3), rough=0.38, coat=0.5)
    half_ellipsoid(1.0, T, T, crust, upper=False)
    crumb = yp.mat('crumb', (0.93, 0.66, 0.34), rough=0.6, coat=0.15)
    yp.cyl(0.95, 0.012, (0, 0, T + 0.004), crumb, bevel=0.0)
    return T


def f_bunTop():
    H = 0.66
    crust = ramp_mat('bun_crown', (0.93, 0.62, 0.26), (0.62, 0.27, 0.06), rough=0.3, coat=0.75)
    half_ellipsoid(1.0, H, 0.0, crust, upper=True)
    seed = yp.mat('sesame', (0.99, 0.93, 0.74), rough=0.3, coat=0.6)
    rnd = random.Random(7)
    objs = []
    for k in range(17):
        th = math.radians(12 + 58 * math.sqrt(rnd.random()))
        ph = rnd.random() * math.tau
        p = Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), H * math.cos(th)))
        n = Vector((p.x, p.y, p.z / (H * H))).normalized()
        q = Vector((0, 0, 1)).rotation_difference(n) @ Matrix.Rotation(rnd.random() * math.tau, 3, 'Z').to_quaternion()
        o = yp.sph(0.055, p + n * 0.01, seed, scale=(1.7, 0.85, 0.5), seg=16, rot=q)
        objs.append(o)
    to_noline(objs)
    return 0.0


def f_patty():
    T = T_of(22)
    meat = bpy.data.materials.new('patty')
    meat.use_nodes = True
    nt = meat.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = 0.4
    try:
        bs.inputs["Coat Weight"].default_value = 0.5
        bs.inputs["Coat Roughness"].default_value = 0.12
    except Exception:
        pass
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 14.0
    nz.inputs['Detail'].default_value = 6.0
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].position = 0.35
    cr.color_ramp.elements[0].color = (0.07, 0.025, 0.01, 1)
    cr.color_ramp.elements[1].position = 0.7
    cr.color_ramp.elements[1].color = (0.36, 0.14, 0.05, 1)
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.55
    nt.links.new(nz.outputs['Fac'], cr.inputs[0])
    nt.links.new(cr.outputs['Color'], bs.inputs['Base Color'])
    nt.links.new(nz.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bs.inputs['Normal'])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=96, ring_count=48, location=(0, 0, T / 2))
    o = bpy.context.object
    o.scale = (1.03, 1.03, T / 2 * 1.02)
    tex = bpy.data.textures.new('meat', 'CLOUDS')
    tex.noise_scale = 0.12
    md = o.modifiers.new('bumps', 'DISPLACE')
    md.texture = tex
    md.strength = 0.05
    md.mid_level = 0.5
    yp._fin(o, meat)
    return T


def f_cheese():
    T = T_of(12)
    cheese = yp.mat('cheese', (1.0, 0.64, 0.06), rough=0.22, coat=0.9)
    try:
        b = cheese.node_tree.nodes["Principled BSDF"]
        b.inputs["Subsurface Weight"].default_value = 0.15
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.6, 0.2)
    except Exception:
        pass
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=36, y_subdivisions=36, size=1.84, location=(0, 0, 0))
    o = bpy.context.object
    for v in o.data.vertices:
        x, y = v.co.x, v.co.y
        # 45° 돌린 정사각 — 모서리가 앞·뒤·좌·우로 흘러내린다
        rx, ry = (x - y) / math.sqrt(2), (x + y) / math.sqrt(2)
        d = math.hypot(rx, ry)
        droop = 2.1 * max(0.0, d - 0.86) ** 2 + 0.03 * math.sin(rx * 7) * max(0.0, d - 0.7)
        v.co = Vector((rx, ry, T - droop))
    md = o.modifiers.new("sol", 'SOLIDIFY')
    md.thickness = 0.075
    md.offset = -1
    sub = o.modifiers.new("sub", 'SUBSURF')
    sub.levels = 1
    sub.render_levels = 1
    return yp._fin(o, cheese) and T


def f_lettuce():
    T = T_of(16)
    g1 = yp.mat('lettuce', (0.28, 0.66, 0.1), rough=0.3, coat=0.7)
    g2 = yp.mat('lettuce_hi', (0.52, 0.86, 0.22), rough=0.3, coat=0.7)
    R = 1.14

    def zf1(r, th):
        u = r / R
        return T * 0.78 * (1 - u * u) ** 0.6 + 0.085 * u ** 2.5 * math.sin(11 * th + 1.7 * math.sin(3 * th)) - 0.1 * u ** 4
    polar_sheet(R, 16, 132, zf1, g1, thick=0.05)

    def zf2(r, th):
        u = r / (R * 0.9)
        return T * 0.95 * (1 - min(1, u) ** 2) ** 0.5 + 0.07 * u ** 2.5 * math.sin(9 * th + 0.8) - 0.06 * u ** 4 + 0.02
    s = polar_sheet(R * 0.9, 14, 110, zf2, g2, thick=0.045)
    s.rotation_euler = (0, 0, 0.5)
    return T


def f_tomato():
    T = T_of(10)
    skin = yp.mat('tom_skin', (0.78, 0.05, 0.03), rough=0.18, coat=1.0)
    pulp = yp.mat('tom_pulp', (0.95, 0.24, 0.16), rough=0.25, coat=1.0)
    gel = yp.mat('tom_gel', (1.0, 0.62, 0.3), rough=0.1, coat=1.0)
    core = yp.mat('tom_core', (1.0, 0.5, 0.42), rough=0.3, coat=0.8)
    yp.cyl(0.92, T, (0, 0, T / 2), skin, bevel=0.04, verts=96)
    yp.cyl(0.84, 0.01, (0, 0, T + 0.002), pulp, bevel=0.0, verts=96)
    objs = []
    for k in range(5):
        a = k / 5 * math.tau + 0.2
        p = (0.47 * math.cos(a), 0.47 * math.sin(a), T + 0.012)
        o = yp.sph(0.2, p, gel, scale=(1.0, 0.72, 0.08), seg=24)
        o.rotation_euler = (0, 0, a)
        objs.append(o)
        for s in (-1, 1):
            q = (0.5 * math.cos(a + s * 0.12), 0.5 * math.sin(a + s * 0.12), T + 0.022)
            objs.append(yp.sph(0.04, q, yp.mat('tom_seed', (1.0, 0.9, 0.55), rough=0.3), scale=(1.4, 0.8, 0.5), seg=10))
    objs.append(yp.sph(0.16, (0, 0, T + 0.01), core, scale=(1, 1, 0.08), seg=24))
    to_noline(objs)
    return T


def f_onion():
    T = T_of(8)
    on = yp.mat('onion', (0.94, 0.82, 0.95), rough=0.2, coat=0.9)
    on2 = yp.mat('onion_in', (0.99, 0.95, 0.98), rough=0.25, coat=0.9)
    for R, r, m in ((0.8, 0.085, on), (0.56, 0.075, on2), (0.32, 0.065, on)):
        yp.torus(R, r, (0, 0, T / 2), m, scale=(1, 1, T / 2 / r))
    return T


FOOD_FN = dict(bunBottom=f_bunBottom, bunTop=f_bunTop, patty=f_patty, cheese=f_cheese,
               lettuce=f_lettuce, tomato=f_tomato, onion=f_onion)
FOOD_W, FOOD_H = 512, 320
FOOD_ORTHO = 2.9


def food_studio():
    yp.SAMPLES = SAMPLES
    sc = yp.studio()
    sc.render.resolution_x = FOOD_W
    sc.render.resolution_y = FOOD_H
    th = 2.4
    sc.render.line_thickness = th
    bpy.context.view_layer.freestyle_settings.linesets[0].linestyle.thickness = th
    cam = sc.camera
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = FOOD_ORTHO
    d = Vector((0.0, -math.cos(ELEV), math.sin(ELEV)))
    tgt = Vector((0.0, 0.0, 0.02))
    cam.location = tgt + d * 14.0
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
    cam.data.clip_end = 60
    return sc


def render_food(name):
    sc = food_studio()
    T = FOOD_FN[name]()
    dd = os.path.join(OUT, "food")
    os.makedirs(dd, exist_ok=True)
    sc.render.filepath = os.path.join(dd, name + ".png")
    bpy.ops.render.render(write_still=True)
    o = proj(sc, (0, 0, 0))
    u = proj(sc, (1, 0, 0))
    t = proj(sc, (0, 0, T or 0.0))
    print("RENDERED food", name)
    return dict(o=o, ux=round(u[0] - o[0], 5), top=t)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    what = argv[0] if argv else 'chef'
    kind, _, only = what.partition(':')
    mpath = os.path.join(OUT, kind, "meta.json")
    os.makedirs(os.path.dirname(mpath), exist_ok=True)
    meta = {}
    if os.path.exists(mpath):
        with open(mpath, encoding='utf-8') as f:
            meta = json.load(f)
    if kind == 'chef':
        for n in (only.split(',') if only else CHEF_ORDER):
            meta[n] = render_chef(n)
            with open(mpath, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=1)
    elif kind == 'guest':
        jobs = [(s, e) for s in GUEST_SP for e in GUEST_EX]
        if only:
            jobs = [tuple(j.split('-')) for j in only.split(',')]
        for s, e in jobs:
            meta['%s-%s' % (s, e)] = render_guest(s, e)
            with open(mpath, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=1)
    elif kind == 'food':
        for n in (only.split(',') if only else FOOD):
            meta[n] = render_food(n)
            with open(mpath, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=1)
