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

# A page is "dark" if its body background resolves to a dark surface.
DARK_BG_SIGNALS = ("var(--bg)", "var(--dark)", "#070a12", "#0a0e16", "#070b12")


def detect_scheme(html: str) -> str:
    m = re.search(r"body\s*\{[^}]*?background\s*:\s*([^;]+);", html, re.I | re.S)
    bg = (m.group(1).strip().lower() if m else "")
    if any(sig in bg for sig in DARK_BG_SIGNALS):
        return "dark"
    # Fallback: if the dark daily palette variable is defined anywhere, treat dark.
    if "--bg:#070a12" in html.replace(" ", ""):
        return "dark"
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
