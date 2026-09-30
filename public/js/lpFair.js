/* =====================================================================
   lpFair.js — LuckyPlz Rooms v2 공정성 프리미티브 (P1)
   설계: docs/multiplayer/DESIGN.md §6.1·§6.2.5·§8.3
   브라우저와 Node(WebCrypto 내장) 양쪽에서 돈다 — DOM 은 badge() 안에서만 만진다.

   ── API 동결 (2026-09-30, "rooms-v2: API freeze") ─────────────────────
   [+] = §8.3 원문에 없던 추가 항목.

   declare global { interface Window { LpFair: LpFair } }

   interface Rng {                    // sfc32, 정수 연산만 (기기 간 결정성)
     u32(): number;                   // [0, 2^32)
     int(n:number): number;           // [0, n) 거부 샘플링 — 편향 0
     float(): number;                 // [0, 1) 53비트
     pick<T>(a:T[]): T;
     shuffle<T>(a:T[]): T[];          // 제자리 Fisher–Yates, 같은 배열 반환
   }
   interface Cert {                   // 자가검증 인증서 (#cert=)
     v:1; g:string (*gameId*); code:string; round:number; params:any;
     C:string; hs:string (*hostSeed hex*); ph:string;
     L:string[]; N:{[pid:string]:string} (*n_i hex*); H:{[pid:string]:string} (*커밋 hex*);
     S:{[pid:string]:string} (*게스트 커밋 서명*); K:{[pid:string]:string} (*게스트 서명 공개키*);
     rpk:{sig:string, dh:string}; chain?:any[]; rsig:string (*방장 reveal 서명*); st:number (*startAt*);
     res?:any; t:number; stats:{draws:number, aborts:number};
   }
   type FairEvent =                   // room.on('fair', ev) — 방장·멤버 모두 받는다
       {k:'commit', round, params, C}
     | {k:'lock', round, L:string[]}
     | {k:'reveal', round, seed:Uint8Array, startAt:number, cert:Cert, ok:boolean, why?:string, mine:boolean, solo:boolean}
     | {k:'abort', round, by:'host'|'guest', reason:string, who?:string[]}
     | {k:'witness', round, ok:number, bad:number}                    // [+] 목격 집계(방장 hb 편승)
     | {k:'chain0', s0:string, len:number}
     | {k:'deal', round, G:string}  | {k:'dealR', round, hs:string, ok:boolean};

   interface LpFair {
     version: string;                                                     // [+]
     draw(room, o:{params:any, window?:number (*1500*), beacon?:boolean, hidden?:boolean (*deal 용*)}):
          Promise<{seed:Uint8Array, round:number, cert:Cert, startAt:number}>;    // 방장 호출. 멤버는 room.on('fair')
     rng(seed:Uint8Array|string, label:string): Rng;
     chain: {
       create(room, len:number): Promise<{s0:string}>;       // 방장: s_K…s_0 생성, s_0 공개(fair chain0)
       event(i:number, n?:string|Uint8Array): Promise<Uint8Array>;   // 방장: 사건 i 난수 = H("lpf1-e"|s_i|n)
       reveal(i:number): string;                             // [+] 방장: s_i hex (게임이 로그에 실어 공개)
       value(sI:string, n?:string): Uint8Array;              // [+] 누구나: 공개된 s_i·n 으로 사건 난수 재계산(동기)
       verify(s0:string, sI:string, i:number): boolean;      // H^i(s_i) == s_0 (동기)
     };
     deal: {
       begin(room): Promise<{hostSeed:Uint8Array, G:string, seed:Uint8Array}>;   // 방장만 seed 를 안다
       reveal(room): void;                                   // 판 끝 — hostSeed 공개(fair dealR)
       verify(cert:{C:string, hs:string, G:string, code:string, round:number, ph:string}): boolean;
     };
     cert: {
       encode(o:Cert): Promise<string>;                      // base64url(deflate-raw(JSON)) — 'z' 접두(압축)/'j'(무압축)
       decode(s:string): Promise<Cert>;
       verify(o:Cert, outcomeFn:(params:any, rng:Rng)=>any): Promise<{ok:boolean, res:any, why?:string}>;
     };
     witness(room, round:number, result:any): void;          // [+] 결과 해시를 내 다음 hb 에 편승(추가 메시지 0)
     badge(el:HTMLElement, info:{kind:'verified'|'seed'|'solo'|'mismatch', n?:number, round?:number, cert?:Cert}): void;
     beacon?: { at(round:number): Promise<{randomness:string, round:number}> };   // drand quicknet (기본 OFF)
     H(...parts:(string|Uint8Array)[]): Uint8Array;          // [+] 동기 SHA-256(문자열은 UTF-8, 이어붙임)
     hex(u8:Uint8Array): string;  unhex(s:string): Uint8Array;  canon(o:any): string;   // [+]
     outcomes: {                                             // [+] 참조 outcome(정수 연산만) — 게임이 그대로 써도 된다
       pickIndex(n:number, rng:Rng): number;
       pickWeighted(w:number[] (*정수*), rng:Rng): number;
       permutation(n:number, rng:Rng): number[];
       sample(n:number, k:number, rng:Rng): number[];        // 로또: 0..n-1 중 k개 순서대로
     };
   }

   ── 프로토콜 문자열 (모든 H 는 SHA-256, hex 소문자) ────────────────────
   ph   = hex(H(canon(params)))
   C    = hex(H("lpf1-c|"+code+"|"+round+"|"+ph+"|"+hex(hostSeed)))
   h_i  = hex(H("lpf1-n|"+round+"|"+pid+"|"+hex(n_i)))          zs_i = ECDSA(dsk, "lpf1-gc|"+code+"|"+round+"|"+h_i)
   seed = H("lpf1-s|"+C+"|"+hex(hostSeed)+"|"+ sort(pid).map(p=>p+":"+hex(n_p)).join(","))
   rsig = ECDSA(rsk, "lpf1-rv|"+canon({code,round,C,ph,hs,L,N,st}))
   rng(seed,label) = sfc32( H(seed ‖ UTF8(label))[0..15] ), 12회 예열
   ===================================================================== */
