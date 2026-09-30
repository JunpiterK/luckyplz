/* 레이스·브리지 시나리오 (DESIGN §10.2 R1~R8 · B1~B4) — P5
   실제 게임 페이지(/games/<id>/ = public/games/<id>/index.html)를 릴레이가 그대로 서빙한다.
   supabase 는 relay 의 Realtime 호환 심, 퀴즈 DB 는 relay.rpcMocks 의 메모리 목(운영 DB 에 쓰지 않는다).
   실행: node scripts/mp/race.mjs [race|games|bridges|all]  (MP_PORT 기본 8481, MP_ONLY=R1,R2…) */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { SCR } from './h.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const PUB = path.join(ROOT, 'public');
const J = JSON.stringify;
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const run1 = (only, id) => !only.length || only.includes(id);
export const SHOTS = process.env.MP_SHOTS || path.join(SCR, 'race_shots');

function pageFor(p) {
    const m = /^\/games\/([a-z0-9-]+)\/$/.exec(p);
    if (m && fs.existsSync(path.join(PUB, 'games', m[1], 'index.html'))) return path.join(PUB, 'games', m[1], 'index.html');
    if (p === '/lobby/' || /^\/r\/[^/]+\/?$/.test(p)) return path.join(PUB, 'lobby', 'index.html');
    return null;
}

/* 기기 1대 = 브라우저 컨텍스트 1개. o.skew = 이 기기 Date.now 어긋남(ms) — 시계 오프셋 보정 검증 */
export async function dev(E, label, o = {}) {
    const P = await E.page({ label });
    const c = P.c;
    await c.send('Network.setBlockedURLs', { urls: ['*supabase.co*', '*googletagmanager.com*', '*google-analytics.com*', '*doubleclick*', '*pagead2*', '*googlesyndication*', '*fonts.googleapis.com*', '*fonts.gstatic.com*', '*cdn.jsdelivr.net*', '*api.drand.sh*', '*drand.cloudflare.com*'] });
    await c.send('Emulation.setDeviceMetricsOverride', { width: o.w || 412, height: o.h || 915, deviceScaleFactor: 1, mobile: true });
    const kv = Object.assign({ luckyplz_lang: o.lang || 'ko', lp_profile: J({ nick: o.nick || label.toUpperCase(), av: label.charCodeAt(label.length - 1) % 16, v: 1 }) }, o.ls || {});
    const src = `try{if(!sessionStorage.getItem('__pv')){var o=${J(kv)};for(var k in o){localStorage.setItem(k,o[k])}sessionStorage.setItem('__pv','1')}}catch(e){}` +
        (o.skew ? `;(function(){var k=${o.skew|0},dn=Date.now;Date.now=function(){return dn.call(Date)+k};})();` : '') +
        /* 가시성 조작(백그라운드 흉내) — 캡처 단계 리스너까지 실제처럼 돈다 */
        `;window.__vis=function(h){try{Object.defineProperty(document,'visibilityState',{configurable:true,get:function(){return h?'hidden':'visible'}});Object.defineProperty(document,'hidden',{configurable:true,get:function(){return !!h}})}catch(e){}document.dispatchEvent(new Event('visibilitychange',{bubbles:true}))};`;
    await c.send('Page.addScriptToEvaluateOnNewDocument', { source: src });
    P.nav = async (u, cond, ms) => {
        await c.send('Page.navigate', { url: u.startsWith('http') ? u : E.base + u });
        await P.wait(cond || `document.readyState==='complete'`, ms || 20000);
    };
    P.shot = async (file) => { const r = await c.send('Page.captureScreenshot', { format: 'png' }); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, Buffer.from(r.data, 'base64')); return file; };
    P.click = (sel, txt) => P.ev(`(()=>{const e=[...document.querySelectorAll(${J(sel)})].find(x=>!${J(txt || '')}||x.textContent.includes(${J(txt || '')}));if(!e)return false;e.click();return true})()`);
    return P;
}
export async function closeAll(E, pages) { for (const p of pages) { try { await p.close(); } catch (_) {} try { await E.disposeContext(p.ctx); } catch (_) {} } }

const V2READY = `document.readyState==='complete'&&window.LpRoomsUI&&!/stub/.test(LpRoomsUI.version)&&window.LpRooms&&LpRooms.getAdapter&&!!LpRooms.getAdapter()`;
const RACEREADY = V2READY + `&&!!window.LpRoomsRace`;

