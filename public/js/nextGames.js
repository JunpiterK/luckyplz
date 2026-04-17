/*
  Lucky Please - "Try another game" cross-promotion
  Auto-mounts on any element with [data-lp-next-games="<current-game-id>"].
  Picks 3 random other games and shows icon cards + a "back to all" link.
*/

(function injectStyles() {
    if (document.getElementById('lp-next-games-styles')) return;
    const s = document.createElement('style');
    s.id = 'lp-next-games-styles';
    s.textContent = `
.lp-next-wrap{margin-top:24px;padding:20px 4px 6px;border-top:1px solid rgba(255,255,255,.08);font-family:'Noto Sans KR',sans-serif}
.lp-next-title{font-family:'Orbitron','Noto Sans KR',sans-serif;font-size:.78em;color:rgba(255,255,255,.5);letter-spacing:2.5px;text-align:center;margin-bottom:14px;font-weight:700}
.lp-next-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;max-width:440px;margin:0 auto}
.lp-next-card{display:flex;flex-direction:column;align-items:center;gap:5px;padding:14px 8px;border-radius:14px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);cursor:pointer;transition:transform .18s,background .25s,border-color .25s;text-decoration:none;color:#fff}
.lp-next-card:hover{background:rgba(255,230,109,.1);border-color:rgba(255,230,109,.45);transform:translateY(-2px)}
.lp-next-icon{font-size:1.8em;line-height:1;margin-bottom:2px}
.lp-next-name{font-size:.76em;font-weight:700;letter-spacing:.02em;color:rgba(255,255,255,.88);text-align:center}
.lp-next-home{display:block;text-align:center;margin-top:14px;font-size:.75em;color:rgba(255,255,255,.45);text-decoration:none;letter-spacing:.02em;transition:color .2s}
.lp-next-home:hover{color:#FFE66D}
@media(max-width:500px){
  .lp-next-wrap{margin-top:18px;padding:14px 2px 4px}
  .lp-next-card{padding:10px 6px}
  .lp-next-icon{font-size:1.5em}
  .lp-next-name{font-size:.68em}
}
`;
    document.head.appendChild(s);
})();

const LP_GAMES = [
    { id: 'lotto', icon: '🎱', url: '/games/lotto/' },
    { id: 'team', icon: '👥', url: '/games/team/' },
    { id: 'car-racing', icon: '🏎️', url: '/games/car-racing/' },
    { id: 'roulette', icon: '🎯', url: '/games/roulette/' },
    { id: 'ladder', icon: '🪜', url: '/games/ladder/' },
    { id: 'dice', icon: '🎲', url: '/games/dice/' },
];

const LP_GAME_NAMES = {
    en: { lotto:'Lotto', team:'Team', 'car-racing':'Race', roulette:'Roulette', ladder:'Ladder', dice:'Dice' },
    gb: { lotto:'Lotto', team:'Team', 'car-racing':'Race', roulette:'Roulette', ladder:'Ladder', dice:'Dice' },
    ko: { lotto:'로또', team:'팀 뽑기', 'car-racing':'카레이싱', roulette:'룰렛', ladder:'사다리', dice:'주사위' },
    ja: { lotto:'ロト', team:'チーム', 'car-racing':'レース', roulette:'ルーレット', ladder:'はしご', dice:'サイコロ' },
    zh: { lotto:'乐透', team:'分队', 'car-racing':'赛车', roulette:'轮盘', ladder:'梯子', dice:'骰子' },
    es: { lotto:'Lotería', team:'Equipos', 'car-racing':'Carrera', roulette:'Ruleta', ladder:'Escalera', dice:'Dados' },
    de: { lotto:'Lotto', team:'Teams', 'car-racing':'Rennen', roulette:'Roulette', ladder:'Leiter', dice:'Würfel' },
    fr: { lotto:'Loto', team:'Équipes', 'car-racing':'Course', roulette:'Roulette', ladder:'Échelle', dice:'Dés' },
    pt: { lotto:'Loteria', team:'Times', 'car-racing':'Corrida', roulette:'Roleta', ladder:'Escada', dice:'Dados' },
    ru: { lotto:'Лото', team:'Команды', 'car-racing':'Гонки', roulette:'Рулетка', ladder:'Лестница', dice:'Кубики' },
    ar: { lotto:'يانصيب', team:'فرق', 'car-racing':'سباق', roulette:'روليت', ladder:'سلم', dice:'نرد' },
    hi: { lotto:'लॉटो', team:'टीम', 'car-racing':'रेस', roulette:'रूलेट', ladder:'सीढ़ी', dice:'पासा' },
    th: { lotto:'ลอตโต', team:'ทีม', 'car-racing':'แข่งรถ', roulette:'รูเล็ต', ladder:'บันได', dice:'เต๋า' },
    id: { lotto:'Undian', team:'Tim', 'car-racing':'Balap', roulette:'Roulette', ladder:'Tangga', dice:'Dadu' },
    vi: { lotto:'Xổ số', team:'Đội', 'car-racing':'Đua xe', roulette:'Vòng quay', ladder:'Thang', dice:'Xúc xắc' },
    tr: { lotto:'Çekiliş', team:'Takım', 'car-racing':'Yarış', roulette:'Rulet', ladder:'Merdiven', dice:'Zar' },
};

