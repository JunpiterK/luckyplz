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
    rnd = random.Random(5)
    f = font("arialbd.ttf", 58)
    for i in range(7):
        x = MX + 40 + rnd.randint(0, 110); y = MY + 60 + i * 48 + rnd.randint(-12, 12)
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=(93, 193, 255))
    for i in range(7):
        x = MX + MW - 150 + rnd.randint(0, 110); y = MY + 60 + i * 48 + rnd.randint(-12, 12)
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=(255, 107, 53))
    d.rounded_rectangle([MCX - 5, MY + 24, MCX + 5, MY + MH - 24], 5, fill=(255, 255, 255, 60))
    tb = d.textbbox((0, 0), "VS", font=f)
    d.rounded_rectangle([MCX - 62, MCY - 48, MCX + 62, MCY + 48], 24, fill=(18, 22, 34), outline=(255, 206, 92), width=4)
    d.text((MCX - (tb[2] - tb[0]) / 2, MCY - (tb[3] - tb[1]) / 2 - tb[1]), "VS", font=f, fill=(255, 206, 92))


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
    """트랙 위에서 서로 밀치며 달리는 두 주자. 앞(빨강)/뒤(청록)."""
    # 트랙 — 체크무늬 바닥 라인
    sq = 34
    for r in range(2):
        for i in range(9):
            c = WHITE if (i + r) % 2 == 0 else (28, 32, 44)
            d.rectangle([MX + 20 + i * sq, MY + 322 + r * sq,
                         MX + 20 + (i + 1) * sq, MY + 322 + (r + 1) * sq], fill=c)
    # 속도선
    for i, y in enumerate((MY + 120, MY + 165, MY + 210)):
        d.line([(MX + 20, y), (MX + 20 + 70 - i * 14, y)], fill=(255, 255, 255, 90), width=7)

    def runner(cx, cy, col, lean, arm_to):
        """cy=머리 중심. lean>0 이면 오른쪽으로 기운 자세."""
        hr = 30
        d.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=col)
        # 몸통
        d.line([(cx, cy + hr), (cx + lean * 10, cy + hr + 78)], fill=col, width=34)
        # 미는 팔 — 상대 쪽으로 뻗는다
        d.line([(cx + lean * 6, cy + hr + 22), arm_to], fill=col, width=24)
        # 반대 팔
        d.line([(cx - lean * 6, cy + hr + 22), (cx - lean * 46, cy + hr + 4)], fill=col, width=20)
        # 다리 (앞뒤로 벌어진 러닝 자세)
        base = (cx + lean * 10, cy + hr + 78)
        d.line([base, (cx + lean * 10 - 46, cy + hr + 150)], fill=col, width=26)
        d.line([base, (cx + lean * 10 + 40, cy + hr + 118)], fill=col, width=26)
        d.line([(cx + lean * 10 + 40, cy + hr + 118), (cx + lean * 10 + 30, cy + hr + 168)], fill=col, width=24)

    cy = MCY - 92
    runner(MCX - 130, cy + 20, (77, 208, 225), 1, (MCX - 20, cy + 42))    # 뒤 주자 — 앞사람을 민다
    runner(MCX + 120, cy, (255, 107, 107), -1, (MCX + 10, cy + 40))       # 앞 주자 — 뒤로 막는다

    # 충돌 임팩트 — 두 팔이 만나는 지점
    ix, iy = MCX - 5, cy + 40
    star = []
    import math
    for k in range(10):
        rr = 46 if k % 2 == 0 else 20
        a = math.pi / 5 * k - math.pi / 2
        star.append((ix + math.cos(a) * rr, iy + math.sin(a) * rr))
    d.polygon(star, fill=(255, 206, 92))

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


