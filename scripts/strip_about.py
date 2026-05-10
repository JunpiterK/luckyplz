#!/usr/bin/env python3
"""Strip the lp-game-about HTML section + CSS block from a game's index.html.
Used as a one-shot rollback after the AdSense long-form rollout broke
several game layouts (setup-overlay games leaked the about section behind
their transparent setupWrap).

Usage: python scripts/strip_about.py <game-name> [<game-name> ...]
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Strip the HTML <section class="lp-game-about"> ... </section> block
# (with the leading comment if present).
HTML_RE = re.compile(
    r'\s*<!--\s*ABOUT THIS GAME[^\n]*-->\s*'
    r'<section class="lp-game-about"[\s\S]*?</section>\s*',
    re.DOTALL,
)

# Strip the CSS block. We match every line that is a `.lp-game-about` rule
# (or the @media rules that target it) plus the optional leading comment.
CSS_COMMENT_RE = re.compile(
    r'/\*\s*=== ABOUT THIS GAME[^\n]*\*/\s*\n',
)
# Single-line CSS rules starting with `.lp-game-about` (could span tokens like
# `.lp-game-about .lp-about-head`, `.lp-game-about p`, etc.) — match each
# such line and remove. The CSS block was injected as a single line per rule.
CSS_RULE_RE = re.compile(
    r'^\.lp-game-about[^\n]*\{[^\n]*\}\s*\n',
    re.MULTILINE,
)
# @media containing only lp-game-about rules — match opening @media line
# through closing brace.
CSS_MEDIA_RE = re.compile(
    r'^@media[^\n]*\{[^\n]*\.lp-game-about[^\n]*\}\s*\n',
    re.MULTILINE,
)


def strip_one(game: str) -> bool:
    path = REPO_ROOT / 'public' / 'games' / game / 'index.html'
    if not path.exists():
        print(f'  ! missing: {path}')
        return False
    text = path.read_text(encoding='utf-8')
    new_text, html_n = HTML_RE.subn('\n', text)
    new_text, c1 = CSS_COMMENT_RE.subn('', new_text)
    new_text, c2 = CSS_RULE_RE.subn('', new_text)
    new_text, c3 = CSS_MEDIA_RE.subn('', new_text)
    css_n = c1 + c2 + c3
    if html_n == 0 and css_n == 0:
        print(f'  - {game}: nothing to strip')
        return False
    path.write_text(new_text, encoding='utf-8')
    print(f'  OK {game}: stripped html={html_n} css={css_n}')
    return True


def main():
    if len(sys.argv) < 2:
        print('usage: python scripts/strip_about.py <game> [<game> ...]')
        return 1
    for g in sys.argv[1:]:
        strip_one(g)
    return 0


if __name__ == '__main__':
    sys.exit(main())
