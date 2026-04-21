/*
  Lucky Please — Game Invite module
  ==================================
  End-to-end flow for "host invites a friend to an opened game":

    Host side:                              Guest side:
    ----------                              -----------
    LpInvite.sendInvite(to, type, url) ──►  inbox channel INSERT
           │                                     │
           │                                     ▼
           │                                GLOBAL TOAST with
           │                                [수락] [거절] buttons
           │                                     │
           │    respond_game_invite RPC  ◄───────┘
           ▼
    onInviteResponse(cb) fires {action, ...}
    Host shows "XXX가 수락했어요" and knows the guest
    is about to join the room.

  Design choices:
    • The toast lives on EVERY page (via siteFooter.js) so the guest
      sees it whether they're on /games/lotto/, /messages/, /me/, or
      the home page. Accept navigates to the host's game URL.
    • One active toast at a time — if a second invite arrives while
      the first is on screen, the first is auto-dismissed (latest
      wins). Stale invites are less confusing than a queue.
    • 2-minute server-side TTL; the client shows a 60-second countdown
      so the user knows it'll disappear. Server-side expiry is
      authoritative — late Accept returns {ok:false, error:'expired'}.
    • Sender presence gate: we don't send the invite if
      LpPresence.getStatus(target) !== 'online'. DB also enforces via
      RLS + RPC so a malicious client can't bypass.
    • Self-invite guard on server so host-clicking-themselves is a
      no-op.
*/
(function(){
    if (window.LpInvite) return;

    let _channel       = null;
    let _booted        = false;
    let _bootingPromise= null;
    let _listeners     = { incoming: [], response: [] };
    let _toastEl       = null;
    let _toastTimer    = null;
    let _toastCountdown= null;

    /* ---- Boot --------------------------------------------- */
    async function boot() {
        if (_booted) return;
        if (_bootingPromise) return _bootingPromise;
        _bootingPromise = (async () => {
            const user = await getUser();
            if (!user) { _bootingPromise = null; return; }
            const sb = getSupabase();

            /* Two subscriptions piggybacked on one channel.
               INSERT where to_id=me   → toast
               UPDATE where from_id=me → "friend responded" callback */
            _channel = sb.channel('lp_invite_' + user.id.slice(0,8));

            _channel.on('postgres_changes', {
                event: 'INSERT', schema: 'public', table: 'game_invites',
                filter: 'to_id=eq.' + user.id
            }, (payload) => {
                _handleIncoming(payload.new);
            });

            _channel.on('postgres_changes', {
                event: 'UPDATE', schema: 'public', table: 'game_invites',
                filter: 'from_id=eq.' + user.id
            }, (payload) => {
                const row = payload.new;
                /* Only fire for terminal states — pending→pending updates
                   would be noise. */
                if (row && row.status && row.status !== 'pending') {
                    for (const cb of _listeners.response) {
                        try { cb(row); } catch (_) {}
                    }
                }
            });

            await new Promise(r => _channel.subscribe(s => { if (s === 'SUBSCRIBED') r(); }));
            _booted = true;
        })();
        try { await _bootingPromise; } finally { _bootingPromise = null; }
    }

    async function _handleIncoming(row) {
        if (!row || row.status !== 'pending') return;

        /* Fire onIncoming listeners first — pages can suppress the
           default toast if they want to show their own UI. */
        let suppressed = false;
        for (const cb of _listeners.incoming) {
            try { if (cb(row) === true) suppressed = true; } catch (_) {}
        }
        if (suppressed) return;

        /* DND mode — persist no toast + auto-decline after a tick so
           the host gets a fast signal. */
        if (window.LpPresence && LpPresence.getMyStatus() === 'dnd') {
            respond(row.id, 'decline');
            return;
        }

        _showToast(row);
    }

    /* ---- Toast UI ---------------------------------------- */
    /* Built from scratch (no library) so it works on every page
       without extra CSS dependencies. Lives at the top-right, slides
       in, dismisses on click outside / escape / timeout. */
    function _ensureToastStyles() {
        if (document.getElementById('lp-invite-toast-css')) return;
        const css = `
        .lp-invite-toast{
            position:fixed;top:18px;right:18px;z-index:9999;
            min-width:280px;max-width:360px;
            background:linear-gradient(160deg,rgba(22,22,42,.95),rgba(12,12,28,.98));
            border:1px solid rgba(0,217,255,.35);border-radius:14px;
            box-shadow:0 16px 40px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.05);
            backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
            color:#fff;font-family:'Noto Sans KR',sans-serif;
            padding:14px 16px;animation:lpIvSlide .22s ease-out;
        }
        @keyframes lpIvSlide{from{opacity:0;transform:translateX(24px)}to{opacity:1;transform:translateX(0)}}
        .lp-invite-toast .lp-iv-head{display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:.72em;letter-spacing:.08em;text-transform:uppercase;color:rgba(0,217,255,.85);font-weight:800}
        .lp-invite-toast .lp-iv-body{font-size:.96em;line-height:1.45;margin-bottom:4px;font-weight:600}
        .lp-invite-toast .lp-iv-nick{color:#FFE66D;font-weight:900}
        .lp-invite-toast .lp-iv-game{color:#00D9FF;font-weight:900}
        .lp-invite-toast .lp-iv-timer{font-size:.72em;color:rgba(255,255,255,.35);margin-bottom:10px}
        .lp-invite-toast .lp-iv-actions{display:flex;gap:8px}
        .lp-invite-toast button{
            flex:1;padding:9px 12px;border-radius:10px;border:0;cursor:pointer;
            font-family:inherit;font-size:.88em;font-weight:800;letter-spacing:.02em;
            transition:filter .15s,transform .12s;
        }
        .lp-invite-toast button:active{transform:translateY(1px)}
        .lp-invite-toast .lp-iv-accept{background:linear-gradient(135deg,#00FF88,#00D9FF);color:#00201A}
        .lp-invite-toast .lp-iv-accept:hover{filter:brightness(1.08)}
        .lp-invite-toast .lp-iv-decline{background:rgba(255,255,255,.07);color:rgba(255,255,255,.85);border:1px solid rgba(255,255,255,.1)}
        .lp-invite-toast .lp-iv-decline:hover{background:rgba(255,255,255,.12)}
        @media (max-width:560px){
            .lp-invite-toast{top:auto;bottom:86px;right:10px;left:10px;max-width:none}
        }
        `;
        const style = document.createElement('style');
        style.id = 'lp-invite-toast-css';
        style.textContent = css;
        document.head.appendChild(style);
    }

    function _dismissToast() {
        if (_toastTimer)      { clearTimeout(_toastTimer);   _toastTimer = null; }
        if (_toastCountdown)  { clearInterval(_toastCountdown); _toastCountdown = null; }
        if (_toastEl)         { _toastEl.remove(); _toastEl = null; }
    }

    async function _showToast(inv) {
        _ensureToastStyles();
        _dismissToast();

        /* Look up sender nickname + avatar from profiles. If the fetch
           fails, fall back to a generic label — the toast still works. */
        let fromNick = '친구', fromAvatar = null;
        try {
            const { data } = await getSupabase().from('profiles')
                .select('nickname, avatar_url').eq('id', inv.from_id).maybeSingle();
            if (data) { fromNick = data.nickname || fromNick; fromAvatar = data.avatar_url; }
        } catch (_) {}

        const game = _humanGame(inv.game_type);
        const el = document.createElement('div');
        el.className = 'lp-invite-toast';
        el.setAttribute('role', 'alert');
        el.innerHTML =
            '<div class="lp-iv-head">🎮 게임 초대</div>' +
            '<div class="lp-iv-body"><span class="lp-iv-nick">' + _esc(fromNick) + '</span>님이 ' +
                '<span class="lp-iv-game">' + _esc(game) + '</span> 에 초대했어요!</div>' +
            '<div class="lp-iv-timer" data-remaining="60">60초 남음</div>' +
            '<div class="lp-iv-actions">' +
                '<button class="lp-iv-decline" type="button">거절</button>' +
                '<button class="lp-iv-accept" type="button">수락</button>' +
            '</div>';
        document.body.appendChild(el);
        _toastEl = el;

        const timerEl = el.querySelector('[data-remaining]');
        let left = 60;
        _toastCountdown = setInterval(() => {
            left -= 1;
            if (left <= 0) { _dismissToast(); return; }
            if (timerEl) timerEl.textContent = left + '초 남음';
        }, 1000);

        el.querySelector('.lp-iv-accept').addEventListener('click', async () => {
            _dismissToast();
            const r = await respond(inv.id, 'accept');
            if (r.ok && r.game_url) {
                location.assign(r.game_url);
            } else if (r.error === 'expired') {
                _flash('초대가 만료됐어요.');
            } else if (!r.ok) {
                _flash('수락 실패: ' + (r.error || 'unknown'));
            }
        });
        el.querySelector('.lp-iv-decline').addEventListener('click', async () => {
            _dismissToast();
            respond(inv.id, 'decline');
        });

        /* Auto-dismiss at 60s (server TTL is 120s, we show earlier). */
        _toastTimer = setTimeout(_dismissToast, 60 * 1000);
    }

    /* Super-simple flash for inline errors (after accept/decline). */
    function _flash(msg) {
        _ensureToastStyles();
        const el = document.createElement('div');
        el.className = 'lp-invite-toast';
        el.innerHTML = '<div class="lp-iv-body">' + _esc(msg) + '</div>';
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 2500);
    }

    function _esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
            .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
    }

    /* game_type → human-readable Korean label. If we ship a new game,
       add an entry here. Fallback is the raw type string. */
    function _humanGame(type) {
        const map = {
            lotto:'로또', roulette:'룰렛', ladder:'사다리', dice:'주사위',
            team:'팀 나누기', bingo:'빙고', 'car-racing':'카레이싱'
        };
        return map[type] || type || '게임';
    }

    /* ---- Public API ----------------------------------------- */
    /* Create a new invite. Returns { ok, id? , error? }. Client is
       expected to filter the target by LpPresence.getStatus before
       calling, but the DB enforces "no invites to offline targets" as
       a safety net. */
    async function sendInvite(targetId, gameType, gameUrl) {
        if (!targetId || !gameType || !gameUrl) return { ok:false, error:'missing_params' };
        try {
            const { data, error } = await getSupabase().rpc('send_game_invite', {
                p_to_id: targetId, p_game_type: gameType, p_game_url: gameUrl
            });
            if (error) {
                const m = (error.message || '').toLowerCase();
                if (m.includes('not_friends'))      return { ok:false, error:'not_friends' };
                if (m.includes('recipient_offline'))return { ok:false, error:'offline' };
                if (m.includes('self_invite'))      return { ok:false, error:'self' };
                return { ok:false, error: error.message };
            }
            return { ok:true, id: data };
        } catch (e) {
            return { ok:false, error: String(e) };
        }
    }

    async function respond(inviteId, action) {
        try {
            const { data, error } = await getSupabase().rpc('respond_game_invite', {
                p_invite_id: inviteId, p_action: action
            });
            if (error) return { ok:false, error: error.message };
            return data || { ok:true };
        } catch (e) { return { ok:false, error: String(e) }; }
    }

    async function cancel(inviteId) {
        try {
            const { data, error } = await getSupabase().rpc('cancel_game_invite', {
                p_invite_id: inviteId
            });
            if (error) return { ok:false, error: error.message };
            return { ok:true, cancelled: !!data };
        } catch (e) { return { ok:false, error: String(e) }; }
    }

    /* Subscribe to incoming invites — return true from the callback
       to SUPPRESS the default toast (e.g. a page might want its own
       dialog). */
    function onIncoming(cb) {
        _listeners.incoming.push(cb);
        return () => { _listeners.incoming = _listeners.incoming.filter(x => x !== cb); };
    }

    /* Subscribe to responses for invites I sent. Callback receives the
       updated game_invites row (status = accepted / declined /
       cancelled / expired). */
    function onResponse(cb) {
        _listeners.response.push(cb);
        return () => { _listeners.response = _listeners.response.filter(x => x !== cb); };
    }

    /* ---- Auto-boot ------------------------------------------- */
    function _wireAuth() {
        try {
            getSupabase().auth.onAuthStateChange((event) => {
                if (event === 'SIGNED_IN') boot();
                else if (event === 'SIGNED_OUT') _teardown();
            });
        } catch (_) { setTimeout(_wireAuth, 200); }
    }

    function _teardown() {
        if (_channel) { try { getSupabase().removeChannel(_channel); } catch (_) {} _channel = null; }
        _dismissToast();
        _booted = false;
    }

    _wireAuth();
    (async () => { try { await boot(); } catch (_) {} })();

    window.LpInvite = { boot, sendInvite, respond, cancel, onIncoming, onResponse };
})();
