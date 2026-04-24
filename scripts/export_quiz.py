#!/usr/bin/env python3
"""
Supabase quiz_questions → CSV 추출기
data/quiz/<lang>/<category>.csv 파일로 저장 (기존 파일 덮어쓰기)

Usage:
  python scripts/export_quiz.py              # 전체 추출 (ko + en)
  python scripts/export_quiz.py ko           # 한국어만
  python scripts/export_quiz.py ko kpop      # 특정 언어+카테고리만

인증: .env 파일의 SUPABASE_SERVICE_KEY 또는 환경변수
"""

import csv
import json
import os
import sys
import urllib.request
import urllib.error

SUPABASE_URL = 'https://jkrpxijybuljdxkrbsan.supabase.co'
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'quiz')
CATEGORIES = ['kpop', 'variety', 'sports', 'general', 'retro', 'latest', 'history', 'world', 'nonsense']
LANGUAGES = ['ko', 'en']


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


def fetch_questions(key, lang, category):
    url = (f'{SUPABASE_URL}/rest/v1/quiz_questions'
           f'?category=eq.{category}&language=eq.{lang}'
           f'&select=question,options,correct,era,difficulty,hint'
           f'&order=id.asc&limit=10000')
    req = urllib.request.Request(url, headers={
        'apikey': key,
        'Authorization': f'Bearer {key}',
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'HTTP {e.code}: {e.read().decode("utf-8", errors="replace")}')


def write_csv(rows, lang, category):
    folder = os.path.join(DATA_DIR, lang)
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f'{category}.csv')
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['question', 'opt1', 'opt2', 'opt3', 'opt4', 'answer', 'era', 'difficulty', 'hint'])
        for r in rows:
            opts = r['options']
            correct_idx = r['correct']
            answer = opts[correct_idx] if 0 <= correct_idx < len(opts) else ''
            writer.writerow([
                r['question'],
                opts[0] if len(opts) > 0 else '',
                opts[1] if len(opts) > 1 else '',
                opts[2] if len(opts) > 2 else '',
                opts[3] if len(opts) > 3 else '',
                answer,
                r.get('era', 'modern') or 'modern',
                r.get('difficulty', 2) or 2,
                r.get('hint', '') or '',
            ])
    return filepath


def main():
    args = sys.argv[1:]
    target_langs = [args[0]] if len(args) >= 1 else LANGUAGES
    target_cats = [args[1]] if len(args) >= 2 else CATEGORIES

    key = load_service_key()
    if not key:
        print('오류: SUPABASE_SERVICE_KEY를 찾을 수 없습니다.')
        print('  .env 파일에 SUPABASE_SERVICE_KEY=<서비스롤키> 추가하세요.')
        sys.exit(1)

    total = 0
    for lang in target_langs:
        for cat in target_cats:
            rows = fetch_questions(key, lang, cat)
            if not rows:
                continue
            filepath = write_csv(rows, lang, cat)
            print(f'✓  {lang}/{cat}.csv  ({len(rows)}행)')
            total += len(rows)

    print(f'\n완료: 총 {total}행 추출')


if __name__ == '__main__':
    main()
