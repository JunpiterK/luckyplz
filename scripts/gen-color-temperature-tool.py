# -*- coding: utf-8 -*-
"""Generate the Color Temperature / White Point converter tool (ko/en/ja/zh/es).

Third tool in the color-science suite. Bidirectional:
  - From temperature: CCT (+ Duv offset, Planckian or Daylight locus) -> CIE xy,
    u'v', sRGB swatch, nearest standard illuminant.
  - From coordinates: x, y -> CCT (McCamy) + Duv (nearest-Planckian, signed).

The diagram draws the Planckian locus and CIE daylight locus as JS-computed
curves over the shared CIE 1931 gamut PNG, plus the standard illuminant points.

Verified math (the moat):
  - Planckian locus: Kim et al. (2002) piecewise cubic (x_c break 4000K; y_c
    breaks 2222K, 4000K).
  - CCT from xy: McCamy (1992) cubic.
  - Duv: CIE 1960 uv, signed distance to the Planckian locus (Ohno 2013 idea,
    dense-sampled nearest point).
  - Daylight locus: CIE 15 (x_D break 7000K; y_D single quadratic).
  - Standard illuminant white points: CIE 15:2004, 2° observer.

Output: public/tools/color-temperature[/-en/-ja/-zh/-es]/index.html  (+ sitemap)
"""
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
TOOLS = PUBLIC / "tools"
SLUG = "color-temperature"
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
        title="색온도·백색점 변환기 — CCT ↔ CIE xy, Duv, 플랑크 궤적 | Lucky Please",
        desc="색온도(CCT)와 CIE 1931 x,y를 양방향 변환합니다. 온도+Duv로 백색점 좌표를, 좌표로부터 CCT(McCamy)·Duv를 산출. 플랑크(흑체)·주광(D) 궤적과 표준 광원(A·D50·D65·F2 등)을 색도도에 함께 표시. 디스플레이 화이트밸런스·조명 평가용 전문 도구.",
        keywords="색온도 변환, CCT, 백색점, Duv, 플랑크 궤적, McCamy, D65, 색온도 계산기, 화이트밸런스, 표준 광원, color temperature converter",
        ogt="색온도·백색점 변환기 — CCT ↔ xy, Duv",
        ogd="색온도와 CIE xy를 양방향 변환하고 Duv·플랑크 궤적·표준 광원을 색도도에 표시.",
    ),
    "en": dict(
        title="Color Temperature & White Point Converter — CCT ↔ CIE xy, Duv, Planckian Locus | Lucky Please",
        desc="Convert between correlated color temperature (CCT) and CIE 1931 x,y both ways. From temperature + Duv get the white-point coordinates; from coordinates get CCT (McCamy) and Duv. Planckian (blackbody) and daylight (D) loci plus standard illuminants (A, D50, D65, F2…) drawn on the chromaticity diagram. A professional tool for display white balance and lighting.",
        keywords="color temperature converter, CCT, white point, Duv, Planckian locus, McCamy, D65, color temperature calculator, white balance, standard illuminant",
        ogt="Color Temperature & White Point Converter",
        ogd="Convert CCT ↔ CIE xy both ways, with Duv, the Planckian locus and standard illuminants on the diagram.",
    ),
    "ja": dict(
        title="色温度・白色点変換ツール — CCT ↔ CIE xy, Duv, 黒体軌跡 | Lucky Please",
        desc="相関色温度(CCT)とCIE 1931 x,yを双方向変換。温度+Duvから白色点座標を、座標からCCT(McCamy)・Duvを算出。黒体(プランク)・昼光(D)軌跡と標準光源(A・D50・D65・F2など)を色度図に表示。ディスプレイのホワイトバランス・照明評価向け専門ツール。",
        keywords="色温度変換, CCT, 白色点, Duv, 黒体軌跡, プランク軌跡, McCamy, D65, 色温度計算, ホワイトバランス, 標準光源",
        ogt="色温度・白色点変換ツール — CCT ↔ xy, Duv",
        ogd="色温度とCIE xyを双方向変換し、Duv・黒体軌跡・標準光源を色度図に表示。",
    ),
    "zh": dict(
        title="色温与白点转换器 — CCT ↔ CIE xy, Duv, 普朗克轨迹 | Lucky Please",
        desc="在相关色温(CCT)与CIE 1931 x,y之间双向转换。由温度+Duv求白点坐标，由坐标求CCT(McCamy)与Duv。在色度图上绘制普朗克(黑体)与日光(D)轨迹及标准光源(A·D50·D65·F2等)。面向显示白平衡与照明评估的专业工具。",
        keywords="色温转换, CCT, 白点, Duv, 普朗克轨迹, 黑体轨迹, McCamy, D65, 色温计算, 白平衡, 标准光源",
        ogt="色温与白点转换器 — CCT ↔ xy, Duv",
        ogd="双向转换色温与CIE xy，在色度图上显示Duv·普朗克轨迹·标准光源。",
    ),
    "es": dict(
        title="Conversor de Temperatura de Color y Punto Blanco — CCT ↔ CIE xy, Duv, Locus Planckiano | Lucky Please",
        desc="Convierte entre temperatura de color correlacionada (CCT) y CIE 1931 x,y en ambos sentidos. Desde temperatura + Duv obtén las coordenadas del punto blanco; desde coordenadas obtén CCT (McCamy) y Duv. Locus planckiano (cuerpo negro) y de luz de día (D) más iluminantes estándar (A, D50, D65, F2…) dibujados en el diagrama de cromaticidad. Herramienta profesional para balance de blancos e iluminación.",
        keywords="conversor de temperatura de color, CCT, punto blanco, Duv, locus planckiano, McCamy, D65, calculadora de temperatura de color, balance de blancos, iluminante estándar",
        ogt="Conversor de Temperatura de Color y Punto Blanco",
        ogd="Convierte CCT ↔ CIE xy en ambos sentidos, con Duv, el locus planckiano y los iluminantes estándar.",
    ),
}

