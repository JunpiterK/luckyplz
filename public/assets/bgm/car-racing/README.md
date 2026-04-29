# 🏎️ Car Racing BGM

탑다운 레이싱. 신나면서 가슴 뛰는 전속력 질주.

## 게임 스타일 메모

- 탑다운 2D 레이싱, 최대 4명 멀티플레이
- 코스: 오벌 / 인피니티 figure-8 등
- 아이템: 부스트, 미사일, 아이템박스
- 위험: 물·얼음·진흙·언덕
- 100초 레이스 기본, 충돌 3회까지
- 게임 페이즈에 따라 페이드 인/아웃 (GO! 와 함께 빌드업)

다른 게임들이 차분·집중형 chiptune 위주라면, car-racing은 **톤이 한 단계 위** —
질주감·흥분감·흥미진진. 4가지 다른 장르로 4 트랙 생성해서 레이스마다 분위기
바뀌게 하는 걸 추천.

## Suno 프롬프트

### 옵션 A — 8-bit Race Anthem (정통 칩튠)
```
high-energy 8-bit chiptune racing anthem, 160 BPM, triumphant square
melody with rapid sixteenth-note runs, driving triangle bass on downbeats,
snappy chip percussion, F-Zero NES style heroic vibe, intense and uplifting,
instrumental, loopable, no vocals
```

### 옵션 B — Retro Synthwave Cruise (80s 네온)
```
exciting retro synthwave, 140 BPM, gated reverb drums, soaring saw-wave
lead melody, pulsing analog bass, neon-night highway vibe like Outrun
arcade, wide stereo, cinematic and thrilling, instrumental, loopable,
no vocals
```

### 옵션 C — Eurobeat Race Pump (Initial D 스타일)
```
pumping eurobeat racing music, 165 BPM, four-on-the-floor kick, rapid
arpeggiated synth riff, fast hi-hat shuffle, anthemic stab chords, Italo
disco influence, Initial D vibe, super energetic and tense, instrumental,
loopable, no vocals
```

### 옵션 D — Chip-Rock Hybrid (칩튠 + 록)
```
exciting 8-bit chiptune fused with electric rock guitar, 155 BPM, chunky
square lead doubled by distorted guitar, driving triangle bass, live drum
kit pattern, Daytona USA arcade rock vibe, heroic and pumped-up,
instrumental, loopable, no vocals
```

## 트랙 배치

```
public/assets/bgm/car-racing/
├── track1.mp3   ← 옵션 A (정통 칩튠 — 안정적 기본)
├── track2.mp3   ← 옵션 B (synthwave — 야간 코스 분위기)
├── track3.mp3   ← 옵션 C (eurobeat — 가장 격렬)
└── track4.mp3   ← 옵션 D (chip-rock — 칩튠과 친숙하면서 더 강렬)
```

## ⚠ 다중 트랙 사용 시 주의

car-racing 의 오디오 엔진은 현재 **단일 트랙 루프** 구조 (`bgmAudio = new Audio(...)`).
그래서 지금 상태로 track1.mp3 만 재생되고 track2~4 는 무시됨.

4 트랙을 다 활용하려면 두 가지 옵션:

1. **수동 교체** — 그냥 track1.mp3 자리에 원하는 곡 1개를 두고 정기적으로
   교체. 가장 간단.
2. **dodge 패턴 차용** — dodge처럼 `TRACKS = ['/assets/bgm/car-racing/track1.mp3',
   ..., 'track4.mp3']` 배열로 큐잉. `ended` 이벤트에서 다음 인덱스 재생.
   페이드 인/아웃 로직은 그대로 보존 가능.

향후 4 트랙 활용 원하면 옵션 2로 확장 의뢰해줘 (~30줄 변경).

## Exclude

```
vocals, lyrics, slow tempo, ambient, lo-fi, ballad, sad mood, minor key brooding
```

## 길이·정규화

| 항목 | 권장값 |
|---|---|
| 길이 | 75~90초 (레이스 100초보다 약간 짧게 → 한 레이스에 1.0~1.3 루프) |
| 비트레이트 | 128 kbps mp3 |
| 정규화 | -14 LUFS (다른 게임과 통일). 자체 엔진이 0.5 곱해서 추가 -6dB 차감 |
| 페이드 | 첫/끝 모두 페이드 없이 순수 루프 (게임 엔진이 페이드 처리) |

## Suno 사용 팁

- "instrumental" 와 "no vocals" 둘 다 포함해야 보컬 안 끼어듦
- "loopable" 키워드로 매끄러운 루프 가능성 ↑ (그래도 끝부분 트리밍 권장)
- BPM 명시 → tempo 일관성. 장르 키워드만으로는 자꾸 다른 BPM 나옴
- 생성 후 첫 박과 끝 박이 매칭 안 되면 Audacity 로 트림
