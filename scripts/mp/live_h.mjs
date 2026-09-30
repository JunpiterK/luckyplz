/* 실전(LIVE) 하네스 도우미 — 실제 Supabase Realtime + 실제 게임 페이지 (릴레이 심 없음)
   · 정적 서버: python server.py (PORT=LIVE_PORT 기본 8601, HOST=127.0.0.1) — 운영(Cloudflare Pages) 라우팅과 같은 경로(/r/CODE, /games/<id>/)
   · 기기: 헤드리스 Edge 1개 + 브라우저 컨텍스트 N개(h.mjs Edge{live:true}) — REST·Auth·Storage·Functions·GA 차단, Realtime 웹소켓만 허용
   · 계수: 문서 앞에 심는 WebSocket 래퍼가 lpr-* 토픽의 방송 프레임(발신 1 + 수신 1)을 센다 = Supabase 과금 공식
   · 방 코드: 테스트 키(LpRooms.config({testKeys}) — 로컬 개발 도메인 전용)로 'ZZ' 로 시작하는 코드만 만든다. 방은 시나리오 끝에 닫는다 */
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadFair } from './fairlib.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, '..', '..');
export const J = JSON.stringify;
export const sleep = (ms) => new Promise(r => setTimeout(r, ms));

/* ── 정적 서버 (server.py) ── */
export async function startServer(port) {
    const env = Object.assign({}, process.env, { PORT: String(port), HOST: '127.0.0.1', PYTHONIOENCODING: 'utf-8' });
    const proc = spawn('python', ['server.py'], { cwd: ROOT, env, stdio: 'ignore', windowsHide: true });
    const base = 'http://127.0.0.1:' + port;
    for (let i = 0; i < 100; i++) {
        await sleep(200);
        try { const r = await fetch(base + '/build.json'); if (r.ok) return { base, proc, stop() { try { execFileSync('taskkill', ['/PID', String(proc.pid), '/T', '/F'], { stdio: 'ignore' }); } catch (_) {} } }; } catch (_) {}
    }
    try { execFileSync('taskkill', ['/PID', String(proc.pid), '/T', '/F'], { stdio: 'ignore' }); } catch (_) {}
    throw new Error('server.py did not start on ' + port);
}

/* ── 'ZZ' 코드가 나오는 방 키(테스트 방 식별용) ── */
export async function zzKeys(prefix = 'ZZ') {
    const F = loadFair(), t = F._t, S = crypto.subtle;
    for (let tries = 1; ; tries++) {
        const s = await S.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
        const d = await S.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits', 'deriveKey']);
        const rpk = { sig: t.b64u(new Uint8Array(await S.exportKey('raw', s.publicKey))), dh: t.b64u(new Uint8Array(await S.exportKey('raw', d.publicKey))) };
        const code = t.codeOfF(t.roomF(rpk));
        if (code.startsWith(prefix) && /[A-Z]/.test(code.slice(2))) return { keys: { sig: await S.exportKey('jwk', s.privateKey), dh: await S.exportKey('jwk', d.privateKey) }, code, tries };
    }
}

