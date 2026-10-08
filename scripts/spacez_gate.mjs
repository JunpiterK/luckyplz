#!/usr/bin/env node
/* =====================================================================
   Space-Z 회귀 게이트 (P0, 2026-09-27)
   public/games/dodge/index.html 을 여러 에이전트가 동시에 고쳐도
   결정성·성능·레이아웃·상표·다국어·에러 회귀를 자동으로 잡는다.

   사용:
     node scripts/spacez_gate.mjs [명령...] --root <체크아웃 경로> --port <n> [옵션]

   명령 (생략 시 기본 = all):
     all     det perf layout tm i18n fx0 beamdrain hitpath noshake  (기본 게이트 묶음 — MP0 에서 hitpath·noshake 추가)
     full    all + sweep + bot + soak + assets
     merge   all + restart audioctx latency boot flags0 startshot  (웨이브 병합 묶음 — ibot 1000 은 따로)
     det     합성 시계 결정성 — 16.67/21/33.33/8.33ms × 솔로/레이스 × 미션 성공/실패 × 폭탄. 구성마다 rand·randH·randD 호출 수(nR·nH·nD) 기준선 비교
     perf    프레임 JS 시간 p50/p95/p99 — CPU 1x·4x, 고정 존 구간(구간마다 Edge 새로 띄움)
     sweep   perf 와 같지만 전 존(1~30) 순회
     layout  320x568 360x640 375x667 375x812 412x915 740x360 768x1024 1280x800
             가로 스크롤·잘림·겹침·버튼 44px·캔버스 글자 9px + 스크린샷
     tm      상표 검사 — 소스 문자열 리터럴(주석 제외) + 6개 언어 실제 화면(DOM·캔버스 fillText)
     i18n    *I18N* 표 ko/en/ja/zh/es/pt 키 누락 + 비한국어 화면의 한글 잔존
     fx0     ?fx=0 (SZ_FLAGS.fx=false) 로 31존 순회 — 에러 0
     bot     자동 조종봇 몬테카를로 — 같은 시드 N판, 30/60fps, 184·343·475초 도달률
     ibot    아이템 봇 — bot 회피 + 보급 BEAM 줍기·아이템 사용·위성 미션 확률(--mis-p, 기본 0.8). 60~540초 도달률·10초당 피격률·아이템 통계
     soak    합성 시계 1260초 무작위 입력 — 에러 0·힙 톱니
     assets  첫 로드·존 순회 전송량
     beamdrain  BEAM 게이지 소진 회귀(탭·꾹·PC F 키 — 4초 방치 뒤 시계가 계속 가는가) + SAT R 키 설치
                (존 1 궤도에서 R 꾹 → 설치, BEAM 게이지·상태 불변, 설치 중 보급 획득이 진행률을 깎지 않음)
     ── MP0 (2026-10-08, 명작화 기반) ──
     hitpath    무적을 끈 충돌 경로 — 자연 운석(기체 고정)·주입 운석(고정 궤적, 직격·스침 교대) × 16.67/33.33ms.
                {피격·목숨·콤보·게임오버 논리 시각·순서} 해시를 기준선과 비교 + Math.random 시드를 바꿔도 같은지(논리 독립)
     noshake    ① #canvasWrap·조상 CSS transform 항등 ② 캔버스 전체 fillRect 시점 변환 항등(평행이동·회전 0)
                ③ 프레임 간 평균 휘도 증가 ≤ 0.12×255 (폭탄·플라즈마 폭풍·피버·피격을 일부러 건다)
     restart    사망 → 결과 카드 '다시하기' 탭 가능 → 다음 판 조종 가능까지 실제 시간 ms (가짜 시계 없음). p50·p90
     audioctx   페이지 전체(공용 lpAudio.js 포함) AudioContext 생성 수 — 생성 위치(스택) 포함
     latency    입력 지연 — 마우스(PC)·터치(폰 플로팅) 이벤트 → 기체가 새 위치로 그려진 프레임까지 ms·프레임 수
     boot       첫 로드 — CPU 4x 스로틀, 탐색 시작 → #ovBtn 탭 가능까지 ms + 그 전 롱태스크 합
     flags0     ?mp1=0…&mp8=0 (킬스위치 전부 끔) 으로 det(16.67ms 구성)·hitpath 해시가 기준선과 같은지
     startshot  시작 화면 ko·en × 320x568·390x844 — 스크린샷(보통 + 애니메이션 정지·캔버스 숨김) 해시·DOM 배치 서명 기준선 비교
     gl0        (자리) MP8b 가 채운다 — GL 끔 31존 순회·컨텍스트 손실
     ── 패키지 확장 명령 (각 gate:mpN 펜스가 등록, 여기 표에 1줄씩) ──
     mp1        MP1 시작 화면(ko·en·ja×320·390: 버튼 ≤5·출발 엄지 영역·시트 20회 멱등·?mp1=0=MP0 서명)·단계 개방 1~3판·시드 판·링크 진입 (--mp1-nopin: 하네스 3판 고정 끔)

   옵션:
     --root <path>         체크아웃 루트 (기본: 이 스크립트의 상위 폴더)
     --port <n>            게이트가 띄울 python server.py 포트 (기본 8090)
     --baseline <file>     기준선 (기본 <root>/scripts/spacez_baseline.json)
     --write-baseline      이번 측정값을 기준선에 기록 (실행한 명령 구역만 교체)
     --allow-det-change    기준선 대비 det 해시 변화를 FAIL 대신 WARN (P2 처럼 코스를 의도적으로 바꿀 때)
     --out <dir>           스크린샷·결과 JSON 저장 폴더 (기본 OS temp/spacez_gate/<시각>)
     --prof-dir <dir>      Edge 프로필 상위 폴더 (기본 OS temp)
     --prof-prefix <s>     Edge 프로필 폴더 접두어 (기본 edgeprof_gate)
     --jobs <n>            det/layout/bot 병렬 Edge 수 (기본 3). perf/sweep 은 항상 직렬
     --layout-ctl <m>      layout 의 조작 방식 고정: float | classic (기본 = 페이지 기본값, 세로 터치 폰·태블릿은 float)
     --secs <n>            det 합성 시간(초, 기본 460)
     --quick               det 180초·perf 존 5개·layout 4해상도·bot 100판 (빠른 확인용, 기준선 비교는 같은 조건끼리만)
     --zones 1,2,4         perf 존 목록 덮어쓰기
     --bot-runs <n>        bot 판 수 (fps 당, 기본 1000 — 약 3분)
     --course-seeds <n>    bot 코스 시드 수 (기본 1 = 424242 한 코스). n>1 이면 판마다 n 개 코스를 돌려 쓴다 —
                           코스(수열)를 의도적으로 바꾼 변경(P2)은 한 코스 도달률이 우연히 크게 변하므로 여러 코스 분포로 비교
     --soak-secs <n>       soak 합성 시간 (기본 1260)
     --mis-p <p>           ibot 위성 미션 성공 확률 (기본 0.8)
     --ibot-secs <n>       ibot 한 판 최대 합성 시간 (기본 560)
     --mis-p-warn <p>      ibot 경고(위성 1번 놓침)가 뜬 뒤의 미션 성공 확률 — 경고를 본 사람이 다음 미션에 집중하는 모델 (기본 = --mis-p)
     --no-cut              ibot 에서 보급 영구 차단 규칙만 끈다 (규칙의 영향 비교용)
     --no-tank             ibot 이 궤도 급유 탱커를 하나도 안 먹는다(나오자마자 치움) — 추진제 고갈까지 걸리는 시간 확인용 (2026-10-08)
     --ibot-sets <n>       ibot 시드 묶음 수 (기본 1). 2 면 서로 다른 시드·코스 묶음 2개를 돌려 실행 간 중앙값 차이(runDiff)를 기록 —
                           병합 판정 허용폭 N = max(8초, runDiff×2) 의 근거 (MP0)
     --seed-set <k>        ibot/bot 시드 묶음 번호 (기본 0). k 번 묶음 = 봇 시드 1000+k×판수…, 코스 번호도 k×판수 만큼 민다
     --boot-runs <n>       boot 반복 수 (기본 3, 중앙값)
     --restart-runs <n>    restart 반복 수 (기본 6)
     --edge <exe>          msedge.exe 경로
     --json <file>         결과 전체를 JSON 으로 저장
     --verbose             진행 로그

   종료 코드: FAIL 이 하나라도 있으면 1, 아니면 0.
   종료 시 항상: 자기가 띄운 Edge(프로세스 트리)·서버 종료, 프로필 폴더 삭제, 잔존 확인.
   ===================================================================== */
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import vm from 'node:vm';
import crypto from 'node:crypto';

/* ---------------- 인자 ---------------- */
const argv = process.argv.slice(2);
const A = { _: [] };
for(let i = 0; i < argv.length; i++){
    const a = argv[i];
    if(a.startsWith('--')){
        const k = a.slice(2);
        const nx = argv[i + 1];
        if(nx === undefined || nx.startsWith('--')) A[k] = true; else { A[k] = nx; i++; }
    } else A._.push(a);
}
if(A.help || A.h){ console.log(fs.readFileSync(new URL(import.meta.url), 'utf8').split('\n').slice(1, 50).join('\n')); process.exit(0); }
const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const ROOT = path.resolve(A.root || path.join(HERE, '..'));
const PORT = +(A.port || 8090);
const BASE_FILE = path.resolve(A.baseline || path.join(ROOT, 'scripts', 'spacez_baseline.json'));
const STAMP = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const OUT = path.resolve(A.out || path.join(os.tmpdir(), 'spacez_gate', STAMP));
const PROF_DIR = path.resolve(A['prof-dir'] || os.tmpdir());
const PROF_PREFIX = String(A['prof-prefix'] || 'edgeprof_gate');
const JOBS = Math.max(1, +(A.jobs || 3));
const QUICK = !!A.quick;
const DET_SECS = +(A.secs || (QUICK ? 180 : 460));
const BOT_RUNS = +(A['bot-runs'] || (QUICK ? 100 : 1000));
const COURSE_SEEDS = Math.max(1, +(A['course-seeds'] || 1));
const SOAK_SECS = +(A['soak-secs'] || 1260);
const VERBOSE = !!A.verbose;
const GAME_FILE = path.join(ROOT, 'public', 'games', 'dodge', 'index.html');
const LANGS6 = ['ko', 'en', 'ja', 'zh', 'es', 'pt'];
const EDGE = A.edge || ['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Microsoft/Edge/Application/msedge.exe'].find(p => fs.existsSync(p));
/* 상표 — 대소문자 구분. 내부 식별자(_drawStarshipAt)·주석은 검사 대상이 아니다 */
const BRAND_RE = /SPACEX|SpaceX|Space X|STARSHIP|Starship|STAR FOX|Star Fox|StarFox|TETRIS|Tetris|Tetrimino|TETRIMINO|BREAKOUT|Breakout|Arkanoid|Mechazilla|Falcon 9|\bUFC\b/;
const HANGUL_RE = /[\uAC00-\uD7A3]/;

/* ---------------- 패키지 확장 등록부 (MP0, 2026-10-08) ----------------
   명작화 패키지(mp1~mp8)는 아래 자기 펜스 gate:mpN (열고 닫는 주석 표식) 안에서만 게이트를 늘린다.
     EXT_CMDS.<명령> = { run: async (base) => 결과, judge: (cur, base) => { row(...) }, all: true|false, server: true|false }
       → 결과는 CUR[<명령>] 에 저장되고 --write-baseline 이면 기준선 같은 이름 구역에 기록된다. all:true 면 'all' 묶음에 들어간다
     PAGE_EXT.push(function(){ const G = window.__G; G.내도구 = function(P){ ... }; })   → 페이지 쪽 도구(__G) 추가
     IBOT_HOOKS.push((P) => P)   → ibot 페이로드 P 를 고친다(예: --assist 면 P.ext.assist = 1). 페이지 쪽은 G.ibotPre(P, bi)/G.ibotPost(P, bi, rec)
     HIT_SCEN.push({ key, mode, step, ... })   → hitpath 시나리오 추가(예: MP3 데스봄 유예 누름·안 누름)
   명령 표(파일 머리)에는 1줄만 추가한다. 펜스 밖의 기존 코드는 고치지 않는다 */
const EXT_CMDS = {};
const PAGE_EXT = [];
const IBOT_HOOKS = [];
const HIT_SCEN = [];
/*<gate:mp1>*/
/* MP1 (2026-10-08) — 첫 30초·시작 화면·단계 개방(운영자 A6).
   ① 하네스 고정: 모든 게이트 페이지에서 SZMP1.pin(3). 단계는 '판 시작(startGame → runStart)' 때만 정해지므로 det·ibot·hitpath(G.begin 경로)는
      원래 영향이 없고, startGame 을 부르는 layout·restart·latency·noshake 도 숙련자(3판 이상) 화면·규칙으로 돈다(기준선과 같은 조건).
      1·2판은 아래 mp1 명령이 고정을 풀고 따로 본다. --mp1-nopin 이면 고정하지 않는다(새 프로필 = 1판).
   ② mp1 명령 —
      시작 화면 ko·en·ja × 320x568·390x844: 처음 보이는 버튼 ≤5(칩 줄 제외)·출발 버튼이 스크롤 없이 화면 안·엄지 영역(중심 ≥ 화면 1/3)·버튼 글자 잘림 0,
        시트 열고 닫기 20회 + 옵저버 자극 → 슬롯 버튼 수 불변·중복 id 0, 스크린샷(시작·함께 날기·설정)
      ?mp1=0 시작 화면 DOM 서명 = startshot 기준선(킬스위치 끔 = MP0 화면)
      단계 개방: 새 기기 1판(BEAM·아이템 칸 숨김, 보급·연료·차단 잠김, 존 0 미션 대기만, 첫 활성 미션 ≥25초, 10초 스침 링 스크린샷) → 2판(BEAM·보급 열림, 힌트) → 3판(연료 소모)
        · 오늘의 코스(시드 판) = 3단계 · 기존 사용자(szx_log.runs>0) 이전 = 3단계 · det 시작 경로(G.begin)의 단계·첫 판 판정
      링크 진입 ?ch= · ?race= — mp1 켬/끔에서 같은 흐름(시작 카드 숨김 여부·도전장 띠·열린 패널) */
if(!A['mp1-nopin']) PAGE_EXT.push(function(){ try{ if(window.SZMP1 && window.SZMP1.pin) window.SZMP1.pin(3); }catch(_){} });
const MP1_LANGS = ['ko', 'en', 'ja'];
const MP1_SIZES = [[320, 568, 2], [390, 844, 3]];
const MP1_SCREEN = `(function(){
    var ov = document.getElementById('overlay'), vw = innerWidth, vh = innerHeight;
    function vis(el){ if(!el || !el.getClientRects().length) return false; for(var p = el; p && p !== document.documentElement; p = p.parentElement){ var c = getComputedStyle(p); if(c.display === 'none' || c.visibility === 'hidden' || +c.opacity < 0.05) return false; } var r = el.getBoundingClientRect(); return r.width > 1 && r.height > 1; }
    var btns = [].slice.call(ov.querySelectorAll('button')).filter(vis);
    var main = btns.filter(function(b){ return !b.closest('#szm1Chips') && !b.closest('.szx-ch'); });
    var chips = btns.filter(function(b){ return !!b.closest('#szm1Chips'); });
    var name = function(b){ return b.id || (b.textContent || '').trim().slice(0, 14); };
    var ob = document.getElementById('ovBtn').getBoundingClientRect(), orc = ov.getBoundingClientRect();
    var clip = btns.filter(function(b){ return b.scrollWidth > b.clientWidth + 1; }).map(name);
    var inView = ob.top >= Math.max(0, orc.top) - 1 && ob.bottom <= Math.min(vh, orc.bottom) + 1 && ob.left >= -1 && ob.right <= vw + 1;
    return { vw: vw, vh: vh, n: main.length, ids: main.map(name), chips: chips.map(name), ovBtn: [Math.round(ob.left), Math.round(ob.top), Math.round(ob.width), Math.round(ob.height)],
        cy: Math.round(100 * (ob.top + ob.height / 2) / vh), inView: inView, scroll: ov.scrollHeight - ov.clientHeight, clip: clip, applied: ov.classList.contains('szm1'), E: (window.__E || []).slice(0, 5) };
})()`;
const MP1_CYCLE = `(async function(){
    var sl = function(ms){ return new Promise(function(r){ setTimeout(r, ms); }); };
    var ov = document.getElementById('overlay');
    var q = function(s){ return document.querySelectorAll(s).length; };
    var cnt = function(){ var ids = {}, dup = 0; ov.querySelectorAll('[id]').forEach(function(x){ if(ids[x.id]) dup++; ids[x.id] = 1; });
        return [q('#szm1TogBody button'), q('#szm1SetBody button'), q('#szm1Chips button'), q('#overlay button'), q('#overlay .sz-opts'), q('#overlay .szf-opts'), q('#szxMp'), q('#szxDuo'), dup].join(','); };
    var poke = function(){ var d = document.createElement('i'); ov.appendChild(d); ov.removeChild(d); };
    var c0 = cnt(), seen = {}; seen[c0] = 1;
    for(var i = 0; i < 20; i++){
        SZMP1.open(i % 2 ? 'set' : 'tog'); poke(); await sl(25);
        seen[cnt()] = 1;
        SZMP1.close(); poke(); await sl(25);
        seen[cnt()] = 1;
    }
    var tb = document.getElementById('szm1TogBody'), sb = document.getElementById('szm1SetBody');
    return { c0: c0, states: Object.keys(seen), tog: tb ? [].map.call(tb.querySelectorAll('button'), function(b){ return b.id || b.textContent.trim().slice(0, 12); }) : null,
        set: sb ? { hand: !!sb.querySelector('#handToggle'), opts: !!sb.querySelector('.sz-opts'), szf: !!sb.querySelector('#szfOpts'), n: sb.querySelectorAll('button').length } : null };
})()`;
async function mp1Start(base){
    const out = {};
    const jobs = [];
    for(const L of MP1_LANGS) for(const s of MP1_SIZES) jobs.push({ L, w: s[0], h: s[1], dsf: s[2] });
    const res = await pool(jobs, 1, async (j) => withEdge({ w: j.w, h: j.h, dsf: j.dsf, mobile: true }, async (e) => {
        const key = j.L + '_' + j.w + 'x' + j.h, fn = (st) => path.join(OUT, 'mp1', key + '_' + st + '.png');
        await e.open(gameUrl(base, j.L), 2600);
        const scr = await e.ev(MP1_SCREEN);
        await e.shot(fn('start'));
        await e.ev('SZMP1.open("tog"); 1'); await sleep(450); await e.shot(fn('together'));
        const togScr = await e.ev('(function(){ var c = document.querySelector("#szm1Tog .szm1-card").getBoundingClientRect(); return [Math.round(c.top), Math.round(c.bottom), innerHeight]; })()');
        await e.ev('SZMP1.close(); SZMP1.open("set"); 1'); await sleep(450); await e.shot(fn('settings'));
        const setScr = await e.ev('(function(){ var c = document.querySelector("#szm1Set .szm1-card"); var r = c.getBoundingClientRect(); return [Math.round(r.top), Math.round(r.bottom), innerHeight, c.scrollHeight - c.clientHeight]; })()');
        await e.ev('SZMP1.close(); 1');
        const cyc = await e.ev(MP1_CYCLE, 60000);
        const pe = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs('mp1 ' + key, e, pe);
        return { key, scr, cyc, togScr, setScr };
    }));
    for(const r of res) out[r.key] = r;
    return out;
}
/* ?mp1=0 — startshot 와 같은 절차(고정 pid·정지 스타일)로 DOM 서명 */
async function mp1Off(base){
    const out = {};
    const jobs = [];
    for(const L of ['ko', 'en']) for(const s of STARTSHOT_SIZES) jobs.push({ L, w: s[0], h: s[1], dsf: s[2] });
    const res = await pool(jobs, 1, async (j) => withEdge({ w: j.w, h: j.h, dsf: j.dsf, mobile: true }, async (e) => {
        const key = j.L + '_' + j.w + 'x' + j.h;
        await e.send('Page.addScriptToEvaluateOnNewDocument', { source: 'try{ if(!localStorage.getItem("szx_pid")) localStorage.setItem("szx_pid", "gatepid0001"); }catch(e){}' });
        await e.open(gameUrl(base, j.L, 'mp1=0'), 2600);
        await e.shot(path.join(OUT, 'mp1', 'off_' + key + '.png'));
        await e.ev(`(function(){ var s = document.createElement('style'); s.textContent = '*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important} #dodge-canvas{visibility:hidden!important}'; document.head.appendChild(s); return 1; })()`);
        await sleep(400);
        const sig = await e.ev(`(function(){ var ov = document.getElementById('overlay'); var o = [];
            ov.querySelectorAll('*').forEach(function(x){ if(!x.getClientRects().length) return; var r = x.getBoundingClientRect(); var c = getComputedStyle(x); if(c.display === 'none' || c.visibility === 'hidden') return;
                var t = ''; for(var n = x.firstChild; n; n = n.nextSibling) if(n.nodeType === 3) t += n.nodeValue.trim();
                o.push([x.tagName, String(x.className || ''), t.slice(0, 30), Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]); });
            return o; })()`);
        const pe = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs('mp1 off ' + key, e, pe);
        return { key, dom: sha(sig), nDom: sig.length, sig };
    }));
    for(const r of res) out[r.key] = r;
    return out;
}
const MP1_STATE = `(function(){
    var g = document.getElementById('gravBtn'), sr = document.querySelector('.control-row .slot-row');
    return { stage: SZMP1.stage(), runs: SZMP1.runs(), kind: szRunKind(), running: running, s1: document.body.classList.contains('szm1-s1'),
        grav: g ? getComputedStyle(g).visibility : null, slots: sr ? getComputedStyle(sr).visibility : null,
        lock: { beam: SZMP1.lock('beam'), fuel: SZMP1.lock('fuel'), cut: SZMP1.lock('cut') },
        mis: [missionState, missionZoneIdx, missionPendingUntil > 1e14], fuel: [Math.round(SZP.ch4 * 1e4) / 1e4, Math.round(SZP.lox * 1e4) / 1e4, SZP.mode],
        dep: depots.map(function(d){ return d.item + '@' + d.key; }).slice(0, 8), t: Math.round(elapsedMs), z: currentZoneIdx,
        act: window.__mp1Act || null, hint: g ? g.classList.contains('szm1-hint') : null, E: (window.__E || []).slice(0, 5) };
})()`;
/* 판을 진짜 경로로 시작(startGame) — 무적·목숨 고정, 첫 '활성' 미션 시각 기록 */
const MP1_GO = `(function(){
    if(!window.__inv) window.__inv = setInterval(function(){ invincibleUntil = 1e15; lives = 5; }, 50);
    window.__mp1Act = null;
    if(!window.__mp1Hook){ window.__mp1Hook = 1; SZE.on('tick', function(){ if(!window.__mp1Act && missionState === 'active' && missionKind === 'main') window.__mp1Act = [missionZoneIdx, Math.round(elapsedMs)]; }); }
    try{ startGame(); }catch(e){ return 'err ' + e.message; } return 1; })()`;
