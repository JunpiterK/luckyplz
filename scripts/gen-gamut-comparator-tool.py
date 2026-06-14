# -*- coding: utf-8 -*-
"""Generate the Gamut Comparator tool (ko/en/ja/zh/es).

Second tool in the color-science suite, and the first piece of Spanish content.
A display/color professional picks a REFERENCE gamut (target standard) and a
COMPARISON gamut (another standard, or custom measured primaries), and the tool:
  - overlays both gamut triangles on the CIE 1931 chromaticity diagram,
  - fills the intersection (the actually-covered region),
  - computes COVERAGE % = area(intersection) / area(reference) and
    AREA RATIO % = area(comparison) / area(reference).

The moat is exact polygon geometry: shoelace area + Sutherland-Hodgman convex
clipping for the true intersection (not the naive area-ratio that most "gamut
%" claims conflate). Reuses the color-difference tool's CSS for visual parity
and the shared CIE 1931 gamut PNG + langSelect.js.

Output: public/tools/gamut-comparator[/-en/-ja/-zh/-es]/index.html  (+ sitemap)
"""
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
TOOLS = PUBLIC / "tools"
SLUG = "gamut-comparator"
DATE = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")

try:
    BUILD = json.loads((PUBLIC / "build.json").read_text(encoding="utf-8")).get("v", DATE)
except Exception:
    BUILD = DATE

# reuse the color-difference tool's dark-theme CSS for visual parity
_spec = importlib.util.spec_from_file_location("cdtool", ROOT / "scripts" / "gen-color-difference-tool.py")
_cd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cd)
BASE_CSS = _cd.CSS

LANGS = ("ko", "en", "ja", "zh", "es")
LANG_SUFFIX = {"ko": "", "en": "-en", "ja": "-ja", "zh": "-zh", "es": "-es"}
HTML_LANG = {"ko": "ko", "en": "en", "ja": "ja", "zh": "zh", "es": "es"}
OG_LOCALE = {"ko": "ko_KR", "en": "en_US", "ja": "ja_JP", "zh": "zh_CN", "es": "es_ES"}

# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------
META = {
    "ko": dict(
        title="색역 비교기 — CIE 1931 색역 커버리지·면적비 계산 (sRGB·DCI-P3·BT.2020) | Lucky Please",
        desc="기준 색역(sRGB·DCI-P3·Adobe RGB·BT.2020·NTSC)과 비교 색역(표준 또는 측정한 R·G·B 1차색 좌표)을 골라 CIE 1931 색도도에 두 삼각형을 겹쳐 그리고, 다각형 교집합으로 정확한 커버리지%와 면적비%를 산출합니다. 디스플레이 패널 색역 평가용 전문 도구.",
        keywords="색역 비교, 색역 커버리지, gamut coverage, DCI-P3 커버리지, BT.2020, sRGB, 색역 면적비, CIE 1931 색역, 디스플레이 색역, 패널 색역 측정",
        ogt="색역 비교기 — 커버리지·면적비 정확 계산",
        ogd="두 색역을 CIE 1931 색도도에 겹쳐 그리고 다각형 교집합으로 커버리지%·면적비%를 산출.",
    ),
    "en": dict(
        title="Gamut Comparator — CIE 1931 Gamut Coverage & Area Ratio (sRGB, DCI-P3, BT.2020) | Lucky Please",
        desc="Pick a reference gamut (sRGB, DCI-P3, Adobe RGB, BT.2020, NTSC) and a comparison gamut (a standard, or your measured R/G/B primary x,y), overlay both triangles on the CIE 1931 diagram, and get an exact coverage % (via polygon intersection) and area ratio %. A professional tool for evaluating display panel gamut.",
        keywords="gamut comparator, gamut coverage, DCI-P3 coverage, BT.2020, sRGB, gamut area ratio, CIE 1931 gamut, display gamut, panel gamut measurement",
        ogt="Gamut Comparator — exact coverage & area ratio",
        ogd="Overlay two gamuts on the CIE 1931 diagram; get coverage % (polygon intersection) and area ratio %.",
    ),
    "ja": dict(
        title="色域比較ツール — CIE 1931 色域カバー率・面積比 (sRGB・DCI-P3・BT.2020) | Lucky Please",
        desc="基準色域(sRGB・DCI-P3・Adobe RGB・BT.2020・NTSC)と比較色域(標準、または測定したR・G・B原刺激のx,y)を選び、CIE 1931色度図に2つの三角形を重ねて、多角形交差により正確なカバー率%と面積比%を算出。ディスプレイパネルの色域評価向け専門ツール。",
        keywords="色域比較, 色域カバー率, gamut coverage, DCI-P3カバー率, BT.2020, sRGB, 色域面積比, CIE 1931色域, ディスプレイ色域, パネル色域測定",
        ogt="色域比較ツール — カバー率・面積比を正確に",
        ogd="2色域をCIE 1931色度図に重ね、多角形交差でカバー率%・面積比%を算出。",
    ),
    "zh": dict(
        title="色域比较器 — CIE 1931 色域覆盖率与面积比 (sRGB·DCI-P3·BT.2020) | Lucky Please",
        desc="选择基准色域(sRGB·DCI-P3·Adobe RGB·BT.2020·NTSC)与比较色域(标准，或测得的R/G/B三原色x,y)，在CIE 1931色度图上叠加两个三角形，通过多边形相交计算精确的覆盖率%与面积比%。面向显示面板色域评估的专业工具。",
        keywords="色域比较, 色域覆盖率, gamut coverage, DCI-P3覆盖率, BT.2020, sRGB, 色域面积比, CIE 1931色域, 显示色域, 面板色域测量",
        ogt="色域比较器 — 精确覆盖率与面积比",
        ogd="在CIE 1931色度图上叠加两色域，用多边形相交求覆盖率%与面积比%。",
    ),
    "es": dict(
        title="Comparador de Gamas — Cobertura y Razón de Área CIE 1931 (sRGB, DCI-P3, BT.2020) | Lucky Please",
        desc="Elige una gama de referencia (sRGB, DCI-P3, Adobe RGB, BT.2020, NTSC) y una gama de comparación (un estándar, o las coordenadas x,y medidas de tus primarios R/G/B), superpón ambos triángulos en el diagrama CIE 1931 y obtén el % de cobertura exacto (por intersección de polígonos) y el % de razón de área. Herramienta profesional para evaluar la gama de paneles de pantalla.",
        keywords="comparador de gamas, cobertura de gama, gamut coverage, cobertura DCI-P3, BT.2020, sRGB, razón de área de gama, gama CIE 1931, gama de pantalla, medición de gama de panel",
        ogt="Comparador de Gamas — cobertura y razón de área exactas",
        ogd="Superpón dos gamas en el diagrama CIE 1931; obtén % de cobertura (intersección de polígonos) y % de razón de área.",
    ),
}

