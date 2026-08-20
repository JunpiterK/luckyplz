# -*- coding: utf-8 -*-
"""브롤런 타일·OG 원본 장면 — Blender Cycles (2026-08-21).

청록 추격자가 빨강 선두의 등을 밀며 달리고, 선두는 뒤돌아보며 경악.
충돌 지점에 발광 임팩트 별, 바닥에 체커 트랙 스트립.

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P brawl_scene.py
출력: scripts/og-assets/brawl-scene-3d.png (1600x950 투명 PNG)
타일(public/assets/tiles/glory-racing.webp)과 OG(m_glory)가 이 자산을 쓴다.

좌표 규약은 team_scene.py 와 동일: three 식 (x, y=위, z=앞) → blender (x, -z, y).
러너는 +x 로 달린다. root 회전 rz=-ry_three (ry=1.15 ≈ 66° → 카메라 쪽 1/4 노출).
"""
import bpy
import math
import os
from mathutils import Vector, geometry

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "og-assets", "brawl-scene-3d.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'
prefs.get_devices()
for d in prefs.devices:
    d.use = True
scene.cycles.samples = 192
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 950
scene.render.film_transparent = True
scene.render.filepath = OUT
scene.view_settings.look = 'AgX - Punchy'

world = bpy.data.worlds.new("W")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.012, 0.016, 0.05, 1)
scene.world = world


def mat(name, color, rough=0.35, metal=0.0, sss=0.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss > 0:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.15, 0.08, 0.08)
    if emit > 0:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


RED = mat("red", (0.98, 0.15, 0.15), sss=0.03)
CYAN = mat("cyan", (0.05, 0.68, 0.82), sss=0.03)
DARK = mat("dark", (0.04, 0.055, 0.12), rough=0.5)
STAR = mat("star", (1.0, 0.6, 0.05), rough=0.4, emit=7.0)
FLOOR = mat("floor", (0.16, 0.18, 0.32), rough=0.85)
WHITE_GLOW = mat("wglow", (0.9, 0.95, 1.0), emit=1.2)


def M(px, py, pz):
    return (px, -pz, py)


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True


def sphere(parent, tpos, r, m, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=48, ring_count=24, location=M(*tpos))
    o = bpy.context.object
    o.scale = scale
    o.data.materials.append(m)
    smooth(o)
    o.parent = parent
    return o


def capsule(parent, ta, tb, r, m):
    va, vb = Vector(M(*ta)), Vector(M(*tb))
    d = vb - va
    mid = (va + vb) / 2
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, vertices=32, location=mid)
    cyl = bpy.context.object
    cyl.rotation_mode = 'QUATERNION'
    cyl.rotation_quaternion = d.to_track_quat('Z', 'Y')
    cyl.data.materials.append(m)
    smooth(cyl)
    cyl.parent = parent
    for pt in (va, vb):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=32, ring_count=16, location=pt)
        s = bpy.context.object
        s.data.materials.append(m)
        smooth(s)
        s.parent = parent


def face(parent, head_c, yaw, style):
    """머리 중심 head_c(three 로컬)에, 로컬 +z 기준 yaw 만큼 돌린 방향으로 표정.

    style='fury'(추격자: 분노) | 'panic'(선두: 경악)
    """
    hr = 1.0
    def at(fx, fy, fz):
        # (fx, fz) 를 yaw 회전
        rx = fx * math.cos(yaw) + fz * math.sin(yaw)
        rz = -fx * math.sin(yaw) + fz * math.cos(yaw)
        return (head_c[0] + rx, head_c[1] + fy, head_c[2] + rz)
    if style == 'fury':
        for ex in (-0.34, 0.34):
            sphere(parent, at(ex, 0.06, 0.92), 0.13, DARK, scale=(1, 0.5, 0.6))
        for bx, tilt in ((-0.36, -0.55), (0.36, 0.55)):
            bpy.ops.mesh.primitive_cube_add(size=1, location=M(*at(bx, 0.3, 0.9)))
            o = bpy.context.object
            o.scale = (0.27, 0.05, 0.06)
            o.rotation_euler = (0.45, tilt, -yaw)
            o.data.materials.append(DARK)
            o.parent = parent
        # 이 악문 입: 어두운 가로 박스
        bpy.ops.mesh.primitive_cube_add(size=1, location=M(*at(0.0, -0.34, 0.96)))
        o = bpy.context.object
        o.scale = (0.24, 0.05, 0.07)
        o.rotation_euler = (0.35, 0, -yaw)
        o.data.materials.append(DARK)
        o.parent = parent
    else:  # panic
        for ex in (-0.3, 0.32):
            sphere(parent, at(ex, 0.1, 0.9), 0.15, DARK, scale=(1, 1.15, 0.6))
        # 치켜 올라간 눈썹
        for bx, tilt in ((-0.32, -0.4), (0.34, 0.4)):
            bpy.ops.mesh.primitive_cube_add(size=1, location=M(*at(bx, 0.4, 0.88)))
            o = bpy.context.object
            o.scale = (0.3, 0.05, 0.06)
            o.rotation_euler = (0.5, tilt, -yaw)
            o.data.materials.append(DARK)
            o.parent = parent
        # 벌어진 입: 세로 타원
        sphere(parent, at(0.02, -0.36, 0.93), 0.17, DARK, scale=(0.85, 1.25, 0.6))


