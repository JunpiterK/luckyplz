# -*- coding: utf-8 -*-
"""오목 홈 타일 — '레트로 장난감 진열장' 한 벌(tiles_toybox.py)과 같은 스튜디오·재질·외곽선으로 찍는다 (2026-10-01).

tiles_toybox.py 는 다른 작업이 함께 고치는 파일이라 건드리지 않고, 그 도우미(studio·mat·P·box·cyl·sph·prism·group·star_pts)를
가져다 쓴다. 장면: 비스듬히 세운 비자나무(榧) 오목판(9줄 장난감 판 — 15줄은 타일 크기에서 격자가 뭉개진다),
대각선으로 이어진 흑 다섯 + 금빛 승리선, 막으러 온 백 몇 알, 앞에서 막 떨어지는 커다란 흑돌 하나.

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/tile_omok.py
출력: scripts/og-assets/tiles3d/omok.png (1000×1000 투명) → python scripts/build_tiles.py omok → public/assets/tiles/toy-omok.webp
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import tiles_toybox as TB  # noqa: E402


def _noline(objs):
    """격자선·화점은 잉크 외곽선에서 뺀다(가는 선에 외곽선이 붙으면 굵은 철망처럼 보인다)."""
    col = bpy.data.collections.get("NOLINE")
    if col is None:
        col = bpy.data.collections.new("NOLINE")
        bpy.context.scene.collection.children.link(col)
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)


def omok_toy():
    g = TB.group("omok", math.radians(-16), loc=(-0.12, 0, 0))
    b = TB.group("board", 0, loc=(-0.04, 0.3, 0))
    b.parent = g
    b.rotation_euler = (math.radians(-26), 0, 0)
    S = 1.92
    KAYA = TB.mat('kaya', (0.76, 0.43, 0.14), rough=0.4, coat=0.35)
    KAYA_D = TB.mat('kayaside', (0.50, 0.26, 0.08), rough=0.5, coat=0.25)
    # 두툼한 판 — 앞면은 비자나무 금빛, 두께는 한 톤 어둡게
    TB.box((S + 0.22, 0.26, S + 0.22), (0, 0.02, S / 2 + 0.11), KAYA_D, bevel=0.07, parent=b)
    TB.box((S + 0.12, 0.03, S + 0.12), (0, -0.115, S / 2 + 0.11), KAYA, bevel=0.012, parent=b)
    n = 9
    m = 0.15
    cs = (S - 2 * m) / (n - 1)
    z0 = 0.11
    LINE = TB.mat('omline', (0.20, 0.10, 0.03), rough=0.6, coat=0.0)
    lines = []
    for k in range(n):
        x = -S / 2 + m + k * cs
        lines.append(TB.box((0.013, 0.006, S - 2 * m + 0.013), (x, -0.132, z0 + S / 2), LINE, bevel=0.0, parent=b))
        lines.append(TB.box((S - 2 * m + 0.013, 0.006, 0.013), (0, -0.132, z0 + m + k * cs), LINE, bevel=0.0, parent=b))
    for (c, r) in [(2, 2), (6, 2), (4, 4), (2, 6), (6, 6)]:
        x, z = -S / 2 + m + c * cs, z0 + m + r * cs
        lines.append(TB.cyl(0.03, 0.008, (x, -0.134, z), LINE, rot=(math.radians(90), 0, 0), bevel=0.0, verts=20, parent=b))
    _noline(lines)

    BK = TB.mat('omblack', (0.02, 0.022, 0.028), rough=0.3, coat=0.6)
    try:   # 넓은 광택이 검은 돌을 회색으로 띄운다 → 반사 세기를 낮춰 '검정'으로
        BK.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.25
    except Exception:
        pass
    WH = TB.mat('omwhite', (0.96, 0.95, 0.91), rough=0.15, coat=1.0)
    sr = cs * 0.47

    def xz(c, r):
        return -S / 2 + m + c * cs, z0 + m + r * cs

    def stone(c, r, black, par):
        x, z = xz(c, r)
        return TB.sph(sr, (x, -0.132 - sr * 0.5, z), BK if black else WH, scale=(1, 0.55, 1), parent=par, seg=36)

    five = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]
    GOLDGLOW = TB.mat('omgold', (1.0, 0.80, 0.28), rough=0.2, coat=0.3, emit=(1.0, 0.72, 0.2), estr=2.2)
    for (c, r) in five:
        stone(c, r, True, b)
        x, z = xz(c, r)
        TB.torus(sr * 1.12, 0.022, (x, -0.14 - sr * 0.3, z), GOLDGLOW, rot=(math.radians(90), 0, 0), parent=b)
    for (c, r) in [(7, 6), (2, 5), (4, 3), (6, 5), (3, 6), (5, 2), (0, 1)]:
        stone(c, r, False, b)
    star = TB.mat('omstar', TB.PAL['mustard'], emit=(1.0, 0.75, 0.2), estr=0.45, coat=0.6)
    x5, z5 = xz(*five[-1])
    TB.prism(TB.star_pts(0.16, 0.07), 0.05, (x5 + 0.22, -0.24, z5 + 0.3), star, parent=b)
    TB.prism(TB.star_pts(0.09, 0.04), 0.04, (x5 - 0.08, -0.24, z5 + 0.46), star, parent=b)
    # 앞에서 막 떨어지는 큰 흑돌 — 렌즈 모양 두께가 보이게 기울인다
    fx = TB.group("fall", 0, loc=(1.02, -0.9, 0.62))
    fx.parent = g
    fx.rotation_euler = (math.radians(78), math.radians(-38), 0)
    TB.sph(sr * 2.0, (0, 0, 0), BK, scale=(1, 1, 0.42), parent=fx, seg=40)
    return g


if __name__ == "__main__":
    sc = TB.studio()
    omok_toy()
    sc.render.filepath = os.path.join(TB.OUTDIR, "omok.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED omok")
