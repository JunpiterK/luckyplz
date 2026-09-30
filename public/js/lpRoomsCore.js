/* =====================================================================
   lpRoomsCore.js — LuckyPlz Rooms v2 커널 (P1)
   설계: docs/multiplayer/DESIGN.md §2·§3·§6.0·§8  (이 파일이 §8.1·§8.2 의 구현)

   ── API 동결 (2026-09-30, "rooms-v2: API freeze") ─────────────────────
   다른 패키지(P2 UI · P3 추첨 · P4 턴 · P5 레이스)는 아래 계약만 보고 병렬로 만든다.
   바꿔야 하면 맨 아래 CHANGE LOG 에 적고 하위 호환을 유지한다.
   [+] 표시는 §8 원문에 없던 추가 항목(원문 항목은 전부 그대로 있음).

   declare global { interface Window { LpRooms: LpRooms } }

   type Role   = 'host' | 'player' | 'spec' | 'bot';
   type Conn   = 'on' | 'away' | 'off';
   type Phase  = 'lobby' | 'starting' | 'playing' | 'paused' | 'result';
   type Kind   = 'draw' | 'turn' | 'realtime' | 'db' | 'race' | 'lobby';
   type LateJoin = 'anytime' | 'nextRound' | 'takeBot' | 'spectate';

   interface Member {
     p: string;            // pid = 'p' + base32(SHA-256("lpr2-dev"‖raw(sig.pub)))[0..19]  (위조 불가)
     n: string;            // 닉네임(방장이 위생 처리·중복 해소한 확정값)
     av: number;           // 아바타 인덱스 0..15
     r: Role;
     seat: number | null;  // 어댑터 좌석(없으면 null)
     pick: {[key:string]: string};   // 게임별 선택(캐릭터·색 …)
     rd: boolean;          // 준비
     c: Conn;              // 연결(방장이 판정: §6.0.4)
     j: number;            // 합류 시각(방장 시계 ms) — succ 순서 기준
     au?: {uid:string, name:string} | null;   // 로그인 사용자 표시(✓) — Phase A 에선 자기 신고
     afk?: boolean;
     k?: {sig:string, dh:string};    // [+] 기기 공개키(raw b64url) — 승계 시 새 방장이 서명 검증에 사용
   }

   interface S {                     // 방장 권위 상태 (§6.0.1)
     v: 2; seq: number; phase: Phase; gameId: string;
     opts: object; startAt: number | null;       // startAt = 방장 시계 ms
     roster: Member[];
     succ: string[]; succz?: string;             // 승계 순서 + 방장 서명 [+succz]
     lock: boolean; appr: boolean; pinReq: boolean;
     turn: {seat:number, n:number, deadline:number} | null;
     fair: object | null;
     log: any[];                                  // 최근 64개
     game: any;                                   // 어댑터 상태 (view 가 있으면 pub 부분만)
     bans?: string[];                             // [+] 차단 pid (봉인 상태로만 전달 — 승계자가 이어받음)
     inv?: string;                                // [+] 링크 토큰(봉인 모드에서만 멤버에게 전달 → 멤버도 초대 가능)
     mem?: {[gameId:string]: {[pid:string]: {pick?:object, seat?:number}}};   // [+] 게임별 선택 기억
     hbx?: number;                                // [+] 게스트 hb 주기 배율(예산 가드)
   }

   interface JoinStatus { st: 'probing'|'joining'|'pending'|'member'|'retry', code: string, hello?: object }

   interface AdapterSpec {
     gameId: string; kind: Kind;
     seats?: [number, number] | null;   // [최소, 최대] 좌석. null = 좌석 없음(전원 참가자)
     max?: number;                      // 방 정원(관전 포함, 기본 12, 상한 12)
     lateJoin?: LateJoin;               // 기본 'anytime'
     picks?: {key:string, options:string[], unique?:boolean, botYield?:boolean}[];
     options?: {key:string, values:any[], def:any}[];
     bots?: boolean; hiddenInfo?: boolean;
     migratable?: boolean | ((S:S) => boolean);   // 대기실·결과 단계는 항상 승계 가능
     delta?: boolean;                   // true 면 state 대신 delta 방송(10번마다 전체)
     commutes?(a:string): boolean;      // expectSeq 불일치여도 수락할 의도
     canStart?(roster:Member[], S:S): boolean;
     view?(game:any, pid:string|null): {pub:any, priv?:any};   // 숨은 정보: pid=null 이면 공개분만
     initGame?(S:S): any;               // [+] 방 생성 시 S.game 초기값
     host?: object; client?: object;    // lpRoomsTurn/lpRoomsRace 가 해석 (커널은 보관만)
   }

   interface LpRooms {
     version: string;                                        // [+] '2.0.0'
     ready(): Promise<void>;
     identity(): Promise<{pid:string, tid:string}>;
     profile: { get(): {nick:string, av:number}; set(p:{nick?:string, av?:number}): {nick:string, av:number} };
     create(o:{gameId:string, opts?:object, pinReq?:boolean, pin?:string, appr?:boolean, max?:number, sealed?:boolean}): Promise<Room>;
     join(o:{code:string, inv?:{fp:string, tok?:string}, pin?:string, want?:'play'|'watch',
             steal?:boolean (*[+] "여기서 계속" *), onStatus?(s:JoinStatus):void (*[+]*)}): Promise<Room>;
          // 거절 = Error{reason, gameId?, url?}. reason:
          //  'not_found' | 'host_conflict'(응답 2개) | 'bad_fp' | 'bad_proof' | 'locked' | 'full' | 'banned' | 'rate'
          //  | 'version' | 'closed' | 'denied'(승인 거절) | 'wrong_game'(gameId·url 동봉 → UI 가 이동)
          //  | 'pin_required'(PIN 켠 방 + 토큰 없음 → PIN 받아 다시 join) | 'other_tab'(→ steal:true 로 다시) | 'unsupported'
          //  | 'inapp'(인앱 브라우저 탈출 예정 — 탈출 뒤 다시) | 'network' | 'error'      [+]
          //  create 거절: 'bad_game'(레지스트리에 없음) | 'collision'(5회 충돌) | 'network' | 'inapp'  [+]
          //  'pending'(승인 대기)은 거절이 아니다 — onStatus({st:'pending'}) 후 방장 결정까지 promise 유지(최대 3분)
     resolve(input:string): Promise<{kind:'rooms'|'rooms-v1'|'qlive'|'szx'|'choice'|'none', code:string,
             gameId?:string, url?:string, hello?:object, options?:{kind:string, url:string}[] (*[+] kind='choice'*)}>;
     parseInvite(hrefOrText:string): {code:string, inv?:{fp:string, tok?:string}, hint?:'v2'|'v1'|'qlive'|'szx'} | null;
     resume(): Promise<Room|null>;
     current(): Room|null;
     adapter(spec:AdapterSpec): void;
     getAdapter(): AdapterSpec|null;                         // [+]
     on(ev:'room'|'left'|'status', cb:(x:any)=>void): () => void;
     config(o:{client?:any, navigate?:(url:string)=>void, autoNav?:boolean, origin?:string,
               debug?:boolean, testKeys?:any[] (* localhost 전용 *)}): void;        // [+] UI·테스트 훅
     util: {                                                  // [+] 공용 도구(lpFair·UI 가 재사용)
       b64u(u8:Uint8Array):string; ub64u(s:string):Uint8Array; hex(u8:Uint8Array):string;
       sha256(u8|string):Promise<Uint8Array>; canon(o:any):string;
       fmtCode(code:string):string (* 'K7M-2QX' *); normCode(s:string):string|null;
       cleanNick(s:string):string; seal(F:Uint8Array):string (* 봉인 이모지 3개 *);
       verify(pkSigB64:string, msg:string, sigB64:string):Promise<boolean>;
       pidOf(pkSigB64:string):Promise<string>;
     };
     stats(): {sent:number, recv:number, estPerSec:number, bad:number};   // [+] 디버그·예산 가드
   }

   interface Room {
     code: string; gameId: string; isHost: boolean; ep: number;
     me: {pid:string, role:Role, seat:number|null};
     fp: string;        // [+] 방장 키 지문(22자) — 초대 링크 #k= 의 앞부분
     seal: string;      // [+] 봉인 이모지 3개(모든 기기 동일)
     sealed: boolean;   // [+]
     roster(): Member[];  state(): S;  clock(): number;      // clock = 방장 시계 ms
     on(ev:'roster'|'state'|'phase'|'priv'|'fair'|'x'|'react'|'hostlost'|'hostback'|'takeover'|'kicked'|'closed'|'detached'
           | 'hb' | 'tick' | 'switch' | 'pending' | 'net' (*[+]*), cb:(...a:any[])=>void): () => void;
          // 콜백 인자:
          //  roster(roster:Member[], d:{join:string[], left:string[], back:string[]})   (늦게 붙은 리스너는 마지막 값 즉시 재생)
          //  state(S, prev)  · phase(phase, S)  · priv(d, e)  · fair(ev)  · x(k, d, fromPid|null(방장))  · react(i, fromPid)
          //  hostlost({level:1|2|3})  1=확인 중(12s) 2=끊김(20s) 3=승계 불가 대기   · hostback()
          //  takeover({pid, ep})  · kicked({ban})  · closed({reason:'host'|'host_gone'|'replaced'|'left'})  · detached()
          //  hb(fromPid|null, d) [+]  · tick(d) [+]  · switch({gameId, url}) [+]  · pending(list) [+ 방장]  · net({ok}) [+]
          //  join(member) [+ 방장: 새 사람]  · demoted({by}) [+ 방장이 승계 사실을 알고 게스트로 합류]  · pinflood({until}) [+ 방장]
     intent(a:string, x?:any, o?:{expectSeq?:number}): Promise<{ok:true, seq:number} | {ok:false, reason:string}>;
          // 커널 내장 의도: 'ready'(x:boolean) · 'pick'(x:{key,val}) · 'role'(x:'play'|'watch') · 'back'(afk 해제)
          // 나머지는 방장의 onIntent 로 전달
     x(k:string, d:any): void;
     react(i:number): void;  leave(): void;  inviteUrl(): string;
     hb(k:string, v:any): void;   // [+] 다음 하트비트에 편승할 필드(w·sc·bd …) — 추가 메시지 0
     canStart(): boolean;         // [+] 기본 게이트(좌석≥min ∧ 좌석 게스트 전원 준비·온라인) 또는 adapter.canStart
     // ── 방장 전용 ──
     setState(fn:(S:S)=>void|S, o?:{full?:boolean}): number;
     onIntent(cb:(from:Member, a:string, x:any, ctx:{c:number, es?:number}) => void | false | {reject:string} | Promise<any>): void;
          // 반환 false / {reject} → nack(reason). 그 외 → 처리 중 setState 가 있으면 그 방송이 수락 응답, 없으면 ack
     sendTo(pid:string, e:string, d:any): void;   // ECIES 비공개 → 받는 쪽 on('priv')(d, e)
     tick(d:any): void;                          // 틱 모드 전용(최대 20Hz, 초과분 버림)
     start(o?:{countdownMs?:number}): void;  toLobby(): void;  switchGame(gameId:string): void;
     pause(): void;  resume(): void;  end(): void;  close(): void;
     kick(pid:string, o?:{ban?:boolean}): void;  unban(pid:string): void;
     lock(on:boolean): void;  approval(on:boolean): void;  approve(pid:string, ok:boolean): void;
     transferHost(pid:string): void;  rotateLink(): void;
     setPin(on:boolean, pin?:string): string | null;   // [+] 방장: PIN 켜기/끄기(pin 생략 = 기존 PIN 유지 또는 새 4자리) → 현재 PIN
     setApproval(on:boolean): boolean;            // [+] 방장: approval(on) 과 같음(이름 통일용)
     pin?: string;                                // [+] 방장: 현재 PIN(pinReq 일 때)
     pending(): {p:string, n:string, av:number, flag?:'banned_nick'}[];   // [+] 승인 대기
   }

   ── 와이어 (채널 lpr-<CODE>, 이벤트 'h'/'g' 두 개뿐) ──────────────────
   h: {v:2, e, ep, s|t, to?, id?, j|c:{k,iv,ct}, z}      서명 "lpr2|h|code|ep|s 또는 t<t>|e|to정렬|j 또는 iv.ct"
   g: {v:2, e, p, c, j|y:{k,iv,ct}, z}                    서명 "lpr2|g|code|pid|c|e|j 또는 iv.ct"   (hello_req 만 무서명)
   (게스트 봉인문은 c 가 순번이라 y 필드를 쓴다 — §3.2 원문과의 유일한 차이)
   ===================================================================== */
