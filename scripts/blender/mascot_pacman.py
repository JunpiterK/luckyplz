# -*- coding: utf-8 -*-
"""닷 러너(games/pacman) 주인공 = 마스코트 레서판다 머리 스프라이트 (2026-09-27).

운영자: "아케이드는 손맛, 비주얼 효과, 캐릭터성, 이펙트가 어우러져 주는 임팩트가 핵심".
예전 주인공은 노란 원판 먹보(원작 트레이드 드레스에 가깝다 — arcade_audit 의 '운영자 판단 대기 ①')였다.
사이트 마스코트 레서판다(yut_pieces.py 의 랫서팬더, mascot_panda.py 와 같은 얼굴)로 바꾼다.

미로 한 칸(폰에서 머리 ≈ 18~24px)에서 읽혀야 하므로 **머리만** 쓴다 — 큰 귀·흰 마스크·눈물 줄무늬가
그 크기에서도 레서판다로 읽히는 최소 표식이다. 몸통을 붙이면 머리가 반으로 작아져 표정이 뭉개진다.

## 프레임 (ORDER 순서 = 아틀라스 순서 = 게임의 PMF 표)
  r0 r1 r2   오른쪽을 본다(왼쪽은 캔버스가 좌우 반전) · 입 0 닫힘 / 1 반 / 2 크게(와앙)
  u0 u1 u2   위를 본다 — 고개를 젖히고 눈동자도 위로
  d0 d1 d2   아래를 본다 — 고개를 숙인다
  pr0..pd2   파워 모드 — 같은 9장 + 치켜 V 눈썹 + 송곳니 (유령을 잡으러 가는 얼굴)
  ready      정면 · 웃는 눈 + 벌린 입 (READY)
  shock      정면 · 작아진 눈동자 + o 입 (유령에게 닿은 순간)
  dizzy      정면 · 꼭 감은 >< + 엉엉 입 (쓰러짐)
  happy      정면 · 별눈 + 크게 웃음 (스테이지 클리어)

모델 헬퍼는 yut_pieces 에서 import 만 한다(수정 금지). 조명·재질·잉크선도 그 스튜디오 그대로.

실행:
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_pacman.py            # 전부
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_pacman.py -- r0,ready  # 일부
  DR_SAMPLES=24 로 시안
출력: scripts/og-assets/dotrunner/<frame>.png + meta.json
  → python scripts/build_pacman_atlas.py → public/assets/pacman/runner.webp
"""
import bpy
import json
import math
import os
import sys
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yut_pieces as yp  # noqa: E402  (모델 원본 — 헬퍼만 쓴다)

OUTDIR = os.path.join(HERE, "..", "og-assets", "dotrunner")
os.makedirs(OUTDIR, exist_ok=True)
RES = int(os.environ.get('DR_RES', '192'))
SAMPLES = int(os.environ.get('DR_SAMPLES', '64'))
ORTHO = 2.5                          # 셀 한 변 = 월드 2.5 — 귀 끝(≈2.5)과 고개 돌린 볼까지 들어간다
HC = Vector(yp.HEAD_C)               # 머리 중심 (0,0,1.5)
CAM_TGT = Vector((0.0, 0.0, 1.62))   # 귀 때문에 살짝 위를 가운데로
CAM_DIR = Vector((0.0, -9.2, 2.2)).normalized()   # 거의 정면(≈13°) — 미로의 위에서 본 느낌보다 얼굴이 우선

YAW_SIDE = 0.46                      # 옆을 볼 때 고개 돌림(rad) ≈ 26°. 0.62 는 먼 쪽 눈이 볼에 눌려 처져 보였다
PITCH_UP = -0.42
PITCH_DOWN = 0.22                    # 0.36 은 눈이 가려 흰 눈썹 점이 눈처럼 읽혔다


def studio():
    sc = yp.studio()
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.cycles.samples = SAMPLES
    th = 1.7 * RES / 192.0
    sc.render.line_thickness = th
    ls = bpy.context.view_layer.freestyle_settings.linesets[0]
    ls.linestyle.thickness = th
    ls.linestyle.color = (0.004, 0.0025, 0.012)      # 짙은 미로 배경 위 먹색 외곽선
    fc = bpy.data.collections.new("FACE")            # 이목구비는 선을 긋지 않는다(작은 크기에서 뭉개짐)
    sc.collection.children.link(fc)
    cam = sc.camera
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ORTHO
    cam.location = CAM_TGT + CAM_DIR * 14.0
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (-CAM_DIR).to_track_quat('-Z', 'Y')
    cam.data.clip_end = 60
    return sc


