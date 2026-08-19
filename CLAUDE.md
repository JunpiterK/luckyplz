# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Site Identity & Mission (READ FIRST)

> **luckyplz.com 은 랜덤 뽑기·내기 게임 전용 사이트다.**
> 2026-08-18 자로 블로그·도구·AI Labs 를 **별도 저장소 `C:\code\python\luckyplz_blog` 로 완전히 분리**했다.
> 이 저장소에는 **게임과 게임을 굴리는 인프라만** 남는다.

### 왜 이렇게 좁혔나

운영자 판단: *"랜덤게임을 주력으로 하는 사이트로 오랫동안 인식시키는 게 조금이라도 수익을 낼 수 있는 유일한 방법"*.

근거는 2026-08-18 수익화 감사([docs/MONETIZATION_AUDIT_2026-08.md](docs/MONETIZATION_AUDIT_2026-08.md)):
- 구글 2026 심사·랭킹 기준은 **주제 깊이(topical authority)** 이고, 분산된 사이트는 감점된다
- 게임 사이트에 증시·AI·우주 글이 섞여 있으면 도메인 주제가 무엇인지 신호가 흐려진다
- AdSense "low value content" 3회 이상 거절 이력이 있어, 주제 일관성 회복이 승인 확률의 핵심 레버

### 하지 말 것 (되돌리기 금지)

- **홈·푸터·게임 페이지에 블로그/도구/랩 링크를 다시 추가하지 말 것.** 의도적으로 전부 제거했다.
- `/blog/`·`/tools/`·`/labs/`·`/all/` 경로를 되살리지 말 것. `public/_redirects` 에서 **410 Gone** 으로 색인 제거 중이다.
- 콘텐츠가 필요하면 **게임에 대한 콘텐츠**를 만든다. 게임과 무관한 주제는 `luckyplz_blog` 쪽 일이다.

### 사이트 구조 (2026-08-19 확정 — 되돌리기 금지)

```
/                     메인 = 랜덤 뽑기 6종 + RETRO 스트립 1개.  영어 canonical
/es/ /pt/ /ja/ /ko/   같은 홈의 실제 번역 페이지 (scripts/gen-lang-home.py)
/arcade/              레거시 아케이드 11종 허브. 홈과 같은 타일 규칙, 본문은 접기
/games/               전체 17종 목록 (한국어)
/games/<id>/          게임 본체 17종. 한국어 본문 500~650단어 보유
```

**언어 클러스터 — 한 도구 = 5개 언어 페이지 한 세트 (총 30 페이지).**

| 도구 | en | es | pt | ja | ko(게임 본체) |
|---|---|---|---|---|---|
| 룰렛 | `/wheel-spinner/` | `/es/ruleta/` | `/pt/roleta/` | `/ja/roulette/` | `/games/roulette/` |
| 팀 | `/team-generator/` | `/es/sorteo-equipos/` | `/pt/sorteio-times/` | `/ja/team-generator/` | `/games/team/` |
| 주사위 | `/dice-roller/` | `/es/tirar-dados/` | `/pt/rolar-dados/` | `/ja/saikoro/` | `/games/dice/` |
| 빙고 | `/bingo-caller/` | `/es/bingo/` | `/pt/bingo/` | `/ja/bingo/` | `/games/bingo/` |
| 레이스 | `/race-picker/` | `/es/carrera-aleatoria/` | `/pt/corrida-aleatoria/` | `/ja/random-race/` | `/games/car-racing/` |
| 사다리 | `/ladder-draw/` | `/es/escalera/` | `/pt/escada/` | `/ja/amidakuji/` | `/games/ladder/` |

- **정의는 [scripts/lp_clusters.py](scripts/lp_clusters.py) 한 곳에만 둔다.** 다른 파일에서 재정의하면 두 곳이 어긋나고, hreflang 은 **한 변만 깨져도 클러스터 전체가 무시**되므로 반쪽 클러스터는 없는 것과 같다
- ko 멤버는 별도 랜딩이 아니라 **게임 본체**다. 이미 한국어 본문이 있어 새로 만들 이유가 없다
- 슬러그는 그 언어의 실제 검색어를 담는다 — `/ja/amidakuji/` 처럼 현지 표기가 곧 검색어인 경우가 가장 강하다
- **변경 후에는 반드시 `python scripts/verify-clusters.py`** — canonical 자기참조 · hreflang 상호성 · `<html lang>` · FAQ 1:1 · JSON-LD 를 30 페이지 전수 검사한다

