/*
  Lucky Please — Social API
  Wraps the Supabase queries backing the friends + DM feature
  (schema.sql §4-5) in a small, easy-to-reason-about module.

  Design goals:
  • Explicit cache layers keyed by user id. Friend list 2-min TTL,
    inbox 60-sec TTL. Clears on SIGNED_OUT.
  • Realtime subscriptions are created lazily and tied to the caller's
    lifetime — caller gets an `unsubscribe()` fn back and is expected
    to call it when the UI tears down (we don't leak channels).
  • Never throws across the public surface. Returns {ok, error|data}.
  • DB is the single source of truth for ordering/auth; client only
    renders what it reads back.
*/
(function(){
    if (window.LpSocial) return;

    const FRIENDS_TTL_MS = 2 * 60 * 1000;
    const INBOX_TTL_MS   = 60 * 1000;

    /* ---- Cache helpers --------------------------------------- */
    const _cache = { friends: null, inbox: null, uid: null };

    function _setUid(uid){
        if (_cache.uid !== uid) {
            _cache.friends = null;
            _cache.inbox = null;
            _cache.uid = uid;
        }
    }
    function _clearCache(){
        _cache.friends = null;
        _cache.inbox = null;
        _cache.uid = null;
        /* Tear down the shared incoming-message channel so the next
           login re-creates it for the new user id. */
        if (_incomingChannel) {
            try { getSupabase().removeChannel(_incomingChannel); } catch (_) {}
            _incomingChannel = null;
            _incomingChannelUid = null;
        }
        _incomingListeners.length = 0;
        /* Also drop the mute cache — the next user has their own list. */
        if (_muteCache) { _muteCache.ready = false; _muteCache.set = new Set(); }
    }

    /* ---- Friend list ----------------------------------------- */
    /**
     * Returns ALL friendships where the current user is a member,
     * along with the joined profile (nickname/avatar) of the other
     * side. `direction` tells the UI which bucket to render it in:
     *   'accepted'          → friends
     *   'incoming-pending'  → someone requested YOU
     *   'outgoing-pending'  → YOU requested someone
     *   'blocked-by-me' / 'blocked-by-them'
     */
    async function getFriends({ force = false } = {}) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        _setUid(user.id);

        if (!force && _cache.friends && Date.now() - _cache.friends.savedAt < FRIENDS_TTL_MS) {
            return { ok: true, rows: _cache.friends.rows };
        }

        try {
            /* Two-step: fetch friendships, then the profile of every
               non-self user_id in one `in` lookup. Avoids N+1. */
            const sb = getSupabase();
            const { data: fs, error } = await sb
                .from('friendships')
                .select('user_a, user_b, requester_id, status, blocked_by, created_at, accepted_at');
            if (error) return { ok: false, error: error.message };

            const otherIds = new Set();
            fs.forEach(r => {
                otherIds.add(r.user_a === user.id ? r.user_b : r.user_a);
            });
            let profiles = {};
            if (otherIds.size) {
                const { data: profs, error: perr } = await sb
                    .from('profiles')
                    .select('id, nickname, avatar_url, profile_complete')
                    .in('id', Array.from(otherIds));
                if (perr) return { ok: false, error: perr.message };
                profs.forEach(p => profiles[p.id] = p);
            }

            const rows = fs.map(r => {
                const otherId = r.user_a === user.id ? r.user_b : r.user_a;
                const p = profiles[otherId] || {};
                let direction;
                if (r.status === 'accepted')      direction = 'accepted';
                else if (r.status === 'blocked')  direction = r.blocked_by === user.id ? 'blocked-by-me' : 'blocked-by-them';
                else /* pending */                direction = r.requester_id === user.id ? 'outgoing-pending' : 'incoming-pending';
                return {
                    friend_id: otherId,
                    nickname: p.nickname || '(deleted)',
                    avatar_url: p.avatar_url || null,
                    profile_complete: !!p.profile_complete,
                    status: r.status,
                    direction,
                    created_at: r.created_at,
                    accepted_at: r.accepted_at
                };
            });
            _cache.friends = { rows, savedAt: Date.now() };
            return { ok: true, rows };
        } catch (e) {
            return { ok: false, error: String(e) };
        }
    }

    /**
     * Send a friend request by target nickname. Goes through the
     * RPC so client doesn't need to know the target's uuid.
     * Result.auto_accepted is true when the other side had already
     * requested us — we auto-accept their outgoing request instead
     * of creating a duplicate.
     */
    async function sendFriendRequest(targetNickname) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        try {
            const { data, error } = await getSupabase()
                .rpc('send_friend_request', { target_nickname: targetNickname });
            if (error) return { ok: false, error: error.message };
            _cache.friends = null;
            return data || { ok: true };
        } catch (e) {
            return { ok: false, error: String(e) };
        }
    }

    /** Accept an incoming request by friend's user_id. */
    async function acceptFriendRequest(friendId) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        const a = user.id < friendId ? user.id : friendId;
        const b = user.id < friendId ? friendId : user.id;
        try {
            const { error } = await getSupabase()
                .from('friendships')
                .update({ status: 'accepted', accepted_at: new Date().toISOString() })
                .eq('user_a', a).eq('user_b', b);
            if (error) return { ok: false, error: error.message };
            _cache.friends = null;
            return { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /** Hard-delete the friendship row (unfriend / reject request). */
    async function removeFriend(friendId) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        const a = user.id < friendId ? user.id : friendId;
        const b = user.id < friendId ? friendId : user.id;
        try {
            const { error } = await getSupabase()
                .from('friendships').delete().eq('user_a', a).eq('user_b', b);
            if (error) return { ok: false, error: error.message };
            _cache.friends = null;
            _cache.inbox = null;
            return { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /** Block a friend / user. Status flips to 'blocked'; the block_by
        column records who did it so unblocking can check. */
    async function blockFriend(friendId) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        const a = user.id < friendId ? user.id : friendId;
        const b = user.id < friendId ? friendId : user.id;
        try {
            /* Upsert because (a,b) row may not exist yet (blocking
               someone who never requested). */
            const { error } = await getSupabase()
                .from('friendships')
                .upsert({
                    user_a: a, user_b: b,
                    requester_id: user.id,
                    status: 'blocked',
                    blocked_by: user.id,
                    blocked_at: new Date().toISOString()
                }, { onConflict: 'user_a,user_b' });
            if (error) return { ok: false, error: error.message };
            _cache.friends = null;
            return { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /* ---- Inbox + messages ------------------------------------ */
    /** Conversation list with unread counts. Cached 60 s. */
    async function getInbox({ force = false } = {}) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        _setUid(user.id);
        if (!force && _cache.inbox && Date.now() - _cache.inbox.savedAt < INBOX_TTL_MS) {
            return { ok: true, rows: _cache.inbox.rows };
        }
        try {
            const { data, error } = await getSupabase().rpc('dm_inbox');
            if (error) return { ok: false, error: error.message };
            _cache.inbox = { rows: data || [], savedAt: Date.now() };
            return { ok: true, rows: data || [] };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /** Total unread count across all threads. Cheap — piggybacks on
        inbox cache when fresh. */
    async function getUnreadCount() {
        const inb = await getInbox();
        if (!inb.ok) return 0;
        return inb.rows.reduce((n, r) => n + Number(r.unread_count || 0), 0);
    }

    /** Column list for every DM read path — centralised so we stay in
        sync across the three query sites (initial load, pagination,
        reply-target lookup). Deleted rows are returned too: the UI
        renders them as a tombstone instead of hiding them outright,
        which matches how KakaoTalk / WhatsApp handle delete-for-
        everyone and tells the reader that *something* was there. */
    const DM_COLUMNS = 'id, thread_id, from_id, to_id, body, created_at, read_at, deleted_at, attachment_url, attachment_type, attachment_size, attachment_name, reply_to_id';

    async function getThreadMessages(friendId, { before = null, limit = 50 } = {}) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        /* Call the server-side SECURITY DEFINER RPC. Mirrors the
           pattern dm_inbox uses. Sidesteps:
             - client-side md5 thread_id ambiguity (mobile Chrome
               Android + Samsung Internet returned empty result when
               the hash disagreed with the DB md5 by a single byte)
             - RLS evaluation edge cases on mobile WebViews that
               sometimes returned 0 rows on direct SELECTs even when
               dm_inbox (also SECURITY DEFINER) worked fine
             - PostgREST .or() filter parser variations between
               environments
           Only input is the friend id; auth.uid() is resolved
           server-side. Returns chronological oldest-first so the
           caller can render directly. */
        try {
            const { data, error } = await getSupabase().rpc('get_dm_thread_messages', {
                p_friend: friendId,
                p_before: before || null,
                p_limit: Math.min(limit, 200)
            });
            if (error) return { ok: false, error: error.message };
            return { ok: true, rows: data || [] };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /** Fetch a single DM row (used to resolve reply_to quotes). */
    async function getDmById(id) {
        if (!id) return { ok: false, error: 'missing_id' };
        try {
            const { data, error } = await getSupabase()
                .from('direct_messages')
                .select(DM_COLUMNS).eq('id', id).maybeSingle();
            if (error) return { ok: false, error: error.message };
            return { ok: true, row: data || null };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    async function sendMessage(friendId, body, attachment, opts) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        const trimmed = String(body || '').trim();
        if (!trimmed && !attachment) return { ok: false, error: 'empty' };
        if (trimmed && trimmed.length > 2000) return { ok: false, error: 'too_long' };
        try {
            const row = { from_id: user.id, to_id: friendId };
            if (trimmed) row.body = trimmed;
            if (attachment) {
                row.attachment_url  = attachment.url;
                row.attachment_type = attachment.type;
                row.attachment_size = attachment.size;
                row.attachment_name = attachment.name;
            }
            if (opts && opts.replyToId) row.reply_to_id = opts.replyToId;
            const { data, error } = await getSupabase()
                .from('direct_messages')
                .insert(row).select(DM_COLUMNS).single();
            if (error) {
                const msg = String(error.message || '').toLowerCase();
                if (msg.includes('not_friends')) return { ok: false, error: 'not_friends' };
                if (msg.includes('blocked'))     return { ok: false, error: 'blocked' };
                if (msg.includes('not_accepted')) return { ok: false, error: 'pending' };
                return { ok: false, error: error.message };
            }
            _cache.inbox = null;
            return { ok: true, message: data };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /** Soft-delete a DM (author only, 5-min grace). Server clears body
        + attachment fields and sets deleted_at. UI renders a tombstone. */
    async function deleteDm(messageId) {
        try {
            const { data, error } = await getSupabase()
                .rpc('delete_dm', { p_msg_id: messageId });
            if (error) {
                const m = (error.message || '').toLowerCase();
                if (m.includes('too_old'))   return { ok: false, error: 'too_old' };
                if (m.includes('not_author'))return { ok: false, error: 'not_author' };
                return { ok: false, error: error.message };
            }
            return data || { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /** Mark all unread messages FROM a friend as read. */
    async function markThreadRead(friendId) {
        const user = await getUser();
        if (!user) return { ok: false };
        try {
            const { error } = await getSupabase()
                .from('direct_messages')
                .update({ read_at: new Date().toISOString() })
                .eq('from_id', friendId)
                .eq('to_id', user.id)
                .is('read_at', null);
            if (error) return { ok: false, error: error.message };
            _cache.inbox = null;
            return { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /* ---- Realtime subscriptions ------------------------------ */
    /**
     * Subscribe to incoming messages for the CURRENT user (across
     * all threads). Used for global unread-badge updates. Returns
     * an unsubscribe fn.
     */
    /* Multiple callers want to know about incoming DMs — the
       /messages/ page (updates inbox + sidebar) AND LpNotify (fires
       the OS/in-page notification). Supabase Realtime forbids
       adding .on() listeners after .subscribe() on the same channel,
       so the naïve "create a channel per caller" approach crashes
       the second subscriber. Instead we create ONE channel per user,
       fan-out INSERT events to a local listeners array, and each
       caller gets their own unsubscribe handle that only removes
       their callback (not the channel). */
    const _incomingListeners = [];
    let _incomingChannel = null;
    let _incomingChannelUid = null;

    async function _ensureIncomingChannel(sb, userId) {
        if (_incomingChannel && _incomingChannelUid === userId) return;
        /* If we had a channel for a different user (rare — session
           swap), tear the old one down before wiring the new user. */
        if (_incomingChannel) {
            try { sb.removeChannel(_incomingChannel); } catch (_) {}
            _incomingChannel = null;
        }
        _incomingChannelUid = userId;
        _incomingChannel = sb.channel('lp_inbox_' + userId.slice(0, 8))
            .on('postgres_changes',
                { event: 'INSERT', schema: 'public', table: 'direct_messages', filter: 'to_id=eq.' + userId },
                (payload) => {
                    _cache.inbox = null;
                    for (const cb of _incomingListeners) {
                        try { cb(payload.new); } catch (_) {}
                    }
                });
        _incomingChannel.subscribe();
    }

    function subscribeToIncoming(onMessage) {
        if (onMessage) _incomingListeners.push(onMessage);
        const sb = getSupabase();
        let cleaned = false;
        (async () => {
            const user = await getUser();
            if (!user || cleaned) return;
            await _ensureIncomingChannel(sb, user.id);
        })();
        return function unsubscribe() {
            cleaned = true;
            if (onMessage) {
                const i = _incomingListeners.indexOf(onMessage);
                if (i !== -1) _incomingListeners.splice(i, 1);
            }
            /* We leave _incomingChannel alive — other listeners may
               still need it. On full sign-out, _clearCache tears it
               down via the auth listener at the bottom of this file. */
        };
    }

    /**
     * Subscribe to messages in ONE thread. Fires for both directions
     * (receiver + echo of sender's own INSERT via postgres_changes).
     * Caller gets {kind, row} — kind is 'insert' for new messages,
     * 'update' for field changes (read_at flipping null → timestamp
     * when the other side marks read). Senders use 'update' to
     * flip their own ✓ → ✓✓ read indicator live.
     * Caller should dedupe by id since the sender also sees the row
     * via the insert RPC return.
     */
    function subscribeToThread(friendId, onMessage) {
        const sb = getSupabase();
        let chan = null;
        let cleaned = false;
        (async () => {
            const user = await getUser();
            if (!user || cleaned) return;
            const threadId = await _computeThreadId(user.id, friendId);
            chan = sb.channel('lp_thread_' + threadId.slice(0, 8))
                .on('postgres_changes',
                    { event: 'INSERT', schema: 'public', table: 'direct_messages', filter: 'thread_id=eq.' + threadId },
                    (payload) => {
                        if (onMessage) try { onMessage({kind:'insert', row: payload.new}); } catch (_) {}
                    })
                .on('postgres_changes',
                    { event: 'UPDATE', schema: 'public', table: 'direct_messages', filter: 'thread_id=eq.' + threadId },
                    (payload) => {
                        if (onMessage) try { onMessage({kind:'update', row: payload.new, old: payload.old}); } catch (_) {}
                    })
                .subscribe();
        })();
        return function unsubscribe() {
            cleaned = true;
            if (chan) { try { getSupabase().removeChannel(chan); } catch (_) {} chan = null; }
        };
    }

    /* ================================================================
       Per-thread mute
       =================
       Stored server-side in thread_mutes (RLS: owner-only). Cached
       locally in a Set<string> keyed by `<kind>:<threadKey>` so
       LpNotify's show() path can consult it synchronously on every
       incoming message without a round-trip.
       ================================================================ */
    const _muteCache = { ready: false, set: new Set() };
    async function _loadMutes() {
        const user = await getUser();
        if (!user) { _muteCache.ready = true; return; }
        try {
            const { data, error } = await getSupabase()
                .from('thread_mutes')
                .select('kind, thread_key')
                .eq('user_id', user.id);
            if (!error && data) {
                _muteCache.set = new Set(data.map(r => r.kind + ':' + r.thread_key));
            }
        } catch (_) {}
        _muteCache.ready = true;
    }
    /* Kick off cache load once per session — idempotent. */
    let _muteLoadPromise = null;
    function _ensureMutesLoaded() {
        if (_muteCache.ready) return Promise.resolve();
        if (_muteLoadPromise) return _muteLoadPromise;
        _muteLoadPromise = _loadMutes().finally(() => { _muteLoadPromise = null; });
        return _muteLoadPromise;
    }

    /** Synchronous check — assumes caller awaited getMutes() at least
        once. For pre-load reliability the notification path calls
        getMutes() at init; after that, isMuted is fire-and-answer. */
    function isMuted(kind, threadKey) {
        return _muteCache.set.has(kind + ':' + threadKey);
    }

    /** Public: fetch (and cache) the user's mute list. Returns an
        array of { kind, thread_key } rows. */
    async function getMutes() {
        await _ensureMutesLoaded();
        return Array.from(_muteCache.set).map(s => {
            const i = s.indexOf(':');
            return { kind: s.slice(0, i), thread_key: s.slice(i + 1) };
        });
    }

    async function muteThread(kind, threadKey) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        try {
            const { error } = await getSupabase()
                .from('thread_mutes')
                .upsert({ user_id: user.id, kind, thread_key: threadKey },
                        { onConflict: 'user_id,kind,thread_key' });
            if (error) return { ok: false, error: error.message };
            _muteCache.set.add(kind + ':' + threadKey);
            return { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    async function unmuteThread(kind, threadKey) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        try {
            const { error } = await getSupabase()
                .from('thread_mutes').delete()
                .eq('user_id', user.id)
                .eq('kind', kind)
                .eq('thread_key', threadKey);
            if (error) return { ok: false, error: error.message };
            _muteCache.set.delete(kind + ':' + threadKey);
            return { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /** Group chat owner-only — remove a member. */
    async function kickGroupChatMember(roomId, targetUserId) {
        try {
            const { data, error } = await getSupabase()
                .rpc('kick_group_chat_member',
                     { p_room: roomId, p_target: targetUserId });
            if (error) {
                const m = (error.message || '').toLowerCase();
                if (m.includes('not_owner'))      return { ok: false, error: 'not_owner' };
                if (m.includes('cannot_kick_self'))return { ok: false, error: 'cannot_kick_self' };
                if (m.includes('not_a_member'))   return { ok: false, error: 'not_a_member' };
                if (m.includes('room_not_found')) return { ok: false, error: 'room_not_found' };
                return { ok: false, error: error.message };
            }
            return data || { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /* ================================================================
       Typing indicator — Realtime broadcast (no DB writes).
       Pattern used by WhatsApp / Signal: the sender pushes a cheap
       "I'm typing" signal on a shared channel, and the receiver's UI
       shows a "..." hint. Throttled client-side to one broadcast per
       3 seconds and auto-cleared by the listener 5 seconds after the
       last signal. No persistence — if the listener joins late, they
       simply don't see past typing activity.

       threadKey is the thread_id (DM) OR room_id (group) — same value
       we already use as the reactions subscribe key, so reusing that
       partition keeps the client-side channel map simple.
       ================================================================ */
    const _typingChannels = new Map(); /* threadKey -> channel (send side, cached) */
    const _typingLastSent = new Map(); /* threadKey -> ts for throttle */

    function _getOrCreateTypingChannel(threadKey) {
        if (_typingChannels.has(threadKey)) return _typingChannels.get(threadKey);
        const sb = getSupabase();
        const ch = sb.channel('lp_typing_' + threadKey.slice(0, 12), {
            config: { broadcast: { self: false, ack: false } }
        });
        ch.subscribe();
        _typingChannels.set(threadKey, ch);
        return ch;
    }

    /** Called from the composer's input handler. Throttles internally
        so a rapid-fire typing user only generates one broadcast per
        3 seconds — keeps Realtime quota + network usage trivial. */
    async function sendTyping(threadKey) {
        if (!threadKey) return;
        const now = Date.now();
        const last = _typingLastSent.get(threadKey) || 0;
        if (now - last < 2800) return;      /* throttle window */
        _typingLastSent.set(threadKey, now);
        const user = await getUser();
        if (!user) return;
        const ch = _getOrCreateTypingChannel(threadKey);
        try {
            await ch.send({ type: 'broadcast', event: 'typing',
                            payload: { from: user.id, at: now } });
        } catch (_) {}
    }

    /** Subscribe to typing events on the given thread. Callback gets
        { from, at } for each ping. Callers are expected to auto-hide
        the indicator themselves after ~5s of no ping — this module
        doesn't own that timer because UI animations differ per page. */
    function subscribeToTyping(threadKey, onPing) {
        if (!threadKey) return function(){};
        const sb = getSupabase();
        const ch = sb.channel('lp_typing_' + threadKey.slice(0, 12), {
            config: { broadcast: { self: false, ack: false } }
        });
        ch.on('broadcast', { event: 'typing' }, (msg) => {
            try { onPing && onPing(msg.payload || {}); } catch (_) {}
        });
        ch.subscribe();
        return function unsubscribe() {
            try { sb.removeChannel(ch); } catch (_) {}
        };
    }

    /* ---- Util ------------------------------------------------ */
    /** Client-side thread_id computation (matches the DB trigger).
        md5(a_uuid || '_' || b_uuid) cast to uuid. */
    async function _computeThreadId(uidA, uidB) {
        const a = uidA < uidB ? uidA : uidB;
        const b = uidA < uidB ? uidB : uidA;
        const text = a + '_' + b;
        const enc = new TextEncoder().encode(text);
        const digest = await crypto.subtle.digest('MD5', enc).catch(() => null);
        if (digest) {
            const bytes = Array.from(new Uint8Array(digest))
                .map(b => b.toString(16).padStart(2, '0'));
            return bytes.slice(0,4).join('') + '-'
                 + bytes.slice(4,6).join('') + '-'
                 + bytes.slice(6,8).join('') + '-'
                 + bytes.slice(8,10).join('') + '-'
                 + bytes.slice(10,16).join('');
        }
        /* Fallback: subtle crypto MD5 may not be supported in all
           browsers. Use a lightweight implementation — thread id
           must match DB's md5() exactly. */
        return _md5ToUuid(text);
    }
    /* Pure-JS MD5 — only used when SubtleCrypto doesn't support MD5
       (Safari). Output format matches postgres md5()::uuid. */
    function _md5ToUuid(str) {
        const bytes = _md5Bytes(str);
        const hex = bytes.map(b => b.toString(16).padStart(2, '0'));
        return hex.slice(0,4).join('') + '-'
             + hex.slice(4,6).join('') + '-'
             + hex.slice(6,8).join('') + '-'
             + hex.slice(8,10).join('') + '-'
             + hex.slice(10,16).join('');
    }
    function _md5Bytes(str){
        /* Minimal MD5 implementation, returns Uint8-like array of 16
           bytes. Based on RFC 1321. */
        function add32(a,b){return (a+b)&0xFFFFFFFF}
        function rol(a,s){return (a<<s)|(a>>>(32-s))}
        function cmn(q,a,b,x,s,t){return add32(rol(add32(add32(a,q),add32(x,t)),s),b)}
        function ff(a,b,c,d,x,s,t){return cmn((b&c)|((~b)&d),a,b,x,s,t)}
        function gg(a,b,c,d,x,s,t){return cmn((b&d)|(c&(~d)),a,b,x,s,t)}
        function hh(a,b,c,d,x,s,t){return cmn(b^c^d,a,b,x,s,t)}
        function ii(a,b,c,d,x,s,t){return cmn(c^(b|(~d)),a,b,x,s,t)}
        function str2blks(s){
            const nbl=((s.length+8)>>6)+1, blks=new Array(nbl*16).fill(0);
            for (let i=0;i<s.length;i++) blks[i>>2] |= s.charCodeAt(i)<<((i%4)*8);
            blks[s.length>>2] |= 0x80<<((s.length%4)*8);
            blks[nbl*16-2] = s.length*8;
            return blks;
        }
        const x = str2blks(unescape(encodeURIComponent(str)));
        let a=1732584193,b=-271733879,c=-1732584194,d=271733878;
        for (let i=0;i<x.length;i+=16){
            const olda=a, oldb=b, oldc=c, oldd=d;
            a=ff(a,b,c,d,x[i],7,-680876936);   d=ff(d,a,b,c,x[i+1],12,-389564586);
            c=ff(c,d,a,b,x[i+2],17,606105819); b=ff(b,c,d,a,x[i+3],22,-1044525330);
            a=ff(a,b,c,d,x[i+4],7,-176418897); d=ff(d,a,b,c,x[i+5],12,1200080426);
            c=ff(c,d,a,b,x[i+6],17,-1473231341); b=ff(b,c,d,a,x[i+7],22,-45705983);
            a=ff(a,b,c,d,x[i+8],7,1770035416); d=ff(d,a,b,c,x[i+9],12,-1958414417);
            c=ff(c,d,a,b,x[i+10],17,-42063); b=ff(b,c,d,a,x[i+11],22,-1990404162);
            a=ff(a,b,c,d,x[i+12],7,1804603682); d=ff(d,a,b,c,x[i+13],12,-40341101);
            c=ff(c,d,a,b,x[i+14],17,-1502002290); b=ff(b,c,d,a,x[i+15],22,1236535329);
            a=gg(a,b,c,d,x[i+1],5,-165796510); d=gg(d,a,b,c,x[i+6],9,-1069501632);
            c=gg(c,d,a,b,x[i+11],14,643717713); b=gg(b,c,d,a,x[i],20,-373897302);
            a=gg(a,b,c,d,x[i+5],5,-701558691); d=gg(d,a,b,c,x[i+10],9,38016083);
            c=gg(c,d,a,b,x[i+15],14,-660478335); b=gg(b,c,d,a,x[i+4],20,-405537848);
            a=gg(a,b,c,d,x[i+9],5,568446438); d=gg(d,a,b,c,x[i+14],9,-1019803690);
            c=gg(c,d,a,b,x[i+3],14,-187363961); b=gg(b,c,d,a,x[i+8],20,1163531501);
            a=gg(a,b,c,d,x[i+13],5,-1444681467); d=gg(d,a,b,c,x[i+2],9,-51403784);
            c=gg(c,d,a,b,x[i+7],14,1735328473); b=gg(b,c,d,a,x[i+12],20,-1926607734);
            a=hh(a,b,c,d,x[i+5],4,-378558); d=hh(d,a,b,c,x[i+8],11,-2022574463);
            c=hh(c,d,a,b,x[i+11],16,1839030562); b=hh(b,c,d,a,x[i+14],23,-35309556);
            a=hh(a,b,c,d,x[i+1],4,-1530992060); d=hh(d,a,b,c,x[i+4],11,1272893353);
            c=hh(c,d,a,b,x[i+7],16,-155497632); b=hh(b,c,d,a,x[i+10],23,-1094730640);
            a=hh(a,b,c,d,x[i+13],4,681279174); d=hh(d,a,b,c,x[i],11,-358537222);
            c=hh(c,d,a,b,x[i+3],16,-722521979); b=hh(b,c,d,a,x[i+6],23,76029189);
            a=hh(a,b,c,d,x[i+9],4,-640364487); d=hh(d,a,b,c,x[i+12],11,-421815835);
            c=hh(c,d,a,b,x[i+15],16,530742520); b=hh(b,c,d,a,x[i+2],23,-995338651);
            a=ii(a,b,c,d,x[i],6,-198630844); d=ii(d,a,b,c,x[i+7],10,1126891415);
            c=ii(c,d,a,b,x[i+14],15,-1416354905); b=ii(b,c,d,a,x[i+5],21,-57434055);
            a=ii(a,b,c,d,x[i+12],6,1700485571); d=ii(d,a,b,c,x[i+3],10,-1894986606);
            c=ii(c,d,a,b,x[i+10],15,-1051523); b=ii(b,c,d,a,x[i+1],21,-2054922799);
            a=ii(a,b,c,d,x[i+8],6,1873313359); d=ii(d,a,b,c,x[i+15],10,-30611744);
            c=ii(c,d,a,b,x[i+6],15,-1560198380); b=ii(b,c,d,a,x[i+13],21,1309151649);
            a=ii(a,b,c,d,x[i+4],6,-145523070); d=ii(d,a,b,c,x[i+11],10,-1120210379);
            c=ii(c,d,a,b,x[i+2],15,718787259); b=ii(b,c,d,a,x[i+9],21,-343485551);
            a=add32(a,olda); b=add32(b,oldb); c=add32(c,oldc); d=add32(d,oldd);
        }
        const res=[];
        [a,b,c,d].forEach(v=>{ for(let i=0;i<4;i++) res.push((v>>>(i*8))&0xFF); });
        return res;
    }

    /* ---- Wire auth cache invalidation ------------------------ */
    (function wire() {
        try {
            getSupabase().auth.onAuthStateChange((event) => {
                if (event === 'SIGNED_OUT') _clearCache();
            });
        } catch (_) {}
    })();

    /* ================================================================
       Group chat — schema §6. Parallel surface to the DM API above.
       Rooms have a concept of "members" (as opposed to the DM model
       where the pair itself defines membership), so the API exposes
       member-list + invite/leave flows alongside message send/receive.
       Caching uses the same TTLs as DMs: 60s inbox-style list, no
       cache for roster (small enough to refetch on demand).
       ================================================================ */
    const _grpCache = { list: null, uid: null };
    function _grpSetUid(uid){ if(_grpCache.uid!==uid){ _grpCache.list=null; _grpCache.uid=uid; } }

    async function getGroupChats({ force = false } = {}) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        _grpSetUid(user.id);
        if (!force && _grpCache.list && Date.now() - _grpCache.list.savedAt < INBOX_TTL_MS) {
            return { ok: true, rows: _grpCache.list.rows };
        }
        try {
            const { data, error } = await getSupabase().rpc('group_chat_list');
            if (error) return { ok: false, error: error.message };
            _grpCache.list = { rows: data || [], savedAt: Date.now() };
            return { ok: true, rows: data || [] };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    async function createGroupChat(name, memberIds, iconEmoji) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        const trimmed = String(name || '').trim();
        if (!trimmed) return { ok: false, error: 'invalid_name' };
        if (trimmed.length > 60) return { ok: false, error: 'invalid_name' };
        try {
            const { data, error } = await getSupabase().rpc('create_group_chat', {
                p_name: trimmed,
                p_member_ids: memberIds || [],
                p_icon_emoji: iconEmoji || '💬'
            });
            if (error) return { ok: false, error: error.message };
            _grpCache.list = null;
            return data || { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    async function inviteToGroupChat(roomId, userId) {
        try {
            const { data, error } = await getSupabase().rpc('invite_to_group_chat', {
                p_room: roomId, p_user: userId
            });
            if (error) return { ok: false, error: error.message };
            _grpCache.list = null;
            return data || { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    async function leaveGroupChat(roomId) {
        try {
            const { data, error } = await getSupabase().rpc('leave_group_chat', { p_room: roomId });
            if (error) return { ok: false, error: error.message };
            _grpCache.list = null;
            return data || { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    async function getGroupMembers(roomId) {
        try {
            const { data, error } = await getSupabase().rpc('group_chat_members', { p_room: roomId });
            if (error) return { ok: false, error: error.message };
            return { ok: true, rows: data || [] };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /* Shared column list for group messages. Like DMs we now include
       the deleted rows + attachment fields + reply_to_id, and let the
       UI render tombstones for deleted ones. */
    const GROUP_COLUMNS = 'id, room_id, from_id, body, created_at, edited_at, deleted_at, attachment_url, attachment_type, attachment_size, attachment_name, reply_to_id';

    async function getGroupMessages(roomId, { before = null, limit = 50 } = {}) {
        try {
            let q = getSupabase()
                .from('chat_messages')
                .select(GROUP_COLUMNS)
                .eq('room_id', roomId)
                .order('created_at', { ascending: false })
                .limit(Math.min(limit, 200));
            if (before) q = q.lt('created_at', before);
            const { data, error } = await q;
            if (error) return { ok: false, error: error.message };
            return { ok: true, rows: (data || []).slice().reverse() };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /** Single-row fetch for reply-quote resolution. */
    async function getGroupMessageById(id) {
        if (!id) return { ok: false, error: 'missing_id' };
        try {
            const { data, error } = await getSupabase()
                .from('chat_messages')
                .select(GROUP_COLUMNS).eq('id', id).maybeSingle();
            if (error) return { ok: false, error: error.message };
            return { ok: true, row: data || null };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    async function sendGroupMessage(roomId, body, attachment, opts) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        const trimmed = String(body || '').trim();
        if (!trimmed && !attachment) return { ok: false, error: 'empty' };
        if (trimmed && trimmed.length > 2000) return { ok: false, error: 'too_long' };
        try {
            const row = { room_id: roomId, from_id: user.id };
            if (trimmed) row.body = trimmed;
            if (attachment) {
                row.attachment_url  = attachment.url;
                row.attachment_type = attachment.type;
                row.attachment_size = attachment.size;
                row.attachment_name = attachment.name;
            }
            if (opts && opts.replyToId) row.reply_to_id = opts.replyToId;
            const { data, error } = await getSupabase()
                .from('chat_messages')
                .insert(row).select(GROUP_COLUMNS).single();
            if (error) return { ok: false, error: error.message };
            _grpCache.list = null;
            return { ok: true, message: data };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /** Delete group message — author (5 min) or room creator (any age). */
    async function deleteGroupMessage(messageId) {
        try {
            const { data, error } = await getSupabase()
                .rpc('delete_group_msg', { p_msg_id: messageId });
            if (error) {
                const m = (error.message || '').toLowerCase();
                if (m.includes('too_old'))       return { ok: false, error: 'too_old' };
                if (m.includes('not_authorized'))return { ok: false, error: 'not_authorized' };
                return { ok: false, error: error.message };
            }
            return data || { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /* ---- Attachments ----------------------------------------- */
    /* Upload a file to the chat-attachments storage bucket. Path is
       always {user_id}/{uuid}-{safe_name} so:
         (a) Storage RLS gates write access by folder prefix
         (b) Filenames are non-enumerable across the bucket
         (c) Per-user cleanup is a single prefix delete
       Returns the public URL + metadata for embedding in a message
       row. Caller validates type/size locally before calling so we
       don't waste an upload that the DB CHECK would reject anyway. */
    const ATTACH_MAX_BYTES = 10 * 1024 * 1024;
    const ATTACH_ALLOWED = /^image\/(png|jpeg|jpg|gif|webp|heic)$/;

    async function uploadAttachment(file) {
        const user = await getUser();
        if (!user) return { ok: false, error: 'not_authenticated' };
        if (!file) return { ok: false, error: 'no_file' };
        if (file.size > ATTACH_MAX_BYTES) return { ok: false, error: 'too_large' };
        const type = String(file.type || '').toLowerCase();
        if (!ATTACH_ALLOWED.test(type)) return { ok: false, error: 'bad_type' };

        /* Sanitise the filename — strip path separators and weird
           chars, enforce a max length. The uuid prefix guarantees
           uniqueness even when two users upload "photo.jpg". */
        const rawName = String(file.name || 'image').replace(/[/\\?%*:|"<>]/g, '_').slice(-100);
        const ext = (rawName.match(/\.[A-Za-z0-9]+$/) || [''])[0];
        const stem = rawName.replace(/\.[A-Za-z0-9]+$/, '').replace(/[^A-Za-z0-9_\-가-힣]/g, '_').slice(0, 60) || 'image';
        const safeName = stem + ext;
        const id = (crypto.randomUUID && crypto.randomUUID()) ||
                   (Date.now().toString(36) + Math.random().toString(36).slice(2, 10));
        const path = user.id + '/' + id + '-' + safeName;

        try {
            const sb = getSupabase();
            const up = await sb.storage.from('chat-attachments')
                .upload(path, file, { contentType: type, cacheControl: '31536000', upsert: false });
            if (up.error) return { ok: false, error: up.error.message };
            const { data: pub } = sb.storage.from('chat-attachments').getPublicUrl(path);
            return { ok: true, url: pub.publicUrl, type, size: file.size, name: safeName };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    async function markGroupRead(roomId) {
        try {
            const { error } = await getSupabase().rpc('mark_group_chat_read', { p_room: roomId });
            if (error) return { ok: false, error: error.message };
            _grpCache.list = null;
            return { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /** Subscribe to a single room's INSERTs. Same lifecycle contract
        as subscribeToThread: returns an unsubscribe() fn. */
    function subscribeToGroupRoom(roomId, onMessage) {
        const sb = getSupabase();
        let chan = null; let cleaned = false;
        (async () => {
            if (cleaned) return;
            chan = sb.channel('lp_groupchat_' + roomId.slice(0, 8))
                .on('postgres_changes',
                    { event: 'INSERT', schema: 'public', table: 'chat_messages', filter: 'room_id=eq.' + roomId },
                    (payload) => { if (onMessage) try { onMessage(payload.new); } catch (_) {} })
                .subscribe();
        })();
        return function unsubscribe() {
            cleaned = true;
            if (chan) { try { sb.removeChannel(chan); } catch (_) {} chan = null; }
        };
    }

    /** Subscribe to room-membership changes (someone invited / left)
        for a single room. Used by the members sheet to live-update. */
    function subscribeToGroupMembers(roomId, onChange) {
        const sb = getSupabase();
        let chan = null; let cleaned = false;
        (async () => {
            if (cleaned) return;
            chan = sb.channel('lp_groupmem_' + roomId.slice(0, 8))
                .on('postgres_changes',
                    { event: '*', schema: 'public', table: 'chat_members', filter: 'room_id=eq.' + roomId },
                    (payload) => { if (onChange) try { onChange(payload); } catch (_) {} })
                .subscribe();
        })();
        return function unsubscribe() {
            cleaned = true;
            if (chan) { try { sb.removeChannel(chan); } catch (_) {} chan = null; }
        };
    }

    /** Sum unread across all group rooms. Piggybacks on the list cache. */
    async function getGroupUnreadCount() {
        const r = await getGroupChats();
        if (!r.ok) return 0;
        return r.rows.reduce((n, x) => n + Number(x.unread_count || 0), 0);
    }

    /* ================================================================
       Reactions (schema §8) — unified across DM + group messages.
       kind='dm'|'group' + message_id discriminates. toggle_reaction
       RPC handles add-or-remove in one round-trip. Realtime filter
       uses thread_key so both kinds share a single subscription
       pattern. Client never needs to know the pg table name of the
       parent message.
       ================================================================ */

    async function getReactions(kind, messageIds) {
        if (!Array.isArray(messageIds) || !messageIds.length) return { ok: true, byId: {} };
        try {
            const { data, error } = await getSupabase()
                .from('message_reactions')
                .select('message_id, user_id, emoji')
                .eq('kind', kind)
                .in('message_id', messageIds);
            if (error) return { ok: false, error: error.message };
            /* Shape: { [msgId]: { [emoji]: [user_id, ...] } } — O(1)
               lookup in the bubble renderer + cheap "did I react?"
               check by user_id. */
            const byId = {};
            (data || []).forEach(r => {
                const m = byId[r.message_id] || (byId[r.message_id] = {});
                (m[r.emoji] || (m[r.emoji] = [])).push(r.user_id);
            });
            return { ok: true, byId };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    async function toggleReaction(kind, messageId, emoji) {
        try {
            const { data, error } = await getSupabase()
                .rpc('toggle_reaction', { p_kind: kind, p_msg_id: messageId, p_emoji: emoji });
            if (error) return { ok: false, error: error.message };
            return data || { ok: true };
        } catch (e) { return { ok: false, error: String(e) }; }
    }

    /** Subscribe to reaction changes in a specific thread (DM thread_id
        or group room_id). Fires for INSERT + DELETE with the new/old
        row so the caller can patch local chip state without a refetch. */
    function subscribeToReactions(threadKey, onChange) {
        const sb = getSupabase();
        let chan = null; let cleaned = false;
        (async () => {
            if (cleaned) return;
            const shortKey = (threadKey || '').slice(0, 8);
            chan = sb.channel('lp_reactions_' + shortKey)
                .on('postgres_changes',
                    { event: 'INSERT', schema: 'public', table: 'message_reactions', filter: 'thread_key=eq.' + threadKey },
                    (p) => { if (onChange) try { onChange({ kind: 'insert', row: p.new }); } catch (_) {} })
                .on('postgres_changes',
                    { event: 'DELETE', schema: 'public', table: 'message_reactions', filter: 'thread_key=eq.' + threadKey },
                    (p) => { if (onChange) try { onChange({ kind: 'delete', row: p.old }); } catch (_) {} })
                .subscribe();
        })();
        return function unsubscribe() {
            cleaned = true;
            if (chan) { try { sb.removeChannel(chan); } catch (_) {} chan = null; }
        };
    }

    window.LpSocial = {
        getFriends, sendFriendRequest, acceptFriendRequest,
        removeFriend, blockFriend,
        getInbox, getUnreadCount, getThreadMessages, sendMessage, markThreadRead,
        getDmById, deleteDm,
        subscribeToIncoming, subscribeToThread,
        /* Typing indicator (Realtime broadcast, thread-key partitioned) */
        sendTyping, subscribeToTyping,
        /* Per-thread mute (DM + group) */
        getMutes, muteThread, unmuteThread, isMuted,
        /* Group admin — kick member (owner only) */
        kickGroupChatMember,
        /* Group chat */
        getGroupChats, createGroupChat, inviteToGroupChat, leaveGroupChat,
        getGroupMembers, getGroupMessages, sendGroupMessage, markGroupRead,
        getGroupMessageById, deleteGroupMessage,
        subscribeToGroupRoom, subscribeToGroupMembers, getGroupUnreadCount,
        /* Attachments */
        uploadAttachment,
        /* Reactions */
        getReactions, toggleReaction, subscribeToReactions,
        clearCache: _clearCache
    };
})();
