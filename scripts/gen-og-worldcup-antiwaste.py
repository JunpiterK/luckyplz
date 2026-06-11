#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OG images (4 langs) for the worldcup anti-time-wasting post.

Pitch-green theme matching the worldcup series, with a big 8-SEC stopwatch +
a little bed icon (침대축구) motif. Reuses the CJK-safe font loader from
gen_daily_og. Output: public/assets/blog/worldcup-2026-anti-time-wasting-<lang>.png
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
GREEN = (45, 212, 191)
GREEN2 = (52, 211, 153)
GOLD = (251, 191, 36)
RED = (239, 68, 68)
WHITE = (245, 250, 247)
DIM = (120, 150, 140)
DARK = (10, 26, 20)

TEXT = {
    "ko": ("월드컵 2026 · 침대축구 근절", ["침대축구,", "이제 8초 안에 일어나세요"], "8초 골키퍼 · 교체 10초 · 부상 1분"),
    "en": ("WORLD CUP 2026 · WAR ON TIME-WASTING", ["Time-wasting?", "You have 8 seconds"], "8-sec keeper · 10-sec sub · 1-min injury"),
    "ja": ("W杯 2026 · 時間稼ぎ撲滅", ["遅延行為よ、", "あと8秒です"], "8秒キーパー · 交代10秒 · 負傷1分"),
    "zh": ("世界杯2026 · 反拖延时间", ["拖延时间？", "你还有8秒"], "8秒门将 · 换人10秒 · 受伤1分钟"),
}


def vgrad(top, bot):
    base = Image.new("RGB", (W, H), top)
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), int(y / (H - 1) * 255))
    return Image.composite(Image.new("RGB", (W, H), bot), base, g.resize((W, H)))


def stopwatch(d, cx, cy, r):
    # top button + crown
    d.rectangle([cx - 14, cy - r - 26, cx + 14, cy - r - 8], fill=DIM)
    d.ellipse([cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18], outline=GREEN2, width=4)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DARK, outline=GOLD, width=8)
    # big 8
    f = load_font_for_lang("en", 150, bold=True)
    tb = d.textbbox((0, 0), "8", font=f)
    d.text((cx - (tb[2] - tb[0]) / 2, cy - (tb[3] - tb[1]) / 2 - tb[1]), "8", font=f, fill=GOLD)
    # ticking hand near the top, into the red zone
    a = math.radians(-52)
    d.line([cx, cy, cx + math.cos(a) * (r - 22), cy + math.sin(a) * (r - 22)], fill=RED, width=6)


def bed(d, x, y, s):
    # tiny bed icon (침대축구)
    d.rounded_rectangle([x, y, x + s, y + int(s * 0.52)], 6, fill=(60, 130, 240))
    d.rounded_rectangle([x - 8, y - int(s * 0.34), x + int(s * 0.34), y + int(s * 0.2)], 6, fill=WHITE)  # pillow
    d.rectangle([x - 8, y + int(s * 0.5), x - 2, y + int(s * 0.7)], fill=(40, 90, 180))   # legs
    d.rectangle([x + s - 4, y + int(s * 0.5), x + s + 2, y + int(s * 0.7)], fill=(40, 90, 180))
    d.text((x + int(s * 0.42), y - int(s * 0.05)), "z", font=load_font_for_lang("en", 26, bold=True), fill=DIM)


def build(lang):
    img = vgrad((10, 32, 24), (4, 13, 10))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=GREEN)
    # mowed stripes hint
    for i in range(0, W, 120):
        if (i // 120) % 2 == 0:
            ov = Image.new("RGBA", (120, H), (255, 255, 255, 6))
            img.paste(Image.alpha_composite(img.convert("RGBA").crop((i, 0, i + 120, H)), ov).convert("RGB"), (i, 0))
    d = ImageDraw.Draw(img)

    kicker, lines, sub = TEXT[lang]
    f_k = load_font_for_lang(lang, 28, bold=True)
    d.text((60, 60), kicker, font=f_k, fill=GREEN)

    f_h = load_font_for_lang(lang, 60, bold=True)
    y = 140
    for ln in lines:
        d.text((60, y), ln, font=f_h, fill=WHITE)
        y += 82

    f_s = load_font_for_lang(lang, 30, bold=True)
    d.text((60, y + 26), sub, font=f_s, fill=GOLD)

    f_b = load_font_for_lang("en", 26, bold=True)
    d.text((60, 556), "luckyplz.com", font=f_b, fill=GOLD)

    stopwatch(d, 1000, 220, 120)
    bed(d, 920, 430, 150)

    out = OUT / f"worldcup-2026-anti-time-wasting-{lang}.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB)")


for lang in ("ko", "en", "ja", "zh"):
    build(lang)
