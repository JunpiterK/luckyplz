# -*- coding: utf-8 -*-
"""Generate the Color Vision Deficiency simulator tool (ko/en/ja/zh/es).

Fourth tool in the color-science suite. Simulates how colors and images appear
to viewers with protan / deutan / tritan color vision deficiency, at adjustable
severity, using the Machado, Oliveira & Fernandes (2009) physiologically-based
matrices (applied in LINEAR sRGB, the correct pipeline).

Features:
  - Type selector (Normal / Protan / Deutan / Tritan) + severity slider.
  - Built-in test chart (hue spectrum, confusable named swatches, gradients),
    Normal vs Simulated side by side on canvas.
  - Upload your own image (client-side only, never leaves the browser).
  - Single-color picker: original vs simulated swatch + hex.

The moat: the verified Machado 2009 matrices (all 11 severity levels per type,
element-wise interpolated) + the correct linearize -> matrix -> re-encode pipeline.

Output: public/tools/color-vision[/-en/-ja/-zh/-es]/index.html  (+ sitemap)
"""
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
TOOLS = PUBLIC / "tools"
SLUG = "color-vision"
DATE = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")

try:
    BUILD = json.loads((PUBLIC / "build.json").read_text(encoding="utf-8")).get("v", DATE)
except Exception:
    BUILD = DATE

_spec = importlib.util.spec_from_file_location("cdtool", ROOT / "scripts" / "gen-color-difference-tool.py")
_cd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cd)
BASE_CSS = _cd.CSS

LANGS = ("ko", "en", "ja", "zh", "es")
LANG_SUFFIX = {"ko": "", "en": "-en", "ja": "-ja", "zh": "-zh", "es": "-es"}
HTML_LANG = {"ko": "ko", "en": "en", "ja": "ja", "zh": "zh", "es": "es"}
OG_LOCALE = {"ko": "ko_KR", "en": "en_US", "ja": "ja_JP", "zh": "zh_CN", "es": "es_ES"}

META = {
    "ko": dict(
        title="색각이상 시뮬레이터 — 적·녹·청색각이상 색·이미지 변환 (Machado 2009) | Lucky Please",
        desc="적색각이상(protan)·녹색각이상(deutan)·청색각이상(tritan)이 색과 이미지를 어떻게 보는지 심각도 조절하며 시뮬레이션. Machado 2009 생리 기반 행렬을 선형 RGB에서 정확히 적용. 내장 테스트 차트 + 내 이미지 업로드(브라우저 내 처리, 전송 없음) + 색 선택기. 디자인 접근성·UI 색 검증용 전문 도구.",
        keywords="색각이상 시뮬레이터, 색맹 시뮬레이션, 적록색약, protanopia, deuteranopia, tritanopia, Machado 2009, 색약 변환, 접근성, 색맹 테스트",
        ogt="색각이상 시뮬레이터 — 적·녹·청 색약 변환",
        ogd="색·이미지가 적·녹·청색각이상에게 어떻게 보이는지 심각도 조절 시뮬. Machado 2009 정확 적용.",
    ),
    "en": dict(
        title="Color Blindness Simulator — Protan / Deutan / Tritan Color & Image (Machado 2009) | Lucky Please",
        desc="Simulate how protan, deutan and tritan color vision deficiency see colors and images, with an adjustable severity. Uses the Machado 2009 physiologically-based matrices, applied correctly in linear sRGB. Built-in test chart + upload your own image (processed in-browser, never uploaded) + single-color picker. A professional tool for design accessibility and UI color checking.",
        keywords="color blindness simulator, CVD simulation, protanopia, deuteranopia, tritanopia, Machado 2009, red-green color blind, accessibility, color blind test, daltonism",
        ogt="Color Blindness Simulator — Protan / Deutan / Tritan",
        ogd="See how colors and images look to protan/deutan/tritan viewers, severity adjustable. Machado 2009, done right.",
    ),
    "ja": dict(
        title="色覚異常シミュレーター — 1型・2型・3型 色覚の色・画像変換 (Machado 2009) | Lucky Please",
        desc="1型(protan)・2型(deutan)・3型(tritan)色覚が色や画像をどう見るかを、重症度を調整しながらシミュレーション。Machado 2009の生理学的行列を線形sRGBで正しく適用。内蔵テストチャート + 自分の画像アップロード(ブラウザ内処理、送信なし) + 単色ピッカー。デザインのアクセシビリティ・UI色検証向け専門ツール。",
        keywords="色覚異常シミュレーター, 色覚多様性, 1型2型色覚, protanopia, deuteranopia, tritanopia, Machado 2009, 色弱変換, アクセシビリティ, 色覚テスト",
        ogt="色覚異常シミュレーター — 1型・2型・3型",
        ogd="色や画像が1型・2型・3型色覚にどう見えるかを重症度調整でシミュレーション。Machado 2009準拠。",
    ),
    "zh": dict(
        title="色盲模拟器 — 红/绿/蓝色觉障碍的色彩与图像变换 (Machado 2009) | Lucky Please",
        desc="模拟红色盲(protan)、绿色盲(deutan)、蓝色盲(tritan)如何看待色彩与图像，可调节严重程度。采用Machado 2009生理学矩阵，在线性sRGB中正确应用。内置测试图 + 上传自己的图像(浏览器内处理，不上传) + 单色拾取器。面向设计无障碍与UI色彩检查的专业工具。",
        keywords="色盲模拟器, 色觉障碍模拟, 红绿色盲, protanopia, deuteranopia, tritanopia, Machado 2009, 色弱变换, 无障碍, 色盲测试",
        ogt="色盲模拟器 — 红/绿/蓝色觉障碍",
        ogd="模拟色彩与图像在红/绿/蓝色觉障碍者眼中的样子，严重程度可调。基于Machado 2009。",
    ),
    "es": dict(
        title="Simulador de Daltonismo — Color e Imagen Protan / Deutan / Tritan (Machado 2009) | Lucky Please",
        desc="Simula cómo el daltonismo protan, deutan y tritan ve los colores y las imágenes, con una severidad ajustable. Usa las matrices fisiológicas de Machado 2009, aplicadas correctamente en sRGB lineal. Gráfico de prueba integrado + sube tu propia imagen (procesada en el navegador, nunca se sube) + selector de un color. Herramienta profesional para accesibilidad de diseño y verificación de color de UI.",
        keywords="simulador de daltonismo, simulación CVD, protanopia, deuteranopia, tritanopia, Machado 2009, daltonismo rojo-verde, accesibilidad, test de daltonismo",
        ogt="Simulador de Daltonismo — Protan / Deutan / Tritan",
        ogd="Mira cómo ven los colores y las imágenes las personas protan/deutan/tritan, severidad ajustable. Machado 2009.",
    ),
}

