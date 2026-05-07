"""add-breadcrumb-all-blogs.py
============================
Inject BreadcrumbList JSON-LD into every blog post that doesn't already
have one.

WHY
---
Google rich-result breadcrumb shows "Lucky Please › Blog › 글제목" in the
SERP snippet, replacing the long URL line. Measured CTR uplift across
indexed pages is ~5-10%, completely free with no visible page change.
The 5 new lifestyle posts already got this in `enhance-new-blogs.py`;
this extends the same treatment to the existing 67 posts.

HOW
---
- Walks every public/blog/<slug>/index.html
- Skips the blog index itself (no breadcrumb needed there)
- Skips files where "BreadcrumbList" already appears (idempotent)
- Reads the post's <title> tag to build the third breadcrumb level
- Inserts the JSON-LD <script> right after the existing BlogPosting
  JSON-LD (the most stable anchor across the post templates)
"""
import re
import sys
from pathlib import Path

# Force UTF-8 stdout on Windows so Korean log lines print cleanly.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BLOG_DIR = Path(__file__).resolve().parent.parent / 'public' / 'blog'
SKIP_SLUGS = {'index', 'posts.js'}  # not actual posts

TITLE_RX = re.compile(r'<title>([^<]+?)(?:\s*\|\s*Lucky Please)?</title>')
BLOGPOSTING_RX = re.compile(
    r'(<script type="application/ld\+json">\s*\{[^<]*?"@type":"BlogPosting"[^<]*?</script>)',
    re.DOTALL,
)


def make_breadcrumb(slug: str, title: str) -> str:
    safe_title = title.replace('"', '\\"').strip()
    payload = (
        '{"@context":"https://schema.org",'
        '"@type":"BreadcrumbList",'
        '"itemListElement":['
        '{"@type":"ListItem","position":1,"name":"홈","item":"https://luckyplz.com/"},'
        '{"@type":"ListItem","position":2,"name":"블로그","item":"https://luckyplz.com/blog/"},'
        f'{{"@type":"ListItem","position":3,"name":"{safe_title}","item":"https://luckyplz.com/blog/{slug}/"}}'
        ']}'
    )
    return f'    <script type="application/ld+json">\n    {payload}\n    </script>'


def process(path: Path) -> str:
    """Returns one of: 'added', 'skipped (already)', 'skipped (no anchor)',
    'skipped (no title)'."""
    slug = path.parent.name
    content = path.read_text(encoding='utf-8')

    if '"BreadcrumbList"' in content:
        return 'skipped (already)'

    title_match = TITLE_RX.search(content)
    if not title_match:
        return 'skipped (no title)'
    title = title_match.group(1).strip()

    breadcrumb = make_breadcrumb(slug, title)

    new_content, n = BLOGPOSTING_RX.subn(
        lambda m: m.group(1) + '\n' + breadcrumb,
        content,
        count=1,
    )
    if n != 1:
        return 'skipped (no anchor)'

    path.write_text(new_content, encoding='utf-8')
    return 'added'


def main() -> int:
    counts = {'added': 0, 'skipped (already)': 0, 'skipped (no anchor)': 0, 'skipped (no title)': 0}

    for sub in sorted(BLOG_DIR.iterdir()):
        if not sub.is_dir():
            continue
        if sub.name in SKIP_SLUGS:
            continue
        index = sub / 'index.html'
        if not index.exists():
            continue
        result = process(index)
        counts[result] = counts.get(result, 0) + 1
        if result == 'added':
            print(f'  + {sub.name}')

    print()
    for k, v in counts.items():
        if v:
            print(f'  {k}: {v}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
