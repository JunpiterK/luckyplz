/* LuckyPlz Rooms v2 — P4 턴제 하네스 실행기 (실제 게임 페이지)
   node scripts/mp/run_turn.mjs [T1 T2 …]      (인자 없음 = 전부)
   포트 MP_PORT(기본 8451) · 스크래치 MP_SCRATCH · 결과 JSON MP_OUT · 디버그 로그 MP_DEBUG=1 */
import { startRelay } from './relay.mjs';
import { Edge, R, ok, sleep } from './h.mjs';
import fs from 'node:fs';
import * as T from './suite_turn.mjs';

const want = process.argv.slice(2).filter(a => !a.startsWith('--'));
async function main() {
    const t0 = Date.now();
    const relay = await startRelay({ port: +(process.env.MP_PORT || 8451) });
    const E = new Edge(relay.base);
    try {
        await E.start();
        const ctx = { relay, E, ok, sleep, want };
        await T.all(ctx);
    } catch (e) { ok('RUN', false, 'runner crashed', String(e && e.stack || e).slice(0, 900)); }
    finally { await E.stop(); await relay.stop(); }
    const pass = R.rows.filter(r => r.pass).length, fail = R.rows.length - pass;
    console.log('\n| ID | 결과 | 항목 | 비고 |\n|---|---|---|---|');
    R.rows.forEach(r => console.log('| ' + r.id + ' | ' + (r.pass ? 'PASS' : '**FAIL**') + ' | ' + r.name + ' | ' + r.info.replace(/\|/g, '/').slice(0, 220) + ' |'));
    console.log('\n' + pass + ' pass / ' + fail + ' fail · ' + Math.round((Date.now() - t0) / 1000) + 's');
    if (process.env.MP_OUT) fs.writeFileSync(process.env.MP_OUT, JSON.stringify(R.rows, null, 1));
    process.exit(fail ? 1 : 0);
}
main().catch(e => { console.error(e); process.exit(2); });