S = {
    "h1": dict(ko="색온도·백색점 변환기", en="Color Temperature &amp; White Point", ja="色温度・白色点変換", zh="色温与白点转换器", es="Temperatura de Color y Punto Blanco"),
    "sub": dict(
        ko="CCT ↔ CIE xy · Duv · 플랑크(흑체)·주광 궤적 · 표준 광원",
        en="CCT ↔ CIE xy · Duv · Planckian &amp; daylight loci · standard illuminants",
        ja="CCT ↔ CIE xy · Duv · 黒体・昼光軌跡 · 標準光源",
        zh="CCT ↔ CIE xy · Duv · 黑体与日光轨迹 · 标准光源",
        es="CCT ↔ CIE xy · Duv · loci planckiano y de luz de día · iluminantes estándar"),
    "modeT": dict(ko="온도에서", en="From temperature", ja="温度から", zh="由温度", es="Desde temperatura"),
    "modeXY": dict(ko="좌표에서", en="From coordinates", ja="座標から", zh="由坐标", es="Desde coordenadas"),
    "cct": dict(ko="색온도 CCT (K)", en="Temperature CCT (K)", ja="色温度 CCT (K)", zh="色温 CCT (K)", es="Temperatura CCT (K)"),
    "duvIn": dict(ko="Duv (궤적에서 거리)", en="Duv (offset from locus)", ja="Duv (軌跡からの距離)", zh="Duv (距轨迹偏移)", es="Duv (desplazamiento del locus)"),
    "locus": dict(ko="궤적", en="Locus", ja="軌跡", zh="轨迹", es="Locus"),
    "planck": dict(ko="플랑크 (흑체)", en="Planckian (blackbody)", ja="黒体 (プランク)", zh="普朗克 (黑体)", es="Planckiano (cuerpo negro)"),
    "daylight": dict(ko="주광 (D 계열)", en="Daylight (D series)", ja="昼光 (D系列)", zh="日光 (D系列)", es="Luz de día (serie D)"),
    "diagram": dict(ko="CIE 1931 색도도 · 궤적 · 광원", en="CIE 1931 diagram · loci · illuminants", ja="CIE 1931色度図 · 軌跡 · 光源", zh="CIE 1931色度图 · 轨迹 · 光源", es="Diagrama CIE 1931 · loci · iluminantes"),
    "result": dict(ko="결과", en="Result", ja="結果", zh="结果", es="Resultado"),
    "nearest": dict(ko="가장 가까운 표준 광원", en="Nearest standard illuminant", ja="最も近い標準光源", zh="最接近的标准光源", es="Iluminante estándar más cercano"),
    "illumTbl": dict(ko="표준 광원", en="Standard illuminants", ja="標準光源", zh="标准光源", es="Iluminantes estándar"),
    "tint": dict(ko="틴트", en="Tint", ja="ティント", zh="色调", es="Tinte"),
    "green": dict(ko="초록", en="green", ja="緑", zh="绿", es="verde"),
    "magenta": dict(ko="마젠타", en="magenta", ja="マゼンタ", zh="品红", es="magenta"),
    "onloc": dict(ko="궤적 위", en="on locus", ja="軌跡上", zh="轨迹上", es="sobre el locus"),
    "pipeline": dict(ko="계산 방법 · 수식", en="Method · formulas", ja="計算方法 · 数式", zh="计算方法 · 公式", es="Método · fórmulas"),
    "pipe_body": dict(
        ko="<b>온도 → 좌표</b>: 플랑크 궤적은 Kim 외(2002)의 구간별 3차식으로, x는 1/T 의 다항식(분기 4000K), y는 x 의 3차식(분기 2222K·4000K)으로 계산합니다. 주광(D) 궤적은 CIE 15 의 x<sub>D</sub>(분기 7000K)와 y<sub>D</sub> = −3x² + 2.87x − 0.275. Duv 는 CIE 1960 uv 평면에서 궤적의 법선 방향으로 그만큼 이동시켜 적용합니다(+는 초록, −는 마젠타).<br><br><b>좌표 → 온도</b>: CCT 는 McCamy(1992) 근사식 CCT = 437n³ + 3601n² + 6831n + 5517, n = (x−0.3320)/(0.1858−y). Duv 는 입력점을 CIE 1960 uv 로 옮긴 뒤 촘촘히 샘플링한 플랑크 궤적과의 최단(부호 있는) 거리로 구합니다.<br><br>※ CCT 근사식은 약 1667–25000K 에서 유효하며 양 끝에서 정확도가 떨어집니다. Duv 가 ±0.05 를 넘으면 'CCT' 자체의 의미가 약해집니다(궤적에서 너무 멈). 표준 광원 좌표는 CIE 15:2004 2° 관측자 기준입니다.",
        en="<b>Temperature → coordinates</b>: the Planckian locus uses the piecewise cubic of Kim et al. (2002) — x is a polynomial in 1/T (break at 4000K), y a cubic in x (breaks at 2222K, 4000K). The daylight (D) locus uses CIE 15's x<sub>D</sub> (break at 7000K) and y<sub>D</sub> = −3x² + 2.87x − 0.275. Duv is applied by stepping along the locus normal in the CIE 1960 uv plane (+ toward green, − toward magenta).<br><br><b>Coordinates → temperature</b>: CCT is McCamy's (1992) approximation CCT = 437n³ + 3601n² + 6831n + 5517, n = (x−0.3320)/(0.1858−y). Duv is the shortest (signed) distance from the input point, mapped to CIE 1960 uv, to a densely sampled Planckian locus.<br><br>※ The CCT approximations are valid roughly 1667–25000K and lose accuracy at the extremes. When |Duv| exceeds ~0.05 the very notion of a 'CCT' weakens (too far from the locus). Standard illuminant coordinates are CIE 15:2004, 2° observer.",
        ja="<b>温度 → 座標</b>: 黒体軌跡はKim他(2002)の区間別3次式 — xは1/Tの多項式(分岐4000K)、yはxの3次式(分岐2222K・4000K)。昼光(D)軌跡はCIE 15のx<sub>D</sub>(分岐7000K)とy<sub>D</sub> = −3x² + 2.87x − 0.275。DuvはCIE 1960 uv平面で軌跡の法線方向にその分移動して適用(+は緑、−はマゼンタ)。<br><br><b>座標 → 温度</b>: CCTはMcCamy(1992)近似式 CCT = 437n³ + 3601n² + 6831n + 5517, n = (x−0.3320)/(0.1858−y)。Duvは入力点をCIE 1960 uvに移し、密にサンプリングした黒体軌跡との最短(符号付き)距離。<br><br>※ CCT近似式は約1667–25000Kで有効、両端で精度が落ちます。|Duv|が約0.05を超えると『CCT』自体の意味が弱まります(軌跡から遠すぎる)。標準光源座標はCIE 15:2004 2°観測者基準。",
        zh="<b>温度 → 坐标</b>: 黑体轨迹采用Kim等(2002)的分段三次式 — x为1/T的多项式(分界4000K)，y为x的三次式(分界2222K·4000K)。日光(D)轨迹采用CIE 15的x<sub>D</sub>(分界7000K)与y<sub>D</sub> = −3x² + 2.87x − 0.275。Duv通过在CIE 1960 uv平面沿轨迹法线方向移动相应距离来施加(+偏绿，−偏品红)。<br><br><b>坐标 → 温度</b>: CCT采用McCamy(1992)近似式 CCT = 437n³ + 3601n² + 6831n + 5517, n = (x−0.3320)/(0.1858−y)。Duv为输入点映射到CIE 1960 uv后，与密集采样的黑体轨迹之间的最短(带符号)距离。<br><br>※ CCT近似式在约1667–25000K有效，两端精度下降。当|Duv|超过约0.05时，'CCT'本身的意义减弱(离轨迹太远)。标准光源坐标为CIE 15:2004 2°观察者。",
        es="<b>Temperatura → coordenadas</b>: el locus planckiano usa la cúbica por tramos de Kim et al. (2002) — x es un polinomio en 1/T (corte en 4000K), y una cúbica en x (cortes en 2222K, 4000K). El locus de luz de día (D) usa la x<sub>D</sub> de CIE 15 (corte en 7000K) y y<sub>D</sub> = −3x² + 2.87x − 0.275. La Duv se aplica desplazándose a lo largo de la normal del locus en el plano CIE 1960 uv (+ hacia verde, − hacia magenta).<br><br><b>Coordenadas → temperatura</b>: la CCT es la aproximación de McCamy (1992) CCT = 437n³ + 3601n² + 6831n + 5517, n = (x−0.3320)/(0.1858−y). La Duv es la distancia más corta (con signo) desde el punto de entrada, mapeado a CIE 1960 uv, hasta un locus planckiano muestreado densamente.<br><br>※ Las aproximaciones de CCT son válidas aproximadamente entre 1667–25000K y pierden precisión en los extremos. Cuando |Duv| supera ~0.05 la noción misma de 'CCT' se debilita (demasiado lejos del locus). Las coordenadas de iluminantes estándar son CIE 15:2004, observador 2°."),
    "foot": dict(
        ko="이 도구는 표준 색도식(Kim·McCamy·CIE 15)으로 색온도와 좌표를 변환합니다. CIE 색좌표의 원리는 색채과학 시리즈에서 다룹니다.",
        en="This tool converts between color temperature and coordinates using the standard chromaticity formulas (Kim, McCamy, CIE 15). The underlying CIE chromaticity theory is explained in the Color Science series.",
        ja="本ツールは標準色度式(Kim・McCamy・CIE 15)で色温度と座標を変換します。CIE色度の原理は色彩科学シリーズで解説しています。",
        zh="本工具用标准色度公式(Kim·McCamy·CIE 15)在色温与坐标之间转换。CIE色度的原理见色彩科学系列。",
        es="Esta herramienta convierte entre temperatura de color y coordenadas usando las fórmulas estándar de cromaticidad (Kim, McCamy, CIE 15). La teoría de cromaticidad CIE se explica en la serie de Ciencia del Color."),
    "readArt": dict(ko="색채과학 시리즈 읽기 →", en="Read the Color Science series →", ja="色彩科学シリーズを読む →", zh="阅读色彩科学系列 →", es="Leer la serie de Ciencia del Color →"),
    "home": dict(ko="홈", en="Home", ja="ホーム", zh="首页", es="Inicio"),
}

