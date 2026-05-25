# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Site Identity & Mission (READ FIRST)

**luckyplz.com 은 두 축으로 운영된다.** 새 기능·새 글·새 디자인 변경은 이 정체성을 반드시 기준으로 삼는다.

### 1. 게임 — 친구들과 함께 쓰는 작은 도구
- **목적**: 친구·동료와 함께 내기·벌칙·역할 정하기, 또는 잠깐의 시간 떼우기.
- **두 카테고리**:
  - **행운 게임** — 룰렛, 사다리, 로또, 주사위, 팀나누기. 결정·내기·벌칙 도구.
  - **레트로 액션** — 스네이크, 팩맨, 테트리스, 카레이싱, 등 기록 갱신·심심풀이.
- **원칙**:
  - 모든 게임은 **로그인 없이 즉시 플레이 가능해야 한다**. 로그인은 소셜/멀티플레이 기능에만.
  - 모바일 우선 (세로 폰), 데스크탑·태블릿은 확장.
  - 한 게임 = 한 HTML 파일 (inline CSS/JS, 자가완결). 게임 간 의존성 만들지 말 것.

### 2. 블로그 — 테크 위주 + 관련 종목 + 매일 증시
- **목적**: 기술·산업·금융을 다루는 깊이 있는 글로 사이트 트래픽·신뢰 구축.
- **세 갈래**:
  - **자동 발행** — 매일 4편 증시 글 (US 마감·KR 개장·KR 마감·US 프리마켓). `scripts/auto-daily-post.py` 가 GitHub Actions cron 으로 작동. 이미 ko + en 자동 동시 작성.
  - **수동 작성 시리즈** — Anthropic 시리즈, SpaceX 시리즈, AI 진화사, 우주 진화사 등 깊이 있는 longform.
  - **수동 작성 단편** — 라이프스타일·확률·게이밍사 등 단발성 글.
- **카테고리 (6종)**: `ai-tech`, `space-tech`, `industry`, `gaming-history`, `lifestyle`, `probability`. 추가는 [docs/BLOG_AUTHORING.md](docs/BLOG_AUTHORING.md) 의 카테고리 추가 절차 참조.

### 운영자의 압축 메시지
> 게임은 소소하게 친구들과 쓰는 도구, 블로그는 테크 위주 깊이 있는 글. 둘 다 한국어·영어·일본어 3종 동시 운영.

---

## Blog Authoring (MANDATORY — bilingual + ja by default)

**모든 새 블로그 글은 한국어 + 영어 + 일본어 3종 동시 작성한다. 이건 default 다. 영문판·일본어판은 절대 별도 요청을 기다리지 않는다.**

### Why mandatory
사이트의 언어 선택은 메인 페이지에서 결정된다: **한국어 선택 → `ko` 판, 영어 선택 → `en` 판, 일본어 선택 → `ja` 판**. 한쪽 언어만 올리면 다른 언어 사용자에게는 그 글이 존재하지 않는 것과 같다. 자동 발행 시스템(증시 4편)은 이미 ko+en 동시 작성하고 있다 — 수동 작성 글이 그 룰을 따르지 않아 누적 부채(34개 글 영문판 누락, 2026-05-25 기준)가 쌓였다. 이 부채는 백로그로 청산 중이며, 새 글부터는 처음부터 3종으로 만든다.

### Slug 규칙
- **ko**: `<slug>` (예: `anthropic-story-03-claude-evolution`)
- **en**: `<slug>-en`
- **ja**: `<slug>-ja`
- 각 언어판 디렉토리는 `public/blog/<slug>[/-en/-ja]/index.html`

### 작업 흐름 (사용자가 따로 요청하지 않아도 자동 적용)
1. `scripts/new-blog-post.py --slug <s> --category <c>` 로 3개 디렉토리·posts.js 엔트리·sitemap 자동 비계 (Tier 2 스크립트 도입 후).
2. 또는 수동 작성 시 3개 디렉토리·HTML·posts.js 엔트리 모두 만든다.
3. 각 HTML 의 `<html lang="…">` 와 `hreflang` 메타 정확히 설정.
4. posts.js 의 `alt` 필드로 ko↔en↔ja 상호 연결.
5. sitemap.xml 의 `<xhtml:link rel="alternate" hreflang="…">` 블록 3개 등록.

