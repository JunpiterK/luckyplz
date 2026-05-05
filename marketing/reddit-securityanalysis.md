# r/SecurityAnalysis · 학술 톤

**서브**: r/SecurityAnalysis (250K)
**룰**: 매우 strict, 학술 톤 필수, 1차 자료 + 모델 첨부 권장
**시간대**: 평일 09:00 EDT
**예상**: 50~200 upvotes, 깊이 있는 댓글 (애널리스트, 펀드매니저)

---

## TITLE

```
SpaceX IPO valuation framework: $1.75T target sits at 95-115x sales — defensible or stretched?
```

---

## BODY

```
SpaceX is targeting $1.75T market cap with the public S-1 expected mid-May 2026, roadshow June 8 week, and IPO around June 28-29.

I've been working through the valuation framework using primary sources (PitchBook, Sacra Equity Research, Reuters S-1 review, Bloomberg, Quilty Space). Posting the model here for sharper minds to push back.

# Forward earnings setup

PitchBook fair-value range: **$1.1T – $1.7T**.
Underwriter target: **$1.75T** (above the analyst range — typical for hot deals, but worth flagging).

2026E revenue: **~$28B** (Sacra mid-range; Quilty has $25-30B).
P/S target multiple: ~**62x**.

Comparable multiples:
- AWS: ~15x sales
- NVDA: ~30x sales
- Tesla peak: ~75x sales (early 2021, since contracted)

So the 62x multiple sits between Tesla peak and NVDA. The implicit thesis is that SpaceX justifies premium-AI multiples + premium-launch monopoly + premium-comms-moat simultaneously.

# Sum-of-the-parts breakdown (Base case)

| Segment | 2025 Rev | 2026E Rev | EBITDA Margin | Implied EV |
|---------|----------|-----------|---------------|------------|
| Starlink | $11.4B | $16-20B | 60-63% | $400-500B (5-6x rev) |
| Falcon launch | $4.1B | $5-6B | ~35% | $30-40B (5-6x rev) |
| Govt/Starshield | ~$3.5B | $6-7B | ~40% | $40-50B (6x rev) |
| xAI/Grok | ~$0.5B | $2-3B | deep loss | $100-150B (50-60x rev) |
| **SOTP Total** | | | | **$570-740B** |

That leaves **$1T-$1.2T of "strategic premium"** — which is where the bear/bull divergence happens.

The premium represents:
- Starship V3 normalization (orbital propellant transfer + 150t LEO)
- Direct-to-Cell mass deployment (EchoStar spectrum integration)
- Artemis HLS execution
- Orbital data centers (1M satellite FCC filing → 100GW/year AI compute)
- Mars optionality

# Pattern matching against history

Operating Musk programs (Falcon 1 → 9, Starlink) hit announced timelines within ±10%.
New vehicles (Falcon Heavy, Crew Dragon, Cybertruck, Roadster v2) slip 2-5 years.

Starship is currently 5x behind plan: 5 flights in 2025 against 25 target. V3 first flight is targeted mid-May 2026, literally weeks before IPO. If V3 succeeds → bull thesis intact. If it fails → expect IPO reset of -10% to -15%.

# xAI consolidation (the wildcard nobody's pricing right)

February 2026 all-stock merger at $250B/$1T ratio. Consequences:
- 2025 P&L flips from +$791M (legacy SpaceX) to estimated -$5B (consolidated)
- ~$1B/month burn rate (Bloomberg)
- 61% of capex absorbed by AI infrastructure
- 12 founding members → ~2 of original co-founders remaining (FT, March 2026)

Counterargument: Grok 4 outperforms GPT-5 (9.9%) and Gemini 2.5 Pro (21.6%) on ARC-AGI-2 (15.9%). Compute infrastructure (200K H100 → 1M GPU target) is genuinely industry-leading.

But the key risk: if xAI commercial revenue stays at $0.5B/year against $12.7B/year capex absorption, the unit economics don't close even at the optimistic Sacra projections. Either Grok subscription monetization 10x's by 2027, or xAI becomes a structural drag on the consolidated enterprise.

# Accounting reconciliation needed

Source variance is uncomfortable:
- Reuters S-1 review: **$18.7B revenue / $4.9B loss** for 2025 consolidated
- Sacra/PitchBook: **$15-16B revenue / $8B profit** (different consolidation timing)

Until the public S-1 is filed, this gap can't be reconciled. The differential is large enough ($11B+) to materially shift the valuation framework.

# Allocation reality

The 30% retail tranche ($22.5B) flows through wirehouse priority lists:
- Schwab/Fidelity Premier ($1M+ in qualifying assets) gets meaningful allocation
- Robinhood IPO Access lottery: typical fills 0-5 shares
- IBKR Pro indication of interest: pro-rata, $10K request → 1-2 shares typical for hot deals

For accounts under $250K, expect zero direct allocation. Indirect exposure pathways:
- XOVR (16.2% SpaceX) — most balanced ETF
- DXYZ (23% SpaceX) — highest concentration but historically traded at +120% NAV premium pre-IPO of comparable names
- RONB (14-22%) — newer, less liquidity
- EchoStar (SATS) — holds direct SpaceX equity from $17B 2025 spectrum deal

# What I'd push back on in my own thesis

1. The 3.3B FD share assumption: implied from $1.75T/$530, but actual count could vary by ±5% depending on comp package execution.
2. The 62x multiple anchor: NVDA's 30x already includes AI optionality. Layering SpaceX-specific moats on top might justify 45-55x without claiming 62x.
3. Bull CAGR of 30% for 5 years: optimistic relative to historical hyperscaler trajectories. AWS managed 30%+ for 7 years but at much smaller revenue base.
4. Pre-IPO ETF NAV premium model: my drag assumption (3-5%/year) might be too low if the post-IPO re-rating is steeper than the comps.

# Tools

If helpful for sensitivity analysis:
- Slider-based valuation calc with global rank: https://luckyplz.com/tools/spacex-valuation-en/
- Investment simulator with DCA, ETF mix, S&P 500 benchmark: https://luckyplz.com/tools/spacex-invest-sim-en/
- Full deep dive: https://luckyplz.com/blog/spacex-ipo-2026-en/
- Risk matrix with quantified probabilities: https://luckyplz.com/blog/spacex-ipo-risks-en/

Looking for substantive critique on:
- The SOTP framework — am I missing segments?
- The xAI revenue ramp assumption
- The Starship V3 binary risk pricing
```