# ---------------------------------------------------------------------------
# UI strings
# ---------------------------------------------------------------------------
S = {
    "h1": dict(ko="색역 비교기", en="Gamut Comparator", ja="色域比較ツール", zh="色域比较器", es="Comparador de Gamas"),
    "sub": dict(
        ko="CIE 1931 색도도 · 커버리지 = 교집합 ÷ 기준 색역 · 면적비 = 비교 ÷ 기준",
        en="CIE 1931 diagram · coverage = intersection ÷ reference · area ratio = comparison ÷ reference",
        ja="CIE 1931色度図 · カバー率 = 交差 ÷ 基準色域 · 面積比 = 比較 ÷ 基準",
        zh="CIE 1931色度图 · 覆盖率 = 交集 ÷ 基准色域 · 面积比 = 比较 ÷ 基准",
        es="Diagrama CIE 1931 · cobertura = intersección ÷ referencia · razón de área = comparación ÷ referencia"),
    "planeLbl": dict(ko="색도 평면", en="Chromaticity plane", ja="色度平面", zh="色度平面", es="Plano de cromaticidad"),
    "refSel": dict(ko="기준 색역 (목표 표준)", en="Reference gamut (target standard)", ja="基準色域 (目標標準)", zh="基准色域 (目标标准)", es="Gama de referencia (estándar objetivo)"),
    "compSel": dict(ko="비교 색역 (내 패널·소스)", en="Comparison gamut (your panel / source)", ja="比較色域 (パネル・ソース)", zh="比较色域 (你的面板/源)", es="Gama de comparación (tu panel / fuente)"),
    "custom": dict(ko="사용자 측정값 (직접 입력)", en="Custom (measured)", ja="カスタム (測定値)", zh="自定义 (测量值)", es="Personalizada (medida)"),
    "customH": dict(ko="측정한 1차색 좌표 (x, y)", en="Measured primary coordinates (x, y)", ja="測定した原刺激座標 (x, y)", zh="测得的三原色坐标 (x, y)", es="Coordenadas de primarios medidas (x, y)"),
    "diagram": dict(ko="CIE 1931 색도도 위의 두 색역", en="The two gamuts on the CIE 1931 diagram", ja="CIE 1931色度図上の2色域", zh="CIE 1931色图上的两色域", es="Las dos gamas en el diagrama CIE 1931"),
    "coverage": dict(ko="커버리지", en="Coverage", ja="カバー率", zh="覆盖率", es="Cobertura"),
    "covSub": dict(ko="비교가 기준을 덮는 비율", en="how much of the reference is covered", ja="基準を覆う割合", zh="覆盖基准的比例", es="cuánto de la referencia se cubre"),
    "arat": dict(ko="면적비", en="Area ratio", ja="面積比", zh="面积比", es="Razón de área"),
    "aratSub": dict(ko="비교 면적 ÷ 기준 면적", en="comparison area ÷ reference area", ja="比較面積 ÷ 基準面積", zh="比较面积 ÷ 基准面积", es="área de comparación ÷ área de referencia"),
    "prim": dict(ko="1차색 좌표 (x, y)", en="Primary coordinates (x, y)", ja="原刺激座標 (x, y)", zh="三原色坐标 (x, y)", es="Coordenadas de primarios (x, y)"),
    "ref": dict(ko="기준", en="Reference", ja="基準", zh="基准", es="Referencia"),
    "comp": dict(ko="비교", en="Comparison", ja="比較", zh="比较", es="Comparación"),
    "pipeline": dict(ko="계산 방법 · 커버리지 ≠ 면적비", en="Method · coverage ≠ area ratio", ja="計算方法 · カバー率 ≠ 面積比", zh="计算方法 · 覆盖率 ≠ 面积比", es="Método · cobertura ≠ razón de área"),
    "pipe_body": dict(
        ko="<b>면적</b>은 세 1차색 (R, G, B) 의 x, y 를 꼭짓점으로 하는 삼각형의 넓이로, 신발끈 공식 ½·|Σ(xᵢyⱼ−xⱼyᵢ)| 로 구합니다.<br><br><b>면적비</b> = 비교 삼각형 면적 ÷ 기준 삼각형 면적 × 100. 흔히 'DCI-P3 대비 OO%' 로 광고되지만, 이건 <b>겹치는 위치를 보지 않습니다</b>. 비교 색역이 기준 밖으로 튀어나가도 면적만 크면 100% 가 넘게 나옵니다.<br><br><b>커버리지</b> = (비교 ∩ 기준) 면적 ÷ 기준 면적 × 100. 두 삼각형의 <b>실제 교집합</b>을 Sutherland–Hodgman 볼록 클리핑으로 구한 뒤 그 넓이를 기준으로 나눕니다. 기준 영역 중 비교 색역이 실제로 재현할 수 있는 비율이라, 패널 평가에는 이쪽이 정직합니다. 도표에서 칠해진 영역이 그 교집합입니다.<br><br>※ xy 평면 면적은 지각적으로 균일하지 않습니다 (녹색 영역이 과장됨). 상단 <b>색도 평면</b> 토글을 <b>CIE 1976 u′v′</b> 로 바꾸면 지각적으로 더 균일한 평면에서 같은 커버리지·면적비를 다시 계산합니다.",
        en="<b>Area</b> is the area of the triangle whose vertices are the x, y of the three primaries (R, G, B), via the shoelace formula ½·|Σ(xᵢyⱼ−xⱼyᵢ)|.<br><br><b>Area ratio</b> = comparison triangle area ÷ reference triangle area × 100. Often advertised as 'OO% of DCI-P3', but it <b>ignores where the triangles overlap</b>. If the comparison spills outside the reference, a larger area alone can read over 100%.<br><br><b>Coverage</b> = area(comparison ∩ reference) ÷ reference area × 100. The <b>actual intersection</b> of the two triangles is found by Sutherland–Hodgman convex clipping, then divided by the reference area. It is the fraction of the target the comparison can really reproduce, so it is the honest number for panel evaluation. The filled region in the diagram is that intersection.<br><br>※ Area on the xy plane is not perceptually uniform (it exaggerates the green region). Switch the <b>Chromaticity plane</b> toggle above to <b>CIE 1976 u′v′</b> and the same coverage and area ratio are recomputed on a more perceptually uniform plane.",
        ja="<b>面積</b>は3原刺激 (R, G, B) のx, yを頂点とする三角形の面積で、靴ひも公式 ½·|Σ(xᵢyⱼ−xⱼyᵢ)| で求めます。<br><br><b>面積比</b> = 比較三角形の面積 ÷ 基準三角形の面積 × 100。よく『DCI-P3比OO%』と宣伝されますが、これは<b>重なる位置を見ていません</b>。比較色域が基準の外にはみ出しても、面積さえ大きければ100%を超えて出ます。<br><br><b>カバー率</b> = (比較 ∩ 基準) 面積 ÷ 基準面積 × 100。2つの三角形の<b>実際の交差</b>をSutherland–Hodgman凸クリッピングで求め、基準面積で割ります。基準のうち比較色域が実際に再現できる割合なので、パネル評価にはこちらが誠実です。図の塗りつぶし領域がその交差です。<br><br>※ xy平面の面積は知覚的に均一ではありません(緑領域が誇張される)。上部の<b>色度平面</b>トグルを<b>CIE 1976 u′v′</b>に切り替えると、より知覚的に均一な平面で同じカバー率・面積比を再計算します。",
        zh="<b>面积</b>是以三原色 (R, G, B) 的x, y为顶点的三角形面积，用鞋带公式 ½·|Σ(xᵢyⱼ−xⱼyᵢ)| 求得。<br><br><b>面积比</b> = 比较三角形面积 ÷ 基准三角形面积 × 100。常被宣传为『DCI-P3的OO%』，但它<b>不看三角形重叠的位置</b>。若比较色域超出基准之外，仅凭面积大就可能读出超过100%。<br><br><b>覆盖率</b> = (比较 ∩ 基准) 面积 ÷ 基准面积 × 100。用Sutherland–Hodgman凸裁剪求两三角形的<b>真实交集</b>，再除以基准面积。它是基准中比较色域真正能重现的比例，故对面板评估更诚实。图中填充区域即该交集。<br><br>※ xy平面上的面积并非知觉均匀(会夸大绿色区域)。将上方<b>色度平面</b>切换为<b>CIE 1976 u′v′</b>，即可在更知觉均匀的平面上重新计算相同的覆盖率与面积比。",
        es="El <b>área</b> es la del triángulo cuyos vértices son las x, y de los tres primarios (R, G, B), mediante la fórmula del cordón de zapato ½·|Σ(xᵢyⱼ−xⱼyᵢ)|.<br><br><b>Razón de área</b> = área del triángulo de comparación ÷ área del triángulo de referencia × 100. A menudo se anuncia como 'OO% de DCI-P3', pero <b>ignora dónde se solapan</b> los triángulos. Si la comparación se sale de la referencia, un área mayor por sí sola puede dar más de 100%.<br><br><b>Cobertura</b> = área(comparación ∩ referencia) ÷ área de referencia × 100. La <b>intersección real</b> de los dos triángulos se obtiene por recorte convexo de Sutherland–Hodgman y se divide por el área de referencia. Es la fracción del objetivo que la comparación puede reproducir de verdad, así que es el número honesto para evaluar paneles. La región rellena del diagrama es esa intersección.<br><br>※ El área en el plano xy no es perceptualmente uniforme (exagera la región verde). Cambia el selector <b>Plano de cromaticidad</b> de arriba a <b>CIE 1976 u′v′</b> y se recalculan la misma cobertura y razón de área en un plano perceptualmente más uniforme."),
    "foot": dict(
        ko="이 도구는 1차색 좌표로부터 색역 커버리지를 기하학적으로 산출합니다. CIE 색좌표·색역의 원리는 색채과학 시리즈에서 다룹니다.",
        en="This tool computes gamut coverage geometrically from primary coordinates. The underlying CIE chromaticity and gamut theory is explained in the Color Science series.",
        ja="本ツールは原刺激座標から色域カバー率を幾何学的に算出します。CIE色度・色域の原理は色彩科学シリーズで解説しています。",
        zh="本工具从三原色坐标几何地计算色域覆盖率。CIE色度与色域的原理见色彩科学系列。",
        es="Esta herramienta calcula la cobertura de gama geométricamente a partir de las coordenadas de los primarios. La teoría de cromaticidad y gama CIE se explica en la serie de Ciencia del Color."),
    "readArt": dict(ko="색채과학 시리즈 읽기 →", en="Read the Color Science series →", ja="色彩科学シリーズを読む →", zh="阅读色彩科学系列 →", es="Leer la serie de Ciencia del Color →"),
    "home": dict(ko="홈", en="Home", ja="ホーム", zh="首页", es="Inicio"),
}

