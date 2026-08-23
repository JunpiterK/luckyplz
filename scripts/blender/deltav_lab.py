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
    """추진 연구동 — 화이트보드와 엔진 시험 셀.

    2026-08-23 재작성. 실시간 3D 로 바뀌면서 절차적 노이즈가 사라졌으므로
    디테일을 **기하와 재질 수**로 낸다. 상자 몇 개짜리 방이었던 것을 실제
    시험 셀처럼 채운다 — 구조 트러스, 케이블 트레이, 가스 실린더 뱅크,
    계측 랙, 작업대, 안전 설비.
    """
    reset()
    # ── 재질 — 회색 하나로 뭉치지 않는다 ──
    WALL = mat("wall", (0.285, 0.30, 0.325), rough=0.68)
    WALL2 = mat("wall2", (0.20, 0.215, 0.24), rough=0.60)      # 허리 아래 짙은 도장
    FLOOR = mat("floor", (0.105, 0.11, 0.125), rough=0.42)
    CEIL = mat("ceil", (0.135, 0.142, 0.16), rough=0.85)
    HAZ = mat("haz", (0.62, 0.50, 0.10), rough=0.55)           # 경고 노랑(바닥 띠)
    GRATE = mat("grate", (0.17, 0.18, 0.20), rough=0.52, metal=0.7)
    BOARD = mat("board", (0.905, 0.91, 0.915), rough=0.16)
    FRAME = mat("frame", (0.62, 0.64, 0.67), rough=0.30, metal=0.9)
    ALU = mat("alu", (0.55, 0.57, 0.60), rough=0.36, metal=1.0)   # 브러시드 알루미늄
    STEEL = mat("steel", (0.48, 0.50, 0.54), rough=0.26, metal=1.0)
    INCO = mat("inco", (0.42, 0.40, 0.38), rough=0.34, metal=1.0)  # 니켈합금(연소실)
    COPPER = mat("copper", (0.71, 0.36, 0.17), rough=0.24, metal=1.0)
    BRASS = mat("brass", (0.72, 0.58, 0.24), rough=0.30, metal=1.0)
    ANOD = mat("anod", (0.085, 0.09, 0.105), rough=0.40, metal=0.55)  # 아노다이즈 흑색
    RUBBER = mat("rubber", (0.055, 0.058, 0.065), rough=0.88)
    PAINT_R = mat("paint_r", (0.42, 0.09, 0.08), rough=0.48)      # 소화기·비상
    PAINT_G = mat("paint_g", (0.10, 0.30, 0.16), rough=0.52)      # 가스병 뱅크
    PAINT_B = mat("paint_b", (0.10, 0.20, 0.36), rough=0.52)
    LAMP = mat("lamp", (1, 1, 1), rough=0.4, emit=(1.0, 0.95, 0.88), emit_str=5.2)
    SCREEN = mat("screen", (0.04, 0.07, 0.09), rough=0.12,
                 emit=(0.10, 0.58, 0.66), emit_str=1.7)
    SCREEN2 = mat("screen2", (0.05, 0.05, 0.04), rough=0.12,
                  emit=(0.62, 0.42, 0.10), emit_str=1.2)
    LED_G = mat("led_g", (0.1, 0.5, 0.2), rough=0.3, emit=(0.15, 1.0, 0.45), emit_str=6.0)
    LED_R = mat("led_r", (0.5, 0.1, 0.1), rough=0.3, emit=(1.0, 0.20, 0.15), emit_str=6.0)
    STRIP = mat("strip", (0.4, 0.3, 0.05), rough=0.5,
                emit=(1.0, 0.62, 0.08), emit_str=2.2)

    W, D, H = 10.0, 12.5, 4.6
    room(W, D, H, WALL, FLOOR, CEIL)

    # ── 벽 — 허리 아래 짙은 도장 + 몰딩. 단조로운 벽 한 장을 피한다 ──
    for (px, py, sx, sy) in ((0, D / 2 - 0.02, W, 0.06),
                             (0, -D / 2 + 0.02, W, 0.06),
                             (-W / 2 + 0.02, 0, 0.06, D),
                             (W / 2 - 0.02, 0, 0.06, D)):
        box((px, py, 0.60), (sx, sy, 1.20), WALL2, bev=0)
        box((px, py, 1.24), (sx * 1.001, sy * 1.4, 0.05), FRAME, bev=0.006)

    # ── 천장 구조 — 노출 보. 빈 천장은 실내를 싸구려로 만든다 ──
    for y in range(-5, 6, 2):
        box((0, y, H - 0.22), (W - 0.3, 0.16, 0.44), FRAME, bev=0.01)
        box((0, y, H - 0.44), (W - 0.3, 0.42, 0.05), FRAME, bev=0.006)
    for x in (-3.4, 0, 3.4):
        box((x, 0, H - 0.52), (0.14, D - 0.4, 0.30), FRAME, bev=0.01)

    # 조명 — 라인 4줄
    for y in (-4.4, -1.5, 1.5, 4.4):
        box((-2.2, y, H - 0.62), (2.6, 0.22, 0.07), LAMP, bev=0)
        box((2.2, y, H - 0.62), (2.6, 0.22, 0.07), LAMP, bev=0)
        panel_light((-2.2, y, H - 0.72), (2.7, 0.34), 62)
        panel_light((2.2, y, H - 0.72), (2.7, 0.34), 62)

    # ── 케이블 트레이 — 벽을 타고 천장으로. 실제 시험동의 표식 ──
    def tray(x, y, z, length, along_y=True, mm=ALU):
        sx, sy = (0.34, length) if along_y else (length, 0.34)
        box((x, y, z), (sx, sy, 0.05), mm, bev=0.006)
        box((x - (0 if along_y else 0), y, z + 0.07),
            (sx if along_y else length, 0.03 if along_y else sy, 0.14), mm, bev=0.004)
        n = max(2, int(length / 0.8))
        for i in range(n):
            t = -length / 2 + length * (i + 0.5) / n
            if along_y:
                box((x, y + t, z + 0.04), (0.30, 0.05, 0.05), ANOD, bev=0.004)
            else:
                box((x + t, y, z + 0.04), (0.05, 0.30, 0.05), ANOD, bev=0.004)

    tray(-4.6, 0.0, H - 1.05, D - 1.2, True)
    tray(4.6, 0.0, H - 1.05, D - 1.2, True)
    tray(0.0, -5.6, H - 1.05, W - 1.2, False)

    # 벽 배관 — 굵기와 재질을 섞는다
    for (x, r, mm, zz) in ((-4.72, 0.075, STEEL, 2.55), (-4.72, 0.055, BRASS, 2.30),
                           (4.72, 0.085, STEEL, 2.62), (4.72, 0.045, COPPER, 2.38)):
        cyl((x, 0.4, zz), r, D - 2.0, mm, rot=(math.radians(90), 0, 0), verts=20)
        for yy in (-4.2, -1.4, 1.4, 4.2):
            cyl((x, yy, zz), r * 1.5, 0.10, ANOD, rot=(math.radians(90), 0, 0), verts=18)

    # ── 바닥 — 경고 띠와 배수 그레이팅 ──
    for sx in (-1.9, 1.9):
        box((2.4 + sx * 0.85, 1.4, 0.012), (0.16, 5.2, 0.02), HAZ, bev=0)
    for sy in (-1.0, 1.0):
        box((2.4, 1.4 + sy * 2.6, 0.012), (3.4, 0.16, 0.02), HAZ, bev=0)
    for i in range(9):
        box((2.4, -1.9 + i * 0.13, 0.02), (2.2, 0.07, 0.04), GRATE, bev=0.004)

    # ══════════ 화이트보드 — 이 방에서 가장 중요한 물건 ══════════
    BX = -W / 2 + 0.10
    board = box((BX + 0.04, 0.8, 1.95), (0.05, 4.0, 1.9), BOARD)
    box((BX, 0.8, 1.95), (0.04, 4.20, 2.10), FRAME, bev=0.01)          # 테두리
    box((BX + 0.06, -1.15, 0.96), (0.09, 0.62, 0.05), FRAME, bev=0.006)  # 마커 받침
    for i, cc in enumerate(((0.7, 0.1, 0.1), (0.1, 0.1, 0.7), (0.1, 0.1, 0.1))):
        mk = mat("mk%d" % i, cc, rough=0.42)
        cyl((BX + 0.10, -1.32 + i * 0.15, 1.01), 0.011, 0.13, mk,
            rot=(0, math.radians(90), 0), verts=12)
    # 보드 옆 압정으로 붙인 출력물 — 사람이 쓰는 방으로 보이게 한다
    for i, (yy, zz, ww, hh) in enumerate(((3.35, 2.55, 0.42, 0.58),
                                          (3.35, 1.85, 0.42, 0.58),
                                          (3.90, 2.20, 0.40, 0.54))):
        pp = mat("paper%d" % i, (0.86, 0.85, 0.82), rough=0.70)
        box((BX + 0.05, yy, zz), (0.01, ww, hh), pp, bev=0)

    # ══════════ 엔진 시험 셀 ══════════
    EX, EY = 2.4, 1.4

    # 추력 프레임 — 4주 트러스 + 사선 브레이스
    for sx in (-1.5, 1.5):
        for sy in (-1.5, 1.5):
            box((EX + sx, EY + sy, 1.75), (0.17, 0.17, 3.5), FRAME, bev=0.012)
            box((EX + sx, EY + sy, 0.06), (0.42, 0.42, 0.12), ANOD, bev=0.008)
            for a in range(4):     # 앵커 볼트
                ang = math.pi / 2 * a + math.pi / 4
                cyl((EX + sx + math.cos(ang) * 0.15, EY + sy + math.sin(ang) * 0.15, 0.14),
                    0.022, 0.09, STEEL, verts=10)
    for z in (1.1, 2.4):
        for sy in (-1.5, 1.5):
            box((EX, EY + sy, z), (3.0, 0.12, 0.12), FRAME, bev=0.008)
        for sx in (-1.5, 1.5):
            box((EX + sx, EY, z), (0.12, 3.0, 0.12), FRAME, bev=0.008)
    for sy in (-1.5, 1.5):        # 사선 브레이스
        box((EX, EY + sy, 1.75), (3.3, 0.09, 0.09), FRAME,
            rot=(0, math.radians(23), 0), bev=0.006)
    box((EX, EY, 3.52), (3.3, 3.3, 0.16), FRAME, bev=0.012)      # 상부 크로스헤드
    box((EX, EY, 3.30), (1.3, 1.3, 0.30), ANOD, bev=0.01)        # 마운트 블록

    # 엔진 — 인젝터 돔 · 연소실 · 종형 노즐 · 냉각 리브
    cyl((EX, EY, 3.02), 0.34, 0.26, ANOD, verts=48)                     # 짐벌
    cyl((EX, EY, 2.76), 0.44, 0.30, ALU, verts=48)                      # 인젝터 돔
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.44, segments=48, ring_count=24,
                                         location=(EX, EY, 2.88))
    dome = bpy.context.object
    dome.scale = (1, 1, 0.55)
    dome.data.materials.append(ALU)
    for p in dome.data.polygons:
        p.use_smooth = True
    for a in range(16):           # 돔 볼트 링
        ang = math.pi * 2 * a / 16
        cyl((EX + math.cos(ang) * 0.455, EY + math.sin(ang) * 0.455, 2.62),
            0.020, 0.055, STEEL, verts=8)
    cyl((EX, EY, 2.20), 0.31, 0.86, INCO, verts=48)                     # 연소실
    for a in range(28):           # 재생냉각 채널 리브
        ang = math.pi * 2 * a / 28
        box((EX + math.cos(ang) * 0.322, EY + math.sin(ang) * 0.322, 2.20),
            (0.030, 0.030, 0.80), COPPER, rot=(0, 0, ang), bev=0.004)
    cyl((EX, EY, 1.72), 0.345, 0.14, BRASS, verts=48)                   # 스로트 매니폴드

    bpy.ops.mesh.primitive_cone_add(radius1=0.92, radius2=0.29, depth=1.30,
                                    vertices=64, location=(EX, EY, 1.02))
    noz = bpy.context.object
    noz.rotation_euler = (math.radians(180), 0, 0)
    noz.data.materials.append(COPPER)
    for p in noz.data.polygons:
        p.use_smooth = True
    for a in range(36):           # 노즐 냉각관
        ang = math.pi * 2 * a / 36
        cyl((EX + math.cos(ang) * 0.63, EY + math.sin(ang) * 0.63, 1.02),
            0.026, 1.28, STEEL, rot=(math.radians(13) * math.cos(ang + math.pi / 2),
                                     math.radians(13) * math.sin(ang + math.pi / 2), 0),
            verts=8)
    cyl((EX, EY, 0.37), 0.96, 0.07, INCO, verts=64)                     # 출구 링

    # 터보펌프 2기 + 배관
    for sx in (-1, 1):
        px, py = EX + sx * 0.72, EY + 0.30
        cyl((px, py, 2.36), 0.20, 0.40, ALU, verts=32)
        cyl((px, py, 2.62), 0.12, 0.18, ANOD, verts=24)
        cyl((px, py, 2.06), 0.15, 0.24, STEEL, verts=24)
        # 벨로우즈가 있는 급기 배관
        cyl((px, py - 0.55, 2.06), 0.085, 0.9, STEEL,
            rot=(math.radians(90), 0, 0), verts=20)
        for i in range(5):
            cyl((px, py - 0.30 - i * 0.10, 2.06), 0.105, 0.06, ALU,
                rot=(math.radians(90), 0, 0), verts=20)
        # 밸브 바디
        box((px, py - 1.02, 2.06), (0.22, 0.22, 0.24), BRASS, bev=0.01)
        cyl((px, py - 1.02, 2.28), 0.055, 0.22, STEEL, verts=16)
        cyl((px, py - 1.02, 2.40), 0.13, 0.03, PAINT_R, verts=20)       # 핸들

    # 짐벌 액추에이터 2기
    for a in (0.6, math.pi - 0.6):
        ax, ay = EX + math.cos(a) * 0.95, EY + math.sin(a) * 0.95
        cyl((ax, ay, 2.60), 0.075, 0.70, ALU,
            rot=(math.radians(28) * math.sin(a), math.radians(28) * math.cos(a), 0), verts=16)
        cyl((ax, ay, 2.30), 0.045, 0.34, STEEL,
            rot=(math.radians(28) * math.sin(a), math.radians(28) * math.cos(a), 0), verts=12)

    # 화염 유도로 — 엔진 아래
    box((EX, EY, 0.03), (2.0, 2.0, 0.06), ANOD, bev=0)
    cyl((EX, EY, 0.10), 0.78, 0.20, ANOD, verts=40)

    # ══════════ 계측 랙 · 콘솔 ══════════
    # 카메라 정면 0.8m 에 두면 모니터가 화면의 11% 를 먹고 방을 가린다(실측).
    # 왼쪽 중경으로 물려 화면 구성을 연다.
    CX, CY = -2.4, -1.9
    box((CX, CY - 0.32, 1.00), (2.9, 0.72, 2.00), ANOD, bev=0.012)       # 19인치 랙
    for i in range(7):                                                    # 랙 유닛
        zz = 0.24 + i * 0.26
        uu = [ALU, ANOD, ALU, STEEL, ANOD, ALU, ANOD][i]
        box((CX, CY - 0.66, zz), (2.76, 0.06, 0.21), uu, bev=0.005)
        for j in range(4):
            box((CX - 1.15 + j * 0.77, CY - 0.70, zz), (0.05, 0.03, 0.05),
                LED_G if (i + j) % 3 else LED_R, bev=0)
    box((CX, CY - 0.70, 2.06), (2.9, 0.05, 0.05), STRIP, bev=0)          # 경고 스트립

    # 책상 + 모니터 3대
    box((CX + 2.6, CY + 0.10, 0.74), (2.4, 1.0, 0.06), ALU, bev=0.008)
    for sx in (-1.1, 1.1):
        box((CX + 2.6 + sx, CY + 0.10, 0.36), (0.08, 0.86, 0.72), ANOD, bev=0.006)
    scr = None
    for i, sx in enumerate((-0.78, 0.0, 0.78)):
        cyl((CX + 2.6 + sx, CY + 0.34, 0.80), 0.11, 0.03, ANOD, verts=20)
        box((CX + 2.6 + sx, CY + 0.34, 0.96), (0.05, 0.05, 0.30), ANOD, bev=0.004)
        m = box((CX + 2.6 + sx, CY + 0.36, 1.34), (0.70, 0.04, 0.44),
                SCREEN if i != 1 else SCREEN2, rot=(math.radians(-8), 0, 0), bev=0.004)
        if i == 1:
            scr = m
    box((CX + 2.6, CY - 0.22, 0.79), (0.62, 0.20, 0.02), ANOD, bev=0.004)   # 키보드
    # 의자
    box((CX + 2.6, CY - 0.95, 0.46), (0.52, 0.50, 0.07), RUBBER, bev=0.02)
    box((CX + 2.6, CY - 1.20, 0.78), (0.50, 0.07, 0.56), RUBBER,
        rot=(math.radians(-9), 0, 0), bev=0.02)
    cyl((CX + 2.6, CY - 0.95, 0.22), 0.045, 0.44, STEEL, verts=16)
    for a in range(5):
        ang = math.pi * 2 * a / 5
        box((CX + 2.6 + math.cos(ang) * 0.20, CY - 0.95 + math.sin(ang) * 0.20, 0.04),
            (0.30, 0.05, 0.04), ANOD, rot=(0, 0, ang), bev=0.004)

    # ══════════ 지원 설비 ══════════
    # 가스 실린더 뱅크 — 벽에 체인으로 묶여 있다
    for i in range(5):
        gx = -3.9 + i * 0.46
        cyl((gx, 5.85, 0.78), 0.155, 1.50, PAINT_G, verts=28)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.155, segments=28, ring_count=14,
                                             location=(gx, 5.85, 1.53))
        cap = bpy.context.object
        cap.scale = (1, 1, 0.55)
        cap.data.materials.append(PAINT_G)
        for p in cap.data.polygons:
            p.use_smooth = True
        cyl((gx, 5.85, 1.72), 0.045, 0.16, BRASS, verts=14)
        cyl((gx, 5.85, 1.82), 0.085, 0.03, BRASS, verts=18)
    box((-3.0, 5.72, 1.10), (2.6, 0.04, 0.05), STEEL, bev=0.004)         # 체인 대용 스트랩

    # 작업대 — 오른쪽 벽. 카메라가 서는 남쪽 코너는 비워 둔다
    box((4.35, -3.2, 0.86), (0.85, 3.4, 0.08), ALU, bev=0.008)
    for sy in (-1.5, 1.5):
        box((4.35, -3.2 + sy, 0.43), (0.78, 0.10, 0.86), ANOD, bev=0.006)
    box((4.35, -3.2, 0.42), (0.70, 3.1, 0.05), ANOD, bev=0.006)
    for i in range(6):                                                    # 부품통
        by = -4.5 + i * 0.52
        bmat = [PAINT_B, PAINT_R, PAINT_G][i % 3]
        box((4.55, by, 1.02), (0.34, 0.44, 0.24), bmat, bev=0.012)
    for i in range(7):                                                    # 벽걸이 공구
        cyl((4.72, -4.4 + i * 0.36, 1.72), 0.017, 0.34, STEEL,
            rot=(0, math.radians(90), 0), verts=10)
        box((4.72, -4.4 + i * 0.36, 1.94), (0.05, 0.09, 0.11), ANOD, bev=0.006)
    box((4.76, -3.2, 1.85), (0.03, 2.8, 0.62), WALL2, bev=0)             # 공구판

    # 이동식 공구함 — 왼쪽 벽 앞
    box((-4.1, -4.5, 0.52), (0.86, 0.62, 0.94), PAINT_R, bev=0.012)
    for i in range(4):
        box((-3.70, -4.5, 0.20 + i * 0.24), (0.05, 0.48, 0.05), ALU, bev=0.004)
    for sx in (-0.3, 0.3):
        for sy in (-0.22, 0.22):
            cyl((-4.1 + sx, -4.5 + sy, 0.06), 0.06, 0.05, RUBBER,
                rot=(math.radians(90), 0, 0), verts=14)

    # 안전 설비 — 소화기 · 구급함 · 비상등
    cyl((4.72, -0.6, 0.70), 0.115, 0.72, PAINT_R, rot=(0, math.radians(90), 0), verts=24)
    cyl((4.72, -0.6, 1.12), 0.045, 0.16, ANOD, verts=14)
    box((4.70, 2.6, 1.55), (0.06, 0.44, 0.36), PAINT_R, bev=0.01)
    box((4.66, 2.6, 1.55), (0.01, 0.16, 0.05), BOARD, bev=0)
    box((4.66, 2.6, 1.55), (0.01, 0.05, 0.16), BOARD, bev=0)
    for yy in (-3.6, 3.6):
        box((4.70, yy, 2.85), (0.07, 0.34, 0.14), STRIP, bev=0.006)

    # 사다리 — 크로스헤드로 올라가는
    for sx in (-0.24, 0.24):
        box((EX + 2.1 + sx, EY - 1.9, 1.80), (0.06, 0.06, 3.6), ALU, bev=0.006)
    for i in range(11):
        box((EX + 2.1, EY - 1.9, 0.28 + i * 0.32), (0.50, 0.05, 0.04), ALU, bev=0.004)

    # ── 카메라 ──
    # 화이트보드(왼쪽)와 엔진(오른쪽)이 한 프레임에 들어와야 한다.
    eye((0.3, -5.75, 1.70), (-0.4, 1.2, 1.85), lens=17)
    bpy.context.view_layer.update()
    mark('prop', 'board', board)
    mark('prop', 'engine', noz, pad=0.02)
    mark('prop', 'console', scr)
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


