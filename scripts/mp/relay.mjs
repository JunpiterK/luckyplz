/* LuckyPlz Rooms v2 — 로컬 릴레이 + 정적 서버 (npm 의존 0)
   - HTTP: public/ 정적 파일, /vendor/supabase.min.js → Realtime 호환 심(shim.js), 그 밖의 문서 경로 → 테스트 페이지(page.html)
   - WS  : /__relay — 채널 구독·브로드캐스트·rpc 목. 지연·손실·재정렬(지터)·중복·분할(파티션) 주입
   - 계수: Supabase 과금 공식대로 (방송 1건 = 발신 1 + 수신자 수)
   사용: import { startRelay } from './relay.mjs'; const R = await startRelay({ port: 8411 }); ... R.stop() */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, '..', '..');
const PUB = path.join(ROOT, 'public');
const MIME = { '.mjs': 'application/javascript; charset=utf-8', '.js': 'application/javascript; charset=utf-8', '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.json': 'application/json', '.webp': 'image/webp', '.png': 'image/png', '.svg': 'image/svg+xml' };
const GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';

function wsAccept(key) { return crypto.createHash('sha1').update(key + GUID).digest('base64'); }
function frame(str) {
    const p = Buffer.from(str, 'utf8'), n = p.length;
    let h;
    if (n < 126) h = Buffer.from([0x81, n]);
    else if (n < 65536) { h = Buffer.alloc(4); h[0] = 0x81; h[1] = 126; h.writeUInt16BE(n, 2); }
    else { h = Buffer.alloc(10); h[0] = 0x81; h[1] = 127; h.writeBigUInt64BE(BigInt(n), 2); }
    return Buffer.concat([h, p]);
}

