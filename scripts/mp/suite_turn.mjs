/* P4 시나리오 T1~T12 (DESIGN §10.2 턴제) — 실제 게임 페이지 2~4대 */
import { gamePage, closePages, inviteToLocal, eqAll, sleep } from './turn_h.mjs';
import * as A from './attacker.mjs';

const J = JSON.stringify;
const on = (want, id) => !want.length || want.includes(id);

/* ── 공용: 방장 1 + 게스트 n ──────────────────────────────────── */
async function room(E, gid, n, o = {}) {
    const hook = o.hook || ('__' + gid.replace(/-/g, '') + 'V2');
    const H = await gamePage(E, (o.px || gid.slice(0, 2)) + 'H', { nick: o.hostNick || 'Ann' });
    await H.nav('/games/' + gid + '/index.html?rooms=v2');
    await H.wait('!!window.' + hook, 15000);
    await H.ev(`${hook}.v2Create()`);
    await H.wait(`${hook}.on&&${hook}.K.room.isHost`, 20000);
    const url = await H.ev(`${hook}.K.inviteUrl()`);
    const G = [];
    for (let i = 0; i < n; i++) {
        const g = await gamePage(E, (o.px || gid.slice(0, 2)) + 'G' + i, { nick: (o.nicks && o.nicks[i]) || ['Bob', 'Cara', 'Dan', 'Eve'][i] });
        await g.nav(inviteToLocal(url, E.base));
        await g.wait(`window.${hook}&&${hook}.on`, 25000);
        G.push(g);
    }
    const code = await H.ev(`${hook}.K.room.code`);
    return { H, G, url, code, hook, all: [H].concat(G) };
}
const K = (h) => h + '.K';

/* ================================================================
   YUT — T1 전 기능 회귀 · T2 사칭 · T4 마감 표시 차 · T5 끊김 봇 · T12 게임 hb 0
   ================================================================ */
