/* ══════════════════════════════════════════════════════════════════════
   델타-브이 — 실시간 3D 빌드 (Babylon.js)

   코덱스 제1부 Chapter 1 / Mission 1-1 「연소 불안정의 정복」.

   왜 Babylon 인가: 이 프로젝트에서 품질을 담보하려면 **코드로 짜고 숫자로
   검증**할 수 있어야 한다. 씬 그래프·재질·프레임타임을 전부 읽을 수 있는
   엔진이라야 눈으로 못 보는 상태에서도 틀린 것을 잡을 수 있다.

   3D 모델의 단일 원본은 여전히 Blender 다 (`scripts/blender/export_gltf.py`).
   ══════════════════════════════════════════════════════════════════════ */
import { Engine } from "@babylonjs/core/Engines/engine";
import { Scene } from "@babylonjs/core/scene";
import { ArcRotateCamera } from "@babylonjs/core/Cameras/arcRotateCamera";
import { HemisphericLight } from "@babylonjs/core/Lights/hemisphericLight";
import { DirectionalLight } from "@babylonjs/core/Lights/directionalLight";
import { ShadowGenerator } from "@babylonjs/core/Lights/Shadows/shadowGenerator";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { StandardMaterial } from "@babylonjs/core/Materials/standardMaterial";
import { Texture } from "@babylonjs/core/Materials/Textures/texture";
import { CreateGround } from "@babylonjs/core/Meshes/Builders/groundBuilder";
import { Vector3, Color3, Color4 } from "@babylonjs/core/Maths/math";
import { SceneLoader } from "@babylonjs/core/Loading/sceneLoader";
import { ParticleSystem } from "@babylonjs/core/Particles/particleSystem";
import { GlowLayer } from "@babylonjs/core/Layers/glowLayer";
import { DefaultRenderingPipeline } from "@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/defaultRenderingPipeline";
/* 모듈 빌드에서는 일부 기능이 **사이드이펙트 임포트**를 따로 요구한다.
   빠뜨리면 런타임에 "needs to be imported before" 로 죽는다. */
import "@babylonjs/core/Rendering/depthRendererSceneComponent";
import "@babylonjs/core/Lights/Shadows/shadowGeneratorSceneComponent";
import "@babylonjs/core/Layers/effectLayerSceneComponent";
import "@babylonjs/core/Particles/webgl2ParticleSystem";
import "@babylonjs/core/Animations/animatable";
import "@babylonjs/core/Loading/loadingScreen";
import "@babylonjs/core/Materials/Textures/Loaders/envTextureLoader";
import "@babylonjs/loaders/glTF/2.0";
/* 현장(LabView) 용 */
import { UniversalCamera } from "@babylonjs/core/Cameras/universalCamera";
import { PointLight } from "@babylonjs/core/Lights/pointLight";
import { HighlightLayer } from "@babylonjs/core/Layers/highlightLayer";
import { PointerEventTypes } from "@babylonjs/core/Events/pointerEvents";
import "@babylonjs/core/Culling/ray";                 /* 피킹에 필요 */
import "@babylonjs/core/Cameras/Inputs/freeCameraMouseInput";

