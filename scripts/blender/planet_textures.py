# -*- coding: utf-8 -*-
"""행성 표면 텍스처 생성기 (equirectangular) — 2026-08-21.

절차적 셰이더 노드만으로는 "리얼한 행성"이 안 나왔다. Voronoi 크레이터는
골프공처럼 보이고, 목성 줄무늬는 좌표계 때문에 세로로 서 버렸다.
위도·경도를 직접 다루는 이미지 텍스처를 만들면 실제 행성의 특징
(위도별 밴드, 원형 크레이터와 광조, 극관, 대적점)을 정확히 통제할 수 있다.

출력: scripts/og-assets/planets/tex_<name>.png (2048x1024, equirectangular)
실행: python planet_textures.py   (일반 파이썬 — Blender 불필요)
"""
import math
import os
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "og-assets", "planets")
os.makedirs(OUT, exist_ok=True)

W, H = 2048, 1024
rng = np.random.default_rng(20260821)


# ─────────────────────────── 노이즈 유틸 ───────────────────────────
def _smooth(a, sigma):
    """가우시안 블러 (PIL 경유 — scipy 없이)."""
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), 'L')
    im = im.filter(ImageFilter.GaussianBlur(sigma))
    return np.asarray(im).astype(np.float32) / 255.0


def value_noise(shape, cells, seed=None):
    """저해상 랜덤 격자를 확대·보간한 값 노이즈. 경도 방향은 순환(seamless)."""
    r = np.random.default_rng(seed) if seed is not None else rng
    cy = max(2, int(cells))
    cx = max(2, int(cells * 2))
    g = r.random((cy, cx)).astype(np.float32)
    g = np.concatenate([g, g[:, :1]], axis=1)          # 경도 순환
    im = Image.fromarray((g * 255).astype(np.uint8), 'L')
    im = im.resize((shape[1] + 1, shape[0]), Image.BICUBIC)
    a = np.asarray(im).astype(np.float32)[:, :shape[1]] / 255.0
    return a


