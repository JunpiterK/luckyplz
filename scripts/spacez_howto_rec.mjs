#!/usr/bin/env node
/* =====================================================================
   Space-Z 「게임방법」 팝업 영상 녹화기 (2026-10-08, fx-szhow3)
   public/assets/dodge/howto/{sat,beam,fever,items}.mp4 + 포스터 .webp 를 실제 게임에서 찍는다.

   방식: 헤드리스 Edge(CDP) + 가상 시계 + 녹화 전용 주입. 주입 코드는 페이지 파일에 넣지 않는다(Runtime.evaluate 로만).
     · 가상 시계 — performance.now·requestAnimationFrame·setTimeout/setInterval 을 가로채 VT 로 돌린다.
       한 프레임 = 16.67ms 두 번(60Hz 시뮬) → 스크린샷 1장(30fps 영상). CSS 애니메이션·전환도 VT 에 맞춰 멈췄다 놓는다
     · 입력 — 진짜 터치(Input.dispatchTouchEvent, 멀티터치). 조향은 빈 곳 상대 드래그(게임의 손가락 고리 그대로),
       BEAM·SAT·슬롯은 그 버튼을 손가락으로 누른다. 화면에 손가락 점(녹화 전용 DOM)을 그린다
     · 녹화 전용 주입 — 존 이동(startedAt 당기기)·피버 게이지·보급 캡슐/아이템 슬롯 채우기·운석 회피 보정(멀리서 궤도를 살짝 비킴)
       ·보급 영구 차단 경고(첫 판 면제 우회). 화면 전체 흔들림은 만들지 않는다(게임에도 없다)
   결과: H.264 Main yuv420p 432×930 30fps faststart(소리 없음) + 포스터 webp. 프레임 시트(검수용)는 --review 폴더에.

   사용:
     node scripts/spacez_howto_rec.mjs [sat beam items | verify | probe | touchtest] --root <체크아웃> [옵션]
       sat·beam·items — 녹화 → mp4·webp 를 --out 에, 프레임 시트·로그를 --review 에 (피격이 영상에 남으면 3번까지 다시)
       verify  — 팝업을 412×915·360×740 × ko·en 으로 열어 4장 모두 재생되는지·콘솔 에러 0 인지 (스크린샷은 --review)
       probe   — --probe-zone 존으로 이동해 몇 장 찍기 · touchtest — CDP 멀티터치 떼기 동작 확인
       fever.mp4 는 2026-10-07 녹화 그대로(녹화기 없음 — 필요하면 clipFever 를 더한다)
   옵션:
     --port <n>       정적 서버 포트 (기본 9421 — 8611–8810·50000–50059 는 Windows 예약이라 피한다)
     --out <dir>      mp4·webp 저장 폴더 (기본 <root>/public/assets/dodge/howto)
     --tmp <dir>      프레임 임시 폴더 (기본 OS temp/szhow_rec) — 끝나면 지운다(--keep 이면 남김)
     --review <dir>   프레임 시트 저장 폴더 (기본 OS temp/szhow3_review)
     --crf <n>        x264 CRF (기본 장마다 다름)
     --lang <l>       게임 언어 (기본 en — 이전 녹화와 같게)
     --edge <exe>     msedge.exe 경로
     --probe-zone <z> probe: 이 존으로 이동해 몇 장 찍기
   종료 시 항상 Edge(프로세스 트리)·서버 종료, 프로필·임시 폴더 삭제.
   ===================================================================== */
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import http from 'node:http';

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
const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const ROOT = path.resolve(A.root || path.join(HERE, '..'));
const PUB = path.join(ROOT, 'public');
const PORT = +(A.port || 9421);
const OUTDIR = path.resolve(A.out || path.join(PUB, 'assets', 'dodge', 'howto'));
const TMP = path.resolve(A.tmp || path.join(os.tmpdir(), 'szhow_rec'));
const REVIEW = path.resolve(A.review || path.join(os.tmpdir(), 'szhow3_review'));
const LANG = String(A.lang || 'en');
const FFMPEG = A.ffmpeg || (fs.existsSync('C:/ffmpeg/bin/ffmpeg.exe') ? 'C:/ffmpeg/bin/ffmpeg.exe' : 'ffmpeg');
const EDGE = A.edge || ['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Microsoft/Edge/Application/msedge.exe'].find(p => fs.existsSync(p));
const VW = 432, VH = 930, DSF = 2;      /* 영상 = 사이트 상단 바(--sz-tbh) 아래 432×930 CSS px. 2배로 찍어 줄인다(가장자리 계단 없이) */
let TBH = 50;                           /* 상단 바 높이 — 부팅 때 재서 뷰포트를 930 + TBH 로 맞춘다 */
const FPS = 30, SUB = 2, STEP = 1000 / (FPS * SUB);   /* 60Hz 시뮬 · 30fps 영상 */
let CLIPS = A._.length ? A._ : ['sat', 'beam', 'fever', 'items'];

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const say = (...a) => console.log('[rec]', ...a);

/* ---------------- 정적 서버 (Pages 라우팅 흉내: 디렉토리 → index.html) ---------------- */
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png',
    '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.wav': 'audio/wav', '.mp4': 'video/mp4', '.woff2': 'font/woff2', '.ico': 'image/x-icon', '.txt': 'text/plain' };