**메인 = 3×3 그리드에 7종 노출 (2026-08-20).** 룰렛 · 팀 나누기 · 주사위 · 빙고 · 카레이싱 · 사다리 + **브롤런**. 남는 2칸은 향후 여유이며 **채우기 위해 채우지 말 것**.
- 브롤런 승격 근거: 운영자 감 — 재미 면에서 카레이싱보다 끌린다. 검색 유입은 랜딩 클러스터(race-picker 등)가 홈 노출과 무관하게 담당하므로 카레이싱도 홈에 남는다. **홈 타일과 SEO 클러스터는 독립**이다
- 브롤런 타일에는 `isAdv` → ⚠️ 미니 배지 (교실·가족 사용자 대상 정직한 고지)
근거: 경쟁 사이트 9종(wheelofnames·pickerwheel·pickerspin 외) **전원이 휠+팀+주사위+빙고
스위트를 이미 갖고 있다**. 즉 스위트는 차별점이 아니라 진입 요건이다. 차별점은
**카레이싱(순위를 레이스로 보여주는 도구 — 경쟁사 전무)** 과 사다리(한·일 고유 수요)이고,
그 둘을 6칸에 넣기 위해 로또·Brawl Run 을 `/arcade/` 로 내렸다. 6칸을 늘리면
주제 집중이 흐려지고 이 사이트의 유일한 SEO 레버가 사라진다.

**타일 규칙 (2026-08-19 2차 개편 — 되돌리기 금지).**
- **전 화면 3열 고정 (2026-08-20).** 세로 폰도 3열 — 운영자 결정. 타일이 108px 로 작아지는 대신 clamp 최소값을 낮춰 비율 유지. 폴더블 접힘(≤339px)에서는 설명 줄을 숨긴다(두 줄이 물리적으로 안 들어감)
- **정사각 타일 하나로 통일.** 화면폭별 비율 분기를 두지 않는다. 320px(146px 카드)부터 4K(408px)까지 아이콘·이름·설명이 다 들어가는 것을 실측 확인했다
- **크기는 카드 폭 기준(`cqw`)** — 아이콘 36cqw, 이름 13cqw, 설명 8.5cqw. 화면폭(`vw`)으로 잡으면 열 수가 바뀌는 지점에서 비율이 깨진다(768px 3열에서 아이콘이 카드의 43%를 먹던 문제). `@supports` 로 감싸고 vw 폴백을 앞에 둔다
- **세로가 짧으면 카드를 눌러 찌그러뜨리지 말고 그리드 폭을 줄인다.** 정사각 비율이 유지된 채 한 화면에 들어온다. 940/800/700/640px 4단계
- 카드 내용은 **아이콘 + 이름 + "언제 쓰는가" 한 줄**뿐이다. PLAY 배지는 카드 전체가 버튼이라 중복이고 글자만 늘린다
- **비율은 아이콘 33% : 이름 10.5cqw : 설명 7cqw.** 이름을 13cqw 로 뒀더니 271px 카드에서 27px 가 되어 아이콘 대비 과했다
- **게임마다 고유 색**(`GAME_TINT` → 인라인 `--tile-rgb`). 카드 상단 광량·아이콘 글로우·액센트 라인·호버 테두리가 전부 이 값을 쓴다. 회색 타일 6개가 나란한 것보다 살아 보이고, 색 자체가 게임의 표시가 되어 재방문 시 글자를 안 읽고 찾는다. `color-mix` 대신 RGB 3값 + `rgba()` 를 쓰는 이유는 구형 웹뷰 호환
- **`.header` 에 `width:100%` 를 빼지 말 것.** flex 아이템이라 콘텐츠 폭으로 줄어들고, 그러면 도움말 `?` 버튼의 `right:0` 이 화면이 아니라 **로고 글자 끝** 기준이 되어 글자 위에 겹친다(2026-08-19 실제 버그)

