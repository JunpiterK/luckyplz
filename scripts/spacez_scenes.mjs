#!/usr/bin/env node
/* =====================================================================
   Space-Z 장면 검수 시트 (MP8c, 2026-10-09)
   31존 × 3시점(진입 +2초 · 중간 · 끝 −2초)을 찍어 존별 한 줄 시트 HTML 을 만든다(GL 끔·켬 두 벌).
   본체는 scripts/spacez_gate.mjs 의 `scenes` 명령(gate:mp8c 펜스) — 게이트 하네스(합성 시계·G.begin·szWarpTo·Edge·서버·정리)를 그대로 쓴다.
   이 스크립트는 그 명령을 scripts/gate_locked.mjs 로 부른다 → 게이트 순번 잠금(_gatelock)을 지키고, 헤드리스 Edge 는 한 번에 1개.

   사용:
     node scripts/spacez_scenes.mjs [--size 412x915] [--dsf 2] [--lang ko] [--gl both|0|1] [--zones 0,5,19] [--warp]
                                    [--out <dir>] [--root <체크아웃>] [--port 9860] [--prof-prefix edgeprof_scenes] [--q '<추가 쿼리>'] [--norows]
     예) 기본(ko·412x915 DPR2·GL 끔/켬 두 벌)     node scripts/spacez_scenes.mjs
         작은 폰·영어·GL 끔만                      node scripts/spacez_scenes.mjs --size 320x568 --lang en --gl 0
   출력: <out>/<lang>_<w>x<h>/sheet_gl0.html · sheet_gl1.html (시트), gl0|gl1/zNN_{a,b,c}.jpg (원본 컷), rows_glN/zNN.png (존 한 줄 PNG), scenes.json
   기본 out = C:/code/python/luckyplz_wt/_scenes_out
   GL 켬 벌은 MP8b(WebGL 배경층)가 병합된 뒤에만 의미가 있다 — 시트 머리에 'GL 실제 켜짐' 여부가 찍힌다.
   ===================================================================== */
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const O = {};
for(let i = 0; i < argv.length; i++){
    const a = argv[i];
    if(!a.startsWith('--')) continue;
    const k = a.slice(2), nx = argv[i + 1];
    if(nx == null || nx.startsWith('--')) O[k] = true; else { O[k] = nx; i++; }
}
if(O.help || O.h){ console.log('node scripts/spacez_scenes.mjs [--size 412x915] [--dsf 2] [--lang ko] [--gl both|0|1] [--zones a,b] [--warp] [--out dir] [--root dir] [--port n] [--norows]'); process.exit(0); }
const root = path.resolve(O.root || path.join(here, '..'));
const args = ['scenes', '--root', root, '--port', String(O.port || 9860), '--jobs', '1',
    '--prof-prefix', String(O['prof-prefix'] || 'edgeprof_scenes'),
    '--out', path.resolve(O.out || 'C:/code/python/luckyplz_wt/_scenes_out'),
    '--sc-size', String(O.size || '412x915'), '--sc-dsf', String(O.dsf || 2), '--sc-lang', String(O.lang || 'ko'), '--sc-gl', String(O.gl == null ? 'both' : O.gl)];
if(O.zones) args.push('--sc-zones', String(O.zones));
if(O.warp) args.push('--sc-warp');
if(O.norows) args.push('--sc-norows');
if(O.q) args.push('--sc-q', String(O.q));
if(O.seed) args.push('--sc-seed', String(O.seed));
if(O.json) args.push('--json', String(O.json));
if(O.verbose) args.push('--verbose');
console.log('[scenes] gate_locked.mjs ' + args.join(' '));
const child = spawn(process.execPath, [path.join(here, 'gate_locked.mjs'), ...args], { stdio: 'inherit' });
for(const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => { try{ child.kill(sig); }catch(_){} });
child.on('exit', (code) => process.exit(code == null ? 1 : code));
