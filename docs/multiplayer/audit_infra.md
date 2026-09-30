# 멀티플레이 공용 인프라 감사 (audit_infra.md)

작성: 2026-09-30 · 대상 저장소 `C:\code\python\luckyplz` · 범위: 공용 멀티플레이 인프라 (게임별 배선은 이름만 언급, 별도 감사 대상)

실측은 Node `vm` 하네스로 **실제 `vendor/supabase.min.js`(@supabase/supabase-js 2.104.0) + `lpRoom.js`** 를 격리 컨텍스트("탭")마다 올려 Supabase Realtime broadcast 만 태우고 REST/Auth/Storage 는 전부 차단(`Network.setBlockedURLs` 대응)하여 수행. 방코드는 전부 `ZZTEST*`. 실험 스크립트·원자료는 같은 폴더 `infra/`.

---

## 0. 큰 그림 — 현재 몇 개의 서로 다른 멀티플레이 시스템이 공존하는가

운영자 요구는 "**Battle.net 식 공통 대기공간 + 모든 게임에 하나의 방 만들기/참가 포맷**". 실제 코드에는 **서로 말이 안 통하는 멀티플레이 스택이 4개** 있다.

| 스택 | 채널/전송 | 진실원천 | 참가 식별 | 쓰는 곳 |
|---|---|---|---|---|
| **A. lpRoom (host-authoritative broadcast)** | `lp-room-<CODE>` broadcast | 호스트 브라우저 메모리 | 6자리 코드+4자리 PIN+닉 (+ device `lp_pid`) | 12게임: roulette·ladder·lotto·bingo·car-racing·team·gummy·ludo·reversi·mahjong-tw·prism-hex·yut + `/lobby/` |
| **B. Space-Z SZX** (games/dodge 하단) | `szx-race-<6digit>` broadcast + **WebRTC P2P 메시** | 없음(각 폰이 시드로 로컬 생성, 상태만 gossip) | 6자리 **숫자** 코드, PIN 없음, 로그인 없음 | dodge 동시 대결(≤8)·2인 협동 |
| **C. Space-Z PvP** (같은 파일, 별개) | `spacez:room:<uuid>` broadcast + `spacez_*` RPC(DB 테이블) | Supabase 테이블(RLS+RPC) | 로그인 필요, DB room id | dodge 1:1 대결 |
| **D. Live Quiz v2** (games/quiz) | `qlive-<CODE>` broadcast(nudge만) + `qlive_*` SECURITY DEFINER RPC | **Supabase DB**(진짜 서버 진행) | 6자리 코드, PIN 폐지, 기기 `lp_qlive_pid` | quiz |
| (E. game_invites) | postgres_changes(`game_invites`) + `send/respond_game_invite` RPC | DB | 로그인+친구 관계 | 친구 초대 토스트 |
| (F. LpPresence) | 단일 전역 `lp_presence` presence 채널 | 클라이언트 presence + 45s RPC | 로그인 | 온라인/DND 점 |

**핵심 결론**: 방 만들기/참가가 게임마다 다른 이유는 A~D가 근본 설계(누가 진실원천인가·PIN 유무·코드 형식·로그인 요구)부터 다르기 때문이다. 공통 포맷을 씌우려면 코드/PIN 형식과 join 핸드셰이크를 **한 계약으로 통일**하는 게 선결이고, 그다음에 "게임별 러너"를 그 계약 위에 얹는 구조여야 한다. 지금은 lpRoom(A)이 사실상 그 계약에 가장 가깝지만, 아래 §2의 신뢰모델 결함 때문에 그대로 확장하면 구멍이 같이 커진다.

또한 **코드 형식부터 충돌**한다: lpRoom = 6자 영숫자(0/O/1/I/L 제외 알파벳), SZX/quiz = 6자리 **숫자**. 홈 join 모달은 4~10자 영숫자를 받는다(`parseRoomInput`). 즉 "홈에서 아무 코드나 넣어 참가"는 A만 가능하고 B/C/D 코드는 홈에서 못 받는다 → Battle.net식 단일 로비의 제1 장애물.

---

## 1. 모듈별 정밀 분석

### 1.1 `public/js/lpRoom.js` (3,592줄, 209KB) — 스택 A의 심장

**목적**: 호스트가 방송, 게스트가 시청하는 host-authoritative 방. 전송은 Supabase Realtime broadcast, DB 쓰기 0.

**공개 API** (`window.LpRoom`, lpRoom.js:3570): `hostCreate·guestJoin·probeRoom·parseRoomInput·detectAutoJoinParams·showHostModal·showGuestJoinModal·showHomeJoinModal·detectGuestIntent·normalizeOnlineBtn·tryResumeHost·peekLastRoom·showConnectingPill·hideConnectingPill·_injectStyles`.

**room(host) 표면** (lpRoom.js:849): `broadcast·broadcastReliable·rtt·onStatusChange·connectionStatus·snapshot·saveSnapshot·restoredSnapshot·clearSnapshot·onGuestJoin·onGuestLeave·onGuestPresence·onGuestAction·kick·ban·unban·banned·lock·unlock·isLocked·close·transferTo·shareUrl·guests·code·pin·gameId·hostName·epoch·resumed`.

