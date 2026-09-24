/* lpHelp.js — 게임 페이지 도움말 버튼 (2026-09-24)
 *
 * 운영자: "게임에 들어가 스크롤하면 쓸데없는 글이 보인다. 게임 설정·선택만 보이게 하고,
 *          도움말 버튼 하나에 가장 필요한 내용만 간결하게, 언어별로."
 *
 * - 게임 아래 긴 글(.lp-game-about)은 화면에서 숨긴다. 지우지 않는다 — 구글·애드센스는
 *   버튼 뒤에 접힌 글도 정상 색인하므로 검색 노출은 유지된다(운영자 선택: '도움말 안으로 이동').
 * - 왼쪽 세로 버튼 줄(⛶ 전체화면 · 🔊 소리) 맨 아래 빈자리에 ? 버튼을 붙인다 → 기기별 겹침 없음.
 * - 누르면 시트: 맨 위 = 언어별 3~4줄 간단 도움말(lpHelpText.js, 처음 열 때만 불러온다),
 *   아래 '자세히' = 숨겨 둔 긴 글을 시트 안으로 옮겨 펼친다.
 * - 언어는 luckyplz_lang 를 따른다. 간단 도움말이 없는 언어는 영어.
 */
(function () {
    'use strict';
    if (window.LpHelp) return;
    var about = document.querySelector('.lp-game-about');
    var m = location.pathname.match(/^\/games\/([a-z0-9-]+)\/?/);
    if (!about || !m) return;
    var gameId = m[1];
    var V = (function () {
        try { var s = document.currentScript && document.currentScript.src; var q = s && s.match(/[?&]v=([^&]+)/); return q ? q[1] : ''; } catch (_) { return ''; }
    })();

    var UI = {
        ko: { more: '자세히', less: '접기', close: '닫기', help: '도움말' },
        en: { more: 'Full guide (Korean)', less: 'Hide guide', close: 'Close', help: 'Help' },
        ja: { more: '詳しい解説（韓国語）', less: '閉じる', close: '閉じる', help: 'ヘルプ' },
        zh: { more: '详细说明（韩语）', less: '收起', close: '关闭', help: '帮助' },
        es: { more: 'Guía completa (coreano)', less: 'Ocultar guía', close: 'Cerrar', help: 'Ayuda' },
        pt: { more: 'Guia completo (coreano)', less: 'Ocultar guia', close: 'Fechar', help: 'Ajuda' }
    };
    function lang() {
        var l = 'en';
        try { l = (localStorage.getItem('luckyplz_lang') || 'en').toLowerCase(); } catch (_) {}
        if (l === 'gb') l = 'en';
        return l;
    }
    function ui() { return UI[lang()] || UI.en; }

    var css = document.createElement('style');
    css.textContent =
        '.lp-game-about{display:none!important}' +
        '.lp-help-fab{position:fixed;left:calc(10px + env(safe-area-inset-left,0px));top:calc(56px + env(safe-area-inset-top,0px));' +
        'z-index:9040;width:38px;height:38px;border-radius:50%;border:1.5px solid rgba(255,230,109,.55);' +
        'background:rgba(10,10,26,.6);color:#FFE66D;font:900 17px/1 "Noto Sans KR",sans-serif;cursor:pointer;padding:0;' +
        'display:flex;align-items:center;justify-content:center;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);' +
        'box-shadow:0 4px 12px rgba(0,0,0,.4);touch-action:manipulation}' +
        '.lp-help-fab:active{transform:scale(.92)}' +
        'body.qlive-in .lp-help-fab,body.lp-help-open .lp-help-fab{display:none}' +
        '.lp-help-ov{position:fixed;inset:0;z-index:9600;background:rgba(3,4,12,.72);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);' +
        'display:none;align-items:flex-end;justify-content:center}' +
        '.lp-help-ov.on{display:flex}' +
        '.lp-help-sheet{position:relative;width:100%;max-width:560px;max-height:86vh;max-height:86dvh;overflow:auto;-webkit-overflow-scrolling:touch;' +
        'background:linear-gradient(180deg,#171935,#0E0F24);border:1px solid rgba(255,255,255,.1);border-bottom:0;border-radius:20px 20px 0 0;' +
        'padding:20px 18px calc(22px + env(safe-area-inset-bottom,0px));color:#fff;font-family:"Noto Sans KR",sans-serif;' +
        'box-shadow:0 -20px 60px rgba(0,0,0,.5);animation:lpHelpUp .22s ease-out}' +
        '@keyframes lpHelpUp{from{transform:translateY(24px);opacity:.4}to{transform:none;opacity:1}}' +
        '@media(min-width:700px){.lp-help-ov{align-items:center}.lp-help-sheet{border-radius:20px;border-bottom:1px solid rgba(255,255,255,.1)}}' +
        '.lp-help-x{position:absolute;top:10px;right:10px;width:34px;height:34px;border-radius:50%;border:0;background:rgba(255,255,255,.08);' +
        'color:rgba(255,255,255,.8);font-size:16px;cursor:pointer}' +
        '.lp-help-t{font-size:1.15em;font-weight:900;margin:2px 40px 12px 2px;color:#FFE66D}' +
        '.lp-help-l{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:9px}' +
        '.lp-help-l li{position:relative;padding:10px 12px 10px 30px;border-radius:12px;background:rgba(255,255,255,.05);' +
        'font-size:.93em;line-height:1.5;color:rgba(255,255,255,.88)}' +
        '.lp-help-l li::before{content:"";position:absolute;left:13px;top:17px;width:7px;height:7px;border-radius:50%;background:#00D9FF}' +
        '.lp-help-more{margin:14px 0 0;width:100%;padding:11px;border-radius:12px;border:1px solid rgba(255,255,255,.14);' +
        'background:transparent;color:rgba(255,255,255,.7);font:700 .86em "Noto Sans KR",sans-serif;cursor:pointer}' +
        '.lp-help-body .lp-game-about{display:block!important;position:static!important;margin:14px 0 0!important;' +
        'padding:0!important;background:none!important;z-index:auto!important;min-height:0!important;width:auto!important;font-size:13.5px}' +
        '.lp-help-body .lp-game-about .lp-about-inner{max-width:none}';
    document.head.appendChild(css);

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'lp-help-fab';
    btn.textContent = '?';
    btn.setAttribute('aria-label', ui().help);
    document.body.appendChild(btn);

    /* 왼쪽 세로 버튼 줄의 맨 아래 빈자리 — ⛶·🔊 은 늦게 붙기도 해서 몇 번 다시 잰다 */
    function place() {
        var bottom = 0;
        var els = document.querySelectorAll('.lp-fs-btn,.lp-bgm-btn');
        for (var i = 0; i < els.length; i++) {
            var r = els[i].getBoundingClientRect();
            if (r.width && r.height && r.left < 90 && r.top < 260 && getComputedStyle(els[i]).display !== 'none') bottom = Math.max(bottom, r.bottom);
        }
        btn.style.top = bottom ? (bottom + 8) + 'px' : '';
    }
    place();
    [400, 1200, 2500, 5000].forEach(function (t) { setTimeout(place, t); });
    window.addEventListener('resize', place);

    var ov = null, listEl, titleEl, moreBtn, bodyEl, xBtn, loaded = false, moved = false;
    function build() {
        ov = document.createElement('div');
        ov.className = 'lp-help-ov';
        ov.setAttribute('role', 'dialog');
        ov.setAttribute('aria-modal', 'true');
        ov.innerHTML = '<div class="lp-help-sheet"><button type="button" class="lp-help-x">✕</button>' +
            '<div class="lp-help-t"></div><ul class="lp-help-l"></ul>' +
            '<button type="button" class="lp-help-more"></button><div class="lp-help-body"></div></div>';
        document.body.appendChild(ov);
        titleEl = ov.querySelector('.lp-help-t');
        listEl = ov.querySelector('.lp-help-l');
        moreBtn = ov.querySelector('.lp-help-more');
        bodyEl = ov.querySelector('.lp-help-body');
        xBtn = ov.querySelector('.lp-help-x');
        xBtn.addEventListener('click', close);
        ov.addEventListener('click', function (e) { if (e.target === ov) close(); });
        moreBtn.addEventListener('click', function () {
            if (!moved) { bodyEl.appendChild(about); moved = true; }
            var showing = bodyEl.style.display !== 'none' && bodyEl.childNodes.length && bodyEl.dataset.on === '1';
            bodyEl.dataset.on = showing ? '0' : '1';
            bodyEl.style.display = showing ? 'none' : 'block';
            moreBtn.textContent = showing ? ui().more : ui().less;
        });
        /* 게임 캔버스의 touchstart preventDefault 가 클릭을 삼키지 않게 — 시트 안 터치는 여기서 멈춘다 */
        ['touchstart', 'touchmove', 'pointerdown'].forEach(function (ev) {
            ov.addEventListener(ev, function (e) { e.stopPropagation(); }, { passive: true });
        });
    }
    function render() {
        var d = window.LP_HELP_TEXT && window.LP_HELP_TEXT[gameId];
        var l = lang(), e = d && (d[l] || d.en);
        var fallbackTitle = (document.querySelector('h1') || {}).textContent || document.title.split('|')[0];
        titleEl.textContent = (e && e.t) || String(fallbackTitle).trim();
        listEl.innerHTML = '';
        (e && e.l || []).forEach(function (s) { var li = document.createElement('li'); li.textContent = s; listEl.appendChild(li); });
        listEl.style.display = e ? '' : 'none';
        var u = ui();
        xBtn.setAttribute('aria-label', u.close);
        moreBtn.textContent = bodyEl.dataset.on === '1' ? u.less : u.more;
        if (!e) { /* 간단 도움말이 없으면 바로 긴 글을 보여 준다 */
            if (!moved) { bodyEl.appendChild(about); moved = true; }
            bodyEl.dataset.on = '1'; bodyEl.style.display = 'block'; moreBtn.style.display = 'none';
        } else moreBtn.style.display = '';
    }
    function loadText(cb) {
        if (loaded || window.LP_HELP_TEXT) { loaded = true; cb(); return; }
        var s = document.createElement('script');
        s.src = '/js/lpHelpText.js' + (V ? '?v=' + V : '');
        s.onload = function () { loaded = true; cb(); };
        s.onerror = function () { loaded = true; cb(); };
        document.head.appendChild(s);
    }
    function open() {
        if (!ov) { build(); bodyEl.style.display = 'none'; bodyEl.dataset.on = '0'; }
        loadText(function () {
            render();
            ov.classList.add('on');
            document.body.classList.add('lp-help-open');
        });
    }
    function close() {
        if (!ov) return;
        ov.classList.remove('on');
        document.body.classList.remove('lp-help-open');
    }
    btn.addEventListener('click', function (e) { e.stopPropagation(); open(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    document.addEventListener('lp:langchanged', function () { btn.setAttribute('aria-label', ui().help); if (ov && ov.classList.contains('on')) render(); });

    window.LpHelp = { open: open, close: close };
})();
