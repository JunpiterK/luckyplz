# Hacker News · Show HN

**최우선 화력**. HN 1면 진입 시 단일 day 30K+ 트래픽 + 평생 백링크.

**시간대**: 화/수/목 미국 동부 09:00~10:00 (EDT). 한국시간 22:00~23:00.
**Show HN 룰**: 본인이 만든 것만, 라이브 데모 가능, 원격 commerce X.

---

## SUBMIT

**Title (60자 이하):**
```
Show HN: SpaceX IPO valuation calculator with mega-cap comparison
```

(Backup titles)
```
Show HN: SpaceX IPO countdown, valuation calc, and 5Y investment simulator
Show HN: I built three SpaceX IPO tools to help retail investors model the deal
```

**URL:**
```
https://luckyplz.com/tools/spacex-valuation-en/
```

(Reasoning: Valuation calc 가 가장 즉시 인터랙티브 — HN 사용자가 첫 화면에서 슬라이더 만지면 retain. Countdown 보다 dwell ↑.)

---

## FIRST COMMENT (post immediately as OP — important for context)

```
Hey HN — This started as me trying to figure out what $1.75T market cap would actually mean per share for SpaceX (~3.3B fully-diluted shares means ~$530/share if the underwriter target sticks). The Bloomberg widget is locked behind a paywall and Sacra's data is paywalled too, so I extracted the public ranges and built a slider.

Three live tools, all client-side (no backend, no analytics besides GA4):

1. Valuation calc (the linked page) — slider for market cap, get implied share price, P/S multiple vs 2026E ~$28B revenue, global rank vs the top 10 mega-caps
2. Live countdown — https://luckyplz.com/tools/spacex-countdown-en/  with four milestones (S-1 confidential ✓ Apr 1, public S-1 mid-May, roadshow Jun 8 wk, IPO target Jun 29)
3. 5Y investment simulator — https://luckyplz.com/tools/spacex-invest-sim-en/  lump-sum vs DCA, 100% IPO vs ETF mix vs 100% ETF (with NAV-premium drag modeled at 3-5%/yr), benchmarked vs S&P 500. URL state syncs so you can share results.

The deep-dive analysis behind the assumptions (CAGR ranges, Y1 IPO ±20% vol, the xAI consolidation P&L double-count): https://luckyplz.com/blog/spacex-ipo-2026-en/

What I'd love feedback on:
- Is the ~3.3B FD share assumption defensible? Anyone has a tighter source?
- ETF drag at -3 to -5%/yr — too generous or too harsh? DXYZ has historically traded at huge NAV premiums.
- Sharpe-like ratio implementation: I'm using (alpha / bull-bear range) as a volatility proxy. Real risk-adjusted return would need a Monte Carlo. Worth adding?

Tech notes: vanilla HTML/CSS/JS, no framework, no build step, single static HTML per tool. URL state via querystring → fully shareable. Hosted on Cloudflare Pages.
```

---

## TYPICAL HN OBJECTIONS — REPLIES READY

**"This is just promotion"** →
"Fair flag. The site has Adsense (still pending), and yes I want traffic. But the tools themselves are calculator-grade — try the slider, share a state URL, and tell me what's wrong with the math. Source code I'm happy to MIT-license if anyone asks."

**"$1.75T is dot-com bubble"** →
"PitchBook's fair-value range is $1.1T-$1.7T, so $1.75T is at the upper edge. The Bull/Base CAGR I use (30% / 12%) come from Sacra's published distribution. Bear case is -8% which prices in another Starship multi-year slip + xAI losses + FCC pushback."

**"Why does this need to exist when X has live data"** →
"X has the spot price after listing. None of these have pre-IPO scenario modeling at this granularity. Closest equivalent is the Sacra paywall report ($499). I'd love this to be free."

**"Mid-2026 mega-caps numbers are guesses"** →
"Yes — annotated as 2026.05 estimates. Slider lets you adjust. Share me your preferred numbers and I'll update the constants."

---

## POST-SUBMISSION TACTICS

1. **First 30 minutes**: don't refresh. Don't comment own thread until at least one external comment.
2. **First 2 hours**: respond to every comment, even hostile. HN ranking algorithm weights early engagement.
3. **If front page (~30+ points in 1h)**: don't share elsewhere yet — let HN traffic compound.
4. **If sinking (no traction in 1h)**: don't repost same day. Wait 1 week, try alt title.

## MEASUREMENT

GA4 acquisition = `Direct` mostly (HN strips referrer); track via:
- Time-window correlation (sudden spike = HN)
- `?utm_source=hn` if you add UTM to first comment URL (small inconvenience but worth it)
