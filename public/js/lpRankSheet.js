/*
  Lucky Please — Unified Rank Sheet

  모든 액션 게임 (tetris/snake/burger/pacman/dodge + tetris-sprint) 의
  랭킹 윈도우를 단일 컴포넌트로 통일. 게임마다 점수/시간 등 메트릭이
  달라도 옵션으로 분기.

  사용:
    LpRankSheet.open({
        gameKey:        'tetris',                  // 데이터 키 (CSS class)
        gameTitle:      'TETRIS',                  // 헤더 제목
        leaderboardRpc: 'tetris_leaderboard',      // RPC 이름
        myStatsRpc:     'tetris_my_stats',         // 본인 통계 RPC
        scoreField:     'best_score',              // row 의 점수 필드
        myStatsRankField:  'world_rank',           // my_stats 응답의 등수 필드
        myStatsScoreField: 'best_score',           // my_stats 응답의 점수 필드
        formatScore:    n => n.toLocaleString(),   // 표시 형식 (default 콤마)
        scopes:         ['world','today','friends']// 토글 (default 동일)
    });

  UI 구조:
    · 풀스크린 모달 (z-index 9999)
    · 헤더: 제목 + 우상단 ✕ 닫기
    · 모드 탭: 월드/오늘/친구
    · 점프 입력: 특정 순위 → 그 순위부터 +29위
    · 본문: default 1~30위. 본인 행 강조 (.self).
    · 본인이 표시 범위 밖이면 하단에 sticky 본인 행 추가.

  Why a class-based DOM (not inline-built)? — 한 번 만들고 재사용 →
  매 호출 시 layout thrash 없음. innerHTML 로 list 만 갱신.

  Style: <style> tag injected once on first open. self-contained 디자인 —
  각 게임 HTML 에 CSS 추가 안 해도 됨.
*/