**홈 본문은 접는다 (사용자 원칙).** 운영자가 반복해서 밝힌 선호: *"글자가 과도하게 많은 걸 안 좋아해. 너무 장황한 건 사람들이 절대 안 좋아한다."* 2026-08-19 1차 개편에서 넣은 영어 850단어가 정확히 그 문제였다. 지금은:
- 펼쳐진 글 = 리드 한 문장뿐. 나머지는 `<details class="lp-fold">` 3개와 접히는 FAQ 6개
- 닫힌 상태에서 화면에 보이는 글자 ≈ 190자
- 상세는 헤더의 `?` 버튼 → 도움말 시트. **문장이 아니라 키워드 3개**로 적는다 (`HELP_TAGS`)
- 구글은 아코디언 안 콘텐츠를 정상 색인하므로 FAQPage 1:1 대응은 유지된다

### 언어 정책 (2026-08-19)

| 등급 | 언어 | 실체 |
|---|---|---|
| **SEO 투자** | en(기본) · es · pt · ja · ko | 실제 경로 페이지 + 상호 hreflang + 번역 본문 |
| UI 만 | zh de fr ru ar hi th id vi tr gb | I18N 번역은 유지, hreflang·색인 대상 아님 |

- **영어가 canonical.** 홈의 가시 본문·FAQ 는 영어 고정이며 UI 언어 전환에 따라 바뀌지 않는다 — FAQPage 스키마와 1:1 대응이 깨지면 안 되기 때문
- **중국어·힌디어를 뺀 이유**: 사용자 수는 크지만(8.9억/1.9억) 중국 본토는 구글이 차단돼 구글 SEO 로 도달 불가, 인도권은 유틸리티 도구를 영어로 검색한다. 국가별 AdSense RPM 격차가 10배 이상이라 도달 가능성 × RPM 으로 우선순위를 잡았다
- **`?lang=` hreflang 을 다시 만들지 말 것.** 2026-08-19 에 108개를 제거했다. canonical 이 쿼리 없는 URL 을 가리키는 상태에서 `?lang=xx` 를 alternate 로 선언하면 구글이 전부 버린다 — 16개 언어 전부 SEO 가치 0 이었다. 언어 페이지가 필요하면 **실제 경로**를 만든다
- 홈을 고치면 `python scripts/gen-lang-home.py` 를 다시 돌려야 언어판이 따라온다

### 게임 — 친구들과 함께 쓰는 작은 도구

- **목적**: 친구·동료와 내기·벌칙·역할 정하기, 또는 잠깐의 시간 떼우기
- **두 카테고리**
  - **행운/뽑기 (핵심 정체성)** — 룰렛, 팀뽑기, 주사위, 빙고, 카레이싱, 사다리. 결정·내기·벌칙 도구
  - **레트로 액션 (부가)** — `/arcade/` 뒤. 스네이크, 닷 러너, 블록 스택 등. 기록 갱신·심심풀이
- **원칙**
  - 모든 게임은 **로그인 없이 즉시 플레이 가능**해야 한다. 로그인은 소셜/멀티플레이 기능에만
  - 모바일 우선(세로 폰), 데스크탑·태블릿은 확장
  - 한 게임 = 한 HTML 파일 (inline CSS/JS, 자가완결). 게임 간 의존성 만들지 말 것

### 상표 주의 (2026-08-18 중립화 완료)

레트로 아케이드 2종은 상표를 피해 중립 명칭을 쓴다. **되돌리지 말 것.**

| 디렉토리(식별자) | 표시명 |
|---|---|
| `games/pacman/` | 닷 러너 / Dot Runner |
| `games/tetris/` | 블록 스택 / Block Stack |
| `games/glory-racing/` | Brawl Run / 브롤 런 |

**`UFC RUN` 은 절대 쓰지 말 것** (2026-08-19 검토). Zuffa(UFC)는 유비소프트를 상대로
게임 이름도 아닌 **패키지 뒷면의 "Ultimate Fighting" 문구 한 줄**을 두고 소송했고
유비소프트가 합의·패키지 변경했다. 세 글자를 게임명에 직접 쓰는 건 그보다 명백하다.
반면 **폭력성 표기 자체는 문제없다** — AdSense 는 2023-08 정책 개정으로 게임플레이
영상에 폭력성 예외를 뒀고, 현재 제한 대상은 고문·성폭력·미성년자/실존인물 대상·차별
기반 폭력뿐이다. 그래서 Brawl Run 은 이름만 중립화하고 `⚠️ 만화적 몸싸움 연출 포함`
고지를 title 아래(`.lp-advisory`)와 meta description 에 남겼다 — 호기심 유발 + 정직한 고지.

