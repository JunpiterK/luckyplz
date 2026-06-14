# -*- coding: utf-8 -*-
"""Generate "The Science of Color — Part 1: How We See Color" (ko/en/ja/zh).

A hand-authored, figure-rich, flagship educational longform. Original prose +
original inline-SVG diagrams (computed from physics where curves are involved),
so it is legal, unique, high-quality content — the opposite signal to the
auto-daily posts. INDEXED + visible (not noindex).

Covers: electromagnetic waves -> why the visible band is visible -> the eye
(rods & cones) -> L/M/S cone phototransduction -> optic nerve -> cortex &
opponent process. Part 2 (CIE 1931 / CMF negatives / 1976 u'v' / CIELAB /
CIEDE2000) is a separate post.

Output:
  public/blog/color-science-01-how-we-see[/-en/-ja/-zh]/index.html
  public/assets/blog/color-science-01-<lang>.png   (OG)
  + posts.js entries (4) + sitemap.xml blocks (4)

Self-contained responsive CSS (wide figures on desktop, single column on
mobile). Does NOT use blog-desktop.css (handles its own desktop layout).
"""
import importlib.util
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
BLOG = PUBLIC / "blog"
ASSETS_BLOG = PUBLIC / "assets" / "blog"

SLUG = "color-science-01-how-we-see"
CATEGORY = "ai-tech"
DATE = "2026-06-14"
READ_MIN = 16
COVER_EMOJI = "🌈"

try:
    BUILD = json.loads((PUBLIC / "build.json").read_text(encoding="utf-8")).get("v", DATE)
except Exception:
    BUILD = DATE

LANG_SUFFIX = {"ko": "", "en": "-en", "ja": "-ja", "zh": "-zh"}
OG_LOCALE = {"ko": "ko_KR", "en": "en_US", "ja": "ja_JP", "zh": "zh_CN"}

# ---------------------------------------------------------------------------
# Math for the data-driven curves
# ---------------------------------------------------------------------------
LMIN, LMAX = 380, 720  # nm range drawn


def gauss(x, mu, sig):
    return math.exp(-((x - mu) ** 2) / (2 * sig * sig))


def planck_rel(lam_nm, T=5800.0):
    """Relative spectral radiance (Planck), arbitrary scale."""
    h = 6.626e-34; c = 3.0e8; k = 1.381e-23
    lam = lam_nm * 1e-9
    return (1.0 / lam ** 5) / (math.exp(h * c / (lam * k * T)) - 1.0)


def wl_to_rgb(wl):
    """Approximate visible wavelength (nm) -> sRGB hex for the rainbow gradient."""
    if wl < 380 or wl > 780:
        return "#000000"
    if wl < 440:
        r, g, b = -(wl - 440) / (440 - 380), 0.0, 1.0
    elif wl < 490:
        r, g, b = 0.0, (wl - 440) / (490 - 440), 1.0
    elif wl < 510:
        r, g, b = 0.0, 1.0, -(wl - 510) / (510 - 490)
    elif wl < 580:
        r, g, b = (wl - 510) / (580 - 510), 1.0, 0.0
    elif wl < 645:
        r, g, b = 1.0, -(wl - 645) / (645 - 580), 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0
    if wl > 700:
        f = 0.3 + 0.7 * (780 - wl) / (780 - 700)
    elif wl < 420:
        f = 0.3 + 0.7 * (wl - 380) / (420 - 380)
    else:
        f = 1.0
    g_ = 0.8
    to = lambda v: int(round(255 * (v * f) ** g_))
    return f"#{to(r):02x}{to(g):02x}{to(b):02x}"