async function yut(ctx) {
    const { E, relay, ok, want } = ctx;
    const r = await room(E, 'yut', 2, { px: 'y' });
    const { H, G, hook, all } = r, [g1, g2] = G, k = K(hook);
    try {
        const pids = await Promise.all(all.map(p => p.ev(`${k}.me.pid`)));
        let eq = await eqAll(all, `${k}.S().roster.map(m=>m.p+':'+m.r+':'+m.seat).sort().join(',')`);
        ok('T1a', eq.ok && eq.v.split(',').length === 3, 'yut v2: 방장 1 + 링크 참가 2 → 명단 동일(좌석 배정)', eq.ok ? eq.v : eq.vals);

        /* 캐릭터 고르기 — 남이 고른 건 잠김, 봇 것은 맞바꿈 */
        await g1.ev(`${k}.pick('char','cat')`); await sleep(500);
        const rj = await g2.ev(`${k}.pick('char','cat')`);
        await H.ev(`${k}.addBot()`); await sleep(400);
        const botPick = await H.ev(`(${k}.S().roster.find(m=>m.r==='bot').pick||{}).char`);
        const sw = await g2.ev(`${k}.pick('char',${J(botPick)})`); await sleep(500);
        eq = await eqAll(all, `${k}.S().roster.filter(m=>m.seat!=null).map(m=>(m.pick||{}).char).sort().join(',')`);
        const uniq = eq.ok && new Set(eq.v.split(',')).size === 4;
        ok('T1b', rj && !rj.ok && rj.reason === 'taken' && sw && sw.ok && uniq, '캐릭터: 잠김(taken) · 봇 것은 맞바꿈 · 4석 고유', { rj, sw, picks: eq.v || eq.vals });

        /* 준비 → 시작 게이트 */
        const c0 = await H.ev(`${k}.canStart()`);
        await g1.ev(`${k}.ready(true)`); await sleep(300);
        const c1 = await H.ev(`${k}.canStart()`);
        await g2.ev(`${k}.ready(true)`); await sleep(500);
        const c2 = await H.ev(`${k}.canStart()`);
        ok('T1c', c0 === false && c1 === false && c2 === true, '준비 게이트: 전원 준비 전엔 시작 불가', { c0, c1, c2 });

        await H.shot('yut_1lobby_host'); await g1.shot('yut_1lobby_guest');
        /* 옵션: 말 1개 · 턴 15초 */
        await H.ev(`${k}.setOpt('k',1)`); await H.ev(`${k}.setOpt('turnSec',15)`); await sleep(300);
        await H.ev(`${k}.start()`);
        eq = await eqAll(all, `${k}.S().phase==='playing'&&!!${k}.S().game&&(${k}.S().game.game+':'+${k}.S().tk.seats.length)`, 15000);
        if (!eq.ok) console.log('T1d-DBG', JSON.stringify(await Promise.all(all.map(p => p.ev(`(()=>{const r=LpRooms.current();return {st:r._state,lastS:r._lastS,buf:Object.keys(r._buf||{}),ph:r.state().phase,seq:r.state().seq,hs:r._H&&r._H.s,ep:r.ep,snapAt:Date.now()-r._snapAt,lastHost:Date.now()-r._lastHostAt,bad:LpRooms.stats().bad}})()`)))));
        ok('T1d', eq.ok, '시작 → 전원 같은 판(4석)', eq.ok ? eq.v : eq.vals);
        await sleep(2500); await H.shot('yut_2play_host'); await g1.shot('yut_2play_guest');

        /* T12: 게임 자체 하트비트 0 — 20초 동안 게스트 'g' 이벤트 종류 */
        relay.resetStats(); relay.stats.logOn = true;
        /* T2: 사칭 — g2 가 g1 차례에 굴리기(서명은 자기 것) → 거절, 원시 공격자가 g1 pid 로 서명 없는 intent → 무시 */
        /* 사람 좌석 차례가 올 때까지(봇 차례면 기다림) */
        await H.wait(`(()=>{const S=${k}.S();return S.turn&&!S.tk.seats[S.turn.seat].bot})()`, 30000).catch(() => {});
        const turnSeat = await H.ev(`${k}.S().turn.seat`);
        const seatOwner = await H.ev(`${k}.S().tk.seats[${k}.S().turn.seat].p`);
        const who = [H, g1, g2][pids.indexOf(seatOwner)];
        const other = [g1, g2].find(p => p !== who) || g1;
        const seq0 = await H.ev(`${k}.S().seq`);
        const imp = await other.ev(`(async()=>{const S=${k}.S();return ${k}.room.intent('t',{a:{k:'throw',pow:0.5},tn:S.turn.n,n:'00'.repeat(16)})})()`);
        const forged = await A.gEnv({ code: r.code, e: 'intent', p: pids[1], c: Date.now() + 99999, d: { a: 'ready', x: false } });
        relay.inject('lpr-' + r.code, 'g', forged);
        await sleep(800);
        const seq1 = await H.ev(`${k}.S().seq`);
        const g1rd = await H.ev(`${k}.S().roster.find(m=>m.p===${J(pids[1])}).rd`);
        ok('T2', who ? (imp && !imp.ok && ['turn', 'seat'].includes(imp.reason) && g1rd === true) : false, '사칭: 남의 차례 굴리기 거절 · 위조(무서명) intent 무시', { imp, seqChanged: seq1 !== seq0, g1rd, turnSeat });

        /* T4: 턴 마감 표시 — 같은 순간 남은 시간 차 ≤ 300ms (방장 시계) */
        await H.wait(`${k}.S().turn&&${k}.S().turn.deadline`, 20000).catch(() => {});
        const rs = await Promise.all(all.map(p => p.ev(`({t:Date.now(),r:${k}.remain()})`)));
        const adj = rs.filter(x => x.r != null).map(x => x.r + (x.t - rs[0].t));
        const skew = adj.length ? Math.max(...adj) - Math.min(...adj) : 1e9;
        ok('T4', adj.length === 3 && skew <= 300, '턴 마감 표시 차 ≤ 300ms (방장 시계 deadline)', { skew: Math.round(skew), n: adj.length });

        /* 한 판 굴리기: 사람 차례면 사람이 두고(가끔 일부러 안 둬서 마감 자동), 끝날 때까지 */
        const drive = async (skipPage, maxMs) => {
            const t0 = Date.now();
            while (Date.now() - t0 < maxMs) {
                const ph = await H.ev(`${k}.S().phase`);
                if (ph !== 'playing') return ph;
                for (const p of all) {
                    if (p === skipPage) continue;
                    await p.ev(`(()=>{const V=__yut.V;if(!V||V.phase!=='play'||!__yut.canInput())return 0;if(V.throws>0){__yut.act;document.getElementById('btnThrow').click();return 1}const os=__yut.options(V,V.turn);if(os.length){window.__yutV2.K.act({k:'move',from:os[0].from,v:os[0].v});return 2}return 0})()`).catch(() => 0);
                }
                await sleep(400);
            }
            return 'timeout';
        };
        /* afk: g2 가 두 번 연속 시간 초과 → 봇이 대신(afk) → '내가 할게요'로 복귀 */
        const g2seat = await H.ev(`${k}.seatOf(${J(pids[2])})`);
        let afkSeen = false;
        const tA = Date.now();
        while (Date.now() - tA < 90000) {
            await drive(g2, 2500);
            afkSeen = await H.ev(`!!(${k}.S().roster.find(m=>m.p===${J(pids[2])})||{}).afk`);
            if (afkSeen || (await H.ev(`${k}.S().phase`)) !== 'playing') break;
        }
        const autoBy = await g2.ev(`(${k}.S().tk.to||{})[${g2seat}]|0`);
        const backR = await g2.ev(`${k}.back()`);
        const afkAfter = await H.wait(`!(${k}.S().roster.find(m=>m.p===${J(pids[2])})||{}).afk&&'ok'`, 5000).then(() => false).catch(() => true);
        ok('T1e', afkSeen && !afkAfter, 'afk: 연속 2회 시간 초과 → 자동(봇) → "내가 할게요" 복귀', { afkSeen, autoBy, afkAfter, backR });

        /* T12 집계 */
        relay.stats.logOn = false;
        const gl = relay.stats.log.filter(x => x.event === 'g').map(x => { try { return JSON.parse(x.raw).e; } catch (_) { return '?'; } });
        const byE = {}; gl.forEach(e => { byE[e] = (byE[e] || 0) + 1; });
        const hl = relay.stats.log.filter(x => x.event === 'h').map(x => { try { return JSON.parse(x.raw).e; } catch (_) { return '?'; } });
        const byH = {}; hl.forEach(e => { byH[e] = (byH[e] || 0) + 1; });
        const secs = (Date.now() - relay.stats.t0) / 1000, snap = relay.snapshot(), bill = Math.round(snap.bill / (snap.ms / 1000) * 100) / 100;
        ok('T12', !byE.x && Object.keys(byE).every(e => e === 'hb' || e === 'intent' || e === 'fair' || e === 'snap_req') && (byE.hb || 0) / secs < 0.5, '게임 자체 하트비트 0 — 게스트 발신은 커널 hb·intent 뿐 (+ 과금 msg/s)', { secs: Math.round(secs), g: byE, h: byH, billPerSec: bill });

        /* 게임 중 합류 → 봇 자리 이어받기 */
        const g3 = await gamePage(E, 'yG3', { nick: 'Dan' });
        await g3.nav(inviteToLocal(r.url, E.base));
        await g3.wait(`window.${hook}&&${hook}.on`, 25000);
        const g3role = await g3.ev(`${k}.me.role`);
        const botSeat = await H.ev(`${k}.S().tk.seats.findIndex(s=>s.bot)`);
        const cl = await g3.ev(`${k}.claim(${botSeat})`); await sleep(600);
        const owner = await H.ev(`${k}.S().tk.seats[${botSeat}].p`);
        const g3pid = await g3.ev(`${k}.me.pid`);
        ok('T1f', g3role === 'spec' && cl && cl.ok !== false && owner === g3pid, '게임 중 합류(관전) → 봇 자리 이어받기', { g3role, cl, botSeat, owned: owner === g3pid });
        all.push(g3);

        /* 재접속: g1 새로고침 → 같은 자리 */
        const s1 = await H.ev(`${k}.seatOf(${J(pids[1])})`);
        await g1.reload2();
        await g1.wait(`window.${hook}&&${hook}.on`, 20000);
        await sleep(800);
        const s1b = await H.ev(`${k}.seatOf(${J(pids[1])})`), c1b = await H.ev(`(${k}.S().roster.find(m=>m.p===${J(pids[1])})||{}).c`);
        const g1sees = await g1.ev(`${k}.seat()`);
        ok('T1g', s1 != null && s1 === s1b && g1sees === s1 && c1b === 'on', '재접속: 새로고침 → 같은 자리로 복귀', { s1, s1b, g1sees, c1b });

        /* 게임 끝까지 → 결과 → 한 판 더(대기실, 준비 초기화, 봇 유지) */
        /* 연출을 건너뛰게(숨김 탭은 애니메이션 없이 최신 상태로) 모두 숨긴 채 끝까지 */
        for (const p of all) await p.hide(false);
        const ph = await drive(null, 240000);
        for (const p of all) await p.show();
        await H.wait(`${k}.S().phase==='result'`, 20000).catch(() => {});
        const res = await eqAll(all, `${k}.S().phase+':'+(${k}.S().tk.res&&${k}.S().tk.res.winner)`, 8000);
        await H.ev(`${k}.rematch()`); await sleep(800);
        const lob = await eqAll(all, `${k}.S().phase`, 8000);
        const rdReset = await H.ev(`${k}.S().roster.filter(m=>m.r==='player').every(m=>!m.rd)`);
        const botsKept = await H.ev(`${k}.S().roster.filter(m=>m.r==='bot').length`);
        ok('T1h', res.ok && /^result:\d$/.test(res.v) && lob.ok && lob.v === 'lobby' && rdReset, '끝 → 결과 동일 → 한 판 더 = 대기실(준비 초기화)', { ph, res: res.v || res.vals, lob: lob.v, rdReset, botsKept });

        /* 내보내기+차단 → 재입장 거절 */
        await H.ev(`${k}.kick(${J(pids[2])},true)`);
        await g2.wait(`!${hook}.on`, 8000).catch(() => {});
        const gone = await g2.ev(`!${hook}.on`);
        await g2.nav(inviteToLocal(r.url, E.base)); await sleep(4000);
        const back = await g2.ev(`!!(window.${hook}&&${hook}.on)`);
        const inRoster = await H.ev(`!!${k}.S().roster.find(m=>m.p===${J(pids[2])})`);
        ok('T1i', gone && !back && !inRoster, '내보내기+차단 → 재입장 거절', { gone, back, inRoster });

        /* 방장 승계(윷 — 숨은 정보 없음): 새 판을 시작하고 방장 소켓만 끊는다 → 30초 뒤 게스트가 이어받아 게임 계속 */
        const live = [g1, g3];
        await g1.ev(`${k}.ready(true)`); await g3.ev(`${k}.ready(true)`); await sleep(600);
        await H.ev(`${k}.start()`);
        await eqAll(live.concat([H]), `${k}.S().phase==='playing'&&${k}.S().game.game`, 15000);
        relay.partition('yH');
        let took = null; const tp = Date.now();
        while (Date.now() - tp < 50000) { const hs = await Promise.all(live.map(p => p.ev(`${k}.isHost`))); if (hs.some(Boolean)) { took = Date.now() - tp; break; } await sleep(500); }
        const s0 = await g1.ev(`${k}.S().game.seq`);
        const t1 = Date.now(); let sM = s0;
        while (Date.now() - t1 < 20000) { for (const p of live) await p.ev(`(()=>{const V=__yut.V;if(!V||V.phase!=='play'||!__yut.canInput())return 0;if(V.throws>0){document.getElementById('btnThrow').click();return 1}const os=__yut.options(V,V.turn);if(os.length){window.__yutV2.K.act({k:'move',from:os[0].from,v:os[0].v});return 2}return 0})()`).catch(() => 0); await sleep(400); sM = await g1.ev(`${k}.S().game.seq`); if (sM > s0 + 2) break; }
        const eqM = await eqAll(live, `${k}.S().game.seq+':'+${k}.S().game.game`, 8000);
        ok('T1j', took && sM > s0 && eqM.ok, '윷 방장 크래시 → 승계(30초) → 새 방장 기기가 봇·마감을 이어서 · 두 게스트 상태 일치', { took, s0, s1: sM, eq: eqM.ok });
        relay.partition('yH', false);
        const exc = all.map(p => p.exc.slice(0, 3)).filter(x => x.length);
        ok('T1z', !exc.length, 'yut 페이지 예외 0', exc);
    } finally { await closePages(E, all.concat(G.filter(g => !all.includes(g)))); }
}


