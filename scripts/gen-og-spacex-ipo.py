#!/usr/bin/env python3
"""Generate polished 1200x630 OG images for the SpaceX IPO flagship post.

Replaces the old text-on-grid OG (which also showed an outdated $1.75T).
Design: deep-space gradient + seeded starfield + drawn ascending rocket with
engine glow, big SPACEX IPO wordmark, localized subtitle, three fact chips
($135/share · Nasdaq 6/12 · $1.77T), luckyplz.com branding.

Outputs 7 localized variants into public/og/:
  spacex-ipo-2026.png      (ko)   spacex-ipo-2026-en.png
  spacex-ipo-2026-de.png   spacex-ipo-2026-es.png
  spacex-ipo-2026-hi.png   spacex-ipo-2026-zh.png
  spacex-ipo-2026-ja.png
"""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OG = ROOT / "public" / "og"
FONTS = Path("C:/Windows/Fonts")

W, H = 1200, 630
BLUE = (93, 193, 255)
PURPLE = (167, 139, 250)
FLAME = (255, 160, 60)
FLAME_CORE = (255, 230, 160)
WHITE = (245, 247, 250)
DIM = (150, 162, 180)
CHIP_BG = (14, 18, 28)
CHIP_BD = (44, 58, 84)

LANGS = {
    "":    {"font": "malgunbd.ttf",  "sub": "사상 최대 IPO — 머스크 제국의 발사"},
    "-en": {"font": "arialbd.ttf",   "sub": "The Largest IPO in History — Musk's Empire Lifts Off"},
    "-de": {"font": "arialbd.ttf",   "sub": "Der größte Börsengang aller Zeiten"},
    "-es": {"font": "arialbd.ttf",   "sub": "La mayor OPV de la historia"},
    "-hi": {"font": "NirmalaB.ttf",  "sub": "इतिहास का सबसे बड़ा IPO"},
    "-zh": {"font": "msyhbd.ttc",    "sub": "史上最大IPO — 马斯克帝国升空"},
    "-ja": {"font": "YuGothB.ttc",   "sub": "史上最大のIPO — マスク帝国の打ち上げ"},
}

CHIPS = ["$135 / SHARE", "NASDAQ · 6/12", "$1.77T VALUATION"]


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def vertical_gradient(w, h, top, bot):
    base = Image.new("RGB", (w, h), top)
    grad = Image.new("L", (1, h))
    for y in range(h):
        grad.putpixel((0, y), int(y / max(1, h - 1) * 255))
    grad = grad.resize((w, h))
    return Image.composite(Image.new("RGB", (w, h), bot), base, grad)


def radial_glow(w, h, cx, cy, radius, color, max_alpha):
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=color + (max_alpha,))
    return layer.filter(ImageFilter.GaussianBlur(radius // 2))


def starfield(img, seed=42, n=130):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        r = rnd.choice([1, 1, 1, 2])
        a = rnd.randint(70, 200)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))


def draw_rocket(img):
    """Stylized rocket ascending on the right with engine glow + trail."""
    cx = 985          # rocket axis x
    top = 96          # nose tip y
    body_w = 74
    body_h = 240
    nose_h = 86
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    bx0, bx1 = cx - body_w // 2, cx + body_w // 2
    by0 = top + nose_h
    by1 = by0 + body_h

    # engine glow stack (drawn first, behind everything)
    img.alpha_composite(radial_glow(W, H, cx, by1 + 96, 190, FLAME, 120))
    img.alpha_composite(radial_glow(W, H, cx, by1 + 56, 90, FLAME_CORE, 170))

    # exhaust trail
    for i, (w_, a) in enumerate([(34, 150), (22, 190), (10, 235)]):
        d.polygon([(cx - w_, by1 + 14), (cx + w_, by1 + 14), (cx, by1 + 150 + i * 38)],
                  fill=FLAME[:3] + (a,) if i < 2 else FLAME_CORE + (a,))

    # fins
    fin = 36
    d.polygon([(bx0, by1 - 64), (bx0 - fin, by1 + 16), (bx0, by1)], fill=(120, 134, 160, 255))
    d.polygon([(bx1, by1 - 64), (bx1 + fin, by1 + 16), (bx1, by1)], fill=(96, 108, 132, 255))

    # body
    d.rounded_rectangle([bx0, by0 - 8, bx1, by1], radius=16, fill=(214, 222, 236, 255))
    # body shading (right side darker strip)
    d.rounded_rectangle([cx + 8, by0 - 8, bx1, by1], radius=16, fill=(176, 188, 208, 255))
    # nose cone
    d.polygon([(bx0, by0 + 6), (bx1, by0 + 6), (cx, top)], fill=(230, 236, 246, 255))
    d.polygon([(cx, top), (bx1, by0 + 6), (cx + 6, by0 + 6)], fill=(196, 206, 224, 255))
    # window
    d.ellipse([cx - 17, by0 + 38, cx + 17, by0 + 72], fill=(20, 30, 50, 255), outline=(120, 180, 235, 255), width=4)
    # engine nozzle
    d.polygon([(bx0 + 12, by1), (bx1 - 12, by1), (bx1 - 22, by1 + 16), (bx0 + 22, by1 + 16)],
              fill=(70, 80, 98, 255))

    img.alpha_composite(layer)


