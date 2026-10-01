/* 긁는 제비뽑기 — 같이 보기(Rooms v2 draw) 시험 L1~L12: 방장 1 + 게스트 2 (로컬 릴레이, 실제 게임 페이지)
   node scripts/mp/lots_online.mjs   (포트 PORT=8695 · 스크린샷 MP_SHOTS=<폴더> · 프로필 MP_SCRATCH)
   레지스트리(lpGames.js)에 lots 가 아직 없으면 문서 앞 스크립트로 LpGames 에 lots(v2·draw) 항목을 덧붙여 시험한다
   (메인 통합 뒤에는 실제 등록 줄이 같은 값을 준다 — 덧붙임은 이미 있으면 아무 것도 안 한다). */
import fs from 'node:fs';
import path from 'node:path';
const WT = new URL('./', import.meta.url).href;
const { startRelay } = await import(WT + 'relay.mjs');
const { Edge, sleep, ok, R } = await import(WT + 'h.mjs');
const { gamePage, eqAll } = await import(WT + 'turn_h.mjs');
const OUT = process.env.MP_SHOTS || null; if (OUT) fs.mkdirSync(OUT, { recursive: true });
const REG = `(function(){var real;try{Object.defineProperty(window,'LpGames',{configurable:true,get:function(){return real},set:function(v){
  if(v&&v.get&&!v.__lt&&!v.get('lots')){var e={id:'lots',path:'/games/lots/',cat:'random',icon:'/assets/tiles/toy-lots.webp',name:{ko:'긁는 제비뽑기',en:'Scratch Lots',ja:'スクラッチくじ',zh:'刮刮签'},
    mp:{kind:'draw',v:'v2',v1:false,adapter:'draw',seats:null,max:12,lateJoin:'anytime',migr:true,hidden:false,trust:'A'}};
    var g=v.get,h=v.has,p=v.path,u=v.url,n=v.name,vv=v.v,all=v.all,mp=v.mp;
    v.get=function(id){return id==='lots'?e:g(id)};v.has=function(id){return id==='lots'||h(id)};v.isId=function(id){return id==='lots'||h(id)};
    v.path=function(id){return id==='lots'?e.path:p(id)};v.url=function(id,c){if(id==='lots'){var cc=String(c||'').replace(/[^0-9A-Z]/g,'');return e.path+(cc?'?r='+cc:'')}return u(id,c)};
    v.name=function(id,l){return id==='lots'?(e.name[l||'en']||e.name.en):n(id,l)};v.v=function(id){return id==='lots'?'v2':vv(id)};
    v.all=function(){return all().concat([e])};v.mp=function(ver){var r=mp(ver);if(!ver||ver==='v2')r=r.concat([e]);return r};v.__lt=1}
  real=v}})}catch(_){}})();`;
