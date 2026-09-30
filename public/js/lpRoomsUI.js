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
     replay?: (cert) => void;                 // [+] 검증 시트의 [↻ 다시 보기] — 게임이 인증서로 연출을 다시 튼다
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
     openJoin(o?: { code?: string, gameId?: string, inv?: {fp, tok?}, sheet?: boolean }): Promise<void>;
          // 코드/링크 입력 → LpRooms.resolve → 같은 게임이면 여기서 참가, 아니면 그 게임 페이지로 이동
          // [+] 올바른 code + 저장된 닉네임이면 시트 없이 바로 참가(링크로 온 게임의 자동 참가 — sheet:true 면 항상 시트).
          //     inv 가 있으면 sessionStorage lpr_inv 로 옮겨 fp 고정 참가. gameId 는 참고용(페이지 게임과 다르면 resolve 가 이동)
     openInvite(room?): void;                 // 초대 시트: 💬 메신저로 초대(1순위) · 링크+복사 · QR · 코드 · 🔄 링크 새로(방장)
     openRoom(room?): void;                   // 방 시트(= HUD 탭): 명단 · 초대 · 방장 도구 · 나가기
     openSwitch(room?): void;                 // 방장: 게임 바꾸기 그리드 → room.switchGame(id)
     mountLobby(room, o?: { into?: HTMLElement }): Handle;   // 풀 대기실(기본 화면 전체). 보통 자동 — 수동은 lobby:'none' 일 때
     mountHud(room): Handle;                  // HUD 알약 `K7M-2QX · 👥5 · ●` — 보통 자동
     strip(room, el?: HTMLElement): Handle;   // 띠형 대기실: 명단 1줄 + [초대] (+ 준비/시작은 게임 버튼이 맡는다)
     drawStrip(o: { room: Room | null, gameId?: string, allow?: boolean,
                    onEntry?(): void, onAllow?(): void, onFill?(): void }): Handle | null;
          // [+] 추첨 게임(draw) 계약 — strip() 위에 추첨 버튼을 얹는다. 게임은 명단·상태가 바뀔 때마다 불러도 된다(멱등, 다시 그리기만).
          //     방장: [✋ allow 토글 → onAllow] [👥 → onFill(멤버 이름으로 채우기)]  게스트: allow 일 때 [✋ → onEntry(내 이름 넣기)]
          //     room=null → 띠 정리(UI 가 붙든 방이 없을 때). UI 가 아직 그 방을 안 붙였으면 붙인다(bind).
     badge(el: HTMLElement, info: {kind:'verified'|'seed'|'solo'|'mismatch', n?, round?, cert?}): void;
          // LpFair.badge + 스타일 + 현지화("✓ 공정 · 5명 확인") + 탭 → 검증 시트. LpFair.badge 를 직접 불러도 같은 모양(후크)
     confirm(msg: string, o?: { ok?: string, cancel?: string, danger?: boolean }): Promise<boolean>;   // window.confirm 대체(인앱 안전)
     sheet(o: { title?: string, body: HTMLElement | string, onClose?(): void }): { el: HTMLElement, close(): void };   // 공용 바텀시트
     toast(msg: string, ms?: number): void;
     say(msg: string): void;                  // aria-live=polite 알림
     t(key: string, vars?: object): string;   // 문구 표(16개 언어, 빠진 언어 → en)
     lang(): string;                          // luckyplz_lang (gb → en)
     avatars: string[];                       // 16종 — LpRooms.profile.av 인덱스
     hub(el: HTMLElement): { el };            // [+] /lobby/ 허브(코드 6칸 · 방 만들기 그리드 · 최근 방 점) — lobby/index.html 이 쓴다
     route(input: string, el?: HTMLElement): Promise<Room | null>;   // [+] 코드/링크 → resolve → 여기서 참가 또는 이동(/r/ 는 replace)
   }
   게임 등록 대기열 [+]: 게임 인라인 스크립트는 로더보다 먼저 돈다 →
     window.LpRoomsQ = window.LpRoomsQ || [];
     LpRoomsQ.push(function (LpRooms, UI) { LpRooms.adapter({...}); UI.config({...}); });
   UI 가 부팅하면서(자동 참가·resume 전에) 차례로 부르고, 이후 push 는 즉시 실행된다(LpAutoPauseQ 와 같은 패턴).
   URL: ?r=CODE(참가) · ?lpr=new(이 게임으로 방 만들기 시트) · #k=<fp>.<tok>(초대 — sessionStorage lpr_inv 로 옮긴 뒤 주소창에서 지움)
   [+] window.__lprBoot — 자동 참가·resume 을 한 곳만 하도록 하는 깃발. UI 가 부팅하며 그 일을 맡으면 'ui' 로 세우고,
       이미 다른 값(게임 어댑터가 먼저 맡음, 예 'p3a')이면 UI 는 자동 참가·resume 을 건너뛴다. 게임도 같은 규칙으로 확인한다.

   자동 동작(v2 로더가 이 파일을 실으면): URL(?r= · /r/CODE · #k=) → sessionStorage lpr_inv 로 옮기고 주소창에서 지움 →
   LpRooms.resume() → (없으면) ?r= 코드로 참가(저장된 닉 있으면 묻지 않음) → 방이 붙으면 HUD 1개 +
   phase='lobby' 동안 풀 대기실 또는 띠. phase≠'lobby' 면 대기실이 닫히고 'play'. 게임 도크(LpChrome)에 👥 버튼.
   ===================================================================== */
(function (G) {
    'use strict';
    if (G.LpRoomsUI && G.LpRoomsUI.version && G.LpRoomsUI.version.indexOf('stub') < 0) return;
    var D = G.document;
    if (!D) return;
    var VER = '2.0.0';

    /* ── 아바타 16종 (lp_profile.av 인덱스, 코어와 공유) ─────────────── */
    var AV = ['🐼', '🦊', '🐯', '🐰', '🐶', '🐱', '🐨', '🐸', '🐧', '🦄', '🐙', '🐢', '🦉', '🐝', '🦖', '🐳'];
    var REACT = ['👍', '😂', '😱', '🔥', '👏', '🍀'];

    /* ── 문구 표 (§4.7) — 2~4단어·아이콘 우선. 빠진 키/언어 → en ───────── */
    var I = {
        ko: {
            create: '방 만들기', join: '입장', joinCode: '코드로 참가', code: '방 코드', nick: '닉네임', codePh: '코드 6자리 또는 링크',
            invite: '초대', inviteMsg: '메신저로 초대', copy: '복사', copied: '복사했어요', newLink: '링크 새로', linkNew: '새 링크를 만들었어요',
            ready: '준비', readyOn: '준비 완료', start: '시작', startAny: '준비한 사람만 시작', needN: '{n}명 더 필요', needReady: '준비 {a}/{b}',
            waitHost: '방장이 시작해요', pickGame: '게임 고르기', pickingGame: '방장이 게임 고르는 중', host: '방장', me: '나',
            watch: '관전', watchN: '관전 {n}', play: '참가', bot: '봇', addBot: '봇', away: '다른 앱', off: '끊김', on: '연결됨',
            kick: '내보내기', ban: '내보내고 차단', makeHost: '방장 넘기기', toWatch: '관전으로', rmBot: '봇 빼기',
            kickQ: '{n} 님을 내보낼까요?', banQ: '{n} 님을 차단할까요?', closeQ: '방을 닫을까요?', leaveQ: '방에서 나갈까요?',
            ok: '확인', cancel: '취소', yes: '네', lock: '잠금', appr: '승인 입장', pin: 'PIN', pause: '일시정지', resume: '계속',
            toLobby: '대기실로', switchG: '게임 바꾸기', closeRoom: '방 닫기', leave: '나가기', home: '홈',
            hostCheck: '방장 확인 중…', hostLost: '방장 연결 끊김', hostWait: '방장 기다리는 중', waitBtn: '기다리기',
            takeover: '{n} 님이 방장', meHost: '내가 방장이 됐어요', joinedN: '{n} 입장', leftN: '{n} 나감',
            kicked: '방에서 내보내졌어요', banned: '들어갈 수 없는 방', closed: '방이 닫혔어요', hostGone: '방장이 떠났어요', replaced: '다른 곳에서 이어서 진행 중',
            notFound: '방을 찾지 못했어요', conflict: '방장 확인 실패 · 링크로 들어오세요', badFp: '링크가 맞지 않아요', full: '방이 꽉 찼어요',
            locked: '잠긴 방이에요', rate: '잠시 뒤 다시', denied: '입장이 거절됐어요', pending: '방장 승인 기다리는 중…', pinNeed: 'PIN 4자리',
            pinBad: 'PIN 이 달라요', network: '연결이 안 돼요', version: '새로고침이 필요해요', unsupported: '이 브라우저는 안 돼요',
            inapp: '브라우저로 여는 중…', otherTab: '다른 탭에서 열려 있어요', here: '여기서 계속', retry: '다시', finding: '방 찾는 중…',
            joining: '들어가는 중…', creating: '방 만드는 중…', recent: '최근 방', gather: '먼저 모이기', moving: '게임으로 이동…',
            fairN: '✓ 공정 · {n}명 확인', fairSeed: '✓ 공정 시드', solo: '🎲 혼자 뽑기', mismatch: '⚠ {n}명 화면 다름', certCopy: '결과 링크 복사',
            fairT: '공정 추첨', replay: '다시 보기', sealHint: '모두 같은 그림이면 같은 방', paused: '일시정지', myTurn: '내 차례', pinFlood: 'PIN 시도 많음',
            askIn: '{n} 입장 요청', players: '{n}명', addMe: '내 이름 넣기', choose: '고르기', taken: '이미 골랐어요', rooms: '같이 하기',
            shareTxt: '🎲 {g} 같이 해요 · {c}', pinOnly: 'PIN {p}', inviteOnlyHint: '코드 입력자만',
            char: '캐릭터', color: '색', side: '자리', turnSec: '턴 시간', mode: '모드', seat: '자리'
        },
        en: {
            create: 'Create room', join: 'Join', joinCode: 'Join by code', code: 'Room code', nick: 'Nickname', codePh: '6-letter code or link',
            invite: 'Invite', inviteMsg: 'Invite via chat', copy: 'Copy', copied: 'Copied', newLink: 'New link', linkNew: 'New link made',
            ready: 'Ready', readyOn: 'Ready!', start: 'Start', startAny: 'Start with ready', needN: '{n} more needed', needReady: 'Ready {a}/{b}',
            waitHost: 'Host starts', pickGame: 'Pick a game', pickingGame: 'Host is picking', host: 'Host', me: 'me',
            watch: 'Watch', watchN: '{n} watching', play: 'Play', bot: 'Bot', addBot: 'Bot', away: 'away', off: 'offline', on: 'online',
            kick: 'Remove', ban: 'Remove & block', makeHost: 'Make host', toWatch: 'To watchers', rmBot: 'Remove bot',
            kickQ: 'Remove {n}?', banQ: 'Block {n}?', closeQ: 'Close the room?', leaveQ: 'Leave the room?',
            ok: 'OK', cancel: 'Cancel', yes: 'Yes', lock: 'Lock', appr: 'Approve joins', pin: 'PIN', pause: 'Pause', resume: 'Resume',
            toLobby: 'To lobby', switchG: 'Change game', closeRoom: 'Close room', leave: 'Leave', home: 'Home',
            hostCheck: 'Checking host…', hostLost: 'Host disconnected', hostWait: 'Waiting for host', waitBtn: 'Wait',
            takeover: '{n} is host now', meHost: 'You are host now', joinedN: '{n} joined', leftN: '{n} left',
            kicked: 'You were removed', banned: 'Can’t join this room', closed: 'Room closed', hostGone: 'Host left', replaced: 'Continued elsewhere',
            notFound: 'Room not found', conflict: 'Host check failed · use the link', badFp: 'Link doesn’t match', full: 'Room is full',
            locked: 'Room is locked', rate: 'Try again soon', denied: 'Join declined', pending: 'Waiting for host OK…', pinNeed: '4-digit PIN',
            pinBad: 'Wrong PIN', network: 'No connection', version: 'Please refresh', unsupported: 'Browser not supported',
            inapp: 'Opening in browser…', otherTab: 'Open in another tab', here: 'Continue here', retry: 'Retry', finding: 'Finding room…',
            joining: 'Joining…', creating: 'Creating…', recent: 'Recent', gather: 'Gather first', moving: 'Going to game…',
            fairN: '✓ Fair · {n} verified', fairSeed: '✓ Fair seed', solo: '🎲 Solo draw', mismatch: '⚠ {n} saw different', certCopy: 'Copy result link',
            fairT: 'Fair draw', replay: 'Replay', sealHint: 'Same pictures = same room', paused: 'Paused', myTurn: 'Your turn', pinFlood: 'Many PIN tries',
            askIn: '{n} wants in', players: '{n}', addMe: 'Add me', choose: 'Pick', taken: 'Already taken', rooms: 'Play together',
            shareTxt: '🎲 Play {g} with me · {c}', pinOnly: 'PIN {p}', inviteOnlyHint: 'code only',
            char: 'Character', color: 'Color', side: 'Side', turnSec: 'Turn time', mode: 'Mode', seat: 'Seat'
        },
        ja: {
            create: 'ルーム作成', join: '参加', joinCode: 'コードで参加', code: 'ルームコード', nick: 'ニックネーム', codePh: '6文字コードかリンク',
            invite: '招待', inviteMsg: 'メッセで招待', copy: 'コピー', copied: 'コピーしました', newLink: '新しいリンク', linkNew: 'リンクを更新',
            ready: '準備', readyOn: '準備OK', start: 'スタート', startAny: '準備済みで開始', needN: 'あと{n}人', needReady: '準備 {a}/{b}',
            waitHost: 'ホストが開始', pickGame: 'ゲームを選ぶ', pickingGame: 'ホストが選択中', host: 'ホスト', me: '自分',
            watch: '観戦', watchN: '観戦 {n}', play: '参加', bot: 'ボット', addBot: 'ボット', away: '離席', off: '切断', on: '接続中',
            kick: '退出させる', ban: '退出+ブロック', makeHost: 'ホストを譲る', toWatch: '観戦へ', rmBot: 'ボットを外す',
            kickQ: '{n} を退出させますか？', banQ: '{n} をブロックしますか？', closeQ: 'ルームを閉じますか？', leaveQ: 'ルームを出ますか？',
            ok: 'OK', cancel: 'キャンセル', yes: 'はい', lock: 'ロック', appr: '承認制', pin: 'PIN', pause: '一時停止', resume: '再開',
            toLobby: 'ロビーへ', switchG: 'ゲーム変更', closeRoom: 'ルームを閉じる', leave: '退出', home: 'ホーム',
            hostCheck: 'ホスト確認中…', hostLost: 'ホスト切断', hostWait: 'ホスト待ち', waitBtn: '待つ',
            takeover: '{n} がホストに', meHost: 'あなたがホストに', joinedN: '{n} 参加', leftN: '{n} 退出',
            kicked: '退出させられました', banned: '参加できません', closed: 'ルーム終了', hostGone: 'ホストが退出', replaced: '別の場所で続行中',
            notFound: 'ルームが見つかりません', conflict: 'ホスト確認失敗・リンクで参加', badFp: 'リンクが一致しません', full: '満員です',
            locked: 'ロック中', rate: '少し待って再試行', denied: '参加を断られました', pending: 'ホストの承認待ち…', pinNeed: 'PIN 4桁',
            pinBad: 'PIN が違います', network: '接続できません', version: '再読み込みしてください', unsupported: '非対応ブラウザ',
            inapp: 'ブラウザで開いています…', otherTab: '別のタブで開いています', here: 'ここで続ける', retry: '再試行', finding: 'ルーム検索中…',
            joining: '参加中…', creating: '作成中…', recent: '最近のルーム', gather: '先に集合', moving: 'ゲームへ移動…',
            fairN: '✓ 公正 · {n}人確認', fairSeed: '✓ 公正シード', solo: '🎲 ひとり抽選', mismatch: '⚠ {n}人の画面が違う', certCopy: '結果リンクをコピー',
            fairT: '公正抽選', replay: 'もう一度見る', sealHint: '同じ絵なら同じルーム', paused: '一時停止中', myTurn: 'あなたの番', pinFlood: 'PIN 試行多数',
            askIn: '{n} が参加希望', players: '{n}人', addMe: '自分を追加', choose: '選ぶ', taken: '選択済み', rooms: 'みんなで遊ぶ',
            shareTxt: '🎲 {g} 一緒にやろう · {c}', pinOnly: 'PIN {p}', inviteOnlyHint: 'コード入力のみ',
            char: 'キャラ', color: '色', side: '手番', turnSec: '持ち時間', mode: 'モード', seat: '席'
        },
        zh: {
            create: '创建房间', join: '加入', joinCode: '输入房间码', code: '房间码', nick: '昵称', codePh: '6位房间码或链接',
            invite: '邀请', inviteMsg: '发给好友', copy: '复制', copied: '已复制', newLink: '新链接', linkNew: '已生成新链接',
            ready: '准备', readyOn: '已准备', start: '开始', startAny: '已准备的先开始', needN: '还差{n}人', needReady: '准备 {a}/{b}',
            waitHost: '等房主开始', pickGame: '选游戏', pickingGame: '房主选游戏中', host: '房主', me: '我',
            watch: '观战', watchN: '观战 {n}', play: '参加', bot: '机器人', addBot: '机器人', away: '离开', off: '断线', on: '在线',
            kick: '移出', ban: '移出并拉黑', makeHost: '转让房主', toWatch: '改为观战', rmBot: '移除机器人',
            kickQ: '移出 {n}？', banQ: '拉黑 {n}？', closeQ: '关闭房间？', leaveQ: '离开房间？',
            ok: '确定', cancel: '取消', yes: '是', lock: '锁定', appr: '审核加入', pin: 'PIN', pause: '暂停', resume: '继续',
            toLobby: '回大厅', switchG: '换游戏', closeRoom: '关闭房间', leave: '离开', home: '首页',
            hostCheck: '确认房主中…', hostLost: '房主已断线', hostWait: '等待房主', waitBtn: '等待',
            takeover: '{n} 成为房主', meHost: '你成为房主了', joinedN: '{n} 加入', leftN: '{n} 离开',
            kicked: '你被移出了房间', banned: '无法加入', closed: '房间已关闭', hostGone: '房主离开了', replaced: '已在别处继续',
            notFound: '找不到房间', conflict: '房主验证失败 · 请用链接', badFp: '链接不匹配', full: '房间已满',
            locked: '房间已锁定', rate: '请稍后再试', denied: '加入被拒绝', pending: '等待房主同意…', pinNeed: '4位PIN',
            pinBad: 'PIN 错误', network: '无法连接', version: '请刷新页面', unsupported: '浏览器不支持',
            inapp: '正在用浏览器打开…', otherTab: '已在其他标签页打开', here: '在这里继续', retry: '重试', finding: '寻找房间…',
            joining: '加入中…', creating: '创建中…', recent: '最近房间', gather: '先集合', moving: '前往游戏…',
            fairN: '✓ 公平 · {n}人确认', fairSeed: '✓ 公平种子', solo: '🎲 单人抽签', mismatch: '⚠ {n}人画面不同', certCopy: '复制结果链接',
            fairT: '公平抽签', replay: '重播', sealHint: '图案相同=同一房间', paused: '已暂停', myTurn: '轮到你了', pinFlood: 'PIN 尝试过多',
            askIn: '{n} 请求加入', players: '{n}人', addMe: '加上我', choose: '选择', taken: '已被选', rooms: '一起玩',
            shareTxt: '🎲 一起玩{g} · {c}', pinOnly: 'PIN {p}', inviteOnlyHint: '仅输入码时',
            char: '角色', color: '颜色', side: '执子', turnSec: '回合时间', mode: '模式', seat: '座位'
        },
        es: {
            create: 'Crear sala', join: 'Entrar', joinCode: 'Entrar con código', code: 'Código', nick: 'Apodo', codePh: 'Código de 6 o enlace',
            invite: 'Invitar', inviteMsg: 'Invitar por chat', copy: 'Copiar', copied: 'Copiado', newLink: 'Nuevo enlace', linkNew: 'Enlace nuevo',
            ready: 'Listo', readyOn: '¡Listo!', start: 'Empezar', startAny: 'Empezar con listos', needN: 'Faltan {n}', needReady: 'Listos {a}/{b}',
            waitHost: 'El anfitrión empieza', pickGame: 'Elegir juego', pickingGame: 'El anfitrión elige', host: 'Anfitrión', me: 'yo',
            watch: 'Ver', watchN: '{n} mirando', play: 'Jugar', bot: 'Bot', addBot: 'Bot', away: 'fuera', off: 'desconectado', on: 'conectado',
            kick: 'Sacar', ban: 'Sacar y bloquear', makeHost: 'Hacer anfitrión', toWatch: 'A espectadores', rmBot: 'Quitar bot',
            kickQ: '¿Sacar a {n}?', banQ: '¿Bloquear a {n}?', closeQ: '¿Cerrar la sala?', leaveQ: '¿Salir de la sala?',
            ok: 'OK', cancel: 'Cancelar', yes: 'Sí', lock: 'Cerrar', appr: 'Aprobar entradas', pin: 'PIN', pause: 'Pausa', resume: 'Seguir',
            toLobby: 'A la sala', switchG: 'Cambiar juego', closeRoom: 'Cerrar sala', leave: 'Salir', home: 'Inicio',
            hostCheck: 'Comprobando anfitrión…', hostLost: 'Anfitrión desconectado', hostWait: 'Esperando anfitrión', waitBtn: 'Esperar',
            takeover: '{n} es anfitrión', meHost: 'Ahora eres anfitrión', joinedN: '{n} entró', leftN: '{n} salió',
            kicked: 'Te sacaron de la sala', banned: 'No puedes entrar', closed: 'Sala cerrada', hostGone: 'El anfitrión se fue', replaced: 'Sigue en otro lugar',
            notFound: 'Sala no encontrada', conflict: 'Anfitrión no verificado · usa el enlace', badFp: 'El enlace no coincide', full: 'Sala llena',
            locked: 'Sala cerrada', rate: 'Prueba en un rato', denied: 'Entrada rechazada', pending: 'Esperando al anfitrión…', pinNeed: 'PIN de 4',
            pinBad: 'PIN incorrecto', network: 'Sin conexión', version: 'Recarga la página', unsupported: 'Navegador no compatible',
            inapp: 'Abriendo en el navegador…', otherTab: 'Abierta en otra pestaña', here: 'Seguir aquí', retry: 'Reintentar', finding: 'Buscando sala…',
            joining: 'Entrando…', creating: 'Creando…', recent: 'Recientes', gather: 'Reunirse primero', moving: 'Yendo al juego…',
            fairN: '✓ Justo · {n} verificados', fairSeed: '✓ Semilla justa', solo: '🎲 Sorteo solo', mismatch: '⚠ {n} vieron otro', certCopy: 'Copiar enlace',
            fairT: 'Sorteo justo', replay: 'Ver de nuevo', sealHint: 'Mismos dibujos = misma sala', paused: 'En pausa', myTurn: 'Tu turno', pinFlood: 'Muchos intentos de PIN',
            askIn: '{n} quiere entrar', players: '{n}', addMe: 'Añadirme', choose: 'Elegir', taken: 'Ya elegido', rooms: 'Jugar juntos',
            shareTxt: '🎲 Juguemos {g} · {c}', pinOnly: 'PIN {p}', inviteOnlyHint: 'solo con código',
            char: 'Personaje', color: 'Color', side: 'Lado', turnSec: 'Tiempo', mode: 'Modo', seat: 'Asiento'
        },
        pt: {
            create: 'Criar sala', join: 'Entrar', joinCode: 'Entrar com código', code: 'Código', nick: 'Apelido', codePh: 'Código de 6 ou link',
            invite: 'Convidar', inviteMsg: 'Convidar no chat', copy: 'Copiar', copied: 'Copiado', newLink: 'Novo link', linkNew: 'Link novo',
            ready: 'Pronto', readyOn: 'Pronto!', start: 'Começar', startAny: 'Começar com prontos', needN: 'Faltam {n}', needReady: 'Prontos {a}/{b}',
            waitHost: 'O anfitrião começa', pickGame: 'Escolher jogo', pickingGame: 'Anfitrião escolhendo', host: 'Anfitrião', me: 'eu',
            watch: 'Assistir', watchN: '{n} assistindo', play: 'Jogar', bot: 'Bot', addBot: 'Bot', away: 'fora', off: 'desconectado', on: 'conectado',
            kick: 'Remover', ban: 'Remover e bloquear', makeHost: 'Passar anfitrião', toWatch: 'Para plateia', rmBot: 'Tirar bot',
            kickQ: 'Remover {n}?', banQ: 'Bloquear {n}?', closeQ: 'Fechar a sala?', leaveQ: 'Sair da sala?',
            ok: 'OK', cancel: 'Cancelar', yes: 'Sim', lock: 'Trancar', appr: 'Aprovar entradas', pin: 'PIN', pause: 'Pausar', resume: 'Continuar',
            toLobby: 'Para a sala', switchG: 'Trocar jogo', closeRoom: 'Fechar sala', leave: 'Sair', home: 'Início',
            hostCheck: 'Checando anfitrião…', hostLost: 'Anfitrião caiu', hostWait: 'Esperando anfitrião', waitBtn: 'Esperar',
            takeover: '{n} é o anfitrião', meHost: 'Você é o anfitrião', joinedN: '{n} entrou', leftN: '{n} saiu',
            kicked: 'Você foi removido', banned: 'Não pode entrar', closed: 'Sala fechada', hostGone: 'O anfitrião saiu', replaced: 'Continua em outro lugar',
            notFound: 'Sala não encontrada', conflict: 'Anfitrião não verificado · use o link', badFp: 'Link não confere', full: 'Sala cheia',
            locked: 'Sala trancada', rate: 'Tente daqui a pouco', denied: 'Entrada recusada', pending: 'Esperando o anfitrião…', pinNeed: 'PIN de 4',
            pinBad: 'PIN errado', network: 'Sem conexão', version: 'Recarregue a página', unsupported: 'Navegador sem suporte',
            inapp: 'Abrindo no navegador…', otherTab: 'Aberta em outra aba', here: 'Continuar aqui', retry: 'Tentar de novo', finding: 'Procurando sala…',
            joining: 'Entrando…', creating: 'Criando…', recent: 'Recentes', gather: 'Reunir primeiro', moving: 'Indo ao jogo…',
            fairN: '✓ Justo · {n} conferiram', fairSeed: '✓ Semente justa', solo: '🎲 Sorteio solo', mismatch: '⚠ {n} viram diferente', certCopy: 'Copiar link',
            fairT: 'Sorteio justo', replay: 'Ver de novo', sealHint: 'Mesmos desenhos = mesma sala', paused: 'Pausado', myTurn: 'Sua vez', pinFlood: 'Muitas tentativas de PIN',
            askIn: '{n} quer entrar', players: '{n}', addMe: 'Me incluir', choose: 'Escolher', taken: 'Já escolhido', rooms: 'Jogar juntos',
            shareTxt: '🎲 Bora jogar {g} · {c}', pinOnly: 'PIN {p}', inviteOnlyHint: 'só com código',
            char: 'Personagem', color: 'Cor', side: 'Lado', turnSec: 'Tempo', mode: 'Modo', seat: 'Lugar'
        },
        /* 그 밖의 언어 — 눈에 가장 많이 띄는 키만. 나머지는 en */
        de: { create: 'Raum erstellen', join: 'Beitreten', joinCode: 'Mit Code beitreten', code: 'Raumcode', nick: 'Spitzname', invite: 'Einladen', inviteMsg: 'Per Chat einladen', copy: 'Kopieren', copied: 'Kopiert', ready: 'Bereit', readyOn: 'Bereit!', start: 'Start', host: 'Host', watch: 'Zuschauen', play: 'Spielen', leave: 'Verlassen', closeRoom: 'Raum schließen', switchG: 'Spiel wechseln', lock: 'Sperren', ok: 'OK', cancel: 'Abbrechen', notFound: 'Raum nicht gefunden', hostLost: 'Host getrennt', finding: 'Suche Raum…', joining: 'Trete bei…', pickGame: 'Spiel wählen', home: 'Start', retry: 'Nochmal' },
        fr: { create: 'Créer un salon', join: 'Rejoindre', joinCode: 'Rejoindre par code', code: 'Code du salon', nick: 'Pseudo', invite: 'Inviter', inviteMsg: 'Inviter par chat', copy: 'Copier', copied: 'Copié', ready: 'Prêt', readyOn: 'Prêt !', start: 'Lancer', host: 'Hôte', watch: 'Regarder', play: 'Jouer', leave: 'Quitter', closeRoom: 'Fermer le salon', switchG: 'Changer de jeu', lock: 'Verrouiller', ok: 'OK', cancel: 'Annuler', notFound: 'Salon introuvable', hostLost: 'Hôte déconnecté', finding: 'Recherche…', joining: 'Connexion…', pickGame: 'Choisir un jeu', home: 'Accueil', retry: 'Réessayer' },
        ru: { create: 'Создать комнату', join: 'Войти', joinCode: 'Войти по коду', code: 'Код комнаты', nick: 'Ник', invite: 'Пригласить', inviteMsg: 'Пригласить в чате', copy: 'Копировать', copied: 'Скопировано', ready: 'Готов', readyOn: 'Готов!', start: 'Старт', host: 'Хост', watch: 'Смотреть', play: 'Играть', leave: 'Выйти', closeRoom: 'Закрыть комнату', switchG: 'Сменить игру', lock: 'Закрыть вход', ok: 'OK', cancel: 'Отмена', notFound: 'Комната не найдена', hostLost: 'Хост отключился', finding: 'Ищем комнату…', joining: 'Входим…', pickGame: 'Выбрать игру', home: 'Домой', retry: 'Ещё раз' },
        tr: { create: 'Oda kur', join: 'Katıl', joinCode: 'Kodla katıl', code: 'Oda kodu', nick: 'Takma ad', invite: 'Davet et', copy: 'Kopyala', copied: 'Kopyalandı', ready: 'Hazır', start: 'Başla', host: 'Ev sahibi', watch: 'İzle', play: 'Oyna', leave: 'Çık', ok: 'Tamam', cancel: 'İptal', home: 'Ana sayfa' },
        id: { create: 'Buat ruang', join: 'Gabung', joinCode: 'Gabung pakai kode', code: 'Kode ruang', nick: 'Nama', invite: 'Undang', copy: 'Salin', copied: 'Disalin', ready: 'Siap', start: 'Mulai', host: 'Host', watch: 'Tonton', play: 'Main', leave: 'Keluar', ok: 'OK', cancel: 'Batal', home: 'Beranda' },
        vi: { create: 'Tạo phòng', join: 'Vào', joinCode: 'Vào bằng mã', code: 'Mã phòng', nick: 'Biệt danh', invite: 'Mời', copy: 'Sao chép', copied: 'Đã chép', ready: 'Sẵn sàng', start: 'Bắt đầu', host: 'Chủ phòng', watch: 'Xem', play: 'Chơi', leave: 'Rời', ok: 'OK', cancel: 'Hủy', home: 'Trang chủ' },
        th: { create: 'สร้างห้อง', join: 'เข้าร่วม', joinCode: 'เข้าด้วยรหัส', code: 'รหัสห้อง', nick: 'ชื่อเล่น', invite: 'ชวน', copy: 'คัดลอก', copied: 'คัดลอกแล้ว', ready: 'พร้อม', start: 'เริ่ม', host: 'เจ้าของห้อง', watch: 'ดู', play: 'เล่น', leave: 'ออก', ok: 'ตกลง', cancel: 'ยกเลิก', home: 'หน้าแรก' },
        hi: { create: 'रूम बनाएँ', join: 'जुड़ें', joinCode: 'कोड से जुड़ें', code: 'रूम कोड', nick: 'उपनाम', invite: 'बुलाएँ', copy: 'कॉपी', copied: 'कॉपी हुआ', ready: 'तैयार', start: 'शुरू', host: 'होस्ट', watch: 'देखें', play: 'खेलें', leave: 'छोड़ें', ok: 'ठीक', cancel: 'रद्द', home: 'होम' },
        ar: { create: 'أنشئ غرفة', join: 'انضم', joinCode: 'انضم بالرمز', code: 'رمز الغرفة', nick: 'اللقب', invite: 'ادعُ', copy: 'نسخ', copied: 'تم النسخ', ready: 'جاهز', start: 'ابدأ', host: 'المضيف', watch: 'شاهد', play: 'العب', leave: 'غادر', ok: 'حسناً', cancel: 'إلغاء', home: 'الرئيسية' }
    };
    /* 닉네임 생성기 — 형용사+동물 (es/pt 는 동물+형용사) */
    var NICK = {
        ko: [['신나는', '용감한', '졸린', '배고픈', '빠른', '느긋한', '반짝', '수줍은', '행운의', '씩씩한', '엉뚱한', '다정한'], ['판다', '여우', '호랑이', '토끼', '강아지', '고양이', '코알라', '펭귄', '수달', '햄스터', '부엉이', '거북이']],
        en: [['Happy', 'Brave', 'Sleepy', 'Hungry', 'Zippy', 'Chill', 'Shiny', 'Shy', 'Lucky', 'Bold', 'Silly', 'Kind'], ['Panda', 'Fox', 'Tiger', 'Bunny', 'Pup', 'Kitty', 'Koala', 'Otter', 'Owl', 'Duck', 'Frog', 'Bee']],
        ja: [['げんきな', 'ねむい', 'はらぺこ', 'はやい', 'のんびり', 'きらきら', 'てれや', 'ラッキー', 'つよい', 'へんてこ', 'やさしい', 'ゆうかん'], ['パンダ', 'キツネ', 'トラ', 'ウサギ', 'イヌ', 'ネコ', 'コアラ', 'ペンギン', 'カワウソ', 'ハムスター', 'フクロウ', 'カメ']],
        zh: [['开心的', '勇敢的', '困困的', '饿饿的', '飞快的', '悠闲的', '闪亮的', '害羞的', '幸运的', '帅气的', '调皮的', '温柔的'], ['熊猫', '狐狸', '老虎', '兔子', '小狗', '小猫', '考拉', '企鹅', '水獭', '仓鼠', '猫头鹰', '乌龟']],
        es: [['Feliz', 'Veloz', 'Valiente', 'Amable', 'Audaz', 'Genial', 'Alegre', 'Fuerte', 'Ágil', 'Libre', 'Dulce', 'Leal'], ['Panda', 'Zorro', 'Tigre', 'Conejo', 'Perrito', 'Gatito', 'Koala', 'Búho', 'Nutria', 'Pato', 'Rana', 'Oso']],
        pt: [['Feliz', 'Veloz', 'Valente', 'Gentil', 'Audaz', 'Legal', 'Alegre', 'Forte', 'Ágil', 'Livre', 'Doce', 'Leal'], ['Panda', 'Raposa', 'Tigre', 'Coelho', 'Cachorro', 'Gatinho', 'Coala', 'Coruja', 'Lontra', 'Pato', 'Sapo', 'Urso']]
    };

    /* [+] 추첨 띠(drawStrip) 문구 — 빠진 언어는 en */
    var I2 = {
        allowIn: { ko: '참가자 이름 넣기 허용', en: 'Let guests add names', ja: '参加者の名前追加を許可', zh: '允许加入名单', es: 'Permitir añadir nombres', pt: 'Permitir incluir nomes',
            de: 'Namen hinzufügen erlauben', fr: 'Autoriser l’ajout de noms', ru: 'Разрешить добавлять имена', tr: 'İsim eklemeye izin ver', id: 'Izinkan tambah nama',
            vi: 'Cho phép thêm tên', th: 'ให้เพิ่มชื่อได้', hi: 'नाम जोड़ने दें', ar: 'السماح بإضافة الأسماء' },
        fillIn: { ko: '멤버로 채우기', en: 'Fill with members', ja: 'メンバーで埋める', zh: '用成员填充', es: 'Llenar con miembros', pt: 'Preencher com membros',
            de: 'Mit Mitgliedern füllen', fr: 'Remplir avec les membres', ru: 'Заполнить участниками', tr: 'Üyelerle doldur', id: 'Isi dengan anggota',
            vi: 'Điền bằng thành viên', th: 'เติมด้วยสมาชิก', hi: 'सदस्यों से भरें', ar: 'املأ بالأعضاء' }
    };
    Object.keys(I2).forEach(function (k) { Object.keys(I2[k]).forEach(function (l) { if (I[l] && I[l][k] == null) I[l][k] = I2[k][l]; }); });

    function lsGet(k) { try { return G.localStorage.getItem(k); } catch (_) { return null; } }
    function lsSet(k, v) { try { if (v == null) G.localStorage.removeItem(k); else G.localStorage.setItem(k, v); } catch (_) {} }
    function ssGet(k) { try { return G.sessionStorage.getItem(k); } catch (_) { return null; } }
    function ssSet(k, v) { try { if (v == null) G.sessionStorage.removeItem(k); else G.sessionStorage.setItem(k, v); } catch (_) {} }
    function jparse(s, d) { try { var v = JSON.parse(s); return v == null ? d : v; } catch (_) { return d; } }
    function lang() { var l = String(lsGet('luckyplz_lang') || 'en').toLowerCase().slice(0, 2); return l === 'gb' ? 'en' : l; }
    function t(k, v) {
        var L = I[lang()] || I.en, s = L[k] != null ? L[k] : (I.en[k] != null ? I.en[k] : k);
        if (v) s = s.replace(/\{(\w+)\}/g, function (_, x) { return v[x] != null ? String(v[x]) : ''; });
        return s;
    }
    function tl(o) { if (o == null) return ''; if (typeof o === 'string') return o; var l = lang(); return o[l] || o.en || o.ko || ''; }

    /* ── DOM 도구 ───────────────────────────────────────────── */
    function E(tag, cls, txt) { var e = D.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
    function B(cls, txt, fn, aria) {
        var b = E('button', 'lpr-btn' + (cls ? ' ' + cls : ''), txt); b.type = 'button';
        if (aria) b.setAttribute('aria-label', aria);
        if (fn) b.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); if (!b.disabled) fn(e); });
        return b;
    }
    /* 캔버스 게임의 touchstart preventDefault 가 click 합성을 막는 함정(메모리 mobile_canvas_click_trap) —
       우리 층 안의 터치는 게임까지 내려가지 않게 버블 단계에서 멈춘다 */
    function shield(el) {
        ['touchstart', 'touchmove', 'touchend', 'pointerdown', 'pointerup', 'mousedown', 'mouseup', 'keydown', 'keyup', 'wheel'].forEach(function (ev) {
            el.addEventListener(ev, function (e) { e.stopPropagation(); }, { passive: true });
        });
        return el;
    }
    function fmtCode(c) { c = String(c || ''); return c.length === 6 ? c.slice(0, 3) + '-' + c.slice(3) : c; }
    function avOf(i) { return AV[Math.max(0, Math.min(15, i | 0))]; }
    function gname(id) { try { return G.LpGames ? G.LpGames.name(id, lang()) : id; } catch (_) { return id; } }
    function gicon(id) { try { var e = G.LpGames && G.LpGames.get(id); return e ? e.icon : null; } catch (_) { return null; } }
    function reg(id) { try { return G.LpGames && G.LpGames.get(id); } catch (_) { return null; } }
    function iconEl(id, cls) {
        var src = gicon(id), w = E('span', 'lpr-gi' + (cls ? ' ' + cls : ''));
        if (src) { var im = E('img'); im.src = src; im.alt = ''; im.decoding = 'async'; im.onerror = function () { w.textContent = '🎲'; }; w.appendChild(im); }
        else w.textContent = '🎲';
        return w;
    }
    function copyText(s) {
        return new Promise(function (res) {
            try { if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(s).then(function () { res(true); }, fallback); return; } } catch (_) {}
            fallback();
            function fallback() {
                try { var ta = E('textarea'); ta.value = s; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;top:-99px;opacity:0'; D.body.appendChild(ta); ta.select(); var ok = D.execCommand('copy'); ta.remove(); res(!!ok); } catch (_) { res(false); }
            }
        });
    }
    function pageGid() {
        var m = /^\/games\/([a-z0-9-]+)\//.exec(location.pathname);
        if (m) return m[1];
        if (/^\/(lobby|r)(\/|$)/.test(location.pathname)) return 'lobby';
        return null;
    }

    /* ── CSS ─────────────────────────────────────────────────── */
    var CSS =
        '.lpr-root,.lpr-root *{box-sizing:border-box}' +
        '.lpr-root{font-family:"Noto Sans KR",system-ui,-apple-system,"Segoe UI",sans-serif;color:#fff;-webkit-tap-highlight-color:transparent;line-height:1.25;letter-spacing:0;text-align:left}' +
        '.lpr-btn{min-height:44px;min-width:44px;padding:0 14px;border-radius:12px;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.07);color:#fff;' +
        'font:700 15px/1.1 "Noto Sans KR",system-ui,sans-serif;display:inline-flex;align-items:center;justify-content:center;gap:6px;cursor:pointer;touch-action:manipulation;' +
        'white-space:nowrap;text-transform:none;letter-spacing:0;box-shadow:none;transition:background .15s,opacity .15s,border-color .15s}' +
        '.lpr-btn:hover{background:rgba(255,255,255,.12)}.lpr-btn:active{transform:translateY(1px)}' +
        '.lpr-btn:focus-visible{outline:2px solid #FFE66D;outline-offset:2px}' +
        '.lpr-btn.pri{background:linear-gradient(135deg,#00D9FF,#4FC3F7);color:#03131b;border-color:transparent}' +
        '.lpr-btn.go{background:linear-gradient(135deg,#FF6B35,#FFB347);color:#1d0c00;border-color:transparent;font-size:17px}' +
        '.lpr-btn.on{background:rgba(0,217,255,.18);border-color:#00D9FF;color:#bff4ff}' +
        '.lpr-btn.ok{background:rgba(76,217,100,.2);border-color:#4CD964;color:#d9ffe0}' +
        '.lpr-btn.danger{color:#ff9d94;border-color:rgba(255,120,110,.45);background:rgba(255,80,70,.08)}' +
        '.lpr-btn.ghost{background:transparent;border-color:transparent}' +
        '.lpr-btn[disabled]{opacity:.36;cursor:default}' +
        '.lpr-btn.wide{width:100%}' +
        '.lpr-ico{font-size:20px;line-height:1}' +
        '.lpr-gi{display:inline-flex;width:28px;height:28px;align-items:center;justify-content:center;font-size:20px;flex:0 0 auto}' +
        '.lpr-gi img{width:100%;height:100%;object-fit:contain}' +
        /* 바텀시트 */
        '.lpr-bd{position:fixed;inset:0;z-index:9700;background:rgba(3,3,12,.6);display:flex;align-items:flex-end;justify-content:center;animation:lprFade .14s ease}' +
        '.lpr-sheet{width:100%;max-width:520px;max-height:92vh;max-height:92dvh;overflow:auto;background:#141430;border:1px solid rgba(255,255,255,.1);border-bottom:0;' +
        'border-radius:20px 20px 0 0;padding:14px 16px calc(16px + env(safe-area-inset-bottom,0px));box-shadow:0 -12px 40px rgba(0,0,0,.5);animation:lprUp .18s cubic-bezier(.2,.8,.3,1)}' +
        '@media(min-width:720px){.lpr-bd{align-items:center}.lpr-sheet{border-radius:20px;border-bottom:1px solid rgba(255,255,255,.1)}}' +
        '.lpr-sh-h{display:flex;align-items:center;gap:8px;min-height:44px;margin-bottom:8px}' +
        '.lpr-sh-t{flex:1;font-weight:900;font-size:17px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
        '.lpr-x{font-size:20px;color:rgba(255,255,255,.7)}' +
        '.lpr-row{display:flex;gap:8px;align-items:center;margin:8px 0}.lpr-row>.lpr-btn{flex:1}' +
        '.lpr-col{display:flex;flex-direction:column;gap:8px}' +
        '.lpr-mut{color:rgba(255,255,255,.55);font-size:13px}' +
        '.lpr-msg{min-height:20px;font-size:14px;color:#FFE66D;text-align:center;margin:6px 0}.lpr-msg.err{color:#ff9d94}.lpr-msg:empty{min-height:0;margin:0}' +
        '@keyframes lprUp{from{transform:translateY(24px);opacity:.3}to{transform:none;opacity:1}}@keyframes lprFade{from{opacity:0}to{opacity:1}}' +
        /* 입력 */
        '.lpr-in{width:100%;min-height:48px;border-radius:12px;border:1px solid rgba(255,255,255,.2);background:rgba(0,0,0,.35);color:#fff;padding:0 12px;font:700 17px "Noto Sans KR",system-ui,sans-serif;outline:none}' +
        '.lpr-in:focus{border-color:#00D9FF}' +
        '.lpr-cells{position:relative;display:flex;gap:6px;justify-content:center;margin:4px 0}' +
        '.lpr-cell{width:44px;height:54px;border-radius:10px;border:1.5px solid rgba(255,255,255,.22);background:rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;' +
        'font:900 24px "Orbitron",ui-monospace,monospace;color:#00D9FF}' +
        '.lpr-cell.cur{border-color:#00D9FF;box-shadow:0 0 0 2px rgba(0,217,255,.25)}.lpr-cell.dash{width:10px;border:0;background:none;color:rgba(255,255,255,.3)}' +
        '.lpr-cells.bad .lpr-cell{border-color:#ff7b72}' +
        '.lpr-cells input{position:absolute;inset:0;width:100%;height:100%;opacity:0;font-size:16px;border:0;background:transparent;color:transparent;caret-color:transparent}' +
        '.lpr-prof{display:flex;gap:8px;align-items:center}' +
        '.lpr-prof .lpr-in{flex:1;min-width:0}' +
        '.lpr-avs{display:flex;gap:4px;overflow-x:auto;padding:4px 0;scrollbar-width:none}.lpr-avs::-webkit-scrollbar{display:none}' +
        '.lpr-av{flex:0 0 44px;height:44px;border-radius:50%;border:2px solid transparent;background:rgba(255,255,255,.06);font-size:24px;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0}' +
        '.lpr-av.sel{border-color:#FFE66D;background:rgba(255,230,109,.14)}' +
        /* 명단 */
        '.lpr-list{display:flex;flex-direction:column;gap:2px}' +
        '.lpr-m{display:flex;align-items:center;gap:8px;min-height:44px;padding:2px 8px;border-radius:12px;background:rgba(255,255,255,.035)}' +
        '.lpr-m.tap{cursor:pointer}.lpr-m.tap:hover{background:rgba(255,255,255,.08)}' +
        '.lpr-m.me{background:rgba(0,217,255,.08)}' +
        '.lpr-st{width:22px;text-align:center;font-size:15px;flex:0 0 22px}' +
        '.lpr-mav{font-size:24px;width:30px;text-align:center;flex:0 0 30px;position:relative}' +
        '.lpr-mn{flex:1;min-width:0;font-weight:700;font-size:15px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
        '.lpr-mn small{font-weight:400;color:rgba(255,255,255,.5);font-size:12px;margin-left:4px}' +
        '.lpr-dot{width:12px;height:12px;flex:0 0 12px;border-radius:50%;background:#4CD964;box-shadow:0 0 6px rgba(76,217,100,.7)}' +
        '.lpr-dot.away{background:linear-gradient(90deg,#FFD23F 50%,transparent 50%);border:2px solid #FFD23F;box-shadow:none}' +
        '.lpr-dot.off{background:transparent;border:2px solid #8a8aa0;box-shadow:none}' +
        '.lpr-dot.bot{background:none;box-shadow:none;width:auto;font-size:13px}' +
        '.lpr-pk{font-size:20px;min-width:24px;text-align:center}' +
        '.lpr-ask{display:flex;align-items:center;gap:6px;min-height:44px;padding:2px 8px;border-radius:12px;background:rgba(255,230,109,.1);border:1px solid rgba(255,230,109,.35)}' +
        '.lpr-ask .lpr-mn{font-size:14px}.lpr-ask .lpr-btn{min-width:44px;padding:0 10px}' +
        /* 풀 대기실 */
        '.lpr-lobby{position:fixed;inset:0;z-index:9200;background:radial-gradient(ellipse at 50% 0%,rgba(0,217,255,.1),transparent 60%),#0A0A1A;display:flex;justify-content:center}' +
        '.lpr-lb{width:100%;max-width:520px;height:100%;display:flex;flex-direction:column;padding:calc(8px + env(safe-area-inset-top,0px)) 12px calc(10px + env(safe-area-inset-bottom,0px))}' +
        '@media(min-width:720px) and (min-height:600px){.lpr-lobby{align-items:center}.lpr-lb{height:min(calc(100% - 48px),780px);border:1px solid rgba(0,217,255,.22);border-radius:22px;' +
        'background:linear-gradient(160deg,rgba(24,24,52,.96),rgba(12,12,30,.98));box-shadow:0 24px 60px rgba(0,0,0,.55);padding:12px 16px 14px}}' +
        '.lpr-hd{display:flex;align-items:center;gap:8px;min-height:44px}' +
        '.lpr-hd .lpr-gi{width:34px;height:34px}' +
        '.lpr-gn{flex:1;min-width:0;font-weight:900;font-size:17px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
        '.lpr-code{font:900 17px "Orbitron",ui-monospace,monospace;letter-spacing:.06em;color:#00D9FF;background:none;border:0;min-height:44px;padding:0 4px;cursor:pointer}' +
        '.lpr-seal{font-size:16px;letter-spacing:1px;background:none;border:0;min-height:44px;min-width:44px;padding:0 2px;cursor:pointer}' +
        '.lpr-tools{display:flex;gap:8px;align-items:center;margin:4px 0 8px}.lpr-tools .sp{flex:1}' +
        '.lpr-flags{display:flex;gap:4px;font-size:14px;color:rgba(255,255,255,.7)}' +
        '.lpr-body{flex:1;min-height:0;overflow-y:auto;overscroll-behavior:contain;display:flex;flex-direction:column;gap:8px}' +
        '.lpr-spec{display:flex;align-items:center;gap:6px;min-height:44px;padding:0 8px;color:rgba(255,255,255,.65);font-size:14px;background:none;border:0;cursor:pointer;width:100%;text-align:left}' +
        '.lpr-ch{border-top:1px solid rgba(255,255,255,.08);padding-top:6px;display:flex;flex-direction:column;gap:4px}' +
        '.lpr-chr{display:flex;align-items:center;gap:6px;min-height:44px}' +
        '.lpr-chl{width:72px;flex:0 0 72px;font-size:13px;color:rgba(255,255,255,.6);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
        '.lpr-chv{display:flex;gap:4px;flex-wrap:wrap;flex:1}' +
        '.lpr-chip{min-height:44px;min-width:44px;padding:0 10px;border-radius:999px;border:1.5px solid rgba(255,255,255,.18);background:rgba(255,255,255,.05);color:#fff;font:700 15px system-ui,sans-serif;cursor:pointer}' +
        '.lpr-chip.sel{border-color:#FFE66D;background:rgba(255,230,109,.16)}.lpr-chip.tk{opacity:.3}.lpr-chip[disabled]{cursor:default}' +
        '.lpr-ft{display:flex;flex-direction:column;gap:6px;padding-top:6px}' +
        '.lpr-reacts{display:flex;justify-content:space-between;gap:2px}.lpr-reacts .lpr-btn{flex:1;min-width:0;padding:0;font-size:22px;background:transparent;border-color:transparent}' +
        '.lpr-hint{font-size:13px;color:rgba(255,255,255,.55);text-align:center;min-height:16px}' +
        '.lpr-float{position:fixed;z-index:9950;pointer-events:none;font-size:30px;animation:lprFloat 1.4s ease-out forwards}' +
        '@keyframes lprFloat{0%{transform:translateY(0) scale(.6);opacity:0}15%{opacity:1;transform:translateY(-8px) scale(1.1)}100%{transform:translateY(-70px) scale(1);opacity:0}}' +
        /* HUD 알약 */
        '.lpr-hud{position:fixed;z-index:9050;top:calc(10px + env(safe-area-inset-top,0px));right:calc(10px + env(safe-area-inset-right,0px));height:32px;padding:0 10px;border-radius:16px;' +
        'display:flex;align-items:center;gap:6px;background:rgba(10,10,26,.72);border:1px solid rgba(0,217,255,.35);color:#fff;font:700 13px "Noto Sans KR",system-ui,sans-serif;cursor:pointer;' +
        'backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);touch-action:manipulation;transition:padding .15s,opacity .15s}' +
        '.lpr-hud::before{content:"";position:absolute;inset:-6px}' +
        '.lpr-hud .c{font-family:"Orbitron",ui-monospace,monospace;letter-spacing:.04em;color:#00D9FF}' +
        '.lpr-hud.mini{padding:0;width:32px;justify-content:center;opacity:.8}.lpr-hud.mini .c,.lpr-hud.mini .n{display:none}' +
        '.lpr-hud .lpr-dot{width:10px;height:10px;flex:0 0 10px}.lpr-hud .lpr-dot.warn{background:#FFD23F;box-shadow:0 0 6px #FFD23F}.lpr-hud .lpr-dot.bad{background:#ff5a4f;box-shadow:0 0 6px #ff5a4f}' +
        /* 방장 끊김 띠 · 토스트 · 떠남 카드 */
        '.lpr-band{position:fixed;z-index:9960;left:0;right:0;margin:0 auto;width:max-content;top:calc(48px + env(safe-area-inset-top,0px));max-width:calc(100% - 20px);display:flex;align-items:center;gap:8px;white-space:nowrap;' +
        'padding:6px 8px 6px 14px;border-radius:14px;font-weight:700;font-size:14px;background:rgba(60,48,0,.94);border:1px solid #FFD23F;color:#FFE66D}' +
        '.lpr-band.bad{background:rgba(70,10,10,.95);border-color:#ff6b61;color:#ffd4d0}.lpr-band .lpr-btn{min-height:44px;font-size:14px;padding:0 10px}' +
        '.lpr-toast{position:fixed;z-index:9990;left:0;right:0;margin:0 auto;width:max-content;bottom:calc(84px + env(safe-area-inset-bottom,0px));padding:10px 16px;border-radius:999px;background:rgba(10,10,26,.94);' +
        'border:1px solid rgba(255,230,109,.35);color:#fff;font-weight:700;font-size:14px;max-width:90vw;text-align:center;pointer-events:none;animation:lprFade .15s ease}' +
        '.lpr-card{position:fixed;inset:0;z-index:9800;display:flex;align-items:center;justify-content:center;background:rgba(3,3,12,.72);padding:16px}' +
        '.lpr-card>div{width:100%;max-width:360px;background:#141430;border:1px solid rgba(255,255,255,.12);border-radius:20px;padding:20px 16px 14px;text-align:center}' +
        '.lpr-card .big{font-size:44px;line-height:1.1}.lpr-card .tt{font-weight:900;font-size:18px;margin:8px 0 12px}' +
        '.lpr-spin{display:inline-block;width:18px;height:18px;border:2px solid rgba(255,255,255,.25);border-top-color:#00D9FF;border-radius:50%;animation:lprSpin .8s linear infinite;vertical-align:-3px}' +
        '@keyframes lprSpin{to{transform:rotate(360deg)}}' +
        /* 띠형 대기실 */
        '.lpr-strip{display:flex;align-items:center;gap:6px;min-height:44px;padding:4px 6px 4px 10px;border-radius:14px;background:rgba(10,10,26,.78);border:1px solid rgba(0,217,255,.3);margin:0 0 8px;max-width:100%}' +
        '.lpr-strip.fixed{position:fixed;z-index:9045;top:calc(8px + env(safe-area-inset-top,0px));left:50%;transform:translateX(-50%);width:calc(100% - 120px);max-width:480px;margin:0;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}' +
        '.lpr-strip .c{font:900 14px "Orbitron",ui-monospace,monospace;color:#00D9FF;background:none;border:0;padding:0 2px;min-height:44px;cursor:pointer}' +
        '.lpr-strip .who{flex:1;min-width:0;display:flex;align-items:center;overflow:hidden;cursor:pointer;min-height:44px}' +
        '.lpr-strip .who span{font-size:20px;margin-right:-4px;position:relative}.lpr-strip .who span.off{opacity:.35}' +
        '.lpr-strip .who b{margin-left:10px;font-size:13px;color:rgba(255,255,255,.7);white-space:nowrap}' +
        '.lpr-strip .lpr-btn{min-height:44px;padding:0 10px;font-size:14px}' +
        /* 게임 그리드 */
        '.lpr-cats{display:flex;gap:6px;overflow-x:auto;padding:2px 0 6px;scrollbar-width:none}.lpr-cats::-webkit-scrollbar{display:none}' +
        '.lpr-cat{flex:0 0 auto;min-height:44px;padding:0 10px;border-radius:12px;border:1.5px solid rgba(255,255,255,.14);background:rgba(255,255,255,.05);color:#fff;display:flex;align-items:center;gap:6px;font:700 13px system-ui,sans-serif;cursor:pointer}' +
        '.lpr-cat img{width:26px;height:26px;object-fit:contain}.lpr-cat.sel{border-color:#00D9FF;background:rgba(0,217,255,.14)}' +
        '.lpr-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}' +
        '.lpr-tile{min-height:92px;border-radius:14px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.05);color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:6px 4px;cursor:pointer;font:700 13px "Noto Sans KR",system-ui,sans-serif}' +
        '.lpr-tile .lpr-gi{width:48px;height:48px;font-size:34px}.lpr-tile span.nm{max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
        '.lpr-tile.cur{border-color:#FFE66D}' +
        /* 공정 배지 */
        '.lpf-badge{display:inline-flex;align-items:center;gap:4px;min-height:32px;padding:0 12px;border-radius:999px;font:800 13px "Noto Sans KR",system-ui,sans-serif;cursor:pointer;' +
        'border:1px solid rgba(76,217,100,.55);background:rgba(76,217,100,.14);color:#c9ffd2;user-select:none;position:relative}' +
        '.lpf-badge::before{content:"";position:absolute;inset:-6px -2px}' +
        '.lpf-badge.lpf-seed{border-color:rgba(0,217,255,.5);background:rgba(0,217,255,.12);color:#c4f5ff}' +
        '.lpf-badge.lpf-solo{border-color:rgba(255,255,255,.22);background:rgba(255,255,255,.06);color:rgba(255,255,255,.8)}' +
        '.lpf-badge.lpf-mismatch{border-color:rgba(255,190,60,.6);background:rgba(255,190,60,.14);color:#ffe2a8}' +
        '.lpr-qr{display:flex;justify-content:center;margin:6px 0}.lpr-qr svg,.lpr-qr img{width:132px;height:132px;background:#fff;border-radius:10px;padding:6px}' +
        '.lpr-bigcode{font:900 30px "Orbitron",ui-monospace,monospace;letter-spacing:.08em;color:#00D9FF;text-align:center;margin:2px 0}' +
        '.lpr-link{display:flex;gap:6px}.lpr-link .lpr-in{font-size:13px;font-weight:400;min-height:44px}' +
        '.lpr-pause{position:fixed;inset:0;z-index:9150;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;background:rgba(3,3,12,.66);font-weight:900;font-size:22px}' +
        '.lpr-m .lpr-code{min-height:0;line-height:1;align-self:center;padding:0 4px}' +
        '.lpr-hubt{font:900 22px "Noto Sans KR",system-ui,sans-serif;text-align:center;margin:6px 0 10px}' +
        '.lpr-rect{margin:14px 0 4px}' +
        '.lpr-sr{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}' +
        '.lp-rooms-btn{width:38px;height:38px;border-radius:50%;border:1px solid rgba(255,255,255,.35);background:rgba(10,10,26,.55);color:#fff;font-size:18px;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;position:fixed;left:10px;top:200px;z-index:9040}' +
        '.lp-rooms-btn.in{border-color:#00D9FF;box-shadow:0 0 0 2px rgba(0,217,255,.3)}' +
        '.lp-rooms-btn::before{content:"";position:absolute;inset:-4px;border-radius:50%}' +
        '@media(prefers-reduced-motion:reduce){.lpr-bd,.lpr-sheet,.lpr-float,.lpr-toast{animation:none!important}}' +
        '@media(max-width:340px){.lpr-cell{width:38px;height:48px;font-size:20px}.lpr-chl{width:56px;flex-basis:56px}.lpr-gn{font-size:15px}}';
    function injectCss() {
        if (D.getElementById('lpr-css')) return;
        var s = E('style'); s.id = 'lpr-css'; s.textContent = CSS; (D.head || D.documentElement).appendChild(s);
    }

    /* ── 이벤트 버스 ─────────────────────────────────────────── */
    var LS = {};
    function on(ev, cb) { (LS[ev] || (LS[ev] = [])).push(cb); return function () { var a = LS[ev] || [], i = a.indexOf(cb); if (i >= 0) a.splice(i, 1); }; }
    function emit(ev, x) { (LS[ev] || []).slice().forEach(function (cb) { try { cb(x); } catch (e) { if (G.console) console.error(e); } }); }

    /* ── 상태 ────────────────────────────────────────────────── */
    var CFG = {};
    var cur = null;               /* 붙은 방 */
    var offs = [];                /* 방 리스너 해제 */
    var H = { lobby: null, hud: null, strip: null, band: null, pause: null, card: null };
    var bindAt = 0, lastNames = {}, lastTurnN = -1, blockSince = 0;

    /* ── 공용 층: 시트·확인창·토스트·aria-live ─────────────────────── */
    var live = null;
    function say(msg) {
        if (!live) { live = E('div', 'lpr-sr'); live.setAttribute('aria-live', 'polite'); live.setAttribute('role', 'status'); D.body.appendChild(live); }
        live.textContent = ''; setTimeout(function () { live.textContent = String(msg || ''); }, 30);
    }
    var toastT = 0, toastEl = null;
    function toast(msg, ms) {
        if (toastEl) toastEl.remove();
        toastEl = E('div', 'lpr-root lpr-toast', msg); toastEl.setAttribute('role', 'status');
        D.body.appendChild(toastEl); clearTimeout(toastT);
        var el = toastEl; toastT = setTimeout(function () { el.remove(); if (toastEl === el) toastEl = null; }, ms || 1800);
    }
    var sheets = [];
    function sheet(o) {
        o = o || {};
        var bd = shield(E('div', 'lpr-root lpr-bd')), sh = E('div', 'lpr-sheet');
        sh.setAttribute('role', 'dialog'); sh.setAttribute('aria-modal', 'true');
        if (o.cls) sh.className += ' ' + o.cls;
        var hd = E('div', 'lpr-sh-h');
        if (o.icon) hd.appendChild(o.icon);
        var tt = E('div', 'lpr-sh-t', o.title || ''); hd.appendChild(tt);
        if (o.title) sh.setAttribute('aria-label', o.title);
        var x = B('ghost lpr-x', '✕', function () { close(); }, t('cancel'));
        hd.appendChild(x); sh.appendChild(hd);
        if (typeof o.body === 'string') sh.appendChild(E('div', null, o.body)); else if (o.body) sh.appendChild(o.body);
        bd.appendChild(sh);
        bd.addEventListener('click', function (e) { if (e.target === bd && o.dismiss !== false) close(); });
        var closed = false, rec = { el: sh, bd: bd, close: close, title: tt };
        function close() { if (closed) return; closed = true; bd.remove(); var i = sheets.indexOf(rec); if (i >= 0) sheets.splice(i, 1); D.removeEventListener('keydown', esc, true); try { o.onClose && o.onClose(); } catch (_) {} }
        function esc(e) { if (e.key === 'Escape' && sheets[sheets.length - 1] === rec) { e.stopPropagation(); close(); } }
        D.addEventListener('keydown', esc, true);
        D.body.appendChild(bd); sheets.push(rec);
        setTimeout(function () { var f = sh.querySelector('[data-focus]') || x; try { f.focus({ preventScroll: true }); } catch (_) {} }, 30);
        return rec;
    }
    function closeSheets() { sheets.slice().forEach(function (s) { s.close(); }); }
    function confirmBox(msg, o) {
        o = o || {};
        return new Promise(function (res) {
            var done = false, body = E('div', 'lpr-col');
            var row = E('div', 'lpr-row');
            var no = B('', o.cancel || t('cancel'), function () { fin(false); });
            var yes = B(o.danger ? 'danger' : 'pri', o.ok || t('ok'), function () { fin(true); });
            yes.setAttribute('data-focus', '');
            row.appendChild(no); row.appendChild(yes); body.appendChild(row);
            var s = sheet({ title: msg, body: body, onClose: function () { fin(false); } });
            function fin(v) { if (done) return; done = true; s.close(); res(v); }
        });
    }
    function card(icon, title, btns) {
        if (H.card) H.card.remove();
        var c = shield(E('div', 'lpr-root lpr-card')), in_ = E('div');
        c.setAttribute('role', 'alertdialog'); c.setAttribute('aria-label', title);
        in_.appendChild(E('div', 'big', icon)); in_.appendChild(E('div', 'tt', title));
        var row = E('div', 'lpr-row'); (btns || []).forEach(function (b) { row.appendChild(b); }); in_.appendChild(row);
        c.appendChild(in_); D.body.appendChild(c); H.card = c;
        return { el: c, close: function () { c.remove(); if (H.card === c) H.card = null; } };
    }
    function goHome() { location.href = '/'; }

    /* ── 프로필 편집(닉 1칸 + 🎲 + 아바타 줄) ─────────────────────── */
    function genNick() {
        var L = NICK[lang()] || NICK.en, n = '';
        for (var i = 0; i < 12; i++) {
            var a = L[0][Math.floor(Math.random() * L[0].length)], b = L[1][Math.floor(Math.random() * L[1].length)];
            n = (lang() === 'es' || lang() === 'pt') ? b + ' ' + a : (/^(ko|zh|ja)$/.test(lang()) ? a + (lang() === 'ko' ? ' ' : '') + b : a + b);
            if (Array.from(n).length <= 12) break;
        }
        return n;
    }
    function profEditor() {
        var P = G.LpRooms ? G.LpRooms.profile.get() : { nick: '', av: 0 };
        var w = E('div', 'lpr-col'), row = E('div', 'lpr-prof');
        var avb = B('', avOf(P.av), null, 'avatar'); avb.style.fontSize = '24px'; avb.style.padding = '0'; avb.style.width = '48px';
        var inp = E('input', 'lpr-in'); inp.type = 'text'; inp.maxLength = 24; inp.value = P.nick || ''; inp.placeholder = t('nick');
        inp.setAttribute('aria-label', t('nick')); inp.autocomplete = 'nickname'; inp.enterKeyHint = 'go';
        var dice = B('', '🎲', function () { inp.value = genNick(); inp.dispatchEvent(new Event('input')); }, 'random nickname');
        row.appendChild(avb); row.appendChild(inp); row.appendChild(dice); w.appendChild(row);
        var avs = E('div', 'lpr-avs'); avs.setAttribute('role', 'radiogroup'); avs.setAttribute('aria-label', 'avatar');
        var cur_ = P.av | 0;
        AV.forEach(function (a, i) {
            var c = E('button', 'lpr-av' + (i === cur_ ? ' sel' : ''), a); c.type = 'button'; c.setAttribute('role', 'radio'); c.setAttribute('aria-checked', i === cur_ ? 'true' : 'false');
            c.addEventListener('click', function (e) { e.preventDefault(); cur_ = i; avb.textContent = a; [].forEach.call(avs.children, function (x, j) { x.classList.toggle('sel', j === i); x.setAttribute('aria-checked', j === i ? 'true' : 'false'); }); });
            avs.appendChild(c);
        });
        avs.style.display = 'none';
        avb.addEventListener('click', function (e) { e.preventDefault(); avs.style.display = avs.style.display === 'none' ? 'flex' : 'none'; });
        w.appendChild(avs);
        if (!P.nick) avs.style.display = 'flex';
        return {
            el: w, input: inp,
            value: function () { return { nick: (G.LpRooms ? G.LpRooms.util.cleanNick(inp.value) : inp.value.trim()), av: cur_ }; },
            save: function () { var v = this.value(); if (!v.nick) v.nick = genNick(); if (G.LpRooms) G.LpRooms.profile.set(v); inp.value = v.nick; return v; }
        };
    }

    /* ── 코드 입력(6칸) — 한 입력칸 + 칸 모양. 링크 붙여넣기 허용 ──────── */
    function codeInput(o) {
        o = o || {};
        var n = o.len || 6, wrap = E('div', 'lpr-cells'), cells = [];
        for (var i = 0; i < n; i++) {
            if (n === 6 && i === 3) wrap.appendChild(E('div', 'lpr-cell dash', '-'));
            var c = E('div', 'lpr-cell'); c.setAttribute('aria-hidden', 'true'); cells.push(c); wrap.appendChild(c);
        }
        var inp = E('input'); inp.type = 'text'; inp.setAttribute('aria-label', o.label || t('code'));
        inp.autocomplete = 'off'; inp.autocapitalize = 'characters'; inp.spellcheck = false; inp.enterKeyHint = 'go';
        if (o.numeric) { inp.inputMode = 'numeric'; inp.pattern = '[0-9]*'; }
        inp.setAttribute('data-focus', '');
        wrap.appendChild(inp);
        var val = '', inv = null, rawIn = '';
        function norm(s) { return String(s || '').toUpperCase().replace(o.numeric ? /[^0-9]/g : /[^0-9A-Z]/g, '').slice(0, n); }
        function paint() { cells.forEach(function (c, i) { c.textContent = val[i] || ''; c.classList.toggle('cur', i === Math.min(val.length, n - 1) && D.activeElement === inp); }); }
        inp.addEventListener('input', function () {
            var raw = inp.value;
            wrap.classList.remove('bad');
            if (!o.numeric && /[\/#?.]/.test(raw) && G.LpRooms) {
                var p = G.LpRooms.parseInvite(raw);
                if (p) { val = norm(p.code); inv = p; rawIn = raw; inp.value = val; paint(); if (o.onFull) o.onFull(val, p, raw); return; }
            }
            val = norm(raw); inv = null; rawIn = ''; if (inp.value !== val) inp.value = val; paint();
            if (val.length === n && o.onFull) o.onFull(val, null, raw);
        });
        inp.addEventListener('focus', paint); inp.addEventListener('blur', paint);
        inp.addEventListener('keydown', function (e) { if (e.key === 'Enter' && o.onEnter) { e.preventDefault(); o.onEnter(val); } });
        paint();
        return { el: wrap, input: inp, value: function () { return val; }, inv: function () { return inv; }, raw: function () { return inv ? rawIn : val; }, set: function (s) { inp.value = s; val = norm(s); paint(); }, bad: function () { wrap.classList.add('bad'); } };
    }

    /* ── 참가 / 생성 흐름 ─────────────────────────────────────────── */
    var REASON = { not_found: 'notFound', host_conflict: 'conflict', bad_fp: 'badFp', full: 'full', locked: 'locked', banned: 'banned', rate: 'rate',
        denied: 'denied', closed: 'closed', version: 'version', unsupported: 'unsupported', network: 'network', inapp: 'inapp', bad_proof: 'pinBad', error: 'network', collision: 'network', bad_game: 'notFound' };
    function invFor(code) { var v = jparse(ssGet('lpr_inv'), null); return v && v.code === code && v.fp ? { fp: v.fp, tok: v.tok } : null; }
    function saveInv(p) { if (p && p.code && p.inv && p.inv.fp) ssSet('lpr_inv', JSON.stringify({ code: p.code, fp: p.inv.fp, tok: p.inv.tok || null })); }
    function stripHash(u) { return String(u || '').replace(/#.*$/, ''); }

    /* 여기(이 페이지)에서 참가. ui = {msg(txt,err), busy(bool), pin()} 시트 연결점(없으면 카드) */
    function joinHere(code, o, ui) {
        o = o || {};
        ui = ui || statusCard();
        ui.busy(true); ui.msg(t('joining'));
        return G.LpRooms.join({ code: code, inv: o.inv || invFor(code), pin: o.pin, want: o.want, steal: o.steal,
            onStatus: function (s) { if (s.st === 'pending') ui.msg('✋ ' + t('pending')); else if (s.st === 'probing') ui.msg(t('finding')); else if (s.st === 'joining') ui.msg(t('joining')); }
        }).then(function (room) {
            var pg = pageGid();
            if (pg && room.gameId !== pg && pg !== 'lobby' && G.LpGames && G.LpGames.url(room.gameId, room.code)) {
                ui.done && ui.done();
                toast(t('moving')); setTimeout(function () { location.assign(G.LpGames.url(room.gameId, room.code)); }, 250);
                return room;
            }
            if (pg === 'lobby' && room.gameId !== 'lobby' && G.LpGames && G.LpGames.url(room.gameId, room.code)) {
                ui.done && ui.done();
                location.assign(G.LpGames.url(room.gameId, room.code)); return room;
            }
            bind(room);
            ui.done && ui.done();
            return room;
        }, function (e) {
            var r = e && e.reason || 'error';
            ui.busy(false);
            if (r === 'wrong_game' && e.url) { ui.msg(t('moving')); location.replace(stripHash(e.url)); return null; }
            if (r === 'pin_required' || r === 'bad_proof') {
                return ui.pin ? ui.pin(r === 'bad_proof').then(function (pin) { return pin ? joinHere(code, Object.assign({}, o, { pin: pin }), ui) : null; }) : (ui.msg(t('pinNeed'), true), null);
            }
            if (r === 'other_tab') {
                ui.msg(t('otherTab'), true);
                ui.action && ui.action(t('here'), function () { joinHere(code, Object.assign({}, o, { steal: true }), ui); });
                return null;
            }
            if (r === 'inapp') {
                ui.msg(t('inapp'));
                ui.action && ui.action(t('here'), function () { try { if (G.LpInApp && G.LpInApp.dismiss) G.LpInApp.dismiss(); } catch (_) {} joinHere(code, o, ui); });
                var retry = function () { if (D.visibilityState === 'visible') { D.removeEventListener('visibilitychange', retry); setTimeout(function () { joinHere(code, o, ui); }, 400); } };
                D.addEventListener('visibilitychange', retry);
                setTimeout(function () { D.removeEventListener('visibilitychange', retry); if (!cur) joinHere(code, o, ui); }, 9000);
                return null;
            }
            ui.msg(t(REASON[r] || 'network'), true);
            ui.action && ui.action(t('retry'), function () { joinHere(code, o, ui); });
            return null;
        });
    }
    /* 시트 없이 참가할 때(저장된 닉 + 링크) — 작은 가운데 카드 */
    function statusCard() {
        var c = null, msgEl = null, act = null;
        function ensure() {
            if (c) return;
            c = card('👥', '', [B('', t('home'), goHome)]);
            msgEl = c.el.querySelector('.tt');
            act = c.el.querySelector('.lpr-row');
        }
        return {
            msg: function (s, err) { ensure(); msgEl.textContent = s; msgEl.style.color = err ? '#ff9d94' : ''; },
            busy: function () {},
            done: function () { if (c) c.close(); },
            action: function (label, fn) { ensure(); var b = B('pri', label, function () { fn(); }); act.appendChild(b); },
            pin: function (bad) { if (c) c.close(); c = null; return askPin(bad); }
        };
    }
    function askPin(bad) {
        return new Promise(function (res) {
            var body = E('div', 'lpr-col'), done = false;
            var msg = E('div', 'lpr-msg' + (bad ? ' err' : ''), bad ? t('pinBad') : t('pinNeed'));
            var ci = codeInput({ len: 4, numeric: true, label: 'PIN', onFull: function (v) { fin(v); } });
            if (bad) ci.bad();
            body.appendChild(ci.el); body.appendChild(msg);
            var s = sheet({ title: '🔑 ' + t('pin'), body: body, onClose: function () { fin(null); } });
            function fin(v) { if (done) return; done = true; s.close(); res(v); }
        });
    }
    /* 시트 안의 상태 줄 · 버튼 연결 */
    function sheetUI(msgEl, mainBtn, extraRow) {
        return {
            msg: function (s, err) { msgEl.textContent = s || ''; msgEl.className = 'lpr-msg' + (err ? ' err' : ''); },
            busy: function (b) { if (mainBtn) mainBtn.disabled = !!b; },
            action: function (label, fn) { if (!extraRow) return; extraRow.innerHTML = ''; extraRow.appendChild(B('pri', label, function () { extraRow.innerHTML = ''; fn(); })); },
            pin: function (bad) { return askPin(bad); }
        };
    }

    /* 코드·링크 → resolve → 여기서 참가 / 다른 페이지로 이동 */
    function route(input, o, ui) {
        o = o || {};
        ui.busy(true); ui.msg(t('finding'));
        var p = G.LpRooms.parseInvite(input);
        if (p) saveInv(p);
        return G.LpRooms.resolve(input).then(function (r) {
            ui.busy(false);
            if (!r || r.kind === 'none') { ui.msg(t(r && r.reason === 'host_conflict' ? 'conflict' : 'notFound'), true); return null; }
            if (r.kind === 'choice' && r.options) {
                ui.msg('');
                ui.choice && ui.choice(r.options.map(function (op) { return { label: op.kind === 'qlive' ? '❓ ' + gname('quiz') : '🚀 ' + gname('dodge'), url: op.url }; }));
                return null;
            }
            var pg = pageGid();
            if (r.kind === 'rooms' && o.here !== false && pg && (r.gameId === pg || (pg === 'lobby' && r.gameId === 'lobby'))) {
                return joinHere(r.code, { inv: p && p.inv }, ui);
            }
            ui.msg(t('moving'));
            if (/^\/r\//.test(location.pathname)) location.replace(stripHash(r.url)); else location.assign(stripHash(r.url));
            return null;
        }, function () { ui.busy(false); ui.msg(t('network'), true); return null; });
    }

    function openJoin(o) {
        o = o || {};
        if (!G.LpRooms) return Promise.resolve();
        /* [+] 링크로 온 게임의 자동 참가(추첨 게임 계약) — 코드가 온전하고 닉이 저장돼 있으면 시트 없이 바로 */
        var oc = o.code && G.LpRooms.util && G.LpRooms.util.normCode ? G.LpRooms.util.normCode(o.code) : null;
        if (oc && o.inv && o.inv.fp) saveInv({ code: oc, inv: o.inv });
        if (oc && !o.sheet && G.LpRooms.profile.get().nick) {
            if (cur && cur.code === oc && !cur._left) return Promise.resolve();
            var pg0 = pageGid();
            if (pg0 && pg0 !== 'lobby') return joinHere(oc, { inv: (o.inv && o.inv.fp ? o.inv : null) || invFor(oc) }).then(function () {});
            return route(oc, {}, statusCard()).then(function () {});
        }
        var body = E('div', 'lpr-col'), msg = E('div', 'lpr-msg'), extra = E('div', 'lpr-row');
        var needProf = !G.LpRooms.profile.get().nick && pageGid();
        var prof = needProf ? profEditor() : null;
        var go = B('pri wide', t('join'), function () { submit(); });
        var ui = sheetUI(msg, go, extra);
        ui.choice = function (opts) { extra.innerHTML = ''; opts.forEach(function (op) { extra.appendChild(B('', op.label, function () { location.assign(op.url); })); }); };
        var ci = codeInput({ onFull: function () { if (!prof) submit(); }, onEnter: function () { submit(); } });
        if (o.code) ci.set(o.code);
        body.appendChild(ci.el);
        if (prof) body.appendChild(prof.el);
        body.appendChild(msg); body.appendChild(go); body.appendChild(extra);
        var s = sheet({ title: '🔑 ' + t('joinCode'), body: body });
        ui.done = function () { s.close(); };
        function submit() {
            var v = ci.value(), p = ci.inv();
            if (!p && v.length < 6) { ci.bad(); ui.msg(t('notFound'), true); return; }
            if (prof) prof.save();
            route(ci.raw(), {}, ui);
        }
        return Promise.resolve();
    }

    function doCreate(gid, o) {
        o = o || {};
        var ui = o.ui;
        if (ui) { ui.busy(true); ui.msg(t('creating')); }
        return G.LpRooms.create({ gameId: gid, pinReq: !!o.pinReq }).then(function (room) {
            bind(room);
            if (ui && ui.done) ui.done();
            return room;
        }, function (e) {
            var r = e && e.reason || 'error';
            if (ui) { ui.busy(false); ui.msg(t(REASON[r] || 'network'), true); }
            else toast(t(REASON[r] || 'network'));
            return null;
        });
    }
    function openCreate(o) {
        o = o || {};
        if (!G.LpRooms) return Promise.resolve(null);
        if (cur) { openRoom(cur); return Promise.resolve(cur); }
        var gid = o.gameId || CFG.gameId || pageGid();
        if (o.pick || !gid) return new Promise(function (res) { gameGrid({ title: '＋ ' + t('create'), withGather: true, onPick: function (id) { res(null); goCreate(id); } }); });
        return new Promise(function (res) {
            var body = E('div', 'lpr-col'), prof = profEditor(), msg = E('div', 'lpr-msg');
            var pinOn = false;
            var pinB = B('', '🔑 ' + t('pin'), function () { pinOn = !pinOn; pinB.classList.toggle('on', pinOn); pinB.setAttribute('aria-pressed', pinOn ? 'true' : 'false'); });
            pinB.setAttribute('aria-pressed', 'false'); pinB.style.flex = '0 0 auto';
            var go = B('go', '＋ ' + t('create'), function () { prof.save(); doCreate(gid, { pinReq: pinOn, ui: ui }).then(function (r) { if (r) res(r); }); });
            go.setAttribute('data-focus', '');
            var ui = sheetUI(msg, go, null);
            body.appendChild(prof.el);
            var row = E('div', 'lpr-row'); row.appendChild(pinB); row.appendChild(go); body.appendChild(row); body.appendChild(msg);
            var jr = E('div', 'lpr-row'); jr.appendChild(B('ghost', '🔑 ' + t('joinCode'), function () { s.close(); openJoin(); })); body.appendChild(jr);
            var s = sheet({ title: gname(gid), icon: iconEl(gid), body: body, onClose: function () { res(cur); } });
            ui.done = function () { s.close(); };
        });
    }
    /* 허브·그리드에서 고른 게임으로 방 만들기 */
    function goCreate(id) {
        if (id === 'lobby' || id === pageGid()) { openCreate({ gameId: id }); return; }
        var path = G.LpGames && G.LpGames.path(id);
        if (!path) return;
        location.assign(path + (v2ok(id) ? '?lpr=new' : ''));
    }

    /* ── 게임 그리드(허브 만들기 · 방장 게임 바꾸기) ─────────────────── */
    var CAT_ICON = { random: 'toy-cat-random', draw: 'toy-cat-draw', arcade: 'toy-cat-arcade', mission: 'toy-cat-mission', board: 'toy-cat-board' };
    var CAT_NAME = {
        random: { ko: '랜덤뽑기', en: 'Random', ja: 'ランダム', zh: '随机', es: 'Azar', pt: 'Sorteio' },
        draw: { ko: '추첨', en: 'Draws', ja: '抽選', zh: '抽奖', es: 'Sorteos', pt: 'Sorteios' },
        arcade: { ko: '아케이드', en: 'Arcade', ja: 'アーケード', zh: '街机', es: 'Arcade', pt: 'Arcade' },
        mission: { ko: '미션', en: 'Mission', ja: 'ミッション', zh: '任务', es: 'Misión', pt: 'Missão' },
        board: { ko: '보드', en: 'Board', ja: 'ボード', zh: '棋盘', es: 'Tablero', pt: 'Tabuleiro' }
    };
    /* v2 로 방을 열 수 있는 게임: 레지스트리 유효 버전 v2, 또는 이 탭이 ?rooms=v2 로 강제된 경우(멀티 가능 게임 전부) */
    function v2ok(id) { try { var v = G.LpGames.v(id); return v === 'v2' || (v !== 'off' && ssGet('lpr_v2') === '1'); } catch (_) { return false; } }
    function gameList(onlyV2) {
        if (!G.LpGames) return [];
        var l = onlyV2 ? G.LpGames.mp().filter(function (e) { return v2ok(e.id); }) : G.LpGames.mp();
        return l.filter(function (e) { return e.id !== 'lobby'; });
    }
    function gridEl(o) {
        var w = E('div', 'lpr-col'), list = gameList(o.onlyV2);
        var cats = G.LpGames ? G.LpGames.cats().filter(function (c) { return list.some(function (e) { return e.cat === c; }); }) : [];
        var sel = o.cat && cats.indexOf(o.cat) >= 0 ? o.cat : (cats.indexOf(reg(o.current || '') && reg(o.current).cat) >= 0 ? reg(o.current).cat : cats[0]);
        var cr = E('div', 'lpr-cats'), grid = E('div', 'lpr-grid');
        cats.forEach(function (c) {
            var b = E('button', 'lpr-cat' + (c === sel ? ' sel' : '')); b.type = 'button';
            var im = E('img'); im.src = '/assets/tiles/' + CAT_ICON[c] + '.webp'; im.alt = ''; b.appendChild(im); b.appendChild(E('span', null, tl(CAT_NAME[c])));
            b.addEventListener('click', function (e) { e.preventDefault(); sel = c; [].forEach.call(cr.children, function (x) { x.classList.toggle('sel', x === b); }); paint(); });
            cr.appendChild(b);
        });
        function tile(id, name) {
            var b = E('button', 'lpr-tile' + (id === o.current ? ' cur' : '')); b.type = 'button';
            b.appendChild(iconEl(id)); b.appendChild(E('span', 'nm', name || gname(id)));
            b.addEventListener('click', function (e) { e.preventDefault(); o.onPick(id); });
            return b;
        }
        function paint() {
            grid.innerHTML = '';
            if (o.withGather && gameList(true).length) grid.appendChild(tile('lobby', '👥 ' + gname('lobby')));
            list.filter(function (e) { return e.cat === sel; }).forEach(function (e) { grid.appendChild(tile(e.id)); });
        }
        paint();
        if (cats.length > 1) w.appendChild(cr);
        w.appendChild(grid);
        if (!list.length && !o.withGather) w.appendChild(E('div', 'lpr-mut', '—'));
        return w;
    }
    function gameGrid(o) {
        var s = sheet({ title: o.title, body: gridEl({ withGather: o.withGather, onlyV2: o.onlyV2, current: o.current, onPick: function (id) { s.close(); o.onPick(id); } }) });
        return s;
    }
    function openSwitch(room) {
        room = room || cur; if (!room || !room.isHost) return;
        gameGrid({ title: '🎮 ' + t('switchG'), onlyV2: true, current: room.gameId, onPick: function (id) {
            if (id === room.gameId) return;
            if (room.switchGame(id) !== false) toast(t('moving'));
        } });
    }

    /* ── 명단 ─────────────────────────────────────────────────── */
    function humans(room) { return room.roster().filter(function (m) { return m.r !== 'bot'; }); }
    function players(room) { return room.roster().filter(function (m) { return m.r !== 'spec'; }); }
    function specs(room) { return room.roster().filter(function (m) { return m.r === 'spec'; }); }
    function connEl(m) {
        var d = E('span', 'lpr-dot');
        if (m.r === 'bot') { d.className = 'lpr-dot bot'; d.textContent = '🤖'; d.setAttribute('aria-label', t('bot')); return d; }
        var c = m.c === 'away' ? 'away' : m.c === 'off' ? 'off' : 'on';
        if (c !== 'on') d.classList.add(c);
        d.setAttribute('role', 'img'); d.setAttribute('aria-label', t(c)); d.title = t(c);
        return d;
    }
    function pickDisp(key, val) {
        var L = CFG.labels || {}, k = key + '.' + val;
        if (L[k] != null) return tl(L[k]);
        return String(val);
    }
    function memberRow(room, m, o) {
        o = o || {};
        var me = m.p === room.me.pid, r = E('div', 'lpr-m' + (me ? ' me' : ''));
        r.setAttribute('data-pid', m.p);
        var st = E('span', 'lpr-st', m.r === 'host' ? '👑' : m.rd && m.r === 'player' ? '✓' : '');
        if (m.r === 'host') st.setAttribute('aria-label', t('host'));
        else if (m.rd && m.r === 'player') { st.setAttribute('aria-label', t('readyOn')); st.style.color = '#4CD964'; }
        r.appendChild(st);
        r.appendChild(E('span', 'lpr-mav', m.r === 'bot' ? '🤖' : avOf(m.av)));
        var nm = E('span', 'lpr-mn', m.n || '?');
        if (me) nm.appendChild(E('small', null, '(' + t('me') + ')'));
        if (m.au) nm.appendChild(E('small', null, '✓'));
        r.appendChild(nm);
        var pk = m.pick || {};
        Object.keys(pk).slice(0, 2).forEach(function (k) { r.appendChild(E('span', 'lpr-pk', pickDisp(k, pk[k]))); });
        r.appendChild(connEl(m));
        if (o.tap && room.isHost && !me) {
            r.classList.add('tap'); r.tabIndex = 0; r.setAttribute('role', 'button');
            r.addEventListener('click', function () { memberSheet(room, m); });
            r.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); memberSheet(room, m); } });
        }
        return r;
    }
    function pendingRows(room) {
        var w = E('div', 'lpr-col');
        if (!room.isHost || !room.pending) return w;
        room.pending().forEach(function (q) {
            var r = E('div', 'lpr-ask');
            r.appendChild(E('span', 'lpr-mav', avOf(q.av)));
            r.appendChild(E('span', 'lpr-mn', (q.flag ? '⚠ ' : '✋ ') + q.n));
            r.appendChild(B('ok', '✓', function () { room.approve(q.p, true); refreshAll(); }, t('ok')));
            r.appendChild(B('danger', '✕', function () { room.approve(q.p, false); refreshAll(); }, t('cancel')));
            w.appendChild(r);
        });
        return w;
    }
    function rosterEl(room, o) {
        o = o || {};
        var w = E('div', 'lpr-list');
        w.appendChild(pendingRows(room));
        var ps = players(room).sort(function (a, b) { return (a.r === 'host' ? -1 : 0) - (b.r === 'host' ? -1 : 0) || ((a.seat == null ? 99 : a.seat) - (b.seat == null ? 99 : b.seat)) || a.j - b.j; });
        ps.forEach(function (m) { w.appendChild(memberRow(room, m, { tap: true })); });
        if (CFG.bots && room.isHost && room.state().phase === 'lobby') {
            var ab = B('', '＋ 🤖 ' + t('addBot'), function () { try { CFG.bots.add(room); } catch (_) {} });
            ab.style.alignSelf = 'flex-start'; w.appendChild(ab);
        }
        var sp = specs(room);
        if (sp.length) {
            var open = !!o.specOpen;
            var sb = E('button', 'lpr-spec'); sb.type = 'button'; sb.setAttribute('aria-expanded', open ? 'true' : 'false');
            sb.textContent = '👀 ' + t('watchN', { n: sp.length }) + ' ' + (open ? '▴' : '▾');
            var sl = E('div', 'lpr-list'); sl.style.display = open ? '' : 'none';
            sp.forEach(function (m) { sl.appendChild(memberRow(room, m, { tap: true })); });
            sb.addEventListener('click', function () { var v = sl.style.display === 'none'; sl.style.display = v ? '' : 'none'; sb.setAttribute('aria-expanded', v ? 'true' : 'false'); sb.textContent = '👀 ' + t('watchN', { n: sp.length }) + ' ' + (v ? '▴' : '▾'); if (o.onSpec) o.onSpec(v); });
            w.appendChild(sb); w.appendChild(sl);
        }
        return w;
    }
    function memberSheet(room, m) {
        var body = E('div', 'lpr-col');
        var S = room.state();
        if (m.r === 'bot') {
            if (CFG.bots) body.appendChild(B('danger wide', '✕ ' + t('rmBot'), function () { s.close(); try { CFG.bots.remove(room, m.p); } catch (_) {} }));
        } else {
            if ((S.phase === 'lobby' || S.phase === 'result') && m.c !== 'off') body.appendChild(B('wide', '👑 ' + t('makeHost'), function () { s.close(); confirmBox(t('makeHost') + ' · ' + m.n + '?').then(function (ok) { if (ok) room.transferHost(m.p); }); }));
            if (m.r === 'player') body.appendChild(B('wide', '👀 ' + t('toWatch'), function () { s.close(); toWatch(room, [m.p]); }));
            body.appendChild(B('wide', '🚪 ' + t('kick'), function () { s.close(); confirmBox(t('kickQ', { n: m.n })).then(function (ok) { if (ok) room.kick(m.p); }); }));
            body.appendChild(B('danger wide', '⛔ ' + t('ban'), function () { s.close(); confirmBox(t('banQ', { n: m.n }), { danger: true, ok: t('ban') }).then(function (ok) { if (ok) room.kick(m.p, { ban: true }); }); }));
        }
        var s = sheet({ title: (m.r === 'bot' ? '🤖 ' : avOf(m.av) + ' ') + m.n, body: body });
    }
    function toWatch(room, pids) {
        room.setState(function (S) { S.roster.forEach(function (x) { if (pids.indexOf(x.p) >= 0 && x.r === 'player') { x.r = 'spec'; x.seat = null; x.rd = false; } }); });
    }

    /* ── 선택 칸(캐릭터·색·자리 + 방장 옵션) ────────────────────────── */
    function choices(room) {
        if (CFG.choices) return CFG.choices;
        var ad = G.LpRooms.getAdapter && G.LpRooms.getAdapter();
        var gid = room.state().gameId;
        if (ad && ad.gameId === gid && (ad.picks || ad.options)) return { picks: ad.picks || [], options: ad.options || [] };
        var e = reg(gid); var c = e && e.mp && e.mp.choices;
        return c ? { picks: c.picks || [], options: c.options || [] } : { picks: [], options: [] };
    }
    function choicesEl(room) {
        var ch = choices(room), S = room.state(), me = room.roster().filter(function (m) { return m.p === room.me.pid; })[0];
        var w = E('div', 'lpr-ch'), any = false;
        (ch.picks || []).forEach(function (pk) {
            if (!pk.options || !pk.options.length || !me || me.r === 'spec') return;
            any = true;
            var r = E('div', 'lpr-chr'); r.appendChild(E('span', 'lpr-chl', tl((CFG.labels || {})[pk.key]) || t(pk.key)));
            var v = E('div', 'lpr-chv'); v.setAttribute('role', 'radiogroup'); v.setAttribute('aria-label', pk.key);
            pk.options.forEach(function (op) {
                var holder = room.roster().filter(function (m) { return m.p !== me.p && m.pick && m.pick[pk.key] === op; })[0];
                var taken = pk.unique && holder && !(holder.r === 'bot' && pk.botYield !== false);
                var sel = me.pick && me.pick[pk.key] === op;
                var b = E('button', 'lpr-chip' + (sel ? ' sel' : '') + (taken ? ' tk' : ''), pickDisp(pk.key, op)); b.type = 'button';
                b.setAttribute('role', 'radio'); b.setAttribute('aria-checked', sel ? 'true' : 'false');
                if (taken) b.setAttribute('aria-disabled', 'true');
                b.addEventListener('click', function (e) {
                    e.preventDefault();
                    if (taken) { toast(t('taken')); return; }
                    room.intent('pick', { key: pk.key, val: op }).then(function (r) { if (r && !r.ok && r.reason === 'taken') toast(t('taken')); });
                });
                v.appendChild(b);
            });
            r.appendChild(v); w.appendChild(r);
        });
        (ch.options || []).forEach(function (op) {
            any = true;
            var curV = S.opts && S.opts[op.key] !== undefined ? S.opts[op.key] : op.def;
            var r = E('div', 'lpr-chr'); r.appendChild(E('span', 'lpr-chl', tl((CFG.labels || {})[op.key]) || t(op.key)));
            var v = E('div', 'lpr-chv');
            op.values.forEach(function (val) {
                var sel = String(val) === String(curV);
                var b = E('button', 'lpr-chip' + (sel ? ' sel' : ''), pickDisp(op.key, val)); b.type = 'button';
                b.setAttribute('aria-pressed', sel ? 'true' : 'false');
                if (!room.isHost) b.disabled = true;
                else b.addEventListener('click', function (e) { e.preventDefault(); room.setState(function (S2) { S2.opts = S2.opts || {}; S2.opts[op.key] = val; }); });
                v.appendChild(b);
            });
            r.appendChild(v); w.appendChild(r);
        });
        return any ? w : null;
    }

    /* ── 리액션 ───────────────────────────────────────────────── */
    function reactRow(room) {
        var w = E('div', 'lpr-reacts');
        REACT.forEach(function (em, i) { w.appendChild(B('', em, function () { room.react(i); }, em)); });
        return w;
    }
    function floatReact(i, from) {
        var em = REACT[Math.max(0, Math.min(5, i | 0))];
        var anchor = D.querySelector('.lpr-lobby [data-pid="' + from + '"] .lpr-mav') || D.querySelector('.lpr-strip .who') || D.querySelector('.lpr-hud');
        var x = G.innerWidth / 2, y = G.innerHeight / 2;
        if (anchor) { var r = anchor.getBoundingClientRect(); x = r.left + r.width / 2; y = r.top; }
        var f = E('div', 'lpr-float', em); f.style.left = (x - 15) + 'px'; f.style.top = (y - 20) + 'px'; f.setAttribute('aria-hidden', 'true');
        D.body.appendChild(f); setTimeout(function () { f.remove(); }, 1500);
    }

    /* ── 시작 게이트 ───────────────────────────────────────────── */
    function minPlayers(room) {
        if (CFG.minPlayers) return CFG.minPlayers;
        var ad = G.LpRooms.getAdapter && G.LpRooms.getAdapter(), gid = room.state().gameId;
        var seats = ad && ad.gameId === gid && ad.seats !== undefined ? ad.seats : (reg(gid) && reg(gid).mp ? reg(gid).mp.seats : null);
        return seats ? seats[0] : 1;
    }
    function gateInfo(room) {
        var ps = players(room), min = minPlayers(room);
        var guests = ps.filter(function (m) { return m.r === 'player'; });
        var rdy = guests.filter(function (m) { return m.rd && m.c === 'on'; });
        return { ok: room.canStart(), need: Math.max(0, min - ps.length), ready: rdy.length, total: guests.length, notReady: guests.filter(function (m) { return !(m.rd && m.c === 'on'); }).map(function (m) { return m.p; }) };
    }
    function hostStart(room) {
        try { if (CFG.onStart && CFG.onStart(room) === false) return; } catch (_) {}
        room.start({ countdownMs: 1500 });
    }

    /* ── 풀 대기실 ─────────────────────────────────────────────── */
    function mountLobby(room, o) {
        o = o || {};
        room = room || cur;
        if (H.lobby) H.lobby.remove();
        injectCss();
        var root = shield(E('div', 'lpr-root lpr-lobby')), lb = E('div', 'lpr-lb');
        root.setAttribute('role', 'dialog'); root.setAttribute('aria-label', gname(room.gameId));
        root.appendChild(lb);
        var specOpen = false;
        function render() {
            var S = room.state(); if (!S) return;
            var oldB = lb.querySelector('.lpr-body'), keep = oldB ? oldB.scrollTop : 0;
            lb.innerHTML = '';
            /* 머리: 게임 · 코드 · 봉인 이모지 */
            var hd = E('div', 'lpr-hd');
            hd.appendChild(iconEl(S.gameId));
            hd.appendChild(E('div', 'lpr-gn', gname(S.gameId)));
            var cb = E('button', 'lpr-code', fmtCode(room.code)); cb.type = 'button'; cb.setAttribute('aria-label', t('code') + ' ' + room.code);
            cb.addEventListener('click', function () { copyText(room.inviteUrl()).then(function (ok) { toast(ok ? t('copied') : room.code); }); });
            hd.appendChild(cb);
            var sb = E('button', 'lpr-seal', room.seal || ''); sb.type = 'button'; sb.setAttribute('aria-label', t('sealHint'));
            sb.addEventListener('click', function () { toast(room.seal + ' · ' + t('sealHint'), 2400); });
            hd.appendChild(sb);
            lb.appendChild(hd);
            /* 도구: 초대 · QR · 상태 깃발 · ⋯ */
            var tools = E('div', 'lpr-tools');
            tools.appendChild(B('pri', '💬 ' + t('invite'), function () { openInvite(room); }));
            tools.appendChild(B('', '▦ QR', function () { openInvite(room, { qr: true }); }, 'QR'));
            var flags = E('span', 'lpr-flags');
            if (S.lock) flags.appendChild(E('span', null, '🔒'));
            if (S.appr) flags.appendChild(E('span', null, '✋'));
            if (S.pinReq) flags.appendChild(E('span', null, '🔑'));
            if (room._pinFlood && Date.now() < room._pinFlood) flags.appendChild(E('span', null, '⚠'));
            tools.appendChild(flags);
            tools.appendChild(E('span', 'sp'));
            tools.appendChild(B('', '⋯', function () { openRoom(room); }, room.isHost ? t('host') : t('leave')));
            lb.appendChild(tools);
            /* 몸통: 명단 + 선택 칸 */
            var body = E('div', 'lpr-body');
            body.appendChild(rosterEl(room, { specOpen: specOpen, onSpec: function (v) { specOpen = v; } }));
            var ch = S.gameId !== 'lobby' ? choicesEl(room) : null;
            lb.appendChild(body);
            if (keep) body.scrollTop = keep;
            if (ch) lb.appendChild(ch);
            /* 발: 리액션 · 준비/시작 */
            var ft = E('div', 'lpr-ft');
            ft.appendChild(reactRow(room));
            var me = room.roster().filter(function (m) { return m.p === room.me.pid; })[0] || {};
            var hint = E('div', 'lpr-hint');
            if (S.gameId === 'lobby') {
                if (room.isHost) ft.appendChild(B('go wide', '🎮 ' + t('pickGame'), function () { openSwitch(room); }));
                else hint.textContent = '⏳ ' + t('pickingGame');
            } else if (room.isHost) {
                var g = gateInfo(room);
                var sbtn = B('go wide', '▶ ' + t('start'), function () { hostStart(room); });
                sbtn.disabled = !g.ok;
                if (g.need > 0) hint.textContent = '👥 ' + t('needN', { n: g.need });
                else if (!g.ok) hint.textContent = '⏳ ' + t('needReady', { a: g.ready, b: g.total });
                if (!g.ok && g.need === 0 && g.notReady.length && g.ready > 0 && blockSince && Date.now() - blockSince > 20000) {
                    var row = E('div', 'lpr-row');
                    row.appendChild(B('', '👀▶ ' + t('startAny'), function () { toWatch(room, g.notReady); setTimeout(function () { if (room.canStart()) hostStart(room); }, 250); }));
                    ft.appendChild(row);
                }
                ft.appendChild(sbtn);
            } else if (me.r === 'spec') {
                ft.appendChild(B('wide', '🙋 ' + t('play'), function () { room.intent('role', 'play'); }));
            } else {
                var rd = !!me.rd;
                var rb = B((rd ? 'ok' : 'go') + ' wide', rd ? '✓ ' + t('readyOn') : t('ready'), function () { room.intent('ready', !rd); });
                rb.setAttribute('aria-pressed', rd ? 'true' : 'false');
                ft.appendChild(rb);
                hint.textContent = '▶ ' + t('waitHost');
            }
            ft.appendChild(hint);
            lb.appendChild(ft);
        }
        render();
        (o.into || D.body).appendChild(root);
        var hdl = { el: root, refresh: render, remove: function () { root.remove(); if (H.lobby === hdl) H.lobby = null; } };
        H.lobby = hdl;
        emit('lobby');
        return hdl;
    }

    /* ── HUD 알약 ─────────────────────────────────────────────── */
    function mountHud(room) {
        room = room || cur;
        if (H.hud) H.hud.remove();
        injectCss();
        var b = shield(E('button', 'lpr-root lpr-hud')); b.type = 'button';
        var c = E('span', 'c'), n = E('span', 'n'), d = E('span', 'lpr-dot');
        b.appendChild(c); b.appendChild(n); b.appendChild(d);
        b.addEventListener('click', function (e) { e.preventDefault(); openRoom(room); });
        var lvl = 0;
        function render() {
            if (!room.state()) return;
            c.textContent = fmtCode(room.code);
            n.textContent = '👥' + humans(room).length;
            d.className = 'lpr-dot' + (lvl === 1 ? ' warn' : lvl >= 2 ? ' bad' : '');
            b.setAttribute('aria-label', t('code') + ' ' + room.code + ', ' + humans(room).length);
            var playing = G.LpChrome && G.LpChrome.isPlaying && G.LpChrome.isPlaying();
            b.classList.toggle('mini', !!playing);
            b.style.display = (H.lobby || stripShown()) ? 'none' : '';
        }
        render();
        D.body.appendChild(b);
        var hdl = { el: b, refresh: render, remove: function () { b.remove(); if (H.hud === hdl) H.hud = null; }, level: function (l) { lvl = l; render(); } };
        H.hud = hdl;
        return hdl;
    }

    /* ── 띠형 대기실 ───────────────────────────────────────────── */
    /* 띠가 화면에 보이는 동안엔 HUD 알약을 숨긴다(같은 정보 두 번 X). 게임이 설정 화면을 숨기거나 스크롤로 벗어나면 HUD 가 돌아온다 */
    function stripShown() {
        var w = H.strip && H.strip.el; if (!w || !w.isConnected) return false;
        var r = w.getBoundingClientRect();
        if (!r.width || !r.height || r.bottom <= 0 || r.top >= G.innerHeight) return false;
        for (var n = w; n && n.nodeType === 1; n = n.parentElement) { var cs = getComputedStyle(n); if (cs.visibility === 'hidden' || +cs.opacity < 0.05) return false; }
        return true;
    }
    function stripEl_() { var s = CFG.stripEl; try { return typeof s === 'function' ? s() : s; } catch (_) { return null; } }
    function strip(room, el) {
        room = room || cur;
        if (H.strip) H.strip.remove();
        injectCss();
        var host = el || stripEl_();
        var w = shield(E('div', 'lpr-root lpr-strip' + (host ? '' : ' fixed')));
        w.setAttribute('role', 'group'); w.setAttribute('aria-label', t('rooms'));
        function render() {
            if (!room.state()) return;
            w.innerHTML = '';
            var cb = E('button', 'c', fmtCode(room.code)); cb.type = 'button';
            cb.addEventListener('click', function () { openInvite(room); });
            w.appendChild(cb);
            var who = E('div', 'who'); who.setAttribute('role', 'button'); who.tabIndex = 0;
            var hs = humans(room);
            hs.slice(0, 8).forEach(function (m) { var s = E('span', m.c === 'off' ? 'off' : '', avOf(m.av)); s.title = m.n; who.appendChild(s); });
            who.appendChild(E('b', null, '👥' + hs.length + (hs.length > 8 ? '+' : '')));
            who.addEventListener('click', function () { openRoom(room); });
            w.appendChild(who);
            var ds = DS && DS.room === room ? DS : null;       /* 추첨 게임 계약(drawStrip) */
            if (room.isHost && ds) {
                if (ds.onAllow) {
                    var al = B(ds.allow ? 'on' : '', '✋', function () { try { ds.onAllow(); } catch (_) {} }, t('allowIn'));
                    al.setAttribute('aria-pressed', ds.allow ? 'true' : 'false'); al.setAttribute('data-k', 'allow'); w.appendChild(al);
                }
                if (ds.onFill) { var fb = B('', '👥', function () { try { ds.onFill(); } catch (_) {} }, t('fillIn')); fb.setAttribute('data-k', 'fill'); w.appendChild(fb); }
            } else if (!room.isHost) {
                var entry = ds && ds.onEntry ? (ds.allow ? function () { try { ds.onEntry(); } catch (_) {} } : null)
                    : (CFG.addMe ? function () { try { CFG.addMe(room); } catch (_) {} } : null);
                if (entry) { var eb = B('', '✋', entry, t('addMe')); eb.setAttribute('data-k', 'entry'); w.appendChild(eb); }
            }
            w.appendChild(B('pri', '💬', function () { openInvite(room); }, t('invite')));
        }
        render();
        if (host) host.insertBefore(w, host.firstChild); else D.body.appendChild(w);
        var hdl = { el: w, room: room, refresh: render, remove: function () { w.remove(); if (H.strip === hdl) H.strip = null; } };
        H.strip = hdl;
        return hdl;
    }

    /* ── 추첨 게임 띠 (P3a 계약 — strip() 위에 추첨 버튼) ─────────────── */
    var DS = null;
    function drawStrip(o) {
        o = o || {};
        var room = o.room && !o.room._left ? o.room : null;
        if (!room) {
            DS = null;
            if (H.strip && (!cur || cur._left)) H.strip.remove(); else if (H.strip) H.strip.refresh();
            return null;
        }
        DS = { room: room, gameId: o.gameId || room.gameId, allow: o.allow !== false,
            onEntry: typeof o.onEntry === 'function' ? o.onEntry : null, onAllow: typeof o.onAllow === 'function' ? o.onAllow : null,
            onFill: typeof o.onFill === 'function' ? o.onFill : null };
        if (!cur || cur._left) bind(room);                  /* 게임이 직접 붙인 방도 공통 UI 가 맡는다 */
        if (cur !== room) return null;
        if (!H.strip || H.strip.room !== room || !H.strip.el.isConnected) strip(room);
        else H.strip.refresh();
        return H.strip;
    }

    /* ── 초대 시트 ─────────────────────────────────────────────── */
    function loadQr() {
        if (G.qrcode) return Promise.resolve(G.qrcode);
        return new Promise(function (res) {
            var s = D.createElement('script'); s.src = '/vendor/qrcode.js'; s.onload = function () { res(G.qrcode || null); }; s.onerror = function () { res(null); };
            D.head.appendChild(s);
        });
    }
    function openInvite(room, o) {
        room = room || cur; if (!room) return;
        o = o || {};
        var url = room.inviteUrl(), body = E('div', 'lpr-col');
        var big = E('div', 'lpr-bigcode', fmtCode(room.code)); body.appendChild(big);
        var seal = E('div', 'lpr-mut', room.seal || ''); seal.style.textAlign = 'center'; seal.style.fontSize = '18px'; body.appendChild(seal);
        var share = B('pri wide', '💬 ' + t('inviteMsg'), function () {
            var txt = t('shareTxt', { g: gname(room.gameId), c: fmtCode(room.code) });
            if (navigator.share) { navigator.share({ title: 'Lucky Please', text: txt, url: url }).catch(function (e) { if (!e || e.name !== 'AbortError') copyText(txt + '\n' + url).then(function () { toast(t('copied')); }); }); }
            else copyText(txt + '\n' + url).then(function (ok) { toast(ok ? t('copied') : url); });
        });
        share.setAttribute('data-focus', '');
        body.appendChild(share);
        var lr = E('div', 'lpr-link'), li = E('input', 'lpr-in'); li.readOnly = true; li.value = url; li.setAttribute('aria-label', 'link');
        li.addEventListener('focus', function () { li.select(); });
        lr.appendChild(li); lr.appendChild(B('', t('copy'), function () { copyText(li.value).then(function (ok) { toast(ok ? t('copied') : li.value); }); }));
        body.appendChild(lr);
        var qr = E('div', 'lpr-qr'); body.appendChild(qr);
        function paintQr(u) {
            qr.innerHTML = '';
            loadQr().then(function (q) {
                if (!q) return;
                try { var c = q(0, 'M'); c.addData(u); c.make(); qr.innerHTML = c.createSvgTag({ cellSize: 3, margin: 2, scalable: true }); var sv = qr.querySelector('svg'); if (sv) sv.setAttribute('aria-label', 'QR'); } catch (_) {}
            });
        }
        paintQr(url);
        if (room.isHost && room.pin && room.state().pinReq) {
            var pr = E('div', 'lpr-mut', '🔑 ' + t('pinOnly', { p: room.pin }) + ' · ' + t('inviteOnlyHint')); pr.style.textAlign = 'center'; body.appendChild(pr);
        }
        if (room.isHost) {
            var rr = E('div', 'lpr-row');
            rr.appendChild(B('ghost', '🔄 ' + t('newLink'), function () { url = room.rotateLink() || room.inviteUrl(); li.value = url; paintQr(url); toast(t('linkNew')); }));
            body.appendChild(rr);
        }
        var s = sheet({ title: '💬 ' + t('invite'), body: body });
        if (o.qr) setTimeout(function () { try { qr.scrollIntoView({ block: 'center' }); } catch (_) {} }, 60);
        return s;
    }

    /* ── 방 시트(HUD 탭) ───────────────────────────────────────── */
    /* 방장 도구 — 코어 공개 API(room.setPin · room.setApproval, 2026-09-30 추가)만 쓴다 */
    function setPin(room, on) { if (typeof room.setPin === 'function') room.setPin(on); }
    function setAppr(room, on) { if (typeof room.setApproval === 'function') room.setApproval(on); else room.approval(on); }
    function openRoom(room) {
        room = room || cur; if (!room) return;
        var body = E('div', 'lpr-col'), s;
        function render() {
            var S = room.state(); if (!S) return;
            body.innerHTML = '';
            s && (s.title.textContent = fmtCode(room.code) + '  ' + (room.seal || ''));
            body.appendChild(rosterEl(room));
            var r1 = E('div', 'lpr-row');
            r1.appendChild(B('pri', '💬 ' + t('invite'), function () { openInvite(room); }));
            body.appendChild(r1);
            if (room.isHost) {
                var g = E('div', 'lpr-row'); g.style.flexWrap = 'wrap';
                function tg(icon, key, onv, fn) { var b = B(onv ? 'on' : '', icon + ' ' + t(key), function () { fn(!onv); setTimeout(render, 30); }); b.setAttribute('aria-pressed', onv ? 'true' : 'false'); b.style.flex = '1 1 30%'; return b; }
                g.appendChild(tg('🔒', 'lock', !!S.lock, function (v) { room.lock(v); }));
                g.appendChild(tg('✋', 'appr', !!S.appr, function (v) { setAppr(room, v); }));
                g.appendChild(tg('🔑', 'pin', !!S.pinReq, function (v) { setPin(room, v); if (v && room.pin) toast(t('pinOnly', { p: room.pin }), 2600); }));
                body.appendChild(g);
                var g2 = E('div', 'lpr-row'); g2.style.flexWrap = 'wrap';
                if (S.phase === 'playing') g2.appendChild(B('', '⏸ ' + t('pause'), function () { room.pause(); s.close(); }));
                if (S.phase === 'paused') g2.appendChild(B('', '▶ ' + t('resume'), function () { room.resume(); s.close(); }));
                if (S.phase !== 'lobby') g2.appendChild(B('', '⏹ ' + t('toLobby'), function () { room.toLobby(); s.close(); }));
                if (gameList(true).length) g2.appendChild(B('', '🎮 ' + t('switchG'), function () { s.close(); openSwitch(room); }));
                [].forEach.call(g2.children, function (b) { b.style.flex = '1 1 40%'; });
                if (g2.children.length) body.appendChild(g2);
                body.appendChild(B('danger wide', '✕ ' + t('closeRoom'), function () { confirmBox(t('closeQ'), { danger: true, ok: t('closeRoom') }).then(function (ok) { if (ok) { s.close(); room.close(); } }); }));
            } else {
                var me = room.roster().filter(function (m) { return m.p === room.me.pid; })[0] || {};
                var r2 = E('div', 'lpr-row');
                if (me.r === 'spec') r2.appendChild(B('', '🙋 ' + t('play'), function () { room.intent('role', 'play'); s.close(); }));
                else r2.appendChild(B('', '👀 ' + t('watch'), function () { room.intent('role', 'watch'); s.close(); }));
                r2.appendChild(B('danger', '🚪 ' + t('leave'), function () { confirmBox(t('leaveQ'), { danger: true, ok: t('leave') }).then(function (ok) { if (ok) { s.close(); room.leave(); } }); }));
                body.appendChild(r2);
            }
        }
        s = sheet({ title: fmtCode(room.code), body: body, onClose: function () { off1(); off2(); } });
        var off1 = room.on('roster', function () { render(); }), off2 = room.on('pending', function () { render(); });
        render();
        return s;
    }

    /* ── 배지(공정 추첨) + 검증 시트 ───────────────────────────────── */
    function decorateBadge(el, info) {
        if (!el) return;
        info = info || {};
        var k = info.kind || 'solo';
        el.textContent = k === 'verified' ? t('fairN', { n: info.n || 0 }) : k === 'seed' ? t('fairSeed') : k === 'mismatch' ? t('mismatch', { n: info.n || 0 }) : t('solo');
        if (!el.classList.contains('lpf-badge')) el.classList.add('lpf-badge', 'lpf-' + k);
        el.tabIndex = 0;
        if (!el._lprTap) {
            el._lprTap = true;
            var fn = function (e) { if (e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ') return; e.preventDefault(); e.stopPropagation(); verifySheet(el._lpfCert, el.getAttribute('data-kind')); };
            el.addEventListener('click', fn); el.addEventListener('keydown', fn);
            shield(el);
        }
    }
    function badge(el, info) {
        injectCss();
        if (G.LpFair && G.LpFair.badge && G.LpFair.badge._lprOrig) G.LpFair.badge._lprOrig(el, info);
        else if (G.LpFair && G.LpFair.badge) G.LpFair.badge(el, info);
        decorateBadge(el, info);
    }
    function hookFair() {
        var F = G.LpFair;
        if (!F || !F.badge || F.badge._lprOrig) return;
        var orig = F.badge;
        var wrapped = function (el, info) { orig(el, info); try { injectCss(); decorateBadge(el, info); } catch (_) {} };
        wrapped._lprOrig = orig;
        F.badge = wrapped;
    }
    function verifySheet(cert, kind) {
        var body = E('div', 'lpr-col');
        if (cert) {
            var names = {};
            if (cur) cur.roster().forEach(function (m) { names[m.p] = avOf(m.av) + ' ' + m.n; });
            var l = E('div', 'lpr-list');
            (cert.L || []).forEach(function (p) { var r = E('div', 'lpr-m'); r.appendChild(E('span', 'lpr-st', '✓')); r.firstChild.style.color = '#4CD964'; r.appendChild(E('span', 'lpr-mn', names[p] || p.slice(0, 7))); l.appendChild(r); });
            body.appendChild(l);
            var info = E('div', 'lpr-mut', '#' + cert.round + ' · seed ' + String(cert.hs || cert.C || '').slice(0, 8) + (cert.stats ? ' · ' + cert.stats.draws + '/' + (cert.stats.aborts || 0) : ''));
            info.style.textAlign = 'center'; info.style.fontFamily = 'ui-monospace,monospace'; body.appendChild(info);
            if (typeof CFG.replay === 'function') body.appendChild(B('wide', '↻ ' + t('replay'), function () { closeSheets(); try { CFG.replay(cert); } catch (_) {} }));
            if (G.LpFair && G.LpFair.cert) body.appendChild(B('pri wide', '🔗 ' + t('certCopy'), function () {
                G.LpFair.cert.encode(cert).then(function (s) { var u = location.origin + (G.LpGames && G.LpGames.path(cert.g) || location.pathname) + '#cert=' + s; return copyText(u); }).then(function (ok) { toast(ok ? t('copied') : '✗'); });
            }));
        } else body.appendChild(E('div', 'lpr-mut', kind === 'solo' ? t('solo') : t('fairT')));
        sheet({ title: '✓ ' + t('fairT'), body: body });
    }

    /* ── 방장 끊김 띠 · 일시정지 · 떠남 ───────────────────────────── */
    function band(level) {
        if (H.band) { H.band.remove(); H.band = null; }
        if (H.hud) H.hud.level(level || 0);
        if (!level) return;
        injectCss();
        var b = shield(E('div', 'lpr-root lpr-band' + (level >= 2 ? ' bad' : ''))); b.setAttribute('role', 'alert');
        b.appendChild(E('span', null, level === 1 ? '⏳ ' + t('hostCheck') : level === 2 ? '📡 ' + t('hostLost') : '⏳ ' + t('hostWait')));
        if (level >= 2) {
            b.appendChild(B('', t('waitBtn'), function () { b.remove(); H.band = null; }));
            b.appendChild(B('danger', t('leave'), function () { if (cur) cur.leave(); }));
        }
        D.body.appendChild(b); H.band = b;
    }
    function pauseOverlay(on) {
        if (H.pause) { H.pause.remove(); H.pause = null; }
        if (!on || !cur) return;
        var p = shield(E('div', 'lpr-root lpr-pause')); p.setAttribute('role', 'status');
        p.appendChild(E('div', null, '⏸ ' + t('paused')));
        if (cur.isHost) { var r = cur; p.appendChild(B('go', '▶ ' + t('resume'), function () { r.resume(); })); }
        D.body.appendChild(p); H.pause = p;
    }
    function teardownUI() {
        ['lobby', 'hud', 'strip'].forEach(function (k) { if (H[k]) H[k].remove(); });
        band(0); pauseOverlay(false);
        closeSheets();
        roomBtnState();
    }
    function unbind() { offs.forEach(function (f) { try { f(); } catch (_) {} }); offs = []; cur = null; }
    function leftCard(reason, ban) {
        var map = { kicked: ban ? 'banned' : 'kicked', host: 'closed', host_gone: 'hostGone', replaced: 'replaced' };
        var k = map[reason]; if (!k) return;
        card(reason === 'kicked' ? '🚪' : '👋', t(k), [B('', t('ok'), function () { if (H.card) H.card.remove(); H.card = null; }), B('pri', '🏠 ' + t('home'), goHome)]);
        say(t(k));
    }

    /* ── 방 붙이기 ─────────────────────────────────────────────── */
    function bindsHere(r) {
        var pg = pageGid(); if (!pg || !r) return false;
        return pg === 'lobby' ? r.gameId === 'lobby' : r.gameId === pg;
    }
    function layout(room) {
        if (CFG.lobby) return CFG.lobby;
        var gid = room.state() ? room.state().gameId : room.gameId;
        if (gid === 'lobby') return 'full';
        var ad = G.LpRooms.getAdapter && G.LpRooms.getAdapter();
        var kind = ad && ad.gameId === gid ? ad.kind : (reg(gid) && reg(gid).mp ? reg(gid).mp.kind : 'turn');
        return kind === 'draw' ? 'strip' : 'full';
    }
    var rafQ = 0;
    function refreshAll() {
        if (rafQ) return;
        rafQ = 1;
        var run = function () { if (!rafQ) return; rafQ = 0; ['lobby', 'hud', 'strip'].forEach(function (k) { if (H[k]) try { H[k].refresh(); } catch (e) { if (G.console) console.error(e); } }); };
        if (G.requestAnimationFrame) G.requestAnimationFrame(run);
        setTimeout(run, 80);
    }
    function onPhase(ph) {
        var room = cur; if (!room) return;
        var lay = layout(room);
        if (ph === 'lobby') {
            if (lay === 'full' && !H.lobby) mountLobby(room);
            if (lay === 'strip' && !H.strip) strip(room);
            blockSince = 0;
        } else {
            if (H.lobby) H.lobby.remove();
            if (H.strip && H.strip.el.classList.contains('fixed')) H.strip.remove();
            emit('play', ph);
        }
        pauseOverlay(ph === 'paused');
        if (CFG.hud !== false && !H.hud) mountHud(room);
        refreshAll();
    }
    function bind(room) {
        if (!room || cur === room) return;
        if (cur) { teardownUI(); unbind(); }
        cur = room; bindAt = Date.now(); lastNames = {}; lastTurnN = -1;
        injectCss();
        room.roster().forEach(function (m) { lastNames[m.p] = m.n; });
        offs.push(room.on('roster', function (ros, d) {
            if (d && Date.now() - bindAt > 600) {
                (d.join || []).forEach(function (p) { var m = ros.filter(function (x) { return x.p === p; })[0]; if (m && p !== room.me.pid) say(t('joinedN', { n: m.n })); });
                (d.left || []).forEach(function (p) { if (lastNames[p]) say(t('leftN', { n: lastNames[p] })); });
            }
            ros.forEach(function (m) { lastNames[m.p] = m.n; });
            if (room.isHost && room.state().phase === 'lobby') { if (!room.canStart()) { if (!blockSince) blockSince = Date.now(); } else blockSince = 0; }
            refreshAll();
        }));
        offs.push(room.on('state', function (S) {
            if (S && S.turn && room.me.seat != null && S.turn.seat === room.me.seat && S.turn.n !== lastTurnN) { lastTurnN = S.turn.n; say(t('myTurn')); }
            if (H.lobby && S && S.phase === 'lobby' && layout(room) !== 'full') { H.lobby.remove(); strip(room); }
            refreshAll();
        }));
        offs.push(room.on('phase', function (ph) { onPhase(ph); }));
        offs.push(room.on('pending', function (list) { if (list && list.length) { say(t('askIn', { n: list[list.length - 1].n })); } refreshAll(); }));
        offs.push(room.on('pinflood', function (x) { room._pinFlood = x && x.until; toast('⚠ ' + t('pinFlood')); refreshAll(); }));
        offs.push(room.on('react', function (i, from) { floatReact(i, from); }));
        offs.push(room.on('hostlost', function (x) { var l = x && x.level || 1; band(l); if (l >= 2) say(t('hostLost')); }));
        offs.push(room.on('hostback', function () { band(0); }));
        offs.push(room.on('takeover', function (x) {
            band(0);
            if (x && x.pid === room.me.pid) toast('👑 ' + t('meHost'), 2600);
            else { var m = room.roster().filter(function (y) { return y.p === (x && x.pid); })[0]; toast('👑 ' + t('takeover', { n: m ? m.n : '?' }), 2600); }
            refreshAll();
        }));
        offs.push(room.on('switch', function () { toast('🎮 ' + t('moving'), 1500); }));
        offs.push(room.on('kicked', function (x) { var r = room; teardownUI(); unbind(); leftCard('kicked', x && x.ban); emit('left', { reason: 'kicked', room: r }); }));
        offs.push(room.on('closed', function (x) { var r = room, why = x && x.reason; teardownUI(); unbind(); if (why !== 'left') leftCard(why); emit('left', { reason: why, room: r }); }));
        offs.push(room.on('detached', function () {
            if (cur !== room) return;
            var code = room.code;
            teardownUI(); unbind();
            card('🗂️', t('otherTab'), [B('', '🏠 ' + t('home'), goHome), B('pri', t('here'), function () { if (H.card) H.card.remove(); H.card = null; joinHere(code, { steal: true }); })]);
        }));
        roomBtnState();
        onPhase(room.state() ? room.state().phase : 'lobby');
        var anyShown = false;
        var iv = setInterval(function () {
            if (cur !== room) { clearInterval(iv); return; }
            if (D.visibilityState === 'hidden') return;
            if (H.hud) H.hud.refresh();
            /* 20초 넘게 시작이 막히면 [준비한 사람만 시작] 을 띄우려고 한 번 다시 그린다 */
            var late = !!(room.isHost && blockSince && Date.now() - blockSince > 20000);
            if (late !== anyShown) { anyShown = late; if (H.lobby) H.lobby.refresh(); }
        }, 700);
        offs.push(function () { clearInterval(iv); });
        emit('room', room);
    }

    /* ── 게임 도크의 👥 버튼 (LpChrome 가 .lp-rooms-btn 을 도크로 옮긴다) ── */
    var roomBtn = null;
    function roomBtnState() { if (roomBtn) { roomBtn.classList.toggle('in', !!cur); roomBtn.setAttribute('aria-label', cur ? fmtCode(cur.code) : t('rooms')); } }
    function ensureRoomBtn() {
        if (roomBtn || !/^\/games\//.test(location.pathname)) return;
        var e0 = reg(pageGid()); if (!e0 || !e0.mp) return;          /* 멀티 없는 게임엔 👥 없음 */
        roomBtn = E('button', 'lp-rooms-btn', '👥'); roomBtn.type = 'button'; roomBtn.title = t('rooms');
        roomBtn.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); if (cur) openRoom(cur); else entrySheet(); });
        roomBtnState();
        D.body.appendChild(roomBtn);
    }
    function entrySheet() {
        var gid = CFG.gameId || pageGid();
        return openCreate({ gameId: gid });
    }

    /* ── /lobby/ 허브 ─────────────────────────────────────────── */
    function hub(el) {
        injectCss();
        el.classList.add('lpr-root');
        el.innerHTML = '';
        var msg = E('div', 'lpr-msg'), extra = E('div', 'lpr-row');
        var ui = sheetUI(msg, null, extra);
        ui.choice = function (opts) { extra.innerHTML = ''; opts.forEach(function (op) { extra.appendChild(B('', op.label, function () { location.assign(op.url); })); }); };
        var h1 = E('h1', 'lpr-hubt', '👥 ' + t('rooms')); el.appendChild(h1);
        var ci = codeInput({ onFull: function (v, p, raw) { route(p ? raw : v, {}, ui); }, onEnter: function (v) { if (v.length >= 6) route(v, {}, ui); } });
        ci.input.removeAttribute('data-focus');
        el.appendChild(ci.el); el.appendChild(msg); el.appendChild(extra);
        var mk = B('go wide', '＋ ' + t('create'), function () { mk.style.display = 'none'; gw.style.display = ''; });
        el.appendChild(mk);
        var gw = E('div'); gw.style.display = 'none';
        gw.appendChild(gridEl({ withGather: true, onPick: function (id) { goCreate(id); } }));
        el.appendChild(gw);
        var rec = jparse(lsGet('lpr_recent'), []);
        if (Array.isArray(rec) && rec.length) {
            el.appendChild(E('div', 'lpr-mut lpr-rect', t('recent')));
            var list = E('div', 'lpr-list');
            rec.slice(0, 5).forEach(function (x) {
                if (!x || !x.code) return;
                var r = E('div', 'lpr-m tap'); r.tabIndex = 0; r.setAttribute('role', 'button');
                var dot = E('span', 'lpr-dot off'); dot.setAttribute('aria-label', t('off'));
                r.appendChild(iconEl(x.g)); r.appendChild(E('span', 'lpr-mn', gname(x.g) + (x.h ? ' · ' + x.h : '')));
                var c = E('span', 'lpr-code', fmtCode(x.code)); c.style.fontSize = '14px'; r.appendChild(c); r.appendChild(dot);
                var go = function () { route(x.code, {}, ui); };
                r.addEventListener('click', go); r.addEventListener('keydown', function (e) { if (e.key === 'Enter') go(); });
                list.appendChild(r);
                r._x = x; r._dot = dot;
            });
            el.appendChild(list);
            /* 살아있는지 점 — 보일 때 한 번, 2개씩 */
            var rows = [].slice.call(list.children), qi = 0;
            function next() {
                var r = rows[qi++]; if (!r) return;
                G.LpRooms.resolve(r._x.code).then(function (v) {
                    var alive = v && (v.kind === 'rooms' || v.kind === 'rooms-v1');
                    r._dot.className = 'lpr-dot' + (alive ? '' : ' off'); r._dot.setAttribute('aria-label', t(alive ? 'on' : 'off'));
                    r.setAttribute('data-alive', alive ? '1' : '0');
                }).catch(function () {}).then(next);
            }
            setTimeout(function () { next(); next(); }, 300);
        }
        return { el: el };
    }

    /* ── 부팅: URL 처리 → resume → 자동 참가 ─────────────────────────── */
    var bootP = null;
    function boot() {
        if (bootP) return bootP;
        bootP = (async function () {
            injectCss();
            hookFair();
            if (G.LpRooms && !G.LpRooms.UI) try { G.LpRooms.UI = G.LpRoomsUI; } catch (_) {}
            G.LpRooms.on('room', function (r) { if (bindsHere(r)) bind(r); });
            G.LpRooms.on('left', function (x) { if (cur && x && x.code === cur.code && cur._left) { var r = cur; teardownUI(); unbind(); emit('left', { reason: x.reason, room: r }); } });
            var pg = pageGid(), href0 = G.__lprHref || location.href;
            /* 초대 fragment → sessionStorage, 주소창에서 지움 (§2.3) */
            var p = null;
            try { if (/[#&]k=/.test(href0) || /\/r\//.test(href0) || /[?&]r=/.test(href0)) p = G.LpRooms.parseInvite(href0); } catch (_) {}
            if (p && p.inv) saveInv(p);
            if (/#.*\bk=/.test(location.href) && G.history && history.replaceState) { try { history.replaceState(history.state, '', location.pathname + location.search); } catch (_) {} }
            if (!pg) return null;                                   /* 홈 등: 버튼 동작만 */
            /* 게임 어댑터 대기열 — 게임 인라인 스크립트는 이 모듈보다 먼저 돈다:
               window.LpRoomsQ=(window.LpRoomsQ||[]); LpRoomsQ.push(function(LpRooms,UI){ LpRooms.adapter({...}); UI.config({...}); }) */
            var q0 = G.LpRoomsQ; G.LpRoomsQ = { push: function (fn) { try { fn(G.LpRooms, G.LpRoomsUI); } catch (e) { if (G.console) console.error(e); } } };
            if (q0 && q0.length) q0.forEach(function (fn) { G.LpRoomsQ.push(fn); });
            if (pg !== 'lobby') ensureRoomBtn();
            /* 허브 페이지 = '먼저 모이기' 방의 대기실. 다른 게임 방 코드면 방장이 wrong_game 으로 알려 주고 그 게임으로 간다 */
            if (pg === 'lobby' && !(G.LpRooms.getAdapter && G.LpRooms.getAdapter())) G.LpRooms.adapter({ gameId: 'lobby', kind: 'lobby', seats: null });
            if (CFG.auto === false) return null;
            if (/^\/r\//.test(location.pathname)) return null;      /* /r/CODE — 허브 페이지가 route() */
            /* 자동 참가·resume 은 한 곳만 — 게임 어댑터가 먼저 맡았으면(__lprBoot) 건너뛰고, 아니면 UI 가 맡았다고 표시 */
            if (G.__lprBoot && G.__lprBoot !== 'ui') return null;
            G.__lprBoot = 'ui';
            var room = null, act = jparse(ssGet('lpr_active'), null);
            /* 허브에서는 '먼저 모이기' 방만 이어받는다 — 다른 게임 방은 HUD·최근 방으로 돌아간다 */
            var skipResume = pg === 'lobby' && act && act.gameId && act.gameId !== 'lobby' && !/[?&]r=/.test(location.search);
            if (!skipResume) { try { room = await G.LpRooms.resume(); } catch (_) {} }
            if (room) { bind(room); return room; }
            var q = null; try { q = new URLSearchParams(location.search); } catch (_) {}
            var code = q && G.LpRooms.util.normCode(q.get('r') || '');
            if (q && q.get('lpr') === 'new') {
                try { q.delete('lpr'); history.replaceState(history.state, '', location.pathname + (q.toString() ? '?' + q : '')); } catch (_) {}
                if (!code) { setTimeout(function () { openCreate({ gameId: CFG.gameId || pg }); }, 0); return null; }
            }
            if (code) {
                if (G.LpRooms.profile.get().nick) return joinHere(code, {});
                return new Promise(function (res) {
                    var body = E('div', 'lpr-col'), prof = profEditor(), msg = E('div', 'lpr-msg'), extra = E('div', 'lpr-row');
                    var big = E('div', 'lpr-bigcode', fmtCode(code)); body.appendChild(big);
                    body.appendChild(prof.el);
                    var go = B('go wide', t('join'), function () { prof.save(); joinHere(code, {}, ui).then(function (r) { if (r) { s.close(); res(r); } }); });
                    prof.input.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); go.click(); } });
                    body.appendChild(go); body.appendChild(msg); body.appendChild(extra);
                    var ui = sheetUI(msg, go, extra);
                    var s = sheet({ title: gname(pg === 'lobby' ? 'lobby' : pg), icon: iconEl(pg), body: body, dismiss: false, onClose: function () { res(cur); } });
                    prof.input.setAttribute('data-focus', '');
                });
            }
            return null;
        })().catch(function (e) { if (G.console) console.warn('[LpRoomsUI] boot', e); return null; });
        return bootP;
    }

    /* 언어 전환 → 다시 그리기 */
    D.addEventListener('lp:langchanged', function () { refreshAll(); roomBtnState(); });
    G.addEventListener('lp-chrome-change', function () { if (H.hud) H.hud.refresh(); });

    G.LpRoomsUI = {
        version: VER,
        config: function (o) {
            o = o || {}; for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) CFG[k] = o[k];
            if (!cur) return;
            var ph = cur.state() && cur.state().phase;
            if (H.strip && (layout(cur) !== 'strip' || (o.stripEl && H.strip.el.classList.contains('fixed')))) H.strip.remove();
            if (ph === 'lobby') { if (H.lobby && layout(cur) !== 'full') H.lobby.remove(); onPhase(ph); }
        },
        ready: function () { return boot(); },
        room: function () { return cur; },
        on: on,
        openCreate: openCreate, openJoin: openJoin, openInvite: openInvite, openRoom: openRoom, openSwitch: openSwitch,
        mountLobby: mountLobby, mountHud: mountHud, strip: strip, drawStrip: drawStrip, badge: badge,
        confirm: confirmBox, sheet: sheet, toast: toast, say: say, t: t, lang: lang, avatars: AV.slice(),
        hub: hub,
        route: function (input, el) {
            injectCss();
            var m = E('div', 'lpr-msg'), ex = E('div', 'lpr-row');
            if (el) { el.appendChild(m); el.appendChild(ex); }
            var ui = sheetUI(m, null, ex);
            ui.choice = function (opts) { ex.innerHTML = ''; opts.forEach(function (op) { ex.appendChild(B('', op.label, function () { location.assign(op.url); })); }); };
            return route(input, { here: !/^\/r\//.test(location.pathname) }, ui);
        },
        _bind: bind
    };
    if (G.LpRooms) try { G.LpRooms.UI = G.LpRoomsUI; } catch (_) {}

    function start() { if (G.LpRooms) boot(); }
    if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', start); else start();
})(typeof window !== 'undefined' ? window : globalThis);
/* CHANGE LOG
   2026-09-30  P2 — 참가·대기실·HUD·초대·전환·허브·배지.
   2026-09-30  통합 수정(P3a 추첨 게임 계약, 하위 호환 추가만):
               [+] drawStrip({room, gameId, allow, onEntry, onAllow, onFill}) — strip() 위 추첨 버튼(방장 ✋허용·👥채우기, 게스트 ✋내 이름).
               [+] openJoin({code, gameId, inv, sheet}) — 온전한 코드 + 저장된 닉이면 시트 없이 바로 참가, inv 는 lpr_inv 로.
               [+] window.__lprBoot — UI 가 자동 참가·resume 을 맡으면 'ui', 게임이 먼저 맡았으면 UI 는 건너뜀(이중 참가 방지).
               방장 도구 PIN·승인은 코어 공개 API(room.setPin · room.setApproval)만 쓴다(room._H 직접 접근 제거).
*/