- 표시명(title·og·h1·i18n `gameTitle`/`subtitle`·설명문)은 16개 언어 전부 중립화됨 — `scripts/neutralize-trademarks.py` (멱등)
- **내부 식별자는 절대 바꾸지 말 것**: `gameKey:'tetris'`, `tetris_leaderboard` RPC, CSS 클래스, URL 슬러그 → 바꾸면 Supabase 리더보드와 기존 공유 링크가 깨진다

---

## Commands

- 로컬 개발 서버: `python server.py` (또는 `start.bat`). `public/` 을 `http://localhost:8080` 에 서빙. `HOST`/`PORT` 환경변수 override
- 의존성: `pip install -r requirements.txt` (Flask만)
- **HTML 또는 공용 JS/CSS 를 건드린 커밋 전 반드시**: `bash scripts/bump-cache.sh` (아래 Cache policy 참조)
- 빌드·번들러·린트·테스트 없음. 프로덕션은 Cloudflare Pages 가 정적 파일로 서빙하고, `server.py` 는 로컬 미리보기 전용이며 Pages 라우팅(디렉토리 → `index.html`)을 그대로 흉내 내야 한다

### SEO·다국어 도구

- `python scripts/verify-clusters.py` — **변경 후 필수 게이트.** 30 페이지 전수 검사
- `python scripts/gen-lang-home.py` — 언어 홈 4종 생성 (홈을 고치면 반드시 다시 돌릴 것)
- `python scripts/gen-landing.py` / `gen-landing-i18n.py` — 도구 랜딩 en / es·pt·ja
- `python scripts/fix-page-lang.py` — 게임 본체의 `<html lang>`·`og:locale`·hreflang 정합화 (멱등)
- `python scripts/sync-faq-schema.py` — FAQPage 스키마를 화면에서 재생성 (멱등)
- `python scripts/gen-sitemap.py` — sitemap 생성 + 등록 URL 파일 존재 검증

### 게임 콘텐츠 도구

- `python scripts/inject-game-about.py` — 게임 하단 가시 SEO 콘텐츠(`lp-game-about` 섹션) + FAQPage 스키마 주입 (멱등, 펜스 `<!--lp-game-about:start/end-->`). 새 게임에 콘텐츠를 붙일 때 `CONTENT` 딕셔너리에 항목 추가
- `python scripts/neutralize-trademarks.py [--dry-run]` — 상표성 표시명 중립화 (멱등)
- `python scripts/gen-og-games.py` / `gen-og-main.py` — 게임별·사이트 대표 OG 이미지 생성

---

## Architecture

**Static multi-page site, no framework.** 모든 게임은 `public/games/<name>/index.html` 에 자가완결 HTML(inline CSS+JS, 자체 `<head>` SEO 블록)로 존재한다. 게임끼리 독립을 유지할 것 — 공용 번들러나 게임 간 import 를 도입하지 말고, 복붙이 의도된 패턴이다(한 게임을 고쳐도 다른 게임이 깨지지 않게).

현재 게임 17종: `bingo` `brick` `burger` `car-racing` `dice` `dodge` `glory-racing`(Brawl Run) `ladder` `lotto` `lucky-merge` `pacman`(닷 러너) `quiz` `roulette` `snake` `starship-lander` `team` `tetris`(블록 스택). 이 중 **메인 6종**(roulette·team·dice·bingo·car-racing·ladder)만 홈에 노출되고 나머지 11종은 `/arcade/` 뒤에 있다.

**도구 랜딩.** 게임 본체(`/games/<id>/`)의 가시 콘텐츠는 한국어라 영어·스페인어·포르투갈어·일본어 검색에는 잡히지 않는다. 랜딩은 게임을 iframe 으로 임베드하고 그 언어의 콘텐츠 + FAQ 스키마를 얹는다. **게임 본체는 수정하지 않는다.**
- 영어 6종 — `scripts/gen-landing.py`. 기존 3종(wheel-spinner·team-generator·dice-roller)은 손으로 쓴 콘텐츠라 재생성하지 않으며, 스크립트의 `ALL` 목록만 상호 링크에 쓰인다
- es·pt·ja 18종 — `scripts/gen-landing-i18n.py` + 언어별 콘텐츠 모듈 `landing_content_{es,pt,ja}.py`
- 분량: en 848~942단어 / es 575~732단어 / pt 542~716단어 / ja 1,229~1,765자
- **집필 원칙은 게임 콘텐츠와 동일 — 정보 이득.** 조작 설명("이름 넣고 버튼 누르기")은 경쟁 사이트에 전부 있다. 빙고 75볼/90볼 밴딩 차이와 콜 수 분포, 레이스의 n! 순열, 사다리의 전단사(bijection) 성질처럼 **이 페이지에서만 얻는 내용**을 넣는다
- **기계 번역이 아니다.** 각 언어권에서만 의미 있는 맥락을 넣는다 — 일본어판 사다리의 아미다(阿弥陀) 유래와 忘年会 빙고, 포르투갈어판의 festa junina, 스페인어판의 90볼 관행

