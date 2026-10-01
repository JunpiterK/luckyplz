// 台灣麻將 엔진 하네스 — 결정적(시드) AI 대국 + 불변식 + 독립 채점기 대조
// 사용: node scripts/mjtw_harness.mjs [html] [hands=400] [seed=1] [--agent0=greedy|bot]
import fs from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const args = process.argv.slice(2);
const HTML = args.find(a => a.endsWith('.html')) || fileURLToPath(new URL('../public/games/mahjong-tw/index.html', import.meta.url));
const nums = args.filter(a => /^\d+$/.test(a)).map(Number);
const HANDS = nums[0] || 400, SEED0 = nums[1] || 1;
const AGENT0 = (args.find(a => a.startsWith('--agent0=')) || '--agent0=bot').split('=')[1];
const QUIET = args.includes('-q');

function loadEngine(file) {
  const src = fs.readFileSync(file, 'utf8');
  const a = src.indexOf('var MJ=(function(){'), b = src.indexOf('/* === MJ ENGINE v1 end === */');
  if (a < 0 || b < 0) throw new Error('engine block not found');
  const code = src.slice(a, b) + '\n;MJ';
  const ctx = { module: undefined, console };
  vm.createContext(ctx);
  return vm.runInContext(code, ctx);
}
const MJ = loadEngine(HTML);
const ENG0 = (args.find(a => a.startsWith('--eng0=')) || '').split('=')[1];
const MJ0 = ENG0 ? loadEngine(ENG0) : null;
const OTH = (args.find(a => a.startsWith('--others=')) || '').split('=')[1];
const MJO = OTH ? loadEngine(OTH) : null;

/* ───────── 독립 구현: 구조 검사 · 분해 · 채점 ───────── */
const isFl = k => k >= 34, isHon = k => k >= 27 && k < 34, suit = k => k < 9 ? 0 : k < 18 ? 1 : k < 27 ? 2 : 3;
function counts(t) { const c = Array(34).fill(0); for (const x of t) if (x < 34) c[x]++; return c; }
// 모든 분해: 머리 1 + 나머지 전부 面子. (재귀 — 엔진과 다른 순서: 작은 패부터 刻 우선/順 우선 둘 다)
function allDecomp(c) {
  const out = [], tot = c.reduce((a, b) => a + b, 0);
  if (tot % 3 !== 2) return out;
  function rec(c, sets) {
    let i = c.findIndex(v => v > 0);
    if (i < 0) { out.push(sets.slice()); return; }
    if (c[i] >= 3) { c[i] -= 3; sets.push(['P', i]); rec(c, sets); sets.pop(); c[i] += 3; }
    if (i < 27 && (i % 9) <= 6 && c[i + 1] > 0 && c[i + 2] > 0) { c[i]--; c[i + 1]--; c[i + 2]--; sets.push(['C', i]); rec(c, sets); sets.pop(); c[i]++; c[i + 1]++; c[i + 2]++; }
  }
  for (let p = 0; p < 34; p++) if (c[p] >= 2) { const cc = c.slice(); cc[p] -= 2; const before = out.length; rec(cc, []); for (let j = before; j < out.length; j++) out[j] = { pair: p, sets: out[j] }; }
  return out;
}
const complete = tiles => allDecomp(counts(tiles)).length > 0;
function waitsIndep(tiles) { const w = []; for (let t = 0; t < 34; t++) { if (tiles.filter(x => x === t).length >= 4) continue; if (complete(tiles.concat([t]))) w.push(t); } return w; }

