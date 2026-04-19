/* Lucky Please — participant preset memory
   Saves the most-recently-used participant lists per game to localStorage
   so returning users can restore a list in one tap instead of retyping.

   Scope: games that take a set of named participants at setup time
   (roulette, ladder, team, car-racing, dice). Lotto uses numeric ranges
   only and doesn't need this.

   Privacy: names stay in the visitor's own browser. No server round-trip. */
(function(){
    const MAX_PRESETS=5;
    const MIN_ITEMS=2;  /* single-person list is useless; skip */

    function storageKey(gameId){return 'luckyplz_presets_'+gameId}

    function load(gameId){
        try{
            const raw=localStorage.getItem(storageKey(gameId));
            if(!raw)return [];
            const arr=JSON.parse(raw);
            return Array.isArray(arr)?arr.filter(p=>p&&Array.isArray(p.items)):[];
        }catch(e){return []}
    }

    function save(gameId,presets){
        try{localStorage.setItem(storageKey(gameId),JSON.stringify(presets))}catch(e){}
    }

    /* Dedup by serialized items order so the same list on two different
       days becomes one entry (just bumps its timestamp). */
    function sig(items){return items.join('|')}

    /* Record a new preset. Items that are purely the default placeholder
       values (passed via `placeholders`) are ignored so we don't pollute
       the list when a user just hits Start without typing. */
    function record(gameId,items,placeholders){
        if(!Array.isArray(items))return;
        const cleaned=items.map(s=>(s||'').trim()).filter(Boolean);
        if(cleaned.length<MIN_ITEMS)return;
        /* Skip if every slot matches its placeholder (no user edit). */
        if(placeholders&&placeholders.length===cleaned.length){
            const allDefault=cleaned.every((v,i)=>v===(placeholders[i]||'').trim());
            if(allDefault)return;
        }
        const presets=load(gameId);
        const mySig=sig(cleaned);
        const existingIdx=presets.findIndex(p=>sig(p.items)===mySig);
        const now=Date.now();
        if(existingIdx>=0){
            presets[existingIdx].savedAt=now;
        }else{
            presets.push({items:cleaned,savedAt:now});
        }
        presets.sort((a,b)=>b.savedAt-a.savedAt);
        save(gameId,presets.slice(0,MAX_PRESETS));
    }

    function remove(gameId,itemsSig){
        const presets=load(gameId).filter(p=>sig(p.items)!==itemsSig);
        save(gameId,presets);
    }

    /* Render preset chips into `mount`. When a chip is clicked, `onApply`
       is invoked with the preset's items array; caller is responsible for
       pushing those into its input fields and triggering any re-render. */
    function render(gameId,mount,onApply,labels){
        labels=labels||{};
        const presets=load(gameId);
        mount.innerHTML='';
        if(!presets.length)return;
        const title=document.createElement('div');
        title.className='lp-preset-title';
        title.textContent=labels.recent||'Recent';
        mount.appendChild(title);
        const row=document.createElement('div');
        row.className='lp-preset-row';
        presets.forEach(p=>{
            const chip=document.createElement('button');
            chip.type='button';
            chip.className='lp-preset-chip';
            const preview=p.items.slice(0,3).join(', ')+(p.items.length>3?' …':'');
            chip.innerHTML='<span class="lp-preset-count">'+p.items.length+'</span>'
                         +'<span class="lp-preset-names">'+escapeHtml(preview)+'</span>'
                         +'<span class="lp-preset-x" aria-label="remove">&times;</span>';
            chip.querySelector('.lp-preset-x').addEventListener('click',function(ev){
                ev.stopPropagation();
                remove(gameId,sig(p.items));
                render(gameId,mount,onApply,labels);
            });
            chip.addEventListener('click',function(){onApply(p.items.slice())});
            row.appendChild(chip);
        });
        mount.appendChild(row);
    }

    function escapeHtml(s){
        return String(s).replace(/[&<>"']/g,function(c){
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
        });
    }

    function injectStyles(){
        if(document.getElementById('lp-preset-styles'))return;
        const s=document.createElement('style');
        s.id='lp-preset-styles';
        s.textContent=
            '.lp-preset-title{font-family:"Orbitron","Noto Sans KR",sans-serif;font-size:.62em;letter-spacing:2.5px;color:rgba(255,255,255,.45);font-weight:700;margin:0 0 8px;text-transform:uppercase}'
           +'.lp-preset-row{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}'
           +'.lp-preset-chip{display:inline-flex;align-items:center;gap:6px;padding:6px 10px 6px 8px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:999px;color:rgba(255,255,255,.78);font-family:"Noto Sans KR",sans-serif;font-size:.72em;cursor:pointer;transition:background .18s,border-color .18s,color .18s;max-width:100%}'
           +'.lp-preset-chip:hover{background:rgba(255,230,109,.1);border-color:rgba(255,230,109,.35);color:#fff}'
           +'.lp-preset-count{background:rgba(255,230,109,.18);color:#FFE66D;font-weight:700;padding:1px 7px;border-radius:999px;font-size:.85em;flex-shrink:0}'
           +'.lp-preset-names{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:180px}'
           +'.lp-preset-x{color:rgba(255,255,255,.25);font-size:1.1em;line-height:1;padding:0 2px;flex-shrink:0;transition:color .18s}'
           +'.lp-preset-x:hover{color:#FF6B8B}';
        document.head.appendChild(s);
    }

    injectStyles();

    window.LpPresets={
        record:record,
        render:render,
        load:load
    };
})();
