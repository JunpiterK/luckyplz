/* Blog email subscribe form — auto-injected at the bottom of every blog
   post and the blog index. Builds a quiet retention loop: visitor reads
   one piece of analysis, drops their email, gets pinged when the next
   one publishes. Even a 5-10% conversion at low traffic compounds into
   a meaningful return-visitor base by the SpaceX IPO peak.

   Backend: Supabase RPC `public.subscribe_email(email, lang, source)`.
   Returns 'subscribed' | 'reactivated' | 'already_active' | 'invalid'.
   The form maps each to a user-facing message and disables further
   submissions afterwards. No auth required — RLS allows anon insert.

   Mount: explicit <div id="lpSubscribeMount"> wins; otherwise the form
   inserts before the page's first <footer> (same convention as
   blogRelated.js, so on a blog post the form lands directly under the
   "추천 글" block — natural call-to-action position).

   Skips entirely when:
   - Supabase client is unavailable (auth.js failed to load)
   - User dismissed the form within the last 14 days (cooldown)
   - localStorage shows they already subscribed in this browser */
(function () {
    if (typeof window === 'undefined' || !document) return;
    if (document.querySelector('.lp-subscribe')) return;

    var DISMISS_KEY = 'lp_subscribe_dismissed';
    var SUBSCRIBED_KEY = 'lp_subscribed_email';
    var COOLDOWN_MS = 14 * 24 * 60 * 60 * 1000;

    /* === Skip checks ================================================= */
    try {
        if (localStorage.getItem(SUBSCRIBED_KEY)) return;
        var ts = parseInt(localStorage.getItem(DISMISS_KEY) || '0', 10);
        if (ts && (Date.now() - ts) < COOLDOWN_MS) return;
    } catch (_) {}

    /* Resolve current language. Falls back through the same chain the
       blog index uses so KR users get the KR copy and everyone else
       gets EN. */
    function resolveLang() {
        try {
            if (window.LP_LANG) return window.LP_LANG === 'ko' ? 'ko' : 'en';
            var stored = (localStorage.getItem('luckyplz_lang') || '').toLowerCase();
            return stored === 'ko' ? 'ko' : 'en';
        } catch (_) { return 'ko'; }
    }
    var lang = resolveLang();

    /* === Copy table — short, no marketing spin ======================= */
    var COPY = lang === 'ko' ? {
        title: '새 글 알림 받기',
        desc: 'SpaceX · AI · 산업 분석 — 새 글이 올라올 때 한 번 메일로 알려드립니다.',
        placeholder: '이메일 주소',
        submit: '구독',
        loading: '확인 중…',
        ok_subscribed: '구독 완료. 새 글이 올라올 때 알려드릴게요.',
        ok_reactivated: '다시 구독되었습니다. 환영합니다.',
        ok_already: '이미 구독 중인 이메일입니다.',
        err_invalid: '이메일 형식을 다시 확인해주세요.',
        err_network: '잠시 후 다시 시도해주세요.',
        close: '닫기',
    } : {
        title: 'Get post alerts',
        desc: 'SpaceX · AI · industry deep dives. One email when something new ships.',
        placeholder: 'Your email',
        submit: 'Subscribe',
        loading: 'Working…',
        ok_subscribed: 'Subscribed. You\'ll hear from us when the next post ships.',
        ok_reactivated: 'Re-subscribed. Welcome back.',
        ok_already: 'This email is already subscribed.',
        err_invalid: 'Please check the email format.',
        err_network: 'Something went wrong. Try again in a moment.',
        close: 'Close',
    };

    /* === Build markup ================================================= */
    var sec = document.createElement('section');
    sec.className = 'lp-subscribe';
    sec.innerHTML = ''
        + '<button type="button" class="lp-sub-close" aria-label="' + COPY.close + '">×</button>'
        + '<div class="lp-sub-text">'
        + '  <span class="lp-sub-title">' + COPY.title + '</span>'
        + '  <span class="lp-sub-desc">' + COPY.desc + '</span>'
        + '</div>'
        + '<form class="lp-sub-form" novalidate>'
        + '  <input type="email" class="lp-sub-input" inputmode="email" autocomplete="email" '
        + '         spellcheck="false" placeholder="' + COPY.placeholder + '" required>'
        + '  <button type="submit" class="lp-sub-btn">' + COPY.submit + '</button>'
        + '</form>'
        + '<p class="lp-sub-status" hidden></p>';

    /* === Styles (one-shot inject) ===================================== */
    if (!document.getElementById('lpSubscribeStyle')) {
        var st = document.createElement('style');
        st.id = 'lpSubscribeStyle';
        st.textContent = ''
            + '.lp-subscribe{position:relative;margin:28px 16px 0;padding:20px 22px;'
            + 'background:linear-gradient(135deg,rgba(20,28,46,.72),rgba(15,21,37,.92));'
            + 'border:1px solid rgba(140,162,196,.22);border-radius:14px;'
            + 'font-family:"Pretendard Variable","Pretendard","Inter",-apple-system,sans-serif;'
            + 'color:rgba(232,238,247,.92)}'
            + '.lp-sub-close{position:absolute;top:8px;right:10px;background:transparent;border:none;'
            + 'color:rgba(180,200,230,.4);font-size:18px;line-height:1;padding:6px 8px;cursor:pointer;'
            + 'font-family:-apple-system,sans-serif;transition:color .2s}'
            + '.lp-sub-close:hover{color:rgba(255,255,255,.85)}'
            + '.lp-sub-text{display:flex;flex-direction:column;gap:4px;margin-bottom:14px;line-height:1.45}'
            + '.lp-sub-title{font-size:14.5px;font-weight:800;letter-spacing:-.015em;color:#fff}'
            + '.lp-sub-desc{font-size:12.5px;color:rgba(180,200,230,.62);font-weight:400}'
            + '.lp-sub-form{display:flex;gap:8px;align-items:stretch;flex-wrap:wrap}'
            + '.lp-sub-input{flex:1;min-width:0;height:40px;padding:0 14px;'
            + 'background:rgba(255,255,255,.04);border:1px solid rgba(140,162,196,.28);'
            + 'border-radius:9px;color:#fff;font-size:13px;font-family:inherit;letter-spacing:-.005em;'
            + 'outline:none;transition:border-color .2s,background .2s}'
            + '.lp-sub-input:focus{border-color:rgba(140,162,196,.55);background:rgba(255,255,255,.07)}'
            + '.lp-sub-input::placeholder{color:rgba(180,200,230,.42)}'
            + '.lp-sub-btn{flex:0 0 auto;height:40px;padding:0 18px;'
            + 'background:linear-gradient(135deg,rgba(140,162,196,.18),rgba(140,162,196,.08));'
            + 'border:1px solid rgba(140,162,196,.4);border-radius:9px;color:rgba(220,232,248,.96);'
            + 'font-family:"JetBrains Mono",ui-monospace,monospace;font-size:11px;font-weight:800;'
            + 'letter-spacing:.1em;text-transform:uppercase;cursor:pointer;'
            + 'transition:background .2s,border-color .2s,color .2s,transform .15s}'
            + '.lp-sub-btn:hover{background:linear-gradient(135deg,rgba(140,162,196,.28),rgba(140,162,196,.14));'
            + 'border-color:rgba(180,200,230,.55);color:#fff;transform:translateY(-1px)}'
            + '.lp-sub-btn:disabled{opacity:.6;cursor:not-allowed;transform:none}'
            + '.lp-sub-status{margin:12px 0 0;font-size:12px;line-height:1.5;letter-spacing:-.005em}'
            + '.lp-sub-status[data-state="ok"]{color:#86efac}'
            + '.lp-sub-status[data-state="err"]{color:#ff9aa8}'
            + '.lp-sub-status[hidden]{display:none}'
            + '@media(max-width:480px){'
            + '.lp-subscribe{margin:24px 12px 0;padding:16px 18px}'
            + '.lp-sub-title{font-size:13.5px}.lp-sub-desc{font-size:11.5px}'
            + '.lp-sub-input{height:38px;font-size:12.5px}'
            + '.lp-sub-btn{height:38px;font-size:10.5px;padding:0 14px}'
            + '}';
        document.head.appendChild(st);
    }

    /* === Mount ======================================================== */
    var mount = document.getElementById('lpSubscribeMount');
    var anchor = mount ? null : document.querySelector('footer');
    if (!mount && !anchor) return;
    if (mount) mount.appendChild(sec);
    else anchor.parentNode.insertBefore(sec, anchor);

    /* === Wire up ======================================================= */
    var form = sec.querySelector('.lp-sub-form');
    var input = sec.querySelector('.lp-sub-input');
    var btn = sec.querySelector('.lp-sub-btn');
    var status = sec.querySelector('.lp-sub-status');
    var closeBtn = sec.querySelector('.lp-sub-close');

    function showStatus(text, state) {
        status.textContent = text;
        status.hidden = false;
        status.setAttribute('data-state', state || 'ok');
    }

    closeBtn.addEventListener('click', function () {
        try { localStorage.setItem(DISMISS_KEY, String(Date.now())); } catch (_) {}
        sec.remove();
    });

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        var email = (input.value || '').trim().toLowerCase();
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
            showStatus(COPY.err_invalid, 'err');
            input.focus();
            return;
        }

        /* Lazy-load Supabase. supabase-config.js exposes window.getSupabase()
           on every page that includes it. If absent (SDK didn't load), we
           degrade gracefully to a network error message. */
        var sb;
        try { sb = window.getSupabase && window.getSupabase(); } catch (_) {}
        if (!sb) {
            showStatus(COPY.err_network, 'err');
            return;
        }

        btn.disabled = true;
        btn.textContent = COPY.loading;

        var source = (function () {
            var p = location.pathname;
            if (p === '/blog/' || p === '/blog/index.html') return 'blog-index';
            var m = p.match(/^\/blog\/([^/]+)/);
            if (m) return 'blog-post:' + m[1];
            return 'site:' + p;
        })();

        sb.rpc('subscribe_email', { p_email: email, p_lang: lang, p_source: source })
            .then(function (res) {
                btn.disabled = false;
                btn.textContent = COPY.submit;
                if (res.error) {
                    showStatus(COPY.err_network, 'err');
                    return;
                }
                var v = res.data;
                if (v === 'subscribed') {
                    showStatus(COPY.ok_subscribed, 'ok');
                } else if (v === 'reactivated') {
                    showStatus(COPY.ok_reactivated, 'ok');
                } else if (v === 'already_active') {
                    showStatus(COPY.ok_already, 'ok');
                } else if (v === 'invalid') {
                    showStatus(COPY.err_invalid, 'err');
                    return;
                } else {
                    showStatus(COPY.err_network, 'err');
                    return;
                }
                /* Lock the form so we don't double-submit on the same
                   pageload, and remember locally so the form is hidden
                   on the next pageload too. */
                form.querySelectorAll('input,button').forEach(function (el) { el.disabled = true; });
                try { localStorage.setItem(SUBSCRIBED_KEY, email); } catch (_) {}
            })
            .catch(function () {
                btn.disabled = false;
                btn.textContent = COPY.submit;
                showStatus(COPY.err_network, 'err');
            });
    });
})();
