#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retroactively add the '기준 시점 스냅샷' badge to existing daily stock posts.

Daily prices are baked at publish time. This badge makes that explicit — for
close recaps it's definitionally final; for open / pre-market briefs the
snapshot is mid-session, so those get a 'see live price' link to the market
index. The article's own numbers are never touched (the prose interprets them).

New posts get this from the daily-base.html template + auto-daily-post.py's
snapshot_note(); this script covers the ~370 already-published stock posts.
Uses inline styles (older posts predate the .snapshot-note CSS rule).

Scope: stock dailies only — <market>-<...>-YYYY-MM-DD[-lang]. Sports dailies
are excluded (their scores are final results, not a moving snapshot).
Idempotent: skips any post already carrying a snapshot-note.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "public" / "blog"

STOCK_DIR_RE = re.compile(r"^(us|kr|cn)-.+-(20\d\d-\d\d-\d\d)(-(en|ja|zh))?$")
ANCHOR_RE = re.compile(r'(<div class="disclaimer-top">.*?</div>)', re.DOTALL)

LIVE_URL = {
    "us": "https://www.google.com/finance/quote/.INX:INDEXSP",
    "kr": "https://www.google.com/finance/quote/KOSPI:KRX",
    "cn": "https://www.google.com/finance/quote/000001:SHA",
}
NOTE = {
    "ko": "이 글의 수치는 <b>{d} 발행 시점</b>에 고정된 스냅샷입니다. 실시간 시세가 아닙니다.",
    "en": "These figures are a snapshot fixed at publication on <b>{d}</b>. Not a live quote.",
    "ja": "本記事の数値は<b>{d} 公開時点</b>で固定されたスナップショットです。リアルタイム値ではありません。",
    "zh": "本文数据为<b>{d} 发布时点</b>固定的快照，非实时行情。",
}
LIVE_LABEL = {"ko": "실시간 현재가 보기", "en": "See live price",
              "ja": "現在値を見る", "zh": "查看实时行情"}

WRAP = ('<div class="snapshot-note" style="margin:0 16px 14px;padding:10px 13px;'
        'background:rgba(255,255,255,.03);border:1px solid #1e2d45;'
        'border-left:3px solid #ffd166;border-radius:7px;font-size:12px;'
        'color:#9fb0c2;line-height:1.5">📌 {body}</div>')
LINK = (' <a href="{url}" target="_blank" rel="noopener" '
        'style="color:#00e5ff;text-decoration:none;font-weight:700;white-space:nowrap">{label} →</a>')


def parse(slug):
    m = STOCK_DIR_RE.match(slug)
    if not m:
        return None
    market, date, _, lang = m.group(1), m.group(2), m.group(3), m.group(4)
    lang = lang or "ko"
    intraday = ("open-brief" in slug) or ("premarket" in slug)
    return market, date, lang, intraday


def badge_html(market, date, lang, intraday):
    body = NOTE[lang].format(d=date)
    if intraday:
        body += LINK.format(url=LIVE_URL[market], label=LIVE_LABEL[lang])
    return WRAP.format(body=body)


def main():
    apply = "--apply" in sys.argv
    done = skipped = no_anchor = 0
    for path in sorted(BLOG.glob("*/index.html")):
        slug = path.parent.name
        info = parse(slug)
        if not info:
            continue
        html = path.read_text(encoding="utf-8")
        if "snapshot-note" in html:
            skipped += 1
            continue
        m = ANCHOR_RE.search(html)
        if not m:
            no_anchor += 1
            continue
        badge = badge_html(*info)
        new = html[:m.end()] + "\n" + badge + html[m.end():]
        if apply:
            path.write_text(new, encoding="utf-8")
        done += 1
    mode = "APPLIED" if apply else "DRY-RUN (pass --apply)"
    print(f"[{mode}]  injected: {done}  already-had: {skipped}  no-anchor: {no_anchor}")


if __name__ == "__main__":
    main()