# ---------------------------------------------------------------------------
# JS core (gamut data + geometry + render)
# ---------------------------------------------------------------------------
JS_CORE = r"""
var GAMUTS={
 srgb:{n:'sRGB / BT.709',R:[0.640,0.330],G:[0.300,0.600],B:[0.150,0.060]},
 p3:{n:'DCI-P3 (D65)',R:[0.680,0.320],G:[0.265,0.690],B:[0.150,0.060]},
 adobe:{n:'Adobe RGB',R:[0.640,0.330],G:[0.210,0.710],B:[0.150,0.060]},
 bt2020:{n:'BT.2020',R:[0.708,0.292],G:[0.170,0.797],B:[0.131,0.046]},
 ntsc:{n:'NTSC 1953',R:[0.670,0.330],G:[0.210,0.710],B:[0.140,0.080]}
};
function triPts(g){return [g.R,g.G,g.B];}
function shoelace(p){var a=0;for(var i=0;i<p.length;i++){var j=(i+1)%p.length;a+=p[i][0]*p[j][1]-p[j][0]*p[i][1];}return a/2;}
function area(p){return Math.abs(shoelace(p));}
function ccw(p){return shoelace(p)>0?p.slice():p.slice().reverse();}
function inside(pt,a,b){return (b[0]-a[0])*(pt[1]-a[1])-(b[1]-a[1])*(pt[0]-a[0])>=-1e-12;}
function segInt(p,q,a,b){
 var A1=q[1]-p[1],B1=p[0]-q[0],C1=A1*p[0]+B1*p[1];
 var A2=b[1]-a[1],B2=a[0]-b[0],C2=A2*a[0]+B2*a[1];
 var d=A1*B2-A2*B1;if(Math.abs(d)<1e-15)return q.slice();
 return [(B2*C1-B1*C2)/d,(A1*C2-A2*C1)/d];}
// Sutherland-Hodgman: clip subject polygon by convex clip polygon (CCW)
function clipPoly(subj,clip){
 var out=subj;
 for(var i=0;i<clip.length;i++){
  var a=clip[i],b=clip[(i+1)%clip.length];var inp=out;out=[];
  if(inp.length===0)break;
  for(var j=0;j<inp.length;j++){
   var P=inp[j],Q=inp[(j+1)%inp.length];var Pin=inside(P,a,b),Qin=inside(Q,a,b);
   if(Pin){out.push(P);if(!Qin)out.push(segInt(P,Q,a,b));}
   else if(Qin){out.push(segInt(P,Q,a,b));}
  }
 }
 return out;
}
function intersect(compTri,refTri){return clipPoly(ccw(compTri),ccw(refTri));}
function coverage(compTri,refTri){var ip=intersect(compTri,refTri);if(ip.length<3)return 0;return area(ip)/area(refTri)*100;}
function areaRatio(compTri,refTri){return area(compTri)/area(refTri)*100;}

// CIE 1931 xy -> CIE 1976 u'v'
function xy2uv(x,y){var d=-2*x+12*y+3;return [4*x/d,9*y/d];}
function plane(){return document.getElementById('planeSel').value;}
var RANGES={'1931':{xr:0.8,yr:0.9,xl:'x',yl:'y'},'1976':{xr:0.65,yr:0.62,xl:"u'",yl:"v'"}};
function toP(pt){return plane()==='1976'?xy2uv(pt[0],pt[1]):[pt[0],pt[1]];}
function triPtsP(g){return [toP(g.R),toP(g.G),toP(g.B)];}
// diagram mapping (plot box 46,60..456,470; data range depends on plane)
var DOX=46,DOY=470,DPW=410,DPH=410;
function PX(x){return DOX+DPW*(x/RANGES[plane()].xr);}
function PY(y){return DOY-DPH*(y/RANGES[plane()].yr);}
function num(id){var v=parseFloat(document.getElementById(id).value);return isFinite(v)?v:0;}
function ptsAttr(tri){return tri.map(function(p){return PX(p[0]).toFixed(1)+','+PY(p[1]).toFixed(1);}).join(' ');}

function curRef(){return GAMUTS[document.getElementById('refSel').value];}
function curComp(){
 var v=document.getElementById('compSel').value;
 if(v==='custom'){return {n:CUSTOM_NAME,R:[num('cRx'),num('cRy')],G:[num('cGx'),num('cGy')],B:[num('cBx'),num('cBy')]};}
 return GAMUTS[v];
}
function render(){
 var ref=curRef(),comp=curComp();
 var R=RANGES[plane()];
 // swap the chromaticity background + axis labels/ticks for the active plane
 document.getElementById('gamutImg').setAttribute('href',GAMUT_IMG[plane()]);
 document.getElementById('axX').textContent=R.xl;
 document.getElementById('axY').textContent=R.yl;
 var tx=document.getElementById('tickX');tx.setAttribute('x',PX(0.4).toFixed(0));
 var ty=document.getElementById('tickY');ty.setAttribute('y',PY(0.4).toFixed(0));
 // geometry in the active plane (xy or u'v')
 var rt=triPtsP(ref),ct=triPtsP(comp);
 document.getElementById('refTri').setAttribute('points',ptsAttr(rt));
 document.getElementById('compTri').setAttribute('points',ptsAttr(ct));
 var ip=intersect(ct,rt);
 document.getElementById('interPoly').setAttribute('points',ip.length>=3?ptsAttr(ip):'');
 var cp=[toP(comp.R),toP(comp.G),toP(comp.B)];
 ['R','G','B'].forEach(function(k,i){var d=document.getElementById('v'+k);d.setAttribute('cx',PX(cp[i][0]).toFixed(1));d.setAttribute('cy',PY(cp[i][1]).toFixed(1));});
 var cov=coverage(ct,rt),ar=areaRatio(ct,rt);
 document.getElementById('covV').textContent=cov.toFixed(1)+'%';
 document.getElementById('arV').textContent=ar.toFixed(1)+'%';
 document.getElementById('covName').textContent=comp.n+'  →  '+ref.n;
 document.getElementById('arName').textContent=comp.n+'  /  '+ref.n;
 document.getElementById('lgRef').textContent=ref.n;
 document.getElementById('lgComp').textContent=comp.n;
 function setRow(pre,tri,suf){
  [['R',0],['G',1],['B',2]].forEach(function(kv){
   document.getElementById(pre+kv[0]+'x'+suf).textContent=tri[kv[1]][0].toFixed(3);
   document.getElementById(pre+kv[0]+'y'+suf).textContent=tri[kv[1]][1].toFixed(3);
  });
 }
 setRow('r',triPts(ref),'');setRow('c',triPts(comp),'v');  // table always in xy
}
function onCompChange(){
 var custom=document.getElementById('compSel').value==='custom';
 document.getElementById('customCard').style.display=custom?'block':'none';
 render();
}
function init(){
 document.getElementById('refSel').addEventListener('change',render);
 document.getElementById('planeSel').addEventListener('change',render);
 document.getElementById('compSel').addEventListener('change',onCompChange);
 ['cRx','cRy','cGx','cGy','cBx','cBy'].forEach(function(id){document.getElementById(id).addEventListener('input',render);});
 onCompChange();
}
if(document.readyState!=='loading')init();else document.addEventListener('DOMContentLoaded',init);
"""


