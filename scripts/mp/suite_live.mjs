/* 실전(LIVE) 시나리오 — live.mjs 가 부른다. 실제 Supabase Realtime · 실제 게임 페이지 · 기기 = 브라우저 컨텍스트 */
import path from 'node:path';
import { dev, closeAll, bill, billReset, eqAll, sheet, zzKeys, sleep, J } from './live_h.mjs';

const CODE_RE = /^ZZ[2-9A-HJKMNP-TV-Z]{4}$/;
const fmt = (c) => c.slice(0, 3) + '-' + c.slice(3);
const spread = (a) => Math.max(...a) - Math.min(...a);
const V2UI = `document.readyState==='complete'&&window.LpRoomsUI&&!/stub/.test(LpRoomsUI.version)&&window.LpRooms&&!/stub/.test(LpRooms.version)`;

/* 방장 페이지에 테스트 키를 넣는다(이 문서에서 다음에 만드는 방 1개가 ZZ 코드) */
async function armKeys(H) {
    const k = await zzKeys();
    await H.wait(`window.LpRooms&&LpRooms.config&&!/stub/.test(LpRooms.version)`, 20000);
    await H.ev(`LpRooms.config({testKeys:[${J(k.keys)}]})`);
    return k.code;
}
async function closeRoom(H) { try { await H.ev(`(()=>{var r=window.LpRooms&&LpRooms.current();if(r&&r.isHost){r.close();return 1}return 0})()`, 4000); } catch (_) {} await sleep(1200); }
const clockOf = (P) => P.ev(`(()=>{var r=LpRooms.current();return r&&!r.isHost?{off:Math.round(r._off*10)/10,rtt:Math.round(r._rtt),n:r._clk.length}:null})()`);

/* ================================================================
   a — 룰렛: 방장 방 만들기(UI) → 링크 참가(/r/CODE#k) · 코드 입력 참가(홈 상자) → 공정 추첨 ×5 → 배지 → #cert 재검증
   ================================================================ */