JS_CORE = r"""
// ---- standard illuminant white points (CIE 15:2004, 2-deg observer) ----
var ILLUM={A:[0.44757,0.40745],C:[0.31006,0.31616],D50:[0.34567,0.35850],D55:[0.33242,0.34743],
 D65:[0.31271,0.32902],D75:[0.29902,0.31485],E:[1/3,1/3],F2:[0.37208,0.37529],F7:[0.31292,0.32933],F11:[0.38052,0.37713]};
var ILLUM_ORDER=['A','C','D50','D55','D65','D75','E','F2','F7','F11'];

// ---- Planckian locus: Kim et al. (2002) ----
function planckXY(T){
 if(T<1667)T=1667; if(T>25000)T=25000;
 var xc;
 if(T<=4000)xc=-0.2661239e9/(T*T*T)-0.2343589e6/(T*T)+0.8776956e3/T+0.179910;
 else xc=-3.0258469e9/(T*T*T)+2.1070379e6/(T*T)+0.2226347e3/T+0.240390;
 var yc;
 if(T<=2222)yc=-1.1063814*xc*xc*xc-1.34811020*xc*xc+2.18555832*xc-0.20219683;
 else if(T<=4000)yc=-0.9549476*xc*xc*xc-1.37418593*xc*xc+2.09137015*xc-0.16748867;
 else yc=3.0817580*xc*xc*xc-5.87338670*xc*xc+3.75112997*xc-0.37001483;
 return [xc,yc];
}
// ---- CIE daylight locus (CIE 15) ----
function daylightXY(T){
 if(T<4000)T=4000; if(T>25000)T=25000;
 var xD;
 if(T<=7000)xD=-4.6070e9/(T*T*T)+2.9678e6/(T*T)+0.09911e3/T+0.244063;
 else xD=-2.0064e9/(T*T*T)+1.9018e6/(T*T)+0.24748e3/T+0.237040;
 var yD=-3.000*xD*xD+2.870*xD-0.275;
 return [xD,yD];
}
function locusXY(T){return document.getElementById('locusSel').value==='daylight'?daylightXY(T):planckXY(T);}
// ---- McCamy CCT from xy ----
function mccamy(x,y){var n=(x-0.3320)/(0.1858-y);return 437*n*n*n+3601*n*n+6831*n+5517;}
// ---- CIE 1960 uv (for Duv) and CIE 1976 u'v' (for display) ----
function xy2uv60(x,y){var d=-2*x+12*y+3;return [4*x/d,6*y/d];}
function uv60toXY(u,v){var d=2*u-8*v+4;return [3*u/d,2*v/d];}
function xy2uv76(x,y){var d=-2*x+12*y+3;return [4*x/d,9*y/d];}
// signed Duv from xy to Planckian locus (dense nearest sample + sign by v)
function calcDuv(x,y){
 var uv=xy2uv60(x,y),best=1e9,bt=0,bv=0;
 for(var T=1667;T<=25000;T+=25){var p=planckXY(T),luv=xy2uv60(p[0],p[1]);var d=Math.hypot(uv[0]-luv[0],uv[1]-luv[1]);if(d<best){best=d;bt=T;bv=luv[1];}}
 var sign=(uv[1]-bv)>=0?1:-1;
 return {cct:bt,duv:sign*best};
}
// apply Duv: step along locus normal in uv60, return xy
function applyDuv(T,duv){
 var p=locusXY(T),uv=xy2uv60(p[0],p[1]);
 var p1=locusXY(T-Math.min(50,T-1667)),p2=locusXY(T+50);
 var a=xy2uv60(p1[0],p1[1]),b=xy2uv60(p2[0],p2[1]);
 var tx=b[0]-a[0],ty=b[1]-a[1],L=Math.hypot(tx,ty)||1e-9;tx/=L;ty/=L;
 var nx=-ty,ny=tx; if(ny<0){nx=-nx;ny=-ny;} // normal points to +v (green)
 return uv60toXY(uv[0]+nx*duv,uv[1]+ny*duv);
}
function xy2css(x,y){
 var Y=1,X=x*Y/y,Z=(1-x-y)*Y/y;
 var r=3.2406*X-1.5372*Y-0.4986*Z,g=-0.9689*X+1.8758*Y+0.0415*Z,b=0.0557*X-0.2040*Y+1.0570*Z;
 r=Math.max(0,r);g=Math.max(0,g);b=Math.max(0,b);
 var mx=Math.max(r,g,b,1e-6);r/=mx;g/=mx;b/=mx;
 function gm(v){return v<=0.0031308?12.92*v:1.055*Math.pow(v,1/2.4)-0.055;}
 return 'rgb('+Math.round(gm(r)*255)+','+Math.round(gm(g)*255)+','+Math.round(gm(b)*255)+')';
}
function nearestIllum(x,y){
 var best=1e9,bn='';
 for(var i=0;i<ILLUM_ORDER.length;i++){var k=ILLUM_ORDER[i],p=ILLUM[k];var d=Math.hypot(x-p[0],y-p[1]);if(d<best){best=d;bn=k;}}
 return {name:bn,dist:best};
}

// ---- diagram mapping (CIE 1931 gamut PNG: x[0,0.8] y[0,0.9]) ----
var DOX=46,DOY=470,DPW=410,DPH=410,DXR=0.8,DYR=0.9;
function PX(x){return DOX+DPW*(x/DXR);}
function PY(y){return DOY-DPH*(y/DYR);}
function num(id){var v=parseFloat(document.getElementById(id).value);return isFinite(v)?v:0;}
function fmt(v,n){return isFinite(v)?v.toFixed(n===undefined?4:n):'–';}

function drawLocusCurves(){
 var pl=[],dl=[];
 for(var T=1500;T<=20000;T+=(T<6000?100:500)){var p=planckXY(T);pl.push(PX(p[0]).toFixed(1)+','+PY(p[1]).toFixed(1));}
 for(var T2=4000;T2<=25000;T2+=500){var d=daylightXY(T2);dl.push(PX(d[0]).toFixed(1)+','+PY(d[1]).toFixed(1));}
 document.getElementById('locusPath').setAttribute('points',pl.join(' '));
 document.getElementById('dayPath').setAttribute('points',dl.join(' '));
 // illuminant dots
 var g=document.getElementById('illumG');g.innerHTML='';
 ILLUM_ORDER.forEach(function(k){var p=ILLUM[k];var x=PX(p[0]),y=PY(p[1]);
  var c=document.createElementNS('http://www.w3.org/2000/svg','circle');c.setAttribute('cx',x.toFixed(1));c.setAttribute('cy',y.toFixed(1));c.setAttribute('r','3');c.setAttribute('fill','#fff');c.setAttribute('stroke','#000');c.setAttribute('stroke-width','0.8');g.appendChild(c);
  var t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x',(x+5).toFixed(1));t.setAttribute('y',(y+3).toFixed(1));t.setAttribute('font-size','9');t.setAttribute('fill','#cfe');t.setAttribute('stroke','#000');t.setAttribute('stroke-width','2.2');t.setAttribute('paint-order','stroke');t.textContent=k;g.appendChild(t);});
}

function setMode(m){
 document.getElementById('paneT').style.display=m==='T'?'block':'none';
 document.getElementById('paneXY').style.display=m==='XY'?'block':'none';
 document.getElementById('btnT').className='seg'+(m==='T'?' on':'');
 document.getElementById('btnXY').className='seg'+(m==='XY'?' on':'');
 window._mode=m;render();
}
function render(){
 var x,y,cct,duv;
 if(window._mode==='XY'){
  x=num('inX');y=num('inY');
  cct=mccamy(x,y); var dd=calcDuv(x,y); duv=dd.duv;
 }else{
  cct=num('inCCT');duv=num('inDuv');
  var p=applyDuv(cct,duv); x=p[0];y=p[1];
 }
 var uv76=xy2uv76(x,y);
 document.getElementById('oX').textContent=fmt(x);
 document.getElementById('oY').textContent=fmt(y);
 document.getElementById('oU').textContent=fmt(uv76[0]);
 document.getElementById('oV').textContent=fmt(uv76[1]);
 document.getElementById('oCCT').textContent=isFinite(cct)?Math.round(cct).toLocaleString()+' K':'–';
 document.getElementById('oDuv').textContent=(duv>=0?'+':'')+fmt(duv);
 var tnt=Math.abs(duv)<0.0005?L.onloc:(duv>0?L.green:L.magenta);
 document.getElementById('oTint').textContent=tnt;
 document.getElementById('sw').style.background=xy2css(x,y);
 var ni=nearestIllum(x,y);
 document.getElementById('oNear').textContent=ni.name+' (Δ'+ni.dist.toFixed(4)+')';
 // current point on diagram
 document.getElementById('curPt').setAttribute('transform','translate('+PX(x).toFixed(1)+','+PY(y).toFixed(1)+')');
 // highlight nearest row
 var rows=document.querySelectorAll('#illumBody tr');rows.forEach(function(tr){tr.classList.toggle('hl',tr.getAttribute('data-k')===ni.name);});
}
function buildIllumTable(){
 var b=document.getElementById('illumBody');var html='';
 ILLUM_ORDER.forEach(function(k){var p=ILLUM[k];var cct=mccamy(p[0],p[1]);
  html+='<tr data-k="'+k+'"><td><span class="pri" style="background:'+xy2css(p[0],p[1])+'"></span>'+k+'</td><td>'+p[0].toFixed(4)+'</td><td>'+p[1].toFixed(4)+'</td><td>'+(k==='E'?'~5455':Math.round(cct).toLocaleString())+'</td></tr>';});
 b.innerHTML=html;
}
function init(){
 buildIllumTable();drawLocusCurves();
 document.getElementById('btnT').addEventListener('click',function(){setMode('T');});
 document.getElementById('btnXY').addEventListener('click',function(){setMode('XY');});
 ['inCCT','inDuv','inX','inY'].forEach(function(id){document.getElementById(id).addEventListener('input',render);});
 document.getElementById('locusSel').addEventListener('change',render);
 // quick illuminant buttons
 document.querySelectorAll('#quickIll button').forEach(function(btn){btn.addEventListener('click',function(){var k=btn.getAttribute('data-k');var p=ILLUM[k];document.getElementById('inX').value=p[0];document.getElementById('inY').value=p[1];setMode('XY');});});
 setMode('T');
}
if(document.readyState!=='loading')init();else document.addEventListener('DOMContentLoaded',init);
"""


