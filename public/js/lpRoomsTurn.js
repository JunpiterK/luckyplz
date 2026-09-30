/* =====================================================================
   lpRoomsTurn.js — LuckyPlz Rooms v2 턴제 커널 (P4)
   설계: docs/multiplayer/DESIGN.md §6.2 (turn 어댑터) · §6.2.5 (chain·deal) · §6.0.4 (연결 판정)
   코어(lpRoomsCore.js)와 공정성(lpFair.js) 위에서 도는 "방장 권위 턴제" 공용 엔진.
   게임 파일 안의 어댑터가 규칙만 넘기면 좌석·역할·준비·시작 게이트·턴 마감(방장 시계)·
   봇 대행·자리 보호·늦참·다시 하기·공정 굴림(LpFair.chain)·숨김 배분(LpFair.deal)을 여기서 한다.

   ── API (P4, 2026-09-30) ────────────────────────────────────────────
   const K = LpRoomsTurn.mount(spec)
   spec = {
     gameId, name?:()=>string, icon?:string,
     seats:[min,max], max?:12, lateJoin:'takeBot'|'spectate'|'nextRound',
     picks?:[{key, options, unique?, botYield?, label?(val)=>html}], options?:[{key, values, def, label?(v)=>string}],
     bots?:true, hiddenInfo?:false, migratable?:true, needGuest?:true, drive?:'kernel'|'game',
     canStart?(roster,S), botName?(seat,pick)=>string,
     host:{
       init(seats, opts, fx) → game          seats=[{seat,p,n,bot,pick}]
       apply(game, seat, a, fx) → {game?, ev?, anim?:ms} | {reject}   (game 은 복사본 — 고쳐도 된다)
       next(game) → seat | null(끝)          result?(game) → any
       bot(game, seat, fx) → a               timeout?(game, seat, fx) → a (기본 bot)
       rolls?(a, game, seat) → bool          이 행동이 공정 난수(chain)를 쓰는가
       offTurn?(a, game, seat) → bool        차례가 아니어도 받는 행동(마작 울기 등)
       intent?(fromMember, a, x, seat) → any 게임 전용 부가 의도(drive:'game')
       view?(game, seat, pid) → {pub, priv?} 숨은 정보(좌석별 priv 는 커널이 ECIES 로 보냄)
       busy?() → bool                        방장 화면이 아직 연출 중이면 봇·마감 처리를 미룬다
       onSeats?(game, seats) → game          좌석 주인이 바뀜(인계·봇 전환) — 게임 표시용 이름 갱신
     },
     client:{ render(S, info), priv?(d), fair?(ev), onLeave?(why), onRoom?(room) }
   }
   K: room · isHost · me · S() · seat() · seatInfo(i) · seats() · remain() · online()
      create(opts?) · boot() · leave(noAsk?) · act(a, x?) → Promise<{ok,…}>
      ready(v) · pick(key,val) · setOpt(key,v) · addBot() · rmBot(pid) · kick(pid,ban) · unban(pid)
      start() · rematch() · claim(seat) · release(seat) · back() · watch(on)
      commit(fn(game)→game, ev?) (drive:'game' 방장) · deal() · dealReveal() · fairState()
      ui: { lobby(el), hud(), sheet(), ask(q, ok, danger), toast(s), invite(), nick() }
      inviteUrl()
   상태: S.game(어댑터) · S.turn{seat,n,deadline(방장 시계)} · S.tk{seats[{p,bot,n,pick,was}], to{}, c0, ci, fe, ev, evn, res}
   ===================================================================== */
