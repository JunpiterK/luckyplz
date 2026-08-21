# -*- coding: utf-8 -*-
"""럭키머지 천체 스프라이트 — Blender Cycles (2026-08-21 v2).

11단계 태양계 진화(운석→소행성→달→수성→금성→지구→화성→목성→토성→항성→블랙홀)를
각각 투명 배경 PNG 로 렌더한다.

v1 은 셰이더 노드만 썼다가 실패했다 — Voronoi 크레이터는 골프공처럼 보였고
목성 줄무늬는 좌표계 때문에 세로로 섰다. v2 는 planet_textures.py 가 만든
equirectangular 이미지(위도·경도를 직접 통제)를 UV 구에 감는다.
지구만 예외로 절차적 셰이더를 쓴다 — 대륙/바다 임계 + 구름층 + 대기 림이
이미 사실적으로 나왔다.

선행: python planet_textures.py   (텍스처 먼저 생성)
실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P planets_scene.py
출력: scripts/og-assets/planets/tier01.png ... tier11.png (384x384 투명)
"""
import bpy
import math
import os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "..", "og-assets", "planets")
os.makedirs(DIR, exist_ok=True)

RES = 384
SAMPLES = 180


# ────────────────────────────── 공통 ──────────────────────────────
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
    sc.view_settings.look = 'AgX - High Contrast'
    sc.view_settings.exposure = 0.18   # 명도 상향. 0.45 는 지구·태양이 하얗게 날아갔다
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    sc.world = w
    return sc


def add_camera(ortho=2.30):
    bpy.ops.object.camera_add(location=(0, -8, 0))
    cam = bpy.context.object
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ortho
    cam.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.camera = cam
    return cam


def add_lights(key_energy=6.2, rim_energy=3.2, warm=False):
    """왼쪽 위 키 + 오른쪽 뒤 림. 전 천체 공통이라 나란히 놓아도 광원이 일치한다."""
    bpy.ops.object.light_add(type='SUN', location=(-4, -4.5, 3.4))
    key = bpy.context.object
    key.data.energy = key_energy
    key.data.angle = math.radians(6)
    key.rotation_mode = 'QUATERNION'
    key.rotation_quaternion = (Vector((0, 0, 0)) - key.location).to_track_quat('-Z', 'Y')
    if warm:
        key.data.color = (1.0, 0.96, 0.90)
    bpy.ops.object.light_add(type='SUN', location=(3.6, 4.6, 1.6))
    rim = bpy.context.object
    rim.data.energy = rim_energy
    rim.data.color = (0.52, 0.68, 1.0)
    rim.rotation_mode = 'QUATERNION'
    rim.rotation_quaternion = (Vector((0, 0, 0)) - rim.location).to_track_quat('-Z', 'Y')


def uv_sphere(radius=1.0, segs=128, rings=64, tilt=0.0, spin=90.0):
    """equirectangular UV 를 가진 구.

    tilt = 자전축 기울기(도). 카메라가 -Y 에 있으므로 X 축 회전이 곧 기울기다.
    극관·극지방이 살짝 보여야 행성처럼 읽힌다 (기울기 0 이면 극이 정확히
    가장자리에 걸려 아예 안 보인다).
    spin = 자전각(도) — 텍스처의 어느 경도를 정면에 둘지.
    """
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=segs, ring_count=rings)
    o = bpy.context.object
    for p in o.data.polygons:
        p.use_smooth = True
    o.rotation_euler = (math.radians(tilt), 0, math.radians(spin))
    return o


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m


def img_node(mat, filename, non_color=False):
    nodes = mat.node_tree.nodes
    tex = nodes.new("ShaderNodeTexImage")
    path = os.path.join(DIR, filename)
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.extension = 'REPEAT'
    if non_color:
        tex.image.colorspace_settings.name = 'Non-Color'
    return tex


def textured_planet(obj, color_tex, height_tex=None, rough=0.9, bump=0.28, name="mat"):
    m = new_mat(name)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    col = img_node(m, color_tex)
    links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    # 행성 표면(암석 먼지·구름)에는 거울 반사가 없다. 기본 Specular 를 두면
    # 금성처럼 매끈한 재질에서 큰 타원 하이라이트가 생겨 즉시 CG 처럼 보인다
    for _k in ("Specular IOR Level", "Specular"):
        if _k in bsdf.inputs:
            bsdf.inputs[_k].default_value = 0.06
            break
    if height_tex:
        h = img_node(m, height_tex, non_color=True)
        bmp = nodes.new("ShaderNodeBump")
        bmp.inputs["Strength"].default_value = bump
        links.new(h.outputs["Color"], bmp.inputs["Height"])
        links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
    obj.data.materials.append(m)
    return m