/* 방장 방 만들기(UI 경로와 같은 LpRooms.create — UI 가 'room' 으로 붙인다) */
async function hostCreate(H, gid) {
    await H.nav(`/games/${gid}/?rooms=v2`, RACEREADY, 25000);
    const c = await H.ev(`LpRooms.create({gameId:${J(gid)}}).then(r=>({code:r.code,url:r.inviteUrl(),pid:r.me.pid}))`);
    await H.wait(`LpRoomsUI.room()&&LpRoomsUI.room().isHost`, 8000);
    return c;
}
function gameUrl(gid, c) { const k = c.url.split('#')[1] || ''; return `/games/${gid}/?r=${c.code}${k ? '#' + k : ''}`; }
async function guestJoin(G, gid, c, cond) {
    await G.nav(gameUrl(gid, c), (cond || RACEREADY) + `&&LpRoomsUI.room&&!!LpRoomsUI.room()&&LpRoomsUI.room().me.role!=='host'`, 30000);
    return G.ev(`({pid:LpRoomsUI.room().me.pid,role:LpRoomsUI.room().me.role})`);
}
const ready = (G) => G.ev(`LpRoomsUI.room().intent('ready',true).then(r=>r.ok)`);
async function allEq(pages, expr, ms = 15000) {
    const t0 = Date.now(); let vals;
    while (Date.now() - t0 < ms) {
        vals = await Promise.all(pages.map(p => p.ev(expr).catch(e => 'ERR ' + e.message)));
        if (vals.every(v => v === vals[0] && v !== null && v !== undefined && v !== '' && !String(v).startsWith('ERR'))) return { ok: true, v: vals[0] };
        await sleep(200);
    }
    return { ok: false, vals };
}
/* 방장 시작 — 대기실의 [▶ 시작] 버튼(실제 UI 경로). 없으면 API */
async function hostStartBtn(H) {
    await H.wait(`LpRoomsUI.room().canStart()`, 10000);
    const clicked = await H.click('.lpr-lobby .lpr-btn.go', '▶');
    if (!clicked) await H.ev(`LpRoomsRace.hostStart(LpRoomsUI.room())`);
    return clicked;
}
const INFO = `(()=>{const i=LpRoomsRace.info();return {st:i.st,heat:i.heat,seed:i.seed,t0:i.t0,skew:i.skew,ts:i.trueStart,g:i.g,fin:i.fin,card:i.card,chip:i.chip,res:i.game&&i.game.res?i.game.res.map(r=>r.p+':'+r.s).join(','):null,gst:i.game&&i.game.st,ent:i.game&&i.game.ent}})()`;

/* ================================================================
   R1~R5 — 테트로미노(레퍼런스 게임)로 커널 전체 흐름
   ================================================================ */
