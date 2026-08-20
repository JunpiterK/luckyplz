/* lpBgm.js — random-shuffle background music for /games/* pages.
   ─────────────────────────────────────────────────────────────────
   Goal (2026-06-11 정책 변경): BGM 은 페이지 진입 시가 아니라 게임이
   실제로 시작될 때 시작된다. 각 게임의 시작 버튼 핸들러가
   LpBgm.start() (또는 모듈 로드 전이면 window.__lpBgmWanted=true) 를
   호출한다. 그 후에는 /assets/bgm/<gameId>/track1.mp3 ... track4.mp3
   중 하나를 랜덤 재생; 트랙이 끝나면 다른 트랙으로 무한 셔플.

   Why "speculative play" instead of HEAD probe + delayed start
   ────────────────────────────────────────────────────────────
   The previous version did:
     start() → discoverTracks() (4 HEAD probes) → playNext()
   The HEAD probe is async, so by the time playNext() ran, the user
   gesture (touch/click) had already fired and unwound. Browsers track
   autoplay permission via the call stack: an Audio.play() call
   reachable from a synchronous user gesture is allowed; one inside a
   .then() callback isn't. So the original "start on first touch"
   handler kicked off start(), but the actual play() call landed past
   the gesture window and got rejected — silently — leaving the page
   muted forever.

   Fix:
     - No HEAD probe up front. We just try track1.mp3 (or whichever
       random index hasn't been marked-missing). The Audio element
       fetches it; if 404, it fires `error` and we move to the next
       index. If 200, it fires `canplay` and we proceed.
     - The audio.play() call runs inside the SYNC body of either
       (a) the DOMContentLoaded handler (sticky activation from the
       user's same-origin click on the home page usually permits this),
       or (b) the first-interaction handler.
     - 'started' is only set true after play() actually succeeds, so
       a failed autoplay leaves the door open for the first-interaction
       handler to retry.

   Skipped games: car-racing and dodge ship their own audio engines
   (in-page logic that handles their game's BGM lifecycle — fade-in
   coupled to race start, pause-with-game, etc). Adding a second
   concurrent stream on top would clash.

   Note: even though they're skipped from auto-play here, both games
   STORE their mp3 files at /assets/bgm/<gameId>/track*.mp3 (same
   convention as the auto-played games) so the directory tree stays
   symmetric and Cloudflare's /assets/* cache rule applies uniformly.
   They just construct their own Audio() inside their game scripts
   pointing at the shared file path.

   Public API:
     LpBgm.start()        — kick off (게임 시작 핸들러에서 호출)
     LpBgm.stop()         — immediate stop, drop the audio handle
     LpBgm.toggle()       — flip mute, returns new muted state
     LpBgm.setMuted(bool) — explicit mute (persisted to localStorage)
     LpBgm.isMuted()      — current mute state
     LpBgm.setVolume(0–1) — runtime volume override (default 0.3)
     LpBgm._state()       — diagnostic snapshot
*/
(function(){
  'use strict';
  if(window.LpBgm)return;

  /* Skip games whose pages already wire their own audio engine. */
  var SKIP_GAMES={
    'car-racing':true,
    'dodge':true,
    'tetris':true,    /* 3-tier dynamic BGM tied to stack height */
    'balloon':true    /* 단일 트랙 + 위험도 볼륨 스웰 + 벌칙 징글 자체 엔진 */
  };

  /* Detect game from URL. Lobby + home + blog → no BGM. */
  var pathMatch=location.pathname.match(/^\/games\/([^\/]+)\/?/);
  if(!pathMatch)return;
  var gameId=pathMatch[1];
  if(SKIP_GAMES[gameId])return;

  /* 10dB below typical 1.0 SFX peak. Games with quieter SFX can call
     LpBgm.setVolume to scale further down at runtime. */
  var DEFAULT_VOLUME=0.3;
  var MAX_TRACKS=4;
  var TRACK_BASE='/assets/bgm/'+gameId+'/track';
  var MUTE_KEY='lp_bgm_muted';

  var audio=null;
  var started=false;            /* true only after play() actually started */
  var startRequested=false;     /* true once a game asked for BGM (게임 시작) */
  var currentTrackIdx=-1;
  var muted=(function(){
    try{return localStorage.getItem(MUTE_KEY)==='1'}catch(_){return false}
  })();
  var userVolume=DEFAULT_VOLUME;

  /* As we attempt plays, we learn which track indexes (1..MAX) actually
     exist on the server and which don't. This avoids retrying the same
     missing index over and over and lets pickRandomIdx avoid known
     404s for subsequent picks. */
  var knownExisting={};   /* {idx:true} */
  var knownMissing={};    /* {idx:true} */
  var attemptInFlight=false;

  function isExisting(i){return !!knownExisting[i]}
  function isMissing(i){return !!knownMissing[i]}

  function pickRandomIdx(){
    /* Build candidate list — every index 1..MAX_TRACKS that isn't
       confirmed missing. Filter out the current to avoid immediate
       repeats. If only the current is left (single-track game), play
       it again rather than nothing. */
    var all=[];
    for(var i=1;i<=MAX_TRACKS;i++){
      if(!isMissing(i))all.push(i);
    }
    if(all.length===0)return -1;
    var filtered=[];
    for(var j=0;j<all.length;j++){
      if(all[j]!==currentTrackIdx)filtered.push(all[j]);
    }
    if(filtered.length>0){
      return filtered[Math.floor(Math.random()*filtered.length)];
    }
    return all[0];
  }

  function tryPlayIdx(idx){
    if(idx<=0||idx>MAX_TRACKS){
      try{console.log('[LpBgm] no playable tracks for '+gameId)}catch(_){}
      attemptInFlight=false;
      return;
    }
    var url=TRACK_BASE+idx+'.mp3';
    /* Tear down any previous audio so the listeners on it don't fire
       after we've moved on. Mobile Safari has been observed to keep
       a paused element in a half-loaded state if you don't .load()
       reset, which then leaks bytes on the next switch. */
    if(audio){
      try{audio.pause();audio.src='';audio.load()}catch(_){}
      audio=null;
    }
    audio=new Audio(url);
    audio.volume=muted?0:userVolume;
    audio.preload='auto';
    var resolved=false;
    /* 404 / decode error / cors → bump this index into the missing
       set and try the next. */
    audio.addEventListener('error',function(){
      if(resolved)return;
      resolved=true;
      knownMissing[idx]=true;
      try{console.log('[LpBgm] track missing or invalid: '+url)}catch(_){}
      tryPlayIdx(pickRandomIdx());
    },{once:true});
    /* End of track → seamless switch to the next random one. The
       'ended' listener stays for the lifetime of this audio element;
       no {once:true} because we want to be ready every loop. (We
       tear down audio entirely when stop() runs, removing it then.) */
    audio.addEventListener('ended',function(){
      tryPlayIdx(pickRandomIdx());
    });
    /* Note we call .play() SYNCHRONOUSLY inside whatever caller
       reached us — this is the whole point of the speculative-play
       design. If we're inside DOMContentLoaded or a click handler,
       browsers grant autoplay; otherwise they reject and the
       first-interaction fallback retries. */
    var p=audio.play();
    if(p&&p.then){
      p.then(function(){
        if(resolved)return;
        resolved=true;
        started=true;
        attemptInFlight=false;
        currentTrackIdx=idx;
        knownExisting[idx]=true;
        try{console.log('[LpBgm] playing '+url)}catch(_){}
      }).catch(function(err){
        if(resolved)return;
        /* NotAllowedError = autoplay block. NotSupportedError /
           AbortError = something else (decode, etc). For autoplay
           block we leave started=false and let the first-interaction
           handler retry. For decode errors we mark this index missing
           and move on (the 'error' event usually fires too, but not
           on every browser). */
        var name=err&&err.name||'';
        if(name==='NotAllowedError'){
          attemptInFlight=false;
          try{console.log('[LpBgm] autoplay blocked — will retry on first user gesture')}catch(_){}
        }else{
          resolved=true;
          knownMissing[idx]=true;
          try{console.log('[LpBgm] play rejected ('+name+'): '+url)}catch(_){}
          tryPlayIdx(pickRandomIdx());
        }
      });
    }else{
      /* Pre-Promise browser (very old). Optimistically assume started. */
      started=true;
      attemptInFlight=false;
      currentTrackIdx=idx;
      knownExisting[idx]=true;
    }
  }

  function start(){
    startRequested=true;
    if(started||muted||attemptInFlight)return;
    attemptInFlight=true;
    tryPlayIdx(pickRandomIdx());
  }

  function stop(){
    started=false;
    startRequested=false;
    attemptInFlight=false;
    if(audio){
      try{audio.pause();audio.src='';audio.load()}catch(_){}
      audio=null;
    }
    currentTrackIdx=-1;
  }

  function setMuted(m){
    muted=!!m;
    try{localStorage.setItem(MUTE_KEY,muted?'1':'0')}catch(_){}
    if(audio)audio.volume=muted?0:userVolume;
  }

  function setVolume(v){
    var nv=Number(v);
    if(!isFinite(nv))return;
    userVolume=Math.max(0,Math.min(1,nv));
    if(audio&&!muted)audio.volume=userVolume;
  }

  function isMuted(){return muted}

  function toggle(){
    setMuted(!muted);
    if(!muted&&!started&&startRequested)start();
    return muted;
  }

  /* 게임 시작 전에 이 모듈이 아직 로드 안 됐을 수 있다 (siteFooter 가
     defer 주입). 그 경우 게임 쪽 시작 핸들러는 window.__lpBgmWanted=true
     플래그만 세워 두고, 여기서 로드 직후 이어받아 start() 한다.
     사용자가 방금 시작 버튼을 눌렀으므로 sticky activation 으로
     play() 가 대부분 허용되고, 막히면 아래 interaction 폴백이 잡는다. */
  if(window.__lpBgmWanted){
    start();
  }

  /* Gesture-context retry. 게임이 start() 를 요청했지만 브라우저가
     autoplay 를 막았을 때 (NotAllowedError), 다음 터치/클릭/키 입력의
     SYNC 콜스택 안에서 재시도한다. startRequested 가 켜지기 전에는
     아무것도 하지 않는다 — 페이지 진입만으로 음악이 나오면 안 된다.
     Capture phase + passive — 게임 버튼이 소비하는 제스처를 그대로
     공유, preventDefault/stopPropagation 없음. */
  function onInteraction(){
    if(started){
      try{document.removeEventListener('touchstart',onInteraction,true)}catch(_){}
      try{document.removeEventListener('click',onInteraction,true)}catch(_){}
      try{document.removeEventListener('keydown',onInteraction,true)}catch(_){}
      return;
    }
    if(startRequested&&!muted){
      /* SYNC inside this handler — the call stack reaches audio.play()
         while the user-gesture flag is still active in the browser. */
      start();
    }
  }
  document.addEventListener('touchstart',onInteraction,{capture:true,passive:true});
  document.addEventListener('click',onInteraction,true);
  document.addEventListener('keydown',onInteraction,true);

  /* Pause on tab-hide so battery doesn't drain when the user switches
     apps; resume on visible. We can call play() here because the user
     previously interacted on this tab, so sticky activation is intact. */
  document.addEventListener('visibilitychange',function(){
    if(!started||muted)return;
    if(document.hidden){
      if(audio)try{audio.pause()}catch(_){}
    }else{
      if(audio){
        var p=audio.play();
        if(p&&p.catch)p.catch(function(){});
      }
    }
  });

  window.addEventListener('beforeunload',stop);

  /* ── 표준 BGM 토글 버튼 (2026-08-20, 풍선 룰렛 프레임으로 통일) ──
     그동안 toggle() API 만 있고 이를 노출하는 UI 가 없어, lpBgm 구동
     게임 9종에서 사용자가 음악을 끌 방법이 없었다. 전체화면 버튼
     (top-left)의 우측 미러 자리에 38px 버튼을 놓는다. track1 존재를
     HEAD 로 확인한 뒤에만 표시 — 트랙 없는 게임에 죽은 버튼을 두지
     않는다 (HEAD 는 재생이 아니라 autoplay 제약과 무관하다). */
  var bgmBtn=null;
  function syncBgmBtn(){
    if(!bgmBtn)return;
    bgmBtn.textContent=muted?'🔇':'🔊';
    bgmBtn.classList.toggle('on',!muted);
  }
  function mountBgmBtn(){
    if(bgmBtn)return;
    var st=document.createElement('style');
    st.textContent=
      '.lp-bgm-btn{position:fixed;'
      +'top:calc(56px + env(safe-area-inset-top,0px));'
      +'right:calc(10px + env(safe-area-inset-right,0px));'
      +'z-index:9040;width:38px;height:38px;border-radius:11px;'
      +'border:1.5px solid rgba(255,255,255,.14);background:rgba(10,10,26,.55);'
      +'backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);'
      +'color:#fff;font-size:16px;cursor:pointer;padding:0;'
      +'display:flex;align-items:center;justify-content:center;'
      +'touch-action:manipulation;transition:border-color .2s,background .2s}'
      +'.lp-bgm-btn.on{border-color:rgba(255,230,109,.6);background:rgba(255,230,109,.14)}';
    document.head.appendChild(st);
    bgmBtn=document.createElement('button');
    bgmBtn.type='button';
    bgmBtn.className='lp-bgm-btn';
    bgmBtn.setAttribute('aria-label','BGM on/off');
    bgmBtn.addEventListener('click',function(){toggle();syncBgmBtn();});
    syncBgmBtn();
    (document.body||document.documentElement).appendChild(bgmBtn);
  }
  try{
    fetch(TRACK_BASE+'1.mp3',{method:'HEAD'}).then(function(r){
      if(r&&r.ok){
        if(document.body)mountBgmBtn();
        else document.addEventListener('DOMContentLoaded',mountBgmBtn);
      }
    }).catch(function(){});
  }catch(_){}

  window.LpBgm={
    start:start,
    stop:stop,
    setMuted:setMuted,
    isMuted:isMuted,
    setVolume:setVolume,
    toggle:toggle,
    _state:function(){
      return{
        gameId:gameId,
        started:started,
        startRequested:startRequested,
        muted:muted,
        currentTrackIdx:currentTrackIdx,
        knownExisting:Object.keys(knownExisting).map(Number),
        knownMissing:Object.keys(knownMissing).map(Number),
        volume:userVolume
      };
    }
  };
})();
