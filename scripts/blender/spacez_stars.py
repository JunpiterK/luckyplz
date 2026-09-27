# -*- coding: utf-8 -*-
"""Space-Z v5 항성 히어로 — Blender Cycles 발광 구 + numpy 후처리 (2026-09-28, P7).

P6 의 spacez_planets.py 와 겹치지 않게 따로 둔 파일(같은 규칙·같은 헬퍼 재사용).
  betel_limb  1080x720  베텔게우스 — 초거성의 '불의 벽'. 거대한 구의 위쪽 호만 판에 들어온다.
                        대류 세포 6~10개(실제 베텔게우스는 표면에 세포가 몇 개뿐인 별), 강한 주연 감광,
                        림 바깥 채층 광 + 비대칭 먼지 껍질(VLT 관측의 한쪽 깃털)
  proxima     384       프록시마 센타우리 — 적색왜성 원반 + 흑점·백반 + 림의 플레어 고리
  proxima_b   256       프록시마 b — 붉은 별빛을 옆뒤에서 받는 암석 행성 초승달(얼음 극관)
  star_sirius 384       시리우스 A — 점광원이라 원반이 분해되지 않는다 → Blender 없이 numpy 로 청백 코어 +
                        8방향 회절 스파이크를 굽는다. 동반성 B 는 런타임 SZ_GLOW 작은 점(여기 굽지 않음)

규칙 (메모 planet_art_pipeline — 되돌리기 금지)
  - 항성만 view_transform='Standard', look='None', 발광 1.35 (AgX 는 강한 발광을 분홍·흰색으로 틀고,
    1.35 를 넘기면 R·G 가 모두 클리핑돼 형광 노랑이 된다)
  - 행성(proxima_b)은 AgX High Contrast + exposure 0.18, roughness ≥ 0.9, Specular IOR 0.06
  - 얇은 발광 껍질 금지 — 채층·코로나 광은 굽는 단계(2D)에서 알파 마스크를 블러해 만든다

실행
  python scripts/blender/spacez_stars.py all        # 텍스처 → Blender 렌더 → 굽기
  python scripts/blender/spacez_stars.py tex | render [이름..] | post
  (Blender 쪽: blender.exe -b -P scripts/blender/spacez_stars.py -- [이름..])
중간 파일: scripts/og-assets/spacez_z7/ (텍스처 tex_s7_*.png, 렌더 *.png)
"""
import math
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REN_DIR = os.path.join(ROOT, "scripts", "og-assets", "spacez_z7")
BLENDER = os.environ.get("BLENDER_EXE", r"C:/tools/blender-4.2.5-windows-x64/blender.exe")
os.makedirs(REN_DIR, exist_ok=True)

# 베텔게우스 림 기하 (최종 px) — 구 반지름 1100, 림 꼭대기는 위에서 470px
BETEL_W, BETEL_H, BETEL_R, BETEL_APEX = 1080, 720, 1100.0, 470
PROX_DISK = 0.52        # proxima 판 폭 대비 원반 지름 (플레어 고리·코로나 여백)

try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False