---

## REPLY 운영

### 톤
- 학술적, 정중. 절대 농담/밈 X.
- 모든 응답에 1차 자료 인용.
- 본인 모델 한계 솔직히 인정.

### 자주 나올 댓글

**"Why P/S not P/E or DCF?"**
"Fair point. DCF doesn't anchor for SpaceX given the negative consolidated earnings. I default to P/S because (a) the bull case requires multi-segment revenue scaling, (b) Sacra/PitchBook also use revenue multiples for comparable. I'd happily build a DCF if anyone has terminal value assumption — likely 4-5% perpetual on the launch+Starlink legs."

**"Your xAI revenue model is too rosy"**
"Likely true. The $2-3B 2026E xAI revenue assumes Grok subscriptions reach $300/mo SuperGrok pricing across 800K-1M paid users. Grok currently has 200-300K paid (estimates vary). Halving that → drops xAI segment value $50-60B."

**"What's the public-comp for orbital data centers"**
"Honestly nothing close. Orbital DC is the most speculative leg. ARK estimated $100/kg launch cost makes orbital compute 25% cheaper than terrestrial — but the full lifecycle cost (radiation hardening, autonomous service, deorbit) probably adds 50%+ on top. I'd ascribe minimal value at IPO until first commercial orbital DC contract is signed (2027-2028)."
