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

### 게임 — 친구들과 함께 쓰는 작은 도구

- **목적**: 친구·동료와 내기·벌칙·역할 정하기, 또는 잠깐의 시간 떼우기
- **두 카테고리**
  - **행운/뽑기 (핵심 정체성)** — 룰렛, 사다리, 로또, 팀뽑기, 주사위, 빙고. 결정·내기·벌칙 도구
  - **레트로 액션 (부가)** — 스네이크, 닷 러너, 블록 스택, 카레이싱 등 기록 갱신·심심풀이
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

- 표시명(title·og·h1·i18n `gameTitle`/`subtitle`·설명문)은 16개 언어 전부 중립화됨 — `scripts/neutralize-trademarks.py` (멱등)
- **내부 식별자는 절대 바꾸지 말 것**: `gameKey:'tetris'`, `tetris_leaderboard` RPC, CSS 클래스, URL 슬러그 → 바꾸면 Supabase 리더보드와 기존 공유 링크가 깨진다

---

## Commands

- 로컬 개발 서버: `python server.py` (또는 `start.bat`). `public/` 을 `http://localhost:8080` 에 서빙. `HOST`/`PORT` 환경변수 override
- 의존성: `pip install -r requirements.txt` (Flask만)
- **HTML 또는 공용 JS/CSS 를 건드린 커밋 전 반드시**: `bash scripts/bump-cache.sh` (아래 Cache policy 참조)
- 빌드·번들러·린트·테스트 없음. 프로덕션은 Cloudflare Pages 가 정적 파일로 서빙하고, `server.py` 는 로컬 미리보기 전용이며 Pages 라우팅(디렉토리 → `index.html`)을 그대로 흉내 내야 한다

### 게임 콘텐츠 도구

- `python scripts/inject-game-about.py` — 게임 하단 가시 SEO 콘텐츠(`lp-game-about` 섹션) + FAQPage 스키마 주입 (멱등, 펜스 `<!--lp-game-about:start/end-->`). 새 게임에 콘텐츠를 붙일 때 `CONTENT` 딕셔너리에 항목 추가
- `python scripts/neutralize-trademarks.py [--dry-run]` — 상표성 표시명 중립화 (멱등)
- `python scripts/gen-og-games.py` / `gen-og-main.py` — 게임별·사이트 대표 OG 이미지 생성

---

## Architecture

**Static multi-page site, no framework.** 모든 게임은 `public/games/<name>/index.html` 에 자가완결 HTML(inline CSS+JS, 자체 `<head>` SEO 블록)로 존재한다. 게임끼리 독립을 유지할 것 — 공용 번들러나 게임 간 import 를 도입하지 말고, 복붙이 의도된 패턴이다(한 게임을 고쳐도 다른 게임이 깨지지 않게).

현재 게임 17종: `bingo` `brick` `burger` `car-racing` `dice` `dodge` `glory-racing` `ladder` `lotto` `lucky-merge` `pacman`(닷 러너) `quiz` `roulette` `snake` `starship-lander` `team` `tetris`(블록 스택).

**게임 SEO 랜딩 3종** — `/wheel-spinner/`, `/team-generator/`, `/dice-roller/`. 게임을 iframe 으로 임베드하고 영어 콘텐츠+FAQ 스키마를 얹은 검색 유입용 페이지. 게임 본체는 수정하지 않는다.

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

**i18n & SEO.** 게임은 `?lang=` 쿼리로 16개 언어를 지원하며 `hreflang` alternate 와 JSON-LD `ItemList` 가 [public/index.html](public/index.html) 에 있다. 정규 도메인은 `https://luckyplz.com/`. 페이지를 추가하면 hreflang/canonical/OG 블록을 복제하고 `public/sitemap.xml` 에 등록한다. `.lang-bar` 는 `public/js/langBar.js` 가 주요 5개(en/ko/ja/zh/es) + "🌐 More" 드롭다운으로 정리한다.

**구조화 데이터.** 전 게임이 JSON-LD 를 갖는다(BreadcrumbList). 콘텐츠가 붙은 게임은 FAQPage 도 함께 — 화면의 `<dl>` 과 1:1 대응해야 구글 리치결과 요건을 만족한다(보이지 않는 Q&A 를 스키마에만 넣으면 위반).

**OG 이미지.** 링크로 공유되는 모든 페이지는 내용에 맞는 OG 이미지를 갖춰야 한다. 생성기는 `scripts/gen-og-games.py`(게임별), `scripts/gen-og-main.py`(사이트 대표). 폰트는 `scripts/og-fonts/`.

**Analytics.** GA4 measurement ID 는 `G-NZDPE3H3DQ` (property: LuckyPlz). 이전 `notmeplz.com` ID `G-W91WWVNLD6` 는 어디에도 남아 있으면 안 된다 — 커밋 전 grep 할 것.

**Monetization.** AdSense Publisher ID `ca-pub-5370817769801923`. **현재 미승인**("low value content" 3회+ 거절). 광고 슬롯 ID 3개는 `public/js/adSlots.js` 에 실값으로 있으나, 게임 17종 전부 `<meta name="lp-ad-policy" content="off">` 라서 `adSlots.js` 가 로드조차 되지 않는다 — 즉 **광고 배선 준비도는 0%** 이며 승인이 나도 2~3주 배선 작업이 남는다. 상세는 [docs/MONETIZATION_AUDIT_2026-08.md](docs/MONETIZATION_AUDIT_2026-08.md).

광고 배치 원칙(유지): 게임 플레이 중·설정 화면·홈 상단 **금지**. 결과 화면·홈 하단만 허용. Auto Ads 금지.

**Migration context.** 이 저장소는 2026-04-17 에 브랜딩 이유로 `notmeplz.com` 에서 분리됐다. 브랜드 텍스트는 "Lucky Please" 로 통일됐으니 `notmeplz`/`NotMePlz`/"Not Me Please" 문자열이 보이면 버그다.

**Content split (2026-08-18).** 블로그(2,015 디렉토리)·도구(27)·AI Labs(8)와 관련 스크립트·워크플로·문서는 `C:\code\python\luckyplz_blog` 로 이동했다. 그쪽 콘텐츠가 필요하면 그 저장소에서 작업하고, 이 저장소로 되가져오지 말 것.
