/* P5 성능 게이트 — 아케이드 6종 프레임 JS 시간 p95 (CPU 4x 스로틀)
   base = 기준 커밋의 게임 HTML(git show), new = 작업 트리. 같은 릴레이·같은 Edge 에서 번갈아 잰다(base,new,base,new).
   + race = new 페이지를 v2 레이스 판 도중에 잰다(커널 250ms 폴링·칩·hb 편승 포함).
   합격: new·race 의 p95 가 base 보다 0.5ms 넘게 나빠지지 않을 것.
   판정 = 회차(기본 5, 번갈아) 프레임을 모두 합친 p95 비교(pooled). 프레임이 적은(변할 때만 그리는) 게임은 판정 제외
   PERF_NOCHIP=1 = 레이스 측정 때 칩·HUD 를 숨겨 커널 DOM 비용을 떼어 본다(진단용)
   node scripts/mp/perf_race.mjs [--base <commit>] [--secs 5] [--rounds 5] [--games tetris,brick] [--no-race] */
import { startRelay } from './relay.mjs';
import { Edge, SCR } from './h.mjs';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const A = process.argv.slice(2);
const arg = (k, d) => { const i = A.indexOf('--' + k); return i >= 0 ? A[i + 1] : d; };
const BASE = arg('base', '6a3c43fce68');
const SECS = +arg("secs", 5);
const RATE = +arg('rate', 4);
const NORACE = A.includes('--no-race');
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const J = JSON.stringify;
const GAMES = {
    'tetris': `startGame()`,
    'mahjong-solitaire': `__mjs.startGame('butterfly')`,
    'brick': `document.getElementById('btnStart').click()`,
    'burger': `startGame()`,
    'starship-lander': `document.getElementById('btnStart').click()`,
    'lucky-merge': `startGame()`
};
const want = (arg('games', '') || Object.keys(GAMES).join(',')).split(',');

/* 릴레이는 저장소 안 파일만 서빙한다 → 기준 HTML 은 임시로 scripts/mp/.perf_base/ 에(끝나면 지운다) */
const baseDir = path.join(HERE, '.perf_base');
fs.mkdirSync(baseDir, { recursive: true });
for (const g of want) {
    const f = path.join(baseDir, g + '.html');
    fs.writeFileSync(f, execFileSync('git', ['-C', ROOT, 'show', BASE + ':public/games/' + g + '/index.html']));
}
let MODE = 'new';
function pageFor(p) {
    const m = /^\/games\/([a-z0-9-]+)\/$/.exec(p);
    if (!m || !GAMES[m[1]]) return null;
    return MODE === 'base' ? path.join(baseDir, m[1] + '.html') : path.join(ROOT, 'public', 'games', m[1], 'index.html');
}
/* rAF 콜백마다 JS 시간 기록 (페이지 스크립트보다 먼저) */
const PRE = `(function(){var raf=window.requestAnimationFrame.bind(window);window.__ft=[];window.__ftOn=false;
window.requestAnimationFrame=function(cb){return raf(function(ts){var t0=performance.now();try{cb(ts)}finally{if(window.__ftOn)window.__ft.push(performance.now()-t0)}})};})();`;
const BLOCK = ['*supabase.co*', '*googletagmanager.com*', '*google-analytics.com*', '*doubleclick*', '*pagead2*', '*googlesyndication*', '*fonts.googleapis.com*', '*fonts.gstatic.com*', '*cdn.jsdelivr.net*'];

async function mkPage(E, label, ls) {
    const P = await E.page({ label });
    await P.c.send('Network.setBlockedURLs', { urls: BLOCK });
    await P.c.send('Page.addScriptToEvaluateOnNewDocument', { source: PRE + `try{if(!sessionStorage.getItem('__pv')){var o=${J(Object.assign({ luckyplz_lang: 'ko' }, ls || {}))};for(var k in o)localStorage.setItem(k,o[k]);sessionStorage.setItem('__pv','1')}}catch(e){}` });
    P.nav = async (u, cond, ms) => { await P.c.send('Page.navigate', { url: E.base + u }); await P.wait(cond || `document.readyState==='complete'`, ms || 45000); };
    return P;
}
function stats(a) {
    const s = a.slice().sort((x, y) => x - y), q = (p) => s.length ? s[Math.min(s.length - 1, Math.floor(p * s.length))] : 0;
    return { n: s.length, p50: +q(0.5).toFixed(3), p95: +q(0.95).toFixed(3), p99: +q(0.99).toFixed(3) };
}
async function measure(P) {
    await P.c.send('Emulation.setCPUThrottlingRate', { rate: RATE });
    await sleep(1000);
    await P.ev(`(window.__ft=[],window.__ftOn=true)`);
    await sleep(SECS * 1000);
    const ft = await P.ev(`(window.__ftOn=false,window.__ft)`);
    await P.c.send('Emulation.setCPUThrottlingRate', { rate: 1 });
    const st = stats(ft); st.ft = ft; return st;
}
async function solo(E, g, mode) { try { return await solo1(E, g, mode); } catch (e) { console.log('retry', g, mode, String(e.message).slice(0, 120)); return solo1(E, g, mode); } }
async function solo1(E, g, mode) {
    MODE = mode;
    const P = await mkPage(E, mode + '-' + g);
    try {
        await P.nav(`/games/${g}/`);
        await P.wait(`(()=>{try{${GAMES[g]};return true}catch(e){return false}})()`, 20000, 250);
        const st = await measure(P);
        st.exc = P.exc.slice(0, 3);
        return st;
    } finally { try { await P.close(); } catch (_) {} try { await E.disposeContext(P.ctx); } catch (_) {} }
}
async function raced(E, g) { try { return await raced1(E, g); } catch (e) { console.log('retry race', g, String(e.message).slice(0, 120)); return raced1(E, g); } }
async function raced1(E, g) {
    MODE = 'new';
    const H = await mkPage(E, 'ph-' + g, { lp_profile: J({ nick: 'PH', av: 1, v: 1 }) }), G = await mkPage(E, 'pg-' + g, { lp_profile: J({ nick: 'PG', av: 2, v: 1 }) });
    const RR = `document.readyState==='complete'&&window.LpRoomsUI&&!!window.LpRoomsRace`;
    try {
        await H.nav(`/games/${g}/?rooms=v2`, RR);
        const c = await H.ev(`LpRooms.create({gameId:${J(g)}}).then(r=>({code:r.code,url:r.inviteUrl()}))`);
        await G.nav(`/games/${g}/?r=${c.code}#${c.url.split('#')[1]}`, RR + `&&!!LpRoomsUI.room()`, 30000);
        await H.ev(`(()=>{const r=LpRooms.getAdapter().race;r.durFor=()=>60;r.durationS=60;return true})()`);
        await G.ev(`LpRoomsUI.room().intent('ready',true)`);
        await H.wait(`LpRoomsUI.room().canStart()`, 8000);
        await H.ev(`LpRoomsRace.hostStart(LpRoomsUI.room())`);
        await H.wait(`LpRoomsRace.info().st==='play'`, 20000);
        /* 같은 기계에서 게스트 판까지 돌면 CPU 를 나눠 써서 불공정 — 게스트 판은 바로 끝낸다(방장만 레이스 중) */
        await G.wait(`LpRoomsRace.info().st==='play'`, 20000).catch(() => null);
        await G.ev(`(LpRoomsRace._t.endRun('bg'),true)`).catch(() => null);
        if (process.env.PERF_NOCHIP) await H.ev(`(()=>{const st=document.createElement('style');st.textContent='.lprc-chip,.lpr-hud{display:none!important}';document.head.appendChild(st);return true})()`);
        return await measure(H);
    } finally { for (const P of [H, G]) { try { await P.close(); } catch (_) {} try { await E.disposeContext(P.ctx); } catch (_) {} } }
}