const mp1Jump = (s) => `(function(){ startedAt = performance.now() - ${s} * 1000 - totalPausedMs; return 1; })()`;
async function mp1WaitRun(e){ for(let i = 0; i < 60; i++){ if(await e.ev('!!running')) return true; await sleep(150); } return false; }
async function mp1Stages(base){
    return withEdge({ w: 390, h: 844, dsf: 3, mobile: true }, async (e) => {
        const out = {}, fn = (st) => path.join(OUT, 'mp1', 'stage_' + st + '.png');
        await e.open(gameUrl(base, 'ko'), 2200);
        await e.ev('SZMP1.pin(null); 1');
        /* det 시작 경로(G.begin — startGame·runStart 없음)에서의 상태: 새 프로필 = 기존 '첫 판'(szFirstRunCalc) · 단계 3(변화 없음) */
        out.det = await e.ev('(function(){ __G.begin(424242, false, true); var o = { first: szFirstRunCalc(), firstNow: szFirstRunNow(), stage: SZMP1.stage(), lock: [SZMP1.lock("beam"), SZMP1.lock("fuel"), SZMP1.lock("cut")], runs: SZMP1.runs() }; running = false; return o; })()');
        await e.open(gameUrl(base, 'ko'), 2200);
        await e.ev('SZMP1.pin(null); 1');
        out.runs0 = await e.ev('SZMP1.runs()');
        /* ── 1판 ── */
        out.go1 = await e.ev(MP1_GO); out.run1 = await mp1WaitRun(e);
        out.s1 = await e.ev(MP1_STATE);
        await e.ev(mp1Jump(10.4)); await sleep(500); await e.shot(fn('1_ring_10s'));
        await e.ev(mp1Jump(16)); await sleep(1200);
        out.s1b = await e.ev(MP1_STATE);
        out.s1drop = await e.ev('(function(){ var d = szDropDepot(0, "mp1probe", ITEM.HEART, performance.now()); return d === null ? "null" : "dropped"; })()');
        await e.shot(fn('1_play_16s'));
        await e.ev(mp1Jump(22.6)); await sleep(700);
        out.s1z1 = await e.ev(MP1_STATE);
        out.win1 = await e.ev('szMissionWin(1)');
        await sleep(6200);   /* 대기 미션 활성 시각은 벽시계 — 논리 시각을 건너뛰지 말고 실제로 기다린다(달 창 27.5초) */
        out.s1c = await e.ev(MP1_STATE);
        await e.ev('triggerGameOver(); 1'); await sleep(1800);
        out.runsAfter1 = await e.ev('SZMP1.runs()');
        /* ── 2판 ── */
        out.go2 = await e.ev(MP1_GO); out.run2 = await mp1WaitRun(e);
        out.s2 = await e.ev(MP1_STATE);
        await e.ev(mp1Jump(6.2)); await sleep(1600);
        out.s2b = await e.ev(MP1_STATE);
        await e.shot(fn('2_beam_hint'));
        await e.ev(mp1Jump(12)); await sleep(1500);
        out.s2c = await e.ev(MP1_STATE);
        await e.ev('triggerGameOver(); 1'); await sleep(1800);
        out.runsAfter2 = await e.ev('SZMP1.runs()');
        /* ── 3판 ── */
        out.go3 = await e.ev(MP1_GO); out.run3 = await mp1WaitRun(e);
        await sleep(2500);
        out.s3 = await e.ev(MP1_STATE);
        await e.shot(fn('3_full'));
        await e.ev('triggerGameOver(); 1'); await sleep(1500);
        /* ── 오늘의 코스(시드 판) — 판 수 0 으로 되돌린 뒤에도 3단계 ── */
        await e.ev('localStorage.setItem("szx_runs", "0"); 1');
        await e.open(gameUrl(base, 'ko'), 2200);
        await e.ev('SZMP1.pin(null); if(!window.__inv) window.__inv = setInterval(function(){ invincibleUntil = 1e15; lives = 5; }, 50); 1');
        out.dailyChip = await e.ev('(function(){ var b = document.getElementById("szDailyChip"); if(!b) return "no chip"; b.click(); return b.parentElement && b.parentElement.id; })()');
        await mp1WaitRun(e);
        out.daily = await e.ev(MP1_STATE);
        await e.ev('triggerGameOver(); 1'); await sleep(1200);
        /* ── 이미 해 본 기기 이전: szx_runs 없음 + szx_log.runs>0 → 3 ── */
        out.logRuns = await e.ev('szLog().runs');
        await e.ev('localStorage.removeItem("szx_runs"); 1');
        await e.open(gameUrl(base, 'ko'), 1800);
        out.migrated = await e.ev('SZMP1.runs()');
        const pe = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs('mp1 stages', e, pe);
        return out;
    });
}
/* 링크 진입 — mp1 켬/끔에서 같은 흐름인지 (시작 카드 숨김·도전장 띠·열린 패널). 네트워크는 막혀 있다(방 접속은 실패해도 흐름만 본다) */
async function mp1Links(base){
    const LINKS = [['ch', 'ch=a1b2c3-1n2o-gate&cv=2'], ['race', 'race=123456']];
    return withEdge({ w: 390, h: 844, dsf: 3, mobile: true }, async (e) => {
        const out = {};
        for(const [k, q] of LINKS) for(const f of ['1', '0']){
            await e.ev('try{ localStorage.clear(); sessionStorage.clear(); }catch(_){} 1').catch(() => {});
            await e.open(gameUrl(base, 'ko', q + '&mp1=' + f), 2600);
            out[k + '_' + f] = await e.ev(`(function(){ var ov = document.getElementById('overlay');
                var shown = [].slice.call(document.querySelectorAll('.pvp-overlay.on, .szx-panel.on, [id^=szx].on, #szxPanel')).filter(function(x){ return x.getClientRects().length && getComputedStyle(x).display !== 'none' && getComputedStyle(x).visibility !== 'hidden'; }).map(function(x){ return x.id || x.className; });
                return { ovHidden: ov.classList.contains('hidden'), start: !!ov.querySelector('#ovTitle'), chBanner: !!document.getElementById('szxChBanner'), shown: shown }; })()`);
            await e.shot(path.join(OUT, 'mp1', 'link_' + k + '_mp1-' + f + '.png'));
        }
        return out;
    });
}
async function runMp1(base){
    say('mp1: 시작 화면 ' + (MP1_LANGS.length * MP1_SIZES.length) + '개 + ?mp1=0 4개 + 단계 개방 + 링크 2종 → ' + path.join(OUT, 'mp1'));
    const start = await mp1Start(base);
    const off = await mp1Off(base);
    const stages = await mp1Stages(base);
    const links = await mp1Links(base);
    return { start, off, stages, links };
}
function judgeMp1(cur){
    const G = 'G30 mp1';
    for(const [k, r] of Object.entries(cur.start)){
        const s = r.scr;
        row(G, k + ' 처음 보이는 버튼(칩 제외)', s.n + ' (' + s.ids.join(' ') + ')', null, '≤ 5', s.applied && s.n <= 5 ? 'PASS' : 'FAIL', '칩: ' + s.chips.join(' '));
        row(G, k + ' 출발 버튼 스크롤 없이·엄지 영역', (s.inView ? '화면 안' : '가려짐') + ' · 중심 ' + s.cy + '% · 카드 넘침 ' + s.scroll + 'px', null, '화면 안 · 중심 ≥ 33%', s.inView && s.cy >= 33 ? 'PASS' : 'FAIL');
        row(G, k + ' 버튼 글자 잘림', s.clip.length ? s.clip.join(' ') : 0, null, '0', s.clip.length ? 'FAIL' : 'PASS');
        const c = r.cyc;
        row(G, k + ' 시트 열고 닫기 20회·옵저버 자극 — 버튼 수', c.states.length === 1 ? '불변 [' + c.c0 + ']' : '변함 ' + c.states.join(' / '), null, '불변·중복 id 0', c.states.length === 1 && /,0$/.test(c.c0) ? 'PASS' : 'FAIL', '[함께·설정·칩·카드 전체·.sz-opts·.szf-opts·szxMp·szxDuo·중복id]');
        const tg = c.tog || [];
        const needTog = ['szxRaceBtn', 'szxCoopBtn', 'ovCreateBtn', 'ovJoinBtn'].filter(x => !tg.includes(x));
        row(G, k + ' 함께 날기 시트 내용', tg.join(' '), null, '대결·협동·방 만들기·참여', needTog.length ? 'FAIL' : 'PASS', needTog.length ? '없음: ' + needTog.join(' ') : '');
        const st = c.set || {};
        row(G, k + ' 설정 시트 내용', '조향 ' + !!st.hand + ' · 소리칩 ' + !!st.opts + ' · 조작칩 ' + !!st.szf + ' · 버튼 ' + st.n, null, '조향·소리칩 있음', st.hand && st.opts ? 'PASS' : 'FAIL');
        row(G, k + ' 시트 카드 화면 안(함께 / 설정)', JSON.stringify(r.togScr) + ' / ' + JSON.stringify(r.setScr), null, '위 ≥0 · 아래 ≤ 화면', (r.togScr[0] >= 0 && r.togScr[1] <= r.togScr[2] && r.setScr[0] >= 0 && r.setScr[1] <= r.setScr[2]) ? 'PASS' : 'FAIL', r.setScr[3] > 0 ? '설정 카드 안 스크롤 ' + r.setScr[3] + 'px' : '');
    }
    const bs = BASE && BASE.startshot;
    for(const [k, r] of Object.entries(cur.off)){
        const b = bs && bs[k];
        if(!b){ row(G, '?mp1=0 ' + k + ' DOM 서명', '#' + r.dom, null, 'startshot 기준선', 'WARN', '기준선 없음'); continue; }
        let diff = '';
        if(r.dom !== b.dom && b.sig){ const bset = new Set(b.sig.map(x => JSON.stringify(x))); diff = '새: ' + r.sig.filter(x => !bset.has(JSON.stringify(x))).slice(0, 2).map(x => x.join(',')).join(' | '); }
        row(G, '?mp1=0 ' + k + ' DOM 서명 = MP0 시작 화면', r.dom === b.dom ? '같음 (' + r.nDom + '개)' : '다름', '#' + b.dom, '같음', r.dom === b.dom ? 'PASS' : 'FAIL', diff.slice(0, 160));
    }
    const S = cur.stages;
    const ok = (c) => c ? 'PASS' : 'FAIL';
    row(G, 'det 시작 경로(G.begin) 상태', JSON.stringify(S.det), null, '단계 3 · 잠금 없음(단계 개방이 det 를 바꾸지 않음)', ok(S.det && S.det.stage === 3 && !S.det.lock.some(Boolean)), '첫 판 판정(szFirstRunCalc) ' + (S.det && S.det.first) + ' — MP1 이전부터 det 기준선에 들어 있던 상태');
    row(G, '새 기기 판 수', S.runs0, null, '0', ok(S.runs0 === 0));
    const s1 = S.s1 || {};
    row(G, '1판 단계·숨김', 'stage ' + s1.stage + ' · BEAM ' + s1.grav + ' · 아이템 칸 ' + s1.slots + ' · 잠금 ' + JSON.stringify(s1.lock), null, '1 · hidden · hidden · 전부 잠김', ok(s1.stage === 1 && s1.grav === 'hidden' && s1.slots === 'hidden' && s1.lock && s1.lock.beam && s1.lock.fuel && s1.lock.cut));
    const s1b = S.s1b || {};
    row(G, '1판 16초 — 보급·연료', '캡슐 ' + JSON.stringify(s1b.dep) + ' · 연료 ' + JSON.stringify(s1b.fuel) + ' · 보급 투하 ' + S.s1drop + ' · 존0 미션 ' + JSON.stringify(s1b.mis), null, '캡슐 0 · 연료 1/1 · null · 대기(무기한)', ok(s1b.dep && s1b.dep.length === 0 && s1b.fuel && s1b.fuel[0] === 1 && s1b.fuel[1] === 1 && S.s1drop === 'null' && s1b.mis && s1b.mis[0] === 'pending' && s1b.mis[1] === 0 && s1b.mis[2]));
    const s1z1 = S.s1z1 || {};
    row(G, '1판 존 1 진입 — 존 0 대기 미션 정리·달 미션 대기', JSON.stringify(s1z1.mis) + ' · 달 창 ' + JSON.stringify(S.win1), null, "['pending',1,false] · on ≥ 25000", ok(s1z1.mis && s1z1.mis[0] === 'pending' && s1z1.mis[1] === 1 && !s1z1.mis[2] && S.win1 && S.win1.on >= 25000));
    const act = (S.s1c || {}).act;
    row(G, '1판 첫 활성 위성 미션 시각', JSON.stringify(act), null, '존 1 · ≥ 25000ms', ok(act && act[0] === 1 && act[1] >= 25000));
    row(G, '1판 끝 → 판 수', S.runsAfter1, null, '1', ok(S.runsAfter1 === 1));
    const s2 = S.s2 || {}, s2b = S.s2b || {}, s2c = S.s2c || {};
    row(G, '2판 단계·BEAM', 'stage ' + s2.stage + ' · BEAM ' + s2.grav + ' · 아이템 칸 ' + s2.slots + ' · 잠금 ' + JSON.stringify(s2.lock), null, '2 · visible · visible · 연료·차단만 잠김', ok(s2.stage === 2 && s2.grav === 'visible' && s2.slots === 'visible' && s2.lock && !s2.lock.beam && s2.lock.fuel && s2.lock.cut));
    row(G, '2판 보급 캡슐·힌트·연료', '캡슐 ' + JSON.stringify(s2b.dep) + ' · 힌트 ' + s2b.hint + ' · 연료(12초) ' + JSON.stringify(s2c.fuel), null, '캡슐 ≥1 · 힌트 true · 연료 1/1', ok(s2b.dep && s2b.dep.length >= 1 && s2b.hint === true && s2c.fuel && s2c.fuel[0] === 1));
    row(G, '2판 끝 → 판 수', S.runsAfter2, null, '2', ok(S.runsAfter2 === 2));
    const s3 = S.s3 || {};
    row(G, '3판 전부 열림·연료 소모', 'stage ' + s3.stage + ' · 잠금 ' + JSON.stringify(s3.lock) + ' · 연료 ' + JSON.stringify(s3.fuel), null, '3 · 잠금 없음 · 연료 < 1', ok(s3.stage === 3 && s3.lock && !s3.lock.beam && !s3.lock.fuel && !s3.lock.cut && s3.fuel && s3.fuel[0] < 1));
    const dl = S.daily || {};
    row(G, '오늘의 코스(시드 판, 판 수 0)', 'kind ' + dl.kind + ' · stage ' + dl.stage + ' · 칩 자리 ' + S.dailyChip, null, 'daily · 3', ok(dl.kind === 'daily' && dl.stage === 3));
    row(G, '기존 사용자 이전(szx_runs 없음, szx_log.runs ' + S.logRuns + ')', S.migrated, null, '3', ok(S.migrated === 3));
    for(const k of ['ch', 'race']){
        const a = cur.links[k + '_1'], b = cur.links[k + '_0'];
        row(G, '링크 진입 ?' + k + '= 흐름 (mp1 켬 / 끔)', JSON.stringify(a) + ' / ' + JSON.stringify(b), null, '같음', JSON.stringify(a) === JSON.stringify(b) ? 'PASS' : 'FAIL');
    }
}
EXT_CMDS.mp1 = { all: false, server: true, run: (base) => runMp1(base), judge: (cur) => judgeMp1(cur) };
/*</gate:mp1>*/
/*<gate:mp2>*/
/*</gate:mp2>*/
/*<gate:mp3>*/
/*</gate:mp3>*/
/*<gate:mp4>*/
/*</gate:mp4>*/
/*<gate:mp5>*/
/*</gate:mp5>*/
/*<gate:mp6>*/
/*</gate:mp6>*/
/*<gate:mp7>*/
/*</gate:mp7>*/
/*<gate:mp8>*/
/*</gate:mp8>*/

const ALL_CMDS = ['det', 'perf', 'layout', 'tm', 'i18n', 'fx0', 'beamdrain', 'hitpath', 'noshake'].concat(Object.keys(EXT_CMDS).filter(k => EXT_CMDS[k].all));
let CMDS = A._.length ? A._ : ['all'];
if(CMDS.includes('merge')) CMDS = [...new Set(CMDS.filter(c => c !== 'merge').concat(['all', 'restart', 'audioctx', 'latency', 'boot', 'flags0', 'startshot']))];
if(CMDS.includes('all')) CMDS = [...new Set(CMDS.filter(c => c !== 'all').concat(ALL_CMDS))];
if(CMDS.includes('full')) CMDS = [...new Set(CMDS.filter(c => c !== 'full').concat(ALL_CMDS, ['sweep', 'bot', 'soak', 'assets']))];
const KNOWN = ['det', 'perf', 'sweep', 'layout', 'tm', 'i18n', 'fx0', 'bot', 'ibot', 'soak', 'assets', 'beamdrain',
    'hitpath', 'noshake', 'restart', 'audioctx', 'latency', 'boot', 'flags0', 'startshot', 'gl0'].concat(Object.keys(EXT_CMDS));
for(const c of CMDS) if(!KNOWN.includes(c)){ console.error('알 수 없는 명령: ' + c); process.exit(2); }
/* MP0 — 명작화 킬스위치 전부 끔 쿼리 (flags0) */
const MP_OFF_Q = Array.from({ length: 8 }, (_, i) => 'mp' + (i + 1) + '=0').join('&');
const SEED_SET = Math.max(0, +(A['seed-set'] || 0));

const log = (...a) => { if(VERBOSE) console.log('[gate]', ...a); };
const say = (...a) => console.log('[gate]', ...a);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const sha = (o) => crypto.createHash('sha1').update(typeof o === 'string' ? o : JSON.stringify(o)).digest('hex').slice(0, 12);
const q = (arr, p) => arr.length ? arr[Math.min(arr.length - 1, Math.floor(arr.length * p))] : null;
const r1 = (v) => v == null ? v : Math.round(v * 10) / 10;
const r2 = (v) => v == null ? v : Math.round(v * 100) / 100;

/* ---------------- 결과 표 ---------------- */
const ROWS = [];
function row(gate, check, value, base, limit, status, note){ ROWS.push({ gate, check, value, base, limit, status, note: note || '' }); return ROWS[ROWS.length - 1]; }
/* 기준선과 똑같은 기존 문제(WARN) — 표에서는 접고 개수만 보여 준다 (--verbose 로 전부) */
const pre = (r, cond) => { if(cond && r && r.status === 'WARN') r.pre = true; return r; };
const fmt = (v) => v == null ? '-' : (typeof v === 'object' ? JSON.stringify(v) : String(v));

/* ---------------- 프로세스 관리 ---------------- */
const LIVE = new Set();          /* 살아 있는 Edge 인스턴스 */
const PROFILES = new Set();
let SERVER = null;
function killTree(pid){ try{ execFileSync('taskkill', ['/PID', String(pid), '/T', '/F'], { stdio: 'ignore' }); }catch(_){} }
function freePort(){ return new Promise((res, rej) => { const s = net.createServer(); s.unref(); s.on('error', rej); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); }); }
async function httpOk(url, ms = 1500){ try{ const c = new AbortController(); const t = setTimeout(() => c.abort(), ms); const r = await fetch(url, { signal: c.signal }); clearTimeout(t); return r.ok; }catch(_){ return false; } }

async function startServer(){
    const base = 'http://127.0.0.1:' + PORT;
    if(await httpOk(base + '/games/dodge/')) throw new Error('포트 ' + PORT + ' 가 이미 사용 중 — 다른 --port 를 주거나 그 서버를 끄세요 (게이트는 자기 서버를 직접 띄운다)');
    const py = process.platform === 'win32' ? 'python' : 'python3';
    SERVER = spawn(py, ['server.py'], { cwd: ROOT, env: { ...process.env, PORT: String(PORT), HOST: '127.0.0.1', PYTHONIOENCODING: 'utf-8' }, stdio: 'ignore', windowsHide: true });
    for(let i = 0; i < 80; i++){
        await sleep(250);
        if(await httpOk(base + '/games/dodge/')){
            /* 같은 포트를 0.0.0.0 으로 잡은 다른 서버가 있어도 뜰 수 있다 — 응답이 이 체크아웃의 파일인지 확인 */
            const body = await (await fetch(base + '/games/dodge/')).text();
            const disk = fs.readFileSync(GAME_FILE, 'utf8');
            if(body.replace(/\r\n/g, '\n') !== disk.replace(/\r\n/g, '\n')) throw new Error('127.0.0.1:' + PORT + ' 의 응답이 ' + GAME_FILE + ' 와 다름 — 다른 서버가 포트를 쓰는 중');
            return base;
        }
    }
    throw new Error('서버가 뜨지 않음: ' + ROOT + ' (python server.py, PORT=' + PORT + ')');
}
function stopServer(){ if(SERVER){ killTree(SERVER.pid); SERVER = null; } }

class Edge {
    constructor(){ this.id = 0; this.pend = new Map(); this.events = []; this.exc = []; this.cerr = []; this.logErr = []; }
    async launch(opts = {}){
        /* 가끔 디버깅 포트가 안 열린다(부하·포트 경합) — 새 포트·새 프로필로 3번까지 */
        for(let t = 1; ; t++){
            try{ return await this._launch(opts); }
            catch(e){
                try{ this.ws && this.ws.close(); }catch(_){}
                if(this.proc) killTree(this.proc.pid);
                LIVE.delete(this); await sleep(800);
                try{ fs.rmSync(this.prof, { recursive: true, force: true }); PROFILES.delete(this.prof); }catch(_){}
                if(t >= 3) throw e;
                log('Edge 재시도', t, e.message);
            }
        }
    }
    async _launch({ w = 412, h = 915, dsf = 2.625, mobile = true } = {}){
        if(!EDGE) throw new Error('msedge.exe 를 찾지 못함 (--edge 로 지정)');
        this.dport = await freePort();
        this.prof = path.join(PROF_DIR, PROF_PREFIX + '_' + process.pid + '_' + this.dport);
        PROFILES.add(this.prof);
        this.proc = spawn(EDGE, ['--headless=old', '--edge-skip-compat-layer-relaunch', '--remote-debugging-port=' + this.dport, '--remote-allow-origins=*', '--user-data-dir=' + this.prof,
            '--no-first-run', '--no-default-browser-check', '--disable-extensions', '--disable-sync', '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows', '--disable-features=CalculateNativeWinOcclusion,IntensiveWakeUpThrottling', '--mute-audio', '--autoplay-policy=no-user-gesture-required',
            '--window-size=' + w + ',' + h, 'about:blank'], { stdio: 'ignore', windowsHide: true });
        LIVE.add(this);
        let tabs = null;
        for(let i = 0; i < 120 && !tabs; i++){ await sleep(200); try{ const t = await (await fetch('http://127.0.0.1:' + this.dport + '/json')).json(); if(t.find(x => x.type === 'page')) tabs = t; }catch(_){} }
        if(!tabs) throw new Error('Edge 디버깅 포트 응답 없음');
        const page = tabs.find(t => t.type === 'page');
        this.ws = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((res, rej) => { this.ws.onopen = res; this.ws.onerror = rej; });
        this.ws.onmessage = (m) => {
            const d = JSON.parse(m.data);
            if(d.id && this.pend.has(d.id)){ const p = this.pend.get(d.id); this.pend.delete(d.id); clearTimeout(p.t); d.error ? p.rej(new Error(JSON.stringify(d.error))) : p.res(d.result); return; }
            if(d.method === 'Runtime.exceptionThrown'){ const ed = d.params.exceptionDetails; this.exc.push(((ed.exception && ed.exception.description) || ed.text || '').split('\n')[0].slice(0, 200) + ' @' + ed.lineNumber); }
            else if(d.method === 'Runtime.consoleAPICalled' && d.params.type === 'error'){ this.cerr.push(d.params.args.map(a => a.value != null ? String(a.value) : (a.description || '')).join(' ').slice(0, 200)); }
            else if(d.method === 'Log.entryAdded' && d.params.entry.level === 'error'){ this.logErr.push((d.params.entry.source + ': ' + d.params.entry.text + ' ' + (d.params.entry.url || '')).slice(0, 200)); }
        };
        await this.send('Page.enable'); await this.send('Runtime.enable'); await this.send('Log.enable'); await this.send('Network.enable');
        /* 외부 요청 전부 차단 — Supabase(리더보드·기록 RPC)·광고·폰트. 게이트가 운영 DB 에 기록을 남기면 안 된다 */
        await this.send('Network.setBlockedURLs', { urls: ['https://*', 'wss://*', 'http://*.supabase.co*'] });
        await this.metrics({ w, h, dsf, mobile });
        try{ await this.send('Emulation.setFocusEmulationEnabled', { enabled: true }); }catch(_){}
        await this.send('Page.addScriptToEvaluateOnNewDocument', { source: `window.__E=[];addEventListener("error",function(e){__E.push(String(e.message).slice(0,200)+" @"+e.lineno)});addEventListener("unhandledrejection",function(e){__E.push("rejection: "+String(e.reason&&e.reason.message||e.reason).slice(0,200))});
            window.__LT=[];try{new PerformanceObserver(function(l){l.getEntries().forEach(function(e){__LT.push([Math.round(e.startTime),Math.round(e.duration)])})}).observe({entryTypes:['longtask']})}catch(e){}` });
        return this;
    }
    async metrics({ w, h, dsf = 1, mobile = false }){
        await this.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: dsf, mobile });
        await this.send('Emulation.setTouchEmulationEnabled', { enabled: !!mobile, maxTouchPoints: mobile ? 5 : 1 });
    }
    send(method, params = {}, timeout = 60000){
        const i = ++this.id;
        return new Promise((res, rej) => {
            const t = setTimeout(() => { this.pend.delete(i); rej(new Error('CDP 시간 초과: ' + method)); }, timeout);
            this.pend.set(i, { res, rej, t });
            try{ this.ws.send(JSON.stringify({ id: i, method, params })); }catch(e){ clearTimeout(t); this.pend.delete(i); rej(e); }
        });
    }
    async ev(expr, timeout = 60000){
        const r = await this.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }, timeout);
        if(r.exceptionDetails) throw new Error('page: ' + JSON.stringify(r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text).slice(0, 600));
        return r.result.value;
    }
    async open(url, settle = 2600){
        await this.send('Page.navigate', { url });
        for(let i = 0; i < 100; i++){ await sleep(150); try{ if(await this.ev('document.readyState === "complete" && typeof gameLoop === "function"', 5000)) break; }catch(_){} }
        await sleep(settle);
        await this.ev(PAGE_LIB);
    }
    async shot(file){ const r = await this.send('Page.captureScreenshot', { format: 'png' }, 30000); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, Buffer.from(r.data, 'base64')); }
    async close(){
        try{ if(this.ws && this.ws.readyState === 1) await Promise.race([this.send('Browser.close', {}, 2000), sleep(1500)]); }catch(_){}
        try{ this.ws && this.ws.close(); }catch(_){}
        if(this.proc) killTree(this.proc.pid);
        LIVE.delete(this);
        await sleep(600);
        for(let i = 0; i < 6; i++){ try{ fs.rmSync(this.prof, { recursive: true, force: true }); PROFILES.delete(this.prof); break; }catch(_){ await sleep(700); } }
    }
    errors(){ return { exc: this.exc.slice(), cerr: this.cerr.slice(), logErr: this.logErr.slice() }; }
}
async function withEdge(opts, fn){ const e = new Edge(); try{ await e.launch(opts); return await fn(e); } finally { await e.close(); } }
async function pool(items, n, fn){
    const out = new Array(items.length); let k = 0;
    const worker = async () => { while(k < items.length){ const i = k++; try{ out[i] = await fn(items[i], i); }catch(e){ /* 한 번 더 */ try{ out[i] = await fn(items[i], i); }catch(e2){ throw new Error('작업 ' + i + ' 실패: ' + e2.message); } } } };
    await Promise.all(Array.from({ length: Math.min(n, items.length) }, worker));
    return out;
}
/* 페이지 에러 수집 — 모든 세션 합산 */
const ERR = { exc: [], cerr: [], pageE: [] };
function collectErrs(tag, e, pageE){
    const x = e.errors();
    for(const s of x.exc) ERR.exc.push(tag + ': ' + s);
    for(const s of x.cerr) ERR.cerr.push(tag + ': ' + s);
    for(const s of (pageE || [])) ERR.pageE.push(tag + ': ' + s);
}

