# -*- coding: utf-8 -*-
"""장기·象棋 홈 타일 — '레트로 장난감 진열장' 한 벌(tiles_toybox.py)과 같은 스튜디오·재질·외곽선으로 찍는다 (2026-10-02).

tiles_toybox.py 는 다른 작업이 함께 고치는 파일이라 건드리지 않고(tile_omok.py·tile_lots.py 와 같은 방식) 도우미를 가져다 쓴다.
장면: 비스듬히 세운 은행나무 빛 장기판(9×10 선 + 궁성 X — 장난감 크기라 선은 굵게), 판 위에 초(초록)·한(빨강) 팔각 말 몇 개,
앞쪽에 커다란 초록 楚 팔각 말이 서 있고 그 옆에 붉은 帥 둥근 象棋 말이 기대어 있다(두 규칙을 한 판에서). 장군 별 두 개.

글자: 한자는 아리얼 블랙에 없다 → 한컴 바탕(HBATANG.TTF, 없으면 맑은 고딕 굵게)으로 직접 만든다. 글자는 잉크 외곽선에서 뺀다.
실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/tile_janggi.py
출력: scripts/og-assets/tiles3d/janggi.png (1000×1000 투명) → python scripts/build_tiles.py janggi → public/assets/tiles/toy-janggi.webp
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import tiles_toybox as TB  # noqa: E402

R = math.radians
FONTS = ["C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/HBATANG.TTF"]


def _noline(objs):
    """격자선·글자는 잉크 외곽선에서 뺀다(가는 선에 외곽선이 붙으면 굵은 철망처럼 보인다)."""
    col = bpy.data.collections.get("NOLINE")
    if col is None:
        col = bpy.data.collections.new("NOLINE")
        bpy.context.scene.collection.children.link(col)
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)


def cjk(s, size, loc, m, parent, rot=(R(90), 0, 0), extrude=0.012):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.data.body = s
    o.data.size = size
    o.data.extrude = extrude
    o.data.align_x = 'CENTER'
    o.data.align_y = 'CENTER'
    for f in FONTS:
        if os.path.exists(f):
            try:
                o.data.font = bpy.data.fonts.load(f)
                break
            except Exception:
                pass
    o.data.materials.append(m)
    o.parent = parent
    return o


def octo_pts(r):
    return [(math.cos(R(22.5) + k * R(45)) * r, math.sin(R(22.5) + k * R(45)) * r) for k in range(8)]


def janggi_toy():
    """판 전체(9×10)는 타일 크기에서 선이 뭉개진다 → 궁성 한 귀퉁이를 크게: 6줄 × 5줄 + 궁성 X, 앞 가장자리만 판 끝."""
    g = TB.group("janggi", R(-14), loc=(-0.34, 0, 0))
    b = TB.group("board", 0, loc=(-0.06, 0.34, 0))
    b.parent = g
    b.rotation_euler = (R(-30), 0, 0)
    SW, SH = 2.0, 1.72
    GINKGO = TB.mat('jgwood', (0.72, 0.45, 0.17), rough=0.4, coat=0.3)
    GINKGO_D = TB.mat('jgwoodd', (0.42, 0.22, 0.07), rough=0.5, coat=0.25)
    TB.box((SW + 0.22, 0.26, SH + 0.22), (0, 0.02, SH / 2 + 0.11), GINKGO_D, bevel=0.07, parent=b)
    TB.box((SW + 0.12, 0.03, SH + 0.12), (0, -0.115, SH / 2 + 0.11), GINKGO, bevel=0.012, parent=b)
    LINE = TB.mat('jgline', (0.20, 0.10, 0.03), rough=0.6, coat=0.0)
    mx, mz = 0.2, 0.2
    NC, NR = 6, 5
    cw = (SW - 2 * mx) / (NC - 1)
    ch = (SH - 2 * mz) / (NR - 1)
    z0 = 0.11
    lw = 0.024
    lines = []

    def xz(c, r):   # c 0..5 왼→오, r 0..4 아래(판 끝)→위
        return -SW / 2 + mx + c * cw, z0 + mz + r * ch

    for k in range(NC):
        x, _ = xz(k, 0)
        lines.append(TB.box((lw, 0.006, SH - 2 * mz + lw), (x, -0.132, z0 + SH / 2), LINE, bevel=0.0, parent=b))
    for k in range(NR):
        _, z = xz(0, k)
        lines.append(TB.box((SW - 2 * mx + lw, 0.006, lw), (0, -0.132, z), LINE, bevel=0.0, parent=b))
    # 판 끝 쪽(아래) 굵은 테
    _, zb = xz(0, 0)
    lines.append(TB.box((SW - 2 * mx + lw * 3, 0.006, lw * 2.2), (0, -0.133, zb - 0.06), LINE, bevel=0.0, parent=b))
    # 궁성 X — (1,0)-(3,2) · (3,0)-(1,2)
    for (a2, c2) in (((1, 0), (3, 2)), ((3, 0), (1, 2))):
        x1, z1 = xz(*a2)
        x2, z2 = xz(*c2)
        L = math.hypot(x2 - x1, z2 - z1)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        o = bpy.context.object
        o.scale = (L, 0.006, lw)
        bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(LINE)
        o.parent = b
        o.location = ((x1 + x2) / 2, -0.132, (z1 + z2) / 2)
        o.rotation_euler = (0, -math.atan2(z2 - z1, x2 - x1), 0)
        lines.append(o)
    _noline(lines)

    FACE = TB.mat('jgface', (0.80, 0.62, 0.36), rough=0.45, coat=0.4)
    SIDE = TB.mat('jgside', (0.40, 0.20, 0.07), rough=0.45, coat=0.3)
    GRN = TB.mat('jggreen', (0.0, 0.13, 0.04), rough=0.5, coat=0.1)
    RED = TB.mat('jgred', (0.45, 0.0, 0.01), rough=0.5, coat=0.1)
    texts = []

    def piece(c, r, ch_, ink, size):
        x, z = xz(c, r)
        rr = cw * size * 0.5
        TB.prism(octo_pts(rr), 0.08, (x, -0.175, z), SIDE, parent=b)
        TB.prism(octo_pts(rr * 0.92), 0.03, (x, -0.226, z), FACE, parent=b)
        texts.append(cjk(ch_, rr * 1.45, (x, -0.247, z - rr * 0.06), ink, b, extrude=0.02))

    # 초 궁: 장은 궁성 가운데(장기) · 사 · 차 / 공격해 오는 한: 포·마·병
    piece(2, 1, '楚', GRN, 1.12)
    piece(1, 0, '士', GRN, 0.84)
    piece(0, 2, '車', GRN, 1.0)
    piece(2, 4, '包', RED, 1.0)
    piece(4, 3, '馬', RED, 1.0)
    piece(3, 2, '兵', RED, 0.84)

    # 앞 — 커다란 초록 楚(팔각·장기)와 붉은 帥(둥근·象棋)가 나란히: 두 규칙을 한 판에서
    hero = TB.group("hero", 0, loc=(0.72, -1.05, 0.64))
    hero.parent = g
    hero.rotation_euler = (R(74), R(6), R(16))
    hr = 0.52
    TB.prism(octo_pts(hr), 0.17, (0, 0, 0), SIDE, rot=(0, 0, 0), parent=hero)
    TB.prism(octo_pts(hr * 0.92), 0.05, (0, 0, 0.105), FACE, rot=(0, 0, 0), parent=hero)
    texts.append(cjk('楚', hr * 1.3, (0, -0.04, 0.132), GRN, hero, rot=(0, 0, 0), extrude=0.025))
    xq = TB.group("xq", 0, loc=(1.6, -0.62, 0.48))
    xq.parent = g
    xq.rotation_euler = (R(66), R(-6), R(-24))
    xr = 0.42
    IVORY = TB.mat('jgivory', (0.86, 0.72, 0.48), rough=0.4, coat=0.5)
    TB.cyl(xr, 0.15, (0, 0, 0), SIDE, bevel=0.03, verts=64, parent=xq)
    TB.cyl(xr * 0.94, 0.04, (0, 0, 0.085), IVORY, bevel=0.012, verts=64, parent=xq)
    texts.append(TB.torus(xr * 0.78, 0.014, (0, 0, 0.106), RED, parent=xq))
    texts.append(cjk('帥', xr * 1.2, (0, -0.03, 0.11), RED, xq, rot=(0, 0, 0), extrude=0.02))
    _noline(texts)

    star = TB.mat('jgstar', TB.PAL['mustard'], emit=(1.0, 0.75, 0.2), estr=0.45, coat=0.6)
    xs, zs = xz(2, 1)
    TB.prism(TB.star_pts(0.16, 0.07), 0.05, (xs - 0.36, -0.27, zs + 0.34), star, parent=b)
    TB.prism(TB.star_pts(0.1, 0.045), 0.04, (xs - 0.62, -0.27, zs + 0.12), star, parent=b)
    return g


if __name__ == "__main__":
    sc = TB.studio()
    janggi_toy()
    sc.render.filepath = os.path.join(TB.OUTDIR, "janggi.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED janggi")
