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
    if (G.LpFair && G.LpFair.version) return;
    var NI = function () { return Promise.reject(new Error('LpFair: not implemented yet (API freeze stub)')); };
    G.LpFair = { version: '2.0.0-stub', draw: NI, rng: function () { throw new Error('stub'); },
        chain: { create: NI, event: NI, reveal: function () { return ''; }, value: function () { return new Uint8Array(32); }, verify: function () { return false; } },
        deal: { begin: NI, reveal: function () {}, verify: function () { return false; } },
        cert: { encode: NI, decode: NI, verify: NI }, witness: function () {}, badge: function () {} };
})(typeof window !== 'undefined' ? window : globalThis);
/* CHANGE LOG
   2026-09-30  API freeze (stub).
*/
