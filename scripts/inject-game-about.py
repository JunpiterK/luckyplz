#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inject-game-about.py — 게임 페이지에 실제 가시 SEO 콘텐츠 + FAQPage 스키마 주입 (멱등).

배경 (2026-08-18 수익화 감사, docs/MONETIZATION_AUDIT_2026-08.md):
게임 페이지의 가시 텍스트가 61~115단어뿐이라 구글이 랭크할 콘텐츠가 없었다.
ladder 만 예외적으로 `lp-game-about` 섹션(715단어)을 갖고 있었고 그 패턴이
검증됐으므로, 핵심 행운/뽑기 게임에 동일 구조를 이식한다.

중요 — 숨김 텍스트가 아니다:
`html,body{overflow:hidden}` 은 `@media(min-width:900px)` 안에만 있다. 모바일에서는
정상 스크롤되어 사람이 실제로 읽는 콘텐츠이고, 구글은 모바일 우선 색인이라 그대로
읽는다. 과거 `left:-9999px` 방식(가이드라인 위반, 이미 제거됨)과는 완전히 다르다.

멱등: `<!--lp-game-about:start-->` ~ `<!--lp-game-about:end-->` 펜스로 감싸고,
재실행 시 블록을 통째로 교체한다.

사용: python scripts/inject-game-about.py
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES = ROOT / "public" / "games"

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CSS = """<style>
/* === lp-game-about — 게임 하단 가시 콘텐츠 (ladder 패턴 이식) ===
   모바일에서 스크롤로 도달하는 실제 콘텐츠. 데스크탑(>=900px)은 게임 UI 가
   화면을 채우므로 overflow:hidden 으로 가려지지만, 모바일 우선 색인 기준
   Googlebot 은 이 콘텐츠를 정상적으로 읽는다. */
/* 게임 UI 는 대부분 position:fixed/absolute 라 문서 흐름 높이가 0 이다.
   그대로 두면 이 섹션이 top:0 에서 시작해 게임 화면 위에 겹친다(2026-08-19
   신고, 17종 전부 해당). 아래 인라인 스크립트가 정확한 여백을 계산하고,
   여기 100dvh 는 스크립트가 못 돌 때의 폴백이다.
   z-index 9100 은 게임 고정 UI 최대치(9040 = 전체화면 버튼)보다 위 —
   스크롤해서 읽을 때 게임 UI 가 글자 위에 떠 있으면 안 된다.
   배경은 불투명 + 전체 폭이어야 뒤의 고정 UI 가 좌우로 비치지 않는다. */
.lp-game-about{position:relative;z-index:9100;width:100%;
  margin-top:100vh;margin-top:100dvh;
  background:#0A0A1A;
  padding:36px 20px 80px;color:rgba(255,255,255,.78);
  font-family:'Noto Sans KR','Pretendard',-apple-system,sans-serif;
  font-size:14.5px;line-height:1.75}
.lp-game-about .lp-about-inner{max-width:880px;margin:0 auto}
.lp-game-about .lp-about-head{margin-bottom:24px;padding-bottom:16px;
  border-bottom:1px solid rgba(255,255,255,.06)}
.lp-game-about .lp-about-head h2{font-family:'Orbitron','Noto Sans KR',sans-serif;
  font-size:1.4em;font-weight:800;letter-spacing:-.01em;color:#fff;margin:0 0 6px}
.lp-game-about .lp-about-sub{font-size:.85em;color:rgba(255,255,255,.5);
  font-style:italic;margin:0}
.lp-game-about .lp-about-block{margin-bottom:28px}
.lp-game-about .lp-about-block h3{font-size:1.05em;font-weight:700;color:#fff;
  margin:0 0 10px;letter-spacing:-.005em}
.lp-game-about p{margin:0 0 10px}
.lp-game-about ol,.lp-game-about ul{margin:8px 0 8px 22px;padding:0}
.lp-game-about ol li,.lp-game-about ul li{margin:5px 0}
.lp-game-about strong{color:rgba(255,255,255,.95);font-weight:700}
.lp-game-about a{color:#5dc1ff;text-decoration:none;
  border-bottom:1px dashed rgba(93,193,255,.3)}
.lp-game-about a:hover{border-bottom-style:solid;border-bottom-color:#5dc1ff}
.lp-game-about .lp-use-cases{list-style:none;margin-left:0;display:grid;
  grid-template-columns:1fr;gap:6px}
.lp-game-about .lp-use-cases li{padding:7px 12px;background:rgba(255,255,255,.025);
  border-left:2px solid rgba(93,193,255,.3);border-radius:0 6px 6px 0}
.lp-game-about .lp-faq{margin:0}
.lp-game-about .lp-faq dt{font-weight:700;color:rgba(255,255,255,.92);
  margin-top:14px;font-size:.95em}
.lp-game-about .lp-faq dt:first-child{margin-top:0}
.lp-game-about .lp-faq dd{margin:4px 0 0;color:rgba(255,255,255,.7);font-size:.92em;
  padding-left:8px;border-left:2px solid rgba(255,255,255,.06)}
.lp-game-about .lp-about-footer{margin-top:32px;padding-top:18px;
  border-top:1px solid rgba(255,255,255,.05);font-size:.82em;color:rgba(255,255,255,.5)}
@media (min-width:600px){
  .lp-game-about{padding:48px 32px 100px;font-size:15px}
  .lp-game-about .lp-use-cases{grid-template-columns:1fr 1fr}
  .lp-game-about .lp-about-head h2{font-size:1.55em}
}
@media (min-width:900px){.lp-game-about .lp-use-cases{grid-template-columns:1fr 1fr 1fr}}
</style>"""

