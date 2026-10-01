import fs from 'node:fs';
const src = fs.readFileSync('public/games/ladder/index.html', 'utf8');
const a = src.indexOf('    outcome(p,rng){');
const b = src.indexOf('    resText(p,r)', a);
const body = src.slice(a, b).trim().replace(/,\s*$/, '');
const AV = 600;
const G = eval('({' + body + '})');
const rng = {
  int: n => Math.floor(Math.random() * n),
  shuffle(arr) { for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]]; } return arr; }
};
for (const n of [2, 3, 6, 12]) {
  for (const v of [0, 2]) {
    const T = 20000, cnt = Array.from({ length: n }, () => new Array(n).fill(0));
    for (let t = 0; t < T; t++) {
      const p = { n, names: Array.from({ length: n }, (_, i) => 'p' + i), results: Array.from({ length: n }, (_, i) => 'r' + i), cx: 'high', mode: 'seq' };
      if (v) p.v = v;
      const r = G.outcome(p, rng);
      for (let i = 0; i < n; i++) { const col = r.m[i]; const ri = r.q ? r.q[col] : col; cnt[i][ri]++; }
    }
    let maxDev = 0; for (const row of cnt) for (const c of row) maxDev = Math.max(maxDev, Math.abs(c / T - 1 / n));
    console.log(`n=${n} v=${v || 1}  P(p0→r0)=${(cnt[0][0] / T).toFixed(3)}  ideal=${(1 / n).toFixed(3)}  maxDev=${maxDev.toFixed(3)}`);
  }
}
