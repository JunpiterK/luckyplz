# -*- coding: utf-8 -*-
"""luckyplz 마스코트 레서판다 — 우주 조종사 흉상 세트 (Space-Z · 스타십 착륙 공용 모델, 2026-09-27).

운영자: "아케이드는 손맛, 비주얼 효과, 캐릭터성, 이펙트가 어우러져 주는 임팩트가 핵심이야."
→ 두 우주 게임의 조종석에 같은 마스코트(윷놀이 말 랫서팬더)를 앉힌다. 게임 캔버스에서 기체는 폭 12~20px 라
  기체 안의 얼굴은 읽히지 않는다 — 그래서 **조종석 통신창(HUD 초상)** 으로 보여 준다(스타폭스식 교신창).
  헬멧 유리·금·김서림은 게임 캔버스가 그린다(움직이는 반사·금 가기 연출을 위해). 여기서는 조종복·목 링·헤드셋까지.

모델은 scripts/blender/mascot_panda.py(→ yut_pieces.py) 를 **import 해서 그대로** 쓴다(수정하지 않음).
표정은 mascot_panda.face() 를 감싸 새 표정(dizzy·look·focus·salute)만 여기서 더한다.

## 프레임 (FRAMES — 순서 = 아틀라스 순서, 게임의 PILOT 표와 같아야 한다)
  focus   조종 중(기본) — 또렷한 눈 + 자신감 입꼬리
  blink   깜빡임
  lookL / lookR   회피 — 고개·눈이 피하는 쪽으로
  scared  아슬아슬 스침 — 작아진 눈동자 + o 입 + 식은땀 + 손 번쩍
  cheer   보급·위성 성공 — 별눈 + 만세
  happy   구간 도착·기록 — ^^ 웃음
  dizzy   추락 — 소용돌이 눈 + 혀
  worry   마지막 목숨·저연료 — 올려다보는 걱정 눈 + 식은땀
  cry     게임 오버
  salute  시작 화면 — 윙크 + 손 흔들기
  ouch    피격 순간 — ><

실행:
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_spacez.py            # 전부
  C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P scripts/blender/mascot_spacez.py -- cheer,dizzy
  PS_SAMPLES=24 로 시안 확인
출력: scripts/og-assets/pilot_dodge/<frame>.png → python scripts/build_pilot_atlas.py dodge
      → public/assets/dodge/pilot.webp
"""
import bpy
import math
import os
import sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yut_pieces as yp      # noqa: E402  (모델 원본 — 수정하지 않는다)
import mascot_panda as mp    # noqa: E402  (몸 조립·표정 — 수정하지 않는다)

RES = int(os.environ.get('PS_RES', '512'))
SAMPLES = int(os.environ.get('PS_SAMPLES', '64'))
ORTHO = 2.36
CAM_TGT = Vector((0.0, 0.0, 1.5))
CAM_DIR = Vector((0.0, -9.2, 2.1)).normalized()    # 거의 정면(≈13° 내려다봄) — 교신창은 눈을 마주쳐야 한다
NECK = mp.NECK

SPACEZ = dict(
    name='dodge',
    suit=(0.93, 0.94, 0.97),        # 흰 조종복
    trim=(0.0, 0.85, 1.0),          # Space-Z 시안
    badge=(1.0, 0.80, 0.25),
)

REST = ((0.24, -0.5, 0.52), (-0.24, -0.5, 0.52))       # 조종간 쪽으로 모은 손(프레임 아래로 빠진다)
FRAMES = {
    'focus':  dict(ex='F', hfwd=0.05),
    'blink':  dict(ex='b', hfwd=0.05),
    'lookL':  dict(ex='L', hyaw=-0.3, hroll=-0.1, roll=-0.08),
    'lookR':  dict(ex='R', hyaw=0.3, hroll=0.1, roll=0.08),
    'scared': dict(ex='v', hands=((0.62, -0.5, 0.95), (-0.62, -0.5, 0.95)), hfwd=-0.08, droop=0.35),
    'cheer':  dict(ex='x', hands=((0.98, -0.34, 1.3), (-0.98, -0.34, 1.3)), hfwd=-0.06),
    'happy':  dict(ex='h', hroll=0.12),
    'dizzy':  dict(ex='D', hroll=-0.2, hfwd=0.04, droop=0.7, roll=0.06),
    'worry':  dict(ex='u', hands=((0.28, -0.62, 0.86), (-0.28, -0.62, 0.86)), hfwd=-0.18, droop=0.3),
    'cry':    dict(ex='c', hands=((0.26, -0.64, 0.9), (-0.26, -0.64, 0.9)), droop=1.0, hfwd=0.06),
    'salute': dict(ex='w', hands=((0.9, -0.42, 1.52), REST[1]), hroll=0.1, roll=0.05),
    'ouch':   dict(ex='k', hfwd=0.1, droop=0.25, roll=-0.05),
}
ORDER = ['focus', 'blink', 'lookL', 'lookR', 'scared', 'cheer', 'happy', 'dizzy', 'worry', 'cry', 'salute', 'ouch']