CONTENT = {}

CONTENT["roulette"] = {
    "h2": "룰렛 돌리기 — 더 알아보기",
    "sub": "Wheel Spinner / 돌림판 — 여러 후보 중 하나를 무작위로 뽑는 가장 빠른 방법",
    "blocks": [
        ("🎯 사용 방법", """<p>룰렛(돌림판)은 후보를 적어 넣고 원판을 돌려 바늘이 가리킨 항목을 뽑는 도구입니다. 사람이 직접 고르면 눈치와 서열이 개입하지만, 룰렛은 결과가 나온 뒤에야 알 수 있어 <strong>모두가 납득하는 결정</strong>이 됩니다. Lucky Please 룰렛은 이렇게 씁니다:</p>
<ol>
<li><strong>항목 입력</strong> — 이름·메뉴·벌칙 등 후보를 한 줄에 하나씩. 2개부터 수십 개까지 가능합니다.</li>
<li><strong>프리셋 활용</strong> — 자주 쓰는 조합(점심 메뉴, 팀원 이름 등)은 저장해 두면 다음에 한 번에 불러올 수 있어요.</li>
<li><strong>돌리기</strong> — 버튼을 누르면 원판이 회전하고, 감속하며 멈춘 지점이 당첨입니다.</li>
<li><strong>결과 공유</strong> — 결과 화면의 공유 버튼으로 카톡·메신저에 바로 보낼 수 있습니다.</li>
</ol>"""),
        ("🎲 룰렛은 정말 공정한가요", """<p>이 룰렛은 <strong>각 항목이 차지한 각도에 정확히 비례해서</strong> 당첨 확률이 결정됩니다. 항목이 N개이고 크기가 같다면 각 항목의 확률은 정확히 1/N입니다. 회전은 브라우저의 난수로 시작 속도와 감속이 정해지므로, 같은 버튼을 눌러도 매번 다른 지점에 멈춥니다.</p>
<p>사람이 "아무 숫자나" 고를 때는 실제로 무작위가 아니라는 점이 흥미롭습니다. 사람에게 1~10 중 아무 수나 고르라고 하면 7이 과도하게 많이 나오고 양 끝(1·10)은 회피하는 경향이 반복 관찰됩니다. <strong>사람의 직관은 무작위에 약하기 때문에</strong>, 공정함이 중요한 자리일수록 도구를 쓰는 편이 낫습니다.</p>
<p>다만 룰렛은 <em>기억이 없습니다</em>. 방금 A가 걸렸다고 다음에 A가 덜 나오지 않아요. 매 회전은 독립 시행이라 같은 항목이 연속으로 나올 수도 있고, 이건 고장이 아니라 무작위의 정상적인 모습입니다.</p>"""),
        ("💡 더 잘 쓰는 요령", """<ul>
<li><strong>항목은 짧게.</strong> 원판 위 글자는 조각 안에 들어가야 읽힙니다. "김철수 대리님"보다 "김철수"가 낫습니다.</li>
<li><strong>10개를 넘기면 조각이 얇아집니다.</strong> 후보가 많으면 두 단계로 나누세요. 먼저 그룹을 뽑고 그 안에서 다시 돌리는 방식이 읽기 편합니다.</li>
<li><strong>돌리기 전에 규칙을 합의하세요.</strong> "걸린 사람이 계산"인지 "걸린 사람이 면제"인지 먼저 정해야 뒤탈이 없습니다.</li>
<li><strong>재추첨은 미리 정한 경우에만.</strong> 결과를 보고 나서 다시 돌리자고 하면 공정성이 무너집니다.</li>
<li><strong>여럿이 볼 때는 화면을 크게.</strong> 모바일은 가로 모드, PC는 전체화면이 잘 보입니다.</li>
</ul>"""),
        ("🌟 이럴 때 씁니다", """<ul class="lp-use-cases">
<li>☕ <strong>커피·밥값 내기</strong> — 누가 계산할지 10초 결정</li>
<li>🍽️ <strong>점심 메뉴 고르기</strong> — 아무거나 무한루프 끝내기</li>
<li>🎁 <strong>경품 추첨</strong> — 이벤트 당첨자 공개 선정</li>
<li>🎤 <strong>발표 순서</strong> — 수업·회의에서 누가 먼저</li>
<li>🧹 <strong>당번 정하기</strong> — 청소·설거지·정리 담당</li>
<li>🎭 <strong>벌칙 뽑기</strong> — 모임·회식 게임 진행</li>
<li>👫 <strong>짝·자리 배정</strong> — 처음 만난 사람들 페어링</li>
</ul>"""),
    ],
    "faq": [
        ("룰렛 결과를 조작할 수 있나요?",
         "아닙니다. 회전 시작 속도와 감속이 브라우저 난수로 정해지고 멈추는 지점은 물리 계산 결과입니다. 특정 항목이 나오도록 만드는 설정은 없습니다."),
        ("같은 항목이 계속 나오는데 고장인가요?",
         "정상입니다. 매 회전은 앞의 결과와 무관한 독립 시행이라 같은 항목이 연속으로 나올 수 있습니다. 4개 항목에서 같은 게 두 번 연속 나올 확률은 25%로 생각보다 자주 일어납니다."),
        ("항목은 몇 개까지 넣을 수 있나요?",
         "기술적으로는 수십 개까지 되지만 글자가 읽히려면 10개 안팎이 적당합니다. 더 많으면 그룹을 먼저 뽑고 그 안에서 다시 돌리는 2단계 방식을 권합니다."),
        ("로그인이나 앱 설치가 필요한가요?",
         "필요 없습니다. 브라우저에서 바로 쓸 수 있고 무료입니다. 홈 화면에 추가하면 앱처럼 쓸 수 있어요."),
        ("결과를 친구에게 보여줄 수 있나요?",
         "결과 화면의 공유 버튼을 누르면 카톡·메신저로 보낼 수 있습니다. 여러 명이 같은 화면을 보려면 한 기기에서 돌리고 화면을 함께 보는 방식이 가장 간단합니다."),
    ],
    "footer": '다른 결정 도구가 필요하면 <a href="/games/ladder/">사다리타기</a>·<a href="/games/team/">팀 나누기</a>도 함께 써 보세요. 모두 무료이며 로그인이 필요 없습니다.',
}

