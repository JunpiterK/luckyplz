/* 오목 — 온라인(Rooms v2 턴제) 시험 M1~M18: 방장 1 + 게스트 1 + 관전 1 (로컬 릴레이, 실제 게임 페이지)
   node scripts/mp/omok_online.mjs   (포트 PORT=8682 · 스크린샷 MP_SHOTS=<폴더> · 프로필 MP_SCRATCH)
   레지스트리(lpGames.js)에 omok 가 아직 없으면 문서 앞 스크립트로 LpGames 에 omok(v2·turn·2석·관전) 항목을 덧붙여 시험한다
   (메인 통합 뒤에는 실제 등록 줄이 같은 값을 준다 — 덧붙임은 이미 있으면 아무 것도 안 한다). */
import fs from 'node:fs';
import path from 'node:path';
const WT = new URL('./', import.meta.url).href;
const { startRelay } = await import(WT + 'relay.mjs');
const { Edge, sleep, ok, R } = await import(WT + 'h.mjs');
const { gamePage, inviteToLocal, eqAll } = await import(WT + 'turn_h.mjs');
const OUT = process.env.MP_SHOTS || null; if (OUT) fs.mkdirSync(OUT, { recursive: true });
const J = JSON.stringify;
const REG = `(function(){var real;try{Object.defineProperty(window,'LpGames',{configurable:true,get:function(){return real},set:function(v){
  if(v&&v.get&&!v.__om&&!v.get('omok')){var e={id:'omok',path:'/games/omok/',cat:'board',icon:'/assets/tiles/toy-omok.webp',name:{ko:'오목',en:'Gomoku',ja:'五目並べ',zh:'五子棋'},
    mp:{kind:'turn',v:'v2',v1:false,adapter:'turn',seats:[2,2],max:12,lateJoin:'spectate',migr:true,hidden:false,trust:'A'}};
    var g=v.get,h=v.has,p=v.path,u=v.url,n=v.name,vv=v.v,all=v.all,mp=v.mp;
    v.get=function(id){return id==='omok'?e:g(id)};v.has=function(id){return id==='omok'||h(id)};v.isId=function(id){return id==='omok'||h(id)};
    v.path=function(id){return id==='omok'?e.path:p(id)};v.url=function(id,c){if(id==='omok'){var cc=String(c||'').replace(/[^0-9A-Z]/g,'');return e.path+(cc?'?r='+cc:'')}return u(id,c)};
    v.name=function(id,l){return id==='omok'?(e.name[l||'en']||e.name.en):n(id,l)};v.v=function(id){return id==='omok'?'v2':vv(id)};
    v.all=function(){return all().concat([e])};v.mp=function(ver){var r=mp(ver);if(!ver||ver==='v2')r=r.concat([e]);return r};v.__om=1}
  real=v}})}catch(_){}})();`;
