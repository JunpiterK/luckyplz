# 랜덤뽑기·결정 도구 — "같이 보기 방 + 검증 가능한 공정 추첨" 감사

작성: 2026-09-30 · 범위: `public/games/{roulette,team,ladder,lotto,bingo,car-racing,dice,balloon,glory-racing}` + 공용 `public/js/lpRoom.js`, `lpShare.js`, `lpInvite*.js`, `recentResults.js`, `groups.js`. READ-ONLY. 라이브 2-페이지 CDP 실험(헤드리스 Edge, `server.py` 127.0.0.1:8302, 방코드 `ZZTEST*`) 병행. 프로덕션 쓰기(GA·`log_game_play` RPC 등)는 전부 차단하고 GET 만 통과시킴.

---

## 0. 한눈에 — 현재 상태 매트릭스

| 도구 | 방(host/guest) | 동기화 방식 | 게스트가 보는 것 | 늦참/재접속 | 공유결과 링크 | 위조가능? |
|---|---|---|---|---|---|---|
| **roulette** | ✅ lpRoom | host가 tick(20Hz) 각도 broadcast, 게스트는 물리 안 돌림 | 호스트 각도 그대로(실측 **바이트 동일**) | snapshot=설정만, spin 중 늦참은 lock 으로 차단 | `?winner=` (표시용) | 링크 위조 사소, 방 결과는 host신뢰 |
| **team** | ✅ lpRoom(직접 hostCreate) | drawQueue 1회 + landed 카운트 + result ×3 | 호스트 큐 재생→같은 팀 | snapshot=현단계 전체, catchUp() | 없음 | host신뢰 |
| **ladder** | ✅ lpRoom | 토폴로지(rungs) config + start + result override | 호스트 사다리 그대로, 자기캔버스 스케일 | snapshot=config, start시 lock | 없음 | host신뢰 |
| **lotto** | ✅ lpRoom | config + lotto_begin/capture/result 스트림 | 공 하나하나 host가 준 label | snapshot=capturedBalls tally | 없음 | host신뢰 |
| **bingo** | ✅ lpRoom + **DB(bingo_winners)** | host:action{bingo_draw n} + 승자 postgres_changes | 같은 뽑힌 번호, 자기 카드는 seed 로 로컬생성 | 카드 localStorage 복원 + 뽑힘 재생 | 없음 | **승자 클레임 위조 가능(아래 H4)** |
| **car-racing** | ✅ lpRoom | host:start(트랙전체)+tick(20Hz 전체 상태)+result | host 좌표 그대로 렌더, 물리 안 돌림 | tick 이 상태 재확립 | 없음 | host신뢰 |
| **dice** | ❌ **방 없음** | — | — | — | `?winner=` 표시용 | 방 자체가 없음 |
| **balloon** | ❌ **방 없음** | — | — | — | 없음 | 방 자체가 없음 |
| **glory-racing** | ❌ **방 없음**(supabase도 미로드) | — | — | — | 없음 | 방 자체가 없음 |

핵심 결론 3줄:
1. **9종 중 6종(roulette·team·ladder·lotto·bingo·car-racing)은 이미 "같이 보기"가 있고 잘 돈다.** 실험에서 룰렛 게스트의 `angle` 이 호스트와 **소수점 15자리까지 동일**(2.025267635737094)했다 — 같은 화면이 실제로 재현됨을 라이브 확인.
2. **dice·balloon·glory-racing 3종은 방 배선이 0.** 운영자 목표("모든 게임 공통 방 포맷")를 채우려면 이 3종에 lpRoom 을 붙여야 한다.
3. **현재 신뢰 모델은 "호스트를 믿어라"다.** 결과는 전적으로 호스트 기기의 `Math.random()` 이 정하고, 게스트는 받아 그린다. "다 같이 목격·인증"의 *목격*은 되지만 *인증(호스트가 조작 안 했다는 증명)*은 안 된다. commit-reveal 이 빠져 있다.

