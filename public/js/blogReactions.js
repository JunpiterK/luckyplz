/* Lucky Please — Blog Reactions
   Anonymous 1-click reaction widget for blog posts. Mounts where the
   page declares `<div data-blog-reactions data-slug="..."></div>`.

   Backend is Supabase RPC (see supabase/migrations/2026-05-04-blog-reactions.sql).
   If the migration hasn't been applied yet, the widget silently degrades
   to a localStorage-only counter so we never block the page on backend
   issues. Once the migration runs, real aggregated counts appear on
   next page load — no client redeploy needed.

   Per-device dedupe via localStorage keyed `lp_react_<slug>_<kind>`.
   This is a vanity-engagement signal, not a vote — light enforcement
   is fine and keeps the backend simple. */
(function(){
    'use strict';

    const KINDS = [
        { key: 'like',     emoji: '👍', label_ko: '좋아요',  label_en: 'Like' },
        { key: 'fire',     emoji: '🔥', label_ko: '흥미로움', label_en: 'Hot' },
        { key: 'idea',     emoji: '💡', label_ko: '도움됨',   label_en: 'Helpful' },
        { key: 'question', emoji: '❓', label_ko: '의문',     label_en: 'Hmm' },
    ];

    function getLang(){
        try { return (localStorage.getItem('luckyplz_lang') || 'ko').toLowerCase(); }
        catch(_) { return 'ko'; }
    }

    function hasReacted(slug, kind){
        try { return localStorage.getItem('lp_react_' + slug + '_' + kind) === '1'; }
        catch(_) { return false; }
    }
    function markReacted(slug, kind){
        try { localStorage.setItem('lp_react_' + slug + '_' + kind, '1'); }
        catch(_) {}
    }
    function unmarkReacted(slug, kind){
        try { localStorage.removeItem('lp_react_' + slug + '_' + kind); }
        catch(_) {}
    }

    /* Local fallback counter — used when Supabase isn't available or the
       migration hasn't been applied yet. Per-device only, but lets the
       widget feel responsive in dev/preview before the backend exists. */
    function getLocalCounts(slug){
        try {
            const raw = localStorage.getItem('lp_react_local_' + slug);
            if (!raw) return {};
            return JSON.parse(raw);
        } catch(_) { return {}; }
    }
    function bumpLocalCount(slug, kind){
        try {
            const cur = getLocalCounts(slug);
            cur[kind] = (cur[kind] || 0) + 1;
            localStorage.setItem('lp_react_local_' + slug, JSON.stringify(cur));
        } catch(_) {}
    }
    function bumpLocalCountDown(slug, kind){
        try {
            const cur = getLocalCounts(slug);
            cur[kind] = Math.max(0, (cur[kind] || 0) - 1);
            localStorage.setItem('lp_react_local_' + slug, JSON.stringify(cur));
        } catch(_) {}
    }

    /* Inject the widget's CSS once per page. The default palette targets
       the site's dark theme; the `--paper` modifier overrides every
       affected property for cream/journal pages (e.g. AI 진화사 series).
       Pages opt into paper by setting `data-theme="paper"` on the host
       <div data-blog-reactions>. */
    function injectStyles(){
        if (document.getElementById('lp-blog-reactions-style')) return;
        const s = document.createElement('style');
        s.id = 'lp-blog-reactions-style';
        s.textContent =
            /* === DARK / DEFAULT === */
            '.lp-react{margin:36px 0 18px;padding:22px;border-radius:16px;background:linear-gradient(145deg,rgba(0,217,255,.04),rgba(255,230,109,.03));border:1px solid rgba(255,255,255,.06)}'
          + '.lp-react-title{font-family:\'Orbitron\',\'Noto Sans KR\',sans-serif;font-size:.78em;letter-spacing:2.5px;color:rgba(255,255,255,.5);text-align:center;font-weight:700;margin-bottom:14px;text-transform:uppercase}'
          + '.lp-react-row{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}'
          + '.lp-react-btn{display:flex;flex-direction:column;align-items:center;gap:4px;padding:14px 6px;border-radius:12px;background:rgba(255,255,255,.04);border:1.5px solid rgba(255,255,255,.08);color:rgba(255,255,255,.85);cursor:pointer;font-family:\'Noto Sans KR\',sans-serif;font-size:.78em;font-weight:600;letter-spacing:.02em;transition:transform .15s,background .2s,border-color .2s,color .2s}'
          + '.lp-react-btn:hover{background:rgba(255,230,109,.08);border-color:rgba(255,230,109,.3);color:#fff;transform:translateY(-1px)}'
          + '.lp-react-btn:active{transform:scale(.96)}'
          + '.lp-react-btn .lp-react-emoji{font-size:1.6em;line-height:1}'
          + '.lp-react-btn .lp-react-count{font-family:\'Orbitron\',sans-serif;font-size:.95em;font-weight:800;color:rgba(255,230,109,.85);min-height:1em}'
          + '.lp-react-btn[data-active="1"]{background:linear-gradient(135deg,rgba(255,230,109,.18),rgba(255,107,53,.1));border-color:rgba(255,230,109,.5);color:#FFE66D}'
          + '.lp-react-btn[data-active="1"] .lp-react-count{color:#FFE66D}'
            /* On hover of an already-reacted button, hint at undo with
               a warm orange shift + a tiny ✕ glyph below the label. */
          + '.lp-react-btn[data-active="1"]:hover{background:linear-gradient(135deg,rgba(255,107,53,.18),rgba(220,38,38,.08));border-color:rgba(255,107,53,.55);color:#FFB57A;transform:none}'
          + '.lp-react-btn[data-active="1"]:hover::after{content:"✕";display:block;font-size:.85em;font-weight:700;color:#FFB57A;margin-top:1px;opacity:.85;line-height:1}'
          + '.lp-react-disclaimer{margin-top:12px;font-size:.72em;color:rgba(255,255,255,.32);text-align:center;letter-spacing:.02em}'
          + '@media(max-width:500px){.lp-react{padding:16px;margin:28px 0 14px}.lp-react-btn{padding:11px 4px;font-size:.72em}.lp-react-btn .lp-react-emoji{font-size:1.35em}}'
            /* === PAPER VARIANT (cream/journal pages) ===
               Overrides every dark-theme color so the widget reads on
               #FAF7F0 backgrounds without losing the engagement-card feel.
               Gold (#C8924E) is the primary accent; rose (#B85462) shows
               up only as a faint gradient seasoning so the card has
               warmth instead of looking like a clinical inset.            */
          + '.lp-react.lp-react--paper{background:linear-gradient(145deg,rgba(200,146,78,.07) 0%,rgba(184,84,98,.04) 100%);border:1px solid rgba(200,146,78,.22);box-shadow:0 2px 12px rgba(44,62,80,.05)}'
          + '.lp-react--paper .lp-react-title{font-family:\'JetBrains Mono\',monospace;color:#5A6C7D;letter-spacing:.18em}'
          + '.lp-react--paper .lp-react-btn{background:#FFFFFF;border:1.5px solid #E8E2D5;color:#2C3E50;font-family:\'Pretendard\',-apple-system,BlinkMacSystemFont,sans-serif;box-shadow:0 1px 2px rgba(44,62,80,.04)}'
          + '.lp-react--paper .lp-react-btn:hover{background:#FBF5EA;border-color:#C8924E;color:#2C3E50;transform:translateY(-1px);box-shadow:0 3px 10px rgba(200,146,78,.15)}'
          + '.lp-react--paper .lp-react-btn .lp-react-count{font-family:\'JetBrains Mono\',monospace;color:#C8924E;font-weight:700}'
          + '.lp-react--paper .lp-react-btn[data-active="1"]{background:linear-gradient(135deg,#FBF1E1,#F5E5C8);border-color:#C8924E;color:#854D0E;box-shadow:inset 0 1px 0 rgba(255,255,255,.6),0 2px 6px rgba(200,146,78,.18)}'
          + '.lp-react--paper .lp-react-btn[data-active="1"] .lp-react-count{color:#854D0E}'
            /* Paper variant: hovering an active button hints at cancel
               with a rose shift + the same ✕ glyph hint. */
          + '.lp-react--paper .lp-react-btn[data-active="1"]:hover{background:linear-gradient(135deg,#FCE7F3,#F8E8E8);border-color:#B85462;color:#831843;transform:none}'
          + '.lp-react--paper .lp-react-btn[data-active="1"]:hover::after{color:#B85462}'
          + '.lp-react--paper .lp-react-disclaimer{color:#8A9AA8}';
        document.head.appendChild(s);
    }

    /* Try Supabase RPC; resolve to {kind,cnt} array or null on any failure
       (network, missing function, RLS, anything). Caller falls back to
       local counts on null. */
    async function fetchCounts(slug){
        if (!window.getSupabase) return null;
        try {
            const sb = await window.getSupabase();
            if (!sb) return null;
            const { data, error } = await sb.rpc('get_blog_reactions', { p_slug: slug });
            if (error || !Array.isArray(data)) return null;
            return data;
        } catch(_) { return null; }
    }

    async function postReaction(slug, kind){
        if (!window.getSupabase) return false;
        try {
            const sb = await window.getSupabase();
            if (!sb) return false;
            const { error } = await sb.rpc('add_blog_reaction', { p_slug: slug, p_kind: kind });
            return !error;
        } catch(_) { return false; }
    }

    /* Toggle-off path: undo a click. Backend deletes the most recent
       row for (slug, kind); the local count decrements; localStorage
       flag is cleared so the user can re-react later. Same trust
       model as add — vanity counter, not a vote. */
    async function removeReaction(slug, kind){
        if (!window.getSupabase) return false;
        try {
            const sb = await window.getSupabase();
            if (!sb) return false;
            const { error } = await sb.rpc('remove_blog_reaction', { p_slug: slug, p_kind: kind });
            return !error;
        } catch(_) { return false; }
    }

    function render(host, slug, counts){
        const lang = getLang();
        const labelKey = lang === 'ko' ? 'label_ko' : 'label_en';
        const titleText = lang === 'ko' ? '이 글 어땠나요?' : 'How was this post?';
        const disclaimerText = lang === 'ko'
            ? '클릭으로 토글 · 다시 누르면 취소 · 익명 집계'
            : 'Click to toggle · click again to cancel · anonymous';
        const tipReact = lang === 'ko' ? '클릭하여 반응' : 'Click to react';
        const tipCancel = lang === 'ko' ? '다시 클릭하면 취소' : 'Click again to cancel';

        /* Theme is opt-in via host's `data-theme` attribute. Default
           palette stays dark; pages with cream backgrounds (AI 진화사
           series, future paper/journal posts) pass `data-theme="paper"`
           and get the warm cream-friendly variant. */
        const theme = (host.dataset.theme || '').toLowerCase();
        const themeClass = theme === 'paper' ? ' lp-react--paper' : '';

        host.innerHTML =
            '<div class="lp-react' + themeClass + '">'
          + '<div class="lp-react-title">' + titleText + '</div>'
          + '<div class="lp-react-row">'
          + KINDS.map(k => {
                const cnt = counts[k.key] || 0;
                const active = hasReacted(slug, k.key) ? '1' : '0';
                const tip = active === '1' ? tipCancel : tipReact;
                return '<button type="button" class="lp-react-btn" data-kind="' + k.key + '" data-active="' + active + '" aria-label="' + k[labelKey] + '" title="' + tip + '">'
                     +   '<span class="lp-react-emoji">' + k.emoji + '</span>'
                     +   '<span>' + k[labelKey] + '</span>'
                     +   '<span class="lp-react-count">' + (cnt > 0 ? cnt : '') + '</span>'
                     + '</button>';
            }).join('')
          + '</div>'
          + '<div class="lp-react-disclaimer">' + disclaimerText + '</div>'
          + '</div>';

        host.querySelectorAll('.lp-react-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const kind = btn.dataset.kind;
                const wasReacted = hasReacted(slug, kind);
                const countEl = btn.querySelector('.lp-react-count');
                const cur = parseInt(countEl.textContent || '0', 10) || 0;

                if (wasReacted) {
                    /* Toggle OFF — user cancels their reaction. Optimistic
                       decrement + unlock + clear local counter. Backend
                       deletes the most recent matching row. */
                    const next = Math.max(0, cur - 1);
                    countEl.textContent = next > 0 ? next : '';
                    btn.dataset.active = '0';
                    btn.setAttribute('title', tipReact);
                    unmarkReacted(slug, kind);
                    bumpLocalCountDown(slug, kind);
                    removeReaction(slug, kind); /* fire and forget */
                } else {
                    /* Toggle ON — first reaction. Optimistic +1 + lock. */
                    countEl.textContent = (cur + 1);
                    btn.dataset.active = '1';
                    btn.setAttribute('title', tipCancel);
                    markReacted(slug, kind);
                    bumpLocalCount(slug, kind);
                    postReaction(slug, kind); /* fire and forget */
                }
            });
        });
    }

    async function mount(host){
        const slug = host.dataset.slug;
        if (!slug) return;
        injectStyles();

        /* Render immediately with whatever local counts we have so the
           widget appears even on slow connections. Then, if Supabase
           resolves with real data, re-render to overlay the truth. */
        const local = getLocalCounts(slug);
        render(host, slug, local);

        const remote = await fetchCounts(slug);
        if (remote) {
            const counts = {};
            remote.forEach(r => { counts[r.kind] = r.cnt; });
            /* If remote has a row at zero but local has something, prefer
               local — covers the brief window between user's first click
               and Supabase replication catching up. */
            Object.keys(local).forEach(k => {
                if ((counts[k] || 0) < (local[k] || 0)) counts[k] = local[k];
            });
            render(host, slug, counts);
        }
    }

    function init(){
        document.querySelectorAll('[data-blog-reactions]').forEach(mount);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
