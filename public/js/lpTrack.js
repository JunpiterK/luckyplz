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
     game_start      — games can call window.LpTrack('game_start', {gameId})

   LpStat — 1st-party 방문 통계(운영 상황판 /ops/ 의 원천). /api/p (Pages
   Function) → Supabase lp_hits. IP·쿠키 없이 브라우저 저장소의 무작위 id 만 쓴다.
   - 페이지뷰 1건 = 시작 1번 + 머문 시간 갱신(15초 · 1분 · 이후 4분마다 · 숨김·이탈 때).
     매번 같은 내용을 보내고 서버가 upsert 하므로 어느 하나가 유실돼도 된다
   - 머문 시간은 '화면에 보이는 동안 + 마지막 조작 후 30분 이내' 만 센다.
     켜 둔 채 방치한 탭이 몇 시간으로 잡히지 않게
   - 세션 = 30분 무활동이면 새로. 랜딩의 iframe 속 게임은 페이지뷰를 따로
     만들지 않고 이벤트만 부모 페이지뷰에 붙인다
   - luckyplz.com 에서만 켜진다(로컬 미리보기는 ?lp_stat=1 로 시험) */
(function(){
    if(window.LpStat)return;
    var EP='/api/p', IDLE=1800000, SES=1800000;
    var ss=null;try{ss=window.sessionStorage}catch(e){}
    var on=/(^|\.)luckyplz\.com$/.test(location.hostname);
    try{if(/[?&]lp_stat=1/.test(location.search))ss.setItem('lp_stat_test','1');on=on||ss.getItem('lp_stat_test')==='1'}catch(e){}
    if(!on)return;

    if(window.top!==window.self){
        /* 같은 origin 부모(랜딩)의 페이지뷰에 이벤트만 붙인다 */
        window.LpStat={ev:function(n,p){try{var P=window.parent.LpStat;if(P&&P.ev)P.ev(n,p)}catch(e){}}};
        return;
    }

    var ls=null;try{ls=window.localStorage;ls.setItem('lp_t','1');ls.removeItem('lp_t')}catch(e){ls=null}
    function get(k){try{return ls?ls.getItem(k):null}catch(e){return null}}
    function put(k,v){try{if(ls)ls.setItem(k,v)}catch(e){}}
    function uuid(){
        try{if(crypto.randomUUID)return crypto.randomUUID()}catch(e){}
        var b=new Uint8Array(16),h=[],i;
        try{crypto.getRandomValues(b)}catch(e){for(i=0;i<16;i++)b[i]=Math.random()*256|0}
        b[6]=b[6]&15|64;b[8]=b[8]&63|128;
        for(i=0;i<16;i++)h.push((b[i]+256).toString(16).slice(1));
        return h.slice(0,4).join('')+'-'+h.slice(4,6).join('')+'-'+h.slice(6,8).join('')+'-'+h.slice(8,10).join('')+'-'+h.slice(10).join('');
    }
    var ID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

    var vid=get('lp_vid'),firstVisit=false;
    if(!ID.test(vid||'')){vid=uuid();put('lp_vid',vid);firstVisit=true}
    var S=null;
    function touchSes(){
        var t=Date.now();
        try{var x=JSON.parse(get('lp_ses')||'null');if(x&&x.id)S=x}catch(e){}   /* 다른 탭이 갱신했을 수 있다 */
        if(!S||!ID.test(S.id||'')||!(t-(S.t||0)<SES)){
            var vn=(parseInt(get('lp_vn')||'0',10)||0)+1;put('lp_vn',String(vn));
            S={id:uuid(),t:t,n:0,vn:vn,nw:firstVisit||vn===1};
        }
        S.t=t;put('lp_ses',JSON.stringify(S));
    }
    function sesAge(){
        try{var x=JSON.parse(get('lp_ses')||'null');if(x&&x.t)return Date.now()-x.t}catch(e){}
        return S?Date.now()-(S.t||0):Infinity;
    }

    var pv,sp,acc,since,lastAct,Q=[],flushT=0,hbT=0,hbN=0,ctx=null,lastFinal=-1;
    function vis(){return document.visibilityState!=='hidden'}
    function tick(){
        var t=Date.now();
        if(since!=null){var end=Math.min(t,lastAct+IDLE);if(end>since)acc+=end-since;since=(vis()&&t<lastAct+IDLE)?t:null}
        return acc;
    }
    function path(){
        return location.pathname.replace(/\/index\.html?$/,'/').replace(/^\/r\/[^\/]+.*/,'/r/*').replace(/^\/u\/[^\/]+.*/,'/u/*').slice(0,200);
    }
    function begin(){
        touchSes();S.n=(S.n||0)+1;put('lp_ses',JSON.stringify(S));
        pv=uuid();sp=S.n;acc=0;lastAct=Date.now();since=vis()?lastAct:null;hbN=0;lastFinal=-1;
        var q=new URLSearchParams(location.search),ref='';
        try{if(document.referrer&&new URL(document.referrer).host!==location.host)ref=document.referrer.slice(0,400)}catch(e){}
        ctx={id:pv,sid:S.id,vid:vid,path:path(),sp:sp,new:!!S.nw,vn:S.vn,
            ref:sp===1?ref:'',utm:sp===1?(q.get('utm_source')||''):'',cmp:sp===1?(q.get('utm_campaign')||''):'',
            lang:get('luckyplz_lang')||'',blang:navigator.language||'',
            vw:window.innerWidth,vh:window.innerHeight,tch:navigator.maxTouchPoints||0,me:get('lp_stat_me')==='1'};
        send(false);beat();
    }
    function send(final){
        if(!ctx)return;
        ctx.dur=tick();
        if(final&&!Q.length&&ctx.dur===lastFinal)return;   /* 숨김 + pagehide 가 연달아 와도 한 번만 */
        if(final)lastFinal=ctx.dur;
        if(Q.length)ctx.ev=Q.splice(0,20);else delete ctx.ev;
        var body=JSON.stringify(ctx);
        if(final&&navigator.sendBeacon){try{if(navigator.sendBeacon(EP,body))return}catch(e){}}
        try{fetch(EP,{method:'POST',body:body,keepalive:true,credentials:'omit',headers:{'content-type':'text/plain'}}).catch(function(){})}catch(e){}
    }
    /* 15초 · 1분 · 이후 4분마다(최대 3시간). 숨김·방치 중에는 보내지 않는다 */
    function beat(){
        clearTimeout(hbT);
        var d=hbN===0?15000:hbN===1?45000:240000;
        if(hbN>48)return;
        hbT=setTimeout(function(){hbN++;tick();if(since!=null){touchSes();send(false)}beat()},d);
    }
    function act(){
        var t=Date.now();if(t-lastAct<1000&&since!=null)return;
        tick();lastAct=t;if(since==null&&vis())since=t;
    }
    ['pointerdown','keydown','wheel','touchstart','scroll'].forEach(function(n){
        window.addEventListener(n,act,{passive:true,capture:true});
    });
    document.addEventListener('visibilitychange',function(){
        if(!vis()){tick();since=null;send(true)}
        else if(sesAge()>=SES)begin();   /* 30분 넘게 떠나 있다 돌아오면 새 세션 */
        else{lastAct=Date.now();since=lastAct;touchSes()}
    });
    window.addEventListener('pagehide',function(){tick();since=null;send(true)});
    window.addEventListener('pageshow',function(e){if(e.persisted)begin()});

    window.LpStat={
        ev:function(name,params){
            if(!/^[a-z_]{1,32}$/.test(name||''))return;
            var g=params&&(params.game||params.gameId);
            if(!g){var m=location.pathname.match(/\/games\/([^\/]+)/);g=m?m[1]:''}
            var p=null;
            if(params&&params.platform)p={platform:String(params.platform).slice(0,20)};
            Q.push({n:name,g:String(g||'').slice(0,32),p:p||undefined});
            act();
            clearTimeout(flushT);flushT=setTimeout(function(){send(false)},4000);
        }
    };
    begin();
})();
(function(){
    function fire(name, params){
        try{if(window.LpStat)window.LpStat.ev(name, params)}catch(e){}
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