let SERVER = null;
function startServer(){
    return new Promise((res, rej) => {
        const srv = http.createServer((req, rsp) => {
            try{
                let u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
                let f = path.join(PUB, u);
                if(!f.startsWith(PUB)){ rsp.writeHead(403); rsp.end(); return; }
                if(fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
                if(!fs.existsSync(f)){ rsp.writeHead(404); rsp.end('404'); return; }
                rsp.writeHead(200, { 'Content-Type': MIME[path.extname(f).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store' });
                fs.createReadStream(f).pipe(rsp);
            }catch(e){ rsp.writeHead(500); rsp.end(String(e)); }
        });
        srv.on('error', rej);
        srv.listen(PORT, '127.0.0.1', () => { SERVER = srv; res('http://127.0.0.1:' + PORT); });
    });
}

/* ---------------- Edge (CDP) ---------------- */
const LIVE = new Set();
function killTree(pid){ try{ execFileSync('taskkill', ['/PID', String(pid), '/T', '/F'], { stdio: 'ignore' }); }catch(_){} }
function freePort(){ return new Promise((res, rej) => { const s = net.createServer(); s.unref(); s.on('error', rej); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); }); }
class Edge {
    constructor(){ this.id = 0; this.pend = new Map(); this.exc = []; this.cerr = []; }
    async launch(){
        if(!EDGE) throw new Error('msedge.exe 를 찾지 못함 (--edge)');
        this.dport = await freePort();
        this.prof = path.join(os.tmpdir(), 'edgeprof_szhow_' + process.pid + '_' + this.dport);
        this.proc = spawn(EDGE, ['--headless=old', '--edge-skip-compat-layer-relaunch', '--remote-debugging-port=' + this.dport, '--remote-allow-origins=*', '--user-data-dir=' + this.prof,
            '--no-first-run', '--no-default-browser-check', '--disable-extensions', '--disable-sync', '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows', '--disable-features=CalculateNativeWinOcclusion,IntensiveWakeUpThrottling', '--mute-audio', '--autoplay-policy=no-user-gesture-required',
            '--hide-scrollbars', '--window-size=' + VW + ',' + (VH + TBH), 'about:blank'], { stdio: 'ignore', windowsHide: true });
        LIVE.add(this);
        let tabs = null;
        for(let i = 0; i < 120 && !tabs; i++){ await sleep(200); try{ const t = await (await fetch('http://127.0.0.1:' + this.dport + '/json')).json(); if(t.find(x => x.type === 'page')) tabs = t; }catch(_){} }
        if(!tabs) throw new Error('Edge 디버깅 포트 응답 없음');
        this.ws = new WebSocket(tabs.find(t => t.type === 'page').webSocketDebuggerUrl);
        await new Promise((res, rej) => { this.ws.onopen = res; this.ws.onerror = rej; });
        this.ws.onmessage = (m) => {
            const d = JSON.parse(m.data);
            if(d.id && this.pend.has(d.id)){ const p = this.pend.get(d.id); this.pend.delete(d.id); clearTimeout(p.t); d.error ? p.rej(new Error(JSON.stringify(d.error))) : p.res(d.result); return; }
            if(d.method === 'Runtime.exceptionThrown'){ const ed = d.params.exceptionDetails; this.exc.push(((ed.exception && ed.exception.description) || ed.text || '').split('\n')[0].slice(0, 200) + ' @' + ed.lineNumber); }
            else if(d.method === 'Runtime.consoleAPICalled' && d.params.type === 'error'){ this.cerr.push(d.params.args.map(a => a.value != null ? String(a.value) : (a.description || '')).join(' ').slice(0, 200)); }
        };
        await this.send('Page.enable'); await this.send('Runtime.enable'); await this.send('Network.enable');
        /* 외부 요청 차단 — Supabase(기록 RPC)·광고·폰트 CDN. 녹화가 운영 DB 에 기록을 남기면 안 된다 */
        await this.send('Network.setBlockedURLs', { urls: ['https://*', 'wss://*', 'http://*.supabase.co*'] });
        await this.send('Emulation.setDeviceMetricsOverride', { width: VW, height: VH + TBH, deviceScaleFactor: DSF, mobile: true });
        await this.send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
        try{ await this.send('Emulation.setFocusEmulationEnabled', { enabled: true }); }catch(_){}
        return this;
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
        if(r.exceptionDetails) throw new Error('page: ' + JSON.stringify(r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text).slice(0, 800));
        return r.result.value;
    }
    async close(){
        try{ if(this.ws && this.ws.readyState === 1) await Promise.race([this.send('Browser.close', {}, 2000), sleep(1500)]); }catch(_){}
        try{ this.ws && this.ws.close(); }catch(_){}
        if(this.proc) killTree(this.proc.pid);
        LIVE.delete(this);
        await sleep(700);
        for(let i = 0; i < 8; i++){ try{ fs.rmSync(this.prof, { recursive: true, force: true }); break; }catch(_){ await sleep(700); } }
    }
}

/* ---------------- 페이지 쪽 녹화 도구 (문자열로 주입 — 페이지 파일에는 넣지 않는다) ---------------- */
function pageLib(){
    if(window.__R) return 1;
    const R = window.__R = { on: false, errs: [] };
    const realPN = performance.now.bind(performance);
    const rCT = window.clearTimeout.bind(window), rCI = window.clearInterval.bind(window);
    R.err = (e) => { if(R.errs.length < 30) R.errs.push(String(e && e.stack || e).split('\n').slice(0, 2).join(' | ').slice(0, 300)); };
    /* 가상 시계 */
    R.install = function(){
        if(R.on) return;
        R.on = true;
        R.VT = realPN();
        performance.now = () => R.VT;
        let rid = 0, tid = 1e7;
        R.rq = new Map(); R.tq = new Map();
        window.requestAnimationFrame = (cb) => { const id = ++rid; R.rq.set(id, cb); return id; };
        window.cancelAnimationFrame = (id) => { R.rq.delete(id); };
        window.setTimeout = (fn, ms, ...a) => { const id = ++tid; R.tq.set(id, { at: R.VT + Math.max(0, +ms || 0), fn, a, iv: 0 }); return id; };
        window.clearTimeout = (id) => { if(R.tq.has(id)) R.tq.delete(id); else rCT(id); };
        window.setInterval = (fn, ms, ...a) => { const id = ++tid; const iv = Math.max(4, +ms || 0); R.tq.set(id, { at: R.VT + iv, fn, a, iv }); return id; };
        window.clearInterval = (id) => { if(R.tq.has(id)) R.tq.delete(id); else rCI(id); };
        window.__szLockTier = 1;
    };
    R.step = function(ms){
        const tEnd = R.VT + ms;
        for(let g = 0; g < 400; g++){
            let best = null, bid = 0;
            for(const [id, t] of R.tq) if(t.at <= tEnd && (!best || t.at < best.at)){ best = t; bid = id; }
            if(!best) break;
            if(best.at > R.VT) R.VT = best.at;
            if(best.iv) best.at += best.iv; else R.tq.delete(bid);
            try{ if(typeof best.fn === 'function') best.fn(...best.a); }catch(e){ R.err(e); }
        }
        R.VT = tEnd;
        if(R.pre) try{ R.pre(); }catch(e){ R.err(e); }
        const q = R.rq; R.rq = new Map();
        for(const cb of q.values()){ try{ cb(R.VT); }catch(e){ R.err(e); } }
        if(R.post) try{ R.post(); }catch(e){ R.err(e); }
    };
    /* CSS 애니메이션·전환을 VT 에 맞춘다 (처음 본 순간 멈추고 VT 기준 시각으로) */
    R.anim = function(){
        let L; try{ L = document.getAnimations(); }catch(_){ return; }
        for(const a of L){
            if(a.__v0 === undefined){ a.__v0 = R.VT - (+a.currentTime || 0); try{ a.pause(); }catch(_){} }
            try{ a.currentTime = R.VT - a.__v0; }catch(_){}
        }
    };
    R.frame = function(n){ for(let i = 0; i < (n || 1); i++) R.step(R.STEP); R.anim(); R.dotsDraw(); return R.snap(); };
    /* 손가락 점 — 녹화 전용 (화면에 실제 손가락이 어디를 누르는지) */
    R.fing = {};
    R.dotsDraw = function(){
        let L = document.getElementById('__recDots');
        if(!L){ L = document.createElement('div'); L.id = '__recDots'; L.style.cssText = 'position:fixed;left:0;top:0;width:0;height:0;pointer-events:none;z-index:2147483646'; document.body.appendChild(L); }
        const ks = Object.keys(R.fing);
        while(L.children.length < ks.length){ const d = document.createElement('div');
            d.style.cssText = 'position:absolute;left:0;top:0;width:30px;height:30px;margin:-15px 0 0 -15px;border-radius:50%;pointer-events:none;'
                + 'background:radial-gradient(circle,rgba(255,255,255,.92) 0,rgba(255,255,255,.78) 34%,rgba(255,255,255,.28) 58%,rgba(255,255,255,0) 72%);box-shadow:0 0 0 1.5px rgba(255,255,255,.35)';
            L.appendChild(d); }
        for(let i = 0; i < L.children.length; i++){
            const d = L.children[i], f = R.fing[ks[i]];
            if(!f){ d.style.display = 'none'; continue; }
            const age = R.VT - f.t0, s = age < 120 ? 1.35 - 0.35 * age / 120 : 1;
            d.style.display = 'block';
            d.style.transform = 'translate(' + f.x.toFixed(1) + 'px,' + f.y.toFixed(1) + 'px) scale(' + s.toFixed(3) + ')';
        }
    };
    R.snap = function(){
        let st = {};
        try{ st = { run: running, z: currentZoneIdx, e: Math.round(elapsedMs), px: Math.round(player.x), py: Math.round(player.y), lives, ms: missionState, nb: bullets.length,
            inv: inventory.slice(), fev: !!szFeverOn, g: Math.round(gravGauge), dep: depots.length, sat: Math.round(satInstallProgress), mz: missionZoneIdx,
            slot: SZM2.vis ? [Math.round(SZM2.x), Math.round(SZM2.y)] : null, eng: !!SZM2.eng, cut: !!szSupplyCut, miss: szSatMiss,
            dps: depots.map(d => [Math.round(d.x), Math.round(d.y), d.item, d.collected ? 1 : 0, Math.round(d.chargeTime * 100) / 100]), beam: !!gravityFieldActive, ag: szAgOn(), ion: szIonOn(), sh: shieldBubbleActive(performance.now()) }; }catch(e){ st.err = String(e); }
        return st;
    };
    /* 화면(CSS px) ↔ 캔버스 논리 좌표 */
    R.c2s = function(x, y){ const r = canvas.getBoundingClientRect(); return { x: r.left + x / CW * r.width, y: r.top + y / CH * r.height }; };
    R.el = function(sel){ const e = document.querySelector(sel); if(!e) return null; const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height, vis: getComputedStyle(e).visibility !== 'hidden' && +getComputedStyle(e).opacity > 0.05 }; };
    /* 조향 — 목표 지점까지 부드럽게(최대 속도·가속 제한). 반환 = 손가락이 움직일 CSS px (ship 이동 / k) */
    R.pv = { x: 0, y: 0 };
    R.pilot = function(tx, ty, vmax, acc){
        const dt = R.STEP * R.SUB / 1000;
        const dx = tx - player.x, dy = ty - player.y, d = Math.hypot(dx, dy);
        let vx = 0, vy = 0;
        if(d > 0.5){ const v = Math.min(vmax, d * 4.2); vx = dx / d * v; vy = dy / d * v; }
        const a = (acc || 2600) * dt;
        let ex = vx - R.pv.x, ey = vy - R.pv.y; const el = Math.hypot(ex, ey);
        if(el > a){ ex *= a / el; ey *= a / el; }
        R.pv.x += ex; R.pv.y += ey;
        const k = (window.SZCTL && SZCTL.sens * SZCTL.scale) || 1;
        return { dx: R.pv.x * dt / k, dy: R.pv.y * dt / k };
    };
    R.pilotStop = function(){ R.pv.x = 0; R.pv.y = 0; };
    /* 회피 보정 — 멀리(rmin~rmax) 있는 운석 중 기체에 minMiss 안으로 지나갈 것만 궤도를 아주 조금씩 비킨다(속력 유지) */
    R.avoid = { on: true, minMiss: 30, rmin: 55, rmax: 300, kill: true };
    R.deflect = function(){
        if(!R.avoid.on || typeof bullets === 'undefined') return;
        const A = R.avoid, cx = player.x, cy = player.y;
        /* 기체 속도(직전 스텝과의 차) — 기체가 운석 쪽으로 달려가는 경우까지 상대 속도로 본다 */
        const dts = R.STEP / 1000;
        const pvx = R.lpx == null ? 0 : (cx - R.lpx) / dts, pvy = R.lpy == null ? 0 : (cy - R.lpy) / dts;
        R.lpx = cx; R.lpy = cy;
        for(const b of bullets){
            if(b.zk) continue;
            const rx = b.x - cx, ry = b.y - cy, d = Math.hypot(rx, ry);
            if(d < A.rmin || d > A.rmax) continue;
            const ux = b.vx - pvx, uy = b.vy - pvy;
            const vv = ux * ux + uy * uy; if(vv < 1) continue;
            const t = -(rx * ux + ry * uy) / vv; if(t <= 0) continue;
            const mx = rx + ux * t, my = ry + uy * t, miss = Math.hypot(mx, my);
            if(miss >= A.minMiss) continue;
            let nx = mx, ny = my, nl = Math.hypot(nx, ny);
            if(nl < 0.01){ nx = -uy; ny = ux; nl = Math.hypot(nx, ny); }
            nx /= nl; ny /= nl;
            const sp = Math.hypot(b.vx, b.vy) || 1, need = (A.minMiss - miss) / t, add = Math.min(need, sp * 0.06);
            b.vx += nx * add; b.vy += ny * add;
            const s2 = Math.hypot(b.vx, b.vy) || 1; b.vx *= sp / s2; b.vy *= sp / s2;
        }
        /* 그래도 판정 거리 안에 들어온 운석은 지운다(드물다 — 피격 연출이 영상에 남지 않게) */
        if(A.kill){
            const HR = (HIT_RADIUS + 9) * (HIT_RADIUS + 9);
            for(let i = bullets.length - 1; i >= 0; i--){ const b = bullets[i]; if(b.zk) continue; const dx = b.x - cx, dy = b.y - cy; if(dx * dx + dy * dy < HR) bullets.splice(i, 1); }
        }
    };
    /* 운석 하나를 (x,y)에서 (tx,ty)를 향해 speed 로 — 게임의 spawnBullet 으로 만든 뒤 자리·속도만 바꾼다 */
    R.rock = function(x, y, tx, ty, speed){
        const n0 = bullets.length;
        try{ spawnBullet(performance.now(), speed, 0, 1); }catch(e){ R.err(e); return 0; }
        for(let i = n0; i < bullets.length; i++){
            const b = bullets[i], dx = tx - x, dy = ty - y, d = Math.hypot(dx, dy) || 1;
            b.x = x; b.y = y; b.vx = dx / d * speed; b.vy = dy / d * speed; b.aimed = true;
            if(b.trail) b.trail.length = 0; b.trailLen = 0; b._trailInit = false;
        }
        return bullets.length - n0;
    };
    /* 운석 말고 다른 위험물(플레어·혜성·보스 등)은 녹화 중 기체 판정만 끈다(그림·움직임은 그대로) */
    R.noHaz = function(){
        for(const n of ['checkAsteroidClusterCollision', 'checkSolarFlareCollision', 'checkMagneticMineCollision', 'checkSupernovaRingCollision', 'checkPulsarBeamCollision',
            'checkCometCollision', 'checkSplitterCollision', 'checkBlackHoleJetCollision', 'checkZoneBossCollision']) if(typeof window[n] === 'function') window[n] = function(){ return false; };
        R.pre = R.deflect;
        /* 피격 기록 — 어떤 것에 맞았는지(회피 보정 튜닝용) */
        if(typeof window.triggerHitFx === 'function' && !R._hitW){
            R._hitW = 1; const o = window.triggerHitFx;
            window.triggerHitFx = function(){
                try{ const near = bullets.map(b => [Math.round(Math.hypot(b.x - player.x, b.y - player.y)), Math.round(b.vx), Math.round(b.vy), b.zk || '']).sort((a, b) => a[0] - b[0]).slice(0, 3);
                    R.err('HIT e=' + Math.round(elapsedMs) + ' p=' + Math.round(player.x) + ',' + Math.round(player.y) + ' near=' + JSON.stringify(near) + ' km=' + JSON.stringify(szKillMark && [Math.round(szKillMark.x), Math.round(szKillMark.y), Math.round(szKillMark.vx), Math.round(szKillMark.vy)])); }catch(_){}
                return o.apply(this, arguments);
            };
        }
        return 1;
    };
    /* 장면 전환 — 어두운 막(녹화 전용 DOM, 화면 흔들림 아님) */
    R.veil = function(a){
        let v = document.getElementById('__recVeil');
        if(!v){ v = document.createElement('div'); v.id = '__recVeil'; v.style.cssText = 'position:fixed;inset:0;background:#02040c;pointer-events:none;z-index:2147483647;opacity:0'; document.body.appendChild(v); }
        v.style.opacity = String(Math.max(0, Math.min(1, a)));
        return 1;
    };
    /* 보급 캡슐 하나 (녹화 전용 — 게임의 캡슐 객체와 같은 모양) */
    R.depot = function(item, x, y){
        const now = performance.now(), key = currentZoneIdx + '-rec' + (++R._dk || (R._dk = 1));
        depotsSpawnedZones.add(key);
        depots.push({x, y, speed: 24, item, zoneIdx: currentZoneIdx, slot: 'rec', key, chargeTime: 0, collected: false, collectedByPeer: false, spawnedAt: now, radius: 19});
        return 1;
    };
    R.STEP = 16.6667; R.SUB = 2;
    return 1;
}
const PAGE_LIB = '(' + pageLib.toString() + ')()';

/* ---------------- 녹화 세션 ---------------- */
class Rec {
    constructor(e, base){ this.e = e; this.base = base; this.fing = new Map(); this.n = 0; this.dir = null; this.log = []; this.tid = 0; }
    async boot(ls){
        const e = this.e;
        /* localStorage 를 먼저 심는다 — 같은 오리진의 빈 페이지에서 */
        await e.send('Page.navigate', { url: this.base + '/404-szhow' });
        await sleep(600);
        await e.ev(`(function(){ localStorage.clear(); sessionStorage.clear(); const o = ${JSON.stringify(ls)}; for(const k in o) localStorage.setItem(k, o[k]); return 1; })()`);
        await e.send('Page.navigate', { url: this.base + '/games/dodge/?lang=' + LANG });
        for(let i = 0; i < 120; i++){ await sleep(200); try{ if(await e.ev('document.readyState === "complete" && typeof gameLoop === "function" && typeof startGame === "function"', 5000)) break; }catch(_){} }
        /* 드론 그림(drones.webp)은 부팅 5초 뒤 받는다 — 녹화 전에 다 받고 굽게 */
        for(let i = 0; i < 60; i++){
            await sleep(250);
            const ok = await e.ev('(function(){ try{ const im = szDroneImg(); return !!(im && im.complete && im.naturalWidth); }catch(_){ return false; } })()');
            if(ok) break;
        }
        /* 상단 바 높이를 재서 뷰포트 = 930 + 바 (영상은 바 아래만 자른다 — 이전 녹화와 같은 구도) */
        const tb = await e.ev('Math.round(document.querySelector(".topbar").getBoundingClientRect().bottom)');
        if(tb !== TBH){ TBH = tb; await e.send('Emulation.setDeviceMetricsOverride', { width: VW, height: VH + TBH, deviceScaleFactor: DSF, mobile: true }); }
        await sleep(1500);
        await e.ev(PAGE_LIB);
        const info = await e.ev('({tbh: Math.round(document.querySelector(".topbar").getBoundingClientRect().bottom), canvas: (function(){ const r = canvas.getBoundingClientRect(); return [r.left, r.top, r.width, r.height].map(Math.round); })(), drone: (function(){ try{ const im = szDroneImg(); return im ? im.naturalWidth + "x" + im.naturalHeight : null; }catch(_){ return null; } })(), float: !!(window.SZCTL && SZCTL.on), lang: (window.LpI18n && LpI18n.getLang && LpI18n.getLang()), dpr: devicePixelRatio, cw: CW, ch: CH})');
        say('부팅', JSON.stringify(info));
        if(!info.float) throw new Error('플로팅 조작이 아님 — 터치 에뮬레이션 확인');
        return info;
    }
    /* 터치 — 모든 손가락 상태를 한 번에 보낸다(바뀐 손가락만 이벤트가 된다) */
    pts(){ return [...this.fing.values()].map((p) => ({ x: p.x, y: p.y, id: p.id, radiusX: 8, radiusY: 8, force: 1 })); }
    async dots(){ const o = {}; for(const [id, p] of this.fing) o[id] = { x: p.x, y: p.y, t0: p.t0 }; await this.e.ev('__R.fing = ' + JSON.stringify(o) + ', 1'); }
    async down(name, x, y){
        const vt = await this.e.ev('__R.VT');
        this.fing.set(name, { x, y, t0: vt, id: ++this.tid });
        await this.e.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: this.pts() });
        await this.dots();
    }
    async move(name, x, y){
        const p = this.fing.get(name); if(!p) return;
        p.x = x; p.y = y;
        await this.e.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: this.pts() });
        await this.dots();
    }
    async up(name){
        /* Chromium CDP: touchEnd 에 실은 점만 뗀다(빈 목록 = 전부). 남은 손가락은 그대로 — 실측 2026-10-08 */
        const p = this.fing.get(name); if(!p) return;
        this.fing.delete(name);
        await this.e.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [{ x: p.x, y: p.y, id: p.id }] });
        await this.dots();
    }
    async upAll(){ if(this.fing.size){ this.fing.clear(); await this.e.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); await this.dots(); } }
    /* 조향 손가락을 목표(캔버스 좌표)로 한 프레임 */
    async steer(tx, ty, vmax, acc){
        const f = this.fing.get('steer'); if(!f) return;
        const d = await this.e.ev(`__R.pilot(${tx}, ${ty}, ${vmax || 260}, ${acc || 2600})`);
        if(Math.abs(d.dx) + Math.abs(d.dy) < 0.01) return;
        await this.move('steer', f.x + d.dx, f.y + d.dy);
    }
    /* 한 영상 프레임 = 시뮬 2번 + 스크린샷 */
    async shot(){
        const r = await this.e.send('Page.captureScreenshot', { format: 'jpeg', quality: 94, clip: { x: 0, y: TBH, width: VW, height: VH, scale: 1 } }, 30000);
        const f = path.join(this.dir, String(this.n++).padStart(5, '0') + '.jpg');
        fs.writeFileSync(f, Buffer.from(r.data, 'base64'));
    }
    async frame(capture = true){
        const st = await this.e.ev('__R.frame(' + SUB + ')');
        this.st = st;
        if(capture){ await this.shot(); this.log.push([this.n - 1, st]); }
        return st;
    }
    /* 녹화 없이 시간만 (ms) */
    async skip(ms){ const n = Math.round(ms / STEP); await this.e.ev(`(function(){ for(let i = 0; i < ${n}; i++) __R.step(__R.STEP); __R.anim(); return 1; })()`); this.st = await this.e.ev('__R.snap()'); return this.st; }
    t(){ return this.n / FPS; }
}

