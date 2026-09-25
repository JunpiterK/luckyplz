#!/usr/bin/env python3
"""Generate per-game 1200x630 OG images for every game on luckyplz.com.

Every game page previously shared the generic site OG. This produces a
distinct, game-themed card per game: dark gradient in the game's palette,
a drawn motif (wheel / ladder / tetrominoes / pacman / burger / rocket ...),
bilingual title block, PLAY FREE chip, and site branding.

Output: public/og/games/<slug>.png  (17 games)
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "og" / "games"
HERE = Path(__file__).resolve().parent
FONTS = Path("C:/Windows/Fonts")

W, H = 1200, 630
WHITE = (245, 247, 250)
DIM = (165, 175, 192)
CHIP_BG = (10, 13, 22)
CHIP_BD = (52, 64, 90)

# motif zone (right side)
MX, MY, MW, MH = 730, 80, 420, 440
MCX, MCY = MX + MW // 2, MY + MH // 2


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def vgrad(top, bot):
    base = Image.new("RGB", (W, H), top)
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), int(y / (H - 1) * 255))
    return Image.composite(Image.new("RGB", (W, H), bot), base, g.resize((W, H))).convert("RGBA")


def glow(img, cx, cy, r, color, alpha):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (alpha,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(r // 2)))


# ---------------------------------------------------------------- motifs ---
def m_roulette(d, img):
    r = 185
    cols = [(214, 48, 73), (24, 26, 36)] * 6
    for i, c in enumerate(cols):
        d.pieslice([MCX - r, MCY - r, MCX + r, MCY + r], i * 30 - 90, (i + 1) * 30 - 90, fill=c)
    d.ellipse([MCX - r, MCY - r, MCX + r, MCY + r], outline=(255, 206, 92), width=10)
    d.ellipse([MCX - 60, MCY - 60, MCX + 60, MCY + 60], fill=(18, 20, 30), outline=(255, 206, 92), width=6)
    d.ellipse([MCX - 14, MCY - 14, MCX + 14, MCY + 14], fill=(255, 206, 92))
    ba = math.radians(-54)
    bx, by = MCX + int(math.cos(ba) * (r - 34)), MCY + int(math.sin(ba) * (r - 34))
    d.ellipse([bx - 13, by - 13, bx + 13, by + 13], fill=WHITE)
    d.polygon([(MCX - 16, MY - 8), (MCX + 16, MY - 8), (MCX, MY + 26)], fill=(255, 206, 92))


def m_ladder(d, img):
    rnd = random.Random(7)
    rails = [MX + 60, MX + 210, MX + 360]
    for x in rails:
        d.rounded_rectangle([x - 7, MY + 10, x + 7, MY + MH - 10], 7, fill=(80, 200, 255))
    for i in range(7):
        y = MY + 40 + i * 55
        a = rnd.choice([0, 1])
        d.rounded_rectangle([rails[a] + 7, y - 6, rails[a + 1] - 7, y + 6], 6, fill=(255, 230, 109))
    # start/end dots
    for x, c in [(rails[0], (255, 107, 53)), (rails[1], (61, 214, 140)), (rails[2], (167, 139, 250))]:
        d.ellipse([x - 17, MY - 14, x + 17, MY + 20], fill=c)
        d.ellipse([x - 17, MY + MH - 20, x + 17, MY + MH + 14], outline=c, width=5)


def m_lotto(d, img):
    rnd = random.Random(3)
    cols = [(255, 107, 53), (61, 214, 140), (93, 193, 255), (255, 206, 92), (167, 139, 250), (255, 99, 132)]
    nums = ["7", "11", "23", "35", "42", "45"]
    f = font("arialbd.ttf", 40)
    pos = [(MX + 80, MY + 80), (MX + 230, MY + 50), (MX + 350, MY + 130),
           (MX + 110, MY + 230), (MX + 260, MY + 210), (MX + 200, MY + 350)]
    for (x, y), c, n in zip(pos, cols, nums):
        r = 56
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255, 90), width=4)
        d.ellipse([x - r + 12, y - r + 10, x - r + 34, y - r + 30], fill=(255, 255, 255, 110))
        tb = d.textbbox((0, 0), n, font=f)
        d.text((x - (tb[2] - tb[0]) / 2, y - (tb[3] - tb[1]) / 2 - tb[1]), n, font=f, fill=(15, 18, 28))


def m_team(d, img):
    """홍팀 vs 블루팀 3:3 팔짱 대치 — Blender Cycles 렌더 합성.

    원본: scripts/blender/team_scene.py → og-assets/team-scene-3d.png.
    수정하려면 그 씬 스크립트를 고치고 Blender 로 재렌더한다
    (C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P team_scene.py).
    """
    scene = Image.open(HERE / "og-assets" / "team-scene-3d.png").convert("RGBA")
    b = scene.getbbox()
    scene = scene.crop(b)
    w = 500
    h = round(scene.height * w / scene.width)
    scene = scene.resize((w, h), Image.LANCZOS)
    img.paste(scene, (MCX - w // 2 - 6, MCY - h // 2 + 10), scene)

def m_dice(d, img):
    def die(x, y, s, c, pips):
        d.rounded_rectangle([x, y, x + s, y + s], 26, fill=c, outline=(255, 255, 255, 70), width=4)
        pr = s // 10
        grid = {1: [(.5, .5)], 3: [(.25, .25), (.5, .5), (.75, .75)],
                5: [(.25, .25), (.75, .25), (.5, .5), (.25, .75), (.75, .75)]}
        for fx, fy in grid[pips]:
            px, py = x + fx * s, y + fy * s
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(20, 22, 32))
    die(MX + 30, MY + 110, 200, (245, 247, 250), 5)
    die(MX + 215, MY + 215, 165, (167, 139, 250), 3)


def m_snake(d, img):
    path = [(0, 3), (1, 3), (2, 3), (2, 2), (2, 1), (3, 1), (4, 1), (4, 2), (4, 3), (5, 3)]
    cs = 56
    ox, oy = MX + 30, MY + 90
    for i, (gx, gy) in enumerate(path):
        sh = 200 - i * 9
        d.rounded_rectangle([ox + gx * cs + 3, oy + gy * cs + 3, ox + gx * cs + cs - 3, oy + gy * cs + cs - 3],
                            14, fill=(61, max(120, sh), 100))
    hx, hy = ox + path[-1][0] * cs, oy + path[-1][1] * cs
    d.ellipse([hx + 12, hy + 14, hx + 24, hy + 26], fill=(10, 14, 20))
    d.ellipse([hx + 32, hy + 14, hx + 44, hy + 26], fill=(10, 14, 20))
    ax, ay = ox + 6 * cs + cs // 2, oy + 1 * cs + cs // 2
    d.ellipse([ax - 22, ay - 22, ax + 22, ay + 22], fill=(255, 90, 110))
    d.rounded_rectangle([ax - 4, ay - 34, ax + 4, ay - 18], 4, fill=(61, 180, 100))


def m_pacman(d, img):
    r = 95
    px, py = MX + 110, MCY
    d.pieslice([px - r, py - r, px + r, py + r], 35, 325, fill=(255, 221, 51))
    d.ellipse([px - 18, py - 64, px + 6, py - 40], fill=(10, 12, 20))
    for i in range(3):
        x = px + 150 + i * 80
        d.ellipse([x - 14, py - 14, x + 14, py + 14], fill=(255, 230, 150))
    gx, gy, gr = MX + MW - 70, py, 62
    d.pieslice([gx - gr, gy - gr - 24, gx + gr, gy + gr], 180, 360, fill=(255, 99, 132))
    d.rectangle([gx - gr, gy - 24, gx + gr, gy + gr - 16], fill=(255, 99, 132))
    for i in range(4):
        bx = gx - gr + i * (gr // 2) + 8
        d.ellipse([bx, gy + gr - 34, bx + gr // 2, gy + gr + 2], fill=(255, 99, 132))
    for ex in (gx - 26, gx + 10):
        d.ellipse([ex, gy - 34, ex + 24, gy - 6], fill=WHITE)
        d.ellipse([ex + 10, gy - 24, ex + 22, gy - 12], fill=(40, 60, 200))


def m_tetris(d, img):
    cs = 62
    def cell(gx, gy, c):
        x, y = MX + 20 + gx * cs, MY + MH - (gy + 1) * cs
        d.rounded_rectangle([x + 3, y + 3, x + cs - 3, y + cs - 3], 10, fill=c)
        d.rounded_rectangle([x + 8, y + 8, x + cs - 14, y + 18], 6, fill=(255, 255, 255, 60))
    for gx in range(6): cell(gx, 0, (93, 193, 255))          # I row base
    for gx, gy in [(0, 1), (0, 2), (1, 1)]: cell(gx, gy, (255, 107, 53))   # L
    for gx, gy in [(2, 1), (3, 1), (2, 2), (3, 2)]: cell(gx, gy, (255, 206, 92))  # O
    for gx, gy in [(4, 1), (5, 1), (4, 2)]: cell(gx, gy, (61, 214, 140))   # J-ish
    for gx, gy in [(2, 4), (3, 4), (4, 4), (3, 5)]: cell(gx, gy, (167, 139, 250))  # T falling
    d.rounded_rectangle([MX + 20 + 3 * cs + 8, MY + 30, MX + 20 + 3 * cs + 14, MY + MH - 6 * cs], 3, fill=(255, 255, 255, 28))


def m_brick(d, img):
    cols = [(255, 99, 132), (255, 159, 64), (255, 206, 92)]
    bw, bh = 92, 36
    for row in range(3):
        for i in range(4):
            x = MX + 16 + i * (bw + 10) + (row % 2) * 18
            y = MY + 30 + row * (bh + 12)
            d.rounded_rectangle([x, y, x + bw, y + bh], 8, fill=cols[row])
    bx, by = MCX + 30, MCY + 80
    d.ellipse([bx - 16, by - 16, bx + 16, by + 16], fill=WHITE)
    d.line([bx - 60, by + 60, bx - 6, by + 6], fill=(255, 255, 255, 90), width=5)
    d.rounded_rectangle([MCX - 110, MY + MH - 40, MCX + 50, MY + MH - 12], 14, fill=(93, 193, 255))


def m_burger(d, img):
    cx = MCX; w = 320
    y = MY + 70
    d.pieslice([cx - w // 2, y, cx + w // 2, y + 170], 180, 360, fill=(240, 178, 92))
    rnd = random.Random(2)
    for _ in range(8):
        sx = cx - w // 2 + 40 + rnd.randint(0, w - 80); sy = y + 28 + rnd.randint(0, 36)
        d.ellipse([sx, sy, sx + 10, sy + 16], fill=(255, 240, 210))
    y += 88
    pts = [(cx - w // 2 + i * (w // 10), y + (14 if i % 2 else 28)) for i in range(11)]
    d.polygon([(cx - w // 2, y + 6)] + pts + [(cx + w // 2, y + 6), (cx + w // 2, y + 30), (cx - w // 2, y + 30)], fill=(120, 200, 80))
    y += 30
    d.rounded_rectangle([cx - w // 2 + 6, y, cx + w // 2 - 6, y + 26], 10, fill=(255, 206, 92))
    y += 24
    d.rounded_rectangle([cx - w // 2, y, cx + w // 2, y + 52], 22, fill=(141, 85, 49))
    y += 60
    d.rounded_rectangle([cx - w // 2 + 4, y, cx + w // 2 - 4, y + 44], 18, fill=(240, 178, 92))


def m_car(d, img):
    for i, lx in enumerate([MX + 40, MX + 180, MX + 320]):
        d.rounded_rectangle([lx, MY, lx + 8, MY + MH], 4, fill=(255, 255, 255, 36))
    for i in range(6):
        d.rounded_rectangle([MX + 113, MY + i * 80, MX + 121, MY + i * 80 + 44], 4, fill=(255, 255, 255, 60))
        d.rounded_rectangle([MX + 253, MY + 40 + i * 80, MX + 261, MY + 84 + i * 80], 4, fill=(255, 255, 255, 60))
    cx, cy = MX + 187, MCY + 40
    for wx, wy in [(-52, -62), (52, -62), (-52, 62), (52, 62)]:
        d.rounded_rectangle([cx + wx - 14, cy + wy - 26, cx + wx + 14, cy + wy + 26], 10, fill=(20, 24, 34))
    d.rounded_rectangle([cx - 48, cy - 95, cx + 48, cy + 95], 36, fill=(235, 64, 84))
    d.rounded_rectangle([cx - 34, cy - 48, cx + 34, cy - 6], 14, fill=(150, 210, 255))
    d.rounded_rectangle([cx - 34, cy + 22, cx + 34, cy + 56], 14, fill=(150, 210, 255))
    for i, sy in enumerate([cy - 150, cy - 190]):
        d.rounded_rectangle([cx - 6 - 26 * (i + 1), sy, cx + 6 - 26 * (i + 1), sy + 26], 4, fill=(255, 255, 255, 70 - i * 25))
        d.rounded_rectangle([cx - 6 + 26 * (i + 1), sy, cx + 6 + 26 * (i + 1), sy + 26], 4, fill=(255, 255, 255, 70 - i * 25))


def m_glory(d, img):
    """달리며 미는 두 러너 — Blender Cycles 렌더 합성.

    원본: scripts/blender/brawl_scene.py → og-assets/brawl-scene-3d.png.
    수정하려면 씬 스크립트를 고치고 Blender 로 재렌더한다
    (C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P brawl_scene.py).
    """
    scene = Image.open(HERE / "og-assets" / "brawl-scene-3d.png").convert("RGBA")
    b = scene.getbbox()
    scene = scene.crop(b)
    w = 500
    h = round(scene.height * w / scene.width)
    scene = scene.resize((w, h), Image.LANCZOS)
    img.paste(scene, (MCX - w // 2 - 6, MCY - h // 2 + 10), scene)

def m_dodge(d, img):
    rnd = random.Random(9)
    for _ in range(26):
        x, y = MX + rnd.randint(0, MW), MY + rnd.randint(0, MH)
        r = rnd.choice([1, 1, 2])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rnd.randint(60, 160)))
    for ax, ay, ar in [(MX + 90, MY + 70, 34), (MX + 320, MY + 120, 26), (MX + 200, MY + 40, 18)]:
        d.ellipse([ax - ar, ay - ar, ax + ar, ay + ar], fill=(120, 110, 130))
        d.ellipse([ax - ar // 2, ay - ar // 2, ax, ay], fill=(90, 82, 100))
    for bx, by in [(MX + 150, MY + 180), (MX + 290, MY + 230), (MX + 110, MY + 280)]:
        d.rounded_rectangle([bx - 4, by, bx + 4, by + 36], 4, fill=(0, 217, 255))
    sx, sy = MCX, MY + MH - 90
    glow(img, sx, sy + 64, 50, (255, 160, 60), 150)
    d.polygon([(sx, sy - 64), (sx - 44, sy + 44), (sx + 44, sy + 44)], fill=(230, 238, 250))
    d.polygon([(sx, sy - 64), (sx + 44, sy + 44), (sx + 8, sy + 44)], fill=(190, 200, 218))
    d.ellipse([sx - 14, sy - 16, sx + 14, sy + 12], fill=(20, 30, 50), outline=(0, 217, 255), width=4)
    d.polygon([(sx - 16, sy + 44), (sx + 16, sy + 44), (sx, sy + 86)], fill=(255, 200, 120))


def m_lander(d, img):
    d.rounded_rectangle([MCX - 130, MY + MH - 34, MCX + 130, MY + MH - 14], 8, fill=(80, 92, 116))
    f = font("arialbd.ttf", 22)
    d.text((MCX - 14, MY + MH - 64), "H", font=f, fill=(160, 175, 200))
    cx, top = MCX, MY + 40
    bw, bh, nh = 64, 150, 56
    glow(img, cx, top + nh + bh + 70, 70, (255, 160, 60), 160)
    d.polygon([(cx - bw // 2, top + nh + bh - 6), (cx - bw // 2 - 34, top + nh + bh + 54)], fill=None)
    for s in (-1, 1):
        d.line([cx + s * (bw // 2 - 4), top + nh + bh - 10, cx + s * (bw // 2 + 30), top + nh + bh + 52], fill=(150, 162, 184), width=9)
        d.line([cx + s * (bw // 2 + 30), top + nh + bh + 52, cx + s * (bw // 2 + 44), top + nh + bh + 52], fill=(150, 162, 184), width=9)
    d.rounded_rectangle([cx - bw // 2, top + nh - 8, cx + bw // 2, top + nh + bh], 16, fill=(214, 222, 236))
    d.polygon([(cx - bw // 2, top + nh + 4), (cx + bw // 2, top + nh + 4), (cx, top)], fill=(230, 236, 246))
    d.ellipse([cx - 15, top + nh + 28, cx + 15, top + nh + 58], fill=(20, 30, 50), outline=(120, 180, 235), width=4)
    d.polygon([(cx - 18, top + nh + bh), (cx + 18, top + nh + bh), (cx, top + nh + bh + 56)], fill=(255, 200, 120))


def m_merge(d, img):
    p1x, p1y, r1 = MX + 100, MCY - 60, 64
    d.ellipse([p1x - r1, p1y - r1, p1x + r1, p1y + r1], fill=(93, 193, 255))
    d.ellipse([p1x - r1 + 14, p1y - 20, p1x - r1 + 52, p1y + 6], fill=(140, 215, 255))
    p2x, p2y, r2 = MX + 240, MCY + 60, 50
    d.ellipse([p2x - r2, p2y - r2, p2x + r2, p2y + r2], fill=(255, 159, 64))
    f = font("arialbd.ttf", 54)
    d.text((MX + 152, MCY + 116), "+", font=f, fill=DIM)
    d.polygon([(MX + 300, MCY - 6), (MX + 340, MCY - 26), (MX + 340, MCY + 14)], fill=DIM)
    p3x, p3y, r3 = MX + MW - 80, MCY, 86
    glow(img, p3x, p3y, r3 + 26, (167, 139, 250), 90)
    d.ellipse([p3x - r3, p3y - r3, p3x + r3, p3y + r3], fill=(167, 139, 250))
    d.ellipse([p3x - r3 - 36, p3y - 16, p3x + r3 + 36, p3y + 22], outline=(255, 206, 92), width=10)
    d.ellipse([p3x - r3 + 20, p3y - r3 + 18, p3x - r3 + 58, p3y - r3 + 44], fill=(206, 188, 255))


def m_orbit(d, img):
    """지구 + 타원 궤도 + 위성. 이 게임의 한 장면이 그대로 요약이다."""
    rnd = random.Random(23)
    for _ in range(30):
        x, y = MX + rnd.randint(0, MW), MY + rnd.randint(0, MH)
        r = rnd.choice([1, 1, 2])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rnd.randint(60, 150)))
    # 궤도 두 개 — 안쪽은 원, 바깥은 타원(아직 다듬는 중)
    d.ellipse([MCX - 150, MCY - 150, MCX + 150, MCY + 150], outline=(79, 227, 193), width=3)
    d.ellipse([MCX - 196, MCY - 118, MCX + 196, MCY + 118], outline=(240, 165, 55), width=3)
    # 지구
    er = 74
    glow(img, MCX, MCY, er + 30, (60, 140, 220), 80)
    d.ellipse([MCX - er, MCY - er, MCX + er, MCY + er], fill=(21, 74, 120))
    d.ellipse([MCX - er + 16, MCY - 34, MCX - er + 74, MCY + 10], fill=(52, 140, 96))
    d.ellipse([MCX + 4, MCY + 14, MCX + 52, MCY + 48], fill=(52, 140, 96))
    d.ellipse([MCX - er, MCY - er, MCX + er, MCY + er], outline=(120, 190, 245), width=3)
    # 위성 두 기
    for sx, sy in [(MCX + 150, MCY), (MCX - 106, MCY - 106)]:
        d.rounded_rectangle([sx - 11, sy - 8, sx + 11, sy + 8], 4, fill=(226, 232, 242))
        d.rectangle([sx - 34, sy - 5, sx - 15, sy + 5], fill=(30, 48, 110))
        d.rectangle([sx + 15, sy - 5, sx + 34, sy + 5], fill=(30, 48, 110))
    # 원지점 표식
    d.ellipse([MCX + 190 - 9, MCY - 9, MCX + 190 + 9, MCY + 9], outline=(240, 165, 55), width=3)


def m_bingo(d, img):
    cs = 64
    ox, oy = MX + 40, MY + 60
    f = font("arialbd.ttf", 30)
    rnd = random.Random(11)
    daub = {(0, 1), (1, 1), (2, 1), (1, 0), (1, 2), (2, 3)}
    for gy in range(4):
        for gx in range(4):
            x, y = ox + gx * cs, oy + gy * cs
            d.rounded_rectangle([x + 3, y + 3, x + cs - 3, y + cs - 3], 10,
                                fill=(24, 28, 42), outline=(70, 84, 116), width=2)
            if (gx, gy) in daub:
                d.ellipse([x + 10, y + 10, x + cs - 10, y + cs - 10], fill=(255, 99, 132, 220))
            else:
                n = str(rnd.randint(1, 75))
                tb = d.textbbox((0, 0), n, font=f)
                d.text((x + cs / 2 - (tb[2] - tb[0]) / 2, y + cs / 2 - (tb[3] - tb[1]) / 2 - tb[1]), n, font=f, fill=DIM)
    for bx, by, c in [(MX + MW - 80, MY + 90, (61, 214, 140)), (MX + MW - 50, MY + 210, (255, 206, 92))]:
        d.ellipse([bx - 36, by - 36, bx + 36, by + 36], fill=c)
        tb = d.textbbox((0, 0), "B", font=f)
        d.text((bx - (tb[2] - tb[0]) / 2, by - (tb[3] - tb[1]) / 2 - tb[1]), "B", font=f, fill=(15, 18, 28))


def m_quiz(d, img):
    bx0, by0, bx1, by1 = MX + 60, MY + 20, MX + MW - 60, MY + 240
    d.rounded_rectangle([bx0, by0, bx1, by1], 34, fill=(28, 24, 52), outline=(167, 139, 250), width=4)
    d.polygon([(bx0 + 60, by1 - 2), (bx0 + 130, by1 - 2), (bx0 + 70, by1 + 50)], fill=(28, 24, 52))
    f = font("arialbd.ttf", 130)
    tb = d.textbbox((0, 0), "?", font=f)
    d.text(((bx0 + bx1) / 2 - (tb[2] - tb[0]) / 2, (by0 + by1) / 2 - (tb[3] - tb[1]) / 2 - tb[1]), "?", font=f, fill=(167, 139, 250))
    fb = font("arialbd.ttf", 30)
    for i, (label, c) in enumerate([("A", (61, 214, 140)), ("B", (255, 107, 53))]):
        y = MY + 320 + i * 64
        d.rounded_rectangle([MX + 70, y, MX + MW - 70, y + 50], 25, fill=(20, 24, 38), outline=c, width=3)
        d.ellipse([MX + 82, y + 9, MX + 114, y + 41], fill=c)
        tb = d.textbbox((0, 0), label, font=fb)
        d.text((MX + 98 - (tb[2] - tb[0]) / 2, y + 25 - (tb[3] - tb[1]) / 2 - tb[1]), label, font=fb, fill=(15, 18, 28))



def m_balloon(d, img):
    """풍선 룰렛 — 크기가 커지는 풍선 3개 + 마지막은 파열 파편."""
    balloons = [(MX + 70, MY + 240, 46), (MX + 190, MY + 210, 66), (MX + 330, MY + 170, 92)]
    for x, y, r in balloons:
        d.ellipse([x - r, y - r * 1.18, x + r, y + r * 1.02], fill=(255, 92, 122))
        d.ellipse([x - r, y - r * 1.18, x + r, y + r * 1.02], outline=(255, 255, 255, 70), width=3)
        d.ellipse([x - r + int(r * .25), y - r + int(r * .1), x - r + int(r * .58), y - r + int(r * .62)],
                  fill=(255, 255, 255, 90))
        d.polygon([(x - 8, y + r), (x + 8, y + r), (x, y + r + 16)], fill=(217, 42, 78))
        d.line([(x, y + r + 16), (x - 6, y + r + 44), (x + 4, y + r + 70)], fill=(255, 255, 255, 90), width=3)
    # 파열 파편 (우상단)
    import math
    cx, cy = MX + 440, MY + 90
    for i in range(10):
        a = i / 10 * 6.283
        x1 = cx + math.cos(a) * 22; y1 = cy + math.sin(a) * 22
        x2 = cx + math.cos(a) * (52 + (i % 3) * 12); y2 = cy + math.sin(a) * (52 + (i % 3) * 12)
        d.line([(x1, y1), (x2, y2)], fill=(255, 206, 92), width=6)


def m_bubble(d, img):
    """버블 버스트 — 벌집 격자로 매달린 광택 버블 + 벽 튕김 조준선 + 발사대 + 터지는 링."""
    import math
    cols = [(255, 77, 106), (255, 210, 63), (61, 220, 132), (61, 139, 255), (176, 107, 255)]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    r = 30
    row_h = int(2 * r * 0.866)

    def ball(cx, cy, c, rr=r):
        g.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=c + (255,), outline=(16, 10, 30, 255), width=3)
        dk = tuple(int(v * .62) for v in c)
        g.chord([cx - rr + 3, cy - rr + 3, cx + rr - 3, cy + rr - 3], 20, 160, fill=dk + (150,))
        g.ellipse([cx - rr * .62, cy - rr * .66, cx - rr * .05, cy - rr * .28], fill=(255, 255, 255, 190))

    pat = [[0, 3, 3, 1, 4, 2], [3, 1, 1, 4, 2], [0, 0, 1, 4, 3, 2], [None, 0, 2, None, 3]]
    x0, y0 = MX + 58 + r, MY + 6 + r
    for ri, row in enumerate(pat):
        for ci, k in enumerate(row):
            if k is None:
                continue
            cx = x0 + ci * 2 * r + (r if ri % 2 else 0)
            ball(cx, y0 + ri * row_h, cols[k])
    # 터지는 링 + 파편 (위치는 아래 조준선 끝)
    px, py = x0 + 1 * 2 * r + r, y0 + 3 * row_h
    lx, ly = MCX - 40, MY + MH - 30
    wall = MX + MW - 6
    px = wall - (70 + 6) * (wall - lx) / (ly - py - 70) - 30
    for k in range(3):
        rr = 36 + k * 16
        g.ellipse([px - rr, py - rr, px + rr, py + rr], outline=(255, 255, 255, 150 - k * 45), width=4 - k)
    for i in range(10):
        a = i / 10 * 6.283
        g.ellipse([px + math.cos(a) * 64 - 5, py + math.sin(a) * 64 - 5, px + math.cos(a) * 64 + 5, py + math.sin(a) * 64 + 5],
                  fill=cols[1] + (230,))
    # 발사대 + 벽 튕김 조준선
    lx, ly = MCX - 40, MY + MH - 30
    wall = MX + MW - 6
    by = py + 70
    tx, ty = wall - (by - py + 6) * (wall - lx) / (ly - by), py + 6
    for (ax, ay), (bx, byy) in (((lx, ly), (wall, by)), ((wall, by), (tx, ty))):
        n = int(math.hypot(bx - ax, byy - ay) / 20)
        for j in range(1, n):
            u = j / n
            qx, qy = ax + (bx - ax) * u, ay + (byy - ay) * u
            g.ellipse([qx - 4, qy - 4, qx + 4, qy + 4], fill=(61, 220, 132, 220))
    g.rectangle([wall + 2, MY, wall + 6, MY + MH], fill=(95, 227, 255, 120))
    g.pieslice([lx - 78, ly - 40, lx + 78, ly + 116], 180, 360, fill=(246, 231, 198, 255), outline=(16, 10, 30, 255), width=3)
    ball(lx, ly - 6, cols[2], 32)
    img.alpha_composite(lay)


def m_ludo(d, img):
    """루도 — 4색 기지·십자 길·가운데 삼각 집의 미니 판 + 광택 말 + 주사위."""
    cols = [(229, 57, 80), (31, 174, 91), (244, 180, 26), (45, 123, 229)]
    S = 400
    u = S / 15
    ox, oy = MX + (MW - S) // 2 + 6, MY + (MH - S) // 2 + 6
    # 원목 테두리 + 상아 판
    d.rounded_rectangle([ox - 14, oy - 14, ox + S + 14, oy + S + 14], 26, fill=(110, 68, 34))
    d.rounded_rectangle([ox - 6, oy - 6, ox + S + 6, oy + S + 6], 18, fill=(70, 40, 18))
    d.rounded_rectangle([ox, oy, ox + S, oy + S], 12, fill=(240, 232, 214))
    P = lambda c, r: (ox + c * u, oy + r * u)
    # 기지(좌하 빨강·좌상 초록·우상 노랑·우하 파랑)
    bases = [(0, 9), (0, 0), (9, 0), (9, 9)]
    for (bx, by), col in zip(bases, cols):
        x0, y0 = P(bx, by)
        d.rounded_rectangle([x0 + 3, y0 + 3, x0 + 6 * u - 3, y0 + 6 * u - 3], 14, fill=col)
        d.rounded_rectangle([x0 + u, y0 + u, x0 + 5 * u, y0 + 5 * u], 12, fill=(252, 248, 240))
        for tx, ty in [(2, 2), (4, 2), (2, 4), (4, 4)]:
            cx, cy = P(bx + tx, by + ty)
            d.ellipse([cx - u * .62, cy - u * .62, cx + u * .62, cy + u * .62], fill=col)
    # 길 칸
    def cell(c, r, fill):
        x0, y0 = P(c, r)
        d.rounded_rectangle([x0 + 1.5, y0 + 1.5, x0 + u - 1.5, y0 + u - 1.5], 4, fill=fill)
    for r in range(15):
        for c in range(15):
            inarm = (6 <= c <= 8 and (r <= 5 or r >= 9)) or (6 <= r <= 8 and (c <= 5 or c >= 9))
            if inarm:
                cell(c, r, (255, 255, 255))
    for k in range(5):
        cell(7, 13 - k, cols[0]); cell(1 + k, 7, cols[1]); cell(7, 1 + k, cols[2]); cell(13 - k, 7, cols[3])
    cell(6, 13, cols[0]); cell(1, 6, cols[1]); cell(8, 1, cols[2]); cell(13, 8, cols[3])
    # 가운데 집
    c0 = P(7.5, 7.5)
    tris = [((6, 9), (9, 9)), ((6, 6), (6, 9)), ((6, 6), (9, 6)), ((9, 6), (9, 9))]
    for (a, b), col in zip(tris, cols):
        d.polygon([P(*a), P(*b), c0], fill=col)
    d.ellipse([c0[0] - u * .55, c0[1] - u * .55, c0[0] + u * .55, c0[1] + u * .55], fill=(242, 193, 78))

    # 광택 말
    def pawn(cx, by, s, col):
        dk = tuple(int(v * .6) for v in col)
        lt = tuple(min(255, int(v + (255 - v) * .5)) for v in col)
        d.ellipse([cx - s * .40, by - s * .02, cx + s * .40, by + s * .16], fill=(0, 0, 0, 90))
        d.ellipse([cx - s * .37, by - s * .12, cx + s * .37, by + s * .12], fill=dk)
        d.ellipse([cx - s * .37, by - s * .16, cx + s * .37, by + s * .08], fill=col)
        d.polygon([(cx - s * .27, by - s * .04), (cx - s * .1, by - s * .55), (cx + s * .1, by - s * .55), (cx + s * .27, by - s * .04)], fill=col)
        d.polygon([(cx - s * .2, by - s * .06), (cx - s * .08, by - s * .5), (cx - s * .02, by - s * .5), (cx - s * .1, by - s * .06)], fill=lt)
        d.ellipse([cx - s * .17, by - s * .6, cx + s * .17, by - s * .5], fill=dk)
        d.ellipse([cx - s * .21, by - s * .95, cx + s * .21, by - s * .53], fill=col)
        d.ellipse([cx - s * .13, by - s * .88, cx - s * .02, by - s * .8], fill=(255, 255, 255))
    s = u * 1.25
    pawn(*P(6.5, 11.7), s, cols[0])
    pawn(*P(2.5, 6.7), s, cols[1])
    pawn(*P(12.5, 6.7), s, cols[3])
    pawn(*P(8.5, 3.7), s, cols[2])
    # 주사위(우하 코너에 걸쳐)
    dx, dy, ds = ox + S - 40, oy + S - 52, 92
    d.rounded_rectangle([dx + 6, dy + 10, dx + ds + 6, dy + ds + 10], 20, fill=(0, 0, 0, 110))
    d.rounded_rectangle([dx, dy, dx + ds, dy + ds], 20, fill=(250, 246, 238), outline=(200, 190, 172), width=3)
    for px, py in [(.27, .27), (.73, .27), (.27, .5), (.73, .5), (.27, .73), (.73, .73)]:
        cx, cy = dx + ds * px, dy + ds * py
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(26, 26, 36))


def m_reversi(d, img):
    """리버시 — 호두나무 틀 + 녹색 펠트 8×8, 광택 흑백 돌, 뒤집히는 중인 돌 하나."""
    SS = 2                       # 2배로 그린 뒤 줄여 가장자리를 매끈하게
    S = 404
    bx, by = MX + (MW - S) // 2, MY + (MH - S) // 2 + 6
    lay = Image.new("RGBA", (S * SS + 80, S * SS + 80), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    o = 40
    fr = int(S * .058) * SS
    # 그림자 + 틀
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([o + 10, o + 26, o + S * SS + 10, o + S * SS + 26], 28, fill=(0, 0, 0, 170))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    g.rounded_rectangle([o, o, o + S * SS, o + S * SS], 28, fill=(92, 54, 26))
    rnd = random.Random(7)
    for _ in range(170):
        y = o + rnd.random() * S * SS
        a = rnd.randint(18, 60)
        col = (40, 18, 6, a) if rnd.random() < .65 else (255, 200, 140, a // 3)
        pts = [(o + x, y + math.sin(x * .01 + rnd.random()) * 3) for x in range(0, S * SS, 24)]
        g.line(pts, fill=col, width=rnd.randint(1, 3))
    x0 = o + fr
    w = S * SS - 2 * fr
    g.rectangle([x0 - 4, x0 - 4, x0 + w + 4, x0 + w + 4], fill=(20, 10, 4))
    g.rectangle([x0, x0, x0 + w, x0 + w], fill=(18, 108, 64))
    cell = w / 8
    for k in range(9):
        p = x0 + k * cell
        g.line([(p, x0), (p, x0 + w)], fill=(6, 50, 28), width=3)
        g.line([(x0, p), (x0 + w, p)], fill=(6, 50, 28), width=3)
    for a_, b_ in ((2, 2), (6, 2), (2, 6), (6, 6)):
        cx, cy = x0 + a_ * cell, x0 + b_ * cell
        g.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(6, 40, 22))
    inl = fr * .42
    g.rectangle([x0 - inl, x0 - inl, x0 + w + inl, x0 + w + inl], outline=(214, 178, 106), width=3)
    pos = ["........",
           "........",
           "..BW....",
           "..BBB...",
           "...BWW..",
           "...WBB..",
           "....W...",
           "........"]
    R = cell * .41

    def disc(cx, cy, col, sx=1.0):
        rx = R * sx
        dark = (18, 18, 20) if col == "B" else (190, 188, 176)
        side = (200, 198, 188) if col == "B" else (24, 24, 26)
        g.ellipse([cx - rx + 8, cy - R + 16, cx + rx + 8, cy + R + 16], fill=(0, 0, 0, 110))
        g.ellipse([cx - rx, cy - R + 6, cx + rx, cy + R + 6], fill=side)
        g.ellipse([cx - rx, cy - R + 3, cx + rx, cy + R + 3], fill=dark)
        top = (20, 20, 23) if col == "B" else (238, 237, 230)
        g.ellipse([cx - rx, cy - R, cx + rx, cy + R], fill=top)
        hl = (120, 120, 128, 150) if col == "B" else (255, 255, 255, 255)
        g.ellipse([cx - rx * .62, cy - R * .72, cx - rx * .05, cy - R * .28], fill=hl)
    for r, row in enumerate(pos):
        for c, ch in enumerate(row):
            if ch in "BW":
                disc(x0 + (c + .5) * cell, x0 + (r + .5) * cell, ch)
    # 뒤집히는 중인 돌 (f5 쪽으로 넘어가는 중) + 방금 놓은 돌 표시
    fx, fy = x0 + 5.5 * cell, x0 + 3.5 * cell - cell * .28
    disc(fx, fy, "W", .38)
    lx, ly = x0 + 2.5 * cell, x0 + 3.5 * cell
    g.ellipse([lx - 9, ly - 9, lx + 9, ly + 9], fill=(255, 106, 61))
    small = lay.resize((lay.width // SS, lay.height // SS), Image.LANCZOS)
    img.alpha_composite(small, (bx - o // SS, by - o // SS))


def m_yut(d, img):
    """윷놀이 — 공중의 윷가락 넷 + Blender 말 4종(public/assets/yut/pieces.webp 아틀라스, 신남 표정).

    말 원본: scripts/blender/yut_pieces.py → scripts/build_yut_atlas.py."""
    import math
    atlas = Image.open(ROOT / "public" / "assets" / "yut" / "pieces.webp").convert("RGBA")
    cell = atlas.width // 6
    # 윷판 조각(한지 + 먹선 + 말밭)
    bx0, by0, bx1, by1 = MX + 50, MY + 125, MX + MW - 20, MY + MH + 25
    d.rounded_rectangle([bx0 - 12, by0 - 12, bx1 + 12, by1 + 12], 22, fill=(110, 66, 34))
    d.rounded_rectangle([bx0, by0, bx1, by1], 14, fill=(243, 228, 198))
    ink = (74, 42, 22)
    d.line([(bx0 + 40, by0 + 40), (bx1 - 40, by1 - 40)], fill=ink, width=5)
    d.line([(bx1 - 40, by0 + 40), (bx0 + 40, by1 - 40)], fill=ink, width=5)
    d.rectangle([bx0 + 40, by0 + 40, bx1 - 40, by1 - 40], outline=ink, width=5)
    for k in range(6):
        for (x, y) in ((bx0 + 40 + k * (bx1 - bx0 - 80) / 5, by0 + 40), (bx0 + 40 + k * (bx1 - bx0 - 80) / 5, by1 - 40),
                       (bx0 + 40, by0 + 40 + k * (by1 - by0 - 80) / 5), (bx1 - 40, by0 + 40 + k * (by1 - by0 - 80) / 5)):
            big = k in (0, 5)
            r = 17 if big else 11
            d.ellipse([x - r, y - r, x + r, y + r], fill=(201, 67, 47) if big else (255, 246, 226), outline=(242, 193, 90) if big else ink, width=3)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    d.ellipse([cx - 17, cy - 17, cx + 17, cy + 17], fill=(40, 66, 140), outline=(242, 193, 90), width=3)
    # 말 네 마리 (신남 표정 = 5번째 열)
    for i, (x, y, sz) in enumerate(((MX + 95, MY + 420, 165), (MX + 190, MY + 360, 165), (MX + 285, MY + 410, 165), (MX + 360, MY + 330, 160))):
        spr = atlas.crop((4 * cell, i * cell, 5 * cell, (i + 1) * cell)).resize((sz, sz), Image.LANCZOS)
        img.alpha_composite(spr, (int(x - sz / 2), int(y - sz * 0.86)))
    # 공중의 윷가락
    d2 = ImageDraw.Draw(img)
    for i, (x, y, a, flat) in enumerate(((MX + 90, MY + 40, -30, True), (MX + 190, MY + 10, 20, False),
                                         (MX + 300, MY + 45, -10, True), (MX + 400, MY + 20, 40, True))):
        L, W = 120, 26
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        pts = [(x + ca * dx - sa * dy, y + sa * dx + ca * dy) for dx, dy in ((-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2))]
        d2.polygon(pts, fill=(244, 222, 170) if flat else (160, 92, 40), outline=(40, 18, 6))
        if flat:
            for k in (-1, 0, 1):
                ux, uy = x + ca * k * 30, y + sa * k * 30
                d2.line([(ux - 7, uy - 7), (ux + 7, uy + 7)], fill=(70, 30, 10), width=3)
                d2.line([(ux + 7, uy - 7), (ux - 7, uy + 7)], fill=(70, 30, 10), width=3)


def m_gummy(d, img):
    """구미 체인 — 홈 타일과 같은 Blender 장난감 렌더(tiles_toybox.py 의 gummy_toy)를 합성.

    원본: scripts/og-assets/tiles3d/gummy.png. 수정은 씬 스크립트에서 하고 재렌더한다
    (blender -b -P scripts/blender/tiles_toybox.py -- gummy). 뒤에 젤리색 후광을 깐다.
    """
    glow(img, MCX, MCY + 10, 250, (255, 111, 168), 46)
    glow(img, MCX + 90, MCY - 90, 150, (124, 240, 200), 30)
    toy = Image.open(HERE / "og-assets" / "tiles3d" / "gummy.png").convert("RGBA")
    a = toy.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    toy = toy.crop(a.getbbox())
    h = 470
    w = round(toy.width * h / toy.height)
    toy = toy.resize((w, h), Image.LANCZOS)
    img.alpha_composite(toy, (MCX - w // 2, MCY - h // 2 + 8))


def m_prism_hex(d, img):
    """프리즘 헥스 — 홈 타일과 같은 Blender 장난감 렌더(tiles_toybox.py 의 prism_hex_toy)를 합성.

    원본: scripts/og-assets/tiles3d/prism-hex.png. 수정은 씬 스크립트에서 하고 재렌더한다
    (blender -b -P scripts/blender/tiles_toybox.py -- prism-hex). 뒤에 보석색 후광을 깐다.
    """
    glow(img, MCX, MCY + 20, 250, (168, 85, 247), 50)
    glow(img, MCX + 110, MCY - 80, 150, (255, 178, 26), 34)
    glow(img, MCX - 120, MCY + 60, 140, (46, 107, 255), 30)
    toy = Image.open(HERE / "og-assets" / "tiles3d" / "prism-hex.png").convert("RGBA")
    a = toy.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    toy = toy.crop(a.getbbox())
    w = 450
    h = round(toy.height * w / toy.width)
    toy = toy.resize((w, h), Image.LANCZOS)
    img.alpha_composite(toy, (MCX - w // 2, MCY - h // 2 + 10))


GAMES = {
    "prism-hex":       dict(title="PRISM HEX", sub="프리즘 헥스 — 보석 블록을 꼭짓점으로 잇기", cat="BOARD", top=(22, 12, 38), bot=(8, 5, 16), accent=(246, 211, 138), motif=m_prism_hex),
    "gummy":           dict(title="GUMMY CHAIN", sub="구미 체인 — 쫀득한 연쇄로 1:1 대결", cat="PUZZLE", top=(30, 12, 40), bot=(12, 5, 18), accent=(255, 111, 168), motif=m_gummy),
    "yut":             dict(title="YUT NORI", sub="윷놀이 — 여럿이 함께, 최대 4팀", cat="BOARD", top=(30, 18, 12), bot=(12, 7, 5), accent=(244, 195, 90), motif=m_yut),
    "reversi":         dict(title="REVERSI", sub="리버시 — AI·친구와 한 판, 모서리를 잡아라", cat="BOARD", top=(8, 26, 18), bot=(3, 10, 7), accent=(232, 200, 114), motif=m_reversi),
    "ludo":            dict(title="LUDO", sub="루도 — 친구와 온라인 보드게임", cat="BOARD", top=(24, 12, 20), bot=(9, 5, 10), accent=(255, 209, 102), motif=m_ludo),
    "bubble":          dict(title="BUBBLE BURST", sub="버블 버스트 — 같은 색 셋이면 펑", cat="RETRO", top=(22, 12, 34), bot=(8, 5, 16), accent=(255, 95, 162), motif=m_bubble),
    "balloon":         dict(title="BALLOON POP", sub="풍선 룰렛 — 터뜨린 사람이 벌칙", cat="LUCKY", top=(28, 10, 18), bot=(11, 4, 8), accent=(255, 92, 122), motif=m_balloon),
    "roulette":        dict(title="ROULETTE", sub="룰렛 — 돌려서 정하는 내기 한 판", cat="LUCKY", top=(26, 10, 16), bot=(10, 4, 8), accent=(255, 206, 92), motif=m_roulette),
    "ladder":          dict(title="LADDER GAME", sub="사다리타기 — 벌칙·내기 공정 결정", cat="LUCKY", top=(8, 16, 30), bot=(4, 7, 14), accent=(80, 200, 255), motif=m_ladder),
    "lotto":           dict(title="LOTTO", sub="로또 번호 생성기 — 오늘의 행운 번호", cat="LUCKY", top=(10, 22, 16), bot=(4, 9, 7), accent=(61, 214, 140), motif=m_lotto),
    "team":            dict(title="TEAM PICKER", sub="팀나누기 — 공정한 랜덤 팀 배정", cat="LUCKY", top=(10, 14, 30), bot=(5, 6, 13), accent=(93, 193, 255), motif=m_team),
    "dice":            dict(title="DICE ROLLER", sub="주사위 — 흔들어서 결정", cat="LUCKY", top=(18, 12, 30), bot=(8, 5, 13), accent=(167, 139, 250), motif=m_dice),
    "snake":           dict(title="SNAKE", sub="스네이크 — 클래식 기록 갱신", cat="RETRO", top=(8, 20, 12), bot=(3, 8, 5), accent=(61, 214, 140), motif=m_snake),
    "pacman":          dict(title="DOT RUNNER", sub="닷 러너 — 미로 속 추격전", cat="RETRO", top=(10, 10, 26), bot=(4, 4, 11), accent=(255, 221, 51), motif=m_pacman),
    "tetris":          dict(title="TETROMINO STACK", sub="테트로미노 쌓기 — 한 줄의 쾌감", cat="RETRO", top=(12, 10, 28), bot=(5, 4, 12), accent=(93, 193, 255), motif=m_tetris),
    "brick":           dict(title="BRICK BREAKER", sub="벽돌깨기 — 한 발의 각도 싸움", cat="RETRO", top=(24, 12, 10), bot=(10, 5, 4), accent=(255, 159, 64), motif=m_brick),
    "burger":          dict(title="BURGER CHEF", sub="버거 셰프 — 주문 폭주 스택 쌓기", cat="RETRO", top=(24, 14, 8), bot=(10, 6, 3), accent=(240, 178, 92), motif=m_burger),
    "car-racing":      dict(title="CAR RACE", sub="카레이싱 — 랜덤 레이스 내기", cat="RETRO", top=(20, 8, 12), bot=(8, 3, 5), accent=(235, 64, 84), motif=m_car),
    "glory-racing":    dict(title="BRAWL RUN", sub="Brawl Run — 달리고 빼앗는 내기", cat="RETRO", top=(20, 16, 6), bot=(8, 7, 3), accent=(255, 206, 92), motif=m_glory),
    "dodge":           dict(title="SPACE-Z", sub="스페이스-Z — 총알 피하기 생존전", cat="RETRO", top=(6, 10, 24), bot=(3, 4, 10), accent=(0, 217, 255), motif=m_dodge),
    "starship-lander": dict(title="STARSHIP LANDER", sub="우주선 착륙 — 추력 조절의 미학", cat="RETRO", top=(8, 12, 24), bot=(3, 5, 10), accent=(255, 160, 60), motif=m_lander),
    "lucky-merge":     dict(title="LUCKY MERGE", sub="행성 합체 — 우주 2048 퍼즐", cat="PUZZLE", top=(14, 10, 28), bot=(6, 4, 12), accent=(167, 139, 250), motif=m_merge),
    "orbit":           dict(title="DELTA-V", sub="델타-브이 — 우주기업 연구원 시뮬레이션", cat="SIM", top=(4, 6, 14), bot=(1, 2, 5), accent=(56, 232, 200), motif=m_orbit),
    "bingo":           dict(title="BINGO", sub="빙고 — 친구와 실시간 한 판", cat="PARTY", top=(24, 10, 18), bot=(10, 4, 8), accent=(255, 99, 132), motif=m_bingo),
    "quiz":            dict(title="LIVE QUIZ", sub="라이브 퀴즈 — 같이 풀고 겨루기", cat="PARTY", top=(14, 10, 30), bot=(6, 4, 13), accent=(167, 139, 250), motif=m_quiz),
}


def build(slug, cfg):
    img = vgrad(cfg["top"], cfg["bot"])
    glow(img, 1050, 60, 330, cfg["accent"], 38)
    glow(img, 120, 600, 300, cfg["accent"], 26)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=cfg["accent"])

    cfg["motif"](d, img)
    d = ImageDraw.Draw(img)  # re-bind after any alpha_composite in motif

    LX = 76
    f_eyebrow = font("arialbd.ttf", 24)
    d.text((LX, 96), f"LUCKY PLEASE · {cfg['cat']} GAME", font=f_eyebrow, fill=cfg["accent"])

    f_big = font("arialbd.ttf", 88 if len(cfg["title"]) <= 12 else 70)
    d.text((LX, 142), cfg["title"], font=f_big, fill=WHITE)

    f_sub = font("malgunbd.ttf", 31)
    d.text((LX, 268), cfg["sub"], font=f_sub, fill=DIM)

    f_chip = font("arialbd.ttf", 23)
    chips = ["PLAY FREE", "NO LOGIN", "MOBILE · PC"]
    cx, cy = LX, 352
    for c in chips:
        tb = d.textbbox((0, 0), c, font=f_chip)
        w = tb[2] - tb[0] + 50
        h = tb[3] - tb[1] + 20
        d.rounded_rectangle([cx, cy, cx + w, cy + h], h // 2, fill=CHIP_BG, outline=CHIP_BD, width=1)
        r = 5
        d.ellipse([cx + 16 - r + 5, cy + h // 2 - r, cx + 16 + r + 5, cy + h // 2 + r], fill=cfg["accent"])
        d.text((cx + 34, cy + 10 - tb[1]), c, font=f_chip, fill=WHITE)
        cx += w + 14

    f_brand = font("arialbd.ttf", 26)
    f_meta = font("arial.ttf", 21)
    d.text((LX, H - 76), "luckyplz.com", font=f_brand, fill=WHITE)
    d.text((LX, H - 44), "games that settle the bet", font=f_meta, fill=DIM)

    out = OUT / f"{slug}.png"
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"  wrote games/{out.name}  ({out.stat().st_size // 1024} KB)")


def main():
    import sys
    # 인자로 slug 를 주면 그 게임만 만든다 (예: python scripts/gen-og-games.py bubble)
    only = set(sys.argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    print("Generating per-game OG images:")
    for slug, cfg in GAMES.items():
        if only and slug not in only:
            continue
        build(slug, cfg)
    print("done.")


if __name__ == "__main__":
    main()