(function (G) {
    'use strict';
    if (G.LpRooms && G.LpRooms.version && G.LpRooms.version.indexOf('stub') < 0) return;

    /* ── 상수 (§6.0.3·§6.0.4·§6.0.5 타이밍) ───────────────────── */
    var VER = '2.0.0';
    var PFX = 'lpr-';
    var MAXJ = 32768, ROOM_MAX = 12;
    var TM = {
        hostHb: 5000, hostHbAlone: 15000, gLobby: 20000, gPlay: 8000, gHidden: 30000,
        wd1: 12000, wd2: 20000, wd3: 30000, wdEnd: 300000,
        offLobby: 45000, offLobbyHidden: 90000, rmLobby: 120000, offPlay: 20000, offSpec: 60000,
        helloGap: 300, rosterGap: 100, snapWait: 250, snapPer: 2000, conflictWin: 400, collideWin: 1200,
        resend: [200, 400, 600], joinRetry: [2000, 4000, 7000], joinTimeout: 10000, pendingMax: 180000
    };
    var SUPA_URL = 'https://jkrpxijybuljdxkrbsan.supabase.co';
    var SUPA_KEY = 'sb_publishable_Ypa1NMQCVGxFWidBOd5iEA_ECBldTAb';
    var A30 = '23456789ABCDEFGHJKMNPQRSTVWXYZ';
    var CODE_RE = /^[2-9A-HJKMNP-TV-Z]{6}$/;
    var PID_RE = /^p[a-z2-7]{20}$/;
    var SEAL_EMOJI = ['🍋', '🐼', '🚀', '🎲', '🍀', '⭐', '🎈', '🍩', '🐯', '🦊', '🐰', '🐶', '🐱', '🐸', '🐧', '🦄',
        '🍓', '🍉', '🍒', '🍇', '🥝', '🍄', '🌵', '🌻', '🌙', '☀️', '⚡', '🔥', '❄️', '🌈', '💎', '🎁',
        '🎸', '🎺', '🥁', '🎯', '🏀', '⚽', '🎳', '🛼', '🚗', '🚲', '⛵', '✈️', '🛸', '🏰', '🗿', '🎡',
        '🍕', '🍔', '🌮', '🍣', '🍦', '🧁', '🍪', '🥨', '🐙', '🦋', '🐢', '🐳', '🦉', '🐝', '🦖', '🐞'];
    var HOST_EV = { hello: 1, welcome: 1, deny: 1, roster: 1, state: 1, delta: 1, priv: 1, nack: 1, ack: 1, hb: 1, tick: 1, phase: 1, 'switch': 1, kicked: 1, rekey: 1, close: 1, fair: 1, x: 1, react: 1, th: 1 };
    var PLAIN_H = { hello: 1, deny: 1, welcome: 1, rekey: 1 };
    var T_EV = { hb: 1, hello: 1, tick: 1 };

    /* ── 바이트·문자열 도구 ─────────────────────────────────── */
    var TE = new TextEncoder(), TD = new TextDecoder();
    function utf8(s) { return TE.encode(String(s)); }
    function cat() { var a = Array.prototype.slice.call(arguments).map(function (p) { return typeof p === 'string' ? utf8(p) : p; }); var n = 0; a.forEach(function (p) { n += p.length; }); var o = new Uint8Array(n), k = 0; a.forEach(function (p) { o.set(p, k); k += p.length; }); return o; }
    var HEXC = '0123456789abcdef';
    function hex(u8) { var s = ''; for (var i = 0; i < u8.length; i++) s += HEXC[u8[i] >> 4] + HEXC[u8[i] & 15]; return s; }
    function b64u(u8) { var s = ''; for (var i = 0; i < u8.length; i++) s += String.fromCharCode(u8[i]); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }
    function ub64u(s) { s = String(s || '').replace(/-/g, '+').replace(/_/g, '/'); while (s.length % 4) s += '='; var b = atob(s), o = new Uint8Array(b.length); for (var i = 0; i < b.length; i++) o[i] = b.charCodeAt(i); return o; }
    function rand(n) { var u = new Uint8Array(n); G.crypto.getRandomValues(u); return u; }
    function rid(n) { return b64u(rand(n || 4)); }
    function now() { return Date.now(); }
    function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
    function clone(o) { return o === undefined ? undefined : JSON.parse(JSON.stringify(o)); }
    function canon(o) {
        if (o === null || typeof o !== 'object') return o === undefined ? 'null' : JSON.stringify(o);
        if (Array.isArray(o)) return '[' + o.map(function (x) { return x === undefined ? 'null' : canon(x); }).join(',') + ']';
        var ks = Object.keys(o).filter(function (k) { return o[k] !== undefined; }).sort();
        return '{' + ks.map(function (k) { return JSON.stringify(k) + ':' + canon(o[k]); }).join(',') + '}';
    }
    function isLocalDev() { try { return /^(localhost|127\.0\.0\.1|\[::1\])$/.test(G.location.hostname) || /\.(localhost|test)$/.test(G.location.hostname); } catch (_) { return false; } }
    function lsGet(k) { try { return G.localStorage.getItem(k); } catch (_) { return null; } }
    function lsSet(k, v) { try { if (v == null) G.localStorage.removeItem(k); else G.localStorage.setItem(k, v); } catch (_) {} }
    function ssGet(k) { try { return G.sessionStorage.getItem(k); } catch (_) { return null; } }
    function ssSet(k, v) { try { if (v == null) G.sessionStorage.removeItem(k); else G.sessionStorage.setItem(k, v); } catch (_) {} }
    function jparse(s, d) { try { var v = JSON.parse(s); return v == null ? d : v; } catch (_) { return d; } }
    var _cfg = { client: null, navigate: null, autoNav: true, origin: null, debug: false, testKeys: null };
    function dbg() { if (_cfg.debug || lsGet('lpDebug') === '1') { try { console.log.apply(console, ['[lpr]'].concat(Array.prototype.slice.call(arguments))); } catch (_) {} } }
    var STATS = { sent: 0, recv: 0, bad: 0, win: [] };
    function statTick(kind) { STATS[kind]++; var t = now(); STATS.win.push(t); while (STATS.win.length && t - STATS.win[0] > 60000) STATS.win.shift(); }

    /* ── 에미터(늦게 붙은 리스너에 마지막 값 재생 — realtime 함정 #1) ── */
    function Emitter(cacheable) { this._l = {}; this._c = {}; this._cc = cacheable || {}; }
    Emitter.prototype.on = function (ev, cb) {
        var self = this, arr = this._l[ev] || (this._l[ev] = []), live = true;
        var w = function () { if (live) cb.apply(null, arguments); };
        arr.push(w);
        if (this._cc[ev] && this._c[ev]) { var args = this._c[ev]; Promise.resolve().then(function () { if (live) { try { cb.apply(null, args); } catch (e) { dbg('listener', e); } } }); }
        return function () { live = false; var a = self._l[ev]; if (a) { var i = a.indexOf(w); if (i >= 0) a.splice(i, 1); } };
    };
    Emitter.prototype.emit = function (ev) {
        var args = Array.prototype.slice.call(arguments, 1);
        if (this._cc[ev]) this._c[ev] = args;
        (this._l[ev] || []).slice().forEach(function (f) { try { f.apply(null, args); } catch (e) { dbg('listener err', ev, e); } });
    };
    var GLOBAL = new Emitter({ room: 1 });

    /* ── WebCrypto ──────────────────────────────────────────── */
    var SUB = G.crypto && G.crypto.subtle;
    var EC_S = { name: 'ECDSA', namedCurve: 'P-256' }, EC_D = { name: 'ECDH', namedCurve: 'P-256' }, SIG = { name: 'ECDSA', hash: 'SHA-256' };
    async function sha256(x) { return new Uint8Array(await SUB.digest('SHA-256', typeof x === 'string' ? utf8(x) : x)); }
    async function rawPub(k) { return new Uint8Array(await SUB.exportKey('raw', k)); }
    async function genPair(ext) {
        var s = await SUB.generateKey(EC_S, !!ext, ['sign', 'verify']);
        var d = await SUB.generateKey(EC_D, !!ext, ['deriveBits', 'deriveKey']);
        return { sig: { priv: s.privateKey, pub: b64u(await rawPub(s.publicKey)) }, dh: { priv: d.privateKey, pub: b64u(await rawPub(d.publicKey)) } };
    }
    async function signStr(priv, str) { return b64u(new Uint8Array(await SUB.sign(SIG, priv, utf8(str)))); }
    var _vk = {}, _vkN = 0;
    function vkey(pk) {
        if (!_vk[pk]) { if (++_vkN > 400) { _vk = {}; _vkN = 0; } _vk[pk] = SUB.importKey('raw', ub64u(pk), EC_S, false, ['verify']); }
        return _vk[pk];
    }
    async function verifyStr(pk, str, sig) {
        if (typeof pk !== 'string' || typeof sig !== 'string' || sig.length > 100) return false;
        try { return await SUB.verify(SIG, await vkey(pk), ub64u(sig), utf8(str)); } catch (_) { return false; }
    }
    async function hkdf(bits, salt, info) {
        var ikm = await SUB.importKey('raw', bits, 'HKDF', false, ['deriveKey']);
        return SUB.deriveKey({ name: 'HKDF', hash: 'SHA-256', salt: utf8(salt), info: utf8(info) }, ikm, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
    }
    /* ECIES (§3.2): 임시 ECDH → HKDF(salt=code, info='lpr2-ecies|'+용도) → AES-GCM */
    async function eciesEnc(dhPub, code, purpose, obj) {
        var eph = await SUB.generateKey(EC_D, true, ['deriveBits']);
        var pub = await SUB.importKey('raw', ub64u(dhPub), EC_D, false, []);
        var bits = await SUB.deriveBits({ name: 'ECDH', public: pub }, eph.privateKey, 256);
        var key = await hkdf(bits, code, 'lpr2-ecies|' + purpose);
        var iv = rand(12);
        var ct = new Uint8Array(await SUB.encrypt({ name: 'AES-GCM', iv: iv }, key, utf8(JSON.stringify(obj))));
        return { epk: b64u(await rawPub(eph.publicKey)), iv: b64u(iv), ct: b64u(ct) };
    }
    async function eciesDec(dhPriv, code, purpose, blob) {
        if (!blob || typeof blob.epk !== 'string' || typeof blob.ct !== 'string') throw new Error('ecies');
        var pub = await SUB.importKey('raw', ub64u(blob.epk), EC_D, false, []);
        var bits = await SUB.deriveBits({ name: 'ECDH', public: pub }, dhPriv, 256);
        var key = await hkdf(bits, code, 'lpr2-ecies|' + purpose);
        var pt = await SUB.decrypt({ name: 'AES-GCM', iv: ub64u(blob.iv) }, key, ub64u(blob.ct));
        return JSON.parse(TD.decode(pt));
    }
    async function aesKey(raw) { return SUB.importKey('raw', raw, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']); }
    async function aesSeal(key, kv, str) { var iv = rand(12); var ct = new Uint8Array(await SUB.encrypt({ name: 'AES-GCM', iv: iv }, key, utf8(str))); return { k: kv, iv: b64u(iv), ct: b64u(ct) }; }
    async function aesOpen(key, c) { return TD.decode(await SUB.decrypt({ name: 'AES-GCM', iv: ub64u(c.iv) }, key, ub64u(c.ct))); }

    /* ── 코드·지문·pid ─────────────────────────────────────── */
    var B32 = 'abcdefghijklmnopqrstuvwxyz234567';
    function base32(u8) { var out = '', bits = 0, v = 0; for (var i = 0; i < u8.length; i++) { v = ((v << 8) | u8[i]) & 0xffff; bits += 8; while (bits >= 5) { out += B32[(v >>> (bits - 5)) & 31]; bits -= 5; } } if (bits > 0) out += B32[(v << (5 - bits)) & 31]; return out; }
    async function pidOf(pkSig) { return 'p' + base32(await sha256(cat('lpr2-dev', ub64u(pkSig)))).slice(0, 20); }
    async function roomF(rpk) { return sha256(cat('lpr2-room', ub64u(rpk.sig), ub64u(rpk.dh))); }
    function codeOfF(F) { var x = 0; for (var i = 0; i < 6; i++) x = x * 256 + F[i]; x = x % 729000000; var s = ''; for (var j = 0; j < 6; j++) { s = A30[x % 30] + s; x = Math.floor(x / 30); } return s; }
    function fpOfF(F) { return b64u(F.slice(0, 16)); }
    function sealOfF(F) { var v = (F[6] << 16) | (F[7] << 8) | F[8]; return SEAL_EMOJI[(v >>> 18) & 63] + SEAL_EMOJI[(v >>> 12) & 63] + SEAL_EMOJI[(v >>> 6) & 63]; }
    function hasLetter(c) { return /[A-Z]/.test(c); }
    function fmtCode(c) { c = String(c || ''); return c.length === 6 ? c.slice(0, 3) + '-' + c.slice(3) : c; }
    function normCode(s) { var c = String(s || '').toUpperCase().replace(/[\s\-_.]/g, ''); if (/^\d{6}$/.test(c)) return c; return CODE_RE.test(c) && hasLetter(c) ? c : null; }
    function succMsg(code, ep, succ) { return 'lpr2|succ|' + code + '|' + ep + '|' + (succ || []).join(','); }
    /* 승계 체인 검증 → 최종 서명 키 (lpFair 와 같은 정의) */
    async function chainKey(code, rpk, chain) {
        var key = rpk.sig;
        if (!chain || !chain.length) return key;
        if (!Array.isArray(chain) || chain.length > 8) return null;
        for (var i = 0; i < chain.length; i++) {
            var L = chain[i];
            if (!L || !Array.isArray(L.succ) || !L.npk || typeof L.npk.sig !== 'string') return null;
            if (!(await verifyStr(key, succMsg(code, L.ep, L.succ), L.z))) return null;
            if (L.succ.indexOf(await pidOf(L.npk.sig)) < 0) return null;
            key = L.npk.sig;
        }
        return key;
    }

    /* ── 닉네임 위생 (§2.4) ─────────────────────────────────── */
    var BAD_WORDS = ['fuck', 'shit', 'bitch', 'cunt', 'nigger', 'faggot', '씨발', '시발', '병신', '좆', '개새끼', '느금', 'ちんこ', 'まんこ', 'puta', 'mierda', 'caralho', 'porra', 'buceta'];
    function cleanNick(s) {
        s = String(s == null ? '' : s);
        try { s = s.normalize('NFKC'); } catch (_) {}
        s = s.replace(/[\u0000-\u001F\u007F-\u009F​-‏‪-‮⁠-⁩؜﻿￹-￻]/g, '').replace(/\s+/g, ' ').trim();
        var parts;
        try { parts = Array.from(new Intl.Segmenter(undefined, { granularity: 'grapheme' }).segment(s), function (x) { return x.segment; }); } catch (_) { parts = Array.from(s); }
        s = parts.slice(0, 12).join('').trim();
        var low = s.toLowerCase().replace(/\s/g, '');
        for (var i = 0; i < BAD_WORDS.length; i++) if (low.indexOf(BAD_WORDS[i]) >= 0) return '***';
        return s;
    }
    function nickKey(s) { try { return String(s).normalize('NFKC').toLowerCase().replace(/\s/g, ''); } catch (_) { return String(s).toLowerCase(); } }

    /* ── IndexedDB (lp-id / keys) ───────────────────────────── */
    var _idbP = null;
    function idb() {
        if (!_idbP) _idbP = new Promise(function (res, rej) {
            try { var r = G.indexedDB.open('lp-id', 1); r.onupgradeneeded = function () { r.result.createObjectStore('keys'); }; r.onsuccess = function () { res(r.result); }; r.onerror = function () { rej(r.error); }; } catch (e) { rej(e); }
        });
        return _idbP;
    }
    function idbOp(mode, fn) { return idb().then(function (db) { return new Promise(function (res, rej) { var tx = db.transaction('keys', mode), st = tx.objectStore('keys'), rq = fn(st); tx.oncomplete = function () { res(rq && rq.result); }; tx.onerror = tx.onabort = function () { rej(tx.error); }; }); }); }
    function idbGet(k) { return idbOp('readonly', function (s) { return s.get(k); }); }
    function idbPut(k, v) { return idbOp('readwrite', function (s) { return s.put(v, k); }); }
    function idbDel(k) { return idbOp('readwrite', function (s) { return s.delete(k); }); }

    /* ── 기기 신원 (§2.5) ─────────────────────────────────────
       비추출 CryptoKey 를 IndexedDB 에 그대로 저장. 실패 시 sessionStorage JWK(탭 한정) 폴백.
       ?lpdev=tab (로컬 개발 도메인에서만) → 탭마다 다른 pid */
    var _dev = null, _devP = null;
    var TID = (G.crypto && G.crypto.randomUUID) ? G.crypto.randomUUID() : rid(12);
    async function devFromJwk(o) {
        var sp = await SUB.importKey('jwk', o.sig, EC_S, true, ['sign']);
        var dp = await SUB.importKey('jwk', o.dh, EC_D, true, ['deriveBits', 'deriveKey']);
        return { sig: { priv: sp, pub: o.sigPub }, dh: { priv: dp, pub: o.dhPub } };
    }
    async function devSession() {
        var raw = jparse(ssGet('lpr_dev'), null);
        if (raw) { try { return await devFromJwk(raw); } catch (_) {} }
        var k = await genPair(true);
        var o = { sig: await SUB.exportKey('jwk', k.sig.priv), dh: await SUB.exportKey('jwk', k.dh.priv), sigPub: k.sig.pub, dhPub: k.dh.pub };
        ssSet('lpr_dev', JSON.stringify(o));
        return k;
    }
    function loadDevice() {
        if (_devP) return _devP;
        _devP = (async function () {
            if (!SUB) { var e = new Error('unsupported'); e.reason = 'unsupported'; throw e; }
            var tabMode = false;
            try { tabMode = isLocalDev() && new URLSearchParams(G.location.search).get('lpdev') === 'tab'; } catch (_) {}
            var k = null;
            if (!tabMode) {
                try {
                    var rec = await idbGet('dev');
                    if (rec && rec.sig && rec.sig.priv && rec.dh && rec.dh.priv) k = rec;
                    else {
                        var nk = await genPair(false);
                        nk.t = now();
                        await idbPut('dev', nk);
                        var back = await idbGet('dev');   /* 두 탭이 동시에 만들면 먼저 저장된 쪽을 따른다 */
                        k = (back && back.sig && back.sig.priv) ? back : nk;
                    }
                } catch (err) { dbg('idb fallback', err); k = null; }
            }
            if (!k) k = await devSession();
            _dev = { sig: k.sig, dh: k.dh, pid: await pidOf(k.sig.pub), tid: TID };
            return _dev;
        })();
        return _devP;
    }

    /* ── 프로필 (§2.4) ──────────────────────────────────────── */
    var profile = {
        get: function () {
            var p = jparse(lsGet('lp_profile'), null);
            if (!p || typeof p !== 'object') {
                var n = lsGet('luckyplz_nick') || lsGet('lp_qlive_nick') || lsGet('szx_nick') || '';
                p = { nick: cleanNick(n), av: 0, v: 1 };
            }
            return { nick: cleanNick(p.nick || ''), av: Math.max(0, Math.min(15, p.av | 0)) };
        },
        set: function (q) {
            var p = profile.get();
            if (q && q.nick !== undefined) p.nick = cleanNick(q.nick);
            if (q && q.av !== undefined) p.av = Math.max(0, Math.min(15, q.av | 0));
            lsSet('lp_profile', JSON.stringify({ nick: p.nick, av: p.av, v: 1 }));
            return p;
        }
    };

    /* ── supabase 클라이언트 · 채널 관리자 ───────────────────────
       같은 토픽을 두 번 channel() 하면 realtime-js 가 기존 객체를 돌려준다(2.104 확인) →
       토픽 단위 참조 계수로 공유하고, 해제 중이면 끝날 때까지 기다렸다 새로 만든다. */
    var _ownClient = null;
    function sbClient() {
        if (_cfg.client) return _cfg.client;
        if (typeof G.getSupabase === 'function') { try { var c = G.getSupabase(); if (c) return c; } catch (_) {} }
        if (G.supabase && typeof G.supabase.createClient === 'function') {
            if (!_ownClient) _ownClient = G.supabase.createClient(SUPA_URL, SUPA_KEY, { auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false } });
            return _ownClient;
        }
        return null;
    }
    var _topics = {};
    async function openTopic(topic) {
        var T = _topics[topic];
        while (T && T.closing) { await T.closing; T = _topics[topic]; }
        if (!T) {
            var sb = sbClient();
            if (!sb) { var e = new Error('no_client'); e.reason = 'unsupported'; throw e; }
            T = _topics[topic] = { topic: topic, refs: 0, hs: [], gs: [], sts: [], ok: false, extra: {} };
            var ch = T.ch = sb.channel(topic, { config: { broadcast: { self: false, ack: false } } });
            ch.on('broadcast', { event: 'h' }, function (m) { statTick('recv'); var p = m && m.payload; T.hs.slice().forEach(function (f) { f(p); }); });
            ch.on('broadcast', { event: 'g' }, function (m) { statTick('recv'); var p = m && m.payload; T.gs.slice().forEach(function (f) { f(p); }); });
            T.ready = new Promise(function (res) {
                ch.subscribe(function (status) {
                    if (status === 'SUBSCRIBED') { var was = T.ok; T.ok = true; res(true); if (!was) T.sts.slice().forEach(function (f) { f(true); }); }
                    else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT' || status === 'CLOSED') { var was2 = T.ok; T.ok = false; if (was2) T.sts.slice().forEach(function (f) { f(false); }); }
                });
                setTimeout(function () { res(T.ok); }, 10000);
            });
        }
        T.refs++;
        var mine = { h: [], g: [], s: [] }, closed = false;
        return {
            ready: T.ready,
            onH: function (f) { T.hs.push(f); mine.h.push(f); },
            onG: function (f) { T.gs.push(f); mine.g.push(f); },
            onStatus: function (f) { T.sts.push(f); mine.s.push(f); },
            ok: function () { return T.ok; },
            send: function (ev, payload) {
                if (closed || !T.ok) return false;
                statTick('sent');
                try { var r = T.ch.send({ type: 'broadcast', event: ev, payload: payload }); if (r && r.catch) r.catch(function () {}); } catch (e) { dbg('send', e); return false; }
                return true;
            },
            close: function () {
                if (closed) return; closed = true;
                mine.h.forEach(function (f) { var i = T.hs.indexOf(f); if (i >= 0) T.hs.splice(i, 1); });
                mine.g.forEach(function (f) { var i = T.gs.indexOf(f); if (i >= 0) T.gs.splice(i, 1); });
                mine.s.forEach(function (f) { var i = T.sts.indexOf(f); if (i >= 0) T.sts.splice(i, 1); });
                if (--T.refs <= 0) {
                    var sb2 = sbClient();
                    T.closing = Promise.resolve().then(function () { return sb2 && sb2.removeChannel(T.ch); }).catch(function () {}).then(function () { if (_topics[topic] === T) delete _topics[topic]; T.closing = null; });
                }
            }
        };
    }

    /* ── 토큰 버킷 ─────────────────────────────────────────── */
    function Bucket(rate, burst) { this.r = rate; this.b = burst; this.v = burst; this.t = now(); }
    Bucket.prototype.take = function () { var t = now(); this.v = Math.min(this.b, this.v + (t - this.t) * this.r / 1000); this.t = t; if (this.v >= 1) { this.v -= 1; return true; } return false; };

    /* ── 어댑터·레지스트리 조회 ─────────────────────────────── */
    var _adapter = null;
    function reg(gid) { return (G.LpGames && G.LpGames.get) ? G.LpGames.get(gid) : null; }
    function regOk(gid) { return gid === 'lobby' || !!reg(gid); }
    function seatsFor(gid) {
        if (_adapter && _adapter.gameId === gid && _adapter.seats !== undefined) return _adapter.seats;
        var r = reg(gid); return r && r.mp ? r.mp.seats : null;
    }
    function lateFor(gid) { if (_adapter && _adapter.gameId === gid && _adapter.lateJoin) return _adapter.lateJoin; var r = reg(gid); return (r && r.mp && r.mp.lateJoin) || 'anytime'; }
    function kindFor(gid) { if (_adapter && _adapter.gameId === gid) return _adapter.kind; var r = reg(gid); return r && r.mp ? r.mp.kind : (gid === 'lobby' ? 'lobby' : 'draw'); }
    function urlFor(gid, code) {
        if (G.LpGames && G.LpGames.url) { var u = G.LpGames.url(gid, code); if (u) return u; }
        return gid === 'lobby' ? '/lobby/?r=' + code : null;
    }

    /* ================================================================
       Room — 방장/멤버 공용 객체. 승계·강등 때도 같은 객체가 역할만 바꾼다
       (게임이 붙여 둔 리스너가 끊기지 않게).
       ================================================================ */
    var CACHE_EV = { roster: 1, state: 1, phase: 1 };
    var _current = null;

    function Room(code, dev) {
        Emitter.call(this, CACHE_EV);
        this.code = code; this.gameId = null; this.isHost = false; this.ep = 0;
        this.me = { pid: dev.pid, role: 'player', seat: null };
        this.fp = ''; this.seal = ''; this.sealed = true;
        this._dev = dev; this._S = null; this._T = null;
        this._rpk = null; this._chain = null; this._hostPk = null; this._hostDh = null;
        this._mk = {}; this._kv = 0;
        this._left = false; this._timers = [];
        this._vq = Promise.resolve(); this._hq = Promise.resolve(); this._gq = Promise.resolve();
        this._cseq = Math.max(now(), (+ssGet('lpr_c_' + code) || 0) + 1);
        /* 멤버 */
        this._lastS = null; this._lastT = 0; this._buf = {}; this._gapT = 0; this._snapAt = 0;
        this._lastHostAt = now(); this._hostHidden = false; this._wd = 0; this._pend = {}; this._hbX = {}; this._hbSoon = 0; this._lastGHb = 0;
        this._clk = []; this._off = 0; this._peer = {}; this._peerC = {}; this._takeBy = null; this._state = 'idle';
        this._reactAt = 0; this._fst = null; this._io = this._mkIO();
        this._fl = [];   /* lpFair 'fair' 리스너 */
        this._H = null;  /* 방장 전용 상태 */
    }
    Room.prototype = Object.create(Emitter.prototype);
    Room.prototype.constructor = Room;

    Room.prototype.roster = function () { return this._S ? this._S.roster.slice() : []; };
    Room.prototype.state = function () { return this._S; };
    Room.prototype.clock = function () { return this.isHost ? now() : now() + this._off; };
    Room.prototype._member = function (p) { var S = this._S; if (!S) return null; for (var i = 0; i < S.roster.length; i++) if (S.roster[i].p === p) return S.roster[i]; return null; };
    Room.prototype._hostMember = function () { var S = this._S; if (!S) return null; for (var i = 0; i < S.roster.length; i++) if (S.roster[i].r === 'host') return S.roster[i]; return null; };
    Room.prototype._timer = function (fn, ms, every) { var id = every ? setInterval(fn, ms) : setTimeout(fn, ms); this._timers.push([id, every]); return id; };
    Room.prototype._clearTimers = function () { this._timers.forEach(function (t) { t[1] ? clearInterval(t[0]) : clearTimeout(t[0]); }); this._timers = []; };
    Room.prototype._syncMe = function () {
        var m = this._member(this.me.pid);
        if (m) { this.me.role = m.r; this.me.seat = m.seat == null ? null : m.seat; }
    };
    Room.prototype._rawSend = function (ev, env) { if (this._T && !this._left) this._T.send(ev, env); };
    Room.prototype.hb = function (k, v, o) {
        this._hbX[k] = v;
        if (o && o.soon) { var t = now() + 1200 + Math.floor(Math.random() * 400); if (!this._hbSoon || this._hbSoon > t) this._hbSoon = t; }
    };
    Room.prototype.inviteUrl = function () {
        var org = _cfg.origin || (G.location && /^https?:/.test(G.location.origin) ? G.location.origin : 'https://luckyplz.com');
        var tok = this.isHost ? this._H.tok : (this._S && this._S.inv);
        return org + '/r/' + this.code + '#k=' + this.fp + (tok ? '.' + tok : '');
    };
    Room.prototype.canStart = function () {
        var S = this._S; if (!S) return false;
        if (_adapter && _adapter.gameId === S.gameId && typeof _adapter.canStart === 'function') { try { return !!_adapter.canStart(S.roster.slice(), S); } catch (_) { return false; } }
        var sp = seatsFor(S.gameId), min = sp ? sp[0] : 1;
        var players = S.roster.filter(function (m) { return m.r === 'host' || m.r === 'player' || m.r === 'bot'; });
        if (players.length < min) return false;
        return players.every(function (m) { return m.r !== 'player' || (m.rd && m.c === 'on'); });
    };
    Room.prototype._migratable = function () {
        var S = this._S; if (!S) return false;
        if (S.phase === 'lobby' || S.phase === 'result') return true;
        if (_adapter && _adapter.gameId === S.gameId && _adapter.migratable !== undefined) {
            try { return typeof _adapter.migratable === 'function' ? !!_adapter.migratable(S) : !!_adapter.migratable; } catch (_) { return false; }
        }
        var r = reg(S.gameId); return !!(r && r.mp && r.mp.migr && !r.mp.hidden);
    };

    /* ── lpFair 가 쓰는 내부 입출력 ────────────────────────────── */
    Room.prototype._mkIO = function () {
        var self = this;
        return {
            get isHost() { return self.isHost; },
            sendH: function (e, d, o) { return self._hsend(e, d, o || {}); },
            sendG: function (e, d) { return self._gsend(e, d); },
            on: function (e, cb) { if (e !== 'fair') return function () {}; self._fl.push(cb); return function () { var i = self._fl.indexOf(cb); if (i >= 0) self._fl.splice(i, 1); }; },
            emit: function (ev) { if (ev === 'fair') self._reactUntil = now() + 20000; self.emit.apply(self, arguments); },
            sign: function (str) { return signStr(self.isHost ? self._H.sk : self._dev.sig.priv, str); },
            signPk: function () { return self.isHost ? self._hostPk : self._dev.sig.pub; },
            hostPk: function () { return self._hostPk; },
            rpk: function () { return self._rpk; },
            chain: function () { return self._chain && self._chain.length ? self._chain : null; },
            store: function () { if (!self._H) return self._fst || (self._fst = {}); return self._H.fs || (self._H.fs = {}); },
            save: function () { if (self.isHost) self._dirty(); },
            clockSample: function (t0, t1, t2, t3) { if (!self.isHost) self._clockSample(t0, t1, t2, t3); }   /* [+] 추첨 에코 표본 */
        };
    };
    Room.prototype._fair = function (from, d, rx) { this._fl.slice().forEach(function (f) { try { f(from, d, rx); } catch (e) { dbg('fair listener', e); } }); };

    /* ================================================================
       송신 — 방장 'h' 봉투 (서명 직렬 큐, §3.2)
       ================================================================ */
    Room.prototype._hsend = function (e, d, o) {
        var self = this; o = o || {};
        if (!this._H) return Promise.resolve(null);
        var useT = !!T_EV[e];
        var env = { v: 2, e: e, ep: this.ep };
        if (useT) env.t = ++this._H.t; else env.s = ++this._H.s;
        if (o.to) env.to = Array.isArray(o.to) ? o.to.slice().sort() : o.to;
        if (o.reliable) env.id = rid(3);
        var j = JSON.stringify(d === undefined ? null : d);
        if (j.length > MAXJ) dbg('WARN payload > 32KB', e, j.length);
        var sealIt = this.sealed && !PLAIN_H[e] && !o.plain;
        var p = this._hq = this._hq.then(async function () {
            if (self._left || !self._H) return null;
            var body;
            if (sealIt) { var c = await aesSeal(self._mk[self._kv], self._kv, j); env.c = c; body = c.iv + '.' + c.ct; }
            else { env.j = j; body = j; }
            var tos = env.to ? (Array.isArray(env.to) ? env.to.join(',') : env.to) : '';
            env.z = await signStr(self._H.sk, ['lpr2', 'h', self.code, env.ep, useT ? 't' + env.t : String(env.s), e, tos, body].join('|'));
            self._rawSend('h', env);
            if (o.reliable) TM.resend.forEach(function (ms) { setTimeout(function () { if (!self._left) self._rawSend('h', env); }, ms); });
            return env;
        }).catch(function (err) { dbg('hsend', e, err); return null; });
        return p;
    };
    /* 게스트 'g' 봉투 — 서명·봉인. 반환 = 서명된 봉투(재전송은 같은 봉투) */
    Room.prototype._genv = function (e, d, o) {
        var self = this; o = o || {};
        var c = ++this._cseq; ssSet('lpr_c_' + this.code, String(c));
        var env = { v: 2, e: e, p: this.me.pid, c: c };
        var j = JSON.stringify(d === undefined ? null : d);
        var sealIt = this.sealed && !o.plain && e !== 'join' && e !== 'hello_req' && this._mk[this._kv];
        return (this._gq = this._gq.then(async function () {
            var body;
            if (sealIt) { var y = await aesSeal(self._mk[self._kv], self._kv, j); env.y = y; body = y.iv + '.' + y.ct; }
            else { env.j = j; body = j; }
            env.z = await signStr(self._dev.sig.priv, ['lpr2', 'g', self.code, self.me.pid, c, e, body].join('|'));
            return env;
        }));
    };
    Room.prototype._gsend = function (e, d, o) {
        var self = this;
        if (this.isHost && e !== 'takeover' && e !== 'state_offer') return Promise.resolve(null);
        return this._genv(e, d, o).then(function (env) { self._rawSend('g', env); return env; }).catch(function (err) { dbg('gsend', e, err); return null; });
    };

    /* ================================================================
       수신 공통 — 빠른 거름(서명 검증 전) + 직렬 검증 큐
       ================================================================ */
    function envSize(env) { return (env.j ? env.j.length : 0) + (env.c && env.c.ct ? env.c.ct.length : 0) + (env.y && env.y.ct ? env.y.ct.length : 0); }
    function hBody(env) { return env.c ? (env.c.iv + '.' + env.c.ct) : env.j; }
    function hSigStr(code, env) {
        var tos = env.to ? (Array.isArray(env.to) ? env.to.join(',') : String(env.to)) : '';
        return ['lpr2', 'h', code, env.ep, env.t != null ? 't' + env.t : String(env.s), env.e, tos, hBody(env)].join('|');
    }
    function gSigStr(code, env) { return ['lpr2', 'g', code, env.p, env.c, env.e, env.y ? env.y.iv + '.' + env.y.ct : env.j].join('|'); }
    /* 수신 콜백 진입 시각(서명 검증·복호 큐 대기 전) — 시계 표본의 t1·t3 은 이 값을 쓴다(큐 지연이 오프셋을 비틀지 않게) */
    var RXT = typeof WeakMap === 'function' ? new WeakMap() : null;
    function rxMark(env) { if (RXT && env && typeof env === 'object' && !RXT.has(env)) RXT.set(env, now()); }
    function rxOf(env) { var v = RXT && env && typeof env === 'object' ? RXT.get(env) : undefined; return typeof v === 'number' ? v : now(); }
    function okH(env) {
        return env && typeof env === 'object' && env.v === 2 && typeof env.e === 'string' && HOST_EV[env.e] && typeof env.z === 'string' && typeof env.ep === 'number'
            && (typeof env.s === 'number' || typeof env.t === 'number') && (typeof env.j === 'string' || (env.c && typeof env.c.ct === 'string' && typeof env.c.iv === 'string')) && envSize(env) <= MAXJ;
    }
    function okG(env) {
        return env && typeof env === 'object' && env.v === 2 && typeof env.e === 'string' && env.e.length < 16 && typeof env.p === 'string' && PID_RE.test(env.p)
            && typeof env.c === 'number' && typeof env.z === 'string' && (typeof env.j === 'string' || (env.y && typeof env.y.ct === 'string' && typeof env.y.iv === 'string')) && envSize(env) <= MAXJ;
    }
    Room.prototype._openBody = async function (env, cf) {
        var c = env[cf];
        if (!c) return JSON.parse(env.j);
        var key = this._mk[c.k];
        if (!key) { var e = new Error('nokey'); e.nokey = c.k; throw e; }
        return JSON.parse(await aesOpen(key, c));
    };
    Room.prototype._attach = function (T) {
        var self = this;
        this._T = T;
        T.onH(function (env) { self._rxH(env); });
        T.onG(function (env) { self._rxG(env); });
        T.onStatus(function (ok) {
            self.emit('net', { ok: ok });
            if (ok && self._state === 'member') {
                if (self.isHost) self._flushState(true);
                else self._snapReq(true);
            }
        });
    };
    Room.prototype._rxH = function (env) {
        rxMark(env);
        if (this._left) return;
        if (!okH(env)) { STATS.bad++; return; }
        var self = this;
        this._vq = this._vq.then(function () { return self.isHost ? self._hostSeesH(env) : self._guestH(env); }).catch(function (e) { STATS.bad++; dbg('rxH', e); });
    };
    Room.prototype._rxG = function (env) {
        rxMark(env);
        if (this._left) return;
        if (env && env.e === 'hello_req' && env.v === 2) { if (this.isHost) this._helloReq(env); return; }
        if (!okG(env)) { STATS.bad++; return; }
        if (this.isHost) {
            var H = this._H;
            if (env.e !== 'join' && !H.members[env.p]) { STATS.bad++; return; }
            if (env.e === 'join') { if (!H.joinB.take()) return; }
            else { var mb = H.members[env.p]; if (!mb.bk.take()) return; }
        } else {
            if (this._state !== 'member' || !this._member(env.p)) return;
            var pb = this._peer[env.p] || (this._peer[env.p] = { t: now(), b: new Bucket(15, 30) });
            if (!pb.b.take()) return;
        }
        var self = this;
        this._vq = this._vq.then(function () { return self.isHost ? self._hostG(env) : self._peerG(env); }).catch(function (e) { STATS.bad++; dbg('rxG', e); });
    };

    /* ================================================================
       멤버: 방장 봉투 처리 (서명 → 재생 방지 → 복호 → 순서 → 적용)
       ================================================================ */
    Room.prototype._guestH = async function (env) {
        if (this._state === 'joining') { if (this._joinW) this._joinW(env); else if (this._jbuf && this._jbuf.length < 64) this._jbuf.push(env); return; }
        if (this._state !== 'member') return;
        if (!(await verifyStr(this._hostPk, hSigStr(this.code, env), env.z))) { STATS.bad++; return; }
        if (env.ep < this.ep) return;                        /* 옛 epoch 재생 */
        if (env.ep > this.ep) {                               /* 같은 키의 새 epoch = 방장 재개 */
            this.ep = env.ep; this._lastS = null; this._lastT = 0; this._buf = {}; this._gaps = [];
        }
        this._lastHostAt = now();
        if (this._wd) { this._wd = 0; this.emit('hostback'); }
        var d;
        try { d = await this._openBody(env, 'c'); }
        catch (e) { if (e && e.nokey) this._snapReq(true, true); STATS.bad++; return; }
        if (env.t != null) {
            if (env.t <= this._lastT) return;
            this._lastT = env.t;
            return this._gApply(env, d);
        }
        if (this._lastS === null) {
            if (env.e === 'state' || (env.e === 'welcome' && this._forMe(env))) { this._lastS = env.s; this._buf = {}; return this._gApply(env, d); }
            this._buf[env.s] = [env, d]; this._gapCheck(); return;
        }
        if (env.s <= this._lastS) {                           /* 중복·재전송·재생 — 단, 전체 state 로 건너뛴 사이 늦게 온 '사건'은 id 로 한 번만 살린다 */
            if (env.id && LATE_OK[env.e] && this._inGap(env.s) && !this._seen(env.id)) this._gApply(env, d);
            return;
        }
        if (env.s === this._lastS + 1 || env.e === 'state') {
            if (env.e === 'state') {
                if (env.s > this._lastS + 1) { this._gaps = (this._gaps || []).concat([[this._lastS, env.s]]).slice(-8); }   /* 건너뛴 구간 기억 */
                var ks = Object.keys(this._buf); for (var i = 0; i < ks.length; i++) if (+ks[i] <= env.s) delete this._buf[ks[i]];
            }
            this._lastS = env.s; this._gApply(env, d); this._drain(); return;
        }
        this._buf[env.s] = [env, d]; this._gapCheck();
    };
    Room.prototype._drain = function () {
        while (this._lastS !== null && this._buf[this._lastS + 1]) {
            var x = this._buf[this._lastS + 1]; delete this._buf[this._lastS + 1];
            this._lastS++; this._gApply(x[0], x[1]);
        }
    };
    Room.prototype._gapCheck = function () {
        var self = this;
        if (this._gapT) return;
        this._gapT = setTimeout(function () {
            self._gapT = 0;
            if (Object.keys(self._buf).length) self._snapReq(false);
        }, TM.snapWait);
    };
    Room.prototype._snapReq = function (force, needKey) {
        if (this.isHost || this._state !== 'member') return;
        var t = now();
        if (!force && t - this._snapAt < TM.snapPer) return;
        if (force && t - this._snapAt < 500) return;
        this._snapAt = t;
        this._gsend('snap_req', { have: this._lastS, kv: needKey ? this._kv : undefined });
    };
    Room.prototype._forMe = function (env) {
        if (!env.to) return true;
        return Array.isArray(env.to) ? env.to.indexOf(this.me.pid) >= 0 : env.to === this.me.pid;
    };
    Room.prototype._applyS = function (S) {
        var prev = this._S;
        if (!S || S.v !== 2 || !Array.isArray(S.roster)) return;
        var acks = S._a; delete S._a;
        this._S = S;
        if (S.gameId) this.gameId = S.gameId;
        this._syncMe();
        this._rosterDelta(prev ? prev.roster : [], S.roster);
        this.emit('state', S, prev);
        if (!prev || prev.phase !== S.phase) this.emit('phase', S.phase, S);
        this._acks(acks);
    };
    Room.prototype._rosterDelta = function (a, b, force) {
        var A = {}, B = {}, d = { join: [], left: [], back: [] }, changed = !!force;
        a.forEach(function (m) { A[m.p] = m; }); b.forEach(function (m) { B[m.p] = m; });
        b.forEach(function (m) { if (!A[m.p]) { d.join.push(m.p); changed = true; } else if (A[m.p].c === 'off' && m.c !== 'off') { d.back.push(m.p); changed = true; } else if (canon(A[m.p]) !== canon(m)) changed = true; });
        a.forEach(function (m) { if (!B[m.p]) { d.left.push(m.p); changed = true; } });
        if (changed || !this._c.roster) this.emit('roster', b.slice(), d);
        var self = this; b.forEach(function (m) { if (!self._peer[m.p]) self._peer[m.p] = { t: now(), b: new Bucket(15, 30) }; });
    };
    Room.prototype._acks = function (acks) {
        var self = this;
        if (!Array.isArray(acks)) return;
        acks.forEach(function (a) { if (a && a[0] === self.me.pid) self._resolveIntent(a[1], { ok: true, seq: self._S ? self._S.seq : 0 }); });
    };
    /* 재전송 id 기억(최근 256개) — 같은 사건을 두 번 적용하지 않게 */
    var LATE_OK = { 'switch': 1, kicked: 1, close: 1, fair: 1, x: 1, rekey: 1, th: 1, priv: 1, welcome: 1 };
    Room.prototype._inGap = function (x) { var g = this._gaps || []; for (var i = 0; i < g.length; i++) if (x > g[i][0] && x < g[i][1]) return true; return false; };
    Room.prototype._seen = function (id) {
        var S = this._ids || (this._ids = { set: {}, q: [] });
        if (S.set[id]) return true;
        S.set[id] = 1; S.q.push(id); if (S.q.length > 256) delete S.set[S.q.shift()];
        return false;
    };
    Room.prototype._gApply = function (env, d) {
        var e = env.e, me = this._forMe(env), self = this;
        if (env.id && env.s != null && LATE_OK[e]) this._seen(env.id);
        switch (e) {
            case 'state': if (d && d.v === 2) this._applyS(d); break;
            case 'delta':
                if (!this._S || !d || d.base !== this._S.seq) { this._snapReq(true); break; }
                var S2 = clone(this._S); applyOps(S2, d.ops || []); S2.seq = d.seq; S2._a = d.a; this._applyS(S2); break;
            case 'roster':
                if (!this._S || !d || !Array.isArray(d.r)) break;
                var prevR = this._S.roster;
                this._S.roster = d.r; this._S.succ = d.succ || []; this._S.succz = d.sz; this._S.succe = d.se;
                if (d.lock !== undefined) this._S.lock = d.lock;
                if (d.appr !== undefined) this._S.appr = d.appr;
                this._syncMe(); this._rosterDelta(prevR, d.r); this._acks(d.a); break;
            case 'phase':
                if (!this._S || !d) break;
                if (this._S.phase !== d.phase || this._S.startAt !== d.startAt) { this._S.phase = d.phase; this._S.startAt = d.startAt == null ? null : d.startAt; this.emit('phase', d.phase, this._S); }
                break;
            case 'hb':
                if (!d) break;
                this._hostHidden = d.vis === 'hidden';
                if (d.ec && d.ec[this.me.pid]) this._clockSample(d.ec[this.me.pid][0], d.ec[this.me.pid][1], d.t, rxOf(env));
                if (typeof d.hs === 'number' && this._lastS !== null && d.hs > this._lastS) this._gapCheck2(d.hs);
                this.emit('hb', null, d);
                break;
            case 'tick': this.emit('tick', d); break;
            case 'priv':
                if (!me || !d || !d.x) break;
                eciesDec(this._dev.dh.priv, this.code, 'priv', d.x).then(function (v) { self.emit('priv', v, d.e); }).catch(function () { STATS.bad++; });
                break;
            case 'ack': if (me && d) this._resolveIntent(d.c, { ok: true, seq: d.seq }); break;
            case 'nack': if (me && d) this._resolveIntent(d.c, { ok: false, reason: String(d.r || 'rejected'), seq: d.seq }); break;
            case 'kicked': if (me) this._kicked(d || {}); break;
            case 'rekey':
                if (!me || !d || !d.x) break;
                eciesDec(this._dev.dh.priv, this.code, 'rekey', d.x).then(function (v) { var raw = ub64u(v.mk); (self._mkRawG || (self._mkRawG = {}))[v.kv] = raw; return aesKey(raw).then(function (k) { self._mk[v.kv] = k; if (v.kv > self._kv) self._kv = v.kv; }); }).catch(function () { STATS.bad++; });
                break;
            case 'close': this._closedBy('host'); break;
            case 'switch': if (d) this._onSwitch(d.gameId); break;
            case 'fair': this._fair(null, d, rxOf(env)); break;
            case 'x': if (d && typeof d.k === 'string') this.emit('x', d.k, d.d, null); break;
            case 'react': if (d) { var hm = this._hostMember(); this.emit('react', d.i | 0, hm ? hm.p : null); } break;
            case 'th': if (me && d) this._becomeHost({ transfer: d }); break;
            case 'welcome':
                if (!me || !d || !d.x) break;
                eciesDec(this._dev.dh.priv, this.code, 'welcome', d.x).then(function (inner) { return self._onWelcome(env, inner); }).catch(function () { STATS.bad++; });
                break;
            default: break;
        }
    };
    Room.prototype._gapCheck2 = function (hs) {
        var self = this;
        setTimeout(function () { if (self._lastS !== null && self._lastS < hs) self._snapReq(false); }, TM.snapWait);
    };
    /* NTP 식 시계 (§6.0.3, 2026-09-30 정밀화): 표본 창 최근 24개·10분(최소 3개 유지), RTT 하위 N(=min(5,⌈n/2⌉))개의
       오프셋 중앙값. 표본 출처 = 합류 welcome · hb 에코(ec) · 추첨 lock/reveal 에코(lpFair, 추첨마다 2개, 추가 메시지 0).
       t1·t3 은 수신 콜백 진입 시각(rxOf) — 서명 검증·복호 큐 대기와 긴 작업으로 늦게 처리된 표본은 RTT 가 커져 자동 배제된다. */
    var CLK = { win: 24, age: 600000, keep: 3, best: 5 };
    Room.prototype._clockSample = function (t0, t1, t2, t3) {
        if (typeof t0 !== 'number' || typeof t1 !== 'number' || typeof t2 !== 'number') return;
        if (typeof t3 !== 'number') t3 = now();
        var rtt = (t3 - t0) - (t2 - t1), off = ((t1 - t0) + (t2 - t3)) / 2;
        if (!(rtt >= 0) || rtt > 30000 || !isFinite(off)) return;
        var t = now(), c = this._clk;
        c.push({ rtt: rtt, off: off, t: t });
        while (c.length > CLK.win || (c.length > CLK.keep && t - c[0].t > CLK.age)) c.shift();
        var by = c.slice().sort(function (a, b) { return a.rtt - b.rtt; });
        var k = Math.max(1, Math.min(CLK.best, Math.ceil(c.length / 2)));
        var best = by.slice(0, k).map(function (x) { return x.off; }).sort(function (a, b) { return a - b; });
        var mid = best.length >> 1;
        this._off = best.length % 2 ? best[mid] : (best[mid - 1] + best[mid]) / 2;
        this._rtt = by[0].rtt;
        this._clkN = (this._clkN || 0) + 1;
    };
    /* 다시 맞추기 — 화면 복귀(visibilitychange→visible) 때 빠른 에코 hb 3개(fs:1 → 방장이 250ms 안에 hb 로 되돌림).
       30초에 한 번까지. 60초 넘게 숨어 있었으면(기기 시계 보정 가능) 그 전 표본은 버린다. */
    Room.prototype._resync = function (hiddenMs) {
        if (this.isHost || this._left || this._state !== 'member') return;
        var t = now(), self = this;
        if (hiddenMs > 60000 && this._clk.length) this._clk = this._clk.filter(function (x) { return t - x.t < hiddenMs; });
        if (this._resyncAt && t - this._resyncAt < 30000) { this._sendGHb(); return; }
        this._resyncAt = t; this._fsUntil = t + 4000;
        this._sendGHb();
        this._timer(function () { self._sendGHb(); }, 700);
        this._timer(function () { self._sendGHb(); }, 1900);
    };

    /* 멤버: 다른 게스트의 'g' (연결 추적·리액션·x·승계) */
    Room.prototype._peerG = async function (env) {
        var m = this._member(env.p);
        if (!m || !m.k || env.p === this.me.pid) return;
        if (!(await verifyStr(m.k.sig, gSigStr(this.code, env), env.z))) { STATS.bad++; return; }
        var pc = this._peerC[env.p];
        if (!pc || typeof pc !== 'object') pc = this._peerC[env.p] = { lastC: pc || 0 };
        if (!replayOk(pc, env.c)) return;
        var pr = this._peer[env.p] || (this._peer[env.p] = { b: new Bucket(15, 30) });
        pr.t = now(); if (env.e === 'bye') pr.t = 0;
        var d; try { d = await this._openBody(env, 'y'); } catch (_) { return; }
        switch (env.e) {
            case 'react': if (d && this._reactOk(env.p)) this.emit('react', d.i | 0, env.p); break;
            case 'x': if (d && typeof d.k === 'string') this.emit('x', d.k, d.d, env.p); break;
            case 'hb': this.emit('hb', env.p, d); break;
            case 'takeover': this._onTakeover(env.p, d); break;
            default: break;
        }
    };
    Room.prototype._reactOk = function (p) {
        var r = this._reactT || (this._reactT = {}), t = now();
        if (r[p] && t - r[p] < 1100) return false;
        r[p] = t; return true;
    };

    /* ── 멤버 루프: 하트비트 + 방장 감시 (§6.0.3·§6.0.5) ───────── */
    Room.prototype._guestLoops = function () {
        var self = this;
        this._lastGHb = 0;
        this._timer(function () { self._guestTick(); }, 500, true);
        this._timer(function () { self._sendGHb(); }, 600);
        this._timer(function () { self._sendGHb(); }, 2600);
    };
    Room.prototype._hbInterval = function () {
        var S = this._S, hidden = G.document && G.document.visibilityState === 'hidden';
        var x = (S && S.hbx) || 1;
        if (hidden) return TM.gHidden * x;
        if (S && (S.phase === 'playing' || S.phase === 'starting' || S.phase === 'paused') && this.me.seat != null && this.me.role === 'player') return TM.gPlay * x;
        return TM.gLobby * x;
    };
    Room.prototype._sendGHb = function () {
        if (this.isHost || this._left || this._state !== 'member') return;
        var d = { t0: now(), vis: (G.document && G.document.visibilityState) || 'visible' };
        if (this._fsUntil && now() < this._fsUntil) d.fs = 1;            /* 빠른 에코 요청(다시 맞추기) */
        for (var k in this._hbX) d[k] = this._hbX[k];
        this._hbX = {}; this._hbSoon = 0; this._lastGHb = now();
        this._gsend('hb', d);
    };
    Room.prototype._guestTick = function () {
        if (this.isHost || this._left || this._state !== 'member') return;
        var t = now();
        if (t - this._lastGHb >= this._hbInterval() || (this._hbSoon && t >= this._hbSoon)) this._sendGHb();
        var mult = this._hostHidden ? 2 : 1, dt = t - this._lastHostAt;
        if (dt >= TM.wd1 * mult && this._wd < 1) { this._wd = 1; this.emit('hostlost', { level: 1 }); this._snapReq(true); }
        if (dt >= TM.wd2 * mult && this._wd < 2) { this._wd = 2; this.emit('hostlost', { level: 2 }); }
        if (dt >= TM.wd3 * mult && this._wd >= 2) {
            if (this._migratable()) this._tryTakeover();
            else if (this._wd < 3) { this._wd = 3; this.emit('hostlost', { level: 3 }); }
        }
        if (dt >= TM.wdEnd && !this._migratable()) this._closedBy('host_gone');
    };
    Room.prototype._peerAlive = function (p) {
        if (p === this.me.pid) return true;
        var pr = this._peer[p], S = this._S;
        var win = S && S.phase === 'playing' ? 25000 : 50000;
        return !!pr && now() - pr.t < win;
    };
    Room.prototype._tryTakeover = function () {
        var S = this._S, hm = this._hostMember(), self = this;
        if (!S || this._takeBy) return;
        var dead = this._deadCand || (this._deadCand = {});
        var cands = (S.succ || []).filter(function (p) { return (!hm || p !== hm.p) && !dead[p] && self._member(p) && self._peerAlive(p); });
        if (!cands.length) { if (this._wd < 3) { this._wd = 3; this.emit('hostlost', { level: 3 }); } return; }
        if (cands[0] === this.me.pid) { this._becomeHost({}); return; }
        /* 앞 후보가 10초 안에 나서지 않으면 죽은 것으로 보고 다음으로 */
        var c0 = cands[0];
        if (!this._waitCand || this._waitCand.p !== c0) this._waitCand = { p: c0, t: now() };
        else if (now() - this._waitCand.t > 10000) { dead[c0] = 1; this._waitCand = null; }
    };

    /* 의도 (§6.0.7) */
    Room.prototype.intent = function (a, x, o) {
        var self = this;
        if (typeof a !== 'string' || !a) return Promise.resolve({ ok: false, reason: 'bad' });
        if (this.isHost) {
            var hm = this._member(this.me.pid);
            return Promise.resolve(this._runIntent(hm, a, x, { c: 0, es: o && o.expectSeq, local: true }));
        }
        if (this._state !== 'member') return Promise.resolve({ ok: false, reason: 'not_member' });
        var d = { a: a, x: x === undefined ? null : x };
        if (o && typeof o.expectSeq === 'number') d.es = o.expectSeq;
        return this._genv('intent', d).then(function (env) {
            return new Promise(function (res) {
                var P = self._pend[env.c] = { res: res, n: 0 };
                self._rawSend('g', env);
                var tries = [1500, 3000, 6000];
                (function next() {
                    var ms = tries[P.n++];
                    if (ms == null) { P.to = setTimeout(function () { self._resolveIntent(env.c, { ok: false, reason: 'timeout' }); }, 4000); return; }
                    P.to = setTimeout(function () { if (self._pend[env.c]) { self._rawSend('g', env); next(); } }, ms);
                })();
            });
        });
    };
    Room.prototype._resolveIntent = function (c, r) {
        var P = this._pend[c]; if (!P) return;
        delete this._pend[c]; clearTimeout(P.to); P.res(r);
    };
    Room.prototype.x = function (k, d) {
        if (typeof k !== 'string') return;
        if (this.isHost) this._hsend('x', { k: k, d: d }, { reliable: k === 'result' || k === 'board' });
        else this._gsend('x', { k: k, d: d });
    };
    Room.prototype.react = function (i) {
        var S = this._S, t = now();
        if (!S || t - this._reactAt < 1200) return;
        /* 리액션은 대기실·결과·추첨 시청 중에만(운영자 결정 8) — 공정 추첨 사건 뒤 20초는 플레이 중이어도 허용 */
        if (S.phase === 'playing' && !(t < (this._reactUntil || 0)) && !this._reactAny) return;
        this._reactAt = t; i = Math.max(0, Math.min(5, i | 0));
        if (this.isHost) this._hsend('react', { i: i }); else this._gsend('react', { i: i });
        this.emit('react', i, this.me.pid);
    };

    /* 추방 · 종료 · 전환 (멤버 쪽) */
    Room.prototype._kicked = function (d) {
        if (d.ban) { lsSet('lpr_ban_' + this.code, '1'); try { G.document.cookie = 'lpr_ban_' + this.code + '=1; max-age=86400; path=/; SameSite=Lax'; } catch (_) {} idbPut('ban:' + this.code, now()).catch(function () {}); }
        this.emit('kicked', { ban: !!d.ban });
        this._teardown('kicked', true);
    };
    Room.prototype._closedBy = function (reason) {
        if (this._left) return;
        this.emit('closed', { reason: reason });
        this._teardown(reason, true);
    };
    Room.prototype._onSwitch = function (gid) {
        if (typeof gid !== 'string' || !regOk(gid)) { dbg('switch ignored (unknown gameId)', gid); return; }
        var url = urlFor(gid, this.code);
        if (!url) return;
        this.gameId = gid; if (this._S) this._S.gameId = gid;
        setActive({ code: this.code, role: this.isHost ? 'host' : 'guest', gameId: gid, want: this._want, inv: this._inv });
        this.emit('switch', { gameId: gid, url: url });
        if (_cfg.autoNav !== false) {
            var self = this;
            setTimeout(function () { if (!self._left || self.isHost) navigate(url); }, this.isHost ? 700 : 600);
        }
    };
    function navigate(url) {
        if (_cfg.navigate) { try { _cfg.navigate(url); } catch (_) {} return; }
        try { G.location.assign(url); } catch (_) {}
    }
    Room.prototype.leave = function () {
        if (this._left) return;
        if (this.isHost) { this.close(); return; }
        this._gsend('bye', {});
        var self = this;
        setTimeout(function () { self.emit('closed', { reason: 'left' }); self._teardown('left', true); }, 60);
    };
    Room.prototype._teardown = function (why, clearActive) {
        if (this._left) return;
        this._left = true; this._state = 'left';
        this._clearTimers();
        var self = this;
        Object.keys(this._pend).forEach(function (c) { self._resolveIntent(c, { ok: false, reason: 'left' }); });
        try { if (this._T) this._T.close(); } catch (_) {}
        if (this._seatRel) { try { this._seatRel(); } catch (_) {} }
        if (this._hostRel) { try { this._hostRel(); } catch (_) {} }
        if (clearActive) { var a = getActive(); if (a && a.code === this.code) setActive(null); }
        if (_current === this) _current = null;
        GLOBAL.emit('left', { code: this.code, reason: why });
    };

    /* ================================================================
       방장
       ================================================================ */
    function newH(o) {
        return {
            sk: o.sk, dk: o.dk, s: o.s || 0, t: o.t || 0, tok: o.tok, pin: o.pin || null, pinReq: !!o.pinReq, max: Math.min(ROOM_MAX, o.max || ROOM_MAX),
            members: {}, known: o.known || {}, bans: o.bans || {}, banNicks: o.banNicks || {}, pending: {}, bad: [], cool: 0,
            apprAuto: o.apprAuto || 0, helloN: [], helloT: 0, helloAt: 0, joinB: new Bucket(20, 20), rosterT: 0, flushQ: false,
            ackQ: [], snapT: 0, snapPer: {}, lastB: null, nB: 0, privH: {}, lastHb: 0, mem: {}, fs: o.fs || {}, saveT: 0, dirty: false,
            intentCb: null, tickAt: 0, curI: null, stateDirty: false
        };
    }
    function memRec(k, lastC) { return { k: k, lastC: lastC || 0, seen: now(), vis: 'visible', t0: null, t1: 0, bk: new Bucket(30, 40), ib: new Bucket(10, 20), ic: {}, icN: [], bye: false, offAt: 0 }; }
    /* 재생 방지 창 (2026-09-30 통합): 릴레이 지연 편차로 같은 게스트의 봉투 순서가 바뀌면 예전엔 c ≤ lastC 로 버려져
       hb 편승(w 목격·sc 점수)·fair c/r 이 유실됐다(추첨 재시도·목격 누락 — 30~150ms 지터 하네스에서 실측).
       이제 최근 RWIN 개 창 안에서 처음 보는 c 는 받는다(서명된 진짜 봉투의 늦은 도착). 창 밖·이미 본 c 는 여전히 버린다. */
    var RWIN = 64;
    function replayOk(rec, c) {
        var w = rec.win || (rec.win = {});
        if (c > rec.lastC) {
            rec.lastC = c; w[c] = 1;
            if (++rec.winN > RWIN * 2 || !rec.winN) { rec.winN = 0; for (var k in w) { if (+k <= c - RWIN) delete w[k]; else rec.winN++; } }
            return true;
        }
        if (c <= rec.lastC - RWIN || w[c]) return false;
        w[c] = 1; rec.winN = (rec.winN || 0) + 1;
        return true;
    }

    Room.prototype._helloReq = function (env) {
        var H = this._H;
        if (!H.joinB.take()) return;
        if (typeof env.n === 'string' && env.n.length <= 16 && H.helloN.length < 8) H.helloN.push(env.n);
        /* 증폭 방지: hello 는 방송(N 명 과금)이라 10초에 10건 넘게 청하면 간격을 2초로 늘린다 */
        var t = now(); H.helloReqs = (H.helloReqs || []).filter(function (x) { return t - x < 10000; }); H.helloReqs.push(t);
        var gap = H.helloReqs.length > 10 ? 2000 : TM.helloGap;
        var self = this, wait = Math.max(0, H.helloAt + gap - now());
        if (H.helloT) return;
        H.helloT = setTimeout(function () { H.helloT = 0; self._sendHello(); }, wait);
    };
    Room.prototype._helloData = function () {
        var S = this._S, H = this._H;
        return { v: 2, code: this.code, ep: this.ep, rpk: this._rpk, hk: { sig: this._hostPk, dh: this._hostDh }, chain: this._chain && this._chain.length ? this._chain : undefined,
            gameId: S.gameId, kind: kindFor(S.gameId), phase: S.phase, lock: !!S.lock, appr: !!(S.appr || now() < H.apprAuto), pinReq: !!H.pinReq,
            count: this._humans().length, max: H.max, succ: S.succ, sz: S.succz, se: S.succe, n: H.helloN.splice(0) };
    };
    Room.prototype._sendHello = function () { if (!this._H || this._left) return; this._H.helloAt = now(); this._hsend('hello', this._helloData()); };
    Room.prototype._humans = function () { return this._S.roster.filter(function (m) { return m.r !== 'bot'; }); };

    Room.prototype._hostG = async function (env) {
        var H = this._H;
        if (env.e === 'join') return this._handleJoin(env);
        var mb = H.members[env.p];
        if (!mb) return;
        if (!(await verifyStr(mb.k.sig, gSigStr(this.code, env), env.z))) { STATS.bad++; return; }
        if (!replayOk(mb, env.c)) {
            if (env.e === 'intent' && mb.ic[env.c]) this._replyIntent(env.p, env.c, mb.ic[env.c]);
            return;
        }
        var d;
        try { d = await this._openBody(env, 'y'); } catch (e) { if (e && e.nokey) this._resendRekey(env.p); return; }
        mb.seen = now(); mb.bye = false;
        var m = this._member(env.p);
        if (m && m.c === 'off' && env.e !== 'bye') { m.c = mb.vis === 'hidden' ? 'away' : 'on'; this._rosterDirty(); }
        switch (env.e) {
            case 'hb':
                if (!d) break;
                if (typeof d.t0 === 'number') {
                    mb.t0 = d.t0; mb.t1 = rxOf(env);
                    /* 합류 직후 15초 · 게스트 다시 맞추기(fs, 10초에 4번까지) → 에코를 빨리 돌려 시계 표본을 금방 채운다(동시 출발 §6.1.4) */
                    var fast = now() < (mb.fastUntil || 0);
                    if (!fast && d.fs) { mb.fsT = (mb.fsT || []).filter(function (x) { return now() - x < 10000; }); if (mb.fsT.length < 4) { mb.fsT.push(now()); fast = true; } }
                    if (fast) { var soon = now() + 250; if (!this._hbSoon || this._hbSoon > soon) this._hbSoon = soon; }
                }
                if (d.vis === 'hidden' || d.vis === 'visible') {
                    mb.vis = d.vis;
                    if (m && m.c !== 'off') { var nc = d.vis === 'hidden' ? 'away' : 'on'; if (m.c !== nc) { m.c = nc; this._rosterDirty(); } }
                }
                this.emit('hb', env.p, d);
                break;
            case 'bye':
                mb.bye = true;
                if (m && m.c !== 'off') { m.c = 'off'; mb.offAt = now(); this._rosterDirty(); }
                break;
            case 'intent': if (d && typeof d.a === 'string') await this._hostIntent(env.p, env.c, d); break;
            case 'snap_req':
                if (d && d.kv) this._resendRekey(env.p);
                this._snapFrom(env.p); break;
            case 'fair': this._fair(env.p, d, rxOf(env)); break;
            case 'x': if (d && typeof d.k === 'string') this.emit('x', d.k, d.d, env.p); break;
            case 'react': if (d && this._reactOk(env.p)) this.emit('react', d.i | 0, env.p); break;
            case 'takeover': this._onTakeover(env.p, d); break;
            case 'state_offer': this._stateOffer(env.p, d); break;
            default: break;
        }
    };
    Room.prototype._snapFrom = function (p) {
        var H = this._H, t = now(), self = this;
        if (H.snapPer[p] && t - H.snapPer[p] < TM.snapPer) return;
        H.snapPer[p] = t;
        if (H.snapT) return;
        H.snapT = setTimeout(function () { H.snapT = 0; self._flushState(true); }, TM.snapWait);   /* 250ms 안 요청 전부 = 전체 state 1통 */
    };

    /* ── 참가 처리 (§2.6 검증 순서) ─────────────────────────────── */
    Room.prototype._handleJoin = async function (env) {
        var H = this._H, S = this._S, self = this;
        if (typeof env.j !== 'string') return;
        var d = jparse(env.j, null);
        if (!d || !d.dpk || typeof d.dpk.sig !== 'string' || typeof d.dpk.dh !== 'string' || d.dpk.sig.length > 100 || d.dpk.dh.length > 100) return;
        if ((await pidOf(d.dpk.sig)) !== env.p) { STATS.bad++; return; }                     /* 1 pid==fp(dpk) */
        if (!(await verifyStr(d.dpk.sig, gSigStr(this.code, env), env.z))) { STATS.bad++; return; }   /* 1 서명 */
        var prev = H.members[env.p];
        if (prev && env.c <= prev.lastC) return;
        var jl = H.joinSeen || (H.joinSeen = {});
        if (jl[env.p] && jl[env.p].c === env.c) {                                          /* 같은 join 재전송 */
            if (now() - jl[env.p].t < 1000) return;
            jl[env.p].t = now();
            if (jl[env.p].deny) { var dn = jl[env.p].deny; return this._deny(env.p, dn.r, dn.extra); }   /* 캐시된 거절 — PIN 오답 재계수 없음 */
            if (!this._member(env.p) && !H.pending[env.p]) return;
        } else jl[env.p] = { c: env.c, t: now() };
        var x = {};
        try { if (d.x) x = await eciesDec(H.dk, this.code, 'join', d.x) || {}; } catch (_) { return this._deny(env.p, 'bad_proof'); }
        var p = env.p;
        if (H.bans[p]) return this._deny(p, 'banned');                                        /* 2 차단 */
        if (d.v != null && d.v !== 2) return this._deny(p, 'version');
        var inRoster = !!this._member(p), known = inRoster || !!H.known[p];
        if (known) return this._admit(p, d, x, env);                                         /* 4 알려진 pid → 복귀 */
        if (S.lock) return this._deny(p, 'locked');                                          /* 5 잠금·정원 */
        if (this._humans().length >= H.max) return this._deny(p, 'full');
        if (typeof d.g === 'string' && d.g && d.g !== S.gameId && S.gameId !== 'lobby') return this._deny(p, 'wrong_game', { gameId: S.gameId });
        var tokOk = typeof x.tok === 'string' && !!H.tok && x.tok === H.tok;                  /* 6 증명 */
        if (H.pinReq && !tokOk) {
            if (now() < H.cool) return this._deny(p, 'rate');                                  /* 3 레이트리밋 */
            if (!H.pin) { /* 승계 방장: PIN 을 모른다 → 승인 대기로 */ }
            else if (!x.pin) return this._deny(p, 'pin_required');
            else if (String(x.pin) !== String(H.pin)) {
                var t = now(); H.bad = H.bad.filter(function (b) { return t - b < 60000; }); H.bad.push(t);
                if (H.bad.length >= 10) { H.cool = t + 60000; H.bad = []; this.emit('pinflood', { until: H.cool }); }
                return this._deny(p, 'bad_proof');
            }
        }
        var needAppr = S.appr || now() < H.apprAuto || (H.pinReq && !H.pin && !tokOk);
        if (needAppr) {
            var nk = nickKey(cleanNick(x.nick));
            H.pending[p] = { env: env, d: d, x: x, t: now(), flag: H.banNicks[nk] ? 'banned_nick' : undefined };
            this.emit('pending', this.pending());
            return this._deny(p, 'pending');
        }
        return this._admit(p, d, x, env);
    };
    Room.prototype._deny = function (p, r, extra) {
        /* 증폭 방지: 거절도 방송이다 — 초당 5건(버스트 10). 같은 join 재전송엔 캐시된 거절을 다시 보낸다(재평가·재계수 없음) */
        var H = this._H;
        if (!H.denyB) H.denyB = new Bucket(5, 10);
        var js = H.joinSeen && H.joinSeen[p]; if (js) js.deny = { r: r, extra: extra };
        if (!H.denyB.take()) return Promise.resolve(null);
        var d = { r: r }; if (extra) for (var k in extra) d[k] = extra[k];
        return this._hsend('deny', d, { to: p });
    };
    Room.prototype._freeSeat = function (gid) {
        var sp = seatsFor(gid); if (!sp) return null;
        var used = {}; this._S.roster.forEach(function (m) { if (m.seat != null) used[m.seat] = 1; });
        for (var i = 0; i < sp[1]; i++) if (!used[i]) return i;
        return -1;
    };
    Room.prototype._uniqNick = function (n, p) {
        var base = n || 'Guest', name = base, k = 2, S = this._S;
        function taken(x) { return S.roster.some(function (m) { return m.p !== p && m.r !== 'bot' && nickKey(m.n) === nickKey(x); }); }
        while (taken(name) && k < 100) name = base + k++;
        return name;
    };
    Room.prototype._admit = async function (p, d, x, env) {
        var H = this._H, S = this._S, t = now(), rx = env ? rxOf(env) : t;
        delete H.pending[p];
        var m = this._member(p), back = !!m, wasOff = m && m.c === 'off';
        var nick = this._uniqNick(cleanNick(x.nick) || (m && m.n) || 'Guest', p);
        if (!m) {
            var mem = (S.mem && S.mem[S.gameId] && S.mem[S.gameId][p]) || {};
            m = { p: p, n: nick, av: Math.max(0, Math.min(15, (x.av | 0))), r: 'player', seat: null, pick: mem.pick || {}, rd: false, c: 'on', j: t, au: x.au && typeof x.au === 'object' ? { uid: String(x.au.uid || '').slice(0, 64), name: cleanNick(x.au.name) } : null, k: { sig: d.dpk.sig, dh: d.dpk.dh } };
            var watch = d.want === 'watch', late = lateFor(S.gameId), inPlay = S.phase !== 'lobby' && S.phase !== 'result';
            if (watch || (inPlay && late !== 'anytime')) { m.r = 'spec'; if (!watch) m.wq = true; }
            else {
                var fs = this._freeSeat(S.gameId);
                if (fs === -1) { m.r = 'spec'; m.wq = true; } else m.seat = (mem.seat != null && this._seatFree(mem.seat)) ? mem.seat : fs;
            }
            S.roster.push(m);
        } else {
            m.c = 'on'; m.k = { sig: d.dpk.sig, dh: d.dpk.dh };
            if (x.nick) m.n = nick;
            if (x.av !== undefined) m.av = Math.max(0, Math.min(15, x.av | 0));
        }
        var mb = H.members[p] || (H.members[p] = memRec(m.k, 0));
        mb.k = m.k; mb.lastC = Math.max(mb.lastC, env.c); mb.seen = t; mb.bye = false; mb.vis = 'visible';
        mb.fastUntil = t + 15000;
        if (typeof d.t0 === 'number') { mb.t0 = null; }
        H.known[p] = 1;
        this._recalcSucc();
        var st = this._pubState();
        var stj = JSON.stringify(st);
        var inner = { ok: true, role: m.r, seat: m.seat, nick: m.n, mk: this.sealed ? b64u(H.mkRaw[this._kv]) : undefined, kv: this._kv,
            st: stj.length <= MAXJ ? st : undefined, ec: typeof d.t0 === 'number' ? [d.t0, rx] : undefined, t2: now() };
        var blob = await eciesEnc(d.dpk.dh, this.code, 'welcome', inner);
        this._hsend('welcome', { x: blob }, { to: p, reliable: true });
        this._rosterDirty();
        this._dirty();
        if (!back) this.emit('join', m);
        dbg('admit', p, back ? (wasOff ? 'back' : 'rejoin') : 'new');
    };
    Room.prototype._seatFree = function (s) { return !this._S.roster.some(function (m) { return m.seat === s; }); };
    Room.prototype._recalcSucc = function () {
        var S = this._S, me = this.me.pid;
        var list = S.roster.filter(function (m) { return m.r !== 'bot' && m.p !== me && m.c !== 'off'; })
            .sort(function (a, b) { var sa = a.seat != null ? 0 : 1, sb = b.seat != null ? 0 : 1; return sa - sb || a.j - b.j; })
            .map(function (m) { return m.p; });
        var off = S.roster.filter(function (m) { return m.r !== 'bot' && m.p !== me && m.c === 'off'; }).sort(function (a, b) { return a.j - b.j; }).map(function (m) { return m.p; });
        var succ = list.concat(off);
        if (canon(succ) === canon(S.succ || []) && S.succe === this.ep && S.succz) return false;
        S.succ = succ; S.succe = this.ep; S.succz = null;
        var self = this, ep = this.ep;
        this._succP = signStr(this._H.sk, succMsg(this.code, ep, succ)).then(function (z) { if (canon(S.succ) === canon(succ) && S.succe === ep) S.succz = z; });
        return true;
    };
    Room.prototype.pending = function () {
        if (!this._H) return [];
        var P = this._H.pending, out = [];
        Object.keys(P).forEach(function (p) { if (now() - P[p].t < TM.pendingMax) out.push({ p: p, n: cleanNick(P[p].x.nick) || 'Guest', av: P[p].x.av | 0, flag: P[p].flag }); });
        return out;
    };

    /* ── 상태 방송 (§6.0.1·§6.0.2) ──────────────────────────────── */
    function diffOps(a, b, path, ops) {
        if (canon(a) === canon(b)) return ops;
        if (a && b && typeof a === 'object' && typeof b === 'object' && !Array.isArray(a) && !Array.isArray(b)) {
            var ks = {}; Object.keys(a).forEach(function (k) { ks[k] = 1; }); Object.keys(b).forEach(function (k) { ks[k] = 1; });
            Object.keys(ks).forEach(function (k) {
                if (!(k in b)) ops.push({ p: path.concat(k), d: 1 });
                else if (!(k in a)) ops.push({ p: path.concat(k), v: b[k] });
                else diffOps(a[k], b[k], path.concat(k), ops);
            });
            return ops;
        }
        ops.push({ p: path, v: b });
        return ops;
    }
    function applyOps(o, ops) {
        ops.forEach(function (op) {
            if (!op || !Array.isArray(op.p) || !op.p.length) return;
            var t = o;
            for (var i = 0; i < op.p.length - 1; i++) { var k = op.p[i]; if (k === '__proto__' || k === 'constructor' || k === 'prototype') return; if (t[k] == null || typeof t[k] !== 'object') t[k] = {}; t = t[k]; }
            var last = op.p[op.p.length - 1]; if (last === '__proto__' || last === 'constructor' || last === 'prototype') return;
            if (op.d) delete t[last]; else t[last] = op.v;
        });
    }
    Room.prototype._view = function (pid) {
        var S = this._S;
        if (_adapter && _adapter.gameId === S.gameId && typeof _adapter.view === 'function') { try { return _adapter.view(S.game, pid) || { pub: S.game }; } catch (e) { dbg('view', e); } }
        return null;
    };
    Room.prototype._pubState = function () {
        var S = clone(this._S), v = this._view(null);
        if (v) S.game = v.pub;
        S.inv = this.sealed ? this._H.tok : undefined;
        S.bans = Object.keys(this._H.bans);
        S.pinReq = !!this._H.pinReq;
        return S;
    };
    Room.prototype.setState = function (fn, o) {
        if (!this.isHost) throw new Error('LpRooms: setState is host-only');
        var S = this._S;
        if (typeof fn === 'function') { var r = fn(S); if (r && r !== S && typeof r === 'object') { r.roster = S.roster; r.v = 2; this._S = S = r; } }
        S.seq++;
        if (Array.isArray(S.log) && S.log.length > 64) S.log = S.log.slice(-64);
        var ci = this._H.curI; if (ci && !ci.acked) { this._H.ackQ.push([ci.p, ci.c]); ci.acked = true; }
        this._H.stateDirty = true;
        if (o && o.full) this._H.forceFull = true;
        this._schedFlush();
        return S.seq;
    };
    Room.prototype._schedFlush = function () {
        var self = this, H = this._H;
        if (H.flushQ) return; H.flushQ = true;
        Promise.resolve().then(function () { H.flushQ = false; if (H.stateDirty) self._flushState(!!H.forceFull); });
    };
    Room.prototype._flushState = function (full) {
        var H = this._H; if (!H || this._left) return;
        H.stateDirty = false; H.forceFull = false;
        var prevLocal = this._lastLocal || null;
        var st = this._pubState();
        var acks = H.ackQ.splice(0);
        var useDelta = !full && _adapter && _adapter.gameId === this._S.gameId && _adapter.delta && H.lastB && (++H.nB % 10) !== 0;
        if (useDelta) {
            var ops = diffOps(H.lastB, st, [], []);
            this._hsend('delta', { base: H.lastB.seq, seq: st.seq, ops: ops, a: acks.length ? acks : undefined });
        } else {
            if (acks.length) st._a = acks;
            this._hsend('state', st);
            delete st._a; H.nB = 0;
        }
        H.lastB = st;
        clearTimeout(H.rosterT); H.rosterT = 0;
        /* 숨은 정보: 좌석별 priv (§6.0.1) */
        var self = this;
        if (_adapter && _adapter.gameId === this._S.gameId && typeof _adapter.view === 'function') {
            this._S.roster.forEach(function (m) {
                if (m.r === 'bot' || m.p === self.me.pid || !m.k) return;
                var v = self._view(m.p); if (!v || v.priv === undefined) return;
                var h = canon(v.priv); if (H.privH[m.p] === h) return;
                H.privH[m.p] = h; self.sendTo(m.p, '_view', v.priv);
            });
            var mine = this._view(this.me.pid); if (mine && mine.priv !== undefined) this.emit('priv', mine.priv, '_view');
        }
        this._syncMe();   /* 방장이 자기 좌석·역할을 바꾼 setState(턴 커널 시작·자리 넘기기) 도 me 에 바로 반영 */
        this._lastLocal = clone(this._S);
        this.emit('state', this._S, prevLocal);
        if (!prevLocal || prevLocal.phase !== this._S.phase) this.emit('phase', this._S.phase, this._S);
        this._dirty();
    };
    Room.prototype._rosterDirty = function () {
        var self = this, H = this._H; if (!H) return;
        this._recalcSucc();
        if (H.rosterT) return;
        H.rosterT = setTimeout(function () {
            H.rosterT = 0; if (self._left || !self._H) return;
            Promise.resolve(self._succP).then(function () {
                var S = self._S, acks = H.ackQ.splice(0);
                self._hsend('roster', { r: S.roster, succ: S.succ, sz: S.succz, se: S.succe, lock: S.lock, appr: !!(S.appr || now() < H.apprAuto), a: acks.length ? acks : undefined });
                var prev = self._lastRoster || [];
                self._lastRoster = clone(S.roster);
                self._syncMe(); self._rosterDelta(prev, S.roster);
                self._dirty();
            });
        }, TM.rosterGap);
    };

    /* ── 의도 처리 (§6.0.7) ──────────────────────────────────────── */
    Room.prototype.onIntent = function (cb) { if (this._H) this._H.intentCb = cb; this._intentCb = cb; };
    Room.prototype._replyIntent = function (p, c, r) {
        if (r.ok) this._hsend('ack', { c: c, seq: r.seq }, { to: p });
        else this._hsend('nack', { c: c, r: r.reason, seq: this._S.seq }, { to: p });
    };
    Room.prototype._hostIntent = async function (p, c, d) {
        var H = this._H, mb = H.members[p], m = this._member(p);
        if (!m) return;
        var r, cur = H.curI = { p: p, c: c, acked: false };
        if (!mb.ib.take()) r = { ok: false, reason: 'rate' };
        else r = await this._runIntent(m, d.a, d.x, { c: c, es: typeof d.es === 'number' ? d.es : undefined });
        H.curI = null;
        mb.ic[c] = r; mb.icN.push(c); if (mb.icN.length > 32) delete mb.ic[mb.icN.shift()];
        /* 수락 응답 = 그 변경을 싣는 state/roster 방송(_a). 방송이 없을 때만 ack 1통 */
        if (r.ok && cur.acked) return;
        if (r.ok && r.viaFlush && (H.rosterT || H.stateDirty || H.flushQ)) { H.ackQ.push([p, c]); return; }
        this._replyIntent(p, c, r);
    };
    Room.prototype._runIntent = async function (m, a, x, ctx) {
        var H = this._H, S = this._S;
        if (!m) return { ok: false, reason: 'not_member' };
        var seq0 = S.seq, rost0 = !!H.rosterT;
        var k = this._kernelIntent(m, a, x);
        if (k) return k;
        if (ctx.es !== undefined && ctx.es !== S.seq && !(_adapter && typeof _adapter.commutes === 'function' && _adapter.commutes(a))) return { ok: false, reason: 'stale' };
        var cb = H.intentCb || this._intentCb;
        if (!cb) return { ok: false, reason: 'no_handler' };
        var res;
        try { res = cb(clone(m), a, x, ctx); if (res && typeof res.then === 'function') res = await res; }
        catch (e) { dbg('intent handler', e); return { ok: false, reason: 'error' }; }
        if (res === false) return { ok: false, reason: 'rejected' };
        if (res && typeof res === 'object' && res.reject) return { ok: false, reason: String(res.reject) };
        return { ok: true, seq: this._S.seq, viaFlush: this._S.seq !== seq0 || (!rost0 && !!H.rosterT) };
    };
    Room.prototype._kernelIntent = function (m, a, x) {
        var S = this._S, self = this;
        function done() { self._rosterDirty(); return { ok: true, seq: S.seq, viaFlush: true }; }
        if (a === 'ready') {
            if (S.phase !== 'lobby' && S.phase !== 'result') return { ok: false, reason: 'phase' };
            m = this._member(m.p); m.rd = !!x; return done();
        }
        if (a === 'back') { m = this._member(m.p); m.afk = false; return done(); }
        if (a === 'pick') {
            if (!x || typeof x.key !== 'string' || typeof x.val !== 'string' || x.val.length > 32) return { ok: false, reason: 'bad' };
            var spec = null, picks = (_adapter && _adapter.gameId === S.gameId && _adapter.picks) || ((reg(S.gameId) || {}).mp || {}).choices && reg(S.gameId).mp.choices.picks || [];
            picks.forEach(function (pk) { if (pk.key === x.key) spec = pk; });
            if (!spec) return { ok: false, reason: 'bad' };
            if (spec.options && spec.options.indexOf(x.val) < 0) return { ok: false, reason: 'bad' };
            m = this._member(m.p);
            if (spec.unique) {
                var holder = S.roster.filter(function (o) { return o.p !== m.p && o.pick && o.pick[x.key] === x.val; })[0];
                if (holder) {
                    if (holder.r === 'bot' && spec.botYield !== false) { holder.pick[x.key] = (m.pick && m.pick[x.key]) || this._freePick(spec, x.val); }
                    else return { ok: false, reason: 'taken' };
                }
            }
            m.pick = m.pick || {}; m.pick[x.key] = x.val;
            S.mem = S.mem || {}; (S.mem[S.gameId] || (S.mem[S.gameId] = {}))[m.p] = { pick: clone(m.pick), seat: m.seat };
            return done();
        }
        if (a === 'role') {
            m = this._member(m.p);
            if (x === 'watch') { m.r = m.r === 'host' ? 'host' : 'spec'; if (m.r === 'spec') { m.seat = null; m.rd = false; } return done(); }
            if (x === 'play') {
                if (m.r !== 'spec') return { ok: true, seq: S.seq };
                if (S.phase !== 'lobby' && S.phase !== 'result' && lateFor(S.gameId) !== 'anytime') { m.wq = true; return done(); }
                var fs = this._freeSeat(S.gameId); if (fs === -1) return { ok: false, reason: 'no_seat' };
                m.r = 'player'; m.seat = fs; delete m.wq; return done();
            }
            return { ok: false, reason: 'bad' };
        }
        return null;
    };
    Room.prototype._freePick = function (spec, avoid) {
        var S = this._S, used = {}; S.roster.forEach(function (m) { if (m.pick && m.pick[spec.key]) used[m.pick[spec.key]] = 1; });
        var opts = spec.options || []; for (var i = 0; i < opts.length; i++) if (!used[opts[i]] && opts[i] !== avoid) return opts[i];
        return null;
    };

    /* ── 방장 루프: 하트비트·연결 판정·저장 ─────────────────────── */
    Room.prototype._hostLoops = function () {
        var self = this;
        this._timer(function () { self._hostTick(); }, 1000, true);
        this._timer(function () { self._connCheck(); }, 2000, true);
    };
    Room.prototype._hostTick = function () {
        var H = this._H; if (!H || this._left) return;
        var t = now(), n = this._humans().length - 1;
        var iv = n > 0 ? TM.hostHb : TM.hostHbAlone;
        if (t - H.lastHb >= iv || (this._hbSoon && t >= this._hbSoon)) this._sendHostHb();
        if (H.dirty && t - H.saveT > 1000) this._save();
        /* 예산 가드 (§7.3): 1분 이동평균 추정 msg/s > 25 → 게스트 hb 1.5배 */
        var est = estRate(this._humans().length);
        if (est > 25 && !this._S.hbx) { dbg('budget guard', est); this.setState(function (S) { S.hbx = 1.5; }); }
    };
    function estRate(N) { return STATS.win.length / 60 * Math.max(1, N); }
    Room.prototype._sendHostHb = function () {
        var H = this._H, t = now(), ec = {}, any = false, self = this;
        Object.keys(H.members).forEach(function (p) { var mb = H.members[p]; if (mb.t0 != null) { ec[p] = [mb.t0, mb.t1]; mb.t0 = null; any = true; } });
        var d = { t: t, hs: H.s, vis: (G.document && G.document.visibilityState) || 'visible' };
        if (any) d.ec = ec;
        for (var k in this._hbX) d[k] = this._hbX[k];
        this._hbX = {}; this._hbSoon = 0; H.lastHb = t;
        this._hsend('hb', d);
    };
    Room.prototype._connCheck = function () {
        var H = this._H, S = this._S; if (!H || this._left) return;
        var t = now(), ch = false, inPlay = S.phase === 'playing' || S.phase === 'starting' || S.phase === 'paused', self = this, rm = [];
        S.roster.forEach(function (m) {
            if (m.r === 'bot' || m.p === self.me.pid) return;
            var mb = H.members[m.p]; if (!mb) return;
            var silent = t - mb.seen, hidden = mb.vis === 'hidden';
            if (m.r === 'spec') {
                if (silent > TM.offSpec) rm.push(m.p);
                else if (silent > TM.offLobby && m.c !== 'off') { m.c = 'off'; mb.offAt = t; ch = true; }
                return;
            }
            var offAfter = inPlay && m.seat != null ? TM.offPlay : (hidden ? TM.offLobbyHidden : TM.offLobby);
            if (m.c !== 'off' && (silent > offAfter || mb.bye)) { m.c = 'off'; mb.offAt = mb.offAt || t; ch = true; }
            if (m.c === 'off' && !inPlay && t - Math.max(mb.offAt, mb.seen) > TM.rmLobby) rm.push(m.p);
        });
        if (rm.length) {
            S.roster = S.roster.filter(function (m) { return rm.indexOf(m.p) < 0; });
            rm.forEach(function (p) { delete H.members[p]; }); ch = true;
        }
        Object.keys(H.pending).forEach(function (p) { if (t - H.pending[p].t > TM.pendingMax) delete H.pending[p]; });
        if (ch) this._rosterDirty();
    };
    Room.prototype._dirty = function () { if (this._H) this._H.dirty = true; };
    Room.prototype._save = function () {
        var H = this._H; if (!H) return;
        H.dirty = false; H.saveT = now();
        var mem = {};
        Object.keys(H.members).forEach(function (p) { mem[p] = { k: H.members[p].k, lastC: H.members[p].lastC }; });
        var mk = {}; Object.keys(H.mkRaw).forEach(function (k) { mk[k] = b64u(H.mkRaw[k]); });
        var blob = { v: 2, code: this.code, ep: this.ep, s: H.s, t: H.t, S: this._S, mk: mk, kv: this._kv, tok: H.tok, pin: H.pin, pinReq: H.pinReq,
            max: H.max, sealed: this.sealed, members: mem, known: H.known, bans: H.bans, banNicks: H.banNicks, apprAuto: H.apprAuto, fs: H.fs,
            rpk: this._rpk, chain: this._chain, devHost: !!H.devHost, prevPk: this._prevHostPk || null, saved: now() };
        ssSet('lpr_host_' + this.code, JSON.stringify(blob));
        setActive({ code: this.code, role: 'host', gameId: this._S.gameId, t: now() });
    };

    /* ── 방장 API ────────────────────────────────────────────────── */
    function hostOnly(r) { if (!r.isHost) throw new Error('LpRooms: host-only'); }
    Room.prototype.sendTo = function (pid, e, d) {
        hostOnly(this);
        var m = this._member(pid), self = this; if (!m || !m.k) return;
        eciesEnc(m.k.dh, this.code, 'priv', d).then(function (x) { self._hsend('priv', { e: String(e), x: x }, { to: pid, reliable: true }); });
    };
    Room.prototype.tick = function (d) {
        hostOnly(this);
        var t = now(); if (t - this._H.tickAt < 48) return; this._H.tickAt = t;
        this._hsend('tick', d);
    };
    Room.prototype._phase = function (ph, startAt) {
        var S = this._S;
        S.phase = ph; S.startAt = startAt == null ? null : startAt;
        this._hsend('phase', { phase: ph, startAt: S.startAt }, { reliable: true });
        this.setState(null);
    };
    Room.prototype.start = function (o) {
        hostOnly(this);
        var cd = Math.max(0, Math.min(10000, (o && o.countdownMs != null) ? o.countdownMs : 1500)), self = this, t = now();
        this._S.roster.forEach(function (m) { if (m.r === 'spec' && m.wq) delete m.wq; });
        this._phase('starting', t + cd);
        clearTimeout(this._startT);
        this._startT = setTimeout(function () { if (!self._left && self.isHost && self._S.phase === 'starting') self._phase('playing', t + cd); }, cd);
    };
    Room.prototype.toLobby = function () {
        hostOnly(this);
        var S = this._S, self = this;
        S.lock = false;
        S.roster.forEach(function (m) {
            if (m.r === 'player') m.rd = false;
            if (m.r === 'spec' && m.wq) { var fs = self._freeSeat(S.gameId); if (fs !== -1) { m.r = 'player'; m.seat = fs; delete m.wq; } }
        });
        this._phase('lobby', null);
        this._rosterDirty();
    };
    Room.prototype.pause = function () { hostOnly(this); if (this._S.phase === 'playing') this._phase('paused', this._S.startAt); };
    Room.prototype.resume = function () { hostOnly(this); if (this._S.phase === 'paused') this._phase('playing', this._S.startAt); };
    Room.prototype.end = function () { hostOnly(this); this._phase('result', this._S.startAt); };
    Room.prototype.close = function () {
        hostOnly(this);
        var self = this, code = this.code;
        this._hsend('close', {}, { reliable: true });
        ssSet('lpr_host_' + code, null);
        idbDel('room:' + code).catch(function () {});
        setTimeout(function () { self.emit('closed', { reason: 'host' }); self._teardown('closed', true); }, 700);
    };
    Room.prototype.switchGame = function (gid) {
        hostOnly(this);
        if (!regOk(gid)) return false;
        var S = this._S;
        S.gameId = gid; this.gameId = gid; S.phase = 'lobby'; S.startAt = null; S.lock = false; S.game = null;
        S.roster.forEach(function (m) { if (m.r === 'player') m.rd = false; var mm = S.mem && S.mem[gid] && S.mem[gid][m.p]; m.pick = mm && mm.pick ? mm.pick : {}; });
        this.setState(null, { full: true });
        this._hsend('switch', { gameId: gid }, { reliable: true });
        this._save();
        this._onSwitch(gid);
        return true;
    };
    Room.prototype.kick = function (pid, o) {
        hostOnly(this);
        var H = this._H, S = this._S, m = this._member(pid), self = this;
        if (!m || pid === this.me.pid || m.r === 'bot') { if (m && m.r === 'bot') { S.roster = S.roster.filter(function (x) { return x.p !== pid; }); this._rosterDirty(); } return; }
        var ban = !!(o && o.ban);
        this._hsend('kicked', { ban: ban }, { to: pid, reliable: true });
        S.roster = S.roster.filter(function (x) { return x.p !== pid; });
        delete H.members[pid]; delete H.known[pid]; delete H.pending[pid];
        if (ban) { H.bans[pid] = 1; H.banNicks[nickKey(m.n)] = 1; H.apprAuto = now() + 600000; }
        this._rekey();
        this._rosterDirty();
        if (ban) this.setState(null);
    };
    Room.prototype.unban = function (pid) { hostOnly(this); delete this._H.bans[pid]; this.setState(null); };
    Room.prototype._rekey = async function () {
        if (!this.sealed) return;
        var H = this._H, raw = rand(32), kv = this._kv + 1, self = this;
        H.mkRaw[kv] = raw;
        var key = await aesKey(raw);
        var targets = this._S.roster.filter(function (m) { return m.r !== 'bot' && m.p !== self.me.pid && m.k; });
        for (var i = 0; i < targets.length; i++) {
            var x = await eciesEnc(targets[i].k.dh, this.code, 'rekey', { mk: b64u(raw), kv: kv });
            this._hsend('rekey', { x: x }, { to: targets[i].p, reliable: true });
        }
        this._mk[kv] = key; this._kv = kv;
        this._dirty();
    };
    Room.prototype._resendRekey = function (pid) {
        var H = this._H, m = this._member(pid), self = this; if (!m || !m.k || !this.sealed) return;
        var kv = this._kv;
        eciesEnc(m.k.dh, this.code, 'rekey', { mk: b64u(H.mkRaw[kv]), kv: kv }).then(function (x) { self._hsend('rekey', { x: x }, { to: pid }); });
    };
    Room.prototype.lock = function (on) { hostOnly(this); this._S.lock = !!on; this.setState(null); };
    Room.prototype.approval = function (on) { hostOnly(this); this._S.appr = !!on; if (!on) this._H.apprAuto = 0; this.setState(null); };
    /* [+] 방장 도구 공개 API — UI 가 room._H 를 직접 만지지 않게 (2026-09-30 통합) */
    Room.prototype.setApproval = function (on) { this.approval(on); return !!this._S.appr; };
    Room.prototype.setPin = function (on, pin) {
        hostOnly(this);
        var H = this._H;
        H.pinReq = !!on;
        if (on) H.pin = /^\d{4}$/.test(String(pin == null ? '' : pin)) ? String(pin) : (/^\d{4}$/.test(String(H.pin || '')) ? String(H.pin) : pin4());
        else H.pin = null;
        this.pin = H.pin || undefined;
        this._S.pinReq = !!on;
        this.setState(null);
        this._dirty();
        return H.pin || null;
    };
    Room.prototype.approve = function (pid, ok) {
        hostOnly(this);
        var P = this._H.pending[pid]; if (!P) return;
        delete this._H.pending[pid];
        if (ok) this._admit(pid, P.d, P.x, P.env); else this._deny(pid, 'denied');
        this.emit('pending', this.pending());
    };
    Room.prototype.rotateLink = function () { hostOnly(this); this._H.tok = rid(16); this.setState(null); this._dirty(); return this.inviteUrl(); };
    Room.prototype.transferHost = function (pid) {
        hostOnly(this);
        var m = this._member(pid), self = this;
        if (!m || m.r === 'bot' || pid === this.me.pid || m.c === 'off' || !this._migratable()) return false;
        var ep = this.ep, succ = [pid];
        signStr(this._H.sk, succMsg(this.code, ep, succ)).then(function (z) { self._hsend('th', { succ: succ, ep: ep, z: z }, { to: pid, reliable: true }); });
        return true;
    };

    /* ================================================================
       승계 (§6.0.6)
       ================================================================ */
    Room.prototype._becomeHost = async function (o) {
        if (this.isHost || this._left) return;
        var S = this._S, dev = this._dev, self = this;
        var link;
        if (o.transfer) {
            var tr = o.transfer;
            if (!Array.isArray(tr.succ) || tr.succ[0] !== this.me.pid || !(await verifyStr(this._hostPk, succMsg(this.code, tr.ep, tr.succ), tr.z))) return;
            link = { succ: tr.succ, ep: tr.ep, z: tr.z, npk: { sig: dev.sig.pub, dh: dev.dh.pub } };
        } else {
            if (!S.succz || !Array.isArray(S.succ) || S.succ.indexOf(this.me.pid) < 0) return;
            link = { succ: S.succ, ep: S.succe, z: S.succz, npk: { sig: dev.sig.pub, dh: dev.dh.pub } };
        }
        var oldHost = this._hostMember(), ep2 = Math.max(now(), this.ep + 1), fromSeq = S.seq;
        this._takeBy = this.me.pid;
        this._prevHostPk = this._hostPk; this._prevHostDh = this._hostDh; this._prevEp = this.ep;
        this._chain = (this._chain || []).concat([link]);
        var tk = { ep2: ep2, fromSeq: fromSeq, sh: hex(await sha256(canon(S))).slice(0, 16), link: link };
        /* 방장 모드로 전환 — 같은 Room 객체 */
        var H = this._H = newH({ sk: dev.sig.priv, dk: dev.dh.priv, tok: S.inv || rid(16), pinReq: !!S.pinReq, pin: null, fs: this._fst || {}, bans: {}, banNicks: {} });
        H.devHost = true;
        (S.bans || []).forEach(function (p) { H.bans[p] = 1; });
        H.mkRaw = {}; this._mkRawFromGuest(H);
        this.isHost = true; this._hostPk = dev.sig.pub; this._hostDh = dev.dh.pub;
        this.ep = ep2; this._lastS = null;
        S.roster.forEach(function (m) {
            if (m.r === 'host') { m.r = 'player'; m.c = 'off'; }
            if (m.p === self.me.pid) { m.r = 'host'; m.c = 'on'; }
            if (m.r !== 'bot' && m.p !== self.me.pid && m.k) { H.members[m.p] = memRec(m.k, self._peerC[m.p] ? (self._peerC[m.p].lastC || 0) : 0); H.known[m.p] = 1; if (!self._peerAlive(m.p)) m.c = 'off'; }
        });
        this.me.role = 'host';
        this._clearTimers(); this._hostLoops();
        this._state = 'member';
        await this._gsend('takeover', tk);   /* isHost 이지만 takeover 는 기기 키 서명 'g' 로 */
        this._recalcSucc();
        this.setState(null, { full: true });
        this._sendHello();
        this.emit('takeover', { pid: this.me.pid, ep: ep2 });
        this._save();
        dbg('became host', ep2, oldHost && oldHost.p);
        /* 1.5초 동안 더 높은 seq 제안을 받는다 */
        this._offerUntil = now() + 1500;
    };
    Room.prototype._mkRawFromGuest = function (H) {
        var raw = this._mkRawG || {};
        Object.keys(raw).forEach(function (k) { H.mkRaw[k] = raw[k]; });
    };
    Room.prototype._stateOffer = function (p, d) {
        if (!this.isHost || !this._offerUntil || now() > this._offerUntil || !d || !d.S || d.S.v !== 2) return;
        if (d.S.seq > this._S.seq) {
            var me = this.me.pid, roster = this._S.roster;
            var S2 = d.S; S2.roster = roster; this._S = S2;
            dbg('adopted state_offer from', p, S2.seq);
            this.setState(null, { full: true });
        }
    };
    Room.prototype._onTakeover = async function (p, d) {
        if (!d || !d.link || !d.link.npk || typeof d.ep2 !== 'number') return;
        var S = this._S, L = d.link;
        if ((await pidOf(L.npk.sig)) !== p) return;
        var curKey = this.isHost ? (this._prevHostPk || this._hostPk) : this._hostPk;
        var transfer = Array.isArray(L.succ) && L.succ.length === 1 && L.succ[0] === p && L.ep === (this.isHost && this._prevEp ? this._prevEp : this.ep);
        /* 링크 서명: 지금(또는 직전) 방장 키가 서명한 succ 에 p 가 있어야 */
        var keyOk = await verifyStr(curKey, succMsg(this.code, L.ep, L.succ), L.z);
        if (!keyOk && this.isHost && !this._prevHostPk) keyOk = await verifyStr(this._hostPk, succMsg(this.code, L.ep, L.succ), L.z);
        if (!keyOk || L.succ.indexOf(p) < 0) return;
        var idx = L.succ.indexOf(p);
        if (this.isHost) {
            /* 나는 방장인데 누군가 승계를 선언: 원방장이면 강등, 승계 방장이면 더 앞 순번에게 양보 */
            var myIdx = L.succ.indexOf(this.me.pid);
            if (this._takeBy === this.me.pid && myIdx >= 0 && myIdx < idx) return;
            dbg('demote: takeover by', p);
            return this._demote(p, d);
        }
        if (!transfer && this._wd < 2) return;              /* 나는 방장이 아직 들린다 → 무시 */
        if (this._takeBy && this._takeBy !== p) {
            var cur = L.succ.indexOf(this._takeBy);
            if (cur >= 0 && cur <= idx) return;
        }
        this._acceptHost(p, d);
    };
    Room.prototype._acceptHost = function (p, d) {
        var S = this._S, L = d.link, self = this;
        this._takeBy = p;
        this._hostPk = L.npk.sig; this._hostDh = L.npk.dh;
        this._chain = (this._chain || []).concat([L]);
        this.ep = d.ep2; this._lastS = null; this._buf = {}; this._lastT = 0; this._gaps = [];
        this._lastHostAt = now(); this._wd = 0;
        S.roster.forEach(function (m) { if (m.r === 'host') { m.r = 'player'; m.c = 'off'; } if (m.p === p) m.r = 'host'; });
        this._syncMe();
        this.emit('takeover', { pid: p, ep: d.ep2 });
        this.emit('hostback');
        if (S.seq > d.fromSeq) this._gsend('state_offer', { seq: S.seq, S: S });
        setActive({ code: this.code, role: 'guest', gameId: S.gameId, want: this._want, inv: this._inv });
    };
    Room.prototype._demote = function (p, d) {
        var self = this;
        this._clearTimers();
        this.isHost = false; this._H = null; this._prevHostPk = null;
        if (this._hostRel) { try { this._hostRel(); } catch (_) {} this._hostRel = null; }
        this.emit('demoted', { by: p });
        this._acceptHost(p, d);
        this._wd = 0; this._takeBy = p;
        this._guestLoops();
        ssSet('lpr_host_' + this.code, null);
        /* 새 방장에게 알려진 pid 로 다시 인사(복귀) */
        this._rejoin();
    };
    Room.prototype._hostSeesH = async function (env) {
        /* 방장이 남의 'h' 를 듣는 경우: 내가 끊긴 사이 누군가 승계했다 → 게스트로 합류 */
        /* (a) 다른 기기 키로 서명된 더 높은 epoch 방송 = 누가 승계했다(내가 끊겨 있던 사이) →
               hello 를 청해 승계 체인을 받고 (b) 에서 게스트로 합류. 되찾기 없음(§6.0.6-5) */
        if (env.e !== 'hello' && env.ep > this.ep && now() - (this._fgnAt || 0) > 3000) {
            this._fgnAt = now();
            var S0 = this._S, me0 = this.me.pid;
            for (var i = 0; i < S0.roster.length; i++) {
                var m0 = S0.roster[i];
                if (m0.p === me0 || !m0.k || m0.r === 'bot') continue;
                if (await verifyStr(m0.k.sig, hSigStr(this.code, env), env.z)) { dbg('successor detected', m0.p); this._rawSend('g', { v: 2, e: 'hello_req', n: rid(6) }); break; }
            }
            return;
        }
        if (env.e === 'hello' && typeof env.j === 'string') {
            var h = jparse(env.j, null);
            if (h && h.chain && h.rpk && this._rpk && h.rpk.sig === this._rpk.sig && h.hk && h.hk.sig !== this._hostPk) {
                var fk = await chainKey(this.code, h.rpk, h.chain);
                if (fk && fk === h.hk.sig && await verifyStr(fk, hSigStr(this.code, env), env.z)) {
                    dbg('hello chain shows successor → demote');
                    var last = h.chain[h.chain.length - 1];
                    this._chain = h.chain.slice(0, -1);
                    this._demote(await pidOf(fk), { link: last, ep2: h.ep, fromSeq: 0 });
                }
            }
        }
    };
    Room.prototype._rejoin = async function () {
        var self = this;
        try {
            var env = await this._genv('join', await this._joinPayload({}), { plain: true });
            this._rawSend('g', env);
        } catch (e) { dbg('rejoin', e); }
    };
    Room.prototype._joinPayload = async function (o) {
        var prof = profile.get(), x = { nick: prof.nick, av: prof.av };
        if (o.tok) x.tok = o.tok;
        if (o.pin) x.pin = String(o.pin);
        var hdh = this._hostDh;
        return { v: 2, dpk: { sig: this._dev.sig.pub, dh: this._dev.dh.pub }, g: o.g || undefined, want: o.want || this._want || 'play', t0: now(), x: hdh ? await eciesEnc(hdh, this.code, 'join', x) : undefined };
    };

    /* 멤버: welcome 적용 (최초 참가·재참가 공용) */
    Room.prototype._onWelcome = async function (env, inner) {
        this.ep = env.ep; this._lastS = env.s; this._buf = {}; this._gaps = [];
        if (inner.mk) {
            var raw = ub64u(inner.mk), kv = inner.kv | 0;
            this._mkRawG = this._mkRawG || {}; this._mkRawG[kv] = raw;
            this._mk[kv] = await aesKey(raw); if (kv > this._kv) this._kv = kv;
            this.sealed = true;
        } else if (!this._kv) this.sealed = false;
        if (inner.ec && typeof inner.t2 === 'number') this._clockSample(inner.ec[0], inner.ec[1], inner.t2, rxOf(env));
        this._lastHostAt = now(); this._wd = 0;
        if (inner.st) this._applyS(inner.st); else this._snapReq(true);
        this._syncMe();
    };

    /* ── Web Lock (한 기기 = 방 안 한 자리, §2.5) ──────────────────── */
    function acquireLock(name, steal) {
        return new Promise(function (res) {
            var L = G.navigator && G.navigator.locks;
            if (!L || typeof L.request !== 'function') { res({ ok: true, release: function () {} }); return; }
            var rel, out = { ok: true, lost: null }, held = new Promise(function (r) { rel = r; });
            out.release = function () { out.lost = null; if (rel) rel(); };
            L.request(name, steal ? { steal: true } : { ifAvailable: true }, function (lock) {
                if (!lock) { res({ ok: false }); return; }
                res(out); return held;
            }).catch(function (e) { if (e && e.name === 'AbortError' && out.lost) out.lost(); });
        });
    }
    Room.prototype._detach = function () {
        if (this._left) return;
        dbg('seat stolen by another tab → detached');
        this._seatRel = null;
        this.emit('detached');
        this._teardown('detached', false);   /* bye 안 보냄 — 같은 pid 라 방장 쪽 좌석 그대로 */
    };

    /* ── 세션 저장 키 (§8.5) ─────────────────────────────────────── */
    function getActive() { return jparse(ssGet('lpr_active'), null); }
    function setActive(a) { if (!a) ssSet('lpr_active', null); else { a.t = now(); ssSet('lpr_active', JSON.stringify(a)); } }
    function addRecent(code, gid, host) {
        var list = jparse(lsGet('lpr_recent'), []);
        if (!Array.isArray(list)) list = [];
        list = list.filter(function (x) { return x && x.code !== code; });
        list.unshift({ code: code, g: gid, h: host || '', t: now() });
        lsSet('lpr_recent', JSON.stringify(list.slice(0, 5)));
    }
    function invFromSession(code) { var v = jparse(ssGet('lpr_inv'), null); return v && v.code === code && v.fp ? { fp: v.fp, tok: v.tok } : null; }
    /* 인앱 브라우저가 곧 외부 브라우저로 탈출할 예정이면 신원·핸드셰이크를 만들지 않는다(§2.3) — 신원이 한 번만 생기게 */
    function inAppEscaping() { try { return !!(G.LpInApp && typeof G.LpInApp.willEscape === 'function' && G.LpInApp.willEscape()); } catch (_) { return false; } }
    function err(reason, extra) { var e = new Error('LpRooms: ' + reason); e.reason = reason; if (extra) for (var k in extra) e[k] = extra[k]; return e; }

    /* ── hello 검증 (코드 = 방장 키 지문, 링크면 128비트 지문 고정) ─── */
    async function verifyHello(code, h, env, inv) {
        if (!h || h.v !== 2 || h.code !== code || !h.rpk || !h.hk || typeof h.rpk.sig !== 'string' || typeof h.rpk.dh !== 'string') return { ok: false };
        var F = await roomF(h.rpk);
        if (codeOfF(F) !== code) return { ok: false };
        if (inv && inv.fp && fpOfF(F) !== inv.fp) return { ok: false, badFp: true };
        var key = await chainKey(code, h.rpk, h.chain);
        if (!key || key !== h.hk.sig) return { ok: false };
        if (!(await verifyStr(key, hSigStr(code, env), env.z))) return { ok: false };
        return { ok: true, F: F, key: key };
    }
    function chainLen(h) { return h && Array.isArray(h.chain) ? h.chain.length : 0; }
    /* 두 hello 가 같은 방의 승계 관계인가(더 긴 체인이 더 최근) */
    function sameLineage(a, b) { return a.rpk.sig === b.rpk.sig && a.rpk.dh === b.rpk.dh; }

    /* 참가 전 탐색: hello_req → hello(서명·지문) → 400ms 이중 응답 감지 (§2.6·§3.3) */
    function probeHello(T, code, inv, total) {
        return new Promise(function (res) {
            var best = null, conflict = false, badFp = false, fin = false, timers = [];
            function end(v) { if (fin) return; fin = true; timers.forEach(clearTimeout); res(v); }
            var q = Promise.resolve();
            T.onH(function (env) {
                if (fin || !env || env.e !== 'hello' || typeof env.j !== 'string' || env.j.length > MAXJ) return;
                q = q.then(async function () {
                    if (fin) return;
                    var h = jparse(env.j, null), v = await verifyHello(code, h, env, inv);
                    if (!v.ok) { if (v.badFp) badFp = true; return; }
                    if (!best) {
                        best = { h: h, env: env, F: v.F };
                        timers.push(setTimeout(function () { end(conflict ? { conflict: true } : best); }, TM.conflictWin));
                    } else if (h.hk.sig !== best.h.hk.sig) {
                        if (sameLineage(h, best.h) && chainLen(h) !== chainLen(best.h)) { if (chainLen(h) > chainLen(best.h)) best = { h: h, env: env, F: v.F }; }
                        else conflict = true;
                    }
                }).catch(function () {});
            });
            var n = rid(6);
            function ask() { if (!fin) T.send('g', { v: 2, e: 'hello_req', n: n }); }
            ask();
            (total > 4000 ? TM.joinRetry : [1500]).forEach(function (ms) { timers.push(setTimeout(ask, ms)); });
            timers.push(setTimeout(function () { end(best ? best : { none: true, badFp: badFp }); }, total));
        });
    }

    /* ================================================================
       LpRooms.create — 방장
       ================================================================ */
    async function importTestKeys(k) {
        var sp = await SUB.importKey('jwk', k.sig, EC_S, false, ['sign']);
        var dp = await SUB.importKey('jwk', k.dh, EC_D, false, ['deriveBits', 'deriveKey']);
        var spub = await SUB.importKey('jwk', { kty: 'EC', crv: 'P-256', x: k.sig.x, y: k.sig.y }, EC_S, true, ['verify']);
        var dpub = await SUB.importKey('jwk', { kty: 'EC', crv: 'P-256', x: k.dh.x, y: k.dh.y }, EC_D, true, []);
        return { sig: { priv: sp, pub: b64u(await rawPub(spub)) }, dh: { priv: dp, pub: b64u(await rawPub(dpub)) } };
    }
    function collides(T, code, rpk) {
        return new Promise(function (res) {
            var hit = false, q = Promise.resolve();
            T.onH(function (env) {
                if (!env || env.e !== 'hello' || typeof env.j !== 'string') return;
                q = q.then(async function () { var h = jparse(env.j, null); if (h && h.rpk && h.rpk.sig !== rpk.sig) { var v = await verifyHello(code, h, env, null); if (v.ok) hit = true; } }).catch(function () {});
            });
            T.send('g', { v: 2, e: 'hello_req', n: rid(6) });
            setTimeout(function () { q.then(function () { res(hit); }); }, TM.collideWin);
        });
    }
    function pin4() { var u = rand(4); return String(((u[0] << 8 | u[1]) * 65536 + (u[2] << 8 | u[3])) % 10000).padStart(4, '0'); }

    async function create(o) {
        o = o || {};
        await ready();
        var dev = await loadDevice();
        var gid = String(o.gameId || '');
        if (!regOk(gid)) throw err('bad_game');
        if (inAppEscaping()) throw err('inapp');
        if (_current && !_current._left) _current.leave();
        var keys, rpk, F, code, P = null, tries = 0;
        var tq = (_cfg.testKeys && isLocalDev()) ? _cfg.testKeys : null;
        for (;;) {
            keys = (tq && tq.length) ? await importTestKeys(tq.shift()) : await genPair(false);
            rpk = { sig: keys.sig.pub, dh: keys.dh.pub }; F = await roomF(rpk); code = codeOfF(F);
            if (!hasLetter(code)) continue;
            P = await openTopic(PFX + code);
            if (!(await P.ready)) { P.close(); throw err('network'); }
            if (!(await collides(P, code, rpk))) break;
            dbg('code collision → new keys', code);
            P.close(); P = null;
            if (++tries >= 5) throw err('collision');
        }
        var hl = await acquireLock('lpr-host-' + code, false);
        var sl = await acquireLock('lpr-seat-' + code, false);
        var room = new Room(code, dev);
        room.isHost = true; room.gameId = gid; room.sealed = o.sealed !== false;
        room._rpk = rpk; room._hostPk = rpk.sig; room._hostDh = rpk.dh; room.fp = fpOfF(F); room.seal = sealOfF(F);
        room.ep = now();
        room._hostRel = hl.release; room._seatRel = sl.release;
        var pinReq = !!(o.pinReq || o.pin);
        var H = room._H = newH({ sk: keys.sig.priv, dk: keys.dh.priv, tok: rid(16), pinReq: pinReq, pin: pinReq ? (/^\d{4}$/.test(String(o.pin || '')) ? String(o.pin) : pin4()) : null, max: o.max });
        H.mkRaw = { 1: rand(32) }; room._mk[1] = await aesKey(H.mkRaw[1]); room._kv = 1;
        room.pin = H.pin || undefined;
        var prof = profile.get();
        var sp = seatsFor(gid);
        room._S = {
            v: 2, seq: 0, phase: 'lobby', gameId: gid, opts: clone(o.opts) || {}, startAt: null,
            roster: [{ p: dev.pid, n: prof.nick || 'Host', av: prof.av, r: 'host', seat: sp ? 0 : null, pick: {}, rd: true, c: 'on', j: now(), au: null, k: { sig: dev.sig.pub, dh: dev.dh.pub } }],
            succ: [], succz: null, succe: room.ep, lock: false, appr: !!o.appr, pinReq: pinReq, turn: null, fair: null, log: [], game: null, mem: {}
        };
        if (_adapter && _adapter.gameId === gid && typeof _adapter.initGame === 'function') { try { room._S.game = _adapter.initGame(room._S); } catch (e) { dbg('initGame', e); } }
        room._state = 'member';
        room._attach(await openTopic(PFX + code));
        P.close();
        room._recalcSucc(); await room._succP;
        try { await idbPut('room:' + code, { sig: keys.sig, dh: keys.dh, rpk: rpk, t: now() }); } catch (_) {}
        hl.lost = null; sl.lost = function () { room._detach(); };
        room._hostLoops();
        room._syncMe();   /* 방장 me.role/seat = 명단 값('host', 좌석) — 예전엔 첫 roster 방송 전까지 'player' 로 남았다 */
        room._lastRoster = clone(room._S.roster);
        room.setState(null);
        room._save();
        _current = room;
        addRecent(code, gid, prof.nick);
        wireLifecycle();
        GLOBAL.emit('room', room);
        dbg('created', code, gid);
        return room;
    }

    /* ================================================================
       LpRooms.join — 멤버
       ================================================================ */
    async function join(o) {
        o = o || {};
        var code = normCode(o.code);
        if (!code || /^\d{6}$/.test(code)) throw err('not_found');
        if (lsGet('lpr_ban_' + code)) throw err('banned');
        if (inAppEscaping()) throw err('inapp');
        await ready();
        var dev = await loadDevice();
        if (_current && _current.code === code && !_current._left && _current._state === 'member') return _current;
        if (_current && !_current._left) _current.leave();
        var inv = o.inv || invFromSession(code);
        var st = function (s, extra) { var v = { st: s, code: code }; if (extra) for (var k in extra) v[k] = extra[k]; try { o.onStatus && o.onStatus(v); } catch (_) {} GLOBAL.emit('status', v); };
        var seat = await acquireLock('lpr-seat-' + code, !!o.steal);
        if (!seat.ok) throw err('other_tab');
        var room = new Room(code, dev);
        room._inv = inv; room._want = o.want === 'watch' ? 'watch' : 'play'; room._seatRel = seat.release;
        seat.lost = function () { room._detach(); };
        try {
            st('probing');
            var T = await openTopic(PFX + code);
            room._attach(T); room._state = 'joining';
            if (!(await T.ready)) throw err('network');
            var pr = await probeHello(T, code, inv, TM.joinTimeout);
            if (pr.conflict) throw err('host_conflict');
            if (pr.none) throw err(pr.badFp ? 'bad_fp' : 'not_found');
            var h = pr.h;
            room._rpk = h.rpk; room._hostPk = h.hk.sig; room._hostDh = h.hk.dh; room._chain = h.chain || null;
            room.fp = fpOfF(pr.F); room.seal = sealOfF(pr.F); room.gameId = h.gameId; room.ep = h.ep;
            if (_adapter && _adapter.gameId && h.gameId !== _adapter.gameId && h.gameId !== 'lobby' && !o.anyGame) throw err('wrong_game', { gameId: h.gameId, url: urlFor(h.gameId, code) });
            /* PIN 켠 방이라도 일단 시도 — 알려진 pid(재접속)는 PIN 없이 통과, 아니면 방장이 pin_required 로 답한다 */
            st('joining', { hello: h });
            room._jbuf = [];
            var res = await room._handshake(inv, o, st);
            await room._onWelcome(res.env, res.inner);
            room._state = 'member';
            var buf = room._jbuf || []; room._jbuf = null;
            buf.forEach(function (e) { room._rxH(e); });
            room._guestLoops();
            st('member');
        } catch (e) {
            room._teardown('join_failed', false);
            throw e.reason ? e : err('error', { cause: e });
        }
        _current = room;
        setActive({ code: code, role: 'guest', gameId: room.gameId, want: room._want, inv: inv });
        var hm = room._hostMember(); addRecent(code, room.gameId, hm ? hm.n : '');
        wireLifecycle();
        GLOBAL.emit('room', room);
        dbg('joined', code, room.me);
        return room;
    }
    Room.prototype._handshake = function (inv, o, st) {
        var self = this;
        return new Promise(async function (res, rej) {
            var fin = false, pending = false, timers = [];
            function end(fn, v) { if (fin) return; fin = true; timers.forEach(clearTimeout); self._joinW = null; fn(v); }
            var env;
            try { env = await self._genv('join', await self._joinPayload({ tok: inv && inv.tok, pin: o.pin, want: o.want, g: _adapter && _adapter.gameId }), { plain: true }); }
            catch (e) { return end(rej, err('error')); }
            self._joinW = function (e) {
                if (fin) return;
                if (e.e === 'hello') return;
                if ((e.e !== 'welcome' && e.e !== 'deny') || !self._forMe(e)) { if (self._jbuf && self._jbuf.length < 64) self._jbuf.push(e); return; }
                verifyStr(self._hostPk, hSigStr(self.code, e), e.z).then(async function (ok) {
                    if (!ok || fin) return;
                    var d = jparse(e.j, null); if (!d) return;
                    if (e.e === 'deny') {
                        if (d.r === 'pending') {
                            if (!pending) { pending = true; timers.forEach(clearTimeout); st('pending'); timers.push(setTimeout(function () { end(rej, err('denied')); }, TM.pendingMax)); }
                            return;
                        }
                        return end(rej, err(String(d.r || 'denied'), d.gameId ? { gameId: d.gameId, url: urlFor(d.gameId, self.code) } : null));
                    }
                    try { var inner = await eciesDec(self._dev.dh.priv, self.code, 'welcome', d.x); end(res, { env: e, inner: inner }); }
                    catch (_) { STATS.bad++; }
                });
            };
            self._rawSend('g', env);
            TM.joinRetry.forEach(function (ms) { timers.push(setTimeout(function () { if (!fin && !pending) { st('retry'); self._rawSend('g', env); } }, ms)); });
            timers.push(setTimeout(function () { if (!pending) end(rej, err('not_found')); }, TM.joinTimeout + 1000));
        });
    };

    /* ================================================================
       resume — 새로고침·게임 전환 후 이 탭의 방 복구 (§6.0.6)
       ================================================================ */
    function urlRoomCode() { try { var q = new URLSearchParams(G.location.search); return normCode(q.get('r') || q.get('room') || ''); } catch (_) { return null; } }
    async function resume() {
        var a = getActive();
        if (!a || !a.code || inAppEscaping()) return null;
        if (now() - (a.t || 0) > 24 * 3600e3) { setActive(null); return null; }
        var q = urlRoomCode(); if (q && q !== a.code) return null;
        if (_current && _current.code === a.code && !_current._left) return _current;
        if (a.role === 'host') { try { var r = await resumeHost(a); if (r) return r; } catch (e) { dbg('resumeHost', e); } }
        try { return await join({ code: a.code, inv: a.inv, want: a.want, anyGame: true }); }
        catch (e) { if (e && /^(closed|banned|not_found|denied|bad_fp|host_conflict)$/.test(e.reason)) setActive(null); dbg('resume join failed', e && e.reason); return null; }
    }
    async function resumeHost(a) {
        var code = a.code, blob = jparse(ssGet('lpr_host_' + code), null);
        if (!blob || blob.v !== 2 || !blob.S) return null;
        await ready();
        var dev = await loadDevice(), keys = null;
        if (blob.devHost) keys = { sig: dev.sig, dh: dev.dh };
        else { var rec = null; try { rec = await idbGet('room:' + code); } catch (_) {} if (!rec || !rec.sig || !rec.sig.priv) return null; keys = rec; }
        var hl = await acquireLock('lpr-host-' + code, false);
        if (!hl.ok) return null;
        var rpk = blob.rpk, F = await roomF(rpk);
        var P = await openTopic(PFX + code);
        if (!(await P.ready)) { P.close(); hl.release(); return null; }
        /* 누가 이미 방장인가? (승계됐거나 다른 탭) */
        var pr = await probeHello(P, code, null, 1200);
        if (pr && pr.h && pr.h.hk && pr.h.hk.sig !== keys.sig.pub) { P.close(); hl.release(); dbg('resume: another host is live'); return null; }
        var sl = await acquireLock('lpr-seat-' + code, true);
        var room = new Room(code, dev);
        room.isHost = true; room.sealed = blob.sealed !== false;
        room._rpk = rpk; room._chain = blob.chain || null; room._hostPk = keys.sig.pub; room._hostDh = keys.dh.pub;
        room.fp = fpOfF(F); room.seal = sealOfF(F); room.ep = Math.max(now(), (blob.ep || 0) + 1);
        room._prevHostPk = blob.prevPk || null;
        room._hostRel = hl.release; room._seatRel = sl.release; sl.lost = function () { room._detach(); };
        var H = room._H = newH({ sk: keys.sig.priv, dk: keys.dh.priv, s: blob.s, t: blob.t, tok: blob.tok, pin: blob.pin, pinReq: blob.pinReq, max: blob.max,
            known: blob.known, bans: blob.bans, banNicks: blob.banNicks, apprAuto: blob.apprAuto, fs: blob.fs });
        H.devHost = !!blob.devHost; H.mkRaw = {};
        var ks = Object.keys(blob.mk || {});
        for (var i = 0; i < ks.length; i++) { H.mkRaw[ks[i]] = ub64u(blob.mk[ks[i]]); room._mk[ks[i]] = await aesKey(H.mkRaw[ks[i]]); }
        room._kv = blob.kv | 0;
        Object.keys(blob.members || {}).forEach(function (p) { H.members[p] = memRec(blob.members[p].k, blob.members[p].lastC); });
        room._S = blob.S; room.gameId = blob.S.gameId; room.pin = H.pin || undefined;
        room._S.roster.forEach(function (m) { if (m.p === dev.pid) { m.c = 'on'; } });
        room._state = 'member';
        room._attach(await openTopic(PFX + code));
        P.close();
        room._syncMe();
        room._hostLoops();
        room._lastRoster = clone(room._S.roster);
        room._recalcSucc(); await room._succP;
        room.setState(null, { full: true });   /* 새 epoch 첫 방송 = 전체 state */
        room._sendHello();
        room._save();
        _current = room;
        wireLifecycle();
        GLOBAL.emit('room', room);
        dbg('resumed host', code, room.ep);
        return room;
    }

    /* 페이지 수명: 숨김·이탈 (§6.0.3) */
    var _wired = false;
    function wireLifecycle() {
        if (_wired || !G.document) return; _wired = true;
        var hidAt = 0;
        G.document.addEventListener('visibilitychange', function () {
            var vis = G.document.visibilityState !== 'hidden';
            if (!vis) hidAt = now();
            var r = _current; if (!r || r._left || r._state !== 'member') return;
            if (r.isHost) { r._sendHostHb(); r._save(); }
            else if (vis) r._resync(hidAt ? now() - hidAt : 0);   /* 복귀 = 시계 다시 맞추기(§6.0.3) */
            else r._sendGHb();
        });
        G.addEventListener('pagehide', function () {
            var r = _current; if (!r || r._left) return;
            if (r.isHost) { r._save(); r._sendHostHb(); }
            else if (r._state === 'member') r._gsend('bye', {});
        });
    }

    /* ================================================================
       parseInvite · resolve (§2.2)
       ================================================================ */
    function parseInvite(text) {
        var s = String(text == null ? '' : text).trim();
        if (!s) return null;
        var u = null;
        if (/^(https?:)?\/\//i.test(s) || /^[\/?#]/.test(s) || /^[\w.-]+\.[a-z]{2,}(:\d+)?\//i.test(s)) {
            try { u = new URL(/^[\w.-]+\.[a-z]{2,}(:\d+)?\//i.test(s) ? 'https://' + s : s, 'https://luckyplz.com/'); } catch (_) { u = null; }
        }
        if (u) {
            var inv = null, m = /(?:^#|[#&])k=([A-Za-z0-9_-]{22})(?:\.([A-Za-z0-9_-]{16,43}))?/.exec(u.hash);
            if (m) inv = m[2] ? { fp: m[1], tok: m[2] } : { fp: m[1] };
            var pm = /\/r\/([^\/?#]+)/.exec(u.pathname), q = u.searchParams, c;
            if (pm && (c = normCode(decodeURIComponent(pm[1]))) && !/^\d{6}$/.test(c)) return inv ? { code: c, inv: inv, hint: 'v2' } : { code: c, hint: 'v2' };
            if (q.get('r') && (c = normCode(q.get('r'))) && !/^\d{6}$/.test(c)) return inv ? { code: c, inv: inv, hint: 'v2' } : { code: c, hint: 'v2' };
            if (/^\d{6}$/.test(q.get('c') || '')) return { code: q.get('c'), hint: 'qlive' };
            var sz = q.get('race') || q.get('coop');
            if (/^\d{6}$/.test(sz || '')) return { code: sz, hint: 'szx' };
            var rm = String(q.get('room') || '').toUpperCase().replace(/[^0-9A-Z]/g, '');
            if (/^[0-9A-Z]{4,8}$/.test(rm)) return { code: rm, hint: 'v1' };
            return null;
        }
        var nc = normCode(s);
        if (nc) return { code: nc };
        var raw = s.toUpperCase().replace(/[\s\-_.]/g, '');
        if (/^[0-9A-Z]{4,8}$/.test(raw)) return { code: raw, hint: 'v1' };
        return null;
    }
    function withTimeout(p, ms, v) { return Promise.race([p, sleep(ms).then(function () { return v; })]); }
    async function probeV2(code, inv) {
        var T = await openTopic(PFX + code);
        try {
            if (!(await withTimeout(T.ready, 3000, false))) return null;
            var r = await probeHello(T, code, inv, 3500);
            if (r.conflict) return { conflict: true };
            return r.h ? r : null;
        } finally { T.close(); }
    }
    function probeV1(code) {
        var sb = sbClient(); if (!sb) return Promise.resolve(null);
        return new Promise(function (res) {
            var ch = sb.channel('lp-room-' + code, { config: { broadcast: { self: false, ack: false } } }), pid = rid(8), fin = false;
            function end(v) { if (fin) return; fin = true; try { sb.removeChannel(ch); } catch (_) {} res(v); }
            ch.on('broadcast', { event: 'host:probe_ack' }, function (m) { var p = (m && m.payload) || {}; if (p.pid === pid) end({ gameId: String(p.gameId || ''), locked: !!p.locked }); });
            ch.subscribe(function (s) { if (s === 'SUBSCRIBED') ch.send({ type: 'broadcast', event: 'guest:probe', payload: { pid: pid } }); });
            setTimeout(function () { end(null); }, 4000);
        });
    }
    function probeQlive(code) {
        var sb = sbClient(); if (!sb || typeof sb.rpc !== 'function') return Promise.resolve(false);
        return withTimeout(Promise.resolve(sb.rpc('qlive_state', { p_code: code, p_pid: null, p_host_key: null })).then(function (r) { return !!(r && r.data && r.data.ok); }).catch(function () { return false; }), 4000, false);
    }
    function probeSzx(code, ms) {
        var sb = sbClient(); if (!sb) return Promise.resolve(false);
        return new Promise(function (res) {
            var ch = sb.channel('szx-race-' + code, { config: { broadcast: { self: false, ack: false } } }), fin = false;
            function end(v) { if (fin) return; fin = true; try { sb.removeChannel(ch); } catch (_) {} res(v); }
            ch.on('broadcast', { event: 'st' }, function () { end(true); });
            ch.subscribe(function () {});
            setTimeout(function () { end(false); }, ms);
        });
    }
    var V1_GAMES = ['roulette', 'ladder', 'team', 'lotto', 'bingo', 'car-racing', 'quiz', 'ludo', 'yut', 'reversi', 'gummy', 'prism-hex', 'mahjong-tw'];
    async function resolve(input) {
        var p = parseInvite(input);
        if (!p) return { kind: 'none', code: '' };
        var code = p.code;
        if (p.hint === 'qlive') return { kind: 'qlive', code: code, gameId: 'quiz', url: '/games/quiz/?c=' + code };
        if (p.hint === 'szx') return { kind: 'szx', code: code, gameId: 'dodge', url: '/games/dodge/?race=' + code };
        await ready();
        if (/^\d{6}$/.test(code)) {
            var szP = probeSzx(code, 3000), qOk = await probeQlive(code);
            if (qOk) {
                var sz0 = await withTimeout(szP, 50, false);
                if (sz0) return { kind: 'choice', code: code, options: [{ kind: 'qlive', url: '/games/quiz/?c=' + code }, { kind: 'szx', url: '/games/dodge/?race=' + code }] };
                return { kind: 'qlive', code: code, gameId: 'quiz', url: '/games/quiz/?c=' + code };
            }
            if (await szP) return { kind: 'szx', code: code, gameId: 'dodge', url: '/games/dodge/?race=' + code };
            return { kind: 'none', code: code };
        }
        var v2ok = CODE_RE.test(code) && hasLetter(code);
        return new Promise(function (res) {
            var left = 0, fin = false;
            function end(v) { if (!fin) { fin = true; res(v); } }
            function miss() { if (--left <= 0) end({ kind: 'none', code: code }); }
            if (v2ok) {
                left++;
                probeV2(code, p.inv).then(function (r) {
                    if (r && r.conflict) return end({ kind: 'none', code: code, reason: 'host_conflict' });
                    if (!r) return miss();
                    var h = r.h, url = urlFor(h.gameId, code);
                    if (!url) return miss();
                    if (p.inv) url += '#k=' + p.inv.fp + (p.inv.tok ? '.' + p.inv.tok : '');
                    end({ kind: 'rooms', code: code, gameId: h.gameId, url: url, hello: { gameId: h.gameId, kind: h.kind, phase: h.phase, count: h.count, max: h.max, lock: h.lock, pinReq: h.pinReq, appr: h.appr } });
                }).catch(miss);
            }
            left++;
            probeV1(code).then(function (r) {
                if (!r) return miss();
                if (r.gameId === 'lobby') return end({ kind: 'rooms-v1', code: code, gameId: 'lobby', url: '/lobby/?room=' + code });
                var gid = V1_GAMES.indexOf(r.gameId) >= 0 ? r.gameId : null;
                if (!gid) return miss();
                end({ kind: 'rooms-v1', code: code, gameId: gid, url: '/games/' + gid + '/?room=' + code });
            }).catch(miss);
        });
    }

    /* ================================================================
       LpRooms 공개 객체
       ================================================================ */
    var _readyP = null;
    function ready() {
        if (_readyP) return _readyP;
        _readyP = (async function () {
            for (var i = 0; i < 150 && !sbClient(); i++) await sleep(100);
            if (!sbClient()) { _readyP = null; throw err('unsupported'); }
            await loadDevice();
        })();
        return _readyP;
    }
    G.LpRooms = {
        version: VER,
        ready: ready,
        identity: function () { return loadDevice().then(function (d) { return { pid: d.pid, tid: d.tid }; }); },
        profile: profile,
        create: create,
        join: join,
        resolve: resolve,
        parseInvite: parseInvite,
        resume: resume,
        current: function () { return _current && !_current._left ? _current : null; },
        adapter: function (spec) { if (spec && typeof spec.gameId === 'string') _adapter = spec; },
        getAdapter: function () { return _adapter; },
        on: function (ev, cb) { return GLOBAL.on(ev, cb); },
        config: function (o) {
            o = o || {};
            ['client', 'navigate', 'autoNav', 'origin', 'debug'].forEach(function (k) { if (o[k] !== undefined) _cfg[k] = o[k]; });
            if (o.testKeys && isLocalDev()) _cfg.testKeys = o.testKeys.slice();
        },
        util: {
            b64u: b64u, ub64u: ub64u, hex: hex, sha256: sha256, canon: canon, fmtCode: fmtCode, normCode: normCode,
            cleanNick: cleanNick, seal: sealOfF, verify: verifyStr, pidOf: pidOf, codeOfF: codeOfF, fpOfF: fpOfF, roomF: roomF
        },
        stats: function () { return { sent: STATS.sent, recv: STATS.recv, bad: STATS.bad, estPerSec: STATS.win.length / 60 }; },
        _t: { TM: TM, Room: Room, diffOps: diffOps, applyOps: applyOps, chainKey: chainKey }
    };
})(typeof window !== 'undefined' ? window : globalThis);
/* CHANGE LOG
   2026-09-30  API freeze (stub).
   2026-09-30  구현 1차 — 신원(IDB 비추출 키·pid·tid·Web Lock 좌석), 코드 파생·충돌 검사, 서명 봉투·봉인·ECIES,
               핸드셰이크·레이트리밋·승인·PIN, 명단·연결 판정, hb 1종·시계·편승, gap/snap 뭉침, setState/delta/priv,
               의도 멱등, 방장 저장/재개, 감시·승계(서명 체인)·양도, 게임 전환, resolve(v2·v1·퀴즈·SZX).
               API 추가: Room.hb/canStart/pending/fp/seal/sealed/pin, LpRooms.config/util/stats/getAdapter,
               이벤트 hb/tick/switch/pending/net/join(방장), join 옵션 steal/onStatus.
   2026-09-30  하네스 검증 중 수정 — (1) 전체 state 로 건너뛴 구간에 늦게 온 재전송 사건(switch·kicked·fair·x…)은
               id 로 한 번만 살림(재정렬 시 switch 유실 버그). (2) 원방장 복귀 = 게스트 합류(되찾기 없음).
               (3) 의도 수락 응답을 state/roster 방송에 싣기(별도 ack 제거). (4) hello·deny 증폭 제한,
               같은 join 재전송엔 캐시된 거절(PIN 오답 재계수 없음). (5) 합류 직후 15초 시계 에코 가속.
               (6) 인앱 탈출 예정이면 create/join/resume 보류(reason 'inapp'). (7) 추첨 시청 중 리액션 허용.
   2026-09-30  통합 수정(P3a 보고 반영, 전부 하위 호환 추가):
               [+] Room.setPin(on, pin?) → 현재 PIN|null · Room.setApproval(on) — 방장 도구 공개 API(UI 가 _H 를 만지지 않게).
               시계 정밀화 — 표본 창 24개·10분, RTT 하위 min(5,⌈n/2⌉)개 오프셋 중앙값(이전: 7개 중 3개),
               t1·t3 = 수신 콜백 진입 시각(검증·복호 큐 대기 제외), 화면 복귀 시 빠른 에코 hb 3개(fs:1, 30초에 1번,
               방장은 게스트당 10초 4번까지 응답), 추첨 lock/reveal 에코 표본(lpFair, 추가 메시지 0).
               fair 리스너 3번째 인자 rx(도착 시각), room._io.clockSample [+].
               게스트 봉투 재생 방지 = 최근 64개 창(순서 바뀐 늦은 도착 수용, 중복·창 밖은 거절) — 예전 엄격 단조(c>lastC)는
               지터 30~150ms 에서 hb 편승 w·fair c/r 을 버려 추첨 재시도·목격 누락을 냈다.
   2026-09-30  통합 2차(턴제↔공통 UI): 방장 room.me 동기화 — create 직후와 방장 state 방송마다 _syncMe().
               예전엔 방장 me.role 이 첫 roster 방송(명단 변화) 전까지 'player', me.seat 는 시작 때 재배치돼도 옛 값이었다.
               영향: UI '내 차례' 알림(me.seat) · 게스트 hb 주기(_hbInterval 은 게스트 전용이라 무관).
   결정: supabase realtime {worker:true} 는 채택 보류 — 방 페이지는 getSupabase() 공용 클라이언트(소켓 1개)를
         재사용하고, 워커 옵션은 클라이언트 생성 시점에만 줄 수 있어 공용 클라이언트와 충돌한다. 헤드리스 하네스로는
         백그라운드 스로틀을 재현할 수 없어 실기기 확인 항목으로 넘긴다(§6.0.3 소켓 항목).
*/
