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

### 2. 블로그 — 테크 위주 + 관련 종목 + 매일 증시 + 스포츠
- **목적**: 기술·산업·금융·스포츠를 다루는 깊이 있는 글로 사이트 트래픽·신뢰 구축.
- **네 갈래**:
  - **자동 발행 (증시)** — 매일 증시 글 (US 마감·프리마켓 / KR 개장·마감 / CN 개장·마감, 3개 시장 × 2 슬롯). `scripts/auto-daily-post.py` 가 GitHub Actions cron 으로 작동. ko + en + ja + zh 자동 동시 작성.
  - **자동 발행 (스포츠)** — 매일 라리가·EPL·MLB 경기 결과·이슈. `scripts/auto-sports-post.py`. 리그 summary 는 객관적 테이블/이슈, 응원 코멘트는 축구=레알 마드리드·맨유, 야구=LA 다저스 팬 관점.
  - **수동 작성 시리즈** — Anthropic 시리즈, SpaceX 시리즈, AI 진화사, 우주 진화사 등 깊이 있는 longform.
  - **수동 작성 단편** — 산업·게임·확률 등 단발성 글.
- **카테고리 (7종, 2026-06-11 개편)**: `stocks`(증시), `industry`(산업), `ai-tech`(AI·테크), `space-tech`(우주 Tech), `football`(축구), `baseball`(야구), `gaming-history`(게임). 정의는 [public/blog/posts.js](public/blog/posts.js) 의 `BLOG_CATEGORIES` 가 단일 진실원천. 추가는 [docs/BLOG_AUTHORING.md](docs/BLOG_AUTHORING.md) 의 카테고리 추가 절차 참조.
  - 개편 매핑: 구 `industry`(경제·산업) → 데일리 증시는 `stocks`, 섹터/경제 심층은 `industry`(라벨만 산업으로). 구 `lifestyle`+`probability` → `gaming-history`(라벨 게임). 신설 `football`·`baseball`. 구 슬러그(`lifestyle`/`probability`/`build`/`tech-space`)는 index.html 검증에서 "all" 로 폴백.

### 운영자의 압축 메시지
> 게임은 소소하게 친구들과 쓰는 도구, 블로그는 테크 위주 깊이 있는 글. 둘 다 **한국어·영어·일본어·중국어(간체) 4종 동시 운영**.

### 4개국어 운영 — 청중 매핑
| 언어 | ISO 639-1 | 메인페이지 라우팅 | 청중 |
|---|---|---|---|
| **한국어** | `ko` | 한국어 선택 시 | 국내 본진 |
| **영어** | `en` | 영어 또는 기타 라우팅 미지정 시 (default) | 글로벌 / SEO 표준 |
| **일본어** | `ja` | 일본어 선택 시 | 일본 AI·테크 시장 |
| **중국어(간체)** | `zh` | 중국어 선택 시 | 중국 본토·홍콩 (중국 증시 자동발행과 연계) |

자동발행 증시 글은 **3개 시장 × 2 슬롯 = 6 슬롯**, 각 슬롯이 4 언어로 출력되어 하루 **24개 글**이 생성된다. 한국·미국 외에 **중국 증시 (cn-open / cn-close)** 도 자동발행 대상. 자세한 시스템은 [scripts/prompts/README.md](scripts/prompts/README.md).

---

## Blog Authoring (MANDATORY — 4 languages by default)

**모든 새 블로그 글은 한국어 + 영어 + 일본어 + 중국어(간체) 4종 동시 작성한다. 이건 default 다. 다른 언어판은 절대 별도 요청을 기다리지 않는다.**

### Why mandatory
사이트의 언어 선택은 메인 페이지에서 결정된다: **한국어 → `ko`, 일본어 → `ja`, 중국어 → `zh`, 그 외 모두 → `en`**. 한 언어만 올리면 다른 언어 사용자에게는 그 글이 존재하지 않는 것과 같다. 자동 발행 시스템도 같은 정책을 따르며, **3개 시장 (us/kr/cn) × 2 슬롯 × 4 언어 = 하루 24개 글**을 생성한다.