/* ── 문서 앞 스크립트: 웹소켓 프레임 계수 + 방 상태 시각 기록 ── */
const PRE = `(function(){
  if(window.__ws)return;
  var M=window.__ws={tx:0,rx:0,by:{},other:{},t0:Date.now(),marks:[]};
  var W=window.WebSocket;
  function text(d){if(typeof d==='string')return d;try{return new TextDecoder().decode(d instanceof ArrayBuffer?new Uint8Array(d):d)}catch(e){return ''}}
  function note(dir,d){
    var bin=typeof d!=='string',s=text(d);
    var isB=bin?(s.indexOf('realtime:')>=0):(s.indexOf('"broadcast"')>=0&&s.indexOf('"phx_')<0);
    if(!isB)return;
    var tm=/realtime:([A-Za-z0-9_-]+)/.exec(s),topic=tm?tm[1]:'?';
    if(topic.indexOf('lpr-')!==0){M.other[topic]=(M.other[topic]||0)+1;return}
    var em=/"e":"([a-z_]+)"/.exec(s),e=em?em[1]:'?';
    var hg=/"ep":\\d/.test(s)?'h':'g';
    var k=dir+' '+hg+':'+e;M.by[k]=(M.by[k]||0)+1;M[dir]++;
  }
  function WS(u,p){
    var ws=p===undefined?new W(u):new W(u,p);
    try{
      var send=ws.send;ws.send=function(d){try{note('tx',d)}catch(e){}return send.apply(ws,arguments)};
      ws.addEventListener('message',function(ev){try{note('rx',ev.data)}catch(e){}});
    }catch(e){}
    return ws;
  }
  WS.prototype=W.prototype;WS.CONNECTING=0;WS.OPEN=1;WS.CLOSING=2;WS.CLOSED=3;
  window.WebSocket=WS;
  window.__wsReset=function(){M.tx=0;M.rx=0;M.by={};M.t0=Date.now()};
  /* LpRooms 상태 시각(probing→joining→member) — 참가 지연 측정 */
  window.__st=[];
  var iv=setInterval(function(){if(window.LpRooms&&LpRooms.on&&!window.__stOn){window.__stOn=1;clearInterval(iv);LpRooms.on('status',function(s){window.__st.push([Date.now(),s.st])});LpRooms.on('room',function(r){window.__st.push([Date.now(),'room'])})}},15);
  window.__vis=function(h){try{Object.defineProperty(document,'visibilityState',{configurable:true,get:function(){return h?'hidden':'visible'}});Object.defineProperty(document,'hidden',{configurable:true,get:function(){return !!h}})}catch(e){}document.dispatchEvent(new Event('visibilitychange',{bubbles:true}))};
})();`;

/* 기기 1대 = 컨텍스트 1개 */
export async function dev(E, label, o = {}) {
    const kv = Object.assign({ luckyplz_lang: o.lang || 'ko', lp_profile: J({ nick: o.nick || label, av: (label.charCodeAt(label.length - 1) % 16), v: 1 }), luckyplz_nick: o.nick || label }, o.ls || {});
    if (o.noNick) { delete kv.lp_profile; delete kv.luckyplz_nick; }
    const pre = PRE + `try{if(!sessionStorage.getItem('__pv')){var o=${J(kv)};for(var k in o){localStorage.setItem(k,o[k])}sessionStorage.setItem('__pv','1')}}catch(e){}` + (o.pre || '');
    const P = await E.page({ label, pre, ctx: o.ctx });
    const c = P.c;
    await c.send('Network.setBlockedURLs', { urls: ['*supabase.co/rest/*', '*supabase.co/auth/*', '*supabase.co/storage/*', '*supabase.co/functions/*', '*googletagmanager.com*', '*google-analytics.com*', '*doubleclick*', '*pagead2*', '*googlesyndication*', '*fonts.googleapis.com*', '*fonts.gstatic.com*', '*cdn.jsdelivr.net*', '*api.drand.sh*', '*drand.cloudflare.com*'] });
    await c.send('Emulation.setDeviceMetricsOverride', { width: o.w || 412, height: o.h || 915, deviceScaleFactor: 1, mobile: (o.w || 412) < 800 });
    P.nav = async (u, cond, ms) => {
        P.t0 = Date.now();
        await c.send('Page.navigate', { url: /^(https?:|about:|file:)/.test(u) ? u : E.base + u });
        await sleep(150);
        await P.wait(cond || `document.readyState==='complete'`, ms || 25000);
        return Date.now() - P.t0;
    };
    P.shot = async (file) => { const r = await c.send('Page.captureScreenshot', { format: 'png' }); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, Buffer.from(r.data, 'base64')); return file; };
    P.click = (sel, txt) => P.ev(`(()=>{const e=[...document.querySelectorAll(${J(sel)})].find(x=>!${J(txt || '')}||x.textContent.includes(${J(txt || '')}));if(!e)return false;e.click();return true})()`);
    P.clickWhen = async (sel, txt, ms) => { await P.wait(`!![...document.querySelectorAll(${J(sel)})].find(x=>(!${J(txt || '')}||x.textContent.includes(${J(txt || '')}))&&x.getBoundingClientRect().width>0)`, ms || 8000); return P.click(sel, txt); };
    P.ws = () => P.ev(`(()=>{var M=window.__ws||{};return {tx:M.tx|0,rx:M.rx|0,by:M.by||{},other:M.other||{},ms:Date.now()-(M.t0||Date.now())}})()`);
    P.wsReset = () => P.ev(`window.__wsReset&&window.__wsReset()`);
    /* 참가 지연: probing → member (핸드셰이크만) */
    P.joinLat = () => P.ev(`(()=>{var a=window.__st||[],p=a.filter(x=>x[1]==='probing').pop(),m=a.filter(x=>x[1]==='member').pop(),j=a.filter(x=>x[1]==='joining').pop();return p&&m?{probeToMember:m[0]-p[0],probeToHello:j?j[0]-p[0]:null}:null})()`);
    return P;
}
export async function closeAll(E, pages) { for (const p of pages) { if (!p) continue; try { await p.close(); } catch (_) {} try { await E.disposeContext(p.ctx); } catch (_) {} const i = E.pages.indexOf(p); if (i >= 0) E.pages.splice(i, 1); } }

