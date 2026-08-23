# -*- coding: utf-8 -*-
"""시험동 부품 키트 — 씬마다 다시 짜지 말 것 (2026-08-23).

**왜 만들었나.** 방을 만들 때마다 프리미티브를 손으로 쌓았더니 (1) 작업이
비싸고 (2) 결과가 실제 시험동과 다르게 나왔다. NASA/HAER 퍼블릭 도메인
시험동 사진(HAER OH-124-A-41, A-45)을 보고 내 씬에 없던 것을 골라 **부품
함수로 고정**한다. 다음 방부터는 이걸 조합만 하면 된다.

사진에서 확인한, 내 씬에 없던 다섯 가지:
  1. 바닥 전체가 **스틸 그레이팅** — 통짜 슬래브가 아니다
  2. 엔진 받침은 **벌어진 원형 튜브 삼각대** — 수직 각파이프가 아니다
  3. 배관이 **휘어 있다.** 직선 실린더만 쓴 것이 가장 큰 차이였다
  4. **플랜지와 볼트가 크다.** 배관 지름 대비 눈에 띄게 크다
  5. 굵은 **고무 호스**가 바닥을 가로지른다

휜 배관은 베지어 커브에 `bevel_depth` 를 줘서 만든다. 실린더를 이어 붙이는
것보다 싸고, 무엇보다 **모서리가 실제로 둥글다.**

주의: glTF 는 커브를 담지 못하므로 내보내기 전에 반드시 메시로 변환한다
(`to_mesh()` 를 호출하는 `_finish()` 가 처리한다).
"""
import bpy
import math
from mathutils import Vector


# ═════════════ 공통 ═════════════
def _finish(o, m, name=None, smooth=True):
    if m:
        o.data.materials.append(m)
    if name:
        o.name = name
    if smooth and hasattr(o.data, "polygons"):
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def _to_mesh(o):
    """커브를 메시로 굽는다 — glTF 는 커브를 담지 못한다."""
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.ops.object.convert(target='MESH')
    return bpy.context.object


# ═════════════ 배관 ═════════════
def pipe(points, r, m, name=None, res=8, smoothness=0.65):
    """점들을 잇는 **휜 배관**.

    `points` 는 [(x,y,z), ...]. 모퉁이가 실린더 이어붙이기처럼 각지지 않고
    실제 배관처럼 둥글게 돈다. 이것 하나가 씬의 인상을 가장 크게 바꾼다.
    """
    cu = bpy.data.curves.new("pipe", 'CURVE')
    cu.dimensions = '3D'
    cu.resolution_u = 6
    cu.bevel_depth = r
    cu.bevel_resolution = res
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(points) - 1)
    for i, p in enumerate(points):
        bp = sp.bezier_points[i]
        bp.co = Vector(p)
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name or "pipe", cu)
    bpy.context.collection.objects.link(o)
    if m:
        o.data.materials.append(m)
    o = _to_mesh(o)
    if name:
        o.name = name
    return o


def hose(a, b, sag, r, m, name=None):
    """바닥을 가로지르는 굵은 고무 호스. 가운데가 처진다."""
    ax, ay, az = a
    bx, by, bz = b
    mid = ((ax + bx) / 2, (ay + by) / 2, (az + bz) / 2 - sag)
    q1 = ((ax * 2 + bx) / 3, (ay * 2 + by) / 3, (az * 2 + bz) / 3 - sag * 0.72)
    q2 = ((ax + bx * 2) / 3, (ay + by * 2) / 3, (az + bz * 2) / 3 - sag * 0.72)
    return pipe([a, q1, mid, q2, b], r, m, name=name, res=6)


