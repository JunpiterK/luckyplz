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
        slug: 'lotto-history-story',
        lang: 'ko',
        date: '2026-04-20',
        readMinutes: 7,
        coverEmoji: '🏛️',
        tags: ['로또', '역사', '스토리'],
        title: '근데 로또 언제부터 있었어? 2000년 역사 썰 풀어줄게',
        excerpt: '로마 황제 연회부터 엘리자베스 여왕, 하버드 대학, 조선시대 산통계까지. 친구가 풀어주는 복권 2000년 족보.',
    },
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
        title: '로또 8개국 비교 — 어느 나라 로또가 제일 내 스타일?',
        excerpt: '한국·미국·중국·일본·유럽까지. 공 개수도 확률도 다 달라서 당첨 난이도가 수백 배씩 차이남. 친구한테 푸는 나라별 로또 투어.',
        alt: 'powerball-random-generator',
    },
    {
        slug: 'team-split-fair',
        lang: 'ko',
        date: '2026-04-19',
        readMinutes: 6,
        coverEmoji: '👥',
        tags: ['팀 나누기', 'MT', '워크샵'],
        title: 'MT·워크샵 팀 나누기, "쟤랑 왜 같이?" 소리 안 나오게 하는 3가지 방식',
        excerpt: '완전 랜덤·티어 균형·친한 애들 분산. 상황별로 뭐 쓰면 되는지 + 갈등 줄이는 꿀팁 4개.',
    },
    {
        slug: 'coffee-1-minute',
        lang: 'ko',
        date: '2026-04-19',
        readMinutes: 5,
        coverEmoji: '☕️',
        tags: ['회식', '커피', '1분'],
        title: '회식 커피 누가 쏠지 1분 안에 정하는 법',
        excerpt: '눈치싸움 3분 대신 게임 1분. 룰렛·사다리·카레이싱 상황별 추천 + 반복 당첨 안 나게 만드는 트릭.',
    },
    {
        slug: 'coffee-who-pays',
        lang: 'ko',
        date: '2026-04-17',
        readMinutes: 4,
        coverEmoji: '☕️',
        tags: ['커피', '내기', '사무실'],
        title: '커피 누가 쏠래? — "매번 저만 쏘는" 루프 끊는 5가지 방법',
        excerpt: '사무실·친구 모임에서 매번 같은 사람이 쏘는 상황. 10초로 끝내는 5가지 방식 + 단톡방 밈 만드는 법.',
    },
];
