/* lpPhaseTimer.js — wall-clock phase scheduler with auto-catch-up.
   ─────────────────────────────────────────────────────────────────
   Replaces plain `setTimeout(fire, durMs)` for game phase transitions
   that the host (or the local solo player) drives. Mobile Chrome
   throttles setTimeout on a backgrounded tab to ~1/min after the
   first minute, which means a host who locks their phone or switches
   apps mid-question/-round/-spin would stall the whole room until
   they return AND wait out the throttled timer.

   This module records BOTH the setTimeout handle AND a Date.now()
   wall-clock deadline. On `visibilitychange→visible`, any phase
   whose deadline has already passed is force-fired immediately
   (clearing the throttled timer first to prevent double-fire).

   Single-slot semantics: most games have only one active phase
   at a time (e.g. "show question for 5s, then reveal"). This
   module assumes the same. If a game DOES need parallel phases,
   it can use `LpPhaseTimer.create()` to mint independent slots.

   API:
     LpPhaseTimer.schedule(durMs, fire)  — schedule on the default
                                           singleton slot. Replaces
                                           any existing pending phase.
     LpPhaseTimer.clear()                — cancel pending phase.
     LpPhaseTimer.catchUp()              — force-fire if deadline
                                           passed. Called automatically
                                           on visibilitychange→visible.
     LpPhaseTimer.create(name?)          — mint a new independent slot
                                           for games that need parallel
                                           timers. Returns same shape
                                           as the singleton API.

   Philosophy: this is a "timer that survives backgrounding" — it does
   NOT try to keep the game running while hidden. The OS can still
   suspend the tab fully. What it guarantees is: when the user returns,
   the game state catches up to where it should be NOW, not where it
   was when the tab went hidden. */
(function(){
  'use strict';
  if(window.LpPhaseTimer)return;

  function _log(msg){try{console.log('[LpPhaseTimer] '+msg)}catch(_){}}

  function _makeSlot(name){
    name=name||'default';
    /* {deadline, fire, timerId} | null */
    var slot=null;

    function schedule(durMs,fire){
      if(typeof fire!=='function')return;
      durMs=Math.max(0,Math.floor(durMs)||0);
      if(slot){try{clearTimeout(slot.timerId)}catch(_){}}
      var deadline=Date.now()+durMs;
      var timerId=setTimeout(function(){
        if(slot&&slot.timerId===timerId)slot=null;
        try{fire()}catch(e){try{console.error(e)}catch(_){}}
      },durMs);
      slot={deadline:deadline,fire:fire,timerId:timerId};
    }
    function clear(){
      if(slot){
        try{clearTimeout(slot.timerId)}catch(_){}
        slot=null;
      }
    }
    function catchUp(){
      if(!slot)return false;
      if(Date.now()<slot.deadline)return false;
      var fn=slot.fire;
      try{clearTimeout(slot.timerId)}catch(_){}
      slot=null;
      _log('catch-up fired ('+name+')');
      try{fn()}catch(e){try{console.error(e)}catch(_){}}
      return true;
    }
    function pending(){return !!slot}
    function remainingMs(){return slot?Math.max(0,slot.deadline-Date.now()):0}

    return {
      schedule:schedule,
      clear:clear,
      catchUp:catchUp,
      pending:pending,
      remainingMs:remainingMs
    };
  }

  /* Track every slot we ever minted so the visibility handler can
     iterate them all. Includes the default singleton. */
  var _allSlots=[];
  function _trackSlot(slot){_allSlots.push(slot);return slot}

  var _default=_trackSlot(_makeSlot('default'));

  function _onVisibilityChange(){
    if(document.hidden)return;
    /* Iterate a copy in case a fired callback creates a new slot. */
    var slots=_allSlots.slice();
    for(var i=0;i<slots.length;i++){
      try{slots[i].catchUp()}catch(_){}
    }
  }
  if(typeof document!=='undefined'){
    document.addEventListener('visibilitychange',_onVisibilityChange);
  }

  window.LpPhaseTimer={
    schedule:_default.schedule,
    clear:_default.clear,
    catchUp:_default.catchUp,
    pending:_default.pending,
    remainingMs:_default.remainingMs,
    create:function(name){return _trackSlot(_makeSlot(name))}
  };
})();