if IN_BLENDER:
    import bpy
    from mathutils import Vector

    def _load_planet_helpers():
        """planets_scene.py 공통 헬퍼만(모듈 끝의 렌더 호출 전까지 잘라) 실행 — P6 와 같은 방식."""
        p = os.path.join(HERE, "planets_scene.py")
        src = open(p, encoding="utf-8").read()
        cut = src.index("def t01_meteor")
        ns = {"__name__": "planets_scene_helpers", "__file__": p}
        exec(compile(src[:cut], p, "exec"), ns)
        ns["DIR"] = REN_DIR
        return ns

    H = _load_planet_helpers()

    def scene(rx, ry, samples=96, star=True):
        H["RES"] = rx
        H["SAMPLES"] = samples
        sc = H["reset_scene"]()
        sc.render.resolution_x = rx
        sc.render.resolution_y = ry
        sc.render.resolution_percentage = 100
        if star:
            sc.view_settings.view_transform = 'Standard'
            sc.view_settings.look = 'None'
            sc.view_settings.exposure = 0.0
        else:
            sc.view_settings.look = 'AgX - High Contrast'
            sc.view_settings.exposure = 0.18
        sc.render.image_settings.color_mode = 'RGBA'
        sc.render.image_settings.color_depth = '8'
        sc.render.filter_size = 1.2
        return sc

    def cam(ortho, x=0.0, z=0.0):
        c = H["add_camera"](ortho=ortho)
        c.location = (x, -12, z)
        c.data.clip_end = 100
        return c

    def sphere(r=1.0, rot=(0, 0, 0), segs=256, rings=128):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=segs, ring_count=rings)
        o = bpy.context.object
        for p in o.data.polygons:
            p.use_smooth = True
        o.rotation_mode = 'XYZ'
        o.rotation_euler = tuple(math.radians(a) for a in rot)
        return o

    def star_mat(o, tex, strength=1.35, limb_u=0.75, limb_p=1.6, name="star"):
        """발광 구 + 주연 감광: 색 = 텍스처 × (1 - u·Facing^p). Facing = 레이어 웨이트(0 정면 → 1 가장자리)."""
        m = H["new_mat"](name)
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type == 'BSDF_PRINCIPLED':
                nt.nodes.remove(n)
        out = nt.nodes["Material Output"]
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(REN_DIR, tex), check_existing=True)
        t.interpolation = 'Cubic'
        lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
        pw = nt.nodes.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = limb_p
        nt.links.new(lw.outputs["Facing"], pw.inputs[0])
        mu = nt.nodes.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = limb_u
        nt.links.new(pw.outputs[0], mu.inputs[0])
        one = nt.nodes.new("ShaderNodeMath"); one.operation = 'SUBTRACT'; one.inputs[0].default_value = 1.0
        nt.links.new(mu.outputs[0], one.inputs[1])
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        sock = lambda coll, nm: [x for x in coll if x.name == nm and x.type == 'RGBA' and x.enabled][0]
        mix.inputs[0].default_value = 1.0
        nt.links.new(t.outputs["Color"], sock(mix.inputs, "A"))
        cv = nt.nodes.new("ShaderNodeCombineColor")
        for i in range(3):
            nt.links.new(one.outputs[0], cv.inputs[i])
        nt.links.new(cv.outputs[0], sock(mix.inputs, "B"))
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = strength
        nt.links.new(sock(mix.outputs, "Result"), em.inputs["Color"])
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        o.data.materials.append(m)
        return m

    def render(name):
        bpy.context.scene.render.filepath = os.path.join(REN_DIR, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("  rendered", name, flush=True)

    def r_betel():
        # 1.5배 슈퍼샘플. 구 반지름 1 = 최종 1100px. 카메라 중심을 구 중심보다 위로 올려 윗호만 담는다
        ss = 1.5
        scene(int(BETEL_W * ss), int(BETEL_H * ss), samples=64)
        ortho = BETEL_W / BETEL_R
        center_y_px = BETEL_APEX + BETEL_R            # 판 위에서 구 중심까지(px)
        cam(ortho, z=(center_y_px - BETEL_H / 2) / BETEL_R)
        o = sphere(1.0, rot=(0, 0, 0), segs=384, rings=192)
        star_mat(o, "tex_s7_betel.png", strength=1.35, limb_u=0.88, limb_p=0.9, name="betel")
        render("betel_limb")

    def r_proxima():
        scene(768, 768, samples=96)
        cam(2.0 / PROX_DISK)
        o = sphere(1.0, rot=(12, 0, 30))
        star_mat(o, "tex_s7_proxima.png", strength=1.35, limb_u=0.70, limb_p=1.5, name="proxima")
        render("proxima")

    def r_proxb():
        scene(512, 512, samples=160, star=False)
        cam(2.0 / 0.90)
        # 붉은 별빛이 오른쪽 뒤에서 — 초승달(약 30% 조명)
        d = Vector((0.92, 0.55, 0.28)).normalized()
        bpy.ops.object.light_add(type='SUN', location=tuple(d * 10))
        l = bpy.context.object
        l.data.energy = 9.5; l.data.color = (1.0, 0.52, 0.32); l.data.angle = math.radians(1.2)
        l.rotation_mode = 'QUATERNION'; l.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
        o = sphere(1.0, rot=(18, 0, 60))
        m = H["textured_planet"](o, "tex_s7_proxb.png", "tex_s7_proxb_h.png", rough=0.95, bump=0.30, name="proxb")
        bs = m.node_tree.nodes["Principled BSDF"]
        bs.inputs["Specular IOR Level"].default_value = 0.06
        render("proxima_b")

    JOBS = {"betel": r_betel, "proxima": r_proxima, "proxb": r_proxb}
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for n in (argv or list(JOBS)):
        print("==", n, flush=True)
        JOBS[n]()
    print("SPACEZ STARS DONE ->", REN_DIR)


# ══════════════════════════════ 일반 파이썬 쪽 ══════════════════════════════
def _sp():
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import spacez_plates as sp
    return sp


def _sphere_xyz(h, w):
    import numpy as np
    lat = (0.5 - (np.arange(h) + 0.5) / h) * np.pi
    lon = ((np.arange(w) + 0.5) / w - 0.5) * 2 * np.pi
    la, lo = np.meshgrid(lat, lon, indexing="ij")
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1).astype(np.float32), la


