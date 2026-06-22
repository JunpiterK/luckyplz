#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OG images (4 langs) for the Hyundai governance succession / Boston Dynamics post.

Premium finance card — dark navy + gold, serif-feel headline, and the hero
number 22.6% (Chung's personal Boston Dynamics stake) called out on the right.
Reuses the CJK-safe font loader. Output:
public/assets/blog/hyundai-succession-boston-dynamics-<lang>.png
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
GOLD = (199, 154, 46)
GOLD2 = (235, 198, 116)
WHITE = (238, 242, 248)
DIM = (150, 164, 186)
CARDBG = (24, 38, 60)

TEXT = {
    "ko": ("증시 심층 · 지배구조",
           ["정의선의 마지막 퍼즐,", "현대차 승계의 히든카드"],
           "순환출자·모비스·글로비스, 그리고 보스턴 다이내믹스",
           "보스턴 다이내믹스", "정의선 개인 지분"),
    "en": ("STOCKS · GOVERNANCE",
           ["Hyundai's Succession", "& the Hidden Card"],
           "Circular ownership, Mobis, Glovis, and Boston Dynamics",
           "Boston Dynamics", "Chung's personal stake"),
    "ja": ("株式 · ガバナンス",
           ["鄭義宣 最後のパズル、", "現代承継の切り札"],
           "循環出資・モービス・グロービス、そしてボストン・ダイナミクス",
           "ボストン・ダイナミクス", "鄭会長 個人持分"),
    "zh": ("股市 · 治理结构",
           ["郑义宣最后的拼图，", "传承的隐藏王牌"],
           "循环出资·摩比斯·格罗维斯，以及波士顿动力",
           "波士顿动力", "郑会长 个人持股"),
}


def vgrad(top, bot):
    base = Image.new("RGB", (W, H), top)
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), int(y / (H - 1) * 255))
    return Image.composite(Image.new("RGB", (W, H), bot), base, g.resize((W, H)))


def build(lang):
    img = vgrad((17, 27, 46), (8, 13, 24))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=GOLD)

    kicker, lines, sub, cap1, cap2 = TEXT[lang]

    d.text((60, 66), kicker, font=load_font_for_lang(lang, 26, bold=True), fill=GOLD)

    f_h = load_font_for_lang(lang, 47, bold=True)
    y = 156
    for ln in lines:
        d.text((60, y), ln, font=f_h, fill=WHITE)
        y += 66

    d.text((60, y + 30), sub, font=load_font_for_lang(lang, 22, bold=False), fill=DIM)

    # Right hero card — 22.6%
    d.rounded_rectangle([764, 150, 1140, 474], 18, fill=CARDBG, outline=GOLD, width=2)
    d.text((792, 184), cap1, font=load_font_for_lang(lang, 23, bold=True), fill=WHITE)
    d.text((788, 232), "22.6%", font=load_font_for_lang("en", 92, bold=True), fill=GOLD2)
    d.text((792, 372), cap2, font=load_font_for_lang(lang, 21, bold=False), fill=DIM)
    # thin gold underline accent inside card
    d.rectangle([792, 426, 1112, 429], fill=GOLD)

    d.text((60, 556), "luckyplz.com", font=load_font_for_lang("en", 26, bold=True), fill=GOLD)

    out = OUT / f"hyundai-succession-boston-dynamics-{lang}.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB)")


for lang in ("ko", "en", "ja", "zh"):
    build(lang)
