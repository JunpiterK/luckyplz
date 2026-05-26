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
# ---------------------------------------------------------------------------
# Language configuration
# ---------------------------------------------------------------------------
# Tier A languages (mandatory). The pipeline always produces ko + en;
# ja and zh are added when the prompt JSON includes the corresponding
# fields. This list is the iteration order used by main() — anywhere the
# code needs "every language we might publish", import this constant.
LANGS = ["ko", "en", "ja", "zh"]

# Per-language metadata used in HTML rendering. Each tuple is (og_locale,
# canonical_suffix). suffix "" means base slug (ko owns the bare slug);
# everything else gets `-<lang>` appended.
LANG_META = {
    "ko": {"og_locale": "ko_KR", "slug_suffix": ""},
    "en": {"og_locale": "en_US", "slug_suffix": "-en"},
    "ja": {"og_locale": "ja_JP", "slug_suffix": "-ja"},
    "zh": {"og_locale": "zh_CN", "slug_suffix": "-zh"},
}


def L(lang: str, ko: str, en: str, ja: str | None = None, zh: str | None = None) -> str:
    """4-way locale picker for UI labels.

    Returns the label for `lang`. ja/zh fall back to en if not provided;
    this keeps the call sites short for the (common) case where ko and en
    are the only really different strings. Existing two-arg patterns like
    "X" if lang == "en" else "Y" become L(lang, "Y", "X").
    """
    if lang == "ko":
        return ko
    if lang == "ja":
        return ja if ja is not None else en
    if lang == "zh":
        return zh if zh is not None else en
    return en  # 'en' or any unknown


def pick_localized(data: dict, key: str, lang: str, fallback: str = "en") -> str:
    """Read `data[f"{key}_{lang}"]` with graceful fallback to en.

    Returns "" if neither lang nor fallback has the field. Used everywhere
    we read Claude-produced multilingual fields (headline_ko/_en/_ja/_zh,
    summary_*, narrative_html_*, etc.). When the prompt has not yet been
    extended to emit _ja/_zh fields, ja/zh callers automatically receive
    the en version — keeps the pipeline running while content catches up.
    """
    val = data.get(f"{key}_{lang}")
    if val:
        return val
    return data.get(f"{key}_{fallback}", "") or ""


def has_lang_content(data: dict, lang: str) -> bool:
    """Decide whether to publish a directory for `lang`.

    ko and en are always published (legacy contract — existing prompts
    always emit them). ja/zh are published only when the prompt actually
    produced a non-empty `headline_<lang>`. This means scripts/prompts/*.md
    files can be extended one at a time; languages with no content yet
    simply don't get a directory, an entry, or a sitemap URL.
    """
    if lang in ("ko", "en"):
        return True
    head = (data.get(f"headline_{lang}") or "").strip()
    return bool(head)


SLOTS = {
    "us-close": {
        "prompt": "us-close-recap.md",
        "slug_prefix": "us-tech-recap",
        # "trading_date" = US ET close date the post covers
        "trading_date_offset_days": -1,    # publish day 06:00 KST covers prev US session
        "category": "industry",
        "read_min": 8,
        "cover_emoji": "🇺🇸",
        "header_label_ko": "미국 테크 마감 리캡",
        "header_label_en": "US TECH DAILY RECAP",
        "header_label_ja": "米国テック市場マーケット引け",
        "header_label_zh": "美股科技市场收盘速览",
    },
    "kr-open": {
        "prompt": "kr-open-brief.md",
        "slug_prefix": "kr-open-brief",
        "trading_date_offset_days": 0,
        "category": "industry",
        "read_min": 6,
        "cover_emoji": "🇰🇷",
        "header_label_ko": "한국장 개장 브리핑",
        "header_label_en": "KOREA OPEN BRIEF",
        "header_label_ja": "韓国市場・寄り前ブリーフ",
        "header_label_zh": "韩国股市开盘前简报",
    },
    "kr-close": {
        "prompt": "kr-close-recap.md",
        "slug_prefix": "kr-tech-recap",
        "trading_date_offset_days": 0,
        "category": "industry",
        "read_min": 7,
        "cover_emoji": "🇰🇷",
        "header_label_ko": "한국 테크 마감 리캡",
        "header_label_en": "KOREA TECH DAILY RECAP",
        "header_label_ja": "韓国テック市場マーケット引け",
        "header_label_zh": "韩国科技市场收盘速览",
    },
    "us-premarket": {
        "prompt": "us-premarket.md",
        "slug_prefix": "us-premarket",
        "trading_date_offset_days": 0,    # US session that opens tonight (KST 22:30)
        "category": "industry",
        "read_min": 6,
        "cover_emoji": "🇺🇸",
        "header_label_ko": "미국 프리마켓 브리핑",
        "header_label_en": "US PRE-MARKET BRIEF",
        "header_label_ja": "米国プレマーケット・ブリーフ",
        "header_label_zh": "美股盘前简报",
    },
    "cn-open": {
        "prompt": "cn-open-brief.md",
        "slug_prefix": "cn-open-brief",
        # KST 10:30 = CST 09:30 = exact CN opening. Same-day trading_date.
        "trading_date_offset_days": 0,
        "category": "industry",
        "read_min": 6,
        "cover_emoji": "🇨🇳",
        "header_label_ko": "중국장 개장 브리핑",
        "header_label_en": "CHINA OPEN BRIEF",
        "header_label_ja": "中国市場・寄り前ブリーフ",
        "header_label_zh": "中国股市开盘前简报",
    },
    "cn-close": {
        "prompt": "cn-close-recap.md",
        "slug_prefix": "cn-tech-recap",
        # KST 16:30 = CST 15:30 = 30 min after CN close (data settled).
        "trading_date_offset_days": 0,
        "category": "industry",
        "read_min": 7,
        "cover_emoji": "🇨🇳",
        "header_label_ko": "중국 테크 마감 리캡",
        "header_label_en": "CHINA TECH DAILY RECAP",
        "header_label_ja": "中国テック市場マーケット引け",
        "header_label_zh": "中国科技市场收盘速览",
    },
}


# ---------------------------------------------------------------------------
# Trading-day / holiday guard (short-circuits the pipeline before any
# Claude or yfinance call when the relevant exchange is closed)
# ---------------------------------------------------------------------------
# Without this guard, holidays generated content from training-data
# hallucination because Claude's prompt-based holiday detection was not
# reliable. Now the pipeline short-circuits BEFORE any API call: if the
# exchange is closed, we log a clean skip and exit 0.
#
# Two-tier check:
#   1. Weekend (Sat/Sun) — handled inline by Python's datetime, no library
#      dependency. Covers ~28% of days.
#   2. Exchange holiday — handled by `exchange_calendars` library which
#      ships authoritative NYSE, XKRX (Korea Exchange), XSHG (Shanghai SE)
#      calendars. Covers the remaining ~3% of non-trading weekdays. China
#      has additional non-trading windows (Lunar New Year ~1 week, National
#      Day ~1 week, Qingming, Dragon Boat, Mid-Autumn) so this guard
#      becomes especially important once cn-* slots are active.
# Total: ~31% of calendar days short-circuit at near-zero cost.

# slot → exchange map. Each slot's trading_date is judged against the
# exchange that produces its data.
SLOT_TO_MARKET = {
    "us-close":     "XNYS",   # NYSE; us-close uses yesterday US ET
    "us-premarket": "XNYS",   # NYSE; us-premarket uses today US ET
    "kr-open":      "XKRX",   # KRX; kr-open uses today KR (opening today)
    "kr-close":     "XKRX",   # KRX; kr-close uses today KR (closing today)
    "cn-open":      "XSHG",   # Shanghai SE; cn-open uses today CN (opening today)
    "cn-close":     "XSHG",   # Shanghai SE; cn-close uses today CN (closing today)
}


def is_trading_day(date_str: str, market: str) -> tuple[bool, str]:
    """Check if `date_str` is a trading day on the given market.

    Returns (is_open, reason). On any library failure, falls back to True
    (graceful — better to publish a post we can later delete than to skip
    a real trading day because of a library issue).

    market: 'XNYS' (NYSE), 'XKRX' (Korea Exchange), or 'XSHG' (Shanghai
            Stock Exchange) — ISO MIC codes. exchange_calendars ships
            all three out of the box.
    """
    from datetime import datetime
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return True, f"invalid date format: {date_str}"

    # Tier 1 — weekend (cheap, no library)
    if target.weekday() >= 5:   # 5=Sat, 6=Sun
        day_name = ("Mon","Tue","Wed","Thu","Fri","Sat","Sun")[target.weekday()]
        return False, f"weekend ({day_name})"

    # Tier 2 — exchange holiday calendar
    try:
        import exchange_calendars as ec
        cal = ec.get_calendar(market)
        if cal.is_session(date_str):
            return True, f"{market} regular trading session"
        # Weekday but not a session = holiday
        return False, f"{market} holiday (closed weekday)"
    except ImportError:
        print(f"[holiday] exchange_calendars not installed — assuming {market} open on {date_str}")
        return True, "library unavailable, defaulting open"
    except Exception as e:
        print(f"[holiday] {market} calendar lookup failed: {type(e).__name__}: {e} — assuming open")
        return True, f"calendar lookup error: {e}"