export async function race(ctx) {
    const { E, relay, ok, only } = ctx;
    relay.pageFor = pageFor;
    const gid = 'tetris';
    const H = await dev(E, 'rh'), G1 = await dev(E, 'rg1', { skew: 1500 }), G2 = await dev(E, 'rg2', { skew: -900 });
    const pages = [H, G1, G2];
    let G3 = null;
    try {
        const c = await hostCreate(H, gid);
        await guestJoin(G1, gid, c); await guestJoin(G2, gid, c);
        await H.wait(`LpRoomsUI.room().roster().length===3`, 8000);
        /* 판 길이를 하네스용으로 줄인다(방장 쪽 사양만 — 모든 기기는 S.game.dur 를 따른다) */
        await H.ev(`(()=>{const r=LpRooms.getAdapter().race;r.durFor=()=>16;r.durationS=16;return true})()`);
        await sleep(2500);   /* 시계 에코 표본(합류 직후 15초 가속) */
        await ready(G1); await ready(G2);
        const btn = await hostStartBtn(H);
        await Promise.all(pages.map(p => p.wait(`LpRoomsRace.info().st==='play'`, 20000)));
        const inf = await Promise.all(pages.map(p => p.ev(INFO)));
        /* R1 — 같은 시드 = 같은 판 */
        if (run1(only, 'R1')) {
            const pr = await Promise.all(pages.map(p => p.ev(`JSON.stringify(LpRooms.getAdapter().race.probe(100))`)));
            const seeds = inf.map(i => i.seed);
            ok('R1', pr.every(x => x === pr[0]) && JSON.parse(pr[0]).length === 100 && seeds.every(s => s === seeds[0] && /^[0-9a-f]{64}$/.test(s)),
                'same seed → identical first 100 pieces on 3 devices (tetris 7-bag seeded)', { seed: seeds[0].slice(0, 12), first12: JSON.parse(pr[0]).slice(0, 12).join(''), uiStartBtn: btn });
        }
        /* R2 — 동시 출발(기기 시계를 +1.5s/−0.9s 어긋나게 해도 방장 시계 t0 로 맞춘다) */
        if (run1(only, 'R2')) {
            const ts = inf.map(i => i.ts), spread = Math.max(...ts) - Math.min(...ts);
            ok('R2', spread <= 80 && inf.every(i => Math.abs(i.skew) <= 60), 'synchronized start: true start spread ≤ 80ms across skewed clocks', { spreadMs: Math.round(spread), localSkew: inf.map(i => Math.round(i.skew)) });
        }
        /* R3 — 순위판은 hb 편승: 플레이 중 hb 외 메시지 0 */
        if (run1(only, 'R3')) {
            const g1pid = await G1.ev('LpRoomsUI.room().me.pid');
            await sleep(1500);   /* 출발 순간의 phase(playing) 재전송이 끝난 뒤부터 잰다 */
            relay.resetStats();
            await G1.ev(`(score=4321,true)`);
            await H.wait(`((LpRoomsRace.info().live||{})[${J(g1pid)}]||{}).g===4321`, 12000).catch(() => null);
            await G2.wait(`(()=>{const b=LpRoomsRace.info().board;return !!(b&&b[1]&&b[1].some(r=>r[0]===${J(g1pid)}&&r[1]===4321))})()`, 9000).catch(() => null);
            const snap = relay.snapshot();
            const extra = Object.keys(snap.byEvent).filter(k => !/^(h|g):hb$/.test(k));
            const hostSees = await H.ev(`(LpRoomsRace.info().live||{})[${J(g1pid)}]`);
            const g2Board = await G2.ev(`JSON.stringify(LpRoomsRace.info().board)`);
            const chip = await G2.ev(`LpRoomsRace.info().chip`);
            ok('R3', extra.length === 0 && hostSees && hostSees.g === 4321 && /4321/.test(g2Board) && /4,321|4321/.test(chip),
                'live standings ride on heartbeats: guest sc → host LIVE → host bd → other guest chip, 0 extra messages', { events: snap.byEvent, windowMs: snap.ms, g2chip: chip });
        }
        /* R4 — 백그라운드 = 그 순간 기록으로 종료 */
        if (run1(only, 'R4')) {
            const before = await G2.ev(`LpRooms.getAdapter().race.progress()`);
            await G2.ev(`__vis(true)`);
            await sleep(400);
            const r4 = await G2.ev(`({i:LpRoomsRace.info(),over:!!gameOverFlag,ap:!!(window.LpAutoPause&&LpAutoPause.isShowing())})`);
            await G2.ev(`__vis(false)`); await sleep(300);
            const ap2 = await G2.ev(`!!(window.LpAutoPause&&LpAutoPause.isShowing())`);
            const g2pid = await G2.ev('LpRoomsUI.room().me.pid');
            const hostFin = await H.wait(`(LpRoomsRace.info().live||{})[${J(g2pid)}]&&LpRoomsRace.info().live[${J(g2pid)}].a===0`, 6000).then(() => true).catch(() => false);
            ok('R4', r4.i.st === 'done' && r4.i.fin && r4.i.fin.s === 'bg' && r4.i.fin.v === before && r4.over && !r4.ap && !ap2 && hostFin,
                'background ends the run at that moment (final sent, game over, no auto-pause dialog)', { fin: r4.i.fin, gameOver: r4.over, autoPauseDlg: r4.ap || ap2, hostGotFinal: hostFin });
        }
        /* R5 — 늦참 → 다음 판 */
        if (run1(only, 'R5') || run1(only, 'R6')) {
            G3 = await dev(E, 'rg3'); pages.push(G3);
            const j3 = await guestJoin(G3, gid, c);
            await sleep(600);
            const i3 = await G3.ev(`({i:LpRoomsRace.info(),role:LpRoomsUI.room().me.role})`);
            /* 판 종료(16초) → 결과 카드 */
            await Promise.all([H, G1, G2, G3].map(p => p.wait(`LpRoomsUI.room().state().phase==='result'`, 40000)));
            await sleep(700);
            const res = await Promise.all([H, G1, G2, G3].map(p => p.ev(INFO)));
            fs.mkdirSync(SHOTS, { recursive: true });
            await H.shot(path.join(SHOTS, 'tetris_result_host.png')); await G2.shot(path.join(SHOTS, 'tetris_result_guest.png'));
            const resOk = res.every(r => r.res === res[0].res && r.gst === 'res') && res[0].res.split(',').length === 3 && res.slice(0, 3).every(r => r.card);
            /* 한 판 더 = toLobby → 늦참자 좌석 */
            await H.click('.lprc-ft .pri');
            await G3.wait(`LpRoomsUI.room().me.role==='player'&&LpRoomsUI.room().state().phase==='lobby'`, 8000);
            await ready(G1); await ready(G2); await ready(G3);
            await hostStartBtn(H);
            await Promise.all([H, G1, G2, G3].map(p => p.wait(`LpRoomsRace.info().st==='play'&&LpRoomsRace.info().heat===2`, 20000)));
            const h2 = await Promise.all([H, G1, G2, G3].map(p => p.ev(INFO)));
            const pr2 = await Promise.all([H, G3].map(p => p.ev(`JSON.stringify(LpRooms.getAdapter().race.probe(40))`)));
            ok('R5', j3.role === 'spec' && i3.i.st === null && /👀/.test(i3.i.chip) && resOk && h2.every(i => i.heat === 2 && i.ent.length === 4) && pr2[0] === pr2[1] && h2[0].seed !== inf[0].seed,
                'late joiner watches heat 1 (spec + 👀 chip), result card on all, [↻] → lobby seats them, heat 2 has 4 entrants with a fresh seed', { late: { role: j3.role, chip: i3.i.chip }, res1: res[0].res, heat2ent: h2[0].ent.length, newSeed: h2[0].seed.slice(0, 10) });
            if (run1(only, 'R6')) {
                /* R6 — 방장이 판 도중 새로고침: 커널이 상태에서 판을 되살리고(종료 처리) 게스트는 계속, 결과 확정 */
                await H.nav(`/games/${gid}/?r=${c.code}`, RACEREADY + `&&LpRoomsUI.room&&!!LpRoomsUI.room()&&LpRoomsUI.room().isHost`, 25000);
                const hi = await H.ev(INFO);
                await Promise.all([H, G1, G2, G3].map(p => p.wait(`LpRoomsUI.room().state().phase==='result'`, 45000)));
                const r6 = await Promise.all([H, G1, G2, G3].map(p => p.ev(INFO)));
                ok('R6', hi.st === 'done' && hi.fin && hi.fin.s === 'leave' && r6.every(r => r.res === r6[0].res) && r6[0].res.split(',').length === 4,
                    'host reload mid-heat: own run closed as "leave", heat still finalizes for all 4', { hostAfterReload: hi.fin, res: r6[0].res });
            }
        }
        console.log('exc', pages.map(p => p.exc.slice(0, 3)));
    } finally { await closeAll(E, pages); }
}

