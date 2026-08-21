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


def save(arr, name):
    if not name.startswith("rings"):
        arr = polar_fade(arr)
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
    r, g, b = ramp(t, [(0.0, (1.00, 0.32, 0.02)), (0.45, (1.00, 0.60, 0.08)),
                       (0.72, (1.00, 0.84, 0.30)), (1.0, (1.00, 0.98, 0.80))])
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

if __name__ == "__main__":
    for fn in ALL:
        print("==", fn.__name__)
        fn()
    print("TEXTURES DONE ->", OUT)
