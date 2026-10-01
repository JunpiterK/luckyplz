/* lpHelpText.js — 게임별 간단 도움말 (언어별 3~4줄). lpHelp(siteFooter) 가 ? 버튼 시트 맨 위에 보여 준다.
   키 = public/games/<id>/ 디렉토리명. 언어 ko·en·ja·zh·es·pt, 그 밖의 언어는 코드에서 en 폴백.
   t = 게임이 실제로 쓰는 표시명(상표 중립명 유지: 닷 러너·테트로미노 쌓기·브롤 런), l = 무엇을 / 어떻게 / 쓸모 있는 팁 한 줄. */
window.LP_HELP_TEXT = {
  'roulette': {
    ko: {t:'룰렛', l:['항목을 넣고 돌려서 딱 하나를 뽑아요','가운데 SPIN을 누르거나 휠을 스와이프해요','멈췄을 때 바늘이 가리킨 칸이 당첨','매번 독립이라 같은 항목이 또 나올 수 있어요']},
    en: {t:'Wheel Spinner', l:['Add options, spin, and get exactly one pick','Tap SPIN in the center or swipe the wheel','Whatever the pointer stops on wins','Every spin is independent, so repeats can happen']},
    ja: {t:'ルーレット', l:['候補を入れて回し、1つだけ選びます','中央のSPINを押すか、ホイールをスワイプ','止まったとき針が指したマスが当選','毎回独立なので、同じ項目が続くこともあります']},
    zh: {t:'轮盘', l:['输入选项，转一下只选出一个','点中间的 SPIN，或直接滑动转盘','停下时指针指向的格子就是结果','每次都独立，同一项可能连续出现']},
    es: {t:'Ruleta', l:['Añade opciones, gira y sale solo una','Toca SPIN en el centro o desliza la ruleta','Gana la casilla donde se detiene la aguja','Cada giro es independiente: puede repetirse']},
    pt: {t:'Roleta', l:['Adicione opções, gire e sai só uma','Toque em SPIN no centro ou deslize a roleta','Vence a casa onde o ponteiro parar','Cada giro é independente: pode repetir']}
  },
  'mahjong-tw': {
    ko: {t:'대만 마작', l:['16장을 들고 17장째로 면자 5개 + 머리 1개를 먼저 만들면 화료','패를 한 번 누르면 들고, 한 번 더 누르면 버려요 · 고른 패를 버렸을 때의 대기(聽)가 오른쪽 아래에 · 초록 점 = 버리면 聽牌','吃는 윗사람 패만, 碰·槓은 누구 패든 · 버튼은 8초 뒤 자동 過 · 꽃패는 자동 補花','점수는 底 300 + 台 × 100 포인트(돈 아님) · 첫 화면의 台 점수표 참고']},
    en: {t:'Taiwanese Mahjong', l:['Hold 16 tiles; the 17th completes 5 sets + 1 pair to win','Tap a tile to lift it, tap again to discard · the waits (聽) for that discard show at the bottom right · green dot = discard to be ready','Chow only from the player before you; pong/kong from anyone · buttons auto-pass after 8 s · flowers are replaced automatically','Points: base 300 + 100 per tai (no money) · see the Tai table on the start screen']},
    ja: {t:'台湾麻雀', l:['16枚を持ち、17枚目で5面子＋雀頭を先にそろえたら和了','牌をタップで持ち上げ、もう一度で捨てる・その牌を切ったときの待ち(聽)が右下に · 緑の点 = 切ると聴牌','チーは上家からだけ、ポン・カンは誰からでも・ボタンは8秒で自動パス・花牌は自動で補花','点数は底300＋台×100ポイント（お金なし）・最初の画面の台数表を参照']},
    zh: {t:'台灣麻將', l:['16 張起手，摸到第 17 張湊成五組＋一對就胡','點一張牌升起，再點一次打出 · 打這張會聽哪些牌顯示在右下 · 綠點 = 打出就聽牌','吃只能吃上家，碰槓不限 · 按鈕 8 秒後自動「過」· 花牌自動補花','積分：底 300＋每台 100（不涉及金錢）· 首頁可看台數表']},
    es: {t:'Mahjong Taiwanés', l:['Con 16 fichas, la 17.ª completa 5 grupos + 1 pareja para ganar','Toca una ficha para levantarla y otra vez para descartarla · abajo a la derecha ves las esperas (聽) · punto verde = descarte que te deja listo','Chow solo del jugador anterior; pong/kong de cualquiera · los botones pasan solos a los 8 s · flores automáticas','Puntos: base 300 + 100 por tai (sin dinero) · tabla de tai en la pantalla inicial']},
    pt: {t:'Mahjong Taiwanês', l:['Com 16 peças, a 17.ª completa 5 grupos + 1 par para vencer','Toque uma peça para erguê-la e de novo para descartar · as esperas (聽) aparecem no canto inferior direito · ponto verde = descarte que deixa pronto','Chow só do jogador anterior; pong/kong de qualquer um · botões passam sozinhos em 8 s · flores automáticas','Pontos: base 300 + 100 por tai (sem dinheiro) · veja a tabela de tai na tela inicial']}
  },
  'mahjong-solitaire': {
    ko: {t:'마작 솔리테어', l:['같은 패 두 장을 눌러 짝지어 판을 모두 비워요','위에 겹친 패가 없고 왼쪽·오른쪽 중 한쪽이 트인 패만 뗄 수 있어요','꽃패는 꽃패끼리, 계절패는 계절패끼리 아무거나 짝','막히면 섞기(풀리는 배치로) · 힌트 · 되돌리기, 두 손가락으로 확대']},
    en: {t:'Mahjong Solitaire', l:['Tap two identical tiles to pair them off and clear the table','A tile is free only if nothing sits on it and its left or right side is open','Any flower pairs with any flower, any season with any season','Stuck? Shuffle (always solvable), Hint or Undo; pinch to zoom']},
    ja: {t:'麻雀ソリティア', l:['同じ牌を2枚タップして取り、全部なくせばクリア','上に牌がなく、左右どちらかが空いている牌だけ取れます','花牌は花牌どうし、季節牌は季節牌どうしどれでもペア','詰まったらシャッフル・ヒント・戻す、2本指で拡大']},
    zh: {t:'麻将接龙', l:['点两张相同的牌配对消除，清空整个牌桌','上面没有压牌、且左右任一侧空着的牌才能取','花牌任两张、季节牌任两张都能配对','卡住时可洗牌（保证有解）、提示或撤销，两指放大']},
    es: {t:'Mahjong Solitario', l:['Toca dos fichas iguales para emparejarlas y vaciar la mesa','Solo están libres si nada las tapa y un lado (izq. o der.) está abierto','Cualquier flor con cualquier flor, cualquier estación con otra','¿Atascado? Mezclar (siempre resoluble), Pista o Deshacer; pellizca para zoom']},
    pt: {t:'Paciência Mahjong', l:['Toque em duas peças iguais para formar o par e limpar a mesa','Só estão livres se nada as cobre e um lado (esq. ou dir.) está aberto','Qualquer flor com qualquer flor, qualquer estação com outra','Travou? Embaralhar (sempre resolvível), Dica ou Desfazer; pinça para zoom']}
  },
  'bubble': {
    ko: {t:'버블 버스트', l:['같은 색 3개 이상 붙이면 펑 — 천장과 끊긴 덩어리는 와르르, 점수가 커요','끌어서 조준하고 떼면 발사 · 조준선은 벽 한 번까지 착지 칸을 보여줘요','짝수 판은 아기 판다 구출 · 얼음 버블은 두 번 맞아야 녹아요','헛방이 쌓이면 새 줄 · 적은 발 수로 깨면 별 3개 · 작은 버블을 눌러 교체']},
    en: {t:'Bubble Burst', l:['Touch 3+ of one colour to pop — anything cut off from the ceiling drops for big points','Drag to aim, release to shoot · the guide shows the landing cell (up to one wall bounce)','Even stages: rescue the baby pandas · ice bubbles need two hits','Misses bring a new row · fewer shots = more stars · tap the small bubble to swap']},
    ja: {t:'バブルバースト', l:['同じ色を3つ以上つなげるとポン · 天井から切れた塊はまとめて落ちて高得点','ドラッグで狙って離すと発射 · ガイドは壁1回まで着地点を表示','偶数ステージは赤ちゃんパンダ救出 · 氷バブルは2回当てると溶ける','ミスが続くと新しい列 · 少ない手数で星3つ · 小さいバブルで交換']},
    zh: {t:'泡泡爆破', l:['三个以上同色相连就爆 · 与顶部断开的整串掉落，分数更高','拖动瞄准，松开发射 · 辅助线显示落点（最多反弹一次）','偶数关救出小熊猫 · 冰泡泡要打两次才会融化','失误多了会压下新一行 · 用越少的球过关星越多 · 点小泡泡交换']},
    es: {t:'Revienta Burbujas', l:['Junta 3+ del mismo color para reventar · lo que se suelta del techo cae y da más puntos','Arrastra para apuntar y suelta para disparar · la guía marca dónde cae (hasta un rebote)','Niveles pares: rescata a los pandas bebé · las burbujas de hielo necesitan dos golpes','Si fallas baja una fila · menos disparos = más estrellas · toca la burbuja pequeña para cambiar']},
    pt: {t:'Estoura Bolhas', l:['Junte 3+ da mesma cor para estourar · o que se solta do teto cai e vale mais','Arraste para mirar e solte para atirar · a guia mostra onde para (até uma tabela)','Fases pares: resgate os pandinhas · bolhas de gelo precisam de dois acertos','Errou muito? Desce uma fileira · menos tiros = mais estrelas · toque na bolha pequena para trocar']}
  },
  'yacht': {
    ko: {t:'요트 다이스', l:['주사위 5개를 한 차례에 세 번까지 굴려 12칸 중 한 칸에 적어요 · 12라운드 합계 1등이 승리','굴리기를 꾹 눌러 흔들고 떼면 던져요 · 남길 주사위를 누르면 위 칸에 고정','칸을 누르고 한 번 더(또는 노란 버튼) 누르면 확정 · 맞는 칸이 없으면 0점으로 지워야 해요','1~6의 눈 합 63점 이상이면 +35 · 💡 힌트를 켜면 가장 좋은 선택을 보여 줘요']},
    en: {t:'Yacht Dice', l:['Roll five dice up to three times, then score one of 12 boxes · highest total after 12 rounds wins','Hold Roll to shake the cup, release to throw · tap dice to keep them on the rail','Tap a box, then tap again (or the yellow button) to score · no match means writing a 0','Upper boxes totalling 63+ give +35 · turn on 💡 hints to see the best move']},
    ja: {t:'ヨットダイス', l:['サイコロ5個を1ターン3回まで振り、12マスのどれかに記入 · 12ラウンドの合計で勝負','振るボタン長押しでカップを振り、離すと投げる · 残すサイコロをタップで上にキープ','マスをタップしてもう一度（または黄色ボタン）で確定 · 合うマスがなければ0点で消す','1〜6の合計63点以上で+35 · 💡ヒントでおすすめを表示']},
    zh: {t:'快艇骰子', l:['每回合最多掷三次五颗骰子，选十二格之一记分 · 十二轮后总分最高者胜','长按掷骰摇骰盅，松开掷出 · 点骰子可保留到上方','点一格再点一次（或黄色按钮）确认 · 没有合适的格就要记0分','一到六点合计63分以上奖励+35 · 打开💡提示可看最佳选择']},
    es: {t:'Yacht Dice', l:['Tira cinco dados hasta tres veces y anota en una de 12 casillas · gana el mayor total tras 12 rondas','Mantén Tirar para agitar el cubilete y suelta para lanzar · toca los dados para guardarlos','Toca una casilla y otra vez (o el botón amarillo) para anotar · si nada encaja, anotas un 0','Si la parte de arriba suma 63+ ganas +35 · activa 💡 para ver la mejor jugada']},
    pt: {t:'Yacht Dice', l:['Role cinco dados até três vezes e anote em uma de 12 casas · vence o maior total após 12 rodadas','Segure Rolar para chacoalhar o copo e solte para lançar · toque nos dados para segurá-los','Toque numa casa e de novo (ou o botão amarelo) para anotar · sem combinação, anota-se 0','Se a parte de cima somar 63+ ganha +35 · ligue 💡 para ver a melhor jogada']}
  },
  'omok': {
    ko: {t:'오목', l:['가로·세로·대각선으로 내 돌 다섯 개를 먼저 이으면 승리','규칙: 자유(제한 없음) · 표준(정확히 다섯만) · 렌주(흑만 3-3·4-4·장목 금지, 금수는 ✕ 표시)','AI는 레서판다 가족 — 콩이·단풍·아빠·할배 순으로 강해져요','위협 표시를 켜면 열린 3·4 자리가 보여요 · 무르기로 한 수 되돌리기']},
    en: {t:'Gomoku', l:['Line up five of your stones in a row — across, down or diagonal — first to win','Rules: Free (anything goes) · Standard (exactly five) · Renju (Black may not make 3-3, 4-4 or overlines; forbidden points show ✕)','AI is a red-panda family — Kong, Maple, Papa, Grandpa, from easy to expert','Threats shows open threes and fours · Undo takes back a move']},
    ja: {t:'五目並べ', l:['縦・横・斜めに自分の石を先に五つ並べたら勝ち','ルール: 自由(制限なし) · 標準(ちょうど五つ) · 連珠(黒のみ三三・四四・長連が禁手、禁点は✕表示)','AIはレッサーパンダ一家 — コン・もみじ・パパ・じいじの順に強くなります','脅威表示で活三・四の場所が見えます · 待ったで一手戻せます']},
    zh: {t:'五子棋', l:['横、竖、斜任一方向先连成五子即获胜','规则：自由（无限制）· 标准（恰好五子）· 连珠（仅黑棋禁三三、四四、长连，禁手点显示✕）','电脑是小熊猫一家：豆豆、小枫、熊猫爸爸、爷爷，依次变强','开启威胁提示可看到活三、冲四位置 · 悔棋可退回一步']},
    es: {t:'Gomoku', l:['Alinea cinco de tus piedras en fila — horizontal, vertical o diagonal — y ganas','Reglas: Libre (todo vale) · Estándar (exactamente cinco) · Renju (las negras no pueden hacer 3-3, 4-4 ni seis; los puntos prohibidos muestran ✕)','La IA es una familia de pandas rojos — Kong, Arce, Papá y Abuelo, de fácil a experto','Amenazas muestra treses y cuatros abiertos · Deshacer retira una jugada']},
    pt: {t:'Gomoku', l:['Alinhe cinco das suas pedras em fila — horizontal, vertical ou diagonal — e vença','Regras: Livre (vale tudo) · Padrão (exatamente cinco) · Renju (as pretas não podem fazer 3-3, 4-4 nem seis; pontos proibidos mostram ✕)','A IA é uma família de pandas-vermelhos — Kong, Bordo, Papai e Vovô, do fácil ao mestre','Ameaças mostra trincas e quadras abertas · Desfazer volta uma jogada']}
  },
  'janggi': {
    ko: {t:'장기 · 象棋', l:['상대 장을 피할 수 없게 몰면(외통) 승리 · 위쪽 버튼으로 장기/象棋 선택','장기: 궁성 대각선 · 포는 꼭 한 말을 넘고 포는 못 넘음 · 장군 아니면 한수쉼 · 빅장을 안 풀면 점수(한 +1.5)','象棋: 강 · 장끼리 마주보기 금지 · 둘 수 없으면(궁지) 패 · 같은 국면 3번에 한쪽만 계속 장군이면 그쪽 패','말을 누르면 갈 곳이 점으로 · 💡 힌트는 추천 수 화살표 · AI는 콩이·단풍·아빠·할배']},
    en: {t:'Janggi & Xiangqi', l:['Trap the enemy general so it cannot escape (checkmate) · pick Janggi or Xiangqi at the top','Janggi: palace diagonals · cannons must jump exactly one piece, never a cannon · pass when not in check · unbroken bikjang ends on points (Han +1.5)','Xiangqi: river · generals may not face each other · no legal move (stalemate) loses · perpetual check over a 3-fold repetition loses','Tap a piece to see its moves · 💡 Hint shows a suggested move · AI: Kong, Maple, Papa, Grandpa']},
    ja: {t:'チャンギ・シャンチー', l:['相手の将を逃げられなくすれば(詰み)勝ち · 上でチャンギ/シャンチーを選択','チャンギ: 宮の斜め線 · 包は必ず1枚越え、包は越えない · 王手でなければパス可 · 将の対面を解かないと点数(漢 +1.5)','シャンチー: 河 · 将同士の対面禁止 · 指せなければ(手詰まり)負け · 同一局面3回で一方だけ王手を続けたらその側の負け','駒をタップで動ける点 · 💡ヒントでおすすめの手 · AIはコン・もみじ・パパ・じいじ']},
    zh: {t:'象棋', l:['把对方将帅逼到无路可走(将死)即胜 · 顶部可选象棋或韩国将棋','韩国将棋：九宫斜线 · 包必须隔一子且不能越包 · 未被将军可停一手 · 将帅对面不化解则计分(汉 +1.5)','象棋：楚河汉界 · 将帅不能照面 · 无子可动(困毙)判负 · 同一局面三次且一方一直将军，该方判负','点棋子显示可走位置 · 💡提示显示推荐着法 · 电脑：豆豆、小枫、熊猫爸爸、爷爷']},
    es: {t:'Janggi y Xiangqi', l:['Acorrala al general rival sin escape (jaque mate) · elige Janggi o Xiangqi arriba','Janggi: diagonales del palacio · el cañón salta exactamente una pieza, nunca un cañón · se puede pasar sin jaque · bikjang sin romper se decide por puntos (Han +1,5)','Xiangqi: río · los generales no pueden verse · sin jugadas (ahogado) pierde · jaque perpetuo en triple repetición pierde','Toca una pieza para ver sus jugadas · 💡 Pista muestra una jugada · IA: Kong, Arce, Papá, Abuelo']},
    pt: {t:'Janggi e Xiangqi', l:['Encurrale o general rival sem saída (xeque-mate) · escolha Janggi ou Xiangqi no topo','Janggi: diagonais do palácio · canhão salta exatamente uma peça, nunca um canhão · pode passar sem xeque · bikjang não desfeito vai a pontos (Han +1,5)','Xiangqi: rio · generais não podem se encarar · sem lances (afogamento) perde · xeque perpétuo em tripla repetição perde','Toque numa peça para ver os lances · 💡 Dica mostra uma jogada · IA: Kong, Bordo, Papai, Vovô']}
  },
  'lots': {
    ko: {t:'긁는 제비뽑기', l:['이름(또는 개수)과 제비 속 내용(당첨·벌칙·역할·순서·직접)을 정하고 나눠주기','제비를 눌러 손가락으로 은박을 긁기 — 절반 넘게 긁으면 자동 공개','결과는 나눠줄 때 이미 정해져요 · 몇 번째로 긁든 확률은 같아요','🥁 다 같이 공개로 남은 제비를 한 장씩 · 👥 같이 보기는 링크로 각자 폰에서']},
    en: {t:'Scratch Lots', l:['Set names (or a count) and what’s inside — win, forfeit, roles, order or custom — then deal','Tap a lot and scratch the foil with your finger; past half it reveals itself','Results are fixed the moment you deal · every position has the same odds','🥁 Reveal all opens the rest one by one · 👥 Watch together lets friends join by link']},
    ja: {t:'スクラッチくじ', l:['名前(または枚数)と中身(当たり・罰ゲーム・役割・順番・自由)を決めて配る','くじをタップして指で銀紙を削る — 半分以上削ると自動で開く','結果は配った瞬間に決まっています · 何番目に削っても確率は同じ','🥁 一斉に開封で残りを1枚ずつ · 👥 みんなで見るはリンクで各自のスマホから']},
    zh: {t:'刮刮签', l:['设定名字(或数量)和签里的内容(中签·惩罚·分工·顺序·自定义)后发签','点一张签，用手指刮开银箔 — 刮过一半自动揭晓','结果在发签时就已确定 · 第几个刮概率都一样','🥁 一起揭晓逐张打开剩下的签 · 👥 一起看可通过链接各自用手机参加']},
    es: {t:'Sorteo para rascar', l:['Pon nombres (o una cantidad) y qué hay dentro — premio, castigo, tareas, orden o libre — y reparte','Toca un boleto y rasca la lámina con el dedo; pasada la mitad se revela solo','El resultado se fija al repartir · todos tienen la misma probabilidad','🥁 Revelar todos abre el resto uno a uno · 👥 Ver juntos: cada uno desde su móvil con un enlace']},
    pt: {t:'Sorteio de raspar', l:['Defina nomes (ou uma quantidade) e o que tem dentro — prêmio, castigo, tarefas, ordem ou livre — e distribua','Toque num bilhete e raspe a película com o dedo; passando da metade ele se revela','O resultado é fixado ao distribuir · a chance é igual para todos','🥁 Revelar todos abre o resto um a um · 👥 Ver juntos: cada um no seu celular pelo link']}
  },
  'ludo': {
    ko: {t:'루도', l:['주사위를 굴려 말 4개를 먼저 가운데 집에 넣으면 승리','6이 나와야 출발, 6이면 한 번 더 · 상대 말 위에 멈추면 잡기','별 칸·출발칸은 안전 · 갈 말이 하나면 자동 이동(설정에서 끄기)','봇 성격: 레서판다 돌격 · 고양이 신중 · 여우 질주 · 수달 균형']},
    en: {t:'Ludo', l:['Roll the dice and race all 4 tokens into the center home','Roll a 6 to leave base; a 6 rolls again. Land on a rival to capture','Stars and start squares are safe · a single movable token moves itself (toggle in setup)','Bot styles: Red Panda attacks · Cat plays safe · Fox races · Otter balances']},
    ja: {t:'ルドー', l:['サイコロを振り、4つのコマを先に中央のゴールへ','6で出発、6ならもう一回 · 相手のコマに止まると取れる','星マスとスタートは安全 · 動かせるコマが1つなら自動(設定でオフ)','ボットの性格: レッサーパンダ突撃 · ネコ慎重 · キツネ疾走 · カワウソ均衡']},
    zh: {t:'鲁多棋', l:['掷骰子，先把四枚棋子全部送进中央的家','掷出6才能出发，6可再掷 · 停在对手棋子上即可吃掉','星格和起点格安全 · 只有一枚可走时自动移动(可在设置关闭)','电脑性格：小熊猫进攻 · 猫咪谨慎 · 狐狸冲刺 · 水獭均衡']},
    es: {t:'Ludo', l:['Tira el dado y lleva tus 4 fichas a la casa central','Sal con un 6; el 6 repite. Cae sobre un rival para comerlo','Estrellas y salidas son seguras · si solo una ficha puede mover, se mueve sola (ajustes)','Estilos: Panda rojo ataca · Gato prudente · Zorro veloz · Nutria equilibrada']},
    pt: {t:'Ludo', l:['Jogue o dado e leve suas 4 peças à casa central','Saia com um 6; o 6 joga de novo. Pare no rival para capturar','Estrelas e saídas são seguras · se só uma peça puder andar, anda sozinha (ajustes)','Estilos: Panda-vermelho ataca · Gato cauteloso · Raposa veloz · Lontra equilibrada']}
  },
  'reversi': {
    ko: {t:'리버시', l:['상대 돌을 내 돌 사이에 끼우면 전부 내 색으로 뒤집혀요','AI는 레서판다 가족 — 콩이(쉬움)·단풍(보통)·아빠(어려움)·할배(고수)','힌트 버튼: 점 → 뒤집는 개수 → 끔 · 💡 코치 팁은 설정에서','모서리는 절대 안 뒤집혀요 — 모서리 옆 대각선 칸은 피하세요']},
    en: {t:'Reversi', l:['Sandwich opponent discs between yours to flip them all','AI is a red-panda family — Kong (Easy), Maple (Normal), Papa (Hard), Grandpa (Expert)','Hint button: dots → flip counts → off · 💡 Coach tips in setup','Corners never flip: avoid the diagonal square next to one']},
    ja: {t:'リバーシ', l:['相手の石を自分の石で挟むと全部ひっくり返ります','AIはレッサーパンダ一家 — コン(かんたん)・もみじ(ふつう)・パパ(むずかしい)・じいじ(達人)','ヒントボタン: 点 → 返す枚数 → オフ · 💡コーチは設定で','角は二度と返されません。角の斜め隣は避けましょう']},
    zh: {t:'黑白棋', l:['用自己的棋子夹住对方棋子，就能全部翻成己色','AI是小熊猫一家：豆豆(简单)·小枫(普通)·熊猫爸爸(困难)·爷爷(高手)','提示按钮：圆点 → 可翻数量 → 关闭 · 💡教练提示在设置里','角上的棋子永远不会被翻，避开角的斜邻格']},
    es: {t:'Reversi', l:['Encierra fichas rivales entre las tuyas y se voltean','La IA es una familia de pandas rojos — Kong (Fácil), Arce (Normal), Papá (Difícil), Abuelo (Experto)','Botón de pistas: puntos → cuántas voltea → apagado · 💡 Consejos en ajustes','Las esquinas nunca se voltean: evita la casilla diagonal vecina']},
    pt: {t:'Reversi', l:['Cerque peças rivais entre as suas e todas viram','A IA é uma família de pandas-vermelhos — Kong (Fácil), Bordo (Normal), Papai (Difícil), Vovô (Mestre)','Botão de dicas: pontos → quantas vira → desligado · 💡 Dicas nos ajustes','Cantos nunca viram: evite a casa diagonal ao lado deles']}
  },
  'yut': {
    ko: {t:'윷놀이', l:['2~4팀이 윷을 던져 말을 먼저 모두 내보내면 승리','윷 던지기 → 말을 누르고 빛나는 칸을 눌러 이동','윷·모는 한 번 더, 도·개·걸로 잡아도 한 번 더 · 모서리·방에 멈추면 지름길','온라인: 초대 링크 → 각자 캐릭터 고르고 「준비」 → 방장이 시작 · 시간을 넘기면 자동으로 둬요']},
    en: {t:'Yut Nori', l:['2–4 teams race to bring all their pieces home','Throw the sticks, tap a piece, then tap a glowing spot','Yut/Mo = throw again; a capture with Do/Gae/Geol too · corners give shortcuts','Online: share the link → each picks a character and taps Ready → host starts; slow turns auto-play']},
    ja: {t:'ユンノリ', l:['2〜4チームで、先に全部のコマをゴールさせたら勝ち','棒を投げる → コマをタップ → 光るマスをタップ','ユッ・モはもう一回、ト・ケ・コルで取ってももう一回。角で止まると近道','オンライン：リンクを送る → 各自キャラを選んで「準備OK」→ ホストが開始・時間切れは自動で進行']},
    zh: {t:'掷柶(尤茨)', l:['2–4队比赛，先让所有棋子走完一圈的队获胜','掷柶 → 点棋子 → 点发光的格子移动','掷出4步、5步再掷一次；用1-3步吃子也再掷；停在角上可抄近路','在线：发送链接 → 各自选角色并点“准备” → 房主开始；超时会自动走棋']},
    es: {t:'Yut Nori', l:['2–4 equipos: gana quien saque primero todas sus fichas','Lanza los palos, toca una ficha y luego la casilla brillante','Yut/Mo = otro tiro; capturar con Do/Gae/Geol también · esquina = atajo','Online: comparte el enlace → cada uno elige personaje y pulsa Listo → empieza el anfitrión; si se acaba el tiempo, juega solo']},
    pt: {t:'Yut Nori', l:['2–4 times: vence quem levar todas as peças para casa primeiro','Jogue os palitos, toque na peça e depois na casa brilhante','Yut/Mo = joga de novo; capturar com Do/Gae/Geol também · canto = atalho','Online: envie o link → cada um escolhe o personagem e toca em Pronto → o anfitrião começa; tempo esgotado joga sozinho']}
  },
  'prism-hex': {
    ko: {t:'프리즘 헥스', l:['보석 블록 18개를 판에 최대한 많이 놓으면 승리 — 남은 칸이 적은 순','첫 블록은 ★ 시작 칸, 같은 색은 변이 닿으면 안 되고 꼭짓점 다리로만 연결','블록 고르기 → 판 누르기(착지) → 한 번 더 누르면 놓기 · 두 손가락으로 확대','봇 실력 쉬움·보통·어려움 · 한 판 더는 직전 꼴찌가 먼저']},
    en: {t:'Prism Hex', l:['Place as many of your 18 gem blocks as you can — fewest cells left wins','First block covers your ★ start; same colors never share an edge, only a corner bridge','Pick a block, tap the board to land it, tap again to place · pinch to zoom','Bot level Easy/Normal/Hard · on a rematch the last-place player starts']},
    ja: {t:'プリズムヘックス', l:['宝石ブロック18個をできるだけ多く置く — 残りマスが少ない人の勝ち','最初は★スタートマス、同じ色は辺で接さず角のブリッジでだけつなぐ','ブロックを選ぶ → 盤をタップで仮置き → もう一度タップで確定 · 2本指で拡大','ボットの強さ やさしい・ふつう・つよい · もう一回は前回最下位から']},
    zh: {t:'棱镜六角棋', l:['尽量把18块宝石积木放上棋盘，剩余格数最少者获胜','第一块盖住★起点；同色不能边对边，只能用角上的桥相连','选积木 → 点棋盘先放下 → 再点一次确定 · 双指缩放','电脑难度 简单/普通/困难 · 再来一局由上局最后一名先手']},
    es: {t:'Prism Hex', l:['Coloca todos los bloques de gemas que puedas: gana quien deje menos celdas','El primero cubre tu ★; el mismo color nunca comparte lado, solo un puente de esquina','Elige un bloque, toca el tablero para posarlo y otra vez para colocar · pellizca para ampliar','Nivel del bot Fácil/Normal/Difícil · en la revancha empieza el último']},
    pt: {t:'Prism Hex', l:['Coloque o máximo dos 18 blocos de gemas: vence quem sobrar menos casas','O primeiro cobre sua ★; a mesma cor nunca encosta pelo lado, só por uma ponte de canto','Escolha um bloco, toque no tabuleiro para pousar e de novo para colocar · pinça para zoom','Nível do robô Fácil/Normal/Difícil · na revanche começa o último colocado']}
  },
  'gummy': {
    ko: {t:'구미 체인', l:['같은 색 젤리 4개 이상을 이으면 터져요','떨어져서 또 터지면 연쇄 — 점수가 크게 뛰어요','대전에선 연쇄가 설탕 블록 공격, 내 연쇄로 예고분을 상쇄','3열 맨 윗칸이 막히면 패배']},
    en: {t:'Gummy Chain', l:['Link 4+ gummies of one color to pop them','Pops that cause more pops are chains — big score','In versus, chains send sugar blocks; your chains cancel incoming ones','Lose when the top of column 3 is blocked']},
    ja: {t:'グミチェイン', l:['同じ色を4つ以上つなげると消える','落ちてまた消えれば連鎖、得点が大きく伸びる','対戦では連鎖が砂糖ブロック攻撃、自分の連鎖で予告を相殺','3列目のいちばん上が埋まると負け']},
    zh: {t:'软糖连锁', l:['同色软糖4个以上相连即消除','落下后再次消除即连锁，分数大增','对战中连锁会发送糖块，自己的连锁可抵消预告','第3列最上方被堵住即失败']},
    es: {t:'Gummy Chain', l:['Une 4+ gominolas del mismo color para explotarlas','Si lo que cae vuelve a explotar es una cadena: muchos puntos','En duelo las cadenas envían bloques de azúcar; las tuyas anulan los que llegan','Pierdes si se llena la parte alta de la columna 3']},
    pt: {t:'Gummy Chain', l:['Ligue 4+ balas da mesma cor para estourar','Se o que cai estourar de novo é uma corrente: muitos pontos','No duelo, correntes enviam blocos de açúcar; as suas anulam os que chegam','Perde quando o topo da coluna 3 fica bloqueado']}
  },
  'team': {
    ko: {t:'팀 뽑기', l:['가챠 기계가 캡슐을 한 팀씩 뽑아 줘요','참가자와 팀 수(또는 팀당 인원)를 정하고 시작','같이 보기: 메신저 링크로 각자 폰에서 함께 봐요','실력 차가 크면 티어 밸런스 모드를 쓰세요']},
    en: {t:'Team Picker', l:['A gacha machine pops out capsules, team by team','Set players and teams (or people per team), then start','Watch together: others follow live via a chat-app link','Uneven skill? Use Skill balanced mode']},
    ja: {t:'チーム分け', l:['ガチャマシンがカプセルを1チームずつ出します','参加者とチーム数（または1チームの人数）を決めて開始','みんなで見る：リンクを送れば各自のスマホで同時に見られます','実力差があるなら「実力で均等」モードを']},
    zh: {t:'分队抽签', l:['扭蛋机一队一队地吐出胶囊','设定人数和队数（或每队人数）后开始','一起看：发链接，大家在自己手机上同步观看','水平差距大时，用“等级平衡”模式']},
    es: {t:'Sorteo de Equipos', l:['Una máquina gacha saca cápsulas, equipo por equipo','Pon jugadores y equipos (o personas por equipo) y empieza','Ver juntos: con un enlace, los demás lo siguen en su móvil','¿Niveles dispares? Usa el modo Por Nivel']},
    pt: {t:'Sorteio de Times', l:['Uma máquina gacha solta cápsulas, time por time','Defina jogadores e times (ou pessoas por time) e comece','Ver juntos: com um link, todos assistem no próprio celular','Níveis bem diferentes? Use o modo Por Nível']}
  },
  'dice': {
    ko: {t:'주사위 배틀', l:['퀵 롤: 한 번 굴려 바로 승부','낮은 숫자와 높은 숫자 중 어느 쪽이 질지 정해요','돼지 게임: 굴려서 점수를 쌓되 1이 나오면 그 턴 0점','돼지 게임은 한 턴 20점쯤에서 멈추는 게 유리해요']},
    en: {t:'Dice Battle', l:['Quick Roll: one roll settles it','Choose whether the lowest or the highest number loses','Pig Game: keep rolling to build points, but a 1 wipes the turn','In Pig, holding at about 20 points a turn pays off best']},
    ja: {t:'サイコロバトル', l:['クイックロール：1回振って即決着','小さい目と大きい目、どちらが負けか選べます','ピッグゲーム：振って点を貯め、1が出たらそのターン0点','ピッグは1ターン20点前後で止めるのが有利']},
    zh: {t:'骰子大战', l:['快速掷：掷一次立刻分胜负','可设定点数最低输还是最高输','猪游戏：连续掷骰累积分数，掷出1本回合清零','猪游戏里每回合攒到20分左右就停，最划算']},
    es: {t:'Batalla de Dados', l:['Tiro Rápido: una tirada y se decide','Elige si pierde el número menor o el mayor','Juego del Cerdo: tira para sumar, pero un 1 borra el turno','En el Cerdo, plantarse cerca de 20 por turno rinde más']},
    pt: {t:'Batalha de Dados', l:['Lançamento Rápido: uma jogada decide','Escolha se perde o número menor ou o maior','Jogo do Porco: role para somar, mas um 1 zera a vez','No Porco, parar perto de 20 pontos por vez rende mais']}
  },
  'bingo': {
    ko: {t:'빙고', l:['방을 만들면 친구들은 링크로 자기 폰에서 참가해요','판 크기(3×3~6×6)와 수동·자동 뽑기를 골라요','성공 줄 수·당첨자 수로 한 판 길이를 조절해요','종이 빙고판을 쓴다면 📋 오프라인 = 번호 호출만']},
    en: {t:'Bingo', l:['Host a room; friends join by link and get cards on their phones','Pick a grid (3×3 to 6×6) and manual or auto draws','Set lines to win and number of winners to control length','Playing on paper cards? 📋 Offline just calls the numbers']},
    ja: {t:'ビンゴ', l:['ルームを作ると、友だちはリンクから自分のスマホで参加','盤の大きさ（3×3〜6×6）と手動・自動の抽選を選択','勝利ライン数と当選人数で1回の長さを調整','紙のビンゴカードなら 📋 オフライン＝番号の読み上げだけ']},
    zh: {t:'宾果', l:['开房间后，朋友用链接在自己手机上加入','选择卡片大小（3×3～6×6）和手动或自动抽号','用获胜线数和中奖人数控制一局的长度','用纸质宾果卡时，选 📋 离线，只负责叫号']},
    es: {t:'Bingo', l:['Crea una sala; tus amigos entran con el enlace desde su móvil','Elige el cartón (3×3 a 6×6) y sorteo manual o automático','Ajusta líneas para ganar y número de ganadores','¿Cartones de papel? 📋 Sin conexión solo canta los números']},
    pt: {t:'Bingo', l:['Crie uma sala; os amigos entram pelo link no próprio celular','Escolha a cartela (3×3 a 6×6) e sorteio manual ou automático','Ajuste linhas para vencer e número de ganhadores','Cartelas de papel? 📋 Offline só canta os números']}
  },
  'car-racing': {
    ko: {t:'카레이싱', l:['이름을 넣으면 차들이 달려 전원의 순위가 한 번에 나와요','고급 설정: 코스·경주 시간·바퀴 수·이벤트 빈도','보상 설정으로 순위별 금액 분배나 할 일을 붙여요','출발 전에 각자 자기 차를 찾아 두면 훨씬 재밌어요']},
    en: {t:'Car Racing', l:['Enter names; the cars race and the finish ranks everyone','Advanced: course, race time, laps and event frequency','Rewards: split a bill or assign tasks by finishing place','Have everyone spot their own car before the start']},
    ja: {t:'カーレース', l:['名前を入れると車が走り、全員の順位が一度に決まります','詳細設定：コース・レース時間・周回数・イベント頻度','報酬設定で順位ごとの金額配分や役割を付けられます','スタート前に各自が自分の車を見つけておくと盛り上がります']},
    zh: {t:'赛车', l:['输入名字，赛车跑完就排出所有人的名次','高级设置：赛道、比赛时间、圈数、事件频率','奖励设置：按名次分摊金额或分配任务','开跑前让每个人先找到自己的车，更好看']},
    es: {t:'Carrera', l:['Escribe nombres; los coches corren y la meta ordena a todos','Avanzado: circuito, duración, vueltas y frecuencia de eventos','Premios: reparte una cuenta o tareas según el puesto','Que cada uno localice su coche antes de la salida']},
    pt: {t:'Corrida', l:['Digite nomes; os carros correm e a chegada ordena todos','Avançado: pista, duração, voltas e frequência de eventos','Prêmios: divida a conta ou tarefas pela colocação','Peça para cada um achar o próprio carro antes da largada']}
  },
  'ladder': {
    ko: {t:'사다리타기', l:['참가자 수만큼 결과(벌칙·보상)를 적어요','프리셋(🍺 음주·💰 계산·🧹 집안일·🎭 벌칙)으로 빠르게 채우기','진행 방식: 순서대로(1번부터)·동시에 · 시작할 때 결과 위치를 섞어 누구나 같은 확률','같은 사다리에서 두 사람이 같은 결과에 닿는 일은 없어요']},
    en: {t:'Ladder Game', l:['Write one result (dare or prize) per player','Presets fill results fast: drinks, pay, chores, dares','Reveal in sequence or all at once · result slots are shuffled at Start, so everyone has equal odds','No two starting points ever reach the same result']},
    ja: {t:'あみだくじ', l:['参加者と同じ数だけ結果（罰ゲーム・ごほうび）を書きます','プリセット（飲み・支払い・家事・罰ゲーム）ですぐ埋まります','進め方：順番に・全員同時 · スタート時に結果の位置をシャッフルするので全員同じ確率','同じくじで2人が同じ結果に着くことはありません']},
    zh: {t:'爬梯子', l:['写下和人数一样多的结果（惩罚或奖励）','用预设（喝酒、买单、家务、惩罚）快速填好','进行方式：按顺序或同时 · 开始时打乱结果位置，人人机会均等','同一张梯子上，两个人不会走到同一个结果']},
    es: {t:'Juego de Escalera', l:['Escribe un resultado (castigo o premio) por jugador','Los preajustes rellenan rápido: tragos, pagar, tareas, retos','Revela en secuencia o todos a la vez · al empezar se mezclan los resultados: misma probabilidad para todos','Dos puntos de salida nunca llegan al mismo resultado']},
    pt: {t:'Jogo da Escada', l:['Escreva um resultado (castigo ou prêmio) por jogador','Predefinições preenchem rápido: bebida, conta, tarefas, desafios','Revele em sequência ou todos juntos · ao começar os resultados são embaralhados: mesma chance para todos','Dois pontos de partida nunca chegam ao mesmo resultado']}
  },
  'glory-racing': {
    ko: {t:'브롤 런', l:['이름을 넣으면 캐릭터들이 달리고 몸싸움하며 순위를 가려요','? 상자에서 아이템이 나와요 — 선두일수록 꽝이 잦아요','바위 구간에선 0~2번 넘어져 막판까지 뒤집혀요','경주 시간·속도·이벤트 빈도는 설정에서 바꿔요']},
    en: {t:'Brawl Run', l:['Runners race and brawl; the finish order is the result','Items come from ? boxes, and leaders draw more duds','Rocky stretches trip runners 0–2 times, so leads flip late','Change race time, speed and event rate in setup']},
    ja: {t:'ブロールラン', l:['名前を入れるとキャラが走り、もみ合いながら順位が決まります','？箱からアイテム。先頭ほどハズレが出やすい','岩場では0〜2回転ぶので、終盤まで逆転があります','レース時間・速度・イベント頻度は設定で変更']},
    zh: {t:'混战跑酷', l:['输入名字，角色边跑边推挤，冲线顺序就是结果','道具来自？箱子，领先者更容易抽到坏道具','岩石路段会摔倒0～2次，最后阶段也能逆转','比赛时间、速度和事件频率可在设置里调整']},
    es: {t:'Brawl Run', l:['Los corredores compiten a empujones; manda el orden de llegada','Los objetos salen de cajas ?; el que lidera saca más fallos','En las rocas se caen de 0 a 2 veces: hay vuelcos al final','Cambia duración, velocidad y frecuencia de eventos al inicio']},
    pt: {t:'Brawl Run', l:['Os corredores disputam no empurrão; vale a ordem de chegada','Itens saem das caixas ?; quem lidera tira mais itens ruins','Nas pedras caem de 0 a 2 vezes, então vira até o fim','Mude duração, velocidade e frequência de eventos no início']}
  },
  'balloon': {
    ko: {t:'풍선 룰렛', l:['돌아가며 펌프 — 풍선을 터뜨린 사람이 벌칙','한 턴에 최소 1번, 더 누를지는 배짱. 그다음 넘겨요','터지는 지점은 숨어 있어요: 첫 펌프에도, 30번 넘어서도','크기·게이지는 단서가 아니에요. 이름은 비워도 돼요']},
    en: {t:'Balloon Pop', l:['Take turns pumping; whoever pops the balloon loses','At least 1 pump per turn, more if you dare, then pass','Each balloon hides its burst point: pump 1 or past 30','Size and gauge are not clues. Names can stay blank']},
    ja: {t:'風船ルーレット', l:['順番にポンプ。風船を割った人が罰ゲーム','1ターン最低1回、あとは度胸次第で押して次へ','割れる回数は風船ごとに秘密：1回目でも、30回超えでも','大きさやゲージは手がかりになりません。名前は空欄でもOK']},
    zh: {t:'气球轮盘', l:['轮流打气，把气球打爆的人受罚','每回合至少打1次，敢不敢多打看胆量，然后传给下一位','每个气球的爆点都是隐藏的：第1下或30下以后都可能','大小和气压表都不是线索。名字可以留空']},
    es: {t:'Revienta Globos', l:['Inflen por turnos: quien revienta el globo pierde','Mínimo 1 bombeo por turno; sigue si te atreves y pasa','Cada globo esconde su punto: puede ser el 1.º o pasar de 30','El tamaño y el medidor no son pistas. Los nombres son opcionales']},
    pt: {t:'Estoura Balão', l:['Encham na vez de cada um: quem estourar perde','No mínimo 1 bombeada por vez; continue se tiver coragem e passe','Cada balão esconde seu ponto: pode ser o 1.º ou passar de 30','Tamanho e medidor não dão pista. Nomes são opcionais']}
  },
  'lotto': {
    ko: {t:'로또 추첨', l:['중복 없는 무작위 번호 조합을 뽑아요','국가별 프리셋을 고르거나 범위·개수·보너스볼을 정해요','속도(즉시~느리게)와 세트 수를 정하고 START','당첨 예측은 불가능해요 — 모든 조합의 확률은 같아요']},
    en: {t:'Lotto Draw', l:['Draws random number sets with no repeats','Pick a country preset or set range, count and bonus ball','Choose speed (Instant to Slow) and how many sets, then START','Nothing predicts winners: every combination is equally likely']},
    ja: {t:'ロト抽選', l:['重複のないランダムな番号の組み合わせを抽選','国別プリセットを選ぶか、範囲・個数・ボーナス球を指定','速さ（即時〜ゆっくり）とセット数を決めてSTART','当選の予測はできません。どの組み合わせも確率は同じです']},
    zh: {t:'乐透抽奖', l:['随机抽出不重复的号码组合','选国家预设，或自定范围、个数和特别号','选好速度（即时～慢速）和组数，点 START','中奖无法预测，每种组合的概率都一样']},
    es: {t:'Sorteo de Lotería', l:['Saca combinaciones de números al azar, sin repetir','Elige un país o fija rango, cantidad y bola extra','Elige velocidad (Instantáneo a Lento) y juegos, y pulsa START','Nada predice el premio: toda combinación es igual de probable']},
    pt: {t:'Sorteio da Loteria', l:['Sorteia combinações de números sem repetição','Escolha um país ou defina faixa, quantidade e bola bônus','Escolha a velocidade (Instantâneo a Lento) e os jogos, e START','Nada prevê o prêmio: toda combinação tem a mesma chance']}
  },
  'lucky-merge': {
    ko: {t:'행성 키우기', l:['같은 천체가 닿으면 합체 — 운석에서 블랙홀까지 11단계','드래그로 조준, 손을 떼면 떨어져요 (PC: ← → · Space)','초록 링 = 그 자리면 합체. 경고선 위로 쌓이면 끝','큰 천체는 아래·한쪽 벽으로. 작은 것 위에 얹지 마세요']},
    en: {t:'Planet Merge', l:['Matching bodies merge into the next stage: meteor to black hole','Drag to aim, release to drop (PC: ← → and Space)','Green ring = it merges there. Stack past the warning line and it ends','Keep big bodies low and against one wall, never on small ones']},
    ja: {t:'惑星マージ', l:['同じ天体が触れると合体。隕石からブラックホールまで11段階','ドラッグで狙って指を離すと落下（PC：← →・Space）','緑のリング＝そこなら合体。警告線を超えるとゲームオーバー','大きい天体は下と片側の壁へ。小さい天体の上に乗せない']},
    zh: {t:'行星合成', l:['相同天体碰到就合成升级，从陨石到黑洞共11级','拖动瞄准，松手落下（电脑：← → 和 Space）','绿圈＝落在这里会合成。堆过警戒线就结束','大天体放底部、靠一侧墙，别压在小天体上']},
    es: {t:'Planet Merge', l:['Cuerpos iguales se fusionan: de meteorito a agujero negro','Arrastra para apuntar y suelta para dejar caer (PC: ← → y Espacio)','Anillo verde = ahí se fusiona. Si pasas la línea roja, se acaba','Deja los grandes abajo y contra una pared, nunca sobre los pequeños']},
    pt: {t:'Planet Merge', l:['Corpos iguais se fundem: de meteorito a buraco negro','Arraste para mirar e solte para cair (PC: ← → e Espaço)','Anel verde = ali ele funde. Passou da linha de alerta, acabou','Deixe os grandes embaixo e numa parede, nunca sobre os pequenos']}
  },
  'orbit': {
    ko: {t:'델타-브이', l:['점화부터 발사탑 포획까지 6미션을 직접 조종해요(각 1~2분)','폰은 화면 아래 버튼, PC는 화살표·SHIFT·SPACE','미션마다 별 3개까지, 순서대로 다음 미션이 열려요','실패하면 원인이 숫자로 나와요 — 브리핑 목표부터 확인']},
    en: {t:'DELTA-V', l:['Fly six missions, from first ignition to a tower catch (1–2 min each)','Phone: on-screen buttons. PC: arrows, SHIFT and SPACE','Earn up to 3 stars per mission; they unlock in order','A failure shows its cause in numbers, so read the briefing goals first']},
    ja: {t:'デルタV', l:['初点火から発射塔キャッチまで6ミッションを自分で操縦（各1〜2分）','スマホは画面下のボタン、PCは矢印・SHIFT・SPACE','ミッションごとに星3つまで。順番に次が解放されます','失敗すると原因が数値で出ます。まずブリーフィングの目標を確認']},
    zh: {t:'DELTA-V', l:['从首次点火到发射塔捕获，亲手操控6个任务（每个1～2分钟）','手机用屏幕下方按钮，电脑用方向键、SHIFT 和 SPACE','每个任务最多3星，按顺序解锁下一关','失败时会用数字显示原因，先看清简报里的目标']},
    es: {t:'DELTA-V', l:['Pilota seis misiones, del primer encendido a atrapar un cohete en la torre','Móvil: botones en pantalla. PC: flechas, SHIFT y ESPACIO','Hasta 3 estrellas por misión; se desbloquean en orden','Si fallas, verás la causa en cifras: lee antes los objetivos']},
    pt: {t:'DELTA-V', l:['Pilote seis missões, da primeira ignição à captura na torre','Celular: botões na tela. PC: setas, SHIFT e ESPAÇO','Até 3 estrelas por missão; elas liberam em ordem','Se falhar, a causa aparece em números: leia antes os objetivos']}
  },
  'dodge': {
    ko: {t:'스페이스-Z', l:['운석을 피해 버틴 시간이 점수 · 링크로 👥 동시 대결(최대 8) · 🤝 2인 협동','폰: 아래 패드 드래그·BEAM·SAT 꾹 / PC: 방향키, F = BEAM, R = SAT','BEAM = 보급 끌기 · SAT = 궤도의 노란 슬롯을 1.2초 비춰 위성 설치','별가루·스침으로 고리가 차면 🌈 피버 — 닿는 운석이 부서져요','🤝 협동: 격추되면 캡슐 — 파트너가 6초 안에 스치면 부활(구조한 쪽 ❤ −1)','📖 시작 화면 「게임방법」 — 위성·BEAM·피버·아이템을 실제 영상으로']},
    en: {t:'Space-Z', l:['Dodge meteors; survival time is your score · via a link: 👥 race (up to 8) or 🤝 2P co-op','Phone: drag the pad, hold BEAM or SAT. PC: arrow keys, hold F for BEAM, R for SAT','BEAM pulls in supplies; hold SAT on the yellow orbit slot for 1.2 s to place a satellite','Stardust and grazes fill the ring: 🌈 FEVER smashes meteors you touch','🤝 Co-op: shot down = escape pod; your partner flies over it within 6 s to revive you (costs them ❤1)','📖 "How to play" on the start screen — satellite, BEAM, FEVER and items in real gameplay clips']},
    ja: {t:'スペース-Z', l:['隕石をよけ、生き残った時間がスコア · リンクで👥同時対戦（最大8人）・🤝2人協力','スマホ：下のパッドをドラッグ・BEAM/SAT長押し／PC：矢印キー、F長押しでBEAM・RでSAT','BEAMで補給を引き寄せ、SATで軌道の黄色いスロットを1.2秒照らすと衛星設置','星くずとかすりでリングが満ちると🌈フィーバー：触れた隕石が砕けます','🤝 協力：撃墜されるとカプセルに。相棒が6秒以内にかすめれば復活（救助側❤−1）','📖 スタート画面の「遊び方」— 衛星・BEAM・フィーバー・アイテムを実際の映像で']},
    zh: {t:'太空-Z', l:['躲开陨石，存活时间就是分数 · 发链接：👥 同场对战（最多8人）· 🤝 双人合作','手机：拖动下方圆盘、按住 BEAM 或 SAT；电脑：方向键，按住 F 开 BEAM，按住 R 用 SAT','BEAM 拉来补给；按住 SAT 照住轨道上的黄色槽位 1.2 秒即可安装卫星','收集星尘、擦边飞过填满光环 → 🌈 狂热：碰到的陨石会碎掉','🤝 合作：被击落会弹出逃生舱，队友6秒内掠过即可复活（救援方 ❤−1）','📖 开始画面的「玩法」— 用实际画面看卫星、BEAM、狂热和道具']},
    es: {t:'Space-Z', l:['Esquiva meteoritos: aguantar es puntuar · con un enlace: 👥 carrera (hasta 8) o 🤝 cooperativo 2P','Móvil: arrastra el panel y mantén BEAM o SAT. PC: flechas, mantén F para BEAM y R para SAT','BEAM atrae suministros; mantén SAT 1,2 s sobre la ranura amarilla de la órbita para instalar un satélite','Polvo estelar y roces llenan el anillo: 🌈 FIEBRE rompe los meteoritos que tocas','🤝 Cooperativo: si te derriban sales en cápsula; tu compañero te revive pasando por encima en 6 s (le cuesta ❤1)','📖 «Cómo jugar» en la pantalla inicial — satélite, BEAM, FEVER y objetos en vídeos reales']},
    pt: {t:'Space-Z', l:['Desvie dos meteoros: sobreviver é pontuar · por um link: 👥 corrida (até 8) ou 🤝 cooperativo 2P','Celular: arraste o painel e segure BEAM ou SAT. PC: setas, segure F para BEAM e R para SAT','BEAM puxa suprimentos; segure SAT 1,2 s sobre o encaixe amarelo da órbita para instalar um satélite','Poeira estelar e raspões enchem o anel: 🌈 FEBRE quebra os meteoros que você toca','🤝 Cooperativo: abatido vira cápsula; o parceiro passa por cima em 6 s e te revive (custa ❤1 a ele)','📖 "Como jogar" na tela inicial — satélite, BEAM, FEVER e itens em vídeos reais']}
  },
  'tetris': {
    ko: {t:'테트로미노 쌓기', l:['떨어지는 블록을 돌리고 옮겨 가로줄을 채우면 지워져요','폰: 아래 버튼으로 이동·회전·홀드, DROP = 즉시 낙하, SOFT(누르는 동안) = 천천히','PC: ← → 이동 · ↑ 회전 · Space 즉시 낙하','한 열을 비워 두고 긴 막대로 4줄을 한 번에 지우세요']},
    en: {t:'Tetromino Stack', l:['Rotate and move falling blocks; full rows clear','Phone: bottom buttons move, rotate, hold; DROP slams instantly, hold SOFT to ease down','PC: ← → move, ↑ rotate, ↓ soft drop, Space hard drop','Leave one column open and clear 4 rows at once with the long bar']},
    ja: {t:'テトロミノ・スタック', l:['落ちてくるブロックを回して動かし、横一列そろうと消えます','スマホ：下のボタンで移動・回転・ホールド、DROPで即落下、SOFT長押しでゆっくり','PC：← → 移動・↑ 回転・↓ 速く・Space 即落下','1列を空けておき、長い棒で4列を一気に消しましょう']},
    zh: {t:'四格方块', l:['旋转、移动下落的方块，填满一整行就消除','手机：下方按钮移动、旋转、暂存，DROP 直接落底，按住 SOFT 缓慢下落','电脑：← → 移动，↑ 旋转，↓ 加速，Space 直接落底','留出一列，用长条一次消4行']},
    es: {t:'Tetrominós', l:['Gira y mueve los bloques; las filas completas desaparecen','Móvil: botones abajo mueven, giran y guardan; DROP = caída instantánea, mantén SOFT para bajar','PC: ← → mover, ↑ girar, ↓ bajar, Espacio caída instantánea','Deja una columna libre y borra 4 filas de golpe con la barra larga']},
    pt: {t:'Tetraminós', l:['Gire e mova os blocos; linhas completas somem','Celular: botões embaixo movem, giram e guardam; DROP = queda instantânea, segure SOFT para descer','PC: ← → mover, ↑ girar, ↓ descer, Espaço queda instantânea','Deixe uma coluna livre e limpe 4 linhas de uma vez com a barra longa']}
  },
  'starship-lander': {
    ko: {t:'스타십 착륙', l:['연료를 아끼며 착륙장에 느리고 똑바로 내려앉혀요','⟲ ⟳ 누르는 동안 회전, MAIN·화면 탭은 분사 (PC: 방향키)','늦게, 강하게: STOP 표시가 땅에 닿을 때 길게 분사','점선 끝 = 지금 분사를 멈추면 닿을 지점']},
    en: {t:'Starship Lander', l:['Set the ship down slowly and upright on the pad, saving fuel','Hold ⟲ ⟳ to rotate; tap MAIN or anywhere to fire (PC: ← →, ↑/Space)','Late and hard: burn long when the STOP marker touches the ground','The end of the dotted line is where you land if you cut thrust now']},
    ja: {t:'スターシップ着陸', l:['燃料を節約しながら、着陸場にゆっくりまっすぐ降ろします','⟲ ⟳ 長押しで回転、MAINか画面タップで噴射（PC：← →・↑/Space）','遅く強く：STOPマークが地面に触れたら長く噴射','点線の先＝今噴射をやめたときの着地点']},
    zh: {t:'星舰着陆', l:['节省燃料，让飞船缓慢、竖直地落在着陆台上','按住 ⟲ ⟳ 旋转，点 MAIN 或屏幕喷射（电脑：方向键）','晚而猛：STOP 标记碰到地面时长按喷射','虚线末端＝现在停止喷射会落到的位置']},
    es: {t:'Starship Lander', l:['Posa la nave lento y recto en la plataforma, ahorrando combustible','Mantén ⟲ ⟳ para girar; toca MAIN o la pantalla para empujar (PC: flechas)','Tarde y fuerte: quema largo cuando la marca STOP toque el suelo','El final de la línea punteada es donde caes si cortas el empuje']},
    pt: {t:'Starship Lander', l:['Pouse a nave devagar e reta na plataforma, poupando combustível','Segure ⟲ ⟳ para girar; toque em MAIN ou na tela para acelerar (PC: setas)','Tarde e forte: queime longo quando a marca STOP tocar o chão','O fim da linha pontilhada é onde você pousa se cortar o empuxo agora']}
  },
  'brick': {
    ko: {t:'벽돌깨기', l:['패들로 공을 튕겨 벽돌을 다 깨면 다음 스테이지(총 18)','드래그로 패들 이동, 탭으로 발사 (PC: 마우스·← →)','패들 끝에 맞힐수록 공이 옆으로 크게 꺾여요','제한시간 없음 — 빨리 깨면 보너스. 축소 아이템은 함정']},
    en: {t:'Brick Breaker', l:['Bounce the ball off your paddle and clear every brick (18 stages)','Drag to move the paddle, tap to launch (PC: mouse or ← →)','Hits near the paddle edge send the ball off at a sharp angle','No time limit, but fast clears earn a bonus. Shrink is a trap item']},
    ja: {t:'ブロック崩し', l:['パドルでボールを跳ね返し、ブロックを全部壊すと次へ（全18ステージ）','ドラッグでパドル移動、タップで発射（PC：マウス・← →）','パドルの端に当てるほどボールが横に大きく曲がります','制限時間なし。速く壊せばボーナス。縮小アイテムは罠']},
    zh: {t:'打砖块', l:['用挡板弹球，打掉所有砖块就进下一关（共18关）','拖动移动挡板，点击发球（电脑：鼠标或 ← →）','球打在挡板越靠边，反弹角度越斜','没有时间限制，打得快有奖励。缩小道具是陷阱']},
    es: {t:'Rompe Ladrillos', l:['Rebota la bola con la paleta y rompe todos los ladrillos (18 fases)','Arrastra para mover la paleta, toca para lanzar (PC: ratón o ← →)','Cuanto más al borde golpea, más se abre el ángulo','Sin límite de tiempo; rápido da bonus. Encoger es una trampa']},
    pt: {t:'Quebra-Tijolos', l:['Rebata a bola com a raquete e quebre todos os tijolos (18 fases)','Arraste para mover a raquete, toque para lançar (PC: mouse ou ← →)','Quanto mais na ponta da raquete, mais aberto sai o ângulo','Sem limite de tempo; rápido dá bônus. Encolher é armadilha']}
  },
  'snake': {
    ko: {t:'스네이크', l:['먹이를 먹을수록 길어져요. 벽이나 몸에 닿으면 끝','폰: 스와이프나 방향 패드 / PC: 방향키 · Space 일시정지','진행 방향의 정반대로는 바로 꺾을 수 없어요','가장자리를 따라 크게 돌면 몸에 갇히지 않아요']},
    en: {t:'Snake', l:['Eat to grow longer; hit a wall or yourself and it ends','Phone: swipe or the D-pad. PC: arrow keys, Space to pause','You cannot turn straight back the way you came','Loop wide along the edges so your body never boxes you in']},
    ja: {t:'スネーク', l:['エサを食べるほど長くなり、壁か自分の体に当たると終了','スマホ：スワイプか方向パッド。PC：矢印キー、Spaceで一時停止','進行方向の真逆にはすぐ曲がれません','外周に沿って大きく回ると、自分の体に閉じ込められません']},
    zh: {t:'贪吃蛇', l:['吃得越多身体越长，撞墙或撞到自己就结束','手机：滑动或方向键盘。电脑：方向键，Space 暂停','不能直接掉头往反方向走','沿着边缘绕大圈，就不会被自己的身体困住']},
    es: {t:'Serpiente', l:['Come para crecer; si chocas con un muro o contigo, se acaba','Móvil: desliza o usa la cruceta. PC: flechas, Espacio pausa','No puedes girar de golpe en sentido contrario','Recorre los bordes en círculos amplios para no encerrarte']},
    pt: {t:'Snake', l:['Coma para crescer; bateu na parede ou em si, acabou','Celular: deslize ou use o direcional. PC: setas, Espaço pausa','Não dá para virar direto no sentido contrário','Contorne as bordas em voltas largas para não se prender']}
  },
  'pacman': {
    ko: {t:'닷 러너', l:['미로의 점을 다 먹으면 다음 스테이지, 유령에 닿으면 목숨 −1','폰: 스와이프나 방향 패드 / PC: 방향키','파워 쿠키 → 유령이 파랗게, 연속으로 잡을수록 점수 2배','파워 쿠키는 유령 둘 이상이 다가올 때까지 아껴 두세요']},
    en: {t:'Dot Runner', l:['Eat every dot in the maze; touching a ghost costs a life','Phone: swipe or the D-pad. PC: arrow keys','Power cookie turns ghosts blue; chain catches score 200·400·800·1600','Save power cookies until two or more ghosts close in']},
    ja: {t:'ドットランナー', l:['迷路のドットを全部食べると次へ。ゴーストに触れるとライフ−1','スマホ：スワイプか方向パッド。PC：矢印キー','パワークッキーでゴーストが青に。連続で捕まえると200·400·800·1600','パワークッキーはゴーストが2体以上迫るまで取っておきましょう']},
    zh: {t:'点点跑者', l:['吃光迷宫里的点就过关，碰到幽灵少一条命','手机：滑动或方向键盘。电脑：方向键','吃能量饼干，幽灵变蓝；连续抓到得200·400·800·1600分','能量饼干留到两个以上幽灵逼近时再吃']},
    es: {t:'Dot Runner', l:['Cómete todos los puntos del laberinto; un fantasma te quita una vida','Móvil: desliza o usa la cruceta. PC: flechas','Con la galleta de poder, fantasmas azules: 200·400·800·1600 en cadena','Guarda las galletas de poder hasta que se acerquen dos o más fantasmas']},
    pt: {t:'Dot Runner', l:['Coma todos os pontos do labirinto; um fantasma tira uma vida','Celular: deslize ou use o direcional. PC: setas','Com o biscoito de poder, fantasmas azuis: 200·400·800·1600 em sequência','Guarde os biscoitos de poder até dois ou mais fantasmas chegarem perto']}
  },
  'burger': {
    ko: {t:'버거 셰프', l:['주문서와 같은 순서로 재료를 탭해 버거를 쌓아요','폰은 접시 탭, PC는 클릭이나 숫자 키 1~5','틀리면 2초 감점, 한 번도 안 틀리면 PERFECT 보너스','재료가 5개를 넘으면 덩어리로 묶어 외우세요']},
    en: {t:'Burger Chef', l:['Tap ingredients in the order on the ticket to build the burger','Phone: tap the plates. PC: click or number keys 1–5','A wrong tap costs 2 seconds; no mistakes earns PERFECT','Past five ingredients, memorize them in chunks']},
    ja: {t:'バーガーシェフ', l:['注文票と同じ順番で具材をタップしてバーガーを積みます','スマホは皿をタップ、PCはクリックか数字キー1〜5','間違えると2秒減、ノーミスならPERFECTボーナス','具材が5つを超えたら、まとまりで覚えましょう']},
    zh: {t:'汉堡厨师', l:['按订单顺序点食材，把汉堡叠起来','手机点盘子，电脑点击或按数字键1～5','点错扣2秒，全程不错得 PERFECT 奖励','食材超过5种时，分组来记更稳']},
    es: {t:'Chef Burger', l:['Toca los ingredientes en el orden del pedido para armar la hamburguesa','Móvil: toca los platos. PC: clic o teclas 1–5','Un error resta 2 segundos; sin fallos, bonus PERFECT','Con más de cinco ingredientes, memorízalos en bloques']},
    pt: {t:'Chef Burger', l:['Toque os ingredientes na ordem do pedido para montar o lanche','Celular: toque nos pratos. PC: clique ou teclas 1–5','Um erro tira 2 segundos; sem erros, bônus PERFECT','Com mais de cinco ingredientes, decore em blocos']}
  },
  'quiz': {
    ko: {t:'라이브 퀴즈', l:['진행자가 방을 열고 카테고리·문제 수·제한 시간을 정해요','참가자는 6자리 코드나 메신저 링크로, 닉네임만 넣고 입장','빨리 맞힐수록 점수가 크고, 연속 정답엔 보너스','튕겨도 같은 링크를 다시 열면 점수 그대로 이어져요','혼자 풀기 — 방 없이 바로, 주제별 최고 기록에 도전']},
    en: {t:'Live Quiz', l:['The host opens a room and picks categories, question count and time','Players join with the 6-digit code or a chat link, nickname only','Faster correct answers score more, and streaks add a bonus','Dropped out? Reopen the same link and your score carries on','Play solo — no room needed, beat your best in each category']},
    ja: {t:'ライブクイズ', l:['司会がルームを開き、カテゴリ・問題数・制限時間を決めます','参加者は6桁コードかリンクから、ニックネームだけで入室','早く正解するほど高得点、連続正解でボーナス','落ちても同じリンクを開き直せば、点数はそのまま続きます','ひとりで解く — ルーム不要、カテゴリ別ベストに挑戦']},
    zh: {t:'实时问答', l:['主持人开房间，设定题目类别、题数和限时','参与者用6位房间码或聊天链接加入，只需填昵称','答对越快分数越高，连续答对有加分','掉线了？重新打开同一链接，分数照样接着算','单人挑战 — 不用开房间，刷新每个类别的最高分']},
    es: {t:'Quiz en Vivo', l:['El anfitrión abre una sala y elige categorías, preguntas y tiempo','Se entra con el código de 6 dígitos o un enlace, solo con apodo','Acertar rápido da más puntos y las rachas suman bonus','¿Se cortó? Abre el mismo enlace y sigues con tu puntuación','Jugar solo — sin sala, supera tu récord en cada categoría']},
    pt: {t:'Quiz ao Vivo', l:['O anfitrião abre uma sala e escolhe categorias, perguntas e tempo','Entra-se com o código de 6 dígitos ou um link, só com apelido','Acertar rápido vale mais e sequências dão bônus','Caiu? Abra o mesmo link e continue com sua pontuação','Jogar sozinho — sem sala, bata seu recorde em cada categoria']}
  }
};
