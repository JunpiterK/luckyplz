"""Generate OG image (1200x630 PNG) for blog posts.

Each PNG is built per-post: title, date, key tickers, dominant tickers.
Run: python scripts/gen-og-recap.py
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "public" / "assets" / "blog"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Fonts (Windows path; falls back to default if missing)
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_REG = "C:/Windows/Fonts/arial.ttf"
FONT_KR_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_KR = "C:/Windows/Fonts/malgun.ttf"


def make_bg(W, H):
    """Vertical gradient dark navy."""
    img = Image.new("RGB", (W, H), (6, 8, 15))  # #06080f
    draw = ImageDraw.Draw(img)
    # Top accent ribbon
    for x in range(W):
        # Cyan -> green gradient
        t = x / W
        r = int(0 + 127 * t)
        g = int(229 - 0 * t)
        b = int(255 - 77 * t)
        draw.line([(x, 0), (x, 5)], fill=(r, g, b))
    # Bottom accent ribbon
    for x in range(W):
        t = x / W
        r = int(255 - 128 * t)
        g = int(209 - 80 * t)
        b = int(102 + 30 * t)
        draw.line([(x, H - 5), (x, H - 1)], fill=(r, g, b))
    # Subtle glow blob top-left
    glow = Image.new("RGB", (W, H), (6, 8, 15))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([(-200, -200), (700, 500)], fill=(0, 50, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.blend(img, glow, 0.6)
    # Glow blob bottom-right
    glow2 = Image.new("RGB", (W, H), (6, 8, 15))
    glow2_draw = ImageDraw.Draw(glow2)
    glow2_draw.ellipse([(W - 500, H - 400), (W + 200, H + 200)], fill=(50, 35, 0))
    glow2 = glow2.filter(ImageFilter.GaussianBlur(120))
    img = Image.blend(img, glow2, 0.4)
    return img


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def draw_text_centered(draw, text, y, font, fill):
    """Center text horizontally."""
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((1200 - w) / 2, y), text, font=font, fill=fill)


def draw_text_left(draw, text, x, y, font, fill):
    draw.text((x, y), text, font=font, fill=fill)


def make_recap_og(out_path, lang="en"):
    """Daily recap OG: 'US TECH DAILY RECAP · MAY 11, 2026 CLOSE'."""
    W, H = 1200, 630
    img = make_bg(W, H)
    draw = ImageDraw.Draw(img)

    # Top label
    label_font = load_font(FONT_BOLD, 22)
    label = "US TECH DAILY RECAP" if lang == "en" else "미국 테크 데일리 리캡"
    fnt = label_font if lang == "en" else load_font(FONT_KR_BOLD, 22)
    draw_text_centered(draw, label, 60, fnt, (255, 209, 102))

    # Big headline (multi-line)
    if lang == "en":
        title_font = load_font(FONT_BOLD, 78)
        draw_text_centered(draw, "MARKET CLOSE", 110, title_font, (255, 255, 255))
        draw_text_centered(draw, "MAY 11, 2026", 195, title_font, (0, 229, 255))
    else:
        title_font = load_font(FONT_KR_BOLD, 70)
        draw_text_centered(draw, "정규장 마감", 115, title_font, (255, 255, 255))
        draw_text_centered(draw, "2026-05-11", 200, load_font(FONT_BOLD, 70), (0, 229, 255))

    # Subline
    sub_font = load_font(FONT_REG, 28) if lang == "en" else load_font(FONT_KR, 28)
    sub = "S&P · Nasdaq fresh ATH · AI optics frenzy" if lang == "en" else "S&P · Nasdaq 신고가 · AI 옵틱스 폭주"
    draw_text_centered(draw, sub, 310, sub_font, (160, 175, 200))

    # 4 ticker cards
    tickers = [
        ("S&P 500", "7,412", "+0.19%", (127, 255, 178)),
        ("NASDAQ", "26,274", "+0.10%", (127, 255, 178)),
        ("LITE", "+16.4%", "OPTICS", (255, 209, 102)),
        ("INTC", "+5.7%", "APPLE", (255, 209, 102)),
    ]
    card_w, card_h = 240, 130
    gap = 24
    total_w = card_w * 4 + gap * 3
    start_x = (W - total_w) // 2
    card_y = 380
    for i, (tick, val, sub_, color) in enumerate(tickers):
        x = start_x + i * (card_w + gap)
        # Card background
        draw.rounded_rectangle([(x, card_y), (x + card_w, card_y + card_h)],
                               radius=14, fill=(20, 28, 44), outline=(50, 70, 100), width=2)
        # Ticker
        tick_font = load_font(FONT_BOLD, 22)
        draw.text((x + 16, card_y + 14), tick, font=tick_font, fill=(0, 229, 255))
        # Value
        val_font = load_font(FONT_BOLD, 36)
        draw.text((x + 16, card_y + 46), val, font=val_font, fill=color)
        # Sub
        sub_font2 = load_font(FONT_BOLD, 18)
        draw.text((x + 16, card_y + 94), sub_, font=sub_font2, fill=(160, 175, 200))

    # Bottom: domain
    domain_font = load_font(FONT_BOLD, 28)
    draw_text_centered(draw, "LUCKYPLZ.COM", 555, domain_font, (0, 229, 255))

    img.save(out_path, "PNG", optimize=True)
    print(f"[ok] {out_path}")


def make_semi_og(out_path, lang="en"):
    """Semiconductor rally OG: 9 stocks chart."""
    W, H = 1200, 630
    img = make_bg(W, H)
    draw = ImageDraw.Draw(img)

    # Top label
    fnt = load_font(FONT_BOLD, 22) if lang == "en" else load_font(FONT_KR_BOLD, 22)
    label = "SEMICONDUCTOR SUPER-RALLY 2026" if lang == "en" else "반도체 슈퍼랠리 2026"
    draw_text_centered(draw, label, 60, fnt, (255, 209, 102))

    # Big title
    if lang == "en":
        title_font = load_font(FONT_BOLD, 70)
        draw_text_centered(draw, "HOW HIGH CAN", 110, title_font, (255, 255, 255))
        draw_text_centered(draw, "KR & US CHIPS GO?", 190, title_font, (0, 229, 255))
    else:
        title_font = load_font(FONT_KR_BOLD, 64)
        draw_text_centered(draw, "한미 반도체주", 115, title_font, (255, 255, 255))
        draw_text_centered(draw, "어디까지 오를까?", 195, title_font, (0, 229, 255))

    # Subline
    sub = "9 stocks · live data · scenarios" if lang == "en" else "9종 · 실데이터 · 시나리오 분석"
    sub_font = load_font(FONT_REG, 26) if lang == "en" else load_font(FONT_KR, 26)
    draw_text_centered(draw, sub, 310, sub_font, (160, 175, 200))

    # 4 highlight stats
    stats = [
        ("SNDK", "+3,710%", "1Y", (127, 255, 178)),
        ("SKH", "+898%", "1Y", (127, 255, 178)),
        ("NVDA", "$5.23T", "CAP", (0, 229, 255)),
        ("INTC", "+41.9%", "7D", (255, 209, 102)),
    ]
    card_w, card_h = 240, 130
    gap = 24
    total_w = card_w * 4 + gap * 3
    start_x = (W - total_w) // 2
    card_y = 380
    for i, (tick, val, sub_, color) in enumerate(stats):
        x = start_x + i * (card_w + gap)
        draw.rounded_rectangle([(x, card_y), (x + card_w, card_y + card_h)],
                               radius=14, fill=(20, 28, 44), outline=(50, 70, 100), width=2)
        tick_font = load_font(FONT_BOLD, 22)
        draw.text((x + 16, card_y + 14), tick, font=tick_font, fill=(0, 229, 255))
        val_font = load_font(FONT_BOLD, 32)
        draw.text((x + 16, card_y + 46), val, font=val_font, fill=color)
        sub_font2 = load_font(FONT_BOLD, 18)
        draw.text((x + 16, card_y + 94), sub_, font=sub_font2, fill=(160, 175, 200))

    # Domain
    domain_font = load_font(FONT_BOLD, 28)
    draw_text_centered(draw, "LUCKYPLZ.COM", 555, domain_font, (0, 229, 255))

    img.save(out_path, "PNG", optimize=True)
    print(f"[ok] {out_path}")


if __name__ == "__main__":
    make_recap_og(OUT_DIR / "og-us-tech-recap-2026-05-11-en.png", lang="en")
    make_recap_og(OUT_DIR / "og-us-tech-recap-2026-05-11.png", lang="ko")
    make_semi_og(OUT_DIR / "og-semiconductor-rally-2026-en.png", lang="en")
    make_semi_og(OUT_DIR / "og-semiconductor-rally-2026.png", lang="ko")
    print("Done.")