(function (G) {
    'use strict';
    if (G.LpFair && G.LpFair.version && G.LpFair.version.indexOf('stub') < 0) return;

    /* ── 바이트 도구 ─────────────────────────────────────────── */
    var TE = new TextEncoder(), TD = new TextDecoder();
    function utf8(s) { return TE.encode(String(s)); }
    function cat(parts) {
        var n = 0, i, arr = [];
        for (i = 0; i < parts.length; i++) { var p = parts[i]; p = (typeof p === 'string') ? utf8(p) : (p instanceof Uint8Array ? p : new Uint8Array(p)); arr.push(p); n += p.length; }
        var out = new Uint8Array(n), o = 0;
        for (i = 0; i < arr.length; i++) { out.set(arr[i], o); o += arr[i].length; }
        return out;
    }
    var HEX = '0123456789abcdef';
    function hex(u8) { var s = ''; for (var i = 0; i < u8.length; i++) s += HEX[u8[i] >> 4] + HEX[u8[i] & 15]; return s; }
    function unhex(s) { s = String(s || ''); var out = new Uint8Array(s.length >> 1); for (var i = 0; i < out.length; i++) out[i] = parseInt(s.substr(i * 2, 2), 16); return out; }
    function b64u(u8) { var s = ''; for (var i = 0; i < u8.length; i++) s += String.fromCharCode(u8[i]); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }
    function ub64u(s) { s = String(s || '').replace(/-/g, '+').replace(/_/g, '/'); while (s.length % 4) s += '='; var b = atob(s), out = new Uint8Array(b.length); for (var i = 0; i < b.length; i++) out[i] = b.charCodeAt(i); return out; }
    /* 정규 JSON — 키 정렬, undefined 제거. 기기 간 같은 바이트를 보장한다 */
    function canon(o) {
        if (o === null || typeof o !== 'object') { return o === undefined ? 'null' : JSON.stringify(o); }
        if (Array.isArray(o)) return '[' + o.map(function (x) { return x === undefined ? 'null' : canon(x); }).join(',') + ']';
        var ks = Object.keys(o).filter(function (k) { return o[k] !== undefined; }).sort();
        return '{' + ks.map(function (k) { return JSON.stringify(k) + ':' + canon(o[k]); }).join(',') + '}';
    }
    function rand(n) { var u = new Uint8Array(n); G.crypto.getRandomValues(u); return u; }

    /* ── 동기 SHA-256 (rng·chain.verify 는 동기여야 한다) ───────── */
    var K256 = new Uint32Array([0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]);
    var W = new Uint32Array(64);
    function sha256(msg) {
        var l = msg.length, nb = ((l + 9 + 63) >> 6) << 6, m = new Uint8Array(nb);
        m.set(msg); m[l] = 0x80;
        var bits = l * 8; m[nb - 4] = (bits >>> 24) & 255; m[nb - 3] = (bits >>> 16) & 255; m[nb - 2] = (bits >>> 8) & 255; m[nb - 1] = bits & 255;
        m[nb - 5] = Math.floor(l / 0x20000000) & 255;
        var h0 = 0x6a09e667, h1 = 0xbb67ae85, h2 = 0x3c6ef372, h3 = 0xa54ff53a, h4 = 0x510e527f, h5 = 0x9b05688c, h6 = 0x1f83d9ab, h7 = 0x5be0cd19;
        for (var off = 0; off < nb; off += 64) {
            var i, t1, t2;
            for (i = 0; i < 16; i++) W[i] = (m[off + i * 4] << 24) | (m[off + i * 4 + 1] << 16) | (m[off + i * 4 + 2] << 8) | m[off + i * 4 + 3];
            for (i = 16; i < 64; i++) {
                var x = W[i - 15], y = W[i - 2];
                var s0 = ((x >>> 7) | (x << 25)) ^ ((x >>> 18) | (x << 14)) ^ (x >>> 3);
                var s1 = ((y >>> 17) | (y << 15)) ^ ((y >>> 19) | (y << 13)) ^ (y >>> 10);
                W[i] = (W[i - 16] + s0 + W[i - 7] + s1) | 0;
            }
            var a = h0, b = h1, c = h2, d = h3, e = h4, f = h5, g = h6, h = h7;
            for (i = 0; i < 64; i++) {
                var S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7));
                var ch = (e & f) ^ (~e & g);
                t1 = (h + S1 + ch + K256[i] + W[i]) | 0;
                var S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10));
                var mj = (a & b) ^ (a & c) ^ (b & c);
                t2 = (S0 + mj) | 0;
                h = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
            }
            h0 = (h0 + a) | 0; h1 = (h1 + b) | 0; h2 = (h2 + c) | 0; h3 = (h3 + d) | 0; h4 = (h4 + e) | 0; h5 = (h5 + f) | 0; h6 = (h6 + g) | 0; h7 = (h7 + h) | 0;
        }
        var out = new Uint8Array(32), hs = [h0, h1, h2, h3, h4, h5, h6, h7];
        for (var k = 0; k < 8; k++) { out[k * 4] = hs[k] >>> 24; out[k * 4 + 1] = (hs[k] >>> 16) & 255; out[k * 4 + 2] = (hs[k] >>> 8) & 255; out[k * 4 + 3] = hs[k] & 255; }
        return out;
    }
    function H() { return sha256(cat(Array.prototype.slice.call(arguments))); }
    function Hx(s) { return hex(sha256(utf8(s))); }

    /* ── sfc32 결정적 RNG (§6.1.3) ────────────────────────────── */
    function rng(seed, label) {
        var sd = (typeof seed === 'string') ? (/^[0-9a-f]{64}$/.test(seed) ? unhex(seed) : utf8(seed)) : seed;
        var k = H(sd, String(label == null ? '' : label));
        var a = (k[0] | k[1] << 8 | k[2] << 16 | k[3] << 24) >>> 0, b = (k[4] | k[5] << 8 | k[6] << 16 | k[7] << 24) >>> 0,
            c = (k[8] | k[9] << 8 | k[10] << 16 | k[11] << 24) >>> 0, d = (k[12] | k[13] << 8 | k[14] << 16 | k[15] << 24) >>> 0;
        function u32() {
            var t = (a + b) | 0; a = b ^ (b >>> 9); b = (c + (c << 3)) | 0; c = (c << 21) | (c >>> 11); d = (d + 1) | 0; t = (t + d) | 0; c = (c + t) | 0;
            return t >>> 0;
        }
        for (var i = 0; i < 12; i++) u32();
        function int(n) {
            n = Math.floor(n);
            if (!(n >= 1) || n > 4294967296) throw new Error('LpFair.rng.int: bad n');
            if (n === 1) return 0;
            var lim = 4294967296 - (4294967296 % n), u;
            do { u = u32(); } while (u >= lim);
            return u % n;
        }
        function float() { return ((u32() >>> 5) * 67108864 + (u32() >>> 6)) / 9007199254740992; }
        function pick(arr) { return arr[int(arr.length)]; }
        function shuffle(arr) { for (var i = arr.length - 1; i > 0; i--) { var j = int(i + 1), t = arr[i]; arr[i] = arr[j]; arr[j] = t; } return arr; }
        return { u32: u32, int: int, float: float, pick: pick, shuffle: shuffle };
    }
    var outcomes = {
        pickIndex: function (n, r) { return r.int(n); },
        pickWeighted: function (w, r) {
            var tot = 0, i; for (i = 0; i < w.length; i++) { if (w[i] < 0 || Math.floor(w[i]) !== w[i]) throw new Error('weights must be non-negative integers'); tot += w[i]; }
            var x = r.int(tot); for (i = 0; i < w.length; i++) { if (x < w[i]) return i; x -= w[i]; } return w.length - 1;
        },
        permutation: function (n, r) { var a = []; for (var i = 0; i < n; i++) a.push(i); return r.shuffle(a); },
        sample: function (n, k, r) { var a = [], i; for (i = 0; i < n; i++) a.push(i); for (i = 0; i < k; i++) { var j = i + r.int(n - i), t = a[i]; a[i] = a[j]; a[j] = t; } return a.slice(0, k); }
    };

    /* ── 신원·코드 (lpRoomsCore 와 같은 정의 — 인증서 단독 검증용) ── */
    var B32 = 'abcdefghijklmnopqrstuvwxyz234567';
    function base32(u8) { var out = '', bits = 0, v = 0; for (var i = 0; i < u8.length; i++) { v = (v << 8) | u8[i]; bits += 8; while (bits >= 5) { out += B32[(v >>> (bits - 5)) & 31]; bits -= 5; } } if (bits > 0) out += B32[(v << (5 - bits)) & 31]; return out; }
    function pidOf(pkSig) { return 'p' + base32(H('lpr2-dev', ub64u(pkSig))).slice(0, 20); }
    var A30 = '23456789ABCDEFGHJKMNPQRSTVWXYZ';
    function codeOfF(F) {
        var x = 0; for (var i = 0; i < 6; i++) x = x * 256 + F[i];
        x = x % 729000000; var s = '';
        for (var j = 0; j < 6; j++) { s = A30[x % 30] + s; x = Math.floor(x / 30); }
        return s;
    }
    function roomF(rpk) { return H('lpr2-room', ub64u(rpk.sig), ub64u(rpk.dh)); }
    function subtle() { return G.crypto && G.crypto.subtle; }
    var _pkCache = {};
    function importPk(pk) {
        if (_pkCache[pk]) return _pkCache[pk];
        return (_pkCache[pk] = subtle().importKey('raw', ub64u(pk), { name: 'ECDSA', namedCurve: 'P-256' }, false, ['verify']));
    }
    async function verifySig(pk, msg, sig) {
        try { var k = await importPk(pk); return await subtle().verify({ name: 'ECDSA', hash: 'SHA-256' }, k, ub64u(sig), utf8(msg)); }
        catch (_) { return false; }
    }
    /* 승계 서명 체인(§6.0.6) — 링크마다 이전 키가 succ 명단에 서명, 새 키의 pid 가 그 명단에 있어야 한다 */
    async function chainKey(code, rpk, chain) {
        var key = rpk.sig;
        if (!chain || !chain.length) return key;
        for (var i = 0; i < chain.length; i++) {
            var L = chain[i];
            if (!L || !Array.isArray(L.succ) || !L.npk || !L.npk.sig) return null;
            if (!(await verifySig(key, 'lpr2|succ|' + code + '|' + L.ep + '|' + L.succ.join(','), L.z))) return null;
            if (L.succ.indexOf(pidOf(L.npk.sig)) < 0) return null;
            key = L.npk.sig;
        }
        return key;
    }

    /* ── 공정 추첨 계산 ─────────────────────────────────────── */
    function phOf(params) { return Hx(canon(params)); }
    function commitOf(code, round, ph, hsHex) { return Hx('lpf1-c|' + code + '|' + round + '|' + ph + '|' + hsHex); }
    function nHash(round, pid, nHex) { return Hx('lpf1-n|' + round + '|' + pid + '|' + nHex); }
    function pairs(N) { return Object.keys(N || {}).sort().map(function (p) { return p + ':' + N[p]; }).join(','); }
    function seedOf(C, hsHex, N) { return H('lpf1-s|' + C + '|' + hsHex + '|' + pairs(N)); }
    function gOf(N) { return Hx('lpf1-g|' + pairs(N)); }
    function dealSeed(hsHex, G_) { return H('lpf1-d|' + hsHex + '|' + G_); }
    function revealBody(o) { return 'lpf1-rv|' + canon({ code: o.code, round: o.round, C: o.C, ph: o.ph, hs: o.hs, L: o.L, N: o.N, st: o.st }); }
    function gcMsg(code, round, h) { return 'lpf1-gc|' + code + '|' + round + '|' + h; }
    function resHash(res) { return Hx(canon(res)).slice(0, 8); }

    /* ── 인증서 ─────────────────────────────────────────────── */
    async function streamBytes(u8, Ctor, mode) {
        var cs = new Ctor(mode), w = cs.writable.getWriter(); w.write(u8); w.close();
        var rd = cs.readable.getReader(), parts = [], n = 0;
        for (;;) { var r = await rd.read(); if (r.done) break; parts.push(r.value); n += r.value.length; }
        return cat(parts);
    }
    var cert = {
        encode: async function (o) {
            var js = utf8(JSON.stringify(o));
            if (typeof G.CompressionStream === 'function') {
                try { return 'z' + b64u(await streamBytes(js, G.CompressionStream, 'deflate-raw')); } catch (_) {}
            }
            return 'j' + b64u(js);
        },
        decode: async function (s) {
            s = String(s || '').replace(/^#?cert=/, '');
            var t = s.charAt(0), body = ub64u(s.slice(1));
            if (t === 'z') body = await streamBytes(body, G.DecompressionStream, 'deflate-raw');
            else if (t !== 'j') throw new Error('bad cert');
            return JSON.parse(TD.decode(body));
        },
        verify: async function (o, outcomeFn) {
            function no(why) { return { ok: false, res: null, why: why }; }
            try {
                if (!o || o.v !== 1 || !o.rpk || typeof o.code !== 'string') return no('format');
                if (codeOfF(roomF(o.rpk)) !== o.code) return no('code');
                var key = await chainKey(o.code, o.rpk, o.chain);
                if (!key) return no('chain');
                if (phOf(o.params) !== o.ph) return no('params');
                if (commitOf(o.code, o.round, o.ph, o.hs) !== o.C) return no('commit');
                if (!(await verifySig(key, revealBody(o), o.rsig))) return no('host_sig');
                var L = o.L || [];
                if (Object.keys(o.N || {}).sort().join(',') !== L.slice().sort().join(',')) return no('nonces');
                for (var i = 0; i < L.length; i++) {
                    var p = L[i];
                    if (!o.K || !o.K[p] || pidOf(o.K[p]) !== p) return no('guest_key');
                    if (nHash(o.round, p, o.N[p]) !== (o.H && o.H[p])) return no('guest_commit');
                    if (!(await verifySig(o.K[p], gcMsg(o.code, o.round, o.H[p]), o.S && o.S[p]))) return no('guest_sig');
                }
                var seed = seedOf(o.C, o.hs, o.N);
                var res = outcomeFn ? outcomeFn(o.params, rng(seed, 'main')) : null;
                if (outcomeFn && o.res !== undefined && canon(res) !== canon(o.res)) return { ok: false, res: res, why: 'result' };
                return { ok: true, res: res };
            } catch (e) { return no('error:' + (e && e.message)); }
        }
    };

    /* ── 방 연동 (lpRoomsCore 의 room._io) ────────────────────── */
    function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
    function isMember(m, me) { return m && m.p !== me && m.r !== 'bot' && m.r !== 'host' && m.c !== 'off'; }
    function fstats(room) { var io = room._io; var st = io.isHost ? io.store() : (room._fst || (room._fst = {})); st.draws = st.draws || 0; st.aborts = st.aborts || 0; return st; }

    /* 방장 쪽 공통: 커밋 → 참가자 커밋 → 잠금 → 참가자 공개 */
    async function collect(room, round, C, ph, params, win, kind) {
        var io = room._io, me = room.me.pid;
        var want = room.roster().filter(function (m) { return isMember(m, me); }).map(function (m) { return m.p; });
        var st = io.store(); st.pend = st.pend || {};
        var commits = {}, reveals = {};
        var off = io.on('fair', function (from, d) {
            if (!from || !d || d.round !== round) return;
            if (d.k === 'c' && want.indexOf(from) >= 0 && typeof d.h === 'string' && !commits[from]) {
                var m = room.roster().filter(function (x) { return x.p === from; })[0];
                if (!m || !m.k) return;
                verifySig(m.k.sig, gcMsg(room.code, round, d.h), d.zs).then(function (ok) { if (ok && !commits[from]) commits[from] = { h: d.h, zs: d.zs, pk: m.k.sig }; });
            } else if (d.k === 'r' && commits[from] && typeof d.n === 'string' && !reveals[from]) {
                if (nHash(round, from, d.n) === commits[from].h) reveals[from] = d.n;
            }
        });
        try {
            await io.sendH('fair', { k: kind || 'commit', round: round, C: C, ph: ph, params: params, win: win }, { reliable: true });
            io.emit('fair', { k: 'commit', round: round, params: params, C: C });
            if (!want.length) return { L: [], N: {}, Hh: {}, S: {}, K: {}, missing: [] };
            var t0 = Date.now();
            while (Date.now() - t0 < win && Object.keys(commits).length < want.length) await sleep(40);
            await sleep(60);   /* 서명 검증 비동기 마무리 */
            var L = Object.keys(commits).sort();
            if (!L.length) return { L: [], N: {}, Hh: {}, S: {}, K: {}, missing: [] };
            await io.sendH('fair', { k: 'lock', round: round, L: L }, {});
            io.emit('fair', { k: 'lock', round: round, L: L });
            var t1 = Date.now();
            while (Date.now() - t1 < 1500 && Object.keys(reveals).length < L.length) await sleep(40);
            var N = {}, Hh = {}, S = {}, K = {}, missing = [];
            L.forEach(function (p) { if (reveals[p]) { N[p] = reveals[p]; Hh[p] = commits[p].h; S[p] = commits[p].zs; K[p] = commits[p].pk; } else missing.push(p); });
            return { L: L, N: N, Hh: Hh, S: S, K: K, missing: missing };
        } finally { off(); }
    }

    function makeCert(room, o) {
        var io = room._io;
        return { v: 1, g: room.gameId, code: room.code, round: o.round, params: o.params, C: o.C, hs: o.hs, ph: o.ph,
            L: o.L, N: o.N, H: o.Hh, S: o.S, K: o.K, rpk: io.rpk(), chain: io.chain() || undefined, rsig: o.rsig, st: o.st,
            t: Date.now(), stats: { draws: o.draws, aborts: o.aborts } };
    }

    async function draw(room, o) {
        o = o || {};
        if (!room || !room.isHost || !room._io) throw new Error('LpFair.draw: host room required');
        attach(room);
        var io = room._io, fs = fstats(room), params = o.params === undefined ? null : o.params;
        var win = Math.max(300, Math.min(5000, o.window || 1500));
        var exclude = [];
        for (var attempt = 0; attempt < 3; attempt++) {
            var round = (fs.round = (fs.round || 0) + 1);
            var hs = rand(32), hsHex = hex(hs), ph = phOf(params), C = commitOf(room.code, round, ph, hsHex);
            fs.pend = { round: round, hs: hsHex, C: C, ph: ph, params: params, hidden: !!o.hidden, t: Date.now() };
            io.save && io.save();
            var r = await collect(room, round, C, ph, params, win, o.hidden ? 'deal0' : 'commit');
            r.L = r.L.filter(function (p) { return exclude.indexOf(p) < 0 || r.N[p]; });
            if (r.missing.length) {
                fs.aborts++;
                await io.sendH('fair', { k: 'abort', round: round, by: 'guest', reason: 'no_reveal', who: r.missing }, { reliable: true });
                io.emit('fair', { k: 'abort', round: round, by: 'guest', reason: 'no_reveal', who: r.missing });
                exclude = exclude.concat(r.missing);
                continue;
            }
            var solo = !r.L.length;
            var st = solo ? room.clock() : room.clock() + 900;
            var body = { code: room.code, round: round, C: C, ph: ph, hs: o.hidden ? '' : hsHex, L: r.L, N: r.N, st: st };
            var rsig = await io.sign(revealBody(body));
            fs.draws++;
            var certO = makeCert(room, { round: round, params: params, C: C, hs: body.hs, ph: ph, L: r.L, N: r.N, Hh: r.Hh, S: r.S, K: r.K, rsig: rsig, st: st, draws: fs.draws, aborts: fs.aborts });
            if (o.hidden) {
                var Gs = gOf(r.N);
                fs.deal = { round: round, hs: hsHex, C: C, ph: ph, G: Gs };
                delete fs.pend; io.save && io.save();
                await io.sendH('fair', { k: 'deal', round: round, C: C, ph: ph, L: r.L, N: r.N, H: r.Hh, S: r.S, K: r.K, st: st, rsig: rsig, G: Gs }, { reliable: true });
                io.emit('fair', { k: 'deal', round: round, G: Gs });
                return { seed: dealSeed(hsHex, Gs), round: round, cert: certO, startAt: st, hostSeed: hs, G: Gs };
            }
            delete fs.pend; io.save && io.save();
            await io.sendH('fair', { k: 'reveal', round: round, hs: hsHex, L: r.L, N: r.N, H: r.Hh, S: r.S, K: r.K, st: st, rsig: rsig }, { reliable: true });
            var seed = seedOf(C, hsHex, r.N);
            io.emit('fair', { k: 'reveal', round: round, seed: seed, startAt: st, cert: certO, ok: true, mine: true, solo: solo });
            fs.last = { round: round };
            return { seed: seed, round: round, cert: certO, startAt: st };
        }
        throw new Error('LpFair.draw: aborted 3 times');
    }

    /* 멤버 쪽 자동 응답 + 검증 (방마다 1회 부착) */
    function attach(room) {
        if (!room || !room._io || room._lpfAttached) return;
        room._lpfAttached = true;
        var io = room._io, rounds = {};
        io.on('fair', function (from, d) {
            if (io.isHost || from !== null || !d || typeof d.round !== 'number' && d.k !== 'chain0') return;
            handleGuest(room, rounds, d);
        });
        /* 방장: 목격 집계 — 게스트 hb 의 w:{r,h} */
        room.on('hb', function (from, d) {
            if (!d || !d.w) return;
            if (io.isHost && from) {
                var W = room._lpfW || (room._lpfW = {});
                var w = d.w; if (typeof w.r !== 'number' || typeof w.h !== 'string') return;
                var e = W[w.r] || (W[w.r] = { mine: null, seen: {} });
                e.seen[from] = w.h; tallyHost(room, w.r);
            } else if (!io.isHost && from === null && typeof d.w.r === 'number' && typeof d.w.ok === 'number') {
                var key = d.w.r + ':' + d.w.ok + ':' + d.w.bad;
                if (room._lpfLastW === key) return; room._lpfLastW = key;
                io.emit('fair', { k: 'witness', round: d.w.r, ok: d.w.ok, bad: d.w.bad | 0 });
            }
        });
    }
    function tallyHost(room, round) {
        var e = room._lpfW && room._lpfW[round]; if (!e || !e.mine) return;
        var ok = 1, bad = 0;
        Object.keys(e.seen).forEach(function (p) { if (e.seen[p] === e.mine) ok++; else bad++; });
        room.hb('w', { r: round, ok: ok, bad: bad }, { soon: true });
        room._io.emit('fair', { k: 'witness', round: round, ok: ok, bad: bad });
    }

    async function handleGuest(room, rounds, d) {
        var io = room._io, me = room.me.pid, R = rounds[d.round] || (rounds[d.round] = {}), fs = fstats(room);
        if (d.k === 'commit' || d.k === 'deal0') {
            if (R.commit) return;
            R.commit = d; R.t = Date.now();
            if (typeof d.C !== 'string' || phOf(d.params) !== d.ph) { R.bad = 'params'; }
            var mem = room.roster().filter(function (m) { return m.p === me; })[0];
            if (mem && mem.r !== 'bot' && !R.bad) {
                var n = hex(rand(16)), h = nHash(d.round, me, n);
                R.n = n; R.h = h;
                var zs = await io.sign(gcMsg(room.code, d.round, h));
                io.sendG('fair', { k: 'c', round: d.round, h: h, zs: zs });
            }
            io.emit('fair', { k: 'commit', round: d.round, params: d.params, C: d.C });
            /* 방장이 공개를 보류하면(결과 보고 버리기) — 모든 화면에 취소 표시 */
            var lim = (d.win || 1500) + 1500 + 3000;
            R.timer = setTimeout(function () {
                if (R.done) return; R.done = true; fs.aborts++;
                io.emit('fair', { k: 'abort', round: d.round, by: 'host', reason: 'no_reveal' });
            }, lim);
        } else if (d.k === 'lock') {
            if (!Array.isArray(d.L)) return;
            R.L = d.L;
            if (R.n && d.L.indexOf(me) >= 0) io.sendG('fair', { k: 'r', round: d.round, n: R.n });
            io.emit('fair', { k: 'lock', round: d.round, L: d.L });
        } else if (d.k === 'abort') {
            if (R.done) return; R.done = true; clearTimeout(R.timer);
            if (d.by === 'guest') { /* 방장이 이미 셌다 — 내 통계엔 1 */ }
            fs.aborts++;
            io.emit('fair', { k: 'abort', round: d.round, by: d.by === 'guest' ? 'guest' : 'host', reason: String(d.reason || ''), who: Array.isArray(d.who) ? d.who : undefined });
        } else if (d.k === 'reveal' || d.k === 'deal') {
            if (R.done) return; R.done = true; clearTimeout(R.timer);
            var c = R.commit || {};
            var o = { code: room.code, round: d.round, C: c.C, ph: c.ph, hs: d.k === 'deal' ? '' : d.hs, L: d.L || [], N: d.N || {}, st: d.st };
            var why = null;
            if (!R.commit) why = 'no_commit';
            else if (R.bad) why = R.bad;
            else if (d.k === 'reveal' && commitOf(room.code, d.round, c.ph, d.hs) !== c.C) why = 'commit';
            else if (!(await verifySig(io.hostPk(), revealBody(o), d.rsig))) why = 'host_sig';
            else {
                for (var i = 0; i < o.L.length && !why; i++) {
                    var p = o.L[i];
                    if (!o.N[p] || nHash(d.round, p, o.N[p]) !== (d.H && d.H[p])) why = 'guest_commit';
                    else if (!d.K || pidOf(d.K[p]) !== p) why = 'guest_key';
                }
            }
            var mine = !R.n || (o.L.indexOf(me) >= 0 && o.N[me] === R.n);
            if (!why && R.n && R.L && R.L.indexOf(me) >= 0 && !mine) why = 'my_nonce';
            fs.draws++;
            var certO = { v: 1, g: room.gameId, code: room.code, round: d.round, params: c.params, C: c.C, hs: o.hs, ph: c.ph, L: o.L, N: o.N,
                H: d.H || {}, S: d.S || {}, K: d.K || {}, rpk: io.rpk(), chain: io.chain() || undefined, rsig: d.rsig, st: d.st, t: Date.now(),
                stats: { draws: fs.draws, aborts: fs.aborts } };
            if (d.k === 'deal') {
                R.G = d.G;
                if (!why && gOf(o.N) !== d.G) why = 'G';
                io.emit('fair', { k: 'deal', round: d.round, G: d.G, ok: !why, why: why || undefined, cert: certO });
                return;
            }
            var seed = seedOf(c.C || '', d.hs || '', o.N);
            io.emit('fair', { k: 'reveal', round: d.round, seed: seed, startAt: d.st, cert: certO, ok: !why, why: why || undefined, mine: mine, solo: !o.L.length });
        } else if (d.k === 'dealR') {
            var c2 = R.commit || {};
            var ok = !!R.commit && commitOf(room.code, d.round, c2.ph, d.hs) === c2.C;
            io.emit('fair', { k: 'dealR', round: d.round, hs: d.hs, ok: ok, seed: ok && R.G ? dealSeed(d.hs, R.G) : undefined });
        } else if (d.k === 'chain0') {
            room._lpfChain = { s0: d.s0, len: d.len };
            io.emit('fair', { k: 'chain0', s0: d.s0, len: d.len });
        }
    }

    /* ── chain (연속 사건) ───────────────────────────────────── */
    var _chainMem = {};   /* code → 배열 캐시 */
    function chainArr(room) {
        var st = room._io.store(); var c = st.chain; if (!c) throw new Error('LpFair.chain: create first');
        var memo = _chainMem[room.code];
        if (memo && memo.sK === c.sK) return memo.a;
        var a = new Array(c.len + 1); a[c.len] = unhex(c.sK);
        for (var i = c.len; i > 0; i--) a[i - 1] = sha256(a[i]);
        _chainMem[room.code] = { sK: c.sK, a: a };
        return a;
    }
    function curRoom() { var R = G.LpRooms && G.LpRooms.current && G.LpRooms.current(); if (!R || !R.isHost) throw new Error('LpFair.chain: no host room'); return R; }
    var chain = {
        create: async function (room, len) {
            len = Math.max(1, Math.min(100000, len | 0));
            var st = room._io.store(); st.chain = { sK: hex(rand(32)), len: len };
            var a = chainArr(room), s0 = hex(a[0]);
            st.chain.s0 = s0; room._io.save && room._io.save();
            await room._io.sendH('fair', { k: 'chain0', s0: s0, len: len }, { reliable: true });
            room._io.emit('fair', { k: 'chain0', s0: s0, len: len });
            return { s0: s0 };
        },
        reveal: function (i) { var a = chainArr(curRoom()); if (i < 1 || i >= a.length) throw new Error('chain index'); return hex(a[i]); },
        event: async function (i, n) { return chain.value(chain.reveal(i), n); },
        value: function (sI, n) { var nn = n == null ? '' : (typeof n === 'string' ? n : hex(n)); return H('lpf1-e|' + String(sI) + '|' + nn); },
        verify: function (s0, sI, i) {
            if (!/^[0-9a-f]{64}$/.test(String(sI)) || !(i >= 1)) return false;
            var x = unhex(sI); for (var k = 0; k < i; k++) x = sha256(x);
            return hex(x) === String(s0);
        }
    };

    /* ── deal (숨김 배분) ───────────────────────────────────── */
    var deal = {
        begin: async function (room) {
            var r = await draw(room, { params: { deal: true, g: room.gameId }, hidden: true });
            return { hostSeed: r.hostSeed, G: r.G, seed: r.seed, round: r.round };
        },
        reveal: function (room) {
            var st = room._io.store(); if (!st.deal) return;
            room._io.sendH('fair', { k: 'dealR', round: st.deal.round, hs: st.deal.hs }, { reliable: true });
            room._io.emit('fair', { k: 'dealR', round: st.deal.round, hs: st.deal.hs, ok: true, seed: dealSeed(st.deal.hs, st.deal.G) });
        },
        verify: function (c) { return !!c && commitOf(c.code, c.round, c.ph, c.hs) === c.C; }
    };

    function witness(room, round, result) {
        if (!room || !room._io) return;
        var rh = resHash(result);
        if (room._io.isHost) {
            var W = room._lpfW || (room._lpfW = {});
            var e = W[round] || (W[round] = { mine: null, seen: {} });
            e.mine = rh; tallyHost(room, round);
        } else room.hb('w', { r: round, h: rh }, { soon: true });
    }

    function badge(el, info) {
        if (!el) return;
        info = info || {};
        var k = info.kind || 'solo';
        var txt = k === 'verified' ? '✓ ' + (info.n || '') : k === 'seed' ? '✓ 🎲' : k === 'mismatch' ? '⚠ ' + (info.n || '') : '🎲';
        el.textContent = txt.trim();
        el.className = (el.className || '').replace(/\blpf-\S+/g, '').trim() + ' lpf-badge lpf-' + k;
        el.setAttribute('data-kind', k);
        if (info.n != null) el.setAttribute('data-n', String(info.n));
        if (info.round != null) el.setAttribute('data-round', String(info.round));
        el.setAttribute('role', 'status');
        el.setAttribute('aria-label', k === 'verified' ? 'fair draw, ' + (info.n || 0) + ' devices agree' : k === 'mismatch' ? 'result differs on ' + (info.n || 0) + ' device(s)' : k === 'seed' ? 'fair seed' : 'solo draw');
        el._lpfCert = info.cert || null;
    }

    var DRAND_CHAIN = '52db9ba70e0cc0f6eaf7803dd07447a1f5477735fd3f661792ba94600c84e971';
    var beacon = {
        at: async function (round) {
            var urls = ['https://api.drand.sh/' + DRAND_CHAIN + '/public/' + round, 'https://drand.cloudflare.com/' + DRAND_CHAIN + '/public/' + round];
            var rs = await Promise.all(urls.map(function (u) { return fetch(u).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }));
            var got = rs.filter(Boolean);
            if (!got.length) throw new Error('beacon unavailable');
            if (got.length === 2 && got[0].randomness !== got[1].randomness) throw new Error('beacon mismatch');
            return { randomness: got[0].randomness, round: got[0].round };
        }
    };

    G.LpFair = {
        version: '2.0.0',
        draw: draw, rng: rng, chain: chain, deal: deal, cert: cert, witness: witness, badge: badge, beacon: beacon,
        H: H, hex: hex, unhex: unhex, canon: canon, outcomes: outcomes,
        _attach: attach,
        _t: { sha256: sha256, pidOf: pidOf, codeOfF: codeOfF, roomF: roomF, commitOf: commitOf, nHash: nHash, seedOf: seedOf, revealBody: revealBody, gcMsg: gcMsg, phOf: phOf, resHash: resHash, b64u: b64u, ub64u: ub64u, chainKey: chainKey, gOf: gOf, dealSeed: dealSeed }
    };
    /* 코어가 먼저 떠 있으면 현재·이후 방에 자동 부착 */
    try {
        if (G.LpRooms && G.LpRooms.on) {
            G.LpRooms.on('room', attach);
            var cur = G.LpRooms.current && G.LpRooms.current(); if (cur) attach(cur);
        }
    } catch (_) {}
})(typeof window !== 'undefined' ? window : globalThis);
/* CHANGE LOG
   2026-09-30  API freeze (stub).
   2026-09-30  구현: 동기 SHA-256·sfc32·draw(커밋-공개, 참가자 엔트로피, 게스트 미공개 재시도, 방장 보류 취소 표시)·
               chain·deal·cert(deflate-raw)·witness(hb 편승)·badge(최소 DOM)·beacon(drand, 기본 OFF).
               [+] outcomes·H·hex·canon·witness·chain.reveal/value 추가(기존 항목 불변).
*/