def gamut_options(sel_default):
    order = [("srgb", "sRGB / BT.709"), ("p3", "DCI-P3 (D65)"), ("adobe", "Adobe RGB"),
             ("bt2020", "BT.2020"), ("ntsc", "NTSC 1953")]
    out = []
    for val, lbl in order:
        sel = " selected" if val == sel_default else ""
        out.append(f'<option value="{val}"{sel}>{lbl}</option>')
    return "".join(out)


def comp_options(custom_label):
    return gamut_options("srgb") + f'<option value="custom">{custom_label}</option>'


def fig_svg():
    return f'''<svg viewBox="0 0 500 510" xmlns="http://www.w3.org/2000/svg">
  <image id="gamutImg" href="/assets/blog/cs-cie1931-gamut.png?v={BUILD}" x="46" y="60" width="410" height="410" preserveAspectRatio="none" opacity="0.55"/>
  <line x1="46" y1="470" x2="470" y2="470" stroke="#3a4a66" stroke-width="1.2"/>
  <line x1="46" y1="470" x2="46" y2="55" stroke="#3a4a66" stroke-width="1.2"/>
  <text x="40" y="474" text-anchor="end" font-size="10" fill="#647698">0</text>
  <text id="tickX" x="{46+410*0.4/0.8:.0f}" y="486" text-anchor="middle" font-size="10" fill="#647698">0.4</text>
  <text id="axX" x="466" y="486" text-anchor="end" font-size="11" fill="#93a3bf">x</text>
  <text id="tickY" x="32" y="{470-410*0.4/0.9:.0f}" text-anchor="end" font-size="10" fill="#647698">0.4</text>
  <text id="axY" x="34" y="64" font-size="11" fill="#93a3bf">y</text>
  <polygon id="interPoly" points="" fill="rgba(93,193,255,.28)" stroke="none"/>
  <polygon id="refTri" points="" fill="none" stroke="#ffffff" stroke-width="2" stroke-dasharray="6 4" opacity="0.9"/>
  <polygon id="compTri" points="" fill="none" stroke="#5dc1ff" stroke-width="2.4"/>
  <circle id="vR" r="5" fill="#ff5d6c" stroke="#000" stroke-width="1.2"/>
  <circle id="vG" r="5" fill="#3dd68c" stroke="#000" stroke-width="1.2"/>
  <circle id="vB" r="5" fill="#5d8bff" stroke="#000" stroke-width="1.2"/>
</svg>'''