CONTENT["team"] = {
    "h2": "팀 나누기 — 더 알아보기",
    "sub": "Team Generator / 조 편성 — 인원을 무작위로, 그러나 균등하게 나누는 도구",
    "blocks": [
        ("🎯 사용 방법", """<p>팀 나누기는 참가자 명단을 넣고 원하는 팀 수를 정하면 무작위로 배분해 주는 도구입니다. 가위바위보나 번호 세기와 달리 <strong>인원이 한쪽으로 몰리지 않게</strong> 자동으로 균등 배분합니다.</p>
<ol>
<li><strong>참가자 입력</strong> — 이름을 한 줄에 하나씩 적습니다. 명단을 복사해 붙여넣어도 됩니다.</li>
<li><strong>팀 수 지정</strong> — 2팀, 3팀 등 원하는 개수를 고릅니다. 딱 나눠떨어지지 않으면 남는 인원을 한 명씩 분산합니다.</li>
<li><strong>섞기</strong> — 버튼을 누르면 명단이 무작위로 재배열되어 팀에 배정됩니다.</li>
<li><strong>다시 섞기</strong> — 마음에 안 들면 다시 돌릴 수 있지만, 공정성을 위해 <em>돌리기 전에 재추첨 규칙을 정해 두는 것</em>을 권합니다.</li>
</ol>"""),
        ("⚖️ 어떻게 균등하게 나누나요", """<p>내부적으로는 명단 전체를 무작위로 섞은 뒤 순서대로 각 팀에 하나씩 나눠 담는 방식을 씁니다. 이 방법은 <strong>피셔-예이츠 셔플(Fisher-Yates shuffle)</strong>이라 불리는 표준 알고리즘으로, 가능한 모든 순서가 똑같은 확률로 나오는 것이 수학적으로 보장됩니다.</p>
<p>덕분에 10명을 3팀으로 나누면 4-3-3처럼 최대 1명 차이 안에서만 갈립니다. 사람이 손으로 나눌 때 흔히 생기는 "친한 사람끼리 몰림"이나 "특정 팀만 인원 초과" 같은 문제가 생기지 않습니다.</p>
<p>한 가지 알아둘 점은 무작위 배분이 <em>실력까지 균등하게 맞춰 주지는 않는다</em>는 것입니다. 운동 경기처럼 실력 균형이 중요하면, 잘하는 사람들을 먼저 각 팀에 한 명씩 배치한 뒤 나머지를 무작위로 돌리는 방식이 낫습니다.</p>"""),
        ("💡 더 잘 쓰는 요령", """<ul>
<li><strong>명단은 복사·붙여넣기가 빠릅니다.</strong> 단톡방 참여자 목록이나 엑셀 열을 그대로 붙여도 줄 단위로 인식됩니다.</li>
<li><strong>동명이인은 구분해 주세요.</strong> "김민수"가 둘이면 "김민수(1반)"처럼 적어야 결과를 보고 헷갈리지 않습니다.</li>
<li><strong>실력 균형이 필요하면 2단계로.</strong> 핵심 인원을 먼저 수동 배치하고 나머지만 무작위로 돌리세요.</li>
<li><strong>결석자는 미리 빼세요.</strong> 배정 후 빠지면 팀 인원이 어긋납니다.</li>
<li><strong>결과를 캡처해 공유하세요.</strong> 나중에 "나 저 팀 아니었는데" 같은 분쟁을 막아 줍니다.</li>
</ul>"""),
        ("🌟 이럴 때 씁니다", """<ul class="lp-use-cases">
<li>🏫 <strong>수업 조 편성</strong> — 모둠 활동·발표 조 나누기</li>
<li>⚽ <strong>체육대회·풋살</strong> — 팀전 인원 배분</li>
<li>🏕️ <strong>MT·워크숍</strong> — 방 배정, 조별 미션</li>
<li>🎮 <strong>게임 팀전</strong> — 내전 밸런스 맞추기</li>
<li>💼 <strong>회사 프로젝트</strong> — 태스크포스 구성</li>
<li>🍳 <strong>역할 분담</strong> — 요리·설거지·장보기 조</li>
</ul>"""),
    ],
    "faq": [
        ("인원이 팀 수로 나눠떨어지지 않으면 어떻게 되나요?",
         "남는 인원을 팀마다 한 명씩 분산해 배정합니다. 10명을 3팀으로 나누면 4-3-3이 되어 최대 1명 차이만 생깁니다."),
        ("정말 무작위인가요, 아니면 순서대로 나누나요?",
         "명단 전체를 피셔-예이츠 셔플로 완전히 섞은 뒤 배분합니다. 입력 순서는 결과에 영향을 주지 않습니다."),
        ("실력이 비슷하게 팀을 짤 수 있나요?",
         "무작위 배분은 인원만 균등하게 맞춥니다. 실력 균형이 필요하면 핵심 인원을 먼저 각 팀에 수동 배치한 뒤 나머지만 무작위로 돌리는 방식을 권합니다."),
        ("같은 사람들끼리 계속 같은 팀이 되는데요?",
         "매번 독립적으로 섞기 때문에 우연히 반복될 수 있습니다. 인원이 적을수록 같은 조합이 다시 나올 확률은 낮지 않습니다."),
        ("명단을 저장해 둘 수 있나요?",
         "자주 쓰는 명단은 프리셋으로 저장해 두면 다음에 한 번에 불러올 수 있습니다. 저장은 이 브라우저에만 남으며 서버로 전송되지 않습니다."),
    ],
    "footer": '순서까지 정해야 한다면 <a href="/games/ladder/">사다리타기</a>, 한 명만 뽑을 거라면 <a href="/games/roulette/">룰렛</a>이 더 빠릅니다.',
}

