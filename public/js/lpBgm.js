/* lpBgm.js — random-shuffle background music for /games/* pages.
   ─────────────────────────────────────────────────────────────────
   Concept:
     Each game folder under /assets/bgm/<gameId>/ holds 1–4 mp3 tracks
     named track1.mp3 ... track4.mp3. On first user interaction, the
     module discovers which of those files actually exist (HEAD probe)
     and starts playing one at random. When that track ends, picks
     another at random (excluding the just-played one), repeats forever
     until the page unloads or the user mutes.

     Volume: BGM target is 10dB below SFX. Most games' SFX peaks near
     1.0, so BGM rests at 0.3 (10^(-10/20) ≈ 0.316). Per-game pages
     can fine-tune via LpBgm.setVolume(0.x).

     Skipped games: car-racing and dodge already manage their own BGM
     via in-page audio engines — overlapping playlists would just clash.

   Public API:
     LpBgm.start()        — manually kick off (also auto-runs on first tap)
     LpBgm.stop()         — immediate stop, drop the audio handle
     LpBgm.toggle()       — flip mute, returns new muted state
     LpBgm.setMuted(bool) — explicit mute (persisted to localStorage)
     LpBgm.isMuted()      — current mute state
     LpBgm.setVolume(0–1) — runtime volume override
     LpBgm._state()       — diagnostic snapshot

   Wiring per-game (optional):
     If a game has its own "🔊 BGM ON / OFF" button, call
     LpBgm.toggle() from its onclick. The first call starts BGM (after
     interaction unlock), subsequent calls flip mute. Mute is shared
     across game pages via localStorage.
*/
(function(){
  'use strict';
  if(window.LpBgm)return;

  /* Skip games whose pages already wire their own audio engine. They
     pick tracks via game-specific logic (e.g. car-racing's AudioEngine
     starts BGM after the countdown). Adding lpBgm on top would create
     overlapping concurrent streams. */
  var SKIP_GAMES={
    'car-racing':true,
    'dodge':true
  };

  /* Detect game from URL. Lobby + home + blog → no BGM. */
  var pathMatch=location.pathname.match(/^\/games\/([^\/]+)\/?/);
  if(!pathMatch)return;
  var gameId=pathMatch[1];
  if(SKIP_GAMES[gameId])return;

  /* 10dB below the standard 1.0 SFX peak. Games whose SFX runs
     softer can call LpBgm.setVolume to scale down further. */
  var DEFAULT_VOLUME=0.3;
  var MAX_TRACKS=4;
  var TRACK_BASE='/assets/bgm/'+gameId+'/track';
  /* Persisted across all game pages — mute on roulette stays muted on
     lotto. Distinct from per-game SFX toggles (those usually have their
     own keys). */
  var MUTE_KEY='lp_bgm_muted';

  var audio=null;
  var started=false;
  var startInflight=false;
  var currentTrackIdx=-1;
  var tracks=[];
  var muted=(function(){
    try{return localStorage.getItem(MUTE_KEY)==='1'}catch(_){return false}
  })();
  var userVolume=DEFAULT_VOLUME;

  /* HEAD-probe the four candidate filenames. Cloudflare Pages serves
     a 404 quickly for missing assets so this is cheap (~50–150ms total
     on cold cache). Each game can ship anywhere from 1 to MAX_TRACKS
     mp3s — the playlist is whatever's actually there. */
  function discoverTracks(){
    var promises=[];
    for(var i=1;i<=MAX_TRACKS;i++){
      (function(idx){
        var url=TRACK_BASE+idx+'.mp3';
        promises.push(
          fetch(url,{method:'HEAD',cache:'no-cache'})
            .then(function(r){return r.ok?url:null})
            .catch(function(){return null})
        );
      })(i);
    }
    return Promise.all(promises).then(function(results){
      return results.filter(function(u){return !!u});
    });
  }

  function pickRandomTrackIdx(){
    if(tracks.length===0)return -1;
    if(tracks.length===1)return 0;
    /* Avoid immediate repeats. Two-track lists collapse to strict
       alternation; longer lists shuffle freely. */
    var idx;
    do{idx=Math.floor(Math.random()*tracks.length)}
    while(idx===currentTrackIdx);
    return idx;
  }

  function playNext(){
    if(!tracks.length)return;
    var idx=pickRandomTrackIdx();
    currentTrackIdx=idx;
    /* Tear down the previous Audio element fully — leaving a paused
       element with a stale src has caused stuck-audio reports on
       Mobile Safari and old Samsung Internet. */
    if(audio){
      try{audio.pause();audio.src='';audio.load()}catch(_){}
      audio=null;
    }
    audio=new Audio(tracks[idx]);
    audio.volume=muted?0:userVolume;
    audio.preload='auto';
    audio.addEventListener('ended',playNext);
    /* Some browsers emit `error` if the file is corrupt — skip to next
       track instead of stalling silently. */
    audio.addEventListener('error',function(){
      try{console.warn('[LpBgm] track failed, skipping: '+tracks[idx])}catch(_){}
      setTimeout(playNext,200);
    });
    var p=audio.play();
    if(p&&p.catch)p.catch(function(){
      /* Autoplay blocked — first-interaction handler hasn't fired yet.
         The handler will retry once the user taps. Safe to no-op here. */
    });
  }

  function start(){
    if(started||startInflight)return Promise.resolve();
    startInflight=true;
    return (tracks.length?Promise.resolve(tracks):discoverTracks().then(function(found){
      tracks=found;
      return found;
    })).then(function(found){
      startInflight=false;
      if(!found.length){
        try{console.log('[LpBgm] no tracks found for '+gameId+' (looking under '+TRACK_BASE+'1..4.mp3)')}catch(_){}
        return;
      }
      started=true;
      playNext();
    }).catch(function(){
      startInflight=false;
    });
  }

  function stop(){
    started=false;
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

  /* Auto-start on first user gesture. Without a user-initiated play,
     browsers (Chrome 71+, Safari 11+, Firefox 66+) silently block
     Audio.play(). We listen in CAPTURE phase with passive:true so the
     same touch that the game's own button consumes also kicks BGM —
     no interference, no preventDefault. once:true ensures we don't
     keep firing on every interaction. */
  var firstInteractionFired=false;
  function onFirstInteraction(){
    if(firstInteractionFired)return;
    firstInteractionFired=true;
    try{document.removeEventListener('touchstart',onFirstInteraction,true)}catch(_){}
    try{document.removeEventListener('click',onFirstInteraction,true)}catch(_){}
    try{document.removeEventListener('keydown',onFirstInteraction,true)}catch(_){}
    if(!muted)start();
  }
  document.addEventListener('touchstart',onFirstInteraction,{capture:true,passive:true});
  document.addEventListener('click',onFirstInteraction,true);
  document.addEventListener('keydown',onFirstInteraction,true);

  /* Pause on tab-hide so battery doesn't drain when the user
     switches apps; resume on visible. Don't auto-start here if the
     user never triggered first-interaction (browser would still
     reject play). */
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

  /* Page navigation tearing down the audio element saves a few KB of
     RAM on the unload tick. Browsers do this anyway but the explicit
     stop is safer on iOS Safari which occasionally leaks. */
  window.addEventListener('beforeunload',stop);

  window.LpBgm={
    start:start,
    stop:stop,
    setMuted:setMuted,
    isMuted:isMuted,
    setVolume:setVolume,
    toggle:toggle,
    _state:function(){
      return{gameId:gameId,started:started,muted:muted,currentTrackIdx:currentTrackIdx,tracks:tracks.slice()}
    }
  };
})();
