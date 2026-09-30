# LuckyPlz Rooms — 공통 방 플랫폼 설계서 (v2)

작성 2026-09-30 · 입력: `audit_infra.md` · `audit_draws.md` · `audit_games.md` + 코드 재확인(아래 §0.3) · 대상 저장소 `C:\code\python\luckyplz`
독자: 구현 에이전트(패키지 P0~P7). 이 문서만 보고 파일·API·메시지·타이밍을 그대로 만들 수 있어야 한다.

---

## 0. 한 장 요약

**문제.** 방 시스템이 4개(lpRoom · Space-Z SZX · Space-Z 로그인 PvP · 라이브 퀴즈 DB)이고 코드 형식·PIN·진실원천·신원이 전부 다르다. 공통 로비가 없고(`/lobby/` 는 스피너), 떠 있는 방 UI가 4겹이며, 방송 채널이 공개라 **코드만 알면 호스트 사칭(강퇴·이동·종료)·게스트 사칭·PIN 도청/무차별 대입**이 된다. 추첨 결과는 "방장 기기 `Math.random()` 을 믿어라"라 *목격*은 되지만 *인증*은 안 된다.

**해법 = LuckyPlz Rooms v2** (한 계약 + 한 UI + 게임 유형별 엔진 어댑터).

| 층 | 결정 |
|---|---|
| 방 신원 | **6자 코드 1종**(`23456789ABCDEFGHJKMNPQRSTVWXYZ`, 글자 1개 이상 포함) = **방장 방 공개키 해시에서 파생**(자기 인증 코드). 초대 링크 `https://luckyplz.com/r/K7M2QX#k=<지문>.<토큰>` · QR · 코드 입력 모두 같은 코드. 숫자 6자리는 레거시(퀴즈·SZX)로 라우팅 |
| 신원 | 기기 키(ECDSA+ECDH P-256, **비추출 CryptoKey, IndexedDB**) → `pid = 해시(공개키)` = 위조 불가 기기 신원. 탭은 `tid` + Web Lock 으로 "다른 탭에서 열림 → 여기서 계속" |
| 신뢰 Phase A (지금, 서버 변경 0) | **방장 방송 전부 서명**, 게스트 의도 전부 서명, 재생 방지(ep·seq), 링크에 방장 키 지문 고정, 코드 입력은 TOFU + 이중 응답 감지 + 봉인 이모지 3개 비교. PIN/토큰은 방장 공개키로 암호화(ECIES)해 도청 불가, 실패 10회/분 → 60초 쿨다운 |
| 신뢰 Phase B (나중, 운영자 SQL) | Supabase 익명 로그인 + 비공개 채널 RLS(방 멤버만 구독/송신) + uid 기반 차단 + 서버 PIN 검사 + (선택) 공개 방 목록 |
| 공통 UI | `lpRoomsUI.js` 하나: 참가 화면 · 대기실(명단·연결점·게임별 선택·준비·시작 게이트·방장 도구·관전·리액션) · 플레이 중 **HUD 알약 1개**(기존 4개 부유 UI 대체) · 초대 시트 · 게임 전환. `/lobby/` = 진짜 허브, `/r/CODE` = 짧은 초대 링크 |
| 엔진 | 공통 커널(상태 봉투·seq·스냅샷·자동 저장·방장 감시·방장 승계) + 어댑터 5종: **draw**(공정 추첨·결정적 재생·동시 출발·검증 배지·자가검증 결과 링크) · **turn**(방장 권위·멱등 의도·턴 마감·봇 대행·자리 보호) · **realtime**(구미·SZX 브리지) · **db**(퀴즈 브리지) · **race**(솔로 아케이드 같은 시드 레이스) |
| 공정성 프리미티브 | `LpFair.draw`(1회 추첨: 방장 커밋 → 참가자 커밋 → 참가자 공개 → 방장 공개) · `LpFair.chain`(연속 사건: 해시체인 + 사건마다 "비밀을 모르는 사람"의 새 엔트로피) · `LpFair.deal`(숨김 배분: 공동 시드로 섞고 끝나면 공개 검증) |
| 예산 | 4인 대기방 **10.8 → 1.4 msg/s**(−87%), 8인 추첨 1회 **~1,800 → ~150 msg**. 하트비트 1종으로 통합, ping/pong·게임 hb 제거, 진행 점수·목격 해시는 하트비트에 편승, 틱 폭풍 제거 |
| 마이그레이션 | P0(v1 긴급 보강) ∥ P1(코어) → P2(UI) ∥ P3a/P3b(추첨) ∥ P4(보드) ∥ P5(레이스·브리지) → P6(정리) · P7(Phase B, 운영자 SQL 후). 게임별 기능 플래그(v1/v2), v1 과 채널 접두어가 달라 공존 |

### 0.1 원칙 (CLAUDE.md·메모리에서 온 제약 — 설계 전체에 적용)
- **로그인 없이 즉시** 참가·플레이. 로그인은 ✓ 배지·친구 초대에만.
- **모바일 세로 우선**, 글은 최소(키워드·아이콘·배지 1개). 상세는 접기/시트.
- 게임 = 자가완결 HTML. 공용은 `public/js/lp*.js` 로만(게임 간 import 금지). 어댑터 코드는 각 게임 파일 안에.
- 운영자가 만든 시스템은 없애지 말고 고도화(윷 대기실·SZX P2P·퀴즈 DB 엔진·카레이싱 LPFX 유지).
- 모바일 WebView 에서 RLS 직접 SELECT 금지 → DB 읽기는 SECURITY DEFINER RPC.
- presence 사용 금지(무료 20/s, 누락 실측) — 브로드캐스트 하트비트만.
- 커밋: `bump-cache.sh` 세션당 1회, 대형 작업 1~2 커밋, 워크트리는 `C:\code\python\luckyplz_wt\<pkg>`(`.claude/` 밖).

### 0.2 비목표
- 영상/화면 스트리밍(상태 동기화로 대체). CRDT(Yjs). TURN 서버. 서버 딜러(MPC) — 마작은 "방장=딜러" 고지 + 검증 가능한 배분으로 타협.
- 공개 방 목록은 기본 OFF(§5.6, Phase B 이후).

### 0.3 코드로 재확인한 사실 (감사 주장 검증)
- `lpRoom.js:483` PIN 평문 비교, `:1201` 부근 join_request 에 pin 실림 — 사실.
- `:478-480` 잠금 우회는 `p.rejoin&&isKnown` 일 때만 — 새로고침 첫 join(`rejoin:false`) 차단 사실.
- `:644-655` guest:action 은 `gid` 명단 존재만 확인하고 payload 그대로 전달, `:1775` `Object.assign({gid,nickname,...},payload)` 로 payload 가 nickname/pid 를 덮어씀 — 사칭 사실.
- `:895-897` host broadcast 가 tick 에도 `++_bcastSeq`, `:1545` 게스트는 tick 을 seq 추적에서 제외 → 틱 뒤 첫 이벤트에서 가짜 gap — 스냅샷 폭풍 사실. 또 `broadcastReliable` 재전송마다 seq 증가(`:925`).
- `:1569-1580` 핫픽스 확인: navigate 는 같은 origin `/games/<id>/` 만. **`/lobby/` 로는 못 감**(v2 는 URL 대신 gameId 로 전환 → 문제 소멸).
- `:3320` `_validGames` 에 `bubble`(멀티 없음) 포함, 목록 4중 정의 사실(`lpMultiplayer.js:111` 7종 등).
- `vendor/supabase.min.js`(2.104): `signInAnonymously` · `httpSend` · 채널 `private` · `setAuth` · realtime `workerUrl` 지원 확인 → Phase B 와 백그라운드 워커 하트비트가 라이브러리 교체 없이 가능. `eventsPerSecond` 클라 스로틀 없음.
- `lpInApp.js:35-37` intent 이스케이프가 `#hash` 보존(주석) — 초대 토큰을 fragment 에 둬도 된다(실기기 확인 항목으로 남김).
- supabase 미탑재 게임: balloon·brick·bubble·glory-racing·lucky-merge·mahjong-solitaire·starship-lander·orbit(+snake/pacman/burger/tetris/dice 는 탑재). → v2 는 **필요할 때 지연 로드**.

---

## 1. 아키텍처 개관

```
┌──────────────────────── 게임 페이지 /games/<id>/ (자가완결 HTML) ─────────────────────────┐
│  게임 코드  ── LpRooms.adapter({...})  ← 어댑터(게임 파일 안)                               │
│                    │                                                                          │
│   lpRoomsTurn.js   lpRoomsRace.js   lpFair.js(draw 커널+공정성)      ← 유형별 커널          │
│                    │                                                                          │
│   lpRoomsUI.js  (참가·대기실·HUD·초대·전환·배지·리액션, 16개 언어)                          │
│                    │                                                                          │
│   lpRoomsCore.js (신원·코드·채널·봉투 서명/검증·핸드셰이크·명단·하트비트·시계·감시·승계·저장) │
│                    │                                                                          │
│   lpGames.js (게임 레지스트리 단일 원천)        vendor/supabase.min.js (Realtime broadcast)   │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
     채널: lpr-<CODE>  (이벤트 이름 2개뿐: 'h' 방장→모두, 'g' 게스트→모두)
     레거시: lp-room-<CODE>(v1, 공존) · qlive-<숫자>(퀴즈) · szx-race-<숫자>(SZX)
```

로딩: `siteFooter.js` 가 (a) 페이지가 v2 게임(레지스트리 `mp.v==='v2'`)이고 supabase 가 있거나 (b) URL 에 `?r=`·경로 `/r/` 가 있거나 (c) 사용자가 👥 를 누르면 → `supabase.min.js`(없으면) → `lpGames.js` → `lpRoomsCore.js` → `lpFair.js` → `lpRoomsUI.js` (+ 어댑터 kind 에 따라 `lpRoomsTurn.js`/`lpRoomsRace.js`) 를 순서 보장 로드(각 스크립트 `onload` 체인, `?v=` 스탬프). 게임은 폴링 대신 `await LpRooms.ready()`.

---

## 2. 방 신원·참가 계약 (모든 게임 공통)

### 2.1 방 코드
- 알파벳 `23456789ABCDEFGHJKMNPQRSTVWXYZ`(30자, 0/O/1/I/L/U 제외), 길이 6, **글자(A–Z) 최소 1개**. 표시 `K7M-2QX`(3-3), 입력은 대소문자·하이픈·공백 무시.
- **자기 인증 코드**: 방장이 방마다 새 키쌍 2개(서명용 ECDSA P-256 `rsk`, 암호용 ECDH P-256 `rdk`)를 만들고
  `F = SHA-256("lpr2-room" ‖ raw(rsk.pub) ‖ raw(rdk.pub))` (32바이트, raw = 65바이트 비압축 점)
  `code = base30( F[0..5] 를 48비트 정수로 → mod 30^6 )` (편향 < 0.0003%). 숫자만 나오면(확률 0.036%) 키 재생성.
- 충돌: 방장은 채널 `lpr-<code>` 를 1.2초 구독해 다른 키의 `h:hello` 가 들리면 키 재생성(최대 5회).
- 의미: 코드 = 방장 키 지문 앞 29.4비트. 코드만 아는 사람이 방장을 사칭하려면 같은 코드를 내는 키를 찾아야 하고(평균 7.3억 회 키 생성), 그래도 진짜 방장이 동시에 응답하므로 충돌이 드러난다(§3.3).
- 방 수명: 마지막 방장 활동 후 24시간(방 키 IndexedDB 삭제). 게임을 바꿔도 코드 불변.

### 2.2 코드 해석 `LpRooms.resolve(input)` — 홈·허브·게임 어디서든 같은 함수
입력: 코드, `K7M-2QX`, `/r/K7M2QX#k=..`, `/games/yut/?r=..`, 옛 `?room=`, 퀴즈 `?c=123456`, SZX 링크.
1. URL 이면 파싱: `/r/<code>` 또는 `?r=` → v2 코드 + fragment `k`. `?room=` → v1/v2 후보. `?c=` → 퀴즈. SZX 링크 파라미터(dodge 의 기존 형식) → SZX.
2. 정규화 후 분기(병렬 probe, 먼저 확정되는 것 채택, 전체 타임아웃 4초):
   - 글자 포함 6자: `lpr-<code>` 에 `g:hello_req` → `h:hello`(v2). 동시에 **전환 기간에만** `lp-room-<code>` 에 v1 `guest:probe`.
   - 숫자 6자리: 퀴즈 `qlive_state(code)` RPC 존재 확인 → 없으면 `szx-race-<code>` 채널 3초 수동 청취(SZX 는 2.5초마다 `st` 하트비트를 쏘므로 추가 코드 없이 감지). 둘 다 있으면 선택 칩 2개.
3. 결과 `{kind:'rooms'|'rooms-v1'|'qlive'|'szx'|'none', code, gameId, url, hello}` → UI 가 해당 페이지로 이동(v2 는 `/games/<gameId>/?r=<code>` + fragment 유지, gameId 가 `lobby` 면 `/lobby/?r=`).

### 2.3 링크 · QR · 공유 · 인앱
- **초대 링크(정식)**: `https://luckyplz.com/r/K7M2QX#k=<fp>.<tok>`
  - `fp` = `F[0..15]` base64url(22자) — 링크로 온 사람은 방장 키를 128비트로 고정 검증.
  - `tok` = 방 초대 토큰 16바이트 base64url(22자) — "초대받음" 증명(PIN·승인 대기 면제). 방장이 `🔄 링크 새로` 로 교체 가능(차단 직후 권장).
  - fragment 라 서버 로그·Referer 에 안 남는다. 페이지는 읽자마자 `sessionStorage.lpr_inv` 로 옮기고 `history.replaceState` 로 주소창에서 지운다.