---

## 1. 공용 방 인프라 — `lpRoom.js` (3592줄, 잘 만들어짐)

**전송:** Supabase Realtime **broadcast** 채널 `lp-room-<CODE>` (lpRoom.js:178). DB 쓰기 없음(빙고 승자만 예외), 무료티어 친화. 채널당 `{broadcast:{self:false,ack:false}}`.

**신뢰 모델(파일 헤더 주석, lpRoom.js:11–16):** 채널은 **공개**다 — 코드만 알면 누구나 subscribe. PIN 은 호스트의 join 핸들셰이크에서만 검증(:483 `p.pin!==pin`→`bad_pin`). 즉 **PIN 은 로스터/게임UI 진입만 막고, 채널 와이어 접근은 못 막는다.** 실험에서 잘못된 PIN(9999) 게스트는 `_lpGuest` 가 안 붙었고(호스트 로그 `pin_ok=false`) 결과도 렌더 안 됐지만, 원시 subscribe 자체는 성립한다 → **기밀성 한계(H5)**.

**성숙한 하드닝(이미 구현됨, 되돌리기 금지):**
- 시퀀스 넘버(`_seq`)로 갭 감지→즉시 snapshot 재요청(lpRoom.js:1549), tick 은 제외(best-effort).
- snapshot 신선도(`_seqAtSnap`)로 늦게 온 오래된 snapshot 드롭(:1526).
- critical 이벤트 `_id` + 3회 재전송 + LRU 디듀프(host:close 등, :916 broadcastReliable).
- 하트비트 5s + 워치독 12s→재동기, visibilitychange 재동기(:1338, :1360).
- RTT(host:ping/pong) + 호스트 시계 skew 샘플링(NTP식 median, :1330) — **`g.skew()` 가 이미 있다**. 아래 §4 시계동기 설계가 이 위에 바로 얹힌다.
- 게스트 liveness hb 4s, stale 15s 드롭, 투명 재접속(같은 pid/nick), host epoch 로 호스트 재시작 감지(:1218, item 14/15).
- Web Lock 으로 "방당 호스트 1명"(item 16), 세션 재개(tryResumeHost, :3396), kick+ban(item 19).

**pid(영속 기기 ID):** `getLpPlayerId()`(supabase-config.js:12, localStorage `lp_pid`). 익명·기기귀속. 인증 사용자면 `_lpAuthSignature()`(:333)로 authed 뱃지.

**공유링크(shareUrl, lpRoom.js:1074):** `<원본URL>?room=<CODE>` 만. PIN 은 별도 전달(팀만 :3395 에서 `&pin=` 을 링크에 실음). 자동참가: `detectAutoJoinParams()`(:3352) 가 `?room/&pin/&nick` + sessionStorage 핸드오프를 읽음.

**홈/로비 흐름:** `showHostModal({fromHome:true})`→gameId `lobby`, 게스트는 `/lobby/` 에서 대기, 호스트가 게임 고르면 `transferTo()`(:1046)로 `host:navigate` 브로드캐스트, 게스트가 URL 따라감. **게임 간 방 이동 인프라가 이미 있다.**

---

## 2. 게임별 — 결과 생성 위치·동기화·위조

### roulette (`games/roulette/index.html`)
- **결과 생성:** 호스트 기기 물리. `doSpin()`:1291 `velocity=19+Math.random()*4`, 감속 물리로 착지칸 결정. **시드 없음, `Math.random()` 17곳.**
- **동기화:** host가 `host:spin_start`(:1825)→`host:tick{angle,flapperAngle}` 20Hz(:1832)→`host:result{winner,finalAngle}`(:1836). 게스트는 물리 정지, `_lpTickBuf` 에 버퍼링 후 100ms 지연 lerp 렌더(:1875, Valve Source 패턴). **게스트는 각도를 받아 그릴 뿐 스스로 안 뽑는다** → 화면 일치 보장. 실측 확인.
- **늦참:** spin 시작 시 `window._lpHost.lock()`(:1819) → 이후 join 은 `reason:'locked'`. snapshot 은 설정(players)만.
- **공유링크:** `buildShareButtons()`:1442 `?winner=<name>` — **순수 표시용, 서명 없음, 자명하게 편집가능**(주소창에서 이름 바꾸면 끝). recentResults 도 같은 URL(:1422).