def runner(color_m, x, z, ry, pose):
    """달리는 자세. pose='chase'(민다) | 'lead'(밀리며 뒤돌아봄)."""
    bpy.ops.object.empty_add(location=(x, -z, 0))
    root = bpy.context.object
    root.rotation_euler = (0, 0, -ry)
    # 몸통: 앞으로 기울인 캡슐
    capsule(root, (0, 1.15, -0.25), (0, 2.7, 0.45), 0.8, color_m)
    # 골반
    sphere(root, (0, 1.05, -0.2), 0.62, color_m, scale=(1, 0.85, 0.9))
    # 머리 (전진 자세라 앞쪽 위)
    head_c = (0, 3.55, 0.85)
    sphere(root, head_c, 1.0, color_m)
    if pose == 'chase':
        face(root, head_c, 1.73, 'fury')
        # 두 팔을 앞으로 뻗어 민다
        capsule(root, (-0.8, 2.6, 0.35), (-0.75, 2.35, 1.35), 0.27, color_m)
        capsule(root, (-0.75, 2.35, 1.35), (-0.5, 2.2, 2.3), 0.25, color_m)
        sphere(root, (-0.5, 2.2, 2.42), 0.3, color_m)
        capsule(root, (0.8, 2.6, 0.35), (0.85, 2.3, 1.3), 0.27, color_m)
        capsule(root, (0.85, 2.3, 1.3), (0.6, 2.1, 2.25), 0.25, color_m)
        sphere(root, (0.6, 2.1, 2.37), 0.3, color_m)
    else:
        # 뒤돌아본 얼굴 (로컬 -z 쪽으로 143°)
        face(root, head_c, 0.51, 'panic')
        # 오른팔 앞위로 허우적
        capsule(root, (0.8, 2.55, 0.5), (1.0, 2.65, 1.55), 0.27, color_m)
        sphere(root, (1.03, 2.67, 1.75), 0.3, color_m)
        # 왼팔 뒤로
        capsule(root, (-0.8, 2.55, 0.3), (-1.0, 1.95, -0.7), 0.27, color_m)
        sphere(root, (-1.05, 1.85, -0.85), 0.3, color_m)
    # 다리: 러닝 스트라이드
    capsule(root, (-0.27, 1.0, -0.15), (-0.3, 0.7, -1.05), 0.3, color_m)
    capsule(root, (-0.3, 0.7, -1.05), (-0.32, 0.18, -1.75), 0.28, color_m)
    sphere(root, (-0.32, 0.14, -1.9), 0.32, color_m, scale=(0.9, 0.75, 1.25))
    capsule(root, (0.27, 1.0, 0.0), (0.3, 0.62, 0.95), 0.3, color_m)
    capsule(root, (0.3, 0.62, 0.95), (0.32, 0.1, 1.5), 0.28, color_m)
    sphere(root, (0.32, 0.07, 1.65), 0.32, color_m, scale=(0.9, 0.75, 1.25))
    return root