**내부 링크.** 랜딩끼리만 링크하면 홈에서 들어가는 경로가 0이 되어 사실상 고아 페이지가 된다(2026-08-19에 실제로 그 상태였다). 각 언어 홈 본문에 `ul.lp-seo-links` 로 그 언어의 도구 6개를 텍스트 링크한다. **게임 카드는 게임 본체를 그대로 가리킨다** — 도구 사이트에서 플레이까지 클릭을 늘리면 안 된다.

**홈 가시 콘텐츠 (`lp-home-seo`).** 2026-08-19 이전 홈은 본문 텍스트가 사실상 0 인데 **FAQPage 스키마만 달려 있었다** — 화면에 없는 Q&A 를 스키마에 넣는 건 구글 구조화데이터 정책 위반이다. 지금은 스키마와 1:1 대응하는 `<dl class="lp-seo-faq">` 를 실제로 렌더하고, 영어 850단어 본문(도구별 용도·왜 보이는 추첨이어야 하는가·공정성 수학·사용 상황)이 붙어 있다. **스키마만 늘리고 화면을 안 늘리는 변경을 하지 말 것.**

**`lp-game-about` 는 반드시 한 화면 아래에서 시작해야 한다 (2026-08-19 사고).** 게임 UI 가 거의 전부 `position:fixed/absolute` 라 **문서 흐름 높이가 0** 인 페이지가 많다. 그대로 두면 이 섹션이 `top:0` 에서 시작해 **게임 화면 위에 겹쳐** 보인다 — 17종 전부 그 상태였다(실측 aboutTop 0~734px). 조치 3종을 함께 유지할 것:
- 인라인 스크립트가 `margin-top` 을 런타임에 계산한다. CSS 의 `100dvh` 는 폴백이며, 게임이 이미 흐름 높이를 가지면 0 이 되어 빈 화면이 생기지 않는다
- **마진 상쇄 2패스 보정 필수.** 인접 형제와 margin 이 상쇄되면 계산한 만큼 안 내려간다(car-racing 에서 8px 모자랐다). 위치를 다시 재서 모자란 만큼 더한다
- `z-index:9100` + 불투명 배경 + 전체 폭. 게임 고정 UI 최대치가 9040(전체화면 버튼)이라 그 위여야 스크롤해서 읽을 때 글자 위에 UI 가 안 뜬다. 폭 제한은 `.lp-about-inner` 로 옮겼다 — 배경이 가운데만 덮으면 좌우로 게임이 비친다

**`/arcade/` 도 `luckyplz_lang` 을 따른다.** 영어 고정이라 메인에서 고른 언어가 여기서 끊겼다(2026-08-19). 지금은 `data-i18n` / `data-i18n-html` 마커 + 인라인 번역표(5개 언어)로 전환한다.
- **HTML 원문은 영어로 둔다.** canonical 이 영어 한 장뿐이라 크롤러가 보는 것은 영어여야 한다. 전환은 사용자 화면에서만 일어난다
- `/games/`(한국어 전용 목록)로 가는 nav 링크는 **한국어일 때만** 유지하고 나머지 언어는 홈으로 보낸다 — 영어 사용자가 눌러서 한국어 페이지에 떨어지면 안 된다
- 게임 본체의 `<html lang>` 은 UI 언어를 따라가지 **않는다**. 색인되는 본문(`lp-game-about`)이 한국어이고 클러스터의 ko 멤버로 선언돼 있어, UI 선호로 바꾸면 hreflang 과 신호가 충돌한다

