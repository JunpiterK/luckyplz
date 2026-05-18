"""Auto Daily Post pipeline.

Generates one of 4 daily blog slots (us-close / kr-open / kr-close / us-premarket)
by calling Claude with web_search, rendering bilingual HTML + OG images,
updating posts.js / sitemap.xml, bumping cache, and committing to git.

Usage:
    python scripts/auto-daily-post.py --slot us-close                # uses "today"
    python scripts/auto-daily-post.py --slot kr-open --date 2026-05-12
    python scripts/auto-daily-post.py --slot us-close --dry-run      # no git push

Env:
    ANTHROPIC_API_KEY   required (loaded from env or .env)
    LP_GIT_PUSH=1       set to actually git push (default: 0 in dev, 1 in CI)
    LP_SKIP_CACHE=1     skip bump-cache.sh (faster local testing)
"""

from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytz

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SCRIPTS = ROOT / "scripts"
PROMPTS = SCRIPTS / "prompts"
TEMPLATES = SCRIPTS / "templates"
BLOG_DIR = PUBLIC / "blog"
ASSETS_BLOG = PUBLIC / "assets" / "blog"

KST = pytz.timezone("Asia/Seoul")
ET = pytz.timezone("US/Eastern")

# ---------------------------------------------------------------------------
# Slot definitions — single source of truth
# ---------------------------------------------------------------------------
SLOTS = {
    "us-close": {
        "prompt": "us-close-recap.md",
        "slug_prefix": "us-tech-recap",
        # "trading_date" = US ET close date the post covers
        "trading_date_offset_days": -1,    # publish day 06:00 KST covers prev US session
        "category": "industry",
        "read_min": 8,
        "cover_emoji": "🇺🇸",
        "header_label_ko": "🇺🇸 미국 테크 마감 리캡",
        "header_label_en": "🇺🇸 US TECH DAILY RECAP",
    },
    "kr-open": {
        "prompt": "kr-open-brief.md",
        "slug_prefix": "kr-open-brief",
        "trading_date_offset_days": 0,
        "category": "industry",
        "read_min": 6,
        "cover_emoji": "🇰🇷",
        "header_label_ko": "🇰🇷 한국장 개장 브리핑",
        "header_label_en": "🇰🇷 KOREA OPEN BRIEF",
    },
    "kr-close": {
        "prompt": "kr-close-recap.md",
        "slug_prefix": "kr-tech-recap",
        "trading_date_offset_days": 0,
        "category": "industry",
        "read_min": 7,
        "cover_emoji": "🇰🇷",
        "header_label_ko": "🇰🇷 한국 테크 마감 리캡",
        "header_label_en": "🇰🇷 KOREA TECH DAILY RECAP",
    },
    "us-premarket": {
        "prompt": "us-premarket.md",
        "slug_prefix": "us-premarket",
        "trading_date_offset_days": 0,    # US session that opens tonight (KST 22:30)
        "category": "industry",
        "read_min": 6,
        "cover_emoji": "🇺🇸",
        "header_label_ko": "🇺🇸 미국 프리마켓 브리핑",
        "header_label_en": "🇺🇸 US PRE-MARKET BRIEF",
    },
}


# ---------------------------------------------------------------------------
# Anthropic call
# ---------------------------------------------------------------------------
def call_claude(prompt: str, *, model: str = "claude-sonnet-4-5", max_tokens: int = 12000) -> dict:
    """Call Claude API with web_search tool. Returns parsed JSON dict."""
    import anthropic

    client = anthropic.Anthropic()

    messages = [{"role": "user", "content": prompt}]
    # Web search tool (Anthropic native, model server-side fetches)
    tools = [
        {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 12,
        }
    ]

    print(f"[claude] calling {model} with {max_tokens=}, web_search enabled (max_uses=12)")
    t0 = time.time()
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        tools=tools,
        messages=messages,
    )
    dt = time.time() - t0
    print(f"[claude] response in {dt:.1f}s — stop_reason={resp.stop_reason}")

    # Collect text from final assistant message
    text_chunks = []
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            text_chunks.append(block.text)
    full = "\n".join(text_chunks).strip()

    # Strip possible ```json fences
    if full.startswith("```"):
        full = re.sub(r"^```(?:json)?\s*", "", full)
        full = re.sub(r"\s*```$", "", full)

    try:
        return json.loads(full)
    except json.JSONDecodeError:
        # Last-resort: find first { … last } window
        m = re.search(r"\{.*\}", full, re.DOTALL)
        if not m:
            raise SystemExit(f"Could not parse Claude output as JSON.\n---\n{full[:2000]}")
        candidate = m.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Defensive cleanup #1: drop trailing commas before } or ]
            cleaned = re.sub(r",(\s*[}\]])", r"\1", candidate)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                # Defensive cleanup #2: try json-repair-style fallback
                # (collapse unescaped newlines inside strings, lenient parse)
                try:
                    import ast
                    return ast.literal_eval(cleaned)
                except Exception as e:
                    raise SystemExit(
                        f"Could not parse Claude output as JSON even after cleanup: {e}\n"
                        f"--- first 2000 chars of candidate ---\n{candidate[:2000]}\n"
                        f"--- last 500 chars of candidate ---\n{candidate[-500:]}"
                    )


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------
def html_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def pct_class(pct: float) -> str:
    if pct >= 0.05:
        return "up"
    if pct <= -0.05:
        return "down"
    return "flat"


