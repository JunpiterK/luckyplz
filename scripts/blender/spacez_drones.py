# -*- coding: utf-8 -*-
"""Space-Z 아이템 드론 2종 스프라이트 — Blender Cycles (2026-10-08 v2 '진공판').

v1(같은 날 오전): 윙맨 = 꼬리 없는 플라잉윙 UCAV, 호위 드론 = 덕트 팬 4발 센티넬.
운영자: "대기가 있어야 프로펠러가 도는 드론은 안 어울린다. 우주는 초고진공이라 작용·반작용 추진만 있으니
        형태와 구동 방식을 바꾸고 UFO 형태나 멋진 셰이프로 재구성해라."  → 날개·프로펠러·공력 조종면 전부 폐기.

  ① 윙맨(MINI, 아이템 '✈ +1') — 날개 없는 우주 요격기.
     팔각 단면 다면체 동체(평면 셰이딩 = 면마다 빛이 갈린다) + 앞 센서 창(짙은 유리) + 코 양옆 레이저 이미터(빨강 = 윙맨 레이저 색)
     + 동체에서 띄워 지주로 단 방열판 한 쌍(흰 세라믹 + 히트파이프 골, 뒤로 살짝 벌어진 좁고 긴 판 — 동체와 틈이 있어 날개로 안 읽힌다)
     + 후미 그리드 이온 추력기(원통 하우징 + 청색 발광 그리드 테) + RCS 쿼드 4개(앞 둘·뒤 둘, 각각 옆 노즐 + 앞/뒤 노즐).
  ② 호위 드론(AEGIS, 위성 임무 보상 🛸) — UFO 렌즈 원반.
     매끈한 렌즈 동체(회전체) + 가운데 센서 돔(짙은 유리, 앞쪽 청록 눈) + 하부 고리형 이온 추력기(위 렌즈보다 넓어 렌즈와 바깥 링 사이로
     청색 그리드 고리가 보인다) + 바깥 링 + 대각 45°마다 RCS 쿼드 포드 4개(바깥 방향 노즐 1 + 접선 노즐 2) + 앞쪽 쌍 이미터(청록).
     돌아가는 기계 부품 없음 — 링을 따라 도는 항법등·이온 배기·RCS 분사는 게임 쪽 그리기 코드(sz:mod:drones)가 빛으로만 얹는다.
  실존 기체·상표·국적 표지 없음.

스타일 = 플레이어 기체(starship_scene.py)와 같은 문법: Standard 뷰(AgX 금지 — 은색을 탁하게 누른다), 스테인리스 금속 +
  거의 검은 내열타일, 왼쪽 위 키 + 세로 띠 소프트박스(긴 스페큘러) + 오른쪽 청색 림, 월드 그라디언트는 반사에만.
  도장 2종: steel(솔로·방장) / gold(2인 모드 참가자) — 기체 LIVERY 와 같은 값.

좌표: 평면도(위에서 내려다봄). 월드 +Y = 화면 위 = 노즈, +X = 화면 오른쪽, 카메라는 +Z 에서 −Z 를 본다.
칸: 윙맨 FRAME_U(10.5) / 호위 FRAME_A(7.4) 단위 정사각, 렌더 RPX(384) → 굽기 CELL(128px, 샤픈).
  게임 쪽 앵커(SZ_DRONE 표 — 노즐·이미터·RCS 위치)는 이 단위 그대로 적는다. 아래 WM_*·AG_* 상수가 원천.

실행:
  전체   : python scripts/blender/spacez_drones.py              (Blender 렌더 → 굽기)
  렌더만 : C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/spacez_drones.py -- all   (wing | aegis)
  굽기만 : python scripts/blender/spacez_drones.py post         → public/assets/dodge/drones.webp
  시안   : SZD_SAMPLES=48 로 샘플 낮추기 / SZD_REN=<폴더> 로 중간 PNG 위치 바꾸기(기본 scripts/og-assets/spacez_drones, git 미추적)
아틀라스(128px 칸, 2열 × 2행 = 256×256):
  행 0 = 윙맨 steel · gold / 행 1 = 호위 드론 steel · gold
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REN = os.environ.get("SZD_REN") or os.path.join(ROOT, "scripts", "og-assets", "spacez_drones")
PUB = os.path.join(ROOT, "public", "assets", "dodge")
SAMPLES = int(os.environ.get("SZD_SAMPLES", "128"))
FRAME_U = 10.5                    # 윙맨 칸 = 10.5 단위 정사각 (전장 ≈ 8.9)
FRAME_A = 7.4                     # 호위 드론 칸 = 7.4 단위 (노즐 끝 지름 ≈ 6.7)
RPX = 384
CELL = 128
LIVERY = {
    'steel': dict(base=(0.64, 0.655, 0.68), rr=(0.11, 0.24)),
    'gold': dict(base=(1.0, 0.77, 0.34), rr=(0.10, 0.22), coat=0.55),
}
# 앵커(모델 단위) — 게임 SZ_DRONE 표와 같은 값
WM_MUZZLE = (0.66, 4.50)          # 레이저 이미터 렌즈
WM_ENGINE = (0.0, -3.66)          # 이온 그리드 끝
WM_RCS_F = (1.16, 2.15)           # 앞 RCS 쿼드 중심(±x)
WM_RCS_R = (0.78, -2.90)          # 뒤 RCS 쿼드 중심(±x)
AG_HULL_R = 2.25                  # 위 렌즈 반지름
AG_ION = (2.12, 2.70)             # 이온 고리 안·밖 반지름
AG_RIM = 2.90                     # 바깥 링 중심 반지름
AG_POD_R = 3.06                   # RCS 포드 중심 반지름(45° + 90°k)
AG_EMIT = (0.36, 3.06)            # 앞 쌍 이미터(하우징 앞면 y, 렌즈 끝은 +0.12)
AG_TILT = 30.0                    # 호위 드론만 앞으로 30° 기울여 찍는다(평면도 원반은 시계판처럼 읽혔다)
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


def materials(livery, rough_add=0.0):
    import bpy
    LV = dict(LIVERY[livery])
    LV['rr'] = (LV['rr'][0] + rough_add, LV['rr'][1] + rough_add)

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
    panel = plain("panel", (0.34, 0.35, 0.37), 0.30, 1.0)                          # 한 톤 어두운 판(링·테두리)
    glass = plain("glass", (0.010, 0.016, 0.026), 0.04, 0.35, coat=1.0)      # 센서 창 — 짙은 유리
    dome = plain("dome", (0.015, 0.06, 0.08), 0.16, 0.2, emit=(0.0, 0.45, 0.6), es=0.12, coat=0.7)   # UFO 돔 — 짙은 청록 유리(안쪽 희미한 빛)
    noz = plain("nozzle", (0.20, 0.19, 0.19), 0.42, 1.0)
    eye = plain("eye", (0.0, 0.0, 0.0), 0.3, 0.0, emit=(0.0, 0.85, 1.0), es=4.0)            # 센서 렌즈 — 기체 청록 액센트
    red = plain("laser_red", (0.0, 0.0, 0.0), 0.3, 0.0, emit=(1.0, 0.16, 0.12), es=2.8)      # 윙맨 레이저 포구
    cyan = plain("laser_cyan", (0.0, 0.0, 0.0), 0.3, 0.0, emit=(0.35, 0.85, 1.0), es=2.6)    # 호위 드론 이미터
    ion = plain("ion", (0.02, 0.03, 0.06), 0.4, 0.0, emit=(0.20, 0.48, 1.0), es=0.62)         # 이온 그리드 — 청색 발광
    iondk = plain("ion_dark", (0.03, 0.035, 0.05), 0.45, 0.6, emit=(0.10, 0.25, 0.8), es=0.25)  # 그리드 살(어두운 칸막이)
    # 방열판 — 흰 세라믹 코팅 + 길이 방향 히트파이프 골(오브젝트 X 로 흐르는 띠 = 판 길이 방향 줄무늬)
    rad, nt, b = principled("radiator")
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.38
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs["Scale"].default_value = 1.15; wv.inputs["Distortion"].default_value = 0.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    e = cr.color_ramp.elements
    e[0].position = 0.10; e[0].color = (0.16, 0.17, 0.19, 1)
    e[1].position = 0.30; e[1].color = (0.80, 0.82, 0.84, 1)
    nt.links.new(wv.outputs["Fac"], cr.inputs[0])
    nt.links.new(cr.outputs[0], b.inputs["Base Color"])
    bmp = nt.nodes.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.6; bmp.inputs["Distance"].default_value = 0.02
    nt.links.new(wv.outputs["Fac"], bmp.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], b.inputs["Normal"])
    return dict(hull=st, tile=tl, gun=gun, panel=panel, glass=glass, dome=dome, noz=noz, eye=eye, red=red, cyan=cyan,
                ion=ion, iondk=iondk, rad=rad)


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


def loft(name, sections, mats, parent=None, n=28, subsurf=1, mat_fn=None, ex=2.6, smooth=True):
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
                    parent=parent, subsurf=subsurf, smooth=smooth)


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


def lathe(name, prof, mats, parent=None, seg=72, mat_fn=None, smooth=True, z_rot=0.0):
    """회전체 — prof = [(r, z)] 순서대로 이어 붙인 단면(r≈0 은 한 점). mat_fn(i_prof, k_seg) → 재질 인덱스."""
    verts, faces, rings, fm = [], [], [], []
    for (r, z) in prof:
        if r <= 1e-5:
            rings.append([len(verts)]); verts.append((0.0, 0.0, z)); continue
        ring = []
        for k in range(seg):
            a = z_rot + 2 * math.pi * k / seg
            ring.append(len(verts)); verts.append((r * math.cos(a), r * math.sin(a), z))
        rings.append(ring)
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(seg):
            k2 = (k + 1) % seg
            if len(a) == 1:
                faces.append([a[0], b[k], b[k2]])
            elif len(b) == 1:
                faces.append([a[k], b[0], a[k2]])
            else:
                faces.append([a[k], b[k], b[k2], a[k2]])
            fm.append(mat_fn(i, k) if mat_fn else 0)
    return mesh_obj(name, verts, faces, mats, mat_idx=lambda i, p: fm[i], smooth=smooth, parent=parent)


def nozzle(M, pos, d, parent, throat=0.045, exit_r=0.085, length=0.15, z=None):
    """RCS 노즐 — 종 모양(목이 좁고 출구가 넓은 원뿔), 열린 출구가 방향 d=(dx, dy) 를 본다. pos 는 노즐 목(뿌리) 위치."""
    import bpy
    dx, dy = d
    n = math.hypot(dx, dy); dx, dy = dx / n, dy / n
    zz = pos[2] if len(pos) > 2 else (z or 0.0)
    c = (pos[0] + dx * length / 2, pos[1] + dy * length / 2, zz)
    bpy.ops.mesh.primitive_cone_add(radius1=throat, radius2=exit_r, depth=length, vertices=14, location=c, end_fill_type='NOTHING')
    o = bpy.context.object
    o.rotation_euler = (math.radians(-90), 0, math.atan2(-dx, dy))
    o.data.materials.append(M['noz'])
    for p in o.data.polygons:
        p.use_smooth = True
    sol = o.modifiers.new("sol", 'SOLIDIFY'); sol.thickness = 0.012
    o.parent = parent
    return o


def box(name, loc, half, mats, parent=None, rot_z=0.0, bevel=0.03):
    import bpy
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = half
    o.rotation_euler = (0, 0, rot_z)
    for m in mats:
        o.data.materials.append(m)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        bv = o.modifiers.new("bev", 'BEVEL'); bv.width = bevel; bv.segments = 2
    if parent:
        o.parent = parent
    return o


def _pl(xs, ys, x):
    """구간 선형 보간 (xs 오름차순)."""
    if x <= xs[0]:
        return ys[0]
    for i in range(len(xs) - 1):
        if x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + (ys[i + 1] - ys[i]) * t
    return ys[-1]


# ─────────── ① 윙맨 (날개 없는 우주 요격기) ───────────
# 동체 단면표 (y, 반폭, 위 반높이, 아래 반높이, z0) — 앞→뒤. 팔각 단면 + 평면 셰이딩 = 다면체.
WM_SECS = [(3.10, 0.0, 0.0, 0.0, 0.10), (2.70, 0.30, 0.16, 0.10, 0.10), (1.80, 0.78, 0.31, 0.18, 0.08),
           (0.60, 1.08, 0.40, 0.22, 0.06), (-0.80, 1.04, 0.38, 0.22, 0.05), (-2.00, 0.86, 0.33, 0.20, 0.03),
           (-2.70, 0.64, 0.28, 0.18, 0.02), (-2.85, 0.0, 0.0, 0.0, 0.02)]
# 앞 갈퀴(이미터 붐) 2개 — 어깨에서 앞으로 뻗은 좁은 다면체 빔, 끝에 레이저 렌즈. 사이가 비어 '포크' 실루엣
WM_PRONG_X, WM_PRONG_DEG = 0.86, 2.5
WM_PRONG = [(4.50, 0.0, 0.0, 0.0, 0.10), (4.30, 0.13, 0.09, 0.06, 0.10), (3.40, 0.19, 0.13, 0.08, 0.10),
            (1.80, 0.24, 0.16, 0.10, 0.09), (0.60, 0.28, 0.17, 0.10, 0.08), (-0.40, 0.0, 0.0, 0.0, 0.06)]
# 등 모듈(전자장비 블록) — 동체 위에 한 층 더 얹은 좁은 다면체
WM_DORSAL = [(2.45, 0.0, 0.0, 0.0, 0.34), (2.05, 0.26, 0.12, 0.05, 0.36), (1.20, 0.40, 0.18, 0.06, 0.38),
             (-0.40, 0.44, 0.19, 0.06, 0.40), (-1.80, 0.38, 0.16, 0.06, 0.36), (-2.35, 0.26, 0.10, 0.05, 0.30),
             (-2.50, 0.0, 0.0, 0.0, 0.28)]
WM_RAD = [(1.44, 0.90), (2.06, 0.64), (2.20, -1.90), (1.58, -1.90)]   # 방열판 평면형(오른쪽) — 배 가운데(꼬리 날개처럼 안 읽히게)


def _side_mat(lo, hi):
    def f(y, ang):
        a = math.degrees(ang) % 360
        if 180 < a < 360:
            return 1                               # 배면 — 타일
        if (a < 45 or a > 135) and lo < y < hi:
            return 2                               # 옆 체인 면 — 어두운 판(윤곽이 또렷해진다)
        return 0
    return f


def build_wingman(M, root):
    """우주 요격기 — 날개·조종면 없음. 다면체 동체 + 앞 갈퀴 2(이미터) + 등 모듈 + 센서 + 방열판 2(지주로 띄움) + 이온 추력기 + RCS 쿼드 4."""
    H = M['hull']
    loft("hull", WM_SECS, [H, M['tile'], M['panel']], parent=root, n=8, subsurf=0, ex=2.0, mat_fn=_side_mat(-2.6, 2.6), smooth=False)
    for sg in (1, -1):
        pr = loft("prong", WM_PRONG, [H, M['tile'], M['panel']], parent=root, n=8, subsurf=0, ex=2.0, mat_fn=_side_mat(0.4, 4.2),
                  smooth=False)
        pr.location = (sg * WM_PRONG_X, 0, 0)
        pr.rotation_euler = (0, 0, sg * math.radians(WM_PRONG_DEG))
        # 갈퀴 끝 레이저 렌즈 + 갈퀴 위 어두운 띠
        mx, my = WM_MUZZLE
        sphere("muzzle", (sg * mx, my, 0.10), 0.085, (1, 1.3, 1), [M['red']], parent=root, seg=12)
        sphere("gun_ring", (sg * (mx + 0.01), my - 0.16, 0.10), 0.12, (1, 0.7, 0.9), [M['gun']], parent=root, seg=14)
    loft("dorsal", WM_DORSAL, [H, M['panel']], parent=root, n=8, subsurf=0, ex=2.0, smooth=False,
         mat_fn=lambda y, ang: 1 if (math.degrees(ang) % 360) < 45 or (math.degrees(ang) % 360) > 135 else 0)
    box("spine", (0, -1.0, 0.61), (0.06, 1.05, 0.03), [M['tile']], parent=root, bevel=0.015)
    lathe("ant", [(0, 0.68), (0.20, 0.66), (0.22, 0.62), (0, 0.60)], [M['panel']], parent=root, seg=24).location = (0, 0.30, 0)
    # 센서 창 — 등 모듈 앞 다면 유리 + 뱃머리 청록 눈
    s = sphere("visor", (0, 1.55, 0.53), 0.24, (1.0, 2.4, 0.40), [M['glass']], parent=root, seg=10)
    for p in s.data.polygons:
        p.use_smooth = False
    sphere("eye", (0, 2.95, 0.16), 0.10, (1.2, 0.9, 0.6), [M['eye']], parent=root, seg=14)
    # 방열판 — 동체에서 틈을 두고 지주 2개로 단 좁고 긴 판(몸통과 거의 나란함). 흰 세라믹 + 히트파이프 골, 테두리는 어두운 판
    for sg in (1, -1):
        wing_slab("radiator", [(sg * x, y) for (x, y) in WM_RAD], 0.07, 0.07, 0.0, 10.0, 0.10, [M['rad'], M['panel']], parent=root,
                  bevel=0.02, mat_fn=lambda nx, ny, nz, cx, cy: 0 if nz > 0.9 else 1)
        for yy in (0.35, -1.35):
            xin = _pl([-2.7, -2.0, -0.8, 0.6], [0.64, 0.86, 1.04, 1.08], yy) - 0.08
            x1 = WM_RAD[0][0] + (WM_RAD[0][1] - yy) / (WM_RAD[0][1] - WM_RAD[3][1]) * (WM_RAD[3][0] - WM_RAD[0][0]) + 0.03
            st = cyl("strut", (sg * (xin + x1) / 2, yy, 0.09), 0.05, x1 - xin, 'Z', [M['gun']], parent=root, verts=10)
            st.rotation_euler = (0, math.radians(90), 0)
    # 이온 추력기 — 원통 하우징 + 넓어지는 종 + 그리드 테(청색 발광) + 안쪽 그리드 원판(발광)
    ex_, ey_ = WM_ENGINE
    cyl("eng_house", (0, -2.92, 0.04), 0.60, 0.62, 'Y', [M['gun']], parent=root, verts=32)
    cyl("eng_bell", (0, -3.42, 0.04), 0.68, 0.40, 'Y', [M['noz']], parent=root, verts=32, r2=0.60, cap=False)
    ring = torus("eng_grid", (0, ey_ + 0.06, 0.04), 0.62, 0.07, [M['ion']], parent=root)
    ring.rotation_euler = (math.radians(90), 0, 0)
    bpy_disc(M['ion'], (0, ey_ + 0.12, 0.04), 0.58, root)
    # RCS 쿼드 4 — 앞 둘(갈퀴 바깥: 옆 노즐 + 앞 노즐), 뒤 둘(엔진 옆: 옆 노즐 + 뒤 노즐)
    for sg in (1, -1):
        fx, fy = WM_RCS_F
        box("rcs_f", (sg * fx, fy, 0.10), (0.15, 0.17, 0.12), [M['panel']], parent=root)
        nozzle(M, (sg * (fx + 0.14), fy, 0.10), (sg, 0), root)
        nozzle(M, (sg * fx, fy + 0.16, 0.10), (0, 1), root)
        rx, ry = WM_RCS_R
        box("rcs_r", (sg * rx, ry, 0.10), (0.15, 0.17, 0.12), [M['panel']], parent=root)
        nozzle(M, (sg * (rx + 0.14), ry, 0.10), (sg, 0), root)
        nozzle(M, (sg * rx, ry - 0.16, 0.10), (0, -1), root)


def bpy_last():
    import bpy
    return bpy.context.object


def torus(name, loc, R, r, mats, parent=None, seg=56, mseg=12):
    import bpy
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=seg, minor_segments=mseg, location=loc)
    t = bpy.context.object
    t.name = name
    for m in mats:
        t.data.materials.append(m)
    for p in t.data.polygons:
        p.use_smooth = True
    if parent:
        t.parent = parent
    return t


def bpy_disc(mat, loc, r, parent):
    import bpy
    bpy.ops.mesh.primitive_circle_add(radius=r, vertices=32, fill_type='NGON', location=loc)
    d = bpy.context.object
    d.rotation_euler = (math.radians(90), 0, 0)
    d.data.materials.append(mat)
    d.parent = parent
    return d


# ─────────── ② 호위 드론 (UFO 렌즈 원반) ───────────
def lens_top(r):
    """위 렌즈 높이 — 가운데 0.80, 가장자리 0 으로 매끈하게(렌즈 단면)."""
    t = min(1.0, r / AG_HULL_R)
    return 0.80 * (1 - t * t) ** 1.25 + 0.04


def build_aegis(M, root):
    H = M['hull']
    # 위 렌즈 — 회전체, 가운데는 돔이 앉으므로 r 0.8 안쪽은 평평하게
    prof = [(0.0, lens_top(0.0))]
    for i in range(1, 19):
        r = AG_HULL_R * (1 - math.cos(math.pi / 2 * i / 18))
        prof.append((r, lens_top(r)))
    prof += [(AG_HULL_R + 0.02, 0.0), (AG_HULL_R - 0.10, -0.12), (1.6, -0.30), (0.0, -0.36)]
    lathe("lens", prof, [H], parent=root, seg=96)
    # 동심 홈 2줄(타일) — 렌즈 곡면에 붙인 가는 고리
    for rr in (1.55,):
        torus("groove", (0, 0, lens_top(rr) - 0.005), rr, 0.028, [M['tile']], parent=root, seg=96, mseg=8)
    # 센서 돔 — 짙은 유리 + 받침 고리 + 앞쪽 청록 눈
    sphere("dome", (0, 0, lens_top(0) - 0.10), 0.86, (1, 1, 0.72), [M['dome']], parent=root, seg=48)
    torus("dome_collar", (0, 0, lens_top(0.88) + 0.01), 0.90, 0.07, [M['panel']], parent=root, seg=72, mseg=10)
    sphere("eye", (0, 0.52, lens_top(0) + 0.38), 0.14, (1.3, 1.0, 0.55), [M['eye']], parent=root, seg=18)
    # 하부 고리형 이온 추력기 — 위 렌즈보다 넓어서 렌즈와 바깥 링 사이로 보인다. 48칸 그리드(4칸마다 어두운 살)
    ri, ro = AG_ION
    lathe("ion_ring", [(ri, -0.05), (ro, -0.05)], [M['ion'], M['iondk']], parent=root, seg=96,
          mat_fn=lambda i, k: 1 if (k % 4) == 0 else 0)
    lathe("ion_well", [(ro, -0.04), (ro, -0.22), (ri - 0.2, -0.24)], [M['gun']], parent=root, seg=96)
    # 바깥 링 — 어두운 판 금속 고리(납작)
    tr = torus("rim", (0, 0, 0.02), AG_RIM, 0.25, [M['panel']], parent=root, seg=128, mseg=16)
    tr.scale = (1, 1, 0.62)
    torus("rim_lip", (0, 0, 0.12), AG_RIM - 0.10, 0.06, [H], parent=root, seg=128, mseg=8)
    # RCS 쿼드 포드 4 — 45° 대각. 바깥 방향 노즐 1 + 접선 노즐 2(시계·반시계)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        ca, sa = math.cos(a), math.sin(a)
        px, py = ca * AG_POD_R, sa * AG_POD_R
        box("pod", (px, py, 0.08), (0.17, 0.27, 0.15), [H], parent=root, rot_z=a, bevel=0.05)
        box("pod_cap", (px + ca * 0.02, py + sa * 0.02, 0.24), (0.10, 0.18, 0.02), [M['tile']], parent=root, rot_z=a, bevel=0.01)
        nozzle(M, (px + ca * 0.16, py + sa * 0.16, 0.08), (ca, sa), root)
        tx, ty = -sa, ca
        nozzle(M, (px + tx * 0.26, py + ty * 0.26, 0.08), (tx, ty), root, length=0.13)
        nozzle(M, (px - tx * 0.26, py - ty * 0.26, 0.08), (-tx, -ty), root, length=0.13)
    # 앞쪽 쌍 이미터 — 링 앞(노즈 방향) 하우징 + 청록 렌즈
    ex, ey = AG_EMIT
    box("emit_house", (0, ey - 0.16, 0.10), (0.52, 0.16, 0.12), [M['gun']], parent=root, bevel=0.05)
    for sg in (1, -1):
        cyl("emit", (sg * ex, ey - 0.02, 0.10), 0.10, 0.30, 'Y', [M['gun']], parent=root, verts=16)
        sphere("emit_tip", (sg * ex, ey + 0.12, 0.10), 0.085, (1, 1, 1), [M['cyan']], parent=root, seg=12)


def render(path):
    import bpy
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("  rendered", path, flush=True)


def do_all(which):
    import bpy
    os.makedirs(REN, exist_ok=True)
    for lv in ('steel', 'gold'):
        if which in ('all', 'wing'):
            scene(FRAME_U); M = materials(lv, -0.05); lights()     # 평면 다면체는 넓은 반사 꼬리가 면 전체를 덮어 하얗게 뜬다 → 결을 한 단계 매끈하게
            root = bpy.data.objects.new("wm", None); bpy.context.scene.collection.objects.link(root)
            build_wingman(M, root)
            render(os.path.join(REN, "wing_%s.png" % lv))
        if which in ('all', 'aegis'):
            scene(FRAME_A); M = materials(lv); lights()
            root = bpy.data.objects.new("ag", None); bpy.context.scene.collection.objects.link(root)
            build_aegis(M, root)
            root.rotation_euler = (math.radians(-AG_TILT), 0, 0)    # 앞(화면 아래)쪽이 보이게 기울임 → 돔이 위로 솟아 UFO 로 읽힌다
            render(os.path.join(REN, "aegis_%s.png" % lv))


# ══════════════════════════════ 굽기(일반 파이썬) ══════════════════════════════
def post():
    import json
    import numpy as np
    sys.path.insert(0, HERE)
    import spacez_planets as sp
    from starship_scene import sharpen, bbox
    rep = {}

    def cell(name, gold):
        a = sp.load_rgba(os.path.join(REN, name + ".png"))
        x0, y0, x1, y1 = bbox(a)
        assert x0 > 2 and y0 > 2 and x1 < a.shape[1] - 3 and y1 < a.shape[0] - 3, ("잘림", name, (x0, y0, x1, y1))
        rep[name] = [x0, y0, x1, y1]
        c = sharpen(sp.resize_premul(a, CELL, CELL), 0.4)
        if gold:
            c[..., 0] = np.clip(c[..., 0] * 1.10, 0, 1); c[..., 1] = np.clip(c[..., 1] * 1.04, 0, 1); c[..., 2] = np.clip(c[..., 2] * 0.90, 0, 1)
        return c
    rows = []
    for kind in ('wing', 'aegis'):
        rows.append(np.concatenate([cell("%s_%s" % (kind, lv), lv == 'gold') for lv in ('steel', 'gold')], axis=1))
    A = sp.clean_alpha(np.concatenate(rows, axis=0))
    os.makedirs(PUB, exist_ok=True)
    q, sz = sp.save_webp(A, os.path.join(PUB, "drones.webp"), 60, q0=90, qmin=70, qmax=95, aq=95)
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