/* ---------------- 페이지 쪽 도구 (문자열로 주입) ---------------- */
function pageLib(){
    if(window.__G) return 1;
    const realPN = performance.now.bind(performance);
    const rafReal = window.requestAnimationFrame.bind(window);
    const R1 = v => Math.round(v * 10) / 10, R2 = v => Math.round(v * 100) / 100;
    const G = window.__G = { realPN, rafReal };
    const HZ = ['spawnAsteroidCluster', 'spawnSolarFlare', 'spawnComet', 'spawnSplitter', 'spawnWave', 'spawnMagneticMine', 'spawnSupernovaRing', 'nhSpawnTick'];
    /* 합성 시계 — performance.now 를 VT 로 고정하고 rAF 를 끊는다. gameLoop 는 직접 부른다 */
    G.synth = function(){ G.VT = 1e6; performance.now = () => G.VT; window.requestAnimationFrame = () => 0; window.__szLockTier = 1; };
    G.unsynth = function(){ performance.now = realPN; window.requestAnimationFrame = rafReal; };
    G.begin = function(seed, racing, noMission){
        if(racing) SZX.racing = () => true;
        resetGame(); applySteerToControlRow(); $('overlay').classList.add('hidden');
        if(seed) _setSeed(seed);
        running = true; paused = false; startedAt = performance.now(); totalPausedMs = 0; pausedAt = 0; lastSpawn = 0; lastFrame = performance.now(); zoneLabel = { idx: 0, timer: 0 };
        if(!noMission) startMissionForZone(0, startedAt);
    };
    G.visibleText = function(){
        const out = [];
        const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let n;
        while((n = w.nextNode())){
            const s = n.nodeValue.replace(/\s+/g, ' ').trim(); if(!s) continue;
            const el = n.parentElement; if(!el) continue;
            if(el.closest('.lp-game-about, script, style, noscript, template')) continue;
            if(!el.getClientRects().length) continue;
            const cs = getComputedStyle(el); if(cs.visibility === 'hidden' || +cs.opacity === 0) continue;
            let hid = false; for(let p = el; p && p !== document.body; p = p.parentElement){ const c = getComputedStyle(p); if(c.display === 'none' || +c.opacity === 0){ hid = true; break; } }
            if(!hid) out.push(s.slice(0, 160));
        }
        return [...new Set(out)];
    };
    /* 캔버스 글자 수집 (문자열 → 최소 CSS px). DOM 캔버스만 크기를 잰다 */
    G.hookText = function(){
        if(G.texts) return; G.texts = new Map();
        const P = CanvasRenderingContext2D.prototype;
        for(const fn of ['fillText', 'strokeText']){
            const o = P[fn];
            P[fn] = function(s, x, y, mw){
                try{
                    const str = String(s);
                    if(str.trim()){
                        let px = null; const cv = this.canvas;
                        if(cv && cv.isConnected){ const m = /(\d+(?:\.\d+)?)px/.exec(this.font); const rw = cv.getBoundingClientRect().width;
                            if(m && rw){ const tr = this.getTransform(); px = R1(+m[1] * Math.hypot(tr.a, tr.b) / (cv.width / rw)); } }
                        const p = G.texts.get(str); if(p === undefined || (px != null && (p == null || px < p))) G.texts.set(str, px);
                    }
                }catch(_){}
                return o.apply(this, arguments);
            };
        }
    };
    G.det = function(P){
        const out = { errs: [] };
        if(P.noDraw) window.drawFrame = function(){};   /* 검증용 — 봇이 그리기를 끄고 돌려도 시뮬이 같은지 */
        G.synth();
        G.begin(0, P.racing, true);
        /* 1:1 PvP 호스트 — 채널 없이 호스트 경로(공유 조준·위험물 끔·보급 결정)만 돈다 */
        if(P.pvp){ pvpState.gameMode = 'pvp'; pvpState.role = 'host'; pvpState.channel = null; }
        _setSeed(P.seed);
        const gR = _seededRng, gH = _rngH, gD = _rngD;
        /* 결정성 v2(P2) 이후엔 위험물 스케줄러(SZ_HZ)가 '어느 존의 몇 ms 사건'인지 안다 — 프레임과 무관한 기록 */
        const hzOn = () => (typeof SZ_HZ !== 'undefined' && SZ_HZ && SZ_HZ.firing);
        const hzZ = () => hzOn() ? SZ_HZ.fz : currentZoneIdx;
        let nR = 0, nH = 0, nD = 0; const H = [], D = [];
        _seededRng = function(){ nR++; return gR(); };
        /* 시각 = 스케줄러의 논리 사건 시각(있으면). 히트스톱 뒤 프레임 양자화로 관측 시각만 흔들리는 것을 빼고 본다 */
        _rngH = function(){ const v = gH(); nH++; H.push([hzOn() ? Math.round(SZ_HZ.ft) : Math.round(elapsedMs), hzZ(), v]); return v; };
        _rngD = function(){ const v = gD(); nD++; D.push([Math.round(elapsedMs), currentZoneIdx, v]); return v; };
        const haz = [], hz2 = [];
        for(const n of HZ){ const o = window[n]; if(typeof o !== 'function') continue;
            window[n] = function(){ const h0 = nH, t = elapsedMs, z = hzZ(); const r = o.apply(this, arguments); if(nH !== h0 || n !== 'nhSpawnTick') haz.push([n, z, h0, nH, Math.round(t)]);
                if(n !== 'nhSpawnTick') hz2.push([n, z, hzOn() ? Math.round(SZ_HZ.ft) : null, nH - h0]); return r; }; }
        /* 운석 스폰 목록 — 스폰 순간 좌표(프레임 이동 전)·논리 스폰 시각. 폭탄으로 바로 지워지는 운석도 포함 */
        const metS = []; const oSB = window.spawnBullet; let nS = 0;
        window.spawnBullet = function(){ const n0 = bullets.length; const r = oSB.apply(this, arguments);
            for(let i = n0; i < bullets.length; i++){ nS++; const b = bullets[i]; if(metS.length < (P.nMetS || 1500)) metS.push([Math.round(lastSpawn - startedAt - totalPausedMs), R2(b.x), R2(b.y), R2(b.vx), R2(b.vy)]); }
            return r; };
        startedAt = G.VT; lastFrame = G.VT; lastSpawn = 0; if(!P.pvp) startMissionForZone(0, startedAt);
        const seenB = new WeakSet(), seenD = new WeakSet(); const met = [], dep = {}, bh = [];
        let nextBh = 0, bombI = 0, frames = 0, nextStop = 7000, nextWarp = 30000, nStop = 0, nWarp = 0; const t0 = realPN();
        const bombAt = P.bomb ? [40, 130, 260, 400] : [];
        while(G.VT - startedAt < P.secs * 1000 && running){
            G.VT += P.step; frames++;
            invincibleUntil = 1e15; player.x = 180; player.y = 390;
            /* fx — 히트스톱(세상 정지)·TIME_WARP(세상 감속)을 일부러 건다. 스폰 시각·목록은 그대로여야 한다 */
            if(P.fx){
                if(elapsedMs >= nextStop){ nextStop += 7000; nStop++; try{ szHitStopUntil = G.VT + 140; }catch(_){} }
                if(elapsedMs >= nextWarp){ nextWarp += 60000; nWarp++; try{ timeWarpUntil = G.VT + 12000; timeWarpStartedAt = G.VT; }catch(_){} }
            }
            if(P.mission === 'success' && missionState === 'active') try{ completeMission(G.VT); }catch(e){ out.errs.push('completeMission ' + e.message); }
            if(bombI < bombAt.length && elapsedMs >= bombAt[bombI] * 1000){ bombI++; try{ triggerWipe(); }catch(e){ out.errs.push('wipe ' + e.message); } }
            try{ gameLoop(G.VT); }catch(e){ out.errs.push(String(e && e.stack || e).split('\n').slice(0, 2).join(' | ').slice(0, 240)); if(out.errs.length > 12) break; }
            for(const b of bullets){ if(!seenB.has(b)){ seenB.add(b); if(met.length < P.nMet) met.push([Math.round(elapsedMs), R2(b.x), R2(b.y), R2(b.vx), R2(b.vy)]); } }
            for(const d of depots){ if(!seenD.has(d)){ seenD.add(d); dep[d.key] = [R1(d.x), R1(d.y), d.zoneIdx, d.slot, Math.round(elapsedMs), String(d.item)]; } }
            if(typeof isBlackHoleZone === 'function' && isBlackHoleZone() && elapsedMs >= nextBh){ nextBh = elapsedMs + 500; bh.push([Math.round(elapsedMs / 100), R1(blackHole.cx), R1(blackHole.cy), R1(blackHole.r), R1(blackHole.jetReach)]); }
        }
        const endReason = running ? 'secs' : 'stopped';
        running = false; G.unsynth();
        if(P.pvp){ pvpState.gameMode = null; pvpState.role = ''; }
        const fl = hz2.find(x => x[0] === 'spawnSolarFlare');
        Object.assign(out, { frames, wall: Math.round(realPN() - t0), nR, nH, nD, nS, nStop, nWarp, endZone: currentZoneIdx, endSec: Math.round(elapsedMs / 100) / 10, endReason, H, D, haz, hz2, met, metS, dep, bh,
            flare0: fl ? (fl[2] != null ? fl[2] : null) : null, flare0Seen: haz.length ? (haz.find(x => x[0] === 'spawnSolarFlare') || [0, 0, 0, 0, null])[4] : null, E: (window.__E || []).slice(0, 8) });
        return out;
    };
    /* 실시간 성능 구간 — gameLoop 를 감싸 한 프레임 JS 시간을 잰다 */
    G.perfStart = function(P){
        window.__M = { fr: [], mark: 0, markT: 0 };
        G.begin(P.seed, false);
        const T = performance.now(); startedAt = T; lastSpawn = T; lastFrame = T; lives = 5; invincibleUntil = 1e15;
        window.__szLockTier = 1; window.__szFuelInf = 1; try{ if(window.SZ3 && SZ3.setTier) SZ3.setTier(P.tier); }catch(_){}
        const og = gameLoop; let last = 0;
        window.gameLoop = function(t){
            const rec = { iv: last ? t - last : 0, z0: currentZoneIdx, m0: missionState }; last = t;
            const s = performance.now(); og(t); rec.js = performance.now() - s;
            rec.z1 = currentZoneIdx; rec.m1 = missionState; __M.fr.push(rec);
            invincibleUntil = 1e15; if(paused) paused = false;
        };
        requestAnimationFrame(gameLoop);
        return ZONES.length;
    };
    G.perfJump = function(z){ const now = performance.now(); if(z > 0) startedAt = now - (ZONES[z].s * 1000 - 800) - totalPausedMs; __M.mark = __M.fr.length; __M.markT = now; return 1; };
    /* 예고 전(idle)이면 바로 발동 — 캡처 타이밍에 따라 idle 이 걸려 'SAT·BEAM 버튼 (idle)' FAIL 이 해상도를 옮겨 다녔다(2026-10-08) */
    G.forceMission = function(){
        if(missionState === 'pending'){ missionPendingUntil = performance.now() + 30; return 1; }
        if(missionState !== 'active' && typeof _activateMission === 'function'){ try{ _activateMission(performance.now()); return 2; }catch(_){} }
        return 0;
    };
    G.perfCollect = function(){
        const a = __M.fr.slice(__M.mark);
        const tr = a.filter(x => x.z0 !== x.z1), ac = a.filter(x => x.m0 === 'pending' && x.m1 === 'active');
        const steady = a.filter(x => x.z0 === x.z1 && !(x.m0 === 'pending' && x.m1 === 'active')).map(x => x.js);
        const iv = a.map(x => x.iv).filter(x => x > 0).sort((p, q) => p - q);
        const lt = (window.__LT || []).filter(x => x[0] >= __M.markT);
        return { n: a.length, steady, zoneJs: tr.map(x => x.js), actJs: ac.map(x => x.js), iv50: iv.length ? iv[Math.floor(iv.length / 2)] : null, lt50: lt.filter(x => x[1] > 50).length, ltMax: lt.reduce((m, x) => Math.max(m, x[1]), 0), running, E: (window.__E || []).slice(0, 5) };
    };
    /* 존 순회 — 합성 시계로 존마다 몇 프레임씩 그린다 (글자 수집·킬스위치·에러 확인) */
    G.tour = function(P){
        const errs = [];
        G.synth(); G.begin(P.seed || 424242, false); window.__szFuelInf = 1;   /* 무적 순회 — 추진제도 무한(sz:mod:fuel) */
        startedAt = G.VT; lastFrame = G.VT;
        const zones = P.zones || ZONES.map((_, i) => i);
        let frames = 0;
        const run = (n) => { for(let i = 0; i < n; i++){ G.VT += P.step || 16.667; frames++; invincibleUntil = 1e15; player.x = 180; player.y = 390; if(paused) paused = false;
            try{ gameLoop(G.VT); }catch(e){ errs.push(String(e && e.stack || e).split('\n').slice(0, 2).join(' | ').slice(0, 240)); if(errs.length > 20) return; } } };
        for(const z of zones){
            startedAt = G.VT - (ZONES[z].s * 1000 + 300) - totalPausedMs;
            run(P.frames || 60);
            if(missionState === 'pending') missionPendingUntil = G.VT + 1;
            run(P.frames || 60);
            if(P.textAt && P.textAt.includes(z)) (G.midDom = G.midDom || []).push(...G.visibleText());
        }
        G.unsynth(); window.__szFuelInf = 0;
        return { frames, errs, E: (window.__E || []).slice(0, 8), zones: zones.length };
    };
    /* 레이아웃 검사 */
    G.layout = function(){
        const vw = innerWidth, vh = innerHeight;
        const SEL = ['#gravBtn', '#satBtn', '#itemSlot0', '#itemSlot1', '#itemSlot2', '#itemSlot3', '#itemSlot4', '#pauseBtn', '#ovBtn', '#missionBanner', '.control-row', '.topbar', '.score-strip', '.szx-live', '.sz-pilot', '#rewardRow', '#introStory', '#tpRing', '#handToggle', '#overlay .ov-btn-row', '#dodge-canvas', '.dodge-kbd-ref'];
        const CTRL = ['#gravBtn', '#satBtn', '#itemSlot0', '#itemSlot1', '#itemSlot2', '#itemSlot3', '#itemSlot4', '#pauseBtn', '#ovBtn'];
        const vis = (el) => { if(!el || !el.getClientRects().length || el.closest('.hidden')) return false; for(let p = el; p && p !== document.documentElement; p = p.parentElement){ const c = getComputedStyle(p); if(c.display === 'none' || c.visibility === 'hidden' || +c.opacity < 0.05) return false; } const r = el.getBoundingClientRect(); return r.width > 1 && r.height > 1; };
        const rects = {};
        for(const s of SEL){ const el = document.querySelector(s); if(vis(el)){ const r = el.getBoundingClientRect(); rects[s] = [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; } }
        const small = CTRL.filter(s => rects[s] && Math.min(rects[s][2], rects[s][3]) < 44).map(s => s + ' ' + rects[s][2] + 'x' + rects[s][3]);
        const clip = Object.entries(rects).filter(([s, r]) => r[0] < -1 || r[1] < -1 || r[0] + r[2] > vw + 1 || r[1] + r[3] > vh + 1).map(([s, r]) => s + ' ' + r.join(','));
        const OV = ['#missionBanner', '.szx-live', '.control-row', '.topbar', '.score-strip', '.sz-pilot', '#rewardRow', '#tpRing', '#dodge-canvas', '.dodge-kbd-ref'];
        const overlap = [];
        for(let i = 0; i < OV.length; i++) for(let j = i + 1; j < OV.length; j++){
            const a = rects[OV[i]], b = rects[OV[j]]; if(!a || !b) continue;
            const ix = Math.min(a[0] + a[2], b[0] + b[2]) - Math.max(a[0], b[0]), iy = Math.min(a[1] + a[3], b[1] + b[3]) - Math.max(a[1], b[1]);
            if(ix > 2 && iy > 2){ const inside = (x, y) => x[0] >= y[0] - 1 && x[1] >= y[1] - 1 && x[0] + x[2] <= y[0] + y[2] + 1 && x[1] + x[3] <= y[1] + y[3] + 1; if(!inside(a, b) && !inside(b, a)) overlap.push(OV[i] + '×' + OV[j]); }
        }
        const se = document.scrollingElement || document.documentElement;
        const hScroll = Math.max(se.scrollWidth, document.body.scrollWidth) - vw;
        let smallText = [];
        if(G.texts) smallText = [...G.texts.entries()].filter(([s, px]) => px != null && px < 9).map(([s, px]) => s.slice(0, 24) + '@' + px);
        const missing = ['#satBtn', '#gravBtn'].filter(s => !rects[s]);
        /* E (2026-09-29) — 조종판·키 가이드가 캔버스(플레이필드)를 덮는 넓이(px). 0 이어야 한다 (PC 에서 56px 덮던 문제) */
        const cov = {};
        for(const s of ['.control-row', '.dodge-kbd-ref']){ const a = rects[s], b = rects['#dodge-canvas']; if(!a || !b) continue;
            const ix = Math.min(a[0] + a[2], b[0] + b[2]) - Math.max(a[0], b[0]), iy = Math.min(a[1] + a[3], b[1] + b[3]) - Math.max(a[1], b[1]); cov[s] = (ix > 0 && iy > 0) ? ix : 0; }
        /* SZF (2026-10-07) — 세로 터치 기본 '플로팅 조작': .control-row 는 왼쪽 열 전체를 덮는 투명 입력 층(버튼만 떠 있고 위험물 근처에서 흐려진다).
           캔버스를 덮는 게 설계라 cov 검사 대신 버튼 ≥48px 를 본다 */
        const float = document.body.classList.contains('sz-float');
        const fbtn = float ? ['#gravBtn', '#satBtn', '#itemSlot0'].filter(s => rects[s]).map(s => s + ' ' + rects[s][2] + 'x' + rects[s][3]) : [];
        return { vw, vh, hScroll, rects, small, clip, overlap, missing, cov, float, fbtn, mission: (typeof missionState !== 'undefined') ? missionState : null, smallText: smallText.slice(0, 80), nSmallText: smallText.length };
    };
    /* 자동 조종봇 — 같은 시드, 봇 난수만 다르게. 그리기는 끈다(시뮬만) */
    G.bot = function(P){
        const res = [];
        const oDraw = window.drawFrame, oOver = window.triggerGameOver;
        window.drawFrame = function(){};
        let dead = false;
        window.triggerGameOver = function(){ running = false; dead = true; };
        const mb = (s) => { let a = s | 0; return () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), a | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
        const DIRS = [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1], [0.707, 0.707], [-0.707, 0.707], [0.707, -0.707], [-0.707, -0.707]];
        const SP = (typeof PLAYER_SPEED !== 'undefined') ? PLAYER_SPEED : 300;
        const HR = (typeof HIT_RADIUS !== 'undefined') ? HIT_RADIUS : 5;
        const pure = [['checkSolarFlareCollision', 0], ['checkSupernovaRingCollision', 0], ['checkPulsarBeamCollision', 1], ['checkCometCollision', 0], ['checkSplitterCollision', 0], ['checkBlackHoleJetCollision', 0]]
            .filter(([n]) => typeof window[n] === 'function');
        G.synth();
        /* bot 은 보급을 안 줍는다 — 위험물 난이도만 재도록 추진제는 무한(2026-10-08 sz:mod:fuel). 연료는 ibot 이 잰다 */
        window.__szFuelInf = 1;
        for(let bi = 0; bi < P.botSeeds.length; bi++){
            const bs = P.botSeeds[bi];
            const br = mb(bs);
            dead = false;
            /* 코스 시드 — 기본은 하나(P.seed). --course-seeds 면 판마다 다른 코스(코스를 바꾸는 변경의 분포 비교용) */
            G.begin(P.courseSeeds ? P.courseSeeds[bi] : P.seed, false);
            invincibleUntil = 0;
            let nextDecide = 0, dir = DIRS[0], frames = 0; const lifeLost = [];
            let lv = lives;
            const score = (d) => {
                let s = 0; const ox = player.x, oy = player.y;
                for(let k = 1; k <= 4; k++){
                    const t = k * 0.07;
                    const px = Math.max(16, Math.min(CW - 16, ox + d[0] * SP * t)), py = Math.max(18, Math.min(CH - 18, oy + d[1] * SP * t));
                    for(const b of bullets){ const dx = b.x + b.vx * t - px, dy = b.y + b.vy * t - py; const dd = Math.sqrt(dx * dx + dy * dy) - HR - 6; s += dd < 0 ? 400 / k : 40 / (k * (dd + 6) * (dd + 6)); }
                    if(typeof asteroidClusters !== 'undefined') for(const c of asteroidClusters) for(const r of c.rocks){ const dd = Math.hypot(r.x + (r.vx || c.vx || 0) * t - px, r.y + (r.vy || c.vy || 0) * t - py) - r.r - HR; s += dd < 0 ? 400 / k : 30 / (k * (dd + 6) * (dd + 6)); }
                    if(typeof magneticMines !== 'undefined') for(const m of magneticMines){ const dd = Math.hypot(m.x - px, m.y - py) - (typeof MINE_R !== 'undefined' ? MINE_R : 10) - HR; s += dd < 0 ? 400 / k : 30 / (k * (dd + 6) * (dd + 6)); }
                    player.x = px; player.y = py;
                    for(const [n, withNow] of pure){ try{ if(withNow ? window[n](G.VT) : window[n]()) s += 300 / k; }catch(_){} }
                    player.x = ox; player.y = oy;
                    s += 0.00002 * ((px - CW * 0.5) ** 2 + (py - CH * 0.62) ** 2);
                }
                return s;
            };
            while(G.VT - startedAt < P.secs * 1000 && running){
                G.VT += P.step; frames++;
                if(elapsedMs >= nextDecide){
                    /* 반응 지연 90~170ms, 가끔(4%) 멍때림 */
                    nextDecide = elapsedMs + 90 + br() * 80;
                    if(br() > 0.04){ let best = Infinity; for(const d of DIRS){ const s = score(d) + br() * 0.002; if(s < best){ best = s; dir = d; } } }
                    for(const k of ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown']) keys[k] = false;
                    if(dir[0] < -0.1) keys.ArrowLeft = true; if(dir[0] > 0.1) keys.ArrowRight = true;
                    if(dir[1] < -0.1) keys.ArrowUp = true; if(dir[1] > 0.1) keys.ArrowDown = true;
                }
                if(missionState === 'active' && br() < 0.02) try{ completeMission(G.VT); }catch(_){}
                try{ gameLoop(G.VT); }catch(e){ res.push({ err: String(e.message).slice(0, 160) }); running = false; break; }
                if(lives < lv) lifeLost.push(Math.round(elapsedMs / 100) / 10); lv = lives;
            }
            for(const k of ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown']) keys[k] = false;
            res.push({ bs, t: Math.round(elapsedMs / 100) / 10, z: currentZoneIdx, dead, frames, lost: lifeLost.slice(0, 12) });
            running = false;
        }
        G.unsynth(); window.__szFuelInf = 0;
        window.drawFrame = oDraw; window.triggerGameOver = oOver;
        return res;
    };
    /* 아이템 봇 (2026-10-08) — G.bot 과 같은 회피에 ① 보급 캡슐 쪽으로 가서 BEAM 으로 끌기 ② 아이템 사용(위험할 때 방어형,
       윙맨 등은 바로) ③ 위성 미션을 확률 P.misP 로 성공(성공이면 활성 뒤 1.5~6초에 설치, 실패면 시간 초과)를 더한다.
       첫 판 완화(szFirstRunCalc)는 끈다 — 운영자처럼 여러 판 해 본 플레이어. 판마다 피격 시각 전부·주운/쓴 아이템·보급 차단 시각 */
    G.ibot = function(P){
        const res = [];
        const oDraw = window.drawFrame, oOver = window.triggerGameOver;
        window.drawFrame = function(){};
        let dead = false, deadKind = null;
        window.triggerGameOver = function(k){ running = false; dead = true; deadKind = k || null; };
        try{ window.szFirstRunCalc = function(){ return false; }; }catch(_){}
        window.__szFuelInf = 0;
        /* --no-cut — 보급 영구 차단 규칙만 끈 비교용 */
        if(P.noCut) try{ window.szSatMissed = function(){}; }catch(_){}
        const mb = (s) => { let a = s | 0; return () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), a | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
        const DIRS = [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1], [0.707, 0.707], [-0.707, 0.707], [0.707, -0.707], [-0.707, -0.707]];
        const SP = (typeof PLAYER_SPEED !== 'undefined') ? PLAYER_SPEED : 300;
        const HR = (typeof HIT_RADIUS !== 'undefined') ? HIT_RADIUS : 5;
        const MAXL = (typeof MAX_LIVES !== 'undefined') ? MAX_LIVES : 5;
        const pure = [['checkSolarFlareCollision', 0], ['checkSupernovaRingCollision', 0], ['checkPulsarBeamCollision', 1], ['checkCometCollision', 0], ['checkSplitterCollision', 0], ['checkBlackHoleJetCollision', 0]]
            .filter(([n]) => typeof window[n] === 'function');
        /* 보스(S2 별·퀘이사 제트)·블랙홀 지평선도 내다본다 — G.bot 은 이걸 못 봐서 7~9분 보스에서 무더기로 죽는다 */
        if(typeof checkZoneBossCollision === 'function') pure.push(['checkZoneBossCollision', 1]);
        const NOW_USE = { mini: 1, whipple: 1, lidar: 1, laser: 1, aerogel: 1 };
        const DEF_ORDER = ['shield', 'antigrav', 'ion', 'rail', 'wipe'];
        /* 추진제 (2026-10-08 sz:mod:fuel) — 탱커(item 'fuel')는 슬롯과 무관하게 줍는다. --no-tank 면 일부러 안 줍는다.
           연료 70% 넘으면 노리지 않고(원뿔에 들면 줍기만), 그 아래면 거리에 (0.25 + 연료) 를 곱한다 — 사람처럼 연료가 낮을수록 탱커를 먼저 */
        const fuelLv = () => { try{ return SZP.mode >= 1 ? 0 : Math.min(SZP.ch4, SZP.lox); }catch(_){ return 1; } };
        const pickable = (d) => !d.collected && !d.collectedByPeer && (d.item === 'fuel' ? !P.noTank : d.item === 'heart' ? lives < MAXL : inventoryHasSpace());
        G.synth();
        for(let bi = 0; bi < P.botSeeds.length; bi++){
            const bs = P.botSeeds[bi];
            const br = mb(bs), bm = mb(bs ^ 0x5bd1e995);
            dead = false; deadKind = null;
            G.begin(P.courseSeeds ? P.courseSeeds[bi] : P.seed, false);
            invincibleUntil = 0;
            if(G.ibotPre) try{ G.ibotPre(P, bi); }catch(_){}   /* MP0 — 패키지 고리(예: 편한 비행·연습 비행 시작 막) */
            let nextDecide = 0, dir = DIRS[0], frames = 0; const lifeLost = [];
            let fuelMin = 1, moved = 0, mpx = player.x, mpy = player.y;
            let lv = lives; const picks = {}, uses = {}; let misKey = '', misOk = false, misAt = 0, nMis = 0, nMisOk = 0, cutAt = null;
            const nPick0 = {};
            const oPick = window.onDepotCollected;
            window.onDepotCollected = function(d){ picks[d.item] = (picks[d.item] || 0) + 1; return oPick.apply(this, arguments); };
            const score = (d, tgt) => {
                let s = 0; const ox = player.x, oy = player.y;
                for(let k = 1; k <= 4; k++){
                    const t = k * 0.07;
                    const px = Math.max(16, Math.min(CW - 16, ox + d[0] * SP * t)), py = Math.max(18, Math.min(CH - 18, oy + d[1] * SP * t));
                    for(const b of bullets){ const dx = b.x + b.vx * t - px, dy = b.y + b.vy * t - py; const dd = Math.sqrt(dx * dx + dy * dy) - HR - 6; s += dd < 0 ? 400 / k : 40 / (k * (dd + 6) * (dd + 6)); }
                    if(typeof asteroidClusters !== 'undefined') for(const c of asteroidClusters) for(const r of c.rocks){ const dd = Math.hypot(r.x + (r.vx || c.vx || 0) * t - px, r.y + (r.vy || c.vy || 0) * t - py) - r.r - HR; s += dd < 0 ? 400 / k : 30 / (k * (dd + 6) * (dd + 6)); }
                    if(typeof magneticMines !== 'undefined') for(const m of magneticMines){ const dd = Math.hypot(m.x - px, m.y - py) - (typeof MINE_R !== 'undefined' ? MINE_R : 10) - HR; s += dd < 0 ? 400 / k : 30 / (k * (dd + 6) * (dd + 6)); }
                    player.x = px; player.y = py;
                    let hk = null, ha = 0; try{ hk = SZM.hitKind; ha = SZM.hitAt; }catch(_){}
                    for(const [n, withNow] of pure){ try{ if(withNow ? window[n](G.VT) : window[n]()) s += 300 / k; }catch(_){} }
                    try{ SZM.hitKind = hk; SZM.hitAt = ha; }catch(_){}
                    player.x = ox; player.y = oy;
                    try{ if(isBlackHoleZone()){ const hd = Math.hypot(px - blackHole.cx, py - blackHole.cy) - blackHole.r - 4; s += hd < 0 ? 400 / k : 30 / (k * (hd + 6) * (hd + 6)); } }catch(_){}
                    if(tgt) s += 0.00006 * ((px - tgt[0]) ** 2 + (py - tgt[1]) ** 2);
                    else s += 0.00002 * ((px - CW * 0.5) ** 2 + (py - CH * 0.62) ** 2);
                }
                return s;
            };
            while(G.VT - startedAt < P.secs * 1000 && running){
                G.VT += P.step; frames++;
                if(elapsedMs >= nextDecide){
                    nextDecide = elapsedMs + 90 + br() * 80;
                    /* 노릴 보급 — 화면 안, 주울 수 있는 것 중 가장 가까운 것 (기체가 그 아래 90px 에 서면 원뿔에 든다) */
                    let tgt = null, bd = 1e9;
                    const fl = fuelLv();
                    for(const d of depots){ if(!pickable(d) || d.y < -10 || d.y > CH - 40) continue; let q = Math.hypot(d.x - player.x, d.y + 90 - player.y); if(d.item === 'fuel'){ if(fl > 0.7) continue; q *= 0.25 + fl; } if(q < bd){ bd = q; tgt = [d.x, Math.min(CH - 30, d.y + 90)]; } }
                    let best = Infinity;
                    if(br() > 0.04){ for(const d of DIRS){ const s = score(d, tgt) + br() * 0.002; if(s < best){ best = s; dir = d; } } }
                    for(const k of ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown']) keys[k] = false;
                    if(dir[0] < -0.1) keys.ArrowLeft = true; if(dir[0] > 0.1) keys.ArrowRight = true;
                    if(dir[1] < -0.1) keys.ArrowUp = true; if(dir[1] > 0.1) keys.ArrowDown = true;
                    /* BEAM — 주울 수 있는 캡슐이 원뿔 안이면 켜고, 없으면 끈다 */
                    let inCone = false;
                    for(const d of depots){ if(!pickable(d)) continue; const dx = d.x - player.x, dy = d.y - player.y, dl = Math.hypot(dx, dy); if(dl < 172 && dl > 8 && Math.abs(Math.atan2(dx, -dy)) < 0.72){ inCone = true; break; } }
                    try{ if(inCone && !gravityFieldActive) szBeamOn(false); else if(!inCone && gravityFieldActive) szBeamOff(); }catch(_){}
                    /* 아이템 */
                    const danger = best >= (lives <= 2 ? 120 : 200);
                    for(let i = 0; i < inventory.length; i++){
                        const it = inventory[i]; if(!it) continue;
                        if(NOW_USE[it] || (it === 'repair' && lives < MAXL)){ const n0 = inventory[i]; inventoryUseSlot(i); if(!inventory[i]) uses[n0] = (uses[n0] || 0) + 1; }
                    }
                    if(danger){
                        let used = false;
                        for(const want of DEF_ORDER){
                            const i = inventory.indexOf(want); if(i < 0) continue;
                            if(want === 'shield' && typeof shieldBubbleUntil !== 'undefined' && performance.now() < shieldBubbleUntil) continue;
                            inventoryUseSlot(i); if(!inventory[i]){ uses[want] = (uses[want] || 0) + 1; used = true; break; }
                        }
                        /* 위성 보상(호위 드론·플라즈마 폭풍)도 위험할 때 쓴다 */
                        if(!used && typeof rewardCounts !== 'undefined') for(const rk of ['drone', 'storm']){   /* 시간 왜곡은 뺀다 — 봇의 내다보기가 느려진 세계를 몰라 오히려 손해 */
                            if(rewardCounts[rk] > 0){ const c0 = rewardCounts[rk]; try{ activateRewardSlot(rk); }catch(_){} if(rewardCounts[rk] < c0){ uses['r_' + rk] = (uses['r_' + rk] || 0) + 1; break; } }
                        }
                    }
                }
                /* 위성 미션 — 새 미션마다 확률로 성공 여부를 정한다 */
                if(missionState === 'active'){
                    const key = missionZoneIdx + ':' + (typeof missionKind !== 'undefined' ? missionKind : 'main') + ':' + (typeof missionBuoyK !== 'undefined' ? missionBuoyK : 0);
                    if(key !== misKey){ misKey = key; const pw = (P.misPW != null && typeof szSatMiss !== 'undefined' && szSatMiss > 0) ? P.misPW : (P.misP != null ? P.misP : 0.8); misOk = bm() < pw; misAt = elapsedMs + 1500 + bm() * 4500; nMis++; if(misOk) nMisOk++; }
                    if(misOk && elapsedMs >= misAt) try{ completeMission(G.VT); }catch(_){}
                }
                try{ gameLoop(G.VT); }catch(e){ res.push({ err: String(e.message).slice(0, 160) }); running = false; break; }
                /* --no-tank — 탱커를 끝까지 안 먹는다(우연히 원뿔·드론에 걸려도): 떨어지자마자 화면 밖으로 치운다 */
                if(P.noTank) for(const d of depots) if(d.item === 'fuel' && !d.collected) d.y = CH + 100;
                if(lives < lv) lifeLost.push(Math.round(elapsedMs / 100) / 10); lv = lives;
                { const f = fuelLv(); if(f < fuelMin) fuelMin = f; moved += Math.hypot(player.x - mpx, player.y - mpy); mpx = player.x; mpy = player.y; }
                if(cutAt == null && typeof szSupplyCut !== 'undefined' && szSupplyCut) cutAt = Math.round(elapsedMs / 1000);
            }
            window.onDepotCollected = oPick;
            for(const k of ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown']) keys[k] = false;
            try{ if(gravityFieldActive) szBeamOff(); }catch(_){}
            let why = null; try{ why = dead ? deadKind || (SZM && SZM.hitKind) || null : null; }catch(_){}
            let hdrN = 0; try{ hdrN = SZP.hdrN; }catch(_){}
            const rec = { bs, t: Math.round(elapsedMs / 100) / 10, z: currentZoneIdx, dead, why, frames, lost: lifeLost, picks, uses, nMis, nMisOk, cutAt,
                fuelMin: Math.round(fuelMin * 100) / 100, hdrN, pxs: elapsedMs > 0 ? Math.round(moved / (elapsedMs / 1000)) : 0 };
            if(G.ibotPost) try{ G.ibotPost(P, bi, rec); }catch(_){}
            res.push(rec);
            running = false;
        }
        G.unsynth();
        window.drawFrame = oDraw; window.triggerGameOver = oOver;
        return res;
    };
    /* 소크 — 합성 시계, 무작위 입력(키·아이템·일시정지 없음), 무적 */
    G.soak = function(P){
        const errs = []; const heap = [];
        G.synth(); G.begin(P.seed || 777, false); window.__szFuelInf = 1;   /* 무적 소크 — 추진제도 무한 */
        startedAt = G.VT; lastFrame = G.VT;
        let nextIn = 0, nextHeap = 0, frames = 0; let s = 12345;
        const rnd = () => { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; };
        const K = ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'];
        while(G.VT - startedAt < P.secs * 1000 && running){
            G.VT += P.step; frames++; invincibleUntil = 1e15;
            if(elapsedMs >= nextIn){ nextIn = elapsedMs + 150 + rnd() * 400; for(const k of K) keys[k] = rnd() < 0.3;
                if(rnd() < 0.02 && missionState === 'active') try{ completeMission(G.VT); }catch(_){}
                if(rnd() < 0.01) try{ triggerWipe(); }catch(e){ errs.push('wipe ' + e.message); } }
            try{ gameLoop(G.VT); }catch(e){ errs.push(String(e && e.stack || e).split('\n').slice(0, 2).join(' | ').slice(0, 240)); if(errs.length > 20) break; }
            if(elapsedMs >= nextHeap){ nextHeap = elapsedMs + 30000; heap.push([Math.round(elapsedMs / 1000), performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : -1]); }
        }
        for(const k of K) keys[k] = false;
        running = false; G.unsynth(); window.__szFuelInf = 0;
        return { frames, errs, heap, E: (window.__E || []).slice(0, 8), endSec: Math.round(elapsedMs / 1000) };
    };
    /* ── MP0 hitpath — 무적을 끈 충돌 경로. det 는 매 스텝 무적(1e15)이라 피격 처리를 아예 안 탄다.
       P = {seed, step, secs, mode:'natural'|'inject', mr(Math.random 시드), lives, setup(선택: 시작 직후 평가할 식 — 패키지 시나리오용)}
       기록(해시 대상)은 감싼 함수·상태 관찰만으로 만든다 — SZE 같은 새 API 에 기대면 MP0 전후 기준선이 갈린다 */
    G.hitpath = function(P){
        const out = { errs: [] };
        const mbr = (s) => { let a = s | 0; return () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), a | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
        const mr0 = Math.random;
        if(P.mr) Math.random = mbr(P.mr);
        G.synth();
        G.begin(0, false, true);
        _setSeed(P.seed);
        window.__szFuelInf = 1;
        startedAt = G.VT; lastFrame = G.VT; lastSpawn = 0;
        invincibleUntil = 0;
        if(P.lives) lives = P.lives;
        const PX = 180, PY = 390;
        player.x = PX; player.y = PY;
        const EV = []; let over = null, nHit = 0;
        const oHit = window.szOnHit, oOver = window.triggerGameOver;
        window.szOnHit = function(now, x, y){ nHit++; EV.push(['h', Math.round(elapsedMs), lives, comboCount, R1(x), R1(y)]); return oHit.apply(this, arguments); };
        window.triggerGameOver = function(k){ if(over == null){ over = Math.round(elapsedMs); EV.push(['o', over, lives, String(k || '')]); } return oOver.apply(this, arguments); };
        if(P.setup) try{ (0, eval)(P.setup); }catch(e){ out.errs.push('setup ' + e.message); }
        let pc = comboCount, pl = lives, frames = 0, k = 0, nextInj = 3000;
        try{
            while(G.VT - startedAt < P.secs * 1000 && running){
                G.VT += P.step; frames++;
                player.x = PX; player.y = PY;
                if(P.mode === 'inject'){
                    lastSpawn = G.VT;   /* 자연 운석 스폰을 막는다(스폰 루프 조건이 바로 거짓) — 위험물 스케줄러는 그대로 */
                    if(elapsedMs >= nextInj){
                        nextInj += 1300;
                        /* 고정 궤적 — 황금각으로 방향을 돌리며 170px 밖에서 200px/s. 짝수 = 직격, 홀수 = 20px 비껴 스침 */
                        const a = k * 2.39996, cx = Math.cos(a), cy = Math.sin(a), off = (k % 2) ? 20 : 0;
                        bullets.push({ x: PX + cx * 170 - cy * off, y: PY + cy * 170 + cx * off, vx: -cx * 200, vy: -cy * 200, aimed: true, trail: [] });
                        k++;
                    }
                }
                gameLoop(G.VT);
                if(comboCount !== pc){ EV.push(['c', Math.round(elapsedMs), comboCount]); pc = comboCount; }
                if(lives !== pl){ EV.push(['l', Math.round(elapsedMs), lives]); pl = lives; }
            }
        }catch(e){ out.errs.push(String(e && e.stack || e).split('\n').slice(0, 2).join(' | ').slice(0, 240)); }
        window.szOnHit = oHit; window.triggerGameOver = oOver;
        running = false; G.unsynth(); window.__szFuelInf = 0; Math.random = mr0;
        Object.assign(out, { frames, nHit, over, livesEnd: lives, comboMax: comboMaxThisRun | 0, endZone: currentZoneIdx, endSec: Math.round(elapsedMs / 100) / 10,
            nEv: EV.length, ev: EV, E: (window.__E || []).slice(0, 8) });
        return out;
    };
    /* ── MP0 noshake — 합성 시계로 판을 돌리며 ② 캔버스 전체를 덮는 fillRect 시점의 변환 ③ 프레임 간 평균 휘도 증가를 잰다.
       폭탄(4s)·플라즈마 폭풍(9s)·피버(14s)·자연 피격(기체 고정, 목숨 99)을 일부러 건다. ① CSS transform 은 실시간 단계에서 따로 */
    G.noshake = function(P){
        const out = { errs: [] };
        const CP = CanvasRenderingContext2D.prototype, oFR = CP.fillRect;
        const bad = []; let nFull = 0;
        CP.fillRect = function(x, y, w, h){
            try{
                if(this === ctx && x <= 0.5 && y <= 0.5 && x + w >= CW - 0.5 && y + h >= CH - 0.5){
                    nFull++;
                    const t = this.getTransform();
                    if(Math.abs(t.b) > 1e-6 || Math.abs(t.c) > 1e-6 || Math.abs(t.e) > 0.01 || Math.abs(t.f) > 0.01){
                        if(bad.length < 20) bad.push([Math.round(elapsedMs), R2(t.a), R2(t.b), R2(t.c), R2(t.d), R2(t.e), R2(t.f), String((new Error().stack || '').split('\n')[2] || '').trim().slice(0, 90)]);
                    }
                }
            }catch(_){}
            return oFR.apply(this, arguments);
        };
        const sc = document.createElement('canvas'); sc.width = 24; sc.height = 40;
        const sx = sc.getContext('2d', { willReadFrequently: true });
        const lum = () => { sx.drawImage(canvas, 0, 0, 24, 40); const d = sx.getImageData(0, 0, 24, 40).data; let s = 0; for(let i = 0; i < d.length; i += 4) s += 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2]; return s / (d.length / 4); };
        G.synth();
        G.begin(P.seed || 424242, false, true);
        window.__szFuelInf = 1;
        startedAt = G.VT; lastFrame = G.VT; lastSpawn = 0; invincibleUntil = 0; lives = 99;
        const marks = [], fired = {};
        let prev = null, maxInc = 0, maxAt = null, frames = 0, feverSeen = false;
        const inc = [];
        try{
            while(G.VT - startedAt < (P.secs || 30) * 1000 && running){
                G.VT += P.step || 16.667; frames++;
                player.x = 180; player.y = 390; if(lives < 50) lives = 99;
                const e = elapsedMs;
                if(e >= 4000 && !fired.w){ fired.w = 1; marks.push(['wipe', Math.round(e)]); try{ triggerWipe(); }catch(err){ out.errs.push('wipe ' + err.message); } }
                if(e >= 9000 && !fired.s){ fired.s = 1; marks.push(['storm', Math.round(e)]); try{ _activatePlasmaStorm(G.VT); }catch(err){ out.errs.push('storm ' + err.message); } }
                if(e >= 14000 && !fired.f){ fired.f = 1; marks.push(['fever', Math.round(e)]); try{ szFeverAdd(100); }catch(err){ out.errs.push('fever ' + err.message); } }
                gameLoop(G.VT);
                if(typeof szFeverOn !== 'undefined' && szFeverOn) feverSeen = true;
                const L = lum();
                if(prev != null){ const d = L - prev; inc.push([d, Math.round(elapsedMs)]); if(d > maxInc){ maxInc = d; maxAt = Math.round(elapsedMs); } }
                prev = L;
            }
        }catch(err){ out.errs.push(String(err && err.stack || err).split('\n').slice(0, 2).join(' | ').slice(0, 240)); }
        CP.fillRect = oFR;
        running = false; G.unsynth(); window.__szFuelInf = 0;
        const near = (t) => { let b = 'hit/기타'; for(const m of marks) if(t != null && t >= m[1] && t - m[1] < 1500) b = m[0]; return b; };
        const top = inc.slice().sort((a, b) => b[0] - a[0]).slice(0, 6).map(([d, t]) => [R1(d), t, near(t)]);
        Object.assign(out, { frames, nFull, bad, maxInc: R1(maxInc), maxIncFrac: R2(maxInc / 255), maxAt, maxNear: near(maxAt), top, marks, feverSeen, E: (window.__E || []).slice(0, 8) });
        return out;
    };
    /* ── MP0 ibot 확장 고리 — 패키지가 PAGE_EXT 로 채운다(없으면 아무것도 안 함) */
    G.ibotPre = G.ibotPre || null;
    G.ibotPost = G.ibotPost || null;
    return 1;
}
const PAGE_LIB = '(' + pageLib.toString() + ')();' + PAGE_EXT.map(f => '(' + f.toString() + ')();').join('');
const gameUrl = (base, lang, extra = '') => base + '/games/dodge/?lang=' + lang + (extra ? '&' + extra : '');

/* ================= det ================= */
function detConfigs(){
    const S = [1000 / 60, 21, 1000 / 30];
    /* MP0 — 120Hz 기기(8.33ms) 를 기본 구성 둘에 더한다 */
    const S8 = S.concat([1000 / 120]);
    return [
        { mode: 'solo', mission: 'fail', bomb: false, steps: S8 },
        { mode: 'race', mission: 'fail', bomb: false, steps: S8 },
        { mode: 'solo', mission: 'success', bomb: false, steps: S.slice(0, 2) },
        { mode: 'solo', mission: 'fail', bomb: true, steps: S.slice(0, 2) },
        { mode: 'race', mission: 'success', bomb: true, steps: S.slice(0, 2) },
        /* P2 추가 — 히트스톱·TIME_WARP 를 건 판(스폰 시각 불변 확인), 1:1 PvP 호스트 */
        { mode: 'solo', mission: 'fail', bomb: false, fx: true, steps: [S[0], S[2]] },
        { mode: 'pvp', mission: 'fail', bomb: false, steps: S.slice(0, 2) },
    ];
}
const cfgKey = (c, st) => c.mode + '/' + c.mission + '/' + (c.bomb ? 'bomb' : 'nobomb') + (c.fx ? '/fx' : '') + '@' + st.toFixed(2);
/* det 한 판 → 비교 서명 (flags0 도 같은 식을 쓴다) */
function detSig(o, r){
    return {
        frames: o.frames, nR: o.nR, nH: o.nH, nD: o.nD, endZone: o.endZone, endSec: o.endSec, endReason: o.endReason, errs: o.errs.length,
        hH: sha(o.H.map(x => [x[1], x[2]])), hHaz: sha(o.haz.map(x => [x[0], x[1], x[2], x[3]])), hMet: sha(o.met), hMetGeo: sha(o.met.map(m => [r1(m[1]), r1(m[2]), r1(m[3]), r1(m[4])])),
        hDep: sha(Object.keys(o.dep).sort().map(k => [k, o.dep[k][0], o.dep[k][1]])), hBh: sha(o.bh), nHaz: o.haz.length, nMet: o.met.length, nDep: Object.keys(o.dep).length, nBh: o.bh.length,
        /* P2 — 프레임과 무관한 기록: 운석 스폰 목록(스폰 순간 좌표·논리시각)·위험물 사건(존·논리 ms·수열 소비 수) */
        hMetS: sha(o.metS || []), nMetS: (o.metS || []).length, nS: o.nS, hHz2: sha(o.hz2 || []), nHz2: (o.hz2 || []).length,
        flare0: o.flare0, flare0Seen: o.flare0Seen, step: r.step, mode: r.mode, nStop: o.nStop, nWarp: o.nWarp,
    };
}
const DET_CMP = ['nR', 'nH', 'nD', 'hH', 'hHaz', 'hMet', 'hDep', 'hBh'];
async function runDet(base, opt = {}){
    const runs = [];
    for(const c of detConfigs()) for(const st of (opt.firstOnly ? c.steps.slice(0, 1) : c.steps)) runs.push({ ...c, step: st, key: cfgKey(c, st) });
    say((opt.tag || 'det') + ': ' + runs.length + '회 × ' + DET_SECS + 's 합성 시간, 병렬 ' + JOBS + (opt.extra ? ' · ?' + opt.extra : ''));
    const results = await pool(runs, JOBS, async (r) => withEdge({ w: 412, h: 915, dsf: 2.625, mobile: true }, async (e) => {
        await e.open(gameUrl(base, 'ko', opt.extra || ''), 1500);
        const t0 = Date.now();
        const out = await e.ev('__G.det(' + JSON.stringify({ seed: 424242, racing: r.mode === 'race', pvp: r.mode === 'pvp', fx: !!r.fx, step: r.step, secs: DET_SECS, mission: r.mission, bomb: r.bomb, nMet: 400, nMetS: 1500, noDraw: !!A['det-nodraw'] }) + ')', 900000);
        const pe = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs((opt.tag || 'det') + ' ' + r.key, e, pe.concat(out.errs));
        log('det', r.key, 'frames', out.frames, 'wall', Date.now() - t0, 'rand', out.nR, 'randH', out.nH, 'randD', out.nD, 'end', out.endZone, out.endSec, out.endReason);
        return { ...r, out };
    }));
    const M = {};
    for(const r of results){
        M[r.key] = detSig(r.out, r);
        M[r.key]._raw = r.out;
    }
    if(opt.firstOnly){ for(const k of Object.keys(M)) delete M[k]._raw; return { secs: DET_SECS, runs: M }; }
    /* 스폰 목록 비교 — 같은 인덱스끼리 논리시각·좌표·속도가 모두 같아야 한다(허용 0.01) */
    const metSDiff = (a, b, fromMs) => {
        const A2 = (a.metS || []).filter(m => m[0] >= (fromMs || 0)), B2 = (b.metS || []).filter(m => m[0] >= (fromMs || 0));
        const n = Math.min(A2.length, B2.length); let mis = 0, first = -1;
        for(let i = 0; i < n; i++){ const p = A2[i], s = B2[i]; if(p[0] !== s[0] || Math.abs(p[1] - s[1]) > 0.011 || Math.abs(p[2] - s[2]) > 0.011 || Math.abs(p[3] - s[3]) > 0.011 || Math.abs(p[4] - s[4]) > 0.011){ mis++; if(first < 0) first = i; } }
        return { n, mis, first, lenA: A2.length, lenB: B2.length };
    };
    const hz2Diff = (a, b) => {
        const x = a.hz2 || [], y = b.hz2 || []; let mis = 0, first = -1;
        for(let i = 0; i < Math.max(x.length, y.length); i++){ const p = x[i], s = y[i]; if(!p || !s || p[0] !== s[0] || p[1] !== s[1] || p[2] !== s[2] || p[3] !== s[3]){ mis++; if(first < 0) first = i; } }
        return { n: Math.max(x.length, y.length), mis, first };
    };
    /* 교차 비교 */
    const X = {};
    for(const c of detConfigs()){
        const A0 = M[cfgKey(c, c.steps[0])];
        for(const st of c.steps.slice(1)){
            const B = M[cfgKey(c, st)]; const a = A0._raw, b = B._raw;
            /* 짝짓기는 순서에 느슨하게(2026-09-28 통합): 33ms 에선 서로 다른 논리 시각의 운석(협곡 줄 + 일반 운석)이 한 프레임에
               함께 처음 관측돼 목록 순서가 16.67ms 와 달라질 수 있다 → 같은 인덱스끼리 짝지으면 오탐(249px).
               각 운석을 인덱스 ±8 안의 미사용 운석 중 '속도가 같은 것 우선, 그다음 좌표 거리 + 0.1×관측 시각차(ms)' 가 가장 작은 것과 짝짓는다.
               관측 시각은 창이 아니라 가중치로만 쓴다(fx 모드는 히트스톱 때문에 첫 관측 시각이 프레임률마다 수십 ms 어긋난다).
               같은 x 열이 반복되는 협곡 줄끼리 엇갈려 짝지어지지 않게 하는 게 시각 가중치의 몫. 짝 없는 운석은 999px */
            const n = Math.min(a.met.length, b.met.length); let maxPos = 0, velDiff = 0;
            const usedB = new Uint8Array(b.met.length), WIN = 8;
            for(let i = 0; i < n - WIN; i++){   /* 목록 끝(관측 상한 400) 근처는 짝이 목록 밖에 있을 수 있어 제외 */
                const p = a.met[i]; let bj = -1, bc = 1e18, bd = 0;
                for(let j = Math.max(0, i - WIN); j <= Math.min(b.met.length - 1, i + WIN); j++){
                    if(usedB[j]) continue; const s = b.met[j];
                    const dd = Math.hypot(p[1] - s[1], p[2] - s[2]), vd = Math.hypot(p[3] - s[3], p[4] - s[4]) > 0.5 ? 1 : 0;
                    const cost = vd * 1e6 + dd + 0.1 * Math.abs(s[0] - p[0]); if(cost < bc){ bc = cost; bj = j; bd = dd; }
                }
                if(bj < 0 || bd > 60){ maxPos = Math.max(maxPos, 999); continue; }
                usedB[bj] = 1; const s = b.met[bj];
                maxPos = Math.max(maxPos, bd); if(Math.hypot(p[3] - s[3], p[4] - s[4]) > 0.5) velDiff++;
            }
            let hMis = -1, drift = 0; for(let i = 0; i < Math.min(a.H.length, b.H.length); i++){ if(hMis < 0 && a.H[i][2] !== b.H[i][2]) hMis = i; drift = Math.max(drift, Math.abs(a.H[i][0] - b.H[i][0])); }
            let hazMis = 0, hazDrift = 0; for(let i = 0; i < Math.max(a.haz.length, b.haz.length); i++){ const p = a.haz[i], s = b.haz[i]; if(!p || !s || p[0] !== s[0] || p[1] !== s[1] || p[2] !== s[2]) hazMis++; else hazDrift = Math.max(hazDrift, Math.abs(p[4] - s[4])); }
            let depMis = 0, depMax = 0; const keys = new Set(Object.keys(a.dep).concat(Object.keys(b.dep)));
            for(const k of keys){ const p = a.dep[k], s = b.dep[k]; if(!p || !s){ depMis++; continue; } const d = Math.hypot(p[0] - s[0], p[1] - s[1]); depMax = Math.max(depMax, d); if(d > 1.5) depMis++; }
            X[cfgKey(c, c.steps[0]) + ' vs ' + st.toFixed(2)] = { countsEq: a.nR === b.nR && a.nH === b.nH && a.nD === b.nD, counts: [[a.nR, b.nR], [a.nH, b.nH], [a.nD, b.nD]], metN: n, metMaxPos: r1(maxPos), metVelDiff: velDiff,
                hFirstMismatch: hMis, hDriftMs: drift, hazMismatch: hazMis, hazDriftMs: hazDrift, depMismatch: depMis, depMaxPx: r1(depMax),
                metS: metSDiff(a, b), hz2: hz2Diff(a, b) };
        }
    }
    /* 미션 성패·폭탄과 무관해야 하는 것 */
    const pairDiff = (ka, kb) => {
        const a = M[ka]._raw, b = M[kb]._raw;
        let depMis = 0, depCommon = 0; for(const k of Object.keys(a.dep)){ if(!b.dep[k]) continue; depCommon++; if(Math.hypot(a.dep[k][0] - b.dep[k][0], a.dep[k][1] - b.dep[k][1]) > 1.5) depMis++; }
        let hMis = 0; for(let i = 0; i < Math.min(a.H.length, b.H.length); i++) if(a.H[i][2] !== b.H[i][2] || a.H[i][1] !== b.H[i][1]) hMis++;
        let hazMis = 0; for(let i = 0; i < Math.max(a.haz.length, b.haz.length); i++){ const p = a.haz[i], s = b.haz[i]; if(!p || !s || p[0] !== s[0] || p[1] !== s[1]) hazMis++; }
        let metMis = 0; const n = Math.min(a.met.length, b.met.length); for(let i = 0; i < n; i++){ const p = a.met[i], s = b.met[i]; if(Math.hypot(p[3] - s[3], p[4] - s[4]) > 0.5) metMis++; }
        /* P2 — 스폰 목록이 있으면 그걸로 센다(폭탄으로 바로 지운 운석은 화면 관측 목록에 안 잡혀 인덱스가 밀린다) */
        if(a.metS && b.metS && a.metS.length && b.metS.length){ metMis = 0; const m2 = Math.min(400, a.metS.length, b.metS.length); for(let i = 0; i < m2; i++){ const p = a.metS[i], s = b.metS[i]; if(Math.hypot(p[3] - s[3], p[4] - s[4]) > 0.5) metMis++; } }
        return { depCommon, depOnlyA: Object.keys(a.dep).filter(k => !b.dep[k]).length, depOnlyB: Object.keys(b.dep).filter(k => !a.dep[k]).length, depMis, hMis, hazMis, metVelMis: metMis,
            metS: metSDiff(a, b), metS5: metSDiff(a, b, 45000), hz2: hz2Diff(a, b) };
    };
    const s0 = 1000 / 60;
    X['mission fail vs success (solo)'] = pairDiff(cfgKey({ mode: 'solo', mission: 'fail', bomb: false }, s0), cfgKey({ mode: 'solo', mission: 'success', bomb: false }, s0));
    X['nobomb vs bomb (solo)'] = pairDiff(cfgKey({ mode: 'solo', mission: 'fail', bomb: false }, s0), cfgKey({ mode: 'solo', mission: 'fail', bomb: true }, s0));
    X['race fail/nobomb vs success/bomb'] = pairDiff(cfgKey({ mode: 'race', mission: 'fail', bomb: false }, s0), cfgKey({ mode: 'race', mission: 'success', bomb: true }, s0));
    /* P2 — 히트스톱·TIME_WARP 와 무관, 1:1 PvP 호스트 */
    const fxK = cfgKey({ mode: 'solo', mission: 'fail', bomb: false, fx: true }, s0);
    if(M[fxK]) X['plain vs hitstop/warp (solo)'] = pairDiff(cfgKey({ mode: 'solo', mission: 'fail', bomb: false }, s0), fxK);
    /* 전 구성 위험물 사건 목록(존·논리 ms·수열 소비 수) — 1:1 PvP 는 위험물을 끈다 */
    const hzH = {}; for(const [k, m] of Object.entries(M)){ if(m.mode === 'pvp') continue; (hzH[m.hHz2] = hzH[m.hHz2] || []).push(k); }
    const flare = Object.entries(M).filter(([k, m]) => m.mode !== 'pvp').map(([k, m]) => ({ k, ft: m.flare0, seen: m.flare0Seen, step: m.step }));
    for(const k of Object.keys(M)) delete M[k]._raw;
    return { secs: DET_SECS, runs: M, cross: X, hzGroups: hzH, flare };
}
function judgeDet(cur, base){
    const B = base && base.secs === cur.secs ? base : null;
    if(base && !B) row('G1 det', '기준선 조건', cur.secs + 's', base.secs + 's', '같아야 비교', 'WARN', '기준선과 --secs 가 달라 해시 비교 생략');
    for(const [k, m] of Object.entries(cur.runs)){
        if(m.errs) row('G1 det', k + ' 에러', m.errs, 0, '0', 'FAIL');
        if(!B || !B.runs[k]){ row('G1 det', k + ' 해시', m.hH + '/' + m.hHaz + '/' + m.hMet, null, '기준선 없음', 'INFO'); continue; }
        const b = B.runs[k];
        const parts = DET_CMP.filter(p => m[p] !== b[p]);
        /* MP0 — 호출 수는 따로 한 줄 (패키지 수용 기준: nR·nH·nD 동일) */
        const cnt = ['nR', 'nH', 'nD'].filter(p => m[p] !== b[p]);
        row('G1 det', k + ' 호출 수 nR/nH/nD', m.nR + '/' + m.nH + '/' + m.nD, b.nR + '/' + b.nH + '/' + b.nD, '기준선과 같음', cnt.length ? (A['allow-det-change'] ? 'WARN' : 'FAIL') : 'PASS');
        const st = parts.length === 0 ? 'PASS' : (A['allow-det-change'] ? 'WARN' : 'FAIL');
        row('G1 det', k + ' 기준선 일치', parts.length ? '다름: ' + parts.join(',') : '동일', '', '완전 일치', st, parts.length ? parts.map(p => p + ' ' + m[p] + '≠' + b[p]).join(' ').slice(0, 160) : '');
    }
    for(const [k, x] of Object.entries(cur.cross)){
        const b = B && B.cross[k];
        if(k.includes(' vs ') && x.countsEq !== undefined){
            row('G1 det', k + ' 호출 수', x.countsEq ? '같음' : JSON.stringify(x.counts), b ? (b.countsEq ? '같음' : JSON.stringify(b.counts)) : null, 'rand/randH/randD 같음', x.countsEq ? 'PASS' : 'FAIL');
            row('G1 det', k + ' randH 순서', x.hFirstMismatch < 0 ? '같음' : '#' + x.hFirstMismatch + ' 어긋남', b ? (b.hFirstMismatch < 0 ? '같음' : '#' + b.hFirstMismatch) : null, '같음', x.hFirstMismatch < 0 ? 'PASS' : 'FAIL');
            const dl = Math.max(b ? b.hDriftMs : 0, 50) + 5;
            row('G1 det', k + ' randH 시각차', x.hDriftMs + 'ms', b ? b.hDriftMs + 'ms' : null, '≤' + dl + 'ms', x.hDriftMs <= dl ? 'PASS' : 'FAIL');
            row('G1 det', k + ' 위험물 목록', x.hazMismatch + '건 다름', b ? b.hazMismatch + '건' : null, '≤ 기준선', !b ? (x.hazMismatch ? 'WARN' : 'PASS') : (x.hazMismatch <= b.hazMismatch ? 'PASS' : 'FAIL'));
            const pl = (b ? b.metMaxPos : 0) + 0.6;
            row('G1 det', k + ' 운석 좌표차', x.metMaxPos + 'px/속도차 ' + x.metVelDiff, b ? b.metMaxPos + 'px/' + b.metVelDiff : null, '좌표≤' + r1(pl) + ' 속도차≤기준', !b ? 'INFO' : ((x.metMaxPos <= pl && x.metVelDiff <= b.metVelDiff) ? 'PASS' : 'FAIL'));
            row('G1 det', k + ' 보급 좌표', x.depMismatch + '건/최대 ' + x.depMaxPx + 'px', b ? b.depMismatch + '건' : null, '≤ 기준선', !b ? 'INFO' : (x.depMismatch <= b.depMismatch ? 'PASS' : 'FAIL'));
        } else {
            const worse = b ? ['depMis', 'hMis', 'hazMis', 'metVelMis'].filter(f => x[f] > b[f]) : [];
            row('G1 det', k, 'dep ' + x.depMis + '/' + x.depCommon + ' 누락 ' + x.depOnlyA + '·' + x.depOnlyB + ' H ' + x.hMis + ' haz ' + x.hazMis + ' met ' + x.metVelMis,
                b ? 'dep ' + b.depMis + ' H ' + b.hMis + ' haz ' + b.hazMis + ' met ' + b.metVelMis : null, '각 항목 ≤ 기준선 (목표 0)', worse.length ? 'FAIL' : ((x.depMis + x.hMis + x.hazMis + x.metVelMis) ? 'WARN' : 'PASS'), worse.length ? '악화: ' + worse.join(',') : '');
        }
        /* P2 — 프레임과 무관한 목록(스폰 순간 기록)은 완전히 같아야 한다 */
        if(x.metS){
            const s = x.metS, bad = s.mis || s.lenA !== s.lenB;
            row('G1 det', k + ' 운석 스폰 목록', s.mis + '/' + s.n + ' 다름' + (s.lenA !== s.lenB ? ' (길이 ' + s.lenA + '·' + s.lenB + ')' : ''), null, '0 (시각·좌표·속도)', bad ? 'FAIL' : 'PASS', s.first >= 0 ? '첫 차이 #' + s.first : '');
        }
        if(x.metS5) row('G1 det', k + ' 운석 스폰 목록 45s 이후', x.metS5.mis + '/' + x.metS5.n + ' 다름', null, '0', x.metS5.mis ? 'FAIL' : 'PASS');
        if(x.hz2) row('G1 det', k + ' 위험물 사건', x.hz2.mis + '/' + x.hz2.n + ' 다름', null, '0 (종류·존·논리ms·소비 수)', x.hz2.mis ? 'FAIL' : 'PASS', x.hz2.first >= 0 ? '첫 차이 #' + x.hz2.first : '');
    }
    if(cur.hzGroups){
        const g = Object.values(cur.hzGroups);
        row('G1 det', '위험물 목록 전 구성 동일(솔로·레이스 × 성패 × 폭탄 × 프레임 × 히트스톱)', g.length === 1 ? '같음 (' + g[0].length + '구성)' : g.length + '갈래', null, '1갈래', g.length === 1 ? 'PASS' : 'FAIL', g.length > 1 ? g.map(x => x.join('|')).join(' ≠ ').slice(0, 200) : '');
    }
    for(const f of (cur.flare || [])){
        const ok = f.ft === 10000 && f.seen != null && f.seen >= 10000 && f.seen <= 10000 + f.step + 1;
        row('G1 det', f.k + ' 존0 첫 플레어', 'ft ' + f.ft + ' / 관측 ' + f.seen + 'ms', null, '10000 (+1프레임)', ok ? 'PASS' : 'FAIL');
    }
}

/* ================= perf / sweep ================= */
async function runPerf(base, zones, tag){
    const out = {};
    for(const rate of [1, 4]){
        const segs = [];
        for(const z of zones){
            let r;
            try{ r = await withEdge({ w: 412, h: 915, dsf: 2.625, mobile: true }, async (e) => {
                await e.open(gameUrl(base, 'ko'), 2200);
                await e.send('Emulation.setCPUThrottlingRate', { rate });
                await e.ev('__G.perfStart({seed:424242, tier:0})');
                await sleep(z === 0 ? 300 : 600);
                await e.ev('__G.perfJump(' + z + ')');
                await sleep(z === 0 ? 2500 : 2300);
                await e.ev('__G.forceMission()');
                await sleep(1800);
                const c = await e.ev('__G.perfCollect()');
                collectErrs(tag + ' ' + rate + 'x z' + z, e, c.E);
                return c;
            }); }catch(err){ row('G2 ' + tag, rate + 'x z' + z + ' 구간 실패', String(err.message).slice(0, 80), null, '', 'WARN', '이 구간은 통계에서 빠짐'); continue; }
            log(tag, rate + 'x', 'z' + z, 'n', r.n, 'iv50', r1(r.iv50), 'p95', r1(q(r.steady.slice().sort((a, b) => a - b), 0.95)), 'zone', r.zoneJs.map(r1), 'act', r.actJs.map(r1), 'lt', r.lt50);
            segs.push({ z, ...r });
        }
        const all = segs.flatMap(s => s.steady).sort((a, b) => a - b);
        const perZone = {}; for(const s of segs){ const st = s.steady.slice().sort((a, b) => a - b); perZone[s.z] = { p95: r2(q(st, 0.95)), zone: r2(Math.max(0, ...s.zoneJs)), act: r2(Math.max(0, ...s.actJs)), iv50: r1(s.iv50), n: s.n }; }
        out[rate + 'x'] = { frames: all.length, p50: r2(q(all, 0.5)), p95: r2(q(all, 0.95)), p99: r2(q(all, 0.99)), max: r2(all[all.length - 1]),
            zoneMax: r2(Math.max(0, ...segs.flatMap(s => s.zoneJs))), actMax: r2(Math.max(0, ...segs.flatMap(s => s.actJs))),
            zoneMed: r2(q(segs.flatMap(s => s.zoneJs).sort((a, b) => a - b), 0.5) || 0), actMed: r2(q(segs.flatMap(s => s.actJs).sort((a, b) => a - b), 0.5) || 0),
            longTasks50: segs.reduce((n, s) => n + s.lt50, 0), iv50: r1(q(segs.map(s => s.iv50).filter(Boolean).sort((a, b) => a - b), 0.5)), zones, perZone };
        say(tag + ' ' + rate + 'x: p50 ' + out[rate + 'x'].p50 + ' p95 ' + out[rate + 'x'].p95 + ' p99 ' + out[rate + 'x'].p99 + ' 존전환 ' + out[rate + 'x'].zoneMax + ' 미션 ' + out[rate + 'x'].actMax + ' 롱태스크 ' + out[rate + 'x'].longTasks50);
    }
    return out;
}
function judgePerf(cur, base, tag){
    const G = tag === 'sweep' ? 'G2 sweep' : 'G2 perf';
    const SPEC = { '1x': { p95: 3 }, '4x': { p95: 10, zone: 25, act: 20 } };
    for(const rk of ['1x', '4x']){
        const c = cur[rk], b = base && base[rk] && JSON.stringify(base[rk].zones) === JSON.stringify(c.zones) ? base[rk] : null;
        if(base && base[rk] && !b) row(G, rk + ' 기준선 조건', c.zones.join(','), base[rk].zones.join(','), '같은 존 목록', 'WARN', '존 목록이 달라 비교 생략');
        const lim = (bv, mul, add) => bv == null ? null : r2(bv * mul + add);
        const chk = (name, v, bv, mul, add, spec) => {
            const L = lim(bv, mul, add);
            const st = L == null ? 'INFO' : (v <= L ? 'PASS' : 'FAIL');
            row(G, rk + ' ' + name, v + 'ms', bv == null ? null : bv + 'ms', L == null ? '-' : '≤' + L + 'ms' + (spec ? ' (목표 ' + spec + ')' : ''), st, spec && v > spec ? '스펙 목표 미달(P1 과제)' : '');
        };
        chk('p50', c.p50, b && b.p50, 1.25, 0.4);
        chk('p95', c.p95, b && b.p95, 1.25, 0.8, SPEC[rk].p95);
        chk('p99', c.p99, b && b.p99, 1.35, 2);
        /* 한 프레임 최대값은 headless 에서 2배까지 흔들린다 — 회귀 판정은 중앙값, 최대값은 스펙 목표 대비 참고 */
        chk('존 전환 프레임 중앙값', c.zoneMed, b && b.zoneMed, 1.35, 4);
        chk('미션 활성 프레임 중앙값', c.actMed, b && b.actMed, 1.35, 4);
        row(G, rk + ' 존 전환·미션 최대 (참고)', c.zoneMax + ' / ' + c.actMax + 'ms', b ? b.zoneMax + ' / ' + b.actMax + 'ms' : null, SPEC[rk].zone ? '목표 ≤' + SPEC[rk].zone + ' / ≤' + SPEC[rk].act : '-', 'INFO', SPEC[rk].zone && (c.zoneMax > SPEC[rk].zone || c.actMax > SPEC[rk].act) ? '스펙 목표 미달(P1 과제)' : '');
        const ltL = b ? Math.round(b.longTasks50 * 1.5 + 3) : null;
        row(G, rk + ' 롱태스크>50ms', c.longTasks50, b ? b.longTasks50 : null, b ? '≤' + ltL : '-', b ? (c.longTasks50 <= ltL ? 'PASS' : 'FAIL') : 'INFO', 'G2 목표는 0');
        if(c.iv50 && rk === '1x' && c.iv50 > 25) row(G, rk + ' rAF 간격', c.iv50 + 'ms', null, '≈16.7', 'WARN', 'headless rAF 저하 의심 — 수치 신뢰도 낮음');
    }
}

/* ================= layout ================= */
const SIZES_FULL = [[320, 568, 2], [360, 640, 3], [375, 667, 2], [375, 812, 3], [412, 915, 2.625], [740, 360, 3], [768, 1024, 2], [1280, 800, 1], [1366, 768, 1]];
const SIZES_QUICK = [[320, 568, 2], [375, 667, 2], [740, 360, 3], [1280, 800, 1]];
async function runLayout(base){
    const langs = String(A['layout-langs'] || 'ko,en').split(',');
    const sizes = QUICK ? SIZES_QUICK : SIZES_FULL;
    const jobs = [];
    for(const L of langs) for(const s of sizes) jobs.push({ L, w: s[0], h: s[1], dsf: s[2] });
    say('layout: ' + jobs.length + '개 (언어 ' + langs.join('/') + ') → 스크린샷 ' + path.join(OUT, 'layout'));
    const res = await pool(jobs, JOBS, async (j) => withEdge({ w: j.w, h: j.h, dsf: j.dsf, mobile: j.w < 900 }, async (e) => {
        const key = j.L + ' ' + j.w + 'x' + j.h, fn = (st) => path.join(OUT, 'layout', j.L + '_' + j.w + 'x' + j.h + '_' + st + '.png');
        await e.open(gameUrl(base, j.L), 2200);
        /* --layout-ctl classic|float — 조작 방식 고정 (기본: 페이지 기본값 = 세로 터치는 플로팅) */
        if(A['layout-ctl']){ await e.ev(`localStorage.setItem('szx_ctl', ${JSON.stringify(String(A['layout-ctl']))}); 1`); await e.open(gameUrl(base, j.L), 2200); }
        await e.ev('__G.hookText()');
        const o = {};
        o.start = await e.ev('__G.layout()'); await e.shot(fn('start'));
        /* 실제 시작 경로(인트로 포함) */
        /* 인트로 이야기는 무작위 — 가장 긴 이야기를 고정으로 골라 최악의 경우를 본다(재현 가능) */
        const startExpr = `(function(){ const mr = Math.random; let v = 0.999;
            try{ const L = (window.LpI18n && LpI18n.getLang && LpI18n.getLang()) || 'en'; const S = INTRO_STORIES[L] || INTRO_STORIES.en;
                 let bi = 0, bl = -1; S.forEach(function(x, i){ const l = [].concat(x).join('').length; if(l > bl){ bl = l; bi = i; } }); v = (bi + 0.5) / S.length; }catch(_){}
            Math.random = function(){ return v; };
            try{ startGame(); } finally { Math.random = mr; }
            if(!window.__inv) window.__inv = setInterval(function(){ invincibleUntil = 1e15; }, 100); return 1; })()`;
        await e.ev(startExpr);
        /* 드물게 첫 호출이 먹지 않는다(부팅 직후 경합) — 인트로가 시작됐는지 확인하고 한 번 더 */
        for(let i = 0; i < 24; i++){ if(await e.ev('!!((typeof _introRunning !== "undefined" && _introRunning) || running)')) break; await sleep(150); if(i === 12) await e.ev(startExpr); }
        await sleep(1200);
        o.intro = await e.ev('__G.layout()'); await e.shot(fn('intro'));
        await sleep(3200);
        await e.ev('(function(){ var z = 1; startedAt = performance.now() - (ZONES[z].s * 1000 + 400) - totalPausedMs; return 1; })()');
        await sleep(700);
        await e.ev('__G.forceMission()');
        await sleep(900);
        o.play = await e.ev('__G.layout()'); await e.shot(fn('play'));
        await e.ev('(function(){ clearInterval(window.__inv); invincibleUntil = 0; try{ triggerGameOver(); }catch(e){ (window.__E=window.__E||[]).push("gameover "+e.message); } return 1; })()');
        await sleep(1800);
        o.result = await e.ev('__G.layout()'); await e.shot(fn('result'));
        const pe = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs('layout ' + key, e, pe);
        return { key, o };
    }));
    const out = {};
    for(const r of res) out[r.key] = r.o;
    return out;
}
/* 배치 비교 — 숨 쉬는 애니메이션(.sz-pilot)은 빼고, 3px 이내 흔들림은 같다고 본다 */
function sameGeo(R, B){
    const keys = new Set([...Object.keys(R || {}), ...Object.keys(B || {})]); keys.delete('.sz-pilot');
    for(const k of keys){ const x = R[k], y = B[k]; if(!x || !y) return false; for(let i = 0; i < 4; i++) if(Math.abs(x[i] - y[i]) > 3) return false; }
    return true;
}
/* 선체에 칠한 장식 글자 — 읽는 글이 아니라 무늬라 크기 검사에서 뺀다 (기존 'SPACEX' 6px 자리) */
const DECOR_TEXT = new Set(['LUCKY-1']);
let SMALL_BASE = new Set();
function judgeLayout(cur, base){
    SMALL_BASE = new Set();
    if(base) for(const st of Object.values(base)) for(const m of Object.values(st)) for(const x of (m.smallText || [])) SMALL_BASE.add(x.replace(/@[\d.]+$/, ''));
    const G = 'G3 layout';
    let geoChanged = 0;
    for(const [k, states] of Object.entries(cur)){
        const bs = base && base[k];
        for(const [st, m] of Object.entries(states)){
            const b = bs && bs[st];
            const id = k + ' ' + st;
            if(m.hScroll > 1) row(G, id + ' 가로 스크롤', m.hScroll + 'px', b ? b.hScroll + 'px' : null, '0', 'FAIL');
            const newOf = (arr, barr) => arr.filter(x => !(barr || []).some(y => y.split(' ')[0] === x.split(' ')[0]));
            const nClip = newOf(m.clip, b && b.clip), nSmall = newOf(m.small, b && b.small), nOv = m.overlap.filter(x => !(b && b.overlap || []).includes(x));
            if(m.clip.length) pre(row(G, id + ' 잘림', m.clip.join(' | ').slice(0, 120), b ? (b.clip.join(' | ').slice(0, 60) || '없음') : null, '새로 생긴 잘림 0', nClip.length || !b ? (b ? 'FAIL' : 'WARN') : 'WARN'), b && !nClip.length);
            if(m.small.length) pre(row(G, id + ' 버튼<44px', m.small.join(' | ').slice(0, 120), b ? (b.small.join(' | ').slice(0, 60) || '없음') : null, '새 위반 0 (목표 전부 ≥44)', nSmall.length && b ? 'FAIL' : 'WARN'), b && !nSmall.length);
            if(m.overlap.length) pre(row(G, id + ' 겹침', m.overlap.join(' ').slice(0, 120), b ? (b.overlap.join(' ') || '없음') : null, '새 겹침 0', nOv.length && b ? 'FAIL' : 'WARN'), b && !nOv.length);
            if(base){
                /* 기준선 어디에도 없던 9px 미만 글자만 회귀로 본다 (타이밍에 따라 그려지는 글자가 달라 전체 집합과 비교) */
                const nw = (m.smallText || []).filter(x => { const t = x.replace(/@[\d.]+$/, ''); return !SMALL_BASE.has(t) && !DECOR_TEXT.has(t); });
                if(nw.length) row(G, id + ' 새 캔버스 글자<9px', nw.slice(0, 4).join(' | '), null, '0 (G3: ≥9 CSS px)', 'FAIL');
            }
            if(b && !sameGeo(m.rects, b.rects)) geoChanged++;
            /* E (2026-09-29) — 조종판·키 가이드 × 캔버스 겹침 0px (PC) */
            if(m.cov) for(const [s, px] of Object.entries(m.cov)) if(!(m.float && s === '.control-row')) if(px > 0 || (st === 'play' && m.vw >= 1024)) row(G, id + ' ' + s + '×캔버스 겹침', px + 'px', b && b.cov && b.cov[s] != null ? b.cov[s] + 'px' : null, '0px', px > 0 ? 'FAIL' : 'PASS');
            /* E — 세로 폰에서 캔버스가 눌리지 않게: 표시 세로/가로 ≥ 1.0 (목표 1.1) */
            if(st === 'play' && m.vw < 900 && m.vh > m.vw && m.rects['#dodge-canvas']){
                const c = m.rects['#dodge-canvas'], a = c[3] / c[2], bc = b && b.rects && b.rects['#dodge-canvas'];
                row(G, id + ' 캔버스 세로/가로', a.toFixed(2), bc ? (bc[3] / bc[2]).toFixed(2) : null, '≥1.0 (목표 1.1)', a >= 1.0 ? 'PASS' : 'FAIL');
            }
            /* SZF — 플로팅 조작: 떠 있는 버튼 ≥48px · 캔버스 3:5 그대로(±2%) */
            if(st === 'play' && m.float){
                const c = m.rects['#dodge-canvas'], ar = c ? c[3] / c[2] : 0;
                const bad = (m.fbtn || []).filter(x => { const [w, h] = x.split(' ')[1].split('x').map(Number); return Math.min(w, h) < 48; });
                row(G, id + ' 플로팅 조작 버튼≥48 · 캔버스 3:5', (m.fbtn || []).join(' | ') + ' · ' + ar.toFixed(3), null, '≥48px · 1.667±2%', bad.length || Math.abs(ar - 5 / 3) > 0.034 ? 'FAIL' : 'PASS');
            }
            /* E — 결과 카드가 떠 있으면 HUD 줄(.score-strip)은 숨긴다 (카드 글자를 가렸다) */
            if(st === 'result') row(G, id + ' 결과 카드 위 HUD 줄', m.rects['.score-strip'] ? '보임' : '숨김', b ? (b.rects['.score-strip'] ? '보임' : '숨김') : null, '숨김', m.rects['.score-strip'] ? 'FAIL' : 'PASS');
            /* 미션 중 SAT·BEAM 두 버튼이 모두 보이고 44px 이상 (2026-09-29 SAT 숨김 사고 재발 방지) */
            if(st === 'play'){
                const bad = (m.missing || []).concat((m.small || []).filter(x => /^#(satBtn|gravBtn) /.test(x)));
                row(G, id + ' 미션 중 SAT·BEAM 버튼 (' + (m.mission || '?') + ')', bad.length ? bad.join(' | ') : ['#satBtn', '#gravBtn'].map(s => m.rects[s] ? m.rects[s][2] + 'x' + m.rects[s][3] : '-').join(' / '), null, '둘 다 보임 · ≥44px', bad.length || m.mission !== 'active' ? 'FAIL' : 'PASS');
            }
        }
        if(k.endsWith('360x640') && states.result){
            const ov = states.result.rects['#ovBtn'];
            const ok = ov && ov[1] + ov[3] <= states.result.vh + 1;
            row(G, k + ' 결과 화면 다시하기 보임', ov ? ov.join(',') : '안 보임', null, '스크롤 없이 보임', ok ? 'PASS' : 'WARN', ok ? '' : 'G3 목표 — 현재 미달이면 P5 과제');
        }
    }
    const n = Object.keys(cur).length;
    row(G, '해상도×언어 ' + n + '개 요약', '가로스크롤·새 잘림·새 겹침 위 목록 외 없음', null, '', ROWS.some(r => r.gate === G && r.status === 'FAIL') ? 'FAIL' : 'PASS');
    if(base) row(G, 'DOM 배치 기준선 대비', geoChanged ? geoChanged + '개 상태에서 좌표 변화' : '동일', null, 'UI 패키지 외엔 동일', geoChanged ? 'WARN' : 'PASS', geoChanged ? '의도한 UI 변경인지 스크린샷으로 확인' : '');
}

/* ================= 정적 분석 (주석 제외 문자열 리터럴) ================= */
function scanJs(src, onString){
    /* 가벼운 토크나이저 — 주석/문자열/템플릿/정규식 구분. 문자열 내용과 시작 offset 을 넘긴다 */
    let i = 0; const n = src.length; let prevSig = '';
    const tplStack = [];
    while(i < n){
        const c = src[i], d = src[i + 1];
        if(c === '/' && d === '/'){ const e = src.indexOf('\n', i); i = e < 0 ? n : e; continue; }
        if(c === '/' && d === '*'){ const e = src.indexOf('*/', i + 2); i = e < 0 ? n : e + 2; continue; }
        if(c === '"' || c === '\''){
            let j = i + 1, s = '';
            while(j < n && src[j] !== c){ if(src[j] === '\\'){ s += src[j + 1]; j += 2; continue; } if(src[j] === '\n') break; s += src[j]; j++; }
            onString(s, i); i = j + 1; prevSig = 'a'; continue;
        }
        if(c === '`' || (c === '}' && tplStack.length && tplStack[tplStack.length - 1] === 0)){
            if(c === '}') tplStack.pop();
            let j = i + 1, s = '';
            while(j < n){ if(src[j] === '\\'){ s += src[j + 1]; j += 2; continue; } if(src[j] === '`'){ j++; break; } if(src[j] === '$' && src[j + 1] === '{'){ tplStack.push(0); j += 2; break; } s += src[j]; j++; }
            onString(s, i); i = j; prevSig = 'a'; continue;
        }
        if(c === '{' && tplStack.length){ tplStack[tplStack.length - 1]++; }
        if(c === '}' && tplStack.length && tplStack[tplStack.length - 1] > 0){ tplStack[tplStack.length - 1]--; }
        if(c === '/'){
            const kw = /(?:return|typeof|case|in|of|delete|void|throw|new)\s*$/.test(src.slice(Math.max(0, i - 10), i));
            if(!prevSig || '(,=:[!&|?{};+-*%<>~^'.includes(prevSig) || kw){
                let j = i + 1, cls = false;
                while(j < n && src[j] !== '\n'){ if(src[j] === '\\'){ j += 2; continue; } if(src[j] === '[') cls = true; else if(src[j] === ']') cls = false; else if(src[j] === '/' && !cls) break; j++; }
                i = j + 1; while(i < n && /[a-z]/i.test(src[i])) i++; prevSig = 'a'; continue;
            }
        }
        if(!/\s/.test(c)) prevSig = /[A-Za-z0-9_$)\]]/.test(c) ? 'a' : c;
        i++;
    }
}
function staticScan(html){
    const hits = []; const lineOf = (off) => html.slice(0, off).split('\n').length;
    const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi; let m; let last = 0; const htmlParts = [];
    while((m = re.exec(html))){
        htmlParts.push([last, html.slice(last, m.index)]); last = m.index + m[0].length;
        const bodyOff = m.index + m[0].indexOf('>') + 1;
        if(/application\/ld\+json/.test(m[1])){ const t = m[2]; const mm = BRAND_RE.exec(t); if(mm) hits.push({ where: 'json-ld', line: lineOf(bodyOff + mm.index), text: t.slice(Math.max(0, mm.index - 30), mm.index + 30) }); continue; }
        scanJs(m[2], (s, off) => { if(s.length > 400 && !/\s/.test(s.slice(0, 400))) return; const mm = BRAND_RE.exec(s); if(mm) hits.push({ where: 'js-string', line: lineOf(bodyOff + off), text: s.slice(0, 80) }); });
    }
    htmlParts.push([last, html.slice(last)]);
    for(const [off, part] of htmlParts){
        const clean = part.replace(/<!--[\s\S]*?-->/g, (x) => ' '.repeat(x.length)).replace(/<style\b[\s\S]*?<\/style>/gi, (x) => ' '.repeat(x.length));
        const r2_ = new RegExp(BRAND_RE.source, 'g'); let mm;
        while((mm = r2_.exec(clean))) hits.push({ where: 'html', line: lineOf(off + mm.index), text: clean.slice(Math.max(0, mm.index - 30), mm.index + 30).replace(/\s+/g, ' ') });
    }
    return hits;
}
/* fillText 계열 인자 리터럴 — 소스 수준 */
function fillTextScan(html){
    const hits = []; const re = /\b(?:fillText|strokeText)\(\s*(['"`])((?:\\.|(?!\1).)*)\1/g; let m;
    while((m = re.exec(html))){ if(BRAND_RE.test(m[2])) hits.push({ line: html.slice(0, m.index).split('\n').length, text: m[2] }); }
    return hits;
}
/* *I18N* 표 추출 → vm 으로 평가 → 언어 누락 계산 */
function extractLiteral(src, start){
    /* start = '{' 또는 '[' 위치. 짝이 맞는 닫는 괄호 다음 위치를 돌려준다 */
    let depth = 0, i = start; const n = src.length;
    while(i < n){
        const c = src[i], d = src[i + 1];
        if(c === '/' && d === '/'){ i = src.indexOf('\n', i); if(i < 0) return -1; continue; }
        if(c === '/' && d === '*'){ i = src.indexOf('*/', i + 2); if(i < 0) return -1; i += 2; continue; }
        if(c === '"' || c === '\'' || c === '`'){ let j = i + 1; while(j < n && src[j] !== c){ if(src[j] === '\\') j++; j++; } i = j + 1; continue; }
        if(c === '{' || c === '[' || c === '(') depth++;
        else if(c === '}' || c === ']' || c === ')'){ depth--; if(depth === 0) return i + 1; }
        i++;
    }
    return -1;
}
function i18nStatic(html){
    const out = {};
    const re = /(?:const|let|var)\s+([A-Za-z0-9_]*I18N[A-Za-z0-9_]*)\s*=\s*([{[])/g; let m;
    while((m = re.exec(html))){
        const name = m[1]; const st = m.index + m[0].length - 1; const en = extractLiteral(html, st);
        if(en < 0){ out[name] = { err: '괄호 짝 없음' }; continue; }
        let obj; try{ obj = vm.runInNewContext('(' + html.slice(st, en) + ')', {}, { timeout: 2000 }); }catch(e){ out[name] = { err: '평가 불가(식 포함): ' + String(e.message).slice(0, 60) }; continue; }
        const missing = []; let leaves = 0;
        const top = Object.keys(obj || {});
        const langTop = top.filter(k => LANGS6.includes(k) || /^[a-z]{2}$/.test(k));
        if(langTop.length >= 2 && LANGS6.filter(l => top.includes(l)).length >= 2){
            /* 형태 A: {ko:{...}, en:{...}} — ko∪en 키가 6개 언어에 모두 있어야 */
            const ref = new Set([...Object.keys(obj.ko || {}), ...Object.keys(obj.en || {})]);
            for(const L of LANGS6){ if(!obj[L]){ missing.push(L + ':(언어 전체)'); continue; } for(const k of ref) if(!(k in obj[L])) missing.push(L + ':' + k); }
            leaves = ref.size * LANGS6.length;
        } else {
            /* 형태 B: 어디서든 {ko:'..', en:'..'} 모양의 잎 — 6개 언어가 다 있어야 */
            const walk = (o, p) => {
                if(!o || typeof o !== 'object') return;
                const ks = Object.keys(o);
                if(!Array.isArray(o) && ks.filter(k => LANGS6.includes(k)).length >= 2){ leaves++; for(const L of LANGS6) if(!(L in o)) missing.push(p + '.' + L); return; }
                for(const k of ks) walk(o[k], p + '.' + k);
            };
            walk(obj, '');
        }
        out[name] = { leaves, missing: missing.length, sample: missing.slice(0, 6) };
    }
    return out;
}

/* ================= 화면 글자 (tm·i18n 공용) ================= */
async function runText(base){
    const langs = LANGS6;
    say('text: ' + langs.length + '개 언어 화면 순회 (DOM·캔버스 글자 수집)');
    const res = await pool(langs, JOBS, async (L) => withEdge({ w: 412, h: 915, dsf: 2.625, mobile: true }, async (e) => {
        await e.open(gameUrl(base, L), 2200);
        await e.ev('__G.hookText()');
        const domStart = await e.ev('__G.visibleText()');
        const t = await e.ev('__G.tour({step:16.667, frames:45, textAt:[1,4,9,17]})', 300000);
        const domPlay = await e.ev('__G.midDom || []');
        await e.ev('(function(){ try{ triggerGameOver(); }catch(e){ (window.__E=window.__E||[]).push("gameover "+e.message); } return 1; })()');
        await sleep(1600);
        const domResult = await e.ev('__G.visibleText()');
        const canvas = await e.ev('[...__G.texts.keys()]');
        const pe = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs('text ' + L, e, pe.concat(t.errs));
        return { L, dom: [...new Set([...domStart, ...domPlay, ...domResult])], canvas };
    }));
    const out = {};
    for(const r of res){
        const all = r.dom.map(s => ['dom', s]).concat(r.canvas.map(s => ['canvas', s]));
        out[r.L] = {
            brand: all.filter(([, s]) => BRAND_RE.test(s)).map(([w, s]) => w + ':' + s.slice(0, 60)),
            hangul: r.L === 'ko' ? [] : all.filter(([, s]) => HANGUL_RE.test(s)).map(([w, s]) => w + ':' + s.slice(0, 50)),
            nDom: r.dom.length, nCanvas: r.canvas.length,
        };
    }
    return out;
}

/* ================= beamdrain (2026-09-29 BEAM 소진 무한 재귀 회귀 + SAT 전용 조작) ================= */
async function runBeamDrain(base){
    const out = {};
    for(const mode of ['tap', 'hold', 'key']){
        out[mode] = await withEdge({ w: 412, h: 915, dsf: 2.625, mobile: mode !== 'key' }, async (e) => {
            await e.open(gameUrl(base, 'ko'), 1800);
            /* 실시간 rAF 로 돈다 (합성 시계 아님) — 멈춤은 rAF 가 끊겨 elapsedMs 가 서는 것으로 드러난다 */
            await e.ev('(function(){ __G.begin(424242, false, true); requestAnimationFrame(gameLoop); if(!window.__inv) window.__inv = setInterval(function(){ invincibleUntil = 1e15; lives = 5; }, 50);'
                + ' gravGauge = GRAV_GAUGE_MAX; SZ_FLAGS.beamHold = ' + (mode === 'hold' ? 'true' : 'false') + '; return 1; })()');
            await sleep(1200);
            const on = await e.ev('(function(){ var m = ' + JSON.stringify(mode) + ';'
                + ' if(m === "tap") szBeamOn(true);'                  /* 터치 탭 토글 경로 */
                + ' else if(m === "hold") szBeamOn(false);'           /* 손가락을 누른 채 둔다(떼지 않음) */
                + ' else document.dispatchEvent(new KeyboardEvent("keydown", { key: "f", bubbles: true }));'   /* PC F 누른 채 */
                + ' return { el: Math.round(elapsedMs), on: gravityFieldActive, g: Math.round(gravGauge) }; })()');
            await sleep(4000);
            const a = await e.ev('({ el: Math.round(elapsedMs), on: gravityFieldActive, g: Math.round(gravGauge), run: running })');
            await sleep(1200);
            const b = await e.ev('({ el: Math.round(elapsedMs), on: gravityFieldActive, g: Math.round(gravGauge), run: running })');
            if(mode === 'key') await e.ev('(document.dispatchEvent(new KeyboardEvent("keyup", { key: "f", bubbles: true })), 1)');
            let sat = null;
            if(mode === 'key'){
                /* SAT — R 키 꾹. 존 1 로 건너뛰어 미션을 켜고 기체를 궤도 아래(원뿔 끝이 궤도에 닿는 자리)에 고정 */
                /* C (2026-09-29) — 달 미션 시각표의 활성 시각으로 건너뛴다(링이 화면에 들어온 뒤). 기체는 이동 슬롯 바로 아래에 고정 */
                await e.ev('(function(){ var W = (typeof szMissionWin === "function") ? szMissionWin(1) : null; startedAt = performance.now() - (W ? W.on - 300 : ZONES[1].s * 1000 + 400) - totalPausedMs; return 1; })()');
                await sleep(700);
                await e.ev('(function(){ if(missionState === "pending") missionPendingUntil = performance.now() + 20; return 1; })()');
                await sleep(400);
                sat = await e.ev('(function(){ var o = _missionCurrentOrbit(); if(!o || missionState !== "active") return { err: "no orbit/mission " + missionState };'
                    + ' window.__pin = setInterval(function(){ var M = (typeof SZM2 !== "undefined") ? SZM2 : null; if(M && M.vis){ player.x = Math.max(20, Math.min(CW - 20, M.x)); player.y = Math.min(CH - 30, M.y + 90); return; }'
                    + ' var oo = _missionCurrentOrbit(); if(oo){ player.x = Math.max(20, Math.min(CW - 20, oo.cx)); player.y = Math.min(CH - 30, oo.cy + oo.r + 90); } }, 4);'
                    + ' return { st: missionState, g0: Math.round(gravGauge), on0: gravityFieldActive }; })()');
                await sleep(150);
                await e.ev('(document.dispatchEvent(new KeyboardEvent("keydown", { key: "r", bubbles: true })), 1)');
                await sleep(700);
                const mid = await e.ev('(function(){ var p0 = satInstallProgress; szBeamOn(true); try{ szBeamTargetDone(); }catch(_){}'
                    + ' return { p0: Math.round(p0), held: satHeld, beamOn: gravityFieldActive, cls: (document.getElementById("satBtn") || {}).className }; })()');
                await sleep(120);
                const mid2 = await e.ev('({ p1: Math.round(satInstallProgress), st: missionState })');
                await e.ev('(function(){ szBeamOff(); gravGauge = GRAV_GAUGE_MAX; return 1; })()');
                const gA = await e.ev('Math.round(gravGauge)');
                await sleep(1500);
                const end = await e.ev('({ st: missionState, g: Math.round(gravGauge), on: gravityFieldActive, held: satHeld, sats: satelliteOrbiting.length })');
                await e.ev('(document.dispatchEvent(new KeyboardEvent("keyup", { key: "r", bubbles: true })), clearInterval(window.__pin), 1)');
                sat = sat && sat.err ? sat : { ...sat, mid, mid2, gA, end };
            }
            await e.ev('(function(){ clearInterval(window.__inv); running = false; return 1; })()');
            const pe = await e.ev('(window.__E||[]).slice(0,8)');
            const x = e.errors();
            collectErrs('beamdrain ' + mode, e, pe);
            return { on, a, b, sat, exc: x.exc.length + pe.length, sample: x.exc.concat(pe).slice(0, 3) };
        });
    }
    return out;
}
function judgeBeamDrain(cur){
    const G = 'G12 beam';
    for(const [mode, r] of Object.entries(cur)){
        const moving = r.a.el > r.on.el + 3000 && r.b.el > r.a.el + 800;
        row(G, mode + ' BEAM 켜고 방치 → 시계 계속', r.on.el + '→' + r.a.el + '→' + r.b.el + 'ms (게이지 ' + r.a.g + '→' + r.b.g + ')', null, '4s 뒤 +3000 이상 · 이후 계속 증가', moving && r.on.on ? 'PASS' : 'FAIL');
        row(G, mode + ' 소진 뒤 BEAM 해제·재충전', 'on=' + r.a.on + ' g ' + r.a.g + '→' + r.b.g, null, 'on=false · 게이지 증가', !r.a.on && r.b.g > r.a.g ? 'PASS' : 'FAIL');
        row(G, mode + ' 예외', r.exc, null, '0', r.exc ? 'FAIL' : 'PASS', r.sample.join(' | ').slice(0, 120));
        if(r.sat){
            const s = r.sat;
            if(s.err){ row(G, 'SAT R 키 설치', s.err, null, 'success', 'FAIL'); continue; }
            row(G, 'SAT R 키 꾹 → 존 1 위성 설치', s.end.st + ' (위성 ' + s.end.sats + ')', null, 'success', s.end.st === 'success' ? 'PASS' : 'FAIL');
            row(G, 'SAT 가 BEAM 게이지·상태를 안 건드림', 'g ' + s.g0 + ' → ' + s.gA + ' → ' + s.end.g + ' · beam ' + s.on0 + '/' + s.end.on, null, '게이지 ±1 · beam off', Math.abs(s.end.g - s.gA) <= 1 && !s.end.on && !s.on0 ? 'PASS' : 'FAIL');
            row(G, '설치 중 BEAM 보급 획득 → 진행률 유지', s.mid.p0 + ' → ' + s.mid2.p1 + ' (held ' + s.mid.held + ')', null, '감소 없음', s.mid.held && (s.mid2.p1 >= s.mid.p0 || s.mid2.st === 'success') ? 'PASS' : 'FAIL');
            row(G, 'R 키 누름 → SAT 버튼 눌림 표시', String(s.mid.cls || '').replace(/sat-btn ?/, ''), null, 'firing 포함', /\bfiring\b/.test(s.mid.cls || '') ? 'PASS' : 'WARN');
        }
    }
}

/* ================= fx0 ================= */
async function runFx0(base){
    const res = {};
    for(const [tag, extra] of [['fx0', 'fx=0'], ['fx1', '']]){
        res[tag] = await withEdge({ w: 412, h: 915, dsf: 2.625, mobile: true }, async (e) => {
            await e.open(gameUrl(base, 'ko', extra), 2000);
            const flags = await e.ev('(function(){ try{ return typeof SZ_FLAGS === "undefined" ? null : JSON.parse(JSON.stringify(SZ_FLAGS)); }catch(e){ return "err"; } })()');
            const sentinel = tag === 'fx1' ? await e.ev(SENTINEL_EXPR) : null;   /* MP0 — 스텁 센티널·API (투어 전에) */
            const t = await e.ev('__G.tour({step:16.667, frames:40})', 300000);
            const pe = await e.ev('(window.__E||[]).slice(0,8)');
            const x = e.errors();
            collectErrs(tag, e, pe.concat(t.errs));
            return { flags, sentinel, errs: t.errs.length + pe.length + x.exc.length, sample: t.errs.concat(pe, x.exc).slice(0, 3), frames: t.frames, zones: t.zones };
        });
    }
    return res;
}

/* ================= bot ================= */
async function runBot(base){
    const out = {};
    for(const fps of [30, 60]){
        const seeds = Array.from({ length: BOT_RUNS }, (_, i) => 1000 + i);
        const chunks = []; const per = Math.ceil(seeds.length / JOBS);
        for(let i = 0; i < seeds.length; i += per) chunks.push(seeds.slice(i, i + per));
        const t0 = Date.now();
        const parts = await pool(chunks, JOBS, async (ch) => withEdge({ w: 412, h: 915, dsf: 1, mobile: true }, async (e) => {
            await e.open(gameUrl(base, 'ko'), 1200);
            const cs = COURSE_SEEDS > 1 ? ch.map(b => 424242 + ((b - 1000) % COURSE_SEEDS) * 7919) : undefined;
            const r = await e.ev('__G.bot(' + JSON.stringify({ seed: 424242, courseSeeds: cs, botSeeds: ch, step: 1000 / fps, secs: 480 }) + ')', 3600000);
            const pe = await e.ev('(window.__E||[]).slice(0,8)');
            collectErrs('bot ' + fps, e, pe.concat(r.filter(x => x.err).map(x => x.err)));
            return r;
        }));
        const runs = parts.flat().filter(x => !x.err);
        const reach = (s) => r1(100 * runs.filter(x => x.t >= s || !x.dead).length / runs.length);
        const zoneDeaths = {}; for(const x of runs) if(x.dead) zoneDeaths[x.z] = (zoneDeaths[x.z] || 0) + 1;
        const ts = runs.map(x => x.t).sort((a, b) => a - b);
        out[fps + 'fps'] = { runs: runs.length, reach60: reach(60), reach184: reach(184), reach343: reach(343), reach475: reach(475), medianT: q(ts, 0.5), zoneDeaths, wallS: Math.round((Date.now() - t0) / 1000) };
        say('bot ' + fps + 'fps: ' + runs.length + '판, 60s ' + out[fps + 'fps'].reach60 + '% · 184s ' + out[fps + 'fps'].reach184 + '% · 343s ' + out[fps + 'fps'].reach343 + '% · 475s ' + out[fps + 'fps'].reach475 + '% (중앙 ' + out[fps + 'fps'].medianT + 's, ' + out[fps + 'fps'].wallS + 's)');
    }
    return out;
}
function judgeBot(cur, base){
    const G = 'G9 bot';
    for(const k of ['30fps', '60fps']){
        const c = cur[k], b = base && base[k];
        for(const s of ['reach60', 'reach184', 'reach343', 'reach475']){
            const ok = !b || Math.abs(c[s] - b[s]) <= 5;
            row(G, k + ' ' + s.replace('reach', '') + 's 도달률', c[s] + '%', b ? b[s] + '%' : null, '기준 ±5%p', b ? (ok ? 'PASS' : 'FAIL') : 'INFO');
        }
    }
    for(const s of ['reach184', 'reach343']){
        const d = Math.abs(cur['30fps'][s] - cur['60fps'][s]);
        row(G, '30/60fps 차 ' + s.replace('reach', '') + 's', r1(d) + '%p', null, '≤2%p (표본 적으면 흔들림)', d <= 2 ? 'PASS' : 'WARN');
    }
}

/* ================= ibot (아이템 봇) ================= */
async function runIBot(base){
    /* MP0 — --ibot-sets 2: 서로 다른 시드·코스 묶음 2개 → 실행 간 중앙값 차이(runDiff). 기준선 본값은 0번 묶음 */
    const NS = Math.max(1, +(A['ibot-sets'] || 1));
    const sets = [];
    for(let k = 0; k < NS; k++) sets.push(await runIBotSet(base, SEED_SET + k));
    const out = sets[0];
    out.seedSet = SEED_SET;
    if(NS > 1){
        out.sets = sets.map((x, i) => { const o = {}; for(const f of ['30fps', '60fps']) o[f] = { medianT: x[f].medianT, ci: x[f].ci, meanT: x[f].meanT, meanCI: x[f].meanCI, reach: x[f].reach, runs: x[f].runs, seedSet: SEED_SET + i }; return o; });
        out.runDiff = {}; out.N = {};
        for(const f of ['30fps', '60fps']){ const ms = sets.map(x => x[f].medianT); out.runDiff[f] = r1(Math.max(...ms) - Math.min(...ms)); out.N[f] = Math.max(8, r1(out.runDiff[f] * 2));
            const mm = sets.map(x => x[f].meanT); (out.runDiffMean = out.runDiffMean || {})[f] = r1(Math.max(...mm) - Math.min(...mm)); }
        say('ibot 실행 간 중앙값 차이: ' + JSON.stringify(out.runDiff) + ' → 허용폭 N ' + JSON.stringify(out.N));
    }
    return out;
}
async function runIBotSet(base, setK){
    const out = {};
    const MISP = A['mis-p'] != null ? +A['mis-p'] : 0.8, SECS = +(A['ibot-secs'] || 560);
    const MARKS = [60, 120, 184, 240, 300, 343, 385, 420, 475, 540];
    for(const fps of [30, 60]){
        /* 묶음 k = 봇 시드 1000+k×판수…, 코스 번호도 k×판수 만큼 민다 (k=0 은 MP0 이전과 같은 시드·코스) */
        const off = setK * BOT_RUNS;
        const seeds = Array.from({ length: BOT_RUNS }, (_, i) => 1000 + off + i);
        const chunks = []; const per = Math.ceil(seeds.length / JOBS);
        for(let i = 0; i < seeds.length; i += per) chunks.push(seeds.slice(i, i + per));
        const t0 = Date.now();
        const parts = await pool(chunks, JOBS, async (ch) => withEdge({ w: 412, h: 915, dsf: 1, mobile: true }, async (e) => {
            await e.open(gameUrl(base, 'ko'), 1200);
            const cs = COURSE_SEEDS > 1 ? ch.map(b => 424242 + (off + ((b - 1000 - off) % COURSE_SEEDS)) * 7919) : undefined;
            let P = { seed: 424242, courseSeeds: cs, botSeeds: ch, step: 1000 / fps, secs: SECS, misP: MISP, misPW: A['mis-p-warn'] != null ? +A['mis-p-warn'] : null, noCut: !!A['no-cut'], noTank: !!A['no-tank'], ext: {} };
            for(const h of IBOT_HOOKS) P = h(P) || P;
            const r = await e.ev('__G.ibot(' + JSON.stringify(P) + ')', 3600000);
            const pe = await e.ev('(window.__E||[]).slice(0,8)');
            collectErrs('ibot ' + fps, e, pe.concat(r.filter(x => x.err).map(x => x.err)));
            return r;
        }));
        const runs = parts.flat().filter(x => !x.err);
        const reach = {}; for(const s of MARKS) reach[s] = r1(100 * runs.filter(x => x.t >= s || !x.dead).length / runs.length);
        /* 10초 칸 피격률 — 그 칸 시작에 살아 있던 판 하나당 피격 수 */
        const hit10 = [];
        for(let b = 0; b < Math.ceil(SECS / 10); b++){
            const alive = runs.filter(x => x.t >= b * 10).length;
            const n = runs.reduce((a, x) => a + x.lost.filter(t => t >= b * 10 && t < b * 10 + 10).length, 0);
            hit10.push(alive ? r2(n / alive) : null);
        }
        const sum = (f) => { const o = {}; for(const x of runs) for(const [k, v] of Object.entries(x[f] || {})) o[k] = (o[k] || 0) + v; for(const k in o) o[k] = r2(o[k] / runs.length); return o; };
        const cut = runs.filter(x => x.cutAt != null);
        const zoneDeaths = {}; for(const x of runs) if(x.dead) zoneDeaths[x.z] = (zoneDeaths[x.z] || 0) + 1;
        const ts = runs.map(x => x.t).sort((a, b) => a - b);
        out[fps + 'fps'] = { runs: runs.length, misP: MISP, reach, hit10, picks: sum('picks'), uses: sum('uses'), mis: r2(runs.reduce((a, x) => a + x.nMis, 0) / runs.length),
            raw: runs.map(x => [x.t, x.dead ? 1 : 0, x.cutAt, x.lost.length, x.z, x.why]),
            fuelDeathPct: r1(100 * runs.filter(x => x.dead && x.why === 'fuel').length / runs.length),
            fuelDeathMed: (() => { const f = runs.filter(x => x.dead && x.why === 'fuel').map(x => x.t).sort((a, b) => a - b); return f.length ? q(f, 0.5) : null; })(),
            fuelDeathRange: (() => { const f = runs.filter(x => x.dead && x.why === 'fuel').map(x => x.t).sort((a, b) => a - b); return f.length ? [f[0], f[f.length - 1]] : null; })(),
            hdrPct: r1(100 * runs.filter(x => x.hdrN > 0).length / runs.length),
            fuelMinMed: q(runs.map(x => x.fuelMin == null ? 1 : x.fuelMin).sort((a, b) => a - b), 0.5),
            pxs: q(runs.map(x => x.pxs || 0).sort((a, b) => a - b), 0.5),
            cutPct: r1(100 * cut.length / runs.length), cutMed: cut.length ? q(cut.map(x => x.cutAt).sort((a, b) => a - b), 0.5) : null, zoneDeaths, medianT: q(ts, 0.5), ci: bootCI(ts), meanT: r1(ts.reduce((a, b) => a + b, 0) / Math.max(1, ts.length)), meanCI: bootCI(ts, 1000, true), wallS: Math.round((Date.now() - t0) / 1000) };
        if(setK) delete out[fps + 'fps'].raw;   /* 원자료는 0번 묶음만 보관 (기준선 파일 크기) */
        say('ibot ' + fps + 'fps: ' + runs.length + '판 · ' + MARKS.map(s => s + 's ' + reach[s] + '%').join(' · ') + ' (중앙 ' + out[fps + 'fps'].medianT + 's, 차단 ' + out[fps + 'fps'].cutPct + '%, 연료사 ' + out[fps + 'fps'].fuelDeathPct + '% 중앙 ' + out[fps + 'fps'].fuelDeathMed + 's ' + JSON.stringify(out[fps + 'fps'].fuelDeathRange) + ', 헤더 ' + out[fps + 'fps'].hdrPct + '%, 탱커 ' + (out[fps + 'fps'].picks.fuel || 0) + '/판, 최저연료 중앙 ' + out[fps + 'fps'].fuelMinMed + ', 이동 ' + out[fps + 'fps'].pxs + 'px/s, CI ' + JSON.stringify(out[fps + 'fps'].ci) + ', 묶음 ' + setK + ', ' + out[fps + 'fps'].wallS + 's)');
    }
    return out;
}
function judgeIBot(cur, base){
    const G = 'G9 ibot';
    /* MP0 (6장) — 병합 판정: 중앙값 생존시간 ±N초 그리고 부트스트랩 95% CI 겹침. N = max(8, 실행 간 차이×2).
       도달률(꼬리 지표)은 표본 잡음이 커서 참고(INFO)만 한다 */
    const sameCond = base && (base.seedSet || 0) === (cur.seedSet || 0) && base['30fps'] && base['30fps'].runs === cur['30fps'].runs;
    if(base && !sameCond) row(G, '기준선 조건', '묶음 ' + (cur.seedSet || 0) + ' · ' + cur['30fps'].runs + '판', '묶음 ' + (base.seedSet || 0) + ' · ' + (base['30fps'] && base['30fps'].runs) + '판', '같은 시드 묶음·판 수', 'WARN', '판 수·묶음이 달라도 분포 판정은 하지만 해석 주의');
    for(const k of ['30fps', '60fps']){
        const c = cur[k], b = base && base[k];
        if(b && b.medianT != null){
            const N = ibotN(base, k);
            const d = r1(c.medianT - b.medianT);
            const ov = c.ci && b.ci && c.ci[0] != null && b.ci && b.ci[0] != null ? (c.ci[0] <= b.ci[1] && b.ci[0] <= c.ci[1]) : null;
            row(G, k + ' 중앙값 생존시간', c.medianT + 's (CI ' + (c.ci || []).join('–') + ')', b.medianT + 's (CI ' + (b.ci || []).join('–') + ')', '±' + N + 's · CI 겹침', Math.abs(d) <= N && ov !== false ? 'PASS' : 'FAIL', 'Δ ' + d + 's' + (ov === null ? ' · 기준선 CI 없음' : ov ? '' : ' · CI 안 겹침'));
        } else row(G, k + ' 중앙값 생존시간', c.medianT + 's (CI ' + (c.ci || []).join('–') + ')', null, '기준선 없음', 'INFO');
        /* MP0 발견(2026-10-08) — ibot 생존시간은 존 19 블랙홀(475.8~475.9s)에 12~15% 가 한꺼번에 몰려 중앙값이 그 점에 붙는다.
           중앙값 판정이 둔해지므로 평균(부트스트랩 CI)을 보조 지표로 함께 본다 — 허용폭 = max(8, 평균 실행 간 차이×2), 벗어나면 WARN(판정은 6장 규칙 유지) */
        if(c.meanT != null){
            const bm = b && b.meanT != null ? b : null;
            const Nm = Math.max(8, r1(2 * ((base && base.runDiffMean && base.runDiffMean[k]) || 0)));
            const dm = bm ? r1(c.meanT - bm.meanT) : null;
            row(G, k + ' 평균 생존시간 (보조)', c.meanT + 's (CI ' + (c.meanCI || []).join('–') + ')', bm ? bm.meanT + 's (CI ' + (bm.meanCI || []).join('–') + ')' : null, bm ? '±' + Nm + 's' : '기록', bm ? (Math.abs(dm) <= Nm ? 'PASS' : 'WARN') : 'INFO', bm ? 'Δ ' + dm + 's' : '');
        }
        for(const s2 of [60, 184, 343, 475]) row(G, k + ' ' + s2 + 's 도달률 (참고)', c.reach[s2] + '%', b && b.reach ? b.reach[s2] + '%' : null, '참고', 'INFO');
        row(G, k + ' 보급 영구 차단 판', c.cutPct + '%', b ? b.cutPct + '%' : null, '-', 'INFO');
        if(c.fuelDeathPct != null) row(G, k + ' 추진제 고갈(우주 미아) 판', c.fuelDeathPct + '%', b && b.fuelDeathPct != null ? b.fuelDeathPct + '%' : null, '-', 'INFO');
    }
    if(cur.runDiff) row(G, '실행 간 중앙값 차이 (묶음 ' + (cur.sets || []).length + '개)', JSON.stringify(cur.runDiff), base && base.runDiff ? JSON.stringify(base.runDiff) : null, '허용폭 N = max(8, ×2) → ' + JSON.stringify(cur.N), 'INFO');
}

/* ================= MP0 (2026-10-08) — hitpath · noshake · restart · audioctx · latency · boot · flags0 · startshot · gl0 ================= */
function hitScenarios(){
    const base = [
        { key: 'natural@16.67', mode: 'natural', step: 1000 / 60 },
        { key: 'natural@33.33', mode: 'natural', step: 1000 / 30 },
        { key: 'inject@16.67', mode: 'inject', step: 1000 / 60 },
        { key: 'inject@33.33', mode: 'inject', step: 1000 / 30 },
    ];
    return base.concat(HIT_SCEN);
}
const hitSig = (o) => ({ h: sha(o.ev), nEv: o.nEv, nHit: o.nHit, over: o.over, livesEnd: o.livesEnd, comboMax: o.comboMax, endSec: o.endSec, endZone: o.endZone, frames: o.frames, errs: o.errs.length });
async function runHitpath(base, extra = '', tag = 'hitpath'){
    const jobs = [];
    for(const s of hitScenarios()){
        jobs.push({ ...s, mr: 1, id: s.key });
        /* Math.random 시드만 바꾼 짝 — 판정·수명·콤보가 Math.random 에 기대지 않는지(표시 전용 Math.random 은 자유) */
        if(!extra && !s.noPair && s.step < 20) jobs.push({ ...s, mr: 7, id: s.key + '#mr7' });
    }
    say(tag + ': ' + jobs.length + '판 (자연·주입 × 프레임' + (extra ? ' · ?' + extra : '') + ')');
    const res = await pool(jobs, JOBS, async (j) => withEdge({ w: 412, h: 915, dsf: 2.625, mobile: true }, async (e) => {
        await e.open(gameUrl(base, 'ko', extra), 1500);
        const o = await e.ev('__G.hitpath(' + JSON.stringify({ seed: j.seed || 424242, step: j.step, secs: j.secs || 240, mode: j.mode, mr: j.mr, lives: j.lives || 5, setup: j.setup || null }) + ')', 600000);
        const pe = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs(tag + ' ' + j.id, e, pe.concat(o.errs));
        return { id: j.id, sig: hitSig(o), head: o.ev.slice(0, 14) };
    }));
    const out = { runs: {}, head: {} };
    for(const r of res){ out.runs[r.id] = r.sig; out.head[r.id] = r.head; }
    return out;
}
function judgeHitpath(cur, base, G = 'G13 hitpath'){
    for(const [k, m] of Object.entries(cur.runs)){
        if(k.includes('#mr')) continue;
        if(m.errs) row(G, k + ' 에러', m.errs, 0, '0', 'FAIL');
        if(!(m.nHit > 0)) row(G, k + ' 피격 경로를 탔는가', m.nHit + '회', null, '≥1', 'FAIL', '하네스가 충돌 경로를 못 탔다');
        const b = base && base.runs && base.runs[k];
        const desc = '피격 ' + m.nHit + ' · 끝 ' + (m.over != null ? (m.over / 1000).toFixed(1) + 's' : '생존') + ' · 콤보 ' + m.comboMax + ' · #' + m.h;
        if(!b){ row(G, k + ' 해시', desc, null, '기준선 없음', 'INFO'); }
        else row(G, k + ' 기준선 일치', desc, '#' + b.h + ' (피격 ' + b.nHit + ')', '해시 동일', m.h === b.h ? 'PASS' : 'FAIL');
        const p = cur.runs[k + '#mr7'];
        if(p) row(G, k + ' Math.random 시드 무관', p.h === m.h ? '같음' : '다름 #' + p.h, null, '같음 (판정은 수열·시계만)', p.h === m.h ? 'PASS' : 'FAIL', p.h === m.h ? '' : '피격·콤보 경로가 Math.random 에 기대고 있다');
    }
}

async function runNoshake(base){
    return withEdge({ w: 412, h: 915, dsf: 2.625, mobile: true }, async (e) => {
        await e.open(gameUrl(base, 'ko'), 1500);
        const syn = await e.ev('__G.noshake({seed:424242, step:16.667, secs:24})', 600000);
        /* ① 실시간 — 진짜 rAF 로 날며 피격·폭탄을 건 동안 #canvasWrap 과 조상의 CSS transform/translate/rotate/scale 을 50ms 마다 본다 */
        await e.ev(`(function(){ __G.begin(424242, false, true); requestAnimationFrame(gameLoop); lives = 99; invincibleUntil = 0;
            window.__css = { n: 0, bad: [] };
            const chk = function(){ let el = document.getElementById('canvasWrap'); const cv = document.getElementById('dodge-canvas'); const L = [cv]; for(; el; el = el.parentElement) L.push(el);
                for(const x of L){ const c = getComputedStyle(x); const tf = c.transform, tr = c.translate, ro = c.rotate, sc = c.scale;
                    const okT = tf === 'none' || tf === 'matrix(1, 0, 0, 1, 0, 0)'; const ok2 = (!tr || tr === 'none') && (!ro || ro === 'none') && (!sc || sc === 'none');
                    if(!okT || !ok2){ if(__css.bad.length < 12) __css.bad.push((x.id || x.className || x.tagName) + ' ' + tf + ' ' + tr + ' ' + ro + ' ' + sc); } }
                __css.n++; };
            window.__cssT = setInterval(function(){ chk(); player.x = 180; player.y = 390; if(lives < 50) lives = 99; }, 50);
            setTimeout(function(){ try{ triggerWipe(); }catch(_){} }, 600);
            setTimeout(function(){ try{ _activatePlasmaStorm(performance.now()); }catch(_){} }, 1600);
            return 1; })()`);
        await sleep(3600);
        const css = await e.ev('(function(){ clearInterval(window.__cssT); running = false; return window.__css; })()');
        const pe = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs('noshake', e, pe.concat(syn.errs));
        return { ...syn, css };
    });
}
function judgeNoshake(cur, base){
    const G = 'G14 noshake';
    const b = base || null;
    row(G, '① CSS transform 항등 (#canvasWrap·조상·캔버스)', cur.css.bad.length ? cur.css.bad.slice(0, 2).join(' | ') : '항등 (' + cur.css.n + '회 확인)', b ? (b.css.bad.length ? b.css.bad.length + '건' : '항등') : null, '0건', cur.css.bad.length ? 'FAIL' : (cur.css.n > 10 ? 'PASS' : 'WARN'));
    row(G, '② 전체 fillRect 변환 항등', cur.bad.length ? cur.bad.length + '건 ' + JSON.stringify(cur.bad[0]).slice(0, 90) : '항등 (' + cur.nFull + '회)', b ? (b.bad.length + '건') : null, '평행이동·회전 0', cur.bad.length ? 'FAIL' : 'PASS');
    const lim = Math.round(0.12 * 255 * 10) / 10;
    row(G, '③ 프레임 간 평균 휘도 증가 최대', cur.maxInc + ' (' + cur.maxIncFrac + '×255) @' + cur.maxAt + 'ms ' + cur.maxNear, b ? b.maxInc + ' ' + b.maxNear : null, '≤' + lim + ' (0.12×255)', cur.maxInc <= lim ? 'PASS' : 'FAIL', '상위 ' + cur.top.map(x => x[0] + '@' + x[2]).join(' '));
    row(G, '자극 장면 실제로 걸림', cur.marks.map(m => m[0]).join('·') + (cur.feverSeen ? '·피버켜짐' : '·피버안켜짐'), null, '폭탄·폭풍·피버', cur.marks.length >= 3 ? 'PASS' : 'WARN');
}

async function runRestart(base){
    const N = Math.max(2, +(A['restart-runs'] || 6));
    return withEdge({ w: 412, h: 915, dsf: 2.625, mobile: true }, async (e) => {
        await e.open(gameUrl(base, 'ko'), 1800);
        /* 첫 판은 긴 인트로(이야기 3·2·1) — 재시작 측정은 두 번째 판부터. 실제 시간, 가짜 시계 없음 */
        await e.ev('(function(){ startGame(); window.__inv = setInterval(function(){ invincibleUntil = 1e15; }, 100); return 1; })()');
        await e.ev(`new Promise(function(res){ var t0 = performance.now(); (function w(){ if(running || performance.now() - t0 > 15000) return res(1); setTimeout(w, 50); })(); })`, 30000);
        const out = [];
        for(let i = 0; i < N; i++){
            await sleep(1500);
            const r = await e.ev(`new Promise(function(res){
                clearInterval(window.__inv); invincibleUntil = 0;
                var t0 = performance.now(), tCard = null, tTap = null;
                try{ triggerGameOver(); }catch(err){ return res({ err: 'gameover ' + err.message }); }
                (function w(){
                    var now = performance.now();
                    if(now - t0 > 20000) return res({ err: 'timeout', tCard: tCard, tTap: tTap });
                    var ov = document.getElementById('overlay'), b = document.getElementById('ovBtn');
                    if(tTap == null){
                        var ok = ov && b && !ov.classList.contains('hidden') && !ov.classList.contains('go-lock') && b.getClientRects().length && getComputedStyle(ov).pointerEvents !== 'none' && +getComputedStyle(ov).opacity > 0.5;
                        if(ok){ tCard = now - t0; tTap = now; b.click(); }
                    } else if(running && !(typeof _introRunning !== 'undefined' && _introRunning)){
                        window.__inv = setInterval(function(){ invincibleUntil = 1e15; }, 100);
                        return res({ total: Math.round(now - t0), card: Math.round(tCard), intro: Math.round(now - tTap) });
                    }
                    setTimeout(w, 10);
                })();
            })`, 40000);
            out.push(r);
        }
        await e.ev('(function(){ clearInterval(window.__inv); running = false; return 1; })()');
        const pe = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs('restart', e, pe);
        const ok = out.filter(x => x.total != null).map(x => x.total).sort((a, b) => a - b);
        return { path: 'tap', runs: out, n: ok.length, p50: q(ok, 0.5), p90: q(ok, 0.9), cardP50: q(out.filter(x => x.card != null).map(x => x.card).sort((a, b) => a - b), 0.5), introP50: q(out.filter(x => x.intro != null).map(x => x.intro).sort((a, b) => a - b), 0.5) };
    });
}
function judgeRestart(cur, base){
    const G = 'G15 restart';
    const errs = cur.runs.filter(x => x.err);
    row(G, '탭 경로 측정 오류', errs.length, null, '0', errs.length ? 'FAIL' : 'PASS', errs.map(x => x.err).join(' ').slice(0, 80));
    row(G, '탭 경로 사망→조종 p50 / p90', cur.p50 + ' / ' + cur.p90 + 'ms (카드 ' + cur.cardP50 + ' + 인트로 ' + cur.introP50 + ')', base ? base.p50 + ' / ' + base.p90 + 'ms' : null, base ? 'p50 ≤ 기준선+250ms (MP2 목표: 탭 p90 ≤3500)' : '기록', base ? (cur.p50 <= base.p50 + 250 ? 'PASS' : 'FAIL') : 'INFO');
}

/* AudioContext 생성 수 — 페이지 스크립트보다 먼저 생성자를 감싼다 */
const AC_HOOK = `(function(){ window.__AC = 0; window.__ACs = []; var seen = [];
  ['AudioContext','webkitAudioContext'].forEach(function(k){ var O = window[k]; if(!O || seen.indexOf(O) >= 0) return; seen.push(O);
    var W = function(a, b){ window.__AC++; try{ window.__ACs.push(String(new Error().stack || '').split('\\n').slice(2, 4).map(function(s){ return s.trim().replace(location.origin, ''); }).join(' < ')); }catch(_){}
      return new O(a, b); };
    W.prototype = O.prototype; try{ Object.setPrototypeOf(W, O); }catch(_){}
    window.AudioContext = W; if(window.webkitAudioContext) window.webkitAudioContext = W; }); })();`;
async function runAudioCtx(base){
    return withEdge({ w: 412, h: 915, dsf: 2.625, mobile: true }, async (e) => {
        await e.send('Page.addScriptToEvaluateOnNewDocument', { source: AC_HOOK });
        await e.open(gameUrl(base, 'ko'), 2200);
        const a0 = await e.ev('window.__AC');
        /* 실제 사용자 제스처(탭) — 잠금 해제 경로를 다 깨운다 */
        const pt = await e.ev('(function(){ var r = document.getElementById("dodge-canvas").getBoundingClientRect(); return [Math.round(r.left + r.width / 2), Math.round(r.top + 40)]; })()');
        await e.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: pt[0], y: pt[1] }] });
        await e.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
        await e.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Shift', code: 'ShiftLeft' });
        await e.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Shift', code: 'ShiftLeft' });
        await sleep(400);
        await e.ev('(function(){ startGame(); window.__inv = setInterval(function(){ invincibleUntil = 1e15; }, 100); return 1; })()');
        await sleep(6500);
        await e.ev('(function(){ clearInterval(window.__inv); invincibleUntil = 0; try{ triggerGameOver(); }catch(_){} return 1; })()');
        await sleep(1200);
        const r = await e.ev('({ n: window.__AC, src: window.__ACs })');
        const pe = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs('audioctx', e, pe);
        return { atLoad: a0, n: r.n, src: r.src };
    });
}
function judgeAudioCtx(cur, base){
    const G = 'G16 audioctx';
    row(G, '페이지 전체 AudioContext 생성 수', cur.n + ' (로드 직후 ' + cur.atLoad + ')', base ? base.n : null, base ? '≤ 기준선 (MP4a 목표 ≤2)' : '기록 (MP4a 목표 ≤2)', base ? (cur.n <= base.n ? 'PASS' : 'FAIL') : 'INFO', cur.src.map(s => s.split(' < ')[0].replace(/^at /, '')).join(' | ').slice(0, 150));
}

/* 입력 지연 — 입력 이벤트(캡처 단계) 시각 → 기체 좌표가 바뀐 채 drawFrame 이 끝난 시각. 프레임 수 = 그 사이 gameLoop 호출 수 */
const LAT_PAGE = `(function(){
  if(window.__LAT) return 1;
  var L = window.__LAT = { on: null, res: [], loops: 0 };
  var mark = function(){ if(L.on || !running) return; L.on = { t: performance.now(), x: player.x, y: player.y, loops: L.loops }; };
  addEventListener('mousemove', mark, true); addEventListener('touchmove', mark, true);
  var od = window.drawFrame;
  window.drawFrame = function(now, dt){ var r = od.apply(this, arguments);
    if(L.on && (Math.abs(player.x - L.on.x) > 0.5 || Math.abs(player.y - L.on.y) > 0.5)){ L.res.push([Math.round((performance.now() - L.on.t) * 10) / 10, L.loops - L.on.loops]); L.on = null; }
    return r; };
  var og = window.gameLoop;
  window.gameLoop = function(t){ L.loops++; return og.apply(this, arguments); };
  return 1; })()`;
async function runLatency(base){
    const out = {};
    const N = 24;
    for(const mode of ['mouse', 'touch']){
        const vp = mode === 'mouse' ? { w: 1280, h: 800, dsf: 1, mobile: false } : { w: 412, h: 915, dsf: 2.625, mobile: true };
        out[mode] = await withEdge(vp, async (e) => {
            await e.open(gameUrl(base, 'ko'), 1800);
            await e.ev(LAT_PAGE);
            /* 실제 시작 경로(startGame) — 플로팅 조작 층은 판 시작(.on) 때 놓인다 */
            await e.ev('(function(){ window.__inv = setInterval(function(){ invincibleUntil = 1e15; lives = 5; }, 50); startGame(); return 1; })()');
            await e.ev(`new Promise(function(res){ var t0 = performance.now(); (function w(){ if((running && !_introRunning) || performance.now() - t0 > 15000) return res(1); setTimeout(w, 50); })(); })`, 30000);
            await sleep(900);
            const geo = await e.ev('(function(){ var r = document.getElementById("dodge-canvas").getBoundingClientRect(); var cx = r.left + r.width * 0.5, cy = r.top + r.height * 0.55; var el = document.elementFromPoint(cx, cy);'
                + ' return { l: r.left, t: r.top, w: r.width, h: r.height, float: document.body.classList.contains("sz-float"), at: el ? (el.id || el.className || el.tagName) : null }; })()');
            const cx = geo.l + geo.w * 0.5, cy = geo.t + geo.h * 0.55;
            if(mode === 'touch') await e.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: cx, y: cy, id: 1 }] });
            for(let i = 0; i < N; i++){
                const dx = ((i % 2) ? 1 : -1) * (14 + (i % 5) * 3), x = cx + dx, y = cy + ((i % 3) - 1) * 6;
                await e.ev('(window.__LAT.on = null, 1)');
                if(mode === 'mouse') await e.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
                else await e.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y, id: 1 }] });
                await sleep(90 + (i % 4) * 13);   /* 프레임 위상을 고르게 섞는다 */
            }
            if(mode === 'touch') await e.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
            const dbg = await e.ev('({ tp: (typeof pendingTp !== "undefined") ? JSON.stringify(pendingTp).slice(0, 160) : null, id: (typeof tpTouchId !== "undefined") ? tpTouchId : null, run: running, px: player.x })');
            const r = await e.ev('(function(){ clearInterval(window.__inv); running = false; return window.__LAT.res; })()');
            const pe = await e.ev('(window.__E||[]).slice(0,8)');
            collectErrs('latency ' + mode, e, pe);
            const ms = r.map(x => x[0]).sort((a, b) => a - b), fr = r.map(x => x[1]).sort((a, b) => a - b);
            return { n: r.length, sent: N, float: geo.float, at: geo.at, dbg: r.length ? undefined : dbg, p50: q(ms, 0.5), p90: q(ms, 0.9), max: ms[ms.length - 1], fr50: q(fr, 0.5), frMax: fr[fr.length - 1] };
        });
        say('latency ' + mode + ': ' + JSON.stringify(out[mode]));
    }
    return out;
}
function judgeLatency(cur, base){
    const G = 'G17 latency';
    for(const [m, c] of Object.entries(cur)){
        const b = base && base[m];
        row(G, m + ' 측정 수', c.n + '/' + c.sent + (m === 'touch' ? (c.float ? ' (플로팅)' : ' (클래식)') : ''), null, '≥ 절반', c.n >= c.sent / 2 ? 'PASS' : 'FAIL');
        row(G, m + ' 입력→그려짐 프레임 수 중앙/최대', c.fr50 + ' / ' + c.frMax, b ? b.fr50 + ' / ' + b.frMax : null, b ? '중앙값 증가 0프레임' : '기록', b ? (c.fr50 <= b.fr50 ? 'PASS' : 'FAIL') : 'INFO');
        row(G, m + ' 입력→그려짐 ms p50/p90/최대', c.p50 + ' / ' + c.p90 + ' / ' + c.max, b ? b.p50 + ' / ' + b.p90 : null, '참고 (rAF 위상 포함)', 'INFO');
    }
}

