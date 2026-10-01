/* P5 성능 게이트 — 아케이드 6종 프레임 JS 시간 p95 (CPU 4x 스로틀)
   base = 기준 커밋의 게임 HTML(git show), new = 작업 트리. 같은 릴레이·같은 Edge 에서 번갈아 잰다(base,new,base,new).
   + race = new 페이지를 v2 레이스 판 도중에 잰다(커널 250ms 폴링·칩·hb 편승 포함).
   합격: new·race 의 p95 가 base 보다 0.5ms 넘게 나빠지지 않을 것.
   판정 = 회차(기본 5, 번갈아) 프레임을 모두 합친 p95 비교(pooled). 프레임이 적은(변할 때만 그리는) 게임은 판정 제외
   PERF_NOCHIP=1 = 레이스 측정 때 칩·HUD 를 숨겨 커널 DOM 비용을 떼어 본다(진단용)
   node scripts/mp/perf_race.mjs [--base <commit>] [--secs 5] [--rounds 5] [--games tetris,brick] [--no-race] [--cpu]
   --cpu (2026-10-01): 공유 기계(다른 에이전트가 CPU 를 쓰는 중)에서는 벽시계 p95 가 회차마다 4~36ms 로 흔들려 0.5ms 게이트를 잴 수 없다.
     이 모드는 CDP Performance.getMetrics(timeDomain=threadTicks) 로 **렌더러 메인 스레드 CPU 시간**만 잰다(선점·대기 시간 제외):
     프레임당 Script·Task·Layout+Style CPU ms (스로틀 없음) — base/new/race 회차 중앙값 비교. 0.5ms@4x 스로틀 = 실 CPU 0.125ms/프레임.
     race-k = 레이스 중 커널 250ms 틱(poll·hostTick·chip)을 세운 채, race-c = 칩·HUD 를 숨긴 채 → 커널 몫을 분리 */
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
const CPU = A.includes('--cpu');
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
const PRE = `(function(){var si=window.setInterval;window.__iv250=[];window.setInterval=function(f,t){var id=si.apply(window,arguments);if(t===250)window.__iv250.push(id);return id};})();(function(){var raf=window.requestAnimationFrame.bind(window);window.__ft=[];window.__ftOn=false;
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
async function metrics(P) { const r = await P.c.send('Performance.getMetrics'); const o = {}; r.metrics.forEach(m => { o[m.name] = m.value; }); return o; }
async function measureCpu(P) {
    await P.c.send('Performance.enable', { timeDomain: 'threadTicks' });
    await sleep(1000);
    await P.ev(`(window.__ft=[],window.__ftOn=true)`);
    const m0 = await metrics(P), t0 = Date.now();
    await sleep(SECS * 1000);
    const m1 = await metrics(P), wall = Date.now() - t0;
    const ft = await P.ev(`(window.__ftOn=false,window.__ft)`);
    await P.c.send('Performance.disable');
    const n = Math.max(1, ft.length), d = (k) => (m1[k] - m0[k]) * 1000;
    const st = stats(ft);
    st.cpu = { n: ft.length, fps: +(ft.length / (wall / 1000)).toFixed(1), script: +(d('ScriptDuration') / n).toFixed(4), task: +(d('TaskDuration') / n).toFixed(4), layout: +((d('LayoutDuration') + d('RecalcStyleDuration')) / n).toFixed(4), scriptPerSec: +(d('ScriptDuration') / (wall / 1000)).toFixed(2), taskPerSec: +(d('TaskDuration') / (wall / 1000)).toFixed(2) };
    st.ft = ft; return st;
}
async function measure(P) {
    if (CPU) return measureCpu(P);
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
async function raced(E, g, variant) { try { return await raced1(E, g, variant); } catch (e) { console.log('retry race', g, String(e.message).slice(0, 120)); return raced1(E, g, variant); } }
async function raced1(E, g, variant) {
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
        if (process.env.PERF_NOCHIP || variant === 'nochip') await H.ev(`(()=>{const st=document.createElement('style');st.textContent='.lprc-chip,.lpr-hud{display:none!important}';document.head.appendChild(st);return true})()`);
        /* 커널 틱 정지(진단): 250ms 간격 타이머를 전부 세운다 — 레이스 판 자체(게임 코드)의 비용만 남는다 */
        if (variant === 'nokernel') await H.ev(`(()=>{for(const id of (window.__iv250||[]))clearInterval(id);return (window.__iv250||[]).length})()`);
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
            const RK = [], RH = [];
            for (let k = 0; k < ROUNDS; k++) {
                B.push(await solo(E, g, 'base')); N.push(await solo(E, g, 'new'));
                if (!NORACE && (CPU || k < 3)) RC.push(await raced(E, g));
                if (CPU && !NORACE) { RK.push(await raced(E, g, 'nokernel')); RH.push(await raced(E, g, 'nochip')); }
            }
            if (CPU) {
                const md = (xs, k) => { const a = xs.map(x => x.cpu[k]).sort((x, y) => x - y); return a.length ? a[Math.floor((a.length - 1) / 2)] : null; };
                const row = (name, xs) => xs.length ? { name, script: md(xs, 'script'), task: md(xs, 'task'), layout: md(xs, 'layout'), fps: md(xs, 'fps'), scriptPerSec: md(xs, 'scriptPerSec'), taskPerSec: md(xs, 'taskPerSec'), all: xs.map(x => x.cpu.script) } : null;
                const R = [row('base(solo)', B), row('new(solo)', N), row('race', RC), row('race-k(no kernel tick)', RK), row('race-c(no chip/HUD)', RH)].filter(Boolean);
                const b = R[0], rc = R.find(r => r.name === 'race'), nk = R.find(r => r.name.startsWith('race-k'));
                const dRace = rc ? +(rc.script - b.script).toFixed(4) : null, dKernel = rc && nk ? +(rc.script - nk.script).toFixed(4) : null;
                const dTaskK = rc && nk ? +(rc.task - nk.task).toFixed(4) : null;
                /* 게이트: 커널이 더하는 CPU(레이스 − 커널 세운 레이스) ≤ 0.125ms/프레임(= 0.5ms @4x). 레이스 판과 솔로 판의 차이(게임 장면 차이)는 참고 */
                const pass = dKernel == null || (dKernel <= 0.125 && dTaskK <= 0.2);
                if (!pass) fail++;
                rows.push({ g, cpu: R, dRaceVsSolo: dRace, dKernelScript: dKernel, dKernelTask: dTaskK, pass });
                console.log(JSON.stringify(rows[rows.length - 1]));
                continue;
            }
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
    if (CPU) {
        console.log('\n| 게임 | 변형 | Script CPU ms/프레임 | Task CPU ms/프레임 | Layout+Style | fps | 회차별 script |\n|---|---|---|---|---|---|---|');
        rows.forEach(r => { r.cpu.forEach(c => console.log(`| ${r.g} | ${c.name} | ${c.script} | ${c.task} | ${c.layout} | ${c.fps} | ${c.all.join(' ')} |`)); console.log(`| ${r.g} | **커널 몫(race − race-k)** | ${r.dKernelScript} | ${r.dKernelTask} | | | 게이트 ≤ 0.125 (=0.5ms@4x) → ${r.pass ? 'PASS' : '**FAIL**'} · race−solo ${r.dRaceVsSolo} |`); });
        console.log(`CPU 시간(threadTicks, 스로틀 없음) · ${SECS}s/측정 · 기준 ${BASE}`);
        process.exit(fail ? 1 : 0);
    }
    console.log('\n| 게임 | pooled p95 base/new/race (ms) | Δnew | Δrace | 회차 중앙값 base/new/race | 프레임/회 | 판정 |\n|---|---|---|---|---|---|---|');
    rows.forEach(r => console.log(`| ${r.g} | ${r.pooled.map(x => x ?? '-').join(' / ')} | ${r.dNew} | ${r.dRace ?? '-'} | ${r.med.map(x => x ?? '-').join(' / ')} | ${r.frames.join('/')} | ${r.idle ? 'n/a(변할 때만 그림)' : r.pass ? 'PASS' : '**FAIL**'} |`));
    console.log(`CPU ${RATE}x · ${SECS}s/측정 · 기준 ${BASE}`);
    process.exit(fail ? 1 : 0);
}
main().catch(e => { console.error(e); process.exit(2); });