def heat_class(pct: float) -> str:
    if pct >= 5: return "heat-vstrong"
    if pct >= 1.5: return "heat-strong"
    if pct >= 0.3: return "heat-mild"
    if pct >= -0.3: return "heat-flat"
    if pct >= -1.5: return "heat-down"
    return "heat-vdown"


def fmt_pct(p: float) -> str:
    sign = "+" if p >= 0 else ""
    return f"{sign}{p:.1f}%"


def render_indices_block(indices: list[dict], lang: str) -> str:
    """6-card 3-column grid (indices snapshot)."""
    cards = []
    for idx in indices[:6]:
        chg = idx.get("change_pct", 0)
        chg_cls = pct_class(chg)
        chg_str = fmt_pct(chg) if isinstance(chg, (int, float)) else str(chg)
        tag = idx.get("tag", "")
        # simple sparkline (8 points, derived from change sign)
        if chg > 0:
            sp = "0,18 14,17 28,15 42,14 56,11 70,9 84,7 100,4"
            color = "#7fffb2"
        elif chg < 0:
            sp = "0,4 14,7 28,9 42,11 56,14 70,15 84,17 100,18"
            color = "#ff7888"
        else:
            sp = "0,12 14,12 28,11 42,12 56,12 70,11 84,12 100,12"
            color = "#5a6a85"
        cards.append(f"""
  <div class="idx-card">
    <div class="idx-name">{html_escape(idx['name'])}</div>
    <div class="idx-val">{html_escape(str(idx['value']))}</div>
    <div class="idx-chg {chg_cls}">{html_escape(chg_str)}</div>
    <svg viewBox="0 0 100 24" preserveAspectRatio="none"><polyline points="{sp}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/></svg>
    <div class="idx-tag">{html_escape(tag)}</div>
  </div>""")
    title = "▸ Indices Snapshot" if lang == "en" else "▸ 주요 지수 스냅샷"
    return f"""<div class="section-title">{title}</div>
<div class="idx-grid">{''.join(cards)}</div>
"""


def render_mag7(mag7: list[dict], lang: str) -> str:
    if not mag7:
        return ""
    tiles = []
    for m in mag7[:8]:
        cls = pct_class(m.get("change_pct", 0))
        chg = fmt_pct(m.get("change_pct", 0)) if isinstance(m.get("change_pct"), (int, float)) else str(m.get("change_pct"))
        tiles.append(f"""
  <div class="mag-tile {cls}">
    <div class="mag-tick">{html_escape(m['ticker'])}</div>
    <div class="mag-px">{html_escape(str(m.get('price','—')))}</div>
    <div class="mag-pct {cls}">{html_escape(chg)}</div>
  </div>""")
    title = "▸ Magnificent 7 · Closing Strip" if lang == "en" else "▸ 매그니피센트 7 · 종가 스트립"
    return f"""<div class="section-title">{title}</div>
<div class="mag-grid">{''.join(tiles)}</div>
"""


