/* Shared site-wide footer. Mounted as a static element at the end of <body>
   so it flows naturally below scrollable content pages (home, blog, privacy,
   about) and stays out of the way on game pages, where the page is covered
   by fixed #setupWrap/#gameWrap panels (the footer is still in the DOM for
   crawlers + AdSense review to find Privacy/About links). */
(function(){
    if(document.querySelector('.lp-site-footer'))return;

    /* Game pages are fixed-overlay UIs (setupWrap / gameScreen). The global
       footer leaks into mobile scroll when rendered there, and the PWA
       install button overlaps in-game controls. Flag the body so both can
       be CSS-suppressed on /games/* while still visible on home/blog. */
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
        /* On game pages, keep the footer in the DOM (SEO + AdSense policy)
           but visually collapse it — games are full-viewport apps, not
           scrollable pages, so a footer below "the fold" is just noise. */
        +'body.lp-game-page .lp-site-footer{display:none}'
        +'body.lp-game-page .lp-pwa-btn{display:none!important}';
    document.head.appendChild(style);

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

    /* AdSense slot injector — only loads if the page has a
       <div data-lp-ad="..."> somewhere. Keeps pages without ads clean. */
    if(document.querySelector('[data-lp-ad]')){
        var s=document.createElement('script');
        s.src='/js/adSlots.js';
        s.defer=true;
        document.body.appendChild(s);
    }

    /* Recent-results memory — small module, loaded everywhere so game
       pages can write results on finish and home page can read them. */
    if(!window.LpRecent){
        var rr=document.createElement('script');
        rr.src='/js/recentResults.js';
        document.body.appendChild(rr);
    }

    /* PWA install prompt — listens for beforeinstallprompt everywhere. */
    var pwa=document.createElement('script');
    pwa.src='/js/pwaInstall.js';
    pwa.defer=true;
    document.body.appendChild(pwa);

    /* Analytics event helper — delegated listeners + LpRecent bridge. */
    var tr=document.createElement('script');
    tr.src='/js/lpTrack.js';
    tr.defer=true;
    document.body.appendChild(tr);

    /* Share helper — Web Share API + clipboard fallback for Kakao. */
    var sh=document.createElement('script');
    sh.src='/js/lpShare.js';
    sh.defer=true;
    document.body.appendChild(sh);
})();