/* ================================================================
   R7·R8 — 게임별 훅 (6종): 2대, 같은 시드 판(probe 100), 진행값·종료(bg)·결과 카드
   ================================================================ */
const GAMES = [
    { id: 'tetris', note: '7-bag pieces' },
    { id: 'mahjong-solitaire', note: 'tile faces' },
    { id: 'brick', note: 'stage bricks + power-up types' },
    { id: 'burger', note: 'order ingredients' },
    { id: 'starship-lander', note: 'wind phases + terrain' },
    { id: 'lucky-merge', note: 'drop tiers' }
];
export async function games(ctx) {
    const { E, relay, ok, only } = ctx;
    relay.pageFor = pageFor;
    for (const gm of GAMES) {
        if (only.length && !only.includes(gm.id) && !only.includes('R7') && !only.includes('R8')) continue;
        const H = await dev(E, 'h-' + gm.id.slice(0, 4)), G = await dev(E, 'g-' + gm.id.slice(0, 4));
        try {
            const c = await hostCreate(H, gm.id);
            await guestJoin(G, gm.id, c);
            await H.ev(`(()=>{const r=LpRooms.getAdapter().race;r.durFor=()=>12;r.durationS=12;return true})()`);
            await sleep(1200);
            await ready(G);
            await hostStartBtn(H);
            await Promise.all([H, G].map(p => p.wait(`LpRoomsRace.info().st==='play'`, 20000)));
            const pr = await Promise.all([H, G].map(p => p.ev(`JSON.stringify(LpRooms.getAdapter().race.probe(100))`)));
            const n = JSON.parse(pr[0]).length;
            ok('R7:' + gm.id, pr[0] === pr[1] && n >= 40, gm.id + ': same seed → identical first ' + n + ' ' + gm.note + ' (host vs guest)', { n, head: JSON.parse(pr[0]).slice(0, 6) });
            await sleep(600);
            await H.shot(path.join(SHOTS, gm.id + '_play.png'));
            /* 게스트 백그라운드 → 즉시 종료(게임의 over()가 참, 자동정지 창 없음) · 방장은 시간 종료 */
            await G.ev(`__vis(true)`); await sleep(300);
            const gi = await G.ev(`({i:LpRoomsRace.info(),over:LpRooms.getAdapter().race.over()||!!(window.LpAutoPause&&!LpAutoPause.anyActive()),hasAP:!!window.LpAutoPause,ap:!!(window.LpAutoPause&&LpAutoPause.isShowing())})`);
            await G.ev(`__vis(false)`);
            await Promise.all([H, G].map(p => p.wait(`LpRoomsUI.room().state().phase==='result'&&LpRoomsRace.info().card`, 40000)));
            await sleep(500);
            const rs = await Promise.all([H, G].map(p => p.ev(INFO)));
            await H.shot(path.join(SHOTS, gm.id + '_result.png'));
            ok('R8:' + gm.id, gi.i.st === 'done' && gi.i.fin.s === 'bg' && gi.over && !gi.ap && rs[0].res === rs[1].res && rs[0].res.split(',').length === 2 && /time|fin|out/.test(rs[0].res),
                gm.id + ': hooks progress/over/stop/final → bg end (game no longer active), host time-up, same result card on both', { guest: gi.i.fin, stopped: gi.over, hasAutoPause: gi.hasAP, res: rs[0].res });
            console.log('exc', gm.id, H.exc.slice(0, 3), G.exc.slice(0, 3));
        } catch (e) { ok('R7:' + gm.id, false, gm.id + ' crashed', String(e.message || e).slice(0, 400)); }
        finally { await closeAll(E, [H, G]); }
    }
}

