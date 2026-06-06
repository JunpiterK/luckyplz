/* Lucky Please — Blog Reading Aids
   Top reading-progress bar (ALL posts) + sticky TOC (desktop, posts with ≥3 <h2>).

   Loads on /blog/<slug>/ pages (via the page's own <script> tag and/or
   siteFooter.js). Never on the blog index, games, or other pages.

   Progress bar:
   - ALWAYS shown on any article — including the auto-published 증시 posts,
     which use <h3>/<h4> section headings (no <h2>) and previously got no bar
     because the whole script bailed on the "<3 <h2>" check. The bar is now
     decoupled from the TOC: it fills left→right as you scroll so you always
     know where you are in the article.

   TOC (table of contents):
   - Desktop only (≥1200px). Built from <h2> headings inside the main content
     container. Requires ≥3 <h2> — short posts / data-style posts skip it.
   - Active heading highlights as you scroll; click → smooth-scroll.

   Theme:
   - body[data-theme="paper"] → cream/gold variant (AI 진화사 등 paper posts)
   - otherwise → dark variant (default game/industry/증시 post aesthetic)

   Disable on a page: <body data-no-aids="1">.

   Perf: single rAF per scroll; getBoundingClientRect over N headings is cheap.
*/
(function(){
    'use strict';

    if (document.body && document.body.dataset.noAids === '1') return;

    var theme = (document.body.dataset.theme || '').toLowerCase();
    var isPaper = theme === 'paper';

    /* ---- inject scoped styles once ---- */
    var styleId = 'lp-reading-aids-style';
    if (!document.getElementById(styleId)) {
        var s = document.createElement('style');
        s.id = styleId;
        s.textContent =
            /* Progress bar — visible at all viewport sizes, every article */
            '.lp-progress{position:fixed;top:0;left:0;right:0;height:3px;background:rgba(255,255,255,.06);z-index:200;pointer-events:none}'
          + '.lp-progress-bar{height:100%;width:0;background:linear-gradient(90deg,rgba(92,200,255,.95),rgba(95,224,168,.95));transition:width .12s ease-out;will-change:width}'
          + '.lp-progress--paper{background:rgba(200,146,78,.12)}'
          + '.lp-progress--paper .lp-progress-bar{background:linear-gradient(90deg,#C8924E,#D4A574)}'
            /* TOC — desktop only */
          + '.lp-toc{display:none;position:fixed;left:24px;top:96px;width:230px;max-height:calc(100vh - 130px);overflow-y:auto;padding:18px 14px;background:rgba(22,22,42,.88);border:1px solid rgba(255,255,255,.07);border-radius:14px;box-shadow:0 6px 28px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.05);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);z-index:90;font-family:\'Pretendard\',-apple-system,BlinkMacSystemFont,system-ui,sans-serif;color:#fff;-webkit-font-smoothing:antialiased}'
          + '.lp-toc--paper{background:rgba(255,255,255,.92);border:1px solid rgba(232,226,213,.7);box-shadow:0 4px 22px rgba(44,62,80,.07),inset 0 1px 0 rgba(255,255,255,.5);color:#2C3E50}'
          + '.lp-toc-title{font-family:\'JetBrains Mono\',\'Courier New\',monospace;font-size:10px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:rgba(255,255,255,.45);margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,.06)}'
          + '.lp-toc--paper .lp-toc-title{color:#8A9AA8;border-bottom-color:#E8E2D5}'
          + '.lp-toc ul{list-style:none;padding:0;margin:0}'
          + '.lp-toc li{margin:0;padding:0}'
          + '.lp-toc a{display:block;padding:7px 10px;font-size:12.5px;line-height:1.45;color:rgba(255,255,255,.55);text-decoration:none;border-left:2px solid transparent;border-radius:0 6px 6px 0;transition:color .2s,background .2s,border-color .2s}'
          + '.lp-toc a:hover{color:rgba(255,255,255,.95);background:rgba(255,255,255,.04);border-left-color:rgba(255,230,109,.45)}'
          + '.lp-toc--paper a{color:#5A6C7D}'
          + '.lp-toc--paper a:hover{color:#2C3E50;background:#FBF5EA;border-left-color:#C8924E}'
          + '.lp-toc li.active a{color:#FFE66D;background:rgba(255,230,109,.07);border-left-color:#FFE66D;font-weight:600}'
          + '.lp-toc--paper li.active a{color:#854D0E;background:#FBF1E1;border-left-color:#C8924E;font-weight:600}'
          + '@media (min-width:1200px){.lp-toc{display:block}}'
          + '@media (prefers-reduced-motion:reduce){.lp-progress-bar{transition:none}}';
        document.head.appendChild(s);
    }

    /* ---- progress bar: ALWAYS ---- */
    var progress = document.createElement('div');
    progress.className = 'lp-progress' + (isPaper ? ' lp-progress--paper' : '');
    progress.innerHTML = '<div class="lp-progress-bar"></div>';
    document.body.appendChild(progress);
    var progressBar = progress.firstElementChild;

    /* ---- TOC: only when the article has ≥3 <h2> headings ---- */
    var container = document.querySelector('.page')
                 || document.querySelector('main')
                 || document.querySelector('article')
                 || document.body;
    var headings = Array.prototype.slice.call(container.querySelectorAll('h2'));
    var hasTOC = headings.length >= 3;
    var liItems = null;

    if (hasTOC) {
        var lang = (document.documentElement.lang || 'ko').toLowerCase();
        var tocTitle = lang.indexOf('en') === 0 ? 'CONTENTS' : '목차';
        var items = headings.map(function(h, i){
            if (!h.id) h.id = 'lp-h2-' + i;
            var clone = h.cloneNode(true);
            var dec = clone.querySelector('.num, .accent-line');
            if (dec) dec.remove();
            return { id: h.id, text: clone.textContent.trim().replace(/\s+/g, ' '), node: h };
        });
        var toc = document.createElement('aside');
        toc.className = 'lp-toc' + (isPaper ? ' lp-toc--paper' : '');
        toc.setAttribute('aria-label', tocTitle);
        toc.innerHTML =
            '<div class="lp-toc-title">' + tocTitle + '</div>'
          + '<ul>' + items.map(function(it){
                return '<li data-id="' + it.id + '"><a href="#' + it.id + '">' + escapeHtml(it.text) + '</a></li>';
            }).join('') + '</ul>';
        document.body.appendChild(toc);
        liItems = toc.querySelectorAll('li');

        toc.addEventListener('click', function(e){
            var a = e.target.closest('a');
            if (!a) return;
            e.preventDefault();
            var id = a.getAttribute('href').slice(1);
            var t = document.getElementById(id);
            if (!t) return;
            var top = t.getBoundingClientRect().top + window.pageYOffset - 80;
            window.scrollTo({ top: top, behavior: 'smooth' });
        });
    }

    /* ---- single rAF gate for all scroll-driven updates ---- */
    var ticking = false;
    function update(){
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function(){
            var scrolled = window.pageYOffset;
            var maxScroll = (document.documentElement.scrollHeight - window.innerHeight) || 1;
            var pct = Math.max(0, Math.min(100, (scrolled / maxScroll) * 100));
            progressBar.style.width = pct + '%';

            if (hasTOC && liItems) {
                var activeIdx = -1;
                for (var i = 0; i < headings.length; i++) {
                    if (headings[i].getBoundingClientRect().top < 120) activeIdx = i;
                    else break;
                }
                for (var j = 0; j < liItems.length; j++) {
                    if (j === activeIdx) liItems[j].classList.add('active');
                    else liItems[j].classList.remove('active');
                }
            }
            ticking = false;
        });
    }

    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update, { passive: true });
    update();

    function escapeHtml(str){
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
})();
