/* 헤드리스 Edge 하네스 — 브라우저 1개 + 컨텍스트 N개 = 기기 N대(저장소·IndexedDB·Web Lock 분리)
   --headless=old --edge-skip-compat-layer-relaunch. 외부 쓰기 차단(supabase.co REST/Auth/Realtime, GA).
   종료 시 브라우저 프로세스 트리 종료 + 프로필 삭제(디스크 정리 규칙). */
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';

export const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const EDGE = ['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Microsoft/Edge/Application/msedge.exe'].find(p => fs.existsSync(p));
export const SCR = process.env.MP_SCRATCH || path.join(os.tmpdir(), 'lp-mp');
const BLOCK = ['*supabase.co*', '*googletagmanager.com*', '*google-analytics.com*', '*doubleclick*', '*pagead2*', '*googlesyndication*'];
function killTree(pid) { try { execFileSync('taskkill', ['/PID', String(pid), '/T', '/F'], { stdio: 'ignore' }); } catch (_) {} }
function freePort() { return new Promise((res, rej) => { const s = net.createServer(); s.unref(); s.on('error', rej); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); }); }

export class Edge {
    constructor(base, opt = {}) { this.base = base; this.pages = []; this.prof = path.join(SCR, 'prof_mp_' + process.pid + '_' + Date.now()); this.live = !!opt.live; }
    async start() {
        fs.mkdirSync(SCR, { recursive: true });
        this.dport = await freePort();
        this.proc = spawn(EDGE, ['--headless=old', '--edge-skip-compat-layer-relaunch', '--remote-debugging-port=' + this.dport, '--remote-allow-origins=*',
            '--user-data-dir=' + this.prof, '--no-first-run', '--no-default-browser-check', '--disable-extensions', '--mute-audio',
            '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows',
            '--disable-features=Translate,msEdgeSidebarV2', '--window-size=412,915', 'about:blank'], { stdio: 'ignore', windowsHide: true });
        let ver = null;
        for (let i = 0; i < 150 && !ver; i++) { await sleep(200); try { ver = await (await fetch('http://127.0.0.1:' + this.dport + '/json/version')).json(); } catch (_) {} }
        if (!ver) throw new Error('edge did not start');
        this.bws = await this._ws(ver.webSocketDebuggerUrl);
    }
    async _ws(url) {
        const ws = new WebSocket(url); await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
        const o = { ws, id: 0, pend: new Map(), handlers: [] };
        ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && o.pend.has(d.id)) { const p = o.pend.get(d.id); o.pend.delete(d.id); d.error ? p.rej(new Error(JSON.stringify(d.error))) : p.res(d.result); } else o.handlers.forEach(h => h(d)); };
        o.send = (method, params = {}) => new Promise((res, rej) => {
            const i = ++o.id; const to = setTimeout(() => { if (o.pend.has(i)) { o.pend.delete(i); rej(new Error('CDP timeout ' + method)); } }, 60000);
            o.pend.set(i, { res: v => { clearTimeout(to); res(v); }, rej: e => { clearTimeout(to); rej(e); } }); ws.send(JSON.stringify({ id: i, method, params }));
        });
        return o;
    }
    async newContext() { return (await this.bws.send('Target.createBrowserContext', { disposeOnDetach: false })).browserContextId; }
    /* 새 탭. opts: {label, ctx(같은 기기 두 번째 탭), pre(문서 전 스크립트), adapter, noResume, noNav} */
    async page(opts = {}) {
        const label = opts.label || ('p' + this.pages.length);
        const ctx = opts.ctx || await this.newContext();
        const { targetId } = await this.bws.send('Target.createTarget', { url: 'about:blank', browserContextId: ctx });
        const c = await this._ws('ws://127.0.0.1:' + this.dport + '/devtools/page/' + targetId);
        const P = { label, c, targetId, ctx, log: [], exc: [] };
        c.handlers.push(d => {
            if (d.method === 'Runtime.exceptionThrown') { const ed = d.params.exceptionDetails; P.exc.push(((ed.exception && ed.exception.description) || ed.text || '').split('\n').slice(0, 3).join(' | ')); }
            else if (d.method === 'Runtime.consoleAPICalled') { const s = d.params.args.map(a => a.value !== undefined ? String(a.value) : (a.description || '')).join(' '); P.log.push(d.params.type + ': ' + s); if (P.log.length > 600) P.log.shift(); }
            else if (d.method === 'Page.javascriptDialogOpening') { P.log.push('DIALOG ' + d.params.message); c.send('Page.handleJavaScriptDialog', { accept: true }).catch(() => {}); }
        });
        await c.send('Page.enable'); await c.send('Runtime.enable'); await c.send('Network.enable');
        if (!this.live) await c.send('Network.setBlockedURLs', { urls: BLOCK });
        else await c.send('Network.setBlockedURLs', { urls: ['*supabase.co/rest/*', '*supabase.co/auth/*', '*supabase.co/storage/*', '*supabase.co/functions/*', '*google*', '*doubleclick*'] });
        await c.send('Emulation.setDeviceMetricsOverride', { width: 412, height: 915, deviceScaleFactor: 1, mobile: true });
        const pre = `window.__mpLabel=${JSON.stringify(label)};try{sessionStorage.setItem('__mpLabel',${JSON.stringify(label)})}catch(e){}` +
            (opts.adapter ? `window.__mpAdapter=${JSON.stringify(opts.adapter)};` : '') + (opts.noResume ? 'window.__mpNoResume=1;' : '') + (opts.noNav ? 'window.__mpNoNav=1;' : '') + (opts.pre || '');
        await c.send('Page.addScriptToEvaluateOnNewDocument', { source: pre });
        P.ev = async (expr, timeout) => {
            const r = await c.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true, timeout: timeout || 45000 });
            if (r.exceptionDetails) throw new Error(label + ': ' + String(r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text).slice(0, 700));
            return r.result.value;
        };
        P.go = async (p) => { await c.send('Page.navigate', { url: p.startsWith('http') ? p : this.base + p }); return P.waitReady(); };
        P.waitReady = async () => { await sleep(200); for (let i = 0; i < 120; i++) { await sleep(100); try { if (await P.ev('document.readyState==="complete"&&!!window.T&&T.resumed!==null')) return true; } catch (_) {} } return false; };
        P.reload = async () => { await c.send('Page.reload', { ignoreCache: true }); return P.waitReady(); };
        P.wait = async (expr, ms = 15000, step = 100) => { const t0 = Date.now(); let last; while (Date.now() - t0 < ms) { try { last = await P.ev(expr); if (last) return last; } catch (e) { last = e.message; } await sleep(step); } throw new Error(label + ' wait timeout: ' + expr + ' last=' + JSON.stringify(last)); };
        P.close = async () => { try { c.ws.close(); } catch (_) {} try { await this.bws.send('Target.closeTarget', { targetId }); } catch (_) {} };
        this.pages.push(P);
        return P;
    }
    async disposeContext(ctx) { try { await this.bws.send('Target.disposeBrowserContext', { browserContextId: ctx }); } catch (_) {} }
    async stop() {
        for (const p of this.pages) { try { p.c.ws.close(); } catch (_) {} }
        try { await this.bws.send('Browser.close'); } catch (_) {}
        try { this.bws.ws.close(); } catch (_) {}
        await sleep(500);
        if (this.proc) killTree(this.proc.pid);
        await sleep(500);
        try { fs.rmSync(this.prof, { recursive: true, force: true }); } catch (_) {}
    }
}

/* 결과 표 */
export const R = { rows: [] };
export function ok(id, cond, name, info) {
    const row = { id, pass: !!cond, name, info: info === undefined ? '' : (typeof info === 'string' ? info : JSON.stringify(info)) };
    R.rows.push(row);
    console.log((cond ? 'PASS ' : 'FAIL ') + id + ' ' + name + (row.info ? ' → ' + row.info.slice(0, 400) : ''));
    return !!cond;
}
