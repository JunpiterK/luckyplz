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

    function kakao(text,url){
        text=text||document.title;
        url=url||location.href;

        /* Mobile: native share sheet includes Kakao/LINE/etc. */
        if(IS_MOBILE&&typeof navigator.share==='function'){
            navigator.share({title:document.title,text:text,url:url})
                .catch(function(err){
                    if(err&&err.name==='AbortError')return; /* user cancelled */
                    copyWithHint(text); /* real error → clipboard */
                });
            return;
        }
        /* Desktop: best we can do without Kakao SDK is clipboard. */
        copyWithHint(text);
    }

    window.LpShare={kakao:kakao,copyWithHint:copyWithHint,toast:toast};
})();
