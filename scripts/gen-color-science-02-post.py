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

# extra CSS: formula blocks + series nav
CSS = CSS_BASE + """
.formula{margin:18px auto;padding:16px 18px;background:#fbf9f4;border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:0 10px 10px 0;font-family:'Cambria','Georgia',serif;font-size:18px;line-height:2;color:#1c2930;overflow-x:auto;text-align:center}
.formula i{font-style:italic}
.snav{display:flex;gap:10px;margin:8px 0 26px;flex-wrap:wrap}
.snav a{display:inline-flex;align-items:center;gap:8px;padding:9px 15px;background:#fff;border:1px solid var(--line);border-radius:10px;font-size:13.5px;font-weight:600;color:var(--soft)}
.snav a b{color:var(--ink)}
@media(min-width:900px){.formula{font-size:20px;max-width:760px}}
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
    s.append(f'<text x="{ox+w}" y="{oy+30}" text-anchor="end" font-size="{FS}" fill="{PAL["soft"]}">{xl}</text>')
    s.append(f'<text x="{ox-6}" y="{oy-h-10}" font-size="{FS}" fill="{PAL["soft"]}">{yl}</text>')


def fig_match(t):
    W, H = 900, 380
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    cx, cy, r = 240, 180, 130
    # bipartite field
    s.append(f'<clipPath id="cm"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
    s.append(f'<g clip-path="url(#cm)">')
    s.append(f'<rect x="{cx-r}" y="{cy-r}" width="{r}" height="{2*r}" fill="#10c0c8"/>')  # test (cyan)
    s.append(f'<rect x="{cx}" y="{cy-r}" width="{r}" height="{2*r}" fill="#16b9c0"/>')   # match
    s.append('</g>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{PAL["ink"]}" stroke-width="2"/>')
    s.append(f'<line x1="{cx}" y1="{cy-r}" x2="{cx}" y2="{cy+r}" stroke="{PAL["bg"] if "bg" in PAL else "#fff"}" stroke-width="2" opacity="0.5"/>')
    s.append(f'<text x="{cx-r/2:.0f}" y="{cy-r-14}" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["ink"]}">{t["test"]}</text>')
    s.append(f'<text x="{cx+r/2:.0f}" y="{cy-r-14}" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["ink"]}">{t["mix"]}</text>')
    # three primary knobs
    prim = [("R 700nm", PAL["L"]), ("G 546nm", PAL["M"]), ("B 436nm", PAL["S"])]
    bx = 540
    s.append(f'<text x="{bx}" y="{60}" font-size="{FST}" font-weight="700" fill="{PAL["ink"]}">{t["knobs"]}</text>')
    for i, (lab, col) in enumerate(prim):
        y = 100 + i * 70
        s.append(f'<circle cx="{bx+20}" cy="{y}" r="20" fill="{col}"/>')
        s.append(f'<line x1="{bx+20}" y1="{y}" x2="{bx+20+14}" y2="{y-12}" stroke="#fff" stroke-width="3"/>')
        s.append(f'<rect x="{bx+60}" y="{y-7}" width="180" height="14" rx="7" fill="#eee" stroke="{PAL["line"]}"/>')
        s.append(f'<rect x="{bx+60}" y="{y-7}" width="{60+i*40}" height="14" rx="7" fill="{col}" opacity="0.8"/>')
        s.append(f'<text x="{bx+50}" y="{y+6}" text-anchor="end" font-size="{FS}" font-weight="700" fill="{col}">{lab}</text>')
    s.append(f'<text x="{bx}" y="{330}" font-size="{FS}" fill="{PAL["soft"]}">{t["adjust"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_cmf_rgb(t):
    W, H = 900, 430
    ox, oy, w, h = 64, 330, 780, 240
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    lo, hi = 380, 700
    xs = lambda nm: ox + w * (nm - lo) / (hi - lo)
    zero = oy - h * 0.30  # baseline above axis bottom so negatives show
    s.append(f'<line x1="{ox}" y1="{zero}" x2="{ox+w}" y2="{zero}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy-h}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    s.append(f'<text x="{ox+w}" y="{zero-8}" text-anchor="end" font-size="{FS}" fill="{PAL["soft"]}">{t["x"]}</text>')
    s.append(f'<text x="{ox+6}" y="{oy-h+4}" font-size="{FS}" fill="{PAL["soft"]}">{t["y"]}</text>')
    for nm in range(400, 701, 50):
        s.append(f'<text x="{xs(nm):.0f}" y="{oy+24}" text-anchor="middle" font-size="{FSA}" fill="{PAL["mute"]}">{nm}</text>')
        s.append(f'<line x1="{xs(nm):.0f}" y1="{zero}" x2="{xs(nm):.0f}" y2="{zero+5}" stroke="{PAL["axis"]}"/>')
    sc = h * 0.62
    # schematic CIE rgb CMFs (shape incl. negative r-bar lobe)
    def rbar(nm):
        pos = 0.30 * gauss(nm, 600, 28) + 0.06 * gauss(nm, 445, 18)
        neg = 0.10 * gauss(nm, 510, 26)
        return pos - neg
    def gbar(nm):
        return 0.30 * gauss(nm, 545, 33) - 0.02 * gauss(nm, 430, 20)
    def bbar(nm):
        return 0.34 * gauss(nm, 445, 19)
    for fn, col, lab, lx in [(bbar, PAL["S"], "b̄(λ)", 455), (gbar, PAL["M"], "ḡ(λ)", 545), (rbar, PAL["L"], "r̄(λ)", 600)]:
        pts = [(xs(nm), zero - sc * fn(nm)) for nm in range(lo, hi + 1, 2)]
        s.append(f'<polyline points="{_poly(pts)}" fill="none" stroke="{col}" stroke-width="3.2"/>')
        s.append(f'<text x="{xs(lx):.0f}" y="{zero - sc*fn(lx) - 12:.0f}" text-anchor="middle" font-size="{FST}" font-weight="800" fill="{col}">{lab}</text>')
    # highlight negative region of r-bar
    s.append(f'<rect x="{xs(440):.0f}" y="{zero}" width="{xs(545)-xs(440):.0f}" height="{oy-zero}" fill="{PAL["L"]}" opacity="0.07"/>')
    s.append(f'<text x="{xs(495):.0f}" y="{oy-6}" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["L"]}">{t["neg"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_negative(t):
    W, H = 900, 360
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    # left panel: cannot match
    for px, title, ok in [(40, t["p_left"], False), (480, t["p_right"], True)]:
        s.append(f'<rect x="{px}" y="40" width="380" height="290" rx="14" fill="{PAL["panel"]}" stroke="{PAL["line"]}"/>')
        s.append(f'<text x="{px+190}" y="74" text-anchor="middle" font-size="{FST}" font-weight="800" fill="{PAL["ink"]}">{title}</text>')
    # left: test cyan vs mix (too dull) -> X
    s.append(f'<circle cx="120" cy="160" r="42" fill="#0ec6cf"/><text x="120" y="222" text-anchor="middle" font-size="{FS}" fill="{PAL["soft"]}">{t["test"]}</text>')
    s.append(f'<text x="210" y="166" text-anchor="middle" font-size="26" fill="{PAL["mute"]}">≠</text>')
    s.append(f'<circle cx="300" cy="160" r="42" fill="#6aa6a0"/><text x="300" y="222" text-anchor="middle" font-size="{FS}" fill="{PAL["soft"]}">R+G+B</text>')
    s.append(f'<text x="230" y="300" text-anchor="middle" font-size="{FS}" fill="{PAL["L"]}">{t["dull"]}</text>')
    # right: test+red -> matches G+B
    s.append(f'<circle cx="560" cy="150" r="34" fill="#0ec6cf"/>')
    s.append(f'<text x="610" y="156" text-anchor="middle" font-size="24" fill="{PAL["L"]}">+</text>')
    s.append(f'<circle cx="660" cy="150" r="22" fill="{PAL["L"]}"/><text x="660" y="120" text-anchor="middle" font-size="{FSA}" fill="{PAL["L"]}">R</text>')
    s.append(f'<text x="720" y="156" text-anchor="middle" font-size="26" fill="{PAL["M"]}">=</text>')
    s.append(f'<circle cx="790" cy="150" r="34" fill="#6fae86"/><text x="790" y="120" text-anchor="middle" font-size="{FSA}" fill="{PAL["soft"]}">G+B</text>')
    s.append(f'<text x="670" y="250" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["ink"]}">{t["eq"]}</text>')
    s.append(f'<text x="670" y="292" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["L"]}">{t["arrow_neg"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_xyz_cmf(t):
    W, H = 900, 400
    ox, oy, w, h = 64, 330, 780, 250
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    lo, hi = 380, 700
    xs = lambda nm: ox + w * (nm - lo) / (hi - lo)
    _ax(s, ox, oy, w, h, t["x"], t["y"])
    for nm in range(400, 701, 50):
        s.append(f'<text x="{xs(nm):.0f}" y="{oy+24}" text-anchor="middle" font-size="{FSA}" fill="{PAL["mute"]}">{nm}</text>')
    peak = max(max(cie_x(n), cie_y(n), cie_z(n)) for n in range(lo, hi))
    for fn, col, lab, lx in [(cie_z, PAL["S"], "z̄(λ)", 445), (cie_y, PAL["M"], "ȳ(λ)", 558), (cie_x, PAL["L"], "x̄(λ)", 600)]:
        pts = [(xs(nm), oy - h * fn(nm) / peak) for nm in range(lo, hi + 1, 2)]
        s.append(f'<polyline points="{_poly(pts)}" fill="none" stroke="{col}" stroke-width="3.2"/>')
        s.append(f'<text x="{xs(lx):.0f}" y="{oy - h*fn(lx)/peak - 12:.0f}" text-anchor="middle" font-size="{FST}" font-weight="800" fill="{col}">{lab}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_chromaticity(t):
    W, H = 760, 640
    ox, oy = 90, 580          # origin (x=0,y=0)
    sx, sy = 760, 640
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    X0, Y0 = 0.74, 0.85
    PX = lambda x: ox + (sx - 130) * (x / X0)
    PY = lambda y: oy - (sy - 110) * (y / Y0)
    # axes
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{PX(X0):.0f}" y2="{oy}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{PY(Y0):.0f}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    for v in (0.2, 0.4, 0.6):
        s.append(f'<text x="{PX(v):.0f}" y="{oy+26}" text-anchor="middle" font-size="{FSA}" fill="{PAL["mute"]}">{v}</text>')
        s.append(f'<text x="{ox-12}" y="{PY(v)+5:.0f}" text-anchor="end" font-size="{FSA}" fill="{PAL["mute"]}">{v}</text>')
    s.append(f'<text x="{PX(X0):.0f}" y="{oy+26}" text-anchor="end" font-size="{FS}" fill="{PAL["soft"]}">x</text>')
    s.append(f'<text x="{ox-12}" y="{PY(Y0)+14:.0f}" font-size="{FS}" fill="{PAL["soft"]}">y</text>')
    # spectral locus boundary (colored by wavelength)
    locus = [(nm,) + chromaticity(nm) for nm in range(380, 701, 2)]
    pts = [(PX(x), PY(y)) for nm, x, y in locus]
    # filled interior (very light) using locus + purple line back to start
    path = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + " Z"
    s.append(f'<path d="{path}" fill="#f3f1ec" stroke="none"/>')
    # colored boundary segments
    for i in range(len(pts) - 1):
        nm = locus[i][0]
        s.append(f'<line x1="{pts[i][0]:.1f}" y1="{pts[i][1]:.1f}" x2="{pts[i+1][0]:.1f}" y2="{pts[i+1][1]:.1f}" stroke="{wl_to_rgb(nm)}" stroke-width="4"/>')
    # purple line (close)
    s.append(f'<line x1="{pts[-1][0]:.1f}" y1="{pts[-1][1]:.1f}" x2="{pts[0][0]:.1f}" y2="{pts[0][1]:.1f}" stroke="#8a2be2" stroke-width="3.5"/>')
    # wavelength labels
    for nm in (460, 480, 500, 520, 540, 560, 580, 600, 640):
        x, y = chromaticity(nm)
        s.append(f'<text x="{PX(x)+(8 if x>0.2 else -8):.0f}" y="{PY(y)-4:.0f}" font-size="13" fill="{PAL["soft"]}">{nm}</text>')
    # sRGB triangle + white point
    R, G, B = (0.64, 0.33), (0.30, 0.60), (0.15, 0.06)
    tri = f'{PX(R[0]):.0f},{PY(R[1]):.0f} {PX(G[0]):.0f},{PY(G[1]):.0f} {PX(B[0]):.0f},{PY(B[1]):.0f}'
    s.append(f'<polygon points="{tri}" fill="none" stroke="{PAL["ink"]}" stroke-width="2" stroke-dasharray="6 4"/>')
    s.append(f'<text x="{PX(R[0])+8:.0f}" y="{PY(R[1]):.0f}" font-size="13" fill="{PAL["ink"]}">{t["srgb"]}</text>')
    wx, wy = 0.3127, 0.329
    s.append(f'<circle cx="{PX(wx):.0f}" cy="{PY(wy):.0f}" r="5" fill="#222"/>')
    s.append(f'<text x="{PX(wx)+9:.0f}" y="{PY(wy)+4:.0f}" font-size="13" fill="{PAL["ink"]}">{t["white"]}</text>')
    s.append(f'<text x="{PX(0.18):.0f}" y="{PY(0.72):.0f}" font-size="{FS}" font-weight="700" fill="{PAL["soft"]}">{t["locus"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_macadam(t):
    W, H = 760, 600
    ox, oy = 90, 540
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    X0, Y0 = 0.74, 0.85
    PX = lambda x: ox + 560 * (x / X0)
    PY = lambda y: oy - 480 * (y / Y0)
    locus = [(nm,) + chromaticity(nm) for nm in range(380, 701, 3)]
    pts = [(PX(x), PY(y)) for nm, x, y in locus]
    path = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + " Z"
    s.append(f'<path d="{path}" fill="#f5f3ee" stroke="{PAL["line"]}" stroke-width="1.5"/>')
    # schematic ellipses (×10 exaggerated): green big, blue small
    ell = [(0.30, 0.55, 60, 26, 25), (0.20, 0.40, 30, 16, -10), (0.16, 0.20, 18, 12, 60),
           (0.45, 0.45, 44, 22, -20), (0.55, 0.40, 40, 18, -35), (0.34, 0.36, 30, 18, 10),
           (0.25, 0.62, 50, 24, 35), (0.42, 0.30, 26, 14, 0)]
    for x, y, rx, ry, ang in ell:
        s.append(f'<ellipse cx="{PX(x):.0f}" cy="{PY(y):.0f}" rx="{rx}" ry="{ry}" transform="rotate({ang} {PX(x):.0f} {PY(y):.0f})" fill="none" stroke="{PAL["ink"]}" stroke-width="2"/>')
    s.append(f'<text x="{PX(0.30):.0f}" y="{PY(0.55)+4:.0f}" text-anchor="middle" font-size="{FSA}" fill="{PAL["M"]}">{t["green"]}</text>')
    s.append(f'<text x="{PX(0.16):.0f}" y="{PY(0.20)+4:.0f}" text-anchor="middle" font-size="{FSA}" fill="{PAL["S"]}">{t["blue"]}</text>')
    s.append(f'<text x="{ox+10}" y="40" font-size="{FS}" fill="{PAL["soft"]}">{t["note"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_lab(t):
    W, H = 760, 520
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    cx, cy = 380, 300
    # L* vertical bar (black->white)
    s.append('<defs><linearGradient id="lstar" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#111"/><stop offset="1" stop-color="#fff"/></linearGradient></defs>')
    s.append(f'<rect x="{cx-18}" y="60" width="36" height="300" fill="url(#lstar)" stroke="{PAL["line"]}"/>')
    s.append(f'<text x="{cx}" y="44" text-anchor="middle" font-size="{FST}" font-weight="800" fill="{PAL["ink"]}">L* {t["light"]}</text>')
    s.append(f'<text x="{cx+28}" y="72" font-size="{FSA}" fill="{PAL["soft"]}">100</text>')
    s.append(f'<text x="{cx+28}" y="358" font-size="{FSA}" fill="{PAL["soft"]}">0</text>')
    # a*-b* plane (isometric-ish), centered below
    px, py = 380, 410
    L = 150
    s.append(f'<line x1="{px-L}" y1="{py}" x2="{px+L}" y2="{py}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    s.append(f'<line x1="{px}" y1="{py-90}" x2="{px}" y2="{py+90}" stroke="{PAL["axis"]}" stroke-width="1.5"/>')
    s.append(f'<rect x="{px+L-46}" y="{py-12}" width="44" height="24" rx="5" fill="{PAL["L"]}"/><text x="{px+L+8}" y="{py+5}" font-size="{FS}" font-weight="700" fill="{PAL["L"]}">+a* {t["red"]}</text>')
    s.append(f'<rect x="{px-L+2}" y="{py-12}" width="44" height="24" rx="5" fill="{PAL["M"]}"/><text x="{px-L-8}" y="{py+5}" text-anchor="end" font-size="{FS}" font-weight="700" fill="{PAL["M"]}">−a* {t["green"]}</text>')
    s.append(f'<rect x="{px-22}" y="{py-90}" width="44" height="22" rx="5" fill="{PAL["accent"] if "accent" in PAL else "#d6b400"}"/><text x="{px}" y="{py-98}" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["gold"]}">+b* {t["yellow"]}</text>')
    s.append(f'<rect x="{px-22}" y="{py+68}" width="44" height="22" rx="5" fill="{PAL["S"]}"/><text x="{px}" y="{py+108}" text-anchor="middle" font-size="{FS}" font-weight="700" fill="{PAL["S"]}">−b* {t["blue"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_de(t):
    W, H = 900, 340
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    # two swatches + euclidean line
    s.append(f'<rect x="60" y="80" width="90" height="90" rx="10" fill="#3a6ea5"/><rect x="220" y="120" width="90" height="90" rx="10" fill="#4a86c5"/>')
    s.append(f'<line x1="150" y1="125" x2="220" y2="165" stroke="{PAL["ink"]}" stroke-width="2.5" stroke-dasharray="5 4"/>')
    s.append(f'<text x="185" y="120" text-anchor="middle" font-size="{FST}" font-weight="800" fill="{PAL["ink"]}">ΔE</text>')
    s.append(f'<text x="185" y="250" text-anchor="middle" font-size="{FS}" fill="{PAL["soft"]}">{t["e76"]}</text>')
    # arrow to DE2000 terms
    s.append(f'<text x="420" y="60" font-size="{FST}" font-weight="800" fill="{PAL["ink"]}">CIEDE2000</text>')
    terms = [(t["sl"], PAL["ink"]), (t["sc"], PAL["L"]), (t["sh"], PAL["M"]), (t["rt"], PAL["S"])]
    for i, (lab, col) in enumerate(terms):
        x = 420 + (i % 2) * 240
        y = 100 + (i // 2) * 90
        s.append(f'<rect x="{x}" y="{y}" width="220" height="64" rx="10" fill="{PAL["panel"]}" stroke="{col}" stroke-width="1.5"/>')
        for j, ln in enumerate(lab.split("|")):
            s.append(f'<text x="{x+14}" y="{y+26+j*22}" font-size="{FS}" fill="{PAL["ink"]}">{ln}</text>')
    s.append(f'<text x="660" y="300" text-anchor="middle" font-size="{FS}" fill="{PAL["soft"]}">{t["goal"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def build_figures(lang):
    F = figure_labels(lang)
    return {
        "match": fig_match(F["match"]), "cmf_rgb": fig_cmf_rgb(F["cmf_rgb"]),
        "negative": fig_negative(F["negative"]), "xyz_cmf": fig_xyz_cmf(F["xyz_cmf"]),
        "chromaticity": fig_chromaticity(F["chromaticity"]), "macadam": fig_macadam(F["macadam"]),
        "lab": fig_lab(F["lab"]), "de": fig_de(F["de"]),
    }


# ---------------------------------------------------------------------------
# Figure labels per language
# ---------------------------------------------------------------------------
def figure_labels(lang):
    F = {}
    F["match"] = {
        "ko": dict(aria="색일치 실험", test="측정 단색광", mix="세 원색 혼합", knobs="세 기준광 손잡이", adjust="두 반쪽이 같아 보일 때까지 조절"),
        "en": dict(aria="Color matching experiment", test="test light", mix="3-primary mix", knobs="three primary knobs", adjust="adjust until both halves look identical"),
        "ja": dict(aria="等色実験", test="測定単色光", mix="三原色混合", knobs="三原色のつまみ", adjust="両半分が同じに見えるまで調整"),
        "zh": dict(aria="颜色匹配实验", test="待测单色光", mix="三原色混合", knobs="三原色旋钮", adjust="调到两半看起来相同"),
    }[lang]
    F["cmf_rgb"] = {
        "ko": dict(aria="CIE RGB 색일치함수", x="파장 (nm)", y="값", neg="음수 구간"),
        "en": dict(aria="CIE RGB color-matching functions", x="Wavelength (nm)", y="Value", neg="negative region"),
        "ja": dict(aria="CIE RGB等色関数", x="波長 (nm)", y="値", neg="負の区間"),
        "zh": dict(aria="CIE RGB颜色匹配函数", x="波长 (nm)", y="值", neg="负值区间"),
    }[lang]
    F["negative"] = {
        "ko": dict(aria="음수가 나오는 이유", p_left="더해서는 안 됨", p_right="빼면 일치", test="청록", dull="섞을수록 탁해짐", eq="측정색 = G+B − R", arrow_neg="→ 빨강이 음수로 기록"),
        "en": dict(aria="Why it goes negative", p_left="adding fails", p_right="subtracting matches", test="cyan", dull="mixing only dulls it", eq="test = G+B − R", arrow_neg="→ red recorded as negative"),
        "ja": dict(aria="なぜ負になるか", p_left="足すと不可", p_right="引くと一致", test="シアン", dull="混ぜると濁る", eq="測定色 = G+B − R", arrow_neg="→ 赤が負として記録"),
        "zh": dict(aria="为何出现负值", p_left="相加不行", p_right="相减则匹配", test="青", dull="越混越浊", eq="待测 = G+B − R", arrow_neg="→ 红被记为负"),
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
    F["lab"] = {
        "ko": dict(aria="CIELAB 색공간", light="밝기", red="적", green="녹", yellow="황", blue="청"),
        "en": dict(aria="CIELAB color space", light="lightness", red="red", green="green", yellow="yellow", blue="blue"),
        "ja": dict(aria="CIELAB色空間", light="明るさ", red="赤", green="緑", yellow="黄", blue="青"),
        "zh": dict(aria="CIELAB色空间", light="亮度", red="红", green="绿", yellow="黄", blue="蓝"),
    }[lang]
    F["de"] = {
        "ko": dict(aria="색차 ΔE 진화", e76="ΔE76 = 단순 직선거리", sl="SL|밝기 가중", sc="SC|채도 가중", sh="SH|색상 가중", rt="RT|파랑 회전 보정", goal="목표: 한 숫자 = 체감 색차"),
        "en": dict(aria="Evolution of color difference", e76="ΔE76 = plain distance", sl="SL|lightness weight", sc="SC|chroma weight", sh="SH|hue weight", rt="RT|blue rotation", goal="goal: one number = perceived difference"),
        "ja": dict(aria="色差ΔEの進化", e76="ΔE76 = 単純距離", sl="SL|明度の重み", sc="SC|彩度の重み", sh="SH|色相の重み", rt="RT|青の回転補正", goal="目標: 一つの数 = 体感色差"),
        "zh": dict(aria="色差ΔE演进", e76="ΔE76 = 简单距离", sl="SL|明度权重", sc="SC|彩度权重", sh="SH|色相权重", rt="RT|蓝区旋转", goal="目标: 一个数 = 体感色差"),
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

    for i, sec in enumerate(c["secs"]):
        parts.append('<section>')
        parts.append(f'<h2>{sec["h2"]}</h2>')
        for p in sec["paras"]:
            parts.append(f'<p>{p}</p>')
        for fk in sec.get("fml", []):
            parts.append(f'<div class="formula">{FORMULAS[fk]}</div>')
        if sec.get("fig"):
            parts.append('<figure>')
            parts.append(f'<div class="fig-box">{figs[sec["fig"]]}</div>')
            parts.append(f'<figcaption><b>{c["fig_word"]} {i+1}.</b> {sec["cap"]}</figcaption>')
            parts.append('</figure>')
        parts.append('</section>')
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