S = {
    "h1": dict(ko="색각이상 시뮬레이터", en="Color Blindness Simulator", ja="色覚異常シミュレーター", zh="色盲模拟器", es="Simulador de Daltonismo"),
    "sub": dict(
        ko="적·녹·청색각이상이 보는 색·이미지 · 심각도 조절 · Machado 2009",
        en="How protan / deutan / tritan see color &amp; images · adjustable severity · Machado 2009",
        ja="1型・2型・3型色覚が見る色・画像 · 重症度調整 · Machado 2009",
        zh="红/绿/蓝色觉障碍所见的色彩与图像 · 可调严重度 · Machado 2009",
        es="Cómo ven el color y las imágenes protan / deutan / tritan · severidad ajustable · Machado 2009"),
    "typeLbl": dict(ko="유형", en="Type", ja="タイプ", zh="类型", es="Tipo"),
    "sev": dict(ko="심각도", en="Severity", ja="重症度", zh="严重度", es="Severidad"),
    "normal": dict(ko="정상 색각", en="Normal vision", ja="正常色覚", zh="正常色觉", es="Visión normal"),
    "simulated": dict(ko="시뮬레이션", en="Simulated", ja="シミュレーション", zh="模拟", es="Simulado"),
    "upload": dict(ko="내 이미지 업로드", en="Upload your image", ja="画像をアップロード", zh="上传图像", es="Subir tu imagen"),
    "reset": dict(ko="테스트 차트로", en="Test chart", ja="テストチャート", zh="测试图", es="Gráfico de prueba"),
    "privacy": dict(ko="이미지는 브라우저 안에서만 처리되며 어디에도 전송되지 않습니다.", en="Images are processed only in your browser and never uploaded.", ja="画像はブラウザ内でのみ処理され、送信されません。", zh="图像仅在浏览器内处理，不会上传。", es="Las imágenes se procesan solo en tu navegador y nunca se suben."),
    "picker": dict(ko="단색 확인", en="Single-color check", ja="単色チェック", zh="单色检查", es="Comprobar un color"),
    "orig": dict(ko="원래 색", en="Original", ja="元の色", zh="原色", es="Original"),
    "confTitle": dict(ko="흔한 혼동 색쌍", en="Common confusion pairs", ja="よくある混同色", zh="常见混淆色对", es="Pares de confusión comunes"),
    "confSub": dict(ko="아래 두 색이 비슷해 보일수록 그 유형이 구분하기 어려운 색입니다.", en="The more alike the two swatches look, the harder that pair is for this type.", ja="2色が似て見えるほど、そのタイプには区別しにくい色です。", zh="两色看起来越相似，该类型越难区分。", es="Cuanto más se parezcan las dos muestras, más difícil es ese par para este tipo."),
    "pipeline": dict(ko="계산 방법 · 수식", en="Method · formulas", ja="計算方法 · 数式", zh="计算方法 · 公式", es="Método · fórmulas"),
    "pipe_body": dict(
        ko="각 픽셀의 sRGB 값을 먼저 <b>선형 RGB</b>로 되돌린 뒤(역감마: c≤0.04045 면 c/12.92, 아니면 ((c+0.055)/1.055)<sup>2.4</sup>), <b>Machado 외(2009)</b>의 3×3 생리 기반 행렬을 곱하고, 다시 sRGB로 인코딩합니다. 이 모델은 망막의 추상체 분광 감도가 이동·소실되는 정도를 물리적으로 모사하므로, 단순 색상 회전보다 정확합니다.<br><br>유형은 세 가지입니다. <b>적색각이상(protan)</b>은 L추상체, <b>녹색각이상(deutan)</b>은 M추상체, <b>청색각이상(tritan)</b>은 S추상체가 영향을 받습니다. 심각도 0%는 정상, 100%는 완전 2색형(색맹)이며, 중간값은 인접한 두 표준 행렬을 원소별로 보간합니다.<br><br>※ 적·녹색각이상은 모델 신뢰도가 높지만, 청색각이상(tritan)은 희귀하고 특성화가 어려워 심각도 0.6 이상에서 정확도가 떨어집니다(원 논문도 명시). 이 도구는 진단용이 아니라 디자인 검증용입니다. 행렬 값은 DaltonLens 레퍼런스와 일치합니다.",
        en="Each pixel's sRGB value is first converted back to <b>linear RGB</b> (inverse gamma: c/12.92 if c≤0.04045, else ((c+0.055)/1.055)<sup>2.4</sup>), then multiplied by the 3×3 physiologically-based matrix of <b>Machado et al. (2009)</b>, and re-encoded to sRGB. The model physically simulates how the retinal cone spectral sensitivities shift and collapse, so it is more accurate than a naive hue rotation.<br><br>There are three types: <b>protan</b> affects the L cone, <b>deutan</b> the M cone, <b>tritan</b> the S cone. Severity 0% is normal, 100% is full dichromacy, and intermediate values element-wise interpolate the two adjacent published matrices.<br><br>※ The protan and deutan models are reliable; the tritan model is less accurate above ~0.6 severity because tritan is rare and hard to characterize (the original paper says so). This tool is for design checking, not diagnosis. The matrix values match the DaltonLens reference.",
        ja="各ピクセルのsRGB値をまず<b>線形RGB</b>に戻し(逆ガンマ: c≤0.04045ならc/12.92、それ以外は((c+0.055)/1.055)<sup>2.4</sup>)、<b>Machado他(2009)</b>の3×3生理学的行列を掛け、再びsRGBにエンコードします。このモデルは網膜の錐体分光感度が移動・消失する度合いを物理的に模倣するため、単純な色相回転より正確です。<br><br>タイプは3つ。<b>1型(protan)</b>はL錐体、<b>2型(deutan)</b>はM錐体、<b>3型(tritan)</b>はS錐体が影響を受けます。重症度0%は正常、100%は完全2色覚で、中間値は隣接する2つの標準行列を要素ごとに補間します。<br><br>※ 1型・2型は信頼性が高いですが、3型(tritan)は希少で特性化が難しく、重症度0.6以上で精度が落ちます(原論文も明記)。本ツールは診断用ではなく設計検証用です。行列値はDaltonLensリファレンスと一致します。",
        zh="先将每个像素的sRGB值还原为<b>线性RGB</b>(逆伽马: c≤0.04045时c/12.92，否则((c+0.055)/1.055)<sup>2.4</sup>)，再乘以<b>Machado等(2009)</b>的3×3生理学矩阵，然后重新编码为sRGB。该模型物理地模拟视网膜锥体光谱敏感度的偏移与坍缩，因此比单纯的色相旋转更准确。<br><br>共三种类型: <b>红色盲(protan)</b>影响L锥体，<b>绿色盲(deutan)</b>影响M锥体，<b>蓝色盲(tritan)</b>影响S锥体。严重度0%为正常，100%为完全二色觉，中间值对相邻两个标准矩阵逐元素插值。<br><br>※ 红、绿色盲模型可靠，但蓝色盲(tritan)罕见且难以表征，严重度0.6以上精度下降(原论文亦说明)。本工具用于设计检查而非诊断。矩阵值与DaltonLens参考一致。",
        es="El valor sRGB de cada píxel se convierte primero de vuelta a <b>RGB lineal</b> (gamma inversa: c/12.92 si c≤0.04045, si no ((c+0.055)/1.055)<sup>2.4</sup>), luego se multiplica por la matriz fisiológica 3×3 de <b>Machado et al. (2009)</b> y se vuelve a codificar a sRGB. El modelo simula físicamente cómo las sensibilidades espectrales de los conos retinianos se desplazan y colapsan, así que es más preciso que una simple rotación de tono.<br><br>Hay tres tipos: <b>protan</b> afecta al cono L, <b>deutan</b> al cono M, <b>tritan</b> al cono S. Severidad 0% es normal, 100% es dicromacia total, y los valores intermedios interpolan elemento a elemento las dos matrices publicadas adyacentes.<br><br>※ Los modelos protan y deutan son fiables; el modelo tritan es menos preciso por encima de ~0.6 de severidad porque el tritan es raro y difícil de caracterizar (lo dice el artículo original). Esta herramienta es para verificación de diseño, no para diagnóstico. Los valores de la matriz coinciden con la referencia DaltonLens."),
    "foot": dict(
        ko="이 시뮬레이터는 Machado 외(2009) 생리 기반 모델로 색각이상을 재현합니다. 색 인지의 원리(L·M·S 추상체)는 색채과학 시리즈에서 다룹니다.",
        en="This simulator reproduces color vision deficiency with the Machado et al. (2009) physiologically-based model. How color perception works (the L/M/S cones) is explained in the Color Science series.",
        ja="本シミュレーターはMachado他(2009)の生理学的モデルで色覚異常を再現します。色知覚の原理(L・M・S錐体)は色彩科学シリーズで解説しています。",
        zh="本模拟器用Machado等(2009)生理学模型重现色觉障碍。色彩感知的原理(L/M/S锥体)见色彩科学系列。",
        es="Este simulador reproduce el daltonismo con el modelo fisiológico de Machado et al. (2009). Cómo funciona la percepción del color (los conos L/M/S) se explica en la serie de Ciencia del Color."),
    "readArt": dict(ko="색채과학 시리즈 읽기 →", en="Read the Color Science series →", ja="色彩科学シリーズを読む →", zh="阅读色彩科学系列 →", es="Leer la serie de Ciencia del Color →"),
    "home": dict(ko="홈", en="Home", ja="ホーム", zh="首页", es="Inicio"),
}

