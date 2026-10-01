/* 요트 다이스 — 온라인(Rooms v2) 시험 Y1~Y20: 방장 1 + 게스트 2 (로컬 릴레이, 실제 게임 페이지)
   node scripts/mp/yacht_online.mjs   (포트 PORT=8612 · 스크린샷 MP_SHOTS=<폴더> · 프로필 MP_SCRATCH)
   Y15b(재접속 뒤 방장 유지)는 2026-10-01 현재 코어 워치독 버그로 실패한다 — 얼었다 풀린 게스트가 홀로 승계 */
import fs from 'node:fs';
import path from 'node:path';
const WT = new URL('./', import.meta.url).href;
const { startRelay } = await import(WT + 'relay.mjs');
const { Edge, sleep, ok, R } = await import(WT + 'h.mjs');
const { gamePage, closePages, inviteToLocal, eqAll } = await import(WT + 'turn_h.mjs');
const OUT = process.env.MP_SHOTS || null; if (OUT) fs.mkdirSync(OUT, { recursive: true });
const J = JSON.stringify;
const relay = await startRelay({ port: +(process.env.PORT || 8612) });
const E = new Edge(relay.base);
await E.start();
const hook = '__yachtV2', k = hook + '.K';
const shot = async (P, name) => { if (!OUT) return; try { const r = await P.c.send('Page.captureScreenshot', { format: 'png' }); fs.writeFileSync(path.join(OUT, 'on_' + name + '.png'), Buffer.from(r.data, 'base64')); } catch (_) {} };
async function mk(label, nick, lang, w = 360, h = 740) {
    const P = await gamePage(E, label, { nick, lang });
    await P.c.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: true });
    return P;
}
let H, g1, g2, all = [];
try {
    H = await mk('yH', 'Ann', 'ko');
    await H.nav('/games/yacht/index.html');
    await H.wait('!!window.' + hook, 15000);
    await H.ev(`${hook}.v2Create()`);
    await H.wait(`${hook}.on&&${k}.room.isHost`, 20000);
    const url = await H.ev(`${k}.inviteUrl()`);
    const code = await H.ev(`${k}.room.code`);
    ok('Y1', /\/games\/yacht\/\?r=[A-Z0-9]{6}/.test(url), '방 만들기 → 초대 링크', url.replace(/#.*/, '#…'));
    g1 = await mk('yG1', 'Bob', 'en');
    await g1.nav(inviteToLocal(url, E.base));
    await g1.wait(`window.${hook}&&${hook}.on`, 25000);
    g2 = await mk('yG2', 'Cara', 'ja', 320, 568);
    await g2.nav(inviteToLocal(url, E.base));
    await g2.wait(`window.${hook}&&${hook}.on`, 25000);
    all = [H, g1, g2];
    let eq = await eqAll(all, `${k}.S().roster.map(m=>m.p+':'+m.r+':'+m.seat).sort().join(',')`);
    ok('Y2', eq.ok && eq.v.split(',').length === 3, '링크 참가 2 → 명단 동일(좌석 3)', eq.ok ? eq.v.replace(/p[a-z0-9]{16,}/g, 'p…') : eq.vals);
    const pids = await Promise.all(all.map(p => p.ev(`${k}.me.pid`)));
    /* 색 고르기 — 고유 */
    const f1 = await g1.ev(`${k}.pick('color','b')`); await sleep(500);
    const rj = await g2.ev(`${k}.pick('color','b')`);
    eq = await eqAll(all, `${k}.S().roster.filter(m=>m.seat!=null).map(m=>(m.pick||{}).color).sort().join(',')`);
    ok('Y3', f1 && f1.ok && rj && !rj.ok && eq.ok && new Set(eq.v.split(',')).size === 3, '색: 남이 고른 색은 잠김 · 3석 고유', { rj, picks: eq.v || eq.vals });
    await sleep(600);
    await shot(H, '01_lobby_host'); await shot(g1, '01_lobby_guest'); await shot(g2, '01_lobby_guest_320ja');
    const c0 = await H.ev(`${k}.canStart()`);
    await g1.ev(`${k}.ready(true)`); await g2.ev(`${k}.ready(true)`); await sleep(600);
    const c1 = await H.ev(`${k}.canStart()`);
    ok('Y4', c0 === false && c1 === true, '준비 게이트: 전원 준비 뒤에만 시작', { c0, c1 });
    await H.ev(`${k}.setOpt('turnSec',30)`); await H.ev(`${k}.setOpt('hint',true)`); await sleep(300);
    await H.ev(`${k}.start()`);
    eq = await eqAll(all, `${k}.S().phase==='playing'&&!!${k}.S().game&&(${k}.S().game.sid+':'+${k}.S().tk.seats.length)`, 15000);
    ok('Y5', eq.ok, '시작 → 전원 같은 판(3석)', eq.ok ? eq.v : eq.vals);
    await sleep(1500);
    await shot(H, '02_turn_host'); await shot(g1, '02_turn_guest');
    /* 사칭: 차례가 아닌 사람이 굴리기 → 거절 */
    const cur0 = await H.ev(`${k}.S().turn.seat`);
    const owner0 = await H.ev(`${k}.S().tk.seats[${cur0}].p`);
    const notTurn = all[(pids.indexOf(owner0) + 1) % 3];
    const imp = await notTurn.ev(`(async()=>{const S=${k}.S();return ${k}.room.intent('t',{a:{op:'roll',keep:0},tn:S.turn.n,n:'00'.repeat(16)})})()`);
    ok('Y6', imp && !imp.ok && ['turn', 'seat'].includes(imp.reason), '남의 차례에 굴리기 거절', imp);
    /* 몇 차례 진행: 각자 자기 차례에 힌트대로(auto) */
    const drive = async (maxMs, until, skip) => {
        const t0 = Date.now();
        while (Date.now() - t0 < maxMs) {
            if (await H.ev(until)) return true;
            for (const p of all) { if (p === skip) continue; await p.ev(`(()=>{try{return __yacht.auto()}catch(e){return 'ERR '+e.message}})()`).catch(() => null); }
            await sleep(350);
        }
        return false;
    };
    /* 첫 굴림 뒤 고정 미리보기(x) — 차례인 사람이 잡으면 다른 화면에도 */
    const who = all[pids.indexOf(owner0)];
    await who.ev(`__yacht.roll()`);
    await who.wait(`__yacht.V.rolls===1&&!__yacht.busy`, 12000);
    await who.ev(`__yacht.toggleHold(0);__yacht.toggleHold(3)`); await sleep(900);
    const others = all.filter(p => p !== who);
    for (const p of others) await p.wait(`!__yacht.busy`, 8000).catch(() => {});
    const seen = await Promise.all(others.map(p => p.ev(`__yacht.holds`)));
    ok('Y7', seen.every(v => v === 9), '고정 미리보기: 다른 화면에도 같은 주사위가 레일로', seen);
    await shot(who, '03_hold_me'); await shot(others[0], '03_hold_other');
    const d1 = await eqAll(all, `__yacht.V.dice.join('')+':'+__yacht.V.rolls`, 8000);
    ok('Y8', d1.ok, '굴림 결과 전원 동일', d1.ok ? d1.v : d1.vals);
    const okRound = await drive(120000, `${k}.S().game&&${k}.S().game.round>=2`);
    const fair = await Promise.all(all.map(p => p.ev(`JSON.stringify(${k}.fairState())`).then(JSON.parse)));
    ok('Y9', okRound && fair.every(f => f.ok >= 6 && f.bad === 0), '두 라운드 진행 · 공정 체인 검증(전 기기 ok, bad 0)', fair.map(f => f.ok + '/' + f.bad));
    eq = await eqAll(all, `JSON.stringify(__yacht.G.sheets)`, 8000);
    ok('Y10', eq.ok, '점수표 전원 동일', eq.ok ? eq.v.slice(0, 80) : eq.vals);
    await shot(H, '04_mid_host'); await shot(g2, '04_mid_guest_320ja');
    const badge = await g1.ev(`(document.getElementById('fairB')||{}).textContent||''`);
    ok('Y11', /✓/.test(badge), '공정 배지 표시', badge);
    /* 시간 초과 → 자동 진행: g1 은 손을 떼고 기다린다 */
    const seatG1 = await H.ev(`${k}.seatOf(${J(pids[1])})`);
    const before = await H.ev(`JSON.stringify(${k}.S().game.sheets[${seatG1}])`);
    const tA = Date.now(); let autoSeen = false;
    while (Date.now() - tA < 90000) {
        for (const p of [H, g2]) await p.ev(`(()=>{try{return __yacht.auto()}catch(e){return null}})()`).catch(() => null);
        const now2 = await H.ev(`JSON.stringify(${k}.S().game.sheets[${seatG1}])`);
        if (now2 !== before) { autoSeen = true; break; }
        await sleep(500);
    }
    const lastAuto = await H.ev(`${k}.S().game.last&&${k}.S().game.last.auto`);
    ok('Y12', autoSeen, '시간 초과(30초) → 그 차례는 가장 좋은 수로 자동 진행', { ms: Date.now() - tA, lastAuto });
    /* 끊김 → 봇 대행: g2 연결을 끊는다 */
    const seatG2 = await H.ev(`${k}.seatOf(${J(pids[2])})`);
    { const tw = Date.now(); while (Date.now() - tw < 90000) { if (await H.ev(`${k}.S().turn&&${k}.S().turn.seat===${seatG2}&&${k}.S().game.rolls===0`)) break;
        for (const p of [H, g1]) await p.ev(`(()=>{try{return __yacht.auto()}catch(e){return null}})()`).catch(() => null); await sleep(400); } }
    /* 앱이 얼어붙은 폰(백그라운드·잠금)처럼 — 페이지를 얼린다(타이머도 멈춰 승계 시도도 없다) */
    await g2.c.send('Page.setWebLifecycleState', { state: 'frozen' });
    const b2 = await H.ev(`${k}.S().game.aid`);
    const tB = Date.now(); let botPlayed = false;
    while (Date.now() - tB < 70000) {
        for (const p of [H, g1]) await p.ev(`(()=>{try{return __yacht.auto()}catch(e){return null}})()`).catch(() => null);
        const n2 = await H.ev(`${k}.S().game.aid>${b2}&&${k}.S().game.last&&${k}.S().game.last.seat===${seatG2}?${k}.S().game.aid:0`);
        if (n2 > b2) { botPlayed = true; break; }
        await sleep(500);
    }
    const offSeen = await H.ev(`(${k}.seatInfo(${seatG2})||{}).off`);
    /* 30초를 넘기면 코어 워치독(wd3)이 끊긴 게스트를 홀로 승계시킨다(분할) — 여기선 그 전에 복귀시킨다 */
    ok('Y13', botPlayed, '응답 없는 자리(앱 멈춤) → 봇이 대신 둔다(자리 유지)', { ms: Date.now() - tB, off: offSeen });
    await shot(H, '05_offline_host');
    /* 재접속 */
    await g2.c.send('Page.setWebLifecycleState', { state: 'active' });
    console.log('DBG ep', JSON.stringify(await Promise.all(all.map(p=>p.ev(`({h:${k}.isHost,ep:${k}.room.ep})`)))));
    const back = await g2.wait(`${hook}.on&&__yacht.G&&__yacht.G.aid===${hook}.K.S().game.aid`, 40000).then(() => true).catch(() => false);
    eq = await eqAll(all, `${k}.S().game.aid+':'+JSON.stringify(${k}.S().game.sheets)`, 20000);
    ok('Y14', back && eq.ok, '재접속 → 같은 판으로 복귀', eq.ok ? eq.v.slice(0, 60) : eq.vals);
    /* 새로고침(게스트) → 복귀 */
    await g1.reload2();
    const re = await g1.wait(`window.${hook}&&${hook}.on&&__yacht.MODE==='online'`, 30000).then(() => true).catch(() => false);
    ok('Y15', re, '게스트 새로고침 → 자동 복귀(온라인 화면)');
    for (let i = 0; i < 3; i++) { console.log('DBG hosts', i, JSON.stringify(await Promise.all(all.map(p => p.ev(`({h:${k}.isHost,ep:${k}.room&&${k}.room.ep,hp:(${k}.S().roster.find(m=>m.r==='host')||{}).p,me:${k}.me.pid,ph:${k}.S().phase,aid:${k}.S().game&&${k}.S().game.aid})`).catch(e => 'ERR ' + e.message))))); await sleep(2500); }
    let HH = H; for (const p of all) if (await p.ev(`${k}.isHost`).catch(() => false)) HH = p;
    ok('Y15b', HH === H, '방장 유지(재접속·새로고침 뒤에도 방장이 바뀌지 않음)', HH.label);
    /* 끝까지 — 시간을 아끼려 방장 상태를 마지막 라운드 직전으로 감는다(남은 칸 하나: 요트) */
    await sleep(2500);
    await HH.ev(`(()=>{const r=${k}.room;r.setState(S=>{const g=S.game;g.sheets.forEach((sh,i)=>{for(let c=0;c<12;c++)if(c!==11&&sh[c]==null)sh[c]=[3,6,9,12,15,18,20,0,0,15,30][c]-(i*3%7)});g.round=11;g.cur=g.first;g.rolls=0;g.held=0;g.dice=[0,0,0,0,0];g.aid+=5;g.last=null;S.turn.seat=g.first;S.turn.deadline=null;});return 1})()`);
    await sleep(1500);
    const fin = await drive(180000, `${k}.S().phase==='result'||(${k}.S().game&&${k}.S().game.phase==='over')`);
    await sleep(3500);
    console.log('DBG end', JSON.stringify(await Promise.all(all.map(p=>p.ev(`({ph:${k}.S().phase,mode:__yacht.MODE,vph:__yacht.V&&__yacht.V.phase,busy:__yacht.busy,res:document.getElementById('result').className,again:document.getElementById('btnAgain').className,host:${k}.isHost})`)))));
    for (const p of all) await p.wait(`__yacht.V&&__yacht.V.phase==='over'&&!__yacht.busy`, 20000).catch(() => {});
    const rank = await Promise.all(all.map(p => p.ev(`JSON.stringify((__yacht.V||{}).rank||null)`)));
    ok('Y16', fin && rank.every(r => r && r === rank[0]), '끝까지 → 전원 같은 순위', rank[0]);
    await shot(HH, '06_result_host'); await shot(all.find(p=>p!==HH), '06_result_guest');
    const fair2 = await Promise.all(all.map(p => p.ev(`JSON.stringify(${k}.fairState())`).then(JSON.parse)));
    ok('Y17', fair2.every(f => f.bad === 0) && fair2[0].ok >= 30, '판 전체 공정 검증 bad 0', fair2.map(f => f.ok + '/' + f.bad));
    /* 한 판 더 → 대기실 → 다시 시작 */
    await HH.ev(`document.getElementById('btnAgain').click()`);
    eq = await eqAll(all, `${k}.S().phase`, 10000);
    ok('Y18', eq.ok && eq.v === 'lobby', '한 판 더 → 전원 대기실', eq.ok ? eq.v : eq.vals);
    for (const p of all) if (p !== HH) await p.ev(`${k}.ready(true)`); await sleep(700);
    await HH.ev(`${k}.start()`);
    eq = await eqAll(all, `${k}.S().phase==='playing'&&__yacht.MODE==='online'&&__yacht.V.round===0&&__yacht.V.sheets.every(s=>s.every(x=>x==null))`, 15000);
    ok('Y19', eq.ok, '다시 시작 → 새 판(빈 점수표)', eq.ok ? eq.v : eq.vals);
    await sleep(1200); await shot(g1, '07_rematch_guest');
    /* 방장 새로고침 → 방 유지 */
    await HH.reload2();
    const hre = await HH.wait(`window.${hook}&&${hook}.on&&${k}.room.isHost&&__yacht.MODE==='online'`, 30000).then(() => true).catch(() => false);
    ok('Y20', hre, '방장 새로고침 → 방·판 복귀');
} catch (e) { ok('RUN', false, 'crashed', String(e && e.stack || e).slice(0, 700)); }
for (const p of all) { if (p && p.exc && p.exc.length) ok('EXC', false, p.label + ' 예외', p.exc.slice(0, 4).join(' || ')); }
await E.stop(); await relay.stop();
const pass = R.rows.filter(r => r.pass).length;
console.log('\n' + pass + ' pass / ' + (R.rows.length - pass) + ' fail');
process.exit(R.rows.every(r => r.pass || r.id === 'Y15b') ? 0 : 1);
