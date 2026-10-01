/* 장기·象棋 엔진 하네스 (결정적 — 시드 고정) — 2026-10-02
   엔진 원본은 게임 페이지 한 곳뿐이다: public/games/janggi/index.html 의 /*JGE:start*\/ … /*JGE:end*\/ 구간을 잘라 돌린다.

   node scripts/janggi_harness.mjs            perft + 규칙 시험 + 독립 구현 대조 + AI 대국 200판(위반 0)
   node scripts/janggi_harness.mjs ladder     난이도 사다리(각 단계 40판, worker_threads 병렬)
   옵션: --src <엔진 js 파일>  --games N  --pairs easy-normal,normal-hard,hard-expert

   1) 象棋 시작 국면 perft 1~4 = 44 · 1,920 · 79,666 · 3,290,240 (공개된 값)
   2) 장기: 상차림 4×4 = 16가지 시작 국면 perft(쉼 제외/포함) 기록 + 불변식
   3) 독립 구현(아래 ref*, 좌표 계산만으로 짠 느린 규칙)과 무작위 국면 수천 개에서 합법수 집합이 정확히 같은지
   4) make/unmake 왕복 — 판·해시·평가·점수가 처음과 같고, 해시는 처음부터 다시 계산한 값과 같다
   5) 규칙 장면 시험 — 궁성 대각선 차·포·졸, 포끼리 못 넘고 못 잡음, 상 막힘, 빅장, 한 수 쉼, 반복 장군 패, 장군끼리 마주보기(象棋) 등
   6) AI 대 AI 200판 — 끝까지 두고 매 수를 독립 구현의 합법수로 검사(위반 0) */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { Worker, isMainThread, parentPort, workerData } from 'node:worker_threads';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };

function loadEngine(src) {
    let code;
    if (src) code = fs.readFileSync(src, 'utf8');
    else code = fs.readFileSync(path.join(ROOT, 'public', 'games', 'janggi', 'index.html'), 'utf8');
    const a = code.indexOf('/*JGE:start*/'), b = code.indexOf('/*JGE:end*/');
    if (a < 0 || b < 0) throw new Error('engine markers not found');
    return new Function(code.slice(a, b) + '\nreturn JGEngine();')();
}

/* ─────────────── 독립 구현(느리지만 읽기 쉬운 규칙) ───────────────
   좌표 (r,f), 진영 0 = 아래(먼저), 1 = 위. 기물 1장 2사 3상 4마 5차 6포 7졸. 엔진 표·코드를 하나도 쓰지 않는다. */