# type option labels (scientific term + localized short hint)
TYPE_OPTS = {
    "ko": [("normal", "정상"), ("protan", "적색각이상 (Protan)"), ("deutan", "녹색각이상 (Deutan)"), ("tritan", "청색각이상 (Tritan)")],
    "en": [("normal", "Normal"), ("protan", "Protan (red)"), ("deutan", "Deutan (green)"), ("tritan", "Tritan (blue)")],
    "ja": [("normal", "正常"), ("protan", "1型 Protan (赤)"), ("deutan", "2型 Deutan (緑)"), ("tritan", "3型 Tritan (青)")],
    "zh": [("normal", "正常"), ("protan", "红色盲 Protan"), ("deutan", "绿色盲 Deutan"), ("tritan", "蓝色盲 Tritan")],
    "es": [("normal", "Normal"), ("protan", "Protan (rojo)"), ("deutan", "Deutan (verde)"), ("tritan", "Tritan (azul)")],
}

JS_CORE = r"""
// Machado, Oliveira & Fernandes (2009). LINEAR sRGB, row-major 3x3.
// Index 0..10 == severity 0.0..1.0. Matches DaltonLens reference.
var MACHADO={
 protan:[[1,0,0,0,1,0,0,0,1],
  [0.856167,0.182038,-0.038205,0.029342,0.955115,0.015544,-0.002880,-0.001563,1.004443],
  [0.734766,0.334872,-0.069637,0.051840,0.919198,0.028963,-0.004928,-0.004209,1.009137],
  [0.630323,0.465641,-0.095964,0.069181,0.890046,0.040773,-0.006308,-0.007724,1.014032],
  [0.539009,0.579343,-0.118352,0.082546,0.866121,0.051332,-0.007136,-0.011959,1.019095],
  [0.458064,0.679578,-0.137642,0.092785,0.846313,0.060902,-0.007494,-0.016807,1.024301],
  [0.385450,0.769005,-0.154455,0.100526,0.829802,0.069673,-0.007442,-0.022190,1.029632],
  [0.319627,0.849633,-0.169261,0.106241,0.815969,0.077790,-0.007025,-0.028051,1.035076],
  [0.259411,0.923008,-0.182420,0.110296,0.804340,0.085364,-0.006276,-0.034346,1.040622],
  [0.203876,0.990338,-0.194214,0.112975,0.794542,0.092483,-0.005222,-0.041043,1.046265],
  [0.152286,1.052583,-0.204868,0.114503,0.786281,0.099216,-0.003882,-0.048116,1.051998]],
 deutan:[[1,0,0,0,1,0,0,0,1],
  [0.866435,0.177704,-0.044139,0.049567,0.939063,0.011370,-0.003453,0.007233,0.996220],
  [0.760729,0.319078,-0.079807,0.090568,0.889315,0.020117,-0.006027,0.013325,0.992702],
  [0.675425,0.433850,-0.109275,0.125303,0.847755,0.026942,-0.007950,0.018572,0.989378],
  [0.605511,0.528560,-0.134071,0.155318,0.812366,0.032316,-0.009376,0.023176,0.986200],
  [0.547494,0.607765,-0.155259,0.181692,0.781742,0.036566,-0.010410,0.027275,0.983136],
  [0.498864,0.674741,-0.173604,0.205199,0.754872,0.039929,-0.011131,0.030969,0.980162],
  [0.457771,0.731899,-0.189670,0.226409,0.731012,0.042579,-0.011595,0.034333,0.977261],
  [0.422823,0.781057,-0.203881,0.245752,0.709602,0.044646,-0.011843,0.037423,0.974421],
  [0.392952,0.823610,-0.216562,0.263559,0.690210,0.046232,-0.011910,0.040281,0.971630],
  [0.367322,0.860646,-0.227968,0.280085,0.672501,0.047413,-0.011820,0.042940,0.968881]],
 tritan:[[1,0,0,0,1,0,0,0,1],
  [0.926670,0.092514,-0.019184,0.021191,0.964503,0.014306,0.008437,0.054813,0.936750],
  [0.895720,0.133330,-0.029050,0.029997,0.945400,0.024603,0.013027,0.104707,0.882266],
  [0.905871,0.127791,-0.033662,0.026856,0.941251,0.031893,0.013410,0.148296,0.838294],
  [0.948035,0.089490,-0.037526,0.014364,0.946792,0.038844,0.010853,0.193991,0.795156],
  [1.017277,0.027029,-0.044306,-0.006113,0.958479,0.047634,0.006379,0.248708,0.744913],
  [1.104996,-0.046633,-0.058363,-0.032137,0.971635,0.060503,0.001336,0.317922,0.680742],
  [1.193214,-0.109812,-0.083402,-0.058496,0.979410,0.079086,-0.002346,0.403492,0.598854],
  [1.257728,-0.139648,-0.118081,-0.078003,0.975409,0.102594,-0.003316,0.501214,0.502102],
  [1.278864,-0.125333,-0.153531,-0.084748,0.957674,0.127074,-0.000989,0.601151,0.399838],
  [1.255528,-0.076749,-0.178779,-0.078411,0.930809,0.147602,0.004733,0.691367,0.303900]]};
function machadoMatrix(type,s){
 if(type==='normal')return [1,0,0,0,1,0,0,0,1];
 var t=MACHADO[type];var x=Math.min(Math.max(s,0),1)*10;var lo=Math.floor(x),hi=Math.min(lo+1,10),f=x-lo;
 var out=[];for(var i=0;i<9;i++)out.push(t[lo][i]*(1-f)+t[hi][i]*f);return out;
}
// sRGB linearize LUT + encode
var LIN=new Float32Array(256);for(var _i=0;_i<256;_i++){var _c=_i/255;LIN[_i]=_c<=0.04045?_c/12.92:Math.pow((_c+0.055)/1.055,2.4);}
function enc(v){v=v<0?0:(v>1?1:v);return v<=0.0031308?v*12.92:1.055*Math.pow(v,1/2.4)-0.055;}
function simRGB(r,g,b,m){
 var R=LIN[r],G=LIN[g],B=LIN[b];
 var nr=m[0]*R+m[1]*G+m[2]*B,ng=m[3]*R+m[4]*G+m[5]*B,nb=m[6]*R+m[7]*G+m[8]*B;
 return [Math.round(enc(nr)*255),Math.round(enc(ng)*255),Math.round(enc(nb)*255)];
}
function simImage(srcData,dst,m){
 var s=srcData.data,d=dst.data;
 for(var i=0;i<s.length;i+=4){var R=LIN[s[i]],G=LIN[s[i+1]],B=LIN[s[i+2]];
  var nr=m[0]*R+m[1]*G+m[2]*B,ng=m[3]*R+m[4]*G+m[5]*B,nb=m[6]*R+m[7]*G+m[8]*B;
  d[i]=Math.round(enc(nr)*255);d[i+1]=Math.round(enc(ng)*255);d[i+2]=Math.round(enc(nb)*255);d[i+3]=s[i+3];}
}
function hex2rgb(h){h=h.replace('#','');return [parseInt(h.substr(0,2),16),parseInt(h.substr(2,2),16),parseInt(h.substr(4,2),16)];}
function rgb2css(a){return 'rgb('+a[0]+','+a[1]+','+a[2]+')';}

// ---- built-in test chart drawn into the source canvas ----
function drawChart(ctx,w,h){
 ctx.clearRect(0,0,w,h);
 // 1) hue spectrum strip (top 28%)
 var hb=Math.round(h*0.28);
 for(var x=0;x<w;x++){var hue=x/w*360;ctx.fillStyle='hsl('+hue+',95%,50%)';ctx.fillRect(x,0,1,hb);}
 // 2) saturation ramp for a red->green confusion band (next 22%)
 var y2=hb,hb2=Math.round(h*0.22);
 for(var x2=0;x2<w;x2++){var t=x2/w;var hue2=t*140;ctx.fillStyle='hsl('+hue2+',80%,45%)';ctx.fillRect(x2,y2,1,hb2);}
 // 3) confusable named swatches grid (bottom)
 var y3=hb+hb2, rowH=h-y3;
 var cols=['#d11f1f','#2e7d32','#b5651d','#e8a33d','#1f6fd1','#7b4fc4','#e36fb0','#9aa0a6','#1d1d1d','#f2f2f2'];
 var cw=w/cols.length;
 for(var c=0;c<cols.length;c++){ctx.fillStyle=cols[c];ctx.fillRect(Math.round(c*cw),y3,Math.ceil(cw),rowH);}
}

var SRC=null,W=0,H=0; // source ImageData + dims
function rerender(){
 var type=document.getElementById('typeSel').value;
 var sev=parseInt(document.getElementById('sevR').value,10)/100;
 document.getElementById('sevV').textContent=Math.round(sev*100)+'%';
 var m=machadoMatrix(type,sev);
 var oc=document.getElementById('cvOrig'),sc=document.getElementById('cvSim');
 var octx=oc.getContext('2d'),sctx=sc.getContext('2d');
 octx.putImageData(SRC,0,0);
 var out=sctx.createImageData(W,H);simImage(SRC,out,m);sctx.putImageData(out,0,0);
 // single color picker
 var hex=document.getElementById('pick').value;var rgb=hex2rgb(hex);
 document.getElementById('swOrig').style.background=rgb2css(rgb);
 var so=simRGB(rgb[0],rgb[1],rgb[2],m);
 document.getElementById('swSim').style.background=rgb2css(so);
 document.getElementById('swSimHex').textContent='#'+so.map(function(v){return ('0'+v.toString(16)).slice(-2);}).join('');
 // confusion pairs
 var pairs=[['#c81e1e','#1f7a1f'],['#1d6fd1','#7b3fc4'],['#d98a1e','#1f7a4f']];
 var pe=document.getElementById('confPairs');pe.innerHTML='';
 pairs.forEach(function(pr){
  var a=hex2rgb(pr[0]),b=hex2rgb(pr[1]);var sa=simRGB(a[0],a[1],a[2],m),sb=simRGB(b[0],b[1],b[2],m);
  var box=document.createElement('div');box.className='cp';
  box.innerHTML='<div class="pair"><span style="background:'+rgb2css(a)+'"></span><span style="background:'+rgb2css(b)+'"></span></div>'+
   '<div class="arrow">&#8595;</div><div class="pair"><span style="background:'+rgb2css(sa)+'"></span><span style="background:'+rgb2css(sb)+'"></span></div>';
  pe.appendChild(box);
 });
}
function fitDraw(img){
 var maxW=440,maxH=300;var r=Math.min(maxW/img.width,maxH/img.height,1);
 W=Math.max(1,Math.round(img.width*r));H=Math.max(1,Math.round(img.height*r));
 sizeCanvases();var oc=document.getElementById('cvOrig').getContext('2d');oc.drawImage(img,0,0,W,H);SRC=oc.getImageData(0,0,W,H);rerender();
}
function sizeCanvases(){['cvOrig','cvSim'].forEach(function(id){var c=document.getElementById(id);c.width=W;c.height=H;});}
function loadChart(){
 W=440;H=300;sizeCanvases();
 var oc=document.getElementById('cvOrig').getContext('2d');drawChart(oc,W,H);SRC=oc.getImageData(0,0,W,H);rerender();
}
function init(){
 loadChart();
 document.getElementById('typeSel').addEventListener('change',rerender);
 document.getElementById('sevR').addEventListener('input',rerender);
 document.getElementById('pick').addEventListener('input',rerender);
 document.getElementById('btnChart').addEventListener('click',function(e){e.preventDefault();loadChart();});
 document.getElementById('imgUp').addEventListener('change',function(e){
  var f=e.target.files&&e.target.files[0];if(!f)return;var rd=new FileReader();
  rd.onload=function(ev){var img=new Image();img.onload=function(){fitDraw(img);};img.src=ev.target.result;};rd.readAsDataURL(f);
 });
}
if(document.readyState!=='loading')init();else document.addEventListener('DOMContentLoaded',init);
"""


