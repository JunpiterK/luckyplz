"""add-game-guide-section.py
==========================
Injects a "관련 가이드" section into each decision-tool game page
that links to 3-4 relevant Korean lifestyle blog posts.

WHY
---
The decision-tool games (roulette, ladder, team, lotto, car-racing)
have minimal text content for Google's content-quality signal — most
of the page is canvas + interactive UI. Adding a curated 3-4 link
panel at the bottom does three things:

1. Internal pagerank: passes link equity from frequently-visited
   game pages to the freshly-published lifestyle blog posts.
2. Site-internal navigation funnel: a user who finishes a roulette
   round may want a guide on "how do I run this for a wedding MC?",
   and the panel surfaces exactly that.
3. SEO content surface: gives the crawler a few semantic-rich
   anchor-text mentions on otherwise-canvas-heavy pages, helping
   the page show up for related Korean keyword clusters.

WHAT
----
- Decision tools only (5 games). Skill games (tetris/snake/etc) skipped
  — entertainment-focused, blog tie-in less natural.
- Idempotent via "lp-game-guide:start" marker.
- Inserts right before </body>.
- Mobile-friendly CSS, cool teal/blue palette to read as "info" not
  "play" (mirrors the home guide-strip palette).
"""
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

GAMES_DIR = Path(__file__).resolve().parent.parent / 'public' / 'games'

# (slug, title) per blog post we link to
GAME_GUIDE_MAP = {
    'roulette': [
        ('coffee-1-minute', '회식 커피 1분 결정 가이드 — 룰렛·사다리 상황별 추천'),
        ('presentation-order-fair', '수업 발표 순서 정하는 도구 4가지 — 손 안 들고 끝내기'),
        ('wedding-mc-games', '결혼식 사회 게임 7가지 — 부케 룰렛 연출 포함'),
        ('dinner-menu-fair', '회식 메뉴 1분 안에 공평하게 정하는 5가지 방법'),
    ],
    'ladder': [
        ('ladder-fairness-simulation', '사다리타기 진짜 공정한가? 시작 위치 매트릭스 분석'),
        ('presentation-order-fair', '수업 발표 순서 정하는 도구 4가지'),
        ('club-seating-fair', '동아리·교회 모임 자리 정하기 5가지'),
        ('coffee-1-minute', '회식 커피 1분 결정 가이드'),
    ],
    'team': [
        ('team-split-fair', 'MT·워크샵 팀 나누기 3가지 방식 — 갈등 줄이는 꿀팁'),
        ('elementary-team-grouping', '초등학교 모둠 짜기 — 친한 친구 분리'),
        ('picnic-game-ideas', '야유회 게임 10가지 — 팀 단위 운영'),
        ('wedding-mc-games', '결혼식 사회 게임 7가지'),
    ],
    'lotto': [
        ('lotto-country-compare', '로또 8개국 비교 — 어느 나라 로또가 제일 내 스타일?'),
        ('lotto-history-story', '근데 로또 언제부터 있었어? 2000년 역사'),
        ('powerball-random-generator', 'Free Powerball Random Number Generator (English)'),
    ],
    'car-racing': [
        ('coffee-1-minute', '회식 커피 1분 결정 가이드 — 카레이싱 활용법'),
        ('picnic-game-ideas', '야유회 게임 10가지'),
        ('wedding-mc-games', '결혼식 사회 게임 7가지'),
    ],
}

GUIDE_BLOCK_TEMPLATE = """<!-- lp-game-guide:start -->
<style>
.lp-game-guide{max-width:740px;width:calc(100% - 32px);margin:36px auto 24px;padding:22px 22px 18px;border-radius:14px;background:linear-gradient(180deg,rgba(93,193,255,.05) 0%,rgba(167,139,250,.03) 100%);border:1px solid rgba(93,193,255,.2);box-sizing:border-box;position:relative;z-index:1}
.lp-game-guide h3{font-family:'Orbitron','Noto Sans KR',sans-serif;font-size:.74em;letter-spacing:2.2px;color:rgba(255,255,255,.55);font-weight:800;margin:0 0 14px;text-transform:uppercase}
.lp-game-guide ul{list-style:none;margin:0;padding:0}
.lp-game-guide li{margin-bottom:8px}
.lp-game-guide a{display:block;padding:12px 14px;border-radius:11px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);color:rgba(255,255,255,.85);text-decoration:none;font-size:.92em;line-height:1.45;transition:all .18s;letter-spacing:.005em}
.lp-game-guide a:hover{border-color:rgba(93,193,255,.45);background:rgba(93,193,255,.08);color:#fff;transform:translateY(-1px)}
.lp-game-guide a::after{content:' →';color:rgba(93,193,255,.6);font-weight:700}
@media(max-width:600px){.lp-game-guide{margin:24px 14px 14px;width:auto;padding:16px 16px 12px}.lp-game-guide h3{font-size:.66em;letter-spacing:1.6px}.lp-game-guide a{padding:10px 12px;font-size:.88em}}
</style>
<aside class="lp-game-guide" aria-label="관련 가이드 — 결정 도구 활용법">
  <h3>📚 관련 가이드 (한국어)</h3>
  <ul>
__LINKS__
  </ul>
</aside>
<!-- lp-game-guide:end -->
"""


def build_block(slug: str) -> str:
    items = GAME_GUIDE_MAP[slug]
    links = '\n'.join(
        f'    <li><a href="/blog/{s}/">{t}</a></li>' for s, t in items
    )
    return GUIDE_BLOCK_TEMPLATE.replace('__LINKS__', links)


def process(slug: str, path: Path) -> str:
    if slug not in GAME_GUIDE_MAP:
        return 'no map'
    content = path.read_text(encoding='utf-8')

    if 'lp-game-guide:start' in content:
        return 'already'

    block = build_block(slug)
    if '</body>' not in content:
        return 'no body close'

    new_content = content.replace('</body>', block + '\n</body>', 1)
    path.write_text(new_content, encoding='utf-8')
    return 'added'


def main() -> int:
    counts = {}
    for slug in GAME_GUIDE_MAP.keys():
        path = GAMES_DIR / slug / 'index.html'
        if not path.exists():
            print(f'  ! {slug}: file not found')
            continue
        result = process(slug, path)
        counts[result] = counts.get(result, 0) + 1
        print(f'  {result:>10}  {slug}')

    print()
    for k, v in counts.items():
        print(f'  {k}: {v}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
