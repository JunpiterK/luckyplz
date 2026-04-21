// Supabase Edge Function — Kakao OAuth code ↔ id_token exchange
// =============================================================
// Why this exists:
//   Supabase's built-in Kakao OAuth provider (signInWithOAuth) hard-
//   codes the `account_email` scope at the server layer. Non-business-
//   verified Kakao apps can't grant that scope, so personal-developer
//   apps (like ours) always fail with KOE205 before the consent screen
//   even renders. See https://github.com/supabase/supabase/issues/36878.
//
// Our workaround:
//   1. Client (auth/index.html handleKakaoLogin) redirects the user
//      straight to kauth.kakao.com/oauth/authorize with response_type=
//      code and scope=openid+profile_nickname+profile_image — no
//      account_email.
//   2. Kakao bounces back to /auth/?code=... with an authorization code.
//   3. Client POSTs {code, redirect_uri} to THIS function.
//   4. This function calls kauth.kakao.com/oauth/token with the client
//      secret (kept server-side here) and returns { id_token }.
//   5. Client calls supabase.auth.signInWithIdToken({provider:'kakao',
//      token: id_token, nonce}) — Supabase verifies the Kakao-signed
//      id_token and creates a session exactly as it would for any other
//      OIDC provider. Bypasses the hardcoded-scope wall entirely.
//
// Required env vars (set via Supabase dashboard → Edge Functions → Secrets):
//   KAKAO_CLIENT_ID     — REST API Key from Kakao Developers (public,
//                         same value the client sends in the authorize
//                         URL; we keep it server-side only to avoid
//                         round-tripping it in request bodies)
//   KAKAO_CLIENT_SECRET — Client Secret generated in Kakao's
//                         "플랫폼 키 → REST API 키 → 클라이언트 시크릿"
//                         page. MUST stay server-side.
//
// CORS:
//   luckyplz.com is the only expected origin. Allow just that in prod
//   to prevent other sites from spending authorization codes (which
//   would bind a foreign user's Supabase session to our Kakao account).

const ALLOWED_ORIGINS = new Set([
    'https://luckyplz.com',
    'http://localhost:8080',       // local dev
    'http://127.0.0.1:8080',
]);

function corsHeaders(origin: string | null): Record<string, string> {
    const allow = origin && ALLOWED_ORIGINS.has(origin) ? origin : 'https://luckyplz.com';
    return {
        'Access-Control-Allow-Origin': allow,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'content-type, authorization',
        'Access-Control-Max-Age': '86400',
    };
}

function json(body: unknown, status: number, origin: string | null): Response {
    return new Response(JSON.stringify(body), {
        status,
        headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' },
    });
}

// deno-lint-ignore no-explicit-any
Deno.serve(async (req: Request): Promise<Response> => {
    const origin = req.headers.get('origin');

    // Preflight
    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }
    if (req.method !== 'POST') {
        return json({ error: 'method_not_allowed' }, 405, origin);
    }

    const clientId = Deno.env.get('KAKAO_CLIENT_ID');
    const clientSecret = Deno.env.get('KAKAO_CLIENT_SECRET');
    if (!clientId || !clientSecret) {
        return json({ error: 'server_misconfigured' }, 500, origin);
    }

    let body: { code?: string; redirect_uri?: string };
    try {
        body = await req.json();
    } catch {
        return json({ error: 'invalid_json' }, 400, origin);
    }
    const { code, redirect_uri } = body;
    if (!code || !redirect_uri) {
        return json({ error: 'missing_params' }, 400, origin);
    }

    // Exchange code for tokens at Kakao
    const form = new URLSearchParams({
        grant_type: 'authorization_code',
        client_id: clientId,
        client_secret: clientSecret,
        redirect_uri: redirect_uri,
        code: code,
    });

    let kakaoRes: Response;
    try {
        kakaoRes = await fetch('https://kauth.kakao.com/oauth/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: form.toString(),
        });
    } catch (e) {
        return json({ error: 'kakao_unreachable', detail: String(e) }, 502, origin);
    }

    const tokenData = await kakaoRes.json().catch(() => ({}));
    if (!kakaoRes.ok) {
        // Relay Kakao's error verbatim so the client can log it
        return json({ error: 'kakao_error', kakao: tokenData }, kakaoRes.status, origin);
    }
    if (!tokenData.id_token) {
        // No id_token means OpenID Connect isn't enabled on the Kakao
        // app, or the scope didn't include `openid`. Surface that.
        return json({ error: 'no_id_token', hint: 'enable OIDC on Kakao + include openid scope' }, 400, origin);
    }

    // Return only what the client needs for signInWithIdToken.
    return json({
        id_token: tokenData.id_token,
        access_token: tokenData.access_token ?? null,
        token_type: tokenData.token_type ?? null,
        expires_in: tokenData.expires_in ?? null,
    }, 200, origin);
});
