#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the 4-language Iran-US ceasefire LIVE post (category: issue).

Rewritten as a latest-first LIVE FEED (not an encyclopedic explainer): a red
'right now' lead box capturing the live tension, then reverse-chronological
timestamped entries with vivid specifics and direct quotes, then a short
read-through. The live story is the GAP between Trump publicly hyping an
imminent signing ('this weekend', 'oil prices dropping like a rock') and
Iran's foreign ministry calling overnight US strikes a 'flagrant violation'
that rendered the April 8 ceasefire 'meaningless'.

Every entry is attributed; only the relative/explicit time markers the
sources actually give are used (no fabricated minute timestamps).

Sources (public reporting, June 2026): ABC News & ms.now live blogs, CNN,
Al Jazeera, Wikipedia. Indexed manual analysis.
Output: public/blog/iran-us-ceasefire-2026-06[/-en/-ja/-zh]/index.html
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "public" / "blog"
SLUG = "iran-us-ceasefire-2026-06"
STAMP = json.loads((ROOT / "public" / "build.json").read_text())["v"]

SRC = [
    ("ABC News · live", "https://abcnews.com/International/live-updates/iran-live-updates-israel-iran-trade-strikes-trump/?id=133674243"),
    ("ms.now · live (Jun 10)", "https://www.ms.now/liveblog/iran-news-trump-israel-war-june-10-2026"),
    ("CNN · live (Jun 7–8)", "https://www.cnn.com/2026/06/07/world/live-news/iran-war-trump-israel-lebanon"),
    ("Al Jazeera", "https://www.aljazeera.com/news/2026/5/25/rubio-says-us-will-find-another-way-if-iran-talks-fail"),
    ("Wikipedia · 2026 Iran war ceasefire", "https://en.wikipedia.org/wiki/2026_Iran_war_ceasefire"),
]