/* 첫 로드 — CPU 4x, 캐시 끔. 탐색 시작(timeOrigin) → #ovBtn 이 보이고 startGame 이 정의되고 문서 파싱이 끝난 시각 */
const BOOT_HOOK = `(function(){ var t = setInterval(function(){ try{ var b = document.getElementById('ovBtn');
  if(b && typeof startGame === 'function' && document.readyState !== 'loading' && b.getClientRects().length){ window.__BOOT = performance.now(); clearInterval(t); } }catch(e){} }, 4); })();`;
async function runBoot(base){
    const N = Math.max(1, +(A['boot-runs'] || 3));
    const runs = [];
    for(let i = 0; i < N; i++){
        runs.push(await withEdge({ w: 412, h: 915, dsf: 2.625, mobile: true }, async (e) => {
            await e.send('Page.addScriptToEvaluateOnNewDocument', { source: BOOT_HOOK });
            await e.send('Network.setCacheDisabled', { cacheDisabled: true });
            await e.send('Emulation.setCPUThrottlingRate', { rate: 4 });
            await e.send('Page.navigate', { url: gameUrl(base, 'ko') });
            let r = null;
            for(let k = 0; k < 200 && !r; k++){ await sleep(150); try{ r = await e.ev('window.__BOOT ? { boot: Math.round(window.__BOOT), lt: (window.__LT || []).filter(function(x){ return x[0] < window.__BOOT; }), dcl: Math.round(performance.getEntriesByType("navigation")[0].domContentLoadedEventEnd || 0) } : null', 5000); }catch(_){} }
            await e.send('Emulation.setCPUThrottlingRate', { rate: 1 });
            const pe = await e.ev('(window.__E||[]).slice(0,8)').catch(() => []);
            collectErrs('boot', e, pe);
            if(!r) return { err: 'timeout' };
            return { boot: r.boot, dcl: r.dcl, ltSum: r.lt.reduce((s, x) => s + x[1], 0), ltN: r.lt.length, ltMax: r.lt.reduce((m, x) => Math.max(m, x[1]), 0) };
        }));
    }
    const ok = runs.filter(x => !x.err), med = (f) => q(ok.map(x => x[f]).sort((a, b) => a - b), 0.5);
    return { runs, n: ok.length, boot: med('boot'), dcl: med('dcl'), ltSum: med('ltSum'), ltN: med('ltN'), ltMax: med('ltMax') };
}
function judgeBoot(cur, base){
    const G = 'G18 boot';
    row(G, '측정', cur.n + '/' + cur.runs.length, null, '전부', cur.n === cur.runs.length ? 'PASS' : 'WARN');
    const lim = base ? Math.round(base.boot * 1.15 + 150) : null;
    row(G, '4x 탐색→#ovBtn 탭 가능 (중앙값)', cur.boot + 'ms (DCL ' + cur.dcl + ')', base ? base.boot + 'ms' : null, base ? '≤' + lim + 'ms (기준×1.15+150)' : '기록', base ? (cur.boot <= lim ? 'PASS' : 'WARN') : 'INFO', 'headless 흔들림이 커서 WARN 까지만');
    row(G, '그 전 롱태스크 합 / 수 / 최대', cur.ltSum + 'ms / ' + cur.ltN + ' / ' + cur.ltMax + 'ms', base ? base.ltSum + 'ms / ' + base.ltN : null, '기록', 'INFO');
}

