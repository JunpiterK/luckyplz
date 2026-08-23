# -*- coding: utf-8 -*-
"""터보펌프 시험 리그 → glTF (2026-08-23).

코덱스 제1부 Mission 1-2 「터보펌프의 악몽」의 무대.

**엔진에서 실시간으로 조작할 수 있게 이름을 붙인다.** 이게 이 씬의 핵심이다:
  · `rot_*`   회전체 — 축·인듀서·임펠러·터빈. RPM 에 맞춰 JS 가 돌린다
  · `ind_*`   인듀서 변형 — 플레이어 선택에 따라 보이거나 숨는다
  · `blade_*` 임펠러 블레이드 — 각도 슬라이더에 맞춰 JS 가 기울인다
  · `cavpt`   캐비테이션 기포가 생길 지점(입구). 보이지 않는 기준점

절차적 노이즈는 glTF 로 안 넘어가므로 디테일은 기하와 재질 수로 낸다
([[orbit_lab]] 의 방 조형 기준과 같다).

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P pump_rig.py
출력: public/assets/deltav/pumprig.glb
"""
import bpy
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "public", "assets", "deltav")
os.makedirs(OUT, exist_ok=True)


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, base, rough=0.4, metal=0.0, emit=None, emit_str=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = 'BLEND'
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def bev(o, w=0.004, seg=2):
    md = o.modifiers.new("b", 'BEVEL')
    md.width = w
    md.segments = seg
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(40)
    return smooth(o)


def cyl(loc, r, d, m, rot=(0, 0, 0), verts=48, name=None, do_bev=True):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, vertices=verts, location=loc)
    o = bpy.context.object
    o.rotation_euler = rot
    o.data.materials.append(m)
    if name:
        o.name = name
    return bev(o) if do_bev else smooth(o)


def box(loc, scale, m, rot=(0, 0, 0), name=None, w=0.006):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.scale = scale
    o.rotation_euler = rot
    o.data.materials.append(m)
    if name:
        o.name = name
    return bev(o, w)


def torus(loc, R, r, m, rot=(0, 0, 0), name=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r,
                                     major_segments=48, minor_segments=14, location=loc)
    o = bpy.context.object
    o.rotation_euler = rot
    o.data.materials.append(m)
    if name:
        o.name = name
    return smooth(o)


def sphere(loc, r, m, scale=(1, 1, 1), name=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=40, ring_count=20, location=loc)
    o = bpy.context.object
    o.scale = scale
    o.data.materials.append(m)
    if name:
        o.name = name
    return smooth(o)