**게임 UI 언어는 `luckyplz_lang` 을 따른다.** 메인에서 고른 언어가 게임에서 깨지면 안 된다. 2026-08-19 전수 검사에서 17종 전부 어딘가 한국어가 남아 있었다.
- 공통 `← 홈` 은 17개 파일에 각각 하드코딩돼 있었다 → `siteFooter.js` 의 `lpLocalizeHome()` 이 일괄 처리한다. **게임 파일마다 고치지 말 것** — 새 게임에서 또 빠진다
- 게임별 i18n 테이블에 키가 없거나 함수 안에 한국어가 박힌 자리는 `public/js/lpGameText.js` 가 표시 문자열만 바꾼다(게임 페이지에서만 로드). 텍스트 노드 맵 + HTML 블록 맵 2종이며, **HTML 맵이 먼저** 돌아야 한다(텍스트 맵이 먼저 돌면 키의 낱말이 이미 번역돼 매칭이 깨진다)
- **게임 HTML 을 직접 고칠 때는 반드시 대상 테이블 구간을 좁혀라.** car-racing 에는 `I18N` 과 `SHARE_I18N` 이 같은 모양으로 있어, 문서 전체를 대상으로 치환했다가 공유 다이얼로그 제목을 덮어썼다
- 검사 방법: 각 언어로 게임을 열어 `.lp-game-about` 밖의 **보이는** 텍스트 노드에 한글이 있는지 본다. 한국어일 때는 원문이 남아 있어야 정상이다

**게임 페이지 가시 콘텐츠 (`lp-game-about`).** 게임 페이지는 풀스크린 캔버스라 텍스트가 거의 없었고(61~115단어), 이는 검색 랭킹·AdSense 심사 양쪽에서 치명적이었다. 그래서 게임 하단에 사용법·원리·팁·활용사례·FAQ 를 담은 섹션을 붙인다.
- **숨김 텍스트가 아니다**: `html,body{overflow:hidden}` 은 `@media(min-width:900px)` 안에만 있어, 모바일에서는 정상 스크롤로 도달한다. 구글은 모바일 우선 색인이므로 이 콘텐츠를 정상적으로 읽는다. 과거의 `left:-9999px` 방식(가이드라인 위반)은 이미 제거됐고 되살리면 안 된다
- **17종 전부 적용 완료 (2026-08-18)**. 실측 가시 텍스트 610~773단어로 2026 thin 기준(600)을 전 게임이 통과
- 콘텐츠는 파일 비대화를 막으려 분리 보관: 1차 4종은 `inject-game-about.py` 내부, 아케이드 6종은 `game_about_content_2.py`, 레이싱·우주·퀴즈·주사위 6종은 `_3.py`, 600단어 보강 블록은 `_4.py`(`EXTRA_BLOCKS`). 메인 스크립트가 전부 병합
- **집필 원칙 — 정보 이득(Information Gain)**: 조작법 나열은 다른 사이트에도 다 있어 2026 기준으로는 저품질 판정을 받는다. 각 게임의 역사·수학·전략 원리처럼 **이 페이지에서만 얻는 내용**을 반드시 넣는다 (예: 스네이크의 해밀턴 순환, 블록 스택의 7-백 시스템, 주사위 두 개의 합 분포, 착륙의 수어사이드 번)
- 새 게임 추가 시: `game_about_content_4.py` 뒤에 이어 붙이거나 `_5.py` 를 만들어 같은 방식으로 등록

**Hosting & deploy.** 저장소 `JunpiterK/luckyplz`, Cloudflare Pages 프로젝트 `luckyplz` 가 `main` 을 자동 배포(빌드 출력 디렉토리 `public`). `public/_headers` 가 캐시 규칙을 통제 — HTML·`/games/*`·`/js/*` 는 `no-cache` 로 즉시 반영, `/assets/*` 와 `*.mp3` 는 1주 캐시.

**Cache policy — 3중 에어백 (커밋 전 필독).** 모바일 브라우저(Chrome Android, 삼성인터넷, 구형 iOS Safari)는 HTML 과 동적 주입 `<script>` 에 대해 `no-cache` 헤더를 반복적으로 무시한다. **HTML 또는 `public/js/` 하위를 건드린 커밋 전에는 반드시 `bash scripts/bump-cache.sh`** 를 돌린다. 세 층이 한꺼번에 갱신된다:

