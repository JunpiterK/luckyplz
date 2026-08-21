# -*- coding: utf-8 -*-
"""Space-Z 우주선 + 위협 오브젝트 스프라이트 — Blender Cycles (2026-08-21).

행성 키우기에서 검증한 파이프라인을 Space-Z 에 적용한다.
게임은 탑다운(위에서 내려다봄)이고 우주선은 항상 화면 위쪽을 향한다.
따라서 카메라를 기체 바로 위에 두고 정면(노즈가 위)으로 렌더한다.

출력: scripts/og-assets/spacez/*.png (투명 배경)
  ship.png        기본 기체
  ship_thrust.png 추진 화염 포함 (게임에서 교대로 그려 점멸 연출)
  meteor_a/b/c.png  운석 3종 (회전시켜 쓰면 다양해 보인다)
  mine.png        기뢰
실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P ship_scene.py
"""
import bpy
import math
import os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "..", "og-assets", "spacez")
os.makedirs(DIR, exist_ok=True)

RES = 512
SAMPLES = 200


def reset_scene():
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
    sc.render.resolution_x = RES
    sc.render.resolution_y = RES
    sc.render.film_transparent = True
    sc.view_settings.look = 'AgX - Punchy'
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    sc.world = w
    return sc


def top_camera(ortho=3.2):
    """탑다운 — 기체 위에서 내려다본다. +Y 가 화면 위(= 기체 진행 방향)."""
    bpy.ops.object.camera_add(location=(0, 0, 9))
    cam = bpy.context.object
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ortho
    cam.rotation_euler = (0, 0, 0)      # -Z 를 내려다봄
    bpy.context.scene.camera = cam
    return cam


def lights(key=11.0, fill=3.4, rim=9.0):
    """왼쪽 위 키 + 청록 림. 게임 배경이 어두운 우주라 림이 실루엣을 만든다."""
    bpy.ops.object.light_add(type='AREA', location=(-3.2, 3.0, 5.5))
    k = bpy.context.object
    k.data.energy = key * 40
    k.data.size = 4.0
    k.rotation_mode = 'QUATERNION'
    k.rotation_quaternion = (Vector((0, 0, 0)) - k.location).to_track_quat('-Z', 'Y')

    bpy.ops.object.light_add(type='AREA', location=(3.0, -2.4, 3.6))
    f = bpy.context.object
    f.data.energy = fill * 40
    f.data.size = 5.0
    f.data.color = (0.55, 0.72, 1.0)
    f.rotation_mode = 'QUATERNION'
    f.rotation_quaternion = (Vector((0, 0, 0)) - f.location).to_track_quat('-Z', 'Y')

    bpy.ops.object.light_add(type='AREA', location=(0, -3.6, -2.0))
    r = bpy.context.object
    r.data.energy = rim * 40
    r.data.size = 3.0
    r.data.color = (0.35, 0.95, 1.0)
    r.rotation_mode = 'QUATERNION'
    r.rotation_quaternion = (Vector((0, 0, 0)) - r.location).to_track_quat('-Z', 'Y')