/* ---------------- 인코딩 ---------------- */
function encode(dir, name, crf, extra = {}){
    const out = path.join(OUTDIR, name + '.mp4');
    const vf = 'scale=' + VW + ':' + VH + ':flags=lanczos' + (extra.vf ? ',' + extra.vf : '');
    execFileSync(FFMPEG, ['-v', 'error', '-y', '-framerate', String(FPS), '-i', path.join(dir, '%05d.jpg'), '-vf', vf, '-c:v', 'libx264', '-profile:v', 'main', '-pix_fmt', 'yuv420p',
        '-preset', 'veryslow', '-crf', String(crf), '-tune', 'animation', '-x264-params', 'keyint=60:min-keyint=30', '-movflags', '+faststart', '-an', out], { stdio: 'inherit' });
    return out;
}
function poster(dir, name, idx){
    const out = path.join(OUTDIR, name + '.webp');
    execFileSync(FFMPEG, ['-v', 'error', '-y', '-i', path.join(dir, String(idx).padStart(5, '0') + '.jpg'), '-vf', 'scale=' + VW + ':' + VH + ':flags=lanczos', '-c:v', 'libwebp', '-quality', '50', '-frames:v', '1', out], { stdio: 'inherit' });
    return out;
}
function sheet(mp4, name, cols = 8, every = 0.5){
    fs.mkdirSync(REVIEW, { recursive: true });
    const out = path.join(REVIEW, name + '_sheet.png');
    execFileSync(FFMPEG, ['-v', 'error', '-y', '-i', mp4, '-vf', 'fps=' + (1 / every) + ',scale=216:-1,tile=' + cols + 'x3:padding=4:color=black', '-frames:v', '1', out], { stdio: 'inherit' });
    return out;
}
function probeDur(mp4){
    try{ return +execFileSync(FFMPEG.replace(/ffmpeg(\.exe)?$/, 'ffprobe$1'), ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', mp4]).toString().trim(); }catch(_){ return null; }
}

/* ---------------- 공통: 판 시작 → 존 이동 ---------------- */
const LS_BASE = {
    luckyplz_lang: LANG, lp_lang: LANG,
    szx_ctl: 'float', szx_sens: '1.8', szx_tier: '0', szx_fx: '1',
    szx_log: JSON.stringify({ v: 1, far: 8, seen: 511, sat: 0, ch: 1, runs: 6, end: 0, bestAct: [0, 0, 0, 0, 0], skin: 0 }),
    szx_ctl_tip: '3'
};
async function startRun(rec, opts = {}){
    const e = rec.e;
    await e.ev('__R.install(); window.__szLockTier = 1; 1');
    await e.ev('(function(){ try{ startGame(); }catch(e){ __R.err(e); } return 1; })()');
    for(let i = 0; i < 400; i++){ await rec.skip(STEP * 6); if(rec.st.run) break; }
    if(!rec.st.run) throw new Error('판이 시작되지 않음: ' + JSON.stringify(rec.st) + ' ' + JSON.stringify(await e.ev('__R.errs')));
    await rec.skip(300);
}
/* 존 z 의 시작 + off 초로 논리 시각을 옮긴다 (그 사이 보급·미션은 건너뛴 것으로) */
async function jump(rec, z, off){
    await rec.e.ev(`(function(){ const now = performance.now(); startedAt = now - (ZONES[${z}].s * 1000 + ${Math.round(off * 1000)}) - totalPausedMs; bullets.length = 0; depots.length = 0; lives = Math.max(lives, 4); return 1; })()`);
    await rec.skip(STEP * 2);
}

const lerp = (a, b, k) => a + (b - a) * k;
const ease = (k) => k <= 0 ? 0 : k >= 1 ? 1 : k * k * (3 - 2 * k);
/* 버튼 중심 (뷰포트 CSS px) */
async function btn(rec, sel){ return rec.e.ev('__R.el(' + JSON.stringify(sel) + ')'); }
/* 장면 전환 막 — n 프레임 동안 a0→a1 (녹화하면서) */
async function veil(rec, a0, a1, n, each){
    for(let i = 1; i <= n; i++){ await rec.e.ev('__R.veil(' + lerp(a0, a1, i / n) + ')'); if(each) await each(i); await rec.frame(); }
}

/* ---------------- 장 1: 위성 (달) ----------------
   ① 빈 곳을 끌어 조향(손가락 고리) ② 미션 → SAT 가 BEAM 오른쪽에 반투명으로 나타남 → 노란 슬롯 아래로
   ③ SAT 꾹 1.2초 → PERFECT LINK ④ (다른 판의 장면) 위성 미션 2연속 실패 → 보급 영구 차단 경고 배너 */
async function clipSat(rec){
    const e = rec.e, cue = {};
    await e.ev('__R.noHaz()');
    /* 존 1(달) 미션 활성 = 논리 27.48s. 클립 1.0s 쯤 켜지게 26.45s 로 */
    await jump(rec, 1, 4.45);
    const S0 = { x: 336, y: TBH + 560 };      /* 조향 손가락 — 오른쪽 아래 빈 곳 */
    let satDown = false, satUp = false, okAt = -1, actAt = -1;
    for(let f = 0; f < 150; f++){
        const t = rec.t(), st = rec.st;
        if(f === 3) await rec.down('steer', S0.x, S0.y);
        if(st.ms === 'active' && actAt < 0){ actAt = t; cue.mission = t; }
        if(rec.fing.has('steer')){
            if(actAt < 0){
                /* 미션 전 — 왼쪽 위로 갔다가 가운데로 (끌어서 조종하는 모습) */
                const tg = t < 0.62 ? { x: 120, y: 360 } : { x: 205, y: 330 };
                await rec.steer(tg.x, tg.y, 300);
            } else if(st.slot){
                /* 노란 슬롯 바로 아래 — 원뿔(±45°, 180px)이 슬롯을 덮는 자리 */
                await rec.steer(st.slot[0], Math.min(st.slot[1] + 118, 520), satDown ? 210 : 330);
            }
        }
        /* SAT 꾹 — 원뿔이 슬롯에 닿은 뒤(엔게이지) */
        if(!satDown && actAt >= 0 && st.eng && t - actAt > 0.7){
            const b = await btn(rec, '#satBtn');
            await rec.down('sat', b.x, b.y); satDown = true; cue.sat = t;
        }
        if(satDown && okAt < 0 && st.ms === 'success'){ okAt = t; cue.ok = t; }
        if(satDown && !satUp && okAt >= 0 && t - okAt > 0.12){ await rec.up('sat'); satUp = true; }
        await rec.frame();
        if(okAt >= 0 && t - okAt > 1.55) break;
    }
    if(okAt < 0) throw new Error('위성 설치 실패: ' + JSON.stringify(rec.st));
    /* ④ 다른 장면 — 목성 미션을 놓친다(이번 판 첫 실패는 이미 한 번 있었던 것으로 주입) → 보급 영구 차단 */
    await veil(rec, 0, 1, 6);
    await rec.upAll();
    await e.ev('__R.pilotStop(), 1');
    /* 목성 도착 카드가 사라진 뒤(3.5s) 미션이 켜지는 5.0s 까지 녹화 없이 — 배너 자리(위)는 비워 둔다(위험물·보급이 가까우면 배너가 옅어져 안 읽힌다) */
    await jump(rec, 4, 0.6);
    await e.ev('(function(){ __R.pre = function(){ __R.deflect(); for(let i = bullets.length - 1; i >= 0; i--) if(bullets[i].y < 210 && !bullets[i].zk) bullets.splice(i, 1); depots.length = 0; }; player.x = 92; player.y = 470; return 1; })()');
    for(let i = 0; i < 80 && rec.st.ms !== 'active'; i++) await rec.skip(STEP * 6);
    await rec.skip(300);
    await e.ev('(function(){ szSatMiss = 1; commLinkLost = true; missionActiveUntil = performance.now() + 1300; return 1; })()');
    cue.cutVeil = rec.t();
    await veil(rec, 1, 0, 6);
    let failAt = -1;
    for(let f = 0; f < 90; f++){
        const st = rec.st;
        if(st.cut && failAt < 0){ failAt = rec.t(); cue.cut = failAt; }
        await rec.frame();
        if(failAt >= 0 && rec.t() - failAt > 1.9) break;
    }
    if(failAt < 0) throw new Error('보급 차단이 안 걸림: ' + JSON.stringify(rec.st));
    cue.poster = cue.sat + 0.6;
    return cue;
}

/* ---------------- 장 2: BEAM (화성) ----------------
   슬롯 [방어막·폭탄] 에서 시작 → 캡슐(윙맨 — 새 드론 그림) 아래로 → BEAM 꾹 1.5초 → 슬롯 3칸째
   → 두 번째 캡슐(이온 충격파) → BEAM 꾹 → 슬롯 4칸째 (5칸까지 보관) */
async function clipBeam(rec){
    const e = rec.e, cue = {};
    await e.ev('__R.noHaz()');
    await e.ev('(function(){ missionsCompletedZones.add(2); depotsSpawnedZones.add("2-0"); depotsSpawnedZones.add("2-1"); return 1; })()');   /* 화성 과제(포보스)·화성 정규 보급은 이 장의 주제가 아니다 — 녹화 캡슐 두 개만 */
    await jump(rec, 2, 2.2);
    await rec.skip(2600);                      /* 화성 도착 카드가 걷힐 때까지 */
    await e.ev('(function(){ depots.length = 0; inventory.fill(null); inventory[0] = ITEM.SHIELD; inventory[1] = ITEM.WIPE; syncInventoryUI(); player.x = 176; player.y = 450; gravGauge = GRAV_GAUGE_MAX; return 1; })()');
    const S0 = { x: 334, y: TBH + 575 };
    let phase = 0, beamAt = -1, gotAt = -1, n = 0;
    const plan = [{ item: 'MINI', x: 250, y: 92, at: 0.12 }, { item: 'ION', x: 112, y: 96, at: 2.2 }], OFF = 142;
    for(let f = 0; f < 260; f++){
        const t = rec.t(), st = rec.st;
        for(const p of plan) if(!p.done && t >= p.at){ p.done = true; await e.ev(`__R.depot(ITEM.${p.item}, ${p.x}, ${p.y})`); if(p === plan[0]) cue.cap1 = t; else cue.cap2 = t; }
        if(f === 10) await rec.down('steer', S0.x, S0.y);
        const live = (st.dps || []).filter(d => !d[3]);
        const d = live[0];
        if(rec.fing.has('steer') && d) await rec.steer(d[0], Math.min(d[1] + OFF, 560), 300);
        else if(rec.fing.has('steer')) await rec.steer(st.px, st.py, 300);
        /* BEAM 꾹 — 캡슐 아래에 거의 왔을 때 */
        if(d && !rec.fing.has('beam') && Math.abs(st.px - d[0]) < 14 && Math.abs(st.py - (d[1] + OFF)) < 24 && t > (phase === 0 ? 0.8 : 3.4) && phase < 2){
            const b = await btn(rec, '#gravBtn');
            await rec.down('beam', b.x, b.y); beamAt = t; cue['beam' + (phase + 1)] = t;
        }
        const filled = (st.inv || []).filter(Boolean).length;
        if(rec.fing.has('beam') && filled >= 3 + phase){ await rec.up('beam'); cue['got' + (phase + 1)] = t; gotAt = t; phase++; }
        await rec.frame();
        if(phase >= 2 && t - gotAt > 1.15) break;
    }
    if(phase < 2) throw new Error('BEAM 획득 실패: ' + JSON.stringify(rec.st));
    cue.poster = cue.beam1 + 0.7;
    return cue;
}
/* ---------------- 장 4: 아이템 (천왕성) ----------------
   슬롯 [반중력파·이온 충격파·방어막·폭탄] — 자막 순서대로 슬롯을 눌러 쓴다. 아이템마다 짧은 장면(어두운 막으로 넘김)이라
   앞 아이템 효과는 장면이 바뀔 때 끈다(녹화 보정 — 실제 지속 15·30·20초는 자막에). 운석은 녹화 전용으로 기체 쪽에 더 보낸다 */
async function clipItems(rec){
    const e = rec.e, cue = {};
    await e.ev('__R.noHaz()');
    await e.ev('(function(){ missionsCompletedZones.add(6); depotsSpawnedZones.add("6-0"); depotsSpawnedZones.add("6-1"); return 1; })()');
    await jump(rec, 6, 1.0);
    await rec.skip(2700);                      /* 천왕성 도착 카드가 걷힐 때까지 */
    await e.ev('(function(){ depots.length = 0; inventory.fill(null); inventory[0] = ITEM.ANTIGRAV; inventory[1] = ITEM.ION; inventory[2] = ITEM.SHIELD; inventory[3] = ITEM.WIPE; syncInventoryUI(); player.x = 180; player.y = 430; bullets.length = 0; __R.avoid.on = false; return 1; })()');
    const S0 = { x: 330, y: TBH + 585 };
    const rocks = async (list) => { if(list.length) await e.ev('(function(){ ' + list.map(r => `__R.rock(${r.map(v => Math.round(v * 10) / 10).join(',')});`).join('') + ' return 1; })()'); };
    const rnd = (() => { let x = 20261008; return () => { x = (x * 1103515245 + 12345) >>> 0; return x / 4294967296; }; })();
    let tapAt = -1;
    const press = async (i, name) => { const b = await btn(rec, '#itemSlot' + i); await rec.down('tap', b.x, b.y); tapAt = rec.t(); cue[name] = rec.t(); };
    /* 한 장면 — dur 초 동안 조향·탭 떼기·운석 보내기 */
    const scene = async (dur, spawn, at) => {
        const t0 = rec.t(); let next = t0 + (at || 0.3);
        while(rec.t() - t0 < dur){
            const t = rec.t(), st = rec.st;
            if(rec.fing.has('steer')) await rec.steer(180 + Math.sin(t * 1.3) * 20, 430 + Math.sin(t * 0.9) * 8, 120, 900);
            if(tapAt >= 0 && t - tapAt > 0.17){ await rec.up('tap'); tapAt = -1; }
            if(spawn && t >= next){ const r = spawn(t - t0, st); if(r){ await rocks(r.L); next = t + r.gap; } else next = 1e9; }
            await rec.frame();
        }
    };
    const cut = async (fx) => {
        await veil(rec, 0, 1, 4);
        await e.ev('(function(){ ' + fx + ' bullets.length = 0; return 1; })()');
        await veil(rec, 1, 0, 4);
    };
    await rec.frame(); await rec.frame();
    await rec.down('steer', S0.x, S0.y);
    /* ① 반중력파 — 사방에서 기체를 향해. 빠른 것일수록 깊이 파고들었다 밀려 나간다 */
    await rec.frame(); await rec.frame(); await rec.frame(); await rec.frame(); await rec.frame(); await rec.frame(); await rec.frame(); await rec.frame();
    await press(0, 'ag');
    await scene(2.45, (dt, st) => {
        if(dt > 2.05) return null;
        const L = [];
        for(let k = 0; k < (rnd() < 0.45 ? 2 : 1); k++){ const a = -Math.PI / 2 + (rnd() - 0.5) * 3.2, R0 = 340, sp = 250 + rnd() * 200;
            L.push([st.px + Math.cos(a) * R0, st.py + Math.sin(a) * R0, st.px + (rnd() - 0.5) * 8, st.py - 8, sp]); }
        return { L, gap: 0.13 + rnd() * 0.06 };
    }, 0.12);
    /* ② 이온 충격파 — 앞(위)에서 쏟아지는 운석이 부채꼴에 드는 순간 분해 */
    await cut('szItemsReset();');
    await e.ev('(function(){ __R.avoid.on = true; __R.avoid.minMiss = 34; return 1; })()');
    await press(1, 'ion');
    await scene(2.55, (dt, st) => {
        if(dt > 2.2) return null;
        const L = [];
        for(let k = 0; k < 2; k++){ const x = st.px + (rnd() - 0.5) * 320, y = -20 - rnd() * 50; L.push([x, y, st.px + (rnd() - 0.5) * 80, st.py - 40, 250 + rnd() * 130]); }
        return { L, gap: 0.12 + rnd() * 0.06 };
    }, 0.05);
    /* ③ 방어막 — 사방에서 기체로, 막에 부딪혀 부서진다 */
    await cut('szItemsReset();');
    await e.ev('(function(){ __R.avoid.on = false; return 1; })()');
    await press(2, 'sh');
    await scene(2.2, (dt, st) => {
        if(dt > 1.75) return null;
        const a = rnd() * Math.PI * 2, R0 = 300, sp = 230 + rnd() * 90;
        return { L: [[st.px + Math.cos(a) * R0, st.py + Math.sin(a) * R0, st.px, st.py, sp]], gap: 0.2 + rnd() * 0.08 };
    }, 0.15);
    /* ④ 폭탄 — 화면 가득 운석 → 싹쓸이 + 5초간 새 운석 없음 */
    await cut('shieldBubbleUntil = 0;');
    await e.ev('(function(){ __R.avoid.on = true; __R.avoid.minMiss = 30; return 1; })()');
    {
        const L = [];
        for(let k = 0; k < 20; k++){ const x = 20 + rnd() * 320, y = 40 + rnd() * 300; L.push([x, y, x + (rnd() - 0.5) * 160, 640, 120 + rnd() * 80]); }
        for(let k = 0; k < 8; k++){ const x = 20 + rnd() * 320, y = -20 - rnd() * 60; L.push([x, y, x + (rnd() - 0.5) * 120, 640, 220 + rnd() * 60]); }
        await rocks(L);
    }
    cue.wave = rec.t();
    await scene(0.55, null);
    await press(3, 'wipe');
    await scene(1.6, null);
    cue.poster = cue.ion + 0.9;
    return cue;
}

async function main(){
    fs.mkdirSync(TMP, { recursive: true }); fs.mkdirSync(OUTDIR, { recursive: true }); fs.mkdirSync(REVIEW, { recursive: true });
    const base = await startServer();
    say('서버', base, '루트', PUB);
    const e = await new Edge().launch();
    try{
        if(CLIPS[0] === 'verify'){
            /* 팝업 검증 — 412×915·360×740 × ko·en: 장마다 영상이 실제로 재생되는가(시간이 흐르는가)·자막 칩·콘솔 에러 */
            const out = [];
            for(const [w, h, dsf] of [[412, 915, 2.625], [360, 740, 3]]){
                for(const lang of ['ko', 'en']){
                    await e.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: dsf, mobile: true });
                    await e.send('Page.navigate', { url: base + '/404-x' }); await sleep(500);
                    await e.ev(`localStorage.clear(); localStorage.setItem('luckyplz_lang', '${lang}'); 1`);
                    e.exc.length = 0; e.cerr.length = 0;
                    await e.send('Page.navigate', { url: base + '/games/dodge/?lang=' + lang });
                    for(let i = 0; i < 80; i++){ await sleep(200); try{ if(await e.ev('document.readyState === "complete" && !!window.SZH')) break; }catch(_){} }
                    await sleep(1200);
                    await e.ev('document.getElementById("ovHowBtn").click(), 1');
                    for(let ch = 0; ch < 4; ch++){
                        await e.ev('SZH.show(' + ch + '), 1');
                        await sleep(2600);
                        const r = await e.ev(`(function(){ const v = document.querySelector('#szHow video'), c = document.querySelector('#szHow .szh-chip'), vb = document.querySelector('#szHow .szh-vbox').getBoundingClientRect();
                            return { src: (v.currentSrc || '').split('/').pop(), rs: v.readyState, t: Math.round(v.currentTime * 100) / 100, d: Math.round(v.duration * 100) / 100, vw: v.videoWidth, vh: v.videoHeight, paused: v.paused, err: v.error && v.error.code,
                                chip: c.classList.contains('on') ? c.textContent : '', box: [Math.round(vb.width), Math.round(vb.height)] }; })()`);
                        const shot = await e.send('Page.captureScreenshot', { format: 'png' });
                        const f = path.join(REVIEW, 'popup_' + w + 'x' + h + '_' + lang + '_ch' + (ch + 1) + '.png');
                        fs.writeFileSync(f, Buffer.from(shot.data, 'base64'));
                        r.ok = r.rs >= 2 && r.t > 0.5 && !r.err && r.vw === 432;
                        out.push(Object.assign({ vp: w + 'x' + h, lang, ch: ch + 1 }, r));
                    }
                    out.push({ vp: w + 'x' + h, lang, exc: e.exc.slice(), cerr: e.cerr.slice() });
                }
            }
            for(const o of out) say(JSON.stringify(o));
            const bad = out.filter(o => o.ok === false || (o.exc && (o.exc.length || o.cerr.length)));
            say(bad.length ? '검증 실패 ' + bad.length : '검증 통과 — 16장 재생·콘솔 에러 0');
            if(bad.length) process.exitCode = 1;
            return;
        }
        if(CLIPS[0] === 'touchtest'){
            await e.send('Page.navigate', { url: base + '/404-x' }); await sleep(800);
            await e.ev(`window.__tl=[];for(const t of ['touchstart','touchmove','touchend','touchcancel'])document.addEventListener(t,e=>__tl.push(t+':'+[...e.changedTouches].map(x=>x.identifier).join(',')+'/'+e.touches.length),{passive:true});1`);
            const P = (a) => a.map(([x, y, id]) => ({ x, y, id }));
            const mode = A.mode || 'move';
            await e.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: P([[100, 100, 1]]) });
            await e.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: P([[100, 100, 1], [200, 200, 2]]) });
            await e.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: P([[110, 100, 1], [200, 200, 2]]) });
            if(mode === 'move') await e.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: P([[110, 100, 1]]) });
            else await e.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: P([[110, 100, 1]]) }).catch(x => say('err', x.message));
            await e.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: P([[120, 100, 1]]) });
            await e.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
            await sleep(300);
            say('events', JSON.stringify(await e.ev('__tl')));
            return;
        }
        if(CLIPS[0] === 'probe'){
            const rec = new Rec(e, base);
            rec.dir = path.join(TMP, 'probe'); fs.mkdirSync(rec.dir, { recursive: true });
            await rec.boot(LS_BASE);
            await startRun(rec);
            const z = +(A['probe-zone'] || 1);
            await jump(rec, z, +(A['probe-off'] || 2));
            for(let i = 0; i < 90; i++){ await rec.frame(i % 15 === 0); }
            say('상태', JSON.stringify(rec.st));
            say('에러', JSON.stringify(await e.ev('__R.errs')), JSON.stringify(e.exc.slice(0, 5)));
            return;
        }
        const FN = { sat: clipSat, beam: clipBeam, items: clipItems };
        /* fever.mp4 — 2026-10-07 녹화 그대로 둔다(플로팅·5칸 UI 와 같고 바뀐 아이템·SAT 가 화면에 없다). 다시 찍어야 하면 여기에 clipFever 를 더한다 */
        const CRF = { sat: 30, beam: 30, items: 31 };
        const LSX = { sat: { szx_ctl_tip: '0' } };
        const report = {};
        for(let ci = 0; ci < CLIPS.length; ci++){
            const c = CLIPS[ci];
            if(!FN[c]){ say('건너뜀(녹화기 없음)', c); continue; }
            const e2 = ci === 0 && !(report[c] && report[c].hits) ? e : await new Edge().launch();
            try{
                const rec = new Rec(e2, base);
                rec.dir = path.join(TMP, c); fs.rmSync(rec.dir, { recursive: true, force: true }); fs.mkdirSync(rec.dir, { recursive: true });
                await rec.boot(Object.assign({}, LS_BASE, LSX[c] || {}));
                await startRun(rec);
                const cue = await FN[c](rec);
                const errs = await e2.ev('__R.errs');
                const mp4 = encode(rec.dir, c, +(A.crf || CRF[c]));
                poster(rec.dir, c, cue.poster != null ? Math.round(cue.poster * FPS) : 0);
                const sh = sheet(mp4, c);
                const r = { frames: rec.n, dur: probeDur(mp4), kb: Math.round(fs.statSync(mp4).size / 1024), cue, errs, exc: e2.exc.slice(0, 5), cerr: e2.cerr.slice(0, 5), sheet: sh };
                /* 피격(목숨 감소)이 영상에 남았는지 — 회피 보정이 놓친 것 */
                let hits = 0; for(let i = 1; i < rec.log.length; i++) if(rec.log[i][1].lives < rec.log[i - 1][1].lives) hits++;
                r.hits = hits;
                r.tries = ((report[c] && report[c].tries) || 0) + 1;
                report[c] = r;
                /* 연출 난수(Math.random)가 판마다 달라 드물게 회피 보정이 놓친다 — 피격이 영상에 남았으면 3번까지 다시 */
                if(hits && r.tries < 3){ say('⚠ 피격 ' + hits + '회 — 다시 찍는다', c); ci--; continue; }
                if(hits) say('⚠ 피격 ' + hits + '회가 영상에 남음', c);
                say(c, JSON.stringify(r));
                fs.writeFileSync(path.join(REVIEW, c + '_log.json'), JSON.stringify({ cue, log: rec.log }, null, 0));
                if(!A.keep) fs.rmSync(rec.dir, { recursive: true, force: true });
            } finally { if(e2 !== e) await e2.close(); }
        }
        say('완료', JSON.stringify(Object.fromEntries(Object.entries(report).map(([k, v]) => [k, { dur: v.dur, kb: v.kb, cue: v.cue }]))));
    } finally {
        await e.close();
        try{ SERVER && SERVER.close(); }catch(_){}
    }
}
main().catch(err => { console.error('[rec] 실패', err && err.stack || err); process.exitCode = 1; })
    .finally(() => { for(const x of LIVE) try{ killTree(x.proc.pid); }catch(_){} setTimeout(() => process.exit(process.exitCode || 0), 300); });