CONTENT["lotto"] = {
    "h2": "로또 번호 추첨기 — 더 알아보기",
    "sub": "Lotto Number Generator — 무작위 번호 조합을 만들어 주는 도구",
    "blocks": [
        ("🎯 사용 방법", """<p>이 도구는 정해진 범위 안에서 <strong>중복 없는 번호 조합을 무작위로 뽑아 주는 생성기</strong>입니다. 여러 나라의 로또 형식(번호 범위와 뽑는 개수)을 프리셋으로 제공하며, 한 번에 여러 세트를 만들 수도 있습니다.</p>
<ol>
<li><strong>형식 선택</strong> — 국가별 프리셋을 고르거나 범위를 직접 지정합니다.</li>
<li><strong>세트 수 지정</strong> — 1~10세트까지 한 번에 생성할 수 있습니다.</li>
<li><strong>속도 선택</strong> — 추첨 연출을 보고 싶으면 보통·느리게, 바로 결과만 원하면 즉시 모드를 고릅니다.</li>
<li><strong>기록 확인</strong> — 생성한 조합은 이 브라우저에 최근 30건까지 남아 다시 볼 수 있습니다.</li>
</ol>"""),
        ("📊 확률에 대해 알아 둘 것", """<p>먼저 분명히 해 둘 것이 있습니다. <strong>이 도구는 당첨 번호를 예측하지 않습니다.</strong> 로또 추첨은 매회 완전히 독립적인 사건이라, 과거 회차 데이터로 다음 번호를 맞힐 수 있는 방법은 수학적으로 존재하지 않습니다.</p>
<p>45개 중 6개를 고르는 형식에서 모든 번호를 맞힐 확률은 <strong>814만 5,060분의 1</strong>입니다. 크기를 실감하기 어려우니 비교하자면, 번호 하나를 사서 1등에 당첨될 확률은 벼락을 맞을 확률보다 낮습니다.</p>
<p>흔히 도는 이야기들도 대부분 사실이 아닙니다. "한동안 안 나온 번호가 나올 때가 됐다"는 생각은 <em>도박사의 오류</em>라 불리는 대표적인 착각입니다. 공에는 기억이 없어서 지난주에 나왔든 10년간 안 나왔든 이번 주 확률은 똑같습니다. 마찬가지로 1·2·3·4·5·6 조합도 다른 어떤 조합과 정확히 같은 확률을 가집니다.</p>
<p>번호 선택이 <em>유일하게</em> 실질적 차이를 만드는 지점은 당첨 확률이 아니라 <strong>당첨금 분배</strong>입니다. 많은 사람이 고르는 조합(생일 때문에 몰리는 1~31, 대각선 패턴 등)에 당첨되면 같은 등수 당첨자가 많아 1인당 금액이 줄어듭니다. 무작위 생성기가 도움이 된다면 바로 이 부분입니다.</p>"""),
        ("💡 건강하게 즐기는 법", """<ul>
<li><strong>잃어도 괜찮은 금액만.</strong> 로또는 투자가 아니라 오락입니다. 기대수익은 구조적으로 마이너스입니다.</li>
<li><strong>"시스템"을 파는 곳을 조심하세요.</strong> 당첨 번호를 예측한다는 유료 서비스는 수학적 근거가 없습니다.</li>
<li><strong>본전 생각으로 늘리지 마세요.</strong> 지난 손실을 만회하려 금액을 키우는 것이 가장 흔한 함정입니다.</li>
<li><strong>몰리는 번호를 피하고 싶다면</strong> 31을 넘는 숫자를 섞으면 생일 기반 조합과 겹칠 가능성이 줄어듭니다.</li>
<li><strong>재미가 사라지면 멈추세요.</strong> 스트레스가 된다면 그건 오락이 아닙니다.</li>
</ul>"""),
        ("🌟 이럴 때 씁니다", """<ul class="lp-use-cases">
<li>🎱 <strong>번호 고민 없이</strong> — 어떤 조합을 쓸지 못 정할 때</li>
<li>🎁 <strong>사내 경품 번호</strong> — 추첨 번호 무작위 배정</li>
<li>🔢 <strong>무작위 숫자 필요</strong> — 순번·좌석 번호 뽑기</li>
<li>📚 <strong>확률 수업 자료</strong> — 무작위 표본 시연</li>
<li>🎲 <strong>보드게임 보조</strong> — 숫자 생성 대용</li>
</ul>"""),
    ],
    "faq": [
        ("이 도구로 당첨 확률이 올라가나요?",
         "아닙니다. 어떤 방식으로 번호를 고르든 당첨 확률은 동일합니다. 이 도구는 번호를 대신 골라 주는 생성기일 뿐 예측 기능은 없습니다."),
        ("자주 나온 번호를 골라 주나요?",
         "아닙니다. 과거 회차와 무관하게 매번 새로 무작위 생성합니다. 과거 데이터로 다음 번호를 예측할 수 있다는 주장은 수학적 근거가 없습니다."),
        ("연속된 숫자가 나왔는데 다시 뽑아야 하나요?",
         "그럴 필요 없습니다. 연속 숫자 조합도 다른 조합과 정확히 같은 확률을 가집니다. 무작위는 원래 사람 눈에 덜 무작위로 보이는 패턴을 자주 만듭니다."),
        ("생성한 번호가 저장되나요?",
         "최근 30건까지 이 브라우저에만 저장됩니다. 서버로 전송되지 않으며 브라우저 저장소를 지우면 사라집니다."),
        ("몇 세트까지 한 번에 만들 수 있나요?",
         "1회에 최대 10세트까지 생성할 수 있습니다. 즉시 모드를 쓰면 연출 없이 바로 결과가 나옵니다."),
    ],
    "footer": '이 도구는 오락용 번호 생성기이며 당첨을 보장하거나 예측하지 않습니다. 구매는 본인의 판단과 책임입니다. 다른 추첨 도구는 <a href="/games/roulette/">룰렛</a>·<a href="/games/bingo/">빙고</a>를 참고하세요.',
}