EXTRA_CSS = """
.cv-grid{display:grid;grid-template-columns:1fr;gap:12px;margin-top:6px}
@media(min-width:620px){.cv-grid{grid-template-columns:1fr 1fr}}
.cv-pane{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px;text-align:center}
.cv-pane .lab{font-size:11.5px;font-weight:700;color:var(--mute);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}
.cv-pane canvas{width:100%;height:auto;border-radius:8px;background:#000;image-rendering:auto}
.cv-actions{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin:14px 0 4px}
.cv-actions .upl{position:relative;overflow:hidden;display:inline-flex;align-items:center;gap:6px;background:var(--card2);border:1px solid var(--line);border-radius:9px;padding:9px 13px;font-size:13px;font-weight:700;color:var(--accent);cursor:pointer}
.cv-actions .upl input{position:absolute;inset:0;opacity:0;cursor:pointer}
.cv-actions .ghost{background:none;border:1px solid var(--line);border-radius:9px;padding:9px 13px;font-size:13px;font-weight:700;color:var(--dim);cursor:pointer;font-family:inherit}
.privacy{font-size:10.5px;color:var(--mute);margin-top:6px}
.range-row{display:flex;align-items:center;gap:11px}
.range-row input[type=range]{flex:1;accent-color:var(--accent)}
.range-row .val{font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--accent);min-width:42px;text-align:right;font-weight:700}
.pick-row{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:6px}
.pick-row input[type=color]{width:54px;height:42px;border:1px solid var(--line);border-radius:9px;background:var(--card2);cursor:pointer;padding:3px}
.pk{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--dim)}
.pk .chip{width:40px;height:40px;border-radius:8px;border:1px solid #0006}
.conf-wrap{display:flex;gap:14px;flex-wrap:wrap;margin-top:6px}
.conf-wrap .cp{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:11px 13px;text-align:center}
.conf-wrap .pair{display:flex;gap:0}
.conf-wrap .pair span{width:34px;height:30px;display:block}
.conf-wrap .pair span:first-child{border-radius:6px 0 0 6px}
.conf-wrap .pair span:last-child{border-radius:0 6px 6px 0}
.conf-wrap .arrow{font-size:13px;color:var(--mute);margin:3px 0}
"""

