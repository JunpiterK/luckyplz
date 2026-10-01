/* =====================================================================
   lpGames.js — 게임 레지스트리 단일 원천 (LuckyPlz Rooms v2, P1)
   설계: docs/multiplayer/DESIGN.md §5 · §6.6 · §12
   새 게임 = 아래 LP_GAMES 에 한 줄. lpRoom.js 의 _validGames/_LP_PICKER_GAMES, lpMultiplayer.js GAMES,
   lpInvite*.js _humanGame 은 P6 에서 이 표를 읽게 바뀐다(지금은 아무 페이지도 이 파일을 로드하지 않는다).

   ── API 동결 (2026-09-30, "rooms-v2: API freeze") ─────────────────────
   declare global { interface Window { LP_GAMES: GameEntry[]; LpGames: LpGames } }

   type MpVer = 'v1' | 'v2' | 'off';
   interface MpSpec {
     kind: 'draw' | 'turn' | 'realtime' | 'db' | 'race' | 'lobby';
     v: MpVer;                 // 기능 플래그 — 전부 'v1'(기존 방식) 또는 'off'(멀티 없음·예정)로 시작. 게임이 옮겨 가면 'v2'
     v1: boolean;              // 기존(v1) 멀티 구현이 있는가 — 롤백 가능 여부
     adapter: string;          // 'draw' | 'draw-tick' | 'draw-session' | 'turn' | 'realtime' | 'szx' | 'qlive' | 'race' | 'lobby'
     seats: [number, number] | null;   // [최소, 최대] 좌석, null = 좌석 없음
     max: number;              // 방 정원(관전 포함) ≤ 12
     lateJoin: 'anytime' | 'nextRound' | 'takeBot' | 'spectate';
     migr: boolean;            // 플레이 중 방장 자동 승계 허용(숨은 정보 없음). 대기실·결과는 항상 허용
     hidden: boolean;          // 숨은 정보(손패·체인 비밀)
     trust: 'A' | 'B';         // 신뢰 단계(§3) — Phase B 는 채널 lprp-*
     choices?: { picks?: {key:string, options?:string[], unique?:boolean, botYield?:boolean}[],
                 options?: {key:string, values:any[], def:any}[] };   // 대기실 선택 스키마(어댑터가 덮어쓸 수 있음)
     later?: boolean;          // 멀티 예정(시드화 필요 등) — mp() 목록에서 제외
   }
   interface GameEntry {
     id: string; path: string; cat: 'random'|'draw'|'arcade'|'mission'|'board'|'hub';
     icon: string;             // /assets/tiles/toy-<id>.webp
     name: {[lang:string]: string};   // ko en ja es pt zh de fr ru ar hi th id vi tr (gb→en). 빠진 언어는 en 으로
     mp: MpSpec | null;        // null = 멀티 없음
   }
   interface LpGames {
     version: string;
     all(): GameEntry[];
     get(id:string): GameEntry | null;
     has(id:string): boolean;
     mp(ver?: MpVer): GameEntry[];            // 인자 없음 = 멀티 가능(유효 v ≠ 'off', later 아님), 있으면 그 버전만
     v(id:string): MpVer;                     // 유효 버전 — 우선순위: 링크 ?rooms=v1|v2 > 이 탭 고정(sessionStorage lpr_v2='1',
                                              //   ?rooms=v2 를 본 탭) > 개인 localStorage.lpRoomsV('1'|'2'|'v1'|'v2') > 표(mp.v)
                                              //   v1 강제는 mp.v1 없으면 'off', v2 강제는 later 게임이면 표 값. mp=null 은 항상 'off'
     override(): { v: 'v1' | 'v2', src: 'query' | 'tab' | 'storage' } | null;   // [+] 지금 걸린 오버라이드(없으면 null)
     name(id:string, lang?:string): string;   // lang 생략 = localStorage.luckyplz_lang
     path(id:string): string | null;
     url(id:string, code?:string): string | null;   // 방 이동 경로 '/games/<id>/?r=<code>' — 표에 없는 id 는 null(오픈 리다이렉트 방지)
     cats(): string[];
     isId(s:any): boolean;                    // 형식 검사 /^[a-z0-9-]{1,32}$/ + 등록 여부
   }
   ===================================================================== */
