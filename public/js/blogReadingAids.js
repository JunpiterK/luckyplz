/* Lucky Please — Blog Reading Aids
   Sticky TOC (left, desktop only) + reading progress bar (top, all sizes).

   Loads dynamically via siteFooter.js on /blog/<slug>/ pages only.
   On the blog index (/blog/), games, and other pages this script is never
   injected — keeping non-blog payload light.

   Auto-discovery:
   - Builds TOC from <h2> tags inside the main content container
     (.page, or fallback to body)
   - Bails silently if fewer than 3 <h2> are found (short posts don't
     benefit from a TOC and would feel cluttered)

   Theme awareness:
   - body[data-theme="paper"] → cream/gold variant matching AI 진화사
     and any other paper-aesthetic posts
   - Otherwise → dark variant matching the site's default game/industry
     post aesthetic

   Behavior:
   - Top-of-page progress bar reflects scroll % across the article
   - TOC item highlights as you scroll past each section heading
   - Click a TOC item → smooth-scroll to that section (offset 80px so
     the heading isn't jammed under the sticky site-nav)

   Performance:
   - Single rAF per scroll event (no thrashing)
   - One IntersectionObserver-free implementation kept simple — getBoundingClientRect
     across N=5-10 headings per scroll is cheap

   Disabling on a specific post:
   - Add data-no-aids="1" to <body>, or
   - Use fewer than 3 <h2> tags (auto-bails)
*/
(function(){
    'use strict';

    /* Bail if user opted out on this page */
    if (document.body && document.body.dataset.noAids === '1') return;

    /* Find heading container. Prefer .page (the convention in our blog
       templates), fall back to <main> or <article>, finally body. */
    var container = document.querySelector('.page')
                 || document.querySelector('main')
                 || document.querySelector('article')
                 || document.body;

    /* Collect <h2> headings from the container only — avoids the site-nav
       brand or footer accidentally appearing in the TOC. */
    var headings = Array.prototype.slice.call(container.querySelectorAll('h2'));
    if (headings.length < 3) return;

    /* Detect paper theme. Body attribute is authoritative; we don't sniff
       computed colors because the AdSense + GA scripts can change body
       background mid-load and we don't want a flash of wrong theme. */
    var theme = (document.body.dataset.theme || '').toLowerCase();
    var isPaper = theme === 'paper';

    /* Lang-aware title for the TOC */
    var lang = (document.documentElement.lang || 'ko').toLowerCase();
    var tocTitle = lang.indexOf('en') === 0 ? 'CONTENTS' : '목차';

    /* Build TOC items.
       Heading text often contains decorative markup like
       <span class="num">01</span> — strip those so the TOC stays clean. */
    var items = headings.map(function(h, i){
        if (!h.id) h.id = 'lp-h2-' + i;
        var clone = h.cloneNode(true);
        var dec = clone.querySelector('.num, .accent-line');
        if (dec) dec.remove();
        return { id: h.id, text: clone.textContent.trim().replace(/\s+/g, ' '), node: h };
    });

    /* Inject styles once. Scoping all rules under .lp-toc / .lp-progress
       so they can't bleed into the host page. */
    var styleId = 'lp-reading-aids-style';
    if (!document.getElementById(styleId)) {
        var s = document.createElement('style');
        s.id = styleId;
        s.textContent =
            /* Progress bar — visible at all viewport sizes */
            '.lp-progress{position:fixed;top:0;left:0;right:0;height:3px;background:rgba(0,0,0,.05);z-index:200;pointer-events:none}'
          + '.lp-progress-bar{height:100%;width:0;background:linear-gradient(90deg,rgba(255,230,109,.85),rgba(255,154,60,.85));transition:width .12s ease-out;will-change:width}'
          + '.lp-progress--paper{background:rgba(200,146,78,.08)}'
          + '.lp-progress--paper .lp-progress-bar{background:linear-gradient(90deg,#C8924E,#D4A574)}'
            /* TOC — desktop only. Hidden below 1200px so on tablet/laptop we
               don\'t crowd the gutter or overlap the centered text column. */
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
            /* Show TOC only on roomy desktops. We need ≥1200px to leave
               240px gutter + 760px main column + 200px right breathing room. */
          + '@media (min-width:1200px){.lp-toc{display:block}}'
            /* Hide TOC if user prefers reduced motion AND the page is short:
               not aggressive — we still show it, just no slide animation. */
          + '@media (prefers-reduced-motion:reduce){.lp-progress-bar{transition:none}}';
        document.head.appendChild(s);
    }

    /* Inject progress bar */
    var progress = document.createElement('div');
    progress.className = 'lp-progress' + (isPaper ? ' lp-progress--paper' : '');
    progress.innerHTML = '<div class="lp-progress-bar"></div>';
    document.body.appendChild(progress);
    var progressBar = progress.firstElementChild;

    /* Inject TOC */
    var toc = document.createElement('aside');
    toc.className = 'lp-toc' + (isPaper ? ' lp-toc--paper' : '');
    toc.setAttribute('aria-label', tocTitle);
    toc.innerHTML =
        '<div class="lp-toc-title">' + tocTitle + '</div>'
      + '<ul>' + items.map(function(it){
            return '<li data-id="' + it.id + '"><a href="#' + it.id + '">' + escapeHtml(it.text) + '</a></li>';
        }).join('') + '</ul>';
    document.body.appendChild(toc);

    var liItems = toc.querySelectorAll('li');

    /* Smooth scroll on TOC click. We compute target offset against the
       sticky site-nav (~56px) plus a small breathing buffer, so the
       heading lands ~80px from the top instead of touching the nav. */
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

    /* Single rAF gate for all scroll-driven updates. */
    var ticking = false;
    function update(){
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function(){
            /* Progress: how far we\'ve scrolled across the document */
            var scrolled = window.pageYOffset;
            var maxScroll = (document.documentElement.scrollHeight - window.innerHeight) || 1;
            var pct = Math.max(0, Math.min(100, (scrolled / maxScroll) * 100));
            progressBar.style.width = pct + '%';

            /* Active section: the last heading whose top has crossed
               our 120px threshold (below sticky nav). If none has crossed,
               we don\'t mark anything active (cleaner than always showing
               #1 active before user scrolls there). */
            var activeIdx = -1;
            for (var i = 0; i < headings.length; i++) {
                if (headings[i].getBoundingClientRect().top < 120) activeIdx = i;
                else break;
            }
            for (var j = 0; j < liItems.length; j++) {
                if (j === activeIdx) liItems[j].classList.add('active');
                else liItems[j].classList.remove('active');
            }

            ticking = false;
        });
    }

    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update, { passive: true });
    update();

    /* Lightweight HTML escape for TOC text — heading text from the page
       is generally safe but we don\'t want stray < or & to break out. */
    function escapeHtml(str){
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
})();
