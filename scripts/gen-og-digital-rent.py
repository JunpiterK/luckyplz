#!/usr/bin/env python3
"""Generate polished 1200x630 OG images for the Claude Fable 5 blog post.

One-off generator. Produces 4 localized OG images (ko/en/ja/zh) into
public/og/ matching the blog slug convention:
  claude-opus-4-8.png      (ko)
  claude-opus-4-8-en.png   (en)
  claude-opus-4-8-ja.png   (ja)
  claude-opus-4-8-zh.png   (zh)

Design: dark gradient + warm "Claude clay" radial glow, the Claude spark
logo, a big "Claude Opus 4.8" wordmark, a localized subtitle, two factual
benchmark chips, and luckyplz.com branding.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OG = ROOT / "public" / "og"
LOGO = ROOT / "public" / "assets" / "anthropic-series" / "ep1" / "fig-05-claude-logo.png"
FONTS = Path("C:/Windows/Fonts")

W, H = 1200, 630
BG_TOP = (12, 14, 20)
BG_BOT = (5, 6, 10)
CLAY = (217, 119, 87)      # Claude warm clay accent
BLUE = (77, 163, 255)      # site accent
WHITE = (245, 247, 250)
DIM = (150, 162, 180)
CHIP_BG = (17, 21, 28)
CHIP_BD = (40, 52, 72)

LANGS = {
    "":    {"font": "malgunbd.ttf", "sub": "반도체로 벌고, 구독으로 새는 돈"},
    "-en": {"font": "arialbd.ttf",  "sub": "Earned in Chips, Spent on Subscriptions"},
    "-ja": {"font": "YuGothB.ttc",  "sub": "半導体で稼ぎ、購読料で流出"},
    "-zh": {"font": "msyhbd.ttc",   "sub": "芯片赚来，订阅流走"},
}


def load_spark():
    """The logo PNG is the full Claude lockup (coral spark + black
    'Claude' wordmark). The black wordmark is invisible on a dark
    background, so crop just the coral spark on the left and trim
    transparent margins."""
    logo = Image.open(LOGO).convert("RGBA")
    w, h = logo.size
    spark = logo.crop((0, 0, int(w * 0.235), h))  # left ~23.5% = spark only
    bbox = spark.getbbox()
    if bbox:
        spark = spark.crop(bbox)
    return spark


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def vertical_gradient(w, h, top, bot):
    base = Image.new("RGB", (w, h), top)
    top_arr = top
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


def rounded_chip(draw, xy, text, fnt, pad=(16, 9), accent=BLUE):
    x, y = xy
    tb = draw.textbbox((0, 0), text, font=fnt)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    w = tw + pad[0] * 2
    h = th + pad[1] * 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2,
                           fill=CHIP_BG, outline=CHIP_BD, width=1)
    # accent dot
    dot_r = 5
    dot_cx = x + pad[0] + dot_r
    dot_cy = y + h // 2
    draw.ellipse([dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r],
                 fill=accent)
    draw.text((dot_cx + dot_r + 8, y + pad[1] - tb[1]), text, font=fnt, fill=WHITE)
    return w, h


def build(lang_suffix, subtitle):
    img = vertical_gradient(W, H, BG_TOP, BG_BOT).convert("RGBA")
    # warm clay glow top-right + faint blue bottom-left
    img.alpha_composite(radial_glow(W, H, 1080, 80, 460, CLAY, 90))
    img.alpha_composite(radial_glow(W, H, 120, 600, 420, BLUE, 45))

    # thin top accent rule
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=CLAY)

    # Claude spark mark (cropped from the full lockup; the black wordmark
    # is dropped because it's invisible on dark — we render our own).
    LS = 150
    logo = Image.new("RGBA", (LS, LS), (0, 0, 0, 0))
    ld = ImageDraw.Draw(logo)
    ld.ellipse([4, 4, LS - 4, LS - 4], outline=CLAY, width=7)
    f_won = ImageFont.truetype(str(FONTS / "malgunbd.ttf"), 78)
    wb = ld.textbbox((0, 0), "₩", font=f_won)
    ld.text(((LS - (wb[2]-wb[0])) // 2 - wb[0], (LS - (wb[3]-wb[1])) // 2 - wb[1]),
            "₩", font=f_won, fill=CLAY)
    LS_W, LS_H = logo.size

    # --- hero block (logo + wordmark) centered as a group near upper-middle ---
    f_claude = font("arialbd.ttf", 46)
    f_opus = font("arialbd.ttf", 104)
    claude_txt = "Korea's"
    opus_txt = "Digital Rent"

    # measure
    cb = d.textbbox((0, 0), claude_txt, font=f_claude)
    ob = d.textbbox((0, 0), opus_txt, font=f_opus)
    cw = cb[2] - cb[0]
    ow = ob[2] - ob[0]
    text_w = max(cw, ow)
    gap = 40
    group_w = LS_W + gap + text_w
    gx = (W - group_w) // 2
    gy_center = 250

    # logo vertically centered to the text block (text block height approx)
    text_block_h = 56 + 132
    logo_y = gy_center - LS_H // 2
    img.alpha_composite(logo, (gx, logo_y))

    tx = gx + LS_W + gap
    # "Claude" (clay) then "Opus 4.8" (white)
    d.text((tx, gy_center - text_block_h // 2 - 6), claude_txt, font=f_claude, fill=CLAY)
    d.text((tx, gy_center - text_block_h // 2 + 50), opus_txt, font=f_opus, fill=WHITE)

    # subtitle (localized), centered
    f_sub = font(LANGS[lang_suffix]["font"], 34)
    sb = d.textbbox((0, 0), subtitle, font=f_sub)
    sw = sb[2] - sb[0]
    d.text(((W - sw) // 2, 392), subtitle, font=f_sub, fill=DIM)

    # benchmark chips (universal, factual) centered row
    f_chip = font("arialbd.ttf", 24)
    chips = ["Chip exports  $37.16B / May", "ChatGPT spend  #2  worldwide"]
    # measure total
    widths = []
    for c in chips:
        tb = d.textbbox((0, 0), c, font=f_chip)
        widths.append((tb[2] - tb[0]) + 16 * 2 + 5 * 2 + 8 + 6)
    chip_gap = 22
    total = sum(widths) + chip_gap
    cx = (W - total) // 2
    cy = 470
    accents = [CLAY, BLUE]
    for i, c in enumerate(chips):
        w, h = rounded_chip(d, (cx, cy), c, f_chip, accent=accents[i])
        cx += w + chip_gap

    # footer brand
    f_brand = font("arialbd.ttf", 26)
    f_meta = font("arial.ttf", 22)
    d.text((70, H - 70), "luckyplz.com", font=f_brand, fill=WHITE)
    meta = "INDUSTRY · 2026.06.10"
    mb = d.textbbox((0, 0), meta, font=f_meta)
    d.text((W - 70 - (mb[2] - mb[0]), H - 68), meta, font=f_meta, fill=DIM)

    out = OG / f"korea-digital-rent{lang_suffix}.png"
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"  wrote {out.name}  ({out.stat().st_size // 1024} KB)")


def main():
    OG.mkdir(parents=True, exist_ok=True)
    print("Generating Digital Rent OG images:")
    for suffix in ("", "-en", "-ja", "-zh"):
        build(suffix, LANGS[suffix]["sub"])
    print("done.")


if __name__ == "__main__":
    main()
