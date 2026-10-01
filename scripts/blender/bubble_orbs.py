# -*- coding: utf-8 -*-
"""버블 버스트 — 젤리·유리 버블 아틀라스 (2026-10-01 개편).

운영자 기준: "아케이드는 손맛·비주얼·캐릭터성·이펙트" — 평면 그라디언트 원(옛 캔버스 그림)을
코팅 젤리 사탕 + 새김 무늬(색약 보조)로 바꾼다. 모든 버블이 한 스튜디오(같은 조명·카메라)에서 찍힌다.

## 프레임 (ORDER = 아틀라스 순서 — 게임 JS 의 BA_ORDER 와 같다)
  c0..c5   색 버블 — 빨강(원)·노랑(별)·초록(세모)·파랑(네모)·보라(마름모)·주황(십자)
           몸 = Principled SSS + Coat(젤리 사탕), 무늬 = 밝은 에나멜로 볼록 새김(Bevel)
  k0..k5   아기 판다가 갇힌 유리 버블 — 색 유리 껍질(투과) 안에 마스코트 얼굴(stand.png 재사용)
           film_transparent_glass 로 유리 뒤 배경은 투명, 얼굴은 굴절돼 보인다
  rb       무지개(각도 따라 6색) + 흰 별
  bm       폭탄 — 검푸른 금속 + 황동 마개·심지 + 붉은 띠(불꽃은 게임이 그린다)
  ln       레이저(줄 지우기) — 은빛 젤리 + 청록 발광 ◀▶
  gy       회색(게임 오버 때 굳은 버블)
  ice      얼음 껍질(덧그림) — 각진 결정 + 서리
  ice2     금 간 얼음 껍질(한 번 맞은 뒤)

좌표: 버블 반지름 0.5(지름 = 월드 1.0), 직교 카메라 ortho 1.25 = 게임 스프라이트 반폭 SP=R+5 와 같은 비율.
카메라는 -Y 에서 +Y 를 본다(정면, 기울기 없음 — 판의 버블이 전부 같은 각도로 보여야 한다). 화면 위 = +Z.
Standard 뷰 변환(AgX 는 원색을 파스텔로 누른다 — art_pipeline 메모).

실행:
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/bubble_orbs.py            # 전부
  ... -P scripts/blender/bubble_orbs.py -- c0,k3,ice                                              # 일부
  BO_SAMPLES=24 BO_RES=176 ... 로 시안
출력: scripts/og-assets/bubble/<frame>.png → python scripts/build_bubble_atlas.py → public/assets/bubble/orbs.webp
"""
import bpy
import math
import os
import sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "..", "og-assets", "bubble")
os.makedirs(OUTDIR, exist_ok=True)
PANDA = os.path.join(HERE, "..", "og-assets", "mascot", "stand.png")
PANDA_HEAD = (0.5000, 0.3696)        # build_mascot_atlas 가 찍은 PD.stand.h (프레임 정규 좌표, v 아래로)
RES = int(os.environ.get('BO_RES', '176'))
SAMPLES = int(os.environ.get('BO_SAMPLES', '160'))
ORTHO = 1.25

COLS = [  # sRGB 게임색(#ff4d6a 등)을 선형으로 — 젤리 SSS 가 밝히므로 약간 짙게
    (1.00, 0.06, 0.12),
    (1.00, 0.62, 0.02),
    (0.05, 0.70, 0.22),
    (0.04, 0.24, 1.00),
    (0.42, 0.13, 1.00),
    (1.00, 0.24, 0.03),
]
ORDER = ['c%d' % i for i in range(6)] + ['k%d' % i for i in range(6)] + ['rb', 'bm', 'ln', 'gy', 'ice', 'ice2']


