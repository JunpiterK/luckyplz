/* Lucky Please - AdSense slot injector
   Mounts on-demand ad units into `<div data-lp-ad="<type>"></div>` containers.
   Slot IDs are filled AFTER AdSense approval — until then, nothing renders
   (no empty boxes, no layout shift, no console noise).

   Post-approval steps:
   1. Create 3 ad units in AdSense dashboard (Display, Responsive, Auto format):
      · "Game Result"   → Replace SLOTS.result below
      · "Home Grid"     → Replace SLOTS.home below
      · "Blog Article"  → Replace SLOTS.blog below
   2. Commit the file. Slots go live on next deploy. */
(function(){
    const CLIENT_ID='ca-pub-5370817769801923';
    const SLOTS={
        result:'3406981908',  /* Game Result — 5 games' result screens */
        home:  '1104252197',  /* Home Grid — below the game cards */
        blog:  '8046124551'   /* Blog Article — below each post */
    };

    function mountAd(container){
        const type=container.dataset.lpAd;
        const slot=SLOTS[type];
        if(!slot||slot.indexOf('TODO_')===0)return;
        if(container.dataset.lpAdMounted)return;
        container.dataset.lpAdMounted='1';
        const ins=document.createElement('ins');
        ins.className='adsbygoogle';
        ins.style.display='block';
        ins.style.margin='24px auto';
        ins.style.maxWidth='728px';
        ins.style.width='100%';
        ins.setAttribute('data-ad-client',CLIENT_ID);
        ins.setAttribute('data-ad-slot',slot);
        ins.setAttribute('data-ad-format','auto');
        ins.setAttribute('data-full-width-responsive','true');
        container.appendChild(ins);
        try{(window.adsbygoogle=window.adsbygoogle||[]).push({})}catch(e){}
    }

    /* Wait for the container to be visible before pushing — result screens
       start hidden behind `display:none` and only render when the game
       completes; pushing to a 0-height container wastes a fill. */
    function observeAll(){
        const targets=document.querySelectorAll('[data-lp-ad]:not([data-lp-ad-mounted])');
        if(!targets.length)return;
        if(!('IntersectionObserver' in window)){
            targets.forEach(mountAd);
            return;
        }
        const io=new IntersectionObserver(function(entries){
            entries.forEach(function(e){
                if(e.isIntersecting){
                    mountAd(e.target);
                    io.unobserve(e.target);
                }
            });
        },{rootMargin:'100px'});
        targets.forEach(function(el){io.observe(el)});
    }

    if(document.readyState==='loading'){
        document.addEventListener('DOMContentLoaded',observeAll);
    }else{
        observeAll();
    }

    /* Expose a re-scan hook for games that inject result screens dynamically
       or rebuild the DOM; they can call window.lpMountAds() after the change. */
    window.lpMountAds=observeAll;
})();
