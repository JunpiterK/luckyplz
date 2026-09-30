/* Node 쪽 원시 참여자 — 공격자·가짜 방장·레거시(v1·SZX) 흉내. relay.inject/tap 으로 채널에 직접 말한다 */
import { loadFair } from './fairlib.mjs';
const F = loadFair(), t = F._t;
const S = () => crypto.subtle;
const EC_S = { name: 'ECDSA', namedCurve: 'P-256' };

export async function importSig(jwk) { return S().importKey('jwk', jwk, EC_S, false, ['sign']); }
export async function signB(priv, str) { return t.b64u(new Uint8Array(await S().sign({ name: 'ECDSA', hash: 'SHA-256' }, priv, new TextEncoder().encode(str)))); }
export async function newSigKey() { const k = await S().generateKey(EC_S, true, ['sign', 'verify']); return { priv: k.privateKey, pub: t.b64u(new Uint8Array(await S().exportKey('raw', k.publicKey))) }; }

/* 방장 봉투 원시 제작 (서명 키를 임의로) */
export async function hEnv({ code, e, ep, s, tt, to, d, priv, zOverride }) {
    const env = { v: 2, e, ep };
    if (tt != null) env.t = tt; else env.s = s;
    if (to) env.to = to;
    env.j = JSON.stringify(d === undefined ? null : d);
    const tos = to ? (Array.isArray(to) ? to.slice().sort().join(',') : to) : '';
    env.z = zOverride || (priv ? await signB(priv, ['lpr2', 'h', code, ep, tt != null ? 't' + tt : String(s), e, tos, env.j].join('|')) : 'A'.repeat(86));
    return env;
}
export async function gEnv({ code, e, p, c, d, priv }) {
    const env = { v: 2, e, p, c, j: JSON.stringify(d === undefined ? null : d) };
    env.z = priv ? await signB(priv, ['lpr2', 'g', code, p, c, e, env.j].join('|')) : 'A'.repeat(86);
    return env;
}

/* 가짜 v2 방장: 같은 코드를 내는 다른 키(fixtures/collide.json 의 b)로 hello 에 응답 */
export async function fakeV2Host(relay, keys, code, gameId = 'roulette') {
    const priv = await importSig(keys.sig);
    let tt = 1; const ep = Date.now();
    const off = [];
    const f = async (topic, event, payload, from) => {
        if (topic !== 'lpr-' + code || event !== 'g' || !payload || payload.e !== 'hello_req' || from == null) return;
        const d = { v: 2, code, ep, rpk: keys.rpk, hk: keys.rpk, gameId, kind: 'draw', phase: 'lobby', lock: false, appr: false, pinReq: false, count: 1, max: 12, succ: [], n: [payload.n] };
        relay.inject('lpr-' + code, 'h', await hEnv({ code, e: 'hello', ep, tt: tt++, d, priv }));
    };
    relay.tap.push(f);
    return { stop() { const i = relay.tap.indexOf(f); if (i >= 0) relay.tap.splice(i, 1); } };
}
/* 레거시 v1 방장: guest:probe → host:probe_ack */
export function fakeV1Host(relay, code, gameId) {
    const f = (topic, event, payload, from) => {
        if (topic !== 'lp-room-' + code || event !== 'guest:probe' || from == null) return;
        relay.inject('lp-room-' + code, 'host:probe_ack', { pid: payload.pid, gameId, hostName: 'v1host', locked: false, guestCount: 1 });
    };
    relay.tap.push(f);
    return { stop() { const i = relay.tap.indexOf(f); if (i >= 0) relay.tap.splice(i, 1); } };
}
/* SZX 레이스 방: 2.5초마다 st 하트비트 */
export function fakeSzx(relay, code) {
    const iv = setInterval(() => relay.inject('szx-race-' + code, 'st', { p: 'szxfake', s: 'lobby', u: Date.now(), n: 'bot' }), 2500);
    relay.inject('szx-race-' + code, 'st', { p: 'szxfake', s: 'lobby', u: Date.now(), n: 'bot' });
    return { stop() { clearInterval(iv); } };
}
/* 수동 청취자(코드만 아는 외부인): 토픽의 모든 원문 기록 */
export function listener(relay, code) {
    const got = [];
    const f = (topic, event, payload) => { if (topic === 'lpr-' + code) got.push(JSON.stringify(payload)); };
    relay.tap.push(f);
    return { got, stop() { const i = relay.tap.indexOf(f); if (i >= 0) relay.tap.splice(i, 1); } };
}
/* 녹화기 — 특정 이벤트의 원본 봉투를 모은다(재생 공격용) */
export function recorder(relay, code) {
    const h = [], g = [];
    const f = (topic, event, payload) => { if (topic !== 'lpr-' + code || !payload) return; (event === 'h' ? h : g).push(JSON.parse(JSON.stringify(payload))); };
    relay.tap.push(f);
    return { h, g, stop() { const i = relay.tap.indexOf(f); if (i >= 0) relay.tap.splice(i, 1); } };
}