/* ═════════════ 물리 — 미션 1-1 ═════════════
   코덱스의 수식을 그대로 쓴다.

     f_1L ≈ c / (2L)          연소실 1차 종방향 음향 모드
     f_1T ≈ 1.841·c / (π·D)   1차 접선 모드

   c 는 연소 가스 음속(약 1,100 m/s). 플레이어는 FFT 에서 피크를 읽고
   **그게 1L 인지 1T 인지** 판별해야 대응이 달라진다.

   배플과 필름 쿨링은 각각 하나씩만 가르친다:
     배플   → 진동은 잡지만 연소 효율을 깎는다 (추력 부족으로 실패 가능)
     필름쿨링 → 벽은 식지만 비추력을 깎는다 (Isp 8% 하락으로 실패 가능)
   두 창이 겹치는 구간이 정답이고, 창은 넉넉하다(운영자 방침: 너무 어렵지 않게).
*/
export const PHYS = {
  c: 1100,          // 연소 가스 음속 (m/s)
  L: 0.39,          // 연소실 유효 길이 (m)
  D: 0.31,          // 연소실 지름 (m)
  alpha: 0.055,     // 연소 지연 커플링에 의한 성장률
  F_design: 380,    // 설계 추력 (kN)
  F_req: 340,       // 요구 추력 (kN)  → 효율 89.5% 이상 필요
  Isp_design: 300,  // 설계 비추력 (s)
  T_limit: 900,     // 연소실 벽 허용 온도 (°C)
  T_base: 1250,     // 필름 쿨링 0 일 때 벽 온도 (°C)
  burnTarget: 15,   // 목표 연소 시간 (s)
};
export function f1L(){ return PHYS.c / (2 * PHYS.L); }              // ≈ 1410 Hz
export function f1T(){ return 1.841 * PHYS.c / (Math.PI * PHYS.D); } // ≈ 2079 Hz

/** 설계값 → 예상 성능. 미션 판정과 계기 표시가 전부 여기서 나온다. */
export function evaluate(baffle_mm, film_pct){
  const zeta = 0.008 + 0.0022 * baffle_mm;         // 감쇠비
  const margin = zeta / PHYS.alpha;                 // 1 을 넘어야 안정
  const eta_c = 1 - 0.000075 * baffle_mm * baffle_mm; // 배플의 연소 효율 손실
  const thrust = PHYS.F_design * eta_c;
  const wallT = PHYS.T_base - 40 * film_pct;
  const ispLoss = 0.62 * film_pct;                  // %
  const isp = PHYS.Isp_design * (1 - ispLoss / 100);
  return {
    zeta, margin, eta_c, thrust, wallT, ispLoss, isp,
    stable: margin > 1,
    thrustOK: thrust >= PHYS.F_req,
    wallOK: wallT <= PHYS.T_limit,
    ispOK: ispLoss <= 8,
    get pass(){ return this.stable && this.thrustOK && this.wallOK && this.ispOK; }
  };
}

/* ═════════════ 3D ═════════════ */
export class TestStand {
  constructor(canvas){
    this.canvas = canvas;
    this.engine = new Engine(canvas, true, { preserveDrawingBuffer: false, stencil: false });
    this.scene = new Scene(this.engine);
    this.scene.clearColor = new Color4(0.02, 0.028, 0.045, 1);
    this.ready = false;
    this.fire = 0;        // 0~1 연소 강도
    this.shake = 0;       // 0~1 진동
    this.chamberHeat = 0; // 0~1 벽 가열
    this._t = 0;
    this._build();
  }

  _build(){
    const sc = this.scene;

    /* 카메라 — 방폭벽 뒤에서 시험대를 본다 */
    const cam = new ArcRotateCamera("cam", -Math.PI / 2 + 0.55, 1.18, 22,
      new Vector3(0, 3.0, 1.2), sc);
    cam.lowerRadiusLimit = 9;
    cam.upperRadiusLimit = 42;
    cam.upperBetaLimit = 1.52;   // 지면 아래로 못 내려가게
    cam.wheelDeltaPercentage = 0.02;
    cam.attachControl(this.canvas, true);
    this.cam = cam;
    this._camTarget = cam.target.clone();

    /* 조명 — 사막의 해질녘 + 시험장 조명 */
    const hemi = new HemisphericLight("hemi", new Vector3(0, 1, 0), sc);
    hemi.intensity = 0.28;
    hemi.diffuse = new Color3(0.42, 0.52, 0.72);
    hemi.groundColor = new Color3(0.10, 0.09, 0.08);

    const sun = new DirectionalLight("sun", new Vector3(-0.55, -0.72, 0.42), sc);
    sun.position = new Vector3(14, 20, -12);
    sun.intensity = 2.1;
    sun.diffuse = new Color3(1.0, 0.92, 0.80);
    this.sun = sun;

    const sg = new ShadowGenerator(1024, sun);
    sg.useBlurExponentialShadowMap = true;
    sg.blurScale = 2;
    sg.setDarkness(0.42);
    this.shadows = sg;

    /* 지면 — 사막 */
    const g = CreateGround("ground", { width: 300, height: 300 }, sc);
    const gm = new PBRMaterial("gm", sc);
    gm.albedoColor = new Color3(0.16, 0.14, 0.12);
    gm.metallic = 0;
    gm.roughness = 0.95;
    g.material = gm;
    g.receiveShadows = true;

    /* 발광 — 연소실과 화염이 실제로 빛나게 */
    const glow = new GlowLayer("glow", sc);
    glow.intensity = 0.55;
    this.glow = glow;

    /* 포스트 — 블룸·비네트. 화면이 '카메라로 찍은 것' 처럼 보이는 값싼 장치 */
    const pipe = new DefaultRenderingPipeline("pipe", true, sc, [cam]);
    pipe.fxaaEnabled = true;
    pipe.bloomEnabled = true;
    pipe.bloomThreshold = 0.62;
    pipe.bloomWeight = 0.42;
    pipe.bloomKernel = 48;
    pipe.imageProcessing.vignetteEnabled = true;
    pipe.imageProcessing.vignetteWeight = 2.1;
    pipe.imageProcessing.contrast = 1.14;
    pipe.imageProcessing.exposure = 1.05;
    this.pipe = pipe;
  }