def fig_svg():
    return f'''<svg viewBox="0 0 500 510" xmlns="http://www.w3.org/2000/svg">
  <image href="/assets/blog/cs-cie1931-gamut.png?v={BUILD}" x="46" y="60" width="410" height="410" preserveAspectRatio="none" opacity="0.5"/>
  <line x1="46" y1="470" x2="470" y2="470" stroke="#3a4a66" stroke-width="1.2"/>
  <line x1="46" y1="470" x2="46" y2="55" stroke="#3a4a66" stroke-width="1.2"/>
  <text x="40" y="474" text-anchor="end" font-size="10" fill="#647698">0</text>
  <text x="{46+410*0.4/0.8:.0f}" y="486" text-anchor="middle" font-size="10" fill="#647698">0.4</text>
  <text x="466" y="486" text-anchor="end" font-size="11" fill="#93a3bf">x</text>
  <text x="32" y="{470-410*0.4/0.9:.0f}" text-anchor="end" font-size="10" fill="#647698">0.4</text>
  <text x="34" y="64" font-size="11" fill="#93a3bf">y</text>
  <polyline id="dayPath" points="" fill="none" stroke="#7fd4ff" stroke-width="1.6" stroke-dasharray="4 3" opacity="0.85"/>
  <polyline id="locusPath" points="" fill="none" stroke="#ffd27f" stroke-width="2.2" opacity="0.95"/>
  <g id="illumG"></g>
  <g id="curPt"><circle r="9" fill="none" stroke="#fff" stroke-width="2.5"/><circle r="3.5" fill="#ff5d6c"/></g>
</svg>'''


