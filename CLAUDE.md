# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Run local dev server: `python server.py` (or double-click `start.bat` on Windows). Serves `public/` on `http://localhost:8080`; `HOST`/`PORT` env vars override. The LAN IP is printed so same-Wi-Fi devices can test mobile.
- Install deps: `pip install -r requirements.txt` (only Flask).
- **Bump cache version before every commit that touches HTML or shared JS/CSS:** `bash scripts/bump-cache.sh`. Rewrites every `?v=<stamp>` query on `/js/*.js`, `/blog/*.js`, and `/css/*.css` references to the current epoch so browsers ignoring `no-cache` still fetch fresh bundles. See the "Cache policy" section.
- **Re-inject blog-desktop.css link after creating new blog posts:** `python scripts/inject-blog-desktop-css.py`. Idempotent — adds the `<link rel="stylesheet" href="/css/blog-desktop.css?v=…">` tag right before `</head>` in every `public/blog/*/index.html` (including the blog index). Run after `bump-cache.sh` so it picks up the latest version stamp.
- There is no build step, bundler, lint, or test suite. Production is served as static files by Cloudflare Pages — `server.py` exists only for local preview and must mirror Pages' routing (directory → `index.html`).

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

**Analytics.** GA4 measurement ID is `G-NZDPE3H3DQ` (property: LuckyPlz). The prior `notmeplz.com` ID `G-W91WWVNLD6` should not appear anywhere — grep before committing.

**Migration context.** This repo was split from `notmeplz.com` on 2026-04-17 for branding reasons (lucky vs. "not me" tone). `notmeplz.com` now serves only a 4-language landing page pointing here; no code is shared between the repos. Brand text has been fully renamed to "Lucky Please" — if you spot any stray `notmeplz`/`NotMePlz`/"Not Me Please" strings, they're bugs, not intentional.
