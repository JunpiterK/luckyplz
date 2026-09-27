# -*- coding: utf-8 -*-
"""Space-Z v5 블랙홀 — 슈바르츠실트 광선추적으로 미리 굽는 렌즈 원반 스프라이트 (2026-09-28, P7).

존 19 궁수자리 A*·존 25 TON 618. 매 프레임 캔버스로 그리던 평면 타원 원반 + 검은 원을
'원반이 그림자 위아래로 휘어 감기는' 실제 렌즈 모습으로 바꾼다. 픽셀 단위 렌즈를 런타임에서
계산하지 않는다(getImageData 금지) — 여기서 한 번 굽고 게임은 drawImage 1회.

물리 (G=c=M=1, 사건의 지평선 r=2, 광자구 r=3, 그림자 반지름 b_c=3√3≈5.196, ISCO r=6)
  - 광선 궤도: 비네 방정식 u'' + u = 3u² (u=1/r) 를 충격 매개변수 b 별로 RK4 적분해 표로 만든다
    (관측자 = 무한대, u(0)=0, u'(0)=1/b). u≥0.5 이면 흡수(그림자), u 가 다시 0 이 되면 탈출
  - 픽셀 (X,Y) → b=√(X²+Y²), 궤도면 방향 α=atan2(Y,X). 궤도면 안 각 φ 에서 광자 위치의 원반면(z=0)
    교차각은 해석적으로 φ_k = δ+π/2+kπ. 교차 순서 k=0(1차 상), 1(원반 뒷면이 그림자 위로 감긴 상),
    2(광자 고리). 광학적으로 두꺼운 원반이라 앞 교차가 뒤를 대부분 가린다
  - 원반: 케플러 원운동(순행, 위에서 반시계), r_in=6(ISCO) ~ r_out. 방출 I ∝ r⁻³(1-√(r_in/r)),
    온도 T ∝ I^¼. 도플러 δ=1/(γ(1-β cosψ)), β=√(1/(r-2)), 중력 적색편이 √(1-2/r)
    → 관측 밝기 ∝ g^p. 명세 '다가오는 쪽 1.8배' 에 맞춰 p=0.8 (g⁴ 는 10배가 넘어 게임 화면에서 반쪽이 사라진다)
  - 배경 별: 탈출 광선의 무한대 방향으로 천구 별 지도를 샘플 → 그림자 둘레 아인슈타인 호.
    그림자 주변 원반(약 3.2 b_c)까지는 짙은 하늘로 덮어 게임 별이 이중으로 비치지 않게 하고, 바깥은 페이드

출력 (public/assets/spacez/z/, 각 _lo 절반)
  bh_sgra     640  RGBA  주황·금 원반, 경사 83°(거의 옆에서) — 원반 뒷면이 그림자 위아래로 감긴다
  bh_ton      768  RGBA  자홍·보라, 원반 반경 1.6배, 경사 74° — 게임은 화면에 호만 걸리게 크게 배치
  bh_shimmer  256  RGB   원반 면을 위에서 본 나선 난류 고리 — 'lighter' 로 0.15rad/s 회전, scale(1, cos i) 로 눌러 그린다
  bh_jet      64x512 RGB 제트 원뿔(아래 = 블랙홀, 위 = 끝). 충돌 원뿔(JET_HALF_ANGLE 0.14)과 같은 모양이 굽혀 있다
실행: python scripts/spacez_blackhole.py            (전부)
      python scripts/spacez_blackhole.py bh_sgra     (하나)
"""
import math
import os
import sys

import numpy as np
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spacez_plates as sp  # noqa: E402

B_C = 3 * math.sqrt(3)


