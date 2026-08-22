# -*- coding: utf-8 -*-
"""델타-브이 시편·설비 — 실사급 렌더 (2026-08-22).

운영자 지적: 어설픈 3D 대신 더 높은 퀄리티.

방향 전환의 근거: 캡슐 피규어 캐릭터는 이 스타일의 약점(얼굴 디테일)을
정면으로 노출한다. 그런데 이 게임에서 화면의 주인공은 사람이 아니라
**시편·설비·데이터**다. 그래서 캐릭터를 빼고 물체를 실사로 올린다.

실사로 보이게 하는 요소 (전부 여기 적용):
  1. **모든 모서리에 베벨.** 완벽히 날카로운 모서리가 CG 티의 1순위다.
     실제 물체는 아무리 정밀해도 모서리에 하이라이트가 생긴다
  2. **거칠기를 절차적으로 흔든다.** 균일한 roughness 는 플라스틱처럼 보인다
  3. **스튜디오 3점 조명 + 큰 소프트 키.** 큰 광원이 금속의 형태를 만든다
  4. **바닥과 접지 그림자.** 떠 있는 물체는 스티커처럼 보인다
  5. **피사계심도.** 초점이 있는 사진처럼 만든다
  6. **강철의 열변색(temper color).** 온도에 따라 짚색→보라→청색 산화막이
     생기는 실제 현상. 재료 게임에서 이보다 좋은 디테일이 없다

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P deltav_specimens.py
출력: scripts/og-assets/deltav/spec_*.png · rig.png
"""
import bpy
import math
import os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "..", "og-assets", "deltav")
os.makedirs(DIR, exist_ok=True)