CONTENT["bingo"] = {
    "h2": "빙고 — 더 알아보기",
    "sub": "Bingo — 경품 추첨과 모임 진행에 쓰는 고전 추첨 게임",
    "blocks": [
        ("🎯 사용 방법", """<p>빙고는 격자판에 적힌 숫자나 단어가 하나씩 호명될 때마다 지워 나가다가, 가로·세로·대각선 한 줄을 먼저 완성하면 이기는 게임입니다. 규칙이 단순해 <strong>나이와 상관없이 바로 참여</strong>할 수 있어 행사 진행에 자주 쓰입니다.</p>
<ol>
<li><strong>판 크기 선택</strong> — 3×3부터 5×5까지. 인원이 많고 시간이 넉넉하면 큰 판이 좋습니다.</li>
<li><strong>항목 채우기</strong> — 숫자로 자동 채우거나 이름·미션·경품 등 원하는 단어를 직접 넣습니다.</li>
<li><strong>호명 시작</strong> — 버튼을 누르면 무작위로 하나씩 뽑히고, 참가자는 자기 판에서 해당 칸을 지웁니다.</li>
<li><strong>승리 확인</strong> — 한 줄이 완성되면 빙고. 여러 줄을 조건으로 걸어 게임을 길게 끌 수도 있습니다.</li>
</ol>"""),
        ("📐 빙고가 잘 굴러가는 조건", """<p>빙고의 재미는 <strong>언제 끝날지 모르는 긴장감</strong>에서 나옵니다. 그래서 판 크기와 호명할 항목 수의 비율이 중요합니다. 항목 풀이 판 칸 수보다 훨씬 크면 좀처럼 줄이 완성되지 않아 지루해지고, 반대로 너무 작으면 몇 번 만에 여러 명이 동시에 빙고를 외쳐 김이 샙니다.</p>
<p>경험적으로 5×5 판(25칸)에는 호명 풀 40~60개 정도가 알맞습니다. 3×3 판은 15~25개면 충분하고, 짧은 시간에 승부를 내야 하는 자리에 적합합니다.</p>
<p>여러 명이 동시에 빙고를 외치는 상황도 미리 정해 두면 좋습니다. 공동 우승으로 할지, 다음 줄까지 이어서 단독 승자를 가릴지 시작 전에 합의하면 진행이 매끄럽습니다.</p>"""),
        ("💡 진행을 매끄럽게 하는 요령", """<ul>
<li><strong>화면을 크게 띄우세요.</strong> 행사장이라면 프로젝터나 큰 화면에 호명 결과를 함께 보여 주는 편이 좋습니다.</li>
<li><strong>숫자 대신 단어를 넣어 보세요.</strong> 참가자 이름, 회사 키워드, 미션 문구를 넣으면 훨씬 반응이 좋습니다.</li>
<li><strong>경품은 등수별로 미리 공개하세요.</strong> 무엇을 걸고 하는지 알면 집중도가 올라갑니다.</li>
<li><strong>호명 속도를 조절하세요.</strong> 초반은 빠르게, 줄이 차오르면 천천히 뽑아야 긴장감이 삽니다.</li>
<li><strong>중복 호명은 자동으로 걸러집니다.</strong> 이미 뽑힌 항목은 다시 나오지 않으니 따로 표시할 필요가 없어요.</li>
</ul>"""),
        ("🌟 이럴 때 씁니다", """<ul class="lp-use-cases">
<li>🎁 <strong>경품 추첨</strong> — 사내 행사·연말 모임</li>
<li>🏫 <strong>수업 활동</strong> — 단어 학습·복습 게임</li>
<li>🎪 <strong>워크숍 아이스브레이킹</strong> — 처음 만난 사람들</li>
<li>👨‍👩‍👧 <strong>가족 모임</strong> — 명절·생일 파티</li>
<li>💒 <strong>결혼식·돌잔치</strong> — 하객 참여 이벤트</li>
<li>📺 <strong>온라인 방송</strong> — 시청자 참여 추첨</li>
</ul>"""),
    ],
    "faq": [
        ("몇 명까지 함께할 수 있나요?",
         "인원 제한은 없습니다. 진행자가 한 화면에서 호명하고 참가자들은 각자 종이 판이나 자기 기기를 보는 방식이면 수십 명도 가능합니다."),
        ("판 크기는 어떻게 고르나요?",
         "시간이 짧으면 3×3, 행사에서 길게 끌고 싶으면 5×5가 적당합니다. 5×5에는 호명 풀 40~60개 정도가 균형이 좋습니다."),
        ("숫자 말고 다른 걸 넣어도 되나요?",
         "이름·미션·키워드 등 원하는 단어를 넣을 수 있습니다. 행사 성격에 맞춘 단어를 쓰면 참여도가 훨씬 높아집니다."),
        ("이미 뽑힌 항목이 또 나오나요?",
         "나오지 않습니다. 호명된 항목은 자동으로 제외되므로 중복을 따로 관리할 필요가 없습니다."),
        ("여러 명이 동시에 빙고가 되면 어떻게 하나요?",
         "규칙을 미리 정해 두는 것이 좋습니다. 공동 우승으로 처리하거나 다음 줄까지 이어서 단독 승자를 가리는 방식이 일반적입니다."),
    ],
    "footer": '한 명만 빠르게 뽑을 거라면 <a href="/games/roulette/">룰렛</a>, 순서를 정할 거라면 <a href="/games/ladder/">사다리타기</a>가 더 간단합니다.',
}

