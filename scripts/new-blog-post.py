#!/usr/bin/env python3
"""
new-blog-post.py — scaffold a new blog post in ko + en + ja + zh (mandatory).

This script enforces the 4-language default established in
CLAUDE.md "Blog Authoring (MANDATORY)" section. Run it whenever
you start a new manual blog post. Auto-generated daily market
posts have their own pipeline (scripts/auto-daily-post.py) and
do NOT use this script.

Usage:
  python scripts/new-blog-post.py \\
    --slug claude-vs-gpt5 \\
    --category ai-tech \\
    --title-ko "Claude vs GPT-5 — 차이의 본질" \\
    --title-en "Claude vs GPT-5: The Real Difference" \\
    --title-ja "Claude vs GPT-5 — 違いの本質" \\
    --title-zh "Claude vs GPT-5：差异的本质" \\
    --excerpt-ko "..." --excerpt-en "..." --excerpt-ja "..." --excerpt-zh "..." \\
    --read-min 12 --cover-emoji "🤖" \\
    --tags "Claude,GPT-5,AI,model,benchmark"

Optional:
  --series anthropic-story   ← apply beige-book theme + episode header
  --theme beige-book|standard ← override theme (default: based on series)
  --date YYYY-MM-DD          ← override publish date (default: today KST)
  --episode 4                ← series episode number (only if --series)

Creates:
  public/blog/<slug>/index.html         (ko, lang="ko")
  public/blog/<slug>-en/index.html      (en, lang="en")
  public/blog/<slug>-ja/index.html      (ja, lang="ja")
  public/blog/<slug>-zh/index.html      (zh, lang="zh")
  Updates public/blog/posts.js          (4 entries at top, alts-linked)
  Updates public/sitemap.xml            (4 url blocks with hreflang)

After running:
  1. Fill in body content (search for "<!-- BODY START -->" in each file)
  2. python scripts/inject-blog-desktop-css.py
  3. bash scripts/bump-cache.sh
  4. git add . && git commit -m "feat(blog): publish <slug> (ko+en+ja+zh)"
  5. git pull --rebase -X theirs origin main && git push origin HEAD:main
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

# Force UTF-8 stdout/stderr on Windows (default cp949 chokes on em-dash in help text)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "public" / "blog"
POSTS_JS = BLOG / "posts.js"
SITEMAP = ROOT / "public" / "sitemap.xml"

KST = ZoneInfo("Asia/Seoul")

# Category set overhauled 2026-06-11 (see public/blog/posts.js BLOG_CATEGORIES).
# `stocks` is normally produced by auto-daily-post.py, not the manual scaffolder,
# but it's accepted here for completeness. `lifestyle`/`probability` retired.
VALID_CATEGORIES = {
    "stocks", "industry", "ai-tech", "space-tech", "robotics",
    "football", "baseball", "gaming-history",
}

VALID_SERIES = {
    "anthropic-story": {"theme": "beige-book", "series_label": "An Anthropic Story"},
    "ai-evo":          {"theme": "standard",   "series_label": "AI Evolution"},
    "space-evo":       {"theme": "standard",   "series_label": "Space Evolution"},
}

# ---------------------------------------------------------------------------
# HTML templates — two themes
# ---------------------------------------------------------------------------

# Standard theme: mobile-first inline CSS, picks up blog-desktop.css on ≥768px.
STANDARD_TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Lucky Blog</title>
<meta name="description" content="{excerpt}">
<meta name="keywords" content="{tags_csv}, lucky blog">
<link rel="canonical" href="https://luckyplz.com/blog/{slug_for_lang}/">

<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{excerpt}">
<meta property="og:url" content="https://luckyplz.com/blog/{slug_for_lang}/">
<meta property="og:locale" content="{og_locale}">
<meta property="og:site_name" content="Lucky Blog">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{excerpt}">

<link rel="alternate" hreflang="ko" href="https://luckyplz.com/blog/{slug_ko}/">
<link rel="alternate" hreflang="en" href="https://luckyplz.com/blog/{slug_en}/">
<link rel="alternate" hreflang="ja" href="https://luckyplz.com/blog/{slug_ja}/">
<link rel="alternate" hreflang="zh" href="https://luckyplz.com/blog/{slug_zh}/">
<link rel="alternate" hreflang="x-default" href="https://luckyplz.com/blog/{slug_en}/">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "{title}",
  "description": "{excerpt}",
  "inLanguage": "{lang}",
  "datePublished": "{date}",
  "dateModified": "{date}",
  "author": {{ "@type": "Organization", "name": "Lucky Blog", "url": "https://luckyplz.com/" }},
  "publisher": {{ "@type": "Organization", "name": "Lucky Blog", "logo": {{ "@type": "ImageObject", "url": "https://luckyplz.com/assets/icon-192.png" }}}},
  "mainEntityOfPage": {{ "@type": "WebPage", "@id": "https://luckyplz.com/blog/{slug_for_lang}/" }}
}}
</script>

<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0a0a0a; color: #e8e8e8;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans KR", sans-serif;
    font-size: 16px; line-height: 1.7;
  }}
  .post {{ max-width: 480px; margin: 0 auto; padding: 24px 20px 80px; }}
  .nav {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; margin-bottom: 24px; border-bottom: 1px solid #2a2a2a; }}
  .nav a {{ color: #888; text-decoration: none; font-size: 13px; }}
  .nav a:hover {{ color: #fff; }}
  .nav .brand {{ font-weight: 600; }}
  .hero {{ margin: 32px 0 24px; }}
  .hero h1 {{ font-size: 28px; line-height: 1.3; font-weight: 800; word-break: keep-all; margin-bottom: 12px; }}
  .hero .meta {{ display: flex; gap: 12px; color: #888; font-size: 13px; margin-bottom: 16px; }}
  .hero .meta .dot {{ color: #444; }}
  .hero .excerpt {{ color: #b8b8b8; font-size: 15px; line-height: 1.7; }}
  .post h2 {{ font-size: 22px; line-height: 1.35; margin: 40px 0 16px; font-weight: 700; word-break: keep-all; }}
  .post h3 {{ font-size: 18px; line-height: 1.4; margin: 28px 0 12px; font-weight: 700; word-break: keep-all; }}
  .post p {{ margin-bottom: 18px; text-align: justify; word-break: normal; overflow-wrap: break-word; -webkit-hyphens: auto; hyphens: auto; }}
  .post strong {{ color: #fff; }}
  .post em {{ color: #f0b040; font-style: normal; }}
  .post a {{ color: #4da3ff; text-decoration: underline; }}
  .post ul, .post ol {{ margin: 0 0 18px 24px; }}
  .post li {{ margin-bottom: 8px; word-break: keep-all; }}
  figure {{ margin: 24px -20px; }}
  figure img {{ width: 100%; height: auto; display: block; }}
  figcaption {{ margin: 8px 20px 0; font-size: 13px; color: #888; line-height: 1.6; }}
  .footnotes {{ margin-top: 60px; padding-top: 20px; border-top: 1px solid #2a2a2a; font-size: 13px; color: #888; }}
  .footnotes h4 {{ font-size: 14px; color: #b8b8b8; margin-bottom: 10px; }}
  .footnotes ol {{ padding-left: 18px; }}
  .footnotes li {{ margin-bottom: 6px; }}
</style>
</head>
<body>

<div class="post">

  <nav class="nav">
    <a href="/blog/">{nav_back}</a>
    <a href="/" class="brand">Lucky Blog</a>
    <a href="/blog/?cat={category}">{category_label}</a>
  </nav>

  <header class="hero">
    <h1>{title}</h1>
    <div class="meta">
      <span>{date}</span>
      <span class="dot">·</span>
      <span>{read_min} min read</span>
    </div>
    <p class="excerpt">{excerpt}</p>
  </header>

  <!-- BODY START — fill in your content here -->

  <h2>{placeholder_h2}</h2>
  <p>{placeholder_body}</p>

  <!-- BODY END -->

  <div class="footnotes">
    <h4>{footnotes_label}</h4>
    <ol>
      <li>{footnotes_placeholder}</li>
    </ol>
  </div>

</div>

</body>
</html>
"""