L = {
    "ko": {
        "lang": "ko", "slug": SLUG, "og_locale": "ko_KR",
        "title": "이란-미국 휴전 라이브 — 트럼프 '주말 서명' vs 이란 '휴전 무의미', 지금 무슨 일이",
        "desc": "트럼프는 '며칠 내, 어쩌면 이번 주말 유럽서 서명' '유가가 돌처럼 떨어질 것'이라며 종전 임박을 띄우는데, 이란 외무부는 간밤 미국 공습이 '4월 8일 휴전을 무의미하게 만들었다'고 맞받았다. 최신순으로 정리한 이란-미국 전황·협상 라이브. (6월 12일 기준)",
        "kicker": "📰 이슈 · 중동 정세 LIVE",
        "h1": '말은 \'주말 서명\', 현장은 <span class="hl">간밤 공습</span>',
        "dek": "지금 이란-미국 국면은 한 화면에 두 장면이 겹쳐 있다. 트럼프는 \"전쟁을 멋지게 끝냈다\"며 <strong>이번 주말 서명</strong>도 가능하다고 띄우는데, 같은 시각 이란은 <strong>간밤 미국의 공습</strong>으로 휴전이 \"무의미해졌다\"고 선언했다. 최신 소식부터 시간 역순으로 따라가 본다.",
        "asof": "이 글은 <strong>2026년 6월 12일(한국시간)</strong> 기준 공개 라이브 보도를 최신순으로 정리한 것입니다. 분 단위로 상황이 바뀌므로, 인용 전 원문 보도를 다시 확인하세요.",
        "read": "6분",
        "lead": "🔴 <strong>지금 핵심.</strong> 외교(말)와 전장(현장)이 따로 논다. 트럼프 — \"이란과의 전쟁을 멋지게 매듭지었다… 며칠 내, 아마 유럽에서 서명\". 이란 외무부 — 간밤 미국 공습은 \"노골적 위반\"이며 4월 8일 휴전을 \"사실상 무의미하게\" 만들었다. 둘 다 사실이다.",
        "feed": [
            ("방금 · 트럼프", '<b>"이번 주말 서명도 가능."</b> 트럼프 대통령은 기자들에게 "우리는 이란과의 전쟁을 멋지게 매듭지었다(great settlement)"며, 합의가 "며칠 안에" 마무리돼 "아마 유럽에서 서명"할 수 있다고 말했다. 다만 양해각서(MOU)는 "조금 개념적"이라고 단서를 달았다.'),
            ("트럼프 · 호르무즈·유가", '<b>"서명 즉시 호르무즈 공식 개방."</b> 트럼프는 합의가 서명되는 순간 해협이 열리고, 미국의 해상 봉쇄도 "합의의 일부"로 해제될 것이라며 <em>"유가가 돌처럼 떨어질 것(dropping like a rock)"</em>이라고 했다.'),
            ("간밤 · 이란 외무부", '<b>"휴전은 무의미해졌다."</b> 이란 외무부는 간밤 미국의 공습을 국제법의 "노골적 위반(flagrant violation)"으로 규정하며, 이 공격이 <strong>4월 8일 휴전을 사실상 무의미하게</strong> 만들었다고 비난했다. 미국이 모순된 신호를 보내고 있다는 주장도 덧붙였다.'),
            ("미군", '<b>정밀유도탄으로 이란 표적 타격.</b> 미 해병대·공군·해군 자산이 이란 표적에 정밀유도탄을 발사했다. 미국은 이를 "이란의 부당하고 지속적인 공격에 대한 대응"이라고 밝혔다. 트럼프 대통령과 헤그세스 국방장관의 경고 직후 이뤄진 추가 타격이다.'),
            ("6월 10일 오후 2:45 (EDT)", '<b>CENTCOM, 이란 주장 부인.</b> 미 중부사령부는 이란이 "호르무즈 해협을 봉쇄했다"거나 "미 군함을 공격했다"는 주장을 부인했다. 미국은 이란 내 "다수 표적"에 새 타격을 가했다.'),
            ("현장 · 오만 인근", '<b>아파치 헬기 추락, 승무원 2명 구조.</b> 전날 오만 인근에서 추락한 미 육군 AH-64 아파치 헬기 승무원 2명이 구조됐고 상태는 안정적이다. 한 미국 관리는 헬기가 이란 드론과 충돌했다고 전했으나, 의도성은 불분명하다고 했다.'),
            ("누적 피해", '<b>레바논 사망 3,600명 초과 · 분쟁 100일 돌파.</b> 레바논 보건부 집계상 이스라엘의 헤즈볼라 대상 공습 사망자가 3,600명을 넘어섰다. 이번 분쟁은 100일을 넘겼다.'),
            ("시장", '<b>미 인플레이션 3년 만에 4% 돌파.</b> 전쟁과 유가 부담 속에 미국 물가상승률이 3년 만에 처음으로 4%를 넘어섰다. 호르무즈 개방 여부가 지금 시장의 최대 실시간 관전 포인트다.'),
            ("배경 한 줄", '2월 28일 트럼프가 "주요 전투작전" 개시를 선언 → 초기 2주 휴전 → 이후 무기한 연장 + 협상이 "어떤 식으로든" 끝날 때까지 봉쇄 유지. 4월 8일 휴전이 그 기준선이다.'),
        ],
        "read_h": "이 그림, 어떻게 읽나",
        "read_p": [
            "지금 국면의 본질은 <strong>말과 현장의 시차</strong>다. 협상 테이블에선 \"주말 서명\"이라는 단어가 오가지만, 같은 밤 하늘에선 정밀유도탄이 떨어지고 \"휴전 무의미\" 선언이 나온다. 트럼프의 낙관은 협상 동력을 끌어올리는 압박 카드일 수 있고, 이란의 강경 발언은 양보 전 몸값을 올리는 협상술일 수 있다. 둘 다 진심일 수도 있다.",
            "그래서 실시간으로 지켜볼 단 하나의 지표를 꼽으라면 <strong>호르무즈 해협과 유가</strong>다. 트럼프 말대로 서명과 동시에 해협이 열리면 유가는 빠르게 빠지고 증시는 안도할 것이다. 반대로 야간 공습이 한 번 더 반복되면, \"서명 임박\"이라는 말은 다시 며칠 뒤로 밀린다. 지금은 끝이 아니라, 시간 단위로 갈리는 갈림길이다.",
        ],
        "foot": "본 글은 2026년 6월 12일(한국시간) 기준 <strong>공개 라이브 보도를 종합·정리</strong>한 것으로, 특정 입장을 옹호하지 않습니다. 전황·발언은 분 단위로 바뀌며 매체 간 차이가 있을 수 있습니다(중재국·휴전 효력 등). 일부 시각 표기는 보도가 제공한 상대적 시점(간밤·목요일·현지시각)을 그대로 옮긴 것이며, 군사·외교 사안 특성상 추정이 포함될 수 있으니 원문과 공식 발표로 교차 확인하시기 바랍니다.",
        "nav_cat": "← 이슈", "home": "🎮 GAMES",
        "bc": ["홈", "블로그", "이란-미국 휴전 LIVE"],
        "og_title": "이란-미국 휴전 LIVE — 트럼프 '주말 서명' vs 이란 '휴전 무의미'",
        "og_desc": "말은 종전 임박, 현장은 간밤 공습. 최신순 라이브로 따라가는 전황·협상. (6/12 기준)",
        "label": "이슈", "asof_badge": "2026.6.12 기준 · 분 단위로 변함",
    },
    "en": {
        "lang": "en", "slug": f"{SLUG}-en", "og_locale": "en_US",
        "title": "Iran–US Ceasefire LIVE — Trump Touts 'Signing This Weekend' as Iran Calls Overnight Strikes 'Meaningless'",
        "desc": "Trump says a deal could be signed 'in days, maybe in Europe' and 'oil prices will drop like a rock,' while Iran's foreign ministry says overnight US strikes rendered the April 8 ceasefire 'meaningless.' A latest-first live read of the war and the talks. (As of June 12.)",
        "kicker": "📰 ISSUE · MIDDLE EAST LIVE",
        "h1": 'Talk Says \'Sign This Weekend.\' The Sky Says <span class="hl">Overnight Strikes</span>',
        "dek": "Two scenes are sharing one screen. Trump says he \"settled the war\" and a deal could be signed <strong>this weekend</strong>; at the same hour Iran says <strong>overnight US strikes</strong> rendered the truce \"meaningless.\" Here it is, newest first.",
        "asof": "This is a latest-first compile of public live reporting <strong>as of June 12, 2026 (KST)</strong>. It changes by the minute — re-check primary sources before relying on it.",
        "read": "6 min",
        "lead": "🔴 <strong>The core, right now.</strong> Diplomacy and the battlefield are out of sync. Trump: \"a great settlement of the war with Iran… signed in days, maybe in Europe.\" Iran's foreign ministry: the overnight US strikes are a \"flagrant violation\" that left the April 8 ceasefire \"meaningless.\" Both are true at once.",
        "feed": [
            ("Just now · Trump", '<b>"Could be signed this weekend."</b> Speaking to reporters, President Trump said the US \"made a great settlement of the war with Iran,\" that it should \"get done over the next few days\" and \"probably have a signing, maybe in Europe.\" He hedged that the memorandum of understanding is \"a little conceptual.\"'),
            ("Trump · Hormuz & oil", '<b>"Hormuz opens the moment we sign."</b> Trump said the Strait would \"officially open\" on signing and the US naval blockade would lift as \"part of the deal\" — <em>\"you\'ll have oil prices dropping like a rock.\"</em>'),
            ("Overnight · Iran MFA", '<b>"The ceasefire is meaningless."</b> Iran\'s foreign ministry called the overnight US attacks a \"flagrant violation\" of international law that <strong>\"effectively rendered the April 8 ceasefire meaningless,\"</strong> and accused Washington of sending contradictory signals.'),
            ("US military", '<b>Precision munitions on Iranian targets.</b> US Marine Corps, Air Force and Navy assets fired precision munitions at Iranian targets — \"in response to Iran\'s unwarranted and continued aggression,\" the US said. The strikes followed warnings from Trump and Defense Secretary Pete Hegseth.'),
            ("Jun 10, 2:45 PM EDT", '<b>CENTCOM denies Iran\'s claims.</b> US Central Command denied Iranian claims that Tehran had closed the Strait of Hormuz or hit a US warship. The US struck \"multiple targets\" inside Iran.'),
            ("On the ground · near Oman", '<b>Apache crew rescued.</b> Two crew of a US Army AH-64 Apache that crashed near Oman the day before were rescued and reported stable. A US official said the helicopter collided with an Iranian drone; intent unclear.'),
            ("Toll", '<b>3,600+ dead in Lebanon · past 100 days.</b> Israeli strikes on Hezbollah in Lebanon have killed more than 3,600 (Lebanese health ministry). The conflict has now passed 100 days.'),
            ("Markets", '<b>US inflation tops 4% for the first time in three years.</b> War and oil pressure pushed US inflation above 4%. Whether Hormuz reopens is the market\'s single biggest live watch-point.'),
            ("One-line backdrop", 'Feb 28: Trump announced \"major combat operations\" → an initial two-week ceasefire → an open-ended extension plus a blockade until talks conclude \"one way or the other.\" The April 8 truce is the baseline.'),
        ],
        "read_h": "How to read this",
        "read_p": [
            "The essence of this moment is a <strong>lag between words and the ground</strong>. The table talks about \"signing this weekend,\" while the same night brings precision strikes and a \"meaningless\" declaration. Trump\'s optimism may be pressure to force momentum; Iran\'s hard line may be price-raising before a concession. Both could also be sincere.",
            "If you watch one real-time gauge, watch <strong>the Strait of Hormuz and oil</strong>. If it opens on signing as Trump says, oil falls fast and equities exhale. If one more overnight strike lands, \"imminent signing\" slips a few more days. This is a fork that turns by the hour, not an ending.",
        ],
        "foot": "This compiles <strong>public live reporting as of June 12, 2026 (KST)</strong> and advocates no side. The picture and the statements change by the minute and differ across outlets (mediators, the truce\'s status). Some time markers reproduce the relative timing the sources gave (overnight, Thursday, local time); given the topic, some elements may be estimates — cross-check primary reporting and official statements.",
        "nav_cat": "← ISSUES", "home": "🎮 GAMES",
        "bc": ["Home", "Blog", "Iran–US Ceasefire LIVE"],
        "og_title": "Iran–US Ceasefire LIVE — 'Sign This Weekend' vs 'Meaningless'",
        "og_desc": "Talk says imminent deal; the sky says overnight strikes. A latest-first live read. (As of Jun 12.)",
        "label": "Issue", "asof_badge": "As of Jun 12, 2026 · changes by the minute",
    },
    "ja": {
        "lang": "ja", "slug": f"{SLUG}-ja", "og_locale": "ja_JP",
        "title": "イラン・米国 停戦ライブ — トランプ「週末に署名も」、イランは「停戦は無意味」",
        "desc": "トランプは「数日内、おそらく欧州で署名」「原油価格は石のように落ちる」と終戦の近さを煽る一方、イラン外務省は夜間の米空爆が「4月8日の停戦を無意味にした」と反発。最新順でたどるイラン・米国の戦況と交渉ライブ。（6月12日時点）",
        "kicker": "📰 時事 · 中東情勢 LIVE",
        "h1": '言葉は「週末署名」、現場は<span class="hl">夜間空爆</span>',
        "dek": "今のイラン・米国局面は、一つの画面に二つの場面が重なっている。トランプは「戦争を見事に決着させた」として<strong>週末の署名</strong>も可能だと煽るが、同じ時刻にイランは<strong>夜間の米空爆</strong>で停戦が「無意味になった」と宣言した。最新の動きから時間を遡って追う。",
        "asof": "本記事は<strong>2026年6月12日（日本時間）</strong>時点の公開ライブ報道を最新順に整理したものです。分単位で変化するため、引用前に原典を再確認してください。",
        "read": "6分",
        "lead": "🔴 <strong>今の核心。</strong> 外交（言葉）と戦場（現場）がずれている。トランプ —「イランとの戦争を見事に決着…数日内、おそらく欧州で署名」。イラン外務省 — 夜間の米空爆は「露骨な違反」であり、4月8日の停戦を「事実上無意味」にした。どちらも同時に事実だ。",
        "feed": [
            ("たった今 · トランプ", '<b>「週末に署名も。」</b> トランプ大統領は記者団に、米国は「イランとの戦争を見事に決着させた」とし、合意は「数日内」に固まり「おそらく欧州で署名」できると述べた。ただし覚書（MOU）は「やや概念的」と留保した。'),
            ("トランプ · ホルムズ・原油", '<b>「署名と同時にホルムズ公式開放。」</b> トランプは合意署名の瞬間に海峡が開き、米国の海上封鎖も「合意の一部」として解除されるとし、<em>「原油価格は石のように落ちる」</em>と語った。'),
            ("夜間 · イラン外務省", '<b>「停戦は無意味になった。」</b> イラン外務省は夜間の米空爆を国際法の「露骨な違反」と断じ、この攻撃が<strong>4月8日の停戦を事実上無意味に</strong>したと非難。米国が矛盾した信号を送っているとも主張した。'),
            ("米軍", '<b>精密誘導弾でイラン標的を攻撃。</b> 米海兵隊・空軍・海軍の資産がイラン標的に精密誘導弾を発射。米国はこれを「イランの不当かつ継続的な攻撃への対応」とした。トランプ大統領とヘグセス国防長官の警告直後の追加攻撃だ。'),
            ("6月10日 午後2:45（EDT）", '<b>中央軍、イラン主張を否定。</b> 米中央軍は、イランが「ホルムズ海峡を封鎖した」「米軍艦を攻撃した」とする主張を否定。米国はイラン内の「複数の標的」を新たに攻撃した。'),
            ("現場 · オマーン近海", '<b>アパッチ墜落、乗員2名救助。</b> 前日オマーン近海で墜落した米陸軍AH-64アパッチの乗員2名が救助され、容体は安定。ある米当局者は、機体がイランのドローンと衝突したと述べたが、意図性は不明とした。'),
            ("累積被害", '<b>レバノン死者3,600人超 · 紛争100日突破。</b> レバノン保健省の集計で、イスラエルのヒズボラ攻撃の死者が3,600人を超えた。紛争は100日を超えた。'),
            ("市場", '<b>米インフレ、3年ぶり4%超。</b> 戦争と原油の負担の中、米国の物価上昇率が3年ぶりに4%を超えた。ホルムズ開放の可否が、いま市場最大のリアルタイム注目点だ。'),
            ("背景・一行", '2月28日にトランプが「主要戦闘作戦」開始を宣言 → 当初2週間の停戦 → その後無期限延長＋交渉が「いずれにせよ」決着するまで封鎖維持。4月8日の停戦が基準線だ。'),
        ],
        "read_h": "この絵をどう読むか",
        "read_p": [
            "今の局面の本質は<strong>言葉と現場の時差</strong>だ。交渉卓では「週末署名」という言葉が飛び交うが、同じ夜空には精密誘導弾が落ち「停戦無意味」の宣言が出る。トランプの楽観は勢いを作る圧力カードかもしれず、イランの強硬発言は譲歩前の値上げ交渉術かもしれない。両方が本気の可能性もある。",
            "リアルタイムで見る指標を一つ挙げるなら<strong>ホルムズ海峡と原油</strong>だ。トランプの言う通り署名と同時に開けば原油は速やかに下がり株式は安堵する。逆に夜間空爆がもう一度起きれば、「署名間近」は再び数日先に押される。今は終わりではなく、時間単位で分かれる分岐点だ。",
        ],
        "foot": "本記事は2026年6月12日（日本時間）時点の<strong>公開ライブ報道を総合・整理</strong>したもので、特定の立場を擁護しません。戦況・発言は分単位で変化し、媒体間で差異があり得ます（仲介国・停戦の効力など）。一部の時刻表記は報道が示した相対的時点（夜間・木曜・現地時刻）をそのまま移したもので、性質上推定を含む場合があるため、原典と公式発表で相互確認してください。",
        "nav_cat": "← 時事", "home": "🎮 GAMES",
        "bc": ["ホーム", "ブログ", "イラン・米国停戦 LIVE"],
        "og_title": "イラン・米国 停戦ライブ — 「週末署名」vs「停戦無意味」",
        "og_desc": "言葉は終戦間近、現場は夜間空爆。最新順でたどるライブ。（6/12時点）",
        "label": "時事", "asof_badge": "2026.6.12時点 · 分単位で変化",
    },
    "zh": {
        "lang": "zh-CN", "slug": f"{SLUG}-zh", "og_locale": "zh_CN",
        "title": "伊朗-美国停火直播 — 特朗普称\"周末可签\"，伊朗称\"停火已无意义\"",
        "desc": "特朗普称\"数日内、或在欧洲签署\"\"油价将像石头一样下跌\"，渲染终战在即；而伊朗外交部称夜间美军空袭已使\"4月8日停火变得毫无意义\"。按最新顺序追踪伊朗-美国战况与谈判直播。（截至6月12日）",
        "kicker": "📰 时事 · 中东局势 LIVE",
        "h1": '嘴上\"周末签署\"，天上<span class="hl">夜间空袭</span>',
        "dek": "眼下伊朗-美国局面，一个画面叠着两个场景。特朗普称\"漂亮地结束了战争\"，<strong>周末即可签署</strong>；同一时刻伊朗宣布<strong>夜间美军空袭</strong>已让停火\"毫无意义\"。下面按最新顺序、由近及远地追踪。",
        "asof": "本文按最新顺序整理截至<strong>2026年6月12日（北京时间）</strong>的公开直播报道。事态以分钟计变化，引用前请核对原始报道。",
        "read": "6分钟",
        "lead": "🔴 <strong>当下核心。</strong> 外交（话语）与战场（现场）错位。特朗普——\"漂亮地结束了与伊朗的战争……数日内，或在欧洲签署\"。伊朗外交部——夜间美军空袭是\"公然违反\"，使4月8日停火\"实际上毫无意义\"。两者同时为真。",
        "feed": [
            ("刚刚 · 特朗普", '<b>\"周末即可签署。\"</b> 特朗普总统对记者表示，美国\"漂亮地结束了与伊朗的战争\"，协议将在\"未来几天\"敲定，\"或在欧洲签署\"。但他也称谅解备忘录（MOU）\"略偏概念性\"。'),
            ("特朗普 · 霍尔木兹与油价", '<b>\"一签字霍尔木兹就正式开放。\"</b> 特朗普称协议签署的瞬间海峡即开放，美国的海上封锁也将作为\"协议的一部分\"解除，并称<em>\"油价将像石头一样下跌\"</em>。'),
            ("夜间 · 伊朗外交部", '<b>\"停火已无意义。\"</b> 伊朗外交部把夜间美军空袭定性为国际法的\"公然违反\"，称此次攻击<strong>实际上使4月8日停火变得毫无意义</strong>，并指责华盛顿发出矛盾信号。'),
            ("美军", '<b>以精确制导弹药打击伊朗目标。</b> 美海军陆战队、空军和海军资产向伊朗目标发射精确制导弹药，美方称这是\"对伊朗无端且持续的攻击的回应\"。打击发生在特朗普总统与国防部长赫格塞斯发出警告之后。'),
            ("6月10日 下午2:45（EDT）", '<b>中央司令部否认伊朗说法。</b> 美国中央司令部否认伊朗关于\"已封锁霍尔木兹海峡\"或\"袭击美军舰\"的说法。美国对伊朗境内\"多个目标\"发动了新打击。'),
            ("现场 · 阿曼附近", '<b>阿帕奇坠毁，2名机组获救。</b> 前一日在阿曼附近坠毁的美陆军AH-64阿帕奇直升机的2名机组人员获救，情况稳定。一名美国官员称直升机与伊朗无人机相撞，但是否蓄意尚不清楚。'),
            ("累计伤亡", '<b>黎巴嫩死亡逾3,600人 · 冲突破百日。</b> 据黎巴嫩卫生部统计，以色列对真主党的空袭已致逾3,600人死亡。本轮冲突已超过100天。'),
            ("市场", '<b>美国通胀三年来首破4%。</b> 在战争与油价压力下，美国通胀率三年来首次突破4%。霍尔木兹能否重开，是当前市场最大的实时看点。'),
            ("一句话背景", '2月28日特朗普宣布\"主要作战行动\"开始 → 最初两周停火 → 此后无限期延长，并维持封锁直到谈判\"以某种方式\"结束。4月8日停火是基准线。'),
        ],
        "read_h": "这幅图怎么读",
        "read_p": [
            "当下局面的本质是<strong>话语与现场之间的时差</strong>。谈判桌上飞着\"周末签署\"，同一个夜空却落下精确制导弹药、传出\"停火无意义\"的宣告。特朗普的乐观或是制造势头的施压牌，伊朗的强硬或是让步前的抬价术，两者也可能都是真心。",
            "若只盯一个实时指标，那就盯<strong>霍尔木兹海峡与油价</strong>。若如特朗普所言一签字就开放，油价将迅速回落、股市松一口气；若再来一次夜间空袭，\"签署在即\"便又被推迟数日。眼下不是结局，而是以小时为单位分岔的路口。",
        ],
        "foot": "本文综合整理截至2026年6月12日（北京时间）的<strong>公开直播报道</strong>，不为任何一方背书。战况与表态以分钟计变化，不同媒体间存在差异（斡旋国、停火效力等）。部分时间标注沿用报道给出的相对时点（夜间、周四、当地时间），鉴于议题性质可能含推测，请以原始报道与官方声明交叉核对。",
        "nav_cat": "← 时事", "home": "🎮 GAMES",
        "bc": ["首页", "博客", "伊朗-美国停火 LIVE"],
        "og_title": "伊朗-美国停火直播 — \"周末签署\"对\"停火无意义\"",
        "og_desc": "嘴上终战在即，天上夜间空袭。按最新顺序追踪的直播。（截至6/12）",
        "label": "时事", "asof_badge": "截至2026.6.12 · 以分钟计变化",
    },
}

