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
    if (G.LpRooms && G.LpRooms.version) return;
    var NI = function () { return Promise.reject(new Error('LpRooms: not implemented yet (API freeze stub)')); };
    G.LpRooms = { version: '2.0.0-stub', ready: NI, identity: NI, create: NI, join: NI, resolve: NI, resume: NI,
        parseInvite: function () { return null; }, current: function () { return null; }, adapter: function () {},
        getAdapter: function () { return null; }, on: function () { return function () {}; }, config: function () {},
        profile: { get: function () { return { nick: '', av: 0 }; }, set: function (p) { return p; } }, util: {},
        stats: function () { return { sent: 0, recv: 0, estPerSec: 0, bad: 0 }; } };
})(typeof window !== 'undefined' ? window : globalThis);
/* CHANGE LOG
   2026-09-30  API freeze (stub).
*/
