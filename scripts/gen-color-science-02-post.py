# -*- coding: utf-8 -*-
"""Generate "The Science of Color — Part 2: Turning Color into Numbers".

Reuses the proven scaffolding (CSS/FONT/helpers) from the Part 1 generator and
adds Part-2-specific figures, formulas, content, series nav. Figure label fonts
are deliberately larger than Part 1 (per author feedback). The CIE 1931 horseshoe
and x/y/z CMFs are computed from the Wyman-Sloan-Shirley (2013) analytic
approximation of the CIE 1931 2-degree color-matching functions.

Output: public/blog/color-science-02-color-in-numbers[/-en/-ja/-zh]/index.html
        + OG (4) + posts.js (4) + sitemap (4). Indexed flagship.
"""
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
BLOG = PUBLIC / "blog"
ASSETS_BLOG = PUBLIC / "assets" / "blog"

SLUG = "color-science-02-color-in-numbers"
PREV_SLUG = "color-science-01-how-we-see"
CATEGORY = "ai-tech"
DATE = "2026-06-14"
READ_MIN = 18
COVER_EMOJI = "📐"

try:
    BUILD = json.loads((PUBLIC / "build.json").read_text(encoding="utf-8")).get("v", DATE)
except Exception:
    BUILD = DATE

LANG_SUFFIX = {"ko": "", "en": "-en", "ja": "-ja", "zh": "-zh"}
OG_LOCALE = {"ko": "ko_KR", "en": "en_US", "ja": "ja_JP", "zh": "zh_CN"}

# --- reuse pure helpers + CSS + FONT from the Part 1 generator -------------
_p1 = importlib.util.spec_from_file_location("cs1", ROOT / "scripts" / "gen-color-science-01-post.py")
p1 = importlib.util.module_from_spec(_p1); _p1.loader.exec_module(p1)
CSS_BASE, FONT, _esc, wl_to_rgb, _wl_rgb255, gauss, _poly = (
    p1.CSS, p1.FONT, p1._esc, p1.wl_to_rgb, p1._wl_rgb255, p1.gauss, p1._poly)
PAL = p1.PAL

# content module (4 langs)
_c2 = importlib.util.spec_from_file_location("cs2c", ROOT / "scripts" / "color_science_02_content.py")
c2 = importlib.util.module_from_spec(_c2); _c2.loader.exec_module(c2)
content = c2.content

# accurate CIE data + filled-gamut PNG generator (real standard CMFs)
_cie = importlib.util.spec_from_file_location("ciedata", ROOT / "scripts" / "color_science_cie_data.py")
cie = importlib.util.module_from_spec(_cie); _cie.loader.exec_module(cie)
GAMUT_1931 = "cs-cie1931-gamut.png"
GAMUT_1976 = "cs-cie1976-gamut.png"
LAB_DISK = "cs-cielab-ab-disk.png"

# extra CSS: formula blocks + series nav
CSS = CSS_BASE + """
.formula{margin:18px auto;padding:16px 18px;background:#fbf9f4;border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:0 10px 10px 0;font-family:'Cambria','Georgia',serif;font-size:18px;line-height:2;color:#1c2930;overflow-x:auto;text-align:center}
.formula i{font-style:italic}
.snav{display:flex;gap:10px;margin:8px 0 26px;flex-wrap:wrap}
.snav a{display:inline-flex;align-items:center;gap:8px;padding:9px 15px;background:#fff;border:1px solid var(--line);border-radius:10px;font-size:13.5px;font-weight:600;color:var(--soft)}
.snav a b{color:var(--ink)}
/* square color-diagram figures: fit the screen, never horizontal-scroll on phone */
.fig-box.square{overflow-x:visible;display:flex;justify-content:center}
.fig-box.square svg{min-width:0;width:100%;max-width:560px;height:auto}
@media(min-width:900px){.formula{font-size:20px;max-width:760px}.fig-box.square svg{max-width:640px}}
/* interactive color-matching simulation */
.cs-sim{margin:26px 0 8px;background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 16px 14px;box-shadow:0 2px 18px rgba(34,48,58,.06)}
.cs-sim .cs-ttl{font-size:15.5px;font-weight:800;color:var(--ink);display:flex;align-items:center;gap:8px}
.cs-sim .cs-live{font-family:'JetBrains Mono',monospace;font-size:9.5px;font-weight:800;letter-spacing:.1em;color:#fff;background:#e4572e;padding:2px 7px;border-radius:4px}
.cs-sim .cs-desc{font-size:13px;color:var(--soft);margin:6px 0 12px;line-height:1.6}
.cs-sim svg{width:100%;height:auto;display:block;min-width:0}
.cs-ctrl{display:flex;align-items:center;gap:12px;margin-top:12px}
.cs-btn{flex-shrink:0;width:44px;height:44px;border-radius:50%;border:none;background:var(--ink);color:#fff;font-size:17px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.cs-slider{flex:1;accent-color:var(--accent);height:6px}
.cs-readout{flex-shrink:0;font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:700;color:var(--ink);min-width:76px;text-align:right}
"""

# ---------------------------------------------------------------------------
# CIE 1931 2-deg CMF — Wyman/Sloan/Shirley (2013) analytic approximation
# ---------------------------------------------------------------------------
def _pg(x, mu, s1, s2):
    s = s1 if x < mu else s2
    return math.exp(-0.5 * ((x - mu) / s) ** 2)


def cie_x(l):
    return 1.056 * _pg(l, 599.8, 37.9, 31.0) + 0.362 * _pg(l, 442.0, 16.0, 26.7) - 0.065 * _pg(l, 501.1, 20.4, 26.2)


def cie_y(l):
    return 0.821 * _pg(l, 568.8, 46.9, 40.5) + 0.286 * _pg(l, 530.9, 16.3, 31.1)


def cie_z(l):
    return 1.217 * _pg(l, 437.0, 11.8, 36.0) + 0.681 * _pg(l, 459.0, 26.0, 13.8)


def chromaticity(l):
    X, Y, Z = cie_x(l), cie_y(l), cie_z(l)
    s = X + Y + Z
    return (X / s, Y / s) if s > 0 else (0, 0)


# ---------------------------------------------------------------------------
# Figures — bigger label fonts than Part 1. viewBox ~ 900 wide.
# ---------------------------------------------------------------------------
FS = 16    # base label
FST = 19   # title / emphasis
FSA = 15   # axis numbers


def _ax(s, ox, oy, w, h, xl, yl):
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{ox+w}" y2="{oy}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy-h}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    # x-label sits a row BELOW the tick numbers (oy+24) to avoid colliding with the last tick
    s.append(f'<text x="{ox+w}" y="{oy+46}" text-anchor="end" font-size="{FS}" fill="{PAL["soft"]}">{xl}</text>')
    s.append(f'<text x="{ox-6}" y="{oy-h-10}" font-size="{FS}" fill="{PAL["soft"]}">{yl}</text>')


