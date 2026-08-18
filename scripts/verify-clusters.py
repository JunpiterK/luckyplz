# -*- coding: utf-8 -*-
"""언어 클러스터 전수 검증 (2026-08-19).

hreflang 은 상호 선언이 한 변이라도 어긋나면 구글이 그 클러스터를 통째로
무시한다. 즉 "대충 맞음"이라는 상태가 없다. 6 도구 × 5 언어 = 30 페이지가
서로를 빠짐없이 가리키는지 기계적으로 확인한다.

검사 항목:
    1. 파일 존재
    2. canonical 이 자기 자신(self-referential)
    3. hreflang 5개 언어 + x-default 를 모두 선언
    4. 선언한 URL 이 클러스터 정의와 정확히 일치 (상호성)
    5. <html lang> 이 그 멤버의 언어와 일치
    6. FAQPage 스키마와 화면 Q&A 가 1:1
    7. JSON-LD 파싱

    python scripts/verify-clusters.py
"""
import html as htmllib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lp_clusters import CLUSTERS, LANGS, BASE, member  # noqa: E402

fails = []


def fail(where, msg):
    fails.append("%s: %s" % (where, msg))


def visible_faq(t):
    """화면 Q&A 추출. 세 가지 마크업을 모두 지원한다 —
    <details> (랜딩) / <dl class="lp-faq"> (게임) / <dl class="lp-seo-faq"> (홈).
    "Q. " 접두어는 화면 표시용 라벨이라 비교 전에 뗀다. scripts/sync-faq-schema.py
    가 스키마를 만들 때와 같은 규칙이어야 한다."""
    scope = None
    for pat in (r'<div class="faq">(.*?)</div>', r'<div class="lp-faq-list">(.*?)</div>'):
        m = re.search(pat, t, re.S)
        if m:
            scope = m.group(1)
            break
    out = [(q, a) for q, a in re.findall(
        r"<details><summary>(.*?)</summary><p>(.*?)</p></details>",
        scope if scope is not None else "", re.S)]
    if not out:
        m = re.search(r'<dl class="lp-(?:seo-)?faq">(.*?)</dl>', t, re.S)
        if m:
            dts = re.findall(r"<dt>(.*?)</dt>", m.group(1), re.S)
            dds = re.findall(r"<dd>(.*?)</dd>", m.group(1), re.S)
            if len(dts) == len(dds):
                out = list(zip(dts, dds))
    return [(re.sub(r"^Q\s*[.:]\s*", "", strip(q)), strip(a)) for q, a in out]


def strip(x):
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", "", x))).strip()


def check(tool, lang):
    path = member(tool, lang)
    where = "%s/%s" % (tool, lang)
    f = ROOT / "public" / path.strip("/") / "index.html"
    if not f.exists():
        fail(where, "파일 없음 %s" % path)
        return
    t = f.read_text(encoding="utf-8")

    # 2. canonical self-referential
    m = re.search(r'<link rel="canonical" href="([^"]+)"', t)
    if not m:
        fail(where, "canonical 없음")
    elif m.group(1) != BASE + path:
        fail(where, "canonical 불일치: %s (기대 %s)" % (m.group(1), BASE + path))

    # 3~4. hreflang 상호성
    alts = dict(re.findall(r'<link rel="alternate" hreflang="([a-z-]+)" href="([^"]+)"', t))
    for lg in LANGS:
        want = BASE + member(tool, lg)
        if lg not in alts:
            fail(where, "hreflang=%s 선언 없음" % lg)
        elif alts[lg] != want:
            fail(where, "hreflang=%s 대상 불일치: %s (기대 %s)" % (lg, alts[lg], want))
    if "x-default" not in alts:
        fail(where, "x-default 없음")
    elif alts["x-default"] != BASE + CLUSTERS[tool]["en"]:
        fail(where, "x-default 가 영어판을 안 가리킴: %s" % alts["x-default"])

    # 5. <html lang>
    hl = re.search(r'<html lang="([^"]+)"', t)
    if not hl or hl.group(1) != lang:
        fail(where, "html lang=%s (기대 %s)" % (hl.group(1) if hl else "없음", lang))

    # 7. JSON-LD 파싱 + 6. FAQ 1:1
    schema = None
    for mm in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
        try:
            d = json.loads(mm.group(1))
        except Exception as e:
            fail(where, "JSON-LD 파싱 실패: %s" % str(e)[:50])
            continue
        if d.get("@type") == "FAQPage":
            schema = [(strip(q["name"]), strip(q["acceptedAnswer"]["text"])) for q in d["mainEntity"]]
    vis = visible_faq(t)
    if schema is None:
        fail(where, "FAQPage 스키마 없음")
    elif len(schema) != len(vis):
        fail(where, "FAQ 개수 불일치: 스키마 %d / 화면 %d" % (len(schema), len(vis)))
    else:
        for i, ((sq, sa), (vq, va)) in enumerate(zip(schema, vis)):
            if sq != vq or sa != va:
                fail(where, "FAQ #%d 스키마-화면 불일치" % (i + 1))


def main():
    n = 0
    for tool in CLUSTERS:
        for lang in LANGS:
            check(tool, lang)
            n += 1
    print("검사 대상: %d 페이지 (%d 도구 × %d 언어)" % (n, len(CLUSTERS), len(LANGS)))
    if fails:
        print("\n실패 %d건:" % len(fails))
        for x in fails:
            print("  -", x)
        sys.exit(1)
    print("전 항목 통과 — canonical 자기참조 · hreflang 상호성 · html lang · FAQ 1:1 · JSON-LD")


if __name__ == "__main__":
    main()