/* flags0 — 킬스위치 전부 끈 URL 로 det(구성마다 첫 스텝)·hitpath 가 기준선과 같아야 한다 */
async function runFlags0(base){
    const det = await runDet(base, { extra: MP_OFF_Q, firstOnly: true, tag: 'flags0 det' });
    const hit = await runHitpath(base, MP_OFF_Q, 'flags0 hitpath');
    let flags = null;
    try{ flags = await withEdge({ w: 412, h: 915, dsf: 2.625, mobile: true }, async (e) => { await e.open(gameUrl(base, 'ko', MP_OFF_Q), 1200); return e.ev('(function(){ try{ var o = {}; for(var i = 1; i <= 8; i++) o["mp" + i] = window.SZ_FLAGS ? SZ_FLAGS["mp" + i] : null; return o; }catch(e){ return null; } })()'); }); }catch(_){}
    return { det, hit, flags };
}
function judgeFlags0(cur, BASE){
    const G = 'G19 flags0';
    const off = cur.flags && Object.values(cur.flags).every(v => v === false);
    row(G, '?mp1..8=0 → SZ_FLAGS.mpN 전부 false', JSON.stringify(cur.flags), null, '전부 false', off ? 'PASS' : 'FAIL');
    const bd = BASE && BASE.det && BASE.det.secs === cur.det.secs ? BASE.det : null;
    for(const [k, m] of Object.entries(cur.det.runs)){
        const b = bd && bd.runs[k];
        if(!b){ row(G, 'det ' + k, '기준선 없음', null, '-', 'WARN'); continue; }
        const parts = DET_CMP.filter(p => m[p] !== b[p]);
        row(G, 'det ' + k + ' (킬스위치 끔)', parts.length ? '다름: ' + parts.join(',') : '동일', '', '기준선과 완전 일치', parts.length ? 'FAIL' : 'PASS');
    }
    const bh = BASE && BASE.hitpath;
    for(const [k, m] of Object.entries(cur.hit.runs)){
        const b = bh && bh.runs[k];
        if(!b){ row(G, 'hitpath ' + k, '기준선 없음', null, '-', 'WARN'); continue; }
        row(G, 'hitpath ' + k + ' (킬스위치 끔)', '#' + m.h, '#' + b.h, '같음', m.h === b.h ? 'PASS' : 'FAIL');
    }
}

