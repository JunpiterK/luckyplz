"""enhance-new-blogs.py
=====================
Adds two SEO assets to the 5 new Korean lifestyle blog posts:

1. BreadcrumbList JSON-LD — eligible for Google rich-result breadcrumbs in
   search snippets ("Lucky Please › Blog › 결혼식 사회 게임..."). Higher CTR
   in SERP without changing the page's visible content.

2. Author bio block — E-E-A-T (Experience/Expertise/Authority/Trust) signal
   that Google now factors into core updates. Same template as the existing
   space-tech/ai-tech posts, but with a lifestyle-fit description.

Idempotent: looks for unique markers ("BreadcrumbList" and
"lp-author-bio:start") and skips files that already have them. Safe to
re-run.
"""
import re
import sys
from pathlib import Path

# Windows cp949 console can't print unicode marks; force UTF-8 output.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

NEW_POSTS = [
    ('presentation-order-fair', '수업 발표 순서 정하는 도구 4가지 — 손 안 들고 끝내기'),
    ('wedding-mc-games', '결혼식 사회 게임·이벤트 추천 7가지 — 어색한 정적 0초 만들기'),
    ('elementary-team-grouping', '초등학교 모둠 짜기 — 친한 친구 분리하면서 갈등 안 만드는 법'),
    ('club-seating-fair', '동아리·교회 모임 자리 정하기 5가지 — 매번 같은 사람만 뭉치지 않게'),
    ('picnic-game-ideas', '야유회·소풍 게임 10가지 — MT랑은 다른 색깔로 분위기 띄우기'),
]

LIFESTYLE_BIO_DESC = (
    '회식·MT·결혼식·학교·동아리에서 쓰는 결정 도구를 만드는 독립 사이트. '
    '룰렛·사다리·팀 나누기·로또 — 30초로 끝나는 무료 도구.'
)

AUTHOR_BIO = """<!-- lp-author-bio:start -->
<style>
.lp-author-bio { margin: 28px 16px 0; padding: 18px 16px; background: linear-gradient(180deg, rgba(93,193,255,0.06) 0%, rgba(167,139,250,0.04) 100%); border: 1px solid rgba(93,193,255,0.22); border-radius: 12px; }
.lp-author-bio .lp-row { display: flex; align-items: flex-start; gap: 13px; }
.lp-author-bio .lp-avatar { width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg, #5dc1ff 0%, #a78bfa 100%); display: flex; align-items: center; justify-content: center; font-size: 19px; flex-shrink: 0; box-shadow: 0 2px 8px rgba(93,193,255,0.25); }
.lp-author-bio .lp-text { flex: 1; min-width: 0; }
.lp-author-bio .lp-name { font-size: 13.5px; font-weight: 700; color: #fff; line-height: 1.3; }
.lp-author-bio .lp-name a { color: inherit; text-decoration: none; border-bottom: 1px dashed rgba(255,255,255,0.25); }
.lp-author-bio .lp-name a:hover { border-bottom-color: #5dc1ff; }
.lp-author-bio .lp-desc { font-size: 11.5px; color: #8c9cb6; margin-top: 4px; line-height: 1.55; }
.lp-author-bio .lp-meta { display: flex; flex-wrap: wrap; gap: 10px 16px; margin-top: 13px; padding-top: 12px; border-top: 1px dashed rgba(255,255,255,0.07); font-size: 10.5px; color: #5d6e8a; line-height: 1.4; }
.lp-author-bio .lp-meta b { color: #8c9cb6; font-weight: 600; }
@media (min-width: 768px) {
  .lp-author-bio { margin: 32px 28px 0; padding: 22px 22px; }
  .lp-author-bio .lp-name { font-size: 14.5px; }
  .lp-author-bio .lp-desc { font-size: 12.5px; }
  .lp-author-bio .lp-meta { font-size: 11.5px; }
}
</style>
<div class="lp-author-bio" role="contentinfo">
  <div class="lp-row">
    <div class="lp-avatar" aria-hidden="true">🎯</div>
    <div class="lp-text">
      <div class="lp-name">By <a href="/about/">Lucky Please</a></div>
      <div class="lp-desc">__DESC__</div>
    </div>
  </div>
  <div class="lp-meta">
    <span>📅 <b>마지막 업데이트</b>: 2026-05-07</span>
    <span>✓ 30초 결정 도구</span>
    <span>🌐 한국어</span>
  </div>
</div>
<!-- lp-author-bio:end -->
"""


def make_breadcrumb(slug: str, title: str) -> str:
    """Build a BreadcrumbList JSON-LD <script> block."""
    safe_title = title.replace('"', '\\"')
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


def main() -> int:
    base = Path(__file__).resolve().parent.parent / 'public' / 'blog'
    bio_added = 0
    crumb_added = 0

    for slug, title in NEW_POSTS:
        path = base / slug / 'index.html'
        if not path.exists():
            print(f'!  {slug}: file not found, skipped')
            continue

        content = path.read_text(encoding='utf-8')

        # 1. Insert BreadcrumbList JSON-LD right after the FAQPage <script>.
        if '"BreadcrumbList"' not in content:
            breadcrumb = make_breadcrumb(slug, title)
            new_content, n = re.subn(
                r'(<script type="application/ld\+json">\s*\{[^<]*?"@type":"FAQPage"[^<]*?</script>)',
                r'\1\n' + breadcrumb.replace('\\', r'\\'),
                content,
                count=1,
                flags=re.DOTALL,
            )
            if n == 1:
                content = new_content
                crumb_added += 1
            else:
                print(f'!  {slug}: FAQPage anchor not found, breadcrumb skipped')

        # 2. Insert author bio right before </body>.
        if 'lp-author-bio:start' not in content:
            bio = AUTHOR_BIO.replace('__DESC__', LIFESTYLE_BIO_DESC)
            content = content.replace('</body>', bio + '\n</body>', 1)
            bio_added += 1

        path.write_text(content, encoding='utf-8')
        print(f'✓ {slug}')

    print(f'\n  added BreadcrumbList JSON-LD to {crumb_added} file(s)')
    print(f'  added author bio to {bio_added} file(s)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