CSS = BASE_CSS + EXTRA_CSS

TEMPLATE = """<!DOCTYPE html>
<html lang="{{HTMLLANG}}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!--lp-build-check:start-->
<meta name="lp-build" content="{{BUILD}}">
<script>(function(){try{if(!/KAKAOTALK/i.test(navigator.userAgent||""))return;var K="lp_kko_out";try{if(sessionStorage.getItem(K))return;sessionStorage.setItem(K,"1");}catch(e){}location.href="kakaotalk://web/openExternal?url="+encodeURIComponent(location.href);}catch(e){}})();</script>
<script>(function(){var B="{{BUILD}}";try{fetch("/build.json?_="+Date.now(),{cache:"no-store"}).then(function(r){return r.ok?r.json():null}).then(function(d){if(!d||!d.v||d.v===B)return;var k="lp_build_"+B;try{if(sessionStorage.getItem(k))return;sessionStorage.setItem(k,"1");}catch(e){}var u=new URL(location.href);u.searchParams.set("_b",d.v);location.replace(u.toString());}).catch(function(){});}catch(e){}})();</script>
<!--lp-build-check:end-->
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<title>{{TITLE}}</title>
<meta name="description" content="{{DESC}}">
<meta name="keywords" content="{{KEYWORDS}}">
<link rel="canonical" href="{{CANON}}">
<link rel="alternate" hreflang="ko" href="https://luckyplz.com/tools/color-vision/">
<link rel="alternate" hreflang="en" href="https://luckyplz.com/tools/color-vision-en/">
<link rel="alternate" hreflang="ja" href="https://luckyplz.com/tools/color-vision-ja/">
<link rel="alternate" hreflang="zh" href="https://luckyplz.com/tools/color-vision-zh/">
<link rel="alternate" hreflang="es" href="https://luckyplz.com/tools/color-vision-es/">
<link rel="alternate" hreflang="x-default" href="https://luckyplz.com/tools/color-vision-en/">
<meta property="og:type" content="website">
<meta property="og:title" content="{{OGT}}">
<meta property="og:description" content="{{OGD}}">
<meta property="og:url" content="{{CANON}}">
<meta property="og:image" content="https://luckyplz.com/assets/blog/cs-cie1931-gamut.png?v={{BUILD}}">
<meta property="og:locale" content="{{OGLOCALE}}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{OGT}}">
<meta name="twitter:description" content="{{OGD}}">
<script type="application/ld+json">{{JSONLD}}</script>
<script type="application/ld+json">{{CRUMB}}</script>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0b0f17">
<link rel="apple-touch-icon" href="/assets/icon-192.png">
<link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5370817769801923" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NZDPE3H3DQ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-NZDPE3H3DQ');</script>
<style>{{CSS}}</style>
</head>
<body>
<div class="topbar"><a href="/tools/">← {{HOME}}</a><a href="/">luckyplz.com</a></div>
<div class="wrap">
  <h1>{{H1}}</h1>
  <div class="sub">{{SUB}}</div>
  <div id="lp-langbar"></div>

  <div class="controls">
    <div class="f"><label>{{TYPELBL}}</label><select id="typeSel">{{TYPEOPTS}}</select></div>
    <div class="f" style="flex:2;min-width:180px"><label>{{SEV}} <span id="sevV" style="color:var(--accent)">100%</span></label>
      <div class="range-row"><input type="range" id="sevR" min="0" max="100" value="100" step="1"></div></div>
  </div>

  <div class="cv-grid">
    <div class="cv-pane"><div class="lab">{{NORMAL}}</div><canvas id="cvOrig"></canvas></div>
    <div class="cv-pane"><div class="lab">{{SIMULATED}}</div><canvas id="cvSim"></canvas></div>
  </div>
  <div class="cv-actions">
    <label class="upl">📷 {{UPLOAD}}<input type="file" id="imgUp" accept="image/*"></label>
    <button class="ghost" id="btnChart">{{RESET}}</button>
  </div>
  <div class="privacy">🔒 {{PRIVACY}}</div>

  <div class="sec-h">{{PICKER}}</div>
  <div class="pick-row">
    <input type="color" id="pick" value="#d11f1f">
    <div class="pk"><span>{{ORIG}}</span><span class="chip" id="swOrig"></span></div>
    <div class="pk"><span>{{SIMULATED}}</span><span class="chip" id="swSim"></span><span id="swSimHex" style="font-family:'JetBrains Mono',monospace;font-size:12px"></span></div>
  </div>

  <div class="sec-h">{{CONFTITLE}}</div>
  <div class="conf-wrap" id="confPairs"></div>
  <div class="privacy" style="margin-top:8px">{{CONFSUB}}</div>

  <details><summary>{{PIPELINE}}</summary><div class="body">{{PIPEBODY}}</div></details>

  <footer>{{FOOT}}<br><a href="{{ARTURL}}">{{READART}}</a> · <a href="/tools/">/tools</a> · <a href="/">{{HOME}}</a></footer>
</div>
<script>{{JSCORE}}</script>
<script>navigator.serviceWorker&&navigator.serviceWorker.getRegistrations().then(function(rs){rs.forEach(function(r){r.unregister()})});</script>
<script src="/js/langSelect.js?v={{BUILD}}" defer></script>
<script src="/js/siteFooter.js?v={{BUILD}}" defer></script>
</body>
</html>
"""


