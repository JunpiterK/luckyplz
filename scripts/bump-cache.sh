#!/bin/bash
# Auto-bump cache version across all HTML + shared JS loader files.
#
# WHY THIS EXISTS
# ---------------
# Cloudflare Pages sends `Cache-Control: no-cache, must-revalidate` on
# /*.html and /js/* (see public/_headers). That SHOULD be enough, but
# mobile browsers (Chrome Android, Samsung Internet, older iOS Safari)
# have been observed to ignore those headers for dynamically-injected
# <script> tags. The only 100% reliable way to force a fresh fetch is
# to change the URL itself, so every shared JS reference in HTML/
# siteFooter.js carries a `?v=<stamp>` query parameter.
#
# This script rewrites that stamp to the current UNIX epoch on every
# run, guaranteeing a fresh URL per deploy. Run before every commit
# that touches user-visible code or content:
#
#     bash scripts/bump-cache.sh && git add -u
#
# HTML files also carry <meta http-equiv="Cache-Control" no-cache />
# tags as a second line of defense — see any file under public/ for
# reference. Together the two mechanisms mean an update CANNOT get
# stuck behind a stale browser cache.
#
# COVERAGE
# --------
# Two regexes — one for `/js/<name>.js?v=…` (shared loaders) and one
# for `/blog/<name>.js?v=…` (the post manifest). Kept separate so we
# can use sed's basic delimiter `|` without colliding with regex
# alternation, and so each path stays narrow enough to avoid matching
# unrelated query strings (YouTube embeds, UTM tails, etc.).

set -euo pipefail

cd "$(dirname "$0")/.."

NEW_VERSION=$(date +%s)

JS_RE='(/js/[a-zA-Z0-9_-]+\.js)\?v=[0-9a-zA-Z]{4,20}'
BLOG_RE='(/blog/[a-zA-Z0-9_-]+\.js)\?v=[0-9a-zA-Z]{4,20}'

count=0
while IFS= read -r -d '' f; do
    matched=0
    if grep -qE "$JS_RE" "$f" 2>/dev/null; then
        sed -i -E "s|${JS_RE}|\\1?v=${NEW_VERSION}|g" "$f"
        matched=1
    fi
    if grep -qE "$BLOG_RE" "$f" 2>/dev/null; then
        sed -i -E "s|${BLOG_RE}|\\1?v=${NEW_VERSION}|g" "$f"
        matched=1
    fi
    if [ "$matched" = "1" ]; then
        count=$((count+1))
    fi
done < <(find public -name '*.html' -print0)

# siteFooter.js itself dynamically injects lpRoom.js with a ?v= query.
if grep -qE "$JS_RE" public/js/siteFooter.js 2>/dev/null; then
    sed -i -E "s|${JS_RE}|\\1?v=${NEW_VERSION}|g" public/js/siteFooter.js
    count=$((count+1))
fi

echo "✓ Cache version bumped to ${NEW_VERSION} across ${count} file(s)."
