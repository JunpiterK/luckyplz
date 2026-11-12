"""상황판(/ops/) 숫자를 로그인 없이 읽어 요약을 찍는다 — 분석·정기 보고용.

읽기 전용 키(.keys/ops-read.key, 깃 제외)로 Supabase RPC lp_ops_read 를 부른다.
키는 상황판 집계 결과만 읽을 수 있고 쓰기·테이블 직접 조회는 못 한다.
키 등록은 supabase/migrations/2026-11-12-ops-stats.sql 10장 참고.

    python scripts/ops-report.py                 # 최근 7일 요약
    python scripts/ops-report.py --range today   # today / yesterday / 7d / 30d / 90d
    python scripts/ops-report.py --range 30d --json out.json   # 원본 JSON 도 저장
    python scripts/ops-report.py --sessions 40   # 방문 기록 줄 수 (기본 20)
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

SB_URL = 'https://jkrpxijybuljdxkrbsan.supabase.co'
SB_KEY = 'sb_publishable_Ypa1NMQCVGxFWidBOd5iEA_ECBldTAb'   # 공개 키(supabase-config.js 와 같음)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = timezone(timedelta(hours=9))
DEV = {'mobile': '폰', 'desktop': 'PC', 'tablet': '태블릿'}


def read_key():
    k = os.environ.get('LP_OPS_KEY') or ''
    p = os.path.join(ROOT, '.keys', 'ops-read.key')
    if not k and os.path.exists(p):
        k = open(p, encoding='utf-8').read().strip()
    if not k:
        sys.exit('읽기 키가 없어요: .keys/ops-read.key 또는 LP_OPS_KEY')
    return k


def call(key, fn, args):
    req = urllib.request.Request(
        SB_URL + '/rest/v1/rpc/lp_ops_read',
        data=json.dumps({'p_key': key, 'p_fn': fn, 'p_args': args}).encode(),
        headers={'apikey': SB_KEY, 'content-type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        if 'forbidden' in body:
            sys.exit('키가 거부됐어요 — DB 에 키 해시가 등록돼 있는지 확인')
        if 'lp_ops_read' in body:
            sys.exit('DB 에 lp_ops_read 가 아직 없어요 — 마이그레이션을 다시 적용')
        sys.exit(f'요청 실패 {e.code}: {body[:300]}')


def span(rng):
    now = datetime.now(KST)
    m0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now + timedelta(minutes=1)
    days = {'today': 0, '7d': 6, '30d': 29, '90d': 89}
    if rng == 'yesterday':
        a, b = m0 - timedelta(days=1), m0
    else:
        a, b = m0 - timedelta(days=days[rng]), end
    return a.isoformat(), b.isoformat()


def dur(ms):
    s = round((ms or 0) / 1000)
    if s < 60:
        return f'{s}초'
    m, s = divmod(s, 60)
    return f'{m}분 {s}초' if m < 60 else f'{m // 60}시간 {m % 60}분'


def pct(a, b):
    return f'{round(a / b * 100)}%' if b else '-'


def delta(cur, prev):
    if not prev:
        return '(비교 없음)' if not cur else '(새로)'
    d = round((cur - prev) / prev * 100)
    return f'({"+" if d >= 0 else ""}{d}%)'


def top(rows, key, label, n=8, extra=None):
    out = []
    for r in rows[:n]:
        s = f'  {label(r):<28} {r[key]:>6}'
        if extra:
            s += '  ' + extra(r)
        out.append(s)
    return '\n'.join(out) or '  (없음)'


def kst(ts):
    return datetime.fromisoformat(ts).astimezone(KST).strftime('%m-%d %H:%M')


def main():
    for st in (sys.stdout, sys.stderr):
        if hasattr(st, 'reconfigure'):
            st.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--range', default='7d', choices=['today', 'yesterday', '7d', '30d', '90d'])
    ap.add_argument('--json')
    ap.add_argument('--sessions', type=int, default=20)
    ap.add_argument('--inc-me', action='store_true', help='운영자 기기 방문도 포함')
    o = ap.parse_args()

    key = read_key()
    a, b = span(o.range)
    f = {'inc_me': True} if o.inc_me else {}
    board = call(key, 'board', {'from': a, 'to': b, 'f': f})
    ses = call(key, 'sessions', {'from': a, 'to': b, 'f': f, 'limit': o.sessions})
    live = call(key, 'live', {'f': f})
    days = call(key, 'days', {'days': 400})
    if o.json:
        with open(o.json, 'w', encoding='utf-8') as fp:
            json.dump({'range': o.range, 'from': a, 'to': b, 'board': board, 'sessions': ses,
                       'live': live, 'days': days}, fp, ensure_ascii=False, indent=1)

    k, p, h = board['kpi'], board['prev'], board['health']
    print(f'== luckyplz 상황판 · {o.range} ({a[:16]} ~ {b[:16]} KST) ==')
    print(f'수집 시작 {h["first"] and kst(h["first"])} · 마지막 신호 {h["last"] and kst(h["last"])} · '
          f'제외: 내 기기 {h["excluded_me"]} · 서버IP {h["excluded_dc"]}')
    print(f'지금 접속 {live["n"]}명')
    print(f'방문자 {k["visitors"]} {delta(k["visitors"], p["visitors"])} · 신규 {k["new_visitors"]} · '
          f'방문 {k["sessions"]} {delta(k["sessions"], p["sessions"])} · 페이지뷰 {k["pageviews"]}')
    print(f'평균 체류 {dur(k["avg_ms"])} · 참여율 {pct(k["engaged_sessions"], k["sessions"])} · '
          f'게임 플레이 {k["plays"]}판 (플레이한 방문 {k["play_sessions"]})')

    tot = k['sessions'] or 1
    print('\n[나라] 방문 · 방문자 · 평균 체류 · 참여율')
    print(top(board['countries'], 's', lambda r: r['c'], 12,
              lambda r: f'{r["v"]:>4}명  {dur(r["ms"]):>9}  {pct(r["eng"], r["s"])}'))
    print('\n[도시]')
    print(top(board['cities'], 's', lambda r: f'{r["c"]} {r["city"]}', 10, lambda r: dur(r['ms'])))
    print('\n[유입] 방문 · 평균 체류 · 참여율')
    print(top(board['sources'], 's', lambda r: r['src'], 12,
              lambda r: f'{dur(r["ms"]):>9}  {pct(r["eng"], r["s"])}'))
    if board['keywords']:
        print('\n[검색어]')
        print(top(board['keywords'], 'n', lambda r: f'{r["k"]} ({r["src"]})', 12))
    print('\n[페이지] 조회 · 방문자 · 평균 체류 · 첫페이지 · 플레이')
    print(top(board['pages'], 'pv', lambda r: r['p'], 15,
              lambda r: f'{r["v"]:>4}  {dur(r["ms"]):>9}  {r["ent"]:>4}  {r["plays"]:>4}'))
    d = board['dims']
    for name, kk in (('기기', 'dev'), ('OS', 'os'), ('브라우저', 'br'), ('앱 내 브라우저', 'inapp'),
                     ('사이트 언어', 'lang'), ('브라우저 언어', 'blang'), ('통신사', 'isp')):
        items = sorted(d[kk].items(), key=lambda x: -x[1])[:8]
        print(f'\n[{name}] ' + ', '.join(f'{DEV.get(x, x)} {n}({pct(n, tot)})' for x, n in items) if items else f'\n[{name}] (없음)')
    print('\n[체류 분포] <10초 / 10-30초 / 30초-1분 / 1-3분 / 3-10분 / 10-30분 / 30분+ :', board['dwell'])
    print('[페이지 수] 1 / 2 / 3 / 4-5 / 6+ :', board['depth'])
    print('[방문 차수] 처음 / 2 / 3-5 / 6-10 / 11+ :', board['visitno'])
    wd = '월화수목금토일'
    hh = sorted(board['heat'], key=lambda x: -x[2])[:6]
    print('[많이 오는 시각 KST] ' + ', '.join(f'{wd[x[0] - 1]} {x[1]}시 {x[2]}' for x in hh))
    ev = [e for e in board['events'] if e['n0'] == 'game_end']
    print('[게임 플레이] ' + ', '.join(f'{e["g"]} {e["n"]}' for e in ev[:12]))

    print(f'\n[최근 방문 {len(ses["rows"])} / {ses["total"]}]')
    for r in ses['rows']:
        path = ' > '.join(x['p'] for x in r['pv'][:5]) + (' …' if len(r['pv']) > 5 else '')
        plays = sum(1 for e in r['ev'] if e['n'] == 'game_end')
        print(f'  {kst(r["t0"])} {r["country"] or "??"} {r["city"] or "":<12} {DEV.get(r["dev"], r["dev"] or ""):<3} '
              f'{r["src"] or "-":<12} {dur(r["dur"]):>9} {"신규" if r["nw"] else str(r["vn"]) + "회차"} '
              f'{"🎮" + str(plays) if plays else ""}  {path}')
    if len(days) >= 2:
        print('\n[일별 방문자] ' + ' '.join(f'{x["day"][5:]}:{x["visitors"]}' for x in days[-30:]))


if __name__ == '__main__':
    main()
