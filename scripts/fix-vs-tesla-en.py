"""Second pass: clean up remaining Korean in spacex-vs-tesla-en."""
fp = 'public/blog/spacex-vs-tesla-en/index.html'
with open(fp, 'r', encoding='utf-8') as f:
    h = f.read()

swaps = [
    ('Cap·수익·Tech moat·미래·Risk 5축 비교',
     '5-axis comparison: cap, profit, tech moat, future, risk'),
    ('축 1: Cap + 매출 배수', 'Axis 1: Cap + Sales Multiple'),
    ('Cap 차이는 +46%, 그런데 매출 배수는 SpaceX 가 3.5배 비싸다.',
     'Cap differs +46%, yet SpaceX sales multiple is 3.5x more expensive.'),
    ('2030 무인 5기, 2032 유인 첫 시도. 성공 시 Cap $10T+ 이론 가능. 실패 확률 50%+. 머스크 자기평가 50% 적시 도달 확률.',
     '5 uncrewed by 2030, first crewed 2032. Success → $10T+ cap theoretical. 50%+ failure prob. Musk self-rates 50% on-time.'),
    ('각각 5% 이하 + 현금 / 인덱스 ETF 위주. 머스크 헤드라인 Risk 회피.',
     'Each ≤5% + cash/index ETF heavy. Avoiding Musk headline risk entirely.'),
    # Catch-all common phrases
    ('축 ', 'Axis '),
    ('머스크', 'Musk'),
    ('인플레이션 보정', 'inflation-adjusted'),
    ('자기평가', 'self-rated'),
    ('적시 도달', 'on-time'),
    ('한 트윗', 'one tweet'),
    ('변동성', 'volatility'),
    ('진입', 'entry'),
    ('정점', 'peak'),
    ('인증', 'certification'),
    ('시장 점유율', 'market share'),
    ('실행 리스크', 'execution risk'),
    ('규제', 'regulatory'),
    ('자본 요구', 'capital intensity'),
    ('중국 매출', 'China revenue'),
    ('현금', 'cash'),
    ('매출', 'revenue'),
    ('보유', 'hold'),
    ('확률', 'probability'),
    ('비중', 'weight'),
    ('진입 시', 'when entering'),
]

count = 0
for old, new in swaps:
    if old in h:
        c = h.count(old)
        h = h.replace(old, new)
        count += c
print('Fixed', count, 'occurrences')

with open(fp, 'w', encoding='utf-8') as f:
    f.write(h)