def flange(loc, r, m, bolt_m, n=16, th=0.035, bolt_r=None, axis='Z', name=None):
    """굵은 플랜지 + 눈에 띄는 볼트 링.

    사진에서 플랜지와 볼트는 배관 지름 대비 **훨씬 크다.** 작게 넣으면
    장난감처럼 보인다.
    """
    rot = {'Z': (0, 0, 0), 'X': (0, math.radians(90), 0),
           'Y': (math.radians(90), 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=th, vertices=48, location=loc)
    o = bpy.context.object
    o.rotation_euler = rot
    _finish(o, m, name)
    br = bolt_r if bolt_r is not None else r * 0.078
    for i in range(n):
        a = math.pi * 2 * i / n
        dx, dy = math.cos(a) * r * 0.82, math.sin(a) * r * 0.82
        if axis == 'Z':
            bl = (loc[0] + dx, loc[1] + dy, loc[2] + th * 0.55)
        elif axis == 'X':
            bl = (loc[0] + th * 0.55, loc[1] + dx, loc[2] + dy)
        else:
            bl = (loc[0] + dx, loc[1] + th * 0.55, loc[2] + dy)
        bpy.ops.mesh.primitive_cylinder_add(radius=br, depth=th * 1.5,
                                            vertices=6, location=bl)
        b = bpy.context.object
        b.rotation_euler = rot
        _finish(b, bolt_m, smooth=False)
    return o


# ═════════════ 구조 ═════════════
def grating(cx, cy, z, w, d, m, bar=0.055, gap=0.10, cross=0.6):
    """스틸 그레이팅 바닥. 사진의 시험 셀은 바닥 전체가 이것이다.

    막대를 한 방향으로 촘촘히, 직교 방향으로 성기게 깐다. 실제 그레이팅의
    구성이고, 그림자가 줄무늬로 떨어져 조명이 살아난다.
    """
    n = int(d / gap)
    for i in range(n):
        y = cy - d / 2 + gap * (i + 0.5)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, y, z))
        o = bpy.context.object
        o.scale = (w, bar * 0.34, bar)
        _finish(o, m, smooth=False)
    nc = max(2, int(w / cross))
    for i in range(nc):
        x = cx - w / 2 + cross * (i + 0.5)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, cy, z + bar * 0.18))
        o = bpy.context.object
        o.scale = (bar * 0.28, d, bar * 0.5)
        _finish(o, m, smooth=False)


def tripod(cx, cy, top_z, top_r, foot_r, m, foot_m, legs=3, r=0.075, name=None):
    """벌어진 원형 튜브 다리. 사진의 엔진 받침은 전부 이 모양이다.

    수직 각파이프로 세우면 가구처럼 보인다. 벌어진 원형 튜브라야
    '무거운 것을 받치고 있다'로 읽힌다.
    """
    made = []
    for i in range(legs):
        a = math.pi * 2 * i / legs + math.pi / legs
        tx, ty = cx + math.cos(a) * top_r, cy + math.sin(a) * top_r
        fx, fy = cx + math.cos(a) * foot_r, cy + math.sin(a) * foot_r
        L = math.sqrt((fx - tx) ** 2 + (fy - ty) ** 2 + top_z ** 2)
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=L, vertices=20,
                                            location=((tx + fx) / 2, (ty + fy) / 2, top_z / 2))
        o = bpy.context.object
        tilt = math.atan2(math.sqrt((fx - tx) ** 2 + (fy - ty) ** 2), top_z)
        o.rotation_euler = (0, tilt, a)
        _finish(o, m, name)
        made.append(o)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(fx, fy, 0.018))
        p = bpy.context.object
        p.scale = (0.26, 0.26, 0.036)
        p.rotation_euler = (0, 0, a)
        _finish(p, foot_m, smooth=False)
    return made


def valve(loc, r, m, wheel_m, axis='Y', name=None):
    """밸브 바디 + 핸드휠. 벽면 배관에 하나씩 걸면 배경이 살아난다."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    b = bpy.context.object
    b.scale = (r * 2.1, r * 2.1, r * 2.4)
    _finish(b, m, name)
    st = (loc[0], loc[1], loc[2] + r * 1.9)
    bpy.ops.mesh.primitive_cylinder_add(radius=r * 0.30, depth=r * 1.5,
                                        vertices=14, location=st)
    _finish(bpy.context.object, m)
    bpy.ops.mesh.primitive_torus_add(major_radius=r * 1.15, minor_radius=r * 0.16,
                                     major_segments=28, minor_segments=10,
                                     location=(loc[0], loc[1], loc[2] + r * 2.7))
    _finish(bpy.context.object, wheel_m)
    return b


def cable_bundle(points, n, r, m, spread=0.035):
    """케이블 다발 — 여러 가닥이 나란히 흐른다. 한 가닥은 배선으로 안 보인다."""
    out = []
    for i in range(n):
        off = (i - (n - 1) / 2) * spread
        pts = [(p[0] + off * 0.7, p[1] + off * 0.3, p[2] + off * 0.5) for p in points]
        out.append(pipe(pts, r, m, res=5))
    return out