def reset(res=(640, 480), samples=380):
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
    sc.view_settings.exposure = 0.15
    # 환경광 — 금속은 반사할 것이 있어야 금속으로 보인다.
    # 위는 밝고 아래는 어두운 스튜디오 그라디언트를 직접 만든다.
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
    mapn = nt.nodes.new("ShaderNodeMapping")
    texc = nt.nodes.new("ShaderNodeTexCoord")
    mapn.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    ramp.color_ramp.elements[0].color = (0.012, 0.016, 0.028, 1)
    ramp.color_ramp.elements[1].color = (0.075, 0.090, 0.125, 1)
    nt.links.new(texc.outputs['Generated'], mapn.inputs['Vector'])
    nt.links.new(mapn.outputs['Vector'], grad.inputs['Vector'])
    nt.links.new(grad.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    bg.inputs['Strength'].default_value = 1.0
    sc.world = w
    return sc


def cam(loc, look, lens=85, fstop=2.4):
    bpy.ops.object.camera_add(location=loc)
    c = bpy.context.object
    c.data.lens = lens
    d = Vector(look) - Vector(loc)
    c.rotation_mode = 'QUATERNION'
    c.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    # 피사계심도 — 사진처럼 보이게 하는 가장 값싼 장치
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


def studio(key=420, scale=1.0):
    """큰 소프트 키 + 차가운 필 + 뒤쪽 림. 금속의 형태는 광원의 크기가 만든다."""
    area((2.6 * scale, -1.9 * scale, 3.4 * scale), key, 4.5 * scale, (1.0, 0.96, 0.90))
    area((-3.0 * scale, -1.2 * scale, 1.5 * scale), key * 0.30, 5.0 * scale, (0.55, 0.72, 1.0))
    area((-0.6 * scale, 3.2 * scale, 2.2 * scale), key * 0.42, 3.4 * scale, (0.75, 0.88, 1.0))


def floor(color=(0.035, 0.042, 0.058), rough=0.42):
    """바닥 — 접지 그림자와 반사가 있어야 물체가 놓여 있는 것으로 보인다."""
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    p = bpy.context.object
    m = bpy.data.materials.new("floor")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    p.data.materials.append(m)
    return p


def pbr(name, base, rough=0.35, metal=0.0, aniso=0.0, rough_var=0.0,
        clearcoat=0.0, noise_scale=90.0):
    """거칠기를 절차적으로 흔든다 — 균일한 roughness 가 플라스틱 티의 근원."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if "Anisotropic" in b.inputs:
        b.inputs["Anisotropic"].default_value = aniso
    if clearcoat and "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = clearcoat
        b.inputs["Coat Roughness"].default_value = 0.08
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
        # 미세 요철 — 표면이 완벽히 평평하면 CG 로 읽힌다
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.06
        nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def bevel(o, width=0.004, segments=3):
    """**모든 모서리에 베벨.** 완벽히 날카로운 모서리가 CG 티의 1순위다."""
    md = o.modifiers.new("bev", 'BEVEL')
    md.width = width
    md.segments = segments
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(40)
    for p in o.data.polygons:
        p.use_smooth = True
    # 4.1 부터 use_auto_smooth 는 제거됐다. 삼항으로 감싸도 대입 자체는 일어나
    # AttributeError 가 난다 — 조건은 값이 아니라 대입에 걸어야 한다.
    return o


def dogbone(mat_body, thick=0.055):
    """인장 시편(도그본) — 재료시험의 표준 형상. 가운데가 좁아 거기서 끊어진다."""
    parts = []
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, thick / 2))
    g = bpy.context.object
    g.scale = (0.30, 1.05, thick)
    g.data.materials.append(mat_body)
    parts.append(bevel(g, 0.010))
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, sy * 0.78, thick / 2))
        h = bpy.context.object
        h.scale = (0.62, 0.50, thick)
        h.data.materials.append(mat_body)
        parts.append(bevel(h, 0.012))
    return parts


def render(name):
    bpy.context.scene.render.filepath = os.path.join(DIR, name)
    bpy.ops.render.render(write_still=True)
    print("  rendered", name)


def setup_specimen():
    """시편 전체가 프레임에 들어와야 한다. 1차 구도는 카메라가 너무 가깝고
       낮아 도그본이 잘렸다 — 물러서고 각도를 올린다."""
    reset(res=(720, 460), samples=420)
    cam((1.25, -2.55, 2.35), (0, 0.0, 0.05), lens=58, fstop=4.5)
    studio(430)
    floor()


# ─────────────────────── 시편 3종 ───────────────────────
def s_composite():
    """탄소복합재 — 직조 무늬 + 수지 광택. 가장자리는 그을리고 층이 벌어졌다."""
    setup_specimen()
    base = pbr("cfrp", (0.020, 0.021, 0.026), rough=0.22, metal=0.0,
               rough_var=0.10, clearcoat=0.55, noise_scale=40)
    # 직조 무늬 — 체커를 눌러 카본 위브를 흉내낸다
    nt = base.node_tree
    b = nt.nodes["Principled BSDF"]
    chk = nt.nodes.new("ShaderNodeTexChecker")
    chk.inputs["Scale"].default_value = 420.0
    chk.inputs["Color1"].default_value = (0.030, 0.031, 0.037, 1)
    chk.inputs["Color2"].default_value = (0.012, 0.013, 0.017, 1)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(45))
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], chk.inputs["Vector"])
    nt.links.new(chk.outputs["Color"], b.inputs["Base Color"])

    dogbone(base)
    char = pbr("char", (0.010, 0.009, 0.009), rough=0.92, metal=0.0, rough_var=0.06)
    # 그을린 띠
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.02, 0.0565))
    c = bpy.context.object
    c.scale = (0.302, 0.62, 0.002)
    c.data.materials.append(char)
    # 층간 박리 — 복합재의 대표적 파괴 양상
    for k, (x, y, a) in enumerate([(-0.05, 0.12, 0.28), (0.07, -0.10, -0.42)]):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0.058))
        cr = bpy.context.object
        cr.scale = (0.26, 0.010, 0.006)
        cr.rotation_euler = (0, 0, a)
        cr.data.materials.append(char)
    render("spec_composite.png")


def s_alloy():
    """알루미늄 리튬 합금 — 헤어라인 브러싱, 따뜻하고 둔한 금속."""
    setup_specimen()
    base = pbr("alli", (0.62, 0.615, 0.60), rough=0.30, metal=1.0,
               aniso=0.75, rough_var=0.09, noise_scale=200)
    dogbone(base)
    # 각인 — 실제 시편에는 로트 번호가 찍혀 있다
    ink = pbr("ink", (0.10, 0.10, 0.11), rough=0.80, metal=0.0)
    for k in range(4):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.13 + k * 0.085, 0.80, 0.0565))
        t = bpy.context.object
        t.scale = (0.030, 0.055, 0.002)
        t.data.materials.append(ink)
    render("spec_alloy.png")


def s_steel():
    """스테인리스강 — 거울에 가까운 브러시드 금속 + **열변색**.

    가열된 강철 표면에는 산화막 두께에 따라 짚색→보라→청색이 나타난다.
    실제 현상이고, 재료 게임에서 이보다 좋은 디테일이 없다."""
    setup_specimen()
    base = pbr("ss", (0.90, 0.915, 0.94), rough=0.17, metal=1.0,
               aniso=0.85, rough_var=0.06, noise_scale=260)
    dogbone(base)
    # 열변색 띠 — 가운데가 가장 뜨거웠으므로 청색, 바깥으로 갈수록 보라·짚색
    # 산화막은 금속 위의 얇은 간섭막이라 **금속성을 잃지 않는다**.
    # 1차에서는 밝은 파스텔 줄무늬로 보였다 — 어둡고 채도를 낮춰야 진짜 같다.
    tints = [(0.0, 0.20, (0.055, 0.085, 0.20)),
             (0.24, 0.13, (0.13, 0.075, 0.16)),
             (-0.24, 0.13, (0.13, 0.075, 0.16)),
             (0.40, 0.11, (0.26, 0.185, 0.065)),
             (-0.40, 0.11, (0.26, 0.185, 0.065))]
    for y, w, col in tints:
        m = pbr("tint%.2f" % y, col, rough=0.20, metal=1.0, aniso=0.7,
                rough_var=0.06, noise_scale=220)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y, 0.0562))
        t = bpy.context.object
        t.scale = (0.301, w, 0.0016)
        t.data.materials.append(m)
    render("spec_steel.png")


# ─────────────────────── 시험 설비 ───────────────────────
def s_rig():
    """고온 인장 시험기 — 노 안에서 시편을 당긴다. 미션 화면의 표제 이미지."""
    # 1차 구도는 카메라가 기계 안에 들어가 흰 상자와 기둥만 보였다.
    # 충분히 물러나 시험기 전체가 한 컷에 들어오게 한다.
    reset(res=(760, 480), samples=420)
    cam((3.6, -6.4, 3.3), (0, 0.05, 1.20), lens=52, fstop=6.0)
    studio(520, scale=2.2)
    floor((0.030, 0.036, 0.050), rough=0.36)

    STEEL = pbr("rs", (0.55, 0.57, 0.60), rough=0.30, metal=1.0, rough_var=0.10, noise_scale=120)
    DARK = pbr("rd", (0.055, 0.06, 0.075), rough=0.52, metal=0.3, rough_var=0.08)
    CERAMIC = pbr("rc", (0.80, 0.78, 0.74), rough=0.62, metal=0.0, rough_var=0.12, noise_scale=60)
    GLASS = bpy.data.materials.new("gl")
    GLASS.use_nodes = True
    gb = GLASS.node_tree.nodes["Principled BSDF"]
    gb.inputs["Base Color"].default_value = (0.9, 0.95, 1.0, 1)
    gb.inputs["Transmission Weight"].default_value = 1.0
    gb.inputs["Roughness"].default_value = 0.06
    HOT = bpy.data.materials.new("hot")
    HOT.use_nodes = True
    hb = HOT.node_tree.nodes["Principled BSDF"]
    hb.inputs["Emission Color"].default_value = (1.0, 0.42, 0.10, 1)
    hb.inputs["Emission Strength"].default_value = 26.0

    # 프레임 기둥 2개 + 상하 크로스헤드
    for sx in (-0.92, 0.92):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.085, depth=2.5, vertices=48,
                                            location=(sx, 0, 1.25))
        c = bpy.context.object
        c.data.materials.append(STEEL)
        bevel(c, 0.012)
    for z, h in ((0.16, 0.16), (2.30, 0.18)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z))
        cb = bpy.context.object
        cb.scale = (2.16, 0.52, h)
        cb.data.materials.append(DARK)
        bevel(cb, 0.018)

    # 노 — 세라믹 상자, 앞면에 관찰창
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.08, 1.22))
    f = bpy.context.object
    f.scale = (1.15, 0.80, 0.96)
    f.data.materials.append(CERAMIC)
    bevel(f, 0.022)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.33, 1.24))
    win = bpy.context.object
    win.scale = (0.60, 0.03, 0.44)
    win.data.materials.append(GLASS)
    bevel(win, 0.008)
    # 창 안쪽의 붉은 열
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.10, 1.24))
    hot = bpy.context.object
    hot.scale = (0.52, 0.02, 0.36)
    hot.data.materials.append(HOT)

    # 그립과 시편(노 위아래로 삐져나온 부분)
    for sz in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.05, 1.24 + sz * 0.62))
        gp = bpy.context.object
        gp.scale = (0.30, 0.26, 0.18)
        gp.data.materials.append(STEEL)
        bevel(gp, 0.014)
    render("rig.png")


if __name__ == "__main__":
    for fn, nm in ((s_composite, "composite"), (s_alloy, "alloy"),
                   (s_steel, "steel"), (s_rig, "rig")):
        print("==", nm)
        fn()
    print("DELTA-V SPECIMENS DONE ->", DIR)
