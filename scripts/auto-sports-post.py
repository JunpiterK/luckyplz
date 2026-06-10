"""Auto Sports Post pipeline (football / baseball daily).

Mirrors scripts/auto-daily-post.py (the stock pipeline) but for sports:

  * football-daily  — La Liga (PD) + Premier League (PL) via football-data.org
  * baseball-daily  — MLB via MLB StatsAPI (keyless)

DESIGN — factual safety:
  The results and standings TABLES are rendered directly from the verified API
  JSON. Claude never sees a chance to alter a score. Claude writes ONLY the prose
  (summary, objective issues, the one subjective fan section, bottom line) plus a
  team-name localization map. So fabricated results are structurally impossible.

GUARD — no-match-day skip:
  If the monitored leagues played zero finished games on the target date, the
  pipeline logs a clean skip and exits 0. This auto-handles the off-season
  (football Jun-Jul, MLB Nov-Mar) with no special-casing.

Reuses the battle-tested infra from auto-daily-post.py: call_claude (retry +
fallback model), notify_healthcheck / notify_discord, update_sitemap, bump_cache,
git_push, LANG_META, pick_localized, has_lang_content, html_escape, L.

Usage:
    python scripts/auto-sports-post.py --slot baseball-daily
    python scripts/auto-sports-post.py --slot football-daily --date 2026-08-16
    python scripts/auto-sports-post.py --slot baseball-daily --dry-run
    python scripts/auto-sports-post.py --slot football-daily --check-only

Env:
    ANTHROPIC_API_KEY     required
    FOOTBALL_DATA_KEY     required for football-daily (free key, football-data.org)
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
import time
import urllib.request
import urllib.parse
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

# ---------------------------------------------------------------------------
# Reuse tested infrastructure from auto-daily-post.py (hyphenated filename →
# import via importlib). The __main__ guard there means importing has no side
# effects beyond defining helpers/constants.
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
DISCORD_COLOR_YELLOW = adp.DISCORD_COLOR_YELLOW

# Sports OG generator (sibling module, importable name).
_og_spec = importlib.util.spec_from_file_location(
    "gen_sports_og", SCRIPTS / "gen_sports_og.py")
_gso = importlib.util.module_from_spec(_og_spec)
_og_spec.loader.exec_module(_gso)
make_sports_og = _gso.make_sports_og

# ---------------------------------------------------------------------------
# Slot definitions
# ---------------------------------------------------------------------------
SPORTS_SLOTS = {
    "football-daily": {
        "prompt": "football-daily.md",
        "slug_prefix": "football-daily",
        "category": "football",
        "sport": "football",
        "read_min": 6,
        "cover_emoji": "⚽",
        "focus": ["Real Madrid", "Manchester United"],
        "competitions": [("PD", "La Liga", "laliga"), ("PL", "Premier League", "epl")],
        "header_label_ko": "축구 데일리 · 라리가 & EPL",
        "header_label_en": "FOOTBALL DAILY · LA LIGA & EPL",
        "header_label_ja": "サッカー・デイリー · リーガ & プレミア",
        "header_label_zh": "足球每日 · 西甲 & 英超",
    },
    "baseball-daily": {
        "prompt": "baseball-daily.md",
        "slug_prefix": "baseball-daily",
        "category": "baseball",
        "sport": "baseball",
        "read_min": 6,
        "cover_emoji": "⚾",
        "focus": ["Los Angeles Dodgers"],
        "header_label_ko": "MLB 데일리",
        "header_label_en": "MLB DAILY",
        "header_label_ja": "MLB デイリー",
        "header_label_zh": "MLB 每日",
    },
}

USER_AGENT = "luckyplz-sports/1.0 (+https://luckyplz.com)"


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def _get_json(url: str, headers: dict | None = None, timeout: int = 25) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


# ---------------------------------------------------------------------------
# Data fetch — MLB (keyless StatsAPI)
# ---------------------------------------------------------------------------
MLB_DIVISIONS = {
    200: "AL West", 201: "AL East", 202: "AL Central",
    203: "NL West", 204: "NL East", 205: "NL Central",
}
MLB_DIV_ORDER = ["AL East", "AL Central", "AL West", "NL East", "NL Central", "NL West"]


def fetch_baseball(date_str: str) -> dict:
    """Return MLB games + division standings for `date_str` (US game date)."""
    base = "https://statsapi.mlb.com/api/v1"
    sch = _get_json(f"{base}/schedule?sportId=1&date={date_str}&hydrate=linescore,team")
    games = []
    for d in sch.get("dates", []):
        for g in d.get("games", []):
            st = g.get("status", {})
            if st.get("abstractGameState") != "Final":
                continue
            away = g["teams"]["away"]
            home = g["teams"]["home"]
            ls = g.get("linescore", {})
            inning = ls.get("currentInning") or 9
            games.append({
                "away": away["team"]["name"],
                "away_score": away.get("score"),
                "home": home["team"]["name"],
                "home_score": home.get("score"),
                "innings": inning,
                "extra": bool(inning and inning > 9),
                "detail": st.get("detailedState", "Final"),
            })

    season = date_str[:4]
    divisions = []
    if games:  # only fetch standings when there's content to publish
        st = _get_json(
            f"{base}/standings?leagueId=103,104&season={season}"
            f"&standingsTypes=regularSeason&hydrate=team")
        by_name = {}
        for rec in st.get("records", []):
            divid = rec.get("division", {}).get("id")
            name = MLB_DIVISIONS.get(divid, str(divid))
            league = "AL" if rec.get("league", {}).get("id") == 103 else "NL"
            teams = []
            for tr in rec.get("teamRecords", []):
                l10 = None
                for sr in tr.get("records", {}).get("splitRecords", []):
                    if sr.get("type") == "lastTen":
                        l10 = f"{sr.get('wins', 0)}-{sr.get('losses', 0)}"
                        break
                teams.append({
                    "rank": tr.get("divisionRank", ""),
                    "team": tr["team"]["name"],
                    "w": tr.get("wins"),
                    "l": tr.get("losses"),
                    "pct": tr.get("winningPercentage", ""),
                    "gb": tr.get("gamesBack", "-"),
                    "streak": tr.get("streak", {}).get("streakCode", ""),
                    "l10": l10 or "",
                })
            teams.sort(key=lambda t: int(t["rank"]) if str(t["rank"]).isdigit() else 99)
            by_name[name] = {"name": name, "league": league, "teams": teams}
        divisions = [by_name[n] for n in MLB_DIV_ORDER if n in by_name]

    return {
        "sport": "baseball",
        "date": date_str,
        "games": games,
        "divisions": divisions,
    }


# ---------------------------------------------------------------------------
# Data fetch — Football (football-data.org v4, key required)
# ---------------------------------------------------------------------------
def fetch_football(date_str: str, competitions: list, key: str | None) -> dict | None:
    """Return La Liga + EPL finished matches + standings for `date_str`.

    Returns None when no API key is configured (caller treats as a clean skip
    — during the off-season there are no matches anyway).
    """
    if not key:
        print("[football] FOOTBALL_DATA_KEY not set — cannot fetch, skipping")
        return None
    headers = {"X-Auth-Token": key}
    base = "https://api.football-data.org/v4"
    comps_out = []
    for code, name, css in competitions:
        matches = []
        try:
            md = _get_json(
                f"{base}/competitions/{code}/matches"
                f"?dateFrom={date_str}&dateTo={date_str}", headers=headers)
        except Exception as e:
            print(f"[football] {code} matches fetch failed: {e}")
            md = {"matches": []}
        time.sleep(6)  # football-data.org free tier: 10 req/min
        for m in md.get("matches", []):
            if m.get("status") != "FINISHED":
                continue
            ft = m.get("score", {}).get("fullTime", {})
            matches.append({
                "home": m["homeTeam"].get("name") or m["homeTeam"].get("shortName"),
                "away": m["awayTeam"].get("name") or m["awayTeam"].get("shortName"),
                "home_score": ft.get("home"),
                "away_score": ft.get("away"),
                "matchday": m.get("matchday"),
            })
        standings = []
        try:
            sd = _get_json(f"{base}/competitions/{code}/standings", headers=headers)
            time.sleep(6)
            tables = sd.get("standings", [])
            total = next((t for t in tables if t.get("type") == "TOTAL"), tables[0] if tables else {})
            for row in total.get("table", []):
                standings.append({
                    "pos": row.get("position"),
                    "team": row["team"].get("name") or row["team"].get("shortName"),
                    "played": row.get("playedGames"),
                    "w": row.get("won"),
                    "d": row.get("draw"),
                    "l": row.get("lost"),
                    "gd": row.get("goalDifference"),
                    "pts": row.get("points"),
                    "form": row.get("form") or "",
                })
        except Exception as e:
            print(f"[football] {code} standings fetch failed: {e}")
        comps_out.append({"code": code, "name": name, "css": css,
                          "matches": matches, "standings": standings})
    return {"sport": "football", "date": date_str, "competitions": comps_out}


# ---------------------------------------------------------------------------
# Match counting / guard
# ---------------------------------------------------------------------------
def count_matches(slot: str, data: dict | None) -> int:
    if not data:
        return 0
    if slot == "baseball-daily":
        return len(data.get("games", []))
    return sum(len(c.get("matches", [])) for c in data.get("competitions", []))


# ---------------------------------------------------------------------------
# Prompt data block (text the model reads; tables are rendered separately)
# ---------------------------------------------------------------------------
def format_sports_for_prompt(slot: str, data: dict) -> str:
    lines = []
    focus = set(SPORTS_SLOTS[slot]["focus"])
    if slot == "baseball-daily":
        lines.append(f"## MLB results — {data['date']} (US game date)")
        for g in data["games"]:
            star = "  [FOCUS: Dodgers]" if "Los Angeles Dodgers" in (g["away"], g["home"]) else ""
            extra = f" (F/{g['innings']})" if g["extra"] else ""
            lines.append(f"- {g['away']} {g['away_score']} @ {g['home']} {g['home_score']}{extra}{star}")
        lines.append("\n## Division standings (rank · team · W-L · PCT · GB · L10 · streak)")
        for div in data["divisions"]:
            lines.append(f"### {div['name']}")
            for t in div["teams"]:
                star = "  <-- Dodgers" if t["team"] in focus else ""
                lines.append(f"  {t['rank']}. {t['team']}  {t['w']}-{t['l']}  {t['pct']}  GB {t['gb']}  L10 {t['l10']}  {t['streak']}{star}")
    else:
        for comp in data["competitions"]:
            lines.append(f"## {comp['name']} — results {data['date']}")
            if not comp["matches"]:
                lines.append("  (no matches this date)")
            for m in comp["matches"]:
                star = "  [FOCUS]" if (m["home"] in focus or m["away"] in focus) else ""
                lines.append(f"- {m['home']} {m['home_score']}-{m['away_score']} {m['away']}  (MD {m['matchday']}){star}")
            lines.append(f"\n## {comp['name']} — standings (pos · team · P · W-D-L · GD · Pts · form)")
            for t in comp["standings"]:
                star = "  <-- focus club" if t["team"] in focus else ""
                lines.append(f"  {t['pos']}. {t['team']}  P{t['played']}  {t['w']}-{t['d']}-{t['l']}  GD {t['gd']}  {t['pts']}pts  {t['form']}{star}")
            lines.append("")
    return "\n".join(lines)


def build_prompt(slot: str, data: dict) -> str:
    template = (PROMPTS / SPORTS_SLOTS[slot]["prompt"]).read_text(encoding="utf-8")
    return template.replace("{{SPORTS_DATA}}", format_sports_for_prompt(slot, data))


# ---------------------------------------------------------------------------
# Rendering — tables from verified data, prose from Claude
# ---------------------------------------------------------------------------
def tn(name: str, lang: str, team_names: dict) -> str:
    """Localized team name with English fallback."""
    if lang == "en" or not name:
        return name
    loc = (team_names or {}).get(name, {})
    return loc.get(lang) or name


def _sec_title(text: str) -> str:
    return f'<div class="section-title">{html_escape(text)}</div>'


def _form_html(form: str) -> str:
    out = []
    for ch in (form or "").replace(",", "")[-5:]:
        cls = {"W": "w", "D": "d", "L": "l"}.get(ch.upper(), "d")
        out.append(f'<span class="{cls}">{html_escape(ch.upper())}</span>')
    return f'<span class="sp-form">{"".join(out)}</span>' if out else ""


def render_football_sections(data: dict, lang: str, slot: str, tnmap: dict) -> str:
    focus = set(SPORTS_SLOTS[slot]["focus"])
    parts = [_sec_title(L(lang, "경기 결과", "RESULTS", "試合結果", "比赛结果"))]
    for comp in data["competitions"]:
        if not comp["matches"]:
            continue
        sub = L(lang, f"{len(comp['matches'])}경기", f"{len(comp['matches'])} matches",
                f"{len(comp['matches'])}試合", f"{len(comp['matches'])}场")
        rows = [f'<div class="sp-comp"><div class="sp-comp-head">'
                f'<span class="sp-comp-badge {comp["css"]}">{html_escape(comp["name"])}</span>'
                f'<span class="sp-comp-sub">{html_escape(sub)}</span></div>']
        for m in comp["matches"]:
            hs, as_ = m["home_score"], m["away_score"]
            hw = " win" if (hs is not None and as_ is not None and hs > as_) else ""
            aw = " win" if (hs is not None and as_ is not None and as_ > hs) else ""
            foc = " focus" if (m["home"] in focus or m["away"] in focus) else ""
            rows.append(
                f'<div class="sp-match{foc}">'
                f'<span class="t home{hw}">{html_escape(tn(m["home"], lang, tnmap))}</span>'
                f'<span class="sc">{hs}–{as_}</span>'
                f'<span class="t away{aw}">{html_escape(tn(m["away"], lang, tnmap))}</span>'
                f'</div>')
        rows.append("</div>")
        parts.append("\n".join(rows))

    # Standings
    parts.append(_sec_title(L(lang, "순위표", "STANDINGS", "順位表", "积分榜")))
    th = [L(lang, "순위", "#", "順", "#"), L(lang, "팀", "Team", "チーム", "球队"),
          "P", "W", "D", "L", "GD", L(lang, "승점", "Pts", "勝点", "积分"),
          L(lang, "최근", "Form", "近5", "近5")]
    for comp in data["competitions"]:
        if not comp["standings"]:
            continue
        head = (f'<div class="sp-comp"><div class="sp-comp-head">'
                f'<span class="sp-comp-badge {comp["css"]}">{html_escape(comp["name"])}</span></div></div>')
        thead = "".join(f'<th class="l">{html_escape(c)}</th>' if i == 1 else f"<th>{html_escape(c)}</th>"
                        for i, c in enumerate(th))
        trs = []
        for t in comp["standings"]:
            foc = " class=\"focus\"" if t["team"] in focus else ""
            gd = t["gd"]
            gd_s = f"+{gd}" if isinstance(gd, int) and gd > 0 else str(gd)
            trs.append(
                f"<tr{foc}>"
                f'<td class="pos">{t["pos"]}</td>'
                f'<td class="l nm">{html_escape(tn(t["team"], lang, tnmap))}</td>'
                f'<td>{t["played"]}</td><td>{t["w"]}</td><td>{t["d"]}</td><td>{t["l"]}</td>'
                f'<td>{gd_s}</td><td class="pts">{t["pts"]}</td>'
                f'<td>{_form_html(t["form"])}</td></tr>')
        parts.append(
            head +
            f'<div class="sp-table-wrap"><table class="sp-table"><thead><tr>{thead}</tr></thead>'
            f'<tbody>{"".join(trs)}</tbody></table></div>')
    return "\n".join(parts)


def render_baseball_sections(data: dict, lang: str, slot: str, tnmap: dict) -> str:
    focus = set(SPORTS_SLOTS[slot]["focus"])
    n = len(data["games"])
    parts = [_sec_title(L(lang, f"경기 결과 · {n}경기", f"RESULTS · {n} games",
                          f"試合結果 · {n}試合", f"比赛结果 · {n}场"))]
    rows = ['<div class="sp-comp">']
    for g in data["games"]:
        hs, as_ = g["home_score"], g["away_score"]
        hw = " win" if (hs is not None and as_ is not None and hs > as_) else ""
        aw = " win" if (hs is not None and as_ is not None and as_ > hs) else ""
        foc = " focus" if ("Los Angeles Dodgers" in (g["home"], g["away"])) else ""
        extra = ""
        if g["extra"]:
            inn = g["innings"]
            extra_txt = L(lang, f"연장 {inn}회", f"F/{inn}", f"延長{inn}回", f"{inn}局")
            extra = f'<span class="meta">{html_escape(extra_txt)}</span>'
        rows.append(
            f'<div class="sp-match{foc}">'
            f'<span class="t home{aw}">{html_escape(tn(g["away"], lang, tnmap))}</span>'
            f'<span class="sc">{as_}–{hs}</span>'
            f'<span class="t away{hw}">{html_escape(tn(g["home"], lang, tnmap))}</span>'
            f'{extra}</div>')
    rows.append("</div>")
    parts.append("\n".join(rows))

    # Standings — per division
    parts.append(_sec_title(L(lang, "지구 순위", "DIVISION STANDINGS", "地区順位", "分区排名")))
    th = [L(lang, "순위", "#", "順", "#"), L(lang, "팀", "Team", "チーム", "球队"),
          "W", "L", "PCT", "GB", "L10", L(lang, "연속", "Strk", "連", "连")]
    for div in data["divisions"]:
        thead = "".join(f'<th class="l">{html_escape(c)}</th>' if i == 1 else f"<th>{html_escape(c)}</th>"
                        for i, c in enumerate(th))
        trs = []
        for t in div["teams"]:
            foc = " class=\"focus\"" if t["team"] in focus else ""
            trs.append(
                f"<tr{foc}>"
                f'<td class="pos">{t["rank"]}</td>'
                f'<td class="l nm">{html_escape(tn(t["team"], lang, tnmap))}</td>'
                f'<td>{t["w"]}</td><td>{t["l"]}</td><td>{html_escape(str(t["pct"]))}</td>'
                f'<td>{html_escape(str(t["gb"]))}</td><td>{html_escape(str(t["l10"]))}</td>'
                f'<td>{html_escape(str(t["streak"]))}</td></tr>')
        league_css = "al" if div["league"] == "AL" else "nl"
        head = (f'<div class="sp-comp"><div class="sp-comp-head">'
                f'<span class="sp-comp-badge {league_css}">{html_escape(div["name"])}</span></div></div>')
        parts.append(
            head +
            f'<div class="sp-table-wrap"><table class="sp-table"><thead><tr>{thead}</tr></thead>'
            f'<tbody>{"".join(trs)}</tbody></table></div>')
    return "\n".join(parts)


def render_prose_sections(prose: dict, lang: str, slot: str) -> str:
    issues = pick_localized(prose, "issues_html", lang)
    fan = pick_localized(prose, "fan_html", lang)
    fan_tag = L(lang, "팬의 시각 · 주관적 의견", "FAN'S VIEW · OPINION",
                "ファン目線 · 主観", "球迷视角 · 主观")
    if slot == "football-daily":
        fan_who = L(lang, "레알 마드리드 · 맨유 팬", "A Real Madrid & Man United fan",
                    "レアル&ユナイテッドのファン", "皇马&曼联球迷")
    else:
        fan_who = L(lang, "LA 다저스 팬", "An LA Dodgers fan", "ドジャースのファン", "道奇球迷")
    out = []
    if issues:
        out.append(_sec_title(L(lang, "오늘의 이슈", "STORYLINES", "今日の焦点", "今日焦点")))
        out.append(f'<div class="sp-issues">{issues}</div>')
    if fan:
        out.append(_sec_title(L(lang, "팬 시각", "FAN'S VIEW", "ファン目線", "球迷视角")))
        out.append(f'<div class="sp-fan"><span class="sp-fan-tag">{html_escape(fan_tag)} · {html_escape(fan_who)}</span>{fan}</div>')
    return "\n".join(out)


def render_sports_html(slot: str, lang: str, data: dict, prose: dict, *,
                       slug: str, build: str, og_image_filename: str,
                       publish_date: str) -> str:
    cfg = SPORTS_SLOTS[slot]
    template = (TEMPLATES / "daily-base.html").read_text(encoding="utf-8")
    base_url = "https://luckyplz.com"
    suffix = LANG_META[lang]["slug_suffix"]
    canonical = f"{base_url}/blog/{slug}{suffix}/"
    href_ko = f"{base_url}/blog/{slug}/"
    href_en = f"{base_url}/blog/{slug}-en/"
    href_ja = f"{base_url}/blog/{slug}-ja/"
    href_zh = f"{base_url}/blog/{slug}-zh/"

    tnmap = prose.get("team_names", {})
    title = pick_localized(prose, "headline", lang)
    title_full = f"{title} | Lucky Please"
    raw_summary = pick_localized(prose, "summary", lang)
    summary = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw_summary)).strip()
    bottom_body = pick_localized(prose, "bottom_line", lang)
    bottom_title = L(lang, "관전 포인트", "WHAT TO WATCH", "注目ポイント", "看点")

    # Sections: results + standings (from data) → prose (from Claude)
    if slot == "baseball-daily":
        data_sections = render_baseball_sections(data, lang, slot, tnmap)
    else:
        data_sections = render_football_sections(data, lang, slot, tnmap)
    prose_sections = render_prose_sections(prose, lang, slot)
    sections_html = data_sections + "\n" + prose_sections

    # Header badges — compact league summary chips
    badges = []
    if slot == "baseball-daily":
        badges.append(f'<span class="badge badge-blue">MLB {len(data["games"])}{L(lang, "경기","G","試合","场")}</span>')
    else:
        for comp in data["competitions"]:
            if comp["matches"]:
                badges.append(f'<span class="badge badge-orange">{html_escape(comp["name"])} {len(comp["matches"])}</span>')
    header_badges = "\n    ".join(badges)

    # Localized labels
    og_locale = LANG_META[lang]["og_locale"]
    og_locale_alt = "en_US" if lang != "en" else "ko_KR"
    og_image_url = f"{base_url}/assets/blog/{og_image_filename}?v={build}"
    og_image_alt = f"{title} — {summary[:80]}"
    header_label = f'{cfg.get(f"header_label_{lang}") or cfg["header_label_en"]} · {data["date"]}'

    disclaimer = L(lang,
        ko=f"<strong>⚽⚾ 스포츠 데일리 · {data['date']}</strong><br>경기 결과·순위는 공식 데이터(football-data.org · MLB StatsAPI) 그대로입니다. 이슈 정리는 객관적, '팬 시각'은 주관적 의견입니다.",
        en=f"<strong>⚽⚾ Sports Daily · {data['date']}</strong><br>Results and standings are taken verbatim from official data (football-data.org · MLB StatsAPI). Storylines are objective; the 'Fan's View' is a subjective opinion.",
        ja=f"<strong>⚽⚾ スポーツ・デイリー · {data['date']}</strong><br>結果・順位は公式データ（football-data.org · MLB StatsAPI）そのままです。論点は客観、「ファン目線」は主観です。",
        zh=f"<strong>⚽⚾ 体育每日 · {data['date']}</strong><br>比赛结果与排名直接取自官方数据（football-data.org · MLB StatsAPI）。焦点解读保持客观，「球迷视角」为主观观点。")

    footer_disclaimer = L(lang,
        ko="데이터 출처: football-data.org (라리가·프리미어리그), MLB StatsAPI (메이저리그). 경기 결과·순위표는 자동 동기화된 공식 데이터입니다. 본문 중 '팬 시각'은 특정 팀(레알 마드리드·맨유·LA 다저스) 팬 관점의 주관적 의견이며 사실 보도가 아닙니다.",
        en="Data sources: football-data.org (La Liga, Premier League) and MLB StatsAPI (MLB). Results and standings are auto-synced official data. The 'Fan's View' section is a subjective opinion written from a specific club's supporter perspective (Real Madrid, Man United, LA Dodgers) and is not factual reporting.",
        ja="データ出典: football-data.org（リーガ・プレミア）、MLB StatsAPI（MLB）。結果・順位表は自動同期された公式データです。本文の「ファン目線」は特定クラブ（レアル・マドリード、マンU、ドジャース）ファン視点の主観であり、事実報道ではありません。",
        zh="数据来源: football-data.org（西甲·英超）、MLB StatsAPI（美职棒）。比赛结果与积分榜为自动同步的官方数据。文中「球迷视角」为特定球队（皇马·曼联·道奇）球迷视角的主观观点，并非事实报道。")

    # JSON-LD
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
    crumb_label = cfg.get(f"header_label_{lang}") or cfg["header_label_en"]
    jsonld_crumb = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": home_label, "item": f"{base_url}/"},
            {"@type": "ListItem", "position": 2, "name": blog_label, "item": f"{base_url}/blog/"},
            {"@type": "ListItem", "position": 3, "name": crumb_label, "item": canonical},
        ],
    }

    keywords = L(lang,
        "라리가, 프리미어리그, MLB, 축구, 야구, 경기 결과, 순위, 데일리, lucky please" if slot == "football-daily"
            else "MLB, 메이저리그, 야구, 경기 결과, 지구 순위, 다저스, 데일리, lucky please",
        "La Liga, Premier League, MLB, football, baseball, results, standings, daily, lucky please",
        "ラリーガ, プレミアリーグ, MLB, サッカー, 野球, 試合結果, 順位, デイリー",
        "西甲, 英超, MLB, 足球, 棒球, 比赛结果, 排名, 每日")

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
    cat = cfg["category"]
    related_links = (
        f'<a href="/blog/?cat={cat}">{L(lang, "스포츠 글 전체 보기 →", "See all sports posts →", "スポーツ記事一覧 →", "查看全部体育文章 →")}</a>\n'
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
        "{{HREFLANG_KO}}": href_ko, "{{HREFLANG_EN}}": href_en,
        "{{HREFLANG_JA}}": href_ja, "{{HREFLANG_ZH}}": href_zh,
        "{{HREFLANG_DEFAULT}}": href_en if lang == "en" else href_ko,
        "{{OG_LOCALE}}": og_locale, "{{OG_LOCALE_ALT}}": og_locale_alt,
        "{{OG_DESCRIPTION}}": html_escape(summary[:200]),
        "{{OG_IMAGE_URL}}": og_image_url,
        "{{OG_IMAGE_ALT}}": html_escape(og_image_alt),
        "{{PUBLISHED_TIME}}": f"{publish_date}T09:00:00+09:00",
        "{{JSONLD_BLOGPOSTING}}": json.dumps(jsonld_blog, ensure_ascii=False),
        "{{JSONLD_BREADCRUMB}}": json.dumps(jsonld_crumb, ensure_ascii=False),
        "{{FONT_URL}}": font_url, "{{BODY_FONT}}": body_font,
        "{{NAV_BACK}}": "← BLOG",
        "{{HEADER_LABEL}}": html_escape(header_label),
        "{{HEADER_H1}}": html_escape(title),
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
    # Sports posts are in the Sports section, not Markets.
    out = out.replace('<meta property="article:section" content="Markets">',
                      '<meta property="article:section" content="Sports">')
    return out


# ---------------------------------------------------------------------------
# Site integration
# ---------------------------------------------------------------------------
def update_posts_js_sports(slug: str, slot: str, prose: dict, publish_date: str,
                           langs: list[str]) -> None:
    cfg = SPORTS_SLOTS[slot]
    posts_path = PUBLIC / "blog" / "posts.js"
    raw = posts_path.read_text(encoding="utf-8")
    marker = "window.BLOG_POSTS = ["
    idx = raw.find(marker)
    if idx == -1:
        raise SystemExit("Could not find BLOG_POSTS array in posts.js")

    default_tags = {
        "ko": ["스포츠", "축구" if slot == "football-daily" else "야구", "데일리"],
        "en": ["Sports", "Football" if slot == "football-daily" else "Baseball", "Daily"],
        "ja": ["スポーツ", "サッカー" if slot == "football-daily" else "野球", "デイリー"],
        "zh": ["体育", "足球" if slot == "football-daily" else "棒球", "每日"],
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
    ap.add_argument("--slot", required=True, choices=sorted(SPORTS_SLOTS.keys()))
    ap.add_argument("--date", help="target match date YYYY-MM-DD (default: yesterday KST)")
    ap.add_argument("--dry-run", action="store_true", help="no git push, skip cache bump")
    ap.add_argument("--check-only", action="store_true", help="guard only; exit 0=publish, 1=skip")
    ap.add_argument("--force", action="store_true", help="overwrite an existing slug directory")
    args = ap.parse_args()

    slot = args.slot
    cfg = SPORTS_SLOTS[slot]

    if args.dry_run:
        os.environ["LP_GIT_PUSH"] = ""
        os.environ["LP_SKIP_CACHE"] = "1"

    now_kst = datetime.now(KST)
    publish_date = now_kst.strftime("%Y-%m-%d")
    target_date = args.date or (now_kst - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"[main] slot={slot} target_date={target_date} publish_date={publish_date}")

    # Fetch
    if slot == "baseball-daily":
        data = fetch_baseball(target_date)
    else:
        data = fetch_football(target_date, cfg["competitions"], os.environ.get("FOOTBALL_DATA_KEY"))

    n = count_matches(slot, data)
    print(f"[main] matches found: {n}")

    if args.check_only:
        sys.exit(0 if n > 0 else 1)

    if n == 0:
        msg = f"no finished matches for {slot} on {target_date} (off-season or no fixtures)"
        print(f"[guard] {msg} — clean skip")
        notify_healthcheck(slot, "success", summary=msg)
        return

    slug = f"{cfg['slug_prefix']}-{target_date}"
    if (BLOG_DIR / slug).exists() and not args.force:
        print(f"[guard] {slug} already exists — skip (use --force to overwrite)")
        notify_healthcheck(slot, "success", summary=f"{slug} already published")
        return

    # Generate prose via Claude (tables come from data, not the model)
    prompt = build_prompt(slot, data)
    print(f"[main] prompt {len(prompt)} chars, calling Claude...")
    prose = call_claude(prompt, max_tokens=32000)

    # Build version stamp (read current build.json so OG/asset URLs match)
    try:
        build = json.loads((PUBLIC / "build.json").read_text(encoding="utf-8")).get("v", publish_date)
    except Exception:
        build = publish_date

    langs = [l for l in LANGS if has_lang_content(prose, l)]
    if not langs:
        raise SystemExit("Claude returned no usable language content")
    print(f"[main] publishing langs={langs}")

    # OG images (per language) + HTML
    htmls = {}
    for lang in langs:
        og_name = f"{slug}-{lang}.png"
        og_path = ASSETS_BLOG / og_name
        try:
            label = cfg.get(f"header_label_{lang}") or cfg["header_label_en"]
            sub = f"{target_date} · " + (f"MLB {len(data['games'])}" if slot == "baseball-daily"
                                          else " · ".join(c["name"] for c in data["competitions"] if c["matches"]))
            make_sports_og(og_path, sport=cfg["sport"], lang=lang,
                           label=label, headline=pick_localized(prose, "headline", lang), sub=sub)
            print(f"[og] wrote {og_path}")
        except Exception as e:
            print(f"[og] generation failed ({lang}): {e}")
        htmls[lang] = render_sports_html(
            slot, lang, data, prose, slug=slug, build=build,
            og_image_filename=og_name, publish_date=publish_date)

    write_post_files(slug, htmls)
    update_posts_js_sports(slug, slot, prose, publish_date, langs)
    update_sitemap(slug, publish_date, langs)
    bump_cache()
    git_push(slug, slot)

    notify_healthcheck(slot, "success",
                       summary=f"{slug} published ({len(langs)} langs, {n} matches)")
    print(f"[main] done: {slug}")


if __name__ == "__main__":
    import sys as _sys
    import traceback as _tb
    _argv_slot = "unknown"
    for i, a in enumerate(_sys.argv):
        if a == "--slot" and i + 1 < len(_sys.argv):
            _argv_slot = _sys.argv[i + 1]
            break
    try:
        main()
    except SystemExit as e:
        if int(getattr(e, "code", 0) or 0) not in (0,):
            try:
                notify_healthcheck(_argv_slot, "failed", summary=f"SystemExit({e.code})")
                notify_discord(title=f"❌ {_argv_slot} sports publish BLOCKED",
                               body=f"Exited with status **{e.code}**. Check the Actions log.",
                               color=DISCORD_COLOR_RED)
            except Exception:
                pass
        raise
    except BaseException as exc:
        tb_text = _tb.format_exc()
        try:
            notify_healthcheck(_argv_slot, "failed", summary=(f"{type(exc).__name__}: {exc}\n\n{tb_text}")[:4000])
            notify_discord(title=f"❌ {_argv_slot} sports pipeline crashed",
                           body=f"**{type(exc).__name__}**: `{str(exc)[:300]}`\n\n```\n{tb_text[-1500:]}\n```",
                           color=DISCORD_COLOR_RED)
        except Exception:
            pass
        raise
