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
const SUPABASE_URL = 'https://owvaarmnlednfkgmgerf.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_A8o6dBEEc9YXHQy4KPzURw_9pwVZUAu';

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
