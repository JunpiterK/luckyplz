# 같이 하는 게임 — 멀티플레이 감사 (범위 A) + 최신 기법 리서치 (범위 B)

작성 2026-09-30 · 읽기 전용 감사(저장소 수정 없음) · 기준 코드 = `main` 작업 트리
재현 스크립트: `scratchpad/mp/ga/` (`h.mjs` 하네스, `t_ludo.mjs` `t_yut.mjs` `t_rv.mjs` `t_gummy.mjs`)
— 헤드리스 Edge(`--headless=old`), `server.py` 127.0.0.1:8303, Supabase REST/auth/storage/functions·GA 차단(Realtime 브로드캐스트만),
방 코드는 CDP Fetch 로 lpRoom.js 를 메모리에서만 바꿔 `ZZTEST???` 로 강제. 테스트 뒤 프로세스·프로필 정리 완료.

---

## 0. 결론 먼저

**"배틀넷 같은 대기 공간이 있나?" → 반쯤 있다. 하지만 하나가 아니라 넷이고, 서로 안 이어진다.**

| 방 시스템 | 쓰는 곳 | 코드 형식 | 비밀번호 | 기기 id 키 | 닉네임 키 | 권위 |
|---|---|---|---|---|---|---|
| **lpRoom** (`public/js/lpRoom.js`) | 뽑기 7종 + 윷·루도·리버시·프리즘헥스·마작·구미 | 영문숫자 6자 (`genCode`, lpRoom.js:173) | 4자리 PIN | `lp_pid` (supabase-config.js:12) — 리버시는 탭별 `lp_rv_cid`(reversi:613), 마작은 탭별 `mjtw_kid`, 윷은 같은 브라우저면 탭별 `yut_tabpid` | `luckyplz_nick` | 방장 기기(브로드캐스트, DB 없음) |
| **퀴즈 라이브** (`qlive_*` RPC) | 퀴즈 | 숫자 6자리, 서버가 중복 검사 (`2026-09-24-quiz-live-v2.sql` qlive_create) | 없음 | `lp_qlive_pid` | `lp_qlive_nick` | **서버(DB)** — 채널은 '다시 읽어' 신호만 |
| **SZX 동시 대결/협동** (dodge) | 스페이스-Z 8인 레이스·2인 협동 | 숫자 6자리, 중복 검사 없음 (dodge:22426) | 없음 | `szx_pid` | `szx_nick` | **없음(대칭 P2P)** — 각자 자기 상태 자기 신고 |
| **스페이스-Z 1:1 PvP** (`spacez_*` RPC) | 로그인 1:1 | DB 코드 | 로그인 | 계정 | 계정 | DB + 브로드캐스트 |

- 홈의 "방 참가" 창(lpRoom `showHomeJoinModal`)은 **lpRoom 방만** 찾는다(`probeRoom`). 퀴즈·SZX 코드를 넣으면 "방 없음"으로 막힌다. 목록엔 멀티가 없는 `bubble` 까지 들어 있다 (lpRoom.js:3314).
- 방장 게임 전환(배틀넷의 '파티가 같이 이동')은 lpMultiplayer 패널에 있지만 **뽑기 7종만** (lpMultiplayer.js:111-119). 보드게임 6종은 목록에 없어, 윷 한 판 뒤 같은 친구들과 루도로 넘어가려면 방을 새로 만들어 링크를 다시 보내야 한다.
- `/lobby/` 는 "방장이 게임 고를 때까지 기다리는 빈 화면" (lobby/index.html:99-130) — 명단·채팅·준비·게임 투표 없음.
- **윷놀이의 새 흐름(캐릭터 선택·준비·시작 게이트·내보내기/차단·턴 시간·재접속·봇 대행)은 윷 파일 안에만 있다** (yut:2362-2720). 다른 5개 보드게임은 그 이전 세대 흐름(자동 착석·즉시 시작·준비 없음·내보내기 없음)이다.

**구멍 요약 (실측 재현 4건 + 코드 확인)**
1. **다른 사람 사칭이 된다** — lpRoom 이 게스트 행동에 붙이는 `nickname`/`pid` 를 페이로드가 덮어쓸 수 있다(lpRoom.js:1769 `Object.assign({gid,nickname,...},payload)`), 방장은 이를 그대로 믿는다. 루도: Bob 이 Ann 차례에 Ann 이름으로 주사위를 굴림 ✅재현. 윷: Bob 이 Ann 의 '준비'를 켜고, Ann 을 대기실에서 쫓아냄 ✅재현(쫓겨난 Ann 은 연결된 채 명단에서 사라진 유령이 됨).
2. **폰을 잠깐 내려놓으면 자리를 뺏긴다** — 리버시: 백 플레이어가 21초 백그라운드 → 관전자가 '백으로 앉기' 한 번에 자리 차지, 원래 사람은 돌아와도 관전자 ✅재현.
3. **9초 앱 전환 = 기권패, 그리고 양쪽 다 이김** — 구미 대전: 상대 11초 백그라운드 → 방장 승리 처리, 돌아온 상대 화면도 `result:'win'` ✅재현(결과 불일치).
4. **방장이 사라져도 게스트는 모른다** — 루도: 방장 40초 동결 동안 게스트 화면은 "Bob의 선택을 기다리는 중"·핑 154ms 그대로 ✅재현. lpRoom 에 '방장 끊김' 이벤트가 없어(가드 12초 뒤 스냅샷 요청만, lpRoom.js:1338-1352) 윷·SZX 외에는 각 게임이 알아서 안 챙긴다.
5. **내보내기(차단)는 저장소만 지우면 뚫린다** — 윷에서 kick+ban 뒤 `lp_pid` 삭제 후 재참가 성공 ✅재현. (계정 없는 캐주얼 사이트의 한계 — 아래 P1 에서 완화책)
6. **PIN 이 공개 채널에 평문으로 흐른다** — `guest:join_request` 에 `pin` 이 실려(lpRoom.js:1201) 같은 코드 채널을 구독한 누구나 본다. 방장 스냅샷도 채널 전체로 나간다. 코드만 알면 PIN 은 사실상 장식.
7. **무료 한도 예산이 빠듯하다** — 4인 대기 중인 방 하나가 초당 ~11 메시지(아래 §3.1). Supabase 무료 = 초당 100·월 200만 → **동시 대기방 ~9개, 월 ~50 방-시간**이면 한도.

