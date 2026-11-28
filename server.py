import os
import json
import re
import socket
from html import escape
from pathlib import Path
from flask import Flask, Response, request, send_from_directory, send_file

app = Flask(__name__)

PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
with (Path(__file__).parent / 'scripts/og-assets/home-share-locales.json').open(encoding='utf8') as f:
    SHARE_LOCALES = json.load(f)
COUNTRY_LANGUAGES = {country: code for code, data in SHARE_LOCALES.items() for country in data['countries']}


def share_language_code(value):
    tag = (value or '').strip().lower().replace('_', '-')
    if not re.fullmatch(r'[a-z]{2,3}(?:-[a-z0-9]{1,8})*', tag):
        return None
    if re.match(r'^en-(gb|uk)(-|$)', tag):
        return 'gb'
    primary = tag.split('-')[0]
    return primary if primary in SHARE_LOCALES else None


def home_share_language():
    """Local equivalent of the root Pages Function. CF-IPCountry simulates request.cf.country."""
    explicit = share_language_code(request.args.get('lang'))
    if explicit:
        return explicit
    excluded = set()
    for tag, quality in request.accept_languages:
        code = share_language_code(tag)
        if code and quality > 0:
            return code
        if code and quality == 0:
            excluded.add(code)
    agent = request.headers.get('User-Agent', '')
    if re.search(r'kakaotalk|kakaostory|kakaoscrap|kakaobot', agent, re.I):
        return 'en' if 'ko' in excluded else 'ko'
    if re.search(r'bot\b|crawler|spider|facebookexternalhit|meta-external|whatsapp|\bline(?:[-/ ]|$)|preview|unfurl', agent, re.I):
        return 'en'
    country_language = COUNTRY_LANGUAGES.get(request.headers.get('CF-IPCountry', ''))
    return country_language if country_language and country_language not in excluded else 'en'

@app.after_request
def no_cache(resp):
    # Local dev: never cache anything — avoids stale HTML/JS/SW issues
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/')
def index():
    code = home_share_language()
    data = SHARE_LOCALES[code]
    html = (Path(PUBLIC) / 'index.html').read_text(encoding='utf8')
    head, separator, body = html.partition('</head>')
    head = head.replace('<html ', '<html data-share-locale="' + code + '" ', 1)
    values = {
        'og:title': data['title'], 'twitter:title': data['title'],
        'og:image:alt': data['alt'], 'twitter:image:alt': data['alt'],
        'og:locale': data['locale'],
        'og:url': 'https://luckyplz.com' + data.get('path', '/?lang=' + code),
    }
    def replace_meta(match):
        opening, name, value = match.groups()
        return opening + (escape(values[name], quote=True) if name in values else value) + '"'
    head = re.sub(r'(<meta (?:property|name)="([^"]+)" content=")([^"]*)"', replace_meta, head)
    response = Response(head + separator + body, mimetype='text/html')
    response.vary.update(('Accept-Language', 'User-Agent', 'CF-IPCountry'))
    return response

@app.route('/u/<path:nickname>')
def user_profile(nickname):
    """Public profile vanity URL: /u/<nickname> → /u/index.html.
    Cloudflare Pages handles this via public/_redirects; the local
    Flask server needs an explicit route to mirror that behaviour."""
    return send_file(os.path.join(PUBLIC, 'u', 'index.html'))

@app.route('/r/<path:code>')
def room_invite(code):
    """Rooms v2 초대 링크 /r/<CODE>#k=... → /lobby/index.html (public/_redirects 의 200 rewrite 를 흉내)."""
    return send_file(os.path.join(PUBLIC, 'lobby', 'index.html'))

@app.route('/api/p', methods=['POST', 'GET'])
def stat_beacon():
    """방문 통계 비컨 — 운영에서는 functions/api/p.js (Pages Function) 가 받는다.
    로컬은 받은 내용만 찍고 204 (DB 로 보내지 않는다). ?lp_stat=1 로 켠다."""
    from flask import request
    print('[lp_stat]', request.get_data(as_text=True)[:600], flush=True)
    return '', 204

@app.route('/<path:path>')
def static_files(path):
    full = os.path.join(PUBLIC, path)
    # Directory -> serve index.html inside it
    if os.path.isdir(full):
        idx = os.path.join(full, 'index.html')
        if os.path.isfile(idx):
            return send_file(idx)
    # Regular file
    if os.path.isfile(full):
        return send_from_directory(PUBLIC, path)
    return 'Not Found', 404

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8080))
    local_ip = get_local_ip()

    print('=' * 56)
    print('  LuckyPlz - 행운은 나의 것!!')
    print('=' * 56)
    print(f'  Local:    http://localhost:{port}')
    print(f'  Network:  http://{local_ip}:{port}')
    print('-' * 56)
    print('  Same Wi-Fi/LAN users can access via the Network URL')
    print('  For external access, use port forwarding or ngrok')
    print('=' * 56)

    app.run(host=host, port=port, debug=False)