### team (`games/team/index.html`, 3992줄)
- **결과 생성:** 호스트가 `buildTeams()` 로 팀 확정, `teamDrawQueue`(capsuleIdx→teamIdx) 생성. `Math.random()` Fisher-Yates 셔플(:2725,:2789). **시드 없음.**
- **동기화:** `_tmHostStart()`:3411 `host:start{drawQueue,members,...}` 1회 → `host:state{landed}` 진행수 → `broadcastReliable('host:result')` ×3(:3657). 게스트 `_tmGuestDraw()`:3512 가 **큐를 그대로 재생**해 같은 팀 재구성. 연출 RNG(플링코 공 경로)는 기기마다 달라도 착지 팀은 큐가 확정.
- **늦참/재접속:** `_tmSnap()`:2684 이 "현재 단계 전체"(setup/draw+landed/result) 스냅샷 → `TD.catchUp(landed)` 로 따라잡음. 잠그지 않음(늦참도 같은 결과 봄).
- **공유링크:** 결과 공유 URL 없음(recentResults 만, :2933).

### ladder (`games/ladder/index.html`)
- **결과 생성:** `generateLadder()`:885 가 rung 배치를 `Math.random()` 로 생성(:907,:922,:925). **시드 없음.** 결과는 사다리 토폴로지 + 시작칸 매핑에서 결정론적으로 나옴.
- **동기화:** `_lpBroadcastConfig()`:1945 가 `ladder`(verticals/horizontals/rungs)+names+results 를 config/snapshot 로. **게스트는 절대 재생성 금지**(:1531 주석 명시) — 호스트 토폴로지를 받아 자기 캔버스 크기로 `layoutLadder()` 재배치. `host:start`→`host:action{ladder_spawn}`→`host:result{matchResults}` override(:1925)로 최종 결과를 바이트 단위로 강제 일치.
- **늦참:** start 시 lock. snapshot=config.
- **공유링크:** 없음.

### lotto (`games/lotto/index.html`, 2989줄)
- **결과 생성:** 호스트 matter-js 물리 드럼이 공 흡입(`captureBall`:1268). instant 모드는 Fisher-Yates(`instantDraw`:1793). **시드 없음, `Math.random()` 17곳.**
- **동기화:** host 가 `host:action{type:lotto_capture,label,color,isBonus}` 를 공마다 broadcast(:1307), 게스트는 자기 물리와 무관하게 **호스트가 준 label 을 트레이에 미러링**. `lotto_begin`/`lotto_set_reset`/`host:result{numbers}`(:2645). 게스트 물리 드럼은 딴 RNG 로 돌지만 뽑힌 번호는 host 권위.
- **늦참:** snapshot 에 `capturedBalls`(러닝 tally)+`drawing` 플래그(:2688) → 중간 참가자도 현재 트레이 복원.
- **초대:** `lpInviteButton.js` pill 사용(:171). 공유결과 링크 없음.