---

## 1. 게임별 감사

표기: ✅ 있음 · ⚠️ 부분/문제 · ❌ 없음. "윷 대비"는 2026-09-29 윷 개편 기준.

### 1.1 윷놀이 `public/games/yut/index.html` — 현재 사내 최선 사례

- **참가**: 자체 참가 화면(scrJoin). 링크 `?room=&pin=&nick=` 이면 자동, 코드만이면 PIN·이름 입력. 응답 없음은 4/7/9초로 3번 재시도, `wrong_game` 이면 `probeRoom` 으로 그 게임 페이지로 보냄 (yut:2655-2685). 새로고침하면 `sessionStorage.yut_room` 으로 자동 재참가(yut:2640).
- **대기실**: 방장 원장 `LB`(yut:2377). 캐릭터 선택(남이 고른 건 잠김, 봇 것은 맞바꿈 `lbPick`), 게스트 '준비', 봇 추가/삭제, 턴 시간 15/30/60초, **시작 게이트 = 2석 이상 + 게스트 전원 준비** (`lbCanStart` yut:2456). 5번째 사람은 관전석(`spec`), 자리가 나면 자동 승격.
- **동기화**: 방장 권위 + 게스트는 의도만(`guest.action('yut',{a:...})`). 방장은 **전체 상태를 매번 통째로** `host:state` + `room.snapshot` (yut:1277-1283). `seq` 로 순서, 연속이면 애니메이션·아니면 바로 스냅(yut:2697-2703). 표시 큐가 4개 넘으면 연출 건너뜀(yut:1403).
- **턴 시간**: 모든 기기가 '연출이 끝난 순간'부터 센다 → 추가 방송 없음(yut:2600-2625). 초과 = 자동 두기, 2번 연속이면 `afk=2` → 봇이 맡음, '내가 할게요'로 복귀.
- **끊김**: 게임 레벨 hb 4초 + lpRoom presence. 10초 무소식 = '끊김', 8초 뒤 봇 대행(`botDrives` yut:1259), 대기실에선 30초(숨김 120초) 뒤 명단에서 제거. 방장 visibilitychange → 게스트에 '방장 잠시 다른 앱' 띠.
- **방장 이탈**: 새로고침·탭 복원은 `tryResumeHost` + `saveSnapshot` 으로 이어짐. 말없이 사라지면 '방장 끊김' 띠만, **방장 승계 없음**(주석 yut:2371-2374에 의도적 결정으로 명시).
- **내보내기**: `room.kick(+ban)` + 상태의 `ban` 목록 이중 통지, '다시 허용'.
- **다시 하기**: 방장 '한 판 더' → 같은 캐릭터로 대기실, 게스트 준비 초기화(`toLobby` yut:2566).
- **구멍**
  - ⚠️ **사칭**: `onIntent` 가 페이로드의 `p.pid` 를 신원으로 쓴다(yut:2522-2560). 재현: Bob 이 `{a:'ready',v:true,pid:<Ann>}` → Ann 준비 켜짐, `{a:'leave',pid:<Ann>}` → Ann 명단에서 삭제. 방장 lobbyState 가 모든 pid 를 방송하므로 pid 수집은 공짜.
  - ⚠️ 쫓겨난(또는 다른 경로로 LB 에서 빠진) 게스트는 `hb` 로는 되살아나지 않는다 — `markOff(pid,false)` 가 LB 에 없는 사람을 추가하지 않음(yut:2505-2508). 다른 행동을 해야 `lbAdd` 됨.
  - ⚠️ 게임 hb(4초)가 lpRoom `guest:hb`(4초)와 중복 — 채널 전체로 나가 메시지 한도를 두 배로 씀(§3.1).
  - ⚠️ 같은 브라우저 테스트용 탭 pid(`yut_tabpid`, yut:2691-2694)는 lpRoom 의 pid 와 달라, lpRoom 쪽에서 pid 를 강제하면 이 경로가 깨진다 → 공통화 때 "신원 = 방장이 받은 join 기록(gid→pid)" 으로 통일해야 함.
  - ❌ lpMultiplayer 패널·게임 전환 목록 밖 (hostCreate 직접 호출이라 공용 패널 이벤트를 안 탐).

### 1.2 루도 `public/games/ludo/index.html`

- **참가**: 공용 `showHostModal`/`showGuestJoinModal` (ludo:1440-1445, 1542-1546). 방장 새로고침 재개 = `tryResumeHost` + localStorage `lp_ludo_save`(30분).
- **대기실/좌석**: 4석, 들어오면 **자동 착석**(빈 'off' → 봇 자리 순, `autoSeat` ludo:1398). 게스트는 자리·색 선택 불가, 준비 없음. 방장만 좌석 순환(사람→봇→원격→끔).
- **시작**: 방장 '시작' 즉시(2석 이상). 게스트 동의 없음.
- **동기화**: 방장 권위, 전체 상태(`G`) + `aid` 번호(ludo:604-611, recv 1446). 게스트는 `{op:'roll'|'move',aid,seat}`.
- **턴 시간**: 표시 없음. 원격 차례는 **연결돼 있으면 30초, 끊겼으면 6초 뒤 봇 수**(ludo:681) — 게스트는 남은 시간을 모름.
- **끊김/재접속**: 좌석 소유 = **닉네임 문자열**(`owner===NET.myNick`). lpRoom 이 같은 기기 재참가 시 닉네임을 돌려줘서 대체로 이어진다. 대기실에서 끊기면 좌석 'off'.
- **방장 이탈**: `lp-room-closed` 로만 인지. 말없이 사라지면 ❌ 알림 없음(재현: 40초 동결 동안 게스트 화면 "Bob의 선택을 기다리는 중").
- **관전**: 자리 없으면 관전만, **게임 중 들어온 사람은 봇 자리를 이어받을 방법 없음**(재현: Cara 관전 고정, 윷·프리즘헥스는 가능).
- **다시 하기**: 방장 '한 판 더'(같은 좌석) / '설정'(대기실).
- **구멍**
  - ❌ **사칭 재현**: 방장은 `st.owner!==p.nickname` 만 본다(ludo:1428-1435). Bob 이 `nickname:'Ann'` 을 덮어쓴 action → 방장이 Ann 자리 주사위를 굴림(aid 5→6, last={t:'roll',seat:1}).
  - ⚠️ `confirm()` 사용(ludo:1519) — 인앱 브라우저에서 막힐 수 있음(윷은 자체 확인창으로 교체함).
  - ❌ 내보내기, 준비, 색 선택, 턴 표시, 방장 끊김 알림, 중도 합류.

