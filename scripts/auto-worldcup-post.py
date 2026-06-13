"""Auto World Cup Post pipeline (2026 FIFA World Cup daily match reviews).

Mirrors scripts/auto-sports-post.py but for the 2026 World Cup, sourced from
ESPN's keyless public scoreboard API (no key, live during the tournament).

DESIGN — factual safety:
  Every score and every goalscorer line is rendered DIRECTLY from the verified
  ESPN JSON. Claude never gets the chance to alter a result. Claude writes ONLY
  the prose: a per-match review, an editorial "Player of the Day" pick (clearly
  labelled as our pick, drawn from the actual goalscorers), a tournament
  storyline, the headline/summary, and a team-name localization map. Fabricated
  scores are therefore structurally impossible.

GUARD — no-match-day skip:
  If zero finished World Cup matches exist for the target date, the pipeline logs
  a clean skip and exits 0 (rest days between matchdays auto-handled). After the
  final on 2026-07-19 every date is empty, so the cron self-retires with no
  special-casing.

MODES:
  * daily   (default)  — one date → slug `worldcup-daily-YYYY-MM-DD`
  * catchup (--date-from .. --date-to) — many dates aggregated into ONE
    date-grouped recap → slug `worldcup-recap-YYYY-MM-DD` (uses --date-to).

Reuses battle-tested infra from auto-daily-post.py: call_claude (retry +
fallback model), notify_healthcheck / notify_discord, update_sitemap,
bump_cache, git_push, LANG_META, pick_localized, has_lang_content, html_escape, L.

Usage:
    python scripts/auto-worldcup-post.py                         # yesterday KST, daily
    python scripts/auto-worldcup-post.py --date 2026-06-13
    python scripts/auto-worldcup-post.py --date-from 2026-06-11 --date-to 2026-06-14
    python scripts/auto-worldcup-post.py --date 2026-06-13 --dry-run
    python scripts/auto-worldcup-post.py --date 2026-06-13 --check-only

Env:
    ANTHROPIC_API_KEY     required
    LP_GIT_PUSH=1         actually git push (default 0 in dev, 1 in CI)
    LP_SKIP_CACHE=1       skip bump-cache.sh
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import re
import sys
import textwrap
import urllib.request
from datetime import datetime, timedelta
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

LANGS = ["ko", "en", "ja", "zh"]
CATEGORY = "football"
COVER_EMOJI = "🏆"
READ_MIN = 7
SLOT = "worldcup-daily"   # healthcheck / discord channel name

ESPN_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={d}")
USER_AGENT = "luckyplz-worldcup/1.0 (+https://luckyplz.com)"

# ---------------------------------------------------------------------------
# Reuse tested infrastructure from auto-daily-post.py
# ---------------------------------------------------------------------------
_adp_spec = importlib.util.spec_from_file_location(
    "auto_daily_post", SCRIPTS / "auto-daily-post.py")
adp = importlib.util.module_from_spec(_adp_spec)
_adp_spec.loader.exec_module(adp)

call_claude = adp.call_claude
notify_healthcheck = adp.notify_healthcheck
notify_discord = adp.notify_discord
update_sitemap = adp.update_sitemap
bump_cache = adp.bump_cache
git_push = adp.git_push
LANG_META = adp.LANG_META
pick_localized = adp.pick_localized
has_lang_content = adp.has_lang_content
html_escape = adp.html_escape
L = adp.L
DISCORD_COLOR_RED = adp.DISCORD_COLOR_RED

# Sports OG generator (football theme reused for the World Cup).
_og_spec = importlib.util.spec_from_file_location(
    "gen_sports_og", SCRIPTS / "gen_sports_og.py")
_gso = importlib.util.module_from_spec(_og_spec)
_og_spec.loader.exec_module(_gso)
make_sports_og = _gso.make_sports_og


# ---------------------------------------------------------------------------
# HTTP + small helpers
# ---------------------------------------------------------------------------
def _get_json(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def pl(d: dict | None, lang: str) -> str:
    """Localized field from a {ko,en,ja,zh} dict, falling back en → first."""
    if not isinstance(d, dict):
        return d or "" if isinstance(d, str) else ""
    return d.get(lang) or d.get("en") or next((v for v in d.values() if v), "")


# ---------------------------------------------------------------------------
# Data fetch — ESPN keyless scoreboard
# ---------------------------------------------------------------------------
def _group_of(event: dict) -> str:
    """Group label ('Group B') if this is a group-stage game, else round name."""
    comp = event.get("competitions", [{}])[0]
    for note in comp.get("notes", []):
        head = (note.get("headline") or "").strip()
        if head:
            return head
    blob = json.dumps(event, ensure_ascii=False)
    m = re.search(r"Group [A-Z]", blob)
    if m:
        return m.group(0)
    slug = (event.get("season") or {}).get("slug") or ""
    return slug.replace("-", " ").title() if slug else ""


def fetch_worldcup_date(date_str: str) -> list[dict]:
    """Return the list of FINISHED World Cup matches for one date (YYYY-MM-DD)."""
    url = ESPN_SCOREBOARD.format(d=date_str.replace("-", ""))
    try:
        data = _get_json(url)
    except Exception as e:
        print(f"[espn] fetch failed for {date_str}: {e}")
        return []
    matches = []
    for ev in data.get("events", []):
        comp = ev.get("competitions", [{}])[0]
        st = comp.get("status", {}).get("type", {})
        if not st.get("completed"):
            continue
        cs = {c.get("homeAway"): c for c in comp.get("competitors", [])}
        home, away = cs.get("home", {}), cs.get("away", {})
        if not home or not away:
            continue
        home_id = str(home.get("team", {}).get("id") or "")
        away_id = str(away.get("team", {}).get("id") or "")

        def _score(c):
            try:
                return int(c.get("score"))
            except (TypeError, ValueError):
                return None
        hs, as_ = _score(home), _score(away)

        goals = []
        for det in comp.get("details", []):
            if not det.get("scoringPlay"):
                continue
            tid = str(det.get("team", {}).get("id") or "")
            side = "home" if tid == home_id else "away" if tid == away_id else ""
            ath = det.get("athletesInvolved") or []
            player = ath[0].get("displayName") if ath else None
            if not player:
                continue
            goals.append({
                "player": player,
                "minute": (det.get("clock", {}) or {}).get("displayValue", ""),
                "side": side,
                "pk": bool(det.get("penaltyKick")),
                "og": bool(det.get("ownGoal")),
            })

        venue = comp.get("venue") or ev.get("venue") or {}
        addr = venue.get("address", {}) or {}
        matches.append({
            "id": str(ev.get("id")),
            "date": date_str,
            "home": home.get("team", {}).get("displayName"),
            "away": away.get("team", {}).get("displayName"),
            "home_id": home_id, "away_id": away_id,
            "home_score": hs, "away_score": as_,
            "home_win": bool(home.get("winner")),
            "away_win": bool(away.get("winner")),
            "group": _group_of(ev),
            "venue": venue.get("fullName") or "",
            "city": addr.get("city") or "",
            "country": addr.get("country") or "",
            "goals": goals,
        })
    return matches


def fetch_worldcup_range(date_from: str, date_to: str) -> list[tuple[str, list[dict]]]:
    """List of (date, matches) for every date in [from, to] that had finished games."""
    out = []
    d0 = datetime.strptime(date_from, "%Y-%m-%d").date()
    d1 = datetime.strptime(date_to, "%Y-%m-%d").date()
    cur = d0
    while cur <= d1:
        ds = cur.strftime("%Y-%m-%d")
        ms = fetch_worldcup_date(ds)
        if ms:
            out.append((ds, ms))
        cur += timedelta(days=1)
    return out


def count_matches(dates: list[tuple[str, list[dict]]]) -> int:
    return sum(len(ms) for _, ms in dates)


# ---------------------------------------------------------------------------
# Prompt — the model reads the verified data and must NOT change any number
# ---------------------------------------------------------------------------
def _abbr(name: str) -> str:
    return (name or "")[:3].upper()


def format_worldcup_for_prompt(dates: list[tuple[str, list[dict]]]) -> str:
    lines = []
    for ds, matches in dates:
        lines.append(f"## {ds}")
        for m in matches:
            grp = f"{m['group']} — " if m["group"] else ""
            venue = f" @ {m['venue']}, {m['city']}" if m["venue"] else ""
            lines.append(
                f"[match {m['id']}] {grp}{m['home']} {m['home_score']}-{m['away_score']} "
                f"{m['away']}{venue}")
            if m["goals"]:
                gl = []
                for g in m["goals"]:
                    who = _abbr(m["home"]) if g["side"] == "home" else _abbr(m["away"]) if g["side"] == "away" else "?"
                    tag = " (PK)" if g["pk"] else " (OG)" if g["og"] else ""
                    gl.append(f"{g['player']} [{who}] {g['minute']}{tag}")
                lines.append("    Goals: " + "; ".join(gl))
            else:
                lines.append("    Goals: none (0-0 or goalless draw)")
        lines.append("")
    return "\n".join(lines)


def build_prompt(dates: list[tuple[str, list[dict]]], catchup: bool, span: str) -> str:
    template = (PROMPTS / "worldcup-daily.md").read_text(encoding="utf-8")
    mode = ("CATCH-UP RECAP covering every match from the tournament opener through now"
            if catchup else "DAILY review of one matchday")
    return (template
            .replace("{{MODE}}", mode)
            .replace("{{SPAN}}", span)
            .replace("{{WORLDCUP_DATA}}", format_worldcup_for_prompt(dates)))


# ---------------------------------------------------------------------------
# Rendering — match cards from verified data, prose from Claude
# ---------------------------------------------------------------------------
def tn(name: str, lang: str, team_names: dict) -> str:
    if lang == "en" or not name:
        return name
    return (team_names or {}).get(name, {}).get(lang) or name


def _sec_title(text: str) -> str:
    return f'<div class="section-title">{html_escape(text)}</div>'


def _goal_line(m: dict, lang: str) -> str:
    """Goalscorer chips grouped by side, rendered straight from API data."""
    if not m["goals"]:
        return ""
    home_g, away_g = [], []
    for g in m["goals"]:
        tag = ""
        if g["pk"]:
            tag = ' <span class="wc-gtag">PK</span>'
        elif g["og"]:
            tag = ' <span class="wc-gtag og">OG</span>'
        chip = (f'<span class="wc-goal">{html_escape(g["player"])} '
                f'<span class="wc-min">{html_escape(g["minute"])}</span>{tag}</span>')
        (home_g if g["side"] == "home" else away_g).append(chip)
    return (f'<div class="wc-goals">'
            f'<div class="wc-gside">{"".join(home_g) or "&middot;"}</div>'
            f'<div class="wc-gball">⚽</div>'
            f'<div class="wc-gside away">{"".join(away_g) or "&middot;"}</div></div>')


def _mom_chip(mom: dict, m: dict, lang: str, tnmap: dict) -> str:
    if not mom or not mom.get("player"):
        return ""
    side = mom.get("side")
    team = m["home"] if side == "home" else m["away"] if side == "away" else ""
    team_loc = tn(team, lang, tnmap) if team else ""
    note = mom.get("note") or ""
    tag = L(lang, "오늘의 선수 · 편집 선정", "PLAYER OF THE DAY · our pick",
            "今日の選手 · 編集選出", "今日之星 · 编辑评选")
    teamspan = f'<span class="wc-mom-team">{html_escape(team_loc)}</span>' if team_loc else ""
    return (f'<div class="wc-mom"><span class="wc-mom-tag">★ {html_escape(tag)}</span>'
            f'<span class="wc-mom-name">{html_escape(mom["player"])}</span>{teamspan}'
            f'<span class="wc-mom-note">{html_escape(note)}</span></div>')


def render_match_card(m: dict, lang: str, tnmap: dict, review: str, mom: dict) -> str:
    hs, as_ = m["home_score"], m["away_score"]
    hw = " win" if m["home_win"] else ""
    aw = " win" if m["away_win"] else ""
    grp = html_escape(m["group"]) if m["group"] else ""
    loc = ", ".join([p for p in [m["city"], m["country"]] if p])
    venue = html_escape(m["venue"] + (f" · {loc}" if loc else "")) if m["venue"] else ""
    meta = []
    if grp:
        meta.append(f'<span class="wc-grp">{grp}</span>')
    if venue:
        meta.append(f'<span class="wc-venue">{venue}</span>')
    review_html = f'<div class="wc-review">{review}</div>' if review else ""
    return (
        f'<div class="wc-card">'
        f'<div class="wc-card-top">{"".join(meta)}</div>'
        f'<div class="wc-score">'
        f'<span class="wc-t home{hw}">{html_escape(tn(m["home"], lang, tnmap))}</span>'
        f'<span class="wc-sc">{hs}<span class="wc-dash">–</span>{as_}</span>'
        f'<span class="wc-t away{aw}">{html_escape(tn(m["away"], lang, tnmap))}</span>'
        f'</div>'
        f'{_goal_line(m, lang)}'
        f'{review_html}'
        f'{_mom_chip(mom, m, lang, tnmap)}'
        f'</div>')


def render_sections(dates: list[tuple[str, list[dict]]], lang: str, prose: dict) -> str:
    tnmap = prose.get("team_names", {})
    reviews = prose.get("matches", {}) or {}
    multi = len(dates) > 1
    parts = []
    for ds, matches in dates:
        if multi:
            parts.append(_sec_title(_date_label(ds, lang) + f" · {len(matches)}" +
                                    L(lang, "경기", " matches", "試合", "场")))
        else:
            parts.append(_sec_title(L(lang, "경기 결과 & 리뷰", "RESULTS & REVIEW",
                                      "結果 & レビュー", "结果 & 回顾")))
        for m in matches:
            r = reviews.get(m["id"], {})
            review = r.get(f"review_{lang}") or r.get("review_en") or ""
            mom = {"player": r.get("mom_player"), "side": r.get("mom_side"),
                   "note": r.get(f"mom_note_{lang}") or r.get("mom_note_en") or ""}
            parts.append(render_match_card(m, lang, tnmap, review, mom))

    storylines = pick_localized(prose, "storylines", lang)
    if storylines:
        parts.append(_sec_title(L(lang, "토너먼트 흐름", "TOURNAMENT STORYLINES",
                                  "トーナメントの焦点", "赛事焦点")))
        parts.append(f'<div class="wc-stories">{storylines}</div>')
    return "\n".join(parts)


_MONTHS = {
    "ko": "{m}월 {d}일", "ja": "{m}月{d}日", "zh": "{m}月{d}日",
}
_EN_MON = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _date_label(ds: str, lang: str) -> str:
    y, mo, d = ds.split("-")
    if lang == "en":
        return f"{_EN_MON[int(mo)]} {int(d)}"
    return _MONTHS[lang].format(m=int(mo), d=int(d))


# ---------------------------------------------------------------------------
# Full-page render via the shared daily template
# ---------------------------------------------------------------------------
def render_html(lang: str, dates: list, prose: dict, *, slug: str, build: str,
                og_image_filename: str, publish_date: str, span_label: str,
                catchup: bool) -> str:
    template = (TEMPLATES / "daily-base.html").read_text(encoding="utf-8")
    base_url = "https://luckyplz.com"
    suffix = LANG_META[lang]["slug_suffix"]
    canonical = f"{base_url}/blog/{slug}{suffix}/"

    tnmap = prose.get("team_names", {})
    title = pick_localized(prose, "headline", lang)
    title_full = f"{title} | Lucky Please"
    raw_summary = pick_localized(prose, "summary", lang)
    summary = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw_summary)).strip()
    bottom_body = pick_localized(prose, "bottom_line", lang)
    bottom_title = L(lang, "관전 포인트", "WHAT TO WATCH", "注目ポイント", "看点")

    sections_html = render_sections(dates, lang, prose)

    n = count_matches(dates)
    badges = [f'<span class="badge badge-orange">🏆 {L(lang, "월드컵", "WORLD CUP", "W杯", "世界杯")}</span>',
              f'<span class="badge badge-blue">{n}{L(lang, "경기", " G", "試合", "场")}</span>']
    header_badges = "\n    ".join(badges)

    og_locale = LANG_META[lang]["og_locale"]
    og_locale_alt = "en_US" if lang != "en" else "ko_KR"
    og_image_url = f"{base_url}/assets/blog/{og_image_filename}?v={build}"
    og_image_alt = f"{title} — {summary[:80]}"
    wc_label = L(lang, "FIFA 월드컵 2026", "FIFA WORLD CUP 2026",
                 "FIFA ワールドカップ2026", "FIFA 世界杯 2026")
    header_label = f'{wc_label} · {span_label}'

    disclaimer = L(lang,
        ko=f"<strong>🏆 FIFA 월드컵 2026 · {span_label}</strong><br>경기 결과·득점자는 ESPN 공식 데이터 그대로입니다. 경기 리뷰와 '오늘의 선수'는 득점 기록에 근거한 편집부의 평가입니다.",
        en=f"<strong>🏆 FIFA World Cup 2026 · {span_label}</strong><br>Scores and goalscorers are taken verbatim from ESPN's official data. The match reviews and 'Player of the Day' are our editorial picks, grounded in the goal records.",
        ja=f"<strong>🏆 FIFAワールドカップ2026 · {span_label}</strong><br>結果・得点者はESPN公式データそのままです。レビューと「今日の選手」は得点記録に基づく編集部の評価です。",
        zh=f"<strong>🏆 FIFA世界杯2026 · {span_label}</strong><br>比分与进球者直接取自ESPN官方数据。比赛回顾与「今日之星」为编辑部基于进球记录的评选。")

    footer_disclaimer = L(lang,
        ko="데이터 출처: ESPN (FIFA 월드컵 2026). 경기 결과·득점자는 자동 동기화된 공식 데이터입니다. 본문의 경기 리뷰와 '오늘의 선수(편집 선정)'는 득점 기록에 근거한 luckyplz 편집부의 주관적 평가이며 FIFA 공식 시상과 무관합니다.",
        en="Data source: ESPN (FIFA World Cup 2026). Scores and goalscorers are auto-synced official data. The match reviews and 'Player of the Day (our pick)' are luckyplz's subjective editorial assessments based on the goal records and are unrelated to any official FIFA award.",
        ja="データ出典: ESPN（FIFAワールドカップ2026）。結果・得点者は自動同期された公式データです。レビューと「今日の選手（編集選出）」は得点記録に基づくluckyplz編集部の主観評価であり、FIFA公式表彰とは無関係です。",
        zh="数据来源: ESPN（FIFA世界杯2026）。比分与进球者为自动同步的官方数据。比赛回顾与「今日之星（编辑评选）」为luckyplz编辑部基于进球记录的主观评选，与FIFA官方奖项无关。")

    jsonld_blog = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": title, "description": summary[:200],
        "datePublished": publish_date, "dateModified": publish_date,
        "author": {"@type": "Organization", "name": "Lucky Please", "url": "https://luckyplz.com/"},
        "publisher": {"@type": "Organization", "name": "Lucky Please",
                      "logo": {"@type": "ImageObject", "url": "https://luckyplz.com/assets/icon-192.png"}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "inLanguage": lang,
    }
    home_label = L(lang, "홈", "Home", "ホーム", "首页")
    blog_label = L(lang, "블로그", "Blog", "ブログ", "博客")
    jsonld_crumb = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": home_label, "item": f"{base_url}/"},
            {"@type": "ListItem", "position": 2, "name": blog_label, "item": f"{base_url}/blog/"},
            {"@type": "ListItem", "position": 3, "name": wc_label, "item": canonical},
        ],
    }

    keywords = L(lang,
        "월드컵, FIFA 월드컵 2026, 북중미 월드컵, 경기 결과, 리뷰, MOM, 오늘의 선수, 축구, lucky please",
        "World Cup, FIFA World Cup 2026, results, match review, player of the day, football, lucky please",
        "ワールドカップ, FIFA W杯2026, 試合結果, レビュー, 今日の選手, サッカー",
        "世界杯, FIFA世界杯2026, 比赛结果, 回顾, 今日之星, 足球")

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

    related_title = L(lang, "관련 글 RELATED", "RELATED", "関連記事 RELATED", "相关文章 RELATED")
    related_links = (
        f'<a href="/blog/?cat=football">{L(lang, "축구 글 전체 보기 →", "See all football posts →", "サッカー記事一覧 →", "查看全部足球文章 →")}</a>\n'
        f'<a href="/blog/">{L(lang, "블로그 홈 →", "Blog home →", "ブログホーム →", "博客首页 →")}</a>'
    )

    repl = {
        "{{LANG}}": lang,
        "{{CONVENTION}}": "global",
        "{{BUILD}}": build,
        "{{TITLE}}": html_escape(title_full),
        "{{TITLE_SHORT}}": html_escape(title),
        "{{DESCRIPTION}}": html_escape(summary[:200]),
        "{{KEYWORDS}}": html_escape(keywords),
        "{{CANONICAL_URL}}": canonical,
        "{{HREFLANG_KO}}": f"{base_url}/blog/{slug}/",
        "{{HREFLANG_EN}}": f"{base_url}/blog/{slug}-en/",
        "{{HREFLANG_JA}}": f"{base_url}/blog/{slug}-ja/",
        "{{HREFLANG_ZH}}": f"{base_url}/blog/{slug}-zh/",
        "{{HREFLANG_DEFAULT}}": f"{base_url}/blog/{slug}-en/" if lang == "en" else f"{base_url}/blog/{slug}/",
        "{{OG_LOCALE}}": og_locale, "{{OG_LOCALE_ALT}}": og_locale_alt,
        "{{OG_DESCRIPTION}}": html_escape(summary[:200]),
        "{{OG_IMAGE_URL}}": og_image_url,
        "{{OG_IMAGE_ALT}}": html_escape(og_image_alt),
        "{{PUBLISHED_TIME}}": f"{publish_date}T11:00:00+09:00",
        "{{JSONLD_BLOGPOSTING}}": json.dumps(jsonld_blog, ensure_ascii=False),
        "{{JSONLD_BREADCRUMB}}": json.dumps(jsonld_crumb, ensure_ascii=False),
        "{{FONT_URL}}": font_url, "{{BODY_FONT}}": body_font,
        "{{NAV_BACK}}": "← BLOG",
        "{{HEADER_LABEL}}": html_escape(header_label),
        "{{HEADER_H1}}": html_escape(title),
        "{{HEADER_SUB}}": html_escape(summary[:120]),
        "{{HEADER_BADGES}}": header_badges,
        "{{DISCLAIMER}}": disclaimer,
        "{{SNAPSHOT_NOTE}}": "",  # live-price note is stock-only; blank for football
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
    out = out.replace('<meta property="article:section" content="Markets">',
                      '<meta property="article:section" content="Sports">')
    return out


# ---------------------------------------------------------------------------
# Site integration
# ---------------------------------------------------------------------------
def update_posts_js(slug: str, prose: dict, publish_date: str, langs: list[str]) -> None:
    posts_path = PUBLIC / "blog" / "posts.js"
    raw = posts_path.read_text(encoding="utf-8")
    marker = "window.BLOG_POSTS = ["
    idx = raw.find(marker)
    if idx == -1:
        raise SystemExit("Could not find BLOG_POSTS array in posts.js")
    default_tags = {
        "ko": ["월드컵", "축구", "경기 리뷰"],
        "en": ["World Cup", "Football", "Match Review"],
        "ja": ["ワールドカップ", "サッカー", "レビュー"],
        "zh": ["世界杯", "足球", "比赛回顾"],
    }
    slug_map = {l: f"{slug}{LANG_META[l]['slug_suffix']}" for l in langs}
    entries = []
    for lang in langs:
        if not has_lang_content(prose, lang):
            continue
        entry_slug = slug_map[lang]
        alt_legacy = slug_map.get("en", entry_slug) if lang == "ko" else slug_map.get("ko", entry_slug)
        alts_obj = {l: s for l, s in slug_map.items() if l != lang}
        alts_js = "{ " + ", ".join(f"{k}: '{v}'" for k, v in alts_obj.items()) + " }"
        tags = prose.get(f"og_tags_{lang}") or default_tags.get(lang) or default_tags["en"]
        title = pick_localized(prose, "headline", lang)
        excerpt = re.sub(r"<[^>]+>", "", pick_localized(prose, "summary", lang))[:180]
        entries.append(textwrap.dedent(f"""\
            {{
                slug: '{entry_slug}',
                lang: '{lang}',
                category: '{CATEGORY}',
                date: '{publish_date}',
                readMinutes: {READ_MIN},
                coverEmoji: '{COVER_EMOJI}',
                tags: {json.dumps(tags, ensure_ascii=False)},
                title: {json.dumps(title, ensure_ascii=False)},
                excerpt: {json.dumps(excerpt, ensure_ascii=False)},
                alt: '{alt_legacy}',
                alts: {alts_js},
            }},"""))
    if not entries:
        print(f"[posts.js] no entries for {slug}")
        return
    combined = "\n    ".join(entries)
    new_raw = raw[: idx + len(marker)] + "\n    " + combined + raw[idx + len(marker):]
    posts_path.write_text(new_raw, encoding="utf-8")
    print(f"[posts.js] prepended {slug} for langs={','.join(langs)}")


def write_post_files(slug: str, htmls: dict) -> None:
    for lang in LANGS:
        html = htmls.get(lang) or ""
        if not html.strip():
            continue
        suffix = LANG_META[lang]["slug_suffix"]
        directory = BLOG_DIR / f"{slug}{suffix}"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(html, encoding="utf-8")
        print(f"[write] {directory}/index.html ({len(html)} bytes)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="single match date YYYY-MM-DD (default: yesterday KST)")
    ap.add_argument("--date-from", help="catch-up range start YYYY-MM-DD")
    ap.add_argument("--date-to", help="catch-up range end YYYY-MM-DD")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check-only", action="store_true", help="guard only; exit 0=publish, 1=skip")
    ap.add_argument("--force", action="store_true", help="overwrite an existing slug")
    args = ap.parse_args()

    if args.dry_run:
        os.environ["LP_GIT_PUSH"] = ""
        os.environ["LP_SKIP_CACHE"] = "1"

    now_kst = datetime.now(KST)
    publish_date = now_kst.strftime("%Y-%m-%d")

    catchup = bool(args.date_from and args.date_to)
    if catchup:
        date_from, date_to = args.date_from, args.date_to
        dates = fetch_worldcup_range(date_from, date_to)
        slug = f"worldcup-recap-{date_to}"
        span_label = f"{date_from} → {date_to}"
    else:
        target_date = args.date or (now_kst - timedelta(days=1)).strftime("%Y-%m-%d")
        ms = fetch_worldcup_date(target_date)
        dates = [(target_date, ms)] if ms else []
        slug = f"worldcup-daily-{target_date}"
        span_label = target_date

    n = count_matches(dates)
    print(f"[main] mode={'catchup' if catchup else 'daily'} span={span_label} matches={n}")

    if args.check_only:
        sys.exit(0 if n > 0 else 1)

    if n == 0:
        msg = f"no finished World Cup matches for {span_label} (rest day or tournament over)"
        print(f"[guard] {msg} — clean skip")
        notify_healthcheck(SLOT, "success", summary=msg)
        return

    if (BLOG_DIR / slug).exists() and not args.force:
        print(f"[guard] {slug} already exists — skip (use --force)")
        notify_healthcheck(SLOT, "success", summary=f"{slug} already published")
        return

    prompt = build_prompt(dates, catchup, span_label)
    print(f"[main] prompt {len(prompt)} chars, calling Claude...")
    prose = call_claude(prompt, max_tokens=32000)

    try:
        build = json.loads((PUBLIC / "build.json").read_text(encoding="utf-8")).get("v", publish_date)
    except Exception:
        build = publish_date

    langs = [l for l in LANGS if has_lang_content(prose, l)]
    if not langs:
        raise SystemExit("Claude returned no usable language content")
    print(f"[main] publishing langs={langs}")

    htmls = {}
    for lang in langs:
        og_name = f"{slug}-{lang}.png"
        og_path = ASSETS_BLOG / og_name
        try:
            label = L(lang, "FIFA 월드컵 2026", "FIFA WORLD CUP 2026",
                      "FIFA ワールドカップ2026", "FIFA 世界杯 2026")
            sub = f"{span_label} · {n}" + L(lang, "경기", " matches", "試合", "场")
            make_sports_og(og_path, sport="football", lang=lang,
                           label=label, headline=pick_localized(prose, "headline", lang), sub=sub)
            print(f"[og] wrote {og_path}")
        except Exception as e:
            print(f"[og] generation failed ({lang}): {e}")
        htmls[lang] = render_html(
            lang, dates, prose, slug=slug, build=build,
            og_image_filename=og_name, publish_date=publish_date,
            span_label=span_label, catchup=catchup)

    write_post_files(slug, htmls)
    update_posts_js(slug, prose, publish_date, langs)
    update_sitemap(slug, publish_date, langs)
    bump_cache()
    git_push(slug, SLOT)

    notify_healthcheck(SLOT, "success",
                       summary=f"{slug} published ({len(langs)} langs, {n} matches)")
    print(f"[main] done: {slug}")


if __name__ == "__main__":
    import traceback as _tb
    try:
        main()
    except SystemExit as e:
        if int(getattr(e, "code", 0) or 0) not in (0,):
            try:
                notify_healthcheck(SLOT, "failed", summary=f"SystemExit({e.code})")
                notify_discord(title=f"❌ {SLOT} publish BLOCKED",
                               body=f"Exited with status **{e.code}**. Check the Actions log.",
                               color=DISCORD_COLOR_RED)
            except Exception:
                pass
        raise
    except BaseException as exc:
        tb_text = _tb.format_exc()
        try:
            notify_healthcheck(SLOT, "failed", summary=(f"{type(exc).__name__}: {exc}\n\n{tb_text}")[:4000])
            notify_discord(title=f"❌ {SLOT} pipeline crashed",
                           body=f"**{type(exc).__name__}**: `{str(exc)[:300]}`\n\n```\n{tb_text[-1500:]}\n```",
                           color=DISCORD_COLOR_RED)
        except Exception:
            pass
        raise
