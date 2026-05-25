# Blog Authoring Guide (luckyplz.com)

이 문서는 [CLAUDE.md](../CLAUDE.md) 의 **Blog Authoring (MANDATORY)** 섹션을 상세화한다. 새 글 작성 전·중·후에 참조한다.

> **TL;DR** — 모든 새 블로그 글은 **한국어 + 영어 + 일본어 + 중국어(간체) 4종** 동시 작성. `scripts/new-blog-post.py` 로 비계 만들고, 본문 채우고, `bump-cache.sh` 돌리고, push. 끝.

---

## 1. 사이트 정체성 (작성 전 항상 떠올릴 것)

luckyplz.com 의 블로그는 **테크 위주 깊이 있는 글** 이 중심이다. 사이트 운영자의 말 그대로 옮기면:

> "게임은 소소하게 친구들과 쓰는 도구, 블로그는 테크 위주 깊이 있는 글. 둘 다 한국어·영어·일본어·중국어 4종 동시 운영."

이 정체성을 벗어나는 글 (예: 잡담식 일기, 가십, 정치 의견) 은 만들지 않는다.

### 자동발행 글 = 영어 원천 + 3 언어 번역
자동발행 증시 글은 **영어로 원천 작성** 한 뒤 같은 Claude 호출에서 ko·ja·zh 로 자연스러운 번역을 함께 출력한다. 영어가 source-of-truth. 6 슬롯 (us·kr·cn 각 개장/마감) × 4 언어 = 매일 24개 글.

---

## 2. 카테고리 6종 — 어디에 분류할지

posts.js 의 `category` 필드는 6종 중 하나. **카테고리는 블로그 메인의 필터 탭에 그대로 노출**되므로 일관성 중요.

| 카테고리 | 정의 | 톤·길이 | 대표 예시 |
|---|---|---|---|
| **ai-tech** | AI 모델·기업·역사·기술 | 깊이 있게, 12~18분 | Anthropic 시리즈, AI 진화사 (ai-evo-01~08) |
| **space-tech** | 우주 산업 전체 (SpaceX·Starlink·발사·계약·IPO·우주사) | 깊이 있게, 12~20분 | SpaceX IPO, Starship 발사, 우주 진화사 (space-evo-01~10), Echo Star 위성 |
| **industry** | AI 외 산업 (반도체·데이터센터·로봇·태양광·자동차·바이오) **+ 자동 발행 증시 글** | 6~14분 | AI 데이터센터 전력, 반도체 랠리, 자동발행 us-tech-recap 등 |
| **gaming-history** | 레트로 게임 역사·문화 | 가볍게, 6~10분 | Pacman Namco, Tetris Soviet, Snake Nokia, Breakout Jobs/Wozniak |
| **lifestyle** | 일상·공정성·작은 결정 도구 | 가볍게, 4~8분 | Coffee 1 Minute, Coffee Who Pays, Dinner Menu Fair, Wedding MC Games |
| **probability** | 확률·랜덤·로또 분석 | 6~12분 | Lotto History, Ladder Fairness, Lotto Country Compare, Powerball Random |

### 카테고리 추가 절차 (향후 확장)
1. 6종 안에 안 맞는 글 후보가 누적 5편 이상 모이면 새 카테고리 검토.
2. 추가 시 수정 위치:
   - [posts.js](../public/blog/posts.js) 의 상단 코멘트
   - [CLAUDE.md](../CLAUDE.md) "Site Identity" 섹션의 카테고리 목록
   - 본 문서의 위 표
   - [blog/index.html](../public/blog/index.html) 의 필터 탭 (`#cat=…` 매핑)
3. 한 번에 6편 미만이면 카테고리 추가하지 말 것 — 필터 탭이 비어 보이면 사이트 인상이 나빠진다.

---

## 3. 시리즈물 — 현재 운영 중인 시리즈

시리즈는 **일관된 시각 테마**를 가진다. 새 시리즈 시작 시 본 표에 등록.