# ─── 광선 표 ───
def geodesic_table(b_max, nb=2400, dphi=0.004, phi_max=4.2 * math.pi):
    """b 별 u(φ) 표. 반환: bs, phis, U[nb, nphi](종료 후 nan), phi_end[nb], captured[nb], phi_inf[nb]."""
    # b 격자 — 임계값 b_c 근처를 촘촘히(광자 고리)
    lin = np.linspace(0.02, b_max, nb // 2)
    near = B_C + np.sign(np.linspace(-1, 1, nb // 2)) * np.linspace(-1, 1, nb // 2) ** 2 * 1.2
    bs = np.unique(np.concatenate([lin, near]))
    nphi = int(phi_max / dphi) + 1
    phis = np.arange(nphi) * dphi
    U = np.full((len(bs), nphi), np.nan, np.float32)
    u = np.zeros(len(bs)); w = 1.0 / bs
    alive = np.ones(len(bs), bool)
    phi_end = np.full(len(bs), phi_max); captured = np.zeros(len(bs), bool); phi_inf = np.full(len(bs), np.nan)
    f = lambda u_, w_: (w_, -u_ + 3 * u_ * u_)
    U[:, 0] = 0
    for i in range(1, nphi):
        k1u, k1w = f(u, w)
        k2u, k2w = f(u + 0.5 * dphi * k1u, w + 0.5 * dphi * k1w)
        k3u, k3w = f(u + 0.5 * dphi * k2u, w + 0.5 * dphi * k2w)
        k4u, k4w = f(u + dphi * k3u, w + dphi * k3w)
        un = u + dphi / 6 * (k1u + 2 * k2u + 2 * k3u + k4u)
        wn = w + dphi / 6 * (k1w + 2 * k2w + 2 * k3w + k4w)
        cap = alive & (un >= 0.5)
        esc = alive & (un <= 0) & (i > 2)
        if cap.any():
            captured[cap] = True; phi_end[cap] = phis[i]; alive[cap] = False
        if esc.any():
            t = u[esc] / (u[esc] - un[esc])
            phi_inf[esc] = phis[i - 1] + t * dphi
            phi_end[esc] = phi_inf[esc]; alive[esc] = False
        u = np.where(alive, un, u); w = np.where(alive, wn, w)
        U[alive, i] = u[alive]
        if cap.any() or esc.any():
            U[cap | esc, i] = np.where(cap[cap | esc], 0.5, 0.0)
        if not alive.any():
            break
    return bs, phis, U, phi_end, captured, phi_inf


def star_sky(nstars=4200, seed=7, res=(2048, 4096)):
    """천구 별 지도(등장방형) — 밝기 파워법칙, 색 다양."""
    h, w = res
    E = sp.star_field(h, w, nstars, seed, fmin=0.3, fmax=4.0, sigma=0.8)
    return E


def render_bh(size, F, inc_deg, r_out, lut, seed=1, doppler_p=0.8, ss=2, disk_gain=1.0, sky_r=3.2,
              name="bh", sky_alpha=0.88):
    """size = 최종 px, F = 프레임 반폭(M 단위). 반환 RGBA(최종), 기하 정보."""
    S = size * ss
    th = math.radians(inc_deg)
    b_max = F * math.sqrt(2) * 1.02
    bs, phis, U, phi_end, captured, phi_inf = geodesic_table(b_max)
    yy, xx = sp.grid(S, S)
    X = (xx + 0.5 - S / 2) / (S / 2) * F
    Y = -(yy + 0.5 - S / 2) / (S / 2) * F            # 화면 위 = +Y
    b = np.sqrt(X * X + Y * Y) + 1e-6
    al = np.arctan2(Y, X)
    # b → 표 인덱스 (불균등 격자라 보간 인덱스)
    bi = np.interp(b, bs, np.arange(len(bs))).astype(np.float32)
    dphi = phis[1] - phis[0]
    pe = np.interp(b, bs, phi_end).astype(np.float32)
    capd = np.interp(b, bs, captured.astype(np.float32)) > 0.5
    # 원반 교차
    A = math.cos(th); Bv = np.sin(al) * math.sin(th)
    delta = np.arctan2(Bv, A)
    phi1 = np.mod(delta + math.pi / 2, math.pi)
    r_in = 6.0
    # 난류 텍스처 — (방위각, ln r) 공간의 주기 잡음에 나선 전단
    tex = sp.pnoise(256, 1024, 2.6, seed, aniso=(1.0, 0.35))
    tex2 = sp.pnoise(256, 1024, 3.2, seed + 1)
    col_acc = np.zeros((S, S, 3), np.float32)
    trans = np.ones((S, S), np.float32)
    hit_any = np.zeros((S, S), bool)
    for k in range(3):
        phik = phi1 + k * math.pi
        valid = phik < pe
        pi_ = (phik / dphi).astype(np.float32)
        u = ndi.map_coordinates(np.nan_to_num(U, nan=0.0), [bi, pi_], order=1, mode="nearest")
        r = 1.0 / np.maximum(u, 1e-4)
        inside = valid & (r >= r_in * 0.97) & (r <= r_out * 1.03)
        if not inside.any():
            continue
        # 교차점의 원반면 좌표
        cphi, sphi = np.cos(phik), np.sin(phik)
        px = r * (sphi * np.cos(al))
        py = r * (cphi * (-math.sin(th)) + sphi * np.sin(al) * math.cos(th))
        psi = np.arctan2(py, px)
        # 광자 진행 방향(추적의 반대) — dP/dφ 의 반대
        du = (ndi.map_coordinates(np.nan_to_num(U, nan=0.0), [bi, pi_ + 1], order=1, mode="nearest") - u) / dphi
        drdphi = -du / np.maximum(u * u, 1e-8)
        ex = np.stack([np.zeros_like(r), -math.sin(th) * np.ones_like(r), math.cos(th) * np.ones_like(r)])
        ea = np.stack([np.cos(al), np.sin(al) * math.cos(th), np.sin(al) * math.sin(th)])
        dP = drdphi * (cphi * ex + sphi * ea) + r * (-sphi * ex + cphi * ea)
        kv = -dP / (np.linalg.norm(dP, axis=0) + 1e-9)
        vdir = np.stack([-np.sin(psi), np.cos(psi), np.zeros_like(psi)])
        cosg = (kv * vdir).sum(0)
        beta = np.sqrt(1.0 / np.maximum(r - 2.0, 1.0))
        beta = np.minimum(beta, 0.7)
        gam = 1 / np.sqrt(1 - beta ** 2)
        g = 1 / (gam * (1 - beta * cosg)) * np.sqrt(np.clip(1 - 2 / r, 0.05, 1))
        Iem = (r_in / r) ** 3 * np.clip(1 - np.sqrt(r_in / r), 0, None)
        Iem = Iem / 0.0833 * disk_gain * 0.42                 # 최대(약 r=8.2)가 0.42 — 포화(계단)를 피한다
        lr = (np.log(np.clip(r, r_in, r_out)) - math.log(r_in)) / (math.log(r_out) - math.log(r_in))
        tu = (np.mod(psi / (2 * math.pi) + 0.35 * lr, 1.0)) * 1024
        tv = lr * 255
        n = ndi.map_coordinates(tex, [tv, tu], order=1, mode="wrap")
        n2 = ndi.map_coordinates(tex2, [tv, tu * 1.0], order=1, mode="wrap")
        mod = np.clip(0.72 + 0.22 * n + 0.10 * n2, 0.2, None)
        I = Iem * g ** doppler_p * mod
        # 가장자리 부드럽게 (안쪽 ISCO 경계는 또렷, 바깥은 옅어짐)
        edge = sp.sstep(r_in * 0.97, r_in * 1.05, r) * sp.sstep(r_out * 1.03, r_out * 0.72, r)
        I = I * edge
        T = np.clip((Iem / 0.42 * edge) ** 0.25 * g * 0.82, 0, 2.0)   # 관측 온도(상대)
        c = lut(T)
        emit = (I[..., None] * c) * inside[..., None]
        op = np.clip(edge * 0.94, 0, 1) * inside
        col_acc += trans[..., None] * emit
        trans *= (1 - op)
        hit_any |= inside
    # 그림자 · 하늘
    sky = np.zeros((S, S, 3), np.float32)
    esc = ~capd
    pinf = np.interp(b, bs, np.nan_to_num(phi_inf, nan=0.0)).astype(np.float32)
    ex = np.stack([np.zeros_like(b), -math.sin(th) * np.ones_like(b), math.cos(th) * np.ones_like(b)])
    ea = np.stack([np.cos(al), np.sin(al) * math.cos(th), np.sin(al) * math.sin(th)])
    D = np.cos(pinf) * ex + np.sin(pinf) * ea                  # 광자가 온 하늘 방향(블랙홀 기준)
    lon = np.arctan2(D[1], D[0]); lat = np.arcsin(np.clip(D[2], -1, 1))
    SKY = star_sky(seed=seed + 11)
    sy_ = (0.5 - lat / math.pi) * (SKY.shape[0] - 1); sx_ = (lon / (2 * math.pi) + 0.5) * (SKY.shape[1] - 1)
    for ch in range(3):
        sky[..., ch] = ndi.map_coordinates(SKY[..., ch], [sy_, sx_], order=1, mode="wrap")
    rb0 = b / B_C
    sky *= (esc * sp.sstep(sky_r, sky_r * 0.7, rb0) * (0.35 + 0.65 * sp.sstep(1.25, 1.8, rb0)))[..., None]
    # 합성: 원반(앞) + 투과율 × 하늘. 그림자 = 흡수된 광선 → 검정
    rb = b / B_C
    sky_a = sky_alpha * sp.sstep(sky_r, sky_r * 0.55, rb)
    shadow = capd.astype(np.float32)
    E = col_acc + trans[..., None] * sky * 0.8
    C = sp.cap_luma(sp.tone(E, 1.0), 0.60, 0.80)
    Cs = sp.cap_luma(sp.tone(trans[..., None] * sky * 0.8, 1.0), 0.7, 0.9)
    C = np.maximum(C, Cs)
    dust = np.maximum(shadow * trans, sky_a * trans)
    disk_cov = sp.blur(np.clip((1 - trans) * 1.4, 0, 1), 1.0)
    a = np.maximum(np.maximum(sp.envelope_alpha(C, None, r=3, s=1.5), dust), disk_cov)
    a = np.clip(a, 0, 1)
    rgb = np.where(a[..., None] > 1e-4, C / np.maximum(a[..., None], 1e-4), 0)
    out = np.dstack([np.clip(rgb, 0, 1), a]).astype(np.float32)
    out[..., 3][out[..., 3] < 2.5 / 255] = 0
    fin = sp.resize_premul(out, size, size)
    px_per_M = size / (2 * F)
    geo = dict(center=[size / 2, size / 2], shadow_r_px=round(B_C * px_per_M, 1),
               horizon_r_px=round(2 * px_per_M, 1), disk_in_px=round(r_in * px_per_M, 1),
               disk_out_px=round(r_out * px_per_M, 1), inclination_deg=inc_deg, frame_half_M=F,
               sky_fade_px=round(sky_r * B_C * px_per_M, 1))
    return fin, geo


def lut_sgr(T):
    """주황·금 — 어두운 적갈 → 주황 → 금 → 옅은 노랑빛 흰색."""
    xs = np.array([0.0, 0.35, 0.6, 0.85, 1.05, 1.4])
    cs = np.array([(0.40, 0.06, 0.01), (0.95, 0.26, 0.03), (1.0, 0.52, 0.08), (1.0, 0.74, 0.26),
                   (1.0, 0.90, 0.62), (1.0, 0.97, 0.88)], np.float32)
    return np.stack([np.interp(T, xs, cs[:, c]) for c in range(3)], -1).astype(np.float32)


def lut_ton(T):
    """자홍·보라 — 짙은 보라 → 자홍 → 분홍 → 흰빛."""
    xs = np.array([0.0, 0.35, 0.6, 0.85, 1.05, 1.4])
    cs = np.array([(0.18, 0.03, 0.30), (0.55, 0.10, 0.70), (0.95, 0.25, 0.80), (1.0, 0.55, 0.85),
                   (1.0, 0.80, 0.95), (0.98, 0.95, 1.0)], np.float32)
    return np.stack([np.interp(T, xs, cs[:, c]) for c in range(3)], -1).astype(np.float32)


def render_shimmer(size=256, ss=2, seed=31):
    """원반 면을 위에서 본 나선 난류 고리 — 가산('lighter') 반짝임 층. 불투명 RGB(검정 = 투명)."""
    S = size * ss
    yy, xx = sp.grid(S, S)
    dx = (xx + 0.5 - S / 2) / (S / 2); dy = (yy + 0.5 - S / 2) / (S / 2)
    r = np.sqrt(dx * dx + dy * dy); psi = np.arctan2(dy, dx)
    rin, rout = 0.30, 0.98                       # 원반 r_in/r_out = 6/20 → 0.30
    lr = np.clip((r - rin) / (rout - rin), 0, 1)
    tex = sp.pnoise(256, 2048, 1.7, seed, aniso=(1.0, 0.12))
    tu = np.mod(psi / (2 * math.pi) + 0.45 * lr, 1.0) * 2048
    n = ndi.map_coordinates(tex, [lr * 255, tu], order=1, mode="wrap")
    streak = np.clip(n - 0.5, 0, None) ** 1.3
    band = sp.sstep(rin, rin + 0.05, r) * sp.sstep(rout, rout - 0.35, r)
    E = (streak * band * 0.55)[..., None] * sp.col((1.0, 0.86, 0.62))
    C = sp.cap_luma(sp.tone(E, 1.0), 0.28, 0.36)
    out = np.dstack([C, np.ones((S, S), np.float32)])
    return sp.resize_premul(out, size, size), dict(center=[size / 2, size / 2], ring_in_px=rin * size / 2,
                                                   ring_out_px=rout * size / 2)


def render_jet(w=64, h=512, ss=2, seed=41):
    """제트 원뿔 — 아래 가장자리 가운데(블랙홀) → 위 가장자리 전체 폭(끝). 코어 청백 + 보라 헤일로 + 매듭."""
    W, H = w * ss, h * ss
    yy, xx = sp.grid(H, W)
    s = 1 - (yy + 0.5) / H                        # 0 = 밑동(블랙홀), 1 = 끝
    half = np.maximum(s, 0.004) * (W / 2)          # 원뿔 반폭 — 끝에서 판 전체 폭
    q = np.abs(xx + 0.5 - W / 2) / half            # 원뿔 안 정규화 거리(0 중심, 1 가장자리)
    n = sp.pnoise(H, W, 2.6, seed, aniso=(0.3, 1.0))
    knots = 0.65 + 0.55 * np.clip(np.sin(s * 34 + 0.7 * n) ** 6, 0, 1)
    core = np.exp(-(q / 0.16) ** 2) * knots
    halo = np.exp(-(q / 0.55) ** 2) * np.clip(0.75 + 0.35 * n, 0, None)
    fall = np.exp(-s / 0.55) * sp.sstep(0.0, 0.04, s)
    E = (core * 1.6 * fall)[..., None] * sp.col((0.80, 0.95, 1.0)) + (halo * 0.7 * fall)[..., None] * sp.col((0.50, 0.40, 1.0))
    C = sp.cap_luma(sp.tone(E, 1.0), 0.55, 0.75) * sp.sstep(1.0, 0.97, q)[..., None]
    C *= sp.sstep(1.0, 0.9, s)[..., None]
    out = np.dstack([C, np.ones((H, W), np.float32)])
    return sp.resize_premul(out, w, h), dict(base=[w / 2, h], tip_y=0)


BH_ASSETS = {
    # 이름: (함수, 예산 KB, lo 예산 KB, 메모)
    "bh_sgra": (lambda: render_bh(640, 24.0, 83.0, 20.0, lut_sgr, seed=1, name="sgra"), 70, 24,
                "존19 궁수자리 A* — 본체 drawImage 1회. 그림자 반지름(shadow_r_px)을 판정 eventR(32)에 맞춰 스케일"),
    "bh_ton": (lambda: render_bh(768, 36.0, 74.0, 32.0, lut_ton, seed=5, name="ton", disk_gain=1.1), 75, 26,
               "존25 TON 618 — 원반 반경 1.6배, 자홍·보라. 화면에 호만 걸리게 크게 배치"),
    "bh_shimmer": (render_shimmer, 15, 6, "존19·25 반짝임 층 — 'lighter', 0.15rad/s 회전, scale(1,cos(inc)) 로 원반 기울기에 맞춤"),
    "bh_jet": (render_jet, 12, 5, "존19 제트 — 64x512 원뿔(아래=블랙홀). 폭 2·REACH·tan(0.14), 높이 REACH 로 늘려 그림. 아래 제트는 세로 뒤집기"),
}
BH_GEO = {}


def build(names=None):
    res = {}
    for name, (fn, kb, kb_lo, note) in BH_ASSETS.items():
        if names and name not in names:
            continue
        print("==", name, flush=True)
        a, geo = fn()
        BH_GEO[name] = geo
        p = os.path.join(sp.PUB_DIR, name + ".webp")
        q, sz = sp.save_webp(a, p, kb, q0=80)
        h, w = a.shape[:2]
        lo = sp.resize_premul(a, w // 2, h // 2)
        ql, szl = sp.save_webp(lo, os.path.join(sp.PUB_DIR, name + "_lo.webp"), kb_lo, q0=75)
        print("   %dx%d q%d %.1fKB | lo q%d %.1fKB  %s" % (w, h, q, sz / 1024, ql, szl / 1024, geo), flush=True)
        res[name] = dict(q=q, sz=sz, ql=ql, szl=szl, geo=geo)
    sp.geo_update(BH_GEO)
    return res


if __name__ == "__main__":
    build(sys.argv[1:] or None)
