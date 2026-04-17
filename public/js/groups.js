/*
  Lucky Please - Saved Groups
  Shared CRUD + UI widget. Requires /js/supabase-config.js loaded first.
*/

(function injectGroupsStyles() {
    if (document.getElementById('lp-groups-styles')) return;
    const s = document.createElement('style');
    s.id = 'lp-groups-styles';
    s.textContent = `
.lp-groups{display:flex;gap:6px;position:relative;flex-wrap:nowrap;align-items:center;font-family:'Noto Sans KR',sans-serif}
.lp-groups-btn{display:inline-flex;align-items:center;gap:5px;padding:6px 11px;border-radius:10px;border:1.5px solid rgba(255,255,255,.1);background:rgba(255,255,255,.04);color:rgba(255,255,255,.75);font-size:.72em;font-weight:700;cursor:pointer;transition:border-color .2s,background .2s,color .2s;font-family:inherit;white-space:nowrap}
.lp-groups-btn:hover{border-color:rgba(255,230,109,.5);background:rgba(255,230,109,.06);color:#fff}
.lp-groups-save-btn{color:rgba(0,255,136,.85);border-color:rgba(0,255,136,.22)}
.lp-groups-save-btn:hover{border-color:rgba(0,255,136,.6);background:rgba(0,255,136,.08);color:#fff}
.lp-groups-ico{font-size:.95em;line-height:1}
.lp-groups-chev{font-size:.65em;opacity:.6;margin-left:1px}
.lp-groups-txt{letter-spacing:.02em}
.lp-groups-menu{position:absolute;top:calc(100% + 6px);left:0;min-width:220px;max-width:300px;max-height:280px;overflow-y:auto;background:rgba(18,18,36,.98);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.1);border-radius:12px;padding:5px;z-index:40;box-shadow:0 12px 32px rgba(0,0,0,.5)}
.lp-groups-menu[hidden]{display:none}
.lp-groups-item{display:flex;gap:3px;margin:2px 0}
.lp-groups-load-one{flex:1;display:flex;align-items:center;justify-content:space-between;padding:8px 11px;border-radius:8px;border:none;background:rgba(255,255,255,.03);color:#fff;font-size:.82em;cursor:pointer;transition:background .2s;font-family:inherit;text-align:left;gap:8px}
.lp-groups-load-one:hover{background:rgba(255,230,109,.1)}
.lp-groups-name{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lp-groups-count{font-size:.72em;color:rgba(255,255,255,.4);font-family:'Orbitron',sans-serif;flex-shrink:0;padding:2px 7px;border-radius:999px;background:rgba(255,255,255,.05)}
.lp-groups-del{width:28px;height:28px;border-radius:8px;border:none;background:rgba(255,255,255,.03);color:rgba(255,255,255,.35);cursor:pointer;font-size:1.1em;line-height:1;transition:all .2s;flex-shrink:0;align-self:center}
.lp-groups-del:hover{background:rgba(255,51,102,.2);color:#FF6B8B}
.lp-groups-login,.lp-groups-empty,.lp-groups-err{display:block;padding:12px 14px;font-size:.78em;color:rgba(255,255,255,.5);text-align:center;letter-spacing:.02em}
.lp-groups-login{color:#FFE66D;text-decoration:none;font-weight:700;cursor:pointer;border-radius:8px;transition:background .2s}
.lp-groups-login:hover{background:rgba(255,230,109,.08);color:#fff}
.lp-groups-err{color:#FF6B8B}
.lp-groups-toast{position:absolute;top:-34px;left:50%;transform:translateX(-50%);padding:5px 12px;border-radius:999px;background:rgba(0,255,136,.15);border:1px solid rgba(0,255,136,.35);color:#00FF88;font-size:.72em;font-weight:700;letter-spacing:.04em;white-space:nowrap;z-index:41;pointer-events:none}
.lp-groups-toast[hidden]{display:none}
@media(max-width:500px){
  .lp-groups-btn{padding:5px 9px;font-size:.68em}
  .lp-groups-menu{min-width:200px;max-width:92vw}
}
`;
    document.head.appendChild(s);
})();

async function lpListGroups() {
    const { data, error } = await getSupabase()
        .from('groups')
        .select('id, name, members, updated_at')
        .order('updated_at', { ascending: false });
    if (error) throw error;
    return data || [];
}

async function lpCreateGroup(name, members) {
    const user = await getUser();
    if (!user) throw new Error('Not logged in');
    const { data, error } = await getSupabase()
        .from('groups')
        .insert({ user_id: user.id, name, members })
        .select()
        .single();
    if (error) throw error;
    return data;
}

async function lpUpdateGroup(id, patch) {
    const { data, error } = await getSupabase()
        .from('groups')
        .update(patch)
        .eq('id', id)
        .select()
        .single();
    if (error) throw error;
    return data;
}

async function lpDeleteGroup(id) {
    const { error } = await getSupabase().from('groups').delete().eq('id', id);
    if (error) throw error;
}