### bingo (`games/bingo/index.html`, 2685줄) — **유일하게 DB 사용**
- **뽑기 생성:** 호스트 `performDraw()`:1266 `remaining[Math.floor(Math.random()*remaining.length)]` → `host:action{bingo_draw,n,seq}` broadcast(:1279). **시드 없음.**
- **카드 생성:** `generateCard(seed)`:1415 는 **mulberry32 시드 PRNG**(:1409) — 유일하게 결정론적. seed = `genSeedFromString(nick+size+Date.now()+Math.random())`(:1855) → 사실상 기기 로컬 랜덤 시드. 카드는 pid 키로 localStorage 복원(:1665).
- **승자 인증:** **`bingo_winners` DB 테이블**(supabase/schema.sql:72). 각 클라가 빙고 시 INSERT(`claimWin`:1740), 전원 `postgres_changes` 구독으로 승자 리스트 재구성(:1626). unique(room_code, lower(nickname)) 로 디듀프, 100인 클레임 폭주도 postgres 직렬화로 처리. **뽑힌 번호 자체는 broadcast(휘발), 승자만 DB.**
- **위조(H4):** RLS INSERT 정책이 **완전 개방**(schema.sql:102–109) — `room_code` 3~12자, `nickname` 1~30자, `at_draw`/`lines` 범위만 검사. **아무나 방코드만 알면 임의 nickname·lines 로 승자 INSERT 가능.** 서버가 "이 사람이 정말 그 카드로 그 번호를 다 맞췄나"를 검증하지 않는다. 내기·벌칙 도구에서 이건 실질 위조 벡터.
- **공유링크:** 없음.

### car-racing (`games/car-racing/index.html`, 8465줄)
- **결과 생성:** 호스트 물리(`updatePlayers`:2993). LPFX 풍경만 시드 rng(:5681), **레이스 결과는 `Math.random()` 69곳, 시드 없음.**
- **동기화:** `host:start`(트랙 전체 좌표+차 config, `_lpCaptureRaceStartPayload`:7632)→`host:tick` 20Hz(:7686, 차 위치/상태/발사체/그물/충격파 등 렌더 전부 ~7KB)→`host:result`. 게스트 물리 정지, host 좌표 렌더만.
- **늦참:** tick 이 매 프레임 상태 재확립(별도 lock 불필요).
- **공유링크:** 없음.

### dice / balloon / glory-racing — **방 없음**
- **dice** (1177줄): `Math.random()` 26곳, `roll` 값 `Math.floor(Math.random()*6)+1`(:714,:798). lpRoom·supabase 배선 0. 공유는 `?winner=` 표시용만(:841). **같이 보기 불가.**
- **balloon** (1375줄): `drawBurst()`:630 이 숨은 파열점 분포(평균~12) 로컬 생성, `burstAt`. supabase 로드 안 함, 방 0. **로컬 턴제 전용, 온라인 불가.**
- **glory-racing/Brawl Run** (4082줄): `Math.random()` 78곳, supabase 참조 0, lpRoom 0. **완전 오프라인.**

---

## 3. 지금 코드의 구멍 (holes) 목록

- **H1 — 3종 방 부재.** dice·balloon·glory-racing 에 공통 방 포맷이 없음. 운영자 목표 미달의 핵심.
- **H2 — 결과 무결성 증명 없음(전 게임).** 결과는 호스트 `Math.random()` 산출. 게스트는 목격만 하고, 호스트가 "10번 돌려 마음에 드는 걸 result 로 broadcast" 해도 알 방법이 없다. commit-reveal·검증 부재. **이게 "인증"의 핵심 결손.**
- **H3 — 공유 결과 링크 위조.** `?winner=<name>` 은 서명 없는 표시 파라미터. 누구나 편집해 "내가 이겼다" 스크린샷 링크 제조 가능. (단 현재 이 링크는 방 결과와 무관한 마케팅용이라 피해 경미.)
- **H4 — 빙고 승자 클레임 위조.** `bingo_winners` INSERT RLS 완전 개방(schema.sql:102). 방코드만으로 임의 승자 위조 INSERT. 서버 검증 없음.
- **H5 — 채널 기밀성.** 방코드를 아는 제3자는 PIN 없이도 broadcast 와이어를 subscribe 로 도청 가능(이름·설정·결과 노출). 게임UI 진입만 PIN 게이트.
- **H6 — 시드 리플레이 불가(빙고 카드 제외).** roulette/lotto/car-racing 은 게스트가 host tick 없이는 애니메이션을 스스로 못 만든다(같은 시드로 독립 재생 불가). 네트워크가 끊기면 "같은 애니메이션"이 깨지고, 나중에 "그때 그 추첨"을 재검증할 수 없다.
- **H7 — 시계 동시 출발 없음.** 게스트는 호스트 tick 을 따라가므로 ~100–200ms 지연 렌더. 각자 폰에서 "동시에 카운트다운→발사"가 물리적으로 동기화되진 않는다(현재는 host-follow 라 크게 문제 안 되지만, 시드 리플레이로 가면 필요).
- **H8 — team 직접 hostCreate 는 초기 snapshot 공백.** 실험 로그 `NO snapshot to send (currentSnapshot null)` — 설정 전 참가자는 첫 config broadcast 까지 빈 화면. (경미, config 곧 도착.)