def render_themes(themes: list[dict], lang: str) -> str:
    if not themes:
        return ""
    tiles = []
    for t in themes[:9]:
        pct = t.get("pct", 0)
        cls = heat_class(pct)
        label = t.get(f"label_{lang}", t.get("label_en") or t.get("label_ko") or "")
        tiles.append(f"""
  <div class="heat-tile {cls}">
    <div class="hsec">{html_escape(label)}</div>
    <div class="hpct">{html_escape(fmt_pct(pct))}</div>
    <div class="hnames">{html_escape(t.get('names',''))}</div>
  </div>""")
    title = "▸ Tech Theme Heatmap · 1-Day" if lang == "en" else "▸ 테크 테마 히트맵 · 당일"
    return f"""<div class="section-title">{title}</div>
<div class="heat-grid">{''.join(tiles)}</div>
"""


def render_movers(items: list[dict], lang: str, kind: str) -> str:
    if not items:
        return ""
    rows = []
    for it in items[:10]:
        cls = "up" if kind == "winners" else "down"
        arrow = "⬆" if kind == "winners" else "⬇"
        head_cls = "w" if kind == "winners" else "l"
        name = it.get(f"name_{lang}") or it.get("name_en") or it.get("name_ko") or ""
        trig = it.get(f"trigger_{lang}") or it.get("trigger_en") or it.get("trigger_ko") or ""
        chg = it.get("change_pct", 0)
        rows.append(f"""
  <div class="mov-row">
    <div class="mov-tick">{html_escape(it['ticker'])}<span class="nm">{html_escape(name)}</span></div>
    <div class="mov-px">{html_escape(str(it.get('price','—')))}</div>
    <div class="mov-pct {cls}">{html_escape(fmt_pct(chg))}</div>
    <div class="mov-trig">{html_escape(trig)}</div>
  </div>""")
    if kind == "winners":
        title = "▸ Top Winners" if lang == "en" else "▸ 상승 리더"
        head_label = f"{arrow} WINNERS" if lang == "en" else f"{arrow} 상승"
    else:
        title = "▸ Top Losers / Pullbacks" if lang == "en" else "▸ 하락·차익실현 리더"
        head_label = f"{arrow} LOSERS" if lang == "en" else f"{arrow} 하락"
    return f"""<div class="section-title">{title}</div>
<div class="mov-card">
  <div class="mov-head {head_cls}">{head_label}</div>
  {''.join(rows)}
</div>
"""


def render_news(news: list[dict], lang: str) -> str:
    if not news:
        return ""
    cards = []
    for n in news[:6]:
        tag = n.get(f"tag_{lang}") or n.get("tag_en") or ""
        title = n.get(f"title_{lang}") or n.get("title_en") or ""
        body = n.get(f"body_{lang}") or n.get("body_en") or ""
        src = n.get("source", "")
        url = n.get("source_url", "")
        src_html = f'<a href="{html_escape(url)}" target="_blank" rel="noopener">{html_escape(src)}</a>' if url else html_escape(src)
        cards.append(f"""
<div class="news-card">
  <span class="ntag">{html_escape(tag)}</span>
  <h4>{html_escape(title)}</h4>
  <p>{html_escape(body)}</p>
  <span class="src">{src_html}</span>
</div>""")
    title = "▸ Filtered News" if lang == "en" else "▸ 필터된 뉴스"
    return f"""<div class="section-title">{title}</div>
{''.join(cards)}
"""


def render_watch(watch: dict, lang: str) -> str:
    if not watch:
        return ""
    rows = []
    label_map_ko = [("tue", "화 5/12"), ("wed", "수 5/13"), ("thu", "목 5/14"),
                    ("risk", "리스크"), ("flow", "플로우")]
    label_map_en = [("tue", "TUE"), ("wed", "WED"), ("thu", "THU"),
                    ("risk", "RISK"), ("flow", "FLOW")]
    for key, day_label in (label_map_ko if lang == "ko" else label_map_en):
        body = watch.get(f"{key}_{lang}")
        if not body:
            continue
        rows.append(f"""
  <div class="watch-row">
    <div class="watch-day">{html_escape(day_label)}</div>
    <div class="watch-body">{body}</div>
  </div>""")
    if not rows:
        return ""
    title = "▸ Tomorrow's Watchlist" if lang == "en" else "▸ 내일 워치리스트"
    h3 = "📅 KEY EARNINGS · EVENTS · THIS WEEK" if lang == "en" else "📅 이번 주 핵심 어닝 · 이벤트"
    return f"""<div class="section-title">{title}</div>
<div class="watch-card">
  <h3>{h3}</h3>
  {''.join(rows)}
</div>
"""