### 시리즈물 (Anthropic Story 등) 규칙
- 시리즈는 일관된 시각 테마를 가진다. 새 시리즈 시작 시 [docs/BLOG_AUTHORING.md](docs/BLOG_AUTHORING.md) 에 등록.
- 현재 시리즈:
  - **An Anthropic Story** — 베이지 책 테마 (`#f5ebd8` paper, Noto Serif KR + Cormorant Garamond). 챕터 구조: Prologue → Ch.1~N → Epilogue → series-nav → footnotes → footer-block.
  - **AI Evolution (ai-evo)** — 1~8편 기술 진화사.
  - **Space Evolution (space-evo)** — 1~10편 우주 진화사.
- 시리즈 글의 어조 규칙 (사용자 반복 강조):
  - **em-dash 사용 금지** (단절감). 쉼표·세미콜론·새 문장으로 풀어 쓸 것.
  - **AI 자기언급 금지** — "이 글은 Claude 가 작성했습니다" 같은 메타 문장 금지. 사람 글 느낌.
  - **문장 종결 다양하게** — "~다.", "~이다.", "~었다." 같은 한 가지 종결만 반복하지 말 것.
  - **너무 딱딱하지 않으면서 너무 천박하지도 않게** — 진지한 스토리텔링 어조.

### 면책 표기 표준
모든 글 footer 에 `footer-block` 또는 동등한 박스로 면책 명시:
- 출처: 공개 인터뷰·언론 보도·기업 공식 발표
- 일부 세부는 추정·재구성될 수 있음을 명시
- 시리즈물은 다음 회 안내 (`series-nav`) 포함

---

## Commands

- Run local dev server: `python server.py` (or double-click `start.bat` on Windows). Serves `public/` on `http://localhost:8080`; `HOST`/`PORT` env vars override. The LAN IP is printed so same-Wi-Fi devices can test mobile.
- Install deps: `pip install -r requirements.txt` (only Flask).
- **Bump cache version before every commit that touches HTML or shared JS/CSS:** `bash scripts/bump-cache.sh`. Rewrites every `?v=<stamp>` query on `/js/*.js`, `/blog/*.js`, and `/css/*.css` references to the current epoch so browsers ignoring `no-cache` still fetch fresh bundles. See the "Cache policy" section.
- **Re-inject blog-desktop.css link after creating new blog posts:** `python scripts/inject-blog-desktop-css.py`. Idempotent — adds the `<link rel="stylesheet" href="/css/blog-desktop.css?v=…">` tag right before `</head>` in every `public/blog/*/index.html` (including the blog index). Run after `bump-cache.sh` so it picks up the latest version stamp.
- There is no build step, bundler, lint, or test suite. Production is served as static files by Cloudflare Pages — `server.py` exists only for local preview and must mirror Pages' routing (directory → `index.html`).
- **Scaffold a new blog post (ko + en + ja 동시):** `python scripts/new-blog-post.py --slug <slug> --category <cat> --title-ko "…" --title-en "…" --title-ja "…"`. 3개 디렉토리 + posts.js 엔트리 + sitemap hreflang 블록을 한 번에 만든다. 시리즈물은 `--series anthropic-story` 등으로 테마 자동 적용. 자세한 옵션은 [docs/BLOG_AUTHORING.md](docs/BLOG_AUTHORING.md).

## Blog Publishing Checklist (every new post)

새 블로그 글 발행 시 아래 순서를 모두 거친다. 자동화된 부분은 `new-blog-post.py` 가 처리하지만, 본문 작성은 사람·AI 가 직접.