/* ================================================================
   LUDO — T7 주사위 chain 검증 · T5 끊김 8초 봇·복귀 · T9 방장 크래시 → 승계
   ================================================================ */
async function ludoDrive(pages, hook, ms, skip) {
    const t0 = Date.now(), k = hook + '.K';
    while (Date.now() - t0 < ms) {
        for (const p of pages) {
            if (skip && skip.includes(p)) continue;
            await p.ev(`(()=>{const L=${hook};if(!L.on)return 0;if(L.canRoll()){L.act('roll');return 1}if(L.canMove()){const V=L.V;L.act('move',V.legal[0]);return 2}return 0})()`).catch(() => 0);
        }
        await sleep(350);
    }
}
async function ludo(ctx) {
    const { E, relay, ok, want } = ctx;
    const r = await room(E, 'ludo', 2, { px: 'l' });
    const { H, G, hook, all } = r, [g1, g2] = G, k = K(hook);
    const extra = [];
    try {
        const pids = await Promise.all(all.map(p => p.ev(`${k}.me.pid`)));
        await g1.ev(`${k}.ready(true)`); await g2.ev(`${k}.ready(true)`); await H.ev(`${k}.setOpt('turnSec',15)`); await H.ev(`${k}.setOpt('fast',true)`); await sleep(500);
        await H.shot('ludo_1lobby_host'); await g1.shot('ludo_1lobby_guest');
        const st = await H.ev(`${k}.start()`);
        let eq = await eqAll(all, `${k}.S().phase==='playing'&&${k}.S().game.sid`, 15000);
        if (!eq.ok) console.log('T7a-DBG', JSON.stringify(await Promise.all(all.map(p => p.ev(`(()=>{const r=LpRooms.current();return {st:r._state,lastS:r._lastS,buf:Object.keys(r._buf||{}),ph:r.state().phase,seq:r.state().seq,hs:r._H&&r._H.s,ep:r.ep,snapAt:Date.now()-r._snapAt,lastHost:Date.now()-r._lastHostAt,bad:LpRooms.stats().bad}})()`)))));
        ok('T7a', st && eq.ok, 'ludo v2: 시작 → 전원 같은 판', eq.ok ? eq.v : eq.vals);
        await sleep(2000); await H.shot('ludo_2play_host'); await g1.shot('ludo_2play_guest');
        await ludoDrive(all, hook, 20000);
        const fs = await Promise.all(all.map(p => p.ev(`${k}.fairState()`)));
        const c0 = await Promise.all(all.map(p => p.ev(`${k}.S().tk.c0`)));
        ok('T7', fs.slice(1).every(f => f.ok >= 3 && f.bad === 0) && new Set(c0).size === 1, '주사위 = LpFair.chain — 게스트 전원 굴림 검증 ✓(위조 0)', fs.map(f => ({ ok: f.ok, bad: f.bad, i: f.i })));
        /* 위조 시도: 방장 기기가 사건 난수를 바꿔 치기 → 게스트가 잡아낸다 */
        await H.ev(`(()=>{window.__cv=LpFair.chain.value;LpFair.chain.value=function(s,n){return window.__cv(s,String(n||'')+'ff')};return 1})()`);
        const bad0 = await Promise.all(G.map(p => p.ev(`${k}.fairState().bad`)));
        await ludoDrive(all, hook, 9000);
        const bad1 = await Promise.all(G.map(p => p.ev(`${k}.fairState().bad`)));
        await H.ev(`(()=>{LpFair.chain.value=window.__cv;return 1})()`);
        ok('T7b', bad1.every((b, i) => b > bad0[i]), '방장이 굴림 난수를 바꾸면 모든 게스트가 검증 실패로 표시', { before: bad0, after: bad1 });

        /* T5: g1 탭 닫힘(bye) → 8초 뒤 봇 대행(자리 유지) → 같은 기기로 다시 오면 자리 복귀 */
        const s1 = await H.ev(`${k}.seatOf(${J(pids[1])})`);
        await H.ev(`(()=>{window.__autos=[];window.__turns=[];${k}.room.on('state',S=>{const tn=window.__turns;if(S.turn&&(!tn.length||tn[tn.length-1].n!==S.turn.n))tn.push({n:S.turn.n,s:S.turn.seat,t:Date.now()});if(S.tk&&S.tk.ev&&S.tk.ev.auto){const l=window.__autos,e=S.tk.ev;if(!l.length||l[l.length-1].id!==e.id)l.push({id:e.id,s:e.seat,a:e.auto,t:Date.now()})}});return 1})()`);
        const ctx1 = g1.ctx;
        await g1.close();
        const tOff = Date.now();
        await H.wait(`(${k}.S().roster.find(m=>m.p===${J(pids[1])})||{}).c==='off'`, 25000);
        const tOffSeen = Date.now();
        let botT = null;
        const t0 = Date.now();
        const hostOff = await H.ev(`Date.now()`);
        while (Date.now() - t0 < 60000) {
            await ludoDrive([H, g2], hook, 700);
            /* 끊김 판정 뒤 새로 온 그 좌석 차례 — 차례 시작부터 봇이 둘 때까지 */
            const ev = await H.ev(`(()=>{const T=window.__turns||[];const ts=T.filter((x,i)=>x.s===${s1}&&x.t>=${hostOff}&&i>0&&T[i-1].s!==${s1})[0];if(!ts)return null;const e=(window.__autos||[]).filter(x=>x.s===${s1}&&x.a==='bot'&&x.t>=ts.t)[0];return e?{t:e.t,ts:ts.t}:null})()`).catch(() => null);
            if (ev) { botT = tOffSeen + (ev.t - ev.ts); break; }
        }
        const turnStart = await H.ev(`0`);
        const seatKept = await H.ev(`${k}.S().tk.seats[${s1}].p===${J(pids[1])}&&!${k}.S().tk.seats[${s1}].bot`);
        /* 다시 연결: 같은 기기(컨텍스트) 새 탭 → 초대 링크 → 알려진 pid → 같은 자리 */
        const g1b = await (await import('./turn_h.mjs')).gamePage(E, 'lG0b', { nick: 'Bob', ctx: ctx1 });
        extra.push(g1b);
        await g1b.nav(inviteToLocal(r.url, E.base));
        await g1b.wait(`window.${hook}&&${hook}.on`, 25000);
        await sleep(1200);
        const back = await H.ev(`(()=>{const m=${k}.S().roster.find(m=>m.p===${J(pids[1])});return {c:m&&m.c,seat:${k}.seatOf(${J(pids[1])})}})()`);
        const g1bSeat = await g1b.ev(`${k}.seat()`);
        ok('T5', botT && botT - tOffSeen <= 9500 && seatKept && back.c === 'on' && back.seat === s1 && g1bSeat === s1,
            '끊긴 좌석: 끊김 판정 뒤 그 차례 8초 안 봇 대행(자리 예약 유지) → 재접속 시 같은 자리 복귀', { offDetectMs: tOffSeen - tOff, botAfterTurnMs: botT ? botT - tOffSeen : null, seatKept, back, g1bSeat });

        /* T9: 방장 크래시(소켓만 사망) → 12s 확인 중 · 20s 끊김 · 30s 승계 → 게임 계속 */
        const live = [g1b, g2];
        const seqA = await g2.ev(`${k}.S().seq`);
        relay.partition('lH');
        const tP = Date.now();
        let l1 = null, l2 = null, tk = null;
        while (Date.now() - tP < 50000) {
            const x = await g2.ev(`({lv:${k}.hostLost(),host:${k}.isHost,h1:${hook}.K.room&&${hook}.K.room.isHost})`);
            const y = await g1b.ev(`${k}.isHost`);
            if (x.lv >= 1 && !l1) l1 = Date.now() - tP;
            if (x.lv >= 2 && !l2) l2 = Date.now() - tP;
            if ((x.host || y) && !tk) { tk = Date.now() - tP; break; }
            await sleep(500);
        }
        const newHost = (await g2.ev(`${k}.isHost`)) ? g2 : g1b;
        await sleep(1500);
        const seqB = await g2.ev(`${k}.S().seq`);
        await ludoDrive(live, hook, 12000);
        const seqC = await g2.ev(`${k}.S().seq`), ph = await g2.ev(`${k}.S().phase`);
        const eq2 = await eqAll(live, `${k}.S().seq+':'+${k}.S().game.aid`, 8000);
        ok('T9', l1 && l2 && tk && l2 - l1 >= 6500 && tk - l1 >= 16500 && seqC > seqB && eq2.ok && (ph === 'playing' || ph === 'result'),
            '방장 크래시(루도) → 12s 확인 중 · 20s 끊김 · 30s 승계(마지막 방장 소식 기준) → 게임 계속·상태 일치', { l1, l2, tk, seqA, seqB, seqC, ph, eq: eq2.ok });
        relay.partition('lH', false);
        await sleep(6000);
        const oldHost = await H.ev(`({host:${k}.isHost,on:${hook}.on})`);
        ok('T9b', !oldHost.host, '원방장 복귀 → 게스트로 합류(되찾기 없음)', oldHost);
        const exc = all.concat(extra).map(p => p.exc.slice(0, 3)).filter(x => x.length);
        ok('T7z', !exc.length, 'ludo 페이지 예외 0', exc);
    } finally { await closePages(E, all.concat(extra)); }
}