**guest 표면** (lpRoom.js:1722): `on·requestSnapshot·action·close·skew·myRtt·onStatusChange·connectionStatus·rejoin·ok·code·pin·gid·pid·hostName·gameId·nickname`.

**메시지 프로토콜** — 채널 `lp-room-<CODE>` broadcast, `self:false,ack:false`.
- host→guest: `host:join_ack·snapshot·guests·heartbeat(5s)·ping(4s)·config·state·start·spin_start·tick·stop·result·reset·action·close·navigate·rejoin·kicked·bingo_winners·paused·resumed·ended·resume_countdown·quiz_*`. 전부 `KNOWN_HOST_EVENTS`(lpRoom.js:1109)에 명시 등록(와일드카드 flaky 회피). **게임이 쓰는 host 이벤트가 전부 이 배열에 있는지 grep 검증 → 미등록 0건**(정상). 단 새 게임 추가 시 여기 등록 누락이 반복 위험(체크리스트에 있음).
- guest→host: `join_request·hb(4s)·pong·leave·request_snapshot·action·probe`.
- 시퀀스: 모든 host 방송에 `_seq`(단조 증가)·`_ep`(host epoch). snapshot 은 `_seqAtSnap`. 중요이벤트는 `_id`+3회 재전송, 게스트 100개 LRU dedupe.

