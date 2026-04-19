/*
  Lucky Please Blog - post manifest.
  One source of truth. Adding a post = push an entry + create /blog/<slug>/index.html.

  `lang` tells the blog index which language list this post belongs in —
  each post's HTML is written natively in one language (ko or en). We
  don't auto-translate; cross-language siblings (`alt`) are separately
  authored in the target locale's search intent and linked manually.

  Index renders only posts matching the user's current lang. Users whose
  lang has no posts see an empty-state CTA pointing to the primary pool.
*/
window.BLOG_POSTS = [
    {
        slug: 'random-name-picker-guide',
        lang: 'en',
        date: '2026-04-19',
        readMinutes: 6,
        coverEmoji: '🎯',
        tags: ['random picker', 'classroom', 'teacher'],
        title: 'Free Random Name Picker Online — For Classrooms, Meetings, and Parties',
        excerpt: 'How teachers, meeting hosts, and families use a free random name picker. Setup, use cases, and anti-bias tips.',
    },
    {
        slug: 'powerball-random-generator',
        lang: 'en',
        date: '2026-04-19',
        readMinutes: 7,
        coverEmoji: '🎰',
        tags: ['powerball', 'lottery', 'random number'],
        title: 'Free Powerball Random Number Generator — Rules, Odds, and How to Play',
        excerpt: 'How Powerball actually works, odds explained plainly, and a free number generator you can use right now.',
        alt: 'lotto-country-compare',
    },
    {
        slug: 'lotto-country-compare',
        lang: 'ko',
        date: '2026-04-19',
        readMinutes: 7,
        coverEmoji: '🎱',
        tags: ['로또', '국가별', '비교'],
        title: '로또 번호 생성기 8개국 비교 — 어느 나라 로또가 제일 재밌을까',
        excerpt: '한국·미국·중국·일본·유럽 8개국 로또 규칙 비교. 당첨 확률·재미 포인트까지 정리.',
        alt: 'powerball-random-generator',
    },
    {
        slug: 'team-split-fair',
        lang: 'ko',
        date: '2026-04-19',
        readMinutes: 6,
        coverEmoji: '👥',
        tags: ['팀 나누기', 'MT', '워크샵'],
        title: 'MT·워크샵 팀 나누기 공정하게 하는 3가지 방법',
        excerpt: '완전 랜덤·실력 균형·친밀도 분산 3가지 방식과 상황별 추천. 팀 갈등 줄이는 팁까지.',
    },
    {
        slug: 'coffee-1-minute',
        lang: 'ko',
        date: '2026-04-19',
        readMinutes: 5,
        coverEmoji: '☕️',
        tags: ['회식', '커피', '1분'],
        title: '회식 커피 누가 쏠지 1분 안에 정하는 법',
        excerpt: '회식 후 눈치싸움 3분 대신 게임 1분. 상황별 룰렛·사다리·카레이싱 추천과 반복 당첨 방지 노하우까지.',
    },
    {
        slug: 'coffee-who-pays',
        lang: 'ko',
        date: '2026-04-17',
        readMinutes: 4,
        coverEmoji: '☕️',
        tags: ['커피', '내기', '사무실'],
        title: '커피 누가 쏠래? 매번 공평하게 정하는 5가지 방법',
        excerpt: '사무실·학교·친구끼리 커피 내기, 매번 같은 사람만 쏘는 문제 해결. 룰렛·사다리·주사위로 10초에 정하는 법.',
    },
];
