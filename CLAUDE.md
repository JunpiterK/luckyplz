# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Run local dev server: `python server.py` (or double-click `start.bat` on Windows). Serves `public/` on `http://localhost:8080`; `HOST`/`PORT` env vars override. The LAN IP is printed so same-Wi-Fi devices can test mobile.
- Install deps: `pip install -r requirements.txt` (only Flask).
- There is no build step, bundler, lint, or test suite. Production is served as static files by Cloudflare Pages — `server.py` exists only for local preview and must mirror Pages' routing (directory → `index.html`).

## Architecture

**Static multi-page site, no framework.** Every game lives at `public/games/<name>/index.html` as a standalone, self-contained HTML file (inline CSS + JS, own `<head>` SEO block). Keep games independent — do not introduce shared bundlers or cross-game imports; copy-paste is the intended pattern so a game can be edited without regression risk to others. Games currently shipped: `car-racing`, `dice`, `ladder`, `lotto`, `roulette`, `team`.

**Hosting & deploy.** Repo is `JunpiterK/luckyplz`; Cloudflare Pages project `luckyplz` auto-deploys `main` with build output dir `public`. `public/_headers` controls Cloudflare cache rules — HTML, `/games/*`, and `/js/*` are `no-cache` so edits go live immediately; `/assets/*` and `*.mp3` are cached 1 week.

**No service worker.** `public/sw.js` exists only as a self-destruct routine for legacy installs (deletes all caches and unregisters itself on activation). Every HTML page also includes an inline `navigator.serviceWorker.getRegistrations().forEach(unregister)` right before `siteFooter.js` as a belt-and-suspenders cleanup. **Do not re-introduce a caching service worker.** Stale-SW debugging cost hours during the April 2026 Lotto redesign; if you need offline support later, use versioned asset filenames or a signed-off-on plan, not a revival of the old network-first SW.

**Auth / backend.** Supabase is the only backend. Shared client lives in [public/js/supabase-config.js](public/js/supabase-config.js) and exposes `getSupabase()`, `signUp/signIn/signOut`, `getUser`, `onAuthChange`, `getDisplayName`. The anon/publishable key is intentionally committed (it's public by design). **Core games must stay playable without login** — auth is only for social/board/multiplayer features (see `public/auth/`). Don't add login gates to existing games.

**i18n & SEO.** The site targets 16 languages via `?lang=` query param with full `hreflang` alternates and JSON-LD `ItemList` in [public/index.html](public/index.html). Canonical domain is `https://luckyplz.com/`. When adding pages, replicate the hreflang/canonical/OG block and register the route in `public/sitemap.xml`.

**Analytics.** GA4 measurement ID is `G-NZDPE3H3DQ` (property: LuckyPlz). The prior `notmeplz.com` ID `G-W91WWVNLD6` should not appear anywhere — grep before committing.

**Migration context.** This repo was split from `notmeplz.com` on 2026-04-17 for branding reasons (lucky vs. "not me" tone). `notmeplz.com` now serves only a 4-language landing page pointing here; no code is shared between the repos. Brand text has been fully renamed to "Lucky Please" — if you spot any stray `notmeplz`/`NotMePlz`/"Not Me Please" strings, they're bugs, not intentional.
