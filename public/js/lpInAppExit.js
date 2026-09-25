/* lpInAppExit.js — 호환용 심 (2026-09-25).
   본체는 /js/lpInApp.js 로 옮겼다(메신저 전반 지원·자동 탈출·안내 시트).
   캐시된 옛 siteFooter.js 가 아직 이 파일을 부르는 경우를 위해, 같은 ?v= 로
   새 모듈을 불러 주기만 한다. 새 코드에서 이 파일을 참조하지 말 것. */
(function(){
  if (window.LpInApp || window.__lpInAppShim) return;
  window.__lpInAppShim = true;
  var v = '';
  try { var m = /[?&]v=([^&]+)/.exec((document.currentScript && document.currentScript.src) || ''); if (m) v = m[1]; } catch(_){}
  var s = document.createElement('script');
  s.src = '/js/lpInApp.js' + (v ? '?v=' + v : '?v=' + Date.now());
  (document.head || document.documentElement).appendChild(s);
})();
