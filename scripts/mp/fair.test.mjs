/* lpFair 단위 테스트 (Node, WebCrypto 내장) — DESIGN §10.2 D5·D6·D7 (+chain·deal·sha256)
   node scripts/mp/fair.test.mjs   → 실패 있으면 exit 1 */
import crypto from 'node:crypto';
import { loadFair, makeCert, outcomeNamed, sigPair, sign } from './fairlib.mjs';

const F = loadFair(), t = F._t;
let pass = 0, fail = 0;
function ok(id, c, name, info) { console.log((c ? 'PASS ' : 'FAIL ') + id + ' ' + name + (info !== undefined ? ' → ' + (typeof info === 'string' ? info : JSON.stringify(info)) : '')); c ? pass++ : fail++; }

/* 카이제곱 p값: Q(k/2, x/2) — 정규화 상부 불완전 감마 (Numerical Recipes gammq) */
function gammln(x) { const c = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5]; let y = x, tmp = x + 5.5; tmp -= (x + 0.5) * Math.log(tmp); let ser = 1.000000000190015; for (let j = 0; j < 6; j++) ser += c[j] / ++y; return -tmp + Math.log(2.5066282746310005 * ser / x); }
function gammq(a, x) {
    if (x < a + 1) { let ap = a, sum = 1 / a, del = sum; for (let n = 0; n < 1000; n++) { ap++; del *= x / ap; sum += del; if (Math.abs(del) < Math.abs(sum) * 3e-12) break; } return 1 - sum * Math.exp(-x + a * Math.log(x) - gammln(a)); }
    let b = x + 1 - a, c = 1 / 1e-300, d = 1 / b, h = d;
    for (let i = 1; i < 1000; i++) { const an = -i * (i - a); b += 2; d = an * d + b; if (Math.abs(d) < 1e-300) d = 1e-300; c = b + an / c; if (Math.abs(c) < 1e-300) c = 1e-300; d = 1 / d; const del = d * c; h *= del; if (Math.abs(del - 1) < 3e-12) break; }
    return Math.exp(-x + a * Math.log(x) - gammln(a)) * h;
}
function chi(counts, expect) { let x = 0; for (let i = 0; i < counts.length; i++) { const e = expect[i]; x += (counts[i] - e) * (counts[i] - e) / e; } return { x, p: gammq((counts.length - 1) / 2, x / 2) }; }
const seedI = (tag, i) => F.H('lpf-test|' + tag + '|' + i);

