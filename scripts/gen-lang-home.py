# -*- coding: utf-8 -*-
"""언어 경로 홈페이지 생성기 — /ko/ /ja/ /es/ /pt/

왜 필요한가 (2026-08-19):
    이전에는 16개 언어를 `?lang=xx` 쿼리로 hreflang 선언했는데, canonical
    이 쿼리 없는 URL 을 가리켜 구글이 alternate 를 전부 무시했다. 즉
    16개 언어 전부 SEO 가치 0. 실제 경로 페이지를 만들어 canonical 을
    self-referential 로 두고 hreflang 을 상호 선언해야 값이 생긴다.

왜 5개만인가:
    도달 가능성 × 국가별 RPM 기준. 중국어는 본토에서 구글이 차단돼
    구글 SEO 로 도달이 안 되고, 힌디어권은 유틸리티 도구를 영어로
    검색한다. 나머지 11개 언어는 UI 로는 그대로 쓸 수 있고 hreflang
    에서만 빠진다.

멱등:
    public/index.html 을 원본으로 매번 다시 생성한다. 홈을 고치면
    이 스크립트를 다시 돌려야 언어판이 따라온다.

    python scripts/gen-lang-home.py
"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lp_clusters import CLUSTERS, member  # noqa: E402

SRC = ROOT / "public" / "index.html"

# hreflang 상호 선언 세트 (전 언어판 공통)
HREFLANG = """    <link rel="alternate" hreflang="en" href="https://luckyplz.com/">
    <link rel="alternate" hreflang="es" href="https://luckyplz.com/es/">
    <link rel="alternate" hreflang="pt" href="https://luckyplz.com/pt/">
    <link rel="alternate" hreflang="ja" href="https://luckyplz.com/ja/">
    <link rel="alternate" hreflang="ko" href="https://luckyplz.com/ko/">
    <link rel="alternate" hreflang="x-default" href="https://luckyplz.com/">"""

LANGS = {}

# ─────────────────────────────────────────────────────────── 한국어
LANGS["ko"] = dict(
    html_lang="ko",
    og_locale="ko_KR",
    title="무료 룰렛 돌리기 · 팀 나누기 · 주사위 | Lucky Please",
    description="가입 없이 바로 쓰는 랜덤 뽑기 6종 — 룰렛, 팀 나누기, 주사위, 빙고, 랜덤 레이스, 사다리타기. 결과는 1탭으로 공유. 모바일·PC 모두 지원.",
    keywords="룰렛 돌리기, 랜덤 뽑기, 팀 나누기, 사다리타기, 주사위 굴리기, 빙고 번호 추첨, 랜덤 이름 뽑기, 순서 정하기, 벌칙 정하기, 무료 결정 도구",
    og_title="Lucky Please — 무료 룰렛·팀 나누기·주사위",
    og_desc="가입 없이 바로 쓰는 랜덤 뽑기 6종. 결과는 1탭 공유.",
    prose="""            <p class="lp-lead">여럿이 정해야 하는데 아무도 나서기 싫을 때 쓰는 랜덤 뽑기 6종. 돌리고, 나누고, 굴리고, 뽑고, 달리고, 사다리 타고 &mdash; 같은 화면을 다 같이 보면 끝. 가입 없음.</p>

            <details class="lp-fold">
                <summary>정말 무작위인가</summary>
                <p>모든 추첨은 브라우저 자체의 난수 생성기를 씁니다. 가중치도 없고 미리 정해진 결과도 없습니다. 항목이 <i>n</i>개면 매번 각자 1/<i>n</i>입니다.</p>
                <p>추첨끼리 독립이라 한 번 뽑혔다고 다음 확률이 낮아지지 않습니다. 6명이면 같은 사람이 두 번 연속 걸릴 확률이 약 36분의 1 &mdash; 한 자리에서 누군가에겐 일어납니다. 뽑힌 사람을 빼려면 다시 돌리기 전에 목록에서 지우세요.</p>
            </details>

            <details class="lp-fold">
                <summary>왜 굳이 돌아가는 걸 보나</summary>
                <p>난수 한 줄이면 같은 일을 하는데, 누구도 그걸로 "누가 낼지"를 정하지 않습니다. 이유는 사회적입니다. 결정은 목격되어야 합니다. 모두가 같은 룰렛이 느려지는 걸 함께 본 순간, 결과는 사람이 아니라 절차의 것이 됩니다.</p>
            </details>""",
    faq=[
        ("무료인가요?",
         "네. 6종 전부 무료이고 가입도 설치도 없습니다. 광고가 나가는 경우에도 결과 화면과 홈 하단에만 노출되며, 추첨 중에는 절대 나오지 않습니다."),
        ("결과가 정말 무작위인가요?",
         "네. 모든 추첨은 브라우저 자체의 난수 생성기를 호출합니다. 룰렛 위 위치나 사다리 줄, 출발선 어디에 있든 확률은 같습니다. 가중치도 없고 미리 정해진 결과도 없습니다."),
        ("가입해야 하나요?",
         "아니요. 모든 도구가 로그인 없이 바로 실행됩니다. 계정은 기기 간 그룹 저장이나 멀티플레이 같은 부가 기능에만 쓰입니다."),
        ("폰에서도 잘 되나요?",
         "네. 모든 도구가 세로 폰 화면 기준으로 만들어졌고 태블릿·데스크탑으로 확장됩니다. 식탁에서 폰 하나를 돌려 쓰거나 교실 프로젝터에 같은 페이지를 띄워도 됩니다."),
        ("결과를 친구에게 공유할 수 있나요?",
         "네. 추첨이 끝나면 1탭 공유 링크가 생깁니다. 링크를 연 사람은 정확히 같은 결과를 보게 되고, 그래서 결과를 두고 다투기 어려워집니다."),
        ("몇 개 언어를 지원하나요?",
         "인터페이스는 16개 언어를 지원합니다. 그중 영어·스페인어·포르투갈어·일본어·한국어는 전용 페이지가 있는 정식 지원 언어이고, 나머지 11개는 인터페이스 번역만 제공됩니다."),
    ],
)

# ─────────────────────────────────────────────────────────── 日本語
LANGS["ja"] = dict(
    html_lang="ja",
    og_locale="ja_JP",
    title="無料ルーレット・チーム分け・サイコロ | Lucky Please",
    description="登録なしですぐ使えるランダム抽選ツール6種 — ルーレット、チーム分け、サイコロ、ビンゴ、ランダムレース、あみだくじ。結果はワンタップで共有。スマホ・PC対応。",
    keywords="ルーレット 無料, ランダム 抽選, チーム分け ツール, あみだくじ, サイコロ 振る, ビンゴ 番号 抽選, 名前 ランダム, 順番 決め, 罰ゲーム 決め, 無料 決定ツール",
    og_title="Lucky Please — 無料ルーレット・チーム分け・サイコロ",
    og_desc="登録なしで使えるランダム抽選6種。結果はワンタップ共有。",
    prose="""            <p class="lp-lead">みんなで決めたいけれど誰も決めたくないときのランダム抽選6種。回す・分ける・振る・引く・走らせる・たどる &mdash; 同じ画面を全員で見れば終わり。登録不要。</p>

            <details class="lp-fold">
                <summary>本当にランダムか</summary>
                <p>すべての抽選はブラウザ自身の乱数生成器を使います。重み付けも事前に決まった結果もありません。項目が <i>n</i> 個なら毎回それぞれ 1/<i>n</i> です。</p>
                <p>各回は独立なので、一度選ばれても次の確率は下がりません。6人なら同じ人が2回続く確率は約36分の1 &mdash; 一晩あれば誰かに起こります。選ばれた人を外すには、回す前に名前を消してください。</p>
            </details>

            <details class="lp-fold">
                <summary>なぜ回るところを見るのか</summary>
                <p>乱数一行で同じことができるのに、誰もそれで「誰がおごるか」を決めません。理由は社会的です。決定は目撃されなければなりません。全員が同じルーレットの減速を見た時点で、結果は人ではなく手続きのものになります。</p>
            </details>""",
    faq=[
        ("無料ですか？",
         "はい。6種すべて無料で、登録もインストールも不要です。広告が出る場合も結果画面とホーム下部のみで、抽選中には絶対に出ません。"),
        ("結果は本当にランダムですか？",
         "はい。すべての抽選はブラウザ自身の乱数生成器を呼び出します。ルーレット上の位置でも、あみだの線でも、スタートラインのどこにいても確率は同じです。重み付けも事前に決まった結果もありません。"),
        ("アカウントは必要ですか？",
         "いいえ。すべてのツールがログインなしですぐ動きます。アカウントは端末間のグループ保存やマルチプレイなど任意の追加機能にのみ使われます。"),
        ("スマホでも動きますか？",
         "はい。すべてのツールが縦向きスマホを基準に作られ、タブレットやデスクトップに拡張されます。食卓でスマホを回しても、教室のプロジェクターに同じページを映しても構いません。"),
        ("結果を友達に共有できますか？",
         "はい。抽選が終わるとワンタップの共有リンクが出ます。リンクを開いた人は全く同じ結果を見るので、結果について揉めにくくなります。"),
        ("何か国語に対応していますか？",
         "インターフェースは16言語に対応しています。うち英語・スペイン語・ポルトガル語・日本語・韓国語は専用ページを持つ正式対応言語で、残る11言語はインターフェース翻訳のみです。"),
    ],
)

# ─────────────────────────────────────────────────────────── Español
LANGS["es"] = dict(
    html_lang="es",
    og_locale="es_ES",
    title="Ruleta, Sorteo de Equipos y Dados Gratis | Lucky Please",
    description="Seis sorteos aleatorios gratis: ruleta de nombres, generador de equipos, dados, bingo, carrera aleatoria y escalera. Sin registro, funciona en cualquier móvil y se comparte con un toque.",
    keywords="ruleta de nombres, ruleta aleatoria, sorteo de equipos, generador de equipos, tirar dados online, bingo online, sorteo aleatorio gratis, elegir al azar, quien paga, decidir al azar",
    og_title="Lucky Please — Ruleta, Equipos y Dados Gratis",
    og_desc="Seis sorteos aleatorios gratis. Sin registro, se comparte con un toque.",
    prose="""            <p class="lp-lead">Seis sorteos aleatorios para grupos. Gira, divide, tira, canta, corre o sortea &mdash; y ense&ntilde;a a todos la misma pantalla. Sin registro.</p>

            <details class="lp-fold">
                <summary>&iquest;Es realmente aleatorio?</summary>
                <p>Cada sorteo usa el generador de n&uacute;meros aleatorios del navegador. Nada est&aacute; ponderado y ning&uacute;n resultado se elige de antemano. Con <i>n</i> entradas, cada una tiene 1/<i>n</i> cada vez.</p>
                <p>Los sorteos son independientes: salir una vez no baja tu probabilidad la siguiente. Con seis personas, que le toque dos veces seguidas a la misma ocurre 1 de cada 36 &mdash; suficiente para que le pase a alguien. Para que quien sali&oacute; deje de participar, b&oacute;rralo antes de volver a girar.</p>
            </details>

            <details class="lp-fold">
                <summary>&iquest;Por qu&eacute; mirar el sorteo?</summary>
                <p>Un generador de una l&iacute;nea har&iacute;a lo mismo, y nadie lo usa para decidir qui&eacute;n paga. El motivo es social: la decisi&oacute;n tiene que ser presenciada. Cuando todos han visto frenar la misma ruleta, el resultado pertenece al procedimiento y no a una persona.</p>
            </details>""",
    faq=[
        ("¿Son gratis los sorteos?",
         "Sí. Los seis son gratuitos, sin registro y sin instalación. Cuando hay publicidad, aparece solo en las pantallas de resultado y al final de la página de inicio, nunca durante un sorteo."),
        ("¿El resultado es realmente aleatorio?",
         "Sí. Cada sorteo llama al generador de números aleatorios del propio navegador, así que todas las entradas tienen la misma probabilidad sin importar su posición en la ruleta, en la escalera o en la línea de salida. Nada está ponderado ni preseleccionado."),
        ("¿Necesito una cuenta?",
         "No. Todos los sorteos funcionan al instante sin iniciar sesión. La cuenta solo existe para extras opcionales como guardar grupos entre dispositivos y las salas multijugador."),
        ("¿Funciona en el móvil?",
         "Sí. Todo está diseñado primero para pantalla de móvil en vertical y escala a tabletas y ordenadores, así que puedes pasar un móvil por la mesa o poner la misma página en un proyector."),
        ("¿Puedo compartir el resultado?",
         "Sí. Después de un sorteo obtienes un enlace para compartir con un toque. Quien lo abra verá exactamente el mismo resultado, que es justo lo que hace difícil discutirlo."),
        ("¿Qué idiomas están disponibles?",
         "La interfaz está en 16 idiomas. Inglés, español, portugués, japonés y coreano son los idiomas con página propia y soporte completo; los 11 restantes tienen la interfaz traducida pero no páginas de búsqueda propias."),
    ],
)

# ─────────────────────────────────────────────────────────── Português
LANGS["pt"] = dict(
    html_lang="pt",
    og_locale="pt_BR",
    title="Roleta, Sorteio de Times e Dados Grátis | Lucky Please",
    description="Seis sorteios aleatórios grátis: roleta de nomes, sorteio de times, dados, bingo, corrida aleatória e escada. Sem cadastro, funciona em qualquer celular e compartilha com um toque.",
    keywords="roleta de nomes, sorteio aleatorio, sortear nomes, sorteio de times, rolar dados online, bingo online gratis, sorteador de nomes, escolher aleatoriamente, quem paga a conta, decidir no sorteio",
    og_title="Lucky Please — Roleta, Times e Dados Grátis",
    og_desc="Seis sorteios aleatórios grátis. Sem cadastro, compartilha com um toque.",
    prose="""            <p class="lp-lead">Seis sorteios aleat&oacute;rios para grupos. Gire, divida, role, cante, corra ou sorteie &mdash; e mostre a mesma tela para todos. Sem cadastro.</p>

            <details class="lp-fold">
                <summary>&Eacute; mesmo aleat&oacute;rio?</summary>
                <p>Cada sorteio usa o gerador de n&uacute;meros aleat&oacute;rios do navegador. Nada tem peso e nenhum resultado &eacute; escolhido antes. Com <i>n</i> entradas, cada uma tem 1/<i>n</i> a cada vez.</p>
                <p>Os sorteios s&atilde;o independentes: sair uma vez n&atilde;o diminui sua chance na pr&oacute;xima. Com seis pessoas, a mesma sair duas vezes seguidas acontece 1 vez em 36 &mdash; o bastante para acontecer com algu&eacute;m. Para tirar quem j&aacute; saiu, apague o nome antes de girar de novo.</p>
            </details>

            <details class="lp-fold">
                <summary>Por que assistir ao sorteio?</summary>
                <p>Um gerador de uma linha faria o mesmo, e ningu&eacute;m usa isso para decidir quem paga. O motivo &eacute; social: a decis&atilde;o precisa ser testemunhada. Quando todos viram a mesma roleta desacelerar, o resultado passa a pertencer ao procedimento, n&atilde;o a uma pessoa.</p>
            </details>""",
    faq=[
        ("Os sorteios são grátis?",
         "Sim. Os seis são gratuitos, sem cadastro e sem instalação. Quando há anúncios, eles aparecem apenas nas telas de resultado e no rodapé da página inicial, nunca durante um sorteio."),
        ("O resultado é realmente aleatório?",
         "Sim. Cada sorteio chama o gerador de números aleatórios do próprio navegador, então toda entrada tem a mesma chance, não importa a posição na roleta, na escada ou na linha de largada. Nada tem peso nem é pré-selecionado."),
        ("Preciso de uma conta?",
         "Não. Todos os sorteios rodam na hora sem login. A conta existe apenas para extras opcionais, como salvar grupos entre dispositivos e salas multijogador."),
        ("Funciona no celular?",
         "Sim. Tudo é feito primeiro para tela de celular na vertical e escala para tablets e computadores, então você pode passar um celular pela mesa ou colocar a mesma página em um projetor."),
        ("Posso compartilhar o resultado?",
         "Sim. Depois de um sorteio você recebe um link de compartilhamento de um toque. Quem abrir vê exatamente o mesmo resultado, que é justamente o que torna difícil contestar."),
        ("Quais idiomas estão disponíveis?",
         "A interface está em 16 idiomas. Inglês, espanhol, português, japonês e coreano são os idiomas com página própria e suporte completo; os 11 restantes têm a interface traduzida, mas não páginas de busca próprias."),
    ],
)


# ---------------------------------------------------------------- 도구 링크
# 랜딩 6종이 서로만 링크하고 있어 홈에서 들어가는 경로가 0이었다. 사이트맵에만
# 있고 내부 링크가 없는 페이지는 크롤 우선순위가 낮고 홈의 링크 가치도 못 받는다.
# 게임 카드는 게임 본체를 그대로 가리키고(도구 사이트에서 클릭을 늘리면 안 된다),
# 링크는 본문 안 텍스트 링크로 따로 둔다.
LINKS_HEAD = {
    "ko": "어떤 걸 언제 쓰나",
    "ja": "どれをいつ使うか",
    "es": "Cuál usar y cuándo",
    "pt": "Qual usar e quando",
}

# ko 는 클러스터의 ko 멤버가 게임 본체라 별도 랜딩이 없다. 이름·설명을 직접 둔다.
KO_LINKS = [
    ("roulette", "룰렛", "이름을 넣고 돌리면 하나가 뽑힙니다."),
    ("team", "팀 나누기", "명단을 붙여 넣으면 인원이 고른 팀으로 나뉩니다."),
    ("dice", "주사위", "1~6개를 실제로 굴립니다."),
    ("bingo", "빙고", "중복 없이 번호를 뽑고 호출 목록을 남깁니다."),
    ("car-racing", "랜덤 레이스", "추첨 결과를 레이스로 보여줘 전체 순위가 나옵니다."),
    ("ladder", "사다리타기", "경로가 공개되기 전에 각자 선을 고릅니다."),
]


def _landing_content(code):
    path = HERE / ("landing_content_%s.py" % code)
    spec = importlib.util.spec_from_file_location("lc_" + code, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.CONTENT


def links_block(code):
    rows = []
    if code == "ko":
        for tool, name, desc in KO_LINKS:
            rows.append('                <li><a href="%s">%s</a> &mdash; %s</li>'
                        % (CLUSTERS[tool]["game"], name, desc))
    else:
        for tool, cfg in _landing_content(code).items():
            rows.append('                <li><a href="%s">%s</a> &mdash; %s</li>'
                        % (member(tool, code), cfg["h1"], cfg["short"]))
    body = "\n".join(rows)
    return ('\n            <details class="lp-fold">\n                <summary>'
            + LINKS_HEAD[code] + "</summary>\n"
            '                <ul class="lp-seo-links">\n' + body
            + "\n                </ul>\n            </details>\n")


def esc(t):
    return t.replace("\\", "\\\\").replace('"', '\\"')


def build(code, cfg, src):
    s = src

    # <html lang>
    s = s.replace('<html lang="en">', '<html lang="%s">' % cfg["html_lang"], 1)

    # title / description / keywords
    s = re.sub(r"<title>.*?</title>", "<title>%s</title>" % cfg["title"], s, count=1, flags=re.S)
    s = re.sub(r'<meta name="description" content="[^"]*">',
               '<meta name="description" content="%s">' % cfg["description"], s, count=1)
    s = re.sub(r'<meta name="keywords" content="[^"]*">',
               '<meta name="keywords" content="%s">' % cfg["keywords"], s, count=1)

    # canonical (self-referential) + og:url
    s = s.replace('<link rel="canonical" href="https://luckyplz.com/">',
                  '<link rel="canonical" href="https://luckyplz.com/%s/">' % code, 1)
    s = s.replace('<meta property="og:url" content="https://luckyplz.com/">',
                  '<meta property="og:url" content="https://luckyplz.com/%s/">' % code, 1)

    # hreflang 블록 교체 (원본과 동일하지만 명시적으로 다시 씀)
    hl_start = s.index('    <link rel="alternate" hreflang="en" href="https://luckyplz.com/">')
    hl_end = s.index('hreflang="x-default" href="https://luckyplz.com/">') + len('hreflang="x-default" href="https://luckyplz.com/">')
    s = s[:hl_start] + HREFLANG + s[hl_end:]

    # og:title / og:description / og:locale
    s = re.sub(r'<meta property="og:title" content="[^"]*">',
               '<meta property="og:title" content="%s">' % cfg["og_title"], s, count=1)
    s = re.sub(r'<meta property="og:description" content="[^"]*">',
               '<meta property="og:description" content="%s">' % cfg["og_desc"], s, count=1)
    s = s.replace('<meta property="og:type" content="website">',
                  '<meta property="og:type" content="website">\n    <meta property="og:locale" content="%s">' % cfg["og_locale"], 1)

    # FAQPage 스키마는 여기서 쓰지 않는다. 이 스크립트는 **화면**만 만들고,
    # 스키마는 scripts/sync-faq-schema.py 가 그 화면을 읽어 생성한다.
    # 두 곳에서 각자 만들면 문구가 갈라지고, 그게 정확히 2026-08-19에
    # 영어 랜딩 3종에서 터진 문제다. 생성 순서:
    #     python scripts/gen-lang-home.py && python scripts/sync-faq-schema.py

    # 가시 콘텐츠 교체
    sec_start = s.index('        <section class="lp-home-seo"')
    sec_end = s.index("</section>", sec_start) + len("</section>")
    # 접히는 FAQ. sync-faq-schema.py 가 div.lp-faq-list 안만 읽어
    # 위쪽 lp-fold 블록과 섞이지 않는다.
    faq_dl = "\n".join(
        "                <details><summary>%s</summary><p>%s</p></details>" % (q, a)
        for q, a in cfg["faq"])
    faq_head = {"ko": "자주 묻는 질문", "ja": "よくある質問",
                "es": "Preguntas frecuentes", "pt": "Perguntas frequentes"}[code]
    new_sec = ('        <section class="lp-home-seo" lang="%s" aria-label="About Lucky Please">\n'
               "%s\n%s\n"
               '            <h2 class="lp-faq-h">%s</h2>\n'
               '            <div class="lp-faq-list">\n%s\n            </div>\n'
               "        </section>") % (cfg["html_lang"], cfg["prose"], links_block(code), faq_head, faq_dl)
    s = s[:sec_start] + new_sec + s[sec_end:]

    # 언어 강제 주입 — I18N/init 이 읽는다. 첫 <script> 앞이 아니라
    # </head> 직전이면 init() 보다 먼저 실행되므로 충분하다.
    s = s.replace("</head>",
                  "<script>window.__LP_FORCE_LANG=%r;</script>\n</head>" % code, 1)

    return s


def main():
    src = SRC.read_text(encoding="utf-8")
    for code, cfg in LANGS.items():
        out = ROOT / "public" / code / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        html = build(code, cfg, src)
        out.write_text(html, encoding="utf-8")
        txt = re.sub(r"<[^>]+>", " ", html[html.index('<section class="lp-home-seo"'):html.index("</section>", html.index('<section class="lp-home-seo"'))])
        print("%-3s -> %s  (가시 %d자)" % (code, out.relative_to(ROOT), len(re.sub(r"\s+", "", txt))))


if __name__ == "__main__":
    main()