### 1.3 리버시 `public/games/reversi/index.html`

- **참가**: 공용 모달. 초대 링크에 `&pin=` 포함(reversi:1415).
- **좌석**: 흑=방장, **첫 게스트 hello 즉시 백 착석 + 즉시 시작**(`maybeStart` reversi:1341). 방장 '색 바꾸기'는 대기 상태에서만.
- **신원**: 탭별 `sessionStorage.lp_rv_cid`(reversi:613) — 카톡 인앱에서 링크를 다시 열면(새 탭) 다른 사람이 됨.
- **동기화**: 방장 권위, 64칸 문자열 전체 + 직전 수로 검증 후 애니메이션(applyNet reversi:1364-1392). 깔끔.
- **턴 시간**: ❌ 없음 — 상대가 안 두면 영원히 멈춤.
- **끊김**: 게스트 ping 5초, 방장이 16초 무소식이면 좌석 `on:false`(reversi:1300-1306) → **관전자가 그 자리에 바로 앉을 수 있음**(reversi:1330-1333).
- **다시 하기**: 좌석 사용자 누구든 '리매치' 한 번이면 색 바꿔 즉시 시작(reversi:1337-1338, 1347) — 상대 동의 없음.
- **구멍**
  - ❌ **자리 강탈 재현**: 백 21초 백그라운드 → Cara 가 '백으로 앉기' → 좌석 Cara, 돌아온 Ann 은 '👀 관전 중'. 백그라운드 타이머 스로틀·폰 잠금에서 흔히 생기는 상황.
  - ❌ 준비·턴 시간·내보내기·방장 끊김 알림·리매치 합의.
  - ⚠️ `confirm()` 사용(reversi:1234,1462).

### 1.4 프리즘 헥스 `public/games/prism-hex/index.html` — 윷의 '이전 버전'

- **참가/좌석**: 2~6인, 방장이 인원·턴 시간(30/45/60/90/끔) 설정, 게스트가 빈/봇 자리 '이 자리 할래요'(claim), 게임 중에도 봇·끊긴 자리 이어받기 가능(prism-hex:1906-1930).
- **시작**: 방장 즉시. ❌ 준비 없음. 빈 자리는 봇.
- **동기화**: 방장 권위, 전체 상태 + `seq`, 남은 턴 시간 `S.tl` 을 상태에 실어 게스트가 받은 시각 기준으로 계산(prism-hex:941-961). 수 검증 꼼꼼(조각·모양·배치 규칙, prism-hex:1932-1940).
- **턴 시간**: 초과 = 무작위 합법 수(prism-hex:976-984). ❌ 연속 초과 → 봇 전환 없음.
- **끊김**: hb 4초, 10초 → 끊김, 그 차례면 5초 뒤 봇 대행.
- **구멍**
  - ⚠️ 사칭: 신원 = 페이로드 `p.pid`(prism-hex:1906-1912) — 윷과 같은 구조라 같은 공격이 된다(코드 확인).
  - ⚠️ `wireGuest` 의 hb `setInterval`·`pagehide` 리스너가 해제되지 않음(prism-hex:1955-1956) — 방을 여러 번 드나들면 누적.
  - ❌ 준비, 내보내기, 방장 끊김 알림(게스트 host:close 는 LpHostCtl 의존).

### 1.5 대만 마작 `public/games/mahjong-tw/index.html` — 보안은 최상

- **좌석**: 4석, 방장=0번, 게스트 자동 배정. 게임 중 합류 = 같은 이름의 끊긴 자리 → 봇 자리 순(mahjong-tw:2066-2085). ❌ 자리 선택·준비.
- **비공개 정보**: **좌석별 ECDH(P-256) → AES-GCM 으로 손패를 암호화**해 공개 채널에서도 남의 패가 안 보인다(mahjong-tw:2008-2020, netPush 2057-2068). 게스트 행동도 암호화(sendIntent) → 남이 대신 둘 수 없음.
- **동기화**: 방장 권위, 공개 상태 + 좌석별 비밀 blob, 암호화 체인 직렬화(netChain).
- **타이머**: 행동 제한 `ACT_MS`, 울기(碰·吃·槓) 창 `CLAIM_MS`, 봇 대행(`isAuto`, plan() mahjong-tw:1921-1940).
- **구멍**
  - ⚠️ `bye` 는 평문 — 남의 `kid`(hello 페이로드로 공개)로 `{a:'bye',kid}` 를 보내면 그 사람을 '끊김' 처리 → 5.2초 뒤 봇이 대신 둠(mahjong-tw:2107, 2115-2120). 피해자 hb(4초)가 곧 되돌리지만 반복 가능.
  - ⚠️ 방장은 모든 패를 안다(방장 권위의 본질적 한계) — '방장=딜러' 고지 또는 서버 딜러(Edge Function)가 유일한 해결.
  - ⚠️ 신원 탭별(`mjtw_kid` sessionStorage) — 인앱에서 링크 다시 열면 이름 일치로만 복구.
  - ❌ 준비, 내보내기.

### 1.6 구미 체인 `public/games/gummy/index.html` — 1:1 실시간 대전