/* ================================================================
   REVERSI — T3 21초 백그라운드 → 자리 유지 · 관전자 착석 불가 · 턴 시간
   ================================================================ */
async function rvMove(p, hook) {
    return p.ev(`(()=>{const R=${hook};if(!R.on||!R.canAct())return -1;const G=R.G;const ms=R.E.moves(G.board,G.turn);if(!ms.length)return -2;R.tap(ms[0]);return ms[0]})()`);
}
async function reversi(ctx) {
    const { E, relay, ok, want } = ctx;
    const r = await room(E, 'reversi', 2, { px: 'r' });
    const { H, G, hook, all } = r, [g1, g2] = G, k = K(hook);
    try {
        const pids = await Promise.all(all.map(p => p.ev(`${k}.me.pid`)));
        const roles = await Promise.all(all.map(p => p.ev(`${k}.me.role`)));
        await g1.ev(`${k}.ready(true)`); await sleep(400);
        await H.shot('reversi_1lobby_host'); await g1.shot('reversi_1lobby_guest');
        await H.ev(`${k}.start()`);
        let eq = await eqAll(all, `${k}.S().phase==='playing'&&${k}.S().game.b`, 15000);
        await sleep(1500); await H.shot('reversi_2play_host'); await g1.shot('reversi_2play_guest'); await g2.shot('reversi_2play_spectator');
        ok('T3a', roles[2] === 'spec' && eq.ok, 'reversi v2: 2석 + 관전 1 · 시작 → 같은 판', { roles, eq: eq.ok });
        for (let i = 0; i < 4; i++) { for (const p of [H, g1]) await rvMove(p, hook); await sleep(1200); }
        const n0 = await H.ev(`${k}.S().game.n`);
        const g1seat = await H.ev(`${k}.seatOf(${J(pids[1])})`);
        const spec0 = await g2.ev(`${k}.claim(${g1seat})`);
        /* g1 백그라운드 21초(숨김 + 얼림) */
        await g1.hide(true);
        await sleep(21000);
        const mid = await H.ev(`(()=>{const m=${k}.S().roster.find(m=>m.p===${J(pids[1])});return {c:m&&m.c,owner:${k}.S().tk.seats[${g1seat}].p===${J(pids[1])},bot:!!${k}.S().tk.seats[${g1seat}].bot}})()`);
        const steal = await g2.ev(`${k}.claim(${g1seat})`);
        const rel = await H.ev(`${k}.release(${g1seat})`);
        await g1.show();
        await g1.wait(`(${k}.S().roster.find(m=>m.p===${J(pids[1])})||{}).c==='on'`, 12000).catch(() => {});
        await H.wait(`(${k}.S().roster.find(m=>m.p===${J(pids[1])})||{}).c==='on'`, 12000).catch(() => {});
        const after = await H.ev(`({owner:${k}.S().tk.seats[${g1seat}].p===${J(pids[1])},bot:!!${k}.S().tk.seats[${g1seat}].bot})`);
        /* 돌아온 g1 이 직접 둘 수 있다 */
        let moved = false;
        for (let i = 0; i < 12 && !moved; i++) { const m1 = await rvMove(g1, hook); if (m1 >= 0) moved = true; else { await rvMove(H, hook); await sleep(1300); } }
        await sleep(1500);
        const n1 = await H.ev(`${k}.S().game.n`);
        ok('T3', spec0 && !spec0.ok && steal && !steal.ok && mid.owner && after.owner && !after.bot && rel === false && moved && n1 > n0,
            '리버시 21초 백그라운드 → 자리 유지 · 관전자 착석 불가 · 방장도 60초 전엔 못 넘김 · 돌아와 직접 둠', { spec0, steal, mid, rel, after, moved, n0, n1 });
        /* 턴 시간(30초) — 한 판 더 → 옵션 → 시간 초과 자동 수 */
        await H.ev(`${k}.rematch()`); await sleep(600);
        await H.ev(`${k}.setOpt('turnSec',30)`); await g1.ev(`${k}.ready(true)`); await sleep(500);
        await H.ev(`${k}.start()`);
        await H.wait(`${k}.S().phase==='playing'&&${k}.S().turn&&${k}.S().turn.deadline`, 10000);
        await eqAll(all, `${k}.S().phase==='playing'&&${k}.S().turn&&${k}.S().turn.deadline`, 8000);
        const rem = await Promise.all(all.map(p => p.ev(`({t:Date.now(),r:${k}.remain()})`)));
        const adj = rem.map(x => x.r + (x.t - rem[0].t)), skew = Math.max(...adj) - Math.min(...adj);
        await H.ev(`(()=>{window.__rvAuto=null;${k}.room.on('state',S=>{if(S.tk&&S.tk.ev&&S.tk.ev.auto&&!window.__rvAuto)window.__rvAuto={a:S.tk.ev.auto,t:Date.now()}});return 1})()`);
        const t0 = Date.now();
        await H.wait(`!!window.__rvAuto`, 40000).catch(() => {});
        const au = await H.ev(`window.__rvAuto`);
        const tmShown = await g2.ev(`(document.getElementById('rvTm')||{}).textContent||''`);
        ok('T3b', au && au.a === 'timeout' && Date.now() - t0 > 25000 && skew <= 300, '리버시 턴 시간 30초 추가 — 초과 시 방장이 대신 둠 · 표시 차 ≤300ms', { au, waited: Date.now() - t0, skew: Math.round(skew), tmShown });
        const exc = all.map(p => p.exc.slice(0, 3)).filter(x => x.length);
        ok('T3z', !exc.length, 'reversi 페이지 예외 0', exc);
    } finally { await closePages(E, all); }
}

