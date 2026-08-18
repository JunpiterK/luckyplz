# -*- coding: utf-8 -*-
"""스페인어·포르투갈어·일본어 도구 랜딩 생성기 (2026-08-19).

왜 필요한가:
    언어 홈(`/es/` 등)만으로는 도구별 검색어를 못 받는다. 사람들이 치는
    말은 "ruleta de nombres", "sorteio de times", "あみだくじ" 같은 도구
    이름이지 사이트 이름이 아니다. 도구 × 언어 = 18개 진입점이 필요하다.

    영어는 이미 gen-landing.py 가 만든 6종이 있고, 한국어는 게임 본체
    (`/games/<id>/`)가 한국어 본문을 갖고 있어 그대로 클러스터의 ko 멤버다.
    즉 이 스크립트가 클러스터의 나머지 세 변을 채운다.

콘텐츠 원칙:
    영어판의 기계 번역이 아니다. 각 언어 사용자가 실제로 검색하는 표현을
    제목·본문에 쓰고, 그 언어권에서만 의미 있는 맥락을 넣는다
    (예: 일본어판 사다리는 あみだくじ 의 유래, 포르투갈어판 빙고는
    브라질에서 통용되는 진행 방식).

    콘텐츠는 파일 비대화를 막으려 언어별로 분리 보관한다:
        landing_content_es.py / landing_content_pt.py / landing_content_ja.py

    python scripts/gen-landing-i18n.py
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lp_clusters import CLUSTERS, hreflang_lines, member, OG_LOCALE  # noqa: E402

OUT = ROOT / "public"

# 언어별 고정 UI 문구. 페이지마다 반복되는 껍데기라 콘텐츠와 분리한다.
UI = {
    "es": dict(
        nav_back="INICIO", nav_arcade="ARCADE",
        btn_open="Abrir a pantalla completa", btn_how="Cómo funciona",
        cap_pre="Funcionando aquí arriba", cap_post="o",
        cap_link="ábrelo a pantalla completa",
        h_how="Cómo se usa", h_uses="Para qué se usa",
        h_faq="Preguntas frecuentes", h_more="Los otros cinco sorteos",
        site="Lucky Please",
    ),
    "pt": dict(
        nav_back="INÍCIO", nav_arcade="ARCADE",
        btn_open="Abrir em tela cheia", btn_how="Como funciona",
        cap_pre="Rodando aqui em cima", cap_post="ou",
        cap_link="abra em tela cheia",
        h_how="Como usar", h_uses="Para que serve",
        h_faq="Perguntas frequentes", h_more="Os outros cinco sorteios",
        site="Lucky Please",
    ),
    "ja": dict(
        nav_back="ホーム", nav_arcade="アーケード",
        btn_open="全画面で開く", btn_how="使い方",
        cap_pre="上でそのまま動きます", cap_post="または",
        cap_link="全画面で開く",
        h_how="使い方", h_uses="こんな場面で",
        h_faq="よくある質問", h_more="ほかの5つの抽選ツール",
        site="Lucky Please",
    ),
}

# 상호 링크에 쓸 도구 이름·설명 (언어별). 콘텐츠 모듈의 short 필드에서 채운다.
OG_IMG = {"roulette": "roulette", "team": "team", "dice": "dice",
          "bingo": "bingo", "car-racing": "car-racing", "ladder": "ladder"}

TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>

    <meta name="lp-ad-policy" content="off"><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="keywords" content="{keywords}">
<link rel="canonical" href="https://luckyplz.com{slug}">
{hreflang}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Lucky Please">
<meta property="og:locale" content="{og_locale}">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="https://luckyplz.com{slug}">
<meta property="og:image" content="https://luckyplz.com/og/games/{og_img}.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_desc}">
<meta name="twitter:image" content="https://luckyplz.com/og/games/{og_img}.png">
<script type="application/ld+json">{app_ld}</script>
<script type="application/ld+json">{faq_ld}</script>
<script type="application/ld+json">{crumb_ld}</script>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0A0A1A">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Noto+Sans+KR:wght@400;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NZDPE3H3DQ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-NZDPE3H3DQ');</script>
<style>
  :root{{--primary:#FF6B35;--secondary:#00D9FF;--accent:#FFE66D;--dark:#0A0A1A;--surface:#12122a;--border:rgba(255,255,255,.1);--text:#e8ecf4;--dim:#9aa6be}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--dark);color:var(--text);font-family:'Noto Sans KR',-apple-system,sans-serif;line-height:1.75;-webkit-font-smoothing:antialiased}}
  .wrap{{max-width:840px;margin:0 auto;padding:0 18px}}
  .nav{{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid var(--border);position:sticky;top:0;background:rgba(10,10,26,.85);backdrop-filter:blur(8px);z-index:50}}
  .nav a{{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);text-decoration:none;letter-spacing:1px}}
  .nav a:hover{{color:var(--secondary)}}
  .hero{{text-align:center;padding:36px 0 18px}}
  h1{{font-size:29px;font-weight:900;line-height:1.3;letter-spacing:-.02em;background:linear-gradient(135deg,var(--primary),var(--accent),var(--secondary));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
  .lead{{font-size:15.5px;color:var(--dim);margin:14px auto 0;max-width:680px}}
  .cta-row{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:20px 0 6px}}
  .btn{{font-family:'Orbitron','Noto Sans KR',sans-serif;font-weight:700;font-size:13.5px;letter-spacing:.03em;padding:12px 22px;border-radius:10px;text-decoration:none;border:1px solid var(--border)}}
  .btn.primary{{background:linear-gradient(135deg,var(--primary),#ff8c42);color:#1a0d04;border:none}}
  .btn.ghost{{color:var(--text);background:rgba(255,255,255,.05)}}
  .embed{{margin:18px 0 6px;border:1px solid var(--border);border-radius:16px;overflow:hidden;background:#06061a;box-shadow:0 16px 50px rgba(0,0,0,.5)}}
  .embed iframe{{display:block;width:100%;height:660px;border:0}}
  .embed-cap{{font-size:12px;color:var(--dim);text-align:center;margin:8px 0 0}}
  h2{{font-size:20px;font-weight:800;color:#fff;margin:34px 0 10px;letter-spacing:-.01em}}
  p{{margin:10px 0;color:#cfd6e6}}
  ol,ul{{margin:10px 0 10px 22px;color:#cfd6e6}}
  li{{margin:7px 0}}
  .uses{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0}}
  .use{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:13px 14px}}
  .use b{{color:#fff;display:block;margin-bottom:3px;font-size:14px}}
  .use span{{font-size:13px;color:var(--dim)}}
  .faq{{margin:10px 0}}
  .faq details{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:0 14px;margin:8px 0}}
  .faq summary{{cursor:pointer;padding:13px 0;font-weight:700;color:#fff;font-size:15px;list-style:none}}
  .faq summary::-webkit-details-marker{{display:none}}
  .faq summary::after{{content:'+';float:right;color:var(--secondary);font-weight:900}}
  .faq details[open] summary::after{{content:'\\2013'}}
  .faq p{{padding:0 0 14px;margin:0;color:var(--dim);font-size:14px}}
  .more{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0}}
  .more a{{display:block;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px;text-decoration:none;color:#fff;font-weight:700;transition:border-color .2s}}
  .more a:hover{{border-color:var(--secondary)}}
  .more a span{{display:block;font-size:12px;color:var(--dim);font-weight:400;margin-top:3px}}
  @media(max-width:600px){{h1{{font-size:23px}}.uses,.more{{grid-template-columns:1fr}}.embed iframe{{height:560px}}}}
</style>
</head>
<body>

<nav class="nav">
  <a href="/{lang}/">&larr; {nav_back}</a>
  <a href="/arcade/">{nav_arcade}</a>
</nav>

<div class="wrap">

  <header class="hero">
    <h1>{h1}</h1>
    <p class="lead">{lead}</p>
    <div class="cta-row">
      <a class="btn primary" href="{game}">&#9654; {btn_open}</a>
      <a class="btn ghost" href="#how">{btn_how}</a>
    </div>
  </header>

  <div class="embed">
    <iframe src="{game}" title="{h1}" loading="lazy"></iframe>
  </div>
  <p class="embed-cap">{cap_pre} &#9757;&#65039; &mdash; {cap_post} <a href="{game}" style="color:var(--secondary)">{cap_link}</a>.</p>

  <div class="body">

    <h2 id="how">{h_how}</h2>
    <ol>
{steps}
    </ol>

    <h2>{h_uses}</h2>
    <div class="uses">
{uses}
    </div>

{sections}
    <h2>{h_faq}</h2>
    <div class="faq">
{faq_html}
    </div>

    <h2>{h_more}</h2>
    <div class="more">
{more_html}
    </div>

  </div>
</div>

<script src="/js/siteFooter.js?v=1" defer></script>
</body>
</html>
"""


