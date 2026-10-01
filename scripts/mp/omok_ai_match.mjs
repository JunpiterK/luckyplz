/* 오목 AI 실력 시험 — 실제 페이지(public/games/omok/index.html) 안의 OMEngine 을 꺼내 워커 스레드로 대국
   node scripts/mp/omok_ai_match.mjs <A단계> <B단계> [판수=100] [규칙=free] [판=15] [스레드=4]
   예) node scripts/mp/omok_ai_match.mjs expert hard 100   ·   node scripts/mp/omok_ai_match.mjs hard normal 100
   판마다 처음 2~3수는 가운데 5×5 안 무작위(같은 판이 반복되지 않게), A 는 짝수 판에 흑 · 홀수 판에 백(색 공평).
   매 수 규칙 검사(빈칸·렌주 금수) — 어기면 'illegal' 로 집계. 수마다 걸린 시간(엔진 생성 포함)도 잰다. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Worker, isMainThread, parentPort, workerData } from 'node:worker_threads';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = process.env.ENGINE || path.resolve(HERE, '..', '..', 'public', 'games', 'omok', 'index.html');
function load() {
    const src = fs.readFileSync(SRC, 'utf8') + '\n';
    const m = /function OMEngine\(\)\{[\s\S]*?\n\}\n(?=\(function\(\)\{|\n|$)/.exec(src);
    if (!m) throw new Error('OMEngine not found in ' + SRC);
    return (new Function(m[0] + ';return OMEngine;'))()();
}
function play(E, lvB, lvW, rule, N, seed) {
    let s = seed >>> 0; const rnd = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
    const ctx = new E.Ctx(N, rule), h = (N - 1) >> 1, times = { 1: [], '-1': [] };
    let p = 1;
    const nOpen = 2 + Math.floor(rnd() * 2);
    for (let k = 0; k < nOpen; k++) for (let tr = 0; tr < 50; tr++) { const x = h + Math.floor(rnd() * 5) - 2, y = h + Math.floor(rnd() * 5) - 2, i = y * N + x; if (!ctx.b[i] && ctx.legal(i, p).ok) { ctx.place(i, p); p = -p; break; } }
    for (;;) {
        const lv = p === 1 ? lvB : lvW, t0 = Date.now();
        const r = new E.Ctx(N, rule, ctx.b).choose(p, lv, { seed: (seed * 31 + ctx.cnt) >>> 0 });
        times[p].push(Date.now() - t0);
        if (!ctx.legal(r.m, p).ok) return { res: 'illegal', by: p, times, n: ctx.cnt };
        ctx.place(r.m, p);
        if (ctx.winLine(r.m, p)) return { res: p, times, n: ctx.cnt };
        if (ctx.cnt >= ctx.NN) return { res: 0, times, n: ctx.cnt };
        p = -p;
    }
}
if (isMainThread) {
    const [lvA = 'expert', lvB = 'hard', G0 = '100', rule = 'free', N0 = '15', W0 = '4'] = process.argv.slice(2);
    const G = +G0, N = +N0, W = +W0;
    let done = 0, aw = 0, bw = 0, dr = 0, ill = 0, next = 0, aB = 0, aW = 0;
    const tA = [], tB = [], lens = [], t0 = Date.now();
    const st = a => { a = a.slice().sort((x, y) => x - y); return `avg ${(a.reduce((s, v) => s + v, 0) / a.length).toFixed(0)}ms · p95 ${a[Math.floor(a.length * .95)]}ms · max ${a[a.length - 1]}ms`; };
    for (let w = 0; w < W; w++) {
        const wk = new Worker(new URL(import.meta.url), { workerData: { lvA, lvB, rule, N } });
        const feed = () => { if (next < G) wk.postMessage(next++); else wk.terminate(); };
        wk.on('message', r => {
            done++; const aBlack = r.g % 2 === 0, aCol = aBlack ? 1 : -1;
            if (r.res === 'illegal') ill++; else if (r.res === 0) dr++; else if (r.res === aCol) { aw++; if (aBlack) aB++; else aW++; } else bw++;
            tA.push(...r.times[aCol]); tB.push(...r.times[-aCol]); lens.push(r.n);
            if (done % 10 === 0 || done === G) console.log(`${done}/${G}  ${lvA} ${aw} : ${bw} ${lvB}  draw ${dr}  illegal ${ill}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
            if (done === G) {
                console.log(`RESULT ${lvA} vs ${lvB} [${rule} ${N}×${N}] — ${lvA} wins ${aw}/${G} = ${(aw / G * 100).toFixed(0)}% (as black ${aB}/${Math.ceil(G / 2)}, as white ${aW}/${Math.floor(G / 2)}) · ${lvB} ${bw} · draw ${dr} · illegal ${ill} · avg ${(lens.reduce((s, v) => s + v, 0) / lens.length).toFixed(1)} stones`);
                console.log(`  move time ${lvA}: ${st(tA)}`);
                console.log(`  move time ${lvB}: ${st(tB)}`);
            }
            feed();
        });
        wk.on('online', feed);
    }
} else {
    const E = load(), { lvA, lvB, rule, N } = workerData;
    parentPort.on('message', g => { const aBlack = g % 2 === 0; const r = play(E, aBlack ? lvA : lvB, aBlack ? lvB : lvA, rule, N, 1000 + g * 7919); r.g = g; parentPort.postMessage(r); });
}