### 3.1 An Anthropic Story (`ai-tech`)
- **테마**: 베이지 책 (paper `#f5ebd8`, ink `#2c2416`, auburn `#c2410c`, gold `#b8860b`)
- **폰트**: Noto Serif KR + Cormorant Garamond + JetBrains Mono
- **구조**:
  ```
  Hero (series · episode · title · subtitle · meta)
  ├─ Prologue (chapter-num: Prologue)
  ├─ Chapter 1..N (chapter-num: Chapter One / Two / …)
  ├─ Epilogue (chapter-num: Epilogue)
  ├─ series-nav (다음 회 안내)
  ├─ footnotes (참고 자료)
  └─ footer-block (시리즈 안내 + 면책)
  ```
- **현재 발행**: Ep.1 (창립), Ep.2 (Amodei 형제), Ep.3 (Claude 진화사). Ep.4~6 예정.

### 3.2 AI Evolution (`ai-tech`, slug 접두사 `ai-evo-`)
- **테마**: 표준 블로그 스타일 (mobile-first inline + blog-desktop.css)
- **현재 발행**: ai-evo-01~08 (Perceptron → CNN → Transformer → ChatGPT → Diffusion → GPU → Fab → RAG)
- **앞으로 추가될 수도 있는 회**: AI Alignment, AI Energy, AI Robotics 등.

### 3.3 Space Evolution (`space-tech`, slug 접두사 `space-evo-`)
- **테마**: 표준
- **현재 발행**: space-evo-01~10 (Paperclip → Sputnik → Gagarin → Tragedies → Apollo11 → Soviet Loss → Shuttle → Voyager → Falcon1 → Reusable)

### 3.4 SpaceX IPO 다국어 시리즈 (`space-tech`, slug 접두사 `spacex-ipo-2026`)
- **테마**: 표준
- **언어**: Tier B (ko, en, de, es, hi, jp, zh 7종) — SpaceX IPO 라는 글로벌 검색 트래픽 타깃.

### 시리즈 추가 절차
1. 최소 3편 이상 기획되어 있을 때만 시리즈로 시작.
2. 시각 테마 결정 (베이지 책 / 표준 / 새 테마).
3. 새 테마면 첫 편 작성 시 CSS 전체를 inline 으로 박고 다음 회들이 같은 CSS 를 복사.
4. 본 문서의 3.x 항에 등록.
5. `scripts/new-blog-post.py --series <name>` 옵션 추가 (Tier 2 스크립트 도입 후).

---

## 4. 본문 작성 톤 가이드 (사용자가 반복 강조한 원칙)

이 절은 **모든** 블로그 글에 적용. 시리즈물뿐 아니라 단편에도.

### 4.1 사람 글 느낌 — 5 가지 금기·5 가지 권장

#### 금기
1. **em-dash (`—`) 사용 금지** — 단절감, 기계가 만든 글 같은 인상. 쉼표·세미콜론·새 문장으로 풀어 쓸 것. 단, 시각적 장식 (`<span class="ornament">` 안의 디바이더, hero 의 `·` 구분자) 은 예외.
2. **AI 자기언급 금지** — "이 글은 Claude 가 작성했습니다", "AI 가 정리했습니다" 같은 메타 문장 절대 금지. 사람들은 본능적으로 AI 가 만든 글에 거부감이 있다 (사용자 명시).
3. **문장 종결 한 가지로 도배 금지** — "~다." "~다." "~다." 연속 금지. "~었다.", "~이다.", "~다." 를 섞을 것.
4. **단절감 있는 문장 끊기 금지** — "그것은 컸다. 그것은 빨랐다. 그것은 강했다." 같은 짧은 단문 연속. 풀어서 한 문장에 정리하거나 접속사로 잇기.
5. **천박한 톤 금지** — "ㅎㅎ", "ㅋㅋ", 과한 이모지, 인터넷 밈 인용. 진지한 스토리텔링이 사이트 정체성.