def _poly(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


# Real cone fundamentals from the shared CIE data module (numpy/scipy, local-only).
# Same single-source data the Part 2 figures use — replaces the old gaussian guess.
_cie_spec = importlib.util.spec_from_file_location(
    "cie_data", ROOT / "scripts" / "color_science_cie_data.py")
_cie = importlib.util.module_from_spec(_cie_spec)
_cie_spec.loader.exec_module(_cie)
_wl, _L, _M, _S = _cie.cone_fundamentals()
_CONES = {int(w): (float(l), float(m), float(sv)) for w, l, m, sv in zip(_wl, _L, _M, _S)}


def cone_at(nm):
    """(L, M, S) sensitivity at nm (peak-normalized). 0 outside the table."""
    return _CONES.get(int(round(nm)), (0.0, 0.0, 0.0))


# ---------------------------------------------------------------------------
# SVG figures — geometry fixed, text labels injected per language
# Each returns an <svg> string. viewBox width 960 (scales responsively).
# ---------------------------------------------------------------------------
PAL = {
    "ink": "#22303a", "soft": "#5a6b76", "mute": "#8a9aa3",
    "line": "#dfe6ea", "card": "#ffffff", "L": "#e4572e", "M": "#3aa655",
    "S": "#2d6cdf", "axis": "#9fb0b8", "gold": "#c08a2d", "panel": "#f4f7f8",
}


def fig_em_spectrum(t):
    """Figure 1 — the electromagnetic spectrum with the visible band expanded."""
    W, H = 960, 360
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    # full-spectrum bar
    bands = [
        ("#3b4a8c", t["radio"]), ("#5a6fae", t["micro"]), ("#9a5db8", t["ir"]),
        ("rainbow", t["vis"]), ("#7a4bd0", t["uv"]), ("#4a7fb0", t["xray"]),
        ("#2a3a6a", t["gamma"]),
    ]
    x0, y0, bw, bh = 40, 50, (W - 80) / len(bands), 46
    defs = ['<defs><linearGradient id="rain" x1="0" x2="1">']
    for i in range(0, 101, 4):
        wl = 380 + (700 - 380) * i / 100
        defs.append(f'<stop offset="{i}%" stop-color="{wl_to_rgb(wl)}"/>')
    defs.append('</linearGradient></defs>')
    s += defs
    for i, (col, lab) in enumerate(bands):
        x = x0 + i * bw
        fill = "url(#rain)" if col == "rainbow" else col
        s.append(f'<rect x="{x:.1f}" y="{y0}" width="{bw-1:.1f}" height="{bh}" fill="{fill}"/>')
        s.append(f'<text x="{x+bw/2:.1f}" y="{y0+bh+18}" text-anchor="middle" font-size="14" font-weight="600" fill="{PAL["soft"]}">{lab}</text>')
    # wavelength annotation (long -> short)
    s.append(f'<text x="40" y="36" font-size="13" fill="{PAL["mute"]}">{t["long_wl"]} ←</text>')
    s.append(f'<text x="{W-40}" y="36" text-anchor="end" font-size="13" fill="{PAL["mute"]}">→ {t["short_wl"]}</text>')
    # expand connector from the visible band to the zoom bar
    vx = x0 + 3 * bw
    s.append(f'<path d="M{vx:.1f},{y0+bh} L120,{H-120} M{vx+bw-1:.1f},{y0+bh} L{W-120},{H-120}" stroke="{PAL["line"]}" stroke-width="1.2" fill="none"/>')
    # zoomed visible band 380..700 rainbow
    zx, zy, zw, zh = 120, H - 120, W - 240, 44
    s.append(f'<rect x="{zx}" y="{zy}" width="{zw}" height="{zh}" fill="url(#rain)" rx="4"/>')
    for nm in (400, 450, 500, 550, 600, 650, 700):
        px = zx + zw * (nm - 380) / (700 - 380)
        s.append(f'<line x1="{px:.1f}" y1="{zy+zh}" x2="{px:.1f}" y2="{zy+zh+6}" stroke="{PAL["axis"]}"/>')
        s.append(f'<text x="{px:.1f}" y="{zy+zh+22}" text-anchor="middle" font-size="13" fill="{PAL["soft"]}">{nm}</text>')
    s.append(f'<text x="{zx+zw/2:.1f}" y="{zy+zh+42}" text-anchor="middle" font-size="14" fill="{PAL["mute"]}">{t["nm"]}</text>')
    s.append(f'<text x="{zx+zw/2:.1f}" y="{zy-10}" text-anchor="middle" font-size="15.5" font-weight="800" fill="{PAL["ink"]}">{t["vis_full"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def _axes(s, ox, oy, w, h, xlabel, ylabel):
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{ox+w}" y2="{oy}" stroke="{PAL["axis"]}" stroke-width="1.4"/>')
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy-h}" stroke="{PAL["axis"]}" stroke-width="1.4"/>')
    s.append(f'<text x="{ox+w}" y="{oy+54}" text-anchor="end" font-size="15" font-weight="600" fill="{PAL["soft"]}">{xlabel}</text>')
    s.append(f'<text x="{ox-6}" y="{oy-h-10}" font-size="15" font-weight="600" fill="{PAL["soft"]}">{ylabel}</text>')


def fig_visible_window(t):
    """Figure 2 — why visible is visible: solar spectrum (filled) × atmospheric window."""
    W, H = 960, 460
    ox, oy, w, h = 78, 372, 812, 268
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    lo, hi = 300, 1100
    xs = lambda nm: ox + w * (nm - lo) / (hi - lo)
    defs = ['<defs>',
            '<linearGradient id="rain2" x1="0" x2="1">' +
            "".join(f'<stop offset="{i}%" stop-color="{wl_to_rgb(380+(700-380)*i/100)}"/>' for i in range(0, 101, 4)) +
            '</linearGradient>',
            f'<linearGradient id="solfill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="{PAL["gold"]}" stop-opacity="0.32"/><stop offset="100%" stop-color="{PAL["gold"]}" stop-opacity="0.03"/></linearGradient>',
            '</defs>']
    s += defs
    # visible band column highlight (rainbow, subtle)
    s.append(f'<rect x="{xs(380):.1f}" y="{oy-h}" width="{xs(700)-xs(380):.1f}" height="{h}" fill="url(#rain2)" opacity="0.18"/>')
    s.append(f'<rect x="{xs(380):.1f}" y="{oy-h}" width="{xs(700)-xs(380):.1f}" height="{h}" fill="none" stroke="{PAL["line"]}" stroke-dasharray="3 4"/>')
    # gridlines
    for v in (0.25, 0.5, 0.75, 1.0):
        s.append(f'<line x1="{ox}" y1="{oy-h*v:.1f}" x2="{ox+w}" y2="{oy-h*v:.1f}" stroke="{PAL["line"]}" stroke-width="1"/>')
    _axes(s, ox, oy, w, h, t["x"], t["y"])
    for nm in (300, 500, 700, 900, 1100):
        s.append(f'<line x1="{xs(nm):.1f}" y1="{oy}" x2="{xs(nm):.1f}" y2="{oy+5}" stroke="{PAL["axis"]}"/>')
        s.append(f'<text x="{xs(nm):.1f}" y="{oy+24}" text-anchor="middle" font-size="13" fill="{PAL["mute"]}">{nm}</text>')
    # solar curve (Planck 5800K, normalized) — filled area + line
    pts, peak = [], max(planck_rel(nm) for nm in range(lo, hi, 5))
    for nm in range(lo, hi + 1, 5):
        pts.append((xs(nm), oy - h * (planck_rel(nm) / peak)))
    area = f'M{pts[0][0]:.1f},{oy:.1f} ' + " ".join(f"L{x:.1f},{y:.1f}" for x, y in pts) + f' L{pts[-1][0]:.1f},{oy:.1f} Z'
    s.append(f'<path d="{area}" fill="url(#solfill)"/>')
    s.append(f'<polyline points="{_poly(pts)}" fill="none" stroke="{PAL["gold"]}" stroke-width="3" stroke-linejoin="round"/>')
    # atmospheric transmission (schematic): UV blocked, visible+some NIR open, IR bands absorb
    def atm(nm):
        if nm < 320:
            return 0.05
        v = 0.95
        v *= 1 - 0.9 * math.exp(-((nm - 320) ** 2) / (2 * 18 ** 2))
        for c, wd, d in [(720, 14, .5), (820, 16, .45), (940, 26, .8), (1130, 30, .7)]:
            v *= 1 - d * math.exp(-((nm - c) ** 2) / (2 * wd ** 2))
        return max(0.03, min(0.97, v))
    pts2 = [(xs(nm), oy - h * atm(nm)) for nm in range(lo, hi + 1, 4)]
    s.append(f'<polyline points="{_poly(pts2)}" fill="none" stroke="{PAL["S"]}" stroke-width="2.6" stroke-dasharray="7 4"/>')
    # legend (top-right)
    lx, ly = ox + w - 250, oy - h + 6
    s.append(f'<rect x="{lx-12}" y="{ly-12}" width="262" height="62" rx="9" fill="#ffffff" stroke="{PAL["line"]}" opacity="0.95"/>')
    s.append(f'<rect x="{lx}" y="{ly+2}" width="26" height="5" rx="2.5" fill="{PAL["gold"]}"/>')
    s.append(f'<text x="{lx+34}" y="{ly+8}" font-size="13.5" fill="{PAL["ink"]}">{t["solar"]}</text>')
    s.append(f'<line x1="{lx}" y1="{ly+28}" x2="{lx+26}" y2="{ly+28}" stroke="{PAL["S"]}" stroke-width="3" stroke-dasharray="7 4"/>')
    s.append(f'<text x="{lx+34}" y="{ly+33}" font-size="13.5" fill="{PAL["ink"]}">{t["atm"]}</text>')
    # visible band label
    s.append(f'<text x="{(xs(380)+xs(700))/2:.1f}" y="{oy-h-12}" text-anchor="middle" font-size="15.5" font-weight="800" fill="{PAL["ink"]}">{t["vis"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_eye(t):
    """Figure 3 — eye cross-section (light → lens → fovea) + retina layer zoom."""
    W, H = 960, 430
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    cx, cy, r = 250, 214, 152
    s.append('<defs>'
             '<radialGradient id="vit" cx="42%" cy="50%" r="64%"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#e9f3fa"/></radialGradient>'
             f'<linearGradient id="ret" x1="0" x2="1"><stop offset="0%" stop-color="{PAL["L"]}" stop-opacity="0.10"/><stop offset="100%" stop-color="{PAL["L"]}" stop-opacity="0.60"/></linearGradient>'
             f'<marker id="eah" markerWidth="11" markerHeight="11" refX="7.6" refY="3.4" orient="auto"><path d="M0,0 L8.6,3.4 L0,6.8 Z" fill="{PAL["gold"]}"/></marker>'
             '</defs>')
    # eyeball + retina (inner back arc)
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#vit)" stroke="{PAL["line"]}" stroke-width="2.5"/>')
    s.append(f'<path d="M{cx-6},{cy-r+10} A{r-10},{r-10} 0 0 1 {cx-6},{cy+r-10}" fill="none" stroke="url(#ret)" stroke-width="11"/>')
    s.append(f'<text x="{cx+r-78}" y="{cy-r+38}" font-size="14.5" font-weight="700" fill="{PAL["L"]}">{t["retina"]}</text>')
    # cornea (front bulge) + lens + iris hint
    s.append(f'<path d="M{cx-r+4},{cy-50} q-30,50 0,100" fill="#e0f2fc" stroke="{PAL["S"]}" stroke-width="1.8"/>')
    lensx = cx - r + 34
    s.append(f'<ellipse cx="{lensx}" cy="{cy}" rx="18" ry="48" fill="#cfeafb" stroke="{PAL["S"]}" stroke-width="1.8"/>')
    s.append(f'<line x1="{lensx}" y1="{cy-48}" x2="{lensx}" y2="{cy-68}" stroke="{PAL["soft"]}" stroke-width="3"/>')
    s.append(f'<line x1="{lensx}" y1="{cy+48}" x2="{lensx}" y2="{cy+68}" stroke="{PAL["soft"]}" stroke-width="3"/>')
    s.append(f'<text x="{lensx}" y="{cy+76}" text-anchor="middle" font-size="14" fill="{PAL["soft"]}">{t["lens"]}</text>')
    # fovea + optic nerve
    fx, fy = cx + r - 14, cy
    s.append(f'<circle cx="{fx}" cy="{fy}" r="6" fill="{PAL["gold"]}"/>')
    s.append(f'<text x="{fx+4}" y="{cy+28}" text-anchor="middle" font-size="14" fill="{PAL["gold"]}">{t["fovea"]}</text>')
    s.append(f'<path d="M{cx+r-8},{cy+44} q42,30 76,22" stroke="#cbb98f" stroke-width="12" fill="none" stroke-linecap="round"/>')
    s.append(f'<text x="{cx+r+42}" y="{cy+84}" font-size="14" fill="{PAL["soft"]}">{t["nerve"]}</text>')
    # light: 3 parallel rays refract through the lens and converge on the fovea
    s.append(f'<text x="34" y="{cy-74}" font-size="14" font-weight="600" fill="{PAL["gold"]}">{t["light"]}</text>')
    for dy in (-54, 0, 54):
        s.append(f'<line x1="34" y1="{cy+dy}" x2="{lensx-22}" y2="{cy+dy}" stroke="{PAL["gold"]}" stroke-width="2" opacity="0.9"/>')
        s.append(f'<line x1="{lensx+20}" y1="{cy+dy}" x2="{fx-7}" y2="{fy}" stroke="{PAL["gold"]}" stroke-width="2" opacity="0.85" marker-end="url(#eah)"/>')
    # zoom panel: rod vs cone
    px, py, pw, ph = 562, 60, 364, 308
    s.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="14" fill="{PAL["panel"]}" stroke="{PAL["line"]}"/>')
    s.append(f'<text x="{px+pw/2:.0f}" y="{py+28}" text-anchor="middle" font-size="15" font-weight="700" fill="{PAL["ink"]}">{t["zoom"]}</text>')
    rx = px + 98
    s.append(f'<rect x="{rx-13}" y="{py+64}" width="26" height="96" rx="13" fill="#aebcc4"/>')
    s.append(f'<rect x="{rx-9}" y="{py+158}" width="18" height="56" rx="6" fill="#c7d2d8"/>')
    s.append(f'<circle cx="{rx}" cy="{py+224}" r="9" fill="#bcc8ce"/>')
    s.append(f'<text x="{rx}" y="{py+258}" text-anchor="middle" font-size="14.5" font-weight="700" fill="{PAL["soft"]}">{t["rod"]}</text>')
    s.append(f'<text x="{rx}" y="{py+278}" text-anchor="middle" font-size="12" fill="{PAL["mute"]}">{t["rod_sub"]}</text>')
    cxx = px + 258
    s.append(f'<path d="M{cxx-17},{py+160} L{cxx+17},{py+160} L{cxx+8},{py+64} L{cxx-8},{py+64} Z" fill="#f0b2a0" stroke="{PAL["L"]}" stroke-width="1.3"/>')
    s.append(f'<rect x="{cxx-9}" y="{py+160}" width="18" height="54" rx="6" fill="#f4cabd"/>')
    s.append(f'<circle cx="{cxx}" cy="{py+224}" r="9" fill="#f0b8aa"/>')
    s.append(f'<text x="{cxx}" y="{py+258}" text-anchor="middle" font-size="14.5" font-weight="700" fill="{PAL["L"]}">{t["cone"]}</text>')
    s.append(f'<text x="{cxx}" y="{py+278}" text-anchor="middle" font-size="12" fill="{PAL["mute"]}">{t["cone_sub"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_lms(t):
    """Figure 5 — L/M/S cone spectral sensitivity, from real cone fundamentals.

    Hunt-Pointer-Estevez transform of the CIE 1931 CMF (the same verified data the
    Part 2 figures use), not a gaussian guess: true asymmetric shapes, the heavy
    L/M overlap, and the narrow blue-shifted S."""
    W, H = 960, 470
    ox, oy, w, h = 76, 392, 808, 300
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    xs = lambda nm: ox + w * (nm - LMIN) / (LMAX - LMIN)
    ys = lambda v: oy - h * v
    # defs: rainbow strip + per-cone vertical fade fills
    defs = ['<defs>', '<linearGradient id="rain3" x1="0" x2="1">' +
            "".join(f'<stop offset="{i}%" stop-color="{wl_to_rgb(LMIN+(LMAX-LMIN)*i/100)}"/>' for i in range(0, 101, 4)) +
            '</linearGradient>']
    for name, col in (("S", PAL["S"]), ("M", PAL["M"]), ("L", PAL["L"])):
        defs.append(f'<linearGradient id="cf{name}" x1="0" x2="0" y1="0" y2="1">'
                    f'<stop offset="0%" stop-color="{col}" stop-opacity="0.26"/>'
                    f'<stop offset="100%" stop-color="{col}" stop-opacity="0.015"/></linearGradient>')
    defs.append('</defs>')
    s += defs
    # horizontal gridlines + y ticks
    for v in (0.25, 0.5, 0.75, 1.0):
        s.append(f'<line x1="{ox}" y1="{ys(v):.1f}" x2="{ox+w}" y2="{ys(v):.1f}" stroke="{PAL["line"]}" stroke-width="1"/>')
        s.append(f'<text x="{ox-10}" y="{ys(v)+4:.1f}" text-anchor="end" font-size="13" fill="{PAL["mute"]}">{v:.2f}</text>')
    _axes(s, ox, oy, w, h, t["x"], t["y"])
    # wavelength rainbow strip + ticks under the axis
    s.append(f'<rect x="{ox}" y="{oy+7}" width="{w}" height="11" fill="url(#rain3)" rx="2"/>')
    for nm in range(400, 701, 50):
        s.append(f'<line x1="{xs(nm):.1f}" y1="{oy}" x2="{xs(nm):.1f}" y2="{oy+5}" stroke="{PAL["axis"]}"/>')
        s.append(f'<text x="{xs(nm):.1f}" y="{oy+38}" text-anchor="middle" font-size="13" fill="{PAL["mute"]}">{nm}</text>')
    # sample the real curves
    series, peak_v, peak_nm = {}, {"S": 0, "M": 0, "L": 0}, {"S": LMIN, "M": LMIN, "L": LMIN}
    for nm in range(LMIN, LMAX + 1, 2):
        l, m, sv = cone_at(nm)
        series[nm] = {"S": sv, "M": m, "L": l}
        for k, val in series[nm].items():
            if val > peak_v[k]:
                peak_v[k], peak_nm[k] = val, nm
    # filled areas first, then strokes on top (S, M, L so L sits frontmost)
    for name, col in (("S", PAL["S"]), ("M", PAL["M"]), ("L", PAL["L"])):
        pts = [(xs(nm), ys(series[nm][name])) for nm in range(LMIN, LMAX + 1, 2)]
        area = f'M{pts[0][0]:.1f},{oy:.1f} ' + " ".join(f"L{x:.1f},{y:.1f}" for x, y in pts) + f' L{pts[-1][0]:.1f},{oy:.1f} Z'
        s.append(f'<path d="{area}" fill="url(#cf{name})"/>')
        s.append(f'<polyline points="{_poly(pts)}" fill="none" stroke="{col}" stroke-width="3.2" stroke-linejoin="round"/>')
    # peak markers + bold labels
    for name, col in (("S", PAL["S"]), ("M", PAL["M"]), ("L", PAL["L"])):
        px, py = xs(peak_nm[name]), ys(peak_v[name])
        s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.2" fill="{col}" stroke="#fff" stroke-width="1.6"/>')
        s.append(f'<text x="{px:.1f}" y="{py-13:.1f}" text-anchor="middle" font-size="16" font-weight="800" fill="{col}">{name}</text>')
        s.append(f'<text x="{px:.1f}" y="{py+(22 if name=="S" else -30):.1f}" text-anchor="middle" font-size="12.5" fill="{PAL["mute"]}">≈{peak_nm[name]}nm</text>')
    # legend (top-right, away from the peaks)
    lx, ly = ox + w - 250, ys(1.0) + 4
    for i, (name, lab) in enumerate([("L", t["l"]), ("M", t["m"]), ("S", t["s"])]):
        col = dict(S=PAL["S"], M=PAL["M"], L=PAL["L"])[name]
        s.append(f'<rect x="{lx}" y="{ly+i*25}" width="26" height="5.5" rx="2.5" fill="{col}"/>')
        s.append(f'<text x="{lx+34}" y="{ly+9+i*25}" font-size="14" fill="{PAL["ink"]}">{lab}</text>')
    s.append('</svg>')
    return "\n".join(s)


# Process flows (fig 5 & 6) are responsive HTML, not SVG: a row of icon cards on
# desktop that reflows to a top-to-bottom stack with larger text on phones.
# Icons are hand-drawn inline SVG line-art of the actual structure at each step
# (chromophore, GPCR, ion channel, cone cell, ganglion neuron, optic chiasm,
# LGN, V1) — not stock emoji. They inherit the step's accent via currentColor.
_FLOW_ACCENT = [PAL["S"], PAL["gold"], PAL["M"], PAL["L"], "#8a5cd0", "#2f8f9d"]


def _icon(inner):
    return ('<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.2" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + inner + '</svg>')


# phototransduction cascade — molecular line-art
_PT_ICONS = [
    # 1 11-cis retinal bound in opsin: protein pocket + kinked chromophore
    _icon('<circle cx="24" cy="24" r="14"/><polyline points="15,27 20,19 25,27 30,19 33,23"/>'),
    # 2 photon absorbed: light burst
    _icon('<circle cx="24" cy="24" r="6.5"/>'
          '<line x1="24" y1="5" x2="24" y2="11"/><line x1="24" y1="37" x2="24" y2="43"/>'
          '<line x1="5" y1="24" x2="11" y2="24"/><line x1="37" y1="24" x2="43" y2="24"/>'
          '<line x1="11" y1="11" x2="15" y2="15"/><line x1="33" y1="33" x2="37" y2="37"/>'
          '<line x1="37" y1="11" x2="33" y2="15"/><line x1="15" y1="33" x2="11" y2="37"/>'),
    # 3 opsin activated: 7-TM receptor crossing the bilayer + activation spark
    _icon('<line x1="5" y1="17" x2="43" y2="17"/><line x1="5" y1="31" x2="43" y2="31"/>'
          '<rect x="17" y="12" width="11" height="24" rx="5.5"/>'
          '<path d="M36,8 l1.3,3.4 3.4,1.3 -3.4,1.3 -1.3,3.4 -1.3,-3.4 -3.4,-1.3 3.4,-1.3 z"/>'),
    # 4 transducin -> PDE: two coupled proteins
    _icon('<circle cx="17" cy="24" r="8"/><circle cx="31" cy="24" r="8"/>'
          '<circle cx="17" cy="24" r="1.6" fill="currentColor"/><circle cx="31" cy="24" r="1.6" fill="currentColor"/>'),
    # 5 cGMP falls sharply: downward trend + thinning molecules
    _icon('<line x1="24" y1="9" x2="24" y2="34"/><polyline points="17,27 24,36 31,27"/>'
          '<circle cx="12" cy="12" r="2" fill="currentColor"/><circle cx="36" cy="12" r="2" fill="currentColor"/>'
          '<circle cx="12" cy="22" r="2" fill="currentColor"/>'),
    # 6 CNG channels close -> hyperpolarization: pinched membrane channel
    _icon('<line x1="5" y1="14" x2="43" y2="14"/><line x1="5" y1="34" x2="43" y2="34"/>'
          '<path d="M19,14 q6,10 0,20"/><path d="M29,14 q-6,10 0,20"/>'
          '<line x1="20.5" y1="24" x2="27.5" y2="24"/>'),
]

# visual pathway — anatomical line-art
_PATH_ICONS = [
    # 1 photoreceptor (cone): tapered cell with outer-segment discs
    _icon('<path d="M19,42 L19,23 L24,8 L29,23 L29,42"/>'
          '<line x1="20.5" y1="14" x2="27.5" y2="14"/><line x1="19.8" y1="18" x2="28.2" y2="18"/>'
          '<line x1="19" y1="22" x2="29" y2="22"/>'),
    # 2 bipolar & ganglion cell: soma + dendrites up + axon down
    _icon('<circle cx="24" cy="23" r="6"/>'
          '<path d="M24,17 L24,9"/><path d="M21,18 L15,10"/><path d="M27,18 L33,10"/>'
          '<path d="M24,29 L24,41"/><path d="M24,41 L20,44"/><path d="M24,41 L28,44"/>'),
    # 3 optic chiasm: two nerve bundles crossing in an X
    _icon('<path d="M9,9 C19,19 29,29 39,39" stroke-width="2.8"/>'
          '<path d="M39,9 C29,19 19,29 9,39" stroke-width="2.8"/>'),
    # 4 LGN: layered kidney-shaped relay nucleus
    _icon('<path d="M18,11 C9,13 8,31 17,36 C27,41 37,33 34,23 C37,13 27,9 18,11 Z"/>'
          '<path d="M14,19 C21,17 28,18 31,21"/><path d="M13,25 C21,23 29,24 32,27"/>'
          '<path d="M15,31 C21,29 28,30 30,32"/>'),
    # 5 V1 visual cortex: brain profile + occipital stripes
    _icon('<path d="M13,29 C9,25 11,18 18,17 C21,11 31,12 33,18 C40,18 41,27 35,29 '
          'C36,34 28,35 25,31 C20,34 14,33 13,29 Z"/>'
          '<path d="M31,21 q4,4 1,9"/><path d="M34,20.5 q4,5 1,11"/>'),
]


def _flow(steps, icons):
    cards = []
    for i, (lab, ic) in enumerate(zip(steps, icons)):
        c = _FLOW_ACCENT[i % len(_FLOW_ACCENT)]
        txt = lab.replace("|", " ")
        cards.append(
            f'<div class="step" style="--c:{c}">'
            f'<span class="step-no">{i+1}</span>'
            f'<span class="step-ic">{ic}</span>'
            f'<span class="step-tx">{txt}</span></div>')
        if i < len(steps) - 1:
            cards.append('<span class="flow-arrow" aria-hidden="true">&#8594;</span>')
    return '<div class="flow">' + "".join(cards) + '</div>'


def fig_phototransduction(t):
    """Figure 5 — phototransduction cascade (responsive icon flow)."""
    steps = [t["p1"], t["p2"], t["p3"], t["p4"], t["p5"], t["p6"]]
    flow = _flow(steps, _PT_ICONS)
    note = (f'<p class="flow-note"><span class="flow-photon">&#9728; {t["photon"]}</span> &middot; {t["caption"]}</p>')
    return f'<div class="proc" role="img" aria-label="{t["aria"]}">{flow}{note}</div>'


def fig_pathway(t):
    """Figure 6 — visual pathway (responsive icon flow) + opponent recoding."""
    nodes = [t["n1"], t["n2"], t["n3"], t["n4"], t["n5"]]
    flow = _flow(nodes, _PATH_ICONS)
    chips = [(t["ch1"], PAL["L"], PAL["M"]), (t["ch2"], PAL["S"], PAL["gold"]), (t["ch3"], "#2b3640", "#d2d9de")]
    chip_html = "".join(
        f'<span class="chip"><span class="sw" style="background:{a}"></span>'
        f'<span class="sw" style="background:{b}"></span>{lab}</span>' for lab, a, b in chips)
    opp = (f'<div class="opp"><div class="opp-title">{t["opp_title"]}</div>'
           f'<div class="opp-chips">{chip_html}</div>'
           f'<div class="opp-sub">{t["opp_sub"]}</div></div>')
    return f'<div class="proc" role="img" aria-label="{t["aria"]}">{flow}{opp}</div>'


# ---------------------------------------------------------------------------
# Figure label sets per language
# ---------------------------------------------------------------------------
def figure_labels(lang):
    F = {}
    F["em"] = {
        "ko": dict(aria="전자기파 스펙트럼", radio="전파", micro="마이크로파", ir="적외선", vis="가시광선", uv="자외선", xray="X선", gamma="감마선", long_wl="긴 파장 (낮은 에너지)", short_wl="짧은 파장 (높은 에너지)", nm="파장 (nm)", vis_full="가시광선 — 우리가 '색'으로 보는 좁은 띠"),
        "en": dict(aria="Electromagnetic spectrum", radio="Radio", micro="Microwave", ir="Infrared", vis="Visible", uv="UV", xray="X-ray", gamma="Gamma", long_wl="Long wavelength (low energy)", short_wl="Short wavelength (high energy)", nm="Wavelength (nm)", vis_full="Visible light — the narrow band we see as 'color'"),
        "ja": dict(aria="電磁波スペクトル", radio="電波", micro="マイクロ波", ir="赤外線", vis="可視光", uv="紫外線", xray="X線", gamma="ガンマ線", long_wl="長波長（低エネルギー）", short_wl="短波長（高エネルギー）", nm="波長 (nm)", vis_full="可視光 — 私たちが「色」として見る狭い帯"),
        "zh": dict(aria="电磁波谱", radio="无线电", micro="微波", ir="红外", vis="可见光", uv="紫外", xray="X射线", gamma="伽马射线", long_wl="长波长（低能量）", short_wl="短波长（高能量）", nm="波长 (nm)", vis_full="可见光 — 我们看作「颜色」的狭窄波段"),
    }[lang]
    F["win"] = {
        "ko": dict(aria="태양 복사와 대기 투과 창", x="파장 (nm)", y="상대 강도 / 투과율", solar="태양 복사 (≈5800K)", atm="대기·물의 투과율", vis="가시광선 창 380–700nm"),
        "en": dict(aria="Solar radiation and the atmospheric window", x="Wavelength (nm)", y="Relative intensity / transmission", solar="Solar radiation (≈5800K)", atm="Atmosphere & water transmission", vis="The visible window 380–700nm"),
        "ja": dict(aria="太陽放射と大気の窓", x="波長 (nm)", y="相対強度 / 透過率", solar="太陽放射 (≈5800K)", atm="大気・水の透過率", vis="可視光の窓 380–700nm"),
        "zh": dict(aria="太阳辐射与大气窗口", x="波长 (nm)", y="相对强度 / 透过率", solar="太阳辐射 (≈5800K)", atm="大气与水的透过率", vis="可见光窗口 380–700nm"),
    }[lang]
    F["eye"] = {
        "ko": dict(aria="눈의 단면과 망막 확대", lens="수정체", retina="망막", fovea="중심와", nerve="시신경", light="빛", zoom="망막의 두 광수용체", rod="간상세포", rod_sub="명암·야간시 (약 1.2억 개)", cone="원추세포", cone_sub="색·주간시 (약 600만 개)"),
        "en": dict(aria="Eye cross-section and retina zoom", lens="Lens", retina="Retina", fovea="Fovea", nerve="Optic nerve", light="Light", zoom="Two photoreceptors of the retina", rod="Rod", rod_sub="brightness / night (~120M)", cone="Cone", cone_sub="color / day (~6M)"),
        "ja": dict(aria="眼の断面と網膜の拡大", lens="水晶体", retina="網膜", fovea="中心窩", nerve="視神経", light="光", zoom="網膜の2つの光受容体", rod="桿体細胞", rod_sub="明暗・暗所視（約1.2億個）", cone="錐体細胞", cone_sub="色・明所視（約600万個）"),
        "zh": dict(aria="眼睛剖面与视网膜放大", lens="晶状体", retina="视网膜", fovea="中央凹", nerve="视神经", light="光", zoom="视网膜的两种感光细胞", rod="视杆细胞", rod_sub="明暗·夜视（约1.2亿个）", cone="视锥细胞", cone_sub="颜色·昼视（约600万个）"),
    }[lang]
    F["lms"] = {
        "ko": dict(aria="L M S 원추세포 분광 감도", x="파장 (nm)", y="상대 감도", s="S — 단파장 (청색 계열)", m="M — 중파장 (녹색 계열)", l="L — 장파장 (적색 계열)"),
        "en": dict(aria="L M S cone spectral sensitivity", x="Wavelength (nm)", y="Relative sensitivity", s="S — short (bluish)", m="M — medium (greenish)", l="L — long (reddish)"),
        "ja": dict(aria="L M S 錐体の分光感度", x="波長 (nm)", y="相対感度", s="S — 短波長（青系）", m="M — 中波長（緑系）", l="L — 長波長（赤系）"),
        "zh": dict(aria="L M S 视锥细胞光谱灵敏度", x="波长 (nm)", y="相对灵敏度", s="S — 短波（蓝系）", m="M — 中波（绿系）", l="L — 长波（红系）"),
    }[lang]
    F["pt"] = {
        "ko": dict(aria="광전변환 캐스케이드", photon="광자 1개", p1="옵신 속 11-시스 레티날", p2="광자 흡수 → 올-트랜스로 이성질화", p3="옵신 활성화 (메타로돕신)", p4="트랜스듀신 → PDE 활성화", p5="cGMP 농도 급감", p6="CNG 채널 닫힘 → 과분극 (신호)", caption="빛이 '꺼짐'을 만든다 — 어둠 신호가 줄며 전기 신호가 발생한다"),
        "en": dict(aria="Phototransduction cascade", photon="1 photon", p1="11-cis retinal in opsin", p2="photon absorbed → isomerizes to all-trans", p3="opsin activated (metarhodopsin)", p4="transducin → PDE activated", p5="cGMP level falls sharply", p6="CNG channels close → hyperpolarization (signal)", caption="Light creates an 'off': the dark current drops, and that change is the signal"),
        "ja": dict(aria="光伝達カスケード", photon="光子1個", p1="オプシン内の11-シスレチナール", p2="光子吸収 → オールトランスへ異性化", p3="オプシン活性化（メタロドプシン）", p4="トランスデューシン → PDE活性化", p5="cGMP濃度が急減", p6="CNGチャネル閉鎖 → 過分極（信号）", caption="光が「オフ」を作る：暗電流が減り、その変化が信号になる"),
        "zh": dict(aria="光转导级联", photon="1个光子", p1="视蛋白中的11-顺式视黄醛", p2="吸收光子 → 异构化为全反式", p3="视蛋白激活（变视紫红质）", p4="转导蛋白 → 激活PDE", p5="cGMP浓度骤降", p6="CNG通道关闭 → 超极化（信号）", caption="光制造「关闭」：暗电流下降，这一变化就是信号"),
    }[lang]
    F["path"] = {
        "ko": dict(aria="시각 경로와 반대색 처리", n1="광수용체", n2="양극·신경절|세포", n3="시신경|시교차", n4="외측슬상핵|(LGN)", n5="1차 시각|피질 V1", opp_title="반대색 처리 — 3채널로 재부호화", ch1="적 ↔ 녹 (L−M)", ch2="청 ↔ 황 (S vs L+M)", ch3="명 ↔ 암 (L+M)", opp_sub="원추 3종의 응답이 '차이'로 변환되어 색과 밝기가 분리된다"),
        "en": dict(aria="Visual pathway and opponent processing", n1="Photo-|receptor", n2="Bipolar &|ganglion", n3="Optic nerve|/ chiasm", n4="LGN|(thalamus)", n5="V1 visual|cortex", opp_title="Opponent process — recoded into 3 channels", ch1="Red ↔ Green (L−M)", ch2="Blue ↔ Yellow (S vs L+M)", ch3="Light ↔ Dark (L+M)", opp_sub="The 3 cone responses become 'differences', separating color from brightness"),
        "ja": dict(aria="視覚経路と反対色処理", n1="光受容体", n2="双極・|神経節", n3="視神経|/視交叉", n4="外側膝状体|(LGN)", n5="一次視覚|野 V1", opp_title="反対色処理 — 3チャネルに再符号化", ch1="赤 ↔ 緑 (L−M)", ch2="青 ↔ 黄 (S vs L+M)", ch3="明 ↔ 暗 (L+M)", opp_sub="3種の錐体応答が「差」に変換され、色と明るさが分離する"),
        "zh": dict(aria="视觉通路与对立色处理", n1="感光细胞", n2="双极·|神经节", n3="视神经|/视交叉", n4="外侧膝状体|(LGN)", n5="初级视觉|皮层 V1", opp_title="对立色处理 — 重新编码为3通道", ch1="红 ↔ 绿 (L−M)", ch2="蓝 ↔ 黄 (S vs L+M)", ch3="明 ↔ 暗 (L+M)", opp_sub="三种视锥的响应被转换为「差值」，将颜色与亮度分离"),
    }[lang]
    return F


def build_figures(lang):
    F = figure_labels(lang)
    return {
        "em": fig_em_spectrum(F["em"]),
        "win": fig_visible_window(F["win"]),
        "eye": fig_eye(F["eye"]),
        "lms": fig_lms(F["lms"]),
        "pt": fig_phototransduction(F["pt"]),
        "path": fig_pathway(F["path"]),
    }


# ---------------------------------------------------------------------------
# Content module (separate file, no shell-escaping pain)
# ---------------------------------------------------------------------------
_cs_spec = importlib.util.spec_from_file_location(
    "cs_content", ROOT / "scripts" / "color_science_01_content.py")
_cs = importlib.util.module_from_spec(_cs_spec)
_cs_spec.loader.exec_module(_cs)
content = _cs.content


# ---------------------------------------------------------------------------
# Self-contained responsive CSS (wide figures on desktop, 1-col on mobile)
# ---------------------------------------------------------------------------
CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#faf7f0;--card:#fff;--ink:#22303a;--soft:#516069;--mute:#8a9aa3;--line:#e7e0d3;--accent:#c08a2d;--rain:linear-gradient(90deg,#7a4bd0,#2d6cdf,#3aa655,#e8d23a,#e4572e)}
html{-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--ink);font-family:BODYFONT;line-height:1.8;-webkit-font-smoothing:antialiased;font-size:16.5px}
a{color:#2d6cdf;text-decoration:none}
.topbar{position:sticky;top:0;z-index:20;display:flex;justify-content:space-between;align-items:center;padding:11px 16px;background:rgba(250,247,240,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);font-size:12px;letter-spacing:.04em}
.topbar a{color:var(--soft);font-weight:600}
.wrap{max-width:720px;margin:0 auto;padding:0 18px 60px}
.hero{padding:34px 0 18px;border-bottom:1px solid var(--line);margin-bottom:26px}
.kicker{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:12px;font-weight:700;letter-spacing:.14em;color:var(--accent);text-transform:uppercase}
h1{font-size:30px;line-height:1.28;font-weight:800;margin:12px 0 10px;letter-spacing:-.01em}
.hero .sub{font-size:15.5px;color:var(--soft);line-height:1.6}
.lead{font-size:18px;line-height:1.85;color:#2c3a44;margin:0 0 30px;font-weight:500}
h2{font-size:21px;font-weight:800;margin:38px 0 14px;padding-top:8px;letter-spacing:-.01em;color:#1c2930}
section p{margin:0 0 16px}
strong{font-weight:700;color:#11507a}
figure{margin:24px 0 8px}
.fig-box{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 12px 10px;box-shadow:0 2px 16px rgba(34,48,58,.05);overflow-x:auto}
.fig-box>svg{display:block;width:100%;height:auto;min-width:520px}
figcaption{font-size:14.5px;line-height:1.65;color:var(--mute);margin:13px 4px 0;padding-left:13px;border-left:3px solid var(--line)}
figcaption b{color:var(--soft)}
.closing{margin:40px 0 0;padding:22px 20px;background:linear-gradient(180deg,rgba(192,138,45,.07),rgba(192,138,45,.02));border:1px solid rgba(192,138,45,.25);border-radius:14px}
.closing h2{margin:0 0 10px;font-size:18px;color:var(--accent)}
.closing p{margin:0;font-size:15px;color:#3a4750}
footer{max-width:720px;margin:30px auto 0;padding:18px 18px 40px;font-size:12.5px;line-height:1.7;color:var(--mute);border-top:1px solid var(--line)}
footer a{color:var(--soft);font-weight:600}
@media(min-width:900px){
  body{font-size:17px}
  .wrap{max-width:760px;padding:0 24px 80px}
  h1{font-size:38px}
  .lead{font-size:19.5px}
  h2{font-size:25px;margin-top:48px}
  /* figures break out wider than the text column */
  figure{margin:34px 0 10px}
  .fig-box{margin-left:calc((760px - 980px)/2);margin-right:calc((760px - 980px)/2);padding:20px 18px 12px}
  .fig-box>svg{min-width:0}
  figcaption{font-size:13.5px;max-width:760px;margin-left:auto;margin-right:auto}
  footer{max-width:760px}
}
@media(min-width:1040px){
  .fig-box{margin-left:-110px;margin-right:-110px}
}
/* responsive process flow (fig 5 & 6): horizontal cards on desktop,
   top-to-bottom stack with bigger text on phones */
.proc{padding:6px 2px 2px}
.flow{display:flex;flex-wrap:nowrap;align-items:stretch;justify-content:center;gap:7px}
.step{flex:1 1 0;min-width:0;background:#fff;border:1px solid var(--line);border-top:3px solid var(--c);border-radius:13px;padding:14px 10px 12px;display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center;box-shadow:0 3px 12px rgba(34,48,58,.06)}
.step-no{width:23px;height:23px;border-radius:50%;background:var(--c);color:#fff;font-size:13px;font-weight:800;display:flex;align-items:center;justify-content:center;flex:none}
.step-ic{color:var(--c);display:flex;align-items:center;justify-content:center;flex:none}
.step-ic svg{width:44px;height:44px;display:block}
.step-tx{font-size:14.5px;line-height:1.42;color:var(--ink);font-weight:500}
.flow-arrow{display:flex;align-items:center;color:var(--mute);font-size:24px;flex:none;font-weight:700}
.flow-note{font-size:14.5px;color:var(--soft);margin:16px 6px 2px;text-align:center;line-height:1.65}
.flow-photon{color:var(--accent);font-weight:700}
.opp{margin-top:18px;background:var(--panel,#f4f7f8);border:1px solid var(--line);border-radius:13px;padding:16px}
.opp-title{font-size:15px;font-weight:700;color:var(--ink);text-align:center;margin-bottom:13px}
.opp-chips{display:flex;flex-wrap:wrap;justify-content:center;gap:10px}
.chip{display:inline-flex;align-items:center;gap:7px;background:#fff;border:1px solid var(--line);border-radius:999px;padding:8px 15px;font-size:14px;font-weight:600;color:var(--ink)}
.chip .sw{width:15px;height:15px;border-radius:4px;display:inline-block;border:1px solid rgba(0,0,0,.08)}
.opp-sub{font-size:13px;color:var(--mute);text-align:center;margin-top:13px;line-height:1.6}
@media(max-width:680px){
  .flow{flex-direction:column;gap:0}
  .step{flex-direction:row;align-items:center;gap:15px;text-align:left;padding:15px 16px;border-top:1px solid var(--line);border-left:4px solid var(--c)}
  .step-ic svg{width:50px;height:50px}
  .step-tx{font-size:16.5px;flex:1}
  .flow-arrow{transform:rotate(90deg);justify-content:center;height:30px;font-size:26px}
  .opp-chips{flex-direction:column}
  .chip{justify-content:center;font-size:15.5px;padding:11px}
  .opp-title{font-size:16.5px}.opp-sub{font-size:14.5px}
}
"""

FONT = {
    "ko": ("'Pretendard','Noto Sans KR',sans-serif", "https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;700;800&family=JetBrains+Mono:wght@400;700&display=swap"),
    "en": ("'Inter',-apple-system,sans-serif", "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&family=JetBrains+Mono:wght@400;700&display=swap"),
    "ja": ("'Noto Sans JP','Pretendard',sans-serif", "https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;800&family=JetBrains+Mono:wght@400;700&display=swap"),
    "zh": ("'Noto Sans SC','Pretendard',sans-serif", "https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;800&family=JetBrains+Mono:wght@400;700&display=swap"),
}

HEAD = """<!DOCTYPE html>
<html lang="{{LANG}}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!--lp-build-check:start-->
<meta name="lp-build" content="{{BUILD}}">
<script>(function(){try{if(!/KAKAOTALK/i.test(navigator.userAgent||""))return;var K="lp_kko_out";try{if(sessionStorage.getItem(K))return;sessionStorage.setItem(K,"1");}catch(e){}location.href="kakaotalk://web/openExternal?url="+encodeURIComponent(location.href);}catch(e){}})();</script>
<script>(function(){var B="{{BUILD}}";try{fetch("/build.json?_="+Date.now(),{cache:"no-store"}).then(function(r){return r.ok?r.json():null}).then(function(d){if(!d||!d.v||d.v===B)return;var k="lp_build_"+B;try{if(sessionStorage.getItem(k))return;sessionStorage.setItem(k,"1");}catch(e){}var u=new URL(location.href);u.searchParams.set("_b",d.v);location.replace(u.toString());}).catch(function(){});}catch(e){}})();</script>
<!--lp-build-check:end-->
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<title>{{TITLE}} | Lucky Please</title>
<meta name="description" content="{{DESC}}">
<meta name="keywords" content="{{KEYWORDS}}">
<link rel="canonical" href="{{CANON}}">
<link rel="alternate" hreflang="ko" href="https://luckyplz.com/blog/color-science-01-how-we-see/">
<link rel="alternate" hreflang="en" href="https://luckyplz.com/blog/color-science-01-how-we-see-en/">
<link rel="alternate" hreflang="ja" href="https://luckyplz.com/blog/color-science-01-how-we-see-ja/">
<link rel="alternate" hreflang="zh" href="https://luckyplz.com/blog/color-science-01-how-we-see-zh/">
<link rel="alternate" hreflang="x-default" href="https://luckyplz.com/blog/color-science-01-how-we-see-en/">
<meta property="og:type" content="article">
<meta property="og:title" content="{{OG_TITLE}}">
<meta property="og:description" content="{{OG_DESC}}">
<meta property="og:url" content="{{CANON}}">
<meta property="og:image" content="{{OG_IMG}}">
<meta property="og:locale" content="{{OG_LOCALE}}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{OG_TITLE}}">
<meta name="twitter:description" content="{{OG_DESC}}">
<meta name="twitter:image" content="{{OG_IMG}}">
<script type="application/ld+json">{{JSONLD}}</script>
<script type="application/ld+json">{{JSONLD_CRUMB}}</script>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#faf7f0">
<link rel="apple-touch-icon" href="/assets/icon-192.png">
<link href="{{FONT_URL}}" rel="stylesheet">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5370817769801923" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NZDPE3H3DQ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-NZDPE3H3DQ');</script>
<style>{{CSS}}</style>
</head>
<body>
<div class="topbar"><a href="/blog/">← BLOG</a><a href="/">🏠 luckyplz.com</a></div>
<div class="wrap">
"""


def _esc(s):
    return (s or "").replace("&", "&amp;").replace('"', "&quot;")


def build_html(lang):
    c = content(lang)
    figs = build_figures(lang)
    suffix = LANG_SUFFIX[lang]
    canon = f"https://luckyplz.com/blog/{SLUG}{suffix}/"
    body_font, font_url = FONT[lang]
    og_img = f"https://luckyplz.com/assets/blog/{SLUG}-{lang}.png?v={BUILD}"

    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": c["title"], "description": c["desc"],
        "image": og_img, "datePublished": DATE, "dateModified": DATE,
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
    parts.append(f'<p class="lead">{c["lead"]}</p>')

    for i, sec in enumerate(c["secs"]):
        parts.append('<section>')
        parts.append(f'<h2>{sec["h2"]}</h2>')
        for p in sec["paras"]:
            parts.append(f'<p>{p}</p>')
        if sec.get("fig"):
            parts.append('<figure>')
            parts.append(f'<div class="fig-box">{figs[sec["fig"]]}</div>')
            parts.append(f'<figcaption><b>{c["fig_word"]} {i+1}.</b> {sec["cap"]}</figcaption>')
            parts.append('</figure>')
        parts.append('</section>')
        if i == 3:  # mid-article ad after section 4
            parts.append('<div data-lp-ad="blog" style="margin:30px 0;"></div>')

    parts.append(f'<div class="closing"><h2>{c["closing_h2"]}</h2><p>{c["closing"]}</p></div>')
    parts.append('</div>')  # .wrap

    # author bio (E-E-A-T) + footer
    parts.append('<!-- lp-author-bio --><div class="wrap" style="padding-top:0">')
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


# ---------------------------------------------------------------------------
# OG image (light theme, rainbow bar)
# ---------------------------------------------------------------------------
def make_og(lang):
    from PIL import Image, ImageDraw
    spec = importlib.util.spec_from_file_location("gdo", ROOT / "scripts" / "gen_daily_og.py")
    gdo = importlib.util.module_from_spec(spec); spec.loader.exec_module(gdo)
    f = gdo.load_font_for_lang
    c = content(lang)
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (250, 247, 240))
    d = ImageDraw.Draw(img)
    # rainbow bar
    cols = [(122, 75, 208), (45, 108, 223), (58, 166, 85), (232, 210, 58), (228, 87, 46), (200, 50, 40)]
    bw = W / len(cols)
    for i, col in enumerate(cols):
        d.rectangle([i * bw, 0, (i + 1) * bw, 12], fill=col)
    d.text((64, 70), c["kicker"], font=f(lang, 30, bold=True), fill=(192, 138, 45))
    # title (wrap)
    title = c["h1"]
    fz = 64 if len(title) < 16 else 52
    fnt = f(lang, fz, bold=True)
    words = title.split(" ")
    lines, cur = [], ""
    maxw = W - 128
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=fnt) > maxw and cur:
            lines.append(cur); cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    if len(lines) == 1 and len(title) > 10:  # CJK no spaces -> hard wrap
        s = title; half = len(s) // 2
        lines = [s[:half], s[half:]]
    y = 200
    for ln in lines[:3]:
        d.text((64, y), ln, font=fnt, fill=(28, 41, 48)); y += fz + 14
    d.text((64, 470), c["sub"][:46], font=f(lang, 27, bold=False), fill=(81, 96, 105))
    # spectrum strip motif bottom
    for i in range(380, 700, 4):
        x = 64 + (i - 380) / (700 - 380) * (W - 128)
        col = _wl_rgb255(i)
        d.rectangle([x, 540, x + 4, 568], fill=col)
    d.text((64, 582), "luckyplz.com", font=f("en", 24, bold=True), fill=(192, 138, 45))
    out = ASSETS_BLOG / f"{SLUG}-{lang}.png"
    img.save(out, "PNG", optimize=True)
    print(f"[og] {out.name} ({out.stat().st_size//1024}KB)")


def _wl_rgb255(wl):
    h = wl_to_rgb(wl)
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


# ---------------------------------------------------------------------------
# Site integration
# ---------------------------------------------------------------------------
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
    if idx == -1:
        raise SystemExit("BLOG_POSTS not found")
    if f"'{SLUG}'" in raw:
        print("[posts.js] already present, skipping")
        return
    tags = {"ko": ["색채과학", "시각", "디스플레이"], "en": ["Color Science", "Vision", "Display"],
            "ja": ["色彩科学", "視覚", "ディスプレイ"], "zh": ["色彩科学", "视觉", "显示"]}
    slug_map = {l: f"{SLUG}{LANG_SUFFIX[l]}" for l in ("ko", "en", "ja", "zh")}
    entries = []
    for lang in ("ko", "en", "ja", "zh"):
        c = content(lang)
        alts = {l: s for l, s in slug_map.items() if l != lang}
        alts_js = "{ " + ", ".join(f"{k}: '{v}'" for k, v in alts.items()) + " }"
        alt_legacy = slug_map["en"] if lang == "ko" else slug_map["ko"]
        entries.append(
            "{\n"
            f"        slug: '{slug_map[lang]}',\n"
            f"        lang: '{lang}',\n"
            f"        category: '{CATEGORY}',\n"
            f"        date: '{DATE}',\n"
            f"        readMinutes: {READ_MIN},\n"
            f"        coverEmoji: '{COVER_EMOJI}',\n"
            f"        tags: {json.dumps(tags[lang], ensure_ascii=False)},\n"
            f"        title: {json.dumps(c['h1'], ensure_ascii=False)},\n"
            f"        excerpt: {json.dumps(c['og_desc'], ensure_ascii=False)},\n"
            f"        alt: '{alt_legacy}',\n"
            f"        alts: {alts_js},\n"
            "    },")
    combined = "\n    ".join(entries)
    raw = raw[:idx + len(marker)] + "\n    " + combined + raw[idx + len(marker):]
    p.write_text(raw, encoding="utf-8")
    print("[posts.js] prepended 4 entries")


def update_sitemap():
    p = PUBLIC / "sitemap.xml"
    raw = p.read_text(encoding="utf-8")
    if f"{SLUG}/" in raw and f"{SLUG}-en/" in raw:
        print("[sitemap] already present, skipping")
        return
    base = "https://luckyplz.com/blog/"
    alts = {
        "ko": f"{base}{SLUG}/", "en": f"{base}{SLUG}-en/",
        "ja": f"{base}{SLUG}-ja/", "zh": f"{base}{SLUG}-zh/",
    }
    blocks = []
    for lang, url in alts.items():
        links = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{u}"/>'
            for l, u in alts.items())
        links += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{alts["en"]}"/>'
        blocks.append(
            f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{DATE}</lastmod>'
            f'\n    <changefreq>monthly</changefreq>\n    <priority>0.9</priority>{links}\n  </url>')
    ins = "\n" + "\n".join(blocks) + "\n"
    raw = raw.replace("</urlset>", ins + "</urlset>")
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
    print("[done] color-science-01")


if __name__ == "__main__":
    main()
