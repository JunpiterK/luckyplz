/* /api/p — 1st-party 방문 통계 수집기 (Cloudflare Pages Function)
 *
 * lpTrack.js 가 페이지마다 보내는 작은 JSON 을 받아, Cloudflare 가 아는
 * 위치(국가·지역·도시·시간대·통신사)와 기기 정보를 붙여 Supabase RPC
 * lp_stat_ingest 로 넘긴다. 응답은 언제나 204 — 실패해도 페이지는 모른다.
 *
 * - IP 는 어디에도 저장하지 않는다(Cloudflare 가 IP 로 추정한 지명만 쓴다)
 * - 봇 UA 는 여기서 버린다. 데이터센터 IP 는 버리지 않고 dc 표시만 해서
 *   상황판에서 켜고 끌 수 있게 한다
 * - 이 파일이 있는 것만으로 Pages 가 /api/* 만 Function 으로 보낸다.
 *   정적 페이지는 그대로 무료 정적 서빙이다
 * - 키는 supabase-config.js 와 같은 공개(publishable) 키다. RPC 는 쓰기만 열려 있고 읽기는 관리자 전용
 */
const SB_URL = 'https://jkrpxijybuljdxkrbsan.supabase.co';
const SB_KEY = 'sb_publishable_Ypa1NMQCVGxFWidBOd5iEA_ECBldTAb';

const BOT = /bot\b|bot\/|crawl|spider|slurp|mediapartners|adsbot|apis-google|feedfetcher|google-read-aloud|lighthouse|pagespeed|gtmetrix|pingdom|uptime|headless|phantom|puppeteer|playwright|selenium|python|curl\/|wget|go-http|java\/|okhttp|axios|node-fetch|httpclient|facebookexternalhit|preview|scanner|yandex|baiduspider|petalbot|bytespider|semrush|ahrefs/i;
const DC = /amazon|aws|google cloud|google llc|microsoft|azure|digitalocean|ovh|hetzner|linode|akamai connected|vultr|choopa|oracle|alibaba|tencent|huawei cloud|contabo|scaleway|leaseweb|m247|datacamp|cdn77|kamatera|psychz|colocrossing|quadranet|zenlayer|hostinger|ionos/i;

/* 참조 호스트 → 유입 이름. 위에서부터 먼저 맞는 것 */
const SRC = [
    [/(^|\.)gemini\.google\.com$/, 'gemini'],
    [/(^|\.)google\.[a-z.]+$/, 'google'],
    [/(^|\.)naver\.com$/, 'naver'],
    [/(^|\.)daum\.net$/, 'daum'],
    [/(^|\.)kakao\.com$/, 'kakao'],
    [/(^|\.)bing\.com$/, 'bing'],
    [/(^|\.)yahoo\.[a-z.]+$/, 'yahoo'],
    [/(^|\.)duckduckgo\.com$/, 'duckduckgo'],
    [/(^|\.)baidu\.com$/, 'baidu'],
    [/(^|\.)yandex\.[a-z.]+$/, 'yandex'],
    [/(^|\.)ecosia\.org$/, 'ecosia'],
    [/(^|\.)(chatgpt\.com|openai\.com)$/, 'chatgpt'],
    [/(^|\.)perplexity\.ai$/, 'perplexity'],
    [/(^|\.)claude\.ai$/, 'claude'],
    [/(^|\.)copilot\.microsoft\.com$/, 'copilot'],
    [/(^|\.)(facebook\.com|fb\.com)$/, 'facebook'],
    [/(^|\.)instagram\.com$/, 'instagram'],
    [/^t\.co$|(^|\.)(x|twitter)\.com$/, 'x'],
    [/(^|\.)(youtube\.com|youtu\.be)$/, 'youtube'],
    [/(^|\.)reddit\.com$/, 'reddit'],
    [/(^|\.)threads\.(net|com)$/, 'threads'],
    [/(^|\.)tiktok\.com$/, 'tiktok'],
    [/(^|\.)line\.me$/, 'line'],
    [/(^|\.)band\.us$/, 'band'],
    [/(^|\.)everytime\.kr$/, 'everytime'],
    [/(^|\.)(discord\.com|discordapp\.com)$/, 'discord'],
    [/(^|\.)(t\.me|telegram\.org)$/, 'telegram'],
];
/* 검색 결과 주소에서 검색어를 꺼낼 쿼리 이름 */
const KW = { google: 'q', naver: 'query', daum: 'q', bing: 'q', yahoo: 'p', duckduckgo: 'q', baidu: 'wd', yandex: 'text', ecosia: 'q' };