def emissive_shell(radius, color, strength, name="shell", ior=1.45):
    """대기·코로나 — 프레넬로 가장자리에서만 보이는 발광 껍질."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=64, ring_count=32)
    o = bpy.context.object
    for p in o.data.polygons:
        p.use_smooth = True
    m = new_mat(name)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    out = nodes["Material Output"]
    for n in list(nodes):
        if n.type == 'BSDF_PRINCIPLED':
            nodes.remove(n)
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*color, 1)
    emit.inputs["Strength"].default_value = strength
    tr = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    fres = nodes.new("ShaderNodeFresnel")
    fres.inputs["IOR"].default_value = ior
    links.new(fres.outputs["Fac"], mix.inputs[0])
    links.new(tr.outputs[0], mix.inputs[1])
    links.new(emit.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    m.blend_method = 'BLEND'
    o.data.materials.append(m)
    return o


def annulus(inner, outer, segs=192, name="annulus"):
    """가운데가 뚫린 고리. U = 반경(0..1) 이라 1D 고리 텍스처를 그대로 쓴다."""
    verts, faces, uvs = [], [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        ca, sa = math.cos(a), math.sin(a)
        verts.append((ca * inner, sa * inner, 0.0))
        verts.append((ca * outer, sa * outer, 0.0))
    for i in range(segs):
        i0 = i * 2
        i1 = ((i + 1) % segs) * 2
        faces.append([i0, i0 + 1, i1 + 1, i1])
        uvs.extend([(0.0, 0.5), (1.0, 0.5), (1.0, 0.5), (0.0, 0.5)])
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for li, uv in enumerate(uvs):
        uvl.data[li].uv = uv
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def rough_shape(obj, scale=0.6, strength=0.3):
    """운석·소행성의 불규칙한 실루엣."""
    d = obj.modifiers.new("D", 'DISPLACE')
    t = bpy.data.textures.new("rock" + obj.name, 'CLOUDS')
    t.noise_scale = scale
    d.texture = t
    d.strength = strength


def render_to(name):
    bpy.context.scene.render.filepath = os.path.join(DIR, name)
    bpy.ops.render.render(write_still=True)
    print("  rendered", name)


# ──────────────────────────── 천체별 ────────────────────────────
def t01_meteor():
    reset_scene(); add_camera(); add_lights(warm=True)
    o = uv_sphere(1.0, 96, 48)
    rough_shape(o, 0.55, 0.34)
    textured_planet(o, "tex_meteor.png", "tex_meteor_h.png", rough=0.96, bump=0.5, name="meteor")
    render_to("tier01.png")


def t02_asteroid():
    reset_scene(); add_camera(); add_lights(warm=True)
    o = uv_sphere(1.0, 112, 56)
    rough_shape(o, 0.8, 0.22)
    textured_planet(o, "tex_asteroid.png", "tex_asteroid_h.png", rough=0.95, bump=0.45, name="asteroid")
    render_to("tier02.png")


def t03_moon():
    reset_scene(); add_camera(); add_lights()
    o = uv_sphere(1.0, tilt=14, spin=60)
    textured_planet(o, "tex_moon.png", "tex_moon_h.png", rough=0.95, bump=0.36, name="moon")
    render_to("tier03.png")


def t04_mercury():
    reset_scene(); add_camera(); add_lights(warm=True)
    o = uv_sphere(1.0, tilt=10, spin=140)
    textured_planet(o, "tex_mercury.png", "tex_mercury_h.png", rough=0.94, bump=0.34, name="mercury")
    render_to("tier04.png")


def t05_venus():
    reset_scene(); add_camera(); add_lights(key_energy=5.0, warm=True)
    o = uv_sphere(1.0, tilt=12, spin=30)
    textured_planet(o, "tex_venus.png", rough=0.92, name="venus")   # 0.55 면 넓은 반사 하이라이트가 생겨 얼룩처럼 보였다
    # 발광 껍질 제거 — 텍스처를 바꿔도 같은 자리에 밝은 타원이 남아 껍질이
    # 원인으로 확정됐다. 실제 금성도 균질한 크림색 구이지 발광 림이 없다
    render_to("tier05.png")


def t06_earth():
    """지구만 절차적 — 텍스처판은 색 배정이 뒤집혀 실패했고 이쪽이 이미 사실적."""
    reset_scene(); add_camera(); add_lights(key_energy=5.2)
    o = uv_sphere(1.0, tilt=23.4)
    m = new_mat("earth")
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes["Principled BSDF"]
    tex = nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 2.6
    tex.inputs["Detail"].default_value = 14.0
    tex.inputs["Roughness"].default_value = 0.58
    if "Distortion" in tex.inputs:
        tex.inputs["Distortion"].default_value = 1.1
    ramp = nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    # 딥블루 계열 (2026-08-21 운영자 요청) — 심해를 진한 코발트로 내리고
    # 얕은 바다를 선명한 청색으로 올려 물이 '파랗게' 읽히게 한다.
    # 대륙은 채도를 올려 바다와의 대비를 키웠다
    cr.elements[0].position = 0.00; cr.elements[0].color = (0.004, 0.022, 0.26, 1)
    e = cr.elements.new(0.42);  e.color = (0.008, 0.075, 0.50, 1)
    e = cr.elements.new(0.495); e.color = (0.02, 0.20, 0.74, 1)
    e = cr.elements.new(0.515); e.color = (0.86, 0.78, 0.50, 1)
    e = cr.elements.new(0.56);  e.color = (0.14, 0.52, 0.16, 1)
    e = cr.elements.new(0.70);  e.color = (0.36, 0.44, 0.16, 1)
    e = cr.elements.new(0.86);  e.color = (0.70, 0.66, 0.56, 1)
    links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bmp = nodes.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = 0.22
    links.new(tex.outputs["Fac"], bmp.inputs["Height"])
    links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.62
    o.data.materials.append(m)

    # 구름층
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.022, segments=96, ring_count=48)
    cl = bpy.context.object
    for p in cl.data.polygons:
        p.use_smooth = True
    cm = new_mat("clouds")
    cn, clk = cm.node_tree.nodes, cm.node_tree.links
    cout = cn["Material Output"]
    for n in list(cn):
        if n.type == 'BSDF_PRINCIPLED':
            cn.remove(n)
    diff = cn.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = (1, 1, 1, 1)
    tr = cn.new("ShaderNodeBsdfTransparent")
    mix = cn.new("ShaderNodeMixShader")
    cnz = cn.new("ShaderNodeTexNoise")
    cnz.inputs["Scale"].default_value = 4.5
    cnz.inputs["Detail"].default_value = 12.0
    if "Distortion" in cnz.inputs:
        cnz.inputs["Distortion"].default_value = 2.2
    cra = cn.new("ShaderNodeValToRGB")
    ccr = cra.color_ramp
    # 구름 임계 상향 — 0.50/0.66 은 구름이 지구를 덮어 바다가 안 보였다
    ccr.elements[0].position = 0.66; ccr.elements[0].color = (0, 0, 0, 1)
    ccr.elements[1].position = 0.82; ccr.elements[1].color = (1, 1, 1, 1)
    clk.new(cnz.outputs["Fac"], cra.inputs["Fac"])
    clk.new(cra.outputs["Color"], mix.inputs[0])
    clk.new(tr.outputs[0], mix.inputs[1])
    clk.new(diff.outputs[0], mix.inputs[2])
    clk.new(mix.outputs[0], cout.inputs["Surface"])
    cm.blend_method = 'BLEND'
    cl.data.materials.append(cm)

    # 강도 2.6 은 프레넬이 구 전체를 덮어 바다가 하늘색이 됐다 → 가장자리 힌트만
    emissive_shell(1.10, (0.20, 0.52, 1.0), 1.1, "earth_atmo")
    render_to("tier06.png")


def t07_mars():
    reset_scene(); add_camera(); add_lights(warm=True)
    o = uv_sphere(1.0, tilt=25, spin=70)
    textured_planet(o, "tex_mars.png", "tex_mars_h.png", rough=0.92, bump=0.26, name="mars")
    # 화성의 대기는 육안 규모에서 림으로 보이지 않는다. 얇은 껍질을 두면
    # 프레넬 얼룩만 생겨 제거했다 (2026-08-21)
    render_to("tier07.png")


def t08_jupiter():
    reset_scene(); add_camera(); add_lights(warm=True)
    o = uv_sphere(1.0, tilt=6, spin=-30)
    o.scale = (1.0, 1.0, 0.935)      # 자전 편평도
    textured_planet(o, "tex_jupiter.png", rough=0.72, name="jupiter")
    render_to("tier08.png")


def t09_saturn():
    # ortho 3.10 은 프레임 반폭 1.55 < 고리 2.05 라 좌우가 잘렸다 (2026-08-21 실측).
    # 고리를 1.60 으로 줄이고 프레임을 3.50 으로 — 게임에서도 고리가 과하지 않다
    reset_scene(); add_camera(ortho=3.50); add_lights(warm=True)
    o = uv_sphere(1.0, tilt=8)
    o.scale = (1.0, 1.0, 0.90)
    textured_planet(o, "tex_saturn.png", rough=0.70, name="saturn")

    ring = annulus(1.20, 1.60, 220, "saturn_ring")
    ring.rotation_euler = (math.radians(17), 0, math.radians(9))
    rm = new_mat("rings")
    rn, rl = rm.node_tree.nodes, rm.node_tree.links
    rout = rn["Material Output"]
    for n in list(rn):
        if n.type == 'BSDF_PRINCIPLED':
            rn.remove(n)
    rdiff = rn.new("ShaderNodeBsdfDiffuse")
    rtr = rn.new("ShaderNodeBsdfTransparent")
    rmix = rn.new("ShaderNodeMixShader")
    rcol = rn.new("ShaderNodeTexImage")
    rcol.image = bpy.data.images.load(os.path.join(DIR, "tex_rings.png"), check_existing=True)
    ralp = rn.new("ShaderNodeTexImage")
    ralp.image = bpy.data.images.load(os.path.join(DIR, "tex_rings_a.png"), check_existing=True)
    ralp.image.colorspace_settings.name = 'Non-Color'
    rl.new(rcol.outputs["Color"], rdiff.inputs["Color"])
    rl.new(ralp.outputs["Color"], rmix.inputs[0])
    rl.new(rtr.outputs[0], rmix.inputs[1])
    rl.new(rdiff.outputs[0], rmix.inputs[2])
    rl.new(rmix.outputs[0], rout.inputs["Surface"])
    rm.blend_method = 'BLEND'
    rm.shadow_method = 'NONE' if hasattr(rm, 'shadow_method') else None
    ring.data.materials.append(rm)
    render_to("tier09.png")


def t10_star():
    sc = reset_scene(); add_camera(ortho=2.62)
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    o = uv_sphere(1.0, tilt=8, spin=20)
    m = new_mat("star")
    nodes, links = m.node_tree.nodes, m.node_tree.links
    out = nodes["Material Output"]
    for n in list(nodes):
        if n.type == 'BSDF_PRINCIPLED':
            nodes.remove(n)
    emit = nodes.new("ShaderNodeEmission")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(DIR, "tex_sun.png"), check_existing=True)
    links.new(tex.outputs["Color"], emit.inputs["Color"])
    emit.inputs["Strength"].default_value = 1.35  # 표준 변환에서는 1.35 가 금빛. 2.6 은 R,G 가 모두 클리핑돼 형광 노랑이 된다
    links.new(emit.outputs[0], out.inputs["Surface"])
    o.data.materials.append(m)
    emissive_shell(1.08, (1.0, 0.66, 0.16), 2.2, "corona1")
    emissive_shell(1.18, (1.0, 0.40, 0.07), 1.1, "corona2")
    render_to("tier10.png")


def t11_blackhole():
    reset_scene(); add_camera(ortho=2.85)
    # 사건의 지평선 — 빛을 전혀 내지 않는 완전한 검정
    o = uv_sphere(0.47, 64, 32)
    m = new_mat("horizon")
    nodes, links = m.node_tree.nodes, m.node_tree.links
    out = nodes["Material Output"]
    for n in list(nodes):
        if n.type == 'BSDF_PRINCIPLED':
            nodes.remove(n)
    blk = nodes.new("ShaderNodeEmission")
    blk.inputs["Color"].default_value = (0, 0, 0, 1)
    blk.inputs["Strength"].default_value = 0.0
    links.new(blk.outputs[0], out.inputs["Surface"])
    o.data.materials.append(m)

    # 광자 링
    bpy.ops.mesh.primitive_torus_add(major_radius=0.62, minor_radius=0.013,
                                     major_segments=128, minor_segments=12)
    ph = bpy.context.object
    ph.rotation_euler = (math.radians(11), 0, 0)
    pm = new_mat("photon")
    pn, pl = pm.node_tree.nodes, pm.node_tree.links
    pout = pn["Material Output"]
    for n in list(pn):
        if n.type == 'BSDF_PRINCIPLED':
            pn.remove(n)
    pe = pn.new("ShaderNodeEmission")
    pe.inputs["Color"].default_value = (1.0, 0.90, 0.62, 1)
    pe.inputs["Strength"].default_value = 26.0
    pl.new(pe.outputs[0], pout.inputs["Surface"])
    ph.data.materials.append(pm)

    # 정면 광자링 — 지평선 바로 둘레의 밝은 테. 기울인 원반만으로는
    # 검은 반구처럼 보여서, 이 링이 있어야 블랙홀로 읽힌다
    bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.020,
                                     major_segments=128, minor_segments=10)
    ph2 = bpy.context.object
    ph2.rotation_euler = (math.radians(90), 0, 0)
    pm2 = new_mat("photon2")
    pn2, pl2 = pm2.node_tree.nodes, pm2.node_tree.links
    pout2 = pn2["Material Output"]
    for n in list(pn2):
        if n.type == 'BSDF_PRINCIPLED':
            pn2.remove(n)
    pe2 = pn2.new("ShaderNodeEmission")
    pe2.inputs["Color"].default_value = (1.0, 0.93, 0.72, 1)
    pe2.inputs["Strength"].default_value = 40.0
    pl2.new(pe2.outputs[0], pout2.inputs["Surface"])
    ph2.data.materials.append(pm2)

    # 강착원반 — 반경 방향 그라데이션(안쪽이 뜨겁다) + 얇은 두께
    disk = annulus(0.62, 1.34, 220, "accretion")
    disk.rotation_euler = (math.radians(11), 0, 0)   # 90도=정면, 0도=완전 옆. 눕힐수록 지평선이 온전한 원으로 남는다
    dm = new_mat("disk")
    dn, dl = dm.node_tree.nodes, dm.node_tree.links
    dout = dn["Material Output"]
    for n in list(dn):
        if n.type == 'BSDF_PRINCIPLED':
            dn.remove(n)
    de = dn.new("ShaderNodeEmission")
    # U = 반경(0 안쪽 ~ 1 바깥) → 안쪽 흰-노랑, 바깥 주황-적
    uvn = dn.new("ShaderNodeUVMap")
    sep = dn.new("ShaderNodeSeparateXYZ")
    dl.new(uvn.outputs["UV"], sep.inputs["Vector"])
    dramp = dn.new("ShaderNodeValToRGB")
    dcr = dramp.color_ramp
    while len(dcr.elements) > 1:
        dcr.elements.remove(dcr.elements[-1])
    dcr.elements[0].position = 0.0;  dcr.elements[0].color = (1.0, 0.98, 0.86, 1)
    e = dcr.elements.new(0.30); e.color = (1.0, 0.78, 0.26, 1)
    e = dcr.elements.new(0.65); e.color = (1.0, 0.42, 0.08, 1)
    e = dcr.elements.new(1.0);  e.color = (0.55, 0.12, 0.02, 1)
    dl.new(sep.outputs["X"], dramp.inputs["Fac"])
    dl.new(dramp.outputs["Color"], de.inputs["Color"])
    de.inputs["Strength"].default_value = 9.0
    dl.new(de.outputs[0], dout.inputs["Surface"])
    disk.data.materials.append(dm)
    render_to("tier11.png")


ALL = [t01_meteor, t02_asteroid, t03_moon, t04_mercury, t05_venus, t06_earth,
       t07_mars, t08_jupiter, t09_saturn, t10_star, t11_blackhole]

for fn in ALL:
    print("==", fn.__name__)
    fn()

print("ALL PLANETS DONE ->", DIR)
