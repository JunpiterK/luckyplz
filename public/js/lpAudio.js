/* LPAudio — shared Web Audio engine for LuckyPlz action games.
 *
 * Why a shared module: every action game (snake/pacman/burger/dodge) needs
 * the same robust unlock + sfx primitives. Per-game copies kept drifting
 * (pacman had Web Audio, the other three had nothing) and silently failing
 * because resume() races. This module fixes the unlock once and exposes
 * a tiny API any game can drop in.
 *
 * Target browsers: Chromium (Android Chrome, PC Chrome, MS Edge). iOS
 * Safari silent-switch workaround is intentionally NOT included — those
 * games are login-gated and not officially targeted at iOS.
 *
 * Key correctness moves vs. the previous per-game copies:
 *  1. Unlock fires on capture-phase pointerdown/touchstart/keydown so
 *     it runs BEFORE the click handler that triggers a sfx call. The
 *     resume() Promise hadn't resolved yet in the old race.
 *  2. Plays a 1-sample silent BufferSource synchronously inside the
 *     gesture. Chromium treats this as the canonical "wake the context"
 *     gesture; subsequent osc.start() calls are guaranteed to be
 *     audible without the 0.04s offset hack.
 *  3. All sfx funnel through a master GainNode so a single mute toggle
 *     silences everything (persisted in localStorage).
 */
