"""fix-bio-categories.py
=====================
Replaces the SpaceX/AI/finance author-bio description on lifestyle and
probability blog posts with a topic-fit description.

WHY
---
The original author-bio template was written for the SpaceX/AI corpus
("Independent analysis on space, AI, and finance — every figure verified
against primary sources (Bloomberg, Reuters, PitchBook, SEC)"). When
later applied to lifestyle/probability posts (회식·MT·로또·사다리 etc),
the description became incoherent — Google's E-E-A-T signal sees a
lifestyle post claiming SpaceX/AI authority. That hurts indexing chances
on the very posts we now expect to drive Korean keyword traffic.

This script replaces the description on those posts with one that
matches their actual topic, while leaving the SpaceX/AI/Industry posts
untouched.

WHAT
----
- Korean lifestyle/probability (7 posts): Korean lifestyle description
- English lifestyle/probability (2 posts): English lifestyle description
- All other posts: untouched

Idempotent — checks current description before replacing.
"""
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BLOG_DIR = Path(__file__).resolve().parent.parent / 'public' / 'blog'

KOREAN_LIFESTYLE_SLUGS = {
    'coffee-1-minute',
    'coffee-who-pays',
    'dinner-menu-fair',
    'team-split-fair',
    'ladder-fairness-simulation',
    'lotto-country-compare',
    'lotto-history-story',
}

ENGLISH_LIFESTYLE_SLUGS = {
    'random-name-picker-guide',
    'powerball-random-generator',
}

KO_DESC = (
    '회식·MT·결혼식·학교·동아리에서 쓰는 결정 도구를 만드는 독립 사이트. '
    '룰렛·사다리·팀 나누기·로또 — 30초로 끝나는 무료 도구.'
)
EN_DESC = (
    'Independent site building free decision tools for parties, '
    'classrooms, and team meetings. Roulette, ladder, team picker, '
    'lotto — every result in 30 seconds.'
)

OLD_KO_DESC_SUBSTR = '우주산업·AI·금융 데이터를 1차 자료로 분석'
OLD_EN_DESC_SUBSTR = 'Independent analysis on space, AI, and finance'

DESC_RX = re.compile(r'(<div class="lp-desc">)([^<]*)(</div>)')


def process(slug: str, new_desc: str, old_substr: str) -> str:
    path = BLOG_DIR / slug / 'index.html'
    if not path.exists():
        return 'missing'
    content = path.read_text(encoding='utf-8')

    if 'lp-author-bio:start' not in content:
        return 'no bio'

    if old_substr not in content:
        return 'already fixed'

    new_content, n = DESC_RX.subn(
        lambda m: m.group(1) + new_desc + m.group(3) if old_substr in m.group(2) else m.group(0),
        content,
        count=1,
    )
    if n == 0:
        return 'pattern miss'

    path.write_text(new_content, encoding='utf-8')
    return 'fixed'


def main() -> int:
    fixed_ko = 0
    fixed_en = 0
    skipped = 0
    print('Korean lifestyle/probability:')
    for slug in sorted(KOREAN_LIFESTYLE_SLUGS):
        result = process(slug, KO_DESC, OLD_KO_DESC_SUBSTR)
        print(f'  {slug}: {result}')
        if result == 'fixed':
            fixed_ko += 1
        else:
            skipped += 1

    print('\nEnglish lifestyle/probability:')
    for slug in sorted(ENGLISH_LIFESTYLE_SLUGS):
        result = process(slug, EN_DESC, OLD_EN_DESC_SUBSTR)
        print(f'  {slug}: {result}')
        if result == 'fixed':
            fixed_en += 1
        else:
            skipped += 1

    print(f'\n  fixed: {fixed_ko} KO + {fixed_en} EN ({fixed_ko + fixed_en} total)')
    print(f'  skipped: {skipped}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