/* ================================================================
   PRISM-HEX — 기본 흐름 · T11 방 5회 출입 뒤 interval·리스너 수 불변
   ================================================================ */
async function prism(ctx) {
    const { E, relay, ok, want } = ctx;
    const r = await room(E, 'prism-hex', 2, { px: 'p', hook: '__prismhexV2' });
    const { H, G, hook, all } = r, [g1, g2] = G, k = K(hook);
    const extra = [];
    try {
        await g1.ev(`${k}.ready(true)`); await g2.ev(`${k}.ready(true)`); await H.ev(`${k}.setOpt('turnSec',30)`); await sleep(400);
        await H.shot('prism_1lobby_host'); await g1.shot('prism_1lobby_guest');
        await H.ev(`${k}.start()`);
        let eq = await eqAll(all, `${k}.S().phase==='playing'&&${k}.S().game.game+':'+${k}.S().game.np`, 15000);
        const t0 = Date.now();
        while (Date.now() - t0 < 25000) { for (const p of all) await p.ev(`${hook}.playMine()`).catch(() => 0); await sleep(500); }
        await H.shot('prism_2play_host'); await g1.shot('prism_2play_guest');
        const eq2 = await eqAll(all, `${k}.S().game.tn+':'+${k}.S().game.pl.length`, 10000);
        const tn = eq2.ok ? +eq2.v.split(':')[0] : 0;
        ok('T11a', eq.ok && eq2.ok && tn >= 3, 'prism-hex v2: 3인 시작 → 수 진행 · 전원 같은 판', { start: eq.v || eq.vals, now: eq2.v || eq2.vals });
        /* T11: 같은 탭에서 방 5회 출입(참가→나가기) — interval·window/document 리스너 수 */
        const L = await gamePage(E, 'pL', { nick: 'Leak' }); extra.push(L);
        await L.nav('/games/prism-hex/index.html?rooms=v2');
        await L.wait(`!!window.${hook}`, 15000);
        await L.ev(`${hook}.v2Ready().then(()=>1)`);
        const cyc = async () => {
            await L.ev(`LpRooms.join({code:${J(r.code)}}).then(()=>1)`);
            await L.wait(`${hook}.on`, 15000);
            await sleep(2500);
            await L.ev(`${k}.leave(true).then(()=>1)`);
            await L.wait(`!${hook}.on`, 8000);
            await sleep(800);
        };
        await cyc();
        const base = await L.ev(`({iv:window.__iv.size,ls:window.__ls.n})`);
        for (let i = 0; i < 5; i++) await cyc();
        const after = await L.ev(`({iv:window.__iv.size,ls:window.__ls.n})`);
        ok('T11', after.iv <= base.iv && after.ls <= base.ls, '프리즘: 방 5회 출입 뒤 interval·리스너 수 불변(누수 0)', { base, after });
        const exc = all.concat(extra).map(p => p.exc.slice(0, 3)).filter(x => x.length);
        ok('T11z', !exc.length, 'prism-hex 페이지 예외 0', exc);
    } finally { await closePages(E, all.concat(extra)); }
}