# ---------------------------------------------------------------------------
# Hard market data fetch (replaces Claude hallucination with verified API data)
# ---------------------------------------------------------------------------
# Claude's training data caps around late 2024. When asked for "today's" S&P
# close it sometimes returns 2024 numbers verbatim — and the fact-check field
# may still claim '3-source verification' because the prompt biased it to.
# Solution: fetch the numbers ourselves via yfinance (Yahoo Finance) and
# inject them into the prompt as MANDATORY ground truth. Claude then writes
# narrative around the fixed numbers — cannot fabricate.

# Ticker maps per slot. Names are KO/EN-friendly labels.
_COMMON_TOP7 = {
    "USD/KRW": "KRW=X", "Gold": "GC=F", "Silver": "SI=F", "WTI": "CL=F",
    "BTC": "BTC-USD", "ETH": "ETH-USD", "XRP": "XRP-USD",
}
_US_INDICES = {
    "S&P 500": "^GSPC", "Nasdaq Composite": "^IXIC", "Dow Jones": "^DJI",
    "Russell 2000": "^RUT", "Philadelphia Semi (SOX)": "^SOX",
    "VIX": "^VIX", "DXY (Dollar Index)": "DX-Y.NYB",
    "10Y Treasury Yield": "^TNX", "2Y Treasury Yield": "^IRX",
    "30Y Treasury Yield": "^TYX",
}
_MAG7 = {
    "AAPL": "AAPL", "MSFT": "MSFT", "GOOGL": "GOOGL", "AMZN": "AMZN",
    "META": "META", "NVDA": "NVDA", "TSLA": "TSLA", "AVGO": "AVGO",
}
_US_SECTOR_ETFS = {
    "XLK (Technology)": "XLK", "XLF (Financials)": "XLF",
    "XLV (Health Care)": "XLV", "XLY (Cons Disc)": "XLY",
    "XLP (Cons Staples)": "XLP", "XLE (Energy)": "XLE",
    "XLI (Industrials)": "XLI", "XLB (Materials)": "XLB",
    "XLU (Utilities)": "XLU", "XLRE (Real Estate)": "XLRE",
    "XLC (Comm Services)": "XLC",
}
_KR_INDICES = {
    "KOSPI": "^KS11", "KOSDAQ": "^KQ11", "KOSPI 200": "^KS200",
}
_KR_STOCKS = {
    "삼성전자 (005930)": "005930.KS",
    "SK하이닉스 (000660)": "000660.KS",
    "NAVER (035420)": "035420.KS",
    "Kakao (035720)": "035720.KS",
    "LG에너지솔루션 (373220)": "373220.KS",
    "삼성SDI (006400)": "006400.KS",
    "현대차 (005380)": "005380.KS",
    "POSCO Future M (003670)": "003670.KS",
    "에코프로비엠 (247540)": "247540.KQ",
    "셀트리온 (068270)": "068270.KS",
    "한화에어로스페이스 (012450)": "012450.KS",
    "HD현대중공업 (329180)": "329180.KS",
}
# China indices. Yahoo Finance tickers:
#   ^GSPC  family symbols → SSE Composite (000001.SS), Shenzhen Component
#   (399001.SZ), CSI 300 (000300.SS), ChiNext (399006.SZ),
#   STAR 50 (^STAR50 not always reliable; use 000688.SS as fallback if needed),
#   Hang Seng (^HSI), Hang Seng China Enterprises (^HSCE), Hang Seng Tech (^HSTECH).
# Decision: include both Mainland (SSE/SZSE/CSI300/ChiNext) and Hong Kong
# (HSI/HSCE/HSTECH) because Chinese tech investing is dominated by ADRs and
# H-shares on the HK exchange even when "Chinese market" is mentioned.
_CN_INDICES = {
    "SSE Composite (上证综指)":        "000001.SS",
    "Shenzhen Component (深证成指)":   "399001.SZ",
    "CSI 300 (沪深300)":               "000300.SS",
    "ChiNext (创业板指)":              "399006.SZ",
    "Hang Seng (恒生指数)":            "^HSI",
    "Hang Seng China Enterprises (国企指数)": "^HSCE",
    "Hang Seng Tech (恒生科技)":       "^HSTECH",
}
# China tech & consumer leaders. ADRs (BABA/JD/PDD/BIDU/NIO/XPEV/LI) trade
# on NYSE/Nasdaq during US hours and reflect overnight sentiment. The
# .HK pairs are the primary listing for Tencent/Meituan/BYD/SMIC and price
# Chinese on-shore demand directly.
_CN_STOCKS = {
    # US-listed Chinese ADRs (overnight sentiment)
    "Alibaba ADR (BABA)":      "BABA",
    "JD.com ADR (JD)":         "JD",
    "PDD (Pinduoduo) ADR":     "PDD",
    "Baidu ADR (BIDU)":        "BIDU",
    "NIO ADR":                 "NIO",
    "XPeng ADR":               "XPEV",
    "Li Auto ADR":             "LI",
    # HK-listed primaries
    "Tencent (00700.HK)":      "0700.HK",
    "Meituan (03690.HK)":      "3690.HK",
    "BYD (01211.HK)":          "1211.HK",
    "SMIC (00981.HK)":         "0981.HK",
    "Xiaomi (01810.HK)":       "1810.HK",
    "AIA Group (01299.HK)":    "1299.HK",
}


def fetch_market_data(slot: str, trading_date: str) -> dict:
    """Fetch verified market data via yfinance. Returns dict keyed by label,
    each value: {close, prev_close, change_pct, ticker}. Empty dict if all fail.
    """
    try:
        import yfinance as yf
    except ImportError:
        print("[fetch] yfinance not installed — skipping hard fetch")
        return {}

    # Resolve slot-specific ticker set
    tickers = dict(_COMMON_TOP7)
    if slot == "us-close":
        tickers.update(_US_INDICES)
        tickers.update(_MAG7)
        tickers.update(_US_SECTOR_ETFS)
    elif slot == "us-premarket":
        tickers.update(_US_INDICES)
        tickers.update(_MAG7)
        # Sector ETFs less critical pre-open
    elif slot == "kr-open":
        # Overnight US for spillover + KR baseline (prev close)
        tickers.update({k: v for k, v in _US_INDICES.items() if k in (
            "S&P 500", "Nasdaq Composite", "Philadelphia Semi (SOX)",
            "10Y Treasury Yield", "DXY (Dollar Index)", "VIX")})
        tickers.update(_MAG7)
        tickers.update(_KR_INDICES)
        tickers.update(_KR_STOCKS)
    elif slot == "kr-close":
        tickers.update(_KR_INDICES)
        tickers.update(_KR_STOCKS)
    elif slot == "cn-open":
        # Overnight US for spillover (Chinese tech tracks Nasdaq) + ADRs +
        # CN indices for prior-close anchor. Run before CN market opens
        # at 09:30 CST (10:30 KST), so yesterday's CN close is the
        # latest data available.
        tickers.update({k: v for k, v in _US_INDICES.items() if k in (
            "S&P 500", "Nasdaq Composite", "Philadelphia Semi (SOX)",
            "10Y Treasury Yield", "DXY (Dollar Index)", "VIX")})
        tickers.update(_CN_INDICES)
        tickers.update(_CN_STOCKS)
    elif slot == "cn-close":
        # After 15:00 CST (16:00 KST + 30min margin) data window settled.
        tickers.update(_CN_INDICES)
        tickers.update(_CN_STOCKS)

    # Date window: fetch ~7 trading days back to safely compute change vs prior close
    target = datetime.strptime(trading_date, "%Y-%m-%d")
    start = (target - timedelta(days=10)).strftime("%Y-%m-%d")
    end = (target + timedelta(days=2)).strftime("%Y-%m-%d")

    result = {}
    print(f"[fetch] yfinance: {len(tickers)} tickers for {slot} on {trading_date}")
    t0 = time.time()
    for name, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(start=start, end=end, auto_adjust=False)
            if hist.empty or len(hist) < 2:
                continue
            # Match the bar dated <= trading_date. If trading_date itself is
            # in hist, use it; otherwise the most recent bar before.
            hist_dates = hist.index.strftime("%Y-%m-%d")
            target_idx = None
            for i in range(len(hist) - 1, -1, -1):
                if hist_dates[i] <= trading_date:
                    target_idx = i
                    break
            if target_idx is None or target_idx == 0:
                continue
            close = float(hist["Close"].iloc[target_idx])
            prev = float(hist["Close"].iloc[target_idx - 1])
            change_pct = (close - prev) / prev * 100 if prev else 0.0
            actual_date = hist_dates[target_idx]
            result[name] = {
                "close": round(close, 2),
                "prev_close": round(prev, 2),
                "change_pct": round(change_pct, 2),
                "ticker": ticker,
                "as_of": actual_date,
            }
        except Exception as e:
            print(f"[fetch] {name} ({ticker}) failed: {type(e).__name__}: {e}")
            continue
    dt = time.time() - t0
    print(f"[fetch] complete: {len(result)}/{len(tickers)} tickers in {dt:.1f}s")
    return result