1. **3개 디렉토리 생성** — `public/blog/<slug>/`, `<slug>-en/`, `<slug>-ja/` 각각에 `index.html`.
2. **본문 작성** — ko 먼저, 그 다음 같은 데이터로 en·ja 번역(자연스러운 번역, 기계번역체 금지).
3. **메타데이터 일치** — 각 HTML 의 `<html lang>`, `<title>`, `<meta description>`, `og:locale`, `canonical` 모두 해당 언어판 URL/언어로 정확히.
4. **hreflang 상호 링크** — 각 HTML `<head>` 에 ko/en/ja 3개 `hreflang` 등록.
5. **posts.js 엔트리 3개** — 각 lang 별 entry, `alt` 필드로 상호 연결 (`alt` 는 다른 두 언어 슬러그를 배열로 — 또는 기존 단일 `alt` 컨벤션 따름).
6. **sitemap.xml 등록** — 3개 `<url>` 블록, 각각 `<xhtml:link rel="alternate" hreflang="…">` 3 줄씩.
7. **이미지 자산** — `public/assets/<series>/<ep>/fig-NN.{jpg,png}` 위치 확인.
8. **blog-desktop.css inject** — `python scripts/inject-blog-desktop-css.py` (멱등, 새 파일에만 추가).
9. **cache bump** — `bash scripts/bump-cache.sh`.
10. **로컬 미리보기** — `python server.py` 로 ko/en/ja 3판 모두 열어 본문·이미지·hreflang 확인.
11. **commit** — 메시지에 ko/en/ja 모두 포함됨을 명시.
12. **git pull --rebase + push** — race 안전 패턴 (cron 자동발행과 충돌 회피).

**3개 언어 중 하나라도 빠진 채 commit 하지 말 것.** 부족한 언어판이 있으면 commit 전에 task 로 등록하고 다음 세션 우선 처리.

## Architecture

**Static multi-page site, no framework.** Every game lives at `public/games/<name>/index.html` as a standalone, self-contained HTML file (inline CSS + JS, own `<head>` SEO block). Keep games independent — do not introduce shared bundlers or cross-game imports; copy-paste is the intended pattern so a game can be edited without regression risk to others. Games currently shipped: `car-racing`, `dice`, `ladder`, `lotto`, `roulette`, `team`.

**Blog has shared cross-cutting concerns** (related-posts injection via `blogRelated.js`, subscribe form via `blogSubscribe.js`, history-based recommendations) that don't fit the games' "fully self-contained" rule. Blog posts also share a single desktop layout override at `public/css/blog-desktop.css` — the inline mobile-first CSS in each blog HTML caps body at 480px (handcrafted for phones), and the desktop stylesheet kicks in at ≥768px to widen the column to 760–820px without touching the inline rules. The link tag is auto-injected into every `public/blog/*/index.html` by `scripts/inject-blog-desktop-css.py` (idempotent, marker-fenced). Run that script after creating a new blog post or it will look 480px-narrow on desktop.

**Hosting & deploy.** Repo is `JunpiterK/luckyplz`; Cloudflare Pages project `luckyplz` auto-deploys `main` with build output dir `public`. `public/_headers` controls Cloudflare cache rules — HTML, `/games/*`, and `/js/*` are `no-cache` so edits go live immediately; `/assets/*` and `*.mp3` are cached 1 week.

**Cache policy — three-layer airbag (MUST READ before committing).** Mobile browsers (Chrome Android, Samsung Internet, older iOS Safari) repeatedly ignore the `no-cache` header for HTML and dynamically-injected `<script>` tags. After half a dozen "내 폰에서는 그대로야" reports the policy is now belt-AND-suspenders-AND-airbag. **Run `bash scripts/bump-cache.sh` before every commit that touches HTML or any file under `public/js/`** — it updates all three layers in lockstep:

1. **`?v=<stamp>` query rewrites** on every shared JS reference (`/js/*.js`, `/blog/posts.js`, plus the dynamic injection inside `siteFooter.js`). Forces the URL itself to change so even cache layers that ignore headers see a different resource.
2. **`/build.json` lighthouse** — a tiny JSON file with `{"v":"<stamp>"}`. Served with `Cache-Control: no-store` and fetched by every pageload. The single source of truth for "what is the live build?".
3. **Inline build-check `<script>`** baked into the `<head>` of every HTML page (fenced by `<!--lp-build-check:start-->` / `<!--lp-build-check:end-->`). Compares the version baked into the HTML it shipped with against `/build.json` — on mismatch it hard-reloads with a `_b=<live>` cache-busting query so the browser MUST go back to the network. `sessionStorage` caps it to one reload per stale-HTML version, so users never loop.

