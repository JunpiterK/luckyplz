/*
  Lucky Please - PC top navigation bar
  Shows on every game page at >=900px. Left edge is a gradient
  "Lucky Please" brand tile that returns to the home page. To the
  right, pill buttons for each game with the current page highlighted.
  Hidden on mobile (existing mobile flows and the floating-home button
  cover that case).
*/

(function(){
    /* Mirror the home-page icon set exactly so every surface (home grid +
       nav bar + cross-promo) shows the same glyph per game. Ladder emoji
       (🪜) tofus on Windows/Edge without full emoji fonts, and the roulette
       / team icons on the home page have diverged from the stock emojis
       (🎯 / 👥) — custom SVGs replicate each. */
    const LADDER_SVG='<svg viewBox="0 0 36 36" width="1em" height="1em" style="vertical-align:middle;display:inline-block"><rect x="9" y="2" width="3.5" height="32" rx="1.5" fill="#e8a848"/><rect x="23.5" y="2" width="3.5" height="32" rx="1.5" fill="#e8a848"/><rect x="11" y="7" width="14" height="3" rx="1" fill="#e8a848"/><rect x="11" y="16.5" width="14" height="3" rx="1" fill="#e8a848"/><rect x="11" y="26" width="14" height="3" rx="1" fill="#e8a848"/></svg>';
    const ROULETTE_SVG='<svg viewBox="0 0 36 36" width="1em" height="1em" style="vertical-align:middle;display:inline-block"><path d="M18 18 L18 4 A14 14 0 0 1 30.1 11 Z" fill="#e74c3c" stroke="#1a1a1a" stroke-width="0.5" stroke-linejoin="round"/><path d="M18 18 L30.1 11 A14 14 0 0 1 30.1 25 Z" fill="#f39c12" stroke="#1a1a1a" stroke-width="0.5" stroke-linejoin="round"/><path d="M18 18 L30.1 25 A14 14 0 0 1 18 32 Z" fill="#f1c40f" stroke="#1a1a1a" stroke-width="0.5" stroke-linejoin="round"/><path d="M18 18 L18 32 A14 14 0 0 1 5.9 25 Z" fill="#2ecc71" stroke="#1a1a1a" stroke-width="0.5" stroke-linejoin="round"/><path d="M18 18 L5.9 25 A14 14 0 0 1 5.9 11 Z" fill="#3498db" stroke="#1a1a1a" stroke-width="0.5" stroke-linejoin="round"/><path d="M18 18 L5.9 11 A14 14 0 0 1 18 4 Z" fill="#9b59b6" stroke="#1a1a1a" stroke-width="0.5" stroke-linejoin="round"/><circle cx="18" cy="18" r="1.8" fill="#1a1a1a"/></svg>';
    const TEAM_SVG='<svg viewBox="0 0 36 36" width="1em" height="1em" style="vertical-align:middle;display:inline-block"><g transform="translate(-5.2 0) scale(0.9)"><circle cx="18" cy="9" r="7" fill="#f0f0f0" stroke="#1a1a1a" stroke-width="1"/><path d="M10 35 L10 22 Q10 17 18 17 Q26 17 26 22 L26 35 Z" fill="#f0f0f0" stroke="#1a1a1a" stroke-width="1" stroke-linejoin="round"/><path d="M17 17 L19 17 L19.3 21 L18 23 L16.7 21 Z" fill="#1a1a1a"/></g><g transform="translate(8.8 0) scale(0.9)"><circle cx="18" cy="9" r="7" fill="#f0f0f0" stroke="#1a1a1a" stroke-width="1"/><path d="M10 35 L10 22 Q10 17 18 17 Q26 17 26 22 L26 35 Z" fill="#f0f0f0" stroke="#1a1a1a" stroke-width="1" stroke-linejoin="round"/><path d="M17 17 L19 17 L19.3 21 L18 23 L16.7 21 Z" fill="#1a1a1a"/></g><circle cx="18" cy="9" r="7" fill="#f0f0f0" stroke="#1a1a1a" stroke-width="0.9"/><path d="M10 35 L10 22 Q10 17 18 17 Q26 17 26 22 L26 35 Z" fill="#f0f0f0" stroke="#1a1a1a" stroke-width="0.9" stroke-linejoin="round"/><path d="M17 17 L19 17 L19.3 21 L18 23 L16.7 21 Z" fill="#1a1a1a"/></svg>';
    const BINGO_SVG='<svg viewBox="0 0 36 36" width="1em" height="1em" style="vertical-align:middle;display:inline-block"><path d="M3 6 Q3 4 5 4 L24 4 L30 9 L30 30 Q30 32 28 32 L5 32 Q3 32 3 30 Z" fill="#f5b5cf" stroke="#1a1a1a" stroke-width="1" stroke-linejoin="round"/><text x="16.5" y="10.5" text-anchor="middle" font-family="Arial Black,Helvetica,sans-serif" font-size="5.2" font-weight="900" fill="#1a1a1a" letter-spacing="0.2">BINGO</text><g fill="#f7f7f7" stroke="#1a1a1a" stroke-width="0.7"><rect x="5.5" y="13" width="6" height="5.5"/><rect x="11.5" y="13" width="6" height="5.5"/><rect x="17.5" y="13" width="6" height="5.5"/><rect x="5.5" y="18.5" width="6" height="5.5"/><rect x="11.5" y="18.5" width="6" height="5.5"/><rect x="17.5" y="18.5" width="6" height="5.5"/><rect x="5.5" y="24" width="6" height="5.5"/><rect x="11.5" y="24" width="6" height="5.5"/><rect x="17.5" y="24" width="6" height="5.5"/></g><path d="M 8.5 15.7 L 9.2 16.95 L 10.5 17.1 L 9.5 18 L 9.85 19.3 L 8.5 18.6 L 7.15 19.3 L 7.5 18 L 6.5 17.1 L 7.8 16.95 Z" fill="#ffc93c" stroke="#1a1a1a" stroke-width="0.25" stroke-linejoin="round"/><g transform="rotate(-28 25 23)"><rect x="18" y="20.8" width="12" height="4.6" rx="0.9" fill="#6cc5ea" stroke="#1a1a1a" stroke-width="0.8"/><rect x="26" y="21.4" width="2.6" height="3.4" fill="#1a1a1a"/><path d="M 30 21.4 L 33.2 23.1 L 30 24.8 Z" fill="#f7c6dd" stroke="#1a1a1a" stroke-width="0.5" stroke-linejoin="round"/></g></svg>';
    const QUIZ_SVG='<svg viewBox="0 0 36 36" width="1em" height="1em" style="vertical-align:middle;display:inline-block"><defs><linearGradient id="lpquizgrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#FFE066"/><stop offset="55%" stop-color="#FFC94D"/><stop offset="100%" stop-color="#FF9A3C"/></linearGradient><path id="lpquizarc" d="M 7.5 17.5 A 10.5 10.5 0 0 1 28.5 17.5"/></defs><circle cx="18" cy="18" r="15.7" fill="url(#lpquizgrad)" stroke="#1a1a1a" stroke-width="1.4"/><text font-family="Arial Black,Impact,sans-serif" font-size="5" font-weight="900" fill="#1a1a1a" letter-spacing="1.2"><textPath href="#lpquizarc" startOffset="50%" text-anchor="middle">QUIZ</textPath></text><text x="18.2" y="29.4" text-anchor="middle" font-family="Arial Black,Impact,sans-serif" font-size="20" font-weight="900" fill="#1a1a1a">?</text></svg>';
    const GAMES=[
        {id:'roulette',  icon:ROULETTE_SVG, url:'/games/roulette/'},
        {id:'ladder',    icon:LADDER_SVG, url:'/games/ladder/'},
        {id:'car-racing',icon:'🏎️',url:'/games/car-racing/'},
        {id:'team',      icon:TEAM_SVG, url:'/games/team/'},
        {id:'lotto',     icon:'🎱', url:'/games/lotto/'},
        {id:'bingo',     icon:BINGO_SVG, url:'/games/bingo/'},
        {id:'quiz',      icon:QUIZ_SVG, url:'/games/quiz/'},
    ];

    const NAMES={
        en:{roulette:'Roulette',ladder:'Ladder','car-racing':'Race',team:'Team',lotto:'Lotto',bingo:'Bingo',quiz:'Quiz'},
        gb:{roulette:'Roulette',ladder:'Ladder','car-racing':'Race',team:'Team',lotto:'Lotto',bingo:'Bingo',quiz:'Quiz'},
        ko:{roulette:'룰렛',ladder:'사다리','car-racing':'카레이싱',team:'팀 뽑기',lotto:'로또',bingo:'빙고',quiz:'퀴즈'},
        ja:{roulette:'ルーレット',ladder:'はしご','car-racing':'レース',team:'チーム',lotto:'ロト',bingo:'ビンゴ',quiz:'クイズ'},
        zh:{roulette:'轮盘',ladder:'梯子','car-racing':'赛车',team:'分队',lotto:'乐透',bingo:'宾果',quiz:'问答'},
        es:{roulette:'Ruleta',ladder:'Escalera','car-racing':'Carrera',team:'Equipos',lotto:'Lotería',bingo:'Bingo',quiz:'Quiz'},
        de:{roulette:'Roulette',ladder:'Leiter','car-racing':'Rennen',team:'Teams',lotto:'Lotto',bingo:'Bingo',quiz:'Quiz'},
        fr:{roulette:'Roulette',ladder:'Échelle','car-racing':'Course',team:'Équipes',lotto:'Loto',bingo:'Bingo',quiz:'Quiz'},
        pt:{roulette:'Roleta',ladder:'Escada','car-racing':'Corrida',team:'Times',lotto:'Loteria',bingo:'Bingo',quiz:'Quiz'},
        ru:{roulette:'Рулетка',ladder:'Лестница','car-racing':'Гонки',team:'Команды',lotto:'Лото',bingo:'Бинго',quiz:'Викторина'},
        ar:{roulette:'روليت',ladder:'سلم','car-racing':'سباق',team:'فرق',lotto:'يانصيب',bingo:'بينغو',quiz:'مسابقة'},
        hi:{roulette:'रूलेट',ladder:'सीढ़ी','car-racing':'रेस',team:'टीम',lotto:'लॉटो',bingo:'बिंगो',quiz:'क्विज़'},
        th:{roulette:'รูเล็ต',ladder:'บันได','car-racing':'แข่งรถ',team:'ทีม',lotto:'ลอตโต',bingo:'บิงโก',quiz:'ควิซ'},
        id:{roulette:'Roulette',ladder:'Tangga','car-racing':'Balap',team:'Tim',lotto:'Undian',bingo:'Bingo',quiz:'Kuis'},
        vi:{roulette:'Vòng quay',ladder:'Thang','car-racing':'Đua xe',team:'Đội',lotto:'Xổ số',bingo:'Bingo',quiz:'Câu đố'},
        tr:{roulette:'Rulet',ladder:'Merdiven','car-racing':'Yarış',team:'Takım',lotto:'Çekiliş',bingo:'Bingo',quiz:'Quiz'},
    };

    function injectStyles(){
        if(document.getElementById('pc-top-nav-styles'))return;
        const s=document.createElement('style');
        s.id='pc-top-nav-styles';
        s.textContent=`
.pc-top-nav{display:none;position:fixed;top:0;left:0;right:0;height:56px;background:rgba(12,14,24,.96);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid rgba(255,255,255,.08);z-index:500;padding:0 14px;align-items:center;gap:10px;box-shadow:0 2px 12px rgba(0,0,0,.3);font-family:'Noto Sans KR',sans-serif}
.pc-top-nav .nav-brand{display:flex;align-items:center;gap:8px;padding:0 16px;height:38px;background:linear-gradient(135deg,#FFE66D,#FF9A3C,#FF6B8B);color:#0A0A1A;font-family:'Orbitron','Noto Sans KR',sans-serif;font-weight:900;font-size:.9em;border-radius:8px;text-decoration:none;letter-spacing:.03em;transition:filter .2s,transform .15s;box-shadow:0 4px 14px rgba(255,154,60,.25);white-space:nowrap;flex-shrink:0}
.pc-top-nav .nav-brand:hover{filter:brightness(1.08);transform:translateY(-1px)}
.pc-top-nav .nav-brand .brand-ico{font-size:1.1em;line-height:1}
.pc-top-nav .nav-sep{width:1px;height:26px;background:rgba(255,255,255,.08);flex-shrink:0}
.pc-top-nav .nav-games{display:flex;gap:5px;align-items:center;overflow-x:auto;scrollbar-width:none;-ms-overflow-style:none;flex:1;min-width:0}
.pc-top-nav .nav-games::-webkit-scrollbar{display:none}
.pc-top-nav .nav-game{display:flex;align-items:center;gap:6px;padding:0 12px;height:36px;border-radius:8px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);color:rgba(255,255,255,.72);text-decoration:none;font-size:.82em;font-weight:600;transition:background .2s,border-color .2s,color .2s;white-space:nowrap;flex-shrink:0}
.pc-top-nav .nav-game:hover{background:rgba(255,255,255,.07);border-color:rgba(255,230,109,.35);color:#fff}
.pc-top-nav .nav-game.active{background:rgba(255,230,109,.1);border-color:rgba(255,230,109,.45);color:#FFE66D;box-shadow:0 0 0 1px rgba(255,230,109,.15)}
.pc-top-nav .nav-game .nav-icon{font-size:1.1em;line-height:1}

@media(min-width:900px){
    .pc-top-nav{display:flex}
    /* Shift fixed page content below the nav bar */
    body.has-top-nav #setupWrap{top:56px !important}
    body.has-top-nav #gameWrap,body.has-top-nav #gameScreen{top:56px !important}
    body.has-top-nav .pc-ad-slot{top:56px !important}
    body.has-top-nav .floating-home{display:none}
}
@media(max-width:899px){
    .pc-top-nav{display:none !important}
}

/* Host-locked state: when a host room is live, all game links here
   (and the mobile FAB) are greyed + unclickable so the host is
   funnelled through the cyan multiplayer panel which is the only
   entry point that correctly locks + transfers the room. The
   brand/home tile + the current-page chip stay clickable since
   they're either "leave the room" (confirmed) or a no-op. */
.pc-top-nav.host-locked .nav-game:not(.active){pointer-events:none;opacity:.28;filter:grayscale(.9)}
.pc-top-nav.host-locked .nav-games::after{
    content:attr(data-host-hint);color:rgba(255,230,109,.65);font-size:.72em;font-weight:700;
    padding:0 10px;align-self:center;white-space:nowrap;letter-spacing:.02em;flex-shrink:0
}

/* ---- Mobile game switcher (floating FAB + bottom sheet) ---- */
.lp-sw-fab{display:none;position:fixed;bottom:84px;right:14px;z-index:600;width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,#FFE66D,#FF9A3C);box-shadow:0 6px 18px rgba(0,0,0,.35);border:none;color:#0A0A1A;font-size:22px;cursor:pointer;font-family:inherit;font-weight:900;line-height:1;align-items:center;justify-content:center;padding:0}
.lp-sw-fab:active{transform:scale(.94)}
@media(max-width:899px){.lp-sw-fab{display:flex}}
/* Host-locked: hide the mobile FAB so the host's only game-switch
   entry point is the cyan multiplayer panel. Prevents "two ways to
   switch" confusion + guards against accidental transfers during
   an active room. */
body.lp-host-active .lp-sw-fab{display:none !important}

.lp-sw-modal{display:none;position:fixed;inset:0;z-index:700;font-family:'Noto Sans KR',sans-serif}
.lp-sw-modal.on{display:block}
.lp-sw-backdrop{position:absolute;inset:0;background:rgba(0,0,0,.6);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px)}
.lp-sw-sheet{position:absolute;left:0;right:0;bottom:0;background:#141426;border-top-left-radius:22px;border-top-right-radius:22px;padding:18px 16px calc(24px + env(safe-area-inset-bottom,0px));max-height:85vh;overflow-y:auto;box-shadow:0 -4px 20px rgba(0,0,0,.5);transform:translateY(100%);transition:transform .25s ease-out}
.lp-sw-modal.on .lp-sw-sheet{transform:translateY(0)}
.lp-sw-title{font-family:'Orbitron','Noto Sans KR',sans-serif;font-weight:900;font-size:1.05em;color:#FFE66D;text-align:center;margin-bottom:6px;letter-spacing:.02em}
.lp-sw-sub{font-size:.75em;color:rgba(255,255,255,.55);text-align:center;margin-bottom:14px}
.lp-sw-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}
.lp-sw-card{display:flex;flex-direction:column;align-items:center;gap:6px;padding:14px 6px;border-radius:12px;background:rgba(255,255,255,.04);border:1.5px solid rgba(255,255,255,.1);color:#fff;font-family:inherit;font-size:.78em;font-weight:700;cursor:pointer;transition:background .2s,border-color .2s,transform .08s}
.lp-sw-card:active{transform:scale(.96)}
.lp-sw-card.active{background:linear-gradient(135deg,rgba(255,230,109,.18),rgba(255,230,109,.05));border-color:#FFE66D;color:#FFE66D;cursor:default}
.lp-sw-ico{font-size:1.8em;line-height:1}
.lp-sw-close{display:block;width:100%;padding:12px;border-radius:10px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);color:#fff;font-family:inherit;font-size:.9em;font-weight:700;cursor:pointer}
.lp-sw-close:active{background:rgba(255,255,255,.1)}
`;
        document.head.appendChild(s);
    }

    function currentGameId(){
        const parts=location.pathname.split('/games/');
        if(parts.length<2)return null;
        const id=parts[1].split('/')[0];
        return GAMES.find(g=>g.id===id)?id:null;
    }

    function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

    function mount(){
        if(document.getElementById('pcTopNav'))return;
        injectStyles();
        const lang=localStorage.getItem('luckyplz_lang')||'en';
        const names=NAMES[lang]||NAMES.en;
        const current=currentGameId();
        const ko=(lang||'en').startsWith('ko');
        const hostHint=ko?'← 파란 창에서 선택하세요':'← Use the cyan panel';

        const nav=document.createElement('nav');
        nav.id='pcTopNav';
        nav.className='pc-top-nav';
        nav.innerHTML=`
            <a class="nav-brand" href="/" aria-label="Lucky Please home">
                <span class="brand-ico">🍀</span>
                <span>Lucky Please</span>
            </a>
            <div class="nav-sep"></div>
            <div class="nav-games" data-host-hint="${escapeHtml(hostHint)}">
                ${GAMES.map(g=>`
                    <a class="nav-game${current===g.id?' active':''}" href="${g.url}" data-game-id="${g.id}">
                        <span class="nav-icon">${g.icon}</span>
                        <span>${escapeHtml(names[g.id]||g.id)}</span>
                    </a>
                `).join('')}
            </div>
        `;
        document.body.prepend(nav);
        document.body.classList.add('has-top-nav');

        /* When a host room is active, intercept nav link clicks and use
           room.transferTo() so the Supabase channel persists across
           navigation (lp_hostTransit + host:navigate broadcast). Without
           this, any click on the top nav drops the room entirely. */
        nav.addEventListener('click',function(e){
            const cur=window.LpMultiplayer&&window.LpMultiplayer._current();
            if(!cur||cur.mode!=='host')return;
            const room=cur.api;
            if(!room||typeof room.transferTo!=='function')return;

            const gameLink=e.target.closest('a[data-game-id]');
            if(gameLink&&!gameLink.classList.contains('active')){
                e.preventDefault();
                room.transferTo(gameLink.href);
                return;
            }
            const brandLink=e.target.closest('.nav-brand');
            if(brandLink){
                e.preventDefault();
                const ko=(localStorage.getItem('luckyplz_lang')||'en').startsWith('ko');
                const msg=ko
                    ?'홈으로 이동하면 멀티플레이 방이 닫힙니다.\n계속하시겠어요?'
                    :'Going home will close the multiplayer room.\nContinue?';
                if(confirm(msg)){
                    try{room.close&&room.close()}catch(_){}
                    location.href='/';
                }
            }
        });

        mountMobileSwitcher(current,names,lang);
        wireHostLock();
    }

    /* Keep the top-nav + mobile FAB in sync with the room state. When
       a host room is live, BOTH surfaces are locked down so the host
       can't accidentally step outside the cyan multiplayer panel —
       which is the only switcher that properly locks + transfers
       the room. Guests stay unaffected. */
    function wireHostLock(){
        function refresh(){
            const cur=window.LpMultiplayer&&window.LpMultiplayer._current();
            const isHost=!!(cur&&cur.mode==='host');
            const nav=document.getElementById('pcTopNav');
            if(nav)nav.classList.toggle('host-locked',isHost);
            document.body.classList.toggle('lp-host-active',isHost);
        }
        window.addEventListener('lp-room-host-ready',refresh);
        window.addEventListener('lp-room-closed',refresh);
        window.addEventListener('lp-room-guest-ready',refresh);
        /* LpMultiplayer attaches asynchronously after lpRoom fires its
           host-ready event. A few staggered probes cover the common
           timing windows (initial load, resume handoff, late-script
           parse) without needing a long-running interval. */
        setTimeout(refresh,300);
        setTimeout(refresh,1200);
        setTimeout(refresh,3000);
    }

    /* Mobile floating game switcher — shown <900px as an always-available
       "🎮" FAB that opens a bottom sheet with all games. Host flows call
       room.transferTo() to preserve the room across navigation; everyone
       else gets a plain location.href. */
    function mountMobileSwitcher(current,names,lang){
        if(document.getElementById('lpSwFab'))return;
        const ko=(lang||'en').startsWith('ko');

        const fab=document.createElement('button');
        fab.id='lpSwFab';
        fab.className='lp-sw-fab';
        fab.type='button';
        fab.setAttribute('aria-label',ko?'다른 게임으로 이동':'Switch game');
        fab.title=ko?'다른 게임':'Switch game';
        fab.textContent='🎮';

        const modal=document.createElement('div');
        modal.id='lpSwModal';
        modal.className='lp-sw-modal';
        modal.innerHTML=
            '<div class="lp-sw-backdrop"></div>'
            +'<div class="lp-sw-sheet">'
            +'<div class="lp-sw-title">'+(ko?'🎮 다른 게임으로':'🎮 Switch Game')+'</div>'
            +'<div class="lp-sw-sub">'+(ko?'시작 전에는 언제든지 바꿀 수 있어요':'Swap freely before the game starts')+'</div>'
            +'<div class="lp-sw-grid">'
            +GAMES.map(function(g){
                const isCur=(current===g.id);
                return '<button class="lp-sw-card'+(isCur?' active':'')+'" type="button" data-game-id="'+g.id+'" data-url="'+g.url+'">'
                    +'<span class="lp-sw-ico">'+g.icon+'</span>'
                    +'<span>'+escapeHtml(names[g.id]||g.id)+'</span>'
                +'</button>';
            }).join('')
            +'</div>'
            +'<button type="button" class="lp-sw-close">'+(ko?'닫기':'Close')+'</button>'
            +'</div>';

        document.body.appendChild(fab);
        document.body.appendChild(modal);

        function open(){modal.classList.add('on')}
        function close(){modal.classList.remove('on')}

        fab.addEventListener('click',open);
        modal.querySelector('.lp-sw-backdrop').addEventListener('click',close);
        modal.querySelector('.lp-sw-close').addEventListener('click',close);

        Array.prototype.forEach.call(modal.querySelectorAll('.lp-sw-card'),function(card){
            card.addEventListener('click',function(){
                if(card.classList.contains('active')){close();return}
                /* Host branch was intentionally removed — when a host
                   room is live the FAB is hidden via body.lp-host-active,
                   so any click here means this is a guest / solo /
                   pre-room visitor and a plain navigation is correct. */
                const url=card.getAttribute('data-url');
                close();
                location.href=url;
            });
        });
    }

    if(document.readyState==='loading'){
        document.addEventListener('DOMContentLoaded',mount);
    } else {
        mount();
    }
})();
