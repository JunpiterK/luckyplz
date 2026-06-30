"""Auto Daily Post pipeline.

Generates one of 6 daily blog slots (us-close / us-premarket / kr-open / kr-close / cn-open / cn-close)
by calling Claude with web_search, rendering ko/en/ja/zh HTML + OG images,
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
        "category": "stocks",
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
        "category": "stocks",
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
        "category": "stocks",
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
        "category": "stocks",
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
        "category": "stocks",
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
        "category": "stocks",
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


# ---------------------------------------------------------------------------
# Three-tier check, called separately from main() so each tier can be
# bypassed (or not) independently.
#   Tier 0 — weekend (Sat/Sun): NEVER bypassable. Markets are globally
#            closed both days. Pure-Python, no library dependency, so it
#            can never silently fail.
#   Tier 1 — exchange holiday (XNYS / XKRX / XSHG): bypassable only with
#            explicit --bypass-holiday-guard flag, used for the rare
#            manual case (e.g., thematic essay we want timestamped on a
#            real holiday). When the calendar library cannot answer (no
#            install, date out of range), we now REFUSE to publish (was
#            previously "default to open" which silently masked failures
#            during the 2026-05-30/31 weekend incident; see CLAUDE.md).
# ---------------------------------------------------------------------------

_WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def is_weekend(date_str: str) -> tuple[bool, str]:
    """Tier-0 weekend check. Pure Python, no library, always works.

    Returns (is_weekend, day_name). `is_weekend` is True for Sat or Sun.
    Raises ValueError on invalid date format (caller handles).
    """
    from datetime import datetime
    target = datetime.strptime(date_str, "%Y-%m-%d").date()
    wd = target.weekday()    # 0=Mon..6=Sun
    return wd >= 5, _WEEKDAY_NAMES[wd]


def is_exchange_holiday(date_str: str, market: str) -> tuple[bool, str]:
    """Tier-1 exchange holiday check.

    Returns (is_holiday, reason). Caller MUST have already passed Tier-0
    (weekend) — this function assumes the date is a weekday.

    Raises ImportError if `exchange_calendars` not installed.
    Raises any other Exception (e.g., DateOutOfBounds) on lookup failure.
    The hard-fail design is intentional: silently defaulting to "open"
    on lookup error masked a real bug in 2026-05 and let us-tech-recap-
    2026-05-30 / 05-31 ship as weekend posts.
    """
    import exchange_calendars as ec
    cal = ec.get_calendar(market)
    if cal.is_session(date_str):
        return False, f"{market} regular trading session"
    return True, f"{market} holiday (closed weekday)"


def is_trading_day(date_str: str, market: str) -> tuple[bool, str]:
    """Legacy combined API kept for backward compat (used by older
    callers). New code should call `is_weekend()` and `is_exchange_holiday()`
    separately so each tier can be bypassed independently.

    Returns (is_open, reason). Hard-fails (returns is_open=False with a
    diagnostic reason) on library/lookup error rather than the old
    "default-open" behavior, because the previous behavior silently
    bypassed the guard when exchange_calendars data was out of range.
    """
    try:
        weekend, day_name = is_weekend(date_str)
    except ValueError:
        return False, f"invalid-date-format: {date_str}"
    if weekend:
        return False, f"weekend ({day_name})"
    try:
        holiday, reason = is_exchange_holiday(date_str, market)
    except ImportError:
        print(f"[holiday] exchange_calendars not installed — REFUSING to publish on uncertain holiday status for {market} {date_str}")
        return False, f"calendar-library-missing"
    except Exception as e:
        print(f"[holiday] {market} calendar lookup failed: {type(e).__name__}: {e} — REFUSING to publish on uncertain status")
        return False, f"calendar-lookup-error: {type(e).__name__}"
    if holiday:
        return False, reason
    return True, reason


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

# Severity thresholds for option D (Tier-branched validation). Tunable
# without code changes — bump them up if real-world mismatches are
# concentrated on rounding edges, bump down if catastrophic-grade
# errors slip through.
#
#   CLEAN        — zero mismatches
#   MINOR        — small drift only: ≤ MINOR_MAX_COUNT mismatches AND
#                  every observed diff is < MINOR_MAX_DIFF_PP
#   CATASTROPHIC — anything else (too many mismatches OR a single one
#                  that's too far from the verified value)
MINOR_MAX_COUNT = 2          # ≤2 mismatches still counts as minor
MINOR_MAX_DIFF_PP = 0.5      # any individual diff ≥ 0.5%p → catastrophic


def validate_narrative_numbers(data: dict, market_data: dict, slot: str) -> dict:
    """Detect potential narrative ↔ market_data mismatches and classify
    them by severity.

    Returns:
        {
          "severity":   "clean" | "minor" | "catastrophic",
          "warnings":   list[str]   — human-readable lines
          "mismatches": list[dict]  — structured detail per mismatch
                                       {ticker, name, verified_pct,
                                        nearest_found_pct, diff_pp}
          "max_diff":   float       — largest |verified - nearest_found|
                                       across all mismatches; 0 if clean
          "count":      int         — total mismatch count
        }

    Read-only — does not mutate inputs. Caller (main) decides what
    severity threshold triggers publish vs retry vs block; see the
    option-D control flow there.

    Algorithm:
      For each ticker in market_data whose name OR ticker appears in
      narrative_html_en, find the signed percentage in the prose that's
      closest to the verified change_pct. If even the closest match
      exceeds ±0.15 tolerance, record the diff and flag a mismatch.

      Why "nearest" instead of "any present"? When the prose says
      "S&P 500 closed +0.4% while semis surged +3.2%" and verified
      S&P is +0.37%, we want to know that the S&P reference matches
      +0.4 (diff=0.03, OK) and NOT confuse the +3.2 semis number with
      the S&P verification target.
    """
    import re

    result = {
        "severity": "clean",
        "warnings": [],
        "mismatches": [],
        "max_diff": 0.0,
        "count": 0,
    }
    narrative_en = (data.get("narrative_html_en") or "").strip()
    if not narrative_en or not market_data:
        return result

    if not re.search(r'[+-]?\d+\.?\d*\s*%', narrative_en):
        # Narrative has no percentages at all — nothing to validate.
        return result

    pct_re = re.compile(r'[+-]?\d+\.?\d*\s*%')
    # For each ticker mention we take the FIRST percentage that appears
    # within IMMEDIATE_WIN chars after the mention ends. This is much
    # tighter than a symmetric window and avoids the trap where a short
    # narrative has all 4 tickers' percentages in one sentence and the
    # validator picks the wrong neighbor (Case D in the unit tests: S&P
    # verified +0.37% but the validator was matching it to Nasdaq's
    # nearby +0.19% instead of S&P's actual +3.7% claim).
    #
    # Real narratives almost always quote a ticker's percentage within
    # 30-50 chars of the ticker mention itself ("S&P 500 +0.37%",
    # "S&P 500 closed at 6047.20, +0.37% on the day"). 80 chars is a
    # safe upper bound that catches the long form and still excludes
    # the next ticker's number.
    IMMEDIATE_WIN = 80

    for name, asset in market_data.items():
        if not isinstance(asset, dict):
            continue
        verified_pct = asset.get("change_pct")
        if verified_pct is None:
            continue
        ticker = asset.get("ticker") or ""

        # Collect end positions of every mention (start + len(needle))
        # so we can scan FORWARD from where the ticker name ends.
        mention_ends: list[int] = []
        for needle in (name, ticker):
            if not needle:
                continue
            try:
                pattern = re.compile(re.escape(needle))
            except re.error:
                continue
            for mm in pattern.finditer(narrative_en):
                mention_ends.append(mm.end())
        if not mention_ends:
            continue   # Ticker not referenced in the narrative — skip

        # For each mention, grab the FIRST % within IMMEDIATE_WIN chars.
        # We capture BOTH the raw text (so we can tell whether the sign was
        # explicit) and the float value. Sign-flip false positives were
        # blocking us-close 2026-06-01 — narrative "XLY fell 2.22%" was
        # being treated as +2.22 and compared to verified -2.22, scoring
        # diff 4.44%p. With explicit-sign detection, an unsigned magnitude
        # match is accepted (sign carried by surrounding verb), and only
        # an EXPLICITLY signed number with wrong sign triggers a flag.
        nearby_signed: list[tuple[float, bool]] = []   # (value, sign_was_explicit)
        for end in mention_ends:
            mm = pct_re.search(narrative_en, end, end + IMMEDIATE_WIN)
            if not mm:
                continue
            raw = mm.group()
            stripped = raw.strip()
            sign_explicit = stripped.startswith("+") or stripped.startswith("-")
            try:
                v = float(stripped.rstrip("%").strip())
            except ValueError:
                continue
            nearby_signed.append((v, sign_explicit))
        if not nearby_signed:
            continue   # Ticker mentioned but no % within 80 chars —
                       # narrative didn't quote a percentage for it,
                       # nothing to validate against.

        verified_f = float(verified_pct)
        verified_abs = abs(verified_f)
        # Two-pass matching to avoid false positives on unsigned magnitudes:
        #   PASS A (lenient, accept unsigned) — for each candidate, if its
        #          sign was NOT explicit ('+' / '-' missing), compare only
        #          absolute magnitude. "fell 2.22%" → 2.22 vs |verified|.
        #          Sign is assumed to be carried by surrounding prose
        #          (rose / fell / up / down / gained / lost).
        #   PASS B (strict, signed) — for explicit-sign candidates, compare
        #          signed value directly. A narrative that explicitly writes
        #          "+2.22%" when verified is -2.22% IS a real sign error
        #          and must still be flagged.
        # If ANY candidate from either pass matches within 0.15%p, accept.
        unsigned_diffs = [abs(abs(v) - verified_abs)
                          for v, exp in nearby_signed if not exp]
        signed_diffs   = [abs(v - verified_f)
                          for v, exp in nearby_signed if exp]
        best_unsigned = min(unsigned_diffs) if unsigned_diffs else None
        best_signed   = min(signed_diffs) if signed_diffs else None
        candidates = [d for d in (best_unsigned, best_signed) if d is not None]
        if not candidates:
            continue
        diff = min(candidates)
        if diff <= 0.15:
            continue   # within rounding tolerance — OK
        # Pick the actual signed value closest to verified for the
        # diagnostic message — picks the explicit signed one if available,
        # otherwise the closest unsigned magnitude (treated as positive).
        nearest = min((v for v, _ in nearby_signed),
                      key=lambda p: abs(p - verified_f))

        # Record the mismatch.
        result["mismatches"].append({
            "ticker": ticker or "?",
            "name": name,
            "verified_pct": round(verified_f, 2),
            "nearest_found_pct": round(nearest, 2),
            "diff_pp": round(diff, 2),
        })
        result["warnings"].append(
            f"slot={slot} ticker={ticker or '?'} name='{name}': "
            f"verified change_pct={verified_f:+.2f}% but EN narrative's "
            f"nearest value (within {IMMEDIATE_WIN} chars of the ticker mention) "
            f"is {nearest:+.2f}% (diff {diff:.2f}%p). Likely fabricated/swapped number."
        )

    result["count"] = len(result["mismatches"])
    if result["mismatches"]:
        result["max_diff"] = max(m["diff_pp"] for m in result["mismatches"])

    # Severity classification (option D thresholds, defined at module top).
    if result["count"] == 0:
        result["severity"] = "clean"
    elif result["count"] <= MINOR_MAX_COUNT and result["max_diff"] < MINOR_MAX_DIFF_PP:
        result["severity"] = "minor"
    else:
        result["severity"] = "catastrophic"

    return result


def build_fix_prompt(original_prompt: str, validation: dict) -> str:
    """Append a corrective retry instruction to the original prompt.

    Used when validate_narrative_numbers returns severity='catastrophic'.
    The retry call re-runs the SAME full prompt (so VERIFIED MARKET DATA,
    OPERATING CONTEXT, all slot-specific rules, web_search tool access,
    everything is preserved) with an extra section listing the specific
    mismatches Claude must fix. Cheaper than two separate calls and
    keeps the conversational context.
    """
    if not validation.get("mismatches"):
        return original_prompt

    bullets = []
    for m in validation["mismatches"]:
        bullets.append(
            f"- **{m['name']}** ({m['ticker']}): VERIFIED change_pct = "
            f"`{m['verified_pct']:+.2f}%`, but your last `narrative_html_en` "
            f"had nearest value `{m['nearest_found_pct']:+.2f}%` "
            f"(off by {m['diff_pp']:.2f}%p)."
        )

    fix_section = (
        "\n\n---\n"
        "# ⚠️ ACCURACY RETRY — your previous response had mismatches\n\n"
        "Your previous JSON output had numeric discrepancies between the "
        "narrative_html_en prose and the VERIFIED MARKET DATA block at the "
        "top of this prompt. Specifically:\n\n"
        + "\n".join(bullets)
        + "\n\n"
        "**REGENERATE the entire JSON response.** This time:\n"
        "1. Re-read the 🔒 VERIFIED MARKET DATA block above.\n"
        "2. Use those EXACT values byte-identically in `narrative_html_en` and "
        "every other field. Same digits, same decimals, same sign.\n"
        "3. Then translate the corrected English to `narrative_html_ko` → "
        "`_ja` → `_zh` (the same Step 2/3/4 process).\n"
        "4. Do NOT recompute change_pct from close/prev_close — use what "
        "VERIFIED already provided.\n"
        "5. If you're uncertain about a number, OMIT it. A missing number is "
        "acceptable; a wrong number destroys reader trust.\n\n"
        "Output the corrected JSON only. Same schema as before.\n"
    )
    return original_prompt + fix_section


# ---------------------------------------------------------------------------
# Anthropic call — with multi-layer reliability
# ---------------------------------------------------------------------------
# Failure modes the wrapper must survive, ordered by historical pain:
#
#   (1) httpx.RemoteProtocolError "incomplete chunked read" — mid-stream
#       connection drop. Killed 5/27 kr-open. Anthropic SDK's built-in
#       max_retries does NOT cover this (it only retries the INITIAL
#       request, not mid-stream failures).
#   (2) 529 "Overloaded" — server-side capacity. Anthropic-recommended
#       handling: backoff and retry.
#   (3) APIConnectionError / APITimeoutError / 5xx — transient network /
#       infrastructure. Always retry.
#   (4) RateLimitError (429) — respect Retry-After if present, otherwise
#       exponential backoff.
#
# Solution = tenacity wrapper with:
#   - 5 attempts (initial + 4 retries)
#   - wait_random_exponential(min=4, max=120) — AWS-style full jitter
#     prevents thundering herd if multiple slots collide on a retry boundary.
#   - retry_if_exception_type for the network + transient HTTP cases.
#
# Then a SEPARATE fallback-model layer outside the retry: if all 5 attempts
# on the primary model fail, try ONE attempt on a fallback model. This
# protects against single-model server outages (e.g., specific Sonnet
# version unavailable). The fallback is a smaller, cheaper, generally
# higher-availability model — we accept lower quality over zero publish.
#
# Streaming is preserved (NOT switched to non-streaming) because:
#   - max_tokens=48000 + web_search up to 25 uses can plausibly exceed
#     the SDK's 10-min non-streaming wall, and the SDK throws on that.
#   - The full-restart retry pattern works regardless of stream/non-stream:
#     a failed stream is discarded and the call starts over from scratch.

# Fallback model used when primary exhausts all retries. claude-sonnet-4
# is the previous-generation Sonnet — same family / similar prompting
# behavior / lower quality but much higher likelihood of being available
# when 4-5 is overloaded.
CLAUDE_FALLBACK_MODEL = "claude-sonnet-4-20250514"


def _claude_one_attempt(client, model: str, max_tokens: int, tools: list, messages: list):
    """One streaming attempt. Caller (tenacity) re-invokes on retryable failures.

    Returns the final assembled Anthropic response Message object. Raises
    the underlying exception unchanged so the retry decorator can classify.
    """
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        tools=tools,
        messages=messages,
    ) as stream:
        # Drain the stream — we don't need per-token progress, just the
        # final assembled message. Iteration here is what surfaces
        # mid-stream errors like RemoteProtocolError.
        for _event in stream:
            pass
        return stream.get_final_message()


def _is_retryable_status(exc: BaseException) -> bool:
    """Whether an Anthropic APIStatusError represents a TRANSIENT failure.

    True for: 408 (timeout), 425 (too early), 429 (rate limit),
              500/502/503/504 (server), 529 (overloaded).
    False for: 400 (bad request), 401/403 (auth) — these never fix themselves.
    """
    try:
        import anthropic
    except Exception:
        return False
    if isinstance(exc, anthropic.APIStatusError):
        return getattr(exc, "status_code", None) in (
            408, 425, 429, 500, 502, 503, 504, 529,
        )
    return False


def call_claude(
    prompt: str,
    *,
    model: str = "claude-sonnet-4-5",
    max_tokens: int = 48000,
    enable_fallback_model: bool = True,
) -> dict:
    """Call Claude API with web_search tool. Returns parsed JSON dict.

    Reliability layers (outermost → innermost):

      1. Fallback model: if `enable_fallback_model` and the primary model
         exhausts all tenacity retries, ONE more attempt with
         CLAUDE_FALLBACK_MODEL. Disable for the corrective fix-prompt
         retry where keeping the same model matters more than availability.

      2. tenacity: 5 attempts on each model with exponential backoff +
         full jitter, retrying on transient network / server errors.

      3. Streaming context manager: SDK-required for our max_tokens range.

    max_tokens raised from 32000 to 48000 (Sub-step 2a-2 deploy) to accommodate
    the 4-language narrative output. Sonnet 4.5's hard cap is 64000 output
    tokens — 48000 keeps a safety margin while fitting 4 × ~700-word narratives
    (~10-12K tokens) plus all _ja/_zh sibling fields (headline/summary/
    bottom_line/fact_check/forward_calendar) and web_search overhead.
    """
    import anthropic
    import httpx
    from tenacity import (
        Retrying,
        RetryError,
        stop_after_attempt,
        wait_random_exponential,
        retry_if_exception_type,
        retry_if_exception,
        retry_any,
        before_sleep_log,
    )
    import logging

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

    # Exception classes that ALWAYS mean transient. mid-stream
    # RemoteProtocolError lives here — that's the 5/27 kr-open root cause.
    transient_exc_types = (
        anthropic.APIConnectionError,
        anthropic.APITimeoutError,
        anthropic.InternalServerError,
        anthropic.RateLimitError,
        httpx.RemoteProtocolError,
        httpx.ReadTimeout,
        httpx.ConnectTimeout,
        httpx.ReadError,
        httpx.WriteError,
        httpx.PoolTimeout,
    )

    log = logging.getLogger("call_claude")
    if not log.handlers:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    def _try_model(target_model: str, attempts: int):
        """Run up to `attempts` retries against `target_model`."""
        print(f"[claude] calling {target_model} with {max_tokens=}, "
              f"web_search enabled (max_uses=25) [streaming, max {attempts} attempts]")
        t0 = time.time()
        retryer = Retrying(
            reraise=True,
            stop=stop_after_attempt(attempts),
            # Full jitter exponential backoff. min=4s so the first retry
            # isn't instant (gives server time to recover from overload).
            # max=120s caps individual wait so total wall time stays bounded.
            wait=wait_random_exponential(multiplier=2, min=4, max=120),
            retry=retry_any(
                retry_if_exception_type(transient_exc_types),
                retry_if_exception(_is_retryable_status),
            ),
            before_sleep=before_sleep_log(log, logging.WARNING),
        )
        for attempt in retryer:
            with attempt:
                resp = _claude_one_attempt(
                    client, target_model, max_tokens, tools, messages,
                )
        dt = time.time() - t0
        print(f"[claude] response from {target_model} in {dt:.1f}s — stop_reason={resp.stop_reason}")
        return resp

    try:
        resp = _try_model(model, attempts=5)
    except Exception as primary_err:
        # All 5 primary-model retries exhausted. Last-chance fallback.
        if not enable_fallback_model:
            raise
        print(f"::warning::[claude] primary model {model} failed after 5 retries: "
              f"{type(primary_err).__name__}: {primary_err}")
        print(f"::warning::[claude] attempting fallback model {CLAUDE_FALLBACK_MODEL} (1 try, 2 retries)")
        try:
            resp = _try_model(CLAUDE_FALLBACK_MODEL, attempts=3)
            print(f"::warning::[claude] fallback model succeeded — content quality may be lower than primary")
        except Exception as fallback_err:
            # Both models exhausted. Re-raise the primary error since it's
            # what the operator's diagnostic mental model expects.
            print(f"::error::[claude] fallback model also failed: "
                  f"{type(fallback_err).__name__}: {fallback_err}")
            raise primary_err

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
# Degraded fallback — used ONLY when both primary AND fallback Claude
# models exhaust all retries. Returns a `data` dict shaped like Claude's
# normal output, but built from verified yfinance numbers + honest
# "AI commentary unavailable" notices. The rest of the publish pipeline
# (render_html, write_post_files, posts.js update, sitemap update, git
# push) consumes this dict normally — readers still get the verified
# market data, just without the narrative analysis layer.
#
# Per operator constraint: "신규 업데이트가 유저에게 안 보이는 것은
# 절대 안 됨" — zero publish is unacceptable. A stripped-down post is
# always strictly better than a missing slot.
# ---------------------------------------------------------------------------

# Localized labels used in degraded posts. Kept in module scope (not inside
# the function) so they're easy to tweak without rebuilding the function.
_DEGRADED_LABELS = {
    "ko": {
        "headline_prefix": "[데이터 요약]",
        "headline_suffix": "— AI 분석 일시 중단",
        "summary": "AI 분석 시스템이 일시적으로 응답하지 않아, 검증된 시장 데이터(Yahoo Finance API)만 요약해 발행합니다. 정상 분석은 다음 슬롯에서 복귀합니다.",
        "notice_title": "안내",
        "notice_body": "이 글은 AI 분석 시스템이 일시적으로 응답하지 않아 자동으로 발행된 <strong>데이터 요약본</strong>입니다. 모든 가격·등락률은 Yahoo Finance API 에서 직접 가져온 검증된 값이며, AI 가 만든 해설·전망은 포함하지 않습니다. 다음 정기 슬롯에서 정상 분석으로 복귀합니다.",
        "numbers_title": "검증된 주요 시장 데이터",
        "bottom_line": "이 슬롯은 데이터 요약본으로 발행되었습니다. AI 분석은 다음 정기 발행 시각에 복귀합니다.",
        "fact_check": "본 글의 모든 숫자는 Yahoo Finance API 직접 fetch 기반입니다. AI 자동 분석 시스템이 일시 응답 불가 상태였기 때문에 해설·전망 없이 데이터만 발행되었습니다.",
        "change_label": "등락률",
        "close_label": "종가",
    },
    "en": {
        "headline_prefix": "[Data Summary]",
        "headline_suffix": "— AI commentary temporarily unavailable",
        "summary": "Our AI analysis system is temporarily unavailable. This post contains only verified market data (Yahoo Finance API). Full commentary returns at the next regular slot.",
        "notice_title": "Notice",
        "notice_body": "This post was published automatically as a <strong>data-only summary</strong> because the AI analysis system was temporarily unresponsive. All prices and percentage changes were fetched directly from the Yahoo Finance API and are verified; no AI-generated commentary or forecast is included. Full analysis resumes at the next scheduled slot.",
        "numbers_title": "Verified market data",
        "bottom_line": "This slot was published as a data-only summary. Full AI analysis resumes at the next scheduled slot.",
        "fact_check": "Every number in this post comes from a direct Yahoo Finance API fetch. AI commentary was skipped because the analysis system was temporarily unresponsive.",
        "change_label": "Change",
        "close_label": "Close",
    },
    "ja": {
        "headline_prefix": "[データサマリー]",
        "headline_suffix": "— AI 解説一時停止中",
        "summary": "AI 分析システムが一時的に応答できないため、検証済みの市場データ(Yahoo Finance API)のみを掲載しています。通常解説は次回のスロットで復帰します。",
        "notice_title": "お知らせ",
        "notice_body": "AI 分析システムが一時的に応答しなかったため、<strong>データのみの要約</strong>として自動発行しました。すべての価格・騰落率は Yahoo Finance API から直接取得した検証済みの値です。AI 解説・予想は含まれていません。次回の定期スロットで通常解説に戻ります。",
        "numbers_title": "検証済みの主要市場データ",
        "bottom_line": "本スロットはデータのみの要約として発行されました。AI 解説は次回の定期スロットで復帰します。",
        "fact_check": "本記事の全ての数字は Yahoo Finance API から直接取得しています。AI 自動解説システムが一時的に応答できなかったため、解説・予想なしでデータのみを掲載しました。",
        "change_label": "騰落率",
        "close_label": "終値",
    },
    "zh": {
        "headline_prefix": "[数据摘要]",
        "headline_suffix": "— AI 解读暂时不可用",
        "summary": "AI 分析系统暂时无法响应,本文仅刊载经验证的市场数据 (Yahoo Finance API)。完整解读将在下一时段恢复。",
        "notice_title": "提示",
        "notice_body": "由于 AI 分析系统暂时无响应,本文以<strong>仅数据摘要</strong>形式自动发布。所有价格与涨跌幅均直接取自 Yahoo Finance API,数据真实可验证;不包含任何 AI 生成的解读或预测。下一时段将恢复完整分析。",
        "numbers_title": "经验证的关键市场数据",
        "bottom_line": "本时段以仅数据摘要形式发布。AI 完整分析将在下一定时时段恢复。",
        "fact_check": "本文所有数据均来自 Yahoo Finance API 的直接抓取。由于 AI 自动解读系统暂时无响应,本次发布省略了解读与展望,仅刊载数据。",
        "change_label": "涨跌幅",
        "close_label": "收盘价",
    },
}


def build_degraded_data(slot: str, trading_date: str, publish_date: str, market_data: dict) -> dict:
    """Construct a minimal `data` dict from verified market_data only.

    Output shape mimics what Claude normally returns, but with:
      - headline / summary / bottom_line in 4 languages explaining the
        degraded mode honestly
      - narrative_html_* containing a brief notice + a verified-numbers list
      - key_metrics mapped from the 7-asset COMMON_TOP7 fetch
      - indices populated from the relevant slot's index group
      - skip=False (we want to publish)
      - _degraded=True (internal flag — callers can detect to skip validation)

    All other fields (themes, news, winners, losers, kr_indices, cn_indices,
    forward_calendar_html, etc.) are intentionally omitted. The existing
    render helpers all return "" when given empty/missing input, so the
    final post is clean: just a notice + key metrics strip + numbers list.
    """
    cfg = SLOTS[slot]

    # Map COMMON_TOP7 to the key_metrics shape the renderer expects.
    # Renderer reads: key_metrics.{usdkrw,gold,silver,wti,btc,eth,xrp} each
    # with {value, change_pct}.
    km_keymap = {
        "USD/KRW": "usdkrw", "Gold": "gold", "Silver": "silver", "WTI": "wti",
        "BTC": "btc", "ETH": "eth", "XRP": "xrp",
    }
    key_metrics = {}
    for ticker_label, km_key in km_keymap.items():
        v = market_data.get(ticker_label)
        if isinstance(v, dict):
            key_metrics[km_key] = {
                "value": v.get("close", "—"),
                "change_pct": v.get("change_pct", 0.0),
            }

    # Indices snapshot — pick the 6 most relevant for this slot from the
    # already-fetched market_data. Visual cards render cleanly even with
    # fewer than 6, so we just include whatever fetched successfully.
    slot_idx_priority = {
        "us-close":     ["S&P 500", "Nasdaq Composite", "Dow Jones", "Philadelphia Semi (SOX)", "VIX", "10Y Treasury Yield"],
        "us-premarket": ["S&P 500", "Nasdaq Composite", "Dow Jones", "Philadelphia Semi (SOX)", "10Y Treasury Yield", "VIX"],
        "kr-open":      ["KOSPI", "KOSDAQ", "S&P 500", "Nasdaq Composite", "Philadelphia Semi (SOX)", "USD/KRW"],
        "kr-close":     ["KOSPI", "KOSDAQ", "KOSPI 200", "Nasdaq Composite", "Philadelphia Semi (SOX)", "USD/KRW"],
        "cn-open":      ["Hang Seng (恒生指数)", "Hang Seng Tech (恒生科技)", "S&P 500", "Nasdaq Composite", "CSI 300 (沪深300)", "SSE Composite (上证综指)"],
        "cn-close":     ["SSE Composite (上证综指)", "Shenzhen Component (深证成指)", "CSI 300 (沪深300)", "Hang Seng (恒生指数)", "Hang Seng Tech (恒生科技)", "ChiNext (创业板指)"],
    }
    indices = []
    for name in slot_idx_priority.get(slot, [])[:6]:
        v = market_data.get(name)
        if not isinstance(v, dict):
            continue
        indices.append({
            "name": name,
            "value": v.get("close", "—"),
            "change_pct": v.get("change_pct", 0.0),
            "tag": "",
        })

    def _build_numbers_html(lang: str, labels: dict) -> str:
        """Plain HTML list of every verified ticker, for the narrative body.

        Defensive: if market_data is empty, we still emit a sensible page
        with just the notice + a 'no data fetched' line.
        """
        if not market_data:
            return (f"<div class=\"tldr-box\">"
                    f"<h3>{labels['notice_title']}</h3>"
                    f"<p>{labels['notice_body']}</p>"
                    f"</div>")
        rows = []
        # Group order matches format_market_data_for_prompt for consistency
        groups_by_lang = [
            ("Top 7 fixed assets", list(_COMMON_TOP7.keys())),
            ("US indices & macro", list(_US_INDICES.keys())),
            ("Mag 7 stocks", list(_MAG7.keys())),
            ("US sector ETFs", list(_US_SECTOR_ETFS.keys())),
            ("KR indices", list(_KR_INDICES.keys())),
            ("KR stocks", list(_KR_STOCKS.keys())),
            ("CN indices", list(_CN_INDICES.keys())),
            ("CN tech / consumer", list(_CN_STOCKS.keys())),
        ]
        for group_name, keys in groups_by_lang:
            group_rows = []
            for k in keys:
                v = market_data.get(k)
                if not isinstance(v, dict):
                    continue
                chg = v.get("change_pct", 0.0)
                try:
                    chg_f = float(chg)
                except Exception:
                    chg_f = 0.0
                sign = "+" if chg_f >= 0 else ""
                cls = "upx" if chg_f > 0 else ("dn" if chg_f < 0 else "")
                close_val = v.get("close", "—")
                group_rows.append(
                    f"<li><strong>{html_escape(k)}</strong> · "
                    f"{labels['close_label']} <code>{html_escape(str(close_val))}</code> · "
                    f"{labels['change_label']} <span class=\"{cls}\">{sign}{chg_f:.2f}%</span></li>"
                )
            if group_rows:
                rows.append(f"<h3>{html_escape(group_name)}</h3><ul>{''.join(group_rows)}</ul>")
        if not rows:
            return (f"<div class=\"tldr-box\">"
                    f"<h3>{labels['notice_title']}</h3>"
                    f"<p>{labels['notice_body']}</p>"
                    f"</div>")
        body = (
            f"<div class=\"tldr-box\">"
            f"<h3>{labels['notice_title']}</h3>"
            f"<p>{labels['notice_body']}</p>"
            f"</div>"
            f"<h2>{labels['numbers_title']}</h2>"
            + "".join(rows)
        )
        return body

    data = {
        "skip": False,
        "_degraded": True,
        "key_metrics": key_metrics,
        "indices": indices,
        # All other list fields intentionally left empty/absent — the
        # render helpers gracefully omit their sections when missing.
    }

    for lang in LANGS:
        labels = _DEGRADED_LABELS[lang]
        header_label = cfg.get(f"header_label_{lang}", cfg.get("header_label_en", slot))
        data[f"headline_{lang}"] = f"{labels['headline_prefix']} {trading_date} {header_label} {labels['headline_suffix']}"
        data[f"summary_{lang}"] = labels["summary"]
        data[f"bottom_line_{lang}"] = labels["bottom_line"]
        data[f"narrative_html_{lang}"] = _build_numbers_html(lang, labels)
        data[f"fact_check_{lang}"] = labels["fact_check"]
        # forward_calendar_html intentionally empty — the renderer drops the
        # section cleanly when content is empty.
        data[f"forward_calendar_html_{lang}"] = ""

    return data


# ---------------------------------------------------------------------------
# External notifications — Healthchecks.io dead-man-switch + Discord webhook
# ---------------------------------------------------------------------------
# Both are CONFIG-FREE BY DEFAULT: if the corresponding env var is empty,
# the call silently no-ops. The operator can wire these in incrementally by
# (a) creating 6 checks on Healthchecks.io and setting HC_URL_<SLOT>
# secrets in the GitHub repo, then (b) creating a Discord channel + webhook
# and setting DISCORD_WEBHOOK_URL.
#
# Why this split:
#   - Healthchecks is the out-of-band dead-man-switch. It pings success or
#     /fail per slot; if a slot never pings before its deadline, HC fires
#     an alert via its own integrations (Discord/email/Slack/ntfy etc.).
#     This survives even a complete GitHub Actions outage, because HC is
#     a separate service entirely. The 5/27 kr-open delay would have been
#     caught here within minutes instead of a few hours.
#   - Discord direct webhook is for IMMEDIATE inline alerts on degraded
#     and failure events, without waiting for HC's grace period. We don't
#     spam on plain success (too noisy for a 6-times-a-day cron).
#
# Both helpers are best-effort: any network failure inside them is logged
# but never propagated, because notification infrastructure must NEVER be
# allowed to break the actual publish pipeline.


def notify_healthcheck(slot: str, status: str, summary: str = "") -> None:
    """Ping Healthchecks.io for `slot` with the given status.

    Env var convention: `HC_URL_US_CLOSE` for slot `us-close`, etc. The
    URL is the full hc-ping.com endpoint copied from the Healthchecks
    dashboard for that check.

    status:
      'success'  — ping the bare URL (HC marks the check as healthy)
      'failed'   — ping URL/fail (HC fires its configured alert chain)
      'start'    — ping URL/start (HC records run start; useful for
                    measuring run duration on the dashboard)

    summary: optional UTF-8 text body. When non-empty, the ping is POSTed
    with this body so HC stores it in the run log — the operator can read
    "why did slot X fail today" from the HC dashboard without opening
    GitHub Actions logs.
    """
    import os
    slot_env = "HC_URL_" + slot.upper().replace("-", "_")
    base_url = os.environ.get(slot_env, "").strip()
    if not base_url:
        return  # not configured — silent no-op by design
    url = base_url.rstrip("/")
    if status == "failed":
        url = url + "/fail"
    elif status == "start":
        url = url + "/start"
    try:
        import urllib.request
        if summary:
            req = urllib.request.Request(
                url,
                data=summary.encode("utf-8", errors="replace"),
                headers={"Content-Type": "text/plain; charset=utf-8"},
                method="POST",
            )
        else:
            req = urllib.request.Request(url, method="GET")
        # 5s timeout — pings must NEVER stall the cron. If HC is itself
        # down, we want to skip and continue, not block the publish.
        urllib.request.urlopen(req, timeout=5).read()
        print(f"[notify] healthcheck ping sent: slot={slot} status={status}")
    except Exception as e:
        # Best-effort. Never propagate notification failures.
        print(f"[notify] healthcheck ping failed (non-fatal): "
              f"{type(e).__name__}: {e}")


# Discord embed colors (RGB int form, as Discord's API expects).
DISCORD_COLOR_GREEN  = 0x57F287   # normal success — currently unused (no-spam policy)
DISCORD_COLOR_YELLOW = 0xFEE75C   # degraded (publish OK but downgraded)
DISCORD_COLOR_RED    = 0xED4245   # failure (no publish)


def notify_discord(title: str, body: str, color: int = DISCORD_COLOR_RED) -> None:
    """Send a Discord webhook embed. Best-effort — never raises.

    Reads DISCORD_WEBHOOK_URL from env. Silent no-op if empty.

    Discord embed limits: title 256 chars, description 4096 chars. We
    truncate defensively so a long Python traceback never breaks delivery.
    """
    import os
    url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        return
    try:
        import json as _json
        import urllib.request
        payload = {
            "username": "luckyplz cron",
            "embeds": [{
                "title": (title or "")[:256],
                "description": (body or "")[:4000],
                "color": color,
            }],
        }
        req = urllib.request.Request(
            url,
            data=_json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5).read()
        print(f"[notify] discord webhook sent: {title[:60]}")
    except Exception as e:
        print(f"[notify] discord webhook failed (non-fatal): "
              f"{type(e).__name__}: {e}")


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
        tag = n.get(f"tag_{lang}") or n.get("tag_en") or n.get("tag") or ""
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


def render_watch(watch: dict, lang: str, ref_date: str = "") -> str:
    """Render the forward "this week's key events" watchlist.

    The weekday labels (화/수/목 …) are computed from the post's trading date
    (`ref_date`, YYYY-MM-DD) — NEVER hardcoded. Previously the labels were a
    static "화 5/12 / 수 5/13 / 목 5/14" baked in at template-authoring time,
    so every post since mid-May showed wrong May dates regardless of the actual
    publish date — a serious credibility bug. Now each weekday slot resolves to
    the next occurrence of that weekday strictly AFTER the trading date, e.g. a
    Friday-close post → Tue/Wed/Thu of the upcoming week. Labels localized 4-lang.
    NOTE: the prompt is instructed to keep dates OUT of the body text so the only
    date shown is this computed, always-correct one."""
    if not watch:
        return ""
    # weekday slots: key -> (Mon=0..Sun=6 index, localized weekday abbreviation)
    wd_slots = {
        "tue": (1, {"ko": "화", "en": "TUE", "ja": "火", "zh": "周二"}),
        "wed": (2, {"ko": "수", "en": "WED", "ja": "水", "zh": "周三"}),
        "thu": (3, {"ko": "목", "en": "THU", "ja": "木", "zh": "周四"}),
    }
    non_day = {
        "risk": {"ko": "리스크", "en": "RISK", "ja": "リスク", "zh": "风险"},
        "flow": {"ko": "플로우", "en": "FLOW", "ja": "フロー", "zh": "资金"},
    }
    base = None
    if ref_date:
        try:
            base = datetime.strptime(str(ref_date)[:10], "%Y-%m-%d")
        except Exception:
            base = None
    rows = []
    for key in ("tue", "wed", "thu", "risk", "flow"):
        body = watch.get(f"{key}_{lang}")
        if not body:
            continue
        if key in wd_slots:
            wd, names = wd_slots[key]
            label = names.get(lang, names["en"])
            if base is not None:
                d = base + timedelta(days=((wd - base.weekday() - 1) % 7) + 1)
                label = f"{label} {d.month}/{d.day}"
        else:
            label = non_day[key].get(lang, non_day[key]["en"])
        rows.append(f"""
  <div class="watch-row">
    <div class="watch-day">{html_escape(label)}</div>
    <div class="watch-body">{body}</div>
  </div>""")
    if not rows:
        return ""
    title = L(lang, ko="▸ 이번 주 워치리스트", en="▸ This Week's Watchlist",
              ja="▸ 今週のウォッチリスト", zh="▸ 本周观察清单")
    h3 = L(lang, ko="📅 이번 주 핵심 어닝 · 이벤트", en="📅 KEY EARNINGS · EVENTS · THIS WEEK",
           ja="📅 今週の主要決算・イベント", zh="📅 本周核心财报 · 事件")
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


def render_sections(slot: str, data: dict, lang: str, ref_date: str = "") -> str:
    """Stitch the body sections based on slot type."""
    parts = []
    if slot == "us-close":
        parts.append(render_indices_block(data.get("indices", []), lang))
        parts.append(render_mag7(data.get("mag7", []), lang))
        parts.append(render_themes(data.get("themes", []), lang))
        parts.append(render_movers(data.get("winners", []), lang, "winners"))
        parts.append(render_movers(data.get("losers", []), lang, "losers"))
        parts.append(render_news(data.get("news", []), lang))
        parts.append(render_watch(data.get("watch", {}), lang, ref_date))
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
    title_full = f"{title} | Lucky Blog"
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
        "author": {"@type": "Organization", "name": "Lucky Blog", "url": "https://luckyplz.com/"},
        "publisher": {"@type": "Organization", "name": "Lucky Blog",
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
    cards = render_sections(slot, data, lang, trading_date)
    forward_cal = render_forward_calendar(pick_localized(data, "forward_calendar_html", lang), lang)
    fact_check_box = render_fact_check(pick_localized(data, "fact_check", lang), lang)
    # Order: 7-asset strip (fixed top) → deep narrative (main) → visual cards
    # (supplementary) → forward calendar → fact-check (closing).
    # Order: hook (summary-card, above) → glanceable DATA snapshot (cards) →
    # deep-analysis narrative (synthesis) → forward calendar → fact-check.
    # Leading with the visual data and following with the written synthesis
    # reads better than dropping a ~700-word wall right under the metrics strip.
    sections_html = "\n".join(p for p in [key_strip, cards, narrative, forward_cal, fact_check_box] if p)

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
        "{{SNAPSHOT_NOTE}}": snapshot_note(slot, lang, publish_date),
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


# Live-quote landing per market for the snapshot note's "see live price" link.
# Google Finance index pages are stable and cover all three markets.
SNAPSHOT_LIVE_URL = {
    "us": "https://www.google.com/finance/quote/.INX:INDEXSP",   # S&P 500
    "kr": "https://www.google.com/finance/quote/KOSPI:KRX",       # KOSPI
    "cn": "https://www.google.com/finance/quote/000001:SHA",      # SSE Composite
}


def snapshot_note(slot: str, lang: str, publish_date: str) -> str:
    """The '기준 시점 스냅샷' badge under the disclaimer.

    Daily prices are baked at publish time and never change afterwards. For
    CLOSE recaps that is definitionally correct (the session is over). For
    OPEN / PRE-MARKET briefs the snapshot is mid-flight, so those add a
    'see live price' link to the market's index — never overwriting the
    article's own numbers (the prose interprets them; a live value would
    contradict the text). Mirrors scripts/inject-snapshot-note.py for
    existing posts — keep the two in sync.
    """
    market = "us" if slot.startswith("us") else "kr" if slot.startswith("kr") else "cn"
    intraday = slot in ("kr-open", "cn-open", "us-premarket")
    note = L(
        lang,
        ko=f'이 글의 수치는 <b>{publish_date} 발행 시점</b>에 고정된 스냅샷입니다. 실시간 시세가 아닙니다.',
        en=f'These figures are a snapshot fixed at publication on <b>{publish_date}</b>. Not a live quote.',
        ja=f'本記事の数値は<b>{publish_date} 公開時点</b>で固定されたスナップショットです。リアルタイム値ではありません。',
        zh=f'本文数据为<b>{publish_date} 发布时点</b>固定的快照，非实时行情。',
    )
    link = ""
    if intraday:
        label = L(lang, ko="실시간 현재가 보기", en="See live price",
                  ja="現在値を見る", zh="查看实时行情")
        link = (f' <a href="{SNAPSHOT_LIVE_URL[market]}" target="_blank" '
                f'rel="noopener">{label} →</a>')
    return f'<div class="snapshot-note">📌 {note}{link}</div>'


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
    """No-op for daily auto-posts (2026-06-11 정책).

    일별 증시·스포츠 자동발행 글은 `noindex,follow` (daily-base.html 에
    baked) 로 검색엔진에서 제외된다 — AdSense scaled-content 리스크 헷지.
    noindex URL 은 sitemap 에 넣지 않는 것이 표준이며 (Google: "don't
    list noindex URLs in your sitemap"), 넣으면 Search Console 에
    "Submitted URL marked noindex" 경고만 쌓인다. 그래서 일별 글은
    sitemap 에 등록하지 않는다. durable SEO 는 주간 통합 리캡(별도 색인)
    에 집중. 과거에 등록됐던 일별 블록은 scripts/noindex-daily-autoposts.py
    가 일괄 제거했다.
    """
    print(f"[sitemap] skip {slug} (noindex daily auto-post — not listed)")


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
                        "Bypasses the DUPLICATE-PUBLISH guard only — does NOT "
                        "bypass weekend or holiday guards. Use this when you "
                        "want to overwrite an existing post (e.g., re-run after "
                        "a bad publish).")
    p.add_argument("--bypass-holiday-guard", action="store_true",
                   help="Skip the exchange-holiday check. Use ONLY for the rare "
                        "manual case where you want to publish a thematic essay "
                        "on a market-closed weekday. Weekend (Sat/Sun) is NEVER "
                        "bypassable — there is no legitimate reason to publish a "
                        "'trading-day recap' for a weekend.")
    p.add_argument("--check-only", action="store_true",
                   help="Run the trading-day guards only and exit. "
                        "Exit code 0 = would publish, 1 = would skip. "
                        "Used by cron-monitor to gate rescue triggers.")
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

    # === TIER 0 — WEEKEND GUARD (UNCONDITIONAL) ===
    # Markets globally are closed Sat/Sun. There is NO legitimate reason
    # to publish a "trading-day recap" for a weekend. This check is
    # OUTSIDE every flag (--force, --bypass-holiday-guard) by design.
    # Lesson from 2026-05-30/31: when the guard is tied to a bypass flag,
    # automation paths (cron-monitor rescue, retry loops) can silently
    # set that flag and ship weekend posts. Weekend skip is now ALWAYS.
    try:
        weekend, day_name = is_weekend(trading_date)
    except ValueError:
        print(f"[guard] invalid trading_date format: {trading_date}. Aborting.")
        notify_healthcheck(args.slot, "fail",
                           summary=f"guard-error: invalid date {trading_date}")
        return
    if weekend:
        print(f"[guard] tier-0 WEEKEND: trading_date {trading_date} is {day_name}. "
              f"Skipping unconditionally (no flag can bypass this).")
        notify_healthcheck(
            args.slot, "success",
            summary=f"weekend-skip: {trading_date} ({day_name})",
        )
        if args.check_only:
            sys.exit(1)
        return

    # === TIER 1 — EXCHANGE HOLIDAY GUARD (bypassable by --bypass-holiday-guard) ===
    # User report 2026-05-23: hallucinated holiday content. Now uses the
    # authoritative exchange_calendars library. Hard-fails (skips) on
    # library/lookup error — was previously "default to open" which
    # masked a real failure mode.
    market = SLOT_TO_MARKET.get(args.slot)
    if market and not args.bypass_holiday_guard:
        try:
            holiday, reason = is_exchange_holiday(trading_date, market)
        except ImportError:
            print(f"[guard] tier-1 exchange_calendars NOT INSTALLED — refusing to "
                  f"publish on uncertain holiday status. Use --bypass-holiday-guard "
                  f"to override (only if you know markets are open).")
            notify_healthcheck(args.slot, "fail",
                               summary="guard-error: exchange_calendars missing")
            if args.check_only:
                sys.exit(1)
            return
        except Exception as e:
            err_type = type(e).__name__
            err_msg = str(e)[:200]
            print(f"[guard] tier-1 {market} calendar lookup FAILED "
                  f"({err_type}: {err_msg}). Refusing to publish on uncertain "
                  f"holiday status. Likely an outdated exchange-calendars pin — "
                  f"bump >= 4.10 in requirements.txt. Use --bypass-holiday-guard "
                  f"to override.")
            notify_healthcheck(args.slot, "fail",
                               summary=f"guard-error: {market} lookup {err_type}")
            if args.check_only:
                sys.exit(1)
            return
        if holiday:
            print(f"[guard] tier-1 HOLIDAY: {market} closed on {trading_date} ({reason}). "
                  f"Skipping cleanly.")
            notify_healthcheck(
                args.slot, "success",
                summary=f"holiday-skip: {market} closed on {trading_date}",
            )
            if args.check_only:
                sys.exit(1)
            return
        print(f"[guard] tier-1 {market} open on {trading_date} ({reason}). Proceeding.")
    elif market and args.bypass_holiday_guard:
        print(f"[guard] ⚠️ --bypass-holiday-guard set — skipping holiday check "
              f"for {market} on {trading_date}. Tier-0 weekend already passed.")

    # If --check-only was set and we got here, the date IS a trading day.
    if args.check_only:
        print(f"[check-only] {args.slot} trading_date={trading_date} would publish (open).")
        sys.exit(0)

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
            # Ping HC success because the slot IS published (just by a
            # different cron run). Without this, an HC auto-recovery
            # workflow_dispatch that lands on already-published slug
            # would never ping → HC keeps thinking it's down → false
            # alarms / repeated webhook fires. This was the 2026-05-27
            # gap that left us-premarket as `status: new` after manual
            # recovery: HC needs at least one successful ping to leave
            # `new` and start the proper up/down alerting cycle.
            notify_healthcheck(
                args.slot, "success",
                summary=f"duplicate-skip: {slug} already on main",
            )
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

    # Shared WRITING-QUALITY guide — appended to EVERY slot. The biggest lever on
    # perceived quality is prose: specific over generic, lead with the point,
    # varied rhythm, no filler. Applies to narrative_html_*, summary_*,
    # bottom_line_*, and every trigger/catalyst/news sentence.
    writing_guide = (
        "\n\n---\n"
        "# WRITING QUALITY — applies to ALL prose (narrative, summary, bottom_line, news, triggers)\n\n"
        "Write like a sharp, trusted market columnist whose readers forward the piece. Concretely:\n"
        "1. LEAD WITH THE POINT. Each paragraph's first sentence states its one conclusion; the rest supports it. No throat-clearing ('오늘 시장은…').\n"
        "2. SPECIFIC OVER GENERIC. Name the catalyst, the number, the mechanism. BANNED filler — never write: '혼조세', '투자자들은 주목', '불확실성이 커지고 있다', '관망세', 'remains to be seen', 'mixed signals'. Replace each with a concrete cause -> effect.\n"
        "3. NUMBERS DO THE WORK. Tie every claim to a figure (%/$/bp/배수) AND say what it MEANS, not just what it is.\n"
        "4. VARY RHYTHM. Do not end three sentences in a row the same way (…했다 / …이다 / …것이다). Mix short punches with longer explanatory lines.\n"
        "5. ONE IDEA PER PARAGRAPH, 2-4 sentences. If a paragraph carries two ideas, split it.\n"
        "6. EARN A VERDICT. State a clear bias (강세/약세/중립) and the single thing that would flip it. No fence-sitting.\n"
        "7. MAKE IT MATTER TO THE READER. Map every major move to a specific local sector/ticker and a concrete 'so what'.\n"
        "8. NO AI TELLS, no self-reference, no repeated hedging ('~로 보입니다'). Confident, human, grounded strictly in the data provided (never invent numbers).\n"
        "Tone: serious but readable — neither dry wire-copy nor hype. Every sentence must inform or advance the argument; cut the rest.\n"
    )
    prompt = prompt + writing_guide

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

    # Call Claude — with degraded last-resort fallback. The retry layer +
    # fallback model inside call_claude already absorb mid-stream drops,
    # 529 overload, network blips, and partial-Anthropic outages. If even
    # the fallback model fails (rare — would require both Sonnet 4.5 and
    # Sonnet 4 to be unavailable simultaneously OR a sustained network
    # partition), we publish a data-only summary built from the verified
    # yfinance fetch. Per operator constraint, zero publish is unacceptable.
    degraded = False
    try:
        data = call_claude(prompt, model=args.model)
    except Exception as claude_err:
        print(f"::error::[claude] all retries + fallback model exhausted: "
              f"{type(claude_err).__name__}: {claude_err}")
        print(f"::warning::[degraded] entering degraded publish mode for "
              f"{args.slot} {trading_date} — data-only summary from yfinance values")
        data = build_degraded_data(args.slot, trading_date, publish_date, market_data)
        degraded = True

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
        reason = data.get('reason','holiday or no session')
        print(f"[skip] {reason}. Exiting.")
        # Claude declared skip (typically: Sunday market closed, partial
        # holiday Claude detected via web_search, etc.). Treat as a clean
        # success for monitoring purposes — same rationale as the
        # weekday-holiday gate above.
        notify_healthcheck(
            args.slot, "success",
            summary=f"claude-skip: {reason}",
        )
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

    # === ACCURACY DOUBLE-CHECK (option D: tiered with retry + block) ===
    # 1. Run validate_narrative_numbers and classify severity:
    #    - clean        → publish immediately
    #    - minor        → publish + ::warning:: in GitHub Actions log
    #    - catastrophic → call Claude one more time with a corrective
    #                     fix prompt, re-validate; if still catastrophic
    #                     after retry, BLOCK the publish entirely
    #
    # Blocking means: no HTML files written, no posts.js / sitemap update,
    # no git push. The cron job exits with status 1 so GitHub Actions
    # marks it as failed → operator gets an email + the slot is missing
    # from the site, which is the user's explicit preference vs publishing
    # a wrong number ("잘못 작성된 내용이 posting되면 어떻게해").
    #
    # Wrapped in try/except so a bug in the validator itself NEVER
    # cascades into blocking a publish — validator errors degrade to
    # plain publish + warning.
    # Degraded data is constructed directly from verified market_data so its
    # narrative is by definition consistent with verified numbers — there's
    # nothing to validate. Skip the whole tiered-validation block. We still
    # surface a CI warning so the operator notices the slot ran degraded.
    if degraded:
        print(f"::warning::[validate] skipped — slot {args.slot} {trading_date} "
              f"was published in DEGRADED mode (Claude unavailable). "
              f"Numbers are from yfinance directly; no narrative to validate.")
    else:
        try:
            v = validate_narrative_numbers(data, market_data, args.slot)
            print(f"[validate] severity={v['severity']} count={v['count']} max_diff={v['max_diff']:.2f}%p")

            if v["severity"] == "catastrophic":
                print(f"::warning::[validate] catastrophic mismatch — issuing corrective retry...")
                for w in v["warnings"]:
                    print(f"::warning::  pre-retry: {w}")

                # One corrective Claude call. Same full prompt (VERIFIED MARKET
                # DATA + OPERATING CONTEXT + slot rules + web_search tool) with
                # a mismatch list appended at the end. We rebuild the prompt
                # from the same pieces used the first time around.
                try:
                    fix_prompt = build_fix_prompt(prompt, v)
                    data2 = call_claude(fix_prompt, model=args.model)
                    # Same post-processing as the first response: pct normalization
                    # + skip guard. If retry says skip, treat as a failure: we
                    # already passed the holiday gate so a skip here is suspicious.
                    # Walk asset shapes the same way as the original normalization.
                    for key in ("indices", "mag7", "themes", "winners", "losers",
                                "kr_indices", "kr_themes", "cn_indices", "cn_themes",
                                "overnight_us", "gap_watch", "futures",
                                "foreign_flow", "institution_flow",
                                "northbound_flow", "southbound_flow",
                                "kr_news", "cn_news", "news"):
                        items = data2.get(key)
                        if isinstance(items, list):
                            for it in items:
                                _normalize_pct(it)
                        elif isinstance(items, dict):
                            for it in items.values():
                                if isinstance(it, list):
                                    for ii in it:
                                        _normalize_pct(ii)
                                elif isinstance(it, dict):
                                    _normalize_pct(it)
                    pm = data2.get("premarket_movers", {})
                    if isinstance(pm, dict):
                        for side in ("winners", "losers"):
                            for it in pm.get(side, []) or []:
                                _normalize_pct(it)
                    key_metrics = data2.get("key_metrics", {})
                    if isinstance(key_metrics, dict):
                        for asset_data in key_metrics.values():
                            if isinstance(asset_data, dict):
                                _normalize_pct(asset_data)

                    if data2.get("skip"):
                        raise RuntimeError(f"retry returned skip=true: {data2.get('reason','no reason')}")

                    v2 = validate_narrative_numbers(data2, market_data, args.slot)
                    print(f"[validate-retry] severity={v2['severity']} count={v2['count']} max_diff={v2['max_diff']:.2f}%p")

                    if v2["severity"] == "catastrophic":
                        # Both attempts failed. Refuse to publish.
                        print(f"::error::[validate] CATASTROPHIC mismatch PERSISTS after retry — BLOCKING publish for {slug}")
                        for w in v2["warnings"]:
                            print(f"::error::  {w}")
                        print(f"::error::Operator action required: review {slug}, fix prompt or yfinance fetch, then re-run with --force")
                        raise SystemExit(1)

                    # Retry succeeded (clean or minor). Use the retry data.
                    print(f"[validate-retry] retry succeeded — using corrected response")
                    data = data2
                    v = v2
                    # Re-render HTML with the corrected data (the first render
                    # used the bad data; throw it away and redo).
                    htmls = {}
                    for lang in publish_langs:
                        try:
                            htmls[lang] = render_html(
                                args.slot, lang, data, slug=slug, build=build,
                                og_image_filename=og_filenames[lang],
                                trading_date=trading_date, publish_date=publish_date,
                            )
                        except Exception as e:
                            print(f"[render-retry] {lang} failed: {type(e).__name__}: {e}")
                            if lang in ("ko", "en"):
                                raise
                    # Trim again — same pattern as the first pass.
                    publish_langs = [l for l in publish_langs if htmls.get(l)]
                except SystemExit:
                    raise  # do not eat the explicit block
                except Exception as e:
                    # Retry itself crashed. Don't publish bad data — block.
                    print(f"::error::[validate] retry call itself failed: {type(e).__name__}: {e}")
                    print(f"::error::[validate] BLOCKING publish for {slug} because we cannot confirm accuracy")
                    raise SystemExit(1)

            # At this point severity is clean or minor. Surface any remaining
            # warnings (minor) so the operator can spot drift at a glance.
            for w in v.get("warnings", []):
                print(f"::warning::[validate] {w}")
            if v["severity"] == "clean":
                print(f"[validate] all verified-ticker references match yfinance values")
            elif v["severity"] == "minor":
                print(f"[validate] {v['count']} minor mismatch(es) — within tolerance, publishing")
        except SystemExit:
            raise
        except Exception as e:
            # Validator bug. Degrade gracefully — publish anyway with a warning.
            # Never let a validation infrastructure bug block legitimate runs.
            print(f"::warning::[validate] check failed with internal error: {type(e).__name__}: {e} — publishing anyway")

    write_post_files(slug, htmls, og_paths)

    # Site integration — only register languages we actually published.
    update_posts_js(slug, args.slot, data, publish_date, langs=publish_langs)
    update_sitemap(slug, publish_date, langs=publish_langs)

    # Cache + git
    bump_cache()
    git_push(slug, args.slot)
    print(f"[done] {slug}")

    # === SUCCESS NOTIFICATIONS ===
    # Healthchecks: always ping success when we reach this point (whether
    # the publish was normal or degraded). The fact that we ran the entire
    # pipeline to completion is what HC cares about.
    # Discord: silent on plain success (too noisy for 6x/day). Send a
    # yellow warning if this slot was degraded — operator wants to know
    # AI commentary didn't run even though the post landed.
    notify_healthcheck(
        args.slot,
        "success",
        summary=f"{args.slot} {publish_date} {'DEGRADED' if degraded else 'OK'} → {slug}",
    )
    if degraded:
        notify_discord(
            title=f"⚠️ {args.slot} published in DEGRADED mode",
            body=(
                f"Slot **{args.slot}** for **{publish_date}** was published with "
                f"data-only summary (Claude API exhausted both primary and "
                f"fallback model retries).\n\n"
                f"• Slug: `{slug}`\n"
                f"• Trading date: {trading_date}\n"
                f"• Action needed: review the post; consider whether the next "
                f"slot recovers or requires manual republish."
            ),
            color=DISCORD_COLOR_YELLOW,
        )


if __name__ == "__main__":
    # Top-level error envelope. Any uncaught exception (Claude failed past
    # the degraded fallback, git push refused, disk full, anything) gets
    # turned into BOTH a Healthchecks /fail ping AND a Discord red alert
    # before the process exits non-zero. Critical: the env-var-driven
    # helpers are no-ops without secrets, so this is safe to land before
    # the operator wires up the Healthchecks/Discord side.
    import sys as _sys
    import traceback as _tb
    # Best-effort slot extraction so the notification carries useful context
    # even if the exception happened before the normal argparse flow ran
    # to completion.
    _argv_slot = "unknown"
    for i, a in enumerate(_sys.argv):
        if a == "--slot" and i + 1 < len(_sys.argv):
            _argv_slot = _sys.argv[i + 1]
            break
    try:
        main()
    except SystemExit as e:
        # main() raises SystemExit(1) deliberately when the validator
        # blocks a publish. That's a real "no post landed" failure — alert.
        if int(getattr(e, "code", 0) or 0) != 0:
            try:
                notify_healthcheck(_argv_slot, "failed",
                                   summary=f"SystemExit({e.code}) — publish blocked")
                notify_discord(
                    title=f"❌ {_argv_slot} publish BLOCKED",
                    body=(
                        f"The pipeline exited with status **{e.code}**, meaning a "
                        f"validator/guard refused to publish this slot.\n\n"
                        f"Common causes:\n"
                        f"• Catastrophic narrative ↔ verified-data mismatch even after retry\n"
                        f"• Holiday-guard tripped after the gate was passed (rare)\n\n"
                        f"Check the GitHub Actions log for `::error::` lines."
                    ),
                    color=DISCORD_COLOR_RED,
                )
            except Exception:
                pass
        raise
    except BaseException as exc:
        tb_text = _tb.format_exc()
        try:
            notify_healthcheck(
                _argv_slot, "failed",
                summary=(f"{type(exc).__name__}: {exc}\n\n{tb_text}")[:4000],
            )
            notify_discord(
                title=f"❌ {_argv_slot} pipeline crashed",
                body=(
                    f"**{type(exc).__name__}**: `{str(exc)[:300]}`\n\n"
                    f"```\n{tb_text[-1500:]}\n```\n"
                    f"This means even the degraded fallback did not run. "
                    f"The slot will be missing from the site until you "
                    f"`gh workflow run daily-cron.yml -f slot={_argv_slot} -f force=true`."
                ),
                color=DISCORD_COLOR_RED,
            )
        except Exception:
            pass
        raise
