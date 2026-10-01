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

사용: python scripts/inject-game-about.py [게임id ...]   (인자 없으면 전체)
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
/* ── 핵심 카드 (2026-08-21) — 스크롤해 내려온 사람이 가장 먼저 만나는 것.
   글을 읽히려 하지 말고 '이 도구를 언제 쓰는가'를 3초 안에 보여준다. */
.lp-game-about .lp-quick{display:grid;grid-template-columns:1fr;gap:8px;margin:0 0 22px}
.lp-game-about .lp-quick-card{display:flex;align-items:center;gap:10px;
  padding:11px 13px;border-radius:12px;background:rgba(255,255,255,.035);
  border:1px solid rgba(255,255,255,.07)}
.lp-game-about .lp-quick-ico{font-size:1.45em;line-height:1;flex-shrink:0}
.lp-game-about .lp-quick-txt{min-width:0}
.lp-game-about .lp-quick-t{display:block;font-weight:700;color:#fff;font-size:.92em;
  line-height:1.3}
.lp-game-about .lp-quick-d{display:block;font-size:.8em;color:rgba(255,255,255,.5);
  line-height:1.35;margin-top:1px}
/* ── 접기 — 닫힌 상태에서는 제목 줄만 보인다 (홈 lp-fold 와 같은 원칙) */
.lp-game-about .lp-about-block{margin:0;border-top:1px solid rgba(255,255,255,.07)}
.lp-game-about .lp-about-block > summary{cursor:pointer;list-style:none;
  padding:13px 30px 13px 2px;font-weight:700;color:rgba(255,255,255,.88);
  font-size:.97em;position:relative;user-select:none;-webkit-user-select:none;
  touch-action:manipulation}
.lp-game-about .lp-about-block > summary::-webkit-details-marker{display:none}
.lp-game-about .lp-about-block > summary::after{content:'+';position:absolute;
  right:6px;top:50%;transform:translateY(-50%);color:#5dc1ff;font-weight:900;
  font-size:1.1em;line-height:1}
.lp-game-about .lp-about-block[open] > summary::after{content:'\\2013'}
.lp-game-about .lp-about-block[open] > summary{color:#fff}
.lp-game-about .lp-about-block > summary:hover{color:#fff}
.lp-game-about .lp-fold-body{padding:2px 2px 18px}
.lp-game-about .lp-about-block > summary:focus-visible{outline:2px solid rgba(255,230,109,.7);
  outline-offset:2px;border-radius:6px}
@media (min-width:600px){
  .lp-game-about .lp-quick{grid-template-columns:1fr 1fr 1fr}
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
<li><strong>항목 입력</strong> — 이름·메뉴·벌칙 등 후보를 칸마다 하나씩. 2개부터 최대 30개까지, 한 항목은 20자까지 들어갑니다.</li>
<li><strong>프리셋 활용</strong> — 최근에 쓴 목록 5개는 이 브라우저에 자동으로 남아 한 번에 다시 불러올 수 있고, 로그인하면 점심 메뉴·팀원 이름 같은 조합을 이름 붙인 세트로 저장해 둘 수도 있어요.</li>
<li><strong>돌리기</strong> — SPIN 버튼을 누르거나 휠을 손가락으로 쓸어 넘기면 원판이 회전하고, 감속하며 멈춘 지점이 당첨입니다.</li>
<li><strong>결과 공유</strong> — 결과 화면의 공유 버튼으로 카톡·LINE·WhatsApp 등 메신저에 바로 보낼 수 있습니다.</li>
<li><strong>같이 보기</strong> — [방 만들기]로 초대 링크를 보내면 친구들이 각자 폰에서 같은 회전을 동시에 봅니다(방 정원 12명). 참가자는 자기 이름을 직접 넣을 수 있고, 결과에는 공정 배지와 검증용 결과 링크가 붙습니다.</li>
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
         "아닙니다. 혼자 돌릴 때는 회전 시작 속도와 감속이 브라우저 난수로 정해지고 멈추는 지점은 물리 계산 결과입니다. 같이 보기 방에서는 방장과 참가자 모두가 낸 난수를 먼저 봉인했다가 공개해 섞기 때문에 방장 혼자 결과를 고를 수 없고, 결과 링크로 누구나 같은 결과가 나오는지 다시 계산해 볼 수 있습니다. 특정 항목이 나오도록 만드는 설정은 없습니다."),
        ("같은 항목이 계속 나오는데 고장인가요?",
         "정상입니다. 매 회전은 앞의 결과와 무관한 독립 시행이라 같은 항목이 연속으로 나올 수 있습니다. 4개 항목에서 같은 게 두 번 연속 나올 확률은 25%로 생각보다 자주 일어납니다."),
        ("항목은 몇 개까지 넣을 수 있나요?",
         "최대 30개까지 넣을 수 있어 반 전체 이름도 한 판에 들어갑니다. 다만 글자가 넉넉히 읽히는 것은 10개 안팎이라, 더 많으면 그룹을 먼저 뽑고 그 안에서 다시 돌리는 2단계 방식도 좋습니다."),
        ("로그인이나 앱 설치가 필요한가요?",
         "필요 없습니다. 브라우저에서 바로 쓸 수 있고 무료입니다. 홈 화면에 추가하면 앱처럼 쓸 수 있어요."),
        ("결과를 친구에게 보여줄 수 있나요?",
         "결과 화면의 공유 버튼을 누르면 카톡·메신저로 보낼 수 있습니다. 돌리는 순간부터 함께 보고 싶다면 [방 만들기]로 초대 링크를 보내세요. 친구들이 각자 폰에서 같은 회전을 동시에 보고, 로그인 없이 닉네임만으로 들어올 수 있습니다."),
    ],
    "footer": '다른 결정 도구가 필요하면 <a href="/games/ladder/">사다리타기</a>·<a href="/games/team/">팀 나누기</a>도 함께 써 보세요. 모두 무료이며 로그인이 필요 없습니다.',
}