# ════════════ 얼굴 ════════════
def eyes_up(F):
    H, er = F.H, F.er
    for s in (-1, 1):
        x, ez = s * F.ex, F.ez
        yp.feat(H, x, ez, er, F.IRd, scale=(0.86, 0.42, 1.1))
        yp.feat(H, x, ez - er * 0.05, er * 0.6, F.IR, scale=(0.95, 0.4, 0.6), lift=0.012)
        yp.feat(H, x, ez + er * 0.42, er * 0.46, F.D, scale=(0.9, 0.4, 1.0), lift=0.022)
        yp.feat(H, x - er * 0.28, ez + er * 0.62, er * 0.32, F.W, scale=(1, 0.4, 1), lift=0.045, seg=20)
        yp.feat(H, x + er * 0.32, ez - er * 0.12, er * 0.15, F.W, scale=(1, 0.4, 1), lift=0.045, seg=16)


def mad_brows(F):
    """파워 모드 — 흰 눈썹 점 위에 짧고 굵은 V 눈썹. 무섭지 않게 눈은 그대로 크게"""
    H, er, ex, ez = F.H, F.er, F.ex, F.ez
    for s in (-1, 1):
        yp.line(H, s * (ex - er * 0.85), ez + er * 1.28, s * (ex + er * 0.8), ez + er * 1.85, 0.034, F.K, lift=0.03)


def chomp(F, m, power):
    """m: 0 닫힘(고양이 입) · 1 반 · 2 와앙. 스프라이트가 작아서 입을 과장한다(머리 폭의 ~25~30%)"""
    H = F.H
    if m == 0:
        F.mouth_w()
        return
    w, h = (0.15, 0.78) if m == 1 else (0.21, 1.22)
    F.mouth_open(w, h, tongue=True)
    if power:
        fang = yp.mat('fang', (1, 1, 1), rough=0.3)
        for s in (-1, 1):
            p, n = H.pt(s * w * 0.55, F.mouth - 0.03, 0.04)
            yp.cone(0.03, 0.002, 0.07, p, fang, rot=(math.pi, 0, 0))


def face(F, spec):
    H = F.H
    ex = spec['ex']
    if ex == 'run':
        if spec.get('up'):
            eyes_up(F)
        else:
            F.eyes(scale=1.08, big=True)
        if spec.get('power'):
            mad_brows(F)
        chomp(F, spec['m'], spec.get('power'))
        yp.blush(H, F.bx, F.bz, 1.0 if spec.get('power') else 0.7)
    elif ex == 'ready':
        for s in (-1, 1):
            F.closed(s, True)
        F.mouth_open(0.14, 0.9)
        yp.blush(H, F.bx, F.bz, 1.2)
    elif ex == 'shock':
        for s in (-1, 1):
            F.eye_small(s)
        F.mouth_o()
        yp.blush(H, F.bx, F.bz, 0.4)
    elif ex == 'dizzy':
        for s in (-1, 1):
            F.squeeze(s)
        F.mouth_open(0.14, 1.2, tongue=True)
        F.tears_stream()
        yp.blush(H, F.bx, F.bz, 1.2)
    elif ex == 'happy':
        F.eyes(scale=1.12, big=True, star=True)
        F.mouth_open(0.16, 1.05)
        yp.blush(H, F.bx, F.bz, 1.4)
    else:
        raise ValueError(ex)


