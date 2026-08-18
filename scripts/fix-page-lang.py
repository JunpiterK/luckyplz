# -*- coding: utf-8 -*-
"""게임 페이지 언어 선언 정합화 (2026-08-19).

측정된 문제:
    한국어 title·본문·FAQ 를 가진 게임 페이지가 `<html lang="en">` 과
    `hreflang="en"` 을 선언하고 있었다(roulette·team·dice·bingo·ladder).
    구글에 "이 URL 이 영어판"이라고 말하는 셈이라, 영어 검색자에게 한국어
    페이지가 노출될 수 있고 실제 영어판(`/wheel-spinner/` 등)과 신호가
    충돌한다.

조치:
    1) 본문 언어를 title 기준으로 판정해 `<html lang>` · `og:locale` 정렬
    2) 메인 6종은 5개 언어 클러스터의 **ko 멤버**로 상호 hreflang 선언
       (en=랜딩 / ko=게임 본체 / es·pt·ja=번역 랜딩)
    3) 나머지 11종은 자기참조 hreflang 만 남긴다

멱등. 몇 번을 돌려도 같은 결과.

    python scripts/fix-page-lang.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUB = ROOT / "public"
BASE = "https://luckyplz.com"

# 클러스터 정의는 scripts/lp_clusters.py 단일 진실원천에서 가져온다.
# 여기서 재정의하면 두 파일이 어긋나 hreflang 상호 선언이 깨진다.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lp_clusters import CLUSTERS, hreflang_lines, OG_LOCALE  # noqa: E402

ALL_GAMES = sorted(p.parent.name for p in PUB.glob("games/*/index.html"))

def page_lang(html_text):
    """title 에 한글이 있으면 한국어 페이지로 본다. 게임 UI 는 16개 언어를
    클라이언트에서 전환하지만, 색인되는 것은 서버가 내려준 본문이다."""
    m = re.search(r"<title>([^<]*)</title>", html_text)
    if m and re.search(r"[가-힣]", m.group(1)):
        return "ko"
    return "en"


def hreflang_block(game, lang, indent="    "):
    """클러스터 멤버면 5개 언어 상호 선언, 아니면 자기참조만."""
    if game in CLUSTERS:
        return hreflang_lines(game, indent)
    self_url = "%s/games/%s/" % (BASE, game)
    return "\n".join([
        '%s<link rel="alternate" hreflang="%s" href="%s">' % (indent, lang, self_url),
        '%s<link rel="alternate" hreflang="x-default" href="%s">' % (indent, self_url),
    ])


def main():
    changed = 0
    for game in ALL_GAMES:
        f = PUB / "games" / game / "index.html"
        s = f.read_text(encoding="utf-8")
        o = s
        lang = page_lang(s)

        # 1) <html lang>
        s = re.sub(r'<html lang="[^"]*"', '<html lang="%s"' % lang, s, count=1)

        # 2) og:locale — 없으면 og:type 뒤에 삽입, 있으면 교체
        if re.search(r'<meta property="og:locale"', s):
            s = re.sub(r'<meta property="og:locale" content="[^"]*"',
                       '<meta property="og:locale" content="%s"' % OG_LOCALE[lang], s, count=1)
        else:
            s = re.sub(r'(<meta property="og:type" content="[^"]*">)',
                       r'\1\n<meta property="og:locale" content="%s">' % OG_LOCALE[lang], s, count=1)

        # 3) hreflang 블록 전체 교체 — 기존 alternate 줄을 지우고 새로 넣는다
        alts = list(re.finditer(r'[ \t]*<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n', s))
        indent = "    "
        if alts:
            m0 = re.match(r'([ \t]*)', alts[0].group(0))
            indent = m0.group(1) or "    "
            start, end = alts[0].start(), alts[-1].end()
            s = s[:start] + hreflang_block(game, lang, indent) + "\n" + s[end:]
        else:
            # alternate 가 아예 없던 페이지(bingo) — canonical 뒤에 붙인다
            s = re.sub(r'(<link rel="canonical" href="[^"]*">\n)',
                       lambda m: m.group(1) + hreflang_block(game, lang, indent) + "\n", s, count=1)

        if s != o:
            f.write_text(s, encoding="utf-8")
            changed += 1
        print("%-17s lang=%-3s cluster=%s" % (game, lang, "Y" if game in CLUSTERS else "-"))
    print("\n수정한 파일: %d / %d" % (changed, len(ALL_GAMES)))


if __name__ == "__main__":
    main()