- **모델**: 각자 자기 판을 시뮬, 같은 시드(`makeSeq`)로 조각 순서 동일, 연쇄 → 방해블록 이벤트(`atk`) 전송. **순번+ACK+재전송 창(24개) 신뢰 이벤트 스트림**(netSend/netFlush/netRecv gummy:2443-2475) — 잘 만든 부분.
- **참가/시작**: 첫 게스트 hello 즉시 양쪽 준비로 간주 → 방장 공유 모달이 닫히면 자동 시작(hostMaybeStart gummy:2507, 모달 열려 있으면 대기 — 헤드리스에선 모달을 닫아야 시작됐다). 시작 시 `room.lock()`.
- **3번째 사람**: "이미 게임이 시작되어 참가할 수 없어요" ✅재현 — ❌ 관전 불가.
- **끊김**: 플레이 중 **9초 무수신 = 상대 기권**(gummy:2563).
- **다시 하기**: 양쪽 '다시'(`rm`) 합의 — 좋음.
- **방장 새로고침**: ❌ `tryResumeHost` 안 씀 → 방이 죽는다.
- **구멍**
  - ❌ **결과 불일치 재현**: Ann 11초 백그라운드 → 방장 `win`, 돌아온 Ann 도 `result:'win'` (wins [1,0]). 둘 다 이겼다고 봄. 원인: 기권 판정이 각자 로컬(9초)이고, 복귀 측이 상대의 `bye`/판정을 받아 정정하는 경로가 없음.
  - ⚠️ 9초는 모바일에서 너무 짧다(알림 확인·카톡 답장). 윷은 8초 뒤 '봇 대행'이지 패배가 아니다.
  - ⚠️ 콘솔 예외: `rrect` 에 음수 반지름(`IndexSizeError`, gummy:994 ← 1131) — 트레이 높이가 4px 미만일 때 `w-4`/`h-4` 가 음수. 게스트·대기 화면에서 매 프레임 발생 가능(렌더 중단). `r=Math.max(0,…)`, `w,h≥0` 클램프 필요.

### 1.7 버블 `public/games/bubble/index.html`

- 온라인 없음(채널·lpRoom 호출 0). 그런데 홈 참가창 유효 게임 목록에 들어 있다(lpRoom.js:3314) — 정리 대상.

### 1.8 퀴즈 라이브 `public/games/quiz/index.html` — 서버 권위 모범

- **모델**: DB 가 진실원천(`qlive_state/join/answer/host` SECURITY DEFINER RPC). 채널은 `nudge`(다시 읽어)만(quiz:343-347), 폴링은 상태·가시성·마감 시각에 맞춰 적응(quiz:334-341).
- **시계 동기**: 응답 왕복 중간값 7개 → 서버 시간 오프셋(quiz:333) — NTP 방식. 마감 시각(`ends_at`)을 서버 시간으로 공유.
- **멱등 답안·자동 재참가**(`autoRejoin`, 명단에 없으면 저장된 닉네임으로 조용히 재참가), 닉네임 유일(DB unique index), 내보내기(`kicked`), 방 만들기 속도 제한(`rate_limited`, 12회).
- **구멍**: 코드 체계가 lpRoom 과 다르다(`?c=` 숫자 6자리, 홈 참가창 불가). 게임 전환 패널에는 `quiz` 가 들어 있지만(lpMultiplayer.js:118) 퀴즈 라이브는 lpRoom 방이 아니다 — 전환 시 무슨 일이 일어나는지 별도 확인 필요(뽑기 쪽 감사와 겹침).

### 1.9 스페이스-Z (dodge) — SZX 레이스(최대 8)·2인 협동·로그인 1:1

- **SZX 레이스/협동** (`R` dodge:21873~): 채널 `szx-race-<6자리 숫자>`, PIN 없음, **리더 없는 대칭 구조**. 멤버십 = 2.5초 브로드캐스트 하트비트(프레즌스 누락을 실측해 버림, 주석 dodge:21897-21904), 12초 무소식 제거. 세계는 **공유 시드 결정론**(운석을 안 보냄), 위치는 **WebRTC P2P 메시**(unordered, maxRetransmits:0), 서버는 신호·출발·결과·직통 불가 짝의 위치만. 출발 버튼 = `actingHost()`(방장 없으면 가장 먼저 온 사람, dodge:21888). 정원 초과 = **클라이언트가 스스로 나감**(dodge:21939). 방장 빌드 불일치 검사(`szBuildOk`).
  - ⚠️ 누구나 `go` 를 보내면 모두 출발(onGo 에 발신자 검사 없음, dodge:22235), 기록은 자기 신고(`t` ms) — 캐주얼엔 괜찮으나 '보상'을 붙이면 안 됨.
  - ⚠️ 숫자 6자리·중복 검사 없음 → 동시 방이 늘면 우연히 합쳐질 수 있음(90만 공간).
  - ⚠️ lpRoom·홈 참가창과 완전히 별개(닉네임 키도 `szx_nick`).
- **로그인 1:1 PvP**: DB 방(`spacez_create_room/join/set_ready/start_game`, `2026-05-03-spacez-pvp-rooms.sql`) + 채널 `spacez:room:<id>` + WebRTC. 준비·시작이 DB 에 있다 — 유일하게 '준비'가 서버 상태.

### 1.10 기타 온라인 게임(참고)

뽑기 7종(룰렛·사다리·팀·로또·빙고·카레이싱·퀴즈)은 '같이 보기'(방장 화면 중계) — 다른 감사 범위. 빙고는 추가 채널 `bingo-winners:<code>`(bingo:1624).

---

## 2. 헤드리스 재현 결과

