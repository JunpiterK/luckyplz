/*
  Lucky Please - Language bar enhancer
  Auto-finds .lang-bar and hides all but 5 primary languages behind a
  "🌐 More" dropdown. Keeps the existing click delegation working —
  secondary buttons retain .lang-btn class so each game's own handler
  still picks them up on click. The More button uses its own class so
  it doesn't accidentally trigger a language switch.
*/

(function(){
    const PRIMARY = ['en','ko','ja','zh','es'];

    function injectStyles(){
        if (document.getElementById('lp-langbar-enhance-styles')) return;
        const s = document.createElement('style');
        s.id = 'lp-langbar-enhance-styles';
        s.textContent = `
.lang-bar{position:relative}
.lang-more-btn{display:inline-flex;align-items:center;gap:3px;padding:3px 9px;border-radius:5px;border:1.5px solid rgba(255,255,255,.12);background:rgba(255,255,255,.04);color:rgba(255,255,255,.55);cursor:pointer;font-size:.72em;font-family:inherit;transition:border-color .25s,background .25s,color .25s;white-space:nowrap;letter-spacing:.02em}
.lang-more-btn:hover{border-color:rgba(255,230,109,.5);background:rgba(255,230,109,.08);color:#fff}
.lang-more-btn .lang-more-chev{font-size:.7em;opacity:.7}
.lang-more-menu{position:absolute;top:calc(100% + 8px);left:50%;transform:translateX(-50%);background:rgba(18,18,36,.98);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.1);border-radius:14px;padding:8px;z-index:60;box-shadow:0 12px 32px rgba(0,0,0,.55);display:grid;grid-template-columns:repeat(3,1fr);gap:6px;min-width:270px;max-width:94vw}
.lang-more-menu[hidden]{display:none}
.lang-more-menu .lang-btn{margin:0;width:100%;justify-content:center}
@media(max-width:500px){
  .lang-more-menu{grid-template-columns:repeat(3,1fr);min-width:240px;padding:6px;gap:4px}
  .lang-more-btn{padding:3px 7px;font-size:.68em}
}
`;
        document.head.appendChild(s);
    }

    function enhance(bar){
        if (bar.dataset.enhanced === '1') return;
        bar.dataset.enhanced = '1';

        const buttons = [...bar.querySelectorAll('.lang-btn')];
        if (!buttons.length) return;

        const secondary = buttons.filter(b => !PRIMARY.includes(b.dataset.lang));
        if (!secondary.length) return; // nothing to hide

        // Build More toggle
        const more = document.createElement('button');
        more.type = 'button';
        more.className = 'lang-more-btn';
        more.title = 'More languages';
        more.innerHTML = '🌐 <span class="lang-more-label">More</span> <span class="lang-more-chev">▾</span>';

        // Build dropdown
        const menu = document.createElement('div');
        menu.className = 'lang-more-menu';
        menu.hidden = true;

        secondary.forEach(b => menu.appendChild(b)); // detach from bar, attach to menu

        bar.appendChild(more);
        bar.appendChild(menu);

        more.addEventListener('click', (e) => {
            e.stopPropagation();
            menu.hidden = !menu.hidden;
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!bar.contains(e.target)) menu.hidden = true;
        });

        // Close when a language inside menu is chosen (after the game's delegated handler runs)
        menu.addEventListener('click', (e) => {
            if (e.target.closest('.lang-btn')) {
                setTimeout(() => { menu.hidden = true; }, 60);
            }
        });
    }

    function run(){
        injectStyles();
        document.querySelectorAll('.lang-bar').forEach(enhance);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', run);
    } else {
        run();
    }
})();
