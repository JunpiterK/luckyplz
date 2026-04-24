/* lpMultiplayer.js — shared multiplayer-session panel.

   A floating, draggable, translucent cyan panel that surfaces the
   current room to BOTH host and guest on every page. Its lifecycle
   is driven by events that lpRoom.js dispatches on window:

     window.dispatchEvent(new CustomEvent('lp-room-host-ready', {detail:{room}}))
     window.dispatchEvent(new CustomEvent('lp-room-guest-ready', {detail:{guest}}))
     window.dispatchEvent(new CustomEvent('lp-room-closed', {detail:{mode}}))

   Design priorities (same bar as lpHostCtl — paid-service quality):
     - Idempotent: safe to load twice, safe to remount on every page.
     - Zero coupling to any specific game page — pure consumer of
       lpRoom's API surface (room.guests(), guest.on('host:guests')).
     - Survives hard navigations via sessionStorage (position + view)
       and localStorage (last-room pointer for rejoin UX — used by a
       later phase).
     - Stacking-safe: z-index 9050 sits ABOVE the legacy status pill
       (9000) but BELOW lpHostCtl pause/end overlays (9100+), so
       critical host actions always win clicks.

   Phase 1 scope: panel shell + live roster + leave/close actions.
   Game-switcher and recent-room rejoin arrive in later phases. */