/* ================================================================
   MAHJONG-TW — T6 손패 복호화 불가 · 판 뒤 배분 검증 ✓ · T8 방장 크래시 → 승계 없음·대기 안내
   ================================================================ */
const TRYDEC = `async function(env,purpose){const r=LpRooms.current(),U=LpRooms.util,te=new TextEncoder(),td=new TextDecoder();
  let d;if(env.c){const key=r._mk[env.c.k];if(!key)return {err:'nomk'};d=JSON.parse(td.decode(await crypto.subtle.decrypt({name:'AES-GCM',iv:U.ub64u(env.c.iv)},key,U.ub64u(env.c.ct))))}else d=JSON.parse(env.j);
  const b=d.x;try{const pub=await crypto.subtle.importKey('raw',U.ub64u(b.epk),{name:'ECDH',namedCurve:'P-256'},false,[]);
    const bits=await crypto.subtle.deriveBits({name:'ECDH',public:pub},r._dev.dh.priv,256);
    const ikm=await crypto.subtle.importKey('raw',bits,'HKDF',false,['deriveKey']);
    const k=await crypto.subtle.deriveKey({name:'HKDF',hash:'SHA-256',salt:te.encode(r.code),info:te.encode('lpr2-ecies|'+purpose)},ikm,{name:'AES-GCM',length:256},false,['decrypt']);
    const pt=JSON.parse(td.decode(await crypto.subtle.decrypt({name:'AES-GCM',iv:U.ub64u(b.iv)},k,U.ub64u(b.ct))));return {ok:true,seat:pt.seat,n:(pt.hand||[]).length}}catch(e){return {ok:false,err:String(e&&e.name||e)}}}`;
async function mahjong(ctx) {
    const { E, relay, ok, want } = ctx;
    const r = await room(E, 'mahjong-tw', 2, { px: 'm', hook: '__mahjongtwV2' });
    const { H, G, hook, all } = r, [g1, g2] = G, k = K(hook);
    try {
        const pids = await Promise.all(all.map(p => p.ev(`${k}.me.pid`)));
        const lis = A.listener(relay, r.code);
        relay.resetStats(); relay.stats.logOn = true;
        await g1.ev(`${k}.ready(true)`); await g2.ev(`${k}.ready(true)`); await H.ev(`${k}.setOpt('speed','f')`); await sleep(400);
        await H.shot('mahjong_1lobby_host'); await g1.shot('mahjong_1lobby_guest');
        await H.ev(`${hook}.v2Start()`);
        const eq = await eqAll(all, `${k}.S().phase==='playing'&&!!${hook}.V&&${hook}.V.phase==='play'&&${hook}.V.handNo`, 20000);
        await sleep(1500);
        await H.shot('mahjong_2play_host'); await g1.shot('mahjong_2play_guest');
        const mine = await Promise.all(all.map(p => p.ev(`({seat:${k}.seat(),ps:${hook}.P&&${hook}.P.seat,n:${hook}.P&&${hook}.P.hand?${hook}.P.hand.length:0,pubHands:!!(${k}.S().game&&${k}.S().game.hands),bots:${k}.S().tk.seats.filter(x=>x.bot).length})`)));
        ok('T6a', eq.ok && mine.every(m => m.seat === m.ps && m.n >= 16) && !mine[1].pubHands && !mine[2].pubHands && mine[0].bots === 1,
            'mahjong v2: 3인+봇1 시작 · 각자 자기 손패만(공개 상태엔 손패 없음)', mine);
        /* 다른 좌석 손패 봉투: g2 는 방 봉인키로 겉은 열 수 있어도 안쪽(ECIES, g1 기기 키)은 못 연다. g1 은 연다 */
        const privTo1 = relay.stats.log.filter(x => x.event === 'h').map(x => JSON.parse(x.raw)).filter(e => e.e === 'priv' && e.to === pids[1]).slice(-1)[0];
        const byG2 = privTo1 ? await g2.ev(`(${TRYDEC})(${J(privTo1)},'priv')`) : null;
        const byG1 = privTo1 ? await g1.ev(`(${TRYDEC})(${J(privTo1)},'priv')`) : null;
        const leak = lis.got.filter(t => /"hand"|"wall"/.test(t)).length;
        ok('T6', privTo1 && byG1 && byG1.ok && byG1.n >= 16 && byG2 && !byG2.ok && leak === 0,
            '손패: 다른 좌석·청취자 복호화 불가(ECIES) · 채널 원문에 손패/패산 0', { byG1, byG2, leak, heard: lis.got.length });
        /* 한 판 끝까지(사람 3명은 자동으로 버리기·넘기기) → 방장 시드 공개 → 모두 배분 검증 */
        const t0 = Date.now();
        while (Date.now() - t0 < 200000) {
            for (const p of all) await p.ev(`${hook}.autoplay()`).catch(() => 0);
            if ((await H.ev(`${hook}.G&&${hook}.G.phase`)) === 'end') break;
            await sleep(250);
        }
        const ph = await H.ev(`${hook}.G&&${hook}.G.phase`);
        await Promise.all(G.map(g => g.wait(`${hook}.dealLog.length>0`, 15000).catch(() => {})));
        const logs = await Promise.all(G.map(g => g.ev(`${hook}.dealLog`)));
        ok('T6b', ph === 'end' && logs.every(l => l.length && l[0].ok && l[0].mine === true), '판 끝 → 방장 시드 공개 → 각자 다시 섞어 첫 손패 일치(배분 검증 ✓)', { ph, logs, secs: Math.round((Date.now() - t0) / 1000) });
        relay.stats.logOn = false; lis.stop();
        /* T8: 방장 크래시(소켓만) → 확인 중·끊김 → 30s 뒤에도 승계 없음 · '방장을 기다리는 중'(3) */
        await H.ev(`document.querySelector('#ovEnd .btn.pri')&&document.querySelector('#ovEnd .btn.pri').click(),1`);
        await sleep(3000);
        relay.partition('mH');
        const tP = Date.now();
        let l1 = null, l2 = null, l3 = null, took = false;
        while (Date.now() - tP < 42000) {
            const x = await Promise.all(G.map(g => g.ev(`({lv:${k}.hostLost(),h:${k}.isHost})`)));
            if (x.some(v => v.h)) took = true;
            const lv = Math.min(...x.map(v => v.lv));
            if (lv >= 1 && !l1) l1 = Date.now() - tP; if (lv >= 2 && !l2) l2 = Date.now() - tP; if (lv >= 3 && !l3) l3 = Date.now() - tP;
            await sleep(500);
        }
        /* 방장 끊김 띠: 공통 UI(.lpr-band) 가 있으면 그것, 없으면 커널 폴백(.lpt-ban) */
        const ban = await g1.ev(`(()=>{const u=document.querySelector('.lpr-band');if(u)return u.textContent;const b=document.querySelector('.lpt-ban');return b&&!b.classList.contains('hide')?b.textContent:''})()`);
        ok('T8', !took && l1 && l2 && l3 && l2 - l1 >= 6500 && l3 - l1 >= 16500 && /방장|host/i.test(ban), '방장 크래시(마작, 숨은 정보) → 승계 없음 · 12s/20s/30s 대기 안내', { l1, l2, l3, took, ban });
        relay.partition('mH', false);
        const exc = all.map(p => p.exc.slice(0, 3)).filter(x => x.length);
        ok('T6z', !exc.length, 'mahjong 페이지 예외 0', exc);
    } finally { relay.stats.logOn = false; await closePages(E, all); }
}