/* 시작 화면 — 보통 스크린샷(사람 확인용) + 정지 스크린샷(애니메이션 끔·캔버스 숨김, 해시 비교) + DOM 배치 서명(id 제외) */
const STARTSHOT_SIZES = [[320, 568, 2], [390, 844, 3]];
async function runStartshot(base){
    const jobs = [];
    for(const L of ['ko', 'en']) for(const s of STARTSHOT_SIZES) jobs.push({ L, w: s[0], h: s[1], dsf: s[2] });
    const res = await pool(jobs, JOBS, async (j) => withEdge({ w: j.w, h: j.h, dsf: j.dsf, mobile: true }, async (e) => {
        const key = j.L + '_' + j.w + 'x' + j.h;
        /* 고정 pid — 첫 방문 pid 생성(Math.random) 위치가 달라도 화면이 같게 */
        await e.send('Page.addScriptToEvaluateOnNewDocument', { source: 'try{ if(!localStorage.getItem("szx_pid")) localStorage.setItem("szx_pid", "gatepid0001"); }catch(e){}' });
        await e.open(gameUrl(base, j.L), 2600);
        await e.shot(path.join(OUT, 'startshot', key + '.png'));
        /* 애니메이션(조종사 숨쉬기 등)을 멈춘 뒤 잰다 — 움직이는 요소의 좌표가 측정 시각마다 달라지지 않게 */
        await e.ev(`(function(){ var s = document.createElement('style'); s.textContent = '*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important} #dodge-canvas{visibility:hidden!important}'; document.head.appendChild(s); return 1; })()`);
        await sleep(400);
        const sig = await e.ev(`(function(){ var ov = document.getElementById('overlay'); var o = [];
            ov.querySelectorAll('*').forEach(function(x){ if(!x.getClientRects().length) return; var r = x.getBoundingClientRect(); var c = getComputedStyle(x); if(c.display === 'none' || c.visibility === 'hidden') return;
                var t = ''; for(var n = x.firstChild; n; n = n.nextSibling) if(n.nodeType === 3) t += n.nodeValue.trim();
                o.push([x.tagName, String(x.className || ''), t.slice(0, 30), Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]); });
            return o; })()`);
        const r = await e.send('Page.captureScreenshot', { format: 'png' }, 30000);
        fs.writeFileSync(path.join(OUT, 'startshot', key + '_frozen.png'), Buffer.from(r.data, 'base64'));
        const pe = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs('startshot ' + key, e, pe);
        return { key, frozen: sha(r.data), dom: sha(sig), nDom: sig.length, sig };
    }));
    const out = {};
    for(const r of res) out[r.key] = r;
    return out;
}
function judgeStartshot(cur, base){
    const G = 'G20 start';
    for(const [k, c] of Object.entries(cur)){
        const b = base && base[k];
        if(!b){ row(G, k + ' 시작 화면', 'DOM ' + c.nDom + '개 #' + c.dom + ' · 정지샷 #' + c.frozen, null, '기준선 없음', 'INFO'); continue; }
        let diff = '';
        if(c.dom !== b.dom && b.sig){ const bs = new Set(b.sig.map(x => JSON.stringify(x))); const cs = new Set(c.sig.map(x => JSON.stringify(x)));
            diff = '새: ' + c.sig.filter(x => !bs.has(JSON.stringify(x))).slice(0, 2).map(x => x.join(',')).join(' | ') + ' · 빠짐: ' + b.sig.filter(x => !cs.has(JSON.stringify(x))).slice(0, 2).map(x => x.join(',')).join(' | '); }
        row(G, k + ' DOM 배치 서명(id 제외)', c.dom === b.dom ? '같음 (' + c.nDom + '개)' : '다름', '#' + b.dom, '같음', c.dom === b.dom ? 'PASS' : 'FAIL', diff.slice(0, 160));
        row(G, k + ' 정지 스크린샷 해시', c.frozen === b.frozen ? '같음' : '다름 #' + c.frozen, '#' + b.frozen, '같음 (다르면 PNG 를 눈으로 비교)', c.frozen === b.frozen ? 'PASS' : 'WARN');
    }
}

