# Daily Market Post Prompts

이 디렉토리의 4개 `.md` 파일은 매일 자동 발행되는 증시 글 4종의 **Claude 프롬프트 본문**이야. cron이 발화시킨 `scripts/auto-daily-post.py` 가 슬롯에 맞는 파일을 읽어 `{trading_date}` / `{publish_date}` 를 치환한 뒤 Claude 에게 전달한다.

> 발화 시각·시장 매핑·휴장 가드는 코드 쪽에 있다. 이 README는 **4개 슬롯이 어떻게 다른가** 만 다룬다.
>
> - 시각/cron: [`.github/workflows/daily-cron.yml`](../../.github/workflows/daily-cron.yml)
> - 슬롯 메타데이터 (slug 접두사, 이모지, 헤더 라벨): `SLOTS` dict in [`auto-daily-post.py`](../auto-daily-post.py)
> - 시장 매핑 (XNYS/XKRX): `SLOT_TO_MARKET` dict 같은 파일
> - HTML 골격: [`../templates/daily-base.html`](../templates/daily-base.html)

---

## 1. 슬롯 한눈 비교표

| | ① us-close | ② kr-open | ③ kr-close | ④ us-premarket |
|---|---|---|---|---|
| **파일** | `us-close-recap.md` | `kr-open-brief.md` | `kr-close-recap.md` | `us-premarket.md` |
| **cron (UTC)** | `0 21 * * *` | `30 22 * * *` | `45 6 * * *` | `30 12 * * *` |
| **발행 (KST)** | 06:00 | 07:30 | 15:45 | 21:30 |
| **독자 컨텍스트** | 출근 전 미국장 리캡 | 지하철, KOSPI 개장 90분 전 | KOSPI 마감 15분 후 | 미국장 개장 직전 (= 08:30 ET) |
| **시장** | XNYS | XKRX | XKRX | XNYS |
| **trading_date offset** | -1 일 (어제 미국장) | 0 일 (오늘) | 0 일 (오늘) | 0 일 (오늘) |
| **slug 접두사** | `us-tech-recap-` | `kr-open-brief-` | `kr-tech-recap-` | `us-premarket-` |
| **헤더 라벨 KO** | 미국 테크 마감 리캡 | 한국장 개장 브리핑 | 한국 테크 마감 리캡 | 미국 프리마켓 브리핑 |
| **헤더 라벨 EN** | US TECH DAILY RECAP | KOREA OPEN BRIEF | KOREA TECH DAILY RECAP | US PRE-MARKET BRIEF |
| **이모지** | 🇺🇸 | 🇰🇷 | 🇰🇷 | 🇺🇸 |
| **읽기 시간** | 8 분 | 6 분 | 7 분 | 6 분 |

---

## 2. 4 슬롯 공통 골격 (V4)

각 프롬프트는 같은 8개 섹션 구조를 따른다. 슬롯별로 다른 건 **데이터 항목**과 **검증 소스 리스트** 뿐이다.

```
## Role            ─ 독자 컨텍스트 (몇 시 누가 읽는지)
## Iron Rules      ─ 4개 원칙: 데이터 정확성·억측 금지·간결성·plain-text summary
## Visual Rules    ─ KR 컨벤션 (🔺 상승 = RED, 🔻 하락 = BLUE)
## Slot Context    ─ 발행 시각, trading_date, 휴장시 skip
## Data Required   ─ ◀ 슬롯별 차이가 가장 큰 곳
## narrative_html  ─ STRICT 4 섹션: TLDR → 결론 → 핵심 deep dive → bottom_line
## Output Contract ─ STRICT JSON 스키마
## Hard Rules      ─ JSON only, no fences, no trailing commas
```

### narrative_html 4 섹션 규약

```html
<!-- ① TLDR 박스 (4-5 bullets) -->
<div class="tldr-box"><h3>⚡ 30초 요약</h3><ul>...</ul></div>

<!-- ② 오늘의 결론 (1 단락, 3-5 문장) -->
<h3>오늘의 결론</h3>
<p>...</p>

<!-- ③ 핵심 deep dive (1 h3 + 2-3 h4, 각 h4 당 2-3 문장) -->
<h3>📊 오늘의 핵심 — [세션의 단일 결정적 테마]</h3>
<p>...</p>
<h4>...</h4><p>...</p>
<h4>...</h4><p>...</p>

<!-- ④ bottom_line — 별도 JSON 필드 (narrative_html 안에 넣지 말 것) -->
```

**금지 사항 (4 슬롯 공통):**
- `<table>` 금지 (CSS grid 카드만)
- 스키마 데이터 (`indices` / `mag7` / `winners` 등) 를 narrative 안에서 다시 풀어쓰지 말 것
- `<h3>` 최대 3개
- 각 `<h4>` 뒤 본문 최대 3 문장
- 시나리오 트리·forward calendar 는 별도 필드 (`forward_calendar_html_ko`)

