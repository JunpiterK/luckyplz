/* 코어 시나리오 C1~C14 (+ Node↔Edge 교차 D6x·D7x) — DESIGN §10.2 */
import { device, create, join, allEqual, closeAll, loadFixture } from './suites.mjs';
import * as A from './attacker.mjs';

const J = JSON.stringify;
const run1 = (only, id) => !only.length || only.includes(id);
const evCount = (p, e) => p.ev(`T.count(${J(e)})`);
async function withSetup(E, n, gid, fn, o = {}) {
    const H = await device(E, o.hl || 'H', gid);
    const G = [];
    for (let i = 0; i < n; i++) G.push(await device(E, (o.gl || 'g') + (i + 1), gid));
    try { return await fn(H, G); } finally { await closeAll(E, [H, ...G]); }
}

export async function core(ctx) {
    const { E, relay, ok, sleep, only } = ctx;
    const fx = loadFixture();

    if (run1(only, 'C1')) {
        const Ap = await device(E, 'c1a'), Bp = await device(E, 'c1b');
        try {
            await Ap.ev(`LpRooms.config({testKeys:[${J({ sig: fx.a.sig, dh: fx.a.dh })}]})`);
            const ca = await create(Ap);
            const chk = await Ap.ev(`(async()=>{const r=T.room,u=LpRooms.util,F=await u.roomF(r._rpk);return {code:u.codeOfF(F)===r.code,fp:u.fpOfF(F)===r.fp,seal:u.seal(F)===r.seal}})()`);
            const fmt = /^[23456789ABCDEFGHJKMNPQRSTVWXYZ]{6}$/.test(ca.code) && /[A-Z]/.test(ca.code);
            ok('C1a', fmt && chk.code && chk.fp && chk.seal && ca.code === fx.code, 'code format·letter·self-certifying fp', { code: ca.code, chk });
            await Bp.ev(`LpRooms.config({testKeys:[${J({ sig: fx.b.sig, dh: fx.b.dh })}]})`);
            const t0 = Date.now(); const cb = await create(Bp);
            ok('C1b', cb.code !== fx.code, 'collision check → new keys (same-code host already live)', { collidingCode: fx.code, got: cb.code, ms: Date.now() - t0 });
        } finally { await closeAll(E, [Ap, Bp]); }
    }

    if (run1(only, 'C2')) await withSetup(E, 3, 'roulette', async (H, G) => {
        const c = await create(H);
        await H.ev(`T.room.setState(S=>{S.game={n:7,names:['a','b']}})`);
        const js = []; for (const g of G) js.push(await join(g, c.url));
        const eq = await allEqual([H, ...G], `T.room&&T.room.roster().map(m=>m.p).sort().join(',')`);
        const st = await Promise.all(G.map(g => g.ev(`T.room.state().game&&T.room.state().game.n`)));
        const seals = await Promise.all(G.map(g => g.ev('T.room.seal')));
        ok('C2', js.every(j => j.ok) && eq.ok && eq.v.split(',').length === 4 && st.every(v => v === 7) && seals.every(s => s === c.seal), 'link join ×3 (fp pinned), roster·welcome state·seal emoji same', { roles: js.map(j => j.role), n: eq.ok ? 4 : eq.vals, st });
        const bad = c.url.replace(/#k=(.)/, (m, ch) => '#k=' + (ch === 'A' ? 'B' : 'A'));
        const X = await device(E, 'c2x');
        const jb = await join(X, bad);
        ok('C2b', !jb.ok && jb.reason === 'bad_fp', 'link with wrong fingerprint → bad_fp', jb);
        await closeAll(E, [X]);
    });

    if (run1(only, 'C3')) await withSetup(E, 2, 'roulette', async (H, G) => {
        await H.ev(`LpRooms.config({testKeys:[${J({ sig: fx.a.sig, dh: fx.a.dh })}]})`);
        const c = await create(H);
        const fake = await A.fakeV2Host(relay, fx.b, fx.code);
        try {
            const j1 = await join(G[0], c.code);
            ok('C3a', !j1.ok && j1.reason === 'host_conflict', 'code-only join + second valid hello (same code, other key) → abort', j1);
            const j2 = await join(G[1], c.url);
            ok('C3b', j2.ok, 'link join (128-bit fp) unaffected by fake host', j2);
        } finally { fake.stop(); }
        const j3 = await join(G[0], c.code);
        ok('C3c', j3.ok, 'code-only join (TOFU) succeeds once fake is gone', j3);
    });

    if (run1(only, 'C4')) await withSetup(E, 2, 'roulette', async (H, G) => {
        const c = await create(H); for (const g of G) await join(g, c.url);
        const before = await H.ev('T.room.canStart()');
        for (const g of G) await g.ev(`T.room.intent('ready',true)`);
        await H.wait('T.room.canStart()', 5000);
        await H.ev('T.room.start({countdownMs:600})');
        await Promise.all(G.map(g => g.wait(`T.room.state().phase==='playing'`, 6000)));
        await H.ev('T.room.end()');
        await Promise.all(G.map(g => g.wait(`T.room.state().phase==='result'`, 4000)));
        await H.ev('T.room.toLobby()');
        await Promise.all(G.map(g => g.wait(`T.room.state().phase==='lobby'&&T.room.roster().filter(m=>m.r==='player').every(m=>!m.rd)`, 4000)));
        const seq = await G[0].ev(`T.ev.filter(v=>v.e==='phase').map(v=>v.x.phase).join('>')`);
        ok('C4', before === false && /starting>playing>result>lobby/.test(seq), 'ready gate → start → playing → result → lobby (ready reset)', seq);
    });

    if (run1(only, 'C5')) await withSetup(E, 0, 'roulette', async (H) => {
        const c = await create(H);
        const g1 = await device(E, 'c5a');
        const g2 = await E.page({ label: 'c5b', ctx: g1.ctx }); await g2.go('/games/roulette/');
        try {
            const j1 = await join(g1, c.url);
            const j2 = await join(g2, c.url);
            const j3 = await join(g2, c.url, { steal: true });
            await g1.wait(`T.count('detached')===1`, 5000);
            const pid = j1.pid;
            await sleep(24000);
            const joins = await H.ev(`T.joins[${J(pid)}]||0`);
            const ros = await H.ev(`T.room.roster().filter(m=>m.p===${J(pid)}).map(m=>m.c).join(',')`);
            const g1room = await g1.ev('!!(LpRooms.current())');
            const g1after = await g1.ev(`T.ev.filter(v=>v.e==='roster'&&v.t>T.ev.find(x=>x.e==='detached').t).length`);
            ok('C5', j1.ok && !j2.ok && j2.reason === 'other_tab' && j3.ok && j3.pid === pid && joins === 1 && ros === 'on' && !g1room && g1after === 0,
                '2 tabs same device → other_tab → "continue here" → old tab detached, host onJoin 1×, no rejoin in 24s', { j2: j2.reason, joins, ros, g1room, g1after });
        } finally { await closeAll(E, [g1]); }
    });

    if (run1(only, 'C6')) await withSetup(E, 1, 'roulette', async (H, G) => {
        const c = await create(H); const j = await join(G[0], c.url);
        await H.ev('T.room.lock(true)');
        await sleep(300);
        const t0 = Date.now();
        await G[0].reload();
        await G[0].wait(`T.room&&LpRooms.current()&&T.resumed===true`, 8000);
        const dt = Date.now() - t0;
        const me = await G[0].ev('({pid:T.room.me.pid,seat:T.room.me.seat,role:T.room.me.role})');
        const X = await device(E, 'c6x'); const jx = await join(X, c.url); await closeAll(E, [X]);
        ok('C6', me.pid === j.pid && me.seat === j.seat && dt <= 3000 && !jx.ok && jx.reason === 'locked', 'guest refresh in locked room → same seat ≤3s; stranger → locked', { dt, me, jx: jx.reason });
    });

    if (run1(only, 'C7')) await withSetup(E, 2, 'roulette', async (H, G) => {
        const c = await create(H); for (const g of G) await join(g, c.url);
        await H.ev(`T.room.setState(S=>{S.game={n:5}})`); await H.ev('T.room.start({countdownMs:0})');
        await Promise.all(G.map(g => g.wait(`T.room.state().game&&T.room.state().game.n===5&&T.room.state().phase==='playing'`, 5000)));
        const ep0 = await G[0].ev('T.room.ep');
        await H.reload();
        await H.wait('T.room&&T.room.isHost&&T.resumed===true', 8000);
        const hs = await H.ev(`({n:T.room.state().game.n,phase:T.room.state().phase,ep:T.room.ep,code:T.room.code})`);
        await Promise.all(G.map(g => g.wait(`T.room.ep>${ep0}`, 6000)));
        const r = await G[1].ev(`T.room.intent('inc',1)`);
        const eq = await allEqual([H, ...G], `T.room.state().game.n+':'+T.room.state().phase`);
        const lost = await Promise.all(G.map(g => evCount(g, 'hostlost')));
        ok('C7', hs.n === 5 && hs.phase === 'playing' && hs.code === c.code && r.ok && eq.ok && eq.v === '6:playing' && lost.every(x => x === 0), 'host refresh mid-round → same state, new epoch accepted, guests continuous', { hs, r, eq: eq.v || eq.vals, lost });
    });

    if (run1(only, 'C8')) await withSetup(E, 3, 'roulette', async (H, G) => {
        const c = await create(H); for (const g of G) await join(g, c.url);
        await sleep(1500);
        const succ = await G[0].ev('T.room.state().succ');
        const t0 = Date.now();
        relay.partition('H');
        const lv = { l1: null, l2: null, tk: null };
        while (Date.now() - t0 < 50000) {
            const s = await G[1].ev(`({l1:(T.ev.find(v=>v.e==='hostlost'&&v.x.level===1)||{}).t,l2:(T.ev.find(v=>v.e==='hostlost'&&v.x.level===2)||{}).t,tk:(T.ev.find(v=>v.e==='takeover')||{}).t})`);
            if (s.l1 && !lv.l1) lv.l1 = s.l1 - t0; if (s.l2 && !lv.l2) lv.l2 = s.l2 - t0; if (s.tk && !lv.tk) lv.tk = s.tk - t0;
            if (lv.tk) break; await sleep(250);
        }
        await sleep(2500);
        const views = await Promise.all(G.map(g => g.ev(`({host:(T.room.roster().find(m=>m.r==='host')||{}).p,isHost:T.room.isHost,pids:T.room.roster().map(m=>m.p).sort().join(',')})`)));
        const sameHost = views.every(v => v.host === succ[0]) && views.filter(v => v.isHost).length === 1;
        const samePids = views.every(v => v.pids === views[0].pids) && views[0].pids.split(',').length === 4;
        const r = await G[2].ev(`T.room.intent('inc',2)`);
        const eq = await allEqual(G, `String(T.room.state().game&&T.room.state().game.n)`);
        ok('C8a', lv.l1 >= 10000 && lv.l1 <= 14500 && lv.l2 >= 18000 && lv.l2 <= 22500 && lv.tk >= 28000 && lv.tk <= 36000, 'host socket dead → 12s yellow · 20s red · ~30s takeover', lv);
        ok('C8b', sameHost && samePids && r.ok && eq.ok && eq.v === '2', 'takeover: first online succ becomes host, roster identical, game continues', { succ0: succ[0], views, r, eq: eq.v || eq.vals });
        relay.partition('H', false);
        const dem = await H.wait(`T.room&&!T.room.isHost&&T.room.state().roster.find(m=>m.p===T.room.me.pid&&m.c==='on'&&m.r!=='host')`, 20000).catch(() => null);
        const hv = await G[0].ev(`T.room.roster().map(m=>m.p+':'+m.r+':'+m.c).sort().join(',')`);
        ok('C8c', !!dem && (hv.match(/:host:/g) || []).length === 1, 'old host returns → joins as guest (no take-back)', hv);
    });

    if (run1(only, 'C9')) await withSetup(E, 2, 'roulette', async (H, G) => {
        const c = await create(H); for (const g of G) await join(g, c.url);
        await G[0].ev(`T.room.intent('pick',{key:'char',val:'b'})`);
        await sleep(300);
        const seats0 = await H.ev(`T.room.roster().map(m=>m.p+':'+m.seat).sort().join(',')`);
        const pages = [H, ...G], res = [];
        for (const gid of ['yut', 'ludo', 'roulette']) {
            await H.ev(`T.room.switchGame(${J(gid)})`);
            const st = await Promise.all(pages.map(p => p.wait(`location.pathname==='/games/${gid}/'&&window.T&&T.room&&LpRooms.current()&&T.room.state()&&T.room.state().gameId===${J(gid)}&&T.room.roster().length===3`, 20000).then(() => true).catch(e => e.message.slice(0, 160))));
            const info = await Promise.all(pages.map(p => p.ev(`({path:location.pathname,cur:!!LpRooms.current(),gid:T.room&&T.room.state()&&T.room.state().gameId,n:T.room&&T.room.roster().length,code:T.room.code,host:T.room.isHost,seats:T.room.roster().map(m=>m.p+':'+m.seat).sort().join(','),q:location.search,ev:T.ev.slice(-6).map(v=>v.e+(v.x&&v.x.reason?':'+v.x.reason:''))})`).catch(e => ({ err: e.message }))));
            if (!st.every(x => x === true)) console.log('C9 debug', gid, JSON.stringify(info), pages.map(p => p.log.slice(-5)));
            res.push({ gid, ok: st.every(x => x === true), same: info.every(i => i.code === c.code && i.seats === seats0), hostOk: info[0].host === true, st: st.filter(x => x !== true) });
        }
        const pick = await G[0].ev(`(T.room.roster().find(m=>m.p===T.room.me.pid).pick||{}).char`);
        ok('C9', res.every(r => r.ok && r.same && r.hostOk) && pick === 'b', 'switch game ×3 → all follow, same code·seats, pick remembered per game', { res, pick });
    });

    if (run1(only, 'C10')) await withSetup(E, 2, 'roulette', async (H, G) => {
        await G[0].ev(`LpRooms.profile.set({nick:'Mallory'})`);
        const c = await create(H); const jx = await join(G[0], c.url); await join(G[1], c.url);
        await H.ev(`T.room.kick(${J(jx.pid)},{ban:true})`);
        await G[0].wait(`T.count('kicked')===1&&!LpRooms.current()`, 5000);
        const r1 = await join(G[0], c.url);
        await G[0].ev(`localStorage.removeItem('lpr_ban_'+${J(c.code)});document.cookie='lpr_ban_${c.code}=; max-age=0; path=/'`);
        const r2 = await join(G[0], c.url);
        const Z = await device(E, 'c10z'); await Z.ev(`LpRooms.profile.set({nick:'Mallory'})`);
        const zp = Z.ev(`(async()=>{const x=LpRooms.parseInvite(${J(c.url)});let st=[];try{const r=await LpRooms.join({code:x.code,inv:x.inv,onStatus:s=>st.push(s.st)});T.bind(r);return {ok:true,st}}catch(e){return {ok:false,reason:e.reason,st}}})()`);
        await H.wait(`T.room.pending().length===1`, 8000);
        const pend = await H.ev(`T.room.pending()`);
        await H.ev(`T.room.approve(T.room.pending()[0].p,true)`);
        const zr = await zp;
        ok('C10', r1.reason === 'banned' && r2.reason === 'banned' && pend[0].flag === 'banned_nick' && zr.ok && zr.st.includes('pending'),
            'kick+ban → self-mark banned, pid banned; storage wiped (new pid) → approval queue (⚠ same nick) → approve', { r1: r1.reason, r2: r2.reason, pend, zr });
        await closeAll(E, [Z]);
    });

    if (run1(only, 'C11')) await withSetup(E, 0, 'roulette', async (H) => {
        const c = await create(H, { pinReq: true, pin: '4321' });
        const Ap = await device(E, 'c11a');
        const L = await device(E, 'c11l');
        try {
            const np = await join(Ap, c.code);
            const reasons = [];
            let tCool = 0;
            for (let i = 0; i < 30; i++) { const r = await join(Ap, c.code, { pin: String(1000 + i) }); reasons.push(r.reason); if (i === 9) tCool = Date.now(); }
            const good = await join(Ap, c.code, { pin: '4321' });
            const lk = await join(L, c.url);
            const nBad = reasons.filter(r => r === 'bad_proof').length, nRate = reasons.filter(r => r === 'rate').length;
            ok('C11a', np.reason === 'pin_required' && nBad === 10 && nRate === 20 && good.reason === 'rate' && lk.ok, '30 wrong PINs → 10 bad_proof then rate (even correct PIN); link token passes during cooldown', { np: np.reason, nBad, nRate, good: good.reason, link: lk.ok });
            let after = null, rejectedLate = 0;
            while (Date.now() - tCool < 80000) { await sleep(4000); after = await join(Ap, c.code, { pin: '4321' }); if (after.ok) break; rejectedLate = Date.now() - tCool; }
            const since = Date.now() - tCool;
            ok('C11b', after && after.ok && since >= 58000 && rejectedLate >= 50000, 'cooldown 60s (from 10th miss) → correct PIN admitted after it', { ok: after && after.ok, admittedAfterMs: since, lastRateAtMs: rejectedLate });
        } finally { await closeAll(E, [Ap, L]); }
    });

    if (run1(only, 'C12')) await withSetup(E, 3, 'roulette', async (H, G) => {
        const c = await create(H); for (const g of G) await join(g, c.url);
        await sleep(1000);
        relay.resetStats();
        relay.setFault({ lat: [10, 150], loss: 0.10, dup: 0.05 });
        for (let i = 0; i < 60; i++) {
            await H.ev(`T.room.setState(S=>{S.game=S.game||{n:0};S.game.n++;S.game.h=(S.game.h||'')+'x'})`);
            if (i % 10 === 5) await G[i % 3].ev(`T.room.intent('ready',${i % 20 < 10})`).catch(() => 0);
            await sleep(60);
        }
        await sleep(1500);
        relay.setFault({});
        const eq = await allEqual([H, ...G], 'T.hash()', 20000);
        const snap = relay.snapshot();
        const sreq = (snap.byEvent['g:snap_req'] || { n: 0 }).n;
        const hDrops = ['state', 'delta', 'roster', 'phase', 'fair', 'x', 'welcome', 'rekey', 'ack', 'nack', 'priv', 'kicked', 'close', 'switch'].reduce((a, k) => a + (snap.dropsByE[k] || 0), 0);
        ok('C12', eq.ok && sreq <= Math.max(1, hDrops), '10% loss + reorder + dup → final state hash equal on all, snap_req ≤ lost s-stream events', { eq: eq.ok ? 'equal' : eq.vals, snap_req: sreq, lostS: hDrops, drops: snap.drops, dup: relay.stats.dup });
    });

    if (run1(only, 'C13')) {
        const H = await device(E, 'c13h'); const pages = [H];
        try {
            const c = await create(H);
            const res = [];
            for (let i = 0; i < 12; i++) {
                const p = await device(E, 'c13g' + i); pages.push(p);
                res.push(await join(p, c.url, i === 0 ? { want: 'watch' } : {}));
            }
            const okN = res.slice(0, 11).every(r => r.ok), last = res[11];
            const n = await H.ev('T.room.roster().length');
            ok('C13', okN && res[0].role === 'spec' && !last.ok && last.reason === 'full' && n === 12, 'spectator joins as spec; 12 incl. spectators → 13th = full', { n, watcher: res[0].role, last: last.reason });
        } finally { await closeAll(E, pages); }
    }

    if (run1(only, 'C14')) await withSetup(E, 0, 'roulette', async (H) => {
        const c = await create(H);
        const X = await device(E, 'c14x');
        const v1 = A.fakeV1Host(relay, 'KQ7R4M', 'yut');
        relay.rpcMocks.qlive_state = a => a.p_code === '123456' ? { ok: true, phase: 'lobby' } : { ok: false, err: 'no_room' };
        const sz = A.fakeSzx(relay, '654321');
        try {
            const r = {};
            r.v2 = await X.ev(`LpRooms.resolve(${J(c.code)})`);
            r.v2link = await X.ev(`LpRooms.resolve(${J(c.url)})`);
            r.v1 = await X.ev(`LpRooms.resolve('KQ7-R4M')`);
            r.oldq = await X.ev(`LpRooms.resolve('https://luckyplz.com/games/yut/?room=KQ7R4M')`);
            r.quiz = await X.ev(`LpRooms.resolve('123456')`);
            r.szx = await X.ev(`LpRooms.resolve('654321')`);
            r.qlink = await X.ev(`LpRooms.resolve('https://luckyplz.com/games/quiz/?c=777777')`);
            r.none = await X.ev(`LpRooms.resolve('Z9Z9Z9')`);
            const good = r.v2.kind === 'rooms' && r.v2.url === '/games/roulette/?r=' + c.code && r.v2link.url.indexOf('#k=' + c.fp) > 0
                && r.v1.kind === 'rooms-v1' && r.v1.url === '/games/yut/?room=KQ7R4M' && r.oldq.kind === 'rooms-v1'
                && r.quiz.kind === 'qlive' && r.quiz.url === '/games/quiz/?c=123456' && r.szx.kind === 'szx' && r.szx.url === '/games/dodge/?race=654321'
                && r.qlink.kind === 'qlive' && r.none.kind === 'none';
            ok('C14', good, 'resolve: v2 code/link · v1 code · old ?room= · quiz numeric · SZX numeric · ?c= · unknown', Object.fromEntries(Object.entries(r).map(([k, v]) => [k, v.kind + ' ' + (v.url || '')])));
        } finally { v1.stop(); sz.stop(); delete relay.rpcMocks.qlive_state; await closeAll(E, [X]); }
    });

    /* 추가: delta 방송 + 숨은 정보 view/priv (P4 마작용 커널 경로) */
    if (run1(only, 'CX1')) {
        const pre = `window.__mpAdapter={delta:true,hiddenInfo:true,migratable:false,view:function(g,pid){if(!g)return {pub:g};return {pub:{n:g.n},priv:pid&&g.hands?g.hands[pid]:undefined}}};`;
        const H = await E.page({ label: 'x1H', pre }); await H.go('/games/mahjong-tw/');
        const Ga = await E.page({ label: 'x1A', pre }); await Ga.go('/games/mahjong-tw/');
        const Gb = await E.page({ label: 'x1B', pre }); await Gb.go('/games/mahjong-tw/');
        try {
            const c = await create(H, { gameId: 'mahjong-tw' });
            const lis = A.listener(relay, c.code);
            const ja = await join(Ga, c.url), jb = await join(Gb, c.url);
            relay.resetStats();
            await H.ev(`T.room.setState(S=>{S.game={n:1,hands:{${J(ja.pid)}:['SECRET_A1','SECRET_A2'],${J(jb.pid)}:['SECRET_B1']}}})`);
            for (let i = 0; i < 12; i++) { await H.ev(`T.room.setState(S=>{S.game.n++})`); await sleep(40); }
            const eq = await allEqual([Ga, Gb], 'String(T.room.state().game.n)+":"+JSON.stringify(Object.keys(T.room.state().game))');
            const pa = await Ga.ev(`JSON.stringify((T.ev.filter(v=>v.e==='priv').slice(-1)[0]||{x:{}}).x.d)`);
            const pb = await Gb.ev(`JSON.stringify((T.ev.filter(v=>v.e==='priv').slice(-1)[0]||{x:{}}).x.d)`);
            const aSeesB = await Ga.ev(`JSON.stringify(T.ev.filter(v=>v.e==='priv')).includes('SECRET_B1')`);
            const snap = relay.snapshot();
            const leak = lis.got.join(' ').includes('SECRET_');
            lis.stop();
            ok('CX1', eq.ok && eq.v === '13:["n"]' && pa === '["SECRET_A1","SECRET_A2"]' && pb === '["SECRET_B1"]' && !aSeesB && !leak && (snap.byEvent['h:delta'] || { n: 0 }).n > 0,
                'delta broadcast + view(): public state only, each seat gets its own priv hand (ECIES), no cross/listener leak', { eq: eq.v || eq.vals, pa, pb, deltas: (snap.byEvent['h:delta'] || {}).n, states: (snap.byEvent['h:state'] || {}).n, privs: (snap.byEvent['h:priv'] || {}).n });
        } finally { await closeAll(E, [H, Ga, Gb]); }
    }
    /* 추가: 방장 넘기기(대기실) + 리액션 */
    if (run1(only, 'CX2')) await withSetup(E, 2, 'roulette', async (H, G) => {
        const c = await create(H); const ja = await join(G[0], c.url); await join(G[1], c.url);
        await G[0].ev('T.room.react(2)'); await G[0].ev('T.room.react(3)');
        await sleep(800);
        const rx = await Promise.all([H, G[1]].map(p => p.ev(`T.ev.filter(v=>v.e==='react').map(v=>v.x.i+'@'+(v.x.from===${J(ja.pid)}?'A':'?')).join(',')`)));
        await H.ev(`T.room.transferHost(${J(ja.pid)})`);
        await G[0].wait('T.room.isHost', 8000);
        await H.wait(`T.room&&!T.room.isHost&&T.room.roster().find(m=>m.p===T.room.me.pid&&m.c==='on')`, 10000).catch(() => null);
        const views = await Promise.all([H, ...G].map(p => p.ev(`(T.room.roster().find(m=>m.r==='host')||{}).p+'|'+T.room.roster().length`)));
        const r = await G[1].ev(`T.room.intent('inc',4)`);
        const eq = await allEqual([H, ...G], 'String(T.room.state().game&&T.room.state().game.n)');
        ok('CX2', rx.every(x => x === '2@A') && views.every(v => v === ja.pid + '|3') && r.ok && eq.ok && eq.v === '4', 'reactions reach all (1 per 1.2s); transferHost → guest becomes host, old host rejoins as guest, game continues', { rx, views, r, eq: eq.v || eq.vals });
    });

    /* 추가: 시계 오프셋(같은 기계 → 참 오프셋 0) · 의도 멱등(응답 유실 → 재전송해도 1번만 적용) · chain·deal 브라우저 경로 */
    if (run1(only, 'CX3')) await withSetup(E, 2, 'roulette', async (H, G) => {
        const c = await create(H); for (const g of G) await join(g, c.url);
        relay.setFault({ lat: [20, 60] });
        await sleep(9000);
        const offs = await Promise.all(G.map(g => g.ev(`({off:Math.round(T.room._off),rtt:T.room._rtt,n:T.room._clk.length})`)));
        relay.setFault({});
        ok('CX3', offs.every(o => Math.abs(o.off) <= 25 && o.n >= 3), 'NTP-style clock: offset ≈ 0 (same machine, 20–60ms one-way jitter) after join samples', offs);
    });
    if (run1(only, 'CX4')) await withSetup(E, 1, 'roulette', async (H, G) => {
        const c = await create(H); await join(G[0], c.url);
        await H.ev(`T.room.setState(S=>{S.game={n:0}})`); await sleep(300);
        relay.dropIf = (topic, ev, pl, from, to) => to === 'g1' && ev === 'h' && pl && (pl.e === 'state' || pl.e === 'ack' || pl.e === 'delta' || pl.e === 'roster');
        const p = G[0].ev(`T.room.intent('inc',1)`);
        await sleep(3500);
        relay.dropIf = null;
        const r = await p;
        await sleep(600);
        const n = await allEqual([H, G[0]], 'String(T.room.state().game.n)');
        const snap = relay.snapshot();
        const intents = (snap.byEvent['g:intent'] || { n: 0 }).n;
        ok('CX4', r.ok && n.ok && n.v === '1' && intents >= 2, 'intent retried with same c after lost ack → applied once (idempotent), promise resolves ok', { r, n: n.v || n.vals, intentSends: intents });
    });
    if (run1(only, 'CX5')) await withSetup(E, 2, 'roulette', async (H, G) => {
        const c = await create(H); for (const g of G) await join(g, c.url);
        const s0 = await H.ev(`LpFair.chain.create(T.room,20).then(r=>r.s0)`);
        const s5 = await H.ev(`LpFair.chain.reveal(5)`);
        const hv = await H.ev(`LpFair.chain.event(5,'ab').then(v=>LpFair.hex(v))`);
        await Promise.all(G.map(g => g.wait(`T.ev.find(v=>v.e==='fair'&&v.x.k==='chain0')`, 5000)));
        const gv = await Promise.all(G.map(g => g.ev(`(()=>{const e=T.ev.find(v=>v.e==='fair'&&v.x.k==='chain0').x;return {s0:e.s0===${J(s0)},ok:LpFair.chain.verify(e.s0,${J(s5)},5),bad:LpFair.chain.verify(e.s0,${J(s5)},4),val:LpFair.hex(LpFair.chain.value(${J(s5)},'ab'))}})()`)));
        const d = await H.ev(`LpFair.deal.begin(T.room).then(r=>({G:r.G,seed:LpFair.hex(r.seed),round:r.round}))`);
        await Promise.all(G.map(g => g.wait(`T.ev.find(v=>v.e==='fair'&&v.x.k==='deal'&&v.x.round===${d.round})`, 6000)));
        const gG = await Promise.all(G.map(g => g.ev(`T.ev.find(v=>v.e==='fair'&&v.x.k==='deal'&&v.x.round===${d.round}).x`)));
        await H.ev('LpFair.deal.reveal(T.room)');
        await Promise.all(G.map(g => g.wait(`T.ev.find(v=>v.e==='fair'&&v.x.k==='dealR')`, 6000)));
        const gR = await Promise.all(G.map(g => g.ev(`T.ev.find(v=>v.e==='fair'&&v.x.k==='dealR').x`)));
        ok('CX5', gv.every(v => v.s0 && v.ok && !v.bad && v.val === hv) && gG.every(x => x.G === d.G && x.ok) && gR.every(x => x.ok && x.seed === d.seed),
            'chain: s0 published, s_i verifies, event value reproducible · deal: G shared, host seed hidden until dealR, then verified', { chain: gv, deal: { G: d.G.slice(0, 10), okG: gG.map(x => x.ok), rev: gR.map(x => x.ok && x.seed === d.seed) } });
    });

    /* Node ↔ Edge 교차 (D6·D7 교차 컨텍스트) */
    if (run1(only, 'FX')) {
        const { makeCert, loadFair } = await import('./fairlib.mjs');
        const Fn = loadFair();
        const X = await device(E, 'fx');
        try {
            const cert = await makeCert(4);
            const enc = await Fn.cert.encode(cert);
            const v = await X.ev(`(async()=>{const c=await LpFair.cert.decode(${J(enc)});const r=await LpFair.cert.verify(c,(p,rng)=>{const i=rng.int(p.names.length);return {idx:i,name:p.names[i]}});return {ok:r.ok,why:r.why,res:r.res}})()`);
            ok('D6x', v.ok && v.res.name === cert.res.name, 'Node-made #cert verifies in Edge, same replay result', v);
            const dNode = (() => { const h = []; for (let i = 0; i < 20000; i++) { const r = Fn.rng(Fn.H('x|' + i), 'main'); h.push(r.u32(), r.int(37)); } return Fn.hex(Fn.H(h.join(','))); })();
            const dEdge = await X.ev(`(()=>{const h=[];for(let i=0;i<20000;i++){const r=LpFair.rng(LpFair.H('x|'+i),'main');h.push(r.u32(),r.int(37))}return LpFair.hex(LpFair.H(h.join(',')))})()`);
            ok('D7x', dNode === dEdge, 'same seeds → identical outputs Node ↔ Edge (20k draws)', dNode.slice(0, 16) + ' vs ' + dEdge.slice(0, 16));
        } finally { await closeAll(E, [X]); }
    }
}
