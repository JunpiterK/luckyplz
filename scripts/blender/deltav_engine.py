# -*- coding: utf-8 -*-
"""델타-브이 엔진 — 개발 단계별 형상 + 클러스터 배치 (2026-08-22).

운영자 요청: 엔진 하나를 계속 발전시키면서, 여러 개를 클러스터로 묶어
추진체를 만드는 시험도 하고, 그래픽도 그럴듯하게.

실제 역사와 같은 축을 쓴다 (멀린 1A → 1C → 1D):
  v1 삭마냉각 — 연소실 안쪽을 태워 없애며 식힌다. 단순하지만 재사용 불가,
     그리고 **종료 후 잔류 추력이 적다**
  v2 재생냉각 — 추진제를 연소실 벽에 감아 돌려 식힌다. 성능이 오르지만
     종료 후 **잔류 추력이 남는다**(팰컨1 3호 단 분리 충돌의 실제 원인)
  v3 개량형 — 터보펌프 출력과 챔버 압력을 올려 추력을 크게 키운 형태

클러스터는 **아래에서 본 배치도**로 렌더한다. 1기 · 9기(옥타웹) · 27기.
배치 자체가 정보다 — 가운데 1기 + 바깥 8기 구조가 엔진 아웃 시 추력
불균형을 줄인다.

실사 6원칙 적용: 베벨 · 거칠기 흔들기 · 큰 소프트 키 · 접지 그림자 ·
피사계심도 · 열변색.

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P deltav_engine.py
출력: scripts/og-assets/deltav/eng_v*.png · clus_*.png
"""
import bpy
import math
import os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "..", "og-assets", "deltav")
os.makedirs(DIR, exist_ok=True)


