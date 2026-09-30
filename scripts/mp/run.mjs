/* LuckyPlz Rooms v2 — 하네스 실행기
   node scripts/mp/run.mjs [suite…] [--live]
     suite: fair | smoke | core | spoof | budget | all (기본 all)
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
if (!want.length || want.includes('all')) want = ['fair', 'core', 'spoof', 'budget'];
const only = (process.env.MP_ONLY || '').split(',').filter(Boolean);

async function main() {
    const t0 = Date.now();
    if (want.includes('fair')) {
        const r = spawnSync(process.execPath, [path.join(HERE, 'fair.test.mjs')], { stdio: 'inherit' });
        ok('D5-D7', r.status === 0, 'fair.test.mjs (Node)', 'exit ' + r.status);
        want = want.filter(w => w !== 'fair');
    }
    if (want.length) {
        const relay = await startRelay({ port: +(process.env.MP_PORT || 8411) });
        const E = new Edge(relay.base, { live });
        let exitCode = 0;
        try {
            await E.start();
            const ctx = { relay, E, ok, sleep, only, live };
            for (const s of want) {
                if (!suites[s]) { console.log('unknown suite', s); continue; }
                console.log('\n=== suite ' + s + ' ===');
                try { await suites[s](ctx); } catch (e) { ok(s.toUpperCase(), false, 'suite crashed', String(e && e.stack || e).slice(0, 800)); }
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
