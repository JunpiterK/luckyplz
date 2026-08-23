# -*- coding: utf-8 -*-
"""현장 6곳을 glTF(.glb) 로 내보낸다 — 프리렌더 PNG 를 대체한다 (2026-08-23).

**왜 바꾸나.** 프리렌더는 960×640 짜리 정지 이미지였고, 1440px 모니터에서
확대되어 흐릿했다. 엔진을 실시간 3D 로 바꿔 놓고 화면만 옛 이미지를 쓰는 건
앞뒤가 안 맞는다. 이제 같은 Blender 씬을 `.glb` 로 내보내 Babylon 이 실시간
렌더한다 — 해상도는 화면을 따라가고, 시점도 돌릴 수 있고, **핫스팟은 투영
사각형이 아니라 진짜 3D 오브젝트를 집는다**.

**모델링 코드를 복제하지 않는다.** `deltav_lab.py` 를 모듈로 불러
`render()`·`mark()`·`panel_light()` 세 함수만 갈아 끼운다. 두 벌로 나뉘면
반드시 어긋난다.

바뀌는 것:
  · render(name)      → PNG 렌더 대신 같은 이름의 .glb 내보내기
  · mark(node,nm,obj) → 오브젝트 이름을 `hs_<nm>` 으로 바꿔 엔진이 집을 수 있게
  · panel_light(...)  → 위치·세기를 기록만 (glTF 는 area light 를 못 담는다)

카메라와 조명은 메시와 함께 내보내지 않고 **JSON 으로 따로 넘긴다.**
엔진에서 실시간 광원으로 다시 세워야 그림자와 반사가 살아 있다.

실행: C:/tools/blender-4.2.5-windows-x64/blender.exe -b -P export_lab_gltf.py
출력: public/assets/deltav/node_*.glb + public/assets/deltav/lab.json
"""
import bpy
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

OUT = os.path.join(HERE, "..", "..", "public", "assets", "deltav")
os.makedirs(OUT, exist_ok=True)

import deltav_lab as L                                       # noqa: E402

META = {}        # {노드: {cam, target, fov, lights[], hotspots[]}}
_cur = {"node": None, "lights": [], "hots": []}


def _mark(node, name, obj, pad=0.0):
    """엔진이 집을 수 있도록 오브젝트 이름을 바꾼다.

    투영 사각형(HOT)은 더 이상 쓰지 않는다 — Babylon 이 레이 피킹으로
    직접 맞히므로 카메라를 조금 움직여도 어긋날 일이 없다. 이게 프리렌더
    방식의 가장 큰 약점이었다.
    """
    obj.name = "hs_" + name
    _cur["hots"].append(name)


def _panel_light(loc, size, power, color=(1, 0.97, 0.92), rot=(0, 0, 0)):
    """glTF 는 area light 를 담지 못한다. 위치·세기만 적어 두고 엔진에서
    point light 로 근사한다. 크기는 감쇠 반경을 잡는 데 쓴다."""
    _cur["lights"].append({
        "p": [round(v, 3) for v in loc],
        "size": [round(size[0], 2), round(size[1], 2)],
        "power": power,
        "c": [round(v, 3) for v in color],
    })
    # 실제 조명 오브젝트는 만들지 않는다 — 내보내지 않을 것이라 의미가 없다
    return None


def _cam_meta():
    """카메라 위치·바라보는 점·수직 화각을 뽑는다.

    Blender 는 Z-up, glTF 는 Y-up 이라 내보낼 때 좌표가 바뀐다.
    `export_yup=True` 의 변환은 (x, y, z) → (x, z, -y) 다. 카메라도 같은
    변환을 먹여야 모델과 같은 공간에 선다 — 이걸 빼먹으면 카메라가 벽
    바깥이나 천장에 박힌다.
    """
    sc = bpy.context.scene
    cam = sc.camera
    if cam is None:
        return None
    from mathutils import Vector
    p = cam.matrix_world.translation
    fwd = cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    t = p + fwd * 3.0

    def yup(v):
        return [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]

    # 수직 화각: 렌더 해상도가 가로로 길면 lens 는 가로 기준이다
    sw = cam.data.sensor_width
    hfov = 2.0 * math.atan(sw / (2.0 * cam.data.lens))
    aspect = L.H / float(L.W)
    vfov = 2.0 * math.atan(math.tan(hfov / 2.0) * aspect)
    return {"cam": yup(p), "target": yup(t), "fov": round(vfov, 4)}


def _light_yup(lights):
    out = []
    for l in lights:
        x, y, z = l["p"]
        out.append({"p": [round(x, 3), round(z, 3), round(-y, 3)],
                    "size": l["size"], "power": l["power"], "c": l["c"]})
    return out


def _render(name):
    """PNG 렌더 자리에 glb 내보내기를 끼운다."""
    node = name.replace("node_", "").replace(".png", "")
    stem = "node_" + node
    path = os.path.join(OUT, stem + ".glb")
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        use_selection=False,
        export_apply=True,          # 베벨 등 모디파이어 적용
        export_cameras=False,
        export_lights=False,        # area light 는 glTF 에 없다 — JSON 으로 넘긴다
        export_yup=True,
        export_texcoords=True,
        export_normals=True,
        export_materials='EXPORT',
    )
    m = _cam_meta() or {}
    m["lights"] = _light_yup(_cur["lights"])
    m["hotspots"] = list(_cur["hots"])
    META[node] = m
    kb = os.path.getsize(path) / 1024.0
    print("  exported %-10s %6.0f KB  조명 %d  핫스팟 %d"
          % (stem, kb, len(m["lights"]), len(m["hotspots"])))


def _wrap(fn, node):
    """노드 빌더 하나를 감싸 현재 노드 상태를 초기화한다."""
    def run():
        _cur["node"] = node
        _cur["lights"] = []
        _cur["hots"] = []
        fn()
    return run


if __name__ == "__main__":
    L.mark = _mark
    L.panel_light = _panel_light
    L.render = _render

    NODES = [("hall", L.n_hall), ("prop", L.n_prop), ("store", L.n_store),
             ("dock", L.n_dock), ("matlab", L.n_matlab), ("teststand", L.n_teststand)]
    for node, fn in NODES:
        print("== " + node)
        _wrap(fn, node)()

    jp = os.path.join(OUT, "lab.json")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(META, f, ensure_ascii=False, indent=1)
    print("LAB GLTF EXPORT DONE ->", os.path.abspath(OUT))
    print("  lab.json %.1f KB" % (os.path.getsize(jp) / 1024.0))
