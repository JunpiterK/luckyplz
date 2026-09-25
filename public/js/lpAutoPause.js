/* lpAutoPause.js — 조작형 게임 공통 '자리 비움 자동 일시정지' (2026-09-25)
 *
 * 운영자: "혼자 하는 조작형 레트로 게임은 홈 버튼을 누르거나 다른 곳으로 가면 자동으로 Pause,
 *          돌아오면 Resume / Quit 을 골라 재개하거나 끝낼 수 있게."
 *
 * 사용 — 게임 초기화 때 한 번(모듈보다 먼저 실행돼도 되도록 큐에 넣는다):
 *   (window.LpAutoPauseQ = window.LpAutoPauseQ || []).push({
 *       isActive: function(){ return playing && !gameOver && !paused && !isMultiplayer },  // 지금 멈출 대상인가
 *       pause:    function(){ ... },   // 게임 자체 일시정지(루프 정지)
 *       resume:   function(){ ... },   // 게임 자체 재개
 *       quit:     function(){ ... }    // 생략하면 LpNav 게임 홈(없으면 /games/<id>/ 새로고침)
 *   });
 * - 화면이 숨겨지는 순간(visibilitychange·pagehide) isActive() 면 pause() 를 부르고,
 *   다시 보이면 '계속하기 / 그만하기' 창을 띄운다. 게임이 이미 자기 정지 화면을 띄웠어도 그 위에 뜬다.
 * - 멀티·방장 모드는 게임이 isActive 에서 false 를 돌려 제외한다(남의 판을 멈추면 안 된다).
 * - 캔버스 게임의 touchstart preventDefault 함정을 피하려고 창 안 터치는 전파를 멈추고 pointerup 에서도 동작한다.
 */