**상태모델**: 호스트 브라우저 메모리가 유일 진실원천. `currentSnapshot`(late-join 재생용), `guests` Map(gid→{nickname,pid,lastSeen,vis}), `_knownPids`/`_banned`(roster blob 로 sessionStorage 영속). 게스트는 seq 추적 + STATEFUL 이벤트 캐시(늦은 리스너 replay, `realtime_sync_patterns.md` 함정#1 대응).

**join flow**: 코드(타이핑/링크/QR BarcodeDetector)+PIN+닉 → `probeRoom`(gameId 조회)→ `/games/<id>/?room=CODE` 로 이동, PIN/닉은 **sessionStorage `lp_guestTransit`(60s TTL)** 로 넘겨 URL 바에 PIN 노출 방지. QR 은 `?pin=&nick=` 도 허용. 완전 프리필이면 폼 없이 `_silentGuestJoin`(3s→6s→8s 재시도). 로그인 불필요, authed 는 ✓ 배지용.

**presence/heartbeat/stale**(2026-09-25 item 13~19): 게스트 `guest:hb` 4s, 호스트 sweep 2s, 무소식 15s(hidden 40s) 드롭. 호스트 epoch 로 재시작 감지, Web Lock `lp-host-<CODE>` 로 탭당 단일 호스트, `saveSnapshot`/`restoredSnapshot` 로 리로드 복원, kick/ban(yut·reversi).

**reconnect/refresh**: 게스트 pagehide→`guest:leave{bye}`, 재진입은 새 `guestJoin`(같은 pid). 호스트 리로드→`tryResumeHost`(sessionStorage marker + Web Lock). 백그라운드 socket keep-alive(item 18).

**host leave/migration**: 마이그레이션 = `transferTo`(게임 전환) — 호스트가 이동, 게스트는 `host:navigate` 따라감. **호스트 이양(다른 사람이 호스트 승계)은 없음** — 호스트가 죽으면 방이 죽는다(quiz/SZX 는 승계 있음, lpRoom 은 없음).

#### 실측으로 확인한 결함 (infra/e*.mjs)

- **[치명·신뢰모델] 채널이 완전 공개 + 모든 제어가 클라 신뢰 방송.** 코드만 알면 PIN 없이 `sb.channel('lp-room-<CODE>')` 구독으로 **PIN·모든 게스트 pid·닉이 평문 노출**되고, 스푸핑 방송이 그대로 먹힌다. E1 실측(ZZTEST85): PIN-less 청취자가 `guest:join_request` 에서 PIN `4821` + 3명 pid 전량 수집 → 그 PIN 으로 join 시 `host:snapshot`(게임 상태) 수신, `authed:true`+임의 이름으로 **가짜 ✓ 인증 배지** 획득. 스푸핑 `host:kicked`(피해자 pid만 알면)로 특정 게스트 강퇴, 스푸핑 `host:navigate` 로 전원을 임의 URL 로 이동(아래 참조), 스푸핑 `host:close` 로 방 폭파 — 전부 성공. **호스트 서명·검증이 전무**(broadcast `self:false` 는 발신자 식별이 아니다).
- **[치명·피싱] `host:navigate` URL 무검증 → 오픈 리다이렉트/스크립트 실행.** 게스트는 받은 `p.url` 을 `new URL(p.url,location.href)` 후 `location.href=` (lpRoom.js:1569). **동일 출처·스킴 화이트리스트 없음.** E1: 스푸핑 방송으로 g1/g3 이 `https://evil.example/phish?...&nick=Alice` 로 이동. 별도 Edge 실측으로 `javascript:` URL 도 `location.href` 경로에서 실행됨을 확인(피해 페이지 DOM 에 실행 흔적). `_headers` 에 CSP 없음. → 방 코드 하나로 참가자 전원을 피싱/XSS 로 몰 수 있다. **화이트리스트(같은 origin + `/games/<validId>/`·`/lobby/` 경로)로 강제 필요.**
- **[높음] PIN brute-force 무제한.** E1: 잘못된 PIN 15연속 → 15× `bad_pin`, 레이트리밋·잠금 전무. 4자리(1만 조합)를 방송으로 수천 건/초 시도 가능. host `guest:action` 만 토큰버킷이 있고 `join_request` 는 무방비.
- **[높음·유령좌석] 같은 브라우저 두 탭 = 같은 `lp_pid` → 방장이 한 명을 두 좌석으로 인식하고 무한 rejoin 루프.** E2 실측: 같은 localStorage 두 탭(둘 다 "Jin")이 한 방 참가 → 24초 관찰 동안 호스트 `onGuestJoin` **15회 발화(1 join + 14 join(re))**, 게스트 A/B 각각 `room:rejoined` 6·5회. 원인: 두 탭이 같은 pid 로 hb 를 보내면 `_touch`/zombie-dedupe 가 서로를 좀비로 오인해 번갈아 rejoin 을 유발. bingo(pid로 카드 배정)·yut(pid로 말 배정)처럼 pid=좌석인 게임은 **좌석이 튄다**. (SZX 는 이걸 "같은 사람 = 같은 pid" 로 의도 흡수하지만 lpRoom 은 별 좌석으로 취급.)
- **[높음] host:tick 이 게스트 seq 를 전진시키지 않아 매 스핀마다 request_snapshot 폭풍.** E7 실측: 1회 스핀(host:spin_start→tick×40→result), 게스트 4명 → `guest:request_snapshot` 4건(전부 `reason:seq_gap`) + 그에 대한 `host:snapshot` 4 + `host:guests` 4. 원인: 호스트는 tick 에도 `++_bcastSeq`(seq 소비)하지만 게스트 dispatch 는 tick 을 seq 갱신에서 제외(lpRoom.js:1549) → tick 40개 뒤 도착한 `host:result` 의 `_seq` 가 `lastSeen+41` 이라 "40개 유실"로 오판 → 스냅샷 요청. **N명 방에서 스핀·레이스마다 N×(요청+스냅샷+로스터) 방송 증폭.** 무료 100msg/s 한도에 직접 위협(§3). 수정: tick 도 `_lastSeenSeq` 를 전진시키되 gap 복구만 스킵.
- **[중] 호스트 크래시(host:close 없이 소켓만 사망)를 게스트가 30초간 감지 못 함.** E5 실측: 호스트 `realtime.disconnect()` 후 30초, 게스트 `connectionStatus` 는 여전히 `connected`, `host:close` 미수신, watchdog 는 `request_snapshot` 만 보냄(방송은 이미 죽은 채널로 나가 무응답). lpHostCtl 의 `host:close→ended` 도 안 뜸. → 호스트가 앱을 죽이면 게스트는 "연결됨"으로 표시된 채 영원히 멈춘 화면. **게스트측 host-liveness watchdog(heartbeat N초 무소식→"호스트 연결 끊김" UI)이 필요**(SZX 는 이걸 12/15초로 갖고 있음).
- **[중] 호스트 리로드 후 게스트 스냅샷 미수신.** E5: `tryResumeHost` 로 호스트 복원은 성공(`hostResumed:true`, 게스트 1명 `room:rejoined`)했으나 **resumedRoom 은 라운드 상태를 모르고**(`resumedLocked:false`, `restoredSnapshot` 은 게임이 saveSnapshot 을 연결했을 때만) 게스트는 리로드 후 `host:snapshot` 을 못 받음(`guestGotSnapshotAfterReload:null`). team·roulette·ladder·lotto·bingo·car-racing·gummy 는 라운드 중 복원 미연결(MEMORY 명시). → 호스트가 스핀 도중 새로고침하면 게스트는 옛 화면에 고착.
- **[중] `lock()` 후 새 게스트/새로고침 게스트 영구 차단.** E5: 호스트가 Start(lock) 후 게스트가 새로고침하면 재진입 `locked` 거절(`afterRefreshJoin:"locked"`). 재진입은 "이미 아는 pid + rejoin:true" 만 통과인데, 새 문서의 첫 `guestJoin` 은 `rejoin:false`(silent 경로 포함) → **정상 참가자가 F5 한 번에 방에서 튕겨 solo 로 떨어진다.** 게임 8종이 lock 을 쓰므로 광범위. 수정: 잠긴 방이라도 `_knownPids` 에 있는 pid 는 첫 join 도 허용.
- **[중] `unlock` 호출 게임 거의 없음.** roulette/ladder/lotto/bingo 는 `lock()` 만 하고 `unlock()` 없음 → 한 판 끝나고 "다시" 해도 방은 잠긴 채라 그 사이 친구가 못 들어온다. car-racing/ludo/gummy 만 unlock 있음.
- **[중·UX 중복] 화면에 방 UI가 3중으로 뜬다.** 같은 방에 대해 (1) lpRoom `showHostStatus`/`showGuestStatus` **상단 상태 pill**(z9000)+게스트 패널, (2) lpMultiplayer **플로팅 패널**(z9050, 로스터+게임전환+방닫기), (3) lpHostCtl **⏸⏹ 바**(z9100)+오버레이 — 셋 다 자동 마운트되어 **로스터가 두 곳(pill 패널 + mp 패널), 방 닫기가 두 곳(pill × + mp "방 닫기"), 코드 표시가 두 곳**에 중복. 게임 페이지엔 여기에 lpInviteButton pill(우하단)까지 4번째 플로팅 요소. 좁은 폰에서 상충. Battle.net식 통일의 최대 정리 대상.
- **[낮음] `_LP_PICKER_GAMES`(lpRoom.js:2105) 7종 하드코딩** — home 방장 게임 피커. lpMultiplayer `GAMES`(7종), `showHomeJoinModal` `_validGames`(14종), `showGuestJoinModal` `_v`(7종)가 **네 곳에 제각기** 게임 목록을 재정의 → yut/ludo/reversi/mahjong-tw/prism-hex/gummy 가 홈 피커·mp 스위처엔 없고 `_validGames` 엔 있는 등 어긋남. 새 게임 추가 시 누락 반복(CLAUDE.md 체크리스트가 이를 증언).
- **[낮음] `bingo_winners` 이벤트**는 KNOWN 배열엔 있으나 실제로 broadcast 하는 코드가 없음(bingo 는 `host:action` 으로 처리) → 죽은 프로토콜 항목.

### 1.2 `public/js/lpMultiplayer.js` (914줄) — 플로팅 패널(스택 A 전용)

목적: `lp-room-host-ready`/`guest-ready`/`lp-room-closed` CustomEvent 소비하는 Battle.net 풍 드래그 패널. 로스터·게임전환(host)·RTT pill·copy·방닫기/나가기. 상태는 sessionStorage(뷰/위치).

- **[낮음] 결과화면 버튼 강제 숨김이 6게임 셀렉터 하드코딩**(lpMultiplayer.js:239) — `body.lp-mp-active` 일 때 `#replayBtn`·`#backToSetupBtn`·`#restartBtn`·`.result-btns` 등 숨김. yut·ludo·reversi·mahjong-tw·prism-hex·gummy 는 이 셀렉터에 없어 멀티 중 로컬 리플레이 버튼이 살아있을 수 있음(방 깨짐 위험, "방이 쉽게 깨진다"의 잔재).
- **[낮음] 게임전환 `GAMES` 7종 고정** — §1.1 목록 4중복 문제의 일부. 보드게임군 전환 불가.
- **[낮음] `nextHint` CSS ::after 텍스트를 로드시 언어로 1회 고정** — 이후 언어 전환 미반영.
- 중복은 §1.1의 3중 UI 문제로 집계.

### 1.3 `public/js/lpHostCtl.js` (522줄) — ⏸/⏹ 바 + 오버레이

목적: 게임별 2~3콜백으로 pause/resume(5초 카운트다운)/end + guest 오버레이. `host:paused/resumed/ended/resume_countdown` + `host:close→ended`.

- **[중] 기본 문구가 한국어 하드코딩**(lpHostCtl.js:91 `DEFAULT_TEXTS`). 게임 10종이 `texts:` 오버라이드를 **전혀 안 넘김**(grep 0건) → **비한국어 게스트가 일시정지·종료 오버레이에서 한국어("일시정지 중","호스트가 게임을 종료했어요")를 본다.** CLAUDE.md의 "게임 UI 는 luckyplz_lang 따른다" 원칙 위반. lpGameText.js 에도 이 문자열 없음.
- **[낮음] `host:resume_countdown` 은 `_id` 재전송 없이 1회 방송** — 유실되면 게스트는 카운트다운 없이 갑자기 resume(또는 계속 멈춤). host:paused/resumed 도 재전송 없음(§ team 만 broadcastReliable 사용).

### 1.4 `public/js/lpInvite.js`(351) + `lpInviteButton.js`(550) — 친구 초대(스택 E)

목적: 로그인+친구 관계 기반 게임 초대. `send_game_invite`/`respond_game_invite` RPC + `game_invites` postgres_changes 토스트. 버튼은 `/games/*` 우하단 pill.

- **[중·기능 단절] 초대에 방 코드/PIN 이 실리지 않는다.** `_sendOne`(lpInviteButton.js:456)이 `gameUrl=location.href` 를 보냄 — 호스트가 방을 만들어도 **host URL 에는 `?room=` 이 없다**(호스트는 `?room=` 없이 방을 만듦; 코드는 lpRoom 내부에만). 즉 친구가 초대를 수락해도 **빈 게임 페이지로 이동, 방에 자동 참가 안 됨.** 초대(E)와 방(A)이 데이터로 연결돼 있지 않다. → "초대로 바로 같은 방" 이라는 기대가 깨짐. `location.href` 에 방 코드 주입 필요.
- **[중] 초대 게임 목록 vs 방 게임 목록 불일치** — lpInvite `_humanGame` i18n games 는 12종이지만 lpInviteButton `_humanGame` games 는 6종(lotto·roulette·ladder·dice·team·bingo·car-racing만). yut/ludo/reversi 등 초대 시 라벨 raw.
- **[낮음] `game_invites_no_dup_pending` UNIQUE(from,to,status) deferrable** — 같은 두 사람 사이 declined/expired 행이 쌓이면 `(from,to,'declined')` 유일 제약과 충돌 가능성(상태 전이가 여러 declined 를 만들면). 실무상 respond 가 UPDATE 라 큰 문제는 아니나 재초대 취소 로직(§send 의 cancel 은 pending 만) 밖의 상태는 정리 안 됨.

### 1.5 `public/js/lpPresence.js`(207) — 전역 presence(스택 F)

목적: online/dnd/offline 단일 전역 `lp_presence` 채널 + 45s `presence_heartbeat` RPC.

- **[중·확장성] 전역 단일 presence 채널** — 코드 주석도 인정: "모든 클라가 모든 온라인 유저를 본다, >5k 동시접속에서 친구별 분할 필요". **presence 는 무료 20/s·Pro 50/s** 로 broadcast(100/s)보다 훨씬 타이트(§3). DAU 가 붙으면 여기가 먼저 터진다. 또 프로필 아바타 등 개인정보가 전 로그인 유저에게 방송됨(현재는 manual_status 만이라 경미).
- **[낮음] lpRoom·SZX 가 presence 를 의도적으로 안 쓰는 것과 별개 채널** — 방 참가자 목록(lpRoom)과 friend presence(lpPresence)는 완전 분리. Battle.net 로비를 만들면 "친구가 지금 이 방에 있음"을 보여주려면 둘을 잇는 다리가 없음.

### 1.6 `public/js/lpShare.js`(219) / `lpNotify.js`(206) / `lpSocial.js`(1016)

- **lpShare**: Kakao SDK 미등록 → Web Share API + 클립보드 폴백. 방 공유 텍스트 생성에 쓰임. 결함 없음(설계상 graceful degrade). 방 코드 공유의 실제 경로.
- **lpNotify**: SW 없이 foreground OS 알림 + in-app 토스트. 게임 페이지엔 미로드(방해 방지). 방과 직접 연동 없음.
- **lpSocial**: 친구/DM/그룹챗. `messaging_rpc_pattern.md` 대로 읽기는 SECURITY DEFINER RPC(`dm_inbox`,`get_dm_thread_messages`)지만 **`getFriends`·`getGroupMessages`·`message_reactions` 는 여전히 직접 SELECT** — 모바일 WebView 무음 실패 잠재 지뢰(메모리에 명시된 미해결 항목). lpRoom 의 "+친구" 단축이 `getFriends`(직접 SELECT)에 의존 → 카톡 인앱에서 방 로스터 +친구가 조용히 빈 목록일 수 있음.

### 1.7 `siteFooter.js`(550) — 모듈 주입

`window.supabase` 존재 시 lpRoom→lpHostCtl→lpMultiplayer, 그리고 lpSocial/lpActivity/lpPresence/lpInvite/(게임페이지)lpInviteButton/(비게임)lpNotify 를 defer `<script>` 로 순차 주입. `?v=<stamp>` 캐시버스팅.

- **[중·순서 의존] 주입 순서가 로드 완료 순서를 보장하지 않는다.** 전부 `defer` 라 DOM 순서대로 실행되지만, lpRoom 은 내부에서 `waitForSupabase`(폴링)로 방어. 그러나 게임 페이지들은 `_waitForLpRoom`(자체 폴링 40~60회)로 또 방어 → **모든 게임이 같은 "LpRoom 있을 때까지 폴링" 보일러플레이트를 복붙**. 공통 `LpRoom.ready()` Promise 하나면 될 일.
- **[낮음] supabase 미탑재 페이지엔 lpRoom 자체가 안 뜸** — balloon/brick/bubble/dice/glory-racing/lucky-merge/snake/starship/tetris/pacman/burger 등은 `supabase.min.js` 미포함이라 방 기능 원천 부재(설계 의도이나, "모든 게임 공통 참가"와 배치).

### 1.8 `public/lobby/index.html`(144) — 유일한 "대기공간"

목적: 호스트가 아직 게임을 안 고른 방(`gameId:'lobby'`)의 게스트 착지 페이지. `host:navigate` 로 게임 확정 시 전원 이동.

- **[중] "Battle.net 로비"의 유일한 흔적이지만 매우 수동적** — 로스터·채팅·게임 미리보기 없음, 그냥 "방장이 고르는 중" 스피너 + 코드. lpMultiplayer 패널이 얹혀 로스터는 보이나, **여기서 게임을 시작하거나 다른 방을 찾거나 친구를 보는 기능 없음.** 진짜 로비가 아니라 "게임 픽 대기실". 운영자가 원하는 공통 공간의 씨앗은 여기지만 대폭 확장 필요.
- **[낮음] 홈 방 만들기(`fromHome:true`)만 lobby 방을 만든다** — 게임 페이지에서 만든 방은 그 게임에 고정. 즉 "먼저 모이고 나중에 게임 고르기"는 홈 경로에서만 가능.

### 1.9 `public/auth/`

- **[낮음·양호] open-redirect 방어 있음** — `getReturnUrl`(auth/index.html:309)이 `/` 시작 + `//` 아님만 허용. OAuth `redirectTo` 도 same-origin. 단 §1.1의 `host:navigate` 무검증과 대비되어, **방 인프라 쪽만 리다이렉트 검증이 없다.**

### 1.10 Space-Z SZX (games/dodge 하단, 스택 B)

목적: 로그인·DB 없이 ≤8인 동시 대결 + 2인 협동. 채널 `szx-race-<6digit>`, 상태 broadcast 하트비트(변경 즉시+2.5s) + **WebRTC P2P 메시**(pid 작은 쪽 offer, ICE 취합 SDP 1통, 위치 10Hz 직통, 실패 짝만 서버 2s). presence **의도적 미사용**(track 변경 알림 누락 실측 교훈, `spacez_race.md`).

- **[구조 상이] 진실원천 없음** — 각 폰이 시드로 로컬 생성, 상태만 gossip. host 승계 있음(`actingHost`: 방장 없으면 최초 입장자). lpRoom 과 프로토콜·코드형식(숫자)·신뢰모델 전부 다름 → 공통화의 이질점.
- **[중] SZX 도 방송 스푸핑에 무방비** — 채널 공개, `st`/`go`/`tk`/`sig` 무검증. 남의 pid 로 `st{s:'left'}` 보내 강퇴, `go` 로 임의 출발 유발 가능(로그인 없는 캐주얼이라 피해는 작지만 일관된 취약).
- **[중] 8인 P2P 메시 확장 한계** — 폰당 7 연결, TURN 없음(대칭 NAT ~5% 서버 폴백). 통신사 NAT 국내 실패 가능성 실측 언급. 무료 한도는 P2P 로 회피하나 **직통 실패 다수 시 서버 pos 폴백이 N² 로 증가**.
- **[중] `disconnect(true)` 후 즉시 `connect()` 재구독** — supabase `channel(topic)` 은 **같은 topic 이면 기존(죽어가는) 채널 객체를 반환**(vendor 확인). E4 실측: removeChannel(0ms) 직후 같은 topic `channel()` → **동일 객체 반환, 재subscribe 가 조용한 no-op**(status 콜백 0건, 채널 0개로 정리됨) → 재연결이 실패해도 에러 없이 침묵. SZX 의 8s 감시 타이머가 결국 새로 만들지만 그 사이 유령 상태. (lpRoom 은 매번 새 code/gid 라 회피.)

### 1.11 Space-Z PvP (같은 파일, 스택 C) & Live Quiz (스택 D)

- **PvP**: `spacez_*` RPC(DB 테이블 RLS+RPC, 로그인 필요) + `spacez:room:<uuid>` broadcast. lpRoom·SZX 와 또 다른 세 번째 dodge 내 방 시스템. 코드 재사용 0.
- **Quiz(D)**: **가장 견고한 설계** — DB가 진실원천, `qlive_*` SECURITY DEFINER RPC, 멱등 답안(PK (code,q,pid)), 폴링이 확실경로(채널은 nudge만), 호스트 부재 자동 진행, PIN 폐지, 기기 pid+세션 복귀. **운영자 요구("튕겨도 언제든 재접속")를 이미 구현한 유일한 스택.** 단 **Pro 플랜 전제**(Realtime 500/50), 운영 마이그레이션 수동 적용. lpRoom 계열과 공유하는 코드 0 — quiz 만 별세계.
  - **[낮음] quiz 는 `?room=` 도 받지만**(index.html:580 `sp.get('room')`) 홈 join 모달이 quiz 로 보내는 코드 형식(6영숫자 vs 6숫자)과 불일치 소지 — quiz 코드는 숫자, lpRoom probe 는 quiz 를 모름(lpRoom 채널이 아니라 qlive 채널).

---

## 2. 신뢰·보안 종합

| 항목 | lpRoom(A) | SZX(B) | PvP(C) | Quiz(D) |
|---|---|---|---|---|
| 게스트가 호스트 사칭 | **가능**(방송 서명 없음) | 가능 | RPC로 방어 | RPC로 방어(host_key) |
| 방코드 추측 | 6영숫자(~5.9e8) 방송이라 열거는 느리나 유출 쉬움 | 6숫자(1e6, 열거 쉬움) | uuid | 6숫자 |
| PIN | 4자리, **brute 무제한** | 없음 | — | 폐지 |
| 리다이렉트/XSS | **host:navigate 무검증(오픈 리다이렉트·javascript: 실행)** | navigate 없음 | — | — |
| 개인정보 방송 | PIN·pid·닉 평문 | pid·닉 | — | pid |

**요지**: DB-RPC 를 진실원천으로 둔 Quiz/PvP 는 서버가 auth.uid()/host_key 로 방어되어 견고하다. 반면 **방송만으로 도는 lpRoom·SZX 는 채널을 아는 누구나 읽고 쓰는 구조**라 신뢰가 필요한 게임(누가 커피 쏠지=원래 목적!)의 근간이 취약하다. 공통 포맷을 만들 때 **최소한 (a) host epoch+서명 토큰으로 host 이벤트 출처 검증, (b) navigate URL 화이트리스트, (c) join_request 레이트리밋** 은 필수. 근본적으로는 신뢰가 필요한 결과(추첨 승자)는 Quiz 처럼 SECURITY DEFINER RPC 로 확정하는 편이 맞다.

---

## 3. Supabase 무료 티어 한도 위험

공식(메모리·코드 주석): **broadcast 100 msg/s**(보낸+받은, 방송 1회=인원수배), **presence 20/s**, 동시연결 200. Quiz 는 Pro(500/50) 전제.

- **idle 도 이미 방송이 많다**(E1): 1호스트+3게스트 유휴에 한 리스너가 1.95 ev/s 관측 = 방 전체로는 heartbeat(0.2/s×4수신)·ping(0.25×4)·pong(0.75×4)·hb(0.7×4) 합산 **~10 msg/s 수준을 4인 유휴 방 하나가 소비.** 8인이면 N배(수신자 증가로 제곱 경향). **동시 방 몇 개만 돌아도 100/s 근접.**
- **seq-gap 폭풍(E7)**: 스핀/레이스 1회마다 N×(request_snapshot+snapshot+guests) 추가 방송 → 활동 중엔 유휴의 수 배. **이 버그 수정이 무료 한도 방어에 직접 기여.**
- presence(F)는 전역 채널이라 로그인 유저 증가 시 20/s 를 가장 먼저 위협.
- **권고**: heartbeat/ping 주기 상향(5s→10s, 4s→8s) 또는 게스트 pong 을 요청형으로, seq-gap 오탐 제거, presence 친구별 분할.

---

## 4. 중복·죽은 코드

- **UI 3~4중 중복**(§1.1): 방 pill(lpRoom) + 패널(lpMultiplayer) + ⏸⏹바(lpHostCtl) + 초대 pill(lpInviteButton). 로스터·방닫기·코드가 두세 곳에 렌더.
- **게임 목록 4중 정의**(§1.1): `_LP_PICKER_GAMES`·`GAMES`·`_validGames`·`_v` — 서로 어긋남.
- **`_waitForLpRoom` 보일러플레이트**를 게임 12개가 각자 복붙(§1.7).
- **`bingo_winners`** 죽은 이벤트(§1.1).
- **3개의 독립 방 스택(A/B/C)이 dodge 한 파일에 C, 나머지 A** — 코드 재사용 0, 유지보수 3배.
- **초대(E)↔방(A) 데이터 미연결**(§1.4) — 실질적 죽은 통합.

---

## 5. 모듈 → 유지/병합/교체 권고

| 모듈 | 권고 | 근거 |
|---|---|---|
| `lpRoom.js` | **유지+강화(공통 계약의 기반으로)** | 12게임이 의존, 가장 성숙. 단 §2 신뢰 3종·seq-gap·lock-refresh·host-crash watchdog·host 이양을 반드시 보강 |
| `lpMultiplayer.js` | **병합**(→ lpRoom 상태 pill과 하나의 방 HUD로) | 로스터·방닫기·코드 3중 중복 제거, 게임목록 단일화 |
| `lpHostCtl.js` | **유지+i18n 수정** | 기능 견고, 기본문구 한국어 하드코딩만 치명 |
| `lpInvite.js` | **유지+방코드 연동** | 전송/응답 골격 양호, gameUrl 에 방코드 주입 필요 |
| `lpInviteButton.js` | **유지+게임목록 통일** | pill 자체는 OK, 6종 라벨 하드코딩 |
| `lpPresence.js` | **유지+친구별 분할 로드맵** | 전역 채널 확장성·presence 한도 |
| `lpSocial.js` | **유지+RPC 마감** | getFriends 등 직접 SELECT 를 RPC 로(모바일 무음 실패) |
| `lpShare.js` | **유지** | 결함 없음 |
| `lpNotify.js` | **유지** | 방과 무관, 견고 |
| `supabase-config.js` | **유지** | 클라 옵션 기본값 사용(realtime rate 파라미터 미설정 — 조정 여지) |
| `siteFooter.js` | **유지+`LpRoom.ready()` 도입** | 폴링 보일러플레이트 제거 |
| `lobby/index.html` | **교체/대폭 확장**(진짜 로비로) | 운영자 요구의 핵심, 현재 수동 스피너뿐 |
| SZX(dodge B) | **유지하되 공통 계약에 어댑터로 편입** | 진실원천 없음·P2P 등 특성상 별 러너, 코드형식/스푸핑만 정렬 |
| Space-Z PvP(C) | **병합 후보**(SZX 또는 공통 방 위로) | dodge 내 세 번째 방 시스템, 중복 |
| Quiz(D) | **유지(신뢰 모델의 참조 구현)** | "튕겨도 재접속" 이미 구현. 신뢰 필요한 결과는 이 패턴을 공통화 |
| game_invites 마이그레이션 | **유지+방코드 컬럼/URL 규약** | 초대↔방 연결 |

---

## 6. 심각도순 상위 15개 구멍

1. **[치명] lpRoom 방송에 호스트 출처 검증 없음** — 코드만 알면 스푸핑 host:kicked/navigate/close/config 전부 먹힘(E1 실측). 신뢰가 목적인 추첨 게임의 근간 붕괴.
2. **[치명] `host:navigate` URL 무검증 → 오픈 리다이렉트 + `javascript:`/외부 도메인으로 참가자 전원 이동**(E1 + Edge 실측). CSP 부재로 XSS 까지. **화이트리스트 즉시 필요.**
3. **[치명] 방 채널 공개로 PIN·전 게스트 pid·닉 평문 유출**(E1). PIN 무력화 + 표적 강퇴/사칭 재료.
4. **[높음] PIN brute-force 무제한**(E1: 15연속 bad_pin, 잠금 0). 4자리 방송 무한 시도.
5. **[높음] seq-gap 오탐으로 매 스핀/레이스마다 request_snapshot 폭풍**(E7: 4게스트 1스핀=요청4+스냅4+로스터4). 무료 100msg/s 직접 위협.
6. **[높음] 같은 브라우저 2탭=같은 lp_pid → 유령 좌석·무한 rejoin 루프**(E2: 24초에 host join 15회). pid=좌석 게임(bingo·yut)에서 좌석 붕괴.
7. **[높음] lock() 후 게스트가 새로고침하면 영구 `locked` 거절 → solo 로 튕김**(E5). 8게임 광범위.
8. **[중] 호스트 크래시(host:close 없는 소켓 사망)를 게스트가 30초+ 감지 못 함**(E5: connectionStatus 계속 connected). 게스트가 멈춘 화면에 고착. host-liveness watchdog 부재.
9. **[중] 호스트 리로드 시 라운드 중 스냅샷 복원 미연결**(E5: 게스트 snapshot null) — 7게임이 라운드 중 복원 안 됨.
10. **[중] lpHostCtl 오버레이 문구 한국어 하드코딩**(10게임 texts 미전달) — 비한국어 게스트가 pause/end 에서 한국어. i18n 정책 위반.
11. **[중] 초대(lpInvite)↔방(lpRoom) 데이터 미연결** — 수락해도 방 코드 없는 URL 로 이동, 자동 참가 실패. "초대로 같은 방" 기대 붕괴.
12. **[중] 방 UI 3~4중 중복**(pill+패널+⏸⏹바+초대pill) — 로스터·방닫기·코드 중복, 좁은 폰 상충. 통일의 최대 정리 대상.
13. **[중] 4개 방 스택(A/B/C/D) 코드형식·PIN·신뢰모델 전부 상이** — 공통 포맷 불가의 근본. 특히 코드형식 6영숫자 vs 6숫자로 홈 단일 join 불가.
14. **[중] SZX `disconnect(true)`→즉시 `connect()` 가 supabase channel 토픽 dedupe 로 죽어가는 채널 재사용, 재subscribe 침묵**(E4). 재연결 무음 실패 창.
15. **[중] presence 전역 단일 채널 + presence 20/s(무료) 한도** — DAU 증가 시 broadcast 보다 먼저 포화, 개인정보 전체 방송. 친구별 분할 로드맵 필요.

(차순위: 게임목록 4중 정의 불일치, lpMultiplayer 결과버튼 셀렉터 6게임 하드코딩(보드게임 방깨짐), unlock 미호출, lpSocial getFriends 직접 SELECT 모바일 무음실패, `bingo_winners` 죽은 이벤트, `_waitForLpRoom` 보일러플레이트 12중복.)

---

## 부록 — 실험 파일(infra/)
`harness.mjs`(vm 탭 + REST/Auth 차단), `e1_spoof.mjs`/`E1_RESULT.txt`(스푸핑·유출·PIN·navigate), `e2_pid.mjs`(같은pid 루프·호스트크래시·채널dedupe), `e4_dedupe.mjs`(재구독 no-op), `e5_refresh.mjs`(lock 후 새로고침·호스트리로드 복원), `e7_gap.mjs`(seq-gap 폭풍). 전부 실제 vendor+lpRoom 코드 구동, 방코드 `ZZTEST*`, 프로덕션 쓰기 0(차단 로그 `blockedRest:0`=REST 미접촉).
