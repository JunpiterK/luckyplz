# -*- coding: utf-8 -*-
"""sitemap.xml 생성기 (2026-08-19).

이전에는 손으로 관리해서 `/games/dice/` 가 통째로 빠져 있었다. 메인 6종
중 하나가 색인 대상에서 누락된 상태였다는 뜻이다. 목록을 코드로 옮겨
그런 누락이 다시 생기지 않게 한다.

우선순위 원칙:
    1.0  언어 홈 5종 — 5개 언어 상호 hreflang 을 실제로 선언한다
    0.9  도구 랜딩 24종 — 6 도구 × en/es/pt/ja
    0.8  메인 6게임 본체 (클러스터의 ko 멤버이기도 하다)
    0.6  아케이드 허브 · 전체 게임 목록 · 나머지 게임 11종
    0.3  법적/정보 페이지

클러스터 URL 은 scripts/lp_clusters.py 가 단일 진실원천이다. 여기서 목록을
따로 적으면 두 곳이 어긋나 hreflang 상호성이 깨진다.

    python scripts/gen-sitemap.py
"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lp_clusters import CLUSTERS, LANGS, member  # noqa: E402

BASE = "https://luckyplz.com"
TODAY = date.today().isoformat()

# 실제 페이지가 있는 5개 언어 홈 (경로 기반). 나머지 11개 언어는 UI 만
# 지원하며 색인 대상이 아니다 — 근거는 CLAUDE.md 의 언어 우선순위.
LANG_HOMES = [("en", "/"), ("es", "/es/"), ("pt", "/pt/"), ("ja", "/ja/"), ("ko", "/ko/")]

# 도구 랜딩은 lp_clusters 에서 온다 — 6 도구 × en/es/pt/ja = 24 페이지.
# ko 멤버는 게임 본체라 아래 GAMES_MAIN 에서 따로 등록한다.
GAMES_MAIN = list(CLUSTERS.keys())
GAMES_REST = ["balloon", "lotto", "glory-racing", "lucky-merge", "orbit", "dodge", "tetris",
              "starship-lander", "brick", "snake", "pacman", "burger", "quiz"]

INFO = ["/about/", "/contact/", "/terms/", "/privacy/"]


def url(loc, priority, changefreq="monthly", alternates=None):
    out = ["    <url>",
           "        <loc>%s%s</loc>" % (BASE, loc),
           "        <lastmod>%s</lastmod>" % TODAY,
           "        <changefreq>%s</changefreq>" % changefreq,
           "        <priority>%s</priority>" % priority]
    for hl, href in (alternates or []):
        out.append('        <xhtml:link rel="alternate" hreflang="%s" href="%s%s"/>' % (hl, BASE, href))
    out.append("    </url>")
    return "\n".join(out)


def main():
    missing = []
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
             ""]

    lang_alts = [(hl, path) for hl, path in LANG_HOMES] + [("x-default", "/")]
    for hl, path in LANG_HOMES:
        parts.append(url(path, "1.0", "daily", lang_alts))
    parts.append("")

    # 도구 클러스터 — 각 페이지가 5개 언어 상호 alternate 를 갖는다.
    # ko 멤버(게임 본체)는 앱 페이지이기도 해서 changefreq 를 따로 준다.
    for tool in CLUSTERS:
        alts = [(lg, member(tool, lg)) for lg in LANGS] + [("x-default", CLUSTERS[tool]["en"])]
        for lg in LANGS:
            path = member(tool, lg)
            if lg == "ko":
                parts.append(url(path, "0.8", "weekly", alts))
            else:
                parts.append(url(path, "0.9", "monthly", alts))
    parts.append("")

    parts.append(url("/arcade/", "0.6", "monthly"))
    parts.append(url("/games/", "0.6", "weekly"))
    for g in GAMES_REST:
        parts.append(url("/games/%s/" % g, "0.6", "monthly"))
    parts.append("")

    for slug in INFO:
        parts.append(url(slug, "0.3", "yearly"))

    parts.append("</urlset>")
    xml = "\n".join(parts) + "\n"

    # 등록한 URL 이 실제로 파일로 존재하는지 확인 — 404 를 색인 요청하면
    # 크롤 예산 낭비이자 품질 신호 감점이다.
    cluster_paths = [member(t, lg) for t in CLUSTERS for lg in LANGS]
    for path in ([p for _, p in LANG_HOMES] + cluster_paths + ["/arcade/", "/games/"]
                 + ["/games/%s/" % g for g in GAMES_REST] + INFO):
        f = ROOT / "public" / path.strip("/") / "index.html" if path != "/" else ROOT / "public" / "index.html"
        if not f.exists():
            missing.append(path)

    (ROOT / "public" / "sitemap.xml").write_text(xml, encoding="utf-8")
    total = xml.count("<loc>")
    print("sitemap.xml: %d URL" % total)
    if missing:
        print("!! 파일 없음 (수정 필요):", missing)
    else:
        print("전 URL 파일 존재 확인 OK")


if __name__ == "__main__":
    main()
