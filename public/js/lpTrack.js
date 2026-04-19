/* Lucky Please — analytics helper
   Thin wrapper around window.gtag so any part of the codebase can fire
   a consistent custom event without caring whether GA4 is initialised
   yet (no-op when gtag isn't loaded). Loads everywhere via siteFooter.

   Auto-tracked events (no per-game wiring needed):
     share_click     — any .share-btn click. platform inferred from class.
     preset_apply    — .lp-preset-chip click on setup screens.
     recent_click    — .lp-recent-chip click on home.
     game_end        — fired by recentResults.js save() via a bridge below.
   Caller-fired events:
     game_start      — games can call window.LpTrack('game_start', {gameId}) */
(function(){
    function fire(name, params){
        try{
            if(typeof window.gtag!=='function')return;
            window.gtag('event', name, params||{});
        }catch(e){}
    }
    window.LpTrack=fire;

    /* Infer game id from the URL path /games/<id>/. Returns null for home/blog. */
    function currentGameId(){
        const m=location.pathname.match(/\/games\/([^\/]+)/);
        return m?m[1]:null;
    }

    /* Extract share platform from the classList — buttons are styled with
       a distinctive class like .kakao / .line / .whatsapp / .copy-link /
       .native-share / .twitter / .facebook / .telegram. */
    const PLATFORM_MAP={
        kakao:'kakao', line:'line', whatsapp:'whatsapp', telegram:'telegram',
        twitter:'twitter', facebook:'facebook', 'copy-link':'copy', 'native-share':'native'
    };
    function sharePlatform(el){
        if(!el||!el.classList)return'unknown';
        for(const key in PLATFORM_MAP){
            if(el.classList.contains(key))return PLATFORM_MAP[key];
        }
        return'unknown';
    }

    /* Delegated click listener catches the 4 common actions anywhere in
       the document without per-game wiring. */
    document.addEventListener('click', function(e){
        const shareBtn=e.target.closest('.share-btn');
        if(shareBtn){
            fire('share_click', {
                game: currentGameId()||'home',
                platform: sharePlatform(shareBtn)
            });
            return;
        }
        const presetChip=e.target.closest('.lp-preset-chip');
        if(presetChip && !e.target.closest('.lp-preset-x')){
            fire('preset_apply', { game: currentGameId()||'unknown' });
            return;
        }
        const recentChip=e.target.closest('.lp-recent-chip');
        if(recentChip){
            const href=recentChip.getAttribute('href')||'';
            const gm=href.match(/\/games\/([^\/?]+)/);
            fire('recent_click', { game: gm?gm[1]:'unknown' });
            return;
        }
    }, true);

    /* Bridge: patch LpRecent.save to also emit a game_end event so we
       measure completion rate without touching every game file. */
    function installRecentBridge(){
        if(!window.LpRecent||window.LpRecent._lpTrackPatched)return;
        const orig=window.LpRecent.save;
        window.LpRecent.save=function(gameId, summary, url){
            fire('game_end', { game: gameId||'unknown' });
            return orig.apply(this, arguments);
        };
        window.LpRecent._lpTrackPatched=true;
    }
    /* recentResults.js loads asynchronously via siteFooter — poll briefly. */
    let tries=0;
    const iv=setInterval(function(){
        tries++;
        if(window.LpRecent){installRecentBridge();clearInterval(iv)}
        else if(tries>40)clearInterval(iv);
    },100);
})();