def format_market_data_for_prompt(data: dict, trading_date: str) -> str:
    """Format hard-fetched market data as a MANDATORY prompt section.
    Claude is required to use these exact numbers; deviation = bug."""
    if not data:
        return ""
    lines = [
        "# 🔒 VERIFIED MARKET DATA (hard-fetched from Yahoo Finance API)",
        "",
        f"**The numbers below are direct API fetches for trading_date {trading_date}.**",
        "**You MUST use these EXACT values in your output JSON** (indices, mag7,",
        "key_metrics, kr_indices, futures, gap_watch, foreign_flow, themes, etc.).",
        "",
        "Rules:",
        "- Do NOT round differently. Use the exact close and change_pct as given.",
        "- Do NOT substitute with values from your training data — those are wrong (stale).",
        "- Do NOT 'estimate' — every number below is verified at the source.",
        "- For numbers not listed here (e.g., individual KR small-caps, 외인/기관 net flow,",
        "  ETF flows, after-hours moves), THEN use web_search with the fact-check protocol",
        "  and cross-verify against KRX official / WSJ / Bloomberg / Reuters as before.",
        "- In the `fact_check_ko` / `fact_check_en` field, explicitly say:",
        "  '주요 지수·종목·환율·원자재·암호화폐 가격은 Yahoo Finance API 직접 fetch 기반'",
        "",
        "## Verified values (close, change %)",
        "",
    ]
    # Group by category for readability. CN groups added Sub-step 2b so
    # cn-open / cn-close slots also see their verified data in the prompt.
    groups = [
        ("Top 7 fixed assets", list(_COMMON_TOP7.keys())),
        ("US indices & macro", list(_US_INDICES.keys())),
        ("Mag 7 stocks", list(_MAG7.keys())),
        ("US sector ETFs (11 GICS)", list(_US_SECTOR_ETFS.keys())),
        ("KR indices", list(_KR_INDICES.keys())),
        ("KR stocks", list(_KR_STOCKS.keys())),
        ("CN indices (Mainland + HK)", list(_CN_INDICES.keys())),
        ("CN tech / consumer leaders (ADR + HK)", list(_CN_STOCKS.keys())),
    ]
    for group_name, keys in groups:
        group_data = [(k, data[k]) for k in keys if k in data]
        if not group_data:
            continue
        lines.append(f"### {group_name}")
        for name, v in group_data:
            close = v["close"]
            chg = v["change_pct"]
            as_of = v.get("as_of", trading_date)
            stale = " ⚠️ (note: as_of differs from trading_date)" if as_of != trading_date else ""
            lines.append(f"- **{name}**: close `{close}` · change `{chg:+.2f}%` · ticker `{v['ticker']}` · as_of `{as_of}`{stale}")
        lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Post-output validation — accuracy double-check (option A: warn-only)
# ---------------------------------------------------------------------------
# Heuristic check that fires AFTER Claude returns its JSON. For each ticker
# in market_data with a known change_pct, search narrative_html_en for any
# nearby signed percentage. If the verified value doesn't appear anywhere
# in the narrative — and the narrative DOES mention the ticker — flag it.
#
# Per user decision (option A): we log GitHub Actions ::warning:: but do
# NOT block the publish. Goal is to surface mismatches in CI without
# interrupting cron throughput. If real mismatches start showing up in the
# logs, we can promote this to option B (retry) or C (block) later.
#
# Why not stricter regex? Narratives mix tickers and percentages
# liberally ("NVDA jumped sharply with semis up 2%"), and Claude
# sometimes describes the same move three different ways across the
# 4 languages. False positives would be more painful than false negatives.
# A loose presence-check is enough to catch the "S&P 500 +0.37% but
# narrative says +3.7%" type of catastrophic mismatch the user remembers.

def validate_narrative_numbers(data: dict, market_data: dict, slot: str) -> list[str]:
    """Detect potential narrative ↔ market_data mismatches.

    Returns a list of warning messages (empty = clean). Read-only — caller
    decides what to do with the warnings (currently: log as
    ::warning:: and continue).

    Algorithm:
      For each ticker name in market_data whose name OR ticker appears in
      narrative_html_en, extract every signed percentage from the EN
      narrative. Check whether the verified change_pct (rounded to 1 dp)
      appears in that set, allowing ±0.06 tolerance for rounding
      differences (e.g., "+1.2%" matching "+1.18%" → 1.2 vs 1.2 → OK).

      If the verified ticker is mentioned but NO matching percentage
      shows up in the narrative, that's a mismatch signal.
    """
    import re

    warnings: list[str] = []
    narrative_en = (data.get("narrative_html_en") or "").strip()
    if not narrative_en or not market_data:
        return warnings

    # Extract every signed percentage from the EN narrative.
    # Tolerates surrounding HTML — we just scan text for the pattern.
    raw_pcts = re.findall(r'[+-]?\d+\.?\d*\s*%', narrative_en)
    found_pcts: set[float] = set()
    for s in raw_pcts:
        try:
            val = float(s.rstrip("%").strip())
            # Bucket to 1 decimal place — Claude often writes +1.2 where
            # the verified value is +1.18, and we don't want to flag those.
            found_pcts.add(round(val, 1))
        except ValueError:
            continue

    for name, asset in market_data.items():
        if not isinstance(asset, dict):
            continue
        verified_pct = asset.get("change_pct")
        if verified_pct is None:
            continue
        ticker = asset.get("ticker") or ""

        # Only check tickers that the narrative actually references.
        # Avoid false positives for the dozens of tickers in market_data
        # that the prompt simply didn't have room to mention.
        # Name match is loose — "S&P 500" inside "the S&P 500 jumped" etc.
        mentioned = bool(name and name in narrative_en) or bool(ticker and ticker in narrative_en)
        if not mentioned:
            continue

        verified_rounded = round(float(verified_pct), 1)
        # Tolerance: ±0.15 in the bucketed space (~0.1 + rounding slack).
        match = any(abs(p - verified_rounded) <= 0.15 for p in found_pcts)
        if not match:
            warnings.append(
                f"slot={slot} ticker={ticker or '?'} name='{name}': "
                f"verified change_pct={verified_pct:+.2f}% mentioned in EN narrative "
                f"but no matching ±% (within ±0.15) found in the prose. "
                f"Review the published page for possible mismatch."
            )

    return warnings