def render_sections(slot: str, data: dict, lang: str) -> str:
    """Stitch the body sections based on slot type."""
    parts = []
    if slot == "us-close":
        parts.append(render_indices_block(data.get("indices", []), lang))
        parts.append(render_mag7(data.get("mag7", []), lang))
        parts.append(render_themes(data.get("themes", []), lang))
        parts.append(render_movers(data.get("winners", []), lang, "winners"))
        parts.append(render_movers(data.get("losers", []), lang, "losers"))
        parts.append(render_news(data.get("news", []), lang))
        parts.append(render_watch(data.get("watch", {}), lang))
    elif slot == "kr-open":
        parts.append(render_indices_block(data.get("overnight_us", []), lang))
        parts.append(render_news(data.get("kr_news", []), lang))
    elif slot == "kr-close":
        parts.append(render_indices_block(data.get("kr_indices", []), lang))
        parts.append(render_themes(data.get("kr_themes", []), lang))
        parts.append(render_movers(data.get("winners", []), lang, "winners"))
        parts.append(render_movers(data.get("losers", []), lang, "losers"))
        parts.append(render_news(data.get("kr_news", []), lang))
    elif slot == "us-premarket":
        parts.append(render_indices_block(data.get("futures", []), lang))
        pm = data.get("premarket_movers", {}) or {}
        parts.append(render_movers(pm.get("winners", []), lang, "winners"))
        parts.append(render_movers(pm.get("losers", []), lang, "losers"))
    return "\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Full HTML render
