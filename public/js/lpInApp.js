/* lpInApp.js — 메신저·SNS 인앱 브라우저에서 기본 브라우저로 탈출 (2026-09-25)
   ─────────────────────────────────────────────────────────────────────────
   왜: 카카오톡·LINE·인스타·페북·위챗 등에서 링크를 누르면 앱 내장 WebView 로
   열린다. 전체화면·화면방향 API 차단, 저장소 휘발, 노치 영역 오렌더 등으로
   게임이 제대로 안 돌아간다. 가능한 곳은 자동으로, 아니면 버튼·안내로 폰의
   기본 브라우저로 보낸다.

   로드: siteFooter.js 가 파일 맨 위에서 UA 사전검사 후에만 주입한다(일반
   브라우저는 이 파일을 받지도 않는다). 카카오톡은 bump-cache-helper.py 가
   모든 HTML <head> 에 심는 인라인 스니펫이 첫 페인트 전에 먼저 튕긴다 —
   이 모듈은 그 뒤처리(성공/실패 판정·안내 시트)와 나머지 앱 전부를 맡는다.

   ── 탈출 수단 표 (근거: 보고서 참조, 2026-09 기준) ──────────────────────
   앱            UA 토큰                        Android              iOS
   KakaoTalk     KAKAOTALK                      kakaotalk://web/openExternal?url=  (자동, 양쪽)
   LINE          Line/<ver>                     ?openExternalBrowser=1             (자동, 양쪽)
   Instagram     Instagram                      intent:// (자동)     instagram://extbrowser/?url= (탭)
   Threads       Barcelona                      intent:// (자동)     barcelona://extbrowser/?url= (탭)
   Facebook      FBAN FBAV FB_IAB FBIOS FB4A    intent:// (자동)     x-safari-https:// window.open (탭)
   Messenger     FB_IAB/MESSENGER, Messenger*   intent:// (자동)     x-safari-https:// (탭)
   Telegram      Telegram / window.TelegramWebview*  intent:// (자동)  x-safari-https:// (탭)
   WhatsApp      WhatsApp WA4A/ WAiOS/          intent:// (탭)       x-safari-https:// (탭)
   TikTok        musical_ly Bytedance trill_    intent:// (탭, 불안정) 수동 안내만
   X/Twitter     Twitter                        intent:// (탭)       수동 안내만
   Snapchat      Snapchat                       intent:// (탭)       수동 안내만
   LinkedIn      LinkedInApp                    intent:// (탭)       x-safari-https:// (탭)
   WeChat        MicroMessenger                 수동 안내만 (intent 차단)
   QQ            " QQ/<ver>"                    수동 안내만
   Naver·Daum·Band·에브리타임·카카오스토리·Discord·Viber·Zalo·Weibo·Baidu
                                                intent:// (탭)       x-safari-https:// (탭, 최선노력)
   기타 Android  "; wv)"                        intent:// (탭)
   기타 iOS      iPhone 인데 "Safari/" 없음      x-safari-https:// (탭)
     * 홈 화면 PWA(standalone)·Google 앱(GSA)·iOS Chrome/Firefox/Edge 등은 제외

   intent 형식: intent://host/path?query#hash#Intent;scheme=https;
               S.browser_fallback_url=<원래URL>;end   ← package 없음 = 기본 브라우저/선택창
   (Intent.parseUri 는 마지막 '#' 로 자르므로 원래 #hash 도 보존된다)

   안전장치:
   - 자동 이동은 세션당 1회 (sessionStorage lp_iab_try / 카톡은 lp_kko_out 공유)
   - "여기서 계속" 을 누르면 이 세션 동안 다시 안 띄움 (lp_iab_stay)
   - /auth/ 경로, ?code=&state= (OAuth 콜백), iframe 안, standalone PWA → 아무것도 안 함
   - ?lp_iab=off → 자동 이동 끔 (테스트·디버그)
   - URL 전체(경로·쿼리 ?room= ?c=·해시) 그대로 넘긴다
   - 일반 브라우저에 도착했는데 LINE 파라미터(openExternalBrowser=1)가 붙어
     있으면 주소창에서만 조용히 지운다

   공개 API: window.LpInApp = { info, detect(ua,env), escapeUrl(info,url),
     open(), copy(), show(), dismiss() }  (+ 구 이름 window.LpInAppExit 별칭)
   테스트 훅: 이 파일보다 먼저 window.__LP_IAB_UA = '<UA>' 를 두면 그 UA 로 판정.
*/
(function(){
  'use strict';
  if (window.LpInApp) return;

  /* ── 1. 앱 표 ─────────────────────────────────────────────────────────
     a / i = Android / iOS 수단.
       'kakao'  카카오 openExternal 스킴      'line'  openExternalBrowser=1
       'intent' Android intent://             'xs'    x-safari-https://
       'xsw'    x-safari-https:// (window.open 으로) 'ig' / 'th' 메타 네이티브 스킴
       null     수단 없음 → 링크 복사 + 메뉴 안내
     auto = 자동 이동할 플랫폼 ('a','i')
     pos  = 메뉴 위치(tr 오른쪽 위 / br 오른쪽 아래 / null 모름) [android, ios]
     ico  = 메뉴 아이콘 [android, ios]
     item = 메뉴 항목 문구 키 [android, ios]  */
  var APPS = [
    {id:'kakaotalk', n:{ko:'카카오톡',en:'KakaoTalk'}, re:/KAKAOTALK/i,
      a:'kakao', i:'kakao', auto:'ai', pos:['br','br'], ico:['⋮','⬆︎'], item:['other','safari']},
    {id:'line', n:{en:'LINE'}, re:/\bLine\/\d/,
      a:'line', i:'line', auto:'ai', pos:['tr','tr'], ico:['⋮','⋯'], item:['browser','safari']},
    {id:'kakaostory', n:{ko:'카카오스토리',en:'KakaoStory'}, re:/KAKAOSTORY/i,
      a:'intent', i:'xs', auto:'', pos:[null,null], ico:['⋮','⋯'], item:['other','safari']},
    {id:'naver', n:{ko:'네이버 앱',en:'NAVER app'}, re:/NAVER\(inapp|; ?naver\)/i,
      a:'intent', i:'xs', auto:'', pos:[null,null], ico:['⋯','⋯'], item:['other','safari']},
    {id:'daum', n:{ko:'다음 앱',en:'Daum app'}, re:/DaumApps|DaumDevice\/mobile/i,
      a:'intent', i:'xs', auto:'', pos:[null,null], ico:['⋮','⋯'], item:['other','safari']},
    {id:'band', n:{ko:'밴드',en:'BAND'}, re:/\bBAND\/\d/i,
      a:'intent', i:'xs', auto:'', pos:[null,null], ico:['⋮','⋯'], item:['other','safari']},
    {id:'everytime', n:{ko:'에브리타임',en:'Everytime'}, re:/everytimeApp/i,
      a:'intent', i:'xs', auto:'', pos:[null,null], ico:['⋮','⋯'], item:['other','safari']},
    {id:'threads', n:{en:'Threads'}, re:/\bBarcelona/i,
      a:'intent', i:'th', auto:'a', pos:['tr','tr'], ico:['⋮','⋯'], item:['external','external']},
    {id:'instagram', n:{en:'Instagram'}, re:/\bInstagram/i,
      a:'intent', i:'ig', auto:'a', pos:['tr','tr'], ico:['⋮','⋯'], item:['external','external']},
    {id:'messenger', n:{en:'Messenger'}, re:/FB_IAB\/MESSENGER|FBAN\/Messenger|MessengerForiOS|MessengerLite|Orca-Android/i,
      a:'intent', i:'xs', auto:'a', pos:['tr','tr'], ico:['⋮','⋯'], item:['external','external']},
    {id:'facebook', n:{en:'Facebook'}, re:/FBAN|FBAV|FB_IAB|FBIOS|FB4A|\bFBSS\//i,
      a:'intent', i:'xsw', auto:'a', pos:['tr','tr'], ico:['⋮','⋯'], item:['external','external']},
    {id:'wechat', n:{zh:'微信',en:'WeChat'}, re:/MicroMessenger/i,
      a:null, i:null, auto:'', pos:['tr','tr'], ico:['⋯','⋯'], item:['browser','safari']},
    {id:'qq', n:{en:'QQ'}, re:/\sQQ\/\d/,
      a:null, i:null, auto:'', pos:['tr','tr'], ico:['⋯','⋯'], item:['browser','safari']},
    {id:'weibo', n:{zh:'微博',en:'Weibo'}, re:/\bWeibo/i,
      a:'intent', i:'xs', auto:'', pos:['tr','tr'], ico:['⋯','⋯'], item:['browser','safari']},
    {id:'tiktok', n:{en:'TikTok'}, re:/musical_ly|BytedanceWebview|\btrill_|TikTok/i,
      a:'intent', i:null, auto:'', pos:['tr','tr'], ico:['⋯','⋯'], item:['browser','browser']},
    {id:'snapchat', n:{en:'Snapchat'}, re:/Snapchat/i,
      a:'intent', i:null, auto:'', pos:[null,null], ico:['⋮','⋯'], item:['browser','safari']},
    {id:'x', n:{en:'X'}, re:/\bTwitter/i,
      a:'intent', i:null, auto:'', pos:[null,null], ico:['⋮','⋯'], item:['browser','safari']},
    {id:'linkedin', n:{en:'LinkedIn'}, re:/LinkedInApp/i,
      a:'intent', i:'xs', auto:'', pos:['tr','tr'], ico:['⋮','⋯'], item:['browser','safari']},
    {id:'whatsapp', n:{en:'WhatsApp'}, re:/\bWhatsApp|\bWA4A\/|\bWAiOS\//i,
      a:'intent', i:'xs', auto:'', pos:['tr','tr'], ico:['⋮','⋯'], item:['browser','safari']},
    {id:'telegram', n:{en:'Telegram'}, re:/\bTelegram\b/i,
      a:'intent', i:'xs', auto:'a', pos:['tr','tr'], ico:['⋮','⋯'], item:['browser','safari']},
    {id:'discord', n:{en:'Discord'}, re:/\bDiscord\//i,
      a:'intent', i:'xs', auto:'', pos:[null,null], ico:['⋮','⋯'], item:['browser','safari']},
    {id:'viber', n:{en:'Viber'}, re:/\bViber\//i,
      a:'intent', i:'xs', auto:'', pos:[null,null], ico:['⋮','⋯'], item:['browser','safari']},
    {id:'zalo', n:{en:'Zalo'}, re:/\bZalo\b/i,
      a:'intent', i:'xs', auto:'', pos:['tr','tr'], ico:['⋯','⋯'], item:['browser','safari']},
    {id:'baidu', n:{zh:'百度',en:'Baidu'}, re:/baiduboxapp/i,
      a:'intent', i:null, auto:'', pos:[null,null], ico:['⋯','⋯'], item:['browser','safari']}
  ];
  var GENERIC_ANDROID = {id:'webview', n:null, a:'intent', i:null, auto:'', pos:[null,null], ico:['⋮','⋯'], item:['browser','safari']};
  var GENERIC_IOS     = {id:'webview', n:null, a:null, i:'xs',  auto:'', pos:[null,null], ico:['⋮','⋯'], item:['browser','safari']};

  /* 진짜 브라우저(iOS 3rd-party 포함)·Google 앱 — 일반 iOS WebView 판정에서 뺀다 */
  var IOS_REAL_BROWSER = /CriOS|FxiOS|EdgiOS|OPiOS|OPT\/|Whale|DuckDuckGo|YaBrowser|Brave|\bGSA\/|SamsungBrowser/i;

  /* ── 2. 판정 (순수 함수 — 테스트에서 직접 호출) ───────────────────── */
  function detect(ua, env){
    ua = ua || ''; env = env || {};
    var isAndroid = /Android/i.test(ua);
    var isIOS = /iPhone|iPad|iPod/i.test(ua) || (/Macintosh/i.test(ua) && env.touch > 1 && /Mobile\//.test(ua));
    var none = {inApp:false, app:null, os: isAndroid ? 'android' : (isIOS ? 'ios' : 'other')};
    if (!isAndroid && !isIOS) return none;          /* 데스크톱·봇·크롤러는 무조건 통과 */
    if (env.standalone) return none;                 /* 홈 화면 PWA */
    var os = isAndroid ? 'android' : 'ios';
    var app = null;
    for (var k = 0; k < APPS.length; k++) { if (APPS[k].re.test(ua)) { app = APPS[k]; break; } }
    if (!app && env.telegram) app = APPS[findIdx('telegram')];   /* Telegram Android 는 UA 표시 없음 */
    if (!app && isAndroid && /; wv\)/.test(ua)) app = GENERIC_ANDROID;
    if (!app && isIOS && !/Safari\//.test(ua) && !IOS_REAL_BROWSER.test(ua)) app = GENERIC_IOS;
    if (!app) return none;
    var p = os === 'android' ? 0 : 1;
    var method = os === 'android' ? app.a : app.i;
    return {
      inApp: true, os: os, app: app.id, names: app.n,
      method: method,                                         /* null = 수동 안내만 */
      auto: !!method && app.auto.indexOf(os === 'android' ? 'a' : 'i') >= 0,
      pos: app.pos[p], icon: app.ico[p], item: app.item[p]
    };
  }
  function findIdx(id){ for (var i = 0; i < APPS.length; i++) if (APPS[i].id === id) return i; return -1; }

  /* ── 3. 탈출 URL 만들기 (순수 함수) ────────────────────────────────── */
  /* 문자열로만 붙인다 — URL/URLSearchParams 로 다시 직렬화하면 %20 이 + 로
     바뀌는 등 원래 쿼리(?room= ?c=)의 인코딩이 달라진다 */
  function addParam(url, k, v){
    var h = url.indexOf('#'), base = h >= 0 ? url.slice(0, h) : url, hash = h >= 0 ? url.slice(h) : '';
    base = base.replace(new RegExp('([?&])' + k + '=[^&]*(&|$)'), function(_, a, b){ return b ? a : ''; }).replace(/[?&]$/, '');
    return base + (base.indexOf('?') >= 0 ? '&' : '?') + k + '=' + v + hash;
  }
  function delParam(url, k){
    var h = url.indexOf('#'), base = h >= 0 ? url.slice(0, h) : url, hash = h >= 0 ? url.slice(h) : '';
    base = base.replace(new RegExp('([?&])' + k + '=[^&]*(&|$)', 'g'), function(_, a, b){ return b ? a : ''; }).replace(/[?&]$/, '');
    return base + hash;
  }
  function escapeUrl(info, url){
    if (!info || !info.method) return null;
    var m = /^(https?):\/\/(.*)$/i.exec(url || '');
    if (!m) return null;
    var scheme = m[1].toLowerCase(), rest = m[2];
    switch (info.method) {
      case 'kakao':  return 'kakaotalk://web/openExternal?url=' + encodeURIComponent(url);
      case 'line':   return addParam(url, 'openExternalBrowser', '1');
      case 'ig':     return 'instagram://extbrowser/?url=' + encodeURIComponent(url);
      case 'th':     return 'barcelona://extbrowser/?url=' + encodeURIComponent(url);
      case 'xs': case 'xsw':
                     return 'x-safari-' + scheme + '://' + rest;
      case 'intent': return 'intent://' + rest + '#Intent;scheme=' + scheme
                          + ';action=android.intent.action.VIEW'
                          + ';S.browser_fallback_url=' + encodeURIComponent(url) + ';end';
    }
    return null;
  }

  /* ── 4. 환경 ───────────────────────────────────────────────────────── */
  var UA = window.__LP_IAB_UA || navigator.userAgent || '';
  var ENV = {
    standalone: (function(){ try { return !!(navigator.standalone || (window.matchMedia && matchMedia('(display-mode: standalone)').matches)); } catch(_){ return false; } })(),
    telegram: ('TelegramWebview' in window) || ('TelegramWebviewProxy' in window) || ('TelegramWebviewProxyProto' in window),
    touch: navigator.maxTouchPoints || 0
  };
  var inTop = true; try { inTop = window.top === window.self; } catch(_){ inTop = false; }
  var INFO = detect(UA, ENV);

  function ss(k, v){ try { if (v === undefined) return sessionStorage.getItem(k); sessionStorage.setItem(k, v); } catch(_){ return null; } }
  function qs(){ try { return new URLSearchParams(location.search); } catch(_){ return {get:function(){return null;}, has:function(){return false;}}; } }

  /* 일반 브라우저에 도착: LINE 이 붙인 파라미터만 주소창에서 지운다(페이지는 그대로) */
  if (!INFO.inApp) {
    try {
      if (inTop && /[?&]openExternalBrowser=1/.test(location.search) && history.replaceState) {
        history.replaceState(history.state, '', delParam(location.pathname + location.search + location.hash, 'openExternalBrowser'));
      }
    } catch(_){}
    window.LpInApp = {info: INFO, detect: detect, escapeUrl: escapeUrl, open: noop, copy: noop, show: noop, dismiss: noop};
    return;
  }
  function noop(){}

  var P = qs();
  var isAuth = /^\/auth(\/|$)/.test(location.pathname) || (P.get('code') && P.get('state'));
  var KEY_TRY = 'lp_iab_try', KEY_STAY = 'lp_iab_stay', KEY_KKO = 'lp_kko_out';

  /* iframe(랜딩의 게임 임베드) 안이거나 OAuth 경로면 아무것도 안 한다 */
  if (!inTop || isAuth) {
    window.LpInApp = {info: INFO, detect: detect, escapeUrl: escapeUrl, open: noop, copy: noop, show: noop, dismiss: noop};
    return;
  }

  /* ── 5. 언어 ───────────────────────────────────────────────────────── */
  function pickLang(){
    var l = P.get('lang');
    if (!l) { try { l = localStorage.getItem('luckyplz_lang'); } catch(_){} }
    if (!l) { var pm = /^\/(ko|ja|es|pt)\//.exec(location.pathname); if (pm) l = pm[1]; }
    if (!l) l = (navigator.language || 'en');
    l = String(l).toLowerCase().slice(0, 2);
    return /^(ko|en|ja|zh|es|pt)$/.test(l) ? l : 'en';
  }
  var LANG = pickLang();
  var T = {
    ko:{title:'{app} 안에서 열렸어요', titleG:'앱 내장 브라우저에서 열렸어요', body:'게임이 제대로 돌아가도록 폰의 기본 브라우저로 열어 주세요.',
        open:'기본 브라우저로 열기', copy:'링크 복사', copied:'링크를 복사했어요', stay:'그냥 여기서 계속',
        how:'{pos} {icon} 를 누르고 “{item}” 선택', howNoPos:'메뉴 {icon} 에서 “{item}” 선택', howCopy:'또는 링크를 복사해 브라우저 주소창에 붙여넣기',
        tr:'오른쪽 위', br:'오른쪽 아래', notOpened:'안 열리면 아래 방법으로 열어 주세요.',
        doneT:'기본 브라우저로 열었어요', doneB:'이 창은 닫아도 돼요.', close:'이 창 닫기', retry:'다시 열기',
        other:'다른 브라우저로 열기', browser:'브라우저로 열기', external:'외부 브라우저로 열기', safari:'Safari로 열기'},
    en:{title:'Opened inside {app}', titleG:'Opened in an in-app browser', body:'For the games to work properly, open this page in your phone’s browser.',
        open:'Open in browser', copy:'Copy link', copied:'Link copied', stay:'Continue here',
        how:'Tap {icon} at the {pos}, then “{item}”', howNoPos:'Open the {icon} menu, then “{item}”', howCopy:'Or copy the link and paste it into your browser',
        tr:'top right', br:'bottom right', notOpened:'Didn’t open? Try this instead:',
        doneT:'Opened in your browser', doneB:'You can close this window.', close:'Close this window', retry:'Open again',
        other:'Open in another browser', browser:'Open in browser', external:'Open in external browser', safari:'Open in Safari'},
    ja:{title:'{app} の中で開いています', titleG:'アプリ内ブラウザで開いています', body:'ゲームを正しく動かすため、スマホの標準ブラウザで開いてください。',
        open:'ブラウザで開く', copy:'リンクをコピー', copied:'リンクをコピーしました', stay:'このまま続ける',
        how:'{pos}の {icon} →「{item}」', howNoPos:'メニュー {icon} →「{item}」', howCopy:'またはリンクをコピーしてブラウザに貼り付け',
        tr:'右上', br:'右下', notOpened:'開かない場合はこちら:',
        doneT:'ブラウザで開きました', doneB:'この画面は閉じて大丈夫です。', close:'この画面を閉じる', retry:'もう一度開く',
        other:'他のブラウザで開く', browser:'ブラウザで開く', external:'外部ブラウザで開く', safari:'Safariで開く'},
    zh:{title:'正在 {app} 内打开', titleG:'正在应用内浏览器中打开', body:'为了游戏正常运行，请用手机默认浏览器打开。',
        open:'在浏览器中打开', copy:'复制链接', copied:'链接已复制', stay:'继续在此使用',
        how:'点击{pos}的 {icon}，选择「{item}」', howNoPos:'打开菜单 {icon}，选择「{item}」', howCopy:'或复制链接，粘贴到浏览器地址栏',
        tr:'右上角', br:'右下角', notOpened:'没有打开？请按以下方法：',
        doneT:'已在浏览器中打开', doneB:'可以关闭此窗口。', close:'关闭此窗口', retry:'再次打开',
        other:'在其他浏览器中打开', browser:'在浏览器打开', external:'在外部浏览器中打开', safari:'在Safari中打开'},
    es:{title:'Abierto dentro de {app}', titleG:'Abierto en un navegador integrado', body:'Para que los juegos funcionen bien, abre esta página en el navegador de tu móvil.',
        open:'Abrir en el navegador', copy:'Copiar enlace', copied:'Enlace copiado', stay:'Seguir aquí',
        how:'Toca {icon} ({pos}) y elige “{item}”', howNoPos:'Abre el menú {icon} y elige “{item}”', howCopy:'O copia el enlace y pégalo en tu navegador',
        tr:'arriba a la derecha', br:'abajo a la derecha', notOpened:'¿No se abrió? Prueba así:',
        doneT:'Abierto en tu navegador', doneB:'Puedes cerrar esta ventana.', close:'Cerrar esta ventana', retry:'Abrir de nuevo',
        other:'Abrir en otro navegador', browser:'Abrir en el navegador', external:'Abrir en navegador externo', safari:'Abrir en Safari'},
    pt:{title:'Aberto dentro do {app}', titleG:'Aberto em um navegador interno', body:'Para os jogos funcionarem direito, abra esta página no navegador do celular.',
        open:'Abrir no navegador', copy:'Copiar link', copied:'Link copiado', stay:'Continuar aqui',
        how:'Toque em {icon} ({pos}) e escolha “{item}”', howNoPos:'Abra o menu {icon} e escolha “{item}”', howCopy:'Ou copie o link e cole no navegador',
        tr:'canto superior direito', br:'canto inferior direito', notOpened:'Não abriu? Tente assim:',
        doneT:'Aberto no seu navegador', doneB:'Você pode fechar esta janela.', close:'Fechar esta janela', retry:'Abrir de novo',
        other:'Abrir em outro navegador', browser:'Abrir no navegador', external:'Abrir no navegador externo', safari:'Abrir no Safari'}
  };
  var L = T[LANG] || T.en;
  function t(k){ return L[k] != null ? L[k] : T.en[k]; }
  function appName(){ var n = INFO.names; if (!n) return ''; return n[LANG] || n.en || ''; }
  function fill(s, o){ return s.replace(/\{(\w+)\}/g, function(_, k){ return o[k] != null ? o[k] : ''; }); }
  function esc(s){ return String(s).replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }

  /* ── 6. 동작 ───────────────────────────────────────────────────────── */
  function currentUrl(){
    /* LINE 재시도 때 파라미터가 중복되지 않게, 그리고 캐시 버스터 _b 는 빼고 넘긴다 */
    return delParam(location.href, '_b');
  }
  /* 외부 앱으로 넘어갔는지: 시도 직후 8초 안에 화면이 숨겨지거나(visibilitychange)
     창이 포커스를 잃으면(blur — Android 선택창 등) 넘어간 것으로 본다. 돌아오면
     '열었어요' 시트(카톡은 인앱 창 닫기 버튼 포함). */
  var wentHidden = false, attemptAt = 0, gen = 0;   /* gen: '열었어요' 이후 묵은 실패 타이머 무효화 */
  function recent(){ return attemptAt && Date.now() - attemptAt < 8000; }
  function back(){ if (!wentHidden || document.hidden) return; wentHidden = false; attemptAt = 0; gen++; showDone(); }
  document.addEventListener('visibilitychange', function(){ if (document.hidden) { if (recent()) wentHidden = true; } else back(); });
  window.addEventListener('blur', function(){ if (recent()) wentHidden = true; });
  window.addEventListener('focus', function(){ setTimeout(back, 60); });

  function markAttempt(){
    attemptAt = Date.now();
    ss(KEY_TRY, INFO.app + '|' + attemptAt);
    if (INFO.app === 'kakaotalk') ss(KEY_KKO, '1');
    /* 1.6초 뒤에도 이 화면이 앞에 있으면 실패로 보고 수동 안내를 펼친다 */
    var g = ++gen;
    setTimeout(function(){ if (g === gen && !document.hidden && !wentHidden) showSheet(true); }, 1600);
  }
  function openExternal(){
    var u = escapeUrl(INFO, currentUrl());
    if (!u) { showSheet(true); return false; }
    markAttempt();
    try {
      if (INFO.method === 'xsw') { var w = window.open(u, '_blank'); if (w) return true; }  /* Facebook iOS 는 window.open 경로만 통한다 */
      location.href = u;
    } catch(_){}
    return true;
  }

  function copyLink(){
    var url = location.href;
    url = delParam(delParam(url, 'openExternalBrowser'), '_b');
    function ok(){ toast(t('copied')); }
    function legacy(){
      try {
        var ta = document.createElement('textarea');
        ta.value = url; ta.setAttribute('readonly', '');
        ta.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;opacity:0;font-size:16px';
        document.body.appendChild(ta); ta.focus(); ta.select();
        try { ta.setSelectionRange(0, url.length); } catch(_){}
        var done = document.execCommand && document.execCommand('copy');
        ta.remove();
        if (done) { ok(); return; }
      } catch(_){}
      showUrlField(url);           /* 최후: 선택 가능한 입력칸으로 보여 준다 */
    }
    try {
      if (navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext !== false) {
        navigator.clipboard.writeText(url).then(ok, legacy); return;
      }
    } catch(_){}
    legacy();
  }

  /* ── 7. UI ─────────────────────────────────────────────────────────── */
  function css(){
    if (document.getElementById('lp-iab-css')) return;
    var s = document.createElement('style'); s.id = 'lp-iab-css';
    s.textContent =
      '#lp-iab{position:fixed;inset:0;z-index:2147483600;font-family:"Noto Sans KR","Noto Sans JP","PingFang SC",system-ui,sans-serif;-webkit-tap-highlight-color:transparent}' +
      '#lp-iab .bd{position:absolute;inset:0;background:rgba(6,6,14,.55);animation:lpiabF .25s ease-out}' +
      '#lp-iab .sh{position:absolute;left:0;right:0;bottom:0;margin:0 auto;max-width:440px;box-sizing:border-box;' +
        'background:#17172a;color:#fff;border-radius:20px 20px 0 0;border:1px solid rgba(255,255,255,.08);border-bottom:0;' +
        'padding:18px 18px calc(14px + env(safe-area-inset-bottom,0px));box-shadow:0 -12px 40px rgba(0,0,0,.5);animation:lpiabU .32s cubic-bezier(.2,.9,.3,1.1)}' +
      '#lp-iab .gr{width:38px;height:4px;border-radius:2px;background:rgba(255,255,255,.18);margin:-6px auto 12px}' +
      '#lp-iab h2{margin:0 0 4px;font-size:17px;font-weight:800;line-height:1.35;letter-spacing:-.01em}' +
      '#lp-iab p{margin:0 0 14px;font-size:13.5px;line-height:1.5;color:rgba(255,255,255,.66)}' +
      '#lp-iab .b1,#lp-iab .b2{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;box-sizing:border-box;min-height:50px;border-radius:14px;' +
        'font:inherit;font-size:16px;font-weight:800;text-decoration:none;cursor:pointer;border:0;margin:0 0 8px}' +
      '#lp-iab .b1{background:#FFE66D;color:#1a1400;box-shadow:0 4px 0 #c9ad2c}' +
      '#lp-iab .b1:active{transform:translateY(2px);box-shadow:0 2px 0 #c9ad2c}' +
      '#lp-iab .b2{background:rgba(255,255,255,.08);color:#fff;font-weight:700;font-size:15px;min-height:46px}' +
      '#lp-iab .b2:active{background:rgba(255,255,255,.14)}' +
      '#lp-iab .b3{display:block;margin:4px auto 0;background:none;border:0;color:rgba(255,255,255,.5);font:inherit;font-size:13.5px;padding:10px 14px;cursor:pointer;text-decoration:underline;text-underline-offset:3px}' +
      '#lp-iab .how{display:none;margin:2px 0 12px;padding:11px 12px;border-radius:12px;background:rgba(255,230,109,.08);border:1px dashed rgba(255,230,109,.35);font-size:13.5px;line-height:1.55;color:#fff4c2}' +
      '#lp-iab.showhow .how{display:block}' +
      '#lp-iab .how b{display:inline-block;min-width:22px;padding:0 6px;border-radius:6px;background:rgba(255,255,255,.14);color:#fff;text-align:center;font-weight:800}' +
      '#lp-iab .how small{display:block;margin-top:4px;color:rgba(255,255,255,.5);font-size:12px}' +
      '#lp-iab .how .nf{display:none;margin-bottom:4px;color:rgba(255,255,255,.62);font-size:12.5px}' +
      '#lp-iab.failed .how .nf{display:block}' +
      '#lp-iab .url{display:none;width:100%;box-sizing:border-box;margin:0 0 8px;padding:10px;border-radius:10px;border:1px solid rgba(255,255,255,.2);background:#0d0d1a;color:#fff;font:14px/1.3 monospace}' +
      '#lp-iab .ar{position:fixed;display:none;flex-direction:column;align-items:flex-end;pointer-events:none;right:10px;color:#FFE66D;font-weight:800;font-size:13px;text-shadow:0 1px 3px rgba(0,0,0,.8)}' +
      '#lp-iab.showhow .ar{display:flex}' +
      '#lp-iab .ar.tr{top:calc(6px + env(safe-area-inset-top,0px))}' +
      '#lp-iab .ar.br{bottom:calc(var(--lpiab-sh,300px) + 8px)}' +
      '#lp-iab .ar i{font-style:normal;font-size:34px;line-height:1;animation:lpiabB 1s ease-in-out infinite}' +
      '#lp-iab .ar.br i{animation-name:lpiabBd}' +
      '#lp-iab .ar span{margin-top:2px;padding:3px 8px;border-radius:8px;background:rgba(23,23,42,.92)}' +
      '#lp-iab .ar.br span{order:-1;margin:0 0 2px}' +
      '#lp-iab-toast{position:fixed;left:50%;top:calc(18px + env(safe-area-inset-top,0px));transform:translateX(-50%);z-index:2147483601;background:#2a2a44;color:#fff;' +
        'padding:10px 16px;border-radius:12px;font:700 14px/1.3 "Noto Sans KR",system-ui,sans-serif;box-shadow:0 6px 20px rgba(0,0,0,.45);animation:lpiabF .2s ease-out}' +
      '@keyframes lpiabF{from{opacity:0}to{opacity:1}}' +
      '@keyframes lpiabU{from{transform:translateY(100%)}to{transform:translateY(0)}}' +
      '@keyframes lpiabB{0%,100%{transform:translate(0,0)}50%{transform:translate(4px,-6px)}}' +
      '@keyframes lpiabBd{0%,100%{transform:translate(0,0)}50%{transform:translate(4px,6px)}}' +
      '@media (prefers-reduced-motion:reduce){#lp-iab .sh,#lp-iab .bd,#lp-iab .ar i{animation:none}}';
    (document.head || document.documentElement).appendChild(s);
  }

  function toast(msg){
    var o = document.getElementById('lp-iab-toast'); if (o) o.remove();
    var d = document.createElement('div'); d.id = 'lp-iab-toast'; d.setAttribute('role', 'status'); d.textContent = msg;
    document.body.appendChild(d); setTimeout(function(){ d.remove(); }, 2000);
  }
  function showUrlField(url){
    var f = document.querySelector('#lp-iab .url'); if (!f) { toast(url); return; }
    f.value = url; f.style.display = 'block'; f.focus(); f.select();
  }

  /* 게임 페이지의 document 레벨 touchstart preventDefault 가 click 합성을 죽이는
     함정(CLAUDE.md 'canvas 모달 클릭 함정') 대비: 루트에서 전파를 끊고, touchend
     에서도 직접 실행한다(중복 실행은 막는다). */
  function tap(el, fn){
    var last = 0;
    function run(e){ if (Date.now() - last < 600) { if (e && e.cancelable) e.preventDefault(); return; } last = Date.now(); fn(e); }
    el.addEventListener('click', run);
    el.addEventListener('touchend', function(e){ if (e.cancelable) e.preventDefault(); run(e); });
  }

  function howHtml(){
    var itemTxt = t(INFO.item || 'browser');
    var line = INFO.pos
      ? fill(t('how'), {pos: t(INFO.pos), icon: '<b>' + esc(INFO.icon) + '</b>', item: esc(itemTxt)})
      : fill(t('howNoPos'), {icon: '<b>' + esc(INFO.icon) + '</b>', item: esc(itemTxt)});
    return (INFO.method ? '<span class="nf">' + esc(t('notOpened')) + '</span>' : '') + line + '<small>' + esc(t('howCopy')) + '</small>';
  }

  var root = null;
  function mount(html, cls){
    css();
    if (root) root.remove();
    root = document.createElement('div'); root.id = 'lp-iab'; root.className = cls || '';
    root.setAttribute('role', 'dialog'); root.setAttribute('aria-modal', 'true');
    root.innerHTML = html;
    ['touchstart','touchmove','touchend','pointerdown','mousedown','click'].forEach(function(ev){
      root.addEventListener(ev, function(e){ e.stopPropagation(); }, false);
    });
    document.body.appendChild(root);
    var sh = root.querySelector('.sh');
    if (sh) root.style.setProperty('--lpiab-sh', sh.offsetHeight + 'px');
    return root;
  }

  /* expandHow: 수동 안내를 펼친 상태로 연다(수단 없음 / 자동·탭 실패 후) */
  function showSheet(expandHow){
    if (ss(KEY_STAY)) return;
    if (!document.body) { document.addEventListener('DOMContentLoaded', function(){ showSheet(expandHow); }); return; }
    var name = appName();
    var title = name ? fill(t('title'), {app: esc(name)}) : esc(t('titleG'));
    var hasEsc = !!escapeUrl(INFO, currentUrl());
    var manual = !hasEsc;
    var arrow = INFO.pos ? '<div class="ar ' + INFO.pos + '"><i>' + (INFO.pos === 'br' ? '↘' : '↗') + '</i><span>' + esc(INFO.icon) + '</span></div>' : '';
    var html =
      '<div class="bd"></div>' + arrow +
      '<div class="sh">' +
        '<div class="gr"></div>' +
        '<h2>' + title + '</h2>' +
        '<p>' + esc(t('body')) + '</p>' +
        '<div class="how">' + howHtml() + '</div>' +
        '<input class="url" readonly aria-label="URL">' +
        (manual
          ? '<button type="button" class="b1" data-a="copy">' + esc(t('copy')) + '</button>'
          : '<a class="b1" data-a="open" href="' + esc(escapeUrl(INFO, currentUrl())) + '">' + esc(t('open')) + '</a>' +
            '<button type="button" class="b2" data-a="copy">' + esc(t('copy')) + '</button>') +
        '<button type="button" class="b3" data-a="stay">' + esc(t('stay')) + '</button>' +
      '</div>';
    /* failed = 자동/탭 시도 후에도 여기 남아 있음 → "안 열리면…" 머리말까지 보인다 */
    var r = mount(html, (manual || expandHow) ? ('showhow' + (expandHow && !manual ? ' failed' : '')) : '');
    var open = r.querySelector('[data-a="open"]');
    if (open) {
      /* 네이티브 <a href> 탭이 가장 강한 사용자 활성화 신호다(메타 iOS 스킴 등) →
         기본 동작을 살리고 상태만 기록. click 합성이 죽은 페이지 대비로
         touchend 뒤 450ms 안에 click 이 안 오면 직접 이동한다. */
      var clicked = 0;
      open.addEventListener('click', function(e){
        clicked = Date.now();
        r.classList.remove('showhow');
        if (INFO.method === 'xsw') { e.preventDefault(); openExternal(); return; }
        markAttempt();
      });
      open.addEventListener('touchend', function(){
        var t0 = Date.now();
        setTimeout(function(){ if (clicked < t0) { r.classList.remove('showhow'); openExternal(); } }, 450);
      });
    }
    tap(r.querySelector('[data-a="copy"]'), function(){ copyLink(); r.classList.add('showhow'); });
    tap(r.querySelector('[data-a="stay"]'), dismiss);
    tap(r.querySelector('.bd'), dismiss);
  }

  function showDone(){
    if (ss(KEY_STAY)) return;
    var kakaoClose = INFO.app === 'kakaotalk';
    var html =
      '<div class="bd"></div>' +
      '<div class="sh">' +
        '<div class="gr"></div>' +
        '<h2>✓ ' + esc(t('doneT')) + '</h2>' +
        '<p>' + esc(t('doneB')) + '</p>' +
        (kakaoClose ? '<button type="button" class="b1" data-a="close">' + esc(t('close')) + '</button>' : '') +
        '<button type="button" class="b2" data-a="retry">' + esc(t('retry')) + '</button>' +
        '<button type="button" class="b3" data-a="stay">' + esc(t('stay')) + '</button>' +
      '</div>';
    var r = mount(html, '');
    var c = r.querySelector('[data-a="close"]');
    if (c) tap(c, function(){
      /* 카카오톡 인앱 창 닫기: Android kakaotalk://inappbrowser/close, iOS kakaoweb://closeBrowser */
      try { location.href = INFO.os === 'ios' ? 'kakaoweb://closeBrowser' : 'kakaotalk://inappbrowser/close'; } catch(_){}
    });
    tap(r.querySelector('[data-a="retry"]'), function(){ openExternal(); });
    tap(r.querySelector('[data-a="stay"]'), dismiss);
    tap(r.querySelector('.bd'), dismiss);
  }

  function dismiss(){
    ss(KEY_STAY, '1');
    if (root) { root.remove(); root = null; }
  }

  /* ── 8. 시작 ───────────────────────────────────────────────────────── */
  var tried = !!ss(KEY_TRY) || (INFO.app === 'kakaotalk' && !!ss(KEY_KKO));
  var lineRetry = INFO.method === 'line' && P.get('openExternalBrowser') === '1';   /* 파라미터가 붙었는데 아직 LINE 이면 실패 */
  var autoOff = P.get('lp_iab') === 'off';
  var stayed = !!ss(KEY_STAY);
  /* <head> 스니펫이 이미 튕겨서 이 모듈이 뜨기 전에 화면이 숨겨졌다면 = 성공 */
  if (INFO.app === 'kakaotalk' && tried && !lineRetry && document.hidden) { wentHidden = true; }

  if (!stayed) {
    if (INFO.auto && !tried && !lineRetry && !autoOff) {
      openExternal();                       /* 성공하면 화면이 숨겨지고, 돌아오면 '열었어요' 시트 */
    } else {
      /* 카카오: <head> 스니펫이 방금 튕겼을 수 있다 → 잠깐 기다렸다가 아직 앞이면 안내 */
      attemptAt = (INFO.app === 'kakaotalk' && tried) ? Date.now() : 0;
      var expand = tried || lineRetry || !INFO.method;
      var g0 = gen;
      var later = function(){ setTimeout(function(){
        if (wentHidden || g0 !== gen) return;                          /* 방금 튕기기 성공 → 돌아오면 '열었어요' */
        if (!document.hidden) { showSheet(expand); return; }
        /* 백그라운드 탭·프리렌더로 열린 경우: 실제로 보일 때 띄운다 */
        var onVis = function(){ if (document.hidden) return; document.removeEventListener('visibilitychange', onVis); if (!root && !wentHidden && g0 === gen) showSheet(expand); };
        document.addEventListener('visibilitychange', onVis);
      }, attemptAt ? 1600 : 400); };
      if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', later); else later();
    }
  }

  var API = {
    info: INFO, detect: detect, escapeUrl: escapeUrl,
    open: openExternal, copy: copyLink, show: function(){ try { sessionStorage.removeItem(KEY_STAY); } catch(_){} showSheet(false); }, dismiss: dismiss,
    /* 구 lpInAppExit.js 호환 */
    openExternal: openExternal, isInAppBrowser: true, detected: INFO.app
  };
  window.LpInApp = API;
  window.LpInAppExit = API;
})();
