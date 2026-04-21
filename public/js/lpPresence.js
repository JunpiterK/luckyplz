/*
  Lucky Please — Presence module
  ================================
  Tracks who is online / do-not-disturb / appear-offline in real time,
  matching the UX shipped by Kakao / Line / Discord:

    • online   — green dot. Normal available state. Can receive invites.
    • dnd      — orange dot. "방해금지". Shown as online to friends but
                 game invites are blocked + notifications suppressed.
    • offline  — grey dot. "숨김". Untracked from the presence channel
                 entirely, so other clients see us as fully offline even
                 while the tab is open. manual_status is still persisted
                 in the profiles row so the state survives tab close.

  Architecture:
    1. profiles.manual_status is the user's persistent intent.
    2. A single Supabase Realtime Presence channel (`lp_presence`) is
       joined by every authenticated tab. track() payload includes
       manual_status so other clients can colour the indicator
       correctly (online vs dnd). 'offline' mode UNTRACKS rather than
       tracking — the only way to truly disappear.
    3. A 45-second presence_heartbeat() RPC updates last_seen_at so we
       have a server-side freshness signal if the realtime channel
       flakes.
    4. Public API is observer-based — UI modules register a callback
       and get re-notified whenever the status map changes.

  Scale note: a single global channel means every client sees every
  other online user. Fine for now; at >5k concurrent users we'd
  partition by friendship (per-user channels instead). Defer.
*/
(function(){
    if (window.LpPresence) return;

    const HEARTBEAT_MS = 45 * 1000;

    let _channel       = null;
    let _hbTimer       = null;
    let _myStatus      = 'online';   /* persisted status, mirrored to UI */
    const _statusMap   = new Map();  /* user_id → 'online'|'dnd'|'offline' */
    let _listeners     = [];
    let _booted        = false;
    let _bootingPromise= null;

    /* ---- Boot ------------------------------------------------- */
    /* Idempotent — can be called multiple times (on auth change or
       manually from a page). Second call is a no-op. */
    async function boot() {
        if (_booted) return;
        if (_bootingPromise) return _bootingPromise;
        _bootingPromise = (async () => {
            const user = await getUser();
            if (!user) { _bootingPromise = null; return; }
            const sb = getSupabase();

            /* Read persisted status. If the row doesn't have
               manual_status yet (migration ran but setup never saved),
               default to 'online'. */
            try {
                const { data: prof } = await sb.from('profiles')
                    .select('manual_status').eq('id', user.id).maybeSingle();
                if (prof && prof.manual_status) _myStatus = prof.manual_status;
            } catch (_) { /* ignore — keep default 'online' */ }

            await _connect(user.id);
            _startHeartbeat();
            _booted = true;
        })();
        try { await _bootingPromise; } finally { _bootingPromise = null; }
    }

    async function _connect(myId) {
        const sb = getSupabase();
        _channel = sb.channel('lp_presence', {
            config: { presence: { key: myId } }
        });
        _channel.on('presence', { event: 'sync' }, () => {
            _statusMap.clear();
            const state = _channel.presenceState() || {};
            for (const [userId, entries] of Object.entries(state)) {
                /* Multiple entries = same user from multiple tabs.
                   If ANY tab reports dnd, we show dnd (stricter wins).
                   Otherwise online. */
                let status = 'online';
                for (const e of entries) {
                    const s = (e && e.manual_status) || 'online';
                    if (s === 'dnd') { status = 'dnd'; break; }
                }
                _statusMap.set(userId, status);
            }
            _notify();
        });
        await new Promise((resolve) => {
            _channel.subscribe(async (status) => {
                if (status === 'SUBSCRIBED') {
                    await _track();
                    resolve();
                }
            });
        });
    }

    /* Track (or untrack) based on current _myStatus. 'offline' is the
       appear-offline mode — we explicitly untrack so other clients'
       presence state for us is empty. */
    async function _track() {
        if (!_channel) return;
        try {
            if (_myStatus === 'offline') {
                await _channel.untrack();
            } else {
                await _channel.track({
                    manual_status: _myStatus,
                    online_at: new Date().toISOString()
                });
            }
        } catch (_) { /* channel not subscribed yet — retry on next call */ }
    }

    function _startHeartbeat() {
        if (_hbTimer) clearInterval(_hbTimer);
        _hbTimer = setInterval(() => {
            try { getSupabase().rpc('presence_heartbeat'); } catch (_) {}
        }, HEARTBEAT_MS);
        /* Fire once immediately so last_seen_at reflects this session
           from the start. */
        try { getSupabase().rpc('presence_heartbeat'); } catch (_) {}
    }

    function _notify() {
        for (const cb of _listeners) {
            try { cb({ statusMap: _statusMap, myStatus: _myStatus }); } catch (_) {}
        }
    }

    /* ---- Public API ------------------------------------------ */
    async function setMyStatus(status) {
        if (!['online','dnd','offline'].includes(status)) return { ok:false, error:'bad_status' };
        try {
            const { error } = await getSupabase().rpc('set_manual_status', { p_status: status });
            if (error) return { ok:false, error: error.message };
            _myStatus = status;
            await _track();
            _notify();
            return { ok:true, status };
        } catch (e) {
            return { ok:false, error: String(e) };
        }
    }

    function getMyStatus() { return _myStatus; }

    /* Returns the live status of a given user id:
         'online' | 'dnd' | 'offline'
       'offline' is the default when the user isn't in the presence map
       — either they never connected, they disconnected, or they're in
       appear-offline mode. All three look the same to friends. */
    function getStatus(userId) {
        if (!userId) return 'offline';
        return _statusMap.get(userId) || 'offline';
    }

    /* Subscribe to status map changes. Returns an unsubscribe fn.
       Callback gets { statusMap, myStatus } — statusMap is a live
       reference so caller should snapshot values they need to keep. */
    function onChange(cb) {
        _listeners.push(cb);
        /* Fire once right away so the caller gets the current state
           without needing a separate read. */
        try { cb({ statusMap: _statusMap, myStatus: _myStatus }); } catch (_) {}
        return () => { _listeners = _listeners.filter(x => x !== cb); };
    }

    /* ---- Auto-boot / teardown -------------------------------- */
    /* Boot when supabase-config.js finishes loading and the user is
       authenticated. Also boot on SIGNED_IN events (login tab). On
       SIGNED_OUT, tear down — next login will reboot fresh. */
    function _wireAuth() {
        try {
            getSupabase().auth.onAuthStateChange((event) => {
                if (event === 'SIGNED_IN')        boot();
                else if (event === 'SIGNED_OUT')  _teardown();
            });
        } catch (_) { setTimeout(_wireAuth, 200); }
    }

    function _teardown() {
        if (_hbTimer) { clearInterval(_hbTimer); _hbTimer = null; }
        if (_channel) { try { getSupabase().removeChannel(_channel); } catch (_) {} _channel = null; }
        _statusMap.clear();
        _listeners = [];
        _booted = false;
    }

    window.addEventListener('beforeunload', () => {
        if (_channel) { try { getSupabase().removeChannel(_channel); } catch (_) {} }
    });

    /* Kick boot — non-fatal if called before auth is ready (getUser
       returns null, boot() no-ops). */
    _wireAuth();
    (async () => { try { await boot(); } catch (_) {} })();

    window.LpPresence = {
        boot, setMyStatus, getMyStatus, getStatus, onChange
    };
})();
