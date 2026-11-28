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

/* =====================================================================
   Cloudflare Turnstile — bot protection on signup/signin/reset.
   =====================================================================
   Empty site key = captcha disabled (forms work as before, no widget).
   To turn it on:
     1. Cloudflare dashboard (https://dash.cloudflare.com) → Turnstile →
        Add a site. Domain: luckyplz.com. Widget mode: Managed.
     2. Copy the SITE KEY → paste below as TURNSTILE_SITE_KEY value.
     3. Copy the SECRET KEY → Supabase dashboard → Authentication →
        Captcha protection → enable, Provider: Turnstile, paste secret.
     4. Bump cache + redeploy. The auth forms now require a Turnstile
        challenge to pass before signup/signin/reset succeed.
   The site key is a PUBLIC value — committing it to the repo is fine
   (it identifies the site, not the validator). The secret key never
   leaves the Cloudflare/Supabase boundary.

   Why Turnstile over hCaptcha/reCAPTCHA: it's free at our scale (1 M
   challenges/month), privacy-respecting (no third-party tracking),
   and integrates natively with Cloudflare Pages where we already
   host. Most challenges resolve invisibly with a managed difficulty
   tier — real users don't see anything; bots get a visible test or
   are blocked outright.
   ===================================================================== */
const TURNSTILE_SITE_KEY = '';

let _supabase = null;

/* Keep the OAuth proof in the tab that started the round trip. Two tabs
   can sign in independently while sharing the resulting Supabase session. */
function authPageStorage() {
    try {
        const shared = window.localStorage, tab = window.sessionStorage;
        for (const store of [shared, tab]) {
            store.setItem('lp_auth_storage_probe', '1');
            store.removeItem('lp_auth_storage_probe');
        }
        const storeFor = key => key.endsWith('-code-verifier') ? tab : shared;
        return {
            getItem: key => storeFor(key).getItem(key),
            setItem: (key, value) => storeFor(key).setItem(key, value),
            removeItem: key => storeFor(key).removeItem(key)
        };
    } catch (_) { return undefined; } // SDK supplies its normal storage fallback.
}

function getSupabase() {
    if (!_supabase) {
        const url = new URL(window.location.href);
        const isAuth = /^\/auth(?:\/index\.html|\/)?$/.test(url.pathname);
        const hash = new URLSearchParams(url.hash.slice(1));
        const legacyReturn = hash.has('access_token') && hash.has('refresh_token');
        // Kakao returns its own code and state. Only the dedicated Kakao
        // callback may exchange that code, even with a pending Google sign-in.
        const kakaoReturn = url.searchParams.has('state');
        _supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
            auth: {
                flowType: legacyReturn ? 'implicit' : 'pkce',
                detectSessionInUrl: !kakaoReturn && (isAuth || legacyReturn),
                storage: isAuth ? authPageStorage() : undefined
            }
        });
    }
    return _supabase;
}

/* Auth helpers */
async function getUser({ throwOnError = false } = {}) {
    const { data, error } = await getSupabase().auth.getUser();
    if (throwOnError && error && error.name !== 'AuthSessionMissingError') throw error;
    return data?.user || null;
}

async function getSession() {
    const { data: { session } } = await getSupabase().auth.getSession();
    return session;
}

/* Login and nickname setup share return destinations, including game-room
   query strings and anchors. Never send a callback back to the login page. */