(function(){
    'use strict';

    /* ---- i18n — 16 언어 지원 (lotto/ladder 등 utility 게임과 동일 패턴).
       lang 은 localStorage('luckyplz_lang') 에서 읽고, 미설정 시 'en' 기본.
       T(key) 가 누락된 키는 영어 fallback → 영어가 없으면 key 자체. */
    const I18N = {
        en: {
            rank: 'RANK', world: 'World', today: 'Today', friends: 'Friends',
            jumpPlaceholder: 'Jump to rank (e.g. 50)', jumpBtn: 'Go',
            loading: 'Loading…', loadFailed: 'Failed to load',
            noClient: 'Supabase client unavailable.',
            emptyToday: '🌅 No records today (KST).<br>Be the first!',
            emptyFriends: 'No friends have played yet.<br>Add friends at /messages/',
            emptyWorld: 'No records yet.<br>Be the first challenger!',
            you: 'You'
        },
        ko: {
            rank: '랭크', world: '월드', today: '오늘', friends: '친구',
            jumpPlaceholder: '순위 점프 (예: 50)', jumpBtn: '이동',
            loading: '불러오는 중…', loadFailed: '불러오기 실패',
            noClient: 'Supabase 클라이언트 없음.',
            emptyToday: '🌅 오늘 (한국 시간) 기록이 아직 없어요.<br>첫 기록의 주인공이 되세요!',
            emptyFriends: '친구가 아직 플레이하지 않았어요.<br>친구 추가는 /messages/ 에서!',
            emptyWorld: '아직 기록이 없어요.<br>첫 도전자가 되세요!',
            you: '나'
        },
        ja: {
            rank: 'ランク', world: '世界', today: '今日', friends: 'フレンド',
            jumpPlaceholder: 'ランクへジャンプ (例: 50)', jumpBtn: '移動',
            loading: '読み込み中…', loadFailed: '読み込み失敗',
            noClient: 'Supabaseクライアントがありません。',
            emptyToday: '🌅 本日(KST)の記録がありません。<br>最初の挑戦者になろう!',
            emptyFriends: 'フレンドがまだプレイしていません。<br>/messages/ でフレンド追加!',
            emptyWorld: 'まだ記録がありません。<br>最初の挑戦者になろう!',
            you: '私'
        },
        zh: {
            rank: '排名', world: '世界', today: '今日', friends: '好友',
            jumpPlaceholder: '跳转到排名 (例: 50)', jumpBtn: '前往',
            loading: '加载中…', loadFailed: '加载失败',
            noClient: 'Supabase 客户端不可用。',
            emptyToday: '🌅 今日 (KST) 暂无记录。<br>成为第一人吧!',
            emptyFriends: '好友还没玩过。<br>到 /messages/ 加好友!',
            emptyWorld: '暂无记录。<br>成为首个挑战者!',
            you: '我'
        },
        es: {
            rank: 'CLASIFICACIÓN', world: 'Mundo', today: 'Hoy', friends: 'Amigos',
            jumpPlaceholder: 'Ir al rango (ej: 50)', jumpBtn: 'Ir',
            loading: 'Cargando…', loadFailed: 'Error al cargar',
            noClient: 'Cliente Supabase no disponible.',
            emptyToday: '🌅 Sin récords hoy (KST).<br>¡Sé el primero!',
            emptyFriends: 'Tus amigos aún no han jugado.<br>Añade amigos en /messages/',
            emptyWorld: 'Sin récords aún.<br>¡Sé el primer retador!',
            you: 'Tú'
        },
        gb: {
            rank: 'RANK', world: 'World', today: 'Today', friends: 'Friends',
            jumpPlaceholder: 'Jump to rank (e.g. 50)', jumpBtn: 'Go',
            loading: 'Loading…', loadFailed: 'Failed to load',
            noClient: 'Supabase client unavailable.',
            emptyToday: '🌅 No records today (KST).<br>Be the first!',
            emptyFriends: 'No friends have played yet.<br>Add friends at /messages/',
            emptyWorld: 'No records yet.<br>Be the first challenger!',
            you: 'You'
        },
        de: {
            rank: 'RANG', world: 'Welt', today: 'Heute', friends: 'Freunde',
            jumpPlaceholder: 'Zu Rang springen (z.B. 50)', jumpBtn: 'Los',
            loading: 'Lädt…', loadFailed: 'Fehler beim Laden',
            noClient: 'Supabase-Client nicht verfügbar.',
            emptyToday: '🌅 Heute keine Einträge (KST).<br>Sei der Erste!',
            emptyFriends: 'Noch keine Freunde gespielt.<br>Freunde unter /messages/ hinzufügen',
            emptyWorld: 'Noch keine Einträge.<br>Sei der erste Herausforderer!',
            you: 'Ich'
        },
        fr: {
            rank: 'CLASSEMENT', world: 'Monde', today: 'Aujourd\'hui', friends: 'Amis',
            jumpPlaceholder: 'Aller au rang (ex: 50)', jumpBtn: 'OK',
            loading: 'Chargement…', loadFailed: 'Échec du chargement',
            noClient: 'Client Supabase indisponible.',
            emptyToday: '🌅 Aucun record aujourd\'hui (KST).<br>Soyez le premier !',
            emptyFriends: 'Aucun ami n\'a joué encore.<br>Ajoutez des amis sur /messages/',
            emptyWorld: 'Aucun record.<br>Soyez le premier challenger !',
            you: 'Moi'
        },
        pt: {
            rank: 'CLASSIFICAÇÃO', world: 'Mundo', today: 'Hoje', friends: 'Amigos',
            jumpPlaceholder: 'Ir para a posição (ex: 50)', jumpBtn: 'Ir',
            loading: 'Carregando…', loadFailed: 'Falha ao carregar',
            noClient: 'Cliente Supabase indisponível.',
            emptyToday: '🌅 Sem registros hoje (KST).<br>Seja o primeiro!',
            emptyFriends: 'Nenhum amigo jogou ainda.<br>Adicione amigos em /messages/',
            emptyWorld: 'Sem registros ainda.<br>Seja o primeiro desafiante!',
            you: 'Eu'
        },
        ru: {
            rank: 'РЕЙТИНГ', world: 'Мир', today: 'Сегодня', friends: 'Друзья',
            jumpPlaceholder: 'Перейти к рангу (напр.: 50)', jumpBtn: 'Перейти',
            loading: 'Загрузка…', loadFailed: 'Не удалось загрузить',
            noClient: 'Клиент Supabase недоступен.',
            emptyToday: '🌅 Сегодня (KST) нет записей.<br>Будьте первым!',
            emptyFriends: 'Друзья ещё не играли.<br>Добавьте друзей в /messages/',
            emptyWorld: 'Записей пока нет.<br>Будьте первым!',
            you: 'Я'
        },
        ar: {
            rank: 'الترتيب', world: 'عالمي', today: 'اليوم', friends: 'الأصدقاء',
            jumpPlaceholder: 'الانتقال إلى المرتبة (مثل: 50)', jumpBtn: 'انتقل',
            loading: 'جارٍ التحميل…', loadFailed: 'فشل التحميل',
            noClient: 'عميل Supabase غير متاح.',
            emptyToday: '🌅 لا سجلات اليوم (KST).<br>كن الأول!',
            emptyFriends: 'لم يلعب أصدقاؤك بعد.<br>أضف الأصدقاء في /messages/',
            emptyWorld: 'لا سجلات بعد.<br>كن أول من يتحدى!',
            you: 'أنا'
        },
        hi: {
            rank: 'रैंक', world: 'विश्व', today: 'आज', friends: 'मित्र',
            jumpPlaceholder: 'रैंक पर जाएँ (उदा.: 50)', jumpBtn: 'जाएँ',
            loading: 'लोड हो रहा है…', loadFailed: 'लोड विफल',
            noClient: 'Supabase क्लाइंट उपलब्ध नहीं।',
            emptyToday: '🌅 आज (KST) कोई रिकॉर्ड नहीं।<br>पहले बनें!',
            emptyFriends: 'किसी मित्र ने अभी नहीं खेला।<br>/messages/ में मित्र जोड़ें',
            emptyWorld: 'अभी कोई रिकॉर्ड नहीं।<br>पहले चुनौती लें!',
            you: 'मैं'
        },
        th: {
            rank: 'อันดับ', world: 'โลก', today: 'วันนี้', friends: 'เพื่อน',
            jumpPlaceholder: 'ข้ามไปอันดับ (เช่น: 50)', jumpBtn: 'ไป',
            loading: 'กำลังโหลด…', loadFailed: 'โหลดล้มเหลว',
            noClient: 'ไม่พบไคลเอ็นต์ Supabase',
            emptyToday: '🌅 วันนี้ยังไม่มีสถิติ (KST).<br>เป็นคนแรกสิ!',
            emptyFriends: 'เพื่อนของคุณยังไม่เคยเล่น<br>เพิ่มเพื่อนที่ /messages/',
            emptyWorld: 'ยังไม่มีสถิติ<br>มาเป็นคนแรก!',
            you: 'ฉัน'
        },
        id: {
            rank: 'PERINGKAT', world: 'Dunia', today: 'Hari Ini', friends: 'Teman',
            jumpPlaceholder: 'Lompat ke peringkat (mis.: 50)', jumpBtn: 'Pergi',
            loading: 'Memuat…', loadFailed: 'Gagal memuat',
            noClient: 'Klien Supabase tidak tersedia.',
            emptyToday: '🌅 Belum ada rekor hari ini (KST).<br>Jadilah yang pertama!',
            emptyFriends: 'Teman belum bermain.<br>Tambah teman di /messages/',
            emptyWorld: 'Belum ada rekor.<br>Jadilah penantang pertama!',
            you: 'Saya'
        },
        vi: {
            rank: 'XẾP HẠNG', world: 'Thế giới', today: 'Hôm nay', friends: 'Bạn bè',
            jumpPlaceholder: 'Nhảy đến hạng (vd: 50)', jumpBtn: 'Đi',
            loading: 'Đang tải…', loadFailed: 'Tải thất bại',
            noClient: 'Không có Supabase client.',
            emptyToday: '🌅 Chưa có kỷ lục hôm nay (KST).<br>Hãy là người đầu tiên!',
            emptyFriends: 'Chưa có bạn bè nào chơi.<br>Thêm bạn tại /messages/',
            emptyWorld: 'Chưa có kỷ lục nào.<br>Hãy là người thách đấu đầu tiên!',
            you: 'Tôi'
        },
        tr: {
            rank: 'SIRA', world: 'Dünya', today: 'Bugün', friends: 'Arkadaşlar',
            jumpPlaceholder: 'Sıraya atla (örn: 50)', jumpBtn: 'Git',
            loading: 'Yükleniyor…', loadFailed: 'Yüklenemedi',
            noClient: 'Supabase istemcisi yok.',
            emptyToday: '🌅 Bugün (KST) kayıt yok.<br>İlk sen ol!',
            emptyFriends: 'Arkadaşların henüz oynamadı.<br>/messages/ adresinden ekle',
            emptyWorld: 'Henüz kayıt yok.<br>İlk meydan okuyucu ol!',
            you: 'Ben'
        }
    };
    function getLang(){
        try {
            const fromUrl = new URLSearchParams(location.search).get('lang');
            if(fromUrl && I18N[fromUrl]) return fromUrl;
        } catch(_){}
        try {
            const ls = localStorage.getItem('luckyplz_lang');
            if(ls && I18N[ls]) return ls;
        } catch(_){}
        return 'en';
    }
    function T(key){
        const l = getLang();
        return (I18N[l] && I18N[l][key]) || I18N.en[key] || key;
    }

    /* CSS 한 번만 주입 (idempotent). */
    let stylesInjected = false;
    function injectStyles(){
        if(stylesInjected) return;
        stylesInjected = true;
        const css = `
.lp-rank-overlay{
    position:fixed;inset:0;z-index:9999;
    background:rgba(5,5,15,.92);backdrop-filter:blur(10px);
    display:none;flex-direction:column;
    color:#fff;font-family:'Noto Sans KR','Pretendard',system-ui,sans-serif;
}
.lp-rank-overlay.on{display:flex}
.lp-rank-header{
    flex-shrink:0;
    display:flex;align-items:center;justify-content:space-between;
    padding:14px 16px 10px;
    border-bottom:1px solid rgba(255,255,255,.08);
}
.lp-rank-title{
    font-family:'Orbitron',sans-serif;font-weight:900;
    font-size:1.1em;letter-spacing:.06em;
    background:linear-gradient(135deg,#FFE66D,#FF9A3C,#FF66E6);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}
.lp-rank-close{
    width:36px;height:36px;border-radius:50%;border:0;cursor:pointer;
    background:rgba(255,255,255,.06);color:rgba(255,255,255,.85);
    font-size:1.2em;line-height:1;display:flex;align-items:center;justify-content:center;
    transition:background .15s ease;
}
.lp-rank-close:active,.lp-rank-close:hover{background:rgba(255,90,120,.25);color:#fff}
.lp-rank-tabs{
    flex-shrink:0;display:flex;gap:6px;padding:8px 14px 6px;
}
.lp-rank-tab{
    flex:1;padding:8px;border-radius:10px;cursor:pointer;
    background:rgba(255,255,255,.04);
    border:1px solid rgba(255,255,255,.1);
    color:rgba(255,255,255,.6);
    font-family:inherit;font-weight:700;font-size:.78em;
}
.lp-rank-tab.active{
    background:rgba(0,217,255,.14);
    border-color:rgba(0,217,255,.45);color:#00D9FF;
}
.lp-rank-jump{
    flex-shrink:0;display:flex;gap:6px;padding:6px 14px 8px;align-items:center;
}
.lp-rank-jump input{
    flex:1;padding:8px 10px;border-radius:10px;
    background:rgba(255,255,255,.04);
    border:1px solid rgba(255,255,255,.1);
    color:#fff;font-family:'JetBrains Mono','Courier New',monospace;font-size:.85em;
    text-align:center;letter-spacing:.04em;
    -webkit-appearance:none;appearance:none;
}
.lp-rank-jump input::placeholder{color:rgba(255,255,255,.3)}
.lp-rank-jump input:focus{outline:none;border-color:rgba(168,85,247,.5);background:rgba(168,85,247,.06)}
.lp-rank-jump button{
    flex-shrink:0;padding:8px 16px;border-radius:10px;border:0;cursor:pointer;
    background:linear-gradient(135deg,#00D9FF,#A855F7);color:#fff;
    font-family:'Orbitron',sans-serif;font-weight:700;font-size:.78em;letter-spacing:.06em;
}
.lp-rank-jump button:active{transform:translateY(1px)}
.lp-rank-body{
    flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;
    padding:6px 12px 14px;
}
.lp-rank-row{
    display:grid;grid-template-columns:48px 1fr auto;
    align-items:center;gap:10px;padding:9px 12px;
    margin-bottom:5px;border-radius:10px;
    background:rgba(255,255,255,.025);
    border:1px solid rgba(255,255,255,.06);
    font-size:.86em;
}
.lp-rank-row.self{
    background:rgba(255,230,109,.08);
    border-color:rgba(255,230,109,.32);
    box-shadow:0 0 0 1px rgba(255,230,109,.12), 0 4px 14px -4px rgba(255,230,109,.18);
}
.lp-rank-row.sticky-self{
    position:sticky;bottom:0;
    background:rgba(255,230,109,.14);
    border-color:rgba(255,230,109,.5);
    margin-top:10px;
    box-shadow:0 -8px 16px -8px rgba(0,0,0,.6);
}
.lp-rank-rnk{
    font-family:'Orbitron',sans-serif;font-weight:900;
    font-size:.9em;text-align:center;
    color:rgba(255,255,255,.6);
}
.lp-rank-rnk.gold{color:#FFD24A}
.lp-rank-rnk.silver{color:#D7E0EA}
.lp-rank-rnk.bronze{color:#E0985E}
.lp-rank-who{display:flex;align-items:center;gap:8px;min-width:0}
.lp-rank-av{
    width:30px;height:30px;flex-shrink:0;border-radius:50%;
    background:linear-gradient(135deg,#A855F7,#00D9FF);
    color:#fff;display:flex;align-items:center;justify-content:center;
    font-weight:800;font-size:.78em;overflow:hidden;
}
.lp-rank-av img{width:100%;height:100%;object-fit:cover}
.lp-rank-nick{font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lp-rank-score{
    font-family:'Orbitron',sans-serif;font-weight:900;
    font-variant-numeric:tabular-nums;
    text-align:right;color:#fff;font-size:.95em;
}
.lp-rank-empty{
    text-align:center;padding:36px 16px;
    color:rgba(255,255,255,.5);font-size:.88em;line-height:1.6;
}
.lp-rank-loading{
    text-align:center;padding:36px 16px;
    color:rgba(255,255,255,.5);font-size:.88em;
}
@media (min-width:640px){
    /* Tablet/desktop: center modal in viewport, max width */
    .lp-rank-overlay{
        align-items:center;justify-content:center;padding:24px;
    }
    .lp-rank-overlay > .lp-rank-card{
        max-width:520px;width:100%;max-height:90vh;
        border-radius:16px;border:1px solid rgba(255,255,255,.08);
        background:rgba(8,10,20,.96);
        display:flex;flex-direction:column;overflow:hidden;
    }
}
.lp-rank-card{display:flex;flex-direction:column;flex:1;min-height:0}
        `;
        const styleEl = document.createElement('style');
        styleEl.id = 'lp-rank-sheet-styles';
        styleEl.textContent = css;
        document.head.appendChild(styleEl);
    }

    /* DOM 한 번만 만들고 재사용 — open 시 게임별 옵션으로 갱신. */
    let overlay = null;
    let elTitle, elTabs, elJumpInput, elJumpBtn, elBody, elClose;
    let currentOpts = null;
    let currentScope = 'world';
    let currentStartRank = 1;
    /* 본인 stats — my_stats 한 번만 fetch 해서 캐시 (rank/score). */
    let myStats = null;

    function buildDom(){
        if(overlay) return;
        overlay = document.createElement('div');
        overlay.className = 'lp-rank-overlay';
        /* placeholder 와 button 텍스트는 i18n — open 시점 lang 기준. */
        overlay.innerHTML = ''
            + '<div class="lp-rank-card">'
            +   '<div class="lp-rank-header">'
            +     '<div class="lp-rank-title">' + esc(T('rank')) + '</div>'
            +     '<button class="lp-rank-close" aria-label="X" type="button">✕</button>'
            +   '</div>'
            +   '<div class="lp-rank-tabs"></div>'
            +   '<div class="lp-rank-jump">'
            +     '<input type="number" min="1" max="100" placeholder="' + esc(T('jumpPlaceholder')) + '" inputmode="numeric"/>'
            +     '<button type="button">' + esc(T('jumpBtn')) + '</button>'
            +   '</div>'
            +   '<div class="lp-rank-body"></div>'
            + '</div>';
        document.body.appendChild(overlay);
        elTitle    = overlay.querySelector('.lp-rank-title');
        elTabs     = overlay.querySelector('.lp-rank-tabs');
        elJumpInput= overlay.querySelector('.lp-rank-jump input');
        elJumpBtn  = overlay.querySelector('.lp-rank-jump button');
        elBody     = overlay.querySelector('.lp-rank-body');
        elClose    = overlay.querySelector('.lp-rank-close');

        elClose.addEventListener('click', close);
        /* 카드 외부 클릭 시 닫기 (모달 backdrop). */
        overlay.addEventListener('click', (e) => {
            if(e.target === overlay) close();
        });
        /* ESC 닫기 */
        document.addEventListener('keydown', (e) => {
            if(overlay.classList.contains('on') && e.key === 'Escape') close();
        });
        /* 점프 — Enter 키 또는 버튼 */
        elJumpBtn.addEventListener('click', onJump);
        elJumpInput.addEventListener('keydown', (e) => {
            if(e.key === 'Enter') onJump();
        });
    }

    function onJump(){
        const v = parseInt(elJumpInput.value, 10);
        if(isNaN(v) || v < 1) return;
        currentStartRank = Math.max(1, v);
        load();
    }

    function close(){
        if(!overlay) return;
        overlay.classList.remove('on');
        document.body.style.overflow = '';
    }

    /* HTML escape for nickname etc. */
    function esc(s){
        return String(s == null ? '' : s)
            .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
            .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
    }
    function initials(n){
        const s = String(n||'?').trim();
        return s ? s.charAt(0).toUpperCase() : '?';
    }
    function meId(){
        try {
            if(typeof window.LP === 'object' && window.LP && window.LP.user) return window.LP.user.id || null;
        } catch(_){}
        try {
            const u = window._lpMe;
            if(u && u.id) return u.id;
        } catch(_){}
        return null;
    }

    function rowHtml(row, opts, isSticky){
        const isSelf = meId() && row.user_id === meId();
        const rnkCls = row.rnk === 1 ? ' gold'
                     : row.rnk === 2 ? ' silver'
                     : row.rnk === 3 ? ' bronze' : '';
        const rnkLabel = row.rnk <= 3
            ? ['🥇','🥈','🥉'][row.rnk - 1]
            : '#' + row.rnk;
        const av = row.avatar_url
            ? '<div class="lp-rank-av"><img src="'+esc(row.avatar_url)+'" referrerpolicy="no-referrer" alt=""></div>'
            : '<div class="lp-rank-av">'+esc(initials(row.nickname))+'</div>';
        const score = opts.formatScore(row[opts.scoreField]);
        const cls = 'lp-rank-row'
                  + (isSelf ? ' self' : '')
                  + (isSticky ? ' sticky-self' : '');
        return '<div class="'+cls+'">'
             +   '<div class="lp-rank-rnk'+rnkCls+'">'+rnkLabel+'</div>'
             +   '<div class="lp-rank-who">'+av
             +     '<div class="lp-rank-nick">'+esc(row.nickname || '?')+'</div>'
             +   '</div>'
             +   '<div class="lp-rank-score">'+esc(score)+'</div>'
             + '</div>';
    }

    /* 헤더 / 탭 / 점프 input — 게임별 옵션 적용. lang 변경 시 매번 호출
       돼서 i18n 라벨 자동 갱신. */
    function applyOpts(opts){
        elTitle.textContent = (opts.gameTitle || T('rank')) + ' ' + T('rank');
        const scopes = opts.scopes || ['world','today','friends'];
        elTabs.innerHTML = scopes.map(s =>
            '<button class="lp-rank-tab'+(s===currentScope?' active':'')+'" data-scope="'+s+'" type="button">'
            + esc(T(s)) + '</button>'
        ).join('');
        /* 점프 input/버튼 i18n re-apply (lang 바뀐 후 다시 open 시) */
        if(elJumpInput) elJumpInput.placeholder = T('jumpPlaceholder');
        if(elJumpBtn) elJumpBtn.textContent = T('jumpBtn');
        elTabs.querySelectorAll('.lp-rank-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                currentScope = btn.dataset.scope;
                currentStartRank = 1;
                elJumpInput.value = '';
                applyOpts(opts);   /* re-render tab actives */
                load();
            });
        });
    }

    /* my_stats fetch — 본인 등수 sticky 표시용. 비로그인이거나 RPC 미설정이면 null. */
    async function fetchMyStats(){
        if(!currentOpts.myStatsRpc || !meId()) { myStats = null; return; }
        try {
            const sb = (typeof window.getSupabase === 'function') ? window.getSupabase() : null;
            if(!sb) { myStats = null; return; }
            const {data, error} = await sb.rpc(currentOpts.myStatsRpc);
            if(error || !data || !data.has_record) { myStats = null; return; }
            myStats = data;
        } catch(_){ myStats = null; }
    }

    async function load(){
        elBody.innerHTML = '<div class="lp-rank-loading">' + esc(T('loading')) + '</div>';
        const sb = (typeof window.getSupabase === 'function') ? window.getSupabase() : null;
        if(!sb){
            elBody.innerHTML = '<div class="lp-rank-empty">' + esc(T('noClient')) + '</div>';
            return;
        }
        const opts = currentOpts;
        try {
            const limit = 30;
            const {data, error} = await sb.rpc(opts.leaderboardRpc, {
                p_scope:      currentScope,
                p_limit:      limit,
                p_start_rank: currentStartRank
            });
            if(error){
                console.warn('[lpRankSheet]', opts.leaderboardRpc, error.message);
                elBody.innerHTML = '<div class="lp-rank-empty">' + esc(T('loadFailed')) + '<br>'
                    + esc(error.message) + '</div>';
                return;
            }
            if(!data || !data.length){
                const msgKey = currentScope === 'today' ? 'emptyToday'
                            : currentScope === 'friends' ? 'emptyFriends'
                            : 'emptyWorld';
                elBody.innerHTML = '<div class="lp-rank-empty">' + T(msgKey) + '</div>';
                return;
            }
            let html = data.map(row => rowHtml(row, opts, false)).join('');

            /* Sticky 본인 행 — 표시된 범위에 본인이 없으면 하단 추가.
               my_stats RPC 가 world rank 만 반환 (오늘/친구 scope 의 rank
               는 다를 수 있음) — world scope 일 때만 sticky 표시. */
            if(currentScope === 'world' && myStats && meId()){
                const inList = data.some(r => r.user_id === meId());
                if(!inList){
                    const myRank = myStats[opts.myStatsRankField || 'world_rank'];
                    const myScore = myStats[opts.myStatsScoreField || opts.scoreField];
                    if(myRank && myScore != null){
                        const fakeRow = {
                            user_id: meId(),
                            nickname: (window._lpMyNickname || T('you')),
                            avatar_url: (window._lpMyAvatar || null),
                            rnk: myRank,
                            [opts.scoreField]: myScore
                        };
                        html += rowHtml(fakeRow, opts, true);
                    }
                }
            }
            elBody.innerHTML = html;
        } catch(e){
            console.warn('[lpRankSheet] threw', e);
            elBody.innerHTML = '<div class="lp-rank-empty">불러오기 실패</div>';
        }
    }

    async function open(opts){
        try {
            injectStyles();
            buildDom();
        } catch(e){
            console.error('[lpRankSheet] init failed', e);
            return;
        }
        currentOpts = opts || {};
        if(!currentOpts.leaderboardRpc){
            console.warn('[lpRankSheet] missing leaderboardRpc — opts:', opts);
            return;
        }
        try { console.log('[lpRankSheet] open', currentOpts.gameTitle, currentOpts.leaderboardRpc); } catch(_){}
        if(!currentOpts.scoreField) currentOpts.scoreField = 'best_score';
        if(typeof currentOpts.formatScore !== 'function'){
            currentOpts.formatScore = (n) => Number(n).toLocaleString();
        }
        currentScope = (currentOpts.initialScope) || 'world';
        currentStartRank = 1;
        elJumpInput.value = '';
        applyOpts(currentOpts);
        overlay.classList.add('on');
        document.body.style.overflow = 'hidden';   /* 배경 스크롤 잠금 */
        await fetchMyStats();
        await load();
    }

    /* 글로벌 노출 */
    window.LpRankSheet = { open, close };
})();