def rounded_chip(d, xy, text, fnt, accent):
    x, y = xy
    pad = (16, 9)
    tb = d.textbbox((0, 0), text, font=fnt)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    w, h = tw + pad[0] * 2 + 18, th + pad[1] * 2
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=CHIP_BG, outline=CHIP_BD, width=1)
    r = 5
    dcx, dcy = x + pad[0] + r, y + h // 2
    d.ellipse([dcx - r, dcy - r, dcx + r, dcy + r], fill=accent)
    d.text((dcx + r + 8, y + pad[1] - tb[1]), text, font=fnt, fill=WHITE)
    return w, h


def build(suffix, cfg):
    img = vertical_gradient(W, H, (7, 10, 22), (3, 4, 10)).convert("RGBA")
    starfield(img)
    # nebula glows
    img.alpha_composite(radial_glow(W, H, 150, -40, 420, PURPLE, 40))
    img.alpha_composite(radial_glow(W, H, 1120, 660, 420, BLUE, 45))
    # earth horizon arc at bottom
    d0 = ImageDraw.Draw(img)
    d0.ellipse([-420, H - 92, W + 420, H + 560], fill=(10, 20, 44, 255))
    d0.ellipse([-420, H - 86, W + 420, H + 566], outline=(70, 150, 230, 110), width=5)

    draw_rocket(img)

    d = ImageDraw.Draw(img)
    # top accent rule
    d.rectangle([0, 0, W, 6], fill=BLUE)

    LX = 76
    # eyebrow
    f_eyebrow = font("arialbd.ttf", 25)
    d.text((LX, 92), "NASDAQ : SPCX  ·  IPO DEEP DIVE", font=f_eyebrow, fill=BLUE)
    # wordmark
    f_big = font("arialbd.ttf", 104)
    d.text((LX, 136), "SPACEX", font=f_big, fill=WHITE)
    d.text((LX, 244), "IPO 2026", font=f_big, fill=PURPLE)
    # localized subtitle
    f_sub = font(cfg["font"], 33)
    d.text((LX, 386), cfg["sub"], font=f_sub, fill=DIM)

    # chips row
    f_chip = font("arialbd.ttf", 23)
    cxp, cy = LX, 462
    accents = [BLUE, FLAME, PURPLE]
    for i, c in enumerate(CHIPS):
        w, _ = rounded_chip(d, (cxp, cy), c, f_chip, accents[i])
        cxp += w + 16

    # footer
    f_brand = font("arialbd.ttf", 26)
    f_meta = font("arial.ttf", 21)
    d.text((LX, H - 72), "luckyplz.com", font=f_brand, fill=WHITE)
    meta = "SPACE TECH · 2026.06.10"
    mb = d.textbbox((0, 0), meta, font=f_meta)
    d.text((W - 70 - (mb[2] - mb[0]), H - 68), meta, font=f_meta, fill=DIM)

    out = OG / f"spacex-ipo-2026{suffix}.png"
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"  wrote {out.name}  ({out.stat().st_size // 1024} KB)")


def main():
    OG.mkdir(parents=True, exist_ok=True)
    print("Generating SpaceX IPO OG images:")
    for suffix, cfg in LANGS.items():
        build(suffix, cfg)
    print("done.")


if __name__ == "__main__":
    main()