# ---------------------------------------------------------------------------
def render_html(slot: str, lang: str, data: dict, *, slug: str, build: str, og_image_filename: str,
                trading_date: str, publish_date: str) -> str:
    cfg = SLOTS[slot]
    template = (TEMPLATES / "daily-base.html").read_text(encoding="utf-8")

    base_url = "https://luckyplz.com"
    canonical = f"{base_url}/blog/{slug}-{lang}/" if lang == "en" else f"{base_url}/blog/{slug}/"
    href_ko = f"{base_url}/blog/{slug}/"
    href_en = f"{base_url}/blog/{slug}-en/"

    title = data.get(f"headline_{lang}", "")
    title_full = f"{title} | Lucky Please"
    summary = data.get(f"summary_{lang}", "")
    bottom_body = data.get(f"bottom_line_{lang}", "")
    bottom_title = "BOTTOM LINE" if lang == "en" else "BOTTOM LINE · 포지셔닝"

    keywords_map = {
        "us-close": ("미국 증시 마감, 테크 리캡, S&P Nasdaq, Mag 7, 데일리 리뷰, lucky please",
                     "US tech recap, S&P Nasdaq close, Magnificent 7, daily debrief, lucky please"),
        "kr-open": ("한국증시 개장, 코스피 개장, 외인 매수 예상, ADR, 매그니피센트 7, 데일리 브리프",
                    "Korea market open brief, KOSPI futures, ADR overnight, KR semis"),
        "kr-close": ("한국증시 마감, 코스피 마감, 외인 수급, 한국 섹터, 데일리 리캡",
                     "Korea market close, KOSPI, foreign flow, KR tech sectors"),
        "us-premarket": ("미국 프리마켓, 야간 시황, 어닝 캘린더, 매크로 이벤트, 데일리 브리프",
                         "US premarket, earnings calendar, macro events, daily brief"),
    }
    kw_ko, kw_en = keywords_map[slot]
    keywords = kw_ko if lang == "ko" else kw_en

    # OG meta
    og_locale = "ko_KR" if lang == "ko" else "en_US"
    og_locale_alt = "en_US" if lang == "ko" else "ko_KR"
    og_image_url = f"{base_url}/assets/blog/{og_image_filename}?v={build}"
    og_image_alt = f"{title} — {summary[:80]}"

    # JSON-LD
    jsonld_blog = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": summary[:200],
        "datePublished": publish_date,
        "dateModified": publish_date,
        "author": {"@type": "Organization", "name": "Lucky Please", "url": "https://luckyplz.com/"},
        "publisher": {"@type": "Organization", "name": "Lucky Please",
                      "logo": {"@type": "ImageObject", "url": "https://luckyplz.com/assets/icon-192.png"}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
    }
    breadcrumb_label = ("미국 테크 마감 리캡" if (slot == "us-close" and lang == "ko") else
                        "US Tech Recap" if (slot == "us-close" and lang == "en") else
                        "한국장 개장 브리핑" if (slot == "kr-open" and lang == "ko") else
                        "Korea Open Brief" if (slot == "kr-open" and lang == "en") else
                        "한국 테크 마감 리캡" if (slot == "kr-close" and lang == "ko") else
                        "Korea Tech Recap" if (slot == "kr-close" and lang == "en") else
                        "미국 프리마켓 브리핑" if (slot == "us-premarket" and lang == "ko") else
                        "US Pre-Market Brief")
    jsonld_crumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1,
             "name": "홈" if lang == "ko" else "Home", "item": f"{base_url}/"},
            {"@type": "ListItem", "position": 2,
             "name": "블로그" if lang == "ko" else "Blog", "item": f"{base_url}/blog/"},
            {"@type": "ListItem", "position": 3, "name": breadcrumb_label, "item": canonical},
        ],
    }

    # Badges from indices (top 5 by absolute change)
    indices = (data.get("indices") or data.get("kr_indices") or data.get("futures") or data.get("overnight_us") or [])
    badges = []
    for idx in indices[:5]:
        cls = "badge-green" if (idx.get("change_pct", 0) > 0) else ("badge-orange" if idx.get("change_pct", 0) < 0 else "badge-blue")
        badges.append(f'<span class="badge {cls}">{html_escape(idx["name"])} {fmt_pct(idx.get("change_pct", 0))}</span>')
    header_badges = "\n    ".join(badges)

    disclaimer_ko = ("<strong>📌 데일리 리캡 · {ts}</strong><br>"
                     "공개 시장 데이터 기반 자동 큐레이션. Yahoo Finance · Investing.com · KRX · CNBC · TheStreet 등.<br>"
                     "매수/매도 권유가 아니며 투자 결정은 독자 본인 책임입니다.").format(ts=publish_date)
    disclaimer_en = ("<strong>📌 Daily debrief · {ts}</strong><br>"
                     "Auto-curated from public market data: Yahoo Finance · Investing.com · KRX · CNBC · TheStreet.<br>"
                     "Not a recommendation. All investment decisions are your responsibility.").format(ts=publish_date)
    disclaimer = disclaimer_ko if lang == "ko" else disclaimer_en

    # Sources block (appended to footer)
    # Claude may return sources as either [{"url": "...", "title": "..."}]
    # or [url_string, ...]. Defensive: handle both shapes + skip empties.
    sources = data.get("sources", []) or []
    src_lines = []
    for s in sources[:8]:
        if isinstance(s, str):
            url, title = s, s
        elif isinstance(s, dict):
            url = s.get("url", "") or ""
            title = s.get("title", "") or url
        else:
            continue
        if not url:
            continue
        src_lines.append(f'<a href="{html_escape(url)}" target="_blank" rel="noopener">{html_escape(title)}</a>')
    src_html = " · ".join(src_lines)

    footer_ko = ("<strong>📢 출처 & 면책 조항</strong><br>"
                 f"{publish_date} 작성 · 출처: {src_html}<br>"
                 "매수/매도 권유가 아니며 투자 책임은 독자 본인에게 있습니다.")
    footer_en = ("<strong>📢 Sources & disclaimer</strong><br>"
                 f"Published {publish_date} · Sources: {src_html}<br>"
                 "Not a recommendation. All investment decisions are your responsibility.")
    footer_disclaimer = footer_ko if lang == "ko" else footer_en

    # Related links — link to sibling slots of same trading_date if exist
    if lang == "ko":
        related_title = "관련 글 RELATED"
        related_links = (
            f'<a href="/blog/daily/">데일리 시리즈 인덱스 전체 보기 →</a>\n'
            f'<a href="/blog/semiconductor-rally-2026/">반도체 슈퍼랠리 2026 — 한미 반도체주는 어디까지 오를까?</a>'
        )
    else:
        related_title = "RELATED"
        related_links = (
            f'<a href="/blog/daily/">See full daily series index →</a>\n'
            f'<a href="/blog/semiconductor-rally-2026-en/">Semiconductor Super-Rally 2026 — How High Can KR & US Chip Stocks Go?</a>'
        )

    # Body sections
    sections_html = render_sections(slot, data, lang)

    # Substitutions
    if lang == "ko":
        body_font = "'Noto Sans KR', sans-serif"
        font_url = "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=JetBrains+Mono:wght@400;700&family=Bebas+Neue&display=swap"
        nav_back = "← BLOG"
        header_label = cfg["header_label_ko"] + f" · {publish_date}"
    else:
        body_font = "'Inter', sans-serif"
        font_url = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700&family=JetBrains+Mono:wght@400;700&family=Bebas+Neue&display=swap"
        nav_back = "← BLOG"
        header_label = cfg["header_label_en"] + f" · {publish_date}"

    repl = {
        "{{LANG}}": lang,
        "{{BUILD}}": build,
        "{{TITLE}}": html_escape(title_full),
        "{{TITLE_SHORT}}": html_escape(title),
        "{{DESCRIPTION}}": html_escape(summary[:200]),
        "{{KEYWORDS}}": html_escape(keywords),
        "{{CANONICAL_URL}}": canonical,
        "{{HREFLANG_KO}}": href_ko,
        "{{HREFLANG_EN}}": href_en,
        "{{HREFLANG_DEFAULT}}": href_en if lang == "en" else href_ko,
        "{{OG_LOCALE}}": og_locale,
        "{{OG_LOCALE_ALT}}": og_locale_alt,
        "{{OG_DESCRIPTION}}": html_escape(summary[:200]),
        "{{OG_IMAGE_URL}}": og_image_url,
        "{{OG_IMAGE_ALT}}": html_escape(og_image_alt),
        "{{PUBLISHED_TIME}}": f"{publish_date}T00:00:00+09:00",
        "{{JSONLD_BLOGPOSTING}}": json.dumps(jsonld_blog, ensure_ascii=False),
        "{{JSONLD_BREADCRUMB}}": json.dumps(jsonld_crumb, ensure_ascii=False),
        "{{FONT_URL}}": font_url,
        "{{BODY_FONT}}": body_font,
        "{{NAV_BACK}}": nav_back,
        "{{HEADER_LABEL}}": html_escape(header_label),
        "{{HEADER_H1}}": _split_h1(title),
        "{{HEADER_SUB}}": html_escape(summary[:120]),
        "{{HEADER_BADGES}}": header_badges,
        "{{DISCLAIMER}}": disclaimer,
        "{{SUMMARY}}": summary,
        "{{SECTIONS}}": sections_html,
        "{{BOTTOM_LINE_TITLE}}": html_escape(bottom_title),
        "{{BOTTOM_LINE_BODY}}": bottom_body,
        "{{FOOTER_DISCLAIMER}}": footer_disclaimer,
        "{{RELATED_TITLE}}": html_escape(related_title),
        "{{RELATED_LINKS}}": related_links,
    }
    out = template
    for k, v in repl.items():
        out = out.replace(k, v if isinstance(v, str) else str(v))
    return out