---

## 3. 슬롯별 차이 — 필수 데이터

### ① us-close (미국 마감 리캡)

| 카테고리 | 항목 |
|---|---|
| 지수 | Dow, S&P 500, Nasdaq, Russell 2000 — 종가·일간 %·일중 레인지 |
| 섹터 | 11 GICS ETF 전부 (XLK, XLF, XLV, XLY, XLP, XLE, XLI, XLB, XLU, XLRE, XLC) |
| 채권/통화 | US 2Y/10Y/30Y, 2s10s spread, DXY, VIX |
| 종목 | Mag 7 + AVGO 종가·%, S&P 500 winners/losers top 5 (촉발 이슈) |
| 어닝 | 마감 후 Big Tech 어닝 — EPS actual/est, revenue actual/est, guidance, AH % |
| 검증 소스 | WSJ, Reuters, CNBC, Yahoo Finance, Briefing.com, SEC EDGAR |

### ② kr-open (한국 개장 브리핑)

| 카테고리 | 항목 |
|---|---|
| 미국 오버나이트 | S&P, Nasdaq, Dow, Russell 2000 + **SOX (반도체)** ← 삼성/SKH 직결 |
| 빅테크 | AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA, AVGO |
| 채권/통화 | US 10Y/2Y, VIX, DXY |
| ADR | CPNG, PKX, KB |
| KR 야간 선물 | KOSPI 200, KOSDAQ (CME night) |
| 갭 watch | 4-6 종목 (종목코드, 오버나이트 촉발, 예상 갭 %) |
| 오늘 일정 | IPO, lock-up, 공시, 거시 데이터, Fed 발언 |
| 검증 소스 | Investing.com, Yahoo Finance, KRX, Naver Finance, Reuters |

### ③ kr-close (한국 마감 리캡)

| 카테고리 | 항목 |
|---|---|
| 지수 | KOSPI, KOSDAQ, KOSPI200, VKOSPI — 종가·일간 % |
| 거래 | 거래대금 (조원) |
| 수급 | 외국인 / 기관 / 개인 net (억원, KOSPI · KOSDAQ 분리) |
| 종목 흐름 | 외인 매수/매도 top 5, 기관 매수/매도 top 5 (각 종목코드 + 촉발) |
| 등락 | KOSPI + KOSDAQ daily gainers/losers top 5 |
| 테마 | 1-3개 강세 테마 (AI 반도체, 배터리, 방산, 조선, 원자력, 바이오, 엔터 등) + 주도 종목 |
| 공시 | 주요 KIND 공시 1-3건 |
| 검증 소스 | KRX, KIND, Naver Finance, 한국경제, Reuters Korea |

### ④ us-premarket (미국 프리마켓)

| 카테고리 | 항목 |
|---|---|
| 선물 | ES, NQ, YM, RTY — 레벨·오버나이트 % |
| 채권/통화 | 2Y/10Y/30Y, DXY, VIX 선물 |
| 프리마켓 | top movers (Yahoo Finance / MarketWatch / Benzinga) |
| **08:30 ET 데이터** | CPI/PPI/NFP/Jobless/GDP/Retail — actual vs consensus vs prior (오늘 발표 없으면 **명시적으로 밝힐 것**) |
| 글로벌 오버나이트 | KOSPI, Nikkei, HSI, DAX, FTSE, STOXX 50 |
| 종목 | Mag 7 프리마켓 |
| 이벤트 | 프리벨 어닝 반응, Fed speaker 일정 |
| 검증 소스 | BLS/BEA, Investing.com, Yahoo Finance, MarketWatch, Briefing.com |

---

## 4. 공통 강제 항목

### Fixed 7-Asset Strip
모든 슬롯이 동일한 7자산을 페이지 최상단 strip에 노출한다. yfinance가 하드 페치해 프롬프트에 **VERIFIED MARKET DATA** 블록으로 주입하므로, Claude 가 환각으로 채울 수 없다.

```
USD/KRW · Gold · Silver · WTI · BTC · ETH · XRP
```

### Visual 컨벤션 (KR 관례)

| 방향 | CSS class | 색상 |
|---|---|---|
| 상승 | `<span class="upx">+1.2%</span>` | RED |
| 하락 | `<span class="dn">-1.5%</span>` | BLUE |
| 강조 | `<span class="hl">키워드</span>` | GOLD |

### JSON 출력 규약 (4 슬롯 공통)