# ════════════ 표정 — mascot_panda.face 에 새 표정을 덧댄다 ════════════
_orig_face = mp.face


def eyes_side(F, d):
    """옆을 보는 눈 — 동공·하이라이트를 d(+1 = 화면 오른쪽) 쪽으로"""
    H, er = F.H, F.er
    for s in (-1, 1):
        x, ez = s * F.ex, F.ez
        yp.feat(H, x, ez, er, F.IRd, scale=(0.86, 0.42, 1.1))
        yp.feat(H, x + d * er * 0.05, ez - er * 0.38, er * 0.62, F.IR, scale=(0.95, 0.4, 0.62), lift=0.012)
        yp.feat(H, x + d * er * 0.42, ez + er * 0.05, er * 0.46, F.D, scale=(0.9, 0.4, 1.05), lift=0.022)
        yp.feat(H, x + d * er * 0.1, ez + er * 0.42, er * 0.32, F.W, scale=(1, 0.4, 1), lift=0.045, seg=20)
        yp.feat(H, x + d * er * 0.62, ez - er * 0.2, er * 0.14, F.W, scale=(1, 0.4, 1), lift=0.045, seg=16)


def spiral(F, s):
    """@ 소용돌이 눈 — 밖에서 안으로 1.8바퀴"""
    H, er = F.H, F.er
    cx, cz = s * F.ex, F.ez
    pts = []
    N = 26
    for i in range(N + 1):
        t = i / N
        r = er * (1.05 - 0.9 * t)
        a = s * (t * math.pi * 3.6) + math.pi * 0.5
        pts.append((cx + math.cos(a) * r * 0.92, cz + math.sin(a) * r * 1.1))
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        yp.line(H, x0, z0, x1, z1, 0.02, F.K, lift=0.02)


def my_face(F, ex, fur):
    H = F.H
    if ex == 'F':            # 조종 중 — 또렷한 눈 + 한쪽 입꼬리 씩
        F.eyes(scale=0.98)
        mz = F.mouth
        yp.arc(H, 0.0, mz, 0.15, -0.03, 0.017, F.K, n=5, lift=0.02)
        yp.line(H, 0.075, mz - 0.004, 0.1, mz + 0.022, 0.016, F.K, lift=0.02)
        yp.blush(H, F.bx, F.bz, 0.7)
    elif ex in ('L', 'R'):   # 회피 — 옆눈 + 앙다문 입
        eyes_side(F, -1 if ex == 'L' else 1)
        yp.arc(H, 0.0, F.mouth - 0.01, 0.12, 0.02, 0.017, F.K, n=5, lift=0.02)
        yp.blush(H, F.bx, F.bz, 0.8)
    elif ex == 'D':          # 어질어질 — 소용돌이 눈 + 물결 입 + 혀
        for s in (-1, 1):
            spiral(F, s)
        mp.mouth_wavy(F)
        yp.feat(H, 0.04, F.mouth - 0.075, 0.05, F.TG, scale=(1.0, 0.5, 1.2), lift=0.03)
        yp.blush(H, F.bx, F.bz, 0.9)
    else:
        _orig_face(F, ex, fur)


mp.face = my_face            # build_panda 가 모듈 전역 face 를 호출 시점에 찾는다


# ════════════ 스튜디오 ════════════
def studio():
    sc = yp.studio()
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.cycles.samples = SAMPLES
    th = 3.6 * RES / 512.0
    sc.render.line_thickness = th
    ls = bpy.context.view_layer.freestyle_settings.linesets[0]
    ls.linestyle.thickness = th
    ls.linestyle.color = (0.004, 0.0025, 0.012)
    fc = bpy.data.collections.new("FACE")
    sc.collection.children.link(fc)
    cam = sc.camera
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = ORTHO
    cam.location = CAM_TGT + CAM_DIR * 14.0
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (-CAM_DIR).to_track_quat('-Z', 'Y')
    cam.data.clip_end = 60
    return sc


def head_matrix(hfwd, hroll, hyaw):
    p = NECK
    return (Matrix.Translation(p) @ Matrix.Rotation(hyaw, 4, 'Z') @ Matrix.Rotation(hroll, 4, 'Y')
            @ Matrix.Rotation(hfwd, 4, 'X') @ Matrix.Translation(-p))


def headset(trim_m):
    """헤드셋 — 머리띠 + 귀덮개 + 입가 마이크. 머리와 함께 기운다"""
    dark = yp.mat('hs_dark', (0.12, 0.13, 0.17), rough=0.3, coat=0.6)
    for s in (-1, 1):
        yp.cyl(0.17, 0.12, (s * 0.9, 0.02, 1.46), dark, rot=(0, math.pi / 2, 0), bevel=0.03)
        yp.cyl(0.1, 0.03, (s * 0.97, 0.02, 1.46), trim_m, rot=(0, math.pi / 2, 0), bevel=0.01)
    pts = []
    for i in range(13):
        a = math.pi * i / 12
        pts.append(Vector((math.cos(a) * 0.93, 0.06, 1.46 + math.sin(a) * 0.8)))
    for a, b in zip(pts, pts[1:]):
        yp.capsule(a, b, 0.045, dark)
    # 마이크 — 왼쪽(화면 왼쪽) 귀덮개에서 입가로
    m0 = Vector((-0.93, -0.12, 1.36))
    m1 = Vector((-0.72, -0.5, 1.2))
    m2 = Vector((-0.46, -0.66, 1.14))
    yp.capsule(m0, m1, 0.028, dark)
    yp.capsule(m1, m2, 0.028, dark)
    yp.sph(0.06, m2, trim_m)


