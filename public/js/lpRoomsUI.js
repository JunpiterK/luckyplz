/* =====================================================================
   lpRoomsUI.js — LuckyPlz Rooms v2 공통 로비 UI (P2)
   설계: docs/multiplayer/DESIGN.md §4 (+ §2.3 링크·QR·인앱, §2.4 닉·아바타, §6.1.5 배지)
   의존: lpGames.js · lpRoomsCore.js (· lpFair.js 있으면 배지) — siteFooter.js 의 v2 로더가 순서대로 싣는다.

   ── API (2026-09-30, "rooms-v2 UI API") ────────────────────────────
   이 블록은 게임 어댑터(P3·P4·P5)가 보고 짜는 계약이다. 이후에는 하위 호환 추가만 한다.

   declare global { interface Window { LpRoomsUI: LpRoomsUI } }    // + 별칭 LpRooms.UI (코어가 먼저 있으면)

   interface UIConfig {                       // 게임이 LpRooms.adapter(...) 직후 1회. 전부 선택
     gameId?: string;                         // 기본 = 경로 /games/<id>/ · /lobby/ = 'lobby'
     lobby?: 'full' | 'strip' | 'none';       // 기본: 레지스트리 kind 가 draw → 'strip', 그 외 → 'full'
     stripEl?: HTMLElement | (() => HTMLElement | null);   // 띠를 넣을 곳(게임 설정 화면 맨 위). 없으면 화면 위 고정 띠
     choices?: { picks?: {key, options?, unique?, botYield?}[], options?: {key, values, def}[] };
                                              // 대기실 선택 칸. 기본 = LpRooms.getAdapter() → 레지스트리 mp.choices
     labels?: { [k: string]: string | {[lang: string]: string} };
                                              // 선택 칸 이름·값 표시: {'char':{ko:'캐릭터'}, 'char.a':'🐯', 'turnSec.30':'30s'}
                                              // 값 표시가 없으면 값 자체(이모지·숫자면 그대로 보기 좋다)
     minPlayers?: number;                     // 시작 게이트 안내용(기본 = 좌석 [min,max] 의 min, 없으면 1)
     onStart?(room): void | false;            // 방장 [시작 ▶] 직전. false 면 room.start() 를 부르지 않는다(게임이 직접 시작)
     bots?: { add(room): void; remove(room, pid: string): void };   // 있으면 [+ 봇]·봇 [✕] 표시(방장)
     addMe?: (room) => void;                  // 띠형: [✋ 내 이름 넣기] (게스트) — 게임이 이름 목록 반영
     hud?: boolean;                           // 기본 true — 플레이 중 알약 1개
     auto?: boolean;                          // 기본 true — ?r= 링크·새로고침 복귀 자동 참가
   }
   interface Handle { el: HTMLElement; refresh(): void; remove(): void; }
   interface LpRoomsUI {
     version: string;
     config(o: UIConfig): void;
     ready(): Promise<Room | null>;           // 부팅(링크 처리·resume·자동 참가) 끝 — 방이 있으면 그 방
     room(): Room | null;
     on(ev: 'room' | 'left' | 'lobby' | 'play', cb: (x?: any) => void): () => void;
          // room(Room) 방이 붙음 · left({reason}) 방을 떠남 · lobby() 대기실 표시 · play(phase) 대기실이 닫히고 게임 화면으로
     openCreate(o?: { gameId?: string, pick?: boolean }): Promise<Room | null>;
          // 닉·아바타 확인 후 방 생성. pick=true → 게임 그리드부터(허브). 이미 방이면 그 방
     openJoin(o?: { code?: string }): Promise<void>;
          // 코드/링크 입력 → LpRooms.resolve → 같은 게임이면 여기서 참가, 아니면 그 게임 페이지로 이동
     openInvite(room?): void;                 // 초대 시트: 💬 메신저로 초대(1순위) · 링크+복사 · QR · 코드 · 🔄 링크 새로(방장)
     openRoom(room?): void;                   // 방 시트(= HUD 탭): 명단 · 초대 · 방장 도구 · 나가기
     openSwitch(room?): void;                 // 방장: 게임 바꾸기 그리드 → room.switchGame(id)
     mountLobby(room, o?: { into?: HTMLElement }): Handle;   // 풀 대기실(기본 화면 전체). 보통 자동 — 수동은 lobby:'none' 일 때
     mountHud(room): Handle;                  // HUD 알약 `K7M-2QX · 👥5 · ●` — 보통 자동
     strip(room, el?: HTMLElement): Handle;   // 띠형 대기실: 명단 1줄 + [초대] (+ 준비/시작은 게임 버튼이 맡는다)
     badge(el: HTMLElement, info: {kind:'verified'|'seed'|'solo'|'mismatch', n?, round?, cert?}): void;
          // LpFair.badge + 스타일 + 현지화("✓ 공정 · 5명 확인") + 탭 → 검증 시트. LpFair.badge 를 직접 불러도 같은 모양(후크)
     confirm(msg: string, o?: { ok?: string, cancel?: string, danger?: boolean }): Promise<boolean>;   // window.confirm 대체(인앱 안전)
     sheet(o: { title?: string, body: HTMLElement | string, onClose?(): void }): { el: HTMLElement, close(): void };   // 공용 바텀시트
     toast(msg: string, ms?: number): void;
     say(msg: string): void;                  // aria-live=polite 알림
     t(key: string, vars?: object): string;   // 문구 표(16개 언어, 빠진 언어 → en)
     lang(): string;                          // luckyplz_lang (gb → en)
     avatars: string[];                       // 16종 — LpRooms.profile.av 인덱스
   }

   자동 동작(v2 로더가 이 파일을 실으면): URL(?r= · /r/CODE · #k=) → sessionStorage lpr_inv 로 옮기고 주소창에서 지움 →
   LpRooms.resume() → (없으면) ?r= 코드로 참가(저장된 닉 있으면 묻지 않음) → 방이 붙으면 HUD 1개 +
   phase='lobby' 동안 풀 대기실 또는 띠. phase≠'lobby' 면 대기실이 닫히고 'play'. 게임 도크(LpChrome)에 👥 버튼.
   ===================================================================== */
(function (G) {
    'use strict';
    if (G.LpRoomsUI && G.LpRoomsUI.version && G.LpRoomsUI.version.indexOf('stub') < 0) return;
    function noop() {}
    function h() { return { el: null, refresh: noop, remove: noop }; }
    G.LpRoomsUI = {
        version: '2.0.0-stub',
        config: noop, ready: function () { return Promise.resolve(null); }, room: function () { return null; },
        on: function () { return noop; },
        openCreate: function () { return Promise.resolve(null); }, openJoin: function () { return Promise.resolve(); },
        openInvite: noop, openRoom: noop, openSwitch: noop,
        mountLobby: h, mountHud: h, strip: h, badge: noop,
        confirm: function () { return Promise.resolve(false); }, sheet: function () { return { el: null, close: noop }; },
        toast: noop, say: noop, t: function (k) { return k; }, lang: function () { return 'en'; }, avatars: []
    };
})(typeof window !== 'undefined' ? window : globalThis);