(function (global) {
    'use strict';

    let _ac = null;
    let _master = null;
    let _unlocked = false;
    let _silenceBuf = null;
    let _muted = false;

    try { _muted = localStorage.getItem('lpAudio.muted') === '1'; } catch (_) {}

    function ctx() {
        if (!_ac) {
            const AC = global.AudioContext || global.webkitAudioContext;
            if (!AC) return null;
            _ac = new AC();
            _master = _ac.createGain();
            _master.gain.value = _muted ? 0 : 1;
            _master.connect(_ac.destination);
        }
        return _ac;
    }

    function unlock() {
        if (_unlocked) {
            const c = ctx();
            if (c && c.state === 'suspended') { try { c.resume(); } catch (_) {} }
            return;
        }
        const c = ctx();
        if (!c) return;
        try {
            if (c.state === 'suspended') c.resume();
            if (!_silenceBuf) _silenceBuf = c.createBuffer(1, 1, 22050);
            const src = c.createBufferSource();
            src.buffer = _silenceBuf;
            src.connect(c.destination);
            src.start(0);
            _unlocked = true;
        } catch (_) {}
    }

    /* Capture phase ensures we run before any same-event click handler
       that calls into LPAudio.beep(...) — otherwise the first sound of
       the session lands while the context is still suspended. */
    ['pointerdown', 'touchstart', 'keydown', 'mousedown', 'click'].forEach(function (ev) {
        document.addEventListener(ev, unlock, { capture: true, passive: true });
    });

    function _start() {
        const c = ctx(); if (!c) return null;
        /* Tiny offset absorbs any leftover scheduling jitter without
           being audible as a click delay. */
        return c.currentTime + 0.005;
    }

    function beep(opts) {
        if (_muted) return;
        unlock();
        const c = ctx(); if (!c) return;
        opts = opts || {};
        try {
            const t0 = _start();
            const dur = opts.dur != null ? opts.dur : 0.1;
            const vol = (opts.vol != null ? opts.vol : 0.18);
            const decay = opts.decay != null ? opts.decay : 0.7;
            const osc = c.createOscillator();
            const g = c.createGain();
            osc.type = opts.type || 'square';
            osc.frequency.setValueAtTime(opts.freq || 440, t0);
            if (opts.slide != null) {
                osc.frequency.linearRampToValueAtTime(opts.slide, t0 + dur);
            }
            g.gain.setValueAtTime(vol, t0);
            g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur * decay);
            osc.connect(g); g.connect(_master);
            osc.start(t0); osc.stop(t0 + dur);
        } catch (_) {}
    }

    /* notes: array of {freq, dur, type?, vol?, slide?, decay?} or
       shorthand {f, d}. Plays back-to-back from the same start time. */
    function seq(notes, opts) {
        if (_muted) return;
        unlock();
        const c = ctx(); if (!c) return;
        opts = opts || {};
        try {
            const baseVol = opts.vol != null ? opts.vol : 0.18;
            const baseType = opts.type || 'square';
            const gap = opts.gap || 0;
            let t = _start();
            for (let i = 0; i < notes.length; i++) {
                const n = notes[i];
                const f = n.freq != null ? n.freq : n.f;
                const d = n.dur != null ? n.dur : n.d;
                if (f == null || d == null) continue;
                if (f === 0) { t += d; continue; } /* rest */
                const osc = c.createOscillator();
                const g = c.createGain();
                osc.type = n.type || baseType;
                osc.frequency.setValueAtTime(f, t);
                if (n.slide != null) osc.frequency.linearRampToValueAtTime(n.slide, t + d);
                const v = n.vol != null ? n.vol : baseVol;
                const decay = n.decay != null ? n.decay : 0.7;
                g.gain.setValueAtTime(v, t);
                g.gain.exponentialRampToValueAtTime(0.0001, t + d * decay);
                osc.connect(g); g.connect(_master);
                osc.start(t); osc.stop(t + d);
                t += d + gap;
            }
        } catch (_) {}
    }

    function noise(opts) {
        if (_muted) return;
        unlock();
        const c = ctx(); if (!c) return;
        opts = opts || {};
        try {
            const dur = opts.dur != null ? opts.dur : 0.15;
            const vol = opts.vol != null ? opts.vol : 0.15;
            const buf = c.createBuffer(1, Math.max(1, Math.floor(c.sampleRate * dur)), c.sampleRate);
            const data = buf.getChannelData(0);
            for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
            const src = c.createBufferSource();
            src.buffer = buf;
            const g = c.createGain();
            const t0 = _start();
            g.gain.setValueAtTime(vol, t0);
            g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
            src.connect(g); g.connect(_master);
            src.start(t0);
        } catch (_) {}
    }

    /* chord(freqs, opts) — fires multiple oscillators simultaneously
       at the same start time. Lets games build bell/harmony textures
       (e.g. burger complete, dodge zone chime) by stacking partials
       on top of LPAudio.beep base tones. */
    function chord(freqs, opts) {
        if (!Array.isArray(freqs)) return;
        opts = opts || {};
        for (let i = 0; i < freqs.length; i++) {
            beep({
                freq: freqs[i],
                dur: opts.dur,
                vol: opts.vol != null ? opts.vol : 0.12,
                type: opts.type,
                decay: opts.decay,
                slide: opts.slide
            });
        }
    }

    function setMuted(m) {
        _muted = !!m;
        try { localStorage.setItem('lpAudio.muted', _muted ? '1' : '0'); } catch (_) {}
        if (_master) _master.gain.value = _muted ? 0 : 1;
    }
    function isMuted() { return _muted; }
    function toggleMuted() { setMuted(!_muted); return _muted; }
    function state() { const c = _ac; return c ? c.state : 'no-context'; }

    /* Debug overlay — append a tiny fixed-position state badge when the
       URL has ?audiodebug=1 (or ?audiodebug=anything truthy). Lets the
       user diagnose live whether LPAudio is unlocked + running on their
       device without opening DevTools. Self-contained (no CSS file). */
    function _maybeMountDebugBadge() {
        try {
            const q = (location.search || '');
            if (!/[?&]audiodebug=([^&]+)/.test(q)) return;
            if (document.getElementById('lpAudioDebug')) return;
            const mount = function () {
                if (document.getElementById('lpAudioDebug')) return;
                const el = document.createElement('div');
                el.id = 'lpAudioDebug';
                el.style.cssText = 'position:fixed;left:8px;bottom:8px;z-index:9999;'
                    + 'background:rgba(0,0,0,.78);color:#0f0;padding:6px 9px;'
                    + 'border-radius:8px;font:600 11px/1.3 monospace;'
                    + 'border:1px solid #0f0;pointer-events:auto;'
                    + 'cursor:pointer;letter-spacing:.02em';
                el.title = 'tap to play test beep';
                el.addEventListener('click', function () {
                    unlock();
                    beep({ freq: 880, dur: 0.12, vol: 0.2, type: 'square' });
                });
                (document.body || document.documentElement).appendChild(el);
                const tick = function () {
                    el.textContent = '🔊 ' + state() + (_unlocked ? ' · unlocked' : ' · LOCKED')
                        + (_muted ? ' · MUTED' : '');
                    requestAnimationFrame(tick);
                };
                tick();
            };
            if (document.body) mount();
            else document.addEventListener('DOMContentLoaded', mount, { once: true });
        } catch (_) {}
    }
    _maybeMountDebugBadge();

    global.LPAudio = {
        unlock: unlock,
        beep: beep,
        seq: seq,
        noise: noise,
        chord: chord,
        setMuted: setMuted,
        isMuted: isMuted,
        toggleMuted: toggleMuted,
        state: state
    };
})(typeof window !== 'undefined' ? window : this);