def mat(name, color, rough=0.35, metal=0.85, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m


def emit_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    out = nodes["Material Output"]
    for n in list(nodes):
        if n.type == 'BSDF_PRINCIPLED':
            nodes.remove(n)
    e = nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    links.new(e.outputs[0], out.inputs["Surface"])
    return m


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def render_to(name):
    bpy.context.scene.render.filepath = os.path.join(DIR, name)
    bpy.ops.render.render(write_still=True)
    print("  rendered", name)


# ─────────────────────────── 우주선 ───────────────────────────
HULL = None
ACCENT = None
GLASS = None
DARK = None


def build_ship(with_flame=False):
    """스타십 계열 실루엣 — 뾰족한 노즈 + 삼각 델타윙 + 후미 엔진 3기.

    탑다운이라 위에서 봤을 때의 실루엣이 전부다. 옆모습 디테일보다
    (1) 노즈가 어디인지 (2) 날개 폭 (3) 엔진 위치가 즉시 읽혀야 한다.
    """
    global HULL, ACCENT, GLASS, DARK
    HULL = mat("hull", (0.93, 0.95, 0.99), rough=0.34, metal=0.55)
    ACCENT = mat("accent", (0.10, 0.72, 0.92), rough=0.25, metal=0.6,
                 emit=(0.15, 0.92, 1.0), emit_str=3.2)
    GLASS = mat("glass", (0.03, 0.22, 0.36), rough=0.06, metal=0.15,
                emit=(0.30, 0.95, 1.0), emit_str=5.0)
    DARK = mat("dark", (0.10, 0.12, 0.18), rough=0.5, metal=0.4)

    parts = []

    # 동체 — 길쭉한 캡슐. Y+ 가 진행 방향
    bpy.ops.mesh.primitive_cylinder_add(radius=0.30, depth=1.7, vertices=48,
                                        location=(0, -0.05, 0))
    body = bpy.context.object
    body.rotation_euler = (math.radians(90), 0, 0)
    body.data.materials.append(HULL)
    parts.append(smooth(body))

    # 노즈콘 — 원뿔
    bpy.ops.mesh.primitive_cone_add(radius1=0.30, radius2=0.0, depth=0.85,
                                    vertices=48, location=(0, 1.22, 0))
    nose = bpy.context.object
    nose.rotation_euler = (math.radians(-90), 0, 0)
    nose.data.materials.append(HULL)
    parts.append(smooth(nose))

    # 델타윙 — 좌우 대칭 삼각 판
    for sgn in (1, -1):
        verts = [
            (sgn * 0.16, 0.55, 0.0),
            (sgn * 0.92, -0.55, 0.0),
            (sgn * 0.34, -0.70, 0.0),
            (sgn * 0.16, -0.10, 0.0),
        ]
        faces = [[0, 1, 2, 3]]
        me = bpy.data.meshes.new("wing")
        me.from_pydata(verts, [], faces)
        me.update()
        wing = bpy.data.objects.new("wing", me)
        bpy.context.collection.objects.link(wing)
        sol = wing.modifiers.new("S", 'SOLIDIFY')
        sol.thickness = 0.20   # 34px 에서 날개가 반투명하게 뭉개지지 않도록 두껍게
        wing.data.materials.append(HULL)
        parts.append(wing)
        # 윙팁 발광 스트립
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sgn * 0.86, -0.58, 0.06))
        tip = bpy.context.object
        tip.scale = (0.22, 0.055, 0.03)
        tip.rotation_euler = (0, 0, math.radians(sgn * -52))
        tip.data.materials.append(ACCENT)
        parts.append(tip)

    # 캐노피 — 청록 발광 (조종석)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.20, segments=40, ring_count=20,
                                         location=(0, 0.52, 0.19))
    can = bpy.context.object
    can.scale = (0.95, 1.65, 0.60)
    can.data.materials.append(GLASS)
    parts.append(smooth(can))

    # 등줄기 라인 — 기체 중앙 발광 스트립
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.35, 0.28))
    spine = bpy.context.object
    spine.scale = (0.055, 0.46, 0.02)
    spine.data.materials.append(ACCENT)
    parts.append(spine)

    # 엔진 3기 — 후미
    for ex in (-0.34, 0.0, 0.34):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.155, depth=0.30, vertices=32,
                                            location=(ex, -0.94, 0))
        eng = bpy.context.object
        eng.rotation_euler = (math.radians(90), 0, 0)
        eng.data.materials.append(DARK)
        parts.append(smooth(eng))
        # 노즐 내부 발광
        bpy.ops.mesh.primitive_cylinder_add(radius=0.115, depth=0.06, vertices=28,
                                            location=(ex, -1.06, 0))
        gl = bpy.context.object
        gl.rotation_euler = (math.radians(90), 0, 0)
        gl.data.materials.append(emit_mat("nozzle" + str(ex), (0.40, 0.88, 1.0), 3.5))
        parts.append(smooth(gl))

        if with_flame:
            # 추진 화염 — 원뿔 2겹 (안쪽 흰-청, 바깥 청)
            bpy.ops.mesh.primitive_cone_add(radius1=0.135, radius2=0.02, depth=0.95,
                                            vertices=28, location=(ex, -1.58, 0))
            fl = bpy.context.object
            fl.rotation_euler = (math.radians(90), 0, 0)
            fl.data.materials.append(emit_mat("flameIn" + str(ex), (0.80, 0.95, 1.0), 5.5))
            parts.append(smooth(fl))
            bpy.ops.mesh.primitive_cone_add(radius1=0.20, radius2=0.03, depth=1.45,
                                            vertices=28, location=(ex, -1.86, 0))
            fo = bpy.context.object
            fo.rotation_euler = (math.radians(90), 0, 0)
            fo.data.materials.append(emit_mat("flameOut" + str(ex), (0.18, 0.58, 1.0), 2.4))
            parts.append(smooth(fo))
    return parts


