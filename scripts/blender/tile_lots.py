# -*- coding: utf-8 -*-
"""긁는 제비뽑기 홈 타일 — '레트로 장난감 진열장' 한 벌(tiles_toybox.py)과 같은 스튜디오·재질·외곽선으로 찍는다 (2026-10-01).

tiles_toybox.py 는 다른 작업이 함께 고치는 파일이라 건드리지 않고(tile_omok.py 와 같은 방식) 그 도우미를 가져다 쓴다.
장면: 부채꼴로 세운 장난감 제비 카드 세 장(빨강·파랑·초록 띠 + 은박 창), 맨 앞 카드는 은박이 반쯤 긁혀
금빛 당첨 별이 드러나 있고, 앞에 커다란 금화가 기대 서 있다. 바닥엔 긁어낸 은박 부스러기.

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/tile_lots.py
출력: scripts/og-assets/tiles3d/lots.png (1000×1000 투명) → python scripts/build_tiles.py lots → public/assets/tiles/toy-lots.webp
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import tiles_toybox as TB  # noqa: E402

R = math.radians


def lots_toy():
    random.seed(7)
    g = TB.group("lots", R(-12), loc=(0.02, 0.05, 0))
    PAPER = TB.mat('lpaper', (0.97, 0.92, 0.80), rough=0.35, coat=0.55)
    FOIL = TB.mat('lfoil', (0.60, 0.63, 0.70), rough=0.26, metal=0.9, coat=0.35)
    FOIL_D = TB.mat('lfoild', (0.30, 0.32, 0.38), rough=0.35, metal=0.6, coat=0.2)
    GOLDP = TB.mat('lgoldp', (1.0, 0.74, 0.16), rough=0.25, coat=0.6, emit=(1.0, 0.7, 0.2), estr=0.25)
    RED = TB.mat('lred', (0.86, 0.10, 0.12), rough=0.3, coat=0.6)
    INK = TB.mat('link', (0.98, 0.86, 0.45), rough=0.4, coat=0.2)
    bands = [TB.P('green'), TB.P('cobalt'), TB.P('tomato')]
    W, H, T = 1.22, 1.72, 0.1

    def card(name, loc, rz, rx, band, front):
        c = TB.group(name, 0, loc=loc)
        c.parent = g
        c.rotation_euler = (R(rx), 0, R(rz))
        TB.box((W, T, H), (0, 0, H / 2), PAPER, bevel=0.07, parent=c)
        TB.box((W + 0.01, T + 0.03, H * 0.32), (0, -0.004, H - H * 0.16), band, bevel=0.07, parent=c)
        # 띠의 '구멍(노치)' — 종이 쪽 양옆 작은 반원 대신 금색 점선 느낌의 작은 원 3개
        for k in range(5):
            TB.cyl(0.022, 0.02, (-W * 0.36 + k * W * 0.18, -T / 2 - 0.006, H * 0.66), INK, rot=(R(90), 0, 0), bevel=0.0, verts=14, parent=c)
        wx, wz, ww, wh = 0.0, H * 0.31, W * 0.8, H * 0.44
        if not front:
            TB.box((ww, 0.04, wh), (wx, -T / 2 - 0.012, wz), FOIL, bevel=0.03, parent=c)
            TB.text("?", 0.42, (wx - 0.1, -T / 2 - 0.036, wz - 0.17), FOIL_D, extrude=0.012, parent=c)
            return c
        # 맨 앞 카드 — 왼쪽 은박이 남고 오른쪽은 긁혀 금빛 당첨판 + 붉은 별
        TB.box((ww, 0.02, wh), (wx, -T / 2 - 0.006, wz), GOLDP, bevel=0.03, parent=c)
        star = TB.prism(TB.star_pts(0.27, 0.12), 0.05, (wx + 0.12, -T / 2 - 0.03, wz + 0.02), RED, parent=c)
        lw = ww * 0.42
        TB.box((lw, 0.045, wh), (wx - ww / 2 + lw / 2, -T / 2 - 0.02, wz), FOIL, bevel=0.025, parent=c)
        # 긁힌 경계의 들쭉날쭉한 은박 조각
        for k in range(7):
            z = wz - wh / 2 + 0.08 + k * (wh - 0.16) / 6
            TB.sph(0.055 + random.random() * 0.03, (wx - ww / 2 + lw + random.uniform(-0.02, 0.05), -T / 2 - 0.022, z), FOIL,
                   scale=(1, 0.35, 1), parent=c, seg=16)
        # 남은 은박 조각 하나(오른쪽 위 구석)
        TB.box((0.16, 0.045, 0.12), (wx + ww / 2 - 0.1, -T / 2 - 0.02, wz + wh / 2 - 0.08), FOIL, rot=(0, R(8), 0), bevel=0.02, parent=c)
        return c

    card("c0", (-0.62, 0.42, 0.06), 16, -14, bands[0], False)
    card("c1", (0.5, 0.36, 0.04), -14, -14, bands[1], False)
    card("c2", (-0.05, -0.05, 0.02), 2, -10, bands[2], True)
    # 금화 — 앞 오른쪽에 비스듬히 기대 선다(긁는 데 쓴 동전)
    coin = TB.group("coin", 0, loc=(0.78, -0.62, 0.43))
    coin.parent = g
    coin.rotation_euler = (R(72), R(-24), R(-30))
    GD = TB.GOLD()
    TB.cyl(0.42, 0.11, (0, 0, 0), GD, bevel=0.03, verts=64, parent=coin)
    TB.torus(0.38, 0.025, (0, 0, 0.056), GD, parent=coin)
    TB.prism(TB.star_pts(0.2, 0.09), 0.03, (0, 0, 0.07), TB.mat('lcoinstar', (1.0, 0.86, 0.4), rough=0.2, metal=1.0, coat=0.0), rot=(0, 0, 0), parent=coin)
    # 바닥의 은박 부스러기
    for k in range(11):
        a = random.uniform(-1.4, 1.2)
        TB.box((random.uniform(0.05, 0.11), random.uniform(0.05, 0.1), 0.012),
               (0.1 + math.cos(a) * random.uniform(0.6, 1.2), -0.6 + math.sin(a) * 0.35 - random.random() * 0.3, 0.01),
               FOIL, rot=(R(random.uniform(-25, 25)), R(random.uniform(-25, 25)), R(random.uniform(0, 180))), bevel=0.0, parent=g)
    # 금빛 별 둘 — 당첨!
    st = TB.mat('lstar', TB.PAL['mustard'], emit=(1.0, 0.75, 0.2), estr=0.45, coat=0.6)
    TB.prism(TB.star_pts(0.2, 0.09), 0.06, (-0.95, -0.3, 1.95), st, parent=g)
    TB.prism(TB.star_pts(0.12, 0.055), 0.05, (0.9, -0.2, 2.05), st, parent=g)
    return g


if __name__ == "__main__":
    sc = TB.studio()
    lots_toy()
    sc.render.filepath = os.path.join(TB.OUTDIR, "lots.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED lots")