const relay = await startRelay({ port: +(process.env.PORT || 8682) });
const E = new Edge(relay.base);
await E.start();
const hook = '__omok', k = hook + '.K';
const shot = async (P, name) => { if (!OUT) return; try { const r = await P.c.send('Page.captureScreenshot', { format: 'png' }); fs.writeFileSync(path.join(OUT, 'om_' + name + '.png'), Buffer.from(r.data, 'base64')); } catch (_) {} };
async function mk(label, nick, lang, w = 360, h = 740) {
    const P = await gamePage(E, label, { nick, lang, pre: REG });
    await P.c.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: true });
    return P;
}
const N = 15, at = (x, y) => y * N + x;
let H, g1, sp, all = [];
const st = (P) => P.ev(`JSON.stringify(${hook}.state())`).then(JSON.parse);
/* 차례인 사람이 i 에 둔다(화면 경로 — 규칙 검사·전송 포함) */
async function play(P, i, label) {
    await P.wait(`${hook}.canAct()`, 20000).catch(() => { throw new Error((label || P.label) + ' cannot act for ' + i); });
    const n0 = (await st(P)).mv.length;
    await P.ev(`${hook}.place(${i})`);
    await eqAll(all, `${hook}.state().mv.length===${n0 + 1}&&!${hook}.state().busy`, 12000);
}
try {
    H = await mk('oH', 'Ann', 'ko');
    await H.nav('/games/omok/index.html');
    await H.wait('!!window.' + hook, 15000);
    await H.ev(`${hook}.v2Create()`);
    await H.wait(`${hook}.v2on&&${k}.room.isHost`, 20000);
    const url = await H.ev(`${k}.inviteUrl()`);
    ok('M1', /\/games\/omok\/\?r=[A-Z0-9]{6}/.test(url), '방 만들기 → 초대 링크', url.replace(/#.*/, '#…'));
    g1 = await mk('oG', 'Bob', 'en');
    await g1.nav(inviteToLocal(url, E.base));
    await g1.wait(`window.${hook}&&${hook}.v2on`, 25000);
    sp = await mk('oS', 'Cara', 'ja', 320, 568);
    await sp.nav(inviteToLocal(url, E.base));
    await sp.wait(`window.${hook}&&${hook}.v2on`, 25000);
    all = [H, g1, sp];
    let eq = await eqAll(all, `${k}.S().roster.map(m=>m.r+':'+(m.seat==null?'-':m.seat)).sort().join(',')`);
    ok('M2', eq.ok && /host:0/.test(eq.v) && /player:1/.test(eq.v) && /spec:-/.test(eq.v), '링크 참가: 2석 + 관전 1 · 명단 동일', eq.ok ? eq.v : eq.vals);
    /* 흑/백 — 방장 옵션 '방장 돌'(흑·백·랜덤). 방장이 백을 고르면 게스트가 흑 */
    const sd0 = await H.ev(`${k}.opts().side`);
    await H.ev(`${k}.setOpt('side','w')`); await sleep(500);
    eq = await eqAll(all, `${k}.S().opts.side`);
    const gset = await g1.ev(`(()=>{try{${k}.setOpt('side','b');return ${k}.S().opts.side}catch(e){return 'err'}})()`);
    ok('M3', sd0 === 'b' && eq.ok && eq.v === 'w' && gset === 'w', '방장 돌 옵션: 기본 흑 → 백으로 · 전원 동일 · 게스트는 못 바꿈', { sd0, all: eq.v || eq.vals, gset });
    await shot(H, '01_lobby_host'); await shot(g1, '01_lobby_guest'); await shot(sp, '01_lobby_spec_320ja');
    await H.ev(`${k}.setOpt('rule','renju')`); await H.ev(`${k}.setOpt('turnSec',30)`); await sleep(400);
    const c0 = await H.ev(`${k}.canStart()`);
    await g1.ev(`${k}.ready(true)`); await sleep(600);
    const c1 = await H.ev(`${k}.canStart()`);
    ok('M4', c0 === false && c1 === true, '준비 게이트: 게스트 준비 뒤에만 시작', { c0, c1 });
    await H.ev(`${k}.start()`);
    eq = await eqAll(all, `${k}.S().phase==='playing'&&${hook}.state().mode==='online'&&${hook}.state().rule+':'+${hook}.state().N+':'+${hook}.state().online.phase`, 15000);
    ok('M5', eq.ok && eq.v === 'renju:15:play', '시작 → 전원 같은 판(렌주 15줄)', eq.ok ? eq.v : eq.vals);
    const me = await Promise.all(all.map(p => p.ev(`${hook}.state().online.me`)));
    ok('M6', me[0] === -1 && me[1] === 1 && me[2] === 0, '좌석: 방장 백 · 게스트 흑 · 관전자 없음', me);
    await sleep(800); await shot(g1, '02_start_guest');
    /* 흑(게스트) 3-3 모양을 만든다 — 백(방장)은 먼 곳 */
    const seq = [[g1, at(6, 7)], [H, at(0, 0)], [g1, at(8, 7)], [H, at(0, 14)], [g1, at(7, 6)], [H, at(14, 0)], [g1, at(7, 8)], [H, at(14, 14)]];
    for (const [P, i] of seq) await play(P, i);
    eq = await eqAll(all, `${hook}.state().mv.join(',')`, 8000);
    ok('M7', eq.ok && eq.v.split(',').length === 8, '8수 진행 → 세 화면 수 목록 동일', eq.ok ? eq.v : eq.vals);
    /* 사칭: 관전자가 수 보내기 → 거절 */
    const imp = await sp.ev(`(async()=>{const S=${k}.S();return ${k}.room.intent('t',{a:{i:${at(3, 3)},n:S.game.mv.length},tn:S.turn.n,n:'00'.repeat(16)})})()`);
    ok('M8', imp && !imp.ok, '관전자의 수 → 거절', imp);
    /* 렌주 금수: 흑 3-3 자리(H8) — 화면에서 ✕ · 눌러도 안 놓임 · 커널 직접 전송도 방장이 거절 */
    await g1.wait(`${hook}.canAct()`, 10000);
    const forbN = await g1.ev(`${hook}.state().forb`);
    await g1.ev(`${hook}.place(${at(7, 7)})`); await sleep(500);
    const after = await g1.ev(`${hook}.state().mv.length`);
    const direct = await g1.ev(`${k}.act({i:${at(7, 7)},n:8})`);
    ok('M9', forbN >= 1 && after === 8 && direct && !direct.ok && direct.reason === '33', '렌주 흑 3-3: ✕ 표시 · 화면 거절 · 방장 거절(33)', { forbN, after, direct });
    await shot(g1, '03_forbidden_guest');
    /* 턴 시간 */
    const rem = await H.ev(`${k}.remain()`);
    ok('M10', rem != null && rem > 0 && rem <= 30000, '턴 시간 30초(방장 시계)', rem);
    /* 끊김 → 봇 대행: 흑(게스트) 페이지를 얼린다 */
    await g1.c.send('Page.setWebLifecycleState', { state: 'frozen' });
    const t0 = Date.now();
    const botOk = await H.wait(`${hook}.state().mv.length>=9`, 40000).then(() => true).catch(() => false);
    const nine = await H.ev(`${hook}.state().mv[8]`);
    ok('M11', botOk && nine !== at(7, 7), '응답 없는 자리(앱 멈춤) → 봇이 대신 둔다 · 금수 자리는 피함', { ms: Date.now() - t0, i: nine });
    await sleep(600); await shot(H, '04_bot_took_host'); await shot(sp, '04_bot_took_spec');
    /* 재접속 */
    await g1.c.send('Page.setWebLifecycleState', { state: 'active' });
    await g1.show();   /* 폰을 다시 켠 것처럼 — 보임 상태 이벤트 */
    eq = await eqAll(all, `${hook}.state().mv.join(',')`, 25000);
    ok('M12', eq.ok, '재접속 → 같은 판으로 복귀(세 화면 동일)', eq.ok ? eq.v.split(',').length + '수' : eq.vals);
    /* 백 차례면 방장이 한 수 */
    let s = await st(H);
    if (s.turn === -1) await play(H, at(13, 1));
    /* 흑이 13번째 줄에 다섯을 만든다(백은 먼 곳에 흩어 둔다) */
    const row = 12, xs = [2, 3, 4, 5, 6], ws = [at(11, 3), at(13, 3), at(11, 5), at(13, 5)];
    for (let n = 0; n < 5; n++) {
        await g1.wait(`${hook}.canAct()`, 30000);
        await play(g1, at(xs[n], row));
        s = await st(H); if (s.over) break;
        await play(H, ws[n]);
    }
    eq = await eqAll(all, `${hook}.state().over&&${hook}.state().win`, 15000);
    ok('M13', eq.ok && eq.v === 1, '흑 다섯 → 세 화면 모두 흑 승리', eq.ok ? eq.v : eq.vals);
    await sleep(3200);
    const ends = await Promise.all(all.map(p => p.ev(`${hook}.state().end`)));
    ok('M14', ends.every(Boolean), '결과 카드 — 방장·게스트·관전자', ends);
    await shot(g1, '05_result_guest'); await shot(H, '05_result_host'); await shot(sp, '05_result_spec');
    /* 한 판 더 → 대기실, 색이 서로 바뀐다 */
    const again = await g1.ev(`document.getElementById('bAgain').hidden`);
    await H.ev(`document.getElementById('bAgain').click()`);
    eq = await eqAll(all, `${k}.S().phase+':'+${k}.S().opts.side`, 10000);
    ok('M15', again === true && eq.ok && eq.v === 'lobby:b', '한 판 더(방장만 버튼) → 대기실 · 방장 돌 백→흑으로 바뀜', eq.ok ? eq.v : eq.vals);
    await sleep(500); await shot(g1, '06_rematch_lobby_guest');
    await g1.ev(`${k}.ready(true)`); await sleep(600);
    const cs2 = await H.ev(`${k}.canStart()`), ro2 = await H.ev(`JSON.stringify(${k}.S().roster.map(m=>({r:m.r,seat:m.seat,rd:m.rd,c:m.c})))`);
    const st2 = await H.ev(`${k}.start()`);
    if (!st2) console.log('DBG start2', cs2, ro2);
    eq = await eqAll(all, `${k}.S().phase==='playing'&&${hook}.state().mv.length===0&&${hook}.state().online.phase==='play'`, 15000);
    const me2 = await Promise.all(all.map(p => p.ev(`${hook}.state().online.me`)));
    ok('M16', me2[0] === 1 && me2[1] === -1 && me2[2] === 0, '다시 시작 → 빈 판 · 방장 흑 · 게스트 백', me2);
    await play(H, at(7, 7)); await play(g1, at(8, 8)); await play(H, at(8, 6));
    /* 게스트 새로고침 → 자동 복귀 */
    await g1.reload2();
    const back = await g1.wait(`window.${hook}&&${hook}.v2on&&${hook}.state().mv.length===3&&${hook}.state().online&&${hook}.state().online.me===-1`, 30000).then(() => true).catch(() => false);
    ok('M17', back, '게스트 새로고침 → 같은 판·같은 자리로 복귀');
    await play(g1, at(9, 9));
    await H.reload2();
    const hb = await H.wait(`window.${hook}&&${hook}.v2on&&${k}.room.isHost&&${hook}.state().mv.length===4`, 30000).then(() => true).catch(() => false);
    ok('M18', hb, '방장 새로고침 → 방·판 유지');
    await sleep(800); await shot(H, '07_after_reload_host'); await shot(sp, '07_after_reload_spec');
} catch (e) { ok('RUN', false, 'crashed', String(e && e.stack || e).slice(0, 700)); }
for (const p of all) { if (p && p.exc && p.exc.length) ok('EXC', false, p.label + ' 예외', p.exc.slice(0, 4).join(' || ')); }
await E.stop(); await relay.stop();
const pass = R.rows.filter(r => r.pass).length;
console.log('\n' + pass + ' pass / ' + (R.rows.length - pass) + ' fail');
process.exit(R.rows.every(r => r.pass) ? 0 : 1);
