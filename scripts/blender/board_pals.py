# -*- coding: utf-8 -*-
"""보드게임 캐릭터 — 루도 말 4종 · 리버시 레서판다 가족 4명 (2026-09-30).

윷놀이 말(yut_pieces.py)의 모델·스튜디오·표정 8종을 그대로 가져다 쓴다(같은 장난감 화풍 —
마스코트는 새로 만들지 않고 같은 Blender 모델을 쓴다는 원칙). 이 파일은 yut_pieces 를 모듈로 불러
  · 루도  : 받침·리본 색만 루도 네 색(빨·초·노·파)으로 바꾼다.
            빨강 = 레서판다 · 초록 = 랙돌 고양이 · 노랑 = 사막여우 · 파랑 = 수달
  · 리버시: 레서판다 한 종에 소품을 얹어 가족 넷을 만든다. 받침은 흑백 리버시 돌.
            kong  콩이(막내)   = 머리 위 새싹      — 쉬움
            dan   단풍(누나)   = 분홍 리본         — 보통
            dad   아빠         = 동그란 안경       — 어려움
            guru  할아버지     = 흰 눈썹 · 흰 수염 — 고수
표정 8종(n b h s x o c w)은 yut_pieces 와 같다.

실행:
  blender -b -P scripts/blender/board_pals.py -- ludo            # 4종 × 8표정
  blender -b -P scripts/blender/board_pals.py -- reversi         # 가족 4 × 8표정
  blender -b -P scripts/blender/board_pals.py -- reversi dad:n,x # 일부만
환경: BP_OUT(출력 폴더, 기본 scripts/og-assets) · YP_RES · YP_SAMPLES (yut_pieces 와 같은 키)
출력: <BP_OUT>/ludo/<sp>-<ex>.png · <BP_OUT>/reversi/<who>-<ex>.png
      → scripts/blender/board_pals_atlas.py 가 public/assets/<game>/pals.webp 로 묶는다.
"""
import bpy
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yut_pieces as yp   # noqa: E402

OUT = os.environ.get('BP_OUT') or os.path.join(HERE, "..", "og-assets")

LUDO_TEAM = {
    'panda': (0.90, 0.10, 0.16),   # 빨강
    'cat': (0.07, 0.62, 0.26),     # 초록
    'fox': (0.98, 0.64, 0.04),     # 노랑
    'otter': (0.08, 0.38, 0.95),   # 파랑
}
FAMILY = ['kong', 'dan', 'dad', 'guru']
BOW = {
    'kong': (0.16, 0.80, 0.58),
    'dan': (0.98, 0.34, 0.56),
    'dad': (0.12, 0.26, 0.72),
    'guru': (0.55, 0.30, 0.95),
}


def render_ludo(sp, ex):
    yp.TEAM.update(LUDO_TEAM)
    sc = yp.studio()
    yp.BUILD[sp](ex)
    d = os.path.join(OUT, "ludo")
    os.makedirs(d, exist_ok=True)
    sc.render.filepath = os.path.join(d, "%s-%s.png" % (sp, ex))
    bpy.ops.render.render(write_still=True)
    print("RENDERED ludo", sp, ex)


def disc_base(sp):
    """리버시 돌 받침 — 위는 흰 면, 아래는 검은 면. 리본 색 재질을 돌려준다."""
    tc = yp.mat('team_' + sp, yp.TEAM[sp], rough=0.25, coat=0.8)
    white = yp.mat('disc_w', (0.97, 0.96, 0.92), rough=0.18, coat=1.0)
    black = yp.mat('disc_b', (0.035, 0.035, 0.045), rough=0.16, coat=1.0)
    yp.cyl(0.66, 0.11, (0, 0, 0.055), black, bevel=0.045)
    yp.cyl(0.66, 0.11, (0, 0, 0.165), white, bevel=0.045)
    return tc