| # | 게임 | 시나리오 | 결과 |
|---|---|---|---|
| 1 | 루도 | Bob 이 `nickname:'Ann'` 을 실어 Ann 차례 굴리기 | ❌ 방장이 수락 (aid 5→6, seat1 roll) · 대조군(자기 이름)은 거절 |
| 2 | 루도 | 게임 중 3번째 참가 | 관전 고정, 봇 자리 인계 불가 |
| 3 | 루도 | 방장 40초 동결 | 게스트에 끊김 표시 없음, 복귀 후 정상 진행 |
| 4 | 윷 | Bob 이 Ann pid 로 `ready` | ❌ Ann `ready:true` |
| 5 | 윷 | Bob 이 Ann pid 로 `leave` | ❌ Ann 명단에서 삭제, 6초 뒤에도 복귀 안 함 |
| 6 | 윷 | kick+ban 뒤 `lp_pid`·sessionStorage 삭제 후 재참가 | 재참가 성공(차단 우회) |
| 7 | 리버시 | 첫 게스트 입장 | 즉시 시작(준비·확인 없음) |
| 8 | 리버시 | 백 21초 동결 → 관전자 '백으로 앉기' | ❌ 자리 강탈, 원래 사람은 관전 |
| 9 | 구미 | 3번째 참가 | "이미 시작" 거절(관전 없음) |
| 10 | 구미 | 상대 11초 동결 | ❌ 방장 승, 복귀한 상대도 '승' |
| 11 | 구미 | 콘솔 | `IndexSizeError` arcTo 음수 반지름 (gummy:994) |

---

## 3. 공통 인프라(lpRoom) 관점의 구멍

1. **신원이 페이로드에서 온다.** 방장이 믿을 수 있는 건 `join_request` 를 받아 만든 명단(`guests` Map: gid→{nickname,pid})뿐이다. lpRoom 은 `guest:action` 을 게임에 넘길 때 `p.gid` 가 명단에 있는지만 보고(lpRoom.js:644-655) `nickname/pid` 는 게스트가 보낸 값을 그대로 넘긴다. **한 줄 수정 후보**: 콜백 직전 `p.nickname=g.nickname; p.pid=g.pid` 로 덮어쓰기(단, 윷의 탭 pid 경로와 리버시 cid·마작 kid 는 게임 레벨 id 라 별도 매핑 필요). gid 자체도 공개 채널에서 보이므로 완전한 방어는 §5 P1(서명/비공개 채널).
2. **PIN 평문 노출**(lpRoom.js:1201, 검사 483). PIN 은 '초대받은 사람만' 을 보장하지 못한다. 캐주얼 수준 방어로는 "PIN 을 방장 공개키로 암호화" 또는 "PIN 해시+nonce" 도 가능하나, 근본책은 Supabase 비공개 채널 + 익명 로그인(§5).
3. **방장 끊김 이벤트가 없다.** 게스트 쪽은 12초 무소식 → 스냅샷 요청만. 공통 `room:host_lost` / `room:host_back` 이벤트를 lpRoom 에 두고 공용 띠를 그리면 6개 게임이 한 번에 해결된다(윷의 hostLost 띠를 승격).
4. **이중 하트비트.** lpRoom 이 이미 `guest:hb`(4초)·`onGuestPresence`·`onGuestLeave(reason:'stale')` 를 제공하는데 윷·프리즘헥스·마작·리버시가 각자 hb/ping 을 또 보낸다. 게스트 발 메시지는 채널 전원에게 배달되므로 비용이 인원수만큼 곱해진다.
5. **대기실·준비·좌석이 공용이 아니다.** 윷 코드(LB·lbAdd·lbPick·lbCanStart·toLobby·kickPlayer)가 가장 완성도가 높은데 파일 안에 묶여 있다.
6. **게임 전환 목록에 보드게임 없음**(lpMultiplayer.js:111-119), 윷은 공용 패널 자체를 안 씀.
7. **홈 참가창이 lpRoom 전용**(parseRoomInput·probeRoom). 퀴즈·SZX 코드 불가, `bubble` 잘못 등재.

### 3.1 메시지 예산 (Supabase 공식 계산법 적용)

Supabase 는 브로드캐스트 1건을 **보낸 1 + 받는 구독자 수**로 센다("4 clients listen … counts as 5"). 방장 1 + 게스트 3 인 **대기 중** lpRoom 방(윷 기준):

| 발신 | 주기 | 초당 발신 | ×(1+수신 3) |
|---|---|---|---|
| host:heartbeat | 5초 | 0.2 | 0.8 |
| host:ping | 4초 | 0.25 | 1.0 |
| guest:pong ×3 | 4초 | 0.75 | 3.0 |
| guest:hb ×3 (lpRoom) | 4초 | 0.75 | 3.0 |
| 게임 hb ×3 (윷·프리즘·마작) | 4초 | 0.75 | 3.0 |
| **합계** | | 2.7 | **≈10.8 msg/s** |

→ 무료 플랜(초당 100, 월 200만) 기준 **동시 대기방 약 9개**, **월 약 51 방-시간**이면 소진. 게임 중 상태 방송은 여기에 더해진다. 결론: (a) 게스트 hb 는 방장만 받도록 할 수 없으니(브로드캐스트는 전원 배달) **주기를 늘리고 하나로 합치기**(ping/pong 을 hb 에 싣기), (b) 대기실은 10~15초 hb, 게임 중에만 4초, (c) 규모가 커지면 Pro(초당 500·월 500만) 또는 방장↔게스트를 WebRTC 로 옮기는 lpRoom 로드맵 A(lpRoom.js:103-128)가 실제 비용 절감책.

---

## 5. 리서치 (범위 B) — 최신 기법과 우리에게 맞는 것