#### 권장
1. **dropcap 사용** — 챕터 첫 문단에 `<p class="dropcap">` (베이지 책 테마). 시각적 입구.
2. **pullquote 사용** — 인용문 강조 시 `<div class="pullquote">` (출처를 `.attr` 로). 한 챕터당 1~2개 적정.
3. **sidebar 박스** — 부가 사실 요약 (`<div class="sidebar">`). 본문 흐름을 끊지 않으면서 정보 압축.
4. **숫자에 구체성** — "많은 사용자" 대신 "약 천만 명", "큰 점프" 대신 "약 두 배의 점프". 단, 검증되지 않은 숫자는 절대 쓰지 말 것 (자동발행 글의 Iron Rule 그대로).
5. **시간·장소·인물의 좌표** — "그날", "거기서" 대신 "2023년 3월 14일", "Princeton", "Dario Amodei". 좌표가 있으면 신뢰가 생긴다.

### 4.2 한국어 ↔ 영어 ↔ 일본어 ↔ 중국어(간체) 번역 원칙

- **원천 언어 먼저** (수동 작성=ko, 자동발행=en), 그 뒤 자연스러운 나머지 언어판으로 다시 쓴다. 기계번역체 절대 금지.
- 모든 언어판은 **same data, different voice** — 원천 언어의 표현을 그대로 옮기면 어색해진다. 각 독자에게 자연스러운 구성·관용 표현으로.
- 일본어판은 **존경어/정중체 (です·ます調) 기본** — 사이트 톤이 진지하므로. 캐주얼체 (だ·である) 는 시리즈물에서 제한적 사용.
- 중국어판은 **간체자 (Simplified) 사용** — `zh-CN` 표준. 정중하지만 딱딱하지 않은 톤. 본토·홍콩·싱가포르·해외 화교 독자 모두 자연스럽게 읽도록.
- 숫자·날짜·인용문·고유명사는 4 판 모두 일치. 다른 톤은 표현, 같은 톤은 사실.
- 길이는 ±15% 안에서 맞춘다. 한쪽이 두 배 길면 다른 쪽이 부실하다는 신호.

### 4.3 면책·출처 표기 표준

모든 글 footer 의 `footer-block` 또는 동등한 박스:
- 출처: 공개 인터뷰·언론 보도·기업 공식 발표·공식 SEC 파일링 등
- 일부 세부 (특히 사적인 가족 배경, 회사 내부 결정 시점) 는 추정·재구성될 수 있음을 명시
- 자동 발행 증시 글은 `fact_check_ko/en/ja` 필드로 교차검증 출처 명시 (이미 시스템에 박혀 있음)
- 시리즈물은 다음 회 안내 (`series-nav`) 포함

---

## 5. 메타데이터 표준 (SEO 안전판)

각 언어판 HTML 의 `<head>` 에 들어가야 할 필수 메타. `new-blog-post.py` 가 자동 생성하지만 수정 시 확인.

### 5.1 공통 (3 언어판 모두)
```html
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!--lp-build-check:start--> (cache airbag, bump-cache.sh 가 자동 주입)
```

### 5.2 언어별로 다른 부분
| 항목 | ko | en | ja | zh |
|---|---|---|---|---|
| `<html lang="…">` | `ko` | `en` | `ja` | `zh` |
| `<title>` | 한국어 제목 | English title | 日本語タイトル | 中文标题 |
| `<meta name="description">` | 한국어 | English | 日本語 | 简体中文 |
| `<meta property="og:locale">` | `ko_KR` | `en_US` | `ja_JP` | `zh_CN` |
| `<link rel="canonical">` | `…/<slug>/` | `…/<slug>-en/` | `…/<slug>-ja/` | `…/<slug>-zh/` |

