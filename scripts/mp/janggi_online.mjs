/* 장기·象棋 — 온라인(Rooms v2 턴제) 시험 J1~J17: 방장 1 + 게스트 1 + 관전 1 (로컬 릴레이, 실제 게임 페이지)
   node scripts/mp/janggi_online.mjs   (포트 PORT=8692 · 스크린샷 MP_SHOTS=<폴더> · 프로필 MP_SCRATCH)
   레지스트리(lpGames.js)에 janggi 가 아직 없으면 문서 앞 스크립트로 LpGames 에 janggi(v2·turn·2석·관전) 항목을 덧붙여 시험한다
   (메인 통합 뒤에는 실제 등록 줄이 같은 값을 준다 — 덧붙임은 이미 있으면 아무 것도 안 한다). */
import fs from 'node:fs';
import path from 'node:path';
const WT = new URL('./', import.meta.url).href;
const { startRelay } = await import(WT + 'relay.mjs');
const { Edge, sleep, ok, R } = await import(WT + 'h.mjs');
const { gamePage, inviteToLocal, eqAll } = await import(WT + 'turn_h.mjs');
const OUT = process.env.MP_SHOTS || null; if (OUT) fs.mkdirSync(OUT, { recursive: true });
const REG = `(function(){var real;try{Object.defineProperty(window,'LpGames',{configurable:true,get:function(){return real},set:function(v){
  if(v&&v.get&&!v.__jg&&!v.get('janggi')){var e={id:'janggi',path:'/games/janggi/',cat:'board',icon:'/assets/tiles/toy-janggi.webp',name:{ko:'장기',en:'Janggi & Xiangqi',ja:'チャンギ・シャンチー',zh:'象棋'},
    mp:{kind:'turn',v:'v2',v1:false,adapter:'turn',seats:[2,2],max:12,lateJoin:'spectate',migr:true,hidden:false,trust:'A'}};
    var g=v.get,h=v.has,p=v.path,u=v.url,n=v.name,vv=v.v,all=v.all,mp=v.mp;
    v.get=function(id){return id==='janggi'?e:g(id)};v.has=function(id){return id==='janggi'||h(id)};v.isId=function(id){return id==='janggi'||h(id)};
    v.path=function(id){return id==='janggi'?e.path:p(id)};v.url=function(id,c){if(id==='janggi'){var cc=String(c||'').replace(/[^0-9A-Z]/g,'');return e.path+(cc?'?r='+cc:'')}return u(id,c)};
    v.name=function(id,l){return id==='janggi'?(e.name[l||'en']||e.name.en):n(id,l)};v.v=function(id){return id==='janggi'?'v2':vv(id)};
    v.all=function(){return all().concat([e])};v.mp=function(ver){var r=mp(ver);if(!ver||ver==='v2')r=r.concat([e]);return r};v.__jg=1}
  real=v}})}catch(_){}})();`;