(function (G) {
    'use strict';
    if (G.LpRoomsTurn && G.LpRoomsTurn.version) return;

    var VER = '2.0.0';
    var TM = { bot: 650, offBot: 8000, release: 60000, grace: 500, afkN: 2, busyPoll: 250, chainLen: 4096 };

    /* ── i18n (ko en ja es pt zh — 나머지는 en) ─────────────────── */
    var TX = {
        ko: { invite: '초대', copied: '링크 복사됨', qr: 'QR', ready: '준비', readyOn: '준비 완료 ✓', start: '시작', addBot: '+ 봇', spec: '관전', specN: '관전 {n}', host: '방장', you: '나',
            waitAll: '모두 준비하면 시작', needGuest: '친구를 기다리는 중', exit: '나가기', close: '방 닫기', kick: '내보내기', ban: '내보내고 차단', unban: '다시 허용', release: '자리 넘기기',
            cancel: '취소', ok: '확인', nickT: '닉네임', nickGo: '입장', hostLost1: '방장 확인 중…', hostLost2: '방장 연결 끊김', hostLost3: '방장을 기다리는 중', hostBack: '방장 복귀',
            took: '{n} 님이 방장을 이어받았어요', kicked: '방에서 내보내졌어요', closed: '방이 닫혔어요', other: '다른 탭에서 계속 중', notFound: '방을 찾지 못했어요', full: '방이 꽉 찼어요',
            locked: '이미 시작한 방이에요', banned: '들어갈 수 없는 방이에요', err: '연결 실패', joining: '입장 중…', bot: '봇', off: '끊김', away: '다른 앱', auto: '자동',
            claim: '이 자리 할래요', back: '내가 할게요', turn: '턴', sec: '{n}초', off0: '끔', rematch: '한 판 더', exitQ: '방에서 나갈까요?', closeQ: '방을 닫을까요? 모두 나가게 돼요.',
            kickQ: '{n} 님을 내보낼까요?', watch: '관전으로', play: '참가', myTurn: '내 차례', fair: '공정 굴림', fairBad: '굴림 검증 실패', again: '다시', pending: '승인 대기 중' },
        en: { invite: 'Invite', copied: 'Link copied', qr: 'QR', ready: 'Ready', readyOn: 'Ready ✓', start: 'Start', addBot: '+ Bot', spec: 'Watching', specN: '{n} watching', host: 'Host', you: 'you',
            waitAll: 'Starts when everyone is ready', needGuest: 'Waiting for friends', exit: 'Leave', close: 'Close room', kick: 'Remove', ban: 'Remove & block', unban: 'Allow', release: 'Free seat',
            cancel: 'Cancel', ok: 'OK', nickT: 'Nickname', nickGo: 'Join', hostLost1: 'Checking host…', hostLost2: 'Host disconnected', hostLost3: 'Waiting for host', hostBack: 'Host is back',
            took: '{n} is now the host', kicked: 'You were removed', closed: 'Room closed', other: 'Open in another tab', notFound: 'Room not found', full: 'Room is full',
            locked: 'Game already started', banned: 'Cannot join this room', err: 'Connection failed', joining: 'Joining…', bot: 'Bot', off: 'offline', away: 'away', auto: 'auto',
            claim: 'Take this seat', back: "I'll play", turn: 'Turn', sec: '{n}s', off0: 'Off', rematch: 'Play again', exitQ: 'Leave the room?', closeQ: 'Close the room for everyone?',
            kickQ: 'Remove {n}?', watch: 'Watch', play: 'Play', myTurn: 'Your turn', fair: 'Fair rolls', fairBad: 'Roll check failed', again: 'Retry', pending: 'Waiting for approval' },
        ja: { invite: '招待', copied: 'リンクをコピー', qr: 'QR', ready: '準備', readyOn: '準備OK ✓', start: 'スタート', addBot: '+ ボット', spec: '観戦', specN: '観戦 {n}', host: 'ホスト', you: '自分',
            waitAll: '全員準備で開始', needGuest: '友だちを待っています', exit: '退出', close: '部屋を閉じる', kick: '退出させる', ban: '退出+ブロック', unban: '許可', release: '席を空ける',
            cancel: 'キャンセル', ok: 'OK', nickT: 'ニックネーム', nickGo: '入室', hostLost1: 'ホスト確認中…', hostLost2: 'ホストの接続が切れました', hostLost3: 'ホストを待っています', hostBack: 'ホスト復帰',
            took: '{n}さんがホストを引き継ぎました', kicked: '部屋から退出させられました', closed: '部屋が閉じられました', other: '別のタブで参加中', notFound: '部屋が見つかりません', full: '満員です',
            locked: 'すでに開始しています', banned: '入れない部屋です', err: '接続失敗', joining: '入室中…', bot: 'ボット', off: '切断', away: '離席', auto: '自動',
            claim: 'この席に入る', back: '自分でやる', turn: '手番', sec: '{n}秒', off0: 'なし', rematch: 'もう一回', exitQ: '部屋を出ますか？', closeQ: '部屋を閉じますか？全員退出します。',
            kickQ: '{n}さんを退出させますか？', watch: '観戦へ', play: '参加', myTurn: 'あなたの番', fair: '公正ロール', fairBad: '検証失敗', again: '再試行', pending: '承認待ち' },
        es: { invite: 'Invitar', copied: 'Enlace copiado', qr: 'QR', ready: 'Listo', readyOn: 'Listo ✓', start: 'Empezar', addBot: '+ Bot', spec: 'Mirando', specN: '{n} mirando', host: 'Anfitrión', you: 'tú',
            waitAll: 'Empieza cuando todos estén listos', needGuest: 'Esperando amigos', exit: 'Salir', close: 'Cerrar sala', kick: 'Expulsar', ban: 'Expulsar y bloquear', unban: 'Permitir', release: 'Liberar asiento',
            cancel: 'Cancelar', ok: 'OK', nickT: 'Apodo', nickGo: 'Entrar', hostLost1: 'Comprobando anfitrión…', hostLost2: 'Anfitrión desconectado', hostLost3: 'Esperando al anfitrión', hostBack: 'Anfitrión de vuelta',
            took: '{n} es el nuevo anfitrión', kicked: 'Te expulsaron', closed: 'Sala cerrada', other: 'Abierta en otra pestaña', notFound: 'Sala no encontrada', full: 'Sala llena',
            locked: 'La partida ya empezó', banned: 'No puedes entrar', err: 'Error de conexión', joining: 'Entrando…', bot: 'Bot', off: 'desconectado', away: 'fuera', auto: 'auto',
            claim: 'Ocupar asiento', back: 'Juego yo', turn: 'Turno', sec: '{n}s', off0: 'No', rematch: 'Otra vez', exitQ: '¿Salir de la sala?', closeQ: '¿Cerrar la sala para todos?',
            kickQ: '¿Expulsar a {n}?', watch: 'Mirar', play: 'Jugar', myTurn: 'Tu turno', fair: 'Tiradas justas', fairBad: 'Falló la verificación', again: 'Reintentar', pending: 'Esperando aprobación' },
        pt: { invite: 'Convidar', copied: 'Link copiado', qr: 'QR', ready: 'Pronto', readyOn: 'Pronto ✓', start: 'Começar', addBot: '+ Bot', spec: 'Assistindo', specN: '{n} assistindo', host: 'Anfitrião', you: 'você',
            waitAll: 'Começa quando todos estiverem prontos', needGuest: 'Esperando amigos', exit: 'Sair', close: 'Fechar sala', kick: 'Remover', ban: 'Remover e bloquear', unban: 'Permitir', release: 'Liberar lugar',
            cancel: 'Cancelar', ok: 'OK', nickT: 'Apelido', nickGo: 'Entrar', hostLost1: 'Verificando anfitrião…', hostLost2: 'Anfitrião desconectado', hostLost3: 'Aguardando anfitrião', hostBack: 'Anfitrião voltou',
            took: '{n} agora é o anfitrião', kicked: 'Você foi removido', closed: 'Sala fechada', other: 'Aberta em outra aba', notFound: 'Sala não encontrada', full: 'Sala cheia',
            locked: 'O jogo já começou', banned: 'Não é possível entrar', err: 'Falha na conexão', joining: 'Entrando…', bot: 'Bot', off: 'offline', away: 'ausente', auto: 'auto',
            claim: 'Pegar este lugar', back: 'Eu jogo', turn: 'Vez', sec: '{n}s', off0: 'Não', rematch: 'Jogar de novo', exitQ: 'Sair da sala?', closeQ: 'Fechar a sala para todos?',
            kickQ: 'Remover {n}?', watch: 'Assistir', play: 'Jogar', myTurn: 'Sua vez', fair: 'Rolagens justas', fairBad: 'Falha na verificação', again: 'Tentar de novo', pending: 'Aguardando aprovação' },
        zh: { invite: '邀请', copied: '已复制链接', qr: '二维码', ready: '准备', readyOn: '已准备 ✓', start: '开始', addBot: '+ 机器人', spec: '观战', specN: '观战 {n}', host: '房主', you: '我',
            waitAll: '全员准备后开始', needGuest: '等待好友加入', exit: '离开', close: '关闭房间', kick: '移出', ban: '移出并拉黑', unban: '允许', release: '让出座位',
            cancel: '取消', ok: '确定', nickT: '昵称', nickGo: '进入', hostLost1: '正在确认房主…', hostLost2: '房主已断线', hostLost3: '等待房主', hostBack: '房主已回来',
            took: '{n} 接任房主', kicked: '你已被移出房间', closed: '房间已关闭', other: '已在其他标签页打开', notFound: '找不到房间', full: '房间已满',
            locked: '游戏已开始', banned: '无法进入该房间', err: '连接失败', joining: '正在进入…', bot: '机器人', off: '离线', away: '离开', auto: '自动',
            claim: '坐这个位子', back: '我来下', turn: '回合', sec: '{n}秒', off0: '关', rematch: '再来一局', exitQ: '离开房间？', closeQ: '为所有人关闭房间？',
            kickQ: '移出 {n}？', watch: '观战', play: '参加', myTurn: '轮到你', fair: '公平掷骰', fairBad: '校验失败', again: '重试', pending: '等待批准' }
    };
    function lang() { var l = 'en'; try { l = (G.localStorage.getItem('luckyplz_lang') || G.navigator.language || 'en').toLowerCase().slice(0, 2); } catch (_) {} return TX[l] ? l : 'en'; }
    function tt(k, v) { var L = TX[lang()], s = (L && L[k] != null) ? L[k] : (TX.en[k] != null ? TX.en[k] : k); if (v) for (var x in v) s = s.split('{' + x + '}').join(v[x]); return s; }

    /* ── 도구 ────────────────────────────────────────────────── */
    function now() { return Date.now(); }
    function clone(o) { return o == null ? o : JSON.parse(JSON.stringify(o)); }
    function hexRand(n) { var u = new Uint8Array(n); G.crypto.getRandomValues(u); var s = ''; for (var i = 0; i < n; i++) s += (u[i] < 16 ? '0' : '') + u[i].toString(16); return s; }
    function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
    function el(tag, cls, html) { var e = G.document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
    /* P2 공통 UI(lpRoomsUI.js)가 떠 있으면 그쪽을 쓴다 — 이 파일의 UI 는 폴백. API 는 병렬 작업 중이라 있는 함수만 부른다 */
    function UI() { return G.LpRoomsUI || (G.LpRooms && G.LpRooms.UI) || null; }
    function uiFn(name) { var u = UI(); return u && typeof u[name] === 'function' ? u[name].bind(u) : null; }
    function member(S, p) { if (!S || !S.roster) return null; for (var i = 0; i < S.roster.length; i++) if (S.roster[i].p === p) return S.roster[i]; return null; }
    var AV = ['🐼', '🦊', '🐰', '🐯', '🐨', '🐶', '🐱', '🐸', '🐧', '🦉', '🐙', '🐢', '🦄', '🐝', '🐳', '🦖'];

    /* 최소 CSS — 어두운 게임 화면 공통. 게임이 --lpt-acc 로 강조색을 바꿀 수 있다 */
    var CSS = '' +
        '.lpt-lobby{font:14px/1.35 system-ui,-apple-system,"Noto Sans KR",sans-serif;color:#eef;max-width:460px;margin:0 auto;padding:12px 14px 18px;box-sizing:border-box}' +
        '.lpt-lobby *{box-sizing:border-box}.lpt-hd{display:flex;align-items:center;gap:8px;margin-bottom:10px}.lpt-hd b{font-size:17px;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
        '.lpt-code{font:800 16px ui-monospace,monospace;letter-spacing:.06em;background:rgba(255,255,255,.08);border-radius:8px;padding:4px 8px}.lpt-seal{font-size:15px}' +
        '.lpt-row2{display:flex;gap:8px;margin-bottom:10px}.lpt-btn{appearance:none;border:0;border-radius:12px;padding:10px 12px;font:700 14px system-ui,sans-serif;color:#fff;background:rgba(255,255,255,.1);cursor:pointer;min-height:40px}' +
        '.lpt-btn:disabled{opacity:.38;cursor:default}.lpt-btn.pri{background:var(--lpt-acc,#6a5cff);flex:1}.lpt-btn.dng{background:#c2354b}.lpt-btn.sm{padding:6px 9px;min-height:30px;font-size:12px;border-radius:9px}' +
        '.lpt-list{display:flex;flex-direction:column;gap:6px;margin-bottom:10px}.lpt-p{display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.06);border-radius:12px;padding:7px 9px;min-height:44px}' +
        '.lpt-p.me{outline:2px solid var(--lpt-acc,#6a5cff)}.lpt-p .av{font-size:20px;width:26px;text-align:center}.lpt-p .nm{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:700}' +
        '.lpt-dot{width:10px;height:10px;border-radius:50%;display:inline-block;flex:none}.lpt-dot.on{background:#3ad07a}.lpt-dot.away{background:#f3c43a;border-radius:2px}.lpt-dot.off{background:#777;border:2px solid #aaa;width:8px;height:8px}' +
        '.lpt-pick{min-width:26px;text-align:center}.lpt-tag{font-size:12px;opacity:.75}.lpt-sec{font-size:12px;opacity:.7;margin:8px 2px 5px}' +
        '.lpt-chips{display:flex;flex-wrap:wrap;gap:6px}.lpt-chip{appearance:none;border:2px solid transparent;border-radius:12px;background:rgba(255,255,255,.08);color:#fff;padding:6px 10px;min-height:38px;min-width:44px;font:700 14px system-ui,sans-serif;cursor:pointer}' +
        '.lpt-chip.on{border-color:var(--lpt-acc,#6a5cff);background:rgba(106,92,255,.25)}.lpt-chip.tk{opacity:.35}.lpt-chip:disabled{cursor:default}' +
        '.lpt-foot{display:flex;gap:8px;margin-top:12px}.lpt-note{font-size:12px;opacity:.7;text-align:center;margin-top:8px;min-height:16px}' +
        '.lpt-hud{position:fixed;top:var(--lpt-hud-top,max(8px,env(safe-area-inset-top)));right:var(--lpt-hud-right,8px);left:var(--lpt-hud-left,auto);z-index:9050;display:flex;align-items:center;gap:6px;background:rgba(10,12,28,.82);color:#fff;border-radius:16px;padding:0 10px;height:32px;font:700 12px system-ui,sans-serif;border:1px solid rgba(255,255,255,.14);cursor:pointer;backdrop-filter:blur(6px)}' +
        '.lpt-hud.hide{display:none}.lpt-ban{position:fixed;left:50%;top:max(46px,calc(env(safe-area-inset-top) + 42px));transform:translateX(-50%);z-index:9060;padding:7px 12px;border-radius:12px;font:700 13px system-ui,sans-serif;color:#221;background:#ffd24a;box-shadow:0 4px 18px rgba(0,0,0,.35);display:flex;gap:8px;align-items:center;max-width:92vw}' +
        '.lpt-ban.red{background:#ff5d6c;color:#fff}.lpt-ban.hide{display:none}' +
        '.lpt-ov{position:fixed;inset:0;z-index:9080;background:rgba(0,0,0,.55);display:flex;align-items:flex-end;justify-content:center}.lpt-ov.hide{display:none}' +
        '.lpt-sheet{background:#15182c;color:#eef;width:100%;max-width:460px;border-radius:18px 18px 0 0;padding:14px 14px calc(16px + env(safe-area-inset-bottom));max-height:86vh;overflow:auto;font:14px system-ui,-apple-system,"Noto Sans KR",sans-serif}' +
        '.lpt-sheet h4{margin:0 0 10px;font-size:16px}.lpt-in{width:100%;padding:11px 12px;border-radius:12px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.07);color:#fff;font-size:16px}' +
        '.lpt-toast{position:fixed;left:50%;bottom:calc(84px + env(safe-area-inset-bottom));transform:translateX(-50%);z-index:9090;background:rgba(10,12,28,.9);color:#fff;padding:8px 14px;border-radius:12px;font:700 13px system-ui,sans-serif;opacity:0;transition:opacity .2s;pointer-events:none}' +
        '.lpt-toast.on{opacity:1}.lpt-live{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}' +
        '.lpt-lov{position:fixed;inset:0;z-index:9045;background:rgba(8,10,24,.97);overflow:auto;-webkit-overflow-scrolling:touch;padding-top:env(safe-area-inset-top)}.lpt-lov.hide{display:none}' +
        '.lpt-qr{display:flex;justify-content:center;margin:10px 0}.lpt-qr img{width:180px;height:180px;image-rendering:pixelated;background:#fff;padding:6px;border-radius:8px}';
    var _css = false;
    function injectCss() { if (_css || !G.document) return; _css = true; var s = el('style'); s.textContent = CSS; G.document.head.appendChild(s); }

    /* ================================================================
       Kernel
       ================================================================ */
    function Kernel(spec) {
        this.spec = spec;
        this.room = null; this.isHost = false; this.me = null;
        this._subs = []; this._tm = 0; this._iv = 0; this._q = Promise.resolve();
        this._offAt = {}; this._lastN = ''; this._sentN = {}; this._fair = { ok: 0, bad: 0, c0: null, i: 0, s: null, last: null, log: [] };
        this._ui = {}; this._lastRender = 0; this._hostLost = 0; this._anim = 0; this._pauseAt = 0; this._lastAt = 0;
    }
    var P = Kernel.prototype;

    P.S = function () { return this.room ? this.room.state() : null; };
    P.online = function () { return !!(this.room && !this.room._left); };
    P.opts = function () { var S = this.S(), o = {}; (this.spec.options || []).forEach(function (op) { o[op.key] = (S && S.opts && S.opts[op.key] !== undefined) ? S.opts[op.key] : op.def; }); return o; };
    P.turnSec = function () { var o = this.opts(); return +o.turnSec || 0; };

    /* 좌석 정보 — 플레이 중엔 S.tk.seats(시작 때 고정·인계로만 바뀜), 대기실엔 명단 */
    /* 판 좌석표는 판이 있을 때만 믿는다(게임 전환·대기실엔 옛 표가 남아 있을 수 있다) */
    function tkSeats(S) { return S && S.game && S.phase !== 'lobby' && S.tk && S.tk.seats ? S.tk.seats : null; }
    P.seatInfo = function (i, S) {
        S = S || this.S(); if (!S) return null;
        var ts = tkSeats(S), t = ts && ts[i];
        if (!t) {
            var m0 = null; (S.roster || []).forEach(function (m) { if (m.seat === i) m0 = m; });
            if (!m0) return null;
            t = { p: m0.p, bot: m0.r === 'bot', n: m0.n, pick: m0.pick };
        }
        var m = member(S, t.p), bot = !!t.bot;
        var c = bot ? 'on' : (m ? m.c : 'off');
        var off = !bot && c === 'off', afk = !bot && !!(m && m.afk);
        var offMs = off && this._offAt[t.p] ? now() - this._offAt[t.p] : 0;
        var myPid = this.me && this.me.pid;
        return {
            seat: i, p: t.p, n: bot ? (this.spec.botName ? this.spec.botName(i, t.pick || {}) : tt('bot')) : ((m && m.n) || t.n || '?'), av: m ? m.av : 0,
            pick: t.pick || (m && m.pick) || {}, bot: bot, human: !bot, c: c, off: off, away: c === 'away', afk: afk, offMs: offMs,
            me: !bot && t.p === myPid, host: !!(m && m.r === 'host'), was: t.was || null,
            botDrive: bot || afk || (off && (this.isHost ? offMs >= TM.offBot : true))
        };
    };
    P.seats = function (S) { S = S || this.S(); var out = [], ts = tkSeats(S), n = ts ? ts.length : 0, i; if (n) { for (i = 0; i < n; i++) out.push(this.seatInfo(i, S)); return out; }
        var self = this; (S && S.roster || []).filter(function (m) { return m.seat != null; }).sort(function (a, b) { return a.seat - b.seat; }).forEach(function (m) { out.push(self.seatInfo(m.seat, S)); }); return out; };
    P.seatOf = function (p, S) { S = S || this.S(); if (!S) return null; var ts = tkSeats(S); if (ts) { for (var i = 0; i < ts.length; i++) if (!ts[i].bot && ts[i].p === p) return i; return null; } var m = member(S, p); return m && m.seat != null ? m.seat : null; };
    P.seat = function () { return this.me ? this.seatOf(this.me.pid) : null; };
    P.remain = function () { var S = this.S(); if (!S || !S.turn || !S.turn.deadline || !this.room) return null; if (S.phase === 'paused') return Math.max(0, S.turn.deadline - (S.tk && S.tk.pz || this.room.clock())); return S.turn.deadline - this.room.clock(); };
    P.myTurn = function () { var S = this.S(); if (!S || S.phase !== 'playing' || !S.turn) return false; var si = this.seatInfo(S.turn.seat, S); return !!(si && si.me); };

    /* ── 방 바인딩 ─────────────────────────────────────────────── */
    P._bind = function (r) {
        if (!r || r === this.room) return;
        if (r.gameId && r.gameId !== this.spec.gameId && r.gameId !== 'lobby') return;
        this._unbind();
        var self = this;
        this.room = r; this.me = r.me; this.isHost = r.isHost;
        injectCss();
        var on = function (ev, fn) { self._subs.push(r.on(ev, fn)); };
        on('state', function (S, prev) { self._onState(S, prev); });
        on('roster', function (ro, d) { self._onRoster(ro, d); });
        on('phase', function (ph) { self._render('phase'); if (self.isHost) self._sched(); });
        on('priv', function (d, e) { if (e === '_view' && self.spec.client && self.spec.client.priv) { try { self.spec.client.priv(d); } catch (x) { dbg(x); } } });
        on('fair', function (ev) { self._onFair(ev); });
        on('hostlost', function (x) { self._hostLost = x.level; self._banner(); });
        on('hostback', function () { if (self._hostLost) { self._hostLost = 0; self._banner(); } });
        on('takeover', function (x) {
            self.isHost = r.isHost; self._hostLost = 0; self._banner();
            var m = member(r.state(), x.pid); self.toast(tt('took', { n: m ? m.n : '?' }), 2400);
            if (r.isHost) self._hostOn(); self._render('takeover');
        });
        on('demoted', function () { self.isHost = false; self._hostOff(); self._render('demoted'); });
        on('kicked', function () { self._left('kicked'); });
        on('closed', function (x) { self._left(x && x.reason === 'left' ? 'left' : 'closed'); });
        on('detached', function () { self._left('detached'); });
        on('join', function () { if (self.isHost) self._norm(); });
        on('x', function (k, d, from) { if (self.spec.client && self.spec.client.x) { try { self.spec.client.x(k, d, from); } catch (e) { dbg(e); } } });
        r.onIntent(function (from, a, x, ctx) { return self._onIntent(from, a, x, ctx); });
        if (r.isHost) this._hostOn();
        this.hud();
        if (this.spec.client && this.spec.client.onRoom) { try { this.spec.client.onRoom(r); } catch (e) { dbg(e); } }
        this._render('bind');
    };
    P._unbind = function () {
        this._subs.forEach(function (f) { try { f(); } catch (_) {} }); this._subs = [];
        this._hostOff();
        this.room = null; this.isHost = false; this._hostLost = 0; this._offAt = {};
        this._fair = { ok: 0, bad: 0, c0: null, i: 0, s: null, last: null, log: [] };
        if (this._ui.lov) this._ui.lov.classList.add('hide');
        if (this._ui.sheet) { this._ui.sheet.classList.add('hide'); this._ui.sheetOn = false; }
        this._banner(); this.hud();
    };
    P._left = function (why) {
        var cb = this.spec.client && this.spec.client.onLeave;
        this._unbind();
        if (why === 'kicked') this.toast(tt('kicked'), 2600); else if (why === 'closed') this.toast(tt('closed'), 2400); else if (why === 'detached') this.toast(tt('other'), 2600);
        if (cb) { try { cb(why); } catch (e) { dbg(e); } }
    };

    /* ── 수신 ────────────────────────────────────────────────────── */
    P._onState = function (S, prev) {
        if (S && S.tk && S.tk.fe) this._verifyFe(S);
        if (this.isHost) { this._trackOff(S.roster); this._sched(); }
        this._render('state', prev);
    };
    P._onRoster = function (ro) {
        if (this.isHost) { this._trackOff(ro); this._norm(); this._sched(); }
        this._render('roster');
        this.hud();
    };
    P._render = function (why, prev) {
        var c = this.spec.client; if (!c || !c.render || !this.room) return;
        var S = this.S(); if (!S) return;
        try { c.render(S, { why: why, prev: prev || null, k: this }); } catch (e) { dbg('render', e); }
        if (this._ui.lobbyEl) this._paintLobby();
        if (this._ui.sheetOn) this._paintSheet();
        this.hud();
    };
    P._trackOff = function (ro) {
        var self = this, t = now();
        (ro || []).forEach(function (m) {
            if (m.r === 'bot') return;
            if (m.c === 'off') { if (!self._offAt[m.p]) self._offAt[m.p] = t; }
            else delete self._offAt[m.p];
        });
    };

    /* ================================================================
       방장: 대기실 정리 · 드라이버 · 의도
       ================================================================ */
    P._hostOn = function () {
        var self = this;
        this.isHost = true;
        if (!this._iv) this._iv = setInterval(function () { self._sched(); }, 1000);
        this._trackOff((this.S() || {}).roster);
        this._norm(); this._sched();
    };
    P._hostOff = function () { clearInterval(this._iv); this._iv = 0; clearTimeout(this._tm); this._tm = 0; };

    /* 대기실·결과 단계 명단 정리: 대기 관전자 승격 · 봇 → 사람 교체 · 고유 선택 배정 */
    P._norm = function () {
        var r = this.room, S = this.S(), spec = this.spec, self = this;
        if (!r || !r.isHost || !S || !(S.phase === 'lobby' || S.phase === 'result')) return;
        var max = spec.seats[1], need = false;
        function used() { var u = {}; S.roster.forEach(function (m) { if (m.seat != null) u[m.seat] = m; }); return u; }
        function freeSeat() { var u = used(); for (var i = 0; i < max; i++) if (!u[i]) return i; return -1; }
        /* 1. 대기 관전자(자리 없어 관전된 사람) → 빈자리 또는 봇 자리 */
        S.roster.forEach(function (m) {
            if (m.r !== 'spec' || !m.wq || m.c === 'off') return;
            var fs = freeSeat();
            if (fs < 0) { var bots = S.roster.filter(function (b) { return b.r === 'bot' && b.seat != null; }); if (bots.length) { var b = bots[bots.length - 1]; fs = b.seat; S.roster.splice(S.roster.indexOf(b), 1); } }
            if (fs >= 0) { m.r = 'player'; m.seat = fs; m.rd = false; delete m.wq; need = true; }
        });
        /* 2. 고유 선택 — 좌석 주인마다 하나. 사람이 먼저(합류 순), 겹치거나 없으면 남은 것 중 첫 번째 */
        (spec.picks || []).forEach(function (pk) {
            if (!pk.unique || !pk.options) return;
            var seated = S.roster.filter(function (m) { return m.seat != null; }).sort(function (a, b) { return (a.r === 'bot') - (b.r === 'bot') || a.j - b.j; });
            var seen = {}, lack = [];
            seated.forEach(function (m) { m.pick = m.pick || {}; var v = m.pick[pk.key]; if (v && pk.options.indexOf(v) >= 0 && !seen[v]) seen[v] = 1; else lack.push(m); });
            lack.forEach(function (m) {
                for (var i = 0; i < pk.options.length; i++) if (!seen[pk.options[i]]) { m.pick[pk.key] = pk.options[i]; seen[pk.options[i]] = 1; need = true; return; }
            });
        });
        /* 3. 관전자에겐 선택을 남기지 않는다(고유 선택이 막히지 않게) */
        S.roster.forEach(function (m) { if (m.r === 'spec' && m.pick && Object.keys(m.pick).length && (spec.picks || []).some(function (pk) { return pk.unique; })) { m.pick = {}; need = true; } });
        if (need) r.setState(null);
    };

    /* 드라이버 — 지금 차례 좌석을 누가 두는지 보고 다음 할 일을 예약한다(방장 시계) */
    P._sched = function () {
        var self = this, r = this.room, S = this.S();
        clearTimeout(this._tm); this._tm = 0;
        if (!r || !r.isHost || !S || S.phase !== 'playing' || !S.turn || this.spec.drive === 'game') return;
        if (S.tk) this._autoReturn(S);
        var T = S.turn, si = this.seatInfo(T.seat, S);
        if (!si) return;
        var t = now(), due = null, kind = null, H = this.spec.host, fa = null;
        /* 강제 수(할 게 하나뿐 · 패스)는 누가 두든 짧게 기다렸다 자동으로 */
        if (H.forced) { try { var f = H.forced(S.game, T.seat); if (f && f.a) { fa = f.a; due = Math.max(t, this._anim, this._lastAt + (+f.delay || 400)); kind = 'forced'; } } catch (e) { dbg('forced', e); } }
        if (fa) { this._tm = setTimeout(function () { self._fire(T.n, kind, fa); }, Math.max(0, due - t)); return; }
        if (si.bot || si.afk) { due = Math.max(t, this._anim, this._lastAt + TM.bot); kind = 'bot'; }
        else if (si.off) {
            /* 끊긴 좌석: 끊김 판정 8초 뒤(또는 마감이 먼저면 마감에) 봇이 대신 — 끊김은 afk 로 세지 않는다 */
            var oa = this._offAt[si.p] || (this._offAt[si.p] = t);
            due = Math.max(Math.min(oa + TM.offBot, T.deadline ? T.deadline + TM.grace : Infinity), this._anim); kind = 'bot';
        }
        else if (T.deadline) { due = T.deadline + TM.grace; kind = 'timeout'; }
        else if (this.turnSec() > 0) {
            /* 봇이 두던 차례에 사람이 돌아왔다('내가 할게요'·재접속) — 그 차례에도 마감을 건다 */
            var ts = this.turnSec();
            this.room.setState(function (S) { if (S.turn && S.turn.n === T.n && !S.turn.deadline) S.turn.deadline = now() + ts * 1000; });
            return;
        }
        if (due == null) return;
        this._tm = setTimeout(function () { self._fire(T.n, kind); }, Math.max(0, due - t));
    };
    P._fire = function (n, kind, fa) {
        var self = this, S = this.S();
        if (!S || S.phase !== 'playing' || !S.turn || S.turn.n !== n || !this.room || !this.room.isHost) return;
        if (this.spec.host.busy && this.spec.host.busy()) { this._tm = setTimeout(function () { self._fire(n, kind, fa); }, TM.busyPoll); return; }
        var seat = S.turn.seat, H = this.spec.host;
        this._enq(function () {
            var S2 = self.S(); if (!S2 || !S2.turn || S2.turn.n !== n) return;
            var g = clone(S2.game), a;
            try { a = fa ? fa : (kind === 'timeout' && H.timeout) ? H.timeout(g, seat, {}) : H.bot(g, seat, {}); } catch (e) { dbg('bot', e); a = null; }
            if (a == null) { dbg('bot: no action'); return; }
            return self._apply(seat, a, { auto: kind });
        });
    };
    P._enq = function (fn) { var p = this._q = this._q.then(fn).catch(function (e) { dbg('queue', e); }); return p; };

    /* 공정 난수 (§6.2.5 chain) — 사건 i 의 난수 = H("lpf1-e"|s_i|n), n 은 비밀을 모르는 게스트가 낸 엔트로피 */
    P._fx = async function (roll, n) {
        var fx = { rec: null }, self = this;
        if (!roll || !G.LpFair) return fx;
        var r = this.room, S = this.S(), LF = G.LpFair, st = r._io.store();
        if (!st.chain || !S.tk.c0 || S.tk.c0 !== st.chain.s0 || (S.tk.ci | 0) >= st.chain.len) {
            var c = await LF.chain.create(r, TM.chainLen);
            this._pendC0 = c.s0; this._pendCi = 0;
        }
        var ci = (this._pendC0 ? this._pendCi : (S.tk.ci | 0)) + 1;
        var sI = LF.chain.reveal(ci), nn = typeof n === 'string' && /^[0-9a-f]{32}$/.test(n) ? n : (this._lastN || '');
        var rng = LF.rng(LF.chain.value(sI, nn), 'roll');
        var rec = { i: ci, s: sI, n: nn, o: [] };
        fx.rec = rec; fx.c0 = this._pendC0 || S.tk.c0;
        fx.rand = {
            int: function (k) { var v = rng.int(k); rec.o.push(['i', k, v]); return v; },
            float: function () { var v = rng.float(); rec.o.push(['f', 0, v]); return v; },
            u32: function () { var v = rng.u32(); rec.o.push(['u', 0, v]); return v; }
        };
        return fx;
    };
    /* 적용 — 의도·봇·마감 공용. 게임 규칙은 어댑터, 차례·마감 계산은 여기서 */
    P._apply = async function (seat, a, meta) {
        var r = this.room, S = this.S(), H = this.spec.host, self = this;
        if (!r || !r.isHost || !S || S.phase !== 'playing') return { reject: 'phase' };
        var game = clone(S.game);
        var roll = !!(H.rolls && H.rolls(a, game, seat));
        var fx = await this._fx(roll, meta && meta.n);
        fx.auto = (meta && meta.auto) || null;
        S = this.S(); if (!S || S.phase !== 'playing') return { reject: 'phase' };
        var res;
        try { res = H.apply(game, seat, a, fx); } catch (e) { dbg('apply', e); return { reject: 'error' }; }
        if (!res || res.reject) return { reject: (res && res.reject) || 'illegal' };
        var ng = res.game || game, human = !(meta && meta.auto);
        this._lastAt = now();
        this._anim = now() + (+res.anim || 0);
        r.setState(function (S) {
            S.game = ng;
            var tk = S.tk;
            if (self._pendC0) { tk.c0 = self._pendC0; tk.ci = 0; self._pendC0 = null; }
            if (fx.rec) { fx.rec.seat = seat; tk.fe = fx.rec; tk.ci = fx.rec.i; }
            tk.evn = (tk.evn | 0) + 1; tk.ev = { id: tk.evn, seat: seat, d: res.ev === undefined ? null : res.ev, auto: meta && meta.auto || undefined };
            tk.to = tk.to || {};
            if (human) { tk.to[seat] = 0; var sp = tk.seats[seat], m = sp && member(S, sp.p); if (m && m.afk) m.afk = false; }
            else if (meta.auto === 'timeout') {
                /* 연속 초과 횟수 — '내가 할게요'로 돌아온 뒤엔 다시 0부터(두 번 더 넘겨야 자동) */
                var sp2 = tk.seats[seat], m2 = sp2 && member(S, sp2.p), cnt = tk.to[seat] | 0;
                if (m2 && !m2.afk && cnt >= TM.afkN) cnt = 0;
                tk.to[seat] = cnt + 1;
                if (tk.to[seat] >= TM.afkN && m2) m2.afk = true;
            }
            self._advance(S, res);
        });
        var S3 = this.S();
        if (S3 && !S3.turn && S3.phase === 'playing') setTimeout(function () { var S4 = self.S(); if (self.room === r && r.isHost && S4 && !S4.turn && S4.phase === 'playing') r.end(); }, 0);
        return undefined;
    };
    P._advance = function (S, res) {
        var H = this.spec.host, nx;
        try { nx = H.next(S.game); } catch (e) { dbg('next', e); nx = null; }
        if (nx == null) {
            S.tk.res = H.result ? H.result(S.game) : null;
            S.turn = null;
            return;
        }
        var n = (S.turn ? S.turn.n : 0) + 1, ts = this.turnSec();
        var si = this.seatInfo(nx, S);
        var human = si && !si.bot && !si.afk;
        S.turn = { seat: nx, n: n, deadline: (ts > 0 && human) ? now() + (+res.anim || 0) + ts * 1000 : null };
    };
    /* 끊겼다 돌아온 원주인 — 방장이 자리를 넘긴 뒤라도 아직 봇이면 되돌려 준다 */
    P._autoReturn = function (S) {
        var self = this, ch = [];
        (S.tk.seats || []).forEach(function (sp, i) {
            if (!sp.bot || !sp.was) return;
            var m = member(S, sp.was);
            if (m && m.c !== 'off' && self.seatOf(sp.was, S) == null) ch.push(i);
        });
        if (!ch.length) return;
        this.room.setState(function (S) {
            ch.forEach(function (i) { var sp = S.tk.seats[i], m = member(S, sp.was); if (!m) return; S.roster = S.roster.filter(function (x) { return !(x.r === 'bot' && x.seat === i); }); m.r = m.r === 'host' ? 'host' : 'player'; m.seat = i; S.tk.seats[i] = { p: m.p, n: m.n, pick: sp.pick }; });
            self._seatsChanged(S);
        });
    };
    P._seatsChanged = function (S) {
        var H = this.spec.host; if (!H.onSeats) return;
        var seats = S.tk.seats.map(function (sp, i) { var m = member(S, sp.p); return { seat: i, p: sp.p, n: sp.bot ? '' : ((m && m.n) || sp.n || ''), bot: !!sp.bot, pick: sp.pick || {} }; });
        try { S.game = H.onSeats(S.game, seats) || S.game; } catch (e) { dbg('onSeats', e); }
    };

    /* 방장 의도 처리 — 신원은 항상 코어가 서명으로 확인한 from.p (페이로드의 이름·pid 는 안 믿는다) */
    P._onIntent = function (from, a, x, ctx) {
        var self = this, r = this.room, S = this.S(), spec = this.spec;
        if (!r || !r.isHost || !S) return { reject: 'state' };
        x = x || {};
        if (a === 't') {
            if (S.phase !== 'playing') return { reject: 'phase' };
            var seat = this.seatOf(from.p, S);
            if (seat == null) return { reject: 'seat' };
            var off = spec.host.offTurn && spec.host.offTurn(x.a, S.game, seat);
            if (!off) {
                if (!S.turn || S.turn.seat !== seat) return { reject: 'turn' };
                if (x.tn !== S.turn.n) return { reject: 'stale' };
            }
            if (typeof x.n === 'string' && /^[0-9a-f]{32}$/.test(x.n) && from.p !== this.me.pid) this._lastN = x.n;
            return this._enq(function () {
                var S2 = self.S();
                if (!off && (!S2.turn || S2.turn.seat !== seat || S2.turn.n !== x.tn)) return { reject: 'stale' };
                return self._apply(seat, x.a, { n: x.n, by: from.p });
            });
        }
        if (a === 'claim') return this._claim(from, x.seat | 0);
        if (a === 'leave') return this._leaveSeat(from.p);
        if (a === 'bot' && from.r === 'host') return this.addBot();
        if (spec.host.intent) { try { return spec.host.intent(from, a, x, this.seatOf(from.p, S)); } catch (e) { dbg(e); return { reject: 'error' }; } }
        return { reject: 'unknown' };
    };
    P._claim = function (from, seat) {
        var S = this.S(), spec = this.spec, self = this, r = this.room;
        var lobby = S.phase === 'lobby' || S.phase === 'result';
        if (lobby) {
            if (seat < 0 || seat >= spec.seats[1]) return { reject: 'seat' };
            var occ = null; S.roster.forEach(function (m) { if (m.seat === seat) occ = m; });
            if (occ && occ.r !== 'bot') return { reject: 'taken' };
            r.setState(function (S) {
                var me = member(S, from.p); if (!me) return;
                var old = me.seat;
                S.roster.forEach(function (m) { if (m.seat === seat && m.r === 'bot') m.seat = old == null ? null : old; });
                S.roster = S.roster.filter(function (m) { return !(m.r === 'bot' && m.seat == null); });
                me.seat = seat; if (me.r === 'spec') me.r = 'player'; delete me.wq; me.rd = false;
            });
            return;
        }
        if (S.phase !== 'playing' || !S.tk) return { reject: 'phase' };
        if ((spec.lateJoin || 'takeBot') !== 'takeBot') return { reject: 'policy' };
        if (this.seatOf(from.p, S) != null) return { reject: 'seated' };
        var sp = S.tk.seats[seat];
        if (!sp || !sp.bot) return { reject: 'taken' };
        if (sp.was && sp.was !== from.p) { var wm = member(S, sp.was); if (wm && wm.c !== 'off') return { reject: 'reserved' }; }
        if (spec.host.claimOk && !spec.host.claimOk(S.game, seat)) return { reject: 'game' };
        r.setState(function (S) {
            var me = member(S, from.p); if (!me) return;
            S.roster = S.roster.filter(function (m) { return !(m.r === 'bot' && m.seat === seat); });
            me.r = me.r === 'host' ? 'host' : 'player'; me.seat = seat; delete me.wq; me.afk = false;
            var pk = S.tk.seats[seat].pick; if (pk) me.pick = clone(pk);
            S.tk.seats[seat] = { p: from.p, n: me.n, pick: pk };
            if (S.tk.to) S.tk.to[seat] = 0;
            if (S.turn && S.turn.seat === seat && self.turnSec() > 0) S.turn.deadline = now() + self.turnSec() * 1000;
            self._seatsChanged(S);
        });
    };
    /* 좌석 → 봇 (스스로 나감 · 방장 '자리 넘기기' · 내보내기). 원래 주인은 was 로 기억 */
    P._toBot = function (S, i, was) {
        var sp = S.tk.seats[i]; if (!sp || sp.bot) return;
        var bp = 'bot' + hexRand(4);
        S.roster.forEach(function (m) { if (m.p === sp.p) { m.seat = null; if (m.r !== 'host') m.r = 'spec'; m.afk = false; } });
        S.roster.push({ p: bp, n: '', av: 0, r: 'bot', seat: i, pick: clone(sp.pick || {}), rd: true, c: 'on', j: now() + 1e12 });
        S.tk.seats[i] = { p: bp, bot: true, pick: sp.pick, was: was || undefined, n: sp.n };
        this._seatsChanged(S);
    };
    P._leaveSeat = function (p) {
        var S = this.S(), r = this.room, self = this;
        if (S.phase === 'lobby' || S.phase === 'result') { r.setState(function (S) { S.roster = S.roster.filter(function (m) { return m.p !== p; }); }); return; }
        var i = this.seatOf(p, S);
        if (i == null) return;
        r.setState(function (S) { self._toBot(S, i, null); });
    };
    P.release = function (i) {
        var S = this.S(), si = this.seatInfo(i, S), self = this;
        if (!this.isHost || !S || S.phase !== 'playing' || !si || si.bot || !si.off || si.offMs < TM.release) return false;
        this.room.setState(function (S) { self._toBot(S, i, si.p); });
        return true;
    };

    /* ================================================================
       공용 조작 (방장·게스트)
       ================================================================ */
    P.act = function (a, x) {
        var S = this.S(); if (!this.room || !S) return Promise.resolve({ ok: false, reason: 'room' });
        var n = hexRand(16);
        var body = { a: a, tn: S.turn ? S.turn.n : null, n: n };
        this._sentN[n] = 1;
        return this.room.intent('t', body);
    };
    P.ready = function (v) { return this.room ? this.room.intent('ready', !!v) : null; };
    P.pick = function (key, val) { return this.room ? this.room.intent('pick', { key: key, val: val }) : null; };
    P.back = function () { return this.room ? this.room.intent('back') : null; };
    P.watch = function (on) { return this.room ? this.room.intent('role', on ? 'watch' : 'play') : null; };
    P.claim = function (seat) { return this.room ? this.room.intent('claim', { seat: seat }) : null; };
    P.setOpt = function (key, v) { if (!this.isHost) return; this.room.setState(function (S) { S.opts = S.opts || {}; S.opts[key] = v; }); try { G.localStorage.setItem('lpt_' + this.spec.gameId + '_' + key, JSON.stringify(v)); } catch (_) {} };
    P.addBot = function () {
        var S = this.S(), spec = this.spec; if (!this.isHost || !S || !(S.phase === 'lobby' || S.phase === 'result')) return;
        var u = {}; S.roster.forEach(function (m) { if (m.seat != null) u[m.seat] = 1; });
        var fs = -1; for (var i = 0; i < spec.seats[1]; i++) if (!u[i]) { fs = i; break; }
        if (fs < 0) return;
        this.room.setState(function (S) { S.roster.push({ p: 'bot' + hexRand(4), n: '', av: (Math.random() * 16) | 0, r: 'bot', seat: fs, pick: {}, rd: true, c: 'on', j: now() + 1e12 }); });
        this._norm();
    };
    P.rmBot = function (p) { if (!this.isHost) return; this.room.setState(function (S) { S.roster = S.roster.filter(function (m) { return !(m.p === p && m.r === 'bot'); }); }); };
    P.kick = function (p, ban) {
        var S = this.S(), self = this; if (!this.isHost || !S) return;
        var i = S.tk && S.phase !== 'lobby' ? this.seatOf(p, S) : null;
        if (i != null) this.room.setState(function (S) { self._toBot(S, i, null); });
        this.room.kick(p, { ban: !!ban });
    };
    P.unban = function (p) { if (this.isHost) this.room.unban(p); };
    P.canStart = function () {
        var S = this.S(); if (!S || !this.room) return false;
        return this.room.canStart();
    };
    P.start = async function () {
        var r = this.room, S = this.S(), spec = this.spec, self = this;
        if (!r || !r.isHost || !S || !(S.phase === 'lobby' || S.phase === 'result') || !this.canStart()) return false;
        this._norm();
        S = this.S();
        var seated = S.roster.filter(function (m) { return m.seat != null && m.r !== 'spec'; }).sort(function (a, b) { return a.seat - b.seat; });
        var seats = seated.map(function (m, i) { return { seat: i, p: m.p, n: m.r === 'bot' ? '' : m.n, bot: m.r === 'bot', pick: clone(m.pick || {}) }; });
        var opts = this.opts();
        var game;
        try { game = spec.host.init(clone(seats), clone(opts), {}); } catch (e) { dbg('init', e); return false; }
        if (G.LpFair && spec.fair !== false && spec.host.rolls) {
            try { var c = await G.LpFair.chain.create(r, TM.chainLen); this._pendC0 = c.s0; this._pendCi = 0; } catch (e) { dbg('chain', e); }
        }
        this._lastAt = now(); this._anim = now() + 900;
        r.setState(function (S) {
            seated.forEach(function (m, i) { var mm = member(S, m.p); if (mm) mm.seat = i; });
            S.opts = Object.assign({}, S.opts || {}, opts);
            S.game = game;
            S.tk = { seats: seats.map(function (s) { return { p: s.p, bot: s.bot || undefined, n: s.n, pick: s.pick }; }), to: {}, c0: self._pendC0 || null, ci: 0, fe: null, ev: null, evn: 0, res: null, g: (S.tk && S.tk.g | 0) + 1 };
            self._pendC0 = null;
            S.turn = null;
            self._advance(S, { anim: 900 });
        }, { full: true });
        r.start({ countdownMs: 0 });
        try { if (G.LpWakeLock && G.LpWakeLock.acquire) G.LpWakeLock.acquire(); } catch (_) {}
        return true;
    };
    P.rematch = function () {
        var r = this.room; if (!r || !r.isHost) return;
        var S = this.S();
        r.setState(function (S) {
            /* 봇 자리는 봇으로, 사람 자리는 사람으로 대기실에 그대로 앉힌다 */
            if (S.tk && S.tk.seats) S.tk.seats.forEach(function (sp, i) { if (sp.bot) S.roster.forEach(function (m) { if (m.p === sp.p) m.seat = i; }); });
            S.game = null; S.turn = null; if (S.tk) { S.tk.res = null; S.tk.fe = null; S.tk.ev = null; S.tk.seats = null; }
        });
        r.toLobby();
        this._norm();
    };
    /* drive:'game' — 게임이 스스로 규칙·타이머를 돌리는 경우(마작): 방장이 새 상태를 올린다 */
    P.commit = function (fn, o) {
        var r = this.room; if (!r || !r.isHost) return 0;
        var self = this;
        return r.setState(function (S) {
            var g = fn(S.game, S); if (g !== undefined) S.game = g;
            if (o && o.turn !== undefined) S.turn = o.turn;
            if (o && o.res !== undefined && S.tk) S.tk.res = o.res;
        });
    };
    P.startGame = async function (game, o) {       /* drive:'game' 시작: 게임이 만든 첫 상태로 */
        var r = this.room, S = this.S(); if (!r || !r.isHost) return false;
        var seated = S.roster.filter(function (m) { return m.seat != null && m.r !== 'spec'; }).sort(function (a, b) { return a.seat - b.seat; });
        r.setState(function (S) {
            seated.forEach(function (m, i) { var mm = member(S, m.p); if (mm) mm.seat = i; });
            S.game = game; S.turn = (o && o.turn) || null;
            S.tk = { seats: seated.map(function (m) { return { p: m.p, bot: m.r === 'bot' || undefined, n: m.r === 'bot' ? '' : m.n, pick: clone(m.pick || {}) }; }), to: {}, c0: null, ci: 0, fe: null, ev: null, evn: 0, res: null, g: (S.tk && S.tk.g | 0) + 1 };
        }, { full: true });
        r.start({ countdownMs: 0 });
        return true;
    };
    P.seatList = function () {   /* 시작 전 좌석 목록(drive:'game' 이 init 에 쓰도록) */
        var S = this.S(); if (!S) return [];
        return S.roster.filter(function (m) { return m.seat != null && m.r !== 'spec'; }).sort(function (a, b) { return a.seat - b.seat; })
            .map(function (m, i) { return { seat: i, p: m.p, n: m.r === 'bot' ? '' : m.n, bot: m.r === 'bot', pick: clone(m.pick || {}), host: m.r === 'host' }; });
    };
    P.finish = function (res) { var r = this.room; if (!r || !r.isHost) return; r.setState(function (S) { if (S.tk) S.tk.res = res === undefined ? null : res; S.turn = null; }); r.end(); };
    P.deal = async function () { if (!G.LpFair || !this.room || !this.room.isHost) return null; var d = await G.LpFair.deal.begin(this.room); return d; };
    P.dealReveal = function () { if (G.LpFair && this.room && this.room.isHost) G.LpFair.deal.reveal(this.room); };

    /* ── 공정 굴림 검증 (게스트·방장 모두) ───────────────────────── */
    P._verifyFe = function (S) {
        var fe = S.tk.fe, F = this._fair, LF = G.LpFair;
        if (!LF || !fe || typeof fe.i !== 'number') return;
        var key = S.tk.c0 + ':' + fe.i;
        if (F.last === key) return;
        F.last = key;
        var ok = true, why = '';
        if (!S.tk.c0 || !/^[0-9a-f]{64}$/.test(String(fe.s))) { ok = false; why = 'format'; }
        else if (F.c0 === S.tk.c0 && F.s && F.i === fe.i - 1) { ok = LF.hex(LF.H(LF.unhex(fe.s))) === F.s; if (!ok) why = 'link'; }
        else { ok = LF.chain.verify(S.tk.c0, fe.s, fe.i); if (!ok) why = 'chain'; }
        if (ok) {
            var rng = LF.rng(LF.chain.value(fe.s, fe.n || ''), 'roll');
            for (var k = 0; k < (fe.o || []).length && ok; k++) {
                var o = fe.o[k], v = o[0] === 'i' ? rng.int(o[1]) : o[0] === 'f' ? rng.float() : rng.u32();
                if (v !== o[2]) { ok = false; why = 'value'; }
            }
        }
        if (ok && fe.n && this.me && this.seatOf(this.me.pid, S) === fe.seat && S.tk.ev && S.tk.ev.seat === fe.seat && !S.tk.ev.auto && !this._sentN[fe.n] && !this.isHost) { ok = false; why = 'nonce'; }
        F.c0 = S.tk.c0; F.i = fe.i; F.s = fe.s;
        if (ok) F.ok++; else { F.bad++; dbg('fair bad', why, fe); }
        F.log.push({ i: fe.i, ok: ok, why: why || undefined, seat: fe.seat }); if (F.log.length > 200) F.log.shift();
        if (this.spec.client && this.spec.client.fair) { try { this.spec.client.fair({ ok: ok, why: why, fe: fe, stats: { ok: F.ok, bad: F.bad } }); } catch (e) { dbg(e); } }
    };
    P._onFair = function (ev) { if (this.spec.client && this.spec.client.fairEv) { try { this.spec.client.fairEv(ev); } catch (e) { dbg(e); } } };
    P.fairState = function () { var F = this._fair; return { ok: F.ok, bad: F.bad, i: F.i, c0: F.c0, log: F.log.slice() }; };

    /* ================================================================
       방 만들기 · 참가 · 복귀 · 나가기
       ================================================================ */
    P.inviteUrl = function () {
        if (!this.room) return '';
        var u = this.room.inviteUrl(), h = u.indexOf('#') >= 0 ? u.slice(u.indexOf('#')) : '';
        var path = (G.LpGames && G.LpGames.path && G.LpGames.path(this.spec.gameId)) || ('/games/' + this.spec.gameId + '/');
        return G.location.origin + path + '?r=' + this.room.code + h;
    };
    P.create = async function (o) {
        var LR = G.LpRooms; if (!LR) throw new Error('no LpRooms');
        await LR.ready();
        var nick = LR.profile.get().nick;
        if (!nick) { nick = await this.nick(); if (!nick) return null; }
        var opts = {}, spec = this.spec;
        (spec.options || []).forEach(function (op) { var v = op.def; try { var s = G.localStorage.getItem('lpt_' + spec.gameId + '_' + op.key); if (s != null) { var pv = JSON.parse(s); if (op.values.indexOf(pv) >= 0) v = pv; } } catch (_) {} opts[op.key] = v; });
        if (o && o.opts) for (var k in o.opts) opts[k] = o.opts[k];
        var r = await LR.create({ gameId: spec.gameId, opts: opts, max: spec.max || 12 });
        this._bind(r);
        return r;
    };
    /* 페이지 진입: 새로고침·게임 전환이면 resume, ?r=CODE(#k=) 링크면 join */
    P.boot = async function (o) {
        o = o || {};
        var LR = G.LpRooms; if (!LR) return null;
        var self = this, code = null, inv = null;
        try {
            var p = LR.parseInvite(G.location.href);
            if (p && p.hint === 'v2') { code = p.code; inv = p.inv || null; }
            if (inv) { try { G.sessionStorage.setItem('lpr_inv', JSON.stringify({ code: code, fp: inv.fp, tok: inv.tok || null })); } catch (_) {} }
            if (G.location.hash && /k=/.test(G.location.hash)) G.history.replaceState(null, '', G.location.pathname + G.location.search);
        } catch (_) {}
        try { await LR.ready(); } catch (e) { if (code) this.toast(tt('err'), 2600); return null; }
        var r = null, act = null;
        try { act = JSON.parse(G.sessionStorage.getItem('lpr_active') || 'null'); } catch (_) {}
        if (!(act && act.gameId && act.gameId !== this.spec.gameId && act.gameId !== 'lobby' && (!code || code !== act.code))) {
            try { r = await LR.resume(); } catch (e) { dbg('resume', e); }
        }
        if (r) { this._bind(r); return r; }
        if (!code) return null;
        if (!LR.profile.get().nick) { var nk = await this.nick(); if (!nk) return null; }
        if (o.onStatus) o.onStatus({ st: 'joining' });
        try {
            r = await LR.join({ code: code, inv: inv, onStatus: function (s) { if (s.st === 'pending') self.toast(tt('pending'), 3000); if (o.onStatus) o.onStatus(s); } });
            this._bind(r);
            return r;
        } catch (e) {
            var why = e && e.reason;
            if (why === 'wrong_game' && e.url) { G.location.replace(e.url); return null; }
            if (why === 'other_tab') {
                if (await this.ask(tt('other'), tt('play'))) { try { r = await LR.join({ code: code, inv: inv, steal: true }); this._bind(r); return r; } catch (e2) { why = e2 && e2.reason; } }
                else return null;
            }
            var msg = { not_found: 'notFound', full: 'full', locked: 'locked', banned: 'banned', closed: 'closed', denied: 'banned' }[why] || 'err';
            this.toast(tt(msg), 3000);
            if (o.onFail) o.onFail(why);
            return null;
        }
    };
    P.leave = async function (noAsk) {
        var r = this.room; if (!r) return;
        if (!noAsk && !(await this.ask(r.isHost ? tt('closeQ') : tt('exitQ'), r.isHost ? tt('close') : tt('exit'), true))) return false;
        if (r.isHost) r.close();
        else { try { await r.intent('leave'); } catch (_) {} r.leave(); }
        return true;
    };

    /* ================================================================
       UI — 기본 대기실(게임에 대기실이 없을 때) · HUD 알약 · 방 시트 · 띠 · 확인창 · 토스트
       lpRoomsUI.js(P2)가 있으면 게임은 그쪽을 먼저 쓴다(여기는 폴백).
       ================================================================ */
    P.toast = function (s, ms) {
        if (!G.document) return; injectCss();
        var t = this._ui.toast; if (!t) { t = this._ui.toast = el('div', 'lpt-toast'); t.setAttribute('role', 'status'); G.document.body.appendChild(t); }
        t.textContent = s; t.classList.add('on'); clearTimeout(this._ui.toastT);
        this._ui.toastT = setTimeout(function () { t.classList.remove('on'); }, ms || 1600);
    };
    P.ask = function (q, okLbl, danger) {
        injectCss();
        var self = this;
        return new Promise(function (res) {
            var ov = el('div', 'lpt-ov'), sh = el('div', 'lpt-sheet');
            sh.innerHTML = '<h4></h4><div class="lpt-foot"><button type="button" class="lpt-btn" data-v="0"></button><button type="button" class="lpt-btn ' + (danger ? 'dng' : 'pri') + '" data-v="1"></button></div>';
            sh.querySelector('h4').textContent = q; sh.querySelector('[data-v="0"]').textContent = tt('cancel'); sh.querySelector('[data-v="1"]').textContent = okLbl || tt('ok');
            ov.appendChild(sh); G.document.body.appendChild(ov);
            function done(v) { try { ov.remove(); } catch (_) {} res(v); }
            ov.addEventListener('click', function (e) { var b = e.target.closest('[data-v]'); if (b) done(b.getAttribute('data-v') === '1'); else if (e.target === ov) done(false); });
        });
    };
    P.nick = function () {
        injectCss();
        var LR = G.LpRooms;
        return new Promise(function (res) {
            var ov = el('div', 'lpt-ov'), sh = el('div', 'lpt-sheet');
            var cur = LR ? LR.profile.get() : { nick: '', av: 0 };
            sh.innerHTML = '<h4></h4><input class="lpt-in" maxlength="12" autocomplete="nickname" enterkeyhint="go"><div class="lpt-chips" style="margin-top:10px">' +
                AV.map(function (a, i) { return '<button type="button" class="lpt-chip' + (i === cur.av ? ' on' : '') + '" data-av="' + i + '">' + a + '</button>'; }).join('') +
                '</div><div class="lpt-foot"><button type="button" class="lpt-btn" data-v="0"></button><button type="button" class="lpt-btn pri" data-v="1"></button></div>';
            sh.querySelector('h4').textContent = tt('nickT');
            var inp = sh.querySelector('input'); inp.value = cur.nick || '';
            sh.querySelector('[data-v="0"]').textContent = tt('cancel'); sh.querySelector('[data-v="1"]').textContent = tt('nickGo');
            var av = cur.av;
            ov.appendChild(sh); G.document.body.appendChild(ov);
            setTimeout(function () { try { inp.focus(); } catch (_) {} }, 50);
            function done(ok) {
                var n = inp.value.trim();
                if (ok && !n) { inp.focus(); return; }
                try { ov.remove(); } catch (_) {}
                if (ok && LR) { var p = LR.profile.set({ nick: n, av: av }); try { G.localStorage.setItem('luckyplz_nick', p.nick); } catch (_) {} res(p.nick); } else res(null);
            }
            inp.addEventListener('keydown', function (e) { if (e.key === 'Enter') done(true); });
            ov.addEventListener('click', function (e) {
                var a = e.target.closest('[data-av]'); if (a) { av = +a.getAttribute('data-av'); sh.querySelectorAll('[data-av]').forEach(function (b) { b.classList.toggle('on', b === a); }); return; }
                var b = e.target.closest('[data-v]'); if (b) done(b.getAttribute('data-v') === '1');
            });
        });
    };
    P.invite = async function () {
        var f = uiFn('invite') || uiFn('openInvite'); if (f && this.room) { try { f(this.room, { url: this.inviteUrl() }); return; } catch (e) { dbg('ui invite', e); } }
        var url = this.inviteUrl(); if (!url) return;
        var nm = this.spec.name ? this.spec.name() : this.spec.gameId;
        var txt = '🎲 ' + nm + ' · ' + (G.LpRooms ? G.LpRooms.util.fmtCode(this.room.code) : this.room.code);
        try { if (G.navigator.share) { await G.navigator.share({ text: txt, url: url }); return; } } catch (e) { if (e && e.name === 'AbortError') return; }
        try { await G.navigator.clipboard.writeText(txt + '\n' + url); this.toast('✓ ' + tt('copied')); } catch (_) { this.qr(); }
    };
    P.qr = function () {
        var url = this.inviteUrl(), self = this; injectCss();
        var ov = el('div', 'lpt-ov'), sh = el('div', 'lpt-sheet');
        sh.innerHTML = '<h4 style="text-align:center"></h4><div class="lpt-qr">…</div><div style="word-break:break-all;font-size:11px;opacity:.6;text-align:center"></div><div class="lpt-foot"><button type="button" class="lpt-btn pri" data-v="1">OK</button></div>';
        sh.querySelector('h4').textContent = G.LpRooms.util.fmtCode(this.room.code) + ' ' + (this.room.seal || '');
        sh.querySelectorAll('div')[2].textContent = url;
        ov.appendChild(sh); G.document.body.appendChild(ov);
        ov.addEventListener('click', function (e) { if (e.target === ov || e.target.closest('[data-v]')) ov.remove(); });
        var box = sh.querySelector('.lpt-qr');
        function draw() { try { var q = G.qrcode(0, 'M'); q.addData(url); q.make(); box.innerHTML = q.createImgTag(5, 0); } catch (_) { box.textContent = url; } }
        if (G.qrcode) draw();
        else { var s = el('script'); s.src = 'https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js'; s.onload = draw; s.onerror = function () { box.textContent = ''; }; G.document.head.appendChild(s); }
    };

    /* HUD 알약 — 플레이 중 방 정보 1개(코드 · 인원 · 연결점). 탭 → 방 시트 */
    P.hud = function () {
        if (!G.document || this.spec.noHud) return;
        if (UI()) { if (this._ui.hud) this._ui.hud.classList.add('hide'); return; }   /* P2 HUD 알약이 대신한다 */
        var h = this._ui.hud, r = this.room, self = this;
        if (!r) { if (h) h.classList.add('hide'); return; }
        injectCss();
        if (!h) {
            h = this._ui.hud = el('button', 'lpt-hud'); h.type = 'button'; h.setAttribute('aria-label', 'room');
            h.addEventListener('click', function () { self.sheet(); });
            G.document.body.appendChild(h);
        }
        var S = this.S(), n = S ? S.roster.filter(function (m) { return m.r !== 'bot'; }).length : 0;
        var bad = this._hostLost >= 2 || (S && S.roster.some(function (m) { return m.r !== 'bot' && m.r !== 'spec' && m.c === 'off'; }));
        var txt = G.LpRooms.util.fmtCode(r.code) + ' · 👥' + n;
        if (h._t !== txt + bad) { h._t = txt + bad; h.innerHTML = esc(txt) + ' <span class="lpt-dot ' + (bad ? 'off' : 'on') + '"></span>'; }
        var hide = !!(this._ui.lov && !this._ui.lov.classList.contains('hide')) || !!(this._ui.lobbyEl && this._ui.lobbyEl.offsetParent) || !!this.spec.hudHidden && this.spec.hudHidden();
        h.classList.toggle('hide', hide);
    };
    P.hostLost = function () { return this._hostLost; };
    P._banner = function () {
        if (this.spec.client && this.spec.client.hostLost) { try { this.spec.client.hostLost(this._hostLost); } catch (_) {} }
        if (!G.document || this.spec.noBanner || UI()) return;   /* P2 방장 끊김 띠가 대신한다 */
        injectCss();
        var b = this._ui.ban, self = this;
        if (!b) {
            b = this._ui.ban = el('div', 'lpt-ban hide'); b.setAttribute('role', 'status'); b.setAttribute('aria-live', 'polite');
            b.innerHTML = '<span></span><button type="button" class="lpt-btn sm" style="background:rgba(0,0,0,.25)"></button>';
            b.querySelector('button').addEventListener('click', function () { self.leave(true); });
            G.document.body.appendChild(b);
        }
        var lv = this._hostLost, msg = lv === 1 ? tt('hostLost1') : lv === 2 ? tt('hostLost2') : lv === 3 ? tt('hostLost3') : '';
        b.classList.toggle('hide', !msg || !this.room); b.classList.toggle('red', lv >= 2);
        b.querySelector('span').textContent = msg;
        var btn = b.querySelector('button'); btn.textContent = tt('exit'); btn.style.display = lv >= 2 ? '' : 'none';
    };

    /* 방 시트 — 명단 · 초대 · (방장) 내보내기/차단/자리 넘기기/방 닫기 · (게스트) 나가기 */
    P.sheet = function () {
        var f = uiFn('sheet') || uiFn('openSheet'); if (f && this.room) { try { f(this.room, { turn: this }); return; } catch (e) { dbg('ui sheet', e); } }
        injectCss(); if (!this.room) return;
        var self = this;
        if (!this._ui.sheet) {
            var ov = this._ui.sheet = el('div', 'lpt-ov hide'), sh = el('div', 'lpt-sheet');
            ov.appendChild(sh); G.document.body.appendChild(ov);
            ov.addEventListener('click', function (e) {
                if (e.target === ov) { ov.classList.add('hide'); self._ui.sheetOn = false; return; }
                var b = e.target.closest('button'); if (!b) return;
                var d = b.dataset;
                if (d.inv) self.invite();
                else if (d.qr) self.qr();
                else if (d.cls) { ov.classList.add('hide'); self._ui.sheetOn = false; }
                else if (d.exit) { ov.classList.add('hide'); self._ui.sheetOn = false; self.leave(); }
                else if (d.kick) self._kickAsk(d.kick, false);
                else if (d.ban) self._kickAsk(d.ban, true);
                else if (d.unban) self.unban(d.unban);
                else if (d.rel) self.release(+d.rel);
                else if (d.claim) self.claim(+d.claim);
                else if (d.back) self.back();
                else if (d.watch) self.watch(d.watch === '1');
            });
        }
        this._ui.sheetOn = true; this._ui.sheet.classList.remove('hide');
        this._paintSheet();
    };
    P._kickAsk = async function (p, ban) {
        var m = member(this.S(), p); if (!m) return;
        if (await this.ask(tt('kickQ', { n: m.n || '?' }), ban ? tt('ban') : tt('kick'), true)) this.kick(p, ban);
    };
    P._paintSheet = function () {
        var ov = this._ui.sheet; if (!ov || !this.room) { if (ov) ov.classList.add('hide'); return; }
        var sh = ov.firstChild, S = this.S(), host = this.isHost, me = this.me.pid, self = this, inPlay = S.phase !== 'lobby' && S.phase !== 'result';
        var rows = S.roster.slice().sort(function (a, b) { return (a.seat == null) - (b.seat == null) || (a.seat | 0) - (b.seat | 0); }).map(function (m) {
            var si = m.seat != null && inPlay ? self.seatInfo(m.seat, S) : null;
            var tools = '';
            if (host && m.p !== me && m.r !== 'bot') {
                if (si && si.off && si.offMs >= TM.release) tools += '<button type="button" class="lpt-btn sm" data-rel="' + m.seat + '">' + esc(tt('release')) + '</button>';
                tools += '<button type="button" class="lpt-btn sm" data-kick="' + esc(m.p) + '">' + esc(tt('kick')) + '</button><button type="button" class="lpt-btn sm dng" data-ban="' + esc(m.p) + '">⛔</button>';
            }
            if (!host && m.p === me && si && si.afk) tools += '<button type="button" class="lpt-btn sm pri" data-back="1">' + esc(tt('back')) + '</button>';
            var dot = m.r === 'bot' ? '🤖' : '<span class="lpt-dot ' + (m.c === 'off' ? 'off' : m.c === 'away' ? 'away' : 'on') + '" aria-label="' + esc(m.c) + '"></span>';
            var nm = m.r === 'bot' ? (self.spec.botName ? self.spec.botName(m.seat, m.pick || {}) : tt('bot')) : m.n;
            return '<div class="lpt-p' + (m.p === me ? ' me' : '') + '"><span class="av">' + (m.r === 'host' ? '👑' : m.r === 'spec' ? '👀' : AV[m.av | 0] || '🙂') + '</span><span class="nm">' + esc(nm) + (m.p === me ? ' <span class="lpt-tag">(' + esc(tt('you')) + ')</span>' : '') + (m.afk ? ' <span class="lpt-tag">🤖' + esc(tt('auto')) + '</span>' : '') + '</span>' + dot + tools + '</div>';
        }).join('');
        /* 게임 중 관전자 — 봇 자리 이어받기(takeBot) */
        var claims = '';
        if (inPlay && S.tk && S.tk.seats && (this.spec.lateJoin || 'takeBot') === 'takeBot' && this.seatOf(me, S) == null) {
            S.tk.seats.forEach(function (sp, i) { if (sp.bot) claims += '<button type="button" class="lpt-btn sm pri" data-claim="' + i + '">' + esc(tt('claim')) + ' #' + (i + 1) + '</button> '; });
        }
        var bans = host && S.bans && S.bans.length ? '<div class="lpt-sec">⛔</div>' + S.bans.map(function (p) { return '<button type="button" class="lpt-btn sm" data-unban="' + esc(p) + '">' + esc(tt('unban')) + ' ' + esc(p.slice(0, 6)) + '</button>'; }).join(' ') : '';
        sh.innerHTML = '<div class="lpt-hd"><b>' + esc(this.spec.name ? this.spec.name() : '') + '</b><span class="lpt-code">' + esc(G.LpRooms.util.fmtCode(this.room.code)) + '</span><span class="lpt-seal" title="seal">' + esc(this.room.seal || '') + '</span></div>' +
            '<div class="lpt-row2"><button type="button" class="lpt-btn pri" data-inv="1">💬 ' + esc(tt('invite')) + '</button><button type="button" class="lpt-btn" data-qr="1">▦ ' + esc(tt('qr')) + '</button></div>' +
            '<div class="lpt-list">' + rows + '</div>' + (claims ? '<div style="margin-bottom:8px">' + claims + '</div>' : '') + bans +
            '<div class="lpt-foot"><button type="button" class="lpt-btn dng" data-exit="1">' + esc(host ? tt('close') : tt('exit')) + '</button><button type="button" class="lpt-btn pri" data-cls="1">OK</button></div>';
    };

    /* 대기실 겹창 — 게임 화면 위에 기본 대기실을 띄운다(게임 HTML 을 고치지 않고) */
    P.lobbyOv = function (show) {
        if (!G.document) return; injectCss();
        var o = this._ui.lov;
        if (!o) { o = this._ui.lov = el('div', 'lpt-lov hide'); var box = el('div'); o.appendChild(box); G.document.body.appendChild(o); this.lobby(box); }
        var on = !!show && !!this.room;
        o.classList.toggle('hide', !on);
        if (on) this._paintLobby();
        this.hud();
    };
    /* 기본 대기실 — el 안에 그린다(게임은 대기실 단계에서 이 칸을 보여 주기만 하면 된다) */
    P.lobby = function (host) {
        injectCss();
        var self = this, uf = uiFn('lobby');
        if (uf && this.room && !this._ui.p2lobby) {   /* P2 대기실: 명단·준비·시작 게이트를 그쪽이 그리고, 시작은 커널에 맡긴다 */
            try { var ok = uf(host, { room: this.room, turn: this, spec: this.spec, start: function () { return self.spec.onStart ? self.spec.onStart() : self.start(); } }); if (ok !== false) { this._ui.p2lobby = host; this._ui.lobbyEl = null; return; } } catch (e) { dbg('ui lobby', e); }
        }
        if (this._ui.p2lobby === host) return;
        if (this._ui.lobbyEl === host) { this._paintLobby(); return; }
        this._ui.lobbyEl = host;
        host.classList.add('lpt-lobby');
        host.addEventListener('click', function (e) {
            var b = e.target.closest('button'); if (!b || b.disabled) return;
            var d = b.dataset;
            if (d.inv) self.invite(); else if (d.qr) self.qr(); else if (d.more) self.sheet();
            else if (d.pick) { var kv = d.pick.split('|'); self.pick(kv[0], kv[1]); }
            else if (d.opt) { var ov = d.opt.split('|'), spec = (self.spec.options || []).filter(function (o) { return o.key === ov[0]; })[0]; if (spec) self.setOpt(ov[0], spec.values[+ov[1]]); }
            else if (d.addbot) self.addBot();
            else if (d.rmbot) self.rmBot(d.rmbot);
            else if (d.kick) self._kickAsk(d.kick, false);
            else if (d.go) { if (self.isHost) { if (self.spec.onStart) self.spec.onStart(); else self.start(); } else { var m = member(self.S(), self.me.pid); self.ready(!(m && m.rd)); } }
            else if (d.exit) self.leave();
            else if (d.watch) self.watch(d.watch === '1');
            else if (d.seat) self.claim(+d.seat);
        });
        this._paintLobby();
    };
    P._paintLobby = function () {
        var host = this._ui.lobbyEl; if (!host || this._ui.p2lobby === host) return;
        var S = this.S(), r = this.room, spec = this.spec, self = this;
        if (!r || !S) { host.innerHTML = '<div class="lpt-note">' + esc(tt('joining')) + '</div>'; return; }
        var me = member(S, this.me.pid), isH = this.isHost;
        var seated = S.roster.filter(function (m) { return m.seat != null; }).sort(function (a, b) { return a.seat - b.seat; });
        var specs = S.roster.filter(function (m) { return m.seat == null; });
        var max = spec.seats[1];
        var rows = seated.map(function (m) {
            var mine = m.p === self.me.pid, bot = m.r === 'bot';
            var pv = (spec.picks || []).map(function (pk) { var v = m.pick && m.pick[pk.key]; return v ? '<span class="lpt-pick">' + (pk.label ? pk.label(v) : esc(v)) + '</span>' : ''; }).join('');
            var st = m.r === 'host' ? '👑' : bot ? '🤖' : m.rd ? '✓' : '·';
            var dot = bot ? '' : '<span class="lpt-dot ' + (m.c === 'off' ? 'off' : m.c === 'away' ? 'away' : 'on') + '" aria-label="' + esc(m.c) + '"></span>';
            var tool = isH && bot ? '<button type="button" class="lpt-btn sm" data-rmbot="' + esc(m.p) + '" aria-label="remove">✕</button>' : isH && !mine && !bot ? '<button type="button" class="lpt-btn sm" data-kick="' + esc(m.p) + '" aria-label="' + esc(tt('kick')) + '">✕</button>' : '';
            var nm = bot ? (spec.botName ? spec.botName(m.seat, m.pick || {}) : tt('bot')) : m.n;
            return '<div class="lpt-p' + (mine ? ' me' : '') + '"><span class="lpt-tag" style="width:16px;text-align:center">' + st + '</span><span class="av">' + (bot ? '🤖' : AV[m.av | 0] || '🙂') + '</span><span class="nm">' + esc(nm) + (mine ? ' <span class="lpt-tag">(' + esc(tt('you')) + ')</span>' : '') + '</span>' + pv + dot + tool + '</div>';
        }).join('');
        var addBot = isH && spec.bots !== false && seated.length < max ? '<button type="button" class="lpt-btn sm" data-addbot="1">' + esc(tt('addBot')) + '</button>' : '';
        var specLine = specs.length ? '<div class="lpt-sec">👀 ' + esc(tt('specN', { n: specs.length })) + ' · ' + specs.map(function (m) { return esc(m.n); }).join(', ') + '</div>' : '';
        var picks = '';
        if (me && me.seat != null) (spec.picks || []).forEach(function (pk) {
            if (!pk.options) return;
            picks += '<div class="lpt-sec">' + esc(pk.title ? pk.title() : pk.key) + '</div><div class="lpt-chips">' + pk.options.map(function (v) {
                var holder = S.roster.filter(function (o) { return o.p !== me.p && o.seat != null && o.pick && o.pick[pk.key] === v; })[0];
                var tk = pk.unique && holder && holder.r !== 'bot', on = me.pick && me.pick[pk.key] === v;
                return '<button type="button" class="lpt-chip' + (on ? ' on' : '') + (tk ? ' tk' : '') + '" data-pick="' + esc(pk.key + '|' + v) + '"' + (tk ? ' disabled' : '') + '>' + (pk.label ? pk.label(v) : esc(v)) + '</button>';
            }).join('') + '</div>';
        });
        var opts = '';
        (spec.options || []).forEach(function (op) {
            var cur = S.opts && S.opts[op.key] !== undefined ? S.opts[op.key] : op.def;
            opts += '<div class="lpt-sec">' + esc(op.title ? op.title() : (op.key === 'turnSec' ? tt('turn') : op.key)) + '</div><div class="lpt-chips">' + op.values.map(function (v, i) {
                var lbl = op.label ? op.label(v) : (op.key === 'turnSec' ? (v ? tt('sec', { n: v }) : tt('off0')) : String(v));
                return '<button type="button" class="lpt-chip' + (v === cur ? ' on' : '') + '" data-opt="' + esc(op.key + '|' + i) + '"' + (isH ? '' : ' disabled') + '>' + esc(lbl) + '</button>';
            }).join('') + '</div>';
        });
        var go;
        if (isH) { var can = this.canStart(); go = '<button type="button" class="lpt-btn pri" data-go="1"' + (can ? '' : ' disabled') + '>▶ ' + esc(tt('start')) + '</button>'; }
        else if (me && me.seat != null) go = '<button type="button" class="lpt-btn pri" data-go="1">' + esc(me.rd ? tt('readyOn') : tt('ready')) + '</button>';
        else {
            var botS = seated.filter(function (m) { return m.r === 'bot'; })[0];
            go = seated.length < max ? '<button type="button" class="lpt-btn pri" data-watch="0">' + esc(tt('play')) + '</button>'
                : botS ? '<button type="button" class="lpt-btn pri" data-seat="' + botS.seat + '">' + esc(tt('play')) + '</button>'
                : '<button type="button" class="lpt-btn pri" disabled>' + esc(tt('play')) + '</button>';
        }
        var guests = seated.filter(function (m) { return m.r === 'player'; });
        var note = isH ? (spec.needGuest !== false && !guests.length ? tt('needGuest') : (this.canStart() ? '' : tt('waitAll'))) : (me && me.seat == null ? tt('spec') : tt('waitAll'));
        host.innerHTML = '<div class="lpt-hd"><b>' + esc(spec.name ? spec.name() : '') + '</b><span class="lpt-code">' + esc(G.LpRooms.util.fmtCode(r.code)) + '</span><span class="lpt-seal">' + esc(r.seal || '') + '</span><button type="button" class="lpt-btn sm" data-more="1" aria-label="room">⋯</button></div>' +
            '<div class="lpt-row2"><button type="button" class="lpt-btn pri" data-inv="1">💬 ' + esc(tt('invite')) + '</button><button type="button" class="lpt-btn" data-qr="1">▦ ' + esc(tt('qr')) + '</button></div>' +
            '<div class="lpt-list">' + rows + '</div>' + addBot + specLine + picks + opts +
            (spec.lobbyNote ? '<div class="lpt-note" style="margin:10px 0 0;opacity:.85">' + esc(spec.lobbyNote()) + '</div>' : '') +
            '<div class="lpt-foot"><button type="button" class="lpt-btn" data-exit="1">' + esc(isH ? tt('close') : tt('exit')) + '</button>' + go + '</div><div class="lpt-note">' + esc(note) + '</div>';
        this.hud();
    };

    function dbg() { try { if (G.localStorage.getItem('lpDebug') === '1') console.log.apply(console, ['[lpt]'].concat(Array.prototype.slice.call(arguments))); } catch (_) {} }

    /* ================================================================
       mount — 게임이 한 번 부른다
       ================================================================ */
    var _k = null;
    function mount(spec) {
        if (!spec || !spec.gameId) throw new Error('LpRoomsTurn.mount: gameId');
        spec.host = spec.host || {}; spec.client = spec.client || {};
        spec.seats = spec.seats || [2, 4];
        var K = new Kernel(spec);
        _k = K;
        var LR = G.LpRooms;
        if (LR) {
            var reg = {
                gameId: spec.gameId, kind: spec.kind || 'turn', seats: spec.seats, max: Math.min(12, spec.max || 12), lateJoin: spec.lateJoin || 'takeBot',
                picks: spec.picks, options: spec.options, bots: spec.bots !== false, hiddenInfo: !!spec.hiddenInfo,
                migratable: spec.migratable === undefined ? !spec.hiddenInfo : spec.migratable, delta: false,
                canStart: function (roster, S) {
                    if (spec.canStart) return spec.canStart(roster, S);
                    var seated = roster.filter(function (m) { return m.seat != null && m.r !== 'spec'; });
                    if (seated.length < spec.seats[0]) return false;
                    var gs = seated.filter(function (m) { return m.r === 'player'; });
                    if (spec.needGuest !== false && !gs.length) return false;
                    return gs.every(function (m) { return m.rd && m.c === 'on'; });
                }
            };
            if (spec.host.view) reg.view = function (game, pid) {
                if (!game) return { pub: game };
                var S = K.S(); var seat = pid == null ? null : K.seatOf(pid, S);
                return spec.host.view(game, seat, pid);
            };
            LR.adapter(reg);
            LR.on('room', function (r) { K._bind(r); });
            var cur = LR.current && LR.current(); if (cur) K._bind(cur);
        }
        return K;
    }

    G.LpRoomsTurn = { version: VER, mount: mount, current: function () { return _k; }, tt: tt, TM: TM, AV: AV, _Kernel: Kernel };
})(typeof window !== 'undefined' ? window : globalThis);
/* CHANGE LOG
   2026-09-30  P4 첫 구현 — 좌석·역할·준비·시작 게이트, 방장 시계 턴 마감, 멱등 의도(tn), 봇 대행(끊김 8초·afk 2회),
               자리 보호(예약 좌석·방장 '자리 넘기기' 60초·원주인 자동 복귀), 늦참(takeBot), 다시 하기(대기실),
               LpFair.chain 굴림(게스트 엔트로피·전원 검증), LpFair.deal 연결, 기본 대기실·HUD·방 시트·띠·확인창(6개 언어+en).
   2026-09-30  하네스(scripts/mp/run_turn.mjs T1~T12) 중 추가 — forced(할 게 하나뿐·패스 자동), lobbyOv(게임 위 대기실 겹창),
               drive:'game'(마작·구미: commit/startGame/finish/seatList), onStart·lobbyNote, 끊긴 좌석은 afk 로 세지 않음,
               '내가 할게요' 뒤 초과 횟수 0부터, 판 좌석표(tk.seats)는 판이 있을 때만(게임 전환 뒤 옛 표 무시).
               P2 연동 지점: window.LpRoomsUI(또는 LpRooms.UI)가 있으면 HUD·방장 끊김 띠는 그쪽에 맡기고,
               lobby(el,{room,turn,spec,start}) · sheet(room,{turn}) · invite(room,{url}) 함수가 있으면 호출(없으면 이 파일 폴백).
*/
