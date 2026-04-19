#!/bin/bash
# One-time migration: inject <meta http-equiv> no-cache tags into every
# HTML file that doesn't have them yet. Run once; thereafter the pattern
# is preserved on existing files and newly-created HTML should copy the
# block from any sibling.
#
# WHY: Cloudflare Pages headers already say no-cache for HTML, but some
# mobile browsers (Chrome Android, Samsung Internet) occasionally honor
# only meta tags, especially when the page came from a "recently
# visited" intent or bfcache. Belt-and-suspenders costs nothing.

set -euo pipefail

cd "$(dirname "$0")/.."

MARKER='<!-- no-cache: force fresh on every visit -->'
BLOCK="    ${MARKER}
    <meta http-equiv=\"Cache-Control\" content=\"no-cache, no-store, must-revalidate\">
    <meta http-equiv=\"Pragma\" content=\"no-cache\">
    <meta http-equiv=\"Expires\" content=\"0\">"

count=0
while IFS= read -r -d '' f; do
    if ! grep -qF "$MARKER" "$f"; then
        # Insert right after the viewport meta tag.
        python - "$f" <<'PYEOF'
import sys, re
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as fh:
    src = fh.read()
block = (
    '    <!-- no-cache: force fresh on every visit -->\n'
    '    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">\n'
    '    <meta http-equiv="Pragma" content="no-cache">\n'
    '    <meta http-equiv="Expires" content="0">\n'
)
# Insert after the viewport meta tag. Uses the first <meta name="viewport" ...> match.
new = re.sub(r'(<meta name="viewport"[^>]*>\s*\n)', r'\1' + block, src, count=1)
if new != src:
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(new)
PYEOF
        count=$((count+1))
    fi
done < <(find public -name '*.html' -print0)

echo "✓ Added no-cache meta to ${count} HTML file(s) (already present on the rest)."
