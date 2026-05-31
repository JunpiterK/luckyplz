#!/usr/bin/env python3
"""Generate 1200x630 OG images for the NVIDIA CPU (Vera/GB10/Grace) blog post.

Produces 4 localized OG images (ko/en/ja/zh) into public/og/ matching:
  nvidia-cpu-vera-grace.png      (ko)
  nvidia-cpu-vera-grace-en.png   (en)
  nvidia-cpu-vera-grace-ja.png   (ja)
  nvidia-cpu-vera-grace-zh.png   (zh)

Design: warm beige paper background matching the article's book theme,
auburn rule lines, three labelled CPU "chips" (Vera / GB10 / Grace) drawn
as labelled tiles, and a localized headline + factual subtitle.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OG = ROOT / "public" / "og"
FONTS = Path("C:/Windows/Fonts")

W, H = 1200, 630
PAPER = (245, 235, 216)
PAPER_LIGHT = (250, 240, 212)
PAPER_DARK = (235, 224, 200)
INK = (44, 36, 22)
INK_SOFT = (74, 62, 42)
INK_DIM = (122, 106, 82)
BROWN = (139, 111, 71)
AUBURN = (194, 65, 12)
GOLD = (184, 134, 11)
GREEN = (47, 125, 79)        # nod to NVIDIA green
LINE = (212, 197, 168)

LANGS = {
    "":    {"font": "malgunbd.ttf", "regular": "malgun.ttf",
            "headline": "NVIDIA 가 노린 자리",
            "sub": "Vera · GB10 · Grace — CPU 세 갈래 정리",
            "tag": "AI 리포트"},
    "-en": {"font": "arialbd.ttf",  "regular": "arial.ttf",
            "headline": "Where NVIDIA Is Aiming",
            "sub": "Vera · GB10 · Grace — three CPUs, one playbook",
            "tag": "AI Report"},
    "-ja": {"font": "YuGothB.ttc",  "regular": "YuGothR.ttc",
            "headline": "NVIDIA が狙う場所",
            "sub": "Vera · GB10 · Grace — 三層の CPU を整理",
            "tag": "AI レポート"},
    "-zh": {"font": "msyhbd.ttc",   "regular": "msyh.ttc",
            "headline": "NVIDIA 瞄准的位置",
            "sub": "Vera · GB10 · Grace — 三层 CPU 一次梳理",
            "tag": "AI 报告"},
}


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def vertical_gradient(w, h, top, bot):
    base = Image.new("RGB", (w, h), top)
    grad = Image.new("L", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        grad.putpixel((0, y), int(t * 255))
    grad = grad.resize((w, h))
    bot_img = Image.new("RGB", (w, h), bot)
    base = Image.composite(bot_img, base, grad)
    return base


def radial_glow(w, h, cx, cy, radius, color, max_alpha):
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=color + (max_alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius // 2))
    return layer


def draw_chip_tile(d, x, y, w, h, title, sub, status, status_color):
    """Draw a labelled rounded tile representing one CPU SKU."""
    d.rounded_rectangle([x, y, x + w, y + h], radius=16,
                        fill=PAPER_LIGHT, outline=LINE, width=2)
    # tiny stripe on top
    d.rounded_rectangle([x, y, x + w, y + 6], radius=3, fill=status_color)
    # title
    f_title = font("arialbd.ttf", 32)
    d.text((x + 22, y + 30), title, font=f_title, fill=INK)
    # sub line
    f_sub = font("arial.ttf", 18)
    d.text((x + 22, y + 76), sub, font=f_sub, fill=INK_DIM)
    # status row
    f_status = font("arialbd.ttf", 16)
    sy = y + h - 38
    # status dot
    dot_r = 5
    d.ellipse([x + 22, sy + 6, x + 22 + dot_r * 2, sy + 6 + dot_r * 2],
              fill=status_color)
    d.text((x + 42, sy), status, font=f_status, fill=INK_SOFT)


def build(lang_suffix, conf):
    img = vertical_gradient(W, H, PAPER, PAPER_DARK).convert("RGBA")
    # warm gold + auburn highlights
    img.alpha_composite(radial_glow(W, H, 1080, 60, 420, GOLD, 55))
    img.alpha_composite(radial_glow(W, H, 100, 580, 380, AUBURN, 28))

    d = ImageDraw.Draw(img)

    # thin top rule
    d.rectangle([0, 0, W, 6], fill=AUBURN)

    # series tag (top-left small)
    f_tag = font("arialbd.ttf", 22)
    d.text((70, 50), "Lucky Please", font=f_tag, fill=BROWN)
    f_tag2 = font(conf["regular"], 20)
    d.text((70, 82), conf["tag"], font=f_tag2, fill=INK_DIM)

    # date top-right
    f_date = font("arialbd.ttf", 20)
    date = "2026 · 05 · 29"
    db = d.textbbox((0, 0), date, font=f_date)
    d.text((W - 70 - (db[2] - db[0]), 56), date, font=f_date, fill=INK_DIM)

    # short auburn underline as ornament
    d.rectangle([70, 130, 130, 132], fill=AUBURN)

    # headline
    f_head = font(conf["font"], 64)
    headline = conf["headline"]
    hb = d.textbbox((0, 0), headline, font=f_head)
    hw = hb[2] - hb[0]
    d.text((70, 158), headline, font=f_head, fill=INK)

    # subtitle (smaller)
    f_sub = font(conf["regular"], 28)
    sub = conf["sub"]
    d.text((70, 248), sub, font=f_sub, fill=INK_SOFT)

    # --- three CPU tiles row ---
    tile_w = 340
    tile_h = 180
    tile_gap = 25
    tiles_total = tile_w * 3 + tile_gap * 2
    tile_x = (W - tiles_total) // 2
    tile_y = 360

    # Vera (next-gen, auburn)
    draw_chip_tile(d, tile_x, tile_y, tile_w, tile_h,
                   "Vera", "88 cores · Olympus Arm",
                   "2H 2026 announced", AUBURN)
    # GB10 (shipping, green)
    draw_chip_tile(d, tile_x + (tile_w + tile_gap), tile_y, tile_w, tile_h,
                   "GB10 / DGX Spark", "20-core Grace · 1 PFLOP AI",
                   "Shipping 2025.10.15", GREEN)
    # Grace (DC, gold)
    draw_chip_tile(d, tile_x + (tile_w + tile_gap) * 2, tile_y, tile_w, tile_h,
                   "Grace Superchip", "144 cores · Neoverse-V2",
                   "Datacenter base", GOLD)

    # footer
    f_brand = font("arialbd.ttf", 24)
    d.text((70, H - 60), "luckyplz.com", font=f_brand, fill=INK)
    f_meta = font("arial.ttf", 20)
    meta = "Sources: NVIDIA · MediaTek · ServeTheHome · Tom's Hardware"
    mb = d.textbbox((0, 0), meta, font=f_meta)
    d.text((W - 70 - (mb[2] - mb[0]), H - 58), meta, font=f_meta, fill=INK_DIM)

    out = OG / f"nvidia-cpu-vera-grace{lang_suffix}.png"
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"  wrote {out.name}  ({out.stat().st_size // 1024} KB)")


def main():
    OG.mkdir(parents=True, exist_ok=True)
    print("Generating NVIDIA CPU OG images:")
    for suffix in ("", "-en", "-ja", "-zh"):
        build(suffix, LANGS[suffix])
    print("done.")


if __name__ == "__main__":
    main()