/* ── sha256 교차 ── */
{
    let bad = 0;
    for (let n = 0; n < 1200; n++) { const u = crypto.randomBytes(n % 300); if (F.hex(t.sha256(u)) !== crypto.createHash('sha256').update(u).digest('hex')) bad++; }
    ok('F0', bad === 0, 'sync SHA-256 == node:crypto (1200 inputs)', bad);
}
/* ── D7a 룰렛 n=2..12 각 10만 회 ── */
{
    /* 11개 독립 검정을 p>0.01 로 각각 보면 올바른 생성기도 ~10% 확률로 하나가 걸린다.
       그래서 p≤0.01 인 n 은 "독립 시드 스트림으로 한 번 더"(2단계) — 두 번 연속 걸릴 확률은 1e-4. 재검정 여부를 비고에 남긴다 */
    const N = 100000, ps = [], notes = [];
    const pOf = (n, tag) => { const cnt = new Array(n).fill(0); for (let i = 0; i < N; i++) cnt[F.outcomes.pickIndex(n, F.rng(seedI(tag, i), 'main'))]++; return chi(cnt, new Array(n).fill(N / n)).p; };
    for (let n = 2; n <= 12; n++) {
        let p = pOf(n, 'rl' + n);
        if (p <= 0.01) { const p2 = pOf(n, 'rl' + n + '-retest'); notes.push('n=' + n + ' p=' + p.toFixed(4) + '→retest ' + p2.toFixed(4)); p = p2; }
        ps.push(p);
    }
    const minP = Math.min(...ps);
    ok('D7a', ps.every(p => p > 0.01), 'roulette n=2..12 × 100k chi-square p>0.01', 'min p=' + minP.toFixed(4) + ' · ' + ps.map(p => p.toFixed(3)).join(' ') + (notes.length ? ' · ' + notes.join('; ') : ''));
}
/* ── D7b 팀·사다리(순열) 균일성: 4! = 24칸 10만 회, 5명 순열 위치 균일 ── */
{
    const N = 100000, cnt = {}, pos = Array.from({ length: 5 }, () => new Array(5).fill(0));
    for (let i = 0; i < N; i++) { const p = F.outcomes.permutation(4, F.rng(seedI('perm', i), 'main')); const k = p.join(''); cnt[k] = (cnt[k] || 0) + 1; }
    const keys = Object.keys(cnt);
    const r = chi(keys.map(k => cnt[k]), keys.map(() => N / 24));
    for (let i = 0; i < N; i++) { const p = F.outcomes.permutation(5, F.rng(seedI('perm5', i), 'main')); p.forEach((v, j) => pos[j][v]++); }
    const pp = pos.map(row => chi(row, new Array(5).fill(N / 5)).p);
    ok('D7b', keys.length === 24 && r.p > 0.01 && pp.every(p => p > 0.01), 'team/ladder permutation uniform (24 cells + 5×5 positions)', 'p=' + r.p.toFixed(4) + ' pos minP=' + Math.min(...pp).toFixed(4));
}
/* ── D7c 로또 6/45: 번호 빈도·첫 공 균일 ── */
{
    const N = 100000, cnt = new Array(45).fill(0), first = new Array(45).fill(0); let dupBad = 0;
    for (let i = 0; i < N; i++) { const s = F.outcomes.sample(45, 6, F.rng(seedI('lotto', i), 'main')); if (new Set(s).size !== 6) dupBad++; s.forEach(v => cnt[v]++); first[s[0]]++; }
    const a = chi(cnt, new Array(45).fill(N * 6 / 45)), b = chi(first, new Array(45).fill(N / 45));
    ok('D7c', dupBad === 0 && a.p > 0.01 && b.p > 0.01, 'lotto 6/45 × 100k: numbers & first ball uniform, no dup', 'p=' + a.p.toFixed(4) + '/' + b.p.toFixed(4));
}
/* ── D7d 가중치 ── */
{
    const N = 100000, w = [1, 2, 3, 4], cnt = [0, 0, 0, 0];
    for (let i = 0; i < N; i++) cnt[F.outcomes.pickWeighted(w, F.rng(seedI('w', i), 'main'))]++;
    const r = chi(cnt, w.map(x => N * x / 10));
    ok('D7d', r.p > 0.01, 'weighted pick 1:2:3:4 × 100k', 'p=' + r.p.toFixed(4));
}
/* ── D7e 결정성: 같은 seed 10만 회 동일 + 교차용 지문 ── */
{
    const run = () => { const h = crypto.createHash('sha256'); for (let i = 0; i < 100000; i++) { const r = F.rng(seedI('det', i), 'main'); h.update(r.u32() + ',' + r.int(37) + ',' + r.float().toFixed(12) + ';'); } return h.digest('hex'); };
    const d1 = run(), d2 = run();
    ok('D7e', d1 === d2, 'same seed → same outputs (100k, 2 runs)', d1.slice(0, 16));
    console.log('DIGEST ' + d1);
}
/* ── D6 인증서 원본 → ✓, 인코딩 왕복 ── */
const cert = await makeCert(3);
{
    const v = await F.cert.verify(cert, outcomeNamed);
    ok('D6a', v.ok && v.res.name === cert.res.name, 'original cert verifies, replay same result', { ok: v.ok, why: v.why, res: v.res });
    const enc = await F.cert.encode(cert), dec = await F.cert.decode(enc);
    const v2 = await F.cert.verify(dec, outcomeNamed);
    ok('D6b', v2.ok && enc[0] === 'z', '#cert encode(deflate-raw)/decode round-trip', 'len=' + enc.length);
}
/* ── D5 위조 탐지 ── */
{
    const cases = [
        ['name 1 char', c => { c.params.names[0] = 'Anb'; }],
        ['result changed', c => { c.res = { idx: (c.res.idx + 1) % 5, name: c.params.names[(c.res.idx + 1) % 5] }; }],
        ['nonce removed', c => { const p = c.L[0]; delete c.N[p]; c.L = c.L.slice(1); }],
        ['nonce altered', c => { const p = c.L[0]; c.N[p] = c.N[p].replace(/^./, x => x === '0' ? '1' : '0'); }],
        ['hostSeed swapped', c => { c.hs = F.hex(crypto.getRandomValues(new Uint8Array(32))); }],
        ['guest key swapped', c => { c.K[c.L[0]] = c.K[c.L[1]]; }],
        ['host sig tampered', c => { c.rsig = c.rsig.slice(0, -2) + (c.rsig.endsWith('AA') ? 'BB' : 'AA'); }],
        ['code changed', c => { c.code = c.code === 'ABCDEF' ? 'ABCDEG' : 'ABCDEF'; }],
        ['startAt changed', c => { c.st += 1; }],
        ['guest added (fake)', c => { c.L.push('paaaaaaaaaaaaaaaaaaaa'); c.N['paaaaaaaaaaaaaaaaaaaa'] = '00'; }]
    ];
    const res = [];
    for (const [name, mut] of cases) { const c = JSON.parse(JSON.stringify(cert)); mut(c); const v = await F.cert.verify(c, outcomeNamed); res.push(name + ':' + (v.ok ? 'ACCEPTED' : v.why)); }
    ok('D5', res.every(r => !/ACCEPTED/.test(r)), 'forged certs rejected (' + cases.length + ' cases)', res.join(' · '));
}
/* ── 방장 공모 불가: 방장이 hostSeed 를 바꾸면 커밋 불일치 ── */
{
    const c = JSON.parse(JSON.stringify(cert));
    const hs2 = F.hex(crypto.getRandomValues(new Uint8Array(32)));
    ok('D5b', t.commitOf(c.code, c.round, c.ph, hs2) !== c.C, 'host cannot change hostSeed after commit');
}
/* ── chain (D8 단위) ── */
{
    const len = 60; const a = new Array(len + 1); a[len] = crypto.getRandomValues(new Uint8Array(32));
    for (let i = len; i > 0; i--) a[i - 1] = t.sha256(a[i]);
    const s0 = F.hex(a[0]);
    const good = [1, 7, 30, 60].every(i => F.chain.verify(s0, F.hex(a[i]), i));
    const badI = F.chain.verify(s0, F.hex(a[8]), 7) || F.chain.verify(s0, F.hex(crypto.getRandomValues(new Uint8Array(32))), 5);
    const v1 = F.chain.value(F.hex(a[3]), 'ab'), v2 = F.chain.value(F.hex(a[3]), 'ab'), v3 = F.chain.value(F.hex(a[3]), 'ac');
    ok('D8u', good && !badI && F.hex(v1) === F.hex(v2) && F.hex(v1) !== F.hex(v3), 'chain verify(s0,s_i,i) + event value determinism');
}
/* ── deal verify ── */
{
    const hs = F.hex(crypto.getRandomValues(new Uint8Array(32))), ph = t.phOf({ deal: true });
    const C = t.commitOf('K7M2QX', 2, ph, hs);
    ok('DLu', F.deal.verify({ C, hs, code: 'K7M2QX', round: 2, ph }) && !F.deal.verify({ C, hs: hs.replace(/^./, '0') === hs ? hs.replace(/^./, '1') : hs.replace(/^./, '0'), code: 'K7M2QX', round: 2, ph }), 'deal commit verify');
}
/* ── pid·코드 정의 교차 (코어와 같은 식) ── */
{
    const g = await sigPair(); const pk = t.b64u(new Uint8Array(await crypto.webcrypto.subtle.exportKey('raw', g.pub)));
    const h = crypto.createHash('sha256').update(Buffer.concat([Buffer.from('lpr2-dev'), Buffer.from(t.ub64u(pk))])).digest();
    const B32 = 'abcdefghijklmnopqrstuvwxyz234567'; let bits = '', out = ''; for (const b of h) bits += b.toString(2).padStart(8, '0'); for (let i = 0; i + 5 <= bits.length; i += 5) out += B32[parseInt(bits.slice(i, i + 5), 2)];
    ok('ID1', t.pidOf(pk) === 'p' + out.slice(0, 20), 'pid = p + base32(SHA-256("lpr2-dev"‖raw))[0..19]', t.pidOf(pk));
}
console.log(`\nfair.test: ${pass} pass / ${fail} fail`);
process.exit(fail ? 1 : 0);
