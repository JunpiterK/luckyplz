# Auto Daily Post Pipeline

**4슬롯 × 24시간** 데일리 시장 리캡 자동 발행 시스템.

---

## 1. 슬롯 시간표 (KST)

| Slot | KST | UTC cron | 다루는 거래일 | 슬러그 prefix |
|------|-----|----------|--------------|---------------|
| ① **us-close** | 06:00 | `0 21 * * *` | 전날 US ET 종가 | `us-tech-recap-YYYY-MM-DD` |
| ② **kr-open** | 07:30 | `30 22 * * *` | 오늘 KR 개장 | `kr-open-brief-YYYY-MM-DD` |
| ③ **kr-close** | 15:45 | `45 6 * * *` | 오늘 KR 종가 | `kr-tech-recap-YYYY-MM-DD` |
| ④ **us-premarket** | 21:30 | `30 12 * * *` | 오늘 밤 US 세션 | `us-premarket-YYYY-MM-DD` |

UTC cron 은 GitHub Actions 시간 기준. 한국 KST = UTC+9.

---

## 2. 동작 흐름

```
GitHub Actions cron
        ↓
auto-daily-post.py --slot <slot>
        ↓
scripts/prompts/<slot>.md  ←  슬롯별 지시 prompt
        ↓
Anthropic Claude API + web_search (max 12 calls)
        ↓
JSON 응답 (strict schema)
        ↓
HTML 렌더 (ko + en, daily-base.html)
        ↓
OG PNG 생성 (gen_daily_og.py + Pillow)
        ↓
posts.js + sitemap.xml 자동 갱신
        ↓
bump-cache.sh
        ↓
git add + commit + push
        ↓
Cloudflare Pages 자동 배포
```

---

## 3. 초기 셋업 (한 번만)

### (1) Anthropic API Key 발급
- https://console.anthropic.com/ 가입 → API Keys → "Create Key"
- 월 결제 한도 설정 권장 (e.g., $20-50/월)
- 비용 추정: 슬롯당 약 $0.05-0.15 (Claude Sonnet + web_search). 하루 4슬롯 × 30일 = **월 $6-18**

### (2) GitHub Secret 등록
```
Settings → Secrets and variables → Actions → New repository secret
Name:  ANTHROPIC_API_KEY
Value: sk-ant-…
```

### (3) 워크플로 활성화
- `.github/workflows/daily-cron.yml` 푸시 후 → GitHub Actions 탭에서 활성화 확인
- **첫 테스트**: workflow_dispatch → slot=`us-close`, date=오늘 → 수동 실행

### (4) 로컬 테스트 (선택)
```powershell
# 환경 준비
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-…"

# Dry-run (git push 없이)
python scripts/auto-daily-post.py --slot us-close --dry-run

# 실제 push까지
$env:LP_GIT_PUSH = "1"
python scripts/auto-daily-post.py --slot us-close
```

---

## 4. 슬롯 prompt 커스터마이징

각 슬롯 prompt 는 `scripts/prompts/<slot>.md` 에 있다. 수정 시:

1. **Output JSON schema 는 절대 깨지 않게**. 키 추가는 OK, 키 삭제는 `auto-daily-post.py` 함께 수정.
2. **Style / Tone 섹션 자유 수정**. 톤 바꾸고 싶으면 여기서.
3. **Required actions** 가 web_search 검색 강도를 결정. 너무 많이 시키면 API 비용 ↑.

Prompt 수정 후 git push → 다음 cron 부터 적용.

---

## 5. 수동 실행 / 재실행

GitHub Actions 페이지에서:
1. **Actions → Daily Market Posts → Run workflow**
2. `slot`: 단일 슬롯 (`us-close`) 또는 `all` (4슬롯 순차)
3. `date`: YYYY-MM-DD 로 특정 날짜 발행 (백필 가능)

CLI 한 줄로도 가능:
```bash
gh workflow run "Daily Market Posts (4 slots)" -f slot=us-close -f date=2026-05-12
```

---

## 6. 실패 시 대처

### 케이스 A — Claude JSON parse 실패
- 로그에서 `Could not parse Claude output as JSON` 확인.
- 원인: web_search 결과가 너무 길어 `max_tokens` 초과, 또는 Claude 가 markdown 으로 응답.
- 대응: prompt 끝에 `"Reply with ONLY the JSON object. No prose. No code fences."` 강조.

### 케이스 B — git push 충돌
- 같은 시각에 다른 슬롯이 동시 푸시 → 충돌.
- 대응: `daily-cron.yml` 의 cron 간격을 5분 이상 띄움 (이미 그렇게 되어있음).

### 케이스 C — 한국/미국 공휴일
- Prompt 가 `{"skip": true, "reason": "..."}` 반환 → 글 생성 안 함.
- 빈 글 생성을 방지.

### 케이스 D — Anthropic 한도 초과
- API 키의 월 한도 초과 → 빌드 실패.
- Console 에서 한도 조정 + Action 수동 재실행.

---

## 7. 로컬 개발 팁

