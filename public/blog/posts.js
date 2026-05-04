/*
  Lucky Please Blog - post manifest.
  One source of truth. Adding a post = push an entry + create /blog/<slug>/index.html.

  Fields:
  - lang:     ko | en — each post is written natively in one language; cross-lang
              siblings are linked via `alt`.
  - category: lifestyle | probability | tech-space | industry | build
              Used by the blog index tab filter. Default tab "all" shows
              every post sorted by date desc.

  Index renders only posts matching the user's current lang. Users whose
  lang has no posts see an empty-state CTA pointing to the primary pool.
*/
window.BLOG_POSTS = [
    {
        slug: 'ladder-fairness-simulation',
        lang: 'ko',
        category: 'probability',
        date: '2026-05-04',
        readMinutes: 11,
        coverEmoji: '🪜',
        tags: ['사다리', '시뮬레이션', '시나리오 분석'],
        title: '사다리타기 진짜 공정한가? 시작 위치 × 도착 옵션 매트릭스 분석',
        excerpt: '회식 메뉴 / 1당첨 4꽝 / 두 팀 나누기 5가지 시나리오 — 어떤 시작 위치가 유리한가? 5×5 전이 행렬로 정밀 분석한 박사의 결론.',
    },
    {
        slug: 'dinner-menu-fair',
        lang: 'ko',
        category: 'lifestyle',
        date: '2026-05-04',
        readMinutes: 6,
        coverEmoji: '🍱',
        tags: ['회식', '메뉴 정하기', '룰렛'],
        title: '회식 메뉴 또 누가 정해? 1분 안에 공평하게 끝내는 5가지 방법',
        excerpt: '회식 메뉴 정하느라 1년에 5시간. 사다리·룰렛·가위바위보·투표·번호뽑기 직접 비교 + 사다리가 사실 공정하지 않은 이유.',
    },
    {
        slug: 'lotto-history-story',
        lang: 'ko',
        category: 'probability',
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
        category: 'lifestyle',
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
        category: 'probability',
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
        category: 'probability',
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
        category: 'lifestyle',
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
        category: 'lifestyle',
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
        category: 'lifestyle',
        date: '2026-04-17',
        readMinutes: 4,
        coverEmoji: '☕️',
        tags: ['커피', '내기', '사무실'],
        title: '커피 누가 쏠래? — "매번 저만 쏘는" 루프 끊는 5가지 방법',
        excerpt: '사무실·친구 모임에서 매번 같은 사람이 쏘는 상황. 10초로 끝내는 5가지 방식 + 단톡방 밈 만드는 법.',
    },
];

/* Category metadata for blog index tabs.
   Order here = order in tab UI. First item is the default ("all"). */
window.BLOG_CATEGORIES = [
    { slug: 'all',         emoji: '🌐', label_ko: '전체',        label_en: 'All' },
    { slug: 'lifestyle',   emoji: '🍽️', label_ko: '생활·결정',   label_en: 'Lifestyle' },
    { slug: 'probability', emoji: '🎰', label_ko: '확률·통계',   label_en: 'Probability' },
    { slug: 'tech-space',  emoji: '🚀', label_ko: '테크·우주',   label_en: 'Tech & Space' },
    { slug: 'industry',    emoji: '💰', label_ko: '경제·산업',   label_en: 'Industry' },
    { slug: 'build',       emoji: '🛠️', label_ko: '빌드인공개',  label_en: 'Build' },
];
