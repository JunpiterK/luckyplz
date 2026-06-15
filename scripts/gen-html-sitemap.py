# -*- coding: utf-8 -*-
"""Generate /all/ — a crawlable HTML sitemap that links every indexable page in
every language with real <a href> links.

Why: the blog index injects post cards from posts.js via JS, so the raw HTML has
~zero internal post links. Language variants (ja/zh/es) are referenced only by
hreflang (700+ times) but almost never by a real <a>, so Google treats them as
orphans → "Discovered – currently not indexed". This page gives every post (and
every language variant), every tool, and every game a real internal link, so
crawl-priority/link-equity actually flows to them. Linked from the global footer
(siteFooter.js) and listed in sitemap.xml.

Auto-daily thin posts (robots-disallowed) are excluded — we do NOT want to feed
crawl budget to them.

Output: public/all/index.html
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
POSTS_JS = PUBLIC / "blog" / "posts.js"

try:
    BUILD = json.loads((PUBLIC / "build.json").read_text(encoding="utf-8")).get("v", "1")
except Exception:
    BUILD = "1"

# auto-daily / noindex slug patterns to exclude (mirror robots.txt)
SKIP = re.compile(r"(tech-recap-|-recap-20|open-brief-|close-brief-|premarket-|"
                  r"baseball-daily-|football-daily-|worldcup-daily-)")

LANG_LABEL = {"ko": "한국어", "en": "EN", "ja": "日本語", "zh": "中文", "es": "ES"}
CAT_LABEL = {
    "ai-tech": "AI · 테크", "space-tech": "우주 테크", "industry": "산업",
    "stocks": "증시", "football": "축구", "baseball": "야구",
    "gaming-history": "게임", "build": "메이킹", "tech-space": "테크·우주",
    "lifestyle": "라이프", "probability": "확률",
}


def parse_posts():
    """Tolerant parse of window.BLOG_POSTS entries (slug, lang, category, title, date)."""
    txt = POSTS_JS.read_text(encoding="utf-8")
    m = re.search(r"window\.BLOG_POSTS\s*=\s*\[", txt)
    if not m:
        return []
    body = txt[m.end():]
    # split into entries on each "slug:" marker
    chunks = re.split(r"\n\s*\{", body)
    out = []
    for ch in chunks:
        slug = re.search(r"slug:\s*'([^']+)'", ch)
        if not slug:
            continue
        lang = re.search(r"lang:\s*'([^']+)'", ch)
        cat = re.search(r"category:\s*'([^']+)'", ch)
        date = re.search(r"date:\s*'([^']+)'", ch)
        title = re.search(r"""title:\s*(['"])(.*?)\1""", ch, re.S)
        out.append({
            "slug": slug.group(1),
            "lang": lang.group(1) if lang else "ko",
            "category": cat.group(1) if cat else "",
            "date": date.group(1) if date else "",
            "title": (title.group(2) if title else slug.group(1)).strip(),
        })
    return out


def base_slug(slug):
    return re.sub(r"-(en|ja|zh|es)$", "", slug)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build():
    posts = [p for p in parse_posts() if not SKIP.search(p["slug"])]
    # cluster by base slug
    clusters = {}
    for p in posts:
        b = base_slug(p["slug"])
        clusters.setdefault(b, {"variants": {}, "category": p["category"], "date": p["date"], "title_ko": None})
        c = clusters[b]
        c["variants"][p["lang"]] = p["slug"]
        if p["lang"] == "ko" or c["title_ko"] is None:
            if p["lang"] == "ko":
                c["title_ko"] = p["title"]
            elif c["title_ko"] is None:
                c["title_ko"] = p["title"]
        if p["date"] > (c["date"] or ""):
            c["date"] = p["date"]
        if not c["category"]:
            c["category"] = p["category"]
    # group clusters by category, newest first
    by_cat = {}
    for b, c in clusters.items():
        by_cat.setdefault(c["category"] or "기타", []).append((b, c))
    for cat in by_cat:
        by_cat[cat].sort(key=lambda t: t[1]["date"], reverse=True)

    parts = []
    # blog clusters
    cat_order = ["ai-tech", "space-tech", "industry", "football", "baseball",
                 "gaming-history", "stocks", "build", "tech-space", "lifestyle", "probability"]
    seen = set()
    blog_html = []
    for cat in cat_order + [c for c in by_cat if c not in cat_order]:
        if cat not in by_cat:
            continue
        items = by_cat[cat]
        blog_html.append(f'<h3>{esc(CAT_LABEL.get(cat, cat))} <span>({len(items)})</span></h3><ul>')
        for b, c in items:
            langs = []
            for lg in ("ko", "en", "ja", "zh", "es"):
                if lg in c["variants"]:
                    langs.append(f'<a href="/blog/{c["variants"][lg]}/">{LANG_LABEL[lg]}</a>')
            title = esc(c["title_ko"] or b)
            blog_html.append(f'<li><span class="t">{title}</span><span class="lk">{" · ".join(langs)}</span></li>')
        blog_html.append("</ul>")
    parts.append('<section><h2>블로그 글 <small>Blog</small></h2>' + "".join(blog_html) + "</section>")

    # tools (color suite — all 5 langs where present; spacex tools ko/en)
    tools = [
        ("color-difference", "색차 계산기 ΔE", ["ko", "en", "ja", "zh"]),
        ("gamut-comparator", "색역 비교기", ["ko", "en", "ja", "zh", "es"]),
        ("color-temperature", "색온도·백색점 변환기", ["ko", "en", "ja", "zh", "es"]),
        ("color-vision", "색각이상 시뮬레이터", ["ko", "en", "ja", "zh", "es"]),
        ("spacex-valuation", "SpaceX 가치평가", ["ko", "en"]),
        ("spacex-portfolio-calculator", "SpaceX 포트폴리오", ["ko", "en"]),
        ("spacex-invest-sim", "SpaceX 투자 시뮬", ["ko", "en"]),
        ("spacex-countdown", "발사 카운트다운", ["ko", "en"]),
    ]
    suf = {"ko": "", "en": "-en", "ja": "-ja", "zh": "-zh", "es": "-es"}
    th = ['<section><h2>도구 <small>Tools</small></h2><ul>']
    for slug, name, langs in tools:
        lk = " · ".join(f'<a href="/tools/{slug}{suf[lg]}/">{LANG_LABEL[lg]}</a>' for lg in langs)
        th.append(f'<li><span class="t">{esc(name)}</span><span class="lk">{lk}</span></li>')
    th.append("</ul></section>")
    parts.append("".join(th))

    # games
    games = [("roulette", "룰렛"), ("ladder", "사다리타기"), ("team", "팀 나누기"),
             ("lotto", "로또 번호"), ("dice", "주사위"), ("car-racing", "카레이싱")]
    gh = ['<section><h2>게임 <small>Games</small></h2><ul>']
    for slug, name in games:
        gh.append(f'<li><span class="t">{esc(name)}</span><span class="lk"><a href="/games/{slug}/">플레이</a></span></li>')
    gh.append("</ul></section>")
    parts.append("".join(gh))

    n_links = sum(len(c["variants"]) for c in clusters.values()) + sum(len(t[2]) for t in tools) + len(games)
    return "\n".join(parts), len(clusters), n_links


TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>전체 콘텐츠 — Lucky Please</title>
<meta name="description" content="Lucky Please의 모든 글·도구·게임을 언어별로 모은 색인 페이지. 블로그(AI·테크·우주·스포츠·게임), 색채 도구, 미니게임.">
<link rel="canonical" href="https://luckyplz.com/all/">
<meta name="robots" content="index, follow">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0b0f17;color:#e8eef7;font-family:'Noto Sans KR',-apple-system,sans-serif;line-height:1.6;font-size:15px}
a{color:#5dc1ff;text-decoration:none}a:hover{text-decoration:underline}
.topbar{display:flex;gap:14px;align-items:center;padding:12px 18px;border-bottom:1px solid #243150;font-size:13px}
.topbar a{color:#93a3bf;font-weight:600}
.wrap{max-width:880px;margin:0 auto;padding:26px 18px 70px}
h1{font-size:26px;font-weight:800;margin-bottom:6px}
.lead{color:#93a3bf;font-size:14.5px;margin-bottom:24px}
section{margin:0 0 30px}
h2{font-size:19px;font-weight:800;margin:26px 0 12px;padding-bottom:8px;border-bottom:1px solid #243150}
h2 small{color:#647698;font-size:13px;font-weight:600;margin-left:6px}
h3{font-size:14px;font-weight:700;color:#a78bfa;margin:16px 0 8px}
h3 span{color:#647698;font-weight:400;font-size:12px}
ul{list-style:none}
li{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:baseline;padding:7px 0;border-bottom:1px solid #18223a}
li .t{flex:1;min-width:200px;color:#e8eef7}
li .lk{font-size:12.5px;color:#647698}
li .lk a{margin:0 1px}
footer{max-width:880px;margin:0 auto;padding:18px;color:#647698;font-size:12px;border-top:1px solid #243150}
</style>
</head>
<body>
<div class="topbar"><a href="/">← Lucky Please</a><a href="/blog/">블로그</a><a href="/tools/">도구</a><a href="/games/">게임</a></div>
<div class="wrap">
<h1>전체 콘텐츠</h1>
<p class="lead">모든 글·도구·게임을 언어별로 모았습니다. ({CLUSTERS}개 글 · {LINKS}개 링크)</p>
{BODY}
</div>
<footer>Lucky Please · 전체 콘텐츠 색인 · <a href="/sitemap.xml">sitemap.xml</a></footer>
<script src="/js/siteFooter.js?v={BUILD}" defer></script>
</body>
</html>"""


def update_sitemap():
    p = PUBLIC / "sitemap.xml"
    raw = p.read_text(encoding="utf-8")
    if "<loc>https://luckyplz.com/all/</loc>" in raw:
        return
    block = ('  <url>\n    <loc>https://luckyplz.com/all/</loc>\n'
             '    <changefreq>daily</changefreq>\n    <priority>0.5</priority>\n  </url>')
    raw = raw.replace("</urlset>", block + "\n</urlset>")
    p.write_text(raw, encoding="utf-8")
    print("[sitemap] added /all/")


def main():
    body, n_clusters, n_links = build()
    html = (TEMPLATE.replace("{BODY}", body).replace("{CLUSTERS}", str(n_clusters))
            .replace("{LINKS}", str(n_links)).replace("{BUILD}", str(BUILD)))
    out = PUBLIC / "all"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    print(f"[write] public/all/index.html — {n_clusters} clusters, {n_links} internal links")
    update_sitemap()


if __name__ == "__main__":
    main()
