#!/usr/bin/env python3
"""Idempotent injector: add a blog-article AdSense mount to every post that
loads the ad infrastructure but has no `data-lp-ad` container yet.

Why this exists
---------------
The bulk of the blog (daily auto-published stocks/sports recaps + several
manual posts) loads adsbygoogle.js + siteFooter.js but never had a
`<div data-lp-ad="blog">` mount, so AdSense delivered ZERO ads on ~75% of
pages while still paying the script weight. This walks every
public/blog/<slug>/index.html, and where the page can actually render an ad
(adsbygoogle.js OR siteFooter.js present) but lacks a mount, it inserts one
inside the article body, just before the closing/footer block.

Idempotent: re-running skips any page that already contains `data-lp-ad`
(whether hand-placed or previously injected). Safe to run after every new
batch of posts.

Posts that load NEITHER adsbygoogle NOR siteFooter are *orphans* (older
pre-infra manual posts) — they are reported and skipped here, because a mount
alone would render nothing. They need the full script-chain retrofit handled
separately (see inject-blog-infra.py).

Anchor priority (insert the mount immediately BEFORE the first match), chosen
so the ad lands at the end of the article body, after the reader has consumed
the content and before disclaimers/related/footer:
  1. <div class="footer-disclaimer">   (daily template)
  2. <footer class="foot">             (worldcup / sports manual)
  3. <div class="footnotes">           (manual series longform)
  4. <div class="series-nav">          (manual series longform)
  5. <footer                           (generic)
  6. <script src="/js/blogRelated.js"  (last-resort: just above the script chain)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "public" / "blog"

AD_DIV = '<div data-lp-ad="blog" style="margin:24px 16px;"></div>'
MARKER = "data-lp-ad"

# (regex, label) in priority order. First hit wins. Insert AD_DIV before match.
ANCHORS = [
    (re.compile(r'<div class="footer-disclaimer">'), "footer-disclaimer"),
    (re.compile(r'<footer class="foot">'), "footer.foot"),
    (re.compile(r'<div class="footnotes">'), "footnotes"),
    (re.compile(r'<div class="series-nav">'), "series-nav"),
    (re.compile(r'<div class="related">'), "related"),
    (re.compile(r'<footer[ >]'), "footer-generic"),
    (re.compile(r'<script src="/(?:js|blog)/blogRelated\.js'), "blogRelated"),
]


def has_ad_infra(html):
    return ("adsbygoogle.js" in html) or ("siteFooter.js" in html)


def main():
    apply = "--apply" in sys.argv
    injected = skipped_have = skipped_orphan = no_anchor = 0
    orphans = []
    no_anchor_files = []

    for path in sorted(BLOG.glob("*/index.html")):
        html = path.read_text(encoding="utf-8")
        if MARKER in html:
            skipped_have += 1
            continue
        if not has_ad_infra(html):
            skipped_orphan += 1
            orphans.append(path.parent.name)
            continue
        for rx, _label in ANCHORS:
            m = rx.search(html)
            if m:
                new = html[:m.start()] + AD_DIV + "\n" + html[m.start():]
                if apply:
                    path.write_text(new, encoding="utf-8")
                injected += 1
                break
        else:
            no_anchor += 1
            no_anchor_files.append(path.parent.name)

    mode = "APPLIED" if apply else "DRY-RUN (pass --apply to write)"
    print(f"[{mode}]")
    print(f"  injected ad mount : {injected}")
    print(f"  already had ad    : {skipped_have}")
    print(f"  orphan (no infra) : {skipped_orphan}  -> need inject-blog-infra.py")
    print(f"  infra but NO anchor: {no_anchor}")
    if no_anchor_files:
        print("   anchorless:", ", ".join(no_anchor_files[:20]))
    if orphans:
        print("   orphans sample:", ", ".join(orphans[:12]), "...")


if __name__ == "__main__":
    main()
