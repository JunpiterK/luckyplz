/* 스푸핑 시나리오 S1~S8 — 원시 클라이언트(Node 공격자)가 채널에 직접 방송 (DESIGN §10.2) */
import { device, create, join, allEqual, closeAll } from './suites.mjs';
import * as A from './attacker.mjs';

const J = JSON.stringify;
const run1 = (only, id) => !only.length || only.includes(id);

export async function spoof(ctx) {
    const { E, relay, ok, sleep, only } = ctx;
    const H = await device(E, 'sH'), Ga = await device(E, 'sA'), Gb = await device(E, 'sB'), Gc = await device(E, 'sC');
    const pages = [H, Ga, Gb, Gc], G = [Ga, Gb, Gc];
    const nick = ['Alice7', 'Bobby7', 'Carol7'];
    for (let i = 0; i < 3; i++) await G[i].ev(`LpRooms.profile.set({nick:${J(nick[i])}})`);
    await H.ev(`LpRooms.profile.set({nick:'Hosty7'})`);
    try {
        const c = await create(H);
        const code = c.code, topic = 'lpr-' + code;
        const lis = A.listener(relay, code), rec = A.recorder(relay, code);
        const js = []; for (const g of G) js.push(await join(g, c.url));
        const [pa, pb, pc] = js.map(j => j.pid);
        await H.ev(`T.room.setState(S=>{S.game={n:1}})`);
        await sleep(500);
        const ep = await Ga.ev('T.room.ep');
        const evil = await A.newSigKey();
        const stateN = () => Promise.all(pages.map(p => p.ev('T.room.state().game.n')));
        const badOf = () => Promise.all(pages.map(p => p.ev('LpRooms.stats().bad')));

        if (run1(only, 'S1')) {
            const bad0 = await badOf();
            const big = 99999;
            const forged = [
                await A.hEnv({ code, e: 'kicked', ep, s: big, to: pa, d: { ban: true } }),
                await A.hEnv({ code, e: 'kicked', ep, s: big + 1, to: pa, d: { ban: true }, priv: evil.priv }),
                await A.hEnv({ code, e: 'close', ep, s: big + 2, d: {} }),
                await A.hEnv({ code, e: 'close', ep: ep + 1, s: 1, d: {}, priv: evil.priv }),
                await A.hEnv({ code, e: 'switch', ep, s: big + 3, d: { gameId: 'yut' }, priv: evil.priv }),
                await A.hEnv({ code, e: 'state', ep: ep + 5, s: 1, d: { v: 2, seq: 999, phase: 'result', gameId: 'roulette', roster: [], succ: [], game: { n: 666 } }, priv: evil.priv }),
                await A.hEnv({ code, e: 'hb', ep, tt: big, d: { t: Date.now(), hs: big } })
            ];
            for (const f of forged) relay.inject(topic, 'h', f);
            await sleep(1500);
            const st = await Promise.all(G.map(g => g.ev(`({mem:!!LpRooms.current(),k:T.count('kicked'),cl:T.count('closed'),nav:T.nav.length,sw:T.count('switch'),n:T.room.state().game.n,ph:T.room.state().phase})`)));
            const bad1 = await badOf();
            ok('S1', st.every(s => s.mem && !s.k && !s.cl && !s.nav && !s.sw && s.n === 1 && s.ph === 'lobby') && bad1.slice(1).every((b, i) => b > bad0[i + 1]),
                'unsigned / wrong-signed h:kicked·close·switch·state → ignored by all', { st, bad: bad1.map((b, i) => b - bad0[i]) });
        }

        if (run1(only, 'S2')) {
            await H.ev(`T.room.kick(${J(pc)})`);
            await Gc.wait(`T.count('kicked')===1&&!LpRooms.current()`, 5000);
            const kickedEnv = rec.h.filter(e => e.e === 'kicked').slice(-1)[0];
            const rj = await join(Gc, c.url);
            await sleep(400);
            relay.inject(topic, 'h', kickedEnv);
            await sleep(1200);
            const s1 = await Gc.ev(`({mem:!!LpRooms.current(),k:T.count('kicked')})`);
            await H.reload(); await H.wait('T.room&&T.room.isHost', 8000);
            await Gc.wait(`T.room.ep>${ep}`, 6000);
            relay.inject(topic, 'h', kickedEnv);
            await sleep(1200);
            const s2 = await Gc.ev(`({mem:!!LpRooms.current(),k:T.count('kicked')})`);
            ok('S2', !!kickedEnv && rj.ok && s1.mem && s1.k === 1 && s2.mem && s2.k === 1, 'recorded genuine h:kicked replayed (same epoch, then after host refresh) → ignored', { rejoined: rj.ok, s1, s2 });
        }

        if (run1(only, 'S3')) {
            const n0 = (await stateN())[0];
            /* 참가자 B 가 자기 기기 키로 서명하되 p 를 A 로 — 방장은 A 의 키로 검증 → 실패 */
            const r = await Gb.ev(`(async()=>{const r=T.room,c=Date.now()*1000,j=JSON.stringify({a:'inc',x:50});
                const str=['lpr2','g',r.code,${J(pa)},c,'intent',j].join('|');
                const sig=new Uint8Array(await crypto.subtle.sign({name:'ECDSA',hash:'SHA-256'},r._dev.sig.priv,new TextEncoder().encode(str)));
                const env={v:2,e:'intent',p:${J(pa)},c,j,z:LpRooms.util.b64u(sig)};r._rawSend('g',env);return true})()`);
            /* 외부 공격자(무서명)도 A 행세 */
            relay.inject(topic, 'g', await A.gEnv({ code, e: 'intent', p: pa, c: Date.now() * 1000 + 5, d: { a: 'inc', x: 70 } }));
            relay.inject(topic, 'g', await A.gEnv({ code, e: 'intent', p: pa, c: Date.now() * 1000 + 6, d: { a: 'inc', x: 70 }, priv: evil.priv }));
            await sleep(1500);
            const n1 = await stateN();
            const legit = await Ga.ev(`T.room.intent('inc',1)`);
            const n2 = await allEqual(pages, 'T.room.state().game.n+":"+T.room.state().game.by');
            ok('S3', r && n1.every(v => v === n0) && legit.ok && n2.ok && n2.v === (n0 + 1) + ':' + pa, "guest intent with someone else's pid (member-signed & outsider) → rejected; real A intent works", { n0, n1, n2: n2.v || n2.vals });
        }

        if (run1(only, 'S4')) {
            relay.inject(topic, 'g', await A.gEnv({ code, e: 'bye', p: pa, c: Date.now() * 1000 + 9, d: {} }));
            await Gb.ev(`(async()=>{const r=T.room,c=Date.now()*1000+11,j='{}';const str=['lpr2','g',r.code,${J(pa)},c,'bye',j].join('|');
                const sig=new Uint8Array(await crypto.subtle.sign({name:'ECDSA',hash:'SHA-256'},r._dev.sig.priv,new TextEncoder().encode(str)));r._rawSend('g',{v:2,e:'bye',p:${J(pa)},c,j,z:LpRooms.util.b64u(sig)})})()`);
            await sleep(3000);
            const cA = await H.ev(`T.room.roster().find(m=>m.p===${J(pa)}).c`);
            ok('S4', cA === 'on', "forged bye/leave for A (outsider + member-signed) → A stays online", cA);
        }

        if (run1(only, 'S5')) {
            const nav0 = await Promise.all(G.map(g => g.ev('T.nav.length')));
            await H.ev(`T.room._hsend('switch',{gameId:'evil',url:'https://evil.example/x'},{reliable:true})`);
            await H.ev(`T.room._hsend('switch',{gameId:'../../lobby',url:'javascript:alert(1)'},{reliable:true})`);
            await H.ev(`T.room._hsend('switch',{url:'/games/yut/'},{reliable:true})`);
            await sleep(1800);
            const st = await Promise.all(G.map(g => g.ev(`({nav:T.nav.length,sw:T.count('switch'),path:location.pathname,mem:!!LpRooms.current()})`)));
            ok('S5', st.every((s, i) => s.nav === nav0[i] && s.sw === 0 && s.path === '/games/roulette/' && s.mem), 'genuine host-signed switch with unregistered gameId / url field → no navigation', st);
        }

        if (run1(only, 'S6')) {
            await H.ev('T.lag=0');
            const bad0 = (await badOf())[0];
            /* 미리 만들어 둔 600통을 초당 200통으로 (서명 비용이 송신 속도를 늦추지 않게) */
            const junk = [];
            for (let i = 0; i < 600; i++) {
                const k = i % 6;
                if (k === 0) junk.push(['g', { v: 2, e: 'intent', p: 'p' + 'a'.repeat(20), c: i, j: '{"a":"inc"}', z: 'x' }]);
                else if (k === 1) junk.push(['g', await A.gEnv({ code, e: 'hb', p: pa, c: 1e15 + i, d: { t0: 1 } })]);
                else if (k === 2) junk.push(['g', { v: 2, e: 'intent', p: pb, c: 1e15 + i, j: 'x'.repeat(40000), z: 'y' }]);
                else if (k === 3) junk.push(['g', { v: 2, e: 'join', p: pb, c: i, j: '{broken', z: 'z' }]);
                else if (k === 4) junk.push(['h', { v: 2, e: 'state', ep, s: 1e9 + i, j: '{"v":2}', z: 'q' }]);
                else junk.push(['g', 'not-an-object-' + i]);
            }
            const legitP = (async () => { await sleep(1000); return Ga.ev(`T.room.intent('inc',3)`); })();
            const t0 = Date.now(); let sent = 0;
            while (sent < junk.length) {
                const due = Math.floor((Date.now() - t0) / 5);
                while (sent < junk.length && sent <= due) { relay.inject(topic, junk[sent][0], junk[sent][1]); sent++; }
                await sleep(4);
            }
            const secs = (Date.now() - t0) / 1000;
            const legit = await legitP;
            await sleep(500);
            const lag = await H.ev('T.lag'), bad1 = (await badOf())[0];
            const n = await allEqual(pages, 'String(T.room.state().game.n)');
            ok('S6', legit.ok && lag < 50 && bad1 > bad0 && n.ok && sent / secs >= 190, `flood ${sent} junk msgs in ${secs.toFixed(1)}s (${Math.round(sent / secs)}/s: bad sig, 40KB, broken JSON, junk) → dropped, host responsive`, { legit, hostMaxLagMs: Math.round(lag), droppedBad: bad1 - bad0 });
        }

        /* S6b (2026-09-30 실전 보강): 한 게스트(A)의 pid 를 적은 위조 봉투 폭주 — 모양은 맞고(서명 86자) 서명만 틀리다.
           수정 전: 방장이 서명 검증 전에 A 의 처리량 버킷을 깎아서 A 의 진짜 의도가 버려졌다(재전송 1.5초 뒤에야 통과하거나 실패).
           수정 후: 검증 뒤에만 차감 → A 의 의도 5개가 전부 재전송 없이(< 1초) 수락, 방장 rate 드롭 0, 메인 스레드 블록 < 50ms.
           + 녹화한 A 의 진짜 봉투 재생 폭주도 같은 결과(재생은 검증 없이 버림, 차감 없음). */
        if (run1(only, 'S6b')) {
            await H.ev('T.lag=0');
            const st0 = await H.ev('LpRooms.stats()');
            const n0 = (await stateN())[0];
            const genuine = rec.g.filter(e => e && e.p === pa && e.c < 1e14).slice(-40);   /* A 가 실제로 보낸 서명 봉투(재생용) */
            const junk = [];
            for (let i = 0; i < 800; i++) {
                if (i % 4 === 3 && genuine.length) junk.push(genuine[i % genuine.length]);
                else junk.push(await A.gEnv({ code, e: i % 2 ? 'intent' : 'hb', p: pa, c: 2e15 + i, d: i % 2 ? { a: 'inc', x: 100 } : { t0: 1 } }));
            }
            const lat = [];
            const legitP = (async () => {
                await sleep(500);
                for (let k = 0; k < 5; k++) { lat.push(await Ga.ev(`(async()=>{const t=performance.now();const r=await T.room.intent('inc',1);return {ok:r.ok,ms:Math.round(performance.now()-t)}})()`)); await sleep(350); }
            })();
            const t0 = Date.now(); let sent = 0;
            while (sent < junk.length) {
                const due = Math.floor((Date.now() - t0) / 5);
                while (sent < junk.length && sent <= due) { relay.inject(topic, 'g', junk[sent]); sent++; }
                await sleep(4);
            }
            const secs = (Date.now() - t0) / 1000;
            await legitP; await sleep(400);
            const lag = await H.ev('T.lag'), st1 = await H.ev('LpRooms.stats()');
            const n = await allEqual(pages, 'String(T.room.state().game.n)');
            const worst = Math.max(...lat.map(x => x.ms));
            ok('S6b', lat.length === 5 && lat.every(x => x.ok) && worst < 1000 && n.ok && +n.v === n0 + 5 && lag < 50 && st1.rate === st0.rate && sent / secs >= 190,
                `targeted flood: ${sent} forged/replayed envelopes claiming guest A's pid at ${Math.round(sent / secs)}/s → A's 5 real intents all accepted without retry, allowance untouched`,
                { intentMs: lat.map(x => x.ms), hostMaxLagMs: Math.round(lag), rateDrops: st1.rate - st0.rate, shed: st1.shed - st0.shed, bad: st1.bad - st0.bad, n: n.v || n.vals });
        }
        /* S6c: 위조 join 폭주 중에도 새 사람이 링크로 바로 들어온다(재시도 전) — join 허용량은 서명이 맞는 join 만 센다.
           hello_req(무서명) 폭주는 join 허용량과 별개 버킷 — hello 방송은 증폭 방지로 2초 간격까지 늦어지므로 입장은 ~2.5초 안 */
        if (run1(only, 'S6c')) {
            const X = await device(E, 'sX'), Y = await device(E, 'sY');
            try {
                const flood = async (junk, fn) => {
                    await H.ev('T.lag=0');
                    const p = (async () => { await sleep(700); return fn(); })();
                    const t0 = Date.now(); let sent = 0;
                    while (sent < junk.length) {
                        const due = Math.floor((Date.now() - t0) / 5);
                        while (sent < junk.length && sent <= due) { relay.inject(topic, 'g', junk[sent]); sent++; }
                        await sleep(4);
                    }
                    const r = await p;
                    return { r, rate: Math.round(sent / ((Date.now() - t0) / 1000)), lag: Math.round(await H.ev('T.lag')) };
                };
                const tj = async (P) => { const t = Date.now(); const r = await join(P, c.url); return { ok: r.ok, reason: r.reason, ms: Date.now() - t }; };
                const j1 = [], j2 = [];
                for (let i = 0; i < 700; i++) {
                    const fake = 'p' + [...Array(20)].map((_, k) => 'abcdefghijklmnopqrstuvwxyz234567'[(i * 7 + k * 13) % 32]).join('');
                    j1.push(await A.gEnv({ code, e: 'join', p: fake, c: 1e12 + i, d: { v: 2, dpk: { sig: evil.pub, dh: evil.pub }, want: 'play', t0: 1 } }));
                    j2.push({ v: 2, e: 'hello_req', n: 'n' + i });
                }
                const a = await flood(j1, () => tj(X));
                await sleep(2500);
                const b = await flood(j2, () => tj(Y));
                ok('S6c', a.r.ok && a.r.ms < 1500 && a.lag < 50 && b.r.ok && b.r.ms < 4500 && b.lag < 50,
                    `join flood: 700 forged joins at ${a.rate}/s → a real newcomer joins by link on the first try; 700 hello_req at ${b.rate}/s → still joins (hello is rate-limited, not join)`,
                    { forgedJoins: a, helloReqs: b });
                await X.ev('T.room&&T.room.leave()').catch(() => 0); await Y.ev('T.room&&T.room.leave()').catch(() => 0);
                await sleep(300);
            } finally { await closeAll(E, [X, Y]); }
        }
        /* S6d: 게스트 쪽도 같다 — A 를 사칭한 위조 g:x 폭주가 다른 게스트(B)의 "A 허용량"을 소진하지 못한다 → A 의 진짜 x 가 B 에 닿는다 */
        if (run1(only, 'S6d')) {
            const junk = [];
            for (let i = 0; i < 400; i++) junk.push(await A.gEnv({ code, e: 'x', p: pa, c: 3e15 + i, d: { k: 'fake', d: i } }));
            const x0 = await Gb.ev(`T.ev.filter(v=>v.e==='x'&&v.x.k==='real6d').length`);
            const sendP = (async () => { await sleep(600); for (let k = 0; k < 3; k++) { await Ga.ev(`T.room.x('real6d',{k:${k}})`); await sleep(300); } })();
            const t0 = Date.now(); let sent = 0;
            while (sent < junk.length) {
                const due = Math.floor((Date.now() - t0) / 5);
                while (sent < junk.length && sent <= due) { relay.inject(topic, 'g', junk[sent]); sent++; }
                await sleep(4);
            }
            await sendP; await sleep(500);
            const got = await Promise.all([H, Gb].map(p => p.ev(`({real:T.ev.filter(v=>v.e==='x'&&v.x.k==='real6d').length,fake:T.ev.filter(v=>v.e==='x'&&v.x.k==='fake').length})`)));
            ok('S6d', got.every(g => g.real - (g === got[1] ? x0 : 0) === 3 && g.fake === 0), "guest-side: forged g:x flood as A → host and guest B still receive A's 3 real x, 0 fake", got);
        }

        if (run1(only, 'S7')) {
            await H.ev(`T.room.x('result',{winner:'WINNER_XYZ',names:['Alice7','Bobby7']})`);
            await Ga.ev(`T.room.react(2)`);
            await H.ev(`T.room.setState(S=>{S.game.names=['Alice7','Bobby7','Carol7'];S.game.res='WINNER_XYZ'})`);
            await sleep(1200);
            const gotX = await Gb.ev(`(T.last('x')||{}).d&&T.last('x').d.winner`);
            const all = lis.got.join('\n');
            const hits = ['Alice7', 'Bobby7', 'Carol7', 'Hosty7', 'WINNER_XYZ'].filter(s => all.indexOf(s) >= 0);
            ok('S7', gotX === 'WINNER_XYZ' && hits.length === 0 && lis.got.length > 20, 'sealed mode: code-only listener sees 0 names / results in ' + lis.got.length + ' msgs (members do see them)', { membersGot: gotX, leaked: hits });
        }
        lis.stop(); rec.stop();
    } finally { await closeAll(E, pages); }

    if (run1(only, 'S8')) {
        const H2 = await device(E, 's8H'), P = await device(E, 's8P'), L = await device(E, 's8L');
        try {
            const c = await create(H2, { pinReq: true, pin: '8642' });
            const tok = c.url.split('.').slice(-1)[0];
            const lis = A.listener(relay, c.code);
            const jp = await join(P, c.code, { pin: '8642' });
            const jl = await join(L, c.url);
            await H2.ev('T.room.rotateLink()');
            await sleep(1500);
            const tok2 = await H2.ev('T.room.inviteUrl().split(".").slice(-1)[0]');
            /* 평문 필드(j)와 원문 전체에서 PIN·토큰 검색 */
            const plain = lis.got.map(s => { try { const o = JSON.parse(s); return (o.j || '') + (typeof o === 'string' ? o : ''); } catch (_) { return s; } }).join('\n');
            const all = lis.got.join('\n');
            const leaks = { pinPlain: plain.includes('8642'), tok: all.includes(tok), tok2: all.includes(tok2) };
            ok('S8', jp.ok && jl.ok && !leaks.pinPlain && !leaks.tok && !leaks.tok2 && lis.got.length > 5, 'PIN & link token never on the channel in plaintext (ECIES) — ' + lis.got.length + ' msgs scanned', { pinJoin: jp.ok, linkJoin: jl.ok, leaks });
            lis.stop();
        } finally { await closeAll(E, [H2, P, L]); }
    }
}
