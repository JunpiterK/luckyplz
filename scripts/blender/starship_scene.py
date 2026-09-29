# -*- coding: utf-8 -*-
"""Space-Z 플레이어 기체 = 초대형 스테인리스 2단 우주선 오마주 (2026-09-29, Blender Cycles).

운영자: "우주선도 최신 우주선을 똑같이 만들어 주고 약간 빛나는 메탈 은색처럼 — 오마주·헌정하는 게임이니까".
실측 비율(최신 블록 기준, m): 상단 기체 52 × 지름 9 · 노즈 오자이브 13 · 전방 플랩 2 + 후방 플랩 2(큰 것) ·
윈드워드 반쪽 검은 육각 내열타일 · 엔진 6기(진공 3 + 해면 3) · 부스터 72 (핫스테이징 링 + 그리드 핀 3장 + 엔진 33).
표기(상표): 모델·텍스처에 회사명·기체명·로고 없음. 콜사인 LUCKY-1 은 화면 글자로만 쓴다(모델에는 무표기).

좌표: 기체 축 = 월드 +Z(노즈 위). 카메라는 -Y 에서 +Y 를 보는 직교(화면 위 = 노즈). 기체 로컬 +X = 배(타일) 방향.
  기본 자세 ALPHA = 135° — 배가 카메라 반대쪽 오른편을 향한다 → 은색 동체가 주인공, 오른쪽 가장자리에 검은 타일 띠,
  플랩 4장은 좌우로 펼쳐 보인다(투영 0.71). 뱅크 프레임은 이 자세에서 축 회전(롤)만 바꾼다.
  뱅크 +(오른쪽 이동) = 기체 왼편이 카메라 쪽으로 굴러 온다(위에서 본 비행기의 오른쪽 뱅크) → 타일 띠가 줄어든다.
금속: 반사할 환경이 없으면 검게 나온다(art_pipeline_blender 메모) — 월드 그라디언트 + 세로 띠 소프트박스 2장
  (카메라엔 안 보이고 반사에만)로 긴 스페큘러 줄을 만든다. 색 = Standard(AgX 는 은색을 탁하게 누른다).

실행:
  Blender : C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/starship_scene.py -- ship stack
  굽기    : python scripts/blender/starship_scene.py post     → public/assets/spacez/ship_steel.webp · launch_stack.webp
중간 PNG: scripts/og-assets/spacez_ship/ (git 미추적)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REN = os.path.join(ROOT, "scripts", "og-assets", "spacez_ship")
PUB = os.path.join(ROOT, "public", "assets", "spacez")
try:
    import bpy  # noqa
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

# ── 형상 (m) ──
R = 4.5
SHIP_H = 52.0
NOSE_L = 13.0
ALPHA = 122.0                     # 배(타일) 방위 — 카메라 방향에서 잰 각
BANKS = [-2, -1, 0, 1, 2]         # 프레임 순서 = 아틀라스 왼→오 (bank −1 … +1)
BANK_DEG = 12.0                   # 한 칸당 롤
# 기체 프레임: 세로 56 m (z −2.0 … 54.0), 가로 28 m. 게임 쪽 앵커는 SZ_SHIP_ART 표가 이 값을 쓴다
FR_Z0, FR_Z1, FR_W = -2.0, 54.0, 28.0
FR_PX = (352, 704)                # 렌더 (4 배) → 굽기 때 88×176
# 스택 프레임: 세로 128 m (z −2 … 126), 가로 24 m
BOOST_H = 72.0
ST_Z0, ST_Z1, ST_W = -2.0, 126.0, 24.0
ST_PX = (192, 1024)               # → 96×512
SAMPLES = int(os.environ.get("SS_SAMPLES", "160"))


# ══════════════════════════════ Blender ══════════════════════════════
def scene(res, ortho, cz):
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
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.filter_size = 1.0
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    # 월드 — 위는 은은한 푸른 하늘빛, 아래(지평 아래)는 어둡다. 금속이 반사할 '세상'
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    el = ramp.color_ramp.elements
    el[0].position = 0.30; el[0].color = (0.020, 0.024, 0.034, 1)
    el[1].position = 0.80; el[1].color = (0.50, 0.56, 0.68, 1)
    mid = el.new(0.52); mid.color = (0.20, 0.23, 0.29, 1)      # 지평 — 옆을 보는 판재(플랩)가 검게 죽지 않게
    nt.links.new(ramp.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 0.7
    sc.world = w
    cd = bpy.data.cameras.new("cam")
    cd.type = 'ORTHO'
    cd.ortho_scale = ortho
    cd.clip_end = 400
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    cam.location = (0, -150, cz)
    cam.rotation_euler = (math.radians(90), 0, 0)
    sc.camera = cam
    return sc


def area(name, loc, size, energy, color, shape='RECTANGLE', sy=None, cam_vis=False, target=(0, 0, 26)):
    import bpy
    from mathutils import Vector
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.color = color
    ld.shape = shape
    ld.size = size
    if sy is not None:
        ld.size_y = sy
    o = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')
    o.visible_camera = cam_vis
    return o


def lights(cz, scale=1.0):
    """키 = 왼쪽 위 앞(운석·행성과 같은 광원). 세로 띠 소프트박스 2장 = 스테인리스 원통의 긴 하이라이트.
    림 = 오른쪽 뒤 청색(어두운 우주에서 타일 쪽 실루엣을 세운다)."""
    s = scale
    area("key", (-70 * s, -90 * s, cz + 60 * s), 30 * s, 2.0e5 * s * s, (1.0, 0.97, 0.92), target=(0, 0, cz))
    area("stripL", (-38 * s, -60 * s, cz), 3.0 * s, 2.6e4 * s * s, (0.92, 0.96, 1.0), sy=90 * s, target=(0, 0, cz))
    area("stripR", (46 * s, -52 * s, cz + 6 * s), 2.6 * s, 2.6e4 * s * s, (0.84, 0.90, 1.0), sy=86 * s, target=(0, 0, cz))
    area("rim", (60 * s, 70 * s, cz + 20 * s), 20 * s, 1.2e5 * s * s, (0.42, 0.70, 1.0), target=(0, 0, cz))
    area("fill", (0, -120 * s, cz - 60 * s), 40 * s, 1.5e4 * s * s, (0.55, 0.62, 0.80), target=(0, 0, cz))


def hex_texture(path, px=512):
    """이음새 없이 반복되는 육각 타일 — 거의 검정, 타일마다 명도·거칠기 미세 편차, 가는 이음새.
    가로 8칸 × 세로 (8·2/√3 행). 반복 주기: u = 8w, v = 8·1.5h' (h' = w/√3·2·0.75)."""
    import numpy as np
    from PIL import Image
    ncol = 8
    w = px / ncol                       # 뾰족 위 육각의 폭
    rowh = w * math.sqrt(3) / 2          # 행 간격
    nrow = 2 * round(px / rowh / 2)
    H = int(round(nrow * rowh))
    yy, xx = np.mgrid[0:H, 0:px].astype(np.float32)
    best = np.full((H, px), 1e9, np.float32); sec = np.full((H, px), 1e9, np.float32)
    idx = np.zeros((H, px), np.int32)
    rng = np.random.RandomState(7)
    shade = rng.uniform(0.0035, 0.0085, (nrow + 2) * (ncol + 2))
    # 드물게 밝은 교체 타일 (실물에도 회백 타일이 섞여 있다)
    for k in rng.choice(len(shade), 3, replace=False):
        shade[k] = 0.045
    for j in range(-1, nrow + 1):
        for i in range(-1, ncol + 1):
            cx = i * w + (j % 2) * w / 2; cy = j * rowh
            for ox in (-px, 0, px):
                for oy in (-H, 0, H):
                    d = np.hypot(xx - cx - ox, yy - cy - oy)
                    m = d < best
                    sec = np.where(m, best, np.minimum(sec, d))
                    idx = np.where(m, (j % nrow) * (ncol + 2) + (i % ncol), idx)
                    best = np.minimum(best, d)
    edge = np.clip((sec - best) / 2.2, 0, 1)             # 이음새 = 두 중심까지 거리 차가 작은 곳
    col = shade[idx] * edge + 0.016 * (1 - edge)
    img = np.dstack([col * 0.96, col * 0.98, col * 1.04, np.ones_like(col)])
    Image.fromarray((np.clip(img, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8), "RGBA").save(path)
    return px, H, w


def materials():
    import bpy
    os.makedirs(REN, exist_ok=True)
    hp = os.path.join(REN, "hex_tiles.png")
    assert os.path.exists(hp), "먼저 python starship_scene.py hex (Blender 파이썬엔 PIL 이 없다)"
    im0 = bpy.data.images.load(hp, check_existing=True)
    tp, th = im0.size
    TILE_W = 0.34                                      # 실물 육각 한 장 ≈ 0.3~0.35 m
    rep_u, rep_v = 1.0 / (TILE_W * 8), 1.0 / (TILE_W * 8 * th / tp)

    # 스테인리스 — 은색 금속, 약간 거칠고(롤링 결) 1.83 m 링 용접선이 아주 옅게
    st = bpy.data.materials.new("steel"); st.use_nodes = True
    nt = st.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.64, 0.655, 0.68, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.20
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    md = nt.nodes.new("ShaderNodeMath"); md.operation = 'PINGPONG'; md.inputs[1].default_value = 0.915
    nt.links.new(sep.outputs["Z"], md.inputs[0])
    sm = nt.nodes.new("ShaderNodeMath"); sm.operation = 'LESS_THAN'; sm.inputs[1].default_value = 0.05
    nt.links.new(md.outputs[0], sm.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs[3].default_value = 0.22; rr.inputs[4].default_value = 0.34
    nt.links.new(nz.outputs["Fac"], rr.inputs[0])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = 'MULTIPLY_ADD'
    add.inputs[1].default_value = 0.025
    nt.links.new(sm.outputs[0], add.inputs[0]); nt.links.new(rr.outputs[0], add.inputs[2])
    nt.links.new(add.outputs[0], b.inputs["Roughness"])
    bmp = nt.nodes.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.05; bmp.inputs["Distance"].default_value = 0.03
    nt.links.new(sm.outputs[0], bmp.inputs["Height"])
    nt.links.new(bmp.outputs["Normal"], b.inputs["Normal"])

    # 내열타일 — 육각 텍스처(UV: u = 둘레 m, v = 높이 m)
    tl = bpy.data.materials.new("tile"); tl.use_nodes = True
    nt = tl.node_tree; b = nt.nodes["Principled BSDF"]
    uv = nt.nodes.new("ShaderNodeUVMap")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (rep_u, rep_v, 1)
    nt.links.new(uv.outputs[0], mp.inputs["Vector"])
    im = nt.nodes.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(hp); im.interpolation = 'Cubic'
    nt.links.new(mp.outputs[0], im.inputs["Vector"])
    nt.links.new(im.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.74
    b.inputs["Specular IOR Level"].default_value = 0.08
    inv = nt.nodes.new("ShaderNodeInvert"); nt.links.new(im.outputs["Color"], inv.inputs["Color"])
    bmp = nt.nodes.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.35; bmp.inputs["Distance"].default_value = 0.03
    bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(im.outputs["Color"], bw.inputs[0])
    nt.links.new(bw.outputs[0], bmp.inputs["Height"]); nt.links.new(bmp.outputs["Normal"], b.inputs["Normal"])

    def plain(name, col, rough, metal, emit=None, es=0.0):
        m = bpy.data.materials.new(name); m.use_nodes = True
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = (*col, 1)
        p.inputs["Roughness"].default_value = rough
        p.inputs["Metallic"].default_value = metal
        if emit:
            p.inputs["Emission Color"].default_value = (*emit, 1)
            p.inputs["Emission Strength"].default_value = es
        return m
    eng = plain("engine", (0.26, 0.25, 0.25), 0.38, 1.0)
    engin = plain("engine_in", (0.05, 0.04, 0.04), 0.5, 0.2, emit=(1.0, 0.45, 0.16), es=2.5)
    dark = plain("vent", (0.03, 0.03, 0.035), 0.6, 0.3)
    grid = plain("gridfin", (0.20, 0.20, 0.21), 0.48, 1.0)
    frost = plain("frost", (0.80, 0.83, 0.88), 0.62, 0.0)
    return dict(steel=st, tile=tl, eng=eng, engin=engin, dark=dark, grid=grid, frost=frost)


def ogive_r(t):
    """노즈 밑에서 t(m) 올라간 곳의 반지름 — 탄젠트 오자이브."""
    rho = (R * R + NOSE_L * NOSE_L) / (2 * R)
    return max(0.0, math.sqrt(max(0.0, rho * rho - t * t)) + R - rho)


def revolve(name, prof, M, seg=96, tile_fn=None, mat_fn=None):
    """프로파일 [(z, r)] 회전체 + UV(u = 둘레 m, v = z m). 면마다 재질 인덱스를 정한다:
    mat_fn(az, zc) → 재질 키. az = 로컬 방위(+X = 배)."""
    import bpy
    verts, faces, fz = [], [], []
    rings = []
    for (z, r) in prof:
        ring = []
        if r <= 1e-4:
            ring = [len(verts)]; verts.append((0.0, 0.0, z))
        else:
            for k in range(seg):
                a = 2 * math.pi * k / seg
                ring.append(len(verts)); verts.append((math.cos(a) * r, math.sin(a) * r, z))
        rings.append(ring)
    uvs = []
    for ai in range(len(rings) - 1):
        lo, hi = rings[ai], rings[ai + 1]
        z0, r0 = prof[ai]; z1, r1 = prof[ai + 1]
        for k in range(seg):
            a0 = 2 * math.pi * k / seg; a1 = 2 * math.pi * (k + 1) / seg
            if len(hi) == 1:
                f = [lo[k], lo[(k + 1) % seg], hi[0]]
                uv = [(a0 * R, z0), (a1 * R, z0), ((a0 + a1) / 2 * R, z1)]
            elif len(lo) == 1:
                f = [lo[0], hi[(k + 1) % seg], hi[k]]
                uv = [((a0 + a1) / 2 * R, z0), (a1 * R, z1), (a0 * R, z1)]
            else:
                f = [lo[k], lo[(k + 1) % seg], hi[(k + 1) % seg], hi[k]]
                uv = [(a0 * R, z0), (a1 * R, z0), (a1 * R, z1), (a0 * R, z1)]
            faces.append(f); uvs.append(uv)
            fz.append(((a0 + a1) / 2, (z0 + z1) / 2))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ul = me.uv_layers.new(name="UVMap")
    li = 0
    for pi, p in enumerate(me.polygons):
        for j in range(p.loop_total):
            ul.data[p.loop_start + j].uv = uvs[pi][j]
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    keys = []
    for pi, p in enumerate(me.polygons):
        a, zc = fz[pi]
        a = (a + math.pi) % (2 * math.pi) - math.pi
        k = mat_fn(a, zc) if mat_fn else 'steel'
        if k not in keys:
            keys.append(k); ob.data.materials.append(M[k])
        p.material_index = keys.index(k)
        p.use_smooth = True
    return ob


def slab(name, M, pts_root, pts_tip, az, thick_root, thick_tip, belly=(1, 0, 0), parent=None, tile_face=True):
    """플랩·핀 판재. pts_root/pts_tip = [(반지름 방향 거리 s, z)] 앞뒤 두 점씩 (뿌리 z0,z1 / 끝 z0,z1).
    방위 az 로 뻗는다. 면 법선이 배(+X) 쪽이면 타일, 아니면 스틸."""
    import bpy
    from mathutils import Vector
    ox, oy = math.cos(az), math.sin(az)
    tx, ty = -oy, ox
    vs = []
    for (s, z), th in [(pts_root[0], thick_root), (pts_root[1], thick_root), (pts_tip[1], thick_tip), (pts_tip[0], thick_tip)]:
        for sgn in (-1, 1):
            vs.append((ox * s + tx * th * sgn / 2, oy * s + ty * th * sgn / 2, z))
    # 0,1 = root z0 (−,+) · 2,3 = root z1 · 4,5 = tip z1 · 6,7 = tip z0
    fs = [[0, 2, 4, 6], [1, 7, 5, 3], [0, 1, 3, 2], [2, 3, 5, 4], [4, 5, 7, 6], [6, 7, 1, 0]]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bv = ob.modifiers.new("bev", 'BEVEL'); bv.width = min(thick_root, thick_tip) * 0.35; bv.segments = 2
    ob.data.materials.append(M['steel']); ob.data.materials.append(M['tile'])
    me.calc_normals_split() if hasattr(me, 'calc_normals_split') else None
    from mathutils import Vector as _V
    cen = sum((_V(v) for v in vs), _V()) / len(vs)
    for p in me.polygons:
        n = p.normal.copy()
        if n.dot(p.center - cen) < 0:          # 감김 방향과 무관하게 바깥 법선으로
            n = -n
        p.material_index = 1 if (tile_face and n.x * belly[0] + n.y * belly[1] > 0.35) else 0
    # 타일 UV — 대충 평면 투영(판재는 작아서 충분)
    ul = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        for j in range(p.loop_total):
            v = me.vertices[me.loops[p.loop_start + j].vertex_index].co
            ul.data[p.loop_start + j].uv = (v.x * 0.7 + v.y * 0.7, v.z)
    if parent:
        ob.parent = parent
    return ob


def build_ship(M, root, z0=0.0, tiles=True):
    """상단 기체 한 대. root(빈 오브젝트)의 로컬: +Z 노즈, +X 배."""
    import bpy
    from mathutils import Vector
    Z1 = z0 + SHIP_H - NOSE_L
    prof = [(z0, R * 0.985), (z0 + 0.35, R)]
    zz = z0 + 0.35
    while zz < Z1 - 1e-6:
        zz = min(Z1, zz + 1.83)
        prof.append((zz, R))
    n = 40
    for i in range(1, n + 1):
        t = NOSE_L * (1 - math.cos(math.pi / 2 * i / n))       # 끝으로 갈수록 촘촘히
        prof.append((Z1 + t, ogive_r(t)))
    TILE_HALF = math.radians(93)

    def mfn(a, zc):
        if not tiles:
            return 'steel'
        if zc > z0 + SHIP_H - 1.1:
            return 'tile'                                       # 노즈 끝 캡
        return 'tile' if abs(a) < TILE_HALF else 'steel'
    hull = revolve("ship_hull", prof, M, seg=96, mat_fn=mfn)
    hull.parent = root
    parts = [hull]
    # 후방 플랩 — 방위 배±100°, 뿌리 z 1.0~12.8, 끝 z 2.2~9.4, 몸통 밖으로 4.3 m
    for sg in (1, -1):
        az = sg * math.radians(100)
        parts.append(slab("aft_flap", M, [(R - 0.2, z0 + 1.0), (R - 0.2, z0 + 12.8)], [(R + 4.3, z0 + 2.2), (R + 4.3, z0 + 9.2)],
                          az, 0.70, 0.42, parent=root))
        # 힌지 에어로커버 — 플랩 뿌리를 덮는 길쭉한 페어링
        parts.append(slab("aft_cover", M, [(R - 0.3, z0 + 0.6), (R - 0.3, z0 + 13.6)], [(R + 0.9, z0 + 1.4), (R + 0.9, z0 + 12.6)],
                          az, 1.5, 1.2, parent=root))
    # 전방 플랩 — 최신 블록: 작고 리워드 쪽(배±118°)으로 올라가 노즈 곡면에 붙는다
    for sg in (1, -1):
        az = sg * math.radians(118)
        zr0, zr1 = Z1 + 1.4, Z1 + 7.6
        rr0, rr1 = ogive_r(zr0 - Z1), ogive_r(zr1 - Z1)
        parts.append(slab("fwd_flap", M, [(rr0 - 0.15, zr0), (rr1 - 0.15, zr1)], [(rr0 + 2.7, zr0 + 1.3), (rr1 + 1.6, zr1 - 1.2)],
                          az, 0.42, 0.26, parent=root))
    # 레이스웨이 — 리워드 쪽 세로 배관 덮개(배 반대 −X 에서 약간 옆)
    import bmesh  # noqa
    bpy.ops.mesh.primitive_cylinder_add(radius=0.36, depth=SHIP_H - NOSE_L - 3.0, vertices=12,
                                        location=(math.cos(math.radians(160)) * (R + 0.1), math.sin(math.radians(160)) * (R + 0.1), z0 + (SHIP_H - NOSE_L) / 2 + 0.5))
    rw = bpy.context.object; rw.data.materials.append(M['steel']); rw.parent = root
    for p in rw.data.polygons:
        p.use_smooth = True
    # 엔진 6기 — 진공 3(바깥, 큰 벨 — 스커트 아래로 조금 나온다) + 해면 3(가운데)
    for k in range(3):
        a = math.radians(60 + 120 * k)
        for (rad, r1, r2, depth, zc) in [(2.95, 1.18, 0.55, 3.2, z0 - 0.35), ]:
            bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth, vertices=32, end_fill_type='NOTHING',
                                            location=(math.cos(a) * rad, math.sin(a) * rad, zc + depth / 2 - 0.9))
            e = bpy.context.object; e.data.materials.append(M['eng']); e.parent = root
            sol = e.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.08
            for p in e.data.polygons:
                p.use_smooth = True
        a2 = math.radians(120 * k)
        bpy.ops.mesh.primitive_cone_add(radius1=0.66, radius2=0.38, depth=1.8, vertices=24, end_fill_type='NOTHING',
                                        location=(math.cos(a2) * 1.25, math.sin(a2) * 1.25, z0 - 0.2 + 0.9 - 0.5))
        e = bpy.context.object; e.data.materials.append(M['eng']); e.parent = root
        sol = e.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.06
    # 엔진 안쪽 달아오름 (아래에서만 보인다 — 옆에선 거의 안 보여도 벨 입구 가장자리에 미세한 온기)
    bpy.ops.mesh.primitive_circle_add(radius=4.35, vertices=64, fill_type='NGON', location=(0, 0, z0 + 0.05))
    d = bpy.context.object; d.data.materials.append(M['dark']); d.parent = root
    return parts


def render(path):
    import bpy
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("  rendered", path, flush=True)


def do_ship(banks=BANKS):
    import bpy
    cz = (FR_Z0 + FR_Z1) / 2
    for bi in banks:
        sc = scene(FR_PX, FR_Z1 - FR_Z0, cz)
        M = materials()
        lights(cz, 0.5)
        root = bpy.data.objects.new("ship", None); sc.collection.objects.link(root)
        build_ship(M, root)
        # 배 방위: 카메라 쪽(−Y) 기준 ALPHA → 월드각 = −90° + ALPHA. 뱅크 +는 CCW(위에서 본 +Z 회전)
        root.rotation_euler = (0, 0, math.radians(-90 + ALPHA + bi * BANK_DEG))
        render(os.path.join(REN, "ship_b%+d.png" % bi))


def do_stack():
    import bpy
    cz = (ST_Z0 + ST_Z1) / 2
    sc = scene(ST_PX, ST_Z1 - ST_Z0, cz)
    M = materials()
    lights(cz, 1.0)
    root = bpy.data.objects.new("stack", None); sc.collection.objects.link(root)
    # 부스터 — 스틸 원통 72 m, 아래 스커트 + 핫스테이징 링(z 68.6~71.8 통풍구) + 그리드 핀 3장
    B = BOOST_H
    prof = [(0.0, R * 0.96), (0.8, R)]
    zz = 0.8
    while zz < B - 1e-6:
        zz = min(B, zz + 1.83); prof.append((zz, R))

    def bfn(a, zc):
        if 68.8 < zc < 71.6:
            return 'vent' if (int((a + math.pi) / (2 * math.pi) * 48) % 2 == 0) else 'steel'
        return 'steel'
    Mx = dict(M); Mx['vent'] = M['dark']
    bh = revolve("booster", prof, Mx, seg=96, mat_fn=bfn); bh.parent = root
    # 그리드 핀 3장 (최신 블록 — 3장, 크고 핫스테이징 링 아래)
    for k in range(3):
        az = math.radians(-60 + 120 * k)
        slab("gridfin", M, [(R - 0.1, 61.0), (R - 0.1, 66.6)], [(R + 3.6, 61.4), (R + 3.6, 66.2)], az, 0.9, 0.9,
             parent=root, tile_face=False).data.materials[0] = M['grid']
    # 체인(공력 스트레이크) 2줄
    for sg in (1, -1):
        slab("chine", M, [(R - 0.1, 6.0), (R - 0.1, 58.0)], [(R + 0.55, 7.0), (R + 0.55, 57.0)], sg * math.radians(90), 0.5, 0.3,
             parent=root, tile_face=False)
    # 부스터 엔진 스커트 아래 벨 가장자리
    for k in range(13):
        a = 2 * math.pi * k / 13
        bpy.ops.mesh.primitive_cone_add(radius1=0.7, radius2=0.45, depth=1.4, vertices=16, end_fill_type='NOTHING',
                                        location=(math.cos(a) * 3.3, math.sin(a) * 3.3, -0.35))
        e = bpy.context.object; e.data.materials.append(M['eng']); e.parent = root
    sroot = bpy.data.objects.new("ship", None); sc.collection.objects.link(sroot)
    sroot.parent = root
    build_ship(M, sroot, z0=B + 0.25)
    root.rotation_euler = (0, 0, math.radians(-90 + ALPHA))
    render(os.path.join(REN, "stack.png"))


def main_blender(args):
    os.makedirs(REN, exist_ok=True)
    if not args or 'ship' in args:
        do_ship()
    elif 'ship0' in args:
        do_ship([0])
    if not args or 'stack' in args:
        do_stack()


# ══════════════════════════════ 굽기(일반 파이썬) ══════════════════════════════
def _sp():
    sys.path.insert(0, HERE)
    import spacez_planets as sp
    return sp


def sharpen(a, amount=0.35, sigma=0.7):
    import numpy as np
    from scipy.ndimage import gaussian_filter
    A = a[..., 3:4]
    pm = a[..., :3] * A
    bl = np.dstack([gaussian_filter(pm[..., c], sigma) for c in range(3)])
    pm2 = np.minimum(np.clip(pm + (pm - bl) * amount, 0, None), A)
    out = a.copy()
    out[..., :3] = np.where(A > 1e-4, pm2 / np.maximum(A, 1e-4), 0)
    return out


def bbox(a):
    import numpy as np
    m = a[..., 3] > 0.02
    ys, xs = np.nonzero(m)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def post():
    import numpy as np
    sp = _sp()
    rep = {}
    # ① 기체 아틀라스 — 5 프레임 가로, 칸 88×176
    fw, fh = FR_PX[0] // 4, FR_PX[1] // 4
    cells = []
    for bi in BANKS:
        a = sp.load_rgba(os.path.join(REN, "ship_b%+d.png" % bi))
        x0, y0, x1, y1 = bbox(a)
        assert x0 > 2 and y0 > 2 and x1 < a.shape[1] - 3 and y1 < a.shape[0] - 3, ("잘림", bi, (x0, y0, x1, y1))
        rep["ship_b%+d" % bi] = dict(bbox=[x0, y0, x1, y1])
        c = sharpen(sp.resize_premul(a, fw, fh), 0.35)
        cells.append(c)
    A = np.concatenate(cells, axis=1)
    A = sp.clean_alpha(A)
    q, sz = sp.save_webp(A, os.path.join(PUB, "ship_steel.webp"), 40, q0=88, qmin=60, qmax=95, aq=90)
    rep["ship_steel"] = dict(w=A.shape[1], h=A.shape[0], q=q, kb=round(sz / 1024, 1))
    # ② 발사대 스택 — 96×512
    a = sp.load_rgba(os.path.join(REN, "stack.png"))
    x0, y0, x1, y1 = bbox(a)
    assert x0 > 2 and y0 > 2 and x1 < a.shape[1] - 3 and y1 < a.shape[0] - 3, ("스택 잘림", (x0, y0, x1, y1))
    c = sp.clean_alpha(sharpen(sp.resize_premul(a, ST_PX[0] // 2, ST_PX[1] // 2), 0.3))
    q, sz = sp.save_webp(c, os.path.join(PUB, "launch_stack.webp"), 40, q0=88, qmin=60, qmax=95, aq=90)
    rep["launch_stack"] = dict(w=c.shape[1], h=c.shape[0], q=q, kb=round(sz / 1024, 1), bbox=[x0, y0, x1, y1])
    # 게임 앵커용 수치 — 프레임 안 z 위치 (px 비)
    rep["anchor"] = dict(ship_frame_m=[FR_Z0, FR_Z1, FR_W], ship_tip_frac=(FR_Z1 - SHIP_H) / (FR_Z1 - FR_Z0),
                         skirt_frac=(FR_Z1 - 0.0) / (FR_Z1 - FR_Z0), stack_frame_m=[ST_Z0, ST_Z1, ST_W],
                         stack_bottom_frac=(ST_Z1 - 0.0) / (ST_Z1 - ST_Z0))
    import json
    with open(os.path.join(REN, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, indent=1))


if IN_BLENDER:
    argv = sys.argv
    main_blender(argv[argv.index("--") + 1:] if "--" in argv else [])
elif __name__ == "__main__":
    if sys.argv[1:2] == ["post"]:
        post()
    elif sys.argv[1:2] == ["hex"]:
        os.makedirs(REN, exist_ok=True)
        print(hex_texture(os.path.join(REN, "hex_tiles.png")))
    else:
        import subprocess
        os.makedirs(REN, exist_ok=True)
        hex_texture(os.path.join(REN, "hex_tiles.png"))
        exe = "C:/tools/blender-4.2.5-windows-x64/blender.exe"
        subprocess.check_call([exe, "-b", "-P", os.path.abspath(__file__), "--"] + sys.argv[1:])
        post()
