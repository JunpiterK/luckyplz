/* lpGameNav.js — 모든 게임의 일시정지·종료 화면 공통 이동 버튼 (2026-09-24)
 *
 * 운영자: "모든 게임은 정지 및 종료 때 해당 게임의 메인 페이지로 가는 버튼과
 *          luckyplz.com 메인으로 가는 버튼을 모두 제공해야 해 — 게임홈, 전체홈"
 *
 * 사용(각 게임에서 정지·결과 화면을 띄울 때):
 *   LpNav.mount(containerEl)                      // 버튼 줄을 container 끝에 붙인다(멱등)
 *   LpNav.mount(containerEl, {gameHome: fn})      // 게임 홈을 페이지 새로고침 대신 fn 으로
 *   LpNav.html()                                  // innerHTML 로 그리는 게임용 문자열(클릭은 위임 처리)
 * - 게임 홈 = 이 게임의 첫 화면(설정·시작). 기본은 /games/<id>/ 로 다시 연다(방·도전장 같은 쿼리는 뗀다)
 * - 전체 홈 = 사이트 메인. 고른 언어의 홈(/ko/ /ja/ /es/ /pt/, 그 밖은 /)
 * - 캔버스 게임의 touchstart preventDefault 가 클릭을 삼키는 함정(mobile_canvas_click_trap)을 피하려고
 *   버튼은 pointerup 에서도 동작하고, 터치 이벤트 전파를 멈춘다
 */
(function () {
    'use strict';
    if (window.LpNav) return;
    var L = {
        ko: ['게임 홈', '전체 홈'], en: ['Game home', 'Main home'], ja: ['ゲームホーム', 'トップへ'],
        zh: ['游戏首页', '网站首页'], es: ['Inicio del juego', 'Inicio'], pt: ['Início do jogo', 'Início'],
        de: ['Spielstart', 'Startseite'], fr: ['Accueil du jeu', 'Accueil'], ru: ['Меню игры', 'Главная'],
        ar: ['بداية اللعبة', 'الرئيسية'], hi: ['गेम होम', 'मुख्य पेज'], th: ['หน้าเกม', 'หน้าหลัก'],
        id: ['Beranda game', 'Beranda'], vi: ['Trang game', 'Trang chủ'], tr: ['Oyun ana sayfası', 'Ana sayfa']
    };
    var HOME = { ko: '/ko/', ja: '/ja/', es: '/es/', pt: '/pt/' };
    function lang() {
        var l = 'en';
        try { l = (localStorage.getItem('luckyplz_lang') || 'en').toLowerCase(); } catch (_) {}
        return l === 'gb' ? 'en' : l;
    }
    function labels() { return L[lang()] || L.en; }
    function gamePath() {
        var m = location.pathname.match(/^\/games\/[a-z0-9-]+\/?/);
        return m ? m[0].replace(/\/?$/, '/') : '/';
    }
    function goGameHome(fn) {
        if (typeof fn === 'function') { try { fn(); return; } catch (_) {} }
        location.href = gamePath();
    }
    function goMainHome() { location.href = HOME[lang()] || '/'; }

    var st = document.createElement('style');
    st.textContent =
        '.lp-nav2{display:flex;gap:8px;width:100%;max-width:340px;margin:12px auto 0;justify-content:center}' +
        '.lp-nav2 button{flex:1;min-width:0;display:flex;align-items:center;justify-content:center;gap:6px;padding:11px 10px;' +
        'border-radius:12px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.07);color:#fff;' +
        'font:800 14px/1.2 "Noto Sans KR",sans-serif;cursor:pointer;touch-action:manipulation;-webkit-tap-highlight-color:transparent;' +
        'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;pointer-events:auto}' +
        '.lp-nav2 button:hover{background:rgba(255,255,255,.14);border-color:rgba(255,230,109,.5)}' +
        '.lp-nav2 button:active{transform:translateY(1px)}' +
        '.lp-nav2 .ic{font-size:15px;line-height:1}';
    (document.head || document.documentElement).appendChild(st);

    function html() {
        var t = labels();
        return '<div class="lp-nav2" data-lp-nav2="1">' +
            '<button type="button" data-lp-nav="game"><span class="ic">🎮</span><span>' + t[0] + '</span></button>' +
            '<button type="button" data-lp-nav="main"><span class="ic">🏠</span><span>' + t[1] + '</span></button></div>';
    }
    /* 위임 처리 — innerHTML 로 다시 그려도 동작. click 과 pointerup 중 먼저 온 쪽 하나만 */
    var fns = new WeakMap();
    var lastAt = 0;
    function handle(e) {
        var b = e.target && e.target.closest && e.target.closest('[data-lp-nav]');
        if (!b) return;
        var now = Date.now();
        if (now - lastAt < 400) return;
        lastAt = now;
        e.preventDefault(); e.stopPropagation();
        var row = b.closest('[data-lp-nav2]');
        if (b.getAttribute('data-lp-nav') === 'main') goMainHome();
        else goGameHome(row && fns.get(row));
    }
    document.addEventListener('click', handle, true);
    document.addEventListener('pointerup', handle, true);
    ['touchstart', 'touchend', 'mousedown'].forEach(function (ev) {
        document.addEventListener(ev, function (e) {
            if (e.target && e.target.closest && e.target.closest('[data-lp-nav2]')) e.stopPropagation();
        }, true);
    });
    function mount(el, opts) {
        if (!el) return null;
        var row = el.querySelector(':scope > [data-lp-nav2]');
        if (!row) {
            var w = document.createElement('div');
            w.innerHTML = html();
            row = w.firstChild;
            el.appendChild(row);
        } else {
            var t = labels(), sp = row.querySelectorAll('button span:last-child');
            if (sp[0]) sp[0].textContent = t[0];
            if (sp[1]) sp[1].textContent = t[1];
        }
        if (opts && typeof opts.gameHome === 'function') fns.set(row, opts.gameHome);
        return row;
    }
    document.addEventListener('lp:langchanged', function () {
        var t = labels();
        document.querySelectorAll('[data-lp-nav2]').forEach(function (row) {
            var sp = row.querySelectorAll('button span:last-child');
            if (sp[0]) sp[0].textContent = t[0];
            if (sp[1]) sp[1].textContent = t[1];
        });
    });
    window.LpNav = { mount: mount, html: html, goGameHome: goGameHome, goMainHome: goMainHome, labels: labels };
})();
