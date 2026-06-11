#!/usr/bin/env python3
"""Original animated GIFs for the 2026 World Cup anti-time-wasting post.

We do NOT host copyrighted broadcast footage (FIFA enforces hard, and it's an
AdSense risk). Instead these are original cartoon animations that capture the
gags the post is about, drawn in the site's pitch-green palette:

  roll.gif     — a player rolling sideways over and over (the famous "roll"),
                 tying to the new rule: get treated on the pitch and you sit
                 out for a full minute.
  slowsub.gif  — a substituted player creeping off one tiny step at a time
                 while a 10s clock ticks red — the new 10-second sub rule.
  keeper8.gif  — a keeper hugging the ball as the ref counts to 8, then a
                 corner flag pops (8-second goalkeeper rule → corner kick).

Text is kept off the figures so one GIF works across all four languages.
Output: public/assets/blog/worldcup-antiwaste/<name>.gif
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "assets" / "blog" / "worldcup-antiwaste"
FDIR = ROOT / "scripts" / "og-fonts"

W, H = 480, 300
PITCH = (12, 58, 40)
PITCH2 = (9, 46, 32)
LINE = (60, 120, 95)
SKIN = (245, 205, 165)
GOLD = (251, 191, 36)
RED = (239, 68, 68)
WHITE = (245, 250, 247)
DARK = (10, 26, 20)


def mono(size):
    try:
        return ImageFont.truetype(str(FDIR / "JetBrainsMono-Bold.ttf"), size)
    except Exception:
        return ImageFont.load_default()


def pitch_bg():
    img = Image.new("RGB", (W, H), PITCH)
    d = ImageDraw.Draw(img)
    # mowed stripes
    for i in range(0, W, 60):
        if (i // 60) % 2 == 0:
            d.rectangle([i, 0, i + 60, H], fill=PITCH2)
    d.line([0, H - 40, W, H - 40], fill=LINE, width=3)  # a touchline near bottom
    return img


def draw_player(d, cx, cy, ang=0, jersey=(220, 60, 70), lean=0, arms="down", legs=0):
    """Simple cartoon footballer. ang rotates the whole body (for rolling)."""
    def rot(px, py):
        s, c = math.sin(math.radians(ang)), math.cos(math.radians(ang))
        return (cx + (px) * c - (py) * s, cy + (px) * s + (py) * c)
    # body
    bx0, by0, bx1, by1 = -13, -6, 13, 40
    d.polygon([rot(bx0, by0), rot(bx1, by0), rot(bx1, by1), rot(bx0, by1)], fill=jersey)
    # legs
    d.line([rot(-7, 40), rot(-7 + legs, 64)], fill=DARK, width=7)
    d.line([rot(7, 40), rot(7 - legs, 64)], fill=DARK, width=7)
    # shoes
    d.ellipse([rot(-12 + legs, 62)[0] - 5, rot(-12 + legs, 62)[1] - 4,
               rot(-12 + legs, 62)[0] + 5, rot(-12 + legs, 62)[1] + 4], fill=WHITE)
    d.ellipse([rot(12 - legs, 62)[0] - 5, rot(12 - legs, 62)[1] - 4,
               rot(12 - legs, 62)[0] + 5, rot(12 - legs, 62)[1] + 4], fill=WHITE)
    # arms
    if arms == "up":
        d.line([rot(-13, 0), rot(-26, -18)], fill=SKIN, width=6)
        d.line([rot(13, 0), rot(26, -18)], fill=SKIN, width=6)
    else:
        d.line([rot(-13, 4), rot(-22, 26)], fill=SKIN, width=6)
        d.line([rot(13, 4), rot(22, 26)], fill=SKIN, width=6)
    # head
    hx, hy = rot(0, -22)
    d.ellipse([hx - 13, hy - 13, hx + 13, hy + 13], fill=SKIN)
    d.ellipse([hx - 13, hy - 17, hx + 13, hy - 5], fill=(60, 40, 30))  # hair


def save_gif(frames, name, duration=110):
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / name
    frames[0].save(out, save_all=True, append_images=frames[1:], loop=0,
                   duration=duration, optimize=True, disposal=2)
    print(f"wrote {out.relative_to(ROOT)}  ({out.stat().st_size // 1024} KB, {len(frames)} frames)")


# ----------------------------------------------------------------- roll.gif --
def make_roll():
    frames = []
    N = 18
    for i in range(N):
        img = pitch_bg()
        d = ImageDraw.Draw(img)
        t = i / N
        # roll across the pitch left->right, full rotations, lying down (90 base)
        x = 70 + t * 300
        ang = 90 + i * (360 / 6)   # several full rolls
        bob = int(6 * math.sin(i * 1.3))
        draw_player(d, x, 175 + bob, ang=ang, jersey=(240, 220, 70))
        # pain stars
        for k, (ox, oy) in enumerate([(-30, -40), (34, -34), (0, -52)]):
            if (i + k) % 2 == 0:
                sx, sy = x + ox, 175 + oy
                d.text((sx, sy), "*", font=mono(26), fill=GOLD)
        # unimpressed ref with rulebook on the right
        d.rectangle([W - 70, 150, W - 48, 200], fill=DARK)  # ref body (black kit)
        d.ellipse([W - 66, 130, W - 44, 152], fill=SKIN)    # head
        d.rectangle([W - 92, 165, W - 70, 188], fill=GOLD)  # rulebook
        frames.append(img)
    save_gif(frames, "roll.gif", duration=95)


# -------------------------------------------------------------- slowsub.gif --
def make_slowsub():
    frames = []
    N = 20
    for i in range(N):
        img = pitch_bg()
        d = ImageDraw.Draw(img)
        t = i / (N - 1)
        # player creeps toward the touchline (right) painfully slowly
        x = 150 + t * 70
        legs = int(8 * math.sin(i * 0.9))  # tiny shuffle
        draw_player(d, int(x), 150, jersey=(60, 130, 240), legs=legs)
        # the substitute waiting impatiently at the line, tapping
        sx = W - 60
        draw_player(d, sx, 150, jersey=(240, 90, 70),
                    arms="up" if i % 4 < 2 else "down", legs=0)
        # sub board (numbers)
        d.rounded_rectangle([sx - 26, 92, sx + 26, 120], 5, fill=DARK, outline=GOLD, width=2)
        d.text((sx - 20, 96), "7", font=mono(20), fill=RED)
        d.text((sx + 3, 96), "9", font=mono(20), fill=(0, 220, 120))
        # 10-second countdown clock, turning red as it runs out
        sec = max(0, 10 - int(t * 11))
        col = RED if sec <= 3 else GOLD
        d.ellipse([24, 24, 92, 92], fill=DARK, outline=col, width=4)
        tb = d.textbbox((0, 0), f"{sec}", font=mono(34))
        d.text((58 - (tb[2] - tb[0]) / 2, 58 - (tb[3] - tb[1]) / 2 - tb[1]),
               f"{sec}", font=mono(34), fill=col)
        # sweat drop on the dawdler
        if i % 3 == 0:
            d.ellipse([int(x) + 14, 130, int(x) + 22, 142], fill=(120, 200, 255))
        frames.append(img)
    # hold the last frame a beat
    frames += [frames[-1]] * 4
    save_gif(frames, "slowsub.gif", duration=130)


# -------------------------------------------------------------- keeper8.gif --
def make_keeper8():
    frames = []
    # count 1..8 then corner flag pop + "CORNER"
    for sec in range(1, 9):
        for sub in range(2):
            img = pitch_bg()
            d = ImageDraw.Draw(img)
            # keeper hugging the ball, shifting nervously
            kx = 150 + (4 if sub else -4)
            draw_player(d, kx, 150, jersey=(80, 220, 160), arms="down", legs=0)
            # the ball hugged to chest (soccer-ball spots, no emoji font)
            d.ellipse([kx - 17, 166, kx + 17, 200], fill=WHITE, outline=DARK, width=2)
            d.regular_polygon((kx, 183, 6), 5, rotation=18, fill=DARK)
            for a in range(5):
                ax = kx + math.cos(math.radians(90 + a * 72)) * 12
                ay = 183 - math.sin(math.radians(90 + a * 72)) * 12
                d.line([kx, 183, ax, ay], fill=(70, 70, 70), width=1)
            # referee hand counting (fingers ~ seconds), big counter
            col = RED if sec >= 6 else GOLD
            d.ellipse([W - 150, 24, W - 70, 104], fill=DARK, outline=col, width=4)
            tb = d.textbbox((0, 0), f"{sec}", font=mono(44))
            d.text((W - 110 - (tb[2] - tb[0]) / 2, 64 - (tb[3] - tb[1]) / 2 - tb[1]),
                   f"{sec}", font=mono(44), fill=col)
            d.text((W - 160, 110), "SEC", font=mono(16), fill=col)
            frames.append(img)
    # corner-kick payoff frames
    for f in range(8):
        img = pitch_bg()
        d = ImageDraw.Draw(img)
        draw_player(d, 150, 150, jersey=(80, 220, 160), arms="up", legs=0)
        # corner flag rising
        fy = 230 - min(f, 5) * 16
        d.line([W - 90, 240, W - 90, fy], fill=WHITE, width=4)
        d.polygon([(W - 90, fy), (W - 50, fy + 8), (W - 90, fy + 22)], fill=RED)
        if f >= 3:
            d.text((W - 200, 40), "CORNER!", font=mono(30), fill=GOLD)
        frames.append(img)
    save_gif(frames, "keeper8.gif", duration=150)


def main():
    make_roll()
    make_slowsub()
    make_keeper8()


if __name__ == "__main__":
    main()
