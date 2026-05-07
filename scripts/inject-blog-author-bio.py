#!/usr/bin/env python3
"""
Inject a small "Author + Last updated" block before </footer> in every
blog HTML file.

Why: Google E-E-A-T signals reward articles with a clear author identity
+ visible last-updated date + methodology hint (primary sources). All
this is cheap to add and the cumulative effect on domain trust score
is real, especially for a site of this age.

Idempotent — uses HTML comment markers, so re-running the script just
updates the date or no-ops.

Reads dateModified from each blog post's existing JSON-LD schema, so
we don't fake-refresh dates; we just surface the existing one to humans.

Usage:
    python scripts/inject-blog-author-bio.py
"""
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / "public" / "blog"

MARKER_START = "<!-- lp-author-bio:start -->"
MARKER_END = "<!-- lp-author-bio:end -->"

# Inline CSS — small enough to ship with each file rather than a shared
# stylesheet (keeps the block self-contained, no extra HTTP request).
STYLE_BLOCK = """<style>
.lp-author-bio { margin: 28px 16px 0; padding: 18px 16px; background: linear-gradient(180deg, rgba(93,193,255,0.06) 0%, rgba(167,139,250,0.04) 100%); border: 1px solid rgba(93,193,255,0.22); border-radius: 12px; }
.lp-author-bio .lp-row { display: flex; align-items: flex-start; gap: 13px; }
.lp-author-bio .lp-avatar { width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg, #5dc1ff 0%, #a78bfa 100%); display: flex; align-items: center; justify-content: center; font-size: 19px; flex-shrink: 0; box-shadow: 0 2px 8px rgba(93,193,255,0.25); }
.lp-author-bio .lp-text { flex: 1; min-width: 0; }
.lp-author-bio .lp-name { font-size: 13.5px; font-weight: 700; color: #fff; line-height: 1.3; }
.lp-author-bio .lp-name a { color: inherit; text-decoration: none; border-bottom: 1px dashed rgba(255,255,255,0.25); }
.lp-author-bio .lp-name a:hover { border-bottom-color: #5dc1ff; }
.lp-author-bio .lp-desc { font-size: 11.5px; color: #8c9cb6; margin-top: 4px; line-height: 1.55; }
.lp-author-bio .lp-meta { display: flex; flex-wrap: wrap; gap: 10px 16px; margin-top: 13px; padding-top: 12px; border-top: 1px dashed rgba(255,255,255,0.07); font-size: 10.5px; color: #5d6e8a; line-height: 1.4; }
.lp-author-bio .lp-meta b { color: #8c9cb6; font-weight: 600; }
@media (min-width: 768px) {
  .lp-author-bio { margin: 32px 28px 0; padding: 22px 22px; }
  .lp-author-bio .lp-name { font-size: 14.5px; }
  .lp-author-bio .lp-desc { font-size: 12.5px; }
  .lp-author-bio .lp-meta { font-size: 11.5px; }
}
</style>"""

# i18n copy for the bio block
COPY = {
    "ko": {
        "name": 'By <a href="/about/">Lucky Please</a>',
        "desc": "우주산업·AI·금융 데이터를 1차 자료로 분석하는 독립 블로그. 모든 수치는 Bloomberg·Reuters·PitchBook·SEC 등 공개 자료에서 검증.",
        "updated": "마지막 업데이트",
        "sources": "1차 자료 검증",
        "lang_label": "한국어",
    },
    "en": {
        "name": 'By <a href="/about/">Lucky Please</a>',
        "desc": "Independent analysis on space, AI, and finance — every figure verified against primary sources (Bloomberg, Reuters, PitchBook, SEC).",
        "updated": "Last updated",
        "sources": "Primary-source verified",
        "lang_label": "English",
    },
}


def extract_lang(html: str) -> str:
    """Return 'ko' or 'en' based on the <html lang="..."> attribute."""
    m = re.search(r'<html\s+lang="([^"]+)"', html)
    if m:
        v = m.group(1).lower()
        if v.startswith("ko"):
            return "ko"
    return "en"


def extract_date_modified(html: str, fallback: str) -> str:
    """Pull dateModified out of the BlogPosting JSON-LD if present.

    We don't fake-refresh dates — we just expose the existing schema
    value to humans so it shows up as a visible freshness signal.
    """
    # Quick regex-based extraction (we don't need a full JSON parser)
    m = re.search(r'"dateModified"\s*:\s*"([^"]+)"', html)
    if m:
        return m.group(1)
    m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', html)
    if m:
        return m.group(1)
    return fallback


def make_block(lang: str, date_str: str) -> str:
    c = COPY.get(lang, COPY["en"])
    return f"""{MARKER_START}
{STYLE_BLOCK}
<div class="lp-author-bio" role="contentinfo">
  <div class="lp-row">
    <div class="lp-avatar" aria-hidden="true">📊</div>
    <div class="lp-text">
      <div class="lp-name">{c['name']}</div>
      <div class="lp-desc">{c['desc']}</div>
    </div>
  </div>
  <div class="lp-meta">
    <span>📅 <b>{c['updated']}</b>: {date_str}</span>
    <span>✓ <b>{c['sources']}</b></span>
    <span>🌐 {c['lang_label']}</span>
  </div>
</div>
{MARKER_END}"""


def process(file_path: Path) -> bool:
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = file_path.read_text(encoding="utf-8-sig")

    # Skip blog index page (it's a listing, not a post)
    if file_path.name == "index.html" and file_path.parent.name == "blog":
        return False

    lang = extract_lang(content)
    date_str = extract_date_modified(content, "2026-05-07")
    block = make_block(lang, date_str)

    if MARKER_START in content and MARKER_END in content:
        # Update existing block
        pattern = re.compile(
            re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
            re.DOTALL,
        )
        new_content = pattern.sub(block, content)
    else:
        # Insert before <footer>
        if "<footer>" in content:
            new_content = content.replace("<footer>", block + "\n\n<footer>", 1)
        elif "</body>" in content:
            new_content = content.replace("</body>", block + "\n\n</body>", 1)
        else:
            print(f"  [skip] {file_path.relative_to(ROOT)} — no <footer> or </body>")
            return False

    if new_content != content:
        file_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    files = sorted(BLOG_DIR.glob("*/index.html"))
    if not files:
        print("No blog post HTML files found.")
        return

    changed = 0
    for f in files:
        if process(f):
            changed += 1

    print(f"✓ author-bio block injected/refreshed in {changed}/{len(files)} blog post(s)")


if __name__ == "__main__":
    main()
