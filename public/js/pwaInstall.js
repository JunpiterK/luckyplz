/* Lucky Please — PWA install prompt
   Listens for the browser's `beforeinstallprompt` event (Chrome/Edge on
   Android + desktop Chrome) and shows a small, dismissible custom button
   so the user can add Lucky Please to their home screen. Installed PWA
   users have ~3x the return rate of one-shot web visitors.

   UX rules:
   - Never shows if the page is already launched from a home-screen install
     (display-mode: standalone).
   - Hidden on mobile `maximum-scale=1` setup screens so it doesn't cover
     the Start button.
   - Dismissal is remembered in localStorage for 30 days (avoid nagging).
   - Auto-hides after native install dialog is accepted. */
(function(){
    /* 7 days instead of the original 30. On Android Chrome the prompt
       felt "random" to real users — Chrome's own engagement heuristic
       already skips sessions where the user isn't engaged enough, so
       stacking another 30-day dismiss cooldown on top made it feel
       broken. 7 days = once a week max if they keep dismissing, which
       is still polite but recoverable. */
    const COOLDOWN_DAYS=7;
    const KEY='luckyplz_pwa_dismissed_at';

    /* Already in PWA mode? Skip. */
    function isStandalone(){
        return window.matchMedia('(display-mode: standalone)').matches
            || window.navigator.standalone===true;
    }
    function inCooldown(){
        try{
            const t=parseInt(localStorage.getItem(KEY)||'0',10);
            if(!t)return false;
            return (Date.now()-t)<COOLDOWN_DAYS*86400000;
        }catch(e){return false}
    }
    function setDismissed(){
        try{localStorage.setItem(KEY,String(Date.now()))}catch(e){}
    }

    function injectStyles(){
        if(document.getElementById('lp-pwa-styles'))return;
        const s=document.createElement('style');
        s.id='lp-pwa-styles';
        s.textContent=
            '.lp-pwa-btn{position:fixed;bottom:16px;right:16px;z-index:900;display:none;align-items:center;gap:8px;padding:10px 16px;border-radius:999px;background:linear-gradient(135deg,#FFE66D,#FF9A3C);color:#0A0A1A;font-family:"Noto Sans KR",sans-serif;font-weight:800;font-size:.82em;letter-spacing:.02em;border:0;cursor:pointer;box-shadow:0 8px 24px rgba(255,154,60,.35);transition:transform .15s,box-shadow .2s}'
           +'.lp-pwa-btn:hover{transform:translateY(-1px);box-shadow:0 12px 32px rgba(255,154,60,.45)}'
           +'.lp-pwa-btn .lp-pwa-x{opacity:.55;margin-left:4px;font-size:1.05em;line-height:1}'
           +'.lp-pwa-btn .lp-pwa-x:hover{opacity:1}'
           +'.lp-pwa-btn.show{display:inline-flex}'
           +'@media(max-width:500px){.lp-pwa-btn{bottom:12px;right:12px;padding:9px 14px;font-size:.78em}}';
        document.head.appendChild(s);
    }

    function pickLabel(){
        const lang=(localStorage.getItem('luckyplz_lang')||document.documentElement.lang||'en').toLowerCase().split('-')[0];
        return (
            lang==='ko'?'📱 홈 화면에 추가':
            lang==='ja'?'📱 ホームに追加':
            lang==='zh'?'📱 添加到主屏':
            lang==='es'?'📱 Instalar app':
            lang==='de'?'📱 App installieren':
            lang==='fr'?'📱 Installer l\'app':
            '📱 Install app'
        );
    }

    let deferredPrompt=null;
    let btn=null;

    function createBtn(){
        if(btn)return btn;
        btn=document.createElement('button');
        btn.type='button';
        btn.className='lp-pwa-btn';
        btn.setAttribute('aria-label','Install Lucky Please');
        btn.innerHTML='<span class="lp-pwa-label">'+pickLabel()+'</span><span class="lp-pwa-x" aria-label="dismiss">&times;</span>';
        /* Dismiss: stop propagation so main click doesn't fire too. */
        btn.querySelector('.lp-pwa-x').addEventListener('click',function(ev){
            ev.stopPropagation();
            setDismissed();
            btn.classList.remove('show');
        });
        btn.addEventListener('click',function(){
            if(!deferredPrompt)return;
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then(function(c){
                if(c&&c.outcome==='accepted'){
                    btn.classList.remove('show');
                }else{
                    setDismissed();
                    btn.classList.remove('show');
                }
                deferredPrompt=null;
            }).catch(function(){});
        });
        document.body.appendChild(btn);
        return btn;
    }

    function onPrompt(e){
        /* iOS Safari doesn't fire this event; we skip iOS entirely — Apple
           doesn't expose a programmatic install flow. */
        try{e.preventDefault&&e.preventDefault()}catch(_){}
        deferredPrompt=e;
        if(isStandalone()||inCooldown())return;
        injectStyles();
        createBtn().classList.add('show');
    }

    /* Two-way hook-up: (a) pick up any event that siteFooter.js already
       captured before this script loaded, (b) also register a live
       listener for events that fire AFTER this script is live. Without
       (a) we'd silently miss the prompt when Chrome fires it during
       the window between siteFooter's early-capture and the defer
       injection of pwaInstall.js — which is exactly the "sometimes it
       shows, sometimes it doesn't" bug users reported on Android. */
    if(window._lpDeferredPrompt){
        onPrompt(window._lpDeferredPrompt);
    }
    window.addEventListener('beforeinstallprompt',onPrompt);
    window.addEventListener('appinstalled',function(){
        if(btn)btn.classList.remove('show');
        deferredPrompt=null;
        try{localStorage.removeItem(KEY)}catch(_){}
    });

    /* Debug helper: `window.LpPwaReset()` from DevTools clears the
       cooldown and, if the prompt is currently available, immediately
       shows the button. Handy when testing or when a user says "I
       accidentally dismissed it and want it back". */
    window.LpPwaReset=function(){
        try{localStorage.removeItem(KEY)}catch(_){}
        if(deferredPrompt&&!isStandalone()){
            injectStyles();
            createBtn().classList.add('show');
        }
        return !!deferredPrompt;
    };
})();