# ════════════ 머리 — yut_pieces.panda() 의 머리 부분과 같은 조립 ════════════
def build_head(spec):
    fur = yp.mat('rp_fur', (0.86, 0.30, 0.07), rough=0.42, coat=0.35, sheen=0.25)
    white = yp.mat('rp_white', (0.99, 0.96, 0.91), rough=0.45, coat=0.3)
    dark = yp.mat('rp_dark', (0.2, 0.07, 0.03), rough=0.4, coat=0.4)
    H = yp.Head(yp.HEAD_C, yp.HA + 0.02, yp.HB, yp.HC - 0.02)
    yp.sph(1.0, H.c, fur, scale=(H.a, H.b, H.cc), seg=128)
    for s in (-1, 1):
        yp.patch(H, s * 0.5, -0.26, 0.27, white)
        yp.feat(H, s * 0.3, 0.3, 0.09, white, scale=(1.25, 0.3, 0.8), lift=-0.004)
    yp.patch(H, 0, -0.34, 0.24, white, sx=1.35, sz=0.85)
    stripe = yp.mat('rp_stripe', (0.45, 0.13, 0.04), rough=0.45)
    for s in (-1, 1):
        yp.line(H, s * 0.34, -0.2, s * 0.3, -0.42, 0.04, stripe, lift=0.03)
    dr = spec.get('droop', 0.0)
    for s in (-1, 1):
        ang = math.radians(28 + 32 * dr)
        d = (s * math.sin(ang), 0.05, math.cos(ang))
        e0 = (s * (0.52 + 0.08 * dr), 0.08, 1.96 - 0.08 * dr)
        yp.ear(d, e0, 0.5, 0.3, white, flat=0.45)
        yp.ear(d, (e0[0], e0[1] - 0.12, e0[2] + 0.03), 0.36, 0.2, dark, flat=0.25)
    yp.nose(H, -0.24, yp.mat('nose', (0.03, 0.02, 0.03), rough=0.15, coat=1.0), w=0.068)
    # 홍채를 마스코트보다 짙게·조금 크게 — 20px 머리에서 주황 털과 대비가 나야 눈으로 읽힌다(실측: 갈색 물방울처럼 번짐)
    F = yp.Face(H, 0.31, 0.0, 0.2, (0.40, 0.15, 0.04), mouth=-0.33)
    F.no_brows = True
    before = set(bpy.data.objects)
    face(F, spec)
    fc = bpy.data.collections["FACE"]
    for o in bpy.data.objects:
        if o not in before:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            fc.objects.link(o)


def fr(ex, **kw):
    d = dict(ex=ex, yaw=0.0, pitch=0.0, roll=0.0, m=0, up=False, power=False, droop=0.0)
    d.update(kw)
    return d


FRAMES = {}
for pw, pre in ((False, ''), (True, 'p')):
    for m in range(3):
        FRAMES['%sr%d' % (pre, m)] = fr('run', m=m, yaw=YAW_SIDE, roll=0.05, power=pw)
        FRAMES['%su%d' % (pre, m)] = fr('run', m=m, pitch=PITCH_UP, up=True, power=pw)
        FRAMES['%sd%d' % (pre, m)] = fr('run', m=m, pitch=PITCH_DOWN, power=pw)
FRAMES.update({
    'ready': fr('ready', roll=-0.06),
    'shock': fr('shock', droop=0.2),
    'dizzy': fr('dizzy', droop=1.0, roll=0.18),
    'happy': fr('happy', pitch=-0.12),
})
ORDER = ['r0', 'r1', 'r2', 'u0', 'u1', 'u2', 'd0', 'd1', 'd2',
         'pr0', 'pr1', 'pr2', 'pu0', 'pu1', 'pu2', 'pd0', 'pd1', 'pd2',
         'ready', 'shock', 'dizzy', 'happy']


def proj(sc, p):
    v = world_to_camera_view(sc, sc.camera, Vector(p))
    return [round(v.x, 5), round(1.0 - v.y, 5)]


def render_frame(name):
    sc = studio()
    spec = FRAMES[name]
    build_head(spec)
    # 고개 — 머리 중심 기준. 순서: 숙임/젖힘(X) → 갸웃(Y) → 돌림(Z)
    M = (Matrix.Translation(HC) @ Matrix.Rotation(spec['yaw'], 4, 'Z') @ Matrix.Rotation(spec['roll'], 4, 'Y')
         @ Matrix.Rotation(spec['pitch'], 4, 'X') @ Matrix.Translation(-HC))
    bpy.context.view_layer.update()
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.parent is None:
            o.matrix_world = M @ o.matrix_world
    sc.render.filepath = os.path.join(OUTDIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)
    return dict(head=proj(sc, HC), headR=round(yp.HA / ORTHO, 5))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = argv[0].split(',') if argv else ORDER
    mp = os.path.join(OUTDIR, "meta.json")
    meta = {}
    if os.path.exists(mp):
        with open(mp, encoding='utf-8') as f:
            meta = json.load(f)
    for n in names:
        meta[n] = render_frame(n)
        with open(mp, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=1)