def _split_h1(title: str) -> str:
    """Split title into 2 lines for h1 styling with <span> accent."""
    if " — " in title:
        a, b = title.split(" — ", 1)
        return f"{html_escape(a)}<br><span>{html_escape(b)}</span>"
    if " · " in title:
        a, b = title.split(" · ", 1)
        return f"{html_escape(a)}<br><span>{html_escape(b)}</span>"
    words = title.split()
    if len(words) > 4:
        mid = len(words) // 2
        return f"{html_escape(' '.join(words[:mid]))}<br><span>{html_escape(' '.join(words[mid:]))}</span>"
    return f"<span>{html_escape(title)}</span>"


# ---------------------------------------------------------------------------
# OG image
# ---------------------------------------------------------------------------
def gen_og_image(slot: str, data: dict, lang: str, out_path: Path) -> None:
    """Delegate to gen-daily-og.py for per-slot OG."""
    from gen_daily_og import make_og  # type: ignore
    og = data.get("og_data", {})
    headline = data.get(f"headline_{lang}", "")
    label = SLOTS[slot][f"header_label_{lang}"]
    make_og(out_path, lang=lang, label=label, headline=headline, og_data=og)


# ---------------------------------------------------------------------------
# Site integration
# ---------------------------------------------------------------------------
def write_post_files(slug: str, html_ko: str, html_en: str, og_ko_path: Path, og_en_path: Path) -> None:
    dir_ko = BLOG_DIR / slug
    dir_en = BLOG_DIR / f"{slug}-en"
    dir_ko.mkdir(parents=True, exist_ok=True)
    dir_en.mkdir(parents=True, exist_ok=True)
    (dir_ko / "index.html").write_text(html_ko, encoding="utf-8")
    (dir_en / "index.html").write_text(html_en, encoding="utf-8")
    print(f"[write] {dir_ko}/index.html ({len(html_ko)} bytes)")
    print(f"[write] {dir_en}/index.html ({len(html_en)} bytes)")
    print(f"[write] OG ko: {og_ko_path}")
    print(f"[write] OG en: {og_en_path}")


