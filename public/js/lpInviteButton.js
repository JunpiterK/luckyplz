/*
  Lucky Please — Game-page Invite button
  =======================================
  Auto-injected on every /games/* page (from siteFooter.js). Shows a
  floating "👥 친구 초대" pill + opens a modal listing the user's
  friends, colour-coded by presence. Clicking a row fires
  LpInvite.sendInvite with the current page URL as the destination,
  so the guest lands on exactly the same URL (and any ?room= query
  threaded through there picks up LpRoom's auto-join logic).

  Visibility rules:
    • Hidden until auth (getUser resolves + profile_complete)
    • Hidden when there are no accepted friends yet
    • Accessible via keyboard (tab-focusable + Enter)

  States for each friend row:
    online    — "초대" button enabled
    dnd       — greyed row, tooltip "방해금지 중이에요"
    offline   — greyed row, tooltip "오프라인이에요"

  Once a row is clicked and the RPC fires, the row switches to
  "전송됨 • 대기 중" with the timestamp. When LpInvite.onResponse
  fires for that invite id, the row flips to "수락함" (green) or
  "거절함" (red) for a few seconds before reverting.
*/
(function(){
    if (window.LpInviteButton) return;
    /* Only inject on /games/* pages — site-wide injection is both
       unnecessary and visually noisy. */
    if (!/^\/games\//.test(location.pathname)) return;

    let _pillEl = null;
    let _modalEl = null;
    /* ── UI i18n (2026-08-20) — 모달 전체가 한국어 고정이었다.
       SEO 5개 언어 + en 폴백. 게임명은 lpInvite 와 동일 표기. */
    const IB_I18N = {
        ko:{invite:'친구 초대',loading:'불러오는 중…',noSocial:'소셜 모듈을 불러올 수 없어요.',
            loadFail:'친구 목록을 불러오지 못했어요.',
            noFriends:'아직 친구가 없어요.<br><a style="color:#00D9FF" href="/messages/">/messages/</a> 에서 추가해보세요.',
            secOnline:'온라인 · 초대 가능',secDnd:'방해금지',secOffline:'오프라인',
            subDnd:'방해금지 중',subOffline:'오프라인',
            act:'초대',actDisabled:'초대 불가',sending:'전송 중…',waiting:'대기 중…',
            errOffline:'오프라인',errNotFriends:'친구 아님',errSelf:'본인 초대 불가',errRetry:'재시도',
            accepted:'수락함 ✓',declined:'거절함',expiredLbl:'만료',game:'게임',
            games:{lotto:'로또',roulette:'룰렛',ladder:'사다리',dice:'주사위',team:'팀 나누기',bingo:'빙고','car-racing':'카레이싱'}},
        en:{invite:'Invite friends',loading:'Loading…',noSocial:'Could not load the social module.',
            loadFail:'Could not load your friends list.',
            noFriends:'No friends yet.<br>Add some at <a style="color:#00D9FF" href="/messages/">/messages/</a>.',
            secOnline:'Online · can invite',secDnd:'Do not disturb',secOffline:'Offline',
            subDnd:'Do not disturb',subOffline:'Offline',
            act:'Invite',actDisabled:'Unavailable',sending:'Sending…',waiting:'Waiting…',
            errOffline:'Offline',errNotFriends:'Not friends',errSelf:'That is you',errRetry:'Retry',
            accepted:'Accepted ✓',declined:'Declined',expiredLbl:'Expired',game:'Game',
            games:{lotto:'Lotto',roulette:'Roulette',ladder:'Ladder',dice:'Dice',team:'Team Picker',bingo:'Bingo','car-racing':'Car Racing'}},
        ja:{invite:'友だちを招待',loading:'読み込み中…',noSocial:'ソーシャルモジュールを読み込めません。',
            loadFail:'フレンド一覧を読み込めませんでした。',
            noFriends:'まだフレンドがいません。<br><a style="color:#00D9FF" href="/messages/">/messages/</a> で追加できます。',
            secOnline:'オンライン · 招待可能',secDnd:'おやすみモード',secOffline:'オフライン',
            subDnd:'おやすみモード中',subOffline:'オフライン',
            act:'招待',actDisabled:'招待不可',sending:'送信中…',waiting:'待機中…',
            errOffline:'オフライン',errNotFriends:'フレンドではありません',errSelf:'自分には送れません',errRetry:'再試行',
            accepted:'参加 ✓',declined:'辞退',expiredLbl:'期限切れ',game:'ゲーム',
            games:{lotto:'ロト',roulette:'ルーレット',ladder:'あみだくじ',dice:'サイコロ',team:'チーム分け',bingo:'ビンゴ','car-racing':'カーレース'}},
        es:{invite:'Invitar amigos',loading:'Cargando…',noSocial:'No se pudo cargar el módulo social.',
            loadFail:'No se pudo cargar tu lista de amigos.',
            noFriends:'Aún no tienes amigos.<br>Agrégalos en <a style="color:#00D9FF" href="/messages/">/messages/</a>.',
            secOnline:'En línea · se puede invitar',secDnd:'No molestar',secOffline:'Desconectado',
            subDnd:'No molestar',subOffline:'Desconectado',
            act:'Invitar',actDisabled:'No disponible',sending:'Enviando…',waiting:'Esperando…',
            errOffline:'Desconectado',errNotFriends:'No sois amigos',errSelf:'Eres tú',errRetry:'Reintentar',
            accepted:'Aceptó ✓',declined:'Rechazó',expiredLbl:'Caducado',game:'Juego',
            games:{lotto:'Lotería',roulette:'Ruleta',ladder:'Escalera',dice:'Dados',team:'Equipos',bingo:'Bingo','car-racing':'Carrera'}},
        pt:{invite:'Convidar amigos',loading:'Carregando…',noSocial:'Não foi possível carregar o módulo social.',
            loadFail:'Não foi possível carregar sua lista de amigos.',
            noFriends:'Ainda sem amigos.<br>Adicione em <a style="color:#00D9FF" href="/messages/">/messages/</a>.',
            secOnline:'Online · pode convidar',secDnd:'Não perturbe',secOffline:'Offline',
            subDnd:'Não perturbe',subOffline:'Offline',
            act:'Convidar',actDisabled:'Indisponível',sending:'Enviando…',waiting:'Aguardando…',
            errOffline:'Offline',errNotFriends:'Não são amigos',errSelf:'É você',errRetry:'Tentar de novo',
            accepted:'Aceitou ✓',declined:'Recusou',expiredLbl:'Expirado',game:'Jogo',
            games:{lotto:'Loteria',roulette:'Roleta',ladder:'Escada',dice:'Dados',team:'Times',bingo:'Bingo','car-racing':'Corrida'}}
    };
    function IBT() {
        let l; try { l = localStorage.getItem('luckyplz_lang') || 'en'; } catch (_) { l = 'en'; }
        if (l === 'gb') l = 'en';
        return IB_I18N[l] || IB_I18N.en;
    }

    let _pendingByFriend = new Map();
    let _dragCleanup = []; /* friendId → invite id for active sends */
    let _responseUnsub = null;
    let _presenceUnsub = null;
    let _booted = false;

    function _gameTypeFromPath() {
        const m = location.pathname.match(/^\/games\/([^\/]+)/);
        return m ? m[1] : 'game';
    }

    function _ensureStyles() {
        if (document.getElementById('lp-invite-button-css')) return;
        const css = `
        .lp-ib-pill{
            position:fixed;right:14px;bottom:14px;z-index:100;
            display:inline-flex;align-items:center;gap:8px;
            padding:11px 16px;border-radius:999px;border:0;cursor:grab;
            background:linear-gradient(135deg,#00D9FF 0%,#0099CC 100%);
            color:#001220;font-family:'Noto Sans KR',sans-serif;
            font-size:.88em;font-weight:800;letter-spacing:.02em;
            box-shadow:0 10px 28px -8px rgba(0,217,255,.55),inset 0 1px 0 rgba(255,255,255,.28);
            transition:transform .18s,filter .18s,box-shadow .22s;
            /* touch-action:none disables the browser's default touch
               gestures (panning/zooming) on the pill so a drag isn't
               hijacked by the page scroller. */
            touch-action:none;
            user-select:none;-webkit-user-select:none;
        }
        .lp-ib-pill:active{cursor:grabbing}
        .lp-ib-pill:hover{transform:translateY(-2px);filter:brightness(1.08)}
        .lp-ib-pill:active{transform:translateY(1px);transition-duration:.08s}
        .lp-ib-pill .ico{font-size:1.06em}
        @media (max-width:560px){
            .lp-ib-pill{right:10px;bottom:10px;padding:10px 14px;font-size:.82em}
        }
        .lp-ib-modal{
            position:fixed;inset:0;background:rgba(5,5,15,.72);
            display:none;align-items:center;justify-content:center;
            z-index:2000;padding:16px;backdrop-filter:blur(4px);
            animation:lpibFade .18s ease-out;
        }
        .lp-ib-modal.on{display:flex}
        @keyframes lpibFade{from{opacity:0}to{opacity:1}}
        .lp-ib-card{
            width:100%;max-width:420px;max-height:80vh;overflow:hidden;
            background:linear-gradient(160deg,rgba(22,22,42,.98),rgba(12,12,28,1));
            border:1px solid rgba(255,255,255,.1);border-radius:18px;
            box-shadow:0 24px 60px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.06);
            color:#fff;font-family:'Noto Sans KR',sans-serif;
            display:flex;flex-direction:column;
        }
        .lp-ib-head{padding:18px 20px 10px;display:flex;align-items:center;gap:10px;border-bottom:1px solid rgba(255,255,255,.06)}
        .lp-ib-head h3{font-size:1.04em;font-weight:800;letter-spacing:-.01em;flex:1}
        .lp-ib-head .close{width:28px;height:28px;border-radius:8px;border:0;background:rgba(255,255,255,.06);color:#fff;cursor:pointer;font-size:1em}
        .lp-ib-head .close:hover{background:rgba(255,255,255,.12)}
        .lp-ib-body{overflow-y:auto;max-height:60vh;padding:6px 8px}
        .lp-ib-section-label{padding:10px 14px 4px;font-size:.68em;letter-spacing:.1em;text-transform:uppercase;color:rgba(255,255,255,.35);font-weight:800}
        .lp-ib-empty{padding:22px 16px;text-align:center;color:rgba(255,255,255,.45);font-size:.9em;line-height:1.55}
        .lp-ib-row{display:flex;align-items:center;gap:11px;padding:10px 12px;border-radius:12px;transition:background .15s}
        .lp-ib-row:hover{background:rgba(255,255,255,.04)}
        .lp-ib-row.disabled{opacity:.45;cursor:not-allowed}
        .lp-ib-av{
            width:38px;height:38px;border-radius:50%;flex-shrink:0;position:relative;overflow:hidden;
            background:linear-gradient(135deg,#FF6B35,#FF6B8B);
            display:flex;align-items:center;justify-content:center;
            font-family:'Orbitron',sans-serif;font-weight:900;font-size:.88em;color:#fff;
        }
        .lp-ib-av img{width:100%;height:100%;object-fit:cover}
        .lp-ib-av .sd{
            position:absolute;bottom:-1px;right:-1px;width:11px;height:11px;border-radius:50%;
            border:2px solid rgba(12,12,28,1);background:#6b6f7a;
        }
        .lp-ib-av .sd.online{background:#00E676;box-shadow:0 0 6px rgba(0,230,118,.55)}
        .lp-ib-av .sd.dnd{background:#FF9A3C}
        .lp-ib-av .sd.offline{background:transparent;border-color:rgba(255,255,255,.25)}
        .lp-ib-meta{flex:1;min-width:0}
        .lp-ib-nick{font-weight:700;font-size:.92em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .lp-ib-sub{font-size:.72em;color:rgba(255,255,255,.42);margin-top:2px}
        .lp-ib-act{
            padding:7px 14px;border-radius:999px;border:0;cursor:pointer;
            background:linear-gradient(135deg,#00D9FF,#0099CC);color:#001220;
            font-family:inherit;font-size:.78em;font-weight:800;letter-spacing:.04em;
            transition:transform .15s,filter .15s;
        }
        .lp-ib-act:hover{transform:translateY(-1px);filter:brightness(1.08)}
        .lp-ib-act:disabled{opacity:.55;cursor:default;transform:none;filter:none}
        .lp-ib-act.sent{background:rgba(255,255,255,.07);color:rgba(255,255,255,.75)}
        .lp-ib-act.accepted{background:linear-gradient(135deg,#00FF88,#00C97A);color:#003322}
        .lp-ib-act.declined{background:rgba(255,51,102,.15);color:#FF6B8B}
        `;
        const style = document.createElement('style');
        style.id = 'lp-invite-button-css';
        style.textContent = css;
        document.head.appendChild(style);
    }

    /* ---- Drag-to-relocate -----------------------------------------
       The pill anchors bottom-right by default but in some games (e.g.
       Space-Z on phone) it covers the right thumb-zone of the live
       game canvas. Letting the user drag it anywhere on screen
       (with the saved position persisted across sessions) is more
       flexible than hard-coding a per-game offset.

       Behaviour:
         • Press + drag past 5 px → enter drag mode, follow finger/mouse.
         • Stay below threshold + release → treated as a click (open
           modal). Click is suppressed if the gesture qualified as a drag.
         • On release, position is clamped within the viewport with a
           4 px gutter and saved to localStorage.
         • On mount (and on viewport resize), saved position is restored
           and re-clamped so a portrait→landscape rotation on phones
           doesn't strand the pill off-screen.
    */
    const DRAG_POS_KEY = 'lp_ib_pos_v1';
    const DRAG_THRESHOLD = 5;
    function _clampPos(pos, btn){
        const w = btn.offsetWidth  || 120;
        const h = btn.offsetHeight || 44;
        return {
            left: Math.max(4, Math.min(window.innerWidth  - w - 4, pos.left)),
            top:  Math.max(4, Math.min(window.innerHeight - h - 4, pos.top))
        };
    }
    function _applyPos(btn, pos){
        const c = _clampPos(pos, btn);
        btn.style.left   = c.left + 'px';
        btn.style.top    = c.top  + 'px';
        btn.style.right  = 'auto';
        btn.style.bottom = 'auto';
    }
    function _savePos(btn){
        try{
            const r = btn.getBoundingClientRect();
            localStorage.setItem(DRAG_POS_KEY, JSON.stringify({left:r.left, top:r.top}));
        }catch(_){}
    }
    function _restorePos(btn){
        try{
            const saved = JSON.parse(localStorage.getItem(DRAG_POS_KEY) || 'null');
            if (saved && typeof saved.left === 'number' && typeof saved.top === 'number'){
                _applyPos(btn, saved);
            }
        }catch(_){}
    }
    function _enableDrag(btn){
        let dragging = false;
        let movedFar  = false;
        let startX = 0, startY = 0;
        let originX = 0, originY = 0;

        function _begin(clientX, clientY){
            const r = btn.getBoundingClientRect();
            originX = r.left; originY = r.top;
            startX  = clientX; startY = clientY;
            movedFar = false;
            dragging = true;
            /* Promote the pill to z-top while dragging so it visually
               sits over any HUD element it crosses. */
            btn.style.zIndex = 9999;
            /* Switch positioning model from right/bottom (CSS default)
               to left/top so the drag math is straightforward. */
            btn.style.left   = originX + 'px';
            btn.style.top    = originY + 'px';
            btn.style.right  = 'auto';
            btn.style.bottom = 'auto';
        }
        function _move(clientX, clientY){
            if (!dragging) return false;
            const dx = clientX - startX;
            const dy = clientY - startY;
            if (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD) movedFar = true;
            if (movedFar){
                _applyPos(btn, {left: originX + dx, top: originY + dy});
                return true;
            }
            return false;
        }
        function _end(){
            if (!dragging) return;
            dragging = false;
            btn.style.zIndex = '';
            if (movedFar){
                _savePos(btn);
                /* Keep movedFar true through the upcoming click event so
                   the click-suppress capture handler sees it, then clear
                   it on the next tick. */
                setTimeout(()=>{ movedFar = false; }, 60);
            }
        }

        /* Mouse */
        btn.addEventListener('mousedown', (e) => {
            if (e.button !== 0) return;
            e.preventDefault();
            _begin(e.clientX, e.clientY);
        });
        const _onMouseMove = (e) => {
            if (_move(e.clientX, e.clientY)) e.preventDefault();
        };
        document.addEventListener('mousemove', _onMouseMove);
        document.addEventListener('mouseup', _end);

        /* Touch */
        btn.addEventListener('touchstart', (e) => {
            const t = e.touches && e.touches[0];
            if (!t) return;
            _begin(t.clientX, t.clientY);
        }, {passive:true});
        const _onTouchMove = (e) => {
            const t = e.touches && e.touches[0];
            if (!t) return;
            if (_move(t.clientX, t.clientY)){
                /* Prevent page scroll only AFTER we've confirmed it's a
                   drag, so an accidental tap-near-edge doesn't lock the
                   page. */
                if (e.cancelable) e.preventDefault();
            }
        };
        document.addEventListener('touchmove', _onTouchMove, {passive:false});
        document.addEventListener('touchend', _end);
        document.addEventListener('touchcancel', _end);

        /* Capture-phase click suppressor — if the pointer moved past
           DRAG_THRESHOLD between down and up, the browser still fires
           a click. We swallow it so the modal doesn't open right after
           the user finished repositioning the pill. */
        btn.addEventListener('click', (e) => {
            if (movedFar){
                e.stopPropagation();
                e.preventDefault();
            }
        }, true);

        /* Re-clamp on viewport resize / orientation change so a saved
           position from landscape doesn't strand the pill off-screen
           after a rotation to portrait. */
        const _onResize = () => {
            const r = btn.getBoundingClientRect();
            _applyPos(btn, {left:r.left, top:r.top});
        };
        window.addEventListener('resize', _onResize);

        /* 로그아웃(_teardown) 후에도 document/window 리스너가 잔류하던
           누수 — 해제 함수를 모아 두고 teardown 에서 실행한다. */
        _dragCleanup.push(() => {
            document.removeEventListener('mousemove', _onMouseMove);
            document.removeEventListener('mouseup', _end);
            document.removeEventListener('touchmove', _onTouchMove);
            document.removeEventListener('touchend', _end);
            document.removeEventListener('touchcancel', _end);
            window.removeEventListener('resize', _onResize);
        });
    }

    function _mountPill() {
        _ensureStyles();
        if (_pillEl) return;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'lp-ib-pill';
        btn.innerHTML = '<span class="ico">👥</span><span>' + IBT().invite + '</span>';
        btn.addEventListener('click', _openModal);
        document.body.appendChild(btn);
        _pillEl = btn;
        /* Restore + drag wire-up runs after appending so offsetWidth/
           offsetHeight are real numbers (otherwise clamp uses fallbacks). */
        _restorePos(btn);
        _enableDrag(btn);
    }

    function _unmountPill() {
        if (_pillEl) { _pillEl.remove(); _pillEl = null; }
    }

    async function _openModal() {
        _ensureStyles();
        _buildModalShell();
        await _renderFriendsList();
        _modalEl.classList.add('on');
    }

    function _closeModal() {
        if (_modalEl) _modalEl.classList.remove('on');
    }

    function _buildModalShell() {
        if (_modalEl) return;
        const wrap = document.createElement('div');
        wrap.className = 'lp-ib-modal';
        wrap.innerHTML =
            '<div class="lp-ib-card">'
            + '<div class="lp-ib-head">'
                + '<h3>' + IBT().invite + ' · ' + _esc(_humanGame(_gameTypeFromPath())) + '</h3>'
                + '<button class="close" type="button" aria-label="Close">✕</button>'
            + '</div>'
            + '<div class="lp-ib-body" id="lpIbBody"></div>'
            + '</div>';
        wrap.addEventListener('click', (e) => { if (e.target === wrap) _closeModal(); });
        wrap.querySelector('.close').addEventListener('click', _closeModal);
        document.body.appendChild(wrap);
        _modalEl = wrap;
    }

    async function _renderFriendsList() {
        const body = _modalEl.querySelector('#lpIbBody');
        body.innerHTML = '<div class="lp-ib-empty">' + IBT().loading + '</div>';
        if (!window.LpSocial) { body.innerHTML = '<div class="lp-ib-empty">' + IBT().noSocial + '</div>'; return; }
        const r = await LpSocial.getFriends();
        if (!r.ok) { body.innerHTML = '<div class="lp-ib-empty">' + IBT().loadFail + '</div>'; return; }
        const accepted = (r.rows || []).filter(f => f.direction === 'accepted');
        if (!accepted.length) {
            body.innerHTML = '<div class="lp-ib-empty">' + IBT().noFriends + '</div>';
            return;
        }

        /* Group by presence — online first (invitable), then greyed. */
        const buckets = { online: [], dnd: [], offline: [] };
        for (const f of accepted) {
            const s = (window.LpPresence && LpPresence.getStatus(f.friend_id)) || 'offline';
            buckets[s] = buckets[s] || [];
            buckets[s].push(f);
        }

        let html = '';
        if (buckets.online.length) {
            html += '<div class="lp-ib-section-label">' + IBT().secOnline + '</div>';
            html += buckets.online.map(f => _friendRowHtml(f, 'online', false)).join('');
        }
        if (buckets.dnd.length) {
            html += '<div class="lp-ib-section-label">' + IBT().secDnd + '</div>';
            html += buckets.dnd.map(f => _friendRowHtml(f, 'dnd', true)).join('');
        }
        if (buckets.offline.length) {
            html += '<div class="lp-ib-section-label">' + IBT().secOffline + '</div>';
            html += buckets.offline.map(f => _friendRowHtml(f, 'offline', true)).join('');
        }
        body.innerHTML = html;
        body.querySelectorAll('[data-invite-to]').forEach(btn => {
            btn.addEventListener('click', () => _sendOne(btn.dataset.inviteTo, btn));
        });
    }

    function _friendRowHtml(f, status, disabled) {
        const av = f.avatar_url
            ? '<div class="lp-ib-av"><img src="' + _esc(f.avatar_url) + '" referrerpolicy="no-referrer" alt=""><span class="sd ' + status + '"></span></div>'
            : '<div class="lp-ib-av">' + _esc((f.nickname || '?').trim()[0] || '?').toUpperCase() + '<span class="sd ' + status + '"></span></div>';
        const sub = status === 'dnd' ? IBT().subDnd : status === 'offline' ? IBT().subOffline : '';
        const btn = disabled
            ? '<button class="lp-ib-act" disabled>' + IBT().actDisabled + '</button>'
            : '<button class="lp-ib-act" type="button" data-invite-to="' + _esc(f.friend_id) + '">' + IBT().act + '</button>';
        return '<div class="lp-ib-row' + (disabled ? ' disabled' : '') + '">'
            + av
            + '<div class="lp-ib-meta">'
                + '<div class="lp-ib-nick">' + _esc(f.nickname || '(deleted)') + '</div>'
                + (sub ? '<div class="lp-ib-sub">' + _esc(sub) + '</div>' : '')
            + '</div>'
            + btn
            + '</div>';
    }

    async function _sendOne(friendId, btn) {
        if (!window.LpInvite) return;
        btn.disabled = true;
        btn.textContent = IBT().sending;
        btn.classList.add('sent');
        const gameType = _gameTypeFromPath();
        const gameUrl  = location.href;
        const r = await LpInvite.sendInvite(friendId, gameType, gameUrl);
        if (!r.ok) {
            btn.classList.remove('sent');
            btn.classList.add('declined');
            btn.textContent = _errToLabel(r.error);
            /* Revert after 2.5 s so the user can retry */
            setTimeout(() => { btn.classList.remove('declined'); btn.textContent = IBT().act; btn.disabled = false; }, 2500);
            return;
        }
        _pendingByFriend.set(friendId, r.id);
        btn.textContent = IBT().waiting;
    }

    function _errToLabel(err) {
        const t = IBT();
        switch (err) {
            case 'offline':     return t.errOffline;
            case 'not_friends': return t.errNotFriends;
            case 'self':        return t.errSelf;
            default:            return t.errRetry;
        }
    }

    /* Incoming response for one of MY invites — update the row's button
       to accepted / declined / expired / cancelled. */
    function _handleResponse(row) {
        if (!row) return;
        const btn = _modalEl && _modalEl.querySelector('[data-invite-to="' + row.to_id + '"]');
        if (!btn) { _pendingByFriend.delete(row.to_id); return; }
        btn.classList.remove('sent','accepted','declined');
        if (row.status === 'accepted') {
            btn.classList.add('accepted');
            btn.textContent = IBT().accepted;
        } else if (row.status === 'declined') {
            btn.classList.add('declined');
            btn.textContent = IBT().declined;
        } else if (row.status === 'expired') {
            btn.classList.add('declined');
            btn.textContent = IBT().expiredLbl;
        } else {
            btn.textContent = IBT().act;
            btn.disabled = false;
        }
        _pendingByFriend.delete(row.to_id);
    }

    function _esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
    function _humanGame(type){
        const t = IBT();
        return t.games[type]||t.game;
    }

    /* ---- Boot --------------------------------------------- */
    async function boot() {
        if (_booted) return;
        const user = await getUser();
        if (!user) return;
        _mountPill();
        if (window.LpInvite) {
            _responseUnsub = LpInvite.onResponse(_handleResponse);
        }
        if (window.LpPresence) {
            _presenceUnsub = LpPresence.onChange(() => {
                /* If the modal is open, re-render so new statuses are reflected. */
                if (_modalEl && _modalEl.classList.contains('on')) _renderFriendsList();
            });
        }
        _booted = true;
    }

    function _teardown() {
        _unmountPill();
        _dragCleanup.forEach((fn) => { try { fn(); } catch (_) {} });
        _dragCleanup = [];
        if (_responseUnsub)  { _responseUnsub(); _responseUnsub = null; }
        if (_presenceUnsub)  { _presenceUnsub(); _presenceUnsub = null; }
        if (_modalEl)        { _modalEl.remove(); _modalEl = null; }
        _booted = false;
    }

    function _wireAuth() {
        try {
            getSupabase().auth.onAuthStateChange((event) => {
                if (event === 'SIGNED_IN')  boot();
                else if (event === 'SIGNED_OUT') _teardown();
            });
        } catch (_) { setTimeout(_wireAuth, 200); }
    }

    _wireAuth();
    (async () => { try { await boot(); } catch (_) {} })();

    window.LpInviteButton = { boot, _open: _openModal };
})();