/* 스텁·API 센티널 (MP0) — 블록마다 IIFE, 끝에서 SZMPn.ok = true. 한 블록이 렉시컬 충돌로 죽으면 그 블록 센티널만 빠진다 */
const MP0_API = ['SZE', 'SZSTART', 'szRunKind', 'szWarpTo', 'szRAF', 'SZGL', 'szShipSkinHook', 'SZAU', 'szTel', 'szRecOk'];
const SENTINEL_EXPR = `(function(){ var s = {}; for(var i = 1; i <= 8; i++){ var o = window['SZMP' + i]; s['mp' + i] = !!(o && o.ok === true); }
    var api = {}; ${JSON.stringify(MP0_API)}.forEach(function(n){ api[n] = typeof window[n]; }); return { s: s, api: api }; })()`;
function judgeSentinel(x){
    const miss = Object.entries(x.s).filter(([k, v]) => !v).map(([k]) => k);
    row('G10 site', '스텁 센티널 SZMP1~8.ok', miss.length ? '없음: ' + miss.join(' ') : '8개 전부', null, '8개', miss.length ? 'FAIL' : 'PASS');
    const am = Object.entries(x.api).filter(([k, v]) => v === 'undefined').map(([k]) => k);
    row('G10 site', 'MP0 API (' + MP0_API.length + '개)', am.length ? '없음: ' + am.join(' ') : '전부 있음', null, '전부', am.length ? 'FAIL' : 'PASS');
}

