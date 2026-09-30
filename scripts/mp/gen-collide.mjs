/* 같은 방 코드를 내는 방장 키 2벌을 생일 공격으로 찾는다(30^6 공간 → 평균 ~3.4만 쌍) — C1 충돌 검사·C3 이중 응답 시험용.
   node scripts/mp/gen-collide.mjs  → fixtures/collide.json (테스트 전용 키 — 운영에 쓰지 말 것) */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadFair } from './fairlib.mjs';
const F = loadFair(), t = F._t, S = crypto.subtle;
const HERE = path.dirname(fileURLToPath(import.meta.url));
const seen = new Map();
let n = 0; const t0 = Date.now();
async function pair() {
  const s = await S.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
  const d = await S.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits', 'deriveKey']);
  const rpk = { sig: t.b64u(new Uint8Array(await S.exportKey('raw', s.publicKey))), dh: t.b64u(new Uint8Array(await S.exportKey('raw', d.publicKey))) };
  return { s, d, rpk, code: t.codeOfF(t.roomF(rpk)) };
}
for (;;) {
  const batch = await Promise.all(Array.from({ length: 64 }, pair)); n += 64;
  for (const k of batch) {
    if (!/[A-Z]/.test(k.code)) continue;
    const prev = seen.get(k.code);
    if (prev && prev.rpk.sig !== k.rpk.sig) {
      const jw = async x => ({ sig: await S.exportKey('jwk', x.s.privateKey), dh: await S.exportKey('jwk', x.d.privateKey), rpk: x.rpk });
      const out = { code: k.code, a: await jw(prev), b: await jw(k), tries: n, note: 'TEST ONLY — colliding room keys for harness C1/C3' };
      fs.mkdirSync(path.join(HERE, 'fixtures'), { recursive: true });
      fs.writeFileSync(path.join(HERE, 'fixtures', 'collide.json'), JSON.stringify(out, null, 1));
      console.log('collision', k.code, 'after', n, 'keys', ((Date.now() - t0) / 1000).toFixed(1) + 's');
      process.exit(0);
    }
    seen.set(k.code, k);
  }
  if (n % 6400 === 0) console.log(n, 'keys', ((Date.now() - t0) / 1000).toFixed(1) + 's');
}