# Beige book theme: Anthropic Story series style.
BEIGE_BOOK_TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Lucky Blog</title>
<meta name="description" content="{excerpt}">
<meta name="keywords" content="{tags_csv}, lucky blog">
<link rel="canonical" href="https://luckyplz.com/blog/{slug_for_lang}/">

<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{excerpt}">
<meta property="og:url" content="https://luckyplz.com/blog/{slug_for_lang}/">
<meta property="og:locale" content="{og_locale}">
<meta property="og:site_name" content="Lucky Blog">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{excerpt}">

<link rel="alternate" hreflang="ko" href="https://luckyplz.com/blog/{slug_ko}/">
<link rel="alternate" hreflang="en" href="https://luckyplz.com/blog/{slug_en}/">
<link rel="alternate" hreflang="ja" href="https://luckyplz.com/blog/{slug_ja}/">
<link rel="alternate" hreflang="zh" href="https://luckyplz.com/blog/{slug_zh}/">
<link rel="alternate" hreflang="x-default" href="https://luckyplz.com/blog/{slug_en}/">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "{title}",
  "description": "{excerpt}",
  "inLanguage": "{lang}",
  "datePublished": "{date}",
  "dateModified": "{date}",
  "author": {{ "@type": "Organization", "name": "Lucky Blog", "url": "https://luckyplz.com/" }},
  "publisher": {{ "@type": "Organization", "name": "Lucky Blog", "logo": {{ "@type": "ImageObject", "url": "https://luckyplz.com/assets/icon-192.png" }}}},
  "mainEntityOfPage": {{ "@type": "WebPage", "@id": "https://luckyplz.com/blog/{slug_for_lang}/" }}
}}
</script>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;500;700;900&family=Noto+Serif+JP:wght@400;500;700;900&family=Noto+Serif+SC:wght@400;500;700;900&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">

