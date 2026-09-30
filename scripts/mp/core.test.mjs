/* 코어 단위 테스트 (Node) — 브라우저 없이 돌릴 수 있는 순수 로직: 시계 필터 · 재생 방지 창
   node scripts/mp/core.test.mjs   (run.mjs 의 fair 단계가 같이 돌린다) */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { webcrypto } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
if (!globalThis.crypto) globalThis.crypto = webcrypto;
vm.runInThisContext(fs.readFileSync(path.join(ROOT, 'public', 'js', 'lpRoomsCore.js'), 'utf8'), { filename: 'lpRoomsCore.js' });
const T = globalThis.LpRooms._t;
let pass = 0, fail = 0;
function ok(id, cond, name, info) { cond ? pass++ : fail++; console.log((cond ? 'PASS ' : 'FAIL ') + id + ' ' + name + (info !== undefined ? ' → ' + (typeof info === 'string' ? info : JSON.stringify(info)) : '')); }

/* 결정적 난수(테스트가 매번 같은 값) */
function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const sample = T.Room.prototype._clockSample;
const realNow = Date.now;
function run(N, lat, theta, R, stepAt, theta2) {
    /* 게스트 시계 = 가상 now, 방장 시계 = now + theta. 표본 간격 1초 */
    const me = { _clk: [], _off: 0 };
    let now = 1_800_000_000_000;
    Date.now = () => now;
    try {
        for (let i = 0; i < N; i++) {
            const th = stepAt != null && i >= stepAt ? theta2 : theta;
            const d1 = lat(R), d2 = lat(R), hold = 5 + R() * 40;
            const t0 = now, t1 = t0 + d1 + th, t2 = t1 + hold, t3 = t0 + d1 + hold + d2;
            now = t3;
            sample.call(me, t0, t1, t2, t3);
            now += 1000;
        }
    } finally { Date.now = realNow; }
    return me;
}
const U = (lo, hi) => (R) => lo + R() * (hi - lo);
function stats(N, lat, trials, seed) {
    const R = rng(seed); let sq = 0, n20 = 0, worst = 0;
    for (let t = 0; t < trials; t++) { const e = run(N, lat, 1234.5, R)._off - 1234.5; sq += e * e; if (Math.abs(e) > 20) n20++; worst = Math.max(worst, Math.abs(e)); }
    return { rms: +Math.sqrt(sq / trials).toFixed(2), over20: +(100 * n20 / trials).toFixed(2), worst: +worst.toFixed(1) };
}

/* CK1 — CX3b 조건(지연 30~150ms 무작위, 표본 19개): 이전 필터 rms 10.7ms·>20ms 6.8% → 양방향 최소 필터 rms ≤ 6·>20ms ≤ 0.5% */
{
    const s = stats(19, U(30, 150), 4000, 1);
    ok('CK1', s.rms <= 6 && s.over20 <= 0.5, 'clock: 19 samples under 30–150ms jitter → rms ≤ 6ms, |err|>20ms ≤ 0.5%', s);
}
/* CK2 — 표본이 적을 때(합류 직후 3개)도 이전과 같거나 낫다 (이전: 20~60ms 에서 rms 6.0) */
{
    const a = stats(3, U(20, 60), 4000, 2), b = stats(6, U(20, 60), 4000, 3);
    ok('CK2', a.rms <= 6.5 && b.rms <= 4.5 && a.worst <= 20, 'clock: 3 / 6 samples under 20–60ms → rms ≤ 6.5 / 4.5ms', { n3: a, n6: b });
}
/* CK3 — 시계가 뛰었다(기기 시각 보정 +500ms): 모순 표본을 버리고 1~2개 표본 안에 새 값으로 */
{
    const R = rng(4);
    const me = run(14, U(20, 60), 0, R, 10, 500);
    ok('CK3', Math.abs(me._off - 500) <= 25 && me._clk.length <= 5, 'clock step (+500ms mid-stream) → inconsistent old samples dropped, estimate follows', { off: +me._off.toFixed(1), kept: me._clk.length });
}
/* CK4 — 표본 1개 = 그 표본의 오프셋(이전과 동일), 참값은 항상 [L,U] 안 */
{
    const R = rng(5);
    const me = run(1, U(10, 30), -777, R);
    const e = T.clkEstimate(me._clk, me._clk[0].t);
    ok('CK4', Math.abs(me._off - me._clk[0].off) < 1e-9 && e && e.slack >= 0, 'clock: single sample = its midpoint', { off: +me._off.toFixed(2) });
}
/* RP1 — 재생 방지 창: 새 c 수락, 중복 거절, 창 안 늦은 도착 수락, 창 밖 거절, floor(방장 새로고침·승계) 이하는 전부 거절.
         replaySeen 은 읽기 전용(표시 안 함) */
{
    const rec = T.memRec({ sig: 'x', dh: 'y' }, 0);
    const a = [T.replayOk(rec, 100), T.replayOk(rec, 100), T.replayOk(rec, 105), T.replayOk(rec, 102), T.replayOk(rec, 102), T.replayOk(rec, 105 - 64)];
    const seen0 = T.replaySeen(rec, 103), seen1 = T.replaySeen(rec, 103), take = T.replayOk(rec, 103), seen2 = T.replaySeen(rec, 103);
    const rec2 = T.memRec({ sig: 'x', dh: 'y' }, 5000);
    const b = [T.replaySeen(rec2, 4990), T.replayOk(rec2, 4990), T.replaySeen(rec2, 5000), T.replayOk(rec2, 5001), T.replayOk(rec2, 4999)];
    ok('RP1', JSON.stringify(a) === '[true,false,true,true,false,false]' && !seen0 && !seen1 && take && seen2 && JSON.stringify(b) === '[true,false,true,true,false]',
        'replay window: new/dup/late-in-window/out-of-window; replaySeen is read-only; restored floor rejects everything ≤ saved lastC', { a, peek: [seen0, seen1, take, seen2], floor: b });
}
console.log(`\ncore.test: ${pass} pass / ${fail} fail`);
process.exit(fail ? 1 : 0);