const relay = await startRelay({ port: +(process.env.PORT || 8695) });
const E = new Edge(relay.base);
await E.start();
const shot = async (P, name) => { if (!OUT) return; try { const r = await P.c.send('Page.captureScreenshot', { format: 'png' }); fs.writeFileSync(path.join(OUT, 'lt_' + name + '.png'), Buffer.from(r.data, 'base64')); } catch (_) {} };
async function mk(label, nick, lang, w = 412, h = 915) {
    const P = await gamePage(E, label, { nick, lang, pre: REG });
    await P.c.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: true });
    await P.c.send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
    return P;
}
const center = (P, sel) => P.ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return null;const r=e.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2,w:r.width,h:r.height,l:r.left,t:r.top}})()`);
async function scratch(P, r, rows, frac, start = 0) {
    const pts = [];
    for (let k = 0; k < rows; k++) {
        const y = r.t + r.h * (start + (frac - start) * (k + .5) / rows);
        const xs = k % 2 ? [r.l + r.w * .95, r.l + r.w * .05] : [r.l + r.w * .05, r.l + r.w * .95];
        for (let s = 0; s <= 10; s++) pts.push({ x: xs[0] + (xs[1] - xs[0]) * s / 10, y });
    }
    await P.c.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [pts[0]] });
    for (const p of pts.slice(1)) { await P.c.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [p] }); await sleep(12); }
    await P.c.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
}
const errs = P => P.exc.concat(P.log.filter(l => /^error/.test(l) && !/supabase\.co|favicon|ERR_|net::|404|Failed to load resource/i.test(l)));
let H, G1, G2, all = [];
try {
    H = await mk('lH', 'Ann', 'ko');
    await H.nav('/games/lots/index.html');
    await H.wait('!!window.LPV2&&!!window.__lots&&getComputedStyle(document.getElementById("onlineBtn")).display!=="none"', 20000);
    await H.ev(`__lots.setCfg({mode:'names',names:['Ann','Bob','Cara','Dan','Eve'],samples:false,preset:'win',rows:[{k:'win',c:1,t:''},{k:'pen',c:1,t:''},{k:'miss',c:3,t:'',f:1}]})`);
    await H.ev(`__lots.setCfg({preset:'custom'})`);
    await H.ev(`LPV2.openRoom()`);
    await H.wait(`!!document.querySelector('.lpr-sheet .lpr-btn.go')`, 20000);
    await H.ev(`document.querySelector('.lpr-sheet .lpr-btn.go').click()`);
    await H.wait(`LPV2._v.room&&LPV2._v.room.isHost`, 20000);
    const inv = await H.ev(`LPV2._v.room.inviteUrl()`);
    const m = /\/r\/([0-9A-Z]{6})(#.*)$/.exec(inv);
    ok('L1', !!m, '방장 방 만들기 → 초대 링크', inv.replace(/#.*/, '#…'));
    const gurl = '/games/lots/index.html?r=' + m[1] + m[2];
    G1 = await mk('lG1', 'Bob', 'en');
    await G1.nav(gurl);
    await G1.wait(`window.LPV2&&LPV2._v.room&&LPV2.guest()`, 30000);
    G2 = await mk('lG2', 'Cara', 'ja', 360, 740);
    await G2.nav(gurl);
    await G2.wait(`window.LPV2&&LPV2._v.room&&LPV2.guest()`, 30000);
    all = [H, G1, G2];
    let eq = await eqAll(all, `LPV2._v.room.roster().map(m=>m.n).sort().join(',')`, 15000);
    ok('L2', eq.ok && eq.v === 'Ann,Bob,Cara', '링크 참가 2명 · 명단 3대 동일', eq.ok ? eq.v : eq.vals);
    /* 게스트 설정 화면 = 방장 설정(읽기 전용) */
    await H.ev(`document.getElementById('setup').dispatchEvent(new Event('change'))`);
    eq = await eqAll(all, `JSON.stringify(__lots.params())`, 12000);
    const guestRO = await G1.ev(`getComputedStyle(document.getElementById('startBtn')).display==='none'&&document.getElementById('nameIn').readOnly`);
    ok('L3', eq.ok && /Eve/.test(eq.v) && guestRO, '게스트 설정 = 방장 설정 · 시작 버튼 숨김 · 입력 읽기 전용', eq.ok ? eq.v.slice(0, 160) : eq.vals);
    await sleep(400); await shot(H, '01_setup_host'); await shot(G1, '01_setup_guest_en');
    /* 공정 추첨 → 같은 판 */
    await H.ev(`document.getElementById('startBtn').click()`);
    eq = await eqAll(all, `(()=>{const B=__lots.B();return B?JSON.stringify(B.res.a)+'#'+B.round:''})()`, 25000);
    ok('L4', eq.ok, '제비 나눠주기 → 세 화면 같은 배정(LpFair 공동 시드)', eq.ok ? eq.v : eq.vals);
    if (!eq.ok) { for (const p of all) console.log(p.label, JSON.stringify(await p.ev(`({ev:LPV2._v.dbg.events.slice(-14),cur:!!LPV2._v.cur})`).catch(e => String(e))).slice(0, 1200)); throw new Error('L4'); }
    await sleep(1500);
    await shot(H, '02_board_host'); await shot(G2, '02_board_guest_ja360');
    const a = JSON.parse(eq.v.split('#')[0]);
    const iBob = 1, iAnn = 0, iDan = 3;
    /* 본인 제비만: 방장은 Bob 제비를 못 긁는다 */
    await H.ev(`__lots.open(${iBob})`); await sleep(400);
    const hw = await H.ev(`({w:__lots.Z().watch,info:document.getElementById('zInfo').textContent,inst:document.getElementById('zInstant').hidden})`);
    await H.ev(`__lots.close(true)`);
    ok('L5', hw.w && hw.inst, '멤버 이름과 같은 제비(Bob)는 방장도 못 긁음(보기만)', hw);
    /* Bob 이 자기 제비를 긁는다 → 손길이 다른 화면에 보인다 */
    await G1.ev(`__lots.open(${iBob})`); await sleep(500);
    const wr = await center(G1, '#bigCard .win');
    await scratch(G1, wr, 3, .4);
    await sleep(700);
    const mir = await Promise.all([H, G2].map(p => p.ev(`({n:__lots.B().strokes[${iBob}].length,c:__lots.B().covN[${iBob}],who:(document.querySelector('.tk[data-i="${iBob}"] .who')||{}).textContent||''})`)));
    const mine = await G1.ev(`__lots.B().covN[${iBob}]`);
    ok('L6', mir.every(x => x.n > 5 && x.c > mine * .7) && mir.every(x => /Bob/.test(x.who)), '긁는 손길 미러링 — 방장·관객 화면의 같은 제비에 긁힌 자국 + ✋Bob 표시', { mine, mir });
    await shot(H, '03_mirror_host'); await shot(G1, '03_mid_guest');
    await scratch(G1, wr, 4, 1, .35);
    eq = await eqAll(all, `__lots.B().rev[${iBob}]===1?'rev':''`, 10000);
    const st = await H.ev(`JSON.stringify(LPV2._v.room.state().game.lots.rev)`);
    ok('L7', eq.ok && /"1":"Bob"/.test(st), 'Bob 이 다 긁음 → 방장 확인(intent rev) → 세 화면 공개', { st });
    await sleep(1200); await shot(G1, '04_reveal_guest'); await shot(G2, '04_reveal_watch');
    /* 방장 자기 제비 한 번에 공개 */
    await H.ev(`__lots.open(${iAnn})`); await sleep(300); await H.ev(`document.getElementById('zInstant').click()`);
    eq = await eqAll(all, `__lots.B().rev[${iAnn}]===1?'rev':''`, 10000);
    ok('L8', eq.ok, '방장 [한 번에 공개] → 모두에게 공개', eq.ok ? 'ok' : eq.vals);
    await sleep(900); await H.ev(`__lots.close(true)`);
    /* 게스트가 남의 제비(Dan, 방에 없음 → 누구나) 공개 시도는 허용, 남의 제비(Ann) 위조 공개는 거절 */
    const forged = await G2.ev(`LPV2._v.room.intent('rev',{r:__lots.B().round,i:${iBob}})`);
    const forged2 = await G2.ev(`(async()=>{const r=await LPV2._v.room.intent('rev',{r:__lots.B().round,i:0});return r})()`);
    ok('L9', forged && forged.ok === false && forged.reason === 'reserved' && forged2 && forged2.ok === false && forged2.reason === 'reserved', 'Cara 가 남의 제비(Bob·Ann) 공개 의도를 보내면 방장이 거절(reserved)', { forged, forged2 });
    /* 다 같이 공개(방장) — 게스트는 못 누름 */
    await G1.ev(`document.getElementById('allBtn').click()`); await sleep(300);
    const gAll = await G1.ev(`!!(__lots.B().allRun)`);
    await H.ev(`document.getElementById('allBtn').click()`);
    await sleep(900); await shot(G2, '05_allrun_guest');
    eq = await eqAll(all, `(()=>{const B=__lots.B();return B&&B.nRev===B.n&&document.getElementById('sum').classList.contains('on')?[...B.rev].join(''):''})()`, 20000);
    ok('L10', !gAll && eq.ok, '게스트 [다 같이 공개] 막힘 · 방장 [다 같이 공개] → 세 화면 모두 공개·결과표', eq.ok ? eq.v : eq.vals);
    await sleep(1500);
    const bd = await Promise.all(all.map(p => p.ev(`(document.querySelector('#sumCard .lpv2-badge')||{}).textContent||''`)));
    ok('L11', bd.every(t => /✓|公正|Fair|공정/.test(t)), '결과표에 공정 배지(목격 집계)', bd);
    await shot(H, '06_sum_host'); await shot(G1, '06_sum_guest_en'); await shot(G2, '06_sum_guest_ja');
    /* 인증서 링크 → 다른 기기에서 검증 + 전부 공개 재생 */
    const cert = await H.ev(`LPV2._t.certLink(LPV2._v.certs[LPV2._v.cur.round])`);
    const X = await mk('lX', 'Zed', 'ko');
    await X.nav(cert.replace(/^https?:\/\/[^/]+/, '').replace('/games/lots/#', '/games/lots/index.html#'));
    await X.wait(`window.LPV2&&LPV2._v.dbg.cert`, 20000);
    const v = await X.ev(`({c:LPV2._v.dbg.cert,ban:(document.querySelector('.lpv2-banner')||{}).textContent||''})`);
    await X.wait(`__lots.B()&&__lots.B().nRev===__lots.B().n`, 15000).catch(() => {});
    const xr = await X.ev(`__lots.B()?JSON.stringify(__lots.B().res.a):''`);
    ok('L12', v.c.ok && xr === JSON.stringify(a), '#cert= 링크 → 서버 없이 검증 ✓ · 같은 배정을 다시 공개', { ban: v.ban, xr });
    await sleep(1800); await shot(X, '07_cert_view');
    const E2 = [H, G1, G2, X].map(p => ({ p: p.label, e: errs(p) })).filter(x => x.e.length);
    ok('L13', !E2.length, '네 페이지 모두 예외·콘솔 오류 없음', E2);
    const sn = relay.snapshot();
    console.log('relay bill', sn.bill, 'msgs in', Math.round(sn.ms / 1000) + 's', '· x:s', JSON.stringify(sn.byEvent['broadcast:x'] || sn.byEvent));
} catch (e) { console.log('ERROR', e && e.stack || e); ok('LX', false, 'exception', String(e && e.message || e)); }
finally { await E.stop(); await relay.stop(); }
const f = R.rows.filter(r => !r.pass).length;
console.log('\n' + R.rows.length + ' checks · ' + f + ' fail');
process.exit(f ? 1 : 0);
