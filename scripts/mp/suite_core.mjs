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

    /* C5b·C5c·C5d (2026-09-30): Web Locks 없는 브라우저 폴백 — BroadcastChannel, 그것도 없으면 storage 이벤트.
       C5 와 같은 결과(other_tab → "여기서 계속" → 옛 탭 분리, 방장 onJoin 1회)여야 한다.
       C5d: 옛 탭이 얼어 있어(백그라운드) 'q' 에 답을 못 한 사이 새 탭이 자리를 잡음 → 옛 탭이 깨어나면 조용히 분리 */
    const NOLOCK = `try{Object.defineProperty(Navigator.prototype,'locks',{get:function(){return undefined},configurable:true})}catch(e){}`;
    const NOBC = `try{window.BroadcastChannel=undefined}catch(e){}`;
    for (const [id, pre, mode] of [['C5b', NOLOCK, 'bc'], ['C5c', NOLOCK + NOBC, 'ls']]) {
        if (!run1(only, id)) continue;
        await withSetup(E, 0, 'roulette', async (H) => {
            const c = await create(H);
            const g1 = await E.page({ label: id + 'a', pre }); await g1.go('/games/roulette/');
            const g2 = await E.page({ label: id + 'b', ctx: g1.ctx, pre }); await g2.go('/games/roulette/');
            try {
                const lm = await g1.ev('LpRooms._t.lockMode()');
                const t0 = Date.now(); const j1 = await join(g1, c.url); const ms1 = Date.now() - t0;
                const j2 = await join(g2, c.url);
                const j3 = await join(g2, c.url, { steal: true });
                const det = await g1.wait(`T.count('detached')===1`, 5000).then(() => true).catch(() => false);
                await sleep(9000);
                const joins = await H.ev(`T.joins[${J(j1.pid)}]||0`);
                const ros = await H.ev(`T.room.roster().filter(m=>m.p===${J(j1.pid)}).map(m=>m.c).join(',')`);
                const g1room = await g1.ev('!!(LpRooms.current())');
                const g2ok = await g2.ev(`T.room.intent('inc',1).then(r=>r.ok)`);
                /* 분리된 탭이 다시 "여기서 계속" → 이번엔 g2 가 분리 */
                const j4 = await join(g1, c.url);
                const j5 = await join(g1, c.url, { steal: true });
                const det2 = await g2.wait(`T.count('detached')===1`, 5000).then(() => true).catch(() => false);
                ok(id, lm === mode && j1.ok && !j2.ok && j2.reason === 'other_tab' && j3.ok && j3.pid === j1.pid && det && joins === 1 && ros === 'on' && !g1room && g2ok && j4.reason === 'other_tab' && j5.ok && det2,
                    `no Web Locks → ${mode === 'bc' ? 'BroadcastChannel' : 'storage-event'} fallback: 2nd tab = other_tab, "continue here" detaches the old tab (both directions), host onJoin 1×`,
                    { lockMode: lm, joinMs: ms1, j2: j2.reason, j3: j3.ok, detached: det, joins, ros, g2intent: g2ok, j4: j4.reason, j5: j5.ok, detached2: det2 });
            } finally { await closeAll(E, [g1]); }
        });
    }
    if (run1(only, 'C5d')) await withSetup(E, 0, 'roulette', async (H) => {
        const c = await create(H);
        const pre = NOLOCK;
        const g1 = await E.page({ label: 'c5da', pre }); await g1.go('/games/roulette/');
        const g2 = await E.page({ label: 'c5db', ctx: g1.ctx, pre }); await g2.go('/games/roulette/');
        try {
            const j1 = await join(g1, c.url);
            /* 얼림 흉내: 디버거로 JS 를 세운다(헤드리스에선 lifecycle 'frozen' 이 메시지 처리를 막지 않는다) */
            await g1.c.send('Debugger.enable'); await g1.c.send('Debugger.pause');
            await sleep(300);
            const j2 = await join(g2, c.url);                     /* 얼어 있는 탭은 답을 못 한다 → 새 탭이 자리를 잡는다 */
            await sleep(500);
            await g1.c.send('Debugger.resume').catch(() => {}); await g1.c.send('Debugger.disable').catch(() => {});
            await sleep(200);
            /* 사용자가 옛 탭으로 돌아옴(같은 컨텍스트의 뒤 탭은 헤드리스에서 hidden 이라 visible 로 덮어쓴다) */
            await g1.ev(`(function(){try{Object.defineProperty(document,'visibilityState',{configurable:true,get:function(){return 'visible'}})}catch(e){}document.dispatchEvent(new Event('visibilitychange'));return 1})()`);
            const det = await g1.wait(`T.count('detached')===1`, 5000).then(() => true).catch(() => false);
            const g2room = await g2.ev('!!LpRooms.current()&&T.count("detached")===0');
            const joins = await H.ev(`T.joins[${J(j1.pid)}]||0`);
            ok('C5d', j1.ok && j2.ok && j2.pid === j1.pid && det && g2room && joins === 1, 'fallback lock: old tab frozen in background → new tab takes the seat; old tab wakes → detaches itself (newest tab wins), 1 seat', { j2: j2.ok ? true : j2.reason, oldDetached: det, newStays: g2room, joins });
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

    /* C8w·C8w2 (2026-10-01, 요트 에이전트 보고 회귀): 게스트(승계 1순위)가 30초 넘게 멈췄다(폰 백그라운드) 깨어나면
       방장 신호를 받기도 전에 워치독이 12·20·30초를 한 번에 넘기고, 자기만 '살아 있음'으로 쳐서 혼자 승계 → 멀쩡한 방장을 밀어냈다.
       C8w = 3대, 소켓은 살아 있음(멈춘 사이 메시지는 릴레이가 버림) · C8w2 = 2대, 깨어날 때 소켓이 끊겨 다시 붙음(폰 실제 상황) */
    for (const [id, n, kill] of [['C8w', 2, false], ['C8w2', 1, true]]) {
        if (!run1(only, id)) continue;
        await withSetup(E, n, 'roulette', async (H, G) => {
            const c = await create(H); for (const g of G) await join(g, c.url);
            await sleep(1500);
            const succ = await G[0].ev('T.room.state().succ');
            const me = await G[0].ev('T.room.me.pid');
            const lab = G[0].label;
            await G[0].c.send('Debugger.enable'); await G[0].c.send('Debugger.pause');
            relay.partition(lab);
            await sleep(36000);
            relay.partition(lab, false);
            if (kill) relay.kill(lab);
            await G[0].c.send('Debugger.resume').catch(() => {}); await G[0].c.send('Debugger.disable').catch(() => {});
            await G[0].ev(`(document.dispatchEvent(new Event('visibilitychange')),1)`).catch(() => 0);
            await sleep(15000);
            const all = [H, ...G];
            const v = await Promise.all(all.map(p => p.ev(`({host:T.room&&T.room.isHost,cur:!!LpRooms.current(),tk:T.count('takeover'),dem:T.count('demoted'),hostP:(T.room.roster().find(m=>m.r==='host')||{}).p,ep:T.room.ep})`).catch(e => ({ err: e.message.slice(0, 120) }))));
            const hostPid = await H.ev('T.room.me.pid');
            const back = await H.ev(`(T.room.roster().find(m=>m.p===${J(me)})||{}).c`);
            const r = await G[0].ev(`T.room.intent('inc',1)`).catch(e => ({ ok: false, reason: e.message.slice(0, 80) }));
            const eq = await allEqual(all, `String(T.room.state().game&&T.room.state().game.n)`, 8000);
            ok(id, succ[0] === me && v[0].host === true && v.every(x => x.cur && x.tk === 0 && x.hostP === hostPid) && !v[1].host && back === 'on' && r.ok && eq.ok && eq.v === '1',
                `guest (first successor) frozen 36s ${kill ? '+ socket dropped on wake, ' : ''}(${n + 1} devices) wakes up → waits for the host, no takeover, original host keeps the room, guest back in its seat`,
                { views: v.map(x => Object.assign({}, x, { hostP: x.hostP === hostPid ? 'H' : x.hostP })), back, intent: r, n: eq.v || eq.vals });
        });
    }

    /* C8r (2026-10-01): 마지막 안전망 — 그래도 누가 멀쩡한 방장을 두고 승계를 선언하면(예: 다른 원인으로 감시가 오판)
       원방장은 강등을 거부하고 서명된 refuse 를 보내며, 승계자는 원방장으로 되돌아가 게스트로 다시 들어온다 */
    if (run1(only, 'C8r')) await withSetup(E, 2, 'roulette', async (H, G) => {
        const c = await create(H); for (const g of G) await join(g, c.url);
        await sleep(1500);
        await H.ev(`T.room.setState(S=>{S.game={n:5}})`); await sleep(600);
        const hostPid = await H.ev('T.room.me.pid');
        const forced = await G[0].ev(`(T.room._becomeHost({}),1)`);
        await sleep(5000);
        const v = await Promise.all([H, ...G].map(p => p.ev(`({host:T.room.isHost,hostP:(T.room.roster().find(m=>m.r==='host')||{}).p,tk:T.ev.filter(x=>x.e==='takeover').map(x=>x.x&&x.x.revert?'revert':'take').join(','),cur:!!LpRooms.current()})`)));
        const r = await G[1].ev(`T.room.intent('inc',1)`);
        const r0 = await G[0].ev(`T.room.intent('inc',1)`);
        const eq = await allEqual([H, ...G], `String(T.room.state().game&&T.room.state().game.n)`, 8000);
        const roles = await H.ev(`T.room.roster().map(m=>m.r+':'+m.c).sort().join(',')`);
        ok('C8r', forced && v[0].host && v.every(x => x.cur && x.hostP === hostPid) && !v[1].host && !v[2].host && v[1].tk === 'take,revert' && v[0].tk === '' && v[2].tk === '' && r.ok && r0.ok && eq.ok && eq.v === '7' && roles === 'host:on,player:on,player:on',
            'forced takeover while the host is healthy → host refuses (signed), taker yields back to guest, room & game intact', { views: v.map(x => Object.assign({}, x, { hostP: x.hostP === hostPid ? 'H' : x.hostP })), intents: [r.ok, r0.ok], n: eq.v || eq.vals, roles });
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
            /* C14b (2026-10-01): 같은 레거시 코드를 쉬지 않고 연달아·동시에 resolve — 예전엔 앞 탐색의 채널이 닫히는 중이라
               두 번째부터 'none'(4초 뒤)이 나왔다(C14 가 가끔 떨어지던 원인 = 실제 버그). SZX 숫자 코드도 같은 경로 */
            const t0 = Date.now();
            const seq = await X.ev(`(async()=>{const o=[];for(let i=0;i<4;i++)o.push((await LpRooms.resolve('KQ7R4M')).kind);return o.join(',')})()`, 40000);
            const par = await X.ev(`Promise.all([LpRooms.resolve('KQ7-R4M'),LpRooms.resolve('https://luckyplz.com/games/yut/?room=KQ7R4M'),LpRooms.resolve('kq7r4m')]).then(a=>a.map(x=>x.kind+':'+x.url).join(','))`, 40000);
            const szx = await X.ev(`(async()=>{const o=[];for(let i=0;i<3;i++)o.push((await LpRooms.resolve('654321')).kind);return o.join(',')})()`, 40000);
            ok('C14b', seq === 'rooms-v1,rooms-v1,rooms-v1,rooms-v1' && par === Array(3).fill('rooms-v1:/games/yut/?room=KQ7R4M').join(',') && szx === 'szx,szx,szx',
                'resolve the same legacy code back-to-back / concurrently (v1 ×4, ×3 parallel, SZX ×3) → always found (per-topic serialized probe)', { seq, par, szx, ms: Date.now() - t0 });
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

    /* D4 (2026-09-30 통합): 게스트가 커밋 후 공개 안 함 → 그 라운드 취소, 재시도는 그 사람 없이 완료, 인증서 X 에 제외 기록.
       (수정 전: 재시도 때 그 사람이 다시 커밋해 L 에 들어가고 missing 이 exclude 로 안 걸러져 3회 모두 취소 → "aborted 3 times") */
    if (run1(only, 'D4')) await withSetup(E, 3, 'roulette', async (H, G) => {
        const c = await create(H); for (const g of G) await join(g, c.url);
        await sleep(600);
        const bad = await G[0].ev(`(()=>{const r=T.room;r.__gs=r._gsend;r._gsend=function(e,d){if(e==='fair'&&d&&d.k==='r')return Promise.resolve(null);return r.__gs.apply(this,arguments)};return r.me.pid})()`);
        const t0 = Date.now();
        const d = await H.ev(`LpFair.draw(T.room,{params:{names:['a','b','c','d']}}).then(r=>({ok:true,round:r.round,seed:LpFair.hex(r.seed),X:r.cert.X||null,L:r.cert.L,stats:r.cert.stats})).catch(e=>({ok:false,err:String(e&&e.message)}))`, 30000);
        const ms = Date.now() - t0;
        if (!d.ok) { ok('D4', false, 'guest commits but never reveals → retry completes without them', d); return; }
        await Promise.all(G.map(g => g.wait(`T.seeds[${d.round}]`, 8000).catch(() => null)));
        const seeds = await Promise.all(G.map(g => g.ev(`T.seeds[${d.round}]||null`)));
        const aborts = await Promise.all(G.map(g => g.ev(`T.ev.filter(v=>v.e==='fair'&&v.x.k==='abort'&&v.x.by==='guest').map(v=>(v.x.who||[]).join(','))`)));
        const excl = await G[0].ev(`T.ev.filter(v=>v.e==='fair'&&v.x.k==='commit'&&v.x.round===${d.round}).map(v=>!!v.x.excluded)`);
        const v = await G[1].ev(`LpFair.cert.verify(T.certs[${d.round}],null).then(x=>({ok:x.ok,why:x.why||null,X:T.certs[${d.round}].X||null}))`);
        const vHost = await G[1].ev(`(async()=>{const c=JSON.parse(JSON.stringify(T.certs[${d.round}]));delete c.X;const a=await LpFair.cert.verify(c,null);const c2=JSON.parse(JSON.stringify(T.certs[${d.round}]));c2.X=[];const b=await LpFair.cert.verify(c2,null);return [a.ok,a.why,b.ok]})()`);
        const good = d.round === 2 && d.X && d.X.length === 1 && d.X[0] === bad && !d.L.includes(bad) && d.L.length === 2 && d.stats.aborts >= 1
            && seeds.every(s => s === d.seed) && aborts.every(a => a.length === 1 && a[0] === bad) && excl[0] === true && v.ok && J(v.X) === J([bad])
            && vHost[0] === false && vHost[1] === 'host_sig' && vHost[2] === false;
        ok('D4', good, 'guest commits but never reveals → round aborted, retry (round 2) completes without them; cert.X records exclusion (signed: dropping X → host_sig)',
            { round: d.round, ms, L: d.L.length, X: d.X && d.X.map(p => p === bad ? 'bad' : p), aborts: d.stats.aborts, seedsEqual: seeds.every(s => s === d.seed), excludedSawCommit: excl, verify: v.ok, forgedNoX: vHost });
        /* 다음 draw() 는 새로 시작 — 그 사람을 다시 부른다(여전히 미공개면 또 한 번 취소 후 제외) */
        await G[0].ev(`(()=>{const r=T.room;r._gsend=r.__gs})()`);
        const d2 = await H.ev(`LpFair.draw(T.room,{params:{names:['a','b']}}).then(r=>({round:r.round,L:r.cert.L.length,X:r.cert.X||null}))`, 30000);
        ok('D4b', d2.L === 3 && !d2.X, 'next draw() includes the guest again once they reveal (no sticky exclusion, no X in cert)', d2);
    });

    /* 시계 정밀도 (2026-09-30 통합): 지연 30~150ms 무작위(D2 조건) — 합류 표본 + 추첨 에코 표본(lock/reveal) → 오프셋 ≈ 0 */
    if (run1(only, 'CX3b')) await withSetup(E, 3, 'roulette', async (H, G) => {
        relay.setFault({ lat: [30, 150] });
        try {
            const c = await create(H); for (const g of G) await join(g, c.url);
            await sleep(3500);
            const pre = await Promise.all(G.map(g => g.ev(`({off:Math.round(T.room._off),n:T.room._clk.length})`)));
            for (let i = 0; i < 8; i++) { await H.ev(`LpFair.draw(T.room,{params:{names:['a','b']}}).then(()=>1)`, 30000); await sleep(250); }
            const offs = await Promise.all(G.map(g => g.ev(`({off:Math.round(T.room._off*10)/10,rtt:T.room._rtt,n:T.room._clk.length,N:T.room._clkN})`)));
            const spread = Math.max(...offs.map(o => o.off)) - Math.min(...offs.map(o => o.off));
            ok('CX3b', offs.every(o => Math.abs(o.off) <= 20 && o.N >= 15) && spread <= 25, 'clock under 30–150ms jitter: join + draw-echo samples (2/draw, 0 extra msgs) → |offset| ≤ 20ms, spread ≤ 25ms', { afterJoin: pre, after8draws: offs, spread });
        } finally { relay.setFault({}); }
    });

    /* 방장 도구 공개 API (2026-09-30 통합): setPin / setApproval — UI 가 room._H 를 만지지 않는다 */
    if (run1(only, 'CX6')) await withSetup(E, 3, 'roulette', async (H, G) => {
        const c = await create(H);
        const pin = await H.ev(`T.room.setPin(true)`);
        const pinReq = await H.ev(`T.room.state().pinReq&&T.room.pin===${JSON.stringify(pin)}`);
        const j0 = await join(G[0], c.code);
        const j1 = await join(G[0], c.code, { pin });
        const keep = await H.ev(`T.room.setPin(true)`);
        const own = await H.ev(`T.room.setPin(true,'4321')`);
        const off = await H.ev(`T.room.setPin(false)===null&&!T.room.state().pinReq&&T.room.pin===undefined`);
        const j2 = await join(G[1], c.code);
        const ap = await H.ev(`T.room.setApproval(true)===true&&T.room.state().appr===true`);
        const j3 = await Promise.race([join(G[2], c.code), new Promise(r => setTimeout(() => r({ pendingStill: true }), 2500))]);
        const pend = await H.ev(`T.room.pending().length`);
        ok('CX6', /^\d{4}$/.test(pin) && pinReq && j0.reason === 'pin_required' && j1.ok && keep === pin && own === '4321' && off && j2.ok && ap && j3.pendingStill && pend === 1,
            'setPin(on,pin?) / setApproval(on): PIN on → code-only join needs PIN, keeps PIN on re-enable, custom PIN, off → open; approval on → new joiner waits', { pin: !!pin, j0: j0.reason, j1: j1.ok, keep: keep === pin, own, off, j2: j2.ok, ap, pend });
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
