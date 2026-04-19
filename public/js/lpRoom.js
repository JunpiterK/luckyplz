/*
  Lucky Please — shared online room (host broadcasts, guests watch)
  -----------------------------------------------------------------
  Prevents single-device tampering on games that rely on trust
  (who pays coffee? who lost?). Host creates a room with a 4-digit
  PIN, shares the link, guests join with PIN + nickname and watch
  the host's screen live.

  Transport: Supabase Realtime broadcast channels — ephemeral, no DB
  writes, free-tier-friendly. Channel per room: `lp-room-<CODE>`.

  Trust model: password verified by host on join request. The channel
  itself is public (anyone who knows the code can subscribe), but only
  guests who complete the handshake appear in the host's roster and
  receive game state replays.

  Per-game integration:
    const room = await window.LpRoom.hostCreate({gameId:'roulette'});
    room.onGuestJoin(g => ...);
    room.broadcast('host:result', {winner:'Alice'});
    ...
    const guest = await window.LpRoom.guestJoin({code, pin, nickname, gameId});
    guest.on('host:result', payload => ...);
*/
(function(){
    const CODE_ALPHABET='23456789ABCDEFGHJKMNPQRSTVWXYZ'; // no 0/O/1/I/L
    function genCode(){
        let s='';
        for(let i=0;i<6;i++)s+=CODE_ALPHABET[Math.floor(Math.random()*CODE_ALPHABET.length)];
        return s;
    }
    function channelName(code){return 'lp-room-'+String(code).toUpperCase()}

    function waitForSupabase(timeout){
        return new Promise(function(resolve,reject){
            if(window.supabase&&typeof window.getSupabase==='function')return resolve(window.getSupabase());
            const t0=Date.now();
            const iv=setInterval(function(){
                if(window.supabase&&typeof window.getSupabase==='function'){
                    clearInterval(iv);
                    resolve(window.getSupabase());
                }else if(Date.now()-t0>(timeout||5000)){
                    clearInterval(iv);
                    reject(new Error('Supabase not loaded'));
                }
            },100);
        });
    }

    function shortId(){return Math.random().toString(36).slice(2,10)}

    /* ============ HOST ============ */
    async function hostCreate(opts){
        opts=opts||{};
        const gameId=opts.gameId||'unknown';
        const pin=String(opts.pin||'').padStart(4,'0');
        const hostName=opts.hostName||'Host';
        const sb=await waitForSupabase();
        const code=opts.code||genCode();
        const chan=sb.channel(channelName(code),{config:{broadcast:{self:false,ack:false},presence:{key:'h-'+shortId()}}});

        const guests=new Map(); /* guestId -> {nickname, joinedAt} */
        const guestJoinCbs=[];
        const guestLeaveCbs=[];
        let subscribed=false;

        chan.on('broadcast',{event:'guest:join_request'},function(msg){
            const p=msg.payload||{};
            if(!p||!p.gid)return;
            if(p.pin!==pin){
                /* wrong PIN */
                chan.send({type:'broadcast',event:'host:join_ack',payload:{gid:p.gid,ok:false,reason:'bad_pin'}});
                return;
            }
            if(p.gameId&&p.gameId!==gameId){
                chan.send({type:'broadcast',event:'host:join_ack',payload:{gid:p.gid,ok:false,reason:'wrong_game'}});
                return;
            }
            guests.set(p.gid,{nickname:p.nickname||'Guest',joinedAt:Date.now()});
            chan.send({type:'broadcast',event:'host:join_ack',payload:{gid:p.gid,ok:true,hostName:hostName,gameId:gameId}});
            guestJoinCbs.forEach(function(cb){try{cb({id:p.gid,nickname:p.nickname||'Guest'})}catch(e){}});
            /* replay last snapshot so the newcomer catches up */
            if(currentSnapshot){
                chan.send({type:'broadcast',event:'host:snapshot',payload:Object.assign({gid:p.gid},currentSnapshot)});
            }
        });

        chan.on('broadcast',{event:'guest:leave'},function(msg){
            const p=msg.payload||{};
            if(!p.gid||!guests.has(p.gid))return;
            const info=guests.get(p.gid);
            guests.delete(p.gid);
            guestLeaveCbs.forEach(function(cb){try{cb({id:p.gid,nickname:info.nickname})}catch(e){}});
        });

        let currentSnapshot=null;

        await new Promise(function(resolve,reject){
            const to=setTimeout(function(){reject(new Error('subscribe timeout'))},10000);
            chan.subscribe(function(status){
                if(status==='SUBSCRIBED'){
                    subscribed=true;
                    clearTimeout(to);
                    resolve();
                }
            });
        });

        return {
            code:code,
            gameId:gameId,
            pin:pin,
            hostName:hostName,
            guests:function(){return Array.from(guests.entries()).map(function(e){return{id:e[0],nickname:e[1].nickname,joinedAt:e[1].joinedAt}})},
            broadcast:function(event,payload){
                if(!subscribed)return false;
                chan.send({type:'broadcast',event:event,payload:payload||{}});
                return true;
            },
            snapshot:function(payload){
                /* Host tells lpRoom "this is the current game state". New
                   joiners will receive it as a host:snapshot so they can
                   render immediately without waiting for the next event. */
                currentSnapshot=Object.assign({},payload||{});
            },
            onGuestJoin:function(cb){if(typeof cb==='function')guestJoinCbs.push(cb)},
            onGuestLeave:function(cb){if(typeof cb==='function')guestLeaveCbs.push(cb)},
            close:function(){
                try{chan.send({type:'broadcast',event:'host:close',payload:{}})}catch(e){}
                try{sb.removeChannel(chan)}catch(e){}
            },
            shareUrl:function(base){
                const root=(base||location.origin+location.pathname).replace(/\?.*$/,'').replace(/#.*$/,'');
                return root+'?room='+code;
            }
        };
    }

    /* ============ GUEST ============ */
    /* Known host→guest events. We register an explicit chan.on() per event
       rather than {event:'*'} because wildcard broadcast subscriptions
       have been historically flaky across supabase-js versions (silently
       dropped messages in the wild). Add any new host event name here
       when a game starts using it. */
    const KNOWN_HOST_EVENTS=[
        'host:join_ack','host:snapshot','host:close',
        'host:config','host:state','host:start','host:spin_start',
        'host:tick','host:stop','host:result','host:reset','host:action'
    ];

    async function guestJoin(opts){
        opts=opts||{};
        const code=String(opts.code||'').trim().toUpperCase();
        const pin=String(opts.pin||'').padStart(4,'0');
        const nickname=(opts.nickname||'Guest').trim().slice(0,20)||'Guest';
        const gameId=opts.gameId||null;
        const sb=await waitForSupabase();
        const chan=sb.channel(channelName(code),{config:{broadcast:{self:false,ack:false},presence:{key:'g-'+shortId()}}});
        const gid=shortId()+'-'+shortId();
        const listeners={}; /* event → [fn] */
        let accepted=false;
        /* Event cache for late listeners. The host broadcasts host:snapshot
           (and the initial host:config) almost immediately after we send
           guest:join_request — often before the game-code callback has a
           chance to register its g.on(...) handlers. Without caching,
           those payloads would be dispatched to an empty listener array
           and lost, leaving the guest stuck on default setup. We store the
           latest payload per state-like event and replay it synchronously
           from g.on() when the listener finally arrives. */
        const cache={};
        const STATEFUL=/^host:(snapshot|config|state|start|spin_start|result)$/;

        function dispatch(ev,p){
            if(ev==='host:join_ack'){
                if(p.gid!==gid)return; /* not for us */
                if(p.ok){
                    accepted=true;
                    emit('_accepted',{hostName:p.hostName,gameId:p.gameId});
                }else{
                    emit('_rejected',{reason:p.reason||'rejected'});
                }
                return;
            }
            /* Host:snapshot targeted replay to newly-joined guest */
            if(ev==='host:snapshot'){
                if(p.gid&&p.gid!==gid)return;
                cache['host:snapshot']=p;
                emit('host:snapshot',p);
                return;
            }
            /* Regular host events after acceptance */
            if(accepted){
                if(STATEFUL.test(ev))cache[ev]=p;
                emit(ev,p);
            }
        }

        KNOWN_HOST_EVENTS.forEach(function(evName){
            chan.on('broadcast',{event:evName},function(msg){
                dispatch(msg.event||evName,msg.payload||{});
            });
        });

        function emit(event,payload){
            (listeners[event]||[]).forEach(function(fn){try{fn(payload)}catch(e){}});
            (listeners['*']||[]).forEach(function(fn){try{fn(event,payload)}catch(e){}});
        }

        await new Promise(function(resolve,reject){
            const to=setTimeout(function(){reject(new Error('subscribe timeout'))},10000);
            chan.subscribe(function(status){
                if(status==='SUBSCRIBED'){clearTimeout(to);resolve()}
            });
        });

        /* Send join request, wait for ack (or timeout) */
        const result=await new Promise(function(resolve){
            const timer=setTimeout(function(){resolve({ok:false,error:'host_unreachable'})},8000);
            listeners._accepted=[function(d){clearTimeout(timer);resolve({ok:true,hostName:d.hostName,gameId:d.gameId})}];
            listeners._rejected=[function(d){clearTimeout(timer);resolve({ok:false,error:d.reason})}];
            chan.send({type:'broadcast',event:'guest:join_request',payload:{gid:gid,pin:pin,nickname:nickname,gameId:gameId}});
        });

        if(!result.ok){
            try{sb.removeChannel(chan)}catch(e){}
            return {ok:false,error:result.error};
        }

        return {
            ok:true,
            code:code,
            gid:gid,
            hostName:result.hostName,
            gameId:result.gameId,
            on:function(event,cb){
                if(!listeners[event])listeners[event]=[];
                listeners[event].push(cb);
                /* Replay any cached payload synchronously. If the event
                   already fired during the join handshake (before the game
                   code had a chance to register this listener), the cache
                   still has it, so the listener won't miss the initial
                   state. host:config listeners also see the host:snapshot
                   payload since a snapshot is just a targeted-replay of
                   the current config. */
                if(cache[event]){
                    try{cb(cache[event])}catch(e){}
                }else if(event==='host:config'&&cache['host:snapshot']){
                    try{cb(cache['host:snapshot'])}catch(e){}
                }
            },
            close:function(){
                try{chan.send({type:'broadcast',event:'guest:leave',payload:{gid:gid}})}catch(e){}
                try{sb.removeChannel(chan)}catch(e){}
            }
        };
    }

    /* ============ UI MODALS ============ */
    function _t(ko,en){
        const lang=(localStorage.getItem('luckyplz_lang')||'en').toLowerCase().split('-')[0];
        return lang==='ko'?ko:en;
    }

    function injectStyles(){
        if(document.getElementById('lp-room-styles'))return;
        const s=document.createElement('style');
        s.id='lp-room-styles';
        s.textContent=
            '.lp-room-online-btn{display:inline-flex;align-items:center;gap:6px;padding:10px 18px;border-radius:12px;border:1.5px solid rgba(0,217,255,.4);background:rgba(0,217,255,.08);color:#00D9FF;font-family:"Noto Sans KR",sans-serif;font-weight:700;font-size:.86em;cursor:pointer;transition:background .2s,transform .15s;margin-left:8px}'
           +'.lp-room-online-btn:hover{background:rgba(0,217,255,.18);transform:translateY(-1px)}'
           +'.lp-room-backdrop{position:fixed;inset:0;background:rgba(5,5,15,.85);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);z-index:9500;display:flex;align-items:center;justify-content:center;padding:16px;font-family:"Noto Sans KR",sans-serif}'
           +'.lp-room-modal{background:linear-gradient(145deg,rgba(22,22,42,.98),rgba(14,14,28,.98));border:1px solid rgba(0,217,255,.25);border-radius:20px;padding:26px 24px;max-width:420px;width:100%;box-shadow:0 30px 80px rgba(0,0,0,.6);color:#fff;max-height:90vh;overflow-y:auto}'
           +'.lp-room-modal h3{font-family:"Orbitron","Noto Sans KR",sans-serif;font-size:1.15em;color:#00D9FF;margin:0 0 4px;letter-spacing:.02em}'
           +'.lp-room-modal .sub{font-size:.82em;color:rgba(255,255,255,.5);margin-bottom:18px;line-height:1.5}'
           +'.lp-room-modal label{display:block;font-size:.75em;color:rgba(255,255,255,.6);margin:10px 0 4px;letter-spacing:.05em;text-transform:uppercase;font-weight:700}'
           +'.lp-room-modal input{width:100%;padding:12px 14px;border-radius:10px;border:1.5px solid rgba(255,255,255,.12);background:rgba(255,255,255,.04);color:#fff;font-family:inherit;font-size:1em;box-sizing:border-box;transition:border-color .2s}'
           +'.lp-room-modal input:focus{outline:none;border-color:#00D9FF}'
           +'.lp-room-modal .pin-input{letter-spacing:8px;text-align:center;font-family:"Orbitron",monospace;font-size:1.35em;font-weight:700}'
           +'.lp-room-modal .row{display:flex;gap:10px;margin-top:18px}'
           +'.lp-room-modal .btn{flex:1;padding:12px 14px;border-radius:10px;border:0;font-family:inherit;font-weight:700;font-size:.95em;cursor:pointer;transition:all .18s}'
           +'.lp-room-modal .btn.primary{background:linear-gradient(135deg,#00D9FF,#0099CC);color:#001220}'
           +'.lp-room-modal .btn.primary:hover{filter:brightness(1.1)}'
           +'.lp-room-modal .btn.ghost{background:rgba(255,255,255,.06);color:rgba(255,255,255,.75);border:1px solid rgba(255,255,255,.1)}'
           +'.lp-room-modal .btn.ghost:hover{background:rgba(255,255,255,.12)}'
           +'.lp-room-code{font-family:"Orbitron","Noto Sans KR",sans-serif;font-size:2.2em;font-weight:900;letter-spacing:.12em;text-align:center;padding:16px;border-radius:14px;background:rgba(0,217,255,.08);border:1.5px dashed rgba(0,217,255,.35);color:#00D9FF;margin:10px 0 4px}'
           +'.lp-room-pin-display{font-family:"Orbitron",monospace;font-size:1.6em;letter-spacing:6px;text-align:center;color:#FFE66D;font-weight:700;padding:10px;margin:6px 0 12px}'
           +'.lp-room-share{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}'
           +'.lp-room-share button{flex:1;padding:9px 12px;border:0;border-radius:8px;background:rgba(255,255,255,.06);color:#fff;font-size:.82em;font-weight:700;cursor:pointer;font-family:inherit;transition:background .15s}'
           +'.lp-room-share button:hover{background:rgba(255,255,255,.14)}'
           +'.lp-room-error{color:#FF6B8B;font-size:.82em;margin-top:8px;text-align:center;min-height:1.2em}'
           +'.lp-room-guest-list{margin-top:14px;padding-top:14px;border-top:1px solid rgba(255,255,255,.08)}'
           +'.lp-room-guest-list .title{font-size:.72em;color:rgba(255,255,255,.45);letter-spacing:.12em;text-transform:uppercase;font-weight:700;margin-bottom:8px}'
           +'.lp-room-guest-list .pill{display:inline-block;padding:4px 10px;border-radius:999px;background:rgba(0,217,255,.12);color:#00D9FF;font-size:.78em;font-weight:600;margin:0 4px 4px 0}'
           +'.lp-room-guest-list .empty{font-size:.78em;color:rgba(255,255,255,.3);font-style:italic}'
           +'.lp-room-status{position:fixed;top:10px;left:50%;transform:translateX(-50%);background:rgba(0,217,255,.12);border:1px solid rgba(0,217,255,.4);color:#00D9FF;padding:6px 14px;border-radius:999px;font-family:"Noto Sans KR",sans-serif;font-size:.78em;font-weight:700;z-index:9000;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);display:flex;align-items:center;gap:8px;max-width:92vw}'
           +'.lp-room-status .dot{width:8px;height:8px;border-radius:50%;background:#00D9FF;animation:lpRoomPulse 1.6s ease-in-out infinite}'
           +'@keyframes lpRoomPulse{0%,100%{opacity:.4}50%{opacity:1}}'
           +'.lp-room-status .x{margin-left:6px;cursor:pointer;opacity:.5;font-weight:700}'
           +'.lp-room-status .x:hover{opacity:1}'
           /* QR in share modal */
           +'.lp-room-qr-wrap{position:relative;margin:14px auto 6px;max-width:220px}'
           +'.lp-room-qr{width:100%;aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;border-radius:12px;overflow:hidden;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);min-height:220px}'
           +'.lp-room-qr-big{position:absolute;top:6px;right:6px;padding:5px 9px;border-radius:8px;border:0;background:rgba(0,0,0,.55);color:#fff;font-family:inherit;font-size:.72em;font-weight:700;cursor:pointer;backdrop-filter:blur(6px);transition:background .2s}'
           +'.lp-room-qr-big:hover{background:rgba(0,0,0,.8)}'
           /* Fullscreen QR overlay */
           +'.lp-room-qr-full{position:fixed;inset:0;background:rgba(5,5,15,.97);z-index:9800;display:flex;align-items:center;justify-content:center;flex-direction:column;padding:24px;font-family:"Noto Sans KR",sans-serif;color:#fff;animation:lpQrFadeIn .25s ease}'
           +'@keyframes lpQrFadeIn{from{opacity:0}to{opacity:1}}'
           +'.lp-room-qr-close{position:absolute;top:16px;right:20px;width:44px;height:44px;border-radius:50%;border:0;background:rgba(255,255,255,.08);color:#fff;font-size:1.5em;line-height:1;cursor:pointer;transition:background .2s}'
           +'.lp-room-qr-close:hover{background:rgba(255,255,255,.15)}'
           +'.lp-room-qr-inner{display:flex;flex-direction:column;align-items:center;gap:18px;max-width:560px;width:100%}'
           +'.lp-room-qr-label{font-family:"Orbitron","Noto Sans KR",sans-serif;font-size:1.2em;font-weight:700;color:#00D9FF;letter-spacing:.02em;text-align:center}'
           +'.lp-room-qr-big-canvas{width:min(75vmin,480px);height:min(75vmin,480px);display:flex;align-items:center;justify-content:center;background:#fff;border-radius:20px;padding:20px;box-shadow:0 30px 80px rgba(0,217,255,.25)}'
           +'.lp-room-qr-big-canvas img{width:100%;height:auto;max-width:100%;display:block}'
           +'.lp-room-qr-footer{text-align:center;width:100%}'
           +'.lp-room-qr-enter{font-size:.85em;color:rgba(255,255,255,.55);letter-spacing:.04em;margin-bottom:10px}'
           +'.lp-room-qr-codes{display:flex;flex-wrap:wrap;gap:10px 22px;justify-content:center;font-family:"Orbitron","Noto Sans KR",sans-serif;align-items:baseline}'
           +'.lp-room-qr-codes .lbl{font-size:.72em;color:rgba(255,255,255,.45);letter-spacing:.14em;font-weight:700;text-transform:uppercase}'
           +'.lp-room-qr-codes .val{font-size:1.9em;font-weight:900;letter-spacing:.1em;color:#fff}'
           +'.lp-room-qr-codes .val.pin{color:#FFE66D}'
           +'@media(max-width:500px){.lp-room-qr-codes .val{font-size:1.4em}.lp-room-qr-label{font-size:1em}}';
        document.head.appendChild(s);
    }

    function closeBackdrop(){
        const bd=document.getElementById('lpRoomBackdrop');
        if(bd)bd.remove();
    }

    function mountBackdrop(innerHtml){
        closeBackdrop();
        injectStyles();
        const bd=document.createElement('div');
        bd.id='lpRoomBackdrop';
        bd.className='lp-room-backdrop';
        bd.innerHTML='<div class="lp-room-modal">'+innerHtml+'</div>';
        document.body.appendChild(bd);
        return bd;
    }

    /* Host creation modal: asks for a 4-digit PIN, then switches to a
       share screen displaying the generated room code, the PIN, and a
       one-tap copy/share of the invite link. Calls onCreated(roomObj)
       when the host finishes and closes the modal. */
    function showHostModal(opts){
        opts=opts||{};
        const gameId=opts.gameId;
        const hostName=opts.hostName||'Host';
        const ko=_t(true,false);

        const step1=mountBackdrop(
            '<h3>'+_t('👥 같이 보기 방 만들기','👥 Create Watch-Together Room')+'</h3>'
           +'<div class="sub">'+_t('4자리 비밀번호를 설정하세요. 친구에게 알려줄 숫자입니다.','Set a 4-digit PIN. You\'ll share this with friends.')+'</div>'
           +'<label>'+_t('비밀번호 4자리','4-digit PIN')+'</label>'
           +'<input id="lpRoomPin" class="pin-input" type="tel" inputmode="numeric" maxlength="4" placeholder="0000" autocomplete="off">'
           +'<div class="lp-room-error" id="lpRoomErr"></div>'
           +'<div class="row">'
           +'<button class="btn ghost" id="lpRoomCancel">'+_t('취소','Cancel')+'</button>'
           +'<button class="btn primary" id="lpRoomConfirm">'+_t('방 만들기','Create')+'</button>'
           +'</div>'
        );
        const pinIn=document.getElementById('lpRoomPin');
        const err=document.getElementById('lpRoomErr');
        setTimeout(function(){pinIn.focus()},50);
        pinIn.addEventListener('input',function(){pinIn.value=pinIn.value.replace(/\D/g,'').slice(0,4)});
        pinIn.addEventListener('keydown',function(e){if(e.key==='Enter')doCreate()});
        document.getElementById('lpRoomCancel').addEventListener('click',function(){closeBackdrop();if(opts.onCancel)opts.onCancel()});

        async function doCreate(){
            const pin=pinIn.value;
            if(pin.length!==4){err.textContent=_t('4자리 숫자로 입력해주세요','Please enter 4 digits');return}
            err.textContent=_t('방 연결 중…','Connecting…');
            try{
                const room=await hostCreate({gameId:gameId,pin:pin,hostName:hostName});
                /* Fire onCreated as soon as the channel is live, before the
                   share modal shows. Games hook this to register their
                   snapshot provider and start live config broadcasting, so
                   any guest that joins via QR while the modal is still up
                   immediately sees the host's setup instead of defaults. */
                if(opts.onCreated)try{opts.onCreated(room)}catch(_){}
                showHostShare(room,opts);
            }catch(e){err.textContent=_t('연결 실패. 다시 시도해주세요','Connection failed. Try again')}
        }
        document.getElementById('lpRoomConfirm').addEventListener('click',doCreate);
    }

    /* QR library loader — lazy load on first host-share view.
       Using qrcode-generator (qrcode.js by Kazuhiko Arase): pure JS,
       ~12KB, no dependencies, hundreds of millions of deploys, renders
       into an <img> with data URL so there's no canvas permission prompt
       on mobile Safari. */
    function _loadQrLib(){
        if(window.qrcode)return Promise.resolve();
        if(window._lpQrPromise)return window._lpQrPromise;
        window._lpQrPromise=new Promise(function(resolve,reject){
            const s=document.createElement('script');
            s.src='https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js';
            s.onload=resolve;
            s.onerror=reject;
            document.head.appendChild(s);
        });
        return window._lpQrPromise;
    }
    function _renderQr(container,text,sizePx){
        _loadQrLib().then(function(){
            try{
                const qr=qrcode(0,'M'); /* type auto, error correction M (15%) */
                qr.addData(text);
                qr.make();
                const cell=Math.max(3,Math.floor(sizePx/(qr.getModuleCount()+4)));
                container.innerHTML=qr.createImgTag(cell,cell*2);
                const img=container.querySelector('img');
                if(img){img.alt='Room QR';img.style.cssText='display:block;width:100%;max-width:'+sizePx+'px;height:auto;border-radius:8px;background:#fff;padding:'+(cell*2)+'px;box-sizing:border-box'}
            }catch(e){container.innerHTML='<div style="color:rgba(255,255,255,.4);font-size:.75em">QR unavailable</div>'}
        }).catch(function(){container.innerHTML='<div style="color:rgba(255,255,255,.4);font-size:.75em">QR library failed</div>'});
    }

    function showHostShare(room,opts){
        opts=opts||{};
        const url=room.shareUrl();
        mountBackdrop(
            '<h3>'+_t('👥 방 생성 완료','👥 Room Created')+'</h3>'
           +'<div class="sub">'+_t('카메라로 QR을 찍거나 링크를 공유하세요. 4자리 비밀번호도 같이 알려줘야 합니다.','Scan the QR with a camera, or share the link. Don\'t forget to share the 4-digit PIN too.')+'</div>'
           +'<div class="lp-room-qr-wrap">'
           +  '<div class="lp-room-qr" id="lpRoomQr"></div>'
           +  '<button class="lp-room-qr-big" id="lpRoomQrBig" type="button" title="Big QR">⛶ '+_t('큰 QR 보기','Fullscreen')+'</button>'
           +'</div>'
           +'<label>'+_t('방 코드','Room Code')+'</label>'
           +'<div class="lp-room-code">'+room.code+'</div>'
           +'<label>'+_t('비밀번호','PIN')+'</label>'
           +'<div class="lp-room-pin-display">'+room.pin.split('').join(' ')+'</div>'
           +'<label>'+_t('공유 링크','Invite Link')+'</label>'
           +'<input id="lpRoomUrl" readonly value="'+url+'" style="font-size:.82em">'
           +'<div class="lp-room-share">'
           +'<button id="lpRoomCopy">📋 '+_t('링크 복사','Copy Link')+'</button>'
           +'<button id="lpRoomKakao">💬 '+_t('카톡/메신저','Kakao/Chat')+'</button>'
           +'</div>'
           +'<div class="lp-room-guest-list" id="lpRoomGuests"><div class="title">'+_t('접속자','Guests')+'</div><div class="empty" id="lpRoomGuestsBody">'+_t('아직 아무도 없음 · 친구 기다리는 중…','No one yet — waiting for friends…')+'</div></div>'
           +'<div class="row">'
           +'<button class="btn ghost" id="lpRoomEnd">'+_t('방 닫기','End Room')+'</button>'
           +'<button class="btn primary" id="lpRoomStart">'+_t('시작!','Start!')+'</button>'
           +'</div>'
        );
        _renderQr(document.getElementById('lpRoomQr'),url,220);
        const qrBigBtn=document.getElementById('lpRoomQrBig');
        if(qrBigBtn)qrBigBtn.addEventListener('click',function(){showQrFullscreen(room,url)});

        function renderGuests(){
            const body=document.getElementById('lpRoomGuestsBody');
            if(!body)return;
            const gs=room.guests();
            if(!gs.length){
                body.className='empty';
                body.textContent=_t('아직 아무도 없음 · 친구 기다리는 중…','No one yet — waiting for friends…');
            }else{
                body.className='';
                body.innerHTML=gs.map(function(g){return '<span class="pill">'+escapeHtml(g.nickname)+'</span>'}).join('');
            }
        }
        room.onGuestJoin(renderGuests);
        room.onGuestLeave(renderGuests);
        renderGuests();

        const shareText=_t(
            '👥 Lucky Please 같이 보기\n방 코드: '+room.code+'\n비밀번호: '+room.pin+'\n'+url,
            '👥 Lucky Please Watch Together\nRoom: '+room.code+'\nPIN: '+room.pin+'\n'+url
        );

        document.getElementById('lpRoomCopy').addEventListener('click',function(){
            (navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(shareText):Promise.reject()).catch(function(){
                const ta=document.createElement('textarea');ta.value=shareText;document.body.appendChild(ta);ta.select();try{document.execCommand('copy')}catch(e){}document.body.removeChild(ta);
            });
            const btn=this;const orig=btn.textContent;btn.textContent='✅ '+_t('복사됨','Copied');setTimeout(function(){btn.textContent=orig},1500);
        });
        document.getElementById('lpRoomKakao').addEventListener('click',function(){
            if(window.LpShare&&window.LpShare.kakao){
                window.LpShare.kakao(shareText,url);
            }else if(navigator.share){
                navigator.share({title:document.title,text:shareText,url:url}).catch(function(){});
            }
        });
        document.getElementById('lpRoomEnd').addEventListener('click',function(){
            room.close();
            closeBackdrop();
            if(opts.onCancel)opts.onCancel();
        });
        document.getElementById('lpRoomStart').addEventListener('click',function(){
            closeBackdrop();
            showHostStatus(room);
            if(opts.onReady)opts.onReady(room);
        });
    }

    /* Fullscreen QR overlay — event hosts display this on a big screen /
       projector so attendees scan with their phone camera. Tap / ESC to
       close. Shows the room code + PIN underneath so audience can enter
       manually if they prefer. */
    function showQrFullscreen(room,url){
        injectStyles();
        const prev=document.getElementById('lpRoomBackdrop');
        if(prev)prev.remove();
        const overlay=document.createElement('div');
        overlay.id='lpRoomQrFull';
        overlay.className='lp-room-qr-full';
        const lang=(localStorage.getItem('luckyplz_lang')||'en').toLowerCase().split('-')[0];
        const scanLabel=lang==='ko'?'📷 카메라로 QR을 찍으세요':(lang==='ja'?'📷 QRをスキャン':(lang==='zh'?'📷 用相机扫描':'📷 Scan with your camera'));
        const enterLabel=lang==='ko'?'직접 입력':(lang==='ja'?'手動で入力':(lang==='zh'?'手动输入':'Or enter manually'));
        const closeLabel=lang==='ko'?'닫기':(lang==='ja'?'閉じる':(lang==='zh'?'关闭':'Close'));
        overlay.innerHTML=
            '<button class="lp-room-qr-close" id="lpRoomQrClose" aria-label="'+closeLabel+'">×</button>'
           +'<div class="lp-room-qr-inner">'
           +'  <div class="lp-room-qr-label">'+scanLabel+'</div>'
           +'  <div class="lp-room-qr-big-canvas" id="lpRoomQrBigCanvas"></div>'
           +'  <div class="lp-room-qr-footer">'
           +'    <div class="lp-room-qr-enter">'+enterLabel+'</div>'
           +'    <div class="lp-room-qr-codes"><span class="lbl">Room</span><span class="val">'+room.code+'</span><span class="lbl">PIN</span><span class="val pin">'+room.pin+'</span></div>'
           +'  </div>'
           +'</div>';
        document.body.appendChild(overlay);
        /* Render QR at big size — 400px target but lets CSS scale down */
        _renderQr(document.getElementById('lpRoomQrBigCanvas'),url,400);
        function close(){overlay.remove();document.removeEventListener('keydown',onKey);showHostShare(room,{})}
        function onKey(e){if(e.key==='Escape')close()}
        document.addEventListener('keydown',onKey);
        document.getElementById('lpRoomQrClose').addEventListener('click',close);
        overlay.addEventListener('click',function(e){if(e.target===overlay)close()});
    }

    function showHostStatus(room){
        closeBackdrop();
        injectStyles();
        let bar=document.getElementById('lpRoomStatus');
        if(bar)bar.remove();
        bar=document.createElement('div');
        bar.id='lpRoomStatus';
        bar.className='lp-room-status';
        function refresh(){
            const count=room.guests().length;
            const lang=(localStorage.getItem('luckyplz_lang')||'en').toLowerCase().split('-')[0];
            const lbl=lang==='ko'?`👥 ${room.code} · ${count}명 같이 보는중`:`👥 ${room.code} · ${count} watching`;
            bar.innerHTML='<span class="dot"></span><span>'+lbl+'</span><span class="x" id="lpRoomStatusX" title="'+(lang==='ko'?'방 닫기':'End room')+'">×</span>';
            const x=document.getElementById('lpRoomStatusX');
            if(x)x.addEventListener('click',function(){room.close();bar.remove()});
        }
        refresh();
        room.onGuestJoin(refresh);
        room.onGuestLeave(refresh);
        document.body.appendChild(bar);
    }

    function showGuestJoinModal(code,opts){
        opts=opts||{};
        const gameId=opts.gameId;
        mountBackdrop(
            '<h3>'+_t('👥 같이 보기 방 참가','👥 Join Watch-Together Room')+'</h3>'
           +'<div class="sub">'+_t('방장이 알려준 4자리 비밀번호와 닉네임을 입력하세요.','Enter the 4-digit PIN from the host and a nickname.')+'</div>'
           +'<label>'+_t('방 코드','Room Code')+'</label>'
           +'<div class="lp-room-code" style="font-size:1.4em">'+code.toUpperCase()+'</div>'
           +'<label>'+_t('닉네임','Nickname')+'</label>'
           +'<input id="lpGuestNick" maxlength="20" placeholder="'+_t('나','Your name')+'" autocomplete="off">'
           +'<label>'+_t('비밀번호 4자리','PIN')+'</label>'
           +'<input id="lpGuestPin" class="pin-input" type="tel" inputmode="numeric" maxlength="4" placeholder="0000" autocomplete="off">'
           +'<div class="lp-room-error" id="lpGuestErr"></div>'
           +'<div class="row">'
           +'<button class="btn ghost" id="lpGuestCancel">'+_t('취소','Cancel')+'</button>'
           +'<button class="btn primary" id="lpGuestJoin">'+_t('참가','Join')+'</button>'
           +'</div>'
        );
        const pin=document.getElementById('lpGuestPin');
        const nick=document.getElementById('lpGuestNick');
        const err=document.getElementById('lpGuestErr');
        const saved=localStorage.getItem('luckyplz_nick');if(saved)nick.value=saved;
        setTimeout(function(){(nick.value?pin:nick).focus()},50);
        pin.addEventListener('input',function(){pin.value=pin.value.replace(/\D/g,'').slice(0,4)});
        pin.addEventListener('keydown',function(e){if(e.key==='Enter')doJoin()});
        document.getElementById('lpGuestCancel').addEventListener('click',function(){
            closeBackdrop();
            if(opts.onCancel)opts.onCancel();
        });
        async function doJoin(){
            if(!nick.value.trim()){err.textContent=_t('닉네임을 입력해주세요','Enter a nickname');return}
            if(pin.value.length!==4){err.textContent=_t('4자리 숫자','4 digits');return}
            localStorage.setItem('luckyplz_nick',nick.value.trim());
            err.textContent=_t('방 연결 중…','Connecting…');
            const g=await guestJoin({code:code,pin:pin.value,nickname:nick.value,gameId:gameId});
            if(!g.ok){
                err.textContent=(g.error==='bad_pin')?_t('비밀번호가 틀렸어요','Wrong PIN')
                    :(g.error==='host_unreachable')?_t('방장이 없어요. 방 코드 확인.','Host not responding. Check the room code.')
                    :(g.error==='wrong_game')?_t('다른 게임 방이에요','That room is for a different game')
                    :_t('입장 실패','Join failed');
                return;
            }
            closeBackdrop();
            showGuestStatus(g);
            if(opts.onJoined)opts.onJoined(g);
        }
        document.getElementById('lpGuestJoin').addEventListener('click',doJoin);
    }

    function showGuestStatus(g){
        injectStyles();
        let bar=document.getElementById('lpRoomStatus');
        if(bar)bar.remove();
        bar=document.createElement('div');
        bar.id='lpRoomStatus';
        bar.className='lp-room-status';
        const lang=(localStorage.getItem('luckyplz_lang')||'en').toLowerCase().split('-')[0];
        const lbl=lang==='ko'?`👀 ${g.hostName} 님의 방 관전 중 · ${g.code}`:`👀 Watching ${g.hostName}'s room · ${g.code}`;
        bar.innerHTML='<span class="dot"></span><span>'+lbl+'</span>';
        document.body.appendChild(bar);
    }

    function escapeHtml(s){return String(s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}

    /* ============ Auto guest prompt when URL has ?room=XXX ============ */
    function detectGuestIntent(){
        const m=location.search.match(/[?&]room=([A-Za-z0-9]+)/);
        return m?m[1].toUpperCase():null;
    }

    /* Auto-localize the "Watch Together" button label if a game page
       placed one. Games put a default English label in HTML; we swap it
       to the user's language on load and whenever lang changes. */
    function localizeOnlineBtn(){
        const lbls=document.querySelectorAll('.online-btn-label, #onlineBtnLabel');
        if(!lbls.length)return;
        const lang=(localStorage.getItem('luckyplz_lang')||'en').toLowerCase().split('-')[0];
        const label=(
            lang==='ko'?'같이 보기':
            lang==='ja'?'一緒に見る':
            lang==='zh'?'一起看':
            lang==='es'?'Ver juntos':
            lang==='de'?'Zusammen ansehen':
            lang==='fr'?'Regarder ensemble':
            lang==='pt'?'Assistir juntos':
            lang==='ru'?'Смотреть вместе':
            lang==='vi'?'Xem cùng':
            lang==='id'?'Nonton bareng':
            lang==='th'?'ดูด้วยกัน':
            lang==='tr'?'Birlikte izle':
            'Watch Together'
        );
        lbls.forEach(function(l){l.textContent=label});
    }
    if(document.readyState==='loading'){
        document.addEventListener('DOMContentLoaded',localizeOnlineBtn);
    }else{
        localizeOnlineBtn();
    }
    /* Re-localize when lang changes (the lang selector uses a storage
       event we can hook into; fallback: observe document.documentElement.lang). */
    window.addEventListener('storage',function(e){
        if(e.key==='luckyplz_lang')localizeOnlineBtn();
    });
    const langObs=new MutationObserver(localizeOnlineBtn);
    langObs.observe(document.documentElement,{attributes:true,attributeFilter:['lang']});

    window.LpRoom={
        hostCreate:hostCreate,
        guestJoin:guestJoin,
        showHostModal:showHostModal,
        showGuestJoinModal:showGuestJoinModal,
        detectGuestIntent:detectGuestIntent,
        localizeOnlineBtn:localizeOnlineBtn,
        _injectStyles:injectStyles
    };
})();
