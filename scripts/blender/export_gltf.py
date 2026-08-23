# -*- coding: utf-8 -*-
"""Blender 씬 → glTF(.glb) 내보내기 (2026-08-23).

**3D 모델의 단일 원본은 여전히 Blender 다.** 달라진 것은 소비처다 —
프리렌더 PNG 대신 `.glb` 를 내보내 Babylon 이 **실시간으로** 렌더한다.
같은 모델이 실시간 조명·그림자·카메라 이동·상호작용을 갖게 된다.

내보낼 때 주의:
  · **재질은 Principled BSDF 만 쓴다.** glTF 는 PBR 표준이라 Principled 의
    Base Color/Metallic/Roughness/Emission 만 그대로 건너간다. 절차적 노이즈
    텍스처는 **굽지 않으면 사라진다**(현재 모델은 굽지 않고 상수값으로 간다)
  · 카메라·조명은 내보내지 않는다 — 엔진 쪽에서 실시간으로 만든다
  · 스케일 1 = 1m 로 맞춘다. 물리·카메라 거리 계산이 실제 단위로 돌아간다

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P export_gltf.py
출력: public/assets/deltav/*.glb
"""
import bpy
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "public", "assets", "deltav")
os.makedirs(OUT, exist_ok=True)


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, base, rough=0.4, metal=0.0, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def bevel(o, w=0.004, seg=2):
    md = o.modifiers.new("b", 'BEVEL')
    md.width = w
    md.segments = seg
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(38)
    smooth(o)
    return o


def cyl(loc, r, d, m, rot=(0, 0, 0), verts=48, name=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, vertices=verts, location=loc)
    o = bpy.context.object
    o.rotation_euler = rot
    o.data.materials.append(m)
    if name:
        o.name = name
    return bevel(o)


def cone(loc, r1, r2, d, m, rot=(0, 0, 0), verts=64, name=None):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=d, vertices=verts,
                                    location=loc)
    o = bpy.context.object
    o.rotation_euler = rot
    o.data.materials.append(m)
    if name:
        o.name = name
    return smooth(o)


def box(loc, scale, m, rot=(0, 0, 0), name=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.scale = scale
    o.rotation_euler = rot
    o.data.materials.append(m)
    if name:
        o.name = name
    return bevel(o, 0.01)


def torus(loc, R, r, m, rot=(0, 0, 0), name=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r,
                                     major_segments=48, minor_segments=12, location=loc)
    o = bpy.context.object
    o.rotation_euler = rot
    o.data.materials.append(m)
    if name:
        o.name = name
    return smooth(o)


def export(name):
    """카메라·조명은 빼고 메시만. 조명은 엔진에서 실시간으로 만든다."""
    path = os.path.join(OUT, name + ".glb")
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        use_selection=False,
        export_apply=True,          # 모디파이어(베벨) 적용
        export_cameras=False,
        export_lights=False,
        export_yup=True,            # glTF 표준: Y 가 위
        export_texcoords=True,
        export_normals=True,
        export_materials='EXPORT',
    )
    print("  exported %s (%.0f KB)" % (name, os.path.getsize(path) / 1024))


