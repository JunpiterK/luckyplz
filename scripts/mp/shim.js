/* supabase-js Realtime 호환 심 (테스트 전용 — relay.mjs 가 /vendor/supabase.min.js 대신 서빙)
   흉내 내는 표면: createClient().channel(name,opts).on('broadcast',{event},cb).subscribe(cb) / send / unsubscribe,
   removeChannel, getChannels, rpc(fn,args), auth.* (빈 세션).
   실제 realtime-js 2.104 와 같은 함정도 재현: 같은 토픽 channel() 은 기존 객체를 돌려준다. */
(function () {
    'use strict';
    var LABEL = (function () { try { return window.__mpLabel || sessionStorage.getItem('__mpLabel') || 'page'; } catch (_) { return 'page'; } })();
    function Client() {
        var self = this, ws = null, open = false, q = [], chans = [], rpcs = {}, rid = 1, refN = 1;
        function url() { return (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/__relay?label=' + encodeURIComponent(LABEL); }
        function connect() {
            ws = new WebSocket(url());
            ws.onopen = function () { open = true; var qq = q; q = []; qq.forEach(function (m) { ws.send(m); }); chans.forEach(function (c) { if (c._want) c._join(); }); };
            ws.onmessage = function (ev) {
                var m; try { m = JSON.parse(ev.data); } catch (_) { return; }
                if (m.t === 'suback') chans.forEach(function (c) { if (c.topic === m.topic && c._ref === m.ref) c._joined(); });
                else if (m.t === 'bc') chans.forEach(function (c) { if (c.topic === m.topic && c._state === 'joined') c._dispatch(m.event, m.payload); });
                else if (m.t === 'rpcres') { var r = rpcs[m.id]; if (r) { delete rpcs[m.id]; r({ data: m.data, error: m.error }); } }
            };
            ws.onclose = function () {
                var was = open; open = false;
                chans.forEach(function (c) { if (c._state === 'joined') { c._state = 'errored'; c._status('CHANNEL_ERROR'); } });
                setTimeout(connect, was ? 1000 : 2000);
            };
            ws.onerror = function () {};
        }
        function raw(o) { var s = JSON.stringify(o); if (open) ws.send(s); else q.push(s); }
        connect();
        function Channel(name, opts) {
            this.topic = name; this.opts = opts || {}; this._b = []; this._cb = null; this._state = 'closed'; this._want = false; this._ref = 0;
        }
        Channel.prototype.on = function (type, filter, cb) { if (type === 'broadcast') this._b.push({ ev: filter && filter.event, cb: cb }); return this; };
        Channel.prototype.subscribe = function (cb) { this._cb = cb || null; this._want = true; this._join(); return this; };
        Channel.prototype._join = function () { this._ref = refN++; this._state = 'joining'; if (open) raw({ t: 'sub', topic: this.topic, ref: this._ref }); };
        Channel.prototype._joined = function () { this._state = 'joined'; this._status('SUBSCRIBED'); };
        Channel.prototype._status = function (s) { var cb = this._cb; if (cb) setTimeout(function () { try { cb(s); } catch (_) {} }, 0); };
        Channel.prototype._dispatch = function (event, payload) {
            this._b.forEach(function (b) { if (b.ev === event || b.ev === '*') { try { b.cb({ type: 'broadcast', event: event, payload: payload }); } catch (e) { console.error(e); } } });
        };
        Channel.prototype.send = function (m) {
            if (!m || m.type !== 'broadcast') return Promise.resolve('error');
            if (this._state !== 'joined') return Promise.resolve('error');
            raw({ t: 'bc', topic: this.topic, event: m.event, payload: m.payload });
            return Promise.resolve('ok');
        };
        Channel.prototype.unsubscribe = function () {
            var c = this; c._want = false;
            if (c._state !== 'closed') { raw({ t: 'unsub', topic: c.topic }); c._state = 'closed'; c._status('CLOSED'); }
            return new Promise(function (r) { setTimeout(function () { r('ok'); }, 15); });
        };
        this.channel = function (name, opts) {
            for (var i = 0; i < chans.length; i++) if (chans[i].topic === name) return chans[i];
            var c = new Channel(name, opts); chans.push(c); return c;
        };
        this.getChannels = function () { return chans.slice(); };
        this.removeChannel = function (c) {
            return c.unsubscribe().then(function (r) { var i = chans.indexOf(c); if (i >= 0) chans.splice(i, 1); return r; });
        };
        this.removeAllChannels = function () { return Promise.all(chans.slice().map(self.removeChannel)); };
        this.rpc = function (fn, args) { return new Promise(function (res) { var id = rid++; rpcs[id] = res; raw({ t: 'rpc', id: id, fn: fn, args: args }); setTimeout(function () { if (rpcs[id]) { delete rpcs[id]; res({ data: null, error: { message: 'timeout' } }); } }, 8000); }); };
        this.from = function () { throw new Error('REST blocked in mp harness'); };
        this.auth = {
            getUser: function () { return Promise.resolve({ data: { user: null }, error: null }); },
            getSession: function () { return Promise.resolve({ data: { session: null }, error: null }); },
            onAuthStateChange: function () { return { data: { subscription: { unsubscribe: function () {} } } }; },
            signInAnonymously: function () { return Promise.resolve({ data: null, error: { message: 'disabled in harness' } }); }
        };
        this.__shim = true;
    }
    window.supabase = { createClient: function () { return new Client(); }, __shim: true };
})();