### Source-of-truth 언어
- **자동발행 증시 글**: 원천은 **영어**로 작성된다. 영어를 기준으로 ko·ja·zh 로 자연스럽게 번역. (Claude 단일 호출에서 4 언어 JSON 필드 모두 출력 → 비용 절약 + 일관성)
- **수동 작성 일반 블로그**: 원천은 **한국어**로 작성된다. 한국어를 기준으로 en·ja·zh 로 자연스럽게 번역.

### Slug 규칙
- **ko**: `<slug>` (예: `anthropic-story-03-claude-evolution`) — 한국어가 base slug
- **en**: `<slug>-en`
- **ja**: `<slug>-ja`
- **zh**: `<slug>-zh`
- 각 언어판 디렉토리는 `public/blog/<slug>[/-en/-ja/-zh]/index.html`

### 작업 흐름 (사용자가 따로 요청하지 않아도 자동 적용)
1. `scripts/new-blog-post.py --slug <s> --category <c>` 로 4개 디렉토리·posts.js 엔트리·sitemap 자동 비계.
2. 또는 수동 작성 시 4개 디렉토리·HTML·posts.js 엔트리 모두 만든다.
3. 각 HTML 의 `<html lang="…">` 와 `hreflang` 메타 정확히 설정.
4. posts.js 의 `alt` 필드로 ko↔en↔ja↔zh 상호 연결.
5. sitemap.xml 의 `<xhtml:link rel="alternate" hreflang="…">` 블록 4개 등록.

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
- **Scaffold a new blog post (ko + en + ja + zh 동시):** `python scripts/new-blog-post.py --slug <slug> --category <cat> --title-ko "…" --title-en "…" --title-ja "…" --title-zh "…"`. 4개 디렉토리 + posts.js 엔트리 + sitemap hreflang 블록을 한 번에 만든다. 시리즈물은 `--series anthropic-story` 등으로 테마 자동 적용. 자세한 옵션은 [docs/BLOG_AUTHORING.md](docs/BLOG_AUTHORING.md).

## Blog Publishing Checklist (every new post)

새 블로그 글 발행 시 아래 순서를 모두 거친다. 자동화된 부분은 `new-blog-post.py` 가 처리하지만, 본문 작성은 사람·AI 가 직접.

1. **4개 디렉토리 생성** — `public/blog/<slug>/`, `<slug>-en/`, `<slug>-ja/`, `<slug>-zh/` 각각에 `index.html`.
2. **본문 작성** — 원천 언어 먼저 (자동발행=en, 수동=ko), 그 다음 같은 데이터로 나머지 3 언어 자연스러운 번역(기계번역체 금지).
3. **메타데이터 일치** — 각 HTML 의 `<html lang>`, `<title>`, `<meta description>`, `og:locale`, `canonical` 모두 해당 언어판 URL/언어로 정확히.
4. **hreflang 상호 링크** — 각 HTML `<head>` 에 ko/en/ja/zh 4개 `hreflang` 등록.
5. **posts.js 엔트리 4개** — 각 lang 별 entry, `alt` 필드로 상호 연결 (다른 3 언어 슬러그 모두 forward-link).
6. **sitemap.xml 등록** — 4개 `<url>` 블록, 각각 `<xhtml:link rel="alternate" hreflang="…">` 4 줄씩.
7. **이미지 자산** — `public/assets/<series>/<ep>/fig-NN.{jpg,png}` 위치 확인.
8. **blog-desktop.css inject** — `python scripts/inject-blog-desktop-css.py` (멱등, 새 파일에만 추가).
9. **cache bump** — `bash scripts/bump-cache.sh`.
10. **로컬 미리보기** — `python server.py` 로 ko/en/ja/zh 4판 모두 열어 본문·이미지·hreflang 확인.
11. **commit** — 메시지에 ko/en/ja/zh 모두 포함됨을 명시.
12. **git pull --rebase + push** — race 안전 패턴 (cron 자동발행과 충돌 회피).

**4개 언어 중 하나라도 빠진 채 commit 하지 말 것.** 부족한 언어판이 있으면 commit 전에 task 로 등록하고 다음 세션 우선 처리.

## Architecture

**Static multi-page site, no framework.** Every game lives at `public/games/<name>/index.html` as a standalone, self-contained HTML file (inline CSS + JS, own `<head>` SEO block). Keep games independent — do not introduce shared bundlers or cross-game imports; copy-paste is the intended pattern so a game can be edited without regression risk to others. Games currently shipped: `car-racing`, `dice`, `ladder`, `lotto`, `roulette`, `team`.

