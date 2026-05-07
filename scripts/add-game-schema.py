"""add-game-schema.py
==================
Inject VideoGame / WebApplication JSON-LD into game pages so Google
treats them as proper game/app entities (eligible for richer SERP
display + better category surfacing in Google Play / Search Discover).

Two schema types based on game purpose:

- "Decision tools" (roulette, ladder, team, lotto, car-racing) →
  WebApplication with applicationCategory: BusinessApplication.
  These are utilities, not games for entertainment.

- "Skill games" (dodge, tetris, snake, pacman, brick, burger, bingo,
  quiz, starship-lander) → VideoGame.
  These are entertainment with score/leaderboard mechanics.

Each schema includes:
  - name, url, description (pulled from page title and meta description)
  - applicationCategory + operatingSystem
  - offers (free, $0)
  - inLanguage (ko primary, also en/zh/ja for the multilingual ones)
  - genre (where applicable)
  - publisher reference to the Organization @id on home page

Idempotent: skips files where '"VideoGame"' or
'"applicationCategory":"BusinessApplication"' already appears.
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

# slug → (schema_type, applicationCategory, genre, korean_name, description)
GAME_DEFS = {
    # Decision tools — WebApplication with BusinessApplication category
    'roulette': ('WebApplication', 'BusinessApplication', None, '룰렛',
                 '한 명 뽑기·메뉴 정하기·복불복을 5초에 결정하는 룰렛 도구. 카카오톡 1탭 공유 지원.'),
    'ladder':   ('WebApplication', 'BusinessApplication', None, '사다리타기',
                 '전체 참가자의 순서·결과를 한 화면에 무작위 배정하는 사다리타기 도구. 라이브 사다리 그어지는 연출.'),
    'team':     ('WebApplication', 'BusinessApplication', None, '팀 나누기',
                 '완전 랜덤·실력 균형·친한 친구 분리 3가지 모드의 팀 뽑기 도구. MT·워크샵·수업에서 30초 결정.'),
    'lotto':    ('WebApplication', 'BusinessApplication', None, '로또 번호 생성기',
                 '한국 1~45·미국 파워볼·일본 등 8개국 로또 번호를 자동 생성하는 무료 도구.'),
    'car-racing': ('WebApplication', 'BusinessApplication', None, '카레이싱',
                   '참가자 차량 경주로 1등을 결정하는 시각적 결정 도구. 회식·내기·복불복용.'),
    # Skill games — VideoGame
    'dodge':    ('VideoGame', 'GameApplication', 'Arcade', 'Space-Z',
                 '우주에서 운석을 피하며 살아남는 모바일 닷지 게임. 중력파·방어막 아이템.'),
    'tetris':   ('VideoGame', 'GameApplication', 'Puzzle', '테트리스',
                 '클래식 테트리스. 모바일 스와이프 + PC 키보드 조작 지원.'),
    'snake':    ('VideoGame', 'GameApplication', 'Arcade', '스네이크',
                 '먹이 먹고 길어지는 클래식 스네이크 게임. 모바일·PC 호환.'),
    'pacman':   ('VideoGame', 'GameApplication', 'Arcade', '팩맨',
                 '미로 따라 도트를 먹는 클래식 팩맨. 유령 4종 AI 포함.'),
    'brick':    ('VideoGame', 'GameApplication', 'Arcade', '벽돌깨기',
                 '패들로 공을 튕겨 벽돌을 부수는 클래식 브릭 브레이커.'),
    'burger':   ('VideoGame', 'GameApplication', 'Casual', '햄버거 쌓기',
                 '재료가 떨어지는 타이밍을 맞춰 햄버거를 쌓는 캐주얼 게임.'),
    'bingo':    ('VideoGame', 'GameApplication', 'Casual', '빙고',
                 '5×5 빙고 카드. 단체방에서 1대1 대결·인원 제한 없는 멀티플레이.'),
    'quiz':     ('VideoGame', 'GameApplication', 'Trivia', '퀴즈',
                 '상식·역사·과학 등 다양한 주제의 퀴즈 게임. 점수 누적.'),
    'starship-lander': ('VideoGame', 'GameApplication', 'Simulation', 'Starship Lander',
                        '스페이스X 스타십 착륙 시뮬레이터. 중력·연료·자세 관리 게임.'),
}


def make_schema(slug: str) -> str:
    schema_type, app_category, genre, name, description = GAME_DEFS[slug]
    url = f'https://luckyplz.com/games/{slug}/'
    parts = [
        '"@context":"https://schema.org"',
        f'"@type":"{schema_type}"',
        f'"name":"{name}"',
        f'"url":"{url}"',
        f'"description":"{description}"',
        f'"applicationCategory":"{app_category}"',
        '"operatingSystem":"Any (Web Browser)"',
        '"inLanguage":["ko","en","ja","zh","es"]',
        '"isAccessibleForFree":true',
        '"offers":{"@type":"Offer","price":"0","priceCurrency":"USD"}',
        '"publisher":{"@id":"https://luckyplz.com/#org"}',
    ]
    if genre:
        parts.append(f'"genre":"{genre}"')
    payload = '{' + ','.join(parts) + '}'
    return f'    <script type="application/ld+json">\n    {payload}\n    </script>'


# Anchor: insert AFTER the existing BreadcrumbList JSON-LD that we
# added earlier. This keeps schema blocks grouped together.
ANCHOR_RX = re.compile(
    r'(<script type="application/ld\+json">\s*\{[^<]*?"BreadcrumbList"[^<]*?</script>)',
    re.DOTALL,
)


def process(slug: str, path: Path) -> str:
    if slug not in GAME_DEFS:
        return 'no def'
    content = path.read_text(encoding='utf-8')

    # Idempotency guards.
    if f'"{GAME_DEFS[slug][0]}"' in content and 'applicationCategory' in content:
        return 'already'

    schema = make_schema(slug)
    new_content, n = ANCHOR_RX.subn(
        lambda m: m.group(1) + '\n' + schema,
        content,
        count=1,
    )
    if n == 0:
        # Fallback: insert before </head>.
        if '</head>' not in content:
            return 'no anchor'
        new_content = content.replace('</head>', schema + '\n</head>', 1)

    path.write_text(new_content, encoding='utf-8')
    return 'added'


def main() -> int:
    counts = {}
    for sub in sorted(GAMES_DIR.iterdir()):
        if not sub.is_dir():
            continue
        if sub.name == 'dice':
            # dice is hidden everywhere by site policy; don't promote it via schema either
            continue
        index = sub / 'index.html'
        if not index.exists():
            continue
        result = process(sub.name, index)
        counts[result] = counts.get(result, 0) + 1
        if result == 'added':
            print(f'  + {sub.name}')

    print()
    for k, v in counts.items():
        print(f'  {k}: {v}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
