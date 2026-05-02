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
        overlay.innerHTML = `
            <div class="lp-rank-card">
                <div class="lp-rank-header">
                    <div class="lp-rank-title">RANK</div>
                    <button class="lp-rank-close" aria-label="닫기" type="button">✕</button>
                </div>
                <div class="lp-rank-tabs"></div>
                <div class="lp-rank-jump">
                    <input type="number" min="1" max="100" placeholder="순위 점프 (예: 50)" inputmode="numeric"/>
                    <button type="button">이동</button>
                </div>
                <div class="lp-rank-body"></div>
            </div>
        `;
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

    /* 헤더 / 탭 / 점프 input — 게임별 옵션 적용. */
    function applyOpts(opts){
        elTitle.textContent = (opts.gameTitle || 'RANK') + ' RANK';
        const scopes = opts.scopes || ['world','today','friends'];
        const labels = { world: '월드', today: '오늘', friends: '친구' };
        elTabs.innerHTML = scopes.map(s =>
            '<button class="lp-rank-tab'+(s===currentScope?' active':'')+'" data-scope="'+s+'" type="button">'
            + labels[s] + '</button>'
        ).join('');
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
        elBody.innerHTML = '<div class="lp-rank-loading">불러오는 중…</div>';
        const sb = (typeof window.getSupabase === 'function') ? window.getSupabase() : null;
        if(!sb){
            elBody.innerHTML = '<div class="lp-rank-empty">Supabase 클라이언트 없음.</div>';
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
                elBody.innerHTML = '<div class="lp-rank-empty">불러오기 실패<br>'
                    + esc(error.message) + '</div>';
                return;
            }
            if(!data || !data.length){
                const msg = currentScope === 'today'
                    ? '🌅 오늘 (한국 시간) 기록이 아직 없어요.<br>첫 기록의 주인공이 되세요!'
                    : currentScope === 'friends'
                    ? '친구가 아직 플레이하지 않았어요.<br>친구 추가는 /messages/ 에서!'
                    : '아직 기록이 없어요.<br>첫 도전자가 되세요!';
                elBody.innerHTML = '<div class="lp-rank-empty">'+msg+'</div>';
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
                            nickname: (window._lpMyNickname || '나'),
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
