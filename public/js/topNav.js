/*
  Lucky Please - PC top navigation bar
  Shows on every game page at >=900px. Left edge is a gradient
  "Lucky Please" brand tile that returns to the home page. To the
  right, pill buttons for each game with the current page highlighted.
  Hidden on mobile (existing mobile flows and the floating-home button
  cover that case).
*/

(function(){
    const GAMES=[
        {id:'roulette',  icon:'🎯', url:'/games/roulette/'},
        {id:'ladder',    icon:'🪜', url:'/games/ladder/'},
        {id:'car-racing',icon:'🏎️',url:'/games/car-racing/'},
        {id:'team',      icon:'👥', url:'/games/team/'},
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
                    <a class="nav-game${current===g.id?' active':''}" href="${g.url}">
                        <span class="nav-icon">${g.icon}</span>
                        <span>${escapeHtml(names[g.id]||g.id)}</span>
                    </a>
                `).join('')}
            </div>
        `;
        document.body.prepend(nav);
        document.body.classList.add('has-top-nav');
    }

    if(document.readyState==='loading'){
        document.addEventListener('DOMContentLoaded',mount);
    } else {
        mount();
    }
})();