---

## 4. 최신 기법 리서치 — 정적 사이트 + Supabase 무료티어에서 실현 가능한 "검증 가능한 공정 공유 랜덤"

### 4-A. Commit–Reveal (핵심 권장, 무료·자명)
표준 커밋-공개 방식. 호스트가 **뽑기 전에** 시드의 해시를 공개하고, **뽑은 뒤** 시드를 공개해 모두가 `hash(seed)==commit` 을 재계산·검증한다. 호스트가 결과를 미리 보고 고를 수 없다(해시를 이미 공개했으므로 시드를 못 바꿈).
- **참가자 엔트로피 결합(호스트 단독 통제 제거):** 커밋 단계에서 각 게스트가 자기 nonce 를 broadcast. 최종 시드 = `SHA256(hostSeed ‖ nonce₁ ‖ nonce₂ ‖ …)` (정렬된 pid 순). 호스트도 게스트도 단독으로 결과를 정하지 못한다(라스트-리비저 문제는 호스트 커밋을 먼저 잠그면 해소). 브라우저 `crypto.subtle.digest('SHA-256', …)` 만으로 구현, 라이브러리 0.
- **비용/UX:** DB 불필요(broadcast 로 commit/reveal 주고받으면 됨). UX 는 뒤에서 조용히 — 사용자는 결과 화면에 **"✓ 검증됨 · N개 화면 동일"** 배지만 본다. 탭하면 commit·seed·재계산 결과 펼침(감사용).

### 4-B. 공개 랜덤 비컨 (drand / NIST) — 실측 가능
브라우저에서 직접 fetch 확인함(2026-09-30, Origin: luckyplz.com):
- `https://api.drand.sh/public/latest` → **200, `Access-Control-Allow-Origin: *`**, `{round, randomness, signature}`. `drand.cloudflare.com` 도 동일 200/ACAO:*. `api.drand.sh/info` 로 체인 period 획득 가능(기본 League of Entropy 30s; quicknet 3s 체인 별도).
- `https://beacon.nist.gov/beacon/2.0/pulse/last` → **200, ACAO:***, 서명된 pulse.
- **즉 CORS 문제 없이 정적 브라우저에서 검증 가능한 공개 엔트로피를 가져올 수 있다.** 용도: "호스트가 미래 라운드 R 을 지목→그 시각 아무도 결과를 모름→R 이 발표되면 그 randomness 로 뽑음"이면 **호스트조차 결과를 선점 못 함**(비컨은 제3자·서명검증). 단 다음 라운드까지 최대 30s 대기(quicknet 쓰면 3s). drand 서명 검증은 BLS(무거움) — MVP 는 "randomness 값 그대로 시드로 사용 + 링크에 round 번호 기재"만 해도 제3자가 나중에 재검증 가능.
- **권장:** 기본은 4-A(commit-reveal, 즉시·오프의존 0), 옵션으로 "🎲 공개 비컨 모드"(drand round) 를 고급 사용자용으로. 비컨은 외부 의존·지연이 있어 기본값으론 부적합.