async function main() {
    const relay = await startRelay({ port: +(process.env.MP_PORT || 8481) });
    relay.pageFor = pageFor;
    const E = new Edge(relay.base);
    const rows = [];
    let fail = 0;
    try {
        await E.start();
        for (const g of want) {
            const ROUNDS = +arg('rounds', 5), B = [], N = [], RC = [];
            for (let k = 0; k < ROUNDS; k++) { B.push(await solo(E, g, 'base')); N.push(await solo(E, g, 'new')); if (!NORACE && k < 3) RC.push(await raced(E, g)); }
            const med = (xs) => { const a = xs.map(x => x.p95).sort((x, y) => x - y); return a.length ? a[Math.floor((a.length - 1) / 2)] : 0; };
            /* 판정 = 회차별 p95 의 최솟값 — 공유 기계의 다른 부하는 프레임 시간을 더하기만 하므로 최솟값이 그 코드 자체의 비용에 가장 가깝다(중앙값은 참고) */
            const mn = (xs) => Math.min(...xs.map(x => x.p95));
            /* 판정 = 모든 회차 프레임을 합친 p95(pooled). 한 번 운 좋게 가벼웠던 회차에 끌려가지 않는다. 프레임이 60개 미만(변할 때만 그리는 게임)은 판정 제외 */
            const pool = (xs) => stats([].concat(...xs.map(x => x.ft || [])));
            const PB = pool(B), PN = pool(N), PR = RC.length ? pool(RC) : null;
            const bp = PB.p95, np = PN.p95, rp = PR ? PR.p95 : null;
            const idle = PB.n < 60 * B.length;
            const pass = idle || (np - bp <= 0.5 && (rp == null || rp - bp <= 0.5));
            const bexc = [].concat(...B.map(x => x.exc || []));
            const exc = [].concat(...N.map(x => x.exc || [])).filter(x => !bexc.includes(x));   /* 기준에도 있던 예외는 제외 */
            const ok2 = pass && !exc.length;
            if (!ok2) fail++;
            rows.push({ g, base: B.map(x => x.p95), new: N.map(x => x.p95), race: RC.length ? RC.map(x => x.p95) : null, pooled: [bp, np, rp], idle, min: [mn(B), mn(N), RC.length ? mn(RC) : null], med: [med(B), med(N), RC.length ? med(RC) : null],
                frames: [B[0].n, N[0].n, RC.length ? RC[0].n : 0], dNew: +(np - bp).toFixed(3), dRace: rp == null ? null : +(rp - bp).toFixed(3), exc, pass: ok2 });
            console.log(JSON.stringify(rows[rows.length - 1]));
        }
    } finally { await E.stop(); await relay.stop(); try { fs.rmSync(baseDir, { recursive: true, force: true }); } catch (_) {} }
    console.log('\n| 게임 | pooled p95 base/new/race (ms) | Δnew | Δrace | 회차 중앙값 base/new/race | 프레임/회 | 판정 |\n|---|---|---|---|---|---|---|');
    rows.forEach(r => console.log(`| ${r.g} | ${r.pooled.map(x => x ?? '-').join(' / ')} | ${r.dNew} | ${r.dRace ?? '-'} | ${r.med.map(x => x ?? '-').join(' / ')} | ${r.frames.join('/')} | ${r.idle ? 'n/a(변할 때만 그림)' : r.pass ? 'PASS' : '**FAIL**'} |`));
    console.log(`CPU ${RATE}x · ${SECS}s/측정 · 기준 ${BASE}`);
    process.exit(fail ? 1 : 0);
}
main().catch(e => { console.error(e); process.exit(2); });