function safeAuthReturn(value) {
    if (typeof value !== 'string' || !value || value !== value.trim()) return null;
    if (/[\\\x00-\x1f\x7f]/.test(value) || value.startsWith('//')) return null;
    if (!value.startsWith('/') && !/^https?:\/\//i.test(value)) return null;
    try {
        const url = new URL(value, window.location.origin);
        if (url.origin !== window.location.origin || url.username || url.password) return null;
        if (url.pathname.startsWith('//') || /^\/auth(?:\/index(?:\.html)?)?\/?$/i.test(url.pathname)) return null;
        return url.pathname + url.search + url.hash;
    } catch (_) { return null; }
}

async function signOut() {
    const { error } = await getSupabase().auth.signOut({ scope: 'local' });
    return { error };
}

/* Turnstile 관련 helper — OAuth-only 전환 후 사용 사이트가 없지만,
   향후 ReCAPTCHA·Turnstile 를 자체 폼에 다시 도입할 때를 위해
   stub 으로 유지. TURNSTILE_SITE_KEY 가 비어있으면 false 반환. */
function isCaptchaEnabled() {
    return !!TURNSTILE_SITE_KEY;
}
function getTurnstileSiteKey() {
    return TURNSTILE_SITE_KEY;
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
    const meta = user.user_metadata || {};
    return [meta.nickname, meta.profile_nickname, meta.full_name, meta.name, meta.preferred_username, user.email?.split('@')[0]]
        .find(value => typeof value === 'string' && value.trim()) || 'User';
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

/* A missing row starts nickname setup. Login callers request errors
   explicitly so a network failure cannot send members through setup. */
async function _fetchProfile(userId, throwOnError) {
    try {
        const { data, error } = await getSupabase()
            .from('profiles')
            /* Older schemas lack the three consent timestamps. Only a
               missing-column response should retry the legacy projection. */
            .select('id, nickname, email, avatar_url, bio, role, profile_complete, created_at, updated_at, terms_agreed_at, privacy_agreed_at, marketing_agreed_at')
            .eq('id', userId)
            .maybeSingle();
        if (error && (error.code === '42703' || error.code === 'PGRST204')) {
            const { data: fallback, error: fbErr } = await getSupabase()
                .from('profiles')
                .select('id, nickname, email, avatar_url, bio, role, profile_complete, created_at, updated_at')
                .eq('id', userId)
                .maybeSingle();
            if (fbErr) throw fbErr;
            return fallback || null;
        }
        if (error) throw error;
        return data || null;
    } catch (e) {
        if (throwOnError) throw e;
        console.warn('[profile] fetch failed:', e?.message || 'network error');
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
async function ensureProfile({ force = false, throwOnError = false } = {}) {
    const user = await getUser({ throwOnError });
    if (!user) return { signedIn: false };

    if (!force) {
        const cached = _readProfileCache(user.id);
        if (cached && cached.age < PROFILE_CACHE_FRESH_MS) {
            return {
                signedIn: true,
                needsSetup: !cached.profile || !cached.profile.profile_complete,
                profile: cached.profile,
                authUser: user
            };
        }
    }

    const profile = await _fetchProfile(user.id, throwOnError);
    if (profile) _writeProfileCache(user.id, profile);
    else clearProfileCache();

    return {
        signedIn: true,
        needsSetup: !profile || !profile.profile_complete,
        profile: profile,
        authUser: user
    };
}

/* The consent RPC updates a profile row. First-time members therefore
   commit after nickname setup; returning members can commit on callback. */
async function commitAuthConsent(userId, profile) {
    const key = 'lp_pending_consent';
    let raw;
    try { raw = sessionStorage.getItem(key); } catch (_) { return false; }
    if (!raw) return false;
    let pending;
    try { pending = JSON.parse(raw); } catch (_) { return false; }
    if (!userId || pending?.userId !== userId || pending.terms !== true || pending.privacy !== true) return false;
    const now = Date.now();
    if (!Number.isFinite(pending.ts) || pending.ts <= 0 || pending.ts > now) return false;
    // The round trip must finish within the original consent window. After
    // binding it to this user, nickname setup and network retries may take longer.
    const boundInTime = Number.isFinite(pending.boundAt) && pending.boundAt >= pending.ts
        && pending.boundAt <= now && pending.boundAt - pending.ts <= 3600000;
    if (!boundInTime && now - pending.ts > 3600000) return false;
    if (!profile || profile.id !== userId) throw new Error('Profile is not ready for consent.');
    const marketing = pending.marketing === true;
    if (!profile.terms_agreed_at || !profile.privacy_agreed_at || (marketing && !profile.marketing_agreed_at)) {
        const client = getSupabase();
        const { data: auth, error: sessionError } = await client.auth.getSession();
        if (sessionError) throw sessionError;
        if (auth.session?.user?.id !== userId) throw new Error('The signed-in account changed.');
        const { data, error } = await client.rpc('set_consent', {
            p_terms: true,
            p_privacy: true,
            p_marketing: marketing || !!profile.marketing_agreed_at
        }).setHeader('Authorization', 'Bearer ' + auth.session.access_token);
        if (error) throw error;
        if (!data?.terms_agreed_at || !data?.privacy_agreed_at || (marketing && !data.marketing_agreed_at)) {
            throw new Error('Consent was not saved.');
        }
        _writeProfileCache(userId, { ...profile, terms_agreed_at: data.terms_agreed_at,
            privacy_agreed_at: data.privacy_agreed_at, marketing_agreed_at: data.marketing_agreed_at });
    }
    if (sessionStorage.getItem(key) === raw) sessionStorage.removeItem(key);
    return true;
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
            /* Nickname cooldown trigger throws 'nickname_cooldown:<sec>'.
               P0001 covers both this and reserved; we disambiguate by
               substring. The remaining-seconds suffix lets the UI render
               "X days, Y hours remaining" without a separate RPC call. */
            if (msg.includes('nickname_cooldown')) {
                const m = (error.message || '').match(/nickname_cooldown:(\d+)/i);
                const remainingSec = m ? parseInt(m[1], 10) : 0;
                return { ok: false, error: 'cooldown', remainingSec };
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
