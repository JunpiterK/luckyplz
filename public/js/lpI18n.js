/*
  Lucky Please — Shared i18n for Action Games

  공용 모듈 — tetris/snake/burger/pacman/dodge 5개 액션게임이 공통으로
  쓰는 UI 문자열 (Login/Game Over/Retry/Score/Level 등) 의 16 언어
  번역. 각 게임은 게임별 unique 문자열만 inline I18N 으로 추가.

  사용:
    const t = LpI18n.T('login');             // → 현재 lang 의 "로그인" 등
    const lang = LpI18n.getLang();           // → 'ko' / 'en' / ...
    LpI18n.onChange(() => applyLanguage());  // → lang 바뀌면 콜백

  지원 언어 (16): en, ko, ja, zh, es, gb, de, fr, pt, ru, ar, hi, th,
                  id, vi, tr (utility 게임 lotto/ladder 와 동일).
*/

(function(){
    'use strict';

    /* 액션게임 공통 dictionary — 게임별 inline I18N 이 같은 키 정의하면
       inline 이 우선 (per-game override). T(key, gameI18n) 형태로 호출
       하면 gameI18n 부터 먼저 lookup. */
    const I18N = {
        en: {
            home: 'Home', login: 'Login', loginNeeded: '🔒 Login to save your record!',
            start: 'Start', play: 'Play', retry: 'Try Again', restart: 'Restart',
            pause: 'Pause', resume: 'Resume', gameOver: 'GAME OVER',
            score: 'SCORE', best: 'BEST', time: 'TIME', lines: 'LINES',
            level: 'LEVEL', mode: 'MODE', rank: 'Rank', rankBtn: '🏆 Rank',
            you: 'You', myBest: '🎉 New best!', priorBest: 'Best',
            recording: 'Saving record…', worldRank: '🌍 #',
            firstRecord: '🎉 First record!', rankFailed: '🌍 Rank lookup failed',
            rateLimited: '⏱ 30/hour limit', invalidScore: '⚠️ Score invalid',
            authNeeded: '🔐 Login required', recordFailed: '⚠️ Save failed',
            move: 'Move', rotate: 'Rotate', drop: 'Drop',
            left: 'Left', right: 'Right', soft: 'Soft drop', hard: 'Hard drop',
            hold: 'Hold', release: 'Release',
            keyboardGuide: 'Keyboard guide', ranking: 'Ranking',
            bgmOn: 'BGM On', bgmOff: 'BGM Off',
            world: 'World', today: 'Today', friends: 'Friends',
            loading: 'Loading…'
        },
        ko: {
            home: '홈', login: '로그인', loginNeeded: '🔒 로그인하면 기록 저장!',
            start: '시작', play: '플레이', retry: '다시 도전', restart: '재시작',
            pause: '일시정지', resume: '재개', gameOver: '게임 오버',
            score: '점수', best: '최고', time: '시간', lines: '라인',
            level: '레벨', mode: '모드', rank: '랭크', rankBtn: '🏆 랭크',
            you: '나', myBest: '🎉 자기 최고 기록!', priorBest: '베스트',
            recording: '기록 등록 중…', worldRank: '🌍 #',
            firstRecord: '🎉 첫 기록!', rankFailed: '🌍 랭킹 조회 실패',
            rateLimited: '⏱ 시간당 30회 초과', invalidScore: '⚠️ 점수 검증 실패',
            authNeeded: '🔐 로그인이 필요해요', recordFailed: '⚠️ 기록 저장 실패',
            move: '이동', rotate: '회전', drop: '드롭',
            left: '왼쪽', right: '오른쪽', soft: '소프트', hard: '하드',
            hold: '홀드', release: '해제',
            keyboardGuide: '키보드 가이드', ranking: '랭킹',
            bgmOn: 'BGM 켬', bgmOff: 'BGM 끔',
            world: '월드', today: '오늘', friends: '친구',
            loading: '불러오는 중…'
        },
        ja: {
            home: 'ホーム', login: 'ログイン', loginNeeded: '🔒 ログインで記録保存!',
            start: 'スタート', play: 'プレイ', retry: 'リトライ', restart: '再スタート',
            pause: '一時停止', resume: '再開', gameOver: 'ゲームオーバー',
            score: 'スコア', best: 'ベスト', time: 'タイム', lines: 'ライン',
            level: 'レベル', mode: 'モード', rank: 'ランク', rankBtn: '🏆 ランク',
            you: '私', myBest: '🎉 自己ベスト!', priorBest: 'ベスト',
            recording: '記録登録中…', worldRank: '🌍 #',
            firstRecord: '🎉 初記録!', rankFailed: '🌍 ランキング取得失敗',
            rateLimited: '⏱ 1時間30回まで', invalidScore: '⚠️ スコア不正',
            authNeeded: '🔐 ログインが必要', recordFailed: '⚠️ 保存失敗',
            move: '移動', rotate: '回転', drop: 'ドロップ',
            left: '左', right: '右', soft: 'ソフト', hard: 'ハード',
            hold: 'ホールド', release: 'リリース',
            keyboardGuide: 'キー操作', ranking: 'ランキング',
            bgmOn: 'BGM オン', bgmOff: 'BGM オフ',
            world: '世界', today: '今日', friends: 'フレンド',
            loading: '読み込み中…'
        },
        zh: {
            home: '主页', login: '登录', loginNeeded: '🔒 登录以保存记录!',
            start: '开始', play: '玩', retry: '再试一次', restart: '重新开始',
            pause: '暂停', resume: '继续', gameOver: '游戏结束',
            score: '得分', best: '最佳', time: '时间', lines: '行',
            level: '关卡', mode: '模式', rank: '排名', rankBtn: '🏆 排名',
            you: '我', myBest: '🎉 个人最佳!', priorBest: '最佳',
            recording: '保存记录中…', worldRank: '🌍 #',
            firstRecord: '🎉 首次记录!', rankFailed: '🌍 排名查询失败',
            rateLimited: '⏱ 每小时30次限制', invalidScore: '⚠️ 分数无效',
            authNeeded: '🔐 需要登录', recordFailed: '⚠️ 保存失败',
            move: '移动', rotate: '旋转', drop: '掉落',
            left: '左', right: '右', soft: '软降', hard: '硬降',
            hold: '保留', release: '释放',
            keyboardGuide: '键盘指南', ranking: '排行榜',
            bgmOn: 'BGM 开', bgmOff: 'BGM 关',
            world: '世界', today: '今日', friends: '好友',
            loading: '加载中…'
        },
        es: {
            home: 'Inicio', login: 'Acceder', loginNeeded: '🔒 ¡Inicia sesión para guardar récords!',
            start: 'Iniciar', play: 'Jugar', retry: 'Reintentar', restart: 'Reiniciar',
            pause: 'Pausa', resume: 'Reanudar', gameOver: 'FIN DEL JUEGO',
            score: 'PUNTOS', best: 'MEJOR', time: 'TIEMPO', lines: 'LÍNEAS',
            level: 'NIVEL', mode: 'MODO', rank: 'Rango', rankBtn: '🏆 Rango',
            you: 'Tú', myBest: '🎉 ¡Récord personal!', priorBest: 'Mejor',
            recording: 'Guardando…', worldRank: '🌍 #',
            firstRecord: '🎉 ¡Primer récord!', rankFailed: '🌍 Error al consultar rango',
            rateLimited: '⏱ Límite 30/hora', invalidScore: '⚠️ Puntuación no válida',
            authNeeded: '🔐 Necesita iniciar sesión', recordFailed: '⚠️ Error al guardar',
            move: 'Mover', rotate: 'Girar', drop: 'Soltar',
            left: 'Izq.', right: 'Der.', soft: 'Suave', hard: 'Fuerte',
            hold: 'Reservar', release: 'Liberar',
            keyboardGuide: 'Guía de teclado', ranking: 'Clasificación',
            bgmOn: 'Música On', bgmOff: 'Música Off',
            world: 'Mundo', today: 'Hoy', friends: 'Amigos',
            loading: 'Cargando…'
        },
        gb: {
            home: 'Home', login: 'Login', loginNeeded: '🔒 Login to save your record!',
            start: 'Start', play: 'Play', retry: 'Try Again', restart: 'Restart',
            pause: 'Pause', resume: 'Resume', gameOver: 'GAME OVER',
            score: 'SCORE', best: 'BEST', time: 'TIME', lines: 'LINES',
            level: 'LEVEL', mode: 'MODE', rank: 'Rank', rankBtn: '🏆 Rank',
            you: 'You', myBest: '🎉 New best!', priorBest: 'Best',
            recording: 'Saving record…', worldRank: '🌍 #',
            firstRecord: '🎉 First record!', rankFailed: '🌍 Rank lookup failed',
            rateLimited: '⏱ 30/hour limit', invalidScore: '⚠️ Score invalid',
            authNeeded: '🔐 Login required', recordFailed: '⚠️ Save failed',
            move: 'Move', rotate: 'Rotate', drop: 'Drop',
            left: 'Left', right: 'Right', soft: 'Soft drop', hard: 'Hard drop',
            hold: 'Hold', release: 'Release',
            keyboardGuide: 'Keyboard guide', ranking: 'Ranking',
            bgmOn: 'BGM On', bgmOff: 'BGM Off',
            world: 'World', today: 'Today', friends: 'Friends',
            loading: 'Loading…'
        },
        de: {
            home: 'Start', login: 'Anmelden', loginNeeded: '🔒 Anmelden zum Speichern!',
            start: 'Start', play: 'Spielen', retry: 'Nochmal', restart: 'Neu starten',
            pause: 'Pause', resume: 'Fortsetzen', gameOver: 'SPIEL VORBEI',
            score: 'PUNKTE', best: 'BESTE', time: 'ZEIT', lines: 'LINIEN',
            level: 'STUFE', mode: 'MODUS', rank: 'Rang', rankBtn: '🏆 Rang',
            you: 'Ich', myBest: '🎉 Neuer Bestwert!', priorBest: 'Beste',
            recording: 'Speichern…', worldRank: '🌍 #',
            firstRecord: '🎉 Erster Eintrag!', rankFailed: '🌍 Rang-Abfrage fehlgeschlagen',
            rateLimited: '⏱ Limit 30/Stunde', invalidScore: '⚠️ Punkte ungültig',
            authNeeded: '🔐 Anmeldung erforderlich', recordFailed: '⚠️ Speichern fehlgeschlagen',
            move: 'Bewegen', rotate: 'Drehen', drop: 'Fallen',
            left: 'Links', right: 'Rechts', soft: 'Sanft', hard: 'Hart',
            hold: 'Halten', release: 'Auslösen',
            keyboardGuide: 'Tastatur-Hilfe', ranking: 'Rangliste',
            bgmOn: 'Musik An', bgmOff: 'Musik Aus',
            world: 'Welt', today: 'Heute', friends: 'Freunde',
            loading: 'Lädt…'
        },
        fr: {
            home: 'Accueil', login: 'Connexion', loginNeeded: '🔒 Connectez-vous pour sauvegarder !',
            start: 'Commencer', play: 'Jouer', retry: 'Réessayer', restart: 'Redémarrer',
            pause: 'Pause', resume: 'Reprendre', gameOver: 'PARTIE TERMINÉE',
            score: 'SCORE', best: 'MEILLEUR', time: 'TEMPS', lines: 'LIGNES',
            level: 'NIVEAU', mode: 'MODE', rank: 'Rang', rankBtn: '🏆 Rang',
            you: 'Moi', myBest: '🎉 Record personnel !', priorBest: 'Meilleur',
            recording: 'Enregistrement…', worldRank: '🌍 #',
            firstRecord: '🎉 Premier record !', rankFailed: '🌍 Échec de la requête',
            rateLimited: '⏱ Limite 30/heure', invalidScore: '⚠️ Score invalide',
            authNeeded: '🔐 Connexion requise', recordFailed: '⚠️ Échec sauvegarde',
            move: 'Bouger', rotate: 'Tourner', drop: 'Lâcher',
            left: 'Gauche', right: 'Droite', soft: 'Doux', hard: 'Fort',
            hold: 'Garder', release: 'Lâcher',
            keyboardGuide: 'Clavier', ranking: 'Classement',
            bgmOn: 'Musique On', bgmOff: 'Musique Off',
            world: 'Monde', today: 'Aujourd\'hui', friends: 'Amis',
            loading: 'Chargement…'
        },
        pt: {
            home: 'Início', login: 'Entrar', loginNeeded: '🔒 Entre para salvar!',
            start: 'Iniciar', play: 'Jogar', retry: 'Tentar de novo', restart: 'Reiniciar',
            pause: 'Pausar', resume: 'Continuar', gameOver: 'FIM DE JOGO',
            score: 'PONTOS', best: 'MELHOR', time: 'TEMPO', lines: 'LINHAS',
            level: 'NÍVEL', mode: 'MODO', rank: 'Rank', rankBtn: '🏆 Rank',
            you: 'Eu', myBest: '🎉 Novo recorde!', priorBest: 'Melhor',
            recording: 'Salvando…', worldRank: '🌍 #',
            firstRecord: '🎉 Primeiro recorde!', rankFailed: '🌍 Falha ao consultar',
            rateLimited: '⏱ Limite 30/hora', invalidScore: '⚠️ Pontuação inválida',
            authNeeded: '🔐 Login necessário', recordFailed: '⚠️ Falha ao salvar',
            move: 'Mover', rotate: 'Girar', drop: 'Soltar',
            left: 'Esq.', right: 'Dir.', soft: 'Suave', hard: 'Forte',
            hold: 'Manter', release: 'Soltar',
            keyboardGuide: 'Guia de teclado', ranking: 'Ranking',
            bgmOn: 'Música On', bgmOff: 'Música Off',
            world: 'Mundo', today: 'Hoje', friends: 'Amigos',
            loading: 'Carregando…'
        },
        ru: {
            home: 'Главная', login: 'Войти', loginNeeded: '🔒 Войдите, чтобы сохранить!',
            start: 'Старт', play: 'Играть', retry: 'Ещё раз', restart: 'Перезапуск',
            pause: 'Пауза', resume: 'Продолжить', gameOver: 'ИГРА ОКОНЧЕНА',
            score: 'ОЧКИ', best: 'ЛУЧШИЙ', time: 'ВРЕМЯ', lines: 'ЛИНИИ',
            level: 'УРОВЕНЬ', mode: 'РЕЖИМ', rank: 'Ранг', rankBtn: '🏆 Ранг',
            you: 'Я', myBest: '🎉 Личный рекорд!', priorBest: 'Лучший',
            recording: 'Сохранение…', worldRank: '🌍 #',
            firstRecord: '🎉 Первый рекорд!', rankFailed: '🌍 Ошибка запроса',
            rateLimited: '⏱ Лимит 30/час', invalidScore: '⚠️ Очки недействительны',
            authNeeded: '🔐 Требуется вход', recordFailed: '⚠️ Сохранение не удалось',
            move: 'Двигать', rotate: 'Вращать', drop: 'Бросить',
            left: 'Лево', right: 'Право', soft: 'Мягко', hard: 'Жёстко',
            hold: 'Держать', release: 'Отпустить',
            keyboardGuide: 'Клавиатура', ranking: 'Рейтинг',
            bgmOn: 'Музыка Вкл', bgmOff: 'Музыка Выкл',
            world: 'Мир', today: 'Сегодня', friends: 'Друзья',
            loading: 'Загрузка…'
        },
        ar: {
            home: 'الرئيسية', login: 'تسجيل الدخول', loginNeeded: '🔒 سجّل الدخول لحفظ السجل!',
            start: 'ابدأ', play: 'لعب', retry: 'حاول مجددًا', restart: 'إعادة',
            pause: 'إيقاف', resume: 'متابعة', gameOver: 'انتهت اللعبة',
            score: 'النقاط', best: 'الأفضل', time: 'الوقت', lines: 'الأسطر',
            level: 'المستوى', mode: 'الوضع', rank: 'الترتيب', rankBtn: '🏆 الترتيب',
            you: 'أنا', myBest: '🎉 رقم قياسي!', priorBest: 'الأفضل',
            recording: 'جارٍ الحفظ…', worldRank: '🌍 #',
            firstRecord: '🎉 أول سجل!', rankFailed: '🌍 فشل البحث',
            rateLimited: '⏱ 30 محاولة/ساعة', invalidScore: '⚠️ نتيجة غير صالحة',
            authNeeded: '🔐 يجب تسجيل الدخول', recordFailed: '⚠️ فشل الحفظ',
            move: 'تحريك', rotate: 'تدوير', drop: 'إسقاط',
            left: 'يسار', right: 'يمين', soft: 'ناعم', hard: 'قوي',
            hold: 'إمساك', release: 'إفلات',
            keyboardGuide: 'دليل لوحة المفاتيح', ranking: 'التصنيف',
            bgmOn: 'الموسيقى ✓', bgmOff: 'الموسيقى ✕',
            world: 'عالمي', today: 'اليوم', friends: 'الأصدقاء',
            loading: 'جارٍ التحميل…'
        },
        hi: {
            home: 'मुख्य', login: 'लॉगिन', loginNeeded: '🔒 रिकॉर्ड सहेजने के लिए लॉगिन करें!',
            start: 'शुरू', play: 'खेलें', retry: 'पुनः प्रयास', restart: 'फिर शुरू',
            pause: 'रुकें', resume: 'जारी', gameOver: 'खेल समाप्त',
            score: 'अंक', best: 'सर्वश्रेष्ठ', time: 'समय', lines: 'पंक्ति',
            level: 'स्तर', mode: 'मोड', rank: 'रैंक', rankBtn: '🏆 रैंक',
            you: 'मैं', myBest: '🎉 नया रिकॉर्ड!', priorBest: 'सर्वश्रेष्ठ',
            recording: 'सहेज रहा है…', worldRank: '🌍 #',
            firstRecord: '🎉 पहला रिकॉर्ड!', rankFailed: '🌍 रैंक विफल',
            rateLimited: '⏱ 30/घंटा सीमा', invalidScore: '⚠️ अंक अमान्य',
            authNeeded: '🔐 लॉगिन आवश्यक', recordFailed: '⚠️ सहेजना विफल',
            move: 'चलें', rotate: 'घुमाएँ', drop: 'गिराएँ',
            left: 'बाएँ', right: 'दाएँ', soft: 'मुलायम', hard: 'कठिन',
            hold: 'रखें', release: 'छोड़ें',
            keyboardGuide: 'कीबोर्ड', ranking: 'रैंकिंग',
            bgmOn: 'संगीत चालू', bgmOff: 'संगीत बंद',
            world: 'विश्व', today: 'आज', friends: 'मित्र',
            loading: 'लोड हो रहा है…'
        },
        th: {
            home: 'หน้าแรก', login: 'เข้าสู่ระบบ', loginNeeded: '🔒 เข้าสู่ระบบเพื่อบันทึก!',
            start: 'เริ่ม', play: 'เล่น', retry: 'ลองอีกครั้ง', restart: 'เริ่มใหม่',
            pause: 'หยุด', resume: 'เล่นต่อ', gameOver: 'จบเกม',
            score: 'คะแนน', best: 'ดีที่สุด', time: 'เวลา', lines: 'แถว',
            level: 'เลเวล', mode: 'โหมด', rank: 'อันดับ', rankBtn: '🏆 อันดับ',
            you: 'ฉัน', myBest: '🎉 สถิติใหม่!', priorBest: 'ดีที่สุด',
            recording: 'กำลังบันทึก…', worldRank: '🌍 #',
            firstRecord: '🎉 บันทึกแรก!', rankFailed: '🌍 ดึงอันดับล้มเหลว',
            rateLimited: '⏱ จำกัด 30/ชม.', invalidScore: '⚠️ คะแนนไม่ถูกต้อง',
            authNeeded: '🔐 ต้องเข้าสู่ระบบ', recordFailed: '⚠️ บันทึกล้มเหลว',
            move: 'เคลื่อน', rotate: 'หมุน', drop: 'ปล่อย',
            left: 'ซ้าย', right: 'ขวา', soft: 'นุ่ม', hard: 'แรง',
            hold: 'เก็บ', release: 'ปล่อย',
            keyboardGuide: 'คีย์บอร์ด', ranking: 'จัดอันดับ',
            bgmOn: 'BGM เปิด', bgmOff: 'BGM ปิด',
            world: 'โลก', today: 'วันนี้', friends: 'เพื่อน',
            loading: 'กำลังโหลด…'
        },
        id: {
            home: 'Beranda', login: 'Masuk', loginNeeded: '🔒 Masuk untuk simpan rekor!',
            start: 'Mulai', play: 'Main', retry: 'Coba lagi', restart: 'Mulai ulang',
            pause: 'Jeda', resume: 'Lanjut', gameOver: 'PERMAINAN BERAKHIR',
            score: 'SKOR', best: 'TERBAIK', time: 'WAKTU', lines: 'BARIS',
            level: 'LEVEL', mode: 'MODE', rank: 'Peringkat', rankBtn: '🏆 Peringkat',
            you: 'Saya', myBest: '🎉 Rekor pribadi!', priorBest: 'Terbaik',
            recording: 'Menyimpan…', worldRank: '🌍 #',
            firstRecord: '🎉 Rekor pertama!', rankFailed: '🌍 Gagal cek peringkat',
            rateLimited: '⏱ Batas 30/jam', invalidScore: '⚠️ Skor tidak valid',
            authNeeded: '🔐 Perlu masuk', recordFailed: '⚠️ Gagal simpan',
            move: 'Gerak', rotate: 'Putar', drop: 'Jatuh',
            left: 'Kiri', right: 'Kanan', soft: 'Lembut', hard: 'Keras',
            hold: 'Tahan', release: 'Lepas',
            keyboardGuide: 'Papan tombol', ranking: 'Peringkat',
            bgmOn: 'BGM On', bgmOff: 'BGM Off',
            world: 'Dunia', today: 'Hari ini', friends: 'Teman',
            loading: 'Memuat…'
        },
        vi: {
            home: 'Trang chủ', login: 'Đăng nhập', loginNeeded: '🔒 Đăng nhập để lưu kỷ lục!',
            start: 'Bắt đầu', play: 'Chơi', retry: 'Thử lại', restart: 'Khởi động lại',
            pause: 'Tạm dừng', resume: 'Tiếp tục', gameOver: 'KẾT THÚC',
            score: 'ĐIỂM', best: 'TỐT NHẤT', time: 'THỜI GIAN', lines: 'HÀNG',
            level: 'CẤP', mode: 'CHẾ ĐỘ', rank: 'Xếp hạng', rankBtn: '🏆 Xếp hạng',
            you: 'Tôi', myBest: '🎉 Kỷ lục mới!', priorBest: 'Tốt nhất',
            recording: 'Đang lưu…', worldRank: '🌍 #',
            firstRecord: '🎉 Kỷ lục đầu tiên!', rankFailed: '🌍 Tra cứu thất bại',
            rateLimited: '⏱ Giới hạn 30/giờ', invalidScore: '⚠️ Điểm không hợp lệ',
            authNeeded: '🔐 Cần đăng nhập', recordFailed: '⚠️ Lưu thất bại',
            move: 'Di chuyển', rotate: 'Xoay', drop: 'Thả',
            left: 'Trái', right: 'Phải', soft: 'Nhẹ', hard: 'Mạnh',
            hold: 'Giữ', release: 'Thả',
            keyboardGuide: 'Bàn phím', ranking: 'Xếp hạng',
            bgmOn: 'Nhạc Bật', bgmOff: 'Nhạc Tắt',
            world: 'Thế giới', today: 'Hôm nay', friends: 'Bạn bè',
            loading: 'Đang tải…'
        },
        tr: {
            home: 'Ana Sayfa', login: 'Giriş', loginNeeded: '🔒 Kaydı korumak için giriş yapın!',
            start: 'Başla', play: 'Oyna', retry: 'Tekrar dene', restart: 'Yeniden başlat',
            pause: 'Duraklat', resume: 'Devam et', gameOver: 'OYUN BİTTİ',
            score: 'PUAN', best: 'EN İYİ', time: 'SÜRE', lines: 'SATIR',
            level: 'SEVİYE', mode: 'MOD', rank: 'Sıralama', rankBtn: '🏆 Sıra',
            you: 'Ben', myBest: '🎉 Yeni rekor!', priorBest: 'En iyi',
            recording: 'Kaydediliyor…', worldRank: '🌍 #',
            firstRecord: '🎉 İlk kayıt!', rankFailed: '🌍 Sıralama alınamadı',
            rateLimited: '⏱ 30/saat sınırı', invalidScore: '⚠️ Puan geçersiz',
            authNeeded: '🔐 Giriş gerekli', recordFailed: '⚠️ Kayıt başarısız',
            move: 'Hareket', rotate: 'Döndür', drop: 'Bırak',
            left: 'Sol', right: 'Sağ', soft: 'Yumuşak', hard: 'Sert',
            hold: 'Tut', release: 'Bırak',
            keyboardGuide: 'Klavye', ranking: 'Sıralama',
            bgmOn: 'Müzik Açık', bgmOff: 'Müzik Kapalı',
            world: 'Dünya', today: 'Bugün', friends: 'Arkadaşlar',
            loading: 'Yükleniyor…'
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

    /* T(key, gameOverride) — gameOverride 가 객체 ({ko: {...}, en: {...}})
       이면 게임 dictionary 우선 lookup. 없으면 공용 I18N. fallback 영어. */
    function T(key, gameOverride){
        const l = getLang();
        if(gameOverride && gameOverride[l] && gameOverride[l][key] != null){
            return gameOverride[l][key];
        }
        if(gameOverride && gameOverride.en && gameOverride.en[key] != null){
            return gameOverride.en[key];
        }
        return (I18N[l] && I18N[l][key]) || (I18N.en[key]) || key;
    }

    /* setLang(lang) — localStorage 저장 + listeners 호출 */
    const _listeners = [];
    function setLang(lang){
        if(!I18N[lang]) lang = 'en';
        try { localStorage.setItem('luckyplz_lang', lang); } catch(_){}
        _listeners.forEach(fn => { try { fn(lang); } catch(_){} });
    }
    function onChange(fn){
        if(typeof fn === 'function') _listeners.push(fn);
    }

    /* Standard 16-button lang bar HTML (게임마다 동일).
       각 게임이 #langBar 컨테이너 두고 LpI18n.injectLangBar(barEl) 호출
       하면 16 버튼 자동 삽입 + 클릭 핸들러 wire. */
    const LANG_FLAGS = {
        en: 'us', ko: 'kr', ja: 'jp', zh: 'cn', es: 'es',
        gb: 'gb', de: 'de', fr: 'fr', pt: 'pt', ru: 'ru',
        ar: 'sa', hi: 'in', th: 'th', id: 'id', vi: 'vn', tr: 'tr'
    };
    function injectLangBar(barEl){
        if(!barEl) return;
        const cur = getLang();
        barEl.innerHTML = Object.keys(I18N).map(code =>
            '<button class="lang-btn'+(code===cur?' active':'')+'" data-lang="'+code+'" type="button" aria-label="'+code+'">'
            + '<img src="https://flagcdn.com/w40/'+LANG_FLAGS[code]+'.png" alt="'+code+'" width="20" height="14" loading="lazy"/>'
            + '</button>'
        ).join('');
        barEl.addEventListener('click', (e) => {
            const btn = e.target.closest('.lang-btn');
            if(!btn) return;
            const code = btn.dataset.lang;
            if(!code || !I18N[code]) return;
            setLang(code);
            barEl.querySelectorAll('.lang-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.lang === code);
            });
        });
    }

    window.LpI18n = { T, getLang, setLang, onChange, injectLangBar, LANGS: Object.keys(I18N) };
})();