EXTRA_CSS = """
.gamut-legend{display:flex;gap:20px;justify-content:center;flex-wrap:wrap;margin-top:10px;font-size:12px;font-family:'JetBrains Mono',monospace}
.gamut-legend .lg{display:flex;align-items:center;gap:7px;color:var(--dim)}
.gamut-legend .ln{display:inline-block;width:24px;height:0;border-top-width:3px}
.de-card .vname{font-size:11px;color:var(--mute);font-family:'JetBrains Mono',monospace;margin-top:4px;word-break:keep-all}
#customCard{margin-top:12px}
#customCard .prim-grid{display:grid;grid-template-columns:auto 1fr 1fr;gap:8px 10px;align-items:center}
#customCard .prim-grid label{font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--dim)}
#customCard .prim-grid input{background:var(--card2);border:1px solid var(--line);border-radius:8px;color:var(--txt);padding:7px 9px;font-family:'JetBrains Mono',monospace;font-size:13.5px;width:100%}
#customCard .prim-grid input:focus{outline:none;border-color:var(--accent)}
#customCard .ph{font-family:'JetBrains Mono',monospace;font-size:10.5px;color:var(--mute);text-align:center}
.prim-tbl td .pri{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:6px;vertical-align:middle}
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
<link rel="alternate" hreflang="ko" href="https://luckyplz.com/tools/gamut-comparator/">
<link rel="alternate" hreflang="en" href="https://luckyplz.com/tools/gamut-comparator-en/">
<link rel="alternate" hreflang="ja" href="https://luckyplz.com/tools/gamut-comparator-ja/">
<link rel="alternate" hreflang="zh" href="https://luckyplz.com/tools/gamut-comparator-zh/">
<link rel="alternate" hreflang="es" href="https://luckyplz.com/tools/gamut-comparator-es/">
<link rel="alternate" hreflang="x-default" href="https://luckyplz.com/tools/gamut-comparator-en/">
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
    <div class="f"><label>{{REFSEL}}</label><select id="refSel">{{REFOPTS}}</select></div>
    <div class="f"><label>{{COMPSEL}}</label><select id="compSel">{{COMPOPTS}}</select></div>
    <div class="f"><label>{{PLANELBL}}</label><select id="planeSel"><option value="1931" selected>CIE 1931 xy</option><option value="1976">CIE 1976 u&#8242;v&#8242;</option></select></div>
  </div>

  <div class="card" id="customCard" style="display:none">
    <h3>{{CUSTOMH}}</h3>
    <div class="prim-grid">
      <span class="ph"></span><span class="ph">x</span><span class="ph">y</span>
      <label style="color:#ff5d6c">R</label><input type="number" id="cRx" step="0.001" value="0.640"><input type="number" id="cRy" step="0.001" value="0.330">
      <label style="color:#3dd68c">G</label><input type="number" id="cGx" step="0.001" value="0.300"><input type="number" id="cGy" step="0.001" value="0.600">
      <label style="color:#5d8bff">B</label><input type="number" id="cBx" step="0.001" value="0.150"><input type="number" id="cBy" step="0.001" value="0.060">
    </div>
  </div>

  <div class="sec-h">{{DIAGRAM}}</div>
  <div class="figwrap" style="flex-direction:column">{{FIG}}
    <div class="gamut-legend">
      <span class="lg"><span class="ln" style="border-top:3px dashed #fff"></span><span id="lgRef">–</span></span>
      <span class="lg"><span class="ln" style="border-top:3px solid #5dc1ff"></span><span id="lgComp">–</span></span>
    </div>
  </div>

  <div class="de-grid" style="margin-top:16px">
    <div class="de-card hero"><div class="k">{{COVERAGE}}</div><div class="v" id="covV">–</div><div class="vname" id="covName">–</div><div class="k2">{{COVSUB}}</div></div>
    <div class="de-card" style="grid-column:1/-1"><div class="k">{{ARAT}}</div><div class="v" id="arV">–</div><div class="vname" id="arName">–</div><div class="k2">{{ARATSUB}}</div></div>
  </div>

  <div class="sec-h">{{PRIM}}</div>
  <table class="prim-tbl">
    <thead><tr><th></th><th>{{REF}} x</th><th>{{REF}} y</th><th>{{COMP}} x</th><th>{{COMP}} y</th></tr></thead>
    <tbody>
      <tr><td><span class="pri" style="background:#ff5d6c"></span>R</td><td id="rRx"></td><td id="rRy"></td><td id="cRxv"></td><td id="cRyv"></td></tr>
      <tr><td><span class="pri" style="background:#3dd68c"></span>G</td><td id="rGx"></td><td id="rGy"></td><td id="cGxv"></td><td id="cGyv"></td></tr>
      <tr><td><span class="pri" style="background:#5d8bff"></span>B</td><td id="rBx"></td><td id="rBy"></td><td id="cBxv"></td><td id="cByv"></td></tr>
    </tbody>
  </table>

  <details><summary>{{PIPELINE}}</summary><div class="body">{{PIPEBODY}}</div></details>

  <footer>{{FOOT}}<br><a href="{{ARTURL}}">{{READART}}</a> · <a href="/tools/">/tools</a> · <a href="/">{{HOME}}</a></footer>
</div>
<script>var CUSTOM_NAME={{CUSTOMNAME}};
var GAMUT_IMG={"1931":"/assets/blog/cs-cie1931-gamut.png?v={{BUILD}}","1976":"/assets/blog/cs-cie1976-gamut.png?v={{BUILD}}"};</script>
<script>{{JSCORE}}</script>
<script>navigator.serviceWorker&&navigator.serviceWorker.getRegistrations().then(function(rs){rs.forEach(function(r){r.unregister()})});</script>
<script src="/js/langSelect.js?v={{BUILD}}" defer></script>
<script src="/js/siteFooter.js?v={{BUILD}}" defer></script>
</body>
</html>
"""