CONTENT["team"] = {
    "h2": "팀 나누기 — 더 알아보기",
    "sub": "Team Generator / 조 편성 — 인원을 무작위로, 그러나 균등하게 나누는 도구",
    "blocks": [
        ("🎯 사용 방법", """<p>팀 나누기는 참가자 명단을 넣고 팀 수(또는 팀당 인원)를 정하면 무작위로 배분해 주는 도구입니다. 가위바위보나 번호 세기와 달리 <strong>인원이 한쪽으로 몰리지 않게</strong> 자동으로 균등 배분합니다.</p>
<ol>
<li><strong>참가자 입력</strong> — 이름을 칸마다 하나씩 적습니다. +1·+2·+3·+5·+10 버튼으로 칸을 한꺼번에 늘릴 수 있고, 최대 40명까지 들어갑니다.</li>
<li><strong>나누는 방법</strong> — '팀 수로'(2~8팀) 또는 '팀당 인원으로'(2~10명씩) 중 고릅니다. 딱 나눠떨어지지 않으면 남는 인원을 한 명씩 분산합니다. 팀 이름은 1팀·2팀, 레드·블루, 동물 이름 중에서 고를 수 있습니다.</li>
<li><strong>뽑기</strong> — 가챠 기계가 팀 차례대로 손잡이를 돌려 캡슐을 하나씩 내보내고, 캡슐이 열리면 두루마리가 펼쳐지며 이름과 팀 도장이 찍힌 뒤 팀 보드에 이름이 적힙니다. 연출은 빠르게·보통·두근두근 중에 고르고, 기다리기 싫으면 '결과 바로 보기'로 건너뜁니다.</li>
<li><strong>다시 섞기</strong> — 마음에 안 들면 다시 돌릴 수 있지만, 공정성을 위해 <em>돌리기 전에 재추첨 규칙을 정해 두는 것</em>을 권합니다.</li>
</ol>"""),
        ("⚖️ 어떻게 균등하게 나누나요", """<p>내부적으로는 명단 전체를 무작위로 섞은 뒤 순서대로 각 팀에 하나씩 나눠 담는 방식을 씁니다. 이 방법은 <strong>피셔-예이츠 셔플(Fisher-Yates shuffle)</strong>이라 불리는 표준 알고리즘으로, 가능한 모든 순서가 똑같은 확률로 나오는 것이 수학적으로 보장됩니다.</p>
<p>덕분에 10명을 3팀으로 나누면 4-3-3처럼 최대 1명 차이 안에서만 갈립니다. 사람이 손으로 나눌 때 흔히 생기는 "친한 사람끼리 몰림"이나 "특정 팀만 인원 초과" 같은 문제가 생기지 않습니다.</p>
<p>한 가지 알아둘 점은 기본 '랜덤 섞기'가 <em>실력까지 균등하게 맞춰 주지는 않는다</em>는 것입니다. 운동 경기처럼 실력 균형이 중요하면 <strong>티어 밸런스</strong> 모드를 켜고 참가자마다 T1·T2·T3(또는 없음)을 지정하세요. 도구가 높은 티어부터 그 안에서만 순서를 섞은 뒤 1팀 → 2팀 → … 순으로 한 명씩 돌려 담습니다. 이 순번은 티어가 바뀌어도 이어지기 때문에 팀 인원 차이는 여전히 최대 1명입니다. 다만 T1이 5명인데 팀이 2개라면 한 팀이 T1을 한 명 더 갖게 되니, <strong>각 티어 인원을 팀 수의 배수로 맞추면</strong> 가장 고르게 갈립니다.</p>"""),
        ("💡 더 잘 쓰는 요령", """<ul>
<li><strong>자주 쓰는 명단은 다시 불러오세요.</strong> 최근에 쓴 명단 5개는 이 브라우저에 자동으로 남아 한 번에 불러올 수 있습니다.</li>
<li><strong>동명이인은 구분해 주세요.</strong> "김민수"가 둘이면 "김민수(1반)"처럼 적어야 결과를 보고 헷갈리지 않습니다.</li>
<li><strong>실력 균형이 필요하면 티어 밸런스로.</strong> 에이스만 T1으로 표시해도 에이스가 한 팀에 몰리는 일은 막을 수 있습니다.</li>
<li><strong>결석자는 미리 빼세요.</strong> 배정 후 빠지면 팀 인원이 어긋납니다.</li>
<li><strong>결과는 공유 버튼으로 남기세요.</strong> 카톡·WhatsApp 등으로 팀 명단과 결과 링크(열면 같은 배정이 그대로 보입니다)를 보내 두면 나중에 "나 저 팀 아니었는데" 같은 분쟁을 막아 줍니다. 처음부터 다 같이 보고 싶다면 [같이 보기]로 링크를 보내 각자 폰에서 뽑는 장면을 함께 보세요.</li>
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
         "네. 균형 모드를 '티어 밸런스'로 바꾸고 참가자마다 T1·T2·T3을 지정하면, 높은 티어부터 각 팀에 한 명씩 돌아가며 배정됩니다. 같은 티어 안에서의 순서는 무작위라 누가 어느 팀에 갈지는 여전히 운에 맡겨집니다."),
        ("같은 사람들끼리 계속 같은 팀이 되는데요?",
         "매번 독립적으로 섞기 때문에 우연히 반복될 수 있습니다. 인원이 적을수록 같은 조합이 다시 나올 확률은 낮지 않습니다."),
        ("명단을 저장해 둘 수 있나요?",
         "최근에 쓴 명단 5개는 자동으로 이 브라우저에만 저장되어 다음에 한 번에 불러올 수 있고, 서버로 전송되지 않습니다. 로그인하면 이름을 붙인 그룹으로 저장해 다른 기기에서도 불러올 수 있습니다."),
    ],
    "footer": '순서까지 정해야 한다면 <a href="/games/ladder/">사다리타기</a>, 한 명만 뽑을 거라면 <a href="/games/roulette/">룰렛</a>이 더 빠릅니다.',
}

CONTENT["lotto"] = {
    "h2": "로또 번호 추첨기 — 더 알아보기",
    "sub": "Lotto Number Generator — 무작위 번호 조합을 만들어 주는 도구",
    "blocks": [
        ("🎯 사용 방법", """<p>이 도구는 정해진 범위 안에서 <strong>중복 없는 번호 조합을 무작위로 뽑아 주는 생성기</strong>입니다. 한국 로또 6/45·Powerball·双色球·ロト6/ロト7·Mega-Sena 등 16개 나라 18가지 로또 형식(번호 범위·뽑는 개수·보너스볼)을 프리셋으로 제공하며, 한 번에 여러 세트를 만들 수도 있습니다. 추첨은 실제 방송 추첨기처럼 공기로 공을 섞다가 밸브가 열리면 공 하나가 튜브로 빨려 올라가 레일을 타고 진열대에 놓이는 방식으로 연출됩니다.</p>
<ol>
<li><strong>형식 선택</strong> — 국가별 프리셋을 고르거나 번호 범위(최대 999)·뽑는 개수(최대 20개)·보너스볼(최대 5개)을 직접 지정합니다.</li>
<li><strong>세트 수 지정</strong> — 1~10세트까지 한 번에 생성할 수 있습니다.</li>
<li><strong>속도 선택</strong> — 추첨 연출을 보고 싶으면 빠르게·보통·느리게, 바로 결과만 원하면 즉시 모드를 고릅니다.</li>
<li><strong>기록 확인</strong> — 이번 방문에서 뽑은 조합은 옆 목록에 최근 30건까지 보이고 새로고침하면 사라집니다. 남겨 두고 싶은 조합은 결과 화면의 ⭐로 저장하면 이 브라우저의 '내 이력'에 보관됩니다.</li>
<li><strong>같이 보기</strong> — [방 만들기]로 링크를 보내면 친구들이 각자 폰에서 같은 순간 같은 공이 뽑히는 장면을 봅니다(방 정원 12명). 방장 혼자 번호를 정할 수 없도록 참가자 모두의 난수를 섞어 번호를 정하고, 결과 링크로 누구나 다시 검증할 수 있습니다.</li>
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
         "옆 목록의 최근 30건은 이번 방문 동안만 보이고 새로고침하면 사라집니다. 결과 화면에서 ⭐를 눌러 저장한 조합만 이 브라우저의 '내 이력'에 남으며, 서버로 전송되지 않고 브라우저 저장소를 지우면 사라집니다."),
        ("몇 세트까지 한 번에 만들 수 있나요?",
         "1회에 최대 10세트까지 생성할 수 있습니다. 즉시 모드를 쓰면 연출 없이 바로 결과가 나옵니다."),
    ],
    "footer": '이 도구는 오락용 번호 생성기이며 당첨을 보장하거나 예측하지 않습니다. 구매는 본인의 판단과 책임입니다. 다른 추첨 도구는 <a href="/games/roulette/">룰렛</a>·<a href="/games/bingo/">빙고</a>를 참고하세요.',
}

