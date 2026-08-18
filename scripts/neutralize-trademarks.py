#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""neutralize-trademarks.py — 아케이드 2종의 상표성 제품명을 중립 명칭으로 교체 (멱등).

배경 (2026-08-18 수익화 감사):
"Pac-Man"(반다이남코)·"Tetris"(Tetris Holding)는 등록상표이고, Tetris Holding 은
itch.io·Android Market 등에서 실제로 DMCA 집행을 해 온 이력이 있다. AdSense 재심사가
걸린 도메인에 상표를 제품명으로 노출해 두는 것은 리스크·수익 비대칭이므로 중립화한다.

교체 원칙 — 무엇을 바꾸고 무엇을 남기는가:
  [O] 표시 문자열: <title>, og/twitter meta, meta description, JSON-LD "name", <h1>,
      홈 index.html 의 i18n 표시 라벨
  [X] 내부 식별자: gameKey:'tetris', 'tetris_leaderboard' RPC, CSS 클래스, 파일 경로,
      URL 슬러그 → 바꾸면 Supabase 리더보드 RPC 와 기존 링크가 깨진다
  [X] 블로그 21개 파일 → 게임 '역사'를 다루는 편집 콘텐츠이므로 지명적 공정이용에
      해당한다. 상표를 제품명으로 쓰는 것이 아니라 그 게임을 지칭하는 서술이다.

사용: python scripts/neutralize-trademarks.py [--dry-run]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 표시명 치환 사전 (긴 문자열 먼저 — 부분 치환 방지)
RENAMES = [
    ("Pac-Man Classic", "Dot Runner"),
    ("Tetris Classic", "Block Stack"),
    ("Pac-Man", "Dot Runner"),
    ("PacMan", "Dot Runner"),
    ("Pacman", "Dot Runner"),
    ("Tetris", "Block Stack"),
    ("팩맨", "닷 러너"),
    ("테트리스", "블록 스택"),
    # 일본어·중국어 표시명 (각 언어의 상표 표기)
    ("パックマン", "ドットランナー"),
    ("テトリス", "ブロックスタック"),
    ("吃豆人", "点点跑者"),
    ("俄罗斯方块", "方块堆叠"),
]

# 표시 문맥만 매칭 — 내부 식별자(gameKey, RPC, CSS)는 이 패턴에 걸리지 않는다
DISPLAY_PATTERNS = [
    re.compile(r'<title>.*?</title>', re.S),
    re.compile(r'<meta\s+name="description"\s+content="[^"]*"'),
    re.compile(r'<meta\s+name="keywords"\s+content="[^"]*"'),
    re.compile(r'<meta\s+property="og:(?:title|description|image:alt)"\s+content="[^"]*"'),
    re.compile(r'<meta\s+name="twitter:(?:title|description)"\s+content="[^"]*"'),
    re.compile(r'"name"\s*:\s*"[^"]*"'),
    re.compile(r'"description"\s*:\s*"[^"]*"'),
    re.compile(r'<h1[^>]*>.*?</h1>', re.S),
    # 게임 내부 i18n 표시 테이블 — h1/부제로 렌더되는 값. 키는 식별자라 값만 매칭
    re.compile(r"(?:gameTitle|subtitle)\s*:\s*'[^']*'"),
]


def swap(text):
    out = text
    for old, new in RENAMES:
        out = out.replace(old, new)
    return out


def process_game(path, label):
    if not path.exists():
        print("[skip] {} — 파일 없음".format(label))
        return 0
    html = path.read_text(encoding="utf-8")
    orig = html
    for pat in DISPLAY_PATTERNS:
        html = pat.sub(lambda m: swap(m.group(0)), html)
    if html == orig:
        print("[same] {}".format(label))
        return 0
    if DRY:
        print("[dry ] {} — 변경 예정".format(label))
        return 1
    path.write_text(html, encoding="utf-8")
    print("[done] {} — 표시명 중립화".format(label))
    return 1


def process_home():
    """홈 index.html 의 i18n 표시 라벨만 교체. 키(pacman:/tetris:)는 식별자라 유지."""
    p = ROOT / "public" / "index.html"
    html = p.read_text(encoding="utf-8")
    orig = html

    def fix_label(m):
        return "{}: '{}'".format(m.group(1), swap(m.group(2)))

    html = re.sub(r"\b(pacman|tetris)\s*:\s*'([^']*)'", fix_label, html)
    if html == orig:
        print("[same] index.html (홈 i18n)")
        return 0
    if DRY:
        print("[dry ] index.html — 변경 예정")
        return 1
    p.write_text(html, encoding="utf-8")
    print("[done] index.html — 홈 카드 라벨 중립화")
    return 1


DRY = "--dry-run" in sys.argv

if __name__ == "__main__":
    n = 0
    n += process_game(ROOT / "public" / "games" / "pacman" / "index.html", "games/pacman")
    n += process_game(ROOT / "public" / "games" / "tetris" / "index.html", "games/tetris")
    n += process_home()
    print("\n변경 파일: {}개{}".format(n, " (dry-run)" if DRY else ""))
    if not DRY and n:
        print("URL 슬러그(/games/pacman/, /games/tetris/)는 의도적으로 유지 — "
              "변경 시 기존 공유 링크·검색 순위·리더보드 RPC 가 깨진다.")