- `/r/*` 는 `_redirects` 한 줄 `/r/*  /lobby/  200` 으로 허브 페이지가 받아 `resolve` → 해당 게임으로 `location.replace`(fragment 는 sessionStorage 경유라 유실 없음).
- **QR**: 같은 링크를 `/vendor/qrcode.js`(이미 내장)로. 회사 환경(카메라 불가)을 고려해 **1순위는 "메신저로 초대" 버튼**(Web Share API → 실패 시 복사), QR 은 초대 시트 안 작게(퀴즈 원칙과 동일).
- 공유 문구(짧게): `🎲 {게임명} 같이 해요 · {코드}\n{링크}`. `lpShare.js` 재사용.
- 인앱 브라우저: `lpInApp.js` 자동 이스케이프 유지. 참가 절차는 **이스케이프가 끝난 브라우저에서만** 시작(신원이 한 번만 생기게): `LpRooms` 는 `window.LpInApp && LpInApp.willEscape()` 가 true 면 핸드셰이크를 미룬다(P2 에서 `lpInApp.js` 에 `willEscape()` 1줄 공개). 이스케이프 시 fragment 보존은 실기기 체크리스트 항목.
- 옛 링크: `?room=<CODE>&pin=&nick=` 는 계속 동작(§9.4 호환).

### 2.4 닉네임 · 아바타
- `localStorage.lp_profile = {nick, av, v:1}`. 최초엔 `luckyplz_nick`·`lp_qlive_nick`·`szx_nick`·로그인 표시명 순으로 채워 마이그레이션(읽기만, 옛 키 유지).
- 아바타 = 16종 이모지 칩(동물·장난감, 기본 🐼 레서판다 마스코트 계열) 인덱스 `av`. 이미지 업로드 없음.
- 🎲 버튼 = 친근한 닉네임 생성기(형용사+동물, 언어별 24×24 단어) — 교실·가족 사용.
- 위생: NFKC 정규화, 제어문자·양방향 제어(U+202A–202E, U+2066–2069)·제로폭 제거, 1~12 그래핌, 방장 이름과 같으면(대소문자·NFKC 무시) 뒤에 숫자. 렌더는 항상 `textContent`. 금칙어 짧은 목록(ko/en/ja/es/pt) → `***`.
- 저장된 닉네임이 있으면 **링크 한 번에 자동 입장**(묻지 않음). 첫 입장 화면은 닉네임 칸 1개 + 아바타 줄 + [입장].

### 2.5 기기 신원 (pid) 과 탭 (tid)
- 기기 키: `crypto.subtle.generateKey({name:'ECDSA',namedCurve:'P-256'}, false, ['sign','verify'])` + ECDH P-256(`deriveKey`) — **extractable:false**, IndexedDB `lp-id`/`keys` 에 CryptoKey 그대로 저장(구조화 복제). 공개키는 JWK 로 함께 저장.
- `pid = 'p' + base32(SHA-256("lpr2-dev" ‖ raw(dsk.pub)))[0..19]` (100비트). **pid 는 키에서 계산되므로 남이 내 pid 를 주장할 수 없다**(모든 게스트 메시지가 그 키로 서명).
- 폴백: IndexedDB/CryptoKey 저장 불가 → 메모리 키(페이지 수명) + `sessionStorage` JWK(추출 가능 키) → 새로고침 복귀는 되지만 탭 간 공유는 안 됨. `crypto.subtle` 자체가 없으면 v2 미지원 안내(외부 브라우저 권유) — 현실적으로 해당 없음.
- 레거시 `lp_pid` 는 건드리지 않는다(솔로 게임 기록용). v2 게임의 pid 기반 저장(빙고 카드 등)은 새 pid 로 키잉.
- `tid = crypto.randomUUID()` (페이지 로드마다 새로). 진단·잠금용일 뿐 신원이 아니다.
- **한 기기 = 방 안 한 자리.** 참가 시 `navigator.locks.request('lpr-seat-'+code, {ifAvailable:true})`. 못 잡으면 "다른 탭에서 이 방이 열려 있어요 · [여기서 계속]" → `{steal:true}` 로 재요청, 빼앗긴 탭은 lock 콜백 promise 거절(AbortError)로 감지해 조용히 분리(`bye` 안 보냄, 같은 pid 라 방장 쪽 좌석 그대로). Web Locks 없으면 `BroadcastChannel('lpr-tabs')` 로 같은 동작.
- 방장 탭: 기존 item 16 과 같은 `lpr-host-<code>` 락(탭당 방장 1명).
- 개발용 한 브라우저 다인 테스트: `localhost`/`127.0.0.1` 에서만 `?lpdev=tab` → 기기 키를 sessionStorage 에 두어 탭마다 다른 pid(윷 `yut_tabpid` 대체). 운영 도메인에선 무시.

### 2.6 참가 핸드셰이크 (v2)
```
게스트                                   채널 lpr-<CODE>                        방장
 subscribe ──────────────────────────────────────────────────────────────────▶
 g{e:'hello_req', n:<8B>}  (익명, 무서명) ──────────────────────────────────▶
                                   ◀── h{e:'hello', d:{v:2, code, ep, rpk:{sig,dh}, gameId, kind,
                                         phase, lock, appr, pinReq, count, max, succ?}, z}
 [검증] fp(rpk) 앞 6자 == code (링크면 128비트 fp 일치)
        400ms 동안 다른 rpk 의 hello 가 오면 → "방장 확인 실패(응답 2개)" 중단
        서명 z 검증(rpk.sig)
 g{e:'join', p:pid, c:1, d:{dpk:{sig,dh}, tid, nick, av, want:'play'|'watch',
     au?:{uid,name,proof}, x:ECIES(rpk.dh, {tok?|pin?, n})}, z(dsk)} ─────────▶
                                                                   [검증 순서]
                                                                   1 z 서명·pid==fp(dpk)
                                                                   2 차단 목록(pid)
                                                                   3 레이트리밋(§3.4)
                                                                   4 알려진 pid → 무조건 복귀(잠금 무시)
                                                                   5 잠금/정원/늦참 정책(§2.7)
                                                                   6 증명: tok 일치 | pin 일치 | 공개방
                                                                      | 승인 모드면 대기열
                   ◀── h{e:'welcome', to:pid, d:{ok:true, role, seat?, nick(확정), mk?:ECIES(dpk.dh, 방 봉인키),
                         st:<현재 상태 전체, 32KB 이하면 동봉>}, s, z}
                   ◀── h{e:'roster', ...} (100ms 뭉침)
 MEMBER 상태, 하트비트 시작
```
- 거절: `h{e:'deny', to:pid, d:{r:'bad_proof'|'locked'|'full'|'banned'|'rate'|'version'|'closed'|'pending'|'wrong_game'}}`. `pending` = 승인 대기(방장 화면에 "✋ 민지 입장 요청 [✓][✕]").
- 재시도: 응답 없으면 2s·4s·7s 재전송(같은 `c`, 방장 멱등). 10초 넘으면 "방을 찾지 못했어요 · 코드 확인" + [다시].
- `wrong_game`: 방이 다른 게임이면 hello 의 gameId 로 **게스트가 스스로 이동**(방장 navigate 불필요).
- 방장 쪽 멱등: `(pid, c)` 이미 처리 → 같은 welcome 재전송.

### 2.7 정원 · 관전 · 늦참
- 방 최대 인원(관전 포함) **12**(예산, §7). 어댑터가 좌석 수를 정하고 나머지는 관전.
- `want:'watch'` 로 들어오면 관전 고정(좌석 요청 안 함).
- 늦참 정책(어댑터 `lateJoin`):

| 값 | 의미 | 쓰는 곳 |
|---|---|---|
| `anytime` | 언제든 멤버, 진행 중이면 현재 장면부터 시청 | 추첨 전부(시청형) |
| `nextRound` | 관전으로 들어와 다음 판 좌석 | 레이스, 구미 |
| `takeBot` | 봇 좌석 인계 가능(방장 자동 승인), 없으면 관전 | 윷·루도·프리즘·마작 |
| `spectate` | 관전만 | 리버시(2석), 퀴즈 브리지 |

- `lock` 은 "새 사람 입장 금지"(알려진 pid 는 항상 복귀). 한 판 끝나 대기실로 가면 **자동 해제**(현재 unlock 누락 버그 제거 — 커널이 phase 로 관리, 게임은 lock 을 직접 부르지 않음).

---

## 3. 신뢰 모델

### 3.1 위협 모델
| 공격자 | 능력 | 막아야 할 것 |
|---|---|---|
| T1 코드만 아는 외부인 | 채널 구독·임의 방송 | 방장 사칭(강퇴·전환·종료·결과), 게스트 사칭, PIN 도청·대입, 명단 수집 |
| T2 참가자(친구) | 정상 멤버 + 콘솔 조작 | 남의 의도 위조, 자리 뺏기, 결과 조작, 방 폭파 |
| T3 방장 | 방장 권한 | 결과 골라 뽑기(재추첨), 추첨 목록 사후 변경, 숨은 정보 악용(한계 고지) |
| T4 차단된 사람 | 저장소 삭제·새 기기 | 재입장 |
| T5 재생 | 옛 서명 메시지 녹화 | 옛 강퇴·종료 재방송 |