def accessories(who, ex):
    H = yp.Head(yp.HEAD_C, yp.HA + 0.02, yp.HB, yp.HC - 0.02)
    top = H.c.z + H.cc
    if who == 'kong':
        # 새싹 — 줄기 + 잎 두 장
        stem = yp.mat('sprout_stem', (0.30, 0.62, 0.16), rough=0.4)
        leaf = yp.mat('sprout_leaf', (0.36, 0.80, 0.22), rough=0.35, coat=0.6)
        yp.capsule((0, -0.08, top - 0.04), (0.02, -0.1, top + 0.2), 0.035, stem)
        for s in (-1, 1):
            o = yp.sph(0.2, (s * 0.17, -0.1, top + 0.27), leaf, scale=(1.0, 0.34, 0.5))
            o.rotation_euler = (0, -s * math.radians(28), 0)
    elif who == 'dan':
        # 분홍 리본 — 머리 왼쪽 위(화면 기준 오른쪽 귀 앞)
        pink = yp.mat('bow_pink', (1.0, 0.36, 0.58), rough=0.3, coat=0.7)
        p, n = H.pt(0.4, 0.5, 0.07)
        for s in (-1, 1):
            o = yp.sph(0.22, (p.x + s * 0.21, p.y - 0.03, p.z + s * 0.045), pink, scale=(1.0, 0.5, 0.8))
            o.rotation_euler = (0, -s * math.radians(14) - math.radians(14), 0)
        yp.sph(0.1, (p.x, p.y - 0.08, p.z), yp.mat('bow_knot', (0.92, 0.22, 0.46), rough=0.3, coat=0.7))
    elif who == 'dad':
        # 동그란 안경 — 눈(±0.31, 0) 둘레
        rim = yp.mat('glass_rim', (0.10, 0.09, 0.12), rough=0.25, coat=0.8)
        cs = []
        for s in (-1, 1):
            p, n = H.pt(s * 0.31, 0.0, 0.085)
            t = yp.torus(0.245, 0.026, p, rim)
            t.rotation_mode = 'QUATERNION'
            t.rotation_quaternion = yp.Vector((0, 0, 1)).rotation_difference(n)
            cs.append(p)
        a, _ = H.pt(-0.075, 0.03, 0.1)
        b, _ = H.pt(0.075, 0.03, 0.1)
        yp.capsule(a, b, 0.022, rim)
    elif who == 'guru':
        # 흰 눈썹(복슬) + 흰 수염
        wool = yp.mat('guru_wool', (0.99, 0.98, 0.95), rough=0.55, coat=0.15, sheen=0.5)
        for s in (-1, 1):
            for k, (dx, dz, r) in enumerate(((0.0, 0.0, 0.1), (0.13, -0.035, 0.085), (0.24, -0.09, 0.065))):
                yp.feat(H, s * (0.24 + dx), 0.31 + dz, r, wool, scale=(1.25, 0.5, 0.8), lift=0.02)
        # 콧수염 — 주둥이 양옆으로 늘어진 두 갈래
        for s in (-1, 1):
            for (dx, dz, r) in ((0.13, -0.36, 0.085), (0.23, -0.45, 0.075), (0.3, -0.56, 0.06)):
                yp.feat(H, s * dx, dz, r, wool, scale=(1.1, 0.6, 1.0), lift=0.03)
        # 턱수염 — 턱 밑에서 리본 앞으로 길게
        for (z, y, r, sx) in ((0.93, -0.5, 0.19, 1.15), (0.78, -0.57, 0.16, 1.0), (0.64, -0.6, 0.12, 0.95), (0.53, -0.6, 0.08, 0.9)):
            yp.sph(r, (0, y, z), wool, scale=(sx, 0.75, 1.1))


def render_reversi(who, ex):
    yp.TEAM['panda'] = BOW[who]
    orig = yp.base
    yp.base = disc_base
    try:
        sc = yp.studio()
        yp.panda(ex)
        accessories(who, ex)
    finally:
        yp.base = orig
    d = os.path.join(OUT, "reversi")
    os.makedirs(d, exist_ok=True)
    sc.render.filepath = os.path.join(d, "%s-%s.png" % (who, ex))
    bpy.ops.render.render(write_still=True)
    print("RENDERED reversi", who, ex)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    mode = argv[0] if argv else 'ludo'
    rest = argv[1:]
    if mode == 'ludo':
        for a in (rest or yp.SPECIES):
            sp, _, exs = a.partition(':')
            for ex in (exs.split(',') if exs else yp.EXPRS):
                render_ludo(sp, ex)
    elif mode == 'reversi':
        for a in (rest or FAMILY):
            who, _, exs = a.partition(':')
            for ex in (exs.split(',') if exs else yp.EXPRS):
                render_reversi(who, ex)