/* ================================================================
   GUMMY — T10 백그라운드 → 양쪽 일시정지 → 복귀 · 결과는 방장 확정(둘 다 승 없음) · 관전
   ================================================================ */
async function gummy(ctx) {
    const { E, relay, ok, want } = ctx;
    const r = await room(E, 'gummy', 2, { px: 'u', hook: '__gummyV2' });
    const { H, G, hook, all } = r, [g1, g2] = G, k = K(hook);
    try {
        const pids = await Promise.all(all.map(p => p.ev(`${k}.me.pid`)));
        await g1.ev(`${k}.ready(true)`); await sleep(400);
        await H.shot('gummy_1lobby_host'); await g1.shot('gummy_1lobby_guest');
        await H.ev(`${hook}.v2StartRound()`);
        const eq = await eqAll(all, `${hook}.G.state==='play'&&${hook}.G.round`, 20000);
        const roles = await Promise.all(all.map(p => p.ev(`${hook}.isPlayer()`)));
        await sleep(6000);
        await H.shot('gummy_2play_host'); await g1.shot('gummy_2play_guest'); await g2.shot('gummy_2play_spectator');
        const specSees = await g2.ev(`(()=>{const P=${hook}.G.players;return P.length===2&&P.every(p=>p.kind==='remote')&&(P[0].b.some(x=>x)||P[1].b.some(x=>x)||!!P[0].piece||!!P[1].piece)})()`);
        ok('T10a', eq.ok && roles[0] && roles[1] && !roles[2] && specSees, 'gummy v2: 1:1 시작(공정 시드) · 3번째는 관전(두 판 시청)', { eq: eq.v || eq.vals, roles, specSees });
        /* g1 11초 백그라운드 → 양쪽 멈춤 → 복귀 → 이어서 */
        await g1.hide(true);
        await sleep(2000);
        await H.shot('gummy_3paused_host');
        const hp = await H.ev(`({p:${hook}.G.paused,pz:!!(${k}.S().game.pz&&${k}.S().game.pz.on)})`);
        await sleep(9000);
        await g1.show();
        const dbgPz = [];
        for (let i = 0; i < 7; i++) { await sleep(500); dbgPz.push(await Promise.all([H, g1].map(p => p.ev(`JSON.stringify({pz:${k}.S().game.pz,p:${hook}.G.paused,vis:document.visibilityState,hid:document.hidden})`)))); }
        if (process.env.MP_DEBUG) console.log('PZ', JSON.stringify(dbgPz.slice(-1)));
        const after = await Promise.all([H, g1].map(p => p.ev(`({p:${hook}.G.paused,st:${hook}.G.state,res:${hook}.G.result})`)));
        ok('T10', hp.p && hp.pz && after.every(a => !a.p && a.st === 'play' && a.res == null), '구미 11초 백그라운드 → 양쪽 일시정지 → 복귀하면 그대로 이어서(기권 없음)', { hostDuring: hp, after });
        /* K.O. → 방장 확정 → 두 화면 결과 일치 */
        await g1.ev(`__gummy.me.die(),1`);
        await sleep(4500);
        const res = await Promise.all(all.map(p => p.ev(`({r:${hook}.G.result,w:${hook}.G.wins.join(':'),st:${hook}.G.state,rw:${hook}.res&&${hook}.res.w})`)));
        ok('T10b', res[0].r === 'win' && res[1].r === 'lose' && res[0].w === '1:0' && res[1].w === '0:1' && res[2].r === 'spec' && res[2].rw === pids[0],
            'K.O. → 방장이 결과 확정 → 방장 승·게스트 패·관전자 같은 승자(둘 다 승 없음)', res);
        /* 2판: 다시 → g1 27초 백그라운드(25초 넘김) → 방장이 결과 확정, 돌아온 g1 도 같은 결과 */
        await H.ev(`document.getElementById('btnRetry').click(),1`); await g1.ev(`document.getElementById('btnRetry').click(),1`);
        const r2 = await eqAll([H, g1], `${hook}.G.state==='play'&&${hook}.G.round===2&&'r2'`, 25000);
        await sleep(1500);
        if (process.env.MP_DEBUG) console.log('R2', JSON.stringify(r2), JSON.stringify(await Promise.all([H, g1].map(p => p.ev(`({st:${hook}.G.state,r:${hook}.G.round,rd:${hook}.NET.ready,res:${hook}.G.result})`)))));
        /* 숨는 순간의 알림이 얼기 전에 못 나갈 수도 있다 → 방장은 8초 무소식으로도 멈춘다(그 뒤 25초). 넉넉히 36초 */
        await g1.hide(true);
        await sleep(36000);
        await g1.show();
        await sleep(4000);
        const res2 = await Promise.all([H, g1].map(p => p.ev(`({r:${hook}.G.result,w:${hook}.G.wins.join(':'),why:${hook}.res&&${hook}.res.why})`)));
        /* T12(구미): 판 밖(결과 화면) 10초 — 게임 스트림 주기 전송 0 */
        relay.resetStats(); relay.stats.logOn = true; await sleep(10000); relay.stats.logOn = false;
        const idle = relay.stats.log.map(x => { try { const e = JSON.parse(x.raw); return x.event + ':' + e.e; } catch (_) { return '?'; } });
        const idleX = idle.filter(e => /:x$/.test(e)).length;
        ok('T12b', idleX === 0, '구미: 결과 화면 10초 동안 게임 스트림 주기 전송 0(커널 hb 만)', { idleX, kinds: [...new Set(idle)] });
        ok('T10c', res2[0].r === 'win' && res2[1].r === 'lose' && res2[0].w === '2:0' && res2[1].w === '0:2' && res2[0].why === 'away',
            '25초 넘게 자리 비움 → 방장 확정(자리 비운 쪽 패) · 돌아온 쪽도 같은 결과', res2);
        const exc = all.map(p => p.exc.slice(0, 3)).filter(x => x.length);
        ok('T10z', !exc.length, 'gummy 페이지 예외 0', exc);
    } finally { await closePages(E, all); }
}