function lpEscape(s) {
    return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/*
  mountGroupsWidget({ container, getMembers, setMembers, labels })
    container   - DOM element to render inside (required)
    getMembers  - () => any[]  current member payload to save (required)
    setMembers  - (members) => void  load saved payload into the game (required)
    labels      - optional i18n overrides
*/
function mountGroupsWidget(opts) {
    const L = Object.assign({
        load: 'Groups',
        save: 'Save',
        empty: 'No saved groups yet.',
        loginCTA: '🔐 Sign in to save groups',
        prompt: 'Name this group:',
        confirmDelete: 'Delete this group?',
        noMembers: 'Add members first.',
        saved: 'Saved ✓',
    }, opts.labels || {});

    const box = opts.container;
    box.classList.add('lp-groups');
    box.innerHTML = `
      <button type="button" class="lp-groups-btn lp-groups-load-btn">
        <span class="lp-groups-ico">📁</span>
        <span class="lp-groups-txt" data-role="load-label">${lpEscape(L.load)}</span>
        <span class="lp-groups-chev">▾</span>
      </button>
      <button type="button" class="lp-groups-btn lp-groups-save-btn">
        <span class="lp-groups-ico">💾</span>
        <span class="lp-groups-txt" data-role="save-label">${lpEscape(L.save)}</span>
      </button>
      <div class="lp-groups-menu" data-role="menu" hidden></div>
      <div class="lp-groups-toast" data-role="toast" hidden></div>
    `;
    const loadBtn = box.querySelector('.lp-groups-load-btn');
    const saveBtn = box.querySelector('.lp-groups-save-btn');
    const menuEl  = box.querySelector('[data-role="menu"]');
    const toastEl = box.querySelector('[data-role="toast"]');
    let currentLabels = L;

    function toast(text) {
        toastEl.textContent = text;
        toastEl.hidden = false;
        clearTimeout(toast._t);
        toast._t = setTimeout(() => { toastEl.hidden = true; }, 1800);
    }

    function returnUrl() {
        return encodeURIComponent(location.pathname + location.search);
    }

    async function refreshMenu() {
        const user = await getUser();
        if (!user) {
            menuEl.innerHTML = `<a class="lp-groups-login" href="/auth/?return=${returnUrl()}">${lpEscape(currentLabels.loginCTA)}</a>`;
            return;
        }
        try {
            const groups = await lpListGroups();
            if (!groups.length) {
                menuEl.innerHTML = `<div class="lp-groups-empty">${lpEscape(currentLabels.empty)}</div>`;
                return;
            }
            menuEl.innerHTML = groups.map(g => {
                const count = Array.isArray(g.members) ? g.members.length : 0;
                return `
                  <div class="lp-groups-item">
                    <button type="button" class="lp-groups-load-one" data-id="${g.id}">
                      <span class="lp-groups-name">${lpEscape(g.name)}</span>
                      <span class="lp-groups-count">${count}</span>
                    </button>
                    <button type="button" class="lp-groups-del" data-id="${g.id}" aria-label="Delete">×</button>
                  </div>`;
            }).join('');
            menuEl.querySelectorAll('.lp-groups-load-one').forEach(el => el.addEventListener('click', () => {
                const g = groups.find(x => x.id === el.dataset.id);
                if (!g) return;
                try { opts.setMembers(g.members || []); } catch (e) { console.error(e); }
                closeMenu();
            }));
            menuEl.querySelectorAll('.lp-groups-del').forEach(el => el.addEventListener('click', async (ev) => {
                ev.stopPropagation();
                if (!confirm(currentLabels.confirmDelete)) return;
                try { await lpDeleteGroup(el.dataset.id); refreshMenu(); }
                catch (e) { alert(e.message || String(e)); }
            }));
        } catch (e) {
            menuEl.innerHTML = `<div class="lp-groups-err">${lpEscape(e.message || String(e))}</div>`;
        }
    }

    function openMenu() { menuEl.hidden = false; refreshMenu(); }
    function closeMenu() { menuEl.hidden = true; }

    loadBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (menuEl.hidden) openMenu(); else closeMenu();
    });
    document.addEventListener('click', (e) => { if (!box.contains(e.target)) closeMenu(); });

    saveBtn.addEventListener('click', async () => {
        const user = await getUser();
        if (!user) { location.href = `/auth/?return=${returnUrl()}`; return; }
        let members;
        try { members = opts.getMembers(); } catch (e) { console.error(e); return; }
        if (!members || !members.length) { alert(currentLabels.noMembers); return; }
        const name = prompt(currentLabels.prompt);
        if (!name || !name.trim()) return;
        try {
            await lpCreateGroup(name.trim().slice(0, 40), members);
            toast(currentLabels.saved);
        } catch (e) { alert(e.message || String(e)); }
    });

    onAuthChange(() => { if (!menuEl.hidden) refreshMenu(); });

    return {
        refresh: refreshMenu,
        setLabels(next) {
            currentLabels = Object.assign({}, L, next || {});
            box.querySelector('[data-role="load-label"]').textContent = currentLabels.load;
            box.querySelector('[data-role="save-label"]').textContent = currentLabels.save;
            if (!menuEl.hidden) refreshMenu();
        },
    };
}