def build():
    """펌프는 축이 세로(Z). 위가 터빈, 아래가 인듀서 입구다."""
    fresh()
    INCO = mat("inco", (0.44, 0.42, 0.40), rough=0.30, metal=1.0)     # 니켈합금
    ALU = mat("alu", (0.56, 0.58, 0.61), rough=0.34, metal=1.0)
    STEEL = mat("steel", (0.47, 0.49, 0.53), rough=0.24, metal=1.0)
    ANOD = mat("anod", (0.085, 0.09, 0.105), rough=0.42, metal=0.55)
    BRASS = mat("brass", (0.72, 0.58, 0.24), rough=0.30, metal=1.0)
    COPPER = mat("copper", (0.71, 0.36, 0.17), rough=0.24, metal=1.0)
    FROST = mat("frost", (0.80, 0.86, 0.92), rough=0.86)              # 착상된 저온 배관
    RUBBER = mat("rubber", (0.055, 0.058, 0.065), rough=0.88)
    HAZ = mat("haz", (0.62, 0.50, 0.10), rough=0.55)
    LED_G = mat("led_g", (0.1, 0.5, 0.2), rough=0.3, emit=(0.15, 1.0, 0.45), emit_str=6.0)
    STRIP = mat("strip", (0.4, 0.3, 0.05), rough=0.5,
                emit=(1.0, 0.62, 0.08), emit_str=2.0)

    # ── 받침 ──
    box((0, 0, 0.05), (2.6, 2.6, 0.10), ANOD, name="pad")
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            box((sx, sy, 0.42), (0.16, 0.16, 0.64), ALU)
            box((sx, sy, 0.12), (0.34, 0.34, 0.06), STEEL)
    box((0, 0, 0.77), (2.3, 2.3, 0.10), ALU, name="table")
    for sy in (-1.16, 1.16):
        box((0, sy, 0.84), (2.3, 0.06, 0.05), HAZ)

    # ── 볼류트(펌프 하우징) — 임펠러를 감싸는 달팽이 ──
    cyl((0, 0, 1.16), 0.40, 0.30, INCO, name="volute")
    torus((0, 0, 1.16), 0.40, 0.115, INCO, name="volute_ring")
    for a in range(20):                       # 하우징 볼트
        ang = math.pi * 2 * a / 20
        cyl((math.cos(ang) * 0.44, math.sin(ang) * 0.44, 1.31),
            0.019, 0.05, STEEL, verts=10)
    # 토출 노즐 — 볼류트 접선 방향으로 빠진다
    cyl((0.52, 0.30, 1.16), 0.115, 0.62, INCO,
        rot=(math.radians(90), 0, math.radians(-30)), verts=32, name="outlet")
    cyl((0.74, 0.42, 1.16), 0.145, 0.05, BRASS,
        rot=(math.radians(90), 0, math.radians(-30)), verts=32)
    cyl((0.92, 0.53, 1.16), 0.085, 0.40, FROST,
        rot=(math.radians(90), 0, math.radians(-30)), verts=24)

    # ── 입구(흡입) 배관 — 아래로. 착상된 저온 라인 ──
    cyl((0, 0, 0.86), 0.19, 0.30, FROST, name="inlet")
    cyl((0, 0, 0.68), 0.215, 0.06, ALU, verts=32)
    for i in range(4):
        cyl((0, 0, 0.60 - i * 0.10), 0.20, 0.055, FROST, verts=32)   # 벨로우즈
    box((0, 0, 0.30), (0.44, 0.44, 0.10), ANOD)

    # ── 회전체 ──  이름이 `rot_` 로 시작하면 JS 가 RPM 에 맞춰 돌린다
    cyl((0, 0, 1.72), 0.055, 1.50, STEEL, verts=24, name="rot_shaft")

    # 인듀서 — 두 변형을 겹쳐 두고 엔진이 골라 보여 준다
    for tag, blades, pitch, length in (("short", 3, 26.0, 0.16), ("long", 3, 20.0, 0.30)):
        hub = cyl((0, 0, 1.00 - length * 0.5), 0.052, length, INCO,
                  verts=24, name="rot_ind_%s_hub" % tag)
        for b in range(blades):
            ang = math.pi * 2 * b / blades
            box((math.cos(ang) * 0.115, math.sin(ang) * 0.115, 1.00 - length * 0.5),
                (0.20, 0.028, length * 0.92), INCO,
                rot=(0, 0, ang + math.radians(pitch)),
                name="rot_ind_%s_b%d" % (tag, b), w=0.003)

    # 임펠러 — 블레이드는 각도 슬라이더에 맞춰 JS 가 기울인다
    cyl((0, 0, 1.16), 0.075, 0.26, INCO, verts=32, name="rot_imp_hub")
    cyl((0, 0, 1.04), 0.34, 0.022, INCO, verts=48, name="rot_imp_shroud")
    for b in range(7):
        ang = math.pi * 2 * b / 7
        box((math.cos(ang) * 0.20, math.sin(ang) * 0.20, 1.14),
            (0.27, 0.020, 0.17), INCO, rot=(0, 0, ang + math.radians(28)),
            name="rot_blade_%d" % b, w=0.003)

    # 베어링 하우징 — 실측 대상
    cyl((0, 0, 1.44), 0.14, 0.20, ALU, verts=32, name="brg_house")
    torus((0, 0, 1.44), 0.145, 0.022, STEEL)
    for i in range(3):
        cyl((0, 0, 1.38 + i * 0.06), 0.155, 0.012, COPPER, verts=32)   # 냉각 핀
    cyl((0, 0, 1.62), 0.10, 0.16, ANOD, verts=28, name="seal")         # 실 패키지

    # 터빈 — 위쪽. 가스발생기가 여기를 돌린다
    cyl((0, 0, 1.92), 0.26, 0.16, INCO, verts=40, name="rot_turb_disk")
    for b in range(24):
        ang = math.pi * 2 * b / 24
        box((math.cos(ang) * 0.30, math.sin(ang) * 0.30, 1.92),
            (0.075, 0.012, 0.11), INCO, rot=(0, 0, ang + math.radians(34)),
            name="rot_turb_b%d" % b, w=0.002)
    cyl((0, 0, 2.06), 0.36, 0.13, ANOD, verts=40, name="turb_case")
    torus((0, 0, 2.06), 0.37, 0.055, ANOD)
    # 가스 인입 — 뜨거운 쪽이라 구리·황동
    cyl((-0.52, 0, 2.06), 0.075, 0.42, COPPER,
        rot=(0, math.radians(90), 0), verts=24, name="gasin")
    cyl((-0.74, 0, 2.06), 0.10, 0.05, BRASS, rot=(0, math.radians(90), 0), verts=24)
    # 배기
    cyl((0, 0, 2.24), 0.20, 0.24, ANOD, verts=32)
    cyl((0, 0, 2.44), 0.16, 0.20, ANOD, verts=32, name="exhaust")

    # ── 계측 ──
    for i, (ang, nm) in enumerate(((0.9, "p_in"), (2.2, "p_out"), (4.0, "vib"))):
        gx, gy = math.cos(ang) * 0.62, math.sin(ang) * 0.62
        cyl((gx, gy, 1.52), 0.011, 0.34, STEEL,
            rot=(math.radians(90) * math.sin(ang), math.radians(90) * math.cos(ang), 0),
            verts=10)
        sphere((gx, gy, 1.70), 0.055, ALU, name="gauge_%s" % nm)
        cyl((gx, gy, 1.74), 0.042, 0.012, LED_G, verts=20)
    # 계측 스탠드
    box((-0.95, -0.95, 1.20), (0.30, 0.22, 0.86), ANOD)
    box((-0.95, -1.07, 1.60), (0.28, 0.03, 0.05), STRIP)

    # 케이블 다발
    for i in range(5):
        cyl((-0.70 + i * 0.04, -0.72 - i * 0.02, 1.02), 0.014, 0.72, RUBBER,
            rot=(math.radians(58), 0, math.radians(20)), verts=8)

    path = os.path.join(OUT, "pumprig.glb")
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', use_selection=False,
        export_apply=True, export_cameras=False, export_lights=False,
        export_yup=True, export_texcoords=True, export_normals=True,
        export_materials='EXPORT')
    print("  exported pumprig (%.0f KB)" % (os.path.getsize(path) / 1024))


if __name__ == "__main__":
    build()
    print("PUMP RIG DONE ->", os.path.abspath(OUT))
