/* P4 턴제 하네스 도우미 — 실제 게임 페이지(/games/<id>/index.html)를 띄운다.
   relay.mjs 는 확장자 없는 문서 경로에 하네스 페이지(page.html)를 주므로 게임은 index.html 경로로 연다.
   (CDP Fetch 로 문서를 대신 채우면 그 문서의 WebSocket 이 1006 으로 막혀서 — 실측 — 쓰지 않는다.
    MP_FETCH=1 이면 예전 방식으로 가로챈다.)
   페이지마다 닉네임·언어를 심고, setInterval·리스너 계수기(누수 검사 T11)를 문서 앞에 심는다. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const J = JSON.stringify;
export const sleep = (ms) => new Promise(r => setTimeout(r, ms));

/* 문서 앞에 심는 계수기 — 활성 interval 집합 · window/document 리스너 수 */
const COUNTERS = `(function(){try{
  var si=window.setInterval,ci=window.clearInterval,A=new Set();window.__iv=A;
  window.setInterval=function(f,t){var id=si.apply(window,arguments);A.add(id);return id};
  window.clearInterval=function(id){A.delete(id);return ci.call(window,id)};
  var add=EventTarget.prototype.addEventListener,rm=EventTarget.prototype.removeEventListener,L={n:0};window.__ls=L;
  var key=function(t){return t===window?'w':t===document?'d':null};
  var seen=new WeakMap();
  EventTarget.prototype.addEventListener=function(ty,fn,o){var k=key(this);if(k&&fn){var m=seen.get(fn)||{};var kk=k+ty+(o&&o.capture||o===true?'c':'');if(!m[kk]){m[kk]=1;seen.set(fn,m);L.n++}}return add.apply(this,arguments)};
  EventTarget.prototype.removeEventListener=function(ty,fn,o){var k=key(this);if(k&&fn){var m=seen.get(fn);var kk=k+ty+(o&&o.capture||o===true?'c':'');if(m&&m[kk]){delete m[kk];L.n--}}return rm.apply(this,arguments)};
}catch(e){}})();`;

export async function gamePage(E, label, o = {}) {
    const nick = o.nick || label;
    const pre = `try{localStorage.setItem('lp_profile',${J(J({ nick, av: o.av || 0, v: 1 }))});localStorage.setItem('luckyplz_nick',${J(nick)});` +
        `localStorage.setItem('luckyplz_lang',${J(o.lang || 'ko')});${process.env.MP_DEBUG ? "localStorage.setItem('lpDebug','1');" : ''}}catch(e){}` + COUNTERS + (o.pre || '');
    const P = await E.page({ label, pre, noResume: true, ctx: o.ctx });
    if (process.env.MP_FETCH) await P.c.send('Fetch.enable', { patterns: [{ urlPattern: '*/games/*', resourceType: 'Document', requestStage: 'Request' }] });
    P.c.handlers.push(d => {
        if (d.method !== 'Fetch.requestPaused') return;
        const u = new URL(d.params.request.url);
        const m = /^\/games\/([a-z0-9-]+)\/(index\.html)?$/.exec(u.pathname);
        const f = m && path.join(ROOT, 'public', 'games', m[1], 'index.html');
        if (f && fs.existsSync(f)) {
            const body = fs.readFileSync(f).toString('base64');
            P.c.send('Fetch.fulfillRequest', { requestId: d.params.requestId, responseCode: 200, responseHeaders: [{ name: 'Content-Type', value: 'text/html; charset=utf-8' }, { name: 'Cache-Control', value: 'no-store' }], body }).catch(() => {});
        } else P.c.send('Fetch.continueRequest', { requestId: d.params.requestId }).catch(() => {});
    });
    P.nav = async (url) => {
        await P.c.send('Page.navigate', { url: url.startsWith('http') ? url : E.base + url });
        await sleep(250);
        await P.wait('document.readyState==="complete"', 25000);
    };
    P.reload2 = async () => { await P.c.send('Page.reload', { ignoreCache: true }); await sleep(300); await P.wait('document.readyState==="complete"', 25000); };
    /* 백그라운드 흉내: 숨김 이벤트 → (얼림) → 복귀. 헤드리스엔 진짜 탭 숨김이 없어 visibilityState 를 덮어쓴다 */
    P.hide = async (freeze) => {
        await P.ev(`(function(){try{Object.defineProperty(document,'visibilityState',{configurable:true,get:function(){return 'hidden'}});Object.defineProperty(document,'hidden',{configurable:true,get:function(){return true}});document.dispatchEvent(new Event('visibilitychange'))}catch(e){}return 1})()`);
        await sleep(150);
        if (freeze) await P.c.send('Page.setWebLifecycleState', { state: 'frozen' });
    };
    P.show = async () => {
        try { await P.c.send('Page.setWebLifecycleState', { state: 'active' }); } catch (_) {}
        await sleep(100);
        await P.ev(`(function(){try{Object.defineProperty(document,'visibilityState',{configurable:true,get:function(){return 'visible'}});Object.defineProperty(document,'hidden',{configurable:true,get:function(){return false}});document.dispatchEvent(new Event('visibilitychange'))}catch(e){}return 1})()`);
    };
    /* 스크린샷 — MP_SHOTS 폴더(없으면 건너뜀) */
    P.shot = async (name) => {
        const dir = process.env.MP_SHOTS; if (!dir) return null;
        try { fs.mkdirSync(dir, { recursive: true }); const r = await P.c.send('Page.captureScreenshot', { format: 'png' }); const f = path.join(dir, name + '.png'); fs.writeFileSync(f, Buffer.from(r.data, 'base64')); return f; } catch (e) { return null; }
    };
    return P;
}
export async function closePages(E, pages) { for (const p of pages) { try { await p.close(); } catch (_) {} try { await E.disposeContext(p.ctx); } catch (_) {} } }
/* 초대 링크(/games/<id>/?r=CODE#k=…)를 그대로 쓴다 — 문서 요청을 가로채므로 경로 형식이 운영과 같다 */
export function inviteToLocal(url, base) { const u = new URL(url); return base + u.pathname.replace(/\/$/, '/index.html') + u.search + u.hash; }
export async function eqAll(pages, expr, ms = 12000) {
    const t0 = Date.now(); let vals;
    while (Date.now() - t0 < ms) { vals = await Promise.all(pages.map(p => p.ev(expr).catch(e => 'ERR ' + e.message))); if (vals.every(v => v === vals[0] && v != null && v !== '' && v !== false && !String(v).startsWith('ERR'))) return { ok: true, v: vals[0] }; await sleep(200); }
    return { ok: false, vals };
}
