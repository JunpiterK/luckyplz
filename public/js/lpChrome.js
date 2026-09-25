/* lpChrome.js — 게임 페이지 공용 떠 있는 버튼 정리 ('코너 독', 2026-09-25)
 * ─────────────────────────────────────────────────────────────────
 * 23종 모바일 감사에서 나온 문제 4가지를 게임별이 아니라 여기 한 곳에서 푼다.
 *   1. 플레이 중 ⛶ 가 캔버스 왼쪽 위 모서리를 ~40px 가렸다 (스네이크·팩맨·블록스택·벽돌 …)
 *   2. 스크롤되는 설정 화면에서 고정 ⛶ / ? / 🎮 가 내용 위에 겹쳤다
 *   3. ? 가 🔊 에 겹쳤다 — lpHelp 가 400/1200/2500/5000ms 에 재서 늦게 붙는 🔊 를 놓쳤다
 *   4. 🎮 게임 전환 버튼이 게임 화면 위에 떠 있었다
 *
 * 구조
 *   - ⛶(lpFullscreen) · 🔊(lpBgm) · ?(lpHelp) 는 붙는 즉시(MutationObserver) 좌상단 세로 독
 *     `.lp-dock` 한 곳으로 옮겨진다. 순서는 CSS order(⛶ → 🔊 → ?)라 붙는 순서·시점과 무관하고,
 *     숨은 버튼은 flex 흐름에서 빠지므로 서로 겹칠 수 없다. 타이머로 재지 않는다.
 *   - 게임이 버튼을 자기 자리로 데려가면(윷놀이 상단 바 .tb-dock) 그대로 둔다 — body 의 직계 자식만 옮긴다.
 *   - 독 위치는 게임의 '← 홈' 링크·PC 상단 내비 아래(최소 56px). 현지화로 홈 글자가 길어져도 따라간다.
 *
 * 상태
 *   - 플레이 중 → 독이 28px 반투명 손잡이 하나로 접힌다. 누르면 펼쳐지고, 2.5초 손대지 않으면 다시 접힌다.
 *     🎮 는 플레이 중 숨는다. 일시정지·결과·설정 화면에서는 평소대로 보인다.
 *   - 스크롤하는 동안 독과 🎮 는 사라졌다가 멈추면 돌아온다. 화면을 아래로 내린 상태(>32px)면 독은 접힌다.
 *   - 설정 화면이라도 펼친 독이 누를 수 있는 것(버튼·입력칸·링크·칩) 위에 앉으면 접는다(사다리 모드 버튼 등).
 *     접힌 손잡이마저 버튼 위라면 손잡이도 감춘다 — 떠 있는 버튼이 누를 것을 가리는 일이 없게.
 *   - 🎮 아래에 버튼·입력칸·캔버스가 오면 🎮 를 숨긴다(시작 버튼 등 주 버튼을 가리지 않게).
 *
 * '플레이 중' 판정 (앞에서부터)
 *   1. LpChrome.setPlaying(true|false) — 게임이 직접 지정. setPlaying(null) 이면 자동으로 돌아간다
 *   2. body 클래스: lp-chrome-play(권장, 모듈 로드 전에도 된다) · lp-playing · cr-ingame · race-active
 *   3. lpAutoPause 에 등록된 게임의 isActive() — 조작형 아케이드 11종이 이미 등록돼 있어 게임 파일 수정 불필요
 *   4. (약한 판정) 큰 캔버스를 누른 지 6초 이내 + 펼친 독이 그 캔버스와 겹칠 때만
 *
 * 게임이 쓸 수 있는 body 클래스
 *   lp-chrome-play  플레이 중으로 취급          lp-no-swfab  🎮 를 이 페이지에서 끈다(우하단 주 버튼이 있는 게임)
 * 이 모듈이 다는 body 클래스
 *   lp-chrome-playing · lp-chrome-scrolling · lp-chrome-compact
 *
 * 주의
 *   - 독 안의 터치·클릭은 전파를 멈춘다(캔버스 게임의 touchstart preventDefault 가 click 을 삼키는 함정 방지,
 *     게임의 '아무 데나 탭' 입력으로 새지 않게). 문서 capture 리스너(lpFullscreen·lpBgm)는 그대로 받는다.
 *   - z-index 9040: 자동 일시정지 창(9500)·도움말 시트(9600) 아래.
 *   - 게임별 숨김 규칙(body.cr-ingame .lp-fs-btn{display:none!important} 등)은 그대로 먹는다 —
 *     보이는 버튼이 하나도 없으면 손잡이도 뜨지 않는다.
 *
 * API: LpChrome.setPlaying(v) · isPlaying() · expand() · collapse() · refresh() · state()
 */