const K = 1, A = 2, E = 3, H = 4, R = 5, C = 6, P = 7, PASS = 16383;
const inB = (r, f) => r >= 0 && r < 10 && f >= 0 && f < 9;
const palOwner = (r, f) => (f < 3 || f > 5) ? -1 : r <= 2 ? 1 : r >= 7 ? 0 : -1;
/* 궁성 대각선 연결: 같은 궁성에서 가운데(r0+1,4) ↔ 네 귀 */
function diagLinked(r1, f1, r2, f2) {
    const p1 = palOwner(r1, f1), p2 = palOwner(r2, f2);
    if (p1 < 0 || p1 !== p2) return false;
    if (Math.abs(r1 - r2) !== 1 || Math.abs(f1 - f2) !== 1) return false;
    const r0 = p1 === 1 ? 0 : 7;
    return (r1 === r0 + 1 && f1 === 4) || (r2 === r0 + 1 && f2 === 4);
}
/* 궁성 대각선 위의 '줄'(귀→가운데→반대 귀): 시작점에서 방향 (dr,df) 로 가는 점들 */
function diagLine(r, f, dr, df) {
    const out = []; let cr = r, cf = f;
    for (;;) { const nr = cr + dr, nf = cf + df; if (!inB(nr, nf) || !diagLinked(cr, cf, nr, nf)) break; out.push([nr, nf]); cr = nr; cf = nf; }
    return out;
}
function refPseudo(b, side, j) {
    const s = side === 0 ? 1 : -1, out = [];
    const at = (r, f) => b[r * 9 + f];
    const add = (r, f, r2, f2) => { if (!inB(r2, f2)) return; const q = at(r2, f2); if (q * s > 0) return; out.push((r * 9 + f) | ((r2 * 9 + f2) << 7)); };
    const D4 = [[-1, 0], [1, 0], [0, -1], [0, 1]], DG = [[-1, -1], [-1, 1], [1, -1], [1, 1]];
    for (let r = 0; r < 10; r++) for (let f = 0; f < 9; f++) {
        const p = at(r, f) * s; if (p <= 0) continue;
        const own = palOwner(r, f);
        if (p === K || p === A) {
            for (const [dr, df] of D4) {
                if (!j && p === A) continue;
                const r2 = r + dr, f2 = f + df; if (inB(r2, f2) && palOwner(r2, f2) === side && own === side) add(r, f, r2, f2);
            }
            for (const [dr, df] of DG) {
                if (!j && p === K) continue;
                const r2 = r + dr, f2 = f + df; if (inB(r2, f2) && diagLinked(r, f, r2, f2) && palOwner(r2, f2) === side) add(r, f, r2, f2);
            }
        } else if (p === H) {
            for (const [dr, df] of D4) {
                const lr = r + dr, lf = f + df; if (!inB(lr, lf) || at(lr, lf)) continue;
                for (const sg of [-1, 1]) { const r2 = lr + dr + (df ? sg : 0), f2 = lf + df + (dr ? sg : 0); add(r, f, r2, f2); }
            }
        } else if (p === E) {
            if (!j) {
                for (const [dr, df] of DG) {
                    const er = r + dr, ef = f + df, r2 = r + 2 * dr, f2 = f + 2 * df;
                    if (!inB(r2, f2) || at(er, ef)) continue;
                    if (side === 0 ? r2 < 5 : r2 > 4) continue;   /* 강을 못 건넌다 */
                    add(r, f, r2, f2);
                }
            } else {
                for (const [dr, df] of D4) {
                    const ar = r + dr, af = f + df; if (!inB(ar, af) || at(ar, af)) continue;
                    for (const sg of [-1, 1]) {
                        const vr = dr + (df ? sg : 0), vf = df + (dr ? sg : 0);
                        const br = ar + vr, bf = af + vf; if (!inB(br, bf) || at(br, bf)) continue;
                        add(r, f, br + vr, bf + vf);
                    }
                }
            }
        } else if (p === R) {
            const lines = D4.map(([dr, df]) => { const L = []; let r2 = r + dr, f2 = f + df; while (inB(r2, f2)) { L.push([r2, f2]); r2 += dr; f2 += df; } return L; });
            if (j) for (const [dr, df] of DG) lines.push(diagLine(r, f, dr, df));
            for (const L of lines) for (const [r2, f2] of L) { const q = at(r2, f2); if (!q) { add(r, f, r2, f2); continue; } if (q * s < 0) add(r, f, r2, f2); break; }
        } else if (p === C) {
            const lines = D4.map(([dr, df]) => { const L = []; let r2 = r + dr, f2 = f + df; while (inB(r2, f2)) { L.push([r2, f2]); r2 += dr; f2 += df; } return L; });
            if (j) for (const [dr, df] of DG) lines.push(diagLine(r, f, dr, df));
            for (const L of lines) {
                if (!j) {
                    let k = 0;
                    for (; k < L.length && !at(L[k][0], L[k][1]); k++) add(r, f, L[k][0], L[k][1]);
                    k++; for (; k < L.length && !at(L[k][0], L[k][1]); k++);
                    if (k < L.length && at(L[k][0], L[k][1]) * s < 0) add(r, f, L[k][0], L[k][1]);
                } else {
                    let k = 0; while (k < L.length && !at(L[k][0], L[k][1])) k++;
                    if (k >= L.length) continue;
                    if (Math.abs(at(L[k][0], L[k][1])) === C) continue;   /* 포는 포를 못 넘는다 */
                    for (k++; k < L.length; k++) {
                        const q = at(L[k][0], L[k][1]);
                        if (!q) { add(r, f, L[k][0], L[k][1]); continue; }
                        if (q * s < 0 && Math.abs(q) !== C) add(r, f, L[k][0], L[k][1]);   /* 포는 포를 못 잡는다 */
                        break;
                    }
                }
            }
        } else if (p === P) {
            const fw = side === 0 ? -1 : 1;
            add(r, f, r + fw, f);
            const crossed = side === 0 ? r <= 4 : r >= 5;
            if (j || crossed) { add(r, f, r, f - 1); add(r, f, r, f + 1); }
            if (j) for (const sg of [-1, 1]) { const r2 = r + fw, f2 = f + sg; if (inB(r2, f2) && diagLinked(r, f, r2, f2) && palOwner(r, f) === 1 - side) add(r, f, r2, f2); }
        }
    }
    return out;
}
function refKing(b, side) { const t = side === 0 ? K : -K; for (let i = 0; i < 90; i++) if (b[i] === t) return i; return -1; }
function refFacing(b) { const a = refKing(b, 0), c = refKing(b, 1); if (a < 0 || c < 0 || a % 9 !== c % 9) return false; for (let q = c + 9; q < a; q += 9) if (b[q]) return false; return true; }
function refInCheck(b, side, j) {
    const k = refKing(b, side);
    if (!j && refFacing(b)) return true;
    return refPseudo(b, 1 - side, j).some(m => (m >> 7) === k);
}
function refLegal(b, side, j) {
    const out = [];
    for (const m of refPseudo(b, side, j)) {
        const fr = m & 127, to = m >> 7, nb = b.slice(); nb[to] = nb[fr]; nb[fr] = 0;
        if (!refInCheck(nb, side, j)) out.push(m);
    }
    if (j && !refInCheck(b, side, j)) out.push(PASS);
    return out;
}

