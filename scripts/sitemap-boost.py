"""sitemap-boost.py
=================
One-shot sitemap upgrade to fix Search Console "discovered - not indexed" stalls.

WHAT IT DOES
------------
1. Adds <lastmod>2026-05-07</lastmod> to every <url> block that doesn't have one.
   Google uses lastmod as a strong freshness signal — without it, the crawler
   has no idea whether a page changed, so it deprioritizes the URL in its
   queue. Every "discovered - not indexed" page in our Search Console can be
   traced back to this missing signal.
2. Inserts the 5 new Korean core blog posts (presentation-order-fair, etc.)
   right after the /blog/ index entry, so they share crawl priority with
   the existing core lifestyle posts.

This script is idempotent — running it twice is safe; the second run sees
all <lastmod> tags already present and does nothing on that side. New URL
inserts are also guarded by a simple "already in file?" check.
"""
import re
import sys
from pathlib import Path

SITEMAP = Path(__file__).resolve().parent.parent / 'public' / 'sitemap.xml'
TODAY = '2026-05-07'

NEW_BLOG_POSTS = [
    'presentation-order-fair',
    'wedding-mc-games',
    'elementary-team-grouping',
    'club-seating-fair',
    'picnic-game-ideas',
]

NEW_URL_TEMPLATE = """    <url>
        <loc>https://luckyplz.com/blog/{slug}/</loc>
        <lastmod>{date}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.75</priority>
    </url>
"""


def add_lastmod(content: str, date: str) -> tuple[str, int]:
    """Inject <lastmod> right after every <loc> that doesn't already have one.

    Returns (new_content, count_added).
    """
    added = 0

    def repl(match: re.Match) -> str:
        nonlocal added
        url_block = match.group(0)
        if '<lastmod>' in url_block:
            return url_block
        # Insert lastmod right after the closing </loc> tag.
        new_block = re.sub(
            r'(</loc>)',
            r'\1\n        <lastmod>' + date + '</lastmod>',
            url_block,
            count=1,
        )
        added += 1
        return new_block

    new_content = re.sub(
        r'<url>.*?</url>',
        repl,
        content,
        flags=re.DOTALL,
    )
    return new_content, added


def insert_new_posts(content: str, date: str, slugs: list[str]) -> tuple[str, int]:
    """Insert new blog post URL blocks after the /blog/ index entry."""
    blocks = []
    inserted = 0
    for slug in slugs:
        url = f'https://luckyplz.com/blog/{slug}/'
        if url in content:
            continue  # already in sitemap
        blocks.append(NEW_URL_TEMPLATE.format(slug=slug, date=date))
        inserted += 1

    if not blocks:
        return content, 0

    payload = '\n' + ''.join(blocks).rstrip() + '\n'

    # Insert right after the /blog/ index entry's closing </url>.
    pattern = re.compile(
        r'(<url>\s*<loc>https://luckyplz\.com/blog/</loc>.*?</url>)',
        re.DOTALL,
    )
    new_content, n = pattern.subn(r'\1' + payload, content, count=1)
    if n != 1:
        raise RuntimeError("Couldn't find /blog/ index entry to insert after")
    return new_content, inserted


def main() -> int:
    src = SITEMAP.read_text(encoding='utf-8')

    # 1. Add the new blog posts first (so they get the lastmod treatment too).
    src, inserted = insert_new_posts(src, TODAY, NEW_BLOG_POSTS)

    # 2. Inject <lastmod> into every URL block missing it.
    src, added = add_lastmod(src, TODAY)

    SITEMAP.write_text(src, encoding='utf-8')
    print(f'OK  inserted {inserted} new URL block(s)')
    print(f'OK  added <lastmod>{TODAY}</lastmod> to {added} URL block(s)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
