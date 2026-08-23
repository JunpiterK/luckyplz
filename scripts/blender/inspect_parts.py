# -*- coding: utf-8 -*-
"""검사용 부품 — 손상 부위를 찾는 미션의 대상 (2026-08-23).

운영자 지시: *"간단히 드래그해서 어디다 넣는다던가... 무엇을 찾아서 어떤 것을
찾아낸다던가 간단한 조작을 통해서도 미션을 클리어할수잇는 간단한 조작 미션도
장치로 넣어야지."*

지금까지 모든 미션이 '숫자 읽고 슬라이더'였다. 손으로 하는 조작이 없다.
이 파일은 그 중 **찾기** 쪽 대상을 만든다.

## 명명 규약 (엔진이 이 이름으로 판정한다)

  `dmg_<n>`   진짜 손상 부위. 플레이어가 찾아야 하는 것
  `bait_<n>`  비슷해 보이지만 정상. 눌러도 오답
  `part_*`    부품 본체

**손상 위치는 물리를 따른다.** 캐비테이션은 블레이드 **흡입면 앞전 근처**
에서 기포가 붕괴하며 금속을 때린다. 아무 데나 찍으면 교육 가치가 0 이고,
플레이어가 규칙을 발견할 수도 없다. 미끼는 같은 블레이드의 **압력면**과
**뒷전** — 위치만 다르고 생김새는 비슷하게 둔다.

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P inspect_parts.py
출력: public/assets/deltav/impeller_damaged.glb
"""
import bpy
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "..", "..", "public", "assets", "deltav")
os.makedirs(OUT, exist_ok=True)


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


def pit_cluster(cx, cy, cz, nx, ny, nz, m, n=9, spread=0.030, name=None):
    """캐비테이션 침식 — 작은 구멍이 벌집처럼 모여 있다.

    한 개짜리 큰 자국이 아니라 **작은 것이 무리지어** 있는 것이 캐비테이션의
    특징이다. 그래서 사진에서 '벌집'이라고 부른다.
    """
    made = []
    for i in range(n):
        a = i * 2.399963           # 황금각 — 규칙적이지 않게 흩어진다
        r = spread * math.sqrt((i + 0.5) / n)
        ox = math.cos(a) * r
        oy = math.sin(a) * r
        sz = 0.0035 + 0.0042 * ((i * 7 % 5) / 5.0)
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=sz, segments=10, ring_count=6,
            location=(cx + ox * (1 - abs(nx)) + nx * 0.002,
                      cy + oy * (1 - abs(ny)) + ny * 0.002,
                      cz + (ox if abs(nz) < 0.5 else oy) * 0.35))
        o = bpy.context.object
        o.scale = (1, 1, 0.55)
        o.data.materials.append(m)
        smooth(o)
        made.append(o)
    if name and made:
        made[0].name = name
    return made


def marker(loc, r, m, name):
    """판정용 표적. 반투명 구 — 화면에서는 엔진이 숨기고 레이 피킹만 쓴다."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=14, ring_count=8,
                                         location=loc)
    o = bpy.context.object
    o.data.materials.append(m)
    o.name = name
    return smooth(o)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    INCO = mat("inco", (0.44, 0.42, 0.40), rough=0.34, metal=1.0)
    WORN = mat("worn", (0.30, 0.29, 0.28), rough=0.62, metal=0.85)
    PIT = mat("pit", (0.055, 0.05, 0.048), rough=0.88, metal=0.2)
    HUB = mat("hub", (0.38, 0.37, 0.36), rough=0.40, metal=1.0)
    MARK = mat("mark", (0.2, 0.9, 0.8), rough=0.4)

    NB = 7                      # 블레이드 수 — 펌프 리그와 같게
    R_HUB, R_TIP = 0.075, 0.335

    # 허브 · 슈라우드
    bpy.ops.mesh.primitive_cylinder_add(radius=R_HUB, depth=0.26, vertices=40,
                                        location=(0, 0, 0))
    smooth(bpy.context.object).data.materials.append(HUB)
    bpy.ops.mesh.primitive_cylinder_add(radius=R_TIP, depth=0.022, vertices=56,
                                        location=(0, 0, -0.12))
    o = bpy.context.object
    o.data.materials.append(INCO)
    o.name = "part_shroud"
    smooth(o)
    bpy.ops.mesh.primitive_cone_add(radius1=R_HUB, radius2=0.012, depth=0.10,
                                    vertices=32, location=(0, 0, 0.18))
    smooth(bpy.context.object).data.materials.append(HUB)

    # 블레이드 — 후향으로 감긴다
    for b in range(NB):
        ang = math.pi * 2 * b / NB
        bpy.ops.mesh.primitive_cube_add(size=1, location=(
            math.cos(ang) * 0.20, math.sin(ang) * 0.20, -0.02))
        o = bpy.context.object
        o.scale = (0.27, 0.018, 0.17)
        o.rotation_euler = (0, 0, ang + math.radians(28))
        o.data.materials.append(WORN if b in (0, 2, 4) else INCO)
        o.name = "part_blade_%d" % b
        md = o.modifiers.new("b", 'BEVEL')
        md.width = 0.003
        md.segments = 2
        md.limit_method = 'ANGLE'
        smooth(o)

    # ── 손상 3곳: 블레이드 흡입면 **앞전 근처** ──
    # 캐비테이션은 여기서 일어난다. 위치가 곧 정답이므로 물리를 지킨다.
    dmg_blades = (0, 2, 4)
    for i, b in enumerate(dmg_blades):
        ang = math.pi * 2 * b / NB
        th = ang + math.radians(28)
        # 앞전(바깥쪽) · 흡입면(회전 반대편) 으로 살짝 밀어낸다
        lx = math.cos(ang) * 0.305
        ly = math.sin(ang) * 0.305
        nx, ny = -math.sin(th), math.cos(th)          # 블레이드 면 법선
        px, py = lx + nx * 0.021, ly + ny * 0.021
        pit_cluster(px, py, -0.03, nx, ny, 0, PIT, n=11, spread=0.034)
        marker((px + nx * 0.012, py + ny * 0.012, -0.03), 0.052, MARK,
               "dmg_%d" % (i + 1))

    # ── 미끼 3곳: 같은 블레이드의 압력면·뒷전 ──
    # 생김새는 비슷하되 캐비테이션이 일어날 수 없는 자리다.
    baits = ((1, 0.305, -1), (3, 0.150, 1), (5, 0.170, -1))
    for i, (b, rad, side) in enumerate(baits):
        ang = math.pi * 2 * b / NB
        th = ang + math.radians(28)
        nx, ny = -math.sin(th) * side, math.cos(th) * side
        px = math.cos(ang) * rad + nx * 0.021
        py = math.sin(ang) * rad + ny * 0.021
        pit_cluster(px, py, -0.03, nx, ny, 0, PIT, n=6, spread=0.022)
        marker((px + nx * 0.012, py + ny * 0.012, -0.03), 0.048, MARK,
               "bait_%d" % (i + 1))

    path = os.path.join(OUT, "impeller_damaged.glb")
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', use_selection=False,
        export_apply=True, export_cameras=False, export_lights=False,
        export_yup=True, export_texcoords=True, export_normals=True,
        export_materials='EXPORT')
    print("  exported impeller_damaged (%.0f KB)" % (os.path.getsize(path) / 1024))


if __name__ == "__main__":
    build()
    print("INSPECT PARTS DONE ->", os.path.abspath(OUT))