EXTRA_CSS = """
.seg-wrap{display:flex;gap:0;margin:4px 0 14px;border:1px solid var(--line);border-radius:10px;overflow:hidden}
.seg{flex:1;background:var(--card);color:var(--dim);border:none;padding:11px 8px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit}
.seg.on{background:rgba(93,193,255,.16);color:var(--accent)}
.swbig{height:70px;border-radius:12px;border:1px solid var(--line);box-shadow:inset 0 0 0 1px #0006;margin:6px 0 4px}
.res-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:6px}
.res-grid .de-card .v{font-size:18px}
.res-grid .de-card.hero{grid-column:1/-1}
.res-grid .de-card.hero .v{font-size:30px}
.gamut-legend{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin-top:10px;font-size:11.5px;font-family:'JetBrains Mono',monospace}
.gamut-legend .lg{display:flex;align-items:center;gap:6px;color:var(--dim)}
.gamut-legend .ln{display:inline-block;width:22px;height:0;border-top-width:3px}
#quickIll{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
#quickIll button{background:var(--card2);border:1px solid var(--line);border-radius:7px;color:var(--dim);padding:6px 11px;font-size:12.5px;font-weight:700;cursor:pointer;font-family:'JetBrains Mono',monospace}
#quickIll button:hover{border-color:var(--accent);color:var(--accent)}
.prim-tbl td .pri{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:7px;vertical-align:middle;border:1px solid #0006}
#illumBody tr.hl{background:rgba(93,193,255,.14)}
#illumBody tr.hl td:first-child{color:var(--accent)}
.range-row{display:flex;align-items:center;gap:10px}
.range-row input[type=range]{flex:1;accent-color:var(--accent)}
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
<link rel="alternate" hreflang="ko" href="https://luckyplz.com/tools/color-temperature/">
<link rel="alternate" hreflang="en" href="https://luckyplz.com/tools/color-temperature-en/">
<link rel="alternate" hreflang="ja" href="https://luckyplz.com/tools/color-temperature-ja/">
<link rel="alternate" hreflang="zh" href="https://luckyplz.com/tools/color-temperature-zh/">
<link rel="alternate" hreflang="es" href="https://luckyplz.com/tools/color-temperature-es/">
<link rel="alternate" hreflang="x-default" href="https://luckyplz.com/tools/color-temperature-en/">
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

  <div class="seg-wrap">
    <button class="seg on" id="btnT">{{MODET}}</button>
    <button class="seg" id="btnXY">{{MODEXY}}</button>
  </div>

  <div id="paneT">
    <div class="controls">
      <div class="f"><label>{{CCT}}</label><input type="number" id="inCCT" min="1667" max="25000" step="10" value="6504"></div>
      <div class="f"><label>{{DUVIN}}</label><input type="number" id="inDuv" step="0.001" value="0.000"></div>
      <div class="f"><label>{{LOCUS}}</label><select id="locusSel"><option value="planck" selected>{{PLANCK}}</option><option value="daylight">{{DAYLIGHT}}</option></select></div>
    </div>
  </div>

  <div id="paneXY" style="display:none">
    <div class="controls">
      <div class="f"><label>x</label><input type="number" id="inX" step="0.0001" value="0.3127"></div>
      <div class="f"><label>y</label><input type="number" id="inY" step="0.0001" value="0.3290"></div>
    </div>
    <div id="quickIll">{{QUICKILL}}</div>
  </div>

  <div class="swbig" id="sw"></div>

  <div class="res-grid">
    <div class="de-card hero"><div class="k">CCT</div><div class="v" id="oCCT">–</div></div>
    <div class="de-card"><div class="k">Duv</div><div class="v" id="oDuv">–</div><div class="k2" id="oTint"></div></div>
    <div class="de-card"><div class="k">x, y</div><div class="v" style="font-size:14px"><span id="oX">–</span>, <span id="oY">–</span></div></div>
    <div class="de-card"><div class="k">u′, v′ (1976)</div><div class="v" style="font-size:14px"><span id="oU">–</span>, <span id="oV">–</span></div></div>
    <div class="de-card" style="grid-column:1/-1"><div class="k">{{NEAREST}}</div><div class="v" id="oNear" style="font-size:18px">–</div></div>
  </div>

  <div class="sec-h">{{DIAGRAM}}</div>
  <div class="figwrap" style="flex-direction:column">{{FIG}}
    <div class="gamut-legend">
      <span class="lg"><span class="ln" style="border-top:3px solid #ffd27f"></span>{{PLANCK}}</span>
      <span class="lg"><span class="ln" style="border-top:3px dashed #7fd4ff"></span>{{DAYLIGHT}}</span>
    </div>
  </div>

  <div class="sec-h">{{ILLUMTBL}}</div>
  <table class="prim-tbl">
    <thead><tr><th></th><th>x</th><th>y</th><th>CCT</th></tr></thead>
    <tbody id="illumBody"></tbody>
  </table>

  <details><summary>{{PIPELINE}}</summary><div class="body">{{PIPEBODY}}</div></details>

  <footer>{{FOOT}}<br><a href="{{ARTURL}}">{{READART}}</a> · <a href="/tools/">/tools</a> · <a href="/">{{HOME}}</a></footer>
</div>
<script>var L={{JSL}};</script>
<script>{{JSCORE}}</script>
<script>navigator.serviceWorker&&navigator.serviceWorker.getRegistrations().then(function(rs){rs.forEach(function(r){r.unregister()})});</script>
<script src="/js/langSelect.js?v={{BUILD}}" defer></script>
<script src="/js/siteFooter.js?v={{BUILD}}" defer></script>
</body>
</html>
"""


