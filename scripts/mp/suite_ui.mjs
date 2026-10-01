/* UI 시나리오 U1~U10 (+ U11 방장 끊김 띠 · U12 게임 전환 · U13 PIN) — DESIGN §10.2 · §4
   실제 페이지(홈 / · /lobby/ · /r/CODE)와 픽스처 게임 페이지(scripts/mp/fixtures/ugame.html 을 /games/<id>/ 로)를
   릴레이가 서빙한다. 게임 페이지는 siteFooter.js 의 v2 로더 → lpGames → lpRoomsCore → lpFair → lpRoomsUI 를 그대로 탄다.
   스크린샷: MP_SHOTS (기본 <MP_SCRATCH>/shots) — 360×740 · 412×915 · 1280×800 × ko/en/ja 시트. MP_NOSHOTS=1 이면 생략 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { closeAll } from './suites.mjs';
import { SCR } from './h.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const PUB = path.join(ROOT, 'public');
const FX = path.join(HERE, 'fixtures', 'ugame.html');
const J = JSON.stringify;
const run1 = (only, id) => !only.length || only.includes(id);
const HANGUL = /[가-힣ㄱ-ㆎ]/;

function pageFor(p) {
    if (p === '/' || p === '/index.html') return path.join(PUB, 'index.html');
    if (p === '/lobby/' || p === '/lobby' || p === '/lobby/index.html') return path.join(PUB, 'lobby', 'index.html');
    if (/^\/r\/[^/]+\/?$/.test(p)) return path.join(PUB, 'lobby', 'index.html');
    if (/^\/games\/[a-z0-9-]+\/$/.test(p)) return FX;
    return null;
}

/* 기기 1대 = 브라우저 컨텍스트 1개 */
async function dev(E, label, o = {}) {
    const P = await E.page({ label });
    const c = P.c;
    await c.send('Network.setBlockedURLs', { urls: ['*supabase.co*', '*googletagmanager.com*', '*google-analytics.com*', '*doubleclick*', '*pagead2*', '*googlesyndication*', '*fonts.googleapis.com*', '*fonts.gstatic.com*', '*cdn.jsdelivr.net*'] });
    P.vp = async (w, h) => { await c.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: w < 800 }); };
    await P.vp(o.w || 412, o.h || 915);
    if (o.ua) await c.send('Emulation.setUserAgentOverride', { userAgent: o.ua });
    let preId = null, pv = 0;
    /* 문서마다 한 번만 저장소 초기값을 심는다(버전이 바뀔 때만) */
    P.setLS = async (kv) => {
        pv++;
        if (preId) await c.send('Page.removeScriptToEvaluateOnNewDocument', { identifier: preId }).catch(() => {});
        const src = `try{if(sessionStorage.getItem('__pv')!=='${pv}'){var o=${J(kv)};for(var k in o){if(o[k]===null)localStorage.removeItem(k);else localStorage.setItem(k,o[k])}sessionStorage.setItem('__pv','${pv}')}}catch(e){}`;
        preId = (await c.send('Page.addScriptToEvaluateOnNewDocument', { source: src })).identifier;
    };
    await P.setLS(Object.assign({ luckyplz_lang: o.lang || 'ko' }, o.nick === undefined ? { lp_profile: J({ nick: label.toUpperCase(), av: (label.charCodeAt(0) % 16), v: 1 }) } : (o.nick ? { lp_profile: J({ nick: o.nick, av: 3, v: 1 }) } : { lp_profile: null })));
    P.nav = async (u, cond, ms) => {
        await c.send('Page.navigate', { url: u.startsWith('http') ? u : E.base + u });
        await P.wait(cond || `document.readyState==='complete'&&window.LpRoomsUI&&!/stub/.test(LpRoomsUI.version)`, ms || 15000);
    };
    P.shot = async (file) => {
        const r = await c.send('Page.captureScreenshot', { format: 'png' });
        fs.writeFileSync(file, Buffer.from(r.data, 'base64'));
        return file;
    };
    P.click = (sel) => P.ev(`(()=>{const e=document.querySelector(${J(sel)});if(!e)return false;e.click();return true})()`);
    P.clickText = (sel, txt) => P.ev(`(()=>{const e=[...document.querySelectorAll(${J(sel)})].find(x=>x.textContent.includes(${J(txt)}));if(!e)return false;e.click();return true})()`);
    return P;
}