function indepScore(S, w, how, from, k) {
  // S: 화료 직전 상태의 스냅샷
  const fl = S.flowers[w], sw = (w - S.dealer + 4) % 4, rw = S.wind;
  const flowerTai = () => { let n = 0, items = []; let z = (fl.includes(34 + sw) ? 1 : 0) + (fl.includes(38 + sw) ? 1 : 0); if (z) items.push(['zhenghua', z]);
    if ([34, 35, 36, 37].every(f => fl.includes(f))) items.push(['huagang', 2]); if ([38, 39, 40, 41].every(f => fl.includes(f))) items.push(['huagang', 2]); return items; };
  const sum = it => it.reduce((a, x) => a + x[1], 0);
  if (how === 'baxian' || how === 'qqy') return 8;
  const hand = S.hands[w].slice(); if (how !== 'tsumo') hand.push(k);
  const ds = allDecomp(counts(hand)); if (!ds.length) return null;
  const melds = S.melds[w];
  const conc = melds.every(m => m.t === 'ak');
  if (how === 'tsumo' && w === S.dealer && S.discN === 0 && !S.called) return 24 + sum(flowerTai());
  if (how === 'tsumo' && w !== S.dealer && S.drawN[w] === 1 && !S.called) return 16 + sum(flowerTai());
  if (how === 'ron' && w !== S.dealer && from === S.dealer && S.discN === 1 && !S.called) return 8 + sum(flowerTai());
  const wt = how === 'tsumo' ? S.lastDraw[w] : k;
  const pre = hand.slice(); pre.splice(pre.indexOf(wt), 1);
  const waits = waitsIndep(pre);
  const allTiles = hand.concat(...melds.map(m => m.t === 'chi' ? [m.k, m.k + 1, m.k + 2] : [m.k, m.k, m.k]));
  const suits = new Set(allTiles.map(suit)); const honor = suits.has(3); const ns = [...suits].filter(s => s < 3).length;
  let best = -1;
  for (const d of ds) {
    // 면자 목록: [kind 'C'|'P', k, concealed?]
    const sets = d.sets.map(([t, x]) => ({ t, x, c: true, own: true })).concat(melds.map(m => ({ t: m.t === 'chi' ? 'C' : 'P', x: m.k, c: m.t === 'ak', own: false })));
    if (how !== 'tsumo') {
      const usedElsewhere = d.sets.some(([t, x]) => t === 'C' && wt >= x && wt <= x + 2) || d.pair === wt;
      if (!usedElsewhere) { const p = sets.find(s => s.own && s.t === 'P' && s.x === wt); if (p) p.c = false; }
    }
    let t = 0, quan = false;
    if (conc && how === 'tsumo') t += 3; else { if (conc) t += 1; if (how === 'tsumo') t += 1; }
    if (melds.length === 5 && melds.every(m => m.t !== 'ak') && how !== 'tsumo') { t += 2; quan = true; }
    const dragons = sets.filter(s => s.t === 'P' && s.x >= 31).length, pD = d.pair >= 31;
    t += dragons === 3 ? 8 : (dragons === 2 && pD) ? 4 : dragons;
    const winds = sets.filter(s => s.t === 'P' && s.x >= 27 && s.x <= 30), pW = d.pair >= 27 && d.pair <= 30;
    if (winds.length === 4) t += 16; else if (winds.length === 3 && pW) t += 8; else { if (winds.some(s => s.x === 27 + rw)) t++; if (winds.some(s => s.x === 27 + sw)) t++; }
    if (ns === 0) t += 16; else if (ns === 1) t += honor ? 4 : 8;
    if (ns > 0 && sets.every(s => s.t === 'P')) t += 4;
    const ak = sets.filter(s => s.t === 'P' && s.c).length; t += ak >= 5 ? 8 : ak === 4 ? 5 : ak === 3 ? 2 : 0;
    if (sets.every(s => s.t === 'C') && !honor && fl.length === 0 && how !== 'tsumo' && waits.length > 1) t += 2;
    if (waits.length === 1 && !quan) t += 1;
    if (how === 'tsumo' && S.wallLen === MJ.LIVE_END) t++;
    if (how === 'ron' && S.wallLen === MJ.LIVE_END) t++;
    if (how === 'tsumo' && S.kanFlag) t++;
    if (how === 'rob') t++;
    t += sum(flowerTai());
    if (t > best) best = t;
  }
  return best;
}

