#!/usr/bin/env python3
"""라이브 퀴즈 문제 은행과 행사 세트 검사 — public/games/quiz/bank/

규칙(qlive_create 서버 검증 + 클라이언트 가정):
  · cat·q·o·c·h 필수. event 세트에는 difficulty(1~3) 필수, 검증 출처 source는 선택
  · 4지선다: 보기 4개·서로 다름·정답은 원본에서 항상 o[0](c=0) — 섞기는 방 만들 때 클라이언트가 한다
  · OX: 보기 2개가 그 은행의 OX 표기 그대로, c 는 0(참)·1(거짓)
  · 질문 중복 금지(대소문자·공백 무시) · cat 은 index.html CATSET 의 그 언어 목록 안
사용: python scripts/validate-quiz-banks.py   (오류가 있으면 종료 코드 1)
"""
import collections, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BANK = ROOT / 'public' / 'games' / 'quiz' / 'bank'
HTML = ROOT / 'public' / 'games' / 'quiz' / 'index.html'
OX = {'ko': ['O', 'X'], 'ja': ['O', 'X'], 'en': ['True', 'False'], 'es': ['Verdadero', 'Falso'], 'pt': ['Verdadeiro', 'Falso']}
OXRE = re.compile(r'^(O|X|True|False|Verdadero|Verdadeiro|Falso)$')


def catset():
    s = HTML.read_text(encoding='utf-8')
    m = re.search(r'const CATSET=\{(.*?)\};', s, re.S)
    out = {}
    for lang, body in re.findall(r"(\w+):\[([^\]]*)\]", m.group(1)):
        out[lang] = re.findall(r"'(\w+)'", body)
    return out


def main():
    cats = catset()
    bad = 0
    event_dir = BANK / 'event'
    missing_languages = {'ko', 'en', 'ja', 'zh', 'es', 'pt'} - {p.stem for p in event_dir.glob('*.json')}
    if missing_languages:
        print('ERROR missing event languages:', ', '.join(sorted(missing_languages)))
        bad += len(missing_languages)
    for p in sorted(BANK.rglob('*.json')):
        lang = p.stem
        event = p.parent == event_dir
        pack = p.relative_to(BANK).with_suffix('').as_posix()
        categories = cats.get(lang, cats['en'] if event else [])
        data = json.loads(p.read_text(encoding='utf-8'))
        errs, seen = [], {}
        for i, x in enumerate(data):
            tag = f'{pack}#{i + 1}'
            required = {'cat', 'q', 'o', 'c', 'h'}
            if event:
                required.add('difficulty')
            optional = {'source'} if event else set()
            if required - x.keys() or x.keys() - (required | optional):
                errs.append(f'{tag} keys {sorted(x)}'); continue
            if event and (type(x['difficulty']) is not int or x['difficulty'] not in (1, 2, 3)):
                errs.append(f'{tag} difficulty must be 1, 2 or 3')
            if 'source' in x and not re.fullmatch(r'https://[^/\s]+/\S+', x['source']):
                errs.append(f'{tag} invalid source URL')
            if x['cat'] not in categories:
                errs.append(f'{tag} unknown cat {x["cat"]}')
            if not x['q'].strip() or not x['h'].strip():
                errs.append(f'{tag} empty question or explanation')
            o = x['o']
            if len(set(o)) != len(o) or any(not str(v).strip() for v in o):
                errs.append(f'{tag} duplicate/empty option {o}')
            if x['cat'] == 'ox':
                if o != OX.get(lang) or x['c'] not in (0, 1):
                    errs.append(f'{tag} bad OX {o} c={x["c"]}')
            else:
                if len(o) != 4 or x['c'] != 0:
                    errs.append(f'{tag} MC needs 4 options and c=0: {o} c={x["c"]}')
                if len(o) == 2 and OXRE.match(o[0]):
                    errs.append(f'{tag} MC looks like OX')
            k = re.sub(r'\s+', ' ', x['q'].strip().lower())
            if k in seen:
                errs.append(f'{tag} duplicate question of #{seen[k]}: {x["q"]}')
            seen[k] = i + 1
            if len(x['q']) > 120 or max(len(v) for v in o) > 40:
                errs.append(f'{tag} too long')
        cnt = collections.Counter(x['cat'] for x in data)
        if event:
            stages = collections.Counter(x.get('difficulty') for x in data)
            details = 'stages ' + '/'.join(str(stages[n]) for n in (1, 2, 3))
            if len(data) < 30 or any(stages[n] == 0 for n in (1, 2, 3)):
                errs.append(f'{pack} must support a full 30-question game and all three stages')
        else:
            oxc = collections.Counter(x['c'] for x in data if x['cat'] == 'ox')
            details = f'OX true/false {oxc[0]}/{oxc[1]}'
            missing = [c for c in categories if not cnt[c]]
            if missing:
                errs.append(f'{lang} categories with no questions: {missing}')
        print(f'{pack}: {len(data)} items  ' + ' '.join(f'{c}={cnt[c]}' for c in categories if cnt[c]) +
              '  | ' + details)
        for e in errs:
            print('  ERROR', e)
        bad += len(errs)
    print('OK' if not bad else f'{bad} error(s)')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