def update_posts_js(slug: str, slot: str, data: dict, publish_date: str) -> None:
    cfg = SLOTS[slot]
    posts_path = PUBLIC / "blog" / "posts.js"
    raw = posts_path.read_text(encoding="utf-8")
    insert_marker = "window.BLOG_POSTS = ["
    idx = raw.find(insert_marker)
    if idx == -1:
        raise SystemExit("Could not find BLOG_POSTS array in posts.js")

    entry_ko = textwrap.dedent(f"""\
        {{
            slug: '{slug}',
            lang: 'ko',
            category: '{cfg["category"]}',
            date: '{publish_date}',
            readMinutes: {cfg["read_min"]},
            coverEmoji: '{cfg["cover_emoji"]}',
            tags: {json.dumps((data.get("og_tags_ko") or ['데일리 리캡', '미국증시', '한국증시', '테크']), ensure_ascii=False)},
            title: {json.dumps(data.get("headline_ko",""), ensure_ascii=False)},
            excerpt: {json.dumps(data.get("summary_ko","")[:180], ensure_ascii=False)},
            alt: '{slug}-en',
        }},
        {{
            slug: '{slug}-en',
            lang: 'en',
            category: '{cfg["category"]}',
            date: '{publish_date}',
            readMinutes: {cfg["read_min"]},
            coverEmoji: '{cfg["cover_emoji"]}',
            tags: {json.dumps((data.get("og_tags_en") or ['Daily Recap', 'US Markets', 'KR Markets', 'Tech']), ensure_ascii=False)},
            title: {json.dumps(data.get("headline_en",""), ensure_ascii=False)},
            excerpt: {json.dumps(data.get("summary_en","")[:180], ensure_ascii=False)},
            alt: '{slug}',
        }},""")
    # Indent each line by 4 spaces (already are by textwrap), then inject right after the marker
    new_raw = raw[: idx + len(insert_marker)] + "\n    " + entry_ko + raw[idx + len(insert_marker):]
    posts_path.write_text(new_raw, encoding="utf-8")
    print(f"[posts.js] prepended slug={slug}")


def update_sitemap(slug: str, publish_date: str) -> None:
    sm_path = PUBLIC / "sitemap.xml"
    raw = sm_path.read_text(encoding="utf-8")
    new_block = textwrap.dedent(f"""\
        <url>
            <loc>https://luckyplz.com/blog/{slug}/</loc>
            <lastmod>{publish_date}</lastmod>
            <changefreq>daily</changefreq>
            <priority>0.85</priority>
            <xhtml:link rel="alternate" hreflang="ko" href="https://luckyplz.com/blog/{slug}/"/>
            <xhtml:link rel="alternate" hreflang="en" href="https://luckyplz.com/blog/{slug}-en/"/>
            <xhtml:link rel="alternate" hreflang="x-default" href="https://luckyplz.com/blog/{slug}-en/"/>
        </url>

        <url>
            <loc>https://luckyplz.com/blog/{slug}-en/</loc>
            <lastmod>{publish_date}</lastmod>
            <changefreq>daily</changefreq>
            <priority>0.85</priority>
            <xhtml:link rel="alternate" hreflang="ko" href="https://luckyplz.com/blog/{slug}/"/>
            <xhtml:link rel="alternate" hreflang="en" href="https://luckyplz.com/blog/{slug}-en/"/>
            <xhtml:link rel="alternate" hreflang="x-default" href="https://luckyplz.com/blog/{slug}-en/"/>
        </url>

    """)
    anchor = "<url>\n        <loc>https://luckyplz.com/blog/us-tech-recap-2026-05-11/</loc>"
    if anchor in raw:
        raw = raw.replace(anchor, new_block + "    " + anchor.lstrip())
    else:
        raw = raw.replace("</urlset>", new_block + "</urlset>")
    sm_path.write_text(raw, encoding="utf-8")
    print(f"[sitemap] added {slug} / {slug}-en")


