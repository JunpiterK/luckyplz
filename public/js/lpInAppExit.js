/* lpInAppExit.js — bounce out of in-app WebViews to the system browser.
   ─────────────────────────────────────────────────────────────────
   Problem: Korean users typically share luckyplz links via KakaoTalk.
   When a friend taps the link inside KakaoTalk, the page opens in
   KakaoTalk's in-app WebView, which:
     • Forces landscape rotation on some devices (override the page's
       orientation preference)
     • Blocks the Fullscreen API on documentElement
     • Blocks the Screen Orientation API
     • Has flaky localStorage / cookie behavior across in-app sessions
     • Doesn't honor viewport-fit=cover (notch areas mis-rendered)
   Net result: every game except car-racing (which is landscape-native)
   is unplayable. Same problems hit Naver app, Facebook, Instagram,
   Line, etc.

   Solution: detect known in-app WebViews via UA, show a non-intrusive
   banner at the bottom inviting the user to re-open in their default
   browser. The "Open" button uses each in-app's documented URL
   scheme to bounce out:
     • KakaoTalk: kakaotalk://web/openExternal?url=<encoded>
       (works on both Android + iOS KakaoTalk since 2015)
     • Naver app: no public scheme, show instructions
     • Instagram / Facebook: no scheme, show instructions

   The banner is dismissable via the × button (session-only — re-shows
   on page reload because the game-breaking issues are too severe to
   silently skip).

   Public API:
     LpInAppExit.openExternal()   — trigger external open
     LpInAppExit.isInAppBrowser   — boolean detection result
     LpInAppExit.dismiss()        — hide the banner
*/
(function(){
  'use strict';
  if (window.LpInAppExit) return;

  var UA = navigator.userAgent || '';

  /* Detection. Each app injects a recognisable token into UA:
     - KakaoTalk:  ".../KAKAOTALK 1234.567"
     - Naver app:  ".../NAVER(inapp; ...)" or ".../naver"
     - Line:       ".../Line/9.99.0"
     - Instagram:  ".../Instagram 100.0.0.0"
     - Facebook:   "FB_IAB/...; FBAN/...; FBAV/..."
     - Daum app:   ".../DaumApps"
  */
  var IN_APP = {
    kakaotalk: /KAKAOTALK/i.test(UA),
    naver:     /NAVER\(inapp/i.test(UA) || /; naver\)/i.test(UA),
    daum:      /DaumApps/i.test(UA),
    line:      /\bLine\//i.test(UA),
    instagram: /Instagram/i.test(UA),
    facebook:  /FBAN|FBAV|FB_IAB/i.test(UA),
    twitter:   /Twitter/i.test(UA)
  };

  var detected = null;
  for (var k in IN_APP) {
    if (IN_APP[k]) { detected = k; break; }
  }
  /* Not in any known in-app browser → module is a no-op. */
  if (!detected) return;

  /* Open-external schemes per app. KakaoTalk has a documented one
     that works on both Android + iOS. Other apps don't have a
     public scheme — we just show instructions in those cases. */
  var SCHEMES = {
    kakaotalk: function(url){
      return 'kakaotalk://web/openExternal?url=' + encodeURIComponent(url);
    }
    /* Add more here when their in-app schemes become available.
       Naver/Daum officially recommend their "외부 브라우저로 열기"
       three-dot menu; no programmatic option. */
  };

  function openExternal(){
    var url = location.href;
    var schemeBuilder = SCHEMES[detected];
    if (schemeBuilder) {
      try {
        location.href = schemeBuilder(url);
        return;
      } catch(_){}
    }
    /* No scheme available — try copying URL + show instructions.
       Most modern in-app browsers expose a 3-dot menu with "Open
       in browser" as a manual fallback. */
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).catch(function(){});
      }
    } catch(_){}
    alert('우측 상단 메뉴 (⋮ 또는 ⋯) 에서 "외부 브라우저로 열기" 를 눌러주세요.\n\nURL 이 클립보드에 복사됐어요.');
  }

  function dismiss(){
    var el = document.getElementById('lp-inapp-banner');
    if (el) el.remove();
  }

  /* CSS injected once. We use a high z-index (above ads + fullscreen
     button) and respect iOS safe-area-inset-bottom so the banner
     doesn't overlap the home indicator. */
  function ensureCss(){
    if (document.getElementById('lp-inapp-css')) return;
    var s = document.createElement('style');
    s.id = 'lp-inapp-css';
    s.textContent = ''
      + '#lp-inapp-banner{'
      +   'position:fixed;left:0;right:0;bottom:0;z-index:2147483600;'
      +   'background:linear-gradient(135deg,#FF9A3C,#FF6B35);color:#fff;'
      +   'padding:12px 14px;padding-bottom:calc(12px + env(safe-area-inset-bottom, 0px));'
      +   'display:flex;align-items:center;gap:10px;'
      +   'font-family:\'Noto Sans KR\',sans-serif;font-size:.85em;line-height:1.4;'
      +   'box-shadow:0 -6px 18px rgba(0,0,0,.45);'
      +   'animation:lp-inapp-slide .35s ease-out'
      + '}'
      + '@keyframes lp-inapp-slide{from{transform:translateY(100%)}to{transform:translateY(0)}}'
      + '#lp-inapp-banner .msg{flex:1;min-width:0}'
      + '#lp-inapp-banner .msg strong{font-weight:800;color:#FFF8DC}'
      + '#lp-inapp-banner button.open{'
      +   'background:#fff;color:#FF6B35;border:0;border-radius:8px;'
      +   'padding:9px 16px;font-weight:800;font-family:inherit;font-size:1em;'
      +   'cursor:pointer;flex-shrink:0;letter-spacing:.02em'
      + '}'
      + '#lp-inapp-banner button.open:active{transform:translateY(1px)}'
      + '#lp-inapp-banner button.close{'
      +   'background:rgba(255,255,255,.18);color:#fff;border:0;border-radius:8px;'
      +   'padding:8px 11px;font-family:inherit;font-size:1.05em;font-weight:700;'
      +   'cursor:pointer;flex-shrink:0;line-height:1'
      + '}'
      + '#lp-inapp-banner button.close:active{background:rgba(255,255,255,.28)}'
      /* Push body content up so the banner doesn't overlap fixed
         bottom-aligned elements that pages have. */
      + 'body.lp-inapp-banner-on{padding-bottom:calc(72px + env(safe-area-inset-bottom, 0px))}';
    document.head.appendChild(s);
  }

  function showBanner(){
    if (document.getElementById('lp-inapp-banner')) return;
    ensureCss();

    /* Per-app messaging. KakaoTalk gets a 1-click button; others get
       an instruction-only flow that copies URL + shows where to find
       "Open in browser" in the menu. */
    var hasOneClick = !!SCHEMES[detected];

    var APP_LABELS = {
      kakaotalk: '카카오톡',
      naver:     '네이버 앱',
      daum:      '다음 앱',
      line:      'Line',
      instagram: 'Instagram',
      facebook:  'Facebook',
      twitter:   'Twitter/X'
    };
    var appLabel = APP_LABELS[detected] || '인앱 브라우저';

    /* Korean copy is primary (Korean market is the audience for the
       biggest pain — KakaoTalk). Multi-lang version could come later
       via lpBgm-style i18n; for now the message is short and obvious. */
    var msg = '<strong>' + appLabel + ' 내장 브라우저</strong>에선 게임이 정상 작동하지 않을 수 있어요. '
            + '<strong>외부 브라우저</strong>에서 열어주세요.';

    var btnLabel = hasOneClick ? '열기' : '안내 보기';

    var div = document.createElement('div');
    div.id = 'lp-inapp-banner';
    div.setAttribute('role','alert');
    div.innerHTML = ''
      + '<div class="msg">' + msg + '</div>'
      + '<button class="open" type="button">' + btnLabel + '</button>'
      + '<button class="close" type="button" aria-label="닫기">×</button>';

    /* Wire handlers programmatically (no inline onclick — CSP friendly). */
    div.querySelector('button.open').addEventListener('click', openExternal);
    div.querySelector('button.close').addEventListener('click', dismiss);

    document.body.appendChild(div);
    document.body.classList.add('lp-inapp-banner-on');
  }

  /* Run after DOM is ready so document.body exists. */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', showBanner);
  } else {
    showBanner();
  }

  window.LpInAppExit = {
    openExternal: openExternal,
    dismiss: dismiss,
    isInAppBrowser: true,
    detected: detected
  };
})();
