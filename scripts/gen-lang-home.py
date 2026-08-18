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
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
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
    prose="""            <h2>한 번의 탭으로 끝나는 랜덤 뽑기</h2>
            <p>Lucky Please 는 여럿이 모여 무언가를 정해야 하는데 아무도 그 결정을 자기 이름으로 하고 싶지 않을 때 쓰는 도구 6종입니다. 룰렛을 돌리거나, 팀을 나누거나, 주사위를 굴리거나, 빙고 번호를 뽑거나, 레이스를 돌리거나, 사다리를 탑니다. 그리고 같은 화면을 모두에게 보여주면 끝입니다. 설치할 것도 가입할 것도 없고, 식탁에서 폰 하나를 돌려가며 쓰든 교실 프로젝터에 띄우든 똑같이 동작합니다.</p>

            <h3>어떤 상황에 어떤 도구를 쓰나</h3>
            <ul class="lp-seo-list">
                <li><b>룰렛</b> — 가장 범용적입니다. 이름이든 선택지든 넣고 돌리면 하나가 뽑힙니다. 항목들이 서로 무관할 때 가장 잘 맞습니다. 누가 살지, 어디서 먹을지, 누가 설거지할지.</li>
                <li><b>팀 나누기</b> — 명단을 붙여 넣으면 인원이 고른 팀으로 나뉩니다. <i>누가</i> 뽑혔는지보다 <b>그 자리의 누구도 편성에 손대지 않았다</b>는 사실이 중요할 때 씁니다.</li>
                <li><b>주사위</b> — 1~6개를 실제로 굴립니다. 보드게임 주사위를 잃어버렸을 때, 그리고 논쟁보다 숫자 두 개가 더 빠를 때.</li>
                <li><b>빙고</b> — 중복 없이 번호를 뽑고 지금까지 부른 목록을 화면에 남깁니다. 교실·행사장·회사 파티처럼 종이 카드가 이미 돌고 있는 자리를 위한 것입니다.</li>
                <li><b>랜덤 레이스</b> — 룰렛과 같은 추첨인데 결과가 레이스로 나옵니다. 일부러 느립니다. 1등만이 아니라 <b>전체 순위</b>가 나오기 때문입니다.</li>
                <li><b>사다리타기</b> — 경로가 공개되기 전에 각자 선을 고릅니다. 자기가 참여하지 않은 추첨을 못 믿는 사람이 있을 때 가장 깔끔한 방법입니다.</li>
            </ul>

            <h3>왜 보이는 추첨이어야 하는가</h3>
            <p>사실 이 여섯 개는 전부 난수 한 줄로 대체할 수 있고, 그러면 하나도 작동하지 않습니다. 사람들이 굳이 돌아가는 룰렛을 찾는 이유는 수학이 아니라 사회적인 것입니다. 결정은 <b>목격되어야</b> 합니다. 모두가 같은 룰렛이 느려지는 걸 함께 볼 때, 결과는 누군가의 것이 아니라 절차의 것이 됩니다. 그래서 여기서 애니메이션은 장식이 아니라 결과를 승복하게 만드는 핵심입니다.</p>
            <p>랜덤 레이스가 룰렛과 겹치는데도 따로 있는 이유도 같습니다. 룰렛은 2초 만에 "누가?"에 답합니다. 레이스는 30초 동안 "어떤 순서로?"에 답하고, 그 사이에 볼거리를 만듭니다. 질문이 다르면 필요한 극적 효과의 양도 다릅니다.</p>

            <h3>얼마나 공정한가</h3>
            <p>모든 추첨은 브라우저 자체의 난수 생성기를 씁니다. 어떤 항목에도 가중치가 없고, 결과가 미리 정해지지도 않으며, 룰렛에서의 위치나 레이스의 레인 번호는 확률에 영향을 주지 않습니다. 항목이 <i>n</i>개면 매 추첨마다 각자 1/<i>n</i>이고, 추첨끼리 독립이라 한 번 뽑혔다고 다음 확률이 낮아지지 않습니다. "이미 뽑힌 사람 제외"를 원하면 다시 돌리기 전에 그 항목을 지우면 됩니다.</p>
            <p>알아두면 좋은 것 하나: 6명이 6번 돌렸을 때 전원이 정확히 한 번씩 뽑힐 확률은 약 1.5%입니다. 몰리는 건 정상이고, 룰렛이 고장 난 증거가 아닙니다.</p>

            <h3>주로 이런 데 씁니다</h3>
            <p>커피값·밥값 누가 낼지. 수업에서 조 나누기. 아무도 마지막을 자원하지 않는 발표 순서. 집안일 분담. 행사 경품 추첨. 모임 벌칙 정하기. 뭘 볼지 정하기. 전부 같은 모양입니다 — 작은 집단, 아무도 책임지고 싶지 않은 결정, 그리고 결과가 모두에게 동시에 보여야 한다는 조건.</p>""",
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
    prose="""            <h2>ワンタップで決まるランダム抽選</h2>
            <p>Lucky Please は、みんなで何かを決めなければならないのに、誰もその決定を自分の名前でしたくない場面のためのツール6種です。ルーレットを回す、チームを分ける、サイコロを振る、ビンゴ番号を引く、レースを走らせる、あみだくじを引く。そして同じ画面を全員に見せれば終わりです。インストールも登録も不要で、食卓でスマホを回して使っても、教室のプロジェクターに映しても同じように動きます。</p>

            <h3>どの場面でどれを使うか</h3>
            <ul class="lp-seo-list">
                <li><b>ルーレット</b> — 一番汎用的です。名前でも選択肢でも入れて回せば一つが選ばれます。項目同士が無関係なときに最も向きます。誰がおごるか、どこで食べるか、誰が片付けるか。</li>
                <li><b>チーム分け</b> — 名簿を貼り付ければ人数の揃ったチームに分かれます。<i>誰が</i>選ばれたかより、<b>その場の誰も編成に手を触れていない</b>ことが重要なときに使います。</li>
                <li><b>サイコロ</b> — 1〜6個を実際に転がします。ボードゲームのサイコロを失くしたとき、そして議論より数字二つのほうが速いとき。</li>
                <li><b>ビンゴ</b> — 重複なしで番号を引き、これまでに呼んだ一覧を画面に残します。教室・イベント会場・職場のパーティーなど、紙のカードがすでに配られている場のためのものです。</li>
                <li><b>ランダムレース</b> — ルーレットと同じ抽選ですが、結果がレースとして現れます。わざと遅いのは、1位だけでなく<b>全順位</b>が出るからです。</li>
                <li><b>あみだくじ</b> — 経路が公開される前に各自が線を選びます。自分が参加していない抽選を信用できない人がいるとき、最も筋が通る方法です。</li>
            </ul>

            <h3>なぜ「見える抽選」でなければならないのか</h3>
            <p>この六つはすべて乱数一行で置き換えられますし、そうすると一つも機能しません。人がわざわざ回るルーレットを求める理由は数学ではなく社会的なものです。決定は<b>目撃されなければならない</b>のです。全員が同じルーレットの減速を一緒に見るとき、結果は誰かのものではなく手続きのものになります。ここでアニメーションが装飾ではなく、結果を受け入れさせる中核である理由がこれです。</p>
            <p>ランダムレースがルーレットと役割が重なるのに別に存在する理由も同じです。ルーレットは2秒で「誰が?」に答えます。レースは30秒かけて「どの順番で?」に答え、その間に見どころを作ります。問いが違えば必要な演出の量も違います。</p>

            <h3>どのくらい公平か</h3>
            <p>すべての抽選はブラウザ自身の乱数生成器を使います。どの項目にも重み付けはなく、結果が事前に決まっていることもなく、ルーレット上の位置やレースのレーン番号は確率に影響しません。項目が <i>n</i> 個なら毎回それぞれ 1/<i>n</i> で、抽選同士は独立なので一度選ばれても次の確率は下がりません。「一度選ばれた人を除く」動作が欲しければ、回す前にその項目を消してください。</p>
            <p>知っておくとよいこと: 6人で6回回したとき、全員がちょうど一度ずつ選ばれる確率は約1.5%です。偏るのは正常であり、ルーレットが壊れている証拠ではありません。</p>

            <h3>よく使われる場面</h3>
            <p>コーヒー代・食事代を誰が払うか。授業のグループ分け。誰も最後を志願しない発表順。家事の分担。イベントの景品抽選。飲み会の罰ゲーム決め。何を観るか。すべて同じ形をしています — 小さな集団、誰も引き受けたくない決定、そして結果が全員に同時に見えなければならないという条件。</p>""",
    faq=[
        ("無料ですか?",
         "はい。6種すべて無料で、登録もインストールも不要です。広告が出る場合も結果画面とホーム下部のみで、抽選中には絶対に出ません。"),
        ("結果は本当にランダムですか?",
         "はい。すべての抽選はブラウザ自身の乱数生成器を呼び出します。ルーレット上の位置でも、あみだの線でも、スタートラインのどこにいても確率は同じです。重み付けも事前に決まった結果もありません。"),
        ("アカウントは必要ですか?",
         "いいえ。すべてのツールがログインなしですぐ動きます。アカウントは端末間のグループ保存やマルチプレイなど任意の追加機能にのみ使われます。"),
        ("スマホでも動きますか?",
         "はい。すべてのツールが縦向きスマホを基準に作られ、タブレットやデスクトップに拡張されます。食卓でスマホを回しても、教室のプロジェクターに同じページを映しても構いません。"),
        ("結果を友達に共有できますか?",
         "はい。抽選が終わるとワンタップの共有リンクが出ます。リンクを開いた人は全く同じ結果を見るので、結果について揉めにくくなります。"),
        ("何か国語に対応していますか?",
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
    prose="""            <h2>Sorteos aleatorios que se resuelven con un toque</h2>
            <p>Lucky Please es un conjunto de seis sorteos aleatorios para ese momento en que un grupo necesita decidir algo y nadie quiere ser quien lo decidió. Gira una ruleta, divide equipos, tira los dados, canta números de bingo, corre una carrera o sortea una escalera, y luego enseña la misma pantalla a todos. No hay nada que instalar ni cuenta que crear, y funciona igual en un móvil que pasa de mano en mano alrededor de una mesa que en un proyector de aula.</p>

            <h3>Para qué sirve mejor cada uno</h3>
            <ul class="lp-seo-list">
                <li><b>Ruleta</b> — la más versátil. Escribe cualquier lista de nombres u opciones, gira y sale una. Va mejor cuando las entradas no tienen relación entre sí: quién paga, a qué restaurante ir, a quién le toca fregar.</li>
                <li><b>Generador de equipos</b> — pega una lista y se divide en grupos equilibrados. Útil cuando lo importante no es <i>a quién</i> le toca, sino que nadie de los presentes tocó el reparto.</li>
                <li><b>Dados</b> — de uno a seis dados con tirada física. Práctico para juegos de mesa a los que se les perdieron los dados, y para cualquier cosa donde dos números resuelvan más rápido que una discusión.</li>
                <li><b>Bingo</b> — saca números sin repetir y deja en pantalla la lista de los cantados. Pensado para aulas, salones y fiestas de oficina donde ya circulan los cartones impresos.</li>
                <li><b>Carrera aleatoria</b> — el mismo sorteo que la ruleta, pero el resultado llega como una carrera con orden de llegada visible. Es lenta a propósito: produce una clasificación completa, no solo un ganador.</li>
                <li><b>Escalera</b> — conocida como <i>amidakuji</i> o ghost leg. Cada persona elige una línea antes de revelar los caminos, la opción más limpia cuando alguien desconfía de un sorteo en el que no participó.</li>
            </ul>

            <h3>Por qué un sorteo visible funciona mejor que uno oculto</h3>
            <p>Cualquiera de estos podría sustituirse por un generador de números aleatorios de una línea, y ninguno funcionaría. La razón por la que un grupo recurre a una ruleta que gira es social, no matemática: la decisión tiene que ser <b>presenciada</b>. Cuando todos ven la misma ruleta frenar, el resultado deja de pertenecer a una persona y pasa a pertenecer al procedimiento. Por eso aquí la animación no es decoración: es la parte que hace que el resultado se acepte.</p>
            <p>Por eso también existe la carrera aunque la ruleta ya cubra el mismo trabajo. La ruleta responde "¿quién?" en dos segundos. La carrera responde "¿en qué orden?" durante treinta, y por el camino da algo que mirar. Preguntas distintas merecen dosis distintas de dramatismo.</p>

            <h3>Qué tan justo es realmente</h3>
            <p>Cada sorteo usa el generador de números aleatorios del propio navegador. Ninguna entrada está ponderada, ningún resultado está elegido de antemano, y la posición en la ruleta o el carril en la carrera no afectan a las probabilidades. Con <i>n</i> entradas, cada una tiene 1/<i>n</i> en cada tirada, y como los sorteos son independientes, salir una vez no reduce tu probabilidad la siguiente. Si prefieres el comportamiento de "ya salió, se elimina", borra esa entrada antes de volver a girar.</p>
            <p>Un dato útil: con seis personas y seis rondas, la probabilidad de que a cada una le toque exactamente una vez es del 1,5 % aproximadamente. Las rachas son normales, no una prueba de que la ruleta esté rota.</p>

            <h3>Dónde se usa esto</h3>
            <p>Decidir quién paga el café o la cena. Dividir una clase en grupos de trabajo. Elegir el orden de las presentaciones sin que nadie se ofrezca a ir el último. Repartir las tareas de casa. Hacer un sorteo en un evento. Elegir una prenda en un juego. Decidir qué película ver. Todos tienen la misma forma: un grupo pequeño, una decisión que nadie quiere asumir y la necesidad de que el resultado sea visible para todos a la vez.</p>""",
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
    prose="""            <h2>Sorteios aleatórios que resolvem com um toque</h2>
            <p>Lucky Please é um conjunto de seis sorteios aleatórios para aquele momento em que um grupo precisa decidir algo e ninguém quer ser a pessoa que decidiu. Gire uma roleta, divida times, role os dados, cante números de bingo, corra uma corrida ou sorteie uma escada, e depois mostre a mesma tela para todo mundo. Não há nada para instalar nem conta para criar, e funciona igual em um celular passando de mão em mão na mesa ou em um projetor de sala de aula.</p>

            <h3>Para que cada um serve melhor</h3>
            <ul class="lp-seo-list">
                <li><b>Roleta</b> — a mais versátil. Digite qualquer lista de nomes ou opções, gire, e uma é escolhida. Funciona melhor quando as entradas não têm relação entre si: quem paga, qual restaurante, quem lava a louça.</li>
                <li><b>Sorteio de times</b> — cole uma lista e ela é dividida em grupos equilibrados. Útil quando o importante não é <i>quem</i> foi escolhido, mas que ninguém presente mexeu na divisão.</li>
                <li><b>Dados</b> — de um a seis dados com rolagem física. Prático para jogos de tabuleiro que perderam os dados, e para qualquer coisa em que dois números resolvem mais rápido que uma discussão.</li>
                <li><b>Bingo</b> — sorteia números sem repetir e mantém na tela a lista dos já chamados. Feito para salas de aula, salões e festas de empresa onde as cartelas impressas já estão circulando.</li>
                <li><b>Corrida aleatória</b> — o mesmo sorteio da roleta, mas o resultado chega como uma corrida com ordem de chegada visível. É lenta de propósito: produz uma classificação completa, não só um vencedor.</li>
                <li><b>Escada</b> — conhecida como <i>amidakuji</i> ou ghost leg. Cada pessoa escolhe uma linha antes de os caminhos serem revelados, a opção mais limpa quando alguém desconfia de um sorteio do qual não participou.</li>
            </ul>

            <h3>Por que um sorteio visível funciona melhor que um escondido</h3>
            <p>Qualquer um destes poderia ser substituído por um gerador de números aleatórios de uma linha, e nenhum funcionaria. O motivo pelo qual um grupo recorre a uma roleta girando é social, não matemático: a decisão precisa ser <b>testemunhada</b>. Quando todos veem a mesma roleta desacelerar, o resultado deixa de pertencer a uma pessoa e passa a pertencer ao procedimento. É por isso que a animação aqui não é enfeite: é a parte que faz o resultado ser aceito.</p>
            <p>É também por isso que a corrida existe mesmo com a roleta já cobrindo o mesmo trabalho. A roleta responde "quem?" em dois segundos. A corrida responde "em que ordem?" ao longo de trinta, e no caminho dá algo para acompanhar. Perguntas diferentes merecem doses diferentes de drama.</p>

            <h3>Quão justo isso realmente é</h3>
            <p>Cada sorteio usa o gerador de números aleatórios do próprio navegador. Nenhuma entrada tem peso, nenhum resultado é escolhido de antemão, e a posição na roleta ou a raia na corrida não afetam as probabilidades. Com <i>n</i> entradas, cada uma tem 1/<i>n</i> a cada rodada, e como os sorteios são independentes, ter sido sorteado uma vez não diminui sua chance na próxima. Se você quer o comportamento de "já saiu, sai da lista", apague a entrada antes de girar de novo.</p>
            <p>Um dado útil: com seis pessoas e seis rodadas, a probabilidade de cada uma sair exatamente uma vez é de cerca de 1,5%. Sequências repetidas são normais, e não prova de que a roleta esteja quebrada.</p>

            <h3>Onde as pessoas usam isso</h3>
            <p>Decidir quem paga o café ou o jantar. Dividir uma turma em grupos de trabalho. Escolher a ordem das apresentações sem ninguém se oferecer para ir por último. Dividir as tarefas de casa. Fazer um sorteio em um evento. Escolher a prenda em um jogo. Decidir qual filme assistir. Todos têm o mesmo formato: um grupo pequeno, uma decisão que ninguém quer assumir e a necessidade de que o resultado seja visível para todos ao mesmo tempo.</p>""",
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

    # FAQPage 스키마 교체 — 아래 가시 <dl> 과 1:1
    fq_start = s.index('    {"@context":"https://schema.org","@type":"FAQPage"')
    fq_end = s.index("]}", fq_start) + 2
    faq_json = ('    {"@context":"https://schema.org","@type":"FAQPage","inLanguage":"%s","mainEntity":[' % code) + ",".join(
        '{"@type":"Question","name":"%s","acceptedAnswer":{"@type":"Answer","text":"%s"}}' % (esc(q), esc(a))
        for q, a in cfg["faq"]) + "]}"
    s = s[:fq_start] + faq_json + s[fq_end:]

    # 가시 콘텐츠 교체
    sec_start = s.index('        <section class="lp-home-seo"')
    sec_end = s.index("</section>", sec_start) + len("</section>")
    faq_dl = "\n".join(
        "                <dt>%s</dt>\n                <dd>%s</dd>" % (q, a) for q, a in cfg["faq"])
    faq_head = {"ko": "자주 묻는 질문", "ja": "よくある質問",
                "es": "Preguntas frecuentes", "pt": "Perguntas frequentes"}[code]
    new_sec = ('        <section class="lp-home-seo" lang="%s" aria-label="About Lucky Please">\n'
               "%s\n\n"
               "            <h2>%s</h2>\n"
               '            <dl class="lp-seo-faq">\n%s\n            </dl>\n'
               "        </section>") % (cfg["html_lang"], cfg["prose"], faq_head, faq_dl)
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
