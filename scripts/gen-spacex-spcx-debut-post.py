#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4-language SpaceX (SPCX) IPO debut analysis — first trading day (category: stocks).

Objective, data-driven markets analysis of SpaceX's Nasdaq debut on June 12,
2026. All figures from credible reporting (NPR, CNBC, Yahoo Finance, NBC,
Morningstar, Motley Fool, TechCrunch, FT). Not investment advice; clearly
labels the bull/bear split and the valuation risk. Indexed (manual longform).

Output: public/blog/spacex-spcx-ipo-debut-2026[/-en/-ja/-zh]/index.html
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "public" / "blog"
SLUG = "spacex-spcx-ipo-debut-2026"
STAMP = json.loads((ROOT / "public" / "build.json").read_text())["v"]

SRC = [
    ("NPR", "https://www.npr.org/2026/06/12/nx-s1-5855004/stock-ai-spacex-ipo-elon-musk"),
    ("CNBC · SPCX debut", "https://www.cnbc.com/2026/06/12/spacex-ipo-spcx-live-updates.html"),
    ("Yahoo Finance · live", "https://finance.yahoo.com/markets/live/spacex-ipo-live-updates-elon-musks-spacex-set-to-make-record-debut-as-dow-sp-500-nasdaq-rise-230015961.html"),
    ("NBC News", "https://www.nbcnews.com/business/markets/spacex-ipo-stock-price-rcna349760"),
    ("Morningstar via CNBC", "https://www.cnbc.com/2026/06/03/morningstar-spacex-ipo-target-price-nasdaq.html"),
    ("Motley Fool · lock-up", "https://www.fool.com/investing/2026/05/26/the-spacex-ipo-has-an-unusual-lockup-policy-for-in/"),
]

# stat grid: (value, label_ko, label_en, label_ja, label_zh)
STATS = [
    ("$160.95", "첫날 종가 (+19%)", "Day-1 close (+19%)", "初日終値 (+19%)", "首日收盘 (+19%)"),
    ("$135", "공모가", "IPO price", "公開価格", "发行价"),
    ("$750억", "조달액 · 사상 최대 IPO", "Raised · largest IPO ever", "調達額 · 史上最大IPO", "募资 · 史上最大IPO"),
    ("$2조+", "첫날 종가 시가총액", "Day-1 close market cap", "初日終値 時価総額", "首日收盘市值"),
]

