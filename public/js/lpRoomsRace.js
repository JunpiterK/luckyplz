/* =====================================================================
   lpRoomsRace.js — LuckyPlz Rooms v2 레이스 커널 (P5)
   설계: docs/multiplayer/DESIGN.md §6.5 (+ §6.0.3 hb 편승 · §6.1.2 LpFair.draw · §6.1.4 동시 출발)
   의존: lpRoomsCore.js · lpFair.js · lpRoomsUI.js (v2 로더가 싣는다). 이 파일은 게임 훅 블록이
   LpRoomsQ 콜백 안에서 필요할 때만 싣는다 → v2 방이 아니면 한 줄도 돌지 않는다(솔로 경로 불변).

   ── API ───────────────────────────────────────────────────────────────
   declare global { interface Window { LpRoomsRace: LpRoomsRace } }

   interface RaceCtx {
     seed: string;                       // 공정 추첨 seed hex(64) — 모든 기기 동일
     rng(label: string): () => number;   // LpFair.rng(seed,label).float — 게임 스트림 분리용 [0,1)
     opts: object;                       // 방장 옵션(S.opts) — 예 {mode:'sprint40'}
     heat: number;                       // 판 번호
   }
   interface RaceSpec {                  // 게임 훅이 register() 로 넘긴다
     gameId: string;
     metric: 'score' | 'time';           // score = 높을수록, time = 완주 시간 짧을수록
     metricFor?(opts): 'score' | 'time'; // 옵션별 순위 방식(없으면 metric)
     durationS: number;                  // score: 판 길이(초) · time: 상한(초). 끝나면 stop('time')
     options?: {key, values, def}[];     // 대기실 옵션(방장) — 커널이 어댑터·UI 에 넘긴다
     labels?: object;                    // UI.config labels (옵션 표시)
     durFor?(opts): number;              // 옵션별 판 길이(초) — 없으면 durationS
     start(ctx: RaceCtx): void;          // 시드로 새 판을 '지금' 시작(시작 화면 없이)
     progress(): number;                 // 실시간 값 — score: 점수, time: 진행(줄·짝 수 …)
     over(): boolean;                    // 판이 스스로 끝났는가(탑아웃·완주·목숨 소진)
     done?(): boolean;                   // time: 완주했는가 (완주한 사람만 시간으로 순위)
     final?(): {v?: number};             // 최종 값(없으면 progress())
     stop(reason: 'time'|'bg'|'leave'|'host'): void;   // 판을 지금 끝낸다(그 순간 기록)
     end?(): void;                       // 판 종료 뒤 — 시드 RNG 해제(솔로 복귀)
     unlock?(): void;                    // 대기실에서 탭할 때 오디오 잠금 해제
     fmt?(v: number): string;            // 값 표시
     fmtProg?(g: number): string;        // (time) 미완주자의 진행 표시
     probe?(n: number): any[];           // 테스트: 시드 스트림으로 만든 첫 n 개(조각·벽돌·패) — R1
   }
   interface LpRoomsRace {
     version: string;
     register(spec: RaceSpec): void;     // 게임 1회 — 어댑터(kind:'race')·UI 시작 훅·방 바인딩
     hostStart(room?): Promise<void>;    // 방장: 공정 추첨 → t0 확정 → room.start (UI.onStart 가 부른다)
     info(): object;                     // 디버그·하네스: {st, heat, seed, t0, skew, trueStart, fin, board}
     active(): boolean;                  // 지금 레이스 판이 도는 중인가
   }

   ── 흐름 (§6.5) ────────────────────────────────────────────────────
   방장 [시작 ▶] → UI.onStart → LpFair.draw(params={g,heat,opts,ent}) → seed · st
     → setState(S.game={heat, st:'run', seed, round, t0=st+3000, dur, opts, ent, nm})
     → room.start({countdownMs:t0-now}) : phase starting → playing(t0)
   모든 참가자: t0 - 오프셋 로컬 시각에 spec.start(ctx) (3-2-1 카운트다운 오버레이)
   진행: 게스트 hb 'sc'=[heat,g,alive,done,t] 편승(8s), 방장 hb 'bd'=[heat,[[p,g,a,d,t]…]] 편승(5s) — 추가 메시지 0
   종료: 각자 g{e:'x', k:'final'} 1통(서명). 방장이 모아 setState(S.game.st='res', res) + x('board')(재전송) + end()
   백그라운드(visibilitychange hidden, 캡처 단계) = 그 순간 기록으로 종료. 늦참 = 관전(wq) → toLobby 때 좌석.
   다시 하기 = 결과 카드 [↻ 한 판 더] → toLobby()(준비 게이트).
   ===================================================================== */
