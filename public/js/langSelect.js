/* Shared language selector for CONTENT pages (blog index, tools landing,
   tool pages). The games homepage keeps its own 16-language .lang-bar (cleaned
   to 5 primary + a "More" dropdown by /js/langBar.js) for global game SEO.
   Content is focused on 5 languages by population x operating cost:
   Korean, English, Japanese, Chinese, Spanish.

   - ko/en are always offered (base). ja/zh/es show their own version when it
     exists, else fall back to English.
   - Two routing modes, auto-detected:
       * directory pages (have per-language <link rel="alternate" hreflang>):
         navigate to that language's URL; missing language -> the English URL.
       * client-i18n pages (blog index, tools landing): set ?lang= and reload;
         the page swaps its own strings (and falls back es/other -> en itself).
   - The pick is stored in localStorage('luckyplz_lang') — the same shared key
     the homepage and blog index read — so the choice follows the user.

   Mount: appends into #lp-langbar if present, else prepends to <body>. */
(function () {
  if (document.getElementById('lpLangSelMounted')) return;
  // [code, label, flag-cc] — same labels/flags/style as the homepage .lang-bar
  var LANGS = [['ko', '한국', 'kr'], ['en', 'EN', 'us'], ['ja', '日本', 'jp'], ['zh', '中文', 'cn'], ['es', 'ES', 'es']];
  var CODES = LANGS.map(function (l) { return l[0]; });

  function norm(l) {
    l = (l || '').toLowerCase();
    for (var i = 0; i < CODES.length; i++) {
      if (l === CODES[i] || l.indexOf(CODES[i]) === 0) return CODES[i];
    }
    return l;
  }
  function altMap() {
    var alts = document.querySelectorAll('link[rel="alternate"][hreflang]'), map = {};
    for (var i = 0; i < alts.length; i++) map[alts[i].getAttribute('hreflang')] = alts[i].href;
    return map;
  }
  /* A "directory page" has its own URL per language (>1 distinct hreflang lang,
     ignoring x-default), e.g. the tool pages. Its current language is fixed by
     <html lang>. A "client-i18n page" (blog index, tools landing) adapts in
     place, so its current language is the ?lang / stored pick. */
  function isDirPage(map) {
    var n = 0; for (var k in map) { if (k !== 'x-default') n++; }
    return n > 1;
  }
  function pick() {
    if (isDirPage(altMap())) {
      var hl = norm(document.documentElement.getAttribute('lang') || '');
      if (hl) return hl;
    }
    try { var q = new URLSearchParams(location.search).get('lang'); if (q) return norm(q); } catch (e) {}
    try { var s = localStorage.getItem('luckyplz_lang'); if (s) return norm(s); } catch (e) {}
    return 'ko';
  }
  var cur = pick();

  var st = document.createElement('style');
  st.textContent =
    '.lp-langsel{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;padding:8px 10px;font-family:inherit}' +
    '.lp-langsel button{display:flex;align-items:center;gap:4px;background:rgba(255,255,255,.05);' +
    'border:1px solid rgba(255,255,255,.1);border-radius:6px;padding:4px 8px;font-size:12.5px;font-weight:600;' +
    'color:rgba(255,255,255,.5);cursor:pointer;transition:border-color .2s,background .2s,color .2s;' +
    'font-family:inherit;line-height:1.2;white-space:nowrap}' +
    '.lp-langsel button img{width:20px;height:14px;border-radius:2px;object-fit:cover;display:block;flex:none}' +
    '.lp-langsel button:hover{border-color:#FF6B35;background:rgba(255,107,53,.1)}' +
    '.lp-langsel button.on{border-color:#FF6B35;background:rgba(255,107,53,.15);color:#fff}';
  document.head.appendChild(st);

  var bar = document.createElement('nav');
  bar.id = 'lpLangSelMounted';
  bar.className = 'lp-langsel';
  bar.setAttribute('aria-label', 'language');
  LANGS.forEach(function (L) {
    var b = document.createElement('button');
    b.type = 'button';
    var img = document.createElement('img');
    img.src = 'https://flagcdn.com/w40/' + L[2] + '.png';
    img.alt = '';
    img.setAttribute('loading', 'lazy');
    b.appendChild(img);
    b.appendChild(document.createTextNode(L[1]));
    b.setAttribute('lang', L[0]);
    if (L[0] === cur) b.className = 'on';
    b.addEventListener('click', function () { go(L[0]); });
    bar.appendChild(b);
  });

  var mount = document.getElementById('lp-langbar');
  if (mount) mount.appendChild(bar);
  else document.body.insertBefore(bar, document.body.firstChild);

  function base(href) { return href.split('#')[0].split('?')[0].replace(/\/+$/, '/'); }

  function go(L) {
    try { localStorage.setItem('luckyplz_lang', L); } catch (e) {}
    var map = altMap();
    if (isDirPage(map)) {
      var target = map[L];
      if (!target && L !== 'ko' && L !== 'en') target = map['en'] || map['x-default'];  // missing -> English
      if (target && base(target) !== base(location.href)) { location.href = target; return; }
      // clicking the current language: nothing to do
      if (target && base(target) === base(location.href)) return;
    }
    var u = new URL(location.href);
    u.searchParams.set('lang', L);
    location.href = u.toString();
  }
})();
