/* 예산 E1·E2·E3 + 추첨 통합(F1: 전 기기 같은 시드·인증서·목격 배지) — DESIGN §7·§10.2 */
import { device, create, join, allEqual, closeAll } from './suites.mjs';

const J = JSON.stringify;
const run1 = (only, id) => !only.length || only.includes(id);
function top(snap, n = 8) { return Object.entries(snap.byEvent).sort((a, b) => b[1].bill - a[1].bill).slice(0, n).map(([k, v]) => k + '×' + v.n + '=' + v.bill).join(' '); }

async function room(E, n, tag) {
    const H = await device(E, tag + 'H'); const G = [];
    for (let i = 0; i < n - 1; i++) G.push(await device(E, tag + 'g' + i));
    const c = await create(H);
    for (const g of G) { const j = await join(g, c.url); if (!j.ok) throw new Error('join failed ' + J(j)); }
    return { H, G, c, all: [H, ...G] };
}

export async function budget(ctx) {
    const { E, relay, ok, sleep, only } = ctx;
    const report = {};

    for (const [id, n, lim] of [['E1a', 4, 2.0], ['E1b', 8, 5.0]]) {
        if (!run1(only, id)) continue;
        const R = await room(E, n, id);
        try {
            await sleep(8000);                  /* 합류 직후 빠른 시계 표본 hb 가 끝나도록 */
            relay.resetStats();
            await sleep(60000);
            const s = relay.snapshot(), rate = s.bill / (s.ms / 1000);
            report[id] = { rate: +rate.toFixed(2), bill: s.bill, top: top(s) };
            ok(id, rate <= lim, `idle lobby ${n} people, 60s → ${rate.toFixed(2)} msg/s (≤ ${lim})`, top(s));
        } finally { await closeAll(E, R.all); }
    }

    if (run1(only, 'E2')) {
        const R = await room(E, 4, 'E2');
        try {
            for (const g of R.G) await g.ev(`T.room.intent('ready',true)`);
            await R.H.ev('T.room.start({countdownMs:0})');
            await sleep(9000);
            relay.resetStats();
            const t0 = Date.now(); let k = 0;
            while (Date.now() - t0 < 60000) { await R.G[k++ % 3].ev(`T.room.intent('inc',1)`); await sleep(5000); }
            const s = relay.snapshot(), rate = s.bill / (s.ms / 1000);
            report.E2 = { rate: +rate.toFixed(2), top: top(s) };
            ok('E2', rate <= 5.0, `turn-style play 4 people (1 intent + 1 state / 5s), 60s → ${rate.toFixed(2)} msg/s (≤ 5.0)`, top(s));
        } finally { await closeAll(E, R.all); }
    }

    if (run1(only, 'E3') || run1(only, 'F1')) {
        const R = await room(E, 8, 'E3');
        try {
            await sleep(4000);
            relay.resetStats();
            const names = ['Ana', 'Bo', 'Cy', 'Dee', 'Eve', 'Fin', 'Gus', 'Hal'];
            const hr = await R.H.ev(`LpFair.draw(T.room,{params:{names:${J(names)}}}).then(r=>({round:r.round,seed:LpFair.hex(r.seed),startAt:r.startAt}))`);
            await Promise.all(R.G.map(g => g.wait(`T.seeds[${hr.round}]`, 8000)));
            await sleep(700);    /* reveal 재전송 마무리 */
            const s = relay.snapshot();
            const fairBill = Object.entries(s.byEvent).filter(([k]) => /:fair$/.test(k)).reduce((a, [, v]) => a + v.bill, 0);
            const snapReq = (s.byEvent['g:snap_req'] || { n: 0 }).n;
            const seeds = await Promise.all(R.all.map(p => p.ev(`T.seeds[${hr.round}]||(T.room.isHost?${J(hr.seed)}:null)`)));
            const verify = await Promise.all(R.G.map(p => p.ev(`(async()=>{const c=T.certs[${hr.round}];if(!c)return 'nocert';const v=await LpFair.cert.verify(c,(p,rng)=>{const i=rng.int(p.names.length);return {idx:i,name:p.names[i]}});return v.ok?v.res.name:'bad:'+v.why})()`)));
            report.E3 = { drawBill: s.bill, fairOnly: fairBill, snapReq, top: top(s) };
            ok('E3', s.bill <= 200 && snapReq === 0, `8-person fair draw: ${s.bill} msgs total (fair ${fairBill}), snap_req ${snapReq} (≤ 200, 0)`, top(s));
            /* 목격 집계: 각자 결과 해시를 hb 에 편승 → 방장 hb 가 확인 수 방송 */
            relay.resetStats();
            await Promise.all(R.all.map(p => p.ev(`(()=>{const sd=T.room.isHost?${J(hr.seed)}:T.seeds[${hr.round}];const rng=LpFair.rng(LpFair.unhex(sd),'main');const i=rng.int(8);LpFair.witness(T.room,${hr.round},{idx:i});return i})()`)));
            const w = await Promise.all(R.all.map(p => p.wait(`(T.ev.filter(v=>v.e==='fair'&&v.x.k==='witness'&&v.x.round===${hr.round}).slice(-1)[0]||{x:{}}).x.ok===8`, 20000).then(() => true).catch(() => false)));
            const ws = relay.snapshot();
            const sameSeed = seeds.every(x => x === hr.seed);
            ok('F1', sameSeed && verify.every(v => v === verify[0] && !/^bad|nocert/.test(v)) && w.every(Boolean),
                'draw across 8 devices: same seed everywhere, every guest verifies #cert, witness badge "8 agree" on all', { seed: hr.seed.slice(0, 12), winner: verify[0], witness: w.filter(Boolean).length + '/8', witnessBill: ws.bill });
        } finally { await closeAll(E, R.all); }
    }
    console.log('BUDGET ' + J(report));
}