### prompt 한 줄 단위 테스트
```bash
# 특정 슬롯만 빠르게 테스트
python scripts/auto-daily-post.py --slot us-close --date 2026-05-12 --dry-run
```

### Claude 응답 디버깅
`auto-daily-post.py::call_claude()` 에서 raw response 를 `tmp/last-claude-response.json` 으로 저장하도록 임시 추가하면 편하다.

### OG 이미지 미리보기
```bash
# JSON 파일 만들어두고 OG 만 따로 생성
python -c "
from scripts.gen_daily_og import make_og
from pathlib import Path
make_og(Path('tmp/og-test.png'), lang='ko', label='🇺🇸 미국 테크 마감 리캡 · 2026-05-12',
        headline='S&P/Nasdaq 신고가 · LITE +16%',
        og_data={'card1':{'tick':'S&P','val':'7,412','sub':'+0.19%','color':'up'},
                 'card2':{'tick':'NASDAQ','val':'26,274','sub':'+0.10%','color':'up'},
                 'card3':{'tick':'LITE','val':'+16.4%','sub':'OPTICS','color':'gold'},
                 'card4':{'tick':'INTC','val':'+5.7%','sub':'APPLE','color':'gold'}})
"
```

---

## 8. 단톡방 자동 공유 (Phase 2)

GitHub Actions 의 마지막 step 으로 추가 가능:

### 옵션 A — Discord 웹훅
```yaml
- name: Notify Discord
  run: |
    curl -X POST -H "Content-Type: application/json" \
      -d '{"content":"📊 ${{ steps.run.outputs.title }}\n👉 https://luckyplz.com/blog/${{ steps.run.outputs.slug }}/"}' \
      ${{ secrets.DISCORD_WEBHOOK }}
```

### 옵션 B — Slack 웹훅
같은 방식.

### 옵션 C — 카카오톡 오픈채팅 봇
공식 API는 비즈에 제한되어 있어 어렵다. 대안:
- 카카오톡 i 비즈메시지 알림톡 (유료, 사업자 인증 필요)
- 또는 별도 PC 에서 `pyautogui` 로 카카오톡 클라이언트 자동 입력 (불안정, 비공식)
- 가장 현실적: **본인이 매 슬롯마다 RSS 알림** → 30초 안에 단톡방 손수 공유.

---

## 9. 비용 / 성능 모니터링

### 일일 비용 추정
- 슬롯당 Claude 호출: input ~2K tokens, output ~3K tokens, web_search 8-12 회
- Sonnet 4.5: input $3/M, output $15/M
- 슬롯당 예상 비용: **$0.05-0.15**
- 일일 총: **$0.20-0.60**
- 월 총: **$6-18**

### Anthropic Console 에서 모니터링
- https://console.anthropic.com/usage 에서 일별/슬롯별 비용 확인
- 슬랙으로 한도 알림 설정 가능

### 실패율 모니터링
- GitHub Actions 의 success rate
- 첫 7일은 매일 수동 점검 권장 → 안정화되면 주 1회

---

## 10. 안전 장치 (이미 구현됨)

- ✅ Prompt 가 holiday/no-session 감지 시 `skip: true` 반환 → 빈 글 안 만듦.
- ✅ JSON parse 실패 시 명확한 에러 + 처음 2000자 로그.
- ✅ `LP_GIT_PUSH=0` (또는 미설정) 으로 dry-run 가능.
- ✅ Cache bump 가 실패해도 다음 슬롯에 자동 복구 (다음 슬롯이 한 번 더 bump).
- ✅ GitHub Actions 의 `if: needs.resolve-slot.outputs.slot != ''` 가드.

---

## 11. 다음 단계 (Phase 2/3)

- [ ] **시리즈 인덱스 페이지** `/blog/daily/` — 4슬롯을 컴팩트 카드로 묶음
- [ ] **데이터 캐싱 layer** — 같은 trading_date 의 web_search 결과 재사용 (비용 ↓)
- [ ] **카톡방 자동 공유** (Discord webhook 부터)
- [ ] **품질 자가검증** — Claude 가 응답 직후 self-critique 1회 호출
- [ ] **A/B 테스트** — 두 가지 OG 디자인을 격일 발행, CTR 비교
- [ ] **이미 공휴일 자동 인지** — KR/US 휴장 캘린더 JSON 추가, prompt 외부 가드

---

## 12. 트러블슈팅 체크리스트

| 증상 | 우선 확인 |
|------|----------|
| 글이 안 올라옴 | Actions 탭 → 마지막 실행 로그 |
| 빈 글이 올라옴 | `data` JSON 의 키 누락. Prompt 의 required 추가 |
| OG 이미지 깨짐 | Pillow font 로딩 실패. Linux 폰트 폴백 확인 |
| 한자/한글 깨짐 | `fonts-noto-cjk` 미설치. workflow apt 추가 |
| git push 실패 | `permissions: contents: write` 확인 |
| 비용 폭증 | web_search `max_uses` 줄이기 (현 12 → 8) |

---

마지막으로: **첫 1주는 무조건 수동 검수**. 다음 cron 안정화되면 점차 손 떼기.