<style>
  /* === Anthropic Series — Beige Book Theme === */
  :root {{
    --paper: #f5ebd8; --paper-light: #faf0d4; --paper-dark: #ebe0c8;
    --ink: #2c2416; --ink-soft: #4a3e2a; --ink-dim: #7a6a52;
    --brown: #8b6f47; --auburn: #c2410c; --gold: #b8860b;
    --line: #d4c5a8; --line-soft: #e6d9bd;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--paper); color: var(--ink);
    font-family: 'Noto Serif KR', 'Noto Serif JP', 'Noto Serif SC', 'Source Serif Pro', Georgia, serif;
    font-size: 17px; line-height: 1.72;
  }}
  .book {{ max-width: 720px; margin: 0 auto; padding: 0 24px 80px; background: var(--paper); }}
  .nav {{ display: flex; justify-content: space-between; align-items: center; padding: 18px 0; border-bottom: 1px solid var(--line-soft); margin-bottom: 32px; font-family: 'Cormorant Garamond', Georgia, serif; }}
  .nav a {{ color: var(--ink-soft); text-decoration: none; font-size: 13px; letter-spacing: 2px; text-transform: uppercase; }}
  .nav a:hover {{ color: var(--auburn); }}
  .nav .brand {{ font-weight: 600; font-style: italic; font-size: 16px; }}
  .hero {{ text-align: center; padding: 40px 0 36px; border-bottom: 1px solid var(--line); margin-bottom: 34px; }}
  .hero .series {{ font-family: 'Cormorant Garamond', Georgia, serif; font-style: italic; font-size: 16px; color: var(--brown); letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px; }}
  .hero .episode {{ font-family: 'Cormorant Garamond', Georgia, serif; font-weight: 600; font-size: 28px; color: var(--auburn); margin-bottom: 28px; letter-spacing: 1px; }}
  .hero h1 {{ font-family: 'Noto Serif KR', 'Noto Serif JP', 'Noto Serif SC', Georgia, serif; font-weight: 700; font-size: 34px; line-height: 1.35; color: var(--ink); margin-bottom: 24px; word-break: keep-all; }}
  .hero .subtitle {{ font-family: 'Cormorant Garamond', 'Noto Serif KR', 'Noto Serif JP', 'Noto Serif SC', Georgia, serif; font-style: italic; font-size: 19px; color: var(--ink-soft); line-height: 1.6; max-width: 580px; margin: 0 auto; word-break: keep-all; }}
  .hero .meta {{ margin-top: 36px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--ink-dim); letter-spacing: 2px; }}
  .hero .meta .dot {{ color: var(--brown); margin: 0 8px; }}
  .chapter {{ margin: 40px 0 0; }}
  .chapter-num {{ font-family: 'Cormorant Garamond', Georgia, serif; font-style: italic; font-size: 15px; color: var(--gold); letter-spacing: 4px; text-transform: uppercase; margin-bottom: 8px; }}
  .chapter h2 {{ font-family: 'Noto Serif KR', 'Noto Serif JP', 'Noto Serif SC', Georgia, serif; font-weight: 700; font-size: 28px; line-height: 1.3; color: var(--ink); margin-bottom: 18px; word-break: keep-all; }}
  .chapter h2 .ornament {{ display: block; width: 60px; height: 2px; background: var(--auburn); margin-top: 14px; }}
  .book p {{ margin-bottom: 16px; color: var(--ink); text-align: justify; word-break: normal; overflow-wrap: break-word; -webkit-hyphens: auto; hyphens: auto; }}
  .book p strong {{ color: var(--ink); font-weight: 700; }}
  .book p em {{ color: var(--brown); font-style: italic; }}
  .dropcap::first-letter {{ font-family: 'Cormorant Garamond', Georgia, serif; font-weight: 700; font-size: 64px; line-height: 0.85; float: left; margin: 6px 10px 0 0; color: var(--auburn); }}
  .pullquote {{ margin: 40px 0; padding: 24px 0 24px 28px; border-left: 3px solid var(--auburn); font-style: italic; font-size: 22px; line-height: 1.55; color: var(--ink); }}
  .pullquote .attr {{ display: block; margin-top: 14px; font-family: 'Cormorant Garamond', Georgia, serif; font-style: normal; font-size: 14px; color: var(--brown); letter-spacing: 1px; }}
  figure {{ margin: 40px -24px; text-align: center; }}
  figure img {{ width: 100%; height: auto; display: block; box-shadow: 0 8px 24px rgba(60, 40, 20, 0.12); }}
  figcaption {{ margin: 14px 24px 0; font-family: 'Cormorant Garamond', 'Noto Serif KR', 'Noto Serif JP', 'Noto Serif SC', Georgia, serif; font-style: italic; font-size: 14px; color: var(--ink-soft); line-height: 1.6; text-align: center; }}
  .sidebar {{ margin: 36px 0; padding: 20px 24px; background: var(--paper-light); border-left: 3px solid var(--gold); border-radius: 0 6px 6px 0; font-size: 15px; line-height: 1.7; color: var(--ink-soft); }}
  .sidebar h4 {{ font-family: 'Cormorant Garamond', Georgia, serif; font-weight: 700; font-size: 13px; color: var(--brown); letter-spacing: 3px; text-transform: uppercase; margin-bottom: 10px; }}
  .sidebar p {{ margin-bottom: 10px; font-size: 15px; }}
  .footnotes {{ margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--line); font-size: 13px; color: var(--ink-dim); line-height: 1.65; }}
  .footnotes h4 {{ font-family: 'Cormorant Garamond', Georgia, serif; font-weight: 600; font-size: 14px; color: var(--brown); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 14px; }}
  .footnotes ol {{ padding-left: 20px; }}
  .footnotes li {{ margin-bottom: 8px; }}
  .footer-block {{ margin-top: 60px; padding: 24px; background: var(--paper-dark); border-radius: 6px; font-size: 12px; line-height: 1.7; color: var(--ink-dim); }}
  .footer-block strong {{ color: var(--brown); }}
  @media (max-width: 540px) {{
    body {{ font-size: 16px; line-height: 1.6; }}
    .book {{ padding: 0 14px 52px; }}
    .hero h1 {{ font-size: 26px; }}
    .hero .subtitle {{ font-size: 17px; }}
    .hero .episode {{ font-size: 22px; }}
    .chapter h2 {{ font-size: 23px; }}
    .pullquote {{ font-size: 19px; padding-left: 20px; }}
    .dropcap::first-letter {{ font-size: 52px; }}
    figure {{ margin: 26px -14px; }}
  }}
