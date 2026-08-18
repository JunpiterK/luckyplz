# -*- coding: utf-8 -*-
"""FAQPage 스키마를 화면 내용으로부터 재생성한다 (2026-08-19).

왜 필요한가:
    구글 FAQPage 요건은 "스키마의 Q&A 가 페이지에 실제로 보일 것"이다.
    손으로 쓴 영어 랜딩 3종은 스키마와 화면 문구가 서로 다르게 흘러가
    있었다(같은 뜻의 다른 문장). 화면에 없는 Q&A 를 스키마에 넣은 것과
    같아 리치결과 박탈이나 수동 조치 대상이 된다.
    `/games/ladder/` 는 반대로 화면에 Q&A 6개가 있는데 스키마가 없어
    17종 중 유일하게 리치결과 자격을 못 갖추고 있었다.

방향:
    **화면이 진실원천**이다. 스키마를 화면에 맞춘다. 반대로 하면 사람이
    읽는 문장을 기계 사정으로 고치게 되고, 결국 또 어긋난다.

지원 마크업:
    <details><summary>Q</summary><p>A</p></details>   랜딩 페이지
    <dl class="lp-faq"><dt>Q. …</dt><dd>A</dd></dl>    게임 페이지
    <dl class="lp-seo-faq">…</dl>                      홈·언어판

    "Q. " 접두어는 화면 표시용 라벨이라 스키마에서는 뗀다 — 나머지 16개
    게임이 이미 그 규칙으로 되어 있어 맞춘다.

멱등. 인자 없이 돌리면 대상 전체를 훑는다.

    python scripts/sync-faq-schema.py [경로 ...]
"""
import html as htmllib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUB = ROOT / "public"

# 기본 대상: 화면 FAQ 를 가진 페이지 전부
DEFAULT = (sorted(PUB.glob("games/*/index.html"))
           + [PUB / "index.html"]
           + [PUB / p / "index.html" for p in
              ("ko", "ja", "es", "pt",
               "wheel-spinner", "team-generator", "dice-roller",
               "bingo-caller", "race-picker", "ladder-draw")]
           + sorted(PUB.glob("es/*/index.html"))
           + sorted(PUB.glob("pt/*/index.html"))
           + sorted(PUB.glob("ja/*/index.html")))


def text(x):
    """태그·엔티티 제거 후 공백 정규화."""
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", "", x))).strip()


def extract(t):
    """화면 Q&A 추출. 없으면 빈 리스트.

    반드시 **FAQ 컨테이너 안**만 본다. 홈에는 FAQ 말고도 접히는 <details>
    (본문 폴드)가 있어서, 문서 전체에서 <details> 를 긁으면 FAQ 가 아닌
    블록까지 스키마에 들어간다. 컨테이너로 범위를 좁혀 그걸 막는다."""
    scope = None
    for pat in (r'<div class="faq">(.*?)</div>',        # 도구 랜딩
                r'<div class="lp-faq-list">(.*?)</div>'):  # 홈·언어판
        m = re.search(pat, t, re.S)
        if m:
            scope = m.group(1)
            break
    pairs = re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>",
                       scope if scope is not None else "", re.S)
    if not pairs:
        m = re.search(r'<dl class="lp-(?:seo-)?faq">(.*?)</dl>', t, re.S)  # 게임 페이지
        if not m:
            return []
        dts = re.findall(r"<dt>(.*?)</dt>", m.group(1), re.S)
        dds = re.findall(r"<dd>(.*?)</dd>", m.group(1), re.S)
        if len(dts) != len(dds):
            return []
        pairs = list(zip(dts, dds))
    out = []
    for q, a in pairs:
        q = text(q)
        # 화면 표시용 접두어 제거 — "Q. ", "Q." , "Q "
        q = re.sub(r"^Q\s*[.:]\s*", "", q)
        out.append((q, text(a)))
    return out


def sync(f):
    t = f.read_text(encoding="utf-8")
    qa = extract(t)
    rel = f.relative_to(ROOT)
    if not qa:
        return "화면 FAQ 없음 — 건너뜀", False

    lang = (re.search(r'<html lang="([^"]+)"', t) or [None, "en"])[1]
    payload = {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": lang,
               "mainEntity": [{"@type": "Question", "name": q,
                               "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}
    block = '<script type="application/ld+json">%s</script>' % json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"))

    # 기존 FAQPage 스크립트 블록 찾기
    target = None
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
        try:
            if json.loads(m.group(1)).get("@type") == "FAQPage":
                target = m
                break
        except Exception:
            continue

    if target:
        new = t[:target.start()] + block + t[target.end():]
        action = "스키마 갱신 (%d문항)" % len(qa)
    else:
        # 없으면 canonical 뒤에 새로 삽입
        m = re.search(r'<link rel="canonical" href="[^"]*">\n', t)
        if not m:
            return "canonical 없어 삽입 위치 불명 — 건너뜀", False
        new = t[:m.end()] + block + "\n" + t[m.end():]
        action = "스키마 신규 추가 (%d문항)" % len(qa)

    if new == t:
        return "변경 없음 (%d문항)" % len(qa), False
    f.write_text(new, encoding="utf-8")
    return action, True


def main():
    targets = [Path(a) for a in sys.argv[1:]] or DEFAULT
    changed = 0
    for f in targets:
        if not f.exists():
            print("%-45s 파일 없음" % str(f))
            continue
        msg, did = sync(f)
        changed += did
        print("%-45s %s" % (str(f.relative_to(ROOT)), msg))
    print("\n변경: %d개 파일" % changed)


if __name__ == "__main__":
    main()
