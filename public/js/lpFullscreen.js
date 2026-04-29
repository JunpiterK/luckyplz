/* lpFullscreen.js — mobile/tablet auto-fullscreen for Lucky Please.
   ─────────────────────────────────────────────────────────────────
   Goal: every game page (single-player + multiplayer) should fill
   the entire screen on phones with the browser address bar hidden.

   Strategy (defense in depth — no single technique works on every
   browser, so we layer all of them):

   1. PWA standalone — manifest already has display:standalone, so a
      home-screen install gets pure chrome-less. Detected via
      matchMedia('(display-mode:standalone)') / navigator.standalone;
      no extra work needed when in this mode.

   2. Fullscreen API — on the FIRST user gesture (touchstart / click)
      we call documentElement.requestFullscreen({navigationUI:'hide'}).
        - Android Chrome / Edge / Samsung Internet: works.
        - iOS Safari (any version): fails on documentElement (only
          <video> is allowed, a long-standing WebKit limit).
      Browsers require a real user gesture, so the call is wired to
      the first interaction, not to onload.

   3. Scroll-to-1 trick — ancient iOS Safari technique: programmatic
      scrollTo(0,1) shortly after page load nudges Safari to hide the
      URL bar. Combined with body min-height:101vh it stays hidden
      until the user explicitly scrolls back. Modern Safari ignores
      this for top-level pages but cheap to keep — no harm if it
      no-ops.

   4. viewport-fit=cover — extends the layout into iOS notch + home-
      indicator safe areas. Without this, viewport-fit=auto leaves
      black bands at top/bottom on notched devices that we can't fill
      even in fullscreen mode.

   5. Status-bar meta — apple-mobile-web-app-status-bar-style set to
      black-translucent so when the user DOES install as PWA, the
      iOS status bar overlays the page in dark theme rather than
      showing a white default bar.

   6. Manual toggle button — small floating ⛶ button (mobile only)
      so users who exited fullscreen (back gesture / ESC) can re-enter
      without reloading the page. Also acts as a discovery affordance
      on iOS where #2 is a no-op.

   Public API:
     LpFullscreen.enter()   → request fullscreen now
     LpFullscreen.exit()    → exit fullscreen
     LpFullscreen.toggle()  → enter or exit
     LpFullscreen.isOn()    → true if currently fullscreen OR standalone
     LpFullscreen.isStandalone() → installed-PWA detection

   Dispatches CustomEvent('lp-fullscreen-change', {detail:{on}}) on
   window so games can react (e.g. recompute canvas size).
*/
(function(){
  'use strict';
  if(window.LpFullscreen)return;

  /* ---------- environment detection ---------- */
  function isStandalone(){
    try{
      if(window.matchMedia&&window.matchMedia('(display-mode:standalone)').matches)return true;
      if(window.matchMedia&&window.matchMedia('(display-mode:fullscreen)').matches)return true;
    }catch(_){}
    if(window.navigator&&window.navigator.standalone===true)return true;
    if(typeof document.referrer==='string'&&document.referrer.indexOf('android-app://')===0)return true;
    return false;
  }
  function inIframe(){
    try{return window.self!==window.top}catch(_){return true}
  }
  function isSmallScreen(){
    /* ≤900px covers phones AND most tablets in portrait. Desktop
       browsers don't need address-bar hiding because they already
       give the page the full viewport. */
    try{return window.matchMedia&&window.matchMedia('(max-width:900px)').matches}
    catch(_){return window.innerWidth<=900}
  }
  function isIos(){
    try{return /iPad|iPhone|iPod/.test(navigator.userAgent)&&!window.MSStream}
    catch(_){return false}
  }
  function isFullscreenActive(){
    return !!(document.fullscreenElement||document.webkitFullscreenElement||document.mozFullScreenElement||document.msFullscreenElement);
  }

  /* ---------- fullscreen API helpers ---------- */
  function getReq(el){
    return el.requestFullscreen
        ||el.webkitRequestFullscreen
        ||el.webkitRequestFullScreen
        ||el.mozRequestFullScreen
        ||el.msRequestFullscreen;
  }
  function getExit(){
    return document.exitFullscreen
        ||document.webkitExitFullscreen
        ||document.webkitCancelFullScreen
        ||document.mozCancelFullScreen
        ||document.msExitFullscreen;
  }

  /* ---------- meta tag enforcement ----------
     Run BEFORE first paint so viewport-fit=cover takes effect on the
     initial layout (notched iPhones get the page extended into the
     safe areas). Idempotent — runs once per pageload. */
  function ensureMeta(){
    function setMeta(name,content){
      var m=document.querySelector('meta[name="'+name+'"]');
      if(!m){
        m=document.createElement('meta');
        m.name=name;
        document.head.appendChild(m);
      }
      m.content=content;
    }
    /* Update viewport — preserve any existing settings, just append
       viewport-fit=cover if missing. Some pages have width=device-width,
       maximum-scale=1, user-scalable=no — keep those, add the fit. */
    var vp=document.querySelector('meta[name="viewport"]');
    var base='width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no,viewport-fit=cover';
    if(!vp){
      vp=document.createElement('meta');
      vp.name='viewport';
      vp.content=base;
      document.head.appendChild(vp);
    }else if(!/viewport-fit\s*=/.test(vp.content)){
      vp.content=(vp.content||'').replace(/\s*$/,'')+(vp.content?',':'')+'viewport-fit=cover';
    }
    /* iOS standalone meta — black-translucent gives the cleanest look
       (dark site bg shows through the status bar instead of a white
       blob). apple-mobile-web-app-capable=yes opts in to the
       fullscreen-when-installed mode. */
    setMeta('apple-mobile-web-app-capable','yes');
    setMeta('apple-mobile-web-app-status-bar-style','black-translucent');
    /* Android Chrome equivalent (deprecated but still respected on
       older versions; modern Chrome uses the manifest). */
    setMeta('mobile-web-app-capable','yes');
  }

  /* ---------- safe-area + dynamic viewport CSS ----------
     Inject once. Applies safe-area padding to body so notched phones
     don't clip game UI behind the home indicator / camera notch. The
     100dvh fallback chain keeps height correct as the browser chrome
     auto-hides on scroll. */
  function ensureCSS(){
    if(document.getElementById('lp-fs-style'))return;
    var s=document.createElement('style');
    s.id='lp-fs-style';
    s.textContent=[
      /* Make the body fill the dynamic viewport. 100vh is the static
         viewport (excludes the URL bar's auto-hide animation), 100dvh
         is the dynamic one — newer browsers honour dvh, older ones
         fall back to vh. The double declaration is the standard
         pattern from web.dev / CSS Working Group examples. */
      'html,body{min-height:100vh;min-height:100dvh}',
      /* Safe-area padding only matters when viewport-fit=cover is on.
         env() falls back to 0 on older browsers. */
      '@supports(padding:env(safe-area-inset-top)){',
      '  body{padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom);',
      '    padding-left:env(safe-area-inset-left);padding-right:env(safe-area-inset-right)}',
      '}',
      /* iOS scroll-trick helper — ensures the document is just barely
         taller than the viewport so a programmatic scrollTo(0,1) can
         actually scroll. Without 1px of headroom, Safari ignores the
         scroll and the URL bar stays visible. Min-height kept to .25vh
         + 1px so layout impact is negligible. */
      'body.lp-fs-scroll-trick{min-height:calc(100vh + 1px);min-height:calc(100dvh + 1px)}',
      /* Fullscreen toggle button — only shown on small screens, only
         on game pages (lp-game-page class set by siteFooter.js for
         /games/* and /lobby/ paths). bottom-right so it doesn\'t clash
         with floating-home (bottom-left). z-index 9040 sits BELOW the
         lpMultiplayer panel (9050) — when the panel is at its default
         bottom anchor it covers the button, but that\'s OK because:
         (a) on Android, requestFullscreen already succeeded on the
             first tap so the button is functionally unused.
         (b) on iOS, the user can drag the panel up (per the new
             vertical-drag support) to expose the button.
         The user\'s "panel takes click priority" requirement is
         preserved this way. safe-area-inset moves the button above
         iOS\'s home indicator on notched devices. */
      '.lp-fs-btn{position:fixed;',
      '  bottom:calc(14px + env(safe-area-inset-bottom,0px));',
      '  right:calc(14px + env(safe-area-inset-right,0px));',
      '  z-index:9040;',
      '  width:40px;height:40px;border-radius:50%;border:1.5px solid rgba(0,217,255,.4);',
      '  background:rgba(0,0,0,.55);color:#00D9FF;font-size:1.05em;cursor:pointer;',
      '  display:none;align-items:center;justify-content:center;backdrop-filter:blur(8px);',
      '  -webkit-backdrop-filter:blur(8px);box-shadow:0 4px 12px rgba(0,0,0,.4);',
      '  transition:transform .15s,background .15s,border-color .15s;padding:0;line-height:1}',
      '.lp-fs-btn:hover{background:rgba(0,217,255,.18);border-color:#4FC3F7}',
      '.lp-fs-btn:active{transform:scale(.92)}',
      /* Show on small screens only (desktop already has full real
         estate). Hide entirely when standalone — the browser chrome
         is already gone, button is visual noise. */
      '@media (max-width:900px){body.lp-game-page .lp-fs-btn:not(.standalone){display:flex}}'
    ].join('\n');
    document.head.appendChild(s);
  }

  /* ---------- core actions ---------- */
  var attempted=false;
  function enter(opts){
    if(isStandalone())return Promise.resolve(true);
    if(inIframe())return Promise.resolve(false);
    if(isFullscreenActive())return Promise.resolve(true);

    var el=document.documentElement;
    var req=getReq(el);
    if(!req){
      /* No fullscreen API at all — try scroll-trick as a fallback for
         very old iOS Safari that hides the URL bar on first scroll. */
      tryScrollTrick();
      return Promise.resolve(false);
    }
    try{
      var p=req.call(el,{navigationUI:'hide'});
      if(p&&p.then){
        return p.then(function(){return true},function(){
          /* iOS Safari rejects requestFullscreen on documentElement.
             Scroll-trick is the only path on Safari — engage it. */
          tryScrollTrick();
          return false;
        });
      }
      /* Older webkit: no promise, check state after a tick. */
      return new Promise(function(resolve){
        setTimeout(function(){
          if(isFullscreenActive())resolve(true);
          else{tryScrollTrick();resolve(false)}
        },200);
      });
    }catch(_){
      tryScrollTrick();
      return Promise.resolve(false);
    }
  }
  function exit(){
    var ex=getExit();
    if(ex&&isFullscreenActive()){
      try{return ex.call(document)}catch(_){}
    }
    return Promise.resolve();
  }
  function toggle(){return isFullscreenActive()?exit():enter()}

  /* iOS scroll-trick — must run AFTER body has loaded enough to be
     scrollable. We add a class that gives 1px of vertical headroom
     so the scroll actually moves something. */
  var scrollTrickArmed=false;
  function tryScrollTrick(){
    if(!isIos())return;
    if(scrollTrickArmed)return;
    scrollTrickArmed=true;
    if(document.body)document.body.classList.add('lp-fs-scroll-trick');
    /* Two attempts spaced apart — Safari sometimes ignores the first
       call when invoked too soon after a touch. */
    setTimeout(function(){window.scrollTo(0,1)},80);
    setTimeout(function(){window.scrollTo(0,1)},400);
  }

  /* ---------- first-interaction trigger ---------- */
  function shouldAutoFullscreen(){
    /* Auto-fullscreen is only desirable on PLAY surfaces — game pages
       + the lobby waiting room. On the home page, the user is
       browsing the games carousel + scrolling content; jumping into
       fullscreen on their first tap is jarring. Same for /blog/,
       /privacy/, etc. The toggle button still works site-wide for
       users who explicitly want fullscreen. */
    if(!isSmallScreen())return false;
    var path=location.pathname||'';
    return /^\/(games|lobby)\//.test(path)||/^\/lobby$/.test(path);
  }
  function onFirstInteraction(e){
    if(!shouldAutoFullscreen())return cleanupFirstInteraction();
    /* Don\'t hijack a tap that is mid-input on a form field — would
       break iOS focus + on-screen keyboard. The Fullscreen API call
       on documentElement may also blur the input. */
    var t=e&&e.target;
    if(t&&t.tagName){
      var tag=t.tagName.toLowerCase();
      if(tag==='input'||tag==='textarea'||tag==='select')return;
    }
    enter();
  }
  function cleanupFirstInteraction(){
    document.removeEventListener('touchstart',onFirstInteraction,true);
    document.removeEventListener('click',onFirstInteraction,true);
  }

  /* ---------- toggle button (mobile only) ---------- */
  var btn=null;
  function ensureButton(){
    if(btn)return btn;
    /* Skip on home + non-game pages (the home picker grid + blog don\'t
       need a fullscreen toggle — most users browse there briefly).
       lp-game-page class is set by siteFooter.js for /games/* paths. */
    if(!document.body)return null;
    btn=document.createElement('button');
    btn.type='button';
    btn.className='lp-fs-btn';
    btn.setAttribute('aria-label','Toggle fullscreen');
    btn.setAttribute('title','전체화면');
    btn.textContent='⛶';
    btn.addEventListener('click',function(e){
      e.preventDefault();
      e.stopPropagation();
      toggle();
    });
    document.body.appendChild(btn);
    if(isStandalone())btn.classList.add('standalone');
    return btn;
  }
  function syncButton(){
    if(!btn)return;
    btn.textContent=isFullscreenActive()?'⛶':'⛶';
    /* Could swap glyph for "exit fullscreen" but ⛶ is widely
       understood as a generic toggle; keep simple to avoid font-fallback
       issues on some Android browsers. */
    if(isStandalone())btn.classList.add('standalone');
    else btn.classList.remove('standalone');
  }

  /* ---------- state-change broadcast ---------- */
  function onChange(){
    syncButton();
    try{window.dispatchEvent(new CustomEvent('lp-fullscreen-change',{detail:{on:isFullscreenActive()||isStandalone()}}))}catch(_){}
  }

  /* ---------- bootstrap ---------- */
  function boot(){
    ensureMeta();
    ensureCSS();
    if(document.body){
      ensureButton();
      syncButton();
    }
    /* First-interaction listener — capture phase + non-passive so the
       requestFullscreen call sits inside the same gesture that the
       browser is checking for. */
    if(!isStandalone()&&!inIframe()&&isSmallScreen()){
      document.addEventListener('touchstart',onFirstInteraction,true);
      document.addEventListener('click',onFirstInteraction,true);
    }
    document.addEventListener('fullscreenchange',onChange);
    document.addEventListener('webkitfullscreenchange',onChange);
    document.addEventListener('mozfullscreenchange',onChange);
    document.addEventListener('MSFullscreenChange',onChange);
    /* Re-arm scroll-trick on visibility change — iOS often shows the
       URL bar again when returning from background. */
    document.addEventListener('visibilitychange',function(){
      if(!document.hidden&&isIos()&&!isStandalone()){
        scrollTrickArmed=false;
        tryScrollTrick();
      }
    });
  }
  if(document.readyState==='loading'){
    /* Run meta + css setup as early as possible (before first paint). */
    ensureMeta();ensureCSS();
    document.addEventListener('DOMContentLoaded',boot);
  }else{
    boot();
  }

  window.LpFullscreen={
    enter:enter,
    exit:exit,
    toggle:toggle,
    isOn:function(){return isFullscreenActive()||isStandalone()},
    isStandalone:isStandalone,
    isSmallScreen:isSmallScreen
  };
})();
