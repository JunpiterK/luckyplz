/* 하네스 페이지 접착제 — 게임 대신 들어가는 최소 "게임". 경로 /games/<id>/ 에서 id 를 읽어 어댑터 등록,
   모든 방 이벤트를 T.ev 에 기록, 방장이면 간단한 의도('inc'·'noop') 처리, 로드 시 resume(). */
(function () {
    'use strict';
    var T = window.T = { ev: [], room: null, nav: [], resumed: null, lag: 0, joins: {} };
    function sum(e, a) {
        try {
            switch (e) {
                case 'roster': return { n: a[0].length, pids: a[0].map(function (m) { return m.p; }), d: a[1] };
                case 'state': return { seq: a[0].seq, phase: a[0].phase, game: a[0].game };
                case 'phase': return { phase: a[0], startAt: a[1] && a[1].startAt };
                case 'fair': var f = Object.assign({}, a[0]); if (f.seed) f.seed = LpFair.hex(f.seed); delete f.cert; return f;
                case 'x': return { k: a[0], d: a[1], from: a[2] };
                case 'react': return { i: a[0], from: a[1] };
                case 'priv': return { d: a[0], e: a[1] };
                default: return a[0] === undefined ? null : JSON.parse(JSON.stringify(a[0]));
            }
        } catch (_) { return null; }
    }
    T.log = function (e, x) { T.ev.push({ t: Date.now(), e: e, x: x }); if (T.ev.length > 3000) T.ev.splice(0, 500); };
    T.count = function (e) { return T.ev.filter(function (v) { return v.e === e; }).length; };
    T.last = function (e) { for (var i = T.ev.length - 1; i >= 0; i--) if (T.ev[i].e === e) return T.ev[i].x; return null; };
    var m = /^\/games\/([a-z0-9-]+)\//.exec(location.pathname);
    T.gid = m ? m[1] : (location.pathname.indexOf('/lobby') === 0 ? 'lobby' : null);
    document.getElementById('h').textContent = 'mp harness · ' + (T.gid || '-') + ' · ' + (window.__mpLabel || '');
    if (T.gid) LpRooms.adapter(Object.assign({ gameId: T.gid, kind: 'turn', seats: [1, 8], migratable: true, lateJoin: 'anytime',
        picks: [{ key: 'char', options: ['a', 'b', 'c', 'd'], unique: true, botYield: true }] }, window.__mpAdapter || {}));
    LpRooms.config({ navigate: function (u) { T.nav.push(u); T.log('nav', u); if (!window.__mpNoNav) location.assign(u); } });
    T.bind = function (r) {
        if (T.room === r) return;
        T.room = r;
        ['roster', 'state', 'phase', 'fair', 'x', 'react', 'hostlost', 'hostback', 'takeover', 'kicked', 'closed', 'detached', 'switch', 'pending', 'priv', 'net', 'join'].forEach(function (e) {
            r.on(e, function () { T.log(e, sum(e, arguments)); if (e === 'join') T.joins[arguments[0].p] = (T.joins[arguments[0].p] || 0) + 1; });
        });
        r.onIntent(function (from, a, x) {
            if (a === 'inc') { r.setState(function (S) { S.game = S.game || {}; S.game.n = (S.game.n || 0) + ((x | 0) || 1); S.game.by = from.p; }); return; }
            if (a === 'noop') return;
            return { reject: 'unknown' };
        });
    };
    LpRooms.on('room', T.bind);
    LpRooms.on('left', function (x) { T.log('left', x); });
    /* 이벤트 루프 지연 측정(S6) */
    var last = performance.now();
    setInterval(function () { var t = performance.now(), lag = t - last - 10; if (lag > T.lag) T.lag = lag; last = t; }, 10);
    T.hash = function () { var r = T.room; if (!r || !r.state()) return null; var S = r.state(); return LpRooms.util.canon({ seq: S.seq, game: S.game, phase: S.phase, pids: S.roster.map(function (m) { return m.p + ':' + m.r + ':' + m.seat; }).sort() }); };
    if (!window.__mpNoResume) LpRooms.resume().then(function (r) { T.resumed = !!r; if (r) T.bind(r); }).catch(function (e) { T.resumed = 'err:' + (e && e.reason); });
    else T.resumed = false;
})();
