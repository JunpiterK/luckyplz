#!/usr/bin/env python3
"""
Quiz CSV importer: data/quiz/<lang>/<category>.csv → Supabase

Usage:
  python scripts/import_quiz.py ko/kpop.csv
  python scripts/import_quiz.py --clear ko/kpop.csv    # DB에서 해당 카테고리 먼저 삭제 후 삽입
  python scripts/import_quiz.py --dry-run ko/kpop.csv  # 검증만, DB 변경 없음
  python scripts/import_quiz.py ko/*.csv               # 전체 한국어 카테고리 한번에

CSV 형식 (첫 줄은 헤더):
  question,opt1,opt2,opt3,opt4,answer,era,difficulty,hint
  - answer: opt1~opt4 중 정답 텍스트와 정확히 일치해야 함
  - era: classic | modern | current (생략 시 modern)
  - difficulty: 1~5 (생략 시 2)
  - hint: 정답 힌트 (생략 가능)

인증:
  1. 환경변수 SUPABASE_SERVICE_KEY
  2. 프로젝트 루트 .env 파일의 SUPABASE_SERVICE_KEY=...
"""

import csv
import json
import os
import sys
import argparse
import urllib.request
import urllib.error

SUPABASE_URL = 'https://jkrpxijybuljdxkrbsan.supabase.co'
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'quiz')
VALID_ERAS = {'classic', 'modern', 'current'}
VALID_CATEGORIES = {'kpop', 'variety', 'sports', 'general', 'retro', 'latest', 'history', 'world', 'nonsense'}
VALID_LANGS = {'ko', 'en', 'ja', 'zh', 'es', 'de', 'fr', 'pt', 'ru', 'ar', 'hi', 'th', 'id', 'vi', 'tr', 'gb'}


def load_service_key():
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    if key:
        return key
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('SUPABASE_SERVICE_KEY=') and not line.startswith('#'):
                    return line.split('=', 1)[1].strip().strip('"\'')
    return None


def api(method, endpoint, key, body=None, params=None):
    url = f'{SUPABASE_URL}/rest/v1/{endpoint}'
    if params:
        url += '?' + '&'.join(f'{k}={v}' for k, v in params.items())
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
    }
    data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'HTTP {e.code}: {e.read().decode("utf-8", errors="replace")}')


def parse_csv(filepath):
    rows, errors = [], 0
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for line_num, r in enumerate(reader, start=2):
            q = r.get('question', '').strip()
            opts = [r.get(f'opt{i}', '').strip() for i in range(1, 5)]
            answer = r.get('answer', '').strip()
            era = r.get('era', '').strip() or 'modern'
            raw_diff = r.get('difficulty', '').strip() or '2'
            hint = r.get('hint', '').strip() or None

            bad = []
            if not q:
                bad.append('question 비어있음')
            if any(not o for o in opts):
                bad.append('opt 비어있음')
            if answer not in opts:
                bad.append(f'answer "{answer}" → opt에 없음')
            if era not in VALID_ERAS:
                bad.append(f'era "{era}" 잘못됨 (classic/modern/current)')
            try:
                diff = int(raw_diff)
                assert 1 <= diff <= 5
            except Exception:
                bad.append(f'difficulty "{raw_diff}" 잘못됨 (1~5)')
                diff = 2

            if bad:
                print(f'  [줄 {line_num}] SKIP — {", ".join(bad)}')
                print(f'           → {q[:60]}')
                errors += 1
                continue

            rows.append({
                'question': q,
                'options': opts,
                'correct': opts.index(answer),
                'era': era,
                'difficulty': diff,
                'hint': hint,
            })

    return rows, errors


def main():
    parser = argparse.ArgumentParser(description='Quiz CSV → Supabase 임포터')
    parser.add_argument('files', nargs='+', help='CSV 파일 경로 (data/quiz/ 기준 상대경로)')
    parser.add_argument('--clear', action='store_true',
                        help='삽입 전 해당 language+category 기존 행 삭제')
    parser.add_argument('--dry-run', action='store_true',
                        help='검증만 하고 DB 변경 없음')
    args = parser.parse_args()

    key = None
    if not args.dry_run:
        key = load_service_key()
        if not key:
            print('오류: SUPABASE_SERVICE_KEY를 찾을 수 없습니다.')
            print('  환경변수로 설정하거나 .env 파일에 SUPABASE_SERVICE_KEY=... 추가하세요.')
            sys.exit(1)

    total_inserted = 0
    total_skipped = 0

    for rel_path in args.files:
        # 절대경로이거나 data/quiz/ 내 상대경로
        if os.path.isabs(rel_path):
            filepath = rel_path
            rel_to_data = os.path.relpath(filepath, DATA_DIR)
        else:
            filepath = os.path.join(DATA_DIR, rel_path)
            rel_to_data = rel_path

        if not os.path.exists(filepath):
            print(f'\n파일 없음: {filepath}')
            continue

        # 경로에서 lang/category 추출: ko/kpop.csv → lang=ko, category=kpop
        parts = rel_to_data.replace('\\', '/').split('/')
        if len(parts) < 2:
            print(f'\n경로 형식 오류 "{rel_path}": ko/kpop.csv 형식으로 지정하세요.')
            continue

        lang = parts[-2]
        category = os.path.splitext(parts[-1])[0]

        if lang not in VALID_LANGS:
            print(f'\n지원하지 않는 언어: "{lang}"')
            continue
        if category not in VALID_CATEGORIES:
            print(f'\n지원하지 않는 카테고리: "{category}"')
            print(f'  사용 가능: {", ".join(sorted(VALID_CATEGORIES))}')
            continue

        print(f'\n{"="*55}')
        print(f'파일  : {rel_path}')
        print(f'대상  : language={lang}  category={category}')
        print(f'{"="*55}')

        rows, skip_count = parse_csv(filepath)
        total_skipped += skip_count
        print(f'파싱  : 유효 {len(rows)}행  /  건너뜀 {skip_count}행')

        if args.dry_run:
            print('→ dry-run 모드: DB 변경 없음')
            continue

        if args.clear and rows:
            print(f'삭제  : DB에서 {lang}/{category} 기존 행 삭제 중…')
            api('DELETE', 'quiz_questions', key, params={
                'category': f'eq.{category}',
                'language': f'eq.{lang}',
            })
            print('삭제  : 완료')

        if not rows:
            print('→ 삽입할 행 없음')
            continue

        insert_rows = [{**r, 'category': category, 'language': lang} for r in rows]
        api('POST', 'quiz_questions', key, body=insert_rows)
        print(f'삽입  : {len(insert_rows)}행 완료')
        total_inserted += len(insert_rows)

    print(f'\n{"="*55}')
    print(f'완료  : 삽입 {total_inserted}행  /  건너뜀 {total_skipped}행')


if __name__ == '__main__':
    main()
