"""Daily OG image generator — invoked by auto-daily-post.py.

Reuses the look from gen-og-recap.py but takes runtime data
(label, headline, 4 highlight cards from Claude's `og_data`).
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_REG = "C:/Windows/Fonts/arial.ttf"
FONT_KR_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_KR = "C:/Windows/Fonts/malgun.ttf"

# Linux fallback paths (GitHub Actions ubuntu-latest)
FONT_FALLBACKS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
]

W, H = 1200, 630


def load_font(primary: str, size: int):
    for p in [primary, *FONT_FALLBACKS]:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def make_bg() -> Image.Image:
    img = Image.new("RGB", (W, H), (6, 8, 15))
    draw = ImageDraw.Draw(img)
    for x in range(W):
        t = x / W
        r = int(0 + 127 * t); g = int(229); b = int(255 - 77 * t)
        draw.line([(x, 0), (x, 5)], fill=(r, g, b))
    for x in range(W):
        t = x / W
        r = int(255 - 128 * t); g = int(209 - 80 * t); b = int(102 + 30 * t)
        draw.line([(x, H - 5), (x, H - 1)], fill=(r, g, b))
    glow = Image.new("RGB", (W, H), (6, 8, 15))
    ImageDraw.Draw(glow).ellipse([(-200, -200), (700, 500)], fill=(0, 50, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.blend(img, glow, 0.6)
    glow2 = Image.new("RGB", (W, H), (6, 8, 15))
    ImageDraw.Draw(glow2).ellipse([(W - 500, H - 400), (W + 200, H + 200)], fill=(50, 35, 0))
    glow2 = glow2.filter(ImageFilter.GaussianBlur(120))
    return Image.blend(img, glow2, 0.4)


def draw_centered(draw, text, y, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) / 2, y), text, font=font, fill=fill)


COLOR_MAP = {
    "up": (127, 255, 178),
    "down": (255, 120, 136),
    "gold": (255, 209, 102),
    "cyan": (0, 229, 255),
}


def make_og(out_path: Path, *, lang: str, label: str, headline: str, og_data: dict) -> None:
    """Build 1200x630 PNG.

    og_data = {"card1":{tick,val,sub,color}, ..., "card4":{...}}
    """
    img = make_bg()
    draw = ImageDraw.Draw(img)

    # Top label
    label_font = load_font(FONT_KR_BOLD if lang == "ko" else FONT_BOLD, 22)
    draw_centered(draw, label, 50, label_font, (255, 209, 102))

    # Big headline (auto-split into 2 lines if long)
    lines = []
    if len(headline) > 28:
        words = headline.split()
        mid = len(words) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    else:
        lines = [headline]

    head_font = load_font(FONT_KR_BOLD if lang == "ko" else FONT_BOLD, 60 if len(lines) > 1 else 70)
    y = 110
    for i, line in enumerate(lines):
        color = (255, 255, 255) if i == 0 else (0, 229, 255)
        draw_centered(draw, line, y, head_font, color)
        y += 78

    # 4 ticker cards
    card_w, card_h = 240, 130
    gap = 24
    total_w = card_w * 4 + gap * 3
    start_x = (W - total_w) // 2
    card_y = 380

    keys = ["card1", "card2", "card3", "card4"]
    for i, k in enumerate(keys):
        c = og_data.get(k) or {}
        x = start_x + i * (card_w + gap)
        draw.rounded_rectangle([(x, card_y), (x + card_w, card_y + card_h)],
                               radius=14, fill=(20, 28, 44), outline=(50, 70, 100), width=2)
        tick_font = load_font(FONT_BOLD, 22)
        draw.text((x + 16, card_y + 14), str(c.get("tick", "—"))[:12], font=tick_font, fill=(0, 229, 255))
        val_font = load_font(FONT_BOLD, 32)
        draw.text((x + 16, card_y + 46), str(c.get("val", "—"))[:10], font=val_font, fill=COLOR_MAP.get(c.get("color", "up"), COLOR_MAP["up"]))
        sub_font = load_font(FONT_BOLD, 18)
        draw.text((x + 16, card_y + 94), str(c.get("sub", ""))[:14], font=sub_font, fill=(160, 175, 200))

    # Bottom domain
    domain_font = load_font(FONT_BOLD, 28)
    draw_centered(draw, "LUCKYPLZ.COM", 555, domain_font, (0, 229, 255))

    img.save(out_path, "PNG", optimize=True)