/* ───────── 불변식 ───────── */
const fails = []; const fail = (m, extra) => { fails.push(m); if (fails.length < 25) console.log('FAIL', m, extra ? JSON.stringify(extra).slice(0, 600) : ''); };
function conserve(G, tag) {
  const c = Array(42).fill(0);
  for (const t of G.wall) c[t]++;
  for (let s = 0; s < 4; s++) {
    for (const t of G.hands[s]) c[t]++;
    for (const m of G.melds[s]) { const ts = m.t === 'chi' ? [m.k, m.k + 1, m.k + 2] : (m.t === 'pon' ? [m.k, m.k, m.k] : [m.k, m.k, m.k, m.k]); ts.forEach(x => c[x]++); }
    for (const f of G.flowers[s]) c[f]++;
    for (const d of G.disc[s]) if (!d.taken) c[d.k]++;
  }
  // 方銃 화료면 화료패가 버림패(taken 아님)에 남아 있다 / 搶槓은 손에서 빠져 있다(加槓 중)
  let extra = null;
  if (G.phase === 'end' && G.result && G.result.type === 'win' && G.result.how === 'rob') extra = G.result.k;
  if (G.phase === 'play' && G.claim && G.claim.kind === 'rob') extra = G.claim.k;
  if (extra != null) c[extra]++;
  for (let k = 0; k < 42; k++) { const want = k < 34 ? 4 : 1; if (c[k] !== want) { fail(`${tag}: tile ${k} count ${c[k]} != ${want}`); return false; } }
  // 손패 장수
  if (G.phase === 'play') for (let s = 0; s < 4; s++) {
    const n = G.hands[s].length + 3 * G.melds[s].length;
    const want = (G.step === 'act' && G.turn === s) ? 17 : 16;
    if (G.step === 'claim' && G.claim && G.claim.kind === 'rob' && s === G.claim.from) { if (n !== 16) fail(`${tag}: rob hand size s${s} ${n}`); continue; }
    if (n !== want) { fail(`${tag}: hand size s${s} = ${n} want ${want} step=${G.step} turn=${G.turn}`); return false; }
  }
  return true;
}
function checkClaimOpts(G) {
  const C = G.claim; if (!C) return;
  const s = C.from, k = C.k;
  for (let d = 1; d < 4; d++) {
    const o = (s + d) % 4, op = C.opts[o] || {}, h = G.hands[o];
    const nk = h.filter(x => x === k).length;
    const huOK = (h.length + 1) === 3 * (5 - G.melds[o].length) + 2 && complete(h.concat([k]));
    if (!!op.hu !== huOK) fail(`claim hu mismatch o${o} k${k} engine=${!!op.hu} indep=${huOK}`, { h, melds: G.melds[o] });
    if (C.kind === 'disc') {
      const live = G.wall.length > MJ.LIVE_END;
      if (!!op.pon !== (live && nk >= 2)) fail(`pon mismatch o${o}`);
      if (!!op.kan !== (live && nk >= 3)) fail(`kan mismatch o${o}`);
      const chiWant = [];
      if (live && o === (s + 1) % 4 && k < 27) { const r = k % 9, has = x => h.includes(x);
        if (r >= 2 && has(k - 2) && has(k - 1)) chiWant.push([k - 2, k - 1]); if (r >= 1 && r <= 7 && has(k - 1) && has(k + 1)) chiWant.push([k - 1, k + 1]); if (r <= 6 && has(k + 1) && has(k + 2)) chiWant.push([k + 1, k + 2]); }
      if (JSON.stringify(op.chi || []) !== JSON.stringify(chiWant)) fail(`chi mismatch o${o} k${k}`, { eng: op.chi, want: chiWant });
    } else if (op.pon || op.kan || op.chi) fail('rob claim offered non-hu');
  }
}

