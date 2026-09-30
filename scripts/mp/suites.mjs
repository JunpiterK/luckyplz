/* 시나리오 모음 (DESIGN §10.2) — run.mjs 가 호출 */
import { webcrypto as wc } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as A from './attacker.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const J = JSON.stringify;

/* ── 공용 헬퍼 ───────────────────────────────────────────────── */
export async function device(E, label, gid = 'roulette', o = {}) { const p = await E.page(Object.assign({ label }, o)); await p.go('/games/' + gid + '/'); return p; }
export async function create(p, o = {}) {
    return p.ev(`LpRooms.create(${J(Object.assign({ gameId: 'roulette' }, o))}).then(r=>{T.bind(r);return {code:r.code,url:r.inviteUrl(),fp:r.fp,pid:r.me.pid,seal:r.seal,pin:r.pin||null}})`);
}
export async function join(p, urlOrCode, o = {}) {
    return p.ev(`(async()=>{try{const x=LpRooms.parseInvite(${J(urlOrCode)});const r=await LpRooms.join(Object.assign({code:x.code,inv:x.inv},${J(o)}));T.bind(r);return {ok:true,pid:r.me.pid,role:r.me.role,seat:r.me.seat,code:r.code,seal:r.seal}}catch(e){return {ok:false,reason:e.reason||String(e)}}})()`);
}
export const pidsOf = (p) => p.ev(`T.room&&T.room.roster().map(m=>m.p+':'+m.r+':'+m.c).sort().join(',')`);
export async function allEqual(pages, expr, ms = 12000) {
    const t0 = Date.now(); let vals;
    while (Date.now() - t0 < ms) { vals = await Promise.all(pages.map(p => p.ev(expr).catch(e => 'ERR ' + e.message))); if (vals.every(v => v === vals[0] && v)) return { ok: true, v: vals[0] }; await new Promise(r => setTimeout(r, 200)); }
    return { ok: false, vals };
}
export async function closeAll(E, pages) { for (const p of pages) { try { await p.close(); } catch (_) {} try { await E.disposeContext(p.ctx); } catch (_) {} } }
export function loadFixture() { return JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'collide.json'), 'utf8')); }

/* ── smoke: 생성·링크 참가 2대·상태·의도 ───────────────────────── */
export async function smoke({ E, ok, sleep }) {
    const H = await device(E, 'H'); const g1 = await device(E, 'g1'); const g2 = await device(E, 'g2');
    const c = await create(H);
    ok('SM1', /^[2-9A-HJKMNP-TV-Z]{6}$/.test(c.code), 'create', c);
    const j1 = await join(g1, c.url), j2 = await join(g2, c.url);
    ok('SM2', j1.ok && j2.ok, 'join x2', { j1, j2 });
    const eq = await allEqual([H, g1, g2], `T.room&&T.room.roster().map(m=>m.p).sort().join(',')`);
    ok('SM3', eq.ok, 'roster equal', eq.ok ? eq.v.split(',').length : eq.vals);
    const r = await g1.ev(`T.room.intent('inc',3)`);
    const eq2 = await allEqual([H, g1, g2], `T.room.state().game&&T.room.state().game.n`);
    ok('SM4', r.ok && eq2.ok && eq2.v === 3, 'intent → state', { r, eq2 });
    console.log('exc', H.exc, g1.exc, g2.exc);
    await closeAll(E, [H, g1, g2]);
}

export { core } from './suite_core.mjs';
export { spoof } from './suite_spoof.mjs';
export { budget } from './suite_budget.mjs';
export { ui } from './suite_ui.mjs';

/* ── live: 실제 vendored supabase-js + 운영 Realtime (브로드캐스트만, REST 차단). 코드는 ZZ 로 시작하게 키를 골라 만든다 ── */
export async function live({ E, ok, sleep }) {
    const { loadFair } = await import('./fairlib.mjs');
    const F = loadFair(), t = F._t, S = crypto.subtle;
    let keys = null, tries = 0;
    while (!keys) {
        tries++;
        const s = await S.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
        const d = await S.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits', 'deriveKey']);
        const rpk = { sig: t.b64u(new Uint8Array(await S.exportKey('raw', s.publicKey))), dh: t.b64u(new Uint8Array(await S.exportKey('raw', d.publicKey))) };
        if (t.codeOfF(t.roomF(rpk)).startsWith('ZZ')) keys = { sig: await S.exportKey('jwk', s.privateKey), dh: await S.exportKey('jwk', d.privateKey) };
    }
    const H = await device(E, 'LH'), g1 = await device(E, 'L1'), g2 = await device(E, 'L2');
    try {
        const real = await H.ev('!window.supabase.__shim&&typeof window.supabase.createClient==="function"');
        await H.ev(`LpRooms.config({testKeys:[${JSON.stringify(keys)}]})`);
        const c = await create(H);
        ok('L1', real && c.code.startsWith('ZZ'), 'live: vendored supabase-js 2.104, ZZ test code', { code: c.code, keyTries: tries });
        const j1 = await join(g1, c.url), j2 = await join(g2, c.code);
        const eq = await allEqual([H, g1, g2], `T.room&&T.room.roster().map(m=>m.p).sort().join(',')`, 15000);
        const r = await g1.ev(`T.room.intent('inc',2)`);
        const eq2 = await allEqual([H, g1, g2], `String(T.room.state().game&&T.room.state().game.n)`, 10000);
        const d = await H.ev(`LpFair.draw(T.room,{params:{names:['a','b','c']}}).then(r=>LpFair.hex(r.seed))`);
        await Promise.all([g1, g2].map(g => g.wait(`Object.values(T.seeds).length`, 10000)));
        const seeds = await Promise.all([g1, g2].map(g => g.ev('Object.values(T.seeds)[0]')));
        ok('L2', j1.ok && j2.ok && eq.ok && r.ok && eq2.ok && eq2.v === '2' && seeds.every(x => x === d), 'live: link + code join, intent→state, fair draw — over real Realtime', { j1: j1.ok, j2: j2.ok, n: eq2.v, seed: d.slice(0, 12) });
        await H.ev('T.room.close()'); await sleep(1500);
        const closed = await Promise.all([g1, g2].map(g => g.ev(`T.count('closed')`)));
        ok('L3', closed.every(x => x === 1), 'live: host close reaches guests', closed);
        console.log('exc', H.exc.concat(g1.exc, g2.exc).slice(0, 5));
    } finally { await closeAll(E, [H, g1, g2]); }
}
