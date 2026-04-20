/* Shared site-wide footer. Mounted as a static element at the end of <body>
   so it flows naturally below scrollable content pages (home, blog, privacy,
   about) and stays out of the way on game pages, where the page is covered
   by fixed #setupWrap/#gameWrap panels (the footer is still in the DOM for
   crawlers + AdSense review to find Privacy/About links). */
/* IMMEDIATELY capture beforeinstallprompt before anything else runs.
   Chrome fires this event exactly once per page load, and we don't
   want to miss it while pwaInstall.js is still being dynamically
   injected through the defer chain. We stash the event on window so
   pwaInstall.js (or anyone else) can consume it whenever they're
   ready. Doing this inside siteFooter (which is defer but loads on
   EVERY page before the deferred pwaInstall.js injection) is the
   earliest hook we have across the site without duplicating inline
   scripts in 18 HTML files. */
try{
    if('onbeforeinstallprompt' in window){
        window.addEventListener('beforeinstallprompt',function(e){
            try{e.preventDefault()}catch(_){}
            window._lpDeferredPrompt=e;
        });
        window.addEventListener('appinstalled',function(){
            window._lpDeferredPrompt=null;
        });
    }
}catch(_){}

(function(){
    if(document.querySelector('.lp-site-footer'))return;

    /* Game pages are fixed-overlay UIs (setupWrap / gameScreen). The global
       footer previously leaked into the mobile scroll area and the PWA
       install button overlapped in-game controls. Simplest fix: don't
       inject the footer or the PWA prompt at all on /games/*. Home and
       blog still get them. SEO on game pages is fine without the footer —
       crawl graph reaches Privacy/About/Blog from the home page. */
    var isGamePage=/^\/games\//.test(location.pathname);
    if(isGamePage)document.body.classList.add('lp-game-page');

    var style=document.createElement('style');
    style.textContent=
        '.lp-site-footer{position:relative;z-index:1;padding:22px 16px 28px;text-align:center;'
        +'font-family:"Noto Sans KR",sans-serif;font-size:.76em;line-height:1.8;'
        +'color:rgba(255,255,255,.42);background:transparent}'
        +'.lp-site-footer a{color:rgba(255,255,255,.65);margin:0 8px;text-decoration:none;transition:color .18s}'
        +'.lp-site-footer a:hover{color:#FF6B35}'
        +'.lp-site-footer .sep{opacity:.25;margin:0 2px}'
        +'.lp-site-footer .copy{display:block;margin-top:6px;opacity:.6}'
        /* Defense-in-depth: even if a stale cached script version still
           injects the footer or PWA button, hide them on game pages. */
        +'body.lp-game-page .lp-site-footer{display:none!important}'
        +'body.lp-game-page .lp-pwa-btn{display:none!important}'
        /* ========= UNIFIED BUTTON DESIGN SYSTEM =========
           Game pages still set their own accent gradients on #startBtn etc.
           so each game keeps its colour personality. These rules polish the
           geometry / micro-interactions / focus / typography across the
           whole site so the buttons look hand-crafted, not thrown-together. */
        /* Base: smoother easing everywhere + tighter active press */
        +'button,.btn{transition:transform .15s cubic-bezier(.2,.8,.4,1),box-shadow .22s ease,filter .18s ease,background .2s ease,border-color .2s ease;font-feature-settings:"tnum","cv11";-webkit-tap-highlight-color:transparent}'
        +'button:active,.btn:active{transform:translateY(1px) scale(.985);transition-duration:.08s}'
        +'button:focus-visible,.btn:focus-visible,input:focus-visible{outline:2px solid rgba(255,230,109,.75);outline-offset:3px}'
        /* Primary action — unified geometry + layered shadow + shimmer sweep on hover.
           Each game keeps its own background gradient (specificity wins) — we only
           tune radius, padding, letter-spacing, shadow depth, and add the sweep. */
        +'#startBtn{border-radius:14px!important;letter-spacing:.12em!important;text-transform:uppercase!important;position:relative!important;overflow:hidden!important;border:0!important;box-shadow:0 8px 24px -6px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.22)!important}'
        +'#startBtn::after{content:"";position:absolute;inset:0;background:linear-gradient(120deg,transparent 35%,rgba(255,255,255,.22) 50%,transparent 65%);transform:translateX(-120%);transition:transform .7s cubic-bezier(.2,.8,.4,1);pointer-events:none}'
        +'#startBtn:hover::after{transform:translateX(120%)}'
        +'#startBtn:hover{filter:brightness(1.06);transform:translateY(-2px)}'
        /* Replay / back-to-setup / modal primaries — calmer weight. */
        +'.btn-replay,.btn-primary,.lp-room-modal .btn.primary{border-radius:12px!important;letter-spacing:.04em!important;font-weight:700!important;box-shadow:0 6px 18px -6px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.2)!important}'
        +'.btn-replay:hover,.btn-primary:hover,.lp-room-modal .btn.primary:hover{filter:brightness(1.08);transform:translateY(-2px)}'
        /* Ghost / cancel in modals */
        +'.lp-room-modal .btn.ghost{border-radius:12px!important;background:rgba(255,255,255,.04)!important;border:1px solid rgba(255,255,255,.12)!important}'
        +'.lp-room-modal .btn.ghost:hover{background:rgba(255,255,255,.09)!important;border-color:rgba(255,255,255,.22)!important;transform:translateY(-1px)}'
        /* Watch-Together chip — only style the standalone-row version. When
           the class is combined with .pab-btn (the pc-action-bar variant),
           defer to pab-btn\'s column layout so it sits with its toolbar
           siblings. */
        +'.lp-room-online-btn:not(.pab-btn){padding:12px 18px!important;border-radius:14px!important;font-family:"Orbitron","Noto Sans KR",sans-serif!important;font-weight:700!important;letter-spacing:.08em!important;font-size:.82em!important;background:linear-gradient(145deg,rgba(0,217,255,.12),rgba(0,217,255,.04))!important;border:1.5px solid rgba(0,217,255,.4)!important;color:#00D9FF!important;box-shadow:0 4px 14px -4px rgba(0,217,255,.25)!important;position:relative;overflow:hidden}'
        +'.lp-room-online-btn:not(.pab-btn)::after{content:"";position:absolute;inset:0;background:linear-gradient(120deg,transparent 40%,rgba(0,217,255,.18) 50%,transparent 60%);transform:translateX(-120%);transition:transform .7s cubic-bezier(.2,.8,.4,1);pointer-events:none}'
        +'.lp-room-online-btn:not(.pab-btn):hover::after{transform:translateX(120%)}'
        +'.lp-room-online-btn:not(.pab-btn):hover{border-color:rgba(0,217,255,.75)!important;box-shadow:0 8px 22px -4px rgba(0,217,255,.4)!important;transform:translateY(-2px)}'
        /* Share buttons — add soft depth + firmer hover */
        +'.share-btn{padding:9px 14px!important;border-radius:12px!important;font-weight:700!important;letter-spacing:.015em!important;box-shadow:0 3px 10px -3px rgba(0,0,0,.3),inset 0 1px 0 rgba(255,255,255,.14)!important}'
        +'.share-btn:hover{transform:translateY(-2px);filter:brightness(1.1);box-shadow:0 8px 22px -4px rgba(0,0,0,.42),inset 0 1px 0 rgba(255,255,255,.2)!important}'
        /* Ladder 5-button toolbar */
        +'.pab-btn{border-radius:12px!important;letter-spacing:.02em!important}'
        +'.pab-btn:hover:not(:disabled){background:rgba(255,255,255,.08)!important;border-color:rgba(255,255,255,.28)!important;transform:translateY(-1px)!important;box-shadow:0 4px 12px -4px rgba(0,0,0,.35)!important}'
        +'.pab-start{box-shadow:0 6px 18px -6px rgba(255,107,53,.55),inset 0 1px 0 rgba(255,255,255,.22)!important}'
        /* Small chips / toggles — consistent radius + hover lift */
        +'.opt-chip,.add-chip,.preset-btn{border-radius:999px!important;letter-spacing:.02em!important;transition:background .2s,border-color .2s,transform .15s,box-shadow .2s}'
        +'.opt-chip:hover,.preset-btn:hover{transform:translateY(-1px);box-shadow:0 4px 10px -3px rgba(0,0,0,.3)}'
        /* Home page CTAs */
        +'.lp-site-footer a,.lp-pwa-btn,.auth-btn,.dl-cta{font-feature-settings:"tnum"}';
    document.head.appendChild(style);

    if(!isGamePage){
        var f=document.createElement('footer');
        f.className='lp-site-footer';
        f.innerHTML=
            '<a href="/">Home</a><span class="sep">·</span>'
            +'<a href="/about/">About</a><span class="sep">·</span>'
            +'<a href="/privacy/">Privacy</a><span class="sep">·</span>'
            +'<a href="/blog/">Blog</a><span class="sep">·</span>'
            +'<a href="mailto:luckyplz.contact@gmail.com">Contact</a>'
            +'<span class="copy">© 2026 Lucky Please · luckyplz.com</span>';
        document.body.appendChild(f);
    }

    /* AdSense slot injector — only loads if the page has a
       <div data-lp-ad="..."> somewhere. Keeps pages without ads clean. */
    if(document.querySelector('[data-lp-ad]')){
        var s=document.createElement('script');
        s.src='/js/adSlots.js?v=1776664470';
        s.defer=true;
        document.body.appendChild(s);
    }

    /* Recent-results memory — small module, loaded everywhere so game
       pages can write results on finish and home page can read them. */
    if(!window.LpRecent){
        var rr=document.createElement('script');
        rr.src='/js/recentResults.js?v=1776664470';
        document.body.appendChild(rr);
    }

    /* PWA install prompt — skip on game pages (overlaps in-game buttons
       and isn't useful mid-race anyway). Home/blog still get it. */
    if(!isGamePage){
        var pwa=document.createElement('script');
        pwa.src='/js/pwaInstall.js?v=1776664470';
        pwa.defer=true;
        document.body.appendChild(pwa);
    }

    /* Analytics event helper — delegated listeners + LpRecent bridge. */
    var tr=document.createElement('script');
    tr.src='/js/lpTrack.js?v=1776664470';
    tr.defer=true;
    document.body.appendChild(tr);

    /* Share helper — Web Share API + clipboard fallback for Kakao. */
    var sh=document.createElement('script');
    sh.src='/js/lpShare.js?v=1776664470';
    sh.defer=true;
    document.body.appendChild(sh);

    /* Online room (host/guest) — loaded on game pages AND the home page
       (so the home-page "Join Watch-Together" button can use LpRoom's
       probeRoom + join modal). Requires Supabase to already be on the
       page for the Realtime client.
       Query-string version is a defensive cache-bust — mobile browsers
       have been observed to ignore the no-cache header on /js/* for
       dynamically-injected scripts. Bump this on breaking changes. */
    if(window.supabase){
        var rr2=document.createElement('script');
        rr2.src='/js/lpRoom.js?v=1776664470';
        rr2.defer=true;
        document.body.appendChild(rr2);
    }
})();
