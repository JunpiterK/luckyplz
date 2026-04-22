/*
  Lucky Please - Supabase Configuration
  Shared auth module for all pages
*/

/* Persistent per-device player ID. Stable across sessions/tabs,
   scoped to this browser origin. Used as the stable identity for
   Watch-Together rooms — lets a disconnected guest match their
   previous bingo card / roster slot on rejoin even when the
   host-assigned nickname has drifted (진희2 → 진희3 on zombie
   dedupe). Generated lazily on first read. */
function getLpPlayerId() {
    try {
        let p = localStorage.getItem('lp_pid');
        if (p && p.length >= 10) return p;
        p = 'pid-' + Math.random().toString(36).slice(2, 10) + Math.random().toString(36).slice(2, 10);
        localStorage.setItem('lp_pid', p);
        return p;
    } catch (_) {
        /* private mode / storage blocked — fall back to session-only */
        if (!window._lpPidSession) {
            window._lpPidSession = 'pid-sess-' + Math.random().toString(36).slice(2, 10);
        }
        return window._lpPidSession;
    }
}
/* Seoul (ap-northeast-2) region — migrated 2026-04-21 from Sydney
   (ap-southeast-2). Primary audience is Korean, and the Sydney box
   added ~250 ms of avoidable RTT to every request. The old Sydney
   project (owvaarmnlednfkgmgerf) is kept alive for ~2 weeks as a
   rollback safety net, then deleted. */
const SUPABASE_URL = 'https://jkrpxijybuljdxkrbsan.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_Ypa1NMQCVGxFWidBOd5iEA_ECBldTAb';

let _supabase = null;

function getSupabase() {
    if (!_supabase) {
        _supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    }
    return _supabase;
}

/* Auth helpers */
async function getUser() {
    const { data: { user } } = await getSupabase().auth.getUser();
    return user;
}

async function getSession() {
    const { data: { session } } = await getSupabase().auth.getSession();
    return session;
}

async function signUp(email, password, nickname) {
    const { data, error } = await getSupabase().auth.signUp({
        email,
        password,
        options: {
            data: { nickname },
            emailRedirectTo: window.location.origin + '/auth/?verified=1'
        }
    });
    return { data, error };
}

async function signIn(email, password) {
    const { data, error } = await getSupabase().auth.signInWithPassword({
        email,
        password
    });
    return { data, error };
}

async function signOut() {
    const { error } = await getSupabase().auth.signOut();
    return { error };
}

async function resetPassword(email) {
    const { data, error } = await getSupabase().auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + '/auth/?reset=1'
    });
    return { data, error };
}

/* Listen for auth changes */
function onAuthChange(callback) {
    getSupabase().auth.onAuthStateChange((event, session) => {
        callback(event, session);
    });
}

/* Get display name */
function getDisplayName(user) {
    if (!user) return null;
    return user.user_metadata?.nickname || user.email?.split('@')[0] || 'User';
}

/* ================================================================
   Profile helpers — nickname/avatar identity anchored in the
   `profiles` table (see supabase/schema.sql §3).

   Design goals:
   • Minimise round-trips. Profile is cached in localStorage with a
     5-min TTL; authed pages don't hit the DB on every navigation.
   • Stale-while-revalidate: cache is returned immediately, then a
     background fetch refreshes in the common case the cache is fresh
     (<30s old we skip the refresh entirely).
   • Cache is keyed by user id, cleared on sign-out.
   • No sensitive fields (email is private per-user, but stored in
     the cache only for the owner's own profile — never cross-user).
   ================================================================ */

const PROFILE_CACHE_KEY = 'lp_profile_cache_v1';
const PROFILE_CACHE_TTL_MS = 5 * 60 * 1000;   /* 5 min hard TTL */
const PROFILE_CACHE_FRESH_MS = 30 * 1000;     /* <30s → no refresh */

function _readProfileCache(userId) {
    try {
        const raw = localStorage.getItem(PROFILE_CACHE_KEY);
        if (!raw) return null;
        const c = JSON.parse(raw);
        if (!c || c.userId !== userId) return null;
        if (Date.now() - c.savedAt > PROFILE_CACHE_TTL_MS) return null;
        return { profile: c.profile, age: Date.now() - c.savedAt };
    } catch (_) { return null; }
}

function _writeProfileCache(userId, profile) {
    try {
        localStorage.setItem(PROFILE_CACHE_KEY, JSON.stringify({
            userId, profile, savedAt: Date.now()
        }));
    } catch (_) { /* private mode / quota — silent fail */ }
}

function clearProfileCache() {
    try { localStorage.removeItem(PROFILE_CACHE_KEY); } catch (_) {}
}