</style>
</head>
<body>

<div class="book">

  <nav class="nav">
    <a href="/blog/">{nav_back}</a>
    <a href="/" class="brand">Lucky Blog</a>
    <a href="/blog/?cat={category}">{category_label}</a>
  </nav>

  <header class="hero">
    <div class="series">{series_label} · Series</div>
    <div class="episode">{episode_label}</div>
    <h1>{title}</h1>
    <p class="subtitle">{excerpt}</p>
    <div class="meta">
      <span>Published {date_iso_dot}</span>
      <span class="dot">·</span>
      <span>{read_min} min read</span>
      <span class="dot">·</span>
      <span>by Lucky Blog Editorial</span>
    </div>
  </header>

  <!-- BODY START — fill in chapters here -->

  <section class="chapter">
    <div class="chapter-num">Prologue</div>
    <h2>{placeholder_h2}<span class="ornament"></span></h2>
    <p class="dropcap"><strong>{placeholder_body_short}</strong> {placeholder_body}</p>
  </section>

  <!-- BODY END -->

  <div class="footnotes">
    <h4>{footnotes_label}</h4>
    <ol>
      <li>{footnotes_placeholder}</li>
    </ol>
  </div>

  <div class="footer-block">
    <p><strong>{disclaimer_label}</strong> · {disclaimer_body}</p>
  </div>

