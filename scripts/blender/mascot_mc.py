# -*- coding: utf-8 -*-
"""luckyplz 마스코트 레서판다 — 추첨 쇼 진행자(MC) 포즈 세트 (2026-09-30, 룰렛·주사위 대개편).

룰렛·주사위의 '작은 쇼'를 진행하는 레서판다. 모델·표정·스튜디오는 mascot_panda.py(→ yut_pieces.py)를
그대로 import 해서 쓰고, 여기서는 포즈와 소품(마이크)만 더한다 — 같은 얼굴이어야 사이트 마스코트로 기억된다.
mascot_panda.py / yut_pieces.py 는 수정하지 않는다.

## 포즈 (MC_FRAMES)
  mc_idle    마이크를 들고 서 있음(기본)               mc_blink   눈 깜빡
  mc_talk    마이크를 입에 대고 한 손을 펼침(시작!)       mc_watch   판을 올려다봄(도는 중)
  mc_tense   두 손으로 마이크를 꼭 쥐고 식은땀(막판)      mc_gasp    걱정스레 올려다봄(넘을까 말까)
  mc_win     마이크 든 손을 번쩍 + 별눈(당첨 발표)        mc_cheer   만세(축하)
  mc_aww     울상(꽝·벌칙 — 주사위 패자 위로)            mc_point   옆(화면 왼쪽)을 가리키며 윙크

실행:
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_mc.py               # 전부
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_mc.py -- mc_win      # 일부
  MP_SAMPLES=24 MP_RES=256 … 로 시안 확인
출력: scripts/og-assets/mascot_mc/<frame>.png → python scripts/blender/build_flagship_mascot.py
      → public/assets/roulette/panda-mc.webp · public/assets/dice/panda-mc.webp (같은 파일, 게임 독립 원칙으로 각자 보관)
"""
import bpy
import math
import os
import sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mascot_panda as mp  # noqa: E402  (포즈 조립·스튜디오 — 수정하지 않고 쓴다)

yp = mp.yp
OUTDIR = os.path.join(HERE, "..", "og-assets", "mascot_mc")
os.makedirs(OUTDIR, exist_ok=True)

# 진행자는 관객(정면)을 본다 — 버블 발사대 쪽으로 틀던 YAW 를 거의 정면으로
mp.YAW = -0.06

REST_L = (-0.2, -0.48, 0.5)
MIC_LOW = (0.34, -0.6, 0.62)      # 마이크를 가슴 앞에 든 오른손(화면 왼쪽)
MIC_MOUTH = (0.24, -0.7, 0.9)     # 입 앞
MIC_HIGH = (0.98, -0.34, 1.5)     # 번쩍

MC_FRAMES = {
    'mc_idle':  (mp.fr('n', (MIC_LOW, REST_L)), 'low'),
    'mc_blink': (mp.fr('b', (MIC_LOW, REST_L)), 'low'),
    'mc_talk':  (mp.fr('h', (MIC_MOUTH, (-0.98, -0.4, 1.0)), hfwd=-0.04, roll=-0.04), 'mouth'),
    'mc_watch': (mp.fr('l', (MIC_LOW, REST_L), hfwd=-0.22, hroll=-0.08), 'low'),
    'mc_tense': (mp.fr('v', ((0.12, -0.7, 0.8), (-0.12, -0.7, 0.74)), droop=0.4, fwd=0.05), 'two'),
    'mc_gasp':  (mp.fr('u', ((0.14, -0.7, 0.82), (-0.14, -0.7, 0.76)), hfwd=-0.2, droop=0.3), 'two'),
    'mc_win':   (mp.fr('x', (MIC_HIGH, (-0.98, -0.34, 1.22)), hfwd=-0.06,
                       feet=((0.32, -0.06, 0.07), (-0.32, -0.06, 0.07))), 'high'),
    'mc_cheer': (mp.fr('h', ((1.06, -0.3, 1.62), (-1.06, -0.3, 1.62)), hfwd=-0.08,
                       feet=((0.32, -0.06, 0.07), (-0.32, -0.06, 0.07))), 'up'),
    'mc_aww':   (mp.fr('c', ((0.3, -0.56, 0.56), (-0.26, -0.62, 0.86)), droop=1.0, hfwd=0.08), 'low'),
    'mc_point': (mp.fr('w', (MIC_LOW, (-1.04, -0.42, 1.1)), roll=-0.07, hroll=-0.08), 'low'),
}
ORDER = ['mc_idle', 'mc_blink', 'mc_talk', 'mc_watch', 'mc_tense', 'mc_gasp', 'mc_win', 'mc_cheer', 'mc_aww', 'mc_point']


def mic(hand, mode):
    """마이크 — 손 위치(월드)에서 위(또는 입 쪽)로 뻗는 검은 손잡이 + 은색 망 머리 + 금띠."""
    body = yp.mat('mic_body', (0.05, 0.05, 0.07), rough=0.28, coat=0.8)
    head = yp.mat('mic_head', (0.78, 0.80, 0.86), rough=0.22, metal=0.55, coat=0.6)
    gold = yp.mat('mic_gold', (1.0, 0.72, 0.18), rough=0.2, metal=0.5, coat=0.8)
    if mode == 'mouth':
        d = Vector((-0.22, -0.1, 0.62)).normalized()
    elif mode == 'two':
        d = Vector((0.0, -0.12, 1.0)).normalized()
    elif mode == 'high':
        d = Vector((0.3, -0.1, 1.0)).normalized()
    elif mode == 'up':
        d = Vector((0.2, -0.1, 1.0)).normalized()
    else:
        d = Vector((-0.1, -0.16, 1.0)).normalized()
    a = hand - d * 0.16
    b = hand + d * 0.3
    yp.capsule(a, b, 0.062, body)
    yp.capsule(b - d * 0.02, b + d * 0.04, 0.074, gold)
    yp.sph(0.16, b + d * 0.17, head, seg=36)


def render_frame(name):
    spec, mode = MC_FRAMES[name]
    mp.FRAMES[name] = spec
    sc = mp.studio()
    _, ZM, Hm, _ = mp.build_frame(name)
    if mode == 'two':
        hand = ZM @ ((Vector(spec['R']) + Vector(spec['L'])) / 2 + Vector((0, -0.05, 0.02)))
    else:
        hand = ZM @ (Vector(spec['R']) + Vector((0, -0.03, 0.0)))
    mic(hand, mode)
    sc.render.filepath = os.path.join(OUTDIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = argv[0].split(',') if argv else ORDER
    for n in names:
        render_frame(n)
