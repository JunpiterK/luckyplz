#!/usr/bin/env python3
"""Generate the flagship 1200x630 OG image for luckyplz.com (site face).

Design language mirrors the live homepage:
  - deep-space #0A0A1A gradient + star field + nebula glows
  - glowing 4-leaf clover (the brand mark)
  - "LUCKY PLEASE!" wordmark in Orbitron Black with the exact .logo
    gradient (--primary #FF6B35 -> --accent #FFE66D -> --secondary #00D9FF)
  - KR tagline + EN game-roster line
  - a row of 8 hand-drawn mini game tiles (roulette / ladder / lotto /
    team / dice / pacman / tetris / rocket) = lucky games + retro arcade
  - bottom mono strip: domain + 4-language + free/no-login badges

Output: public/assets/og-image.png (overwrites the old card; bump the
?v= stamp on the og:image/twitter:image tags so scrapers re-fetch).
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "assets" / "og-image.png"
FDIR = ROOT / "scripts" / "og-fonts"
WINF = Path("C:/Windows/Fonts")

W, H = 1200, 630

# brand palette (public/index.html :root)
ORANGE = (255, 107, 53)    # --primary
YELLOW = (255, 230, 109)   # --accent
CYAN   = (0, 217, 255)     # --secondary
PINK   = (255, 51, 102)    # --danger
GREEN  = (0, 255, 136)     # --success
WHITE  = (244, 247, 252)
DIM    = (168, 178, 196)
TILE_BG = (16, 20, 36)
TILE_BD = (58, 70, 102)


def font_orbitron(size):
    f = ImageFont.truetype(str(FDIR / "Orbitron-var.ttf"), size)
    f.set_variation_by_name("Black")
    return f


def font_pret_xb(size):
    return ImageFont.truetype(str(FDIR / "Pretendard-ExtraBold.otf"), size)


def font_pret_b(size):
    return ImageFont.truetype(str(FDIR / "Pretendard-Bold.otf"), size)


def font_mono(size):
    return ImageFont.truetype(str(FDIR / "JetBrainsMono-Bold.ttf"), size)


def vgrad(top, bot):
    base = Image.new("RGB", (W, H), top)
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), int(y / (H - 1) * 255))
    return Image.composite(Image.new("RGB", (W, H), bot), base, g.resize((W, H))).convert("RGBA")


def hgrad_strip(width, height, stops):
    """Horizontal multi-stop gradient image. stops = [(pos0..1, rgb), ...]"""
    img = Image.new("RGB", (width, height))
    px = img.load()
    for x in range(width):
        t = x / max(1, width - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                lt = (t - p0) / max(1e-6, p1 - p0)
                c = tuple(int(c0[k] + (c1[k] - c0[k]) * lt) for k in range(3))
                break
        else:
            c = stops[-1][1]
        for y in range(height):
            px[x, y] = c
    return img


def glow(img, cx, cy, r, color, alpha):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (alpha,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(r // 2)))


def sparkle(d, x, y, r, color, alpha=255):
    """4-point star sparkle."""
    c = color + (alpha,)
    d.polygon([(x, y - r), (x + r * 0.28, y - r * 0.28), (x + r, y),
               (x + r * 0.28, y + r * 0.28), (x, y + r),
               (x - r * 0.28, y + r * 0.28), (x - r, y),
               (x - r * 0.28, y - r * 0.28)], fill=c)


# ------------------------------------------------------------------ clover --
def _leaf_image(r, fill):
    """One heart-shaped leaf on a roomy canvas: point at canvas center,
    leaf extending straight up. Canvas is 8r so any rotation fits."""
    LS = int(r * 8)
    c = LS / 2
    leaf = Image.new("RGBA", (LS, LS), (0, 0, 0, 0))
    d = ImageDraw.Draw(leaf)
    ly = c - r * 1.9                  # lobe centers height
    for sgn in (-1, 1):
        ox = c + sgn * r * 0.62
        d.ellipse([ox - r, ly - r, ox + r, ly + r], fill=fill)
    d.polygon([(c - r * 1.38, ly + r * 0.42), (c + r * 1.38, ly + r * 0.42), (c, c)], fill=fill)
    return leaf


def draw_clover(img, cx, cy, s):
    """Glossy 4-leaf clover, brand mark. s = lobe radius (overall radius ~3s)."""
    glow(img, cx, cy, int(s * 3.0), GREEN, 64)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    leaf_main = (46, 204, 113)
    leaf_dark = (27, 158, 84)

    # stem (behind leaves) — short curve to bottom-right, clear of the title
    d.line([(cx + 2, cy + s * 0.8), (cx + s * 0.7, cy + s * 2.4),
            (cx + s * 1.15, cy + s * 2.6)], fill=leaf_dark, width=max(6, int(s * 0.3)), joint="curve")

    leaf = _leaf_image(s, leaf_main)
    LS = leaf.size[0]
    # heart point sits at canvas center; rotate about it, then pin near (cx, cy)
    # with a small outward offset so the four leaves separate cleanly.
    for ang in (45, 135, 225, 315):
        rot = leaf.rotate(ang, resample=Image.BICUBIC, center=(LS / 2, LS / 2))
        a = math.radians(-ang + 90)   # screen-space leaf direction after rotation
        ox = cx + math.cos(a) * s * 0.22
        oy = cy + math.sin(a) * s * 0.22
        layer.alpha_composite(rot, (int(ox - LS / 2), int(oy - LS / 2)))

    # creases — from center out along each leaf axis (kept inside the leaves)
    for ang in (45, 135, 225, 315):
        a = math.radians(-ang + 90)   # leaf axes after rotation
        d.line([(cx + math.cos(a) * s * 0.35, cy + math.sin(a) * s * 0.35),
                (cx + math.cos(a) * s * 2.1, cy + math.sin(a) * s * 2.1)],
               fill=leaf_dark, width=max(3, int(s * 0.09)))

    # glossy highlight on the upper-left leaf
    hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dh = ImageDraw.Draw(hl)
    a = math.radians(-135 + 90)
    hx, hy = cx + math.cos(a) * s * 1.7, cy + math.sin(a) * s * 1.7
    dh.ellipse([hx - s * 0.55, hy - s * 0.35, hx + s * 0.55, hy + s * 0.35], fill=(255, 255, 255, 92))
    layer.alpha_composite(hl.filter(ImageFilter.GaussianBlur(2)))

    # tiny sparkle on the upper-right leaf
    dd = ImageDraw.Draw(layer)
    sparkle(dd, cx + s * 1.45, cy - s * 1.6, int(s * 0.34), (255, 255, 255), 230)

    img.alpha_composite(layer)


# -------------------------------------------------------------- mini motifs --
def t_roulette(d, cx, cy):
    cy += 3
    r = 28
    cols = [(235, 64, 84), (26, 30, 46)] * 3
    for i, c in enumerate(cols):
        d.pieslice([cx - r, cy - r, cx + r, cy + r], i * 60 - 90, (i + 1) * 60 - 90, fill=c)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=YELLOW, width=4)
    d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=YELLOW)
    d.polygon([(cx - 6, cy - r - 7), (cx + 6, cy - r - 7), (cx, cy - r + 4)], fill=WHITE)


def t_ladder(d, cx, cy):
    for x in (cx - 18, cx + 18):
        d.rounded_rectangle([x - 4, cy - 30, x + 4, cy + 30], 4, fill=CYAN)
    for y in (cy - 17, cy, cy + 17):
        d.rounded_rectangle([cx - 14, y - 3, cx + 14, y + 3], 3, fill=YELLOW)


def t_lotto(d, cx, cy, f):
    r = 28
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(61, 214, 140))
    d.ellipse([cx - r + 6, cy - r + 5, cx - r + 17, cy - r + 14], fill=(255, 255, 255, 120))
    tb = d.textbbox((0, 0), "7", font=f)
    d.text((cx - (tb[2] - tb[0]) / 2, cy - (tb[3] - tb[1]) / 2 - tb[1]), "7", font=f, fill=(12, 16, 26))


def t_team(d, cx, cy, f):
    d.ellipse([cx - 30, cy - 26, cx - 6, cy - 2], fill=(93, 193, 255))
    d.ellipse([cx + 6, cy + 2, cx + 30, cy + 26], fill=ORANGE)
    tb = d.textbbox((0, 0), "VS", font=f)
    d.text((cx - (tb[2] - tb[0]) / 2, cy - (tb[3] - tb[1]) / 2 - tb[1]), "VS", font=f, fill=YELLOW)


def t_dice(d, cx, cy):
    s = 52
    d.rounded_rectangle([cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2], 12,
                        fill=WHITE, outline=(190, 198, 214), width=2)
    pr = 5
    for fx, fy in [(-.25, -.25), (0, 0), (.25, .25), (.25, -.25), (-.25, .25)]:
        d.ellipse([cx + fx * s - pr, cy + fy * s - pr, cx + fx * s + pr, cy + fy * s + pr], fill=(82, 60, 165))


def t_pacman(d, cx, cy):
    r = 26
    d.pieslice([cx - r - 6, cy - r, cx + r - 6, cy + r], 35, 325, fill=(255, 221, 51))
    for i in range(2):
        x = cx + 26 + i * 16
        d.ellipse([x - 5, cy - 5, x + 5, cy + 5], fill=(255, 235, 160))


def t_tetris(d, cx, cy):
    cs = 19
    cells = [(-1, -0.5), (0, -0.5), (1, -0.5), (0, 0.5)]
    for gx, gy in cells:
        x, y = cx + gx * cs, cy + gy * cs
        d.rounded_rectangle([x - cs / 2 + 1.5, y - cs / 2 + 1.5, x + cs / 2 - 1.5, y + cs / 2 - 1.5],
                            5, fill=(167, 139, 250))
        d.rounded_rectangle([x - cs / 2 + 4, y - cs / 2 + 4, x + cs / 2 - 6, y - cs / 2 + 8],
                            3, fill=(255, 255, 255, 70))


def t_rocket(d, cx, cy):
    d.polygon([(cx, cy - 30), (cx - 16, cy + 12), (cx + 16, cy + 12)], fill=(232, 238, 248))
    d.ellipse([cx - 8, cy - 12, cx + 8, cy + 4], fill=(18, 28, 48), outline=CYAN, width=3)
    d.polygon([(cx - 16, cy + 12), (cx - 26, cy + 24), (cx - 10, cy + 16)], fill=(190, 200, 218))
    d.polygon([(cx + 16, cy + 12), (cx + 26, cy + 24), (cx + 10, cy + 16)], fill=(190, 200, 218))
    d.polygon([(cx - 9, cy + 14), (cx + 9, cy + 14), (cx, cy + 32)], fill=ORANGE)


# -------------------------------------------------------------------- build --
def main():
    img = vgrad((17, 17, 42), (5, 5, 15))

    # nebula glows — cyan TL, orange BR, faint violet center
    glow(img, 150, 100, 320, CYAN, 26)
    glow(img, 1060, 540, 330, ORANGE, 30)
    glow(img, 600, 300, 420, (120, 95, 220), 16)

    d = ImageDraw.Draw(img)

    # star field
    rnd = random.Random(42)
    for _ in range(120):
        x, y = rnd.randint(8, W - 8), rnd.randint(8, H - 8)
        r = rnd.choice([1, 1, 1, 2])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rnd.randint(36, 150)))

    # colored sparkles framing the title zone
    sparkle(d, 178, 200, 11, YELLOW, 220)
    sparkle(d, 1030, 168, 13, CYAN, 220)
    sparkle(d, 1105, 300, 8, PINK, 200)
    sparkle(d, 95, 330, 8, GREEN, 190)
    sparkle(d, 940, 95, 7, ORANGE, 200)

    # brand clover
    draw_clover(img, W // 2, 88, 24)
    d = ImageDraw.Draw(img)

    # ---- wordmark with the exact site .logo gradient -----------------------
    title = "LUCKY PLEASE!"
    fsize = 92
    f_title = font_orbitron(fsize)
    while d.textbbox((0, 0), title, font=f_title)[2] > W - 140:
        fsize -= 2
        f_title = font_orbitron(fsize)
    tb = d.textbbox((0, 0), title, font=f_title)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    tx, ty = (W - tw) // 2 - tb[0], 158 - tb[1]

    # soft glow behind the wordmark
    gm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(gm).text((tx, ty), title, font=f_title, fill=255)
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    halo.paste(Image.new("RGBA", (W, H), (130, 190, 255, 90)), (0, 0), gm)
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(14)))

    # drop shadow then gradient fill through text mask
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((tx + 4, ty + 6), title, font=f_title, fill=(0, 0, 0, 170))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)))

    grad = hgrad_strip(W, H, [(0.0, ORANGE), (0.5, YELLOW), (1.0, CYAN)])
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).text((tx, ty), title, font=f_title, fill=255)
    img.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(img)

    # ---- taglines -----------------------------------------------------------
    kr = "커피·밥·벌칙, 누가 걸릴까?  운명에 맡겨!"
    f_kr = font_pret_xb(40)
    tb = d.textbbox((0, 0), kr, font=f_kr)
    d.text(((W - (tb[2] - tb[0])) / 2 - tb[0], 292 - tb[1]), kr, font=f_kr, fill=WHITE)

    en = "Roulette · Ladder · Lotto · Team Picker  +  Retro Arcade  ·  17 FREE GAMES"
    f_en = font_pret_b(26)
    tb = d.textbbox((0, 0), en, font=f_en)
    d.text(((W - (tb[2] - tb[0])) / 2 - tb[0], 348 - tb[1]), en, font=f_en, fill=DIM)

    # ---- game tile row ------------------------------------------------------
    TS, GAP, N = 92, 16, 8
    row_w = N * TS + (N - 1) * GAP
    x0, y0 = (W - row_w) // 2, 402
    f_ball = font_pret_xb(26)
    f_vs = font_pret_xb(20)
    accents = [YELLOW, CYAN, (61, 214, 140), (93, 193, 255), (167, 139, 250),
               (255, 221, 51), (167, 139, 250), ORANGE]
    motifs = [t_roulette, t_ladder,
              lambda dd, cx, cy: t_lotto(dd, cx, cy, f_ball),
              lambda dd, cx, cy: t_team(dd, cx, cy, f_vs),
              t_dice, t_pacman, t_tetris, t_rocket]
    for i, motif in enumerate(motifs):
        x = x0 + i * (TS + GAP)
        d.rounded_rectangle([x, y0, x + TS, y0 + TS], 20, fill=TILE_BG, outline=TILE_BD, width=2)
        motif(d, x + TS // 2, y0 + TS // 2)

    # ---- bottom mono strip --------------------------------------------------
    f_dom = font_mono(30)
    dom = "luckyplz.com"
    tb = d.textbbox((0, 0), dom, font=f_dom)
    d.text(((W - (tb[2] - tb[0])) / 2 - tb[0], 530 - tb[1]), dom, font=f_dom, fill=WHITE)

    f_meta = font_mono(19)
    meta = "KO · EN · JA · ZH      FREE      NO LOGIN      MOBILE & PC"
    tb = d.textbbox((0, 0), meta, font=f_meta)
    d.text(((W - (tb[2] - tb[0])) / 2 - tb[0], 576 - tb[1]), meta, font=f_meta, fill=(130, 142, 165))

    # brand gradient hairline along the very top
    img.paste(hgrad_strip(W, 6, [(0.0, ORANGE), (0.5, YELLOW), (1.0, CYAN)]), (0, 0))

    img.convert("RGB").save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