def _sine_noise(P, n, kmin, kmax, seed, beta=1.0):
    """구면에서 이음매 없는 잡음 — 무작위 방향 평면파의 합(주파수 파워법칙)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    out = np.zeros(P.shape[:2], np.float32)
    for _ in range(n):
        d = rng.normal(size=3); d /= np.linalg.norm(d)
        k = kmin * (kmax / kmin) ** rng.random()
        out += k ** -beta * np.sin((P @ d.astype(np.float32)) * k + rng.uniform(0, 2 * np.pi))
    return out / (out.std() + 1e-8)


def _worley(P, nseed, seed):
    import numpy as np
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    S = rng.normal(size=(nseed, 3)); S /= np.linalg.norm(S, axis=1, keepdims=True)
    d, i = cKDTree(S).query(P.reshape(-1, 3), k=2)
    return d[:, 0].reshape(P.shape[:2]), d[:, 1].reshape(P.shape[:2]), i[:, 0].reshape(P.shape[:2])


def _save_tex(arr, name, mode="RGB"):
    import numpy as np
    from PIL import Image
    Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(REN_DIR, name))


def make_textures():
    import numpy as np
    sp = _sp()
    # 베텔게우스 — 거대 대류 세포(구 전체 120개 → 보이는 캡에 6~10개) + 세포 속 잔 알갱이
    P, la = _sphere_xyz(1024, 2048)
    # 세포 경계를 크게 흔들어(워프) 벌집처럼 반듯하지 않게. 하강류 띠는 넓고 흐릿하게, 세포마다 밝기 차이 크게
    Pw = P + 0.16 * np.stack([_sine_noise(P, 60, 3, 16, 5 + k, beta=1.2) for k in range(3)], -1)
    d1, d2, idx = _worley(Pw, 120, 3)
    lane = sp.sstep(0.0, 0.16, d2 - d1)                 # 0 = 세포 경계(어두운 하강류)
    cellb = np.random.default_rng(4).uniform(0.35, 1.0, 120)[idx]
    center = np.exp(-(d1 / 0.13) ** 2)
    mid = _sine_noise(P, 80, 8, 30, 7, beta=1.0)
    fine = _sine_noise(P, 140, 30, 110, 6, beta=0.5)
    v = (0.28 + 0.40 * lane * cellb + 0.30 * center * cellb) * (1 + 0.14 * mid + 0.08 * fine)
    xs = [0.0, 0.35, 0.6, 0.85, 1.1]
    cs = np.array([(0.22, 0.03, 0.01), (0.62, 0.12, 0.03), (0.92, 0.32, 0.08), (1.0, 0.55, 0.22), (1.0, 0.72, 0.42)])
    col = np.stack([np.interp(v, xs, cs[:, c]) for c in range(3)], -1)
    _save_tex(col, "tex_s7_betel.png")
    # 프록시마 — 잔 쌀알 무늬 + 흑점 4개 + 둘레 백반
    fine = _sine_noise(P, 160, 40, 140, 11, beta=0.4)
    v = 0.78 + 0.07 * fine
    rng = np.random.default_rng(12)
    for _ in range(4):
        c = rng.normal(size=3); c /= np.linalg.norm(c)
        c[2] *= 0.4; c /= np.linalg.norm(c)                    # 저위도 위주
        ang = np.arccos(np.clip(P @ c.astype(np.float32), -1, 1))
        r0 = rng.uniform(0.06, 0.13)
        v -= 0.45 * np.exp(-(ang / r0) ** 2) + 0.18 * np.exp(-(ang / (r0 * 1.8)) ** 2)
        v += 0.12 * np.exp(-((ang - r0 * 2.2) / (r0 * 0.9)) ** 2)
    xs = [0.0, 0.4, 0.7, 0.9, 1.1]
    cs = np.array([(0.20, 0.03, 0.01), (0.55, 0.10, 0.03), (0.92, 0.26, 0.08), (1.0, 0.40, 0.14), (1.0, 0.58, 0.26)])
    col = np.stack([np.interp(v, xs, cs[:, c]) for c in range(3)], -1)
    _save_tex(col, "tex_s7_proxima.png")
    # 프록시마 b — 현무암·녹 암석 + 크레이터 + 얼음 극관(조석 고정 '눈알 행성' 은 초승달에선 안 보여 생략)
    P2, la2 = _sphere_xyz(1024, 2048)
    n1 = _sine_noise(P2, 90, 2, 30, 21, beta=1.1)
    n2 = _sine_noise(P2, 90, 20, 120, 22, beta=0.7)
    base = np.stack([0.30 + 0.06 * n1, 0.27 + 0.05 * n1, 0.25 + 0.03 * n1], -1)
    rust = np.clip(0.5 + 0.5 * _sine_noise(P2, 40, 2, 10, 23), 0, 1)[..., None]
    base = base * (1 - 0.5 * rust) + np.array([0.46, 0.30, 0.20]) * 0.5 * rust
    ice = sp.sstep(0.95, 1.10, np.abs(la2) + 0.08 * n1)[..., None]
    col = base * (1 - ice) + np.array([0.86, 0.88, 0.92]) * ice
    col *= (1 + 0.08 * n2)[..., None]
    hgt = 0.5 + 0.18 * n1 + 0.10 * n2
    rng = np.random.default_rng(24)
    for _ in range(60):
        c = rng.normal(size=3); c /= np.linalg.norm(c)
        ang = np.arccos(np.clip(P2 @ c.astype(np.float32), -1, 1))
        r0 = rng.uniform(0.02, 0.09)
        hgt += -0.25 * np.exp(-(ang / r0) ** 4) + 0.12 * np.exp(-((ang - r0) / (r0 * 0.25)) ** 2)
    _save_tex(col, "tex_s7_proxb.png")
    _save_tex(np.repeat(np.clip(hgt, 0, 1)[..., None], 3, -1), "tex_s7_proxb_h.png")
    print("textures ->", REN_DIR)


def run_blender(names):
    import subprocess
    cmd = [BLENDER, "-b", "-P", os.path.abspath(__file__), "--"] + list(names)
    print(" ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit("blender failed")


def _load(name):
    import numpy as np
    from PIL import Image
    return np.asarray(Image.open(os.path.join(REN_DIR, name + ".png")).convert("RGBA"), np.float32) / 255.0


def post_betel(sp):
    """렌더(몸통) + 채층 광 + 비대칭 먼지 껍질 깃털 → RGBA 1080x720."""
    import numpy as np
    a = sp.resize_premul(_load("betel_limb"), BETEL_W, BETEL_H)
    W, H = BETEL_W, BETEL_H
    yy, xx = sp.grid(H, W)
    cx, cy = W / 2, BETEL_APEX + BETEL_R
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) - BETEL_R          # 림에서 바깥 거리(px)
    ang = np.arctan2(yy - cy, xx - cx)
    body = a[..., :3] * a[..., 3:4]
    # 채층(붉은 좁은 테) + 넓은 광
    chrom = np.exp(-np.clip(d, 0, None) / 10.0) * (d > -2)
    glow = np.exp(-np.clip(d, 0, None) / 70.0) * (d > -2)
    # 먼지 껍질 — 림 위 60~260px 의 덩어리진 껍질, 왼쪽(서쪽)으로 큰 깃털
    n = sp.pnoise(H, W, 3.0, 71); n2 = sp.pnoise(H, W, 2.4, 72)
    wy = sp.pnoise(H, W, 3.6, 73) * 18; wx = sp.pnoise(H, W, 3.6, 74) * 18
    shell = np.exp(-((d - 150) / 90) ** 2) * np.clip(0.3 + 0.8 * sp.warp(n, wy, wx), 0, None)
    plume = np.exp(-((ang + math.pi / 2 + 0.28) / 0.16) ** 2) * np.exp(-((d - 170) / 120) ** 2) * 1.1
    dust = (shell + plume * np.clip(0.5 + 0.6 * n2, 0, None)) * (d > 0)
    E = (chrom * 0.55)[..., None] * sp.col((1.0, 0.26, 0.08)) + (glow * 0.16)[..., None] * sp.col((1.0, 0.30, 0.10))
    E += (dust * 0.055)[..., None] * sp.col((0.95, 0.40, 0.20))
    halo = sp.cap_luma(sp.tone(E[..., :3] if E.ndim == 3 else E, 1.0), 0.40, 0.55)
    C = body + halo * (1 - a[..., 3:4])
    C = sp.cap_luma(np.clip(C, 0, 1), 0.62, 0.80)
    fade = sp.sstep(0.0, 0.06, yy / H)
    C *= fade[..., None]
    alpha = np.maximum(a[..., 3], sp.envelope_alpha(C, r=14, s=9, boost=2.0))
    rgb = np.where(alpha[..., None] > 1e-4, C / np.maximum(alpha[..., None], 1e-4), 0)
    out = np.dstack([np.clip(rgb, 0, 1), alpha]).astype(np.float32)
    out[..., 3][out[..., 3] < 2.5 / 255] = 0
    geo = dict(limb_center_px=[W / 2, cy], limb_radius_px=BETEL_R, limb_apex_px=[W / 2, BETEL_APEX],
               anchor="bottom-center: 아래 가장자리를 화면 한쪽에 붙이고 90° 돌려 '화면 한쪽 25% 림'으로 쓴다",
               dust_plume="림 꼭대기에서 왼쪽 위로 깃털(서쪽 먼지 분출)")
    return out, geo


def post_proxima(sp):
    import numpy as np
    S = 384
    a = sp.resize_premul(_load("proxima"), S, S)
    yy, xx = sp.grid(S, S)
    c = S / 2
    R = S * PROX_DISK / 2
    dx, dy = xx - c, yy - c
    d = np.sqrt(dx * dx + dy * dy) - R
    ang = np.arctan2(dy, dx)
    corona = np.exp(-np.clip(d, 0, None) / 6.0) * (d > -1) * 0.45 + np.exp(-np.clip(d, 0, None) / 26.0) * (d > -1) * 0.12
    E = corona[..., None] * sp.col((1.0, 0.36, 0.14))
    # 플레어 고리 — 림에 발을 딛은 반원 고리 3개(각도, 폭(라디안), 높이 px, 밝기)
    for a0, span, hgt, amp in ((-1.05, 0.20, 26, 0.30), (-0.70, 0.12, 15, 0.22), (2.40, 0.16, 20, 0.26)):
        t = np.linspace(0, math.pi, 400)
        th = a0 + (t / math.pi - 0.5) * span
        rr = R + np.sin(t) * hgt
        px = c + rr * np.cos(th); py = c + rr * np.sin(th)
        loop = np.zeros((S, S), np.float32)
        np.add.at(loop, (np.clip(py.astype(int), 0, S - 1), np.clip(px.astype(int), 0, S - 1)), 1.0)
        loop = sp.blur(loop, 0.9) * 2.6
        E += (loop * amp)[..., None] * sp.col((1.0, 0.42, 0.14))
        for fx, fy in ((px[0], py[0]), (px[-1], py[-1])):          # 발(footpoint) 밝은 점
            sp.add_star(E, fx, fy, 1.2 * amp, (1.0, 0.60, 0.30), sig=1.4)
    halo = sp.cap_luma(sp.tone(E, 1.0), 0.45, 0.62)
    body = a[..., :3] * a[..., 3:4]
    C = np.clip(body + halo * (1 - a[..., 3:4]), 0, 1)
    C = sp.cap_luma(C, 0.58, 0.74)
    C *= sp.sstep(S / 2, S / 2 * 0.9, np.sqrt(dx * dx + dy * dy))[..., None]
    alpha = np.maximum(a[..., 3], sp.envelope_alpha(C, r=14, s=9, boost=2.0))
    rgb = np.where(alpha[..., None] > 1e-4, C / np.maximum(alpha[..., None], 1e-4), 0)
    out = np.dstack([np.clip(rgb, 0, 1), alpha]).astype(np.float32)
    out[..., 3][out[..., 3] < 2.5 / 255] = 0
    return out, dict(center=[S / 2, S / 2], disk_r_px=round(R, 1), disk_frac=PROX_DISK)


def post_proxb(sp):
    a = sp.resize_premul(_load("proxima_b"), 256, 256)
    a = sp.cap_luma(a[..., :3], 0.56, 0.70)
    import numpy as np
    al = sp.resize_premul(_load("proxima_b"), 256, 256)[..., 3]
    out = np.dstack([a, al]).astype(np.float32)
    out[..., 3][out[..., 3] < 2.5 / 255] = 0
    return out, dict(center=[128, 128], disk_r_px=round(256 * 0.90 / 2, 1), disk_frac=0.90,
                     lit_from="오른쪽 뒤(붉은 별빛) — 약 30% 초승달")


def make_sirius(sp):
    """시리우스 A — 청백 코어 + 8방향 회절 스파이크 + 넓은 헤일로. 불투명 RGB('lighter')."""
    import numpy as np
    S = 384 * 2
    E = np.zeros((S, S, 3), np.float32)
    sp.add_star(E, S / 2, S / 2, 30.0, (0.80, 0.90, 1.0), sig=5.0, halo=0.10, halo_r=26, spikes=8,
                spike_len=70, spike_w=1.6, spike_amp=0.22, spike_ang=0.0)
    sp.add_star(E, S / 2, S / 2, 12.0, (0.95, 0.98, 1.0), sig=2.6)
    # 스파이크에 옅은 무지개 번짐(색수차) — 굵은 4갈래만
    yy, xx = sp.grid(S, S)
    dx, dy = xx - S / 2, yy - S / 2
    r = np.sqrt(dx * dx + dy * dy)
    for k in range(4):
        a = k * math.pi / 2
        perp = np.abs(-dx * math.sin(a) + dy * math.cos(a))
        along = dx * math.cos(a) + dy * math.sin(a)
        L = np.exp(-(perp / 3.0) ** 2) * np.exp(-np.clip(along, 0, None) / 90) * (along > 20)
        E += (L * 0.5)[..., None] * np.stack([sp.sstep(60, 200, r), sp.sstep(20, 120, r) * 0.6 + 0.4,
                                               np.ones_like(r)], -1)
    C = sp.cap_luma(sp.tone(E, 1.0), 0.72, 0.92)
    C *= sp.sstep(S / 2, S / 2 * 0.85, r)[..., None]
    out = np.dstack([C, np.ones((S, S), np.float32)])
    return sp.resize_premul(out, 384, 384), dict(center=[192, 192], blend="lighter",
                                                 companion="시리우스 B 는 굽지 않음 — 런타임 SZ_GLOW 작은 흰 점(A 에서 약 40px)")


STAR_ASSETS = {
    # 이름: (후처리 함수, 예산 KB, lo 예산 KB, 메모)
    "betel_limb": (post_betel, 80, 26, "존15 베텔게우스 불의 벽 — 90° 돌려 화면 한쪽 25% 를 스치는 림. 먼지 껍질 포함"),
    "proxima": (post_proxima, 20, 8, "존11 프록시마(플레어 고리) · 존28 마지막 별로 재그레이드(globalAlpha 0.7 + 호박 틴트 1회)"),
    "proxima_b": (post_proxb, 15, 6, "존11 프록시마 b — szFlyby 로 전경을 스쳐 간다"),
    "star_sirius": (make_sirius, 15, 6, "존12 시리우스 A — 'lighter'. B 는 SZ_GLOW 점"),
}
STAR_GEO = {}
STAR_AQ = {"proxima": 80}


def post(names=None):
    sp = _sp()
    res = {}
    for name, (fn, kb, kb_lo, note) in STAR_ASSETS.items():
        if names and name not in names:
            continue
        print("==", name, flush=True)
        a, geo = fn(sp)
        STAR_GEO[name] = geo
        h, w = a.shape[:2]
        aq = STAR_AQ.get(name, 95)          # 글로우 알파 계단 방지 — 매끈한 알파라 거의 무손실이어도 싸다
        q, sz = sp.save_webp(a, os.path.join(sp.PUB_DIR, name + ".webp"), kb, q0=80, aq=aq)
        lo = sp.resize_premul(a, w // 2, h // 2)
        ql, szl = sp.save_webp(lo, os.path.join(sp.PUB_DIR, name + "_lo.webp"), kb_lo, q0=75, aq=aq)
        print("   %dx%d q%d %.1fKB | lo q%d %.1fKB" % (w, h, q, sz / 1024, ql, szl / 1024), flush=True)
        res[name] = dict(q=q, sz=sz, ql=ql, szl=szl, geo=geo)
    sp.geo_update(STAR_GEO)
    return res


if not IN_BLENDER and __name__ == "__main__":
    args = sys.argv[1:]
    mode = args[0] if args else "all"
    rest = args[1:]
    if mode in ("tex", "all"):
        make_textures()
    if mode in ("render", "all"):
        run_blender(rest)
    if mode in ("post", "all"):
        post(rest or None)
