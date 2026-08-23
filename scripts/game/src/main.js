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
/* 터보펌프 리그 — 회전체를 한 노드에 묶어 돌린다 */
import { TransformNode } from "@babylonjs/core/Meshes/transformNode";
/* 정적 메시 병합 — 드로우콜을 줄이는 표준 수단 */
import { Mesh } from "@babylonjs/core/Meshes/mesh";

/* ═════════════ 렌더 해상도 ═════════════
   Babylon 은 기본적으로 **CSS 픽셀 해상도**로 그린다. 화면 배율이 125%·150%
   인 윈도우나 레티나에서는 그 결과가 확대되어 번진다.

   `new Engine(..., adaptToDeviceRatio=true)` 로도 되지만, 그러면 resize() 가
   매번 `_hardwareScalingLevel` 을 devicePixelRatio 로 덮어써서 상한을 걸 수
   없다. 4K·200% 같은 조합에서 픽셀 수가 4배가 되면 프레임이 무너지므로
   **2배까지만** 올린다. 그래서 직접 관리한다. */
function applyDPR(engine){
  const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
  engine.setHardwareScalingLevel(1 / dpr);
}

/* 후처리 공통 — 선명함을 깎는 설정을 걷어낸다.
   FXAA 는 대비가 큰 가장자리를 흐려 계단을 감추는 방식이라 화면 전체가
   물러진다. MSAA 는 기하 가장자리만 다루므로 텍스트·계기·금속 하이라이트가
   살아 있다. 샤픈은 아주 약하게만 — 과하면 윤곽에 흰 테가 생긴다. */
