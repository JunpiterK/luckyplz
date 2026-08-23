# 델타-브이 — 실시간 3D 빌드

## 왜 번들러를 쓰나

사이트 원칙은 "빌드·번들러 없음" 이고 그대로 유지된다 — **프로덕션은 여전히
정적 파일만 서빙한다.** 번들은 여기서 로컬로 만들어 `public/js/deltav-bundle.js`
로 **커밋**한다. Cloudflare Pages 는 빌드하지 않는다.

Babylon 전체 UMD 는 8.2MB(gzip 1.8MB)라 라이브에 못 올린다.
필요한 모듈만 트리셰이킹하면 **3.4MB / gzip 840KB** 로 줄어든다.

## 빌드

```
cd scripts/game
npm install
npm run build
```

산출물 `public/js/deltav-bundle.js` 를 **반드시 함께 커밋**한다.

## 에셋

3D 모델의 단일 원본은 여전히 Blender 다. `scripts/blender/*.py` 로 씬을 만들고
`export_gltf.py` 로 `public/assets/deltav/*.glb` 를 내보낸다.
프리렌더 PNG 는 문서고·메일 삽화용으로 남고, 현장은 실시간 3D 로 간다.

## 파일명에 점을 넣지 말 것

`scripts/bump-cache.sh` 의 캐시 버스팅 정규식은 `/js/[a-zA-Z0-9_-]+\.js` 다 —
**파일명 안의 점을 잡지 못한다.** `deltav.bundle.js` 로 뒀더니 이 번들만
`?v=` 재작성에서 조용히 빠졌다(2026-08-23). 그래서 `deltav-bundle.js` 다.
새 번들을 추가할 때도 하이픈만 쓴다.
