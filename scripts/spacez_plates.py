# -*- coding: utf-8 -*-
"""Space-Z v5 성간·우주론 플레이트 — numpy/scipy 로 미리 굽는 배경 판 (2026-09-28, P7).

10~30존은 지금까지 매 프레임 절차적으로 성운을 그렸다(존당 +18~25ms, 형태도 실제와 달랐다).
성운·은하는 원래 정지 이미지라 미리 구운 판 한 장을 drawImage 하는 편이 품질·성능 둘 다 이긴다.

형태는 실제 천체를 따른다
  m42        오리온 성운 — 트라페지움 중심광(OIII 청록 코어) + 두 날개 + 오리온 바 + 물고기 입(암흑 만)
             + 위쪽 M43 쉼표 모양. m42_dust 는 가까운 층(패럴랙스용 먼지 띠)
  horsehead  IC 434 붉은 커튼(σ Ori 쪽 세로 줄무늬) + 아래 암흑운 L1630 에서 솟은 말머리
             (스플라인 윤곽 → fbm 침식) + NGC 2023 청색 반사성운
  pillars    창조의 기둥 — 아래서 솟는 기둥 3개(왼쪽이 가장 큼), 위에서 오는 자외선으로
             '위쪽 면만 밝게' (밀도 누적 cumsum = 가림), 끝단 광증발 가스, 허블 팔레트
  pleiades   실제 적경·적위로 찍은 9별(7별 회절 스파이크) + 줄무늬 청색 반사성운(메로페 성운)
  milkyway_river  세로 은하수 + 대균열(Great Rift). 직녀(베가)·견우(알타이르+타라제드·알샤인 일렬)·데네브
  milkyway_back   막대나선 우리 은하를 밖에서 뒤돌아본 모습(2팔 강·2팔 약, 먼지띠, HII 분홍 매듭)
  andromeda  M31 경사 77° — 큰 벌지, 10kpc 고리, 가까운 쪽 먼지띠, M32(가깝고 작음)·M110(멀고 흐림)
  cosmic_web 워프한 보로노이 경계 = 필라멘트, 꼭짓점 = 은하단, 2단 계층
  cmb_plate  음향 피크가 있는 파워 스펙트럼 가우스 랜덤장 + 청·주황 LUT
  helio_ribbon  태양권계면 거품 벽(호) + 난류 필라멘트
  oort_plate 얼음 혜성핵 원경 + 뒤쪽(아래) 별이 된 태양
  quasar     점광원 + 숙주은하 + 자홍·청록 제트(보스 빔과 헷갈리지 않게 사선)

색 합성 규칙
  - 선형 방출량 E 를 채널별로 쌓고, 먼지 흡수 exp(-tau) 를 곱한 뒤 1-exp(-E) 로 부드럽게 포화 → 감마
  - '검은 배경 위 색' C 를 스트레이트 알파로 푼다: a = max(max(C), 먼지 불투명도), rgb = C / a.
    게임의 존 배경 그라데이션 위에 source-over 로 그리면 검은 위에서 본 것과 같고, 암흑 성운은 뒤 별을 가린다
  - 가스 휘도 상한 0.52(인코딩 luma) / 별 0.90 — 전면을 덮는 판이라 행성(0.70)보다 낮게. 운석 림 3:1 은 contrast 검사
  - 판 위·아래 가장자리는 알파 0 으로 페이드(화면보다 짧아 스크롤로 흘러가므로 경계가 보이면 안 된다)

실행
  python scripts/spacez_plates.py plates [이름..]         # 판 굽기 → public/assets/spacez/z/*.webp + _lo
  python scripts/spacez_plates.py cards                    # 엽서 pc_13~pc_30 + pc_gold (완성 webp 에서 잘라 만든다)
  python scripts/spacez_plates.py manifest [--shots 폴더] [--manifest 경로]   # 매니페스트·컨택트시트·대비 검사
  python scripts/spacez_plates.py all [--shots ..] [--manifest ..]
블랙홀은 scripts/spacez_blackhole.py, 항성(베텔게우스·프록시마·프록시마 b)은 scripts/blender/spacez_stars.py.
시드 고정 — 같은 입력이면 같은 그림이 나온다(자산 재생성이 결정적).
"""
import math
import os
import sys
import json

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PUB_DIR = os.path.join(ROOT, "public", "assets", "spacez", "z")
REN_DIR = os.path.join(ROOT, "scripts", "og-assets", "spacez_z7")   # Blender 항성 렌더 PNG
os.makedirs(PUB_DIR, exist_ok=True)

SS = 2          # 슈퍼샘플 배율 — 별이 1px 로 또렷하게 떨어지도록 2배로 그리고 줄인다


# ══════════════════════════════ 공용 도구 ══════════════════════════════
def grid(h, w):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return yy, xx


def pnoise(h, w, beta=3.2, seed=0, kmin=0.0, kmax=None, aniso=(1.0, 1.0)):
    """파워 스펙트럼 P(k)∝k^-beta 인 가우스 잡음(평균 0, 표준편차 1). beta 3~3.5 = 구름.
    aniso=(sy,sx) 로 한 축을 늘이면 줄무늬(성운 섬유) 가 된다. FFT 라 8bit 양자화 띠가 없다
    (planet_textures.value_noise 는 8bit 경유라 넓고 매끈한 성운 그라데이션에 계단이 생겨 쓰지 않았다)."""
    rng = np.random.default_rng(seed)
    wn = rng.standard_normal((h, w)).astype(np.float32)
    F = np.fft.rfft2(wn)
    ky = np.fft.fftfreq(h)[:, None] * aniso[0]
    kx = np.fft.rfftfreq(w)[None, :] * aniso[1]
    k = np.sqrt(kx ** 2 + ky ** 2)
    k[0, 0] = 1.0
    amp = k ** (-beta / 2.0)
    if kmin:
        amp *= 1 - np.exp(-(k / kmin) ** 2)
    if kmax:
        amp *= np.exp(-(k / kmax) ** 2)
    amp[0, 0] = 0
    n = np.fft.irfft2(F * amp, s=(h, w)).astype(np.float32)
    n -= n.mean()
    return n / (n.std() + 1e-8)


def warp(f, dy, dx, mode="wrap"):
    h, w = f.shape
    yy, xx = grid(h, w)
    return ndi.map_coordinates(f, [yy + dy, xx + dx], order=1, mode=mode).astype(np.float32)


def blur(a, s):
    if s <= 0:
        return a
    if a.ndim == 3:
        return np.dstack([ndi.gaussian_filter(a[..., c], s) for c in range(a.shape[2])])
    return ndi.gaussian_filter(a, s)


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def col(c):
    return np.array(c, np.float32)[None, None, :]