def reset(res=(560, 620), samples=400):
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
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = 0.12
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = 'EASING'
    mp = nt.nodes.new("ShaderNodeMapping")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    ramp.color_ramp.elements[0].color = (0.010, 0.013, 0.022, 1)
    ramp.color_ramp.elements[1].color = (0.10, 0.12, 0.16, 1)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], grad.inputs['Vector'])
    nt.links.new(grad.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    bg.inputs['Strength'].default_value = 1.0
    sc.world = w
    return sc


def pbr(name, base, rough=0.35, metal=1.0, aniso=0.0, rough_var=0.0,
        noise_scale=120.0, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if "Anisotropic" in b.inputs:
        b.inputs["Anisotropic"].default_value = aniso
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    if rough_var > 0:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = noise_scale
        tex.inputs["Detail"].default_value = 6.0
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.3
        mr.inputs["From Max"].default_value = 0.7
        mr.inputs["To Min"].default_value = max(0.02, rough - rough_var)
        mr.inputs["To Max"].default_value = min(1.0, rough + rough_var)
        nt.links.new(tex.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.07
        nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def bevel(o, w=0.006, seg=3):
    md = o.modifiers.new("b", 'BEVEL')
    md.width = w
    md.segments = seg
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(38)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def cyl(loc, r, d, m, rot=(0, 0, 0), verts=48, bev=0.006):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, vertices=verts, location=loc)
    o = bpy.context.object
    o.rotation_euler = rot
    o.data.materials.append(m)
    return bevel(o, bev) if bev else o


def cone(loc, r1, r2, d, m, rot=(0, 0, 0), verts=64):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=d, vertices=verts,
                                    location=loc)
    o = bpy.context.object
    o.rotation_euler = rot
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def torus(loc, R, r, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r,
                                     major_segments=56, minor_segments=14, location=loc)
    o = bpy.context.object
    o.rotation_euler = rot
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def cam(loc, look, lens=70, fstop=3.2):
    bpy.ops.object.camera_add(location=loc)
    c = bpy.context.object
    c.data.lens = lens
    d = Vector(look) - Vector(loc)
    c.rotation_mode = 'QUATERNION'
    c.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    c.data.dof.use_dof = True
    c.data.dof.focus_distance = d.length
    c.data.dof.aperture_fstop = fstop
    bpy.context.scene.camera = c
    return c


def area(loc, power, size, color=(1, 1, 1), look=(0, 0, 0)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    L = bpy.context.object
    L.data.energy = power
    L.data.size = size
    L.data.color = color
    d = Vector(look) - Vector(loc)
    L.rotation_mode = 'QUATERNION'
    L.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    return L


def studio(key=600, look=(0, 0, 0.9), sc=1.0):
    area((2.9 * sc, -2.2 * sc, 3.6 * sc), key, 4.2 * sc, (1.0, 0.96, 0.90), look)
    area((-3.4 * sc, -1.4 * sc, 1.8 * sc), key * 0.28, 5.0 * sc, (0.52, 0.70, 1.0), look)
    area((-0.4 * sc, 3.4 * sc, 2.6 * sc), key * 0.40, 3.6 * sc, (0.78, 0.90, 1.0), look)


def floor(color=(0.028, 0.033, 0.045), rough=0.40):
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    p = bpy.context.object
    m = bpy.data.materials.new("fl")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    p.data.materials.append(m)
    return p


def render(name):
    bpy.context.scene.render.filepath = os.path.join(DIR, name)
    bpy.ops.render.render(write_still=True)
    print("  rendered", name)


# ═══════════════════════ 엔진 3세대 ═══════════════════════
def engine(stage, fname):
    """stage 1 삭마냉각 · 2 재생냉각 · 3 개량형.

    세대가 오를수록 노즐이 커지고 배관이 늘고 마감이 좋아진다.
    한눈에 '발전했다' 가 읽혀야 한다.
    """
    reset()
    STEEL = pbr("st", (0.72, 0.74, 0.78), rough=0.26, metal=1.0, aniso=0.7,
                rough_var=0.08, noise_scale=180)
    DARK = pbr("dk", (0.10, 0.105, 0.125), rough=0.44, metal=0.6, rough_var=0.08)
    COP = pbr("cu", (0.74, 0.40, 0.20), rough=0.24, metal=1.0, rough_var=0.09, noise_scale=140)
    ABL = pbr("ab", (0.20, 0.16, 0.13), rough=0.78, metal=0.05, rough_var=0.12, noise_scale=70)
    GOLD = pbr("gd", (0.88, 0.70, 0.30), rough=0.30, metal=1.0, rough_var=0.07)
    HOT = pbr("ht", (0.30, 0.12, 0.06), rough=0.42, metal=0.85, rough_var=0.10,
              noise_scale=90)

    # 세대별 치수
    spec = {1: dict(er=0.60, el=1.05, cr=0.26, cl=0.52, pumps=1, lines=4, bell=ABL),
            2: dict(er=0.70, el=1.25, cr=0.28, cl=0.58, pumps=1, lines=10, bell=STEEL),
            3: dict(er=0.88, el=1.55, cr=0.32, cl=0.66, pumps=2, lines=14, bell=STEEL)}[stage]

    # 종형 노즐 — 위가 좁고 아래가 벌어진다
    noz = cone((0, 0, 0.72), spec['er'], spec['cr'] * 0.95, spec['el'], spec['bell'])
    noz.rotation_euler = (math.radians(180), 0, 0)
    # 연소실
    cyl((0, 0, 1.52), spec['cr'], spec['cl'], HOT if stage == 1 else STEEL)
    # 인젝터 헤드
    cyl((0, 0, 1.90), spec['cr'] * 1.25, 0.24, DARK)
    torus((0, 0, 1.78), spec['cr'] * 1.28, 0.035, GOLD)

    # 냉각 배관 — 재생냉각 세대부터 노즐을 감는다. 세대가 오르면 더 촘촘하다
    if stage >= 2:
        for i in range(spec['lines']):
            t = i / float(spec['lines'] - 1)
            z = 0.30 + t * 1.05
            rr = spec['cr'] * 0.95 + (spec['er'] - spec['cr'] * 0.95) * (1 - (z - 0.30) / 1.05)
            torus((0, 0, z), rr * 1.02, 0.016, COP)
    else:
        # 삭마냉각은 안쪽을 태워 없앤다 — 표면이 거칠고 그을려 있다
        torus((0, 0, 1.20), spec['er'] * 0.72, 0.022, DARK)

    # 터보펌프
    for k in range(spec['pumps']):
        ang = math.pi * 0.5 + k * math.pi
        px, py = math.cos(ang) * (spec['cr'] * 1.9), math.sin(ang) * (spec['cr'] * 1.9)
        cyl((px, py, 1.62), 0.15, 0.38, STEEL)
        cyl((px, py, 1.86), 0.09, 0.14, DARK)
        # 공급 배관
        cyl((px * 0.55, py * 0.55, 1.44), 0.045, 0.42, STEEL,
            rot=(math.radians(90) if abs(py) > abs(px) else 0, 0, 0))

    # 짐벌 마운트 — 방향을 트는 관절. 3세대는 더 굵다
    cyl((0, 0, 2.08), spec['cr'] * (0.6 if stage < 3 else 0.8), 0.16, DARK)

    # 1차 구도는 노즐 아래와 터보펌프 위가 프레임 밖으로 잘렸다.
    # 물체는 z 0.2~2.2, 반지름 0.9 까지 뻗으므로 그만큼 물러선다.
    cam((2.85, -3.75, 2.10), (0, 0, 1.18), lens=45, fstop=5.6)
    studio(620, look=(0, 0, 1.05))
    floor()
    render(fname)


# ═══════════════════════ 클러스터 배치 ═══════════════════════
def cluster(n, fname):
    """아래에서 본 엔진 배치도. 배치 자체가 정보다 —
       가운데 1기 + 바깥 원환 구조가 엔진 아웃 시 추력 불균형을 줄인다."""
    reset(res=(620, 620), samples=380)
    PLATE = pbr("pl", (0.16, 0.17, 0.20), rough=0.52, metal=0.75, rough_var=0.10,
                noise_scale=40)
    RIM = pbr("rm", (0.66, 0.68, 0.72), rough=0.24, metal=1.0, aniso=0.6, rough_var=0.06)
    BELL = pbr("bl", (0.58, 0.60, 0.64), rough=0.28, metal=1.0, rough_var=0.09, noise_scale=150)
    THR = pbr("th", (0.045, 0.045, 0.055), rough=0.80, metal=0.1)

    # 배치 — 1 / 9(가운데 1 + 바깥 8) / 27(가운데 1 + 8 + 18)
    if n == 1:
        pos, R = [(0, 0)], 0.95
    elif n == 9:
        pos = [(0, 0)]
        for i in range(8):
            a = math.pi * 2 * i / 8
            pos.append((math.cos(a) * 1.62, math.sin(a) * 1.62))
        R = 2.55
    else:
        pos = [(0, 0)]
        for i in range(8):
            a = math.pi * 2 * i / 8
            pos.append((math.cos(a) * 1.45, math.sin(a) * 1.45))
        for i in range(18):
            a = math.pi * 2 * i / 18 + 0.09
            pos.append((math.cos(a) * 2.72, math.sin(a) * 2.72))
        R = 3.55

    er = 0.62 if n <= 9 else 0.52
    # 추력판
    cyl((0, 0, -0.16), R, 0.30, PLATE, verts=96, bev=0.02)
    torus((0, 0, -0.02), R, 0.055, RIM)
    for (x, y) in pos:
        b = cone((x, y, 0.30), er, er * 0.40, 0.60, BELL)
        b.rotation_euler = (math.radians(180), 0, 0)
        cyl((x, y, 0.03), er * 0.42, 0.10, THR)

    # 고정 거리로 두니 27기에서 추력판 가장자리가 잘렸다.
    # 배치 반지름에 비례해 물러선다 (렌즈 40mm 기준 여유 1.25 배).
    cam((0, -R * 0.34, R * 2.95 + 1.2), (0, 0, 0.2), lens=40, fstop=9.0)
    area((R * 1.3, -R * 1.1, R * 2.4), 700 + R * 260, R * 2.2,
         (1.0, 0.96, 0.90), (0, 0, 0.3))
    area((-R * 1.5, -R * 0.7, R * 1.8), 260 + R * 80, R * 2.6,
         (0.52, 0.70, 1.0), (0, 0, 0.3))
    area((0, R * 1.5, R * 2.0), 340 + R * 110, R * 2.0,
         (0.80, 0.90, 1.0), (0, 0, 0.3))
    floor((0.020, 0.024, 0.033), rough=0.45)
    render(fname)


if __name__ == "__main__":
    for st in (1, 2, 3):
        print("== engine v%d" % st)
        engine(st, "eng_v%d.png" % st)
    for n in (1, 9, 27):
        print("== cluster %d" % n)
        cluster(n, "clus_%02d.png" % n)
    print("DELTA-V ENGINE DONE ->", DIR)