def fbm(shape, base_cells=4, octaves=6, gain=0.5, seed=0):
    out = np.zeros(shape, np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        out += amp * value_noise(shape, base_cells * (2 ** o), seed=seed + o * 977)
        total += amp
        amp *= gain
    return out / total


def lat_grid(shape):
    """각 픽셀의 위도(-90~90)와 경도(-180~180)."""
    ys = np.linspace(90, -90, shape[0], dtype=np.float32)[:, None]
    xs = np.linspace(-180, 180, shape[1], dtype=np.float32)[None, :]
    return np.broadcast_to(ys, shape), np.broadcast_to(xs, shape)


def to_rgb(r, g, b):
    return np.clip(np.dstack([r, g, b]), 0, 1)


def polar_fade(arr, start=78.0, end=89.0):
    """극 부근을 그 위도의 평균색으로 수렴시킨다.

    start 를 너무 낮게 잡으면 화성 극관(위도 68도~)처럼 극 근처의
    진짜 특징까지 평균색으로 지워진다 (2026-08-21 실측).

    equirectangular 는 극에서 경도가 극단적으로 압축돼 크레이터·난류가
    가로로 뭉개진다. 구에 감으면 극은 화면에서 거의 안 보이므로,
    평균색으로 부드럽게 눌러 주는 편이 훨씬 깔끔하다.
    """
    h = arr.shape[0]
    lat = np.linspace(90, -90, h, dtype=np.float32)[:, None, None]
    t = np.clip((np.abs(lat) - start) / max(1e-6, (end - start)), 0, 1)
    row_mean = arr.mean(axis=1, keepdims=True)
    return arr * (1 - t) + row_mean * t


def saturate(arr, amt=1.22, lift=0.03):
    """채도·명도 소폭 상향 (2026-08-21 운영자 요청: "조금 더 쨍하게").

    회색축(휘도)에서 멀어지는 방향으로 밀어 채도를 올리고, 전체를 살짝
    들어 올려 어두운 면이 뭉개지지 않게 한다.
    """
    lum = (arr * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(axis=2, keepdims=True)
    out = lum + (arr - lum) * amt
    return np.clip(out + lift, 0, 1)


def save(arr, name):
    if not name.startswith("rings"):
        arr = polar_fade(arr)
    arr = saturate(arr)
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGB')
    p = os.path.join(OUT, "tex_" + name + ".png")
    im.save(p)
    print("  tex", name, im.size)


def ramp(t, stops):
    """t(0~1) → 색. stops = [(pos, (r,g,b)), ...] 정렬 가정."""
    r = np.zeros_like(t); g = np.zeros_like(t); b = np.zeros_like(t)
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        m = (t >= p0) & (t <= p1)
        if not m.any():
            continue
        f = (t[m] - p0) / max(1e-6, (p1 - p0))
        r[m] = c0[0] + (c1[0] - c0[0]) * f
        g[m] = c0[1] + (c1[1] - c0[1]) * f
        b[m] = c0[2] + (c1[2] - c0[2]) * f
    r[t < stops[0][0]] = stops[0][1][0]; g[t < stops[0][0]] = stops[0][1][1]; b[t < stops[0][0]] = stops[0][1][2]
    r[t > stops[-1][0]] = stops[-1][1][0]; g[t > stops[-1][0]] = stops[-1][1][1]; b[t > stops[-1][0]] = stops[-1][1][2]
    return r, g, b


# ─────────────────────────── 크레이터 지형 ───────────────────────────
def crater_field(shape, count=900, rmin=3, rmax=46, seed=1, ray_prob=0.10):
    """원형 크레이터 높이맵 + 광조(ray) 알베도.

    실제 크레이터는 (1) 가운데 함몰 (2) 테두리 융기 (3) 큰 것은 밝은 광조.
    Voronoi 셀 경계로는 이 셋 중 무엇도 표현되지 않아 골프공처럼 보였다.
    """
    r = np.random.default_rng(seed)
    hgt = np.zeros(shape, np.float32)
    alb = np.zeros(shape, np.float32)
    Hh, Ww = shape
    for _ in range(count):
        # 위도는 cos 가중(극 왜곡 보정), 크기는 멱법칙(작은 게 훨씬 많다)
        lat = math.degrees(math.asin(r.uniform(-1, 1)))
        lon = r.uniform(-180, 180)
        rad = rmin + (rmax - rmin) * (r.random() ** 2.6)
        cy = int((90 - lat) / 180 * Hh)
        cx = int((lon + 180) / 360 * Ww)
        rr = int(rad * 2.6)
        y0, y1 = max(0, cy - rr), min(Hh, cy + rr + 1)
        if y0 >= y1:
            continue
        yy = np.arange(y0, y1)[:, None]
        xx = np.arange(cx - rr, cx + rr + 1)[None, :]
        # 경도 순환
        xxw = np.mod(xx, Ww)
        # 위도에 따른 경도 압축 (극에서는 픽셀이 촘촘)
        latf = np.cos(np.radians(90 - yy / Hh * 180))
        latf = np.clip(latf, 0.15, 1.0)
        d = np.sqrt(((yy - cy) ** 2) + (((xx - cx) * latf) ** 2)) / max(1.0, rad)
        # 함몰(0~0.75) → 테두리 융기(0.75~1.15) → 바깥
        bowl = -np.exp(-(d ** 2) * 2.2) * 0.9
        rim = np.exp(-((d - 0.95) ** 2) * 22.0) * 0.75
        prof = (bowl + rim).astype(np.float32)
        m = d < 2.4
        np.maximum.at(hgt, (np.broadcast_to(yy, d.shape)[m], np.broadcast_to(xxw, d.shape)[m]),
                      prof[m] * 0)  # no-op (아래에서 가산)
        hgt[y0:y1][:, :][np.arange(0)] if False else None
        # 가산 합성 (겹치는 크레이터가 자연스럽게 누적)
        ys_idx = np.broadcast_to(yy, d.shape)[m]
        xs_idx = np.broadcast_to(xxw, d.shape)[m]
        np.add.at(hgt, (ys_idx, xs_idx), prof[m])
        # 광조 — 큰 크레이터 일부만
        if rad > rmax * 0.45 and r.random() < ray_prob * 6:
            rayv = (np.exp(-((d - 0.2) ** 2) * 0.55) *
                    (0.5 + 0.5 * np.cos(np.arctan2(yy - cy, (xx - cx) + 1e-6) * r.integers(6, 14))))
            rm = (d < 2.4) & (d > 0.9)
            np.add.at(alb, (np.broadcast_to(yy, d.shape)[rm], np.broadcast_to(xxw, d.shape)[rm]),
                      rayv[rm] * 0.35)
    hgt = hgt / max(1e-6, np.abs(hgt).max())
    return hgt, np.clip(alb, 0, 1)


# ══════════════════════════════ 각 천체 ══════════════════════════════
def tex_moon():
    shape = (H, W)
    hgt, rays = crater_field(shape, count=1400, rmin=2, rmax=54, seed=11, ray_prob=0.12)
    base = 0.60 + hgt * 0.28 + (fbm(shape, 6, 5, seed=21) - 0.5) * 0.10
    # 바다(마리아) — 큰 어두운 저지대
    maria = _smooth((fbm(shape, 2, 4, seed=33) > 0.56).astype(np.float32), 18)
    base = base * (1 - maria * 0.42)
    base = np.clip(base + rays * 0.5, 0, 1)
    g = base
    save(to_rgb(g * 1.00, g * 0.99, g * 0.96), "moon")
    save(to_rgb(hgt * .5 + .5, hgt * .5 + .5, hgt * .5 + .5), "moon_h")


def tex_mercury():
    shape = (H, W)
    hgt, rays = crater_field(shape, count=1800, rmin=2, rmax=48, seed=12, ray_prob=0.10)
    base = 0.50 + hgt * 0.26 + (fbm(shape, 7, 5, seed=22) - 0.5) * 0.12
    base = np.clip(base + rays * 0.45, 0, 1)
    save(to_rgb(base * 1.00, base * 0.90, base * 0.82), "mercury")
    save(to_rgb(hgt * .5 + .5, hgt * .5 + .5, hgt * .5 + .5), "mercury_h")


def tex_asteroid():
    shape = (H, W)
    hgt, _ = crater_field(shape, count=900, rmin=4, rmax=70, seed=13, ray_prob=0.0)
    base = 0.42 + hgt * 0.30 + (fbm(shape, 9, 5, seed=23) - 0.5) * 0.18
    save(to_rgb(base * 1.00, base * 0.84, base * 0.66), "asteroid")
    save(to_rgb(hgt * .5 + .5, hgt * .5 + .5, hgt * .5 + .5), "asteroid_h")


def tex_meteor():
    shape = (H, W)
    hgt, _ = crater_field(shape, count=500, rmin=6, rmax=80, seed=14, ray_prob=0.0)
    base = 0.32 + hgt * 0.26 + (fbm(shape, 11, 5, seed=24) - 0.5) * 0.20
    save(to_rgb(base * 1.00, base * 0.80, base * 0.62), "meteor")
    save(to_rgb(hgt * .5 + .5, hgt * .5 + .5, hgt * .5 + .5), "meteor_h")


def tex_mars():
    shape = (H, W)
    lat, lon = lat_grid(shape)
    hgt, _ = crater_field(shape, count=700, rmin=3, rmax=40, seed=15, ray_prob=0.0)
    n = fbm(shape, 3, 7, seed=31)
    # 알베도 특징: 어두운 현무암 지대(시르티스 등)
    dark = _smooth((fbm(shape, 2, 4, seed=41) > 0.58).astype(np.float32), 14)
    t = np.clip(n * 0.75 + hgt * 0.25 + 0.1, 0, 1)
    r, g, b = ramp(t, [(0.0, (0.36, 0.14, 0.07)), (0.45, (0.62, 0.28, 0.14)),
                       (0.70, (0.80, 0.45, 0.24)), (1.0, (0.90, 0.66, 0.45))])
    r = r * (1 - dark * 0.30); g = g * (1 - dark * 0.34); b = b * (1 - dark * 0.30)
    # 극관 — 위도 기반, 가장자리는 노이즈로 자연스럽게
    capn = fbm(shape, 8, 4, seed=51)
    # 구에 감으면 극관은 실제보다 훨씬 얇아 보인다. 위도 55도부터 잡아야
    # 게임 안 60px 스프라이트에서도 '화성'으로 읽힌다
    cap = np.clip((np.abs(lat) - (55 + capn * 7)) / 10.0, 0, 1)
    r = r * (1 - cap) + 0.97 * cap
    g = g * (1 - cap) + 0.98 * cap
    b = b * (1 - cap) + 1.00 * cap
    save(to_rgb(r, g, b), "mars")
    save(to_rgb(hgt * .5 + .5, hgt * .5 + .5, hgt * .5 + .5), "mars_h")


def _banded(shape, bands, turb_cells=14, turb_amt=9.0, seed=61):
    """위도 밴딩 + 난류 왜곡. bands = [(lat_deg, (r,g,b)), ...] 위→아래."""
    lat, lon = lat_grid(shape)
    turb = (fbm(shape, turb_cells, 6, seed=seed) - 0.5) * 2.0 * turb_amt
    # 극으로 갈수록 난류를 줄인다 — 진폭이 일정하면 lat+turb 가 +-90 을 넘어
    # 램프 밖으로 나가고, 극이 통째로 흰색으로 클램프된다
    turb = turb * np.cos(np.radians(lat)) ** 0.6
    latd = lat + turb
    t = (90 - latd) / 180.0
    stops = [((90 - bl) / 180.0, c) for bl, c in bands]
    stops.sort(key=lambda s: s[0])
    return ramp(np.clip(t, 0, 1), stops)


def tex_jupiter():
    shape = (H, W)
    r, g, b = _banded(shape, [
        (90, (0.62, 0.55, 0.48)), (68, (0.85, 0.76, 0.62)), (55, (0.55, 0.38, 0.24)),
        (42, (0.93, 0.86, 0.73)), (30, (0.66, 0.45, 0.28)), (18, (0.97, 0.92, 0.82)),
        (8,  (0.72, 0.50, 0.32)), (0,  (0.95, 0.88, 0.76)), (-10, (0.60, 0.40, 0.26)),
        (-22, (0.94, 0.88, 0.77)), (-34, (0.70, 0.48, 0.30)), (-50, (0.88, 0.80, 0.68)),
        (-68, (0.56, 0.44, 0.34)), (-90, (0.60, 0.53, 0.46)),
    ], turb_cells=20, turb_amt=4.2, seed=61)
    # 대적점 — 남반구 위도 -22도 부근의 큰 타원 소용돌이
    lat, lon = lat_grid(shape)
    sw = fbm(shape, 26, 5, seed=71)
    # 대적점 — 실제 비율보다 크게. 작으면 게임 안 60px 스프라이트에서 사라진다
    d = np.sqrt(((lat + 20) / 13.0) ** 2 + (((lon + 60 + (sw - .5) * 16) % 360 - 180) / 34.0) ** 2)
    spot = np.clip(1.15 - d, 0, 1) ** 1.15
    r = r * (1 - spot) + (0.84 + sw * 0.12) * spot
    g = g * (1 - spot) + (0.28 + sw * 0.10) * spot
    b = b * (1 - spot) + (0.15 + sw * 0.07) * spot
    # 대적점 둘레의 흰 소용돌이 테두리
    ringm = np.clip(1.0 - np.abs(d - 1.05) * 7.0, 0, 1) * 0.55
    r = np.clip(r + ringm * 0.30, 0, 1)
    g = np.clip(g + ringm * 0.26, 0, 1)
    b = np.clip(b + ringm * 0.20, 0, 1)
    save(to_rgb(r, g, b), "jupiter")


def tex_saturn():
    shape = (H, W)
    r, g, b = _banded(shape, [
        (90, (0.72, 0.64, 0.50)), (60, (0.90, 0.82, 0.64)), (40, (0.97, 0.92, 0.76)),
        (20, (0.88, 0.79, 0.60)), (0, (0.98, 0.94, 0.80)), (-20, (0.90, 0.82, 0.64)),
        (-45, (0.95, 0.89, 0.72)), (-70, (0.78, 0.70, 0.56)), (-90, (0.70, 0.62, 0.50)),
    ], turb_cells=16, turb_amt=3.2, seed=62)
    save(to_rgb(r, g, b), "saturn")


def tex_venus():
    shape = (H, W)
    # 실제 금성은 거의 균질한 황산 구름층이다. 난류·대비를 키우면 구에 감았을 때
    # 경계가 선명한 큰 얼룩이 생겨 오히려 행성처럼 안 보인다 (2026-08-21)
    r, g, b = _banded(shape, [
        (90, (0.88, 0.79, 0.56)), (45, (0.96, 0.89, 0.70)), (0, (0.99, 0.94, 0.79)),
        (-45, (0.95, 0.87, 0.67)), (-90, (0.87, 0.78, 0.55)),
    ], turb_cells=6, turb_amt=9.0, seed=63)
    sw = fbm(shape, 9, 6, seed=81)
    r = np.clip(r * (0.94 + sw * 0.12), 0, 1)
    g = np.clip(g * (0.94 + sw * 0.12), 0, 1)
    b = np.clip(b * (0.93 + sw * 0.12), 0, 1)
    save(to_rgb(r, g, b), "venus")


def tex_earth():
    shape = (H, W)
    lat, lon = lat_grid(shape)
    land = fbm(shape, 3, 8, seed=91)
    # 위도별 기후: 적도 초록, 아열대 사막, 고위도 침엽수/툰드라, 극지 만년설
    h = np.clip((land - 0.50) / 0.24, 0, 1)          # 해발
    sea = land <= 0.50
    depth = np.clip((0.50 - land) / 0.30, 0, 1)
    r = np.zeros(shape, np.float32); g = np.zeros(shape, np.float32); b = np.zeros(shape, np.float32)
    # 바다
    r[sea] = 0.02 + (1 - depth[sea]) * 0.06
    g[sea] = 0.10 + (1 - depth[sea]) * 0.22
    b[sea] = 0.28 + (1 - depth[sea]) * 0.28
    # 육지
    al = np.abs(lat)
    dryness = np.clip((np.abs(al - 25) < 12).astype(np.float32) + (fbm(shape, 5, 4, seed=95) - 0.45), 0, 1)
    lr = 0.16 + dryness * 0.55 + h * 0.22
    lg = 0.38 - dryness * 0.14 + h * 0.16
    lb = 0.12 + dryness * 0.18 + h * 0.18
    cold = np.clip((al - 55) / 20.0, 0, 1)
    lr = lr * (1 - cold) + 0.90 * cold
    lg = lg * (1 - cold) + 0.92 * cold
    lb = lb * (1 - cold) + 0.95 * cold
    r[~sea] = lr[~sea]; g[~sea] = lg[~sea]; b[~sea] = lb[~sea]
    # 극관
    cap = np.clip((al - 72) / 8.0, 0, 1)
    r = r * (1 - cap) + 0.95 * cap; g = g * (1 - cap) + 0.97 * cap; b = b * (1 - cap) + 1.0 * cap
    save(to_rgb(r, g, b), "earth")
    # 구름 알파 (흑=투명, 백=구름) — 위도대별 띠 + 소용돌이
    cl = fbm(shape, 5, 7, seed=101)
    band = 0.5 + 0.5 * np.cos(np.radians(lat * 3.4))
    cloud = np.clip((cl * 0.75 + band * 0.35 - 0.52) * 3.2, 0, 1)
    save(to_rgb(cloud, cloud, cloud), "earth_clouds")


def tex_sun():
    shape = (H, W)
    gran = fbm(shape, 40, 5, seed=111)
    supergran = fbm(shape, 9, 4, seed=112)
    t = np.clip(gran * 0.55 + supergran * 0.45, 0, 1)
    # 더 밝은 태양색 — 살구빛에서 금빛 백열 쪽으로 (2026-08-21)
    # 표면은 진한 주황~금으로 두고 '밝기'는 발광(emission)으로 만든다.
    # 팔레트를 크림색까지 올리면 렌더에서 흰 원반이 된다 (2026-08-21)
    r, g, b = ramp(t, [(0.0, (1.00, 0.42, 0.02)), (0.38, (1.00, 0.62, 0.06)),
                       (0.68, (1.00, 0.80, 0.20)), (1.0, (1.00, 0.94, 0.56))])
    # 흑점 몇 개
    lat, lon = lat_grid(shape)
    sp = np.random.default_rng(7)
    for _ in range(7):
        la = sp.uniform(-32, 32); lo = sp.uniform(-180, 180); rad = sp.uniform(3, 8)
        d = np.sqrt(((lat - la) / rad) ** 2 + (((lon - lo + 180) % 360 - 180) / (rad * 2.0)) ** 2)
        m = np.clip(1.15 - d, 0, 1) ** 1.6
        r = r * (1 - m * .85); g = g * (1 - m * .88); b = b * (1 - m * .9)
    save(to_rgb(r, g, b), "sun")


def tex_rings():
    """토성 고리 — 1D 반경 프로파일을 가로로 편 이미지 (U=반경)."""
    w = 2048
    x = np.linspace(0, 1, w)
    dens = (0.55
            + 0.30 * np.sin(x * 46) * np.exp(-((x - 0.5) ** 2) * 3)
            + 0.18 * np.sin(x * 137 + 1.2)
            + 0.12 * np.sin(x * 311 + 0.4))
    dens = np.clip(dens, 0, 1)
    # 카시니 간극
    for c, wd in ((0.62, 0.035), (0.36, 0.012), (0.82, 0.010)):
        dens *= 1 - np.exp(-((x - c) ** 2) / (2 * wd ** 2))
    dens[x < 0.06] = 0
    dens[x > 0.985] = 0
    col = np.dstack([dens * 0.98, dens * 0.92, dens * 0.78])
    img = np.repeat(col, 8, axis=0)
    save(img, "rings")
    save(np.dstack([dens, dens, dens]).repeat(8, axis=0), "rings_a")


# 지구는 제외 — 텍스처판은 색 배정이 뒤집혀 실패했고, Blender 절차적
# 셰이더(대륙/바다 임계 + 구름층 + 대기 림)가 이미 사실적이다
ALL = [tex_meteor, tex_asteroid, tex_moon, tex_mercury, tex_venus,
       tex_mars, tex_jupiter, tex_saturn, tex_sun, tex_rings]

# ══════════════════════════════════════════════════════════════════════
#  Space-Z v5 히어로 천체 텍스처 (2026-09-27 추가 — 위의 기존 함수는 건드리지 않는다)
#
#  소비처: scripts/blender/spacez_planets.py (Blender 렌더 → public/assets/spacez/z/)
#  출력:   scripts/og-assets/planets/tex_sz_<name>.png
#
#  기존 함수와의 차이
#  - 실수형 노이즈(_sz_vnoise): 기존 value_noise 는 uint8 을 거쳐 256 단계로 양자화돼
#    범프맵에 계단이 생긴다. 확대 렌더(지구 림 1080px)에서는 그게 보인다
#  - 실제 지형을 좌표로 찍는다: 지구 대륙 윤곽, 달의 바다, 화성의 매리너 협곡·타르시스,
#    명왕성의 톰보 하트. '행성처럼 보이는 무언가'가 아니라 '그 행성'으로 읽혀야 한다
#  - 데이터 맵(도시불빛·구름·높이)은 save() 의 채도·명도 보정을 타면 안 된다
#    (lift +0.03 이 밤 전체를 발광시킨다) → _sz_save_raw 로 따로 저장
# ══════════════════════════════════════════════════════════════════════

def _sz_ll(shape):
    """픽셀 중심 기준 위도·경도 격자 (float32, 전체 배열)."""
    h, w = shape
    lat = (90.0 - (np.arange(h, dtype=np.float32) + 0.5) / h * 180.0)[:, None]
    lon = (-180.0 + (np.arange(w, dtype=np.float32) + 0.5) / w * 360.0)[None, :]
    return np.broadcast_to(lat, shape).astype(np.float32), np.broadcast_to(lon, shape).astype(np.float32)


def _sz_wrap(dlon):
    return (dlon + 180.0) % 360.0 - 180.0


def _sz_vnoise(shape, cy, cx, seed):
    """실수형 값 노이즈 — 경도 순환. PIL 'F' 모드 bicubic 확대."""
    r = np.random.default_rng(seed)
    cy = max(2, int(cy)); cx = max(3, int(cx))
    g = r.random((cy + 1, cx)).astype(np.float32)
    g = np.concatenate([g[:, -2:], g, g[:, :3]], axis=1)      # 순환 여유분
    im = Image.fromarray(g, 'F')
    # 여유분 포함 폭으로 확대한 뒤 가운데를 잘라낸다 → 좌우 이음매가 연속
    sx = shape[1] / cx
    big = im.resize((int(round((cx + 5) * sx)), shape[0]), Image.BICUBIC)
    a = np.asarray(big, dtype=np.float32)
    x0 = int(round(2 * sx))
    return np.ascontiguousarray(a[:, x0:x0 + shape[1]])


def _sz_fbm(shape, base=4, octaves=6, gain=0.5, seed=0, stretch=1.0, lac=2.0):
    """stretch = 동서 방향으로 늘이는 배수. 1 이면 각도상 등방(정거원통 2:1 이라 경도 셀 = 위도 셀 x 2),
    크게 하면 무늬가 동서로 길게 늘어진다(목성 띠·권운). 셀 수가 아니라 '늘임'이라 헷갈리지 말 것."""
    xratio = 2.0 / max(0.05, stretch)
    out = np.zeros(shape, np.float32)
    amp, tot, f = 1.0, 0.0, float(base)
    for o in range(octaves):
        out += amp * _sz_vnoise(shape, f, f * xratio, seed + o * 1013)
        tot += amp
        amp *= gain
        f *= lac
    return out / tot


def _sz_sample(arr, yy, xx):
    """이중선형 샘플 — x 는 경도 순환, y 는 클램프. yy/xx 는 픽셀 좌표 배열."""
    h, w = arr.shape[:2]
    yy = np.clip(yy, 0, h - 1.001)
    y0 = np.floor(yy).astype(np.int32); fy = (yy - y0).astype(np.float32)
    x0f = np.floor(xx); fx = (xx - x0f).astype(np.float32)
    x0 = np.mod(x0f.astype(np.int64), w); x1 = np.mod(x0 + 1, w)
    y1 = np.minimum(y0 + 1, h - 1)
    if arr.ndim == 3:
        fy = fy[..., None]; fx = fx[..., None]
    a = arr[y0, x0] * (1 - fx) + arr[y0, x1] * fx
    b = arr[y1, x0] * (1 - fx) + arr[y1, x1] * fx
    return a * (1 - fy) + b * fy


def _sz_box1d(a, r, axis, wrap):
    """반경 r 상자 평균 (누적합). wrap=True 면 순환, 아니면 가장자리 반복."""
    if r < 1:
        return a
    n = a.shape[axis]
    if wrap:
        idx = np.arange(-r - 1, n + r) % n
    else:
        idx = np.clip(np.arange(-r - 1, n + r), 0, n - 1)
    ext = np.take(a, idx, axis=axis).astype(np.float64)
    c = np.cumsum(ext, axis=axis)
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)


def _sz_blur(a, sigma):
    """실수형 가우시안 근사 블러 — 상자 평균 3회(중심극한). 경도(x) 순환, 위도(y) 가장자리 반복.
    PIL GaussianBlur 는 'F' 모드를 받지 않고, uint8 로 내리면 범프에 계단이 생긴다."""
    if sigma <= 0.3:
        return a.astype(np.float32)
    # 상자 3회의 분산 = 3 * ((2r+1)^2 - 1) / 12  →  r 을 sigma 에 맞춘다
    r = max(1, int(round((math.sqrt(4 * sigma * sigma + 1) - 1) / 2)))
    out = a.astype(np.float32)
    for _ in range(3):
        out = _sz_box1d(out, r, 1, True)
        out = _sz_box1d(out, r, 0, False)
    return out


def _sz_ellipse(lat, lon, la0, lo0, rlat, rlon, rot=0.0):
    """국소 타원 거리(1 = 가장자리). 경도는 cos(위도) 로 보정해 극 근처에서도 모양 유지."""
    dx = _sz_wrap(lon - lo0) * math.cos(math.radians(la0))
    dy = lat - la0
    if rot:
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        dx, dy = dx * c - dy * s, dx * s + dy * c
    return np.sqrt((dx / max(1e-6, rlon * math.cos(math.radians(la0)))) ** 2 + (dy / rlat) ** 2)


def _sz_gc(lat, lon, la0, lo0):
    """대원 거리(도)."""
    p1 = np.radians(lat); p0 = math.radians(la0)
    dl = np.radians(_sz_wrap(lon - lo0))
    c = np.sin(p1) * math.sin(p0) + np.cos(p1) * math.cos(p0) * np.cos(dl)
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


def _sz_poly_mask(shape, polys, ss=2):
    """(경도, 위도) 다각형 목록 → 0/1 마스크 (ss 배 슈퍼샘플 후 축소 = 부드러운 해안)."""
    from PIL import ImageDraw
    h, w = shape
    im = Image.new('L', (w * ss, h * ss), 0)
    dr = ImageDraw.Draw(im)
    for poly, val in polys:
        pts = [((lo + 180.0) / 360.0 * w * ss, (90.0 - la) / 180.0 * h * ss) for lo, la in poly]
        dr.polygon(pts, fill=val)
    im = im.resize((w, h), Image.BOX)
    return np.asarray(im, dtype=np.float32) / 255.0


def _sz_smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _sz_mix(a, b, t):
    t = t[..., None] if (t.ndim == a.ndim - 1) else t
    return a * (1 - t) + b * t


def _sz_col(shape, c):
    return np.broadcast_to(np.array(c, np.float32), shape + (3,)).astype(np.float32)


def _sz_save_rgb(arr, name, sat=1.10, lift=0.0, fade=True):
    """색 텍스처 저장 — 기존 save() 보다 약한 보정(대비는 렌더의 AgX 가 담당)."""
    if fade:
        arr = polar_fade(arr, 84.0, 90.0)
    lum = (arr * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(axis=2, keepdims=True)
    arr = np.clip(lum + (arr - lum) * sat + lift, 0, 1)
    im = Image.fromarray((arr * 255 + 0.5).astype(np.uint8), 'RGB')
    p = os.path.join(OUT, "tex_sz_" + name + ".png")
    im.save(p)
    print("  tex_sz", name, im.size)


def _sz_save_raw(a, name, bits16=False):
    """데이터 맵(높이·마스크·불빛) — 보정 없이 그대로. 높이는 16bit 로 계단 방지."""
    a = np.clip(a, 0, 1)
    p = os.path.join(OUT, "tex_sz_" + name + ".png")
    if bits16:
        Image.fromarray((a * 65535 + 0.5).astype(np.uint16)).save(p)
    else:
        Image.fromarray((a * 255 + 0.5).astype(np.uint8), 'L').save(p)
    print("  tex_sz", name, a.shape[::-1], "16bit" if bits16 else "8bit")


def _sz_craters(shape, count, rmin_deg, rmax_deg, seed, power=2.8, amp=1.0, region=None):
    """대원 거리 기반 크레이터 높이맵 (극에서도 원형 유지).

    크기 분포를 멱법칙으로 두고 큰 것은 드물게 — 같은 크기가 고르게 깔리면 골프공이 된다.
    region(lat, lon) → 0..1 가중치를 주면 그 지역에만 뿌린다(달의 바다는 젊어서 크레이터가 적다).
    """
    r = np.random.default_rng(seed)
    h, w = shape
    hgt = np.zeros(shape, np.float32)
    for _ in range(count):
        la = math.degrees(math.asin(r.uniform(-1, 1)))
        lo = r.uniform(-180, 180)
        if region is not None and r.random() > region(la, lo):
            continue
        rad = rmin_deg + (rmax_deg - rmin_deg) * (r.random() ** power)
        ext = rad * 2.2
        y0 = int(max(0, (90 - (la + ext)) / 180 * h)); y1 = min(h, int((90 - (la - ext)) / 180 * h) + 1)
        if y1 <= y0:
            continue
        cosl = max(0.05, math.cos(math.radians(min(89.0, abs(la) + ext))))
        xext = min(180.0, ext / cosl)
        xs0 = int(math.floor((lo - xext + 180) / 360 * w)); xs1 = int(math.ceil((lo + xext + 180) / 360 * w)) + 1
        if xs1 - xs0 >= w:
            xs0, xs1 = 0, w
        ys = np.arange(y0, y1); xs = np.arange(xs0, xs1)
        la_g = (90.0 - (ys + 0.5) / h * 180.0)[:, None].astype(np.float32)
        lo_g = (-180.0 + (xs + 0.5) / w * 360.0)[None, :].astype(np.float32)
        d = _sz_gc(la_g, lo_g, la, lo) / rad
        bowl = -np.exp(-(d ** 2) * 2.4) * 0.85
        rim = np.exp(-((d - 1.0) ** 2) * 18.0) * 0.55
        ejecta = np.exp(-((d - 1.35) ** 2) * 3.0) * 0.10
        prof = (bowl + rim + ejecta) * (rad / rmax_deg) ** 0.55 * amp
        prof[d > 2.2] = 0
        hgt[y0:y1][:, np.mod(xs, w)] += prof.astype(np.float32)
    return hgt


# ─────────────────────────── 지구 (실제 대륙 윤곽) ───────────────────────────
# 좌표는 (경도, 위도). 수백 km 오차의 거친 윤곽이지만 128px 지구돋이에서 '지구'로
# 읽히기에는 충분하다. 해안의 프랙털 디테일은 도메인 워핑 노이즈가 만든다.
_SZ_LAND = [
    # 북아메리카 (허드슨만은 윤곽 안의 만)
    [(-168, 66), (-162, 70), (-156, 71.3), (-140, 69.6), (-128, 70), (-115, 68.5), (-95, 68), (-85, 69.5),
     (-82, 66), (-88, 64), (-94, 59), (-92, 57), (-85, 55.2), (-82, 52.5), (-79, 51.5), (-77, 56), (-78, 60),
     (-77.5, 62.5), (-72, 61.8), (-69, 58.9), (-64, 60.3), (-61.5, 56), (-56, 52), (-59.5, 47.6), (-65, 47.5),
     (-64, 44.8), (-65.8, 43.6), (-70, 43.8), (-70, 41.7), (-74, 40.6), (-76, 37), (-75.5, 35.2), (-80, 32.7),
     (-81, 30), (-80, 26.5), (-81, 25.2), (-82.7, 27.8), (-84, 30), (-89, 30.3), (-94, 29.6), (-97.4, 27.8),
     (-97.5, 24), (-97.8, 22.2), (-96, 19), (-94.5, 18.2), (-91, 19), (-90.4, 21), (-87, 21.5), (-87.5, 18.5),
     (-88.3, 16), (-84, 15.8), (-83.3, 12), (-83.6, 10.5), (-80, 9.2), (-77.5, 8.5), (-79.5, 7.3), (-83, 8.2),
     (-86, 11), (-88, 13.2), (-92, 14.5), (-95, 16), (-98, 16.3), (-102, 18), (-105.5, 20.5), (-105.7, 23),
     (-109, 25.5), (-112.2, 29), (-114.8, 31.7), (-113, 29), (-110, 23.2), (-112, 25), (-114.5, 28), (-117, 32.5),
     (-120.5, 34.5), (-122.5, 37.5), (-124, 40.5), (-124, 46), (-124.7, 48.4), (-127.5, 50.5), (-131, 54),
     (-134, 57.5), (-137.5, 58.8), (-141, 60), (-146, 60.8), (-152, 59), (-158, 56.5), (-164, 54.8),
     (-157, 58.8), (-162, 60), (-165.5, 61.5), (-166, 64.5), (-168, 66)],
    # 그린란드
    [(-73, 78), (-60, 82), (-40, 83.5), (-22, 82), (-18, 77), (-20, 72), (-22, 70), (-26, 68.5), (-35, 65.5),
     (-40, 63.5), (-43, 60), (-48, 61), (-51, 64), (-53, 67), (-54, 70), (-57, 74), (-66, 76), (-73, 78)],
    # 배핀섬·북극 제도
    [(-80, 73.5), (-72, 72), (-66, 68), (-62, 66.5), (-65, 63), (-72, 63.5), (-78, 64.5), (-73, 67), (-78, 70),
     (-86, 70.5), (-90, 72), (-80, 73.5)],
    [(-125, 72), (-118, 76.5), (-100, 79), (-85, 80.5), (-70, 83), (-62, 82), (-75, 79), (-80, 76), (-92, 74.5),
     (-100, 73.5), (-110, 70.5), (-125, 72)],
    # 남아메리카
    [(-77.5, 8.5), (-75.5, 10.8), (-72, 12), (-68, 10.6), (-62, 10.7), (-60, 8.5), (-57, 6), (-52, 5), (-50, 1.8),
     (-48.5, -1), (-44, -2.5), (-39, -3.5), (-35, -5.5), (-35, -9), (-37.5, -12.5), (-39, -17.5), (-40.5, -21),
     (-42, -23), (-45, -23.8), (-48.5, -26), (-48.7, -28.5), (-51, -31), (-53, -34), (-57, -35), (-57.5, -38),
     (-62, -39), (-65, -41), (-63.5, -42.7), (-65.5, -45), (-67.5, -46.5), (-66, -48), (-69, -51), (-68.5, -53),
     (-67, -55), (-71, -55), (-74, -52.5), (-75.5, -48), (-74, -44), (-73.5, -40), (-73.3, -37), (-71.6, -33),
     (-71.5, -28), (-70.5, -23.5), (-70.3, -18.5), (-75, -15.5), (-76.3, -13.5), (-78, -10), (-79.5, -7),
     (-81.2, -5.5), (-80.3, -3.5), (-80, -2), (-80.5, 0), (-79, 1.5), (-77.5, 3.8), (-77.3, 7), (-77.5, 8.5)],
    # 아프리카
    [(-17, 21), (-16.5, 24), (-13, 27.5), (-10, 29.5), (-9.5, 32), (-6.5, 34), (-2, 35.2), (3, 36.7), (10, 37.2),
     (11, 35), (10.5, 33.5), (15, 32.3), (20, 31), (20, 32.5), (24, 32), (29, 30.8), (32.3, 31.3), (34, 27.5),
     (35, 24), (37.2, 21), (38.5, 18), (39.7, 15.5), (42, 13), (43.3, 11.5), (51.2, 11.8), (51, 10.4), (49.5, 6.5),
     (47.5, 4), (44, 0), (41, -2), (39.5, -4.5), (39, -6.5), (40.3, -10.5), (40.6, -15), (36.8, -18), (35, -21),
     (35.5, -24), (32.8, -26), (32.4, -29), (30, -31.3), (27, -33.6), (22, -34.2), (18.5, -34.2), (18, -31),
     (15.3, -27), (14.5, -22.5), (11.8, -17.5), (12.2, -13.5), (13.5, -11), (12.3, -6), (9.3, -1), (9.5, 3.5),
     (8.5, 4.5), (5.5, 4.2), (2, 6.3), (-2, 4.8), (-7.5, 4.4), (-10, 6), (-13, 8), (-15, 11), (-17, 14.5),
     (-16.5, 19), (-17, 21)],
    [(49.3, -12), (50.5, -15.5), (49.7, -17.5), (47.5, -25), (45, -25.5), (43.5, -22), (44.3, -18), (46.5, -15.8),
     (49.3, -12)],
    # 유라시아 (이베리아 → 지중해 북안 → 아라비아 → 인도 → 동남아 → 중국 → 한반도 → 극동 → 북극해 → 스칸디나비아)
    [(-9, 43), (-9.5, 39), (-9, 37), (-6, 36.2), (-2, 36.7), (0.5, 38.8), (3, 41.8), (4, 43.5), (7.5, 43.7),
     (10, 44), (13, 41.3), (16, 38.1), (16, 39.5), (18.4, 40.2), (15.8, 41.9), (12.5, 44.2), (13.6, 45.7),
     (15.5, 44), (19.5, 42), (19.8, 39.7), (21, 38), (23, 36.5), (24, 38), (23, 40), (26, 40.8), (26.2, 39.5),
     (28, 37), (30.5, 36.3), (36, 36.5), (35.8, 34.5), (34.9, 32.5), (34.3, 31.3), (34.9, 29.5), (36.5, 26),
     (39, 21.5), (41, 18), (42.8, 15), (43.3, 12.7), (45, 12.8), (48.5, 14), (52, 15.8), (55.5, 17.5), (57, 18.8),
     (59.8, 22.5), (58.8, 23.6), (56.4, 24.8), (56, 26.3), (54, 24.2), (51.5, 24.2), (51, 26), (50, 26.5),
     (48.5, 28.5), (48, 30), (50, 30), (51.5, 27.9), (54.5, 26.6), (57, 25.8), (61.5, 25.2), (66.5, 25.4),
     (68, 23.7), (70, 21), (72.8, 19), (73.5, 15.5), (75, 12), (76.5, 8.6), (77.5, 8), (78.2, 8.9), (79.8, 10.3),
     (80.3, 13.5), (80.2, 15.5), (82.3, 16.6), (86.5, 19.9), (87, 21.5), (89, 21.8), (91.5, 22.5), (92.4, 20.5),
     (94.3, 16), (97.6, 16.5), (98.5, 12), (98.5, 9), (100.5, 7), (100.3, 4), (103.4, 1.4), (104.2, 1.3),
     (103.4, 4.2), (102.2, 6.2), (100.5, 13.5), (102.5, 12), (105, 8.6), (106.5, 10.4), (109.2, 11.6), (109, 15),
     (106.7, 17.5), (107.9, 21.5), (110, 21), (113, 22.2), (117, 23.2), (120, 26.6), (121.8, 30.8), (120.5, 33.5),
     (119, 35), (122.5, 37), (121.5, 37.8), (119, 37.2), (118, 38.5), (117.8, 39.2), (121, 40.8), (124.5, 40),
     (125.2, 37.8), (126.6, 34.4), (129.4, 35.2), (129.4, 37), (128.3, 38.6), (129.8, 41), (131, 42.6),
     (135.5, 43.8), (140.4, 48.2), (141.4, 52.2), (137, 54), (135.2, 54.8), (140.7, 58.3), (148, 59.4),
     (154, 59.2), (156.7, 61.5), (160, 61.8), (163.5, 59.9), (162, 57.8), (156.5, 51), (158.5, 53), (160.5, 54.5),
     (163, 56.2), (163.3, 58), (170.5, 60), (179.9, 62.4), (179.9, 68.8), (176, 69.8), (160, 69.6), (150, 71.5),
     (140, 72.5), (128, 72.5), (113, 73.8), (107, 76.8), (104, 77.7), (95, 76), (87, 74), (80, 72.5), (72, 72.8),
     (68.5, 68.8), (60, 69), (54, 68.5), (44, 68.5), (41, 66.5), (35, 66.5), (33, 69.3), (28, 71), (21, 70.3),
     (15, 68.5), (12.5, 65.5), (10, 63.5), (5.3, 62), (5, 59), (7, 58), (10.6, 59.5), (11.5, 58.5), (12.6, 56.1),
     (14.3, 55.5), (16.5, 56.5), (18.5, 59.3), (17.5, 61), (17.3, 62.5), (21.5, 64.8), (25.4, 65.3), (24.5, 63),
     (21.2, 61), (22.8, 60), (28, 60.5), (30, 59.9), (23.5, 59.2), (24, 57.8), (21.5, 57.3), (21, 55.8),
     (18.5, 54.7), (14.2, 53.9), (12, 54.2), (10.9, 53.9), (10.4, 57.5), (8.2, 56.9), (8.6, 55.5), (8.6, 53.5),
     (7, 53.3), (4.8, 52.9), (3.2, 51.3), (1.6, 50.9), (-1.5, 49.6), (-4.7, 48.5), (-2.3, 47.2), (-1.2, 45.5),
     (-1.8, 43.4), (-8, 43.7), (-9, 43)],
    # 섬들
    [(130.9, 33.9), (132.5, 35.4), (135.5, 35.6), (136.8, 37.3), (139, 38), (140, 40.5), (141.5, 41.4), (142, 39),
     (141, 37), (140.8, 35.7), (139.8, 35), (138.8, 34.6), (137, 34.6), (135.2, 33.8), (133, 34.2), (130.9, 33.9)],
    [(129.8, 33.3), (131.7, 33.2), (131.3, 31.4), (130.2, 31.2), (129.8, 33.3)],
    [(132.5, 34), (134.6, 34.2), (134.2, 33.2), (132.8, 32.8), (132.5, 34)],
    [(140, 41.5), (141.3, 45.4), (145.3, 43.3), (143.3, 42), (140, 41.5)],
    [(142, 46), (143.5, 49), (142.8, 54.3), (142, 51), (142, 46)],
    [(120.2, 23), (121.5, 25.2), (121.8, 24), (120.8, 22), (120.2, 23)],
    [(108.7, 19), (110.5, 20.1), (111, 19.6), (109.5, 18.2), (108.7, 19)],
    [(120, 16), (120.6, 18.5), (122.3, 18.4), (122, 16.5), (124, 13), (120.6, 14), (120, 16)],
    [(122, 7), (125.5, 9.5), (126.5, 7), (125.3, 5.7), (122, 7)],
    [(123, 11), (125.5, 11.3), (124.5, 10), (122.5, 10), (123, 11)],
    [(109, 1.5), (110, -2), (114, -3.8), (116.5, -2.5), (118, 1), (119, 5), (117, 7), (115.5, 5), (113, 3.2),
     (110, 1.8), (109, 1.5)],
    [(95.3, 5.5), (97.5, 5.2), (100.5, 1.5), (104, -1), (106, -3.2), (105.8, -5.8), (104, -5), (101.5, -3),
     (99, 0.5), (96.8, 3.5), (95.3, 5.5)],
    [(105.3, -6.8), (108, -6.3), (111, -6.4), (114.5, -7.7), (114.5, -8.5), (111, -8.2), (106.5, -7.4), (105.3, -6.8)],
    [(119.5, -5.5), (120.5, -2), (119.8, 0.5), (121, 1.2), (125, 1.5), (123, 0.5), (121.5, -1), (123, -4),
     (121, -4.5), (120.5, -5.8), (119.5, -5.5)],
    [(131, -1.3), (135, -3.3), (138, -1.6), (141, -2.6), (145.8, -5), (147.8, -6.5), (150.5, -10.5), (147, -10),
     (143.5, -9), (141, -9.1), (138, -8.3), (137.8, -5.5), (134, -4), (131.5, -3), (131, -1.3)],
    # 오스트레일리아·뉴질랜드
    [(113.5, -22), (114.2, -26), (115, -29.5), (115, -33.6), (117.8, -35.1), (121, -33.8), (124, -32.9),
     (126, -32.3), (129, -31.6), (131, -31.5), (134.2, -32.7), (135.8, -34.8), (138, -34.5), (139.5, -36),
     (140.5, -38), (143.5, -38.8), (146, -39.1), (148, -37.8), (150, -37.5), (150.6, -35), (151.3, -33.7),
     (152.8, -31.5), (153.6, -28.5), (153.2, -25.5), (150.8, -22.6), (149, -20.6), (146.3, -19), (145.4, -16),
     (145.3, -14.8), (143.5, -14), (142.5, -10.8), (141.6, -12.8), (141.6, -16.5), (140.8, -17.4),
     (139.2, -17.4), (137, -15.8), (135.8, -15), (136.8, -12.2), (136, -11.9), (132.5, -11.4), (131, -12.2),
     (129.5, -14.9), (128, -15), (126.5, -14), (125, -15), (123.5, -16.8), (122.3, -17.8), (121, -19.5),
     (118.8, -20.3), (116.7, -20.6), (114.2, -21.8), (113.5, -22)],
    [(144.7, -40.7), (148.3, -40.9), (148, -43), (146.5, -43.6), (145.2, -42.3), (144.7, -40.7)],
    [(172.7, -34.5), (174.5, -36), (176, -37.6), (178.5, -37.7), (177, -39.3), (176.6, -40.5), (175.2, -41.6),
     (174.6, -39.8), (173.8, -39.2), (174.5, -37), (172.7, -34.5)],
    [(172.7, -40.5), (174.2, -41.7), (173, -43.8), (171, -45), (169, -46.6), (166.5, -46), (167, -44.5),
     (171, -42), (172.7, -40.5)],
    # 유럽 섬·기타
    [(-5.7, 50), (1.3, 51.1), (1.7, 52.7), (0, 53.5), (-1.6, 55.6), (-2, 57.6), (-4, 58.6), (-5, 58.6),
     (-6.2, 56.5), (-5.5, 55.5), (-3, 54.9), (-3.2, 53.4), (-4.7, 52.8), (-5.2, 51.7), (-3, 51.5), (-5.7, 50)],
    [(-10, 51.6), (-6, 52.1), (-6, 54.8), (-8, 55.2), (-10, 54.2), (-10, 51.6)],
    [(-24, 65.5), (-21, 66.4), (-15, 66.5), (-13.5, 65), (-18.5, 63.4), (-22.5, 63.8), (-24, 65.5)],
    [(-85, 21.9), (-82, 23.1), (-77, 21.7), (-74.2, 20.2), (-77.5, 19.8), (-81, 21.7), (-85, 21.9)],
    [(-74.4, 19.8), (-70, 19.9), (-68.4, 18.6), (-71.5, 17.6), (-74.4, 18.4), (-74.4, 19.8)],
    [(79.8, 8), (80.2, 9.8), (81.9, 7.3), (81.2, 6.2), (80, 6.1), (79.8, 8)],
    [(52, 71.5), (56, 74.5), (68, 76.8), (62, 75), (57, 72.5), (52, 71.5)],
    [(11, 78.5), (17, 80.3), (27, 80), (21, 78), (14, 77), (11, 78.5)],
    [(9.5, 41.2), (9.6, 39), (8.4, 39), (8.2, 40.9), (9.5, 41.2)],
    [(12.4, 38.1), (15.6, 38.3), (15.1, 36.7), (12.4, 37.6), (12.4, 38.1)],
    # 남극 반도
    [(-57, -63.5), (-60, -63.8), (-64, -65.5), (-67, -68), (-68, -70.5), (-75, -72.5), (-60, -74), (-57, -63.5)],
]
_SZ_WATER = [   # 대륙 윤곽 안의 내해
    [(28, 41.2), (29, 44.5), (31, 46.6), (33.5, 44.5), (36.5, 45.2), (39.5, 47), (38, 44.3), (41.5, 41.5),
     (36, 41.7), (33, 42), (29, 41.1), (28, 41.2)],
    [(47, 44.5), (50, 46.5), (53, 47), (53, 45), (51, 44.5), (51.5, 41.5), (53, 40), (53.8, 37.4), (51, 36.7),
     (49.2, 37.6), (48.8, 39), (49.5, 40.5), (47.5, 42.5), (47, 44.5)],
    [(-89, 60), (-87, 57), (-82.5, 55), (-79.5, 51.5), (-77.5, 55.5), (-78.5, 59), (-78, 62.3), (-83, 63.8),
     (-87, 64.2), (-90, 63.5), (-94, 61), (-89, 60)],
    [(118.5, 38.2), (121, 40.4), (122.2, 39.2), (121.5, 38.5), (119.5, 37.5), (118.5, 38.2)],
]


def _sz_regions(lat, lon, items):
    """(위도, 경도, r위도, r경도, 가중치) 목록 → 부드러운 가중치 합(최대 1)."""
    out = np.zeros(lat.shape, np.float32)
    for la, lo, rla, rlo, wgt in items:
        d = _sz_ellipse(lat, lon, la, lo, rla, rlo)
        out = np.maximum(out, wgt * np.exp(-(d ** 2) * 1.6))
    return out


def tex_sz_earth(shape=(2048, 4096)):
    """지구 — 색·높이·도시불빛·구름·바다 마스크. 림(1080px) 확대를 견디도록 4096 폭."""
    h, w = shape
    lat, lon = _sz_ll(shape)
    base = _sz_poly_mask(shape, [(p, 255) for p in _SZ_LAND], ss=2)
    wat = _sz_poly_mask(shape, [(p, 255) for p in _SZ_WATER], ss=2)
    base = np.clip(base - wat, 0, 1)
    # 남극: 위도 -68 부근을 노이즈로 흔든 해안
    ant = (lat < (-69.5 + (_sz_fbm(shape, 3, 5, seed=7) - 0.5) * 9.0 * (1 - np.abs(np.sin(np.radians(lon * 0.5 + 20)))))).astype(np.float32)
    base = np.maximum(base, ant)
    # 도메인 워핑 — 해안선을 대륙 규모에서 한 번, 해안 규모에서 한 번 흔든다
    wx = (_sz_fbm(shape, 5, 5, seed=11) - 0.5) * (w / 360.0) * 2.6
    wy = (_sz_fbm(shape, 5, 5, seed=12) - 0.5) * (h / 180.0) * 1.8
    wx += (_sz_fbm(shape, 24, 4, seed=13) - 0.5) * (w / 360.0) * 0.9
    wy += (_sz_fbm(shape, 24, 4, seed=14) - 0.5) * (h / 180.0) * 0.7
    yy = np.arange(h, dtype=np.float32)[:, None] + wy
    xx = np.arange(w, dtype=np.float32)[None, :] + wx
    # 다각형 윤곽을 반경 ~0.45° 로 흐린 뒤 다중 스케일 노이즈로 문턱을 흔든다 → 곧은 변이 프랙털 해안이 된다
    # (1차: 1.5px 만 흐려 노이즈가 해안을 못 파고들어, 림 확대에서 일본 열도가 다각형으로 보였다)
    m = _sz_sample(_sz_blur(base, w / 360.0 * 0.45), yy, xx)
    det = _sz_fbm(shape, 40, 5, seed=15, gain=0.55)
    det2 = _sz_fbm(shape, 12, 4, seed=16)
    det3 = _sz_fbm(shape, 110, 3, seed=17)
    landf = m + (det - 0.5) * 0.45 + (det2 - 0.5) * 0.35 + (det3 - 0.5) * 0.22
    near = _sz_blur((m > 0.2).astype(np.float32), w / 360.0 * 1.5)
    islets = (det3 > 0.72) * (near > 0.05) * (m < 0.3) * 0.6        # 해안 근처 작은 섬들
    landf = np.maximum(landf, islets + (det3 - 0.72) * 0.5)
    land = _sz_smoothstep(0.47, 0.53, landf)
    coast = _sz_blur(land, w / 360.0 * 0.6)                       # 해안에서의 거리(대륙붕)

    # 높이 — 산맥 지역 × 능선 노이즈
    ridge = 1.0 - np.abs(_sz_fbm(shape, 14, 6, seed=21, gain=0.55) - 0.5) * 2.0
    ridge = ridge ** 3
    mtn = _sz_regions(lat, lon, [
        (33, 86, 6, 16, 1.0), (28, 84, 2.5, 12, 1.0), (40, 72, 4, 8, 0.8), (-15, -70, 12, 3, 1.0),
        (-35, -70, 10, 2.2, 0.9), (45, -115, 10, 6, 0.8), (55, -125, 8, 4, 0.7), (46, 10, 2, 6, 0.8),
        (42, 44, 2, 5, 0.6), (38, 58, 3, 8, 0.5), (0, 36, 10, 4, 0.5), (62, 130, 6, 20, 0.4),
        (-28, 29, 4, 3, 0.4), (38, 105, 4, 10, 0.4), (72, -40, 10, 14, 0.6), (-80, 60, 8, 120, 0.4)])
    hgt = land * (0.18 + 0.20 * _sz_fbm(shape, 8, 6, seed=22) + mtn * ridge * 0.9)
    hgt = np.clip(hgt, 0, 1)

    # 기후 — 사막·우림·한대. 지역 타원을 워핑한 좌표에서 평가하고 노이즈 문턱으로 자른다.
    # 워핑 없이 부드러운 가중치를 색 램프에 그대로 넣으면 과녁 같은 동심원 띠가 생긴다(1차 실패)
    latw = lat + (_sz_fbm(shape, 6, 5, seed=33) - 0.5) * 9.0
    lonw = lon + (_sz_fbm(shape, 6, 5, seed=34) - 0.5) * 16.0
    dry = _sz_regions(latw, lonw, [
        (23, 10, 9, 26, 1.0), (23, 47, 8, 10, 1.0), (31, 58, 5, 12, 0.75), (27, 70.5, 3, 4, 0.7),
        (39, 83, 3, 8, 0.95), (43, 105, 4, 12, 0.5), (46, 64, 5, 15, 0.5), (-25, 131, 8, 14, 0.95),
        (-24, 19, 6, 6, 0.75), (31, -111, 6, 6, 0.7), (-23, -69.5, 6, 1.8, 0.9), (-45, -68, 6, 4, 0.6),
        (8, 46, 5, 5, 0.6), (40, -116, 4, 4, 0.55), (16, 30, 3, 10, 0.8), (35, 35, 3, 4, 0.4),
        (24, -5, 8, 14, 1.0), (20, 25, 7, 14, 1.0)])
    dry = _sz_smoothstep(0.28, 0.62, dry + (_sz_fbm(shape, 12, 5, seed=31) - 0.5) * 0.5
                         + (_sz_fbm(shape, 48, 4, seed=36) - 0.5) * 0.45)
    wet = _sz_regions(latw, lonw, [
        (-5, -62, 9, 15, 1.0), (0, 20, 6, 10, 1.0), (0, 112, 8, 20, 0.9), (15, 100, 6, 6, 0.6),
        (12, -85, 6, 6, 0.7), (-20, -44, 6, 4, 0.6), (37, -82, 8, 10, 0.6), (50, 12, 7, 20, 0.55),
        (28, 112, 8, 8, 0.6), (-5, 145, 5, 8, 0.8), (35, 135, 5, 6, 0.6), (20, 80, 8, 8, 0.35)])
    wet = _sz_smoothstep(0.3, 0.65, wet + (_sz_fbm(shape, 10, 5, seed=32) - 0.5) * 0.5) * (1 - dry)
    al = np.abs(lat)
    boreal = _sz_smoothstep(46, 55, al) * (1 - _sz_smoothstep(64, 69, al)) * (lat > 0)
    tundra = _sz_smoothstep(62, 70, al)
    ice = np.clip(_sz_smoothstep(74, 79, al) + ant, 0, 1)
    gl = _sz_regions(lat, lon, [(74, -41, 12, 24, 1.0)])          # 그린란드 빙상
    ice = np.maximum(ice, np.clip(gl * 1.6, 0, 1))

    tex = _sz_fbm(shape, 30, 5, seed=41)
    C = lambda c: _sz_col(shape, c)
    col = C((0.22, 0.32, 0.12))                                   # 온대 초원·숲 (1차는 너무 어두워 림에서 회녹색 덩어리였다)
    semi = _sz_smoothstep(0.25, 0.65, _sz_regions(latw, lonw, [(12, 15, 5, 30, 1.0), (-15, 25, 6, 12, 0.8),
                                                                 (45, 50, 6, 25, 0.8), (-30, 135, 12, 20, 0.8),
                                                                 (38, -102, 8, 6, 0.8), (-32, -62, 6, 6, 0.7)])
                          + (_sz_fbm(shape, 14, 4, seed=35) - 0.5) * 0.5)
    col = _sz_mix(col, C((0.46, 0.43, 0.24)), np.clip(np.maximum(semi, dry), 0, 1))                  # 스텝·사바나
    desert = np.where((lon > 110) & (lat < -10), 1.0, 0.0).astype(np.float32)
    dcol = _sz_mix(C((0.80, 0.64, 0.43)), C((0.72, 0.44, 0.26)), desert)                             # 오스트레일리아는 붉은 사막
    dune = _sz_fbm(shape, 70, 5, seed=37, stretch=2.5, gain=0.6)
    rock = _sz_smoothstep(0.55, 0.8, _sz_fbm(shape, 20, 5, seed=38))
    dcol = dcol * (0.78 + 0.40 * dune[..., None])
    dcol = _sz_mix(dcol, C((0.46, 0.34, 0.24)), rock * 0.55)                                         # 암석 사막·산지
    col = _sz_mix(col, dcol, dry)
    col = _sz_mix(col, C((0.08, 0.22, 0.07)), wet)                                                     # 우림
    col = _sz_mix(col, C((0.11, 0.19, 0.09)), boreal * (1 - dry))                                     # 침엽수림
    col = _sz_mix(col, C((0.38, 0.35, 0.29)), tundra)
    col = _sz_mix(col, C((0.45, 0.39, 0.32)), np.clip(mtn * ridge * 1.4, 0, 1) * 0.8)                 # 산악 암석
    col = _sz_mix(col, C((0.88, 0.90, 0.94)), np.clip(_sz_smoothstep(0.55, 0.9, mtn * ridge) * (al > 25), 0, 1) * 0.85)  # 설선
    tex2 = _sz_fbm(shape, 80, 6, seed=43, gain=0.6)
    col = col * (0.70 + 0.30 * tex[..., None] + 0.30 * tex2[..., None])
    col = _sz_mix(col, C((0.30, 0.30, 0.16)), _sz_smoothstep(0.55, 0.8, tex2) * (1 - dry) * 0.35)
    col = _sz_mix(col, C((0.93, 0.95, 0.98)), ice)
    # 바다 — 딥블루(운영자 지정). 대륙붕은 한 톤 밝게
    ocn = _sz_mix(C((0.025, 0.10, 0.36)), C((0.045, 0.19, 0.50)), _sz_smoothstep(0.05, 0.6, coast) * 0.45)
    ocn = ocn * (0.94 + 0.12 * _sz_fbm(shape, 6, 4, seed=42)[..., None])
    sea_ice = _sz_smoothstep(76, 82, lat) + _sz_smoothstep(66, 72, -lat)
    ocn = _sz_mix(ocn, C((0.78, 0.84, 0.92)), np.clip(sea_ice * (0.6 + 0.4 * tex), 0, 1))
    rgb = _sz_mix(ocn, col, land)
    _sz_save_rgb(rgb, "earth", sat=1.05, fade=False)
    _sz_save_raw(hgt, "earth_h", bits16=True)
    _sz_save_raw(1.0 - land, "earth_ocean")

    # 도시 불빛 — 인구 지역 가중치 × 점 샘플 (사막·빙하·바다 제외, 나일강은 예외)
    pop = _sz_regions(lat, lon, [
        (50, 10, 8, 18, 1.0), (53, -2, 3, 3, 1.0), (38, -80, 7, 10, 1.0), (41, -90, 4, 8, 0.7),
        (36, -120, 6, 3, 0.7), (20, -100, 4, 5, 0.6), (-22, -46, 4, 5, 0.8), (-34, -59, 2, 3, 0.6),
        (23, 79, 9, 8, 0.9), (32, 116, 9, 8, 1.0), (36.8, 127.6, 2.0, 1.6, 1.25), (35.6, 137, 3, 6, 1.2),
        (28, 31.2, 6, 1.0, 0.95), (7, 5, 3, 4, 0.5), (55.7, 37.6, 5, 8, 0.7), (30, 48, 5, 8, 0.6),
        (14, 102, 5, 5, 0.5), (-7, 110, 1, 5, 0.8), (24, 121, 1.5, 1, 1.0), (-34, 151, 3, 4, 0.5),
        (-26, 28, 3, 3, 0.5), (45, -75, 3, 6, 0.6), (40, 30, 4, 8, 0.6), (22.5, 114, 2, 2, 1.2),
        (31, 121.5, 1.5, 1.5, 1.2), (39.9, 116.4, 1.5, 1.5, 1.1), (14.6, 121, 1.2, 1.2, 0.9)])
    habitable = land * (1 - ice) * (1 - 0.85 * _sz_smoothstep(0.6, 0.9, dry))
    habitable = np.maximum(habitable, _sz_regions(lat, lon, [(28, 31.2, 6, 0.8, 1.0)]) * land)
    dens = np.maximum(pop, 0.12) * habitable
    r = np.random.default_rng(777)
    n = 260000
    pl = np.degrees(np.arcsin(r.uniform(-1, 1, n))); po = r.uniform(-180, 180, n)
    py = np.clip(((90 - pl) / 180 * h).astype(np.int32), 0, h - 1)
    px = np.clip(((po + 180) / 360 * w).astype(np.int32), 0, w - 1)
    keep = r.random(n) < dens[py, px] ** 1.4
    lights = np.zeros(shape, np.float32)
    bright = np.exp(r.normal(-0.4, 0.8, n))
    np.add.at(lights, (py[keep], px[keep]), bright[keep])
    # 넓은 번짐을 줄여야 확대(림)에서 '불빛 덩어리'가 아니라 '불빛 알갱이'로 보인다
    lights = _sz_blur(lights, 0.6) * 1.8 + _sz_blur(lights, 2.0) * 0.35 + _sz_blur(dens * land, 1.5) * 0.04
    # 확대용 부드러운 밀도 맵 — 림(텍셀 1개 ≈ 4px)에서는 점 맵이 격자 모양 사각 점으로 보여서,
    # Blender 가 이 밀도 × 절차적 보로노이 알갱이로 불빛을 만든다
    dsm = _sz_blur(lights, 2.5)
    _sz_save_raw(np.clip(dsm / np.percentile(dsm[dsm > 0], 99.0), 0, 1) ** 0.7, "earth_lightsd")
    lights = np.clip(lights / np.percentile(lights[lights > 0], 99.3), 0, 1) ** 0.8
    _sz_save_raw(lights, "earth_lights")

    # 구름 — 적도 수렴대(뭉게), 아열대 맑음, 중위도 폭풍대(소용돌이), 극
    cw, ch = w, h
    cl = _sz_fbm(shape, 6, 8, seed=51, gain=0.56)
    # 저기압 소용돌이 — 북반구 반시계, 남반구 시계 (위에서 봤을 때)
    yy = np.arange(ch, dtype=np.float32)[:, None].repeat(cw, 1)
    xx = np.arange(cw, dtype=np.float32)[None, :].repeat(ch, 0)
    rs = np.random.default_rng(52)
    cyc = [(rs.uniform(38, 62) * s, rs.uniform(-180, 180), rs.uniform(5, 9)) for s in (1, -1) for _ in range(9)]
    cyc += [(rs.uniform(12, 22) * s, rs.uniform(-180, 180), rs.uniform(3, 4.5)) for s in (1, -1) for _ in range(3)]
    for la0, lo0, rad in cyc:
        cy0 = (90 - la0) / 180 * ch; cx0 = (lo0 + 180) / 360 * cw
        dx = xx - cx0; dx = (dx + cw / 2) % cw - cw / 2
        dx = dx * math.cos(math.radians(la0))
        dy = yy - cy0
        rp = rad / 180 * ch
        d2 = (dx ** 2 + dy ** 2) / (rp ** 2)
        ang = (2.6 if la0 > 0 else -2.6) * np.exp(-d2 * 0.9)
        m = d2 < 9
        c, s = np.cos(ang[m]), np.sin(ang[m])
        ndx = dx[m] * c - dy[m] * s; ndy = dx[m] * s + dy[m] * c
        xx[m] = cx0 + ndx / math.cos(math.radians(la0)); yy[m] = cy0 + ndy
    cl = _sz_sample(cl, yy, xx)
    fine = _sz_fbm(shape, 48, 5, seed=53, gain=0.6)
    band = (0.34 * np.exp(-((lat - 5) / 6.0) ** 2) * _sz_fbm(shape, 10, 3, seed=55) * 1.6   # ITCZ (뭉게뭉게 끊기게)
            - 0.28 * np.exp(-((al - 24) / 7.0) ** 2)                          # 아열대 고기압
            + 0.32 * np.exp(-((al - 52) / 11.0) ** 2)                         # 폭풍대
            + 0.12 * _sz_smoothstep(65, 80, al))
    cov = cl * 0.9 + fine * 0.25 + band * 0.55 - 0.02 * land
    clouds = _sz_smoothstep(0.58, 0.86, cov)      # 실제 지구 운량 ~60%대 — 0.66 문턱은 너무 맑았다
    clouds = np.clip(clouds * (0.75 + 0.35 * fine), 0, 1)
    # 가느다란 권운 줄무늬 (동서로 늘어진 노이즈)
    cir = _sz_fbm(shape, 10, 6, seed=54, stretch=5.0)
    clouds = np.maximum(clouds, _sz_smoothstep(0.64, 0.80, cir) * 0.45 * np.exp(-((al - 45) / 16.0) ** 2))
    _sz_save_raw(clouds, "earth_clouds")


# ─────────────────────────── 달 (실제 앞면 바다) ───────────────────────────
_SZ_MARIA = [   # (위도, 경도, r위도, r경도) — 지름(km)/2/30.3 = 반지름(도)
    (33, -16, 16, 19), (28, 17.5, 10, 11), (8.5, 31.4, 12, 13), (1, 24, 6, 7), (17, 59, 7.5, 9),
    (-6, 51, 11, 7), (-15.2, 35.5, 5.5, 5.5), (-21.3, -16.6, 10, 11), (-24.4, -38.6, 6, 6.2),
    (20, -55, 14, 12), (5, -50, 12, 11), (30, -48, 9, 10), (-5, -40, 8, 9), (10, -35, 8, 8),
    (56, 0, 4.5, 38), (13.3, 3.6, 4, 5), (-10, -23, 6, 6), (7.5, -30.9, 7, 8), (40, -30, 8, 12),
    (-5.2, -68.6, 3, 3), (-25, -60, 4, 4), (12, 86, 5, 5), (-2, 86, 4, 5), (51.6, -9.4, 1.7, 2.6),
    (-20, 145, 5, 6), (24, 160, 4, 4)]


def tex_sz_moon(shape=(1024, 2048)):
    h, w = shape
    lat, lon = _sz_ll(shape)
    mar = np.zeros(shape, np.float32)
    warp = (_sz_fbm(shape, 6, 5, seed=61) - 0.5) * 0.9
    warp2 = (_sz_fbm(shape, 14, 6, seed=67, gain=0.6) - 0.5) * 0.7   # 해안선 같은 불규칙 경계
    dshade = np.random.default_rng(68)
    for la, lo, rla, rlo in _SZ_MARIA:
        d = _sz_ellipse(lat, lon, la, lo, rla * 1.28, rlo * 1.28) + warp + warp2   # 크게 잡아 서로 이어지게(실제 앞면의 '얼굴')
        # 경계를 넓게 풀어 둥근 도장처럼 보이지 않게 한다(1차 시안의 문제). 바다마다 짙기도 다르다
        mar = np.maximum(mar, (1.0 - _sz_smoothstep(0.62, 1.08, d)) * dshade.uniform(0.75, 1.0))
    mar = np.clip(mar * (0.85 + 0.3 * _sz_fbm(shape, 12, 5, seed=69)), 0, 1)
    region = lambda la, lo: 0.25 + 0.75 * float(1.0 - _sz_smoothstep(0.78, 1.02,
                                                  min([math.hypot((la - a) / b, _sz_wrap(lo - c) * math.cos(math.radians(a)) / (d * math.cos(math.radians(a)))) for a, c, b, d in _SZ_MARIA])))
    # 512px 달에서 1px ≈ 7km. 무작위 크레이터는 반지름 2.6° 까지만 — 7° 까지 두었더니 거품 무늬(골프공)가 됐다
    hgt = _sz_craters(shape, 1600, 0.25, 2.6, seed=62, power=3.6, amp=1.0, region=region)
    # 큰 크레이터를 이름 있는 자리에 (티코·코페르니쿠스·클라비우스·플라톤·케플러·아리스타르코스)
    named = [(-43.3, -11.2, 1.45), (9.6, -20.1, 1.55), (-58.4, -14.4, 3.7), (51.6, -9.4, 1.7), (8.1, -38, 0.55),
             (23.7, -47.4, 0.7), (-9, 26, 1.6), (-29, 61, 1.9), (-27, 15, 1.3)]
    for la, lo, rad in named:
        d = _sz_gc(lat, lon, la, lo) / rad
        hgt += (-np.exp(-(d ** 2) * 2.4) * 0.85 + np.exp(-((d - 1.0) ** 2) * 18.0) * 0.55) * 0.9
    hgt += (_sz_fbm(shape, 10, 6, seed=63) - 0.5) * 0.6 * (1 - mar * 0.7)
    hgt -= mar * 0.35
    hgt = (hgt - hgt.min()) / (hgt.max() - hgt.min())
    # 광조 — 티코·코페르니쿠스·케플러·아리스타르코스
    rays = np.zeros(shape, np.float32)
    rr = np.random.default_rng(64)
    for la, lo, rad, reach, strength in [(-43.3, -11.2, 1.45, 40, 1.0), (9.6, -20.1, 1.55, 22, 0.8),
                                          (8.1, -38, 0.55, 12, 0.6), (23.7, -47.4, 0.7, 10, 0.9)]:
        d = _sz_gc(lat, lon, la, lo)
        dx = _sz_wrap(lon - lo) * np.cos(np.radians(lat)); dy = lat - la
        th = np.arctan2(dy, dx)
        spokes = np.zeros(shape, np.float32)
        for _ in range(16):   # 광조는 가는 바큇살이 아니라 넓고 흐린 줄기 — 1차 시안은 선이 너무 곧고 가늘었다
            a0 = rr.uniform(-math.pi, math.pi); wd = rr.uniform(0.05, 0.13); ln = reach * rr.uniform(0.4, 1.0)
            da = np.abs(np.angle(np.exp(1j * (th - a0))))
            spokes = np.maximum(spokes, np.exp(-(da / wd) ** 2) * np.exp(-(d / ln) ** 2))
        halo = np.exp(-((d / (rad * 2.4)) ** 2))
        rays += strength * (spokes * _sz_smoothstep(rad * 0.9, rad * 1.6, d) * 0.5 + halo * 0.6)
        if strength >= 0.9:
            rays += np.exp(-((d / (rad * 0.8)) ** 2)) * 0.5
    rays = np.clip(rays, 0, 1) * (0.6 + 0.4 * _sz_fbm(shape, 30, 3, seed=65))
    tone = _sz_fbm(shape, 20, 5, seed=66)
    g = 0.60 + (tone - 0.5) * 0.10 + (hgt - 0.5) * 0.10
    g = g * (1 - mar * 0.40) + rays * 0.24
    rgb = np.dstack([g * 1.00, g * 0.985, g * 0.955])
    rgb = _sz_mix(rgb, rgb * np.array([0.97, 0.98, 1.03], np.float32), mar)   # 티타늄 많은 바다는 살짝 푸름
    _sz_save_rgb(np.clip(rgb, 0, 1), "moon", sat=1.0)
    _sz_save_raw(hgt, "moon_h", bits16=True)


# ─────────────────────────── 화성 v2 ───────────────────────────
def tex_mars_v2(shape=(1024, 2048)):
    """매리너 협곡·타르시스 3산+올림푸스·시르티스·헬라스·극관 78°. 크레이터는 120개·진폭 절반."""
    h, w = shape
    lat, lon = _sz_ll(shape)
    n1 = _sz_fbm(shape, 3, 7, seed=71)
    n2 = _sz_fbm(shape, 16, 5, seed=72)
    dark = _sz_regions(lat, lon, [
        (8, 69, 12, 8, 1.0), (46, -22, 10, 22, 0.8), (-25, -40, 10, 25, 0.75), (-2, 5, 5, 16, 0.8),
        (-20, 145, 10, 25, 0.7), (-30, -155, 9, 25, 0.7), (-25, -86, 5, 7, 0.7), (-20, 110, 9, 16, 0.7),
        (-12, 40, 6, 18, 0.55), (40, 75, 6, 25, 0.35), (-45, 10, 8, 30, 0.45), (58, 150, 5, 40, 0.3)])
    dark = np.clip(dark * (0.65 + 0.7 * n2) + (n1 - 0.5) * 0.35, 0, 1)
    bright = _sz_regions(lat, lon, [(-42, 70, 9, 12, 1.0), (-50, -43, 6, 8, 0.7), (5, -110, 18, 25, 0.5),
                                    (20, 20, 12, 30, 0.45), (25, 150, 12, 20, 0.4)])
    hgt = _sz_craters(shape, 120, 0.4, 3.0, seed=73, power=3.0, amp=0.35)
    # 헬라스·아르기레 분지 (넓은 함몰)
    for la, lo, rad, dep in [(-42, 70, 11, 0.6), (-50, -43, 7, 0.4)]:
        d = _sz_gc(lat, lon, la, lo) / rad
        hgt += -np.exp(-(d ** 2) * 1.8) * dep + np.exp(-((d - 1.05) ** 2) * 8) * dep * 0.35
    # 타르시스 방패 화산 — 완만한 원뿔 + 꼭대기 칼데라
    vol = [(-8.3, -120.5, 3.7, 1.0), (1.5, -112.8, 3.2, 0.9), (11.9, -104.5, 3.9, 1.0), (18.6, -134, 5.2, 1.5),
           (25, 147, 2.5, 0.5)]
    for la, lo, rad, hh in vol:
        d = _sz_gc(lat, lon, la, lo) / rad
        cone = np.clip(1 - d, 0, 1) ** 1.5 * hh * 0.5
        cald = np.exp(-((d / 0.16) ** 2)) * hh * 0.45
        scarp = (np.exp(-((d - 1.0) ** 2) * 60) * 0.25 * hh) if hh > 1.2 else 0
        hgt += cone - cald + scarp
    volc_alb = np.zeros(shape, np.float32)
    for la, lo, rad, hh in vol:
        d = _sz_gc(lat, lon, la, lo) / rad
        # 속이 찬 어두운 점 + 밝은 정상 — 고리 모양으로 칠하면 크레이터처럼 읽혔다
        volc_alb = np.maximum(volc_alb, (1 - _sz_smoothstep(0.35, 1.05, d)) * min(1.0, hh) * 0.8)
    tharsis = _sz_regions(lat, lon, [(2, -110, 16, 22, 1.0)])
    hgt += tharsis * 0.35
    # 매리너 협곡 — 서→동 여러 줄기 (녹티스 미로 → 이우스 → 멜라스/칸도르 → 코프라테스 → 에오스 → 혼돈지형)
    vm = np.zeros(shape, np.float32)
    # 폭(도): 실제 협곡 폭 100~600km ÷ 59km/도. 1차 시안(0.9~1.4)은 펜 선처럼 보였다
    segs = [(-6.5, -98, -7.2, -84, 1.6), (-7.2, -84, -9.5, -72, 2.0), (-5.5, -80, -6.5, -66, 2.2),
            (-9.5, -72, -12.8, -58, 1.7), (-12.8, -58, -12.5, -44, 1.8), (-12.5, -44, -8, -34, 2.6),
            (-10.5, -74, -10, -62, 2.6)]
    wig = (_sz_fbm(shape, 30, 4, seed=74) - 0.5) * 1.2
    for la0, lo0, la1, lo1, wd in segs:
        dx = lo1 - lo0; dy = la1 - la0; L2 = dx * dx + dy * dy
        t = np.clip(((lon - lo0) * dx + (lat - la0) * dy) / L2, 0, 1)
        px = lo0 + t * dx; py = la0 + t * dy
        dd = np.sqrt((lon - px) ** 2 + (lat - py) ** 2) + wig
        vm = np.maximum(vm, np.exp(-(np.maximum(dd, 0) / wd) ** 2 * 2.2))
    noct = _sz_regions(lat, lon, [(-7, -102, 3, 5, 1.0)]) * _sz_smoothstep(0.55, 0.75, _sz_fbm(shape, 60, 3, seed=75))
    vm = np.maximum(vm, noct * 0.7)
    hgt -= vm * 0.45        # 깊이보다 알베도로 읽히게 — 범프가 세면 검은 균열선이 된다
    hgt += (n2 - 0.5) * 0.25
    hgt = (hgt - hgt.min()) / (hgt.max() - hgt.min())
    # 색 — 버터스카치 기본, 어두운 현무암, 밝은 먼지, 협곡 바닥은 짙은 적갈
    t = np.clip(0.58 + (n1 - 0.5) * 0.6 + bright * 0.25 - dark * 0.85, 0, 1)
    r, g, b = ramp(t, [(0.0, (0.30, 0.15, 0.09)), (0.35, (0.50, 0.26, 0.14)), (0.6, (0.74, 0.43, 0.24)),
                       (0.85, (0.86, 0.57, 0.36)), (1.0, (0.92, 0.70, 0.50))])
    rgb = np.dstack([r, g, b]).astype(np.float32)
    halo = _sz_blur(vm, shape[1] / 360.0 * 3.0) * (0.6 + 0.8 * _sz_fbm(shape, 20, 4, seed=79))
    rgb = _sz_mix(rgb, _sz_col(shape, (0.42, 0.20, 0.11)), np.clip(halo * 1.1, 0, 0.6))    # 코프라테스 일대의 어두운 번짐
    rgb = _sz_mix(rgb, _sz_col(shape, (0.36, 0.17, 0.10)), np.clip(vm * 0.85, 0, 1))
    rgb = _sz_mix(rgb, _sz_col(shape, (0.42, 0.22, 0.13)), np.clip(volc_alb * 0.7, 0, 1))
    rgb = rgb * (0.92 + 0.16 * _sz_fbm(shape, 40, 3, seed=76)[..., None])
    # 극관 — 북 78°, 남쪽 잔류 극관은 극에서 약간 비껴 있다
    capn = _sz_fbm(shape, 10, 4, seed=77)
    north = _sz_smoothstep(76.0 + capn * 3.0, 79.5 + capn * 3.0, lat)
    north = north * (0.86 + 0.14 * _sz_fbm(shape, 24, 3, seed=78))
    frost = _sz_smoothstep(70, 77, lat) * 0.25 * capn
    sd = _sz_gc(lat, lon, -87, -45)
    south = 1.0 - _sz_smoothstep(4.5 + capn * 2, 7.5 + capn * 2, sd)
    cap = np.clip(north + frost + south, 0, 1)
    rgb = _sz_mix(rgb, _sz_col(shape, (0.97, 0.96, 0.95)), cap)
    _sz_save_rgb(np.clip(rgb, 0, 1), "mars", sat=1.08, fade=False)
    _sz_save_raw(hgt, "mars_h", bits16=True)


# ─────────────────────────── 목성 v2 ───────────────────────────
def tex_jupiter_v2(shape=(2048, 4096)):
    """띠(동서 전단 난류)·대적점(정면용 경도 0)·흰 타원·NEB 꽃줄(festoon)."""
    h, w = shape
    lat, lon = _sz_ll(shape)
    # 동서로 크게 늘어진 난류로 위도를 흔든다 → 띠 경계가 물결치며 말린다
    t1 = _sz_fbm(shape, 6, 6, seed=81, stretch=5.0)
    t2 = _sz_fbm(shape, 22, 5, seed=82, stretch=3.0)
    t3 = _sz_fbm(shape, 70, 4, seed=83, stretch=1.5)
    shear = np.cos(np.radians(lat)) ** 0.5
    latd = lat + ((t1 - 0.5) * 3.2 + (t2 - 0.5) * 1.6 + (t3 - 0.5) * 0.5) * shear
    # 띠 경계의 말림(에디) — 위도만 흔들면 매끈한 물결뿐이라 플라스틱 공처럼 보였다. 경도 방향 변위를 더한다
    latd = latd + (_sz_fbm(shape, 30, 4, seed=88, stretch=2.0) - 0.5) * 2.2 * shear
    # 소용돌이 좌표 왜곡 — 대적점(-22, 0)·타원 BA(-33, 60)·진주 목걸이(-40)·북쪽 갈색 바지선
    yy = (90 - latd) / 180 * h
    xx = np.broadcast_to(((lon + 180) / 360 * w), shape).astype(np.float32).copy()
    yy = yy.astype(np.float32)
    xx = xx + (_sz_fbm(shape, 24, 5, seed=87, stretch=2.5) - 0.5) * (w / 360.0) * 7.0
    xx = xx + (_sz_fbm(shape, 70, 4, seed=89, stretch=1.3) - 0.5) * (w / 360.0) * 2.6   # 잔 소용돌이
    yy = yy + (_sz_fbm(shape, 70, 4, seed=90, stretch=1.3) - 0.5) * (h / 180.0) * 0.9
    vort = [(-22.0, 0.0, 12.0, 6.5, -1.9), (-33.5, 62.0, 3.2, 2.4, -2.2), (-33.5, -110.0, 2.6, 2.0, -2.0)]
    rs = np.random.default_rng(84)
    for k in range(8):
        vort.append((-40.5, -170 + k * 45 + rs.uniform(-6, 6), 1.3, 1.1, -2.4))
    for k in range(5):
        vort.append((15.5, rs.uniform(-180, 180), 2.2, 1.0, 1.8))        # 북 바지선(갈색 저기압)
    small_ovals = []
    for k in range(34):                                                 # 중위도 작은 타원 폭풍들
        la = rs.choice([-1, 1]) * rs.uniform(18, 58); lo = rs.uniform(-180, 180)
        if abs(la + 22) < 8 and abs(lo) < 30:
            continue
        rr_ = rs.uniform(0.5, 1.4)
        vort.append((la, lo, rr_ * 1.5, rr_, (-1 if la < 0 else 1) * 2.0))
        small_ovals.append((la, lo, rr_, rs.random() < 0.7))
    for la0, lo0, rlo, rla, spin in vort:
        cy0 = (90 - la0) / 180 * h; cx0 = (lo0 + 180) / 360 * w
        sx = w / 360 * math.cos(math.radians(la0)); sy = h / 180
        dx = ((xx - cx0 + w / 2) % w - w / 2) / sx; dy = (yy - cy0) / sy
        e = np.sqrt((dx / rlo) ** 2 + (dy / rla) ** 2)
        a = spin * np.exp(-(e ** 2) * 1.2)
        c, s = np.cos(a), np.sin(a)
        ndx = (dx / rlo * c - dy / rla * s) * rlo; ndy = (dx / rlo * s + dy / rla * c) * rla
        xx = cx0 + ndx * sx; yy = cy0 + ndy * sy
    latw = 90 - yy / h * 180
    bands = [
        (90, (0.46, 0.44, 0.42)), (72, (0.56, 0.50, 0.44)), (62, (0.70, 0.62, 0.52)), (55, (0.62, 0.50, 0.40)),
        (47, (0.84, 0.77, 0.66)), (40, (0.66, 0.52, 0.40)), (35, (0.88, 0.82, 0.70)), (30, (0.72, 0.55, 0.40)),
        (24, (0.93, 0.88, 0.78)), (19, (0.90, 0.84, 0.74)), (17, (0.60, 0.40, 0.27)), (12, (0.55, 0.36, 0.24)),
        (8, (0.72, 0.56, 0.44)), (6, (0.95, 0.90, 0.80)), (2, (0.90, 0.82, 0.70)), (0, (0.93, 0.86, 0.72)),
        (-2.5, (0.88, 0.80, 0.68)), (-5, (0.95, 0.89, 0.78)),
        (-8, (0.70, 0.52, 0.38)), (-12, (0.58, 0.40, 0.28)), (-17, (0.66, 0.48, 0.34)), (-20, (0.90, 0.84, 0.73)),
        (-26, (0.93, 0.88, 0.78)), (-29, (0.66, 0.50, 0.37)), (-34, (0.74, 0.60, 0.47)), (-39, (0.88, 0.82, 0.72)),
        (-45, (0.70, 0.58, 0.47)), (-52, (0.80, 0.72, 0.62)), (-62, (0.62, 0.55, 0.48)), (-74, (0.54, 0.50, 0.46)),
        (-90, (0.46, 0.44, 0.42))]
    stops = sorted([((90 - bl) / 180.0, c) for bl, c in bands], key=lambda s: s[0])
    r, g, b = ramp(np.clip((90 - latw) / 180.0, 0, 1), stops)
    rgb = np.dstack([r, g, b]).astype(np.float32)
    # 띠 안쪽 결 — 흐름을 따라 늘어진 밝고 어두운 줄
    streak = _sz_sample(_sz_fbm(shape, 90, 5, seed=85, stretch=5.0, gain=0.62), yy, xx)
    rgb = rgb * (0.78 + 0.44 * streak[..., None])
    for la, lo, rr_, white in small_ovals:
        ee = _sz_ellipse(lat, lon, la, lo, rr_, rr_ * 1.5)
        rgb = _sz_mix(rgb, _sz_col(shape, (0.97, 0.95, 0.90) if white else (0.55, 0.38, 0.27)),
                      (1.0 - _sz_smoothstep(0.4, 1.0, ee)) * 0.75)
    # 대적점 — 연어빛 주황, 가장자리 밝은 고리(Red Spot Hollow)
    e = _sz_ellipse(lat, lon, -22.0, 0.0, 6.0, 11.5)
    swirl = _sz_sample(_sz_fbm(shape, 60, 4, seed=86), yy, xx)
    core = 1.0 - _sz_smoothstep(0.55, 1.0, e)
    rgb = _sz_mix(rgb, np.dstack([0.80 + 0.10 * swirl, 0.38 + 0.12 * swirl, 0.24 + 0.08 * swirl]).astype(np.float32), core * 0.92)
    hollow = np.exp(-((e - 1.15) / 0.16) ** 2)
    rgb = _sz_mix(rgb, _sz_col(shape, (0.96, 0.92, 0.84)), hollow * 0.55)
    # 흰 타원 (BA 는 살짝 붉은빛)·진주 목걸이
    for la0, lo0, rla, rlo, c in [(-33.5, 62.0, 1.9, 3.0, (0.93, 0.80, 0.72)), (-33.5, -110.0, 1.5, 2.4, (0.97, 0.95, 0.92))] + \
            [(-40.5, -170 + k * 45, 0.8, 1.1, (0.98, 0.97, 0.95)) for k in range(8)]:
        ee = _sz_ellipse(lat, lon, la0, lo0, rla, rlo)
        rgb = _sz_mix(rgb, _sz_col(shape, c), (1.0 - _sz_smoothstep(0.5, 1.0, ee)) * 0.9)
    # NEB 남쪽 가장자리 꽃줄 — 적도대로 흘러내리는 청회색 깃털
    fest = np.zeros(shape, np.float32)
    for k in range(11):
        lo0 = -180 + k * (360 / 11) + rs.uniform(-12, 12)
        dx = _sz_wrap(lon - lo0) * np.cos(np.radians(lat))
        along = np.clip((7.5 - lat) / 7.0, 0, 1)
        cx = -along * 9.0
        fest = np.maximum(fest, np.exp(-((dx - cx) / (1.3 + along * 1.8)) ** 2) * np.exp(-((lat - 4.5) / 3.2) ** 2) * (lat < 8))
    fest = _sz_sample(fest, yy, xx) * (0.5 + 0.5 * streak)
    rgb = _sz_mix(rgb, _sz_col(shape, (0.46, 0.47, 0.52)), np.clip(fest * 0.55, 0, 1))
    _sz_save_rgb(np.clip(rgb, 0, 1), "jupiter", sat=1.0, fade=True)


# ─────────────────────────── 토성 v2 + 고리 v2 ───────────────────────────
def tex_saturn_v2(shape=(1024, 2048)):
    h, w = shape
    lat, lon = _sz_ll(shape)
    t1 = _sz_fbm(shape, 6, 5, seed=91, stretch=6.0)
    latd = lat + (t1 - 0.5) * 2.2 * np.cos(np.radians(lat))
    bands = [(90, (0.50, 0.58, 0.66)), (80, (0.55, 0.60, 0.64)), (74, (0.78, 0.72, 0.58)), (62, (0.86, 0.78, 0.60)),
             (50, (0.80, 0.70, 0.52)), (40, (0.92, 0.85, 0.66)), (30, (0.86, 0.76, 0.56)), (20, (0.95, 0.89, 0.72)),
             (10, (0.97, 0.92, 0.76)), (0, (0.98, 0.93, 0.78)), (-10, (0.95, 0.88, 0.70)), (-20, (0.88, 0.78, 0.58)),
             (-32, (0.93, 0.86, 0.68)), (-45, (0.84, 0.75, 0.57)), (-60, (0.80, 0.72, 0.58)), (-90, (0.70, 0.66, 0.60))]
    stops = sorted([((90 - bl) / 180.0, c) for bl, c in bands], key=lambda s: s[0])
    r, g, b = ramp(np.clip((90 - latd) / 180.0, 0, 1), stops)
    rgb = np.dstack([r, g, b]).astype(np.float32)
    rgb *= (0.95 + 0.10 * _sz_fbm(shape, 30, 4, seed=92, stretch=5.0)[..., None])
    # 북극 육각형 제트 (위도 ~77)
    th = np.radians(lon)
    rr = 90 - lat
    hexr = 13.0 / np.cos(((th + math.pi / 6) % (math.pi / 3)) - math.pi / 6)
    inside = 1.0 - _sz_smoothstep(-0.6, 0.6, rr - hexr)
    rim = np.exp(-((rr - hexr) / 0.8) ** 2) * (lat > 60)
    rgb = _sz_mix(rgb, _sz_col(shape, (0.62, 0.66, 0.66)), inside * 0.30 * (lat > 60))
    rgb = _sz_mix(rgb, _sz_col(shape, (0.90, 0.86, 0.74)), rim * 0.6)
    _sz_save_rgb(np.clip(rgb, 0, 1), "saturn", sat=1.12, fade=False)


SZ_RING_IN, SZ_RING_OUT = 1.11, 2.35   # 행성 반지름 단위 (D 고리 안쪽 ~ F 고리 바깥)


def tex_rings_v2(width=4096):
    """U = (r - 1.11)/(2.35 - 1.11). 실제 광학 깊이 구조: C 희미 → B 짙음 → 카시니 간극 → A(엥케 간극) → F."""
    r = SZ_RING_IN + (SZ_RING_OUT - SZ_RING_IN) * (np.arange(width) + 0.5) / width
    rs = np.random.default_rng(95)
    fine = np.zeros(width, np.float32)
    for k in range(60):
        fine += rs.uniform(0.2, 1.0) * np.sin(r * rs.uniform(60, 900) + rs.uniform(0, 6.28)) / 60
    a = np.zeros(width, np.float32)
    c = np.zeros((width, 3), np.float32)
    D = (r >= 1.11) & (r < 1.236)
    C = (r >= 1.239) & (r < 1.527)
    B = (r >= 1.527) & (r < 1.951)
    CD = (r >= 1.951) & (r < 2.025)
    A = (r >= 2.025) & (r < 2.270)
    a[D] = 0.04
    a[C] = 0.22 + 0.10 * np.sin(r[C] * 170) ** 2 + fine[C] * 0.8
    tb = (r[B] - 1.527) / (1.951 - 1.527)
    a[B] = 0.72 + 0.22 * _sz_smoothstep(0.0, 0.35, tb) + fine[B] * 1.4 - 0.08 * np.sin(tb * 40) ** 2
    a[CD] = 0.07 + 0.05 * np.exp(-((r[CD] - 1.99) / 0.01) ** 2)
    ta = (r[A] - 2.025) / (2.270 - 2.025)
    a[A] = 0.62 - 0.12 * ta + fine[A] * 1.0
    a[np.abs(r - 2.214) < 0.0045] = 0.03                 # 엥케 간극
    a[np.abs(r - 2.265) < 0.0012] = 0.10                 # 킬러 간극
    a += 0.5 * np.exp(-((r - 2.326) / 0.0025) ** 2)      # F 고리
    a = np.clip(a, 0, 1)
    c[:] = (0.84, 0.80, 0.72)
    c[C] = (0.62, 0.58, 0.54)
    c[B] = np.stack([0.94 - 0.04 * tb, 0.88 - 0.05 * tb, 0.74 - 0.04 * tb], 1)
    c[CD] = (0.55, 0.52, 0.50)
    c[A] = (0.82, 0.79, 0.73)
    c *= (0.92 + 0.16 * (fine[:, None] * 6 + 0.5).clip(0, 1))
    img = np.repeat(np.clip(c, 0, 1)[None], 8, axis=0)
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(OUT, "tex_sz_rings.png"))
    Image.fromarray((np.repeat(a[None], 8, axis=0) * 255 + 0.5).astype(np.uint8), 'L').save(os.path.join(OUT, "tex_sz_rings_a.png"))
    print("  tex_sz rings", width)


# ─────────────────────────── 천왕성·해왕성 ───────────────────────────
def tex_uranus(shape=(1024, 2048)):
    lat, lon = _sz_ll(shape)
    t = _sz_fbm(shape, 5, 5, seed=101, stretch=6.0)
    latd = lat + (t - 0.5) * 3.0
    base = np.dstack([0.56 + 0 * lat, 0.80 + 0 * lat, 0.86 + 0 * lat]).astype(np.float32)
    band = 0.5 + 0.5 * np.cos(np.radians(latd * 9.0))
    base *= (0.97 + 0.04 * band[..., None])
    # 남극 쪽 밝은 두건 (보이저 2호 시점) + 북반구 희미한 띠
    hood = _sz_smoothstep(-35, -65, latd)
    base = _sz_mix(base, _sz_col(shape, (0.72, 0.90, 0.92)), hood * 0.8)
    collar = np.exp(-((latd + 48) / 4.0) ** 2)
    base = _sz_mix(base, _sz_col(shape, (0.80, 0.94, 0.95)), collar * 0.4)
    base = _sz_mix(base, _sz_col(shape, (0.50, 0.74, 0.82)), np.exp(-((latd - 25) / 8.0) ** 2) * 0.35)
    _sz_save_rgb(np.clip(base, 0, 1), "uranus", sat=1.05, fade=False)


def tex_uranus_rings(width=2048):
    """천왕성 고리 (R 단위 1.60~2.02). 어둡고 가는 9+2개 — ε 고리가 가장 넓고 밝다."""
    r0, r1 = 1.60, 2.02
    r = r0 + (r1 - r0) * (np.arange(width) + 0.5) / width
    a = np.zeros(width, np.float32)
    for rr, wd, op in [(1.637, .0016, .45), (1.652, .0016, .40), (1.666, .0016, .40), (1.750, .0020, .55),
                       (1.786, .0020, .55), (1.834, .0020, .6), (1.863, .0022, .6), (1.900, .0030, .7),
                       (1.957, .0022, .45), (1.990, .0085, 1.0)]:
        a = np.maximum(a, op * np.exp(-((r - rr) / wd) ** 2))
    a += 0.06 * _sz_smoothstep(1.62, 1.66, r) * (1 - _sz_smoothstep(1.95, 1.99, r))
    a = np.clip(a, 0, 1)
    c = np.repeat(np.array([[0.70, 0.76, 0.80]], np.float32), width, 0)
    Image.fromarray((np.repeat(c[None], 8, 0) * 255).astype(np.uint8), 'RGB').save(os.path.join(OUT, "tex_sz_urings.png"))
    Image.fromarray((np.repeat(a[None], 8, 0) * 255).astype(np.uint8), 'L').save(os.path.join(OUT, "tex_sz_urings_a.png"))
    print("  tex_sz urings", width)


def tex_neptune(shape=(1024, 2048)):
    """코발트 + 대암반(GDS, 경도 0 정면)과 동반 흰 구름 + 스쿠터 + D2 + 흰 권운 줄."""
    lat, lon = _sz_ll(shape)
    t = _sz_fbm(shape, 5, 5, seed=111, stretch=5.0)
    t2 = _sz_fbm(shape, 20, 4, seed=112, stretch=4.0)
    latd = lat + (t - 0.5) * 4.0
    base = np.dstack([0.20 + 0 * lat, 0.38 + 0 * lat, 0.80 + 0 * lat]).astype(np.float32)
    base *= (0.94 + 0.10 * (0.5 + 0.5 * np.cos(np.radians(latd * 7)))[..., None]) * (0.95 + 0.1 * t2[..., None])
    base = _sz_mix(base, _sz_col(shape, (0.14, 0.27, 0.64)), np.exp(-((latd + 65) / 7.0) ** 2) * 0.7)
    base = _sz_mix(base, _sz_col(shape, (0.30, 0.50, 0.86)), _sz_smoothstep(-72, -85, latd) * 0.6)
    # 대암반
    e = _sz_ellipse(lat, lon, -20.0, 0.0, 6.0, 13.0)
    base = _sz_mix(base, _sz_col(shape, (0.07, 0.13, 0.42)), (1 - _sz_smoothstep(0.55, 1.0, e)) * 0.95)
    comp = _sz_ellipse(lat, lon, -26.5, 4.0, 1.6, 9.0, rot=-8)
    base = _sz_mix(base, _sz_col(shape, (0.93, 0.96, 1.0)), (1 - _sz_smoothstep(0.3, 1.0, comp)) * 0.95)
    # 스쿠터 (-42) 와 D2 (-55, 밝은 핵)
    sc = _sz_ellipse(lat, lon, -42.0, 38.0, 1.6, 4.5)
    base = _sz_mix(base, _sz_col(shape, (0.90, 0.95, 1.0)), (1 - _sz_smoothstep(0.3, 1.0, sc)) * 0.9)
    d2 = _sz_ellipse(lat, lon, -55.0, -28.0, 2.6, 5.5)
    base = _sz_mix(base, _sz_col(shape, (0.08, 0.15, 0.44)), (1 - _sz_smoothstep(0.5, 1.0, d2)) * 0.9)
    base = _sz_mix(base, _sz_col(shape, (0.85, 0.92, 1.0)), (1 - _sz_smoothstep(0.1, 0.35, d2)) * 0.8)
    # 흰 권운 줄 (메탄 얼음 구름) — 동서로 긴 밝은 줄
    cir = _sz_fbm(shape, 8, 6, seed=113, stretch=8.0)
    belt = np.exp(-((lat - 27) / 4.0) ** 2) + np.exp(-((lat + 30) / 3.0) ** 2) * 0.8 + np.exp(-((lat - 45) / 3.0) ** 2) * 0.4
    streak = _sz_smoothstep(0.60, 0.78, cir) * belt
    base = _sz_mix(base, _sz_col(shape, (0.92, 0.96, 1.0)), np.clip(streak, 0, 1) * 0.85)
    _sz_save_rgb(np.clip(base, 0, 1), "neptune", sat=1.10, fade=False)


# ─────────────────────────── 명왕성·카론 ───────────────────────────
def tex_pluto(shape=(1024, 2048)):
    """톰보 하트(스푸트니크 평원 = 서쪽 엽, 동경 175) + 크툴루 암부(적도, 동경 20~160).
    텍스처 경도 = 동경 - 180 → 하트 중심(동경 180)이 텍스처 경도 0 에 온다.
    UV 이음매(텍스처 경도 ±180)가 정면 하트를 가로지르지 않게 하려는 것."""
    lat, lon = _sz_ll(shape)
    E = lambda e: (e % 360) - 180
    n1 = _sz_fbm(shape, 6, 6, seed=121)
    n2 = _sz_fbm(shape, 24, 5, seed=122)
    base = np.dstack([0.72 + 0 * lat, 0.60 + 0 * lat, 0.49 + 0 * lat]).astype(np.float32)
    base *= (0.85 + 0.3 * n1[..., None])
    # 북극 로웰 영역 — 칙칙한 회청
    base = _sz_mix(base, _sz_col(lat.shape, (0.58, 0.54, 0.52)), _sz_smoothstep(55, 75, lat) * 0.7)
    base = _sz_mix(base, _sz_col(lat.shape, (0.66, 0.52, 0.40)), np.exp(-((lat - 40) / 10.0) ** 2) * 0.35)
    # 크툴루 — 적도 아래 길게 누운 짙은 적갈 (가장자리 노이즈)
    warp = (n2 - 0.5) * 0.5
    cth = _sz_ellipse(lat, lon, -5.0, E(90), 18.0, 60.0) + warp
    cth2 = _sz_ellipse(lat, lon, -10.0, E(40), 12.0, 25.0) + warp
    dm = 1 - _sz_smoothstep(0.75, 1.0, np.minimum(cth, cth2))
    others = _sz_regions(lat, lon, [(-8, E(250), 10, 18, 0.9), (-12, E(300), 9, 16, 0.85), (-5, E(340), 8, 14, 0.8)])
    dm = np.maximum(dm, _sz_smoothstep(0.45, 0.7, others + warp * 0.6))
    base = _sz_mix(base, _sz_col(lat.shape, (0.25, 0.12, 0.08)) * (0.8 + 0.4 * n2[..., None]), dm * 0.95)
    # 하트 — 서엽(스푸트니크, 매끈·밝음)·동엽(얼룩진 밝음)
    # 하트 곡선 (x²+y²-1)³ - x²y³ < 0 을 위도·경도 국소좌표에 얹는다(폭 ~70°, 높이 ~60°, 살짝 기울임).
    # 타원 두 개로 만든 1차 시안은 '흰 원 두 개'로만 보였다
    hx = _sz_wrap(lon - E(180)) * math.cos(math.radians(15)) / 30.0
    hy = (lat - 12.0) / 27.0
    rt = math.radians(-12)
    hx, hy = hx * math.cos(rt) - hy * math.sin(rt), hx * math.sin(rt) + hy * math.cos(rt)
    hx = hx + (n2 - 0.5) * 0.12; hy = hy + (n1 - 0.5) * 0.10 + 0.25
    hv = (hx ** 2 + hy ** 2 - 1) ** 3 - hx ** 2 * hy ** 3
    hm = 1 - _sz_smoothstep(-0.02, 0.06, hv)
    west = _sz_smoothstep(0.15, -0.05, hx)                     # 서엽 = 스푸트니크 평원(매끈·가장 밝음)
    spm = hm * west * (1 - _sz_smoothstep(0.55, 0.9, np.abs(hy - 0.1)) * 0.0)
    em = hm * (1 - west) * (0.65 + 0.35 * _sz_smoothstep(0.35, 0.6, n2))
    cells = 1.0 - np.abs(_sz_fbm(lat.shape, 60, 3, seed=123) - 0.5) * 2.0
    heart = _sz_col(lat.shape, (0.93, 0.88, 0.80)) * (0.96 + 0.04 * cells[..., None])
    base = _sz_mix(base, heart, np.clip(spm, 0, 1) * 0.97)
    base = _sz_mix(base, _sz_col(lat.shape, (0.86, 0.78, 0.68)), np.clip(em * (1 - spm), 0, 1) * 0.85)
    hgt = 0.5 + (n2 - 0.5) * 0.35 - spm * 0.15 + _sz_craters(lat.shape, 60, 0.8, 4.0, seed=124, amp=0.25) * (1 - spm)
    _sz_save_rgb(np.clip(base, 0, 1), "pluto", sat=1.12, fade=False)
    _sz_save_raw(np.clip(hgt, 0, 1), "pluto_h", bits16=True)


def tex_charon(shape=(1024, 2048)):
    lat, lon = _sz_ll(shape)
    n1 = _sz_fbm(shape, 5, 6, seed=131)
    g = 0.56 + (n1 - 0.5) * 0.16
    base = np.dstack([g, g * 0.98, g * 0.97]).astype(np.float32)
    # 모르도르 반점 — 북극의 적갈 모자
    mord = _sz_smoothstep(55 + n1 * 8, 75 + n1 * 6, lat)
    base = _sz_mix(base, _sz_col(lat.shape, (0.36, 0.22, 0.16)), mord * 0.9)
    # 적도 협곡대 (세레니티 협곡)
    can = np.exp(-((lat - 5 - (_sz_fbm(shape, 12, 4, seed=132) - 0.5) * 10) / 1.6) ** 2)
    hgt = _sz_craters(shape, 120, 0.6, 4.5, seed=133, amp=0.45) - can * 0.6 + (n1 - 0.5) * 0.3
    hgt = (hgt - hgt.min()) / (hgt.max() - hgt.min())
    base *= (0.9 + 0.2 * hgt[..., None])
    base = _sz_mix(base, _sz_col(lat.shape, (0.34, 0.33, 0.33)), can * 0.6)
    _sz_save_rgb(np.clip(base, 0, 1), "charon", sat=1.0, fade=False)
    _sz_save_raw(hgt, "charon_h", bits16=True)


# ─────────────────────────── 위성 (이오·타이탄·포보스) ───────────────────────────
def tex_io(shape=(512, 1024)):
    lat, lon = _sz_ll(shape)
    n1 = _sz_fbm(shape, 6, 6, seed=141)
    n2 = _sz_fbm(shape, 20, 4, seed=142)
    base = np.dstack([0.90 + 0 * lat, 0.82 + 0 * lat, 0.42 + 0 * lat]).astype(np.float32)
    base = _sz_mix(base, _sz_col(shape, (0.94, 0.92, 0.80)), _sz_smoothstep(0.55, 0.75, n1) * 0.8)   # SO2 서리
    base = _sz_mix(base, _sz_col(shape, (0.80, 0.55, 0.25)), _sz_smoothstep(0.55, 0.7, n2) * 0.5)
    base = _sz_mix(base, _sz_col(shape, (0.55, 0.38, 0.22)), _sz_smoothstep(45, 75, np.abs(lat)) * 0.75)  # 붉은 극지
    rs = np.random.default_rng(143)
    spots = np.zeros(shape, np.float32)
    for _ in range(46):
        la = math.degrees(math.asin(rs.uniform(-0.85, 0.85))); lo = rs.uniform(-180, 180); rad = rs.uniform(0.8, 3.2)
        d = _sz_gc(lat, lon, la, lo) / rad
        spots = np.maximum(spots, 1 - _sz_smoothstep(0.6, 1.0, d))
        if rs.random() < 0.15:     # 분출 퇴적물은 옅고 불규칙하게 — 선명한 고리는 과녁처럼 보인다
            spots = np.maximum(spots, np.exp(-((d - 2.4 + (_sz_fbm(shape, 30, 3, seed=144) - 0.5) * 2.0) / 0.9) ** 2) * 0.18)
    base = _sz_mix(base, _sz_col(shape, (0.14, 0.10, 0.06)), spots * 0.9)
    # 펠레 붉은 고리 (서경 255.7 → 동경 104.3) + 로키 (동경 51)
    d = _sz_gc(lat, lon, -18.7, 104.3)
    base = _sz_mix(base, _sz_col(shape, (0.78, 0.30, 0.14)), np.exp(-((d - 16) / 3.2) ** 2) * 0.85)
    base = _sz_mix(base, _sz_col(shape, (0.12, 0.08, 0.05)), (1 - _sz_smoothstep(2.0, 4.0, _sz_gc(lat, lon, 13, 51))) * 0.9)
    _sz_save_rgb(np.clip(base, 0, 1), "io", sat=1.1, fade=False)


def tex_titan(shape=(512, 1024)):
    lat, lon = _sz_ll(shape)
    n1 = _sz_fbm(shape, 4, 5, seed=151, stretch=2.0)
    base = np.dstack([0.84 + 0 * lat, 0.58 + 0 * lat, 0.26 + 0 * lat]).astype(np.float32)
    base *= (0.94 + 0.08 * n1[..., None])
    base = _sz_mix(base, _sz_col(shape, (0.70, 0.46, 0.20)), np.exp(-(lat / 16.0) ** 2) * _sz_smoothstep(0.45, 0.6, n1) * 0.6)
    base = _sz_mix(base, _sz_col(shape, (0.66, 0.50, 0.30)), _sz_smoothstep(55, 75, lat) * 0.5)      # 북극 두건
    _sz_save_rgb(np.clip(base, 0, 1), "titan", sat=1.05, fade=False)


def tex_phobos(shape=(512, 1024)):
    """포보스 — 스티크니 크레이터(경도 0 정면) + 평행 홈(groove)."""
    lat, lon = _sz_ll(shape)
    hgt = _sz_craters(shape, 520, 0.8, 9.0, seed=161, power=2.6, amp=1.0)
    d = _sz_gc(lat, lon, 0.0, 0.0) / 18.0
    hgt += (-np.exp(-(d ** 2) * 2.2) * 0.85 + np.exp(-((d - 1.0) ** 2) * 14.0) * 0.5) * 3.0
    groove = np.sin(np.radians(lat * 14 + lon * 2.5) * 6) ** 16 * _sz_smoothstep(10, 60, np.abs(_sz_wrap(lon)))
    hgt -= groove * 0.35
    hgt = (hgt - hgt.min()) / (hgt.max() - hgt.min())
    n = _sz_fbm(shape, 10, 5, seed=162)
    g = 0.42 + (n - 0.5) * 0.12 + (hgt - 0.5) * 0.12
    rgb = np.dstack([g * 1.0, g * 0.90, g * 0.82]).astype(np.float32)
    _sz_save_rgb(np.clip(rgb, 0, 1), "phobos", sat=1.0, fade=False)
    _sz_save_raw(hgt, "phobos_h", bits16=True)


SZ_ALL = [tex_sz_earth, tex_sz_moon, tex_mars_v2, tex_jupiter_v2, tex_saturn_v2, tex_rings_v2,
          tex_uranus, tex_uranus_rings, tex_neptune, tex_pluto, tex_charon, tex_io, tex_titan, tex_phobos]



if __name__ == "__main__":
    for fn in ALL:
        print("==", fn.__name__)
        fn()
    print("TEXTURES DONE ->", OUT)
