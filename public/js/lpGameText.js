/*
  lpGameText.js — 게임 페이지에 남은 한국어 UI 문자열 현지화 (2026-08-19)

  왜 이 방식인가
  ---------------
  메인에서 고른 언어가 게임에 들어가면 일부 자리에서 한국어로 남았다.
  원인은 게임마다 다르다 — i18n 테이블에 키가 아예 없거나, 함수 안에
  한국어가 직접 박혀 있거나, 마크업이 제각각이라 applyLanguage() 가
  그 요소를 건드리지 않는다.

  17개 자가완결 HTML 을 각각 수술하는 방법도 있지만, 실제로 그렇게 하다가
  car-racing 에서 같은 모양의 다른 테이블(SHARE_I18N)을 덮어써 공유
  다이얼로그를 깨뜨렸다. 게임 로직에 손대지 않고 **표시 문자열만** 바꾸는
  이 방식이 사고 반경이 훨씬 작다. 새 게임이 들어와도 표에 줄만 추가하면
  된다.

  적용 범위
  ---------
  - 텍스트 노드 전체가 하나의 문장/단어인 것만 바꾼다.
  - 한 문장이 <b> 등으로 쪼개져 여러 노드에 걸친 경우는 건드리지 않는다.
    조각별로 번역하면 어순이 무너진다. 그런 자리는 게임별 i18n 으로
    처리해야 하며, 남은 목록은 docs 와 커밋 메시지에 적어 둔다.
  - `.lp-game-about` 은 의도적으로 한국어 SEO 콘텐츠라 제외한다.

  언어
  ----
  SEO 투자 5개 언어(en/es/pt/ja/ko) 기준. ko 는 원문이라 치환하지 않고,
  나머지 11개 UI 언어는 en 으로 떨어진다.
*/
(function () {
    'use strict';

    /* ko 원문 → 언어별 번역. 키는 화면에 나타나는 문자열 그대로(공백 정규화 후). */
    var MAP = {
        /* ── 여러 게임 공통 ────────────────────────────────────── */
        '일시정지':      { en: 'Pause', ja: '一時停止', es: 'Pausa', pt: 'Pausa' },
        '⏸ 일시정지':   { en: '⏸ Pause', ja: '⏸ 一時停止', es: '⏸ Pausa', pt: '⏸ Pausa' },
        '불러오는 중…':  { en: 'Loading…', ja: '読み込み中…', es: 'Cargando…', pt: 'Carregando…' },
        '시작':          { en: 'Start', ja: 'スタート', es: 'Empezar', pt: 'Começar' },
        '로그인':        { en: 'Sign in', ja: 'ログイン', es: 'Entrar', pt: 'Entrar' },
        '월드':          { en: 'World', ja: '世界', es: 'Mundo', pt: 'Mundo' },
        '오늘':          { en: 'Today', ja: '今日', es: 'Hoy', pt: 'Hoje' },
        '친구':          { en: 'Friends', ja: 'フレンド', es: 'Amigos', pt: 'Amigos' },
        '🏆 랭킹':       { en: '🏆 Ranking', ja: '🏆 ランキング', es: '🏆 Ranking', pt: '🏆 Ranking' },
        '🎮 다른 게임':  { en: '🎮 More games', ja: '🎮 ほかのゲーム', es: '🎮 Más juegos', pt: '🎮 Mais jogos' },
        '완벽한 착륙 + 충분한 연료': { en: 'Perfect landing, fuel to spare', ja: '完璧な着陸 + 燃料に余裕', es: 'Aterrizaje perfecto y combustible de sobra', pt: 'Pouso perfeito e combustível de sobra' },
        '속도 초과 또는 착륙장 이탈': { en: 'Too fast, or off the pad', ja: '速度超過、または着陸場から外れました', es: 'Demasiada velocidad o fuera de la plataforma', pt: 'Rápido demais ou fora da plataforma' },
        '어떻게 불러드릴까요?': { en: 'What should we call you?', ja: 'お名前は？', es: '¿Cómo te llamamos?', pt: 'Como te chamamos?' },
        '🎙 방 만들기': { en: '🎙 Create a room', ja: '🎙 ルームを作る', es: '🎙 Crear sala', pt: '🎙 Criar sala' },
        '🫂 방 참가':   { en: '🫂 Join a room', ja: '🫂 ルームに参加', es: '🫂 Unirse a una sala', pt: '🫂 Entrar numa sala' },
        '← 뒤로':       { en: '← Back', ja: '← 戻る', es: '← Atrás', pt: '← Voltar' },
        '🏠 홈':        { en: '🏠 Home', ja: '🏠 ホーム', es: '🏠 Inicio', pt: '🏠 Início' },
        '🔁 한판 더':   { en: '🔁 Play again', ja: '🔁 もう一回', es: '🔁 Otra vez', pt: '🔁 De novo' },

        /* ── Brawl Run (glory-racing) ──────────────────────────── */
        '⚠️ 만화적 몸싸움 연출 포함 · Mild cartoon fighting': {
            en: '⚠️ Contains mild cartoon fighting',
            ja: '⚠️ 漫画的な小競り合いの演出があります',
            es: '⚠️ Contiene peleas de dibujos animados',
            pt: '⚠️ Contém brigas em estilo cartoon'
        },
        '✅ 저장된 리스트가 있습니다!': {
            en: '✅ You have saved lists!',
            ja: '✅ 保存済みリストがあります！',
            es: '✅ ¡Tienes listas guardadas!',
            pt: '✅ Você tem listas salvas!'
        },

        /* ── Snake ─────────────────────────────────────────────── */
        '스와이프 · 화살표 · WASD로 조작.': {
            en: 'Swipe, arrow keys or WASD to steer.',
            ja: 'スワイプ・矢印キー・WASD で操作。',
            es: 'Desliza, flechas o WASD para girar.',
            pt: 'Deslize, setas ou WASD para virar.'
        },
        '먹이를 먹으면 길어지고 속도가 빨라져요.': {
            en: 'Every bite makes you longer and faster.',
            ja: 'エサを食べるほど長く、速くなります。',
            es: 'Cada bocado te alarga y acelera.',
            pt: 'Cada mordida te alonga e acelera.'
        },

        /* ── Dot Runner (pacman) ───────────────────────────────── */
        '👻 닷 러너': { en: '👻 Dot Runner', ja: '👻 ドットランナー',
                        es: '👻 Dot Runner', pt: '👻 Dot Runner' },
        '점 모두 먹기. 유령 만나면 끝.': {
            en: 'Eat every dot. Touch a ghost and it is over.',
            ja: 'ドットを全部食べる。ゴーストに触れたら終わり。',
            es: 'Cómete todos los puntos. Si te toca un fantasma, se acabó.',
            pt: 'Coma todos os pontos. Encostou num fantasma, acabou.'
        },
        '모서리 쿠키(🟡)를 먹으면 잠깐 유령을 역으로 잡을 수 있어요.': {
            en: 'Grab a corner cookie (🟡) and you can chase the ghosts instead.',
            ja: '角のクッキー(🟡)を食べると、しばらくゴーストを追いかけられます。',
            es: 'Toma la galleta de la esquina (🟡) y podrás perseguir a los fantasmas.',
            pt: 'Pegue o biscoito do canto (🟡) e você persegue os fantasmas.'
        },

        /* ── Lucky Merge — 합쳐지는 천체 이름 ──────────────────── */
        '운석':     { en: 'Meteor', ja: '隕石', es: 'Meteorito', pt: 'Meteorito' },
        '소행성':   { en: 'Asteroid', ja: '小惑星', es: 'Asteroide', pt: 'Asteroide' },
        '달':       { en: 'Moon', ja: '月', es: 'Luna', pt: 'Lua' },
        '수성':     { en: 'Mercury', ja: '水星', es: 'Mercurio', pt: 'Mercúrio' },
        '금성':     { en: 'Venus', ja: '金星', es: 'Venus', pt: 'Vênus' },
        '지구':     { en: 'Earth', ja: '地球', es: 'Tierra', pt: 'Terra' },
        '화성':     { en: 'Mars', ja: '火星', es: 'Marte', pt: 'Marte' },
        '목성':     { en: 'Jupiter', ja: '木星', es: 'Júpiter', pt: 'Júpiter' },
        '토성':     { en: 'Saturn', ja: '土星', es: 'Saturno', pt: 'Saturno' },
        '항성':     { en: 'Star', ja: '恒星', es: 'Estrella', pt: 'Estrela' },
        '블랙홀':   { en: 'Black Hole', ja: 'ブラックホール', es: 'Agujero Negro', pt: 'Buraco Negro' },

        /* ── Burger Chef ───────────────────────────────────────── */
        '버거 셰프': { en: 'Burger Chef', ja: 'バーガーシェフ',
                       es: 'Chef Burger', pt: 'Chef Burger' },

        /* ── Starship Lander ───────────────────────────────────── */
        'SpaceX 우주선을 발사장·달·화성에 안전하게 착륙시키세요. 연료를 아끼며 속도와 각도를 조절하면 보너스 점수.': {
            en: 'Land the ship on the pad, the Moon and Mars. Save fuel and nail your speed and angle for bonus points.',
            ja: '発射場・月・火星に宇宙船を安全に着陸させましょう。燃料を節約し、速度と角度を合わせるとボーナス点。',
            es: 'Aterriza la nave en la plataforma, la Luna y Marte. Ahorra combustible y ajusta velocidad y ángulo para puntos extra.',
            pt: 'Pouse a nave na plataforma, na Lua e em Marte. Economize combustível e acerte velocidade e ângulo para pontos extras.'
        },
        '점진적 난이도': { en: 'Rising difficulty', ja: '段階的な難易度',
                           es: 'Dificultad creciente', pt: 'Dificuldade crescente' },
        '점수':          { en: 'Score', ja: 'スコア', es: 'Puntuación', pt: 'Pontuação' },
        '모바일 + PC':   { en: 'Mobile + desktop', ja: 'モバイル + PC',
                           es: 'Móvil + escritorio', pt: 'Celular + desktop' },
        '🔄 처음부터':   { en: '🔄 Restart', ja: '🔄 最初から',
                           es: '🔄 Reiniciar', pt: '🔄 Recomeçar' }
    };


    /* ── HTML 블록 맵 ────────────────────────────────────────────
       문장이 태그로 쪼개진 자리. 컨테이너의 innerHTML 을 통째로 바꾼다.
       키는 공백 정규화한 **원문 innerHTML**. 텍스트 맵보다 먼저 적용해야
       한다 — 나중에 돌리면 키 안의 낱말이 이미 번역돼 매칭이 깨진다. */
    var HTML_MAP = {
        /* Dot Runner */
        '<kbd>↑↓←→</kbd> 이동 · <kbd>Space</kbd> 일시정지': {
            en: '<kbd>↑↓←→</kbd> Move · <kbd>Space</kbd> Pause',
            ja: '<kbd>↑↓←→</kbd> 移動 · <kbd>Space</kbd> 一時停止',
            es: '<kbd>↑↓←→</kbd> Mover · <kbd>Space</kbd> Pausa',
            pt: '<kbd>↑↓←→</kbd> Mover · <kbd>Space</kbd> Pausa'
        },
        '파워 쿠키 먹으면 유령 색 변함 → 잡으면 <b>+200</b>점. 모든 점 다 먹으면 <b>+500</b> 보너스.': {
            en: 'A power cookie turns the ghosts blue — catch one for <b>+200</b>. Clear every dot for a <b>+500</b> bonus.',
            ja: 'パワークッキーでゴーストが青く変化 → 捕まえると<b>+200</b>点。全部食べると<b>+500</b>ボーナス。',
            es: 'La galleta de poder los vuelve azules — atrapa uno por <b>+200</b>. Límpialo todo y son <b>+500</b> de bono.',
            pt: 'O biscoito de poder deixa os fantasmas azuis — pegue um por <b>+200</b>. Limpe tudo e ganhe <b>+500</b> de bônus.'
        },

        /* Burger Chef */
        '왼쪽 샘플 버거와 <b>같은 순서</b>로<br> 아래 5개 재료 접시를 <b>탭</b>해요.<br> <b>시간 안에</b> 완성하면 레벨 업!<br> 틀리면 <b>시간 -2초</b>.': {
            en: 'Tap the five ingredient plates below in the <b>same order</b> as the sample burger.<br> Finish <b>in time</b> to level up.<br> A mistake costs <b>2 seconds</b>.',
            ja: '左のサンプルバーガーと<b>同じ順番</b>で<br>下の5つの材料プレートを<b>タップ</b>。<br><b>時間内</b>に完成でレベルアップ！<br>間違えると<b>-2秒</b>。',
            es: 'Toca los cinco platos en el <b>mismo orden</b> que la hamburguesa de muestra.<br> Termina <b>a tiempo</b> para subir de nivel.<br> Cada error cuesta <b>2 segundos</b>.',
            pt: 'Toque nos cinco pratos na <b>mesma ordem</b> do hambúrguer de exemplo.<br> Termine <b>a tempo</b> para subir de nível.<br> Cada erro custa <b>2 segundos</b>.'
        },
        '<kbd>탭</kbd> 또는 <kbd>1</kbd>-<kbd>5</kbd> · <kbd>Space</kbd> 일시정지': {
            en: '<kbd>Tap</kbd> or <kbd>1</kbd>-<kbd>5</kbd> · <kbd>Space</kbd> Pause',
            ja: '<kbd>タップ</kbd> または <kbd>1</kbd>-<kbd>5</kbd> · <kbd>Space</kbd> 一時停止',
            es: '<kbd>Toca</kbd> o <kbd>1</kbd>-<kbd>5</kbd> · <kbd>Space</kbd> Pausa',
            pt: '<kbd>Toque</kbd> ou <kbd>1</kbd>-<kbd>5</kbd> · <kbd>Space</kbd> Pausa'
        },
        '샘플과 <b>동일한 순서</b>로 재료 접시 5개를 탭! 완성할수록 시간이 짧아지고 재료도 길어져요.': {
            en: 'Tap the five plates in the <b>same order</b> as the sample. Each round gets shorter and the stack gets longer.',
            ja: 'サンプルと<b>同じ順番</b>で材料プレート5つをタップ！進むほど時間は短く、材料は長くなります。',
            es: 'Toca los cinco platos en el <b>mismo orden</b> que la muestra. Cada ronda es más corta y la pila más larga.',
            pt: 'Toque nos cinco pratos na <b>mesma ordem</b> da amostra. Cada rodada fica mais curta e a pilha maior.'
        },

        /* Starship Lander */
        /* 아래 5개는 게임이 자체 i18n 으로 <li> 를 다시 그린 뒤의 형태다.
           그 코드가 T.feat(한국어)로 채우므로 여기서 언어별로 덮는다. */
        '<b>1</b>Falcon 9 → Heavy → Starship → 달 → 화성': {
            en: '<b>1</b>Falcon 9 → Heavy → Starship → Moon → Mars',
            ja: '<b>1</b>Falcon 9 → Heavy → Starship → 月 → 火星',
            es: '<b>1</b>Falcon 9 → Heavy → Starship → Luna → Marte',
            pt: '<b>1</b>Falcon 9 → Heavy → Starship → Lua → Marte'
        },
        '<b>2</b>중력·바람·연료 압박': {
            en: '<b>2</b>Gravity, wind and fuel pressure',
            ja: '<b>2</b>重力・風・燃料のプレッシャー',
            es: '<b>2</b>Gravedad, viento y presión de combustible',
            pt: '<b>2</b>Gravidade, vento e pressão de combustível'
        },
        '<b>3</b>연료 + 속도 + 각도 정확도': {
            en: '<b>3</b>Fuel + speed + angle accuracy',
            ja: '<b>3</b>燃料 + 速度 + 角度の正確さ',
            es: '<b>3</b>Combustible + velocidad + precisión del ángulo',
            pt: '<b>3</b>Combustível + velocidade + precisão do ângulo'
        },
        '<b>4</b>각 스테이지마다 실제 데이터': {
            en: '<b>4</b>Real data at every stage',
            ja: '<b>4</b>各ステージに実データ',
            es: '<b>4</b>Datos reales en cada etapa',
            pt: '<b>4</b>Dados reais em cada estágio'
        },
        '<b>5</b>화살표 / 스페이스 / 터치': {
            en: '<b>5</b>Arrows / space / touch',
            ja: '<b>5</b>矢印キー / スペース / タッチ',
            es: '<b>5</b>Flechas / espacio / toque',
            pt: '<b>5</b>Setas / espaço / toque'
        },
        '<b>5</b>스테이지 — Falcon 9 → Heavy → Starship → 달 → 화성': {
            en: '<b>5</b> stages — Falcon 9 → Heavy → Starship → Moon → Mars',
            ja: '<b>5</b>ステージ — Falcon 9 → Heavy → Starship → 月 → 火星',
            es: '<b>5</b> etapas — Falcon 9 → Heavy → Starship → Luna → Marte',
            pt: '<b>5</b> estágios — Falcon 9 → Heavy → Starship → Lua → Marte'
        },
        '<b>점진적 난이도</b> — 중력·바람·연료 압박': {
            en: '<b>Rising difficulty</b> — gravity, wind and fuel pressure',
            ja: '<b>段階的な難易度</b> — 重力・風・燃料のプレッシャー',
            es: '<b>Dificultad creciente</b> — gravedad, viento y presión de combustible',
            pt: '<b>Dificuldade crescente</b> — gravidade, vento e pressão de combustível'
        },
        '<b>점수</b> — 연료 + 속도 + 각도 정확도': {
            en: '<b>Score</b> — fuel + speed + angle accuracy',
            ja: '<b>スコア</b> — 燃料 + 速度 + 角度の正確さ',
            es: '<b>Puntuación</b> — combustible + velocidad + precisión del ángulo',
            pt: '<b>Pontuação</b> — combustível + velocidade + precisão do ângulo'
        },
        '<b>SpaceX 팩트</b> — 각 스테이지마다 실제 데이터': {
            en: '<b>SpaceX facts</b> — real data at every stage',
            ja: '<b>SpaceX の豆知識</b> — 各ステージに実データ',
            es: '<b>Datos de SpaceX</b> — datos reales en cada etapa',
            pt: '<b>Fatos da SpaceX</b> — dados reais em cada estágio'
        },
        '친구들과 실시간으로 대결하는 멀티플레이 퀴즈예요. 호스트가 방을 만들고 게스트는 방 코드 + 4자리 PIN으로 <b>회원가입 없이</b> 참가합니다. 최대 <b>100명</b>까지, <b>최소 2명</b> (호스트 1 + 게스트 1) 부터 시작 가능.': {
            en: 'A live multiplayer quiz. The host opens a room and guests join with the room code and a 4-digit PIN &mdash; <b>no sign-up</b>. Up to <b>100 players</b>, and <b>2 is enough</b> (one host, one guest) to start.',
            ja: 'リアルタイム対戦のマルチプレイクイズ。ホストがルームを作り、ゲストはルームコードと4桁のPINで<b>登録なし</b>で参加します。最大<b>100人</b>、<b>2人</b>（ホスト1＋ゲスト1）から開始できます。',
            es: 'Un concurso multijugador en vivo. El anfitrión abre una sala y los invitados entran con el código y un PIN de 4 dígitos, <b>sin registro</b>. Hasta <b>100 jugadores</b>, y bastan <b>2</b> (anfitrión e invitado) para empezar.',
            pt: 'Um quiz multijogador ao vivo. O anfitrião abre uma sala e os convidados entram com o código e um PIN de 4 dígitos, <b>sem cadastro</b>. Até <b>100 jogadores</b>, e <b>2 já bastam</b> (anfitrião e convidado) para começar.'
        },
        '<b>모바일 + PC</b> — 화살표 / 스페이스 / 터치': {
            en: '<b>Mobile + desktop</b> — arrows / space / touch',
            ja: '<b>モバイル + PC</b> — 矢印キー / スペース / タッチ',
            es: '<b>Móvil + escritorio</b> — flechas / espacio / toque',
            pt: '<b>Celular + desktop</b> — setas / espaço / toque'
        }
    };

    /* ── 퀴즈 UI (2026-08-21) — 자체 i18n 테이블이 없는 유일한 게임이라
       스페인어로 열어도 한국어 48종이 그대로 남아 있었다(실측). 게임
       HTML 에 테이블을 새로 만들면 다음 게임에서 또 빠지므로 여기에 둔다. */
    MAP['🌏 Region · 지역'] = { en: '🌏 Region', ja: '🌏 Region · 地域', es: '🌏 Región', pt: '🌏 Região' };
    MAP['문제는 이 언어 기준으로 출제돼요. 방에 들어오는 모든 게스트가 같은 언어 문제를 봐요.'] = { en: 'Questions come in this language. Everyone who joins sees the same set.', ja: '問題はこの言語で出題されます。参加者全員が同じ言語の問題を見ます。', es: 'Las preguntas salen en este idioma. Todos los que entren verán las mismas.', pt: 'As perguntas vêm neste idioma. Todo mundo que entrar vê as mesmas.' };
    MAP['한국어'] = { en: 'Korean', ja: '韓国語', es: 'Coreano', pt: 'Coreano' };
    MAP['🎲 카테고리 선택'] = { en: '🎲 Pick categories', ja: '🎲 カテゴリ選択', es: '🎲 Elige categorías', pt: '🎲 Escolha categorias' };
    MAP['여러 개 고르면 섞여서 나와요. 어린이~어른 모두 소외 안 되게'] = { en: 'Pick a few and they get mixed, so nobody from kids to grown-ups feels left out.', ja: '複数選ぶと混ざって出ます。子どもから大人まで誰も置いていかれないように', es: 'Si eliges varias, se mezclan para que nadie, de niños a adultos, quede fuera.', pt: 'Escolha várias e elas se misturam, para que ninguém, de crianças a adultos, fique de fora.' };
    MAP['혼합'] = { en: 'Mixed', ja: 'ミックス', es: 'Mixto', pt: 'Misto' };
    MAP['추천.'] = { en: 'recommended.', ja: 'がおすすめ。', es: 'recomendado.', pt: 'recomendado.' };
    MAP['총 문제 수'] = { en: 'Total questions', ja: '問題数', es: 'Total de preguntas', pt: 'Total de perguntas' };
    MAP['📦 카테고리별 분배'] = { en: '📦 Split by category', ja: '📦 カテゴリ別の配分', es: '📦 Reparto por categoría', pt: '📦 Divisão por categoria' };
    MAP['⟳ 균등 분배'] = { en: '⟳ Split evenly', ja: '⟳ 均等に分ける', es: '⟳ Repartir igual', pt: '⟳ Dividir igualmente' };
    MAP['합계'] = { en: 'Total', ja: '合計', es: 'Total', pt: 'Total' };
    MAP['문제'] = { en: 'questions', ja: '問', es: 'preguntas', pt: 'perguntas' };
    MAP['문제당 시간'] = { en: 'Time per question', ja: '1問あたりの時間', es: 'Tiempo por pregunta', pt: 'Tempo por pergunta' };
    MAP['초'] = { en: 'sec', ja: '秒', es: 's', pt: 's' };
    MAP['🙋 호스트도 같이 플레이'] = { en: '🙋 Host plays too', ja: '🙋 ホストも参加する', es: '🙋 El anfitrión también juega', pt: '🙋 O anfitrião também joga' };
    MAP['OFF면 진행만 — 문제 풀지 않고 순위에 안 들어가요'] = { en: 'Off means you just run the game — no answering, no ranking.', ja: 'OFF なら進行のみ — 回答せず順位にも入りません', es: 'Si está apagado, solo diriges: no respondes ni entras en el ranking.', pt: 'Desligado significa que você só conduz: não responde nem entra no ranking.' };
    MAP['▶ 방 만들기 (게스트 모집)'] = { en: '▶ Create a room', ja: '▶ ルームを作る', es: '▶ Crear sala', pt: '▶ Criar sala' };
    MAP['호스트가 알려준'] = { en: 'Enter the', ja: 'ホストから聞いた', es: 'Introduce el', pt: 'Digite o' };
    MAP['6자리 코드'] = { en: '6-character code', ja: '6桁のコード', es: 'código de 6 caracteres', pt: 'código de 6 caracteres' };
    MAP['와'] = { en: 'and the', ja: 'と', es: 'y el', pt: 'e o' };
    MAP['4자리 PIN'] = { en: '4-digit PIN', ja: '4桁のPIN', es: 'PIN de 4 dígitos', pt: 'PIN de 4 dígitos' };
    MAP['을 입력하세요.'] = { en: 'the host gave you.', ja: 'を入力してください。', es: 'que te dio el anfitrión.', pt: 'que o anfitrião passou.' };
    MAP['닉네임 (선택)'] = { en: 'Nickname (optional)', ja: 'ニックネーム（任意）', es: 'Apodo (opcional)', pt: 'Apelido (opcional)' };
    MAP['참가하기 →'] = { en: 'Join →', ja: '参加する →', es: 'Entrar →', pt: 'Entrar →' };
    MAP['방 코드 · PIN'] = { en: 'Room code · PIN', ja: 'ルームコード · PIN', es: 'Código · PIN', pt: 'Código · PIN' };
    MAP['🔗 링크 복사'] = { en: '🔗 Copy link', ja: '🔗 リンクをコピー', es: '🔗 Copiar enlace', pt: '🔗 Copiar link' };
    MAP['📤 공유'] = { en: '📤 Share', ja: '📤 共有', es: '📤 Compartir', pt: '📤 Compartilhar' };
    MAP['명 참가중'] = { en: 'joined', ja: '人 参加中', es: 'conectados', pt: 'conectados' };
    MAP['방 나가기'] = { en: 'Leave room', ja: 'ルームを出る', es: 'Salir de la sala', pt: 'Sair da sala' };
    MAP['일반'] = { en: 'General', ja: '一般', es: 'General', pt: 'Geral' };
    MAP['문제를 불러오는 중…'] = { en: 'Loading questions…', ja: '問題を読み込み中…', es: 'Cargando preguntas…', pt: 'Carregando perguntas…' };
    MAP['답변'] = { en: 'Answers', ja: '回答', es: 'Respuestas', pt: 'Respostas' };
    MAP['정답!'] = { en: 'Correct!', ja: '正解！', es: '¡Correcto!', pt: 'Certa!' };
    MAP['📊 답변 통계'] = { en: '📊 Answer breakdown', ja: '📊 回答の内訳', es: '📊 Reparto de respuestas', pt: '📊 Distribuição das respostas' };
    MAP['잠시 후 다음 문제…'] = { en: 'Next question coming up…', ja: 'まもなく次の問題…', es: 'Siguiente pregunta en un momento…', pt: 'Próxima pergunta já vem…' };
    MAP['🏆 중간 순위'] = { en: '🏆 Standings so far', ja: '🏆 途中順位', es: '🏆 Clasificación parcial', pt: '🏆 Classificação parcial' };
    MAP['🎉 최종 결과'] = { en: '🎉 Final results', ja: '🎉 最終結果', es: '🎉 Resultado final', pt: '🎉 Resultado final' };
    MAP['📋 전체 순위'] = { en: '📋 Full ranking', ja: '📋 全順位', es: '📋 Clasificación completa', pt: '📋 Classificação completa' };
    MAP['내 퀴즈 관리'] = { en: 'My questions', ja: 'マイクイズ管理', es: 'Mis preguntas', pt: 'Minhas perguntas' };
    MAP['로그인한 계정으로 직접 만든 문제예요. 서버에'] = { en: 'Questions you wrote while signed in. They stay on the server for', ja: 'ログイン中に自分で作った問題です。サーバーには', es: 'Preguntas que escribiste con tu cuenta. Se guardan en el servidor durante', pt: 'Perguntas que você criou logado. Ficam no servidor por' };
    MAP['7일'] = { en: '7 days', ja: '7日間', es: '7 días', pt: '7 dias' };
    MAP['까지 보관되고 그 이후 자동으로 삭제됩니다. 최대 200문제까지 저장 가능.'] = { en: 'and are deleted automatically after that. Up to 200 questions.', ja: '保存され、その後は自動で削除されます。最大200問まで。', es: 'y luego se borran solas. Hasta 200 preguntas.', pt: 'e depois são apagadas sozinhas. Até 200 perguntas.' };
    MAP['선택지 (정답에 표시)'] = { en: 'Options (mark the right one)', ja: '選択肢（正解にチェック）', es: 'Opciones (marca la correcta)', pt: 'Opções (marque a certa)' };
    MAP['힌트 (선택)'] = { en: 'Hint (optional)', ja: 'ヒント（任意）', es: 'Pista (opcional)', pt: 'Dica (opcional)' };
    MAP['＋ 문제 추가'] = { en: '＋ Add question', ja: '＋ 問題を追加', es: '＋ Añadir pregunta', pt: '＋ Adicionar pergunta' };
    MAP['내 문제'] = { en: 'My questions', ja: 'マイ問題', es: 'Mis preguntas', pt: 'Minhas perguntas' };
    /* 카운터 접미사 — 영어·스페인어·포르투갈어에는 대응어가 없다. 빈
   문자열은 falsy 라 치환이 스킵되므로 공백 한 칸을 쓴다. */
MAP['개'] = { en: ' ', ja: '件', es: ' ', pt: ' ' };
    MAP['탭하여 펼치기 / 휴지통으로 삭제'] = { en: 'Tap to expand · trash to delete', ja: 'タップで展開 / ゴミ箱で削除', es: 'Toca para abrir · papelera para borrar', pt: 'Toque para abrir · lixeira para excluir' };
    MAP['아직 만든 문제가 없어요. 위에서 추가해보세요!'] = { en: 'No questions yet — add one above!', ja: 'まだ問題がありません。上から追加してみましょう！', es: 'Aún no hay preguntas: ¡añade una arriba!', pt: 'Ainda sem perguntas — adicione uma acima!' };

    /* 카레이싱 랩 표시의 HTML 초기값 — JS 가 레이스 시작 시 갱신하지만
       그 전까지 화면에 한국어로 남는다(2026-08-21 실측). */
    MAP['🔄 2바퀴 순환'] = { en: '🔄 2 laps', ja: '🔄 2周', es: '🔄 2 vueltas', pt: '🔄 2 voltas' };

    function pickLang() {
        var l;
        try { l = localStorage.getItem('luckyplz_lang') || 'en'; } catch (e) { l = 'en'; }
        if (l === 'ko') return null;                 /* 원문 그대로 */
        if (l === 'gb') return 'en';
        return (l === 'ja' || l === 'es' || l === 'pt') ? l : 'en';
    }

    var applied = 0;

    /* ── 원문 레지스트리 (2026-08-20) ─────────────────────────────────
       치환이 원문 파괴형이면 언어를 두 번 바꿀 수 없다 — 이미 영어가 된
       노드는 한국어 키와 매칭이 안 돼 이전 언어로 잔류한다. 그래서 처음
       치환할 때 원문을 기록해 두고, 재적용은 항상 원문 기준으로 한다.
       ko 로 돌아오면 원문을 그대로 복원한다. */
    var regText = [];   /* {node, raw(원문 nodeValue), key} */
    var regHtml = [];   /* {el, key} — 원문은 el.dataset.lpOrigHtml */
    var seenText = (typeof WeakSet !== 'undefined') ? new WeakSet() : null;
    function textSeen(n) {
        if (seenText) return seenText.has(n);
        for (var i = 0; i < regText.length; i++) if (regText[i].node === n) return true;
        return false;
    }

    /* 공백 정규화된 key 로 raw 안을 치환한다. raw 에 줄바꿈이 있으면
       raw.replace(key,…) 가 못 찾으므로(2026-08-21 퀴즈 두 줄 안내문)
       노드 전체를 번역문으로 바꾸되 앞뒤 여백만 보존한다. 신규 스캔과
       재적용(regText) 양쪽이 같은 함수를 써야 한다 — 한쪽에만 넣었더니
       첫 적용 뒤 400ms 재적용에서 한국어로 되돌아갔다. */
    function renderText(raw, key, val) {
        if (raw.indexOf(key) !== -1) return raw.replace(key, val);
        return raw.match(/^\s*/)[0] + val + raw.match(/\s*$/)[0];
    }

    function applyHtml(lang) {
        /* 1) 등록분 재렌더 — 원문 기준이라 어느 언어에서 와도 올바르다. */
        for (var i = 0; i < regHtml.length; i++) {
            var r = regHtml[i];
            if (!r.el.isConnected) continue;
            var row0 = HTML_MAP[r.key];
            r.el.innerHTML = (lang && row0 && row0[lang]) ? row0[lang] : r.el.dataset.lpOrigHtml;
        }
        if (!lang) return;
        /* 2) 신규 스캔. 텍스트 맵보다 먼저. 태그를 포함한 요소만 훑는다. */
        var nodes = document.querySelectorAll('p, li, div, span, h1, h2, h3');
        for (var j = 0; j < nodes.length; j++) {
            var el = nodes[j];
            if (el.dataset.lpOrigHtml != null) continue;   /* 이미 등록됨 */
            if (el.closest('.lp-game-about')) continue;
            var html = el.innerHTML;
            if (!html || html.length > 400 || !/[가-힣]/.test(html)) continue;
            var key = html.replace(/\s+/g, ' ').trim();
            var row = HTML_MAP[key];
            if (row && row[lang]) {
                el.dataset.lpOrigHtml = html;
                regHtml.push({ el: el, key: key });
                el.innerHTML = row[lang];
            }
        }
    }

    function apply() {
        var lang = pickLang();
        /* ko 인데 치환 이력도 없으면 할 일 없음 — 다수 사용자(ko)의 비용 0. */
        if (!lang && !regText.length && !regHtml.length) return;
        try { applyHtml(lang); } catch (e) {}
        /* 1) 등록분 재렌더 */
        for (var k = 0; k < regText.length; k++) {
            var r = regText[k];
            if (!r.node.isConnected) continue;
            var row0 = MAP[r.key];
            r.node.nodeValue = (lang && row0 && row0[lang]) ? renderText(r.raw, r.key, row0[lang]) : r.raw;
        }
        if (!lang) { applied++; return 0; }
        /* 2) 신규 스캔 — 게임이 나중에 다시 그린 노드를 잡는다. */
        var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
        var node, hits = 0;
        var pending = [];
        while ((node = walker.nextNode())) {
            var raw = node.nodeValue;
            if (!raw || !/[가-힣]/.test(raw)) continue;   /* 한글이 없으면 건너뜀 */
            if (textSeen(node)) continue;                 /* 등록분은 위에서 처리 */
            var key = raw.replace(/\s+/g, ' ').trim();
            var row = MAP[key];
            if (!row || !row[lang]) continue;
            var el = node.parentElement;
            if (!el || el.closest('.lp-game-about')) continue;   /* 의도적 한국어 SEO 콘텐츠 */
            if (el.closest('script,style,noscript,textarea')) continue;
            if (el.dataset && el.dataset.lpOrigHtml != null) continue; /* HTML 맵 관할 */
            pending.push([node, renderText(raw, key, row[lang]), raw, key]);
            hits++;
        }
        for (var i2 = 0; i2 < pending.length; i2++) {
            var p = pending[i2];
            regText.push({ node: p[0], raw: p[2], key: p[3] });
            if (seenText) seenText.add(p[0]);
            p[0].nodeValue = p[1];
        }
        applied++;
        return hits;
    }

    function boot() {
        apply();
        /* 게임이 자기 applyLanguage() 로 나중에 다시 그리는 경우가 있어 몇 번 더.
           MutationObserver 는 캔버스 게임에서 과도하게 발화해 쓰지 않는다. */
        setTimeout(apply, 400);
        setTimeout(apply, 1200);
        setTimeout(apply, 2500);
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
    else boot();

    /* 다른 탭에서 언어를 바꾼 경우 */
    window.addEventListener('storage', function (e) {
        if (e && e.key === 'luckyplz_lang') apply();
    });
    /* 같은 탭의 lang bar 전환 — storage 이벤트는 타 탭 전용이라
       이 신호(langBar.js 발행)가 없으면 리로드 전까지 혼종 화면. */
    document.addEventListener('lp:langchanged', function () {
        try { apply(); } catch (e) {}
    });

    window.LpGameText = { apply: apply, map: MAP };
})();