const s = (v, n) => (typeof v === 'string' ? v.slice(0, n) : '');
const int = (v, lo, hi) => (Number.isFinite(+v) ? Math.min(hi, Math.max(lo, Math.round(+v))) : null);
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function device(u, touch) {
    const inapp = /KAKAOTALK/i.test(u) ? 'kakaotalk'
        : /NAVER\(inapp|NAVER\//.test(u) ? 'naver'
        : /DaumApps/.test(u) ? 'daum'
        : /Instagram/.test(u) ? 'instagram'
        : /FBAN|FBAV|FB_IAB/.test(u) ? 'facebook'
        : /\bLine\//.test(u) ? 'line'
        : /everytimeApp/i.test(u) ? 'everytime'
        : /BytedanceWebview|musical_ly|TikTok/i.test(u) ? 'tiktok'
        : /Twitter/i.test(u) ? 'x'
        : /; wv\)/.test(u) ? 'webview' : '';
    let os = /Windows/.test(u) ? 'Windows' : /iPhone|iPad|iPod/.test(u) ? 'iOS' : /Android/.test(u) ? 'Android'
        : /CrOS/.test(u) ? 'ChromeOS' : /Macintosh|Mac OS X/.test(u) ? 'macOS' : /Linux/.test(u) ? 'Linux' : 'Other';
    const br = /SamsungBrowser/.test(u) ? 'Samsung' : /Whale\//.test(u) ? 'Whale' : /Edg(A|iOS)?\//.test(u) ? 'Edge'
        : /OPR\/|Opera/.test(u) ? 'Opera' : /YaBrowser/.test(u) ? 'Yandex' : /Firefox|FxiOS/.test(u) ? 'Firefox'
        : /CriOS|Chrome\//.test(u) ? 'Chrome' : /Safari\//.test(u) ? 'Safari' : 'Other';
    let dev = /iPad|Tablet|PlayBook|Silk/.test(u) || (/Android/.test(u) && !/Mobile/.test(u)) ? 'tablet'
        : /Mobi|iPhone|iPod|Android/.test(u) ? 'mobile' : 'desktop';
    if (os === 'macOS' && touch > 1) { dev = 'tablet'; os = 'iOS'; }   // 데스크톱 UA 를 쓰는 iPad
    return { inapp, os, br, dev };
}

function source(refUrl, utm, inapp) {
    if (utm) return { src: utm.toLowerCase().replace(/[^a-z0-9._-]/g, '').slice(0, 60) || 'utm' };
    let host = '', u = null;
    try { u = new URL(refUrl); host = u.hostname.replace(/^www\.|^m\./, ''); } catch (_) {}
    if (!host) return { src: inapp && inapp !== 'webview' ? inapp : 'direct' };
    for (const [re, name] of SRC) {
        if (re.test(host)) {
            const k = KW[name] && u.searchParams.get(KW[name]);
            return { src: name, ref: host, kw: k ? k.trim().slice(0, 80) : '' };
        }
    }
    return { src: host.slice(0, 60), ref: host };
}

export async function onRequest(ctx) {
    const { request } = ctx;
    const done = new Response(null, { status: 204, headers: { 'cache-control': 'no-store' } });
    if (request.method !== 'POST') return done;

    const ua = request.headers.get('user-agent') || '';
    if (ua.length < 20 || BOT.test(ua)) return done;
    const origin = request.headers.get('origin');
    if (origin && !/^https:\/\/(www\.)?luckyplz\.com$/.test(origin)) return done;

    let b;
    try {
        const t = await request.text();
        if (t.length > 8000) return done;
        b = JSON.parse(t);
    } catch (_) { return done; }
    if (!b || !UUID.test(b.id) || !UUID.test(b.sid) || !UUID.test(b.vid)) return done;

    const cf = request.cf || {};
    const d = device(ua, int(b.tch, 0, 20) || 0);
    const src = b.sp === 1 ? source(s(b.ref, 400), s(b.utm, 60), d.inapp) : {};
    const asorg = s(cf.asOrganization, 80);
    const p = {
        id: b.id, sid: b.sid, vid: b.vid,
        path: s(b.path, 200) || '/',
        sp: int(b.sp, 1, 9999),
        dur: int(b.dur, 0, 21600000) || 0,
        new: b.new === true, vn: int(b.vn, 1, 999999), me: b.me === true,
        lang: s(b.lang, 8), blang: s(b.blang, 16),
        vw: int(b.vw, 0, 32000), vh: int(b.vh, 0, 32000),
        src: src.src || '', ref: src.ref || '', kw: src.kw || '', cmp: s(b.cmp, 80),
        country: s(cf.country, 2), region: s(cf.region, 80), city: s(cf.city, 80),
        tz: s(cf.timezone, 50), asorg, dc: !!asorg && DC.test(asorg),
        dev: d.dev, os: d.os, br: d.br, inapp: d.inapp,
    };
    if (Array.isArray(b.ev) && b.ev.length) {
        p.ev = b.ev.slice(0, 20).map((e) => ({
            n: s(e && e.n, 32), g: s(e && e.g, 32),
            p: e && e.p && typeof e.p === 'object' && !Array.isArray(e.p) ? e.p : undefined,
        }));
    }

    ctx.waitUntil(fetch(SB_URL + '/rest/v1/rpc/lp_stat_ingest', {
        method: 'POST',
        headers: { apikey: SB_KEY, 'content-type': 'application/json' },
        body: JSON.stringify({ p }),
    }).catch(() => {}));
    return done;
}