### 4-C. 결정론적 애니메이션 리플레이 (H6 해결)
시드가 정해지면 **모든 기기가 같은 시드로 같은 애니메이션을 독립 생성**하도록 각 게임의 `Math.random()` 을 시드 PRNG 로 교체(빙고는 이미 mulberry32 보유 — 패턴 재사용). 그러면:
- host tick 스트림 없이도 게스트가 스스로 동일 화면 렌더 → 대역폭 급감, 네트워크 끊겨도 결과·애니메이션 동일.
- 나중에 "seed=X 로 재생"하면 그때 그 추첨을 **누구나 재현·검증**. 이게 진짜 "인증".
- 비용: 게임별 RNG 주입 리팩터(룰렛·주사위·사다리·풍선은 쉬움; lotto/car-racing 물리는 float 결정론성 주의 — 같은 엔진·같은 dt 스텝 고정 필요). 룰렛은 이미 host-follow 라 낮은 우선순위, dice·balloon·ladder·team 은 리플레이가 자연스럽다.

### 4-D. 시계 동기(동시 출발, H7)
`lpRoom` 이 **이미 host-clock skew median 을 `g.skew()` 로 노출**(NTP식 샘플, lpRoom.js:1330). 호스트가 `host:start{startAtHostTime=now+700ms}` 를 broadcast → 각 게스트가 `startAtHostTime - skew` 로컬시각에 애니메이션 개시 → **모든 폰에서 사실상 동시 발사**. 추가 인프라 0, 기존 skew 재사용.

### 4-E. 변조 방지 결과 인증서(선택, 저비용)
결과를 나중에 링크로 재검증하려면 한 줄 DB row 또는 Edge Function 서명:
- **경량(무료·권장 시작점):** 결과 시 `{gameId, seed, commit, participants, result, ts}` 를 broadcast 이미 하므로, 공유 링크를 `?cert=<base64url(JSON)>` 로 바꾸고 페이지가 로드시 `commit==hash(seed)` & `result==replay(seed)` 를 **클라에서 재계산**해 "✓ 검증됨" 표시. 서버 불필요, 위조는 재계산 실패로 즉시 탄로(H3 해결).
- **강력(선택):** Supabase Edge Function(kakao-token 처럼 이미 배포 경험 있음)이 결과를 받아 HMAC 서명 + `draw_results` row 저장, 링크 `?rid=<uuid>` 가 서버 재검증. 무료티어 Edge Function 로 충분. 빙고 승자도 이 RPC 로 옮기면 H4 동시 해결(서버가 draw seed 로 승리조건 재계산 후에만 승자 확정).

---

## 5. 권장 설계 — 도구별 (호스트가 하는 일 / 게스트가 보는 것 / 저장되는 것)

**공통 레이어(lpRoom 에 1회 추가, 모든 게임 공유):**
1. `LpRoom.fairDraw(room, {contributors})` 헬퍼 추가:
   - 호스트: `hostSeed=crypto.getRandomValues`, `commit=SHA256(hostSeed)` 를 `host:commit` broadcast(lock).
   - 게스트: `guest:nonce` 회신(참가자 엔트로피).
   - 호스트: 모두 모이면 `finalSeed=SHA256(hostSeed‖정렬된 nonce들)`, `host:reveal{hostSeed,nonces}` broadcast.
   - 전원: `commit` 재검증 + `finalSeed` 로 **결정론 PRNG** 시드 → 각자 동일 애니메이션(4-C) + `g.skew()` 동시출발(4-D).
2. 결과 화면 공통 컴포넌트: **"✓ 검증됨 · N개 화면 동일"** 배지 + 탭시 seed/commit/재계산 패널 + `?cert=` 재검증 링크(4-E 경량).