/* ───────── 사람 대리(greedy) ───────── */
function greedyAct(G, s) {
  if (MJ.canWin(G, s, null, 'tsumo')) return { a: 'tsumo' };
  const h = G.hands[s], m = 5 - G.melds[s].length, c = MJ.cnt(h);
  let best = null;
  for (const k of [...new Set(h)]) { c[k]--; const sh = MJ.shanten(c, m); c[k]++;
    const iso = isHon(k) ? 2 : (k % 9 === 0 || k % 9 === 8) ? 1 : 0;
    const sc = -sh * 10 + iso; if (!best || sc > best.sc) best = { k, sc }; }
  return { a: 'disc', k: best.k };
}
function greedyClaim(G, o) {
  const C = G.claim, op = C.opts[o]; if (op.hu) return { a: 'hu' };
  const h = G.hands[o], m = 5 - G.melds[o].length, c = MJ.cnt(h), cur = MJ.shanten(c, m), k = C.k;
  const after = rem => { for (const t of rem) c[t]--; let b = 99; for (let t = 0; t < 34; t++) { if (!c[t]) continue; c[t]--; b = Math.min(b, MJ.shanten(c, m - 1)); c[t]++; } for (const t of rem) c[t]++; return b; };
  if (op.pon && after([k, k]) < cur) return { a: 'pon' };
  if (op.chi) for (const v of op.chi) if (after(v) < cur) return { a: 'chi', v };
  return { a: 'pass' };
}
const agentAct = (G, s) => (s === 0 && AGENT0 === 'greedy') ? greedyAct(G, s) : (s === 0 && MJ0) ? MJ0.botAct(G, s) : (s !== 0 && MJO) ? MJO.botAct(G, s) : MJ.botAct(G, s);
const agentClaim = (G, o) => (o === 0 && AGENT0 === 'greedy') ? greedyClaim(G, o) : (o === 0 && MJ0) ? MJ0.botClaim(G, o) : (o !== 0 && MJO) ? MJO.botClaim(G, o) : MJ.botClaim(G, o);

/* ───────── 진행 ───────── */
const R = MJ.rng(SEED0 * 7919 + 13);
const seed = () => (R() * 4294967296) >>> 0;
const stat = { hands: 0, wins: [0, 0, 0, 0], draws: 0, how: {}, items: {}, dealIn: [0, 0, 0, 0], pts: [0, 0, 0, 0], tai: 0, taiN: 0, claims: { chi: 0, pon: 0, kan: 0, hu: 0 }, silly: 0, discards: 0, sillyBot: 0 };
let G = null, steps = 0, games = 0;
const snap = G => ({ hands: MJ.clone(G.hands), melds: MJ.clone(G.melds), flowers: MJ.clone(G.flowers), dealer: G.dealer, wind: G.wind, discN: G.discN, drawN: G.drawN.slice(), called: G.called, lastDraw: G.lastDraw.slice(), kanFlag: G.kanFlag, wallLen: G.wall.length });