async function hostRoom(H, gid = 'yut') {
    await H.nav(`/games/${gid}/?rooms=v2`);
    await H.wait(`!!document.querySelector('.lp-rooms-btn')`, 8000);
    await H.click('.lp-rooms-btn');
    await H.wait(`!!document.querySelector('.lpr-sheet .lpr-btn.go')`, 5000);
    return H;
}
async function createNow(H) {
    await H.click('.lpr-sheet .lpr-btn.go');
    await H.wait(`LpRoomsUI.room()&&LpRoomsUI.room().isHost`, 12000);
    return H.ev(`({code:LpRoomsUI.room().code,url:LpRoomsUI.room().inviteUrl()})`);
}
async function guestJoin(G, url) {
    await G.nav(url, `document.readyState==='complete'&&window.LpRoomsUI&&LpRoomsUI.room&&!!LpRoomsUI.room()`, 25000);
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

/* 화면 검사: 보이는 우리 버튼이 뷰포트 안 · 44px 이상 · 서로 안 겹침, 가로 스크롤 없음 */
const LAYOUT = `(()=>{const vw=innerWidth,vh=innerHeight,bad=[];
 const vis=e=>{const r=e.getBoundingClientRect();if(!r.width||!r.height)return null;for(let n=e;n&&n.nodeType===1;n=n.parentElement){const cs=getComputedStyle(n);if(cs.display==='none'||cs.visibility==='hidden'||+cs.opacity<.05)return null}return r};
 const bs=[...document.querySelectorAll('.lpr-root button,.lpr-root [role=button],.lp-rooms-btn')].map(e=>[e,vis(e)]).filter(x=>x[1]);
 const top=[...document.querySelectorAll('.lpr-bd,.lpr-card')].pop();
 const hs=e=>{for(let n=e.parentElement;n&&n!==document.body;n=n.parentElement){const o=getComputedStyle(n).overflowX;if(o==='auto'||o==='scroll')return true}return false};
 for(const [e,r] of bs){const inTop=!top||top.contains(e);if(!inTop)continue;
  if((r.left<-1||r.right>vw+1)&&!hs(e))bad.push('offx:'+(e.textContent||e.className).trim().slice(0,12));
  /* HUD 알약(32px)·배지·도크 👥(38px, 도크 규격) 는 ::before 로 누르는 범위를 44px 이상 넓혀 둔다 */
  const small=Math.min(r.width,r.height)<43.5&&!e.classList.contains('lpr-hud')&&!e.classList.contains('lpf-badge')&&!e.classList.contains('lp-rooms-btn')&&!e.closest('.lpr-avs');
  if(small)bad.push('small:'+(e.textContent||e.className).trim().slice(0,12)+'@'+Math.round(r.width)+'x'+Math.round(r.height));}
 for(let i=0;i<bs.length;i++)for(let j=i+1;j<bs.length;j++){const a=bs[i][1],b=bs[j][1];if(bs[i][0].contains(bs[j][0])||bs[j][0].contains(bs[i][0]))continue;
  const ov=Math.min(a.right,b.right)-Math.max(a.left,b.left),oh=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
  if(ov>2&&oh>2&&(!top||(top.contains(bs[i][0])===top.contains(bs[j][0]))))bad.push('overlap:'+bs[i][0].textContent.trim().slice(0,8)+'|'+bs[j][0].textContent.trim().slice(0,8))}
 if(document.scrollingElement.scrollWidth>vw+1)bad.push('hscroll');
 return bad.slice(0,8)})()`;

async function sheetPng(E, files, out, cols, title) {
    /* 스크린샷 여러 장 → 시트 한 장 (브라우저에 data URL 로 깔고 찍는다) */
    const P = await E.page({ label: 'sheet' });
    try {
        const imgs = files.map(f => ({ n: path.basename(f, '.png'), d: 'data:image/png;base64,' + fs.readFileSync(f).toString('base64') }));
        const html = `<html><body style="margin:0;background:#222;color:#eee;font:13px system-ui"><div style="padding:6px 8px;font-weight:700">${title}</div><div style="display:grid;grid-template-columns:repeat(${cols},1fr);gap:6px;padding:6px">${imgs.map(i => `<figure style="margin:0"><img src="${i.d}" style="width:100%;display:block;border:1px solid #555"><figcaption>${i.n}</figcaption></figure>`).join('')}</div></body></html>`;
        const tmp = path.join(path.dirname(out), '_sheet.html'); fs.writeFileSync(tmp, html);
        await P.c.send('Emulation.setDeviceMetricsOverride', { width: 1600, height: 900, deviceScaleFactor: 1, mobile: false });
        await P.c.send('Page.navigate', { url: 'file:///' + tmp.replace(/\\/g, '/') });
        await sleep(900);
        const h = await P.ev('document.documentElement.scrollHeight');
        await P.c.send('Emulation.setDeviceMetricsOverride', { width: 1600, height: Math.min(h, 16000), deviceScaleFactor: 1, mobile: false });
        await sleep(300);
        const r = await P.c.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
        fs.writeFileSync(out, Buffer.from(r.data, 'base64'));
        fs.unlinkSync(tmp);
    } finally { await closeAll(E, [P]); }
    return out;
}

export async function ui(ctx) {
    /* pageFor(게임 경로 → UI 픽스처)는 이 스위트 동안만 — 끝나면 되돌린다(뒤 스위트가 하네스 페이지를 못 받아 죽던 순서 의존) */
    const prevPageFor = ctx.relay.pageFor;
    try { return await uiRun(ctx); } finally { ctx.relay.pageFor = prevPageFor || null; }
}
async function uiRun(ctx) {
    const { E, relay, ok, only } = ctx;
    relay.pageFor = pageFor;
    const SHOTS = process.env.MP_SHOTS || path.join(SCR, 'shots');
    fs.mkdirSync(SHOTS, { recursive: true });
    const layoutBad = [];

    /* ── U4·U5·U7·U1 기본 흐름: 방장 생성 → /r/ 링크 참가 → 대기실 → 시작 → HUD ── */
    if (run1(only, 'U5') || run1(only, 'U4') || run1(only, 'U1') || run1(only, 'U7')) {
        const H = await dev(E, 'uh', { lang: 'ko', w: 360, h: 740 }), G = await dev(E, 'ug', { lang: 'ko', w: 360, h: 740 });
        try {
            await hostRoom(H); const c = await createNow(H);
            await H.wait(`!!document.querySelector('.lpr-lobby')`, 5000);
            const t0 = Date.now();
            await guestJoin(G, c.url);
            const where = await G.ev(`({p:location.pathname,s:location.search,h:location.hash,href:location.href,code:LpRoomsUI.room().code,inv:!!sessionStorage.getItem('lpr_inv')})`);
            ok('U5', where.p === '/games/yut/' && where.s === '?r=' + c.code && !where.h && !/#k=/.test(where.href) && where.code === c.code, '/r/CODE#k= → right game page, fragment gone from address bar, joined', Object.assign({ ms: Date.now() - t0 }, where));
            await H.wait(`LpRoomsUI.room().roster().length===2`, 6000);
            await sleep(300);
            const live = await H.ev(`(document.querySelector('.lpr-sr[aria-live]')||{}).textContent||''`);
            ok('U7', /UG/.test(live) && /입장/.test(live), 'aria-live=polite announces the join on host', live);
            /* U1: 360×740 대기실 스크롤 없음 (방장·게스트) */
            await G.ev(`LpRoomsUI.room().intent('pick',{key:'char',val:'b'})`); await G.ev(`LpRoomsUI.room().intent('ready',true)`);
            await H.wait(`LpRoomsUI.room().canStart()`, 5000); await sleep(300);
            const fit = (P) => P.ev(`(()=>{const lb=document.querySelector('.lpr-lb'),ft=document.querySelector('.lpr-ft'),r=ft.getBoundingClientRect(),b=document.querySelector('.lpr-body');return {doc:document.scrollingElement.scrollHeight<=innerHeight+1,lb:lb.scrollHeight<=lb.clientHeight+1,ft:r.bottom<=innerHeight+1,body:b.scrollHeight<=b.clientHeight+1,h:innerHeight}})()`);
            const fh = await fit(H), fg = await fit(G);
            ok('U1', Object.values(fh).every(Boolean) && Object.values(fg).every(Boolean), '360×740 full lobby fits without scroll (host & guest)', { fh, fg });
            /* U4: v2 페이지에 v1 부유 UI 0, 플레이 중 HUD 1개 */
            await H.click('.lpr-ft .lpr-btn.go');
            await Promise.all([H, G].map(P => P.wait(`LpRoomsUI.room().state().phase==='playing'&&!document.querySelector('.lpr-lobby')`, 6000)));
            await sleep(400);
            const fl = (P) => P.ev(`({v1:[...document.scripts].filter(s=>/lpRoom\\.js|lpMultiplayer|lpHostCtl|lpInviteButton/.test(s.src)).length,g:!!(window.LpRoom||window.LpMultiplayer||window.LpHostCtl||window.LpInviteButton),
                fl:document.querySelectorAll('.lp-mp-panel,.lp-room-status,.lp-hostctl,.lp-invite-fab,#lpInviteFab,.lp-mp-fab').length,
                hud:[...document.querySelectorAll('.lpr-hud')].filter(e=>getComputedStyle(e).display!=='none').length,
                rooms:[...document.querySelectorAll('.lpr-root')].filter(e=>e.getBoundingClientRect().width&&getComputedStyle(e).display!=='none').map(e=>e.className)})`);
            const fH = await fl(H), fG = await fl(G);
            ok('U4', fH.v1 === 0 && !fH.g && fH.fl === 0 && fH.hud === 1 && fG.v1 === 0 && fG.hud === 1 && fH.rooms.length === 1 && fG.rooms.length === 1, 'v2 page: no v1 scripts/floating UI, exactly one HUD pill while playing', { fH, fG });
            layoutBad.push(...(await H.ev(LAYOUT)).map(x => 'hud-host ' + x));
            /* v1 기본(플래그 없음) 페이지는 예전대로 v1 */
            const V = await dev(E, 'uv', { lang: 'ko' });
            try {
                /* 표(레지스트리)에서 아직 v1 인 게임을 고른다 — 예전엔 ludo 로 고정이라 2026-09-30 보드게임 v2 전환 뒤 늘 실패했다 */
                const v1g = await H.ev(`(LpGames.all().find(g=>g.mp&&g.mp.v==='v1'&&g.mp.v1&&!g.mp.later)||{}).id||null`);
                if (!v1g) throw Object.assign(new Error('skip'), { skipU4b: true });
                await V.c.send('Page.navigate', { url: E.base + '/games/' + v1g + '/' });
                await V.wait(`document.readyState==='complete'&&[...document.scripts].some(s=>/lpRoom\\.js/.test(s.src))`, 10000);
                await sleep(500);
                const v = await V.ev(`({v2:[...document.scripts].filter(s=>/lpRoomsCore|lpRoomsUI/.test(s.src)).length,v1:[...document.scripts].filter(s=>/lpRoom\\.js|lpHostCtl|lpMultiplayer|lpInviteButton/.test(s.src)).length,btn:!!document.querySelector('.lp-rooms-btn')})`);
                ok('U4b', v.v2 === 0 && v.v1 === 4 && !v.btn, 'default game page (registry v1: ' + v1g + ') keeps the v1 stack, no v2 scripts', v);
            } catch (e) { if (!e.skipU4b) throw e; ok('U4b', true, 'no game left on the v1 flag — nothing to check'); } finally { await closeAll(E, [V]); }
        } finally { await closeAll(E, [H, G]); }
    }

    /* ── U2: 비한국어 15개 언어 — 방 UI 한글 0 ── */
    if (run1(only, 'U2')) {
        const H = await dev(E, 'u2h', { lang: 'en', nick: 'Host' }), G = await dev(E, 'u2g', { lang: 'en', nick: 'Guest' });
        try {
            await hostRoom(H); const c = await createNow(H); await guestJoin(G, c.url);
            await H.wait(`LpRoomsUI.room().roster().length===2`, 6000);
            const LANGS = ['en', 'ja', 'zh', 'es', 'pt', 'de', 'fr', 'ru', 'ar', 'hi', 'th', 'id', 'vi', 'tr', 'gb'];
            const hits = {};
            for (const L of LANGS) {
                const txt = await H.ev(`(async()=>{localStorage.setItem('luckyplz_lang',${J(L)});document.dispatchEvent(new CustomEvent('lp:langchanged',{detail:{lang:${J(L)}}}));
                    await new Promise(r=>setTimeout(r,150));const out=[];const grab=()=>document.querySelectorAll('.lpr-root').forEach(e=>out.push(e.innerText+' '+[...e.querySelectorAll('[aria-label]')].map(x=>x.getAttribute('aria-label')).join(' ')));
                    grab();const UI=LpRoomsUI,r=UI.room();
                    UI.openRoom(r);grab();document.querySelectorAll('.lpr-bd').forEach(b=>b.remove());
                    UI.openInvite(r);grab();document.querySelectorAll('.lpr-bd').forEach(b=>b.remove());
                    UI.openJoin();grab();document.querySelectorAll('.lpr-bd').forEach(b=>b.remove());
                    UI.openSwitch(r);grab();document.querySelectorAll('.lpr-bd').forEach(b=>b.remove());
                    const m=document.querySelector('.lpr-lobby .lpr-m.tap');if(m){m.click();grab();document.querySelector('.lpr-sheet .lpr-btn.wide').click();grab();}
                    document.querySelectorAll('.lpr-bd').forEach(b=>b.remove());
                    const bh=document.createElement('span');document.body.appendChild(bh);UI.badge(bh,{kind:'verified',n:3});out.push(bh.textContent);bh.remove();
                    return out.join('\\n')})()`);
                const g = txt.match(new RegExp(HANGUL.source, 'g'));
                if (g) hits[L] = txt.split('\n').filter(l => HANGUL.test(l)).slice(0, 3);
            }
            ok('U2', !Object.keys(hits).length, '15 non-Korean languages: no Hangul in lobby·room·invite·join·switch·member·confirm sheets·badge', Object.keys(hits).length ? hits : LANGS.length + ' langs clean');
        } finally { await closeAll(E, [H, G]); }
    }

    /* ── U3: 인앱 UA — window.confirm/alert/prompt 0회, 자체 확인창 ── */
    if (run1(only, 'U3')) {
        const UA = 'Mozilla/5.0 (Linux; Android 13; SM-S911N Build/TP1A.220624.014; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.230 Mobile Safari/537.36 KAKAOTALK/10.4.5';
        const H = await dev(E, 'u3h', { lang: 'ko' }), G = await dev(E, 'u3g', { lang: 'ko', ua: UA });
        try {
            await hostRoom(H); const c = await createNow(H);
            /* '여기서 계속'을 고른 인앱 사용자(lp_iab_stay) — 헤드리스에서 kakaotalk:// 로 튕기지 않게 lp_kko_out 도 */
            const pre = `window.__dlg=0;['confirm','alert','prompt'].forEach(k=>{window[k]=function(){window.__dlg++;return true}});try{sessionStorage.setItem('lp_iab_stay','1');sessionStorage.setItem('lp_kko_out','1')}catch(e){}`;
            await G.c.send('Page.addScriptToEvaluateOnNewDocument', { source: pre });
            await H.ev(`window.__dlg=0;['confirm','alert','prompt'].forEach(k=>{window[k]=function(){window.__dlg++;return true}})`);
            const u = c.url.replace('#', (c.url.includes('?') ? '&' : '?') + 'lp_iab=off#');
            await guestJoin(G, u);
            const ia = await G.ev(`({ia:!!window.LpInApp,we:window.LpInApp&&typeof LpInApp.willEscape==='function'?LpInApp.willEscape():'n/a',app:window.LpInApp&&LpInApp.info&&LpInApp.info.app})`);
            await H.wait(`LpRoomsUI.room().roster().length===2`, 6000);
            /* 방장: 명단 행 → 내보내기 → 자체 확인창 → 확인 */
            const rowInfo = await H.wait(`(()=>{const r=[...document.querySelectorAll('.lpr-lobby .lpr-m')];const t=document.querySelector('.lpr-lobby .lpr-m.tap');return t?{rows:r.length,tap:true}:null})()`, 6000).catch(async e => { console.log('U3 rows', await H.ev(`[...document.querySelectorAll('.lpr-lobby .lpr-m')].map(e=>e.className+'|'+e.textContent.slice(0,20)).join(' ;; ')+' // sheets='+document.querySelectorAll('.lpr-sheet').length`)); throw e; });
            await H.click('.lpr-lobby .lpr-m.tap');
            await H.wait(`!!document.querySelector('.lpr-sheet')`, 3000);
            await H.clickText('.lpr-sheet .lpr-btn', '내보내기');
            await H.wait(`[...document.querySelectorAll('.lpr-sheet .lpr-sh-t')].some(e=>/내보낼까요/.test(e.textContent))`, 3000);
            const own = await H.ev(`!!document.querySelector('.lpr-sheet .lpr-btn.pri')`);
            await H.click('.lpr-sheet .lpr-btn.pri');
            await G.wait(`!LpRoomsUI.room()&&!!document.querySelector('.lpr-card')`, 6000);
            const d = { host: await H.ev('window.__dlg'), guest: await G.ev('window.__dlg') };
            ok('U3', ia.ia && ia.we === false && own && d.host === 0 && d.guest === 0, 'in-app UA (KakaoTalk, lp_iab=off): willEscape() exposed, kick uses in-page confirm, 0 native dialogs; kicked guest sees in-page card', { ia, d });
        } finally { await closeAll(E, [H, G]); }
    }

    /* ── U6: 옛 ?room=&pin=&nick= 링크 → v1 경로 · 홈 참가 상자 → resolve 라우팅 ── */
    if (run1(only, 'U6')) {
        const V = await dev(E, 'u6v', { lang: 'ko' }), H = await dev(E, 'u6h', { lang: 'ko' });
        try {
            await V.c.send('Page.navigate', { url: E.base + '/games/yut/?room=ABC123&pin=1234&nick=old' });
            await V.wait(`document.readyState==='complete'&&[...document.scripts].some(s=>/lpRoom\\.js/.test(s.src))`, 10000);
            const v = await V.ev(`({v2:[...document.scripts].filter(s=>/lpRoomsCore|lpRoomsUI/.test(s.src)).length,q:location.search})`);
            await V.c.send('Page.navigate', { url: E.base + '/lobby/?room=ABC123' });
            await V.wait(`document.readyState==='complete'`, 8000); await sleep(400);
            const lg = await V.ev(`({legacy:document.body.classList.contains('lp-legacy'),card:getComputedStyle(document.querySelector('.lobby-card')).display,v2:[...document.scripts].filter(s=>/lpRoomsUI/.test(s.src)).length})`);
            /* 홈의 👥 참가 → v2 openJoin → v2 코드 → 그 게임으로 */
            await hostRoom(H); const c = await createNow(H);
            await V.setLS({ luckyplz_lang: 'ko', lp_profile: J({ nick: 'Vee', av: 2, v: 1 }) });
            await V.c.send('Page.navigate', { url: E.base + '/' });
            await V.wait(`document.readyState==='complete'&&!!document.getElementById('lpHomeJoinBtn')`, 10000);
            await sleep(300);
            await V.ev(`document.getElementById('lpHomeJoinBtn').click()`);
            await V.wait(`!!document.querySelector('.lpr-sheet .lpr-cells input')`, 8000);
            await V.ev(`(()=>{const i=document.querySelector('.lpr-sheet .lpr-cells input');i.value=${J(c.code)};i.dispatchEvent(new Event('input'))})()`);
            await V.wait(`location.pathname==='/games/yut/'&&window.LpRoomsUI&&LpRoomsUI.room&&!!LpRoomsUI.room()`, 20000);
            const hv = await V.ev(`({p:location.pathname,s:location.search,code:LpRoomsUI.room().code})`);
            ok('U6', v.v2 === 0 && lg.legacy && lg.card === 'block' && lg.v2 === 0 && hv.code === c.code && hv.s === '?r=' + c.code,
                'old ?room=&pin=&nick= → v1 stack (game + /lobby/ legacy card); home Join box → LpRooms.resolve → game page → joined', { v, lg, hv });
        } finally { await closeAll(E, [V, H]); }
    }

    /* ── U8: 닉네임 양방향 제어문자 제거 (참가 시트에 직접 입력) ── */
    if (run1(only, 'U8')) {
        const H = await dev(E, 'u8h', { lang: 'en' }), G = await dev(E, 'u8g', { lang: 'en', nick: '' });
        try {
            await hostRoom(H); const c = await createNow(H);
            await G.nav(c.url, `document.readyState==='complete'&&!!document.querySelector('.lpr-sheet .lpr-prof input')`, 20000);
            await G.ev(`(()=>{const i=document.querySelector('.lpr-sheet .lpr-prof input');i.value='\\u202Eev\\u200Bil\\u2066x\\u2069';i.dispatchEvent(new Event('input'))})()`);
            await G.click('.lpr-sheet .lpr-btn.go');
            await G.wait(`!!(LpRoomsUI.room())`, 15000);
            await H.wait(`LpRoomsUI.room().roster().length===2&&document.querySelectorAll('.lpr-lobby .lpr-mn').length===2`, 6000);
            const n = await H.ev(`LpRoomsUI.room().roster().find(m=>m.r!=='host').n`);
            const shown = await H.ev(`[...document.querySelectorAll('.lpr-lobby .lpr-mn')].map(e=>e.firstChild.textContent).join('|')`);
            ok('U8', n === 'evilx' && !/[​-‏‪-‮⁦-⁩]/.test(shown), 'nickname typed with bidi/zero-width controls → stored & rendered clean', { n: J(n), shown: J(shown) });
        } finally { await closeAll(E, [H, G]); }
    }

    /* ── U9: 허브 최근 방 점 (살아있는 방 ● / 없는 방 ○) ── */
    if (run1(only, 'U9')) {
        const H = await dev(E, 'u9h', { lang: 'ko' }), G = await dev(E, 'u9g', { lang: 'ko' });
        try {
            await hostRoom(H); const c = await createNow(H); await guestJoin(G, c.url);
            await G.ev(`LpRoomsUI.room().leave()`); await sleep(300);
            await G.ev(`(()=>{const l=JSON.parse(localStorage.getItem('lpr_recent')||'[]');l.push({code:'ZZ9Q7X',g:'ludo',h:'ghost',t:Date.now()-9e5});localStorage.setItem('lpr_recent',JSON.stringify(l))})()`);
            await G.nav('/lobby/', `!!document.querySelector('#lprHub .lpr-hubt')`, 12000);
            await G.wait(`[...document.querySelectorAll('#lprHub .lpr-m')].filter(r=>r.hasAttribute('data-alive')).length>=2`, 15000);
            const rows = await G.ev(`[...document.querySelectorAll('#lprHub .lpr-m')].map(r=>r.querySelector('.lpr-code').textContent+':'+r.getAttribute('data-alive'))`);
            const fmt = c.code.slice(0, 3) + '-' + c.code.slice(3);
            ok('U9', rows.includes(fmt + ':1') && rows.includes('ZZ9-Q7X:0'), 'hub recent rooms: live room ●, dead room ○', rows);
            /* 최근 방 탭 = 재입장 */
            await G.ev(`[...document.querySelectorAll('#lprHub .lpr-m')].find(r=>r.getAttribute('data-alive')==='1').click()`);
            await G.wait(`location.pathname==='/games/yut/'&&window.LpRoomsUI&&LpRoomsUI.room&&!!LpRoomsUI.room()`, 20000);
            ok('U9b', (await G.ev('LpRoomsUI.room().code')) === c.code, 'tap recent (live) → back in that room', c.code);
        } finally { await closeAll(E, [H, G]); }
    }

    /* ── U11 방장 끊김 띠 · U12 게임 전환(파티 이동) · U13 PIN ── */
    if (run1(only, 'U11') || run1(only, 'U12')) {
        const H = await dev(E, 'uh', { lang: 'ko' }), G = await dev(E, 'ug', { lang: 'ko' });
        try {
            await hostRoom(H); const c = await createNow(H); await guestJoin(G, c.url);
            if (run1(only, 'U12')) {
                await H.ev(`LpRoomsUI.openSwitch()`);
                await H.wait(`!!document.querySelector('.lpr-sheet .lpr-tile')`, 3000);
                const tiles = await H.ev(`[...document.querySelectorAll('.lpr-sheet .lpr-cat')].length`);
                await H.ev(`LpRoomsUI.room().switchGame('roulette')`);
                await Promise.all([H, G].map(P => P.wait(`location.pathname==='/games/roulette/'&&window.LpRoomsUI&&LpRoomsUI.room&&!!LpRoomsUI.room()`, 20000)));
                await sleep(600);
                const s = await Promise.all([H, G].map(P => P.ev(`({code:LpRoomsUI.room().code,host:LpRoomsUI.room().isHost,strip:!!document.querySelector('#setup>.lpr-strip'),fixed:!!document.querySelector('.lpr-strip.fixed'),lobby:!!document.querySelector('.lpr-lobby'),hud:getComputedStyle(document.querySelector('.lpr-hud')).display})`)));
                ok('U12', s.every(x => x.code === c.code && x.strip && !x.fixed && !x.lobby && x.hud === 'none') && s[0].host && !s[1].host && tiles >= 1,
                    'host switches game → both land on /games/roulette/?r= in same room; draw game shows strip in setup (HUD hidden while strip visible)', s);
                const hudBack = await G.ev(`(async()=>{document.getElementById('setup').style.display='none';await new Promise(r=>setTimeout(r,900));const d=getComputedStyle(document.querySelector('.lpr-hud')).display;document.getElementById('setup').style.display='';return d})()`);
                ok('U12b', hudBack !== 'none', 'strip hidden by game (setup screen gone) → HUD pill comes back', hudBack);
            }
            if (run1(only, 'U11')) {
                relay.partition('uh');
                await G.wait(`!!document.querySelector('.lpr-band')`, 16000);
                const b1 = await G.ev(`({t:document.querySelector('.lpr-band').textContent,hud:(document.querySelector('.lpr-hud .lpr-dot')||{}).className})`);
                relay.partition('uh', false);
                await G.wait(`!document.querySelector('.lpr-band')`, 20000);
                ok('U11', /방장/.test(b1.t) && /warn|bad/.test(b1.hud), 'host socket dies → guest band "방장 확인 중…" + HUD dot warns; host back → band gone', b1);
            }
        } finally { relay.partition('uh', false); await closeAll(E, [H, G]); }
    }
    if (run1(only, 'U13')) {
        const H = await dev(E, 'u13h', { lang: 'ko' }), G = await dev(E, 'u13g', { lang: 'ko' });
        try {
            await hostRoom(H);
            await H.click('.lpr-sheet .lpr-row .lpr-btn:not(.go)');   /* 🔑 PIN 토글 */
            const c = await createNow(H);
            const pin = await H.ev('LpRoomsUI.room().pin');
            await G.nav('/games/yut/?r=' + c.code, `!!document.querySelector('.lpr-sheet .lpr-cells input')`, 25000);
            await G.ev(`(()=>{const i=document.querySelector('.lpr-sheet .lpr-cells input');i.value='0000'===${J(pin)}?'1111':'0000';i.dispatchEvent(new Event('input'))})()`);
            await G.wait(`!!document.querySelector('.lpr-sheet .lpr-cells.bad')`, 12000);
            await G.ev(`(()=>{const i=document.querySelector('.lpr-sheet .lpr-cells input');i.value=${J(pin)};i.dispatchEvent(new Event('input'))})()`);
            await G.wait(`window.LpRoomsUI&&!!LpRoomsUI.room()`, 15000);
            ok('U13', /^\d{4}$/.test(pin || ''), 'PIN room: code-only joiner gets 4-cell PIN sheet, wrong → red cells, right → joined', { pin });
        } finally { await closeAll(E, [H, G]); }
    }

    /* ── U14 승인 입장 · 리액션 · U15 방장 넘기기(명단 행 → 👑 → 자체 확인창) ── */
    if (run1(only, 'U14') || run1(only, 'U15')) {
        const H = await dev(E, 'u14h', { lang: 'en' }), G = await dev(E, 'u14g', { lang: 'en' });
        try {
            await hostRoom(H); const c = await createNow(H);
            await H.click('.lpr-lobby .lpr-tools .lpr-btn:last-child');            /* ⋯ → 방 시트 */
            await H.wait(`!!document.querySelector('.lpr-sheet')`, 3000);
            await H.clickText('.lpr-sheet .lpr-btn', 'Approve');
            await H.wait(`LpRoomsUI.room().state().appr===true`, 3000);
            await H.ev(`document.querySelectorAll('.lpr-bd').forEach(b=>b.remove())`);
            await G.c.send('Page.navigate', { url: c.url });
            await H.wait(`!!document.querySelector('.lpr-lobby .lpr-ask')`, 15000);
            const gMsg = await G.ev(`[...document.querySelectorAll('.lpr-card .tt,.lpr-msg')].map(e=>e.textContent).join('|')`);
            await H.click('.lpr-lobby .lpr-ask .lpr-btn.ok');
            await G.wait(`window.LpRoomsUI&&!!LpRoomsUI.room()&&!!document.querySelector('.lpr-lobby')`, 10000);
            ok('U14', /Waiting for host/.test(gMsg), 'approval mode: guest sees "waiting for host OK", host ✋ row → ✓ → guest in', gMsg);
            await G.ev(`LpRoomsUI.room().react(3)`);
            await H.wait(`!!document.querySelector('.lpr-float')`, 4000);
            ok('U14b', true, 'reaction 🔥 floats on the other device (lobby)', 'ok');
            if (run1(only, 'U15')) {
                await H.click('.lpr-lobby .lpr-m.tap');
                await H.wait(`!!document.querySelector('.lpr-sheet')`, 3000);
                await H.clickText('.lpr-sheet .lpr-btn', 'Make host');
                await H.wait(`[...document.querySelectorAll('.lpr-sheet .lpr-sh-t')].some(e=>/Make host/.test(e.textContent))`, 3000);
                await H.click('.lpr-sheet .lpr-btn.pri');
                await G.wait(`LpRoomsUI.room().isHost`, 12000);
                await sleep(800);
                const v = { h: await H.ev(`LpRoomsUI.room()?LpRoomsUI.room().isHost:'none'`), gStart: await G.ev(`!!document.querySelector('.lpr-lobby .lpr-ft .lpr-btn.go')`), toast: await G.ev(`(document.querySelector('.lpr-toast')||{}).textContent||''`) };
                ok('U15', v.h === false && v.gStart, 'host → member sheet → 👑 Make host → in-page confirm → guest becomes host (start button moves)', v);
            }
        } finally { await closeAll(E, [H, G]); }
    }

    /* ── U10: 스크린샷 시트 (360×740 · 412×915 · 1280×800 × ko/en/ja) + 배치 검사 ── */
    if (run1(only, 'U10') && !process.env.MP_NOSHOTS) {
        const VPS = [[360, 740], [412, 915], [1280, 800]], LS = ['ko', 'en', 'ja'];
        const NAMES = { ko: ['준호', '민지', 'Alex'], en: ['Jun', 'Mina', 'Alex'], ja: ['ハル', 'ユイ', 'Alex'] };
        const sheets = [];
        for (const [w, h] of VPS) {
            const files = [];
            for (const L of LS) {
                const tag = w + 'x' + h + '_' + L;
                const H = await dev(E, 'sh', { lang: L, w, h, nick: NAMES[L][0] }), G = await dev(E, 'sg', { lang: L, w, h, nick: '' }), W = await dev(E, 'sw', { lang: L, w, h, nick: NAMES[L][2] });
                const shot = async (P, n) => { const f = path.join(SHOTS, tag + '_' + n + '.png'); await sleep(250); await P.shot(f); files.push(f); const b = await P.ev(LAYOUT); if (b.length) layoutBad.push(tag + ' ' + n + ': ' + b.join(',')); };
                try {
                    await hostRoom(H);
                    await shot(H, '1-create');
                    const c = await createNow(H);
                    await G.nav(c.url, `!!document.querySelector('.lpr-sheet .lpr-prof input')`, 20000);
                    await G.ev(`(()=>{const i=document.querySelector('.lpr-sheet .lpr-prof input');i.value=${J(NAMES[L][1])};i.dispatchEvent(new Event('input'))})()`);
                    await shot(G, '2-join');
                    await G.click('.lpr-sheet .lpr-btn.go');
                    await G.wait(`!!(LpRoomsUI.room())&&!!document.querySelector('.lpr-lobby')`, 15000);
                    await guestJoin(W, c.url);
                    await W.ev(`LpRoomsUI.room().intent('role','watch')`);
                    await G.ev(`LpRoomsUI.room().intent('pick',{key:'char',val:'b'})`);
                    await H.ev(`LpRoomsUI.room().intent('pick',{key:'char',val:'a'})`);
                    await H.wait(`LpRoomsUI.room().roster().length===3`, 8000);
                    await sleep(500);
                    await shot(G, '3-lobby-guest');
                    await G.ev(`LpRoomsUI.room().intent('ready',true)`);
                    await H.wait(`LpRoomsUI.room().canStart()`, 6000); await sleep(300);
                    await shot(H, '4-lobby-host');
                    if (L === 'ko' && w === 360) { await H.ev(`LpRoomsUI.openInvite()`); await sleep(500); await shot(H, '4b-invite'); await H.ev(`document.querySelectorAll('.lpr-bd').forEach(b=>b.remove())`); }
                    await H.click('.lpr-ft .lpr-btn.go');
                    await Promise.all([H, G].map(P => P.wait(`LpRoomsUI.room().state().phase==='playing'`, 6000)));
                    await sleep(500);
                    await shot(G, '5-hud');
                    if (L === 'ko' && w === 360) { await G.ev(`LpRoomsUI.room().emit('hostlost',{level:2})`); await sleep(200); await shot(G, '5b-hostlost'); await G.ev(`LpRoomsUI.room().emit('hostback')`); }
                    await H.click('.lpr-hud');
                    await H.wait(`!!document.querySelector('.lpr-sheet')`, 3000);
                    await shot(H, '6-room-sheet');
                    await H.ev(`document.querySelectorAll('.lpr-bd').forEach(b=>b.remove())`);
                    await H.ev(`LpRoomsUI.room().toLobby()`); await sleep(300);
                    await H.ev(`LpRoomsUI.room().switchGame('roulette')`);
                    await G.wait(`location.pathname==='/games/roulette/'&&window.LpRoomsUI&&LpRoomsUI.room&&!!LpRoomsUI.room()&&!!document.querySelector('.lpr-strip')`, 20000);
                    await G.ev(`LpRoomsUI.badge(document.getElementById('badgeHost').appendChild(document.createElement('span')),{kind:'verified',n:3})`);
                    await sleep(400);
                    await shot(G, '7-strip');
                    await W.nav('/lobby/', `!!document.querySelector('#lprHub .lpr-hubt')`, 12000);
                    await W.ev(`document.querySelector('#lprHub .lpr-btn.go').click()`);
                    await sleep(700);
                    await shot(W, '8-hub');
                } catch (e) {
                    layoutBad.push(tag + ' CRASH ' + String(e.message).slice(0, 200));
                } finally { await closeAll(E, [H, G, W]); }
            }
            const out = path.join(SHOTS, `sheet_${w}x${h}.png`);
            await sheetPng(E, files, out, w > 800 ? 4 : 8, `LuckyPlz Rooms v2 UI — ${w}×${h} · rows ko/en/ja`);
            sheets.push(out);
        }
        ok('U10', !layoutBad.length, 'screenshots 3 viewports × ko/en/ja: our buttons in view, ≥44px, no overlap, no h-scroll (sheets for human review)', layoutBad.length ? layoutBad.slice(0, 12) : sheets.join(' · '));
    } else if (layoutBad.length) ok('U10', false, 'layout check', layoutBad);
}
