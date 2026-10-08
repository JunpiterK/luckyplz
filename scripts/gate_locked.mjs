// 게이트를 '한 번에 하나만' 돌리는 순번 래퍼 (2026-10-08 — 병렬 에이전트 게이트가 겹쳐 PC 가 멈춘 사고 뒤)
//   node scripts/gate_locked.mjs <spacez_gate.mjs 인자들...>
//   예) node scripts/gate_locked.mjs det layout --root C:/code/python/luckyplz_wt/mp1 --port 9611 --jobs 1
// - 잠금: C:/code/python/luckyplz_wt/_gatelock 디렉터리(mkdir 원자성). 안에 owner.json {pid, root, args, at}
// - 다른 게이트가 돌고 있으면 20초마다 다시 시도(최대 3시간). 주인 PID 가 죽었으면 낡은 잠금으로 보고 회수
// - 이 래퍼가 띄운 게이트 프로세스가 끝나면(성공·실패 모두) 잠금 해제. Ctrl+C·kill 에도 해제 시도
// - 같은 프로세스 트리 안에서만 게이트를 돌릴 것(래퍼 없이 spacez_gate.mjs 를 직접 부르면 순번이 깨진다)
import { mkdirSync, rmSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import os from 'node:os';

// 슬롯 수: 기본 2 (2026-10-09 — 6코어 PC 에서 게이트 1개 ≈ CPU 70%. 2개까지는 낮은 우선순위로 돌려 PC 가 멈추지 않게)
const SLOTS = Math.max(1, Math.min(4, +(process.env.GATE_SLOTS || 2)));
const LOCKS = Array.from({ length: SLOTS }, (_, i) => 'C:/code/python/luckyplz_wt/_gatelock' + (i ? i + 1 : ''));
let LOCK = LOCKS[0];
const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const alive = (pid) => { try { process.kill(pid, 0); return true; } catch (e) { return e.code === 'EPERM'; } };

async function tryLock(L) {
    try {
        mkdirSync(L);
        writeFileSync(L + '/owner.json', JSON.stringify({ pid: process.pid, args, at: new Date().toISOString() }));
        return true;
    } catch (e) {
        if (e.code !== 'EEXIST') throw e;
        let o = null;
        try { o = JSON.parse(readFileSync(L + '/owner.json', 'utf8')); } catch (_) {}
        if (o && o.pid && !alive(o.pid)) { console.log('[gate-lock] 낡은 잠금 회수 (' + L + ', pid ' + o.pid + ' 없음)'); try { rmSync(L, { recursive: true, force: true }); } catch (_) {} return tryLock(L); }
        if (!o && existsSync(L)) { await sleep(3000); try { o = JSON.parse(readFileSync(L + '/owner.json', 'utf8')); } catch (_) {} if (!o) { try { rmSync(L, { recursive: true, force: true }); } catch (_) {} return tryLock(L); } }
        return false;
    }
}
async function acquire() {
    const t0 = Date.now();
    for (;;) {
        for (const L of LOCKS) { if (await tryLock(L)) { LOCK = L; return; } }
        if (Date.now() - t0 > 4 * 3600e3) { console.error('[gate-lock] 4시간 대기 초과 — 포기'); process.exit(3); }
        console.log('[gate-lock] 슬롯 ' + SLOTS + '개 모두 사용 중 — 20초 뒤 다시');
        await sleep(20000);
    }
}
function release() {
    try {
        const o = JSON.parse(readFileSync(LOCK + '/owner.json', 'utf8'));
        if (o.pid === process.pid) rmSync(LOCK, { recursive: true, force: true });
    } catch (_) {}
}

await acquire();
console.log('[gate-lock] 잠금 획득(' + LOCK + ') — 게이트 시작');
const child = spawn(process.execPath, [path.join(here, 'spacez_gate.mjs'), ...args], { stdio: 'inherit' });
// 게이트(와 그 자식 Edge)를 '낮음' 우선순위로 — CPU 가 꽉 차도 사용자 조작·화면이 먼저 돈다(Windows 는 자식이 우선순위 클래스를 물려받는다)
try { os.setPriority(child.pid, os.constants.priority.PRIORITY_BELOW_NORMAL); } catch (_) {}
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(sig, () => { try { child.kill(); } catch (_) {} release(); process.exit(130); });
process.on('exit', release);
child.on('exit', (code) => { release(); process.exit(code == null ? 1 : code); });