def quick_illum():
    keys = ['D50', 'D65', 'D75', 'A', 'F2', 'F11', 'E']
    return "".join(f'<button data-k="{k}">{k}</button>' for k in keys)


def build(lang):
    m = META[lang]
    canon = f"https://luckyplz.com/tools/{SLUG}{LANG_SUFFIX[lang]}/"
    art = {"ko": "/blog/color-science-02-color-in-numbers/", "en": "/blog/color-science-02-color-in-numbers-en/",
           "ja": "/blog/color-science-02-color-in-numbers-ja/", "zh": "/blog/color-science-02-color-in-numbers-zh/",
           "es": "/blog/color-science-02-color-in-numbers-en/"}[lang]
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
    jsl = json.dumps({"onloc": S["onloc"][lang], "green": S["green"][lang], "magenta": S["magenta"][lang]}, ensure_ascii=False)
    repl = {
        "{{HTMLLANG}}": HTML_LANG[lang], "{{BUILD}}": BUILD, "{{TITLE}}": m["title"],
        "{{DESC}}": m["desc"], "{{KEYWORDS}}": m["keywords"], "{{CANON}}": canon,
        "{{OGT}}": m["ogt"], "{{OGD}}": m["ogd"], "{{OGLOCALE}}": OG_LOCALE[lang],
        "{{JSONLD}}": jsonld, "{{CRUMB}}": crumb, "{{CSS}}": CSS,
        "{{FIG}}": fig_svg(), "{{JSCORE}}": JS_CORE, "{{JSL}}": jsl, "{{QUICKILL}}": quick_illum(),
        "{{ARTURL}}": art,
        "{{H1}}": S["h1"][lang], "{{SUB}}": S["sub"][lang],
        "{{MODET}}": S["modeT"][lang], "{{MODEXY}}": S["modeXY"][lang],
        "{{CCT}}": S["cct"][lang], "{{DUVIN}}": S["duvIn"][lang], "{{LOCUS}}": S["locus"][lang],
        "{{PLANCK}}": S["planck"][lang], "{{DAYLIGHT}}": S["daylight"][lang],
        "{{NEAREST}}": S["nearest"][lang], "{{DIAGRAM}}": S["diagram"][lang], "{{ILLUMTBL}}": S["illumTbl"][lang],
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
    print("[done] color-temperature tool")


if __name__ == "__main__":
    main()
