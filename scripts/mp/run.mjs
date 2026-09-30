/* LuckyPlz Rooms v2 — 하네스 실행기
   node scripts/mp/run.mjs [suite…] [--live]
     suite: fair | smoke | core | spoof | budget | ui | all (기본 all)
     ui: MP_SHOTS=<폴더> 스크린샷 시트, MP_NOSHOTS=1 이면 U10 생략
   결과: 표 형식 PASS/FAIL + 예산 리포트. 스크래치: MP_SCRATCH (기본 %TEMP%/lp-mp)
   포트: MP_PORT (기본 8411) */
import { startRelay } from './relay.mjs';
import { Edge, R, ok, sleep } from './h.mjs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import * as suites from './suites.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const live = args.includes('--live');
let want = args.filter(a => !a.startsWith('--'));
if (!want.length || want.includes('all')) want = ['fair', 'core', 'spoof', 'budget', 'ui'];
if (live) want = ['live'];   /* --live: 실제 supabase Realtime 에 ZZ 코드 방 1개만 (DB 쓰기 없음) */
const only = (process.env.MP_ONLY || '').split(',').filter(Boolean);

async function isolate(relay, E) {
    relay.pageFor = null; relay.dropIf = null; relay.setFault({}); relay.part.clear();
    Object.keys(relay.rpcMocks).forEach(k => delete relay.rpcMocks[k]);
    relay.tap.length = 0; relay.stats.logOn = false; relay.resetStats();
    const left = E.pages.splice(0);
    const ctxs = new Set();
    for (const p of left) { ctxs.add(p.ctx); try { await p.close(); } catch (_) {} }
    for (const c of ctxs) { try { await E.disposeContext(c); } catch (_) {} }
    await sleep(300);
}
async function main() {
    const t0 = Date.now();
    if (want.includes('fair')) {
        const r = spawnSync(process.execPath, [path.join(HERE, 'fair.test.mjs')], { stdio: 'inherit' });
        ok('D5-D7', r.status === 0, 'fair.test.mjs (Node)', 'exit ' + r.status);
        const r2 = spawnSync(process.execPath, [path.join(HERE, 'core.test.mjs')], { stdio: 'inherit' });
        ok('CK-RP', r2.status === 0, 'core.test.mjs (Node: clock filter · replay window)', 'exit ' + r2.status);
        want = want.filter(w => w !== 'fair');
    }
    if (want.length) {
        const relay = await startRelay({ port: +(process.env.MP_PORT || 8411), live });
        const E = new Edge(relay.base, { live });
        let exitCode = 0;
        try {
            await E.start();
            const ctx = { relay, E, ok, sleep, only, live };
            for (const s of want) {
                if (!suites[s]) { console.log('unknown suite', s); continue; }
                console.log('\n=== suite ' + s + ' ===');
                try { await suites[s](ctx); } catch (e) { ok(s.toUpperCase(), false, 'suite crashed', String(e && e.stack || e).slice(0, 800)); }
                /* 스위트 사이 격리(순서 의존 제거): 릴레이 훅·결함 주입·목·계수 초기화, 남은 탭(스위트가 중간에 죽었을 때)을 닫는다.
                   예전엔 ui 가 걸어 둔 pageFor(게임 경로 → UI 픽스처)가 남아 뒤의 budget 이 'T is not defined' 로 죽었다 */
                await isolate(relay, E);
            }
        } finally {
            await E.stop();
            await relay.stop();
        }
    }
    const pass = R.rows.filter(r => r.pass).length, fail = R.rows.length - pass;
    console.log('\n| ID | 결과 | 항목 | 비고 |\n|---|---|---|---|');
    R.rows.forEach(r => console.log('| ' + r.id + ' | ' + (r.pass ? 'PASS' : '**FAIL**') + ' | ' + r.name + ' | ' + r.info.replace(/\|/g, '/').slice(0, 160) + ' |'));
    console.log('\n' + pass + ' pass / ' + fail + ' fail · ' + Math.round((Date.now() - t0) / 1000) + 's');
    if (process.env.MP_OUT) fs.writeFileSync(process.env.MP_OUT, JSON.stringify(R.rows, null, 1));
    process.exit(fail ? 1 : 0);
}
main().catch(e => { console.error(e); process.exit(2); });
