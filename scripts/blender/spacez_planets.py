# -*- coding: utf-8 -*-
"""Space-Z v5 태양계 히어로 천체 — Blender Cycles 렌더 + WebP 굽기 (2026-09-27, P6).

0~9존(플레이어의 90%가 보는 구간)의 천체를 '그 행성'으로 읽히게 다시 만든다.
지구 첫인상(림 + 구름 + 밤쪽 도시불빛 + 일출 산란), 달 앞면의 실제 바다, 화성의
매리너 협곡·타르시스, 목성 대적점 정면, 토성 고리 22°·카시니 간극·고리 그림자,
누운 천왕성, 해왕성 대암반, 명왕성 톰보 하트.

한 파일이 두 모드로 돈다
  일반 파이썬 : python scripts/blender/spacez_planets.py all        # 텍스처 → 렌더 → 굽기 전부
                python scripts/blender/spacez_planets.py tex        # planet_textures.SZ_ALL 만
                python scripts/blender/spacez_planets.py render [이름..]  # Blender 를 서브프로세스로
                python scripts/blender/spacez_planets.py post [--shots 폴더]  # webp·_lo·엽서·운석 림·매니페스트
  Blender     : blender.exe -b -P scripts/blender/spacez_planets.py -- [이름..]

출력
  중간 PNG : scripts/og-assets/spacez_z/<이름>.png  (투명, 슈퍼샘플)
  게임 자산 : public/assets/spacez/z/<이름>.webp + <이름>_lo.webp (절반 해상도)
              pc_00~pc_12.webp (엽서 썸네일 96px, 투명 — 안 가 본 존은 CSS 로 실루엣 처리 가능)
              meteor_a_rim/b_rim/c_rim.webp (위험 색 림을 구운 운석 — 기존 meteor_*.webp 는 건드리지 않음)
  매니페스트 : --manifest 경로 (기본 scripts/og-assets/spacez_z/manifest.json)

규칙 (메모 planet_art_pipeline — 되돌리기 금지)
  - roughness ≥ 0.9, Specular IOR Level 0.06 — 행성에 거울 하이라이트는 없다
  - 얇은 발광 껍질(emissive shell < 1.075) 금지 — 프레넬 얼룩. 지구 대기는 껍질이 아니라
    '볼륨 산란'으로 만든다(접선 방향 광학 깊이가 길어 림에서만 빛나고, 태양빛이 붉어진다)
  - 실제 축 기울기. 행성은 AgX High Contrast + exposure 0.18
  - 굽는 단계에서 최대 휘도 0.70 (운석이 밝은 행성 위에서도 읽히게 — ART-13)
  - 회전 프레임은 만들지 않는다(존 체류 25초 안에 자전은 체감되지 않고 용량만 4~16배)
"""
import math
import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TEX_DIR = os.path.join(ROOT, "scripts", "og-assets", "planets")
REN_DIR = os.path.join(ROOT, "scripts", "og-assets", "spacez_z")
PUB_DIR = os.path.join(ROOT, "public", "assets", "spacez", "z")
BLENDER = os.environ.get("BLENDER_EXE", r"C:/tools/blender-4.2.5-windows-x64/blender.exe")

# 게임 자산 표 — 이름: (렌더 PNG, 최종 폭, 최종 높이, 예산 KB, 메모)
# disk = 스프라이트 폭 대비 행성 원반 지름 비율 (런타임이 반지름 r 로 그릴 때: 그리기 폭 = 2r / disk)
ASSETS = {
    "z00_earth_limb": dict(src="earth_limb", w=1080, h=560, kb=85, lo=True),
    # 구름은 알파가 디테일을 전부 들고 색은 매끈한 음영뿐 → 색을 흐리고 알파를 손실 압축(q40)해야 예산 안에 든다
    "z00_clouds":     dict(src="earth_clouds", w=1080, h=560, kb=40, lo=True, aq=40, rgb_blur=1.5),
    "zone_moon":      dict(src="moon", w=512, h=512, kb=40, lo=True),
    "earth_small":    dict(src="earth_small", w=128, h=128, kb=8, lo=True),
    "zone_mars":      dict(src="mars", w=512, h=512, kb=45, lo=True),
    "phobos":         dict(src="phobos", w=96, h=96, kb=4, lo=True),
    "zone_jupiter":   dict(src="jupiter", w=768, h=768, kb=70, lo=True),
    "io":             dict(src="io", w=96, h=96, kb=4, lo=True),
    "zone_saturn":    dict(src="saturn", w=896, h=560, kb=75, lo=True),
    "titan":          dict(src="titan", w=96, h=96, kb=4, lo=True),
    "zone_uranus":    dict(src="uranus", w=448, h=448, kb=28, lo=True),
    "zone_neptune":   dict(src="neptune", w=448, h=448, kb=28, lo=True),
    "zone_pluto":     dict(src="pluto", w=384, h=384, kb=22, lo=True),
    "charon":         dict(src="charon", w=192, h=192, kb=8, lo=True),
}

# ══════════════════════════════ Blender 쪽 ══════════════════════════════
try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False


def _load_planet_helpers():
    """planets_scene.py 의 공통 헬퍼(reset_scene·add_camera·add_lights·uv_sphere·textured_planet·annulus…)를 가져온다.

    그 파일은 모듈 끝에서 11개 천체를 바로 렌더한다(__main__ 가드 없음). 그대로 import 하면
    행성 키우기 스프라이트를 전부 다시 굽게 되므로, '천체별' 절 앞까지만 잘라 실행한다.
    """
    p = os.path.join(HERE, "planets_scene.py")
    src = open(p, encoding="utf-8").read()
    cut = src.index("def t01_meteor")
    ns = {"__name__": "planets_scene_helpers", "__file__": p}
    exec(compile(src[:cut], p, "exec"), ns)
    ns["DIR"] = TEX_DIR            # img_node() 가 텍스처를 찾는 폴더
    return ns


