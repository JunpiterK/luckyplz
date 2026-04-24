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
    const GAMES=[
        {id:'roulette',  icon:ROULETTE_SVG, url:'/games/roulette/'},
        {id:'ladder',    icon:LADDER_SVG, url:'/games/ladder/'},
        {id:'car-racing',icon:'🏎️',url:'/games/car-racing/'},
        {id:'team',      icon:TEAM_SVG, url:'/games/team/'},
        {id:'lotto',     icon:'🎱', url:'/games/lotto/'},
    ];

    const NAMES={
        en:{roulette:'Roulette',ladder:'Ladder','car-racing':'Race',team:'Team',lotto:'Lotto'},
        gb:{roulette:'Roulette',ladder:'Ladder','car-racing':'Race',team:'Team',lotto:'Lotto'},
        ko:{roulette:'룰렛',ladder:'사다리','car-racing':'카레이싱',team:'팀 뽑기',lotto:'로또'},
        ja:{roulette:'ルーレット',ladder:'はしご','car-racing':'レース',team:'チーム',lotto:'ロト'},
        zh:{roulette:'轮盘',ladder:'梯子','car-racing':'赛车',team:'分队',lotto:'乐透'},
        es:{roulette:'Ruleta',ladder:'Escalera','car-racing':'Carrera',team:'Equipos',lotto:'Lotería'},
        de:{roulette:'Roulette',ladder:'Leiter','car-racing':'Rennen',team:'Teams',lotto:'Lotto'},
        fr:{roulette:'Roulette',ladder:'Échelle','car-racing':'Course',team:'Équipes',lotto:'Loto'},
        pt:{roulette:'Roleta',ladder:'Escada','car-racing':'Corrida',team:'Times',lotto:'Loteria'},
        ru:{roulette:'Рулетка',ladder:'Лестница','car-racing':'Гонки',team:'Команды',lotto:'Лото'},
        ar:{roulette:'روليت',ladder:'سلم','car-racing':'سباق',team:'فرق',lotto:'يانصيب'},
        hi:{roulette:'रूलेट',ladder:'सीढ़ी','car-racing':'रेस',team:'टीम',lotto:'लॉटो'},
        th:{roulette:'รูเล็ต',ladder:'บันได','car-racing':'แข่งรถ',team:'ทีม',lotto:'ลอตโต'},
        id:{roulette:'Roulette',ladder:'Tangga','car-racing':'Balap',team:'Tim',lotto:'Undian'},
        vi:{roulette:'Vòng quay',ladder:'Thang','car-racing':'Đua xe',team:'Đội',lotto:'Xổ số'},
        tr:{roulette:'Rulet',ladder:'Merdiven','car-racing':'Yarış',team:'Takım',lotto:'Çekiliş'},
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

        const nav=document.createElement('nav');
        nav.id='pcTopNav';
        nav.className='pc-top-nav';
        nav.innerHTML=`
            <a class="nav-brand" href="/" aria-label="Lucky Please home">
                <span class="brand-ico">🍀</span>
                <span>Lucky Please</span>
            </a>
            <div class="nav-sep"></div>
            <div class="nav-games">
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
    }

    if(document.readyState==='loading'){
        document.addEventListener('DOMContentLoaded',mount);
    } else {
        mount();
    }
})();