/* ─────────────── 시험 ─────────────── */
const rows = []; let fails = 0;
function ok(id, cond, name, info) { rows.push({ id, cond }); if (!cond) fails++; console.log((cond ? 'PASS ' : 'FAIL ') + id + ' ' + name + (info !== undefined ? ' → ' + (typeof info === 'string' ? info : JSON.stringify(info)) : '')); return cond; }
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const sameSet = (a, b) => a.length === b.length && [...a].sort((x, y) => x - y).every((v, i, s) => v === [...b].sort((x, y) => x - y)[i]);

function snapshot(p) { return { b: Array.from(p.b), h1: p.h1, h2: p.h2, ev: p.ev, pt: Array.from(p.pt), cnt: Array.from(p.cnt), kp: Array.from(p.kp), stm: p.stm, n: p.n }; }
const eqSnap = (a, b) => JSON.stringify(a) === JSON.stringify(b);

function runRules(EN) {
    /* 1 · perft */
    const x = new EN.Pos('x');
    const want = [44, 1920, 79666, 3290240];
    for (let d = 1; d <= 4; d++) { const t = Date.now(), n = x.perft(d); ok('X-perft' + d, n === want[d - 1], '象棋 시작 국면 perft(' + d + ')', n + ' (기대 ' + want[d - 1] + ', ' + (Date.now() - t) + 'ms)'); }
    /* 2 · 장기 시작 16가지 */
    const jp = [];
    for (let a = 0; a < 4; a++) for (let c = 0; c < 4; c++) {
        const p = new EN.Pos('j', { form: [a, c] });
        const n1 = p.perftNoPass(1), n2 = p.perftNoPass(2), n3 = p.perftNoPass(3), w3 = p.perft(3);
        jp.push(EN.FORMS[a] + '/' + EN.FORMS[c] + ':' + n1 + ',' + n2 + ',' + n3 + '|' + w3);
        if (a === 2 && c === 2) ok('J-perft-std', n1 === 31 && n2 === 961, '장기 마상상마 양쪽 perft(1,2) = 31·961 (쉼 제외, 첫 두 수는 서로 간섭 없음)', [n1, n2, n3, w3]);
    }
    ok('J-perft-all', jp.length === 16, '장기 상차림 16가지 perft(1·2·3, 쉼 포함 3)', jp.join('  '));
    /* 3 · 독립 구현 대조 — 무작위로 두며 국면마다 합법수 집합 비교 */
    for (const v of ['x', 'j']) {
        const R0 = rng(v === 'x' ? 11 : 22); let pos = 0, bad = 0, first = null, nmv = 0;
        for (let g = 0; g < 60; g++) {
            const p = new EN.Pos(v, { form: [g % 4, (g >> 2) % 4] });
            for (let ply = 0; ply < 140; ply++) {
                const eng = p.legal(), ref = refLegal(Array.from(p.b), p.stm, v === 'j');
                pos++; nmv += eng.length;
                if (!sameSet(eng, ref)) { bad++; if (!first) first = { g, ply, b: Array.from(p.b).join(','), stm: p.stm, onlyE: eng.filter(m => !ref.includes(m)), onlyR: ref.filter(m => !eng.includes(m)) }; }
                /* 장군 판정도 대조 */
                if (!!p.inCheck() !== refInCheck(Array.from(p.b), p.stm, v === 'j')) { bad++; if (!first) first = { g, ply, chk: true }; }
                const real = eng.filter(m => m !== PASS); if (!real.length) break;
                /* 잡는 수를 조금 더 자주 — 기물이 빠진 국면도 고르게 */
                const caps = real.filter(m => p.b[m >> 7]);
                const pickL = caps.length && R0() < 0.35 ? caps : (R0() < 0.04 && eng.includes(PASS) ? [PASS] : real);
                p.make(pickL[Math.floor(R0() * pickL.length)]);
            }
        }
        ok('REF-' + v, bad === 0, (v === 'x' ? '象棋' : '장기') + ' 독립 구현과 합법수·장군 판정 일치', { positions: pos, moves: nmv, bad, first });
    }
    /* 4 · make/unmake 왕복 + 해시 재계산 */
    for (const v of ['x', 'j']) {
        const R1 = rng(v === 'x' ? 5 : 6); let bad = 0, cnt = 0;
        for (let g = 0; g < 30; g++) {
            const p = new EN.Pos(v, { form: [(g + 1) % 4, g % 4] });
            for (let ply = 0; ply < 120; ply++) {
                const lg = p.legal(); if (!lg.length) break;
                const s0 = snapshot(p);
                for (const m of lg) { if (!p.make(m)) { bad++; continue; } p.unmake(); cnt++; if (!eqSnap(s0, snapshot(p))) { bad++; break; } }
                const fresh = new EN.Pos(v, { empty: true });
                for (let i = 0; i < 90; i++) if (p.b[i]) fresh.put(i, p.b[i]);
                const fh1 = p.stm ? fresh.h1 ^ EN.ZS[0] : fresh.h1, fh2 = p.stm ? fresh.h2 ^ EN.ZS[1] : fresh.h2;
                if (fh1 !== p.h1 || fh2 !== p.h2) bad++;
                if (fresh.ev !== p.ev || fresh.pt.join() !== p.pt.join()) bad++;
                p.make(lg[Math.floor(R1() * lg.length)]);
            }
        }
        ok('MU-' + v, bad === 0, (v === 'x' ? '象棋' : '장기') + ' make/unmake 왕복·해시·평가·점수 재계산 일치', { checks: cnt, bad });
    }
    /* 5 · 규칙 장면 */
    const J = (fen) => EN.fromFen(fen, 'j');
    const has = (p, a, b) => p.legal().includes(a | (b << 7));
    const sq = (r, f) => r * 9 + f;
    /* 궁성 대각선 차: 아래 궁성 귀(9,3) 의 차 → 가운데 (8,4) → 반대 귀 (7,5) */
    let p = J('4k4/9/9/9/9/9/9/9/9/3R1K3 w');   /* 위 장 (0,4) · 아래 장 (9,5) */
    ok('J-R-diag', has(p, sq(9, 3), sq(8, 4)) && has(p, sq(9, 3), sq(7, 5)), '장기 차는 궁성 대각선을 따라 간다');
    p = EN.fromFen('4k4/9/9/9/9/9/9/9/9/3R1K3 w', 'x');
    ok('X-R-nodiag', !p.legal().includes(sq(9, 3) | sq(8, 4) << 7), '象棋 차는 대각선으로 못 간다');
    /* 포: 가운데 졸을 넘어 대각 귀로 / 포를 넘지 못함 / 포를 잡지 못함 */
    p = J('4k4/9/9/9/9/9/9/9/4P4/3C1K3 w');
    ok('J-C-diag', has(p, sq(9, 3), sq(7, 5)), '장기 포는 궁성 가운데 기물을 넘어 대각선으로');
    const upFrom70 = (q) => q.legal().filter(m => (m & 127) === sq(7, 0) && (m >> 7) % 9 === 0 && (m >> 7) < sq(7, 0));
    p = J('4k4/9/9/9/c8/9/9/C8/9/5K3 w');
    ok('J-C-noCannon', upFrom70(p).length === 0, '장기 포는 포를 넘지 못한다(위쪽 수 0)', upFrom70(p));
    p = J('4k4/9/9/9/c8/p8/9/C8/9/5K3 w');
    ok('J-C-noCapC', upFrom70(p).length === 0, '장기 포: 졸을 넘어 포를 잡는 수도 없다', upFrom70(p));
    p = J('4k4/9/9/9/r8/p8/9/C8/9/5K3 w');
    ok('J-C-capR', has(p, sq(7, 0), sq(4, 0)) && upFrom70(p).length === 1, '장기 포: 졸을 넘어 차는 잡는다(그 한 수뿐)', upFrom70(p));
    p = EN.fromFen('4k4/9/9/9/c8/p8/9/C8/9/5K3 w', 'x');
    ok('X-C-capC', p.legal().includes(sq(7, 0) | sq(4, 0) << 7), '象棋 포는 포를 잡을 수 있다');
    /* 장기 상: 곧게 한 칸(막힘) → 못 감 */
    p = J('4k4/9/9/9/9/9/9/9/4E4/5K3 w');
    ok('J-E-move', has(p, sq(8, 4), sq(5, 2)) && has(p, sq(8, 4), sq(5, 6)), '장기 상: 한 칸 곧게 + 두 칸 대각 (8,4)→(5,2)·(5,6)');
    p = J('4k4/9/9/9/9/9/9/4P4/4E4/5K3 w');
    ok('J-E-block1', !has(p, sq(8, 4), sq(5, 2)) && !has(p, sq(8, 4), sq(5, 6)), '장기 상: 첫 칸이 막히면 못 간다');
    p = J('4k4/9/9/9/9/9/5P3/9/4E4/5K3 w');
    ok('J-E-block2', !has(p, sq(8, 4), sq(5, 6)) && has(p, sq(8, 4), sq(5, 2)), '장기 상: 두 번째 칸(대각)이 막혀도 못 간다');
    /* 象棋 상: 강을 못 건너고 눈이 막히면 못 감 */
    p = EN.fromFen('4k4/9/9/9/9/2B6/9/9/9/3K5 w', 'x');
    const em = p.legal().filter(m => (m & 127) === sq(5, 2));
    ok('X-E-river', em.length === 2 && em.every(m => ((m >> 7) / 9 | 0) >= 5), '象棋 상은 강을 건너지 못한다((5,2) → 아래쪽 2곳만)', em.map(m => m >> 7));
    p = EN.fromFen('4k4/9/9/9/9/2B6/1P7/9/9/3K5 w', 'x');
    ok('X-E-eye', p.legal().filter(m => (m & 127) === sq(5, 2)).length === 1, '象棋 상은 눈이 막히면 못 간다');
    /* 졸: 적 궁성 안 대각선 앞으로(장기) */
    p = J('3k5/9/3P5/9/9/9/9/9/9/4K4 w');
    ok('J-P-diag', has(p, sq(2, 3), sq(1, 4)), '장기 졸은 적 궁성 대각선을 따라 앞으로');
    p = J('3k5/9/9/9/9/9/P8/9/9/4K4 w');
    ok('J-P-side', has(p, sq(6, 0), sq(6, 1)), '장기 졸은 처음부터 옆으로 갈 수 있다');
    p = EN.fromFen('3k5/9/9/9/9/9/P8/9/9/4K4 w', 'x');
    ok('X-P-side', !has(p, sq(6, 0), sq(6, 1)), '象棋 병은 강을 건너기 전엔 옆으로 못 간다');
    /* 象棋 장끼리 마주보기 금지 */
    p = EN.fromFen('3k5/9/9/9/9/9/9/9/9/4K4 w', 'x');
    ok('X-flying', !has(p, sq(9, 4), sq(9, 3)), '象棋: 장끼리 같은 줄에서 마주보게 되는 수는 둘 수 없다');
    /* 장기: 빅장은 둘 수 있다 → 상대가 풀지 않으면 점수 계산 */
    p = J('3k5/9/9/9/9/9/9/9/9/4K4 w');
    ok('J-bik-legal', has(p, sq(9, 4), sq(9, 3)), '장기: 빅장(장끼리 마주보기)은 둘 수 있다');
    p.make(sq(9, 4) | sq(9, 3) << 7);
    ok('J-bik-flag', p.hbik[p.n] === 1 && p.status() === null, '빅장 상태 — 아직 끝이 아니다');
    p.make(PASS);
    let st = p.status();
    ok('J-bik-end', st && st.why === 'bikjang' && st.w === 1, '빅장을 풀지 않으면 점수 계산(덤 1.5 → 한 승)', st);
    /* 한 수 쉼: 장군 중에는 못 쉼 · 두 번 연속 쉼 → 점수 */
    p = J('4k4/9/9/9/9/9/9/9/9/R3K4 w');
    ok('J-pass', p.legal().includes(PASS), '장군이 아니면 한 수 쉼 가능');
    p = J('5k3/9/9/9/9/9/9/9/9/4KR3 b');
    ok('J-pass-check', p.inCheck() && !p.legal().includes(PASS), '장군 중에는 한 수 쉼 불가');
    p = J('3k5/9/9/9/9/9/9/9/9/R3K4 w');
    p.make(PASS); p.make(PASS); st = p.status();
    ok('J-pass2', st && st.why === 'passes' && st.w === 0, '두 번 연속 쉼 → 점수 계산(차 있는 초 승)', st);
    /* 반복 장군: 象棋 — 같은 국면 세 번 + 한쪽만 매번 장군 → 그쪽 패 */
    p = EN.fromFen('3k5/9/9/9/9/9/9/9/9/R3K4 w', 'x');
    const seq = [[sq(9, 0), sq(8, 0)], [sq(0, 3), sq(1, 3)], [sq(8, 0), sq(9, 0)], [sq(1, 3), sq(0, 3)]];
    /* 위 수순은 장군·회피가 아니어도 반복 — 무승부 */
    for (let rep = 0; rep < 2; rep++) for (const [a, b] of seq) p.make(a | b << 7);
    st = p.status();
    ok('X-rep-draw', st && st.why === 'rep' && st.w === -1, '象棋 단순 반복 3회 → 무승부', st);
    p = EN.fromFen('4k4/9/9/9/9/9/9/9/9/R2K5 w', 'x');
    /* 차가 (9,0)↔(0,0) … 위 장을 계속 장군: 0행에서 장군(같은 줄) — 장은 (0,4)↔(0,3)/(1,4) 사이를 오간다 */
    const pc = [[sq(9, 0), sq(0, 0)], [sq(0, 4), sq(1, 4)], [sq(0, 0), sq(1, 0)], [sq(1, 4), sq(0, 4)], [sq(1, 0), sq(0, 0)], [sq(0, 4), sq(1, 4)], [sq(0, 0), sq(1, 0)], [sq(1, 4), sq(0, 4)], [sq(1, 0), sq(0, 0)]];
    let legalSeq = true; for (const [a, b] of pc) { if (!p.make(a | b << 7)) { legalSeq = false; break; } }
    st = p.status();
    ok('X-perp', legalSeq && st && st.why === 'perpetual' && st.w === 1, '象棋 반복 장군(長將) → 장군한 쪽 패', st);
    /* AI 는 반복 장군으로 지는 수를 피한다: 위 수순의 마지막 수 직전에서 AI 가 다른 수를 고른다 */
    p = EN.fromFen('4k4/9/9/9/9/9/9/9/9/R2K5 w', 'x');
    for (const [a, b] of pc.slice(0, 8)) p.make(a | b << 7);
    const avoid = p.think('expert', { nodes: 300000, noTime: true });
    ok('X-perp-avoid', avoid.m !== (sq(1, 0) | sq(0, 0) << 7), 'AI 는 세 번째 반복 장군(지는 수)을 두지 않는다', p.notation(avoid.m, 'zh'));
    /* 외통 · 궁지(象棋 = 패) */
    p = EN.fromFen('3k5/9/9/9/9/9/9/9/R8/R3K4 w', 'x');
    const mates = p.legal().filter(m => { p.make(m); const s = p.status(); p.unmake(); return s && s.why === 'mate'; });
    ok('X-mate', mates.length > 0, '象棋 외통 수 찾기', mates.map(m => p.notation(m, 'zh')));
    p = EN.fromFen('3k5/8R/9/9/9/9/9/9/9/4K4 b', 'x');
    st = p.status();
    ok('X-stalemate', !p.inCheck() && st && st.why === 'stalemate' && st.w === 0, '象棋 궁지(둘 수 없음, 장군 아님) = 둘 차례인 쪽 패', st);
    /* 장기 점수 계산: 시작 국면 = 초 72 · 한 73.5 */
    p = new EN.Pos('j');
    ok('J-points', p.points()[0] === 144 && p.points()[1] === 147, '장기 시작 점수 초 72 · 한 73.5 (×2 = 144·147)', p.points());
    /* 표기 */
    p = new EN.Pos('x');
    const n1 = p.notation(sq(7, 7) | sq(7, 4) << 7, 'zh'), n2 = p.notation(sq(9, 7) | sq(7, 6) << 7, 'wxf');
    ok('X-notation', n1 === '炮二平五' && n2 === 'H2+3', '象棋 표기 炮二平五 · H2+3', [n1, n2]);
    p.make(sq(7, 7) | sq(7, 4) << 7);
    const n3 = p.notation(sq(0, 7) | sq(2, 6) << 7, 'zh');
    ok('X-notation-b', n3 === '馬8進7', '象棋 黑 표기 馬8進7', n3);
    p = new EN.Pos('j');
    const n4 = p.notation(sq(6, 8) | sq(6, 7) << 7, 'ko');
    ok('J-notation', n4 === '79졸78', '장기 표기 79졸78', n4);
    /* AI: 한 수 외통은 무조건 둔다 */
    p = EN.fromFen('3k5/9/9/9/9/9/9/9/R8/R3K4 w', 'x');
    for (const lv of ['easy', 'normal', 'hard', 'expert']) {
        const r = p.think(lv, { seed: 3, nodes: 200000, noTime: true });
        p.make(r.m); const s2 = p.status(); p.unmake();
        ok('AI-mate1-' + lv, s2 && s2.why === 'mate', 'AI ' + lv + ': 한 수 외통을 놓치지 않는다', r.info.why);
    }
}

