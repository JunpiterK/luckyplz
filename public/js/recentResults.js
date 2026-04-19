/* Lucky Please — recent results memory
   Saves the user's last few game results to localStorage so the home page
   can show a "last played" strip — a subtle retention hook that makes
   returning visitors feel picked up where they left off.

   Shape stored (array, newest-first, max 5):
   [
     { gameId: 'roulette', emoji: '🎯', gameName: '룰렛',
       summary: 'BTS 슈가 당첨', url: '/games/roulette/', savedAt: 123... },
     ...
   ]

   Names/labels are stored as recorded at save-time, so past entries keep
   reading sensibly even if the user switches language mid-session. */
(function(){
    const KEY='luckyplz_recent_results';
    const MAX=5;

    const GAME_META={
        roulette:   {emoji:'🎯', ko:'룰렛',   en:'Roulette',   ja:'ルーレット', zh:'轮盘'},
        ladder:     {emoji:'🪜', ko:'사다리', en:'Ladder',     ja:'はしご',     zh:'梯子'},
        team:       {emoji:'👥', ko:'팀 뽑기',en:'Team',       ja:'チーム',     zh:'分队'},
        'car-racing':{emoji:'🏎️',ko:'카레이싱',en:'Race',      ja:'レース',     zh:'赛车'},
        lotto:      {emoji:'🎱', ko:'로또',   en:'Lotto',      ja:'ロト',       zh:'乐透'}
    };

    function load(){
        try{const raw=localStorage.getItem(KEY);if(!raw)return [];const arr=JSON.parse(raw);return Array.isArray(arr)?arr:[]}catch(e){return []}
    }
    function write(list){
        try{localStorage.setItem(KEY,JSON.stringify(list))}catch(e){}
    }

    function save(gameId, summary, url){
        if(!gameId||!summary)return;
        const meta=GAME_META[gameId]||{};
        const lang=(localStorage.getItem('luckyplz_lang')||document.documentElement.lang||'en').toLowerCase();
        const gameName=meta[lang]||meta.en||gameId;
        const entry={
            gameId:gameId,
            emoji:meta.emoji||'🎮',
            gameName:gameName,
            summary:String(summary).slice(0,60),
            url:url||('/games/'+gameId+'/'),
            savedAt:Date.now()
        };
        const list=load().filter(e=>e.gameId!==gameId);
        list.unshift(entry);
        write(list.slice(0,MAX));
    }

    function clearAll(){try{localStorage.removeItem(KEY)}catch(e){}}

    function timeAgo(ts,lang){
        const s=Math.max(1,Math.floor((Date.now()-ts)/1000));
        if(s<60){return lang==='ko'?'방금 전':(lang==='ja'?'たった今':'just now')}
        const m=Math.floor(s/60);if(m<60){return lang==='ko'?m+'분 전':(lang==='ja'?m+'分前':m+'m ago')}
        const h=Math.floor(m/60);if(h<24){return lang==='ko'?h+'시간 전':(lang==='ja'?h+'時間前':h+'h ago')}
        const d=Math.floor(h/24);return lang==='ko'?d+'일 전':(lang==='ja'?d+'日前':d+'d ago');
    }

    function escapeHtml(s){return String(s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}

    function render(mount,labels){
        labels=labels||{};
        const list=load();
        mount.innerHTML='';
        if(!list.length)return;
        const lang=(localStorage.getItem('luckyplz_lang')||'en').toLowerCase();
        const head=document.createElement('div');
        head.className='lp-recent-head';
        head.innerHTML='<span class="lp-recent-title">'+(labels.title||'RECENT')+'</span>'
                     +'<button type="button" class="lp-recent-clear" aria-label="clear">&times;</button>';
        head.querySelector('.lp-recent-clear').addEventListener('click',function(){clearAll();render(mount,labels)});
        mount.appendChild(head);
        const row=document.createElement('div');
        row.className='lp-recent-row';
        list.forEach(function(item){
            const a=document.createElement('a');
            a.className='lp-recent-chip';
            a.href=item.url;
            a.innerHTML='<span class="lp-recent-emoji">'+item.emoji+'</span>'
                       +'<span class="lp-recent-body">'
                           +'<span class="lp-recent-game">'+escapeHtml(item.gameName)+'</span>'
                           +'<span class="lp-recent-summary">'+escapeHtml(item.summary)+'</span>'
                       +'</span>'
                       +'<span class="lp-recent-time">'+timeAgo(item.savedAt,lang)+'</span>';
            row.appendChild(a);
        });
        mount.appendChild(row);
    }

    function injectStyles(){
        if(document.getElementById('lp-recent-styles'))return;
        const s=document.createElement('style');
        s.id='lp-recent-styles';
        s.textContent=
            '.lp-recent-wrap{width:100%;max-width:1200px;margin:20px auto 0;padding:0 4px}'
           +'.lp-recent-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}'
           +'.lp-recent-title{font-family:"Orbitron","Noto Sans KR",sans-serif;font-size:.72em;color:rgba(255,255,255,.4);letter-spacing:2.5px;font-weight:700}'
           +'.lp-recent-clear{background:none;border:0;color:rgba(255,255,255,.25);font-size:1.2em;line-height:1;cursor:pointer;padding:4px 8px;transition:color .2s}'
           +'.lp-recent-clear:hover{color:#FF6B8B}'
           +'.lp-recent-row{display:flex;flex-wrap:wrap;gap:8px}'
           +'.lp-recent-chip{display:inline-flex;align-items:center;gap:10px;padding:8px 14px 8px 10px;border-radius:999px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);color:#fff;text-decoration:none;font-family:"Noto Sans KR",sans-serif;transition:background .2s,border-color .2s,transform .15s;max-width:100%}'
           +'.lp-recent-chip:hover{background:rgba(255,230,109,.08);border-color:rgba(255,230,109,.3);transform:translateY(-1px)}'
           +'.lp-recent-emoji{font-size:1.2em;line-height:1;flex-shrink:0}'
           +'.lp-recent-body{display:flex;flex-direction:column;align-items:flex-start;min-width:0}'
           +'.lp-recent-game{font-size:.66em;color:rgba(255,230,109,.75);letter-spacing:.05em;font-weight:700;text-transform:uppercase}'
           +'.lp-recent-summary{font-size:.82em;color:rgba(255,255,255,.85);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:180px}'
           +'.lp-recent-time{font-size:.68em;color:rgba(255,255,255,.35);letter-spacing:.02em;flex-shrink:0}';
        document.head.appendChild(s);
    }

    injectStyles();

    window.LpRecent={save:save,load:load,render:render,clearAll:clearAll};
})();