def load(mod):
    path = HERE / (mod + ".py")
    spec = importlib.util.spec_from_file_location(mod, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.CONTENT


CONTENT = {
    "es": load("landing_content_es"),
    "pt": load("landing_content_pt"),
    "ja": load("landing_content_ja"),
}


def build(lang, tool, cfg):
    ui = UI[lang]
    slug = member(tool, lang)
    game = CLUSTERS[tool]["game"]

    app_ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": "%s %s" % (ui["site"], cfg["h1"]), "url": "https://luckyplz.com" + slug,
        "applicationCategory": "GameApplication", "operatingSystem": "Any (web browser)",
        "inLanguage": lang,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": cfg["og_desc"],
        "publisher": {"@type": "Organization", "name": "Lucky Please", "url": "https://luckyplz.com/"},
    }, ensure_ascii=False, separators=(",", ":"))
    faq_ld = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage", "inLanguage": lang,
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in cfg["faq"]],
    }, ensure_ascii=False, separators=(",", ":"))
    crumb_ld = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": ui["nav_back"],
             "item": "https://luckyplz.com/%s/" % lang},
            {"@type": "ListItem", "position": 2, "name": cfg["h1"],
             "item": "https://luckyplz.com" + slug},
        ],
    }, ensure_ascii=False, separators=(",", ":"))

    steps = "\n".join("      <li>%s</li>" % x for x in cfg["steps"])
    uses = "\n".join('      <div class="use"><b>%s</b><span>%s</span></div>' % (b, s)
                     for b, s in cfg["uses"])
    faq_html = "\n".join("      <details><summary>%s</summary><p>%s</p></details>" % (q, a)
                         for q, a in cfg["faq"])
    more_html = "\n".join(
        '      <a href="%s">%s<span>%s</span></a>' % (member(t, lang), c["h1"], c["short"])
        for t, c in CONTENT[lang].items() if t != tool)

    return TEMPLATE.format(
        lang=lang, slug=slug, game=game, hreflang=hreflang_lines(tool, indent=""),
        og_locale=OG_LOCALE[lang], og_img=OG_IMG[tool],
        app_ld=app_ld, faq_ld=faq_ld, crumb_ld=crumb_ld,
        steps=steps, uses=uses, faq_html=faq_html, more_html=more_html,
        sections=cfg["sections"], **ui, **{k: cfg[k] for k in
        ("title", "description", "keywords", "og_title", "og_desc", "h1", "lead")})


def main():
    total = 0
    for lang in ("es", "pt", "ja"):
        for tool, cfg in CONTENT[lang].items():
            slug = member(tool, lang)
            out = OUT / slug.strip("/") / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            html = build(lang, tool, cfg)
            out.write_text(html, encoding="utf-8")
            body = html[html.index('<div class="body">'):html.index("</body>")]
            txt = re.sub(r"<[^>]+>", " ", body)
            n = len(txt.split()) if lang != "ja" else len(re.sub(r"\s+", "", txt))
            unit = "단어" if lang != "ja" else "자"
            print("%-30s %5d%s" % (slug, n, unit))
            total += 1
    print("\n생성: %d 페이지" % total)


if __name__ == "__main__":
    main()
