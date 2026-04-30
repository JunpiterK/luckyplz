# 🟦 Tetris BGM — 3-tier 동적 음악

다른 게임과 달리 **lpBgm.js 안 쓰고 자체 오디오 엔진** 사용. 이유: 스택
높이에 따라 3개 트랙을 동적으로 전환해야 하는데, lpBgm 의 랜덤 셔플
모델로는 이걸 표현할 수 없음. SKIP_GAMES 에 `tetris` 포함됨.

## 트랙 단계 (자동 전환)

| 단계 | 트랙 | 트리거 (topRow 기준) | 스택 높이 | 화면 비율 | 분위기 |
|---|---|---|---|---|---|
| **차분** | `track1.mp3` | topRow ≥ 11 | 0~9 행 | ≤ 45% | 게임 시작 ~ 중반 전 |
| **긴장** | `track2.mp3` | topRow 6~10 | 10~14 행 | 50~70% | 절반 넘는 위험 영역 |
| **위급** | `track3.mp3` | topRow ≤ 5 | 15~20 행 | ≥ 75% | 천장 임박, 한 수가 생사 |

`topRow` = 가장 위에 채워진 행 인덱스 (0=맨 위, 빈 보드 = 20).

## 히스테리시스 (음악 깜빡임 방지)

상위 단계로 올라가는 임계: 위 표 그대로
하위 단계로 내려가는 임계: **+2 행 갭**

  - track2 → track1 복귀: topRow ≥ 12 (11 아님)
  - track3 → track2 복귀: topRow ≥ 7  (6 아님)

라인 클리어로 한 행만 빠져 경계 살짝 넘었을 때 음악이 곧바로 안 바뀜.

## 크로스페이드

트랙 전환 시 800ms 동안:
  - 이전 트랙: 0.35 → 0 페이드 아웃 후 pause
  - 다음 트랙: 0 → 0.35 페이드 인

같은 max volume (0.35) 으로 트랙 간 음량 매칭. SFX (피스 락·라인
클리어) 보다 작아서 게임 사운드 가려지지 않음.

## Suno 프롬프트 (3개 단계용)

### track1 — 차분 (Calm)
```
calm 8-bit chiptune for the early phase of a tetris game, 100-110 BPM,
gentle square melody, walking triangle bass, sparse percussion, NES-era
nostalgic vibe, focused but relaxed mood, Russian folk influence
(Korobeiniki style), instrumental, loopable, no vocals
```

### track2 — 긴장 (Tense)
```
tense 8-bit chiptune for mid-game tetris with stack getting high,
130-140 BPM, urgent square arpeggio, driving triangle bass, snappy hi-
hat, retro arcade pressure mood, slightly minor key, building
intensity, instrumental, loopable, no vocals
```

### track3 — 위급 (Critical)
```
intense fast-paced 8-bit chiptune for danger-zone tetris play, 160-180
BPM, rapid sixteenth-note square lead, pounding triangle bass, busy
chip drums, dissonant minor chords, frantic arcade game-over warning
vibe, instrumental, loopable, no vocals
```

## 트랙 배치

```
public/assets/bgm/tetris/
├── track1.mp3   ← 차분 (게임 시작부터 ~ 절반 차기 전)
├── track2.mp3   ← 긴장 (절반 ~ 3/4)
└── track3.mp3   ← 위급 (3/4 이상, 천장 임박)
```

`track4.mp3` 는 사용 안 함 (3-tier 시스템). 누락된 트랙은 silently
skip 되고 다른 트랙은 정상 재생.

## 길이·정규화

| 항목 | 권장값 |
|---|---|
| 길이 | 60~90초 (한 게임에 여러 번 루프) |
| 비트레이트 | 128 kbps mp3 |
| 정규화 | -14 LUFS (다른 게임과 통일) |
| 페이드 | 첫/끝 페이드 없이 순수 루프 (엔진이 800ms 크로스페이드 처리) |

## 라이프사이클

| 게임 이벤트 | BGM 동작 |
|---|---|
| `startGame()` | track1 부터 페이드 인 |
| 피스 lock | board.update(board) 호출 → tier 재평가 |
| 라인 클리어 | 라인 빠진 후 board.update(board) → 차분한 음악으로 복귀 가능 |
| 일시정지 | 모든 트랙 pause |
| 재개 | currentTier 트랙만 재생 |
| 게임 오버 | 모든 트랙 즉시 stop (gameOver SFX 방해받지 않게) |

## Exclude

```
vocals, lyrics, slow ballad, ambient drone, sad mood, jazz, lo-fi,
swing, country, ballad
```

## 디버그

콘솔에서 `TetrisBGM._state()` 호출 시 현재 tier·started·enabled 반환.
