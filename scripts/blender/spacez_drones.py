# -*- coding: utf-8 -*-
"""Space-Z 아이템 드론 2종 스프라이트 — Blender Cycles (2026-10-08).

운영자: "아이템 중 드론들 종류가 몇 개 있는데 그래픽이 너무 형편없어 — 더 고도화된 그래픽으로 리얼한 생김새로 렌더링해줘."
바뀌는 것(그림만, 규칙·판정 그대로):
  ① 윙맨(MINI, 아이템 '✈ +1') — 옛 캔버스 삼각형(스텔스기 흉내) → 무인 요격기(UCAV). 꼬리 없는 블렌디드 플라잉윙
     (스팬 × 시위 매개 곡면, 에어포일 두께 √c·(1−c) 라 앞전·뒷전이 칼날처럼 얇다) + 등 혹(센서 바이저·흡입구·안테나) +
     쌍발 슬롯 이온 노즐 + 앞전 크랭크 레이저 이미터(빨강 = 게임의 윙맨 레이저 색) + 검은 내열타일 앞전·노즈 캡 + 엘레본·편대등·항법등.
     (시안 단계에서 버린 것: 둥근 동체+델타익 = 50년대 제트기처럼 읽혔다 / 두꺼운 리프팅 바디 = 우주왕복선처럼 읽혔다)
  ② 호위 드론(AEGIS, 위성 임무 보상 🛸) — 옛 육각형 선 → 덕트 팬 4발 센티넬. 원반 동체 + 앞쪽 센서 블리스터(청록 렌즈) +
     쌍열 이미터(청록 = 호위 드론 레이저 색) + 4 덕트(로터 2프레임 교대 = 회전 착시).
  실존 기체·상표·국적 표지 없음(형상은 일반적인 요격 드론 문법만 — 특정 기체 실루엣 복제 금지).

스타일 = 플레이어 기체(starship_scene.py)와 같은 문법: Standard 뷰(AgX 금지 — 은색을 탁하게 누른다), 스테인리스 금속 +
  거의 검은 내열타일, 왼쪽 위 키 + 세로 띠 소프트박스(긴 스페큘러) + 오른쪽 청색 림, 월드 그라디언트는 반사에만.
  도장 2종: steel(솔로·방장) / gold(2인 모드 참가자) — 기체 LIVERY 와 같은 값.

좌표: 평면도(위에서 내려다봄). 월드 +Y = 화면 위 = 진행 방향(노즈), +X = 화면 오른쪽, 카메라는 +Z 에서 −Z 를 본다.
  뱅크 + (오른쪽으로 이동) = Y 축 +회전 → 오른쪽 날개가 아래로(비행기가 선회 방향으로 기운다).
프레임: 한 칸 = 윙맨 FRAME_U(12) / 호위 FRAME_A(7) 단위 정사각, 렌더 384px → 굽기 96px(4배 축소·샤픈).
  윙맨 노즈 y +5 · 노즐 끝 y −4.2 · 날개폭 9.6, 호위 드론 덕트 끝 지름 ≈ 6.2 단위. 게임 쪽 앵커(SZ_DRONE 표)는 이 단위로 적는다.
  금속이 평면도에서 하얗게 뜨지 않게: 월드 = 키 방향 하늘만 밝은 내적 그라디언트, 거칠기 0.11~0.24(반사가 기울기를 따라 갈린다).

실행:
  전체   : python scripts/blender/spacez_drones.py              (Blender 렌더 → 굽기)
  렌더만 : C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/spacez_drones.py -- all
  굽기만 : python scripts/blender/spacez_drones.py post         → public/assets/dodge/drones.webp
  시안   : SZD_SAMPLES=48 로 샘플 낮추기 / SZD_REN=<폴더> 로 중간 PNG 위치 바꾸기(기본 scripts/og-assets/spacez_drones, git 미추적)
아틀라스(96px 칸, 5열 × 3행):
  행 0 = 윙맨 steel 뱅크 −2…+2 / 행 1 = 윙맨 gold 뱅크 −2…+2 / 행 2 = 호위 steel 로터 a·b, gold a·b, (빈칸)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REN = os.environ.get("SZD_REN") or os.path.join(ROOT, "scripts", "og-assets", "spacez_drones")
PUB = os.path.join(ROOT, "public", "assets", "dodge")
SAMPLES = int(os.environ.get("SZD_SAMPLES", "128"))
FRAME_U = 12.0                    # 윙맨 칸 = 12 단위 정사각
FRAME_A = 7.0                     # 호위 드론 칸 = 7 단위(덕트 끝 지름 ≈ 6.2 가 칸의 88%)
RPX = 384
CELL = 96
BANKS = [-2, -1, 0, 1, 2]
BANK_DEG = 16.0
LIVERY = {
    'steel': dict(base=(0.64, 0.655, 0.68), rr=(0.11, 0.24)),
    'gold': dict(base=(1.0, 0.77, 0.34), rr=(0.10, 0.22), coat=0.55),
}
try:
    import bpy  # noqa
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False


# ══════════════════════════════ Blender ══════════════════════════════
def scene(ortho=FRAME_U):
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
    except Exception as e:
        print("GPU 실패 — CPU", e)
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = sc.render.resolution_y = RPX
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.filter_size = 1.0
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    # 월드 — 금속이 반사할 '세상'. 키 조명 방향(왼쪽 위 앞) 하늘이 가장 밝고, 반대쪽은 어둡다.
    # 평면도에서 판재는 거의 천정을 반사하므로, 천정을 한 톤 낮추고 기울기에 따라 밝기가 갈리게 해야 은색에 깊이가 생긴다
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    dot = nt.nodes.new("ShaderNodeVectorMath"); dot.operation = 'DOT_PRODUCT'
    d0 = (-0.42, 0.55, 0.72)
    n0 = math.sqrt(sum(c * c for c in d0))
    dot.inputs[1].default_value = tuple(c / n0 for c in d0)
    nt.links.new(tc.outputs["Generated"], dot.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(dot.outputs["Value"], ramp.inputs[0])
    el = ramp.color_ramp.elements
    el[0].position = 0.05; el[0].color = (0.012, 0.014, 0.022, 1)
    el[1].position = 0.97; el[1].color = (0.62, 0.68, 0.80, 1)
    m = el.new(0.55); m.color = (0.13, 0.15, 0.20, 1)
    m2 = el.new(0.82); m2.color = (0.30, 0.34, 0.42, 1)
    nt.links.new(ramp.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 0.85
    sc.world = w
    cd = bpy.data.cameras.new("cam")
    cd.type = 'ORTHO'
    cd.ortho_scale = ortho
    cd.clip_end = 200
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    cam.location = (0, 0, 60)
    cam.rotation_euler = (0, 0, 0)
    sc.camera = cam
    return sc


def area(name, loc, size, energy, color, sy=None, target=(0, 0, 0)):
    import bpy
    from mathutils import Vector
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.color = color
    ld.shape = 'RECTANGLE'
    ld.size = size
    ld.size_y = sy if sy is not None else size
    o = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')
    o.visible_camera = False
    return o


def lights():
    """기체와 같은 배치를 평면도로 옮긴 것: 키 = 왼쪽 위(화면) 높이, 세로 띠 2장 = 긴 스페큘러 줄,
    림 = 오른쪽 낮은 청색(어두운 우주에서 오른편 실루엣), 필 = 화면 아래쪽에서 약하게."""
    area("key", (-24, 22, 34), 14, 1.4e4, (1.0, 0.97, 0.92))
    area("stripL", (-16, 4, 18), 1.4, 3.0e3, (0.92, 0.96, 1.0), sy=34)
    area("stripR", (17, -2, 16), 1.2, 2.6e3, (0.84, 0.90, 1.0), sy=32)
    area("rim", (22, -10, 6), 10, 8.0e3, (0.42, 0.70, 1.0))
    area("fill", (0, -26, 14), 18, 1.1e3, (0.55, 0.62, 0.80))


def materials(livery):
    import bpy
    LV = LIVERY[livery]

    def principled(name):
        m = bpy.data.materials.new(name); m.use_nodes = True
        return m, m.node_tree, m.node_tree.nodes["Principled BSDF"]

    # 스테인리스(또는 광택 금) 외피 — 패널선(브릭 텍스처 모르타르 = 가는 홈) + 롤링 결 거칠기 + 노즐 쪽 그을음
    st, nt, b = principled("hull")
    b.inputs["Base Color"].default_value = (*LV['base'], 1)
    b.inputs["Metallic"].default_value = 1.0
    if LV.get('coat'):
        b.inputs["Coat Weight"].default_value = LV['coat']
        b.inputs["Coat Roughness"].default_value = 0.06
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 0.55
    br.inputs["Mortar Size"].default_value = 0.022
    br.inputs["Mortar Smooth"].default_value = 0.2
    br.inputs["Brick Width"].default_value = 1.6
    br.inputs["Row Height"].default_value = 0.9
    br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (1, 1, 1, 1)
    br.inputs["Mortar"].default_value = (0, 0, 0, 1)
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.4; nz.inputs["Detail"].default_value = 8.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs[3].default_value = LV['rr'][0]; rr.inputs[4].default_value = LV['rr'][1]
    nt.links.new(nz.outputs["Fac"], rr.inputs[0])
    nt.links.new(rr.outputs[0], b.inputs["Roughness"])
    bmp = nt.nodes.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.55; bmp.inputs["Distance"].default_value = 0.02
    bmp.invert = True                                     # Fac 1 = 모르타르 → 홈으로 판다
    nt.links.new(br.outputs["Fac"], bmp.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], b.inputs["Normal"])
    # 그을음 — 오브젝트 y 가 꼬리(−)로 갈수록 살짝 어둡게 · 패널선은 더 어둡게
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    soot = nt.nodes.new("ShaderNodeMapRange")
    soot.inputs[1].default_value = -5.0; soot.inputs[2].default_value = -1.5
    soot.inputs[3].default_value = 0.62; soot.inputs[4].default_value = 1.0
    nt.links.new(sep.outputs["Y"], soot.inputs[0])
    lines = nt.nodes.new("ShaderNodeMapRange")
    lines.inputs[3].default_value = 1.0; lines.inputs[4].default_value = 0.55
    nt.links.new(br.outputs["Fac"], lines.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
    nt.links.new(soot.outputs[0], mul.inputs[0]); nt.links.new(lines.outputs[0], mul.inputs[1])
    tint = nt.nodes.new("ShaderNodeMixRGB"); tint.blend_type = 'MULTIPLY'
    tint.inputs["Fac"].default_value = 1.0
    tint.inputs["Color1"].default_value = (*LV['base'], 1)
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    for k in range(3):
        nt.links.new(mul.outputs[0], comb.inputs[k])
    nt.links.new(comb.outputs[0], tint.inputs["Color2"])
    nt.links.new(tint.outputs[0], b.inputs["Base Color"])

    # 내열타일(거의 검정 세라믹) — 앞전·팔 윗면. 기체 타일과 같은 톤
    tl, nt, b = principled("tile")
    b.inputs["Base Color"].default_value = (0.012, 0.013, 0.016, 1)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.62
    b.inputs["Specular IOR Level"].default_value = 0.18
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 7.0
    vo.feature = 'DISTANCE_TO_EDGE'
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    bmp = nt.nodes.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.4; bmp.inputs["Distance"].default_value = 0.02
    nt.links.new(vo.outputs["Distance"], bmp.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], b.inputs["Normal"])

    def plain(name, col, rough, metal, emit=None, es=0.0, coat=0.0):
        m, nt, p = principled(name)
        p.inputs["Base Color"].default_value = (*col, 1)
        p.inputs["Roughness"].default_value = rough
        p.inputs["Metallic"].default_value = metal
        if coat:
            p.inputs["Coat Weight"].default_value = coat
            p.inputs["Coat Roughness"].default_value = 0.03
        if emit:
            p.inputs["Emission Color"].default_value = (*emit, 1)
            p.inputs["Emission Strength"].default_value = es
        return m
    gun = plain("gunmetal", (0.11, 0.115, 0.125), 0.36, 1.0)
    panel = plain("panel", (0.34, 0.35, 0.37), 0.30, 1.0)                          # 엘레본 — 한 톤 어두운 판
    slime = plain("slime", (0.02, 0.03, 0.03), 0.4, 0.0, emit=(0.45, 1.0, 0.80), es=0.45)   # 편대등(희미한 띠)
    glass = plain("glass", (0.010, 0.016, 0.026), 0.04, 0.35, coat=1.0)      # 센서 블리스터 — 짙은 유리
    noz = plain("nozzle", (0.20, 0.19, 0.19), 0.42, 1.0)
    nozin = plain("nozzle_in", (0.05, 0.05, 0.06), 0.5, 0.2, emit=(0.55, 0.80, 1.0), es=3.2)   # 이온 노즐 안쪽 — 청백
    eye = plain("eye", (0.0, 0.0, 0.0), 0.3, 0.0, emit=(0.0, 0.85, 1.0), es=4.0)            # 센서 렌즈 — 기체 청록 액센트
    red = plain("laser_red", (0.0, 0.0, 0.0), 0.3, 0.0, emit=(1.0, 0.16, 0.12), es=2.8)      # 윙맨 레이저 포구
    cyan = plain("laser_cyan", (0.0, 0.0, 0.0), 0.3, 0.0, emit=(0.35, 0.85, 1.0), es=2.6)    # 호위 드론 이미터
    navr = plain("nav_r", (0, 0, 0), 0.3, 0.0, emit=(1.0, 0.10, 0.08), es=6.0)
    navg = plain("nav_g", (0, 0, 0), 0.3, 0.0, emit=(0.15, 1.0, 0.35), es=6.0)
    # 로터 — 반투명 짙은 날(회전 흐림 대신 2프레임 교대)
    rot = bpy.data.materials.new("rotor"); rot.use_nodes = True
    nt = rot.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.05, 0.05, 0.06, 1)
    p.inputs["Roughness"].default_value = 0.45; p.inputs["Metallic"].default_value = 0.6
    p.inputs["Alpha"].default_value = 0.62
    try:
        rot.blend_method = 'BLEND'
    except Exception:
        pass
    return dict(hull=st, tile=tl, gun=gun, panel=panel, slime=slime, glass=glass, noz=noz, nozin=nozin, eye=eye, red=red, cyan=cyan,
                navr=navr, navg=navg, rotor=rot)


def mesh_obj(name, verts, faces, mats, mat_idx=None, smooth=True, parent=None, subsurf=0, bevel=0.0):
    import bpy
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.validate()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for m in mats:
        ob.data.materials.append(m)
    for i, p in enumerate(me.polygons):
        p.use_smooth = smooth
        if mat_idx is not None:
            p.material_index = mat_idx(i, p)
    if bevel > 0:
        bv = ob.modifiers.new("bev", 'BEVEL'); bv.width = bevel; bv.segments = 3; bv.limit_method = 'ANGLE'
    if subsurf:
        ss = ob.modifiers.new("ss", 'SUBSURF'); ss.levels = subsurf; ss.render_levels = subsurf
    if parent:
        ob.parent = parent
    return ob


def loft(name, sections, mats, parent=None, n=28, subsurf=1, mat_fn=None, ex=2.6):
    """단면 로프트 — sections = [(y, half_w, half_h_top, half_h_bot, z0)] 앞→뒤. 단면은 초타원(지수 ex).
    끝 단면 폭이 0 이면 한 점으로 모은다. ex 가 2 보다 작으면 옆선이 뾰족한 체인(chine)이 된다. mat_fn(y, ang) → 재질 인덱스."""
    verts, faces, rings = [], [], []
    for (y, hw, ht, hb, z0) in sections:
        if hw <= 1e-4:
            rings.append([len(verts)]); verts.append((0.0, y, z0)); continue
        ring = []
        for k in range(n):
            a = 2 * math.pi * k / n
            c, s = math.cos(a), math.sin(a)
            e = 2.0 / ex
            x = hw * math.copysign(abs(c) ** e, c)
            hz = ht if s >= 0 else hb
            z = z0 + hz * math.copysign(abs(s) ** e, s)
            ring.append(len(verts)); verts.append((x, y, z))
        rings.append(ring)
    fy = []
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        yc = (sections[i][0] + sections[i + 1][0]) / 2
        if len(a) == 1:
            for k in range(n):
                faces.append([a[0], b[k], b[(k + 1) % n]]); fy.append((yc, 2 * math.pi * (k + 0.5) / n))
        elif len(b) == 1:
            for k in range(n):
                faces.append([a[k], b[0], a[(k + 1) % n]]); fy.append((yc, 2 * math.pi * (k + 0.5) / n))
        else:
            for k in range(n):
                faces.append([a[k], b[k], b[(k + 1) % n], a[(k + 1) % n]]); fy.append((yc, 2 * math.pi * (k + 0.5) / n))
    return mesh_obj(name, verts, faces, mats, mat_idx=(lambda i, p: mat_fn(*fy[i])) if mat_fn else None,
                    parent=parent, subsurf=subsurf)


def wing_slab(name, pts, t_root, t_tip, x_root, x_tip, z0, mats, parent=None, mat_fn=None, bevel=0.05):
    """평면 다각형 날개 — pts = 평면형 꼭짓점 [(x, y)] (반시계). 두께는 x 에 따라 t_root → t_tip 선형, 위아래 대칭(살짝 위로 볼록).
    mat_fn(nx, ny, nz, cx, cy) → 재질 인덱스."""
    nv = len(pts)
    if sum(pts[i][0] * pts[(i + 1) % nv][1] - pts[(i + 1) % nv][0] * pts[i][1] for i in range(nv)) < 0:
        pts = pts[::-1]                                   # 반시계로 맞춘다 → 윗면 법선 +Z
    verts = []
    for (x, y) in pts:
        k = min(1, max(0, (abs(x) - x_root) / max(1e-6, x_tip - x_root)))
        t = t_root + (t_tip - t_root) * k
        verts.append((x, y, z0 + t * 0.6))
    for (x, y) in pts:
        k = min(1, max(0, (abs(x) - x_root) / max(1e-6, x_tip - x_root)))
        t = t_root + (t_tip - t_root) * k
        verts.append((x, y, z0 - t * 0.4))
    faces = [list(range(nv)), list(range(2 * nv - 1, nv - 1, -1))]
    for i in range(nv):
        j = (i + 1) % nv
        faces.append([i, nv + i, nv + j, j])
    ob = mesh_obj(name, verts, faces, mats, smooth=False, parent=parent, bevel=bevel)
    if mat_fn:
        me = ob.data
        cen = sum((v.co for v in me.vertices), me.vertices[0].co * 0) / len(me.vertices)
        for p in me.polygons:
            nrm = p.normal.copy()
            if nrm.dot(p.center - cen) < 0:
                nrm = -nrm
            p.material_index = mat_fn(nrm.x, nrm.y, nrm.z, p.center.x, p.center.y)
    return ob


def cyl(name, loc, r, depth, axis, mats, parent=None, verts=24, r2=None, cap=True):
    import bpy
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc,
                                            end_fill_type='NGON' if cap else 'NOTHING')
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=depth, vertices=verts, location=loc,
                                        end_fill_type='NGON' if cap else 'NOTHING')
    o = bpy.context.object
    o.name = name
    if axis == 'Y':
        o.rotation_euler = (math.radians(-90), 0, 0)     # 로컬 +Z → 월드 +Y (원뿔 radius2 쪽이 앞)
    for m in mats:
        o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    if parent:
        o.parent = parent
    return o


def sphere(name, loc, r, scale, mats, parent=None, seg=32):
    import bpy
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    for m in mats:
        o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    if parent:
        o.parent = parent
    return o


# ─────────── ① 윙맨 (무인 요격기) ───────────
def _pl(xs, ys, x):
    """구간 선형 보간 (xs 오름차순)."""
    if x <= xs[0]:
        return ys[0]
    for i in range(len(xs) - 1):
        if x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + (ys[i + 1] - ys[i]) * t
    return ys[-1]


# 윙맨 평면형(오른쪽 반, x ≥ 0) — 앞전은 노즈 쪽이 급하고(체인) 크랭크 뒤 50° 후퇴, 뒷전은 가운데가 들어간 노치
WM_LE = ([0.0, 0.55, 1.25, 2.6, 4.55, 4.78], [5.0, 3.85, 2.50, 0.85, -1.55, -2.02])
WM_TE = ([0.0, 0.62, 0.95, 1.55, 2.55, 4.55, 4.78], [-3.92, -3.92, -3.50, -3.50, -2.95, -2.28, -2.12])
WM_XMAX = 4.78


def wingman_body(M, root):
    """블렌디드 플라잉윙 한 장 — 스팬 방향 스테이션 × 시위 방향 에어포일(두께 분포 √c·(1−c)) 매개 곡면.
    앞전·뒷전이 칼날처럼 얇아져서 위에서 보면 가장자리가 림라이트를 받는다. 재질: 앞전 띠·노즈 캡 = 타일, 바깥 뒷전 = 엘레본 판."""
    NS, NC = 30, 22
    # 스테이션 — 뿌리 쪽 촘촘(코사인)
    xs = [WM_XMAX * (1 - math.cos(math.pi / 2 * i / (NS - 1))) for i in range(NS)]
    xs_full = [-x for x in xs[::-1]] + xs[1:]
    cs = [0.5 * (1 - math.cos(math.pi * j / (NC - 1))) for j in range(NC)]      # 앞전·뒷전 촘촘

    def thick(x):
        ax = abs(x)
        return 0.46 * (1 - ax / WM_XMAX) ** 1.4 + 0.05

    def prof(c):
        return math.sqrt(max(c, 0.0)) * (1 - c) / 0.3849
    verts, faces, fm = [], [], []
    top, bot = [], []
    for x in xs_full:
        ax = abs(x)
        le, te = _pl(*WM_LE, ax), _pl(*WM_TE, ax)
        T = thick(x)
        # 노즈 쪽(긴 시위 앞부분)은 두께를 앞전으로 몰지 않게 — 위치 y 로도 얇게
        rt, rb = [], []
        for c in cs:
            y = le + (te - le) * c
            k = prof(c) * min(1.0, max(0.25, (5.0 - y) / 2.2))
            rt.append(len(verts)); verts.append((x, y, T * 0.62 * k))
        for c in cs:
            y = le + (te - le) * c
            k = prof(c) * min(1.0, max(0.25, (5.0 - y) / 2.2))
            rb.append(len(verts)); verts.append((x, y, -T * 0.38 * k))
        # 앞전·뒷전 꼭짓점은 위아래 같은 점으로
        rb[0] = rt[0]; rb[-1] = rt[-1]
        top.append(rt); bot.append(rb)

    def key_top(x0, x1, j):
        ax = (abs(x0) + abs(x1)) / 2
        c = (cs[j] + cs[j + 1]) / 2
        le = _pl(*WM_LE, ax)
        if le - (le - _pl(*WM_TE, ax)) * c > 4.25:
            return 1                                           # 노즈 캡
        if c < 0.15 + 0.05 * min(1, ax / 2.0) and ax > 0.9:
            return 1                                           # 앞전 타일 띠
        if c > 0.76 and 1.7 < ax < 4.35:
            return 2                                           # 엘레본
        return 0
    for i in range(len(xs_full) - 1):
        for j in range(NC - 1):
            a, b, c_, d = top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]
            f = [a, d, c_, b]
            f = [v for k_, v in enumerate(f) if v not in f[:k_]]
            if len(f) >= 3:
                faces.append(f); fm.append(key_top(xs_full[i], xs_full[i + 1], j))
            a, b, c_, d = bot[i][j], bot[i + 1][j], bot[i + 1][j + 1], bot[i][j + 1]
            f = [a, b, c_, d]
            f = [v for k_, v in enumerate(f) if v not in f[:k_]]
            if len(f) >= 3:
                faces.append(f); fm.append(1)
    # 날개 끝 마감
    for side in (0, len(xs_full) - 1):
        ring = top[side] + bot[side][-2:0:-1]
        faces.append(ring if side else ring[::-1]); fm.append(0)
    ob = mesh_obj("wing", verts, faces, [M['hull'], M['tile'], M['panel']], mat_idx=lambda i, p: fm[i], parent=root)
    return ob


def build_wingman(M, root):
    """무인 요격기(UCAV) — 꼬리 없는 블렌디드 플라잉윙 + 가운데 등 혹(센서·흡입구·안테나) + 납작한 쌍발 이온 슬롯 노즐.
    조종석 없음: 노즈 위 짙은 센서 바이저 + 청록 렌즈. 앞전 크랭크에 레이저 이미터 2개(빨간 렌즈 = 윙맨 레이저 색)."""
    H = M['hull']
    wingman_body(M, root)
    # 등 혹 — 낮은 초타원 로프트(날개 윗면에서 솟는다)
    secs = [(4.35, 0.0, 0.0, 0.0, 0.18), (3.9, 0.30, 0.13, 0.10, 0.20), (3.1, 0.56, 0.24, 0.12, 0.22),
            (2.0, 0.78, 0.32, 0.14, 0.24), (0.6, 0.90, 0.36, 0.15, 0.24), (-1.0, 0.92, 0.35, 0.15, 0.22),
            (-2.4, 0.86, 0.30, 0.14, 0.18), (-3.4, 0.74, 0.22, 0.12, 0.12), (-3.85, 0.66, 0.16, 0.10, 0.06)]
    loft("hump", secs, [H], parent=root, n=36, subsurf=1, ex=2.4)
    # 센서 바이저 — 짙은 유리 + 앞쪽 청록 렌즈
    sphere("visor", (0, 2.75, 0.42), 0.26, (1.05, 2.3, 0.36), [M['glass']], parent=root)
    sphere("eye_ring", (0, 3.55, 0.36), 0.13, (1.2, 0.7, 0.55), [M['gun']], parent=root, seg=20)
    sphere("eye", (0, 3.60, 0.37), 0.085, (1.2, 0.8, 0.6), [M['eye']], parent=root, seg=16)
    # 등 흡입구(검은 쐐기) + 위성 통신 안테나 판 + 등 능선
    sphere("intake", (0, 1.05, 0.55), 0.30, (1.5, 0.75, 0.26), [M['tile']], parent=root, seg=24)
    sphere("intake_lip", (0, 1.30, 0.57), 0.30, (1.55, 0.30, 0.26), [M['panel']], parent=root, seg=24)
    sphere("spine", (0, -1.4, 0.55), 0.24, (0.85, 4.2, 0.30), [H], parent=root)
    sphere("ant", (0, -0.35, 0.64), 0.17, (1, 1, 0.45), [M['panel']], parent=root, seg=16)
    for sg in (1, -1):
        # 편대등 — 날개 윗면 희미한 띠(실기 '슬라임 라이트')
        sl = [(2.35, -0.85), (3.85, -2.05), (3.82, -2.15), (2.32, -0.95)]
        wing_slab("slime", [(sg * x, y) for (x, y) in sl], 0.006, 0.006, 0.0, 1.0, 0.13, [M['slime']], parent=root, bevel=0.0)
        # 날개 끝 항법등 — 왼쪽 빨강, 오른쪽 초록
        sphere("nav", (sg * 4.70, -2.10, 0.02), 0.10, (1, 1, 1), [M['navg'] if sg > 0 else M['navr']], parent=root, seg=12)
        # 레이저 이미터 — 앞전 크랭크의 포드 + 앞을 보는 빨간 렌즈
        px = sg * 1.30
        sphere("gun_fair", (px, 1.95, 0.10), 0.24, (1, 2.8, 0.7), [M['gun']], parent=root, seg=24)
        cyl("barrel", (px, 2.75, 0.10), 0.085, 0.70, 'Y', [M['gun']], parent=root, verts=16)
        sphere("muzzle", (px, 3.12, 0.10), 0.085, (1, 1, 1), [M['red']], parent=root, seg=12)
        # 납작한 슬롯 노즐(스텔스 배기) — 검은 덕트 + 청백 발광 슬릿
        nx = sg * 0.50
        cyl("nozzle", (nx, -3.80, 0.08), 0.36, 0.50, 'Y', [M['noz']], parent=root, verts=28, r2=0.36, cap=False).scale = (1.0, 0.55, 1.0)   # 로컬 Y = 월드 Z(높이)
        bpy_disc(M['nozin'], (nx, -3.92, 0.08), 0.30, root).scale = (1.0, 0.55, 1.0)


def bpy_disc(mat, loc, r, parent):
    import bpy
    bpy.ops.mesh.primitive_circle_add(radius=r, vertices=28, fill_type='NGON', location=loc)
    d = bpy.context.object
    d.rotation_euler = (math.radians(90), 0, 0)
    d.data.materials.append(mat)
    d.parent = parent
    return d


# ─────────── ② 호위 드론 (덕트 팬 4발 센티넬) ───────────
def build_aegis(M, root, phase):
    import bpy
    H = M['hull']
    # 원반 동체 — 납작한 렌즈형 + 윗면 링 홈
    RC = 1.95
    secs = [(RC, 0.0, 0.0, 0.0, 0.0)]
    n = 16
    for i in range(1, n):
        t = i / n
        y = RC - 2 * RC * t
        hw = math.sqrt(max(0.0, 1.0 - (2 * t - 1) ** 2)) * RC
        secs.append((y, hw, 0.58 * hw / RC + 0.06, 0.32 * hw / RC + 0.04, 0.0))
    secs.append((-RC, 0.0, 0.0, 0.0, 0.0))
    loft("disc", secs, [H], parent=root, n=40, subsurf=1)
    # 윗면 검은 타일 링(센서 터렛 받침)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.08, minor_radius=0.11, major_segments=48, minor_segments=10, location=(0, -0.1, 0.56))
    t = bpy.context.object; t.data.materials.append(M['tile']); t.parent = root
    for p in t.data.polygons:
        p.use_smooth = True
    # 중앙 돔 — 짙은 유리, 그 앞 센서 블리스터 + 청록 렌즈(진행 방향)
    sphere("dome", (0, -0.1, 0.52), 0.80, (1, 1, 0.55), [M['glass']], parent=root)
    sphere("eye", (0, 0.45, 0.78), 0.17, (1.3, 1.0, 0.7), [M['eye']], parent=root, seg=16)
    # 팔 4개(45° 대각) — 스틸 팔 + 윗면 타일 띠
    for k in range(4):
        a = math.radians(45 + 90 * k)
        ca, sa = math.cos(a), math.sin(a)
        L0, L1 = 1.5, 2.35
        w0, w1 = 0.30, 0.20
        px, py = -sa, ca
        pts = [(ca * L0 + px * w0, sa * L0 + py * w0), (ca * L1 + px * w1, sa * L1 + py * w1),
               (ca * L1 - px * w1, sa * L1 - py * w1), (ca * L0 - px * w0, sa * L0 - py * w0)]
        # 반시계 정렬
        cx_ = sum(p[0] for p in pts) / 4; cy_ = sum(p[1] for p in pts) / 4
        pts.sort(key=lambda p: math.atan2(p[1] - cy_, p[0] - cx_))
        wing_slab("arm", pts, 0.26, 0.20, 0.0, 10.0, 0.06, [H, M['tile']], parent=root, bevel=0.04,
                  mat_fn=lambda nx, ny, nz, cx, cy: 1 if nz > 0.9 else 0)
        # 덕트 링
        dx, dy = ca * 2.85, sa * 2.85
        # 덕트 = 짙은 금속 링(높이 1.6 배) + 위 가장자리 외피색 립
        bpy.ops.mesh.primitive_torus_add(major_radius=0.90, minor_radius=0.15, major_segments=56, minor_segments=14, location=(dx, dy, 0.08))
        d = bpy.context.object; d.data.materials.append(M['panel']); d.parent = root
        d.scale = (1, 1, 1.6)
        for p in d.data.polygons:
            p.use_smooth = True
        bpy.ops.mesh.primitive_torus_add(major_radius=0.92, minor_radius=0.075, major_segments=56, minor_segments=10, location=(dx, dy, 0.30))
        d = bpy.context.object; d.data.materials.append(H); d.parent = root
        for p in d.data.polygons:
            p.use_smooth = True
        # 덕트 안 바닥(어두운 배기 그릴) + 허브
        bpy_disc_flat(M['gun'], (dx, dy, -0.12), 0.80, root)
        cyl("hub", (dx, dy, 0.06), 0.20, 0.22, 'Z', [M['gun']], parent=root, verts=20)
        sphere("hubcap", (dx, dy, 0.18), 0.13, (1, 1, 0.6), [H], parent=root, seg=16)
        # 로터 3엽 — phase 0/1 은 60° 어긋남(2프레임 교대 = 회전 착시)
        for b in range(3):
            ang = math.radians(b * 120 + phase * 60 + k * 17)
            bx, by = math.cos(ang), math.sin(ang)
            nx_, ny_ = -by, bx
            r0, r1, bw0, bw1 = 0.18, 0.76, 0.14, 0.09
            bl = [(dx + bx * r0 + nx_ * bw0, dy + by * r0 + ny_ * bw0), (dx + bx * r1 + nx_ * bw1, dy + by * r1 + ny_ * bw1),
                  (dx + bx * r1 - nx_ * bw1, dy + by * r1 - ny_ * bw1), (dx + bx * r0 - nx_ * bw0, dy + by * r0 - ny_ * bw0)]
            ccx = sum(p[0] for p in bl) / 4; ccy = sum(p[1] for p in bl) / 4
            bl.sort(key=lambda p: math.atan2(p[1] - ccy, p[0] - ccx))
            wing_slab("blade", bl, 0.04, 0.04, 0.0, 10.0, 0.04, [M['rotor']], parent=root, bevel=0.0)
        # 덕트 바깥 상태등(청록 LED)
        sphere("led", (ca * 3.86, sa * 3.86, 0.24), 0.07, (1, 1, 1), [M['eye']], parent=root, seg=10)
    # 앞쪽 쌍열 이미터 — 앞 두 덕트 사이
    for sg in (1, -1):
        cyl("emit", (sg * 0.40, 2.35, 0.12), 0.15, 1.2, 'Y', [M['gun']], parent=root, verts=18)
        sphere("emit_tip", (sg * 0.40, 2.97, 0.12), 0.11, (1, 1, 1), [M['cyan']], parent=root, seg=12)
    cyl("emit_base", (0, 1.90, 0.10), 0.36, 0.60, 'Y', [H], parent=root, verts=24)
    # 뒤 안테나 핀
    cyl("ant", (0, -2.15, 0.30), 0.04, 0.9, 'Y', [M['gun']], parent=root, verts=8)


def bpy_disc_flat(mat, loc, r, parent):
    import bpy
    bpy.ops.mesh.primitive_circle_add(radius=r, vertices=40, fill_type='NGON', location=loc)
    d = bpy.context.object
    d.data.materials.append(mat)
    d.parent = parent
    return d


def render(path):
    import bpy
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("  rendered", path, flush=True)


def do_all(which):
    import bpy
    os.makedirs(REN, exist_ok=True)
    for lv in ('steel', 'gold'):
        if which in ('all', 'wing', 'wing0'):
            for bi in (BANKS if which != 'wing0' else [0, 2]):
                scene(); M = materials(lv); lights()
                root = bpy.data.objects.new("wm", None); bpy.context.scene.collection.objects.link(root)
                build_wingman(M, root)
                root.rotation_euler = (0, math.radians(bi * BANK_DEG), 0)
                render(os.path.join(REN, "wing_%s_b%+d.png" % (lv, bi)))
        if which in ('all', 'aegis'):
            for ph in (0, 1):
                scene(FRAME_A); M = materials(lv); lights()
                root = bpy.data.objects.new("ag", None); bpy.context.scene.collection.objects.link(root)
                build_aegis(M, root, ph)
                render(os.path.join(REN, "aegis_%s_%d.png" % (lv, ph)))


# ══════════════════════════════ 굽기(일반 파이썬) ══════════════════════════════
def post():
    import json
    import numpy as np
    sys.path.insert(0, HERE)
    import spacez_planets as sp
    from starship_scene import sharpen, bbox
    cells = []
    rep = {}

    def cell(name):
        a = sp.load_rgba(os.path.join(REN, name + ".png"))
        x0, y0, x1, y1 = bbox(a)
        assert x0 > 2 and y0 > 2 and x1 < a.shape[1] - 3 and y1 < a.shape[0] - 3, ("잘림", name, (x0, y0, x1, y1))
        rep[name] = [x0, y0, x1, y1]
        return sharpen(sp.resize_premul(a, CELL, CELL), 0.4)
    rows = []
    for lv in ('steel', 'gold'):
        r = [cell("wing_%s_b%+d" % (lv, bi)) for bi in BANKS]
        if lv == 'gold':
            for c in r:
                c[..., 0] = np.clip(c[..., 0] * 1.10, 0, 1); c[..., 1] = np.clip(c[..., 1] * 1.04, 0, 1); c[..., 2] = np.clip(c[..., 2] * 0.90, 0, 1)
        rows.append(np.concatenate(r, axis=1))
    ag = []
    for lv in ('steel', 'gold'):
        for ph in (0, 1):
            c = cell("aegis_%s_%d" % (lv, ph))
            if lv == 'gold':
                c[..., 0] = np.clip(c[..., 0] * 1.10, 0, 1); c[..., 1] = np.clip(c[..., 1] * 1.04, 0, 1); c[..., 2] = np.clip(c[..., 2] * 0.90, 0, 1)
            ag.append(c)
    ag.append(np.zeros((CELL, CELL, 4), np.float32))
    rows.append(np.concatenate(ag, axis=1))
    A = sp.clean_alpha(np.concatenate(rows, axis=0))
    os.makedirs(PUB, exist_ok=True)
    q, sz = sp.save_webp(A, os.path.join(PUB, "drones.webp"), 70, q0=88, qmin=60, qmax=94, aq=92)
    rep["drones"] = dict(w=A.shape[1], h=A.shape[0], q=q, kb=round(sz / 1024, 1))
    print(json.dumps(rep, indent=1))


if IN_BLENDER:
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    do_all(args[0] if args else 'all')
elif __name__ == "__main__":
    if sys.argv[1:2] == ["post"]:
        post()
    else:
        import subprocess
        exe = "C:/tools/blender-4.2.5-windows-x64/blender.exe"
        subprocess.check_call([exe, "-b", "-P", os.path.abspath(__file__), "--"] + (sys.argv[1:] or ['all']))
        post()
