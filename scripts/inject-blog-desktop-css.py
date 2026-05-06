#!/usr/bin/env python3
"""
Inject /css/blog-desktop.css link tag into every blog HTML file.

Idempotent — uses HTML comment markers so re-running the script just
updates the cache-bust query (or no-ops if the link is already current).

Targets:
- public/blog/index.html (blog index)
- public/blog/<slug>/index.html (every blog post)

Placement:
- Right before </head>, AFTER the inline <style> block, so source-order
  cascade lets the desktop overrides win on tied specificity at ≥768px.

Run before commit to ensure new blog posts get the link too.
The cache version on the ?v= query is whatever the most recent
bump-cache.sh stamped in /build.json. If build.json is missing, falls
back to current epoch.

Usage:
    python scripts/inject-blog-desktop-css.py
"""
import json
import re
import sys
import time
from pathlib import Path

# Force UTF-8 stdout on Windows so the checkmark prints
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / "public" / "blog"
BUILD_JSON = ROOT / "public" / "build.json"

MARKER_START = "<!-- lp-blog-desktop:start -->"
MARKER_END = "<!-- lp-blog-desktop:end -->"


def get_version() -> str:
    """Read cache version from build.json (set by bump-cache.sh)."""
    try:
        data = json.loads(BUILD_JSON.read_text(encoding="utf-8"))
        v = str(data.get("v", "")).strip()
        if v:
            return v
    except Exception:
        pass
    return str(int(time.time()))


def make_block(version: str) -> str:
    return (
        f"{MARKER_START}\n"
        f'<link rel="stylesheet" href="/css/blog-desktop.css?v={version}">\n'
        f"{MARKER_END}"
    )


def process(file_path: Path, block: str) -> bool:
    """Returns True if the file was modified."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Some files might have BOM or different encoding
        content = file_path.read_text(encoding="utf-8-sig")

    if MARKER_START in content and MARKER_END in content:
        # Update existing block (idempotent re-run path)
        pattern = re.compile(
            re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
            re.DOTALL,
        )
        new_content = pattern.sub(block, content)
    else:
        # First time — insert before </head>
        if "</head>" not in content:
            print(f"  [skip] {file_path.relative_to(ROOT)} — no </head> found")
            return False
        new_content = content.replace("</head>", block + "\n</head>", 1)

    if new_content != content:
        file_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    version = get_version()
    block = make_block(version)

    files = []
    blog_index = BLOG_DIR / "index.html"
    if blog_index.exists():
        files.append(blog_index)
    files.extend(sorted(BLOG_DIR.glob("*/index.html")))

    if not files:
        print("No blog HTML files found.")
        return

    changed = 0
    for f in files:
        if process(f, block):
            changed += 1

    print(f"✓ blog-desktop.css link injected/refreshed in {changed}/{len(files)} blog HTML file(s) (v={version})")


if __name__ == "__main__":
    main()