const LP_NEXT_TITLE = {
    en: 'TRY ANOTHER GAME', gb: 'TRY ANOTHER GAME',
    ko: '다른 게임도 해볼래?',
    ja: '他のゲームは？',
    zh: '试试其他游戏',
    es: 'PRUEBA OTRO JUEGO',
    de: 'NOCH EIN SPIEL',
    fr: 'UN AUTRE JEU ?',
    pt: 'OUTRO JOGO?',
    ru: 'ЕЩЁ ИГРА?',
    ar: 'لعبة أخرى؟',
    hi: 'दूसरा गेम?',
    th: 'เล่นเกมอื่น',
    id: 'COBA LAIN?',
    vi: 'GAME KHÁC?',
    tr: 'BAŞKA OYUN?',
};

const LP_HOME_LINK = {
    en: '← All games', gb: '← All games',
    ko: '← 전체 게임 보기',
    ja: '← 全ゲーム',
    zh: '← 所有游戏',
    es: '← Todos los juegos',
    de: '← Alle Spiele',
    fr: '← Tous les jeux',
    pt: '← Todos os jogos',
    ru: '← Все игры',
    ar: '← كل الألعاب',
    hi: '← सभी गेम',
    th: '← เกมทั้งหมด',
    id: '← Semua game',
    vi: '← Tất cả game',
    tr: '← Tüm oyunlar',
};

function lpRenderNextGames(container, currentGame, count) {
    if (!container) return;
    count = Math.min(Math.max(2, count || 3), 5);
    const lang = localStorage.getItem('luckyplz_lang') || 'en';
    const names = LP_GAME_NAMES[lang] || LP_GAME_NAMES.en;
    const title = LP_NEXT_TITLE[lang] || LP_NEXT_TITLE.en;
    const homeText = LP_HOME_LINK[lang] || LP_HOME_LINK.en;

    const others = LP_GAMES.filter(g => g.id !== currentGame);
    for (let i = others.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [others[i], others[j]] = [others[j], others[i]];
    }
    const picks = others.slice(0, count);

    container.innerHTML = `
      <div class="lp-next-wrap">
        <div class="lp-next-title">${title}</div>
        <div class="lp-next-grid">
          ${picks.map(g => `
            <a class="lp-next-card" href="${g.url}">
              <span class="lp-next-icon">${g.icon}</span>
              <span class="lp-next-name">${names[g.id] || g.id}</span>
            </a>
          `).join('')}
        </div>
        <a class="lp-next-home" href="/">${homeText}</a>
      </div>
    `;
}

// Auto-mount on page load: find [data-lp-next-games] and render
(function autoMount() {
    function run() {
        document.querySelectorAll('[data-lp-next-games]').forEach(el => {
            lpRenderNextGames(el, el.dataset.lpNextGames, parseInt(el.dataset.lpNextCount) || 3);
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', run);
    } else {
        run();
    }
})();