/* AI 대 AI — 한 판. 매 수 독립 구현으로 검사. 결과 반환 */
function playGame(EN, v, lvA, lvB, seed, opt = {}) {
    const R2 = rng(seed);
    const form = [Math.floor(R2() * 4), Math.floor(R2() * 4)];
    const p = new EN.Pos(v, { form });
    const mv = []; let illegal = 0, st = null;
    const openN = opt.open == null ? 2 : opt.open;
    for (let ply = 0; ply < 600; ply++) {
        let m;
        if (ply < openN) { const lg = p.legal().filter(x => x !== PASS); m = lg[Math.floor(R2() * lg.length)]; }
        else {
            const lv = p.stm === 0 ? lvA : lvB;
            const cfg = opt.cfg && opt.cfg[lv];
            m = p.think(lv, Object.assign({ seed: seed * 1000 + ply, noTime: true }, cfg || {})).m;
        }
        if (opt.check !== false) {
            const ref = refLegal(Array.from(p.b), p.stm, v === 'j');
            if (!ref.includes(m)) { illegal++; break; }
        }
        if (!p.make(m)) { illegal++; break; }
        mv.push(m);
        st = p.status();
        if (st) break;
    }
    return { v, form, n: mv.length, st, illegal, seed };
}

async function runGames(EN, total) {
    const lv = ['easy', 'normal'];
    let illegal = 0, ended = 0; const why = {}; let plies = 0;
    const t0 = Date.now();
    for (let g = 0; g < total; g++) {
        const v = g % 2 ? 'x' : 'j';
        const r = playGame(EN, v, lv[g % 2], lv[(g >> 1) % 2], 9000 + g, { open: 2 + (g % 3) });
        illegal += r.illegal; plies += r.n;
        if (r.st) { ended++; const k = v + ':' + r.st.why; why[k] = (why[k] || 0) + 1; }
        if (r.illegal) console.log('ILLEGAL', r);
    }
    ok('AIG', illegal === 0 && ended === total, 'AI 대 AI ' + total + '판 끝까지 · 매 수 독립 구현 검사 — 위반 0', { ended, illegal, plies, endings: why, sec: Math.round((Date.now() - t0) / 1000) });
}