(function () {
    'use strict';
    /* pointerup 으로 처리한 뒤 곧이어 오는 click 이, 방금 같은 자리에 새로 뜬 버튼(예: 시작 화면 Start)을
       눌러 버리는 문제(2026-09-25 실측) — 0.45초 동안 그 click 을 삼킨다. 공용(두 모듈이 같은 값을 쓴다) */
    if (!window.__lpClickGuard) {
        window.__lpClickGuard = 1;
        window.addEventListener('click', function (e) {
            if (Date.now() < (window.__lpSwallowClickUntil || 0)) { e.preventDefault(); e.stopImmediatePropagation(); }
        }, true);
    }
    if (window.LpAutoPause) return;
    var L = {
        ko: ['일시정지됨', '자리를 비운 사이 게임을 멈춰 두었어요', '계속하기', '그만하기'],
        en: ['Paused', 'We paused the game while you were away', 'Resume', 'Quit'],
        ja: ['一時停止中', '離れている間、ゲームを止めておきました', '再開', 'やめる'],
        zh: ['已暂停', '你离开时游戏已自动暂停', '继续', '退出'],
        es: ['En pausa', 'Pausamos el juego mientras no estabas', 'Continuar', 'Salir'],
        pt: ['Pausado', 'Pausamos o jogo enquanto você estava fora', 'Continuar', 'Sair'],
        de: ['Pausiert', 'Das Spiel wurde pausiert, während du weg warst', 'Weiter', 'Beenden'],
        fr: ['En pause', 'Le jeu a été mis en pause pendant ton absence', 'Reprendre', 'Quitter'],
        ru: ['Пауза', 'Игра на паузе, пока тебя не было', 'Продолжить', 'Выйти'],
        ar: ['متوقف مؤقتًا', 'أوقفنا اللعبة أثناء غيابك', 'متابعة', 'خروج'],
        hi: ['रुका हुआ', 'आपके जाने पर खेल रोक दिया गया', 'जारी रखें', 'छोड़ें'],
        th: ['หยุดชั่วคราว', 'เกมหยุดไว้ระหว่างที่คุณไม่อยู่', 'เล่นต่อ', 'ออก'],
        id: ['Dijeda', 'Game dijeda saat kamu pergi', 'Lanjut', 'Keluar'],
        vi: ['Tạm dừng', 'Trò chơi đã tạm dừng khi bạn rời đi', 'Tiếp tục', 'Thoát'],
        tr: ['Duraklatıldı', 'Sen yokken oyun duraklatıldı', 'Devam', 'Çık']
    };
    function t() {
        var l = 'en';
        try { l = (localStorage.getItem('luckyplz_lang') || 'en').toLowerCase(); } catch (_) {}
        if (l === 'gb') l = 'en';
        return L[l] || L.en;
    }
    var cfgs = [], pending = null, ov = null, lastAct = 0;

    var st = document.createElement('style');
    st.textContent =
        '.lp-ap-ov{position:fixed;inset:0;z-index:9500;display:none;align-items:center;justify-content:center;padding:20px;' +
        'background:rgba(4,5,14,.72);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);touch-action:none}' +
        '.lp-ap-ov.on{display:flex}' +
        '.lp-ap-card{width:100%;max-width:320px;text-align:center;padding:24px 20px 20px;border-radius:20px;color:#fff;' +
        'background:linear-gradient(180deg,#191b38,#0e0f24);border:1px solid rgba(255,255,255,.12);' +
        'box-shadow:0 20px 60px rgba(0,0,0,.55);font-family:"Noto Sans KR",sans-serif;animation:lpApIn .2s ease-out}' +
        '@keyframes lpApIn{from{transform:scale(.94);opacity:.4}to{transform:none;opacity:1}}' +
        '.lp-ap-ic{font-size:34px;line-height:1;margin-bottom:8px}' +
        '.lp-ap-t{font-size:1.25em;font-weight:900;color:#FFE66D;margin-bottom:6px}' +
        '.lp-ap-s{font-size:.86em;color:rgba(255,255,255,.66);line-height:1.5;margin-bottom:18px}' +
        '.lp-ap-b{display:flex;flex-direction:column;gap:9px}' +
        '.lp-ap-b button{padding:13px;border-radius:14px;font:800 1em "Noto Sans KR",sans-serif;cursor:pointer;' +
        'touch-action:manipulation;-webkit-tap-highlight-color:transparent}' +
        '.lp-ap-go{border:0;color:#10131f;background:linear-gradient(135deg,#FFE66D,#FF9A3C);box-shadow:0 6px 18px rgba(255,154,60,.3)}' +
        '.lp-ap-q{border:1px solid rgba(255,255,255,.18);color:rgba(255,255,255,.85);background:rgba(255,255,255,.06)}' +
        '.lp-ap-b button:active{transform:translateY(1px)}';
    (document.head || document.documentElement).appendChild(st);

    function build() {
        if (ov) return;
        ov = document.createElement('div');
        ov.className = 'lp-ap-ov';
        ov.setAttribute('role', 'dialog');
        ov.setAttribute('aria-modal', 'true');
        ov.innerHTML = '<div class="lp-ap-card"><div class="lp-ap-ic">⏸</div><div class="lp-ap-t"></div><div class="lp-ap-s"></div>' +
            '<div class="lp-ap-b"><button type="button" class="lp-ap-go" data-ap="go"></button>' +
            '<button type="button" class="lp-ap-q" data-ap="quit"></button></div></div>';
        document.body.appendChild(ov);
        ['touchstart', 'touchend', 'touchmove', 'mousedown', 'pointerdown'].forEach(function (ev) {
            ov.addEventListener(ev, function (e) { e.stopPropagation(); }, { passive: true });
        });
        function act(e) {
            var b = e.target && e.target.closest && e.target.closest('[data-ap]');
            if (!b) return;
            var now = Date.now();
            if (now - lastAct < 400) return;
            lastAct = now;
            if (e.type === 'pointerup') window.__lpSwallowClickUntil = now + 450;
            e.preventDefault(); e.stopPropagation();
            var c = pending; hideDialog(); pending = null;
            if (!c) return;
            if (b.getAttribute('data-ap') === 'go') { try { c.resume(); } catch (_) {} }
            else quit(c);
        }
        ov.addEventListener('click', act);
        ov.addEventListener('pointerup', act);
    }
    function quit(c) {
        if (typeof c.quit === 'function') { try { c.quit(); return; } catch (_) {} }
        if (window.LpNav && window.LpNav.goGameHome) { window.LpNav.goGameHome(); return; }
        var m = location.pathname.match(/^\/games\/[a-z0-9-]+\/?/);
        location.href = m ? m[0].replace(/\/?$/, '/') : '/';
    }
    function showDialog() {
        build();
        var s = t();
        ov.querySelector('.lp-ap-t').textContent = s[0];
        ov.querySelector('.lp-ap-s').textContent = s[1];
        ov.querySelector('[data-ap="go"]').textContent = '▶ ' + s[2];
        ov.querySelector('[data-ap="quit"]').textContent = s[3];
        ov.classList.add('on');
        try { ov.querySelector('[data-ap="go"]').focus({ preventScroll: true }); } catch (_) {}
    }
    function hideDialog() { if (ov) ov.classList.remove('on'); }

    function onHide() {
        if (pending) return;
        for (var i = 0; i < cfgs.length; i++) {
            var c = cfgs[i], active = false;
            try { active = !!c.isActive(); } catch (_) {}
            if (active) {
                try { c.pause(); } catch (_) {}
                pending = c;
                return;
            }
        }
    }
    function onShow() {
        if (!pending) return;
        /* 복귀 직후 한 프레임 뒤에 — 게임이 자기 정지 화면을 그린 다음 그 위에 뜨게 */
        setTimeout(function () { if (pending && document.visibilityState !== 'hidden') showDialog(); }, 60);
    }
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'hidden') onHide(); else onShow();
    });
    window.addEventListener('pagehide', onHide);
    window.addEventListener('pageshow', function () { if (document.visibilityState !== 'hidden') onShow(); });
    /* Esc/Enter — PC 에서 창이 떠 있을 때만 */
    window.addEventListener('keydown', function (e) {
        if (!ov || !ov.classList.contains('on')) return;
        /* 창이 떠 있는 동안 키는 게임에 넘기지 않는다 — Enter/Space 가 게임까지 가면 다시 멈추거나 조작이 된다 */
        e.stopPropagation(); e.stopImmediatePropagation();
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); ov.querySelector('[data-ap="go"]').click(); }
    }, true);

    function add(c) {
        if (!c || typeof c.isActive !== 'function' || typeof c.pause !== 'function' || typeof c.resume !== 'function') return;
        cfgs.push(c);
    }
    var q = window.LpAutoPauseQ;
    if (q && q.length) q.forEach(add);
    window.LpAutoPauseQ = { push: add };
    /* anyActive — 등록된 게임 중 지금 플레이 중인 것이 있는가. lpChrome(공용 버튼 독)이 '플레이 중이면 접기'에 쓴다 */
    function anyActive() {
        if (pending) return false;
        for (var i = 0; i < cfgs.length; i++) { try { if (cfgs[i].isActive()) return true; } catch (_) {} }
        return false;
    }
    window.LpAutoPause = { mount: add, anyActive: anyActive, isShowing: function () { return !!(ov && ov.classList.contains('on')); } };
})();