### 5.1 참가 UX
- **짧은 코드 + 이름 두 칸이 표준.** Jackbox 는 대소문자 무관 4글자 코드 + 이름, 끊기면 같은 코드·같은 이름으로 들어오면 자리를 잠시 잡아 준다; 정원(보통 4~8) 초과는 자동 '관객'. Kahoot 는 PIN·링크·**QR** 중 아무거나, 계정 불필요, 방장이 켜면 '친근한 닉네임 생성기', 봇 방지용 2-Step Join. Kahoot 는 재접속 시 점수 복구가 안 되는 게 알려진 약점 — 우리는 pid 기반 복구가 이미 더 낫다.
- **로비는 '파티'가 게임보다 오래 산다.** 배틀넷·디스코드 액티비티: 음성 채널(=파티)에 붙은 인스턴스 id 가 방이고, 참가자 목록(`getInstanceConnectedParticipants`)이 곧 로비. 방 키가 `discord:<guild>:<channel>:<instanceId>` 식으로 '같이 있는 사람들'에 묶인다. → 우리 lpRoom 의 `transferTo`(게임 전환 시 같은 코드 유지)가 이 개념이다. **모든 게임으로 확장**하면 '배틀넷 같은 대기 공간'이 된다.
- **중도 합류/관전**: skribbl.io 비공개 방은 링크만 있으면 언제든 들어와 다음 라운드부터(2라운드부터라도) 합류, 투표 추방·음소거 제공. Gartic Phone 류는 늦게 온 사람을 다음 라운드로.
- **방장 승계**: Among Us 로비는 방장이 나가면 다른 사람이 자동으로 방장. Unity Lobby 도 방장 미지정 시 남은 사람 중 선출. 우리처럼 권위 상태가 방장 브라우저에만 있으면 승계 = 상태 이전 문제 — 윷의 판단(승계 안 함)이 합리적이며, 해결책은 '상태를 서버(DB)나 모든 게스트 스냅샷에 두는 것'.

### 5.2 네트워크 모델
- **턴제 보드게임 = 방장 권위 + 의도(intent) + 전체 스냅샷**이 정답(지금 방식). 보드 상태가 수 KB 이하라 델타가 필요 없다. 추가할 것: 의도에 `clientSeq`(멱등 키)·`expectSeq`(낙관적 동시성) — 루도 `aid`, 리버시 `n`, 프리즘 `tn` 이 이미 이 역할. 공통 형식으로 통일.
- **결정론 락스텝**(Gaffer on Games): 입력만 보내 대역폭이 입력 크기에 비례 — 구미·SZX 가 이미 '시드 공유 + 이벤트만' 으로 이 계열. 부동소수점 결정론 주의(같은 JS 엔진이라도 기기 간 차이 가능 → 판정은 정수 격자로).
- **상태 동기화**(Gaffer): 입력+상태를 보내 완벽한 결정론이 필요 없음 — 실시간 액션 대전에 적합.
- **클라이언트 예측 + 서버 재조정 + 개체 보간**(Gambetta): 내 입력은 즉시 반영, 서버 상태가 오면 미확인 입력을 다시 적용, 남은 과거 시점으로 보간. 우리 턴제 게임엔 '낙관 반영 후 방장 상태로 교정'(윷 lbPend, 루도 NET.pending)으로 충분. 롤백 넷코드는 격투급에만 가치 — 불필요.
- **시계 동기**: 왕복 중간값으로 서버 시간 오프셋(NTP 방식) — 퀴즈(quiz:333)·lpRoom skew 에 이미 있음. 턴 타이머는 '마감 시각(서버/방장 시간)'을 상태에 싣는 방식(프리즘 `S.tl`, 퀴즈 `ends_at`)이 '각자 연출 끝부터 세기'(윷)보다 기기 간 차이가 적다.
- **이벤트 소싱**: 수(move) 로그를 상태에 누적하면 재접속·관전·리플레이·'판 보기'가 공짜. 보드게임은 로그가 작아 전체 로그를 스냅샷에 넣어도 된다.

### 5.3 Supabase Realtime 한도 (공식 문서)
| 항목 | Free | Pro | Team |
|---|---|---|---|
| 동시 연결 | 200 | 500 | 10,000 |
| 초당 메시지 | 100 | 500 | 2,500 |
| 초당 채널 참가 | 100 | 500 | 2,500 |
| 연결당 채널 | 100 | 100 | 100 |
| 초당 프레즌스 메시지 | 20 | 50 | 1,000 |
| 프레즌스 객체당 키 | 10 | 10 | 10 |
| 브로드캐스트 페이로드 | 256 KB | 3,000 KB | 3,000 KB |
| 월 메시지 포함량 | 200만 | 500만 | 500만 |
- 초과 시 연결을 끊고 사용량이 내려가면 클라이언트가 자동 재연결. 과금 계산 = 발신 1 + 수신자 수.
- **프레즌스는 무료 초당 20** — 8인 방 몇 개면 바로 넘는다. SZX 의 '프레즌스 대신 브로드캐스트 하트비트' 결정은 수치상으로도 맞다.
- **비공개 채널**: `config:{private:true}` + `realtime.messages` RLS(`realtime.topic()`, `extension in ('broadcast','presence')`)로 **누가 받고 보낼 수 있는지 서버가 강제**. 방 멤버 테이블과 조인하는 정책이 표준 예제. 권한은 연결 동안 캐시됨.
- **익명 로그인** `signInAnonymously()`: 계정 없이 JWT(`is_anonymous`) 발급 → 비공개 채널·RLS 사용 가능, 기기 id 대신 **서버가 발급한 위조 불가 신원**. IP 당 시간 30회 기본 제한, Turnstile 권장(이미 `TURNSTILE_SITE_KEY` 상수 있음). 저장소 삭제·다른 기기면 새 사람.
- **DB→방송**: `realtime.send(payload,event,topic,private)` 로 서버(RPC)가 직접 방송 가능, 비공개 채널은 **최근 메시지 재생(since, 최대 25건, 72시간)** 지원, `ack:true` 로 서버 수신 확인, `channel.httpSend()` 로 소켓 없이 전송.

### 5.4 CRDT(Yjs) — 필요한가
- Yjs 는 공동 편집(텍스트·그림판)과 Awareness(커서·온라인 표시)에 최적, 중앙 진실원천 없이 수렴. **규칙이 있는 게임에는 과함** — 턴 검증·비밀 정보·승패 판정은 '한 명의 심판'이 필요하고 CRDT 는 합병만 할 뿐 규칙 위반을 막지 못한다. 쓸 곳은 '같이 그리는 캔버스', '공동 참가자 목록 편집(팀 뽑기 명단)' 정도. 권장: 도입하지 않음.