### 5.3 hreflang 상호 링크 (4개 — 모든 언어판 동일하게 박힘)
```html
<link rel="alternate" hreflang="ko" href="https://luckyplz.com/blog/<slug>/">
<link rel="alternate" hreflang="en" href="https://luckyplz.com/blog/<slug>-en/">
<link rel="alternate" hreflang="ja" href="https://luckyplz.com/blog/<slug>-ja/">
<link rel="alternate" hreflang="zh" href="https://luckyplz.com/blog/<slug>-zh/">
<link rel="alternate" hreflang="x-default" href="https://luckyplz.com/blog/<slug>-en/">
```

### 5.4 JSON-LD BlogPosting (각 언어판 자신을 가리키도록)
```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "…",
  "inLanguage": "ko" | "en" | "ja" | "zh",
  "datePublished": "YYYY-MM-DD",
  "mainEntityOfPage": { "@id": "<canonical url>" }
}
```

---

## 6. posts.js 엔트리 — 4 언어판 등록

새 글 발행 시 [public/blog/posts.js](../public/blog/posts.js) 에 **4 개 엔트리** 추가. 각 엔트리는 `alts` 필드 (객체) 로 다른 3 언어판 슬러그를 모두 가리킨다.

```js
{
    slug: 'anthropic-story-03-claude-evolution',
    lang: 'ko',
    category: 'ai-tech',
    date: '2026-05-25',
    readMinutes: 16,
    coverEmoji: '📖',
    tags: ['Anthropic', 'Claude', ...],
    title: "Claude의 진화 — 1.0에서 4.7까지",
    excerpt: '2023년 봄...',
    alts: {
        en: 'anthropic-story-03-claude-evolution-en',
        ja: 'anthropic-story-03-claude-evolution-ja',
        zh: 'anthropic-story-03-claude-evolution-zh',
    },
},
{
    slug: 'anthropic-story-03-claude-evolution-en',
    lang: 'en',
    // ... 영문판 메타
    alts: {
        ko: 'anthropic-story-03-claude-evolution',
        ja: 'anthropic-story-03-claude-evolution-ja',
        zh: 'anthropic-story-03-claude-evolution-zh',
    },
},
{
    slug: 'anthropic-story-03-claude-evolution-ja',
    lang: 'ja',
    // ... 일본어판 메타
    alts: {
        ko: 'anthropic-story-03-claude-evolution',
        en: 'anthropic-story-03-claude-evolution-en',
        zh: 'anthropic-story-03-claude-evolution-zh',
    },
},
{
    slug: 'anthropic-story-03-claude-evolution-zh',
    lang: 'zh',
    // ... 중국어판 메타
    alts: {
        ko: 'anthropic-story-03-claude-evolution',
        en: 'anthropic-story-03-claude-evolution-en',
        ja: 'anthropic-story-03-claude-evolution-ja',
    },
},
```

