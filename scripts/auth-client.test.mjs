/* node --test scripts/auth-client.test.mjs */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { runInNewContext } from 'node:vm';

const source = readFileSync(new URL('../public/js/supabase-config.js', import.meta.url), 'utf8');
const origin = 'https://luckyplz.test';
const consentKey = 'lp_pending_consent';

function storage() {
    const values = new Map();
    return {
        getItem: key => values.get(key) ?? null,
        setItem: (key, value) => values.set(key, String(value)),
        removeItem: key => values.delete(key)
    };
}

function page(path, { shared = storage(), tab = storage(), client = {} } = {}) {
    let options;
    const window = {
        location: new URL(path, origin), localStorage: shared, sessionStorage: tab,
        supabase: {
            createClient(_url, _key, config) {
                options = config.auth;
                return { ...client, auth: { onAuthStateChange() {}, ...client.auth } };
            }
        }
    };
    const helpers = runInNewContext(source + '\n;({ safeAuthReturn, commitAuthConsent, ensureProfile, signOut })',
        { window, localStorage: shared, sessionStorage: tab, URL, URLSearchParams });
    return { options, tab, ...helpers };
}

test('SDK handles the Google callback, preserves legacy sessions and leaves direct Kakao and game codes alone', () => {
    const google = page('/auth/?code=google-fixture').options;
    assert.equal(google.flowType, 'pkce');
    assert.equal(google.detectSessionInUrl, true);
    const legacy = page('/auth/#access_token=old&refresh_token=old').options;
    assert.equal(legacy.flowType, 'implicit');
    assert.equal(legacy.detectSessionInUrl, true);
    for (const path of ['/auth/?code=kakao-fixture&state=tab-state', '/games/reversi/?code=ABCD']) {
        assert.equal(page(path).options.detectSessionInUrl, false);
    }
});

test('two sign-ins keep separate tab verifiers, including after navigation, and share the final session', () => {
    const shared = storage(), a = page('/auth/', { shared }), b = page('/auth/', { shared });
    const verifier = 'sb-project-auth-token-code-verifier', session = 'sb-project-auth-token';
    a.options.storage.setItem(verifier, 'first');
    b.options.storage.setItem(verifier, 'second');
    const callback = page('/auth/?code=return-fixture', { shared, tab: a.tab }).options.storage;
    assert.equal(callback.getItem(verifier), 'first');
    callback.removeItem(verifier);
    assert.equal(b.options.storage.getItem(verifier), 'second');
    callback.setItem(session, 'signed-in');
    assert.equal(b.options.storage.getItem(session), 'signed-in');
    assert.equal(shared.getItem(verifier), null);
});

test('return paths keep room queries and anchors and avoid external or recursive login destinations', () => {
    const { safeAuthReturn } = page('/auth/');
    const room = '/games/reversi/?r=ABCDEF&lang=ko#invite';
    assert.equal(safeAuthReturn(room), room);
    assert.equal(safeAuthReturn(origin + room), room);
    assert.equal(safeAuthReturn('/auth/setup/?next=%2Fops%2F'), '/auth/setup/?next=%2Fops%2F');
    for (const value of [null, '', 'https://other.test/', '//other.test/', '/auth', '/auth/',
        '/auth/index.html?return=%2Fauth%2F', '/games/../auth/']) {
        assert.equal(safeAuthReturn(value), null);
    }
});

test('ordinary logout revokes the current session only and reports provider failures', async () => {
    const scopes = [];
    const client = { auth: { signOut: async ({ scope }) => {
        scopes.push(scope);
        return { error: scopes.length === 1 ? null : new Error('offline') };
    } } };
    const { signOut } = page('/me/', { client });
    assert.equal((await signOut()).error, null);
    assert.equal((await signOut()).error.message, 'offline');
    assert.deepEqual(scopes, ['local', 'local']);
});

test('consent stays pending until the authenticated account has a confirmed profile write', async () => {
    const sent = [];
    let currentUser = 'member', reply = { ok: true, terms_agreed_at: null, privacy_agreed_at: null };
    const client = {
        auth: { getSession: async () => ({ data: { session: { access_token: 'local-fixture', user: { id: currentUser } } } }) },
        rpc(name, payload) {
            return { setHeader(header, value) {
                sent.push({ name, payload, header, value });
                return Promise.resolve({ data: reply });
            } };
        }
    };
    const { tab, commitAuthConsent } = page('/auth/setup/', { client }), profile = { id: 'member' };
    const pending = { userId: profile.id, ts: Date.now(), terms: true, privacy: true, marketing: true };
    tab.setItem(consentKey, JSON.stringify(pending));
    assert.equal(await commitAuthConsent('another-member', { id: 'another-member' }), false);
    currentUser = 'another-member';
    await assert.rejects(commitAuthConsent(profile.id, profile));
    assert.equal(sent.length, 0);
    currentUser = profile.id;
    await assert.rejects(commitAuthConsent(profile.id, profile));
    assert.ok(tab.getItem(consentKey));
    reply = { ok: true, terms_agreed_at: 'agreed', privacy_agreed_at: 'agreed', marketing_agreed_at: 'agreed' };
    assert.equal(await commitAuthConsent(profile.id, profile), true);
    assert.equal(sent[1].name, 'set_consent');
    assert.equal(sent[1].payload.p_marketing, true);
    assert.equal(sent[1].value, 'Bearer local-fixture');
    assert.equal(tab.getItem(consentKey), null);
    tab.setItem(consentKey, JSON.stringify({ ...pending, marketing: false }));
    assert.equal(await commitAuthConsent(profile.id, { ...profile, ...reply }), true);
    assert.equal(sent.length, 2); // Ordinary re-login preserves the existing marketing choice.
    const old = Date.now() - 7200000;
    tab.setItem(consentKey, JSON.stringify({ ...pending, ts: old }));
    assert.equal(await commitAuthConsent(profile.id, profile), false);
    tab.setItem(consentKey, JSON.stringify({ ...pending, ts: old, boundAt: old + 3000 }));
    assert.equal(await commitAuthConsent(profile.id, profile), true); // Long nickname setup.
});

test('a failed profile lookup stays distinguishable from a new user without a profile', async () => {
    let result = { data: null, error: null };
    const query = { select() { return this; }, eq() { return this; }, maybeSingle: async () => result };
    const client = {
        auth: { getUser: async () => ({ data: { user: { id: 'member' } } }) },
        from: () => query
    };
    const { ensureProfile } = page('/auth/', { client });
    assert.equal((await ensureProfile({ throwOnError: true })).needsSetup, true);
    result = { data: null, error: new Error('network unavailable') };
    await assert.rejects(ensureProfile({ throwOnError: true }), /network unavailable/);
});
