# -*- coding: utf-8 -*-
"""델타-브이 연구시설 — 1인칭 노드 시점 프리렌더 (2026-08-22).

운영자 요청: 연구실을 1인칭으로 돌아다니며 실험하고 **단서와 수식을 찾는**
미션을 정교하게.

**왜 프리렌더 노드 방식인가** (실시간 3D 가 아니라):
  · Cycles 로 패스트레이싱한 정지 화면이 스크립트로 짠 실시간 씬보다
    비교가 안 되게 좋다. 이 프로젝트에서 품질은 렌더에서 나온다
  · 폰에서 무겁지 않다 — 이미지 몇 장이다
  · 구도를 완전히 통제할 수 있다
  · 단서를 찾는 장르(Myst·Obra Dinn 계열)의 표준 문법이 원래 이것이다

**텍스트는 Blender 에 넣지 않는다.** 화이트보드·표지판은 빈 판으로 렌더하고
글자는 HTML 로 그 위에 올린다 — 선명하고, 번역 가능하고, 폰트 싸움이 없다.

노드 구성 (CH.1 추진제):
  hall   복도 — 세 방으로 가는 문
  prop   추진 연구동 — 화이트보드(치올콥스키 수식) · 엔진 시험대
  store  자재 창고 — 추진제 3종 탱크 · 물성표
  dock   운송 부두 — 트레일러. 단 길이 상한 9m 의 출처

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P deltav_lab.py
출력: scripts/og-assets/deltav/node_*.png
"""
import bpy
import math
import os
import json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "..", "og-assets", "deltav")
os.makedirs(DIR, exist_ok=True)

W, H = 960, 640          # 4:3 에 가까운 1인칭 프레임
SAMPLES = 300


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'CUDA'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.film_transparent = False
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = 0.0
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    bgn = w.node_tree.nodes["Background"]
    bgn.inputs[0].default_value = (0.02, 0.025, 0.035, 1)
    bgn.inputs[1].default_value = 0.35
    sc.world = w
    return sc