- ONLY JSON — `{` 로 시작, `}` 로 끝. prose·markdown fence 금지
- trailing comma 금지
- `\"` 이스케이프
- 모든 수치 verified — 모르면 omit (절대 추정·반올림 금지)
- 발행시 휴장이면 `{"skip": true, "reason": "..."}` 반환 (실제로는 코드의 `is_trading_day()` 가드가 먼저 차단해서 여기까지 안 옴)

### 양 언어 동시 생성
모든 JSON 필드가 `_ko` / `_en` 쌍으로 정의되어 **Claude 1회 호출 → 한·영 JSON 동시 생산**. 그 뒤 `render_html(slot, "ko", data)` + `render_html(slot, "en", data)` 가 같은 data dict 으로 2개 HTML 을 뽑는다. 결과: 한·영 본문의 숫자가 100% 일치.

---

## 5. 런타임 주입되는 외부 블록

프롬프트 파일 자체에는 안 적혀 있지만, `auto-daily-post.py` 가 **매 호출마다 프롬프트 앞에 두 블록을 자동 prepend** 한다:

### (1) VERIFIED MARKET DATA — yfinance 하드 페치

```
=== VERIFIED MARKET DATA (Yahoo Finance, fetched {publish_date}) ===
S&P 500: 6,047.xx (-1.24%)
Nasdaq: ...
... 36 tickers ...
=== END VERIFIED DATA — USE THESE NUMBERS, do NOT substitute training-data values ===
```

Claude 학습 컷오프가 2024 라서 "오늘의 S&P 종가" 라고 물으면 2024 숫자가 튀어 나오는 환각 문제를 끊으려고 도입. 이 블록이 들어가면 Claude 는 narrative 만 쓰고 숫자는 못 바꾼다.

### (2) OPERATING CONTEXT — 미래 날짜 self-skip 방지

```
# ⚠️ OPERATING CONTEXT
This is a **live production cron** firing in real time on luckyplz.com.
Today's date is **{publish_date} KST**. trading_date **{trading_date}** is real.

If your training cutoff makes today's date feel "future" or "fictional",
IGNORE that intuition. web_search results dated near {trading_date} are
**authoritative ground truth** — never label them as simulated.

Never return {"skip": true} based on "future date" or "cannot verify
because of cutoff" reasoning. The ONLY valid skip is a documented holiday.
```

2024 컷오프 모델이 2026 날짜를 보고 `{"skip": true, "reason": "future date"}` 를 뱉어 파이프라인을 죽이는 사례가 반복돼서 강제 명시.

---

## 6. 슬롯 추가하려면?

신규 슬롯 (예: `eu-close`) 을 붙이려면 5 곳을 수정해야 한다:

1. **cron 추가** — `.github/workflows/daily-cron.yml` 의 `schedule:` 블록 + `case` 분기
2. **SLOTS dict** — `auto-daily-post.py:50` 에 한 entry (`prompt`, `slug_prefix`, `header_label_ko/en`, `cover_emoji`, `read_min`, `trading_date_offset_days`, `category`)
3. **SLOT_TO_MARKET** — 같은 파일 line 114 에 ISO MIC (예: XLON)
4. **render_html branches** — 같은 파일 line 697·781·957 의 분기에 새 슬롯 케이스
5. **프롬프트 파일** — 본 디렉토리에 `eu-close.md` 작성 (위 8 섹션 구조 그대로 복사 후 데이터 항목·검증 소스만 교체)

---

## 7. 디버깅 포인트

| 증상 | 의심할 곳 |
|---|---|
| 글 안 만들어짐 (휴일도 평일도 아닌데) | GitHub Actions `Daily Market Posts (4 slots)` 워크플로 로그 — cron 발화 실패 / API key / 패키지 설치 |
| 환각 숫자 ("S&P 6,047" 같은 2024 값) | VERIFIED MARKET DATA 블록이 비어 있음 → yfinance 페치 실패 / 티커 변경 |
| 휴일에 글 만들어짐 | `is_trading_day()` 의 exchange_calendars lookup 실패 (graceful fallback 으로 열렸다고 판단) |
| `{"skip": true, ...future date...}` 로 종료 | OPERATING CONTEXT 누락 (model swap 후 인식 실패) |
| JSON 파싱 실패 | trailing comma / 한국어 quote 미이스케이프 — json-repair fallback 통과했는지 확인 |
| 한·영 본문 숫자 불일치 | render_html 이 같은 data 로 호출되는지 확인 — 같으면 양쪽 모두 같은 환각 (위 yfinance 점검) |
| OG 한국어 깨짐 | runner 에 `fonts-nanum` 설치 누락 또는 `FONT_FALLBACKS_BOLD` 순서 잘못 |

---

마지막 업데이트: 2026-05-24 — Master V4 (4 sections, ~700 words KO+EN, strict factuality)
