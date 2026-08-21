# -*- coding: utf-8 -*-
"""궤도 연구소 아트 원본 — Blender Cycles (2026-08-22).

방향(운영자 질문에 대한 제안):
  · 월드(궤도 화면)의 **물체**는 행성 키우기·Space-Z 와 같은 실렌더 스프라이트
  · **선**(궤도·예측선·커버리지 링·HUD)은 벡터 그대로. 선을 렌더하면 확대·축소에서
    흐려지고, 계기 화면의 날카로움이 이 게임의 정체성이다
  · **캐릭터**는 브리핑·결과 패널에만 등장하는 관제관 1명. 팀뽑기·브롤런의
    피규어 문법(부드러운 캡슐·구 조립)을 그대로 쓴다 — 사이트 안에서 같은
    사람들이 사는 세계로 읽히게

지구는 행성 키우기의 t06(절차적 지구)을 그대로 재사용하므로 여기서 만들지 않는다.

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P orbit_scene.py
출력: scripts/og-assets/orbit/*.png (투명 배경)
"""
import bpy
import math
import os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "..", "og-assets", "orbit")
os.makedirs(DIR, exist_ok=True)


def reset(res_x=512, res_y=512, samples=200, look='AgX - Punchy'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'CUDA'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x = res_x
    sc.render.resolution_y = res_y
    sc.render.film_transparent = True
    sc.view_settings.look = look
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    # 금속은 반사할 환경이 없으면 검게 렌더된다 (Space-Z 우주선에서 겪은 실패).
    bg.inputs[0].default_value = (0.40, 0.48, 0.62, 1.0)
    bg.inputs[1].default_value = 0.55
    sc.world = w
    return sc


def mat(name, color, rough=0.35, metal=0.0, emit=None, emit_str=0.0, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss > 0:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.15, 0.08, 0.08)
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def area(loc, power, size=6.0, color=(1, 1, 1), track=(0, 0, 0)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    L = bpy.context.object
    L.data.energy = power
    L.data.size = size
    L.data.color = color
    d = Vector(track) - Vector(loc)
    L.rotation_mode = 'QUATERNION'
    L.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    return L


def render(name):
    bpy.context.scene.render.filepath = os.path.join(DIR, name)
    bpy.ops.render.render(write_still=True)
    print("  rendered", name)


# ─────────────────────── 탑다운 (궤도면을 위에서 본다) ───────────────────────
def top_camera(ortho):
    bpy.ops.object.camera_add(location=(0, 0, 9))
    cam = bpy.context.object
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ortho
    cam.rotation_euler = (0, 0, 0)
    bpy.context.scene.camera = cam
    return cam


def top_lights():
    area((3.4, 3.0, 6.0), 900, 7.0, (1.0, 0.97, 0.92))
    area((-4.2, -2.4, 4.4), 420, 8.0, (0.55, 0.75, 1.0))


def panel(x, y, w, h, m, tilt=0.0):
    """태양 전지판 — 얇은 판. 살짝 기울여 빛을 다르게 받게 한다."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0))
    o = bpy.context.object
    o.scale = (w, h, 0.035)
    o.rotation_euler = (tilt, 0, 0)
    o.data.materials.append(m)
    return o


def cells(x, y, w, h, n, m):
    """전지판 위의 셀 격자 — 이게 있어야 '태양전지'로 읽힌다."""
    for i in range(n):
        gx = x - w + (i + 0.5) * (2 * w / n)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(gx, y, 0.042))
        o = bpy.context.object
        o.scale = (w / n * 0.80, h * 0.86, 0.012)
        o.data.materials.append(m)


def s_relay():
    """통신 위성 — 본체 + 전지판 2장 + 접시 안테나. 작고 가볍게 읽혀야 한다."""
    reset()
    top_camera(2.30)
    top_lights()
    BODY = mat("body", (0.86, 0.88, 0.92), rough=0.30, metal=0.55)
    GOLD = mat("gold", (0.95, 0.74, 0.30), rough=0.34, metal=0.80)
    PANEL = mat("panel", (0.055, 0.085, 0.26), rough=0.22, metal=0.35)
    CELL = mat("cell", (0.10, 0.16, 0.42), rough=0.16, metal=0.55)
    TEAL = mat("teal", (0.10, 0.72, 0.92), rough=0.3,
               emit=(0.15, 0.92, 1.0), emit_str=3.0)

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.10))
    b = bpy.context.object
    b.scale = (0.42, 0.50, 0.34)
    b.data.materials.append(GOLD)
    # 전지판
    for sx in (-1, 1):
        panel(sx * 0.72, 0, 0.44, 0.26, PANEL)
        cells(sx * 0.72, 0, 0.44, 0.26, 4, CELL)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.24, vertices=16,
                                            location=(sx * 0.36, 0, 0.06))
        a = bpy.context.object
        a.rotation_euler = (0, math.radians(90), 0)
        a.data.materials.append(BODY)
        smooth(a)
    # 접시 안테나 — 지구를 향한다(화면 아래쪽)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.30, segments=48, ring_count=24,
                                         location=(0, -0.40, 0.10))
    d = bpy.context.object
    d.scale = (1.0, 0.34, 1.0)
    d.data.materials.append(BODY)
    smooth(d)
    # 통신 표시
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, segments=20, ring_count=10,
                                         location=(0, -0.50, 0.16))
    t = bpy.context.object
    t.data.materials.append(TEAL)
    smooth(t)
    render("relay.png")


def s_datacenter():
    """궤도 데이터센터 — 큰 본체 + 전지판 4장 + 방열판.
       방열판은 전지판과 **직각**으로 둔다. 실제로도 방열판은 태양에 모서리를
       향하게 배치하며, 화면에서도 두 판이 무엇이 다른지 즉시 구분된다."""
    reset()
    top_camera(3.05)
    top_lights()
    BODY = mat("body", (0.80, 0.83, 0.88), rough=0.32, metal=0.60)
    DARKB = mat("darkb", (0.13, 0.15, 0.20), rough=0.42, metal=0.55)
    PANEL = mat("panel", (0.055, 0.085, 0.26), rough=0.22, metal=0.35)
    CELL = mat("cell", (0.10, 0.16, 0.42), rough=0.16, metal=0.55)
    RAD = mat("rad", (0.90, 0.91, 0.94), rough=0.62, metal=0.10)
    TEAL = mat("teal", (0.10, 0.72, 0.92), rough=0.3,
               emit=(0.15, 0.92, 1.0), emit_str=2.6)

    # 본체 — 서버 랙 느낌으로 층을 준다
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.12))
    b = bpy.context.object
    b.scale = (0.60, 0.86, 0.40)
    b.data.materials.append(BODY)
    for k in range(3):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.44 + k * 0.44, 0.34))
        r = bpy.context.object
        r.scale = (0.62, 0.10, 0.05)
        r.data.materials.append(DARKB)
    # 연산 표시등
    for k in range(4):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.30 + k * 0.20, 0.62, 0.34))
        L = bpy.context.object
        L.scale = (0.05, 0.05, 0.05)
        L.data.materials.append(TEAL)
    # 전지판 4장 (좌우 2단)
    for sx in (-1, 1):
        for sy in (-1, 1):
            panel(sx * 1.06, sy * 0.34, 0.42, 0.28, PANEL)
            cells(sx * 1.06, sy * 0.34, 0.42, 0.28, 4, CELL)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.50, vertices=16,
                                            location=(sx * 0.86, 0, 0.08))
        a = bpy.context.object
        a.rotation_euler = (0, math.radians(90), 0)
        a.data.materials.append(BODY)
        smooth(a)
    # 방열판 — 전지판과 직각. 얇고 흰 판 2장
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, sy * 1.06, 0.12))
        rp = bpy.context.object
        rp.scale = (0.40, 0.42, 0.028)
        rp.data.materials.append(RAD)
        for k in range(5):
            bpy.ops.mesh.primitive_cube_add(
                size=1, location=(-0.32 + k * 0.16, sy * 1.06, 0.135))
            g = bpy.context.object
            g.scale = (0.012, 0.40, 0.006)
            g.data.materials.append(DARKB)
    render("datacenter.png")


def s_debris():
    """파편 — 부서진 위성 조각. 불규칙해야 한다."""
    reset(res_x=256, res_y=256, samples=160)
    top_camera(1.30)
    top_lights()
    METAL = mat("dm", (0.62, 0.64, 0.70), rough=0.55, metal=0.65)
    PANEL = mat("dp", (0.075, 0.10, 0.28), rough=0.30, metal=0.35)
    import random
    random.seed(7)
    for k in range(5):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(
            random.uniform(-0.30, 0.30), random.uniform(-0.30, 0.30),
            random.uniform(-0.05, 0.10)))
        o = bpy.context.object
        o.scale = (random.uniform(0.10, 0.30), random.uniform(0.06, 0.22),
                   random.uniform(0.04, 0.12))
        o.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3),
                            random.uniform(0, 3))
        o.data.materials.append(PANEL if k % 2 else METAL)
    render("debris.png")


# ─────────────────────── 관제관 (정면 흉상) ───────────────────────
def M(px, py, pz):
    """three 식 (x, y=위, z=앞) → blender (x, -z, y). 사이트 공통 규약."""
    return (px, -pz, py)


def sphere(tpos, r, m, scale=(1, 1, 1), parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=48, ring_count=24,
                                         location=M(*tpos))
    o = bpy.context.object
    o.scale = scale
    o.data.materials.append(m)
    smooth(o)
    if parent:
        o.parent = parent
    return o


def capsule(ta, tb, r, m, parent=None):
    va, vb = Vector(M(*ta)), Vector(M(*tb))
    d = vb - va
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, vertices=32,
                                        location=(va + vb) / 2)
    c = bpy.context.object
    c.rotation_mode = 'QUATERNION'
    c.rotation_quaternion = d.to_track_quat('Z', 'Y')
    c.data.materials.append(m)
    smooth(c)
    if parent:
        c.parent = parent
    for pt in (va, vb):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=32, ring_count=16,
                                             location=pt)
        s = bpy.context.object
        s.data.materials.append(m)
        smooth(s)
        if parent:
            s.parent = parent


def box(tpos, scale, m, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=M(*tpos))
    o = bpy.context.object
    o.scale = scale
    o.rotation_euler = rot
    o.data.materials.append(m)
    if parent:
        o.parent = parent
    return o


def s_controller(mood, fname):
    """관제관 — **전신 피규어**. 팀뽑기·브롤런과 같은 문법이다.

    흉상으로 크게 잡으면 이 스타일의 약점(얼굴 디테일 부족)이 그대로 드러난다.
    전신을 작게 보여주면 실루엣과 자세가 캐릭터를 만든다 — 사이트의 다른
    피규어들이 통하는 이유가 그것이다.

    mood: 'brief'(팔짱 끼고 브리핑) · 'win'(엄지척) · 'fail'(이마 짚기)
    """
    reset(res_x=460, res_y=760, samples=220)
    bpy.ops.object.camera_add(location=(0, -12.0, 3.30))
    cam = bpy.context.object
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 8.2
    cam.rotation_euler = (math.radians(89), 0, 0)
    bpy.context.scene.camera = cam

    area((3.6, -5.4, 6.4), 900, 6.0, (1.0, 0.96, 0.90), track=(0, 0, 3.0))
    area((-4.6, -3.0, 2.6), 330, 6.5, (0.35, 0.80, 1.0), track=(0, 0, 2.6))
    area((0.4, 4.2, 5.2), 380, 5.5, (0.30, 0.95, 0.95), track=(0, 0, 3.4))

    SUIT = mat("suit", (0.15, 0.46, 0.56), rough=0.40, sss=0.02)
    SUIT2 = mat("suit2", (0.10, 0.32, 0.41), rough=0.44)
    SKIN = mat("skin", (0.94, 0.76, 0.60), rough=0.42, sss=0.06)
    HAIR = mat("hair", (0.10, 0.09, 0.11), rough=0.55)
    DARK = mat("dark", (0.04, 0.055, 0.12), rough=0.5)
    TEAL = mat("teal", (0.10, 0.72, 0.92), rough=0.3,
               emit=(0.15, 0.92, 1.0), emit_str=3.4)

    # ── 몸 ──
    sphere((0, 2.62, 0), 0.98, SUIT, scale=(1.20, 0.82, 1.30))    # 상체
    sphere((0, 1.52, 0), 0.72, SUIT2, scale=(1.06, 0.82, 0.92))   # 골반
    capsule((-0.40, 1.34, 0), (-0.42, 0.34, 0.04), 0.28, SUIT2)   # 다리
    capsule((0.40, 1.34, 0), (0.42, 0.34, 0.04), 0.28, SUIT2)
    sphere((-0.44, 0.20, 0.16), 0.28, DARK, scale=(1.0, 0.62, 1.5))  # 신발
    sphere((0.44, 0.20, 0.16), 0.28, DARK, scale=(1.0, 0.62, 1.5))
    capsule((0, 3.52, 0.02), (0, 3.86, 0.03), 0.26, SKIN)         # 목
    sphere((0, 4.46, 0.05), 0.86, SKIN)                           # 머리

    # 머리카락 — 대머리 달걀에서 벗어나는 최소 장치
    sphere((0, 4.62, 0.02), 0.885, HAIR, scale=(1.0, 1.0, 0.78))
    box((0, 4.30, 0.80), (0.92, 0.30, 0.16), HAIR, rot=(0.30, 0, 0))

    # 헤드셋 — 관제관임을 한 컷에 알려주는 소품
    capsule((-0.80, 4.72, 0.0), (0.80, 4.72, 0.0), 0.085, DARK)
    for ex in (-0.86, 0.86):
        sphere((ex, 4.40, 0.03), 0.22, DARK, scale=(0.62, 1.0, 1.0))
    capsule((0.82, 4.30, 0.10), (0.34, 4.06, 0.66), 0.048, DARK)
    sphere((0.28, 4.04, 0.72), 0.075, TEAL)

    # 가슴 패치 — 연구소 소속 표시
    box((0.0, 2.92, 0.80), (0.30, 0.22, 0.04), TEAL, rot=(0.16, 0, 0))

    # ── 팔·손 ──
    def fist(t, r=0.24):
        sphere(t, r, SKIN, scale=(1.0, 0.92, 1.05))

    if mood == 'win':
        # 두 팔 번쩍 — 환호.
        # 엄지척은 쓰지 않는다. 2차에서 주먹 위로 캡슐이 솟은 형태가
        # 가운뎃손가락으로 읽혔고, 손가락 제스처는 이 해상도에서 늘 위험하다.
        # 만세는 실루엣만으로 읽히고 오독의 여지가 없다.
        for sx in (-1, 1):
            capsule((sx*1.10, 3.16, 0.06), (sx*1.52, 4.06, 0.30), 0.26, SUIT)
            capsule((sx*1.52, 4.06, 0.30), (sx*1.66, 5.10, 0.36), 0.25, SUIT)
            fist((sx*1.70, 5.36, 0.38), 0.27)
    elif mood == 'fail':
        # 이마 짚기 — 손을 얼굴 **옆**에 둬 표정이 가리지 않게 한다
        capsule((1.12, 3.10, 0.10), (1.28, 2.10, 0.34), 0.26, SUIT)
        fist((1.32, 1.86, 0.40))
        capsule((-1.08, 3.08, 0.20), (-1.30, 2.44, 0.76), 0.26, SUIT)
        capsule((-1.30, 2.44, 0.76), (-0.72, 4.28, 0.92), 0.25, SUIT)
        fist((-0.62, 4.52, 0.96), 0.27)
    else:
        # 팔짱 — 위팔을 벌려 실루엣에 걸리게 하고, 아래팔을 겹친다
        capsule((-1.14, 3.14, 0.06), (-1.26, 2.34, 0.40), 0.26, SUIT)
        capsule((1.14, 3.14, 0.06), (1.26, 2.34, 0.40), 0.26, SUIT)
        capsule((-1.26, 2.34, 0.46), (0.82, 2.56, 0.72), 0.25, SUIT2)
        capsule((1.26, 2.34, 0.60), (-0.82, 2.28, 0.84), 0.25, SUIT)

    # ── 표정 ──
    if mood == 'fail':
        eyes = [(-0.28, 4.44, 0.86), (0.28, 4.44, 0.86)]
        brows = [(-0.30, 4.68, 0.82, -0.40), (0.30, 4.68, 0.82, 0.40)]
        mouth = ((0.0, 4.12, 0.90), (0.16, 0.035, 0.05))
    elif mood == 'win':
        eyes = [(-0.28, 4.46, 0.86), (0.28, 4.46, 0.86)]
        brows = [(-0.30, 4.74, 0.82, 0.28), (0.30, 4.74, 0.82, -0.28)]
        mouth = ((0.0, 4.14, 0.90), (0.20, 0.05, 0.07))
    else:
        eyes = [(-0.28, 4.45, 0.86), (0.28, 4.45, 0.86)]
        brows = [(-0.30, 4.71, 0.82, 0.13), (0.30, 4.71, 0.82, -0.13)]
        mouth = ((0.0, 4.13, 0.90), (0.14, 0.035, 0.035))

    for ex, ey, ez in eyes:
        sphere((ex, ey, ez), 0.115, DARK, scale=(1, 0.55, 0.6))
    for bx, by, bz, tilt in brows:
        box((bx, by, bz), (0.22, 0.045, 0.055), DARK, rot=(0.42, tilt, 0))
    box(mouth[0], mouth[1], DARK, rot=(0.38, 0, 0))

    render(fname)


if __name__ == "__main__":
    for fn, label in ((s_relay, "relay"), (s_datacenter, "datacenter"),
                      (s_debris, "debris")):
        print("==", label)
        fn()
    for mood, name in (("brief", "ctrl_brief.png"), ("win", "ctrl_win.png"),
                       ("fail", "ctrl_fail.png")):
        print("==", mood)
        s_controller(mood, name)
    print("ORBIT ART DONE ->", DIR)