(function (G) {
    'use strict';
    if (G.LpGames && G.LpGames.version) return;

    var T = function (id) { return '/assets/tiles/toy-' + id + '.webp'; };
    /* 이름 표 — 홈(public/index.html) I18N 에서 추출(2026-09-30). 빠진 언어는 en 폴백 */
    var N = {
        'roulette': {ko:'룰렛',en:'Roulette',ja:'ルーレット',es:'Ruleta',pt:'Roleta',zh:'轮盘',de:'Roulette',fr:'Roulette',ru:'Рулетка',ar:'روليت',hi:'रूलेट',th:'รูเล็ต',id:'Roulette',vi:'Vòng quay',tr:'Rulet'},
        'car-racing': {ko:'카레이싱',en:'Car Racing',ja:'カーレース',es:'Carrera',pt:'Corrida',zh:'赛车',de:'Rennen',fr:'Course',ru:'Гонки',ar:'سباق',hi:'कार रेस',th:'แข่งรถ',id:'Balap',vi:'Đua Xe',tr:'Yarış'},
        'glory-racing': {ko:'브롤 런',en:'Brawl Run',ja:'ブロールラン',es:'Brawl Run',pt:'Brawl Run',zh:'混战跑酷',de:'Brawl Run',fr:'Brawl Run',ru:'Brawl Run',ar:'براول ران',hi:'ब्रॉल रन',th:'บรอลล์ รัน',id:'Brawl Run',vi:'Brawl Run',tr:'Brawl Run'},
        'dice': {ko:'주사위',en:'Dice Battle',ja:'サイコロ',es:'Dados',pt:'Dados',zh:'骰子',de:'Würfel',fr:'Dés',ru:'Кубики',ar:'نرد',hi:'पासा',th:'เต๋า',id:'Dadu',vi:'Xúc xắc',tr:'Zar'},
        'ladder': {ko:'사다리',en:'Ladder',ja:'あみだくじ',es:'Escalera',pt:'Escada',zh:'梯子',de:'Leiter',fr:'Échelle',ru:'Лестница',ar:'سلم',hi:'सीढ़ी',th:'บันได',id:'Tangga',vi:'Thang',tr:'Merdiven'},
        'bingo': {ko:'빙고',en:'Bingo',ja:'ビンゴ',es:'Bingo',pt:'Bingo',zh:'宾果',de:'Bingo',fr:'Bingo',ru:'Бинго',ar:'بينغو',hi:'बिंगो',th:'บิงโก',id:'Bingo',vi:'Bingo',tr:'Bingo'},
        'team': {ko:'팀 뽑기',en:'Team Picker',ja:'チーム分け',es:'Equipos',pt:'Times',zh:'分队抽签',de:'Team-Los',fr:'Équipes',ru:'Жеребьёвка',ar:'قرعة الفرق',hi:'टीम चुनाव',th:'จับทีม',id:'Undi Tim',vi:'Bốc Thăm Đội',tr:'Takım Çekilişi'},
        'balloon': {ko:'풍선 룰렛',en:'Balloon Pop',ja:'風船ルーレット',es:'Revienta Globos',pt:'Estoura Balão',zh:'气球轮盘',de:'Ballon-Knall',fr:'Ballon Boum',ru:'Шар-рулетка',ar:'بالون بوم',hi:'गुब्बारा धमाका',th:'ลูกโป่งแตก',id:'Balon Dor',vi:'Bóng Nổ',tr:'Balon Patlat'},
        'lots': {ko:'긁는 제비뽑기',en:'Scratch Lots',ja:'スクラッチくじ',es:'Sorteo para rascar',pt:'Sorteio de raspar',zh:'刮刮签',de:'Rubbel-Lose',fr:'Tirage à gratter',ru:'Жребий-скретч',ar:'قرعة الكشط',hi:'खुरच पर्ची',th:'จับฉลากขูด',id:'Undian Gosok',vi:'Bốc thăm cào',tr:'Kazı Kura'},
        'lotto': {ko:'로또 추첨',en:'Lotto Draw',ja:'ロト抽選',es:'Lotería',pt:'Loteria',zh:'乐透抽奖',de:'Lottoziehung',fr:'Tirage Loto',ru:'Лотерея',ar:'سحب',hi:'लॉटो',th:'ลอตโต',id:'Undian',vi:'Xổ số',tr:'Çekiliş'},
        'lucky-merge': {ko:'행성 키우기',en:'Planet Merge'},
        'dodge': {ko:'스페이스-Z',en:'Space-Z',ja:'スペースZ',es:'Space-Z',pt:'Space-Z',zh:'太空-Z',de:'Space-Z',fr:'Space-Z',ru:'Спейс-Z',ar:'سبيس-Z',hi:'स्पेस-Z',th:'สเปซ-Z',id:'Space-Z',vi:'Space-Z',tr:'Space-Z'},
        'tetris': {ko:'테트로미노 쌓기',en:'Tetromino Stack'},
        'starship-lander': {ko:'스타십 착륙',en:'Starship Lander'},
        'brick': {ko:'벽돌깨기',en:'Brick Breaker',ja:'ブロック崩し',zh:'打砖块',fr:'Casse-briques'},
        'snake': {ko:'스네이크',en:'Snake'},
        'pacman': {ko:'닷 러너',en:'Dot Runner'},
        'burger': {ko:'버거 셰프',en:'Burger Chef'},
        'quiz': {ko:'라이브 퀴즈',en:'Live Quiz'},
        'orbit': {ko:'델타-브이',en:'Delta-V',ja:'デルタV'},
        'bubble': {ko:'버블 버스트',en:'Bubble Burst',ja:'バブルバースト',es:'Revienta Burbujas',pt:'Estoura Bolhas',zh:'泡泡爆破',de:'Bubble Burst',fr:'Éclate-Bulles',ru:'Лопай пузыри',ar:'انفجار الفقاعات',hi:'बबल बर्स्ट',th:'บับเบิลเบิสต์',id:'Bubble Burst',vi:'Bắn Bong Bóng',tr:'Balon Patlat'},
        'gummy': {ko:'구미 체인',en:'Gummy Chain',ja:'グミチェイン',es:'Gummy Chain',pt:'Gummy Chain',zh:'软糖连锁',de:'Gummy Chain',fr:'Gummy Chain',ru:'Мармеладная цепь',ar:'سلسلة الجيلي',hi:'गमी चेन',th:'กัมมี่เชน',id:'Gummy Chain',vi:'Gummy Chain',tr:'Gummy Chain'},
        'yut': {ko:'윷놀이',en:'Yut Nori',ja:'ユンノリ',es:'Yut Nori',pt:'Yut Nori',zh:'尤茨游戏',de:'Yut Nori',fr:'Yut Nori',ru:'Yut Nori',ar:'Yut Nori',hi:'Yut Nori',th:'Yut Nori',id:'Yut Nori',vi:'Yut Nori',tr:'Yut Nori'},
        'ludo': {ko:'루도',en:'Ludo',ja:'ルドー',es:'Ludo',pt:'Ludo',zh:'鲁多棋',de:'Ludo',fr:'Ludo',ru:'Лудо',ar:'لودو',hi:'लूडो',th:'ลูโด',id:'Ludo',vi:'Ludo',tr:'Ludo'},
        'reversi': {ko:'리버시',en:'Reversi',ja:'リバーシ',es:'Reversi',pt:'Reversi',zh:'黑白棋',de:'Reversi',fr:'Reversi',ru:'Реверси',ar:'ريفيرسي',hi:'रिवर्सी',th:'รีเวอร์ซี',id:'Reversi',vi:'Cờ lật',tr:'Reversi'},
        'prism-hex': {ko:'프리즘 헥스',en:'Prism Hex',ja:'プリズムヘックス',es:'Prism Hex',pt:'Prism Hex',zh:'棱镜六角棋',de:'Prism Hex',fr:'Prism Hex',ru:'Призм Хекс',ar:'بريزم هكس',hi:'प्रिज़्म हेक्स',th:'พริซึม เฮ็กซ์',id:'Prism Hex',vi:'Prism Hex',tr:'Prism Hex'},
        'mahjong-tw': {ko:'대만 마작',en:'Taiwanese Mahjong',ja:'台湾麻雀',es:'Mahjong Taiwanés',pt:'Mahjong Taiwanês',zh:'台灣麻將',de:'Taiwan-Mahjong',fr:'Mahjong taïwanais',ru:'Тайваньский маджонг',ar:'ماجونغ تايواني',hi:'ताइवानी माहजोंग',th:'ไพ่นกกระจอกไต้หวัน',id:'Mahjong Taiwan',vi:'Mạt chược Đài Loan',tr:'Tayvan Mahjong'},
        'mahjong-solitaire': {ko:'마작 솔리테어',en:'Mahjong Solitaire',ja:'麻雀ソリティア',es:'Mahjong Solitario',pt:'Paciência Mahjong',zh:'麻将接龙',de:'Mahjong Solitär',fr:'Mahjong Solitaire',ru:'Маджонг пасьянс',ar:'ماجونغ سوليتير',hi:'माहजोंग सॉलिटेयर',th:'มาจองโซลิแทร์',id:'Mahjong Solitaire',vi:'Mạt chược xếp cặp',tr:'Mahjong Solitaire'},
        'yacht': {ko:'요트 다이스',en:'Yacht Dice',ja:'ヨットダイス',es:'Yacht Dice',pt:'Yacht Dice',zh:'快艇骰子',de:'Yacht Dice',fr:'Yacht Dice',ru:'Яхт Дайс',ar:'يخت دايس',hi:'यॉट डाइस',th:'ยอทช์ไดซ์',id:'Yacht Dice',vi:'Yacht Dice',tr:'Yacht Dice'},
        'omok': {ko:'오목',en:'Gomoku',ja:'五目並べ',es:'Gomoku',pt:'Gomoku',zh:'五子棋',de:'Gomoku',fr:'Gomoku',ru:'Гомоку',ar:'غوموكو',hi:'गोमोकू',th:'โกะโมะกุ',id:'Gomoku',vi:'Cờ caro',tr:'Gomoku'},
        'janggi': {ko:'장기',en:'Janggi & Xiangqi',ja:'チャンギ・シャンチー',es:'Janggi y Xiangqi',pt:'Janggi e Xiangqi',zh:'象棋',de:'Janggi & Xiangqi',fr:'Janggi & Xiangqi',ru:'Чанги и сянци',ar:'جانغي وشيانغتشي',hi:'जांगी और शियांगची',th:'จังกีและเซียงฉี',id:'Janggi & Xiangqi',vi:'Janggi & Cờ tướng',tr:'Janggi ve Xiangqi'},
        'lobby': {ko:'먼저 모이기',en:'Gather first',ja:'先に集合',es:'Reunirse primero',pt:'Reunir primeiro',zh:'先集合',de:'Erst sammeln',fr:'Se réunir d\'abord',ru:'Сначала собраться',ar:'التجمع أولاً',hi:'पहले इकट्ठा हों',th:'รวมตัวก่อน',id:'Kumpul dulu',vi:'Tập hợp trước',tr:'Önce toplan'}
    };
    /* mp 약식 생성기 — 기본값: 좌석 없음·정원 12·늦참 언제든·승계 가능·숨은 정보 없음·신뢰 A */
    function mp(kind, v, o) {
        o = o || {};
        return { kind: kind, v: v, v1: !!o.v1, adapter: o.adapter || kind, seats: o.seats || null, max: Math.min(12, o.max || 12),
            lateJoin: o.late || 'anytime', migr: o.migr !== false, hidden: !!o.hidden, trust: 'A',
            choices: o.choices || undefined, later: !!o.later };
    }
    var TURN_SEC = { key: 'turnSec', values: [15, 30, 60], def: 30 };
    function g(id, cat, m) { return { id: id, path: id === 'lobby' ? '/lobby/' : '/games/' + id + '/', cat: cat, icon: id === 'lobby' ? T('cat-random') : T(id), name: N[id] || { en: id }, mp: m }; }

    var LP_GAMES = [
        /* 추첨(draw) — §6.1.8 */
        g('roulette', 'random', mp('draw', 'v2', { v1: true })),
        g('car-racing', 'random', mp('draw', 'v2', { v1: true, adapter: 'draw-tick', migr: false })),
        g('glory-racing', 'random', mp('draw', 'v2', { adapter: 'draw-tick', migr: false })),
        g('dice', 'random', mp('draw', 'v2')),
        g('ladder', 'random', mp('draw', 'v2', { v1: true })),
        g('team', 'random', mp('draw', 'v2', { v1: true })),
        g('balloon', 'random', mp('turn', 'v2', { seats: [2, 8], late: 'nextRound', migr: false, hidden: true })),
        g('lots', 'random', mp('draw', 'v2')),
        g('bingo', 'draw', mp('draw', 'v2', { v1: true, adapter: 'draw-session', migr: false })),
        g('lotto', 'draw', mp('draw', 'v2', { v1: true })),
        /* 아케이드 — race(같은 시드 대결) · realtime */
        g('lucky-merge', 'arcade', mp('race', 'v2', { seats: [2, 8], late: 'nextRound' })),
        g('dodge', 'arcade', mp('realtime', 'v1', { v1: true, adapter: 'szx', seats: [1, 8], late: 'nextRound' })),
        g('tetris', 'arcade', mp('race', 'v2', { seats: [2, 8], late: 'nextRound', choices: { options: [{ key: 'mode', values: ['sprint40', 'score120'], def: 'score120' }] } })),
        g('starship-lander', 'arcade', mp('race', 'v2', { seats: [2, 8], late: 'nextRound' })),
        g('brick', 'arcade', mp('race', 'v2', { seats: [2, 8], late: 'nextRound' })),
        g('snake', 'arcade', mp('race', 'off', { seats: [2, 8], late: 'nextRound', later: true })),
        g('pacman', 'arcade', mp('race', 'off', { seats: [2, 8], late: 'nextRound', later: true })),
        g('burger', 'arcade', mp('race', 'v2', { seats: [2, 8], late: 'nextRound' })),
        g('bubble', 'arcade', mp('race', 'off', { seats: [2, 8], late: 'nextRound', later: true })),
        g('gummy', 'arcade', mp('realtime', 'v2', { v1: true, seats: [2, 2], late: 'nextRound', migr: false })),
        /* 미션 */
        g('quiz', 'mission', mp('db', 'v1', { v1: true, adapter: 'qlive', late: 'spectate' })),
        g('orbit', 'mission', null),
        /* 보드 — turn (§6.2.6) */
        g('yut', 'board', mp('turn', 'v2', { v1: true, seats: [2, 4], max: 8, late: 'takeBot',
            choices: { picks: [{ key: 'char', unique: true, botYield: true }], options: [TURN_SEC] } })),
        g('ludo', 'board', mp('turn', 'v2', { v1: true, seats: [2, 4], max: 8, late: 'takeBot',
            choices: { picks: [{ key: 'color', options: ['r', 'g', 'b', 'y'], unique: true, botYield: true }], options: [TURN_SEC] } })),
        g('reversi', 'board', mp('turn', 'v2', { v1: true, seats: [2, 2], late: 'spectate',
            choices: { picks: [{ key: 'side', options: ['b', 'w'], unique: true }], options: [{ key: 'turnSec', values: [0, 30, 60], def: 0 }] } })),
        g('prism-hex', 'board', mp('turn', 'v2', { v1: true, seats: [2, 6], late: 'takeBot', choices: { options: [TURN_SEC] } })),
        g('mahjong-tw', 'board', mp('turn', 'v2', { v1: true, seats: [4, 4], max: 8, late: 'takeBot', migr: false, hidden: true })),
        g('mahjong-solitaire', 'board', mp('race', 'v2', { seats: [2, 8], late: 'nextRound' })),
        /* 요트 다이스 (2026-09-30) — v2 전용(처음부터 lpRoomsTurn). 굴림 = LpFair.chain */
        g('yacht', 'board', mp('turn', 'v2', { seats: [2, 4], max: 8, late: 'takeBot',
            choices: { picks: [{ key: 'color', options: ['r', 'y', 'g', 'b'], unique: true, botYield: true }],
                options: [{ key: 'turnSec', values: [30, 45, 60], def: 45 }, { key: 'botLv', values: ['easy', 'normal', 'hard'], def: 'normal' }, { key: 'hint', values: [false, true], def: false }] } })),
        g('omok', 'board', mp('turn', 'v2', { seats: [2, 2], late: 'spectate', choices: { options: [{ key: 'side', values: ['b', 'w', 'r'], def: 'b' }, { key: 'rule', values: ['free', 'std', 'renju'], def: 'free' }, { key: 'size', values: [15, 19], def: 15 }, { key: 'turnSec', values: [0, 30, 60], def: 30 }] } })),
        g('janggi', 'board', mp('turn', 'v2', { seats: [2, 2], late: 'spectate', choices: { options: [{ key: 'rule', values: ['j', 'x'], def: 'j' }, { key: 'side', values: ['a', 'b', 'r'], def: 'a' }, { key: 'turnSec', values: [0, 30, 60, 120], def: 60 }, { key: 'fCho', values: [0, 1, 2, 3], def: 2 }, { key: 'fHan', values: [0, 1, 2, 3], def: 2 }] } })),
        /* 허브 — "먼저 모이기" 방 (방장이 나중에 게임을 고름) */
        g('lobby', 'hub', mp('lobby', 'v1', { v1: true }))
    ];

    var byId = {};
    LP_GAMES.forEach(function (e) { byId[e.id] = e; });
    var ID_RE = /^[a-z0-9-]{1,32}$/;

    function lsGet(k) { try { return G.localStorage ? G.localStorage.getItem(k) : null; } catch (_) { return null; } }
    function qsGet(k) { try { return new URLSearchParams(G.location.search).get(k); } catch (_) { return null; } }
    function ssGet(k) { try { return G.sessionStorage ? G.sessionStorage.getItem(k) : null; } catch (_) { return null; } }
    function ssSet(k, v) { try { if (!G.sessionStorage) return; if (v == null) G.sessionStorage.removeItem(k); else G.sessionStorage.setItem(k, v); } catch (_) {} }
    function get(id) { return (typeof id === 'string' && ID_RE.test(id) && Object.prototype.hasOwnProperty.call(byId, id)) ? byId[id] : null; }
    function verOf(s) { s = String(s == null ? '' : s).toLowerCase(); return s === 'v1' || s === '1' ? 'v1' : s === 'v2' || s === '2' ? 'v2' : null; }
    /* 오버라이드 판정 한 곳 — siteFooter 로더·게임 어댑터·UI 가 같은 답을 얻는다(각자 다시 구현하지 말 것).
       링크 ?rooms= > 이 탭 고정 lpr_v2(로더·이 파일이 ?rooms=v2 를 보면 켜고 ?rooms=v1 이면 끔) > 개인 localStorage.lpRoomsV */
    function override() {
        var q = verOf(qsGet('rooms'));
        if (q) return { v: q, src: 'query' };
        if (ssGet('lpr_v2') === '1') return { v: 'v2', src: 'tab' };
        var o = verOf(lsGet('lpRoomsV'));
        if (o) return { v: o, src: 'storage' };
        return null;
    }
    function eff(id) {
        var e = get(id);
        if (!e || !e.mp) return 'off';
        var o = override();
        if (o && o.v === 'v1') return e.mp.v1 ? 'v1' : 'off';
        if (o && o.v === 'v2' && !e.mp.later) return 'v2';
        return e.mp.v;
    }
    /* 이 탭 고정 플래그 동기화(siteFooter 로더와 같은 규칙 — 로더 없이 게임이 직접 실어도 같게) */
    (function () { var q = verOf(qsGet('rooms')); if (q === 'v2') ssSet('lpr_v2', '1'); else if (q === 'v1') ssSet('lpr_v2', null); })();
    function lang(l) {
        l = l || lsGet('luckyplz_lang') || 'en';
        l = String(l).toLowerCase().slice(0, 2);
        return l === 'gb' ? 'en' : l;
    }

    G.LP_GAMES = LP_GAMES;
    G.LpGames = {
        version: '2.0.0',
        all: function () { return LP_GAMES.slice(); },
        get: get,
        has: function (id) { return !!get(id); },
        isId: function (s) { return !!get(s); },
        mp: function (ver) {
            return LP_GAMES.filter(function (e) {
                if (!e.mp || e.mp.later) return false;
                var v = eff(e.id);
                return ver ? v === ver : v !== 'off';
            });
        },
        v: eff,
        override: override,
        name: function (id, l) { var e = get(id); if (!e) return String(id || ''); var L = lang(l); return e.name[L] || e.name.en || id; },
        path: function (id) { var e = get(id); return e ? e.path : null; },
        url: function (id, code) {
            var e = get(id); if (!e) return null;
            var c = String(code || '').replace(/[^0-9A-Z]/g, '');
            return e.path + (c ? '?r=' + c : '');
        },
        cats: function () { return ['random', 'draw', 'arcade', 'mission', 'board']; }
    };
})(typeof window !== 'undefined' ? window : globalThis);
/* CHANGE LOG
   2026-09-30  API freeze — 전 게임 mp.v 는 기존 방식('v1') 또는 'off'. 어떤 페이지도 아직 로드하지 않음.
   2026-09-30  v() 오버라이드 통일 — ?rooms=v2 를 인식(전에는 v1 만), 이 탭 고정 sessionStorage lpr_v2, localStorage 값 'v1'/'v2' 도 인정.
               우선순위 링크 > 탭 > 개인 저장 > 표. [+] override(). 로드 시 ?rooms= 를 보고 lpr_v2 를 로더와 같게 맞춘다.
*/