def catmull(pts, n):
    """Catmull-Rom 스플라인 (열린 곡선) — pts 를 지나는 부드러운 n 점."""
    P = np.array(pts, np.float64)
    P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    segs = len(P) - 3
    out = []
    for i in range(segs):
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        m = max(2, n // segs)
        for t in np.linspace(0, 1, m, endpoint=(i == segs - 1)):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


def _cc(pts, n):
    """닫힌 Catmull-Rom."""
    P = np.array(pts, np.float64)
    k = len(P)
    out = []
    m = max(2, n // k)
    for i in range(k):
        p0, p1, p2, p3 = P[(i - 1) % k], P[i], P[(i + 1) % k], P[(i + 2) % k]
        for t in np.linspace(0, 1, m, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


def curve_field(h, w, pts, n=2000):
    """곡선까지의 거리 d 와 곡선 매개변수 t(0~1) 를 픽셀마다 돌려준다."""
    C = catmull(pts, n)
    seg = np.sqrt(((C[1:] - C[:-1]) ** 2).sum(1))
    L = np.concatenate([[0], np.cumsum(seg)])
    T = L / max(L[-1], 1e-6)
    # 곡선 길이만큼 촘촘히 다시 샘플
    m = int(L[-1] * 1.5) + 2
    tt = np.linspace(0, 1, m)
    X = np.interp(tt, T, C[:, 0]); Y = np.interp(tt, T, C[:, 1])
    mask = np.ones((h, w), bool)
    tmap = np.zeros((h, w), np.float32)
    xi = np.clip(np.round(X).astype(int), 0, w - 1); yi = np.clip(np.round(Y).astype(int), 0, h - 1)
    mask[yi, xi] = False
    tmap[yi, xi] = tt
    d, (iy, ix) = ndi.distance_transform_edt(mask, return_indices=True)
    return d.astype(np.float32), tmap[iy, ix]


def poly_mask(h, w, poly, ss=1):
    im = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(im).polygon([(float(x) * ss, float(y) * ss) for x, y in poly], fill=255)
    if ss > 1:
        im = im.resize((w, h), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255.0


def sdf_from_mask(m):
    """이진 마스크 → 부호 거리(안쪽 +)."""
    inside = m > 0.5
    return (ndi.distance_transform_edt(inside) - ndi.distance_transform_edt(~inside)).astype(np.float32)


# ─── 별 ───
STAR_COLS = np.array([(0.62, 0.74, 1.00), (0.80, 0.87, 1.00), (1.00, 1.00, 1.00), (1.00, 0.95, 0.84),
                      (1.00, 0.84, 0.62), (1.00, 0.68, 0.45)], np.float32)


def star_field(h, w, n, seed, density=None, fmin=0.15, fmax=3.0, alpha=1.6, sigma=0.85, cols_w=None):
    """희미한 별 n 개를 점으로 찍고 PSF(가우스) 한 번으로 번지게 한다. density 가 있으면 그 분포대로 뽑는다."""
    rng = np.random.default_rng(seed)
    if density is None:
        ys = rng.uniform(0, h, n); xs = rng.uniform(0, w, n)
    else:
        p = density.ravel().astype(np.float64)
        p = p / p.sum()
        idx = rng.choice(p.size, n, p=p)
        ys = idx // w + rng.uniform(-0.5, 0.5, n); xs = idx % w + rng.uniform(-0.5, 0.5, n)
    # 파워법칙 밝기 분포 (어두운 별이 훨씬 많다)
    u = rng.random(n)
    f = fmin * (1 - u * (1 - (fmin / fmax) ** alpha)) ** (-1 / alpha)
    cw = np.array(cols_w or [0.12, 0.2, 0.3, 0.2, 0.12, 0.06], np.float64)
    ci = rng.choice(len(STAR_COLS), n, p=cw / cw.sum())
    E = np.zeros((h, w, 3), np.float32)
    yi = np.clip(ys.astype(int), 0, h - 1); xi = np.clip(xs.astype(int), 0, w - 1)
    for c in range(3):
        np.add.at(E[..., c], (yi, xi), (f * STAR_COLS[ci, c]).astype(np.float32))
    k = 2 * math.pi * sigma * sigma
    return blur(E, sigma) * k


def add_star(E, x, y, flux, c, sig=1.2, halo=0.0, halo_r=6.0, spikes=0, spike_len=40.0, spike_w=0.9,
             spike_ang=0.0, spike_amp=0.35):
    """밝은 별 하나 — 가우스 코어 + 모팻형 헤일로 + 회절 스파이크(4·8 방향)."""
    h, w = E.shape[:2]
    Rh = halo_r * (max(flux * halo, 1e-6) / 0.0015) ** (1 / 3.2) if halo else 0
    R = int(max(5 * sig, Rh, spike_len * 5.5 if spikes else 0)) + 2
    x0, x1 = max(0, int(x) - R), min(w, int(x) + R + 1)
    y0, y1 = max(0, int(y) - R), min(h, int(y) + R + 1)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xx - x, yy - y
    r2 = dx * dx + dy * dy
    I = np.exp(-r2 / (2 * sig * sig))
    if halo:
        I = I + halo * (1 + r2 / (halo_r * halo_r)) ** -1.6
    if spikes:
        lines = spikes // 2
        for k in range(lines):
            a = spike_ang + k * math.pi / lines
            ca, sa = math.cos(a), math.sin(a)
            along = dx * ca + dy * sa
            perp = -dx * sa + dy * ca
            I = I + spike_amp * np.exp(-(perp / spike_w) ** 2) * np.exp(-np.abs(along) / spike_len)
    I *= sstep(R, R * 0.75, np.sqrt(r2))
    E[y0:y1, x0:x1] += (flux * I)[..., None] * col(c)[0, 0]


# ─── 색 합성 · 알파 풀기 ───
def lin2enc(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055).astype(np.float32)


def enc2lin(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def tone(E, exposure=1.0):
    """선형 방출 → 부드러운 포화(1-exp) → sRGB 인코딩. 채널별로 포화해 밝은 곳이 흰색으로 모인다."""
    return lin2enc(1 - np.exp(-np.maximum(E, 0) * exposure))


def cap_luma(C, knee=0.40, top=0.52):
    y = C @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    yn = y.copy()
    o = y > knee
    yn[o] = knee + (top - knee) * (1 - np.exp(-(y[o] - knee) / (top - knee)))
    s = np.where(y > 1e-5, yn / np.maximum(y, 1e-5), 1.0)
    return np.clip(C * s[..., None], 0, 1)


def screen(a, b):
    return 1 - (1 - a) * (1 - b)


def unpremul(C, dust_a=None, floor=2.5 / 255):
    """검은 배경 위 색 C(인코딩, 프리멀티플라이와 같다) → 스트레이트 RGBA."""
    a = C.max(axis=2)
    if dust_a is not None:
        a = np.maximum(a, dust_a)
    a = np.clip(a, 0, 1)
    rgb = np.where(a[..., None] > 1e-4, C / np.maximum(a[..., None], 1e-4), 0)
    out = np.dstack([np.clip(rgb, 0, 1), a]).astype(np.float32)
    out[..., 3][out[..., 3] < floor] = 0
    return out


def edge_fade(h, w, top=0.12, bottom=0.12, left=0.0, right=0.0):
    yy, xx = grid(h, w)
    f = np.ones((h, w), np.float32)
    if top:
        f *= sstep(0, top, yy / h)
    if bottom:
        f *= sstep(0, bottom, 1 - yy / h)
    if left:
        f *= sstep(0, left, xx / w)
    if right:
        f *= sstep(0, right, 1 - xx / w)
    return f


def envelope_alpha(C, dust_op=None, r=5, s=2.5, boost=3.0):
    """매끈한 알파 — 색 최대값을 팽창(max filter)한 뒤 블러. 세부는 손실 압축되는 RGB 가 들고,
    알파는 저주파만 남아 WebP 알파(무손실 계열)가 싸진다. 별 꼭대기만 조금 눌릴 수 있다."""
    m = C.max(axis=2)
    env = ndi.gaussian_filter(ndi.maximum_filter(m, size=2 * r + 1), s)
    env = np.maximum(env, ndi.gaussian_filter(m, 1.0))
    # 빨리 1 로 포화 — 알파는 양자화(alpha_quality 60)되므로, 밝기 기울기를 알파가 들면 계단이 생긴다.
    # 밝은 곳은 불투명으로 두고 기울기는 손실 압축 RGB 가 들게 한다(어두운 가장자리만 알파가 변한다)
    env = 1 - (1 - np.clip(env, 0, 1)) ** boost
    if dust_op is not None:
        env = np.maximum(env, dust_op)
    return np.clip(env, 0, 1)


def compose(gas_E, star_E=None, tau=None, dust_col=(0.0, 0.0, 0.0), dust_op=None, exposure=1.0,
            gas_cap=(0.40, 0.52), star_cap=(0.70, 0.90), fade=None, star_behind=True, soft=1.0 * SS,
            gamma=1.0, mode="add", star_env=True):
    """가스 방출 + 별 + 먼지 흡수 → 판.
    mode='add'  : 불투명 RGB(검정 = 투명). 런타임은 globalCompositeOperation='lighter' 로 그린다 — 알파 채널이 없어 가장 싸다
    mode='over' : 스트레이트 RGBA(매끈한 알파). 뒤 배경·별을 가려야 하는 암흑 성운용, source-over
    tau: 먼지 광학 깊이(가스·뒤 별을 가린다). dust_op: 뒤 게임 배경까지 가리는 불투명도.
    soft: 가스만 살짝 블러(SS px) — 폰에서 2~3배 확대돼 픽셀 단위 잔결은 안 보이고 용량만 먹는다."""
    T = np.exp(-tau)[..., None] if tau is not None else 1.0
    G = gas_E * T
    if soft:
        G = blur(G, soft)
    if gamma != 1.0:
        G = np.power(np.maximum(G, 0), gamma)
    Cg = cap_luma(tone(G, exposure), *gas_cap)
    C = Cg
    if star_E is not None:
        Cs = cap_luma(tone(star_E * (T if star_behind else 1.0), 1.0), *star_cap)
        C = screen(Cg, Cs)
    Cgd = Cg
    if dust_op is not None:
        # 먼지 자체 색(아주 어두운 갈색 — 뒤에서 새는 산란광). 방출보다 앞에 있는 몸통
        dc = col(dust_col)
        C = C + dc * dust_op[..., None] * (1 - C.max(axis=2, keepdims=True))
        Cgd = Cg + dc * dust_op[..., None] * (1 - Cg.max(axis=2, keepdims=True))
    if fade is not None:
        C = C * fade[..., None]
        Cgd = Cgd * fade[..., None]
        if dust_op is not None:
            dust_op = dust_op * fade
    C = np.clip(C, 0, 1)
    if mode == "add":
        return np.dstack([C, np.ones(C.shape[:2], np.float32)]).astype(np.float32)
    if star_env or star_E is None:
        a = envelope_alpha(C, dust_op)
    else:
        # 2026-09-29 (D) 별은 알파 팽창(max filter)에서 뺀다 — 별 둘레까지 불투명해져 뒤 게임 배경(남색·성운)이 빠지면서
        # 가스 위에 '검은 고리 점'이 수십 개 생겼다(S11-08). 별은 제 픽셀 밝기만 알파로(C/a ≤ 1 이 되게 C 최대값)
        a = np.maximum(envelope_alpha(np.clip(Cgd, 0, 1), dust_op), C.max(axis=2))
    rgb = np.where(a[..., None] > 1e-4, C / np.maximum(a[..., None], 1e-4), 0)
    out = np.dstack([np.clip(rgb, 0, 1), a]).astype(np.float32)
    out[..., 3][out[..., 3] < 2.5 / 255] = 0
    return out


def resize_premul(a, w, h):
    pm = a.copy()
    pm[..., :3] *= pm[..., 3:4]
    chans = [np.asarray(Image.fromarray(np.ascontiguousarray(pm[..., c], np.float32)).resize((w, h), Image.LANCZOS), np.float32)
             for c in range(4)]
    out = np.clip(np.dstack(chans), 0, 1)
    al = out[..., 3:4]
    rgb = np.where(al > 1e-4, out[..., :3] / np.maximum(al, 1e-4), 0)
    return np.dstack([np.clip(rgb, 0, 1), al[..., 0]]).astype(np.float32)


def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


def save_webp(a, path, kb, q0=75, qmin=30, qmax=90, aq=60):
    """품질 q0 에서 시작, 예산(KB)을 넘으면 내리고 예산의 60% 미만이면 예산 안에서 올린다(P6 와 같은 규칙).
    알파가 전부 1 이면 RGB 로 저장(알파 채널 없음)."""
    im = to_img(a)
    if float(a[..., 3].min()) >= 0.999:
        im = im.convert("RGB")
    lim = kb * 1024 * 1.03

    def enc(q):
        im.save(path, "WEBP", quality=q, method=6, alpha_quality=aq)
        return os.path.getsize(path)
    q = q0
    sz = enc(q)
    if sz <= lim:
        best = (q, sz)
        while sz < kb * 1024 * 0.6 and q < qmax:
            q = min(qmax, q + 5)
            sz = enc(q)
            if sz > lim:
                break
            best = (q, sz)
        if best[0] != q:
            enc(best[0])
        return best
    while sz > lim and q > qmin:
        q -= 5
        sz = enc(q)
    return q, sz


def load_webp(name):
    return np.asarray(Image.open(os.path.join(PUB_DIR, name + ".webp")).convert("RGBA"), np.float32) / 255.0


def alpha_bbox(a, thr=0.02):
    ys, xs = np.where(a[..., 3] > thr)
    if len(ys) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def luma_stats(a):
    """검은 배경 위에서 본 인코딩 luma — 최대·평균(알파 가중) 을 매니페스트에 적는다."""
    C = a[..., :3] * a[..., 3:4]
    y = C @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    return round(float(y.max()), 3), round(float(y.mean()), 3), round(float(np.percentile(y, 99)), 3)


# ══════════════════════════════ 플레이트 ══════════════════════════════
HA = (1.00, 0.20, 0.32)     # Hα + Hβ 가 섞인 방출 성운 분홍빛 빨강
O3 = (0.22, 0.95, 0.82)     # OIII 청록
REFL = (0.32, 0.52, 1.00)   # 반사성운 청색


def plate_m42():
    """오리온 성운 M42 + M43. 세로 540x960 (SS 2배). 중심 = 트라페지움."""
    W, H = 540 * SS, 960 * SS
    yy, xx = grid(H, W)
    cx, cy = 0.50 * W, 0.52 * H
    u = (xx - cx) / W; v = (yy - cy) / W          # W 단위 좌표 (가로 ±0.5)
    r = np.sqrt(u * u + v * v)
    n1 = pnoise(H, W, 3.3, 11); n2 = pnoise(H, W, 2.8, 12); n3 = pnoise(H, W, 3.6, 13)
    wy = pnoise(H, W, 3.8, 14) * 30 * SS; wx = pnoise(H, W, 3.8, 15) * 30 * SS
    fil = warp(pnoise(H, W, 2.7, 16, kmax=0.08), wy, wx)                 # 섬유(워프한 잔결)
    ridge = (1 - np.abs(warp(pnoise(H, W, 3.0, 17, kmax=0.08), wy * 1.4, wx * 1.4))) ** 4

    # 1) 코어 — 트라페지움 둘레 밝은 휴이겐스 영역(OIII 가 강해 청록빛 흰색)
    core = (1 + (r / 0.040) ** 2) ** -1.35 * (1 + 0.25 * n2)
    core_o3 = np.exp(-(r / 0.085) ** 1.5) * (1 + 0.35 * fil)

    # 2) 날개 — 왼쪽은 아래로 휘었다가 왼쪽 가장자리를 타고 위로 말려 오르고, 오른쪽은 아래로 쓸려 내려간다.
    #    날개는 '얇은 판'이라 한쪽 가장자리(이온화 전면)가 또렷하고 반대쪽으로 옅어진다
    wings = np.zeros((H, W), np.float32)
    for pts, w0, w1, amp, side in (
        ([(-0.03, 0.03), (-0.15, 0.13), (-0.30, 0.17), (-0.42, 0.07), (-0.46, -0.12), (-0.40, -0.30)], 0.028, 0.085, 1.0, 1),
        ([(0.035, 0.025), (0.16, 0.08), (0.29, 0.20), (0.37, 0.36), (0.40, 0.56)], 0.028, 0.10, 0.9, -1),
        ([(0.00, 0.05), (-0.05, 0.19), (-0.11, 0.33), (-0.09, 0.47)], 0.022, 0.07, 0.45, 1),
    ):
        P = [(cx + px * W, cy + py * W) for px, py in pts]
        d, t = curve_field(H, W, P)
        width = (w0 + (w1 - w0) * t) * W
        prof = np.exp(-(d / width) ** 2) * (1 - 0.55 * t)
        wings += amp * prof * np.clip(0.35 + 0.55 * fil + 1.1 * ridge, 0, None)
    # 3) 넓은 Hα 외곽광 (옅게 — 날개 모양이 먼저 읽혀야 한다)
    halo = np.exp(-r / 0.22) * np.clip(0.45 + 0.6 * n1, 0, None)
    # 4) 오리온 바 — 트라페지움 남동쪽(왼쪽 아래)의 대각선 밝은 능선. 바깥쪽(왼아래)은 급격히 어둡다
    bu, bv = u + 0.07, v - 0.07
    along = (bu - bv) / math.sqrt(2); across = (bu + bv) / math.sqrt(2)
    bar = np.exp(-(along / 0.075) ** 2) * np.exp(-((across + 0.004) / 0.009) ** 2) * (0.7 + 0.5 * fil)
    # 5) M43 — 북쪽(위)의 둥근 성운, 왼쪽·아래를 감싼 먼지로 쉼표 모양
    mu, mv = u + 0.05, v + 0.36
    mr = np.sqrt(mu * mu + mv * mv)
    m43 = (1 + (mr / 0.032) ** 2) ** -1.4 * (1 + 0.3 * n2)

    Ha = 1.3 * core + 1.9 * wings + 0.22 * halo + 1.1 * bar + 0.9 * m43
    Oi = 1.6 * core_o3 + 0.12 * wings * np.exp(-r / 0.2)
    E = Ha[..., None] * col(HA) + Oi[..., None] * col(O3)
    E *= 0.60

    # 먼지 — 물고기 입(코어 북동쪽으로 파고드는 암흑 만) + M42/M43 사이 띠 + 외곽 얼룩
    tau = np.zeros((H, W), np.float32)
    P = [(cx - 0.50 * W, cy - 0.20 * W), (cx - 0.25 * W, cy - 0.17 * W), (cx - 0.10 * W, cy - 0.10 * W),
         (cx - 0.035 * W, cy - 0.035 * W)]
    d, t = curve_field(H, W, P)
    tau += 3.2 * np.exp(-(d / ((0.065 - 0.042 * t) * W)) ** 2) * np.clip(0.8 + 0.4 * n3, 0, None)
    P = [(cx - 0.55 * W, cy - 0.27 * W), (cx - 0.25 * W, cy - 0.26 * W), (cx + 0.02 * W, cy - 0.29 * W),
         (cx + 0.12 * W, cy - 0.42 * W), (cx + 0.02 * W, cy - 0.47 * W)]
    d, t = curve_field(H, W, P)
    tau += 2.4 * np.exp(-(d / (0.032 * W)) ** 2) * np.clip(0.7 + 0.5 * n3, 0, None)
    tau += 1.6 * np.clip(warp(pnoise(H, W, 3.2, 18), wy, wx) - 0.5, 0, None) * sstep(0.10, 0.30, r)
    tau += 2.8 * np.exp(-((across + 0.03) / 0.028) ** 2) * np.exp(-(along / 0.12) ** 2)   # 바 바깥 먼지

    # 별 — 트라페지움 4별(작은 사다리꼴) + θ2 + 성단 어린 별 + 배경 별(적게 — 게임에 별 배경이 따로 있다)
    S = star_field(H, W, 260, 19, fmin=0.4, fmax=4.0)
    trap = [(0.000, 0.000, 7.0), (0.011, -0.006, 4.0), (-0.006, 0.010, 5.0), (0.010, 0.012, 3.2)]
    for du, dv, f in trap:
        add_star(S, cx + du * W, cy + dv * W, f, (0.80, 0.88, 1.0), sig=1.2 * SS, halo=0.04, halo_r=3 * SS,
                 spikes=4, spike_len=5 * SS, spike_w=0.5 * SS, spike_amp=0.12)
    add_star(S, cx - 0.045 * W, cy + 0.05 * W, 4.0, (0.78, 0.86, 1.0), sig=1.1 * SS)
    add_star(S, cx - 0.05 * W, cy - 0.36 * W, 4.0, (0.9, 0.93, 1.0), sig=1.1 * SS)      # NU Ori (M43 중심)
    rng = np.random.default_rng(20)
    for _ in range(22):
        ang = rng.uniform(0, 2 * math.pi); rr = abs(rng.normal(0, 0.09))
        add_star(S, cx + math.cos(ang) * rr * W, cy + math.sin(ang) * rr * W, rng.uniform(0.6, 2.0),
                 (1.0, rng.uniform(0.75, 0.95), rng.uniform(0.6, 0.9)), sig=1.0 * SS)
    fade = edge_fade(H, W, 0.14, 0.14)
    return compose(E, S * 0.9, tau=tau, exposure=1.25, gamma=1.1, fade=fade), dict(
        trapezium=[round(cx / SS), round(cy / SS)], m43=[round((cx - 0.05 * W) / SS), round((cy - 0.36 * W) / SS)])


def plate_m42_dust():
    """M42 앞쪽 먼지 띠 (가까운 층 — 0.8CH 이동 패럴랙스). 양옆 가장자리에만 옅은 먼지 자락,
    가운데(플레이 영역)는 비운다. 성운 쪽 가장자리에 분홍 역광 림."""
    W, H = 540 * SS, 960 * SS
    yy, xx = grid(H, W)
    wy = pnoise(H, W, 3.8, 31) * 36 * SS; wx = pnoise(H, W, 3.8, 32) * 36 * SS
    mod = warp(pnoise(H, W, 3.4, 33, kmax=0.03), wy, wx)
    band = np.zeros((H, W), np.float32)
    for pts, wd in (([(-0.05, 0.12), (0.10, 0.20), (0.20, 0.32), (0.16, 0.44), (0.02, 0.52)], 0.09),
                    ([(1.05, 0.50), (0.90, 0.56), (0.82, 0.66), (0.86, 0.78), (1.02, 0.86)], 0.08),
                    ([(-0.05, 0.74), (0.08, 0.80), (0.12, 0.92), (0.04, 1.02)], 0.06),
                    ([(1.05, 0.08), (0.92, 0.16), (0.95, 0.26)], 0.05)):
        d, t = curve_field(H, W, [(px * W, py * H) for px, py in pts])
        band = np.maximum(band, np.exp(-(d / (wd * W)) ** 2))
    band = warp(band, wy, wx, mode="nearest")
    streak = warp(pnoise(H, W, 2.8, 35, aniso=(1.0, 4.0), kmax=0.03), wy, wx)
    dens = np.clip(band * (0.55 + 0.35 * mod + 0.25 * streak) - 0.10, 0, None)
    dens = blur(dens, 5 * SS)
    op = np.clip(1 - np.exp(-3.0 * dens), 0, 0.80)
    thin = sstep(0.05, 0.45, op)
    dcol = col((0.20, 0.07, 0.09)) * (1 - thin[..., None]) + col((0.045, 0.022, 0.026)) * thin[..., None]
    C = dcol * op[..., None]
    fade = edge_fade(H, W, 0.06, 0.06)
    C = C * fade[..., None]
    op = op * fade
    a = np.maximum(op, envelope_alpha(C))
    rgb = np.where(a[..., None] > 1e-4, C / np.maximum(a[..., None], 1e-4), 0)
    out = np.dstack([np.clip(rgb, 0, 1), a]).astype(np.float32)
    out[..., 3][out[..., 3] < 2.5 / 255] = 0
    return out


def horse_poly(x0, y0, s):
    """말머리 윤곽 — 체스 나이트처럼 머리가 크고 왼쪽 아래로 주둥이를 내린다. 아래 암흑운에서 목이 솟는다.
    (u 오른쪽, v 위) W 단위 → 픽셀. 실제 사진(북쪽 위)의 말머리를 따라 잡은 점들."""
    P = [(-0.030, -0.06), (-0.034, 0.05), (-0.046, 0.120),                         # 목 앞(살짝 오목)
         (-0.080, 0.146), (-0.130, 0.152), (-0.180, 0.158),                         # 턱 밑(묵직)
         (-0.216, 0.170), (-0.236, 0.192), (-0.236, 0.218),                         # 주둥이 끝(뭉툭)
         (-0.212, 0.236), (-0.168, 0.256), (-0.118, 0.284),                         # 콧등
         (-0.076, 0.312), (-0.046, 0.336),                                           # 이마
         (-0.030, 0.356), (-0.012, 0.370), (0.002, 0.352),                           # 귀 혹
         (0.028, 0.330), (0.052, 0.300), (0.066, 0.250),                             # 갈기
         (0.074, 0.180), (0.090, 0.110), (0.118, 0.040), (0.160, -0.06)]             # 목 뒤
    return [(x0 + pu * s, y0 - pv * s) for pu, pv in P]


def plate_horsehead():
    """말머리 성운 — IC 434 붉은 커튼 위, 아래 L1630 암흑운에서 말머리가 솟는다. RGBA(source-over)."""
    W, H = 540 * SS, 960 * SS
    yy, xx = grid(H, W)
    edge_y = 0.66 * H
    # 암흑운 가장자리 — 거의 곧은 선(실제 이온화 경계) + 완만한 기복 + 잔 손가락
    rs = np.random.default_rng(41)
    line_n = ndi.gaussian_filter1d(rs.standard_normal(W), 60 * SS); line_n /= np.abs(line_n).max() + 1e-6
    line_f = ndi.gaussian_filter1d(rs.standard_normal(W), 5 * SS); line_f /= np.abs(line_f).max() + 1e-6
    ey = edge_y + line_n * 14 * SS + line_f * 3 * SS - 0.035 * (xx[0] - W / 2)   # 오른쪽이 살짝 높다
    cloud = (yy > ey[None, :]).astype(np.float32)
    hx, hy, hs = 0.55 * W, edge_y + 0.012 * H, 1.05 * W
    C = _cc(horse_poly(hx, hy, hs), 1200)
    head = poly_mask(H, W, [tuple(p) for p in C], ss=1)
    m = np.maximum(cloud, head)
    sd = sdf_from_mask(m)
    ero = warp(pnoise(H, W, 2.8, 43, kmax=0.12), pnoise(H, W, 3.5, 44) * 6 * SS, pnoise(H, W, 3.5, 45) * 6 * SS)
    mask = sstep(-1.4 * SS, 1.4 * SS, sd + ero * 2.2 * SS + pnoise(H, W, 3.4, 46) * 2.5 * SS)
    mask = blur(mask, 0.7 * SS)

    # IC 434 — 이온화 경계 바로 위가 가장 밝고 위로 옅어진다. σ Ori(위) 쪽으로 향한 세로 줄무늬
    streak = pnoise(H, W, 2.6, 47, aniso=(7.0, 1.0), kmax=0.05)
    streak = warp(streak, 0, pnoise(H, W, 3.6, 48) * 10 * SS)
    cl = pnoise(H, W, 3.3, 49)
    dist_up = np.clip((ey[None, :] - yy), 0, None) / H
    glow = (0.30 + 0.70 * np.exp(-dist_up / 0.22)) * sstep(0.0, 0.5, 1 - dist_up / 0.64)
    glow *= np.clip(0.72 + 0.34 * streak + 0.22 * cl, 0.08, None)
    Ha = glow * sstep(0.02, 0.26, yy / H)
    # 이온화 전면 림 — 구름 경계 바깥 좁은 밝은 테(말머리 윤곽이 뜨게)
    rim = np.clip(blur(mask, 2.0 * SS) - mask, 0, None) * 3.0 + np.clip(blur(mask, 8 * SS) - mask, 0, None) * 1.0
    E = (Ha * 1.0 + rim)[..., None] * col((1.0, 0.16, 0.26))
    # 암흑운 안쪽 가장자리로 새는 빛(구름이 약간 두께를 가진 게 보이게)
    inner = mask * np.exp(-np.clip(sd, 0, None) / (14 * SS)) * np.clip(0.5 + 0.5 * cl, 0, 1)
    E += (inner * 0.18)[..., None] * col((0.9, 0.25, 0.25))
    S = star_field(H, W, 220, 50, fmin=0.4, fmax=4.0)
    rng = np.random.default_rng(51)
    for _ in range(5):
        add_star(S, rng.uniform(0.05, 0.95) * W, rng.uniform(0.12, 0.58) * H, rng.uniform(2, 4.5), (0.9, 0.93, 1.0),
                 sig=1.1 * SS, spikes=4, spike_len=7 * SS, spike_w=0.5 * SS, spike_amp=0.15)
    base = compose(E * 0.62, S * 0.85, tau=mask * 6.0, dust_col=(0.030, 0.012, 0.016), dust_op=mask * 0.94,
                   exposure=1.0, gamma=1.15, mode="over", soft=0.8 * SS, star_env=False)
    # NGC 2023 — 암흑운 안(앞)의 청백 반사성운 + 비추는 별. 흡수 뒤에 더한다
    nx, ny = 0.24 * W, 0.86 * H
    nr = np.sqrt((xx - nx) ** 2 + ((yy - ny) * 1.2) ** 2) / W
    wob = warp(cl, pnoise(H, W, 3.6, 52) * 8 * SS, 0)
    refl = (1 + (nr / 0.022) ** 2) ** -1.5 * np.clip(0.75 + 0.5 * wob, 0, None)
    E2 = refl[..., None] * col((0.55, 0.72, 1.0)) * 0.75
    add_star(E2, nx, ny, 4.0, (0.85, 0.9, 1.0), sig=1.2 * SS, spikes=4, spike_len=6 * SS, spike_w=0.5 * SS,
             spike_amp=0.15)
    add = cap_luma(tone(E2, 1.0), 0.32, 0.46)
    Cn = screen(base[..., :3] * base[..., 3:4], add)
    # D — 위 가장자리를 더 길게(0.10→0.16) 페이드: 맨 위 5% 가 들쭉날쭉한 검은 띠로 보였다(S11-08)
    fade = edge_fade(H, W, 0.16, 0.06)
    Cn = Cn * fade[..., None]
    # D — 별이 든 Cn 전체를 팽창하지 않는다(별 둘레 검은 고리). 반사성운(add)만 팽창, 나머지는 제 밝기
    a = np.maximum(base[..., 3] * fade, np.maximum(envelope_alpha(add * fade[..., None]), Cn.max(axis=2)))
    rgb = np.where(a[..., None] > 1e-4, Cn / np.maximum(a[..., None], 1e-4), 0)
    out = np.dstack([np.clip(rgb, 0, 1), a]).astype(np.float32)
    out[..., 3][out[..., 3] < 2.5 / 255] = 0
    return out, dict(head_top=[round(hx / SS), round((hy - 0.37 * hs) / SS)], edge_y=round(edge_y / SS))


def _pillar_mask(H, W, cl, prof):
    """중심선 cl [(x,y) 비율] 과 폭 표 prof [(t, 폭 비율)] 로 기둥 실루엣(부드러운 마스크)."""
    P = [(px * W, py * H) for px, py in cl]
    d, t = curve_field(H, W, P)
    ts = np.array([a for a, _ in prof]); ws = np.array([b for _, b in prof])
    width = np.interp(t, ts, ws).astype(np.float32) * W * 0.5
    m = sstep(1.0, 0.7, d / width)
    tx, ty = P[-1]
    return m, (tx, ty)


def plate_pillars():
    """창조의 기둥 (M16) — 허블 팔레트. 아래서 솟는 기둥 3개(왼쪽이 가장 크다).
    빛은 위에서 온다 → 밀도를 위에서부터 누적(cumsum)해 가리면 윗면·끝단만 밝고 몸통은 어둡다. RGBA."""
    W, H = 540 * SS, 960 * SS
    yy, xx = grid(H, W)
    n1 = pnoise(H, W, 3.3, 61); n2 = pnoise(H, W, 2.8, 62)
    wy = pnoise(H, W, 3.7, 63) * 14 * SS; wx = pnoise(H, W, 3.7, 64) * 14 * SS
    specs = [
        # 왼쪽 — 넓은 밑동, 가운데 잘록, 오른쪽으로 기운 큰 머리
        ([(0.25, 1.04), (0.27, 0.82), (0.30, 0.60), (0.32, 0.42), (0.35, 0.26), (0.39, 0.15)],
         [(0.0, 0.30), (0.25, 0.22), (0.5, 0.15), (0.72, 0.12), (0.88, 0.15), (1.0, 0.13)]),
        # 가운데 — 중간 높이, 끝이 넓적
        ([(0.61, 1.04), (0.62, 0.88), (0.61, 0.72), (0.59, 0.58), (0.585, 0.47)],
         [(0.0, 0.22), (0.35, 0.15), (0.7, 0.10), (0.9, 0.12), (1.0, 0.10)]),
        # 오른쪽 — 작고 가늘다, 왼쪽으로 기울어짐
        ([(0.88, 1.04), (0.87, 0.92), (0.845, 0.80), (0.82, 0.71)],
         [(0.0, 0.11), (0.5, 0.075), (0.85, 0.07), (1.0, 0.055)]),
    ]
    dens = np.zeros((H, W), np.float32); tips = []
    for cl, prof in specs:
        m, tip = _pillar_mask(H, W, cl, prof)
        dens = np.maximum(dens, m); tips.append(tip)
    sd = sdf_from_mask(dens > 0.5)
    edge_n = warp(pnoise(H, W, 3.0, 65, kmax=0.10), wy, wx)
    sd = sd + edge_n * 7 * SS + pnoise(H, W, 3.8, 66) * 16 * SS
    mask = sstep(-1.5 * SS, 1.5 * SS, sd)
    rho = mask * np.clip(0.8 + 0.4 * warp(pnoise(H, W, 3.0, 67, kmax=0.08), wy * 2, wx * 2), 0.45, None)
    # 위(약간 오른쪽 위)에서 오는 자외선 — 빛 방향으로 전단(shear)한 뒤 세로 누적 → 되돌림. 침투 깊이 약 14px(최종)
    sh = 0.25                                   # 가로 이동 / 세로 1px
    src = blur(rho, 2 * SS)
    Hh, Ww = src.shape
    gy, gx = grid(Hh, Ww)
    sheared = ndi.map_coordinates(src, [gy, gx + (Hh - gy) * sh], order=1, mode="nearest")
    cs = np.cumsum(sheared, axis=0) / (14.0 * SS)
    colsum = ndi.map_coordinates(cs, [gy, gx - (Hh - gy) * sh], order=1, mode="nearest").astype(np.float32)
    light = np.exp(-colsum)
    surface = np.clip(blur(mask, 1.5 * SS) - blur(mask, 7 * SS), 0, None)
    # 입체감 — 부호거리로 원기둥형 높이 + 잔 요철 → 법선 → 오른쪽 위 광원 램버트
    hgt = np.sqrt(np.clip(sd, 0, None) / (6 * SS)) * 6 * SS + warp(pnoise(H, W, 2.9, 71, kmax=0.07), wy, wx) * 5 * SS * mask
    hgt = blur(hgt, 1.5 * SS)
    gy_, gx_ = np.gradient(hgt)
    nz = 1.0 / np.sqrt(gx_ ** 2 + gy_ ** 2 + 1.0)
    L = np.array([0.55, -0.62, 0.56]); L = L / np.linalg.norm(L)
    lam = np.clip((-gx_ * L[0] - gy_ * L[1] + L[2]) * nz, 0, 1)
    shade = lam ** 1.6 * (0.30 + 0.70 * light)
    body = rho * (0.015 + 0.55 * shade + 0.5 * light ** 1.5)
    Ebody = body[..., None] * col((0.80, 0.42, 0.16)) * 0.75
    Erim = (surface * (0.06 + light + 0.4 * lam) * 2.2)[..., None] * col((1.0, 0.80, 0.45))
    # 광증발 가스 — 머리 위로 피어오르는 옅은 줄기(세로 결)
    evap = np.zeros((H, W), np.float32)
    streaks = np.clip(0.6 + 0.6 * warp(pnoise(H, W, 2.6, 68, aniso=(5.0, 1.0), kmax=0.06), wy, wx), 0, None)
    for (tx, ty), (_, prof) in zip(tips, specs):
        wt = prof[-1][1] * W * 0.9
        up = (ty - yy) / H
        evap += np.exp(-((xx - tx) / wt) ** 2) * np.exp(-np.abs(up) / 0.05)
    evap *= 1 - blur(mask, 4 * SS)
    Eevap = (evap * streaks)[..., None] * col((0.60, 0.88, 0.82)) * 0.35
    # 배경 — 청록 OIII 안개(위가 밝다) + 아래쪽 금빛 Hα/SII 안개
    top = np.exp(-yy / (0.6 * H))
    bgO = (0.25 + 0.75 * top) * np.clip(0.6 + 0.4 * n1, 0.1, None)
    bgH = sstep(0.35, 1.0, yy / H) * np.clip(0.5 + 0.5 * n2, 0.05, None)
    Ebg = bgO[..., None] * col((0.14, 0.50, 0.55)) * 0.42 + bgH[..., None] * col((0.70, 0.46, 0.18)) * 0.35
    tau = rho * 3.5
    S = star_field(H, W, 160, 69, fmin=0.4, fmax=3.5, cols_w=[0.05, 0.1, 0.25, 0.25, 0.2, 0.15])
    rng = np.random.default_rng(70)
    for _ in range(4):
        add_star(S, rng.uniform(0.05, 0.95) * W, rng.uniform(0.08, 0.85) * H, rng.uniform(2.5, 4.0),
                 (1.0, 0.85, 0.7), sig=1.1 * SS, spikes=4, spike_len=7 * SS, spike_w=0.5 * SS, spike_amp=0.15)
    Eg = Ebg * np.exp(-tau)[..., None] + Ebody + Erim + Eevap
    op = np.clip(mask * 0.96, 0, 0.96)
    fade = edge_fade(H, W, 0.14, 0.04)
    out = compose(Eg, S * (1 - op)[..., None], tau=None, dust_col=(0.035, 0.02, 0.012), dust_op=op, exposure=1.0,
                  gamma=1.1, fade=fade, mode="over", soft=0.8 * SS, star_env=False)
    # D — 10% 어둡게: 갈색 기둥 위 운석(몸통 색이 비슷)이 묻히지 않게(S11-17). 런타임은 알파 0.85
    out[..., :3] *= 0.9
    return out, dict(tips=[[round(x / SS), round(y / SS)] for x, y in tips])


# 플레이아데스 — (이름, 적경 h m s, 적위 ° ′ ″, 등급)
PLEIADES = [("Alcyone", (3, 47, 29.1), (24, 6, 18), 2.87), ("Atlas", (3, 49, 9.7), (24, 3, 12), 3.62),
            ("Electra", (3, 44, 52.5), (24, 6, 48), 3.70), ("Maia", (3, 45, 49.6), (24, 22, 4), 3.87),
            ("Merope", (3, 46, 19.6), (23, 56, 54), 4.18), ("Taygeta", (3, 45, 12.5), (24, 28, 2), 4.30),
            ("Pleione", (3, 49, 11.2), (24, 8, 12), 5.05), ("Celaeno", (3, 44, 48.2), (24, 17, 22), 5.45),
            ("Asterope", (3, 45, 54.4), (24, 33, 16), 5.64)]


def pleiades_xy(W, H, cy_frac=0.46, span=0.84):
    ra = np.array([(h + m / 60 + s / 3600) * 15 for _, (h, m, s), _, _ in PLEIADES])
    de = np.array([d + m / 60 + s / 3600 for _, _, (d, m, s), _ in PLEIADES])
    x = -(ra - ra.mean()) * math.cos(math.radians(24.1)) * 60      # 동쪽이 왼쪽 (분각)
    y = -(de - de.mean()) * 60
    sc = span * W / (x.max() - x.min())
    return [(W / 2 + xi * sc, cy_frac * H + yi * sc) for xi, yi in zip(x, y)], sc


def plate_pleiades():
    W, H = 540 * SS, 960 * SS
    yy, xx = grid(H, W)
    pos, sc = pleiades_xy(W, H)
    # 조명 — 밝은 별일수록 둘레 반사성운을 밝힌다
    illum = np.zeros((H, W), np.float32)
    for (x, y), (_, _, _, mag) in zip(pos, PLEIADES):
        f = 10 ** (-0.4 * (mag - 2.87))
        rr = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / W
        illum += f * (1 + (rr / 0.05) ** 2) ** -1.1
    # 먼지 — 한 방향으로 줄지은 섬유(성단이 성간운을 지나며 생긴 결, 메로페 성운의 사선 줄무늬)
    ang = math.radians(-28)
    ca, sa = math.cos(ang), math.sin(ang)
    s1 = pnoise(H, W, 2.9, 81, aniso=(1.0, 0.18))
    wy = pnoise(H, W, 3.7, 82) * 30 * SS; wx = pnoise(H, W, 3.7, 83) * 30 * SS
    # 회전: 결 방향을 사선으로 — 좌표를 돌려 샘플
    cxp, cyp = W / 2, H / 2
    ry = (xx - cxp) * sa + (yy - cyp) * ca + cyp
    rx = (xx - cxp) * ca - (yy - cyp) * sa + cxp
    fib = ndi.map_coordinates(s1, [ry + wy, rx + wx], order=1, mode="wrap").astype(np.float32)
    fib = blur(fib, 1.5 * SS)
    cloud = np.clip(0.55 + 0.35 * pnoise(H, W, 3.3, 84) + 0.30 * fib, 0, None)
    neb = cloud * illum
    E = neb[..., None] * col(REFL) * 0.55 + (neb ** 1.6)[..., None] * col((0.85, 0.92, 1.0)) * 0.25
    S = star_field(H, W, 240, 85, fmin=0.4, fmax=3.5)
    for i, ((x, y), (_, _, _, mag)) in enumerate(zip(pos, PLEIADES)):
        f = 10 ** (-0.4 * (mag - 2.87))
        big = i < 7
        add_star(S, x, y, 9.0 * f + 2.0, (0.78, 0.86, 1.0), sig=(1.4 + 1.0 * f) * SS, halo=0.08, halo_r=4 * SS,
                 spikes=4 if big else 0, spike_len=(6 + 12 * f) * SS, spike_w=0.6 * SS, spike_amp=0.20)
    fade = edge_fade(H, W, 0.14, 0.14)
    return compose(E, S * 0.9, exposure=1.0, fade=fade, gamma=1.1), dict(stars=dict(
        (n, [round(x / SS), round(y / SS)]) for (x, y), (n, _, _, _) in zip(pos, PLEIADES)))


def summer_xy(W, H):
    return dict(vega=(0.80 * W, 0.20 * H), altair=(0.20 * W, 0.70 * H), deneb=(0.47 * W, 0.075 * H))


def plate_milkyway_river():
    """견우직녀 — 세로 은하수 + 대균열. 직녀(베가, 오른쪽 위)와 견우(알타이르, 왼쪽 아래)가 강을 사이에 둔다."""
    W, H = 540 * SS, 960 * SS
    yy, xx = grid(H, W)
    cxl = W * (0.50 + 0.05 * np.sin(yy / H * 3.0 + 0.7) - 0.04 * (yy / H - 0.5))
    du = (xx - cxl) / W
    band = np.exp(-(du / 0.17) ** 2)
    core = np.exp(-(du / 0.09) ** 2)
    n1 = pnoise(H, W, 3.0, 91); n2 = pnoise(H, W, 2.2, 92)
    wy = pnoise(H, W, 3.7, 93) * 22 * SS; wx = pnoise(H, W, 3.7, 94) * 22 * SS
    glow = band * np.clip(0.65 + 0.35 * n1, 0.05, None) + 0.9 * core * np.clip(0.6 + 0.5 * n2, 0.05, None)
    # 성운성 별구름(희미한 알갱이) — 고해상 잡음
    grain = np.clip(pnoise(H, W, 1.8, 95, kmax=0.12), 0, None) * band
    Eg = glow[..., None] * col((0.78, 0.76, 0.86)) * 0.22 + grain[..., None] * col((0.9, 0.88, 0.95)) * 0.06
    # 드문 HII 분홍 얼룩
    Eg += (np.clip(pnoise(H, W, 3.4, 96) - 1.6, 0, None) * core)[..., None] * col(HA) * 0.35
    # 대균열 — 띠 가운데를 세로로 가르는 먼지(아래로 갈수록 넓다) + 잔 먼지 얼룩
    rift_x = cxl + W * (0.02 + 0.03 * np.sin(yy / H * 5.0))
    rw = (0.015 + 0.05 * sstep(0.1, 0.9, yy / H)) * W
    rift = np.exp(-(((xx - rift_x) / rw) ** 2))
    rift = warp(rift, wy, wx, mode="nearest")
    dust = np.clip(warp(pnoise(H, W, 2.8, 97), wy, wx) - 0.2, 0, None) * band
    tau = 2.6 * rift * np.clip(0.7 + 0.5 * n1, 0, None) * sstep(0.08, 0.3, yy / H) + 0.8 * dust
    dens = band ** 1.3 * np.exp(-tau * 0.9) + 0.06
    S = star_field(H, W, 7000, 98, density=dens, fmin=0.14, fmax=2.0, sigma=0.8)
    S += star_field(H, W, 250, 99, fmin=0.4, fmax=3.5)
    P = summer_xy(W, H)
    vx, vy = P["vega"]; ax, ay = P["altair"]; dx_, dy_ = P["deneb"]
    add_star(S, vx, vy, 16.0, (0.78, 0.86, 1.0), sig=2.2 * SS, halo=0.10, halo_r=7 * SS, spikes=4,
             spike_len=16 * SS, spike_w=0.7 * SS, spike_amp=0.22)
    add_star(S, ax, ay, 12.0, (1.0, 0.98, 0.92), sig=2.0 * SS, halo=0.10, halo_r=6 * SS, spikes=4,
             spike_len=13 * SS, spike_w=0.7 * SS, spike_amp=0.22)
    add_star(S, dx_, dy_, 7.0, (0.92, 0.95, 1.0), sig=1.6 * SS, halo=0.06, halo_r=4 * SS, spikes=4,
             spike_len=8 * SS, spike_w=0.6 * SS, spike_amp=0.18)
    # 알타이르 양옆 일렬 — 타라제드(주황, 북서=오른쪽 위), 알샤인(남동=왼쪽 아래)
    k = 36 * SS
    add_star(S, ax + k * 0.8, ay - k * 0.6, 4.0, (1.0, 0.72, 0.45), sig=1.3 * SS)
    add_star(S, ax - k * 0.8, ay + k * 0.6, 2.4, (1.0, 0.92, 0.80), sig=1.1 * SS)
    # 거문고자리 평행사변형 (베가 아래 왼쪽)
    for ddx, ddy, f in ((-10, 26, 1.6), (6, 30, 1.6), (-4, 56, 2.2), (12, 60, 2.0)):
        add_star(S, vx + ddx * SS, vy + ddy * SS, f, (0.9, 0.93, 1.0), sig=1.0 * SS)
    fade = edge_fade(H, W, 0.05, 0.10)
    return compose(Eg, S * 0.85, tau=tau, exposure=1.0, fade=fade), dict(
        vega=[round(vx / SS), round(vy / SS)], altair=[round(ax / SS), round(ay / SS)],
        deneb=[round(dx_ / SS), round(dy_ / SS)])


def plate_milkyway_back():
    """우리 은하를 밖에서 뒤돌아본 모습 — 막대나선(SBbc). 1080x600 (SS 2160x1200)."""
    W, H = 1080 * SS, 600 * SS
    yy, xx = grid(H, W)
    cx, cy = W * 0.5, H * 0.5
    Rg = W * 0.46                                  # 원반 반지름(화면 반폭의 92%)
    inc = math.radians(56); pa = math.radians(-14)
    x1 = (xx - cx) * math.cos(pa) + (yy - cy) * math.sin(pa)
    y1 = -(xx - cx) * math.sin(pa) + (yy - cy) * math.cos(pa)
    u = x1 / Rg; v = y1 / (Rg * math.cos(inc))
    r = np.sqrt(u * u + v * v) + 1e-6
    th = np.arctan2(v, u)
    n1 = pnoise(H, W, 2.6, 101); n2 = pnoise(H, W, 1.9, 102)
    # 원반·벌지·막대
    disk = np.exp(-r / 0.30)
    rb = np.sqrt((x1 / Rg) ** 2 + (y1 / (Rg * 0.80)) ** 2)
    bulge = np.exp(-(rb / 0.07) ** 0.9)
    bar_ang = math.radians(28)
    bu = u * math.cos(bar_ang) + v * math.sin(bar_ang); bv = -u * math.sin(bar_ang) + v * math.cos(bar_ang)
    bar = np.exp(-((bu / 0.24) ** 2 + (bv / 0.07) ** 2))
    # 나선팔 — 로그 나선, 막대 끝에서 시작. 강한 2팔(페르세우스·방패-켄타우루스) + 약한 2팔
    pitch = math.radians(15.5)
    arms = np.zeros((H, W), np.float32); lanes = np.zeros((H, W), np.float32)
    for k, (off, amp) in enumerate(((0.0, 1.0), (math.pi, 1.0), (math.pi / 2, 0.45), (3 * math.pi / 2, 0.45))):
        th_arm = bar_ang + off + np.log(np.maximum(r, 0.05) / 0.22) / math.tan(pitch)
        dth = np.angle(np.exp(1j * (th - th_arm)))
        dist = dth * r
        w = 0.05 + 0.07 * r
        prof = np.exp(-(dist / w) ** 2) * sstep(0.16, 0.30, r) * np.exp(-np.clip(r - 0.72, 0, None) / 0.14)
        arms += amp * prof
        # 먼지띠 — 팔 안쪽(회전 방향 앞) 가장자리
        lanes += amp * np.exp(-((dist + w * 0.75) / (w * 0.30)) ** 2) * sstep(0.10, 0.25, r) * (r < 0.85)
    clump = np.clip(0.45 + 0.55 * n1 + 0.45 * n2, 0.02, None)
    arms *= clump
    # HII 분홍 매듭 + 젊은 별 무리 — 팔 위에 흩뿌림
    rng = np.random.default_rng(103)
    knots = np.zeros((H, W), np.float32)
    dens = arms / arms.sum()
    idx = rng.choice(arms.size, 420, p=dens.ravel())
    ky_, kx_ = idx // W, idx % W
    np.add.at(knots, (ky_, kx_), rng.uniform(0.5, 1.5, idx.size).astype(np.float32))
    knots = blur(knots, 1.8 * SS) * 60
    Eg = (disk * 0.45)[..., None] * col((0.78, 0.74, 0.76)) + (bulge * 2.4 + bar * 1.6)[..., None] * col((1.0, 0.82, 0.55))
    Eg += (arms * 0.75)[..., None] * col((0.55, 0.70, 1.0))
    Eg += knots[..., None] * col((1.0, 0.36, 0.58)) * 0.6
    tau = 1.3 * lanes * np.clip(0.6 + 0.6 * n1, 0, None) + 0.5 * np.clip(n2 - 0.4, 0, None) * disk * 2
    S = star_field(H, W, 2200, 104, density=(arms * 0.6 + disk * 0.3 + bulge) + 1e-4, fmin=0.12, fmax=1.6,
                   sigma=0.8)
    Eg = Eg * 0.85
    fade = sstep(1.05, 0.85, r) * edge_fade(H, W, 0.02, 0.02, 0.02, 0.02)
    return compose(Eg, S * 0.7, tau=tau, exposure=1.0, gas_cap=(0.46, 0.60), fade=fade)


def plate_andromeda():
    """M31 — 경사 77°, 큰 벌지, 10kpc 고리, 가까운 쪽(위) 먼지띠, M32·M110. 1024x512 (SS 2048x1024)."""
    W, H = 1024 * SS, 512 * SS
    yy, xx = grid(H, W)
    cx, cy = W * 0.50, H * 0.52
    Rg = W * 0.44
    inc = math.radians(77); pa = math.radians(-16)
    ci = math.cos(inc)
    x1 = (xx - cx) * math.cos(pa) + (yy - cy) * math.sin(pa)
    y1 = -(xx - cx) * math.sin(pa) + (yy - cy) * math.cos(pa)
    u = x1 / Rg; v = y1 / (Rg * ci)
    r = np.sqrt(u * u + v * v) + 1e-6
    th = np.arctan2(v, u)
    n1 = pnoise(H, W, 2.6, 111); n2 = pnoise(H, W, 2.0, 112)
    rb = np.sqrt((x1 / Rg) ** 2 + (y1 / (Rg * 0.62)) ** 2)
    bulge = np.exp(-(rb / 0.035) ** 0.75)
    disk = np.exp(-r / 0.24)
    ring = np.exp(-((r - 0.56) / 0.07) ** 2) + 0.5 * np.exp(-((r - 0.33) / 0.05) ** 2) + \
        0.35 * np.exp(-((r - 0.78) / 0.06) ** 2)
    pitch = math.radians(8)
    spiral = np.zeros((H, W), np.float32)
    for off in (0.0, math.pi):
        th_arm = off + np.log(np.maximum(r, 0.05) / 0.3) / math.tan(pitch)
        dth = np.angle(np.exp(1j * (th - th_arm)))
        spiral += np.exp(-((dth * r) / 0.04) ** 2)
    sf = (0.35 * ring + 0.25 * spiral * sstep(0.2, 0.35, r)) * np.clip(0.55 + 0.45 * n1 + 0.3 * n2, 0.05, None)
    sf *= np.exp(-np.clip(r - 0.9, 0, None) / 0.06)
    rng = np.random.default_rng(113)
    knots = np.zeros((H, W), np.float32)
    idx = rng.choice(sf.size, 380, p=(sf / sf.sum()).ravel())
    np.add.at(knots, (idx // W, idx % W), rng.uniform(0.5, 1.4, idx.size).astype(np.float32))
    knots = blur(knots, 1.3 * SS) * 40
    Eg = (bulge * 3.4)[..., None] * col((1.0, 0.86, 0.62)) + (disk * 0.85)[..., None] * col((0.92, 0.86, 0.78))
    Eg += (sf * 0.55)[..., None] * col((0.55, 0.70, 1.0)) + knots[..., None] * col((1.0, 0.40, 0.62)) * 0.45
    # 먼지띠 — 고리·나선을 따라, 가까운 쪽(v<0, 화면 위쪽)에서 벌지를 가로질러 또렷
    lanes = (np.exp(-((r - 0.52) / 0.035) ** 2) + np.exp(-((r - 0.34) / 0.03) ** 2) * 0.9 +
             np.exp(-((r - 0.70) / 0.03) ** 2) * 0.5 + 0.3 * spiral * sstep(0.25, 0.4, r))
    near = sstep(0.25, -0.35, v / np.maximum(r, 0.05))
    patch = np.clip(0.2 + 0.9 * pnoise(H, W, 3.0, 115, aniso=(1.0, 0.5)), 0, None)
    tau = 1.1 * blur(lanes * patch, 1.5 * SS) * (0.08 + 2.0 * near) * (r < 0.95)
    # M32 — 핵 남쪽(아래) 원반 가장자리 근처의 작고 밝은 타원은하
    m32 = np.exp(-(np.sqrt((xx - (cx + 0.02 * W)) ** 2 + ((yy - (cy + 0.13 * H)) * 1.15) ** 2) / (0.009 * W)) ** 0.8)
    # M110 — 북서(왼쪽 위) 멀리, 크고 흐린 길쭉한 타원은하
    mx, my = cx - 0.30 * W, cy - 0.33 * H
    a1 = math.radians(-35)
    ux = (xx - mx) * math.cos(a1) + (yy - my) * math.sin(a1); uy = -(xx - mx) * math.sin(a1) + (yy - my) * math.cos(a1)
    m110 = np.exp(-(np.sqrt((ux / (0.016 * W)) ** 2 + (uy / (0.009 * W)) ** 2)) ** 0.9)
    Eg += (m32 * 1.6 + m110 * 0.30)[..., None] * col((1.0, 0.86, 0.66))
    S = star_field(H, W, 1400, 114, density=disk + 0.3 * sf + 1e-4, fmin=0.1, fmax=1.2, sigma=0.8)
    fade = np.maximum(sstep(1.08, 0.88, r), sstep(1.0, 0.3, np.sqrt(((xx - mx) / (0.12 * W)) ** 2 + ((yy - my) / (0.10 * W)) ** 2)))
    fade *= edge_fade(H, W, 0.02, 0.02, 0.02, 0.02)
    return compose(Eg * 0.8, S * 0.5, tau=tau, exposure=1.0, gas_cap=(0.48, 0.62), fade=fade), \
        dict(m32=[round((cx + 0.02 * W) / SS), round((cy + 0.13 * H) / SS)], m110=[round(mx / SS), round(my / SS)],
             core=[round(cx / SS), round(cy / SS)])


def plate_cosmic_web():
    """우주 거대구조 — 워프한 보로노이 경계(필라멘트) + 꼭짓점(은하단). 큰 셀·작은 셀 2단."""
    from scipy.spatial import cKDTree
    W, H = 540 * SS, 960 * SS
    yy, xx = grid(H, W)
    rng = np.random.default_rng(121)
    Ecomb = np.zeros((H, W, 3), np.float32)
    galaxy_d = np.zeros((H, W), np.float32)
    for level, (nseed, wpx, amp, warpamp) in enumerate(((34, 2.6, 1.0, 50), (130, 1.3, 0.40, 20))):
        pts = np.c_[rng.uniform(-0.1 * W, 1.1 * W, nseed), rng.uniform(-0.1 * H, 1.1 * H, nseed)]
        wy = pnoise(H, W, 3.6, 122 + level) * warpamp * SS; wx = pnoise(H, W, 3.6, 124 + level) * warpamp * SS
        q = np.c_[(xx + wx).ravel(), (yy + wy).ravel()]
        d, i = cKDTree(pts).query(q, k=3)
        d = d.reshape(H, W, 3); i = i.reshape(H, W, 3)
        e = (d[..., 1] - d[..., 0]) * 0.5
        nd = (d[..., 2] - d[..., 0]) * 0.5
        # 필라멘트마다 굵기·밝기가 다르다 (두 셀 id 해시)
        hsh = ((np.minimum(i[..., 0], i[..., 1]) * 73856093) ^ (np.maximum(i[..., 0], i[..., 1]) * 19349663)) % 1000 / 1000.0
        bright = (0.25 + 0.75 * hsh ** 1.5).astype(np.float32)
        wv = wpx * SS * (0.6 + 0.8 * hsh)
        fil = np.exp(-(e / wv) ** 2) * bright
        halo = np.exp(-(e / (wv * 3.5)) ** 2) * bright * 0.18
        knot = np.exp(-(nd / (wv * 4.0)) ** 2) * np.exp(-(e / (wv * 4.0)) ** 2)
        mod = np.clip(0.6 + 0.5 * pnoise(H, W, 2.8, 126 + level), 0.1, None)
        Ecomb += amp * ((fil * 0.8 + halo) * mod)[..., None] * col((0.45, 0.40, 1.0))
        Ecomb += amp * (knot * 1.3)[..., None] * col((1.0, 0.82, 0.55))
        galaxy_d += amp * (fil ** 2 + 0.6 * knot)
    S = star_field(H, W, 450, 127, density=galaxy_d + 1e-4, fmin=0.2, fmax=1.5, sigma=0.8,
                   cols_w=[0.1, 0.2, 0.2, 0.25, 0.15, 0.1])
    fade = edge_fade(H, W, 0.12, 0.12)
    return compose(Ecomb * 0.26, S * 0.6, exposure=1.0, gamma=1.25, gas_cap=(0.30, 0.40), fade=fade, soft=0.8 * SS)


def plate_cmb():
    """우주배경복사 — 음향 피크가 있는 가우스 랜덤장. 청(차가움)·주황(뜨거움) LUT, 가장자리 페더."""
    W, H = 540 * SS, 960 * SS
    rng = np.random.default_rng(131)
    wn = rng.standard_normal((H, W)).astype(np.float32)
    F = np.fft.rfft2(wn)
    ky = np.fft.fftfreq(H)[:, None]; kx = np.fft.rfftfreq(W)[None, :]
    k = np.sqrt(kx ** 2 + ky ** 2) * W               # 가로 한 폭당 파수
    k[0, 0] = 1
    k1 = 7.5                                         # 첫 음향 피크 — 얼룩 크기 약 0.1 폭
    A = k ** -1.0 * (0.35 + 1.4 * np.exp(-((k - k1) / (0.45 * k1)) ** 2) + 0.7 * np.exp(-((k - 2.4 * k1) / (0.5 * k1)) ** 2)
                     + 0.45 * np.exp(-((k - 3.6 * k1) / (0.6 * k1)) ** 2)) * np.exp(-(k / (6.5 * k1)) ** 2)
    A[0, 0] = 0
    T = np.fft.irfft2(F * A, s=(H, W)).astype(np.float32)
    T = (T - T.mean()) / (T.std() + 1e-8)
    # 플랑크 지도 느낌의 발산 LUT (−: 깊은 청 → 0: 흐린 크림 → +: 주황·빨강)
    stops = [(-2.6, (0.02, 0.05, 0.28)), (-1.3, (0.08, 0.35, 0.80)), (-0.3, (0.55, 0.78, 0.95)),
             (0.2, (0.95, 0.88, 0.70)), (1.0, (1.0, 0.55, 0.16)), (2.0, (0.85, 0.18, 0.05)), (3.0, (0.45, 0.04, 0.02))]
    xs = np.array([s[0] for s in stops]); cs = np.array([s[1] for s in stops])
    rgb = np.dstack([np.interp(T, xs, cs[:, c]) for c in range(3)]).astype(np.float32)
    # 밝기 — 벽 전체가 빛나되 운석이 읽히게 인코딩 luma ≈0.25~0.40
    grey = rgb.mean(axis=2, keepdims=True)
    C = (rgb * 0.8 + grey * 0.2) * 0.50
    C = cap_luma(C, 0.32, 0.42)
    yy, xx = grid(H, W)
    ex = (xx / W - 0.5) / 0.5; ey = (yy / H - 0.5) / 0.5
    # D (R21-10) — 초타원(둥근 직사각형)은 화면에서 세로 띠의 좌우 가장자리가 드러났다 → 부드러운 타원 마스크
    rr = np.sqrt(ex ** 2 + ey ** 2)
    feather = sstep(1.0, 0.45, rr)
    C = np.clip(C * feather[..., None], 0, 1)
    return np.dstack([C, np.ones(C.shape[:2], np.float32)]).astype(np.float32)


def plate_helio_ribbon():
    """태양권계면 거품 벽 — 화면 폭을 가로지르는 호(볼록한 쪽이 위). 540x300 (SS 1080x600)."""
    W, H = 540 * SS, 300 * SS
    yy, xx = grid(H, W)
    R = 1.15 * W
    cx, cy = 0.5 * W, 0.22 * H + R
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) - R        # 0 = 벽, 음수 = 안쪽(아래)
    wy = pnoise(H, W, 3.9, 141) * 5 * SS; wx = pnoise(H, W, 3.9, 142) * 8 * SS
    dw = warp(d, wy, wx, mode="nearest")
    front = np.exp(-(dw / (3.0 * SS)) ** 2)                            # 종단 충격파·계면의 얇은 빛
    sheath = np.exp(np.clip(dw, None, 0) / (28 * SS)) * (dw < 0) * 0.8 + np.exp(-np.clip(dw, 0, None) / (6 * SS)) * (dw >= 0) * 0.35
    ang = np.arctan2(yy - cy, xx - cx) * R / W
    fil = np.clip(1 - np.abs(warp(pnoise(H, W, 2.8, 143, aniso=(1.0, 3.0), kmax=0.05), wy * 2, wx)), 0, 1) ** 4
    sheath *= np.clip(0.45 + 0.8 * fil + 0.3 * pnoise(H, W, 3.0, 144), 0, None)
    t = xx / W
    c1 = np.dstack([0.35 + 0.35 * t, 0.72 - 0.22 * t, np.ones_like(t)])        # 청록 → 보라
    E = (front * 1.2)[..., None] * c1 + (sheath * 0.45)[..., None] * c1
    # IBEX 리본 — 벽 한 구간이 더 밝은 좁은 띠
    rib = np.exp(-((t - 0.62) / 0.10) ** 2) * np.exp(-((dw + 6 * SS) / (5 * SS)) ** 2)
    E += (rib * 1.1)[..., None] * col((0.85, 0.9, 1.0))
    # D — 네 변 모두 검정으로 페더(좌우 끝의 사각 이음새 제거)
    fade = sstep(0.0, 0.10, yy / H) * sstep(0.0, 0.30, 1 - yy / H) * sstep(0.0, 0.10, xx / W) * sstep(0.0, 0.10, 1 - xx / W)
    return compose(E * 0.8, None, exposure=1.0, gas_cap=(0.40, 0.55), fade=fade), dict(
        arc_apex=[round(cx / SS), round((cy - R) / SS)], arc_radius=round(R / SS))


def plate_oort():
    """오르트 구름 — 얼음 혜성핵 원경(아래 = 멀어진 태양 쪽에서 비춘다) + 별이 된 태양. 거의 투명."""
    W, H = 540 * SS, 960 * SS
    yy, xx = grid(H, W)
    rng = np.random.default_rng(151)
    C = np.zeros((H, W, 3), np.float32); A = np.zeros((H, W), np.float32)
    sun = (0.30 * W, 0.94 * H)
    # 크기별 개수 (최종 px 지름)
    sizes = [rng.uniform(1.5, 2.6) for _ in range(40)] + [rng.uniform(3.5, 7) for _ in range(12)] + \
            [rng.uniform(10, 18) for _ in range(4)]
    for k, s in enumerate(sizes):
        x, y = rng.uniform(0.04, 0.96) * W, rng.uniform(0.06, 0.88) * H
        r0 = s * SS * 0.5
        R = int(r0 * 3 + 4)
        x0, y0 = int(x) - R, int(y) - R
        if x0 < 0 or y0 < 0 or x0 + 2 * R >= W or y0 + 2 * R >= H:
            continue
        py, px = np.mgrid[0:2 * R, 0:2 * R].astype(np.float32)
        dx, dy = px + x0 - x, py + y0 - y
        ang = np.arctan2(dy, dx)
        bumps = 1 + 0.22 * np.sin(3 * ang + k) + 0.12 * np.sin(5 * ang + 2 * k)
        el = 1.0 + rng.uniform(0, 0.5)
        rr = np.sqrt((dx / el) ** 2 + dy ** 2) / (r0 * bumps)
        body = sstep(1.0, 0.8, rr)
        # 태양 방향(아래 왼쪽)을 향한 면이 밝다
        lx, ly = sun[0] - x, sun[1] - y
        ln = math.hypot(lx, ly); lx, ly = lx / ln, ly / ln
        nz = np.sqrt(np.clip(1 - rr ** 2, 0, 1))
        shade = np.clip((dx / (r0 + 1e-3)) * lx + (dy / (r0 + 1e-3)) * ly + 0.35 * nz, 0, 1)
        c = (0.30 + 0.62 * shade) * body
        tint = col((0.78, 0.86, 1.0))[0, 0]
        C[y0:y0 + 2 * R, x0:x0 + 2 * R] = np.maximum(C[y0:y0 + 2 * R, x0:x0 + 2 * R], c[..., None] * tint * 0.75)
        A[y0:y0 + 2 * R, x0:x0 + 2 * R] = np.maximum(A[y0:y0 + 2 * R, x0:x0 + 2 * R], body * 0.95)
        if s > 7:   # 큰 핵만 옅은 코마
            coma = np.exp(-(np.sqrt(dx ** 2 + dy ** 2) / (r0 * 2.2)) ** 2) * 0.18
            C[y0:y0 + 2 * R, x0:x0 + 2 * R] += coma[..., None] * col((0.6, 0.8, 1.0))[0, 0]
    S = np.zeros((H, W, 3), np.float32)
    add_star(S, sun[0], sun[1], 22.0, (1.0, 0.94, 0.78), sig=2.2 * SS, halo=0.12, halo_r=9 * SS, spikes=4,
             spike_len=18 * SS, spike_w=0.8 * SS, spike_amp=0.25)
    haze = np.clip(pnoise(H, W, 3.6, 152) - 0.3, 0, None) * 0.004
    E = haze[..., None] * col((0.55, 0.65, 0.9))
    base = compose(E, S, exposure=1.0, fade=None, mode="add")
    Cb = base[..., :3]
    Cn = Cb * (1 - A[..., None]) + np.clip(C, 0, 1)
    fade = edge_fade(H, W, 0.06, 0.02)
    Cn = np.clip(Cn, 0, 1) * fade[..., None]
    return np.dstack([Cn, np.ones(Cn.shape[:2], np.float32)]).astype(np.float32), dict(
        sun=[round(sun[0] / SS), round(sun[1] / SS)])


def plate_quasar():
    """퀘이사 — 은하 전체보다 밝은 점광원 + 흐린 숙주은하 + 자홍·청록 제트(사선 -35°). 512 (SS 1024)."""
    W = H = 512 * SS
    yy, xx = grid(H, W)
    cx = cy = W / 2
    dx, dy = xx - cx, yy - cy
    r = np.sqrt(dx * dx + dy * dy) / W
    a = math.radians(-35)
    along = dx * math.cos(a) + dy * math.sin(a); perp = -dx * math.sin(a) + dy * math.cos(a)
    host_r = np.sqrt((along / W / 0.16) ** 2 + (perp / W / 0.10) ** 2)
    host = np.exp(-host_r ** 0.7 * 2.4) * np.clip(0.8 + 0.3 * pnoise(H, W, 2.8, 161), 0, None)
    E = (host * 0.55)[..., None] * col((1.0, 0.78, 0.60))
    # 제트 — 위(자홍), 아래(청록). 매듭 + 끝단 로브
    for sgn, c in ((1, (1.0, 0.30, 0.82)), (-1, (0.30, 0.92, 1.0))):
        s = along * sgn / W
        width = 0.006 + 0.028 * np.clip(s, 0, None)
        jet = np.exp(-(perp / W / width) ** 2) * (s > 0) * np.exp(-np.clip(s, 0, None) / 0.30)
        knots = 0.5 + 0.8 * np.clip(np.sin(s * 70) ** 8, 0, 1)
        jet *= knots * np.clip(0.7 + 0.4 * pnoise(H, W, 2.5, 162 + (sgn > 0)), 0, None)
        lobe_c = 0.40
        lobe = np.exp(-(((s - lobe_c) / 0.07) ** 2 + (perp / W / 0.055) ** 2)) * \
            np.clip(0.6 + 0.6 * pnoise(H, W, 2.8, 164 + (sgn > 0)), 0, None)
        E += (jet * 0.85 + lobe * 0.35)[..., None] * col(c)
    S = np.zeros((H, W, 3), np.float32)
    add_star(S, cx, cy, 40.0, (0.92, 0.95, 1.0), sig=2.4 * SS, halo=0.10, halo_r=10 * SS, spikes=4,
             spike_len=16 * SS, spike_w=0.8 * SS, spike_amp=0.18, spike_ang=math.radians(45))
    fade = sstep(0.50, 0.40, r)
    return compose(E * 0.9, S, exposure=1.0, gas_cap=(0.40, 0.55), star_cap=(0.80, 0.95), fade=fade)


# ══════════════════════════════ 자산 표 ══════════════════════════════
# 이름: (생성 함수, 최종 폭, 최종 높이, 예산 KB, lo 예산 KB, 메모)
PLATES = {
    "m42_far":         (plate_m42, 540, 960, 70, 24, "존16 오리온 성운 원경 — 트라페지움 중심(0.50W,0.52H). 존 전체에 0.35CH 이동"),
    "m42_dust":        (plate_m42_dust, 540, 960, 40, 14, "존16 앞 먼지 층 — 0.8CH 이동 + 기체 x 패럴랙스 0.06. tier>=1 이면 생략"),
    "horsehead_plate": (plate_horsehead, 540, 960, 80, 26, "존17 말머리 — IC434 붉은 커튼 + 아래 암흑운에서 솟은 말머리(전면 덮개, 존 경계 교차 페이드)"),
    "pillars_plate":   (plate_pillars, 540, 960, 90, 30, "존18 창조의 기둥 — 아래서 솟는 기둥 3개(전면 덮개, 교차 페이드)"),
    "pleiades_plate":  (plate_pleiades, 540, 960, 55, 18, "존14 플레이아데스 — 실제 좌표 9별(7별 스파이크) + 청색 반사성운"),
    "milkyway_river":  (plate_milkyway_river, 540, 960, 60, 20, "존13 견우직녀 — 세로 은하수 + 대균열, 베가·알타이르·데네브"),
    "milkyway_back":   (plate_milkyway_back, 1080, 600, 70, 24, "존20 뒤돌아본 우리 은하(막대나선). 존 동안 0.6배로 축소, 존21 에서 뒤 은하로 재사용"),
    "andromeda":       (plate_andromeda, 1024, 512, 75, 24, "존22 안드로메다 M31 — 폭 0.25→1.3CW 확대. 존21 에서 앞 점으로 재사용"),
    "cosmic_web":      (plate_cosmic_web, 540, 960, 70, 24, "존23 우주 거대구조 — 2층(원경 1배·근경 1.6배 확대)으로 같은 판 재사용 가능"),
    "cmb_plate":       (plate_cmb, 540, 960, 60, 20, "존27 관측 가능 우주 끝 — 빛의 벽, scale 0.6→1.4 로 다가옴. 가장자리 페더"),
    "helio_ribbon":    (plate_helio_ribbon, 540, 300, 25, 9, "존9 태양권계면 거품 벽 — 아래→위로 통과(화면 폭 = 판 폭)"),
    "oort_plate":      (plate_oort, 540, 960, 30, 11, "존10 오르트 구름 원경 — 얼음 혜성핵 + 아래쪽 별이 된 태양(0.30W,0.94H)"),
    "quasar":          (plate_quasar, 512, 512, 35, 12, "존24 퀘이사 — 점광원 + 사선 제트(보스 수직 빔과 구분). 중심 (256,256)"),
}

EXTRA = {}     # 판별 추가 기하(매니페스트용)


def _geo_path():
    os.makedirs(REN_DIR, exist_ok=True)
    return os.path.join(REN_DIR, "geo.json")


def geo_update(d):
    """판·블랙홀·항성 스크립트가 각자 구운 기하 정보를 한 파일에 모은다(매니페스트가 읽는다)."""
    p = _geo_path()
    g = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    g.update(d)
    json.dump(g, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def build_plates(names=None):
    res = {}
    for name, (fn, w, h, kb, kb_lo, note) in PLATES.items():
        if names and name not in names:
            continue
        print("==", name, flush=True)
        a = fn()
        if isinstance(a, tuple):
            a, extra = a
            EXTRA[name] = extra
        fin = resize_premul(a, w, h)
        p = os.path.join(PUB_DIR, name + ".webp")
        q, sz = save_webp(fin, p, kb)
        lo = resize_premul(fin, w // 2, h // 2)
        plo = os.path.join(PUB_DIR, name + "_lo.webp")
        ql, szl = save_webp(lo, plo, kb_lo, q0=70)
        print("   %dx%d q%d %.1fKB | lo q%d %.1fKB" % (w, h, q, sz / 1024, ql, szl / 1024), flush=True)
        res[name] = dict(q=q, sz=sz, ql=ql, szl=szl)
    geo_update({k: v for k, v in EXTRA.items()})
    return res


# ══════════════════════════════ 엽서 pc_13~pc_30 + pc_gold ══════════════════════════════
CARD = 96


def _card_from(name, box=None, gain=1.0, round_mask=True, fit=True, soft=0.0, porthole=False):
    """완성 webp 에서 잘라 96px 카드. 불투명(lighter) 판은 검정 = 투명으로 풀어 P6 엽서처럼 투명 배경 위 빛."""
    im = Image.open(os.path.join(PUB_DIR, name + ".webp"))
    add = im.mode == "RGB"
    a = np.asarray(im.convert("RGBA"), np.float32) / 255.0
    if box:
        x0, y0, x1, y1 = box
        a = a[y0:y1, x0:x1]
    h, w = a.shape[:2]
    s = CARD / max(h, w) if fit else CARD / min(h, w)
    r = resize_premul(a, max(1, round(w * s)), max(1, round(h * s)))
    out = np.zeros((CARD, CARD, 4), np.float32)
    rh, rw = r.shape[:2]
    oy, ox = (CARD - rh) // 2, (CARD - rw) // 2
    ys, xs = max(0, -oy), max(0, -ox)
    r = r[ys:ys + CARD, xs:xs + CARD]
    oy, ox = max(0, oy), max(0, ox)
    out[oy:oy + r.shape[0], ox:ox + r.shape[1]] = r
    C = out[..., :3] * out[..., 3:4] * gain
    if soft:
        C = blur(C, soft)
    if round_mask:
        yy, xx = grid(CARD, CARD)
        rr = np.sqrt((xx - CARD / 2 + 0.5) ** 2 + (yy - CARD / 2 + 0.5) ** 2) / (CARD / 2)
        m = sstep(1.0, 0.80, rr)
    else:
        m = np.ones((CARD, CARD), np.float32)
    C = np.clip(C * m[..., None], 0, 1)
    if add and porthole:
        # 화면 가득 찬 판(거대구조·CMB)은 둥근 창 — 알파 = 원 마스크(매끈해 싸다), 빛의 세부는 RGB 가
        rgb = np.where(m[..., None] > 1e-4, C / np.maximum(m[..., None], 1e-4), 0)
        return np.dstack([np.clip(rgb, 0, 1), m]).astype(np.float32)
    if add:
        return unpremul(C)
    al = out[..., 3] * m
    rgb = np.where(al[..., None] > 1e-4, C / np.maximum(al[..., None], 1e-4), 0)
    return np.dstack([np.clip(rgb, 0, 1), al]).astype(np.float32)


def _glow_card(E):
    return unpremul(np.clip(tone(E, 1.0), 0, 1))


def build_cards():
    cards, notes = {}, {}
    W = H = CARD
    yy, xx = grid(H, W)
    rr = np.sqrt((xx - W / 2 + 0.5) ** 2 + (yy - H / 2 + 0.5) ** 2)
    cards["pc_13"] = _card_from("milkyway_river", (0, 150, 540, 690), 1.3); notes["pc_13"] = "존13 견우직녀 — 은하수 사이 베가·알타이르"
    cards["pc_14"] = _card_from("pleiades_plate", (0, 172, 540, 712), 1.3); notes["pc_14"] = "존14 플레이아데스 — 일곱 자매 + 청색 성운"
    cards["pc_15"] = _card_from("betel_limb", (160, 300, 920, 720), 1.1, round_mask=True, fit=False); notes["pc_15"] = "존15 베텔게우스 불의 벽"
    cards["pc_16"] = _card_from("m42_far", (60, 290, 480, 710), 1.35); notes["pc_16"] = "존16 오리온 성운 — 트라페지움 코어 + 물고기 입"
    cards["pc_17"] = _card_from("horsehead_plate", (100, 380, 480, 760), 1.15); notes["pc_17"] = "존17 말머리 성운"
    cards["pc_18"] = _card_from("pillars_plate", (20, 110, 540, 630), 1.1); notes["pc_18"] = "존18 창조의 기둥"
    cards["pc_19"] = _card_from("bh_sgra", (110, 150, 530, 490), 1.15, round_mask=False); notes["pc_19"] = "존19 궁수자리 A* — 렌즈 원반"
    cards["pc_20"] = _card_from("milkyway_back", (40, 0, 1040, 600), 1.3, round_mask=False); notes["pc_20"] = "존20 뒤돌아본 우리 은하"
    # 21 은하간 공간 — 멀어진 우리 은하(아래 왼쪽) + 다가오는 안드로메다 점(위 오른쪽)
    c = np.zeros((H, W, 4), np.float32)
    mw = _card_from("milkyway_back", (40, 0, 1040, 600), 1.2, round_mask=False)
    an = _card_from("andromeda", (40, 60, 984, 460), 1.2, round_mask=False)
    for src, sz_, cx_, cy_ in ((mw, 40, 30, 70), (an, 26, 72, 26)):
        r_ = resize_premul(src, sz_, sz_)
        _over(c, r_, int(cx_ - sz_ / 2), int(cy_ - sz_ / 2))
    cards["pc_21"] = c; notes["pc_21"] = "존21 은하간 공간 — 뒤의 우리 은하, 앞의 안드로메다"
    cards["pc_22"] = _card_from("andromeda", (40, 40, 984, 480), 1.25, round_mask=False); notes["pc_22"] = "존22 안드로메다 + M32·M110"
    cards["pc_23"] = _card_from("cosmic_web", (0, 210, 540, 750), 2.0, soft=0.5, porthole=True); notes["pc_23"] = "존23 우주 거대구조 필라멘트"
    cards["pc_24"] = _card_from("quasar", (96, 96, 416, 416), 1.2, round_mask=False); notes["pc_24"] = "존24 퀘이사 — 점광원 + 두 제트"
    cards["pc_25"] = _card_from("bh_ton", (150, 200, 618, 560), 1.3, round_mask=False); notes["pc_25"] = "존25 TON 618 — 자홍 강착원반"
    # 26 부츠 초공동 — 가운데가 텅 빈 은하 고리
    rng = np.random.default_rng(261)
    E = np.zeros((H, W, 3), np.float32)
    for _ in range(70):
        ang = rng.uniform(0, 2 * math.pi); rad = rng.normal(38, 5)
        add_star(E, W / 2 + math.cos(ang) * rad, H / 2 + math.sin(ang) * rad, rng.uniform(0.25, 0.8),
                 tuple(STAR_COLS[rng.integers(2, 6)]), sig=0.7)
    cards["pc_26"] = _glow_card(E * 1.2); notes["pc_26"] = "존26 부츠 초공동 — 은하 없는 빈터를 두른 은하 고리"
    cards["pc_27"] = _card_from("cmb_plate", (0, 210, 540, 750), 1.25, soft=0.7, porthole=True); notes["pc_27"] = "존27 관측 가능 우주 끝 — 우주배경복사"
    # 28 마지막 별 — 프록시마를 호박색으로 재그레이드, 둘레는 텅 빔
    px = _card_from("proxima", (40, 40, 344, 344), 1.0, round_mask=True)
    px[..., :3] = np.clip(px[..., :3] * np.array([1.0, 0.78, 0.45], np.float32) * 0.85, 0, 1)
    c = np.zeros((H, W, 4), np.float32)
    _over(c, resize_premul(px, 56, 56), 20, 20)
    cards["pc_28"] = c; notes["pc_28"] = "존28 마지막 별 — 호박빛 적색왜성 하나"
    # 29 블랙홀 시대 — 작은 블랙홀(가는 광자 고리) + 증발하는 옅은 빛
    E = np.zeros((H, W, 3), np.float32)
    ring = np.exp(-((rr - 15) / 1.1) ** 2)
    E += (ring * 0.9)[..., None] * col((1.0, 0.62, 0.30))
    E += (np.exp(-np.clip(rr - 15, 0, None) / 12) * (rr > 15) * 0.12)[..., None] * col((0.7, 0.6, 1.0))
    for (dx, dy, f) in ((-30, -26, 0.9), (28, 30, 0.6), (33, -20, 0.5)):
        add_star(E, W / 2 + dx, H / 2 + dy, f, (0.85, 0.8, 1.0), sig=0.9, halo=0.15, halo_r=3)
    g = _glow_card(E)
    g[..., 3] = np.maximum(g[..., 3], (rr < 14.5).astype(np.float32))      # 그림자는 불투명 검정
    g[..., :3] *= np.where(rr < 14.5, 0, 1)[..., None]
    cards["pc_29"] = g; notes["pc_29"] = "존29 블랙홀 시대 — 증발하는 작은 블랙홀"
    # 30 열적 죽음 — 색이 사라진 회색 안개 원
    E = (np.exp(-(rr / 30) ** 2) * 0.12 + 0.02 * np.clip(pnoise(H, W, 3.0, 301), -1, 1))[..., None] * col((0.8, 0.8, 0.8))
    cards["pc_30"] = _glow_card(np.clip(E, 0, None)); notes["pc_30"] = "존30 열적 죽음 — 회색 평형"
    # 황금 엽서 — '창백한 푸른 점' 오마주(저작권 사진 미사용, 구성만 오마주): 흩어진 햇빛 띠 속 1.5px 푸른 점
    # 2026-09-29 (D, R21-14) — 예전 판은 배경(선형 0.035 → 인코딩 ≈0.2)과 넓은 띠가 베이지·갈색 세로 줄무늬 흐림으로 보였고
    # 푸른 점이 1.5px 라 안 보였다. 거의 검은 우주 + 가는 사선 햇빛 띠(가운데만 밝게) + 가운데 띠 속 또렷한 푸른 점(글로우)
    c = np.zeros((H, W, 3), np.float32)
    c += (0.0016 + 0.0010 * np.clip(pnoise(H, W, 2.0, 302), -1, 1))[..., None] * col((0.6, 0.55, 0.7))
    sl = 0.32                                              # 띠 기울기(가로 이동 / 세로 1px)
    for off, wd, amp in ((-26, 2.6, 0.05), (2, 4.2, 0.11), (27, 2.2, 0.04)):
        core = np.exp(-((xx - W / 2 - off - sl * (yy - H / 2)) / wd) ** 2)
        wide = np.exp(-((xx - W / 2 - off - sl * (yy - H / 2)) / (wd * 3.2)) ** 2)
        c += ((core * amp + wide * amp * 0.25) * (0.75 + 0.25 * np.clip(pnoise(H, W, 2.4, 303 + off), -1, 1)))[..., None] * col((1.0, 0.80, 0.55))
    dot_y = H / 2 + 12
    dot_x = W / 2 + 2 + sl * (dot_y - H / 2)
    add_star(c, dot_x, dot_y, 0.10, (0.25, 0.55, 1.0), sig=5.0)            # 청색 글로우
    add_star(c, dot_x, dot_y, 0.9, (0.30, 0.62, 1.0), sig=1.3)             # 점 본체(지름 ≈3px, 청색)
    frame = sstep(3.5, 1.5, np.minimum.reduce([xx, yy, W - 1 - xx, H - 1 - yy]))
    C = np.clip(tone(c, 1.0), 0, 1)
    C = C * (1 - frame[..., None]) + col((0.96, 0.78, 0.38))[0, 0] * frame[..., None]
    corner = np.minimum.reduce([np.hypot(xx - 6, yy - 6), np.hypot(xx - (W - 7), yy - 6), np.hypot(xx - 6, yy - (H - 7)),
                                np.hypot(xx - (W - 7), yy - (H - 7))])
    inside_c = ((xx >= 6) & (xx <= W - 7)) | ((yy >= 6) & (yy <= H - 7))
    al = np.where(inside_c, 1.0, sstep(6.8, 5.8, corner)).astype(np.float32)
    cards["pc_gold"] = np.dstack([C, al]).astype(np.float32)
    notes["pc_gold"] = "황금 엽서 '지구 ★' — 창백한 푸른 점 오마주(흩어진 햇빛 띠 속 푸른 점 %s, 금테 둥근 카드)" % [round(dot_x), round(dot_y)]
    res = {}
    for k, a in cards.items():
        p = os.path.join(PUB_DIR, k + ".webp")
        q, sz = save_webp(a, p, 5, q0=80, aq=80)
        res[k] = dict(q=q, sz=sz, note=notes[k])
        print("  %s q%d %.1fKB" % (k, q, sz / 1024))
    return res


def _over(dst, src, x, y):
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


# ══════════════════════════════ 게임 모의 프레임 · 대비 검사 · 매니페스트 ══════════════════════════════
ZONE_BG = {9: ('#030304', '#060608', '#08080c'), 10: ('#040408', '#080810', '#101220'),
           11: ('#0a0606', '#180c08', '#2a1810'), 12: ('#020208', '#080d18', '#101a30'),
           13: ('#080a18', '#10142a', '#080a18'), 14: ('#040c1c', '#081830', '#0c2848'),
           15: ('#1a0608', '#260a08', '#2a1208'), 16: ('#100208', '#280412', '#481020'),
           17: ('#1a0008', '#2a0012', '#1a0820'), 18: ('#040608', '#080c10', '#101820'),
           19: ('#020005', '#040008', '#080010'), 20: ('#020208', '#040618', '#0a0a30'),
           21: ('#000000', '#020205', '#04040a'), 22: ('#0a0410', '#180a20', '#2a1438'),
           23: ('#020410', '#040820', '#081438'), 24: ('#180020', '#2a0840', '#0a1840'),
           25: ('#1c0408', '#2c0810', '#08020a'), 26: ('#000005', '#000010', '#000018'),
           27: ('#1a0008', '#2a0410', '#180412'), 28: ('#1a0a05', '#241008', '#180c06'),
           29: ('#0a0418', '#180828', '#220a32'), 30: ('#080808', '#101010', '#181818')}


def _hex(c):
    return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255


def _bg(W, H, zi, seed):
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    a, b, c = (_hex(x) for x in ZONE_BG[zi])
    top = np.where(t < 0.5, 1 - t * 2, 0); mid = 1 - np.abs(t - 0.5) * 2; bot = np.where(t > 0.5, (t - 0.5) * 2, 0)
    img = top[..., None] * a + mid[..., None] * b + bot[..., None] * c
    img = np.broadcast_to(img, (H, W, 3)).copy()
    S = star_field(H, W, 160, seed, fmin=0.2, fmax=1.5, sigma=0.8)
    img = np.clip(img + tone(S, 1.0) * 0.8, 0, 1)
    return np.dstack([img, np.ones((H, W), np.float32)])


def _place(dst, name, cx, cy, w, alpha=1.0, rot=0, tint=None, flip=False, h=None):
    """게임처럼 그린다 — 불투명 RGB 판은 'lighter'(가산), RGBA 는 source-over."""
    im = Image.open(os.path.join(PUB_DIR, name + ".webp"))
    add = im.mode == "RGB"
    im = im.convert("RGBA")
    if rot:
        im = im.rotate(rot, expand=True)
    if flip:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    hh = h if h else int(round(w * im.size[1] / im.size[0]))
    im = im.resize((max(1, int(w)), max(1, int(hh))), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255
    if tint is not None:
        a[..., :3] *= np.array(tint, np.float32)
    x0, y0 = int(cx - a.shape[1] / 2), int(cy - a.shape[0] / 2)
    H_, W_ = dst.shape[:2]
    xs, ys = max(0, -x0), max(0, -y0)
    xe, ye = min(a.shape[1], W_ - x0), min(a.shape[0], H_ - y0)
    if xe <= xs or ye <= ys:
        return
    s = a[ys:ye, xs:xe]
    d = dst[y0 + ys:y0 + ye, x0 + xs:x0 + xe]
    if add:
        d[..., :3] = np.clip(d[..., :3] + s[..., :3] * alpha, 0, 1)
    else:
        sa = s[..., 3:4] * alpha
        d[..., :3] = s[..., :3] * sa + d[..., :3] * (1 - sa)


def _rel_lum(rgb):
    return enc2lin(rgb) @ np.array([0.2126, 0.7152, 0.0722], np.float32)


def game_mocks(shots, dpr=2):
    """존별로 판을 런타임 배치(zoneT≈0.5)대로 412x915 프레임에 그리고, 운석 50개(P6 림 스프라이트)를 찍어
    운석(몸통·위험 림·검은 윤곽 가운데 하나)과 주변 배경의 국소 휘도 대비를 잰다. 게임의 dim 오버레이 0.2 반영."""
    W, H = 412 * dpr, 915 * dpr
    CW, CH = W, H
    R = 15 * dpr
    mets = []
    for k in "abc":
        p = os.path.join(PUB_DIR, "meteor_%s_rim.webp" % k)
        if not os.path.exists(p):
            continue
        m = np.asarray(Image.open(p).convert("RGBA").resize((2 * R, 2 * R), Image.LANCZOS), np.float32) / 255
        lum = _rel_lum(m[..., :3])
        rim = (m[..., 3] > 0.5) & (lum > 0.35)
        dark = (m[..., 3] > 0.5) & (lum < 0.02)
        body = (m[..., 3] > 0.5) & ~rim & ~dark
        mets.append((m, body, rim, dark))
    shadow_r = GEO_CACHE.get("bh_sgra", {}).get("shadow_r_px", 69.3)
    reach = max(CW, CH) * 1.1
    jet_w = 2 * reach * math.tan(0.14)
    scenes = {
        9: [("helio_ribbon", 0.5, 0.42, 1.0, {})],
        10: [("oort_plate", 0.5, 0.5, 1.0, {})],
        11: [("proxima", 0.5, 0.24, 0.62, {}), ("proxima_b", 0.30, 0.62, 0.62, dict(alpha=0.85))],
        12: [("star_sirius", 0.5, 0.30, 0.9, {})],
        13: [("milkyway_river", 0.5, 0.45, 1.0, {})],
        14: [("pleiades_plate", 0.5, 0.45, 1.0, {})],
        15: [("betel_limb", 0.0, 0.5, None, dict(rot=-90, h=CH, wpx=CH * 720 / 1080, cxpx="betel"))],
        16: [("m42_far", 0.5, 0.45, 1.0, {}), ("m42_dust", 0.5, 0.55, 1.0, {})],
        17: [("horsehead_plate", 0.5, 0.40, 1.0, {})],
        18: [("pillars_plate", 0.5, 0.45, 1.0, {})],
        19: [("bh_jet", 0.5, 0.42 - 0.5 * reach / CH, None, dict(wpx=jet_w, h=reach)),
             ("bh_jet", 0.5, 0.42 + 0.5 * reach / CH, None, dict(wpx=jet_w, h=reach, flip=True)),
             ("bh_sgra", 0.5, 0.42, 640 * (32 * dpr / shadow_r) / W, {}),
             ("bh_shimmer", 0.5, 0.42, 0.55, dict(alpha=0.8, hscale=0.14))],
        20: [("milkyway_back", 0.5, 0.30, 0.9, {})],
        21: [("milkyway_back", 0.30, 0.82, 0.36, {}), ("andromeda", 0.70, 0.18, 0.25, {})],
        22: [("andromeda", 0.5, 0.35, 1.0, {})],
        23: [("cosmic_web", 0.5, 0.5, 1.6, dict(alpha=0.6)), ("cosmic_web", 0.5, 0.5, 1.0, {})],
        24: [("quasar", 0.5, 0.30, 0.9, {})],
        25: [("bh_ton", 0.5, 0.02, 2.3, {})],
        26: [],
        27: [("cmb_plate", 0.5, 0.5, 1.0, {})],
        28: [("proxima", 0.5, 0.28, 0.5, dict(alpha=0.7, tint=(1.0, 0.78, 0.45)))],
        29: [],
        30: [],
    }
    out = {}
    tiles = []
    rs = np.random.default_rng(11)
    for zi, items in scenes.items():
        s = _bg(W, H, zi, 900 + zi)
        for name, fx, fy, fw, kw in items:
            kw = dict(kw)
            w = kw.pop("wpx", None) or fw * W
            if kw.pop("cxpx", None) == "betel":
                # 90° 돌려 왼쪽 가장자리에 붙인다 — 림 꼭대기가 화면 폭 25% 에 오게
                apex_from_edge = (720 - 470) * (CH / 1080)
                cx = 0.25 * W - apex_from_edge + (CH * 720 / 1080) / 2
                _place(s, name, cx, fy * H, CH * 720 / 1080, rot=-90, h=CH)
                continue
            hs = kw.pop("hscale", None)
            h = kw.pop("h", None)
            if hs:
                h = w * hs
            _place(s, name, fx * W, fy * H, w, h=h, **kw)
        s[..., :3] *= 0.8
        bgonly = s.copy()
        ratios = []
        cr = lambda a_, b_: (max(a_, b_) + 0.05) / (min(a_, b_) + 0.05)
        for i in range(50):
            m, mb, mr, md = mets[i % len(mets)]
            x = int(rs.uniform(R, W - 3 * R)); y = int(rs.uniform(R, H - 3 * R))
            patch = bgonly[y - 6:y + 2 * R + 6, x - 6:x + 2 * R + 6]
            ring = np.ones(patch.shape[:2], bool); ring[6:-6, 6:-6] = False
            reg = s[y:y + 2 * R, x:x + 2 * R]
            reg[..., :3] = m[..., :3] * m[..., 3:4] + reg[..., :3] * (1 - m[..., 3:4])
            L_bg = float(_rel_lum(patch[..., :3][ring]).mean())
            vals = [float(_rel_lum(reg[..., :3][k]).mean()) for k in (mb, mr, md) if k.any()]
            ratios.append(float(max(cr(v, L_bg) for v in vals)))
        out["z%d" % zi] = dict(min=round(min(ratios), 2), p10=round(float(np.percentile(ratios, 10)), 2),
                               median=round(float(np.median(ratios)), 2))
        tiles.append((zi, resize_premul(s, 206, 457)))
    cols = 11
    rows = (len(tiles) + cols - 1) // cols
    big = Image.new("RGB", (cols * 208, rows * 470), (30, 30, 30))
    d = ImageDraw.Draw(big)
    for i, (zi, t) in enumerate(tiles):
        x, y = (i % cols) * 208, (i // cols) * 470
        big.paste(to_img(t).convert("RGB"), (x, y + 12))
        v = out["z%d" % zi]
        d.text((x + 3, y), "z%d min %.1f" % (zi, v["min"]), fill=(255, 230, 120) if v["min"] >= 3 else (255, 80, 80))
    big.save(os.path.join(shots, "game_mock_contrast.png"))
    return out


GEO_CACHE = {}


def contact_sheet(names, shots):
    tiles = []
    for n in names:
        im = Image.open(os.path.join(PUB_DIR, n + ".webp"))
        add = im.mode == "RGB"
        im = im.convert("RGBA")
        s = 300 / max(im.size)
        im = im.resize((max(1, int(im.size[0] * s)), max(1, int(im.size[1] * s))), Image.LANCZOS)
        base = Image.new("RGBA", (304, 318), (12, 12, 22, 255))
        chk = Image.new("RGBA", im.size, (0, 0, 0, 255))
        for yy_ in range(0, im.size[1], 16):
            for xx_ in range(0, im.size[0], 16):
                if (xx_ // 16 + yy_ // 16) % 2:
                    chk.paste((34, 34, 48, 255), (xx_, yy_, min(xx_ + 16, im.size[0]), min(yy_ + 16, im.size[1])))
        if add:
            a = np.asarray(im, np.float32)[..., :3] / 255
            c = np.asarray(chk, np.float32)[..., :3] / 255
            chk = Image.fromarray((np.clip(a + c, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
        else:
            chk.alpha_composite(im)
        base.paste(chk, ((304 - im.size[0]) // 2, 16 + (300 - im.size[1]) // 2))
        ImageDraw.Draw(base).text((3, 2), n + (" [lighter]" if add else ""), fill=(255, 230, 120))
        tiles.append(base)
    cols = 6
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 306, rows * 320), (40, 40, 40))
    for i, t in enumerate(tiles):
        sheet.paste(t.convert("RGB"), ((i % cols) * 306, (i // cols) * 320))
    sheet.save(os.path.join(shots, "contact_p7.png"))


def cards_sheet(shots):
    names = ["pc_%02d" % i for i in range(13, 31)] + ["pc_gold"]
    sheet = Image.new("RGB", (len(names) * 100, 112), (18, 18, 28))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        im = Image.open(os.path.join(PUB_DIR, n + ".webp")).convert("RGBA")
        sheet.paste(im, (i * 100 + 2, 14), im)
        d.text((i * 100 + 4, 1), n, fill=(255, 230, 120))
    sheet.save(os.path.join(shots, "cards_p7.png"))


ZONE_ART = {
    "9": ["helio_ribbon"], "10": ["oort_plate"], "11": ["proxima", "proxima_b"], "12": ["star_sirius"],
    "13": ["milkyway_river"], "14": ["pleiades_plate"], "15": ["betel_limb"], "16": ["m42_far", "m42_dust"],
    "17": ["horsehead_plate"], "18": ["pillars_plate"], "19": ["bh_sgra", "bh_shimmer", "bh_jet"],
    "20": ["milkyway_back"], "21": ["milkyway_back", "andromeda"], "22": ["andromeda"], "23": ["cosmic_web"],
    "24": ["quasar"], "25": ["bh_ton", "bh_shimmer"], "26": [], "27": ["cmb_plate"], "28": ["proxima"], "29": [], "30": [],
}


def write_manifest(manifest, shots, contrast):
    import spacez_blackhole as bh
    sys.path.insert(0, os.path.join(HERE, "blender"))
    import spacez_stars as st
    geo = json.load(open(_geo_path(), encoding="utf-8")) if os.path.exists(_geo_path()) else {}
    table = {}
    for n, (fn, w, h, kb, kb_lo, note) in PLATES.items():
        table[n] = (kb, kb_lo, note)
    for n, (fn, kb, kb_lo, note) in bh.BH_ASSETS.items():
        table[n] = (kb, kb_lo, note)
    for n, (fn, kb, kb_lo, note) in st.STAR_ASSETS.items():
        table[n] = (kb, kb_lo, note)
    draw_rules = {
        "m42_far": "far 층: 폭 = CW, 존 동안 0.35CH 아래로 이동 + 기체 x 패럴랙스 0.02. 'lighter'",
        "m42_dust": "near 층: 폭 = CW, 0.8CH 이동 + 패럴랙스 0.06, source-over. tier>=1 이면 생략",
        "horsehead_plate": "폭 = CW, source-over(암흑운이 뒤를 가린다). 존 경계 zoneTransitionT 로 알파 교차 페이드",
        "pillars_plate": "폭 = CW, source-over(기둥이 뒤를 가린다). 존 경계 교차 페이드",
        "bh_sgra": "drawImage 1회. 스케일 = eventR / shadow_r_px (검은 그림자 가장자리 = 판정 반지름). 중심 = 판 중심",
        "bh_ton": "스케일은 자유(거대 호) — 중심을 화면 위쪽 밖에 두어 원반 아랫호만 걸리게",
        "bh_shimmer": "'lighter', 알파 0.6~0.8. translate→rotate(t*0.15)→scale(1, cos(inc)) 후 원반 바깥 지름 = 2·disk_out_px(스케일 적용)",
        "bh_jet": "'lighter'. 위 제트: drawImage(jet, cx-REACH·tan(0.14), cy-REACH, 2·REACH·tan(0.14), REACH). 아래 제트는 scale(1,-1)",
        "betel_limb": "source-over. 90° 돌려 아래 가장자리를 화면 옆에 붙이고 limb_apex 가 화면 폭 25% 에 오게",
        "proxima": "source-over, 원반 반지름 r → 그리기 폭 = 2r / disk_frac. 존28 은 globalAlpha 0.7 + 호박 틴트",
        "proxima_b": "source-over, szFlyby 반지름 r → 폭 2r / disk_frac",
        "star_sirius": "'lighter', 중심 = 판 중심",
        "andromeda": "'lighter', 폭 0.25→1.3CW 확대",
        "milkyway_back": "'lighter', 존20 동안 1 → 0.6 배 축소",
        "cmb_plate": "'lighter', scale 0.6→1.4",
        "cosmic_web": "'lighter', 2층 = 같은 판을 1.0CW(알파 1) + 1.6CW(알파 0.6, 느린 이동)로",
    }
    assets = []
    tot = 0.0; tot_lo = 0.0; zone_bytes = {}
    decode = {}
    for n, (kb, kb_lo, note) in table.items():
        p = os.path.join(PUB_DIR, n + ".webp"); plo = os.path.join(PUB_DIR, n + "_lo.webp")
        im = Image.open(p)
        add = im.mode == "RGB"
        a = np.asarray(im.convert("RGBA"), np.float32) / 255
        sz = os.path.getsize(p) / 1024; szl = os.path.getsize(plo) / 1024
        tot += sz; tot_lo += szl
        mx, mean, p99 = luma_stats(a)
        decode[n] = round(im.size[0] * im.size[1] * 4 / 1048576, 2)
        e = dict(path="public/assets/spacez/z/%s.webp" % n, px=list(im.size), kb=round(sz, 1), budget_kb=kb,
                 lo=dict(path="public/assets/spacez/z/%s_lo.webp" % n, px=[im.size[0] // 2, im.size[1] // 2],
                         kb=round(szl, 1), budget_kb=kb_lo),
                 blend="lighter" if add else "source-over", alpha="없음(검정=투명, 가산)" if add else "스트레이트 알파",
                 alpha_bbox=alpha_bbox(a) if not add else None, luma=dict(max=mx, mean=mean, p99=p99),
                 decode_mb=decode[n], draw=draw_rules.get(n, "중심 기준 drawImage — 폭은 존 연출에 맞춤"), notes=note)
        if n in geo:
            e["geometry"] = geo[n]
        assets.append(e)
    cards = []
    for n in ["pc_%02d" % i for i in range(13, 31)] + ["pc_gold"]:
        p = os.path.join(PUB_DIR, n + ".webp")
        sz = os.path.getsize(p) / 1024
        tot += sz
        cards.append(dict(path="public/assets/spacez/z/%s.webp" % n, px=[CARD, CARD], kb=round(sz, 1), budget_kb=5,
                          notes=CARD_NOTES.get(n, "")))
    zone_dec = {z: round(sum(decode.get(n, 0) for n in set(v)), 2) for z, v in ZONE_ART.items()}
    zone_kb = {z: round(sum(os.path.getsize(os.path.join(PUB_DIR, n + ".webp")) / 1024 for n in set(v)), 1)
               for z, v in ZONE_ART.items()}
    p6_total = None
    p6m = os.path.join(os.path.dirname(manifest), "p6_assets.json")
    if os.path.exists(p6m):
        try:
            p6_total = json.load(open(p6m, encoding="utf-8"))["summary"]["total_kb"]
        except Exception:
            p6_total = None
    man = dict(
        generated_by="scripts/spacez_plates.py all (+ spacez_blackhole.py, blender/spacez_stars.py)",
        summary=dict(p7_total_kb=round(tot, 1), p7_main_plus_cards_kb=round(tot, 1), p7_lo_kb=round(tot_lo, 1),
                     p6_total_kb=p6_total, p6_plus_p7_kb=round(tot + tot_lo + (p6_total or 0), 1),
                     budget_kb=2048, note="p6_total_kb 는 P6 매니페스트 값(본판+lo+엽서). P7 은 본판·엽서(p7_total) + lo(p7_lo_kb)"),
        zone_art=ZONE_ART,
        zone_preload_kb=zone_kb,
        zone_decode_mb=zone_dec,
        postcards_lazy=["pc_%02d" % i for i in range(13, 31)] + ["pc_gold"],
        conventions=dict(
            blend="blend='lighter' 인 판은 알파 없는 불투명 RGB(검정 = 투명). ctx.globalCompositeOperation='lighter' 로 그린다 — 알파 채널이 없어 용량이 1/4~1/8. 'source-over' 판만 스트레이트 알파(암흑 성운·기둥·항성 몸통·블랙홀 그림자처럼 뒤를 가려야 하는 것)",
            luma_cap="가스 인코딩 luma ≤0.52(판), 별 코어 ≤0.90, 블랙홀·항성 몸통 ≤0.80",
            edges="세로 판(540x960)은 위·아래 가장자리가 알파 0/검정으로 페이드 — 화면보다 짧아 스크롤로 흘려도 경계가 안 보인다",
            lo="_lo = 정확히 절반 해상도, 같은 프레임. 모든 px 좌표 x0.5",
            path="/assets/spacez/z/<이름>.webp + 기존 BV(?v=빌드스탬프)",
            determinism="판 안의 별·구조는 굽는 시점에 고정(시드). 런타임 RNG 사용 없음 — 8인 레이스 결정성과 무관"),
        contrast=contrast,
        assets=assets,
        postcards=cards,
    )
    json.dump(man, open(manifest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("manifest ->", manifest, "P7 main+cards %.1fKB, lo %.1fKB" % (tot, tot_lo))
    return man


CARD_NOTES = {}


if __name__ == "__main__":
    args = sys.argv[1:]
    mode = args[0] if args else "all"
    rest = args[1:]
    shots = os.path.join(ROOT, "scripts", "og-assets", "spacez_z7")
    manifest = os.path.join(REN_DIR, "p7_assets.json")
    if "--shots" in rest:
        i = rest.index("--shots"); shots = rest[i + 1]; rest = rest[:i] + rest[i + 2:]
    if "--manifest" in rest:
        i = rest.index("--manifest"); manifest = rest[i + 1]; rest = rest[:i] + rest[i + 2:]
    os.makedirs(shots, exist_ok=True)
    if mode == "all":
        build_plates()
        import spacez_blackhole as _bh
        _bh.build()
        import subprocess
        subprocess.run([sys.executable, os.path.join(HERE, "blender", "spacez_stars.py"), "all"], check=True)
    if mode == "plates":
        build_plates(rest or None)
    if mode in ("cards", "all"):
        r = build_cards()
        CARD_NOTES.update({k: v["note"] for k, v in r.items()})
        cards_sheet(shots)
    if mode in ("manifest", "all"):
        if not CARD_NOTES:
            CARD_NOTES.update({k: v["note"] for k, v in build_cards().items()})
            cards_sheet(shots)
        GEO_CACHE.update(json.load(open(_geo_path(), encoding="utf-8")) if os.path.exists(_geo_path()) else {})
        names = list(PLATES) + ["bh_sgra", "bh_ton", "bh_shimmer", "bh_jet", "betel_limb", "proxima", "proxima_b",
                                "star_sirius"]
        contact_sheet(names, shots)
        con = game_mocks(shots)
        json.dump(con, open(os.path.join(shots, "contrast.json"), "w"), indent=1)
        print(json.dumps(con))
        write_manifest(manifest, shots, con)