/* ibot 중앙값 부트스트랩 95% CI (결정적 난수) */
function bootCI(ts, B = 1000, mean = false){
    if(!ts.length) return [null, null];
    let a = 0x9e3779b9; const rnd = () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), a | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
    const n = ts.length, meds = new Float64Array(B), buf = new Float64Array(n);
    for(let b = 0; b < B; b++){
        if(mean){ let sum = 0; for(let i = 0; i < n; i++) sum += ts[(rnd() * n) | 0]; meds[b] = sum / n; continue; }
        for(let i = 0; i < n; i++) buf[i] = ts[(rnd() * n) | 0]; buf.sort(); meds[b] = buf[Math.floor(n * 0.5)];   /* q(ts, 0.5) 와 같은 정의 */
    }
    meds.sort();
    return [r1(meds[Math.floor(B * 0.025)]), r1(meds[Math.floor(B * 0.975)])];
}
const ibotN = (base, k) => Math.max(8, r1(2 * ((base && base.runDiff && base.runDiff[k]) || 0)));

/* ================= soak / assets ================= */
async function runSoak(base){
    return withEdge({ w: 412, h: 915, dsf: 2.625, mobile: true }, async (e) => {
        await e.open(gameUrl(base, 'ko'), 1500);
        const r = await e.ev('__G.soak({step:16.667, secs:' + SOAK_SECS + '})', 3600000);
        const pe = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs('soak', e, pe.concat(r.errs));
        /* localStorage 차단 모드 */
        await e.send('Page.addScriptToEvaluateOnNewDocument', { source: 'try{Object.defineProperty(window,"localStorage",{get:function(){throw new Error("blocked")}})}catch(e){}' });
        await e.open(gameUrl(base, 'ko'), 1500);
        const t = await e.ev('__G.tour({step:16.667, frames:30})', 300000);
        const pe2 = await e.ev('(window.__E||[]).slice(0,8)');
        collectErrs('soak-noLS', e, pe2.concat(t.errs));
        return { ...r, noLsErrs: t.errs.length + pe2.length, noLsSample: t.errs.concat(pe2).slice(0, 3) };
    });
}
async function runAssets(base){
    return withEdge({ w: 412, h: 915, dsf: 2.625, mobile: true }, async (e) => {
        await e.open(gameUrl(base, 'ko'), 3000);
        const first = await e.ev('performance.getEntriesByType("resource").map(function(x){return [x.name.replace(location.origin,""), Math.round((x.transferSize||x.encodedBodySize||0)/1024), x.initiatorType]})');
        const nav = await e.ev('(function(){var n=performance.getEntriesByType("navigation")[0];return Math.round((n.transferSize||n.encodedBodySize)/1024)})()');
        await e.ev('__G.tour({step:16.667, frames:30})', 300000);
        await sleep(2500);
        const after = await e.ev('performance.getEntriesByType("resource").map(function(x){return [x.name.replace(location.origin,""), Math.round((x.transferSize||x.encodedBodySize||0)/1024), x.initiatorType]})');
        const sum = (a) => a.reduce((s, x) => s + x[1], 0);
        return { htmlKB: nav, firstKB: sum(first) + nav, tourKB: sum(after) - sum(first), firstTop: first.sort((a, b) => b[1] - a[1]).slice(0, 8), n: after.length };
    });
}

/* ================= 정리·잔존 확인 ================= */
function leftovers(){
    let procs = [];
    try{
        const ps = "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | Where-Object { $_.CommandLine -like '*" + path.join(PROF_DIR, PROF_PREFIX).replace(/'/g, "''") + "_" + process.pid + "_*' } | ForEach-Object { $_.ProcessId }";
        procs = execFileSync('powershell', ['-NoProfile', '-Command', ps], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).split(/\s+/).filter(Boolean);
    }catch(_){}
    for(const p of procs) killTree(p);
    const dirs = fs.existsSync(PROF_DIR) ? fs.readdirSync(PROF_DIR).filter(d => d.startsWith(PROF_PREFIX + '_' + process.pid + '_')) : [];
    for(const d of dirs){ try{ fs.rmSync(path.join(PROF_DIR, d), { recursive: true, force: true }); }catch(_){} }
    const dirs2 = fs.existsSync(PROF_DIR) ? fs.readdirSync(PROF_DIR).filter(d => d.startsWith(PROF_PREFIX + '_' + process.pid + '_')) : [];
    return { procs: procs.length, dirs: dirs2.length };
}
let CLEANED = false;
async function cleanupAll(){
    if(CLEANED) return; CLEANED = true;
    for(const e of [...LIVE]) await e.close();
    stopServer();
    await sleep(500);
    return leftovers();
}
process.on('SIGINT', async () => { say('중단 — 정리 중'); await cleanupAll(); process.exit(130); });

/* ================= main ================= */
const t0 = Date.now();
let exitCode = 0;
const CUR = { meta: { date: new Date().toISOString(), root: ROOT, quick: QUICK, cmds: CMDS } };
let BASE = null;
try{ BASE = JSON.parse(fs.readFileSync(BASE_FILE, 'utf8')); }catch(_){ BASE = null; }
try{
    fs.mkdirSync(OUT, { recursive: true });
    try{ CUR.meta.commit = execFileSync('git', ['-C', ROOT, 'rev-parse', '--short', 'HEAD'], { encoding: 'utf8' }).trim(); CUR.meta.dirty = !!execFileSync('git', ['-C', ROOT, 'status', '--porcelain', '--', 'public/games/dodge/index.html'], { encoding: 'utf8' }).trim(); }catch(_){}
    const html = fs.readFileSync(GAME_FILE, 'utf8');
    CUR.meta.htmlBytes = Buffer.byteLength(html);
    say('root ' + ROOT + ' · port ' + PORT + ' · 명령 ' + CMDS.join(' ') + ' · 기준선 ' + (BASE ? path.relative(ROOT, BASE_FILE) + ' (' + (BASE.meta && BASE.meta.commit) + ')' : '없음'));

    /* 정적 검사 — 서버 불필요 */
    if(CMDS.includes('tm')){
        const hits = staticScan(html), ft = fillTextScan(html);
        CUR.tmStatic = { hits: hits.length, fillText: ft.length, sample: hits.slice(0, 12), ftSample: ft };
        row('G5 tm', '소스 fillText 리터럴 상표', ft.length ? ft.map(h => 'L' + h.line + ' ' + h.text).join(' | ') : 0, BASE && BASE.tmStatic ? BASE.tmStatic.fillText : null, '0', ft.length ? 'FAIL' : 'PASS');
        row('G5 tm', '소스 문자열·HTML 상표 (주석 제외)', hits.length ? hits.slice(0, 4).map(h => 'L' + h.line + ' ' + h.text.slice(0, 40)).join(' | ') : 0, BASE && BASE.tmStatic ? BASE.tmStatic.hits : null, '0', hits.length ? 'FAIL' : 'PASS');
    }
    if(CMDS.includes('i18n')){
        const st = i18nStatic(html);
        CUR.i18nStatic = st;
        for(const [name, v] of Object.entries(st)){
            const b = BASE && BASE.i18nStatic && BASE.i18nStatic[name];
            if(v.err){ row('G4 i18n', name, v.err, null, '-', 'INFO'); continue; }
            const lim = b && !b.err ? b.missing : 0;
            pre(row('G4 i18n', name + ' 누락', v.missing + ' (잎 ' + v.leaves + ')', b ? (b.missing != null ? b.missing : b.err) : null, '≤' + lim + (lim ? ' (기준선)' : ''), !b ? (v.missing ? 'WARN' : 'PASS') : (v.missing <= lim ? (v.missing ? 'WARN' : 'PASS') : 'FAIL'), v.sample.join(' ').slice(0, 100)), b && b.missing === v.missing);
        }
        for(const req of ['SZ_STORY_I18N', 'ZONE_NAMES_I18N']) if(!st[req]) row('G4 i18n', req, '아직 없음', null, 'P3 이후 필수', 'INFO');
    }
    /* 불변 식별자 (G10 일부) */
    {
        const inv = ["'szx_best_ms'", "'szx_nick'", "'szx_pid'", "'szx_race'", "'lp_spacez_vib'", "'dodge_steer'", "'dodge_hand'", "gameKey:", "'dodge_leaderboard'", "'record_dodge_attempt'", 'id="gravBtn"', 'id="satBtn"', 'id="itemSlot0"', 'id="itemSlot1"', 'id="itemSlot2"', 'id="rewardSlot0"', "get('ch')"];
        const miss = inv.filter(s => !html.includes(s));
        /* 펜스 7개 — 열고 닫는 표식이 한 번씩, 순서대로 */
        for(const f of ['flags', 'rng', 'zonescript', 'story', 'meta', 'art', 'race']){
            const o = html.split('/*<sz:mod:' + f + '>*/').length - 1, c = html.split('/*</sz:mod:' + f + '>*/').length - 1;
            if(o !== 1 || c !== 1 || html.indexOf('/*<sz:mod:' + f + '>*/') > html.indexOf('/*</sz:mod:' + f + '>*/')) miss.push('펜스 ' + f + '(' + o + '/' + c + ')');
        }
        /* MP0 — 명작화 스텁 펜스: JS 8 + 하위(mp4:song·mp8a·mp8b) · CSS 8 · HTML(mp6·mp8) · 게이트 자기 펜스 8 */
        const once = (src, o, c) => { const a = src.split(o).length - 1, b = src.split(c).length - 1; return a === 1 && b === 1 && src.indexOf(o) < src.indexOf(c); };
        const mpF = [];
        for(let n = 1; n <= 8; n++){
            mpF.push(['/*<sz:mod:mp' + n + '>*/', '/*</sz:mod:mp' + n + '>*/'], ['/*<sz:css:mp' + n + '>*/', '/*</sz:css:mp' + n + '>*/']);
        }
        mpF.push(['/*<sz:mod:mp4:song>*/', '/*</sz:mod:mp4:song>*/'], ['/*<sz:mod:mp8a>*/', '/*</sz:mod:mp8a>*/'], ['/*<sz:mod:mp8b>*/', '/*</sz:mod:mp8b>*/'],
            ['<!--<sz:html:mp6>-->', '<!--</sz:html:mp6>-->'], ['<!--<sz:html:mp8>-->', '<!--</sz:html:mp8>-->']);
        for(const [o, c] of mpF) if(!once(html, o, c)) miss.push('펜스 ' + o.replace(/[/*<>!-]/g, ''));
        const gsrc = fs.readFileSync(new URL(import.meta.url), 'utf8');
        for(let n = 1; n <= 8; n++){ const o = '/*<gate:mp' + n + '>*/', c = '/*</gate:mp' + n + '>*/'; if(!once(gsrc, o, c)) miss.push('게이트 펜스 gate:mp' + n); }
        if(!fs.existsSync(path.join(ROOT, 'public', 'games', 'dodge', 'flags.json'))) miss.push('flags.json');
        const bad = ['G-W91WWVNLD6', 'notmeplz', '말머리 성운까지'].filter(s => html.includes(s));
        CUR.invariants = { missing: miss, forbidden: bad };
        row('G10 site', '불변 키·RPC·DOM id·펜스', miss.length ? '없음: ' + miss.join(' ') : '전부 있음', null, '전부 있음', miss.length ? 'FAIL' : 'PASS');
        row('G10 site', '금지 문자열', bad.length ? bad.join(' ') : 0, null, '0', bad.length ? (bad.every(s => s === '말머리 성운까지') ? 'WARN' : 'FAIL') : 'PASS', bad.includes('말머리 성운까지') ? '말머리 문구는 P3 과제' : '');
    }

    const needServer = CMDS.some(c => ['det', 'perf', 'sweep', 'layout', 'tm', 'i18n', 'fx0', 'bot', 'ibot', 'soak', 'assets', 'beamdrain',
        'hitpath', 'noshake', 'restart', 'audioctx', 'latency', 'boot', 'flags0', 'startshot', 'gl0'].includes(c) || (EXT_CMDS[c] && EXT_CMDS[c].server !== false));
    if(needServer){
        const base = await startServer();
        say('서버 ' + base + ' (cwd ' + ROOT + ')');
        if(CMDS.includes('det')){ CUR.det = await runDet(base); judgeDet(CUR.det, BASE && BASE.det); }
        if(CMDS.includes('perf')){
            const zones = A.zones ? String(A.zones).split(',').map(Number) : (QUICK ? [0, 1, 4, 9, 17] : [0, 1, 2, 4, 6, 9, 13, 17, 22, 27]);
            CUR.perf = await runPerf(base, zones, 'perf'); judgePerf(CUR.perf, BASE && BASE.perf, 'perf');
        }
        if(CMDS.includes('sweep')){
            const nZ = 31; const zones = A.zones ? String(A.zones).split(',').map(Number) : Array.from({ length: nZ }, (_, i) => i);
            CUR.sweep = await runPerf(base, zones, 'sweep'); judgePerf(CUR.sweep, BASE && BASE.sweep, 'sweep');
        }
        if(CMDS.includes('layout')){ CUR.layout = await runLayout(base); judgeLayout(CUR.layout, BASE && BASE.layout); }
        if(CMDS.includes('tm') || CMDS.includes('i18n')){
            CUR.text = await runText(base);
            for(const [L, v] of Object.entries(CUR.text)){
                const b = BASE && BASE.text && BASE.text[L];
                if(CMDS.includes('tm')) row('G5 tm', L + ' 화면 글자 상표 (DOM ' + v.nDom + '·캔버스 ' + v.nCanvas + ')', v.brand.length ? v.brand.slice(0, 3).join(' | ') : 0, b ? b.brand.length : null, '0', v.brand.length ? 'FAIL' : 'PASS');
                if(CMDS.includes('i18n') && L !== 'ko') pre(row('G4 i18n', L + ' 화면 한글 잔존', v.hangul.length, b ? b.hangul.length : null, '≤ 기준선 (목표 0)', (b ? v.hangul.length <= b.hangul.length : true) ? (v.hangul.length ? 'WARN' : 'PASS') : 'FAIL', v.hangul.slice(0, 3).join(' | ').slice(0, 110)), b && b.hangul.length === v.hangul.length);
            }
        }
        if(CMDS.includes('fx0')){
            CUR.fx0 = await runFx0(base);
            const f = CUR.fx0.fx0;
            row('G8 fx0', '?fx=0 31존 순회 에러', f.errs, null, '0', f.errs ? 'FAIL' : 'PASS', f.sample.join(' | ').slice(0, 120));
            row('G8 fx0', 'SZ_FLAGS (fx0 / 기본)', JSON.stringify(f.flags) + ' / ' + JSON.stringify(CUR.fx0.fx1.flags), null, 'fx:false / fx:true', (f.flags && f.flags.fx === false && CUR.fx0.fx1.flags && CUR.fx0.fx1.flags.fx === true) ? 'PASS' : 'FAIL');
            if(CUR.fx0.fx1.sentinel) judgeSentinel(CUR.fx0.fx1.sentinel);
        }
        /* ── MP0 명령 ── */
        if(CMDS.includes('hitpath')){ CUR.hitpath = await runHitpath(base); judgeHitpath(CUR.hitpath, BASE && BASE.hitpath); }
        if(CMDS.includes('noshake')){ CUR.noshake = await runNoshake(base); judgeNoshake(CUR.noshake, BASE && BASE.noshake); }
        if(CMDS.includes('restart')){ CUR.restart = await runRestart(base); judgeRestart(CUR.restart, BASE && BASE.restart); }
        if(CMDS.includes('audioctx')){ CUR.audioctx = await runAudioCtx(base); judgeAudioCtx(CUR.audioctx, BASE && BASE.audioctx); }
        if(CMDS.includes('latency')){ CUR.latency = await runLatency(base); judgeLatency(CUR.latency, BASE && BASE.latency); }
        if(CMDS.includes('boot')){ CUR.boot = await runBoot(base); judgeBoot(CUR.boot, BASE && BASE.boot); }
        if(CMDS.includes('flags0')){ CUR.flags0 = await runFlags0(base); judgeFlags0(CUR.flags0, BASE); }
        if(CMDS.includes('startshot')){ CUR.startshot = await runStartshot(base); judgeStartshot(CUR.startshot, BASE && BASE.startshot); }
        if(CMDS.includes('gl0')) row('G21 gl0', 'GL 끔 순회 (자리)', 'MP8b 가 채운다', null, '-', 'INFO');
        for(const c of CMDS) if(EXT_CMDS[c]){ CUR[c] = await EXT_CMDS[c].run(base); if(EXT_CMDS[c].judge) EXT_CMDS[c].judge(CUR[c], BASE && BASE[c]); }
        if(CMDS.includes('beamdrain')){ CUR.beamdrain = await runBeamDrain(base); judgeBeamDrain(CUR.beamdrain); }
        if(CMDS.includes('bot')){ CUR.bot = await runBot(base); judgeBot(CUR.bot, BASE && BASE.bot); }
        if(CMDS.includes('ibot')){ CUR.ibot = await runIBot(base); judgeIBot(CUR.ibot, BASE && BASE.ibot); }
        if(CMDS.includes('soak')){
            CUR.soak = await runSoak(base);
            const s = CUR.soak;
            row('G6 soak', SOAK_SECS + 's 무작위 입력 에러', s.errs.length + s.E.length, null, '0', s.errs.length + s.E.length ? 'FAIL' : 'PASS', s.errs.concat(s.E).slice(0, 2).join(' | '));
            const h = s.heap.map(x => x[1]).filter(x => x > 0); const third = Math.max(1, Math.floor(h.length / 3));
            const early = Math.max(...h.slice(0, third)), late = Math.max(...h.slice(-third));
            row('G6 soak', '힙 상한 (앞 1/3 → 뒤 1/3)', early + '→' + late + 'MB', null, '≤ ×1.3', late <= early * 1.3 + 2 ? 'PASS' : 'FAIL');
            row('G6 soak', 'localStorage 차단 모드 에러', s.noLsErrs, null, '0', s.noLsErrs ? 'FAIL' : 'PASS', s.noLsSample.join(' | ').slice(0, 100));
        }
        if(CMDS.includes('assets')){
            CUR.assets = await runAssets(base);
            const b = BASE && BASE.assets;
            row('G7 assets', '첫 로드 전송량', CUR.assets.firstKB + 'KB', b ? b.firstKB + 'KB' : null, b ? '≤' + (b.firstKB + 250) + 'KB (+250)' : '-', b ? (CUR.assets.firstKB <= b.firstKB + 250 ? 'PASS' : 'FAIL') : 'INFO');
            row('G7 assets', '존 순회 추가 전송량', CUR.assets.tourKB + 'KB', b ? b.tourKB + 'KB' : null, b ? '≤' + (b.tourKB + 2048) + 'KB' : '-', b ? (CUR.assets.tourKB <= b.tourKB + 2048 ? 'PASS' : 'FAIL') : 'INFO');
        }
        /* 에러 합계 */
        const cerrB = BASE && BASE.errors ? BASE.errors.cerr : null;
        CUR.errors = { exc: ERR.exc.length, pageE: ERR.pageE.length, cerr: ERR.cerr.length, sample: ERR.exc.concat(ERR.pageE).slice(0, 8), cerrSample: [...new Set(ERR.cerr.map(s => s.replace(/^[^:]+: /, '')))].slice(0, 8) };
        row('errors', 'JS 예외 (모든 세션)', ERR.exc.length + ERR.pageE.length, BASE && BASE.errors ? BASE.errors.exc + BASE.errors.pageE : null, '0', ERR.exc.length + ERR.pageE.length ? 'FAIL' : 'PASS', CUR.errors.sample.slice(0, 3).join(' | ').slice(0, 140));
        row('errors', 'console.error (모든 세션)', ERR.cerr.length, cerrB, '0', ERR.cerr.length ? 'FAIL' : 'PASS', CUR.errors.cerrSample.slice(0, 3).join(' | ').slice(0, 140));
    }
}catch(e){
    row('gate', '실행 오류', String(e && e.stack || e).split('\n').slice(0, 3).join(' | ').slice(0, 200), null, '', 'FAIL');
}finally{
    const lo = await cleanupAll();
    row('G11 cleanup', '게이트가 띄운 msedge 잔존 / 프로필 폴더 잔존', (lo ? lo.procs : 0) + ' / ' + (lo ? lo.dirs : 0), null, '0 / 0', lo && (lo.procs || lo.dirs) ? 'FAIL' : 'PASS');
}

/* ---------------- 출력 ---------------- */
const W = { gate: 11, check: 44, value: 34, base: 22, limit: 26 };
const cut = (s, n) => { s = fmt(s); let w = 0, o = ''; for(const ch of s){ const cw = /[\u1100-\uFFDC]/.test(ch) ? 2 : 1; if(w + cw > n){ o += '…'; w++; break; } o += ch; w += cw; } return o + ' '.repeat(Math.max(0, n - w)); };
console.log('\n' + cut('GATE', W.gate) + ' ' + cut('CHECK', W.check) + ' ' + cut('VALUE', W.value) + ' ' + cut('BASELINE', W.base) + ' ' + cut('LIMIT', W.limit) + ' STATUS');
console.log('-'.repeat(W.gate + W.check + W.value + W.base + W.limit + 12));
const hidden = VERBOSE ? [] : ROWS.filter(r => r.pre);
for(const r of ROWS){
    if(!VERBOSE && r.pre) continue;
    console.log(cut(r.gate, W.gate) + ' ' + cut(r.check, W.check) + ' ' + cut(r.value, W.value) + ' ' + cut(r.base, W.base) + ' ' + cut(r.limit, W.limit) + ' ' + r.status + (r.note ? '  — ' + r.note : ''));
}
const nF = ROWS.filter(r => r.status === 'FAIL').length, nW = ROWS.filter(r => r.status === 'WARN').length, nP = ROWS.filter(r => r.status === 'PASS').length;
console.log('-'.repeat(W.gate + W.check + W.value + W.base + W.limit + 12));
if(hidden.length) console.log('(기준선과 같은 기존 문제 WARN ' + hidden.length + '건은 접음 — --verbose 로 표시. 전부 gate_result.json 에 있음)');
console.log('결과: ' + (nF ? 'FAIL' : 'PASS') + '  (PASS ' + nP + ' · WARN ' + nW + ' · FAIL ' + nF + ')  ' + Math.round((Date.now() - t0) / 1000) + 's  · 산출물 ' + OUT);
if(nF) exitCode = 1;
CUR.rows = ROWS;
try{ fs.writeFileSync(path.join(OUT, 'gate_result.json'), JSON.stringify(CUR, null, 1)); }catch(_){}
if(A.json){ try{ fs.writeFileSync(path.resolve(A.json), JSON.stringify(CUR, null, 1)); }catch(_){} }
if(A['write-baseline']){
    let B = {}; try{ B = JSON.parse(fs.readFileSync(BASE_FILE, 'utf8')); }catch(_){}
    const keep = { ...CUR }; delete keep.rows;
    /* MP0 — ibot 실행 간 차이(runDiff·N)는 --ibot-sets 2 로 잰 값을 다음 기록에도 넘긴다 */
    if(keep.ibot && !keep.ibot.runDiff && B.ibot && B.ibot.runDiff){ keep.ibot.runDiff = B.ibot.runDiff; keep.ibot.N = B.ibot.N; keep.ibot.sets = B.ibot.sets; keep.ibot.runDiffMean = B.ibot.runDiffMean; }
    for(const k of Object.keys(keep)) if(k !== 'meta') B[k] = keep[k];
    B.meta = { ...(B.meta || {}), ...CUR.meta, updated: new Date().toISOString(), sections: [...new Set([...(B.meta && B.meta.sections || []), ...Object.keys(keep).filter(k => k !== 'meta')])] };
    fs.writeFileSync(BASE_FILE, JSON.stringify(B, null, 1));
    say('기준선 기록: ' + BASE_FILE + ' (' + Object.keys(keep).filter(k => k !== 'meta').join(', ') + ')');
}
process.exit(exitCode);