# ---------------------------------------------------------------------------
# Anthropic call
# ---------------------------------------------------------------------------
def call_claude(prompt: str, *, model: str = "claude-sonnet-4-5", max_tokens: int = 48000) -> dict:
    """Call Claude API with web_search tool. Returns parsed JSON dict.

    max_tokens raised from 32000 to 48000 (Sub-step 2a-2 deploy) to accommodate
    the 4-language narrative output. Sonnet 4.5's hard cap is 64000 output
    tokens — 48000 keeps a safety margin while fitting 4 × ~700-word narratives
    (~10-12K tokens) plus all _ja/_zh sibling fields (headline/summary/
    bottom_line/fact_check/forward_calendar) and web_search overhead.
    """
    import anthropic

    client = anthropic.Anthropic()

    messages = [{"role": "user", "content": prompt}]
    # Web search tool (Anthropic native, model server-side fetches).
    # max_uses=25 — bumped from 12 to support the v4 fact-check protocol
    # (every numeric data point must be cross-verified against 2-3 sources).
    tools = [
        {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 25,
        }
    ]

    print(f"[claude] calling {model} with {max_tokens=}, web_search enabled (max_uses=25) [streaming]")
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
        # Semantic class — color resolved at runtime via CSS variables.
        # body.convention-kr → red up / blue down (KR style).
        # body (default global) → green up / red down (Bloomberg style).
        chg_class = "up" if chg_f > 0 else ("down" if chg_f < 0 else "flat")
        arrow = "🔺" if chg_f > 0 else ("🔻" if chg_f < 0 else "·")
        cells.append(f"""
    <div class="km-cell">
      <div class="km-label">{html_escape(label)}</div>
      <div class="km-value">{html_escape(str(value))}</div>
      <div class="km-chg {chg_class}">{arrow} {chg_f:+.2f}%</div>
    </div>""")
    if not cells:
        return ""
    title = "▸ 핵심 시장 지표 · 24h" if lang == "ko" else "▸ Key Market Indicators · 24h"
    return f"""<div class="section-title">{title}</div>
<div class="km-grid">{''.join(cells)}</div>
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
    elif slot == "cn-open":
        # cn-open mirrors kr-open: overnight US spillover (Chinese tech tracks
        # Nasdaq + US-listed ADRs trade BABA/JD/PDD/BIDU/etc through US hours)
        # plus any CN news headlines the prompt produced.
        parts.append(render_indices_block(data.get("overnight_us", []), lang))
        parts.append(render_news(data.get("cn_news", []), lang))
    elif slot == "cn-close":
        # cn-close mirrors kr-close: domestic indices, themes, top movers,
        # session headlines. Indices key is `cn_indices` (parallel to
        # `kr_indices`); themes is `cn_themes`.
        parts.append(render_indices_block(data.get("cn_indices", []), lang))
        parts.append(render_themes(data.get("cn_themes", []), lang))
        parts.append(render_movers(data.get("winners", []), lang, "winners"))
        parts.append(render_movers(data.get("losers", []), lang, "losers"))
        parts.append(render_news(data.get("cn_news", []), lang))
    return "\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Full HTML render
# ---------------------------------------------------------------------------
def render_html(slot: str, lang: str, data: dict, *, slug: str, build: str, og_image_filename: str,
                trading_date: str, publish_date: str) -> str:
    cfg = SLOTS[slot]
    template = (TEMPLATES / "daily-base.html").read_text(encoding="utf-8")

    base_url = "https://luckyplz.com"
    # Canonical URL per-language. ko owns the bare slug; en/ja/zh use suffix.
    suffix = LANG_META[lang]["slug_suffix"]
    canonical = f"{base_url}/blog/{slug}{suffix}/"
    # hreflang URLs for all 4 languages. The template's placeholders are
    # ko/en today; ja/zh are emitted as additional <link> tags inside the
    # template via the {{HREFLANG_EXTRA}} substitution below.
    href_ko = f"{base_url}/blog/{slug}/"
    href_en = f"{base_url}/blog/{slug}-en/"
    href_ja = f"{base_url}/blog/{slug}-ja/"
    href_zh = f"{base_url}/blog/{slug}-zh/"

    # Read multilingual content with graceful en fallback (ja/zh may be
    # missing if the prompt has not been extended yet).
    title = pick_localized(data, "headline", lang)
    title_full = f"{title} | Lucky Please"
    # Strip any inline HTML tags from summary — it's used in plain-text
    # contexts (meta description, og:description, twitter:description,
    # header sub-text) where html_escape() would render them as visible
    # &lt;strong&gt; etc. Claude sometimes includes <strong>/<span> in
    # summary despite the prompt rule; strip defensively.
    raw_summary = pick_localized(data, "summary", lang)
    summary = re.sub(r"<[^>]+>", "", raw_summary).strip()
    # Also collapse multiple spaces from tag removal
    summary = re.sub(r"\s+", " ", summary)
    bottom_body = pick_localized(data, "bottom_line", lang)
    bottom_title = L(lang,
                     ko="BOTTOM LINE · 포지셔닝",
                     en="BOTTOM LINE",
                     ja="ボトムライン · ポジショニング",
                     zh="底线 · 持仓策略")

    keywords_map = {
        "us-close": {
            "ko": "미국 증시 마감, 테크 리캡, S&P Nasdaq, Mag 7, 데일리 리뷰, lucky please",
            "en": "US tech recap, S&P Nasdaq close, Magnificent 7, daily debrief, lucky please",
            "ja": "米国株 引け, テックリキャップ, S&P ナスダック, マグニフィセント7, デイリーレビュー",
            "zh": "美股收盘, 科技复盘, 标普纳指, 七巨头, 每日回顾",
        },
        "kr-open": {
            "ko": "한국증시 개장, 코스피 개장, 외인 매수 예상, ADR, 매그니피센트 7, 데일리 브리프",
            "en": "Korea market open brief, KOSPI futures, ADR overnight, KR semis",
            "ja": "韓国市場 寄り付き, コスピ 開始, ADR, KR 半導体, デイリーブリーフ",
            "zh": "韩国股市开盘, KOSPI 期货, ADR, 韩国半导体, 每日简报",
        },
        "kr-close": {
            "ko": "한국증시 마감, 코스피 마감, 외인 수급, 한국 섹터, 데일리 리캡",
            "en": "Korea market close, KOSPI, foreign flow, KR tech sectors",
            "ja": "韓国市場引け, コスピ 終値, 外国人 需給, 韓国 セクター, デイリーリキャップ",
            "zh": "韩国股市收盘, KOSPI 收盘, 外资动向, 韩国板块, 每日复盘",
        },
        "us-premarket": {
            "ko": "미국 프리마켓, 야간 시황, 어닝 캘린더, 매크로 이벤트, 데일리 브리프",
            "en": "US premarket, earnings calendar, macro events, daily brief",
            "ja": "米国プレマーケット, ナイトセッション, 決算カレンダー, マクロイベント, デイリーブリーフ",
            "zh": "美股盘前, 隔夜行情, 财报日历, 宏观事件, 每日简报",
        },
        "cn-open": {
            "ko": "중국증시 개장, 상해종합, CSI 300, 항생지수, 텐센트, 알리바바, 데일리 브리프",
            "en": "China market open brief, SSE Composite, CSI 300, Hang Seng, Tencent, Alibaba, daily brief",
            "ja": "中国市場 寄り付き, 上海総合, CSI 300, ハンセン指数, テンセント, アリババ, デイリーブリーフ",
            "zh": "中国股市开盘, 上证综指, 沪深300, 恒生指数, 腾讯, 阿里巴巴, 每日简报",
        },
        "cn-close": {
            "ko": "중국증시 마감, 상해 마감, 외인 북향자금, 중국 테크, 항생, 데일리 리캡",
            "en": "China market close, SSE close, northbound flow, China tech, Hang Seng, daily recap",
            "ja": "中国市場引け, 上海 終値, ノースバウンド資金, 中国テック, ハンセン, デイリーリキャップ",
            "zh": "中国股市收盘, 上证收盘, 北向资金, 中国科技, 恒生, 每日复盘",
        },
    }
    keywords = keywords_map[slot].get(lang, keywords_map[slot]["en"])

    # OG meta
    og_locale = LANG_META[lang]["og_locale"]
    og_locale_alt = "en_US" if lang != "en" else "ko_KR"
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
    # Breadcrumb label per (slot × lang). SLOTS dict already carries the
    # per-language header label, so reuse it instead of duplicating here.
    breadcrumb_label = cfg.get(f"header_label_{lang}") or cfg["header_label_en"]
    home_label = L(lang, ko="홈", en="Home", ja="ホーム", zh="首页")
    blog_label = L(lang, ko="블로그", en="Blog", ja="ブログ", zh="博客")
    jsonld_crumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1,
             "name": home_label, "item": f"{base_url}/"},
            {"@type": "ListItem", "position": 2,
             "name": blog_label, "item": f"{base_url}/blog/"},
            {"@type": "ListItem", "position": 3, "name": breadcrumb_label, "item": canonical},
        ],
    }

    # Badges from indices (top 5 by absolute change). The data key varies
    # per slot — Claude emits `indices` for us-close, `kr_indices` for
    # kr-close, `cn_indices` for cn-close, `futures` for us-premarket,
    # `overnight_us` for kr-open / cn-open.
    indices = (data.get("indices") or data.get("kr_indices") or data.get("cn_indices")
               or data.get("futures") or data.get("overnight_us") or [])
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
    disclaimer_ja = ("<strong>📌 デイリーリキャップ · {ts}</strong><br>"
                     "公開市場データに基づく自動キュレーション。Yahoo Finance · Investing.com · KRX · CNBC · TheStreet など。<br>"
                     "売買推奨ではありません。投資判断はご自身の責任で。").format(ts=publish_date)
    disclaimer_zh = ("<strong>📌 每日复盘 · {ts}</strong><br>"
                     "基于公开市场数据的自动整理。来源：Yahoo Finance · Investing.com · KRX · CNBC · TheStreet 等。<br>"
                     "本文不构成买卖建议，投资决策由读者自行承担。").format(ts=publish_date)
    disclaimer = L(lang, ko=disclaimer_ko, en=disclaimer_en, ja=disclaimer_ja, zh=disclaimer_zh)

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
    footer_ja = ("<strong>📢 出典 & 免責事項</strong><br>"
                 f"{publish_date} 公開 · 出典: {src_html}<br>"
                 "売買推奨ではなく、投資判断はご自身の責任でお願いします。")
    footer_zh = ("<strong>📢 来源 & 免责声明</strong><br>"
                 f"发布于 {publish_date} · 来源: {src_html}<br>"
                 "本文不构成买卖建议，投资决策由读者自行承担。")
    footer_disclaimer = L(lang, ko=footer_ko, en=footer_en, ja=footer_ja, zh=footer_zh)

    # Related links — link to sibling slots of same trading_date if exist.
    # Korean-language related box stays Korean-only (links to /blog/daily/ + the
    # semiconductor-rally-2026 ko version). Everyone else (en/ja/zh) gets the
    # English related set — same fallback policy as the rest of the templating
    # while ja/zh content backlogs are being filled in.
    if lang == "ko":
        related_title = "관련 글 RELATED"
        related_links = (
            f'<a href="/blog/daily/">데일리 시리즈 인덱스 전체 보기 →</a>\n'
            f'<a href="/blog/semiconductor-rally-2026/">반도체 슈퍼랠리 2026 — 한미 반도체주는 어디까지 오를까?</a>'
        )
    else:
        related_title = L(lang, ko="관련 글 RELATED", en="RELATED",
                          ja="関連記事 RELATED", zh="相关文章 RELATED")
        related_links = (
            f'<a href="/blog/daily/">See full daily series index →</a>\n'
            f'<a href="/blog/semiconductor-rally-2026-en/">Semiconductor Super-Rally 2026 — How High Can KR & US Chip Stocks Go?</a>'
        )

    # Body sections — combine v2 fields (key_metrics strip, deep narrative,
    # forward calendar, fact-check) with legacy card sections for backwards compat.
    # Multilingual fields use pick_localized() so ja/zh fall back to en if the
    # prompt has not been extended yet — keeps the pipeline running while
    # content catches up.
    key_strip = render_key_metrics_strip(data.get("key_metrics", {}), lang)
    narrative = render_narrative(pick_localized(data, "narrative_html", lang), lang)
    cards = render_sections(slot, data, lang)
    forward_cal = render_forward_calendar(pick_localized(data, "forward_calendar_html", lang), lang)
    fact_check_box = render_fact_check(pick_localized(data, "fact_check", lang), lang)
    # Order: 7-asset strip (fixed top) → deep narrative (main) → visual cards
    # (supplementary) → forward calendar → fact-check (closing).
    sections_html = "\n".join(p for p in [key_strip, narrative, cards, forward_cal, fact_check_box] if p)

    # Substitutions
    # Font selection by language family:
    #   ko → Noto Sans KR  ja → Noto Sans JP  zh → Noto Sans SC
    #   en/everything else → Inter
    # CJK fallback chain is sufficient inside each — browsers will pick the
    # closest available glyphs if the primary face fails to load.
    nav_back = "← BLOG"
    if lang == "ko":
        body_font = "'Noto Sans KR', sans-serif"
        font_url = "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=JetBrains+Mono:wght@400;700&family=Bebas+Neue&display=swap"
    elif lang == "ja":
        body_font = "'Noto Sans JP', 'Noto Sans KR', sans-serif"
        font_url = "https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=JetBrains+Mono:wght@400;700&family=Bebas+Neue&display=swap"
    elif lang == "zh":
        body_font = "'Noto Sans SC', 'Noto Sans KR', sans-serif"
        font_url = "https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&family=JetBrains+Mono:wght@400;700&family=Bebas+Neue&display=swap"
    else:
        body_font = "'Inter', sans-serif"
        font_url = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700&family=JetBrains+Mono:wght@400;700&family=Bebas+Neue&display=swap"

    header_label_text = cfg.get(f"header_label_{lang}") or cfg["header_label_en"]
    header_label = f"{header_label_text} · {publish_date}"

    repl = {
        "{{LANG}}": lang,
        # Color convention: KR slots use Korean convention (red up / blue down,
        # Naver/한국증권사 style). US slots use global convention (green up /
        # red down, Bloomberg/TradingView/WSJ style). Body class toggles
        # CSS --up/--down variables in daily-base.html.
        "{{CONVENTION}}": "kr" if slot in ("kr-open", "kr-close") else "global",
        "{{BUILD}}": build,
        "{{TITLE}}": html_escape(title_full),
        "{{TITLE_SHORT}}": html_escape(title),
        "{{DESCRIPTION}}": html_escape(summary[:200]),
        "{{KEYWORDS}}": html_escape(keywords),
        "{{CANONICAL_URL}}": canonical,
        "{{HREFLANG_KO}}": href_ko,
        "{{HREFLANG_EN}}": href_en,
        "{{HREFLANG_JA}}": href_ja,
        "{{HREFLANG_ZH}}": href_zh,
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
def write_post_files(slug: str, htmls: dict, og_paths: dict) -> None:
    """Write per-language index.html files. Empty languages are skipped.

    htmls    — dict of {lang: html_string}. Languages absent or empty
               are simply not written (graceful skip).
    og_paths — dict of {lang: Path} for OG images. Logged but not written
               here (gen_og_image already wrote them to disk).

    Slug convention: ko → bare slug, en/ja/zh → `{slug}-{lang}`.
    """
    for lang in LANGS:
        html = htmls.get(lang) or ""
        if not html.strip():
            continue
        suffix = LANG_META[lang]["slug_suffix"]
        directory = BLOG_DIR / f"{slug}{suffix}"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(html, encoding="utf-8")
        print(f"[write] {directory}/index.html ({len(html)} bytes)")
        og_path = og_paths.get(lang)
        if og_path:
            print(f"[write] OG {lang}: {og_path}")


def update_posts_js(slug: str, slot: str, data: dict, publish_date: str,
                    langs: list[str] | None = None) -> None:
    """Prepend one entry per language to window.BLOG_POSTS.

    langs — list of languages to publish. Defaults to ko+en (legacy) when
            not provided, so callers that haven't been updated keep their
            existing behavior. Pass ["ko","en","ja","zh"] (or the subset
            with actual data) to publish 4-language entries.

    Each entry carries:
      - the legacy `alt` field (single sibling slug, ko↔en relationship
        preserved) for backward compat with old site code
      - the new `alts` object (forward-link to every sibling that exists)
        consumed by the multi-language router added in Step 3
    """
    if langs is None:
        langs = ["ko", "en"]

    cfg = SLOTS[slot]
    posts_path = PUBLIC / "blog" / "posts.js"
    raw = posts_path.read_text(encoding="utf-8")
    insert_marker = "window.BLOG_POSTS = ["
    idx = raw.find(insert_marker)
    if idx == -1:
        raise SystemExit("Could not find BLOG_POSTS array in posts.js")

    # Default tags per language (used when prompt doesn't supply og_tags_<lang>)
    default_tags = {
        "ko": ['데일리 리캡', '미국증시', '한국증시', '테크'],
        "en": ['Daily Recap', 'US Markets', 'KR Markets', 'Tech'],
        "ja": ['デイリーリキャップ', '米国株', '韓国株', 'テック'],
        "zh": ['每日复盘', '美股', '韩股', '科技'],
    }

    # Build a (lang → published_slug) mapping for alts cross-linking
    slug_map = {l: f"{slug}{LANG_META[l]['slug_suffix']}" for l in langs}

    entries = []
    for lang in langs:
        # Graceful skip if Claude didn't produce ja/zh headline.
        # ko/en always pass through has_lang_content (legacy contract).
        if not has_lang_content(data, lang):
            continue
        entry_slug = slug_map[lang]
        # Legacy `alt` field — points to opposite primary (ko↔en).
        # Keeps the older site code that reads `alt` working unchanged.
        alt_legacy = slug_map.get("en", entry_slug) if lang == "ko" else slug_map.get("ko", entry_slug)
        # New `alts` object — forward-links to every OTHER published lang.
        alts_obj = {l: s for l, s in slug_map.items() if l != lang}
        alts_js = "{ " + ", ".join(f"{k}: '{v}'" for k, v in alts_obj.items()) + " }"

        tags = data.get(f"og_tags_{lang}") or default_tags.get(lang) or default_tags["en"]
        title = pick_localized(data, "headline", lang)
        excerpt = pick_localized(data, "summary", lang)[:180]

        entries.append(textwrap.dedent(f"""\
            {{
                slug: '{entry_slug}',
                lang: '{lang}',
                category: '{cfg["category"]}',
                date: '{publish_date}',
                readMinutes: {cfg["read_min"]},
                coverEmoji: '{cfg["cover_emoji"]}',
                tags: {json.dumps(tags, ensure_ascii=False)},
                title: {json.dumps(title, ensure_ascii=False)},
                excerpt: {json.dumps(excerpt, ensure_ascii=False)},
                alt: '{alt_legacy}',
                alts: {alts_js},
            }},"""))

    if not entries:
        print(f"[posts.js] no entries to prepend for slug={slug} (no language content)")
        return

    combined = "\n    ".join(entries)
    new_raw = raw[: idx + len(insert_marker)] + "\n    " + combined + raw[idx + len(insert_marker):]
    posts_path.write_text(new_raw, encoding="utf-8")
    print(f"[posts.js] prepended slug={slug} for langs={','.join(langs)}")


def update_sitemap(slug: str, publish_date: str,
                   langs: list[str] | None = None) -> None:
    """Append one <url> block per published language to sitemap.xml.

    Each block carries hreflang alternates for every Tier A language so
    Google Search Console understands the full cluster, even when only a
    subset is published (ja/zh fall through to en for search indexing
    until the prompt is extended to emit them).
    """
    if langs is None:
        langs = ["ko", "en"]

    sm_path = PUBLIC / "sitemap.xml"
    raw = sm_path.read_text(encoding="utf-8")

    # Build the cluster of <url> blocks for this slug × langs combination.
    # Each block reuses the same hreflang alternates so the search engine
    # sees the language cluster consistently from every entry point.
    blocks = []
    for lang in langs:
        suffix = LANG_META[lang]["slug_suffix"]
        url_slug = f"{slug}{suffix}"
        block = textwrap.dedent(f"""\
            <url>
                <loc>https://luckyplz.com/blog/{url_slug}/</loc>
                <lastmod>{publish_date}</lastmod>
                <changefreq>daily</changefreq>
                <priority>0.85</priority>
                <xhtml:link rel="alternate" hreflang="ko" href="https://luckyplz.com/blog/{slug}/"/>
                <xhtml:link rel="alternate" hreflang="en" href="https://luckyplz.com/blog/{slug}-en/"/>
                <xhtml:link rel="alternate" hreflang="ja" href="https://luckyplz.com/blog/{slug}-ja/"/>
                <xhtml:link rel="alternate" hreflang="zh" href="https://luckyplz.com/blog/{slug}-zh/"/>
                <xhtml:link rel="alternate" hreflang="x-default" href="https://luckyplz.com/blog/{slug}-en/"/>
            </url>
            """)
        blocks.append(block)

    new_block = "\n".join(blocks) + "\n"

    anchor = "<url>\n        <loc>https://luckyplz.com/blog/us-tech-recap-2026-05-11/</loc>"
    if anchor in raw:
        raw = raw.replace(anchor, new_block + "    " + anchor.lstrip())
    else:
        raw = raw.replace("</urlset>", new_block + "</urlset>")
    sm_path.write_text(raw, encoding="utf-8")
    print(f"[sitemap] added {slug} for langs={','.join(langs)}")


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

    # Push with robust race-recovery. The workflow generates a single new
    # blog post (no overlap with other slots' files), so any rebase
    # conflict is almost certainly mechanical (config edits, line endings)
    # and recoverable. Strategy: up to 6 attempts with progressive recovery.
    #
    # Attempt fails (non-fast-forward) → fetch + try fast-forward rebase.
    # Rebase conflict → resolve by KEEPING OUR new files (--theirs in rebase
    # semantics keeps the upstream version of conflicting non-new files,
    # ours/our-new-post files survive). Then retry push.
    # Final fallback: if all rebase paths fail, do a soft reset to remote
    # main, replay our staged changes on top, and push. Aggressive but
    # safe because our changes are well-defined (one slug directory + posts.js
    # one-line addition + sitemap one-block addition + bump-cache results).
    import random
    for attempt in range(1, 7):
        push_result = subprocess.run(["git", "push"], cwd=ROOT,
                                     capture_output=True, text=True)
        if push_result.returncode == 0:
            print(f"[git] pushed {slug} (attempt {attempt})")
            return
        print(f"[git] push attempt {attempt} rejected: {push_result.stderr.strip()[:200]}")
        if attempt == 6:
            print(f"[git] all 6 push attempts failed for {slug}")
            raise subprocess.CalledProcessError(push_result.returncode,
                                                ["git", "push"],
                                                output=push_result.stdout,
                                                stderr=push_result.stderr)
        # Random jitter 1-5s before rebase to desync from concurrent workflows.
        time.sleep(1 + random.random() * 4)
        # Pull --rebase. Use -X theirs to auto-resolve conflicts by taking
        # upstream version for ANY file (our new-post files don't exist
        # upstream so they survive untouched).
        print(f"[git] running 'git pull --rebase -X theirs' before retry...")
        rebase = subprocess.run(
            ["git", "pull", "--rebase", "-X", "theirs", "origin", "main"],
            cwd=ROOT, capture_output=True, text=True)
        if rebase.returncode == 0:
            print(f"[git] rebase ok, retrying push...")
            continue
        # Rebase failed even with -X theirs. Abort and try harder recovery.
        print(f"[git] rebase -X theirs failed: {rebase.stderr.strip()[:200]}")
        subprocess.run(["git", "rebase", "--abort"], cwd=ROOT, capture_output=True)
        if attempt >= 4:
            # Aggressive recovery: stash our commit's changes, reset to
            # remote main, re-apply, recommit, retry push. This always
            # produces a fast-forwardable state.
            print(f"[git] attempt {attempt} hard recovery: reset to origin/main + replay")
            # Save commit message
            try:
                last_msg = subprocess.run(
                    ["git", "log", "-1", "--pretty=%B"], cwd=ROOT,
                    capture_output=True, text=True, check=True).stdout.strip()
            except Exception:
                last_msg = msg  # fall back to original msg variable
            # Soft reset to undo our commit but keep changes staged
            subprocess.run(["git", "reset", "--soft", "HEAD~1"], cwd=ROOT,
                           capture_output=True)
            # Fetch latest origin/main
            subprocess.run(["git", "fetch", "origin", "main"], cwd=ROOT,
                           capture_output=True)
            # Reset working dir to match origin/main but keep our staged changes
            # via stash → reset → pop pattern
            subprocess.run(["git", "stash", "push", "-u", "-m", "lp-push-recovery"],
                           cwd=ROOT, capture_output=True)
            subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=ROOT,
                           capture_output=True)
            pop = subprocess.run(["git", "stash", "pop"], cwd=ROOT,
                                 capture_output=True, text=True)
            if pop.returncode != 0:
                # Stash pop conflict — checkout our version for any conflicted file
                # (our changes are the new content we want to publish).
                print(f"[git] stash pop conflict, resolving with ours")
                subprocess.run(["git", "checkout", "--theirs", "."], cwd=ROOT,
                               capture_output=True)
            subprocess.run(["git", "add", "-A"], cwd=ROOT, capture_output=True)
            subprocess.run(["git", "commit", "-m", last_msg], cwd=ROOT,
                           capture_output=True)
            print(f"[git] hard recovery complete, retrying push...")


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

    # === HOLIDAY / WEEKEND GUARD (short-circuit before any API call) ===
    # User report 2026-05-23: holiday posts were being generated from
    # hallucinated data because Claude's prompt-based holiday detection
    # is unreliable. Now we check the authoritative exchange calendar
    # BEFORE spending any Anthropic / yfinance / web_search budget.
    # Force flag bypasses this for manual backfill scenarios.
    if not args.force:
        market = SLOT_TO_MARKET.get(args.slot)
        if market:
            is_open, reason = is_trading_day(trading_date, market)
            if not is_open:
                print(f"[holiday] {market} closed on {trading_date} ({reason}). Exiting cleanly — no post generated.")
                return
            else:
                print(f"[holiday] {market} open on {trading_date} ({reason}). Proceeding with pipeline.")

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

    # === HARD FETCH MARKET DATA (yfinance) ===
    # Replaces Claude hallucination of training-data numbers. Indices, stocks,
    # FX, commodities, crypto are fetched directly from Yahoo Finance API
    # and injected into the prompt as MANDATORY ground truth. Claude writes
    # narrative around the fixed numbers.
    market_data = fetch_market_data(args.slot, trading_date)
    verified_block = format_market_data_for_prompt(market_data, trading_date)

    # Load + fill prompt
    prompt_template = (PROMPTS / cfg["prompt"]).read_text(encoding="utf-8")
    prompt = prompt_template.replace("{trading_date}", trading_date).replace("{publish_date}", publish_date)

    # Prepend verified data block AT THE TOP (above everything else) so
    # Claude sees authoritative numbers before its own training-data biases.
    if verified_block:
        prompt = verified_block + "\n" + prompt

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
        "## 4. 📊 지수/섹터 스냅샷 → semantic class spans only\n"
        "Inside paragraphs and lists, use **semantic classes** (color is automatic from CSS):\n"
        "- `<span class=\"upx\">+1.24%</span>` for positive moves (semantically 'up')\n"
        "- `<span class=\"dn\">-1.54%</span>` for negative moves (semantically 'down')\n"
        "- `<span class=\"hl\">중립</span>` for highlight/attention (gold)\n\n"
        "⚠️ **NEVER use inline color styles** like `style=\"color:#dc2626\"` or `style=\"color:red\"`. "
        "The site auto-selects the correct color convention based on the slot:\n"
        "- KR slots (kr-open, kr-close) → red up / blue down (한국 컨벤션, Naver Finance style)\n"
        "- US slots (us-close, us-premarket) → green up / red down (글로벌 컨벤션, Bloomberg/TradingView style)\n"
        "Hardcoded colors break this convention split. Use `class=\"upx\"`/`class=\"dn\"` and let the CSS handle it.\n\n"
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

    # V4 FACT-CHECK PROTOCOL — mandatory 2-3 source cross-verification for
    # every numeric data point. Without this Claude takes one web_search
    # result at face value and publishes wrong index closes / stock prices
    # / sector %s, which has destroyed reader trust on previous runs.
    fact_check_protocol = (
        "\n\n---\n"
        "# 🔒 FACT-CHECK PROTOCOL — MANDATORY MULTI-SOURCE VERIFICATION\n\n"
        "**THIS IS A FINANCIAL BLOG. Wrong numbers destroy reader trust. "
        "Spend more web_search calls and take longer — that is required, not optional.**\n\n"
        "## Source tier list (use ONLY these — never blog posts or aggregators)\n\n"
        "**For Korean market data (KOSPI, KOSDAQ, KOSPI200, VKOSPI, sector ETFs, "
        "individual KR stocks, 외인/기관 수급, USD/KRW):**\n"
        "- TIER 1 (primary, authoritative): KRX official (krx.co.kr, marketdata.krx.co.kr), "
        "KIND (kind.krx.co.kr) for disclosures\n"
        "- TIER 2 (verify against TIER 1): Naver Finance (finance.naver.com), "
        "한국경제 (hankyung.com), 매일경제 (mk.co.kr), Reuters Korea, Bloomberg Korea\n"
        "- TIER 3 (only if TIER 1+2 unavailable): Investing.com KR section, Yahoo Finance KR\n\n"
        "**For US market data (Dow/SPX/Nasdaq/Russell 2000, 11 GICS sectors, "
        "Mag 7 stocks, US Treasury yields, DXY, VIX, US futures, WTI):**\n"
        "- TIER 1: WSJ (wsj.com), CNBC (cnbc.com), Reuters (reuters.com), "
        "Bloomberg (bloomberg.com), Briefing.com, NYSE/Nasdaq official\n"
        "- TIER 2: Yahoo Finance, MarketWatch, Investing.com US\n"
        "- TIER 3 (macro only): FRED (fred.stlouisfed.org), BLS (bls.gov), BEA (bea.gov) — these are PRIMARY for CPI/PPI/Jobs/GDP releases\n\n"
        "**For crypto (BTC, ETH, XRP):**\n"
        "- TIER 1: CoinMarketCap, CoinGecko\n"
        "- TIER 2: Binance, Coinbase, Kraken official tickers\n\n"
        "**For commodities (Gold, Silver, WTI, Brent):**\n"
        "- TIER 1: CME/COMEX official, Kitco (gold/silver), EIA (oil)\n"
        "- TIER 2: Investing.com commodities, Yahoo Finance futures\n\n"
        "## Verification procedure (apply to EVERY numeric data point in your output)\n\n"
        "For each number you plan to publish (index close, sector %, stock price, "
        "yield, currency rate, volume, 수급 net buy/sell):\n\n"
        "1. **Fetch from 2 independent sources.** One MUST be Tier 1 if possible. "
        "Spend separate web_search calls for each source — never assume one search "
        "result covers multiple data points authoritatively.\n"
        "2. **Compare the values.**\n"
        "   - If they agree (within ±0.05% for indices, ±0.5% for individual stocks, "
        "exact match for discrete values like 종목코드): ✅ accept the consensus value.\n"
        "   - If they disagree: fetch a **3rd Tier 1 or Tier 2 source as tiebreaker**.\n"
        "3. **If 2-of-3 still disagree, DROP that data point.** Never hedge with "
        "\"approximately\" or \"around\" — just remove it from the JSON. The post "
        "is better one number short than wrong.\n"
        "4. **For dated data** (closing prices, daily volumes), confirm the source's "
        "date matches trading_date. Some sites lag by 1 day or show stale cache. "
        "If the source's reported date doesn't match trading_date, do NOT use it.\n"
        "5. **For Korean market data specifically**: always verify against KRX (Tier 1) "
        "when possible. KRX is the authoritative source. Naver/한경/매경 should agree "
        "with KRX; if they don't, KRX wins. Foreign English sites (Yahoo/Investing.com) "
        "are sometimes lagged or slightly off on KR data — use as Tier 2/3 only.\n\n"
        "## What to put in the `sources` JSON field\n\n"
        "List **only the URLs you actually verified data against**. Don't pad with "
        "generic landing pages. Each source should be the specific page that provides "
        "the data (e.g., a KRX index page, a Yahoo Finance stock quote page, a Reuters "
        "earnings report URL — not just `wsj.com`).\n\n"
        "## What to put in the `fact_check_ko` / `fact_check_en` field\n\n"
        "Be specific. Don't just say \"verified against sources.\" Say:\n"
        "예: \"Fact-Check: KOSPI 종가는 KRX 공식 (2,847.32) + Naver Finance + "
        "Reuters Korea 3개 출처 일치 확인. 외국인 순매도 -8,452억원은 KRX 투자자별 "
        "매매동향 + 한경 보도 일치. NVDA -2.8%는 WSJ + CNBC + Yahoo Finance 3중 확인. "
        "검증 실패한 항목: [있으면 명시, 없으면 '없음'].\"\n\n"
        "## Trade-offs explicitly acknowledged\n\n"
        "- This protocol will use 15-25 web_search calls per post (max_uses=25).\n"
        "- Response time will increase to 5-8 minutes per slot.\n"
        "- This is intentional and required. **Speed is not the goal — accuracy is.**\n"
    )
    prompt = prompt + fact_check_protocol

    # OG IMAGE DATA — explicit schema for the 4-card SNS preview image.
    # Without this, V4's compressed prompt left og_data as {...} placeholder
    # and Claude returned empty cards, leaving the OG image blank.
    og_data_guide = (
        "\n\n---\n"
        "# 🖼 OG IMAGE DATA — 4-card highlight schema (MANDATORY)\n\n"
        "The OG image (shown when this post is shared to KakaoTalk / Twitter / "
        "Facebook etc.) displays 4 highlight cards. You MUST fill all 4 cards "
        "with the data shape below. Empty objects (`{}`) will produce a blank "
        "card and ruin the first impression of the post on social platforms.\n\n"
        "```json\n"
        "\"og_data\": {\n"
        "  \"card1\": {\"tick\":\"S&P 500\",\"val\":\"7,432\",\"sub\":\"+1.08%\",\"color\":\"up\"},\n"
        "  \"card2\": {\"tick\":\"NVDA\",\"val\":\"$143\",\"sub\":\"-2.8%\",\"color\":\"down\"},\n"
        "  \"card3\": {\"tick\":\"WTI\",\"val\":\"$99.5\",\"sub\":\"-7.66%\",\"color\":\"down\"},\n"
        "  \"card4\": {\"tick\":\"10Y\",\"val\":\"4.57%\",\"sub\":\"-2.04%\",\"color\":\"down\"}\n"
        "}\n"
        "```\n\n"
        "## Each card requires ALL 4 keys\n"
        "- `tick` — ticker or 지표명 (max 12 chars). e.g. `S&P 500`, `KOSPI`, `NVDA`, `WTI`, `10Y`, `USD/KRW`, `BTC`, `005930`(종목코드 가능)\n"
        "- `val`  — main value (max 10 chars). e.g. `7,432`, `$143.22`, `4.57%`, `1,365.20`, `+8.42%`\n"
        "- `sub`  — sub label / change (max 14 chars). e.g. `+1.08%`, `-2.8% AH`, `신고가`, `외인 -8천억`, `매물 출회`\n"
        "- `color` — one of: `up` (상승), `down` (하락), `gold` (강조/특별), `flat` (보합)\n\n"
        "## Per-slot card selection guide\n"
        "- **us-close**: card1=핵심 지수 (S&P 또는 Nasdaq), card2=가장 큰 Mag 7 무브, card3=매크로 (10Y/WTI/DXY 중 가장 movement큰 것), card4=after-hours 어닝 빅 무버\n"
        "- **kr-open**: card1=KOSPI 200 야간선물 추정, card2=美 야간 핵심 종목 (NVDA/SOX 등), card3=USD/KRW, card4=갭 예상 KR 종목\n"
        "- **kr-close**: card1=KOSPI, card2=외인 net (`외인 -8천억` 같이), card3=주도 종목 또는 섹터, card4=USD/KRW 또는 KOSDAQ\n"
        "- **us-premarket**: card1=핵심 futures (ES/NQ), card2=방금 발표된 경제 데이터 (있으면) 또는 Mag 7, card3=10Y, card4=프리마켓 빅 무버\n\n"
        "## Hard rules\n"
        "- 모든 4 card 채워라. 절대 `{}` 빈 객체 금지.\n"
        "- 숫자는 VERIFIED MARKET DATA (Yahoo Finance API fetch) 의 값 그대로 사용.\n"
        "- 한국어 sub 가능 (예: `신고가`, `매물 출회`). NanumGothic font로 정상 렌더링.\n"
        "- emoji 사용 금지 (OG 이미지 폰트에 emoji 없음 — □□로 표시됨).\n"
    )
    prompt = prompt + og_data_guide

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

    # Normalize numeric fields. Claude occasionally returns strings like
    # '+1.08%' / '1,234.56' / '-2.8%' instead of numbers for change_pct
    # and similar fields, which breaks numeric comparison downstream
    # (TypeError: '>' not supported between str and int). After the OG
    # guide was added (with explicit '+1.08%' string examples), Claude
    # started copying that format into all percentage fields.
    def _normalize_pct(item):
        if not isinstance(item, dict):
            return
        for k in ("change_pct", "expected_gap_pct", "pct", "gap_pct"):
            v = item.get(k)
            if isinstance(v, str):
                try:
                    item[k] = float(v.strip().replace('%', '').replace('+', '').replace(',', ''))
                except (ValueError, AttributeError):
                    item[k] = 0.0
    _list_fields = ("indices", "mag7", "themes", "winners", "losers",
                    "overnight_us", "gap_watch", "kr_indices", "kr_themes",
                    "futures", "global_overnight", "macro_data", "news",
                    "kr_news", "foreign_flow", "institution_flow")
    for fld in _list_fields:
        items = data.get(fld)
        if isinstance(items, list):
            for it in items:
                _normalize_pct(it)
    # nested: premarket_movers.{winners,losers}
    pm = data.get("premarket_movers")
    if isinstance(pm, dict):
        for sub in ("winners", "losers"):
            sub_list = pm.get(sub)
            if isinstance(sub_list, list):
                for it in sub_list:
                    _normalize_pct(it)
    # nested: key_metrics.{usdkrw,gold,...} each is {value, change_pct}
    km = data.get("key_metrics")
    if isinstance(km, dict):
        for asset_key, asset_data in km.items():
            _normalize_pct(asset_data)

    if data.get("skip"):
        print(f"[skip] {data.get('reason','holiday or no session')}. Exiting.")
        return

    # Read current build version (gets refreshed by bump-cache later)
    try:
        build = json.loads((PUBLIC / "build.json").read_text(encoding="utf-8"))["v"]
    except Exception:
        build = str(int(time.time()))

    # Decide which languages get published this run. ko + en are always
    # published (legacy contract — every prompt has emitted these since v1).
    # ja + zh are published only when Claude actually produced non-empty
    # `headline_<lang>`, so prompts that haven't been extended yet still
    # complete cleanly and the daily cron keeps running.
    publish_langs = [l for l in LANGS if has_lang_content(data, l)]
    print(f"[langs] publishing for {publish_langs}")

    # OG images (one per published language)
    ASSETS_BLOG.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(SCRIPTS))
    og_filenames = {}    # lang → filename (relative)
    og_paths = {}        # lang → absolute Path
    for lang in publish_langs:
        suffix = LANG_META[lang]["slug_suffix"]
        og_fn = f"og-{slug}{suffix}.png"
        og_filenames[lang] = og_fn
        og_paths[lang] = ASSETS_BLOG / og_fn
        try:
            gen_og_image(args.slot, data, lang, og_paths[lang])
        except Exception as e:
            print(f"[og] {lang} generation failed: {type(e).__name__}: {e} — continuing without OG image for this lang")
            # Don't abort the whole publish on OG failure — page still renders,
            # just without a per-lang OG (Twitter/KakaoTalk preview falls back
            # to default).

    # Render HTML per language
    htmls = {}
    for lang in publish_langs:
        try:
            htmls[lang] = render_html(args.slot, lang, data, slug=slug, build=build,
                                       og_image_filename=og_filenames[lang],
                                       trading_date=trading_date, publish_date=publish_date)
        except Exception as e:
            print(f"[render] {lang} failed: {type(e).__name__}: {e} — skipping this language only")
            # If a non-primary language render fails, drop that language but
            # still publish the rest. ko and en failures will propagate up
            # because they're load-bearing for the legacy cron contract.
            if lang in ("ko", "en"):
                raise

    # Make sure ko + en survived render (legacy contract — must always exist).
    if not htmls.get("ko") or not htmls.get("en"):
        raise SystemExit(f"[fatal] missing primary language(s): "
                         f"ko={'OK' if htmls.get('ko') else 'MISSING'} "
                         f"en={'OK' if htmls.get('en') else 'MISSING'}")

    # Trim publish_langs to those that actually rendered (a ja/zh failure
    # may have dropped them).
    publish_langs = [l for l in publish_langs if htmls.get(l)]

    # === ACCURACY DOUBLE-CHECK (option A: warn-only) ===
    # For each yfinance-verified ticker that the EN narrative actually
    # mentions, confirm a matching signed % shows up in the prose. Logs
    # GitHub Actions ::warning:: for any mismatch but does NOT block
    # the publish. Per user decision: surface mismatches in CI without
    # interrupting throughput; promote to retry/block later if real
    # mismatches accumulate. See validate_narrative_numbers() docstring.
    try:
        accuracy_warnings = validate_narrative_numbers(data, market_data, args.slot)
        for w in accuracy_warnings:
            # ::warning:: makes the message show up in the GH Actions UI
            # without failing the job, so the cron stays green but the
            # operator can spot drift at a glance.
            print(f"::warning::[validate] {w}")
        if accuracy_warnings:
            print(f"[validate] {len(accuracy_warnings)} potential mismatch(es) — publishing anyway (option A)")
        else:
            print(f"[validate] all verified-ticker references in EN narrative match yfinance values")
    except Exception as e:
        # Validation is best-effort. Never block a publish on a bug in
        # the heuristic itself.
        print(f"[validate] check skipped: {type(e).__name__}: {e}")

    write_post_files(slug, htmls, og_paths)

    # Site integration — only register languages we actually published.
    update_posts_js(slug, args.slot, data, publish_date, langs=publish_langs)
    update_sitemap(slug, publish_date, langs=publish_langs)

    # Cache + git
    bump_cache()
    git_push(slug, args.slot)
    print(f"[done] {slug}")


if __name__ == "__main__":
    main()
