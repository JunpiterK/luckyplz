/* LuckyPlz Rooms v2 — 실전(LIVE) 종단 검증: 실제 Supabase Realtime + 실제 게임 페이지
   node scripts/mp/live.mjs [a b c d e f g idle | all]
     a 룰렛(링크·코드 참가, 공정 추첨 ×5, 배지, #cert 재검증)   b 윷(캐릭터 잠금·준비·시작·던지기·새로고침 복귀·한 판 더·내보내기)
     c 테트로미노 레이스   d 카레이싱 같이 보기   e 풍선 파티   f 홈 참가 상자·/lobby/ 허브   g 옛 ?room= 링크   idle 대기방 예산
   환경: LIVE_PORT(기본 8601) · MP_SCRATCH · LIVE_SHOTS(기본 <MP_SCRATCH>/live_shots) · MP_OUT=<json>
   주의: 운영 Realtime 에 실제 방송을 보낸다(DB 쓰기 없음 — REST·Auth 차단). 코드는 전부 'ZZ…' 테스트 방, 시나리오 끝에 닫는다. */
import fs from 'node:fs';
import path from 'node:path';
import { Edge, R, ok, SCR } from './h.mjs';
import { startServer } from './live_h.mjs';
import * as S from './suite_live.mjs';

const args = process.argv.slice(2).filter(a => !a.startsWith('--'));
const ALL = ['a', 'f', 'b', 'c', 'd', 'e', 'g', 'idle'];
const want = !args.length || args.includes('all') ? ALL : args;
const SHOTS = process.env.LIVE_SHOTS || path.join(SCR, 'live_shots');

async function main() {
    const t0 = Date.now();
    fs.mkdirSync(SHOTS, { recursive: true });
    const srv = await startServer(+(process.env.LIVE_PORT || 8601));
    const E = new Edge(srv.base, { live: true });
    const M = { lat: [], skew: [], rate: {}, notes: [] };   /* 측정값 모음 */
    try {
        await E.start();
        for (const w of want) {
            if (!S[w]) { console.log('unknown scenario', w); continue; }
            console.log('\n=== live ' + w + ' ===');
            try { await S[w]({ E, ok, SHOTS, M }); } catch (e) { ok('L' + w.toUpperCase(), false, 'scenario crashed', String(e && e.stack || e).slice(0, 900)); }
            /* 남은 탭 정리(방장 탭을 닫으면 pagehide — 방은 게스트 워치독으로 끝난다. 정상 경로는 시나리오가 직접 close) */
            const left = E.pages.splice(0); const ctxs = new Set();
            for (const p of left) { ctxs.add(p.ctx); try { await p.ev(`(()=>{try{var r=window.LpRooms&&LpRooms.current();if(r&&r.isHost)r.close()}catch(e){}return 1})()`, 3000); } catch (_) {} }
            if (left.length) await new Promise(r => setTimeout(r, 900));
            for (const p of left) { try { await p.close(); } catch (_) {} }
            for (const c of ctxs) { try { await E.disposeContext(c); } catch (_) {} }
        }
    } finally {
        await E.stop();
        srv.stop();
    }
    const pass = R.rows.filter(r => r.pass).length, fail = R.rows.length - pass;
    console.log('\n| ID | 결과 | 항목 | 비고 |\n|---|---|---|---|');
    R.rows.forEach(r => console.log('| ' + r.id + ' | ' + (r.pass ? 'PASS' : '**FAIL**') + ' | ' + r.name + ' | ' + r.info.replace(/\|/g, '/').slice(0, 300) + ' |'));
    console.log('\nMEASURE ' + JSON.stringify(M));
    console.log('\n' + pass + ' pass / ' + fail + ' fail · ' + Math.round((Date.now() - t0) / 1000) + 's · shots ' + SHOTS);
    if (process.env.MP_OUT) fs.writeFileSync(process.env.MP_OUT, JSON.stringify({ rows: R.rows, measure: M }, null, 1));
    process.exit(fail ? 1 : 0);
}
main().catch(e => { console.error(e); process.exit(2); });
