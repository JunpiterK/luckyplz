"""Generate per-post OG (Open Graph) images for every blog entry.

Why: Reddit / HN / X / KakaoTalk all decide first-impression CTR by the
thumbnail attached to a share. Until now every post pointed at the same
generic /assets/og-image.png so a SpaceX IPO deep-dive looked identical
in a feed to a coffee-bet write-up. Custom OG per post bumps social CTR
3-5× per published source on title-driven content.

Approach: Python + Pillow renders 1200×630 PNGs with the same visual
vocabulary as the live blog (dark glass background, category-coloured
left stripe, Pretendard ExtraBold title, mono uppercase labels). One
template per category — cheap to render, robust against title length,
no Node/Puppeteer build chain. Outputs land in public/og/<slug>.png and
the matching og:image / twitter:image meta tags get rewritten by the
companion meta-update step at the bottom of this file.

Usage:
    python scripts/generate-og.py            # render all posts
    python scripts/generate-og.py spacex     # render only slugs containing "spacex"
"""
from __future__ import annotations

import io
import pathlib
import re
import sys
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = pathlib.Path(__file__).parent.parent
PUBLIC = ROOT / 'public'
OG_DIR = PUBLIC / 'og'
FONT_DIR = ROOT / 'scripts' / 'og-fonts'

CANVAS = (1200, 630)


# -- COLOUR PALETTE ---------------------------------------------------------
# Mirrors the live blog. Each category gets a stripe + accent label colour
# so the same template feels distinct across the catalogue without needing
# to hand-art each one. Hex → RGB tuples for Pillow.
def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


CATS = {
    'space-tech':  {'color': hex_rgb('5dc1ff'), 'label': 'SPACE TECH'},
    'ai-tech':     {'color': hex_rgb('FF66CC'), 'label': 'AI TECH'},
    'industry':    {'color': hex_rgb('3dd68c'), 'label': 'INDUSTRY'},
    'lifestyle':   {'color': hex_rgb('FFE66D'), 'label': 'LIFESTYLE'},
    'probability': {'color': hex_rgb('00D9FF'), 'label': 'PROBABILITY'},
    'tech-space':  {'color': hex_rgb('a78bfa'), 'label': 'SPACE TECH'},  # legacy alias
    'build':       {'color': hex_rgb('FF9A3C'), 'label': 'BUILD'},
}
DEFAULT_CAT = {'color': hex_rgb('8c9cb6'), 'label': 'BLOG'}


# -- POSTS.JS PARSER --------------------------------------------------------
# posts.js is a CommonJS-style array literal. We don't ship a JS runtime
# in the build pipeline, so we extract the fields we care about with
# narrowly-scoped regex on individual entry blocks. Faster than json5
# would be, and avoids a dependency.
def parse_posts() -> list[dict]:
    text = (PUBLIC / 'blog' / 'posts.js').read_text(encoding='utf-8')
    # Each entry sits between `{` and a balanced `},` — easy enough with a
    # naive split since entries don't nest objects.
    entries = re.findall(r'{[^{}]+}', text)
    out = []
    for e in entries:
        slug = _grab(e, 'slug')
        if not slug:
            continue
        out.append({
            'slug':  slug,
            'lang':  _grab(e, 'lang') or 'ko',
            'category': _grab(e, 'category') or 'lifestyle',
            'title': _grab(e, 'title') or slug,
        })
    return out


def _grab(block: str, key: str) -> str:
    """Pull `key: "..."` or `key: '...'` from a JS object literal block.

    Apostrophe-tolerant: tries double-quoted first because titles like
    "Musk's $1.75T Empire" would mis-terminate a naive single-quote regex.
    Double-quote regex is escape-aware so any title containing literal
    `\"` or `\\\\` is captured correctly. Single-quote branch handles
    legacy posts where titles are wrapped in `'…'`. """
    m = re.search(rf'{key}\s*:\s*"((?:\\.|[^"\\])*)"', block)
    if m:
        return m.group(1).replace('\\"', '"').replace("\\'", "'")
    m = re.search(rf"{key}\s*:\s*'((?:\\.|[^'\\])*)'", block)
    if m:
        return m.group(1).replace("\\'", "'").replace('\\"', '"')
    return ''


