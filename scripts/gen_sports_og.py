"""Sports OG image generator (football / baseball daily auto-posts).

1200x630 themed card. Reuses the cross-platform (Windows + Ubuntu CI) font
resolution from gen_daily_og.py so headlines render in ko/ja/zh without tofu.

Public API:
    make_sports_og(out_path, *, sport, lang, label, headline, sub) -> None
"""
from __future__ import annotations
import importlib.util
from pathlib import Path

from PIL import Image, ImageDraw

# Reuse font helpers from gen_daily_og.py (hyphen-free sibling, importable).
_spec = importlib.util.spec_from_file_location(
    "gen_daily_og", Path(__file__).resolve().parent / "gen_daily_og.py")
_gdo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gdo)
load_font_for_lang = _gdo.load_font_for_lang

W, H = 1200, 630

THEMES = {
    "football": {
        "top": (8, 30, 20), "bot": (4, 16, 11),
        "accent": (127, 255, 178), "accent2": (255, 122, 89),
        "label_fallback": "FOOTBALL DAILY",
    },
    "baseball": {
        "top": (10, 16, 34), "bot": (5, 9, 20),
        "accent": (255, 209, 102), "accent2": (93, 193, 255),
        "label_fallback": "MLB DAILY",
    },
}


def _vgrad(top, bot):
    img = Image.new("RGB", (W, H), top)
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    return img


def _draw_football_motif(d: ImageDraw.ImageDraw, cx, cy, R, accent):
    # Soft halo + white ball with a central pentagon + thin ring.
    d.ellipse([cx - R - 26, cy - R - 26, cx + R + 26, cy + R + 26],
              outline=(accent[0], accent[1], accent[2]), width=2)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(238, 244, 250))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(20, 26, 34), width=4)
    import math
    pent = []
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        pent.append((cx + R * 0.42 * math.cos(a), cy + R * 0.42 * math.sin(a)))
    d.polygon(pent, fill=(18, 22, 28))
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        x2 = cx + R * 0.95 * math.cos(a)
        y2 = cy + R * 0.95 * math.sin(a)
        d.line([pent[i], (x2, y2)], fill=(120, 130, 140), width=3)


def _draw_baseball_motif(d: ImageDraw.ImageDraw, cx, cy, R, accent):
    d.ellipse([cx - R - 26, cy - R - 26, cx + R + 26, cy + R + 26],
              outline=(accent[0], accent[1], accent[2]), width=2)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(244, 240, 232))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(20, 26, 34), width=4)
    red = (200, 40, 56)
    # Two curved seams (left & right arcs) with stitch ticks.
    for side in (-1, 1):
        bbox = [cx + side * R * 0.30 - R, cy - R, cx + side * R * 0.30 + R, cy + R]
        start, end = (300, 60) if side == 1 else (120, 240)
        d.arc(bbox, start, end, fill=red, width=5)
    import math
    for side in (-1, 1):
        for k in range(-6, 7):
            ay = cy + (R * 0.78) * (k / 7.0)
            ax = cx + side * (R * 0.46) * (1 - (k / 8.0) ** 2)
            d.line([(ax - side * 7, ay - 3), (ax + side * 7, ay + 3)], fill=red, width=2)


def _wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    # Hard-wrap CJK runs (no spaces) that still overflow.
    out = []
    for ln in lines:
        if draw.textlength(ln, font=font) <= max_w:
            out.append(ln)
            continue
        buf = ""
        for ch in ln:
            if draw.textlength(buf + ch, font=font) <= max_w:
                buf += ch
            else:
                out.append(buf)
                buf = ch
        if buf:
            out.append(buf)
    return out[:4]


def make_sports_og(out_path: Path, *, sport: str, lang: str,
                   label: str, headline: str, sub: str = "") -> None:
    th = THEMES.get(sport, THEMES["football"])
    img = _vgrad(th["top"], th["bot"])
    d = ImageDraw.Draw(img)

    accent = th["accent"]
    # Top-left accent bar
    d.rectangle([0, 0, W, 6], fill=accent)

    # Right-side ball motif
    cx, cy, R = 980, 300, 150
    if sport == "baseball":
        _draw_baseball_motif(d, cx, cy, R, accent)
    else:
        _draw_football_motif(d, cx, cy, R, accent)

    # Label chip (top-left)
    f_label = load_font_for_lang(lang, 30, bold=True)
    lab = (label or th["label_fallback"]).upper()
    d.text((60, 64), lab, font=f_label, fill=accent)

    # Headline (wrapped, big)
    f_head = load_font_for_lang(lang, 66, bold=True)
    lines = _wrap(d, headline, f_head, max_w=740)
    y = 170
    for ln in lines:
        d.text((60, y), ln, font=f_head, fill=(255, 255, 255))
        y += 84

    # Sub (date / leagues)
    if sub:
        f_sub = load_font_for_lang(lang, 28, bold=False)
        d.text((60, max(y + 8, 470)), sub, font=f_sub, fill=(150, 165, 190))

    # Brand footer
    f_brand = load_font_for_lang("en", 26, bold=True)
    d.text((60, 556), "luckyplz.com", font=f_brand, fill=accent)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")


if __name__ == "__main__":
    # Smoke test
    out = Path(__file__).resolve().parent.parent / "public" / "assets" / "sports" / "_smoke.png"
    make_sports_og(out, sport="baseball", lang="ko",
                   label="MLB 데일리", headline="다저스, 연장 끝에 9-7 신승",
                   sub="2026-06-11 · MLB 15경기")
    print("wrote", out)