# ═══════════════ 멀린 1A 엔진 — 미션 1-1 의 주인공 ═══════════════
def merlin_1a():
    """가스발생기 사이클, 삭마냉각. 코덱스 제1부의 그 엔진.

    실제 치수에 맞춘다 (1 단위 = 1 m):
      노즐 출구 지름 약 0.9 m, 연소실 지름 약 0.3 m, 전체 높이 약 2.3 m
    미션에서 **연소실 벽이 붉게 달아오르고 균열이 가는** 연출을 해야 하므로
    연소실을 별도 메시(`chamber`)로 분리해 이름을 붙인다.
    """
    fresh()
    STEEL = mat("steel", (0.62, 0.645, 0.68), rough=0.30, metal=1.0)
    DARK = mat("dark", (0.085, 0.09, 0.105), rough=0.45, metal=0.6)
    ABL = mat("ablative", (0.19, 0.155, 0.13), rough=0.78, metal=0.02)
    COP = mat("copper", (0.72, 0.38, 0.19), rough=0.28, metal=1.0)
    GOLD = mat("gold", (0.86, 0.68, 0.28), rough=0.32, metal=0.9)
    # 연소실은 미션 중 이미시브가 실시간으로 오른다 — 초기값 0
    CHAM = mat("chamber", (0.30, 0.28, 0.27), rough=0.55, metal=0.35,
               emit=(1.0, 0.25, 0.05), emit_str=0.0)

    R_CH, L_CH = 0.155, 0.52          # 연소실
    R_EX = 0.45                       # 노즐 출구 반지름
    Z_NOZ = 0.55                      # 노즐 중심 높이

    # 노즐 — 삭마 라이너
    n = cone((0, 0, Z_NOZ), R_EX, R_CH * 0.92, 1.05, ABL,
             rot=(math.radians(180), 0, 0), name="nozzle")
    # 노즐 외피
    cone((0, 0, Z_NOZ), R_EX * 1.03, R_CH * 0.95, 1.05, STEEL,
         rot=(math.radians(180), 0, 0), name="nozzle_shell")
    # 연소실 — **이름 중요**: 엔진에서 이 메시를 찾아 이미시브를 올린다
    cyl((0, 0, 1.34), R_CH, L_CH, CHAM, name="chamber")
    # 인젝터 헤드
    cyl((0, 0, 1.70), R_CH * 1.30, 0.20, DARK, name="injector")
    torus((0, 0, 1.60), R_CH * 1.32, 0.028, GOLD, name="injector_ring")
    # 삭마냉각이라 냉각 배관이 없다 — 대신 연료 매니폴드 하나
    torus((0, 0, 1.10), R_CH * 1.15, 0.032, COP, name="manifold")
    # 터보펌프 1기
    px, py = math.cos(math.pi * 0.5) * 0.30, math.sin(math.pi * 0.5) * 0.30
    cyl((px, py, 1.42), 0.115, 0.30, STEEL, name="turbopump")
    cyl((px, py, 1.62), 0.070, 0.12, DARK, name="turbine")
    cyl((px * 0.5, py * 0.5, 1.26), 0.036, 0.34, STEEL,
        rot=(math.radians(90), 0, 0), name="feedline")
    # 짐벌 마운트
    cyl((0, 0, 1.86), R_CH * 0.75, 0.14, DARK, name="gimbal")
    export("merlin_1a")


# ═══════════════ 시험대 — 미션 1-1 의 무대 ═══════════════
def teststand():
    """맥그리거 사막의 정적 연소 시험대. 엔진은 별도 glb 로 얹는다."""
    fresh()
    CONC = mat("concrete", (0.40, 0.405, 0.415), rough=0.85)
    STEEL = mat("steel", (0.48, 0.50, 0.545), rough=0.36, metal=1.0)
    DARK = mat("dark", (0.075, 0.078, 0.088), rough=0.55, metal=0.4)
    RUST = mat("rust", (0.30, 0.16, 0.09), rough=0.82, metal=0.2)
    TANKM = mat("tank", (0.68, 0.70, 0.74), rough=0.32, metal=0.9)

    # 콘크리트 기단 + 화염 유도로
    box((0, 1.6, 0.5), (8.0, 6.0, 1.0), CONC, name="pad")
    box((0, -3.2, 0.85), (8.0, 4.0, 0.45), CONC,
        rot=(math.radians(-20), 0, 0), name="flame_trench")
    # 시험대 프레임 — 엔진이 여기 매달린다
    for i, sx in enumerate((-2.0, 2.0)):
        for j, sy in enumerate((-1.0, 1.0)):
            box((sx, 1.6 + sy, 2.6), (0.26, 0.26, 4.2), STEEL,
                name="post_%d%d" % (i, j))
    box((0, 1.6, 4.75), (4.8, 2.7, 0.35), STEEL, name="crosshead")
    box((0, 1.6, 4.30), (1.9, 1.9, 0.55), DARK, name="mount")
    # 추진제 탱크 2기 (LOX / RP-1)
    cyl((-5.6, 3.4, 2.3), 1.15, 4.4, TANKM, name="tank_lox")
    box((-5.6, 3.4, 0.2), (2.8, 2.8, 0.4), CONC, name="tank_lox_base")
    cyl((5.6, 3.4, 2.1), 0.95, 4.0, TANKM, name="tank_rp1")
    box((5.6, 3.4, 0.2), (2.4, 2.4, 0.4), CONC, name="tank_rp1_base")
    # 물탱크
    cyl((-7.0, -1.6, 1.5), 1.35, 3.0, RUST, name="water_tank")
    # 조명탑
    for i, sx in enumerate((-7.8, 7.8)):
        cyl((sx, -0.8, 3.4), 0.14, 6.8, STEEL, name="light_mast_%d" % i)
    export("teststand")


if __name__ == "__main__":
    print("== merlin_1a")
    merlin_1a()
    print("== teststand")
    teststand()
    print("GLTF EXPORT DONE ->", os.path.abspath(OUT))