GAMES = {
    "balloon":         dict(title="BALLOON POP", sub="풍선 룰렛 — 터뜨린 사람이 벌칙", cat="LUCKY", top=(28, 10, 18), bot=(11, 4, 8), accent=(255, 92, 122), motif=m_balloon),
    "roulette":        dict(title="ROULETTE", sub="룰렛 — 돌려서 정하는 내기 한 판", cat="LUCKY", top=(26, 10, 16), bot=(10, 4, 8), accent=(255, 206, 92), motif=m_roulette),
    "ladder":          dict(title="LADDER GAME", sub="사다리타기 — 벌칙·내기 공정 결정", cat="LUCKY", top=(8, 16, 30), bot=(4, 7, 14), accent=(80, 200, 255), motif=m_ladder),
    "lotto":           dict(title="LOTTO", sub="로또 번호 생성기 — 오늘의 행운 번호", cat="LUCKY", top=(10, 22, 16), bot=(4, 9, 7), accent=(61, 214, 140), motif=m_lotto),
    "team":            dict(title="TEAM PICKER", sub="팀나누기 — 공정한 랜덤 팀 배정", cat="LUCKY", top=(10, 14, 30), bot=(5, 6, 13), accent=(93, 193, 255), motif=m_team),
    "dice":            dict(title="DICE ROLLER", sub="주사위 — 흔들어서 결정", cat="LUCKY", top=(18, 12, 30), bot=(8, 5, 13), accent=(167, 139, 250), motif=m_dice),
    "snake":           dict(title="SNAKE", sub="스네이크 — 클래식 기록 갱신", cat="RETRO", top=(8, 20, 12), bot=(3, 8, 5), accent=(61, 214, 140), motif=m_snake),
    "pacman":          dict(title="PACMAN", sub="팩맨 — 미로 속 추격전", cat="RETRO", top=(10, 10, 26), bot=(4, 4, 11), accent=(255, 221, 51), motif=m_pacman),
    "tetris":          dict(title="TETRIS", sub="테트리스 — 한 줄의 쾌감", cat="RETRO", top=(12, 10, 28), bot=(5, 4, 12), accent=(93, 193, 255), motif=m_tetris),
    "brick":           dict(title="BRICK BREAKER", sub="벽돌깨기 — 한 발의 각도 싸움", cat="RETRO", top=(24, 12, 10), bot=(10, 5, 4), accent=(255, 159, 64), motif=m_brick),
    "burger":          dict(title="BURGER CHEF", sub="버거 셰프 — 주문 폭주 스택 쌓기", cat="RETRO", top=(24, 14, 8), bot=(10, 6, 3), accent=(240, 178, 92), motif=m_burger),
    "car-racing":      dict(title="CAR RACE", sub="카레이싱 — 랜덤 레이스 내기", cat="RETRO", top=(20, 8, 12), bot=(8, 3, 5), accent=(235, 64, 84), motif=m_car),
    "glory-racing":    dict(title="BRAWL RUN", sub="Brawl Run — 달리고 빼앗는 내기", cat="RETRO", top=(20, 16, 6), bot=(8, 7, 3), accent=(255, 206, 92), motif=m_glory),
    "dodge":           dict(title="SPACE-Z", sub="스페이스-Z — 총알 피하기 생존전", cat="RETRO", top=(6, 10, 24), bot=(3, 4, 10), accent=(0, 217, 255), motif=m_dodge),
    "starship-lander": dict(title="STARSHIP LANDER", sub="우주선 착륙 — 추력 조절의 미학", cat="RETRO", top=(8, 12, 24), bot=(3, 5, 10), accent=(255, 160, 60), motif=m_lander),
    "lucky-merge":     dict(title="LUCKY MERGE", sub="행성 합체 — 우주 2048 퍼즐", cat="PUZZLE", top=(14, 10, 28), bot=(6, 4, 12), accent=(167, 139, 250), motif=m_merge),
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
    OUT.mkdir(parents=True, exist_ok=True)
    print("Generating per-game OG images:")
    for slug, cfg in GAMES.items():
        build(slug, cfg)
    print("done.")


if __name__ == "__main__":
    main()