/* ================================================================
   B1~B4 — 퀴즈 브리지(목 RPC) · 숫자 코드 resolve · SZX 브리지 · SZX 단독 회귀
   ================================================================ */
function quizMock(relay) {
    const rooms = {}, calls = [];
    relay.rpcMocks.qlive_create = (a) => {
        const code = String(100000 + Object.keys(rooms).length * 7 + 424242 % 800000).slice(0, 6);
        rooms[code] = { code, hostKey: a.p_host_key, players: {}, qs: a.p_questions || [], settings: a.p_settings || {}, rev: 1 };
        calls.push(['create', code, (a.p_questions || []).length]);
        return { ok: true, code };
    };
    relay.rpcMocks.qlive_join = (a) => {
        const r = rooms[a.p_code]; calls.push(['join', a.p_code, a.p_nick]);
        if (!r) return { ok: false, err: 'no_room' };
        r.players[a.p_pid] = { nick: a.p_nick, avatar: a.p_avatar, score: 0 }; r.rev++;
        return { ok: true };
    };
    relay.rpcMocks.qlive_state = (a) => {
        const r = rooms[a.p_code];
        if (!r) return { ok: false, err: 'no_room' };
        const me = a.p_pid && r.players[a.p_pid] ? Object.assign({ choice: null }, r.players[a.p_pid]) : null;
        const lobby = Object.values(r.players).map(p => ({ nick: p.nick, avatar: p.avatar }));
        return { ok: true, rev: r.rev, phase: 'lobby', q: 0, total: r.qs.length, now: Date.now(), is_host: a.p_host_key === r.hostKey, host_online: true, me, lobby, count: lobby.length, settings: r.settings, top: [], locked: false, paused: false };
    };
    relay.rpcMocks.qlive_host = () => ({ ok: true });
    return { rooms, calls, off() { ['qlive_create', 'qlive_join', 'qlive_state', 'qlive_host'].forEach(k => delete relay.rpcMocks[k]); } };
}
export async function bridges(ctx) {
    const { E, relay, ok, only } = ctx;
    relay.pageFor = pageFor;
    /* B1·B2 — 퀴즈 */
    if (run1(only, 'B1') || run1(only, 'B2')) {
        const Q = quizMock(relay);
        const H = await dev(E, 'qh', { nick: 'QHOST' }), G = await dev(E, 'qg', { nick: 'QUIZKID' });
        try {
            await H.nav('/games/quiz/?rooms=v2', V2READY, 25000);
            const c = await H.ev(`LpRooms.create({gameId:'quiz'}).then(r=>({code:r.code,url:r.inviteUrl()}))`);
            await G.nav(gameUrl('quiz', c), V2READY + `&&LpRoomsUI.room&&!!LpRoomsUI.room()`, 25000);
            await G.ev(`LpRoomsUI.room().intent('ready',true)`);
            await H.wait(`LpRoomsUI.room().roster().length===2&&LpRoomsUI.room().canStart()`, 8000);
            await H.click('.lpr-lobby .lpr-btn.go', '▶');
            await H.wait(`!!document.querySelector('#qopen')`, 10000);
            await H.shot(path.join(SHOTS, 'quiz_host_setup.png'));
            await H.click('#qopen');
            await H.wait(`QLIVE.S.role==='host'&&!!QLIVE.S.code`, 15000);
            const qcode = await H.ev('QLIVE.S.code');
            await G.wait(`QLIVE.S.role==='player'&&QLIVE.S.code===${J(qcode)}`, 15000);
            await H.wait(`(QLIVE.S.st&&QLIVE.S.st.lobby||[]).some(x=>x.nick==='QUIZKID')`, 12000).catch(() => null);
            const gs = await G.ev(`({role:QLIVE.S.role,code:QLIVE.S.code,me:QLIVE.S.st&&QLIVE.S.st.me&&QLIVE.S.st.me.nick,inQuiz:document.body.classList.contains('qlive-in'),hud:!!document.querySelector('.lpr-hud')})`);
            const hs = await H.ev(`({g:LpRoomsUI.room().state().game,lobbyNames:(QLIVE.S.st&&QLIVE.S.st.lobby||[]).map(x=>x.nick)})`);
            await G.shot(path.join(SHOTS, 'quiz_guest_autojoined.png'));
            ok('B1', gs.code === qcode && gs.role === 'player' && gs.me === 'QUIZKID' && gs.inQuiz && gs.hud && hs.g && hs.g.qcode === qcode && hs.lobbyNames.includes('QUIZKID') && Q.calls.some(x => x[0] === 'join' && x[2] === 'QUIZKID'),
                'Rooms → quiz: host opens quiz as usual, member auto-joins with Rooms nick (mock RPC, no prod DB)', { qcode, guest: gs, calls: Q.calls });
            /* B2 — 숫자 코드 resolve → 퀴즈 */
            const rv = await G.ev(`LpRooms.resolve(${J(qcode)}).then(x=>({kind:x.kind,url:x.url}))`);
            const rv2 = await G.ev(`LpRooms.resolve('999999').then(x=>({kind:x.kind}))`);
            ok('B2', rv.kind === 'qlive' && /\/games\/quiz\/\?c=/.test(rv.url || '') && rv2.kind !== 'qlive', 'numeric code resolves to the quiz (unknown code does not)', { rv, rv2 });
            console.log('exc', H.exc.slice(0, 3), G.exc.slice(0, 3));
        } catch (e) { ok('B1', false, 'quiz bridge crashed', String(e.message || e).slice(0, 500)); }
        finally { Q.off(); await closeAll(E, [H, G]); }
    }
    /* B3 — Rooms → SZX 조용한 참가 · 같은 시드 · 결과 반환 */
    if (run1(only, 'B3')) {
        const H = await dev(E, 'zh', { nick: 'ZHOST' }), G = await dev(E, 'zg', { nick: 'ZGUEST' });
        try {
            await H.nav('/games/dodge/?rooms=v2', V2READY, 40000);
            const c = await H.ev(`LpRooms.create({gameId:'dodge'}).then(r=>({code:r.code,url:r.inviteUrl()}))`);
            await G.nav(gameUrl('dodge', c), V2READY + `&&LpRoomsUI.room&&!!LpRoomsUI.room()`, 40000);
            await G.ev(`LpRoomsUI.room().intent('ready',true)`);
            await H.wait(`LpRoomsUI.room().roster().length===2&&LpRoomsUI.room().canStart()`, 8000);
            await H.click('.lpr-lobby .lpr-btn.go', '▶');
            await Promise.all([H, G].map(p => p.wait(`SZX._R.code&&SZX._R.joined`, 15000)));
            const panelOpen = await G.ev(`!!(document.getElementById('szxPanel')&&document.getElementById('szxPanel').classList.contains('on'))`);
            await Promise.all([H, G].map(p => p.wait(`SZX.racing()`, 25000)));
            const zs = await Promise.all([H, G].map(p => p.ev(`({code:SZX._R.code,seed:SZX._R.seed,round:SZX._R.round,n:Object.keys(SZX._R.members).length,g:LpRoomsUI.room().state().game})`)));
            await sleep(2500);
            await H.shot(path.join(SHOTS, 'szx_bridge_flight.png'));
            /* 둘 다 격추 → SZX 가 판을 닫고 → 방장 브리지가 Rooms 결과로 */
            await Promise.all([H, G].map(p => p.ev(`(typeof triggerGameOver==='function'?(triggerGameOver('hit'),true):false)`)));
            await Promise.all([H, G].map(p => p.wait(`LpRoomsUI.room().state().phase==='result'`, 30000)));
            const res = await Promise.all([H, G].map(p => p.ev(`JSON.stringify(LpRoomsUI.room().state().game.res)`)));
            const g0 = zs[0].g;
            ok('B3', zs[0].code === g0.code6 && zs[1].code === g0.code6 && zs[0].seed === zs[1].seed && zs[0].seed === g0.s && !panelOpen && res[0] === res[1] && JSON.parse(res[0]).length === 2,
                'Rooms lobby → SZX.joinSilent (no panel) → goSilent(fair seed) same course → onFinish → Rooms result', { code6: g0.code6, seed: g0.s, szxSeeds: zs.map(z => z.seed), rows: JSON.parse(res[0]).map(r => r.n + ':' + r.s) });
            console.log('exc', H.exc.slice(0, 3), G.exc.slice(0, 3));
        } catch (e) { ok('B3', false, 'szx bridge crashed', String(e.message || e).slice(0, 500)); }
        finally { await closeAll(E, [H, G]); }
    }
    /* B4 — SZX 단독(패널·6자리 코드·?race= 링크) 회귀: Rooms 없이 기존 그대로 */
    if (run1(only, 'B4')) {
        const H = await dev(E, 'sh', { ls: { szx_nick: 'SOLOH' } }), G = await dev(E, 'sg', { ls: { szx_nick: 'SOLOG' } });
        try {
            await H.nav('/games/dodge/', `document.readyState==='complete'&&!!window.SZX&&!!document.getElementById('szxRaceBtn')`, 40000);
            const v1 = await H.ev(`({rooms:!!window.LpRoomsUI,q:Array.isArray(window.LpRoomsQ)?LpRoomsQ.length:typeof window.LpRoomsQ,fns:['joinSilent','goSilent','onFinish','leaveSilent'].every(k=>typeof SZX[k]==='function')})`);
            await H.click('#szxRaceBtn');
            await H.wait(`!!document.getElementById('szxNick')`, 5000);
            await H.ev(`(document.getElementById('szxNick').value='SOLOH',true)`);
            await H.click('#szxPanel [data-a="create"]');
            await H.wait(`SZX._R.joined&&SZX._R.code.length===6`, 12000);
            const code = await H.ev('SZX._R.code');
            await G.nav('/games/dodge/?race=' + code, `document.readyState==='complete'&&!!window.SZX&&SZX._R.joined`, 40000);
            await H.wait(`Object.keys(SZX._R.members).length===2`, 12000);
            await H.click('#szxPanel [data-a="go"]');
            await Promise.all([H, G].map(p => p.wait(`SZX.racing()`, 20000)));
            const ss = await Promise.all([H, G].map(p => p.ev(`({seed:SZX._R.seed,round:SZX._R.round,panel:document.getElementById('szxPanel').classList.contains('on')})`)));
            ok('B4', !v1.rooms && v1.fns && ss[0].seed === ss[1].seed && ss[0].round === 1 && !ss[0].panel,
                'standalone SZX (panel · 6-digit code · ?race= link · go) unchanged without Rooms', { v1, ss, code });
            console.log('exc', H.exc.slice(0, 3), G.exc.slice(0, 3));
        } catch (e) { ok('B4', false, 'szx standalone crashed', String(e.message || e).slice(0, 500)); }
        finally { await closeAll(E, [H, G]); }
    }
}