**Blog has shared cross-cutting concerns** (related-posts injection via `blogRelated.js`, subscribe form via `blogSubscribe.js`, history-based recommendations) that don't fit the games' "fully self-contained" rule. Blog posts also share a single desktop layout override at `public/css/blog-desktop.css` — the inline mobile-first CSS in each blog HTML caps body at 480px (handcrafted for phones), and the desktop stylesheet kicks in at ≥768px to widen the column to 760–820px without touching the inline rules. The link tag is auto-injected into every `public/blog/*/index.html` by `scripts/inject-blog-desktop-css.py` (idempotent, marker-fenced). Run that script after creating a new blog post or it will look 480px-narrow on desktop.

**Hosting & deploy.** Repo is `JunpiterK/luckyplz`; Cloudflare Pages project `luckyplz` auto-deploys `main` with build output dir `public`. `public/_headers` controls Cloudflare cache rules — HTML, `/games/*`, and `/js/*` are `no-cache` so edits go live immediately; `/assets/*` and `*.mp3` are cached 1 week.

**Cache policy — three-layer airbag (MUST READ before committing).** Mobile browsers (Chrome Android, Samsung Internet, older iOS Safari) repeatedly ignore the `no-cache` header for HTML and dynamically-injected `<script>` tags. After half a dozen "내 폰에서는 그대로야" reports the policy is now belt-AND-suspenders-AND-airbag. **Run `bash scripts/bump-cache.sh` before every commit that touches HTML or any file under `public/js/`** — it updates all three layers in lockstep:

1. **`?v=<stamp>` query rewrites** on every shared JS reference (`/js/*.js`, `/blog/posts.js`, plus the dynamic injection inside `siteFooter.js`). Forces the URL itself to change so even cache layers that ignore headers see a different resource.
2. **`/build.json` lighthouse** — a tiny JSON file with `{"v":"<stamp>"}`. Served with `Cache-Control: no-store` and fetched by every pageload. The single source of truth for "what is the live build?".
3. **Inline build-check `<script>`** baked into the `<head>` of every HTML page (fenced by `<!--lp-build-check:start-->` / `<!--lp-build-check:end-->`). Compares the version baked into the HTML it shipped with against `/build.json` — on mismatch it hard-reloads with a `_b=<live>` cache-busting query so the browser MUST go back to the network. `sessionStorage` caps it to one reload per stale-HTML version, so users never loop.

`public/_headers` separately serves `/*.html`, `/`, `/games/*`, `/js/*`, `/blog/posts.js`, and `/build.json` with `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`. Together this means a deploy lands within one fetch on every device — even if a CDN edge or mobile cache layer would otherwise have served the previous build for hours. The only state that SHOULD survive across visits is localStorage (saved groups/presets/nicknames + game history). Everything else reaches users on the next page load; if it doesn't, you forgot to run `bump-cache.sh`.

**Cache policy — operating workflow (MUST READ when doing series-scale work).** The three-layer mechanism above is correct and must NOT be simplified. What changed after the 2026-05-26 incident is **how often `bump-cache.sh` is run**, not what it does. The script rewrites the build stamp across 200+ HTML files on every invocation; running it 4 times in a single afternoon (which is what happened during the Anthropic series rollout: Ep.3+4 / Ep.5 / Ep.6 / Ep.7) produced 4 back-to-back commits of ~225 modified files each, and GitHub's automated abuse detection temporarily suspended the account at UTC 12:24 — exactly during the us-premarket cron window, which then silently missed. Recovery was clean (account auto-restored within hours, missed slot manually triggered via `gh workflow run`), but to never trip the same wire again, the workflow rules are:

