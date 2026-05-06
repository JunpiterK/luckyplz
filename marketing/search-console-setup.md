# Search Console 등록 — 가장 먼저 해야 할 작업

검색엔진이 luckyplz.com 의 존재 자체를 모르면 글 100개 써도 검색 결과에 안 뜸. 30분이면 끝남.

## ① Google Search Console (가장 중요)

### 1) 접속
https://search.google.com/search-console

### 2) "속성 추가" → "도메인" 선택
`luckyplz.com` 입력 (https:// 빼고 도메인만)

### 3) DNS 인증
화면에 나오는 TXT 레코드 (예: `google-site-verification=ABC123...`) 를 복사 → **Cloudflare DNS** 에 추가

**Cloudflare 에서**:
1. dash.cloudflare.com → luckyplz.com 선택
2. 좌측 메뉴 **DNS** → **Records**
3. **Add record** 클릭
4. Type: `TXT`, Name: `@` (또는 `luckyplz.com`), Content: 복사한 인증 값 그대로 붙여넣기
5. Proxy: 끄기 (회색 구름)
6. Save

DNS 전파에 2~5분. Search Console 로 돌아가서 **확인** 클릭.

### 4) sitemap 제출
인증 후:
1. 좌측 메뉴 **Sitemaps** 클릭
2. "새 사이트맵 추가" 입력란에 `sitemap.xml` 입력 (`/sitemap.xml` 아니고 그냥 `sitemap.xml`)
3. **제출**

상태가 "성공" 나오면 OK. 24~72시간 안에 인덱싱 시작.

### 5) 주요 글 색인 요청 (가속)
좌측 **URL 검사** → 다음 URL 들 하나씩 입력 → **색인 생성 요청**:

```
https://luckyplz.com/
https://luckyplz.com/blog/
https://luckyplz.com/blog/spacex-ipo-2026/
https://luckyplz.com/blog/spacex-ipo-2026-en/
https://luckyplz.com/blog/spacex-etf-comparison/
https://luckyplz.com/blog/spacex-etf-comparison-en/
https://luckyplz.com/blog/echostar-sats-spacex-backdoor/
https://luckyplz.com/blog/echostar-sats-spacex-backdoor-en/
https://luckyplz.com/blog/musk-net-worth-after-spacex-ipo/
https://luckyplz.com/blog/spacex-vs-tesla/
```

10개까지 하루에 색인 요청 가능. 안 하면 "발견은 됐는데 인덱싱 안 됨" 상태로 며칠 머무를 수 있음.

---

## ② Bing Webmaster Tools

Bing/Yahoo/DuckDuckGo 동시 커버. Search Console 데이터 그대로 import 가능해서 5분이면 끝.

### 1) 접속
https://www.bing.com/webmasters

### 2) "Sign In" → Microsoft 계정
없으면 outlook.com 으로 가입 (1분)

### 3) "Import sites from Google Search Console" 선택
권한 부여하면 자동으로 luckyplz.com 가져옴. 인증 절차 생략됨.

수동으로 하려면:
- "Add a site" → `https://luckyplz.com` → DNS TXT 또는 HTML 파일 인증 → sitemap 제출

---

## ③ 네이버 Search Advisor (한국 트래픽 핵심)

한국 검색의 50%+ 가 네이버. 안 하면 한국 트래픽 절반 손실.

### 1) 접속
https://searchadvisor.naver.com

### 2) "웹마스터 도구" → "사이트 등록"
`https://luckyplz.com` 입력

### 3) 사이트 소유 확인
HTML 파일 또는 메타 태그 방식 둘 중 하나 선택. **메타 태그 방식이 빠름**:
- 화면에 나오는 `<meta name="naver-site-verification" content="..." />` 복사
- `public/index.html` 의 `<head>` 안에 붙여넣기 → commit + push (Cloudflare Pages 자동 배포 5분)
- Search Advisor 로 돌아가서 **확인**

### 4) sitemap 제출
"요청 → 사이트맵 제출" 메뉴
입력: `https://luckyplz.com/sitemap.xml`

### 5) RSS 도 제출 (있다면)
luckyplz 는 현재 RSS 없음. 스킵.

⚠️ **네이버는 인덱싱이 Google 보다 느림**. 1~3주 걸릴 수 있음. 그래서 빨리 등록할수록 유리.

---

## ④ Daum 검색

다음 검색엔진 등록. 5분.

### 1) 접속
https://register.search.daum.net/index.daum

### 2) "검색등록" → "사이트 등록"
- 사이트명: Lucky Please
- URL: `https://luckyplz.com`
- 카테고리: 적절히 선택 (생활·정보 / 게임·오락 등)
- 설명: "행운 게임 + 우주·기술 분석 블로그. SpaceX IPO 추적, ETF 비교, 가치 평가 도구."

심사 1~2일. 통과 후 다음 검색에 노출.

---

## ⑤ 추가로 권장 (선택)

### Yandex (러시아 검색)
https://webmaster.yandex.com — 의미 있을 정도의 러시아 트래픽은 없을 듯하지만 5분이라 해두면 좋음.

### Baidu (중국)
중국어 글 (`/spacex-ipo-2026-zh/`) 있으니 등록 가치 있음.
https://ziyuan.baidu.com — 단, 중국어 인터페이스 + 까다로움. 우선순위 낮음.

---

## 등록 완료 후 검증 (1일 후)

24시간 후 Google 에서 확인:
```
site:luckyplz.com
```

이 검색어 결과에 luckyplz 페이지들이 나오면 인덱싱 시작된 것. 안 나오면:
- Search Console → "URL 검사" → 색인 요청 다시
- robots.txt 가 막고 있는지 확인 (현재 luckyplz 는 안 막혀있음)

## 등록 완료 체크리스트

- [ ] Google Search Console 등록 + sitemap 제출
- [ ] Google 주요 글 10개 색인 요청
- [ ] Bing Webmaster Tools 등록 (Search Console import)
- [ ] 네이버 Search Advisor 등록 + 메타 태그 추가 + sitemap 제출
- [ ] Daum 사이트 등록
- [ ] 24시간 후 `site:luckyplz.com` 으로 결과 확인

이 5개만 끝나면 외부 트래픽 인프라 50% 완성. 나머지는 Reddit/X/한국 커뮤니티 발사로 쌓아감.
