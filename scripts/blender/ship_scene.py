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
    """실제 SpaceX Starship 형상.

    탑다운 평면도라 위에서 본 실루엣이 전부다. 스타십을 스타십으로 읽게 하는
    요소는 다음 다섯이며, 하나라도 빠지면 일반 SF 전투기가 된다.
      1. 지름이 일정한 스테인리스 원통 동체 (테이퍼 없음, 비율 약 1:5.5)
      2. 둥근 탄젠트 오자이브 노즈
      3. 후퇴익이 아니라 플랩 4장 — 노즈 아래 전방 2장(작다) + 기저부 2장(크다)
      4. 한쪽 면을 덮는 검은 내열타일
      5. 기저부 랩터 엔진 클러스터. 조종석 캐노피는 없다
    """
    global HULL, ACCENT, GLASS, DARK
    # 스테인리스 스틸 — 스타십의 상징. 무광에 가까운 금속
    HULL = mat("hull", (0.905, 0.925, 0.955), rough=0.34, metal=0.42)
    # 내열타일. 순검정이면 어두운 우주 배경에서 실루엣 절반이 사라져
    # 짙은 차콜블루로 올리고 러프니스를 낮춰 림라이트를 받게 한다
    TILE = mat("tile", (0.150, 0.160, 0.195), rough=0.52, metal=0.12)
    ACCENT = mat("accent", (0.12, 0.74, 0.94), rough=0.28, metal=0.5,
                 emit=(0.15, 0.92, 1.0), emit_str=1.6)
    DARK = mat("dark", (0.13, 0.14, 0.18), rough=0.40, metal=0.55)

    # 금속은 반사할 환경이 없으면 검게 렌더된다 (v2 실패 원인).
    # film_transparent 라 배경에는 안 보이고 반사·조명에만 기여한다.
    _w = bpy.context.scene.world.node_tree.nodes["Background"]
    _w.inputs[0].default_value = (0.42, 0.50, 0.64, 1.0)
    _w.inputs[1].default_value = 0.55

    R = 0.26           # 동체 반지름 (실제 스타십 9m 지름에 대응)
    Y0 = -1.34         # 기저부
    Y1 = 0.84          # 원통 끝 = 노즈 시작
    NOSE = 0.72        # 노즈 길이. 실제 스타십은 전장의 약 25% (50m 중 12m)
    SEG = 48           # 원주 분할. 4의 배수여야 x=0 을 걸치는 면이 없다

    parts = []

    # ── 동체 + 노즈: 회전체를 직접 생성 ──
    # 탄젠트 오자이브: r(t) = sqrt(rho^2 - t^2) + R - rho,  t 는 노즈 밑에서의 거리
    rho = (R * R + NOSE * NOSE) / (2.0 * R)
    prof = [(Y0, R), (Y1, R)]
    NSAMP = 26
    for i in range(1, NSAMP + 1):
        t = NOSE * i / NSAMP
        rr = math.sqrt(max(0.0, rho * rho - t * t)) + R - rho
        prof.append((Y1 + t, max(0.0, rr)))

    verts, faces, mat_idx = [], [], []
    rings = []
    for (yy, rr) in prof:
        ring = []
        if rr <= 1e-5:
            ring = [len(verts)]
            verts.append((0.0, yy, 0.0))
        else:
            for k in range(SEG):
                a = math.pi * 2 * k / SEG
                ring.append(len(verts))
                verts.append((math.cos(a) * rr, yy, math.sin(a) * rr))
        rings.append(ring)

    def face_side(idxs):
        """면 중심의 x 부호 → 0=hull, 1=tile."""
        cx = sum(verts[i][0] for i in idxs) / len(idxs)
        return 1 if cx > 0.0 else 0

    for a in range(len(rings) - 1):
        lo, hi = rings[a], rings[a + 1]
        if len(hi) == 1:                      # 노즈 끝: 삼각 부채꼴
            for k in range(SEG):
                f = [lo[k], lo[(k + 1) % SEG], hi[0]]
                faces.append(f); mat_idx.append(face_side(f))
        else:
            for k in range(SEG):
                f = [lo[k], lo[(k + 1) % SEG], hi[(k + 1) % SEG], hi[k]]
                faces.append(f); mat_idx.append(face_side(f))
    # 기저부 뚜껑
    faces.append(list(reversed(rings[0]))); mat_idx.append(0)

    me = bpy.data.meshes.new("starship_hull")
    me.from_pydata(verts, [], faces)
    me.update()
    hull = bpy.data.objects.new("starship_hull", me)
    bpy.context.collection.objects.link(hull)
    hull.data.materials.append(HULL)
    hull.data.materials.append(TILE)
    for i, p in enumerate(hull.data.polygons):
        p.use_smooth = True
        p.material_index = mat_idx[i] if i < len(mat_idx) else 0
    parts.append(hull)

    # ── 타일 경계선(chine) — 밝은 청록 실선.
    #    어두운 타일 면이 배경에 먹히지 않도록 실루엣을 잡아주는 장치다 ──
    for sx in (1, -1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sx * R * 1.005, (Y0 + Y1) / 2, 0))
        ln = bpy.context.object
        ln.scale = (0.010, (Y1 - Y0) * 0.96, 0.020)
        ln.data.materials.append(ACCENT)
        parts.append(ln)

    # ── 플랩 4장 ──
    def flap(sx, y0, y1, span, thick, tiled, sweep):
        """아래는 넓고 위는 좁은 육면체. 측면 베벨이 림라이트를 받아 두께가 읽힌다.
           sweep: 바깥 끝을 뒤로 눕히는 양 (전방 플랩의 후퇴각)."""
        xi = R * 0.86 * sx
        xo = span * sx
        bot = [(xi, y0, -thick), (xo, y0 + sweep, -thick),
               (xo, y1 - sweep * 0.75, -thick), (xi, y1, -thick)]
        ins = 0.045
        top = [(xi, y0 + ins, thick), (xo - ins * sx, y0 + sweep + ins, thick),
               (xo - ins * sx, y1 - sweep * 0.75 - ins, thick), (xi, y1 - ins, thick)]
        vs = bot + top
        fs = [[0, 1, 2, 3], [7, 6, 5, 4],
              [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]]
        m2 = bpy.data.meshes.new("flap")
        m2.from_pydata(vs, [], fs)
        m2.update()
        ob = bpy.data.objects.new("flap", m2)
        bpy.context.collection.objects.link(ob)
        ob.data.materials.append(TILE if tiled else HULL)
        parts.append(ob)

    # 전방 플랩 — 노즈 바로 아래, 작다
    for sx in (1, -1):
        flap(sx, Y1 - 0.36, Y1 + 0.14, 0.58, 0.075, sx > 0, 0.17)
    # 후방 플랩 — 기저부, 크다
    for sx in (1, -1):
        flap(sx, Y0 + 0.03, Y0 + 0.84, 0.84, 0.095, sx > 0, 0.20)

    # ── 랩터 엔진 6기 ──
    for k in range(6):
        a = math.pi * 2 * k / 6
        bpy.ops.mesh.primitive_cone_add(radius1=R * 0.32, radius2=R * 0.21, depth=0.20,
                                        vertices=24,
                                        location=(math.cos(a) * R * 0.56, Y0 - 0.09,
                                                  math.sin(a) * R * 0.56))
        eng = bpy.context.object
        eng.rotation_euler = (math.radians(90), 0, 0)
        eng.data.materials.append(DARK)
        parts.append(smooth(eng))

    # ── 기저부 링 — 소형 표시에서 '아래쪽'을 즉시 알려준다 ──
    bpy.ops.mesh.primitive_torus_add(major_radius=R * 1.01, minor_radius=0.020,
                                     major_segments=48, minor_segments=10,
                                     location=(0, Y0 + 0.05, 0))
    ring = bpy.context.object
    ring.rotation_euler = (math.radians(90), 0, 0)
    ring.data.materials.append(ACCENT)
    parts.append(ring)

    if with_flame:
        for k in range(3):
            bpy.ops.mesh.primitive_cone_add(radius1=R * 0.34, radius2=0.02, depth=0.9,
                                            vertices=24,
                                            location=((k - 1) * R * 0.50, Y0 - 0.60, 0))
            fl = bpy.context.object
            fl.rotation_euler = (math.radians(90), 0, 0)
            fl.data.materials.append(emit_mat("fl%d" % k, (0.80, 0.95, 1.0), 4.0))
            parts.append(smooth(fl))
    return parts


def s_ship():
    reset_scene(); top_camera(3.45); lights()
    build_ship(False)
    render_to("ship.png")


def s_ship_thrust():
    reset_scene(); top_camera(4.4); lights()
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
