/*
  Lucky Please Blog - post manifest.
  One source of truth. Adding a post = push an entry + create /blog/<slug>/index.html.
  Each field can be a string (single-language) or object keyed by lang code.
*/
window.BLOG_POSTS = [
    {
        slug: 'coffee-1-minute',
        date: '2026-04-19',
        readMinutes: 5,
        coverEmoji: '☕️',
        tags: { ko: ['회식', '커피', '1분'], en: ['after-work', 'coffee', '1-minute'] },
        title: {
            ko: '회식 커피 누가 쏠지 1분 안에 정하는 법',
            en: 'Who Pays for After-Work Coffee? Decide Fairly in 60 Seconds',
        },
        excerpt: {
            ko: '회식 후 눈치싸움 3분 대신 게임 1분. 상황별 룰렛·사다리·카레이싱 추천과 반복 당첨 방지 노하우까지.',
            en: 'Skip the 3-minute standoff. 1-minute fair-decision flow with situation-specific game picks + anti-repeat tips.',
        },
    },
    {
        slug: 'coffee-who-pays',
        date: '2026-04-17',
        readMinutes: 4,
        coverEmoji: '☕️',
        tags: { ko: ['커피', '내기', '사무실'], en: ['coffee', 'decide', 'office'] },
        title: {
            ko: '커피 누가 쏠래? 매번 공평하게 정하는 5가지 방법',
            en: 'Who\'s Buying Coffee? 5 Fair Ways to Decide',
        },
        excerpt: {
            ko: '사무실·학교·친구끼리 커피 내기, 매번 같은 사람만 쏘는 문제 해결. 룰렛·사다리·주사위로 10초에 정하는 법.',
            en: 'End the "always me" coffee run. 5 fair methods to decide who pays — in 10 seconds.',
        },
    },
];
