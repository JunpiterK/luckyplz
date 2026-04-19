#!/bin/bash
# Bump the cache-bust query on every icon reference site-wide.
#
# WHY THIS EXISTS (separate from bump-cache.sh)
# ---------------------------------------------
# Icons live under /assets/* which Cloudflare Pages caches for 1 week
# per _headers. That's fine for bandwidth, but when the icon art
# actually changes — say you swap an orange mark for a green-clover
# one — every returning visitor keeps their cached copy for up to 7
# days, and Android/iOS PWAs that were already "Add to Home Screen"
# installed will continue displaying the old glyph until the OS
# re-fetches the manifest (which can take even longer).
#
# The fix is the same as for JS bundles: change the URL. This script
# walks every manifest.json icon src and every HTML icon/apple-touch-
# icon link, rewriting the `?v=<stamp>` to the current UNIX epoch.
# Run it *only when the icon artwork itself actually changed* — on
# every commit would waste everyone's cache unnecessarily.
#
#     bash scripts/bump-icons.sh
#
# On the already-installed PWA side, Chrome / Safari re-checks the
# manifest every 24h; new icon URLs will land on home screens within
# that window. Power users who want it NOW: uninstall + reinstall.

set -euo pipefail

cd "$(dirname "$0")/.."

NEW_VERSION=$(date +%s)

# /assets/icon*.png|.svg references. Query may already be present from
# a previous bump; wipe + replace, or append if none.
ICON_RE='(/assets/(icon(-[0-9]+)?\.(png|svg)|og-image\.png))(\?v=[0-9a-zA-Z]{4,20})?'

count_html=0
while IFS= read -r -d '' f; do
    if grep -qE "$ICON_RE" "$f" 2>/dev/null; then
        # Use # as sed separator because the regex contains `|` for
        # alternation (png|svg), which collides with the usual `|` sep.
        sed -i -E "s#${ICON_RE}#\\1?v=${NEW_VERSION}#g" "$f"
        count_html=$((count_html+1))
    fi
done < <(find public -name '*.html' -print0)

# manifest.json uses JSON-style src values — same icon path pattern.
if [ -f public/manifest.json ]; then
    sed -i -E "s#${ICON_RE}#\\1?v=${NEW_VERSION}#g" public/manifest.json
    count_manifest=1
else
    count_manifest=0
fi

echo "✓ Icon URLs bumped to ?v=${NEW_VERSION} across ${count_html} HTML + ${count_manifest} manifest.json."
echo "  Already-installed PWAs will pick up the new glyph within ~24h (Chrome manifest refresh)."
echo "  Users who want it sooner: uninstall + reinstall the app."