/* ================================================================
   V1 회귀 — 플래그 없이 열면 기존(v1) 경로 그대로: v2 비활성·예외 0
   ================================================================ */
async function v1smoke(ctx) {
    const { E, ok } = ctx;
    const games = [['yut', '__yutV2'], ['ludo', '__ludoV2'], ['reversi', '__reversiV2'], ['prism-hex', '__prismhexV2'], ['mahjong-tw', '__mahjongtwV2'], ['gummy', '__gummyV2']];
    const res = {}; const pages = [];
    for (const [g, hk] of games) {
        const P = await gamePage(E, 'v1' + g.slice(0, 3), { nick: 'Zed' }); pages.push(P);
        await P.nav('/games/' + g + '/index.html');
        await sleep(2500);
        res[g] = await P.ev(`({hook:!!window.${hk},v2:!!(window.${hk}&&${hk}.on),core:typeof LpRooms,v1:typeof LpRoom})`);
        res[g].exc = P.exc.slice(0, 2);
    }
    await closePages(E, pages);
    ok('V1', Object.values(res).every(x => x.hook && !x.v2 && x.core === 'undefined' && !x.exc.length), '플래그 없음 = v1 경로(v2 스크립트 미로드·예외 0) — 6종', res);
}

/* v1 윷 기능 회귀(플래그 없음) — 방 만들기 → PIN 링크 참가 → 준비 → 시작 */
async function v1yut(ctx) {
    const { E, ok } = ctx;
    const H = await gamePage(E, 'v1yH', { nick: 'Ann' }), Gp = await gamePage(E, 'v1yG', { nick: 'Bob' });
    try {
        await H.nav('/games/yut/index.html'); await sleep(1500);
        await H.ev(`document.getElementById('btnModeOnline').click(),document.getElementById('btnCreate').click(),1`);
        await H.wait(`!document.getElementById('scrLobby').classList.contains('hide')&&/[0-9]{4}/.test(document.getElementById('lbPin').textContent)`, 20000);
        const code = await H.ev(`document.getElementById('lbCode').textContent`), pin = (await H.ev(`document.getElementById('lbPin').textContent`)).replace(/\D/g, '');
        await Gp.nav('/games/yut/index.html?room=' + code + '&pin=' + pin + '&nick=Bob');
        await Gp.wait(`__yut.role==='guest'&&!!__yut.V&&__yut.V.phase==='lobby'`, 25000);
        await H.wait(`__yut.LB.players.length===2`, 10000);
        await Gp.ev(`document.getElementById('btnLbGo').click(),1`); await sleep(1500);
        const can = await H.ev(`!document.getElementById('btnLbGo').disabled`);
        await H.ev(`document.getElementById('btnLbGo').click(),1`);
        await Gp.wait(`__yut.V&&__yut.V.phase==='play'`, 15000);
        const st = await Promise.all([H, Gp].map(p => p.ev(`({role:__yut.role,ph:__yut.V.phase,v2:__yutV2.on})`)));
        ok('V1y', can && st.every(x => x.ph === 'play' && !x.v2) && st[0].role === 'host' && st[1].role === 'guest', 'v1 윷(기존 lpRoom 경로) — 만들기·PIN 참가·준비·시작 그대로 동작', { code, st });
        const exc = [H, Gp].map(p => p.exc.slice(0, 2)).filter(x => x.length);
        ok('V1yz', !exc.length, 'v1 윷 예외 0', exc);
    } finally { await closePages(E, [H, Gp]); }
}

export async function all(ctx) {
    const w = ctx.want;
    if (on(w, 'yut') || ['T1', 'T2', 'T4', 'T12'].some(x => on(w, x))) await yut(ctx);
    if (on(w, 'ludo') || ['T5', 'T7', 'T9'].some(x => on(w, x))) await ludo(ctx);
    if (on(w, 'reversi') || on(w, 'T3')) await reversi(ctx);
    if (on(w, 'prism') || on(w, 'T11')) await prism(ctx);
    if (on(w, 'mahjong') || ['T6', 'T8'].some(x => on(w, x))) await mahjong(ctx);
    if (on(w, 'gummy') || on(w, 'T10')) await gummy(ctx);
    if (on(w, 'v1') || !w.length) { await v1smoke(ctx); await v1yut(ctx); }
}
