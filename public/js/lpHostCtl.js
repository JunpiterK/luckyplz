/*
  Lucky Please — Host control module.

  Single-file, zero-dependency, per-game plugin that renders the
  host's in-game control bar (pause / end) and the matching overlays
  (paused / ended). Designed as a plug-in for the multiplayer runtime
  in /js/lpRoom.js.

  Design priorities (in order):
    1. Correctness under flaky mobile networks — every broadcast is
       idempotent at the receiver; double-clicks are deduplicated at
       the source.
    2. Zero frame drops during pause/end transitions: CSS-only
       animations, no layout thrash, no inline styles that force
       reflow per tick.
    3. Zero per-game boilerplate. A game declares 2–3 callbacks and
       the module handles DOM, CSS, event protocol, guest sync, and
       the ended-view. No HTML/CSS duplication in each game file.
    4. Safe to call twice. A second install() destroys the previous
       instance cleanly — host transfer between pages works.
    5. Stacking-safe. Above lpRoom.js status bar (9000) / guest panel
       (8999) so the controls are always reachable on mobile.

  Public API:

    const ctl = LpHostCtl.install({
      role:      'host' | 'guest',       // required
      room:      <lpRoom host or guest>, // required

      // Feature toggles. canPause/canEnd accept bool OR () => bool.
      // The function form is queried at each click — useful for
      // "pause only valid during the question view" kind of rules.
      canPause:  true,
      canEnd:    true,
      skipConfirm: false,                // skip the end() confirm() dialog

      texts:     { ... overrides ... },

      // Host-only hooks. Called BEFORE the broadcast is sent, so
      // local UI updates without waiting on the network. May return
      // an object of extra fields to merge into the broadcast payload.
      onPause:    (extra) => ({...} | void),
      onResume:   (extra) => ({...} | void),
      onEnd:      (extra) => void,

      // Guest-only hooks. Called AFTER the module has handled its
      // own overlay, so per-game side-effects (timer skew, SFX, etc)
      // run once the UI is in the right state.
      onHostPaused:  (payload) => void,
      onHostResumed: (payload) => void,
      onHostEnded:   (payload) => void
    });

  Controller methods:
    ctl.show() / ctl.hide()        — manual visibility toggle
    ctl.pause(extra) / resume / end — programmatic (same as button click)
    ctl.setPausable(bool)          — toggle pause button visibility
    ctl.setEndable(bool)
    ctl.isPaused() / ctl.isEnded() — state queries
    ctl.hydratePausedState(extra)  — for a late-joining guest whose
                                     snapshot says "host is paused",
                                     pops the overlay without firing
                                     a local pause event.
    ctl.destroy()                  — removes DOM + listeners

  Broadcast protocol (host → guest):
    host:paused   { t: <ms>, ...gameExtra }
    host:resumed  { t: <ms>, ...gameExtra }
    host:ended    { t: <ms>, reason: 'host_ended', ...gameExtra }

  Every event carries a wall-clock timestamp so guests with drifted
  clocks can still compute meaningful "how long have we been paused"
  values. The module never throws if the underlying send fails — it
  logs to console.warn and moves on, trusting lpRoom.js's own
  heartbeat to surface a disconnect to the user.
*/
(function () {
  'use strict';
  if (window.LpHostCtl) return;

  const STYLE_ID = 'lp-host-ctl-styles';

  /* Stacking policy:
       lp-hc       9100  — above lpRoom status bar (9000) + guest panel (8999)
       lp-hc-povl  9200  — covers status bar while paused
       lp-hc-eovl  9300  — covers everything on end (no escape) */
  const Z_CTL   = 9100;
  const Z_PAUSE = 9200;
  const Z_ENDED = 9300;

  const DEFAULT_TEXTS = {
    pause:          '일시정지',
    resume:         '재개',
    end:            '게임 종료',
    endConfirm:     '정말 게임을 종료할까요?\n모든 참가자가 방에서 나갑니다.',
    pausedTitle:    '일시정지 중',
    hostPausedSub:  '참가자 전원의 화면이 멈춰있어요',
    guestPausedSub: '호스트가 잠시 멈췄어요',
    endedTitle:     '게임 종료',
    endedHostSub:   '게임을 종료했어요. 참가자는 모두 방에서 나갔어요.',
    endedGuestSub:  '호스트가 게임을 종료했어요. 파티는 해제되었습니다.',
    homeBtn:        '🏠 홈으로'
  };

  function esc(s){
    return String(s == null ? '' : s)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function _ensureStyles(){
    if (document.getElementById(STYLE_ID)) return;
    const css = [
      /* Bar */
      `.lp-hc{position:fixed;top:58px;right:10px;z-index:${Z_CTL};display:none;gap:8px;pointer-events:auto}`,
      `.lp-hc.on{display:flex}`,
      `.lp-hc-btn{min-width:44px;height:44px;padding:0 12px;border-radius:999px;cursor:pointer;background:rgba(10,10,26,.88);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.18);color:#fff;font-family:inherit;font-size:1.02em;font-weight:900;display:inline-flex;align-items:center;justify-content:center;box-shadow:0 6px 14px -6px rgba(0,0,0,.6);transition:transform .08s,filter .2s,opacity .2s}`,
      `.lp-hc-btn:active{transform:scale(.94)}`,
      `.lp-hc-btn:hover{filter:brightness(1.15)}`,
      `.lp-hc-btn:disabled{opacity:.35;cursor:not-allowed;pointer-events:none}`,
      `.lp-hc-pause{color:#FFE066;border-color:rgba(255,230,109,.45)}`,
      `.lp-hc-end{color:#FF6B8B;border-color:rgba(255,107,139,.45)}`,

      /* Pause overlay */
      `.lp-hc-povl{position:fixed;inset:0;z-index:${Z_PAUSE};padding:20px;background:rgba(10,10,26,.82);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);display:none;align-items:center;justify-content:center;animation:lpHcFade .2s ease-out;font-family:'Noto Sans KR',sans-serif;color:#fff}`,
      `.lp-hc-povl.on{display:flex}`,
      `.lp-hc-pcard{background:linear-gradient(165deg,rgba(30,30,50,.95),rgba(16,16,32,.98));border:1px solid rgba(255,230,109,.3);border-radius:18px;padding:32px 34px;max-width:400px;width:100%;text-align:center;box-shadow:0 24px 60px rgba(0,0,0,.55)}`,
      `.lp-hc-pico{font-size:3.8em;margin-bottom:10px;line-height:1;animation:lpHcPulse 1.4s ease-in-out infinite alternate}`,
      `.lp-hc-ptitle{font-family:'Orbitron','Noto Sans KR',sans-serif;font-size:1.35em;font-weight:900;color:#FFE066;margin-bottom:6px;letter-spacing:.12em}`,
      `.lp-hc-psub{font-size:.92em;color:rgba(255,255,255,.7);line-height:1.5}`,
      `.lp-hc-presume{margin-top:18px;padding:12px 30px;border-radius:999px;border:0;background:linear-gradient(135deg,#FFE066,#FFB84D);color:#0a0a1a;font-family:'Orbitron','Noto Sans KR',sans-serif;font-weight:900;font-size:1em;letter-spacing:.08em;cursor:pointer;box-shadow:0 10px 22px -6px rgba(255,230,109,.45);transition:transform .08s,filter .2s}`,
      `.lp-hc-presume:active{transform:scale(.96)}`,
      `.lp-hc-presume:hover{filter:brightness(1.08)}`,

      /* Ended overlay */
      `.lp-hc-eovl{position:fixed;inset:0;z-index:${Z_ENDED};padding:20px;background:rgba(5,5,15,.95);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);display:none;align-items:center;justify-content:center;animation:lpHcFade .22s ease-out;font-family:'Noto Sans KR',sans-serif;color:#fff}`,
      `.lp-hc-eovl.on{display:flex}`,
      `.lp-hc-ecard{background:linear-gradient(165deg,rgba(30,30,50,.95),rgba(16,16,32,.98));border:1px solid rgba(255,107,139,.3);border-radius:20px;padding:36px 32px;max-width:420px;width:100%;text-align:center;box-shadow:0 30px 70px rgba(0,0,0,.65)}`,
      `.lp-hc-eico{font-size:3.6em;margin-bottom:10px;line-height:1;color:#FF6B8B}`,
      `.lp-hc-etitle{font-family:'Orbitron','Noto Sans KR',sans-serif;font-size:1.5em;font-weight:900;color:#FF6B8B;margin-bottom:8px;letter-spacing:.1em}`,
      `.lp-hc-esub{font-size:.95em;color:rgba(255,255,255,.75);line-height:1.55;margin-bottom:24px}`,
      `.lp-hc-ehome{padding:14px 36px;border-radius:999px;border:0;background:linear-gradient(135deg,#FFE066,#FF6B8B);color:#0a0a1a;font-family:'Orbitron','Noto Sans KR',sans-serif;font-weight:900;font-size:1em;letter-spacing:.08em;cursor:pointer;box-shadow:0 10px 24px -8px rgba(255,107,139,.5);transition:transform .08s,filter .2s}`,
      `.lp-hc-ehome:active{transform:scale(.96)}`,
      `.lp-hc-ehome:hover{filter:brightness(1.08)}`,

      `@keyframes lpHcFade{from{opacity:0}to{opacity:1}}`,
      `@keyframes lpHcPulse{from{transform:scale(1)}to{transform:scale(1.08)}}`,

      /* Landscape phones: topbar is often hidden, don't leave a dead strip. */
      `@media(max-height:520px){.lp-hc{top:10px}}`
    ].join('\n');
    const el = document.createElement('style');
    el.id = STYLE_ID;
    el.textContent = css;
    document.head.appendChild(el);
  }

  /* One live instance at a time. Host-transfer pages re-install; the
     previous controller's DOM is torn down here before the new one is
     built so we never end up with two overlapping bars. */
  let _current = null;

  function install(opts){
    _ensureStyles();
    if (_current) {
      try { _current.destroy(); } catch(_){}
      _current = null;
    }

    opts = opts || {};
    const role  = opts.role === 'guest' ? 'guest' : 'host';
    const room  = opts.room || null;
    const texts = Object.assign({}, DEFAULT_TEXTS, opts.texts || {});

    let endable = opts.canEnd !== false;
    let isPaused = false;
    let ended = false;
    let pauseInflight = false;

    /* Resolve a feature toggle that may be a literal bool or a
       zero-arg function. Functions are re-evaluated on each click so
       a game can express "pause only in the question view" without
       having to notify the module on every view change. */
    function pausableNow(){
      const v = opts.canPause;
      if (typeof v === 'function') {
        try { return !!v(); } catch(_) { return false; }
      }
      return v !== false;
    }

    /* ---- DOM build ---- */
    const bar = document.createElement('div');
    bar.className = 'lp-hc';
    bar.innerHTML =
      `<button class="lp-hc-btn lp-hc-pause" type="button" aria-label="${esc(texts.pause)}" title="${esc(texts.pause)}">⏸</button>` +
      `<button class="lp-hc-btn lp-hc-end" type="button" aria-label="${esc(texts.end)}" title="${esc(texts.end)}">⏹</button>`;
    document.body.appendChild(bar);
    const btnPause = bar.querySelector('.lp-hc-pause');
    const btnEnd   = bar.querySelector('.lp-hc-end');

    /* canPause:false hard-hides the button so games without pause
       semantics (roulette, team reveal) don't show it at all. The
       function form keeps the button visible but may reject a click. */
    if (opts.canPause === false) btnPause.style.display = 'none';
    if (!endable) btnEnd.style.display = 'none';

    const povl = document.createElement('div');
    povl.className = 'lp-hc-povl';
    povl.innerHTML =
      `<div class="lp-hc-pcard">` +
        `<div class="lp-hc-pico">⏸</div>` +
        `<div class="lp-hc-ptitle">${esc(texts.pausedTitle)}</div>` +
        `<div class="lp-hc-psub" data-role="sub"></div>` +
        `<button class="lp-hc-presume" type="button" style="display:none">▶ ${esc(texts.resume)}</button>` +
      `</div>`;
    document.body.appendChild(povl);
    const povlSub   = povl.querySelector('[data-role="sub"]');
    const btnResume = povl.querySelector('.lp-hc-presume');

    const eovl = document.createElement('div');
    eovl.className = 'lp-hc-eovl';
    eovl.innerHTML =
      `<div class="lp-hc-ecard">` +
        `<div class="lp-hc-eico">⏹</div>` +
        `<div class="lp-hc-etitle">${esc(texts.endedTitle)}</div>` +
        `<div class="lp-hc-esub" data-role="sub"></div>` +
        `<button class="lp-hc-ehome" type="button">${esc(texts.homeBtn)}</button>` +
      `</div>`;
    document.body.appendChild(eovl);
    const eovlSub = eovl.querySelector('[data-role="sub"]');
    const btnHome = eovl.querySelector('.lp-hc-ehome');
    btnHome.addEventListener('click', () => {
      try { location.href = opts.homeUrl || '/'; } catch(_){}
    });

    /* ---- Visibility helpers ---- */
    function show(){ if (!ended) bar.classList.add('on'); }
    function hide(){ bar.classList.remove('on'); }
    function setPausable(b){
      /* Literal override only; if opts.canPause is a function, the
         function stays the source of truth. */
      if (typeof opts.canPause !== 'function') opts.canPause = !!b;
      btnPause.style.display = (opts.canPause === false) ? 'none' : '';
    }
    function setEndable(b){
      endable = !!b;
      btnEnd.style.display = endable ? '' : 'none';
    }
    function showPauseOvl(isHost){
      povlSub.textContent = isHost ? texts.hostPausedSub : texts.guestPausedSub;
      btnResume.style.display = isHost ? 'inline-flex' : 'none';
      povl.classList.add('on');
    }
    function hidePauseOvl(){ povl.classList.remove('on'); }
    function showEndedOvl(isHost){
      eovlSub.textContent = isHost ? texts.endedHostSub : texts.endedGuestSub;
      bar.classList.remove('on');
      povl.classList.remove('on');
      eovl.classList.add('on');
      ended = true;
    }

    /* ---- Safe broadcast wrapper ---- */
    function safeBroadcast(event, payload){
      if (!room || typeof room.broadcast !== 'function') return;
      try { room.broadcast(event, payload || {}); }
      catch(e) { console.warn('[lpHostCtl] broadcast ' + event + ' failed:', e && e.message); }
    }

    /* ---- Host actions ---- */
    async function doPause(extra){
      if (role !== 'host' || ended || isPaused || pauseInflight) return;
      if (!pausableNow()) return;
      pauseInflight = true;
      btnPause.disabled = true;
      try {
        isPaused = true;
        let userExtra = null;
        if (typeof opts.onPause === 'function') {
          try { userExtra = opts.onPause(extra || {}) || null; }
          catch(e) { console.warn('[lpHostCtl] onPause threw:', e); }
        }
        showPauseOvl(true);
        const payload = Object.assign({ t: Date.now() }, extra || {}, userExtra || {});
        safeBroadcast('host:paused', payload);
      } finally {
        pauseInflight = false;
        btnPause.disabled = false;
      }
    }

    async function doResume(extra){
      if (role !== 'host' || ended || !isPaused) return;
      isPaused = false;
      let userExtra = null;
      if (typeof opts.onResume === 'function') {
        try { userExtra = opts.onResume(extra || {}) || null; }
        catch(e) { console.warn('[lpHostCtl] onResume threw:', e); }
      }
      hidePauseOvl();
      const payload = Object.assign({ t: Date.now() }, extra || {}, userExtra || {});
      safeBroadcast('host:resumed', payload);
    }

    async function doEnd(extra){
      if (role !== 'host' || ended || !endable) return;
      if (opts.skipConfirm !== true && !confirm(texts.endConfirm)) return;
      ended = true;
      isPaused = false;
      if (typeof opts.onEnd === 'function') {
        try { opts.onEnd(extra || {}); }
        catch(e) { console.warn('[lpHostCtl] onEnd threw:', e); }
      }
      const payload = Object.assign(
        { t: Date.now(), reason: 'host_ended' },
        extra || {}
      );
      safeBroadcast('host:ended', payload);
      /* Flush the broadcast before closing. Some mobile browsers drop
         in-flight frames when the channel tears down immediately. */
      setTimeout(() => {
        try { room && typeof room.close === 'function' && room.close(); } catch(_){}
      }, 400);
      showEndedOvl(true);
    }

    if (role === 'host') {
      btnPause.addEventListener('click', () => doPause());
      btnResume.addEventListener('click', () => doResume());
      btnEnd.addEventListener('click', () => doEnd());
    }

    /* ---- Guest subscription ---- */
    function hydratePausedState(extra){
      /* For a guest that joins while the host is already paused —
         typically after a per-game snapshot says "paused=true". */
      if (ended || isPaused) return;
      isPaused = true;
      showPauseOvl(false);
      if (typeof opts.onHostPaused === 'function') {
        try { opts.onHostPaused(extra || {}); } catch(_){}
      }
    }

    if (role === 'guest' && room && typeof room.on === 'function') {
      room.on('host:paused', p => {
        if (ended || isPaused) return;
        isPaused = true;
        showPauseOvl(false);
        if (typeof opts.onHostPaused === 'function') {
          try { opts.onHostPaused(p || {}); } catch(_){}
        }
      });
      room.on('host:resumed', p => {
        if (ended) return;
        isPaused = false;
        hidePauseOvl();
        if (typeof opts.onHostResumed === 'function') {
          try { opts.onHostResumed(p || {}); } catch(_){}
        }
      });
      room.on('host:ended', p => {
        if (ended) return;
        if (typeof opts.onHostEnded === 'function') {
          try { opts.onHostEnded(p || {}); } catch(_){}
        }
        showEndedOvl(false);
      });
      /* Host closes the channel without a prior host:ended (crash, tab
         close, network failure). We still show ended so the guest
         isn't stranded on a dead room. Games that have their own
         "host disconnected, reconnecting..." UX should set
         opts.suppressHostClose to true. */
      if (!opts.suppressHostClose) {
        room.on('host:close', () => {
          if (ended) return;
          if (typeof opts.onHostEnded === 'function') {
            try { opts.onHostEnded({ reason: 'host_gone' }); } catch(_){}
          }
          showEndedOvl(false);
        });
      }
    }

    /* Refresh disabled state of the pause button by re-evaluating
       canPause. Useful when the host switches views (e.g. quiz
       "pause only valid inside question view") and wants the button
       to visually reflect that it's currently a no-op. */
    function refreshPauseEnabled(){
      if (opts.canPause === false) return;  /* hard-hidden, nothing to do */
      btnPause.disabled = !pausableNow() || isPaused;
    }

    /* Defensive exit from pause without a host:resumed — used when
       something else proves the pause is over (e.g. the next question
       payload arrives at a guest that missed the resumed broadcast). */
    function clearPausedState(){
      if (ended || !isPaused) return;
      isPaused = false;
      hidePauseOvl();
    }

    /* ---- Cleanup ---- */
    function destroy(){
      try { bar.remove(); }  catch(_){}
      try { povl.remove(); } catch(_){}
      try { eovl.remove(); } catch(_){}
      if (_current === ctl) _current = null;
    }

    const ctl = {
      show, hide,
      pause:  doPause,
      resume: doResume,
      end:    doEnd,
      setPausable, setEndable,
      refreshPauseEnabled,
      clearPausedState,
      isPaused: () => isPaused,
      isEnded:  () => ended,
      hydratePausedState,
      destroy
    };
    _current = ctl;
    return ctl;
  }

  window.LpHostCtl = { install: install };
})();