/* Fetch profile from DB. Returns null if no row exists (user hasn't
   completed setup yet). Never throws — callers get null on any
   network/permission failure and can handle gracefully. */
async function _fetchProfile(userId) {
    try {
        const { data, error } = await getSupabase()
            .from('profiles')
            .select('id, nickname, email, avatar_url, bio, role, profile_complete, created_at, updated_at')
            .eq('id', userId)
            .maybeSingle();
        if (error) { console.warn('[profile] fetch error:', error.message); return null; }
        return data || null;
    } catch (e) {
        console.warn('[profile] fetch exception:', e);
        return null;
    }
}

/* Primary entry point used by every page that cares about auth
   state. Resolves to:
     { signedIn:false }                       — no session
     { signedIn:true, needsSetup:true,  ... } — logged in, no profile row OR profile_complete=false
     { signedIn:true, needsSetup:false, profile:{...} } — complete
   Callers can decide whether to redirect to /auth/setup/ or just
   render a passive "complete your profile" banner. */
async function ensureProfile({ force = false } = {}) {
    const user = await getUser();
    if (!user) return { signedIn: false };

    if (!force) {
        const cached = _readProfileCache(user.id);
        if (cached && cached.age < PROFILE_CACHE_FRESH_MS) {
            return {
                signedIn: true,
                needsSetup: !cached.profile || !cached.profile.profile_complete,
                profile: cached.profile
            };
        }
    }

    const profile = await _fetchProfile(user.id);
    if (profile) _writeProfileCache(user.id, profile);
    else clearProfileCache();

    return {
        signedIn: true,
        needsSetup: !profile || !profile.profile_complete,
        profile: profile,
        authUser: user
    };
}

/* Debounced availability RPC. Handy for live typing feedback. Strict
   3-case response shape — UI branches on `reason` to localise. */
async function checkNicknameAvailable(candidate) {
    if (!candidate || typeof candidate !== 'string') {
        return { available: false, reason: 'invalid' };
    }
    try {
        const { data, error } = await getSupabase()
            .rpc('check_nickname_available', { candidate: candidate });
        if (error) return { available: false, reason: 'error', err: error.message };
        const row = Array.isArray(data) ? data[0] : data;
        return {
            available: !!(row && row.available),
            reason: row && row.reason ? row.reason : null
        };
    } catch (e) {
        return { available: false, reason: 'error', err: String(e) };
    }
}

/* Upsert-flavoured save used by the setup page and profile editor.
   Client-side validation first (cheap, fast UX) then trusts the DB
   CHECK + trigger to enforce the same rules server-side. Both layers
   share the same regex/length bounds so an attacker can't bypass the
   client checks and hit the DB with invalid data. */
function _validateNicknameLocal(nickname) {
    if (!nickname || typeof nickname !== 'string') return 'invalid';
    if (nickname.length < 2 || nickname.length > 20) return 'invalid';
    if (!/^[A-Za-z0-9_\-가-힣]+$/.test(nickname)) return 'invalid';
    return null;
}

async function saveProfile({ nickname, email, avatar_url, bio }) {
    const user = await getUser();
    if (!user) return { ok: false, error: 'not_authenticated' };

    const localErr = _validateNicknameLocal(nickname);
    if (localErr) return { ok: false, error: localErr };

    const payload = {
        id: user.id,
        nickname: nickname.trim(),
        email: (email || user.email || '').trim() || null,
        avatar_url: avatar_url || null,
        bio: (bio || '').trim() || null,
        profile_complete: true
    };
    try {
        const { data, error } = await getSupabase()
            .from('profiles')
            .upsert(payload, { onConflict: 'id' })
            .select()
            .single();
        if (error) {
            /* Map DB errors to stable codes the UI can branch on. */
            const msg = String(error.message || '').toLowerCase();
            if (msg.includes('duplicate key') || error.code === '23505') {
                return { ok: false, error: 'taken' };
            }
            if (msg.includes('nickname_reserved') || error.code === 'P0001') {
                return { ok: false, error: 'reserved' };
            }
            if (error.code === '23514' || msg.includes('check constraint')) {
                return { ok: false, error: 'invalid' };
            }
            return { ok: false, error: 'db', detail: error.message };
        }
        _writeProfileCache(user.id, data);
        return { ok: true, profile: data };
    } catch (e) {
        return { ok: false, error: 'exception', detail: String(e) };
    }
}

/* Tie profile cache to auth lifecycle. Any signOut event (including
   from another tab via onAuthStateChange) clears the cached profile
   so a subsequent login doesn't see stale data. */
(function wireAuthCacheReset() {
    try {
        getSupabase().auth.onAuthStateChange((event) => {
            if (event === 'SIGNED_OUT') clearProfileCache();
        });
    } catch (_) { /* SDK might not be loaded yet on some pages */ }
})();