# ════════════ 스튜디오 ════════════
def studio():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try:
        sc.cycles.device = 'GPU'
        pr = bpy.context.preferences.addons['cycles'].preferences
        pr.compute_device_type = 'CUDA'
        pr.get_devices()
        for d in pr.devices:
            d.use = True
    except Exception:
        pass
    sc.cycles.use_denoising = True
    sc.cycles.samples = SAMPLES
    sc.cycles.max_bounces = 16
    sc.cycles.transmission_bounces = 12
    sc.cycles.transparent_max_bounces = 16
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.render.film_transparent = True
    try:
        sc.cycles.film_transparent_glass = True
        sc.cycles.film_transparent_roughness = 0.1
    except Exception:
        pass
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.6, 0.75, 1)
    bg.inputs[1].default_value = 0.9
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMixShader')
    tr = nt.nodes.new('ShaderNodeBackground')
    tr.inputs[1].default_value = 0.10
    nt.links.new(lp.outputs['Is Glossy Ray'], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(bg.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes['World Output'].inputs[0])
    sc.world = w

    def area(loc, power, size, color, shape='SQUARE', sy=None):
        bpy.ops.object.light_add(type='AREA', location=loc)
        L = bpy.context.object
        L.data.energy = power
        L.data.shape = shape
        L.data.size = size
        if sy is not None:
            L.data.size_y = sy
        L.data.color = color
        d = Vector((0, 0, 0)) - Vector(loc)
        L.rotation_mode = 'QUATERNION'
        L.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    area((-2.2, -3.0, 2.6), 180, 1.3, (1.0, 0.97, 0.92), 'RECTANGLE', 0.8)   # 키 — 왼쪽 위 창문 하이라이트
    area((2.4, 2.2, 2.6), 260, 2.2, (1.0, 0.95, 1.0))                        # 뒤 림 — SSS 가장자리
    area((0.0, -4.4, 0.3), 70, 3.6, (1.0, 1.0, 1.0))                         # 정면 채움
    area((1.0, -2.0, -2.8), 60, 2.0, (1.0, 0.9, 0.85))                       # 아래 반사(오른쪽 아래 작은 광택)
    bpy.ops.object.camera_add(location=(0, -10.0, 0))
    cam = bpy.context.object
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ORTHO
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = Vector((0, 1, 0)).to_track_quat('-Z', 'Z')
    sc.camera = cam
    return sc


# ════════════ 재질 ════════════
def principled(name, color, rough=0.14, coat=1.0, sss=0.0, sss_col=None, metal=0.0, emit=None, estr=0.0, alpha=1.0, trans=0.0, ior=1.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.03
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = sss_col or (1.0, 0.6, 0.6)
        b.inputs["Subsurface Scale"].default_value = 0.25
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = estr
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = 'BLEND'
    return m


def lighten(c, t):
    return tuple(c[i] + (1 - c[i]) * t for i in range(3))


def sphere(r=0.5, loc=(0, 0, 0), mat=None, seg=96, scale=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    if scale:
        o.scale = scale
    if mat:
        o.data.materials.append(mat)
    return o


# ════════════ 새김 무늬 (색약 보조 — 같은 색 = 같은 모양) ════════════
def shape_pts(k, s=0.17):
    P = []
    if k == 0:
        for i in range(40):
            a = i / 40 * 2 * math.pi
            P.append((math.cos(a) * s * .95, math.sin(a) * s * .95))
    elif k == 1:
        for i in range(10):
            a = math.pi / 2 + i * math.pi / 5
            r = s * (1.2 if i % 2 == 0 else .5)
            P.append((math.cos(a) * r, math.sin(a) * r))
    elif k == 2:
        for i in range(3):
            a = math.pi / 2 + i * 2 * math.pi / 3
            P.append((math.cos(a) * s * 1.25, math.sin(a) * s * 1.25 - s * .12))
    elif k == 3:
        q = s * .9
        P = [(-q, -q), (q, -q), (q, q), (-q, q)]
    elif k == 4:
        P = [(0, -s * 1.25), (s * .95, 0), (0, s * 1.25), (-s * .95, 0)]
    elif k == 5:
        a, b = s * .36, s * 1.1
        P = [(-a, -b), (a, -b), (a, -a), (b, -a), (b, a), (a, a), (a, b), (-a, b), (-a, a), (-b, a), (-b, -a), (-a, -a)]
    elif k == 'arrows':      # ◀━━▶
        h, t, L, sh = .17, .06, .34, .17
        P = [(-L, 0), (-L + sh, h), (-L + sh, t), (L - sh, t), (L - sh, h), (L, 0), (L - sh, -h), (L - sh, -t), (-L + sh, -t), (-L + sh, -h)]
    return P


def emblem(k, mat, s=0.19, depth=0.045, bevel=0.016):
    """평면 무늬를 잘게 나눈 뒤 구 표면에 얹어(곡면을 따라 휜다) 바깥으로 두께를 준다 — 볼록 새김"""
    import bmesh
    pts = shape_pts(k, s)
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0.0, z)) for (x, z) in pts]
    ctr = bm.verts.new((0.0, 0.0, 0.0))     # 모든 무늬가 중심에 대해 별 모양 → 중심 부채꼴 삼각분할(오목 별·십자도 안 깨진다)
    for i in range(len(vs)):
        bm.faces.new((ctr, vs[i], vs[(i + 1) % len(vs)]))
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=4, use_grid_fill=True)
    for v in bm.verts:
        x, z = v.co.x, v.co.z
        v.co.y = -math.sqrt(max(0.0, 0.25 - x * x - z * z)) + 0.012
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        if f.normal.y > 0:
            f.normal_flip()
    me = bpy.data.meshes.new('emb')
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new('emb', me)
    bpy.context.scene.collection.objects.link(o)
    so = o.modifiers.new('so', 'SOLIDIFY')
    so.thickness = depth
    so.offset = 1
    so.use_even_offset = True
    bv = o.modifiers.new('bv', 'BEVEL')
    bv.width = bevel
    bv.segments = 4
    bv.limit_method = 'ANGLE'
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


