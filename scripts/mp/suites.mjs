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
async function allEqual(pages, expr, ms = 12000) {
    const t0 = Date.now(); let vals;
    while (Date.now() - t0 < ms) { vals = await Promise.all(pages.map(p => p.ev(expr).catch(e => 'ERR ' + e.message))); if (vals.every(v => v === vals[0] && v)) return { ok: true, v: vals[0] }; await new Promise(r => setTimeout(r, 200)); }
    return { ok: false, vals };
}
async function closeAll(E, pages) { for (const p of pages) { try { await p.close(); } catch (_) {} try { await E.disposeContext(p.ctx); } catch (_) {} } }
function loadFixture() { return JSON.parse(fs.readFileSync(path.join(HERE, 'fixtures', 'collide.json'), 'utf8')); }

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
