/* Lucky Please — share helpers
   Centralises the "share to Kakao" path so every game reaches the same
   graceful-degradation chain instead of each having its own ad-hoc logic.

   Chain:
   1. Mobile + Web Share API available → navigator.share opens the native
      share sheet, which on Korean phones lists KakaoTalk as a first-class
      option. This is the cleanest real-world Kakao share we can do without
      registering a Kakao Developer app.
   2. Otherwise (desktop, or Share API missing) → copy the share text to
      clipboard and show a toast telling the user to paste into Kakao.

   Why we removed sharer.kakao.com: that endpoint requires the host domain
   to be registered under a Kakao Developer application. Without registration
   it either 404s or redirects to a login wall. The silent failure is worse
   than a toast that tells you what to do.

   If the domain ever gets Kakao-SDK registered, replace `kakao()` with
   `Kakao.Share.sendDefault(...)` and this module becomes SDK-backed. */
(function(){
    const UA=(navigator.userAgent||'');
    const IS_MOBILE=/Mobi|Android|iPhone|iPad|iPod/.test(UA);

    function ensureToast(){
        let t=document.getElementById('lpShareToastGlobal');
        if(t)return t;
        t=document.createElement('div');
        t.id='lpShareToastGlobal';
        t.style.cssText='position:fixed;top:20px;left:50%;transform:translateX(-50%);'
            +'padding:12px 20px;border-radius:999px;background:rgba(10,10,26,.92);'
            +'color:#fff;font-family:"Noto Sans KR",sans-serif;font-size:.9em;'
            +'z-index:10000;backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);'
            +'border:1px solid rgba(255,230,109,.3);box-shadow:0 12px 30px rgba(0,0,0,.4);'
            +'opacity:0;transition:opacity .2s;pointer-events:none;max-width:90vw;text-align:center';
        document.body.appendChild(t);
        return t;
    }

    function toast(msg,ms){
        const t=ensureToast();
        t.textContent=msg;
        t.style.opacity='1';
        clearTimeout(t._lpToastTimer);
        t._lpToastTimer=setTimeout(function(){t.style.opacity='0'},ms||3000);
    }

    function lang(){
        return (localStorage.getItem('luckyplz_lang')||document.documentElement.lang||'en').toLowerCase().split('-')[0];
    }

    function copiedMsg(){
        const l=lang();
        if(l==='ko')return '📋 복사됨! 카카오톡 열고 붙여넣으세요';
        if(l==='ja')return '📋 コピー完了！LINE/カカオに貼り付けて共有';
        if(l==='zh')return '📋 已复制！打开聊天应用粘贴即可';
        return '📋 Copied! Open Kakao/chat and paste to share';
    }

    function clipboardCopy(text){
        if(navigator.clipboard&&navigator.clipboard.writeText){
            return navigator.clipboard.writeText(text);
        }
        /* execCommand fallback for older browsers / insecure contexts */
        return new Promise(function(resolve,reject){
            try{
                const el=document.createElement('textarea');
                el.value=text;el.style.position='fixed';el.style.opacity='0';
                document.body.appendChild(el);el.select();
                const ok=document.execCommand('copy');
                document.body.removeChild(el);
                ok?resolve():reject(new Error('copy failed'));
            }catch(e){reject(e)}
        });
    }

    function copyWithHint(text){
        clipboardCopy(text)
            .then(function(){toast(copiedMsg(),3500)})
            .catch(function(){toast('⚠️ Copy failed',2500)});
    }

    function kakao(text,url,imageBlob){
        text=text||document.title;
        url=url||location.href;

        /* Mobile: native share sheet includes Kakao/LINE/etc. When an
           image Blob is attached + Web Share Level 2 (files) is
           supported, the share sheet creates a rich preview card with
           the image — this makes Kakao/LINE chat previews 10× more
           eye-catching vs. the plain text+url fallback. */
        if(IS_MOBILE&&typeof navigator.share==='function'){
            const data={title:document.title,text:text,url:url};
            if(imageBlob&&typeof File==='function'&&typeof navigator.canShare==='function'){
                try{
                    const file=new File([imageBlob],'luckyplz-result.png',{type:'image/png'});
                    if(navigator.canShare({files:[file]}))data.files=[file];
                }catch(e){}
            }
            navigator.share(data)
                .catch(function(err){
                    if(err&&err.name==='AbortError')return; /* user cancelled */
                    copyWithHint(text); /* real error → clipboard */
                });
            return;
        }
        /* Desktop: best we can do without Kakao SDK is clipboard. */
        copyWithHint(text);
    }

    /* ===== RESULT CARD (PNG 1200×630) =====
       Generates a branded Open-Graph-sized PNG Blob summarising the
       game result. 1200×630 is the canonical OG image size that
       KakaoTalk, LINE, WhatsApp, Twitter/X, and Facebook all render
       as a link preview. When attached to a Web Share L2 call, iOS/
       Android's native share sheet treats it as the primary visual
       which produces a dramatically more click-worthy chat message.

       Keep the card self-contained: no external images, no web font
       dependencies (relies on 'Noto Sans KR' + sans-serif fallback
       which is already declared on every game page). Async because
       Canvas.toBlob is async on all major engines. Non-blocking so
       games can kick this off at result display and it's usually
       done before the user reaches for the share button. */
    function buildResultCardBlob(opts){
        opts=opts||{};
        return new Promise(function(resolve){
            try{
                const W=1200,H=630;
                const c=document.createElement('canvas');
                c.width=W;c.height=H;
                const ctx=c.getContext('2d');
                /* Diagonal gradient backdrop — LuckyPlz dark brand */
                const bg=ctx.createLinearGradient(0,0,W,H);
                bg.addColorStop(0,'#0A0A1A');
                bg.addColorStop(0.5,'#18183A');
                bg.addColorStop(1,'#0A0A1A');
                ctx.fillStyle=bg;ctx.fillRect(0,0,W,H);
                /* Subtle grid for depth */
                ctx.strokeStyle='rgba(255,255,255,0.035)';
                ctx.lineWidth=1;
                for(let i=40;i<W;i+=40){ctx.beginPath();ctx.moveTo(i,0);ctx.lineTo(i,H);ctx.stroke();}
                for(let j=40;j<H;j+=40){ctx.beginPath();ctx.moveTo(0,j);ctx.lineTo(W,j);ctx.stroke();}
                /* Accent ribbon top */
                const rib=ctx.createLinearGradient(0,0,W,0);
                rib.addColorStop(0,'#FF6B35');rib.addColorStop(0.5,'#FFE66D');rib.addColorStop(1,'#00D9FF');
                ctx.fillStyle=rib;ctx.fillRect(0,0,W,8);
                /* Title (game emoji + name) — top-center */
                ctx.textAlign='center';
                ctx.textBaseline='top';
                ctx.font='700 44px "Noto Sans KR","Apple SD Gothic Neo",sans-serif';
                ctx.fillStyle='rgba(255,230,109,0.92)';
                ctx.fillText(opts.title||'Lucky Please',W/2,54);
                /* Subtitle (context line) */
                if(opts.subtitle){
                    ctx.font='400 28px "Noto Sans KR","Apple SD Gothic Neo",sans-serif';
                    ctx.fillStyle='rgba(255,255,255,0.55)';
                    ctx.fillText(opts.subtitle,W/2,118);
                }
                /* Winner — centerpiece */
                if(opts.winner){
                    const color=opts.color||'#FF6B35';
                    /* Pill badge behind winner */
                    const pillY=235,pillH=190;
                    const winFont='900 132px "Noto Sans KR","Apple SD Gothic Neo",sans-serif';
                    ctx.font=winFont;
                    /* Measure to size the pill */
                    const wMetrics=ctx.measureText(opts.winner);
                    const pillW=Math.min(1080,Math.max(520,wMetrics.width+160));
                    const pillX=(W-pillW)/2;
                    /* Pill glow + fill */
                    ctx.shadowColor=color;ctx.shadowBlur=60;
                    ctx.fillStyle='rgba(255,255,255,0.04)';
                    _roundRect(ctx,pillX,pillY,pillW,pillH,pillH/2);ctx.fill();
                    ctx.shadowBlur=0;
                    ctx.strokeStyle=color;ctx.lineWidth=4;
                    _roundRect(ctx,pillX,pillY,pillW,pillH,pillH/2);ctx.stroke();
                    /* Winner text */
                    ctx.textBaseline='middle';
                    ctx.shadowColor=color;ctx.shadowBlur=30;
                    ctx.fillStyle='#FFFFFF';
                    ctx.fillText(opts.winner,W/2,pillY+pillH/2+4);
                    ctx.shadowBlur=0;
                }
                /* Highlight line under winner */
                if(opts.highlight){
                    ctx.font='500 34px "Noto Sans KR","Apple SD Gothic Neo",sans-serif';
                    ctx.fillStyle='rgba(255,255,255,0.82)';
                    ctx.textBaseline='top';
                    ctx.fillText(opts.highlight,W/2,460);
                }
                /* Brand footer */
                ctx.textAlign='left';
                ctx.font='700 26px "Orbitron","Noto Sans KR",sans-serif';
                ctx.fillStyle='rgba(0,217,255,0.85)';
                ctx.fillText('🍀  luckyplz.com',44,560);
                ctx.textAlign='right';
                ctx.font='400 22px "Noto Sans KR",sans-serif';
                ctx.fillStyle='rgba(255,255,255,0.45)';
                ctx.fillText(opts.tagline||'Decide in 10 seconds.',W-44,564);
                /* Export — JPEG would be smaller but PNG keeps text
                   edges sharp for link previews. */
                c.toBlob(function(b){resolve(b||null)},'image/png',0.92);
            }catch(e){resolve(null)}
        });
    }

    function _roundRect(ctx,x,y,w,h,r){
        r=Math.min(r,w/2,h/2);
        ctx.beginPath();
        ctx.moveTo(x+r,y);
        ctx.arcTo(x+w,y,x+w,y+h,r);
        ctx.arcTo(x+w,y+h,x,y+h,r);
        ctx.arcTo(x,y+h,x,y,r);
        ctx.arcTo(x,y,x+w,y,r);
        ctx.closePath();
    }

    window.LpShare={kakao:kakao,copyWithHint:copyWithHint,toast:toast,buildResultCardBlob:buildResultCardBlob};
})();
