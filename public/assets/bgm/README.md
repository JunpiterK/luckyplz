# Lucky Please — Game BGM Folders

각 게임 폴더에 1~4개의 mp3 파일을 넣으면 [public/js/lpBgm.js](../../js/lpBgm.js)가 자동으로 인식해서 랜덤 셔플 재생합니다.

## 파일 컨벤션

```
public/assets/bgm/<game>/
├── track1.mp3   ← 필수 (1개라도 있으면 됨)
├── track2.mp3   ← 선택
├── track3.mp3   ← 선택
└── track4.mp3   ← 선택
```

- 파일명은 `track1.mp3` ~ `track4.mp3` 고정. 그 이상은 인식 안 함 (`MAX_TRACKS=4` 상수).
- 파일이 없으면 lpBgm.js가 콘솔에 로그만 남기고 BGM 없이 동작.
- **car-racing / dodge** 는 자체 오디오 엔진이 있어 **lpBgm 자동 재생은 스킵**
  (게임 페이즈에 묶인 페이드 인/아웃·일시정지·플레이리스트 큐 등을 직접 제어).
  단 mp3 **파일 저장 위치는 동일 컨벤션** 따름 — 자체 엔진이
  `/assets/bgm/<game>/track*.mp3` 경로를 `new Audio()` 로 직접 로드.
  → 디렉터리 트리 100% 대칭, Cloudflare `/assets/*` 캐시 규칙 (1d) 일관 적용.

## 권장 mp3 사양

| 항목 | 권장값 |
|---|---|
| 길이 | 60~90초 (loop 가능하도록 첫 박/끝 박 매칭) |
| 비트레이트 | 128 kbps mp3 (~1MB / 60초) |
| 정규화 | -14 LUFS (Spotify/YouTube 표준). lpBgm이 0.3 곱해서 -10dB SFX 차감 자동 적용 |
| 채널 | 모노 또는 스테레오 둘 다 OK |
| 페이드 | 첫/끝 페이드 없이 순수 루프 (lpBgm가 트랙 사이 끊김 처리) |

## 동작 방식

1. 게임 페이지 진입 시 lpBgm.js 자동 로드 (siteFooter.js가 inject)
2. 사용자 첫 터치/클릭/키 입력 시 BGM 시작 (브라우저 autoplay 정책)
3. HEAD 요청으로 `track1.mp3` ~ `track4.mp3` 존재 여부 probe
4. 존재하는 트랙 중 랜덤 1개 재생 → 끝나면 다른 랜덤 트랙 (직전과 중복 X)
5. 페이지 unload 또는 사용자가 mute 토글하면 정지
6. tab hide 시 일시정지, 복귀 시 재개

## 볼륨

기본값: `0.3` (≈ 1.0 SFX 대비 −10dB)

게임 페이지에서 직접 조절 가능:
```js
LpBgm.setVolume(0.2);   // 더 작게
LpBgm.setMuted(true);   // 음소거
LpBgm.toggle();         // mute 토글 (반환값 = 새 muted 상태)
```

## 게임별 음소거 버튼 연동 (선택)

각 게임에 이미 "🔊 BGM ON/OFF" 버튼이 있다면:
```js
soundToggleBtn.addEventListener('click', function(){
  const muted = LpBgm.toggle();
  this.textContent = muted ? '🔇 BGM OFF' : '🔊 BGM ON';
});
```
mute 상태는 `localStorage.lp_bgm_muted`에 저장되어 모든 게임에 공유됩니다.

## Suno 프롬프트

각 게임 폴더의 `README.md`에 8-bit chiptune 컨셉 프롬프트가 있어요.

## 라이선스 주의

AdSense 광고가 있는 사이트에 BGM 게재 시:
- Suno 무료 플랜은 비상업 사용만 → **Pro 플랜 이상** ($10/월) 가입 필수
- 다른 출처 (e.g., royalty-free) 사용 시 라이선스 확인
- 트랙 메타데이터에 attribution 필요한 경우 게임 페이지 푸터에 명시
