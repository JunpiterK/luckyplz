#!/usr/bin/env python3
"""Retrofit the shared blog script-chain into orphan posts.

Some older manual longform posts (the Anthropic Story / AI-explained series,
etc.) were authored before the shared blog infrastructure existed. They load
NEITHER adsbygoogle.js NOR siteFooter.js, so they:
  - show zero ads (highest-RPM content on the site, fully unmonetized)
  - have no GA4 tracking
  - have no related-posts internal links, no subscribe form, no site footer

This injects the canonical chain — AdSense + GA4 + the blog script bundle —
just before </body>, fenced by markers so it is idempotent and removable.
After running this, run inject-blog-ads.py to drop the actual ad mount inside
the article body (these posts then resolve to the footnotes/footer anchor).

Idempotent: skips any file already containing the marker or siteFooter.js.
Cache stamps (?v=) are rewritten by scripts/bump-cache.sh on the next bump.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "public" / "blog"
STAMP = json.loads((ROOT / "public" / "build.json").read_text())["v"]

START = "<!-- lp-infra:start -->"
END = "<!-- lp-infra:end -->"

BLOCK = f"""{START}
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5370817769801923" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NZDPE3H3DQ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-NZDPE3H3DQ');</script>
<script src="/js/blogReadingAids.js?v={STAMP}"></script>
<script src="/blog/posts.js?v={STAMP}"></script>
<script src="/js/blogReactions.js?v={STAMP}"></script>
<script src="/js/blogSubscribe.js?v={STAMP}"></script>
<script src="/js/blogRelated.js?v={STAMP}"></script>
<script src="/js/siteFooter.js?v={STAMP}"></script>
{END}"""


def needs_infra(html):
    return ("siteFooter.js" not in html) and ("adsbygoogle.js" not in html)


def main():
    apply = "--apply" in sys.argv
    retrofit = skipped = 0
    targets = []
    for path in sorted(BLOG.glob("*/index.html")):
        html = path.read_text(encoding="utf-8")
        if START in html:
            skipped += 1
            continue
        if not needs_infra(html):
            continue
        if "</body>" not in html:
            print(f"  [warn] no </body>: {path.parent.name}")
            continue
        new = html.replace("</body>", BLOCK + "\n</body>", 1)
        if apply:
            path.write_text(new, encoding="utf-8")
        retrofit += 1
        targets.append(path.parent.name)

    mode = "APPLIED" if apply else "DRY-RUN (pass --apply to write)"
    print(f"[{mode}]")
    print(f"  retrofitted infra : {retrofit}")
    print(f"  already had marker: {skipped}")
    if targets:
        print("   sample:", ", ".join(targets[:12]))


if __name__ == "__main__":
    main()
