#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OG images (4 langs) for the SpaceX SPCX debut analysis.

Finance theme — dark navy, green (+19% up day), a SPCX ticker chip, an
up-trend line and a small rocket. Reuses the CJK-safe font loader.
Output: public/assets/blog/spacex-spcx-ipo-debut-2026-<lang>.png
"""
import importlib.util
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "assets" / "blog"

spec = importlib.util.spec_from_file_location("gdo", ROOT / "scripts" / "gen_daily_og.py")
_gdo = importlib.util.module_from_spec(spec)
sys.modules["gdo"] = _gdo
spec.loader.exec_module(_gdo)
load_font_for_lang = _gdo.load_font_for_lang

W, H = 1200, 630
UP = (34, 197, 94)
UP2 = (74, 222, 128)
GOLD = (251, 191, 36)
WHITE = (240, 246, 252)
DIM = (130, 145, 165)
NAVY = (19, 26, 40)

TEXT = {
    "ko": ("증시 · SpaceX IPO 분석", ["상장 첫날 +19%,", "시총 2조 달러 돌파"], "공모가 $135 → 종가 $160.95 · 나스닥 SPCX"),
    "en": ("MARKETS · SpaceX IPO", ["Day-1 +19%,", "past a $2T cap"], "Priced $135 → closed $160.95 · Nasdaq SPCX"),
    "ja": ("株式 · スペースXIPO", ["初日+19%、", "時価総額2兆ドル超え"], "公開$135 → 終値$160.95 · ナスダックSPCX"),
    "zh": ("股市 · SpaceX IPO", ["首日+19%，", "市值破2万亿美元"], "发行$135 → 收盘$160.95 · 纳斯达克SPCX"),
}


def vgrad(top, bot):
    base = Image.new("RGB", (W, H), top)
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), int(y / (H - 1) * 255))
    return Image.composite(Image.new("RGB", (W, H), bot), base, g.resize((W, H)))


def uptrend(d, x0, y0, x1, y1):
    # jagged rising line + arrow head
    import random
    pts = []
    n = 7
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        base = y0 + (y1 - y0) * t
        jit = (-1) ** i * (8 if i % 2 else 4)
        pts.append((x, base + jit))
    d.line(pts, fill=UP2, width=5, joint="curve")
    # arrowhead at end
    ex, ey = pts[-1]
    d.polygon([(ex, ey), (ex - 16, ey + 4), (ex - 6, ey + 16)], fill=UP2)
    d.polygon([(ex, ey), (ex - 18, ey - 2), (ex - 2, ey + 14)], fill=UP2)
    # arrow tip up-right
    d.line([ex - 22, ey + 12, ex + 6, ey - 14], fill=UP2, width=5)
    d.polygon([(ex + 8, ey - 18), (ex - 6, ey - 14), (ex + 4, ey - 2)], fill=UP2)


def rocket(d, cx, cy, s):
    d.polygon([(cx, cy - s), (cx - s*0.42, cy + s*0.5), (cx + s*0.42, cy + s*0.5)], fill=(225, 232, 242))
    d.ellipse([cx - s*0.2, cy - s*0.35, cx + s*0.2, cy + s*0.05], fill=(20, 30, 50), outline=UP2, width=3)
    d.polygon([(cx - s*0.42, cy + s*0.5), (cx - s*0.66, cy + s*0.74), (cx - s*0.18, cy + s*0.56)], fill=(150, 165, 185))
    d.polygon([(cx + s*0.42, cy + s*0.5), (cx + s*0.66, cy + s*0.74), (cx + s*0.18, cy + s*0.56)], fill=(150, 165, 185))
    d.polygon([(cx - s*0.22, cy + s*0.5), (cx + s*0.22, cy + s*0.5), (cx, cy + s*0.95)], fill=GOLD)


def build(lang):
    img = vgrad((20, 30, 48), (8, 11, 18))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=UP)

    kicker, lines, sub = TEXT[lang]
    f_k = load_font_for_lang(lang, 28, bold=True)
    d.text((60, 64), kicker, font=f_k, fill=UP2)

    # SPCX ticker chip
    f_t = load_font_for_lang("en", 30, bold=True)
    d.rounded_rectangle([60, 108, 250, 152], 9, fill=(12, 20, 34), outline=UP2, width=2)
    d.text((78, 114), "SPCX", font=f_t, fill=UP2)
    f_pct = load_font_for_lang("en", 30, bold=True)
    d.text((268, 114), "▲ 19%", font=f_pct, fill=UP2)

    f_h = load_font_for_lang(lang, 58, bold=True)
    y = 185
    for ln in lines:
        d.text((60, y), ln, font=f_h, fill=WHITE)
        y += 78

    f_s = load_font_for_lang(lang, 26, bold=True)
    d.text((60, y + 22), sub, font=f_s, fill=DIM)

    f_b = load_font_for_lang("en", 26, bold=True)
    d.text((60, 556), "luckyplz.com", font=f_b, fill=GOLD)

    uptrend(d, 760, 470, 1090, 230)
    rocket(d, 1010, 175, 95)

    out = OUT / f"spacex-spcx-ipo-debut-2026-{lang}.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB)")


for lang in ("ko", "en", "ja", "zh"):
    build(lang)
