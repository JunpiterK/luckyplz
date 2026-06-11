#!/usr/bin/env python3
"""Take ephemeral daily auto-posts OUT of the search index (AdSense thin-content hedge).

Decision (2026-06-11): the daily auto-published market recaps/briefs (and the
daily sports posts) are programmatically generated at scale, near-duplicate
across 4 languages, and have a ~48h useful life. As a block they fit Google's
"scaled content abuse" profile, and that risk is enforced at the DOMAIN level
— it could pull ads from the whole site, including the games and the manual
longform. They also carry almost no durable search value individually.

So: mark every daily auto-post `noindex,follow` (drops them from the index and
the scaled-content count; ads still serve; users/links unaffected) and remove
them from sitemap.xml (no "submitted URL marked noindex" GSC warnings, no
mixed signals). Durable SEO instead concentrates on a human-curated weekly
consolidated recap (separate, indexable).

Scope = posts whose category is stocks/football/baseball AND whose slug carries
a YYYY-MM-DD date. Manual analysis in the stocks category (e.g.
ppi-10-prints-2026-may-analysis) has no daily date and stays indexed.

Idempotent: skips HTML already carrying a noindex robots meta; skips sitemap
blocks already gone. Re-run after each batch of new daily posts (or just keep
the robots meta in daily-base.html, which this script's companion edit adds so
future posts ship noindex from birth).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "public" / "blog"
POSTS_JS = BLOG / "posts.js"
SITEMAP = ROOT / "public" / "sitemap.xml"

ROBOTS_META = '<meta name="robots" content="noindex,follow">'
ANCHOR = '<meta http-equiv="Expires" content="0">'
DAILY_CATS = {"stocks", "football", "baseball"}
DATE_RE = re.compile(r"20\d\d-\d\d-\d\d")


# A daily auto-post directory is deterministically named:
#   <market>-<type>-YYYY-MM-DD[-lang]   (market = us|kr|cn; stocks)
#   <sport>-daily-YYYY-MM-DD[-lang]     (sport = baseball|football)
# This filesystem rule is the source of truth for *which HTML files exist*
# (what we actually edit), and it cleanly excludes manual analysis in the
# same categories — those carry no YYYY-MM-DD daily date (e.g.
# ppi-10-prints-2026-may-analysis, ai-power-supply-5year-2030).
DAILY_DIR_RE = re.compile(
    r"^((us|kr|cn)-.+|(baseball|football)-daily)-20\d\d-\d\d-\d\d(-(en|ja|zh))?$"
)


def daily_slugs():
    """Daily auto-post slugs = blog directories whose name matches the
    deterministic daily naming pattern. No posts.js / node dependency."""
    return {
        d.name for d in BLOG.iterdir()
        if d.is_dir() and DAILY_DIR_RE.match(d.name)
    }


def inject_noindex(slugs, apply):
    done = skipped = missing = 0
    for slug in sorted(slugs):
        path = BLOG / slug / "index.html"
        if not path.exists():
            missing += 1
            continue
        html = path.read_text(encoding="utf-8")
        if 'name="robots"' in html and "noindex" in html:
            skipped += 1
            continue
        if ANCHOR not in html:
            missing += 1
            continue
        new = html.replace(ANCHOR, ANCHOR + "\n" + ROBOTS_META, 1)
        if apply:
            path.write_text(new, encoding="utf-8")
        done += 1
    return done, skipped, missing


def prune_sitemap(slugs, apply):
    if not SITEMAP.exists():
        return 0, 0
    xml = SITEMAP.read_text(encoding="utf-8")
    # Split keeping the <url> ... </url> blocks intact.
    parts = re.split(r"(<url>.*?</url>)", xml, flags=re.DOTALL)
    slug_locs = {f"/blog/{s}/" for s in slugs}
    kept, removed = [], 0
    for part in parts:
        if part.startswith("<url>"):
            m = re.search(r"<loc>https://luckyplz\.com(/blog/[^<]+?)</loc>", part)
            if m and m.group(1) in slug_locs:
                removed += 1
                continue
        kept.append(part)
    new_xml = "".join(kept)
    # collapse any blank-line runs left by removed blocks
    new_xml = re.sub(r"\n[ \t]*\n[ \t]*\n+", "\n", new_xml)
    if apply:
        SITEMAP.write_text(new_xml, encoding="utf-8")
    return removed, len(slug_locs)


def main():
    apply = "--apply" in sys.argv
    slugs = daily_slugs()
    print(f"daily auto-post slugs: {len(slugs)}")
    d, s, m = inject_noindex(slugs, apply)
    print(f"  noindex injected : {d}")
    print(f"  already noindex  : {s}")
    print(f"  missing/no-anchor: {m}")
    rem, tot = prune_sitemap(slugs, apply)
    print(f"  sitemap blocks removed: {rem}")
    print("[APPLIED]" if apply else "[DRY-RUN] pass --apply to write")


if __name__ == "__main__":
    main()