# ════════════ 프레임 ════════════
def color_orb(i):
    c = COLS[i]
    body = principled('body%d' % i, c, rough=0.16, coat=1.0, sss=0.45, sss_col=lighten(c, .5), emit=c, estr=0.12)
    sphere(mat=body)
    enamel = principled('enam%d' % i, lighten(c, .72), rough=0.22, coat=1.0, emit=lighten(c, .6), estr=0.08)
    emblem(i, enamel)


def cub_orb(i):
    c = COLS[i]
    # 색 유리 껍질 — 투과(유리 뒤 배경은 투명), 굴절은 약하게(얼굴이 너무 일그러지지 않게)
    shell = principled('shell%d' % i, lighten(c, .55), rough=0.02, coat=1.0, trans=1.0, ior=1.12)
    sphere(mat=shell)
    # 뒤쪽 색 젤리 배경 — 얼굴 뒤에 색이 차 있어야 무슨 색 버블인지 읽힌다
    back = principled('back%d' % i, c, rough=0.4, coat=0.0, sss=0.3, sss_col=lighten(c, .5), emit=c, estr=0.35)
    sphere(r=0.43, loc=(0, 0.2, 0), mat=back, scale=(1, 0.3, 1))
    # 아기 판다 얼굴 판 — happy.png 의 머리 부분만 UV 로 잘라 붙인다
    bpy.ops.mesh.primitive_plane_add(size=0.66, location=(0, -0.02, -0.02))
    pl = bpy.context.object
    pl.rotation_euler = (math.pi / 2, 0, 0)
    m = bpy.data.materials.new('cub')
    m.use_nodes = True
    m.blend_method = 'BLEND'
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.6
    img = nt.nodes.new('ShaderNodeTexImage')
    img.image = bpy.data.images.load(PANDA)
    img.interpolation = 'Cubic'
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    half = 0.33                              # 머리 반지름 0.287 + 귀 여유
    mp.inputs['Scale'].default_value = (2 * half, 2 * half, 1)
    mp.inputs['Location'].default_value = (PANDA_HEAD[0] - half, 1 - PANDA_HEAD[1] - half, 0)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], img.inputs['Vector'])
    nt.links.new(img.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(img.outputs['Color'], b.inputs['Emission Color'])
    b.inputs["Emission Strength"].default_value = 0.35
    # 둥근 마스크(아래 몸통·막대가 비치지 않게) × 그림 알파
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['UV'], sep.inputs[0])
    dx = nt.nodes.new('ShaderNodeMath'); dx.operation = 'SUBTRACT'; dx.inputs[1].default_value = 0.5
    dz = nt.nodes.new('ShaderNodeMath'); dz.operation = 'SUBTRACT'; dz.inputs[1].default_value = 0.5
    nt.links.new(sep.outputs[0], dx.inputs[0]); nt.links.new(sep.outputs[1], dz.inputs[0])
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
    cm = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(dx.outputs[0], cm.inputs[0]); nt.links.new(dz.outputs[0], cm.inputs[1])
    nt.links.new(cm.outputs[0], ln.inputs[0])
    ramp = nt.nodes.new('ShaderNodeMapRange')
    ramp.inputs['From Min'].default_value = 0.5
    ramp.inputs['From Max'].default_value = 0.44
    nt.links.new(ln.outputs['Value'], ramp.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    nt.links.new(ramp.outputs['Result'], mul.inputs[0]); nt.links.new(img.outputs['Alpha'], mul.inputs[1])
    nt.links.new(mul.outputs[0], b.inputs['Alpha'])
    pl.data.materials.append(m)


def rainbow_orb():
    m = bpy.data.materials.new('rainbow')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.14
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.03
    b.inputs["Subsurface Weight"].default_value = 0.3
    b.inputs["Subsurface Scale"].default_value = 0.2
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    at = nt.nodes.new('ShaderNodeMath'); at.operation = 'ARCTAN2'
    nt.links.new(sep.outputs[2], at.inputs[0]); nt.links.new(sep.outputs[0], at.inputs[1])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = -math.pi
    mr.inputs['From Max'].default_value = math.pi
    nt.links.new(at.outputs[0], mr.inputs['Value'])
    cr = nt.nodes.new('ShaderNodeValToRGB')
    el = cr.color_ramp.elements
    hues = [COLS[0], COLS[5], COLS[1], COLS[2], COLS[3], COLS[4], COLS[0]]
    el[0].position = 0.0; el[0].color = (*hues[0], 1)
    el[1].position = 1.0; el[1].color = (*hues[-1], 1)
    for k in range(1, 6):
        e = el.new(k / 6)
        e.color = (*hues[k], 1)
    nt.links.new(mr.outputs['Result'], cr.inputs['Fac'])
    nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(cr.outputs['Color'], b.inputs['Emission Color'])
    b.inputs["Emission Strength"].default_value = 0.25
    sphere(mat=m)
    emblem(1, principled('rbstar', (1, 1, 1), rough=0.15, emit=(1, 1, 1), estr=0.6), s=0.2)


def bomb_orb():
    sphere(r=0.47, loc=(0, 0, -0.02), mat=principled('bomb', (0.03, 0.045, 0.1), rough=0.22, metal=0.55, coat=1.0))
    brass = principled('brass', (0.85, 0.55, 0.12), rough=0.25, metal=0.9, coat=0.6)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.13, depth=0.12, location=(0.16, 0, 0.42))
    cap = bpy.context.object
    cap.rotation_euler = (0, math.radians(24), 0)
    bpy.ops.object.shade_smooth()
    cap.data.materials.append(brass)
    bv = cap.modifiers.new('bv', 'BEVEL'); bv.width = 0.02; bv.segments = 3
    # 심지
    cu = bpy.data.curves.new('fuse', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 0.028
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(1)
    p0, p1 = sp.bezier_points
    p0.co = (0.2, 0, 0.47); p0.handle_left = (0.17, 0, 0.42); p0.handle_right = (0.24, 0, 0.56)
    p1.co = (0.36, 0, 0.53); p1.handle_left = (0.3, 0, 0.58); p1.handle_right = (0.42, 0, 0.5)
    fo = bpy.data.objects.new('fuse', cu)
    bpy.context.scene.collection.objects.link(fo)
    cu.materials.append(principled('rope', (0.85, 0.75, 0.55), rough=0.7, coat=0.0))
    # 붉은 경고 띠
    bpy.ops.mesh.primitive_torus_add(major_radius=0.465, minor_radius=0.03, location=(0, 0, -0.02))
    tr = bpy.context.object
    tr.rotation_euler = (math.radians(90), 0, math.radians(0))
    tr.rotation_euler = (math.radians(14), 0, 0)
    bpy.ops.object.shade_smooth()
    tr.data.materials.append(principled('band', (1.0, 0.25, 0.08), rough=0.3, emit=(1.0, 0.3, 0.05), estr=2.5))


def line_orb():
    c = (0.78, 0.86, 1.0)
    sphere(mat=principled('lnbody', c, rough=0.16, coat=1.0, sss=0.4, sss_col=(0.6, 0.85, 1.0), emit=(0.4, 0.7, 1.0), estr=0.1))
    emblem('arrows', principled('lnemb', (0.1, 0.85, 1.0), rough=0.2, emit=(0.1, 0.9, 1.0), estr=3.0), s=1.0, depth=0.04)


def gray_orb():
    sphere(mat=principled('gray', (0.3, 0.32, 0.4), rough=0.3, coat=0.6, sss=0.2, sss_col=(0.7, 0.7, 0.8)))


def ice_shell(cracked):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.555)
    o = bpy.context.object
    # 결정이 고르지 않게 꼭짓점을 살짝 흔든다(고정 시드)
    import random
    rnd = random.Random(7)
    for v in o.data.vertices:
        v.co *= 1.0 + rnd.uniform(-0.035, 0.035)
    m = bpy.data.materials.new('ice%d' % cracked)
    m.use_nodes = True
    m.blend_method = 'BLEND'
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.82, 0.95, 1.0, 1)
    b.inputs["Roughness"].default_value = 0.12
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.02
    b.inputs["Emission Color"].default_value = (0.55, 0.8, 1.0, 1)
    # 서리 — 가장자리(프레넬)는 하얗고 진하게, 가운데는 비쳐 보이게
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.35
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['To Min'].default_value = 0.30
    mr.inputs['To Max'].default_value = 0.92
    nt.links.new(lw.outputs['Facing'], mr.inputs['Value'])
    alpha_src = mr.outputs['Result']
    emit_src = None
    if cracked:
        vo = nt.nodes.new('ShaderNodeTexVoronoi')
        vo.feature = 'DISTANCE_TO_EDGE'
        vo.inputs['Scale'].default_value = 3.2
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
        cr = nt.nodes.new('ShaderNodeMapRange')
        cr.inputs['From Min'].default_value = 0.035
        cr.inputs['From Max'].default_value = 0.0
        nt.links.new(vo.outputs['Distance'], cr.inputs['Value'])
        mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
        lo = nt.nodes.new('ShaderNodeMath'); lo.operation = 'MULTIPLY'; lo.inputs[1].default_value = 0.7
        nt.links.new(alpha_src, lo.inputs[0])
        nt.links.new(lo.outputs[0], mx.inputs[0]); nt.links.new(cr.outputs['Result'], mx.inputs[1])
        alpha_src = mx.outputs[0]
        em = nt.nodes.new('ShaderNodeMath'); em.operation = 'MULTIPLY'; em.inputs[1].default_value = 2.2
        nt.links.new(cr.outputs['Result'], em.inputs[0])
        emit_src = em.outputs[0]
    nt.links.new(alpha_src, b.inputs['Alpha'])
    if emit_src is not None:
        nt.links.new(emit_src, b.inputs['Emission Strength'])
    else:
        b.inputs['Emission Strength'].default_value = 0.35
    o.data.materials.append(m)


def build(name):
    studio()
    if name.startswith('c'):
        color_orb(int(name[1:]))
    elif name.startswith('k'):
        cub_orb(int(name[1:]))
    elif name == 'rb':
        rainbow_orb()
    elif name == 'bm':
        bomb_orb()
    elif name == 'ln':
        line_orb()
    elif name == 'gy':
        gray_orb()
    elif name == 'ice':
        ice_shell(False)
    elif name == 'ice2':
        ice_shell(True)
    sc = bpy.context.scene
    sc.render.filepath = os.path.join(OUTDIR, name + ".png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = argv[0].split(',') if argv else ORDER
    for n in names:
        build(n)
        print('RENDERED', n)