  /** 경로 또는 data URI 를 그대로 받는다.
      아티팩트처럼 외부 파일을 못 쓰는 환경에서는 base64 data URI 로 넘긴다. */
  async load(stand, merlin){
    const sc = this.scene;
    const one = (u) => u.startsWith("data:")
      ? SceneLoader.AppendAsync("", u, sc)
      : SceneLoader.AppendAsync("", u, sc);
    await one(stand);
    await one(merlin);

    /* 엔진을 시험대 마운트 아래에 매단다. Blender 는 Z-up, glTF 는 Y-up 이라
       내보낼 때 이미 변환됐으므로 여기서는 위치만 잡는다. */
    const engineMeshes = [];
    sc.meshes.forEach(m => {
      if(!m.name || m.name === "__root__") return;
      m.receiveShadows = true;
      this.shadows.addShadowCaster(m);
      if(/nozzle|chamber|injector|manifold|turbo|turbine|feedline|gimbal/i.test(m.name)){
        engineMeshes.push(m);
      }
    });
    /* glTF 는 __root__ 노드를 하나 만든다. 두 번째가 엔진이다. */
    const roots = sc.getNodes().filter(n => n.name === "__root__");
    if(roots.length >= 2){
      this.engineRoot = roots[1];
      this.engineRoot.position = new Vector3(0, 2.55, 1.6);
    }
    this.chamber = sc.meshes.find(m => /chamber/i.test(m.name)) || null;
    this.chamberMat = this.chamber ? this.chamber.material : null;
    this.engineMeshes = engineMeshes;

    this._flame();
    this.ready = true;
    return this;
  }

