/* lpWakeLock.js — singleton Screen Wake Lock manager for live games.
   ─────────────────────────────────────────────────────────────────
   Goal: while a multiplayer game is in active play, keep the device
   screen from dimming/sleeping. Without this, the host's phone locks
   mid-question/-round/-spin and the whole room stalls; for guests, a
   sleeping screen means no broadcasts get rendered until they manually
   wake the phone again.

   API:
     LpWakeLock.acquire(reason?)  — start holding the lock. Reason is
                                    a short string for debug logs.
     LpWakeLock.release()         — drop the lock and stop holding it.
     LpWakeLock.isWanted()        — has the page asked for a lock?
     LpWakeLock.isHeld()          — is the lock currently held by the
                                    OS? (false during background.)

   Behavior:
     - Idempotent: acquire() while already wanted is a no-op.
     - The Screen Wake Lock API auto-releases the lock when the tab
       loses visibility. We listen for visibilitychange→visible and
       re-acquire if a lock was wanted, so the user gets a continuous
       experience across tab-switch/return.
     - Best-effort: where the API is unsupported (Android Chrome <84,
       iOS Safari <16.4, all desktop Firefox until recently), the
       calls are no-ops. Game-level visibility catch-up handlers
       (LpPhaseTimer + per-game logic) cover the rest.

   Also dispatches a single `beforeunload` release in case the game
   navigated away without explicitly releasing — the OS would clean
   it up anyway, but releasing here is faster and avoids a brief
   over-hold while the next page loads. */
(function(){
  'use strict';
  if(window.LpWakeLock)return;

  var lock=null;
  var wanted=false;
  var lastReason='';

  function _log(msg){try{console.log('[LpWakeLock] '+msg)}catch(_){}}

  function isSupported(){return typeof navigator!=='undefined'&&'wakeLock'in navigator}

  async function acquire(reason){
    wanted=true;
    if(reason)lastReason=reason;
    if(!isSupported())return;
    if(lock)return;
    /* Some browsers reject a request while the document is hidden —
       we just wait for the next visibilitychange→visible to retry,
       which is exactly what _onVisibilityChange already does. */
    if(typeof document!=='undefined'&&document.hidden)return;
    try{
      lock=await navigator.wakeLock.request('screen');
      lock.addEventListener&&lock.addEventListener('release',function(){
        /* OS-initiated release (background tab, system battery saver
           kicked in, etc). Drop our handle but keep `wanted=true` so
           the next visibility-restore re-acquires. */
        lock=null;
      });
      _log('acquired ('+lastReason+')');
    }catch(e){
      /* NotAllowedError = page not visible / user gesture missing.
         Just keep wanted=true — visibility-restore handler will retry. */
      _log('acquire failed: '+(e&&e.name||'')+' '+(e&&e.message||''));
    }
  }

  function release(){
    wanted=false;
    if(lock){
      try{lock.release()}catch(_){}
      lock=null;
      _log('released ('+lastReason+')');
    }
    lastReason='';
  }

  function isWanted(){return wanted}
  function isHeld(){return !!lock}

  /* Auto re-acquire on visibility return. The browser drops the lock
     automatically when the tab is hidden, so this is the canonical
     re-arm point. Idempotent: if the lock is already held (some
     browsers don't actually drop it), the inner check on `lock` in
     acquire() short-circuits. */
  function _onVisibilityChange(){
    if(document.hidden)return;
    if(wanted&&!lock)acquire(lastReason);
  }
  if(typeof document!=='undefined'){
    document.addEventListener('visibilitychange',_onVisibilityChange);
  }

  /* Belt-and-suspenders cleanup. The OS releases on tab close anyway,
     but releasing here means the device drops out of "screen-on" mode
     a beat earlier as the user transitions away. */
  if(typeof window!=='undefined'){
    window.addEventListener('beforeunload',release);
  }

  window.LpWakeLock={
    acquire:acquire,
    release:release,
    isWanted:isWanted,
    isHeld:isHeld,
    isSupported:isSupported
  };
})();
