#!/bin/bash
# Auto-bump cache version across HTML, shared JS loaders, and the live
# `/build.json` lighthouse — and refresh the inline build-check block
# in every HTML page.
#
# WHY THREE LAYERS
# ----------------
# Cloudflare Pages serves every HTML and JS path with `Cache-Control:
# no-store, no-cache, must-revalidate, max-age=0` (see public/_headers).
# That SHOULD be enough, but mobile browsers (Chrome Android, Samsung
# Internet, older iOS Safari) have repeatedly been observed serving
# stale copies anyway. After half a dozen "내 폰에서는 그대로야" reports
# the policy is now belt-AND-suspenders-AND-airbag:
#
#   1. `?v=<stamp>` query on every shared JS reference. Forces the URL
#      itself to change so even cache layers that ignore headers see a
#      different resource and refetch.
#
#   2. `/build.json` lighthouse. A tiny JSON file fetched with
#      cache:no-store on every pageload. Its `v` field is the current
#      live build stamp, controlled by THIS script.
#
#   3. Inline build-check `<script>` baked into the <head> of every
#      HTML page. It compares the version in the HTML it shipped with
#      against /build.json — on mismatch it hard-reloads with a
#      `_b=<live>` query so the browser MUST go back to the network.
#      sessionStorage caps it to one reload per stale-HTML version,
#      so the user never loops.
#
# Run before every commit that touches user-visible code or content:
#
#     bash scripts/bump-cache.sh && git add -u
#
# All three layers carry the same stamp so a deploy moves them in
# lockstep — there is no window where the lighthouse says "new build"
# but the HTML is missing the new check.

set -euo pipefail

cd "$(dirname "$0")/.."

NEW_VERSION=$(date +%s)

# ---- LAYER 1: ?v= query rewrites in shared JS + CSS references --------
JS_RE='(/js/[a-zA-Z0-9_-]+\.js)\?v=[0-9a-zA-Z]{4,20}'
BLOG_RE='(/blog/[a-zA-Z0-9_-]+\.js)\?v=[0-9a-zA-Z]{4,20}'
CSS_RE='(/css/[a-zA-Z0-9_-]+\.css)\?v=[0-9a-zA-Z]{4,20}'

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
    if grep -qE "$CSS_RE" "$f" 2>/dev/null; then
        sed -i -E "s|${CSS_RE}|\\1?v=${NEW_VERSION}|g" "$f"
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

# ---- LAYERS 2 & 3: build.json + inline build-check ---------------------
# Done in Python because regex-injecting an HTML block reliably across
# 100+ files is grim in pure Bash on Windows (sed handling of multi-line
# patterns differs by version, and CRLF normalization bites).
# `command -v` 만으로 고르면 Windows 의 Store 스텁(WindowsApps/python3)이
# 잡힌다 — "Python" 한 줄만 찍고 exit 49 로 죽어서 레이어 2·3 이 조용히
# 빠진다(2026-08-20 실제 사고: ?v= 만 갱신되고 build.json/lp-build 는
# 구 스탬프로 남았다). 실제로 실행되는 인터프리터인지 검사해서 고른다.
PYTHON_BIN=""
for c in python3 python py python.exe; do
    if "$c" -c "import sys" >/dev/null 2>&1; then PYTHON_BIN="$c"; break; fi
done
if [ -z "$PYTHON_BIN" ]; then
    echo "error: no working Python found. Install Python or add it to PATH." >&2
    exit 1
fi
"$PYTHON_BIN" scripts/bump-cache-helper.py "${NEW_VERSION}"
echo "✓ build.json + inline build-check updated to ${NEW_VERSION}."