  /** 화염 — 노즐 아래로 뿜어 유도로를 때린다 */
  _flame(){
    const sc = this.scene;
    const ps = new ParticleSystem("flame", 1400, sc);
    /* 외부 텍스처를 못 쓰므로 절차적으로 만든 점 텍스처를 쓴다
       (CSP·정적 호스팅 양쪽에서 안전하다) */
    ps.particleTexture = this._dotTexture();
    ps.emitter = new Vector3(0, 2.05, 1.6);
    ps.minEmitBox = new Vector3(-0.14, 0, -0.14);
    ps.maxEmitBox = new Vector3(0.14, 0, 0.14);
    ps.color1 = new Color4(1.0, 0.72, 0.28, 1.0);
    ps.color2 = new Color4(1.0, 0.35, 0.06, 1.0);
    ps.colorDead = new Color4(0.22, 0.06, 0.02, 0.0);
    ps.minSize = 0.28; ps.maxSize = 1.15;
    ps.minLifeTime = 0.10; ps.maxLifeTime = 0.34;
    ps.emitRate = 0;
    ps.blendMode = ParticleSystem.BLENDMODE_ADD;
    ps.gravity = new Vector3(0, -2.0, 0);
    ps.direction1 = new Vector3(-0.6, -6.5, -0.6);
    ps.direction2 = new Vector3(0.6, -13.0, 0.6);
    ps.minEmitPower = 6; ps.maxEmitPower = 15;
    ps.updateSpeed = 0.016;
    ps.start();
    this.flame = ps;

    /* 유도로에 부딪혀 옆으로 퍼지는 배기 */
    const sm = new ParticleSystem("smoke", 900, sc);
    sm.particleTexture = this._dotTexture();
    sm.emitter = new Vector3(0, 0.55, -1.4);
    sm.minEmitBox = new Vector3(-1.0, 0, -0.6);
    sm.maxEmitBox = new Vector3(1.0, 0.3, 0.6);
    sm.color1 = new Color4(0.72, 0.70, 0.68, 0.55);
    sm.color2 = new Color4(0.40, 0.38, 0.36, 0.35);
    sm.colorDead = new Color4(0.2, 0.2, 0.2, 0);
    sm.minSize = 1.2; sm.maxSize = 4.5;
    sm.minLifeTime = 0.8; sm.maxLifeTime = 2.2;
    sm.emitRate = 0;
    sm.gravity = new Vector3(0, 1.4, 0);
    sm.direction1 = new Vector3(-3, 1, -8);
    sm.direction2 = new Vector3(3, 4, -14);
    sm.minEmitPower = 3; sm.maxEmitPower = 9;
    sm.start();
    this.smoke = sm;
  }

  /** 파티클용 방사형 점 텍스처를 코드로 만든다 — 외부 파일이 필요 없다 */
  _dotTexture(){
    if(this._dot) return this._dot;
    const S = 64;
    const cv = document.createElement("canvas");
    cv.width = cv.height = S;
    const cx = cv.getContext("2d");
    const g = cx.createRadialGradient(S/2, S/2, 0, S/2, S/2, S/2);
    g.addColorStop(0, "rgba(255,255,255,1)");
    g.addColorStop(0.35, "rgba(255,255,255,0.62)");
    g.addColorStop(1, "rgba(255,255,255,0)");
    cx.fillStyle = g;
    cx.fillRect(0, 0, S, S);
    const t = new Texture(cv.toDataURL(), this.scene, true, false);
    t.hasAlpha = true;
    this._dot = t;
    return t;
  }

  /** 매 프레임 — 연소 강도·진동·벽 온도를 3D 에 반영한다 */
  tick(dt){
    if(!this.ready) return;
    this._t += dt;
    const f = this.fire;

    if(this.flame){
      this.flame.emitRate = 1200 * f;
      this.flame.minEmitPower = 5 + 6 * f;
      this.flame.maxEmitPower = 11 + 9 * f;
    }
    if(this.smoke) this.smoke.emitRate = 700 * f;

    /* 연소실 벽이 달아오른다 — 이미시브를 실시간으로 올린다 */
    if(this.chamberMat){
      const h = this.chamberHeat;
      this.chamberMat.emissiveColor = new Color3(1.0 * h, 0.24 * h * h, 0.05 * h * h);
      this.chamberMat.emissiveIntensity = 1.0;
    }

    /* 진동 — 카메라를 흔든다. 불안정하면 화면이 요동친다 */
    const s = this.shake;
    if(s > 0.001){
      const w = 2 * Math.PI * 14;   // 눈에 보이는 흔들림 주파수
      const a = 0.055 * s;
      this.cam.target = this._camTarget.add(new Vector3(
        Math.sin(this._t * w) * a,
        Math.sin(this._t * w * 1.7 + 1.1) * a,
        Math.cos(this._t * w * 0.9) * a * 0.6));
    } else if(this.cam.target !== this._camTarget){
      this.cam.target = this._camTarget.clone();
    }

    /* 화염이 셀수록 주변이 밝아진다 */
    this.sun.intensity = 2.1 + 0.9 * f;
    if(this.glow) this.glow.intensity = 0.55 + 1.1 * f;
  }