CSS = """
  :root{--bg:#0b0f17;--surface:#141a26;--surface2:#1b2433;--border:#283246;--amber:#f59e0b;--amber2:#fbbf24;--red:#ef4444;--text:#d6deea;--dim:#8896ab;--white:#fff}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'Noto Sans KR',sans-serif;line-height:1.8;-webkit-font-smoothing:antialiased}
  .container{max-width:760px;margin:0 auto;background:var(--bg);min-height:100vh}
  .site-nav{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--border);background:rgba(11,15,23,.85);backdrop-filter:blur(8px);position:sticky;top:0;z-index:50}
  .site-nav a{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);text-decoration:none;letter-spacing:1px;transition:color .2s}
  .site-nav a:hover{color:var(--amber)}
  .hero{padding:30px 18px 22px;border-bottom:1px solid var(--border);background:radial-gradient(ellipse at 80% 0%,rgba(245,158,11,.10),transparent 60%),radial-gradient(ellipse at 0% 100%,rgba(239,68,68,.07),transparent 55%)}
  .kicker{display:inline-flex;align-items:center;gap:7px;font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#1a1206;background:linear-gradient(90deg,var(--amber),var(--amber2));padding:5px 11px;border-radius:20px;margin-bottom:14px}
  h1{font-size:29px;font-weight:900;color:var(--white);line-height:1.32;letter-spacing:-.02em;margin-bottom:14px}
  h1 .hl{color:var(--red)}
  .dek{font-size:15.5px;color:#aebccd;line-height:1.75;margin-bottom:16px}
  .dek strong{color:var(--white)}
  .meta{display:flex;gap:14px;flex-wrap:wrap;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);letter-spacing:.5px}
  .meta b{color:var(--amber2)}
  .asof{margin:14px 18px 0;padding:11px 14px;border:1px solid rgba(239,68,68,.3);border-left:3px solid var(--red);border-radius:8px;background:rgba(239,68,68,.05);font-size:12.5px;color:#c7b3b3;line-height:1.6}
  .asof strong{color:#f0d5d5}
  .body{padding:8px 18px 0}
  .body strong{color:var(--white)}
  .body em{color:var(--amber2);font-style:normal;font-weight:700}
  .live-lead{margin:18px 0 6px;padding:15px 16px;border:1px solid rgba(239,68,68,.45);border-radius:12px;background:linear-gradient(135deg,rgba(239,68,68,.12),rgba(245,158,11,.04));font-size:15.5px;line-height:1.8;color:#e7ecf3}
  .live-lead strong{color:#fff}
  .live-lead em{color:var(--amber2);font-style:normal;font-weight:700}
  h2{font-size:20px;font-weight:900;color:var(--white);margin:32px 0 6px;letter-spacing:-.01em;padding-top:18px;border-top:1px solid var(--border)}
  h2 .blink{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--red);margin-right:8px;animation:bl 1.3s steps(2,start) infinite;vertical-align:middle}
  @keyframes bl{50%{opacity:.25}}
  .feed{margin:12px 0;border-left:2px solid var(--border);padding-left:0}
  .entry{position:relative;padding:13px 0 13px 20px;border-bottom:1px solid var(--border)}
  .entry:last-child{border-bottom:none}
  .entry::before{content:"";position:absolute;left:-7px;top:18px;width:11px;height:11px;border-radius:50%;background:var(--surface2);border:2px solid var(--dim)}
  .entry.hot::before{background:var(--red);border-color:var(--red);box-shadow:0 0 0 4px rgba(239,68,68,.15)}
  .entry .t{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:700;letter-spacing:.5px;color:#1a1206;background:var(--amber2);padding:2px 8px;border-radius:5px;margin-bottom:7px}
  .entry.hot .t{background:var(--red);color:#fff}
  .entry .c{font-size:15px;line-height:1.85;color:#cdd8e6}
  .entry .c b{color:var(--white)}
  .read-p{font-size:15.5px;line-height:1.9;color:var(--text);margin:14px 0}
  .read-p strong{color:var(--white)}
  .foot{margin:30px 18px 18px;padding:14px 16px;background:var(--surface);border:1px solid var(--border);border-radius:12px;font-size:11.5px;line-height:1.75;color:var(--dim)}
  .foot strong{color:var(--amber2)}
  .src{margin-top:8px;display:flex;flex-wrap:wrap;gap:6px}
  .src a{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--amber);text-decoration:none;border:1px solid var(--border);padding:3px 8px;border-radius:6px}
  @media(min-width:768px){h1{font-size:34px}}
"""