function tunePipeline(pipe, opt){
  const o = opt || {};
  pipe.samples = 4;                 /* MSAA 4x — 기본값 1(꺼짐) */
  pipe.fxaaEnabled = false;
  pipe.sharpenEnabled = true;
  pipe.sharpen.edgeAmount = 0.22;
  pipe.sharpen.colorAmount = 1.0;
  pipe.bloomEnabled = true;
  pipe.bloomThreshold = o.bloomThreshold != null ? o.bloomThreshold : 0.80;
  pipe.bloomWeight = o.bloomWeight != null ? o.bloomWeight : 0.22;
  pipe.bloomKernel = 32;
  pipe.imageProcessing.contrast = o.contrast != null ? o.contrast : 1.10;
  pipe.imageProcessing.exposure = o.exposure != null ? o.exposure : 1.02;
  pipe.imageProcessing.vignetteEnabled = true;
  pipe.imageProcessing.vignetteWeight = o.vignette != null ? o.vignette : 0.9;
}

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
    applyDPR(this.engine);
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
    tunePipeline(pipe, { bloomThreshold: 0.74, bloomWeight: 0.30,
                        contrast: 1.14, exposure: 1.04, vignette: 1.1 });
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
    window.addEventListener("resize", () => {
      applyDPR(this.engine);
      this.engine.resize();
    });
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
    applyDPR(this.engine);
    this.scene = null;
    this.node = null;
    this.hover = null;
    this._running = false;
    window.addEventListener("resize", () => {
      if(!this.engine) return;
      applyDPR(this.engine);
      this.engine.resize();
    });
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
    /* 앰비언트를 낮춘다 — 밝게 채워 두면 그림자가 안 읽혀 방이 납작해진다 */
    amb.intensity = 0.22;
    amb.diffuse = new Color3(0.62, 0.68, 0.82);
    amb.groundColor = new Color3(0.10, 0.11, 0.15);

    /* 딱딱한 방향광 하나 — 참고 사진의 시험 셀은 강한 빛이 그레이팅에
       줄무늬 그림자를 떨어뜨린다. 그림자가 없으면 물건이 바닥에 안 붙어
       보이고, 아무리 디테일을 넣어도 종이처럼 보인다. */
    const key = new DirectionalLight("key", new Vector3(-0.42, -1, 0.34), sc);
    key.position = new Vector3(2.6, 4.2, -3.4);
    key.intensity = 1.35;
    key.diffuse = new Color3(1.0, 0.96, 0.88);
    const sg = new ShadowGenerator(1024, key);
    sg.usePercentageCloserFiltering = true;
    sg.filteringQuality = ShadowGenerator.QUALITY_LOW;
    sg.bias = 0.002;
    sg.normalBias = 0.012;
    this.shadows = sg;
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

    /* ── 정적 메시 병합 ──
       방 하나가 메시 500 개다. 그림자까지 켜면 드로우콜이 1,000 회를 넘어
       **CPU 가 먼저 막힌다**(실측 21.9ms — 이건 GPU 가 아니라 제출 비용이다).
       전부 정지해 있으므로 재질별로 하나씩 합친다. 집을 수 있는 `hs_*` 만
       따로 남긴다 — 합치면 레이 피킹으로 무엇을 집었는지 알 수 없다. */
    const groups = {};
    sc.meshes.forEach(m => {
      if(!m.name || m.name === "__root__") return;
      if(/^hs_/.test(m.name)) return;
      if(!m.material || !m.geometry) return;
      const k = m.material.name;
      (groups[k] = groups[k] || []).push(m);
    });
    Object.keys(groups).forEach(k => {
      const g = groups[k];
      if(g.length < 2) return;
      const merged = Mesh.MergeMeshes(g, true, true, undefined, false, true);
      if(merged) merged.name = "merged_" + k;
    });

    /* 집을 수 있는 것과 없는 것을 가른다 */
    this.hots = [];
    sc.meshes.forEach(m => {
      if(!m.name || m.name === "__root__") return;
      m.receiveShadows = true;
      /* 캐스터를 고른다. 500 메시를 전부 넣으면 그림자 패스가 프레임을
         12.6ms → 21.6ms 로 밀어 올린다(실측). 고DPI 에서는 더 나빠진다.
         · 벽·바닥·천장은 받기만 한다 — 방 전체를 덮어 셰도우맵 해상도를 낭비
         · 볼트처럼 작은 것은 어차피 그림자가 안 보인다 */
      const mn = (m.material && m.material.name) || "";
      const rad = m.getBoundingInfo
        ? m.getBoundingInfo().boundingSphere.radiusWorld : 1;
      if(!/wall|floor|ceil|room/i.test(mn) && rad > 0.075)
        this.shadows.addShadowCaster(m);
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
    tunePipeline(pipe, { bloomThreshold: 0.78, bloomWeight: 0.24,
                        contrast: 1.10, exposure: 1.02, vignette: 0.85 });

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

/* ═════════════ 물리 — 미션 1-2 「터보펌프의 악몽」 ═════════════

   코덱스가 요구하는 네 가지를 그대로 축으로 삼는다:
     임펠러 형상(블레이드 각) · 베어링/실 · 인듀서 · 고속 회전 시험

   쓰는 식:
     ψ = gH/u²              헤드 계수 — 후향 블레이드 각이 클수록 커진다
     P = ρgQH/η             터빈이 대야 하는 축동력
     Nss = N√Q / NPSH^0.75  흡입 비속도 — **인듀서가 이걸 끌어올린다**

   흡입 비속도가 이 미션의 심장이다. 인듀서 없이는 요구 NPSH 가 128m 까지
   치솟아 **어떤 조합으로도 통과할 수 없다**(설계 공간 전수 조사로 확인).
   실제 역사에서 인듀서가 필수였던 이유가 숫자로 드러난다. */
export const PUMP = {
  rho: 1141,        // LOX 밀도 (kg/m³)
  g: 9.80665,
  Q: 0.071,         // 체적 유량 (m³/s) — 추력 340kN, Isp 300s, O/F 2.34
  Qgpm: 1125,       // 같은 유량 (gpm) — Nss 는 이 단위가 관례다
  r: 0.042,         // 임펠러 반지름 (m)
  Hreq: 670,        // 요구 토출 헤드 (m) — 연소실 6.0MPa + 인젝터 1.2MPa + 손실
  npshA: 32,        // 가용 NPSH (m) — 탱크 가압 0.32MPa + 정수두
  Plimit: 800e3,    // 가스발생기 축동력 상한 (W)
  Tlimit: 20,       // 베어링 허용 온도 (°C) — LOX 중에서는 발화 위험
  bleedLimit: 8,    // 냉각 블리드 상한 (%) — 넘으면 정격 유량 미달
  Ncrit: 18000,     // 1차 임계 회전수 (rpm)
  vibMargin: 0.15,  // 임계에서 15% 는 떨어져야 한다
  runTarget: 60     // 연속 운전 목표 (s)
};
export const INDUCER = { none:9000, short:23000, long:30000 };

export function psiOf(beta){ return 0.30 + 0.0090 * beta; }
export function etaOf(beta){ return 0.78 - 0.00035 * (beta - 28) * (beta - 28); }

export function evaluatePump(rpm, beta, ind, cool){
  const u = 2 * Math.PI * rpm / 60 * PUMP.r;
  const head = psiOf(beta) * u * u / PUMP.g;
  const eff = etaOf(beta);
  const power = PUMP.rho * PUMP.g * PUMP.Q * head / eff;
  const nss = INDUCER[ind] || INDUCER.none;
  const npshr = Math.pow(rpm * Math.sqrt(PUMP.Qgpm) / nss, 4 / 3) * 0.3048;
  const temp = -150 + 0.0072 * rpm - 9.5 * cool;
  const vib = Math.abs(rpm - PUMP.Ncrit) / PUMP.Ncrit;
  const r = {
    u, head, eff, power, npshr, temp, vib,
    headOK: head >= PUMP.Hreq,
    cavOK: npshr <= PUMP.npshA,
    powerOK: power <= PUMP.Plimit,
    tempOK: temp <= PUMP.Tlimit,
    bleedOK: cool <= PUMP.bleedLimit,
    vibOK: vib >= PUMP.vibMargin
  };
  r.pass = r.headOK && r.cavOK && r.powerOK && r.tempOK && r.bleedOK && r.vibOK;
  /* 캐비테이션 심각도 0~1 — 기포 연출과 손상 누적에 쓴다 */
  r.cavSeverity = Math.max(0, Math.min(1, (r.npshr - PUMP.npshA) / 24));
  return r;
}

/* ═════════════ 3D — 터보펌프 시험 리그 ═════════════ */
export class PumpRig {
  constructor(canvas){
    this.canvas = canvas;
    this.engine = new Engine(canvas, true, { preserveDrawingBuffer: false, stencil: false });
    applyDPR(this.engine);
    this.scene = new Scene(this.engine);
    this.scene.clearColor = new Color4(0.018, 0.023, 0.035, 1);
    this.ready = false;
    this.rpm = 0;         // 현재 회전수 (rpm)
    this.cav = 0;         // 0~1 캐비테이션
    this.heat = 0;        // 0~1 베어링 가열
    this.shake = 0;       // 0~1 진동
    this._t = 0;
    this._spinAngle = 0;
    this._build();
    window.addEventListener("resize", () => {
      applyDPR(this.engine);       /* 모니터를 옮기면 DPR 이 바뀐다 */
      this.engine.resize();
    });
  }

  _build(){
    const sc = this.scene;
    const cam = new ArcRotateCamera("c", -Math.PI * 0.62, Math.PI * 0.46, 3.6,
                                    new Vector3(0, 1.35, 0), sc);
    cam.lowerRadiusLimit = 1.9;
    cam.upperRadiusLimit = 7.0;
    cam.lowerBetaLimit = 0.25;
    cam.upperBetaLimit = Math.PI * 0.49;
    cam.wheelPrecision = 42;
    cam.panningSensibility = 0;      /* 패닝은 막는다 — 대상을 잃어버린다 */
    cam.attachControl(this.canvas, true);
    this.cam = cam;
    this._camTarget = cam.target.clone();

    const hemi = new HemisphericLight("h", new Vector3(0.2, 1, 0.1), sc);
    hemi.intensity = 0.42;
    hemi.diffuse = new Color3(0.60, 0.68, 0.84);
    hemi.groundColor = new Color3(0.10, 0.11, 0.15);

    const key = new DirectionalLight("k", new Vector3(-0.55, -1, 0.42), sc);
    key.position = new Vector3(3.2, 5.4, -2.6);
    key.intensity = 2.4;
    this.key = key;
    const sg = new ShadowGenerator(1024, key);
    sg.usePercentageCloserFiltering = true;
    sg.bias = 0.0012;
    this.shadows = sg;

    const rim = new DirectionalLight("r", new Vector3(0.7, -0.35, -0.6), sc);
    rim.intensity = 0.75;
    rim.diffuse = new Color3(0.55, 0.72, 1.0);

    const ground = CreateGround("g", { width: 26, height: 26 }, sc);
    const gm = new PBRMaterial("gm", sc);
    gm.albedoColor = new Color3(0.045, 0.05, 0.062);
    gm.metallic = 0.1;
    gm.roughness = 0.85;
    ground.material = gm;
    ground.receiveShadows = true;

    this.glow = new GlowLayer("g", sc);
    this.glow.intensity = 0.7;

    const pipe = new DefaultRenderingPipeline("p", true, sc, [cam]);
    tunePipeline(pipe, { bloomThreshold: 0.76, bloomWeight: 0.26,
                        contrast: 1.12, exposure: 1.03, vignette: 1.0 });
    pipe.depthOfFieldEnabled = false;
  }

  async load(url){
    const sc = this.scene;
    await SceneLoader.AppendAsync("", url, sc);

    /* 회전체를 한 노드 아래로 모아 통째로 돌린다.
       메시마다 축을 계산해 돌리면 위치까지 손으로 회전시켜야 한다. */
    const spin = new TransformNode("spin", sc);
    this.spin = spin;
    this.inducers = { short: [], long: [] };
    this.blades = [];
    sc.meshes.forEach(m => {
      if(!m.name || m.name === "__root__") return;
      m.receiveShadows = true;
      this.shadows.addShadowCaster(m);
      if(/^rot_/.test(m.name)) m.setParent(spin);
      const mi = /^rot_ind_(short|long)_/.exec(m.name);
      if(mi) this.inducers[mi[1]].push(m);
      if(/^rot_blade_/.test(m.name)){
        m._baseY = m.rotation.y;
        this.blades.push(m);
      }
      if(/brg_house/.test(m.name)) this.bearing = m;
    });
    this.bearingMat = this.bearing ? this.bearing.material : null;
    this._cavity();
    this.setInducer("long");
    this.setBlade(28);
    this.ready = true;
    return this;
  }

  /** 인듀서 변형을 갈아 끼운다 — 플레이어 선택이 눈에 보여야 한다 */
  setInducer(kind){
    if(!this.inducers) return;
    ["short", "long"].forEach(k => {
      this.inducers[k].forEach(m => { m.setEnabled(kind === k); });
    });
    this.inducerKind = kind;
  }

  /** 블레이드 각도를 실제로 기울인다 (기준 28°) */
  setBlade(beta){
    if(!this.blades) return;
    const d = (beta - 28) * Math.PI / 180;
    this.blades.forEach(m => { m.rotation.y = m._baseY + d; });
    this.beta = beta;
  }

  /** 캐비테이션 기포 — 입구에서 피어오른다 */
  _cavity(){
    const sc = this.scene;
    const ps = new ParticleSystem("cav", 700, sc);
    ps.particleTexture = new Texture(this._dot(), sc);
    ps.emitter = new Vector3(0, 0.92, 0);
    ps.minEmitBox = new Vector3(-0.16, -0.06, -0.16);
    ps.maxEmitBox = new Vector3(0.16, 0.06, 0.16);
    ps.color1 = new Color4(0.80, 0.92, 1.0, 0.85);
    ps.color2 = new Color4(0.55, 0.75, 0.95, 0.6);
    ps.colorDead = new Color4(0.4, 0.6, 0.8, 0);
    ps.minSize = 0.014; ps.maxSize = 0.05;
    ps.minLifeTime = 0.25; ps.maxLifeTime = 0.7;
    ps.emitRate = 0;
    ps.direction1 = new Vector3(-0.5, 1.4, -0.5);
    ps.direction2 = new Vector3(0.5, 2.4, 0.5);
    ps.minEmitPower = 0.5; ps.maxEmitPower = 1.6;
    ps.gravity = new Vector3(0, 0.6, 0);
    ps.blendMode = ParticleSystem.BLENDMODE_STANDARD;
    ps.start();
    this.cavPS = ps;
  }

  _dot(){
    if(this._dotUrl) return this._dotUrl;
    const c = document.createElement("canvas");
    c.width = c.height = 64;
    const x = c.getContext("2d");
    const gr = x.createRadialGradient(32, 32, 0, 32, 32, 32);
    gr.addColorStop(0, "rgba(255,255,255,1)");
    gr.addColorStop(0.45, "rgba(255,255,255,0.55)");
    gr.addColorStop(1, "rgba(255,255,255,0)");
    x.fillStyle = gr;
    x.fillRect(0, 0, 64, 64);
    this._dotUrl = c.toDataURL();
    return this._dotUrl;
  }

  tick(dt){
    if(!this.ready) return;
    this._t += dt;

    /* 회전 — 화면에서는 실제 rpm 을 그대로 쓰면 스트로보로 멈춰 보인다.
       회전 느낌만 남기고 속도에 비례시킨다. */
    if(this.spin){
      this._spinAngle += (this.rpm / 30000) * 26 * dt;
      this.spin.rotation.y = this._spinAngle;
    }
    if(this.cavPS) this.cavPS.emitRate = 620 * this.cav;

    /* 베어링이 달아오른다 */
    if(this.bearingMat){
      const h = this.heat;
      this.bearingMat.emissiveColor = new Color3(0.95 * h, 0.22 * h * h, 0.04 * h * h);
      this.bearingMat.emissiveIntensity = 1.0;
    }
    if(this.glow) this.glow.intensity = 0.7 + 1.0 * this.heat + 0.5 * this.cav;

    /* 진동 — 임계 회전수에 가까우면 화면이 떨린다 */
    const sK = this.shake;
    if(sK > 0.001){
      const w = 2 * Math.PI * 17, a = 0.05 * sK;
      this.cam.target = this._camTarget.add(new Vector3(
        Math.sin(this._t * w) * a,
        Math.sin(this._t * w * 1.6 + 0.9) * a,
        Math.cos(this._t * w * 0.85) * a * 0.7));
    } else if(this.cam.target !== this._camTarget){
      this.cam.target = this._camTarget.clone();
    }
  }

  run(onFrame){
    this.engine.runRenderLoop(() => {
      const dt = Math.min(0.05, this.engine.getDeltaTime() / 1000);
      if(onFrame) onFrame(dt);
      this.tick(dt);
      this.scene.render();
    });
  }

  stop(){ this.engine.stopRenderLoop(); }

  dispose(){
    this.stop();
    this.scene.dispose();
    this.engine.dispose();
  }
}

/* 검증·디버그용으로 밖에서 잡을 수 있게 노출한다 */
window.DV3D = { TestStand, LabView, PumpRig, applyDPR, evaluate, evaluatePump,
                PHYS, PUMP, INDUCER, psiOf, etaOf, f1L, f1T };