**도구별:**
- **roulette:** 착지각 = `finalSeed`→PRNG 로 velocity·hold 산출. 호스트가 tick 을 계속 보내되(부드러움), 최종각은 seed 에서 결정론적으로 검증. 게스트는 "이 seed 면 정말 Alice"를 재계산.
- **dice(신규 방):** lpRoom 붙이고 눈금 = PRNG(finalSeed). 가장 쉬운 리플레이 대상 — 각 주사위 값 seed 에서 바로. 공유 `?cert=` 로 "3,5,6" 재현.
- **ladder:** 이미 토폴로지 broadcast. 토폴로지 생성을 `finalSeed` PRNG 로 → 게스트가 자체 생성해도 동일, host 신뢰 제거.
- **team:** drawQueue 를 `finalSeed` 셔플로 → 게스트가 큐를 스스로 재계산·검증(현재는 host 큐 신뢰).
- **balloon(신규 방):** 파열점 분포를 `finalSeed` 로 커밋 → "호스트가 나한테만 12에서 터지게 했나?" 의심 제거. 턴제 그대로 broadcast.
- **lotto:** 뽑힌 번호 집합 = `finalSeed` Fisher-Yates 로 커밋-공개. 물리 드럼은 연출(각 기기 로컬), 결과는 seed 검증. 현재 capture 스트림 유지하되 최종 검증 레이어 추가.
- **bingo:** ① 뽑기 순서를 `finalSeed` PRNG 로(커밋-공개) → 게스트가 다음 번호를 스스로 예측 못 하지만 끝나면 전 순서 재검증. ② **승자 확정을 Edge Function 으로**(H4): 서버가 `finalSeed`+카드seed+claim 을 받아 승리조건 재계산 후에만 `bingo_winners` 확정, RLS INSERT 는 서버 role 만 허용. 카드 seed 도 `SHA256(finalSeed‖pid)` 로 만들면 "내 카드는 방 시드에서 파생"이 검증됨.
- **car-racing / glory-racing(후자 신규 방):** 물리 float 결정론이 어려워 **완전 리플레이는 비용 큼**. 절충: 레이스 seed 를 commit-reveal 로 커밋(호스트가 유리한 결과를 재추첨 못 함) + 기존 host tick 렌더 유지. 순위 결과만 seed 에 바인딩해 사후 검증.

**저장(무료티어 원칙 유지):** 기본은 **아무것도 DB 에 안 씀**(broadcast commit-reveal + 클라 재검증). 영구 인증서·리더보드가 필요한 빙고만 Edge Function+row. drand 비컨 모드는 옵션(외부 fetch).

**UX 원칙(운영자 스타일 부합):** 글자 늘리지 말 것 — 결과 화면엔 배지 1개(✓ 검증됨 · N개 화면 동일)만. 상세는 접힘. commit/seed 문자열은 사용자에게 강요하지 않고 "이게 뭐야?" 탭에만.

---

## 6. 우선순위 제안
1. **P0 — 공통 방 포맷을 dice·balloon·glory-racing 에 이식**(H1). lpRoom 은 이미 게임 독립적이라 룰렛 배선(약 60줄)을 복붙+게임 훅만 맞추면 됨.
2. **P0 — `LpRoom.fairDraw` commit-reveal 레이어**(H2) + 결과화면 "✓ 검증됨" 배지. DB 0, 브라우저 crypto.subtle 만. 전 게임 공통.
3. **P1 — 결정론 PRNG 리플레이**(H6): dice→ladder→team→balloon→lotto 순(쉬운 것부터). 룰렛/레이싱은 후순위(host-follow 로 이미 동작).
4. **P1 — 빙고 승자 Edge Function 검증**(H4) + `?cert=` 경량 재검증 링크(H3).
5. **P2 — 시계 동시출발**(`g.skew()` 재사용, H7), drand 옵션 모드.

부록: 라이브 실측 근거 — 룰렛 게스트 `angle` == 호스트 `angle` (2.025267635737094, 15자리 일치); 잘못된 PIN 거부(`pin_ok=false`); team/ladder 게스트 accept 확인; drand·NIST 비컨 ACAO:* 200 확인. 실험 스크립트: scratchpad/mp/exp_roulette.mjs, exp_team_ladder.mjs, cdp.mjs.
