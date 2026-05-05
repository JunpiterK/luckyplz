"""Companion to scripts/bump-cache.sh.

Two jobs that are clumsy in pure Bash on Windows:

1. Update public/build.json so its `v` field equals the new build stamp.
   The browser fetches that file (cache:no-store) on every pageload and
   compares it to the stamp baked into the HTML it received. If they
   differ, the HTML is stale and the inline build-check script does a
   hard reload. That JSON file is the single source of truth for "what
   is the current live build?".

2. Inject (or update) the inline build-check block in every public/**.html
   file. The block is fenced by `<!--lp-build-check:start-->` /
   `<!--lp-build-check:end-->` so subsequent runs can find and rewrite
   it without diffing the surrounding markup. The script lives inline
   (not in /js/) on purpose — if the build-check script itself were
   cached, a stale HTML could keep loading a stale check that never
   detects mismatch. Inline guarantees the version is in the same byte
   stream as the page itself.

Usage:
    python scripts/bump-cache-helper.py <NEW_VERSION>
"""
import json
import pathlib
import re
import sys


ROOT = pathlib.Path('public')
START = '<!--lp-build-check:start-->'
END = '<!--lp-build-check:end-->'


def snippet(version: str) -> str:
    """Inline build-check HTML block. Fences are stable comment markers
    so the bumper can rewrite the contents on every run.

    The script:
    1. Reads the build version baked into the HTML it ships with.
    2. Fetches /build.json with cache:no-store (must hit origin).
    3. If the fetched version differs, the HTML is stale -> hard reload
       with a fresh `_b` query so the browser actually re-fetches.
    4. Uses sessionStorage to ensure each baked-in version triggers at
       most one reload, avoiding loops if the network keeps returning
       the same stale HTML for any reason.
    """
    return (
        f'{START}\n'
        f'<meta name="lp-build" content="{version}">\n'
        f'<script>(function(){{var B="{version}";try{{fetch("/build.json?_="+Date.now(),{{cache:"no-store"}}).then(function(r){{return r.ok?r.json():null}}).then(function(d){{if(!d||!d.v||d.v===B)return;var k="lp_build_"+B;try{{if(sessionStorage.getItem(k))return;sessionStorage.setItem(k,"1");}}catch(e){{}}var u=new URL(location.href);u.searchParams.set("_b",d.v);location.replace(u.toString());}}).catch(function(){{}});}}catch(e){{}}}})();</script>\n'
        f'{END}'
    )


def update_or_inject(html: str, version: str) -> str:
    block_re = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.DOTALL)
    new_block = snippet(version)
    if block_re.search(html):
        return block_re.sub(new_block, html, count=1)

    # First-time inject: drop the block right after <meta name="viewport"...>.
    # Every page in this repo ships with that meta on a single line just
    # below the charset declaration, so anchoring there keeps the block
    # near the top of <head> (where it must run before page-specific
    # scripts) without colliding with framework-specific structures.
    vp_re = re.compile(
        r'(<meta\s+name\s*=\s*["\']viewport["\'][^>]*>\s*)',
        re.IGNORECASE,
    )
    if vp_re.search(html):
        return vp_re.sub(r'\1' + new_block + '\n', html, count=1)

    head_re = re.compile(r'(<head[^>]*>\s*)', re.IGNORECASE)
    if head_re.search(html):
        return head_re.sub(r'\1' + new_block + '\n', html, count=1)

    return html  # no <head>? skip silently — nothing to inject into.


def main(version: str) -> None:
    sys.stdout.reconfigure(encoding='utf-8')

    # 1. build.json
    bj = ROOT / 'build.json'
    if bj.exists():
        try:
            data = json.loads(bj.read_text(encoding='utf-8'))
        except Exception:
            data = {}
    else:
        data = {}
    data['v'] = version
    bj.write_text(
        json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n',
        encoding='utf-8',
    )

    # 2. inline build-check across every HTML file
    count = 0
    for p in ROOT.rglob('*.html'):
        s = p.read_text(encoding='utf-8')
        s2 = update_or_inject(s, version)
        if s != s2:
            # Preserve LF line endings — git is configured for LF on this
            # repo and CRLF would re-trigger the warning loop on every
            # commit. `Path.write_text(newline=...)` is 3.10+ only, so
            # write bytes directly to stay compatible with older Python
            # installs.
            p.write_bytes(s2.encode('utf-8'))
            count += 1

    print(f'✓ build.json -> v={version}')
    print(f'✓ inline build-check refreshed in {count} HTML file(s).')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: python scripts/bump-cache-helper.py <VERSION>', file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
