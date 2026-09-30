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

  /* Default copy in the site's 16 UI languages (luckyplz_lang; gb → en).
     Before P0 (2026-09-30) this was Korean only and no game passed
     `texts`, so a non-Korean guest saw Korean on every pause / resume
     countdown / end overlay. `opts.texts` still overrides per key.
     {n} = seconds left. */
  const TEXTS = {
    ko: { pause:'일시정지', resume:'재개', end:'게임 종료',
      endConfirm:'정말 게임을 종료할까요?\n모든 참가자가 방에서 나갑니다.',
      pausedTitle:'일시정지 중', hostPausedSub:'참가자 전원의 화면이 멈춰있어요', guestPausedSub:'호스트가 잠시 멈췄어요',
      endedTitle:'게임 종료', endedHostSub:'게임을 종료했어요. 참가자는 모두 방에서 나갔어요.',
      endedGuestSub:'호스트가 게임을 종료했어요. 파티는 해제되었습니다.', homeBtn:'🏠 홈으로',
      resumeCountHost:'{n}초 후 참가자 전원 화면이 다시 움직여요', resumeCountGuest:'{n}초 후 게임이 다시 시작돼요' },
    en: { pause:'Pause', resume:'Resume', end:'End game',
      endConfirm:'End the game?\nEveryone will leave the room.',
      pausedTitle:'Paused', hostPausedSub:'Everyone\u2019s screen is paused', guestPausedSub:'The host paused the game',
      endedTitle:'Game over', endedHostSub:'You ended the game. Everyone has left the room.',
      endedGuestSub:'The host ended the game. The party is over.', homeBtn:'🏠 Home',
      resumeCountHost:'Everyone resumes in {n}s', resumeCountGuest:'Resuming in {n}s' },
    ja: { pause:'一時停止', resume:'再開', end:'ゲーム終了',
      endConfirm:'ゲームを終了しますか？\n全員がルームから退出します。',
      pausedTitle:'一時停止中', hostPausedSub:'参加者全員の画面が止まっています', guestPausedSub:'ホストが一時停止しました',
      endedTitle:'ゲーム終了', endedHostSub:'ゲームを終了しました。参加者は全員退出しました。',
      endedGuestSub:'ホストがゲームを終了しました。パーティーは解散です。', homeBtn:'🏠 ホームへ',
      resumeCountHost:'{n}秒後に全員の画面が再開します', resumeCountGuest:'{n}秒後に再開します' },
    zh: { pause:'暂停', resume:'继续', end:'结束游戏',
      endConfirm:'确定结束游戏吗？\n所有人都会离开房间。',
      pausedTitle:'已暂停', hostPausedSub:'所有人的画面已暂停', guestPausedSub:'房主暂停了游戏',
      endedTitle:'游戏结束', endedHostSub:'你结束了游戏，所有人已离开房间。',
      endedGuestSub:'房主结束了游戏，队伍已解散。', homeBtn:'🏠 首页',
      resumeCountHost:'{n}秒后所有人继续', resumeCountGuest:'{n}秒后继续' },
    es: { pause:'Pausa', resume:'Reanudar', end:'Terminar',
      endConfirm:'¿Terminar la partida?\nTodos saldrán de la sala.',
      pausedTitle:'En pausa', hostPausedSub:'La pantalla de todos está en pausa', guestPausedSub:'El anfitrión pausó el juego',
      endedTitle:'Fin del juego', endedHostSub:'Terminaste la partida. Todos salieron de la sala.',
      endedGuestSub:'El anfitrión terminó la partida. La sala se cerró.', homeBtn:'🏠 Inicio',
      resumeCountHost:'Todos siguen en {n} s', resumeCountGuest:'Se reanuda en {n} s' },
    pt: { pause:'Pausar', resume:'Retomar', end:'Encerrar',
      endConfirm:'Encerrar o jogo?\nTodos sairão da sala.',
      pausedTitle:'Pausado', hostPausedSub:'A tela de todos está pausada', guestPausedSub:'O anfitrião pausou o jogo',
      endedTitle:'Fim de jogo', endedHostSub:'Você encerrou o jogo. Todos saíram da sala.',
      endedGuestSub:'O anfitrião encerrou o jogo. A sala foi fechada.', homeBtn:'🏠 Início',
      resumeCountHost:'Todos voltam em {n} s', resumeCountGuest:'Retomando em {n} s' },
    de: { pause:'Pause', resume:'Weiter', end:'Spiel beenden',
      endConfirm:'Spiel beenden?\nAlle verlassen den Raum.',
      pausedTitle:'Pausiert', hostPausedSub:'Alle Bildschirme sind pausiert', guestPausedSub:'Der Host hat pausiert',
      endedTitle:'Spielende', endedHostSub:'Du hast das Spiel beendet. Alle haben den Raum verlassen.',
      endedGuestSub:'Der Host hat das Spiel beendet. Die Runde ist vorbei.', homeBtn:'🏠 Start',
      resumeCountHost:'Weiter für alle in {n} s', resumeCountGuest:'Weiter in {n} s' },
    fr: { pause:'Pause', resume:'Reprendre', end:'Terminer',
      endConfirm:'Terminer la partie ?\nTout le monde quittera le salon.',
      pausedTitle:'En pause', hostPausedSub:'L\u2019écran de tous est en pause', guestPausedSub:'L\u2019hôte a mis en pause',
      endedTitle:'Partie terminée', endedHostSub:'Vous avez terminé la partie. Tout le monde est parti.',
      endedGuestSub:'L\u2019hôte a terminé la partie. Le salon est fermé.', homeBtn:'🏠 Accueil',
      resumeCountHost:'Reprise pour tous dans {n} s', resumeCountGuest:'Reprise dans {n} s' },
    ru: { pause:'Пауза', resume:'Продолжить', end:'Завершить',
      endConfirm:'Завершить игру?\nВсе выйдут из комнаты.',
      pausedTitle:'Пауза', hostPausedSub:'Экраны всех игроков на паузе', guestPausedSub:'Хост поставил паузу',
      endedTitle:'Игра окончена', endedHostSub:'Вы завершили игру. Все вышли из комнаты.',
      endedGuestSub:'Хост завершил игру. Комната закрыта.', homeBtn:'🏠 Главная',
      resumeCountHost:'Продолжение для всех через {n} с', resumeCountGuest:'Продолжение через {n} с' },
    ar: { pause:'إيقاف مؤقت', resume:'استئناف', end:'إنهاء اللعبة',
      endConfirm:'هل تريد إنهاء اللعبة؟\nسيغادر الجميع الغرفة.',
      pausedTitle:'متوقف مؤقتًا', hostPausedSub:'شاشات الجميع متوقفة', guestPausedSub:'أوقف المضيف اللعبة مؤقتًا',
      endedTitle:'انتهت اللعبة', endedHostSub:'أنهيت اللعبة. غادر الجميع الغرفة.',
      endedGuestSub:'أنهى المضيف اللعبة. أُغلقت الغرفة.', homeBtn:'🏠 الرئيسية',
      resumeCountHost:'يستأنف الجميع بعد {n} ث', resumeCountGuest:'الاستئناف بعد {n} ث' },
    hi: { pause:'रोकें', resume:'फिर शुरू', end:'गेम खत्म',
      endConfirm:'गेम खत्म करें?\nसभी रूम से बाहर हो जाएंगे।',
      pausedTitle:'रुका हुआ', hostPausedSub:'सभी की स्क्रीन रुकी है', guestPausedSub:'होस्ट ने गेम रोका',
      endedTitle:'गेम खत्म', endedHostSub:'आपने गेम खत्म किया। सभी रूम से बाहर हो गए।',
      endedGuestSub:'होस्ट ने गेम खत्म किया। रूम बंद हो गया।', homeBtn:'🏠 होम',
      resumeCountHost:'{n} सेकंड में सभी के लिए फिर शुरू', resumeCountGuest:'{n} सेकंड में फिर शुरू' },
    th: { pause:'หยุดชั่วคราว', resume:'เล่นต่อ', end:'จบเกม',
      endConfirm:'จบเกมเลยไหม?\nทุกคนจะออกจากห้อง',
      pausedTitle:'หยุดชั่วคราว', hostPausedSub:'หน้าจอของทุกคนหยุดอยู่', guestPausedSub:'โฮสต์หยุดเกมชั่วคราว',
      endedTitle:'จบเกม', endedHostSub:'คุณจบเกมแล้ว ทุกคนออกจากห้องแล้ว',
      endedGuestSub:'โฮสต์จบเกมแล้ว ห้องถูกปิด', homeBtn:'🏠 หน้าแรก',
      resumeCountHost:'ทุกคนเล่นต่อใน {n} วิ', resumeCountGuest:'เล่นต่อใน {n} วิ' },
    id: { pause:'Jeda', resume:'Lanjut', end:'Akhiri',
      endConfirm:'Akhiri permainan?\nSemua orang akan keluar dari room.',
      pausedTitle:'Dijeda', hostPausedSub:'Layar semua pemain dijeda', guestPausedSub:'Host menjeda permainan',
      endedTitle:'Permainan selesai', endedHostSub:'Kamu mengakhiri permainan. Semua sudah keluar.',
      endedGuestSub:'Host mengakhiri permainan. Room ditutup.', homeBtn:'🏠 Beranda',
      resumeCountHost:'Semua lanjut dalam {n} dtk', resumeCountGuest:'Lanjut dalam {n} dtk' },
    vi: { pause:'Tạm dừng', resume:'Tiếp tục', end:'Kết thúc',
      endConfirm:'Kết thúc trò chơi?\nMọi người sẽ rời phòng.',
      pausedTitle:'Đang tạm dừng', hostPausedSub:'Màn hình của mọi người đang dừng', guestPausedSub:'Chủ phòng đã tạm dừng',
      endedTitle:'Kết thúc', endedHostSub:'Bạn đã kết thúc trò chơi. Mọi người đã rời phòng.',
      endedGuestSub:'Chủ phòng đã kết thúc trò chơi. Phòng đã đóng.', homeBtn:'🏠 Trang chủ',
      resumeCountHost:'Mọi người tiếp tục sau {n} giây', resumeCountGuest:'Tiếp tục sau {n} giây' },
    tr: { pause:'Duraklat', resume:'Devam', end:'Oyunu bitir',
      endConfirm:'Oyun bitirilsin mi?\nHerkes odadan çıkacak.',
      pausedTitle:'Duraklatıldı', hostPausedSub:'Herkesin ekranı duraklatıldı', guestPausedSub:'Oda sahibi oyunu duraklattı',
      endedTitle:'Oyun bitti', endedHostSub:'Oyunu bitirdin. Herkes odadan çıktı.',
      endedGuestSub:'Oda sahibi oyunu bitirdi. Oda kapandı.', homeBtn:'🏠 Ana sayfa',
      resumeCountHost:'Herkes {n} sn sonra devam ediyor', resumeCountGuest:'{n} sn sonra devam' }
  };
  function _lang(){
    let l = 'en';
    try { l = (localStorage.getItem('luckyplz_lang') || 'en').toLowerCase().split('-')[0]; } catch(_){}
    return l === 'gb' ? 'en' : l;
  }
  /* Resolved at install() time (the language can change between rooms). */
  function defaultTexts(){ return Object.assign({}, TEXTS.en, TEXTS[_lang()] || {}); }

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
      `.lp-hc-presume{margin-top:18px;padding:12px 30px;border-radius:999px;border:0;background:linear-gradient(135deg,#FFE066,#FFB84D);color:#0a0a1a;font-family:'Orbitron','Noto Sans KR',sans-serif;font-weight:900;font-size:1em;letter-spacing:.08em;cursor:pointer;box-shadow:0 10px 22px -6px rgba(255,230,109,.45);transition:transform .08s,filter .2s;min-width:160px}`,
      `.lp-hc-presume:active{transform:scale(.96)}`,
      `.lp-hc-presume:hover{filter:brightness(1.08)}`,
      `.lp-hc-presume:disabled{cursor:default;filter:none}`,
      /* Resume countdown. Replaces the title card with a big pulsing
         number + subtext so both host and guests see the same 5→0
         rundown before play picks back up. Driven by host:resume_countdown. */
      `.lp-hc-cd-num{display:inline-flex;align-items:center;justify-content:center;min-width:68px;height:68px;border-radius:50%;background:linear-gradient(135deg,#FFE066,#FFB84D);color:#0a0a1a;font-family:'Orbitron',sans-serif;font-size:2.2em;font-weight:900;line-height:1;box-shadow:0 10px 26px -6px rgba(255,230,109,.55);animation:lpHcCd .95s ease-out}`,
      `@keyframes lpHcCd{0%{transform:scale(.55);opacity:0}30%{transform:scale(1.12);opacity:1}100%{transform:scale(1);opacity:1}}`,

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
    const texts = Object.assign(defaultTexts(), opts.texts || {});

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

    /* Resume is gated by a 5-second visible countdown so late/distracted
       guests see the pace change before the timer starts ticking again.
       The host triggers it; the same countdown UI runs on every guest
       via host:resume_countdown. After the countdown resolves, the
       host fires the real host:resumed and game state rolls forward. */
    const RESUME_COUNTDOWN_SECS = 5;
    let cdInflight = false;

    function runResumeCountdown(seconds, isHost){
      return new Promise(function(resolve){
        if (cdInflight) return resolve();
        cdInflight = true;
        btnResume.disabled = true;
        const origResumeLabel = btnResume.innerHTML;
        let n = seconds;
        function render(){
          povlSub.textContent = (isHost ? texts.resumeCountHost : texts.resumeCountGuest)
            .replace('{n}', n);
          btnResume.innerHTML = `<span class="lp-hc-cd-num" key="${n}">${n}</span>`;
        }
        render();
        const tick = function(){
          n--;
          if (n > 0){ render(); setTimeout(tick, 1000); }
          else {
            btnResume.innerHTML = origResumeLabel;
            btnResume.disabled = false;
            cdInflight = false;
            resolve();
          }
        };
        setTimeout(tick, 1000);
      });
    }

    async function doResume(extra){
      if (role !== 'host' || ended || !isPaused || cdInflight) return;
      /* Kick the countdown broadcast FIRST so the guests start their
         local countdown in lockstep with the host's UI tick. */
      safeBroadcast('host:resume_countdown', {
        seconds: RESUME_COUNTDOWN_SECS, t: Date.now()
      });
      await runResumeCountdown(RESUME_COUNTDOWN_SECS, true);
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
      /* Dispatch lp-room-closed up-front so the lpMultiplayer floating
         panel + lpRoom status pill tear down in the same tick the
         ended-overlay appears, not 400ms later when the channel is
         finally removed. _onRoomClosed above guards on `ended` so this
         doesn't re-trigger ourselves. */
      try { window.dispatchEvent(new CustomEvent('lp-room-closed',{detail:{mode:'host',reason:'host_ended'}})); } catch(_){}
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
      room.on('host:resume_countdown', p => {
        if (ended || !isPaused) return;
        const secs = (p && typeof p.seconds === 'number' && p.seconds > 0) ? p.seconds : RESUME_COUNTDOWN_SECS;
        runResumeCountdown(secs, false);
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
    /* When the underlying room is closed via ANY path other than this
       module's own ⏹ button (host clicks the lpRoom status-pill ×, the
       lpMultiplayer panel's "방 닫기", or a guest's "나가기"), we still
       need to tear our DOM down — otherwise the floating ⏸ ⏹ bar stays
       pinned to the corner pointing at a dead channel and the next
       click on it tries to broadcast on a removed Supabase channel.
       lpRoom dispatches `lp-room-closed` from every legitimate close
       path; this listener funnels them all into destroy(). */
    function _onRoomClosed(e){
      if (ended) return;
      /* Self-leaves (guest pressed "나가기" to play solo) shouldn't show
         the ended overlay — the user explicitly chose to bail; surfacing
         "GAME ENDED" would be misleading. lpRoom tags those with
         reason:'self'. Host-side self-close paths (the panel "방 닫기",
         the status × button, ⏹) all want the overlay so the host knows
         the room is gone before any further action. */
      const reason = (e && e.detail && e.detail.reason) || '';
      if (role === 'guest' && reason === 'self') {
        try { bar.remove(); }  catch(_){}
        try { povl.remove(); } catch(_){}
        try { eovl.remove(); } catch(_){}
        try { window.removeEventListener('lp-room-closed', _onRoomClosed); } catch(_){}
        if (_current === ctl) _current = null;
        return;
      }
      try { showEndedOvl(role === 'host'); } catch(_){}
    }
    window.addEventListener('lp-room-closed', _onRoomClosed);

    function destroy(){
      try { window.removeEventListener('lp-room-closed', _onRoomClosed); } catch(_){}
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

  window.LpHostCtl = { install: install, texts: defaultTexts };
})();