L = {
    "ko": {
        "lang": "ko", "slug": SLUG, "og_locale": "ko_KR",
        "title": "스페이스X(SPCX) 상장 첫날 완전 분석 — +19% $160.95 마감, 시총 2조 달러 돌파",
        "desc": "스페이스X가 6월 12일 나스닥(SPCX)에 데뷔해 첫날 19% 올라 $160.95로 마감, 시총 2조 달러를 넘었다. 공모가·시초가·장중 흐름, 시가총액, Starlink 실적 기반 밸류에이션, 강세·약세 전망, 단계적 매물 잠금까지 공신력 데이터로 상세 분석.",
        "kicker": "📈 증시 · SpaceX IPO 분석",
        "h1": '스페이스X 상장 첫날, <span class="hl">+19%</span>로 2조 달러를 넘다',
        "dek": "6월 12일, 스페이스X가 나스닥에 <strong>SPCX</strong>로 데뷔했다. 공모가 $135로 <strong>약 750억 달러</strong>를 조달한 사상 최대 IPO이자, 첫 거래일을 <strong>$160.95(+19%)</strong>로 마치며 시가총액 <strong>2조 달러</strong>를 넘긴 역사적 데뷔. 첫날 주가 흐름·시가총액·밸류에이션·전망을 객관적 데이터로 뜯어본다. (첫 거래일 마감 기준)",
        "read": "9분",
        "secs": [
            ("첫 거래일 주가 흐름", "table", [
                ("공모가 (IPO)", "$135", "기준점 · 약 750억 달러 조달"),
                ("시초가", "$150", "공모가 대비 +11%"),
                ("장중 고점", "+30% 부근", "한때 시총 약 2.25조 달러"),
                ("종가", "$160.95", "공모가 대비 +19%, 시총 2조 달러 돌파"),
            ]),
            ("시가총액 — 단숨에 세계 최상위권", "p", [
                "공모가 $135 기준 시가총액은 약 <strong>1.77조 달러</strong>로 출발했지만, 첫날 19% 상승 마감으로 <strong>2조 달러를 넘겼다</strong>(장중 한때 +30%로 약 2.25조 달러). 데뷔 첫날에 세계에서 가장 가치 있는 상장사 중 하나로 올라선 것이다.",
                "조달 규모 약 <strong>750억 달러</strong>는 <strong>역대 최대 IPO</strong>로 기록됐다. 이 상승으로 일론 머스크는 보유 지분 가치에 힘입어 <strong>세계 최초의 조만장자(trillionaire)</strong>가 된 것으로 보도됐다.",
            ]),
            ("밸류에이션 해부 — 무엇이 2조 달러를 정당화하나", "p", [
                "2025년 스페이스X 총매출은 약 <strong>186억 달러</strong>로 추정된다. 이 가운데 위성통신 <strong>Starlink가 114억 달러</strong>로 전체의 <strong>61%</strong>를 차지했고, 전년(77억 달러) 대비 <strong>48% 성장</strong>했다. Starlink는 영업이익 <strong>44억 달러</strong>를 내며 사실상 회사의 유일한 이익 엔진이다(전사 기준으론 GAAP 적자). 2026년 2월 기준 Starlink 가입자는 160개국 <strong>1,000만 명 이상</strong>.",
                "문제는 배수다. 1.8조 달러 밸류에이션은 <strong>2025년 매출의 약 60~96배(P/S)</strong>에 해당한다. 이는 가장 비싼 빅테크조차 압도하는 수준으로, <em>역사상 어떤 기업도 달성한 적 없는 성장률을 이미 가격에 반영</em>했다는 의미다. 즉 지금 주가는 '현재 실적'이 아니라 'Starlink·Starship·우주 인프라가 향후 수년간 폭발적으로 성장한다'는 시나리오에 베팅하고 있다.",
            ]),
            ("강세 vs 약세 — 갈린 전망", "bullbear", [
                ("강세", ["Starlink의 위성통신 사실상 독점 + 가입자 1,000만 돌파", "Starship 상용화 시 발사 단가 파괴 → 신규 시장 창출", "xAI 등 머스크 생태계 인프라 시너지", "이 시나리오에선 2조 달러 이상도 정당화 가능"]),
                ("약세", ["Morningstar: \"심하게 고평가, IPO 후 더 싼 가격에 살 기회\"가 올 것 — 적정가를 공모 목표의 <strong>절반 이하</strong>로 제시", "P/S 60배는 실적이 못 따라오면 급격한 멀티플 정상화 위험", "2026년 거래 레인지 전망 <strong>$75~$200</strong>, 약세 바닥은 $75 부근", "전사 GAAP 적자 — 이익은 Starlink에 집중"]),
            ]),
            ("매물 잠금(Lock-up) — 초반 변동성의 핵심 변수", "p", [
                "스페이스X는 흔한 '180일 일괄 해제' 대신 <strong>단계적(staggered) 구조</strong>를 택했다. 2분기 실적(7~8월) 후 내부자 보유분의 최대 <strong>20%</strong>(주가가 $135 대비 30% 이상이면 <strong>+10%</strong>)가 풀리고, IPO 후 <strong>70·90·105·120·135일</strong> 시점마다 <strong>각 7%씩</strong> 추가로 매도 가능해진다. 그리고 <strong>180일</strong>에 전량 해제된다.",
                "주목할 점은 <strong>머스크 본인은 전체 lock-up 대상</strong>이라 조기 해제에 참여하지 못한다는 것. 단계적 구조는 180일 한 시점에 몰리는 매도 압력을 분산시키지만, <em>역설적으로 상장 초반부터 변동성을 키울 수 있다</em>. 7~8월 1차 해제와 2분기 첫 실적이 초기 주가의 1차 시험대다.",
            ]),
            ("종합 전망", "p", [
                "데뷔는 화려했지만, 앞으로의 그림은 <strong>'성장 실현 vs 멀티플 정상화'의 줄다리기</strong>다. 단기적으로는 (1) 단계적 lock-up 해제, (2) 7~8월 첫 분기 실적, (3) 60배 P/S에 대한 시장의 재평가가 변동성을 지배할 가능성이 크다. Starlink 가입자·매출이 시장 기대치를 계속 상회하고 Starship 진척이 가시화되면 강세 시나리오가 힘을 받지만, 성장이 한 분기라도 둔화하면 약세 진영의 '$75 바닥론'이 빠르게 소환될 수 있다.",
                "한 줄 요약: <strong>지금 SPCX 주가는 실적이 아니라 미래에 대한 신뢰를 사고 있다.</strong> 그 신뢰가 분기 실적으로 증명되는지를 향후 6개월(=180일 lock-up 만기까지)이 결정한다.",
            ]),
        ],
        "foot": "본 글은 2026년 6월 13일(한국시간) 기준 <strong>공개 보도·기관 리서치를 종합·정리</strong>한 정보 제공용 분석이며, 특정 종목의 매수·매도 권유가 아닙니다. 수치는 보도 시점 기준이며 매체 간 차이가 있을 수 있고(매출·시총·밸류에이션 추정), 주가는 실시간으로 변합니다. 투자 판단과 책임은 투자자 본인에게 있습니다.",
        "nav_cat": "← 증시", "home": "🎮 GAMES",
        "bc": ["홈", "블로그", "스페이스X 상장 첫날 분석"],
        "og_title": "스페이스X(SPCX) 상장 첫날 +19% — 시총 2조 달러 돌파",
        "og_desc": "공모가 $135 → 종가 $160.95. 시총·Starlink 실적 밸류에이션·강세약세·lock-up까지 상세 분석.",
        "label": "증시", "asof_badge": "첫 거래일 마감 기준 · 2026.6.13",
        "series_link": "스페이스X 심층 시리즈 — /blog/spacex-ipo-2026/",
    },
    "en": {
        "lang": "en", "slug": f"{SLUG}-en", "og_locale": "en_US",
        "title": "SpaceX (SPCX) IPO Debut, Fully Analyzed — Closes +19% at $160.95, Past a $2 Trillion Cap",
        "desc": "SpaceX debuted on the Nasdaq (SPCX) on June 12, closing up 19% at $160.95 and topping a $2 trillion market cap. A data-driven breakdown of the day-1 price action, market cap, Starlink-based valuation, the bull/bear split, and the unusual staggered lock-up.",
        "kicker": "📈 MARKETS · SpaceX IPO ANALYSIS",
        "h1": 'SpaceX\'s First Day: <span class="hl">+19%</span> and Past $2 Trillion',
        "dek": "On June 12, SpaceX debuted on the Nasdaq as <strong>SPCX</strong>. Priced at $135, it raised about <strong>$75 billion</strong> — the largest IPO ever — and closed its first session at <strong>$160.95 (+19%)</strong>, vaulting past a <strong>$2 trillion</strong> market cap. Here is the day-1 price action, market cap, valuation, and outlook, by the numbers. (As of the first trading day's close.)",
        "read": "9 min",
        "secs": [
            ("Day-1 price action", "table", [
                ("IPO price", "$135", "Baseline · ~$75B raised"),
                ("Open", "$150", "+11% over the offer price"),
                ("Intraday high", "≈ +30%", "Briefly ~$2.25T market value"),
                ("Close", "$160.95", "+19% over offer, market cap above $2T"),
            ]),
            ("Market cap — instantly among the world's largest", "p", [
                "At the $135 offer price the company started near a <strong>$1.77 trillion</strong> cap, but the 19% first-day gain pushed it <strong>past $2 trillion</strong> (it briefly touched ~$2.25T at the intraday +30% peak). On day one it joined the ranks of the most valuable listed companies on Earth.",
                "The roughly <strong>$75 billion</strong> raised stands as the <strong>largest IPO on record</strong>. On the back of his stake's value, Elon Musk was reported to have become the <strong>world's first trillionaire</strong>.",
            ]),
            ("Valuation, dissected — what justifies $2 trillion", "p", [
                "SpaceX's 2025 total revenue is estimated near <strong>$18.6 billion</strong>. Of that, <strong>Starlink contributed $11.4 billion</strong> — <strong>61%</strong> of the total and up <strong>48%</strong> from $7.7B in 2024. Starlink also produced <strong>$4.4 billion in operating profit</strong>, making it effectively the company's only profit engine (the broader company posts a GAAP loss). By February 2026 Starlink had surpassed <strong>10 million subscribers</strong> across 160 countries.",
                "The catch is the multiple. A $1.8T valuation is roughly <strong>60–96× 2025 revenue</strong> (price-to-sales) — a level that dwarfs even the priciest megacap tech and <em>already prices in growth no company in history has achieved</em>. In other words, the stock isn't pricing current results; it's betting that Starlink, Starship, and space infrastructure compound explosively for years.",
            ]),
            ("Bull vs bear — a split outlook", "bullbear", [
                ("Bull", ["Starlink's de facto satellite-broadband dominance + 10M subscribers", "Starship, once operational, collapses launch cost → new markets", "Synergy with Musk's wider stack (xAI and others)", "In this scenario, $2T+ can be justified"]),
                ("Bear", ["Morningstar: \"significantly overvalued,\" with chances to buy cheaper after the IPO — fair value set <strong>below half</strong> the offer target", "A ~60× P/S risks a sharp multiple reset if growth disappoints", "2026 trading range seen at <strong>$75–$200</strong>, with a bear floor near $75", "Company-wide GAAP loss — profit is concentrated in Starlink"]),
            ]),
            ("The lock-up — the key driver of early volatility", "p", [
                "Rather than the usual single 180-day cliff, SpaceX chose a <strong>staggered structure</strong>. After Q2 earnings (Jul–Aug), up to <strong>20%</strong> of insider shares unlock (plus <strong>10%</strong> more if the stock is 30%+ above $135), and another <strong>7%</strong> frees up at each of the <strong>70/90/105/120/135-day</strong> marks post-IPO. <strong>All shares</strong> unlock at <strong>180 days</strong>.",
                "Notably, <strong>Musk himself is under the full lock-up</strong> and cannot use the early-release windows. The staggered design spreads out the selling pressure that usually bunches at the 180-day mark, but <em>it can paradoxically raise volatility early</em> in the stock's public life. The first unlock and the first quarterly print this summer are the early stock's first real tests.",
            ]),
            ("Bottom line", "p", [
                "The debut was spectacular, but from here it's a <strong>tug-of-war between delivering growth and normalizing the multiple</strong>. Near term, three things likely dominate: (1) the staggered lock-up unlocks, (2) the first quarterly results in Jul–Aug, and (3) the market re-rating that ~60× P/S. If Starlink subscribers and revenue keep beating expectations and Starship progress becomes visible, the bull case gains; if growth cools even for a quarter, the bears' \"$75 floor\" gets summoned fast.",
                "In one line: <strong>SPCX is pricing belief in the future, not current earnings.</strong> Whether that belief is validated by quarterly results is what the next six months — to the 180-day lock-up expiry — will decide.",
            ]),
        ],
        "foot": "This article compiles <strong>public reporting and institutional research as of June 13, 2026 (KST)</strong> for information only; it is not a recommendation to buy or sell any security. Figures reflect reporting at the time and may differ across outlets (revenue, market cap, valuation are estimates); prices move in real time. Investment decisions and their consequences are your own.",
        "nav_cat": "← MARKETS", "home": "🎮 GAMES",
        "bc": ["Home", "Blog", "SpaceX IPO Debut Analysis"],
        "og_title": "SpaceX (SPCX) Debuts +19% — Past a $2 Trillion Cap",
        "og_desc": "Priced $135 → closed $160.95. Market cap, Starlink valuation, bull/bear, and the lock-up — analyzed.",
        "label": "Markets", "asof_badge": "First trading day close · Jun 13, 2026",
        "series_link": "Deep SpaceX series → /blog/spacex-ipo-2026-en/",
    },
    "ja": {
        "lang": "ja", "slug": f"{SLUG}-ja", "og_locale": "ja_JP",
        "title": "スペースX(SPCX)上場初日 徹底分析 — +19%の$160.95で終了、時価総額2兆ドル突破",
        "desc": "スペースXが6月12日にナスダック(SPCX)へ上場し、初日19%高の$160.95で終了、時価総額2兆ドルを突破。公開価格・初値・日中の値動き、時価総額、Starlink業績に基づくバリュエーション、強気・弱気見通し、段階的ロックアップまでを信頼できるデータで詳細分析。",
        "kicker": "📈 株式市場 · スペースXIPO分析",
        "h1": 'スペースX上場初日、<span class="hl">+19%</span>で2兆ドル超え',
        "dek": "6月12日、スペースXがナスダックに<strong>SPCX</strong>として上場。公開価格$135で<strong>約750億ドル</strong>を調達した史上最大のIPOであり、初取引日を<strong>$160.95(+19%)</strong>で終え、時価総額<strong>2兆ドル</strong>を突破する歴史的デビューとなった。初日の値動き・時価総額・バリュエーション・見通しを客観データで読み解く。（初取引日の終値時点）",
        "read": "9分",
        "secs": [
            ("初取引日の値動き", "table", [
                ("公開価格 (IPO)", "$135", "基準 · 約750億ドル調達"),
                ("初値", "$150", "公開価格比 +11%"),
                ("日中高値", "+30%前後", "一時 時価総額 約2.25兆ドル"),
                ("終値", "$160.95", "公開価格比 +19%、時価総額2兆ドル突破"),
            ]),
            ("時価総額 — 一気に世界最上位", "p", [
                "公開価格$135での時価総額は約<strong>1.77兆ドル</strong>で始まったが、初日19%高で<strong>2兆ドルを突破</strong>（日中+30%の高値で一時約2.25兆ドル）。デビュー初日に世界で最も価値ある上場企業の一角へ躍り出た。",
                "調達規模 約<strong>750億ドル</strong>は<strong>史上最大のIPO</strong>として記録された。保有株の価値により、イーロン・マスクは<strong>世界初の兆万長者(trillionaire)</strong>になったと報じられている。",
            ]),
            ("バリュエーション解剖 — 何が2兆ドルを正当化するか", "p", [
                "2025年のスペースX総売上は約<strong>186億ドル</strong>と推定。うち衛星通信<strong>Starlinkが114億ドル</strong>で全体の<strong>61%</strong>を占め、前年(77億ドル)比<strong>48%増</strong>。Starlinkは営業利益<strong>44億ドル</strong>を稼ぎ、事実上唯一の利益エンジンだ（全社ベースではGAAP赤字）。2026年2月時点でStarlink加入者は160カ国<strong>1,000万人超</strong>。",
                "問題は倍率だ。1.8兆ドルのバリュエーションは<strong>2025年売上の約60〜96倍(PSR)</strong>に相当し、最も割高な大型テックすら凌ぐ水準で、<em>歴史上どの企業も達成していない成長率を既に織り込んでいる</em>。今の株価は『現在の業績』ではなく『Starlink・Starship・宇宙インフラが今後数年で爆発的に伸びる』というシナリオに賭けている。",
            ]),
            ("強気 vs 弱気 — 割れる見通し", "bullbear", [
                ("強気", ["Starlinkの衛星通信ほぼ独占 + 加入者1,000万突破", "Starship商用化で打ち上げコスト破壊 → 新市場創出", "xAIなどマスク経済圏インフラとの相乗効果", "このシナリオなら2兆ドル超も正当化可能"]),
                ("弱気", ["Morningstar:「著しく割高、IPO後により安く買う機会」— 適正値を公開目標の<strong>半分以下</strong>と提示", "PSR60倍は業績が追いつかなければ急激な倍率調整リスク", "2026年の想定レンジは<strong>$75〜$200</strong>、弱気の底は$75付近", "全社GAAP赤字 — 利益はStarlinkに集中"]),
            ]),
            ("ロックアップ — 初期ボラティリティの鍵", "p", [
                "スペースXは一般的な『180日一括解除』ではなく<strong>段階的(staggered)構造</strong>を採用。第2四半期決算(7〜8月)後にインサイダー株の最大<strong>20%</strong>（株価が$135比30%以上なら<strong>+10%</strong>）が解放され、IPO後<strong>70・90・105・120・135日</strong>の各時点で<strong>さらに7%ずつ</strong>売却可能になる。そして<strong>180日</strong>で全株が解除される。",
                "注目すべきは<strong>マスク本人は全体ロックアップ対象</strong>で早期解除に参加できない点。段階的構造は180日の一点に集中する売り圧力を分散させるが、<em>逆に上場初期のボラティリティを高めうる</em>。7〜8月の初回解除と初の四半期決算が、初期株価の最初の試金石だ。",
            ]),
            ("総合見通し", "p", [
                "デビューは華々しかったが、ここからは<strong>『成長の実現 vs 倍率の正常化』の綱引き</strong>だ。短期的には(1)段階的ロックアップ解除、(2)7〜8月の初四半期決算、(3)PSR60倍に対する市場の再評価がボラティリティを支配する公算が大きい。Starlinkの加入者・売上が市場予想を上回り続け、Starshipの進捗が見えれば強気が勢いづくが、成長が一四半期でも鈍れば弱気陣営の『$75底値論』が素早く呼び戻される。",
                "一言で言えば — <strong>今のSPCX株価は業績ではなく未来への信頼を買っている。</strong> その信頼が四半期決算で証明されるかを、今後6カ月（=180日ロックアップ満了まで）が決める。",
            ]),
        ],
        "foot": "本記事は2026年6月13日（日本時間）時点の<strong>公開報道・機関リサーチを総合・整理</strong>した情報提供目的の分析であり、特定銘柄の売買推奨ではありません。数値は報道時点のもので媒体間で差異があり得（売上・時価総額・バリュエーションは推定）、株価はリアルタイムで変動します。投資判断と結果はご自身の責任です。",
        "nav_cat": "← 株式市場", "home": "🎮 GAMES",
        "bc": ["ホーム", "ブログ", "スペースX上場初日分析"],
        "og_title": "スペースX(SPCX)初日+19% — 時価総額2兆ドル突破",
        "og_desc": "公開価格$135→終値$160.95。時価総額・Starlinkバリュエーション・強弱・ロックアップを分析。",
        "label": "株式市場", "asof_badge": "初取引日終値時点 · 2026.6.13",
        "series_link": "スペースX深掘りシリーズ → /blog/spacex-ipo-2026-ja/",
    },
    "zh": {
        "lang": "zh-CN", "slug": f"{SLUG}-zh", "og_locale": "zh_CN",
        "title": "SpaceX(SPCX)上市首日全解析 — 收涨19%报160.95美元，市值突破2万亿美元",
        "desc": "SpaceX于6月12日登陆纳斯达克(SPCX)，首日收涨19%报160.95美元，市值突破2万亿美元。基于权威数据详解发行价、开盘价、日内走势、市值、基于Starlink业绩的估值、多空展望，以及不同寻常的分阶段解禁。",
        "kicker": "📈 股市 · SpaceX IPO 分析",
        "h1": 'SpaceX上市首日，<span class="hl">+19%</span>市值破2万亿',
        "dek": "6月12日，SpaceX以<strong>SPCX</strong>登陆纳斯达克。发行价135美元，募资约<strong>750亿美元</strong>，为史上最大IPO；首个交易日收报<strong>160.95美元(+19%)</strong>，市值一举突破<strong>2万亿美元</strong>，缔造历史性首秀。下面用客观数据拆解首日走势、市值、估值与展望。（截至首个交易日收盘）",
        "read": "9分钟",
        "secs": [
            ("首个交易日走势", "table", [
                ("发行价 (IPO)", "$135", "基准 · 募资约750亿美元"),
                ("开盘价", "$150", "较发行价 +11%"),
                ("日内高点", "约 +30%", "一度市值约2.25万亿美元"),
                ("收盘价", "$160.95", "较发行价 +19%，市值突破2万亿美元"),
            ]),
            ("市值 — 一举跻身全球最大之列", "p", [
                "按发行价135美元，市值起步约<strong>1.77万亿美元</strong>；首日上涨19%后<strong>突破2万亿美元</strong>（日内+30%高点时一度约2.25万亿美元）。上市首日便跻身全球最具价值的上市公司之列。",
                "约<strong>750亿美元</strong>的募资规模创下<strong>史上最大IPO</strong>纪录。凭借所持股份价值，据报道埃隆·马斯克成为<strong>全球首位万亿富翁(trillionaire)</strong>。",
            ]),
            ("估值拆解 — 什么撑起2万亿", "p", [
                "SpaceX 2025年总营收估计约<strong>186亿美元</strong>。其中卫星通信<strong>Starlink贡献114亿美元</strong>，占总营收<strong>61%</strong>，较上年(77亿)增长<strong>48%</strong>。Starlink还实现营业利润<strong>44亿美元</strong>，几乎是公司唯一的利润引擎（公司整体为GAAP亏损）。截至2026年2月，Starlink用户已超<strong>1,000万</strong>，覆盖160个国家。",
                "问题在于倍数。1.8万亿美元估值约为<strong>2025年营收的60～96倍(市销率)</strong>，远超最贵的大型科技股，<em>已把历史上从未有企业实现过的增速计入价格</em>。换言之，当前股价买的不是‘当下业绩’，而是‘Starlink、Starship与太空基建未来数年爆发式增长’的剧本。",
            ]),
            ("多空对决 — 分歧的展望", "bullbear", [
                ("看多", ["Starlink在卫星宽带近乎垄断 + 用户破千万", "Starship商用化将打破发射成本 → 开辟新市场", "与马斯克生态(xAI等)的基建协同", "在此情景下2万亿以上可被合理化"]),
                ("看空", ["晨星(Morningstar)：\"严重高估，IPO后有机会更便宜买入\"——给出的合理价不到发行目标的<strong>一半</strong>", "60倍市销率，一旦业绩跟不上将面临剧烈的估值回归", "2026年交易区间预期<strong>$75～$200</strong>，看空底部约75美元", "公司整体GAAP亏损——利润集中于Starlink"]),
            ]),
            ("解禁(Lock-up) — 早期波动的关键变量", "p", [
                "SpaceX没有采用常见的‘180天一次性解禁’，而是选择<strong>分阶段(staggered)结构</strong>。二季度财报(7～8月)后，内部人股份至多<strong>20%</strong>解禁（若股价较135美元高出30%以上则再<strong>+10%</strong>）；IPO后<strong>第70/90/105/120/135天</strong>各再解禁<strong>7%</strong>；<strong>第180天</strong>全部解禁。",
                "值得注意的是<strong>马斯克本人受全程解禁约束</strong>，无法参与提前解禁。分阶段设计分散了通常集中在180天的抛压，但<em>反而可能在上市早期放大波动</em>。7～8月的首次解禁与首份季报，是早期股价的第一道试金石。",
            ]),
            ("综合展望", "p", [
                "首秀华丽，但接下来是<strong>‘兑现增长 vs 估值回归’的拉锯</strong>。短期内，(1)分阶段解禁、(2)7～8月首份季报、(3)市场对60倍市销率的重定价，很可能主导波动。若Starlink用户与营收持续超预期、Starship进展可见，看多情景将获动能；但只要增长哪怕一个季度放缓，看空阵营的‘75美元底部论’就会被迅速唤起。",
                "一句话：<strong>当前SPCX买的是对未来的信任，而非当下盈利。</strong> 这份信任能否被季度业绩证明，将由未来六个月（即180天解禁到期前）决定。",
            ]),
        ],
        "foot": "本文综合整理截至2026年6月13日（北京时间）的<strong>公开报道与机构研究</strong>，仅供信息参考，不构成对任何证券的买卖建议。数据为报道时点口径，不同媒体间可能存在差异（营收、市值、估值均为估算），股价实时变动。投资决策及其后果由投资者自行承担。",
        "nav_cat": "← 股市", "home": "🎮 GAMES",
        "bc": ["首页", "博客", "SpaceX上市首日分析"],
        "og_title": "SpaceX(SPCX)首日+19% — 市值突破2万亿美元",
        "og_desc": "发行价$135→收盘$160.95。市值、Starlink估值、多空、解禁全解析。",
        "label": "股市", "asof_badge": "首个交易日收盘 · 2026.6.13",
        "series_link": "SpaceX深度系列 → /blog/spacex-ipo-2026-zh/",
    },
}

