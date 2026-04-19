/* Shared site-wide footer. Mounted as a static element at the end of <body>
   so it flows naturally below scrollable content pages (home, blog, privacy,
   about) and stays out of the way on game pages, where the page is covered
   by fixed #setupWrap/#gameWrap panels (the footer is still in the DOM for
   crawlers + AdSense review to find Privacy/About links). */
(function(){
    if(document.querySelector('.lp-site-footer'))return;

    var style=document.createElement('style');
    style.textContent=
        '.lp-site-footer{position:relative;z-index:1;padding:22px 16px 28px;text-align:center;'
        +'font-family:"Noto Sans KR",sans-serif;font-size:.76em;line-height:1.8;'
        +'color:rgba(255,255,255,.42);background:transparent}'
        +'.lp-site-footer a{color:rgba(255,255,255,.65);margin:0 8px;text-decoration:none;transition:color .18s}'
        +'.lp-site-footer a:hover{color:#FF6B35}'
        +'.lp-site-footer .sep{opacity:.25;margin:0 2px}'
        +'.lp-site-footer .copy{display:block;margin-top:6px;opacity:.6}';
    document.head.appendChild(style);

    var f=document.createElement('footer');
    f.className='lp-site-footer';
    f.innerHTML=
        '<a href="/">Home</a><span class="sep">·</span>'
        +'<a href="/about/">About</a><span class="sep">·</span>'
        +'<a href="/privacy/">Privacy</a><span class="sep">·</span>'
        +'<a href="/blog/">Blog</a><span class="sep">·</span>'
        +'<a href="mailto:luckyplz.contact@gmail.com">Contact</a>'
        +'<span class="copy">© 2026 Lucky Please · luckyplz.com</span>';
    document.body.appendChild(f);
})();