</div>

</body>
</html>
"""


# ---------------------------------------------------------------------------
# Locale-specific labels
# ---------------------------------------------------------------------------
LABELS = {
    "ko": {
        "nav_back": "← BLOG",
        "category_label": "카테고리",  # overridden per category below
        "footnotes_label": "참고 자료 · Sources",
        "footnotes_placeholder": "출처를 여기에 채워 넣습니다.",
        "placeholder_h2": "여는 글",
        "placeholder_body_short": "여기서부터",
        "placeholder_body": "본문을 시작합니다. 본 텍스트는 자리표시자이며, 실제 글로 교체해야 합니다.",
        "disclaimer_label": "📌 면책",
        "disclaimer_body": "본 글은 공개된 자료를 바탕으로 작성되었습니다. 모든 사실은 출처와 함께 검증되었으나, 본 글의 해석과 서술의 톤은 작성자의 편집입니다.",
    },
    "en": {
        "nav_back": "← BLOG",
        "category_label": "Category",
        "footnotes_label": "References · Sources",
        "footnotes_placeholder": "Fill in your source citations here.",
        "placeholder_h2": "Opening",
        "placeholder_body_short": "From here",
        "placeholder_body": "the body begins. This placeholder text should be replaced with the actual article.",
        "disclaimer_label": "📌 Disclaimer",
        "disclaimer_body": "This article is based on publicly available materials. All facts have been verified with sources, but the interpretation and editorial tone are the author's own.",
    },
    "ja": {
        "nav_back": "← BLOG",
        "category_label": "カテゴリー",
        "footnotes_label": "参考資料 · Sources",
        "footnotes_placeholder": "出典をここに記入してください。",
        "placeholder_h2": "はじめに",
        "placeholder_body_short": "ここから",
        "placeholder_body": "本文が始まります。このプレースホルダーは実際の記事に置き換えてください。",
        "disclaimer_label": "📌 免責",
        "disclaimer_body": "本記事は公開資料に基づいて作成されました。すべての事実は出典とともに検証されていますが、解釈と編集トーンは執筆者によるものです。",
    },
    "zh": {
        "nav_back": "← 博客",
        "category_label": "分类",
        "footnotes_label": "参考资料 · Sources",
        "footnotes_placeholder": "请在此处填写出处。",
        "placeholder_h2": "开篇",
        "placeholder_body_short": "从这里",
        "placeholder_body": "正文开始。此占位文本应替换为实际文章。",
        "disclaimer_label": "📌 免责声明",
        "disclaimer_body": "本文基于公开资料撰写。所有事实均已与出处核实，但解读与编辑语气由作者负责。",
    },
}

OG_LOCALES = {"ko": "ko_KR", "en": "en_US", "ja": "ja_JP", "zh": "zh_CN"}

CATEGORY_LABELS = {
    "stocks":         {"ko": "증시", "en": "Markets", "ja": "株式市場", "zh": "股市"},
    "industry":       {"ko": "산업", "en": "Industry", "ja": "産業", "zh": "产业"},
    "ai-tech":        {"ko": "AI", "en": "AI", "ja": "AI", "zh": "AI"},
    "space-tech":     {"ko": "우주", "en": "Space", "ja": "宇宙", "zh": "太空"},
    "robotics":       {"ko": "로봇", "en": "Robotics", "ja": "ロボット", "zh": "机器人"},
    "football":       {"ko": "축구", "en": "Football", "ja": "サッカー", "zh": "足球"},
    "baseball":       {"ko": "야구", "en": "Baseball", "ja": "野球", "zh": "棒球"},
    "gaming-history": {"ko": "게임", "en": "Games", "ja": "ゲーム", "zh": "游戏"},
}


# ---------------------------------------------------------------------------
# File generation
# ---------------------------------------------------------------------------
def render_html(lang: str, args, slug_ko: str, slug_en: str, slug_ja: str, slug_zh: str,
                title: str, excerpt: str, theme: str) -> str:
    """Render the HTML for a single language version."""
    slug_for_lang = {"ko": slug_ko, "en": slug_en, "ja": slug_ja, "zh": slug_zh}[lang]
    labels = LABELS[lang].copy()
    labels["category_label"] = CATEGORY_LABELS.get(args.category, {}).get(lang, args.category)

    tmpl = BEIGE_BOOK_TEMPLATE if theme == "beige-book" else STANDARD_TEMPLATE

    series_info = VALID_SERIES.get(args.series, {})
    series_label = series_info.get("series_label", "")
    episode_label = f"Episode {args.episode}" if args.episode else ""

    date_iso = args.date
    date_iso_dot = date_iso.replace("-", "·")

    ctx = {
        "lang": lang,
        "title": title,
        "excerpt": excerpt,
        "tags_csv": args.tags or "",
        "slug_for_lang": slug_for_lang,
        "slug_ko": slug_ko, "slug_en": slug_en, "slug_ja": slug_ja, "slug_zh": slug_zh,
        "og_locale": OG_LOCALES[lang],
        "date": date_iso,
        "date_iso_dot": date_iso_dot,
        "read_min": args.read_min,
        "category": args.category,
        "series_label": series_label,
        "episode_label": episode_label,
        **labels,
    }
    return tmpl.format(**ctx)


def make_posts_js_entry(slug: str, lang: str, args, title: str, excerpt: str,
                        slug_ko: str, slug_en: str, slug_ja: str, slug_zh: str) -> str:
    """Return a single posts.js entry (JS object literal) for one language.

    Uses the new `alts` object convention (forward-linking to all 3 sibling
    languages). Also writes a backward-compat single `alt` field pointing
    to the ko (or en if entry IS ko) slug so older site code keeps working.
    """
    tags_arr = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    tags_arr.append("lucky blog")
    tags_js = "[" + ", ".join(f"'{escape_js(t)}'" for t in tags_arr) + "]"

    # Build the alts object: all sibling languages except this entry's lang
    all_slugs = {"ko": slug_ko, "en": slug_en, "ja": slug_ja, "zh": slug_zh}
    alts_obj = {k: v for k, v in all_slugs.items() if k != lang}
    alts_js = "{ " + ", ".join(f"{k}: '{v}'" for k, v in alts_obj.items()) + " }"

    # Backward-compat single `alt` field: en if entry is ko, else ko
    alt_legacy = slug_en if lang == "ko" else slug_ko

    return f"""    {{
        slug: '{slug}',
        lang: '{lang}',
        category: '{args.category}',
        date: '{args.date}',
        readMinutes: {args.read_min},
        coverEmoji: '{args.cover_emoji}',
        tags: {tags_js},
        title: "{escape_js(title)}",
        excerpt: '{escape_js(excerpt)}',
        alt: '{alt_legacy}',
        alts: {alts_js},
    }},
