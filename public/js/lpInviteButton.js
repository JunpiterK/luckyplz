/*
  Lucky Please — Game-page Invite button
  =======================================
  Auto-injected on every /games/* page (from siteFooter.js). Shows a
  floating "👥 친구 초대" pill + opens a modal listing the user's
  friends, colour-coded by presence. Clicking a row fires
  LpInvite.sendInvite with the current page URL as the destination,
  so the guest lands on exactly the same URL (and any ?room= query
  threaded through there picks up LpRoom's auto-join logic).

  Visibility rules:
    • Hidden until auth (getUser resolves + profile_complete)
    • Hidden when there are no accepted friends yet
    • Accessible via keyboard (tab-focusable + Enter)

  States for each friend row:
    online    — "초대" button enabled
    dnd       — greyed row, tooltip "방해금지 중이에요"
    offline   — greyed row, tooltip "오프라인이에요"

  Once a row is clicked and the RPC fires, the row switches to
  "전송됨 • 대기 중" with the timestamp. When LpInvite.onResponse
  fires for that invite id, the row flips to "수락함" (green) or
  "거절함" (red) for a few seconds before reverting.
*/
(function(){
    if (window.LpInviteButton) return;
    /* Only inject on /games/* pages — site-wide injection is both
       unnecessary and visually noisy. */
    if (!/^\/games\//.test(location.pathname)) return;

    let _pillEl = null;
    let _modalEl = null;
    let _pendingByFriend = new Map(); /* friendId → invite id for active sends */
    let _responseUnsub = null;
    let _presenceUnsub = null;
    let _booted = false;

    function _gameTypeFromPath() {
        const m = location.pathname.match(/^\/games\/([^\/]+)/);
        return m ? m[1] : 'game';
    }

    function _ensureStyles() {
        if (document.getElementById('lp-invite-button-css')) return;
        const css = `
        .lp-ib-pill{
            position:fixed;right:14px;bottom:14px;z-index:100;
            display:inline-flex;align-items:center;gap:8px;
            padding:11px 16px;border-radius:999px;border:0;cursor:pointer;
            background:linear-gradient(135deg,#00D9FF 0%,#0099CC 100%);
            color:#001220;font-family:'Noto Sans KR',sans-serif;
            font-size:.88em;font-weight:800;letter-spacing:.02em;
            box-shadow:0 10px 28px -8px rgba(0,217,255,.55),inset 0 1px 0 rgba(255,255,255,.28);
            transition:transform .18s,filter .18s,box-shadow .22s;
        }
        .lp-ib-pill:hover{transform:translateY(-2px);filter:brightness(1.08)}
        .lp-ib-pill:active{transform:translateY(1px);transition-duration:.08s}
        .lp-ib-pill .ico{font-size:1.06em}
        @media (max-width:560px){
            .lp-ib-pill{right:10px;bottom:10px;padding:10px 14px;font-size:.82em}
        }
        .lp-ib-modal{
            position:fixed;inset:0;background:rgba(5,5,15,.72);
            display:none;align-items:center;justify-content:center;
            z-index:2000;padding:16px;backdrop-filter:blur(4px);
            animation:lpibFade .18s ease-out;
        }
        .lp-ib-modal.on{display:flex}
        @keyframes lpibFade{from{opacity:0}to{opacity:1}}
        .lp-ib-card{
            width:100%;max-width:420px;max-height:80vh;overflow:hidden;
            background:linear-gradient(160deg,rgba(22,22,42,.98),rgba(12,12,28,1));
            border:1px solid rgba(255,255,255,.1);border-radius:18px;
            box-shadow:0 24px 60px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.06);
            color:#fff;font-family:'Noto Sans KR',sans-serif;
            display:flex;flex-direction:column;
        }
        .lp-ib-head{padding:18px 20px 10px;display:flex;align-items:center;gap:10px;border-bottom:1px solid rgba(255,255,255,.06)}
        .lp-ib-head h3{font-size:1.04em;font-weight:800;letter-spacing:-.01em;flex:1}
        .lp-ib-head .close{width:28px;height:28px;border-radius:8px;border:0;background:rgba(255,255,255,.06);color:#fff;cursor:pointer;font-size:1em}
        .lp-ib-head .close:hover{background:rgba(255,255,255,.12)}
        .lp-ib-body{overflow-y:auto;max-height:60vh;padding:6px 8px}
        .lp-ib-section-label{padding:10px 14px 4px;font-size:.68em;letter-spacing:.1em;text-transform:uppercase;color:rgba(255,255,255,.35);font-weight:800}
        .lp-ib-empty{padding:22px 16px;text-align:center;color:rgba(255,255,255,.45);font-size:.9em;line-height:1.55}
        .lp-ib-row{display:flex;align-items:center;gap:11px;padding:10px 12px;border-radius:12px;transition:background .15s}
        .lp-ib-row:hover{background:rgba(255,255,255,.04)}
        .lp-ib-row.disabled{opacity:.45;cursor:not-allowed}
        .lp-ib-av{
            width:38px;height:38px;border-radius:50%;flex-shrink:0;position:relative;overflow:hidden;
            background:linear-gradient(135deg,#FF6B35,#FF6B8B);
            display:flex;align-items:center;justify-content:center;
            font-family:'Orbitron',sans-serif;font-weight:900;font-size:.88em;color:#fff;
        }
        .lp-ib-av img{width:100%;height:100%;object-fit:cover}
        .lp-ib-av .sd{
            position:absolute;bottom:-1px;right:-1px;width:11px;height:11px;border-radius:50%;
            border:2px solid rgba(12,12,28,1);background:#6b6f7a;
        }
        .lp-ib-av .sd.online{background:#00E676;box-shadow:0 0 6px rgba(0,230,118,.55)}
        .lp-ib-av .sd.dnd{background:#FF9A3C}
        .lp-ib-av .sd.offline{background:transparent;border-color:rgba(255,255,255,.25)}
        .lp-ib-meta{flex:1;min-width:0}
        .lp-ib-nick{font-weight:700;font-size:.92em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .lp-ib-sub{font-size:.72em;color:rgba(255,255,255,.42);margin-top:2px}
        .lp-ib-act{
            padding:7px 14px;border-radius:999px;border:0;cursor:pointer;
            background:linear-gradient(135deg,#00D9FF,#0099CC);color:#001220;
            font-family:inherit;font-size:.78em;font-weight:800;letter-spacing:.04em;
            transition:transform .15s,filter .15s;
        }
        .lp-ib-act:hover{transform:translateY(-1px);filter:brightness(1.08)}
        .lp-ib-act:disabled{opacity:.55;cursor:default;transform:none;filter:none}
        .lp-ib-act.sent{background:rgba(255,255,255,.07);color:rgba(255,255,255,.75)}
        .lp-ib-act.accepted{background:linear-gradient(135deg,#00FF88,#00C97A);color:#003322}
        .lp-ib-act.declined{background:rgba(255,51,102,.15);color:#FF6B8B}
        `;
        const style = document.createElement('style');
        style.id = 'lp-invite-button-css';
        style.textContent = css;
        document.head.appendChild(style);
    }

    function _mountPill() {
        _ensureStyles();
        if (_pillEl) return;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'lp-ib-pill';
        btn.innerHTML = '<span class="ico">👥</span><span>친구 초대</span>';
        btn.addEventListener('click', _openModal);
        document.body.appendChild(btn);
        _pillEl = btn;
    }

    function _unmountPill() {
        if (_pillEl) { _pillEl.remove(); _pillEl = null; }
    }

    async function _openModal() {
        _ensureStyles();
        _buildModalShell();
        await _renderFriendsList();
        _modalEl.classList.add('on');
    }

    function _closeModal() {
        if (_modalEl) _modalEl.classList.remove('on');
    }

    function _buildModalShell() {
        if (_modalEl) return;
        const wrap = document.createElement('div');
        wrap.className = 'lp-ib-modal';
        wrap.innerHTML =
            '<div class="lp-ib-card">'
            + '<div class="lp-ib-head">'
                + '<h3>친구 초대 · ' + _esc(_humanGame(_gameTypeFromPath())) + '</h3>'
                + '<button class="close" type="button" aria-label="Close">✕</button>'
            + '</div>'
            + '<div class="lp-ib-body" id="lpIbBody"></div>'
            + '</div>';
        wrap.addEventListener('click', (e) => { if (e.target === wrap) _closeModal(); });
        wrap.querySelector('.close').addEventListener('click', _closeModal);
        document.body.appendChild(wrap);
        _modalEl = wrap;
    }

    async function _renderFriendsList() {
        const body = _modalEl.querySelector('#lpIbBody');
        body.innerHTML = '<div class="lp-ib-empty">불러오는 중…</div>';
        if (!window.LpSocial) { body.innerHTML = '<div class="lp-ib-empty">소셜 모듈을 불러올 수 없어요.</div>'; return; }
        const r = await LpSocial.getFriends();
        if (!r.ok) { body.innerHTML = '<div class="lp-ib-empty">친구 목록을 불러오지 못했어요.</div>'; return; }
        const accepted = (r.rows || []).filter(f => f.direction === 'accepted');
        if (!accepted.length) {
            body.innerHTML = '<div class="lp-ib-empty">아직 친구가 없어요.<br><a style="color:#00D9FF" href="/messages/">/messages/</a> 에서 추가해보세요.</div>';
            return;
        }

        /* Group by presence — online first (invitable), then greyed. */
        const buckets = { online: [], dnd: [], offline: [] };
        for (const f of accepted) {
            const s = (window.LpPresence && LpPresence.getStatus(f.friend_id)) || 'offline';
            buckets[s] = buckets[s] || [];
            buckets[s].push(f);
        }

        let html = '';
        if (buckets.online.length) {
            html += '<div class="lp-ib-section-label">온라인 · 초대 가능</div>';
            html += buckets.online.map(f => _friendRowHtml(f, 'online', false)).join('');
        }
        if (buckets.dnd.length) {
            html += '<div class="lp-ib-section-label">방해금지</div>';
            html += buckets.dnd.map(f => _friendRowHtml(f, 'dnd', true)).join('');
        }
        if (buckets.offline.length) {
            html += '<div class="lp-ib-section-label">오프라인</div>';
            html += buckets.offline.map(f => _friendRowHtml(f, 'offline', true)).join('');
        }
        body.innerHTML = html;
        body.querySelectorAll('[data-invite-to]').forEach(btn => {
            btn.addEventListener('click', () => _sendOne(btn.dataset.inviteTo, btn));
        });
    }

    function _friendRowHtml(f, status, disabled) {
        const av = f.avatar_url
            ? '<div class="lp-ib-av"><img src="' + _esc(f.avatar_url) + '" referrerpolicy="no-referrer" alt=""><span class="sd ' + status + '"></span></div>'
            : '<div class="lp-ib-av">' + _esc((f.nickname || '?').trim()[0] || '?').toUpperCase() + '<span class="sd ' + status + '"></span></div>';
        const sub = status === 'dnd' ? '방해금지 중' : status === 'offline' ? '오프라인' : '';
        const btn = disabled
            ? '<button class="lp-ib-act" disabled>초대 불가</button>'
            : '<button class="lp-ib-act" type="button" data-invite-to="' + _esc(f.friend_id) + '">초대</button>';
        return '<div class="lp-ib-row' + (disabled ? ' disabled' : '') + '">'
            + av
            + '<div class="lp-ib-meta">'
                + '<div class="lp-ib-nick">' + _esc(f.nickname || '(deleted)') + '</div>'
                + (sub ? '<div class="lp-ib-sub">' + _esc(sub) + '</div>' : '')
            + '</div>'
            + btn
            + '</div>';
    }

    async function _sendOne(friendId, btn) {
        if (!window.LpInvite) return;
        btn.disabled = true;
        btn.textContent = '전송 중…';
        btn.classList.add('sent');
        const gameType = _gameTypeFromPath();
        const gameUrl  = location.href;
        const r = await LpInvite.sendInvite(friendId, gameType, gameUrl);
        if (!r.ok) {
            btn.classList.remove('sent');
            btn.classList.add('declined');
            btn.textContent = _errToLabel(r.error);
            /* Revert after 2.5 s so the user can retry */
            setTimeout(() => { btn.classList.remove('declined'); btn.textContent = '초대'; btn.disabled = false; }, 2500);
            return;
        }
        _pendingByFriend.set(friendId, r.id);
        btn.textContent = '대기 중…';
    }

    function _errToLabel(err) {
        switch (err) {
            case 'offline':     return '오프라인';
            case 'not_friends': return '친구 아님';
            case 'self':        return '본인 초대 불가';
            default:            return '재시도';
        }
    }

    /* Incoming response for one of MY invites — update the row's button
       to accepted / declined / expired / cancelled. */
    function _handleResponse(row) {
        if (!row) return;
        const btn = _modalEl && _modalEl.querySelector('[data-invite-to="' + row.to_id + '"]');
        if (!btn) { _pendingByFriend.delete(row.to_id); return; }
        btn.classList.remove('sent','accepted','declined');
        if (row.status === 'accepted') {
            btn.classList.add('accepted');
            btn.textContent = '수락함 ✓';
        } else if (row.status === 'declined') {
            btn.classList.add('declined');
            btn.textContent = '거절함';
        } else if (row.status === 'expired') {
            btn.classList.add('declined');
            btn.textContent = '만료';
        } else {
            btn.textContent = '초대';
            btn.disabled = false;
        }
        _pendingByFriend.delete(row.to_id);
    }

    function _esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
    function _humanGame(type){
        const map={lotto:'로또',roulette:'룰렛',ladder:'사다리',dice:'주사위',team:'팀 나누기',bingo:'빙고','car-racing':'카레이싱'};
        return map[type]||'게임';
    }

    /* ---- Boot --------------------------------------------- */
    async function boot() {
        if (_booted) return;
        const user = await getUser();
        if (!user) return;
        _mountPill();
        if (window.LpInvite) {
            _responseUnsub = LpInvite.onResponse(_handleResponse);
        }
        if (window.LpPresence) {
            _presenceUnsub = LpPresence.onChange(() => {
                /* If the modal is open, re-render so new statuses are reflected. */
                if (_modalEl && _modalEl.classList.contains('on')) _renderFriendsList();
            });
        }
        _booted = true;
    }

    function _teardown() {
        _unmountPill();
        if (_responseUnsub)  { _responseUnsub(); _responseUnsub = null; }
        if (_presenceUnsub)  { _presenceUnsub(); _presenceUnsub = null; }
        if (_modalEl)        { _modalEl.remove(); _modalEl = null; }
        _booted = false;
    }

    function _wireAuth() {
        try {
            getSupabase().auth.onAuthStateChange((event) => {
                if (event === 'SIGNED_IN')  boot();
                else if (event === 'SIGNED_OUT') _teardown();
            });
        } catch (_) { setTimeout(_wireAuth, 200); }
    }

    _wireAuth();
    (async () => { try { await boot(); } catch (_) {} })();

    window.LpInviteButton = { boot, _open: _openModal };
})();
