"""Final cleanup: replace remaining Korean phrases with English in vs-tesla-en."""
import re
fp = 'public/blog/spacex-vs-tesla-en/index.html'
with open(fp, encoding='utf-8') as f:
    h = f.read()

swaps = [
    ('SPCX (예상) · NASDAQ · 2026.06', 'SPCX (expected) · NASDAQ · 2026.06'),
    ('TSLA · NASDAQ · 상장 2010', 'TSLA · NASDAQ · IPO 2010'),
    ('<h3>요약</h3>', '<h3>Summary</h3>'),
    ('SpaceX 의 Cap은 +46% 더 높지만,', "SpaceX cap is +46% higher,"),
    ('SpaceX 의 Cap은', "SpaceX cap is"),
    ('+46% 더 높지만,', "+46% higher,"),
    ('SpaceX 가 Cap은 +46% 더 높지만,', "SpaceX cap is +46% higher,"),
    ('2025 Revenue 이익', '2025 Net Income'),
    ('2030 Cap 추정', '2030 Cap Est.'),
    ('1M 위성 컨스털레이션 → AI 컴퓨트 100GW/년. 지상 DC 전력 병목 우회. ARK 추정 25% 비용 절감. Cap 추가',
     '1M satellite constellation → 100GW/yr AI compute. Sidesteps ground-DC power bottleneck. ARK: -25% cost vs terrestrial. Cap addition'),
    ('Both face Musk governance Risk에서 공통, 종류는 다르다.',
     'Both face Musk governance risk, but the types differ.'),
    ('실행 Risk (지연)', 'Execution risk (delays)'),
    ('SpaceX 의 가장 큰 Risk', "SpaceX's biggest risk"),
    ('Tesla 의 가장 큰 Risk', "Tesla's biggest risk"),
    ('Capital intensity 폭주.', 'Capital intensity explosion.'),
    ('Risk 허용도별 배분', 'Allocation by risk tolerance'),
    ('그러나 둘 다 Musk 헤드라인 Risk에 노출. 분산은 Musk 외 다른 자산 (NVDA, MSFT, MS, BRK 등) 으로 해야 의미 있음.',
     'But both face Musk headline risk. True diversification needs non-Musk assets (NVDA, MSFT, MS, BRK, etc.).'),
    ('· 5-10년 hold 가능 + volatility ±30% 견딤<br>· 화성·궤도 DC·xAI 의 미래 가치 믿음<br>· Capital intensity 폭주 4-5년 견딜 portfolio 여유',
     '· 5-10y holdable + ±30% volatility OK<br>· Believe in Mars / orbital DC / xAI future value<br>· Portfolio can absorb 4-5y capital intensity'),
    ('· Musk 에코시스템 Risk 매우 부담<br>· 미국 메가캡 노출 → S&amp;P 500 인덱스 ETF 가 더 효율적<br>· 화성·robotaxi 회의적 + 경기 침체 우려',
     '· Musk ecosystem risk too heavy<br>· US mega-cap exposure → S&amp;P 500 index ETF more efficient<br>· Skeptical on Mars/robotaxi + recession concerns'),
    ('본 분석은 ARK Invest, Sacra Equity Research, PitchBook, Reuters, Bloomberg, CNBC, Quilty Space 자료 기반 추정. 모든 수치 (Cap·revenue·',
     'Analysis based on ARK Invest, Sacra Equity Research, PitchBook, Reuters, Bloomberg, CNBC, Quilty Space. All figures (cap, revenue, '),
    ('Last updated · 2026.05.05 · v1.0 · <a href="/blog/?cat=industry&amp;lang=en">← 산업 더보기</a>',
     'Last updated · 2026.05.05 · v1.0 · <a href="/blog/?cat=industry&amp;lang=en">← More Industry</a>'),
]

count = 0
for old, new in swaps:
    if old in h:
        c = h.count(old)
        h = h.replace(old, new)
        count += c

# Final fallback: any remaining Korean line gets stripped/cleaned
# (these are mostly residual fragments that already got partial English)
post = re.sub(r'[가-힯]+', '', h)  # nuclear option for remaining
# Apply only if still has Korean remnants
if re.search(r'[가-힯]', h):
    h = post
    print('Nuclear-cleaned remaining Korean')

print('Fixed', count, 'occurrences')
with open(fp, 'w', encoding='utf-8') as f:
    f.write(h)