### 5.5 P2P WebRTC
- 이미 SZX(메시, 비순서·무재전송 채널)와 1:1 PvP 에 있음. 가치: 같은 와이파이 1~3ms, 서버 메시지 0. 비용: TURN 없으면 대칭 NAT(주로 모바일 데이터) 일부 실패 → **반드시 Supabase 폴백**(SZX 가 그렇게 함). 보드게임엔 불필요, 실시간 대전(구미·SZX·향후 테트로미노 배틀)에만.

### 5.6 남용 방지
- 내보내기+차단(윷에 있음) → **모든 게임 공통**으로. 차단 키는 기기 id 라 우회 가능(재현 6) → 익명 로그인 uid 기반이면 '새 계정 만들기' 비용(IP 당 30회/시)이 생긴다.
- 방장 행동 외 게스트 행동 토큰 버킷(lpRoom 10/s)은 있음. 방 만들기 속도 제한은 퀴즈만(DB). 
- 닉네임 필터: 짧은 금칙어 목록(ko/en/ja/es/pt) + 방장 '이름 바꾸기/숨기기'. Kahoot 식 '친근한 닉네임 생성기'(교실·가족용) 옵션은 욕설 문제를 원천 차단.
- 투표 추방(skribbl)은 방장 없는 SZX 에 적합.

### 5.7 접근성·모바일·인앱 브라우저
- 인앱(카톡 등): `window.confirm/alert` 가 막히거나 이상 동작 → 윷처럼 자체 확인창(루도·리버시·구미 `confirm` 교체). 서비스워커 등 제약, 외부 브라우저 열기(`kakaotalk://web/openExternal`, Android intent) — 저장소에 `lpInApp.js`/`lpInAppExit.js` 가 이미 있음.
- **탭별 신원(sessionStorage)은 인앱에서 약하다** — 링크를 다시 누르면 새 탭. 기기 신원(localStorage `lp_pid`) + 방 멤버십을 방장이 기억하는 윷 방식이 맞다(리버시·마작 교체 대상).
- 백그라운드: 폰은 수 초~수십 초 얼린다. 판정 기준은 '끊김 = 봇 대행/자리 유지'(윷), 절대 '즉시 패배'나 '자리 개방'이 아니어야 한다. Wake Lock(`LpWakeLock`) 게임 중 유지.
- 접근성: 차례 알림은 소리+진동+`aria-live` 문구, 턴 타이머 막대에 남은 초 텍스트, 색만으로 좌석 구분 금지(루도·프리즘은 색 이름을 함께).

---

## 6. 채택 우선순위

**P0 — 구멍 막기 (작게, 바로)**
1. lpRoom: `guest:action` 을 게임에 넘기기 전 `nickname/pid` 를 방장 명단 값으로 덮어쓰기(lpRoom.js:644-655). 게임들은 신원을 `p.gid→명단` 으로만 읽도록(윷 `gidPid`, 리버시 `cid`, 마작 `kid` 는 join 시 방장이 묶은 값만 인정). 이유: 재현 1·4·5.
2. 공통 **'방장 끊김' 이벤트 + 띠**(`room:host_lost/host_back`) — 재현 3.
3. 끊김 정책 통일 = **자리 유지 + 봇 대행 + 돌아오면 복귀**(윷 규칙). 리버시의 '16초 뒤 자리 개방'을 '방장 승인 또는 60초+이후 봇' 으로, 구미의 9초 기권을 '일시정지 20~30초 → 그 뒤 기권, 결과는 방장이 확정해 양쪽에 방송'으로 — 재현 8·10.
4. 게임 레벨 hb 제거하고 lpRoom 프레즌스 사용, 대기실 hb 주기 연장 — §3.1 예산.
5. 구미 `rrect` 클램프, 프리즘 hb/리스너 해제, 홈 참가 목록에서 `bubble` 제거.

**P1 — 공통 '대기실' 모듈 (운영자 요청의 핵심)**
윷 코드를 뽑아 `public/js/lpLobby.js`(가칭)로 승격 — 게임은 설정만 넘긴다:
```
LpLobby.mount({gameId, seats:{min,max}, roles?, picks:[{key:'sp',options,unique:true}],
  options:[{key:'turnSec',values:[15,30,60]}], bots:true, spectators:true, lateJoin:'takeBot'|'nextRound'|'spectate',
  onStart(roster)→initialState, onIntent(pid,intent,state)→newState|null, onBot(state,seat)→intent,
  hidden?:{perSeat(state,seat)} })
```
- 공통 화면: 코드·PIN·QR·공유(Web Share)·명단(준비/끊김/다른 앱/봇)·캐릭터/색 고르기·준비·방장 시작 게이트·봇 추가·내보내기/다시 허용·턴 시간·'한 판 더→대기실'.
- 공통 규칙: 신원 = 방장이 받은 join(pid), 상태 = `{seq, phase, deadline(방장 시각), log[], ...}` 전체 스냅샷, 의도 = `{type, expectSeq, cseq}` 멱등.
- 모든 게임을 **lpMultiplayer 게임 전환 목록에 등록** → 한 방에서 윷→루도→리버시로 파티 이동(배틀넷 파티).
- 홈 참가창: 코드 형식별 라우팅(영문6=lpRoom, 숫자6=퀴즈/SZX 조회) 또는 코드 체계 통일.

**P2 — 신뢰 계층 (규모가 붙으면)**
- Supabase **익명 로그인 + 비공개 채널 RLS**: 방 멤버 테이블에 있는 uid 만 구독/송신 → PIN 노출·사칭·차단 우회를 서버에서 해결. Turnstile 로 익명 가입 남용 방지.
- 방 메타(코드·게임·방장 uid·정원·잠금·차단 목록)만 DB 에, 게임 상태는 계속 방장 브로드캐스트(비용 유지). 방장 새로고침 외 **방장 승계**는 '마지막 스냅샷을 모든 게스트가 보관 → 방장 부재 N초면 가장 오래된 게스트가 스냅샷으로 재개' 방식이 가능(보드게임만, 비밀 정보 없는 게임만).
- 마작처럼 비밀 정보가 있는 게임의 공정성 = 서버 딜러(Edge Function) — 수요가 확인될 때만.