# -- TYPESETTING ------------------------------------------------------------
def load_fonts():
    """Load OTF/TTF for title + label. Pretendard handles KR + Latin in one
    file, so we don't need a fallback chain like the website itself does
    in CSS."""
    return {
        'title':  ImageFont.truetype(str(FONT_DIR / 'Pretendard-ExtraBold.otf'), 64),
        'title_sm': ImageFont.truetype(str(FONT_DIR / 'Pretendard-ExtraBold.otf'), 52),
        'label':  ImageFont.truetype(str(FONT_DIR / 'JetBrainsMono-Bold.ttf'), 22),
        'brand':  ImageFont.truetype(str(FONT_DIR / 'Pretendard-Bold.otf'), 26),
        'domain': ImageFont.truetype(str(FONT_DIR / 'JetBrainsMono-Bold.ttf'), 18),
    }


def wrap_lines(text: str, font: ImageFont.FreeTypeFont, max_width_px: int,
               draw: ImageDraw.ImageDraw) -> list[str]:
    """Greedy word-wrap that handles Korean (no spaces) by character-breaking
    when needed. Returns a list of lines that all fit inside max_width_px."""
    if not text:
        return []
    # First try whitespace-greedy
    words = text.split(' ')
    lines: list[str] = []
    current: list[str] = []
    for w in words:
        trial = (' '.join(current + [w])).strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width_px:
            current.append(w)
        else:
            if current:
                lines.append(' '.join(current))
                current = [w]
            else:
                # Single word too wide — char-break
                lines.extend(_char_break(w, font, max_width_px, draw))
                current = []
    if current:
        lines.append(' '.join(current))

    # Re-process any line that's still too wide (long Korean phrase
    # without spaces).
    out: list[str] = []
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        if bbox[2] - bbox[0] <= max_width_px:
            out.append(ln)
        else:
            out.extend(_char_break(ln, font, max_width_px, draw))
    return out


def _char_break(s: str, font, max_w, draw) -> list[str]:
    """Split a string by character so each chunk fits max_w. For Korean."""
    if not s:
        return []
    out: list[str] = []
    cur = ''
    for ch in s:
        trial = cur + ch
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_w:
            cur = trial
        else:
            if cur:
                out.append(cur)
            cur = ch
    if cur:
        out.append(cur)
    return out