1. **One bump-cache run per working session, not per commit.** If you are doing a series-scale change (e.g. writing Ep.N of a 4-language series), DO all the writes first, then run `bump-cache.sh` ONCE at the end, then commit ONCE. The stamp is the same across all the new files anyway — running the bumper between sub-steps just multiplies the commit size for zero user-visible benefit.
2. **Series-scale work should land in 1–2 commits, not one-per-episode.** The 2026-05-26 incident was 4 large commits in ~6 hours. Combine them.
3. **If multiple large commits are unavoidable, leave ≥30 minutes between pushes.** This avoids colliding with the auto-publish cron schedule (`30 19` us-close / `0 22` kr-open / `30 23` cn-open / `35 6` kr-close / `5 7` cn-close / `30 12` us-premarket, all UTC) and keeps the rate-of-large-commits below the abuse threshold.
4. **The auto-publish cron itself is fine — leave it alone.** Each cron commit touches ~5 new files (one slot's HTML in 4 languages plus a posts.js + sitemap.xml insert) and does NOT call `bump-cache.sh`. That keeps it well under any reasonable abuse threshold and is why cron commits have never tripped detection.
5. **If you see `remote: Your account is suspended` from git or in Actions logs**, do NOT retry in a loop. Wait ~30 minutes (the 2026-05-26 case auto-resolved in roughly that window), then verify with a small fetch. Any cron run that was scheduled inside the suspension window is lost — recover it manually with `gh workflow run daily-cron.yml -f slot=<slot>` once the account is back. `cron-monitor.yml` will also flag it, but the monitor itself is subject to the same suspension so cannot self-heal in that window.

**Auto-publish holiday guard (MUST READ before changing cron / monitor / auto-daily-post.py).** 자동 발행 슬롯 6개는 시장 휴장일에 발행하면 안 된다. 2026-05-30 (토) / 5-31 (일) 사고 — Tier-1 weekend 가드가 코드상 있었음에도 9개 슬러그가 토·일에 발행돼 Friday 데이터를 잘못된 날짜로 노출했다 (총 36 디렉토리 + posts.js + sitemap + OG 일괄 삭제). 사고 후 적용된 3중 가드 규칙:

1. **Tier-0 weekend = UNCONDITIONAL** — `scripts/auto-daily-post.py` 의 `is_weekend()` 는 `args.force` 도 `--bypass-holiday-guard` 도 **절대** 무력화 못 한다. Sat/Sun 의 trading_date 는 늘 skip + HC success ping. weekend 가드는 `if not args.force` 블록 밖으로 빼야 한다 (자동화 경로에서 force 가 무심코 켜지면 막을 길이 없어진다 — 사고의 추정 원인).
2. **Tier-1 exchange holiday = bypassable only with `--bypass-holiday-guard`** — `exchange_calendars` 캘린더에 의존. `--force` 는 더 이상 휴장 가드를 무력화하지 않는다 (의미 분리). 그리고 캘린더 lookup 실패 시 이제 **HARD-FAIL** (skip + HC fail ping). 이전 "default to open" 동작이 silent failure 의 원인이었기 때문에, 모르면 **발행 안 함** 이 원칙.
3. **cron-monitor 도 자체 weekend 가드** — `.github/workflows/cron-monitor.yml` 의 첫 step 에서 `dow_kst` 계산해 KST 가 Sat/Sun 이면 `MONITOR_WEEKEND=1` 환경변수 세팅. 모든 rescue step 은 `if: env.MONITOR_WEEKEND != '1'`. us-close 만 yesterday-KST 의 DOW 를 따로 확인 (offset=-1 이라 어제가 weekend 면 어제용 recap 도 발행 안 함).

운영 규칙:
- `--force` = duplicate-publish guard 만 우회 (이미 있는 슬러그 덮어쓰기). 휴장 가드는 안 건드림.
- `--bypass-holiday-guard` = Tier-1 휴장 가드만 우회 (드문 manual essay 용). Weekend 는 여전히 막힘.
- `--check-only` = 가드만 돌려보고 종료. exit 0 = 발행 대상, 1 = skip 대상. cron-monitor 가 rescue trigger 전 사전 확인 용도로 쓸 수 있음.
- `exchange-calendars` pin (`requirements.txt` >= 4.10.0) — 4.5.x 는 XSHG 데이터가 2025-12-31 까지라 2026 lookup 시 `DateOutOfBounds` 발생. lookup 실패는 hard-skip 으로 처리되므로 silent 가 아니지만, 핀이 안 맞으면 그 슬롯 1개가 매일 hard-skip 된다. workflow 로그에서 `[guard] tier-1 ... lookup FAILED ... DateOutOfBounds` 보이면 핀 버전 bump.

휴장에 글이 또 올라간 게 보이면 → (a) 가드가 통과된 이유를 로그에서 확인, (b) `scripts/delete-weekend-posts.py --apply` 로 일괄 정리, (c) 가드 회피 경로 패치. 정리 스크립트는 base + en/ja/zh 4판 + posts.js + sitemap + OG 까지 한 번에 처리하는 멱등 스크립트다.

**Sports auto-publish (라리가·EPL·MLB 일일 발행 — 2026-06-11 신설).** `scripts/auto-sports-post.py` 가 매일 2 슬롯을 발행한다 (`.github/workflows/sports-cron.yml`):
- **`football-daily`** (category `football`) — 라리가(PD) + EPL(PL), `football-data.org` v4 API. **`FOOTBALL_DATA_KEY` repo secret 필요** (무료 키, https://www.football-data.org/client/register). cron `20 1 * * *` (10:20 KST, 어제 유럽 경기).
- **`baseball-daily`** (category `baseball`) — MLB, `statsapi.mlb.com` (키 불필요). cron `50 8 * * *` (17:50 KST, 어제 MLB 슬레이트). 응원 관점: 축구=레알·맨유, 야구=LA 다저스.
- **팩트 안전 설계 (핵심)**: 경기 결과·순위표 테이블은 **API JSON 에서 직접 렌더**된다. Claude 는 점수를 만질 기회가 없고, **산문(summary·이슈·팬 코멘트)만** 작성한다 → 점수 조작이 구조적으로 불가능. 리그 summary·이슈는 객관적, '팬 시각' 박스만 주관적(명시 라벨).
- **무경기 가드**: 모니터 리그가 그 날짜에 Final 경기 0개면 깨끗하게 skip + HC success ping. 라리가·EPL 여름 휴식기(6~7월)·MLB 오프시즌(11~3월) 자동 비발행. 휴장 weekend 가드는 **불필요**(스포츠는 주말에도 경기) — 증시 가드 로직과 혼동 금지.
- 인프라는 `auto-daily-post.py` 의 검증된 함수(`call_claude` retry+fallback, `notify_healthcheck`, `update_sitemap`, `bump_cache`, `git_push`)를 importlib 로 재사용한다. 템플릿은 `daily-base.html` 공용(스포츠는 `article:section`=Sports 로 치환). CSS 는 `public/css/daily.css` 의 `.sp-*` 컴포넌트. OG 는 `scripts/gen_sports_og.py` (gen_daily_og 폰트 재사용, 축구=초록 잔디·야구=네이비 다이아 테마). 프롬프트는 `scripts/prompts/football-daily.md` / `baseball-daily.md`.
- 운영 첫 가동: (1) `FOOTBALL_DATA_KEY` secret 등록, (2) `gh workflow run sports-cron.yml -f slot=baseball-daily` 로 야구 1편 즉시 발행 테스트(MLB 시즌 중이라 바로 됨), (3) 축구는 8월 시즌 재개 시 자동 가동. 선택: `HC_URL_FOOTBALL_DAILY` / `HC_URL_BASEBALL_DAILY` HC 체크 추가.

**No service worker.** `public/sw.js` exists only as a self-destruct routine for legacy installs (deletes all caches and unregisters itself on activation). Every HTML page also includes an inline `navigator.serviceWorker.getRegistrations().forEach(unregister)` right before `siteFooter.js` as a belt-and-suspenders cleanup. **Do not re-introduce a caching service worker.** Stale-SW debugging cost hours during the April 2026 Lotto redesign; if you need offline support later, use versioned asset filenames or a signed-off-on plan, not a revival of the old network-first SW.

**Auth / backend.** Supabase is the only backend. Shared client lives in [public/js/supabase-config.js](public/js/supabase-config.js) and exposes `getSupabase()`, `signUp/signIn/signOut`, `getUser`, `onAuthChange`, `getDisplayName`. The anon/publishable key is intentionally committed (it's public by design). **Core games must stay playable without login** — auth is only for social/board/multiplayer features (see `public/auth/`). Don't add login gates to existing games.

**Bot protection (Cloudflare Turnstile).** `supabase-config.js` has a `TURNSTILE_SITE_KEY` constant (default empty = disabled). When set, the auth forms (login/signup/password-reset) render a Turnstile widget and pass its token to Supabase, which validates the token against the secret stored in the dashboard. To enable: (1) Cloudflare dashboard → Turnstile → Add a site (domain `luckyplz.com`, mode Managed); (2) paste the SITE KEY into `TURNSTILE_SITE_KEY` in `public/js/supabase-config.js`; (3) paste the SECRET KEY into Supabase dashboard → Authentication → Captcha protection (Provider: Turnstile, Enable). Both keys must match for the system to work — if you deploy the client-side key without configuring the dashboard, Supabase rejects all auth. Turnstile free tier covers 1 M challenges/month, plenty for our scale. The widget uses dark theme (matches the auth page background).

**i18n & SEO.** The site targets 16 languages via `?lang=` query param with full `hreflang` alternates and JSON-LD `ItemList` in [public/index.html](public/index.html). Canonical domain is `https://luckyplz.com/`. When adding pages, replicate the hreflang/canonical/OG block and register the route in `public/sitemap.xml`.

**언어 선택 UI (2026-06-14 개편) — 게임 16 vs 콘텐츠 5.** 게임(홈)은 글로벌 유입 SEO 때문에 16개국어를 유지하되, `.lang-bar` 를 `public/js/langBar.js` 가 5개 주요(en/ko/ja/zh/es) + "🌐 More" 드롭다운으로 정리한다. **콘텐츠(블로그·도구)는 인구×운영 가성비로 5개국어로 선택집중: ko·en·ja·zh·es** (인도는 영어 커버, 중국은 중국어 필수, 스페인어는 중남미, 프랑스어는 영어로 커버되어 제외). 블로그 인덱스·도구 랜딩·도구 페이지에는 공유 선택기 `public/js/langSelect.js` 를 `<div id="lp-langbar"></div>` 마운트로 붙인다. 디렉토리 페이지(hreflang 구분 언어>1)는 hreflang으로 이동·미번역은 영어, 클라이언트 i18n 페이지(블로그/랜딩)는 `?lang` 리로드. **ko/en 기본, ja/zh/es 미번역 시 영어 폴백** (블로그 인덱스 chrome 는 비-ko 전부 영어).

**Blog content language tiers (다국어 운영 기준).** 메인 페이지의 언어 선택이 블로그에도 그대로 라우팅된다:
- **Tier A (mandatory, 모든 블로그 글)**: `ko` (한국어), `en` (영어), `ja` (일본어), `zh` (중국어 간체). 새 글은 처음부터 4종으로 만든다. 자세한 룰은 위 "Blog Authoring (MANDATORY)" 섹션 참조. **`es`(스페인어)는 콘텐츠 5번째 타깃 언어** — 선택기에 노출되며 미작성 시 영어 폴백. 새 플래그십 콘텐츠는 es 추가 고려.
- **Tier B (optional, 특정 트래픽 타깃 글)**: 추가 11언어 (de, es, fr, hi, id, it, pt, ru, th, tr, vi). 현재 `spacex-ipo-2026` 시리즈가 7언어로 운영 중. 새 글이 Tier B 로 갈 필요가 있으면 [docs/BLOG_AUTHORING.md](docs/BLOG_AUTHORING.md) 의 "Tier B 승격 절차" 참조.
- 메인 페이지의 언어 선택은 게임에도 적용되지만, 게임은 UI 가 가벼워 자동 i18n (브라우저 lang 또는 `?lang=`) 으로 처리. 블로그는 본문 자체가 다른 언어로 작성되어야 하므로 디렉토리 분리.
- **라우팅 규칙 (메인페이지 언어 선택 → 블로그)**: `ko` → `<slug>/`, `ja` → `<slug>-ja/`, `zh` → `<slug>-zh/`, 그 외 (en 포함 fallback) → `<slug>-en/`.

**Analytics.** GA4 measurement ID is `G-NZDPE3H3DQ` (property: LuckyPlz). The prior `notmeplz.com` ID `G-W91WWVNLD6` should not appear anywhere — grep before committing.

**Migration context.** This repo was split from `notmeplz.com` on 2026-04-17 for branding reasons (lucky vs. "not me" tone). `notmeplz.com` now serves only a 4-language landing page pointing here; no code is shared between the repos. Brand text has been fully renamed to "Lucky Please" — if you spot any stray `notmeplz`/`NotMePlz`/"Not Me Please" strings, they're bugs, not intentional.
