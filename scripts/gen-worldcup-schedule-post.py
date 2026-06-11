#!/usr/bin/env python3
"""Generate the 4-language "World Cup 2026 group stage full schedule" post.

Single source of truth: MATCHES below stores every group-stage match as
(group, local_date, local_time_24h, utc_offset_hours, team1, team2, venue).
Local kickoff times + offsets were transcribed from the per-group Wikipedia
articles (2026 FIFA World Cup Group A..L, fetched 2026-06-11); each page was
double-fetched and cross-checked. UTC and each language edition's display
time (KST / JST / Beijing / US ET) are COMPUTED here, never hand-converted.

Sanity checks run on every build: 72 matches, 6 per group, every team
exactly 3, and both matchday-3 games of each group share one UTC kickoff.

Output: public/blog/worldcup-2026-group-stage-schedule[/-en/-ja/-zh]/index.html
Re-run any time the schedule data needs a correction.
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "public" / "blog"
SLUG = "worldcup-2026-group-stage-schedule"

BUILD_STAMP = json.loads((ROOT / "public" / "build.json").read_text())["v"]

# --------------------------------------------------------------- match data --
# (group, date, "HH:MM" venue-local 24h, utc_offset, team1, team2, venue_key)
MATCHES = [
    ("A", "2026-06-11", "13:00", -6, "mex", "rsa", "azteca"),
    ("A", "2026-06-11", "20:00", -6, "kor", "cze", "akron"),
    ("A", "2026-06-18", "12:00", -4, "cze", "rsa", "mercedes"),
    ("A", "2026-06-18", "19:00", -6, "mex", "kor", "akron"),
    ("A", "2026-06-24", "19:00", -6, "cze", "mex", "azteca"),
    ("A", "2026-06-24", "19:00", -6, "rsa", "kor", "bbva"),

    ("B", "2026-06-12", "15:00", -4, "can", "bih", "bmo"),
    ("B", "2026-06-13", "12:00", -7, "qat", "sui", "levis"),
    ("B", "2026-06-18", "12:00", -7, "sui", "bih", "sofi"),
    ("B", "2026-06-18", "15:00", -7, "can", "qat", "bcplace"),
    ("B", "2026-06-24", "12:00", -7, "sui", "can", "bcplace"),
    ("B", "2026-06-24", "12:00", -7, "bih", "qat", "lumen"),

    ("C", "2026-06-13", "18:00", -4, "bra", "mar", "metlife"),
    ("C", "2026-06-13", "21:00", -4, "hai", "sco", "gillette"),
    ("C", "2026-06-19", "18:00", -4, "sco", "mar", "gillette"),
    ("C", "2026-06-19", "20:30", -4, "bra", "hai", "linc"),
    ("C", "2026-06-24", "18:00", -4, "sco", "bra", "hardrock"),
    ("C", "2026-06-24", "18:00", -4, "mar", "hai", "mercedes"),

    ("D", "2026-06-12", "18:00", -7, "usa", "par", "sofi"),
    ("D", "2026-06-13", "21:00", -7, "aus", "tur", "bcplace"),
    ("D", "2026-06-19", "12:00", -7, "usa", "aus", "lumen"),
    ("D", "2026-06-19", "20:00", -7, "tur", "par", "levis"),
    ("D", "2026-06-25", "19:00", -7, "tur", "usa", "sofi"),
    ("D", "2026-06-25", "19:00", -7, "par", "aus", "levis"),

    ("E", "2026-06-14", "12:00", -5, "ger", "cuw", "nrg"),
    ("E", "2026-06-14", "19:00", -4, "civ", "ecu", "linc"),
    ("E", "2026-06-20", "16:00", -4, "ger", "civ", "bmo"),
    ("E", "2026-06-20", "19:00", -5, "ecu", "cuw", "arrowhead"),
    ("E", "2026-06-25", "16:00", -4, "cuw", "civ", "linc"),
    ("E", "2026-06-25", "16:00", -4, "ecu", "ger", "metlife"),

    ("F", "2026-06-14", "15:00", -5, "ned", "jpn", "att"),
    ("F", "2026-06-14", "20:00", -6, "swe", "tun", "bbva"),
    ("F", "2026-06-20", "12:00", -5, "ned", "swe", "nrg"),
    ("F", "2026-06-20", "22:00", -6, "tun", "jpn", "bbva"),
    ("F", "2026-06-25", "18:00", -5, "jpn", "swe", "att"),
    ("F", "2026-06-25", "18:00", -5, "tun", "ned", "arrowhead"),

    ("G", "2026-06-15", "12:00", -7, "bel", "egy", "lumen"),
    ("G", "2026-06-15", "18:00", -7, "irn", "nzl", "sofi"),
    ("G", "2026-06-21", "12:00", -7, "bel", "irn", "sofi"),
    ("G", "2026-06-21", "18:00", -7, "nzl", "egy", "bcplace"),
    ("G", "2026-06-26", "20:00", -7, "egy", "irn", "lumen"),
    ("G", "2026-06-26", "20:00", -7, "nzl", "bel", "bcplace"),

    ("H", "2026-06-15", "12:00", -4, "esp", "cpv", "mercedes"),
    ("H", "2026-06-15", "18:00", -4, "ksa", "uru", "hardrock"),
    ("H", "2026-06-21", "12:00", -4, "esp", "ksa", "mercedes"),
    ("H", "2026-06-21", "18:00", -4, "uru", "cpv", "hardrock"),
    ("H", "2026-06-26", "19:00", -5, "cpv", "ksa", "nrg"),
    ("H", "2026-06-26", "18:00", -6, "uru", "esp", "akron"),

    ("I", "2026-06-16", "15:00", -4, "fra", "sen", "metlife"),
    ("I", "2026-06-16", "18:00", -4, "irq", "nor", "gillette"),
    ("I", "2026-06-22", "17:00", -4, "fra", "irq", "linc"),
    ("I", "2026-06-22", "20:00", -4, "nor", "sen", "metlife"),
    ("I", "2026-06-26", "15:00", -4, "nor", "fra", "gillette"),
    ("I", "2026-06-26", "15:00", -4, "sen", "irq", "bmo"),

    ("J", "2026-06-16", "20:00", -5, "arg", "alg", "arrowhead"),
    ("J", "2026-06-16", "21:00", -7, "aut", "jor", "levis"),
    ("J", "2026-06-22", "12:00", -5, "arg", "aut", "att"),
    ("J", "2026-06-22", "20:00", -7, "jor", "alg", "levis"),
    ("J", "2026-06-27", "21:00", -5, "alg", "aut", "arrowhead"),
    ("J", "2026-06-27", "21:00", -5, "jor", "arg", "att"),

    ("K", "2026-06-17", "12:00", -5, "por", "cod", "nrg"),
    ("K", "2026-06-17", "20:00", -6, "uzb", "col", "azteca"),
    ("K", "2026-06-23", "12:00", -5, "por", "uzb", "nrg"),
    ("K", "2026-06-23", "20:00", -6, "col", "cod", "akron"),
    ("K", "2026-06-27", "19:30", -4, "col", "por", "hardrock"),
    ("K", "2026-06-27", "19:30", -4, "cod", "uzb", "mercedes"),

    ("L", "2026-06-17", "15:00", -5, "eng", "cro", "att"),
    ("L", "2026-06-17", "19:00", -4, "gha", "pan", "bmo"),
    ("L", "2026-06-23", "16:00", -4, "eng", "gha", "gillette"),
    ("L", "2026-06-23", "19:00", -4, "pan", "cro", "bmo"),
    ("L", "2026-06-27", "17:00", -4, "pan", "eng", "metlife"),
    ("L", "2026-06-27", "17:00", -4, "cro", "gha", "linc"),
]

# --------------------------------------------------------------- dictionaries --
TEAMS = {
    "mex": ("🇲🇽", "멕시코", "Mexico", "メキシコ", "墨西哥"),
    "rsa": ("🇿🇦", "남아공", "South Africa", "南アフリカ", "南非"),
    "kor": ("🇰🇷", "대한민국", "South Korea", "韓国", "韩国"),
    "cze": ("🇨🇿", "체코", "Czech Republic", "チェコ", "捷克"),
    "can": ("🇨🇦", "캐나다", "Canada", "カナダ", "加拿大"),
    "bih": ("🇧🇦", "보스니아", "Bosnia & Herzegovina", "ボスニア", "波黑"),
    "qat": ("🇶🇦", "카타르", "Qatar", "カタール", "卡塔尔"),
    "sui": ("🇨🇭", "스위스", "Switzerland", "スイス", "瑞士"),
    "bra": ("🇧🇷", "브라질", "Brazil", "ブラジル", "巴西"),
    "mar": ("🇲🇦", "모로코", "Morocco", "モロッコ", "摩洛哥"),
    "hai": ("🇭🇹", "아이티", "Haiti", "ハイチ", "海地"),
    "sco": ("🏴󠁧󠁢󠁳󠁣󠁴󠁿", "스코틀랜드", "Scotland", "スコットランド", "苏格兰"),
    "usa": ("🇺🇸", "미국", "United States", "アメリカ", "美国"),
    "par": ("🇵🇾", "파라과이", "Paraguay", "パラグアイ", "巴拉圭"),
    "aus": ("🇦🇺", "호주", "Australia", "オーストラリア", "澳大利亚"),
    "tur": ("🇹🇷", "튀르키예", "Türkiye", "トルコ", "土耳其"),
    "ger": ("🇩🇪", "독일", "Germany", "ドイツ", "德国"),
    "cuw": ("🇨🇼", "퀴라소", "Curaçao", "キュラソー", "库拉索"),
    "civ": ("🇨🇮", "코트디부아르", "Ivory Coast", "コートジボワール", "科特迪瓦"),
    "ecu": ("🇪🇨", "에콰도르", "Ecuador", "エクアドル", "厄瓜多尔"),
    "ned": ("🇳🇱", "네덜란드", "Netherlands", "オランダ", "荷兰"),
    "jpn": ("🇯🇵", "일본", "Japan", "日本", "日本"),
    "swe": ("🇸🇪", "스웨덴", "Sweden", "スウェーデン", "瑞典"),
    "tun": ("🇹🇳", "튀니지", "Tunisia", "チュニジア", "突尼斯"),
    "bel": ("🇧🇪", "벨기에", "Belgium", "ベルギー", "比利时"),
    "egy": ("🇪🇬", "이집트", "Egypt", "エジプト", "埃及"),
    "irn": ("🇮🇷", "이란", "Iran", "イラン", "伊朗"),
    "nzl": ("🇳🇿", "뉴질랜드", "New Zealand", "ニュージーランド", "新西兰"),
    "esp": ("🇪🇸", "스페인", "Spain", "スペイン", "西班牙"),
    "cpv": ("🇨🇻", "카보베르데", "Cape Verde", "カーボベルデ", "佛得角"),
    "ksa": ("🇸🇦", "사우디", "Saudi Arabia", "サウジアラビア", "沙特"),
    "uru": ("🇺🇾", "우루과이", "Uruguay", "ウルグアイ", "乌拉圭"),
    "fra": ("🇫🇷", "프랑스", "France", "フランス", "法国"),
    "sen": ("🇸🇳", "세네갈", "Senegal", "セネガル", "塞内加尔"),
    "irq": ("🇮🇶", "이라크", "Iraq", "イラク", "伊拉克"),
    "nor": ("🇳🇴", "노르웨이", "Norway", "ノルウェー", "挪威"),
    "arg": ("🇦🇷", "아르헨티나", "Argentina", "アルゼンチン", "阿根廷"),
    "alg": ("🇩🇿", "알제리", "Algeria", "アルジェリア", "阿尔及利亚"),
    "aut": ("🇦🇹", "오스트리아", "Austria", "オーストリア", "奥地利"),
    "jor": ("🇯🇴", "요르단", "Jordan", "ヨルダン", "约旦"),
    "por": ("🇵🇹", "포르투갈", "Portugal", "ポルトガル", "葡萄牙"),
    "cod": ("🇨🇩", "DR콩고", "DR Congo", "コンゴ民主", "刚果(金)"),
    "uzb": ("🇺🇿", "우즈베키스탄", "Uzbekistan", "ウズベキスタン", "乌兹别克斯坦"),
    "col": ("🇨🇴", "콜롬비아", "Colombia", "コロンビア", "哥伦比亚"),
    "eng": ("🏴󠁧󠁢󠁥󠁮󠁧󠁿", "잉글랜드", "England", "イングランド", "英格兰"),
    "cro": ("🇭🇷", "크로아티아", "Croatia", "クロアチア", "克罗地亚"),
    "gha": ("🇬🇭", "가나", "Ghana", "ガーナ", "加纳"),
    "pan": ("🇵🇦", "파나마", "Panama", "パナマ", "巴拿马"),
}

# venue: (stadium, country_code, city_ko, city_en, city_ja, city_zh)
VENUES = {
    "azteca":    ("Estadio Azteca", "MX", "멕시코시티", "Mexico City", "メキシコシティ", "墨西哥城"),
    "akron":     ("Estadio Akron", "MX", "과달라하라", "Guadalajara", "グアダラハラ", "瓜达拉哈拉"),
    "bbva":      ("Estadio BBVA", "MX", "몬테레이", "Monterrey", "モンテレイ", "蒙特雷"),
    "bmo":       ("BMO Field", "CA", "토론토", "Toronto", "トロント", "多伦多"),
    "bcplace":   ("BC Place", "CA", "밴쿠버", "Vancouver", "バンクーバー", "温哥华"),
    "metlife":   ("MetLife Stadium", "US", "뉴욕·뉴저지", "New York/New Jersey", "ニューヨーク/ニュージャージー", "纽约/新泽西"),
    "gillette":  ("Gillette Stadium", "US", "보스턴", "Boston", "ボストン", "波士顿"),
    "linc":      ("Lincoln Financial Field", "US", "필라델피아", "Philadelphia", "フィラデルフィア", "费城"),
    "hardrock":  ("Hard Rock Stadium", "US", "마이애미", "Miami", "マイアミ", "迈阿密"),
    "mercedes":  ("Mercedes-Benz Stadium", "US", "애틀랜타", "Atlanta", "アトランタ", "亚特兰大"),
    "nrg":       ("NRG Stadium", "US", "휴스턴", "Houston", "ヒューストン", "休斯敦"),
    "att":       ("AT&T Stadium", "US", "댈러스", "Dallas", "ダラス", "达拉斯"),
    "arrowhead": ("Arrowhead Stadium", "US", "캔자스시티", "Kansas City", "カンザスシティ", "堪萨斯城"),
    "sofi":      ("SoFi Stadium", "US", "로스앤젤레스", "Los Angeles", "ロサンゼルス", "洛杉矶"),
    "levis":     ("Levi's Stadium", "US", "샌프란시스코 베이", "San Francisco Bay Area", "サンフランシスコ・ベイエリア", "旧金山湾区"),
    "lumen":     ("Lumen Field", "US", "시애틀", "Seattle", "シアトル", "西雅图"),
}

COUNTRY = {
    "US": ("🇺🇸", "미국", "USA", "アメリカ", "美国"),
    "CA": ("🇨🇦", "캐나다", "Canada", "カナダ", "加拿大"),
    "MX": ("🇲🇽", "멕시코", "Mexico", "メキシコ", "墨西哥"),
}

LANG_IDX = {"ko": 1, "en": 2, "ja": 3, "zh": 4}   # column in TEAMS/COUNTRY tuples
CITY_IDX = {"ko": 2, "en": 3, "ja": 4, "zh": 5}   # column in VENUES

WD = {
    "ko": ["월", "화", "수", "목", "금", "토", "일"],
    "ja": ["月", "火", "水", "木", "金", "土", "日"],
    "zh": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}
MONTH_EN = ["", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"]


def to_utc(date_str, time_str, offset):
    naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    return naive - timedelta(hours=offset)


def fmt_time(dt, lang):
    if lang == "en":
        h = dt.hour % 12 or 12
        ampm = "AM" if dt.hour < 12 else "PM"
        return f"{h}:{dt.minute:02d} {ampm}"
    return f"{dt.hour:02d}:{dt.minute:02d}"


def fmt_day_heading(d, lang):
    w = WD[lang][d.weekday()]
    if lang == "ko":
        return f"{d.month}월 {d.day}일 ({w})"
    if lang == "ja":
        return f"{d.month}月{d.day}日（{w}）"
    if lang == "zh":
        return f"{d.month}月{d.day}日（{w}）"
    return f"{w}, {MONTH_EN[d.month]} {d.day}"


def fmt_local_small(d, lang):
    """Venue-local kickoff, shown small: 6/11 20:00 (or 8:00 PM for en)."""
    t = fmt_time(d, lang)
    return f"{d.month}/{d.day} {t}"


# ----------------------------------------------------------------- language UI --
L = {
    "ko": {
        "slug": SLUG, "lang_attr": "ko", "og_locale": "ko_KR",
        "tz_off": 9, "tz_label": "한국시간 (KST)",
        "title": "2026 월드컵 조별리그 전 경기 일정 — 한국시간 총정리 (72경기)",
        "meta_desc": "2026 북중미 월드컵 조별리그 72경기를 한국시간(KST) 기준 날짜·시간 순서로 정리했다. 경기장 도시와 나라, 현지 킥오프 시간까지 병행 표기. 한국 A조 3경기는 전부 오전 킥오프다.",
        "kicker": "🏆 2026 월드컵 · 조별리그 일정",
        "h1": '조별리그 72경기, <span class="hl">한국시간</span>으로 한 장에',
        "dek": "북중미에서 열리는 경기를 챙겨 보려면 시차 계산이 제일 골치다. 그래서 조별리그 전 경기를 한국시간 기준으로 날짜·시간 순서대로 다시 줄 세웠다. 각 경기에는 경기장이 있는 도시·나라와 현지 킥오프 시간을 함께 적어 뒀다.",
        "read_min": "8분",
        "facts": [("72", "조별리그 경기 수"), ("17", "일간 진행 (6/11~27 현지)"), ("16", "개최 도시"), ("3", "개최국 (미·캐·멕)")],
        "featured_h": "🇰🇷 대한민국 3경기 먼저",
        "featured_note": "전부 한국시간 오전이라 본방 사수가 가능하다. 출근 전 한 경기, 주말 아침 한 경기다.",
        "tznote_h": "⏰ 시간 읽는 법",
        "tznote": "아래 모든 날짜·시간은 <strong>한국시간(KST)</strong> 기준이다. 북미의 저녁 경기는 한국에선 대부분 <strong>다음 날 아침</strong>이 된다. 그래서 현지 6월 11일에 열리는 개막전이 이 표에선 6월 12일에 보인다. 각 경기 줄의 회색 글씨가 <strong>경기장 현지 날짜·시간</strong>이다.",
        "sched_h": "📅 날짜별 전체 일정",
        "sched_note": "같은 날짜 안에서는 킥오프가 빠른 순. 조 3차전(마지막 라운드)은 경우의 수 조작을 막기 위해 같은 조 두 경기가 동시에 열린다.",
        "venue_label": "경기장",
        "foot": "일정·킥오프 시간·경기장은 FIFA 공식 발표와 Wikipedia 조별 문서(2026-06-11 확인)를 토대로 정리했고, 시간대 변환은 스크립트로 일괄 계산했습니다. 대회 운영 사정에 따라 <strong>킥오프 시간은 변경될 수 있으니</strong> 관전 전 FIFA 공식 일정에서 한 번 더 확인하세요. 미국·캐나다는 서머타임(EDT/CDT/MDT/PDT), 멕시코는 표준시(UTC-6) 기준입니다.",
        "nav_cat": "← 월드컵", "home": "🎮 GAMES",
        "bc_home": "홈", "bc_blog": "블로그", "bc_this": "2026 월드컵 조별리그 일정",
        "og_title": "2026 월드컵 조별리그 72경기 — 한국시간 총정리",
        "og_desc": "조별리그 전 경기를 한국시간 순서로. 경기장 도시·나라, 현지 시간 병기. 한국 3경기는 전부 오전 킥오프.",
        "intro": [
            "월드컵의 설렘은 좋은데, 북중미 대회의 시차는 영 고약하다. 미국 동부의 저녁 7시는 한국의 아침 8시이고, 멕시코의 밤 8시는 한국의 오전 11시다. 중계 편성표를 볼 때마다 머릿속에서 13시간, 14시간을 더하다 보면 어느 순간 포기하게 된다.",
            "그래서 이 글은 계산을 대신해 둔 표다. 조별리그 72경기 전부를 <strong>한국시간 기준으로 날짜·시간 순서대로</strong> 다시 정렬했고, 경기마다 <strong>경기장이 있는 도시와 나라</strong>, 그리고 참고용 <strong>현지 킥오프 시간</strong>을 함께 적었다. 새벽 알람을 맞출지, 아침 출근 전에 볼지는 이 표 한 장이면 정리된다.",
        ],
        "mine": "kor",
    },
    "en": {
        "slug": f"{SLUG}-en", "lang_attr": "en", "og_locale": "en_US",
        "tz_off": -4, "tz_label": "US Eastern Time (ET)",
        "title": "World Cup 2026 Group Stage — Full Schedule in US Eastern Time (All 72 Matches)",
        "meta_desc": "Every 2026 World Cup group-stage match sorted by date and kickoff in US Eastern Time, with host city and country for each venue plus local stadium time. All three USMNT games highlighted.",
        "kicker": "🏆 WORLD CUP 2026 · GROUP STAGE SCHEDULE",
        "h1": 'All 72 group games, <span class="hl">one page</span>, Eastern Time',
        "dek": "Sixteen host cities across three countries and four kickoff time zones make this World Cup a scheduling puzzle. Here is the entire group stage re-sorted into US Eastern Time, with the host city and country listed for every match alongside the stadium-local kickoff.",
        "read_min": "8 min",
        "facts": [("72", "group-stage matches"), ("17", "match days (Jun 11–27)"), ("16", "host cities"), ("3", "host nations")],
        "featured_h": "🇺🇸 USMNT first — all three group games",
        "featured_note": "Two evening kickoffs and a Friday matinee. No alarm-clock math needed if you live on the East Coast.",
        "tznote_h": "⏰ How to read the times",
        "tznote": "Every date and time below is <strong>US Eastern Time (ET)</strong>. West Coast and Mexico games can spill past midnight ET, which is why a few matches appear one calendar day later than their venue date. The small grey text on each row is the <strong>stadium-local date and kickoff</strong>.",
        "sched_h": "📅 Day-by-day schedule",
        "sched_note": "Within each day, matches run in kickoff order. Both final-round games in each group kick off simultaneously, a FIFA rule to prevent result manipulation.",
        "venue_label": "Venue",
        "foot": "Dates, kickoff times and venues compiled from FIFA announcements and the per-group Wikipedia articles (checked June 11, 2026); all time-zone conversion is script-computed. <strong>Kickoff times can still change</strong>, so double-check FIFA's official schedule before tuning in. US/Canada times are daylight saving (EDT/CDT/MDT/PDT); Mexico stays on standard time (UTC-6).",
        "nav_cat": "← WORLD CUP", "home": "🎮 GAMES",
        "bc_home": "Home", "bc_blog": "Blog", "bc_this": "World Cup 2026 Group Stage Schedule",
        "og_title": "World Cup 2026 Group Stage — All 72 Matches in Eastern Time",
        "og_desc": "The full group stage sorted by ET kickoff, with host city & country for every venue. USMNT games highlighted.",
        "intro": [
            "A home World Cup should be easy to watch, but this one stretches across four kickoff time zones, from Vancouver to Mexico City. A 7 p.m. start in Seattle is a 10 p.m. finish in New York, and Monterrey's late games land even later.",
            "This page does the math once so you never have to. All 72 group-stage matches are re-sorted into <strong>US Eastern Time</strong>, each with its <strong>host city and country</strong> and the stadium-local kickoff for reference. Set your watch parties accordingly.",
        ],
        "mine": "usa",
    },
    "ja": {
        "slug": f"{SLUG}-ja", "lang_attr": "ja", "og_locale": "ja_JP",
        "tz_off": 9, "tz_label": "日本時間 (JST)",
        "title": "2026年W杯 グループステージ全72試合 — 日本時間の日程まとめ",
        "meta_desc": "2026年北中米ワールドカップのグループステージ全72試合を日本時間(JST)で日付・時刻順に整理。各試合のスタジアム所在都市・国と現地キックオフも併記。日本代表3試合は朝の時間帯。",
        "kicker": "🏆 2026 W杯 · グループステージ日程",
        "h1": 'グループステージ全72試合を<span class="hl">日本時間</span>で',
        "dek": "北中米開催のワールドカップ観戦でいちばん厄介なのは時差の計算だ。そこでグループステージの全試合を日本時間に直して日付・時刻順に並べ替えた。各試合にはスタジアムの都市・国と、参考として現地キックオフ時刻も添えてある。",
        "read_min": "8分",
        "facts": [("72", "グループステージ試合数"), ("17", "日間 (現地6/11〜27)"), ("16", "開催都市"), ("3", "開催国 (米・加・墨)")],
        "featured_h": "🇯🇵 まずは日本代表の3試合",
        "featured_note": "初戦は早朝、2戦目は昼、3戦目は朝。リアルタイム観戦が現実的な時間帯に収まった。",
        "tznote_h": "⏰ 時間の読み方",
        "tznote": "以下の日付・時刻はすべて<strong>日本時間(JST)</strong>。北米の夜の試合は日本では<strong>翌日の朝</strong>になることが多い。現地6月11日の開幕戦がこの表で6月12日に見えるのはそのためだ。各行のグレーの小さな文字が<strong>スタジアム現地の日付・時刻</strong>を示す。",
        "sched_h": "📅 日付別の全日程",
        "sched_note": "同じ日付の中ではキックオフの早い順。各組の最終節2試合は、駆け引き防止のため同時刻キックオフとなる。",
        "venue_label": "会場",
        "foot": "日程・キックオフ時刻・会場はFIFA公式発表とWikipediaの各組記事(2026年6月11日確認)をもとに整理し、時差変換はスクリプトで一括計算しています。<strong>キックオフ時刻は変更される場合がある</strong>ため、観戦前にFIFA公式日程でご確認ください。米国・カナダは夏時間(EDT/CDT/MDT/PDT)、メキシコは標準時(UTC-6)です。",
        "nav_cat": "← ワールドカップ", "home": "🎮 GAMES",
        "bc_home": "ホーム", "bc_blog": "ブログ", "bc_this": "2026年W杯 グループステージ日程",
        "og_title": "2026年W杯 グループステージ全72試合 — 日本時間まとめ",
        "og_desc": "全試合を日本時間で日付順に。会場都市・国、現地時刻も併記。日本代表3試合は朝の時間帯。",
        "intro": [
            "ワールドカップは待ち遠しいのに、北中米との時差はなかなか手強い。アメリカ東部の夜7時は日本の朝8時、メキシコの夜8時は日本の昼11時。中継表を見るたびに13時間、14時間と足し算をしていると、だんだん嫌になってくる。",
            "このページはその計算を先に済ませた一覧表だ。グループステージ全72試合を<strong>日本時間の日付・時刻順</strong>に並べ替え、各試合に<strong>スタジアムのある都市と国</strong>、参考用の<strong>現地キックオフ時刻</strong>を併記した。早起きするか、昼休みに観るか。この表一枚で決められる。",
        ],
        "mine": "jpn",
    },
    "zh": {
        "slug": f"{SLUG}-zh", "lang_attr": "zh-CN", "og_locale": "zh_CN",
        "tz_off": 8, "tz_label": "北京时间",
        "title": "2026世界杯小组赛全72场赛程 — 北京时间完整版",
        "meta_desc": "2026美加墨世界杯小组赛72场比赛，按北京时间日期与开球时间排序，每场标注球场所在城市·国家及当地开球时间。附阿根廷、巴西、英格兰等焦点战速查。",
        "kicker": "🏆 2026世界杯 · 小组赛赛程",
        "h1": '小组赛72场，按<span class="hl">北京时间</span>一页看完',
        "dek": "美加墨三国十六城联办，光时差就够算半天。这里把小组赛全部比赛换算成北京时间，按日期和开球先后重新排序，每场都标注球场所在的城市、国家，并附当地开球时间供参考。",
        "read_min": "8分钟",
        "facts": [("72", "小组赛场次"), ("17", "比赛日 (当地6/11–27)"), ("16", "举办城市"), ("3", "东道主 (美·加·墨)")],
        "featured_h": "🔥 焦点之战速查",
        "featured_note": "开幕战加四场豪门首秀与强强对话，先把这几个闹钟定上。",
        "tznote_h": "⏰ 时间怎么看",
        "tznote": "下表所有日期与时间均为<strong>北京时间</strong>。北美的晚场比赛到了北京时间多半是<strong>第二天上午</strong>，所以当地6月11日的揭幕战在表里显示为6月12日。每行灰色小字是<strong>球场当地的日期·开球时间</strong>。",
        "sched_h": "📅 按日期排列的完整赛程",
        "sched_note": "同一天内按开球先后排序。每个小组第三轮的两场比赛同时开球，这是国际足联防止默契球的惯例。",
        "venue_label": "球场",
        "foot": "赛程、开球时间与球场信息整理自FIFA官方公告及Wikipedia各小组条目(2026年6月11日核对)，时区换算由脚本统一计算。<strong>开球时间仍有调整可能</strong>，观赛前请以FIFA官方赛程为准。美国、加拿大采用夏令时(EDT/CDT/MDT/PDT)，墨西哥为标准时间(UTC-6)。",
        "nav_cat": "← 世界杯", "home": "🎮 GAMES",
        "bc_home": "首页", "bc_blog": "博客", "bc_this": "2026世界杯小组赛赛程",
        "og_title": "2026世界杯小组赛全72场 — 北京时间完整赛程",
        "og_desc": "小组赛全部比赛按北京时间排序，标注球场城市·国家与当地开球时间。附焦点战速查。",
        "intro": [
            "世界杯年年盼，可美加墨的时差实在让人头疼。美国东部晚上7点是北京时间次日早上7点，墨西哥城晚上8点是北京时间上午10点。每看一次转播表都要心算一遍，算到最后干脆放弃。",
            "这页就是替你把账算完的表。小组赛72场比赛全部换算成<strong>北京时间</strong>，按日期与开球先后重排，每场比赛都注明<strong>球场所在城市与国家</strong>，并附上当地开球时间。定闹钟还是睡醒看重播，看完这张表再决定。",
        ],
        "mine": None,
        "marquee": [("mex", "rsa"), ("bra", "mar"), ("arg", "alg"), ("eng", "cro"), ("uru", "esp")],
    },
}


# --------------------------------------------------------------- validation --
def validate(rows):
    assert len(rows) == 72, f"expected 72 matches, got {len(rows)}"
    per_team = {}
    per_group = {}
    md3 = {}
    for grp, date, t, off, a, b, v in rows:
        per_group.setdefault(grp, 0)
        per_group[grp] += 1
        for tm in (a, b):
            per_team.setdefault(tm, 0)
            per_team[tm] += 1
        assert v in VENUES, f"unknown venue {v}"
    assert all(c == 6 for c in per_group.values()), per_group
    assert len(per_team) == 48 and all(c == 3 for c in per_team.values()), per_team
    # matchday-3 simultaneity: the last two matches of each group share UTC
    for grp in per_group:
        g = [r for r in rows if r[0] == grp]
        g_utc = sorted(to_utc(r[1], r[2], r[3]) for r in g)
        assert g_utc[4] == g_utc[5], f"group {grp} MD3 not simultaneous: {g_utc[4]} vs {g_utc[5]}"


# ------------------------------------------------------------------ HTML bits --
CSS = """
  :root{
    --bg:#05140e; --surface:#0b211a; --surface2:#102b21; --border:#1c3b30;
    --green:#2dd4bf; --green2:#34d399; --gold:#fbbf24; --text:#cfe6dd; --dim:#6f8a80;
    --hot:#ff7a59; --white:#fff;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'Noto Sans KR',sans-serif;line-height:1.75;-webkit-font-smoothing:antialiased}
  .container{max-width:760px;margin:0 auto;background:var(--bg);min-height:100vh}
  .site-nav{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--border);background:rgba(5,20,14,.85);backdrop-filter:blur(8px);position:sticky;top:0;z-index:50}
  .site-nav a{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);text-decoration:none;letter-spacing:1px;transition:color .2s}
  .site-nav a:hover{color:var(--green)}
  .hero{padding:30px 18px 22px;border-bottom:1px solid var(--border);background:radial-gradient(ellipse at 80% 0%,rgba(45,212,191,.10),transparent 60%),radial-gradient(ellipse at 0% 100%,rgba(251,191,36,.06),transparent 55%)}
  .kicker{display:inline-flex;align-items:center;gap:7px;font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#04231a;background:linear-gradient(90deg,var(--green),var(--green2));padding:5px 11px;border-radius:20px;margin-bottom:16px}
  h1{font-size:29px;font-weight:900;color:var(--white);line-height:1.28;letter-spacing:-.02em;margin-bottom:14px}
  h1 .hl{color:var(--green)}
  .dek{font-size:15px;color:#a9c6bc;line-height:1.7;margin-bottom:18px}
  .meta{display:flex;gap:14px;flex-wrap:wrap;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);letter-spacing:.5px}
  .meta b{color:var(--gold)}
  .body{padding:8px 18px 0}
  .body p{font-size:15px;line-height:1.85;color:var(--text);margin:16px 0}
  .body strong{color:var(--white)}
  h2{font-size:21px;font-weight:900;color:var(--white);margin:38px 0 8px;letter-spacing:-.01em;padding-top:18px;border-top:1px solid var(--border)}
  .lede{font-size:13.5px;color:var(--dim);margin:0 0 14px}
  .facts{display:grid;grid-template-columns:repeat(2,1fr);gap:9px;margin:20px 0 8px}
  .fact{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:13px 14px}
  .fact .num{font-family:'Bebas Neue',sans-serif;font-size:30px;line-height:1;color:var(--gold);letter-spacing:.5px}
  .fact .lbl{font-size:12px;color:var(--dim);margin-top:5px;line-height:1.4}
  .callout{margin:22px 0;padding:16px 18px;border-radius:14px;background:linear-gradient(135deg,rgba(251,191,36,.08),rgba(45,212,191,.04));border:1px solid rgba(251,191,36,.3)}
  .callout h3{font-size:15.5px;color:var(--gold);margin-bottom:7px;font-weight:800}
  .callout p{font-size:13.5px;line-height:1.75;color:var(--text);margin:6px 0}
  .callout strong{color:var(--white)}
  /* featured matches */
  .feat{margin:18px 0;border:1px solid rgba(45,212,191,.45);border-radius:14px;overflow:hidden;background:linear-gradient(180deg,rgba(45,212,191,.07),rgba(45,212,191,.01))}
  .feat-h{padding:12px 15px 4px;font-size:15.5px;font-weight:800;color:var(--white)}
  .feat-n{padding:0 15px 10px;font-size:12.5px;color:var(--dim);line-height:1.6}
  /* day blocks */
  .day{margin:18px 0}
  .day-h{display:flex;align-items:baseline;gap:10px;padding:9px 4px 7px;border-bottom:2px solid var(--green);margin-bottom:8px}
  .day-h .d{font-size:17px;font-weight:900;color:var(--white)}
  .day-h .c{font-family:'JetBrains Mono',monospace;font-size:10.5px;color:var(--dim)}
  .mrow{display:flex;flex-direction:column;gap:3px;padding:11px 12px;border:1px solid var(--border);border-radius:12px;margin-bottom:7px;background:var(--surface)}
  .mrow.mine{border-color:rgba(251,191,36,.55);background:linear-gradient(180deg,rgba(251,191,36,.08),rgba(251,191,36,.015))}
  .mrow .top{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .mtime{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:700;color:var(--green);min-width:46px}
  .mrow.mine .mtime{color:var(--gold)}
  .grp-chip{font-family:'JetBrains Mono',monospace;font-size:9.5px;font-weight:700;color:#04231a;background:var(--green);border-radius:5px;padding:2px 6px;letter-spacing:.5px}
  .mrow.mine .grp-chip{background:var(--gold)}
  .teams{font-size:14.5px;font-weight:700;color:var(--white)}
  .teams .vs{color:var(--dim);font-weight:400;font-size:12px;margin:0 4px}
  .venue{font-size:12px;color:var(--dim);line-height:1.5}
  .venue b{color:#9fc0b5;font-weight:600}
  .venue .loc-t{font-family:'JetBrains Mono',monospace;font-size:10.5px;color:#557065}
  .foot{margin:28px 18px 18px;padding:14px 16px;background:var(--surface);border:1px solid var(--border);border-radius:12px;font-size:11.5px;line-height:1.7;color:var(--dim)}
  .foot strong{color:var(--gold)}
  .src{margin-top:8px;display:flex;flex-wrap:wrap;gap:6px}
  .src a{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--green);text-decoration:none;border:1px solid var(--border);padding:3px 8px;border-radius:6px}
  @media(min-width:768px){
    .facts{grid-template-columns:repeat(4,1fr)}h1{font-size:35px}
    .mrow{flex-direction:row;align-items:center;justify-content:space-between;gap:14px}
    .mrow .top{flex:0 0 auto}
    .venue{text-align:right}
  }
"""

BUILD_CHECK = (
    '<!--lp-build-check:start-->\n'
    f'<meta name="lp-build" content="{BUILD_STAMP}">\n'
    f'<script>(function(){{var B="{BUILD_STAMP}";try{{fetch("/build.json?_="+Date.now(),{{cache:"no-store"}}).then(function(r){{return r.ok?r.json():null}}).then(function(d){{if(!d||!d.v||d.v===B)return;var k="lp_build_"+B;try{{if(sessionStorage.getItem(k))return;sessionStorage.setItem(k,"1");}}catch(e){{}}var u=new URL(location.href);u.searchParams.set("_b",d.v);location.replace(u.toString());}}).catch(function(){{}});}}catch(e){{}}}})();</script>\n'
    '<!--lp-build-check:end-->'
)


def team_html(key, lang):
    t = TEAMS[key]
    return f"{t[0]} {t[LANG_IDX[lang]]}"


def venue_html(vkey, lang, cfg, loc_dt):
    stad, cc, *_ = VENUES[vkey]
    city = VENUES[vkey][CITY_IDX[lang]]
    cflag, *_ = COUNTRY[cc]
    cname = COUNTRY[cc][LANG_IDX[lang]]
    loc = fmt_local_small(loc_dt, lang)
    return (f'🏟 <b>{city} · {cname} {cflag}</b> — {stad} '
            f'<span class="loc-t">({cfg["loc_word"]} {loc})</span>')


def fmt_feat_time(view, lang):
    """Date + short weekday + time, for the featured box where rows have no
    day heading above them."""
    if lang == "en":
        wd = WD["en"][view.weekday()][:3]
        return f"{wd} {view.month}/{view.day} · {fmt_time(view, 'en')}"
    w = WD[lang][view.weekday()]
    if lang == "ko":
        return f"{view.month}/{view.day} ({w}) {fmt_time(view, lang)}"
    return f"{view.month}/{view.day}（{w}）{fmt_time(view, lang)}"


def match_row(m, lang, cfg, with_date=False):
    grp, date, t, off, a, b, vkey = m
    utc = to_utc(date, t, off)
    view = utc + timedelta(hours=cfg["tz_off"])
    loc = to_utc(date, t, 0)  # naive local datetime as given
    mine = cfg.get("mine") and (a == cfg["mine"] or b == cfg["mine"])
    cls = "mrow mine" if mine else "mrow"
    shown = fmt_feat_time(view, lang) if with_date else fmt_time(view, lang)
    return (view, f'<div class="{cls}">'
                  f'<div class="top"><span class="mtime">{shown}</span>'
                  f'<span class="grp-chip">{grp}</span>'
                  f'<span class="teams">{team_html(a, lang)}<span class="vs">vs</span>{team_html(b, lang)}</span></div>'
                  f'<div class="venue">{venue_html(vkey, lang, cfg, loc)}</div>'
                  f'</div>')


def build_lang(lang):
    cfg = L[lang]
    cfg["loc_word"] = {"ko": "현지", "en": "local", "ja": "現地", "zh": "当地"}[lang]

    # rows sorted by viewer time
    rows = []
    for m in MATCHES:
        view, html = match_row(m, lang, cfg)
        rows.append((view, html))
    rows.sort(key=lambda r: r[0])

    # group by viewer-local date
    days = {}
    for view, html in rows:
        days.setdefault(view.date(), []).append(html)

    n_label = {"ko": "경기", "en": " matches", "ja": "試合", "zh": "场"}[lang]
    day_html = []
    for d in sorted(days):
        items = "\n".join(days[d])
        day_html.append(
            f'<div class="day"><div class="day-h"><span class="d">{fmt_day_heading(d, lang)}</span>'
            f'<span class="c">{len(days[d])}{n_label}</span></div>\n{items}\n</div>')

    # featured block
    if cfg.get("mine"):
        feats = [m for m in MATCHES if cfg["mine"] in (m[4], m[5])]
    else:
        feats = []
        for a, b in cfg["marquee"]:
            feats += [m for m in MATCHES if {m[4], m[5]} == {a, b}]
    feats_rows = sorted((match_row(m, lang, cfg, with_date=True) for m in feats), key=lambda r: r[0])
    feat_items = "\n".join(h.replace('class="mrow"', 'class="mrow mine"') for _, h in feats_rows)

    facts = "\n".join(
        f'<div class="fact"><div class="num">{n}</div><div class="lbl">{lb}</div></div>'
        for n, lb in cfg["facts"])
    intro = "\n".join(f"<p>{p}</p>" for p in cfg["intro"])

    alt_links = "\n".join(
        f'<link rel="alternate" hreflang="{hl}" href="https://luckyplz.com/blog/{L[k]["slug"]}/">'
        for hl, k in [("ko", "ko"), ("en", "en"), ("ja", "ja"), ("zh", "zh")])

    ld_post = json.dumps({
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": cfg["title"], "description": cfg["meta_desc"],
        "datePublished": "2026-06-11", "dateModified": "2026-06-11",
        "inLanguage": lang if lang != "zh" else "zh-CN",
        "author": {"@type": "Organization", "name": "Lucky Please", "url": "https://luckyplz.com/"},
        "publisher": {"@type": "Organization", "name": "Lucky Please",
                      "logo": {"@type": "ImageObject", "url": "https://luckyplz.com/assets/icon-192.png"}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"https://luckyplz.com/blog/{cfg['slug']}/"},
    }, ensure_ascii=False)
    ld_bc = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": cfg["bc_home"], "item": "https://luckyplz.com/"},
            {"@type": "ListItem", "position": 2, "name": cfg["bc_blog"], "item": "https://luckyplz.com/blog/"},
            {"@type": "ListItem", "position": 3, "name": cfg["bc_this"], "item": f"https://luckyplz.com/blog/{cfg['slug']}/"},
        ]}, ensure_ascii=False)

    og_img = f"https://luckyplz.com/assets/blog/{SLUG}-{lang}.png?v={BUILD_STAMP}"

    html = f"""<!DOCTYPE html>
<html lang="{cfg['lang_attr']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
{BUILD_CHECK}
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<title>{cfg['title']} | Lucky Please</title>
<meta name="description" content="{cfg['meta_desc']}">
<link rel="canonical" href="https://luckyplz.com/blog/{cfg['slug']}/">
{alt_links}
<link rel="alternate" hreflang="x-default" href="https://luckyplz.com/blog/{SLUG}-en/">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Lucky Please">
<meta property="og:locale" content="{cfg['og_locale']}">
<meta property="og:title" content="{cfg['og_title']}">
<meta property="og:description" content="{cfg['og_desc']}">
<meta property="og:url" content="https://luckyplz.com/blog/{cfg['slug']}/">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="article:published_time" content="2026-06-11T18:00:00+09:00">
<meta property="article:section" content="Sports">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{cfg['og_title']}">
<meta name="twitter:description" content="{cfg['og_desc']}">
<meta name="twitter:image" content="{og_img}">
<script type="application/ld+json">{ld_post}</script>
<script type="application/ld+json">{ld_bc}</script>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#05140e">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=JetBrains+Mono:wght@400;700&family=Bebas+Neue&display=swap" rel="stylesheet">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5370817769801923" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NZDPE3H3DQ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-NZDPE3H3DQ');</script>
<style>{CSS}</style>
</head>
<body>
<div class="container">

<nav class="site-nav">
  <a href="/blog/?cat=worldcup">{cfg['nav_cat']}</a>
  <a href="/">{cfg['home']}</a>
</nav>

<header class="hero">
  <span class="kicker">{cfg['kicker']}</span>
  <h1>{cfg['h1']}</h1>
  <p class="dek">{cfg['dek']}</p>
  <div class="meta"><span>2026. 6. 11.</span><span><b>{cfg['read_min']}</b></span><span>{cfg['tz_label']}</span></div>
</header>

<div class="body">

{intro}

<div class="facts">
{facts}
</div>

<div class="feat">
  <div class="feat-h">{cfg['featured_h']}</div>
  <div class="feat-n">{cfg['featured_note']}</div>
  <div style="padding:0 10px 10px">
{feat_items}
  </div>
</div>

<div class="callout">
  <h3>{cfg['tznote_h']}</h3>
  <p>{cfg['tznote']}</p>
</div>

<h2>{cfg['sched_h']}</h2>
<p class="lede">{cfg['sched_note']}</p>

{chr(10).join(day_html)}

</div>

<footer class="foot">
  <strong>📌 Source &amp; Note</strong><br>
  {cfg['foot']}
  <div class="src">
    <a href="https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/scores-fixtures" target="_blank" rel="noopener">FIFA Fixtures</a>
    <a href="https://en.wikipedia.org/wiki/2026_FIFA_World_Cup" target="_blank" rel="noopener">Wikipedia</a>
  </div>
</footer>

</div>
<script src="/js/blogReadingAids.js?v={BUILD_STAMP}"></script>
<script src="/blog/posts.js?v={BUILD_STAMP}"></script>
<script src="/js/blogReactions.js?v={BUILD_STAMP}"></script>
<script src="/js/blogSubscribe.js?v={BUILD_STAMP}"></script>
<script src="/js/blogRelated.js?v={BUILD_STAMP}"></script>
<script src="/js/siteFooter.js?v={BUILD_STAMP}"></script>
</body>
</html>
"""
    out_dir = BLOG / cfg["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote blog/{cfg['slug']}/index.html")


def main():
    validate(MATCHES)
    print("validation OK: 72 matches, 48 teams x3, MD3 simultaneous")
    for lang in ("ko", "en", "ja", "zh"):
        build_lang(lang)


if __name__ == "__main__":
    main()