# NOTE: the primaries table uses two id schemes (rRx.. for ref, cRx.. collide
# with the custom inputs). The comparison cells get distinct ids below.


def build(lang):
    m = META[lang]
    canon = f"https://luckyplz.com/tools/{SLUG}{LANG_SUFFIX[lang]}/"
    art = {"ko": "/blog/color-science-02-color-in-numbers/", "en": "/blog/color-science-02-color-in-numbers-en/",
           "ja": "/blog/color-science-02-color-in-numbers-ja/", "zh": "/blog/color-science-02-color-in-numbers-zh/",
           "es": "/blog/color-science-02-color-in-numbers-en/"}[lang]  # es article not yet -> en fallback
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
        "{{FIG}}": fig_svg(), "{{JSCORE}}": JS_CORE,
        "{{REFOPTS}}": gamut_options("p3"), "{{COMPOPTS}}": comp_options(S["custom"][lang]),
        "{{CUSTOMNAME}}": json.dumps(S["custom"][lang], ensure_ascii=False),
        "{{ARTURL}}": art,
        "{{H1}}": S["h1"][lang], "{{SUB}}": S["sub"][lang],
        "{{REFSEL}}": S["refSel"][lang], "{{COMPSEL}}": S["compSel"][lang], "{{CUSTOMH}}": S["customH"][lang], "{{PLANELBL}}": S["planeLbl"][lang],
        "{{DIAGRAM}}": S["diagram"][lang], "{{COVERAGE}}": S["coverage"][lang], "{{COVSUB}}": S["covSub"][lang],
        "{{ARAT}}": S["arat"][lang], "{{ARATSUB}}": S["aratSub"][lang], "{{PRIM}}": S["prim"][lang],
        "{{REF}}": S["ref"][lang], "{{COMP}}": S["comp"][lang],
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
    print("[done] gamut-comparator tool")


if __name__ == "__main__":
    main()
