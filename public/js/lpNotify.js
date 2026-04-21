/*
  Lucky Please — Notifications (in-page + foreground OS only)

  Why no Service Worker? CLAUDE.md explicitly forbids re-introducing
  one ("Stale-SW debugging cost hours during the April 2026 Lotto
  redesign"). Without an SW we cannot receive Web Push when the tab
  is closed — that's the trade-off. We DO support:
    • Foreground in-app toast      (no permission needed)
    • Native OS notification       (Notification API w/o SW — works
                                     when the tab is hidden but the
                                     browser process is still alive)
    • Click-to-open the thread     (window.focus() + URL handler)

  Suppression: if the user is currently viewing the relevant thread
  (window._lpActiveThread is set), we don't notify — they're already
  reading. The /messages/ page sets/clears this flag.

  Permission policy: never ask on page load. The /messages/ page
  shows an inline opt-in banner the first time they open it; clicking
  the banner triggers Notification.requestPermission. Everything
  works without permission via the in-app toast fallback.
*/
(function(){
    if (window.LpNotify) return;

    const PREF_KEY = 'luckyplz_notify_pref';

    function getPref(){
        try { return localStorage.getItem(PREF_KEY) || 'default'; } catch(_) { return 'default'; }
    }
    function setPref(v){
        try { localStorage.setItem(PREF_KEY, v); } catch(_) {}
    }

    function permissionState(){
        if (!('Notification' in window)) return 'unsupported';
        return Notification.permission; // 'default' | 'granted' | 'denied'
    }

    async function requestPermission(){
        if (!('Notification' in window)) return 'unsupported';
        if (Notification.permission === 'granted') { setPref('wants'); return 'granted'; }
        if (Notification.permission === 'denied')  { setPref('declined'); return 'denied'; }
        try {
            const r = await Notification.requestPermission();
            setPref(r === 'granted' ? 'wants' : 'declined');
            return r;
        } catch(_) { return 'denied'; }
    }

    /* ---- In-app toast ---------------------------------------- */
    /* Stack of slide-in cards in the top-right corner. Each carries
       its own onClick so multiple stacked toasts route correctly when
       tapped. Auto-dismiss after 5 s; manual dismiss via the × button
       or via tapping the body (which fires onClick first). */
    let toastWrap = null;
    function ensureToastWrap(){
        if (toastWrap && document.body.contains(toastWrap)) return toastWrap;
        toastWrap = document.createElement('div');
        toastWrap.id = 'lpNotifyToasts';
        toastWrap.style.cssText =
            'position:fixed;top:16px;right:16px;z-index:10000;'
            +'display:flex;flex-direction:column;gap:8px;'
            +'pointer-events:none;max-width:90vw;width:340px';
        document.body.appendChild(toastWrap);
        return toastWrap;
    }

    function _safeText(s){
        return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    function showToast({title, body, icon, onClick}){
        const wrap = ensureToastWrap();
        const t = document.createElement('div');
        t.style.cssText =
            'pointer-events:auto;cursor:pointer;'
            +'background:rgba(14,14,28,.95);border:1px solid rgba(0,217,255,.4);'
            +'border-radius:14px;padding:11px 12px;display:flex;gap:10px;align-items:center;'
            +'backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);'
            +'box-shadow:0 12px 30px rgba(0,0,0,.5);'
            +'transform:translateX(120%);transition:transform .25s cubic-bezier(.2,.8,.4,1);'
            +'font-family:"Noto Sans KR",sans-serif;color:#fff';
        const avatarHtml = icon
            ? `<img src="${_safeText(icon)}" referrerpolicy="no-referrer" alt="" style="width:36px;height:36px;border-radius:50%;flex-shrink:0;object-fit:cover;background:#000">`
            : `<div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#FF6B35,#FF6B8B);display:flex;align-items:center;justify-content:center;font-weight:900;color:#fff;flex-shrink:0;font-size:.92em">${_safeText((title||'?').charAt(0).toUpperCase())}</div>`;
        t.innerHTML = avatarHtml
            + `<div style="flex:1;min-width:0">
                <div style="font-size:.86em;font-weight:700;color:#FFE66D;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${_safeText(title)}</div>
                <div style="font-size:.78em;color:rgba(255,255,255,.78);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px">${_safeText(body)}</div>
            </div>
            <button class="lp-toast-x" style="background:none;border:0;color:rgba(255,255,255,.4);font-size:1.1em;cursor:pointer;padding:0 4px;line-height:1;font-weight:700">×</button>`;
        wrap.appendChild(t);
        requestAnimationFrame(() => { t.style.transform = 'translateX(0)'; });
        let dismissed = false;
        function dismiss(){
            if (dismissed) return; dismissed = true;
            t.style.transform = 'translateX(120%)';
            setTimeout(() => t.remove(), 280);
        }
        t.querySelector('.lp-toast-x').addEventListener('click', e => { e.stopPropagation(); dismiss(); });
        t.addEventListener('click', () => {
            if (onClick) try { onClick(); } catch(_) {}
            dismiss();
        });
        setTimeout(dismiss, 5000);
    }

    /* ---- Top-level show ------------------------------------- */
    /* threadKey: stable per-conversation string ('dm:<friend_id>' or
       'group:<room_id>'). Used both as Notification.tag (collapses
       stacked OS notifications for the same thread) and as the
       suppress-when-viewing check. */
    function show({title, body, icon, onClick, threadKey}){
        if (threadKey && window._lpActiveThread === threadKey && document.hasFocus()) return;
        const wantsOS = permissionState() === 'granted'
                     && (document.hidden || !document.hasFocus());
        if (wantsOS){
            try {
                const n = new Notification(title || 'Lucky Please', {
                    body: body || '',
                    icon: icon || '/assets/icon-192.png',
                    tag: threadKey || 'lp-msg',
                    silent: false
                });
                n.onclick = () => {
                    try { window.focus(); } catch(_) {}
                    if (onClick) try { onClick(); } catch(_) {}
                    try { n.close(); } catch(_) {}
                };
                return;
            } catch(_) { /* fall through to toast */ }
        }
        showToast({title, body, icon, onClick});
    }

    /* ---- Auto-wire: subscribe to DM inserts site-wide ------- */
    /* Group-chat notifications would require subscribing to every
       room the user is in (potentially many channels). Skipped for
       this phase — a polling/aggregate-channel design comes later
       if the signal is missed. DM coverage is enough for v1. */
    let initialized = false;
    async function init(){
        if (initialized) return;
        if (typeof getUser !== 'function' || typeof getSupabase !== 'function') return;
        if (typeof window.LpSocial === 'undefined') return;
        const user = await getUser();
        if (!user) return;
        initialized = true;

        /* Prime the mute cache once at init. After this the synchronous
           LpSocial.isMuted() answers the per-message gate instantly. */
        try { if (window.LpSocial && LpSocial.getMutes) await LpSocial.getMutes(); } catch(_){}

        /* Cache sender profiles so a chatty friend doesn't generate
           a profile fetch per message. 5-min TTL is fine — nicknames
           rarely change inside a session. */
        const profCache = new Map();
        async function fetchProfile(uid){
            const c = profCache.get(uid);
            if (c && Date.now() - c.savedAt < 300000) return c.row;
            try {
                const { data } = await getSupabase()
                    .from('profiles').select('nickname, avatar_url').eq('id', uid).single();
                profCache.set(uid, {row: data, savedAt: Date.now()});
                return data;
            } catch(_) { return null; }
        }

        window.LpSocial.subscribeToIncoming(async (msg) => {
            const senderId = msg.from_id;
            if (!senderId || senderId === user.id) return;
            /* Respect the per-thread mute list — the message still
               arrives + counts toward unread, we just don't fire any
               toast / OS notification for this sender. */
            if (LpSocial.isMuted && LpSocial.isMuted('dm', senderId)) return;
            const prof = await fetchProfile(senderId);
            const nick = (prof && prof.nickname) || 'Someone';
            let body = msg.body;
            if (!body && msg.attachment_url) body = '📷 Photo';
            show({
                title: nick,
                body: body || '',
                icon: (prof && prof.avatar_url) || null,
                threadKey: 'dm:' + senderId,
                onClick: () => { location.href = '/messages/?friend=' + encodeURIComponent(senderId); }
            });
        });
    }

    window.LpNotify = { init, requestPermission, getPref, setPref, permissionState, show, showToast };

    /* Auto-init on next tick — supabase-config + lpSocial may still
       be loading. Retry a few times if LpSocial isn't ready. */
    let tries = 0;
    function tryInit(){
        if (initialized) return;
        if (typeof window.LpSocial !== 'undefined') { init(); return; }
        if (tries++ < 30) setTimeout(tryInit, 200);
    }
    if (document.readyState === 'loading'){
        document.addEventListener('DOMContentLoaded', () => setTimeout(tryInit, 100));
    } else {
        setTimeout(tryInit, 100);
    }
})();
