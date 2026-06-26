#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OG images (4 langs) for the SK Hynix peak-out early-warning radar post.

Dark dashboard card echoing the post's identity: deep navy background, a
green->amber->red gauge bar with a white pin at the current cycle position,
and the status callout (e.g. "아직 정점 아님"). Reuses the CJK-safe font loader.
Output: public/assets/blog/skhynix-peakout-radar-<lang>.png
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
RED = (255, 90, 90)
GREEN = (61, 220, 132)
AMBER = (245, 177, 76)
WHITE = (234, 240, 248)
DIM = (148, 163, 184)
CARDBG = (20, 27, 40)
LINE = (38, 49, 63)

TEXT = {
    "ko": ("SK하이닉스 · 피크아웃 레이더",
           ["주가가 꺾이는 순간을,", "남보다 먼저 포착한다"],
           "8대 선행지표 · 4종 시나리오 · 매도 판단 룰",
           "아직 정점 아님", "사이클 후반, 피크 신호 미점등"),
    "en": ("SK HYNIX · PEAK-OUT RADAR",
           ["Catch the top", "before anyone else"],
           "8 leading signals · 4 scenarios · a sell rule",
           "Not at the top yet", "Late cycle, no peak signal lit"),
    "ja": ("SKハイニックス · ピークアウトレーダー",
           ["株価が崩れる瞬間を、", "誰よりも先に捉える"],
           "8つの先行指標 · 4シナリオ · 売却ルール",
           "まだ天井ではない", "サイクル後半、ピーク信号は未点灯"),
    "zh": ("SK海力士 · 见顶预警雷达",
           ["在众人之前，", "捕捉股价见顶时刻"],
           "八大先行指标 · 四种情景 · 卖出规则",
           "尚未见顶", "周期后段，见顶信号未点亮"),
}


def vgrad(top, bot):
    base = Image.new("RGB", (W, H), top)
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), int(y / (H - 1) * 255))
    return Image.composite(Image.new("RGB", (W, H), bot), base, g.resize((W, H)))


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gauge_bar(draw, x0, y0, x1, y1, pin_frac):
    """green->amber->red horizontal gauge with a white pin."""
    w = x1 - x0
    h = y1 - y0
    bar = Image.new("RGB", (w, h))
    bd = bar.load()
    for px in range(w):
        f = px / (w - 1)
        if f <= 0.40:
            col = GREEN
        elif f <= 0.65:
            col = _lerp(GREEN, AMBER, (f - 0.40) / 0.25)
        else:
            col = _lerp(AMBER, RED, (f - 0.65) / 0.35)
        for py in range(h):
            bd[px, py] = col
    # rounded mask
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=255)
    draw._image.paste(bar, (x0, y0), mask)
    # pin
    pin_x = x0 + int(w * pin_frac)
    draw.rounded_rectangle([pin_x - 3, y0 - 9, pin_x + 3, y1 + 9], 3, fill=WHITE)


def build(lang):
    img = vgrad((16, 25, 41), (7, 10, 17))
    d = ImageDraw.Draw(img)
    d._image = img
    # top accent: green->amber->red sliver echoing the gauge
    for px in range(W):
        f = px / (W - 1)
        if f <= 0.40:
            col = GREEN
        elif f <= 0.65:
            col = _lerp(GREEN, AMBER, (f - 0.40) / 0.25)
        else:
            col = _lerp(AMBER, RED, (f - 0.65) / 0.35)
        d.line([(px, 0), (px, 7)], fill=col)

    kicker, lines, sub, status, status_sub = TEXT[lang]

    d.text((60, 70), kicker, font=load_font_for_lang(lang, 25, bold=True), fill=BLUE)

    f_h = load_font_for_lang(lang, 46, bold=True)
    y = 158
    for ln in lines:
        d.text((60, y), ln, font=f_h, fill=WHITE)
        y += 64

    d.text((60, y + 34), sub, font=load_font_for_lang(lang, 21, bold=False), fill=DIM)

    # Right status card
    cx0, cy0, cx1, cy1 = 716, 150, 1140, 474
    d.rounded_rectangle([cx0, cy0, cx1, cy1], 18, fill=CARDBG, outline=LINE, width=2)
    d.text((cx0 + 30, cy0 + 30), "CYCLE POSITION", font=load_font_for_lang("en", 18, bold=True), fill=DIM)
    d.text((cx0 + 30, cy0 + 64), status, font=load_font_for_lang(lang, 40, bold=True), fill=GREEN)
    # gauge inside card
    gauge_bar(d, cx0 + 30, cy0 + 158, cx1 - 30, cy0 + 178, 0.42)
    # legend
    d.text((cx0 + 30, cy0 + 196), "초기 · 상승 · 경계 · 피크" if lang == "ko" else
           ("初期 · 上昇 · 警戒 · ピーク" if lang == "ja" else
            ("初期 · 上行 · 警戒 · 见顶" if lang == "zh" else "Early · Rising · Caution · Peak")),
           font=load_font_for_lang(lang, 16, bold=False), fill=DIM)
    d.text((cx0 + 30, cy0 + 246), status_sub, font=load_font_for_lang(lang, 18, bold=False), fill=(196, 206, 222))

    d.text((60, 556), "luckyplz.com", font=load_font_for_lang("en", 26, bold=True), fill=BLUE)

    out = OUT / f"skhynix-peakout-radar-{lang}.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB)")


for lang in ("ko", "en", "ja", "zh"):
    build(lang)
