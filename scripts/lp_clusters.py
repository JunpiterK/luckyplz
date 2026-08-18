# -*- coding: utf-8 -*-
"""언어 클러스터 단일 진실원천 (2026-08-19).

한 도구 = 5개 언어 페이지 한 세트. 이 세트가 서로 hreflang 으로 묶여야
구글이 "같은 것의 다른 언어판"으로 인식한다. 정의가 여러 파일에 흩어지면
한 곳만 고쳐서 클러스터가 반쪽이 되는데, hreflang 은 상호 선언이 깨지면
**전부** 무시되므로 반쪽 클러스터는 없는 것과 같다. 그래서 여기 한 곳에만 둔다.

멤버 구성이 언어마다 다른 이유:
    ko 는 게임 본체(`/games/<id>/`)가 그대로 멤버다. 이미 한국어 본문
    500~650단어를 갖고 있어 별도 랜딩을 만들 이유가 없다.
    나머지 언어는 게임을 iframe 으로 임베드하는 랜딩 페이지다.

이 파일을 쓰는 곳:
    scripts/fix-page-lang.py    게임 본체의 hreflang
    scripts/gen-landing.py      영어 랜딩
    scripts/gen-landing-i18n.py es·pt·ja 랜딩
    scripts/gen-sitemap.py      sitemap 등록 목록
"""

BASE = "https://luckyplz.com"

# 도구 키 = 게임 디렉토리명(= ko 멤버 경로의 일부).
# 슬러그는 각 언어의 실제 검색어를 담는다 — /ja/amidakuji/ 처럼 현지 표기가
# 곧 검색어인 경우가 가장 강하다.
CLUSTERS = {
    "roulette": {
        "game": "/games/roulette/",
        "en": "/wheel-spinner/",
        "es": "/es/ruleta/",
        "pt": "/pt/roleta/",
        "ja": "/ja/roulette/",
    },
    "team": {
        "game": "/games/team/",
        "en": "/team-generator/",
        "es": "/es/sorteo-equipos/",
        "pt": "/pt/sorteio-times/",
        "ja": "/ja/team-generator/",
    },
    "dice": {
        "game": "/games/dice/",
        "en": "/dice-roller/",
        "es": "/es/tirar-dados/",
        "pt": "/pt/rolar-dados/",
        "ja": "/ja/saikoro/",
    },
    "bingo": {
        "game": "/games/bingo/",
        "en": "/bingo-caller/",
        "es": "/es/bingo/",
        "pt": "/pt/bingo/",
        "ja": "/ja/bingo/",
    },
    "car-racing": {
        "game": "/games/car-racing/",
        "en": "/race-picker/",
        "es": "/es/carrera-aleatoria/",
        "pt": "/pt/corrida-aleatoria/",
        "ja": "/ja/random-race/",
    },
    "ladder": {
        "game": "/games/ladder/",
        "en": "/ladder-draw/",
        "es": "/es/escalera/",
        "pt": "/pt/escada/",
        "ja": "/ja/amidakuji/",
    },
}

LANGS = ["en", "es", "pt", "ja", "ko"]
OG_LOCALE = {"en": "en_US", "es": "es_ES", "pt": "pt_BR", "ja": "ja_JP", "ko": "ko_KR"}
HTML_LANG = {"en": "en", "es": "es", "pt": "pt", "ja": "ja", "ko": "ko"}


def member(tool, lang):
    """도구 × 언어 → 경로. ko 는 게임 본체."""
    c = CLUSTERS[tool]
    return c["game"] if lang == "ko" else c[lang]


def hreflang_lines(tool, indent="    "):
    """클러스터 5개 언어 + x-default(영어 랜딩) 선언 블록."""
    c = CLUSTERS[tool]
    out = ['%s<link rel="alternate" hreflang="%s" href="%s%s">' % (indent, lg, BASE, member(tool, lg))
           for lg in LANGS]
    out.append('%s<link rel="alternate" hreflang="x-default" href="%s%s">' % (indent, BASE, c["en"]))
    return "\n".join(out)


def all_paths():
    """sitemap 용 — 클러스터가 만들어내는 모든 경로."""
    paths = []
    for tool in CLUSTERS:
        for lg in LANGS:
            paths.append(member(tool, lg))
    return paths
