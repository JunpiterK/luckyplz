#!/usr/bin/env python3
"""OG images (4 langs) for the worldcup-2026-group-stage-schedule post.

Matches the worldcup series OG look (deep pitch green, mono kicker, big
headline, ball motif) and adds a mini calendar grid to say "schedule".
Output: public/assets/blog/worldcup-2026-group-stage-schedule-<lang>.png
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
GREEN = (45, 212, 191)
GREEN2 = (52, 211, 153)
GOLD = (251, 191, 36)
DIM = (111, 138, 128)

TEXT = {
    "ko": ("월드컵 2026 · 조별리그 일정", ["조별리그 72경기", "한국시간 총정리"], "도시·나라 병기 · 한국 3경기 전부 오전"),
    "en": ("WORLD CUP 2026 · GROUP STAGE", ["All 72 Group Games", "in US Eastern Time"], "Host city & country for every match"),
    "ja": ("W杯 2026 · グループステージ", ["全72試合の日程を", "日本時間で整理"], "開催都市・国を併記 · 日本戦は朝"),
    "zh": ("2026世界杯 · 小组赛赛程", ["小组赛72场比赛", "北京时间完整版"], "标注球场城市·国家 · 焦点战速查"),
}


def vgrad(top, bot):
    base = Image.new("RGB", (W, H), top)
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), int(y / (H - 1) * 255))
    return Image.composite(Image.new("RGB", (W, H), bot), base, g.resize((W, H)))


def ball(d, cx, cy, r):
    d.ellipse([cx - r - 26, cy - r - 26, cx + r + 26, cy + r + 26], outline=GREEN2, width=3)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(238, 242, 240))
    pr = r * 0.42
    d.regular_polygon((cx, cy, pr), 5, rotation=90, fill=(10, 16, 13))
    import math
    for i in range(5):
        a = math.radians(90 + i * 72)
        x1, y1 = cx + math.cos(a) * pr, cy - math.sin(a) * pr
        x2, y2 = cx + math.cos(a) * r * 0.96, cy - math.sin(a) * r * 0.96
        d.line([x1, y1, x2, y2], fill=(150, 158, 154), width=3)


def calendar(d, x, y, cw, lang):
    """Mini month grid with a few highlighted match days."""
    rows, cols = 4, 7
    ch = cw
    d.rounded_rectangle([x - 14, y - 40, x + cols * cw + 14, y + rows * ch + 14], 16,
                        fill=(8, 26, 20), outline=(28, 59, 48), width=2)
    f = load_font_for_lang(lang, 20, bold=True)
    d.text((x, y - 34), {"ko": "JUNE 2026", "en": "JUNE 2026", "ja": "JUNE 2026", "zh": "JUNE 2026"}[lang],
           font=f, fill=DIM)
    hot = {11, 12, 14, 18, 24}  # representative match days
    n = 1
    for r in range(rows):
        for c in range(cols):
            if n > 27:
                break
            px, py = x + c * cw, y + r * ch
            if n in hot:
                d.rounded_rectangle([px + 2, py + 2, px + cw - 6, py + ch - 6], 8, fill=GREEN)
                fill = (4, 35, 26)
            else:
                d.rounded_rectangle([px + 2, py + 2, px + cw - 6, py + ch - 6], 8,
                                    outline=(28, 59, 48), width=1)
                fill = DIM
            fn = load_font_for_lang("en", 18, bold=True)
            tb = d.textbbox((0, 0), str(n), font=fn)
            d.text((px + (cw - 4) / 2 - (tb[2] - tb[0]) / 2, py + (ch - 4) / 2 - (tb[3] - tb[1]) / 2 - tb[1]),
                   str(n), font=fn, fill=fill)
            n += 1


def build(lang):
    img = vgrad((10, 32, 24), (4, 13, 10))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=GREEN)

    kicker, lines, sub = TEXT[lang]
    f_k = load_font_for_lang(lang, 30, bold=True)
    d.text((60, 64), kicker, font=f_k, fill=GREEN)

    f_h = load_font_for_lang(lang, 72, bold=True)
    y = 150
    for ln in lines:
        d.text((60, y), ln, font=f_h, fill=(255, 255, 255))
        y += 92

    f_s = load_font_for_lang(lang, 28, bold=False)
    d.text((60, y + 22), sub, font=f_s, fill=(150, 175, 165))

    f_b = load_font_for_lang("en", 26, bold=True)
    d.text((60, 556), "luckyplz.com", font=f_b, fill=GOLD)

    ball(d, 1010, 200, 95)
    calendar(d, 800, 400, 44, lang)

    out = OUT / f"worldcup-2026-group-stage-schedule-{lang}.png"
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB)")


for lang in ("ko", "en", "ja", "zh"):
    build(lang)
