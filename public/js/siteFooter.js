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
    /* Treat /lobby/ as a game-class page too — it's an interactive
       waiting room (not browseable content), so the global footer
       would just push the lobby card around, and the lp-fs-btn
       toggle should appear there for symmetry with /games/*. */
    var isGamePage=/^\/games\//.test(location.pathname)||/^\/lobby\/?/.test(location.pathname);
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
        /* ========= Digital activity counter ========= */
        /* Sits ABOVE the Home/About/... link row inside the same footer.
           Label + zero-padded digits in little white boxes, sky-blue LED-
           style digit glyphs inside. Hidden until LpActivity.stats()
           resolves — never renders as zeros while we wait so it doesn't
           flash. */
        +'.lp-stat-row{display:inline-flex;flex-wrap:wrap;justify-content:center;align-items:center;'
        +'gap:8px;margin:0 auto 14px;padding:0;'
        +'font-family:"Orbitron","Noto Sans KR",sans-serif;'
        +'font-size:.72em;letter-spacing:.12em;line-height:1;color:rgba(255,255,255,.5)}'
        /* Re-assert the native [hidden] hide because the inline-flex
           rule above has higher specificity and would otherwise win. */
        +'.lp-stat-row[hidden]{display:none!important}'
        +'.lp-stat-label{text-transform:uppercase;font-weight:700;color:rgba(255,255,255,.55);letter-spacing:.2em}'
        +'.lp-stat-sep{opacity:.3;margin:0 2px;font-weight:700}'
        +'.lp-digits{display:inline-flex;gap:2px}'
        /* Outline-only digit boxes. Previous solid-white fill was too
           bright on the dark home page and drowned out the logo /
           games grid above it. White border + transparent fill keeps
           the LED-counter frame read while fading into the page. */
        +'.lp-digit{display:inline-flex;align-items:center;justify-content:center;'
        +'width:14px;height:20px;background:transparent;color:#00D9FF;'
        +'border:1px solid rgba(255,255,255,.55);'
        +'font-family:"Orbitron","Courier New",monospace;font-weight:900;font-size:13px;line-height:1;'
        +'border-radius:3px;font-variant-numeric:tabular-nums}'
        /* Leading zeros dimmed + their box border muted to match. */
        +'.lp-digit.lead{color:rgba(0,217,255,.25);border-color:rgba(255,255,255,.2)}'
        +'@media(max-width:600px){'
        +'.lp-stat-row{font-size:.62em;gap:6px;margin-bottom:10px}'
        +'.lp-digit{width:12px;height:18px;font-size:11px}'
        +'}'
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
        /* Label localization for the activity counter — kept INSIDE the
           footer injector because siteFooter.js can't import index.html's
           I18N. Reads localStorage (same key index.html writes) AND
           listens for the `lp:langchanged` CustomEvent that
           applyLanguage() dispatches so live language-switching updates
           the labels without a reload. */
        var L_TODAY={ko:'오늘',en:'TODAY',gb:'TODAY',ja:'今日',zh:'今日',es:'HOY',de:'HEUTE',fr:'JOUR',pt:'HOJE',ru:'СЕГОДНЯ',ar:'اليوم',hi:'आज',th:'วันนี้',id:'HARI INI',vi:'HÔM NAY',tr:'BUGÜN'};
        var L_TOTAL={ko:'누적',en:'TOTAL',gb:'TOTAL',ja:'累計',zh:'累计',es:'TOTAL',de:'GESAMT',fr:'TOTAL',pt:'TOTAL',ru:'ВСЕГО',ar:'المجموع',hi:'कुल',th:'รวม',id:'TOTAL',vi:'TỔNG',tr:'TOPLAM'};
        function pickLang(){ return (localStorage.getItem('luckyplz_lang')||'en').toLowerCase(); }
        function lblToday(l){ return L_TODAY[l]||L_TODAY.en; }
        function lblTotal(l){ return L_TOTAL[l]||L_TOTAL.en; }
        var initLang=pickLang();

        var f=document.createElement('footer');
        f.className='lp-site-footer';
        f.innerHTML=
            '<div class="lp-stat-row" id="lpStatRow" hidden>'
                +'<span class="lp-stat-label" data-lp-stat="today">'+lblToday(initLang)+'</span>'
                +'<span class="lp-digits" id="lpDigitsToday"></span>'
                +'<span class="lp-stat-sep">·</span>'
                +'<span class="lp-stat-label" data-lp-stat="total">'+lblTotal(initLang)+'</span>'
                +'<span class="lp-digits" id="lpDigitsTotal"></span>'
            +'</div>'
            +'<a href="/">Home</a><span class="sep">·</span>'
            +'<a href="/about/">About</a><span class="sep">·</span>'
            +'<a href="/privacy/">Privacy</a><span class="sep">·</span>'
            +'<a href="/blog/">Blog</a><span class="sep">·</span>'
            +'<a href="mailto:luckyplz.contact@gmail.com">Contact</a>'
            +'<span class="copy">© 2026 Lucky Please · luckyplz.com</span>';
        document.body.appendChild(f);

        /* Admin-only gate. Early-launch traffic is so low (오늘 1 / 누적 3)
           that showing the counter publicly reads as "dead site" rather
           than social proof. So we render it ONLY when the cached
           profile says the viewer is an admin — the owner can sanity-
           check traffic from the live site without needing to log into
           the dashboard. When cumulative traffic hits a marketing-
           worthy threshold we can lift the gate. */
        function isCurrentUserAdmin(){
            try{
                var raw = localStorage.getItem('lp_profile_cache_v1');
                if (!raw) return false;
                var c = JSON.parse(raw);
                var role = c && c.profile && c.profile.role;
                return role === 'admin' || role === 'super_admin';
            } catch(_){ return false; }
        }

        /* Fetch stats once LpActivity is available AND the viewer is an
           admin. Zero-pad into fixed-width digit-box rows (5 for today,
           9 for total); leading zeros dimmed. Row stays hidden on any
           failure / null return / non-admin viewer. */
        (function waitActivity(tries){
            if (!isCurrentUserAdmin()){
                /* Profile cache might arrive after siteFooter runs on a
                   cold-start login. Retry a few times before giving up
                   silently — NON-admin viewers just never see the row. */
                if (tries > 0) setTimeout(function(){ waitActivity(tries-1); }, 150);
                return;
            }
            if(window.LpActivity && window.LpActivity.stats){
                window.LpActivity.stats().then(function(s){
                    if(!s) return;
                    function pad(n, len){
                        var cap = Math.pow(10, len) - 1;
                        var v = Math.max(0, Math.min(cap, (n|0)));
                        var str = String(v);
                        var pre = len - str.length;
                        var html = '';
                        for (var i=0;i<pre;i++) html += '<span class="lp-digit lead">0</span>';
                        for (var j=0;j<str.length;j++) html += '<span class="lp-digit">'+str[j]+'</span>';
                        return html;
                    }
                    var td = document.getElementById('lpDigitsToday');
                    var tt = document.getElementById('lpDigitsTotal');
                    var row = document.getElementById('lpStatRow');
                    if(!td||!tt||!row) return;
                    td.innerHTML = pad(s.today||0, 5);
                    tt.innerHTML = pad(s.total||0, 9);
                    row.hidden = false;
                }).catch(function(){});
            } else if (tries > 0){
                setTimeout(function(){ waitActivity(tries-1); }, 100);
            }
        })(40);

        /* Live language switch — index.html's applyLanguage() fires
           this event after writing to localStorage. We just re-label
           in place; digit boxes stay untouched. */
        document.addEventListener('lp:langchanged', function(ev){
            var l = (ev && ev.detail && ev.detail.lang) || pickLang();
            l = String(l).toLowerCase();
            var tEl = document.querySelector('[data-lp-stat="today"]');
            var nEl = document.querySelector('[data-lp-stat="total"]');
            if (tEl) tEl.textContent = lblToday(l);
            if (nEl) nEl.textContent = lblTotal(l);
        });
    }

    /* Mobile fullscreen helper — autorun on every page so phone
       users get the address-bar-hidden experience on first tap.
       Loaded FIRST among the dynamic scripts so its meta-tag
       enforcement (viewport-fit, apple-mobile-web-app-status-bar-style)
       runs as early as possible. The module itself self-bootstraps
       and is idempotent across multiple loads. */
    if(!window.LpFullscreen){
        var fs=document.createElement('script');
        fs.src='/js/lpFullscreen.js?v=1777771386';
        document.body.appendChild(fs);
    }

    /* In-app WebView exit helper — detects KakaoTalk / Naver / etc
       in-app browsers via UA and shows a bottom banner inviting the
       user to re-open in their default browser. KakaoTalk-specific
       schemes (most common Korean entry path) get a 1-click "Open"
       button; others get instruction-only. No-ops if not in any
       known in-app WebView. Loaded on EVERY page so users land in
       the right browser from the first hop, not just /games/*. */
    if(!window.LpInAppExit){
        var ia=document.createElement('script');
        ia.src='/js/lpInAppExit.js?v=1777771386';
        ia.defer=true;
        document.body.appendChild(ia);
    }

    /* Random-shuffle BGM for /games/* pages. Self-skips if no
       /assets/bgm/<gameId>/track*.mp3 files exist, or if the gameId
       is in its internal SKIP_GAMES list (car-racing + dodge ship
       their own audio engines). Module's own first-interaction
       listener triggers playback after the user's first tap, so even
       a slow defer load won't cause missed audio. */
    if(isGamePage&&!window.LpBgm){
        var bgm=document.createElement('script');
        bgm.src='/js/lpBgm.js?v=1777771386';
        bgm.defer=true;
        document.body.appendChild(bgm);
    }

    /* Screen Wake Lock + wall-clock phase scheduler — both shared
       across all multiplayer-capable games. Loaded on every game
       page; no-ops on browsers without the Wake Lock API. Must
       arrive before lpRoom resolves so per-game start handlers can
       call LpWakeLock.acquire / LpPhaseTimer.schedule synchronously
       without waiting on script-load. */
    if(isGamePage&&!window.LpWakeLock){
        var wl=document.createElement('script');
        wl.src='/js/lpWakeLock.js?v=1777771386';
        document.body.appendChild(wl);
    }
    if(isGamePage&&!window.LpPhaseTimer){
        var pt=document.createElement('script');
        pt.src='/js/lpPhaseTimer.js?v=1777771386';
        document.body.appendChild(pt);
    }

    /* AdSense slot injector — only loads if the page has a
       <div data-lp-ad="..."> somewhere. Keeps pages without ads clean. */
    if(document.querySelector('[data-lp-ad]')){
        var s=document.createElement('script');
        s.src='/js/adSlots.js?v=1777771386';
        s.defer=true;
        document.body.appendChild(s);
    }

    /* Recent-results memory — small module, loaded everywhere so game
       pages can write results on finish and home page can read them. */
    if(!window.LpRecent){
        var rr=document.createElement('script');
        rr.src='/js/recentResults.js?v=1777771386';
        document.body.appendChild(rr);
    }

    /* PWA install prompt — skip on game pages (overlaps in-game buttons
       and isn't useful mid-race anyway). Home/blog still get it. */
    if(!isGamePage){
        var pwa=document.createElement('script');
        pwa.src='/js/pwaInstall.js?v=1777771386';
        pwa.defer=true;
        document.body.appendChild(pwa);
    }

    /* Analytics event helper — delegated listeners + LpRecent bridge. */
    var tr=document.createElement('script');
    tr.src='/js/lpTrack.js?v=1777771386';
    tr.defer=true;
    document.body.appendChild(tr);

    /* Share helper — Web Share API + clipboard fallback for Kakao. */
    var sh=document.createElement('script');
    sh.src='/js/lpShare.js?v=1777771386';
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
        rr2.src='/js/lpRoom.js?v=1777771386';
        rr2.defer=true;
        document.body.appendChild(rr2);

        /* Shared host-control bar (pause/end/paused-overlay/ended-overlay)
           piggybacks on lpRoom — loaded everywhere lpRoom is loaded so
           every online game can `LpHostCtl.install({role,room,...})`
           without per-game script tag bookkeeping. */
        var hc=document.createElement('script');
        hc.src='/js/lpHostCtl.js?v=1777771386';
        hc.defer=true;
        document.body.appendChild(hc);

        /* Battle.net-style floating multiplayer panel. Listens for
           `lp-room-host-ready` / `lp-room-guest-ready` CustomEvents
           fired by lpRoom; auto-mounts without any per-game wiring. */
        var mp=document.createElement('script');
        mp.src='/js/lpMultiplayer.js?v=1777771386';
        mp.defer=true;
        document.body.appendChild(mp);
    }

    /* Social layer (friends + DM) — loaded EVERYWHERE including game
       pages, so the room-status "+ friend" shortcut (Phase 9) can call
       LpSocial.sendFriendRequest(). Bundle is ~8 KB gzipped. */
    if(window.supabase&&!window.LpSocial){
        var ls=document.createElement('script');
        ls.src='/js/lpSocial.js?v=1777771386';
        ls.defer=true;
        document.body.appendChild(ls);
    }
    /* Site-wide activity counter — logs one play per (game × device ×
       5-min window) to public.game_plays so the home page can render
       honest "⚡ 오늘 N번 · 누적 M번" social-proof stats. autoLog() only
       fires on /games/* URLs; home-page stats fetch is initiated from
       index.html's own script. */
    if(window.supabase&&!window.LpActivity){
        var la=document.createElement('script');
        la.src='/js/lpActivity.js?v=1777771386';
        la.defer=true;
        la.onload=function(){
            if(isGamePage&&window.LpActivity){
                try{ window.LpActivity.autoLog(); }catch(_){}
            }
        };
        document.body.appendChild(la);
    }
    /* Presence layer — online/dnd/offline status for the current user
       plus live friend presence map. Loaded everywhere so every page
       can colour avatar indicators and the invite modal can filter
       for online-only friends. Requires Supabase. */
    if(window.supabase&&!window.LpPresence){
        var lp=document.createElement('script');
        lp.src='/js/lpPresence.js?v=1777771386';
        lp.defer=true;
        document.body.appendChild(lp);
    }
    /* Game invite layer — listens for incoming invites and pops a
       cross-page toast with Accept/Decline. MUST be everywhere
       (including game pages) so a user in a different room still
       sees their friend's invite. Requires Supabase + LpPresence. */
    if(window.supabase&&!window.LpInvite){
        var li=document.createElement('script');
        li.src='/js/lpInvite.js?v=1777771386';
        li.defer=true;
        document.body.appendChild(li);
    }
    /* Game-page invite button — the floating "친구 초대" pill + modal
       that lives ONLY on /games/*. The module itself self-gates by
       pathname, so loading it everywhere is harmless; restricting
       here just saves a network request on non-game pages. */
    if(window.supabase&&isGamePage&&!window.LpInviteButton){
        var lib=document.createElement('script');
        lib.src='/js/lpInviteButton.js?v=1777771386';
        lib.defer=true;
        document.body.appendChild(lib);
    }
    /* Notifications (in-page toast + foreground OS Notification API,
       no Service Worker — see CLAUDE.md SW policy). Skipped on game
       pages — a toast sliding in mid-race would be jarring. */
    if(window.supabase&&!isGamePage&&!window.LpNotify){
        var ln=document.createElement('script');
        ln.src='/js/lpNotify.js?v=1777771386';
        ln.defer=true;
        document.body.appendChild(ln);
    }
})();