CONTENT["bingo"] = {
    "h2": "빙고 — 더 알아보기",
    "sub": "Bingo — 경품 추첨과 모임 진행에 쓰는 고전 추첨 게임",
    "blocks": [
        ("🎯 사용 방법", """<p>빙고는 격자판의 숫자가 하나씩 호명될 때마다 지워 나가다가, 가로·세로·대각선 줄을 먼저 완성하면 이기는 게임입니다. 규칙이 단순해 <strong>나이와 상관없이 바로 참여</strong>할 수 있어 행사 진행에 자주 쓰입니다. 이 페이지에서는 진행자(방장)가 황동 케이지를 돌려 번호를 뽑고, 참가자는 각자 폰에서 자기 카드를 받습니다.</p>
<ol>
<li><strong>판 크기 선택</strong> — 3×3(1–30)·4×4(1–40)·5×5(미국식 1–75)·6×6(1–90) 네 가지. 홀수 판(3×3·5×5)은 가운데가 FREE 칸입니다.</li>
<li><strong>뽑기 방식</strong> — 레버를 직접 당기는 수동, 1~30초 간격으로 저절로 뽑는 자동, 그리고 종이 빙고판을 쓰는 자리를 위한 📋 오프라인(카드 없이 번호 호출만) 중에서 고릅니다.</li>
<li><strong>방 만들기</strong> — [방 만들기]로 초대 링크를 보내면 친구들이 로그인 없이 닉네임만으로 들어와 자기 폰에서 카드를 받습니다(방 정원 12명). 방장은 같이 참가하거나 진행만 맡을 수 있고, 시작 뒤에 들어온 사람은 그 판을 관전하다 다음 판부터 카드를 받습니다.</li>
<li><strong>승리 조건</strong> — 성공 줄 수(5×5 기준 최대 12줄)와 당첨자 수를 정합니다. 호명된 번호는 카드에 자동으로 표시되고, 한 칸만 남은 줄은 금색 점선으로 알려 주며, 줄이 완성되면 자동으로 빙고가 선언됩니다.</li>
</ol>"""),
        ("📐 빙고판의 구조 — 열마다 정해진 번호대", """<p>빙고 카드는 아무 숫자나 흩뿌린 판이 아닙니다. 열마다 쓸 수 있는 <strong>번호대가 정해져 있습니다</strong>. 미국식 5×5에서는 B열이 1–15, I열이 16–30, N열이 31–45, G열이 46–60, O열이 61–75이고, 이 도구의 다른 판도 같은 방식으로 3×3·4×4는 열마다 10개씩, 6×6은 15개씩 번호대를 나눕니다. 그래서 진행자가 "B-7"처럼 글자와 함께 부르면 참가자는 해당 열만 훑으면 되어 진행이 빨라집니다.</p>
<p>판 크기는 곧 게임 길이입니다. 3×3은 줄이 짧고 후보 번호도 30개뿐이라 몇 분 안에 승부가 나고, 6×6은 FREE 칸도 없고 한 줄에 여섯 칸이 필요해 가장 오래갑니다. 짧은 쉬는 시간에는 3×3이나 4×4, 본 행사에는 5×5를 고르는 식으로 시간에 맞춰 고르면 됩니다.</p>"""),
        ("💡 진행을 매끄럽게 하는 요령", """<ul>
<li><strong>화면을 크게 띄우세요.</strong> 행사장이라면 진행자 화면을 프로젝터에 띄우고, 참가자는 각자 폰으로 카드를 보게 하면 좋습니다.</li>
<li><strong>종이 카드가 있다면 오프라인 모드.</strong> 인쇄한 빙고판을 쓰는 자리에서는 번호 호출과 호출판만 쓰면 되어 인원 제한 없이 진행할 수 있습니다.</li>
<li><strong>경품은 등수별로 미리 공개하세요.</strong> 무엇을 걸고 하는지 알면 집중도가 올라갑니다.</li>
<li><strong>호명 속도를 조절하세요.</strong> 수동 모드로 초반은 빠르게, 줄이 차오르면 천천히 뽑아야 긴장감이 삽니다. 손이 부족하면 자동 간격을 4~6초로 두세요.</li>
<li><strong>중복 호명은 자동으로 걸러집니다.</strong> 뽑힌 공은 케이지에서 빠지고 호출판에 불이 들어오니 따로 표시할 필요가 없어요.</li>
</ul>"""),
        ("🌟 이럴 때 씁니다", """<ul class="lp-use-cases">
<li>🎁 <strong>경품 추첨</strong> — 사내 행사·연말 모임</li>
<li>🏫 <strong>수업 활동</strong> — 숫자 듣기·셈 연습 게임</li>
<li>🎪 <strong>워크숍 아이스브레이킹</strong> — 처음 만난 사람들</li>
<li>👨‍👩‍👧 <strong>가족 모임</strong> — 명절·생일 파티</li>
<li>💒 <strong>결혼식·돌잔치</strong> — 하객 참여 이벤트</li>
<li>📺 <strong>온라인 방송</strong> — 시청자 참여 추첨</li>
</ul>"""),
    ],
    "faq": [
        ("몇 명까지 함께할 수 있나요?",
         "폰으로 카드를 받는 온라인 방은 방장을 포함해 12명까지입니다. 그보다 많은 인원이라면 종이 빙고판을 나눠 주고 📋 오프라인 모드로 번호만 호출하면 인원 제한 없이 진행할 수 있습니다."),
        ("판 크기는 어떻게 고르나요?",
         "시간이 짧으면 3×3(1–30)이나 4×4(1–40), 행사에서 정식으로 하려면 미국식 5×5(1–75), 길게 끌고 싶으면 6×6(1–90)이 적당합니다."),
        ("숫자 말고 다른 걸 넣어도 되나요?",
         "아니요. 이 빙고는 숫자 전용이며 카드는 열마다 정해진 번호대에서 자동으로 만들어집니다. 이름이나 단어 중 하나를 뽑고 싶다면 룰렛이나 사다리타기가 더 맞습니다."),
        ("이미 뽑힌 번호가 또 나오나요?",
         "나오지 않습니다. 뽑힌 공은 케이지에서 빠지고 호출판에 표시되므로 중복을 따로 관리할 필요가 없습니다."),
        ("방장이 번호를 마음대로 고를 수 있나요?",
         "온라인 방에서는 고를 수 없습니다. 방장이 시작 전에 호출 순서의 열쇠를 봉인해 두고 참가자들의 난수가 섞인 뒤에야 순서가 정해지며, 매 호출이 공개될 때마다 모두의 기기가 즉시 검증합니다. 끝나면 결과 링크로 누구나 다시 계산해 볼 수 있습니다."),
        ("여러 명이 동시에 빙고가 되면 어떻게 하나요?",
         "당첨자 수를 미리 정해 두면 그 인원이 찰 때까지 게임이 이어지고, 순위와 몇 번째 뽑기에서 달성했는지가 기록됩니다. 1명으로 두었다면 공동 우승으로 할지 다음 줄로 가릴지 시작 전에 합의해 두세요."),
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
CONTENT.update(_load("game_about_content_5", "CONTENT_5"))  # 2026-08-20 풍선 룰렛
CONTENT.update(_load("game_about_content_7", "CONTENT_7"))  # 2026-08-22 궤도 연구소
CONTENT.update(_load("game_about_content_8", "CONTENT_8"))  # 2026-09-25 버블 버스트
CONTENT.update(_load("game_about_content_ludo", "CONTENT_LUDO"))  # 2026-09-25 루도
CONTENT.update(_load("game_about_content_reversi", "CONTENT_REVERSI"))  # 2026-09-25 리버시
CONTENT.update(_load("game_about_content_yut", "CONTENT_YUT"))  # 2026-09-25 윷놀이
CONTENT.update(_load("game_about_content_gummy", "CONTENT_GUMMY"))  # 2026-09-25 구미 체인
CONTENT.update(_load("game_about_content_prism_hex", "CONTENT_PRISM_HEX"))  # 2026-09-25 프리즘 헥스
CONTENT.update(_load("game_about_content_mahjong_solitaire", "CONTENT_MAHJONG_SOLITAIRE"))  # 2026-09-27 마작 솔리테어
CONTENT.update(_load("game_about_content_mahjong_tw", "CONTENT_MAHJONG_TW"))  # 2026-09-27 대만 마작 台灣麻將
CONTENT.update(_load("game_about_content_yacht", "CONTENT_YACHT"))  # 2026-09-30 요트 다이스
CONTENT.update(_load("game_about_content_omok", "CONTENT_OMOK"))  # 2026-10-01 오목
CONTENT.update(_load("game_about_content_lots", "CONTENT_LOTS"))  # 2026-10-01 긁는 제비뽑기

# 600단어 미달 게임 보강 블록 — 각 게임의 blocks 뒤(FAQ 앞)에 덧붙인다.
for _k, _extra in _load("game_about_content_4", "EXTRA_BLOCKS").items():
    if _k in CONTENT:
        CONTENT[_k]["blocks"] = list(CONTENT[_k]["blocks"]) + list(_extra)

# 2차 보강 (2026-08-20) — 홈 노출 3종만. AdSense 재신청 전 thin 리스크 제거.
for _k, _extra in _load("game_about_content_6", "EXTRA_BLOCKS_6").items():
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
    /* (2026-08-20 사고 수정) body 가 고정 높이 flex 컬럼 + overflow:hidden 인
       게임(brick·tetris·lucky-merge·starship-lander)에서는 이 섹션의 큰
       margin 이 flex 컨테이너를 넘치게 해 형제인 게임 영역이 flex-shrink 로
       짓눌린다 — 벽돌깨기 캔버스가 4×4px 가 됐다. 그런 레이아웃에서는 밀기
       자체를 포기한다(섹션은 어차피 overflow:hidden 아래라 이전부터 화면에
       안 보였고, DOM 텍스트는 색인된다). */
    var bs = getComputedStyle(document.body);
    if (bs.display === 'flex' &&
        ((bs.overflowY || '').indexOf('hidden') !== -1 || (bs.overflow || '').indexOf('hidden') !== -1)) {
      /* margin 0 으로는 부족하다 — 섹션 자체 높이(~2900px)가 flex 아이템으로
         컨테이너를 넘치게 해 게임 영역이 여전히 짓눌렸다(실측: 벽돌깨기
         캔버스 4×4px, about 제거 시 364×524 회복). absolute 로 흐름에서
         완전히 빼서 화면 아래(top:100%)에 둔다 — overflow:hidden 이라
         이전과 동일하게 비가시이고, DOM 텍스트는 그대로 색인된다. */
      el.style.marginTop = '0px';
      el.style.position = 'absolute';
      el.style.top = '100%';
      el.style.left = '0';
      return;
    }
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


USE_LI = re.compile(r'<li>\s*([^\s<]+)\s*<strong>(.*?)</strong>\s*(?:&mdash;|—|-)?\s*(.*?)</li>', re.S)


def quick_cards(data):
    """'이럴 때 씁니다' li 에서 상위 3개를 뽑아 시각 카드로 만든다.

    새 집필 없이 기존 콘텐츠를 재사용한다 — 스크롤해 내려온 사람이
    글을 읽기 전에 '언제 쓰는 도구인가'를 아이콘으로 먼저 파악하게 한다.
    li 형식이 다르면(추출 실패) 카드를 생략하고 조용히 넘어간다."""
    for _h3, body in data["blocks"]:
        if 'lp-use-cases' not in body:
            continue
        items = USE_LI.findall(body)[:3]
        if len(items) < 3:
            continue
        cards = []
        for ico, title, desc in items:
            desc = re.sub(r'<[^>]+>', '', desc).strip()
            cards.append(
                '      <div class="lp-quick-card"><span class="lp-quick-ico">{}</span>'
                '<span class="lp-quick-txt"><span class="lp-quick-t">{}</span>'
                '<span class="lp-quick-d">{}</span></span></div>'.format(ico, title, desc))
        return ['    <div class="lp-quick">'] + cards + ['    </div>']
    return []


def build_section(data):
    p = ['<!--lp-game-about:start-->', CSS,
         '<section class="lp-game-about" aria-label="About this game" lang="ko">',
         '  <div class="lp-about-inner">',
         '    <header class="lp-about-head">',
         '      <h2>{}</h2>'.format(data["h2"]),
         '      <p class="lp-about-sub">{}</p>'.format(data["sub"]),
         '    </header>']
    p += quick_cards(data)
    # 본문은 전부 접는다 (2026-08-21 운영자 원칙) — 닫힌 상태에서 보이는
    # 것은 제목 줄뿐. 구글은 아코디언 안 콘텐츠를 정상 색인하므로 색인
    # 가치는 그대로이고, 사람이 만나는 글자 수만 줄어든다. FAQ 는 접기로
    # 감싸되 dl.lp-faq 마크업을 유지해야 sync-faq-schema.py 와 FAQPage
    # 1:1 대응이 깨지지 않는다.
    for h3, body in data["blocks"]:
        p += ['    <details class="lp-about-block">',
              '      <summary>{}</summary>'.format(h3),
              '      <div class="lp-fold-body">', body, '      </div>',
              '    </details>']
    p += ['    <details class="lp-about-block">',
          '      <summary>❓ 자주 묻는 질문</summary>',
          '      <div class="lp-fold-body">',
          '      <dl class="lp-faq">']
    for q, a in data["faq"]:
        p += ['        <dt>Q. {}</dt>'.format(q), '        <dd>{}</dd>'.format(a)]
    p += ['      </dl>', '      </div>', '    </details>',
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
    # 인자로 게임 id 를 주면 그 게임만 주입한다 — 다른 게임 파일을 동시에 고치는 중일 때
    # 전체를 다시 쓰면 남의 작업을 덮을 수 있다 (예: python scripts/inject-game-about.py bubble)
    only = set(sys.argv[1:])
    changed = 0
    for key, data in CONTENT.items():
        if only and key not in only:
            continue
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
