/* ============================================================
   lpActivity — tiny client that logs a "game play" event to the
   shared Supabase site-wide counter + fetches honest activity stats
   for the home-page "⚡ 오늘 N번 · 누적 M번" strip.

   Design notes:
   - log() is called automatically by siteFooter.js on every game
     page load, deduped client-side to at most once per 5 minutes
     per game per device (via localStorage). That keeps the counter
     honest while avoiding silly over-inflation from page reloads.
   - stats() returns {today, total, by_game} — used by the home
     page to render the strip with a count-up animation.
   - Every RPC call is best-effort: we never block UI on it, and
     we silently swallow errors so a momentary Supabase blip doesn't
     affect game play.
   ============================================================ */
(function(){
    const DEDUPE_MS = 5 * 60 * 1000;  /* 5 min per game per device */
    const LS_PREFIX = 'lpact:last:';

    function getSb(){
        try {
            return window.getSupabase ? window.getSupabase() : null;
        } catch(_) { return null; }
    }

    function shouldLog(gameId){
        try {
            const k = LS_PREFIX + gameId;
            const prev = parseInt(localStorage.getItem(k) || '0', 10);
            return (Date.now() - prev) > DEDUPE_MS;
        } catch(_) { return true; }
    }
    function markLogged(gameId){
        try { localStorage.setItem(LS_PREFIX + gameId, String(Date.now())); }
        catch(_) {}
    }

    const LpActivity = {
        /**
         * Log a play for this game id. No-op if already logged within
         * the last 5 minutes from this device. Fire-and-forget.
         */
        log(gameId){
            if (!gameId) return;
            if (!shouldLog(gameId)) return;
            const sb = getSb();
            if (!sb) return;
            markLogged(gameId);
            try {
                sb.rpc('log_game_play', { p_game_id: gameId }).then(()=>{}, ()=>{});
            } catch(_) {}
        },

        /**
         * Fetch site-wide activity stats. Returns {today, total, by_game}
         * or null on any failure (caller should hide the strip in that
         * case rather than render zeros that look like the site is dead).
         */
        async stats(){
            const sb = getSb();
            if (!sb) return null;
            try {
                const { data, error } = await sb.rpc('site_activity_stats');
                if (error || !data) return null;
                return data;
            } catch(_) { return null; }
        },

        /**
         * Auto-detect current page game id from the URL (/games/<id>/)
         * and fire a log. Called from siteFooter.js once per page.
         */
        autoLog(){
            const m = location.pathname.match(/\/games\/([a-z0-9-]+)\/?$/i);
            if (!m) return;
            this.log(m[1]);
        }
    };

    window.LpActivity = LpActivity;
})();
