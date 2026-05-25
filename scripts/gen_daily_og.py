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
# Per-language Windows-side primary paths (used during local dev). Linux
# fallbacks below cover the GitHub Actions runner — the actual production
# environment. On Linux these Windows paths simply fail and the loop
# advances to the per-language fallback chain.
FONT_JP_BOLD = "C:/Windows/Fonts/yugothb.ttc"        # Yu Gothic UI Bold
FONT_JP = "C:/Windows/Fonts/yugothic.ttc"
FONT_ZH_BOLD = "C:/Windows/Fonts/msyhbd.ttc"         # Microsoft YaHei Bold
FONT_ZH = "C:/Windows/Fonts/msyh.ttc"

# Linux fallback paths (GitHub Actions ubuntu-latest).
# CRITICAL: language-appropriate fonts MUST come first because OG image text
# mixes the post's language with Latin (e.g., 'S&P 500 7445선 마감' or
# 'CSI 300 收盘 -0.82%' or 'ナスダック 高値更新'). DejaVu/Liberation only
# render Latin and would silently render CJK as .notdef boxes (□□□).
#
# fonts-nanum (Korean), fonts-noto-cjk-extra (JP/SC/TC single-face OTFs),
# and fonts-noto-cjk (TTC collection) all need to be installed on the
# runner. fonts-noto-cjk-extra is the only package that provides single
# OTFs per language, which Pillow can load reliably without TTC face
# selection ambiguity.
FONT_FALLBACKS_KO_BOLD = [
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Bold.otf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]
FONT_FALLBACKS_JA_BOLD = [
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Bold.otf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",   # Korean is fine for shared CJK Han glyphs
]
FONT_FALLBACKS_ZH_BOLD = [
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",   # ditto
]
FONT_FALLBACKS_EN_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",   # CJK fallback in case Claude leaves CJK chars in EN
]

FONT_FALLBACKS_KO_REG = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]
FONT_FALLBACKS_JA_REG = [
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]
FONT_FALLBACKS_ZH_REG = [
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]
FONT_FALLBACKS_EN_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]

# Legacy aliases used by load_font's autodetect branch (when caller
# doesn't pass `lang`). KR-first ordering preserves the previous default
# behavior so the old code path keeps producing the same output.
FONT_FALLBACKS_BOLD = (
    FONT_FALLBACKS_KO_BOLD
    + FONT_FALLBACKS_JA_BOLD[:2]
    + FONT_FALLBACKS_ZH_BOLD[:2]
    + FONT_FALLBACKS_EN_BOLD[:2]
)
FONT_FALLBACKS_REG = (
    FONT_FALLBACKS_KO_REG
    + FONT_FALLBACKS_JA_REG[:2]
    + FONT_FALLBACKS_ZH_REG[:2]
    + FONT_FALLBACKS_EN_REG[:2]
)


def fallbacks_for(lang: str, bold: bool):
    """Return the language-appropriate fallback chain.

    ko → Nanum first, then CJK TTC. ja → Noto JP OTF first.
    zh → Noto SC OTF first. en/other → DejaVu first.
    Each chain ends with a CJK fallback so mixed-content lines still
    render even when a label leaks an out-of-language character.
    """
    if lang == "ko":
        return FONT_FALLBACKS_KO_BOLD if bold else FONT_FALLBACKS_KO_REG
    if lang == "ja":
        return FONT_FALLBACKS_JA_BOLD if bold else FONT_FALLBACKS_JA_REG
    if lang == "zh":
        return FONT_FALLBACKS_ZH_BOLD if bold else FONT_FALLBACKS_ZH_REG
    return FONT_FALLBACKS_EN_BOLD if bold else FONT_FALLBACKS_EN_REG

W, H = 1200, 630


def load_font(primary: str, size: int):
    """Load font with Korean-aware fallback chain.

    On Linux (cron runner) the Windows primary path will fail; we then try
    Korean-capable fonts FIRST so mixed KR+Latin text renders correctly.
    Without this fallback order, Korean characters silently render as boxes.
    """
    is_bold = any(kw in primary.lower() for kw in ("bold", "bd", "black"))
    fallbacks = FONT_FALLBACKS_BOLD if is_bold else FONT_FALLBACKS_REG
    for p in [primary, *fallbacks]:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def load_font_for_lang(lang: str, size: int, bold: bool = True):
    """Load a font appropriate for the given language.

    ja/zh on Linux: Noto Sans JP / SC OTF first. ko: Nanum. en: Arial/DejaVu.
    The Windows-side primary path lets local devs preview OG images
    accurately without installing the Noto fonts; on Linux runners the
    primary path simply fails and the language-specific fallback chain
    takes over. Falls back to the default font as last resort.
    """
    # Pick a per-language Windows primary so local previews render
    # correctly for ja/zh as well.
    if lang == "ja":
        primary = FONT_JP_BOLD if bold else FONT_JP
    elif lang == "zh":
        primary = FONT_ZH_BOLD if bold else FONT_ZH
    elif lang == "ko":
        primary = FONT_KR_BOLD if bold else FONT_KR
    else:
        primary = FONT_BOLD if bold else FONT_REG

    for p in [primary, *fallbacks_for(lang, bold)]:
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

    # Top label (label text and headline are in the page's language, so
    # pick fonts that can render that language without falling back to
    # tofu boxes for non-Latin characters).
    label_font = load_font_for_lang(lang, 22, bold=True)
    draw_centered(draw, label, 50, label_font, (255, 209, 102))

    # Big headline (auto-split into 2 lines if long)
    lines = []
    if len(headline) > 28:
        words = headline.split()
        mid = len(words) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    else:
        lines = [headline]

    head_font = load_font_for_lang(lang, 60 if len(lines) > 1 else 70, bold=True)
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
