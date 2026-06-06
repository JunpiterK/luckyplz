#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inject the shared /css/daily.css override link into auto-published 증시 posts.

Idempotent + marker-fenced (lp-daily-css). The link is placed right before
</head>, AFTER the blog-desktop.css link, so daily.css loads last and its
rules win over each post's inline <style>. /css/* is served no-store, so once
the link is in place, future daily.css edits reach every post with no re-inject
and no cache bump.

Usage:
  python scripts/inject-daily-css.py            # all stock posts
  python scripts/inject-daily-css.py --preview  # only the latest date's posts
  python scripts/inject-daily-css.py a/index.html b/index.html   # explicit files
"""
import sys, re, io, json, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG = os.path.join(ROOT, "public", "blog")
START = "<!-- lp-daily-css:start -->"
END = "<!-- lp-daily-css:end -->"

def build_stamp():
    try:
        return json.load(io.open(os.path.join(ROOT, "public", "build.json"), encoding="utf-8"))["v"]
    except Exception:
        return "1"

def is_stock(name):
    b = os.path.basename(name)
    return bool(re.match(r'^(us|kr|cn)-', b)) and any(x in b for x in (
        'recap','brief','wrap','premarket','open','close','session','markets'))

def stock_index_files():
    out = []
    for d in os.listdir(BLOG):
        p = os.path.join(BLOG, d, "index.html")
        if is_stock(d) and os.path.isfile(p):
            out.append(p)
    return sorted(out)

def latest_date_files():
    files = stock_index_files()
    dates = sorted({m.group(0) for f in files for m in [re.search(r'\d{4}-\d{2}-\d{2}', f)] if m})
    if not dates:
        return []
    latest = dates[-1]
    return [f for f in files if latest in f]

def inject(path, stamp):
    s = io.open(path, encoding="utf-8").read()
    link = f'{START}\n<link rel="stylesheet" href="/css/daily.css?v={stamp}">\n{END}'
    if START in s:
        # refresh stamp
        s2 = re.sub(re.escape(START) + r".*?" + re.escape(END), link, s, count=1, flags=re.S)
        if s2 == s:
            return "skip"
        io.open(path, "w", encoding="utf-8", newline="\n").write(s2)
        return "refresh"
    if "</head>" not in s:
        return "no-head"
    s = s.replace("</head>", link + "\n</head>", 1)
    io.open(path, "w", encoding="utf-8", newline="\n").write(s)
    return "inject"

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    stamp = build_stamp()
    if args:
        files = args
    elif "--preview" in flags:
        files = latest_date_files()
    else:
        files = stock_index_files()
    counts = {}
    for f in files:
        r = inject(f, stamp)
        counts[r] = counts.get(r, 0) + 1
    print(f"daily.css inject (v={stamp}): {len(files)} files ->", dict(counts))

if __name__ == "__main__":
    main()
