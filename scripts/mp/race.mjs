/* P5 레이스·브리지 하네스 실행기 — node scripts/mp/race.mjs [race|games|bridges|all]
   MP_PORT(기본 8481) · MP_SCRATCH · MP_SHOTS · MP_ONLY=R1,B3,… · MP_OUT=<json> */
import { startRelay } from './relay.mjs';
import { Edge, R, ok } from './h.mjs';
import fs from 'node:fs';
import * as S from './suite_race.mjs';

const args = process.argv.slice(2).filter(a => !a.startsWith('--'));
let want = args.length && !args.includes('all') ? args : ['race', 'games', 'bridges'];
const only = (process.env.MP_ONLY || '').split(',').filter(Boolean);
async function main() {
    const t0 = Date.now();
    const relay = await startRelay({ port: +(process.env.MP_PORT || 8481) });
    const E = new Edge(relay.base);
    try {
        await E.start();
        for (const w of want) {
            if (!S[w]) { console.log('unknown suite', w); continue; }
            console.log('\n=== suite ' + w + ' ===');
            try { await S[w]({ relay, E, ok, only }); } catch (e) { ok(w.toUpperCase(), false, 'suite crashed', String(e && e.stack || e).slice(0, 800)); }
        }
    } finally { await E.stop(); await relay.stop(); }
    const pass = R.rows.filter(r => r.pass).length, fail = R.rows.length - pass;
    console.log('\n| ID | 결과 | 항목 | 비고 |\n|---|---|---|---|');
    R.rows.forEach(r => console.log('| ' + r.id + ' | ' + (r.pass ? 'PASS' : '**FAIL**') + ' | ' + r.name + ' | ' + r.info.replace(/\|/g, '/').slice(0, 220) + ' |'));
    console.log('\n' + pass + ' pass / ' + fail + ' fail · ' + Math.round((Date.now() - t0) / 1000) + 's');
    if (process.env.MP_OUT) fs.writeFileSync(process.env.MP_OUT, JSON.stringify(R.rows, null, 1));
    process.exit(fail ? 1 : 0);
}
main().catch(e => { console.error(e); process.exit(2); });
