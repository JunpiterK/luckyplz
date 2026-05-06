/* Blog "관련 글" / "Related posts" injector.

   Goal: bump retention from 1 page/session toward 2.5+ by giving the
   reader a clean, low-friction next-step at the end of every blog post.
   Cross-linking the same-category pool (and explicitly the next/prev
   EP in serial content) is the single highest-leverage move on a
   53-post blog.

   Loading: this file is plain script (no exports) and depends on
   window.BLOG_POSTS — make sure /blog/posts.js is loaded before it on
   every page that includes <script src="/js/blogRelated.js">.

   Dependencies discovered at runtime:
     - window.BLOG_POSTS  (required; bails silently otherwise)
     - window.BLOG_CATEGORIES  (optional — improves tag labels)

   Output:
     <section class="lp-related">
       <h3 class="lp-rel-heading">관련 글</h3>
       <div class="lp-rel-grid">
         <a class="lp-rel-card cat-…">…</a> × up to 4
       </div>
     </section>

   Mount point: prefers an explicit <div id="lpRelatedMount"> hook;
   otherwise injects right above the page's first <footer>. Skips
   silently if neither is found. */
(function () {
    if (typeof window === 'undefined' || !document) return;
    if (document.querySelector('.lp-related')) return; // idempotent

    var posts = window.BLOG_POSTS;
    var cats = window.BLOG_CATEGORIES || [];
    if (!posts || !posts.length) return;

    /* === Resolve current post from URL =================================
       URL shape: /blog/<slug>/  →  slug is the path segment after /blog/.
       Falls back to nothing-matched (no rel-block rendered) if we can't
       find this slug in the manifest, e.g. a draft preview. */
    var path = (location.pathname || '').replace(/\/+$/, '');
    var m = path.match(/^\/blog\/([^/]+)/);
    if (!m) return;
    var slug = m[1];
    var current = posts.find(function (p) { return p.slug === slug; });
    if (!current) return;

    var lang = current.lang || 'ko';
    var category = current.category || 'lifestyle';

    /* === Series detection (e.g. space-evo-04-tragedies) =================
       Most "evo" series ship 8–10 EPs with a numeric prefix. We use the
       prefix to find the immediate next/previous episode and pin them
       at the head of the related list — this is what readers actually
       want when they finish EP04 ("ok, what's EP05?"). */
    var seriesRe = /^([a-z-]+?)-(\d{2})-/;
    var seriesMatch = current.slug.match(seriesRe);
    var seriesKey = seriesMatch ? seriesMatch[1] : null;
    var seriesIdx = seriesMatch ? parseInt(seriesMatch[2], 10) : null;

    function inSeries(p) {
        if (!seriesKey || !p || !p.slug) return null;
        var mm = p.slug.match(seriesRe);
        if (!mm || mm[1] !== seriesKey) return null;
        return parseInt(mm[2], 10);
    }

    /* === Build candidate pool ============================================
       Filter to same lang, exclude self, sort by date desc. The series
       next/prev (if any) are spliced to the front so they always appear
       as the first 1–2 cards. Fill the rest from same-category, then
       any-category (so even short categories never render an empty
       block). Cap at 4 cards to keep the section compact. */
    var sameLang = posts.filter(function (p) {
        return p.slug !== current.slug && (p.lang || 'ko') === lang;
    });
    sameLang.sort(function (a, b) { return (b.date || '').localeCompare(a.date || ''); });

    var picks = [];
    var seenSlugs = {};
    function add(p) {
        if (!p || seenSlugs[p.slug]) return;
        seenSlugs[p.slug] = 1;
        picks.push(p);
    }

    /* Series: next EP first (forward momentum), then previous EP. */
    if (seriesKey && seriesIdx) {
        var nextEp = sameLang.find(function (p) { return inSeries(p) === seriesIdx + 1; });
        var prevEp = sameLang.find(function (p) { return inSeries(p) === seriesIdx - 1; });
        if (nextEp) add(nextEp);
        if (prevEp) add(prevEp);
    }

    /* Same category, latest first. */
    sameLang.forEach(function (p) {
        if (picks.length >= 4) return;
        if ((p.category || 'lifestyle') === category) add(p);
    });

    /* Any category fallback so the block always has 4 cards if pool size
       allows. Skips silently if the language has fewer than 4 total
       posts. */
    sameLang.forEach(function (p) {
        if (picks.length >= 4) return;
        add(p);
    });

    if (!picks.length) return;

    /* === Locate mount point =============================================
       1) Explicit <div id="lpRelatedMount"> beats everything (lets a
          page author position the block precisely).
       2) Otherwise insert *before* the first <footer>. Most posts have
          their disclaimer/credits inside <footer>, so this places the
          related block at the natural "you finished reading" point. */
    var mount = document.getElementById('lpRelatedMount');
    var anchor = null;
    if (!mount) {
        anchor = document.querySelector('footer');
        if (!anchor) return;
    }

    var section = document.createElement('section');
    section.className = 'lp-related';

    var heading = document.createElement('h3');
    heading.className = 'lp-rel-heading';
    heading.textContent = lang === 'ko' ? '관련 글' : 'Related posts';
    section.appendChild(heading);

    var grid = document.createElement('div');
    grid.className = 'lp-rel-grid';
    section.appendChild(grid);

    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
        });
    }

    function formatDate(dateStr) {
        if (!dateStr) return '';
        try {
            var d = new Date(dateStr);
            return d.toLocaleDateString(lang === 'ko' ? 'ko-KR' : 'en-US',
                { year: 'numeric', month: 'short', day: 'numeric' });
        } catch (_) { return dateStr; }
    }

    /* Series-EP marker for the first 1–2 cards when applicable. Helps
       the reader recognise them as continuation, not just "another post
       I saw". */
    var nextEpSlug = null, prevEpSlug = null;
    if (seriesKey && seriesIdx) {
        var ne = sameLang.find(function (p) { return inSeries(p) === seriesIdx + 1; });
        var pe = sameLang.find(function (p) { return inSeries(p) === seriesIdx - 1; });
        if (ne) nextEpSlug = ne.slug;
        if (pe) prevEpSlug = pe.slug;
    }

    grid.innerHTML = picks.map(function (p) {
        var catMeta = cats.find(function (c) { return c.slug === p.category; });
        var catLabel = catMeta
            ? (lang === 'ko' ? catMeta.label_ko : catMeta.label_en)
            : (p.category || '');

        var seriesBadge = '';
        if (p.slug === nextEpSlug) {
            seriesBadge = '<span class="lp-rel-series">' +
                (lang === 'ko' ? '다음 편 →' : 'NEXT EP →') + '</span>';
        } else if (p.slug === prevEpSlug) {
            seriesBadge = '<span class="lp-rel-series prev">' +
                (lang === 'ko' ? '← 이전 편' : '← PREV EP') + '</span>';
        }

        var readText = p.readMinutes
            ? (lang === 'ko' ? p.readMinutes + '분' : p.readMinutes + ' min')
            : '';
        var meta = [formatDate(p.date), readText].filter(Boolean).join(' · ');

        return '<a class="lp-rel-card cat-' + escapeHtml(p.category || '') + '" ' +
            'href="/blog/' + encodeURIComponent(p.slug) + '/">' +
            seriesBadge +
            '<span class="lp-rel-tag">' + escapeHtml((catLabel || '').toUpperCase()) + '</span>' +
            '<h4 class="lp-rel-title">' + escapeHtml(p.title || '') + '</h4>' +
            (meta ? '<p class="lp-rel-meta">' + escapeHtml(meta) + '</p>' : '') +
            '</a>';
    }).join('');

    /* === Inject styles once ===========================================
       Keeps the loader self-contained — no per-post CSS edits needed.
       Visual language mirrors the blog index post-card so the reader
       recognises these as "more posts" without a learning curve. */
    if (!document.getElementById('lpRelatedStyle')) {
        var style = document.createElement('style');
        style.id = 'lpRelatedStyle';
        style.textContent = ''
            + '.lp-related{margin:34px 16px 0;padding:24px 0 0;border-top:1px solid rgba(255,255,255,.08)}'
            + '.lp-related .lp-rel-heading{font-family:"Pretendard Variable","Pretendard","Inter",-apple-system,sans-serif;'
            + 'font-size:15px;font-weight:800;color:#e2e8f0;letter-spacing:-.015em;margin:0 0 16px}'
            + '.lp-related .lp-rel-grid{display:grid;grid-template-columns:1fr;gap:10px}'
            + '@media(min-width:680px){.lp-related .lp-rel-grid{grid-template-columns:1fr 1fr}}'
            + '.lp-rel-card{position:relative;display:block;padding:14px 14px 13px 18px;background:linear-gradient(145deg,rgba(22,22,42,.65),rgba(14,14,28,.85));'
            + 'border:1px solid rgba(255,255,255,.06);border-radius:11px;text-decoration:none;color:inherit;'
            + 'transition:transform .2s,border-color .25s,background .25s,box-shadow .25s;overflow:hidden}'
            + '.lp-rel-card:hover{transform:translateY(-1px);border-color:rgba(93,193,255,.35);'
            + 'background:linear-gradient(145deg,rgba(28,28,48,.78),rgba(18,18,34,.92));'
            + 'box-shadow:0 8px 22px -8px rgba(0,0,0,.5)}'
            + '.lp-rel-card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:rgba(255,255,255,.08);transition:background .25s}'
            + '.lp-rel-card.cat-space-tech::before{background:linear-gradient(180deg,#5dc1ff,rgba(93,193,255,0))}'
            + '.lp-rel-card.cat-ai-tech::before{background:linear-gradient(180deg,#FF66CC,rgba(255,102,204,0))}'
            + '.lp-rel-card.cat-industry::before{background:linear-gradient(180deg,#3dd68c,rgba(61,214,140,0))}'
            + '.lp-rel-card.cat-lifestyle::before{background:linear-gradient(180deg,#FFE66D,rgba(255,230,109,0))}'
            + '.lp-rel-card.cat-probability::before{background:linear-gradient(180deg,#00D9FF,rgba(0,217,255,0))}'
            + '.lp-rel-card.cat-tech-space::before{background:linear-gradient(180deg,#a78bfa,rgba(167,139,250,0))}'
            /* Series badge — small absolute pill at top-right so it never
               competes with the title for left-aligned reading. */
            + '.lp-rel-series{position:absolute;top:10px;right:10px;font-family:"JetBrains Mono",ui-monospace,monospace;'
            + 'font-size:8.5px;letter-spacing:.16em;text-transform:uppercase;font-weight:800;color:#5dc1ff;'
            + 'background:rgba(93,193,255,.12);border:1px solid rgba(93,193,255,.32);padding:3px 6px;border-radius:3px;line-height:1}'
            + '.lp-rel-series.prev{color:rgba(180,200,230,.75);background:rgba(140,162,196,.1);border-color:rgba(140,162,196,.28)}'
            + '.lp-rel-tag{display:inline-block;font-family:"JetBrains Mono",ui-monospace,monospace;font-size:9px;font-weight:700;'
            + 'letter-spacing:.18em;text-transform:uppercase;color:rgba(180,200,230,.7);margin-bottom:6px;line-height:1}'
            + '.lp-rel-title{font-family:"Pretendard Variable","Pretendard","Inter",-apple-system,sans-serif;'
            + 'font-size:13.5px;font-weight:700;color:#fff;letter-spacing:-.015em;line-height:1.4;margin:0 0 6px;'
            + 'font-feature-settings:"palt";display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}'
            + '.lp-rel-meta{font-family:"JetBrains Mono",ui-monospace,monospace;font-size:9.5px;font-weight:600;color:rgba(180,200,230,.45);'
            + 'letter-spacing:.05em;margin:0;text-transform:uppercase;line-height:1}'
            + '@media(max-width:480px){'
            + '.lp-related{margin:28px 12px 0;padding:20px 0 0}'
            + '.lp-related .lp-rel-heading{font-size:14px;margin-bottom:12px}'
            + '.lp-rel-card{padding:12px 12px 11px 16px}'
            + '.lp-rel-title{font-size:12.5px}'
            + '.lp-rel-tag{font-size:8.5px}'
            + '.lp-rel-meta{font-size:9px}'
            + '.lp-rel-series{font-size:8px;top:8px;right:8px;padding:2px 5px}'
            + '}';
        document.head.appendChild(style);
    }

    if (mount) {
        mount.appendChild(section);
    } else {
        anchor.parentNode.insertBefore(section, anchor);
    }
})();