### 3.2 Phase A — 서명 봉투 (서버 변경 0, 지금 구현)
**채널 이벤트는 2개뿐**: `h`(방장 발신), `g`(게스트 발신). 와일드카드·이벤트 등록 누락 문제(realtime 함정 #2, `KNOWN_HOST_EVENTS` 누락)가 원천 소멸.

방장 봉투:
```js
{ v:2, e:'state', ep:1759212345678, s:42, /* 또는 t:1234 (틱 전용 카운터) */
  to:'p…'|['p…'], id:'x7Qa' /* 재전송 공유 id, 선택 */,
  j:'{"phase":"lobby",...}'  /* d 를 JSON 문자열로 — 정규화 문제 없이 그대로 서명 */,
  c:{iv,ct} /* 봉인 모드면 j 대신 AES-GCM 암호문 */,
  z:'<base64url 64B r||s>' }
```
서명 대상 문자열: `lpr2|h|<code>|<ep>|<s 또는 't'+t>|<e>|<to 정렬 join ','>|<j 또는 iv.ct>` → ECDSA P-256 SHA-256(`rsk`).

게스트 봉투: `{v:2, e, p:pid, c:<cseq>, j, z}` · 대상 `lpr2|g|<code>|<pid>|<c>|<e>|<j>` → `dsk` 서명. `hello_req` 만 무서명.

**검증 규칙(멤버):** 서명 불일치·`v≠2`·`ep` 이 알고 있는 ep 보다 작음·같은 ep 에서 `s ≤ 마지막 s`(단 같은 `id` 재전송은 조용히 버림)·`t ≤ 마지막 t` → 버림. `j` 32KB 초과 버림. 새 `ep` 는 같은 방장 키(또는 §6.0.6 승계 증명) 서명일 때만 채택.
**검증 규칙(방장):** 게스트 서명 불일치·`pid≠fp(dpk)`·명단에 없는 pid(join 제외)·`c ≤ 마지막 c` → 버림(같은 c 재전송은 저장된 응답 재발송). 신원은 **항상 봉투의 pid**, 페이로드의 이름·pid 는 무시.
**비용:** WebCrypto P-256 서명 ≈0.1ms(PC)/≈0.5ms(중급 안드로이드), 검증 비슷. 20Hz 틱도 CPU 1% 미만. 봉투 +~110바이트. 서명은 비동기이므로 방장 송신은 **직렬 큐**(순서 보존), 게스트 검증도 도착 순서 큐.
**봉인 모드(`sealed`, 기본 ON, 플래그로 끌 수 있음):** 방장이 방 봉인키 `mk`(AES-GCM 256) 를 만들어 welcome 때 각 게스트의 `dpk.dh` 로 ECIES 전달. 이후 `hello`/`deny`/`welcome` 외 모든 `h` 는 `c` 암호문 → 코드만 아는 외부인은 명단·이름·결과를 못 본다(H5 해결). 추방 시 `mk` 교체(남은 멤버 각자에게 `h{e:'rekey', to:pid}` N−1통). 게스트 발신 `g` 도 `j` 를 `mk` 로 봉인(join 제외).
- ECIES 정의: 발신자 임시 ECDH 키 `eph` → `shared = ECDH(eph.priv, 수신 dh.pub)` → `HKDF-SHA256(shared, salt=code, info='lpr2-ecies|'+용도)` → AES-GCM(12B iv). 전송 `{epk:raw(eph.pub) b64, iv, ct}`.

### 3.3 방장 키 확인(코드만 입력한 사람)
- 링크/QR: `fp` 128비트 고정 → 모호함 없음.
- 코드 입력: TOFU. 첫 `hello` 뒤 **400ms 동안 다른 키의 hello 가 오면 중단**("방장 확인이 안 돼요. 링크로 들어오세요"). 진짜 방장은 항상 응답하므로 가짜가 몰래 이길 수 없다.
- **봉인 이모지**: `F` 에서 뽑은 이모지 3개(64종 표, 18비트)를 HUD·대기실 헤더에 모든 기기가 같게 표시(예 `🍋🐼🚀`). 한자리에 모인 사람들이 서로 화면을 보고 확인 가능 — 문구 없음, 탭하면 "모두 같은 그림이면 같은 방" 한 줄.

### 3.4 PIN · 토큰 · 무차별 대입
- 기본 방 = **코드/링크 공개**(PIN 없음, 퀴즈와 같은 경험). 방장이 대기실에서 `🔒 PIN` 을 켜면 **코드 입력자만** 4자리 PIN 필요(링크 토큰 보유자는 면제).
- PIN·토큰은 `join.x` 안에 **방장 dh 공개키로 ECIES 암호화** → 채널 청취자가 볼 수 없다(현재 평문 유출 해결). PIN 은 방송 어디에도 안 실림(방장 로컬에만).
- 레이트리밋(방장, 방 단위): 잘못된 증명 **10회/60초 → 60초 쿨다운**(쿨다운 중 증명 기반 새 입장은 `rate`, 알려진 pid 복귀·토큰 보유자는 통과). 4자리 1만 공간 → 기대 성공 시간 ≈ 8시간 이상. `hello_req`/`join` 처리량 **초당 20건** 상한(초과 무시). 방장 화면에 "🔒 PIN 시도 많음" 칩.
- 공개방에서 스팸 입장 대응: `✋ 승인 모드`(새 입장자는 방장 ✓ 필요) 토글. 차단 직후 10분간 자동 ON.

### 3.5 추방 · 차단 (저장소 삭제에도 최대한 버티기)
- `room.kick(pid,{ban})` → `h{e:'kicked', to:pid, d:{ban}}`(재전송 3회) + 명단 제거 + 봉인키 교체.
- 차단 목록 = pid(키 기반, 위조 불가) + 닉네임(정규화) 소프트 플래그 + 기기 표식(`localStorage`·IndexedDB·쿠키 `lpr_ban_<code>` — 순진한 재입장 자기 거절).
- 저장소를 지운 사람 = 새 pid → 막을 방법이 서버 없이는 없다(정직하게 인정). 대신: 차단 시 **자동 승인 모드 10분 + 링크 토큰 교체 권유** → 새 pid 는 방장 ✓ 없이 못 들어온다. 차단된 닉네임과 같은 이름이 승인 대기에 오면 ⚠ 표시.
- Phase B 에서는 uid 차단 + 익명 가입 IP 제한(시간당 30)·Turnstile 로 비용을 올린다.

### 3.6 Phase B — Supabase 익명 로그인 + 비공개 채널 (운영자 SQL 후)
얻는 것: 멤버만 구독·송신(서버 강제) → T1 원천 차단, uid 차단(T4 비용 증가), PIN 검사를 RPC 로(대입 서버 제한), 방 메타 DB(공개 방 목록·친구 "지금 이 방" 표시 가능), 빙고 등 서버 확정이 필요한 결과를 `realtime.send` 로.
유지: 방장 서명·게스트 서명(Phase B 에서도 이벤트별 권한은 RLS 로 구분하기 어려우므로 서명이 방장/게스트 구분을 계속 맡는다).

**운영자가 할 일(정확히):**
1. Supabase 대시보드 → Authentication → Sign In / Providers → **Allow anonymous sign-ins: ON**.
2. (권장) Cloudflare Turnstile 사이트 추가(luckyplz.com, Managed) → SITE KEY 를 `supabase-config.js` `TURNSTILE_SITE_KEY` 에(에이전트가 커밋), SECRET KEY 를 Authentication → Attack Protection → Captcha(Turnstile)에 입력. ⚠ 켜면 이메일 로그인·가입도 캡차가 필요(기존 폼은 이미 대응 코드 있음). 둘을 같은 배포에서 맞춰야 한다.
3. Realtime → Settings: **"Allow public access" 는 켠 채로 둔다**(퀴즈 nudge·SZX·v1 은 공개 채널).
4. SQL Editor 에 `supabase/migrations/2026-10-XX-rooms-v2.sql` 전체 붙여넣기 → Run → 끝의 확인 쿼리 결과 행 수 확인(에이전트가 기대값 명시). 내용:
   - `lpr_rooms(code text pk, host_uid uuid, game_id text, rpk_sig text, created_at, last_seen, expires_at, locked bool, appr bool, pin_hash text, tok_hash text, max_members int, listed bool default false)`
   - `lpr_members(code, uid, role, banned bool, joined_at, pk(code,uid))`
   - RLS 전면 차단 + SECURITY DEFINER RPC: `lpr_create(code, game_id, rpk_sig, tok_hash, pin_hash, max)`(방장 서명 검증은 클라, 서버는 코드 중복·방장 uid 기록·생성 12회/시간 제한), `lpr_join(code, tok, pin) → {ok, reason}`(PIN 실패 uid·방당 제한), `lpr_kick(code, uid, ban)`(host_uid 만), `lpr_touch(code)`, `lpr_close(code)`, `lpr_list(game_id)`(listed=true 만, 나중).
   - `realtime.messages` 정책: `select`/`insert` 모두 `realtime.topic() like 'lprp-%' and public._lpr_is_member(substr(realtime.topic(),6), auth.uid())`(SECURITY DEFINER 헬퍼 — 멤버 테이블 RLS 우회), `extension in ('broadcast')`.
   - 만료 정리: `pg_cron` 1시간마다 `delete from lpr_rooms where expires_at < now()`(pg_cron 미사용이면 `lpr_create` 안에서 오래된 행 청소).
5. 에이전트의 운영 검증 스크립트(anon 키로 RPC·비공개 채널 가입/거절 12항목) 결과 확인.
**사이트 영향(에이전트 몫):** 익명 세션도 `getUser()` 에 잡히므로 로그인 표시(topNav·lpSocial·auth·lpPresence·lpInvite)가 `user.is_anonymous` 를 로그인으로 취급하지 않게 전수 수정. 익명 세션은 방 기능이 처음 필요할 때만 생성(`signInAnonymously` 지연 호출). 로그인 사용자는 실제 uid 그대로 사용.
채널 이름은 `lprp-<CODE>`(비공개) 로 분리 — Phase A 방과 공존, 레지스트리 플래그 `mp.trust:'A'|'B'` 로 게임별 전환.

---

## 4. 공통 로비 UI (`lpRoomsUI.js`)

### 4.1 화면 목록
| 화면 | 언제 | 핵심 요소 |
|---|---|---|
| **참가 시트** | 코드/링크로 도착, 닉 없음 | 코드 표시(링크면 자동) · 닉네임 1칸+🎲 · 아바타 줄 · [입장] · (PIN 켜진 방+코드 입력자만) PIN 4칸 |
| **대기실(풀)** | turn·race·realtime·db 게임 | 아래 목업 |
| **대기실(띠)** | draw 게임 | 게임 설정 화면 위 명단 띠 1줄 + [초대] · 게스트는 방장 설정이 읽기 전용으로 미러링 · 방장이 켜면 [✋ 내 이름 넣기] |
| **HUD 알약** | 플레이 중 전부 | `K7M-2QX · 👥5 · ●` (32px, 우상단, `LpChrome.setPlaying` 시 점 하나로 접힘) · 탭 → 방 시트 |
| **방 시트** | HUD 탭 | 명단 · 초대 · (방장) 🔒 잠금/✋ 승인/⏸/⏹ 대기실로/🎮 게임 바꾸기/👑 방장 넘기기/✕ 방 닫기 · (게스트) 나가기 |
| **초대 시트** | [초대] | [💬 메신저로 초대](1순위, Web Share) · 링크 한 줄 + [복사] · QR(작게) · 코드 크게 · (로그인 시) 친구 목록 초대 · 🔄 링크 새로 |
| **방장 끊김 띠** | 감시(§6.0.5) | 노랑 "방장 확인 중…" → 빨강 "방장 연결 끊김 · [기다리기][나가기]" → (승계 가능 게임) "민지가 방장을 이어받았어요" |
| **일시정지 오버레이** | 방장 ⏸ | 기존 lpHostCtl 오버레이를 UI 모듈로 흡수, 16개 언어 |
| **결과 배지** | draw 결과 | `✓ 공정 · 5명 확인` 1개 · 탭 → 검증 시트(참가자 기여 ✓, 시드 앞 8자, [결과 링크 복사], [다시 보기]) |

### 4.2 대기실(풀) 목업 — 세로 폰 360×740 기준, 글자는 이것뿐
```
┌──────────────────────────────────────┐
│ 🎲 윷놀이           K7M-2QX  🍋🐼🚀 │ ← 게임 아이콘+이름, 코드, 봉인 이모지
│ [💬 초대]  [▦ QR]              ⋯     │ ← ⋯ = 방장 도구(방 시트)
├──────────────────────────────────────┤
│ 👑 🐼 준호        ● 🐯            │ ← 방장, 연결점, 게임별 선택칩
│ ✓  🦊 민지        ● 🐰            │ ← ✓=준비
│    🐨 Alex        ◐ 🐶  (다른 앱)  │ ← ◐=away
│ 🤖 봇             ● 🐼       [✕]   │ ← 방장만 봇 제거
│ [+ 봇]                               │
│ 👀 2 관전                      ▾     │ ← 접힘
├──────────────────────────────────────┤
│ 내 캐릭터  🐯 🐰 🐶 🐼 (잠김=흐림)   │ ← 어댑터 picks 슬롯
│ 턴 시간    15 · [30] · 60            │ ← 어댑터 options(방장만 변경)
├──────────────────────────────────────┤
│ 👍 😂 😱 🔥 👏 🍀                    │ ← 리액션(선택)
│ [ 준비 ✓ ]            (게스트)        │
│ [ 시작 ▶ ]  (전원 준비 · 2명+) (방장) │ ← 조건 미달이면 흐림 + 아이콘 힌트
└──────────────────────────────────────┘
```
- 명단 행 탭(방장): 시트 `[내보내기] [내보내고 차단] [👑 방장 넘기기] [관전으로]`. 확인은 자체 확인창(`window.confirm` 금지 — 인앱에서 막힘).
- 시작 게이트: `adapter.canStart(roster)` 기본 = 좌석 ≥ min ∧ 좌석 게스트 전원 `ready ∧ online`. 20초 이상 막혀 있으면 방장에게 `[준비 안 된 사람 관전으로 두고 시작]`.
- 연결점: ● online(녹) · ◐ away(노, `vis:hidden`) · ○ offline(회) · 🤖 bot. 색+모양 둘 다(색맹 대응), `aria-label`.
- 선택칩 규칙: `unique:true` 면 남이 고른 것 흐림, 봇 것은 맞바꿈(윷 `lbPick` 일반화). 선택은 게임별로 기억(`mem[gameId][pid]`).
- 리액션: 6종, 1인당 1.2초에 1번, 아바타 위 떠오름. 대기실·결과·추첨 시청 중에만(플레이 중 끔). 운영자 결정 항목.

### 4.3 상태 기계
방(방장이 소유, `phase` 로 방송):
```
CREATED ──(첫 hello 응답 가능)──▶ LOBBY ──start()──▶ STARTING(startAt 카운트다운 1.5s)
   ▲                                │  ▲                     │
   │                          switchGame()                   ▼
   │                                │  └──── toLobby() ◀── PLAYING ⇄ PAUSED
   │                                ▼                        │
   └──────────── (새 페이지에서 resume) ◀──────────────── RESULT ──▶ LOBBY
 어디서든 close() ─▶ CLOSED     방장 끊김 ─▶ (게스트 관점) HOST_LOST ─▶ 복귀|승계|종료
```
멤버(각 기기):
```
IDLE ─resolve─▶ PROBING ─hello✓─▶ JOINING ─welcome─▶ MEMBER{role, conn, ready}
                    │ 충돌/없음        │ deny            │  kicked/closed ─▶ LEFT(이유 표시)
                    ▼                  ▼                 │  탭 빼앗김 ─▶ DETACHED("다른 탭에서 계속 중")
                  ERROR              DENIED              ▼
                                                    HOST_LOST(12s)→(20s)→ 승계/대기
```

### 4.4 `/lobby/` 허브 + `/r/`
`public/lobby/index.html` 재작성(noindex 유지, `_headers` 에 `/lobby/*`·`/r/*` → `X-Robots-Tag: noindex`):
- 상단: **코드 입력 6칸**(자동 이동, 붙여넣기=링크 전체 허용, 확인 즉시 `resolve`).
- [＋ 방 만들기] → 5분류 아이콘(`toy-cat-*.webp`) → 게임 타일(`toy-<id>.webp`, 레지스트리의 mp 가능 게임만) 또는 **[먼저 모이기]**(gameId `lobby` — 이 페이지가 대기실, 방장이 나중에 고름).
- 최근 방: `localStorage.lpr_recent`(최대 5, 코드·게임·방장·시각) → 보일 때 한 번 `hello_req` 로 살아있는지 점(●/○) 표시, 탭 = 재입장.
- 경로 `/r/<code>` 로 오면 위 UI 없이 바로 resolve → 이동.
- 홈(`public/index.html`)의 "방 참가" 버튼은 `LpRooms.UI.openJoin()` 호출로 교체(v2 로드 시), 없으면 기존 v1 모달. 홈 수정 후 `python scripts/gen-lang-home.py`. 홈에 새 글·링크 추가 금지(UI 밀도 규칙) — 버튼 동작만 바꾼다.
- 게임 페이지 진입점: `LpChrome` 도크(⛶·🔊·?)에 **👥 버튼 1개**(레지스트리 mp 가능 게임만) → 방 만들기/참가 시트. 게임이 자체 온라인 버튼(윷 모드 화면 등)을 가진 경우 그 버튼도 `LpRooms.UI.openCreate()` 호출.

### 4.5 게임 전환(파티 이동)
- 방장 `🎮 게임 바꾸기` → 레지스트리 그리드 → `room.switchGame(gameId)` → `h{e:'switch', d:{gameId}}`(재전송 3회) → 방장은 새 페이지로 이동, 멤버는 **자기 레지스트리에서 경로를 만들어** `/games/<id>/?r=<code>` 로 600ms 뒤 이동(URL 을 받지 않으므로 오픈 리다이렉트 불가능). 새 페이지에서 `LpRooms.resume()` → 방장은 IndexedDB 방 키로 같은 코드 재개, 멤버는 알려진 pid 로 조용히 복귀. 준비 초기화, 선택은 게임별 기억.
- 레지스트리에 없는 gameId → 무시 + 디버그 로그.

### 4.6 공개 방 목록 (기본 OFF, 나중)
Phase B 이후: 방장이 `🌐 공개` 를 켜면 `lpr_rooms.listed=true`. 허브에 "지금 열린 방" 목록(`lpr_list` RPC, 게임·인원·방장 닉, 30초 캐시). 조건: 신고 버튼·닉 필터·승인 모드 강제·어린이 사용 고려. Phase A 에선 서버 목록이 없으므로 불가.

### 4.7 문구·i18n
- 모든 문자열은 `lpRoomsUI.js` 안 표 1개, **16개 언어**(ko en ja es pt zh de fr ru ar hi th id vi tr gb→en), `luckyplz_lang` 추종, 언어 전환 이벤트 재렌더. 문구는 2~4단어·아이콘 우선(총 ~70키). `lpHostCtl` 기본 문구 한국어 하드코딩 문제는 이 표로 흡수.
- `aria-live=polite` 영역 1개: "내 차례", "방장 연결 끊김", "민지 입장".

---

## 5. 게임 레지스트리 (`lpGames.js`) — 목록 4중 정의 제거

```js
window.LP_GAMES = [
  { id:'roulette', path:'/games/roulette/', cat:'draw', icon:'/assets/tiles/toy-roulette.webp',
    name:{ko:'룰렛', en:'Wheel', ja:'ルーレット', es:'Ruleta', pt:'Roleta', /* …16 */},
    mp:{ kind:'draw', v:'v2', seats:null, max:12, trust:'A' } },
  { id:'yut', …, mp:{ kind:'turn', v:'v2', seats:[2,4], max:8 } },
  { id:'quiz', …, mp:{ kind:'db', v:'v2' } },
  { id:'snake', …, mp:null },          // 멀티 없음
  { id:'lobby', path:'/lobby/', mp:{kind:'lobby', v:'v2'} },
  …
];
LpGames.get(id) · LpGames.mp() (mp 가능 목록) · LpGames.name(id, lang)
```
- `lpRoom.js` 의 `_LP_PICKER_GAMES`·`_validGames`·`_v`, `lpMultiplayer.js` `GAMES`, `lpInvite*.js` `_humanGame` 은 P6 에서 전부 이 레지스트리를 읽게 바꾼다. 새 게임 체크리스트에 "lpGames.js 1줄"만 남는다.
- 기능 플래그도 여기(`mp.v`). 긴급 오버라이드: `localStorage.lpRoomsV='1'|'2'`(개인), `?rooms=v1`(링크 단위).
  - (2026-09-30 통합) 판정은 `LpGames.v(id)` / `LpGames.override()` 한 곳 — 우선순위 링크 `?rooms=v1|v2` > 이 탭 고정 `sessionStorage.lpr_v2`(?rooms=v2 를 본 탭) > 개인 `lpRoomsV`('1'|'2'|'v1'|'v2') > 표. siteFooter 로더도 같은 순서. 게임·UI 는 다시 구현하지 말 것.

---

## 6. 세션 엔진

### 6.0 공통 커널 (`lpRoomsCore.js`)

#### 6.0.1 상태 봉투
방장이 가진 권위 상태(커널 소유, 어댑터는 `game` 만 다룸):
```js
S = { v:2, seq:42, phase:'lobby'|'starting'|'playing'|'paused'|'result',
      gameId:'yut', opts:{turnSec:30}, startAt:null /* 방장 시계 ms */,
      roster:[ {p, n, av, r:'host'|'player'|'spec'|'bot', seat, pick:{sp:'tiger'}, rd, c:'on'|'away'|'off', j, au, afk} ],
      succ:['p…','p…'] /* 승계 순서, 방장 서명 명단에 포함 */,
      lock:false, appr:false, pinReq:false,
      turn:{ seat, n, deadline /* 방장 시계 */ } | null,
      fair:{ round, st:'commit'|'reveal'|'done', … } | null,
      log:[ …최근 64개 수 ],             // 이벤트 소싱: 재접속·관전·리플레이
      game:{ …어댑터 상태… } }
```
- 모든 변경 = `room.setState(fn)` → seq+1 → 방송: 어댑터가 `delta:true` 면 `h{e:'delta', d:{base, ops}}`(JSON 경로 set/del 목록), 10번마다 또는 요청 시 `h{e:'state', d:S}` 전체. 기본은 전체(보드게임 상태 ≤ 4KB).
- 명단만 바뀌면 `h{e:'roster'}`(100ms 뭉침, 전체 명단).
- 숨은 정보: 어댑터 `view(game, pid) → {pub, priv}` 가 있으면 방송엔 `pub` 만, `priv` 는 `h{e:'priv', to:pid}` 로 그 사람 `dpk.dh` 에 ECIES(봉인 모드와 무관하게 항상). 마작 좌석별 ECDH 를 커널로 승격.

#### 6.0.2 순서·유실·스냅샷 폭풍 제거
- 카운터 2개: 상태 스트림 `s`(state/delta/roster/phase/fair/switch/kicked/close/priv/welcome/deny 등 **틱·하트비트 외 전부**), 틱 스트림 `t`(best-effort). 재전송은 **같은 s·같은 id**.
- 모든 봉투가 전원에게 배달되므로(to 가 있어도) 멤버는 s 를 빠짐없이 본다 → 가짜 gap 없음.
- 방장 하트비트가 `hs`(현재 s) 를 실어 꼬리 유실도 감지.
- gap 감지 → 250ms 기다렸다가(뒤늦은 도착 흡수) `g{e:'snap_req', d:{have:s}}`.
- 방장 응답 뭉침: 게스트당 2초에 1번, 250ms 안에 2명 이상 요청이면 `to` 없이 전체 `state` 1번.
- 틱에는 gap 복구 없음. draw 어댑터는 틱 자체를 거의 안 씀(§6.1).

#### 6.0.3 하트비트 1종 (+ 시계·RTT·편승)
- 방장 `h{e:'hb', d:{t:방장now, hs, vis, ec:{pid:[t0,t1]}, w?, bd?}}`
  - 주기: 멤버 1명 이상이면 **5초**, 혼자면 15초. 방장 탭이 숨겨지기 직전 `vis:'hidden'` 즉시 1회.
  - `ec` = 각 게스트의 마지막 hb 송신시각 t0 와 방장 수신시각 t1(에코) → 게스트가 NTP 식 오프셋·RTT 계산(별도 ping/pong 제거).
  - `w` = draw 목격 집계(§6.1.7), `bd` = race 순위판(§6.5).
- 게스트 `g{e:'hb', d:{t0, vis, w?, sc?}}`
  - 주기: 대기실·관전 **20초**, 플레이 중 좌석 보유자 **8초**, 숨김 30초. `visibilitychange` 즉시 1회(vis 변경), `pagehide` 에 `bye`.
  - `w` = 목격 해시, `sc` = 레이스 진행 점수(편승 — 추가 메시지 0).
- 오프셋: 최근 7 샘플 중 RTT 하위 3개의 오프셋 중앙값(NTP 필터). `room.clock()` = `Date.now()+offset`.
- **게임별 자체 하트비트 금지**(윷·프리즘·마작·리버시 hb 제거). 게임은 `room.on('roster')` 의 `c` 로 연결 상태를 읽는다.
- 소켓: 방 페이지의 supabase 클라이언트는 `realtime:{worker:true}`(workerUrl 지원 확인됨)로 백그라운드 스로틀에도 소켓 하트비트 유지 — P1 에서 실측 후 채택(안 되면 기존 item 18 keep-alive).

#### 6.0.4 연결 판정 (방장이 명단에 기록)
| 상황 | away | offline | 조치 |
|---|---|---|---|
| 대기실 | `vis:hidden` 수신 즉시 | 무소식 **45초**(숨김 90초) | 120초 뒤 명단 제거(좌석 기억은 `mem`) |
| 플레이(좌석) | 즉시 | 무소식 **20초** 또는 `bye` | 그 사람 차례면 8초 뒤 봇 대행, 좌석은 **예약 유지** |
| 관전 | – | 60초 | 제거 |

#### 6.0.5 방장 감시(게스트 워치독)
- 마지막 방장 메시지(아무거나) 경과: **12초** → 노랑 "확인 중" + `snap_req` 1회, **20초** → 빨강 "방장 연결 끊김", **30초** → 승계 가능 게임이면 승계(§6.0.6), 아니면 5분까지 대기 후 "방이 끝났어요".
- 방장이 `vis:hidden` 을 보냈으면 "방장 잠시 다른 앱" 띠, 임계값 2배.
- 방장 자신의 연결: 송신에 `ack` 실패·채널 `CHANNEL_ERROR` → HUD 점 빨강 "재연결 중", 복구 후 전체 `state` 재방송.

#### 6.0.6 방장 새로고침 · 승계
- **새로고침/탭 복원/게임 전환**: 커널이 상태 변경마다(1초 스로틀) `sessionStorage.lpr_host_<code>` 에 `{S, bans, fairSecrets}` 저장, 방 키는 IndexedDB. `resume()` 이 Web Lock 획득 후 **같은 ep 계열의 새 ep**(> 이전)로 재개, 곧바로 전체 `state` 방송. 진행 중 추첨의 `hostSeed`·체인 비밀도 저장되므로 공개가 이어진다. → 7개 게임의 "라운드 중 복원 미연결"이 커널에서 일괄 해결.
- **승계(방장 영영 사라짐)** — 어댑터 `migratable:true`(숨은 정보 없음) 게임만:
  1. 방장이 서명한 최신 명단의 `succ`(합류 순, online 좌석 우선) 첫 번째 online 멤버가 후보. 모든 기기가 같은 규칙으로 같은 후보를 계산.
  2. 후보가 `g{e:'takeover', d:{ep2, fromSeq, stHash}}` 를 **자기 기기 키로 서명**해 방송. 멤버는 "서명자 pid 가 방장 서명 명단의 succ 에 있고, 앞 순번이 전부 offline" 이면 수락. 새 방장 키 = 후보의 기기 키(`dpk`)로 이후 `h` 서명.
  3. 후보보다 높은 seq 를 가진 멤버는 `g{e:'state_offer'}` → 후보가 최고 seq 채택.
  4. 새로 코드만 들고 오는 사람을 위해 새 방장의 `hello` 에 `chain:[원방장 rpk, 원방장 서명 succ 명단, 새 방장 dpk]` 동봉 → 코드 지문은 원방장 키로 검증, 승계는 서명 체인으로 검증.
  5. 원방장이 돌아오면 hello 의 chain 을 보고 게스트로 합류(되찾기 없음 — 뒤집기 혼란 방지).
- 숨은 정보 게임(마작·풍선 진행 중 라운드): 승계 없음, 최대 5분 대기 → 무효 처리.

#### 6.0.7 의도(intent) 계약 — 모든 멀티 게임
- `room.intent(a, data)` → `g{e:'intent', p, c, d:{a, x:data, es:expectSeq}}`.
- 방장: `(p,c)` 멱등 캐시(게스트당 최근 32개) → 결과 재발송. `es` 가 있고 `S.seq≠es` 이며 어댑터가 `commutes(a)` 를 false 로 주면 `h{e:'nack', to:p, d:{c, seq}}` → 게스트는 상태 재동기 후 재시도 여부 UI.
- 수락 → `setState` → 새 seq 방송(수락 응답 겸). 게스트 쪽 낙관 반영은 어댑터 선택(윷 lbPend 식), seq 도착 시 교정.
- 토큰 버킷 10/s·버스트 20 유지.

### 6.1 draw 어댑터 — 같이 보기 + 공정 추첨 (`lpFair.js`)
대상: roulette · team · ladder · dice · lotto · bingo · car-racing · glory-racing (balloon 은 turn+chain, §6.2.5).

#### 6.1.1 원칙: 결과 먼저, 연출은 결과로 향한다
- 결과는 `outcome(params, rng)` **순수 함수**(정수 연산만 — 기기 간 부동소수 차이 제거)로 먼저 확정. 애니메이션은 그 결과에 도착하도록 그린다(팀 드롭머신 "결과 미리 확정·공만 유도"와 같은 원칙).
- 모든 기기가 같은 시드로 **스스로** 같은 결과·같은 연출을 만든다 → 20Hz 틱 스트림 불필요(예산 −90%), 네트워크가 끊겨도 결과 동일, 나중에 링크로 재현·검증.
- 연출 함수는 시간의 순수 함수 `frameAt(tMs)` 로 작성(roulette 각도 = 감속 곡선 closed-form) → 늦게 온 사람·백그라운드 복귀자는 경과 시간으로 바로 그 장면부터.

#### 6.1.2 `LpFair.draw` 프로토콜 (1회 추첨, 모든 draw 게임 공통)
```
방장 [뽑기] ─ params 동결(이름 목록·옵션)  hostSeed=rand32  C=H("lpf1-c"|code|round|H(params)|hostSeed)
  h{e:'fair', d:{k:'commit', round, C, ph:H(params), params, win:1500}}         (서명)
게스트(좌석/멤버, online) 자동: n_i=rand16
  g{e:'fair', d:{k:'c', round, h:H("lpf1-n"|round|pid|n_i)}}                    (서명)
  ── 전원 커밋 또는 1.5초 ──  방장: 커밋 목록 L 확정 →
  h{e:'fair', d:{k:'lock', round, L:[pid…]}}
게스트(L 에 든 사람): g{e:'fair', d:{k:'r', round, n:n_i}}
  ── L 전원 공개 또는 1.5초 ──
  h{e:'fair', d:{k:'reveal', round, hostSeed, N:{pid:n_i}, startAt: 방장now+900}}
모두: C 재계산 검증 · 각 H(n_i) 가 커밋과 일치 검증 · 내 n 포함 확인
      seed = H("lpf1-s"|C|hostSeed|sort(pid‖n_i))
      result = outcome(params, rng(seed,'main'))
      startAt(방장 시계) 에 연출 시작 → 같은 순간 같은 장면
```
- **방장 단독 조작 불가**: hostSeed 는 참가자 엔트로피를 보기 전에 커밋됨. **게스트 단독·방장-공모 게스트 조작 불가**: 게스트는 남의 n 을 보기 전에 커밋(2단계).
- **중단 공격**: 커밋 후 공개를 안 하면 결과를 보고 버리는 것 → 커밋된 라운드가 3초 내 공개되지 않으면 모든 화면에 "⚠ 추첨 #3 취소됨"이 남고, 결과 배지·인증서에 "이 방 추첨 5회 · 취소 1회"가 기록된다. 게스트가 커밋 후 공개 안 하면 그 라운드 무효·자동 재시도, 그 사람은 다음 라운드에서 제외 표시.
- 혼자일 때(게스트 0): 커밋·공개 즉시(연출 지연 0), 배지 "혼자 뽑기"(검증 문구 없음).
- 체감: 커밋~공개 ≈ 0.4~1.5초 → **"모두의 행운 섞는 중"** 연출(참가자 아바타에서 코인이 가운데 항아리로 날아감)로 숨김. 시작 버튼 반응은 즉시.

#### 6.1.3 결정적 RNG
- `LpFair.rng(seed, label)` = SHA-256(seed‖label) 32바이트 → **sfc32** 상태 4워드(정수 연산만). 메서드 `u32() · int(n)`(거부 샘플링, 편향 0) `· float() · pick(a) · shuffle(a)`(Fisher–Yates).
- 스트림 분리: `'main'`(결과), `'fx'`(연출 흔들림), `'card:'+pid` 등 — SZX 의 스트림 분리 교훈.
- 부동소수 결정성: 결과 계산에 `Math.sin/cos/exp/pow` 금지(엔진마다 다를 수 있음). 연출에는 허용(결과와 무관).

#### 6.1.4 동시 출발
- `startAt` 은 방장 시계 기준. 멤버는 `startAt - offset` 로컬 시각에 시작(오프셋은 §6.0.3). 목표 오차 ±50ms. 늦게 받은 사람은 `frameAt(now - startAt)` 로 따라잡기.

#### 6.1.5 결과 배지 · 목격 집계
- 각 기기가 결과 해시 `rh = H(result)` 앞 4바이트를 다음 hb 의 `w:{round, rh}` 로 실어 보냄(추가 메시지 0). 방장 hb `w:{round, ok:5, bad:0}` 로 집계 방송.
- 배지: `✓ 공정 · 5명 확인` (불일치가 있으면 `⚠ 1명 화면 다름` — 버그 탐지 겸용). 탭하면 검증 시트.
- 틱 모드 게임(car-racing·glory-racing, §6.1.8)은 `✓ 공정 시드` 로 표기(재현이 아니라 시드 공정성만 보장함을 정직하게).

#### 6.1.6 자가검증 결과 링크 `#cert=`
- 결과 공유 = `/games/<id>/#cert=<base64url(deflate-raw(JSON))>`(CompressionStream, 없으면 무압축). fragment 라 서버에 안 감.
- JSON: `{v:1, g, code, round, params, C, hostSeed, N:{pid:n}, H:{pid:h}, sigs:{pid:게스트 커밋 서명}, rpk, rsig:(reveal 봉투 서명), res, t, stats:{draws, aborts}}` — 8인 기준 ~1.5KB → URL ~2KB.
- 페이지가 `#cert` 를 보면 **검증 모드**: 서명·커밋·시드 재계산 → `outcome` 재실행 → 결과 일치면 연출 다시 재생 + `✓ 검증됨 · 민지 당첨` / 한 글자라도 바뀌면 `✗ 위조된 결과`. 서버 불필요. 기존 `?winner=` 는 솔로 공유용으로 유지(표시용).
- 원문 방송(`reveal`)을 그대로 담으므로 방장 서명 = "이 방 방장이 이 결과를 공표함", 게스트 커밋 서명 = "이 사람들이 참여함".

#### 6.1.7 공개 비컨(선택, 기본 OFF)
- `🌐 공개 비컨` 옵션: 커밋 시 방장이 미래 drand quicknet 라운드 R(현재+2, ~6초 뒤)을 지정 → seed 에 `drand(R).randomness` 추가 혼합. `api.drand.sh` 와 `drand.cloudflare.com` 두 곳에서 받아 일치 확인(둘 다 CORS `*` 실측). BLS 서명 검증은 후속(`@noble/curves` 벤더링 ~40KB). 인증서에 R 기록 → 제3자 재검증.

#### 6.1.8 게임별 draw 매핑
| 게임 | params | outcome | 연출 | 비고 |
|---|---|---|---|---|
| roulette | 칸 목록·가중치 | 당첨 칸 idx + 칸 내 위치 u | 감속 곡선 `angle(t)` 으로 목표각 도착(closed-form), 플래퍼는 fx 스트림 | 틱 방송 제거. 늦참 = `frameAt` |
| team | 명단·팀 수·옵션 | 셔플 → drawQueue | 플링코 공은 큐의 팀으로 유도(기존) | `TD.catchUp` 유지 |
| ladder | 세로줄 수·이름·결과 | rung 배치 → 매핑(전단사) | 기존 트레이서 | 게스트 재생성 금지 규칙 → "시드로 재생성"으로 교체 |
| dice | 개수·면·모드 | 눈 목록. 모드 `모두 굴리기` = 멤버마다 `rng(seed,'die:'+pid)` → 최저/최고 표시 | 3D 굴림 도착값 강제 | **방 신규 배선** |
| lotto | 범위·개수·보너스 | Fisher–Yates 앞 k | 드럼 물리는 각자 로컬 장식, 흡입되는 공 라벨을 결과 순서로 강제 | capture 스트림 제거 |
| bingo | 판 크기·자동 간격 | **세션형**: 시작 시 fair 로 G(공동 시드) 확정 → 카드 = `rng(G,'card:'+pid)`, 호출 순서는 **LpFair.chain**(§6.2.5) — 방장만 다음 번호를 알고 끝나면 전체 검증 | 기존 케이지 | 승자 = 방장이 카드·호출 기록으로 검증해 서명 방송, 누구나 재검증 가능 → `bingo_winners` DB·전용 채널 불필요 |
| car-racing | 참가자·트랙 옵션 | **틱 모드**: seed 로 방장 RNG 초기화(`Math.random` 대신 `rng(seed,'sim')`), 방장 물리+20Hz 틱(10Hz 로 하향 + 보간) | 기존 LPFX | 결과는 방장 서명. 결과-먼저 "감독" 전환은 운영자 결정 |
| glory-racing | 참가자 | car-racing 과 동일(틱 모드) | 기존 | supabase 지연 로드 필요, **방 신규 배선** |

- draw 대기실 = 띠형. `entrants:'host'|'members'`: 방장이 `👥 멤버로 채우기` 를 켜면 명단이 추첨 목록이 된다(초대받은 사람이 곧 참가자). `✋ 내 이름 넣기` = 게스트 의도 `{a:'entry', name}`.

### 6.2 turn 어댑터 (`lpRoomsTurn.js`) — 윷을 일반화
대상: yut · ludo · reversi · prism-hex · mahjong-tw · balloon.

```js
LpRooms.adapter({
  gameId:'ludo', kind:'turn', seats:[2,4], max:8, lateJoin:'takeBot',
  picks:[{key:'color', options:['r','g','b','y'], unique:true, botYield:true}],
  options:[{key:'turnSec', values:[15,30,60], def:30}],
  bots:true, hiddenInfo:false, migratable:true, delta:false,
  host:{
    init(seats, opts, fx)           → game          // fx = {rng, chain} 공정성 도구
    legal(game, seat)               → [a…]          // 봇·타임아웃·UI 공용
    apply(game, seat, a, fx)        → {game, log} | {reject:'illegal'}
    timeout(game, seat, fx)         → a              // 기본: legal 에서 봇 선택
    bot(game, seat, fx)             → a
    next(game)                      → seat | null(끝) ;  result(game) → {rank:[seat…]}
    view?(game, pid)                → {pub, priv}   // 숨은 정보
  },
  client:{ render(S, me), onLobby?(S), onResult?(S) }
})
```
#### 6.2.1 턴 · 마감
- `S.turn = {seat, n, deadline}` — deadline 은 **방장 시계** 절대시각(윷의 "각자 연출 끝부터 세기" 대신 프리즘/퀴즈 방식 채택 → 기기 간 차이 제거). 연출 시간은 `deadline = now + animMs + turnSec*1000` 로 흡수.
- 방장은 `LpPhaseTimer` 로 deadline+500ms 에 `timeout` 실행(백그라운드 복귀 시 catchUp). 연속 2회 초과 → `afk` → 봇 대행, `I'm back` 의도 또는 직접 행동으로 해제(윷 규칙 유지).
- 끊긴 좌석(offline) 차례 → 8초 뒤 봇 대행(마감보다 먼저).

#### 6.2.2 자리 보호(자리 강탈 금지)
- 좌석 소유 = pid(서명). 좌석 상태: `human(online|away|offline)` · `reserved`(offline 사람 자리, 봇이 대신 둠) · `bot` · `off`.
- 다른 사람의 좌석 요청은 `bot`/`off` 좌석만. `reserved` 는 **방장이 명시적으로 "자리 넘기기"**(원주인 offline ≥ 60초일 때만 버튼 활성) 해야 풀린다. 원주인 복귀 = 같은 pid → 자동 복귀(봇 해제).
- 리버시 21초 자리 강탈·루도 닉네임 소유 문제 해결.

#### 6.2.3 늦참
- `takeBot`: 관전자가 봇 좌석 탭 → `{a:'claim', seat}` → 방장 자동 승인(게임이 `canClaim` 거부 가능) → 다음 자기 차례부터.
- `spectate`(리버시): 관전만, 한 판 끝나면 대기실에서 좌석 선택.

#### 6.2.4 다시 하기
- 방장 `한 판 더` → `toLobby()`(좌석·선택 유지, 준비 초기화). 리버시식 "누구나 즉시 리매치" 제거 → 대기실 준비 게이트로 합의.

#### 6.2.5 공정성 in 턴제 — `LpFair.chain` · `LpFair.deal`
문제: 방장도 플레이어인데 주사위·윷·파열점을 방장 기기가 정한다(T3). 시드를 미리 공개하면 모두가 미래를 알고, 숨기면 방장만 안다.
- **chain(연속 사건)**: 게임 시작 때 방장이 해시체인 `s_K → … → s_0`(s_{i-1}=H(s_i)) 생성, `s_0` 을 `fair` 커밋으로 공개. 사건 i(굴리기·펌프·빙고 호출)의 난수 = `H("lpf1-e"|s_i|n_i)` 이고:
  - `n_i` = **그 순간 s_i 를 모르는 사람**이 새로 낸 엔트로피. 게스트가 굴리면 그 게스트의 의도에 `n` 동봉(추가 메시지 0). 방장이 굴리는 사건이 "선택"을 동반하면(풍선 펌프 = 할지 말지 선택) 다음 차례 게스트 기기가 자동 응답 `g{e:'fair',k:'n'}`(1통) — 방장은 결정을 먼저 방송해야 n 을 받는다. "선택 없는 강제 사건"(윷·루도에서 방장 자기 차례 굴리기는 필수)은 마지막 게스트 의도의 n 을 써도 이득이 없다(굴릴지 말지 선택권이 없으므로).
  - 방장이 공개하는 `s_i` 는 `H(s_i)=s_{i-1}` 로 누구나 즉시 검증 → 방장이 사건 결과를 바꿀 수 없다. 게스트는 `s_i` 를 모르고 n 을 내므로 편향 불가.
  - 끝나면 전체 체인·n 목록이 인증서/로그에 남아 사후 검증.
- **deal(숨김 배분)**: 마작 패 산·빙고 카드처럼 처음에 한 번 섞는 것. `wall = shuffle(rng(H(hostSeed|G)))`, G = §6.1.2 로 모은 게스트 공동 엔트로피(방장 커밋 후 수집) → 방장은 G 를 보고 나서야 결과를 알게 되어 **패를 고를 수 없고**, 게스트는 hostSeed 를 몰라 산을 모른다. 판이 끝나면 hostSeed 공개 → 모두 "산을 조작하지 않았음" 검증. 한계: 방장은 진행 중 모든 패를 볼 수 있다 → 대기실에 `🀄 방장 기기가 패를 나눠요` 아이콘 고지(운영자 결정: 이대로 수용 권장).
- 적용: yut 던지기·ludo 주사위 = chain / balloon 파열 = chain + 위험률 변환 / mahjong-tw = deal / bingo 호출 = chain(번호 = 남은 공 중 `int(남은 수)`) + 카드 = deal(G 공개 시 카드도 공개 — 빙고는 결정이 없는 게임이라 무해).
- 풍선 위험률: 기존 파열점 분포(평균 12·SD 6·첫 펌프 2%)를 누적분포 F 로 두고 k번째 펌프의 조건부 확률 `h(k) = (F(k)-F(k-1))/(1-F(k-1))`, 펌프마다 `u_i < h(k)` 면 파열 → **분포 동일 유지**, "크기·게이지는 단서 아님" 원칙도 유지.

#### 6.2.6 게임별 turn 매핑
| 게임 | 좌석 | picks | 숨은 정보 | 승계 | 특이 |
|---|---|---|---|---|---|
| yut | 2–4 | 캐릭터(고유, 봇 양보) | 없음 | ✅ | 레퍼런스 포팅: LB·lbPick·lbCanStart·toLobby·kick → 커널/대기실 공용으로, 윷 규칙·연출 유지. 게임 hb 제거 |
| ludo | 2–4 | 색(고유) | 없음 | ✅ | 닉네임 소유 → pid 소유, `confirm()` 교체, 턴 표시 추가 |
| reversi | 2 + 관전 | 흑/백 | 없음 | ✅ | `lp_rv_cid` 탭 신원 폐지 → pid, 턴 시간 추가(옵션 끔/30/60), 자리 보호 |
| prism-hex | 2–6 | 자리 | 없음 | ✅ | hb·리스너 누수 제거, deadline 은 이미 방장 시각(S.tl) → 커널 turn 으로 |
| mahjong-tw | 4 | – | ✅ 손패 | ❌ | 좌석 ECDH → 커널 `view/priv`, `bye` 평문 문제 → 서명으로 해결, deal 검증, 울기 창 CLAIM_MS 는 어댑터 내부 부타이머 |
| balloon | 2–8 | – | ✅ 체인 비밀 | ❌(라운드 중) | **방 신규 배선**, 턴제 펌프, chain |

### 6.3 realtime 어댑터
#### 6.3.1 구미 체인(1:1 + 관전)
- 대칭 결정론(같은 조각 시드) + 기존 **순번·ACK·재전송 창 스트림 유지**, 전송만 커널 `x` 이벤트로(방장→`h{e:'x'}`, 게스트→`g{e:'x'}`, 둘 다 서명).
- 조각 시드 = `LpFair.draw` 로 만든 seed(`rng(seed,'pieces')`) → 양쪽 공정.
- 끊김: 9초 기권 폐지 → **양쪽 일시정지 "상대 재연결 중 25s"**(방장 시계 deadline), 넘으면 방장이 결과 확정 `h{e:'x',k:'result'}`(서명) → 양쪽이 같은 결과(재현 10 "둘 다 승" 해결). 방장 쪽이 끊기면 게스트 화면이 동일 규칙으로 대기 후 "방장 연결 끊김".
- 관전: 선택 시 관전자는 양쪽 `atk`·보드 요약을 1Hz `h{e:'x',k:'spec'}` 로 시청(관전자 있을 때만 송신).
- `tryResumeHost` 대응은 커널 저장으로 자동. `rrect` 음수 반지름 클램프(P0).

#### 6.3.2 Space-Z SZX(최대 8, 협동 2) — 브리지(엔진 불변)
- 결정: **SZX 엔진(시드 결정론·WebRTC 메시·P2P 위치·도전장)은 그대로**(운영자 핵심 시스템). 대기실·초대·명단만 Rooms 로.
- 흐름: Rooms 방(gameId `dodge`, kind `realtime`, adapter `szx`) 대기실에서 준비 → 방장 시작 → `h{e:'x', d:{k:'szx', code6: 숫자6(H(code|round) 파생), seed, mode:'race'|'coop'}}` → 모든 멤버가 SZX 모듈의 기존 참가 함수를 그 숫자 코드·닉네임으로 **조용히 호출**(SZX 쪽에 `SZX.joinSilent({code,nick,seed})` 공개 1개만 추가). 결과는 SZX 가 모으고, 끝나면 SZX 결과를 Rooms 결과 화면에 전달(`SZX.onFinish(cb)`).
- 기존 단독 SZX 입장 경로(숫자 코드·도전장 링크)는 그대로 유지·resolve 로 라우팅.
- 로그인 1:1 PvP(스택 C): 변경 없음, 진입점 유지(운영자 결정).
- 후속(선택): SZX 제어 메시지를 Rooms 채널로 합쳐 연결 2개 → 1개(예산 소폭 개선).

### 6.4 db 어댑터 — 라이브 퀴즈 브리지(엔진 불변)
- 퀴즈 DB 진행 엔진(qlive_* RPC, 폴링+nudge, 멱등 답안)은 **그대로**. 숫자 코드도 유지(서버 발급, SQL 변경 불필요).
- Rooms 방에서 방장이 퀴즈로 전환 → 퀴즈 페이지 방장이 평소처럼 `qlive_create` → `h{e:'x', d:{k:'qlive', qcode}}` → 멤버 페이지가 `qlive_join(qcode, nick=Rooms 닉, av)` 자동 호출(퀴즈의 autoRejoin 경로 재사용). 퀴즈 화면은 기존 UI, Rooms HUD 만 위에(퀴즈의 `body.qlive-in` 숨김 규칙에 HUD 위치 예외 추가).
- 200명 교실형은 기존 퀴즈 단독 경로(QR·숫자 코드) — Rooms 정원 12 를 넘으므로.
- 홈/허브 resolve 가 숫자 코드를 퀴즈로 보냄(현재 불가 문제 해결).

### 6.5 race 어댑터 (`lpRoomsRace.js`) — 솔로 아케이드 같은 시드 대결
대상: tetris · mahjong-solitaire · brick · burger · starship-lander · lucky-merge (후속: snake · pacman · bubble 은 시드화 후).
```js
LpRooms.adapter({ gameId:'tetris', kind:'race', seats:[2,8], max:12, lateJoin:'nextRound',
  options:[{key:'mode', values:['sprint40','score120'], def:'score120'}],
  race:{ metric:'score'|'time', dir:'desc'|'asc', durationS?:120,
         start(seed, opts) /* 게임을 시드로 새 판 시작 */, progress() → number, final() → {v, t, dig} }
})
```
- 시작: `LpFair.draw` 로 seed(모두 같은 판) → `startAt` 동시 카운트다운 3-2-1(LpChrome 접힘).
- 진행: 게임이 `race.progress()` 제공 → 커널이 **게스트 hb 의 `sc` 에 편승**(8초), 방장 hb 의 `bd:[[pid,v,alive]…]` 로 순위판(5초) → **추가 메시지 0**. HUD 에 미니 순위(내 등수·1등 점수).
- 종료: 각자 `g{e:'x', d:{k:'final', v, t, dig}}`(서명, 1통), `dig` = 입력 로그 해시(향후 리플레이 검증용, 지금은 기록만). 방장이 모아 `h{e:'x',k:'board'}` 최종 순위(서명) → 결과 화면 + `#cert`(시드·점수표; 점수는 자기 신고임을 배지 "기록 신고"로 표기 — 보상 붙이지 않음).
- 백그라운드 = 그 순간 기록으로 종료(SZX 규칙 동일, 시간만 흐르는 구멍 차단). `LpAutoPause` 는 레이스 중 비활성.
- 게임 쪽 요구: `?seed=` 또는 `start(seed)` 로 결정적 판 생성(tetris 7-백 시드화 필요, 나머지 시드 보유 — 감사 §7).

### 6.6 전 게임 매핑 (최종)
| 게임 | kind | lateJoin | 승계 | 패키지 | 현재 → 변화 |
|---|---|---|---|---|---|
| roulette | draw | anytime | ✅ | P3a | 틱 → 시드 재생 |
| team | draw | anytime | ✅ | P3a | 방장 큐 → 시드 큐 |
| ladder | draw | anytime | ✅ | P3a | 방장 토폴로지 → 시드 |
| dice | draw | anytime | ✅ | P3a | **방 없음 → 신규** |
| lotto | draw | anytime | ✅ | P3b | capture 스트림 → 시드 |
| bingo | draw(세션)+chain | anytime | ❌(진행 중) | P3b | DB 승자 → 서명 검증 |
| car-racing | draw(틱) | anytime | ❌(레이스 중) | P3b | 시드 공정만 추가 |
| glory-racing | draw(틱) | anytime | ❌(레이스 중) | P3b | **신규** |
| balloon | turn+chain | nextRound | ❌(라운드 중) | P3b | **신규** |
| yut | turn | takeBot | ✅ | P4 | 레퍼런스 포팅 |
| ludo | turn+chain | takeBot | ✅ | P4 | |
| reversi | turn | spectate | ✅ | P4 | |
| prism-hex | turn | takeBot | ✅ | P4 | |
| mahjong-tw | turn+deal | takeBot | ❌ | P4 | |
| gummy | realtime | nextRound | ❌ | P4 | |
| dodge(SZX) | realtime-bridge | nextRound | (SZX 자체) | P5 | |
| quiz | db-bridge | anytime | (DB 자체) | P5 | |
| tetris·mahjong-solitaire·brick·burger·starship-lander·lucky-merge | race | nextRound | ✅(대기실) | P5 | **신규** |
| snake·pacman·bubble | race(후속) | – | – | 후속 | 시드화 필요 |
| orbit(DELTA-V) | 없음(도전 링크만) | – | – | – | – |

---

## 7. 메시지 예산 (Supabase 과금 = 방송 1건당 발신 1 + 수신자 수 = 방 인원 N)

### 7.1 주기 표 (v2)
| 발신 | 대기실 | 플레이 | 관전자 |
|---|---|---|---|
| 방장 hb | 5s | 5s | – |
| 게스트 hb | 20s | 8s(좌석) | 20s |
| 방장 ping / 게스트 pong / 게임 hb | **폐지** | **폐지** | – |
| 순위·목격 | hb 편승(0) | hb 편승(0) | – |
| 명단 | 변경 시(100ms 뭉침) | 변경 시 | – |

### 7.2 수치 (msg/s = Σ 발신률 × N)
| 시나리오 | 현재 v1 | v2 |
|---|---|---|
| 대기 4인 | 10.8 (감사 실측 계산) | 방장 0.2×4=0.8 + 게스트 3×0.05×4=0.6 → **1.4** |
| 대기 8인 | ~40 (N² 경향) | 0.2×8=1.6 + 7×0.05×8=2.8 → **4.4** |
| 턴제 4인 플레이(5초당 의도1+상태1) | ~13 | hb 0.8+3×0.125×4=1.5 + 게임 0.4×4=1.6 → **3.9** |
| 레이스 8인 | – | 1.6 + 7×0.125×8=7.0 + 0(편승) → **8.6** |
| 8인 룰렛 1회(10s 스핀) | 틱 200×8=1,600 + 폭풍 8×3×8=192 ≈ **1,800 msg** | 커밋1+c7+잠금1+r7+공개1+결과재전송2 = 19×8 ≈ **152 msg** |
| 카레이싱 8인 30s | 600×8=4,800 | 10Hz: 300×8=2,400 (+시드 150) |

### 7.3 한도 대비
- 무료(초당 100·월 200만·동시 연결 200): 동시 턴제 4인 방 **~25개**(현재 ~9), 월 **~250 방-세션**(4인·30분·추첨 10회 ≈ 8k msg) — 현재 ~85.
- 메모리상 프로젝트는 **Pro**(초당 500·월 500만·연결 500)일 수 있다 → 여유 5배. 설계는 무료 기준으로 맞춘다(운영자 확인 항목).
- 방 정원 12 는 예산에서 나온 값: 12인 플레이 hb = 0.2×12 + 11×0.125×12 = 18.9 msg/s — 방 5개면 무료 한도.
- 가드: 방장 커널이 1분 이동평균 추정 msg/s(자기 발신×N + 수신 수)를 계산, 방당 25 msg/s 를 넘으면 디버그 경고 + 게스트 hb 주기 자동 1.5배.

---

## 8. API · 메시지 레퍼런스

### 8.1 `window.LpRooms` (lpRoomsCore.js)
```ts
ready(): Promise<void>
identity(): Promise<{pid, tid}>                       // 키 준비 포함
profile: { get(): {nick, av}; set(p): void }
create(o:{gameId, opts?, pinReq?:boolean, pin?:string, appr?:boolean, max?:number, sealed?:boolean}): Promise<Room>
join(o:{code, inv?:{fp,tok}, pin?, want?:'play'|'watch'}): Promise<Room>   // 거절 시 Error{reason}
resolve(input:string): Promise<{kind, code, gameId?, url?}>
parseInvite(hrefOrText:string): {code, inv?} | null
resume(): Promise<Room|null>                         // 이 탭의 방장/멤버 세션 복구(게임 전환·새로고침)
current(): Room|null
adapter(spec): void                                  // 게임이 1회 등록
on(ev:'room'|'left', cb): () => void
```
### 8.2 `Room`
```ts
code; gameId; isHost; me:{pid, role, seat}; ep
roster(): Member[];  state(): S;  clock(): number /* 방장 시계 ms */
on(ev:'roster'|'state'|'phase'|'priv'|'fair'|'x'|'react'|'hostlost'|'hostback'|'takeover'|'kicked'|'closed'|'detached', cb): () => void
intent(a:string, x?:any, o?:{expectSeq?:number}): Promise<{ok:true, seq}|{ok:false, reason}>
x(k:string, d:any): void                             // 어댑터 전용 부가 스트림(서명)
react(i:0..5): void;  leave(): void;  inviteUrl(): string
// 방장 전용
setState(fn:(S)=>void|S, o?:{full?:boolean}): number
onIntent(cb:(from:Member, a, x, ctx)=>void): void    // 커널 어댑터가 쓰면 게임은 직접 안 씀
sendTo(pid, e, d): void                              // ECIES 비공개
tick(d): void                                        // 틱 모드 전용(10–20Hz 상한)
start(o?:{countdownMs?:number}): void;  toLobby(): void;  switchGame(gameId): void
pause(): void;  resume(): void;  end(): void;  close(): void
kick(pid, o?:{ban?:boolean}): void;  unban(pid): void
lock(on:boolean): void;  approval(on:boolean): void;  approve(pid, ok:boolean): void
setPin(on:boolean, pin?:string): string|null;  setApproval(on:boolean): boolean   /* [+] 2026-09-30 — UI 방장 도구는 이것만 쓴다 */
transferHost(pid): void   /* 대기실·migratable 만 */;  rotateLink(): void
```
### 8.3 `window.LpFair` (lpFair.js)
```ts
draw(room, o:{params, window?:1500, beacon?:boolean}): Promise<{seed:Uint8Array, round, cert}>   // 방장 호출, 멤버는 room.on('fair')
rng(seed:Uint8Array, label:string): {u32(), int(n), float(), pick(a), shuffle(a)}
chain: { create(room, len): Promise<void>; event(i, n?): Promise<Uint8Array>; verify(s0, sI, i): boolean }
deal:  { begin(room): Promise<{hostSeed, G}>; reveal(room): void; verify(cert): boolean }
cert:  { encode(o): Promise<string>; decode(s): Promise<o>; verify(o, outcomeFn): Promise<{ok, res, why?}> }
badge(el:HTMLElement, info:{kind:'verified'|'seed'|'solo'|'mismatch', n, round, cert?}): void
beacon?: { at(round): Promise<{randomness, round}> }
```
### 8.4 이벤트 표 (채널 이벤트 `h`/`g` 안의 `e`)
**방장 `h`**: `hello` · `welcome`(to) · `deny`(to) · `roster` · `state` · `delta` · `priv`(to, ECIES) · `nack`(to) · `hb` · `tick`(t 카운터) · `phase`(starting/playing/paused/result + startAt) · `switch` · `kicked`(to) · `rekey`(to) · `close` · `fair`(k: commit|lock|reveal|abort|chain0|chainI|deal0|dealR) · `x`(어댑터: szx|qlive|board|result|spec|…) · `appr`(승인 대기 알림, 방장 화면 전용이지만 봉인됨)
**게스트 `g`**: `hello_req`(무서명) · `join` · `hb` · `bye` · `intent` · `snap_req` · `fair`(k: c|r|n) · `x` · `react` · `takeover` · `state_offer`
재전송 3회(200ms, 같은 s·id): `kicked` · `close` · `switch` · `phase` · `fair:reveal` · `x:result|board` · `welcome`.

### 8.5 저장 키
| 키 | 위치 | 내용 |
|---|---|---|
| `lp-id/keys` | IndexedDB | 기기 키(비추출) · 방장 방 키(`room:<code>`, 24h) |
| `lp_profile` | localStorage | 닉·아바타 |
| `lpr_recent` | localStorage | 최근 방 5개 |
| `lpr_host_<code>` | sessionStorage | 방장 상태 저장(S·bans·fair 비밀) |
| `lpr_active` | sessionStorage | 이 탭이 속한 방 `{code, inv, role, t}`(전환·새로고침 복귀) |
| `lpr_inv` | sessionStorage | fragment 에서 옮긴 초대 `{code, fp, tok}` |
| `lpr_ban_<code>` | localStorage+IDB+쿠키 | 차단 자기 표식 |

---

## 9. 구현 패키지 (병렬 안전 · 파일 소유 명시)

규칙: 각 패키지는 자기 파일만 수정. 공용 파일 수정이 필요하면 그 파일 소유 패키지에 요청(메인 에이전트가 조정). 워크트리 `C:\code\python\luckyplz_wt\<pkg>`, 병합 전 태그 `rooms-v2-<pkg>-pre`. `bump-cache.sh` 는 메인 에이전트가 통합 후 세션당 1회. 대형 커밋 사이 30분.

### P0 — v1 긴급 보강 (즉시, P1 과 병렬, 반나절)
소유: `public/js/lpRoom.js` · `lpHostCtl.js` · `lpMultiplayer.js` · `games/reversi` · `games/gummy`(아래 2줄 패치만)
1. `guest:action` 콜백 직전 `p.nickname=g.nickname; p.pid=g.pid`(명단 값으로 덮어쓰기) — 루도·윷·프리즘 사칭 차단(윷 `yut_tabpid` 테스트 경로는 포기 명시).
2. 잠긴 방: `_knownPids` 에 있는 pid 는 `rejoin` 플래그와 무관하게 통과.
3. seq: 틱은 별도 카운터(`_tickSeq`), `broadcastReliable` 재전송은 같은 `_seq` 재사용 → 스냅샷 폭풍 제거.
4. `join_request` 레이트리밋: bad_pin 10회/60s → 60s 쿨다운, 처리량 20/s.
5. 게스트 방장 감시: 마지막 방장 메시지 15s → `lp-room-host-lost` CustomEvent + 공용 띠(16개 언어), 복귀 시 `host-back`.
6. `lpHostCtl` DEFAULT_TEXTS 16개 언어.
7. `_validGames` 에서 `bubble` 제거, `host:ping` 4s→8s.
8. reversi: 좌석 소유자 offline 120초 미만이면 착석 불가. gummy: 기권 9s→25s + `rrect` 반지름·크기 `Math.max(0,…)` 클램프.
수용: 감사 재현 1·3·4·5·6(infra E1 사칭 일부·E5 lock-refresh·E7 폭풍)·ga 재현 1·4·5·8·10·11 이 실패→통과로 바뀜.

### P1 — 코어 (최우선, 1명, API 먼저 동결)
소유(신규): `public/js/lpRoomsCore.js` · `public/js/lpFair.js` · `public/js/lpGames.js` · `scripts/mp/`(하네스·릴레이·단위 테스트)
- 1일차: §8 API 를 `.d.ts` 주석 블록으로 파일 머리에 동결 → P2~P5 는 이 계약으로 병렬 착수(스텁 가능).
- 내용: 신원(IDB 키·pid·tid·Web Lock), 코드 파생·충돌 검사, 채널, 봉투 서명/검증·봉인·ECIES, 핸드셰이크·레이트리밋, 명단·연결 판정, hb·시계·편승 필드, gap/snap 뭉침, setState/delta/priv, 의도 멱등, 방장 저장/재개, 감시·승계, 게임 전환, resolve(v2+v1+qlive+szx). `lpFair`: rng(sfc32)·draw·chain·deal·cert·badge(배지 DOM 은 최소, 스타일은 P2 가 입힘).
- `realtime:{worker:true}` 실측 채택 여부 결정.
수용: §10 코어 시나리오 C1~C14 전부 통과, `fair` 단위 테스트(결정성·균일성·위조 탐지) 통과.

### P2 — 공통 UI · 허브 · 로더
소유: `public/js/lpRoomsUI.js`(신규) · `public/lobby/index.html` · `public/_redirects`(+`/r/*`) · `public/_headers`(noindex) · `public/js/siteFooter.js`(v2 로더) · `public/js/lpChrome.js`(👥) · `public/js/lpInApp.js`(`willEscape()` 공개 1줄) · `public/index.html`(참가 버튼 연결만) → `gen-lang-home.py` 재실행
- §4 전부, 16개 언어 표, 모바일 360px·데스크톱 확인, 인앱 확인창.
- 홈·허브 resolve 연결, 최근 방.
수용: U1~U10 시나리오, 360×740 스크린샷 검수(대기실 한 화면, 글 최소), 기존 부유 UI 가 v2 페이지에서 0개(HUD 1개).

### P3a — 추첨 1군: roulette · team · ladder · dice
소유: 각 `public/games/<id>/index.html` (게임당 1 에이전트 가능)
- draw 어댑터 등록, outcome 순수 함수 + `frameAt`, 틱 제거(룰렛), 띠형 대기실, `✋ 내 이름 넣기`, 결과 배지·`#cert` 검증 모드, dice 방 신규.
- 기존 v1 배선은 `if(v1)` 경로로 남김(롤백용), P6 에서 삭제.
### P3b — 추첨 2군: lotto · bingo · car-racing · glory-racing · balloon
- lotto 흡입 라벨 강제, bingo 세션+chain+서명 승자(DB·전용 채널 미사용), car-racing 시드 RNG 주입(69곳 `Math.random` → `R()` 래퍼, 풍경 LPFX 시드 유지) + 틱 10Hz, glory-racing 방 신규(supabase 지연 로드)+틱 모드, balloon turn+chain+위험률.
- car-racing 은 대형 파일(8.5k줄) — 게임 시뮬 하네스로 "시드 동일 → 결과 동일(같은 기기)" 확인, 되돌리기 금지 항목(메모리 car_racing_lpfx·game_sim_harness) 준수.
수용: D1~D12.

### P4 — 턴제 커널 + 보드게임 + 구미
소유: `public/js/lpRoomsTurn.js`(신규) · `games/yut` · `ludo` · `reversi` · `prism-hex` · `mahjong-tw` · `gummy` (P0 병합 후 착수)
- 순서: `lpRoomsTurn.js` + **yut 포팅(레퍼런스)** → 나머지 병렬. 윷 기능(캐릭터·준비·게이트·내보내기·턴 시간·afk 봇·중도 인계·재접속) 전부 보존, 게임 hb 제거.
수용: T1~T12.

### P5 — 레이스 커널 + 아케이드 + 브리지
소유: `public/js/lpRoomsRace.js`(신규) · `games/tetris` · `mahjong-solitaire` · `brick` · `burger` · `starship-lander` · `lucky-merge` · `games/dodge`(SZX 브리지 2함수만) · `games/quiz`(브리지)
- 아케이드는 `start(seed)`·`progress()`·`final()` 훅만 추가(게임 로직 불변). tetris 7-백 시드화.
- dodge 는 거대 파일 — `SZX.joinSilent`/`SZX.onFinish` 외 변경 금지(SAT 버튼 등 운영자 시스템 보존).
수용: R1~R8, B1~B4.

### P6 — 정리 · 소셜 연결 (전 게임 v2 후 14일 안정 시)
소유: `lpInvite.js` · `lpInviteButton.js` · `lpMultiplayer.js` · `lpHostCtl.js` · `lpRoom.js` · `lpPresence.js` · `CLAUDE.md` · 메모리
- 초대 = `room.inviteUrl()`(방 코드·토큰 포함) → 친구 초대 수락 시 바로 그 방. 이름표는 레지스트리.
- v2 페이지에선 lpMultiplayer/lpHostCtl/lpInviteButton 을 로드하지 않음(P2 로더에서 이미), P6 에서 v1 코드·파일 제거, 게임 파일의 v1 분기 삭제.
- (선택) lpPresence 에 "🎮 방에 있음(코드)" 상태 → 친구가 탭해 참가.
- CLAUDE.md 에 Rooms 절(되돌리기 금지 항목) 추가, 새 게임 체크리스트 갱신.

### P7 — Phase B (운영자 SQL 적용 후)
소유: `supabase/migrations/2026-10-XX-rooms-v2.sql` · `lpRoomsCore.js` Phase B 경로 · 로그인 표시 파일들(`is_anonymous` 처리)
- 로컬 검증: PGlite(퀴즈 때 방식) 로 RPC 30 시나리오 → 운영자 적용 → anon 키 종단 검증 스크립트.

### 의존 그래프
```
P0 ─────────────────────────────────▶ (병합) ─▶ P4
P1(1일차 API 동결) ─▶ P2 ─┐
                    ├▶ P3a ─┤
                    ├▶ P3b ─┼─▶ 통합·하네스 전체 ─▶ 게임별 플래그 ON ─▶ 14일 ─▶ P6
                    ├▶ P4 ──┤
                    └▶ P5 ──┘                                   P7(운영자 SQL 후 언제든)
```

---

## 10. 테스트 하네스 (`scripts/mp/`)

### 10.1 구성
- `relay.mjs`: 로컬 WebSocket 릴레이 + **supabase Realtime 호환 심**(`sb.channel(topic).on('broadcast',{event},cb).subscribe()/send/removeChannel` 만) — CDP `Fetch` 로 `/vendor/supabase.min.js` 요청을 심으로 교체. 지연·손실·재정렬·중복·분할(파티션) 주입, 모든 메시지 계수(과금 공식대로 발신+수신).
- `h.mjs`: 헤드리스 Edge 1개 + **브라우저 컨텍스트 N개 = 기기 N대**(저장소 분리, 기존 ga/h.mjs 패턴), `server.py` 자동 기동, REST/Auth/GA 차단, 가상 시계 옵션(백그라운드 탭 rAF 정지 대응), 종료 시 프로세스·프로필 삭제(디스크 정리 규칙).
- `fair.test.mjs`: Node(WebCrypto 내장) 단위 테스트.
- `smoke-live.mjs`: 실제 Supabase(코드 `ZZTEST*` 로 시작하는 고정 테스트 방은 v2 에선 파생 코드라 불가 → 테스트 키 시드 고정으로 `Z` 포함 코드가 나오게 생성) 소수 시나리오.
- 실행: `node scripts/mp/run.mjs [suite] [--live]` → 표 형식 결과 + 예산 리포트.

### 10.2 시나리오 (각 항목 = 합격 조건)
**코어 C**
- C1 방 생성·코드 형식(글자 포함)·지문 일치. C2 링크 참가(fp 고정) 3대. C3 코드 입력 참가 + **가짜 hello 동시 응답 → 중단**. C4 준비·시작·결과·대기실 복귀. C5 같은 기기 2탭 → "여기서 계속" 1회, 방장 onJoin 1회(E2 회귀 방지: 24초 동안 rejoin 0). C6 게스트 새로고침(잠긴 방) → 같은 좌석 복귀 ≤3초. C7 방장 새로고침(라운드 중) → 상태 동일·게스트 화면 연속. C8 방장 크래시(소켓만 사망) → 12s 노랑·20s 빨강·30s 승계(migratable)·명단 동일. C9 게임 전환 3회 → 전원 새 페이지·같은 코드·같은 좌석 기억. C10 추방·차단 → 재입장 거절, 저장소 삭제 후 재입장 = 승인 대기(자동 승인 모드). C11 PIN 켠 방 코드 입력 30회 오답 → 10회 뒤 `rate`, 60초 후 재허용. C12 네트워크 손실 10%·재정렬 → 최종 상태 해시 전원 일치, snap_req ≤ 손실 이벤트 수. C13 관전자·정원 12 초과 → `full`. C14 v1 코드 resolve·퀴즈 숫자 코드·SZX 숫자 코드 라우팅.
**스푸핑 S (원시 supabase 클라이언트로 채널에 직접 방송)**
- S1 서명 없는/틀린 `h:kicked`·`close`·`switch`·`state` → 전원 무시. S2 진짜 `kicked` 녹화 재생(옛 ep/s) → 무시. S3 게스트가 남의 pid 로 `intent`(서명 불일치) → 거절. S4 남의 `bye`/`leave` 위조 → 무시. S5 `switch` 에 미등록 gameId·URL 필드 → 이동 없음. S6 32KB 초과·깨진 JSON·초당 200건 폭주 → 드롭, 방장 UI 반응 유지(메인 스레드 블록 < 50ms). S7 봉인 모드: 코드만 아는 청취자가 받은 메시지에서 이름·결과 문자열 0건. S8 PIN/토큰이 채널 어디에도 평문으로 없음(전 메시지 grep).
**공정 D**
- D1 N=6 페이지, 추첨 50회 → 전 페이지 결과 해시 일치 50/50, 배지 `6명 확인`. D2 연출 동시성: 각 페이지 `startAt` 실시작 편차 ≤ 80ms(릴레이 지연 30~150ms 무작위). D3 방장이 공개를 보류 → 모든 화면 "취소됨" 표시·인증서 aborts=1. D4 게스트 커밋 후 미공개 → 라운드 재시도·표시. D5 인증서 위조(이름 1글자·res 변경·nonce 제거) → ✗. D6 인증서 원본 → ✓ + 재생 결과 동일(다른 브라우저 컨텍스트). D7 `fair.test`: 룰렛 n=2..12 각 10만 회 카이제곱 p>0.01, 팀·사다리·로또 순열 균일성, 같은 seed 10만 회 결과 동일(Node ↔ Edge 교차). D8 chain: 방장 자기 차례 결과를 바꾸려는 시도(다른 s_i) → 검증 실패 표시. D9 풍선 위험률 → 파열점 분포 평균 12±0.2·SD 6±0.2(10만 라운드). D10 빙고 승자 위조 클레임 → 방장 거절, 진짜 클레임 → 전원 재검증 ✓. D11 늦참(스핀 중) → 같은 장면부터·같은 결과. D12 카레이싱 같은 seed 같은 기기 2회 → 같은 순위.
**턴제 T**: T1 윷 전 기능 회귀(캐릭터·준비·게이트·kick/ban·턴·afk 봇·중도 인계). T2 사칭 재현(ga 1·4·5) 전부 실패. T3 리버시 21초 백그라운드 → 자리 유지, 관전자 착석 불가. T4 턴 마감 기기 간 표시 차 ≤ 300ms. T5 끊긴 좌석 8초 봇 대행·복귀 시 해제. T6 마작 손패: 다른 좌석·청취자 복호화 불가, 게임 후 deal 검증 ✓. T7 루도 주사위 chain 검증. T8 방장 크래시(마작) → 승계 없음·대기 안내. T9 방장 크래시(루도) → 승계·게임 계속. T10 구미 11초 백그라운드 → 일시정지·복귀·결과 일치(둘 다 승 재현 실패). T11 프리즘 hb/리스너 누수 0(방 5회 출입 후 interval 수 불변). T12 게임별 자체 hb 0건(메시지 로그).
**레이스 R**: R1 같은 seed 판 동일(첫 100 조각/벽돌 배치). R2 동시 출발 편차. R3 순위판 hb 편승(추가 메시지 0). R4 백그라운드 → 그 순간 기록 종료. R5 늦참 → 다음 판. R6~R8 게임별 훅.
**브리지 B**: B1 Rooms→퀴즈 자동 참가(목 PGlite 서버). B2 숫자 코드 resolve → 퀴즈. B3 Rooms→SZX 조용한 참가·결과 반환. B4 SZX 단독 경로 회귀.
**UI U**: U1 360×740 대기실 스크롤 없음. U2 16개 언어 한글 잔존 0(비한국어). U3 인앱 UA 에서 `confirm` 미사용. U4 HUD 외 부유 방 UI 0. U5 `/r/CODE#k=` → 올바른 게임·주소창에서 fragment 제거. U6 옛 `?room=&pin=&nick=` 링크 동작. U7 aria-live 알림. U8 닉네임 양방향 제어문자 제거. U9 최근 방 점. U10 스크린샷 사람 눈 검수(겹침·잘림).
**예산 E**: E1 대기 4인 60초 ≤ 2.0 msg/s, 8인 ≤ 5.0. E2 턴제 4인 플레이 ≤ 5.0. E3 8인 룰렛 1회 ≤ 200 msg, snap_req 0. E4 레이스 8인 ≤ 10 msg/s. E5 방장 페이지 CPU(서명) 20Hz 틱 시 ≤ 5%.

### 10.3 실기기 체크리스트(자동화 불가)
카톡 인앱 → 외부 브라우저 이스케이프 후 fragment 유지(Android intent·iOS) · 삼성 인터넷 IndexedDB CryptoKey 저장 · iOS Safari 백그라운드 20초 후 복귀 · 회사망(웹소켓 제한) · LTE↔Wi-Fi 전환 중 추첨.

---

## 11. 수용 기준 (출시 게이트)
1. §10 C·S·D·T·R·B·U·E 전 항목 통과(해당 패키지 범위), 하네스 결과 표를 커밋 메시지/PR 에 첨부.
2. 감사 3건의 구멍 목록(infra 상위 15 · draws H1~H8 · games 재현 11건) 각 항목에 "해결 패키지·시나리오 ID" 매핑 표(부록 A) 전부 ✅.
3. 로그인 없이 모든 흐름 가능, 로그인 사용자는 ✓ 배지만 추가.
4. 비한국어 UI 에서 방 관련 한글 0, 대기실·HUD 문구 키 ≤ 70.
5. 예산 E1~E4 수치 충족.
6. 롤백 리허설: 한 게임을 `mp.v:'v1'` 로 되돌려 10분 안에 배포·동작 확인.

---

## 12. 롤아웃 · 롤백
- **플래그**: `lpGames.js` 의 `mp.v`(게임별 `v1`/`v2`/`off`). 개인 오버라이드 `localStorage.lpRoomsV`, 링크 `?rooms=v1`.
- **공존**: v1 채널 `lp-room-*`, v2 `lpr-*`(Phase B `lprp-*`) — 서로 간섭 없음. resolve 가 둘 다 탐색(전환 기간). 캐시된 옛 페이지는 build-check 가 즉시 새로고침.
- **순서**: ① P0 배포(모든 v1 사용자 즉시 보호) → ② 코어+UI+yut·roulette 2종 v2 ON(운영자 실사용 1~2일) → ③ 추첨 나머지 → ④ 보드게임 → ⑤ 레이스·브리지 → ⑥ 14일 무사고 후 P6(v1 삭제).
- **롤백**: 게임 1줄 `v:'v1'` + `bump-cache.sh` + 커밋 1개. 진행 중인 v2 방은 끊김(허용). 코어 결함이면 모든 게임 `v1` 일괄(레지스트리 한 곳). 태그 `rooms-v2-<pkg>-pre` 로 파일 복원 가능.
- **관측**: `localStorage.lpDebug='1'` 디버그 패널(수신 이벤트·seq·서명 실패 수·msg/s 추정) — realtime 함정 #7. GA 이벤트 `room_create/join/deny(reason)/start/draw_verified/host_lost/takeover`(선행지표, 개인정보·코드 미전송).

---

## 13. 운영자 결정 (권장 기본값)
| # | 결정 | 권장 기본값 | 이유 |
|---|---|---|---|
| 1 | 공개 방 목록 | **OFF** (Phase B 이후 검토) | 서버 목록·신고·닉 관리 필요, 가족·교실 사용 |
| 2 | Phase B(익명 로그인+비공개 채널, SQL·대시보드 토글) | **지금은 보류, v2 안정 후 "예"** — 남용·차단 우회가 실제로 보이면 즉시 | Phase A 로 사칭·도청·대입은 막힘. B 는 차단 우회 비용과 서버 PIN·방 목록을 추가. 익명 세션 표시 수정 비용 있음 |
| 3 | 퀴즈 코드 이전 | **이전 안 함**(숫자 코드 유지, resolve 라우팅 + Rooms 브리지) | SQL 변경 없이 목적 달성, 200명 교실형 유지 |
| 4 | Space-Z SZX | **브리지만**(엔진·P2P·도전장 불변), 채널 통합은 후속 | 운영자 핵심 시스템 보존 |
| 5 | Space-Z 로그인 1:1 PvP | **그대로 유지**(변경 없음) | 없애는 결정은 운영자 몫 |
| 6 | PIN | **기본 없음**(코드·링크로 입장), 방장 `🔒 PIN` 선택 · `✋ 승인` 선택 | 퀴즈·Jackbox 수준의 쉬운 입장, 암호화·레이트리밋으로 안전 |
| 7 | 방 정원 | **12**(관전 포함) | 예산. 더 크면 퀴즈 |
| 8 | 이모지 리액션 | **ON**(대기실·결과·추첨 시청 중만) | 재미·몰입, 메시지 비용 작음 |
| 9 | 공개 비컨(drand) 모드 | **OFF**(고급 옵션) | 외부 의존·최대 6초 지연 |
| 10 | 카레이싱·브롤런 결과 방식 | **현 물리 유지 + 공정 시드만**(틱 10Hz) | 운영자가 다듬은 LPFX·밸런스 보존. "결과 먼저 감독 방식"은 별도 결정 |
| 11 | 마작 방장=딜러 | **고지 아이콘 + 검증 가능한 배분**, 서버 딜러 없음 | MPC·Edge 딜러는 수요 확인 후 |
| 12 | 방장 자동 승계 | **ON**(숨은 정보 없는 게임, 30초) | 윷은 과거 "승계 안 함" 결정 — **윷 포함 여부 확인 필요**(권장: 포함, 서명 체인으로 안전해짐) |
| 13 | 인앱 브라우저 | **현행 자동 이스케이프 유지**(fragment 보존 실기기 확인) | 운영자 2026-09-25 결정 존중 |
| 14 | 빙고 `bingo_winners` 열린 INSERT 정책 | **DROP**(운영자 SQL 3줄) — v2 는 DB 미사용 | 위조 벡터 제거 |
| 15 | Supabase 플랜 | **확인 요청**(메모리=Pro, 감사=무료 가정) | 설계는 무료 기준이라 어느 쪽이든 안전 |
| 16 | 봉인 모드 | **ON** | 외부 청취자 명단·결과 차단, 비용 작음 |
| 17 | 하네스 위치 | **`scripts/mp/`**(저장소, npm 의존 0) | 회귀 방지 게이트로 재사용 |

---

## 부록 A. 감사 구멍 → 해결 매핑
| 구멍 | 해결 | 검증 |
|---|---|---|
| infra#1 방장 출처 검증 없음 | 방장 서명 봉투(§3.2) | S1 |
| infra#2 navigate 무검증 | 핫픽스(완료) + v2 URL 없는 gameId 전환(§4.5) | S5 |
| infra#3·games#6 PIN·pid 평문 | ECIES 증명·봉인 모드·pid=키 해시 | S7·S8 |
| infra#4 PIN 대입 | 10회/분 쿨다운·20/s 상한 | C11 |
| infra#5 스냅샷 폭풍 | s/t 분리·재전송 같은 s·요청 뭉침(P0·§6.0.2) | E3 |
| infra#6 두 탭 유령 좌석 | Web Lock 좌석·여기서 계속 | C5 |
| infra#7 잠금 후 새로고침 차단 | 알려진 pid 항상 복귀(P0·§2.6) | C6 |
| infra#8·games#4 방장 크래시 무감지 | 게스트 워치독·띠·승계 | C8·T8·T9 |
| infra#9 라운드 중 복원 미연결 | 커널 자동 저장 | C7 |
| infra#10 한국어 하드코딩 | 16개 언어 표(P0·P2) | U2 |
| infra#11 초대↔방 미연결 | inviteUrl 토큰 포함(P6) | – |
| infra#12 UI 4중 | HUD 1개 | U4 |
| infra#13 코드 형식 4종 | 단일 코드 + resolve | C14 |
| infra#14 SZX 채널 재구독 no-op | 브리지 범위 밖 — SZX 후속 항목(재구독 시 topic 에 세대 접미사) | B4 |
| infra#15 전역 presence | Rooms 는 presence 미사용, lpPresence 분할은 P6 선택 | – |
| draws H1 3종 방 없음 | dice·balloon·glory-racing 신규 | D·T |
| draws H2 결과 무결성 | LpFair.draw/chain/deal | D1~D9 |
| draws H3 `?winner=` 위조 | `#cert` 자가검증 | D5·D6 |
| draws H4 빙고 승자 위조 | 방장 검증·서명 + 전원 재검증, DB 미사용 | D10 |
| draws H5 채널 도청 | 봉인 모드 | S7 |
| draws H6 시드 리플레이 불가 | 결과 먼저 + frameAt | D1·D11 |
| draws H7 동시 출발 | startAt + NTP 오프셋 | D2 |
| draws H8 초기 스냅샷 공백 | welcome 에 상태 동봉 | C2 |
| games 사칭(1·4·5) | 봉투 pid 신원·서명 | T2·S3 |
| games 자리 강탈(8) | reserved 좌석 | T3 |
| games 구미 결과 불일치(10) | 방장 확정·일시정지 | T10 |
| games 차단 우회(6) | 자동 승인 모드(+Phase B uid) | C10 |
| games 이중 hb | 게임 hb 금지·hb 1종 | T12·E1 |
| games 게임 전환 목록 누락 | 레지스트리 | C9 |
| games `confirm()` | 자체 확인창 | U3 |
| games prism 누수 | 커널 hb | T11 |