/* ─────────────── 난이도 사다리(병렬) ─────────────── */
const LADDER_CFG = { expert: { nodes: 2600000 }, hard: {}, normal: {}, easy: {} };
if (!isMainThread) {
    const EN = loadEngine(workerData.src);
    const out = [];
    for (const job of workerData.jobs) {
        const [hi, lo] = job.pair; const v = job.v;
        const hiFirst = job.hiFirst;
        const r = playGame(EN, v, hiFirst ? hi : lo, hiFirst ? lo : hi, job.seed, { open: 2, cfg: LADDER_CFG, check: false });
        let res = 0.5;
        if (r.st && r.st.w >= 0) { const hiSide = hiFirst ? 0 : 1; res = r.st.w === hiSide ? 1 : 0; }
        out.push({ pair: job.pair.join('>'), v, res, why: r.st ? r.st.why : 'cap', n: r.n, illegal: r.illegal });
        parentPort.postMessage({ prog: 1 });
    }
    parentPort.postMessage({ done: out });
} else {
    const src = arg('--src', null);
    const mode = argv[0] && !argv[0].startsWith('--') ? argv[0] : 'rules';
    if (mode === 'ladder') {
        const pairs = arg('--pairs', 'normal-easy,hard-normal,expert-hard').split(',').map(s => s.split('-'));
        const N = +arg('--games', 40);
        const jobs = [];
        for (const pr of pairs) for (let g = 0; g < N; g++) jobs.push({ pair: pr, v: g % 2 ? 'x' : 'j', hiFirst: (g >> 1) % 2 === 0, seed: 777 + g * 13 + pr[0].length * 1000 });
        /* 무거운 판(고수)이 한 일꾼에 몰리지 않게 섞는다 */
        jobs.sort((a, b) => (a.seed * 7919) % 101 - (b.seed * 7919) % 101);
        const W = Math.max(1, Math.min(+arg('--workers', Math.max(1, os.cpus().length - 1)), jobs.length));
        const per = Array.from({ length: W }, () => []); jobs.forEach((j, i) => per[i % W].push(j));
        const t0 = Date.now(); let prog = 0;
        const res = (await Promise.all(per.map(js => new Promise((resolve, reject) => {
            const w = new Worker(fileURLToPath(import.meta.url), { workerData: { src, jobs: js } });
            w.on('message', m => { if (m.prog) { prog++; if (prog % 10 === 0) console.log('  … ' + prog + '/' + jobs.length + ' (' + Math.round((Date.now() - t0) / 1000) + 's)'); } if (m.done) resolve(m.done); });
            w.on('error', reject);
        })))).flat();
        for (const pr of pairs) {
            const k = pr.join('>'), rs = res.filter(r => r.pair === k);
            const w = rs.filter(r => r.res === 1).length, d = rs.filter(r => r.res === 0.5).length, l = rs.filter(r => r.res === 0).length;
            const score = (w + d / 2) / rs.length, why = {}; rs.forEach(r => { why[r.v + ':' + r.why] = (why[r.v + ':' + r.why] || 0) + 1; });
            ok('LAD-' + k, score >= 0.7, pr[0] + ' 가 ' + pr[1] + ' 상대 ' + rs.length + '판 — ' + w + '승 ' + d + '무 ' + l + '패 (득점 ' + Math.round(score * 100) + '%)', why);
        }
        console.log('ladder ' + Math.round((Date.now() - t0) / 1000) + 's');
    } else {
        const EN = loadEngine(src);
        runRules(EN);
        await runGames(EN, +arg('--games', 200));
    }
    const pass = rows.filter(r => r.cond).length;
    console.log('\n' + pass + ' pass / ' + fails + ' fail');
    process.exit(fails ? 1 : 0);
}