1. **`?v=<stamp>` 쿼리 재작성** — 모든 공용 JS 참조(`/js/*.js`)와 `siteFooter.js` 내부의 동적 주입까지. URL 자체를 바꿔 헤더를 무시하는 캐시 층도 새 리소스로 인식하게 한다
2. **`/build.json` 등대** — `{"v":"<stamp>"}` 한 줄. `Cache-Control: no-store` 로 서빙되며 모든 페이지로드가 fetch 한다. "지금 라이브 빌드가 뭔지"의 단일 진실원천
3. **인라인 build-check `<script>`** — 모든 HTML `<head>` 에 `<!--lp-build-check:start/end-->` 펜스로 박힌다. HTML 에 baked 된 버전과 `/build.json` 을 비교해 불일치면 `_b=<live>` 쿼리를 붙여 하드 리로드. `sessionStorage` 로 stale 버전당 1회만 리로드하므로 루프가 없다

`public/_headers` 는 별도로 `/*.html`·`/`·`/games/*`·`/js/*`·`/build.json` 을 `no-store, no-cache, must-revalidate, max-age=0` 으로 서빙한다. 방문자 간 유지돼야 하는 유일한 상태는 localStorage(저장 그룹·프리셋·닉네임·게임 기록)뿐이다.

**Cache policy — 운영 규칙 (대규모 작업 시 필독).** 위 3중 장치는 단순화 금지. 2026-05-26 사고 이후 바뀐 것은 **실행 빈도**다. 스크립트는 매 호출마다 2,000개 이상 HTML 의 빌드 스탬프를 재작성하므로, 하루에 4번 돌렸다가 ~225개 파일 수정 커밋이 연속 4개 생기며 GitHub 자동 어뷰징 탐지에 계정이 일시 정지됐다.

1. **커밋당이 아니라 세션당 1회.** 여러 파일을 고칠 때는 전부 쓴 뒤 마지막에 한 번만 돌리고 한 번만 커밋한다
2. **대규모 작업은 1~2 커밋으로.** 잘게 쪼개 여러 번 푸시하지 말 것
3. **불가피하게 여러 대형 커밋이 필요하면 푸시 사이에 30분 이상** 둔다
4. `remote: Your account is suspended` 가 보이면 루프 재시도 금지. ~30분 대기 후 작은 fetch 로 확인

**Removed URLs (410 Gone).** 2026-08-18 분리로 사라진 `/blog/*`·`/tools/*`·`/labs/*`·`/all*`·`/unsubscribe/*` 는 `public/_redirects` 에서 **410 Gone** 을 반환한다. 404 로 오래 방치하면 크롤 예산과 품질 평가에 불리하므로, 의도적 제거임을 알려 색인에서 빠르게 내리기 위함이다. 콘텐츠가 다른 도메인에 다시 올라가면 그때 301 로 교체한다. 410 은 `public/404.html` 을 본문으로 쓴다.

**No service worker.** `public/sw.js` 는 레거시 설치본을 자폭시키는 루틴(캐시 전부 삭제 + 자기 등록해제)일 뿐이다. 모든 HTML 은 `siteFooter.js` 직전에 `navigator.serviceWorker.getRegistrations().forEach(unregister)` 인라인도 함께 넣는다. **캐싱 서비스워커를 다시 도입하지 말 것.** 2026년 4월 로또 재디자인 때 stale-SW 디버깅으로 몇 시간을 날렸다.

**Auth / backend.** Supabase 가 유일한 백엔드. 공용 클라이언트는 [public/js/supabase-config.js](public/js/supabase-config.js) 에 있고 `getSupabase()`, `signUp/signIn/signOut`, `getUser`, `onAuthChange`, `getDisplayName` 를 노출한다. anon/publishable 키는 공개 설계라 의도적으로 커밋돼 있다. **핵심 게임은 로그인 없이 플레이 가능해야 한다** — 인증은 소셜/멀티플레이 전용(`public/auth/`). 기존 게임에 로그인 게이트를 추가하지 말 것.

**모바일 WebView 주의.** RLS 로 보호된 테이블을 카카오톡 인앱 브라우저에서 직접 SELECT 하면 **무음 실패**한다. 채팅·소셜 읽기는 반드시 SECURITY DEFINER RPC 로만 할 것.

**canvas 모달 클릭 함정.** 부모의 `touchstart preventDefault` 가 click 합성을 취소해서, 새 모달 클래스를 `closest('.overlay')` 목록에 추가하지 않으면 **모바일에서만** 버튼이 무반응이 된다. 진단이 매우 어려우니 새 모달 추가 시 반드시 확인.