  run(onFrame){
    this.engine.runRenderLoop(() => {
      const dt = this.engine.getDeltaTime() / 1000;
      if(onFrame) onFrame(dt);
      this.tick(dt);
      this.scene.render();
    });
    window.addEventListener("resize", () => this.engine.resize());
  }

  dispose(){
    this.engine.stopRenderLoop();
    this.scene.dispose();
    this.engine.dispose();
  }
}

/* ═════════════ 현장 — 실시간 3D 1인칭 뷰 ═════════════

   프리렌더 PNG(960×640) 를 대체한다. 그 방식의 문제는 두 가지였다:
     · 1440px 모니터에서 확대되어 흐렸다
     · 핫스팟이 **카메라 기준으로 계산된 사각형**이라, 씬을 조금만 고쳐도
       클릭 영역이 물체에서 어긋났다

   지금은 같은 Blender 씬을 `.glb` 로 받아 실시간 렌더하고, 클릭은
   **레이 피킹**으로 진짜 메시를 맞힌다. 집을 수 있는 물체는 Blender 쪽에서
   이름이 `hs_<키>` 로 붙어 나온다 (`scripts/blender/export_lab_gltf.py`).

   카메라는 제자리에서 **둘러보기만** 한다. 방 안을 걸어 다니게 하면 벽을
   뚫고 나가고, 게임의 성격(현장을 훑어 근거를 찾는다)과도 안 맞는다. */
export class LabView {
  /** @param onPick 핫스팟 키를 받는 콜백. `hs_` 접두어는 떼어서 준다 */
  constructor(canvas, onPick){
    this.canvas = canvas;
    this.onPick = onPick || function(){};
    this.engine = new Engine(canvas, true, { preserveDrawingBuffer: false, stencil: true });
    this.scene = null;
    this.node = null;
    this.hover = null;
    this._running = false;
    window.addEventListener("resize", () => { if(this.engine) this.engine.resize(); });
  }