def bump_cache() -> None:
    if os.environ.get("LP_SKIP_CACHE"):
        print("[cache] skipped (LP_SKIP_CACHE)")
        return
    subprocess.run(["bash", "scripts/bump-cache.sh"], cwd=ROOT, check=True)


def git_push(slug: str, slot: str) -> None:
    if not os.environ.get("LP_GIT_PUSH"):
        print(f"[git] skipped (LP_GIT_PUSH not set). Manual: git add -A && git commit && git push")
        return
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    msg = (f"daily-{slot}: {slug} 자동 발행\n\n"
           f"- Auto-generated by scripts/auto-daily-post.py\n"
           f"- Slot: {slot}\n"
           f"- Data via Claude + web_search tool\n")
    subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print(f"[git] pushed {slug}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slot", required=True, choices=list(SLOTS.keys()))
    p.add_argument("--date", help="YYYY-MM-DD (KST publish date). Default: today KST.")
    p.add_argument("--dry-run", action="store_true", help="Skip git push and bump-cache.")
    p.add_argument("--model", default="claude-sonnet-4-5")
    args = p.parse_args()

    if args.dry_run:
        os.environ["LP_GIT_PUSH"] = ""
        os.environ["LP_SKIP_CACHE"] = "1"

    # Dates
    now_kst = datetime.now(KST)
    if args.date:
        publish_date = args.date
    else:
        publish_date = now_kst.strftime("%Y-%m-%d")

    cfg = SLOTS[args.slot]
    publish_dt = datetime.strptime(publish_date, "%Y-%m-%d")
    trading_date_dt = publish_dt + timedelta(days=cfg["trading_date_offset_days"])
    trading_date = trading_date_dt.strftime("%Y-%m-%d")

    slug = f"{cfg['slug_prefix']}-{trading_date}"
    print(f"[run] slot={args.slot} trading={trading_date} publish={publish_date} slug={slug}")

    # Load + fill prompt
    prompt_template = (PROMPTS / cfg["prompt"]).read_text(encoding="utf-8")
    prompt = prompt_template.replace("{trading_date}", trading_date).replace("{publish_date}", publish_date)

    # Force strict JSON-only output. Without this Claude occasionally wraps
    # the JSON in commentary or code fences, breaking the parser. Defensive
    # belt — see README "케이스 A — Claude JSON parse 실패".
    prompt += (
        "\n\n---\n"
        "CRITICAL OUTPUT FORMAT: Reply with ONLY the JSON object specified above. "
        "Start your response with `{` and end with `}`. "
        "No prose before. No prose after. No markdown code fences (no ```json). "
        "No commentary on what you did. No 'Here is the JSON:' preamble. "
        "Make sure all strings are properly escaped and there are no trailing commas. "
        "The entire response must be a single valid JSON object that can be parsed by Python's json.loads()."
    )

    # Call Claude
    data = call_claude(prompt, model=args.model)

    if data.get("skip"):
        print(f"[skip] {data.get('reason','holiday or no session')}. Exiting.")
        return

    # Read current build version (gets refreshed by bump-cache later)
    try:
        build = json.loads((PUBLIC / "build.json").read_text(encoding="utf-8"))["v"]
    except Exception:
        build = str(int(time.time()))

    # OG images (one per lang)
    ASSETS_BLOG.mkdir(parents=True, exist_ok=True)
    og_ko_filename = f"og-{slug}.png"
    og_en_filename = f"og-{slug}-en.png"
    sys.path.insert(0, str(SCRIPTS))
    gen_og_image(args.slot, data, "ko", ASSETS_BLOG / og_ko_filename)
    gen_og_image(args.slot, data, "en", ASSETS_BLOG / og_en_filename)

    # Render HTML
    html_ko = render_html(args.slot, "ko", data, slug=slug, build=build,
                          og_image_filename=og_ko_filename,
                          trading_date=trading_date, publish_date=publish_date)
    html_en = render_html(args.slot, "en", data, slug=slug, build=build,
                          og_image_filename=og_en_filename,
                          trading_date=trading_date, publish_date=publish_date)
    write_post_files(slug, html_ko, html_en,
                     ASSETS_BLOG / og_ko_filename, ASSETS_BLOG / og_en_filename)

    # Site integration
    update_posts_js(slug, args.slot, data, publish_date)
    update_sitemap(slug, publish_date)

    # Cache + git
    bump_cache()
    git_push(slug, args.slot)
    print(f"[done] {slug}")


if __name__ == "__main__":
    main()
