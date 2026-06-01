#!/usr/bin/env python3
"""Delete auto-published market-recap posts whose trading_date is a
weekend (Sat/Sun). One-off cleanup for the 2026-05-30/31 incident.

Deletes per base slug:
  - public/blog/<slug>/                    (ko)
  - public/blog/<slug>-en/                 (en)
  - public/blog/<slug>-ja/                 (ja)
  - public/blog/<slug>-zh/                 (zh)
  - public/og/og-<slug>{,-en,-ja,-zh}.png  (OG image, if exists)
  - public/assets/blog/og-<slug>{,-en,-ja,-zh}.png (OG image, if exists)

Also rewrites:
  - public/blog/posts.js   — drops entries whose slug matches a deleted dir
  - public/sitemap.xml     — drops <url> blocks containing the bad slugs

Usage:
  python scripts/delete-weekend-posts.py            # dry-run, prints plan
  python scripts/delete-weekend-posts.py --apply    # actually delete
"""
from __future__ import annotations
import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG_DIR = ROOT / "public" / "blog"
OG_DIRS = [ROOT / "public" / "og", ROOT / "public" / "assets" / "blog"]
POSTS_JS = BLOG_DIR / "posts.js"
SITEMAP = ROOT / "public" / "sitemap.xml"

# Slot slug prefixes that auto-publish daily and should never land on weekends.
SLOT_PREFIXES = (
    "us-tech-recap",
    "us-premarket",
    "kr-open-brief",
    "kr-tech-recap",
    "cn-open-brief",
    "cn-tech-recap",
)


