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
def call_claude(prompt: str, *, model: str = "claude-sonnet-4-5", max_tokens: int = 32000) -> dict:
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

    print(f"[claude] calling {model} with {max_tokens=}, web_search enabled (max_uses=12) [streaming]")
    t0 = time.time()
    # Use streaming because SDK requires it for any call where max_tokens
    # could plausibly take >10 min (which our 32K limit can hit when Claude
    # generates KO+EN narratives + web_search 12 uses).
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        tools=tools,
        messages=messages,
    ) as stream:
        # Drain the stream — we don't need per-token progress, just the final assembled message.
        for _event in stream:
            pass
        resp = stream.get_final_message()
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
                # Defensive cleanup #2: json-repair — robust library that fixes
                # mismatched brackets, missing commas, unescaped quotes inside
                # strings, etc. Catches the cases ast.literal_eval can't.
                try:
                    from json_repair import repair_json
                    repaired = repair_json(cleaned, return_objects=False)
                    return json.loads(repaired)
                except Exception:
                    pass
                # Defensive cleanup #3: ast.literal_eval as final fallback
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
        idx_name = idx.get('name') or idx.get('ticker') or ''
        idx_value = idx.get('value') or idx.get('price') or '—'
        cards.append(f"""
  <div class="idx-card">
    <div class="idx-name">{html_escape(idx_name)}</div>
    <div class="idx-val">{html_escape(str(idx_value))}</div>
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
        if not isinstance(m, dict):
            continue
        cls = pct_class(m.get("change_pct", 0))
        chg = fmt_pct(m.get("change_pct", 0)) if isinstance(m.get("change_pct"), (int, float)) else str(m.get("change_pct", ""))
        ticker = m.get('ticker') or m.get('name') or ''
        tiles.append(f"""
  <div class="mag-tile {cls}">
    <div class="mag-tick">{html_escape(ticker)}</div>
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
        if not isinstance(it, dict):
            continue
        cls = "up" if kind == "winners" else "down"
        arrow = "⬆" if kind == "winners" else "⬇"
        head_cls = "w" if kind == "winners" else "l"
        name = it.get(f"name_{lang}") or it.get("name_en") or it.get("name_ko") or ""
        trig = it.get(f"trigger_{lang}") or it.get("trigger_en") or it.get("trigger_ko") or ""
        chg = it.get("change_pct", 0)
        ticker = it.get('ticker') or it.get('name') or ''
        rows.append(f"""
  <div class="mov-row">
    <div class="mov-tick">{html_escape(ticker)}<span class="nm">{html_escape(name)}</span></div>
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


def render_key_metrics_strip(km: dict, lang: str) -> str:
    """Render the 7-asset fixed top component (USD/KRW, Gold, Silver, WTI, BTC, ETH, XRP).
    This is required on EVERY post per the system prompt master spec."""
    if not km or not isinstance(km, dict):
        return ""
    meta_ko = [("usdkrw","USD/KRW"),("gold","금"),("silver","은"),("wti","WTI"),
               ("btc","BTC"),("eth","ETH"),("xrp","XRP")]
    meta_en = [("usdkrw","USD/KRW"),("gold","Gold"),("silver","Silver"),("wti","WTI"),
               ("btc","BTC"),("eth","ETH"),("xrp","XRP")]
    meta = meta_ko if lang == "ko" else meta_en
    cells = []
    for key, label in meta:
        entry = km.get(key)
        if not isinstance(entry, dict):
            continue
        value = entry.get("value", "—")
        chg = entry.get("change_pct", 0)
        try:
            chg_f = float(chg)
        except Exception:
            chg_f = 0.0
        color = "#dc2626" if chg_f > 0 else ("#2563eb" if chg_f < 0 else "#6b7280")
        arrow = "🔺" if chg_f > 0 else ("🔻" if chg_f < 0 else "·")
        cells.append(f"""
    <div style="flex:1 1 90px;min-width:90px;padding:10px 8px;background:#0f1419;border-radius:6px;text-align:center;">
      <div style="font-size:10px;color:#8b9098;letter-spacing:0.5px;font-weight:600;">{html_escape(label)}</div>
      <div style="font-size:14px;color:#e6e7e9;font-weight:700;margin-top:3px;font-variant-numeric:tabular-nums;">{html_escape(str(value))}</div>
      <div style="font-size:11px;color:{color};font-weight:600;margin-top:2px;font-variant-numeric:tabular-nums;">{arrow} {chg_f:+.2f}%</div>
    </div>""")
    if not cells:
        return ""
    title = "▸ 핵심 시장 지표 · 24h" if lang == "ko" else "▸ Key Market Indicators · 24h"
    return f"""<div class="section-title">{title}</div>
<div style="display:flex;flex-wrap:wrap;gap:6px;padding:8px 16px 14px;">{''.join(cells)}</div>
"""


def render_narrative(html: str, lang: str) -> str:
    """Wrap the deep narrative HTML body. Claude returns rich HTML inside this
    field — h3/h4/p/table/strong/inline color spans — and we pass it through."""
    if not html or not isinstance(html, str) or len(html.strip()) < 50:
        return ""
    title = "▸ 심층 분석" if lang == "ko" else "▸ Deep Analysis"
    # The narrative body has its own h3 sections, so we just need a container
    # with line-height & padding inherited from the daily-base.html article style.
    return f"""<div class="section-title">{title}</div>
<div style="padding:0 16px 18px;line-height:1.65;font-size:14px;">{html}</div>
"""


def render_forward_calendar(html: str, lang: str) -> str:
    """Wrap the forward 10-trading-day calendar HTML table."""
    if not html or not isinstance(html, str) or len(html.strip()) < 20:
        return ""
    title = "▸ 향후 10거래일 캘린더" if lang == "ko" else "▸ Next 10 Trading Days"
    return f"""<div class="section-title">{title}</div>
<div style="padding:0 16px 18px;overflow-x:auto;font-size:13px;">{html}</div>
"""


def render_fact_check(text: str, lang: str) -> str:
    """Closing fact-check declaration."""
    if not text or not isinstance(text, str) or len(text.strip()) < 10:
        return ""
    return f"""<div style="margin:18px 16px 8px;padding:12px 14px;background:#0a1a14;border-left:3px solid #14b87a;border-radius:4px;font-size:12px;color:#a8d8c0;line-height:1.5;">
  <strong style="color:#14b87a;">✓ </strong>{html_escape(text)}
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
    # Strip any inline HTML tags from summary — it's used in plain-text
    # contexts (meta description, og:description, twitter:description,
    # header sub-text) where html_escape() would render them as visible
    # &lt;strong&gt; etc. Claude sometimes includes <strong>/<span> in
    # summary despite the prompt rule; strip defensively.
    raw_summary = data.get(f"summary_{lang}", "")
    summary = re.sub(r"<[^>]+>", "", raw_summary).strip()
    # Also collapse multiple spaces from tag removal
    summary = re.sub(r"\s+", " ", summary)
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
        if not isinstance(idx, dict):
            continue
        cls = "badge-green" if (idx.get("change_pct", 0) > 0) else ("badge-orange" if idx.get("change_pct", 0) < 0 else "badge-blue")
        label = idx.get("name") or idx.get("ticker") or ""
        badges.append(f'<span class="badge {cls}">{html_escape(label)} {fmt_pct(idx.get("change_pct", 0))}</span>')
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
        # IMPORTANT: do not use 'title' as the loop variable here — the
        # outer scope already has `title = data.get("headline_{lang}")`
        # at line 488, and Python's for loop does not create its own scope.
        # Variable shadowing here would overwrite the headline title and
        # corrupt the h1 rendering downstream.
        if isinstance(s, str):
            src_url, src_title = s, s
        elif isinstance(s, dict):
            src_url = s.get("url", "") or ""
            src_title = s.get("title", "") or src_url
        else:
            continue
        if not src_url:
            continue
        src_lines.append(f'<a href="{html_escape(src_url)}" target="_blank" rel="noopener">{html_escape(src_title)}</a>')
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

    # Body sections — combine v2 fields (key_metrics strip, deep narrative,
    # forward calendar, fact-check) with legacy card sections for backwards compat.
    key_strip = render_key_metrics_strip(data.get("key_metrics", {}), lang)
    narrative = render_narrative(data.get(f"narrative_html_{lang}", ""), lang)
    cards = render_sections(slot, data, lang)
    forward_cal = render_forward_calendar(data.get(f"forward_calendar_html_{lang}", ""), lang)
    fact_check_box = render_fact_check(data.get(f"fact_check_{lang}", ""), lang)
    # Order: 7-asset strip (fixed top) → deep narrative (main) → visual cards
    # (supplementary) → forward calendar → fact-check (closing).
    sections_html = "\n".join(p for p in [key_strip, narrative, cards, forward_cal, fact_check_box] if p)

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
    p.add_argument("--force", action="store_true",
                   help="Re-publish even if the slug directory already exists. "
                        "Without this flag, an existing slug is treated as already-published "
                        "and the run exits cleanly (prevents duplicate posts when both the "
                        "main cron and the monitor cron fire on the same day).")
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

    # Duplicate-publish guard: if a directory for this slug already exists with
    # an index.html, treat as already-published and skip cleanly. Use --force
    # to override (e.g., manual re-run to fix a broken post). Prevents the
    # exact scenario seen on 2026-05-19: monitor cron rescues a missing slot,
    # the original schedule cron fires late, both push to the same slug, the
    # second push wins and may contain a worse Claude response.
    if not args.force:
        existing = BLOG_DIR / slug / "index.html"
        if existing.exists() and existing.stat().st_size > 1000:
            print(f"[skip] {slug} already published (use --force to overwrite). Exiting.")
            return

    # Load + fill prompt
    prompt_template = (PROMPTS / cfg["prompt"]).read_text(encoding="utf-8")
    prompt = prompt_template.replace("{trading_date}", trading_date).replace("{publish_date}", publish_date)

    # CRITICAL: prepend operating context. Otherwise Claude (training cutoff ~2024)
    # sees the 2026 trading_date and self-judges the web_search results as
    # "simulated/fictional future data", returning skip=true. We must explicitly
    # tell Claude this is a live production pipeline firing in real time and
    # that web_search results are ground truth.
    operating_context = (
        f"# ⚠️ OPERATING CONTEXT — read before everything below\n\n"
        f"This is a **live production cron** firing in real time on luckyplz.com. "
        f"Today's date is **{publish_date} KST**. The trading_date **{trading_date}** "
        f"is real and current — NOT a hypothetical future scenario.\n\n"
        f"**If your training cutoff makes today's date feel \"future\" or \"fictional\", "
        f"IGNORE that intuition.** The pipeline IS firing right now on this date. "
        f"web_search results dated near {trading_date} are **authoritative ground truth** "
        f"— never label them as simulated, hypothetical, or fictional.\n\n"
        f"The \"Strict Factuality\" principle below means: cross-verify numbers across "
        f"multiple web_search sources and drop ones that disagree. It does NOT mean "
        f"refuse the assignment because the date seems unfamiliar to your training data.\n\n"
        f"**Never return `{{\"skip\": true}}` based on \"future date\", \"fictional data\", "
        f"or \"cannot verify because of cutoff\" reasoning.** The ONLY valid skip reason is "
        f"a documented market holiday (e.g., New Year's Day, Lunar New Year, Chuseok, "
        f"Christmas, Independence Day, etc.) — and only if your web_search confirms the "
        f"market was closed that day.\n\n"
        f"---\n\n"
    )
    prompt = operating_context + prompt

    # V3 visual-design guide. The narrative_html fields render inside our
    # daily-base.html template, which defines specific CSS classes that mimic
    # the visual hierarchy of hand-written best-quality posts (tldr-box,
    # cal-card, scen-grid, dn/upx/hl color spans). Without this guide, Claude
    # falls back to raw <h3>/<ul>/<table> which renders as a wall of text.
    visual_guide = (
        "\n\n---\n"
        "# 🎨 VISUAL DESIGN GUIDE — MANDATORY CSS CLASSES (daily-base.html template)\n\n"
        "When writing `narrative_html_ko` and `narrative_html_en`, you MUST use these "
        "pre-defined CSS classes for visual hierarchy. Do NOT fall back to plain "
        "`<table>`/`<h3>`/`<ul>` — that renders as undistinguished text. Use the "
        "structured components below for each section:\n\n"
        "## 1. ⚡ 30-Second Brief / 30초 요약 → use `.tldr-box`\n"
        "```html\n"
        "<div class=\"tldr-box\">\n"
        "  <h3>⚡ 30초 요약 — 핵심만</h3>\n"
        "  <ul>\n"
        "    <li><strong>S&P 500</strong> <span class=\"dn\">-1.24%</span> — 신고가 다음날 폭락, 반도체 매물</li>\n"
        "    <li><strong>Warsh Fed</strong> <span class=\"hl\">매파 인준</span> — 10Y <span class=\"dn\">4.59%</span> 1년 최고</li>\n"
        "    <li><strong>NVDA</strong> <span class=\"dn\">-2.8%</span> — 칩 협상 무산, AI capex 가이드 우려</li>\n"
        "  </ul>\n"
        "</div>\n"
        "```\n"
        "Color spans inside `.tldr-box li`: `.dn` (down, BLUE), `.upx` (up, RED), `.hl` (highlight, GOLD).\n\n"
        "## 2. 향후 캘린더 / Forward Calendar → use `.cal-card` + `.cal-row`\n"
        "```html\n"
        "<div class=\"cal-card\">\n"
        "  <div class=\"cal-row\">\n"
        "    <div class=\"cal-date\">5/19<span class=\"dow\">TUE</span></div>\n"
        "    <div class=\"cal-body\"><strong>美 4월 주택착공</strong> · <strong>한국 4월 수출입</strong> · NVDA AH 어닝</div>\n"
        "  </div>\n"
        "  <div class=\"cal-row opex\">\n"
        "    <div class=\"cal-date\">5/21<span class=\"dow\">THU</span></div>\n"
        "    <div class=\"cal-body\"><strong>월간 OPEX</strong> · Fed Williams 발언 · 한국 금통위</div>\n"
        "  </div>\n"
        "</div>\n"
        "```\n"
        "Use `.cal-row.opex` for options expiry rows (gold highlight), `.cal-row.holiday` for market holidays (pink).\n"
        "Replace ALL `<table>` 10-day calendars in the v2 prompt with this structure — DO NOT emit `<table>` for the forward calendar.\n\n"
        "## 3. 시나리오 트리 / Scenario Tree → use `.scen-grid` + `.scen-card`\n"
        "```html\n"
        "<div class=\"scen-grid\">\n"
        "  <div class=\"scen-card bull\">\n"
        "    <h4>🟢 강세 시나리오 (확률 30%)</h4>\n"
        "    <p>오버솔드 반등 + Warsh 인준 가격 선반영. 반도체 그룹 갭상승 + Mag 7 동조.</p>\n"
        "    <span class=\"cond\">조건: WTI $100 안착, 10Y 4.55% 이하 안정, 이란 헤드라인 침묵</span>\n"
        "  </div>\n"
        "  <div class=\"scen-card base\">\n"
        "    <h4>🟡 베이스 시나리오 (확률 50%)</h4>\n"
        "    <p>Choppy 반등 — 부분 메우기 후 +0.2~+0.5% 보합 마감. 반도체 약세 지속.</p>\n"
        "    <span class=\"cond\">조건: 10Y 4.55-4.65% 박스, VIX 18-22 유지</span>\n"
        "  </div>\n"
        "  <div class=\"scen-card bear\">\n"
        "    <h4>🔴 약세 시나리오 (확률 20%)</h4>\n"
        "    <p>이란 헤드라인 재점화 → WTI $105 돌파 → 인플레 우려 → 10Y 4.70%↑</p>\n"
        "    <span class=\"cond\">조건: 호르무즈 헤드라인 + DXY 105 돌파</span>\n"
        "  </div>\n"
        "</div>\n"
        "```\n\n"
        "## 4. 📊 지수/섹터 스냅샷 → 인라인 `<span>` color spans\n"
        "Inside paragraphs and lists, use:\n"
        "- `<span class=\"upx\">+1.24%</span>` for positive moves (RED — KR convention)\n"
        "- `<span class=\"dn\">-1.54%</span>` for negative moves (BLUE)\n"
        "- `<span class=\"hl\">중립</span>` for highlight/attention\n"
        "Do NOT use inline `style=\"color:#dc2626\"` — use the classes above for consistency.\n\n"
        "## 5. ⚠️ 면책 / 가정 안내 → use `.section-note`\n"
        "```html\n"
        "<div class=\"section-note\">아래는 5/15 마감 + 주말 매크로에 근거한 <strong>시나리오 추정</strong>이며 확정된 사실이 아닙니다.</div>\n"
        "```\n\n"
        "## Structural rules — RAW <table> IS FORBIDDEN\n"
        "- **Do NOT emit `<table>` tags in narrative_html_ko/en under any circumstances.** Raw tables look unpolished and break the visual rhythm. Convert every tabular concept to one of the dedicated components.\n"
        "- For ANY list of indices/sectors/movers/data points, use one of:\n"
        "  - `.cal-card` + `.cal-row` (1-column label + value pairs)\n"
        "  - `.km-grid` + `.km-cell` (numeric strip, see render_key_metrics_strip example)\n"
        "  - Stacked `<div>` rows with inline grid styles\n"
        "- Section dividers: keep using `<h3>` for major sections (already styled by template).\n"
        "- Sub-headings within sections: `<h4>` (not h5/h6).\n"
        "- For multi-column comparisons (e.g., 외인 vs 기관 수급), use 2 stacked `.cal-card`s.\n"
        "- For 11 GICS sectors heatmap: use the existing `themes` JSON field which already renders as a heatmap grid via render_themes(). Do NOT redo it inside narrative_html.\n"
        "- For 30-second brief: use `.tldr-box`, never `<table>` or plain `<ul>`.\n"
        "- For forward calendar: use `.cal-card`, never `<table>`.\n"
        "- For scenario tree: use `.scen-grid` + `.scen-card`, never `<table>`.\n"
    )
    prompt = prompt + visual_guide

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