  /** 노드 하나를 통째로 갈아 끼운다.
      씬을 새로 만드는 편이 메시를 골라 지우는 것보다 확실하다 — 노드 하나가
      50~190KB 라 다시 만드는 비용이 누수 위험보다 싸다. */
  async goto(url, meta){
    if(this.scene){ this.scene.dispose(); this.scene = null; }
    const sc = new Scene(this.engine);
    sc.clearColor = new Color4(0.012, 0.016, 0.026, 1);
    this.scene = sc;

    const cp = meta.cam || [0, 1.6, 0];
    const tp = meta.target || [0, 1.6, -3];
    const cam = new UniversalCamera("eye", new Vector3(cp[0], cp[1], cp[2]), sc);
    cam.setTarget(new Vector3(tp[0], tp[1], tp[2]));
    cam.fov = meta.fov || 1.05;
    cam.minZ = 0.05;
    cam.speed = 0;                       /* 이동 금지 — 제자리에서 둘러보기만 */
    cam.inertia = 0.72;
    cam.angularSensibility = 2600;
    cam.attachControl(this.canvas, true);
    /* 키보드 이동 입력을 떼어 낸다. 남겨 두면 방향키로 벽을 뚫고 나간다. */
    if(cam.inputs && cam.inputs.attached && cam.inputs.attached.keyboard){
      cam.inputs.removeByType("FreeCameraKeyboardMoveInput");
    }
    this.cam = cam;
    /* _base/_home 은 좌표계 보정 뒤에 다시 잡는다 (아래) */

    /* 조명 — Blender 의 area light 는 glTF 에 담기지 않아 JSON 으로 받아
       point light 로 근사한다. 천장 램프 메시는 이미시브라 GlowLayer 가 받는다. */
    const amb = new HemisphericLight("amb", new Vector3(0, 1, 0), sc);
    amb.intensity = 0.32;
    amb.diffuse = new Color3(0.62, 0.68, 0.82);
    amb.groundColor = new Color3(0.10, 0.11, 0.15);
    this.lights = [];
    (meta.lights || []).forEach((L, i) => {
      const p = new PointLight("p" + i, new Vector3(L.p[0], L.p[1], L.p[2]), sc);
      /* Blender 의 W 값을 그대로 쓰면 실내가 하얗게 탄다. 패널 55W 를
         기준 1.0 으로 두고 비례시킨 뒤 상한을 건다. */
      p.intensity = Math.min(2.2, (L.power || 55) / 55 * 0.95);
      p.diffuse = new Color3(L.c[0], L.c[1], L.c[2]);
      p.range = 14;
      this.lights.push(p);
    });

    await SceneLoader.AppendAsync("", url, sc);

    /* ── 좌표계 보정 (2026-08-23 실제 버그) ──
       glTF 는 오른손 Y-up, Babylon 은 기본이 왼손이라 로더가 `__root__` 에
       scaling z=-1 + Y 180° 를 걸어 모델을 통째로 변환한다. 결과적으로
       **x 부호가 뒤집힌다.** Blender 좌표를 그대로 쓴 카메라는 씬의 거울상에
       서게 되고, 방이 대칭이라 겉보기엔 멀쩡해 눈치채기 어렵다.
       실제로 자재 창고의 수소 카드가 화면 밖 54.8° 로 밀려나 있었다.
       루트의 월드 행렬을 그대로 먹여 카메라·조명을 같은 공간으로 옮긴다. */
    const root = sc.getNodes().filter(n => n.name === "__root__")[0];
    if(root){
      const M = root.getWorldMatrix();
      const cw = Vector3.TransformCoordinates(new Vector3(cp[0], cp[1], cp[2]), M);
      const tw = Vector3.TransformCoordinates(new Vector3(tp[0], tp[1], tp[2]), M);
      cam.position.copyFrom(cw);
      cam.setTarget(tw);
      this.lights.forEach((L, i) => {
        const q = meta.lights[i];
        L.position = Vector3.TransformCoordinates(
          new Vector3(q.p[0], q.p[1], q.p[2]), M);
      });
    }
    this._base = { rx: cam.rotation.x, ry: cam.rotation.y };
    this._home = cam.position.clone();

    /* 집을 수 있는 것과 없는 것을 가른다 */
    this.hots = [];
    sc.meshes.forEach(m => {
      if(!m.name || m.name === "__root__") return;
      if(/^hs_/.test(m.name)){
        m.isPickable = true;
        this.hots.push(m);
      } else {
        m.isPickable = false;     /* 벽·바닥이 레이를 가로채지 않게 */
      }
    });

    const glow = new GlowLayer("g", sc);
    glow.intensity = 0.85;
    this.glow = glow;

    /* 무엇을 누를 수 있는지 보이게 한다. 프리렌더 시절엔 CSS 로 사각형을
       빛냈는데, 지금은 물체 자체에 테두리를 준다. */
    const hl = new HighlightLayer("hl", sc);
    hl.innerGlow = false;
    this.hl = hl;
    this.hots.forEach(m => hl.addMesh(m, new Color3(0.22, 0.91, 0.78)));

    const pipe = new DefaultRenderingPipeline("lab", true, sc, [cam]);
    pipe.bloomEnabled = true;
    pipe.bloomThreshold = 0.62;
    pipe.bloomWeight = 0.42;
    pipe.bloomKernel = 42;
    pipe.imageProcessing.contrast = 1.14;
    pipe.imageProcessing.exposure = 1.02;
    pipe.imageProcessing.vignetteEnabled = true;
    pipe.imageProcessing.vignetteWeight = 1.5;
    pipe.fxaaEnabled = true;

    /* **POINTERPICK 을 쓰지 말 것** (2026-08-23 실제 버그).
       Babylon 은 자기 **정확 피킹**이 down·up 양쪽에서 같은 메시를 맞혀야만
       POINTERPICK 을 던진다. 즉 아래의 너그러운 `_pickNear` 가 개입할 자리가
       없어, 작은 핫스팟은 영원히 안 눌린다. down/up 을 직접 받아 처리한다. */
    let down = null;
    sc.onPointerObservable.add((pi) => {
      const t = pi.type;
      if(t === PointerEventTypes.POINTERMOVE){
        const m = this._pickNear(sc.pointerX, sc.pointerY);
        if(m !== this.hover){
          this.hover = m;
          this.canvas.style.cursor = m ? "pointer" : "default";
        }
      } else if(t === PointerEventTypes.POINTERDOWN){
        down = { x: sc.pointerX, y: sc.pointerY };
      } else if(t === PointerEventTypes.POINTERUP){
        if(!down) return;
        /* 시점을 돌리려고 끈 것과 누른 것을 가른다 */
        const moved = Math.abs(sc.pointerX - down.x) + Math.abs(sc.pointerY - down.y);
        const at = down;
        down = null;
        if(moved > 6) return;
        const m = this._pickNear(at.x, at.y);
        if(m) this.onPick(m.name.replace(/^hs_/, ""));
      }
    });

    /* 제자리에서 둘러보기만 — 회전 범위를 묶고 위치를 매 프레임 되돌린다.
       UniversalCamera 는 speed=0 이어도 관성으로 미세하게 밀린다. */
    sc.onBeforeRenderObservable.add(() => {
      const b = this._base, C = this.cam;
      C.position.copyFrom(this._home);
      C.rotation.y = Math.max(b.ry - 0.44, Math.min(b.ry + 0.44, C.rotation.y));
      C.rotation.x = Math.max(b.rx - 0.24, Math.min(b.rx + 0.24, C.rotation.x));
      const t = performance.now() * 0.0035;
      this.hl.blurHorizontalSize = 0.7 + 0.35 * Math.sin(t);
      this.hl.blurVerticalSize = 0.7 + 0.35 * Math.sin(t);
    });

    this.ready = true;
    if(!this._running) this.run();
    this.engine.resize();
    return this;
  }