# 추격자(청록)와 선두(빨강) — 접촉 직전
runner(CYAN, -2.75, 0.5, 1.15, 'chase')
runner(RED, 1.35, 0.2, 1.15, 'lead')

# ── 임팩트 별 (발광, 카메라를 향해 세움) ──
star_pts = []
for k in range(10):
    r = 0.62 if k % 2 == 0 else 0.27
    a = math.pi / 5 * k - math.pi / 2
    star_pts.append((math.cos(a) * r, math.sin(a) * r))
n = len(star_pts)
verts = [(p[0], p[1], 0.0) for p in star_pts] + [(p[0], p[1], -0.22) for p in star_pts]
tris = geometry.tessellate_polygon([[Vector((p[0], p[1], 0)) for p in star_pts]])
faces = [list(t) for t in tris]
faces += [[a2 + n, b2 + n, c2 + n][::-1] for a2, b2, c2 in tris]
faces += [[i, (i + 1) % n, (i + 1) % n + n, i + n] for i in range(n)]
mesh = bpy.data.meshes.new("star")
mesh.from_pydata(verts, [], faces)
mesh.update()
star = bpy.data.objects.new("star", mesh)
bpy.context.collection.objects.link(star)
star.data.materials.append(STAR)
star.rotation_euler = (math.radians(90), 0, 0)     # xy 별 → 카메라(-y) 정면
star.location = M(-0.1, 2.35, 1.95)
star.scale = (1.3, 1.3, 1.3)

# ── 속도선: 추격자 뒤 발광 капсула 3 ──
for sy, sl in ((3.1, 1.4), (2.3, 1.0), (1.6, 1.3)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.042, depth=sl, vertices=16,
                                        location=M(-4.75 - sl / 2, sy, 0.6))
    o = bpy.context.object
    o.rotation_euler = (0, math.radians(90), 0)
    o.data.materials.append(WHITE_GLOW)
    smooth(o)

# ── 바닥 + 체커 트랙 스트립 ──
# 무대형 바닥: 러너 주변만 (전체 평면이면 투명 렌더의 이점이 사라진다)
bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.6, -0.7, 0))
floor = bpy.context.object
floor.scale = (7.6, 4.4, 1)
floor.data.materials.append(FLOOR)

CHK = bpy.data.materials.new("chk")
CHK.use_nodes = True
bsdf = CHK.node_tree.nodes["Principled BSDF"]
chk = CHK.node_tree.nodes.new("ShaderNodeTexChecker")
chk.inputs["Scale"].default_value = 14.0
chk.inputs["Color1"].default_value = (0.92, 0.93, 0.96, 1)
chk.inputs["Color2"].default_value = (0.07, 0.09, 0.16, 1)
CHK.node_tree.links.new(chk.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.7
bpy.ops.mesh.primitive_cube_add(size=1, location=M(-0.6, 0.035, 2.9))
strip = bpy.context.object
strip.scale = (7.5, 0.5, 0.035)
strip.data.materials.append(CHK)

# ── 조명 (팀 씬과 동일 리그 + 컬러 포인트) ──
def area(loc, power, size, color=(1, 1, 1)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    L = bpy.context.object
    L.data.energy = power
    L.data.size = size
    L.data.color = color
    d = Vector((0, 0, 1.5)) - Vector(loc)
    L.rotation_mode = 'QUATERNION'
    L.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    return L

area(M(-5, 10, 7), 2000, 7)
area(M(4, 6, -6), 360, 5, (0.78, 0.85, 1.0))
area(M(0, 5, 9), 350, 6)
for lx, col in ((-3.6, (0.2, 0.85, 0.95)), (2.2, (1, 0.3, 0.3))):
    bpy.ops.object.light_add(type='POINT', location=M(lx, 0.8, 2.2))
    bpy.context.object.data.energy = 85
    bpy.context.object.data.color = col

# ── 카메라 ──
bpy.ops.object.camera_add(location=M(-0.6, 4.4, 15.5))
cam = bpy.context.object
cam.data.lens = 44
d = Vector(M(-0.6, 1.9, 0)) - cam.location
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = d.to_track_quat('-Z', 'Y')
scene.camera = cam

bpy.ops.render.render(write_still=True)
print("RENDER DONE ->", OUT)
