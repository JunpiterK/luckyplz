# -*- coding: utf-8 -*-
"""팀뽑기 타일·OG 원본 장면 — Blender Cycles (2026-08-21 운영자 확정 그라운드).

홍팀 vs 블루팀 3:3 팔짱 대치 + 지그재그 균열 + 금색 3D VS.
실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P team_scene.py
출력: scripts/og-assets/team-scene-3d.png (1600x950 투명 PNG)
타일(public/assets/tiles/team.webp)과 OG(m_team)가 이 자산을 쓴다.

좌표 규약: three 식 (x, y=위, z=앞) → blender (x, -z, y). figure 회전 rz=-ry.
"""
import bpy
import math
from mathutils import Vector, geometry

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "og-assets", "team-scene-3d.png")

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
bgn = world.node_tree.nodes["Background"]
bgn.inputs[0].default_value = (0.012, 0.016, 0.05, 1)
scene.world = world


def mat(name, color, rough=0.35, metal=0.0, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss > 0:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.15, 0.08, 0.08)
    return m


RED = mat("red", (0.98, 0.15, 0.15), sss=0.03)
BLUE = mat("blue", (0.1, 0.36, 1.0), sss=0.03)
DARK = mat("dark", (0.04, 0.055, 0.12), rough=0.5)
GOLD = mat("gold", (0.95, 0.72, 0.18), rough=0.28, metal=0.85)
FLOOR = mat("floor", (0.16, 0.18, 0.32), rough=0.85)
ABYSS = mat("abyss", (0.008, 0.01, 0.03), rough=1.0)


def M(px, py, pz):
    """three 로컬 (x, y=up, z=front) → blender 로컬 (x, front, up)."""
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


def figure(color_m, x, z, ry_three, face=False):
    bpy.ops.object.empty_add(location=(x, -z, 0))
    root = bpy.context.object
    root.rotation_euler = (0, 0, -ry_three)
    # 몸통 (three: pos y1.8, capsule r.95 len1.5, scale 1.16/1/0.84)
    o = sphere(root, (0, 1.85, 0), 1.0, color_m, scale=(1.1, 0.8, 1.5))
    # 골반
    sphere(root, (0, 0.7, 0), 0.74, color_m, scale=(1.0, 0.8, 0.9))
    # 머리
    sphere(root, (0, 3.6, 0.1), 1.06, color_m)
    # 팔짱 (three v4 관절 좌표 그대로)
    capsule(root, (-1.1, 2.6, 0.1), (-1.2, 1.95, 0.48), 0.3, color_m)
    capsule(root, (1.1, 2.6, 0.1), (1.2, 1.95, 0.48), 0.3, color_m)
    capsule(root, (-1.2, 1.95, 0.48), (0.88, 2.12, 0.66), 0.29, color_m)
    capsule(root, (1.2, 1.95, 0.48), (-0.88, 1.86, 0.7), 0.29, color_m)
    if face:
        for ex in (-0.35, 0.35):
            sphere(root, (ex, 3.62, 1.08), 0.14, DARK, scale=(1, 0.5, 0.6))
        for bx, tilt in ((-0.38, 0.55), (0.38, -0.55)):
            bpy.ops.mesh.primitive_cube_add(size=1, location=M(bx, 3.86, 1.04))
            o = bpy.context.object
            o.scale = (0.27, 0.05, 0.06)
            o.rotation_euler = (0.45, tilt, 0)
            o.data.materials.append(DARK)
            o.parent = root
        bpy.ops.mesh.primitive_cube_add(size=1, location=M(0.02, 3.27, 1.12))
        o = bpy.context.object
        o.scale = (0.15, 0.035, 0.035)
        o.rotation_euler = (0.4, 0, 0)
        o.data.materials.append(DARK)
        o.parent = root
    return root


for color_m, sign in ((RED, -1), (BLUE, 1)):
    for sx, sz, front in ((2.15, 1.6, True), (3.85, -0.9, False), (5.35, -3.0, False)):
        figure(color_m, sign * sx, sz, sign * 0.72, face=front)


def prism(points2d, thickness, m):
    """윗면 다각형(xy) + 두께. 오목 다각형은 tessellate 로 삼각화."""
    n = len(points2d)
    verts = [(p[0], p[1], 0.0) for p in points2d] + \
            [(p[0], p[1], -thickness) for p in points2d]
    tris = geometry.tessellate_polygon([[Vector((p[0], p[1], 0)) for p in points2d]])
    faces = [list(t) for t in tris]
    faces += [[a + n, b + n, c + n][::-1] for a, b, c in tris]
    faces += [[i, (i + 1) % n, (i + 1) % n + n, i + n] for i in range(n)]
    mesh = bpy.data.meshes.new("prism")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new("prism", mesh)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    return o


# 슬래브: three 의 z 를 blender y 로 그대로 (zig 는 z 5→-5)
for sign in (1, -1):
    zig = [(0.55, 5), (1.15, 2.2), (0.5, -0.2), (1.3, -2.6), (0.7, -5)]
    pts = [(sign * 9.5, -5)] + [(sign * x, -z) for x, z in zig] + [(sign * 9.5, 5)]
    if sign < 0:
        pts = pts[::-1]
    prism(pts, 0.55, FLOOR)

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.56))
bpy.context.object.scale = (2.4, 11, 1)
bpy.context.object.data.materials.append(ABYSS)

# ── VS 블록 (three: pos (0,3.35,0.4), rot y -0.38) ──
bpy.ops.mesh.primitive_cube_add(size=1, location=M(0, 3.55, 0.4))
vs = bpy.context.object
vs.scale = (1.3, 0.45, 0.85)
vs.rotation_euler = (0.05, 0.03, -0.38)
vs.data.materials.append(GOLD)
bpy.ops.object.text_add(location=M(0.02, 3.53, 0.88))
txt = bpy.context.object
txt.data.body = "VS"
txt.data.size = 1.22
txt.data.extrude = 0.07
txt.data.align_x = 'CENTER'
txt.data.align_y = 'CENTER'
txt.rotation_euler = (math.radians(90), 0, -0.38)
txt.data.materials.append(DARK)

# ── 조명 (three: key(-5,10,7) rim(4,6,-6) → M) ──
def area(loc, power, size, color=(1, 1, 1)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    L = bpy.context.object
    L.data.energy = power
    L.data.size = size
    L.data.color = color
    # 원점(무대)을 향하게
    d = Vector((0, 0, 1.5)) - Vector(loc)
    L.rotation_mode = 'QUATERNION'
    L.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    return L

area(M(-5, 10, 7), 2000, 7)
area(M(4, 6, -6), 360, 5, (0.78, 0.85, 1.0))
area(M(0, 5, 9), 350, 6)
for lx, col in ((-3.2, (1, 0.3, 0.3)), (3.2, (0.28, 0.5, 1))):
    bpy.ops.object.light_add(type='POINT', location=M(lx, 0.8, 2.2))
    bpy.context.object.data.energy = 85
    bpy.context.object.data.color = col

# ── 카메라: +y 에서 -y 를 본다 (three (0,4.4,15) lookAt(0,1.9,0)) ──
bpy.ops.object.camera_add(location=M(0, 4.6, 15.5))
cam = bpy.context.object
cam.data.lens = 44
d = Vector(M(0, 1.8, 0)) - cam.location
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = d.to_track_quat('-Z', 'Y')
scene.camera = cam

bpy.ops.render.render(write_still=True)
print("RENDER DONE ->", OUT)