def suit(cfg, trim_m, hands):
    """조종복 — 몸통 덮개 + 소매 + 목 링(헬멧 받침) + 가슴 배지. 몸과 함께 기운다"""
    sm = yp.mat('suit', cfg['suit'], rough=0.38, coat=0.4)
    ring = yp.mat('suit_ring', (0.62, 0.66, 0.74), rough=0.22, metal=0.35, coat=0.7)
    gold = yp.mat('badge', cfg['badge'], rough=0.2, metal=0.3, coat=0.8, emit=cfg['badge'], estr=0.4)
    out = []
    mark = set(bpy.data.objects)
    yp.sph(0.455, (0, 0.06, 0.56), sm, scale=(1.02, 0.94, 0.9))
    for s, h in ((1, hands[0]), (-1, hands[1])):
        sh = Vector((s * 0.36, -0.08, 0.86))
        hv = Vector(h)
        yp.capsule(sh, sh + (hv - sh) * 0.72, 0.13, sm, rb=0.12)
        cuff = yp.torus(0.115, 0.03, sh + (hv - sh) * 0.72, trim_m)
        cuff.rotation_mode = 'QUATERNION'
        cuff.rotation_quaternion = Vector((0, 0, 1)).rotation_difference((hv - sh).normalized())
    yp.torus(0.35, 0.085, (0, -0.02, 0.88), ring)
    yp.torus(0.35, 0.03, (0, -0.02, 0.97), trim_m)
    yp.cyl(0.085, 0.04, (0.2, -0.42, 0.6), gold, rot=(math.pi / 2, 0, 0), bevel=0.012)
    yp.cyl(0.05, 0.05, (0.2, -0.43, 0.6), trim_m, rot=(math.pi / 2, 0, 0), bevel=0.01)
    for o in bpy.data.objects:
        if o not in mark:
            out.append(o)
    return out


def build_bust(name, cfg):
    spec = dict(ex='F', hands=REST, fwd=0.0, roll=0.0, hfwd=0.0, hroll=0.0, hyaw=0.0, droop=0.0, tail=0.25)
    spec.update(FRAMES[name])
    trim_m = yp.mat('trim', cfg['trim'], rough=0.2, coat=0.6, emit=cfg['trim'], estr=1.6)
    before = set(bpy.data.objects)
    R, L = spec['hands']
    yp._DANCE = dict(R=tuple(R), L=tuple(L))
    try:
        mp.build_panda(spec['ex'], spec['droop'], spec['tail'])
        # 윷 말의 팀색 목 리본은 목 링 속에 묻혀 지저분하다 — 뺀다
        for o in list(bpy.data.objects):
            if o in before or o.type != 'MESH':
                continue
            if any(ms.material and ms.material.name.startswith('team_') for ms in o.material_slots):
                bpy.data.objects.remove(o, do_unlink=True)
        # 눈물 줄무늬·눈썹 무늬는 잉크 선을 빼서 교신창 크기(머리 ≈40px)에서 얼굴이 뭉개지지 않게 한다
        fc = bpy.data.collections["FACE"]
        for o in list(bpy.data.objects):
            if o in before or o.type != 'MESH' or not o.material_slots:
                continue
            mn = o.material_slots[0].material.name if o.material_slots[0].material else ''
            brow = mn == 'rp_white' and 1.65 < o.location.z < 1.95 and abs(o.location.x) < 0.45
            if mn == 'rp_stripe' or brow:
                for c in list(o.users_collection):
                    c.objects.unlink(o)
                fc.objects.link(o)
        headset(trim_m)
        objs = [o for o in bpy.data.objects if o.type == 'MESH' and o not in before]
        head = [o for o in objs if o not in yp._HEAD_MARK]
        body_parts = suit(cfg, trim_m, (R, L))
        head = [o for o in head if o not in body_parts]
        Hm = head_matrix(spec['hfwd'], spec['hroll'], spec['hyaw'])
        mp.apply(head, Hm)
        M = mp.body_matrix(spec['fwd'], spec['roll'])
        allm = [o for o in bpy.data.objects if o.type == 'MESH' and o not in before]
        mp.apply(allm, M)
    finally:
        yp._DANCE = None


def render_set(cfg, names=None):
    outdir = os.path.join(HERE, "..", "og-assets", "pilot_" + cfg['name'])
    os.makedirs(outdir, exist_ok=True)
    for n in (names or ORDER):
        studio()
        build_bust(n, cfg)
        sc = bpy.context.scene
        sc.render.filepath = os.path.join(outdir, n + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", cfg['name'], n)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    render_set(SPACEZ, argv[0].split(',') if argv else None)