"""


def make_sitemap_url(slug: str, args, slug_ko: str, slug_en: str,
                     slug_ja: str, slug_zh: str) -> str:
    return f"""    <url>
        <loc>https://luckyplz.com/blog/{slug}/</loc>
        <lastmod>{args.date}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.85</priority>
        <xhtml:link rel="alternate" hreflang="ko" href="https://luckyplz.com/blog/{slug_ko}/"/>
        <xhtml:link rel="alternate" hreflang="en" href="https://luckyplz.com/blog/{slug_en}/"/>
        <xhtml:link rel="alternate" hreflang="ja" href="https://luckyplz.com/blog/{slug_ja}/"/>
        <xhtml:link rel="alternate" hreflang="zh" href="https://luckyplz.com/blog/{slug_zh}/"/>
        <xhtml:link rel="alternate" hreflang="x-default" href="https://luckyplz.com/blog/{slug_en}/"/>
    </url>
"""


def escape_js(s: str) -> str:
    """Escape a string for use inside a JS single-quoted literal."""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')


# ---------------------------------------------------------------------------
# Update posts.js / sitemap.xml
# ---------------------------------------------------------------------------
def insert_posts_js_entries(entries: list[str]) -> None:
    """Insert 3 entries at the top of window.BLOG_POSTS = [ ... ]."""
    content = POSTS_JS.read_text(encoding="utf-8")
    # Find the opening "window.BLOG_POSTS = [\n"
    m = re.search(r"window\.BLOG_POSTS\s*=\s*\[\s*\n", content)
    if not m:
        raise RuntimeError("Could not find 'window.BLOG_POSTS = [' in posts.js")
    insert_at = m.end()
    combined = "".join(entries)
    new_content = content[:insert_at] + combined + content[insert_at:]
    POSTS_JS.write_text(new_content, encoding="utf-8")


def insert_sitemap_urls(url_blocks: list[str]) -> None:
    """Insert 3 url blocks before </urlset>."""
    content = SITEMAP.read_text(encoding="utf-8")
    if "</urlset>" not in content:
        raise RuntimeError("Could not find </urlset> in sitemap.xml")
    combined = "\n".join(url_blocks)
    new_content = content.replace("</urlset>", combined + "\n</urlset>")
    SITEMAP.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(
        description="Scaffold a new blog post in ko + en + ja + zh (mandatory).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--slug", required=True, help="kebab-case base slug (ko version).")
    p.add_argument("--category", required=True, choices=sorted(VALID_CATEGORIES))
    p.add_argument("--title-ko", required=True, dest="title_ko")
    p.add_argument("--title-en", required=True, dest="title_en")
    p.add_argument("--title-ja", required=True, dest="title_ja")
    p.add_argument("--title-zh", required=True, dest="title_zh")
    p.add_argument("--excerpt-ko", default="", dest="excerpt_ko")
    p.add_argument("--excerpt-en", default="", dest="excerpt_en")
    p.add_argument("--excerpt-ja", default="", dest="excerpt_ja")
    p.add_argument("--excerpt-zh", default="", dest="excerpt_zh")
    p.add_argument("--read-min", type=int, default=8, dest="read_min")
    p.add_argument("--cover-emoji", default="📖", dest="cover_emoji")
    p.add_argument("--tags", default="", help="Comma-separated tags.")
    p.add_argument("--series", choices=sorted(VALID_SERIES), default=None,
                   help="Series name. Applies series-specific theme.")
    p.add_argument("--theme", choices=["standard", "beige-book"], default=None,
                   help="Override theme. Default: series default, or 'standard'.")
    p.add_argument("--episode", type=int, default=None,
                   help="Episode number (only meaningful with --series).")
    p.add_argument("--date", default=None,
                   help="Publish date YYYY-MM-DD. Default: today KST.")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing directories.")

    args = p.parse_args()

    # Defaults
    if not args.date:
        args.date = datetime.datetime.now(KST).strftime("%Y-%m-%d")

    # Theme resolution: explicit --theme > series default > standard.
    if args.theme is None:
        if args.series and args.series in VALID_SERIES:
            args.theme = VALID_SERIES[args.series]["theme"]
        else:
            args.theme = "standard"

    # Default excerpts to titles if not provided
    if not args.excerpt_ko:
        args.excerpt_ko = args.title_ko
    if not args.excerpt_en:
        args.excerpt_en = args.title_en
    if not args.excerpt_ja:
        args.excerpt_ja = args.title_ja
    if not args.excerpt_zh:
        args.excerpt_zh = args.title_zh

    slug_ko = args.slug
    slug_en = f"{args.slug}-en"
    slug_ja = f"{args.slug}-ja"
    slug_zh = f"{args.slug}-zh"

    # Check for existing
    for s in (slug_ko, slug_en, slug_ja, slug_zh):
        d = BLOG / s
        if d.exists() and not args.force:
            print(f"[error] {d} already exists. Use --force to overwrite.", file=sys.stderr)
            sys.exit(1)

    # Create directories
    for s in (slug_ko, slug_en, slug_ja, slug_zh):
        (BLOG / s).mkdir(parents=True, exist_ok=True)

    # Render and write 4 HTMLs
    payload = [
        ("ko", slug_ko, args.title_ko, args.excerpt_ko),
        ("en", slug_en, args.title_en, args.excerpt_en),
        ("ja", slug_ja, args.title_ja, args.excerpt_ja),
        ("zh", slug_zh, args.title_zh, args.excerpt_zh),
    ]
    for lang, slug, title, excerpt in payload:
        html = render_html(lang, args, slug_ko, slug_en, slug_ja, slug_zh, title, excerpt, args.theme)
        (BLOG / slug / "index.html").write_text(html, encoding="utf-8")
        print(f"[create] public/blog/{slug}/index.html ({len(html)} bytes)")

    # Update posts.js (4 entries at top)
    entries = []
    for lang, slug, title, excerpt in payload:
        entries.append(make_posts_js_entry(slug, lang, args, title, excerpt,
                                           slug_ko, slug_en, slug_ja, slug_zh))
    insert_posts_js_entries(entries)
    print(f"[update] public/blog/posts.js (4 entries inserted at top)")

    # Update sitemap.xml (4 url blocks)
    urls = []
    for _, slug, _, _ in payload:
        urls.append(make_sitemap_url(slug, args, slug_ko, slug_en, slug_ja, slug_zh))
    insert_sitemap_urls(urls)
    print(f"[update] public/sitemap.xml (4 url blocks added)")

    print()
    print("✓ Scaffold complete. Next steps:")
    print(f"  1. Fill body in 4 files (search for '<!-- BODY START -->')")
    print(f"  2. python scripts/inject-blog-desktop-css.py")
    print(f"  3. bash scripts/bump-cache.sh")
    print(f"  4. git add . && git commit -m 'feat(blog): publish {args.slug} (ko+en+ja+zh)'")
    print(f"  5. git pull --rebase -X theirs origin main && git push origin HEAD:main")
    print()
    print(f"Preview URLs after deploy:")
    print(f"  KO: https://luckyplz.com/blog/{slug_ko}/")
    print(f"  EN: https://luckyplz.com/blog/{slug_en}/")
    print(f"  JA: https://luckyplz.com/blog/{slug_ja}/")
    print(f"  ZH: https://luckyplz.com/blog/{slug_zh}/")


if __name__ == "__main__":
    main()
