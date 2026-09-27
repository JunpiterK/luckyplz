# -*- coding: utf-8 -*-
"""luckyplz 마스코트 레서판다 — 스타십 착륙(starship-lander) 캡슐 창 조종사 세트 (2026-09-27).

모델·표정·조종복은 mascot_spacez.py 를 그대로 import 한다(수정 없음). 여기서는 색만 바꾼다:
Space-Z 는 시안 트림, 착륙선은 주황 트림(엔진 불꽃·착륙장 조명과 같은 색) — 두 게임이 같은 조종사라는 건
얼굴로 알고, 어느 게임인지는 색으로 안다.

게임은 기체(폭 12px)가 아니라 캔버스 구석의 **원형 캡슐 창(리벳 달린 현창)** 에 이 흉상을 그린다.
표정 쓰임새(게임 코드 PILOT 표):
  focus 평상시 · blink · lookL/lookR 회전 중 · scared 빠른 하강/지면 코앞 · worry 저연료·땀
  cheer 착륙 성공 · happy GOOD · dizzy 추락 · cry(미사용 여분) · salute 시작 화면 · ouch 강한 착지

실행:
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_lander.py [-- focus,cheer]
출력: scripts/og-assets/pilot_starship-lander/<frame>.png → python scripts/build_pilot_atlas.py starship-lander
      → public/assets/starship-lander/pilot.webp
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mascot_spacez as ms   # noqa: E402

LANDER = dict(
    name='starship-lander',
    suit=(0.94, 0.94, 0.95),
    trim=(1.0, 0.5, 0.12),       # 엔진 불꽃 주황
    badge=(0.35, 0.8, 1.0),
)

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ms.render_set(LANDER, argv[0].split(',') if argv else None)
