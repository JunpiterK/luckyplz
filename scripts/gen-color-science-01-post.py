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
        s.append(f'<text x="{x+bw/2:.1f}" y="{y0+bh+16}" text-anchor="middle" font-size="12" fill="{PAL["soft"]}">{lab}</text>')
    # wavelength annotation (long -> short)
    s.append(f'<text x="40" y="38" font-size="11" fill="{PAL["mute"]}">{t["long_wl"]} ←</text>')
    s.append(f'<text x="{W-40}" y="38" text-anchor="end" font-size="11" fill="{PAL["mute"]}">→ {t["short_wl"]}</text>')
    # expand connector from the visible band to the zoom bar
    vx = x0 + 3 * bw
    s.append(f'<path d="M{vx:.1f},{y0+bh} L120,{H-120} M{vx+bw-1:.1f},{y0+bh} L{W-120},{H-120}" stroke="{PAL["line"]}" stroke-width="1.2" fill="none"/>')
    # zoomed visible band 380..700 rainbow
    zx, zy, zw, zh = 120, H - 120, W - 240, 44
    s.append(f'<rect x="{zx}" y="{zy}" width="{zw}" height="{zh}" fill="url(#rain)" rx="4"/>')
    for nm in (400, 450, 500, 550, 600, 650, 700):
        px = zx + zw * (nm - 380) / (700 - 380)
        s.append(f'<line x1="{px:.1f}" y1="{zy+zh}" x2="{px:.1f}" y2="{zy+zh+6}" stroke="{PAL["axis"]}"/>')
        s.append(f'<text x="{px:.1f}" y="{zy+zh+20}" text-anchor="middle" font-size="11" fill="{PAL["soft"]}">{nm}</text>')
    s.append(f'<text x="{zx+zw/2:.1f}" y="{zy+zh+38}" text-anchor="middle" font-size="12" fill="{PAL["mute"]}">{t["nm"]}</text>')
    s.append(f'<text x="{zx+zw/2:.1f}" y="{zy-8}" text-anchor="middle" font-size="13" font-weight="700" fill="{PAL["ink"]}">{t["vis_full"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def _axes(s, ox, oy, w, h, xlabel, ylabel):
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{ox+w}" y2="{oy}" stroke="{PAL["axis"]}" stroke-width="1.3"/>')
    s.append(f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy-h}" stroke="{PAL["axis"]}" stroke-width="1.3"/>')
    s.append(f'<text x="{ox+w}" y="{oy+28}" text-anchor="end" font-size="12" fill="{PAL["soft"]}">{xlabel}</text>')
    s.append(f'<text x="{ox-8}" y="{oy-h-8}" font-size="12" fill="{PAL["soft"]}">{ylabel}</text>')


def fig_visible_window(t):
    """Figure 2 — why visible is visible: solar spectrum × atmospheric window."""
    W, H = 960, 420
    ox, oy, w, h = 70, 340, 820, 250
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    lo, hi = 300, 1100
    xs = lambda nm: ox + w * (nm - lo) / (hi - lo)
    # visible band shading
    s.append(f'<rect x="{xs(380):.1f}" y="{oy-h}" width="{xs(700)-xs(380):.1f}" height="{h}" fill="url(#rain2)" opacity="0.16"/>')
    s.append('<defs><linearGradient id="rain2" x1="0" x2="1">' +
             "".join(f'<stop offset="{i}%" stop-color="{wl_to_rgb(380+(700-380)*i/100)}"/>' for i in range(0, 101, 5)) +
             '</linearGradient></defs>')
    _axes(s, ox, oy, w, h, t["x"], t["y"])
    for nm in (300, 500, 700, 900, 1100):
        s.append(f'<text x="{xs(nm):.1f}" y="{oy+18}" text-anchor="middle" font-size="11" fill="{PAL["mute"]}">{nm}</text>')
    # solar curve (Planck 5800K, normalized)
    pts = []
    peak = max(planck_rel(nm) for nm in range(lo, hi, 5))
    for nm in range(lo, hi + 1, 5):
        y = oy - h * (planck_rel(nm) / peak)
        pts.append((xs(nm), y))
    s.append(f'<polyline points="{_poly(pts)}" fill="none" stroke="{PAL["gold"]}" stroke-width="2.6"/>')
    s.append(f'<text x="{xs(560):.1f}" y="{oy-h+22:.1f}" font-size="12.5" font-weight="700" fill="{PAL["gold"]}">{t["solar"]}</text>')
    # atmospheric transmission (schematic): UV blocked, visible+some NIR open, IR bands absorb
    def atm(nm):
        if nm < 320:
            return 0.05
        v = 0.95
        v *= 1 - 0.9 * math.exp(-((nm - 320) ** 2) / (2 * 18 ** 2))  # ozone edge
        for c, wd, d in [(720, 14, .5), (820, 16, .45), (940, 26, .8), (1130, 30, .7)]:
            v *= 1 - d * math.exp(-((nm - c) ** 2) / (2 * wd ** 2))
        return max(0.03, min(0.97, v))
    pts2 = [(xs(nm), oy - h * atm(nm)) for nm in range(lo, hi + 1, 4)]
    s.append(f'<polyline points="{_poly(pts2)}" fill="none" stroke="{PAL["S"]}" stroke-width="2.2" stroke-dasharray="1 0"/>')
    s.append(f'<text x="{xs(430):.1f}" y="{oy-h*0.92:.1f}" font-size="12.5" font-weight="700" fill="{PAL["S"]}">{t["atm"]}</text>')
    # visible band label
    s.append(f'<text x="{(xs(380)+xs(700))/2:.1f}" y="{oy-h-14}" text-anchor="middle" font-size="13" font-weight="800" fill="{PAL["ink"]}">{t["vis"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_eye(t):
    """Figure 3 — eye cross-section + retina layer zoom (rod vs cone)."""
    W, H = 960, 420
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    cx, cy, r = 250, 210, 150
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#f7fbfd" stroke="{PAL["line"]}" stroke-width="2"/>')
    # cornea / lens (front, left)
    s.append(f'<path d="M{cx-r},{cy} q-30,0 -30,-46 q0,-46 30,-46" fill="none" stroke="{PAL["soft"]}" stroke-width="0"/>')
    s.append(f'<ellipse cx="{cx-r+14}" cy="{cy}" rx="20" ry="54" fill="#cfeefb" stroke="{PAL["S"]}" stroke-width="1.6"/>')
    s.append(f'<text x="{cx-r-6}" y="{cy-66}" text-anchor="middle" font-size="12" fill="{PAL["soft"]}">{t["lens"]}</text>')
    # retina (back arc, right)
    s.append(f'<path d="M{cx},{cy-r+6} A{r-6},{r-6} 0 0 1 {cx},{cy+r-6}" fill="none" stroke="{PAL["L"]}" stroke-width="6" opacity="0.5"/>')
    s.append(f'<text x="{cx+r+6}" y="{cy-60}" font-size="12" fill="{PAL["L"]}">{t["retina"]}</text>')
    # fovea
    s.append(f'<circle cx="{cx+r-8}" cy="{cy}" r="6" fill="{PAL["gold"]}"/>')
    s.append(f'<text x="{cx+r-4}" y="{cy+26}" font-size="12" fill="{PAL["gold"]}">{t["fovea"]}</text>')
    # optic nerve
    s.append(f'<path d="M{cx+r-4},{cy+40} q40,26 70,20" stroke="{PAL["soft"]}" stroke-width="9" fill="none" opacity="0.6"/>')
    s.append(f'<text x="{cx+r+40}" y="{cy+78}" font-size="12" fill="{PAL["soft"]}">{t["nerve"]}</text>')
    # incoming light
    s.append(f'<line x1="40" y1="{cy-40}" x2="{cx-r+2}" y2="{cy-6}" stroke="{PAL["gold"]}" stroke-width="2" marker-end="url(#ah)"/>')
    s.append(f'<line x1="40" y1="{cy+40}" x2="{cx-r+2}" y2="{cy+6}" stroke="{PAL["gold"]}" stroke-width="2" marker-end="url(#ah)"/>')
    s.append(f'<defs><marker id="ah" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="{PAL["gold"]}"/></marker></defs>')
    s.append(f'<text x="44" y="{cy-50}" font-size="12" fill="{PAL["gold"]}">{t["light"]}</text>')
    # zoom panel: rod & cone
    px, py, pw, ph = 560, 70, 360, 290
    s.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="12" fill="{PAL["panel"]}" stroke="{PAL["line"]}"/>')
    s.append(f'<text x="{px+pw/2:.0f}" y="{py+26}" text-anchor="middle" font-size="13" font-weight="700" fill="{PAL["ink"]}">{t["zoom"]}</text>')
    # rod
    rx = px + 90
    s.append(f'<rect x="{rx-13}" y="{py+60}" width="26" height="90" rx="13" fill="#b9c6cd"/>')
    s.append(f'<rect x="{rx-9}" y="{py+150}" width="18" height="60" rx="6" fill="#cfd9de"/>')
    s.append(f'<text x="{rx}" y="{py+232}" text-anchor="middle" font-size="12.5" font-weight="700" fill="{PAL["soft"]}">{t["rod"]}</text>')
    s.append(f'<text x="{rx}" y="{py+250}" text-anchor="middle" font-size="10.5" fill="{PAL["mute"]}">{t["rod_sub"]}</text>')
    # cone
    cxx = px + 250
    s.append(f'<path d="M{cxx-16},{py+150} L{cxx+16},{py+150} L{cxx+8},{py+60} L{cxx-8},{py+60} Z" fill="#f2b8a6" stroke="{PAL["L"]}" stroke-width="1.2"/>')
    s.append(f'<rect x="{cxx-9}" y="{py+150}" width="18" height="60" rx="6" fill="#f6d2c7"/>')
    s.append(f'<text x="{cxx}" y="{py+232}" text-anchor="middle" font-size="12.5" font-weight="700" fill="{PAL["L"]}">{t["cone"]}</text>')
    s.append(f'<text x="{cxx}" y="{py+250}" text-anchor="middle" font-size="10.5" fill="{PAL["mute"]}">{t["cone_sub"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_lms(t):
    """Figure 5 — L/M/S cone spectral sensitivity (the key figure)."""
    W, H = 960, 430
    ox, oy, w, h = 70, 350, 820, 270
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    xs = lambda nm: ox + w * (nm - LMIN) / (LMAX - LMIN)
    # faint rainbow strip under axis
    s.append('<defs><linearGradient id="rain3" x1="0" x2="1">' +
             "".join(f'<stop offset="{i}%" stop-color="{wl_to_rgb(LMIN+(LMAX-LMIN)*i/100)}"/>' for i in range(0, 101, 5)) +
             '</linearGradient></defs>')
    s.append(f'<rect x="{ox}" y="{oy+6}" width="{w}" height="10" fill="url(#rain3)" opacity="0.9" rx="2"/>')
    _axes(s, ox, oy, w, h, t["x"], t["y"])
    for nm in range(400, 701, 50):
        s.append(f'<text x="{xs(nm):.1f}" y="{oy+34}" text-anchor="middle" font-size="11" fill="{PAL["mute"]}">{nm}</text>')
    curves = [("S", 420, 26, PAL["S"]), ("M", 534, 38, PAL["M"]), ("L", 564, 42, PAL["L"])]
    for name, mu, sig, col in curves:
        pts = [(xs(nm), oy - h * gauss(nm, mu, sig)) for nm in range(LMIN, LMAX + 1, 3)]
        s.append(f'<polyline points="{_poly(pts)}" fill="none" stroke="{col}" stroke-width="3"/>')
        s.append(f'<circle cx="{xs(mu):.1f}" cy="{oy-h:.1f}" r="3.5" fill="{col}"/>')
        s.append(f'<text x="{xs(mu):.1f}" y="{oy-h-10:.1f}" text-anchor="middle" font-size="13" font-weight="800" fill="{col}">{name}</text>')
        s.append(f'<text x="{xs(mu):.1f}" y="{oy-h-26:.1f}" text-anchor="middle" font-size="10.5" fill="{PAL["mute"]}">{mu}nm</text>')
    # legend
    lx, ly = ox + 30, oy - h + 14
    for i, (name, lab) in enumerate([("S", t["s"]), ("M", t["m"]), ("L", t["l"])]):
        col = dict(S=PAL["S"], M=PAL["M"], L=PAL["L"])[name]
        s.append(f'<rect x="{lx}" y="{ly+i*22}" width="13" height="13" rx="3" fill="{col}"/>')
        s.append(f'<text x="{lx+19}" y="{ly+11+i*22}" font-size="12" fill="{PAL["ink"]}">{lab}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_phototransduction(t):
    """Figure 6 — phototransduction cascade inside a cone outer segment."""
    W, H = 960, 360
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    steps = [t["p1"], t["p2"], t["p3"], t["p4"], t["p5"], t["p6"]]
    n = len(steps)
    bw, bh, gap = 132, 92, 18
    x0 = (W - (n * bw + (n - 1) * gap)) / 2
    y = 120
    cols = ["#fde9c8", "#f6d2c7", "#e7d6f3", "#cfe6d6", "#cfe0f5", "#d7dde1"]
    for i, (lab, col) in enumerate(zip(steps, cols)):
        x = x0 + i * (bw + gap)
        s.append(f'<rect x="{x:.1f}" y="{y}" width="{bw}" height="{bh}" rx="11" fill="{col}" stroke="{PAL["line"]}"/>')
        s.append(f'<text x="{x+14:.1f}" y="{y+22}" font-size="14" font-weight="800" fill="{PAL["soft"]}">{i+1}</text>')
        # wrap label into <= 3 lines
        words = lab.split(" ")
        lines, cur = [], ""
        for wd in words:
            if len(cur) + len(wd) > 13 and cur:
                lines.append(cur); cur = wd
            else:
                cur = (cur + " " + wd).strip()
        if cur:
            lines.append(cur)
        for j, ln in enumerate(lines[:3]):
            s.append(f'<text x="{x+bw/2:.1f}" y="{y+44+j*16}" text-anchor="middle" font-size="11.5" fill="{PAL["ink"]}">{ln}</text>')
        if i < n - 1:
            ax = x + bw + gap / 2
            s.append(f'<path d="M{x+bw:.1f},{y+bh/2} L{x+bw+gap:.1f},{y+bh/2}" stroke="{PAL["axis"]}" stroke-width="2" marker-end="url(#ah2)"/>')
    s.append(f'<defs><marker id="ah2" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="{PAL["axis"]}"/></marker></defs>')
    # photon in
    s.append(f'<text x="{x0:.1f}" y="{y-22}" font-size="13" fill="{PAL["gold"]}">☀ {t["photon"]}</text>')
    s.append(f'<line x1="{x0+10:.1f}" y1="{y-14}" x2="{x0+30:.1f}" y2="{y-2}" stroke="{PAL["gold"]}" stroke-width="2" marker-end="url(#ah2)"/>')
    # signal out caption
    s.append(f'<text x="{W/2:.0f}" y="{y+bh+44}" text-anchor="middle" font-size="12.5" fill="{PAL["soft"]}">{t["caption"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


def fig_pathway(t):
    """Figure 7 — retina -> optic nerve -> LGN -> V1, plus opponent recoding."""
    W, H = 960, 380
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{t["aria"]}">']
    nodes = [(110, t["n1"]), (320, t["n2"]), (520, t["n3"]), (730, t["n4"]), (880, t["n5"])]
    y = 110
    for i, (x, lab) in enumerate(nodes):
        s.append(f'<circle cx="{x}" cy="{y}" r="30" fill="{PAL["panel"]}" stroke="{PAL["S"]}" stroke-width="1.8"/>')
        for j, ln in enumerate(lab.split("|")):
            s.append(f'<text x="{x}" y="{y+5+(j-(len(lab.split("|"))-1)/2)*14:.0f}" text-anchor="middle" font-size="11" fill="{PAL["ink"]}">{ln}</text>')
        if i < len(nodes) - 1:
            nx = nodes[i + 1][0]
            s.append(f'<path d="M{x+30},{y} L{nx-30},{y}" stroke="{PAL["axis"]}" stroke-width="2" marker-end="url(#ah3)"/>')
    s.append(f'<defs><marker id="ah3" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="{PAL["axis"]}"/></marker></defs>')
    # opponent-process panel
    px, py, pw, ph = 150, 200, 660, 150
    s.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="12" fill="{PAL["panel"]}" stroke="{PAL["line"]}"/>')
    s.append(f'<text x="{px+pw/2:.0f}" y="{py+26}" text-anchor="middle" font-size="13" font-weight="700" fill="{PAL["ink"]}">{t["opp_title"]}</text>')
    chans = [(t["ch1"], PAL["L"], PAL["M"]), (t["ch2"], PAL["S"], PAL["gold"]), (t["ch3"], "#222", "#ddd")]
    cw = pw / 3
    for i, (lab, ca, cb) in enumerate(chans):
        cx = px + cw * i + cw / 2
        s.append(f'<rect x="{cx-46}" y="{py+52}" width="40" height="22" rx="5" fill="{ca}"/>')
        s.append(f'<rect x="{cx+6}" y="{py+52}" width="40" height="22" rx="5" fill="{cb}" stroke="{PAL["line"]}"/>')
        s.append(f'<text x="{cx}" y="{py+68}" text-anchor="middle" font-size="13" font-weight="800" fill="{PAL["soft"]}">↔</text>')
        s.append(f'<text x="{cx:.0f}" y="{py+98}" text-anchor="middle" font-size="11.5" fill="{PAL["ink"]}">{lab}</text>')
    s.append(f'<text x="{px+pw/2:.0f}" y="{py+ph-12}" text-anchor="middle" font-size="11" fill="{PAL["mute"]}">{t["opp_sub"]}</text>')
    s.append('</svg>')
    return "\n".join(s)


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
.fig-box svg{display:block;width:100%;height:auto;min-width:520px}
figcaption{font-size:13px;line-height:1.6;color:var(--mute);margin:11px 4px 0;padding-left:12px;border-left:3px solid var(--line)}
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
  .fig-box svg{min-width:0}
  figcaption{font-size:13.5px;max-width:760px;margin-left:auto;margin-right:auto}
  footer{max-width:760px}
}
@media(min-width:1040px){
  .fig-box{margin-left:-110px;margin-right:-110px}
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