# -- RENDER -----------------------------------------------------------------
def render_og(post: dict, fonts) -> Image.Image:
    img = Image.new('RGB', CANVAS, (10, 10, 26))   # base #0A0A1A
    draw = ImageDraw.Draw(img)

    # Subtle radial-ish gradient. Pillow has no native radial, so we fake
    # depth with two diagonal blocks of slightly lighter overlay.
    overlay = Image.new('RGBA', CANVAS, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.polygon([(0, 0), (1200, 0), (1200, 320), (0, 220)], fill=(20, 26, 46, 24))
    od.polygon([(0, 410), (1200, 510), (1200, 630), (0, 630)], fill=(8, 8, 18, 30))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)

    # Faint grid pattern — every 60 px, very low opacity. Helps the OG read
    # as data/finance-grade rather than empty space.
    for x in range(0, 1200, 60):
        draw.line([(x, 0), (x, 630)], fill=(255, 255, 255, 6))
    for y in range(0, 630, 60):
        draw.line([(0, y), (1200, y)], fill=(255, 255, 255, 6))

    cat = CATS.get(post['category'], DEFAULT_CAT)

    # Left category stripe — bigger than the live post-card's 3px so it
    # reads at thumbnail size (where 3px would vanish).
    draw.rectangle([(0, 0), (12, 630)], fill=cat['color'])
    # Soft fade at the bottom of the stripe to echo the 'gradient' on the
    # site cards.
    for y in range(0, 630, 1):
        if y < 470:
            continue
        alpha = max(0, 255 - int((y - 470) * 1.6))
        # blend toward background
        c = cat['color']
        draw.rectangle([(0, y), (12, y + 1)], fill=(c[0] * alpha // 255,
                                                      c[1] * alpha // 255,
                                                      c[2] * alpha // 255))

    # Top-left brand
    draw.text((60, 56), 'LUCKY BLOG', font=fonts['brand'], fill=(226, 232, 240))

    # Top-right category label
    label = cat['label']
    bbox = draw.textbbox((0, 0), label, font=fonts['label'])
    draw.text((1200 - 60 - (bbox[2] - bbox[0]), 60), label,
              font=fonts['label'], fill=cat['color'])

    # Title — try the big font first, fall back to the smaller one if it
    # would push past 4 lines (which would either spill off the canvas or
    # crowd the bottom credit). Title block is 80 px from left, 1080 px
    # wide max.
    title = post.get('title') or post['slug']
    title_font = fonts['title']
    lines = wrap_lines(title, title_font, 1080, draw)
    if len(lines) > 4:
        title_font = fonts['title_sm']
        lines = wrap_lines(title, title_font, 1080, draw)
    line_h = title_font.size + 14
    total_h = len(lines) * line_h
    # Vertically centre with a slight upward bias (room for the bottom
    # credit row).
    y = (630 - total_h) // 2 - 16
    for ln in lines:
        draw.text((60, y), ln, font=title_font, fill=(248, 250, 252))
        y += line_h

    # Bottom-right domain
    draw.text((60, 540), 'luckyplz.com', font=fonts['domain'],
              fill=(180, 200, 230))
    # Bottom-right small accent: a tiny dash of category colour so the eye
    # picks out the brand pairing.
    draw.rectangle([(60, 580), (60 + 56, 583)], fill=cat['color'])

    return img


# -- HTML META REWRITER -----------------------------------------------------
# After PNGs land in public/og/, we need each post's HTML to point at the
# new file rather than the generic /assets/og-image.png. Touches og:image
# + twitter:image (Twitter falls back to og:image but explicit is safer
# for older crawlers).
def update_post_meta(slug: str) -> bool:
    candidates = [PUBLIC / 'blog' / slug / 'index.html']
    target = next((p for p in candidates if p.exists()), None)
    if not target:
        return False

    text = target.read_text(encoding='utf-8')
    new_url = f'https://luckyplz.com/og/{slug}.png'

    new_text = re.sub(
        r'(<meta\s+property="og:image"\s+content=")([^"]+)(")',
        rf'\1{new_url}\3',
        text,
    )
    new_text = re.sub(
        r'(<meta\s+name="twitter:image"\s+content=")([^"]+)(")',
        rf'\1{new_url}\3',
        new_text,
    )
    if new_text == text:
        return False
    target.write_bytes(new_text.encode('utf-8'))
    return True


# -- ENTRY POINT ------------------------------------------------------------
def main(filter_substr: str = '') -> int:
    sys.stdout.reconfigure(encoding='utf-8')
    OG_DIR.mkdir(parents=True, exist_ok=True)

    fonts = load_fonts()
    posts = parse_posts()
    if filter_substr:
        posts = [p for p in posts if filter_substr in p['slug']]
    if not posts:
        print('no posts matched')
        return 1

    rendered = 0
    meta_updated = 0
    for post in posts:
        try:
            img = render_og(post, fonts)
            out = OG_DIR / f"{post['slug']}.png"
            img.save(out, format='PNG', optimize=True)
            rendered += 1
            if update_post_meta(post['slug']):
                meta_updated += 1
        except Exception as e:
            print(f"FAIL {post['slug']}: {e}")

    print(f'✓ Rendered {rendered} OG image(s) → public/og/*.png')
    print(f'✓ Rewrote og:image meta in {meta_updated} HTML file(s).')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ''))
