# -*- coding: utf-8 -*-
"""행성 키우기 — 마스코트 레서판다 우주비행사가 탄 미니 UFO (2026-09-27 아케이드 임팩트 개편).

판다 몸·얼굴은 scripts/blender/mascot_panda.py 의 build_frame 을 **import 해서** 그대로 쓴다(원본 수정 없음).
이 파일은 판다 허리 아래를 감싸는 접시형 UFO(레일 조명·조종석 칼라)만 얹는다.
유리 돔·견인 빔·깜빡이는 조명 글로우는 게임 캔버스가 그린다 — 유리를 렌더하면 Freestyle 잉크선이
돔 안의 얼굴 외곽선을 가려 버린다.

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_lucky_merge.py [-- idle,cheer]
출력: scripts/og-assets/lucky-merge/ufo/<frame>.png + meta.json → python scripts/build_arcade_mascots.py merge
"""
import bpy
import json
import math
import os
import sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yut_pieces as yp      # noqa: E402
import mascot_panda as mp    # noqa: E402

OUT = os.path.join(HERE, "..", "og-assets", "lucky-merge", "ufo")
SAMPLES = int(os.environ.get('MM_SAMPLES', '64'))
fr = mp.fr
RIM = ((0.44, -0.8, 0.92), (-0.44, -0.8, 0.92))
UFO = {
    'idle':    fr('n', RIM),
    'blink':   fr('b', RIM),
    'drop':    fr('k', ((0.2, -0.98, 0.84), (-0.2, -0.98, 0.84)), fwd=0.14, hfwd=0.06),
    'happy':   fr('h', ((0.62, -0.52, 1.22), (-0.62, -0.52, 1.22))),
    'cheer':   fr('x', ((1.06, -0.3, 1.62), (-1.06, -0.3, 1.62)), hfwd=-0.08),
    'wow':     fr('o', ((0.66, -0.5, 0.98), (-0.66, -0.5, 0.98)), hfwd=-0.05),
    'nervous': fr('v', ((0.64, -0.5, 1.2), (-0.64, -0.5, 1.2)), droop=0.45, fwd=0.04),
    'cry':     fr('c', mp.CHIN, droop=1.0, hfwd=0.08),
    'wink':    fr('w', ((0.44, -0.8, 0.92), (-1.02, -0.42, 1.08)), roll=-0.05),
}
ORDER = ['idle', 'blink', 'drop', 'happy', 'cheer', 'wow', 'nervous', 'cry', 'wink']
BULBS = 10


def _noline(o):
    if "NOLINE" not in bpy.data.collections:
        c = bpy.data.collections.new("NOLINE")
        bpy.context.scene.collection.children.link(c)
    c = bpy.data.collections["NOLINE"]
    for cc in list(o.users_collection):
        cc.objects.unlink(o)
    c.objects.link(o)


def saucer():
    hull = yp.mat('ufo_hull', (0.80, 0.83, 0.93), rough=0.22, metal=0.35, coat=0.8)
    belly = yp.mat('ufo_belly', (0.42, 0.46, 0.62), rough=0.3, metal=0.3, coat=0.6)
    red = yp.mat('ufo_band', (0.88, 0.10, 0.12), rough=0.25, coat=0.9)
    cream = yp.mat('ufo_collar', (0.99, 0.93, 0.78), rough=0.35, coat=0.6)
    yp.sph(1.0, (0, 0.05, 0.42), hull, scale=(1.62, 1.62, 0.44), seg=96)
    yp.sph(1.0, (0, 0.05, 0.3), belly, scale=(1.2, 1.2, 0.34), seg=64)
    yp.torus(1.56, 0.075, (0, 0.05, 0.47), red)
    yp.torus(0.74, 0.11, (0, 0.02, 0.84), cream)
    cols = [(1.0, 0.85, 0.25), (0.35, 0.9, 1.0), (1.0, 0.4, 0.75)]
    pos = []
    for i in range(BULBS):
        a = -math.pi / 2 + (i - (BULBS - 1) / 2) * (math.pi / (BULBS - 1)) * 1.7
        c = cols[i % 3]
        m = yp.mat('bulb%d' % (i % 3), c, rough=0.15, coat=1.0, emit=c, estr=2.2)
        p = (1.38 * math.cos(a), 0.05 + 1.38 * math.sin(a), 0.6)
        o = yp.sph(0.11, p, m, seg=20)
        _noline(o)
        pos.append(p)
    em = yp.mat('ufo_emit', (0.4, 0.95, 1.0), rough=0.2, emit=(0.4, 0.95, 1.0), estr=2.5)
    yp.sph(0.42, (0, 0.05, 0.02), em, scale=(1, 1, 0.3), seg=40)
    return pos


def proj(sc, p):
    v = world_to_camera_view(sc, sc.camera, Vector(p))
    return [round(v.x, 5), round(1.0 - v.y, 5)]


def render(name):
    mp.ORTHO = 3.6
    mp.CAM_TGT = Vector((0.0, 0.0, 1.12))
    mp.CAM_DIR = Vector((0.0, -9.2, 2.7)).normalized()
    mp.YAW = 0.0
    mp.RES = 448
    mp.SAMPLES = SAMPLES
    mp.FRAMES['ufo_' + name] = UFO[name]
    sc = mp.studio()
    spec, ZM, Hm, _ = mp.build_frame('ufo_' + name)
    bulbs = saucer()
    os.makedirs(OUT, exist_ok=True)
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    head_c = ZM @ (Hm @ Vector(yp.HEAD_C))
    print("RENDERED ufo", name)
    return dict(head=proj(sc, head_c), headR=round(yp.HA / mp.ORTHO, 5), emit=proj(sc, (0, 0.05, -0.04)),
                rimL=proj(sc, (-1.62, 0.05, 0.42)), rimR=proj(sc, (1.62, 0.05, 0.42)),
                bulbs=[proj(sc, p) for p in bulbs])


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = argv[0].split(',') if argv else ORDER
    mpath = os.path.join(OUT, "meta.json")
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    if os.path.exists(mpath):
        with open(mpath, encoding='utf-8') as f:
            meta = json.load(f)
    for n in names:
        meta[n] = render(n)
        with open(mpath, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=1)