**P3 — 확장**
- 공용 '레이스 방'(SZX 패턴 일반화: 시드·출발·실시간 순위·결과표)으로 솔로 아케이드에 '같이 도전' 추가(§7).
- 실시간 대전(구미류)은 WebRTC 직통 + Supabase 폴백(lpRoom 로드맵 A) — 메시지 비용이 문제될 때.

---

## 7. 솔로 아케이드 — '같이 보기/도전' 후보

| 게임 | 시드 결정론 | 제안 | 가치 |
|---|---|---|---|
| 풍선 `balloon` | 숨은 파열점(비밀) | **턴제 온라인**(윷 모델 그대로 — 방장이 파열점 보관, 차례대로 펌프) | **높음** — 랜덤뽑기 분류라 '같이'가 본질 |
| 마작 솔리테어 `mahjong-solitaire` | 있음(오늘의 판) | 같은 판 동시 레이스(남은 패 수 실시간) | 높음·저비용 |
| 테트로미노 `tetris` | 7-백(시드 없음 → 추가 필요) | ① 같은 시드 스프린트 레이스 ② 이후 방해줄 대전(구미 스트림 재사용) | 높음·중비용 |
| 벽돌깨기 `brick` · 버거 `burger` · 착륙 `starship-lander` · 행성 `lucky-merge` | 시드 있음 | 공용 레이스 방(같은 시드·점수 실시간) | 중간 — 모듈 하나로 일괄 |
| 스네이크 `snake` · 닷 러너 `pacman` | 시드 없음(먹이/유령 난수) | 시드화 후 레이스, 또는 도전 링크만 | 중간 |
| DELTA-V `orbit` | 미션 고정 | 도전 링크(기록 비교)만 | 낮음 |
| 버블 `bubble` | 없음 | 도전 링크만 | 낮음 |

'같이 보기'(한 사람 화면 중계)는 액션 게임에선 재미가 약하다 — **같은 시드 동시 레이스 + 끝나면 결과표**가 투자 대비 효과가 가장 크다(SZX 에서 이미 검증된 구조, dodge `chUrl` 도전 링크도 있음).

---

## 8. 게임별 요약표

| 게임 | 좌석/역할 | 개인 선택 | 동기화 모델 | 특이 요구 |
|---|---|---|---|---|
| 윷놀이 | 2~4팀, 관전, 봇 | 캐릭터(고유), 이름, 준비 | 방장 권위·의도·전체 스냅샷·seq | 턴 시간·afk→봇·중도 인계 (기준 구현) |
| 루도 | 4석(사람/봇/원격/끔) | (없음 → 색 선택 추가) | 방장 권위·전체 상태·aid | 주사위는 방장 난수, 중도 인계 필요 |
| 리버시 | 2석 + 관전 | (색 교환은 방장만) | 방장 권위·64칸 문자열 | 턴 시간·리매치 합의·자리 보호 필요 |
| 프리즘 헥스 | 2~6석, 봇, 중도 인계 | 자리 | 방장 권위·seq·남은 시간 동봉 | 수 검증 비용 큼, 핀치 줌 |
| 대만 마작 | 4석(방장=0) | (자리 선택 없음) | 방장 권위 + **좌석별 ECDH 암호화** | 비밀 손패, 울기 창 타이머 |
| 구미 체인 | 1:1 (+관전 필요) | 색 수 | **대칭 결정론 + 신뢰 이벤트 스트림** | 백그라운드 유예·결과 확정 주체 필요 |
| 퀴즈 라이브 | 방장 1 + 최대 200 | 닉네임·아바타 | **서버(DB) 권위 + 폴링 + nudge** | 서버 시계, 멱등 답안 (모범) |
| SZX 레이스/협동 | 8명/2명, 리더 없음 | 닉네임·기체색 | **대칭 P2P·시드 결정론·WebRTC 메시** | 메시지 예산, 자기 신고 기록 |
| 스페이스-Z 1:1 | 로그인 2명 | — | DB 방 + 브로드캐스트 + WebRTC | 로그인 필수(유일) |

---

### 출처
- Supabase Realtime 한도: https://supabase.com/docs/guides/realtime/limits
- Supabase 메시지 과금 계산: https://supabase.com/docs/guides/platform/manage-your-usage/realtime-messages
- Supabase Realtime 권한(비공개 채널·RLS): https://supabase.com/docs/guides/realtime/authorization
- Supabase 브로드캐스트(realtime.send·재생·ack·httpSend): https://supabase.com/docs/guides/realtime/broadcast
- Supabase 익명 로그인: https://supabase.com/docs/guides/auth/auth-anonymous
- Jackbox 참가·재접속·관객: https://support.jackboxgames.com/hc/en-us/articles/15794759479959-How-do-I-join-a-game , https://en.wikipedia.org/wiki/The_Jackbox_Party_Pack
- Kahoot 참가(PIN·QR·닉네임 생성기·재접속 불가): https://support.kahoot.com/hc/en-us/articles/360039890713-Kahoot-join-How-to-join-a-Kahoot-game
- Discord Activities 멀티플레이: https://docs.discord.com/developers/activities/development-guides/multiplayer-experience , https://github.com/discord/embedded-app-sdk
- 방장 승계: https://docs.unity.com/ugs/en-us/manual/lobby/manual/host-migration , https://steamcommunity.com/app/945360/discussions/0/690868861351779108/
- skribbl.io 비공개 방·중도 합류·투표 추방: https://skribbl-io.fandom.com/wiki/Server
- Gaffer on Games: https://gafferongames.com/post/deterministic_lockstep/ , https://gafferongames.com/post/state_synchronization/
- Gabriel Gambetta: https://www.gabrielgambetta.com/client-side-prediction-server-reconciliation.html , https://www.gabrielgambetta.com/entity-interpolation.html
- Yjs: https://docs.yjs.dev/ , https://docs.yjs.dev/api/about-awareness
- 카카오 인앱 외부 브라우저: https://github.com/fi-workers/mocco/issues/238 , https://developers.kakao.com/docs/latest/en/javascript/hybrid