/* 방 전체 과금 계수: 모든 기기의 (발신 + 수신) 방송 프레임 합 */
export async function bill(pages) {
    const ws = await Promise.all(pages.map(p => p.ws().catch(() => ({ tx: 0, rx: 0, by: {}, other: {}, ms: 0 }))));
    const by = {}; let tx = 0, rx = 0, other = {};
    ws.forEach(w => { tx += w.tx; rx += w.rx; for (const k in w.by) by[k] = (by[k] || 0) + w.by[k]; for (const k in w.other) other[k] = (other[k] || 0) + w.other[k]; });
    const ms = Math.max(...ws.map(w => w.ms), 1);
    /* 종류별: 발신 수(tx) 기준으로 묶는다 */
    const sent = {}; Object.keys(by).forEach(k => { if (k.startsWith('tx ')) sent[k.slice(3)] = by[k]; });
    return { bill: tx + rx, tx, rx, ms, perSec: +((tx + rx) / (ms / 1000)).toFixed(2), sent, other };
}
export async function billReset(pages) { await Promise.all(pages.map(p => p.wsReset().catch(() => 0))); }
export async function eqAll(pages, expr, ms = 15000) {
    const t0 = Date.now(); let vals;
    while (Date.now() - t0 < ms) {
        vals = await Promise.all(pages.map(p => p.ev(expr).catch(e => 'ERR ' + e.message.slice(0, 120))));
        if (vals.every(v => v === vals[0] && v !== null && v !== undefined && v !== '' && v !== false && !String(v).startsWith('ERR'))) return { ok: true, v: vals[0] };
        await sleep(200);
    }
    return { ok: false, vals };
}

/* 스크린샷 여러 장 → 시트 한 장(방장 | 게스트 나란히) */
export async function sheet(E, files, out, title) {
    const P = await E.page({ label: 'sheet' });
    try {
        const imgs = files.filter(f => f && fs.existsSync(f)).map(f => ({ n: path.basename(f, '.png'), d: 'data:image/png;base64,' + fs.readFileSync(f).toString('base64') }));
        const html = `<html><body style="margin:0;background:#1b1b22;color:#eee;font:14px system-ui"><div style="padding:8px 10px;font-weight:700">${title}</div><div style="display:grid;grid-template-columns:repeat(${imgs.length},1fr);gap:8px;padding:8px">${imgs.map(i => `<figure style="margin:0"><img src="${i.d}" style="width:100%;display:block;border:1px solid #555"><figcaption style="padding:4px 2px">${i.n}</figcaption></figure>`).join('')}</div></body></html>`;
        const tmp = path.join(path.dirname(out), '_sheet.html'); fs.writeFileSync(tmp, html);
        const W = Math.min(1800, 430 * imgs.length);
        await P.c.send('Emulation.setDeviceMetricsOverride', { width: W, height: 900, deviceScaleFactor: 1, mobile: false });
        await P.c.send('Page.navigate', { url: 'file:///' + tmp.replace(/\\/g, '/') });
        await sleep(900);
        const h = await P.ev('document.documentElement.scrollHeight');
        await P.c.send('Emulation.setDeviceMetricsOverride', { width: W, height: Math.min(h, 4000), deviceScaleFactor: 1, mobile: false });
        await sleep(300);
        const r = await P.c.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
        fs.writeFileSync(out, Buffer.from(r.data, 'base64'));
        fs.unlinkSync(tmp);
        files.forEach(f => { try { fs.unlinkSync(f); } catch (_) {} });
    } finally { await closeAll(E, [P]); }
    return out;
}