**Bot protection (Cloudflare Turnstile).** `supabase-config.js` 에 `TURNSTILE_SITE_KEY` 상수가 있다(기본 빈 값 = 비활성). 값을 넣으면 인증 폼이 Turnstile 위젯을 렌더하고 토큰을 Supabase 로 넘긴다. 활성화하려면 (1) Cloudflare → Turnstile → 사이트 추가(`luckyplz.com`, Managed), (2) SITE KEY 를 상수에, (3) SECRET KEY 를 Supabase → Authentication → Captcha protection 에 넣는다. 둘이 맞아야 하며, 클라이언트 키만 배포하면 Supabase 가 모든 인증을 거부한다.

**i18n & SEO.** 게임은 `?lang=` 쿼리로 16개 언어를 지원하며 `hreflang` alternate 와 JSON-LD `ItemList` 가 [public/index.html](public/index.html) 에 있다. 정규 도메인은 `https://luckyplz.com/`. 페이지를 추가하면 canonical/OG 블록을 복제하고 **`python scripts/gen-sitemap.py` 의 목록에 추가한 뒤 다시 돌린다**. sitemap 은 더 이상 손으로 관리하지 않는다 — 손 관리 시절 메인 6종 중 `/games/dice/` 가 통째로 누락돼 있었다. 생성기는 등록한 URL 이 실제 파일로 존재하는지도 검증한다. `.lang-bar` 는 `public/js/langBar.js` 가 주요 5개(en/ko/ja/zh/es) + "🌐 More" 드롭다운으로 정리한다.

**구조화 데이터.** 전 게임이 JSON-LD 를 갖는다(BreadcrumbList). 콘텐츠가 붙은 페이지는 FAQPage 도 함께.

**FAQPage 는 화면이 진실원천이다.** 스키마를 손으로 쓰지 말고 `python scripts/sync-faq-schema.py` 로 화면 Q&A 에서 생성한다. 손으로 관리하던 시절 영어 랜딩 3종은 스키마와 화면 문구가 같은 뜻의 다른 문장으로 갈라져 있었고(= 화면에 없는 Q&A 를 선언한 상태), `/games/ladder/` 는 화면에 Q&A 6개가 있는데 스키마가 없어 17종 중 유일하게 리치결과 자격이 없었다. 스크립트는 `<details>`(랜딩)·`<dl class="lp-faq">`(게임)·`<dl class="lp-seo-faq">`(홈) 세 마크업을 모두 읽고 `Q. ` 접두어를 뗀다.

**OG 이미지.** 링크로 공유되는 모든 페이지는 내용에 맞는 OG 이미지를 갖춰야 한다. 생성기는 `scripts/gen-og-games.py`(게임별), `scripts/gen-og-main.py`(사이트 대표). 폰트는 `scripts/og-fonts/`.

**Analytics.** GA4 measurement ID 는 `G-NZDPE3H3DQ` (property: LuckyPlz). 이전 `notmeplz.com` ID `G-W91WWVNLD6` 는 어디에도 남아 있으면 안 된다 — 커밋 전 grep 할 것.

**Monetization.** AdSense Publisher ID `ca-pub-5370817769801923`. **현재 미승인**("low value content" 3회+ 거절). 광고 슬롯 ID 3개는 `public/js/adSlots.js` 에 실값으로 있으나, 게임 17종 전부 `<meta name="lp-ad-policy" content="off">` 라서 `adSlots.js` 가 로드조차 되지 않는다 — 즉 **광고 배선 준비도는 0%** 이며 승인이 나도 2~3주 배선 작업이 남는다. 상세는 [docs/MONETIZATION_AUDIT_2026-08.md](docs/MONETIZATION_AUDIT_2026-08.md).

광고 배치 원칙(유지): 게임 플레이 중·설정 화면·홈 상단 **금지**. 결과 화면·홈 하단만 허용. Auto Ads 금지.

**Migration context.** 이 저장소는 2026-04-17 에 브랜딩 이유로 `notmeplz.com` 에서 분리됐다. 브랜드 텍스트는 "Lucky Please" 로 통일됐으니 `notmeplz`/`NotMePlz`/"Not Me Please" 문자열이 보이면 버그다.

**Content split (2026-08-18).** 블로그(2,015 디렉토리)·도구(27)·AI Labs(8)와 관련 스크립트·워크플로·문서는 `C:\code\python\luckyplz_blog` 로 이동했다. 그쪽 콘텐츠가 필요하면 그 저장소에서 작업하고, 이 저장소로 되가져오지 말 것.
