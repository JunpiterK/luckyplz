#!/usr/bin/env python3
"""Inject a `color-scheme` declaration into every blog HTML <head>.

WHY (2026-06-20):
Blog posts use a light design (beige book theme `var(--paper)`, or white). With
NO `color-scheme` declared, some browsers (Chrome desktop Auto Dark Mode, Edge,
Android Chrome "Auto dark theme", certain OS-dark setups) FORCE-DARK light pages,
inverting the beige background into a muddy near-black. Users see "거무튀튀한"
pages even though the site has no dark theme of its own.

Fix: declare the page's intended scheme explicitly. A light page that says
`color-scheme: light` is exempt from browser force-dark. Daily market/sports
posts are genuinely dark (`--bg:#070a12`), so they get `dark` — correct for
their scrollbars/form controls and harmless to force-dark (already dark).

The block is marker-fenced so re-runs rewrite in place (idempotent). Declares
BOTH a `<meta name="color-scheme">` (strongest, parsed in <head> before paint)
and a `:root { color-scheme }` CSS rule (belt-and-suspenders).

Usage:
    python scripts/inject-color-scheme.py            # dry-run (report only)
    python scripts/inject-color-scheme.py --apply    # write changes
"""
import io
import glob
import re
import sys

APPLY = "--apply" in sys.argv
START = "<!--lp-color-scheme:start-->"
END = "<!--lp-color-scheme:end-->"

def _luminance(hex6: str) -> float:
    """Perceived luminance 0~255 from a 6-digit hex (no #)."""
    r, g, b = int(hex6[0:2], 16), int(hex6[2:4], 16), int(hex6[4:6], 16)
    return 0.299 * r + 0.587 * g + 0.114 * b


def detect_scheme(html: str) -> str:
    """Decide light vs dark from the page's actual rendered background.

    History (2026-06-21 블로그 라이트 전환): the old heuristic flagged any page
    whose body background was `var(--bg)` as dark. That wrongly tagged ai-evo /
    space-evo (which define `--bg` as a LIGHT hex) as dark, so they got
    `color-scheme: dark` and were force-darkened. The fix resolves the var to
    its actual hex and judges by luminance, and short-circuits daily posts.
    """
    # 데일리 자동발행 글은 /css/daily.css(라이트 종이 override)를 로드한다.
    # inline body 배경은 var(--bg)(다크)지만 시트가 라이트로 덮으므로 light.
    if "/css/daily.css" in html:
        return "light"

    m = re.search(r"body\s*\{[^}]*?background\s*:\s*([^;]+);", html, re.I | re.S)
    bg = (m.group(1).strip().lower() if m else "")

    # body background 가 var(--x) 면 그 변수의 실제 정의값(hex)으로 resolve.
    vm = re.search(r"var\(\s*(--[\w-]+)", bg)
    if vm:
        dm = re.search(re.escape(vm.group(1)) + r"\s*:\s*(#[0-9a-f]{3,6})", html, re.I)
        if dm:
            bg = dm.group(1).lower()

    h6 = re.search(r"#([0-9a-f]{6})", bg)
    if h6:
        return "dark" if _luminance(h6.group(1)) < 128 else "light"
    h3 = re.search(r"#([0-9a-f]{3})\b", bg)
    if h3:
        x = h3.group(1)
        return "dark" if _luminance(x[0] * 2 + x[1] * 2 + x[2] * 2) < 128 else "light"

    # 배경을 못 정하면 light (force-dark 로 라이트가 반전되는 쪽이 더 위험).
    return "light"


def build_block(scheme: str) -> str:
    return (
        f"{START}"
        f'<meta name="color-scheme" content="{scheme}">'
        f"<style>:root{{color-scheme:{scheme};}}</style>"
        f"{END}"
    )


def process(path: str):
    with io.open(path, encoding="utf-8") as f:
        html = f.read()
    scheme = detect_scheme(html)
    block = build_block(scheme)

    existing = re.search(re.escape(START) + ".*?" + re.escape(END), html, re.S)
    if existing:
        if existing.group(0) == block:
            return ("nochange", scheme)
        new = html[: existing.start()] + block + html[existing.end():]
        action = "updated"
    else:
        # Insert right after the charset meta (kept high in <head>).
        cm = re.search(r"<meta\s+charset=[^>]*>", html, re.I)
        if cm:
            new = html[: cm.end()] + "\n" + block + html[cm.end():]
        else:
            hm = re.search(r"<head[^>]*>", html, re.I)
            if not hm:
                return ("skip-no-head", scheme)
            new = html[: hm.end()] + "\n" + block + html[hm.end():]
        action = "injected"

    if APPLY:
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    return (action, scheme)


def main():
    files = sorted(set(glob.glob("public/blog/**/index.html", recursive=True)))
    counts = {}
    schemes = {"light": 0, "dark": 0}
    samples = {"injected": [], "updated": []}
    for path in files:
        action, scheme = process(path)
        counts[action] = counts.get(action, 0) + 1
        if scheme in schemes:
            schemes[scheme] += 1
        if action in samples and len(samples[action]) < 4:
            samples[action].append(path.replace("public/blog/", "").replace("/index.html", "") + f" [{scheme}]")

    mode = "APPLIED" if APPLY else "DRY-RUN (use --apply to write)"
    print(f"[{mode}] color-scheme over {len(files)} blog HTML files")
    for k in ("injected", "updated", "nochange", "skip-no-head"):
        if k in counts:
            print(f"  {k:12s}: {counts[k]}")
    print(f"  scheme split : light={schemes['light']}  dark={schemes['dark']}")
    for k in ("injected", "updated"):
        if samples[k]:
            print(f"  sample {k}: {', '.join(samples[k])}")


if __name__ == "__main__":
    main()