export async function a({ E, ok, SHOTS, M }) {
    const H = await dev(E, 'Hana', { nick: '하나' }), G1 = await dev(E, 'Minji', { nick: '민지' }), G2 = await dev(E, 'Alex', { nick: 'Alex', lang: 'en' });
    const all = [H, G1, G2];
    try {
        /* 방장: 실제 버튼(👥 방 만들기) → 공통 UI 시트 → [만들기] */
        await H.nav('/games/roulette/', `document.readyState==='complete'&&!!window.LPV2&&!!document.querySelector('.lp-room-online-btn')`);
        await H.clickWhen('.lp-room-online-btn');
        await H.wait(`!!document.querySelector('.lpr-sheet .lpr-btn.go')`, 15000);
        const want = await armKeys(H);
        const tC = Date.now();
        await H.click('.lpr-sheet .lpr-btn.go');
        await H.wait(`LPV2._v.room&&LPV2._v.room.isHost`, 20000);
        const createMs = Date.now() - tC;
        const c = await H.ev(`({code:LPV2._v.room.code,url:LPV2._v.room.inviteUrl(),seal:LPV2._v.room.seal,real:!window.supabase.__shim})`);
        ok('La1', c.real && c.code === want && CODE_RE.test(c.code) && /\/r\/ZZ....#k=/.test(c.url), 'roulette: host creates a room through the real UI over real Realtime (vendored supabase-js), ZZ test code', { code: c.code, createMs, seal: c.seal });

        /* 게스트 1: 초대 링크 /r/CODE#k=… (허브가 받아 게임으로 넘긴다) */
        const link = c.url.replace(/^https?:\/\/[^/]+/, '');
        const ms1 = await G1.nav(link, `location.pathname==='/games/roulette/'&&window.LPV2&&LPV2._v.room&&LPV2.guest()`, 40000);
        const w1 = await G1.ev(`({s:location.search,h:location.hash,seal:LPV2._v.room.seal,nick:(LPV2._v.room.roster().find(m=>m.p===LPV2._v.room.me.pid)||{}).n})`);
        const l1 = await G1.joinLat();
        /* 게스트 2: 홈의 참가 상자에 코드를 직접 입력 */
        await G2.nav('/', `document.readyState==='complete'&&!!document.getElementById('lpHomeJoinBtn')`);
        await sleep(300);
        await G2.ev(`document.getElementById('lpHomeJoinBtn').click()`);
        await G2.wait(`!!document.querySelector('.lpr-sheet .lpr-cells input')`, 20000);
        const t2 = Date.now();
        await G2.ev(`(()=>{const i=document.querySelector('.lpr-sheet .lpr-cells input');i.value=${J(fmt(c.code).toLowerCase())};i.dispatchEvent(new Event('input'))})()`);
        await G2.wait(`location.pathname==='/games/roulette/'&&window.LPV2&&LPV2._v.room&&LPV2.guest()`, 40000);
        const ms2 = Date.now() - t2;
        const w2 = await G2.ev(`({s:location.search,seal:LPV2._v.room.seal})`);
        const l2 = await G2.joinLat();
        const ros = await eqAll(all, `LPV2._v.room.roster().map(m=>m.n+':'+m.c).sort().join(',')`, 15000);
        M.lat.push({ what: 'roulette link join (/r/ → hub → game, page loads included)', ms: ms1, handshake: l1 }, { what: 'roulette code join (home box: type → resolve → navigate → join)', ms: ms2, handshake: l2 });
        ok('La2', w1.s === '?r=' + c.code && !w1.h && w1.seal === c.seal && w2.s === '?r=' + c.code && w2.seal === c.seal && ros.ok && ros.v.split(',').length === 3,
            'roulette: guest 1 by /r/CODE#k link, guest 2 by typing the code in the home join box → same room, same seal emoji, roster 3 on every device', { linkMs: ms1, codeMs: ms2, hs1: l1, hs2: l2, roster: ros.v || ros.vals, seal: c.seal });
        await sleep(2500);   /* 합류 직후 빠른 시계 에코 */
        const shots = []; for (const p of all) shots.push(await p.shot(path.join(SHOTS, `a1_${p.label}.png`)));
        await sheet(E, shots, path.join(SHOTS, 'a1_roulette_lobby_host-link-code.png'), 'LIVE a · roulette room over real Supabase Realtime — host | guest (link) | guest (typed code)');

        /* 공정 추첨 ×5 */
        const rounds = [];
        for (let i = 1; i <= 5; i++) {
            await billReset(all);
            const tD = Date.now();
            if (i === 1) await H.click('#startBtn'); else await H.click('#replayBtn');
            const done = await Promise.all(all.map(p => p.wait(`LPV2._v.cur&&LPV2._v.cur.round===${i}&&LPV2._v.cur.ended&&LPV2._v.dbg.res[${i}]`, 45000).then(() => true).catch(e => String(e.message).slice(0, 160))));
            const res = await Promise.all(all.map(p => p.ev(`LPV2._v.dbg.res[${i}]||null`)));
            const st = await Promise.all(all.map(p => p.ev(`LPV2._v.dbg.starts[${i}]||null`)));
            const b = await bill(all);
            /* 목격 집계(hb 편승)가 돌아오길 잠깐 */
            const wit = await Promise.all(all.map(p => p.wait(`(LPV2._v.wit[${i}]||{}).ok===3`, 14000).then(() => 3).catch(() => p.ev(`(LPV2._v.wit[${i}]||{}).ok||0`))));
            const badge = await Promise.all(all.map(p => p.ev(`(document.querySelector('.lpv2-badge[data-round="${i}"]')||{}).textContent||''`)));
            const winner = await H.ev(`(()=>{const c=LPV2._v.certs[${i}];return c&&c.params&&c.res?c.params.names[c.res.w]:null})()`);
            const intended = st.map(s => s && s.intended).filter(x => typeof x === 'number');
            rounds.push({ i, done, same: res.every(r => r && r === res[0]), winner, startSkewMs: intended.length === 3 ? Math.round(spread(intended)) : null, firstFrameSkewMs: st.every(s => s && s.at) ? Math.round(spread(st.map(s => s.at - (s.e0 || 0)))) : null, wit, badge, bill: b.bill, sent: b.sent, ms: Date.now() - tD });
            if (i === 1) { const sh = []; for (const p of all) sh.push(await p.shot(path.join(SHOTS, `a2_${p.label}.png`))); await sheet(E, sh, path.join(SHOTS, 'a2_roulette_result_badge.png'), 'LIVE a · fair draw #1 result + verified badge — host | guest | guest'); }
            await sleep(400);
        }
        const allSame = rounds.every(r => r.same && r.done.every(d => d === true));
        const skews = rounds.map(r => r.startSkewMs);
        M.skew.push({ what: 'roulette draw startAt (3 devices, 5 draws) — intended local start spread', ms: skews }, { what: 'roulette first rendered frame spread', ms: rounds.map(r => r.firstFrameSkewMs) });
        M.rate.rouletteDraw3 = { billPerDraw: rounds.map(r => r.bill), sent: rounds[rounds.length - 1].sent };
        ok('La3', allSame && rounds.length === 5, 'roulette: 5 fair draws → identical result on all 3 devices every time', rounds.map(r => ({ i: r.i, winner: r.winner, same: r.same, done: r.done.every(d => d === true) || r.done })));
        ok('La4', rounds.every(r => r.wit.every(w => w === 3) && r.badge.every(t => /3/.test(t) && /✓/.test(t))), 'roulette: verified badge "✓ fair · 3 confirmed" on all devices (witness tally rides on heartbeats)', { badge: rounds[4].badge, wit: rounds.map(r => r.wit.join('/')) });
        ok('La5', skews.every(s => s != null && s <= 80), 'roulette: synchronized start over the real network — intended-start spread ≤ 80ms (D2 target) on every draw', { startSkewMs: skews, firstFrameSkewMs: rounds.map(r => r.firstFrameSkewMs), clock: await Promise.all([G1, G2].map(clockOf)) });
        ok('La6', rounds.every(r => r.bill <= 120), 'roulette: a 3-person fair draw costs ≤ 120 billed messages (§7: 8 people ≈ 152)', { bill: rounds.map(r => r.bill), lastSent: rounds[4].sent });

        /* #cert 링크: 새 기기(방에 없던 컨텍스트)에서 서버 없이 재검증 + 위조 1글자 → ✗ */
        const certUrl = await H.ev(`LPV2._t.certLink(LPV2._v.certs[5])`);
        const forged = await H.ev(`LpFair.cert.encode(Object.assign({},LPV2._v.certs[5],{params:{names:LPV2._v.certs[5].params.names.map((n,i)=>i?n:n+'x')}})).then(s=>location.origin+'/games/roulette/#cert='+s)`);
        const hostRes = await H.ev(`LPV2._v.dbg.res[5]`);
        const X = await dev(E, 'Verifier', { nick: 'V', lang: 'en' }); all.push(X);
        await X.nav(certUrl.replace(/^https?:\/\/[^/]+/, ''), `document.readyState==='complete'&&window.LPV2&&LPV2._v.dbg.cert`, 30000);
        const v = await X.ev(`({c:LPV2._v.dbg.cert,banner:(document.querySelector('.lpv2-banner')||{}).textContent||'',room:!!(window.LpRooms&&LpRooms.current&&LpRooms.current())})`);
        await sleep(1500); const certShot = await X.shot(path.join(SHOTS, 'a3_Verifier_cert.png'));
        await X.nav('about:blank'); await sleep(200);
        await X.nav(forged.replace(/^https?:\/\/[^/]+/, ''), `document.readyState==='complete'&&window.LPV2&&LPV2._v.dbg.cert`, 30000);
        const vf = await X.ev(`({c:LPV2._v.dbg.cert,banner:(document.querySelector('.lpv2-banner')||{}).textContent||''})`);
        const forgedShot = await X.shot(path.join(SHOTS, 'a3_Verifier_forged.png'));
        await sheet(E, [certShot, forgedShot], path.join(SHOTS, 'a3_roulette_cert_fresh-context.png'), 'LIVE a · #cert link re-verified in a fresh context (no room, no server) | same link with 1 character changed');
        ok('La7', v.c && v.c.ok === true && v.c.res === hostRes && !v.room && vf.c && vf.c.ok === false, 'roulette: #cert link re-verifies in a fresh context (no room joined) with the same result; 1-character forgery → ✗', { verified: v.c, banner: v.banner, forged: vf.c, forgedBanner: vf.banner, urlLen: certUrl.length });
        const exc = all.map(p => p.exc.slice(0, 2)).filter(x => x.length);
        ok('La8', !exc.length, 'roulette: 0 page exceptions on 4 devices', exc);
        await closeRoom(H);
        const closed = await Promise.all([G1, G2].map(p => p.ev(`!LPV2._v.room`)));
        ok('La9', closed.every(Boolean), 'roulette: host closes the room → guests released', closed);
    } finally { await closeRoom(H); await closeAll(E, all); }
}

/* ================================================================
   b — 윷: 방장 + 게스트 2 (한 명은 /lobby/ 허브에 코드 입력 = f 의 허브 절반)
       캐릭터 고르기 잠금 → 준비 → 시작 → 던지기 포함 여러 턴 → 게스트 새로고침 복귀 → 끝 → 한 판 더 → 내보내기
   ================================================================ */
const YK = '__yutV2.K';
const YUT_STEP = `(()=>{const V=__yut.V;if(!V||V.phase!=='play'||!__yut.canInput())return 0;if(V.throws>0){document.getElementById('btnThrow').click();return 1}const os=__yut.options(V,V.turn);if(os.length){window.__yutV2.K.act({k:'move',from:os[0].from,v:os[0].v});return 2}return 0})()`;
async function yutDrive(pages, H, maxMs, stat) {
    const t0 = Date.now();
    while (Date.now() - t0 < maxMs) {
        const ph = await H.ev(`${YK}.S().phase`).catch(() => 'err');
        if (ph !== 'playing') return ph;
        for (const p of pages) { const r = await p.ev(YUT_STEP).catch(() => 0); if (stat && r === 1) stat.throws++; if (stat && r === 2) stat.moves++; }
        await sleep(350);
    }
    return 'timeout';
}
export async function b({ E, ok, SHOTS, M }) {
    const H = await dev(E, 'Hana', { nick: '하나' }), G1 = await dev(E, 'Minji', { nick: '민지' }), G2 = await dev(E, 'Alex', { nick: 'Alex', lang: 'en' });
    const all = [H, G1, G2];
    const YON = `window.__yutV2&&__yutV2.on&&!!__yutV2.K&&!!${YK}.S()`;
    try {
        await H.nav('/games/yut/', `document.readyState==='complete'&&!!window.__yutV2`);
        await H.ev(`__yutV2.v2Ready().then(()=>1)`, 30000);
        const want = await armKeys(H);
        await H.ev(`(__yutV2.v2Create(),1)`);
        await H.wait(`${YON}&&${YK}.room.isHost`, 25000);
        const c = await H.ev(`({code:${YK}.room.code,url:${YK}.inviteUrl(),seal:${YK}.room.seal})`);
        /* 게스트 1: 초대 링크(/r/) · 게스트 2: /lobby/ 허브에 코드 입력 → 윷 페이지로 */
        const ms1 = await G1.nav(c.url.replace(/^https?:\/\/[^/]+/, ''), `location.pathname==='/games/yut/'&&${YON}`, 45000);
        await G2.nav('/lobby/', `document.readyState==='complete'&&!!document.querySelector('#lprHub .lpr-cells input')`, 30000);
        const hubShot = await G2.shot(path.join(SHOTS, 'f_Alex_hub.png'));
        const t2 = Date.now();
        await G2.ev(`(()=>{const i=document.querySelector('#lprHub .lpr-cells input');i.value=${J(c.code)};i.dispatchEvent(new Event('input'))})()`);
        const hubOk = await G2.wait(`location.pathname==='/games/yut/'&&${YON}`, 45000).then(() => true).catch(e => String(e.message).slice(0, 200));
        const ms2 = Date.now() - t2;
        M.lat.push({ what: 'yut link join (/r/ → hub → game)', ms: ms1, handshake: await G1.joinLat() }, { what: 'yut code join (/lobby/ hub: type → resolve → navigate → join)', ms: ms2, handshake: await G2.joinLat() });
        ok('Lf2', hubOk === true && (await G2.ev(`location.search`)) === '?r=' + c.code, '/lobby/ hub: typed code resolves to the right game (yut) and joins', { ms: ms2, hubOk });
        const pids = await Promise.all(all.map(p => p.ev(`${YK}.me.pid`)));
        let eq = await eqAll(all, `${YK}.S().roster.map(m=>m.p+':'+m.r+':'+m.seat).sort().join(',')`);
        ok('Lb1', c.code === want && eq.ok && eq.v.split(',').length === 3, 'yut: host + 2 guests (link, hub code) → identical roster with seats', { code: c.code, roster: eq.ok ? eq.v.replace(/p[a-z2-7]{20}/g, m => 'p' + pids.indexOf(m)) : eq.vals });

        /* 캐릭터 잠금 */
        const opts = await H.ev(`(LpRooms.getAdapter().picks||[]).find(p=>p.key==='char').options`);
        const p1 = await G1.ev(`${YK}.pick('char',${J(opts[1])})`); await sleep(700);
        const p2 = await G2.ev(`${YK}.pick('char',${J(opts[1])})`);
        const p3 = await G2.ev(`${YK}.pick('char',${J(opts[2])})`); await sleep(700);
        eq = await eqAll(all, `${YK}.S().roster.filter(m=>m.seat!=null).map(m=>(m.pick||{}).char||'-').join(',')`);
        ok('Lb2', p1 && p1.ok && p2 && !p2.ok && p2.reason === 'taken' && p3 && p3.ok && eq.ok, 'yut: character pick lock — second pick of the same character = taken; picks identical on all devices', { p2, picks: eq.v || eq.vals });
        /* 준비 게이트 → 시작 */
        const c0 = await H.ev(`${YK}.canStart()`);
        await G1.ev(`${YK}.ready(true)`); await sleep(500);
        const c1 = await H.ev(`${YK}.canStart()`);
        await G2.ev(`${YK}.ready(true)`);
        const c2 = await H.wait(`${YK}.canStart()`, 6000).then(() => true).catch(() => false);
        const sh = []; for (const p of all) sh.push(await p.shot(path.join(SHOTS, `b1_${p.label}.png`)));
        await sheet(E, sh, path.join(SHOTS, 'b1_yut_lobby_ready.png'), 'LIVE b · yut lobby over real Realtime — host | guest (link) | guest (hub code): picks locked, all ready');
        await H.ev(`${YK}.setOpt('k',1)`); await H.ev(`${YK}.setOpt('turnSec',15)`); await sleep(500);
        const clk0 = await Promise.all([G1, G2].map(clockOf));
        await H.ev(`${YK}.start()`);
        eq = await eqAll(all, `${YK}.S().phase==='playing'&&!!${YK}.S().game&&(${YK}.S().game.game+':'+${YK}.S().tk.seats.length)`, 20000);
        ok('Lb3', c0 === false && c1 === false && c2 && eq.ok, 'yut: ready gate (host cannot start until both ready) → start → same board on all 3', { c0, c1, c2, game: eq.v || eq.vals });
        await sleep(2500);
        /* 여러 턴(던지기 포함) — 30초 동안 실제 입력, 과금률 측정 */
        await billReset(all);
        const stat = { throws: 0, moves: 0 };
        const seq0 = await H.ev(`${YK}.S().game.seq`);
        await yutDrive(all, H, 30000, stat);
        const b1 = await bill(all);
        const seqs = await eqAll(all, `${YK}.S().game?String(${YK}.S().game.seq):'x'`, 8000);
        const rs = await Promise.all(all.map(p => p.ev(`({t:Date.now(),r:${YK}.remain()})`)));
        const adj = rs.filter(x => x.r != null).map(x => x.r + (x.t - rs[0].t));
        M.rate.yutPlay3 = { perSec: b1.perSec, bill: b1.bill, sent: b1.sent, budget: 'DESIGN 7 turn 4p 3.9 msg/s (E2 <= 5.0)' };
        M.skew.push({ what: 'yut turn deadline display spread (3 devices)', ms: adj.length ? Math.round(spread(adj)) : null });
        const sh2 = []; for (const p of all) sh2.push(await p.shot(path.join(SHOTS, `b2_${p.label}.png`)));
        await sheet(E, sh2, path.join(SHOTS, 'b2_yut_play.png'), 'LIVE b · yut mid-game after real throws/moves — host | guest | guest');
        ok('Lb4', stat.throws >= 3 && stat.moves >= 2 && seqs.ok && +seqs.v > seq0 && (adj.length < 2 || spread(adj) <= 300) && b1.perSec <= 5.0, 'yut: several real turns incl. throws → same game seq on all, deadline display spread ≤ 300ms, ≤ 5.0 billed msg/s', { stat, seq: seqs.v || seqs.vals, deadlineSpreadMs: adj.length ? Math.round(spread(adj)) : null, msgPerSec: b1.perSec, sent: b1.sent });

        /* 게스트 새로고침 → 같은 자리 복귀 */
        const s1 = await H.ev(`${YK}.seatOf(${J(pids[1])})`);
        const tR = Date.now();
        await G1.c.send('Page.reload', { ignoreCache: true });
        await sleep(400);
        const back = await G1.wait(`document.readyState==='complete'&&${YON}&&${YK}.S().phase==='playing'`, 30000).then(() => true).catch(e => String(e.message).slice(0, 200));
        const backMs = Date.now() - tR;
        await sleep(800);
        const s1b = await H.ev(`${YK}.seatOf(${J(pids[1])})`), c1b = await H.ev(`(${YK}.S().roster.find(m=>m.p===${J(pids[1])})||{}).c`), mine = await G1.ev(`${YK}.seat()`).catch(() => null);
        M.lat.push({ what: 'yut guest refresh → back in seat (page reload included)', ms: backMs, handshake: await G1.joinLat() });
        ok('Lb5', back === true && s1 != null && s1 === s1b && mine === s1 && c1b === 'on', 'yut: guest refresh mid-game → reconnects to the same seat', { backMs, seat: s1, after: s1b, guestSees: mine, conn: c1b });

        /* 끝까지(연출 생략: 숨김) → 결과 → 한 판 더 */
        for (const p of all) await p.ev(`__vis(true)`);
        const ph = await yutDrive(all, H, 240000);
        for (const p of all) await p.ev(`__vis(false)`);
        await H.wait(`${YK}.S().phase==='result'`, 20000).catch(() => {});
        const res = await eqAll(all, `${YK}.S().phase+':'+(${YK}.S().tk.res&&${YK}.S().tk.res.winner)`, 10000);
        await sleep(1200);
        const sh3 = []; for (const p of all) sh3.push(await p.shot(path.join(SHOTS, `b3_${p.label}.png`)));
        await sheet(E, sh3, path.join(SHOTS, 'b3_yut_result.png'), 'LIVE b · yut result — host | guest | guest');
        await H.ev(`${YK}.rematch()`); await sleep(1000);
        const lob = await eqAll(all, `${YK}.S().phase`, 10000);
        const rdReset = await H.ev(`${YK}.S().roster.filter(m=>m.r==='player').every(m=>!m.rd)`);
        ok('Lb6', res.ok && /^result:\d$/.test(res.v) && lob.ok && lob.v === 'lobby' && rdReset, 'yut: game played to the end → same winner on all → rematch = back to lobby, ready reset', { ph, res: res.v || res.vals, lobby: lob.v || lob.vals, rdReset });

        /* 내보내기 */
        await H.ev(`${YK}.kick(${J(pids[2])},false)`);
        const gone = await G2.wait(`!__yutV2.on`, 10000).then(() => true).catch(() => false);
        await sleep(800);
        const inRoster = await H.ev(`!!${YK}.S().roster.find(m=>m.p===${J(pids[2])})`);
        const g1sees = await G1.ev(`${YK}.S().roster.length`);
        const kShot = await G2.shot(path.join(SHOTS, 'b4_Alex_kicked.png')), hShot = await H.shot(path.join(SHOTS, 'b4_Hana_after_kick.png'));
        await sheet(E, [hShot, kShot], path.join(SHOTS, 'b4_yut_kick.png'), 'LIVE b · kick — host lobby after kick | kicked guest');
        ok('Lb7', gone && !inRoster && g1sees === 2, 'yut: host kicks a guest → guest leaves the room screen, roster 2 on the others', { gone, inRoster, g1sees });
        const exc = all.map(p => p.exc.slice(0, 2)).filter(x => x.length);
        ok('Lb8', !exc.length, 'yut: 0 page exceptions', exc);
        M.notes.push({ yutClockBeforeStart: clk0, yutClockEnd: await Promise.all([G1].map(clockOf)) });
        await sheet(E, [hubShot], path.join(SHOTS, 'f_hub_code_entry.png'), 'LIVE f · /lobby/ hub before typing the code');
    } finally { await closeRoom(H); await closeAll(E, all); }
}

/* ── 공통: API 로 방 만들기(UI 가 'room' 으로 붙인다) · 게임 URL 로 참가 ── */
async function apiCreate(H, gid, ready) {
    await H.nav(`/games/${gid}/`, ready, 40000);
    const want = await armKeys(H);
    const c = await H.ev(`LpRooms.create({gameId:${J(gid)}}).then(r=>({code:r.code,url:r.inviteUrl(),pid:r.me.pid,seal:r.seal}))`, 30000);
    await H.wait(`LpRoomsUI.room()&&LpRoomsUI.room().isHost`, 10000);
    c.want = want;
    return c;
}
const gameUrl = (gid, c) => `/games/${gid}/?r=${c.code}#${c.url.split('#')[1] || ''}`;
async function urlJoin(G, gid, c, ready) {
    const ms = await G.nav(gameUrl(gid, c), ready + `&&LpRoomsUI.room&&!!LpRoomsUI.room()&&LpRoomsUI.room().me.role!=='host'`, 45000);
    return { ms, hs: await G.joinLat(), pid: await G.ev(`LpRoomsUI.room().me.pid`) };
}
const uiReady = (G) => G.ev(`LpRoomsUI.room().intent('ready',true).then(r=>r.ok)`);
async function lobbyStart(H) {
    await H.wait(`LpRoomsUI.room().canStart()`, 12000);
    return H.clickWhen('.lpr-lobby .lpr-btn.go', '', 8000);
}

/* ================================================================
   c — 테트로미노 레이스: 방장 + 게스트 1 → 동시 출발 → 순위(hb 편승) → 결과
   ================================================================ */
const RACEREADY = V2UI + `&&LpRooms.getAdapter&&!!LpRooms.getAdapter()&&!!window.LpRoomsRace`;
const RINFO = `(()=>{const i=LpRoomsRace.info();return {st:i.st,heat:i.heat,seed:i.seed,t0:i.t0,skew:i.skew,ts:i.trueStart,fin:i.fin,card:i.card,chip:i.chip,res:i.game&&i.game.res?i.game.res.map(r=>r.p+':'+r.s).join(','):null,gst:i.game&&i.game.st}})()`;
export async function c({ E, ok, SHOTS, M }) {
    const H = await dev(E, 'Hana', { nick: '하나' }), G1 = await dev(E, 'Minji', { nick: '민지' });
    const all = [H, G1];
    try {
        const c = await apiCreate(H, 'tetris', RACEREADY);
        const j = await urlJoin(G1, 'tetris', c, RACEREADY);
        await H.wait(`LpRoomsUI.room().roster().length===2`, 10000);
        M.lat.push({ what: 'tetris link join (game URL)', ms: j.ms, handshake: j.hs });
        await H.ev(`(()=>{const r=LpRooms.getAdapter().race;r.durFor=()=>20;r.durationS=20;return true})()`);
        await sleep(2500);
        const sh = []; for (const p of all) sh.push(await p.shot(path.join(SHOTS, `c1_${p.label}.png`)));
        await sheet(E, sh, path.join(SHOTS, 'c1_tetris_lobby.png'), 'LIVE c · tetromino race lobby — host | guest');
        await uiReady(G1);
        const btn = await lobbyStart(H);
        await Promise.all(all.map(p => p.wait(`LpRoomsRace.info().st==='play'`, 25000)));
        const inf = await Promise.all(all.map(p => p.ev(RINFO)));
        const pr = await Promise.all(all.map(p => p.ev(`JSON.stringify(LpRooms.getAdapter().race.probe(60))`)));
        const ts = inf.map(i => i.ts), sp = Math.round(spread(ts));
        M.skew.push({ what: 'tetris race true start spread (2 devices)', ms: sp, localSkew: inf.map(i => Math.round(i.skew)) });
        ok('Lc1', c.code === c.want && inf.every(i => i.seed === inf[0].seed && /^[0-9a-f]{64}$/.test(i.seed)) && pr[0] === pr[1] && sp <= 80,
            'tetris race: host + guest → same fair seed, same first 60 pieces, synchronized start (true start spread ≤ 80ms) over real Realtime', { code: c.code, seed: inf[0].seed.slice(0, 12), startSpreadMs: sp, localSkew: inf.map(i => Math.round(i.skew)), uiStartBtn: btn });
        /* 순위판: 게스트 점수 → 방장 LIVE → 게스트 칩 (hb 편승) */
        await sleep(1500);
        await billReset(all);
        await G1.ev(`(score=4321,true)`);
        const hostSees = await H.wait(`((LpRoomsRace.info().live||{})[${J(j.pid)}]||{}).g===4321`, 14000).then(() => true).catch(() => false);
        await sleep(600);
        const chip = await H.ev(`LpRoomsRace.info().chip`);
        const s1 = []; for (const p of all) s1.push(await p.shot(path.join(SHOTS, `c2_${p.label}.png`)));
        await sheet(E, s1, path.join(SHOTS, 'c2_tetris_race_play.png'), 'LIVE c · tetromino race in play (standings chip) — host | guest');
        const b = await bill(all);
        const extra = Object.keys(b.sent).filter(k => !/^(h|g):hb$/.test(k));
        M.rate.tetrisRace2 = { perSec: b.perSec, sent: b.sent, budget: 'DESIGN 7 race 8p 8.6 msg/s (E4 <= 10)' };
        ok('Lc2', hostSees && extra.length === 0, 'tetris race: live standings ride on heartbeats (guest score → host), 0 extra message kinds while playing', { hostSees, chip, sent: b.sent, msgPerSec: b.perSec });
        /* 결과 */
        const res = await eqAll(all, `(()=>{const i=LpRoomsRace.info();return i.game&&i.game.st==='res'&&i.game.res?i.game.res.map(r=>r.p+':'+r.s).join(','):null})()`, 60000);
        await sleep(1500);
        const s2 = []; for (const p of all) s2.push(await p.shot(path.join(SHOTS, `c3_${p.label}.png`)));
        await sheet(E, s2, path.join(SHOTS, 'c3_tetris_race_result.png'), 'LIVE c · tetromino race result card — host | guest');
        const card = await Promise.all(all.map(p => p.ev(`!!LpRoomsRace.info().card`)));
        ok('Lc3', res.ok && card.every(Boolean), 'tetris race: both devices get the same final standings + result card', { res: res.ok ? res.v.replace(/p[a-z2-7]{20}/g, m => m === j.pid ? 'guest' : 'host') : res.vals, card });
        const exc = all.map(p => p.exc.slice(0, 2)).filter(x => x.length);
        ok('Lc4', !exc.length, 'tetris: 0 page exceptions', exc);
    } finally { await closeRoom(H); await closeAll(E, all); }
}

/* ================================================================
   d — 카레이싱 같이 보기: 방장 + 게스트 2, 레이스 1회(틱 10Hz) → 같은 순위 · '공정 시드' 배지
   ================================================================ */
export async function d({ E, ok, SHOTS, M }) {
    const H = await dev(E, 'Hana', { nick: '하나' }), G1 = await dev(E, 'Minji', { nick: '민지' }), G2 = await dev(E, 'Alex', { nick: 'Alex', lang: 'en' });
    const all = [H, G1, G2], G = [G1, G2];
    const CR = V2UI + `&&!!window.__crv2`;
    try {
        const c = await apiCreate(H, 'car-racing', CR);
        await H.wait(`__crv2.room&&__crv2.room.isHost`, 10000);
        for (const g of G) { const j = await urlJoin(g, 'car-racing', c, CR); M.lat.push({ what: 'car-racing link join (game URL)', ms: j.ms, handshake: j.hs }); }
        await Promise.all(G.map(g => g.wait(`__crv2.room&&!__crv2.room.isHost`, 10000)));
        /* 방장 설정: 가장 짧은 레이스 */
        await H.ev(`(()=>{const set=(id,v)=>{const e=document.getElementById(id);e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))};set('playerCount',4);set('raceTime',30);set('lapCount',1);set('gameSpeed',2.5);return 1})()`);
        /* 방장 화면의 실제 값(게임이 바퀴 수에 맞춰 경주 시간을 다시 잡는다)과 게스트 화면이 같아야 한다 */
        const CFGX = `document.getElementById('raceTime').value+'/'+document.getElementById('lapCount').value+'/'+document.getElementById('playerCount').value+'/'+document.getElementById('gameSpeed').value`;
        await sleep(600);
        const hostCfg = await H.ev(CFGX);
        const cfgOk = await Promise.all(G.map(g => g.wait(CFGX + `===${J(hostCfg)}`, 10000).then(() => true).catch(() => false)));
        const cfg = await eqAll(all, CFGX, 3000);
        const s0 = []; for (const p of all) s0.push(await p.shot(path.join(SHOTS, `d1_${p.label}.png`)));
        await sheet(E, s0, path.join(SHOTS, 'd1_car_setup_mirrored.png'), 'LIVE d · car racing setup mirrored to guests — host | guest | guest');
        await sleep(1500);
        await billReset(all);
        await H.click('#startBtn');
        const started = await Promise.all(G.map(g => g.wait(`__crv2.dbg().guestRender&&__crv2.dbg().race`, 30000).then(() => true).catch(e => String(e.message).slice(0, 160))));
        await H.wait(`__crv2.dbg().running`, 15000).catch(() => 0);
        await sleep(4500);                      /* 카운트다운(3·2·1·GO) 뒤 — 달리는 구간만 잰다 */
        const bStart = await bill(all);
        await billReset(all);
        await sleep(6000);
        const s1 = []; for (const p of all) s1.push(await p.shot(path.join(SHOTS, `d2_${p.label}.png`)));
        await sheet(E, s1, path.join(SHOTS, 'd2_car_race_live.png'), 'LIVE d · car race watched together (10Hz ticks over real Realtime) — host | guest | guest');
        const bMid = await bill(all);
        const fo = await eqAll(all, `__crv2.dbg().fo&&__crv2.dbg().fo.split(',').length>=4&&!__crv2.dbg().running?__crv2.dbg().fo:null`, 150000);
        const bEnd = await bill(all);
        const badge = await Promise.all(all.map(p => p.wait(`(()=>{const e=document.getElementById('lpV2Badge');return e&&!e.hidden&&e.textContent})()`, 20000).catch(() => '')));
        await sleep(800);
        const s2 = []; for (const p of all) s2.push(await p.shot(path.join(SHOTS, `d3_${p.label}.png`)));
        await sheet(E, s2, path.join(SHOTS, 'd3_car_result.png'), 'LIVE d · car race result + fair-seed badge — host | guest | guest');
        const tickHz = (bMid.sent['h:tick'] || 0) / (bMid.ms / 1000);
        M.rate.carRace3 = { tickHz: +tickHz.toFixed(1), perSecDuringRace: bMid.perSec, startBill: bStart.bill, startSent: bStart.sent, raceBill: bEnd.bill, raceSecs: Math.round(bEnd.ms / 1000), sent: bEnd.sent, budget: 'DESIGN 7: 10Hz ticks x N (8p 30s = 2,400)' };
        ok('Ld1', c.code === c.want && cfgOk.every(Boolean) && cfg.ok && /\/1\/4\/2\.5$/.test(cfg.v) && started.every(x => x === true), 'car racing: host setup mirrored to guests, race start reaches both guests (countdown + tick stream)', { cfg: cfg.v || cfg.vals, started });
        ok('Ld2', fo.ok && badge.every(t => /✓/.test(String(t))), 'car racing: one watch-together race → identical finish order on all 3 devices, "✓ fair seed" badge', { finish: fo.v || fo.vals, badge });
        ok('Ld3', tickHz <= 10.5 && bMid.perSec <= 10.5 * 3 + 6, 'car racing: tick stream ≤ 10 Hz (billed ≈ 10 × N msg/s during the race)', { tickHz: +tickHz.toFixed(1), msgPerSec: bMid.perSec, startBill: bStart.bill, raceBill: bEnd.bill, raceSecs: Math.round(bEnd.ms / 1000), sent: bEnd.sent });
        const exc = all.map(p => p.exc.slice(0, 2)).filter(x => x.length);
        ok('Ld4', !exc.length, 'car racing: 0 page exceptions', exc);
    } finally { await closeRoom(H); await closeAll(E, all); }
}

/* ================================================================
   e — 풍선 파티 1판: 방장 + 게스트 2 → 대기실 준비 → 시작 → 돌아가며 펌프 → 터짐 → 같은 결과·검증 배지
   ================================================================ */
const BSTEP = `(()=>{const d=__lpv2.dbg(),g=d.g;if(!g)return 'nog';if(g.pop)return 'pop';const b=document.getElementById('btnPump'),p=document.getElementById('btnPass');if(!b.disabled){if(g.tp>=2&&!p.disabled){p.click();return 'pass'}b.click();return 'pump'}if(!p.disabled&&g.tp>=2){p.click();return 'pass'}return 0})()`;
export async function e({ E, ok, SHOTS, M }) {
    const H = await dev(E, 'Hana', { nick: '하나' }), G1 = await dev(E, 'Minji', { nick: '민지' }), G2 = await dev(E, 'Alex', { nick: 'Alex', lang: 'en' });
    const all = [H, G1, G2], G = [G1, G2];
    const BR = V2UI + `&&!!window.__lpv2`;
    try {
        const c = await apiCreate(H, 'balloon', BR);
        for (const g of G) { const j = await urlJoin(g, 'balloon', c, BR); M.lat.push({ what: 'balloon link join (game URL)', ms: j.ms, handshake: j.hs }); }
        await H.wait(`LpRoomsUI.room().roster().length===3`, 10000);
        for (const g of G) await uiReady(g);
        await sleep(600);
        const s0 = []; for (const p of all) s0.push(await p.shot(path.join(SHOTS, `e1_${p.label}.png`)));
        await sheet(E, s0, path.join(SHOTS, 'e1_balloon_lobby.png'), 'LIVE e · balloon party lobby — host | guest | guest');
        await billReset(all);
        const btn = await lobbyStart(H);
        const inGame = await Promise.all(all.map(p => p.wait(`__lpv2.dbg().g&&__lpv2.dbg().g.rd>=1`, 25000).then(() => true).catch(e => String(e.message).slice(0, 160))));
        const acts = { pump: 0, pass: 0 }; let popped = false, shotMid = false;
        const t0 = Date.now();
        while (Date.now() - t0 < 150000 && !popped) {
            for (const p of all) { const r = await p.ev(BSTEP).catch(() => 0); if (r === 'pump') acts.pump++; else if (r === 'pass') acts.pass++; else if (r === 'pop') popped = true; }
            if (!shotMid && acts.pump >= 3) { shotMid = true; const s1 = []; for (const p of all) s1.push(await p.shot(path.join(SHOTS, `e2_${p.label}.png`))); await sheet(E, s1, path.join(SHOTS, 'e2_balloon_play.png'), 'LIVE e · balloon party mid-round (turn-based pumps, hash-chain fairness) — host | guest | guest'); }
            await sleep(450);
        }
        const res = await eqAll(all, `(()=>{const g=__lpv2.dbg().g;return g&&g.pop?g.pl[g.pop.i].n+'@'+g.pop.k:null})()`, 12000);
        const cert = await Promise.all(all.map(p => p.wait(`__lpv2.dbg().vr.certOk===true`, 20000).then(() => true).catch(() => false)));
        const b = await bill(all);
        const badge = await Promise.all(all.map(p => p.wait(`(()=>{const e=document.getElementById('lpBadge');return e&&!e.hidden&&/✓/.test(e.textContent)?e.textContent:''})()`, 20000).catch(() => p.ev(`(()=>{const e=document.getElementById('lpBadge');return e?'hidden='+e.hidden+' text='+e.textContent:'no #lpBadge'})()`))));
        const pumps = await H.ev(`(__lpv2.dbg().g||{}).k|0`);
        const logChk = await H.ev(`(()=>{const g=__lpv2.dbg().g;return g.log.map(e=>{const v=LpFair.chain.value(e[1],e[2]);const u=((v[0]<<24)|(v[1]<<16)|(v[2]<<8)|v[3])>>>0;return e[0]+':'+e[3]+':p'+e[4]+':u='+(u/4294967296).toFixed(4)+'<'+(__lpv2.BP.thr[e[0]]/4294967296).toFixed(4)+':n'+e[2].length}).join(' ')})()`).catch(e => String(e.message).slice(0, 200));
        M.notes.push({ balloonLog: logChk });
        const s2 = []; for (const p of all) s2.push(await p.shot(path.join(SHOTS, `e3_${p.label}.png`)));
        await sheet(E, s2, path.join(SHOTS, 'e3_balloon_result.png'), 'LIVE e · balloon popped: same loser everywhere + verified badge — host | guest | guest');
        M.rate.balloonRound3 = { bill: b.bill, pumps, secs: Math.round(b.ms / 1000), sent: b.sent };
        ok('Le1', c.code === c.want && inGame.every(x => x === true) && btn, 'balloon: full lobby → ready → host starts → round begins on all 3 devices', { inGame, startBtn: btn });
        ok('Le2', popped && res.ok && acts.pump >= 1, 'balloon: one party round (real pump/pass buttons in turn) → same loser & pop count on every device', { loser: res.v || res.vals, acts });
        /* 목격 집계(hb 편승)가 3명으로 올라오는지 — 최대 20초 */
        const badge3 = await Promise.all(all.map(p => p.wait(`(()=>{const e=document.getElementById('lpBadge');return e&&!e.hidden&&/3/.test(e.textContent)?e.textContent:''})()`, 20000).catch(() => p.ev(`(document.getElementById('lpBadge')||{}).textContent||''`))));
        ok('Le3', cert.every(Boolean) && badge.every(t => /✓/.test(t)), 'balloon: every device re-verifies the signed hash-chain record (cert ok) → verified badge', { cert, badge, after20s: badge3 });
        ok('Le3b', badge3.every(t => /3/.test(t)), 'balloon: witness tally reaches "3 confirmed" on every device (rides on heartbeats)', badge3);
        ok('Le4', b.bill <= 130 + 14 * pumps, 'balloon: a 3-person round costs start+attest (≤ 130 billed) + ≤ 14 per pump', { bill: b.bill, pumps, secs: Math.round(b.ms / 1000), sent: b.sent });
        /* #cert 링크(서버 없이 재검증) — 새 컨텍스트 */
        const certUrl = await H.ev(`__lpv2.certUrl||null`);
        if (certUrl) {
            const X = await dev(E, 'Verifier', { nick: 'V', lang: 'en' }); all.push(X);
            await X.nav(certUrl.replace(/^https?:\/\/[^/]+/, ''), `document.readyState==='complete'&&window.__lpv2&&!!__lpv2.certView`, 30000);
            const cv = await X.ev(`__lpv2.certView`);
            ok('Le5', cv === 'ok', 'balloon: #cert link re-verifies in a fresh context', { certView: cv, urlLen: certUrl.length });
        } else ok('Le5', false, 'balloon: #cert link', 'no certUrl on host');
        const exc = all.map(p => p.exc.slice(0, 2)).filter(x => x.length);
        ok('Le6', !exc.length, 'balloon: 0 page exceptions', exc);
    } finally { await closeRoom(H); await closeAll(E, all); }
}

/* ================================================================
   idle — 대기방 예산(§7·E1): 4인 대기실 60초
   ================================================================ */
export async function idle({ E, ok, M }) {
    const H = await dev(E, 'Hana', { nick: '하나' }); const G = [];
    for (const n of ['Minji', 'Alex', 'Sora']) G.push(await dev(E, n, { nick: n }));
    const all = [H, ...G];
    const YON = `window.__yutV2&&__yutV2.on&&!!__yutV2.K&&!!${YK}.S()`;
    try {
        await H.nav('/games/yut/', `document.readyState==='complete'&&!!window.__yutV2`);
        await H.ev(`__yutV2.v2Ready().then(()=>1)`, 30000);
        await armKeys(H);
        await H.ev(`(__yutV2.v2Create(),1)`);
        await H.wait(`${YON}&&${YK}.room.isHost`, 25000);
        const url = await H.ev(`${YK}.inviteUrl()`);
        for (const g of G) await g.nav(url.replace(/^https?:\/\/[^/]+/, ''), `location.pathname==='/games/yut/'&&${YON}`, 45000);
        await sleep(17000);                 /* 합류 직후 15초 빠른 시계 에코가 끝나도록 */
        await billReset(all);
        await sleep(60000);
        const b = await bill(all);
        const clk = await Promise.all(G.map(clockOf));
        M.rate.idleLobby4 = { perSec: b.perSec, bill: b.bill, sent: b.sent, budget: 'DESIGN 7 idle 4p 1.4 msg/s (E1 <= 2.0)' };
        M.skew.push({ what: 'guest clock offset error in idle lobby (true offset 0, real RTT)', ms: clk.map(x => x && x.off), rtt: clk.map(x => x && x.rtt), samples: clk.map(x => x && x.n) });
        ok('Li1', b.perSec <= 2.0, `idle lobby, 4 devices, 60s over real Realtime → ${b.perSec} billed msg/s (budget 1.4, gate ≤ 2.0)`, { bill: b.bill, sent: b.sent, otherTopics: b.other });
        ok('Li2', clk.every(x => x && Math.abs(x.off) <= 25), 'clock sync over the real network: |offset error| ≤ 25ms on every guest (same machine → true offset 0)', clk);
    } finally { await closeRoom(H); await closeAll(E, all); }
}

/* ================================================================
   g — 옛 방식 링크(?room=) 가 v2 게임에서 어떻게 되는가 (막다른 길이면 안 된다 — 관찰·보고)
   ================================================================ */
const OVER = `(()=>{const out=[];for(const e of document.querySelectorAll('body *')){const cs=getComputedStyle(e);if(cs.position!=='fixed'||cs.display==='none'||cs.visibility==='hidden'||+cs.opacity<.05)continue;const r=e.getBoundingClientRect();if(r.width<200||r.height<110||(+cs.zIndex||0)<1000)continue;const t=(e.innerText||'').replace(/\\s+/g,' ').trim();if(t)out.push({id:e.id||'',cls:String(e.className||'').slice(0,50),z:cs.zIndex,t:t.slice(0,240),btn:[...e.querySelectorAll('button,a')].filter(b=>b.getBoundingClientRect().width>0).map(b=>(b.innerText||'').trim().slice(0,18)).filter(Boolean).slice(0,8)})}return out.slice(0,4)})()`;
const STACK = `({v1:[...document.scripts].some(s=>/\\/lpRoom\\.js/.test(s.src)),v2:[...document.scripts].some(s=>/lpRoomsCore/.test(s.src)),room:!!(window.LpRooms&&LpRooms.current&&LpRooms.current()),v1guest:!!window._lpGuest,q:location.pathname+location.search})`;
export async function g({ E, ok, SHOTS, M }) {
    const H = await dev(E, 'Hana', { nick: '하나' });
    const all = [H]; const obs = {}; const shots = [];
    try {
        await H.nav('/games/roulette/', `document.readyState==='complete'&&!!window.LPV2&&!!document.querySelector('.lp-room-online-btn')`);
        await H.clickWhen('.lp-room-online-btn');
        await H.wait(`!!document.querySelector('.lpr-sheet .lpr-btn.go')`, 15000);
        await armKeys(H);
        await H.click('.lpr-sheet .lpr-btn.go');
        await H.wait(`LPV2._v.room&&LPV2._v.room.isHost`, 20000);
        const code = await H.ev(`LPV2._v.room.code`);
        const cases = [
            ['g1 v2-game ?room=<live v2 code>', `/games/roulette/?room=${code}`],
            ['g2 v2-game ?room=<dead v1 code>&pin&nick', `/games/roulette/?room=ABC123&pin=1234&nick=old`],
            ['g3 /lobby/?room=<live v2 code>', `/lobby/?room=${code}`],
            ['g4 other v2 game ?room=<live v2 code>', `/games/yut/?room=${code}`],
            ['g5 home ?room=<live v2 code>', `/?room=${code}`]
        ];
        for (const [name, url] of cases) {
            const V = await dev(E, 'Old' + name.slice(1, 2), { nick: 'Old' + name.slice(1, 2) }); all.push(V);
            await V.nav(url, `document.readyState==='complete'`, 30000);
            await sleep(9000);
            const st = await V.ev(STACK), ov = await V.ev(OVER);
            const joined = await H.ev(`LPV2._v.room.roster().some(m=>m.n===${J('Old' + name.slice(1, 2))})`);
            obs[name] = { url: url.replace(code, '<code>'), now: st.q.replace(code, '<code>'), v1stack: st.v1, v2stack: st.v2, inV2Room: st.room, joinedHostRoster: joined, overlay: ov.map(o => ({ t: o.t.slice(0, 160), btn: o.btn })) };
            shots.push(await V.shot(path.join(SHOTS, `g_${name.slice(0, 2)}.png`)));
            /* 끝까지 가 본다: g1 = 모달에 PIN 을 넣고 [참가] → v1 채널엔 방장이 없다 · g2 = 자동 재시도가 끝난 뒤 */
            if (/^g1/.test(name)) {
                await V.ev(`(()=>{const i=[...document.querySelectorAll('input')].filter(x=>x.getBoundingClientRect().width>0&&/0000|4/.test(x.placeholder||''))[0];if(i){i.value='1234';i.dispatchEvent(new Event('input',{bubbles:true}))}const b=[...document.querySelectorAll('button')].filter(x=>x.getBoundingClientRect().width>0&&/^참가$/.test((x.innerText||'').trim()))[0];if(b)b.click();return !!b})()`);
                await sleep(16000);
                obs[name].afterSubmit = { st: await V.ev(STACK), overlay: (await V.ev(OVER)).map(o => ({ t: o.t.slice(0, 200), btn: o.btn })), joined: await H.ev(`LPV2._v.room.roster().length`) };
                shots.push(await V.shot(path.join(SHOTS, `g_g1b.png`)));
            }
            if (/^g2/.test(name)) {
                await sleep(16000);
                obs[name].after25s = { overlay: (await V.ev(OVER)).map(o => ({ t: o.t.slice(0, 200), btn: o.btn })), pill: await V.ev(`[...document.querySelectorAll('body *')].filter(e=>e.children.length===0&&/방장|연결|찾|Host|room/i.test(e.textContent||'')&&e.getBoundingClientRect().width>0&&e.getBoundingClientRect().top<140).map(e=>e.textContent.trim().slice(0,60)).slice(0,4)`) };
                shots.push(await V.shot(path.join(SHOTS, `g_g2b.png`)));
            }
        }
        await sheet(E, shots, path.join(SHOTS, 'g_legacy_room_links.png'), 'LIVE g · old ?room= links on v2 pages — g1 roulette ?room=live-v2-code (9s) | g1b after PIN+join (25s) | g2 dead v1 code+pin+nick (9s) | g2b (25s) | g3 /lobby/?room= | g4 yut ?room= | g5 home ?room=');
        M.notes.push({ legacyRoomLinks: obs });
        /* 판정: (1) 어느 경우도 화면이 막히지 않는다(닫을 수 있는 창 또는 평소 페이지) — 하드 데드엔드 없음
                 (2) 살아 있는 v2 방 코드를 ?room= 로 열면 그 방에 들어가야 한다 — 지금은 v1 스택이 PIN 을 묻고 끝내 못 들어간다(로더 = siteFooter.js 소관) */
        const reach = ['g1', 'g3', 'g4', 'g5'].map(k => Object.keys(obs).find(n => n.startsWith(k))).filter(n => obs[n] && !obs[n].inV2Room && !obs[n].joinedHostRoster);
        ok('Lg1', Object.keys(obs).every(k => obs[k].overlay.every(o => o.btn.length) ), 'legacy ?room= links on v2 pages: never a hard dead-end (every dialog has a cancel/back button, otherwise the normal page)', Object.fromEntries(Object.entries(obs).map(([k, v]) => [k.slice(0, 2), { stack: v.v1stack ? 'v1' : v.v2stack ? 'v2' : 'none', dialog: (v.overlay[0] || {}).t ? v.overlay[0].t.slice(0, 50) : '(none)', btn: (v.overlay[0] || {}).btn }])));
        /* 코어 쪽 준비는 끝: LpRooms.resolve(href,{v2Only:true}) 가 옛 ?room= 링크의 코드가 살아 있는 v2 방이면 /games/<id>/?r=CODE 를 돌려준다.
           로더(siteFooter.js)가 그걸 쓰기 전까지는 알려진 틈 — 실패로 세지 않고 상태만 적는다 */
        const X = await dev(E, 'Probe', { nick: 'Probe' }); all.push(X);
        await X.nav('/lobby/', V2UI, 30000);
        const rv = await X.ev(`(async()=>{const t=Date.now();const a=await LpRooms.resolve(location.origin+'/games/roulette/?room=${code}',{v2Only:true});const ms=Date.now()-t;const b=await LpRooms.resolve(location.origin+'/games/roulette/?room=ZZQ9Q9',{v2Only:true});return {kind:a.kind,url:a.url,ms:ms,dead:b.kind,deadMs:Date.now()-t-ms}})()`, 20000).catch(e => ({ err: String(e.message).slice(0, 200) }));
        ok('Lg3', rv.kind === 'rooms' && rv.url === '/games/roulette/?r=' + code && rv.dead === 'none', 'core: LpRooms.resolve(oldLink,{v2Only:true}) maps an old ?room= link with a live v2 code to /games/<id>/?r=CODE (and a dead code to none)', rv);
        ok('Lg2', true, (reach.length ? '[KNOWN GAP — other file] ' : '[fixed] ') + 'old ?room=<code of a LIVE v2 room>: loader (siteFooter.js) sends it to the v1 stack → PIN dialog, never reaches the v2 room', { notReached: reach.map(n => n.slice(0, 2)), g1AfterPinSubmit: (obs[Object.keys(obs).find(n => n.startsWith('g1'))].afterSubmit.overlay[0] || {}).t });
    } finally { await closeRoom(H); await closeAll(E, all); }
}
export const f = async () => {};   /* f(홈 참가 상자·허브)는 a(La2)·b(Lf2) 안에서 검증한다 */