function newGame() { games++; G = MJ.newGame({ rounds: 4, base: 300, tai: 100 }, [{ ctrl: 'me' }, {}, {}, {}], Math.floor(R() * 4)); MJ.startHand(G, seed()); conserve(G, 'deal'); if (G.phase === 'end') onWin(snap(G)); }
function onWin(pre) {
  const r = G.result; if (!r) return;
  if (r.type === 'draw') { stat.draws++; return; }
  stat.wins[r.w]++; stat.how[r.how] = (stat.how[r.how] || 0) + 1;
  if (r.how === 'ron' || r.how === 'rob' || r.how === 'qqy') stat.dealIn[r.from]++;
  for (const it of r.items) stat.items[it.key] = (stat.items[it.key] || 0) + 1;
  stat.tai += r.tai; stat.taiN++;
  // 구조 검사
  if (r.how !== 'baxian' && r.how !== 'qqy') {
    const h = r.hands[r.w].slice(); if (r.how === 'ron' || r.how === 'rob') h.push(r.k);
    if (h.length !== 3 * (5 - r.melds[r.w].length) + 2) fail('win size', { h, m: r.melds[r.w] });
    if (!complete(h)) fail('win structure invalid', { h });
  } else {
    if (r.how === 'baxian' && r.flowers[r.w].length !== 8) fail('baxian without 8 flowers');
    if (r.how === 'qqy' && r.flowers[r.w].length !== 7) fail('qqy without 7');
  }
  // 독립 채점
  const it = indepScore(pre, r.w, r.how, r.from, r.k);
  if (it !== r.tai) fail(`tai mismatch engine=${r.tai} indep=${it} how=${r.how}`, { items: r.items, hand: pre.hands[r.w], melds: pre.melds[r.w], fl: pre.flowers[r.w], k: r.k });
  // 지불 검사: 합 0, 莊 台
  const sumP = r.pays.reduce((a, b) => a + b, 0); if (sumP !== 0) fail('pays not zero-sum');
  const dt = 1 + 2 * r.lian;
  for (const p in r.per) { const want = 300 + 100 * (r.tai + ((+p === r.dealer || r.w === r.dealer) ? dt : 0)); if (r.per[p].amt !== want) fail('pay amount', { p, per: r.per[p], want }); }
}
newGame();
let preSnap = null;
const T0 = Date.now();
while (stat.hands < HANDS) {
  if (++steps > 5e6) { fail('runaway'); break; }
  if (G.phase === 'over') { newGame(); continue; }
  if (G.phase === 'end') {
    stat.hands++; for (let s = 0; s < 4; s++) stat.pts[s] += G.result.pays[s];
    if (G.result.type === 'draw') { if (G.wall.length !== MJ.LIVE_END) fail('draw with wall ' + G.wall.length); }
    const ev = MJ.nextHand(G, seed()); if (G.phase === 'play') conserve(G, 'next'); else if (G.phase === 'end') onWin(snap(G)); continue;
  }
  if (G.step === 'draw') { preSnap = snap(G); const ev = MJ.draw(G); if (G.phase === 'end') { onWin(preSnap); conserve(G, 'drawEnd'); } else conserve(G, 'draw'); continue; }
  if (G.step === 'act') {
    const s = G.turn; const a = agentAct(G, s); preSnap = snap(G);
    // '바보 같은 버림' 측정: 이미 聽牌였는데 버린 뒤 聽牌가 깨짐(다른 선택지로 聽 유지 가능했는데)
    if (a.a === 'disc') {
      stat.discards++;
      const h = G.hands[s], m = 5 - G.melds[s].length, c = MJ.cnt(h);
      let bestSh = 99; for (const k of new Set(h)) { c[k]--; bestSh = Math.min(bestSh, MJ.shanten(c, m)); c[k]++; }
      c[a.k]--; const sh = MJ.shanten(c, m); c[a.k]++;
      if (sh > bestSh + 1) { stat.silly++; if (s !== 0 || AGENT0 === 'bot') stat.sillyBot++; }
    }
    let ev = a.a === 'tsumo' ? MJ.tsumo(G, s) : a.a === 'kan' ? MJ.kan(G, s, a.k) : MJ.discard(G, s, a.k);
    if (!ev) { fail('agent illegal act', a); ev = MJ.discard(G, s, G.hands[s][0]); }
    if (ev && ev.k === 'call' && (ev.a === 'tsumo')) stat.claims.hu++;
    if (G.step === 'claim') checkClaimOpts(G);
    if (G.phase === 'end') onWin(preSnap); else conserve(G, 'act');
    continue;
  }
  if (G.step === 'claim') {
    const C = G.claim; preSnap = snap(G); let ev = null;
    for (const o of Object.keys(C.opts).map(Number)) { if (!G.claim || G.claim !== C) break; const ch = agentClaim(G, o); ev = MJ.respond(G, o, ch) || ev; }
    if (G.claim === C) ev = MJ.tryResolve(G, true);
    if (ev && ev.k === 'call') stat.claims[ev.a] = (stat.claims[ev.a] || 0) + 1;
    if (G.phase === 'end') onWin(preSnap); else conserve(G, 'claim');
    if (G.step === 'claim') checkClaimOpts(G);
    continue;
  }
  fail('stuck step ' + G.step); break;
}
const pct = x => (100 * x / stat.hands).toFixed(1) + '%';
const out = {
  agent0: AGENT0, seed: SEED0, hands: stat.hands, games, ms: Date.now() - T0,
  winRate: stat.wins.map(pct), draws: pct(stat.draws), dealIn: stat.dealIn.map(pct), avgPts: stat.pts.map(p => Math.round(p / stat.hands)),
  avgTai: (stat.tai / Math.max(1, stat.taiN)).toFixed(2), how: stat.how, claims: stat.claims,
  sillyDiscards: stat.silly + '/' + stat.discards, items: stat.items, fails: fails.length
};
console.log(JSON.stringify(out, null, QUIET ? 0 : 1));
process.exitCode = fails.length ? 1 : 0;