CSS = """
  :root{--bg:#0a0e17;--surface:#131a28;--surface2:#1a2436;--border:#26334a;--up:#22c55e;--up2:#4ade80;--gold:#fbbf24;--down:#ef4444;--text:#d4dded;--dim:#8090a8;--white:#fff}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'Noto Sans KR',sans-serif;line-height:1.85;-webkit-font-smoothing:antialiased}
  .container{max-width:760px;margin:0 auto;background:var(--bg);min-height:100vh}
  .site-nav{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--border);background:rgba(10,14,23,.85);backdrop-filter:blur(8px);position:sticky;top:0;z-index:50}
  .site-nav a{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);text-decoration:none;letter-spacing:1px;transition:color .2s}
  .site-nav a:hover{color:var(--up2)}
  .hero{padding:30px 18px 22px;border-bottom:1px solid var(--border);background:radial-gradient(ellipse at 80% 0%,rgba(34,197,94,.12),transparent 60%),radial-gradient(ellipse at 0% 100%,rgba(251,191,36,.06),transparent 55%)}
  .kicker{display:inline-flex;align-items:center;gap:7px;font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#04140a;background:linear-gradient(90deg,var(--up),var(--up2));padding:5px 11px;border-radius:20px;margin-bottom:14px}
  h1{font-size:29px;font-weight:900;color:var(--white);line-height:1.3;letter-spacing:-.02em;margin-bottom:14px}
  h1 .hl{color:var(--up2)}
  .dek{font-size:15.5px;color:#aebccd;line-height:1.75;margin-bottom:16px}
  .dek strong{color:var(--white)}
  .meta{display:flex;gap:14px;flex-wrap:wrap;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);letter-spacing:.5px}
  .meta b{color:var(--gold)}
  .stats{display:grid;grid-template-columns:repeat(2,1fr);gap:9px;margin:18px 18px 0}
  .stat{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:13px 14px}
  .stat .v{font-family:'Bebas Neue','JetBrains Mono',sans-serif;font-size:27px;line-height:1;color:var(--up2);letter-spacing:.5px;font-weight:800}
  .stat .l{font-size:11.5px;color:var(--dim);margin-top:6px;line-height:1.4}
  .body{padding:8px 18px 0}
  .body p{font-size:15.5px;line-height:1.9;color:var(--text);margin:13px 0}
  .body strong{color:var(--white)}
  .body em{color:var(--gold);font-style:normal;font-weight:700}
  h2{font-size:20px;font-weight:900;color:var(--white);margin:34px 0 8px;letter-spacing:-.01em;padding-top:18px;border-top:1px solid var(--border)}
  table.flow{width:100%;border-collapse:collapse;margin:12px 0;font-size:14.5px}
  table.flow td{padding:11px 12px;border-bottom:1px solid var(--border);vertical-align:top}
  table.flow tr:last-child td{border-bottom:none}
  table.flow .k{color:var(--dim);width:34%}
  table.flow .v{font-family:'JetBrains Mono',monospace;font-weight:700;color:var(--up2);width:24%}
  table.flow .n{color:#b6c3d4;font-size:13px}
  table.flow tr.hl td{background:rgba(34,197,94,.06)}
  table.flow tr.hl .v{color:#86efac}
  .bb{display:grid;grid-template-columns:1fr 1fr;gap:11px;margin:14px 0}
  .bb .col{border-radius:13px;padding:14px 15px;border:1px solid var(--border)}
  .bb .bull{background:linear-gradient(180deg,rgba(34,197,94,.09),rgba(34,197,94,.02));border-color:rgba(34,197,94,.35)}
  .bb .bear{background:linear-gradient(180deg,rgba(239,68,68,.08),rgba(239,68,68,.02));border-color:rgba(239,68,68,.35)}
  .bb h3{font-size:14px;font-weight:800;margin-bottom:8px}
  .bb .bull h3{color:var(--up2)}.bb .bear h3{color:#fca5a5}
  .bb ul{margin:0;padding-left:16px}
  .bb li{font-size:13px;line-height:1.65;color:#c3cfdf;margin:7px 0}
  .bb li strong{color:#fff}
  .series{margin:18px 18px 0;padding:11px 14px;border:1px dashed var(--border);border-radius:10px;font-size:13px}
  .series a{color:var(--up2);text-decoration:none;font-weight:700}
  .foot{margin:30px 18px 18px;padding:14px 16px;background:var(--surface);border:1px solid var(--border);border-radius:12px;font-size:11.5px;line-height:1.75;color:var(--dim)}
  .foot strong{color:var(--gold)}
  .src{margin-top:8px;display:flex;flex-wrap:wrap;gap:6px}
  .src a{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--up2);text-decoration:none;border:1px solid var(--border);padding:3px 8px;border-radius:6px}
  @media(min-width:768px){.stats{grid-template-columns:repeat(4,1fr)}h1{font-size:35px}}
  @media(max-width:600px){.bb{grid-template-columns:1fr}}
"""