`public/_headers` separately serves `/*.html`, `/`, `/games/*`, `/js/*`, `/blog/posts.js`, and `/build.json` with `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`. Together this means a deploy lands within one fetch on every device — even if a CDN edge or mobile cache layer would otherwise have served the previous build for hours. The only state that SHOULD survive across visits is localStorage (saved groups/presets/nicknames + game history). Everything else reaches users on the next page load; if it doesn't, you forgot to run `bump-cache.sh`.

**No service worker.** `public/sw.js` exists only as a self-destruct routine for legacy installs (deletes all caches and unregisters itself on activation). Every HTML page also includes an inline `navigator.serviceWorker.getRegistrations().forEach(unregister)` right before `siteFooter.js` as a belt-and-suspenders cleanup. **Do not re-introduce a caching service worker.** Stale-SW debugging cost hours during the April 2026 Lotto redesign; if you need offline support later, use versioned asset filenames or a signed-off-on plan, not a revival of the old network-first SW.

**Auth / backend.** Supabase is the only backend. Shared client lives in [public/js/supabase-config.js](public/js/supabase-config.js) and exposes `getSupabase()`, `signUp/signIn/signOut`, `getUser`, `onAuthChange`, `getDisplayName`. The anon/publishable key is intentionally committed (it's public by design). **Core games must stay playable without login** — auth is only for social/board/multiplayer features (see `public/auth/`). Don't add login gates to existing games.

**Bot protection (Cloudflare Turnstile).** `supabase-config.js` has a `TURNSTILE_SITE_KEY` constant (default empty = disabled). When set, the auth forms (login/signup/password-reset) render a Turnstile widget and pass its token to Supabase, which validates the token against the secret stored in the dashboard. To enable: (1) Cloudflare dashboard → Turnstile → Add a site (domain `luckyplz.com`, mode Managed); (2) paste the SITE KEY into `TURNSTILE_SITE_KEY` in `public/js/supabase-config.js`; (3) paste the SECRET KEY into Supabase dashboard → Authentication → Captcha protection (Provider: Turnstile, Enable). Both keys must match for the system to work — if you deploy the client-side key without configuring the dashboard, Supabase rejects all auth. Turnstile free tier covers 1 M challenges/month, plenty for our scale. The widget uses dark theme (matches the auth page background).

**i18n & SEO.** The site targets 16 languages via `?lang=` query param with full `hreflang` alternates and JSON-LD `ItemList` in [public/index.html](public/index.html). Canonical domain is `https://luckyplz.com/`. When adding pages, replicate the hreflang/canonical/OG block and register the route in `public/sitemap.xml`.

**Blog content language tiers (다국어 운영 기준).** 메인 페이지의 언어 선택이 블로그에도 그대로 라우팅된다:
- **Tier A (mandatory, 모든 블로그 글)**: `ko` (한국어), `en` (영어), `ja` (일본어). 새 글은 처음부터 3종으로 만든다. 자세한 룰은 위 "Blog Authoring (MANDATORY)" 섹션 참조.
- **Tier B (optional, 특정 트래픽 타깃 글)**: 추가 12언어 (de, es, fr, hi, id, it, pt, ru, th, tr, vi, zh). 현재 `spacex-ipo-2026` 시리즈가 7언어로 운영 중. 새 글이 Tier B 로 갈 필요가 있으면 [docs/BLOG_AUTHORING.md](docs/BLOG_AUTHORING.md) 의 "Tier B 승격 절차" 참조.
- 메인 페이지의 언어 선택은 게임에도 적용되지만, 게임은 UI 가 가벼워 자동 i18n (브라우저 lang 또는 `?lang=`) 으로 처리. 블로그는 본문 자체가 다른 언어로 작성되어야 하므로 디렉토리 분리.

**Analytics.** GA4 measurement ID is `G-NZDPE3H3DQ` (property: LuckyPlz). The prior `notmeplz.com` ID `G-W91WWVNLD6` should not appear anywhere — grep before committing.

**Migration context.** This repo was split from `notmeplz.com` on 2026-04-17 for branding reasons (lucky vs. "not me" tone). `notmeplz.com` now serves only a 4-language landing page pointing here; no code is shared between the repos. Brand text has been fully renamed to "Lucky Please" — if you spot any stray `notmeplz`/`NotMePlz`/"Not Me Please" strings, they're bugs, not intentional.