const relay = await startRelay({ port: +(process.env.PORT || 8692) });
const E = new Edge(relay.base);
await E.start();
const hook = '__janggi', k = hook + '.K';
const shot = async (P, name) => { if (!OUT) return; try { const r = await P.c.send('Page.captureScreenshot', { format: 'png' }); fs.writeFileSync(path.join(OUT, 'jg_' + name + '.png'), Buffer.from(r.data, 'base64')); } catch (_) {} };
async function mk(label, nick, lang, w = 360, h = 740) {
    const P = await gamePage(E, label, { nick, lang, pre: REG });
    await P.c.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: true });
    return P;
}
let H, g1, sp, all = [];
const st = (P) => P.ev(`JSON.stringify(${hook}.state())`).then(JSON.parse);
/* 차례인 사람이 화면 경로(tryMove — 합법수 검사·먼저 보이기·전송)로 둔다. pick: 합법수 중 고르기 */
async function play(P, pick) {
    await P.wait(`${hook}.canAct()`, 20000).catch(() => { throw new Error(P.label + ' cannot act'); });
    const s = await st(P), n0 = s.mv.length;
    const lg = await P.ev(`${hook}.legal()`);
    const real = lg.filter(m => m !== 16383);
    const m = pick ? pick(real, s) : real[(n0 * 7) % real.length];
    await P.ev(`${hook}.move(${m})`);
    await eqAll(all, `${hook}.state().mv.length===${n0 + 1}&&!${hook}.state().busy`, 12000);
    return m;
}
try {
    H = await mk('jH', 'Ann', 'ko');
    await H.nav('/games/janggi/index.html');
    await H.wait('!!window.' + hook, 15000);
    await H.ev(`${hook}.v2Create()`);
    await H.wait(`${hook}.v2on&&${k}.room.isHost`, 20000);
    const url = await H.ev(`${k}.inviteUrl()`);
    ok('J1', /\/games\/janggi\/\?r=[A-Z0-9]{6}/.test(url), '방 만들기 → 초대 링크', url.replace(/#.*/, '#…'));
    g1 = await mk('jG', 'Bob', 'en');
    await g1.nav(inviteToLocal(url, E.base));
    await g1.wait(`window.${hook}&&${hook}.v2on`, 25000);
    sp = await mk('jS', 'Cara', 'zh', 320, 568);
    await sp.nav(inviteToLocal(url, E.base));
    await sp.wait(`window.${hook}&&${hook}.v2on`, 25000);
    all = [H, g1, sp];
    let eq = await eqAll(all, `${k}.S().roster.map(m=>m.r+':'+(m.seat==null?'-':m.seat)).sort().join(',')`);
    ok('J2', eq.ok && /host:0/.test(eq.v) && /player:1/.test(eq.v) && /spec:-/.test(eq.v), '링크 참가: 2석 + 관전 1 · 명단 동일', eq.ok ? eq.v : eq.vals);
    /* 방장 옵션: 규칙 장기, 방장 진영 = 한(후수 'b'), 상차림, 턴 시간 */
    const r0 = await H.ev(`${k}.opts().rule`), s0 = await H.ev(`${k}.opts().side`);
    await H.ev(`${k}.setOpt('side','b')`); await H.ev(`${k}.setOpt('fCho',0)`); await H.ev(`${k}.setOpt('fHan',3)`); await H.ev(`${k}.setOpt('turnSec',30)`); await sleep(500);
    eq = await eqAll(all, `${k}.S().opts.side+':'+${k}.S().opts.fCho+':'+${k}.S().opts.fHan+':'+${k}.S().opts.turnSec`);
    const gset = await g1.ev(`(()=>{try{${k}.setOpt('side','a');return ${k}.S().opts.side}catch(e){return 'err'}})()`);
    ok('J3', r0 === 'j' && s0 === 'a' && eq.ok && eq.v === 'b:0:3:30' && gset === 'b', '방장 옵션(규칙 기본 장기·진영 한·상차림·30초) 전원 동일 · 게스트는 못 바꿈', { r0, s0, v: eq.v || eq.vals, gset });
    await shot(H, '01_lobby_host'); await shot(g1, '01_lobby_guest'); await shot(sp, '01_lobby_spec_zh');
    const c0 = await H.ev(`${k}.canStart()`);
    await g1.ev(`${k}.ready(true)`); await sleep(600);
    const c1 = await H.ev(`${k}.canStart()`);
    ok('J4', c0 === false && c1 === true, '준비 게이트: 게스트 준비 뒤에만 시작', { c0, c1 });
    await H.ev(`${k}.start()`);
    eq = await eqAll(all, `${k}.S().phase==='playing'&&${hook}.state().mode==='online'&&${hook}.state().v+':'+${hook}.state().f.join('')+':'+${hook}.state().online.phase`, 15000);
    ok('J5', eq.ok && eq.v === 'j:03:play', '시작 → 전원 같은 판(장기 · 초 마상마상 · 한 상마마상)', eq.ok ? eq.v : eq.vals);
    const me = await Promise.all(all.map(p => p.ev(`${hook}.state().online.me`)));
    ok('J6', me[0] === 1 && me[1] === 0 && me[2] === -1, '좌석: 방장 한(후수) · 게스트 초(선수) · 관전자 없음', me);
    await sleep(800); await shot(g1, '02_start_guest'); await shot(H, '02_start_host_flipped');
    /* 6수 — 초(게스트) 먼저 */
    for (let i = 0; i < 6; i++) await play(i % 2 ? H : g1);
    eq = await eqAll(all, `${hook}.state().mv.join(',')`, 8000);
    ok('J7', eq.ok && eq.v.split(',').length === 6, '6수 진행 → 세 화면 수 목록 동일', eq.ok ? eq.v : eq.vals);
    /* 사칭: 관전자의 수 → 거절 */
    const imp = await sp.ev(`(async()=>{const S=${k}.S();return ${k}.room.intent('t',{a:{m:${(6 * 9 + 0) | ((5 * 9 + 0) << 7)},n:S.game.mv.length},tn:S.turn.n,n:'00'.repeat(16)})})()`);
    ok('J8', imp && !imp.ok, '관전자의 수 → 거절', imp);
    /* 불법 수 직접 전송(판 밖·남의 말) → 방장 거절 */
    await g1.wait(`${hook}.canAct()`, 10000);
    const bad = await g1.ev(`${k}.act({m:${0 | (1 << 7)},n:6})`);   /* (0,0) 한 차를 초가 움직이려 함 */
    ok('J9', bad && !bad.ok, '불법 수 직접 전송 → 방장 거절', bad);
    const rem = await H.ev(`${k}.remain()`);
    ok('J10', rem != null && rem > 0 && rem <= 30000, '턴 시간 30초(방장 시계)', rem);
    /* 끊김 → 봇 대행 */
    await g1.c.send('Page.setWebLifecycleState', { state: 'frozen' });
    const t0 = Date.now();
    const botOk = await H.wait(`${hook}.state().mv.length>=7`, 40000).then(() => true).catch(() => false);
    ok('J11', botOk, '응답 없는 자리(앱 멈춤) → 봇이 대신 둔다(합법수)', { ms: Date.now() - t0 });
    await g1.c.send('Page.setWebLifecycleState', { state: 'active' });
    await g1.show();
    eq = await eqAll(all, `${hook}.state().mv.join(',')`, 25000);
    ok('J12', eq.ok, '재접속 → 같은 판으로 복귀(세 화면 동일)', eq.ok ? eq.v.split(',').length + '수' : eq.vals);
    await sleep(500); await shot(sp, '03_mid_spec');
    /* 다음 차례인 사람이 기권 */
    let s = await st(H);
    const resigner = s.stm === 1 ? H : g1, winner = s.stm === 1 ? 0 : 1;
    await resigner.ev(`${k}.act({rs:1})`);
    eq = await eqAll(all, `${hook}.state().over&&(${hook}.state().res.why+':'+${hook}.state().res.w)`, 15000);
    ok('J13', eq.ok && eq.v === 'resign:' + winner, '기권 → 세 화면 모두 같은 결과', eq.ok ? eq.v : eq.vals);
    await sleep(3200);
    const ends = await Promise.all(all.map(p => p.ev(`${hook}.state().end`)));
    ok('J14', ends.every(Boolean), '결과 카드 — 방장·게스트·관전자', ends);
    await shot(g1, '04_result_guest'); await shot(sp, '04_result_spec');
    /* 한 판 더 → 대기실, 진영이 서로 바뀐다 */
    const again = await g1.ev(`document.getElementById('bAgain').hidden`);
    await H.ev(`document.getElementById('bAgain').click()`);
    eq = await eqAll(all, `${k}.S().phase+':'+${k}.S().opts.side`, 10000);
    ok('J15', again === true && eq.ok && eq.v === 'lobby:a', '한 판 더(방장만 버튼) → 대기실 · 방장 진영 한→초로 바뀜', eq.ok ? eq.v : eq.vals);
    /* 象棋로 바꿔 다시 시작 */
    await H.ev(`${k}.setOpt('rule','x')`); await sleep(300);
    await g1.ev(`${k}.ready(true)`); await sleep(600);
    await H.ev(`${k}.start()`);
    eq = await eqAll(all, `${k}.S().phase==='playing'&&${hook}.state().mv.length===0&&${hook}.state().v==='x'&&${hook}.state().online.phase==='play'`, 15000);
    const me2 = await Promise.all(all.map(p => p.ev(`${hook}.state().online.me`)));
    ok('J16', eq.ok && me2[0] === 0 && me2[1] === 1 && me2[2] === -1, '다시 시작(象棋) → 빈 판 · 방장 紅 · 게스트 黑', { me2, eq: eq.ok });
    await play(H); await play(g1); await play(H);
    await sleep(500); await shot(g1, '05_xiangqi_guest');
    await g1.reload2();
    const back = await g1.wait(`window.${hook}&&${hook}.v2on&&${hook}.state().mv.length===3&&${hook}.state().online&&${hook}.state().online.me===1`, 30000).then(() => true).catch(() => false);
    ok('J17', back, '게스트 새로고침 → 같은 판·같은 자리로 복귀');
} catch (e) { ok('RUN', false, 'crashed', String(e && e.stack || e).slice(0, 700)); }
for (const p of all) { if (p && p.exc && p.exc.length) ok('EXC', false, p.label + ' 예외', p.exc.slice(0, 4).join(' || ')); }
await E.stop(); await relay.stop();
const pass = R.rows.filter(r => r.pass).length;
console.log('\n' + pass + ' pass / ' + (R.rows.length - pass) + ' fail');
process.exit(R.rows.every(r => r.pass) ? 0 : 1);