(function () {
    'use strict';
    if (window.LpChrome) return;

    var isGamePage = /^\/games\//.test(location.pathname) || /^\/lobby\/?/.test(location.pathname);
    var MEMBER_SEL = '.lp-fs-btn,.lp-bgm-btn,.lp-help-fab';
    var HOME_SEL = '#homeBtn,#homeLink,.floating-home,a.home';
    var PLAY_CLASSES = ['lp-chrome-play', 'lp-playing', 'cr-ingame', 'race-active'];
    var EXPAND_MS = 2500;      /* 펼친 독이 다시 접히기까지 */
    var CANVAS_PLAY_MS = 6000; /* 캔버스를 누른 뒤 '플레이 중'으로 보는 시간 */
    var SCROLL_END_MS = 380;
    var SCROLLED_AWAY_PX = 32;

    var override = null;       /* setPlaying() 값. null = 자동 */
    var dock = null, handle = null;
    var expandedUntil = 0, expandTimer = 0;
    var scrolling = false, scrollTimer = 0, scrollEl = null;
    var lastCanvasAt = 0, lastCanvasEl = null;
    var lastPlaying = false, lastCompact = false, collide = false;
    var rafPending = false;

    var HANDLE_LABEL = {
        ko: ['버튼 펼치기', '버튼 접기', '게임 버튼'], en: ['Show controls', 'Hide controls', 'Game controls'],
        ja: ['ボタンを表示', 'ボタンを隠す', 'ゲームボタン'], zh: ['显示按钮', '隐藏按钮', '游戏按钮'],
        es: ['Mostrar controles', 'Ocultar controles', 'Controles'], pt: ['Mostrar controles', 'Ocultar controles', 'Controles']
    };
    function label(i) {
        var l = 'en';
        try { l = (localStorage.getItem('luckyplz_lang') || 'en').toLowerCase(); } catch (_) {}
        return (HANDLE_LABEL[l] || HANDLE_LABEL.en)[i];
    }

    function api(fn) { return function () { try { return fn.apply(null, arguments); } catch (_) {} }; }
    if (!isGamePage) {
        window.LpChrome = { setPlaying: function () {}, isPlaying: function () { return false; }, expand: function () {},
            collapse: function () {}, refresh: function () {}, state: function () { return { enabled: false }; } };
        return;
    }

    /* ---------- CSS ---------- */
    var css = document.createElement('style');
    css.id = 'lp-chrome-style';
    css.textContent =
        '.lp-dock{position:fixed;z-index:9040;left:calc(10px + env(safe-area-inset-left,0px));' +
        'top:calc(56px + env(safe-area-inset-top,0px));top:max(calc(56px + env(safe-area-inset-top,0px)),var(--lp-dock-min,0px));' +
        'display:flex;flex-direction:column;align-items:center;gap:6px;width:40px;pointer-events:none;' +
        'transition:opacity .16s ease}' +
        '.lp-dock>*{pointer-events:auto}' +
        /* 게임 CSS 의 고정 좌표(top:56/102px, 인라인 top)를 독 안에서는 무효로 — 흐름이 자리를 정한다 */
        '.lp-dock>.lp-fs-btn,.lp-dock>.lp-bgm-btn,.lp-dock>.lp-help-fab{position:relative!important;top:auto!important;' +
        'left:auto!important;right:auto!important;bottom:auto!important;margin:0!important;z-index:auto!important;' +
        'width:38px;height:38px;flex:0 0 auto;box-sizing:border-box;' +
        'transition:opacity .16s ease,transform .16s ease,visibility 0s linear 0s,background .15s,border-color .15s}' +
        '.lp-dock>.lp-fs-btn{order:1}.lp-dock>.lp-bgm-btn{order:2}.lp-dock>.lp-help-fab{order:3}' +
        /* 접힘 — 자리(레이아웃)는 남기고 안 보이게. visibility:hidden 이라 포커스·탭도 안 된다 */
        '.lp-dock.is-compact>.lp-fs-btn,.lp-dock.is-compact>.lp-bgm-btn,.lp-dock.is-compact>.lp-help-fab{' +
        'visibility:hidden;opacity:0;transform:scale(.6);pointer-events:none;' +
        'transition:opacity .16s ease,transform .16s ease,visibility 0s linear .16s}' +
        '.lp-dock-handle{display:none;position:absolute;left:6px;top:5px;z-index:1;width:28px;height:28px;padding:0;margin:0;' +
        'border-radius:50%;border:1px solid rgba(255,255,255,.35);background:rgba(10,10,26,.55);color:#fff;cursor:pointer;' +
        'align-items:center;justify-content:center;opacity:.42;backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);' +
        'touch-action:manipulation;-webkit-tap-highlight-color:transparent;transition:opacity .16s ease}' +
        /* 28px 손잡이, 누르는 범위는 44px */
        '.lp-dock-handle::before{content:"";position:absolute;inset:-8px;border-radius:50%}' +
        '.lp-dock-handle:hover,.lp-dock-handle:focus-visible,.lp-dock-handle:active{opacity:1}' +
        '.lp-dock-handle svg{width:14px;height:14px;display:block;pointer-events:none}' +
        '.lp-dock.is-compact:not(.is-empty)>.lp-dock-handle{display:flex}' +
        '.lp-dock.is-scrolling{opacity:0}' +
        '.lp-dock.is-ghost>.lp-dock-handle{visibility:hidden;pointer-events:none}' +
        '.lp-dock.is-scrolling>*{pointer-events:none!important}' +
        '@media(prefers-reduced-motion:reduce){.lp-dock,.lp-dock>*{transition:none!important}}';
    (document.head || document.documentElement).appendChild(css);

    /* ---------- 독 ---------- */
    function ensureDock() {
        if (dock) {
            if (!dock.isConnected && document.body) document.body.appendChild(dock);
            return dock;
        }
        if (!document.body) return null;
        dock = document.createElement('div');
        dock.className = 'lp-dock';
        dock.setAttribute('role', 'toolbar');
        dock.setAttribute('aria-orientation', 'vertical');
        dock.setAttribute('aria-label', label(2));
        handle = document.createElement('button');
        handle.type = 'button';
        handle.className = 'lp-dock-handle';
        handle.setAttribute('aria-expanded', 'false');
        handle.setAttribute('aria-label', label(0));
        handle.innerHTML = '<svg viewBox="0 0 14 14" aria-hidden="true"><circle cx="7" cy="2.2" r="1.6" fill="currentColor"/>' +
            '<circle cx="7" cy="7" r="1.6" fill="currentColor"/><circle cx="7" cy="11.8" r="1.6" fill="currentColor"/></svg>';
        handle.addEventListener('click', function (e) {
            e.preventDefault();
            if (dock.classList.contains('is-compact')) expand(); else collapse();
        });
        dock.appendChild(handle);
        /* 독 안의 입력은 게임까지 내려가지 않게 (버블 단계에서 멈춤 — 버튼 자체의 click 은 이미 처리된 뒤) */
        ['touchstart', 'touchend', 'touchmove', 'pointerdown', 'pointerup', 'mousedown', 'mouseup', 'click'].forEach(function (ev) {
            dock.addEventListener(ev, function (e) {
                e.stopPropagation();
                if (ev === 'pointerdown' || ev === 'touchstart') bump();
            }, { passive: true });
        });
        document.body.appendChild(dock);
        return dock;
    }

    function adopt() {
        if (!ensureDock()) return;
        var els = document.querySelectorAll(MEMBER_SEL);
        for (var i = 0; i < els.length; i++) {
            var el = els[i];
            /* body 직계만 — 게임이 자기 자리로 옮긴 버튼(윷놀이 .tb-dock)은 건드리지 않는다 */
            if (el.parentNode !== document.body && el.parentNode !== document.documentElement) continue;
            el.style.top = ''; el.style.left = '';
            dock.appendChild(el);
        }
    }

    /* ---------- 판정 ---------- */
    function visible(el) {
        if (!el || !el.isConnected) return false;
        var cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') return false;
        var r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
    }
    function playingHard() {
        if (override !== null) return !!override;
        var b = document.body.classList;
        for (var i = 0; i < PLAY_CLASSES.length; i++) if (b.contains(PLAY_CLASSES[i])) return true;
        var ap = window.LpAutoPause;
        if (ap && ap.anyActive) {
            try { if (!(ap.isShowing && ap.isShowing()) && ap.anyActive()) return true; } catch (_) {}
        }
        return false;
    }
    function rectsOverlap(a, b) {
        return Math.min(a.right, b.right) - Math.max(a.left, b.left) > 2 && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 2;
    }
    /* 캔버스를 막 누른 경우 — 펼친 독이 그 캔버스를 가릴 때만 접는다(안 겹치면 접을 이유가 없다) */
    function playingSoft() {
        if (override !== null || !lastCanvasEl || Date.now() - lastCanvasAt > CANVAS_PLAY_MS) return false;
        if (!visible(lastCanvasEl)) return false;
        return rectsOverlap(dock.getBoundingClientRect(), lastCanvasEl.getBoundingClientRect());
    }
    function scrollTopOf(el) {
        if (!el) return 0;
        if (el === document.scrollingElement || el === document.documentElement || el === document.body)
            return window.pageYOffset || (document.scrollingElement || document.documentElement).scrollTop || 0;
        return el.scrollTop || 0;
    }
    function scrolledAway() {
        if (scrollEl && scrollEl !== document.scrollingElement && scrollEl !== document.documentElement && !visible(scrollEl)) scrollEl = null;
        return scrollTopOf(scrollEl || document.scrollingElement) > SCROLLED_AWAY_PX;
    }
    function effectivelyVisible(el) {
        for (var n = el; n && n.nodeType === 1; n = n.parentElement) {
            var cs = getComputedStyle(n);
            if (+cs.opacity < 0.05 || cs.visibility === 'hidden') return false;
        }
        return true;
    }
    var INTERACTIVE = 'button,a[href],input,select,textarea,label,[role="button"],canvas';
    /* div 로 만든 칩·카드(onclick) — cursor:pointer 가 시작되는 요소만 (상속받은 자식·body 전체 pointer 는 제외) */
    function isPointerRoot(el) {
        if (getComputedStyle(el).cursor !== 'pointer') return false;
        var p = el.parentElement;
        return !p || getComputedStyle(p).cursor !== 'pointer';
    }
    /* 🎮 아래(가운데 + 네 모서리 안쪽)에 누를 수 있는 것·캔버스가 있는가 */
    function fabObstructed(fab) {
        var r = fab.getBoundingClientRect();
        if (!r.width) return false;
        /* 원형이라 모서리 바깥은 빼고, 원 안쪽 4x4 격자 */
        var pts = [];
        for (var gx = 0; gx < 4; gx++) for (var gy = 0; gy < 4; gy++) {
            var px = r.left + 6 + gx * (r.width - 12) / 3, py = r.top + 6 + gy * (r.height - 12) / 3;
            var dx = px - (r.left + r.width / 2), dy = py - (r.top + r.height / 2);
            if (dx * dx + dy * dy <= (r.width / 2) * (r.width / 2)) pts.push([px, py]);
        }
        for (var i = 0; i < pts.length; i++) {
            var x = pts[i][0], y = pts[i][1];
            if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) continue;
            var stack = document.elementsFromPoint ? document.elementsFromPoint(x, y) : [];
            for (var j = 0; j < stack.length; j++) {
                var el = stack[j];
                if (el === document.body || el === document.documentElement) break;
                if (el === fab || fab.contains(el) || el.closest('.lp-dock,.lp-sw-modal')) continue;
                if ((el.matches(INTERACTIVE) || isPointerRoot(el)) && effectivelyVisible(el)) return true;
                if (opaqueBg(el)) break;
            }
        }
        return false;
    }

    function opaqueBg(el) {
        var m = getComputedStyle(el).backgroundColor.match(/rgba?\(([^)]+)\)/);
        if (!m) return false;
        var p = m[1].split(',');
        return (p.length > 3 ? +p[3] : 1) >= 0.85;
    }
    /* 펼친 독의 버튼이 누를 수 있는 것(버튼·입력칸·링크·칩) 위에 앉는가 — 설정 화면 겹침(사다리 모드 버튼 등).
       글자·캔버스는 세지 않는다(캔버스는 '플레이 중' 판정이 맡는다). 불투명 배경 아래 깔린 것은 보이지 않으므로 제외 */
    function rectCollides(r) {
        for (var gx = 0; gx < 4; gx++) for (var gy = 0; gy < 4; gy++) {
            var x = r.left + 4 + gx * (r.width - 8) / 3, y = r.top + 4 + gy * (r.height - 8) / 3;
            if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) continue;
            var stack = document.elementsFromPoint ? document.elementsFromPoint(x, y) : [];
            for (var j = 0; j < stack.length; j++) {
                var el = stack[j];
                if (el === document.body || el === document.documentElement) break;
                if (dock.contains(el) || el.closest('.lp-sw-fab,.lp-help-ov,.lp-sw-modal,.lp-ap-ov')) continue;
                if (el.tagName !== 'CANVAS' && (el.matches(INTERACTIVE) || isPointerRoot(el)) && effectivelyVisible(el)) return true;
                if (opaqueBg(el)) break;
            }
        }
        return false;
    }
    function dockCollides() {
        var kids = dock.querySelectorAll(':scope>.lp-fs-btn,:scope>.lp-bgm-btn,:scope>.lp-help-fab');
        for (var i = 0; i < kids.length; i++) {
            if (getComputedStyle(kids[i]).display === 'none') continue;
            /* 접힘 상태의 scale(.6) 이 섞이지 않게 변형 전 자리로 잰다(안 그러면 접힘↔펼침이 깜박인다) */
            var d = dock.getBoundingClientRect(), k = kids[i];
            var r = { left: d.left + k.offsetLeft, top: d.top + k.offsetTop, width: k.offsetWidth, height: k.offsetHeight };
            r.right = r.left + r.width; r.bottom = r.top + r.height;
            if (r.width && rectCollides(r)) return true;
        }
        return false;
    }
    /* 접힌 손잡이(독 왼쪽 위 6,5 에서 28px)마저 버튼 위라면(스크롤로 내용이 밀려 올라온 경우) 손잡이도 감춘다.
       맨 위로 올리거나 스크롤을 멈춘 자리가 바뀌면 다시 판단한다 */
    function handleCollides() {
        var d = dock.getBoundingClientRect();
        return rectCollides({ left: d.left + 6, top: d.top + 5, right: d.left + 34, bottom: d.top + 33, width: 28, height: 28 });
    }

    /* ---------- 배치·상태 ---------- */
    function placeTop() {
        var min = 0;
        var homes = document.querySelectorAll(HOME_SEL);
        for (var i = 0; i < homes.length; i++) {
            var h = homes[i];
            if (dock.contains(h) || !visible(h)) continue;
            var r = h.getBoundingClientRect();
            if (r.left < 140 && r.top < 100 && r.bottom < 170) min = Math.max(min, r.bottom + 8);
        }
        var nav = document.getElementById('pcTopNav');
        if (nav && visible(nav)) min = Math.max(min, nav.getBoundingClientRect().bottom + 8);
        var v = Math.round(min) + 'px';
        if (dock.style.getPropertyValue('--lp-dock-min') !== v) dock.style.setProperty('--lp-dock-min', v);
    }

    function evaluate() {
        rafPending = false;
        if (!document.body || !ensureDock()) return;
        adopt();
        placeTop();

        var kids = dock.querySelectorAll(':scope>.lp-fs-btn,:scope>.lp-bgm-btn,:scope>.lp-help-fab'), any = false;
        for (var i = 0; i < kids.length; i++) if (getComputedStyle(kids[i]).display !== 'none') { any = true; break; }
        dock.classList.toggle('is-empty', !any);

        var hard = playingHard();
        if (!scrolling) collide = !hard && dockCollides();
        var compactWanted = hard || scrolledAway() || playingSoft() || collide;
        var userOpen = Date.now() < expandedUntil;
        var compact = compactWanted && !userOpen;
        if (!compactWanted) expandedUntil = 0;

        dock.classList.toggle('is-compact', compact);
        dock.classList.toggle('is-ghost', compact && !scrolling && handleCollides());
        dock.classList.toggle('is-scrolling', scrolling);
        handle.setAttribute('aria-expanded', compact ? 'false' : 'true');
        handle.setAttribute('aria-label', label(compact ? 0 : 1));

        var bc = document.body.classList;
        bc.toggle('lp-chrome-playing', hard);
        bc.toggle('lp-chrome-compact', compact);
        bc.toggle('lp-chrome-scrolling', scrolling);
        if (hard !== lastPlaying || compact !== lastCompact) {
            lastPlaying = hard; lastCompact = compact;
            try { window.dispatchEvent(new CustomEvent('lp-chrome-change', { detail: { playing: hard, compact: compact } })); } catch (_) {}
        }

        /* 🎮 — 플레이 중·스크롤 중에는 CSS 가 숨긴다. 그 밖에서는 아래에 누를 것이 있으면 숨긴다 */
        var fab = document.getElementById('lpSwFab');
        if (fab && !hard && !scrolling && getComputedStyle(fab).display !== 'none') {
            fab.classList.toggle('lp-obstructed', fabObstructed(fab));
        }
    }
    /* rAF 로 한 프레임에 한 번 — 백그라운드 탭처럼 rAF 가 멈추는 곳을 위해 타이머 폴백도 건다 */
    function schedule() {
        if (rafPending) return;
        rafPending = true;
        var done = false;
        function run() { if (done) return; done = true; evaluate(); }
        if (window.requestAnimationFrame) window.requestAnimationFrame(run);
        setTimeout(run, 120);
    }

    function bump() {
        if (Date.now() < expandedUntil) armCollapse();
    }
    function armCollapse() {
        expandedUntil = Date.now() + EXPAND_MS;
        clearTimeout(expandTimer);
        expandTimer = setTimeout(schedule, EXPAND_MS + 30);
    }
    function expand() {
        var hadFocus = document.activeElement === handle;
        armCollapse(); evaluate();
        /* 키보드로 펼쳤으면 사라진 손잡이 대신 첫 버튼으로 초점을 넘긴다 */
        if (hadFocus) {
            var kids = dock.querySelectorAll(':scope>.lp-fs-btn,:scope>.lp-bgm-btn,:scope>.lp-help-fab'), first = null;
            for (var i = 0; i < kids.length; i++) {
                if (getComputedStyle(kids[i]).display === 'none') continue;
                if (!first || getComputedStyle(kids[i]).order < getComputedStyle(first).order) first = kids[i];
            }
            if (first) try { first.focus({ preventScroll: true }); } catch (_) {}
        }
    }
    function collapse() { expandedUntil = 0; clearTimeout(expandTimer); evaluate(); }

    /* ---------- 신호 ---------- */
    function boot() {
        ensureDock();
        adopt();
        evaluate();
        /* 옮기기는 콜백 안에서 바로(그리기 전) — 버튼이 옛 자리에 한 프레임 비치지 않게 */
        var mo = new MutationObserver(function () { adopt(); schedule(); });
        /* 버튼이 body 에 붙는 순간 · 게임이 body 클래스를 바꾸는 순간 · 독에서 버튼이 빠지는 순간 */
        mo.observe(document.body, { childList: true, attributes: true, attributeFilter: ['class'] });
        mo.observe(dock, { childList: true });
    }

    document.addEventListener('scroll', function (e) {
        var t = e.target;
        var el = (t === document || t === document.documentElement || t === document.body) ? (document.scrollingElement || document.documentElement) : t;
        if (!el || el.nodeType !== 1) return;
        if (el.closest && el.closest('.lp-dock,.lp-help-ov,.lp-sw-modal,.lp-ap-ov')) return;
        /* 화면 대부분을 차지하는 스크롤 영역만 — 카드 안 작은 목록이 굴러가는 건 무시 */
        if (el !== document.scrollingElement && el !== document.documentElement && el.clientHeight < innerHeight * 0.45) return;
        scrollEl = el;
        if (!scrolling) { scrolling = true; expandedUntil = 0; schedule(); }
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(function () { scrolling = false; schedule(); }, SCROLL_END_MS);
    }, { capture: true, passive: true });

    function onPointer(e) {
        var t = e.target;
        if (!t || t.nodeType !== 1) return;
        if (dock && dock.contains(t)) return;
        if (t.tagName === 'CANVAS') {
            var r = t.getBoundingClientRect();
            if (r.width * r.height >= innerWidth * innerHeight * 0.2) { lastCanvasAt = Date.now(); lastCanvasEl = t; }
        }
        /* 펼쳐 둔 독 — 바깥을 누르면 바로 접는다 */
        if (expandedUntil) expandedUntil = 0;
        setTimeout(schedule, 60); /* 화면 전환(시작·결과) 직후 다시 판단 */
    }
    document.addEventListener('pointerdown', onPointer, { capture: true, passive: true });
    if (!window.PointerEvent) document.addEventListener('touchstart', onPointer, { capture: true, passive: true });
    document.addEventListener('keydown', function () { setTimeout(schedule, 60); }, true);
    window.addEventListener('resize', schedule);
    window.addEventListener('orientationchange', function () { setTimeout(schedule, 250); });
    window.addEventListener('lp-fullscreen-change', schedule);
    document.addEventListener('lp:langchanged', schedule);
    /* 게임 상태(isActive)는 이벤트가 없어서 가볍게 폴링 — 화면이 보일 때만 */
    setInterval(function () { if (document.visibilityState !== 'hidden') schedule(); }, 450);

    if (document.body) boot();
    else document.addEventListener('DOMContentLoaded', boot);

    window.LpChrome = {
        setPlaying: api(function (v) { override = (v === null || v === undefined) ? null : !!v; if (v) expandedUntil = 0; schedule(); }),
        isPlaying: api(function () { return playingHard(); }),
        expand: api(expand),
        collapse: api(collapse),
        refresh: api(schedule),
        state: api(function () {
            return {
                enabled: true, override: override, playing: playingHard(), soft: dock ? playingSoft() : false,
                scrolling: scrolling, scrolledAway: scrolledAway(), collide: collide,
                compact: !!(dock && dock.classList.contains('is-compact')),
                members: dock ? [].map.call(dock.querySelectorAll(':scope>' + MEMBER_SEL.split(',').join(',:scope>')), function (b) { return b.className.split(' ')[0]; }) : []
            };
        })
    };
})();