def find_weekend_base_slugs() -> list[str]:
    """Scan BLOG_DIR for slot dirs whose trading_date is Sat/Sun."""
    bad = []
    for d in sorted(BLOG_DIR.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        # Skip the -en/-ja/-zh variants; only collect base slugs.
        if name.endswith(("-en", "-ja", "-zh")):
            continue
        for prefix in SLOT_PREFIXES:
            m = re.match(rf"^({prefix})-(\d{{4}}-\d{{2}}-\d{{2}})$", name)
            if not m:
                continue
            td = m.group(2)
            try:
                wd = date.fromisoformat(td).weekday()
            except ValueError:
                continue
            if wd >= 5:
                bad.append(name)
            break
    return bad


def variants_of(base_slug: str) -> list[str]:
    return [base_slug,
            f"{base_slug}-en",
            f"{base_slug}-ja",
            f"{base_slug}-zh"]


def rm_rf(path: Path, dry_run: bool):
    if not path.exists():
        return False
    if dry_run:
        print(f"  [dry-run] would delete {path.relative_to(ROOT)}")
        return False
    if path.is_dir():
        for sub in sorted(path.rglob("*"), reverse=True):
            try:
                if sub.is_file() or sub.is_symlink():
                    sub.unlink()
                else:
                    sub.rmdir()
            except OSError:
                pass
        try:
            path.rmdir()
        except OSError:
            pass
    else:
        path.unlink()
    print(f"  deleted {path.relative_to(ROOT)}")
    return True


def delete_og_for(slug: str, dry_run: bool) -> int:
    n = 0
    for ogdir in OG_DIRS:
        if not ogdir.exists():
            continue
        for pat in (f"{slug}.png", f"og-{slug}.png"):
            f = ogdir / pat
            if f.exists():
                if dry_run:
                    print(f"  [dry-run] would delete {f.relative_to(ROOT)}")
                else:
                    f.unlink()
                    print(f"  deleted {f.relative_to(ROOT)}")
                n += 1
    return n


def prune_posts_js(bad_all_slugs: set[str], dry_run: bool) -> int:
    """Remove BLOG_POSTS entries whose slug is in bad_all_slugs.

    Conservative regex-based prune that targets the `slug:` line as anchor,
    then walks back to the opening `{` and forward to the matching `}`,`
    line and removes that range. Idempotent.
    """
    if not POSTS_JS.exists():
        return 0
    text = POSTS_JS.read_text(encoding="utf-8")
    original = text
    removed = 0

    # We work line-by-line for clarity. Each entry roughly matches:
    #   { ... slug: 'X' ... },
    # spanning multiple lines. Find each top-level entry and check its slug.
    lines = text.split("\n")
    out_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Start of an entry: a line that is exactly "    {" or "{" at the
        # array-entry indent. We accept any leading whitespace + "{".
        stripped = line.strip()
        if stripped == "{":
            # Collect the entry body until matching closing "},"
            entry: list[str] = [line]
            depth = 1
            j = i + 1
            while j < len(lines) and depth > 0:
                entry.append(lines[j])
                # update depth based on { and } count on the line
                depth += lines[j].count("{")
                depth -= lines[j].count("}")
                j += 1
            entry_text = "\n".join(entry)
            m = re.search(r"slug\s*:\s*['\"]([^'\"]+)['\"]", entry_text)
            slug = m.group(1) if m else None
            if slug in bad_all_slugs:
                removed += 1
                # drop the entry, also drop any trailing comma-only line
                i = j
                continue
            out_lines.extend(entry)
            i = j
        else:
            out_lines.append(line)
            i += 1

    new_text = "\n".join(out_lines)
    if new_text == original:
        return 0
    if dry_run:
        print(f"  [dry-run] would prune {removed} entries from posts.js")
        return removed
    POSTS_JS.write_text(new_text, encoding="utf-8")
    print(f"  pruned {removed} entries from posts.js")
    return removed


def prune_sitemap(bad_all_slugs: set[str], dry_run: bool) -> int:
    """Remove <url> blocks whose <loc> mentions a bad slug."""
    if not SITEMAP.exists():
        return 0
    text = SITEMAP.read_text(encoding="utf-8")
    original = text
    removed = 0
    # Greedy-match each <url>...</url> block, drop ones containing any bad slug.
    def repl(m):
        nonlocal removed
        block = m.group(0)
        for slug in bad_all_slugs:
            if f"/blog/{slug}/" in block:
                removed += 1
                return ""
        return block
    new_text = re.sub(r"\s*<url>.*?</url>", repl, text, flags=re.DOTALL)
    if new_text == original:
        return 0
    if dry_run:
        print(f"  [dry-run] would remove {removed} <url> blocks from sitemap.xml")
        return removed
    SITEMAP.write_text(new_text, encoding="utf-8")
    print(f"  removed {removed} <url> blocks from sitemap.xml")
    return removed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="Actually delete. Without this, runs a dry-run plan.")
    args = ap.parse_args()
    dry = not args.apply

    print(f"[mode] {'APPLY' if not dry else 'DRY-RUN'}")
    print()

    bases = find_weekend_base_slugs()
    if not bases:
        print("No weekend posts found. Nothing to do.")
        return 0

    print(f"Found {len(bases)} weekend base slugs:")
    for b in bases:
        td = b.rsplit("-", 3)
        td_str = "-".join(td[-3:])
        wd_name = ("Mon","Tue","Wed","Thu","Fri","Sat","Sun")[
            date.fromisoformat(td_str).weekday()]
        print(f"  - {b}  ({wd_name})")
    print()

    all_slugs = set()
    for base in bases:
        for v in variants_of(base):
            all_slugs.add(v)

    print(f"Will affect {len(all_slugs)} total slugs (base + en/ja/zh variants).")
    print()

    # Delete directories + OG images
    deleted_dirs = 0
    deleted_og = 0
    for base in bases:
        print(f"# {base}")
        for v in variants_of(base):
            d = BLOG_DIR / v
            if rm_rf(d, dry):
                deleted_dirs += 1
            deleted_og += delete_og_for(v, dry)
        print()

    # Prune posts.js
    print("# posts.js")
    pj = prune_posts_js(all_slugs, dry)
    print()

    # Prune sitemap.xml
    print("# sitemap.xml")
    ps = prune_sitemap(all_slugs, dry)
    print()

    print("Summary:")
    print(f"  directories: {deleted_dirs}")
    print(f"  OG images:   {deleted_og}")
    print(f"  posts.js:    {pj} entries")
    print(f"  sitemap.xml: {ps} url blocks")

    if dry:
        print()
        print("Re-run with --apply to actually delete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