  /** 커서 주변까지 훑어 핫스팟을 집는다.

      원근 때문에 먼 물체는 화면의 0.03% (약 16×16px) 밖에 안 된다 — 정확히
      그 픽셀을 찍어야만 반응하면 못 누른다. 프리렌더 시절엔 투영 사각형에
      최소 크기(10%)를 강제했는데, 3D 에서는 기하를 부풀릴 수 없으므로
      **집는 쪽을 너그럽게** 만든다. 가까운 고리부터 훑어 제일 가까운 것을
      고르므로, 물체가 클 때의 정확도는 그대로다. */
  _pickNear(px, py){
    const sc = this.scene;
    const hit = (x, y) => {
      const p = sc.pick(x, y);
      return (p && p.hit && p.pickedMesh && /^hs_/.test(p.pickedMesh.name))
        ? p.pickedMesh : null;
    };
    let m = hit(px, py);
    if(m) return m;
    const RINGS = [9, 18, 28];
    for(let r = 0; r < RINGS.length; r++){
      const rad = RINGS[r];
      for(let a = 0; a < 8; a++){
        const th = a * Math.PI / 4;
        m = hit(px + Math.cos(th) * rad, py + Math.sin(th) * rad);
        if(m) return m;
      }
    }
    return null;
  }

  /** 핫스팟 표시를 껐다 켠다 (이미 찾은 자료는 표시를 줄인다) */
  setFound(keys){
    if(!this.hl) return;
    this.hots.forEach(m => {
      const k = m.name.replace(/^hs_/, "");
      this.hl.removeMesh(m);
      this.hl.addMesh(m, keys && keys.indexOf(k) >= 0
        ? new Color3(0.30, 0.36, 0.46)      /* 이미 챙긴 것 — 눈에 덜 띄게 */
        : new Color3(0.22, 0.91, 0.78));
    });
  }

  run(){
    this._running = true;
    this.engine.runRenderLoop(() => { if(this.scene) this.scene.render(); });
  }

  stop(){
    this._running = false;
    this.engine.stopRenderLoop();
  }

  dispose(){
    this.stop();
    if(this.scene) this.scene.dispose();
    this.engine.dispose();
  }
}

/* 검증·디버그용으로 밖에서 잡을 수 있게 노출한다 */
window.DV3D = { TestStand, LabView, evaluate, PHYS, f1L, f1T };