(function(){
  'use strict';
  if(window.LpMultiplayer)return;// idempotent

  var SS_STATE='lp_mp_panel_state';// {view, pos:{x,y}}
  var current=null;// { mode, api, panel, cleanup[] }

  /* Game list for the host-side switcher. Order follows the home-page
     priority (룰렛·사다리 먼저). `resumable:false` games cannot be
     silently rehydrated by `LpRoom.tryResumeHost` today (quiz seeds
     questions + lobby flow via button clicks), so they're shown
     greyed-out until their page grows a resume path. */
  var GAMES=[
    {id:'roulette',  label:'룰렛',    emoji:'🎯', path:'/games/roulette/',  resumable:true },
    {id:'ladder',    label:'사다리',  emoji:'🪜', path:'/games/ladder/',    resumable:true },
    {id:'team',      label:'팀뽑기',  emoji:'👥', path:'/games/team/',      resumable:true },
    {id:'lotto',     label:'로또',    emoji:'🎰', path:'/games/lotto/',     resumable:true },
    {id:'bingo',     label:'빙고',    emoji:'🎱', path:'/games/bingo/',     resumable:true },
    {id:'car-racing',label:'레이싱',  emoji:'🏎️', path:'/games/car-racing/',resumable:true },
    {id:'quiz',      label:'퀴즈',    emoji:'🎓', path:'/games/quiz/',      resumable:false}
  ];

  /* ---------- styles ---------- */
  var CSS=[
    '.lp-mp-panel{position:fixed;z-index:9050;width:340px;max-width:calc(100vw - 24px);',
    '  background:linear-gradient(140deg,rgba(8,22,40,.62),rgba(12,30,52,.50));',
    '  backdrop-filter:blur(16px) saturate(140%);-webkit-backdrop-filter:blur(16px) saturate(140%);',
    '  border:1px solid rgba(79,195,247,.55);border-radius:14px;',
    '  box-shadow:0 10px 38px rgba(0,140,230,.28),inset 0 0 0 1px rgba(79,195,247,.12);',
    '  color:#E1F5FE;font:500 13.5px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;',
    '  overflow:hidden;transition:width .18s ease,max-height .18s ease;opacity:0;transform:translateY(-6px);',
    '  animation:lpMpIn .22s ease forwards}',
    '@keyframes lpMpIn{to{opacity:1;transform:translateY(0)}}',
    '.lp-mp-panel[data-view="collapsed"] .lp-mp-body{display:none}',
    '.lp-mp-panel[data-view="expanded"]{width:min(720px,calc(100vw - 24px))}',

    '.lp-mp-titlebar{display:flex;align-items:center;gap:8px;padding:10px 12px;',
    '  background:linear-gradient(180deg,rgba(79,195,247,.26),rgba(41,182,246,.08));',
    '  border-bottom:1px solid rgba(79,195,247,.35);cursor:grab;user-select:none;',
    '  -webkit-user-select:none;touch-action:none}',
    '.lp-mp-titlebar:active{cursor:grabbing}',
    '.lp-mp-icon{font-size:15px;filter:drop-shadow(0 0 6px rgba(79,195,247,.55))}',
    '.lp-mp-title{color:#4FC3F7;font-weight:800;letter-spacing:.4px;font-size:12px;text-transform:uppercase;',
    '  text-shadow:0 0 10px rgba(79,195,247,.4)}',
    '.lp-mp-code{font-family:"SF Mono",Menlo,ui-monospace,monospace;color:#B3E5FC;',
    '  background:rgba(79,195,247,.18);border:1px solid rgba(79,195,247,.4);border-radius:6px;',
    '  padding:2px 8px;font-size:11.5px;letter-spacing:.5px}',
    '.lp-mp-actions{margin-left:auto;display:flex;gap:4px}',
    '.lp-mp-actions button{background:transparent;border:1px solid rgba(79,195,247,.35);color:#B3E5FC;',
    '  width:26px;height:26px;border-radius:6px;cursor:pointer;font-size:13px;line-height:1;padding:0;',
    '  display:inline-flex;align-items:center;justify-content:center;transition:all .15s ease}',
    '.lp-mp-actions button:hover{background:rgba(79,195,247,.22);color:#E1F5FE;border-color:#4FC3F7}',

    '.lp-mp-body{padding:12px 14px 14px;display:flex;flex-direction:column;gap:10px;',
    '  max-height:min(60vh,500px);overflow-y:auto;overscroll-behavior:contain}',
    '.lp-mp-panel[data-view="expanded"] .lp-mp-body{max-height:min(72vh,580px)}',

    '.lp-mp-row{display:flex;align-items:center;gap:8px;font-size:13px;color:#B3E5FC}',
    '.lp-mp-row strong{color:#E1F5FE;font-weight:700}',
    '.lp-mp-dot{width:8px;height:8px;border-radius:50%;background:#4FC3F7;',
    '  box-shadow:0 0 8px #4FC3F7;animation:lpMpPulse 2s infinite}',
    '@keyframes lpMpPulse{0%,100%{opacity:1}50%{opacity:.35}}',

    '.lp-mp-sec-label{font-size:10.5px;color:#81D4FA;text-transform:uppercase;letter-spacing:.6px;',
    '  margin-bottom:6px;display:flex;justify-content:space-between;align-items:baseline}',
    '.lp-mp-sec-label b{color:#E1F5FE;font-size:12px;font-weight:700;letter-spacing:.2px}',
    '.lp-mp-sec{border-top:1px solid rgba(79,195,247,.18);padding-top:10px}',
    '.lp-mp-guest-list{display:flex;flex-wrap:wrap;gap:6px}',
    '.lp-mp-chip{background:rgba(79,195,247,.14);border:1px solid rgba(79,195,247,.35);',
    '  border-radius:999px;padding:3px 10px;font-size:12px;color:#E1F5FE;white-space:nowrap}',
    '.lp-mp-chip[data-self="1"]{background:rgba(79,195,247,.32);border-color:#4FC3F7;font-weight:700}',
    '.lp-mp-chip[data-host="1"]{background:rgba(255,213,79,.2);border-color:#FFD54F;color:#FFF8E1}',
    '.lp-mp-empty{color:#81D4FA;font-size:12px;font-style:italic;opacity:.7}',

    '.lp-mp-switcher-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}',
    '.lp-mp-sw-btn{background:rgba(79,195,247,.12);border:1px solid rgba(79,195,247,.3);',
    '  color:#E1F5FE;border-radius:10px;padding:9px 4px 7px;font-size:11.5px;font-weight:600;',
    '  cursor:pointer;transition:all .15s ease;display:flex;flex-direction:column;',
    '  align-items:center;gap:3px;line-height:1.1}',
    '.lp-mp-sw-btn:hover:not([disabled]){background:rgba(79,195,247,.28);border-color:#4FC3F7;',
    '  box-shadow:0 0 10px rgba(79,195,247,.3)}',
    '.lp-mp-sw-btn[data-current="1"]{background:rgba(79,195,247,.38);border-color:#4FC3F7;',
    '  cursor:default;opacity:.85;position:relative}',
    '.lp-mp-sw-btn[data-current="1"]::after{content:"●";position:absolute;top:2px;right:5px;',
    '  font-size:7px;color:#4FC3F7}',
    '.lp-mp-sw-btn[disabled]:not([data-current]){opacity:.35;cursor:not-allowed}',
    '.lp-mp-sw-btn .lp-mp-sw-emoji{font-size:20px;line-height:1}',
    '.lp-mp-sw-btn.lp-mp-transiting{background:rgba(79,195,247,.45);border-color:#4FC3F7;',
    '  box-shadow:0 0 14px rgba(79,195,247,.55);animation:lpMpPulse 1.1s infinite}',

    '.lp-mp-footer{border-top:1px solid rgba(79,195,247,.18);padding-top:10px;',
    '  display:flex;gap:8px;flex-wrap:wrap}',
    '.lp-mp-footer button{flex:1 1 auto;min-width:96px;',
    '  background:rgba(79,195,247,.18);border:1px solid rgba(79,195,247,.4);color:#E1F5FE;',
    '  border-radius:8px;padding:8px 12px;font-size:13px;font-weight:600;cursor:pointer;',
    '  transition:all .15s ease}',
    '.lp-mp-footer button:hover{background:rgba(79,195,247,.3);border-color:#4FC3F7;',
    '  box-shadow:0 0 12px rgba(79,195,247,.3)}',
    '.lp-mp-footer .lp-mp-danger{background:rgba(220,70,70,.15);border-color:rgba(220,80,80,.4);color:#FFCDD2}',
    '.lp-mp-footer .lp-mp-danger:hover{background:rgba(220,70,70,.3);border-color:rgba(255,110,110,.7);color:#fff;',
    '  box-shadow:0 0 12px rgba(255,100,100,.3)}',

    /* Mobile: bottom docking, no drag. */
    '@media (max-width:640px){.lp-mp-panel{left:10px!important;right:10px!important;',
    '  top:auto!important;bottom:10px;width:auto!important;max-width:none}',
    '  .lp-mp-titlebar{cursor:default}',
    '  .lp-mp-panel[data-view="expanded"]{top:10px!important;bottom:10px!important;',
    '    left:8px!important;right:8px!important;max-height:none}}',
    ''
  ].join('\n');

  function injectStyles(){
    if(document.getElementById('lp-mp-style'))return;
    var s=document.createElement('style');
    s.id='lp-mp-style';
    s.textContent=CSS;
    document.head.appendChild(s);
  }

  /* ---------- state persistence ---------- */
  function readState(){
    try{return JSON.parse(sessionStorage.getItem(SS_STATE)||'{}')}catch(_){return{}}
  }
  function writeState(patch){
    try{sessionStorage.setItem(SS_STATE,JSON.stringify(Object.assign({},readState(),patch)))}catch(_){}
  }

  /* ---------- helpers ---------- */
  function esc(s){
    return String(s==null?'':s).replace(/[&<>"']/g,function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }
  function clampPos(x,y,w,h){
    var vw=window.innerWidth,vh=window.innerHeight;
    w=w||340;h=h||44;
    return{
      x:Math.max(8,Math.min(vw-Math.min(w,220),x)),
      y:Math.max(8,Math.min(vh-h-8,y))
    };
  }
  function defaultPos(){
    if(window.innerWidth<=640)return null;// CSS handles mobile
    return{x:window.innerWidth-360,y:82};// right-ish, below the status pill
  }

  /* ---------- drag (desktop) ---------- */
  function enableDrag(panel){
    if(window.innerWidth<=640)return;
    var bar=panel.querySelector('.lp-mp-titlebar');
    if(!bar)return;
    var dragging=false,sx=0,sy=0,ox=0,oy=0;
    function onDown(e){
      if(e.target.closest('button'))return;
      var pt=e.touches?e.touches[0]:e;
      dragging=true;sx=pt.clientX;sy=pt.clientY;
      var r=panel.getBoundingClientRect();ox=r.left;oy=r.top;
      if(e.preventDefault)e.preventDefault();
    }
    function onMove(e){
      if(!dragging)return;
      var pt=e.touches?e.touches[0]:e;
      var r=panel.getBoundingClientRect();
      var pos=clampPos(ox+(pt.clientX-sx),oy+(pt.clientY-sy),r.width,r.height);
      panel.style.left=pos.x+'px';panel.style.top=pos.y+'px';
    }
    function onUp(){
      if(!dragging)return;
      dragging=false;
      var r=panel.getBoundingClientRect();
      writeState({pos:{x:r.left,y:r.top}});
    }
    bar.addEventListener('mousedown',onDown);
    window.addEventListener('mousemove',onMove);
    window.addEventListener('mouseup',onUp);
    bar.addEventListener('touchstart',onDown,{passive:false});
    window.addEventListener('touchmove',onMove,{passive:true});
    window.addEventListener('touchend',onUp);
  }

  /* ---------- shell ---------- */
  function buildShell(mode){
    var prev=document.getElementById('lpMpPanel');
    if(prev)prev.remove();

    injectStyles();
    var p=document.createElement('div');
    p.id='lpMpPanel';
    p.className='lp-mp-panel';
    p.setAttribute('data-mode',mode);
    var st=readState();
    p.setAttribute('data-view',st.view||'normal');

    var pos=st.pos||defaultPos();
    if(pos){p.style.left=pos.x+'px';p.style.top=pos.y+'px'}

    p.innerHTML=
      '<div class="lp-mp-titlebar">'
      +'<span class="lp-mp-icon">🌐</span>'
      +'<span class="lp-mp-title">멀티플레이</span>'
      +'<span class="lp-mp-code"></span>'
      +'<div class="lp-mp-actions">'
        +'<button class="lp-mp-btn-min" title="접기" aria-label="접기">–</button>'
        +'<button class="lp-mp-btn-max" title="전체화면" aria-label="전체화면">▢</button>'
      +'</div>'
      +'</div>'
      +'<div class="lp-mp-body">'
        +'<div class="lp-mp-row lp-mp-host-row"></div>'
        +'<div class="lp-mp-sec lp-mp-guests-sec"></div>'
        +'<div class="lp-mp-sec lp-mp-switcher-sec" hidden></div>'
        +'<div class="lp-mp-sec lp-mp-footer"></div>'
      +'</div>';

    document.body.appendChild(p);

    /* Clamp stored position to the new viewport on every mount — the
       user may have resized, rotated, or moved from desktop to mobile
       between sessions, which would otherwise leave the panel stuck
       off-screen. */
    if(pos){
      var r=p.getBoundingClientRect();
      var c=clampPos(pos.x,pos.y,r.width,r.height);
      if(c.x!==pos.x||c.y!==pos.y){p.style.left=c.x+'px';p.style.top=c.y+'px'}
    }

    p.querySelector('.lp-mp-btn-min').onclick=function(){
      var cur=p.getAttribute('data-view');
      var next=cur==='collapsed'?'normal':'collapsed';
      p.setAttribute('data-view',next);writeState({view:next});
    };
    p.querySelector('.lp-mp-btn-max').onclick=function(){
      var cur=p.getAttribute('data-view');
      var next=cur==='expanded'?'normal':'expanded';
      p.setAttribute('data-view',next);writeState({view:next});
    };

    enableDrag(p);
    return p;
  }

  /* ---------- host mount ---------- */
  function mountHost(room){
    unmount();
    var panel=buildShell('host');
    var hostAuthedName=null;

    /* Host-only game switcher. Clicking a non-current, resumable game
       calls room.transferTo(path) which broadcasts host:navigate to
       guests + persists lp_hostTransit so the next page auto-resumes
       this same room (identical code+pin). Guests follow automatically. */
    function switchGame(path,btn){
      if(!room||typeof room.transferTo!=='function')return;
      /* Lock the room before jumping so no stale join requests race the
         navigation — arriving guests on the NEW page can still join via
         tryResumeHost's unlock path, but mid-transit duplicates are
         suppressed. */
      try{if(room.lock&&!room.isLocked())room.lock()}catch(_){}
      if(btn)btn.classList.add('lp-mp-transiting');
      try{room.transferTo(path)}catch(_){}
    }

    function renderSwitcher(){
      var sec=panel.querySelector('.lp-mp-switcher-sec');
      if(!sec)return;
      var currentId=room.gameId||'';
      var html=GAMES.map(function(g){
        var isCurrent=(currentId===g.id);
        var disabled=isCurrent||!g.resumable;
        var attrs=(isCurrent?' data-current="1"':'')+(disabled?' disabled':'');
        return '<button type="button" class="lp-mp-sw-btn" data-path="'+g.path+'" data-id="'+g.id+'"'+attrs+'>'
          +'<span class="lp-mp-sw-emoji">'+g.emoji+'</span>'
          +'<span>'+esc(g.label)+'</span>'
        +'</button>';
      }).join('');
      sec.hidden=false;
      sec.innerHTML=
        '<div class="lp-mp-sec-label"><span>게임 전환</span><b>호스트 전용</b></div>'
        +'<div class="lp-mp-switcher-grid">'+html+'</div>';
      Array.prototype.forEach.call(sec.querySelectorAll('.lp-mp-sw-btn'),function(btn){
        if(btn.disabled)return;
        btn.onclick=function(){switchGame(btn.getAttribute('data-path'),btn)};
      });
    }

    function render(){
      var code=room.code||'';
      var hn=hostAuthedName||room.hostName||'Host';
      var list=(typeof room.guests==='function')?room.guests():[];

      panel.querySelector('.lp-mp-code').textContent=code;
      panel.querySelector('.lp-mp-host-row').innerHTML=
        '<span class="lp-mp-dot"></span>'
        +'<span>방장 <strong>'+esc(hn)+'</strong> · 나</span>';

      var chips=list.map(function(g){
        return '<span class="lp-mp-chip">'+esc(g.nickname||'Guest')+'</span>';
      }).join('');
      panel.querySelector('.lp-mp-guests-sec').innerHTML=
        '<div class="lp-mp-sec-label"><span>참여자</span><b>'+list.length+'명</b></div>'
        +(list.length?'<div class="lp-mp-guest-list">'+chips+'</div>'
                     :'<div class="lp-mp-empty">아직 참여자 없음 — 링크를 공유해 보세요</div>');

      renderSwitcher();

      panel.querySelector('.lp-mp-footer').innerHTML=
        '<button class="lp-mp-copy">🔗 링크 복사</button>'
        +'<button class="lp-mp-danger lp-mp-end">방 닫기</button>';

      panel.querySelector('.lp-mp-copy').onclick=function(){
        var btn=this;var url='';
        try{url=(typeof room.shareUrl==='function')?room.shareUrl():(location.origin+'/?room='+code)}
        catch(_){url=location.origin+'/?room='+code}
        try{navigator.clipboard.writeText(url);}catch(_){}
        var orig=btn.textContent;btn.textContent='✓ 복사됨';
        setTimeout(function(){btn.textContent=orig},1400);
      };
      panel.querySelector('.lp-mp-end').onclick=function(){
        if(!confirm('방을 닫으시겠어요?\n모든 게스트 연결이 끊깁니다.'))return;
        try{room.close&&room.close()}catch(_){}
        unmount();
      };
    }

    render();
    try{room.onGuestJoin&&room.onGuestJoin(render)}catch(_){}
    try{room.onGuestLeave&&room.onGuestLeave(render)}catch(_){}

    current={mode:'host',api:room,panel:panel};
  }

  /* ---------- guest mount ---------- */
  function mountGuest(g){
    unmount();
    var panel=buildShell('guest');
    var roster=[];
    var hostAuthedName=g.hostName||null;

    function render(){
      var code=g.code||'';
      panel.querySelector('.lp-mp-code').textContent=code;
      panel.querySelector('.lp-mp-host-row').innerHTML=
        '<span class="lp-mp-dot"></span>'
        +'<span>방장 <strong>'+esc(hostAuthedName||'Host')+'</strong></span>';

      var chips=roster.map(function(p){
        var self=(p.id===g.gid)?' data-self="1"':'';
        return '<span class="lp-mp-chip"'+self+'>'+esc(p.nickname||'Guest')+'</span>';
      }).join('');
      panel.querySelector('.lp-mp-guests-sec').innerHTML=
        '<div class="lp-mp-sec-label"><span>참여자</span><b>'+roster.length+'명</b></div>'
        +(roster.length?'<div class="lp-mp-guest-list">'+chips+'</div>'
                       :'<div class="lp-mp-empty">대기 중…</div>');

      panel.querySelector('.lp-mp-footer').innerHTML=
        '<button class="lp-mp-danger lp-mp-leave">나가기</button>';
      panel.querySelector('.lp-mp-leave').onclick=function(){
        if(!confirm('방에서 나가시겠어요?'))return;
        try{g.close&&g.close()}catch(_){}
        unmount();
      };
    }

    render();

    /* host:guests carries the canonical roster. Some hosts re-broadcast
       it on every join/leave, so this is our authoritative source. */
    try{
      g.on&&g.on('host:guests',function(p){
        if(p&&Array.isArray(p.guests)){roster=p.guests;render()}
      });
      g.on&&g.on('host:config',function(p){
        if(p&&p.hostName){hostAuthedName=p.hostName;render()}
      });
      g.on&&g.on('host:snapshot',function(p){
        if(p&&p.hostName){hostAuthedName=p.hostName;render()}
      });
    }catch(_){}

    current={mode:'guest',api:g,panel:panel};
  }

  /* ---------- unmount ---------- */
  function unmount(){
    if(current&&current.panel&&current.panel.parentNode){
      try{current.panel.remove()}catch(_){}
    }
    current=null;
  }

  /* ---------- event wiring ---------- */
  function onHostReady(e){
    var room=e&&e.detail&&e.detail.room;
    if(room)mountHost(room);
  }
  function onGuestReady(e){
    var g=e&&e.detail&&e.detail.guest;
    if(g)mountGuest(g);
  }
  function onRoomClosed(){unmount()}

  window.addEventListener('lp-room-host-ready',onHostReady);
  window.addEventListener('lp-room-guest-ready',onGuestReady);
  window.addEventListener('lp-room-closed',onRoomClosed);

  /* Re-clamp on resize/orientation so the panel never ends up off-screen. */
  window.addEventListener('resize',function(){
    if(!current||!current.panel)return;
    var p=current.panel;
    if(window.innerWidth<=640){
      p.style.left='';p.style.top='';
      return;
    }
    var r=p.getBoundingClientRect();
    var c=clampPos(r.left,r.top,r.width,r.height);
    p.style.left=c.x+'px';p.style.top=c.y+'px';
  });

  window.LpMultiplayer={
    mountHost:mountHost,
    mountGuest:mountGuest,
    unmount:unmount,
    _current:function(){return current}
  };
})();
