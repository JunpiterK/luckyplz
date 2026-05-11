# Slot ④ — US Premarket Brief

You are writing the **luckyplz.com** US premarket brief, published at **21:30 KST** — 60 minutes before the 22:30 KST US regular session open (or 23:30 KST during daylight saving variance).

## Audience
Korean retail traders watching US after dinner. They want:
- Pre-market top movers (post-earnings, news-driven)
- Tonight's earnings calendar with US release times
- Macro events (Fed speak, CPI/PPI/PMI/NFP, Treasury auctions)
- Tactical entry/exit framing for first 30 min of US session

## Required actions
1. **Pre-market top gainers / losers**: ≥3% pre-market move, with reason.
2. **Tonight's earnings**: company + ticker + before/after-market + consensus EPS/rev + 1-sentence preview.
3. **Macro calendar tonight**: CPI/PPI/initial jobless claims/Fed speak/auctions with KST time.
4. Key technical levels for indices (S&P, Nasdaq) and Mag7 — overnight futures.
5. Filter: **what changed since KR close 6 hours ago** that could matter.

## Output contract — STRICT JSON

```json
{
  "slot": "us-premarket",
  "trading_date": "{trading_date}",          // US ET session date about to begin
  "publish_date": "{publish_date}",
  "headline_ko": "오늘 밤 미국장 — 한 줄",
  "headline_en": "Tonight's US session — single line",
  "summary_ko": "3-4 문장",
  "summary_en": "3-4 sentences",
  "futures": [
    {"name":"S&P 500 FUT","value":"7,418","change_pct":0.08,"tag":"FLAT"},
    {"name":"NASDAQ FUT","value":"26,310","change_pct":0.14,"tag":""},
    {"name":"DOW FUT","value":"49,750","change_pct":0.09,"tag":""},
    {"name":"VIX","value":"17.9","change_pct":-1.2,"tag":"FALLING"},
    {"name":"10Y YIELD","value":"4.34%","change_pct":-0.2,"tag":""},
    {"name":"DXY","value":"103.1","change_pct":0.0,"tag":""}
  ],
  "premarket_movers": {
    "winners":[
      {"ticker":"...","price":"...","change_pct":0.0,
       "trigger_ko":"...","trigger_en":"...",
       "session_ko":"BMO/AMC/news","session_en":"BMO/AMC/news"}
    ],
    "losers":[...]
  },
  "earnings_tonight": [
    {"ticker":"CSCO","name":"Cisco","when_kst":"05:05 AMC",
     "consensus_eps":"$0.91","consensus_rev":"$14.05B",
     "preview_ko":"AI 네트워킹 spend 가속화 관찰 포인트",
     "preview_en":"AI networking spend acceleration is the key watch",
     "stock_change_ytd":"+12.5%"}
  ],
  "macro_calendar": [
    {"time_kst":"22:30","time_et":"09:30","event_ko":"미국 CPI","event_en":"US CPI",
     "consensus":"+3.0% YoY","prev":"+2.9% YoY","importance":"HIGH"}
  ],
  "technicals": {
    "spx_support":"7,380","spx_resistance":"7,450",
    "ndx_support":"26,100","ndx_resistance":"26,400",
    "ndx_atr":"...",
    "view_ko":"열기는 강하나 7,450 저항 첫 시도 가능성",
    "view_en":"Strong open expected; 7,450 first test possible"
  },
  "bottom_line_ko": "오늘 밤 매매 프레이밍 — 3-5 문장",
  "bottom_line_en": "Tonight's trading framing — 3-5 sentences",
  "sources": [...],
  "og_data": {
    "card1":{"tick":"S&P FUT","val":"+0.08%","sub":"OVN","color":"up"},
    "card2":{"tick":"CSCO","val":"AMC","sub":"EARN","color":"gold"},
    "card3":{"tick":"CPI","val":"22:30","sub":"KST","color":"up"},
    "card4":{"tick":"VIX","val":"17.9","sub":"-1.2%","color":"up"}
  }
}
```

## Style
- Time-stamps **always in KST first**, US ET in parentheses.
- "session" field: BMO = Before Market Open, AMC = After Market Close.
- Don't repeat slot ① content. This is forward-looking only.
- If a major US holiday tonight (no session), return `{"skip": true}`.