BUILD_CHECK = (
    '<!--lp-build-check:start-->\n'
    f'<meta name="lp-build" content="{STAMP}">\n'
    f'<script>(function(){{var B="{STAMP}";try{{fetch("/build.json?_="+Date.now(),{{cache:"no-store"}}).then(function(r){{return r.ok?r.json():null}}).then(function(d){{if(!d||!d.v||d.v===B)return;var k="lp_build_"+B;try{{if(sessionStorage.getItem(k))return;sessionStorage.setItem(k,"1");}}catch(e){{}}var u=new URL(location.href);u.searchParams.set("_b",d.v);location.replace(u.toString());}}).catch(function(){{}});}}catch(e){{}}}})();</script>\n'
    '<!--lp-build-check:end-->'
)

ALT_HL = [("ko", "ko"), ("en", "en"), ("ja", "ja"), ("zh", "zh")]
LIVE_H = {"ko": "실시간 흐름 — 최신순", "en": "Live feed — newest first",
          "ja": "リアルタイムの流れ — 最新順", "zh": "实时动态 — 由近及远"}


def build(lang):
    c = L[lang]
    alt_links = "\n".join(
        f'<link rel="alternate" hreflang="{hl}" href="https://luckyplz.com/blog/{L[k]["slug"]}/">'
        for hl, k in ALT_HL)

    entries = []
    for i, (t, body) in enumerate(c["feed"]):
        hot = " hot" if i < 3 else ""   # freshest 3 glow red
        entries.append(f'<div class="entry{hot}"><span class="t">{t}</span>'
                       f'<div class="c">{body}</div></div>')
    feed_html = "\n".join(entries)

    read_p = "\n".join(f'<p class="read-p">{p}</p>' for p in c["read_p"])
    src_links = "\n    ".join(
        f'<a href="{url}" target="_blank" rel="noopener">{name}</a>' for name, url in SRC)

    ld_post = json.dumps({
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": c["title"], "description": c["desc"],
        "datePublished": "2026-06-12", "dateModified": "2026-06-12",
        "inLanguage": c["lang"],
        "image": f"https://luckyplz.com/assets/blog/{SLUG}-{lang}.png",
        "author": {"@type": "Organization", "name": "Lucky Please", "url": "https://luckyplz.com/"},
        "publisher": {"@type": "Organization", "name": "Lucky Please",
                      "logo": {"@type": "ImageObject", "url": "https://luckyplz.com/assets/icon-192.png"}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"https://luckyplz.com/blog/{c['slug']}/"},
    }, ensure_ascii=False)
    ld_bc = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": c["bc"][0], "item": "https://luckyplz.com/"},
            {"@type": "ListItem", "position": 2, "name": c["bc"][1], "item": "https://luckyplz.com/blog/"},
            {"@type": "ListItem", "position": 3, "name": c["bc"][2], "item": f"https://luckyplz.com/blog/{c['slug']}/"},
        ]}, ensure_ascii=False)

    og_img = f"https://luckyplz.com/assets/blog/{SLUG}-{lang}.png?v={STAMP}"
    meta_date = {"ko": "2026. 6. 12.", "en": "Jun 12, 2026", "ja": "2026.6.12", "zh": "2026.6.12"}[lang]

    html = f"""<!DOCTYPE html>
<html lang="{c['lang']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
{BUILD_CHECK}
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<title>{c['title']} | Lucky Please</title>
<meta name="description" content="{c['desc']}">
<link rel="canonical" href="https://luckyplz.com/blog/{c['slug']}/">
{alt_links}
<link rel="alternate" hreflang="x-default" href="https://luckyplz.com/blog/{SLUG}-en/">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Lucky Please">
<meta property="og:locale" content="{c['og_locale']}">
<meta property="og:title" content="{c['og_title']}">
<meta property="og:description" content="{c['og_desc']}">
<meta property="og:url" content="https://luckyplz.com/blog/{c['slug']}/">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="article:published_time" content="2026-06-12T21:00:00+09:00">
<meta property="article:section" content="World">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{c['og_title']}">
<meta name="twitter:description" content="{c['og_desc']}">
<meta name="twitter:image" content="{og_img}">
<script type="application/ld+json">{ld_post}</script>
<script type="application/ld+json">{ld_bc}</script>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0b0f17">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5370817769801923" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NZDPE3H3DQ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-NZDPE3H3DQ');</script>
<style>{CSS}</style>
</head>
<body>
<div class="container">

<nav class="site-nav">
  <a href="/blog/?cat=issue">{c['nav_cat']}</a>
  <a href="/">{c['home']}</a>
</nav>

<header class="hero">
  <span class="kicker">{c['kicker']}</span>
  <h1>{c['h1']}</h1>
  <p class="dek">{c['dek']}</p>
  <div class="meta"><span>{meta_date}</span><span><b>{c['read']}</b></span><span>{c['asof_badge']}</span></div>
</header>

<div class="asof">⏱ {c['asof']}</div>

<div class="body">

<div class="live-lead">{c['lead']}</div>

<h2><span class="blink"></span>{LIVE_H[lang]}</h2>
<div class="feed">
{feed_html}
</div>

<h2>{c['read_h']}</h2>
{read_p}

<div data-lp-ad="blog" style="margin:24px 0;"></div>

</div>

<footer class="foot">
  <strong>📌 출처 &amp; 안내 · Source &amp; Note</strong><br>
  {c['foot']}
  <div class="src">
    {src_links}
  </div>
</footer>

</div>
<script src="/js/blogReadingAids.js?v={STAMP}"></script>
<script src="/blog/posts.js?v={STAMP}"></script>
<script src="/js/blogReactions.js?v={STAMP}"></script>
<script src="/js/blogSubscribe.js?v={STAMP}"></script>
<script src="/js/blogRelated.js?v={STAMP}"></script>
<script src="/js/siteFooter.js?v={STAMP}"></script>
</body>
</html>
"""
    out = BLOG / c["slug"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote blog/{c['slug']}/index.html")


def main():
    for lang in ("ko", "en", "ja", "zh"):
        build(lang)


if __name__ == "__main__":
    main()
