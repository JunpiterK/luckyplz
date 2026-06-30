"""Repository quality checks for luckyplz static publishing.

This is intentionally lightweight: no network, no browser, no dependencies.
Run it before commit when changing public HTML, generated posts, or repo hygiene.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
TEXT_EXTS = {".html", ".js", ".css", ".json", ".md", ".txt", ".py", ".sql", ".yml", ".yaml"}
SKIP_DIRS = {".git", ".claude", "vendor", "__pycache__", "node_modules"}


def iter_text_files(*roots: str):
    for root_name in roots:
        root = ROOT / root_name
        if not root.exists():
            continue
        if root.is_file():
            candidates = [root]
        else:
            candidates = root.rglob("*")
        for path in candidates:
            if not path.is_file():
                continue
            if path.resolve() == SELF:
                continue
            rel_parts = set(path.relative_to(ROOT).parts)
            if rel_parts & SKIP_DIRS:
                continue
            if path.suffix.lower() not in TEXT_EXTS:
                continue
            yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def check_no_replacement_glyph(errors: list[str]) -> None:
    for path in iter_text_files("public", "scripts", "supabase", ".github"):
        text = read_text(path)
        if "\ufffd" in text:
            line = text.count("\n", 0, text.index("\ufffd")) + 1
            errors.append(f"replacement glyph found: {path.relative_to(ROOT)}:{line}")


def check_stale_public_copy(errors: list[str]) -> None:
    stale_patterns = [
        "미니게임 9종",
        "무료 결정 도구 5종",
        "게임 모음 15가지",
        "블로그 글 70+편",
        "70편 이상",
        "one of 4 daily blog slots",
        "bilingual HTML",
    ]
    for path in iter_text_files("public", "scripts"):
        text = read_text(path)
        for pattern in stale_patterns:
            if pattern in text:
                errors.append(f"stale copy '{pattern}': {path.relative_to(ROOT)}")


def check_old_brand_in_production(errors: list[str]) -> None:
    pattern = re.compile(r"G-W91WWVNLD6|notmeplz|NotMePlz|Not Me Please")
    for path in iter_text_files("public", "scripts", "supabase", ".github"):
        text = read_text(path)
        match = pattern.search(text)
        if match:
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"old brand or GA id in production path: {path.relative_to(ROOT)}:{line}")


def check_favicon(errors: list[str]) -> None:
    if not (ROOT / "public" / "favicon.ico").is_file():
        errors.append("missing public/favicon.ico")


def check_tracked_artifacts(errors: list[str]) -> None:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            text=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI fallback
        errors.append(f"git ls-files failed: {exc}")
        return

    artifact_re = re.compile(
        r"(^|/)(\.vs|bin|obj)/|"
        r"\.(exe|dll|pdb|zip|suo|user|vsidx|db|sqlite)$",
        re.IGNORECASE,
    )
    bad = [line for line in result.stdout.splitlines() if artifact_re.search(line)]
    for line in bad[:20]:
        errors.append(f"tracked build/editor artifact: {line}")
    if len(bad) > 20:
        errors.append(f"tracked build/editor artifact: ... and {len(bad) - 20} more")


def main() -> int:
    errors: list[str] = []
    check_no_replacement_glyph(errors)
    check_stale_public_copy(errors)
    check_old_brand_in_production(errors)
    check_favicon(errors)
    check_tracked_artifacts(errors)

    if errors:
        print("quality-audit failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("quality-audit OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