export async function startRelay(opt = {}) {
    const port = opt.port || 8411;
    const clients = new Map();          // id → {id, label, sock, subs:Set, alive}
    let nextId = 1;
    const fault = { lat: [2, 12], loss: 0, dup: 0 };
    const part = new Set();             // 분할된 label
    const rpcMocks = {};                // fn → (args) => data
    const S = { sends: 0, recvs: 0, byEvent: {}, byTopic: {}, drops: 0, dropsByE: {}, log: [], logOn: false, t0: Date.now(), dup: 0 };
    const tap = [];                     // 수동 청취 콜백 (label=null) — 원시 공격자·기록자

    function count(topic, ev, e, n) {
        S.sends += 1; S.recvs += n;
        const k = ev + ':' + (e || '?');
        const b = S.byEvent[k] || (S.byEvent[k] = { n: 0, bill: 0 }); b.n++; b.bill += 1 + n;
        const t = S.byTopic[topic] || (S.byTopic[topic] = { n: 0, bill: 0 }); t.n++; t.bill += 1 + n;
    }
    function deliver(c, msg) { if (c.sock.destroyed) return; try { c.sock.write(frame(msg)); } catch (_) {} }
    function route(from, topic, event, payload) {
        if (from && part.has(from.label)) return;      // 죽은 소켓 — 서버에 닿지 않음
        const recips = [...clients.values()].filter(c => c !== from && c.subs.has(topic));
        const e = payload && typeof payload === 'object' ? payload.e : undefined;
        count(topic, event, e, recips.length);
        if (S.logOn) S.log.push({ t: Date.now(), topic, event, from: from ? from.label : '(tap)', raw: JSON.stringify(payload) });
        const msg = JSON.stringify({ t: 'bc', topic, event, payload });
        for (const c of recips) {
            if (part.has(c.label)) continue;
            if (api.dropIf && api.dropIf(topic, event, payload, from ? from.label : null, c.label)) { S.drops++; continue; }
            if (fault.loss && Math.random() < fault.loss) { S.drops++; S.dropsByE[e] = (S.dropsByE[e] || 0) + 1; continue; }
            const d = fault.lat[0] + Math.random() * (fault.lat[1] - fault.lat[0]);
            setTimeout(() => deliver(c, msg), d);
            if (fault.dup && Math.random() < fault.dup) { S.dup++; setTimeout(() => deliver(c, msg), d + 5 + Math.random() * 60); }
        }
        tap.forEach(f => { try { f(topic, event, payload, from && from.label); } catch (_) {} });
    }

    const server = http.createServer((req, res) => {
        const u = new URL(req.url, 'http://x');
        let p = decodeURIComponent(u.pathname);
        let file = null;
        /* U 스위트: 실제 페이지(홈·/lobby/·/r/)와 픽스처 게임 페이지를 서빙하는 훅 — 없으면 예전 그대로 */
        const pf = api && api.pageFor ? api.pageFor(p) : null;
        if (pf) file = pf;
        else if (p === '/vendor/supabase.min.js') file = opt.live ? path.join(PUB, 'vendor', 'supabase.min.js') : path.join(HERE, 'shim.js');
        else if (p.startsWith('/__mp/')) file = path.join(HERE, p.slice(6));
        else if (/\.[a-z0-9]+$/i.test(p)) file = path.join(PUB, p);
        else file = path.join(HERE, 'page.html');
        if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end('nf'); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
        fs.createReadStream(file).pipe(res);
    });

    server.on('upgrade', (req, sock) => {
        const u = new URL(req.url, 'http://x');
        if (u.pathname !== '/__relay') { sock.destroy(); return; }
        sock.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ' + wsAccept(req.headers['sec-websocket-key']) + '\r\n\r\n');
        sock.setNoDelay(true);
        const c = { id: nextId++, label: u.searchParams.get('label') || 'anon', sock, subs: new Set() };
        clients.set(c.id, c);
        let buf = Buffer.alloc(0), frag = [];
        sock.on('data', chunk => {
            buf = Buffer.concat([buf, chunk]);
            for (;;) {
                if (buf.length < 2) return;
                const fin = buf[0] & 0x80, op = buf[0] & 0x0f, masked = buf[1] & 0x80;
                let len = buf[1] & 0x7f, off = 2;
                if (len === 126) { if (buf.length < 4) return; len = buf.readUInt16BE(2); off = 4; }
                else if (len === 127) { if (buf.length < 10) return; len = Number(buf.readBigUInt64BE(2)); off = 10; }
                const mo = off; if (masked) off += 4;
                if (buf.length < off + len) return;
                let pl = buf.subarray(off, off + len);
                if (masked) { const m = buf.subarray(mo, mo + 4); pl = Buffer.from(pl); for (let i = 0; i < pl.length; i++) pl[i] ^= m[i & 3]; }
                buf = buf.subarray(off + len);
                if (op === 8) { try { sock.end(); } catch (_) {} return; }
                if (op === 9) { try { sock.write(Buffer.from([0x8a, 0])); } catch (_) {} continue; }
                if (op === 1 || op === 0) {
                    frag.push(Buffer.from(pl));
                    if (!fin) continue;
                    const txt = Buffer.concat(frag).toString('utf8'); frag = [];
                    onMsg(c, txt);
                }
            }
        });
        const bye = () => { clients.delete(c.id); };
        sock.on('close', bye); sock.on('error', bye);
    });

    function onMsg(c, txt) {
        let m; try { m = JSON.parse(txt); } catch (_) { return; }
        if (m.t === 'sub') { c.subs.add(m.topic); deliver(c, JSON.stringify({ t: 'suback', topic: m.topic, ref: m.ref })); }
        else if (m.t === 'unsub') c.subs.delete(m.topic);
        else if (m.t === 'bc') route(c, m.topic, m.event, m.payload);
        else if (m.t === 'rpc') {
            const f = rpcMocks[m.fn];
            let data = null, error = null;
            if (f) { try { data = f(m.args || {}); } catch (e) { error = { message: String(e.message || e) }; } }
            else error = { message: 'Could not find the function ' + m.fn, code: 'PGRST202' };
            setTimeout(() => deliver(c, JSON.stringify({ t: 'rpcres', id: m.id, data, error })), 5);
        }
    }

    await new Promise((res, rej) => { server.once('error', rej); server.listen(port, '127.0.0.1', res); });

    const api = {
        dropIf: null,   /* (topic, event, payload, fromLabel, toLabel) => true 면 그 수신자에게 버림 */
        pageFor: null,  /* (pathname) => 절대 파일 경로 | null — 페이지 매핑 훅(U 스위트) */
        port, base: 'http://127.0.0.1:' + port, stats: S, fault, part, rpcMocks, tap,
        setFault(o) { Object.assign(fault, { lat: [2, 12], loss: 0, dup: 0 }, o || {}); },
        partition(label, on = true) { on ? part.add(label) : part.delete(label); },
        kill(label) { for (const c of clients.values()) if (c.label === label) { try { c.sock.destroy(); } catch (_) {} } },
        /* Node 쪽 원시 송신(공격자·가짜 호스트): 토픽 구독자 전원에게 */
        inject(topic, event, payload) { route(null, topic, event, payload); },
        resetStats() { Object.assign(S, { sends: 0, recvs: 0, byEvent: {}, byTopic: {}, drops: 0, dropsByE: {}, log: [], t0: Date.now(), dup: 0 }); },
        snapshot() { return JSON.parse(JSON.stringify({ sends: S.sends, recvs: S.recvs, bill: S.sends + S.recvs, byEvent: S.byEvent, byTopic: S.byTopic, drops: S.drops, dropsByE: S.dropsByE, ms: Date.now() - S.t0 })); },
        clients() { return [...clients.values()].map(c => ({ id: c.id, label: c.label, subs: [...c.subs] })); },
        stop() { for (const c of clients.values()) { try { c.sock.destroy(); } catch (_) {} } return new Promise(r => server.close(() => r())); }
    };
    return api;
}