BUILD_CHECK = (
    '<!--lp-build-check:start-->\n'
    f'<meta name="lp-build" content="{STAMP}">\n'
    '<script>(function(){try{if(!/KAKAOTALK/i.test(navigator.userAgent||""))return;var K="lp_kko_out";try{if(sessionStorage.getItem(K))return;sessionStorage.setItem(K,"1");}catch(e){}location.href="kakaotalk://web/openExternal?url="+encodeURIComponent(location.href);}catch(e){}})();</script>\n'
    f'<script>(function(){{var B="{STAMP}";try{{fetch("/build.json?_="+Date.now(),{{cache:"no-store"}}).then(function(r){{return r.ok?r.json():null}}).then(function(d){{if(!d||!d.v||d.v===B)return;var k="lp_build_"+B;try{{if(sessionStorage.getItem(k))return;sessionStorage.setItem(k,"1");}}catch(e){{}}var u=new URL(location.href);u.searchParams.set("_b",d.v);location.replace(u.toString());}}).catch(function(){{}});}}catch(e){{}}}})();</script>\n'
    '<!--lp-build-check:end-->'
)

ALT_HL = [("ko", "ko"), ("en", "en"), ("ja", "ja"), ("zh", "zh")]


def build(lang):
    c = L[lang]
    alt_links = "\n".join(
        f'<link rel="alternate" hreflang="{hl}" href="https://luckyplz.com/blog/{L[k]["slug"]}/">'
        for hl, k in ALT_HL)

    li = {"ko": 1, "en": 2, "ja": 3, "zh": 4}[lang]
    stats = "\n".join(
        f'<div class="stat"><div class="v">{s[0]}</div><div class="l">{s[li]}</div></div>'
        for s in STATS)

    secs = []
    for title, kind, payload in c["secs"]:
        if kind == "table":
            rows = "\n".join(
                f'<tr class="{"hl" if i==len(payload)-1 else ""}"><td class="k">{k}</td>'
                f'<td class="v">{v}</td><td class="n">{n}</td></tr>'
                for i, (k, v, n) in enumerate(payload))
            secs.append(f'<h2>{title}</h2>\n<table class="flow">{rows}</table>')
        elif kind == "bullbear":
            cols = []
            for head, items in payload:
                lis = "\n".join(f"<li>{it}</li>" for it in items)
                cls = "bull" if head in ("강세", "Bull", "強気", "看多") else "bear"
                cols.append(f'<div class="col {cls}"><h3>{head}</h3><ul>{lis}</ul></div>')
            secs.append(f'<h2>{title}</h2>\n<div class="bb">{"".join(cols)}</div>')
        else:
            body = "\n".join(f"<p>{p}</p>" for p in payload)
            secs.append(f"<h2>{title}</h2>\n{body}")
    secs_html = "\n".join(secs)

    src_links = "\n    ".join(
        f'<a href="{url}" target="_blank" rel="noopener">{name}</a>' for name, url in SRC)

    import re as _re
    _m = _re.search(r'(/blog/[^\s]+)', c["series_link"])
    series_url = _m.group(1) if _m else "/blog/"
    series_label = _re.sub(r'\s*[—→].*$', '', c["series_link"]).strip()
    series_html = f'<div class="series">📚 <a href="{series_url}">{series_label} →</a></div>'

    ld_post = json.dumps({
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": c["title"], "description": c["desc"],
        "datePublished": "2026-06-13", "dateModified": "2026-06-13",
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
    meta_date = {"ko": "2026. 6. 13.", "en": "Jun 13, 2026", "ja": "2026.6.13", "zh": "2026.6.13"}[lang]

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
<meta property="article:published_time" content="2026-06-13T09:00:00+09:00">
<meta property="article:section" content="Business">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{c['og_title']}">
<meta name="twitter:description" content="{c['og_desc']}">
<meta name="twitter:image" content="{og_img}">
<script type="application/ld+json">{ld_post}</script>
<script type="application/ld+json">{ld_bc}</script>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0a0e17">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=JetBrains+Mono:wght@400;700&family=Bebas+Neue&display=swap" rel="stylesheet">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5370817769801923" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NZDPE3H3DQ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-NZDPE3H3DQ');</script>
<style>{CSS}</style>
</head>
<body>
<div class="container">

<nav class="site-nav">
  <a href="/blog/?cat=stocks">{c['nav_cat']}</a>
  <a href="/">{c['home']}</a>
</nav>

<header class="hero">
  <span class="kicker">{c['kicker']}</span>
  <h1>{c['h1']}</h1>
  <p class="dek">{c['dek']}</p>
  <div class="meta"><span>{meta_date}</span><span><b>{c['read']}</b></span><span>{c['asof_badge']}</span></div>
</header>

<div class="stats">
{stats}
</div>

{series_html}

<div class="body">

{secs_html}

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
