#!/usr/bin/env python3
"""Replace '수십명+' / 'Dozens+' with '100 명' / '100 people' in the bingo
reference rows of all lifestyle blog posts. Run once."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / 'public' / 'blog'

KO_FILES = [
    'coffee-1-minute', 'coffee-who-pays', 'dinner-menu-fair',
    'team-split-fair', 'elementary-team-grouping', 'wedding-mc-games',
    'picnic-game-ideas', 'presentation-order-fair', 'club-seating-fair',
]
EN_FILES = ['random-name-picker-guide']

KO_BEFORE = '<tr><td>\U0001F3B1 빙고</td><td class="reco">수십명+</td><td>실시간 호스트+게스트 룸</td></tr>'
KO_AFTER  = '<tr><td>\U0001F3B1 빙고</td><td class="reco">100 명</td><td>실시간 호스트 + 게스트 룸</td></tr>'

EN_BEFORE = '<tr><td>\U0001F3B1 Bingo (live)</td><td class="reco">Dozens+</td><td>Realtime host + guest room</td></tr>'
EN_AFTER  = '<tr><td>\U0001F3B1 Bingo (live)</td><td class="reco">100 people</td><td>Realtime host + guests room</td></tr>'

def patch(slug, before, after):
    p = BLOG / slug / 'index.html'
    if not p.exists():
        print(f'  ! missing: {p}')
        return
    txt = p.read_text(encoding='utf-8')
    n = txt.count(before)
    if n == 0:
        print(f'  - {slug}: pattern not found')
        return
    p.write_text(txt.replace(before, after), encoding='utf-8')
    print(f'  OK {slug}: {n} replacement(s)')

for s in KO_FILES:
    patch(s, KO_BEFORE, KO_AFTER)
for s in EN_FILES:
    patch(s, EN_BEFORE, EN_AFTER)
