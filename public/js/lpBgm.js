/* lpBgm.js — random-shuffle background music for /games/* pages.
   ─────────────────────────────────────────────────────────────────
   Goal: BGM starts the moment the user selects a game (i.e. when the
   game page first paints), without a redundant tap. After that, plays
   one of /assets/bgm/<gameId>/track1.mp3 ... track4.mp3 at random;
   when that track ends, picks another (excluding current) forever.

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
     LpBgm.start()        — kick off (auto-runs on page load + first tap)
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
    'tetris':true     /* 3-tier dynamic BGM tied to stack height */
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
    if(started||muted||attemptInFlight)return;
    attemptInFlight=true;
    tryPlayIdx(pickRandomIdx());
  }

  function stop(){
    started=false;
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
    if(!muted&&!started)start();
    return muted;
  }

  /* Auto-start at the earliest possible moment. When the user clicks a
     game tile on /, navigates to /games/<id>/, and the page paints,
     we attempt play() right then. Modern browsers (Chrome 76+,
     Safari 14+, Firefox 66+) honor "sticky activation" — recent same-
     origin user input grants autoplay, so this typically Just Works.
     If the browser rejects (e.g. user came in via a fresh tab without
     prior interaction), the first-interaction listener below retries
     in proper gesture context. */
  function attemptAutoStart(){
    if(muted)return;
    start();
  }
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',attemptAutoStart);
  }else{
    /* Document already parsed; defer one tick so the surrounding
       siteFooter execution finishes first. */
    setTimeout(attemptAutoStart,0);
  }

  /* First-interaction fallback. Capture phase + passive — same gesture
     the game's own button consumes, no preventDefault, no
     stopPropagation. once:true via internal flag (not the option)
     because we manage removal explicitly so all three event names
     come down together. */
  var firstInteractionFired=false;
  function onFirstInteraction(){
    if(firstInteractionFired)return;
    firstInteractionFired=true;
    try{document.removeEventListener('touchstart',onFirstInteraction,true)}catch(_){}
    try{document.removeEventListener('click',onFirstInteraction,true)}catch(_){}
    try{document.removeEventListener('keydown',onFirstInteraction,true)}catch(_){}
    if(!muted&&!started){
      /* SYNC inside this handler — the call stack reaches audio.play()
         while the user-gesture flag is still active in the browser. */
      start();
    }
  }
  document.addEventListener('touchstart',onFirstInteraction,{capture:true,passive:true});
  document.addEventListener('click',onFirstInteraction,true);
  document.addEventListener('keydown',onFirstInteraction,true);

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
        muted:muted,
        currentTrackIdx:currentTrackIdx,
        knownExisting:Object.keys(knownExisting).map(Number),
        knownMissing:Object.keys(knownMissing).map(Number),
        volume:userVolume
      };
    }
  };
})();