(function (G) {
    'use strict';
    if (G.LpRoomsRace && G.LpRoomsRace.version) return;
    var D = G.document;
    var VER = '2.0.0';
    var CD_MS = 3000;          /* 3-2-1 */
    var GRACE = 12000;         /* 판 끝 + 12초 안에 안 온 final 은 마지막 hb 값으로 */
    var OFF_GRACE = 10000;     /* 끊긴 사람(off) 은 10초 기다린 뒤 마지막 값으로 */

    var SPEC = null, ROOM = null, offs = [], tick = 0, busy = false;
    var RUN = null;            /* 이 기기의 판 {heat, seed, t0, dur, st:'wait'|'play'|'done', ...} */
    var LIVE = {};             /* 방장: pid → {g,a,d,t,at} (hb 편승) */
    var FIN = {};              /* 방장: pid → final */
    var FINH = 0;              /* FIN 이 속한 heat */
    var BOARD = null;          /* 멤버: 방장 bd [heat, rows] */
    var FAIR = {};             /* round → {ok, seed, cert, wok, wbad} */
    var SHOWN = 0;             /* 결과 카드를 띄운 heat */

    /* ── 문구 (짧게 · 아이콘 우선) ─────────────────────────────── */
    var L = {
        ko: { next: '다음 판부터 참가', wait: '다른 사람 기다리는 중', again: '한 판 더', close: '닫기', self: '기록 신고', waitHost: '방장이 시작해요', go: 'GO!', mode: '모드', rank: '{a}/{b}등' },
        en: { next: 'You join next heat', wait: 'Waiting for others', again: 'Play again', close: 'Close', self: 'Self-reported', waitHost: 'Host starts next', go: 'GO!', mode: 'Mode', rank: '#{a}/{b}' },
        ja: { next: '次のレースから参加', wait: 'ほかの人を待っています', again: 'もう一回', close: '閉じる', self: '自己申告', waitHost: 'ホストが開始', go: 'GO!', mode: 'モード', rank: '{a}/{b}位' },
        zh: { next: '下一局加入', wait: '等待其他人', again: '再来一局', close: '关闭', self: '自报成绩', waitHost: '等房主开始', go: 'GO!', mode: '模式', rank: '第{a}/{b}' },
        es: { next: 'Entras en la próxima', wait: 'Esperando a los demás', again: 'Otra vez', close: 'Cerrar', self: 'Autodeclarado', waitHost: 'El anfitrión inicia', go: '¡YA!', mode: 'Modo', rank: '{a}/{b}' },
        pt: { next: 'Você entra na próxima', wait: 'Esperando os outros', again: 'De novo', close: 'Fechar', self: 'Autodeclarado', waitHost: 'O anfitrião inicia', go: 'VAI!', mode: 'Modo', rank: '{a}/{b}' },
        de: { next: 'Du spielst nächste Runde', wait: 'Warte auf andere', again: 'Nochmal', close: 'Schließen', self: 'Selbst gemeldet', waitHost: 'Host startet', go: 'LOS!', mode: 'Modus', rank: '{a}/{b}' },
        fr: { next: 'Tu joues la prochaine', wait: 'On attend les autres', again: 'Rejouer', close: 'Fermer', self: 'Auto-déclaré', waitHost: 'L’hôte lance', go: 'GO !', mode: 'Mode', rank: '{a}/{b}' },
        ru: { next: 'Вы в следующем заезде', wait: 'Ждём остальных', again: 'Ещё раз', close: 'Закрыть', self: 'Со слов игрока', waitHost: 'Хост начнёт', go: 'СТАРТ!', mode: 'Режим', rank: '{a}/{b}' },
        ar: { next: 'تنضم في الجولة التالية', wait: 'بانتظار الآخرين', again: 'مرة أخرى', close: 'إغلاق', self: 'نتيجة ذاتية', waitHost: 'المضيف يبدأ', go: 'انطلق!', mode: 'الوضع', rank: '{a}/{b}' },
        hi: { next: 'अगली बारी में शामिल', wait: 'बाकी का इंतज़ार', again: 'फिर से', close: 'बंद', self: 'स्व-घोषित', waitHost: 'होस्ट शुरू करेगा', go: 'GO!', mode: 'मोड', rank: '{a}/{b}' },
        th: { next: 'เข้าร่วมรอบหน้า', wait: 'รอคนอื่นอยู่', again: 'อีกรอบ', close: 'ปิด', self: 'แจ้งผลเอง', waitHost: 'โฮสต์จะเริ่ม', go: 'GO!', mode: 'โหมด', rank: '{a}/{b}' },
        id: { next: 'Ikut babak berikutnya', wait: 'Menunggu yang lain', again: 'Main lagi', close: 'Tutup', self: 'Lapor sendiri', waitHost: 'Host memulai', go: 'GO!', mode: 'Mode', rank: '{a}/{b}' },
        vi: { next: 'Vào lượt sau', wait: 'Đang chờ người khác', again: 'Chơi lại', close: 'Đóng', self: 'Tự báo', waitHost: 'Chủ phòng bắt đầu', go: 'CHẠY!', mode: 'Chế độ', rank: '{a}/{b}' },
        tr: { next: 'Sonraki turda', wait: 'Diğerleri bekleniyor', again: 'Tekrar', close: 'Kapat', self: 'Beyan edilen', waitHost: 'Ev sahibi başlatır', go: 'BAŞLA!', mode: 'Mod', rank: '{a}/{b}' }
    };
    function lang() { var l = 'en'; try { l = (G.localStorage.getItem('luckyplz_lang') || 'en').toLowerCase().slice(0, 2); } catch (_) {} return l === 'gb' ? 'en' : l; }
    function t(k, v) { var s = (L[lang()] || L.en)[k] || L.en[k] || k; if (v) for (var x in v) s = s.split('{' + x + '}').join(v[x]); return s; }

    /* ── 도구 ─────────────────────────────────────────────────── */
    function now() { return Date.now(); }
    function clk() { return ROOM ? ROOM.clock() : now(); }
    function E(tag, cls, txt) { var e = D.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
    function ssGet(k) { try { return G.sessionStorage.getItem(k); } catch (_) { return null; } }
    function ssSet(k, v) { try { if (v == null) G.sessionStorage.removeItem(k); else G.sessionStorage.setItem(k, v); } catch (_) {} }
    function fmtTime(ms) {
        ms = Math.max(0, Math.round(ms || 0));
        var m = Math.floor(ms / 60000), s = Math.floor(ms / 1000) % 60, c = Math.floor(ms / 10) % 100;
        return m + ':' + (s < 10 ? '0' : '') + s + '.' + (c < 10 ? '0' : '') + c;
    }
    function fmtClock(ms) { ms = Math.max(0, ms); var s = Math.ceil(ms / 1000); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
    function fmtV(v) { if (SPEC && SPEC.fmt) try { return SPEC.fmt(v); } catch (_) {} return Math.round(v || 0).toLocaleString(); }
    function fmtRow(r) {
        if (!SPEC || MET() !== 'time') return fmtV(r.v);
        if (r.d) return fmtTime(r.v);
        if (SPEC.fmtProg) try { return SPEC.fmtProg(r.g || 0); } catch (_) {}
        return String(r.g || 0);
    }
    function name(p, g) {
        var m = ROOM && ROOM.roster().filter(function (x) { return x.p === p; })[0];
        if (m) return m.n;
        return (g && g.nm && g.nm[p]) || p.slice(0, 6);
    }
    function avOf(p) {
        var m = ROOM && ROOM.roster().filter(function (x) { return x.p === p; })[0];
        var av = (G.LpRoomsUI && G.LpRoomsUI.avatars) || [];
        return m && av[m.av] ? av[m.av] : '🙂';
    }
    function hexOf(u8) { return G.LpFair ? G.LpFair.hex(u8) : ''; }
    function game() { var S = ROOM && ROOM.state(); return S && S.game && S.game.heat ? S.game : null; }
    /* 판의 순위 방식 — 옵션에 따라 다를 수 있다(테트로미노: 스프린트 = 시간). 판이 정해지면 S.game.m 이 진실 */
    function metricOf(opts) { if (SPEC.metricFor) try { var m = SPEC.metricFor(opts || {}); if (m === 'time' || m === 'score') return m; } catch (_) {} return SPEC.metric === 'time' ? 'time' : 'score'; }
    function MET() { var g = game(); return (g && g.m) || metricOf({}); }
    function durOf(opts) { var s = SPEC.durFor ? SPEC.durFor(opts || {}) : SPEC.durationS; return Math.max(10, Math.min(1800, +s || 120)) * 1000; }

    /* 순위: score = v 큰 순(같으면 먼저 끝난 순) · time = 완주자 시간 짧은 순 → 미완주 진행 큰 순 */
    function better(a, b) {
        if (MET() === 'time') {
            if (!!a.d !== !!b.d) return a.d ? -1 : 1;
            if (a.d) return (a.v - b.v) || (a.p < b.p ? -1 : 1);
            return ((b.g || 0) - (a.g || 0)) || ((a.t || 0) - (b.t || 0)) || (a.p < b.p ? -1 : 1);
        }
        return ((b.v || 0) - (a.v || 0)) || ((a.t || 0) - (b.t || 0)) || (a.p < b.p ? -1 : 1);
    }

    /* ── CSS ──────────────────────────────────────────────────── */
    var cssDone = false;
    function css() {
        if (cssDone) return; cssDone = true;
        var s = E('style');
        s.textContent =
            '.lprc-cd{position:fixed;inset:0;z-index:9600;display:flex;align-items:center;justify-content:center;pointer-events:none;' +
            'font:900 min(34vw,190px)/1 "Orbitron",system-ui,sans-serif;color:#fff;text-shadow:0 0 30px rgba(0,217,255,.8),0 6px 0 rgba(0,0,0,.45)}' +
            '.lprc-cd.go{color:#FFE66D;text-shadow:0 0 34px rgba(255,200,40,.9),0 6px 0 rgba(0,0,0,.45);font-size:min(24vw,140px)}' +
            '.lprc-cd b{display:block;animation:lprcPop .9s ease-out both}' +
            '@keyframes lprcPop{0%{transform:scale(1.8);opacity:0}25%{transform:scale(1);opacity:1}85%{opacity:1}100%{transform:scale(.85);opacity:0}}' +
            /* 순위 칩 — 모든 게임 상단 바 가운데는 장식용 제목뿐이라(조작 버튼·점수판 없음) 그 위에 얹는다 */
            '.lprc-chip{position:fixed;z-index:9050;top:calc(8px + env(safe-area-inset-top,0px));left:50%;transform:translateX(-50%);height:30px;box-sizing:border-box;' +
            'pointer-events:none;display:flex;gap:8px;align-items:center;padding:0 12px;border-radius:15px;font:700 12px/1 system-ui,sans-serif;white-space:nowrap;' +
            'color:#fff;background:rgba(10,10,26,.94);border:1px solid rgba(0,217,255,.35);font-variant-numeric:tabular-nums;max-width:calc(100vw - 150px);overflow:hidden}' +
            '.lprc-chip i{font-style:normal;opacity:.85}.lprc-chip .me{color:#00D9FF}.lprc-chip .ld{color:#FFE66D}' +
            '.lprc-card{position:fixed;inset:0;z-index:9550;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(4,5,14,.66);' +
            '-webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px);touch-action:manipulation}' +
            '.lprc-box{width:100%;max-width:360px;max-height:calc(100dvh - 32px);overflow:auto;border-radius:20px;padding:18px 16px 14px;color:#fff;' +
            'background:linear-gradient(180deg,#191b38,#0e0f24);border:1px solid rgba(255,255,255,.14);box-shadow:0 20px 60px rgba(0,0,0,.5);font:15px/1.4 system-ui,sans-serif}' +
            '.lprc-h{display:flex;align-items:center;gap:8px;font:900 20px/1.2 "Orbitron",system-ui,sans-serif;margin:0 0 10px}' +
            '.lprc-h .sp{flex:1}.lprc-row{display:flex;align-items:center;gap:8px;padding:7px 8px;border-radius:12px;margin:3px 0;background:rgba(255,255,255,.04)}' +
            '.lprc-row.me{background:rgba(0,217,255,.14);outline:1px solid rgba(0,217,255,.4)}' +
            '.lprc-row .rk{width:28px;text-align:center;font-weight:900}.lprc-row .nm{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
            '.lprc-row .v{font-weight:800;font-variant-numeric:tabular-nums}.lprc-row .st{width:20px;text-align:center;opacity:.85}' +
            '.lprc-ft{display:flex;gap:8px;margin-top:12px}.lprc-ft button{flex:1;min-height:46px;border-radius:14px;border:0;font:800 15px system-ui,sans-serif;cursor:pointer}' +
            '.lprc-ft .pri{background:linear-gradient(180deg,#00D9FF,#0090FF);color:#001828}.lprc-ft .sec{background:rgba(255,255,255,.1);color:#fff}' +
            '.lprc-mut{font-size:12px;opacity:.6;text-align:center;margin-top:8px}.lprc-bdg{display:flex;justify-content:center;margin-top:8px}';
        (D.head || D.documentElement).appendChild(s);
    }

    /* ── 카운트다운 ───────────────────────────────────────────── */
    var cdEl = null, cdLast = null, cdT = 0;
    function cdShow() {
        if (!RUN) return;
        css();
        if (!cdEl) { cdEl = E('div', 'lprc-cd'); cdEl.setAttribute('aria-live', 'polite'); D.body.appendChild(cdEl); }
        if (cdT) return;
        cdT = setInterval(cdTick, 50); cdTick();
    }
    function cdTick() {
        if (!RUN || !cdEl) return cdHide();
        var left = RUN.t0 - clk(), txt;
        if (left > CD_MS) txt = '🏁';
        else if (left > 0) txt = String(Math.ceil(left / 1000));
        else if (left > -700) txt = t('go');
        else return cdHide();
        if (txt === cdLast) return;
        cdLast = txt;
        cdEl.className = 'lprc-cd' + (left <= 0 ? ' go' : '');
        cdEl.innerHTML = ''; cdEl.appendChild(E('b', '', txt));
    }
    function cdHide() { clearInterval(cdT); cdT = 0; cdLast = null; if (cdEl) { cdEl.remove(); cdEl = null; } }

    /* ── 실시간 순위 칩 ───────────────────────────────────────── */
    var chipEl = null;
    function rowsLive() {
        var g = game(); if (!g) return [];
        var rows = {};
        (g.ent || []).forEach(function (p) { rows[p] = { p: p, v: 0, g: 0, a: 1, d: 0, t: 0 }; });
        if (ROOM.isHost) {
            Object.keys(LIVE).forEach(function (p) { if (rows[p]) { var x = LIVE[p]; rows[p].g = x.g; rows[p].a = x.a; rows[p].d = x.d; rows[p].t = x.t; } });
        } else if (BOARD && BOARD[0] === g.heat) {
            (BOARD[1] || []).forEach(function (r) { if (rows[r[0]]) { rows[r[0]].g = r[1]; rows[r[0]].a = r[2]; rows[r[0]].d = r[3]; rows[r[0]].t = r[4]; } });
        }
        if (RUN && RUN.heat === g.heat && rows[ROOM.me.pid]) {
            var mine = rows[ROOM.me.pid];
            mine.g = RUN.g; mine.a = RUN.st === 'play' ? 1 : 0; mine.d = RUN.fin ? RUN.fin.d : 0; mine.t = RUN.fin ? RUN.fin.t : 0;
        }
        return Object.keys(rows).map(function (p) { var r = rows[p]; r.v = MET() === 'time' ? (r.d ? r.t : 0) : r.g; return r; }).sort(better);
    }
    function chip() {
        var g = game();
        var on = g && g.st === 'run' && ROOM && (ROOM.state().phase === 'playing' || ROOM.state().phase === 'starting');
        if (!on) { if (chipEl) { chipEl.remove(); chipEl = null; } return; }
        css();
        if (!chipEl) { chipEl = E('div', 'lprc-chip'); chipEl.setAttribute('aria-hidden', 'true'); D.body.appendChild(chipEl); }
        var rows = rowsLive(), me = ROOM.me.pid, ix = -1;
        rows.forEach(function (r, i) { if (r.p === me) ix = i; });
        var parts = [];
        var left = g.t0 + g.dur - clk();
        parts.push('<i>⏱ ' + fmtClock(Math.min(g.dur, left)) + '</i>');
        if (ix >= 0) parts.push('<span class="me">' + t('rank', { a: ix + 1, b: rows.length }) + '</span>');
        else parts.push('<i>👀 ' + esc(t('next')) + '</i>');
        if (rows[0]) parts.push('<span class="ld">🥇 ' + esc(fmtRow(rows[0])) + '</span>');
        if (RUN && RUN.st === 'done' && g.st === 'run') parts.push('<i>⏳</i>');
        var h = parts.join('');
        if (chipEl._h !== h) { chipEl._h = h; chipEl.innerHTML = h; }
    }
    function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

    /* ── 결과 카드 ───────────────────────────────────────────── */
    var cardEl = null;
    function cardHide() { if (cardEl) { cardEl.remove(); cardEl = null; } }
    function cardShow(g) {
        if (!g || !g.res) return;
        css(); cardHide();
        SHOWN = g.heat;
        var root = E('div', 'lprc-card'), box = E('div', 'lprc-box');
        root.setAttribute('role', 'dialog');
        /* 게임 캔버스의 touchstart preventDefault 가 click 합성을 막지 않게 — 카드 안 터치는 여기서 멈춘다 */
        ['touchstart', 'pointerdown', 'mousedown'].forEach(function (ev) { root.addEventListener(ev, function (e) { e.stopPropagation(); }, { passive: true }); });
        var h = E('div', 'lprc-h'); h.appendChild(E('span', '', '🏁 #' + g.heat)); h.appendChild(E('span', 'sp'));
        var gm = (G.LpGames && G.LpGames.name) ? G.LpGames.name(SPEC.gameId) : '';
        h.appendChild(E('span', 'lprc-mut', gm)); box.appendChild(h);
        var ST = { fin: '✓', out: '💥', time: '⏱', bg: '🌙', leave: '🚪', lost: '📴', host: '⏹', error: '⚠' };
        g.res.forEach(function (r, i) {
            var row = E('div', 'lprc-row' + (r.p === ROOM.me.pid ? ' me' : ''));
            row.appendChild(E('span', 'rk', i < 3 ? ['🥇', '🥈', '🥉'][i] : String(i + 1)));
            row.appendChild(E('span', 'nm', avOf(r.p) + ' ' + name(r.p, g)));
            row.appendChild(E('span', 'v', fmtRow(r)));
            row.appendChild(E('span', 'st', ST[r.s] || ''));
            box.appendChild(row);
        });
        var bd = E('div', 'lprc-bdg'), b = E('span');
        bd.appendChild(b); box.appendChild(bd);
        var f = FAIR[g.round] || {};
        var info = f.wbad ? { kind: 'mismatch', n: f.wbad, round: g.round, cert: f.cert } : (f.wok > 1 ? { kind: 'verified', n: f.wok, round: g.round, cert: f.cert } : { kind: 'seed', round: g.round, cert: f.cert });
        if (f.ok === false) info = { kind: 'mismatch', n: 1, round: g.round, cert: f.cert };
        try { if (G.LpRoomsUI && G.LpRoomsUI.badge) G.LpRoomsUI.badge(b, info); else if (G.LpFair) G.LpFair.badge(b, info); } catch (_) {}
        box.appendChild(E('div', 'lprc-mut', '📝 ' + t('self')));
        var ft = E('div', 'lprc-ft');
        var cl = E('button', 'sec', t('close')); cl.type = 'button';
        cl.addEventListener('click', function (e) { e.preventDefault(); cardHide(); });
        ft.appendChild(cl);
        if (ROOM.isHost) {
            var ag = E('button', 'pri', '↻ ' + t('again')); ag.type = 'button';
            ag.addEventListener('click', function (e) { e.preventDefault(); cardHide(); try { ROOM.toLobby(); } catch (_) {} });
            ft.appendChild(ag);
        }
        box.appendChild(ft);
        if (!ROOM.isHost) box.appendChild(E('div', 'lprc-mut', t('waitHost')));
        root.appendChild(box);
        D.body.appendChild(root);
        cardEl = root;
        try { if (G.LpRoomsUI && G.LpRoomsUI.say) G.LpRoomsUI.say('🏁 #' + g.heat); } catch (_) {}
    }

    /* ================================================================
       방장 — 시작 · 수집 · 확정
       ================================================================ */
    async function hostStart(room) {
        if (busy || !room.isHost) return;
        var S = room.state(); if (!S || S.phase !== 'lobby') return;
        busy = true;
        try {
            var ent = S.roster.filter(function (m) { return (m.r === 'host' || m.r === 'player') && m.c !== 'off'; }).map(function (m) { return m.p; }).sort();
            var nm = {}; S.roster.forEach(function (m) { if (ent.indexOf(m.p) >= 0) nm[m.p] = m.n; });
            var opts = {}; (SPEC.options || []).forEach(function (o) { opts[o.key] = S.opts && S.opts[o.key] !== undefined ? S.opts[o.key] : o.def; });
            var heat = ((S.game && S.game.heat) || 0) + 1;
            var d = await G.LpFair.draw(room, { params: { g: SPEC.gameId, heat: heat, opts: opts, ent: ent } });
            if (!room.isHost || room._left) return;
            var t0 = Math.round(d.startAt + CD_MS), dur = durOf(opts);
            FIN = {}; LIVE = {}; FINH = heat;
            room.setState(function (S2) {
                S2.game = { heat: heat, st: 'run', seed: hexOf(d.seed), round: d.round, t0: t0, dur: dur, opts: opts, ent: ent, nm: nm, m: metricOf(opts) };
            });
            room.start({ countdownMs: Math.max(0, t0 - room.clock()) });
        } catch (e) {
            if (G.console) console.warn('[LpRoomsRace] start', e);
            try { G.LpRoomsUI && G.LpRoomsUI.toast('⚠'); } catch (_) {}
        } finally { busy = false; }
    }
    function hostRecord(p, f) {
        var g = game(); if (!g || !f || f.h !== g.heat || g.st !== 'run') return;
        if ((g.ent || []).indexOf(p) < 0 || FIN[p]) return;
        FIN[p] = { v: +f.v || 0, g: +f.g || 0, t: Math.max(0, +f.t || 0), d: f.d ? 1 : 0, s: String(f.s || 'fin').slice(0, 8), dig: String(f.dig || '').slice(0, 32) };
        if (FINH !== g.heat) FINH = g.heat;
        LIVE[p] = { g: FIN[p].g, a: 0, d: FIN[p].d, t: FIN[p].t, at: now() };
    }
    function hostTick() {
        var g = game(); if (!g || !ROOM.isHost || g.st !== 'run') return;
        if (FINH !== g.heat) { FIN = {}; FINH = g.heat; }
        /* 순위판 편승(다음 방장 hb 에 실린다 — 추가 메시지 0) */
        /* 행 = [pid, 진행, 달리는 중, 완주, 시간, final 받음] — 마지막 칸은 게스트의 final 재전송을 멈추는 확인 */
        var bd = (g.ent || []).map(function (p) { var x = LIVE[p] || {}; return [p, x.g || 0, x.a == null ? 1 : x.a, x.d || 0, x.t || 0, FIN[p] ? 1 : 0]; });
        ROOM.hb('bd', [g.heat, bd]);
        var c = clk(), end = g.t0 + g.dur;
        if (c < g.t0) return;
        var ros = {}; ROOM.roster().forEach(function (m) { ros[m.p] = m; });
        var all = (g.ent || []).every(function (p) {
            if (FIN[p]) return true;
            var m = ros[p], x = LIVE[p] || (LIVE[p] = { g: 0, a: 1, d: 0, t: 0 });
            if (!m || m.c === 'off') { if (!x.offAt) x.offAt = now(); return now() - x.offAt > OFF_GRACE; }
            x.offAt = 0;
            return false;
        });
        if (all || c > end + GRACE) hostFinalize();
    }
    function hostFinalize() {
        var g = game(); if (!g || g.st !== 'run' || !ROOM.isHost) return;
        var rows = (g.ent || []).map(function (p) {
            var f = FIN[p];
            if (f) return { p: p, v: f.v, g: f.g, t: f.t, d: f.d, s: f.s, dig: f.dig };
            var x = LIVE[p] || {};
            return { p: p, v: MET() === 'time' ? 0 : (x.g || 0), g: x.g || 0, t: x.t || 0, d: 0, s: 'lost' };
        });
        rows.forEach(function (r) { if (MET() === 'time' && !r.d) r.v = 0; });
        rows.sort(better);
        rows.forEach(function (r, i) { r.rk = i + 1; });
        ROOM.setState(function (S) { S.game.st = 'res'; S.game.res = rows; });
        ROOM.x('board', { heat: g.heat, res: rows });
        try { ROOM.end(); } catch (_) {}
    }

    /* ================================================================
       참가자 — 예약 · 출발 · 진행 · 종료
       ================================================================ */
    function runKey(g) { return 'lprace:' + ROOM.code + ':' + g.heat; }
    function sync() {
        var g = game(); if (!ROOM || !SPEC) return;
        var S = ROOM.state();
        if (!g) return;
        if (g.st === 'run') {
            var mine = (g.ent || []).indexOf(ROOM.me.pid) >= 0;
            if (mine && (!RUN || RUN.heat !== g.heat)) {
                RUN = { heat: g.heat, seed: g.seed, round: g.round, t0: g.t0, dur: g.dur, opts: g.opts || {}, st: 'wait', g: 0, trace: [], fin: null, sent: 0 };
                if (ssGet(runKey(g)) === 'started') {
                    /* 판 도중 새로고침 — 판은 사라졌다. 마지막 기록으로 끝낸다 */
                    RUN.st = 'play'; RUN.g = +(ssGet(runKey(g) + ':g') || 0);
                    endRun('leave', true);
                } else { arm(); cdShow(); }
            }
        } else if (g.st === 'res') {
            if (RUN && RUN.heat === g.heat && RUN.st === 'play') endRun('time');
            if (S.phase === 'result' && SHOWN !== g.heat) { cdHide(); cardShow(g); try { SPEC.end && SPEC.end(); } catch (_) {} }
        }
        chip();
    }
    var armT = 0;
    function arm() {
        clearTimeout(armT);
        if (!RUN || RUN.st !== 'wait') return;
        var d = RUN.t0 - clk();
        if (d <= 0) return fire();
        armT = setTimeout(arm, d > 60 ? d - 40 : d);
    }
    function ctxOf(r) {
        var seed = r.seed;
        return { seed: seed, opts: r.opts, heat: r.heat, rng: function (label) { var q = G.LpFair.rng(seed, String(label)); return q.float; } };
    }
    function fire() {
        if (!RUN || RUN.st !== 'wait') return;
        var g = game(); if (!g || g.heat !== RUN.heat || g.st !== 'run') return;
        RUN.st = 'play';
        RUN.startedAt = clk();
        RUN.skew = RUN.startedAt - RUN.t0;
        try { RUN.trueStart = (G.performance && performance.timeOrigin) ? performance.timeOrigin + performance.now() : Date.now(); } catch (_) { RUN.trueStart = Date.now(); }
        ssSet(runKey(g), 'started');
        try { SPEC.start(ctxOf(RUN)); }
        catch (e) { if (G.console) console.warn('[LpRoomsRace] spec.start', e); return endRun('error'); }
        poll();
    }
    function poll() {
        if (!RUN || RUN.st !== 'play') return;
        var g = game();
        var v = 0; try { v = +SPEC.progress() || 0; } catch (_) {}
        if (v !== RUN.g) {
            RUN.g = v; RUN.trace.push([clk() - RUN.t0, v]); if (RUN.trace.length > 400) RUN.trace.splice(0, 100);
            if (g) ssSet(runKey(g) + ':g', String(v));
            pushSc(1);
        }
        var over = false; try { over = !!SPEC.over(); } catch (_) {}
        if (over) return endRun('over');
        if (clk() >= RUN.t0 + RUN.dur) return endRun('time');
    }
    function pushSc(alive) {
        if (!RUN || !ROOM) return;
        var d = RUN.fin ? RUN.fin.d : 0, tt = RUN.fin ? RUN.fin.t : 0;
        if (ROOM.isHost) LIVE[ROOM.me.pid] = { g: RUN.g, a: alive, d: d, t: tt, at: now() };
        else ROOM.hb('sc', [RUN.heat, RUN.g, alive, d, tt]);
    }
    function endRun(reason, silent) {
        if (!RUN || RUN.st !== 'play') return;
        RUN.st = 'done';
        if (reason !== 'over' && !silent) { try { SPEC.stop(reason); } catch (e) { if (G.console) console.warn('[LpRoomsRace] spec.stop', e); } }
        var g0 = RUN.g; try { g0 = +SPEC.progress() || RUN.g; } catch (_) {}
        if (silent) g0 = RUN.g;
        RUN.g = g0;
        var fv = null; if (!silent) try { fv = SPEC.final ? SPEC.final() : null; } catch (_) {}
        var dn = false; if (!silent && reason === 'over') try { dn = SPEC.done ? !!SPEC.done() : false; } catch (_) {}
        var tt = Math.max(0, Math.round(clk() - RUN.t0));
        var v = MET() === 'time' ? (dn ? tt : 0) : (fv && fv.v != null ? +fv.v : g0);
        var s = reason === 'over' ? (dn ? 'fin' : 'out') : reason;
        var dig = '';
        try { dig = hexOf(G.LpFair.H('lpr5-dig|' + RUN.seed + '|' + RUN.heat + '|' + v + '|' + tt + '|' + JSON.stringify(RUN.trace))).slice(0, 16); } catch (_) {}
        RUN.fin = { h: RUN.heat, v: v, g: g0, t: tt, d: dn ? 1 : 0, s: s, dig: dig };
        pushSc(0);
        sendFinal();
        chip();
    }
    var finT = 0;
    function sendFinal() {
        if (!RUN || !RUN.fin || !ROOM) return;
        var g = game();
        if (g && g.heat === RUN.heat && g.st === 'res') return;
        if (ROOM.isHost) { hostRecord(ROOM.me.pid, RUN.fin); return; }
        if (finAcked()) return;
        ROOM.x('final', RUN.fin);
        RUN.sent++;
        /* 방장이 못 받았을 수 있다(방장 승계·새로고침·유실) — 방장 hb 순위판에 '받음' 표시가 없으면 7초마다, 최대 5번 더 */
        clearTimeout(finT);
        if (RUN.sent < 6) finT = setTimeout(sendFinal, 7000);
    }
    function finAcked() {
        if (!RUN || !BOARD || BOARD[0] !== RUN.heat) return false;
        var me = ROOM.me.pid, r = (BOARD[1] || []).filter(function (x) { return x[0] === me; })[0];
        return !!(r && r[5]);
    }

    /* 백그라운드 = 그 순간 기록으로 종료 (캡처 단계 — 게임·lpAutoPause 핸들러보다 먼저) */
    function onVis() { if (D.visibilityState === 'hidden' && RUN && RUN.st === 'play') endRun('bg'); }
    function onHide() { if (RUN && RUN.st === 'play') endRun('leave'); }

    /* ================================================================
       바인딩
       ================================================================ */
    function unbind() {
        offs.forEach(function (f) { try { f(); } catch (_) {} }); offs = [];
        clearInterval(tick); tick = 0; clearTimeout(armT); clearTimeout(finT);
        if (RUN && RUN.st === 'play') endRun('leave');
        cdHide(); cardHide(); if (chipEl) { chipEl.remove(); chipEl = null; }
        RUN = null; ROOM = null; BOARD = null;
    }
    function bind(room) {
        if (!room || !SPEC || room === ROOM) return;
        if (room.gameId && room.gameId !== SPEC.gameId) return;
        if (ROOM) unbind();
        ROOM = room;
        offs.push(room.on('state', function () { sync(); }));
        offs.push(room.on('phase', function (ph) {
            if (ph === 'lobby') {
                cdHide(); cardHide(); if (chipEl) { chipEl.remove(); chipEl = null; }
                if (RUN && RUN.st === 'play') endRun('host');
                if (RUN) { try { SPEC.end && SPEC.end(); } catch (_) {} }
                RUN = null; BOARD = null;
            }
            sync();
        }));
        offs.push(room.on('hb', function (from, d) {
            if (!d) return;
            if (from && room.isHost && Array.isArray(d.sc)) {
                var g = game(); var sc = d.sc;
                if (g && sc[0] === g.heat && !FIN[from]) LIVE[from] = { g: +sc[1] || 0, a: sc[2] ? 1 : 0, d: sc[3] ? 1 : 0, t: +sc[4] || 0, at: now() };
            } else if (!from && Array.isArray(d.bd)) { BOARD = d.bd; chip(); }
        }));
        offs.push(room.on('x', function (k, d, from) {
            if (k === 'final' && from && room.isHost) hostRecord(from, d);
        }));
        offs.push(room.on('fair', function (ev) {
            if (!ev) return;
            if (ev.k === 'reveal') {
                var f = FAIR[ev.round] || (FAIR[ev.round] = {});
                f.ok = ev.ok !== false; f.seed = ev.seed ? hexOf(ev.seed) : ''; f.cert = ev.cert;
                try { G.LpFair.witness(room, ev.round, f.seed); } catch (_) {}
            } else if (ev.k === 'witness') {
                var f2 = FAIR[ev.round] || (FAIR[ev.round] = {}); f2.wok = ev.ok; f2.wbad = ev.bad;
            }
        }));
        offs.push(room.on('takeover', function () { if (RUN && RUN.fin) { RUN.sent = 0; sendFinal(); } }));
        tick = setInterval(function () {
            if (!ROOM) return;
            if (RUN && RUN.st === 'play') poll();
            if (ROOM.isHost) hostTick();
            chip();
        }, 250);
        sync();
    }

    function register(spec) {
        if (!spec || typeof spec.gameId !== 'string') return;
        SPEC = spec;
        var R = G.LpRooms, UI = G.LpRoomsUI;
        if (R && R.adapter) {
            R.adapter({ gameId: spec.gameId, kind: 'race', seats: [2, 8], max: 12, lateJoin: 'nextRound', migratable: true, options: spec.options || [], race: spec });
        }
        if (UI && UI.config) {
            var cfg = { onStart: function (room) { hostStart(room); return false; } };
            if (spec.options && spec.options.length) cfg.choices = { options: spec.options };
            if (spec.labels) cfg.labels = spec.labels;
            UI.config(cfg);
        }
        if (R && R.on) {
            R.on('room', function (r) { if (r && r.gameId === spec.gameId) bind(r); });
            R.on('left', function () { if (ROOM && ROOM._left) unbind(); });
            var cur = R.current && R.current(); if (cur) bind(cur);
        }
        if (typeof spec.unlock === 'function' && !register._u) {
            register._u = true;
            D.addEventListener('pointerdown', function u() { try { spec.unlock(); } catch (_) {} D.removeEventListener('pointerdown', u, true); }, true);
        }
    }

    G.addEventListener('visibilitychange', onVis, true);
    G.addEventListener('pagehide', onHide, true);

    G.LpRoomsRace = {
        version: VER,
        register: register,
        hostStart: function (room) { return hostStart(room || ROOM); },
        active: function () { return !!(RUN && RUN.st === 'play'); },
        info: function () {
            var g = game();
            return { st: RUN ? RUN.st : null, heat: RUN ? RUN.heat : (g ? g.heat : 0), seed: RUN ? RUN.seed : null, t0: RUN ? RUN.t0 : null,
                skew: RUN ? RUN.skew : null, trueStart: RUN ? RUN.trueStart : null, g: RUN ? RUN.g : null, fin: RUN ? RUN.fin : null,
                board: BOARD, live: ROOM && ROOM.isHost ? LIVE : null, game: g, shown: SHOWN, fair: FAIR, card: !!cardEl, chip: chipEl ? chipEl.textContent : '' };
        },
        _t: { hostFinalize: hostFinalize, endRun: endRun, better: better, fmtTime: fmtTime }
    };
})(typeof window !== 'undefined' ? window : globalThis);
/* CHANGE LOG
   2026-09-30  P5 구현 — 레이스 커널: 공정 시드 · 동시 출발(방장 시계 t0) · hb 편승 순위(추가 메시지 0) ·
               final 1통 · 방장 확정(board) · 백그라운드 종료 · 늦참 다음 판 · 한 판 더(toLobby) · 결과 카드 + 공정 배지.
*/