def mat(name, base, rough=0.5, metal=0.0, emit=None, emit_str=0.0, rough_var=0.0,
        noise_scale=40.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    if rough_var > 0:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = noise_scale
        tex.inputs["Detail"].default_value = 5.0
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.35
        mr.inputs["From Max"].default_value = 0.65
        mr.inputs["To Min"].default_value = max(0.03, rough - rough_var)
        mr.inputs["To Max"].default_value = min(1.0, rough + rough_var)
        nt.links.new(tex.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.05
        nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def box(loc, scale, m, rot=(0, 0, 0), bev=0.012):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.scale = scale
    o.rotation_euler = rot
    o.data.materials.append(m)
    if bev:
        md = o.modifiers.new("b", 'BEVEL')
        md.width = bev
        md.segments = 2
        md.limit_method = 'ANGLE'
        md.angle_limit = math.radians(40)
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def cyl(loc, r, d, m, rot=(0, 0, 0), verts=40):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, vertices=verts, location=loc)
    o = bpy.context.object
    o.rotation_euler = rot
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def eye(loc, look, lens=24):
    """1인칭 시점. 넓은 화각이 방을 방처럼 보이게 한다."""
    bpy.ops.object.camera_add(location=loc)
    c = bpy.context.object
    c.data.lens = lens
    d = Vector(look) - Vector(loc)
    c.rotation_mode = 'QUATERNION'
    c.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    bpy.context.scene.camera = c
    return c


def panel_light(loc, size, power, color=(1, 0.97, 0.92), rot=(0, 0, 0)):
    """천장 패널등 — 실내는 광원이 보여야 실내로 보인다."""
    bpy.ops.object.light_add(type='AREA', location=loc)
    L = bpy.context.object
    L.data.shape = 'RECTANGLE'
    L.data.size = size[0]
    L.data.size_y = size[1]
    L.data.energy = power
    L.data.color = color
    L.rotation_euler = rot
    return L


def room(w, d, h, mw, mf, mc):
    """방 껍데기 — 바닥·천장·벽 네 장."""
    box((0, 0, -0.05), (w, d, 0.1), mf, bev=0)
    box((0, 0, h + 0.05), (w, d, 0.1), mc, bev=0)
    box((0, d / 2 + 0.05, h / 2), (w, 0.1, h), mw, bev=0)
    box((0, -d / 2 - 0.05, h / 2), (w, 0.1, h), mw, bev=0)
    box((-w / 2 - 0.05, 0, h / 2), (0.1, d, h), mw, bev=0)
    box((w / 2 + 0.05, 0, h / 2), (0.1, d, h), mw, bev=0)


HOT = {}          # {노드: {핫스팟이름: [x, y, w, h]}}  — 전부 % 단위


def mark(node, name, obj, pad=0.0):
    """오브젝트의 화면상 사각형을 카메라 투영으로 계산해 기록한다.

    눈대중으로 찍으면 카메라를 조금만 고쳐도 전부 어긋난다. 렌더와 좌표가
    같은 원본에서 나와야 한다.
    """
    sc = bpy.context.scene
    cam = sc.camera
    dg = bpy.context.evaluated_depsgraph_get()
    ob = obj.evaluated_get(dg)
    xs, ys = [], []
    for c in ob.bound_box:
        w = ob.matrix_world @ Vector(c)
        v = world_to_camera_view(sc, cam, w)
        if v.z <= 0:
            continue          # 카메라 뒤쪽 꼭짓점은 버린다
        xs.append(v.x)
        ys.append(1.0 - v.y)  # 화면 y 는 아래로 증가
    if not xs:
        return
    x0, x1 = max(0.0, min(xs) - pad), min(1.0, max(xs) + pad)
    y0, y1 = max(0.0, min(ys) - pad), min(1.0, max(ys) + pad)
    HOT.setdefault(node, {})[name] = [round(x0 * 100, 2), round(y0 * 100, 2),
                                      round((x1 - x0) * 100, 2), round((y1 - y0) * 100, 2)]


def render(name):
    bpy.context.scene.render.filepath = os.path.join(DIR, name)
    bpy.ops.render.render(write_still=True)
    print("  rendered", name)


# ──────────────────────────── 복도 ────────────────────────────
def n_hall():
    """복도 — 세 방으로 가는 문. 캠페인의 교차로."""
    reset()
    WALL = mat("w", (0.30, 0.315, 0.34), rough=0.72, rough_var=0.10, noise_scale=18)
    FLOOR = mat("f", (0.10, 0.105, 0.12), rough=0.28, rough_var=0.10, noise_scale=26)
    CEIL = mat("c", (0.16, 0.17, 0.19), rough=0.80)
    DOOR = mat("d", (0.13, 0.16, 0.20), rough=0.42, metal=0.5, rough_var=0.08)
    TRIM = mat("t", (0.55, 0.57, 0.60), rough=0.35, metal=0.8)
    LAMP = mat("l", (1, 1, 1), rough=0.4, emit=(1.0, 0.96, 0.90), emit_str=5.0)
    SIGN = mat("s", (0.86, 0.87, 0.88), rough=0.55)

    room(6.0, 16.0, 3.2, WALL, FLOOR, CEIL)
    # 천장 조명 줄
    for y in (-5.0, -1.0, 3.0, 7.0):
        box((0, y, 3.14), (1.6, 0.28, 0.06), LAMP, bev=0)
        panel_light((0, y, 3.02), (1.7, 0.4), 55)
    # 문 3개 — 왼쪽 둘, 오른쪽 하나
    doors = []
    for (x, y, key) in ((-3.0, -2.0, 'prop'), (-3.0, 4.0, 'store'), (3.0, 1.0, 'dock')):
        d = box((x, y, 1.15), (0.08, 1.5, 2.3), DOOR, rot=(0, 0, 0))
        box((x + (0.12 if x < 0 else -0.12), y, 1.15), (0.03, 1.62, 2.42), TRIM, rot=(0, 0, 0))
        # 문 위 표지판 — 글자는 HTML 로 올린다
        sg = box((x + (0.12 if x < 0 else -0.12), y, 2.62), (0.03, 0.95, 0.30), SIGN)
        doors.append((key, d, sg))
    # 복도 끝 큰 창(밖은 어둡다)
    box((0, 8.0, 1.8), (3.4, 0.04, 1.9), mat("g", (0.02, 0.03, 0.05), rough=0.08, metal=0.1))
    eye((0, -6.6, 1.62), (0, 2.0, 1.55), lens=22)
    bpy.context.view_layer.update()
    for key, d, sg in doors:
        mark('hall', 'door_' + key, d)
        mark('hall', 'sign_' + key, sg)
    render("node_hall.png")


# ─────────────────────── 추진 연구동 ───────────────────────
def n_prop():
    """추진 연구동 — 화이트보드(수식이 적힐 자리)와 엔진 시험대."""
    reset()
    WALL = mat("w", (0.28, 0.30, 0.33), rough=0.74, rough_var=0.10, noise_scale=16)
    FLOOR = mat("f", (0.095, 0.10, 0.115), rough=0.30, rough_var=0.10, noise_scale=24)
    CEIL = mat("c", (0.15, 0.16, 0.18), rough=0.80)
    BOARD = mat("b", (0.90, 0.905, 0.91), rough=0.22, rough_var=0.04, noise_scale=90)
    FRAME = mat("fr", (0.50, 0.52, 0.55), rough=0.32, metal=0.85)
    STEEL = mat("s", (0.58, 0.60, 0.63), rough=0.28, metal=1.0, rough_var=0.10, noise_scale=90)
    DARK = mat("dk", (0.07, 0.075, 0.09), rough=0.50, metal=0.4)
    COPPER = mat("cu", (0.72, 0.36, 0.18), rough=0.26, metal=1.0, rough_var=0.08)
    LAMP = mat("l", (1, 1, 1), rough=0.4, emit=(1.0, 0.96, 0.90), emit_str=5.0)
    SCREEN = mat("sc", (0.05, 0.08, 0.10), rough=0.14,
                 emit=(0.10, 0.55, 0.62), emit_str=1.4)

    room(9.0, 11.0, 3.4, WALL, FLOOR, CEIL)
    for y in (-3.0, 0.5, 4.0):
        box((0, y, 3.34), (2.4, 0.26, 0.06), LAMP, bev=0)
        panel_light((0, y, 3.22), (2.5, 0.4), 70)

    # 화이트보드 — 이 게임에서 가장 중요한 물건. 수식이 여기 적힌다
    board = box((-4.36, 0.6, 1.85), (0.06, 3.4, 1.7), BOARD)
    box((-4.30, 0.6, 1.85), (0.02, 3.56, 1.86), FRAME)
    box((-4.28, -0.9, 0.94), (0.05, 0.5, 0.05), FRAME)   # 마커 받침

    # 엔진 시험대 — 노즈콘 아래로 향한 종형 노즐
    base = box((2.2, 1.2, 0.35), (2.6, 2.6, 0.7), DARK)
    cyl((2.2, 1.2, 1.55), 0.42, 1.5, STEEL)
    bpy.ops.mesh.primitive_cone_add(radius1=0.86, radius2=0.40, depth=1.1, vertices=48,
                                    location=(2.2, 1.2, 2.75))
    noz = bpy.context.object
    noz.rotation_euler = (math.radians(180), 0, 0)
    noz.data.materials.append(COPPER)
    for p in noz.data.polygons:
        p.use_smooth = True
    # 배관
    for a in range(6):
        ang = math.pi * 2 * a / 6
        cyl((2.2 + math.cos(ang) * 0.62, 1.2 + math.sin(ang) * 0.62, 1.9),
            0.055, 1.9, STEEL)

    # 계측 콘솔
    box((3.0, -2.6, 0.45), (2.0, 0.9, 0.9), DARK)
    screen = box((3.0, -2.95, 1.25), (1.8, 0.10, 0.72), SCREEN, rot=(math.radians(-12), 0, 0))

    # 1차 실패: 시선이 왼쪽에 쏠려 엔진 시험대가 프레임 밖으로 잘렸다.
    eye((0.2, -4.6, 1.62), (-0.9, 1.1, 1.80), lens=18)
    bpy.context.view_layer.update()
    mark('prop', 'board', board)
    mark('prop', 'engine', noz, pad=0.02)
    mark('prop', 'console', screen)
    render("node_prop.png")


# ─────────────────────── 자재 창고 ───────────────────────
def n_store():
    """자재 창고 — 추진제 탱크 3기. 물성표가 붙어 있다."""
    reset()
    WALL = mat("w", (0.24, 0.255, 0.28), rough=0.78, rough_var=0.10, noise_scale=14)
    FLOOR = mat("f", (0.085, 0.09, 0.10), rough=0.34, rough_var=0.10, noise_scale=22)
    CEIL = mat("c", (0.13, 0.14, 0.16), rough=0.82)
    LAMP = mat("l", (1, 1, 1), rough=0.4, emit=(1.0, 0.95, 0.88), emit_str=4.4)
    RACK = mat("r", (0.30, 0.20, 0.10), rough=0.55, metal=0.7, rough_var=0.10)
    CARD = mat("cd", (0.88, 0.87, 0.84), rough=0.62)
    TANKS = [mat("t0", (0.60, 0.50, 0.30), rough=0.34, metal=0.9, rough_var=0.08),
             mat("t1", (0.55, 0.62, 0.68), rough=0.26, metal=1.0, rough_var=0.07),
             mat("t2", (0.72, 0.74, 0.80), rough=0.16, metal=1.0, rough_var=0.05)]

    room(11.0, 9.0, 4.2, WALL, FLOOR, CEIL)
    for x in (-3.0, 0.5, 4.0):
        box((x, 0, 4.14), (0.30, 3.0, 0.06), LAMP, bev=0)
        panel_light((x, 0, 4.02), (0.4, 3.2), 80)

    # 탱크 3기 — 지름이 다르다. 같은 질량을 담는 데 필요한 부피가 다르다는 뜻
    cards = []
    for i, (x, rr, hh) in enumerate(((-3.0, 0.52, 2.0), (0.4, 0.62, 2.3), (4.2, 0.98, 3.0))):
        cyl((x, 1.0, hh / 2 + 0.25), rr, hh, TANKS[i])
        bpy.ops.mesh.primitive_uv_sphere_add(radius=rr, segments=40, ring_count=20,
                                             location=(x, 1.0, hh + 0.25))
        cap = bpy.context.object
        cap.scale = (1, 1, 0.45)
        cap.data.materials.append(TANKS[i])
        for p in cap.data.polygons:
            p.use_smooth = True
        # 받침대
        box((x, 1.0, 0.12), (rr * 2.3, rr * 2.3, 0.24), RACK)
        # 물성 카드 — 글자는 HTML 로
        cards.append(box((x, 0.30, 1.35), (0.72, 0.03, 0.48), CARD,
                         rot=(math.radians(-8), 0, 0)))

    # 선반
    for z in (0.9, 1.9, 2.9):
        box((0, -3.6, z), (9.0, 0.7, 0.08), RACK)
    for x in (-4.2, -1.4, 1.4, 4.2):
        box((x, -3.6, 1.7), (0.10, 0.72, 3.4), RACK)

    # 1차 실패: y=-4.9 는 뒷벽(-4.55) 바깥이라 화면이 통째로 검었다.
    eye((-0.6, -3.85, 1.62), (0.6, 1.0, 1.45), lens=20)
    bpy.context.view_layer.update()
    for i, key in enumerate(('rp1', 'ch4', 'lh2')):
        mark('store', 'card_' + key, cards[i], pad=0.006)
    render("node_store.png")


# ─────────────────────── 운송 부두 ───────────────────────
def n_dock():
    """운송 부두 — 트레일러. 단 길이 상한 9m 가 여기서 나온다."""
    reset()
    WALL = mat("w", (0.20, 0.215, 0.24), rough=0.80, rough_var=0.10, noise_scale=12)
    FLOOR = mat("f", (0.10, 0.10, 0.11), rough=0.40, rough_var=0.12, noise_scale=18)
    CEIL = mat("c", (0.11, 0.12, 0.14), rough=0.85)
    LAMP = mat("l", (1, 1, 1), rough=0.4, emit=(1.0, 0.93, 0.84), emit_str=4.0)
    DECK = mat("dk", (0.16, 0.17, 0.19), rough=0.52, metal=0.5, rough_var=0.10)
    RUB = mat("ru", (0.045, 0.045, 0.05), rough=0.88)
    PAINT = mat("p", (0.72, 0.52, 0.10), rough=0.55)
    SIGN = mat("s", (0.86, 0.87, 0.88), rough=0.55)
    SHELL = mat("sh", (0.80, 0.82, 0.85), rough=0.22, metal=1.0, rough_var=0.06, noise_scale=140)

    room(14.0, 12.0, 5.0, WALL, FLOOR, CEIL)
    for y in (-3.0, 2.0):
        box((0, y, 4.94), (5.0, 0.30, 0.06), LAMP, bev=0)
        panel_light((0, y, 4.82), (5.2, 0.4), 120)

    # 트레일러 — 적재면
    box((0, 1.6, 0.98), (9.4, 2.6, 0.36), DECK)
    for x in (-3.6, -2.4, 2.4, 3.6):
        for sy in (-1, 1):
            cyl((x, 1.6 + sy * 1.15, 0.52), 0.52, 0.42, RUB, rot=(math.radians(90), 0, 0))
    # 적재된 단 — 딱 맞게 들어간다
    # 1차 실패: 반지름 1.85 원통이 프레임을 가득 채워 관 속처럼 보였다.
    cyl((0, 1.6, 1.92), 1.15, 8.4, SHELL, rot=(0, math.radians(90), 0), verts=56)
    # 바닥의 적재 한계선
    limits = [box((x, 1.6, 0.02), (0.10, 3.4, 0.02), PAINT, bev=0) for x in (-4.5, 4.5)]
    # 벽면 규격 표지판
    spec = box((-6.9, 3.4, 2.4), (0.05, 2.2, 1.1), SIGN)

    eye((4.6, -4.4, 2.35), (-1.2, 1.4, 1.55), lens=20)
    bpy.context.view_layer.update()
    mark('dock', 'limit', limits[0], pad=0.02)
    mark('dock', 'spec', spec)
    render("node_dock.png")


# ─────────────────────── 재료 연구실 ───────────────────────
def n_matlab():
    """재료 연구실 — 고온로, 인장 시험기, 현미경, 시편 캐비닛.
       CH.3(동체 재료) 미션의 현장이 된다."""
    reset()
    WALL = mat("w", (0.30, 0.315, 0.345), rough=0.72, rough_var=0.10, noise_scale=16)
    FLOOR = mat("f", (0.105, 0.11, 0.125), rough=0.30, rough_var=0.10, noise_scale=24)
    CEIL = mat("c", (0.16, 0.17, 0.19), rough=0.80)
    LAMP = mat("l", (1, 1, 1), rough=0.4, emit=(1.0, 0.97, 0.92), emit_str=5.0)
    STEEL = mat("s", (0.60, 0.62, 0.66), rough=0.28, metal=1.0, rough_var=0.10, noise_scale=110)
    DARK = mat("dk", (0.075, 0.08, 0.095), rough=0.48, metal=0.4)
    BENCH = mat("bn", (0.22, 0.235, 0.27), rough=0.55, metal=0.3, rough_var=0.08)
    WHITE = mat("wh", (0.84, 0.85, 0.86), rough=0.58)
    GLOW = mat("gl", (0.9, 0.4, 0.1), rough=0.4, emit=(1.0, 0.40, 0.10), emit_str=18.0)
    SCREEN = mat("sc", (0.05, 0.09, 0.11), rough=0.14, emit=(0.10, 0.60, 0.66), emit_str=1.5)

    room(10.0, 10.0, 3.4, WALL, FLOOR, CEIL)
    for y in (-2.6, 1.0, 4.0):
        box((0, y, 3.34), (2.6, 0.26, 0.06), LAMP, bev=0)
        panel_light((0, y, 3.22), (2.7, 0.4), 68)

    # 고온로 — 문틈으로 붉은빛이 샌다
    box((-3.2, 2.6, 0.95), (2.0, 1.5, 1.9), WHITE)
    box((-3.2, 1.83, 1.15), (1.1, 0.05, 0.75), DARK)
    box((-3.2, 1.79, 1.15), (0.9, 0.02, 0.10), GLOW)
    box((-3.2, 2.6, 2.05), (1.4, 1.0, 0.22), STEEL)

    # 인장 시험기 — 두 기둥과 크로스헤드
    for sx in (-0.55, 0.55):
        cyl((1.9 + sx, 2.9, 1.15), 0.075, 2.3, STEEL)
    box((1.9, 2.9, 0.14), (1.8, 0.9, 0.28), DARK)
    box((1.9, 2.9, 2.32), (1.8, 0.9, 0.20), DARK)
    box((1.9, 2.9, 1.55), (0.30, 0.34, 0.30), STEEL)
    box((1.9, 2.9, 0.85), (0.30, 0.34, 0.30), STEEL)
    box((1.9, 2.9, 1.20), (0.10, 0.06, 0.42), WHITE)      # 물려 있는 시편

    # 작업대 + 현미경 + 모니터
    box((0.4, -2.4, 0.44), (5.4, 1.1, 0.88), BENCH)
    cyl((-1.4, -2.4, 1.16), 0.22, 0.56, DARK)
    cyl((-1.4, -2.55, 1.52), 0.07, 0.36, STEEL, rot=(math.radians(20), 0, 0))
    box((1.5, -2.1, 1.28), (1.3, 0.06, 0.78), SCREEN, rot=(math.radians(-8), 0, 0))

    # 시편 캐비닛
    for k in range(4):
        box((4.3, -0.4 + k * 1.0, 1.0), (0.9, 0.88, 2.0), BENCH)

    eye((0.0, -4.2, 1.62), (-0.4, 1.6, 1.55), lens=19)
    render("node_matlab.png")


# ─────────────────────── 엔진 시험동 ───────────────────────
def n_teststand():
    """엔진 점화 시험동 — 옥외 시험대, 화염 유도로, 물탱크.
       클러스터·연소 미션의 현장. 실내가 아니라 야외라 하늘이 보인다."""
    reset()
    sc = bpy.context.scene
    # 야외 — 해질녘 하늘
    w = sc.world.node_tree
    bgn = w.nodes["Background"]
    bgn.inputs[0].default_value = (0.055, 0.075, 0.13, 1)
    bgn.inputs[1].default_value = 1.1

    GROUND = mat("g", (0.14, 0.135, 0.125), rough=0.85, rough_var=0.12, noise_scale=8)
    CONC = mat("cc", (0.42, 0.425, 0.44), rough=0.78, rough_var=0.12, noise_scale=14)
    STEEL = mat("s", (0.52, 0.55, 0.60), rough=0.32, metal=1.0, rough_var=0.12, noise_scale=70)
    DARK = mat("dk", (0.075, 0.08, 0.09), rough=0.52, metal=0.5)
    RUST = mat("ru", (0.30, 0.16, 0.09), rough=0.80, metal=0.2, rough_var=0.14)
    TANKM = mat("tk", (0.70, 0.72, 0.75), rough=0.30, metal=0.9, rough_var=0.08)
    GLOW = mat("gl", (1.0, 0.5, 0.15), rough=0.4, emit=(1.0, 0.48, 0.14), emit_str=24.0)

    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
    bpy.context.object.data.materials.append(GROUND)

    # 콘크리트 기단 + 화염 유도로(경사면)
    box((0, 2.0, 0.5), (9.0, 7.0, 1.0), CONC)
    box((0, -3.4, 0.9), (9.0, 4.2, 0.5), CONC, rot=(math.radians(-19), 0, 0))

    # 시험대 프레임
    for sx in (-2.3, 2.3):
        for sy in (-1.1, 1.1):
            box((sx, 2.0 + sy, 2.6), (0.30, 0.30, 4.2), STEEL)
    box((0, 2.0, 4.8), (5.4, 3.0, 0.4), STEEL)
    box((0, 2.0, 4.3), (2.2, 2.2, 0.6), DARK)

    # 시험 중인 엔진 — 노즐이 유도로를 향한다
    bpy.ops.mesh.primitive_cone_add(radius1=0.95, radius2=0.42, depth=1.5, vertices=56,
                                    location=(0, 2.0, 3.2))
    nz = bpy.context.object
    nz.rotation_euler = (math.radians(180), 0, 0)
    nz.data.materials.append(STEEL)
    # 이 파일에는 smooth() 헬퍼가 없다 — 인라인으로 처리한다
    for _p in nz.data.polygons:
        _p.use_smooth = True
    box((0, 2.0, 1.35), (0.7, 0.7, 0.5), GLOW)          # 노즐 아래 잔광

    # 추진제 탱크 2기
    for sx, r in ((-6.2, 1.25), (6.2, 1.05)):
        cyl((sx, 4.0, 2.4), r, 4.6, TANKM)
        box((sx, 4.0, 0.2), (r * 2.4, r * 2.4, 0.4), CONC)

    # 물탱크와 배관
    cyl((-7.6, -2.0, 1.6), 1.5, 3.2, RUST)
    for k in range(5):
        cyl((-6.0 + k * 0.1, -2.0 + k * 0.9, 0.30), 0.10, 3.0, STEEL,
            rot=(math.radians(90), 0, 0))

    # 조명탑
    for sx in (-8.6, 8.6):
        cyl((sx, -1.0, 3.6), 0.16, 7.2, STEEL)
        box((sx, -1.0, 7.3), (1.1, 0.3, 0.28),
            mat("lp%d" % int(sx), (1, 1, 1), rough=0.4,
                emit=(1.0, 0.95, 0.85), emit_str=8.0), bev=0)
        panel_light((sx, -1.2, 7.0), (1.2, 0.5), 300)
    panel_light((3.0, -7.0, 9.0), (10, 10), 200, (0.55, 0.68, 0.95))

    eye((7.4, -12.5, 4.2), (0, 2.0, 3.0), lens=34)
    render("node_teststand.png")


if __name__ == "__main__":
    for fn, nm in ((n_hall, "hall"), (n_prop, "prop"),
                   (n_store, "store"), (n_dock, "dock"),
                   (n_matlab, "matlab"), (n_teststand, "teststand")):
        print("==", nm)
        fn()
    out = os.path.join(DIR, "nodes.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(HOT, f, ensure_ascii=False, indent=1)
    print("  hotspots ->", out)
    for n, hs in HOT.items():
        print("   ", n, {k: v for k, v in hs.items()})
    print("DELTA-V LAB DONE ->", DIR)