def type_opts(lang):
    return "".join(
        f'<option value="{v}"{" selected" if v=="deutan" else ""}>{lbl}</option>'
        for v, lbl in TYPE_OPTS[lang])


def build(lang):
    m = META[lang]
    canon = f"https://luckyplz.com/tools/{SLUG}{LANG_SUFFIX[lang]}/"
    art = {"ko": "/blog/color-science-01-how-we-see/", "en": "/blog/color-science-01-how-we-see-en/",
           "ja": "/blog/color-science-01-how-we-see-ja/", "zh": "/blog/color-science-01-how-we-see-zh/",
           "es": "/blog/color-science-01-how-we-see-en/"}[lang]
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": m["ogt"],
        "description": m["desc"][:200], "url": canon, "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Any (web browser)", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "inLanguage": lang}, ensure_ascii=False)
    crumb = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": S["home"][lang], "item": "https://luckyplz.com/"},
            {"@type": "ListItem", "position": 2, "name": "Tools", "item": "https://luckyplz.com/tools/"},
            {"@type": "ListItem", "position": 3, "name": m["ogt"], "item": canon}]}, ensure_ascii=False)
    repl = {
        "{{HTMLLANG}}": HTML_LANG[lang], "{{BUILD}}": BUILD, "{{TITLE}}": m["title"],
        "{{DESC}}": m["desc"], "{{KEYWORDS}}": m["keywords"], "{{CANON}}": canon,
        "{{OGT}}": m["ogt"], "{{OGD}}": m["ogd"], "{{OGLOCALE}}": OG_LOCALE[lang],
        "{{JSONLD}}": jsonld, "{{CRUMB}}": crumb, "{{CSS}}": CSS,
        "{{JSCORE}}": JS_CORE, "{{TYPEOPTS}}": type_opts(lang), "{{ARTURL}}": art,
        "{{H1}}": S["h1"][lang], "{{SUB}}": S["sub"][lang], "{{TYPELBL}}": S["typeLbl"][lang], "{{SEV}}": S["sev"][lang],
        "{{NORMAL}}": S["normal"][lang], "{{SIMULATED}}": S["simulated"][lang], "{{UPLOAD}}": S["upload"][lang],
        "{{RESET}}": S["reset"][lang], "{{PRIVACY}}": S["privacy"][lang], "{{PICKER}}": S["picker"][lang],
        "{{ORIG}}": S["orig"][lang], "{{CONFTITLE}}": S["confTitle"][lang], "{{CONFSUB}}": S["confSub"][lang],
        "{{PIPELINE}}": S["pipeline"][lang], "{{PIPEBODY}}": S["pipe_body"][lang],
        "{{FOOT}}": S["foot"][lang], "{{READART}}": S["readArt"][lang], "{{HOME}}": S["home"][lang],
    }
    out = TEMPLATE
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


def update_sitemap():
    p = PUBLIC / "sitemap.xml"
    raw = p.read_text(encoding="utf-8")
    if f"tools/{SLUG}/" in raw:
        print("[sitemap] already present")
        return
    base = "https://luckyplz.com/tools/"
    alts = {l: f"{base}{SLUG}{LANG_SUFFIX[l]}/" for l in LANGS}
    blocks = []
    for lang, url in alts.items():
        links = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{u}"/>' for l, u in alts.items())
        links += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{alts["en"]}"/>'
        blocks.append(f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{DATE}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>{links}\n  </url>')
    raw = raw.replace("</urlset>", "\n" + "\n".join(blocks) + "\n</urlset>")
    p.write_text(raw, encoding="utf-8")
    print(f"[sitemap] added {len(LANGS)} url blocks")


def main():
    for lang in LANGS:
        d = TOOLS / f"{SLUG}{LANG_SUFFIX[lang]}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(build(lang), encoding="utf-8")
        print(f"[write] {d}/index.html")
    update_sitemap()
    print("[done] color-vision tool")


if __name__ == "__main__":
    main()