# ---- 2·3차 콘텐츠 병합 (아케이드 6종 + 레이싱/우주/퀴즈/주사위 6종) ----
# 파일이 비대해지는 것을 막으려 분리했다. 새 게임 콘텐츠는 content_3 에 이어 붙이거나
# content_4 를 만들어 같은 방식으로 등록한다.
def _load(mod, var):
    path = Path(__file__).resolve().parent / (mod + ".py")
    if not path.exists():
        return {}
    spec = importlib.util.spec_from_file_location(mod, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return getattr(m, var, {})


CONTENT.update(_load("game_about_content_2", "CONTENT_2"))
CONTENT.update(_load("game_about_content_3", "CONTENT_3"))

# 600단어 미달 게임 보강 블록 — 각 게임의 blocks 뒤(FAQ 앞)에 덧붙인다.
for _k, _extra in _load("game_about_content_4", "EXTRA_BLOCKS").items():
    if _k in CONTENT:
        CONTENT[_k]["blocks"] = list(CONTENT[_k]["blocks"]) + list(_extra)


PLACE_JS = """<script>
/* 이 섹션이 게임 화면과 겹치지 않도록 시작 위치를 잰다.
   CSS 만으로는 못 한다 — 게임마다 흐름 높이가 0~734px 로 제각각이라
   100dvh 를 고정으로 주면 흐름 높이가 있는 게임에서 빈 화면이 하나 생긴다.
   여백을 0 으로 되돌린 뒤 실제 문서 위치를 재고, 한 화면에서 모자란 만큼만 채운다. */
(function(){
  var el = null;
  function docTop(node){ return node.getBoundingClientRect().top + (window.pageYOffset || 0); }
  function place(){
    el = el || document.querySelector('.lp-game-about');
    if (!el) return;
    el.style.marginTop = '0px';
    var need = Math.max(0, (window.innerHeight || 0) - docTop(el));
    el.style.marginTop = need + 'px';
    /* 인접 형제와 margin 이 상쇄되면(둘 중 큰 값만 적용) 계산한 만큼
       내려가지 않는다 — car-racing 에서 8px 모자랐다. 실제 위치를 다시
       재서 모자란 만큼 더한다. */
    var delta = (window.innerHeight || 0) - docTop(el);
    if (delta > 0) el.style.marginTop = (need + delta) + 'px';
  }
  function boot(){ place(); setTimeout(place, 400); setTimeout(place, 1200); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
  window.addEventListener('resize', place);
  window.addEventListener('orientationchange', function(){ setTimeout(place, 250); });
})();
</script>"""

FENCE = re.compile(r'<!--lp-game-about:start-->.*?<!--lp-game-about:end-->\s*', re.S)


def build_section(data):
    p = ['<!--lp-game-about:start-->', CSS,
         '<section class="lp-game-about" aria-label="About this game" lang="ko">',
         '  <div class="lp-about-inner">',
         '    <header class="lp-about-head">',
         '      <h2>{}</h2>'.format(data["h2"]),
         '      <p class="lp-about-sub">{}</p>'.format(data["sub"]),
         '    </header>']
    for h3, body in data["blocks"]:
        p += ['    <article class="lp-about-block">',
              '      <h3>{}</h3>'.format(h3), body, '    </article>']
    p += ['    <article class="lp-about-block">', '      <h3>❓ 자주 묻는 질문</h3>',
          '      <dl class="lp-faq">']
    for q, a in data["faq"]:
        p += ['        <dt>Q. {}</dt>'.format(q), '        <dd>{}</dd>'.format(a)]
    p += ['      </dl>', '    </article>',
          '    <footer class="lp-about-footer">{}</footer>'.format(data["footer"]),
          '  </div>', '</section>']

    # FAQPage 스키마 — 위 dl 과 1:1 대응 (구글 리치결과 요건: 페이지에 실제로 보이는 Q&A 만)
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q,
                              "acceptedAnswer": {"@type": "Answer", "text": a}}
                             for q, a in data["faq"]]}
    p += ['<script type="application/ld+json">',
          json.dumps(faq_ld, ensure_ascii=False, indent=1),
          '</script>', PLACE_JS, '<!--lp-game-about:end-->']
    return "\n".join(p) + "\n"


def main():
    changed = 0
    for key, data in CONTENT.items():
        f = GAMES / key / "index.html"
        if not f.exists():
            print("[skip] {} — 파일 없음".format(key))
            continue
        html = f.read_text(encoding="utf-8")
        block = build_section(data)
        if FENCE.search(html):
            new, action = FENCE.sub(lambda _m: block, html), "update"
        elif "</body>" in html:
            new, action = html.replace("</body>", block + "</body>", 1), "insert"
        else:
            print("[skip] {} — </body> 없음".format(key))
            continue
        if new != html:
            f.write_text(new, encoding="utf-8")
            words = len(re.sub(r'<[^>]+>', ' ', block).split())
            print("[{}] {} — 약 {}단어 + FAQ {}문항".format(action, key, words, len(data["faq"])))
            changed += 1
        else:
            print("[same] {}".format(key))
    print("\n완료: {}개 게임".format(changed))


if __name__ == "__main__":
    main()
