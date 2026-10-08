"""델타-브이 사가 원고(docs/deltav_saga/*.md) → 한 장짜리 읽기용 HTML.

    python scripts/build_saga_reader.py <출력.html>

- 장마다 본문과 '작가 노트·게임 대응'(부록)을 나눠, 부록은 접어 둔다
- 설정집(00_SERIES_BIBLE.md)은 맨 뒤 '설정집' 장으로
- 외부 라이브러리 없이 필요한 마크다운만 변환(제목·인용·표·목록·굵게·기울임·코드·가로줄)
- 원고를 고치거나 장을 추가하면 다시 돌려 같은 Artifact 로 재배포한다
"""
import html, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / 'docs' / 'deltav_saga'


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])', r'<em>\1</em>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', t)          # 저장소 상대 링크는 글자만 남긴다
    return t


def md_to_html(md):
    lines = md.split('\n')
    out, i = [], 0
    para = []

    def flush():
        if para:
            out.append('<p>' + '<br>'.join(inline(x) for x in para) + '</p>')
            para.clear()

    while i < len(lines):
        ln = lines[i].rstrip()
        s = ln.strip()
        if not s:
            flush(); i += 1; continue
        if s.startswith('```'):
            flush(); j = i + 1; buf = []
            while j < len(lines) and not lines[j].strip().startswith('```'):
                buf.append(html.escape(lines[j])); j += 1
            out.append('<pre><code>' + '\n'.join(buf) + '</code></pre>'); i = j + 1; continue
        m = re.match(r'^(#{1,4})\s+(.*)$', s)
        if m:
            flush(); n = len(m.group(1))
            out.append(f'<h{n+1}>{inline(m.group(2))}</h{n+1}>'); i += 1; continue
        if re.match(r'^-{3,}$', s):
            flush(); out.append('<hr>'); i += 1; continue
        if s.startswith('>'):
            flush(); buf = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip()[1:].strip()); i += 1
            body = md_to_html('\n'.join(buf))
            out.append('<blockquote>' + body + '</blockquote>'); continue
        if s.startswith('|'):
            flush(); rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i].strip()); i += 1
            cells = [[c.strip() for c in r.strip('|').split('|')] for r in rows]
            if len(cells) > 1 and all(re.match(r'^:?-+:?$', c) for c in cells[1] if c):
                head, body = cells[0], cells[2:]
            else:
                head, body = None, cells
            t = ['<div class="tw"><table>']
            if head:
                t.append('<thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead>')
            t.append('<tbody>' + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in body) + '</tbody></table></div>')
            out.append(''.join(t)); continue
        if re.match(r'^(\s*)([-*]|\d+\.)\s+', ln):
            flush(); ordered = bool(re.match(r'^\s*\d+\.', ln)); buf = []
            while i < len(lines) and re.match(r'^(\s*)([-*]|\d+\.)\s+', lines[i]):
                item = re.sub(r'^(\s*)([-*]|\d+\.)\s+', '', lines[i]); depth = len(lines[i]) - len(lines[i].lstrip())
                buf.append(f'<li class="d{min(depth // 2, 3)}">{inline(item)}</li>'); i += 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(buf) + f'</{tag}>'); continue
        para.append(s); i += 1
    flush()
    return '\n'.join(out)


def chapter(path):
    md = path.read_text(encoding='utf-8')
    main, _, notes = md.partition('\n## 작가 노트')
    if notes:
        notes = '## 작가 노트' + notes
    # 권 머리(# 제1권 …)와 장 제목(# 제N장 …)
    titles = re.findall(r'^#\s+(.+)$', main, re.M)
    return titles, md_to_html(main), md_to_html(notes) if notes else ''


def main(outp):
    files = sorted(p for p in ROOT.glob('*.md') if not p.name.startswith('00_'))
    chs = []
    for p in files:
        titles, body, notes = chapter(p)
        name = titles[-1] if titles else p.stem
        book = next((t for t in titles if t.startswith('제') and '권' in t and '장' not in t), '')
        chs.append({'id': p.stem.split('_', 1)[1].replace('_', '-'), 'title': name, 'book': book, 'body': body, 'notes': notes,
                    'chars': len(re.sub(r'\s', '', re.sub(r'<[^>]+>', '', body)))})
    bible = md_to_html((ROOT / '00_SERIES_BIBLE.md').read_text(encoding='utf-8'))
    chs.append({'id': 'bible', 'title': '설정집', 'book': '부록', 'body': bible, 'notes': '', 'chars': 0})

    toc, secs = [], []
    cur_book = None
    for k, c in enumerate(chs):
        if c['book'] and c['book'] != cur_book:
            cur_book = c['book']
            toc.append(f'<li class="tb">{inline(cur_book.replace("# ", ""))}</li>')
        mins = round(c['chars'] / 500) if c['chars'] else 0
        meta = f'<span>{mins}분</span>' if mins else ''
        toc.append(f'<li><a href="#{c["id"]}" data-i="{k}">{inline(c["title"])}{meta}</a></li>')
        notes = (f'<details class="notes"><summary>작가 노트 · 게임 대응</summary>{c["notes"]}</details>' if c['notes'] else '')
        secs.append(f'<article class="ch" id="{c["id"]}" data-i="{k}" data-t="{html.escape(re.sub(r"[*`]", "", c["title"]))}" hidden>{c["body"]}{notes}</article>')

    tpl = (pathlib.Path(__file__).parent / 'saga_reader_template.html').read_text(encoding='utf-8')
    page = tpl.replace('<!--TOC-->', '\n'.join(toc)).replace('<!--CHAPTERS-->', '\n'.join(secs))
    pathlib.Path(outp).write_text(page, encoding='utf-8')
    print('ok', outp, len(page), 'bytes,', len(chs), 'sections')


if __name__ == '__main__':
    main(sys.argv[1])
