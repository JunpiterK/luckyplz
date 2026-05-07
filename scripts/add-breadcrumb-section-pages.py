"""add-breadcrumb-section-pages.py
================================
Extends BreadcrumbList JSON-LD to game / tool / lab pages.

Each section gets a 2-level breadcrumb (Home › <Section> › <PageName>)
so the SERP snippet shows the navigation path. Same SERP CTR uplift
benefit as the blog version.

Skips pages that already carry "BreadcrumbList" (idempotent).

Anchor for injection: each game/tool/lab uses different JSON-LD types
(Game / WebApplication / SoftwareApplication / etc), so we just look
for any existing application/ld+json <script> and append after the
first one. If no JSON-LD exists, we insert before </head>.
"""
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent / 'public'

SECTIONS = [
    {
        'dir': ROOT / 'games',
        'url_prefix': '/games/',
        'breadcrumb_label': '게임',
    },
    {
        'dir': ROOT / 'tools',
        'url_prefix': '/tools/',
        'breadcrumb_label': '도구',
    },
    {
        'dir': ROOT / 'labs',
        'url_prefix': '/labs/',
        'breadcrumb_label': 'AI 랩',
    },
]

TITLE_RX = re.compile(r'<title>([^<]+?)(?:\s*[·|·]\s*[^<]*?)?\s*</title>')
JSONLD_RX = re.compile(
    r'(<script type="application/ld\+json">[\s\S]*?</script>)',
)


def make_breadcrumb(slug: str, title: str, url_prefix: str, section_label: str) -> str:
    safe_title = title.replace('"', '\\"').strip()
    section_url = f'https://luckyplz.com{url_prefix}'
    page_url = f'https://luckyplz.com{url_prefix}{slug}/'
    payload = (
        '{"@context":"https://schema.org",'
        '"@type":"BreadcrumbList",'
        '"itemListElement":['
        '{"@type":"ListItem","position":1,"name":"홈","item":"https://luckyplz.com/"},'
        f'{{"@type":"ListItem","position":2,"name":"{section_label}","item":"{section_url}"}},'
        f'{{"@type":"ListItem","position":3,"name":"{safe_title}","item":"{page_url}"}}'
        ']}'
    )
    return f'    <script type="application/ld+json">\n    {payload}\n    </script>'


def process(path: Path, slug: str, url_prefix: str, section_label: str) -> str:
    content = path.read_text(encoding='utf-8')

    if '"BreadcrumbList"' in content:
        return 'skipped (already)'

    title_match = TITLE_RX.search(content)
    if not title_match:
        return 'skipped (no title)'
    raw_title = title_match.group(1).strip()
    # Strip the " | Lucky Please" or "· Lucky Please" suffix if present.
    title = re.split(r'\s*[|·]\s*Lucky\s*Please', raw_title, 1)[0].strip()

    breadcrumb = make_breadcrumb(slug, title, url_prefix, section_label)

    # Prefer to insert right after the first JSON-LD <script> if any exists.
    if JSONLD_RX.search(content):
        new_content, n = JSONLD_RX.subn(
            lambda m: m.group(1) + '\n' + breadcrumb,
            content,
            count=1,
        )
    else:
        # Fallback: insert before </head>.
        if '</head>' not in content:
            return 'skipped (no head)'
        new_content = content.replace('</head>', breadcrumb + '\n</head>', 1)
        n = 1

    if n != 1:
        return 'skipped (no anchor)'

    path.write_text(new_content, encoding='utf-8')
    return 'added'


def main() -> int:
    grand_added = 0
    for section in SECTIONS:
        section_dir: Path = section['dir']
        if not section_dir.is_dir():
            continue
        added = 0
        for sub in sorted(section_dir.iterdir()):
            if not sub.is_dir():
                continue
            index = sub / 'index.html'
            if not index.exists():
                continue
            result = process(
                index,
                slug=sub.name,
                url_prefix=section['url_prefix'],
                section_label=section['breadcrumb_label'],
            )
            if result == 'added':
                added += 1
                print(f'  + {section["url_prefix"]}{sub.name}/')
        print(f'  {section_dir.name}: +{added}')
        grand_added += added
    print(f'\n  total breadcrumbs added: {grand_added}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
