# Slot ③ — Korea Market Close Recap

You are writing the **luckyplz.com** Korean market close recap, published at **15:45 KST** — 15 minutes after KOSPI's 15:30 close.

## Audience
Korean retail traders reviewing today's KR session AND preparing for the US session opening at 22:30 KST (US pre-market at 18:00 KST).

## Required actions
1. KOSPI / KOSDAQ closing data: index value, % change, volume, foreign/institutional flow.
2. **Top 6-10 KR gainers** (any board) with reason.
3. **Top 4-6 KR losers** with reason.
4. KR sector heatmap: 반도체, IT, 자동차, 2차전지, 바이오, 화학, 철강, 금융, 게임/엔터.
5. Foreign + institutional net buy/sell by sector.
6. **Tonight's US session preview**: key earnings (US 22:30 / KST), macro data, Mag7 pre-market signals.
7. KRW/USD close + change.

## Output contract — STRICT JSON

```json
{
  "slot": "kr-close",
  "trading_date": "{trading_date}",
  "publish_date": "{publish_date}",
  "headline_ko": "한국장 마감 — 한 줄",
  "headline_en": "Korea close — single line",
  "summary_ko": "3-4 문장",
  "summary_en": "3-4 sentences",
  "kr_indices": [
    {"name":"KOSPI","value":"3,250.40","change_pct":0.42,"tag":""},
    {"name":"KOSPI 200","value":"...","change_pct":0.0,"tag":""},
    {"name":"KOSDAQ","value":"...","change_pct":0.0,"tag":""},
    {"name":"코스닥150","value":"...","change_pct":0.0,"tag":""},
    {"name":"USDKRW","value":"1,338.5","change_pct":-0.2,"tag":""},
    {"name":"KOSPI 거래대금","value":"₩14.2T","change_pct":0.0,"tag":""}
  ],
  "flow": {
    "foreign_net_ko":"외인 +₩890B 순매수 · 반도체 집중",
    "foreign_net_en":"Foreign net buy +₩890B · semis-heavy",
    "institution_net_ko":"기관 -₩320B 순매도 · 자동차/2차전지",
    "institution_net_en":"Institutional net sell -₩320B · auto/battery",
    "retail_net_ko":"개인 -₩570B",
    "retail_net_en":"Retail net sell -₩570B"
  },
  "kr_themes": [   // 9 KR sector tiles
    {"label_ko":"반도체","label_en":"SEMIS","pct":1.8,"names":"005930 +1.5 · 000660 +2.6"},
    {"label_ko":"2차전지","label_en":"BATTERIES","pct":-0.7,"names":"..."},
    {"label_ko":"자동차","label_en":"AUTO","pct":0.3,"names":"..."},
    {"label_ko":"바이오","label_en":"BIOTECH","pct":-1.2,"names":"..."},
    {"label_ko":"게임/엔터","label_en":"GAMING/ENT","pct":2.4,"names":"..."},
    ...
  ],
  "winners": [...],   // same shape as us-close-recap winners
  "losers": [...],
  "kr_news": [...],   // same shape as kr-open-brief kr_news
  "tonight_us": {
    "earnings_ko":"오늘 밤 어닝 — CSCO (수요일 마감 후) · MNDY · ...",
    "earnings_en":"Tonight's US earnings — CSCO · MNDY · ...",
    "macro_ko":"매크로 — CPI 발표 · 10년물 입찰 ...",
    "macro_en":"Macro — CPI · 10Y auction ...",
    "premarket_ko":"미국 프리마켓 (KST 18:00) 주목 — NVDA · INTC ...",
    "premarket_en":"US pre-market (6PM KST) watch — NVDA · INTC ..."
  },
  "bottom_line_ko": "3-5 문장",
  "bottom_line_en": "3-5 sentences",
  "sources": [...],
  "og_data": {
    "card1":{"tick":"KOSPI","val":"3,250","sub":"+0.42%","color":"up"},
    "card2":{"tick":"KOSDAQ","val":"...","sub":"...","color":"up"},
    "card3":{"tick":"외인","val":"+₩890B","sub":"FLOW","color":"gold"},
    "card4":{"tick":"USDKRW","val":"1,338","sub":"-0.2%","color":"up"}
  }
}
```

## Style
- Korean version is primary; English version is for international readers tracking KR.
- "tonight_us" section is the critical bridge to slot ④.
- If KR holiday today, return `{"skip": true}`.
