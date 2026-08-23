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
# /assets/ 아래의 JS 도 잡는다. 3MB 짜리 3D 번들은 /js/* 의 no-store 를
# 피하려고 /assets/deltav/ 로 옮겼는데(Pages 의 _headers 는 매칭 규칙을 전부
# 이어 붙여서 예외를 만들 수 없다), 그러면 위의 JS_RE 가 못 잡아 ?v= 가
# 영원히 안 바뀐다. 경로에 슬래시가 들어가므로 문자군에 / 를 넣는다.
ASSETJS_RE='(/assets/[a-zA-Z0-9_/-]+\.js(on)?)\?v=[0-9a-zA-Z]{4,20}'

# 무버전 참조도 잡는다: src="/js/x.js" 처럼 ?v= 없이 로드되는 공용 JS 는
# 이 스크립트가 영원히 못 덮어서 stale 로 남는다(2026-08-20 감사 —
# topNav/langBar/supabase-config 등 다수). 따옴표 직전의 .js 에 스탬프를
# 새로 붙인다. 이미 ?v= 가 있으면 다음 문자가 ? 라 매칭되지 않는다.
JS_BARE_RE='(/js/[a-zA-Z0-9_-]+\.js)(["'"'"'])'

count=0
while IFS= read -r -d '' f; do
    matched=0
    if grep -qE "$JS_RE" "$f" 2>/dev/null; then
        sed -i -E "s|${JS_RE}|\\1?v=${NEW_VERSION}|g" "$f"
        matched=1
    fi
    if grep -qE "$JS_BARE_RE" "$f" 2>/dev/null; then
        sed -i -E "s|${JS_BARE_RE}|\\1?v=${NEW_VERSION}\\2|g" "$f"
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
    if grep -qE "$ASSETJS_RE" "$f" 2>/dev/null; then
        sed -i -E "s|${ASSETJS_RE}|\\1?v=${NEW_VERSION}|g" "$f"
        matched=1
    fi
    if [ "$matched" = "1" ]; then
        count=$((count+1))
    fi
done < <(find public -name '*.html' -print0)

# siteFooter.js itself dynamically injects lpRoom.js with a ?v= query.
if grep -qE "$JS_RE" public/js/siteFooter.js 2>/dev/null; then
    sed -i -E "s|${JS_RE}|\\1?v=${NEW_VERSION}|g" public/js/siteFooter.js
    sed -i -E "s|${JS_BARE_RE}|\\1?v=${NEW_VERSION}\\2|g" public/js/siteFooter.js
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