def s_ship():
    reset_scene(); top_camera(3.15); lights()
    build_ship(False)
    render_to("ship.png")


def s_ship_thrust():
    reset_scene(); top_camera(3.9); lights()
    build_ship(True)
    render_to("ship_thrust.png")


# ─────────────────────────── 위협 오브젝트 ───────────────────────────
def rock(seed_scale, strength, color, rough=0.95):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0)
    o = bpy.context.object
    d = o.modifiers.new("D", 'DISPLACE')
    t = bpy.data.textures.new("rk%.2f" % seed_scale, 'CLOUDS')
    t.noise_scale = seed_scale
    d.texture = t
    d.strength = strength
    m = mat("rock", color, rough=rough, metal=0.0)
    # 표면 요철
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    nz = nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 9.0
    nz.inputs["Detail"].default_value = 10.0
    bmp = nodes.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = 0.45
    links.new(nz.outputs["Fac"], bmp.inputs["Height"])
    links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
    o.data.materials.append(m)
    return smooth(o)


def s_meteors():
    for i, (sc, st, col) in enumerate([
        (0.55, 0.34, (0.30, 0.24, 0.20)),
        (0.85, 0.26, (0.26, 0.22, 0.20)),
        (0.40, 0.40, (0.34, 0.27, 0.21)),
    ]):
        reset_scene(); top_camera(2.55); lights(key=5.0, rim=2.6)
        o = rock(sc, st, col)
        o.rotation_euler = (math.radians(20 + i * 40), math.radians(15 + i * 30), 0)
        render_to("meteor_%s.png" % "abc"[i])


def s_mine():
    reset_scene(); top_camera(2.9); lights(key=4.5, rim=3.2)
    core = mat("mineCore", (0.12, 0.13, 0.17), rough=0.4, metal=0.85)
    warn = emit_mat("mineWarn", (1.0, 0.22, 0.18), 9.0)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.72)
    c = bpy.context.object
    c.data.materials.append(core)
    smooth(c)
    # 스파이크
    import random
    rnd = random.Random(4)
    for _ in range(14):
        a = rnd.uniform(0, math.pi * 2)
        b = rnd.uniform(-1, 1)
        z = b
        rxy = math.sqrt(max(0.0, 1 - z * z))
        d = Vector((math.cos(a) * rxy, math.sin(a) * rxy, z))
        bpy.ops.mesh.primitive_cone_add(radius1=0.12, radius2=0.0, depth=0.42,
                                        vertices=14, location=d * 0.85)
        sp = bpy.context.object
        sp.rotation_mode = 'QUATERNION'
        sp.rotation_quaternion = d.to_track_quat('Z', 'Y')
        sp.data.materials.append(core)
        smooth(sp)
    # 경고등 밴드
    bpy.ops.mesh.primitive_torus_add(major_radius=0.74, minor_radius=0.055,
                                     major_segments=64, minor_segments=12)
    ring = bpy.context.object
    ring.data.materials.append(warn)
    render_to("mine.png")


ALL = [s_ship, s_ship_thrust, s_meteors, s_mine]

for fn in ALL:
    print("==", fn.__name__)
    fn()

print("SPACEZ ASSETS DONE ->", DIR)
