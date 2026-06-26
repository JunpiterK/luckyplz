#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OG images (4 langs) for the AI capex / market-volatility post.

Dark finance card: the $725B hero number, a +77% YoY tag, and four capex
bars (Amazon/Microsoft/Alphabet/Meta) echoing the article's chart. Reuses
the CJK-safe font loader.
Output: public/assets/blog/ai-capex-supercycle-volatility-<lang>.png
"""
import importlib.util
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
BLUE = (84, 168, 255)
BLUE2 = (140, 196, 255)
GREEN = (61, 220, 132)
AMBER = (245, 177, 76)
WHITE = (234, 240, 248)
DIM = (148, 163, 184)
CARDBG = (20, 27, 40)
LINE = (38, 49, 63)
TRACK = (14, 19, 28)

TEXT = {
    "ko": ("AI 캡엑스 슈퍼사이클 · 2026",
           ["1,000조 원의 베팅,", "증시의 롤러코스터"],
           "빅테크 4사의 데이터센터 캡엑스, 그리고 변동성",
           "2026 빅테크 캡엑스 합계", "전년 대비 +77%"),
    "en": ("AI CAPEX SUPERCYCLE · 2026",
           ["The $725B Bet,", "a Market Rollercoaster"],
           "Big tech's data-center capex, and the volatility",
           "2026 BIG-TECH CAPEX", "+77% year over year"),
    "ja": ("AI設備投資スーパーサイクル · 2026",
           ["1兆ドルの賭け、", "株式市場のローラーコースター"],
           "ビッグテックのデータセンター投資と変動性",
           "2026 ビッグテック設備投資", "前年比 +77%"),
    "zh": ("AI资本开支超级周期 · 2026",
           ["万亿美元豪赌，", "股市过山车"],
           "科技巨头的数据中心开支与波动",
           "2026 科技巨头资本开支", "同比 +77%"),
}

# capex bars (label, fraction of 200)
BARS = [("Amazon", 1.00), ("Microsoft", 0.95), ("Alphabet", 0.93), ("Meta", 0.68)]


def vgrad(top, bot):
    base = Image.new("RGB", (W, H), top)
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), int(y / (H - 1) * 255))
    return Image.composite(Image.new("RGB", (W, H), bot), base, g.resize((W, H)))


def build(lang):
    img = vgrad((16, 25, 41), (7, 10, 17))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 7], fill=BLUE)

    kicker, lines, sub, card_label, card_sub = TEXT[lang]

    d.text((60, 70), kicker, font=load_font_for_lang(lang, 24, bold=True), fill=BLUE)

    f_h = load_font_for_lang(lang, 44, bold=True)
    y = 150
    for ln in lines:
        d.text((60, y), ln, font=f_h, fill=WHITE)
        y += 62

    d.text((60, y + 28), sub, font=load_font_for_lang(lang, 20, bold=False), fill=DIM)

    # Right card: $725B hero + capex bars
    cx0, cy0, cx1, cy1 = 724, 150, 1140, 474
    d.rounded_rectangle([cx0, cy0, cx1, cy1], 18, fill=CARDBG, outline=LINE, width=2)
    d.text((cx0 + 28, cy0 + 26), card_label, font=load_font_for_lang(lang, 17, bold=True), fill=DIM)
    d.text((cx0 + 26, cy0 + 52), "$725B", font=load_font_for_lang("en", 72, bold=True), fill=BLUE2)
    d.text((cx0 + 28, cy0 + 142), card_sub, font=load_font_for_lang(lang, 19, bold=True), fill=GREEN)
    # capex bars
    bx0 = cx0 + 28
    bx1 = cx1 - 28
    by = cy0 + 180
    for label, frac in BARS:
        d.text((bx0, by), label, font=load_font_for_lang("en", 13, bold=False), fill=DIM)
        ty = by + 19
        d.rounded_rectangle([bx0, ty, bx1, ty + 9], 4, fill=TRACK)
        fw = int((bx1 - bx0) * frac)
        d.rounded_rectangle([bx0, ty, bx0 + fw, ty + 9], 4, fill=BLUE)
        by += 33

    d.text((60, 556), "luckyplz.com", font=load_font_for_lang("en", 26, bold=True), fill=BLUE)

    out = OUT / f"ai-capex-supercycle-volatility-{lang}.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB)")


for lang in ("ko", "en", "ja", "zh"):
    build(lang)