> 기존 글은 `alt` 한 필드 (단일 문자열) 만 사용. 신규 글부터 `alts` 객체 컨벤션 적용. **블로그 메인의 언어 라우팅 코드도 이 새 필드를 읽도록 수정 필요** (Task #26 Step 3 에서 처리). 기존 `alt` 는 backward compat 으로 유지.

---

## 7. Tier B (11언어 추가) 승격 절차

기본 모든 글은 **Tier A (ko/en/ja/zh)** 만 만든다. 특정 글이 **글로벌 검색 트래픽** 을 노릴 가치가 있으면 Tier B 로 승격:

- 추가 11언어: `de`, `es`, `fr`, `hi`, `id`, `it`, `pt`, `ru`, `th`, `tr`, `vi`
- 슬러그 컨벤션: `<slug>-de`, `<slug>-es` 등 (현재 `spacex-ipo-2026` 시리즈가 이 패턴)
- 승격 기준 (다음 중 둘 이상 충족):
  1. 글로벌 단일 키워드 검색량 월 100 K 이상
  2. AdSense CPM 이 높은 시장 (US, DE, JP, AU 등) 의 핵심 글
  3. 시리즈 전체가 글로벌 화제 (예: SpaceX IPO, GPT-5 Launch)
- 승격 시 작업량: 12개 디렉토리 + 12 posts.js entry + 12 sitemap 블록. 한 글당 ~1~2일 작업. 신중히.

---

## 8. 자동 발행 (증시 4편) 과의 차이

자동 발행 글은 `scripts/auto-daily-post.py` + GitHub Actions cron 으로 작동. 본 문서는 **수동 작성 글**에 적용. 두 흐름의 차이:

| | 자동 발행 (증시 6편) | 수동 작성 |
|---|---|---|
| 트리거 | GitHub Actions cron | Claude Code 세션 또는 사용자 직접 |
| 시장 | us, kr, **cn** (3개 시장 × 개장/마감 2 슬롯 = 6 슬롯) | — |
| 언어 | ko + en + ja + zh (4종, **영어 원천 → 3언어 번역**) | ko + en + ja + zh (4종, **한국어 원천 → 3언어 번역**) |
| 카테고리 | `industry` 고정 | 6종 중 선택 |
| 데이터 | yfinance 하드 페치 → 프롬프트 주입 | 수동 리서치 |
| 길이 | 600~900 단어 narrative | 자유 (보통 6~20분 읽기) |
| 톤 | 분석 보고서 | 스토리텔링·에세이 |
| 검증 | Iron Rule (≥2 소스 cross-verify) | 본 문서 §4.3 (footnotes + 면책) |
| 출력 | 매일 24개 글 (6 슬롯 × 4 언어) | 글당 4개 (1 글 × 4 언어) |

자동 발행 시스템 상세는 [scripts/prompts/README.md](../scripts/prompts/README.md) 참조.

---

## 9. 발행 후 점검 (Cloudflare Pages 배포 후 ~1~2분)

1. 한국어판 직접 열어 보기: `https://luckyplz.com/blog/<slug>/`
2. 영어판 동일하게.
3. 일본어판 동일하게.
4. **중국어판 동일하게**: `https://luckyplz.com/blog/<slug>-zh/`
5. 블로그 메인 (`/blog/`) 에서 카테고리 필터로 새 글 보이는지.
6. 메인 페이지 (`/`) 의 최근 글 카드에 보이는지 (자동 갱신).
7. 카카오톡·트위터·페이스북·웨이보 링크 미리보기 (OG 이미지·CJK 폰트 깨짐 없는지).
8. 모바일 (실기기 또는 Chrome devtools 모바일 모드) 에서 가로 480px 캡 잘 걸리는지.
9. 데스크탑 (>768px) 에서 column 760~820px 로 넓혀지는지.

---

## 부록 A — 빠른 참조 표

| 작업 | 명령 / 위치 |
|---|---|
| 새 글 비계 | `python scripts/new-blog-post.py --slug … --category … --title-ko … --title-en … --title-ja … --title-zh …` |
| 시리즈 글 비계 | 위 + `--series anthropic-story` |
| 발행 후 cache bump | `bash scripts/bump-cache.sh` |
| desktop CSS 주입 | `python scripts/inject-blog-desktop-css.py` |
| 로컬 미리보기 | `python server.py` → `http://localhost:8080/blog/<slug>/` |
| posts.js | [public/blog/posts.js](../public/blog/posts.js) |
| sitemap | [public/sitemap.xml](../public/sitemap.xml) |
| 자동 발행 프롬프트 | [scripts/prompts/](../scripts/prompts/) |
| 자동 발행 README | [scripts/prompts/README.md](../scripts/prompts/README.md) |

---

마지막 업데이트: 2026-05-25 — 다국어 운영 기준을 **ko + en + ja + zh 4종** 으로 확장. 자동발행 증시는 영어 원천 → 3 언어 번역, 일반 블로그는 한국어 원천 → 3 언어 번역. 자동발행 시장도 us + kr + **cn** 3개로 확장 (별도 작업, Task #25).
