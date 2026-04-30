# 🟦 Tetris BGM

고전 블록 게임. 긴장 + 집중 + 점진적 빌드업.

## Suno 프롬프트

### 옵션 A — 정통 칩튠 (Korobeiniki 영감)
```
classic 8-bit chiptune for tetris-style block-stacking arcade game,
130 BPM, mid-tempo, square lead with rapid stepwise melody, walking
triangle bass, hi-hat shuffle, NES-era vibe, mildly Russian folk
influence, focused gameplay mood, instrumental, loopable, no vocals
```

### 옵션 B — 긴장감 점진적 빌드업
```
8-bit chiptune that slowly intensifies, 120 BPM at start ramping to
150 BPM by 60 seconds, sparse square arpeggio building to fast
sixteenth-note runs, kick + hi-hat pattern adding layers, cathartic
chord progression, retro arcade tense vibe, instrumental, loopable,
no vocals
```

### 옵션 C — 신스웨이브 풀러
```
melancholic synthwave puzzle music, 110 BPM, gated reverb drums,
sustained warm pad, plucky synth lead with arpeggiated motif, retro
80s computer game vibe, focused but emotional, instrumental,
loopable, no vocals
```

### 옵션 D — 빠른 액션 변주
```
fast-paced 8-bit chiptune for high-level tetris play, 160 BPM,
driving square lead, energetic triangle bass, snappy chip drums,
arcade tension, intense focus mood, instrumental, loopable, no
vocals
```

## 트랙 배치

```
public/assets/bgm/tetris/
├── track1.mp3   ← 옵션 A (정통, 안정적 기본)
├── track2.mp3   ← 옵션 B (빌드업, 긴장)
├── track3.mp3   ← 옵션 C (신스웨이브, 차분)
└── track4.mp3   ← 옵션 D (빠른 변주, 후반 긴박)
```

lpBgm.js 가 4개 트랙 중 랜덤으로 셔플 재생. 빈 폴더면 BGM 없이 게임 동작.

## 길이·정규화

| 항목 | 권장값 |
|---|---|
| 길이 | 60~90초 (한 게임 길어지면 2~3 루프) |
| 비트레이트 | 128 kbps mp3 |
| 정규화 | -14 LUFS (다른 게임과 통일). lpBgm 이 0.3 곱해서 추가 -10dB 차감 |
| 페이드 | 첫/끝 페이드 없이 순수 루프 |

## Exclude

```
vocals, lyrics, slow ballad, ambient drone, sad mood, jazz, lo-fi
```