if IN_BLENDER:
    import bpy
    from mathutils import Vector
    H = _load_planet_helpers()
    os.makedirs(REN_DIR, exist_ok=True)

    def scene(res_x, res_y, samples=160, look='AgX - High Contrast', exposure=0.18):
        H["RES"] = res_x
        H["SAMPLES"] = samples
        sc = H["reset_scene"]()
        sc.render.resolution_x = res_x
        sc.render.resolution_y = res_y
        sc.render.resolution_percentage = 100
        sc.view_settings.look = look
        sc.view_settings.exposure = exposure
        sc.render.image_settings.color_mode = 'RGBA'
        sc.render.image_settings.color_depth = '8'
        sc.render.filter_size = 1.2
        return sc

    def camera_ortho(scale, z=0.0, x=0.0):
        cam = H["add_camera"](ortho=scale)
        cam.location = (x, -12, z)
        cam.data.clip_end = 100
        return cam

    def sun(direction, energy, color=(1, 1, 1), angle=0.6):
        """direction = 천체에서 태양 쪽을 향한 벡터."""
        bpy.ops.object.light_add(type='SUN', location=tuple(Vector(direction).normalized() * 10))
        l = bpy.context.object
        l.data.energy = energy
        l.data.color = color
        l.data.angle = math.radians(angle)
        l.rotation_mode = 'QUATERNION'
        l.rotation_quaternion = (-Vector(direction)).to_track_quat('-Z', 'Y')
        return l

    def sphere(r=1.0, tilt=0.0, face_lon=0.0, roll=0.0, segs=256, rings=128, oblate=1.0):
        """face_lon = 카메라 정면에 올 텍스처 경도, tilt = 카메라 쪽으로 기운 북극(= 화면 중심 위도),
        roll = 화면 평면 회전. 회전 순서 Z(자전)→X(기울기)→Y(화면 회전).
        (planets_scene.uv_sphere 는 XYZ 순이라 spin 이 극을 옆으로 눕힌다 — 여기서는 쓰지 않는다)
        실측: spin 0 에서 정면 경도는 -90, 동쪽이 화면 오른쪽."""
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=segs, ring_count=rings)
        o = bpy.context.object
        for p in o.data.polygons:
            p.use_smooth = True
        o.scale = (1, 1, oblate)
        bpy.ops.object.transform_apply(scale=True)
        o.rotation_mode = 'ZXY'
        o.rotation_euler = (math.radians(tilt), math.radians(roll), math.radians(-90.0 - face_lon))
        return o

    def _mat_bsdf(m):
        return m.node_tree.nodes["Principled BSDF"]

    def planet_mat(o, tex, height=None, bump=0.25, rough=0.93, limb=None, limb_amt=0.0, name="p"):
        """행성 표면. limb = 가장자리 색(얇은 대기 산란을 껍질 대신 표면 셰이더에서 — 프레넬 얼룩 없음)."""
        m = H["textured_planet"](o, tex, height, rough=rough, bump=bump, name=name)
        if limb and limb_amt > 0:
            nt = m.node_tree
            bsdf = _mat_bsdf(m)
            link = [l for l in nt.links if l.to_socket == bsdf.inputs["Base Color"]][0]
            src = link.from_socket
            nt.links.remove(link)
            lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
            pw = nt.nodes.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.2
            nt.links.new(lw.outputs["Facing"], pw.inputs[0])
            mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = limb_amt
            nt.links.new(pw.outputs[0], mul.inputs[0])
            mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
            sock = lambda coll, nm: [x for x in coll if x.name == nm and x.type == 'RGBA' and x.enabled][0]
            nt.links.new(mul.outputs[0], mix.inputs[0])
            nt.links.new(src, sock(mix.inputs, "A"))
            sock(mix.inputs, "B").default_value = (*limb, 1)
            nt.links.new(sock(mix.outputs, "Result"), bsdf.inputs["Base Color"])
        return m

    def img(nt, fname, non_color=False, interp='Cubic'):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(TEX_DIR, fname), check_existing=True)
        if non_color:
            t.image.colorspace_settings.name = 'Non-Color'
        t.interpolation = interp
        return t

    def math_node(nt, op, a=None, b=None, v1=None):
        n = nt.nodes.new("ShaderNodeMath"); n.operation = op
        if isinstance(a, (int, float)):
            n.inputs[0].default_value = a
        elif a is not None:
            nt.links.new(a, n.inputs[0])
        if b is not None:
            if isinstance(b, (int, float)):
                n.inputs[1].default_value = b
            else:
                nt.links.new(b, n.inputs[1])
        return n

    def new_mat(name):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        return m

    def atmosphere_volume(radius, H_scale, rho0, color=(0.26, 0.55, 1.0), aniso=0.35, name="atmo"):
        """레일리 산란 흉내 볼륨. 밀도 = rho0·exp(-(r-1)/H). 청색이 가장 강하게 산란되고
        접선으로 긴 경로를 지난 햇빛은 붉어진다 → 림은 파랗고 명암 경계 근처는 주황."""
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=256, ring_count=128)
        o = bpy.context.object
        o.name = name
        for p in o.data.polygons:
            p.use_smooth = True
        m = new_mat(name)
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type == 'BSDF_PRINCIPLED':
                nt.nodes.remove(n)
        out = nt.nodes["Material Output"]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'
        nt.links.new(tc.outputs["Object"], ln.inputs[0])
        a = math_node(nt, 'SUBTRACT', ln.outputs["Value"], 1.0)
        a = math_node(nt, 'DIVIDE', a.outputs[0], H_scale)
        a = math_node(nt, 'MULTIPLY', a.outputs[0], -1.0)
        a = math_node(nt, 'EXPONENT', a.outputs[0])
        a = math_node(nt, 'MULTIPLY', a.outputs[0], rho0)
        vs = nt.nodes.new("ShaderNodeVolumeScatter")
        vs.inputs["Color"].default_value = (*color, 1)
        vs.inputs["Anisotropy"].default_value = aniso
        nt.links.new(a.outputs[0], vs.inputs["Density"])
        nt.links.new(vs.outputs[0], out.inputs["Volume"])
        m.cycles.volume_interpolation = 'LINEAR'
        o.data.materials.append(m)
        return o

    def earth_surface(o, sun_dir, lights=2.2, holdout=False, speckle=False):
        m = new_mat("earth")
        nt = m.node_tree
        bsdf = _mat_bsdf(m)
        out = nt.nodes["Material Output"]
        if holdout:
            for n in list(nt.nodes):
                if n.type == 'BSDF_PRINCIPLED':
                    nt.nodes.remove(n)
            ho = nt.nodes.new("ShaderNodeHoldout")
            nt.links.new(ho.outputs[0], out.inputs["Surface"])
            o.data.materials.append(m)
            return m
        col = img(nt, "tex_sz_earth.png")
        nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.92
        bsdf.inputs["Specular IOR Level"].default_value = 0.06
        hh = img(nt, "tex_sz_earth_h.png", non_color=True)
        bmp = nt.nodes.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.18
        bmp.inputs["Distance"].default_value = 0.02
        nt.links.new(hh.outputs["Color"], bmp.inputs["Height"])
        nt.links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
        # 밤쪽 도시불빛: 불빛 맵 × (햇빛 반대쪽 마스크)
        if speckle:
            # 확대(림): 부드러운 밀도 × 보로노이 알갱이(≈3px 간격) × 군집 노이즈 → 도시 불빛 알갱이
            dn = img(nt, "tex_sz_earth_lightsd.png", non_color=True)
            vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 900.0
            pt_ = math_node(nt, 'DIVIDE', vo.outputs["Distance"], 0.30)
            pt_ = math_node(nt, 'SUBTRACT', 1.0, pt_.outputs[0]); pt_.use_clamp = True
            pt_ = math_node(nt, 'POWER', pt_.outputs[0], 2.0)
            cn = nt.nodes.new("ShaderNodeTexNoise"); cn.inputs["Scale"].default_value = 260.0
            cn.inputs["Detail"].default_value = 4.0
            cl_ = nt.nodes.new("ShaderNodeMapRange")
            cl_.inputs["From Min"].default_value = 0.40; cl_.inputs["From Max"].default_value = 0.62
            nt.links.new(cn.outputs["Fac"], cl_.inputs["Value"])
            sp = math_node(nt, 'MULTIPLY', pt_.outputs[0], cl_.outputs["Result"])
            sp = math_node(nt, 'MULTIPLY', sp.outputs[0], 2.4)
            sp = math_node(nt, 'ADD', sp.outputs[0], 0.06)
            li_v = math_node(nt, 'MULTIPLY', dn.outputs["Color"], sp.outputs[0])
            li_out = li_v.outputs[0]
        else:
            li = img(nt, "tex_sz_earth_lights.png", non_color=True)
            li_out = li.outputs["Color"]
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        dp = nt.nodes.new("ShaderNodeVectorMath"); dp.operation = 'DOT_PRODUCT'
        nt.links.new(geo.outputs["True Normal"], dp.inputs[0])
        dp.inputs[1].default_value = tuple(Vector(sun_dir).normalized())
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.08
        mr.inputs["From Max"].default_value = -0.12
        mr.clamp = True
        nt.links.new(dp.outputs["Value"], mr.inputs["Value"])
        mul = math_node(nt, 'MULTIPLY', li_out, mr.outputs["Result"])
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.70, 0.36, 1)
        s = math_node(nt, 'MULTIPLY', mul.outputs[0], lights)
        nt.links.new(s.outputs[0], bsdf.inputs["Emission Strength"])
        o.data.materials.append(m)
        return m

    def cloud_shell(radius, visible_cam=True, detail=True, limb_fade=0.75, dens=1.0):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=384, ring_count=192)
        o = bpy.context.object
        o.name = "clouds"
        for p in o.data.polygons:
            p.use_smooth = True
        o.rotation_mode = 'ZXY'
        m = new_mat("clouds")
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type == 'BSDF_PRINCIPLED':
                nt.nodes.remove(n)
        out = nt.nodes["Material Output"]
        ct = img(nt, "tex_sz_earth_clouds.png", non_color=True)
        a = ct.outputs["Color"]
        if detail:
            # 확대(림 1080px)에서 텍스처 해상도를 넘는 결은 절차적 노이즈로 보탠다
            nz = nt.nodes.new("ShaderNodeTexNoise")
            nz.inputs["Scale"].default_value = 180.0
            nz.inputs["Detail"].default_value = 8.0
            nz.inputs["Roughness"].default_value = 0.62
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.inputs["From Min"].default_value = 0.35; mr.inputs["From Max"].default_value = 0.65
            mr.inputs["To Min"].default_value = 0.55; mr.inputs["To Max"].default_value = 1.15
            nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
            mm = math_node(nt, 'MULTIPLY', a, mr.outputs["Result"])
            a = mm.outputs[0]
        a = math_node(nt, 'MULTIPLY', a, dens).outputs[0]
        if limb_fade > 0:
            lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
            pw = math_node(nt, 'POWER', lw.outputs["Facing"], 3.0)
            f = math_node(nt, 'MULTIPLY', pw.outputs[0], limb_fade)
            inv = math_node(nt, 'SUBTRACT', 1.0, f.outputs[0])
            a = math_node(nt, 'MULTIPLY', a, inv.outputs[0]).outputs[0]
        a = math_node(nt, 'MINIMUM', a, 1.0).outputs[0]
        diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
        diff.inputs["Color"].default_value = (0.92, 0.93, 0.95, 1)
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(a, mix.inputs[0])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(diff.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        m.blend_method = 'BLEND'
        o.data.materials.append(m)
        o.visible_camera = visible_cam
        return o

    def render(name):
        bpy.context.scene.render.filepath = os.path.join(REN_DIR, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("  rendered", name, flush=True)

    # ─── 지구 림 (존 0 첫인상) ───
    # 구 반지름 1 = 화면 1350px (곡률 반지름 = 폭의 1.25배). 림 꼭대기는 위에서 150px.
    # 정면 경도 128°E·위도 -15° → 림 꼭대기는 75°N(시베리아). 가운데 아래로 한반도·일본·중국 동해안이
    # 오고(림에서 38° 아래 = 위에서 436px), 왼쪽 아래 모서리가 밤(도시불빛)이다. 태양은 오른쪽 위 뒤 →
    # 화면 대부분이 낮이고 명암 경계가 왼쪽 아래를 대각으로 지난다.
    # (1차 시안: 정면 145°E·-40° + 태양 오른쪽 뒤 — 태평양만 보이고 절반이 밤이라 첫인상이 어두웠다)
    LIMB_W, LIMB_H, LIMB_R = 1080, 560, 1350.0
    LIMB_TOP = 150
    EARTH_SUN = (0.75, 0.28, 0.55)
    EARTH_ROT = dict(tilt=-15.0, face_lon=128.0)

    def _limb_scene(samples):
        sc = scene(LIMB_W, LIMB_H, samples=samples)
        sc.cycles.volume_step_rate = 0.12
        sc.cycles.volume_max_steps = 2048
        cz = 1.0 + LIMB_TOP / LIMB_R - (LIMB_H / 2) / LIMB_R
        camera_ortho(LIMB_W / LIMB_R, z=cz)
        sun(EARTH_SUN, 6.2, color=(1.0, 0.97, 0.92), angle=0.53)
        e = sphere(1.0, segs=512, rings=256, **EARTH_ROT)
        return sc, e

    def r_earth_limb():
        sc, e = _limb_scene(256)
        earth_surface(e, EARTH_SUN, lights=4.0, speckle=True)
        # 구름: 카메라에는 안 보이고 그림자만 드리운다(구름 스프라이트는 따로 굽는다)
        cl = cloud_shell(1.006, visible_cam=False)
        cl.rotation_euler = e.rotation_euler
        atmosphere_volume(1.035, 0.0050, 9.0, color=(0.12, 0.38, 1.0))
        render("earth_limb")

    def r_earth_clouds():
        sc, e = _limb_scene(128)
        earth_surface(e, EARTH_SUN, holdout=True)
        cl = cloud_shell(1.006, visible_cam=True)
        cl.rotation_euler = e.rotation_euler
        render("earth_clouds")

    def r_earth_small():
        """달에서 본 지구(지구돋이). 구름·대기 포함 한 장. 광원은 달과 같은 왼쪽 앞 위."""
        sc = scene(512, 512, samples=192)
        sc.cycles.volume_step_rate = 0.25
        camera_ortho(2.0 * 1.06 / 0.90)
        sdir = (-4.0, -4.5, 3.4)
        sun(sdir, 5.2)
        rot = dict(tilt=18.0, face_lon=12.0)
        e = sphere(1.0, **rot)
        earth_surface(e, sdir, lights=1.4)
        cl = cloud_shell(1.008, visible_cam=True, detail=False, limb_fade=0.4, dens=0.9)
        cl.rotation_euler = e.rotation_euler
        atmosphere_volume(1.06, 0.018, 7.0)
        render("earth_small")

    # ─── 위성·행성 공통 ───
    DISK = 0.94      # 원반 지름 / 프레임 폭

    def simple_body(name, res, tex, height=None, bump=0.25, tilt=0.0, face_lon=0.0, roll=0.0, oblate=1.0,
                    rough=0.93, limb=None, limb_amt=0.0, key=6.2, rim=3.2, warm=False, samples=160, disk=DISK):
        sc = scene(res, res, samples=samples)
        camera_ortho(2.0 / disk)
        H["add_lights"](key_energy=key, rim_energy=rim, warm=warm)
        o = sphere(1.0, tilt=tilt, face_lon=face_lon, roll=roll, oblate=oblate)
        planet_mat(o, tex, height, bump=bump, rough=rough, limb=limb, limb_amt=limb_amt, name=name)
        render(name)
        return o

    def r_moon():
        simple_body("moon", 1024, "tex_sz_moon.png", "tex_sz_moon_h.png", bump=0.12, tilt=6.7, face_lon=0.0,
                    rough=0.96)

    def r_mars():
        simple_body("mars", 1024, "tex_sz_mars.png", "tex_sz_mars_h.png", bump=0.16, tilt=20.0, face_lon=-80.0,
                    rough=0.94, limb=(0.95, 0.70, 0.58), limb_amt=0.28, warm=True)

    def r_jupiter():
        simple_body("jupiter", 1152, "tex_sz_jupiter.png", None, tilt=3.1, face_lon=4.0, oblate=0.935,
                    rough=0.92, warm=True, limb=(0.72, 0.70, 0.68), limb_amt=0.12, rim=1.4)

    def r_io():
        simple_body("io", 384, "tex_sz_io.png", None, tilt=0.0, face_lon=80.0, rough=0.94, warm=True)

    def r_titan():
        simple_body("titan", 384, "tex_sz_titan.png", None, tilt=10.0, face_lon=0.0, rough=0.95, warm=True,
                    limb=(1.0, 0.78, 0.45), limb_amt=0.55)

    def r_neptune():
        simple_body("neptune", 896, "tex_sz_neptune.png", None, tilt=-12.0, face_lon=18.0, rough=0.93,
                    limb=(0.55, 0.70, 1.0), limb_amt=0.30)

    def r_pluto():
        simple_body("pluto", 768, "tex_sz_pluto.png", "tex_sz_pluto_h.png", bump=0.14, tilt=8.0, face_lon=-25.0,
                    rough=0.95)

    def r_charon():
        simple_body("charon", 384, "tex_sz_charon.png", "tex_sz_charon_h.png", bump=0.15, tilt=38.0,
                    face_lon=0.0, rough=0.95)

    def r_phobos():
        sc = scene(384, 384, samples=160)
        camera_ortho(2.0 / 0.90)
        H["add_lights"](key_energy=6.8, rim_energy=3.0, warm=True)
        o = sphere(1.0, tilt=12, face_lon=40.0, roll=-25, segs=192, rings=96)
        o.scale = (1.0, 0.80, 0.70)
        d = o.modifiers.new("D", 'DISPLACE')
        t = bpy.data.textures.new("phobos_n", 'CLOUDS'); t.noise_scale = 0.75
        d.texture = t; d.strength = 0.16; d.mid_level = 0.5
        planet_mat(o, "tex_sz_phobos.png", "tex_sz_phobos_h.png", bump=0.5, rough=0.97, name="phobos")
        render("phobos")

    def r_proxb():
        """엽서 pc_11 용 — 붉은 왜성빛을 등진 암석 행성 초승달."""
        sc = scene(384, 384, samples=128)
        camera_ortho(2.0 / 0.94)
        sun((0.9, 0.35, 0.35), 9.0, color=(1.0, 0.50, 0.30))
        o = sphere(1.0, tilt=10, face_lon=30)
        planet_mat(o, "tex_sz_charon.png", "tex_sz_charon_h.png", bump=0.3, rough=0.95, name="proxb")
        render("proxb")

    # ─── 토성 ───
    def ring_mat(tex_c, tex_a, name, translucent=0.25):
        m = new_mat(name)
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type == 'BSDF_PRINCIPLED':
                nt.nodes.remove(n)
        out = nt.nodes["Material Output"]
        c = img(nt, tex_c, interp='Linear')
        a = img(nt, tex_a, non_color=True, interp='Linear')
        diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
        nt.links.new(c.outputs["Color"], diff.inputs["Color"])
        tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
        nt.links.new(c.outputs["Color"], tl.inputs["Color"])
        mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = translucent
        nt.links.new(diff.outputs[0], mx.inputs[1]); nt.links.new(tl.outputs[0], mx.inputs[2])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(a.outputs["Color"], mix.inputs[0])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(mx.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        m.blend_method = 'BLEND'
        return m

    SAT_OPEN = 22.0

    def r_saturn():
        # 896x560 을 1.5배로. 고리 외경 2.35R 이 폭의 95% (좌우 잘림 없음 — 알파 bbox 로 검사)
        W, Hh = 1344, 840
        sc = scene(W, Hh, samples=224)
        camera_ortho(2 * 2.35 / 0.95)
        # 키라이트를 더 옆(왼쪽)에서 — 행성 그림자가 오른쪽 뒤 고리 위에 보이게 한다(앞에서 비추면 행성 뒤에 숨는다)
        sun((-0.85, -0.30, 0.45), 6.2, color=(1.0, 0.96, 0.90), angle=1.0)
        sun((0.6, 0.8, 0.2), 1.6, color=(0.52, 0.68, 1.0))
        o = sphere(1.0, tilt=SAT_OPEN, face_lon=0.0, oblate=0.902)
        planet_mat(o, "tex_sz_saturn.png", None, rough=0.93, limb=(0.80, 0.74, 0.62), limb_amt=0.15, name="saturn")
        ring = H["annulus"](1.11, 2.35, 512, "saturn_ring")
        ring.rotation_mode = 'ZXY'
        ring.rotation_euler = (math.radians(SAT_OPEN), 0, 0)
        ring.data.materials.append(ring_mat("tex_sz_rings.png", "tex_sz_rings_a.png", "rings"))
        render("saturn")

    def r_uranus():
        sc = scene(896, 896, samples=192)
        camera_ortho(2 * 2.02 / 0.95)
        H["add_lights"](key_energy=6.0, rim_energy=3.0)
        # 98° 기울기 — 자전축이 화면 오른쪽을 향하고 카메라 쪽으로 20° 열림 → 세로 고리
        rot = dict(tilt=-20.0, face_lon=0.0, roll=90.0)
        o = sphere(1.0, oblate=0.977, **rot)
        planet_mat(o, "tex_sz_uranus.png", None, rough=0.95, limb=(0.70, 0.92, 0.95), limb_amt=0.25, name="uranus")
        ring = H["annulus"](1.60, 2.02, 512, "uranus_ring")
        ring.rotation_mode = 'ZXY'
        ring.rotation_euler = o.rotation_euler
        ring.data.materials.append(ring_mat("tex_sz_urings.png", "tex_sz_urings_a.png", "urings", translucent=0.1))
        render("uranus")

    JOBS = {"earth_limb": r_earth_limb, "earth_clouds": r_earth_clouds, "earth_small": r_earth_small,
            "moon": r_moon, "mars": r_mars, "phobos": r_phobos, "jupiter": r_jupiter, "io": r_io,
            "saturn": r_saturn, "titan": r_titan, "uranus": r_uranus, "neptune": r_neptune,
            "pluto": r_pluto, "charon": r_charon, "proxb": r_proxb}

    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = argv or list(JOBS)
    for n in names:
        print("==", n, flush=True)
        JOBS[n]()
    print("SPACEZ PLANETS DONE ->", REN_DIR)


# ══════════════════════════════ 일반 파이썬 쪽 (굽기) ══════════════════════════════
def _np():
    import numpy as np
    from PIL import Image, ImageFilter, ImageDraw
    return np, Image, ImageFilter, ImageDraw


def load_rgba(path):
    """렌더 PNG(8bit RGBA, Blender 는 스트레이트 알파로 저장) → float32 [0,1]."""
    np, Image, _, _ = _np()
    return np.asarray(Image.open(path).convert("RGBA"), dtype=np.float32) / 255.0


def read_render(name):
    return load_rgba(os.path.join(REN_DIR, name + ".png"))


def resize_premul(a, w, h):
    """프리멀티플라이 상태로 축소 → 가장자리 검은 테두리(프린지) 없음."""
    np, Image, _, _ = _np()
    pm = a.copy()
    pm[..., :3] *= pm[..., 3:4]
    chans = []
    for c in range(4):
        im = Image.fromarray(pm[..., c].astype(np.float32), "F").resize((w, h), Image.LANCZOS)
        chans.append(np.asarray(im, np.float32))
    out = np.clip(np.dstack(chans), 0, 1)
    al = out[..., 3:4]
    rgb = np.where(al > 1e-4, out[..., :3] / np.maximum(al, 1e-4), 0)
    return np.dstack([np.clip(rgb, 0, 1), al[..., 0]])


def _blur_rgb(rgb, sigma):
    """색 채널만 가우시안 블러(8bit 경유 — 음영용이라 충분)."""
    np, Image, ImageFilter, _ = _np()
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma))
    return np.asarray(im, np.float32) / 255.0


def cap_luma(a, knee=0.56, top=0.70):
    """최대 휘도 0.70 소프트 캡 (ART-13 가독성 가드). 색상·채도는 유지, 밝기만 누른다."""
    np = _np()[0]
    rgb = a[..., :3]
    y = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    over = y > knee
    yn = y.copy()
    yn[over] = knee + (top - knee) * (1 - np.exp(-(y[over] - knee) / (top - knee)))
    s = np.where(y > 1e-5, yn / np.maximum(y, 1e-5), 1.0)
    out = a.copy()
    out[..., :3] = np.clip(rgb * s[..., None], 0, 1)
    return out


def clean_alpha(a, floor=2.5 / 255):
    out = a.copy()
    out[..., 3][out[..., 3] < floor] = 0
    return out


def to_img(a):
    np, Image, _, _ = _np()
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")


def save_webp(a, path, kb, q0=80, qmin=50, qmax=90, aq=90):
    """품질 80 에서 시작. 예산(KB)을 넘으면 4씩 내리고, 예산의 60% 미만이면 예산 안에서 qmax 까지 올린다
    (행성은 투명 영역이 넓어 q80 이 예산보다 한참 작은 경우가 많다 — 남는 예산은 화질로 쓴다)."""
    im = to_img(a)
    lim = kb * 1024 * 1.03

    def enc(q):
        im.save(path, "WEBP", quality=q, method=6, alpha_quality=aq)
        return os.path.getsize(path)
    q = q0
    sz = enc(q)
    if sz <= lim:
        best = (q, sz)
        while sz < kb * 1024 * 0.6 and q < qmax:
            q = min(qmax, q + 4)
            sz = enc(q)
            if sz > lim:
                break
            best = (q, sz)
        if best[0] != q:
            enc(best[0])
        return best
    while sz > lim and q > qmin:
        q -= 4
        sz = enc(q)
    return q, sz


def alpha_bbox(a, thr=0.02):
    np = _np()[0]
    ys, xs = np.where(a[..., 3] > thr)
    if len(ys) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def disk_fit(a):
    """불투명 원반의 중심·반지름(픽셀) 실측 — 알파 0.5 이상 면적 → 등가 원 반지름."""
    np = _np()[0]
    m = a[..., 3] > 0.5
    ys, xs = np.nonzero(m)
    if len(ys) == 0:
        return None
    cx, cy = float(xs.mean()), float(ys.mean())
    r = math.sqrt(m.sum() / math.pi)
    return cx, cy, r


# ─── 엽서 썸네일 (pc_00~pc_12) ───
def _glow(np, size, cx, cy, r, color, power=2.0, amp=1.0):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    g = np.clip(1 - d, 0, 1) ** power * amp
    return np.dstack([np.full_like(g, color[0]), np.full_like(g, color[1]), np.full_like(g, color[2]), g])


def over(dst, src, x, y):
    """src(RGBA float, 스트레이트) 를 dst 위 (x,y) 에 알파 합성."""
    np = _np()[0]
    h, w = src.shape[:2]
    H_, W_ = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W_, x + w), min(H_, y + h)
    if x1 <= x0 or y1 <= y0:
        return dst
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    d = dst[y0:y1, x0:x1]
    sa = s[..., 3:4]; da = d[..., 3:4]
    oa = sa + da * (1 - sa)
    oc = (s[..., :3] * sa + d[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-5)
    dst[y0:y1, x0:x1, :3] = oc
    dst[y0:y1, x0:x1, 3:4] = oa
    return dst


def add_light(dst, g):
    """발광(가산) — 알파는 max, 색은 가중 평균으로 밝힌다."""
    np = _np()[0]
    ga = g[..., 3:4]
    oa = np.maximum(dst[..., 3:4], ga)
    col = dst[..., :3] * dst[..., 3:4] + g[..., :3] * ga
    dst[..., :3] = np.clip(col / np.maximum(oa, 1e-5), 0, 1)
    dst[..., 3:4] = np.clip(oa, 0, 1)
    return dst


def fit(a, size):
    """알파 bbox 로 잘라 긴 변을 size 로."""
    bb = alpha_bbox(a)
    x0, y0, x1, y1 = bb
    c = a[y0:y1 + 1, x0:x1 + 1]
    h, w = c.shape[:2]
    s = size / max(h, w)
    return resize_premul(c, max(1, round(w * s)), max(1, round(h * s)))


def build_postcards(finals, out_dir, report):
    np, Image, _, _ = _np()
    S = 96

    def blank():
        return np.zeros((S, S, 4), np.float32)

    def place(dst, a, size, cx, cy):
        f = fit(a, size)
        return over(dst, f, int(round(cx - f.shape[1] / 2)), int(round(cy - f.shape[0] / 2)))

    R = lambda n: read_render(n)
    cards = {}
    c = blank(); place(c, R("earth_small"), 86, 48, 48); cards["pc_00"] = c
    c = blank(); place(c, R("moon"), 78, 42, 54); place(c, R("earth_small"), 30, 78, 16); cards["pc_01"] = c
    c = blank(); place(c, R("mars"), 80, 44, 52); place(c, R("phobos"), 18, 84, 14); cards["pc_02"] = c
    c = blank()
    met = [load_rgba(os.path.join(ROOT, "scripts", "og-assets", "spacez", "meteor_%s.png" % k)) for k in "abc"]
    rs = np.random.default_rng(3)
    for _ in range(26):
        place(c, met[rs.integers(0, 3)], int(rs.uniform(4, 9)), rs.uniform(4, 92), rs.uniform(4, 92))
    place(c, met[0], 46, 40, 52); place(c, met[2], 30, 74, 26); place(c, met[1], 22, 22, 20)
    cards["pc_03"] = c
    c = blank(); place(c, R("jupiter"), 84, 46, 50); place(c, R("io"), 13, 88, 14); cards["pc_04"] = c
    c = blank(); place(c, R("saturn"), 94, 48, 48); cards["pc_05"] = c
    c = blank(); place(c, R("uranus"), 90, 48, 48); cards["pc_06"] = c
    c = blank(); place(c, R("neptune"), 84, 48, 48); cards["pc_07"] = c
    c = blank(); place(c, R("pluto"), 68, 40, 54); place(c, R("charon"), 32, 78, 20); cards["pc_08"] = c

    # 09 태양권 경계 — 태양풍 거품의 가장자리(매끈한 빛의 호) + 안쪽 옅은 채움 + 뒤에 별이 된 태양
    c = blank()
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    d = np.sqrt((xx - 48) ** 2 + (yy - 118) ** 2)
    band = np.exp(-((d - 78) / 5.5) ** 2) + 0.18 * np.clip((78 - d) / 78, 0, 1)
    band *= np.clip((yy + 4) / 60, 0, 1)
    t = np.clip((xx - 8) / 80, 0, 1)
    arc = np.dstack([0.45 + 0.30 * t, 0.70 - 0.15 * t, 1.0 + 0 * t, np.clip(band * 0.8, 0, 1)])
    c = add_light(c, arc)
    c = add_light(c, _glow(np, S, 48, 70, 14, (1.0, 0.92, 0.70), 2.4, 0.9))
    c = add_light(c, _glow(np, S, 48, 70, 3.5, (1.0, 0.98, 0.92), 1.0, 1.0))
    for ang in (0, 90):
        L = np.exp(-((yy - 70) / 0.7) ** 2) * np.exp(-np.abs(xx - 48) / 10) if ang == 0 else             np.exp(-((xx - 48) / 0.7) ** 2) * np.exp(-np.abs(yy - 70) / 10)
        c = add_light(c, np.dstack([np.ones_like(L), np.ones_like(L) * 0.95, np.ones_like(L) * 0.85, np.clip(L * 0.8, 0, 1)]))
    cards["pc_09"] = c

    # 10 오르트 구름 — 얼음 혜성핵(푸른빛으로 물들인 운석) + 가는 꼬리 + 먼 태양 점
    c = blank()
    tail = np.exp(-(((yy - xx * 0.55 - 18) / (1.5 + (96 - xx) * 0.06)) ** 2)) * np.clip((70 - xx) / 60, 0, 1)
    c = add_light(c, np.dstack([0.75 + 0 * tail, 0.88 + 0 * tail, 1.0 + 0 * tail, np.clip(tail * 0.6, 0, 1)]))
    ice = met[1].copy()
    ice[..., :3] = np.clip(ice[..., :3] * np.array([1.2, 1.55, 2.1], np.float32) + 0.06, 0, 1)
    place(c, ice, 40, 64, 56)
    for _ in range(14):
        x, y = rs.uniform(4, 92), rs.uniform(4, 92)
        c = add_light(c, _glow(np, S, x, y, rs.uniform(1.2, 2.4), (0.8, 0.9, 1.0), 1.5, 0.7))
    c = add_light(c, _glow(np, S, 12, 86, 6, (1.0, 0.92, 0.7), 2.0, 0.9))
    cards["pc_10"] = c

    # 11 프록시마 — 붉은 왜성 + 행성 b 초승달
    c = blank()
    c = add_light(c, _glow(np, S, 30, 30, 34, (1.0, 0.36, 0.14), 2.2, 0.8))
    dsk = np.sqrt((xx - 30) ** 2 + (yy - 30) ** 2) / 17
    star = np.clip(1 - dsk, 0, 1)
    limb = np.clip(1 - dsk ** 2, 0, 1) ** 0.4
    c = over(c, np.dstack([0.98 * limb + 0.02, 0.36 * limb + 0.1 * limb ** 3, 0.14 * limb,
                           np.clip((1 - dsk) * 18, 0, 1)]), 0, 0)
    place(c, R("proxb"), 44, 68, 66)
    cards["pc_11"] = c

    # 12 시리우스 — 청백 별 + 회절 스파이크 8방향 + 동반성 B
    c = blank()
    c = add_light(c, _glow(np, S, 48, 48, 30, (0.70, 0.82, 1.0), 2.6, 0.9))
    c = add_light(c, _glow(np, S, 48, 48, 9, (0.95, 0.98, 1.0), 1.2, 1.0))
    for k in range(4):
        t = math.radians(k * 45)
        ux, uy = math.cos(t), math.sin(t)
        along = (xx - 48) * ux + (yy - 48) * uy
        perp = -(xx - 48) * uy + (yy - 48) * ux
        L = np.exp(-(perp / (0.7 if k % 2 == 0 else 0.55)) ** 2) * np.exp(-np.abs(along) / (26 if k % 2 == 0 else 14))
        c = add_light(c, np.dstack([0.85 + 0 * L, 0.92 + 0 * L, 1.0 + 0 * L, np.clip(L, 0, 1)]))
    c = add_light(c, _glow(np, S, 70, 64, 3.2, (1.0, 1.0, 1.0), 1.4, 1.0))
    cards["pc_12"] = c

    out = {}
    for k, a in cards.items():
        a = clean_alpha(cap_luma(a, 0.62, 0.80))
        p = os.path.join(out_dir, k + ".webp")
        q, sz = save_webp(a, p, 5)
        out[k] = dict(q=q, bytes=sz, arr=a)
        report.append(dict(path="public/assets/spacez/z/%s.webp" % k, px=[S, S], kb=round(sz / 1024, 1),
                           quality=q, anchor="center", draw="96px 카드 썸네일(CSS 3열)", notes=POSTCARD_NOTES[k]))
    return out


POSTCARD_NOTES = {
    "pc_00": "존0 지구 — 구름·대기 포함 원반", "pc_01": "존1 달 + 지구돋이", "pc_02": "존2 화성 + 포보스",
    "pc_03": "존3 소행성대 — 운석 스프라이트 군집", "pc_04": "존4 목성(대적점) + 이오", "pc_05": "존5 토성 고리 22°",
    "pc_06": "존6 천왕성 세로 고리", "pc_07": "존7 해왕성 대암반", "pc_08": "존8 명왕성 하트 + 카론",
    "pc_09": "존9 태양권 경계 — 거품 벽 호 + 별이 된 태양", "pc_10": "존10 오르트 구름 — 얼음 혜성핵",
    "pc_11": "존11 프록시마 + 행성 b 초승달", "pc_12": "존12 시리우스 A 회절 스파이크 + B"}


# ─── 운석 위험 림 (ART-13 ②) ───
# 위험 색(달군 황색) — 존 무관 동일. 밝기가 중요하다: 어두운~중간 배경(휘도 ≤0.11)은 이 림이,
# 밝은 배경(≥0.10)은 바깥 검은 윤곽이 3:1 을 맡아 어떤 배경에서도 둘 중 하나가 실루엣을 지킨다.
# (1차: 진한 주황 #FF7329 1.5px — 게임 크기 30px 로 줄면 0.7px 로 뭉개져 중간 톤 행성 위 대비 1.7:1)
RIM_COLOR = (1.0, 0.86, 0.48)     # 상대휘도 ≈0.74


def _maxfilter(np, a, r):
    out = a.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy > r * r + r:
                continue
            out = np.maximum(out, np.roll(np.roll(a, dy, 0), dx, 1))
    return out


def build_meteor_rims(out_dir, report, r_rim=4, r_out=9, out_alpha=1.0):
    """기존 운석 렌더(512) → 128 + 바깥 4px 위험색 림 + 그 밖 5px 검은 윤곽 (게임 30 CSS px·DPR2 에서 각각 ≈1.9px·2.3px).
    균일 배경 휘도 0~0.5 전 구간에서 최악 대비 3.19:1 (DPR2) / 3.4:1 (DPR3) — 스윕으로 정한 값.
    밝은 행성(목성 띠·토성) 위에서는 어두운 윤곽이, 어두운 우주에서는 주황 림이 실루엣을 지킨다.
    그리기 호출 0 추가(스프라이트에 구움). 회전해도 같도록 광원 무관 균일 링."""
    np, Image, _, _ = _np()
    res = {}
    for k in "abc":
        a = load_rgba(os.path.join(ROOT, "scripts", "og-assets", "spacez", "meteor_%s.png" % k))
        a = resize_premul(a, 128, 128)
        A = a[..., 3]
        A1 = _maxfilter(np, A, r_rim)        # 림 바깥 경계
        A2 = _maxfilter(np, A, r_out)        # 검은 윤곽 바깥 경계
        rim = np.clip(A1 - A * 0.85, 0, 1)
        dark = np.clip(A2 - A1, 0, 1)
        base = np.zeros_like(a)
        base = over(base, np.dstack([np.full_like(A, 0.02), np.full_like(A, 0.012), np.full_like(A, 0.008), dark * out_alpha]), 0, 0)
        base = over(base, np.dstack([np.full_like(A, RIM_COLOR[0]), np.full_like(A, RIM_COLOR[1]),
                                     np.full_like(A, RIM_COLOR[2]), rim]), 0, 0)
        base = over(base, a, 0, 0)
        # 몸통 안쪽 가장자리 1px 도 살짝 달군다(작게 그려질 때 림이 몸통과 분리돼 보이지 않게)
        inner = np.clip(A - _minfilter(np, A, 1), 0, 1) * 0.35
        base = over(base, np.dstack([np.full_like(A, RIM_COLOR[0]), np.full_like(A, 0.62), np.full_like(A, 0.35), inner]), 0, 0)
        bb = alpha_bbox(base)
        name = "meteor_%s_rim" % k
        p = os.path.join(out_dir, name + ".webp")
        q, sz = save_webp(clean_alpha(base), p, 6, q0=85)
        res[name] = dict(img=base, body=A > 0.5, rim=(rim > 0.5) & (A < 0.5), dark=(dark > 0.5) & (rim < 0.3))
        report.append(dict(path="public/assets/spacez/z/%s.webp" % name, px=[128, 128], kb=round(sz / 1024, 1),
                           quality=q, anchor="center(64,64) — 기존 meteor_%s.webp 와 같은 프레임·같은 R" % k,
                           draw="기존과 동일: drawImage(im,-R,-R,2R,2R), R=15 (30 CSS px)",
                           alpha_bbox=list(bb),
                           notes="기존 meteor_%s 에 위험색(#FFDB7A) 4px 림 + 바깥 5px 검은 윤곽을 구움(128px 기준). "
                                 "참조만 바꾸면 됨(추가 draw call 0). 원본 meteor_%s.webp 는 덮어쓰지 않음" % (k, k)))
    return res


def _minfilter(np, a, r):
    return 1 - _maxfilter(np, 1 - a, r)


# ─── 메인 굽기 ───
def post(shots=None, manifest=None):
    np, Image, ImageFilter, ImageDraw = _np()
    os.makedirs(PUB_DIR, exist_ok=True)
    report = []
    finals = {}
    for name, spec in ASSETS.items():
        a = read_render(spec["src"])
        a = resize_premul(a, spec["w"], spec["h"]) if (a.shape[1], a.shape[0]) != (spec["w"], spec["h"]) else a
        a = clean_alpha(cap_luma(a))
        if spec.get("rgb_blur"):
            a = a.copy()
            a[..., :3] = _blur_rgb(a[..., :3], spec["rgb_blur"])
        finals[name] = a
        p = os.path.join(PUB_DIR, name + ".webp")
        aq = spec.get("aq", 90)
        q, sz = save_webp(a, p, spec["kb"], aq=aq)
        entry = dict(path="public/assets/spacez/z/%s.webp" % name, px=[spec["w"], spec["h"]],
                     kb=round(sz / 1024, 1), budget_kb=spec["kb"], quality=q)
        bb = alpha_bbox(a)
        entry["alpha_bbox"] = list(bb) if bb else None
        entry.update(GEOM.get(name, {}))
        if name not in ("z00_earth_limb", "z00_clouds", "zone_saturn", "zone_uranus"):
            cx, cy, r = disk_fit(a)
            entry["center"] = [round(cx, 1), round(cy, 1)]
            entry["disk_r_px"] = round(r, 1)
            entry["disk_frac"] = round(2 * r / spec["w"], 3)
        report.append(entry)
        if spec.get("lo"):
            lo = resize_premul(a, spec["w"] // 2, spec["h"] // 2)
            p2 = os.path.join(PUB_DIR, name + "_lo.webp")
            q2, sz2 = save_webp(clean_alpha(lo), p2, max(2, spec["kb"] * 0.3), aq=aq)
            report.append(dict(path="public/assets/spacez/z/%s_lo.webp" % name, px=[spec["w"] // 2, spec["h"] // 2],
                               kb=round(sz2 / 1024, 1), quality=q2,
                               notes="%s 의 절반 해상도 (tier2 또는 deviceMemory<=3). 좌표·비율 동일 — 모든 px 값 x0.5" % name))
        print("  %-16s %4dx%-4d q%-2d %6.1fKB (예산 %d)" % (name, spec["w"], spec["h"], q, sz / 1024, spec["kb"]))
    pcs = build_postcards(finals, PUB_DIR, report)
    rims = build_meteor_rims(PUB_DIR, report)
    tot = sum(os.path.getsize(os.path.join(PUB_DIR, f)) for f in os.listdir(PUB_DIR) if f.endswith(".webp"))
    boot = sum(os.path.getsize(os.path.join(PUB_DIR, n + ".webp")) for n in
               ("z00_earth_limb", "z00_clouds", "zone_moon", "earth_small", "zone_mars", "phobos"))
    summary = dict(total_kb=round(tot / 1024, 1), boot_zone0_2_kb=round(boot / 1024, 1))
    print("  합계 %.1fKB, 부팅(0~2존) %.1fKB" % (tot / 1024, boot / 1024))
    man = dict(generated_by="scripts/blender/spacez_planets.py post", summary=summary,
               zone_art=ZONE_ART, conventions=CONVENTIONS, assets=report)
    manifest = manifest or os.path.join(REN_DIR, "manifest.json")
    with open(manifest, "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)
    print("  manifest ->", manifest)
    if shots:
        contact_sheets(finals, pcs, rims, shots)


# 런타임 통합용 기하 정보 (P6 로더·szFlyby 가 쓴다). 좌표는 최종 해상도 px.
GEOM = {
    "z00_earth_limb": dict(anchor="bottom-center: 화면 폭 = 스프라이트 폭(1080 → CW), 아래 가장자리를 화면 아래에 맞춤",
                           limb_apex_px=[540, 150], limb_radius_px=1350, limb_center_px=[540, 1500],
                           draw="drawImage(im, 0, CH - CW*560/1080, CW, CW*560/1080). 존 진행에 따라 아래로 내려가며 빠짐(곡률 유지)",
                           notes="대기 산란 띠 약 30px 가 림 위로(알파 포함). 왼쪽 밤쪽 도시불빛(동아시아), 오른쪽 낮·일출 산란. 구름 없음 — z00_clouds 를 위에 겹칠 것"),
    "z00_clouds": dict(anchor="z00_earth_limb 와 같은 프레임·같은 위치에 겹쳐 그림",
                       draw="같은 사각형에 0.3px/s 오른쪽으로 흘림(22초 = 6.6px). 흘린 만큼 왼쪽 끝이 비는 건 림 호 밖이라 보이지 않음",
                       notes="구름층만(지구 몸통 holdout). 림 근처는 대기에 묻히게 옅어짐. 밤쪽 구름은 어둡다(불빛을 가림 — 사실적)"),
    "zone_moon": dict(anchor="center", draw="szFlyby 원반 반지름 r → 그리기 폭 = 2r / disk_frac",
                      notes="실제 앞면: 비의 바다·고요의 바다·위난의 바다·폭풍의 대양, 티코·코페르니쿠스 광조. 왼쪽 위 광원"),
    "earth_small": dict(anchor="center", draw="존1 zoneT 0.55~0.8 지구돋이: 달 림 위로 40px 떠오름. 권장 지름 36~56 CSS px",
                        notes="아프리카·유럽 쪽 원반, 구름·대기 포함, 달과 같은 광원 방향"),
    "zone_mars": dict(anchor="center", notes="v2: 매리너 협곡(가운데 가로), 타르시스 3산·올림푸스(왼쪽), 북극관 78°, 기울기 25°"),
    "phobos": dict(anchor="center", draw="권장 지름 18~28 CSS px, 화성 옆 궤도", notes="감자형, 스티크니 크레이터가 왼쪽 가장자리"),
    "zone_jupiter": dict(anchor="center", notes="대적점 정면(남반구 -22°), 흰 타원 BA, 진주 목걸이, 편평도 0.935"),
    "io": dict(anchor="center", draw="권장 지름 12~20 CSS px", notes="황색 황, 검은 화산점, 펠레 붉은 고리"),
    "zone_saturn": dict(anchor="center = 행성 중심(프레임 중심 448,280)", planet_r_px=181.1,
                        ring_outer_px=425.6, ring_open_deg=22.0,
                        draw="행성 반지름 r 기준 그리기 폭 = r * 896 / planet_r_px",
                        notes="고리 22° 열림, 카시니 간극, 엥케 간극, 고리 위 행성 그림자(오른쪽 뒤), 행성 위 고리 그림자. 고리는 가로 — 고리면 통과 메커닉(가로 얼음띠)과 방향 일치"),
    "titan": dict(anchor="center", draw="권장 지름 14~22 CSS px", notes="주황 연무, 가장자리 밝음"),
    "zone_uranus": dict(anchor="center = 행성 중심(224,224)", planet_r_px=105.3, ring_outer_px=212.8,
                        ring_open_deg=20.0, draw="행성 반지름 r 기준 그리기 폭 = r * 448 / 105.3",
                        notes="자전축이 오른쪽(98°) → 고리가 세로 타원. ε 고리가 가장 바깥·가장 밝음. 극 두건이 오른쪽"),
    "zone_neptune": dict(anchor="center", notes="대암반(남위 20°) 정면 왼쪽 + 흰 동반 구름, 스쿠터, D2, 흰 권운 줄"),
    "zone_pluto": dict(anchor="center", notes="톰보 하트(서엽 스푸트니크 평원이 가장 밝음) 정면, 왼쪽 아래 크툴루 암부. 4~5px 라벨 없음"),
    "charon": dict(anchor="center", draw="권장: 명왕성 지름의 0.5배(실제 비 0.51)", notes="북극 모르도르 적갈 모자, 적도 협곡대"),
}

ZONE_ART = {   # 매니페스트 제안(런타임 SZ_ZONE_ART 초안). 0~2 존 = 부팅 로드
    "0": ["z00_earth_limb", "z00_clouds"], "1": ["zone_moon", "earth_small"], "2": ["zone_mars", "phobos"],
    "4": ["zone_jupiter", "io"], "5": ["zone_saturn", "titan"], "6": ["zone_uranus"], "7": ["zone_neptune"],
    "8": ["zone_pluto", "charon"],
    "boot_always": ["meteor_a_rim", "meteor_b_rim", "meteor_c_rim"],
    "postcards_lazy": ["pc_%02d" % i for i in range(13)],
}

CONVENTIONS = {
    "lighting": "전 천체 공통 왼쪽 위 앞 키라이트 + 오른쪽 뒤 청색 림(행성 키우기와 같은 광원). 지구 림만 오른쪽 뒤 태양(일출)",
    "luma_cap": "모든 히어로 스프라이트 최대 휘도(Rec.709 luma, 인코딩 값) <= 0.70 소프트 캡",
    "alpha": "스트레이트 알파 WebP, 프리멀티플라이 리사이즈로 가장자리 프린지 없음. 알파 < 2.5/255 는 0",
    "lo": "_lo = 정확히 절반 해상도, 같은 프레임. 모든 px 좌표 x0.5",
    "path": "/assets/spacez/z/<이름>.webp + 기존 BV(?v=빌드스탬프)",
}


def contact_sheets(finals, pcs, rims, shots):
    """검수용: ① 우주 배경 위 전체 ② 회색·체커 위(알파 가장자리) ③ 게임 프레임 모의 + 운석 대비."""
    np, Image, _, ImageDraw = _np()
    os.makedirs(shots, exist_ok=True)

    def bg_space(w, h, seed=1):
        rs = np.random.default_rng(seed)
        yy = np.linspace(0, 1, h)[:, None]
        base = np.dstack([0.02 + 0.02 * yy + 0 * np.zeros((h, w)), 0.025 + 0.03 * yy + 0 * np.zeros((h, w)),
                          0.06 + 0.06 * yy + 0 * np.zeros((h, w))])
        for _ in range(w * h // 900):
            x, y = rs.integers(0, w), rs.integers(0, h)
            base[y, x] = rs.uniform(0.4, 1.0)
        return np.dstack([base, np.ones((h, w))]).astype(np.float32)

    def checker(w, h):
        yy, xx = np.mgrid[0:h, 0:w]
        c = (((yy // 12) + (xx // 12)) % 2) * 0.18 + 0.45
        return np.dstack([c, c, c, np.ones((h, w))]).astype(np.float32)

    def sheet(bgfn, fname):
        order = list(finals)
        cols = 4
        cell = 300
        rows = (len(order) + cols - 1) // cols
        W, Hh = cols * cell, rows * cell + 140
        s = bgfn(W, Hh)
        for i, n in enumerate(order):
            a = finals[n]
            sc = min((cell - 20) / a.shape[1], (cell - 40) / a.shape[0])
            r = resize_premul(a, max(1, int(a.shape[1] * sc)), max(1, int(a.shape[0] * sc)))
            x = (i % cols) * cell + (cell - r.shape[1]) // 2
            y = (i // cols) * cell + 28 + (cell - 40 - r.shape[0]) // 2
            over(s, r, x, y)
        x = 10
        for k, v in pcs.items():
            over(s, v["arr"], x, rows * cell + 20)
            x += 100
        im = to_img(s).convert("RGB")
        d = ImageDraw.Draw(im)
        for i, n in enumerate(order):
            d.text(((i % cols) * cell + 8, (i // cols) * cell + 6), n, fill=(255, 220, 120))
        im.save(os.path.join(shots, fname))

    sheet(bg_space, "contact_space.png")
    sheet(checker, "contact_checker.png")

    # 큰 원본 크기 확인용 (1:1)
    for n in ("z00_earth_limb", "zone_saturn", "zone_jupiter"):
        a = finals[n]
        s = bg_space(a.shape[1], a.shape[0])
        over(s, a, 0, 0)
        if n == "z00_earth_limb":
            over(s, finals["z00_clouds"], 0, 0)
        to_img(s).convert("RGB").save(os.path.join(shots, "full_%s.png" % n))

    # 게임 프레임 모의 (412x915 CSS, DPR 2) + 운석 대비 측정
    report = game_mock(finals, rims, shots, bg_space)
    with open(os.path.join(shots, "contrast.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("  contact sheets ->", shots)


def _rel_lum(np, rgb):
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return c @ np.array([0.2126, 0.7152, 0.0722], np.float32)


def game_mock(finals, rims, shots, bg_space):
    """존별 히어로를 flyby 최대 크기(s≈1.0~1.4)로 배치한 412x915 프레임에 운석 50개를 찍고
    운석(몸통+림)과 주변 배경의 국소 휘도 대비를 잰다. 게임의 dim 오버레이(0.2)도 반영."""
    np, Image, _, ImageDraw = _np()
    DPR = 2
    W, Hh = 412 * DPR, 915 * DPR
    rs = np.random.default_rng(11)
    met = list(rims.values())
    R = 15 * DPR

    def _mask(m):
        im = Image.fromarray((m * 255).astype(np.uint8)).resize((2 * R, 2 * R), Image.BILINEAR)
        return np.asarray(im) > 127
    metS = [(resize_premul(m["img"], 2 * R, 2 * R), _mask(m["body"]), _mask(m["rim"]), _mask(m["dark"])) for m in met]
    scenes = {
        "z0_earth": [("z00_earth_limb", "limb"), ("z00_clouds", "limb")],
        "z1_moon": [("zone_moon", (0.30, 0.42, 0.75)), ("earth_small", (0.42, 0.14, 0.11))],
        "z2_mars": [("zone_mars", (0.72, 0.45, 0.80)), ("phobos", (0.28, 0.22, 0.05))],
        "z4_jupiter": [("zone_jupiter", (0.28, 0.48, 1.05)), ("io", (0.80, 0.18, 0.04))],
        "z5_saturn": [("zone_saturn", (0.70, 0.45, 1.30))],
        "z6_uranus": [("zone_uranus", (0.30, 0.40, 0.85))],
        "z7_neptune": [("zone_neptune", (0.72, 0.42, 0.85))],
        "z8_pluto": [("zone_pluto", (0.30, 0.45, 0.70)), ("charon", (0.70, 0.22, 0.30))],
    }
    out = {}
    tiles = []
    for zn, items in scenes.items():
        s = bg_space(W, Hh, seed=sum(map(ord, zn)))
        for n, pos in items:
            a = finals[n]
            if pos == "limb":
                h = int(W * a.shape[0] / a.shape[1])
                r = resize_premul(a, W, h)
                over(s, r, 0, Hh - h)
            else:
                cx, cy, dw = pos
                w = int(W * dw)
                h = int(w * a.shape[0] / a.shape[1])
                r = resize_premul(a, w, h)
                r[..., 3] *= 0.85 if dw > 1.0 else 1.0
                over(s, r, int(cx * W - w / 2), int(cy * Hh - h / 2))
        s[..., :3] *= 0.8          # dim 오버레이 0.2
        bgonly = s.copy()
        ratios = []
        # 운석이 '보이는가' = 몸통·위험 림·어두운 윤곽 가운데 하나라도 배경과 3:1 이상 벌어지는가.
        # 게임의 운석 뒤 글로우·꼬리는 빼고 잰다(보수적)
        cr = lambda a_, b_: (max(a_, b_) + 0.05) / (min(a_, b_) + 0.05)
        for i in range(50):
            m, mb, mr, md = metS[i % 3]
            x = int(rs.uniform(R, W - 3 * R)); y = int(rs.uniform(R, Hh - 3 * R))
            patch = bgonly[y - 6:y + 2 * R + 6, x - 6:x + 2 * R + 6]
            ring = np.ones(patch.shape[:2], bool); ring[6:-6, 6:-6] = False
            over(s, m, x, y)
            reg = s[y:y + 2 * R, x:x + 2 * R]
            L_bg = float(_rel_lum(np, patch[..., :3][ring]).mean())
            vals = [float(_rel_lum(np, reg[..., :3][k]).mean()) for k in (mb, mr, md) if k.any()]
            ratios.append(float(max(cr(v, L_bg) for v in vals)))
        out[zn] = dict(min=round(min(ratios), 2), p10=round(float(np.percentile(ratios, 10)), 2),
                       median=round(float(np.median(ratios)), 2))
        tiles.append(resize_premul(s, 412, 915))
    # 모의 프레임 이어 붙이기
    big = np.zeros((915, 412 * len(tiles), 4), np.float32)
    for i, t in enumerate(tiles):
        big[:, i * 412:(i + 1) * 412] = t
    im = to_img(big).convert("RGB")
    d = ImageDraw.Draw(im)
    for i, (zn, v) in enumerate(out.items()):
        d.text((i * 412 + 6, 6), "%s min %.1f" % (zn, v["min"]), fill=(255, 230, 120))
    im.save(os.path.join(shots, "game_mock_contrast.png"))
    return out


def run_blender(names):
    import subprocess
    cmd = [BLENDER, "-b", "-P", os.path.abspath(__file__), "--"] + list(names)
    print(" ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit("blender failed")


if not IN_BLENDER and __name__ == "__main__":
    args = sys.argv[1:]
    mode = args[0] if args else "all"
    rest = args[1:]
    shots = None
    manifest = None
    if "--shots" in rest:
        i = rest.index("--shots"); shots = rest[i + 1]; rest = rest[:i] + rest[i + 2:]
    if "--manifest" in rest:
        i = rest.index("--manifest"); manifest = rest[i + 1]; rest = rest[:i] + rest[i + 2:]
    sys.path.insert(0, HERE)
    if mode in ("tex", "all"):
        import planet_textures as pt
        for fn in pt.SZ_ALL:
            print("==", fn.__name__, flush=True)
            fn()
    if mode in ("render", "all"):
        run_blender(rest)
    if mode in ("post", "all"):
        post(shots=shots, manifest=manifest)