def fig_match(t):
    """A clean optical-apparatus schematic of the bipartite color-matching set-up."""
    W, H = 900, 440
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    s.append(f'<defs><marker id="mbeam" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#888"/></marker></defs>')
    fx, fy, fr = 450, 165, 96
    # beams first (behind the field)
    s.append(f'<line x1="180" y1="120" x2="{fx-fr*0.55:.0f}" y2="{fy-10}" stroke="#9bd" stroke-width="6" opacity="0.5" marker-end="url(#mbeam)"/>')
    for i, col in enumerate(["#f2c4b8", "#bfe6c8", "#bcd2f5"]):
        s.append(f'<line x1="740" y1="{100+i*70}" x2="{fx+fr*0.55:.0f}" y2="{fy+(i-1)*8}" stroke="{col}" stroke-width="6" opacity="0.6" marker-end="url(#mbeam)"/>')
    # bipartite circular field (2-degree)
    s.append(f'<clipPath id="cmf"><circle cx="{fx}" cy="{fy}" r="{fr}"/></clipPath>')
    s.append(f'<g clip-path="url(#cmf)"><rect x="{fx-fr}" y="{fy-fr}" width="{fr}" height="{2*fr}" fill="#0fb6c4"/>'
             f'<rect x="{fx}" y="{fy-fr}" width="{fr}" height="{2*fr}" fill="#16b8c0"/></g>')
    s.append(f'<line x1="{fx}" y1="{fy-fr}" x2="{fx}" y2="{fy+fr}" stroke="#fff" stroke-width="1.5" opacity="0.55"/>')
    s.append(f'<circle cx="{fx}" cy="{fy}" r="{fr}" fill="none" stroke="{PAL["ink"]}" stroke-width="2.5"/>')
    s.append(f'<text x="{fx-fr*0.5:.0f}" y="{fy-fr-12}" text-anchor="middle" font-size="{FSA}" font-weight="700" fill="{PAL["ink"]}">{t["test_half"]}</text>')
    s.append(f'<text x="{fx+fr*0.5:.0f}" y="{fy-fr-12}" text-anchor="middle" font-size="{FSA}" font-weight="700" fill="{PAL["ink"]}">{t["mix_half"]}</text>')
    # test light source (left)
    s.append(f'<circle cx="150" cy="120" r="22" fill="#ffe9a8" stroke="{PAL["gold"]}" stroke-width="2"/>')
    for a in range(0, 360, 45):
        import math as _m
        dx, dy = _m.cos(_m.radians(a)), _m.sin(_m.radians(a))
        s.append(f'<line x1="{150+dx*26:.0f}" y1="{120+dy*26:.0f}" x2="{150+dx*34:.0f}" y2="{120+dy*34:.0f}" stroke="{PAL["gold"]}" stroke-width="2"/>')
    s.append(f'<text x="150" y="70" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["ink"]}">{t["test"]}</text>')
    s.append(f'<text x="150" y="180" text-anchor="middle" font-size="{FSA}" fill="{PAL["soft"]}">{t["single_wl"]}</text>')
    # three primary sources + intensity sliders (right) — lamp + wl below, slider to the right (no overlap)
    s.append(f'<text x="812" y="54" text-anchor="middle" font-size="{FS}" font-weight="800" fill="{PAL["ink"]}">{t["knobs"]}</text>')
    prim = [("R", "700", PAL["L"]), ("G", "546", PAL["M"]), ("B", "436", PAL["S"])]
    tx0, tw = 770, 110
    for i, (lt, nm, col) in enumerate(prim):
        y = 100 + i * 66
        s.append(f'<circle cx="724" cy="{y}" r="15" fill="{col}"/>')
        s.append(f'<text x="724" y="{y+5}" text-anchor="middle" font-size="13" font-weight="800" fill="#fff">{lt}</text>')
        s.append(f'<text x="724" y="{y+30}" text-anchor="middle" font-size="10.5" fill="{PAL["soft"]}">{nm}nm</text>')
        s.append(f'<rect x="{tx0}" y="{y-6}" width="{tw}" height="12" rx="6" fill="#eef1f3" stroke="{PAL["line"]}"/>')
        fillw = 36 + i * 30
        s.append(f'<rect x="{tx0}" y="{y-6}" width="{fillw}" height="12" rx="6" fill="{col}"/>')
        s.append(f'<circle cx="{tx0+fillw}" cy="{y}" r="8" fill="#fff" stroke="{col}" stroke-width="2.5"/>')
    # observer eye (bottom)
    ex, ey = fx, 360
    s.append(f'<line x1="{fx-fr*0.6:.0f}" y1="{fy+fr-6}" x2="{ex-26}" y2="{ey-18}" stroke="{PAL["mute"]}" stroke-width="1" stroke-dasharray="4 3"/>')
    s.append(f'<line x1="{fx+fr*0.6:.0f}" y1="{fy+fr-6}" x2="{ex+26}" y2="{ey-18}" stroke="{PAL["mute"]}" stroke-width="1" stroke-dasharray="4 3"/>')
    s.append(f'<path d="M{ex-40},{ey} Q{ex},{ey-30} {ex+40},{ey} Q{ex},{ey+30} {ex-40},{ey} Z" fill="#fff" stroke="{PAL["ink"]}" stroke-width="2"/>')
    s.append(f'<circle cx="{ex}" cy="{ey}" r="15" fill="#5a7"/><circle cx="{ex}" cy="{ey}" r="7" fill="#111"/>')
    s.append(f'<text x="{ex}" y="{ey+44}" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["ink"]}">{t["observer"]}</text>')
    s.append(f'<text x="{ex+70}" y="{ey-6}" font-size="{FSA}" fill="{PAL["soft"]}">{t["field2"]}</text>')
    s.append(f'<text x="{W/2:.0f}" y="{H-10}" text-anchor="middle" font-size="{FS}" fill="{PAL["soft"]}">{t["adjust"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_cmf_rgb(t):
    """Real CIE 1931 RGB color-matching functions (incl. the true negative lobe)."""
    W, H = 900, 440
    ox, oy, w, h = 70, 360, 770, 300
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    wl, r, g, b = cie.rgb_cmf()
    lo, hi = 380, 700
    msk = (wl >= lo) & (wl <= hi)
    wl, r, g, b = wl[msk], r[msk], g[msk], b[msk]
    vmax = max(float(r.max()), float(g.max()), float(b.max()))
    vmin = min(float(r.min()), float(g.min()), float(b.min()))
    span = vmax - vmin
    xs = lambda nm: ox + w * (nm - lo) / (hi - lo)
    Y = lambda v: oy - h * (v - vmin) / span
    zero = Y(0)
    # negative region shading (r-bar < 0)
    neg_lo, neg_hi = 438, 546
    s.append(f'<rect x="{xs(neg_lo):.0f}" y="{Y(vmax):.0f}" width="{xs(neg_hi)-xs(neg_lo):.0f}" height="{oy-Y(vmax):.0f}" fill="{PAL["L"]}" opacity="0.06"/>')
    # axes (x at zero line)
    s.append(f'<line x1="{ox}" y1="{zero:.0f}" x2="{ox+w}" y2="{zero:.0f}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{Y(vmax):.0f}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    s.append(f'<text x="{ox+w}" y="{zero-8:.0f}" text-anchor="end" font-size="{FS}" fill="{PAL["soft"]}">{t["x"]}</text>')
    s.append(f'<text x="{ox+6}" y="{Y(vmax)+2:.0f}" font-size="{FS}" fill="{PAL["soft"]}">{t["y"]}</text>')
    s.append(f'<text x="{ox-10}" y="{zero+5:.0f}" text-anchor="end" font-size="{FSA}" fill="{PAL["mute"]}">0</text>')
    for nm in range(400, 701, 50):
        s.append(f'<text x="{xs(nm):.0f}" y="{oy+26}" text-anchor="middle" font-size="{FSA}" fill="{PAL["mute"]}">{nm}</text>')
        s.append(f'<line x1="{xs(nm):.0f}" y1="{oy}" x2="{xs(nm):.0f}" y2="{oy+5}" stroke="{PAL["axis"]}"/>')
    step = 2
    for arr, col, lab in [(b, PAL["S"], "b̄(λ)"), (g, PAL["M"], "ḡ(λ)"), (r, PAL["L"], "r̄(λ)")]:
        pts = [(xs(int(wl[i])), Y(float(arr[i]))) for i in range(0, len(wl), step)]
        s.append(f'<polyline points="{_poly(pts)}" fill="none" stroke="{col}" stroke-width="3.2"/>')
    # peak labels
    import numpy as _np
    for arr, col, lab in [(b, PAL["S"], "b̄(λ)"), (g, PAL["M"], "ḡ(λ)"), (r, PAL["L"], "r̄(λ)")]:
        pk = int(_np.argmax(arr)); lx = int(wl[pk])
        s.append(f'<text x="{xs(lx):.0f}" y="{Y(float(arr[pk]))-12:.0f}" text-anchor="middle" font-size="{FST}" font-weight="800" fill="{col}">{lab}</text>')
    s.append(f'<text x="{xs(495):.0f}" y="{oy-8:.0f}" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["L"]}">{t["neg"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_negative(t):
    """Two clean panels: (1) saturation scale shows a mix can't reach pure cyan;
    (2) adding red to the TEST side makes r̄ negative."""
    W, H = 900, 380
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']

    def panel(px, num, title, col):
        s.append(f'<rect x="{px}" y="34" width="400" height="312" rx="14" fill="#fff" stroke="{PAL["line"]}"/>')
        s.append(f'<circle cx="{px+28}" cy="66" r="15" fill="{col}"/><text x="{px+28}" y="71" text-anchor="middle" font-size="{FS}" font-weight="800" fill="#fff">{num}</text>')
        s.append(f'<text x="{px+52}" y="72" font-size="{FS}" font-weight="800" fill="{PAL["ink"]}">{title}</text>')
    panel(30, "1", t["p_left"], PAL["L"])
    panel(470, "2", t["p_right"], PAL["M"])

    # Panel 1 — saturation axis: pure 500nm sits beyond any R+G+B mix
    ax0, ax1, ay = 70, 400, 200
    s.append(f'<defs><linearGradient id="satg" x1="0" x2="1"><stop offset="0" stop-color="#b9c7c9"/><stop offset="1" stop-color="#00d6e6"/></linearGradient></defs>')
    s.append(f'<rect x="{ax0}" y="{ay-9}" width="{ax1-ax0}" height="18" rx="9" fill="url(#satg)"/>')
    s.append(f'<text x="{ax0}" y="{ay+34}" font-size="{FSA}" fill="{PAL["mute"]}">{t["dull2"]}</text>')
    s.append(f'<text x="{ax1}" y="{ay+34}" text-anchor="end" font-size="{FSA}" fill="{PAL["mute"]}">{t["sat"]}</text>')
    mixx = ax0 + (ax1 - ax0) * 0.58
    s.append(f'<circle cx="{mixx:.0f}" cy="{ay}" r="9" fill="#5fc0c8" stroke="#fff" stroke-width="2"/>')
    s.append(f'<text x="{mixx:.0f}" y="{ay-20}" text-anchor="middle" font-size="{FSA}" font-weight="700" fill="{PAL["soft"]}">{t["mixmax"]}</text>')
    s.append(f'<circle cx="{ax1-6:.0f}" cy="{ay}" r="11" fill="#00d6e6" stroke="#111" stroke-width="2"/>')
    s.append(f'<text x="{ax1-6:.0f}" y="{ay-20}" text-anchor="middle" font-size="{FSA}" font-weight="800" fill="{PAL["ink"]}">{t["pure"]}</text>')
    s.append(f'<path d="M{mixx+14:.0f},{ay} L{ax1-22:.0f},{ay}" stroke="{PAL["L"]}" stroke-width="2" stroke-dasharray="4 3"/>')
    s.append(f'<text x="235" y="300" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["L"]}">{t["cant"]}</text>')

    # Panel 2 — test ⊕ red = green+blue  ->  test = G+B − R
    ey = 165
    s.append(f'<circle cx="560" cy="{ey}" r="32" fill="#0ec6cf" stroke="#111" stroke-width="1.5"/>')
    s.append(f'<text x="560" y="{ey+52}" text-anchor="middle" font-size="{FSA}" fill="{PAL["soft"]}">{t["testc"]}</text>')
    s.append(f'<text x="612" y="{ey+7}" text-anchor="middle" font-size="26" font-weight="700" fill="{PAL["L"]}">+</text>')
    s.append(f'<circle cx="652" cy="{ey}" r="18" fill="{PAL["L"]}" stroke="#111" stroke-width="1.5"/><text x="652" y="{ey+5}" text-anchor="middle" font-size="{FS}" font-weight="800" fill="#fff">R</text>')
    s.append(f'<text x="700" y="{ey+7}" text-anchor="middle" font-size="26" font-weight="700" fill="{PAL["ink"]}">=</text>')
    s.append(f'<circle cx="752" cy="{ey}" r="32" fill="#5fae9a" stroke="#111" stroke-width="1.5"/><text x="752" y="{ey+5}" text-anchor="middle" font-size="{FS}" font-weight="800" fill="#fff">G+B</text>')
    s.append(f'<rect x="500" y="248" width="340" height="44" rx="10" fill="{PAL["panel"]}"/>')
    s.append(f'<text x="670" y="276" text-anchor="middle" font-size="{FST}" font-weight="800" fill="{PAL["ink"]}">{t["eq"]}</text>')
    s.append(f'<text x="670" y="320" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["L"]}">{t["conc"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_xyz_cmf(t):
    """Real CIE 1931 XYZ color-matching functions (all positive)."""
    W, H = 900, 400
    ox, oy, w, h = 70, 330, 770, 250
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    wl, x, y, z = cie.cmf_1nm()
    lo, hi = 380, 700
    msk = (wl >= lo) & (wl <= hi)
    wl, x, y, z = wl[msk], x[msk], y[msk], z[msk]
    peak = max(float(x.max()), float(y.max()), float(z.max()))
    xs = lambda nm: ox + w * (nm - lo) / (hi - lo)
    _ax(s, ox, oy, w, h, t["x"], t["y"])
    for nm in range(400, 701, 50):
        s.append(f'<text x="{xs(nm):.0f}" y="{oy+24}" text-anchor="middle" font-size="{FSA}" fill="{PAL["mute"]}">{nm}</text>')
    import numpy as _np
    for arr, col, lab in [(z, PAL["S"], "z̄(λ)"), (y, PAL["M"], "ȳ(λ)"), (x, PAL["L"], "x̄(λ)")]:
        pts = [(xs(int(wl[i])), oy - h * float(arr[i]) / peak) for i in range(0, len(wl), 2)]
        s.append(f'<polyline points="{_poly(pts)}" fill="none" stroke="{col}" stroke-width="3.2"/>')
        pk = int(_np.argmax(arr)); lx = int(wl[pk])
        s.append(f'<text x="{xs(lx):.0f}" y="{oy - h*float(arr[pk])/peak - 12:.0f}" text-anchor="middle" font-size="{FST}" font-weight="800" fill="{col}">{lab}</text>')
    s.append('</svg>')
    return "\n".join(s)


def _chroma_axes(s, PX, PY, XR, YR, ox, oy):
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{PX(XR):.0f}" y2="{oy}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{PY(YR):.0f}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    # ticks at 0.2/0.4/0.6 only — the max-edge tick would collide with the x/y axis label
    for v in (0.2, 0.4, 0.6):
        s.append(f'<text x="{PX(v):.0f}" y="{oy+26}" text-anchor="middle" font-size="{FSA}" fill="{PAL["mute"]}">{v}</text>')
        s.append(f'<text x="{ox-12}" y="{PY(v)+5:.0f}" text-anchor="end" font-size="{FSA}" fill="{PAL["mute"]}">{v}</text>')


def fig_chromaticity(t):
    """Properly FILLED CIE 1931 horseshoe: real CMF + xy->sRGB gamut PNG + vector overlay."""
    W, H = 740, 720
    ox, oy, pw, ph = 80, 650, 600, 600
    (_x0, XR), (_y0, YR) = cie.GAMUT_RANGE["1931"]
    PX = lambda x: ox + pw * (x / XR)
    PY = lambda y: oy - ph * (y / YR)
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    s.append(f'<image href="/assets/blog/{GAMUT_1931}?v={BUILD}" x="{PX(0):.1f}" y="{PY(YR):.1f}" '
             f'width="{PX(XR)-PX(0):.1f}" height="{PY(0)-PY(YR):.1f}" preserveAspectRatio="none"/>')
    # spectral locus outline (crisp dark edge)
    pts = [(PX(x), PY(y)) for x, y in cie.locus_polyline("1931")]
    poly = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + " Z"
    s.append(f'<path d="{poly}" fill="none" stroke="#1c1c1c" stroke-width="1.4" stroke-linejoin="round"/>')
    _chroma_axes(s, PX, PY, XR, YR, ox, oy)
    s.append(f'<text x="{PX(XR):.0f}" y="{oy+26}" text-anchor="end" font-size="{FS}" fill="{PAL["soft"]}">x</text>')
    s.append(f'<text x="{ox-12}" y="{PY(YR)+14:.0f}" font-size="{FS}" fill="{PAL["soft"]}">y</text>')
    # wavelength labels around the locus (white halo for legibility)
    cen = (0.32, 0.34)
    for nm, (x, y) in cie.locus_label_points("1931").items():
        dx, dy = x - cen[0], y - cen[1]
        d = max((dx * dx + dy * dy) ** 0.5, 1e-3)
        lxp, lyp = PX(x) + dx / d * 16, PY(y) - dy / d * 16
        s.append(f'<circle cx="{PX(x):.0f}" cy="{PY(y):.0f}" r="2.5" fill="#111"/>')
        s.append(f'<text x="{lxp:.0f}" y="{lyp:.0f}" text-anchor="middle" font-size="13" font-weight="700" '
                 f'fill="#111" stroke="#fff" stroke-width="3" paint-order="stroke">{nm}</text>')
    # sRGB triangle + white point
    R, G, B = (0.64, 0.33), (0.30, 0.60), (0.15, 0.06)
    tri = f'{PX(R[0]):.0f},{PY(R[1]):.0f} {PX(G[0]):.0f},{PY(G[1]):.0f} {PX(B[0]):.0f},{PY(B[1]):.0f}'
    s.append(f'<polygon points="{tri}" fill="none" stroke="#111" stroke-width="2" stroke-dasharray="7 4"/>')
    # sRGB label inside the triangle (end-anchored, pointing left) — clear of the wavelength labels at the rim
    s.append(f'<text x="{PX(R[0])-12:.0f}" y="{PY(R[1])+26:.0f}" text-anchor="end" font-size="14" font-weight="700" fill="#111" stroke="#fff" stroke-width="3.5" paint-order="stroke">{t["srgb"]}</text>')
    wx, wy = 0.3127, 0.329
    s.append(f'<circle cx="{PX(wx):.0f}" cy="{PY(wy):.0f}" r="6" fill="#fff" stroke="#111" stroke-width="2"/>')
    s.append(f'<text x="{PX(wx)+11:.0f}" y="{PY(wy)+4:.0f}" font-size="14" font-weight="700" fill="#111" stroke="#fff" stroke-width="3" paint-order="stroke">{t["white"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_macadam(t):
    """Real locus outline (dimmed gamut) + exaggerated MacAdam ellipses."""
    W, H = 740, 660
    ox, oy, pw, ph = 80, 590, 560, 560
    (_x0, XR), (_y0, YR) = cie.GAMUT_RANGE["1931"]
    PX = lambda x: ox + pw * (x / XR)
    PY = lambda y: oy - ph * (y / YR)
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    s.append(f'<image href="/assets/blog/{GAMUT_1931}?v={BUILD}" x="{PX(0):.1f}" y="{PY(YR):.1f}" '
             f'width="{PX(XR)-PX(0):.1f}" height="{PY(0)-PY(YR):.1f}" preserveAspectRatio="none" opacity="0.42"/>')
    pts = [(PX(x), PY(y)) for x, y in cie.locus_polyline("1931")]
    poly = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + " Z"
    s.append(f'<path d="{poly}" fill="none" stroke="#444" stroke-width="1.4"/>')
    _chroma_axes(s, PX, PY, XR, YR, ox, oy)
    # exaggerated ellipses (×10): green large, blue small
    ell = [(0.30, 0.55, 58, 26, 25), (0.20, 0.42, 30, 16, -10), (0.17, 0.10, 16, 11, 60),
           (0.45, 0.47, 44, 22, -20), (0.54, 0.40, 40, 18, -35), (0.34, 0.36, 30, 18, 10),
           (0.26, 0.62, 48, 24, 35), (0.42, 0.28, 24, 14, 0)]
    for x, y, rx, ry, ang in ell:
        s.append(f'<ellipse cx="{PX(x):.0f}" cy="{PY(y):.0f}" rx="{rx}" ry="{ry}" transform="rotate({ang} {PX(x):.0f} {PY(y):.0f})" fill="none" stroke="#111" stroke-width="2.2"/>')
    s.append(f'<text x="{PX(0.30):.0f}" y="{PY(0.55)+4:.0f}" text-anchor="middle" font-size="{FSA}" font-weight="700" fill="#0a5a22" stroke="#fff" stroke-width="3" paint-order="stroke">{t["green"]}</text>')
    s.append(f'<text x="{PX(0.17):.0f}" y="{PY(0.10)-8:.0f}" text-anchor="middle" font-size="{FSA}" font-weight="700" fill="#13408a" stroke="#fff" stroke-width="3" paint-order="stroke">{t["blue"]}</text>')
    s.append(f'<text x="{ox+6}" y="36" font-size="{FS}" fill="{PAL["soft"]}">{t["note"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_chromaticity_1976(t):
    """Filled CIE 1976 UCS (u'v') diagram — real CMF gamut PNG + vector overlay."""
    W, H = 720, 700
    ox, oy, pw, ph = 86, 630, 580, 580
    (_u0, UR), (_v0, VR) = cie.GAMUT_RANGE["1976"]
    PX = lambda u: ox + pw * (u / UR)
    PY = lambda v: oy - ph * (v / VR)
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    s.append(f'<image href="/assets/blog/{GAMUT_1976}?v={BUILD}" x="{PX(0):.1f}" y="{PY(VR):.1f}" '
             f'width="{PX(UR)-PX(0):.1f}" height="{PY(0)-PY(VR):.1f}" preserveAspectRatio="none"/>')
    pts = [(PX(u), PY(v)) for u, v in cie.locus_polyline("1976")]
    poly = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + " Z"
    s.append(f'<path d="{poly}" fill="none" stroke="#1c1c1c" stroke-width="1.4" stroke-linejoin="round"/>')
    # axes
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{PX(UR):.0f}" y2="{oy}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{PY(VR):.0f}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    for v in (0.2, 0.4, 0.6):
        s.append(f'<text x="{PX(v):.0f}" y="{oy+26}" text-anchor="middle" font-size="{FSA}" fill="{PAL["mute"]}">{v}</text>')
        s.append(f'<text x="{ox-12}" y="{PY(v)+5:.0f}" text-anchor="end" font-size="{FSA}" fill="{PAL["mute"]}">{v}</text>')
    s.append(f'<text x="{PX(UR):.0f}" y="{oy+26}" text-anchor="end" font-size="{FS}" fill="{PAL["soft"]}">u′</text>')
    s.append(f'<text x="{ox-12}" y="{PY(VR)+14:.0f}" font-size="{FS}" fill="{PAL["soft"]}">v′</text>')
    # wavelength labels
    cen = (0.2, 0.46)
    for nm, (u, v) in cie.locus_label_points("1976").items():
        du, dv = u - cen[0], v - cen[1]
        d = max((du * du + dv * dv) ** 0.5, 1e-3)
        lxp, lyp = PX(u) + du / d * 15, PY(v) - dv / d * 15
        s.append(f'<circle cx="{PX(u):.0f}" cy="{PY(v):.0f}" r="2.3" fill="#111"/>')
        s.append(f'<text x="{lxp:.0f}" y="{lyp:.0f}" text-anchor="middle" font-size="12.5" font-weight="700" fill="#111" stroke="#fff" stroke-width="3" paint-order="stroke">{nm}</text>')
    # sRGB triangle + white in uv
    pr = cie.srgb_primaries_uv()
    tri = f'{PX(pr["R"][0]):.0f},{PY(pr["R"][1]):.0f} {PX(pr["G"][0]):.0f},{PY(pr["G"][1]):.0f} {PX(pr["B"][0]):.0f},{PY(pr["B"][1]):.0f}'
    s.append(f'<polygon points="{tri}" fill="none" stroke="#111" stroke-width="2" stroke-dasharray="7 4"/>')
    s.append(f'<circle cx="{PX(pr["W"][0]):.0f}" cy="{PY(pr["W"][1]):.0f}" r="6" fill="#fff" stroke="#111" stroke-width="2"/>')
    s.append(f'<text x="{PX(pr["W"][0])+11:.0f}" y="{PY(pr["W"][1])+4:.0f}" font-size="14" font-weight="700" fill="#111" stroke="#fff" stroke-width="3" paint-order="stroke">{t["white"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_lab(t):
    """CIELAB: real a*b* hue-chroma wheel (Lab->sRGB PNG) + L* axis + opponent axes."""
    W, H = 720, 640
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    cx, cy, r = 270, 330, 210
    s.append(f'<image href="/assets/blog/{LAB_DISK}?v={BUILD}" x="{cx-r}" y="{cy-r}" width="{2*r}" height="{2*r}"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#bbb" stroke-width="1"/>')
    s.append(f'<defs><marker id="ah" markerWidth="11" markerHeight="11" refX="8" refY="4" orient="auto"><path d="M0,0 L9,4 L0,8 Z" fill="#222"/></marker></defs>')
    # opponent axes through the wheel
    ext = r + 36
    for x1, y1, x2, y2 in [(cx-ext, cy, cx+ext, cy), (cx, cy+ext, cx, cy-ext)]:
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#222" stroke-width="1.6" marker-end="url(#ah)"/>')
    def lbl(x, y, txt, col, anc="middle"):
        s.append(f'<text x="{x}" y="{y}" text-anchor="{anc}" font-size="{FST}" font-weight="800" fill="{col}" stroke="#fff" stroke-width="3.5" paint-order="stroke">{txt}</text>')
    lbl(cx+ext+6, cy+6, f'+a*', PAL["L"], "start"); lbl(cx+ext+6, cy+26, t["red"], PAL["L"], "start")
    lbl(cx-ext-6, cy+6, f'−a*', PAL["M"], "end"); lbl(cx-ext-6, cy+26, t["green"], PAL["M"], "end")
    lbl(cx, cy-ext-8, f'+b* {t["yellow"]}', PAL["gold"])
    lbl(cx, cy+ext+22, f'−b* {t["blue"]}', PAL["S"])
    # L* vertical lightness bar (right)
    bx, bt, bh = 600, cy - r, 2 * r
    s.append('<defs><linearGradient id="lstar" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#0a0a0a"/><stop offset="1" stop-color="#fff"/></linearGradient></defs>')
    s.append(f'<rect x="{bx-22}" y="{bt}" width="44" height="{bh}" rx="6" fill="url(#lstar)" stroke="{PAL["line"]}"/>')
    s.append(f'<text x="{bx}" y="{bt-14}" text-anchor="middle" font-size="{FST}" font-weight="800" fill="{PAL["ink"]}">L*</text>')
    s.append(f'<text x="{bx}" y="{bt-34}" text-anchor="middle" font-size="{FSA}" fill="{PAL["soft"]}">{t["light"]}</text>')
    s.append(f'<text x="{bx+30}" y="{bt+14}" font-size="{FSA}" fill="{PAL["soft"]}">100 ({t["white_w"]})</text>')
    s.append(f'<text x="{bx+30}" y="{bt+bh}" font-size="{FSA}" fill="{PAL["soft"]}">0 ({t["black_w"]})</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_de(t):
    """Two CIELAB samples; ΔE76 = straight distance, ΔE00 = perceptual correction."""
    W, H = 900, 380
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    # left: two close samples + euclidean distance in Lab
    s.append(f'<rect x="50" y="70" width="120" height="120" rx="12" fill="#2f6fb0"/>')
    s.append(f'<rect x="210" y="120" width="120" height="120" rx="12" fill="#3f8fd0"/>')
    s.append(f'<line x1="170" y1="118" x2="210" y2="158" stroke="{PAL["ink"]}" stroke-width="2.6" stroke-dasharray="6 4"/>')
    s.append(f'<text x="190" y="108" text-anchor="middle" font-size="22" font-weight="800" fill="{PAL["ink"]}">ΔE</text>')
    s.append(f'<text x="190" y="280" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["ink"]}">{t["e76"]}</text>')
    s.append(f'<text x="190" y="306" text-anchor="middle" font-size="{FSA}" fill="{PAL["soft"]}">{t["e76sub"]}</text>')
    s.append(f'<path d="M360,180 L430,180" stroke="{PAL["axis"]}" stroke-width="2.4" marker-end="url(#dah)"/>')
    s.append(f'<defs><marker id="dah" markerWidth="10" markerHeight="10" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="{PAL["axis"]}"/></marker></defs>')
    # right: CIEDE2000 correction terms
    s.append(f'<text x="660" y="56" text-anchor="middle" font-size="{FST}" font-weight="800" fill="{PAL["ink"]}">CIEDE2000</text>')
    terms = [(t["sl"], PAL["ink"]), (t["sc"], PAL["L"]), (t["sh"], PAL["M"]), (t["rt"], PAL["S"])]
    for i, (lab, col) in enumerate(terms):
        x = 470 + (i % 2) * 210
        y = 90 + (i // 2) * 96
        s.append(f'<rect x="{x}" y="{y}" width="190" height="74" rx="11" fill="#fff" stroke="{col}" stroke-width="2"/>')
        s.append(f'<rect x="{x}" y="{y}" width="6" height="74" rx="3" fill="{col}"/>')
        for j, ln in enumerate(lab.split("|")):
            fw = "800" if j == 0 else "400"
            fs = FS if j == 0 else FSA
            s.append(f'<text x="{x+18}" y="{y+28+j*22}" font-size="{fs}" font-weight="{fw}" fill="{PAL["ink"]}">{ln}</text>')
    s.append(f'<text x="660" y="356" text-anchor="middle" font-size="{FS}" fill="{PAL["soft"]}">{t["goal"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def build_figures(lang):
    F = figure_labels(lang)
    return {
        "match": fig_match(F["match"]), "cmf_rgb": fig_cmf_rgb(F["cmf_rgb"]),
        "negative": fig_negative(F["negative"]), "xyz_cmf": fig_xyz_cmf(F["xyz_cmf"]),
        "chromaticity": fig_chromaticity(F["chromaticity"]), "macadam": fig_macadam(F["macadam"]),
        "uv1976": fig_chromaticity_1976(F["uv1976"]), "lab": fig_lab(F["lab"]), "de": fig_de(F["de"]),
    }


# ---------------------------------------------------------------------------
# Figure labels per language
# ---------------------------------------------------------------------------
def figure_labels(lang):
    F = {}
    F["match"] = {
        "ko": dict(aria="색일치 실험 장치", test="측정 광원", single_wl="단일 파장", test_half="측정 색", mix_half="혼합 색", knobs="세 기준광 + 강도 조절", observer="관찰자", field2="2° 시야", adjust="세 강도를 돌려 두 반쪽이 똑같아 보이게 맞춘다"),
        "en": dict(aria="Color-matching apparatus", test="test source", single_wl="single wavelength", test_half="test", mix_half="mixture", knobs="three primaries + intensity", observer="observer", field2="2° field", adjust="turn the three intensities until both halves look identical"),
        "ja": dict(aria="等色実験装置", test="測定光源", single_wl="単一波長", test_half="測定色", mix_half="混合色", knobs="三原色 + 強度調整", observer="観察者", field2="2° 視野", adjust="三つの強度を回し両半分が同じに見えるよう合わせる"),
        "zh": dict(aria="颜色匹配装置", test="待测光源", single_wl="单一波长", test_half="待测色", mix_half="混合色", knobs="三原色 + 强度调节", observer="观察者", field2="2° 视场", adjust="转动三个强度，使两半看起来完全相同"),
    }[lang]
    F["cmf_rgb"] = {
        "ko": dict(aria="CIE RGB 색일치함수", x="파장 (nm)", y="값", neg="음수 구간"),
        "en": dict(aria="CIE RGB color-matching functions", x="Wavelength (nm)", y="Value", neg="negative region"),
        "ja": dict(aria="CIE RGB等色関数", x="波長 (nm)", y="値", neg="負の区間"),
        "zh": dict(aria="CIE RGB颜色匹配函数", x="波长 (nm)", y="值", neg="负值区间"),
    }[lang]
    F["negative"] = {
        "ko": dict(aria="음수가 나오는 이유", p_left="R+G+B로는 못 만든다", p_right="측정 색에 빨강을 더한다",
                   dull2="탁함", sat="선명함(채도) →", mixmax="R+G+B 혼합 최대", pure="순수 500nm",
                   cant="혼합은 순수 청록의 채도에 못 미친다", testc="청록", eq="측정색 = G + B − R", conc="빼준 빨강(−R)이 곧 음수 r̄"),
        "en": dict(aria="Why the function goes negative", p_left="R+G+B can't reach it", p_right="add red to the test side",
                   dull2="dull", sat="vividness (chroma) →", mixmax="max R+G+B mix", pure="pure 500nm",
                   cant="no mix is as saturated as pure cyan", testc="cyan", eq="test = G + B − R", conc="the subtracted red (−R) is the negative r̄"),
        "ja": dict(aria="なぜ負になるか", p_left="R+G+Bでは作れない", p_right="測定色に赤を足す",
                   dull2="濁り", sat="鮮やかさ(彩度) →", mixmax="R+G+B混合の最大", pure="純粋500nm",
                   cant="混合は純粋シアンの彩度に届かない", testc="シアン", eq="測定色 = G + B − R", conc="引いた赤(−R)が負のr̄"),
        "zh": dict(aria="为何出现负值", p_left="R+G+B无法达到", p_right="给待测色加红",
                   dull2="浊", sat="鲜艳(彩度) →", mixmax="R+G+B混合上限", pure="纯500nm",
                   cant="任何混合都不及纯青饱和", testc="青", eq="待测 = G + B − R", conc="被减去的红(−R)即负的r̄"),
    }[lang]
    F["xyz_cmf"] = {
        "ko": dict(aria="CIE 1931 XYZ 색일치함수", x="파장 (nm)", y="값 (전 구간 양수)"),
        "en": dict(aria="CIE 1931 XYZ color-matching functions", x="Wavelength (nm)", y="Value (all positive)"),
        "ja": dict(aria="CIE 1931 XYZ等色関数", x="波長 (nm)", y="値（全域で正）"),
        "zh": dict(aria="CIE 1931 XYZ颜色匹配函数", x="波长 (nm)", y="值（全域为正）"),
    }[lang]
    F["chromaticity"] = {
        "ko": dict(aria="CIE 1931 xy 색도도", srgb="sRGB 색역", white="백색점 D65", locus="스펙트럼 궤적"),
        "en": dict(aria="CIE 1931 xy chromaticity diagram", srgb="sRGB gamut", white="white D65", locus="spectral locus"),
        "ja": dict(aria="CIE 1931 xy色度図", srgb="sRGB色域", white="白色点 D65", locus="スペクトル軌跡"),
        "zh": dict(aria="CIE 1931 xy色度图", srgb="sRGB色域", white="白点 D65", locus="光谱轨迹"),
    }[lang]
    F["macadam"] = {
        "ko": dict(aria="맥아담 타원", green="초록: 큼", blue="파랑: 작음", note="타원 ×10 과장 — 위치마다 크기·방향 제각각"),
        "en": dict(aria="MacAdam ellipses", green="green: large", blue="blue: small", note="ellipses ×10 exaggerated — size/orientation vary by location"),
        "ja": dict(aria="マクアダム楕円", green="緑: 大", blue="青: 小", note="楕円×10誇張 — 位置ごとに大きさ・向きが異なる"),
        "zh": dict(aria="麦克亚当椭圆", green="绿: 大", blue="蓝: 小", note="椭圆×10夸张 — 各位置大小方向不同"),
    }[lang]
    F["uv1976"] = {
        "ko": dict(aria="CIE 1976 u'v' 색도도", white="백색점 D65"),
        "en": dict(aria="CIE 1976 u'v' chromaticity diagram", white="white D65"),
        "ja": dict(aria="CIE 1976 u'v'色度図", white="白色点 D65"),
        "zh": dict(aria="CIE 1976 u'v'色度图", white="白点 D65"),
    }[lang]
    F["lab"] = {
        "ko": dict(aria="CIELAB 색공간", light="밝기", red="적", green="녹", yellow="황", blue="청", white_w="흰색", black_w="검정"),
        "en": dict(aria="CIELAB color space", light="lightness", red="red", green="green", yellow="yellow", blue="blue", white_w="white", black_w="black"),
        "ja": dict(aria="CIELAB色空間", light="明るさ", red="赤", green="緑", yellow="黄", blue="青", white_w="白", black_w="黒"),
        "zh": dict(aria="CIELAB色空间", light="亮度", red="红", green="绿", yellow="黄", blue="蓝", white_w="白", black_w="黑"),
    }[lang]
    F["de"] = {
        "ko": dict(aria="색차 ΔE 진화", e76="ΔE*ab (1976)", e76sub="CIELAB 두 점의 직선거리", sl="SL|밝기 가중", sc="SC|채도 가중", sh="SH|색상 가중", rt="RT|파랑 영역 회전 보정", goal="목표: 한 숫자 = 사람이 느끼는 색 차이"),
        "en": dict(aria="Evolution of color difference", e76="ΔE*ab (1976)", e76sub="straight distance in CIELAB", sl="SL|lightness weight", sc="SC|chroma weight", sh="SH|hue weight", rt="RT|blue-region rotation", goal="goal: one number = the difference people perceive"),
        "ja": dict(aria="色差ΔEの進化", e76="ΔE*ab (1976)", e76sub="CIELAB二点の直線距離", sl="SL|明度の重み", sc="SC|彩度の重み", sh="SH|色相の重み", rt="RT|青領域の回転補正", goal="目標: 一つの数 = 人が感じる色差"),
        "zh": dict(aria="色差ΔE演进", e76="ΔE*ab (1976)", e76sub="CIELAB两点的直线距离", sl="SL|明度权重", sc="SC|彩度权重", sh="SH|色相权重", rt="RT|蓝区旋转修正", goal="目标: 一个数 = 人所感知的色差"),
    }[lang]
    return F


# ---------------------------------------------------------------------------
# Display formulas (language-neutral)
# ---------------------------------------------------------------------------
FORMULAS = {
    "xyz_int": "<i>X</i> = ∫ <i>S</i>(λ) x̄(λ) dλ &nbsp;&nbsp; <i>Y</i> = ∫ <i>S</i>(λ) ȳ(λ) dλ &nbsp;&nbsp; <i>Z</i> = ∫ <i>S</i>(λ) z̄(λ) dλ",
    "xy": "<i>x</i> = <i>X</i> / (<i>X</i>+<i>Y</i>+<i>Z</i>) &nbsp;&nbsp;&nbsp; <i>y</i> = <i>Y</i> / (<i>X</i>+<i>Y</i>+<i>Z</i>)",
    "uv": "<i>u′</i> = 4<i>X</i> / (<i>X</i>+15<i>Y</i>+3<i>Z</i>) &nbsp;&nbsp;&nbsp; <i>v′</i> = 9<i>Y</i> / (<i>X</i>+15<i>Y</i>+3<i>Z</i>)",
    "lab": "<i>L*</i> = 116·<i>f</i>(<i>Y</i>/<i>Y</i><sub>n</sub>) − 16<br><i>a*</i> = 500·[<i>f</i>(<i>X</i>/<i>X</i><sub>n</sub>) − <i>f</i>(<i>Y</i>/<i>Y</i><sub>n</sub>)] &nbsp;&nbsp; <i>b*</i> = 200·[<i>f</i>(<i>Y</i>/<i>Y</i><sub>n</sub>) − <i>f</i>(<i>Z</i>/<i>Z</i><sub>n</sub>)]",
    "de76": "Δ<i>E*</i><sub>ab</sub> = √( Δ<i>L*</i>² + Δ<i>a*</i>² + Δ<i>b*</i>² )",
    "de00": "Δ<i>E</i><sub>00</sub> = √[ (Δ<i>L′</i>/<i>k</i><sub>L</sub><i>S</i><sub>L</sub>)² + (Δ<i>C′</i>/<i>k</i><sub>C</sub><i>S</i><sub>C</sub>)² + (Δ<i>H′</i>/<i>k</i><sub>H</sub><i>S</i><sub>H</sub>)² + <i>R</i><sub>T</sub>·(Δ<i>C′</i>/<i>k</i><sub>C</sub><i>S</i><sub>C</sub>)(Δ<i>H′</i>/<i>k</i><sub>H</sub><i>S</i><sub>H</sub>) ]",
}


# ---------------------------------------------------------------------------
# Interactive color-matching simulation widget (auto-playing JS animation)
# ---------------------------------------------------------------------------
def _sim_data_js():
    import numpy as np
    wl, r, g, b = cie.rgb_cmf()
    WL = list(range(400, 701, 5))
    at = lambda a, w: round(float(a[int(np.argmin(np.abs(wl - w)))]), 4)
    R = [at(r, w) for w in WL]; G = [at(g, w) for w in WL]; B = [at(b, w) for w in WL]
    SPEC = [p1.wl_to_rgb(w) for w in WL]
    return "const SIM={wl:%s,r:%s,g:%s,b:%s,spec:%s};" % (
        json.dumps(WL), json.dumps(R), json.dumps(G), json.dumps(B), json.dumps(SPEC))


SIM_JS = _sim_data_js()

SIM_SVG = """<svg viewBox="0 0 600 470" xmlns="http://www.w3.org/2000/svg" aria-label="{{ARIA}}">
  <defs>
    <linearGradient id="csrain" x1="0" x2="1">
      <stop offset="0%" stop-color="#7a4bd0"/><stop offset="14%" stop-color="#3b5bd0"/>
      <stop offset="30%" stop-color="#19b6c4"/><stop offset="46%" stop-color="#36c25a"/>
      <stop offset="62%" stop-color="#d6d23a"/><stop offset="78%" stop-color="#e07b2a"/>
      <stop offset="100%" stop-color="#d23b3b"/></linearGradient>
    <marker id="csauxar" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#e4572e"/></marker>
  </defs>
  <rect x="60" y="38" width="480" height="16" rx="3" fill="url(#csrain)"/>
  <text x="60" y="30" font-size="12" fill="#8a9aa3">400</text>
  <text x="540" y="30" font-size="12" fill="#8a9aa3" text-anchor="end">700 nm</text>
  <polygon id="csPtr" points="0,0" fill="#22303a"/>
  <clipPath id="csfclip"><circle cx="150" cy="172" r="74"/></clipPath>
  <g clip-path="url(#csfclip)">
    <rect id="csTest" x="76" y="98" width="74" height="148" fill="#19b6c4"/>
    <rect id="csMix"  x="150" y="98" width="74" height="148" fill="#19b6c4"/>
  </g>
  <line x1="150" y1="98" x2="150" y2="246" stroke="#fff" stroke-width="1.4" opacity="0.5"/>
  <circle cx="150" cy="172" r="74" fill="none" stroke="#22303a" stroke-width="2.5"/>
  <text x="113" y="90" font-size="13" font-weight="700" fill="#22303a" text-anchor="middle">{{TEST}}</text>
  <text x="187" y="90" font-size="13" font-weight="700" fill="#22303a" text-anchor="middle">{{MIX}}</text>
  <text x="150" y="270" font-size="12.5" fill="#5a6b76" text-anchor="middle">{{MATCH}}</text>
  <g id="csAux" opacity="0">
    <line x1="150" y1="150" x2="113" y2="150" stroke="#e4572e" stroke-width="5" marker-end="url(#csauxar)"/>
    <text x="150" y="126" font-size="11.5" font-weight="700" fill="#e4572e" text-anchor="middle">{{AUX}}</text>
  </g>
  <text x="430" y="90" font-size="13" font-weight="800" fill="#22303a" text-anchor="middle">{{BARS}}</text>
  <line x1="322" y1="226" x2="540" y2="226" stroke="#9fb0b8" stroke-width="1.5"/>
  <text x="318" y="230" font-size="11" fill="#8a9aa3" text-anchor="end">0</text>
  <rect id="csBarR" x="348" y="226" width="40" height="0" fill="#e4572e"/>
  <rect id="csBarG" x="412" y="226" width="40" height="0" fill="#36a655"/>
  <rect id="csBarB" x="476" y="226" width="40" height="0" fill="#2d6cdf"/>
  <text x="368" y="262" font-size="13" font-weight="800" fill="#e4572e" text-anchor="middle">R</text>
  <text x="432" y="262" font-size="13" font-weight="800" fill="#36a655" text-anchor="middle">G</text>
  <text x="496" y="262" font-size="13" font-weight="800" fill="#2d6cdf" text-anchor="middle">B</text>
  <text x="368" y="278" font-size="9.5" fill="#8a9aa3" text-anchor="middle">700</text>
  <text x="432" y="278" font-size="9.5" fill="#8a9aa3" text-anchor="middle">546</text>
  <text x="496" y="278" font-size="9.5" fill="#8a9aa3" text-anchor="middle">436</text>
  <text id="csNeg" x="430" y="300" font-size="10.5" font-weight="700" fill="#e4572e" text-anchor="middle" opacity="0">{{NEG}}</text>
  <text x="60" y="332" font-size="12" font-weight="700" fill="#5a6b76">{{CMFLBL}}</text>
  <line x1="60" y1="410" x2="540" y2="410" stroke="#cfd9de" stroke-width="1.2"/>
  <polyline id="csCurveR" points="" fill="none" stroke="#e4572e" stroke-width="2.4"/>
  <polyline id="csCurveG" points="" fill="none" stroke="#36a655" stroke-width="2.4"/>
  <polyline id="csCurveB" points="" fill="none" stroke="#2d6cdf" stroke-width="2.4"/>
  <line id="csSweep" x1="60" y1="350" x2="60" y2="454" stroke="#22303a" stroke-width="1.6" stroke-dasharray="4 3"/>
</svg>"""

SIM_SCRIPT = """<script>(function(){{
{SIMDATA}
var N=SIM.wl.length, SX0=60,SX1=540, FZERO=410, BASE=226;
function $(id){{return document.getElementById(id);}}
function xp(i){{return SX0+(SX1-SX0)*i/(N-1);}}
function curve(a,sc){{var p='';for(var i=0;i<N;i++){{p+=xp(i).toFixed(1)+','+(FZERO-a[i]*sc).toFixed(1)+' ';}}return p;}}
$('csCurveR').setAttribute('points',curve(SIM.r,210));
$('csCurveG').setAttribute('points',curve(SIM.g,210));
$('csCurveB').setAttribute('points',curve(SIM.b,210));
function bar(el,v){{var h=Math.abs(v)*300;if(v>=0){{el.setAttribute('y',BASE-h);}}else{{el.setAttribute('y',BASE);}}el.setAttribute('height',h);el.setAttribute('opacity',0.92);}}
function render(i){{
  var col=SIM.spec[i];
  $('csTest').setAttribute('fill',col); $('csMix').setAttribute('fill',col);
  $('csLamN').textContent=SIM.wl[i]+' nm';
  var px=xp(i);
  $('csPtr').setAttribute('points',(px-6)+',34 '+(px+6)+',34 '+px+',46');
  bar($('csBarR'),SIM.r[i]); bar($('csBarG'),SIM.g[i]); bar($('csBarB'),SIM.b[i]);
  var neg=SIM.r[i]<0; $('csAux').setAttribute('opacity',neg?1:0); $('csNeg').setAttribute('opacity',neg?1:0);
  $('csSweep').setAttribute('x1',px); $('csSweep').setAttribute('x2',px);
  $('csSld').value=i;
}}
var i=0, dir=1, playing=true, last=0;
function tick(t){{ if(playing && t-last>75){{last=t; i+=dir; if(i>=N-1){{i=N-1;dir=-1;}}else if(i<=0){{i=0;dir=1;}} render(i);}} requestAnimationFrame(tick); }}
$('csPlayBtn').addEventListener('click',function(){{playing=!playing;$('csPlayBtn').textContent=playing?'\\u23F8':'\\u25B6';}});
$('csSld').addEventListener('input',function(e){{playing=false;$('csPlayBtn').textContent='\\u25B6';i=+e.target.value;render(i);}});
render(i); requestAnimationFrame(tick);
}})();</script>"""


def sim_labels(lang):
    return {
        "ko": dict(aria="색일치 자동 시뮬레이션", ttl="색일치 시뮬레이션", live="AUTO",
                   desc="파장이 바뀌면 세 기준광 <b>R·G·B</b>의 강도가 변한다. 청록 구간에서 R이 음수가 되면, 혼합 쪽이 아니라 <b>측정 색 쪽에 R을 더하는 보조광(트릭)</b>으로 처리한다 — 이것이 색일치함수의 음수다.",
                   test="측정", mix="혼합", match="두 반쪽은 항상 일치 (≡)", aux="보조광 +R",
                   bars="기준광 강도", neg="R < 0 → 보조광", cmf="색일치함수 r̄ ḡ b̄"),
        "en": dict(aria="Auto color-matching simulation", ttl="Color-matching simulation", live="AUTO",
                   desc="As the wavelength sweeps, the three primaries <b>R·G·B</b> change intensity. In the cyan band R turns negative, so instead of the mix side, <b>red is added to the test side as an auxiliary light (the trick)</b> — that is the negative in the color-matching function.",
                   test="test", mix="mix", match="the two halves always match (≡)", aux="aux +R",
                   bars="primary intensity", neg="R < 0 → auxiliary", cmf="color-matching functions r̄ ḡ b̄"),
        "ja": dict(aria="等色の自動シミュレーション", ttl="等色シミュレーション", live="AUTO",
                   desc="波長が変わると三原色 <b>R·G·B</b> の強度が変わる。シアン帯でRが負になると、混合側ではなく <b>測定色側に赤を足す補助光（トリック）</b> で処理する — これが等色関数の負だ。",
                   test="測定", mix="混合", match="両半分は常に一致 (≡)", aux="補助光 +R",
                   bars="原色の強度", neg="R < 0 → 補助光", cmf="等色関数 r̄ ḡ b̄"),
        "zh": dict(aria="颜色匹配自动模拟", ttl="颜色匹配模拟", live="AUTO",
                   desc="波长扫过时，三原色 <b>R·G·B</b> 的强度随之变化。青色波段R变为负值，于是不在混合侧，而是 <b>把红加到待测色一侧作为辅助光（技巧）</b> — 这正是颜色匹配函数中的负值。",
                   test="待测", mix="混合", match="两半始终一致 (≡)", aux="辅助光 +R",
                   bars="原色强度", neg="R < 0 → 辅助光", cmf="颜色匹配函数 r̄ ḡ b̄"),
    }[lang]


def sim_widget(lang):
    t = sim_labels(lang)
    svg = SIM_SVG
    for k, v in {"{{ARIA}}": t["aria"], "{{TEST}}": t["test"], "{{MIX}}": t["mix"],
                 "{{MATCH}}": t["match"], "{{AUX}}": t["aux"], "{{BARS}}": t["bars"],
                 "{{NEG}}": t["neg"], "{{CMFLBL}}": t["cmf"]}.items():
        svg = svg.replace(k, v)
    script = SIM_SCRIPT.format(SIMDATA=SIM_JS)
    return (
        '<div class="cs-sim" role="group">'
        f'<div class="cs-ttl">{t["ttl"]} <span class="cs-live">● {t["live"]}</span></div>'
        f'<div class="cs-desc">{t["desc"]}</div>'
        f'{svg}'
        '<div class="cs-ctrl">'
        f'<button class="cs-btn" id="csPlayBtn" aria-label="play/pause">⏸</button>'
        '<input class="cs-slider" type="range" id="csSld" min="0" max="60" value="0">'
        '<div class="cs-readout"><span id="csLamN">400 nm</span></div>'
        '</div></div>'
        f'{script}')


# ---------------------------------------------------------------------------
# HTML head (part-2 hreflang)
# ---------------------------------------------------------------------------
HEAD = p1.HEAD.replace("color-science-01-how-we-see", SLUG)


def build_html(lang):
    c = content(lang)
    figs = build_figures(lang)
    suffix = LANG_SUFFIX[lang]
    canon = f"https://luckyplz.com/blog/{SLUG}{suffix}/"
    body_font, font_url = FONT[lang]
    og_img = f"https://luckyplz.com/assets/blog/{SLUG}-{lang}.png?v={BUILD}"
    prev_url = f"https://luckyplz.com/blog/{PREV_SLUG}{suffix}/"

    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": c["title"], "description": c["desc"], "image": og_img,
        "datePublished": DATE, "dateModified": DATE,
        "author": {"@type": "Organization", "name": "Lucky Please", "url": "https://luckyplz.com/"},
        "publisher": {"@type": "Organization", "name": "Lucky Please",
                      "logo": {"@type": "ImageObject", "url": "https://luckyplz.com/assets/icon-192.png"}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": canon}, "inLanguage": lang,
    }, ensure_ascii=False)
    crumb = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": c["home"], "item": "https://luckyplz.com/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://luckyplz.com/blog/"},
            {"@type": "ListItem", "position": 3, "name": c["title"], "item": canon}]}, ensure_ascii=False)

    head = HEAD
    for k, v in {
        "{{LANG}}": lang, "{{BUILD}}": BUILD, "{{TITLE}}": _esc(c["title"]),
        "{{DESC}}": _esc(c["desc"]), "{{KEYWORDS}}": _esc(c["keywords"]),
        "{{CANON}}": canon, "{{OG_TITLE}}": _esc(c["og_title"]), "{{OG_DESC}}": _esc(c["og_desc"]),
        "{{OG_IMG}}": og_img, "{{OG_LOCALE}}": OG_LOCALE[lang], "{{JSONLD}}": jsonld,
        "{{JSONLD_CRUMB}}": crumb, "{{FONT_URL}}": font_url,
        "{{CSS}}": CSS.replace("BODYFONT", body_font),
    }.items():
        head = head.replace(k, v)

    parts = [head]
    parts.append('<header class="hero">')
    parts.append(f'<div class="kicker">{c["kicker"]}</div>')
    parts.append(f'<h1>{c["h1"]}</h1>')
    parts.append(f'<div class="sub">{c["sub"]}</div>')
    parts.append('</header>')
    parts.append(f'<div class="snav"><a href="{prev_url}">{c["prev_label"]} &nbsp;<b>{c["prev_text"]}</b></a></div>')
    parts.append(f'<p class="lead">{c["lead"]}</p>')

    SQUARE = {"chromaticity", "macadam", "uv1976", "lab"}
    fignum = [0]

    def add_fig(figkey, cap):
        fignum[0] += 1
        cls = " square" if figkey in SQUARE else ""
        parts.append('<figure>')
        parts.append(f'<div class="fig-box{cls}">{figs[figkey]}</div>')
        parts.append(f'<figcaption><b>{c["fig_word"]} {fignum[0]}.</b> {cap}</figcaption>')
        parts.append('</figure>')

    for i, sec in enumerate(c["secs"]):
        parts.append('<section>')
        parts.append(f'<h2>{sec["h2"]}</h2>')
        for p in sec["paras"]:
            parts.append(f'<p>{p}</p>')
        for fk in sec.get("fml", []):
            parts.append(f'<div class="formula">{FORMULAS[fk]}</div>')
        if sec.get("fig"):
            add_fig(sec["fig"], sec["cap"])
        if sec.get("fig2"):
            add_fig(sec["fig2"], sec["cap2"])
        parts.append('</section>')
        if i == 1:  # after the color-matching-function section: the live simulation
            parts.append(sim_widget(lang))
        if i == 3:
            parts.append('<div data-lp-ad="blog" style="margin:30px 0;"></div>')

    parts.append(f'<div class="closing"><h2>{c["closing_h2"]}</h2><p>{c["closing"]}</p></div>')
    parts.append(f'<div class="snav" style="margin-top:26px"><a href="{prev_url}">{c["prev_label"]} &nbsp;<b>{c["prev_text"]}</b></a></div>')
    parts.append('</div>')

    parts.append('<div class="wrap" style="padding-top:0">')
    parts.append(f'<div style="margin:30px 0 0;padding:16px 18px;background:#fff;border:1px solid var(--line);border-radius:12px;font-size:13px;color:var(--soft);line-height:1.7"><b style="color:var(--ink)">By <a href="/about/">Lucky Please</a></b><br>{c["author_desc"]}</div>')
    parts.append('</div>')
    parts.append(f'<footer>{c["src"]}<br><br><a href="/blog/?cat={CATEGORY}">← {c["all_list"]}</a> · <a href="/">🏠 {c["home"]}</a></footer>')
    parts.append("""
<script>
if('serviceWorker' in navigator){navigator.serviceWorker.getRegistrations().then(r=>r.forEach(s=>s.unregister())).catch(()=>{})}
if('caches' in window){caches.keys().then(k=>k.forEach(n=>caches.delete(n))).catch(()=>{})}
</script>
<script src="/vendor/supabase.min.js"></script>
<script src="/js/supabase-config.js?v=BUILD" defer></script>
<script src="/blog/posts.js?v=BUILD" defer></script>
<script src="/js/blogRelated.js?v=BUILD" defer></script>
<script src="/js/blogSubscribe.js?v=BUILD" defer></script>
<script src="/js/siteFooter.js?v=BUILD" defer></script>
</body>
</html>""".replace("BUILD", BUILD))
    return "\n".join(parts)


def make_og(lang):
    from PIL import Image, ImageDraw
    spec = importlib.util.spec_from_file_location("gdo", ROOT / "scripts" / "gen_daily_og.py")
    gdo = importlib.util.module_from_spec(spec); spec.loader.exec_module(gdo)
    f = gdo.load_font_for_lang
    c = content(lang)
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (250, 247, 240))
    d = ImageDraw.Draw(img)
    cols = [(122, 75, 208), (45, 108, 223), (58, 166, 85), (232, 210, 58), (228, 87, 46), (200, 50, 40)]
    bw = W / len(cols)
    for i, col in enumerate(cols):
        d.rectangle([i * bw, 0, (i + 1) * bw, 12], fill=col)
    d.text((64, 70), c["kicker"], font=f(lang, 30, bold=True), fill=(192, 138, 45))
    title = c["h1"]
    fz = 64 if len(title) < 14 else 54
    fnt = f(lang, fz, bold=True)
    words = title.split(" ")
    lines, cur, maxw = [], "", W - 128
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=fnt) > maxw and cur:
            lines.append(cur); cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    if len(lines) == 1 and len(title) > 9:
        half = len(title) // 2
        lines = [title[:half], title[half:]]
    y = 210
    for ln in lines[:3]:
        d.text((64, y), ln, font=fnt, fill=(28, 41, 48)); y += fz + 14
    d.text((64, 470), c["sub"][:42], font=f(lang, 26, bold=False), fill=(81, 96, 105))
    # mini chromaticity horseshoe motif (bottom-right)
    ox2, oy2 = 980, 560
    locus = [chromaticity(nm) for nm in range(400, 690, 6)]
    pl = [(ox2 + 150 * x, oy2 - 150 * y) for x, y in locus]
    if len(pl) > 2:
        d.line(pl + [pl[0]], fill=(150, 120, 200), width=3)
    d.text((64, 582), "luckyplz.com", font=f("en", 24, bold=True), fill=(192, 138, 45))
    out = ASSETS_BLOG / f"{SLUG}-{lang}.png"
    img.save(out, "PNG", optimize=True)
    print(f"[og] {out.name} ({out.stat().st_size//1024}KB)")


def write_files():
    for lang in ("ko", "en", "ja", "zh"):
        d = BLOG / f"{SLUG}{LANG_SUFFIX[lang]}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(build_html(lang), encoding="utf-8")
        print(f"[write] {d}/index.html")


def update_posts_js():
    p = PUBLIC / "blog" / "posts.js"
    raw = p.read_text(encoding="utf-8")
    marker = "window.BLOG_POSTS = ["
    idx = raw.find(marker)
    if f"'{SLUG}'" in raw:
        print("[posts.js] already present")
        return
    tags = {"ko": ["색채과학", "CIE", "색좌표"], "en": ["Color Science", "CIE", "Colorimetry"],
            "ja": ["色彩科学", "CIE", "表色系"], "zh": ["色彩科学", "CIE", "色度学"]}
    slug_map = {l: f"{SLUG}{LANG_SUFFIX[l]}" for l in ("ko", "en", "ja", "zh")}
    entries = []
    for lang in ("ko", "en", "ja", "zh"):
        c = content(lang)
        alts = {l: s for l, s in slug_map.items() if l != lang}
        alts_js = "{ " + ", ".join(f"{k}: '{v}'" for k, v in alts.items()) + " }"
        alt_legacy = slug_map["en"] if lang == "ko" else slug_map["ko"]
        entries.append(
            "{\n"
            f"        slug: '{slug_map[lang]}',\n        lang: '{lang}',\n"
            f"        category: '{CATEGORY}',\n        date: '{DATE}',\n"
            f"        readMinutes: {READ_MIN},\n        coverEmoji: '{COVER_EMOJI}',\n"
            f"        tags: {json.dumps(tags[lang], ensure_ascii=False)},\n"
            f"        title: {json.dumps(c['h1'], ensure_ascii=False)},\n"
            f"        excerpt: {json.dumps(c['og_desc'], ensure_ascii=False)},\n"
            f"        alt: '{alt_legacy}',\n        alts: {alts_js},\n    }},")
    combined = "\n    ".join(entries)
    raw = raw[:idx + len(marker)] + "\n    " + combined + raw[idx + len(marker):]
    p.write_text(raw, encoding="utf-8")
    print("[posts.js] prepended 4 entries")


def update_sitemap():
    p = PUBLIC / "sitemap.xml"
    raw = p.read_text(encoding="utf-8")
    if f"{SLUG}/" in raw and f"{SLUG}-en/" in raw:
        print("[sitemap] already present")
        return
    base = "https://luckyplz.com/blog/"
    alts = {"ko": f"{base}{SLUG}/", "en": f"{base}{SLUG}-en/", "ja": f"{base}{SLUG}-ja/", "zh": f"{base}{SLUG}-zh/"}
    blocks = []
    for lang, url in alts.items():
        links = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{u}"/>' for l, u in alts.items())
        links += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{alts["en"]}"/>'
        blocks.append(f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{DATE}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.9</priority>{links}\n  </url>')
    raw = raw.replace("</urlset>", "\n" + "\n".join(blocks) + "\n</urlset>")
    p.write_text(raw, encoding="utf-8")
    print("[sitemap] added 4 url blocks")


def main():
    ASSETS_BLOG.mkdir(parents=True, exist_ok=True)
    # filled-gamut + Lab disk PNGs (real CMF + xy->sRGB / Lab->sRGB)
    cie.render_chromaticity_png(ASSETS_BLOG / GAMUT_1931, "1931", res=1000)
    cie.render_chromaticity_png(ASSETS_BLOG / GAMUT_1976, "1976", res=1000)
    cie.render_lab_disk(ASSETS_BLOG / LAB_DISK, L=65, ab=120, res=900)
    print(f"[gamut] wrote {GAMUT_1931}, {GAMUT_1976}, {LAB_DISK}")
    for lang in ("ko", "en", "ja", "zh"):
        try:
            make_og(lang)
        except Exception as e:
            print(f"[og] {lang} failed: {e}")
    write_files()
    update_posts_js()
    update_sitemap()
    print("[done] color-science-02")


if __name__ == "__main__":
    main()
