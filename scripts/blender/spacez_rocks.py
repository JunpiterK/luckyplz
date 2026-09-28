# -*- coding: utf-8 -*-
"""Space-Z 위험물(맞으면 데미지) 실사 아트 — Blender Cycles 렌더 + 아틀라스 굽기 (2026-09-29).

운영자: "맞으면 데미지가 가는 unit 들이 조금 blur 해 보이고, 혜성·소행성은 퀄리티가 매우 떨어진다.
선명하고 리얼한 소행성, 질감이 제대로 느껴지게."

무엇을 만드나 (전부 행성과 같은 고정 키라이트 = planets_scene.add_lights 의 왼쪽 위 앞 태양 + 오른쪽 뒤 청색 림)
  rocks_m   운석 6종 × 자전 16프레임 (112px 칸 — DPR 3 폰에서도 1:1 이상)  — 일반·조준·편대·파편·협곡 가장자리·황금 운석 공용
  rocks_b   큰 바위 3종 × 12프레임 (160px 칸)   — 소행성 무리(클러스터)·분열암 몸통 (천천히 돌아 12프레임이면 충분)
  rocks_bh  rocks_b 0번 바위의 '달아오른 균열' 발광만 (가산 합성, 알파 = 달아오름)
  ice       토성 고리 얼음 조각 6종 (정지 — 게임에서 회전하지 않는다, 64px)
  mine      자기 기뢰 (6방향 대칭이라 60° 한 주기 × 8프레임, 96px)
  comet     혜성 핵(얼음 섞인 검은 돌) — 코마·먼지 꼬리·이온 꼬리는 post 에서 numpy 로 굽는다

자전의 원리 — 빛을 구운 스프라이트를 ctx.rotate 로 돌리면 빛도 같이 돈다(가짜). 그래서 돌은 '시선에서
18° 기운 축'으로 돌리고 광원은 고정한 채 16프레임을 찍는다. 게임은 자전각에서 가장 가까운 프레임을 고르고
남는 각(±11.25°)만 ctx.rotate 로 돌린다 → 모양은 매끄럽게 돌고, 빛 방향 오차는 ±11° 이내, 프레임 사이 튐 없음.

한 파일이 두 모드로 돈다
  일반 파이썬 : python scripts/blender/spacez_rocks.py all            # 렌더 → 굽기
                python scripts/blender/spacez_rocks.py render [세트..] # Blender 서브프로세스
                python scripts/blender/spacez_rocks.py post            # 아틀라스·_lo·매니페스트·접사 시트
  Blender     : blender.exe -b -P scripts/blender/spacez_rocks.py -- [세트..]
  환경변수 RK_SAMPLES=32 로 시안(빠르게) 확인

출력
  중간 PNG : scripts/og-assets/spacez_rocks/<세트>/<이름>_<프레임>.png  (git 미추적 — 크다)
  게임 자산 : public/assets/spacez/z/rocks_m.webp · rocks_b.webp · rocks_bh.webp · rk_ice.webp · rk_mine.webp ·
              rk_comet.webp · rk_ctail.webp  (+ 각 _lo = 절반 해상도)
  매니페스트 : scripts/og-assets/spacez_rocks/manifest.json — 칸 크기·등가 반지름 비(k)·용량. 런타임 표 SZ_RK 가 이 값을 쓴다

규칙
  - Standard 뷰 변환(AgX 는 색을 워시한다 — 메모 art_pipeline_blender)
  - 등가 반지름 비 k = sqrt(알파>0.5 면적/π) / (칸/2) 를 프레임 평균으로 실측 → 게임은 그리기 칸 = 2·R충돌 / k.
    '보이는 돌 = 맞는 원' (눈대중 금지)
  - 스티커 외곽선 금지. 가독성은 ① 오른쪽 뒤 림라이트(어두운 쪽 가장자리), ② 실루엣 바깥 1px 남짓한 옅은
    그늘(밝은 배경 위에서 경계), ③ 약한 반사광(그늘 면이 완전 검정이 되지 않게) 로 만든다
  - 칸 가장자리 3px 투명 여백 — 아틀라스 이웃 칸 번짐 방지
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
REN_DIR = os.path.join(ROOT, "scripts", "og-assets", "spacez_rocks")
PUB_DIR = os.path.join(ROOT, "public", "assets", "spacez", "z")
BLENDER = os.environ.get("BLENDER_EXE", r"C:/tools/blender-4.2.5-windows-x64/blender.exe")
SAMPLES = int(os.environ.get("RK_SAMPLES", "128"))

# 월드 단위: 돌 평균 반지름 ≈ 1. 칸이 덮는 반폭 = HALF (최대 돌출 + 그늘 여백)
HALF = 1.32
KEY_DIR = (-4.0, -4.5, 3.4)
RIM_EMIT = float(os.environ.get("RK_RIM", "7.5"))
EXPO = float(os.environ.get("RK_EXPO", "0.0"))       # 노출(스톱) — 햇빛 면이 중간 밝기 성운보다 확실히 밝게, 하이라이트는 안 날아가게      # planets_scene.add_lights 와 같은 키 (천체 → 광원)
RIM_DIR = (3.6, 4.6, 1.6)

# 세트 표 — cell = 최종 칸(px), ss = 렌더 배율, n = 자전 프레임, spin = 한 바퀴 각(도)
SETS = {
    "met":  dict(cell=112, ss=2.5, n=16, spin=360, rows=["m0", "m1", "m2", "m3", "m4", "m5"]),
    "bld":  dict(cell=160, ss=2.5, n=12, spin=360, rows=["b0", "b1", "b2"]),
    "ice":  dict(cell=64,  ss=3,   n=1,  spin=0,   rows=["i0", "i1", "i2", "i3", "i4", "i5"]),
    "mine": dict(cell=96,  ss=3,   n=8,  spin=60,  rows=["mine"]),
    "nuc":  dict(cell=128, ss=2,   n=1,  spin=0,   rows=["nuc"]),
}

# 돌 설계 — 종류(색·금속성) + 모양 씨앗
#   C = 탄소질(어둡고 갈색빛), S = 규산염(회갈색), Sg = 회색 석질, V = 붉은 현무암질, M = 금속질(철-니켈 광택)
ROCKS = {
    "m0": dict(seed=11, kind="S",  axes=(1.10, 0.92, 0.82), lumps=7,  noise=0.10, craters=(2, 6, 26)),
    "m1": dict(seed=23, kind="C",  axes=(1.18, 0.86, 0.80), lumps=8,  noise=0.12, craters=(1, 7, 30)),
    "m2": dict(seed=37, kind="Sg", axes=(1.02, 0.96, 0.86), lumps=6,  noise=0.09, craters=(2, 6, 24), facet=6),
    "m3": dict(seed=41, kind="M",  axes=(1.06, 0.96, 0.88), lumps=9,  noise=0.08, craters=(1, 4, 18)),
    "m4": dict(seed=59, kind="V",  axes=(1.10, 0.93, 0.85), lumps=8,  noise=0.11, craters=(1, 6, 22), facet=3),
    "m5": dict(seed=67, kind="C",  axes=(1.05, 0.98, 0.84), lumps=10, noise=0.13, craters=(2, 8, 34), bilobe=0.35),
    "b0": dict(seed=101, kind="S",  axes=(1.08, 0.94, 0.86), lumps=8,  noise=0.10, craters=(3, 9, 50), sub=7),
    "b1": dict(seed=113, kind="C",  axes=(1.20, 0.88, 0.80), lumps=9,  noise=0.12, craters=(2, 10, 60), sub=7),
    "b2": dict(seed=127, kind="Sg", axes=(1.04, 0.97, 0.88), lumps=7,  noise=0.09, craters=(3, 8, 46), sub=7, facet=4),
    "b3": dict(seed=131, kind="V",  axes=(1.15, 0.90, 0.80), lumps=9,  noise=0.11, craters=(2, 9, 52), sub=7, bilobe=0.3),
    "nuc": dict(seed=211, kind="N", axes=(1.25, 0.86, 0.80), lumps=6, noise=0.10, craters=(0, 3, 10), bilobe=0.45, sub=6),
}
ICE = {"i%d" % k: dict(seed=301 + k * 7, kind="I", axes=(1.12 - 0.03 * k, 0.86 + 0.02 * k, 0.72), lumps=5, noise=0.07,
                       craters=(0, 1, 4), facet=True, sub=4) for k in range(6)}
ROCKS.update(ICE)

# 종류별 색 (선형, 알베도) — c0 어두운 쪽, c1 밝은 쪽
KINDS = {
    "C":  dict(c0=(0.095, 0.088, 0.080), c1=(0.300, 0.268, 0.235), rough=0.94, metal=0.0, spec=0.22),   # 실물보다 밝게 — 햇빛 면이 성운 위에서 읽혀야 한다
    "S":  dict(c0=(0.150, 0.124, 0.094), c1=(0.330, 0.278, 0.212), rough=0.92, metal=0.0, spec=0.25),
    "Sg": dict(c0=(0.130, 0.128, 0.124), c1=(0.300, 0.292, 0.280), rough=0.92, metal=0.0, spec=0.25),
    "V":  dict(c0=(0.165, 0.118, 0.090), c1=(0.345, 0.252, 0.190), rough=0.92, metal=0.0, spec=0.25),
    "M":  dict(c0=(0.130, 0.128, 0.126), c1=(0.300, 0.292, 0.282), rough=0.62, metal=0.26, spec=0.4, bump=0.55),
    "N":  dict(c0=(0.070, 0.068, 0.070), c1=(0.420, 0.470, 0.540), rough=0.75, metal=0.0, spec=0.45),   # 더러운 얼음 — 검은 먼지 껍질 + 드러난 얼음
    "I":  dict(c0=(0.420, 0.580, 0.740), c1=(0.880, 0.950, 1.000), rough=0.2, metal=0.0, spec=0.75),
}

try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False


# ══════════════════════════════ Blender 쪽 ══════════════════════════════
if IN_BLENDER:
    import bpy
    import numpy as np
    from mathutils import Vector, Quaternion, noise

    def reset(res):
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
            print("GPU 설정 실패 — CPU", e)
        sc.cycles.samples = SAMPLES
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 4
        sc.render.resolution_x = res
        sc.render.resolution_y = res
        sc.render.resolution_percentage = 100
        sc.render.film_transparent = True
        sc.render.filter_size = 1.0            # 기본 1.5 는 한 번 더 흐린다 — 선명하게
        sc.render.use_persistent_data = True
        sc.view_settings.view_transform = 'Standard'
        sc.view_settings.look = 'None'
        sc.view_settings.exposure = EXPO
        sc.render.image_settings.file_format = 'PNG'
        sc.render.image_settings.color_mode = 'RGBA'
        sc.render.image_settings.color_depth = '8'
        w = bpy.data.worlds.new("W")
        w.use_nodes = True
        bg = w.node_tree.nodes["Background"]
        bg.inputs[0].default_value = (0.30, 0.34, 0.42, 1)
        bg.inputs[1].default_value = 0.02     # 아주 약한 환경광 — 금속 반사·그늘 면이 완전 검정이 되지 않게
        sc.world = w
        cam_data = bpy.data.cameras.new("cam")
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = 2 * HALF
        cam = bpy.data.objects.new("cam", cam_data)
        sc.collection.objects.link(cam)
        cam.location = (0, -12, 0)
        cam.rotation_euler = (math.radians(90), 0, 0)
        cam_data.clip_end = 100
        sc.camera = cam
        return sc

    def sun(direction, energy, color=(1, 1, 1), angle=4.0):
        d = Vector(direction).normalized()
        ld = bpy.data.lights.new("sun", 'SUN')
        ld.energy = energy
        ld.color = color
        ld.angle = math.radians(angle)
        o = bpy.data.objects.new("sun", ld)
        bpy.context.scene.collection.objects.link(o)
        o.location = d * 10
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
        return o

    def lights(kind):
        if kind == "I":
            sun(KEY_DIR, 4.2, (1.0, 0.98, 0.95))
            sun(RIM_DIR, 5.0, (0.55, 0.72, 1.0))
            sun((0.5, -1.0, -0.8), 0.35, (0.75, 0.8, 1.0))
        else:
            sun(KEY_DIR, 7.4, (1.0, 0.965, 0.915))          # 행성과 같은 키(따뜻한 흰빛) — 햇빛 면이 중간 밝기 배경보다 확실히 밝게
            sun(RIM_DIR, 7.0, (0.52, 0.68, 1.0))             # 행성과 같은 청색 림 방향 — 어두운 쪽 가장자리를 또렷이(가독성)
            sun((0.55, -1.0, -0.75), 0.18, (0.62, 0.66, 0.78))  # 약한 반사광(그늘 면이 완전 검정은 아니게)

    def rand_dir(rng):
        v = rng.normal(size=3)
        return v / np.linalg.norm(v)

    def rock_mesh(name, spec):
        rng = np.random.default_rng(spec["seed"])
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=spec.get("sub", 7), radius=1.0)
        o = bpy.context.object
        o.name = name
        me = o.data
        nv = len(me.vertices)
        co = np.empty(nv * 3, np.float32)
        me.vertices.foreach_get("co", co)
        n = co.reshape(-1, 3).astype(np.float64)
        n /= np.linalg.norm(n, axis=1)[:, None]
        h = np.zeros(nv)
        # ① 큰 덩어리 — 넓은 가우시안 융기·함몰
        for _ in range(spec["lumps"]):
            d = rand_dir(rng)
            w = rng.uniform(0.45, 1.0)
            a = rng.uniform(-0.16, 0.20)
            h += a * np.exp(-(1 - n @ d) / (0.5 * w * w))
        # 쌍엽(67P·이토카와 같은 접촉쌍성) — 한 축 가운데를 조인다
        if spec.get("bilobe"):
            ax = rand_dir(rng)
            c = n @ ax
            h -= spec["bilobe"] * np.exp(-(c * c) / 0.05) * 0.55
        # ② 프랙탈 요철
        off = Vector(rng.uniform(-50, 50, 3).tolist())
        fr = np.fromiter((noise.fractal(Vector(p) * 1.5 + off, 0.42, 2.2, 4, noise_basis='PERLIN_ORIGINAL') for p in n), float, nv)
        h += spec["noise"] * 0.7 * fr
        if spec.get("facet"):
            # 깨진 면 — 충돌 파편처럼 평면으로 깎인 모서리 (얼음 조각은 9면, 암석 파편은 5~6면)
            nf = 9 if spec["facet"] is True else int(spec["facet"])
            for _ in range(nf):
                d = rand_dir(rng)
                cut = rng.uniform(0.55, 0.8) if spec["facet"] is True else rng.uniform(0.80, 0.92)
                r_now = 1 + h
                proj = (n @ d) * r_now
                over = proj > cut
                h[over] -= (proj[over] - cut) / np.maximum(n[over] @ d, 0.2)
        # ③ 크레이터 — 둥근 사발 + 솟은 테두리 + 옅은 방출물. (큰, 중간, 작은) 개수
        big, mid, small = spec["craters"]
        cr = [(rng.uniform(0.34, 0.55)) for _ in range(big)] + [rng.uniform(0.15, 0.30) for _ in range(mid)] + \
             [rng.uniform(0.05, 0.13) for _ in range(small)]
        for rho in cr:
            d = rand_dir(rng)
            t = np.arccos(np.clip(n @ d, -1, 1)) / rho
            depth = rho * (rng.uniform(0.16, 0.26) if rho > 0.33 else rng.uniform(0.30, 0.44))
            rim = rho * rng.uniform(0.08, 0.13)
            bowl = np.where(t < 1, depth * (np.minimum(t, 1) ** 2.2 - 1), 0.0)
            ridge = rim * np.exp(-((t - 1.0) / 0.16) ** 2)
            ejecta = np.where(t > 1, rim * 0.35 * np.exp(-(t - 1) / 0.6), 0.0)
            h += bowl + ridge + ejecta
        # ④ 바위 알갱이 — 작고 날카로운 융기
        for _ in range(int(40 * spec.get("boulders", 1.0))):
            d = rand_dir(rng)
            rho = rng.uniform(0.018, 0.045)
            h += rho * 0.9 * np.exp(-(1 - n @ d) / (0.5 * rho * rho))
        ax = np.array(spec["axes"])
        pts = n * (1 + h)[:, None] * ax[None, :]
        # 최대 돌출 1.16 으로 정규화 — 어떤 자전 각에서도 칸(반폭 HALF) 안에 든다. 보이는 크기는 post 가 k 로 실측
        pts *= 1.16 / np.linalg.norm(pts, axis=1).max()
        me.vertices.foreach_set("co", pts.astype(np.float32).ravel())
        me.update()
        for p in me.polygons:
            p.use_smooth = True
        return o

    def rock_mat(o, kind, seed, crack=False):
        K = KINDS[kind]
        m = bpy.data.materials.new("rk_" + kind)
        m.use_nodes = True
        nt = m.node_tree
        N = nt.nodes
        L = nt.links
        bs = N["Principled BSDF"]
        tc = N.new("ShaderNodeTexCoord")
        mp = N.new("ShaderNodeMapping")
        mp.inputs["Location"].default_value = (seed * 0.37 % 7, seed * 0.71 % 5, seed * 0.13 % 3)
        L.new(tc.outputs["Object"], mp.inputs["Vector"])
        # 알베도: 큰 얼룩(암상 차이) × 중간 얼룩 + 검은 반점
        n1 = N.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 1.6; n1.inputs["Detail"].default_value = 6; n1.inputs["Roughness"].default_value = 0.55
        n2 = N.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 7.5; n2.inputs["Detail"].default_value = 8; n2.inputs["Roughness"].default_value = 0.6
        L.new(mp.outputs["Vector"], n1.inputs["Vector"]); L.new(mp.outputs["Vector"], n2.inputs["Vector"])
        mx = N.new("ShaderNodeMath"); mx.operation = 'MULTIPLY_ADD'
        L.new(n1.outputs["Fac"], mx.inputs[0]); mx.inputs[1].default_value = 0.75
        mx2 = N.new("ShaderNodeMath"); mx2.operation = 'MULTIPLY'
        L.new(n2.outputs["Fac"], mx2.inputs[0]); mx2.inputs[1].default_value = 0.5
        L.new(mx2.outputs[0], mx.inputs[2])
        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.42
        ramp.color_ramp.elements[1].position = 0.86
        ramp.color_ramp.elements[0].color = K["c0"] + (1,)
        ramp.color_ramp.elements[1].color = K["c1"] + (1,)
        L.new(mx.outputs[0], ramp.inputs["Fac"])
        # 검은 반점(탄소질 포획암)·밝은 반점(규산염 알갱이)
        vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 22.0
        vo.feature = 'F1'
        L.new(mp.outputs["Vector"], vo.inputs["Vector"])
        spk = N.new("ShaderNodeValToRGB")
        spk.color_ramp.elements[0].position = 0.0; spk.color_ramp.elements[0].color = (0.55, 0.55, 0.55, 1)
        spk.color_ramp.elements[1].position = 0.10; spk.color_ramp.elements[1].color = (1, 1, 1, 1)
        L.new(vo.outputs["Distance"], spk.inputs["Fac"])
        mul = N.new("ShaderNodeMixRGB"); mul.blend_type = 'MULTIPLY'; mul.inputs["Fac"].default_value = 1.0
        L.new(ramp.outputs["Color"], mul.inputs[1]); L.new(spk.outputs["Color"], mul.inputs[2])
        L.new(mul.outputs["Color"], bs.inputs["Base Color"])
        bs.inputs["Roughness"].default_value = K["rough"]
        bs.inputs["Metallic"].default_value = K["metal"]
        bs.inputs["Specular IOR Level"].default_value = K["spec"]
        if kind == "I":
            bs.inputs["Coat Weight"].default_value = 0.35
            bs.inputs["Coat Roughness"].default_value = 0.12
            bs.inputs["Subsurface Weight"].default_value = 0.18
            bs.inputs["Subsurface Radius"].default_value = (0.3, 0.5, 0.9)
            bs.inputs["Subsurface Scale"].default_value = 0.08
        # 레골리스 알갱이 — 고주파 범프 2겹 (쌓인 먼지 + 자갈)
        b1 = N.new("ShaderNodeTexNoise"); b1.inputs["Scale"].default_value = 48.0; b1.inputs["Detail"].default_value = 10; b1.inputs["Roughness"].default_value = 0.62
        b2 = N.new("ShaderNodeTexVoronoi"); b2.inputs["Scale"].default_value = 16.0; b2.feature = 'SMOOTH_F1'
        L.new(mp.outputs["Vector"], b1.inputs["Vector"]); L.new(mp.outputs["Vector"], b2.inputs["Vector"])
        bp1 = N.new("ShaderNodeBump"); bp1.inputs["Strength"].default_value = (0.42 if kind != "I" else 0.12) * K.get("bump", 1.0); bp1.inputs["Distance"].default_value = 0.02
        bp2 = N.new("ShaderNodeBump"); bp2.inputs["Strength"].default_value = (0.30 if kind != "I" else 0.06) * K.get("bump", 1.0); bp2.inputs["Distance"].default_value = 0.03
        L.new(b1.outputs["Fac"], bp1.inputs["Height"])
        L.new(b2.outputs["Distance"], bp2.inputs["Height"])
        L.new(bp1.outputs["Normal"], bp2.inputs["Normal"])
        L.new(bp2.outputs["Normal"], bs.inputs["Normal"])
        if not crack and kind != "I":
            # 가장자리 림 — 청색 림라이트(RIM_DIR, 행성과 같은 방향)가 닿는 쪽 실루엣 가장자리만 얇게 빛난다.
            # 거친 레골리스는 역광을 거의 못 받아 림이 사라진다 → 시선 스침각(Facing^4) × max(0, N·림방향) 발광으로 보탠다.
            # 스티커 외곽선이 아니라 '광원 쪽 가장자리의 빛' — 어두운 배경·중간 밝기 성운 위에서 실루엣을 세운다
            lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
            fp = N.new("ShaderNodeMath"); fp.operation = 'POWER'; fp.inputs[1].default_value = 4.5
            L.new(lw.outputs["Facing"], fp.inputs[0])
            geo = N.new("ShaderNodeNewGeometry")
            dp = N.new("ShaderNodeVectorMath"); dp.operation = 'DOT_PRODUCT'
            rd = Vector(RIM_DIR).normalized()
            dp.inputs[1].default_value = (rd.x, rd.y, rd.z)
            L.new(geo.outputs["Normal"], dp.inputs[0])
            mx0 = N.new("ShaderNodeMath"); mx0.operation = 'MAXIMUM'; mx0.inputs[1].default_value = 0.0
            L.new(dp.outputs["Value"], mx0.inputs[0])
            # 키 반대쪽(그늘) 가장자리에도 옅게 — 어두운 면이 배경에 녹지 않게 (지구조·반사광 느낌)
            dk = N.new("ShaderNodeVectorMath"); dk.operation = 'DOT_PRODUCT'
            kd = Vector(KEY_DIR).normalized()
            dk.inputs[1].default_value = (-kd.x, -kd.y, -kd.z)
            L.new(geo.outputs["Normal"], dk.inputs[0])
            mk0 = N.new("ShaderNodeMath"); mk0.operation = 'MULTIPLY_ADD'; mk0.inputs[1].default_value = 0.12; mk0.inputs[2].default_value = 0.0
            L.new(dk.outputs["Value"], mk0.inputs[0])
            mk1 = N.new("ShaderNodeMath"); mk1.operation = 'MAXIMUM'; mk1.inputs[1].default_value = 0.0
            L.new(mk0.outputs[0], mk1.inputs[0])
            ad = N.new("ShaderNodeMath"); ad.operation = 'ADD'
            L.new(mx0.outputs[0], ad.inputs[0]); L.new(mk1.outputs[0], ad.inputs[1])
            rim = N.new("ShaderNodeMath"); rim.operation = 'MULTIPLY'
            L.new(fp.outputs[0], rim.inputs[0]); L.new(ad.outputs[0], rim.inputs[1])
            rs = N.new("ShaderNodeMath"); rs.operation = 'MULTIPLY'; rs.inputs[1].default_value = RIM_EMIT
            L.new(rim.outputs[0], rs.inputs[0])
            bs.inputs["Emission Color"].default_value = (0.62, 0.78, 1.0, 1)
            L.new(rs.outputs[0], bs.inputs["Emission Strength"])
        if crack:
            # 달아오른 균열 — Voronoi 경계(F2-F1 가 작은 곳)만 발광. 몸통은 완전 흑체(발광 패스용)
            vc = N.new("ShaderNodeTexVoronoi"); vc.inputs["Scale"].default_value = 1.7; vc.feature = 'DISTANCE_TO_EDGE'
            L.new(mp.outputs["Vector"], vc.inputs["Vector"])
            nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 5.0; nz.inputs["Detail"].default_value = 4
            L.new(mp.outputs["Vector"], nz.inputs["Vector"])
            e1 = N.new("ShaderNodeMapRange")
            e1.inputs["From Min"].default_value = 0.0; e1.inputs["From Max"].default_value = 0.035
            e1.inputs["To Min"].default_value = 1.0; e1.inputs["To Max"].default_value = 0.0
            L.new(vc.outputs["Distance"], e1.inputs["Value"])
            e2 = N.new("ShaderNodeMath"); e2.operation = 'MULTIPLY'
            L.new(e1.outputs["Result"], e2.inputs[0])
            gate = N.new("ShaderNodeMapRange"); gate.inputs["From Min"].default_value = 0.48; gate.inputs["From Max"].default_value = 0.58
            L.new(nz.outputs["Fac"], gate.inputs["Value"]); L.new(gate.outputs["Result"], e2.inputs[1])
            col = N.new("ShaderNodeValToRGB")
            col.color_ramp.elements[0].position = 0.0; col.color_ramp.elements[0].color = (0, 0, 0, 1)
            col.color_ramp.elements[1].position = 1.0; col.color_ramp.elements[1].color = (1.0, 0.55, 0.16, 1)
            mid_el = col.color_ramp.elements.new(0.55); mid_el.color = (0.9, 0.22, 0.04, 1)
            L.new(e2.outputs[0], col.inputs["Fac"])
            L.new(col.outputs["Color"], bs.inputs["Emission Color"])
            bs.inputs["Emission Strength"].default_value = 6.0
            bs.inputs["Base Color"].default_value = (0, 0, 0, 1)
            try:
                L.remove(bs.inputs["Base Color"].links[0])
            except Exception:
                pass
            bs.inputs["Specular IOR Level"].default_value = 0.0
            bs.inputs["Roughness"].default_value = 1.0
        o.data.materials.append(m)
        return m

    def spin_quats(spec_seed, n, spin_deg, tilt_deg=18.0):
        """시선(+Y, 카메라에서 멀어지는 쪽) 기준 tilt 만큼 기운 축으로 k·step 회전.
        +Y 축 +각 = 화면 시계 방향 = 캔버스 rotate(+) 와 같은 방향."""
        rng = np.random.default_rng(spec_seed + 999)
        q0 = Quaternion(Vector(rand_dir(rng).tolist()), rng.uniform(0, 2 * math.pi))
        az = rng.uniform(0, 2 * math.pi)
        t = math.radians(tilt_deg)
        axis = Vector((math.sin(t) * math.cos(az), math.cos(t), math.sin(t) * math.sin(az))).normalized()
        out = []
        for k in range(n):
            ang = math.radians(spin_deg) * k / n
            out.append(Quaternion(axis, ang) @ q0)
        return out

    def render_rock_set(set_name, only=None):
        S = SETS[set_name]
        res = int(round(S["cell"] * S["ss"]))
        out_dir = os.path.join(REN_DIR, set_name)
        os.makedirs(out_dir, exist_ok=True)
        for name in S["rows"]:
            if only and name not in only:
                continue
            spec = ROCKS[name]
            passes = [("", False)]
            if set_name == "bld" and name == "b0":
                passes.append(("_hot", True))
            for suffix, crack in passes:
                sc = reset(res)
                lights(spec["kind"])
                o = rock_mesh(name, spec)
                rock_mat(o, spec["kind"], spec["seed"], crack=crack)
                if crack:
                    # 발광 패스 — 조명 끔(균열 빛만), 월드 0
                    for ob in list(sc.objects):
                        if ob.type == 'LIGHT':
                            ob.data.energy = 0.0
                    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
                o.rotation_mode = 'QUATERNION'
                qs = spin_quats(spec["seed"], S["n"], S["spin"]) if S["n"] > 1 else [Quaternion(Vector(rand_dir(np.random.default_rng(spec["seed"] + 5)).tolist()), 1.1)]
                for k, q in enumerate(qs):
                    o.rotation_quaternion = q
                    sc.render.filepath = os.path.join(out_dir, "%s%s_%02d.png" % (name, suffix, k))
                    bpy.ops.render.render(write_still=True)
                print("렌더", set_name, name + suffix, len(qs), "프레임", flush=True)

    # ─── 기뢰 — 검은 강철 구 + 6방향 뿔(화면 평면) + 붉은 신호등 ───
    def render_mine():
        S = SETS["mine"]
        res = int(round(S["cell"] * S["ss"]))
        out_dir = os.path.join(REN_DIR, "mine")
        os.makedirs(out_dir, exist_ok=True)
        sc = reset(res)
        sun(KEY_DIR, 5.0, (1.0, 0.965, 0.915))
        sun(RIM_DIR, 3.0, (0.52, 0.68, 1.0))
        sun((0.55, -1.0, -0.75), 0.4, (0.62, 0.66, 0.78))
        sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.12
        # 몸통 반지름 = 13/19 (충돌 MINE_R 13, 뿔 끝 19 — 게임 절차 그림과 같은 비)
        R = 0.66 * HALF / 0.97 * 0.97
        body_r = R * 13.0 / 19.0
        bpy.ops.mesh.primitive_uv_sphere_add(radius=body_r, segments=96, ring_count=48)
        body = bpy.context.object
        for p in body.data.polygons:
            p.use_smooth = True
        steel = bpy.data.materials.new("steel"); steel.use_nodes = True
        b = steel.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.13, 0.028, 0.032, 1)
        b.inputs["Metallic"].default_value = 0.5
        b.inputs["Roughness"].default_value = 0.38
        # 판 이음새 범프
        N = steel.node_tree.nodes; Lk = steel.node_tree.links
        tc = N.new("ShaderNodeTexCoord")
        wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 3.0; wv.wave_type = 'RINGS'; wv.inputs["Distortion"].default_value = 0.0
        Lk.new(tc.outputs["Object"], wv.inputs["Vector"])
        nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40; nz.inputs["Detail"].default_value = 8
        Lk.new(tc.outputs["Object"], nz.inputs["Vector"])
        bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25
        Lk.new(nz.outputs["Fac"], bp.inputs["Height"])
        Lk.new(bp.outputs["Normal"], b.inputs["Normal"])
        body.data.materials.append(steel)
        spike_mat = bpy.data.materials.new("spike"); spike_mat.use_nodes = True
        sb = spike_mat.node_tree.nodes["Principled BSDF"]
        sb.inputs["Base Color"].default_value = (0.30, 0.30, 0.32, 1)
        sb.inputs["Metallic"].default_value = 0.8
        sb.inputs["Roughness"].default_value = 0.3
        tip_mat = bpy.data.materials.new("tip"); tip_mat.use_nodes = True
        tb = tip_mat.node_tree.nodes["Principled BSDF"]
        tb.inputs["Base Color"].default_value = (0.9, 0.1, 0.08, 1)
        tb.inputs["Emission Color"].default_value = (1.0, 0.16, 0.10, 1)
        tb.inputs["Emission Strength"].default_value = 2.6
        spikes = []
        for i in range(6):
            a = i / 6 * 2 * math.pi
            d = Vector((math.cos(a), 0, math.sin(a)))
            L = R - body_r * 0.8
            bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=body_r * 0.26, radius2=body_r * 0.07, depth=L)
            s = bpy.context.object
            s.location = d * (body_r * 0.8 + L / 2)
            s.rotation_mode = 'QUATERNION'
            s.rotation_quaternion = d.to_track_quat('Z', 'Y')
            for p in s.data.polygons:
                p.use_smooth = True
            s.data.materials.append(spike_mat)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=body_r * 0.11, segments=24, ring_count=12)
            t = bpy.context.object
            t.location = d * (R - body_r * 0.04)
            t.data.materials.append(tip_mat)
            spikes += [s, t]
            # 뿔 뿌리 링(볼트 판)
            bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=body_r * 0.33, depth=body_r * 0.12)
            ring = bpy.context.object
            ring.location = d * (body_r * 0.93)
            ring.rotation_mode = 'QUATERNION'
            ring.rotation_quaternion = d.to_track_quat('Z', 'Y')
            ring.data.materials.append(spike_mat)
            spikes.append(ring)
        # 앞면 붉은 눈(센서) — 발광
        bpy.ops.mesh.primitive_uv_sphere_add(radius=body_r * 0.28, segments=32, ring_count=16)
        eye = bpy.context.object
        eye.location = (0, -body_r * 0.97, 0)
        eye.scale = (1, 0.45, 1)
        eye.data.materials.append(tip_mat)
        bpy.ops.mesh.primitive_torus_add(major_radius=body_r * 0.34, minor_radius=body_r * 0.06)
        bez = bpy.context.object
        bez.location = (0, -body_r * 0.95, 0)
        bez.rotation_euler = (math.radians(90), 0, 0)
        bez.data.materials.append(spike_mat)
        # 전체를 한 부모로 — 화면 평면(+Y 축) 회전
        bpy.ops.object.empty_add(location=(0, 0, 0))
        root = bpy.context.object
        for ob in [body, eye, bez] + spikes:
            ob.parent = root
        root.rotation_mode = 'XYZ'
        for k in range(S["n"]):
            root.rotation_euler = (0, math.radians(S["spin"] * k / S["n"]), 0)
            sc.render.filepath = os.path.join(out_dir, "mine_%02d.png" % k)
            bpy.ops.render.render(write_still=True)
        print("렌더 mine", S["n"], flush=True)

    def main_blender(args):
        want = args or ["met", "bld", "ice", "mine", "nuc"]
        only = [a for a in want if a in ROCKS and a not in SETS]
        sets = [a for a in want if a in SETS]
        for s in sets:                       # 세트 이름 = 그 세트 전부
            if s == "mine":
                render_mine()
            else:
                render_rock_set(s, None)
        for s, S in SETS.items():             # 돌 이름 = 그 돌만
            rows = [r for r in only if r in S["rows"]]
            if rows and s not in sets:
                render_rock_set(s, rows)

    argv = sys.argv
    main_blender(argv[argv.index("--") + 1:] if "--" in argv else [])


# ══════════════════════════════ 굽기(일반 파이썬) ══════════════════════════════
def _sp():
    sys.path.insert(0, HERE)
    import spacez_planets as sp
    return sp


def _np():
    import numpy as np
    from PIL import Image, ImageFilter, ImageDraw
    return np, Image, ImageFilter, ImageDraw


def sharpen(a, amount=0.45, sigma=0.7):
    """축소 뒤 약한 언샤프 — 캔버스 bilinear 재표본(회전 잔여각·소수 좌표)이 먹는 0.5px 을 미리 돌려준다.
    프리멀티플라이 색에 걸고 알파(실루엣)는 건드리지 않는다 — 가장자리 검은 테 방지."""
    np = _np()[0]
    from scipy.ndimage import gaussian_filter
    A = a[..., 3:4]
    pm = a[..., :3] * A
    bl = np.dstack([gaussian_filter(pm[..., c], sigma) for c in range(3)])
    pm2 = np.clip(pm + (pm - bl) * amount, 0, None)
    pm2 = np.minimum(pm2, A)
    out = a.copy()
    out[..., :3] = np.where(A > 1e-4, pm2 / np.maximum(A, 1e-4), 0)
    return out


HALO_A = float(os.environ.get("RK_HALO_A", "0.92"))
HALO_PX = float(os.environ.get("RK_HALO_PX", "1.6"))
GAIN = float(os.environ.get("RK_GAIN", "1.0"))
HALO_W = int(os.environ.get("RK_HALO_W", "5"))     # MaxFilter 크기 (3 = 1px, 5 = 2px 을 꽉 채워 키움)


def edge_shade(a, px=None, alpha=None):
    """실루엣 바깥 옅은 그늘 — 밝은 배경(지구 림·베텔게우스·오리온) 위에서 경계를 세운다.
    스티커 선이 아니라 가장자리에서 바깥으로 빠르게 사라지는 부드러운 어둠(1~1.5px)."""
    np, Image, ImageFilter, _ = _np()
    px = HALO_PX if px is None else px
    alpha = HALO_A if alpha is None else alpha
    A = a[..., 3]
    im = Image.fromarray((A * 255).astype(np.uint8))
    # 1px 를 꽉 채워 키운 뒤(MaxFilter 3) 바깥만 부드럽게 — 가장자리 바로 밖은 거의 불투명한 어둠, 1.5px 너머는 0
    grown = np.asarray(im.filter(ImageFilter.MaxFilter(HALO_W)).filter(ImageFilter.GaussianBlur(px * 0.45)), np.float32) / 255
    halo = np.clip(grown * 1.7, 0, 1) * alpha
    # 합성: 돌(스트레이트) over 검은 그늘
    ao = A + halo * (1 - A)
    rgb = np.where(ao[..., None] > 1e-4, a[..., :3] * (A / np.maximum(ao, 1e-4))[..., None], 0)
    tint = np.array([0.02, 0.025, 0.04], np.float32)
    rgb = rgb + tint * ((halo * (1 - A)) / np.maximum(ao, 1e-4))[..., None]
    return np.dstack([np.clip(rgb, 0, 1), ao])


def load_frames(set_name, name, n, suffix=""):
    sp = _sp()
    out = []
    for k in range(n):
        p = os.path.join(REN_DIR, set_name, "%s%s_%02d.png" % (name, suffix, k))
        out.append(sp.load_rgba(p))
    return out


def cell_from(a, cell, pad=3, shade=True, sharp=0.45):
    """렌더(ss 배) → 칸. 가장자리 pad px 는 투명(아틀라스 번짐 방지)."""
    sp = _sp()
    np = _np()[0]
    c = sp.resize_premul(a, cell, cell)
    if GAIN != 1.0 and shade:
        # 노출 — 선형 광량 배율(= 태양 세기). 햇빛 받는 면이 중간 밝기 배경(성운·지구 림)보다 3배 밝아야 읽힌다
        lin = np.where(c[..., :3] <= 0.04045, c[..., :3] / 12.92, ((c[..., :3] + 0.055) / 1.055) ** 2.4) * GAIN
        c[..., :3] = np.clip(np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.maximum(lin, 0) ** (1 / 2.4) - 0.055), 0, 1)
    if sharp:
        c = sharpen(c, sharp)
    kb = eq_k(c)                 # 보이는 크기 = 그늘을 붙이기 전 몸통
    if shade:
        c = edge_shade(c)
    cell_from.k = kb
    c[:pad, :, 3] = 0; c[-pad:, :, 3] = 0; c[:, :pad, 3] = 0; c[:, -pad:, 3] = 0
    return sp.clean_alpha(c)


def eq_k(c):
    np = _np()[0]
    m = c[..., 3] > 0.5
    return math.sqrt(m.sum() / math.pi) / (c.shape[0] / 2)


def centroid(c):
    np = _np()[0]
    m = c[..., 3] > 0.5
    ys, xs = np.nonzero(m)
    return float(xs.mean() - (c.shape[1] - 1) / 2), float(ys.mean() - (c.shape[0] - 1) / 2)


def atlas(rows):
    """rows = [[cell, ...], ...] → 한 장."""
    np = _np()[0]
    h = len(rows)
    w = max(len(r) for r in rows)
    ch, cw = rows[0][0].shape[:2]
    A = np.zeros((h * ch, w * cw, 4), np.float32)
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            A[j * ch:(j + 1) * ch, i * cw:(i + 1) * cw] = c
    return A


def half(a):
    sp = _sp()
    return sp.resize_premul(a, a.shape[1] // 2, a.shape[0] // 2)


def save(a, name, kb, report, q0=82, aq=60, **meta):
    sp = _sp()
    os.makedirs(PUB_DIR, exist_ok=True)
    p = os.path.join(PUB_DIR, name + ".webp")
    q, sz = sp.save_webp(a, p, kb, q0=q0, qmin=50, qmax=92, aq=aq)
    pl = os.path.join(PUB_DIR, name + "_lo.webp")
    lo = sharpen(half(a), 0.25)
    ql, szl = sp.save_webp(lo, pl, max(2, kb * 0.4), q0=q0, qmin=45, qmax=90, aq=aq)
    report[name] = dict(w=a.shape[1], h=a.shape[0], q=q, kb=round(sz / 1024, 1), lo_kb=round(szl / 1024, 1), **meta)
    print("  %-10s %dx%d q%d %.1fKB  _lo %.1fKB" % (name, a.shape[1], a.shape[0], q, sz / 1024, szl / 1024), flush=True)


# ─── 혜성 코마·꼬리 (numpy — 빛이라 렌더가 필요 없다) ───
def comet_head(nuc_cell, size=128):
    """혜성 머리: 가산 코마(바깥) + 소스오버 핵. 두 장을 가로로 붙인다 [코마 | 핵].
    코마: 반지름(칸 반폭=1) 기준 r<0.22 밝은 응결, 0.36(=충돌 16/44) 에서 절반, 0.55 에서 0.08 — 위험 원이 또렷이 읽히게
    가장자리가 가파르고, 바깥은 옅은 녹청 헤일로(C2·CN 발광)."""
    np = _np()[0]
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    c = (size - 1) / 2
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (size / 2)
    core = np.exp(-(r / 0.16) ** 2)
    inner = 1 / (1 + np.exp((r - 0.34) / 0.028))          # 가파른 경계(위험 반지름)
    halo = np.exp(-r / 0.19) * 0.55
    L = np.clip(0.78 * inner + 0.8 * core + halo * 0.5, 0, 1.4)
    col = np.dstack([0.78 + 0 * r, 0.95 + 0 * r, 1.0 + 0 * r])
    # 바깥쪽은 청록(C2 스완 밴드) 기미
    g = np.clip((r - 0.25) / 0.4, 0, 1)[..., None]
    col = col * (1 - g) + np.array([0.45, 1.0, 0.85])[None, None, :] * g
    coma = np.dstack([np.clip(col * np.minimum(L, 1)[..., None], 0, 1), np.clip(L, 0, 1)])
    coma[..., 3] = np.clip(L, 0, 1)
    coma[r > 0.98] = 0
    # 핵은 제 칸(128) 그대로 — 게임이 코마와 따로, 작게(선명하게) 그린다
    return coma, nuc_cell


def comet_tails(W=512, H=96):
    """꼬리 한 장 [먼지 꼬리 위 절반 | 이온 꼬리 아래 절반]. 머리는 왼쪽(x=0), 꼬리는 +x 로 뻗는다.
    먼지 꼬리: 넓게 퍼지며 한쪽(+y)으로 휘는 누런 흰빛 부채, 줄무늬(싱크로네) 약간.
    이온 꼬리: 곧고 가늘고 푸른 광선, 가닥(스트리머) 여러 줄. 둘 다 가산 합성용(알파=밝기)."""
    np = _np()[0]
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u = xx / (W - 1)                      # 0 머리 → 1 끝
    v = (yy - (H - 1) / 2) / ((H - 1) / 2)  # -1..1
    # 먼지 꼬리 — 중심선이 +v 쪽으로 u² 만큼 휜다, 폭은 u 에 따라 넓어진다
    cen = 0.42 * u ** 1.5
    wid = 0.10 + 0.50 * u ** 0.8
    d = (v - cen) / wid
    dust = 1.25 * np.exp(-d * d * 1.3) * (1 - u) ** 1.1 * np.clip(u / 0.02, 0, 1)
    # 싱크로네 줄무늬 — 머리에서 부채꼴로 퍼지는 옅은 결
    ang = np.arctan2(v - 0.0, u + 0.02)
    streak = 0.9 + 0.1 * np.sin(ang * 30 + rng.uniform(0, 6))
    dust *= streak
    dust_col = np.dstack([1.0 + 0 * u, 0.93 + 0 * u, 0.78 + 0 * u])
    # 이온 꼬리 — 곧게, 가늘게, 여러 가닥
    ion = np.zeros_like(u)
    for k in range(7):
        off = rng.normal(0, 0.05) * (0.3 + u)
        w = rng.uniform(0.018, 0.04) * (0.6 + 1.2 * u)
        amp = rng.uniform(0.35, 1.0)
        ion += amp * np.exp(-((v - off) / w) ** 2)
    ion = np.clip(ion / 1.3, 0, 1) * (1 - u) ** 0.8 * np.clip(u / 0.02, 0, 1)
    ion_col = np.dstack([0.45 + 0 * u, 0.70 + 0 * u, 1.0 + 0 * u])
    top = np.dstack([dust_col * np.clip(dust, 0, 1)[..., None], np.clip(dust, 0, 1)])
    bot = np.dstack([ion_col * np.clip(ion, 0, 1)[..., None], np.clip(ion, 0, 1)])
    return np.concatenate([top, bot], axis=0)


def post():
    sp = _sp()
    np, Image, _, ImageDraw = _np()
    report = {}
    man = {}
    # ① 운석 아틀라스
    S = SETS["met"]
    rows, ks, cents = [], [], []
    for name in S["rows"]:
        fr, kk = [], []
        for a in load_frames("met", name, S["n"]):
            fr.append(cell_from(a, S["cell"])); kk.append(cell_from.k)
        rows.append(fr)
        ks.append(round(sum(kk) / len(kk), 4))
        cents.append([round(v, 2) for v in np.mean([centroid(c) for c in fr], axis=0)])
    A = atlas(rows)
    save(A, "rocks_m", 175, report, cell=S["cell"], n=S["n"], rows=len(rows), k=ks, cent=cents)
    man["rocks_m"] = report["rocks_m"]
    sheets = {"met": A}
    # ② 큰 바위 아틀라스 + 분열암 균열 발광
    S = SETS["bld"]
    rows, ks = [], []
    for name in S["rows"]:
        fr, kk = [], []
        for a in load_frames("bld", name, S["n"]):
            fr.append(cell_from(a, S["cell"])); kk.append(cell_from.k)
        rows.append(fr)
        ks.append(round(sum(kk) / len(kk), 4))
    A = atlas(rows)
    save(A, "rocks_b", 110, report, cell=S["cell"], n=S["n"], rows=len(rows), k=ks)
    sheets["bld"] = A
    hot = []
    for a in load_frames("bld", "b0", S["n"], "_hot"):
        c = sp.resize_premul(a, S["cell"], S["cell"])
        # 발광 패스: 색 = 빛, 알파 = 밝기(가산 합성)
        lum = np.clip(c[..., :3].max(axis=2) * c[..., 3], 0, 1)
        # 용암빛으로 — 가장 밝은 심은 노랑, 가장자리는 주홍 (가산이라 알파 = 밝기, 1.8배로 굵고 또렷하게)
        a_ = np.clip(lum * 1.8, 0, 1)
        t_ = np.clip(lum * 1.4, 0, 1)[..., None]
        col = np.array([1.0, 0.36, 0.08], np.float32) * (1 - t_) + np.array([1.0, 0.86, 0.52], np.float32) * t_
        c = np.dstack([col, a_])
        c[:3, :, 3] = 0; c[-3:, :, 3] = 0; c[:, :3, 3] = 0; c[:, -3:, 3] = 0
        hot.append(np.clip(c, 0, 1))
    H = atlas([hot])
    save(H, "rocks_bh", 30, report, cell=S["cell"], n=S["n"], rows=1)
    sheets["bh"] = H
    # ③ 얼음 조각
    S = SETS["ice"]
    fr, kk = [], []
    for name in S["rows"]:
        fr.append(cell_from(load_frames("ice", name, 1)[0], S["cell"])); kk.append(round(cell_from.k, 4))
    A = atlas([fr])
    save(A, "rk_ice", 24, report, cell=S["cell"], n=len(fr), rows=1, k=kk)
    sheets["ice"] = A
    # ④ 기뢰
    S = SETS["mine"]
    fr = [cell_from(a, S["cell"], shade=True) for a in load_frames("mine", "mine", S["n"])]
    A = atlas([fr])
    def tip_k(c):
        m = c[..., 3] > 0.5
        ys, xs = np.nonzero(m)
        h = (c.shape[0] - 1) / 2
        return float(np.sqrt((xs - h) ** 2 + (ys - h) ** 2).max() / (c.shape[0] / 2))
    save(A, "rk_mine", 40, report, cell=S["cell"], n=S["n"], rows=1, spin=S["spin"],
         tip=round(sum(tip_k(c) for c in fr) / len(fr), 4), k_body=round(sum(eq_k(c) for c in fr) / len(fr), 4))
    sheets["mine"] = A
    # ⑤ 혜성 머리(코마 | 핵) + 꼬리(먼지 | 이온)
    nuc = cell_from(load_frames("nuc", "nuc", 1)[0], SETS["nuc"]["cell"], sharp=0.3)
    coma, nucl = comet_head(nuc, 128)
    A = np.concatenate([coma, nucl], axis=1)
    save(A, "rk_comet", 20, report, cell=128, k_nuc=round(eq_k(nuc), 4),
         note="[가산 코마 | 소스오버 핵], 위험 반지름 = 코마 칸 반폭 × 0.36, 핵 k = 등가 반지름 비")
    T = comet_tails(512, 96)
    save(T, "rk_ctail", 36, report, note="위 절반 먼지 꼬리(휨), 아래 절반 이온 꼬리. 머리 = x0, 가산")
    sheets["comet"] = A
    sheets["tail"] = T
    total = sum(v["kb"] for v in report.values())
    total_lo = sum(v["lo_kb"] for v in report.values())
    print("합계 %.1fKB  (_lo %.1fKB)" % (total, total_lo))
    report["_total_kb"] = round(total, 1)
    report["_total_lo_kb"] = round(total_lo, 1)
    os.makedirs(REN_DIR, exist_ok=True)
    json.dump(report, open(os.path.join(REN_DIR, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 접사 시트 — 어두운/밝은 배경 위 3배
    for nm, a in sheets.items():
        h, w = a.shape[:2]
        sc = 3 if w * 3 <= 4800 else max(1, 4800 // w)
        big = sp.resize_premul(a, w * sc, h * sc) if sc > 1 else a
        for bgname, bg in (("dark", (0.02, 0.025, 0.05)), ("bright", (0.78, 0.62, 0.52))):
            base = np.zeros_like(big)
            base[..., :3] = bg; base[..., 3] = 1
            out = sp.over(base, big, 0, 0) if hasattr(sp, "over") else base
            sp.to_img(out).convert("RGB").save(os.path.join(REN_DIR, "sheet_%s_%s.png" % (nm, bgname)))
    return report


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
    if mode in ("render", "all"):
        run_blender(rest)
    if mode in ("post", "all"):
        post()
