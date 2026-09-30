/* Node 에서 lpFair.js 를 그대로 올리고(같은 소스 = 같은 결과), 인증서 원본을 만든다 */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { webcrypto } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, '..', '..');

export function loadFair() {
    if (globalThis.LpFair && globalThis.LpFair.version && globalThis.LpFair.version.indexOf('stub') < 0) return globalThis.LpFair;
    if (!globalThis.crypto) globalThis.crypto = webcrypto;
    vm.runInThisContext(fs.readFileSync(path.join(ROOT, 'public', 'js', 'lpFair.js'), 'utf8'), { filename: 'lpFair.js' });
    return globalThis.LpFair;
}

const S = () => globalThis.crypto.subtle;
const EC_S = { name: 'ECDSA', namedCurve: 'P-256' }, EC_D = { name: 'ECDH', namedCurve: 'P-256' };
async function raw(k) { return new Uint8Array(await S().exportKey('raw', k)); }
export async function sigPair() { const k = await S().generateKey(EC_S, true, ['sign', 'verify']); return { priv: k.privateKey, pub: k.publicKey }; }
export async function dhPair() { return S().generateKey(EC_D, true, ['deriveBits']); }
export async function sign(priv, str) { const F = loadFair(); return F._t.b64u(new Uint8Array(await S().sign({ name: 'ECDSA', hash: 'SHA-256' }, priv, new TextEncoder().encode(str)))); }

/* 룰렛형 참조 outcome — 당첨 이름 */
export function outcomeWinner(params, rng) { return { idx: rng.int(params.names.length), name: null }; }
export function outcomeNamed(params, rng) { const i = rng.int(params.names.length); return { idx: i, name: params.names[i] }; }

/* 게스트 nG 명 + 방장으로 완전한 추첨 기록(인증서)을 만든다 — 실제 서명 */
export async function makeCert(nG = 3, params = { names: ['Ana', 'Bo', 'Cy', 'Dee', 'Eve'] }) {
    const F = loadFair(), t = F._t;
    const hs = await sigPair(), hd = await dhPair();
    const rpk = { sig: t.b64u(await raw(hs.pub)), dh: t.b64u(await raw(hd.publicKey)) };
    const code = t.codeOfF(t.roomF(rpk));
    const round = 1, hostSeed = crypto.getRandomValues(new Uint8Array(32)), hsHex = F.hex(hostSeed);
    const ph = t.phOf(params), C = t.commitOf(code, round, ph, hsHex);
    const L = [], N = {}, Hh = {}, Sg = {}, K = {};
    for (let i = 0; i < nG; i++) {
        const g = await sigPair(), pk = t.b64u(await raw(g.pub)), pid = t.pidOf(pk);
        const n = F.hex(crypto.getRandomValues(new Uint8Array(16))), h = t.nHash(round, pid, n);
        L.push(pid); N[pid] = n; Hh[pid] = h; K[pid] = pk; Sg[pid] = await sign(g.priv, t.gcMsg(code, round, h));
    }
    L.sort();
    const st = Date.now() + 900;
    const rsig = await sign(hs.priv, t.revealBody({ code, round, C, ph, hs: hsHex, L, N, st }));
    const seed = t.seedOf(C, hsHex, N);
    const res = outcomeNamed(params, F.rng(seed, 'main'));
    return { v: 1, g: 'roulette', code, round, params, C, hs: hsHex, ph, L, N, H: Hh, S: Sg, K, rpk, rsig, st, res, t: Date.now(), stats: { draws: 1, aborts: 0 } };
}
