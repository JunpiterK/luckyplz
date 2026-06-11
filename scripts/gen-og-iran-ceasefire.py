#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OG images (4 langs) for the Iran-US ceasefire issue post.

Serious news card — dark slate + amber, clean typography, an 'AS OF' stamp
and a simple globe motif. No cartoon (this is war news). Reuses the CJK-safe
font loader. Output: public/assets/blog/iran-us-ceasefire-2026-06-<lang>.png
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
AMBER = (245, 158, 11)
AMBER2 = (251, 191, 36)
RED = (239, 68, 68)
WHITE = (240, 244, 250)
DIM = (130, 145, 165)
SLATE = (40, 50, 70)

TEXT = {
    "ko": ("이슈 · 중동 정세", ["이란-미국 휴전,", "종전으로 가나"], "확정 종전 아님 · 호르무즈·핵·제재 5대 쟁점", "2026.6.12 기준"),
    "en": ("ISSUE · MIDDLE EAST", ["Iran–US Ceasefire:", "How Close Is Peace?"], "Not a finished deal · Hormuz, nuclear, sanctions", "As of Jun 12, 2026"),
    "ja": ("時事 · 中東情勢", ["イラン・米国の停戦は", "終戦へ向かうか"], "終戦合意ではない · ホルムズ・核・制裁", "2026.6.12時点"),
    "zh": ("时事 · 中东局势", ["伊朗-美国停火,", "能走向终战吗"], "并非已达成终战 · 霍尔木兹·核·制裁", "截至2026.6.12"),
}


def vgrad(top, bot):
    base = Image.new("RGB", (W, H), top)
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), int(y / (H - 1) * 255))
    return Image.composite(Image.new("RGB", (W, H), bot), base, g.resize((W, H)))


def globe(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=SLATE, width=3)
    # latitudes
    for fy in (-0.5, 0, 0.5):
        yy = cy + fy * r
        rw = r * math.cos(math.asin(max(-1, min(1, fy))))
        d.ellipse([cx - rw, yy - 6, cx + rw, yy + 6], outline=SLATE, width=2)
    # longitudes
    for fx in (-0.6, 0, 0.6):
        rw = r * abs(fx) if fx else r * 0.18
        d.ellipse([cx - r * abs(fx) - (4 if fx == 0 else 0), cy - r, cx + r * abs(fx) + (4 if fx == 0 else 0), cy + r], outline=SLATE, width=2)
    d.line([cx, cy - r, cx, cy + r], fill=SLATE, width=2)
    # a hot-spot marker (amber pulse) — the region in focus
    mx, my = cx + r * 0.28, cy - r * 0.12
    d.ellipse([mx - 26, my - 26, mx + 26, my + 26], outline=RED, width=2)
    d.ellipse([mx - 9, my - 9, mx + 9, my + 9], fill=RED)


def build(lang):
    img = vgrad((14, 19, 28), (7, 10, 16))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=AMBER)

    kicker, lines, sub, asof = TEXT[lang]

    # "AS OF" stamp top-right
    f_as = load_font_for_lang("en", 22, bold=True)
    fa = load_font_for_lang(lang, 24, bold=True)
    tb = d.textbbox((0, 0), asof, font=fa)
    d.rounded_rectangle([W - 60 - (tb[2] - tb[0]) - 28, 50, W - 60, 96], 10,
                        fill=(30, 18, 10), outline=RED, width=2)
    d.text((W - 60 - (tb[2] - tb[0]) - 14, 60), asof, font=fa, fill=(245, 200, 200))

    f_k = load_font_for_lang(lang, 28, bold=True)
    d.text((60, 70), kicker, font=f_k, fill=AMBER)

    f_h = load_font_for_lang(lang, 62, bold=True)
    y = 150
    for ln in lines:
        d.text((60, y), ln, font=f_h, fill=WHITE)
        y += 84

    f_s = load_font_for_lang(lang, 27, bold=False)
    d.text((60, y + 24), sub, font=f_s, fill=DIM)

    f_b = load_font_for_lang("en", 26, bold=True)
    d.text((60, 556), "luckyplz.com", font=f_b, fill=AMBER)

    globe(d, 990, 360, 150)

    out = OUT / f"iran-us-ceasefire-2026-06-{lang}.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB)")


for lang in ("ko", "en", "ja", "zh"):
    build(lang)
