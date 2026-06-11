#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the 4-language "2026 World Cup anti-time-wasting rules" post.

Fun tone, factually grounded on the real rule changes (8-second goalkeeper
rule -> corner kick, 10-second substitution rule, on-pitch-treatment 1-minute
rule, goal-kick/throw-in countdowns, red cards for leaving the field to
protest / mouth-covering, hydration breaks, expanded VAR). Embeds three
original cartoon GIFs (scripts/gen-worldcup-antiwaste-gifs.py) — no
copyrighted footage.

Indexed (manual content, NOT a daily auto-post): no noindex meta, registered
in sitemap. Sources: Al Jazeera, Yahoo Sports (June 2026).

Output: public/blog/worldcup-2026-anti-time-wasting[/-en/-ja/-zh]/index.html
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "public" / "blog"
SLUG = "worldcup-2026-anti-time-wasting"
STAMP = json.loads((ROOT / "public" / "build.json").read_text())["v"]
GIF = "/assets/blog/worldcup-antiwaste"

L = {
    "ko": {
        "slug": SLUG, "lang": "ko", "og_locale": "ko_KR",
        "title": "침대축구 끝장내기 — 2026 월드컵 시간끌기 근절 새 규칙 총정리",
        "desc": "8초 골키퍼 룰, 교체 10초 룰, 부상 1분 격리까지. 2026 북중미 월드컵이 침대축구·시간끌기를 박멸하려 들고나온 새 규칙들을, 그 유명한 장면들과 함께 유쾌하게 정리했다.",
        "kicker": "🛌 2026 월드컵 · 침대축구 근절 특집",
        "h1": '침대축구, 이제 <span class="hl">8초 안에</span> 일어나세요',
        "dek": "공만 잡으면 눕고, 이기고 있으면 신발끈을 세 번 묶고, 교체될 땐 운동장을 한 바퀴 산책하던 그 시절. 2026 월드컵은 작정하고 칼을 빼들었다. 시간끌기 종합세트를 정조준한 새 규칙들을, 우리가 다 아는 그 장면들과 함께 풀어본다.",
        "read": "6분",
        "intro": [
            "축구를 사랑하지만 누구나 한 번쯤은 리모컨을 던지고 싶었던 순간이 있다. 1대 0, 후반 추가시간. 골키퍼가 공을 품에 안고 하늘을 본다. 하나, 둘, 셋... 코너 깃발 쪽에선 교체 선수가 우주의 기운을 받으며 천천히, 아주 천천히 걸어 나간다. 그리고 어디선가 한 선수가 살짝 스친 발에 다섯 바퀴를 구른다. 이것이 바로 <strong>침대축구</strong>, 영어로는 점잖게 <em>time-wasting</em>이라 부르는 그 예술이다.",
            "FIFA와 국제축구평의회(IFAB)가 드디어 이 '예술'에 제동을 걸었다. 2026 북중미 월드컵에는 시간끌기를 정조준한 규칙들이 줄줄이 도입된다. 핵심은 단순하다. <strong>꾸물거리면 손해를 본다.</strong> 이제 그 장면들이 어떻게 바뀌는지, 하나씩 보자.",
        ],
        "rules": [
            {
                "h": "① 8초 골키퍼 룰 — 공 끌어안기, 이제 코너킥행",
                "gif": "keeper8.gif",
                "cap": "골키퍼가 공을 8초 넘게 들고 있으면 → 상대 코너킥. 심판이 손가락으로 카운트다운한다.",
                "body": [
                    "골키퍼가 공을 잡고 버틸 수 있는 시간이 <strong>8초</strong>로 못 박혔다. 심판은 손을 들어 5초 카운트다운을 시각적으로 보여주고, 그 안에 공을 내보내지 않으면 <strong>상대 팀 코너킥</strong>이다.",
                    "예전에도 '6초 룰'은 있었다. 문제는 위반해도 간접 프리킥이라, 페널티 박스 안에서 주는 거라 위험 부담 때문에 <em>심판이 사실상 한 번도 안 불었다</em>. 규칙은 있는데 유령이었던 셈. 이번엔 벌칙을 코너킥으로 바꿔 실효성을 확 끌어올렸다. 코너킥은 진짜 무서우니까.",
                ],
            },
            {
                "h": "② 교체 10초 룰 — 운동장 산책은 이제 그만",
                "gif": "slowsub.gif",
                "cap": "교체판이 뜨면 10초 안에, 가장 가까운 라인으로 나가야 한다. 반대편 구석 산책은 끝.",
                "body": [
                    "교체되는 선수가 그라운드를 가로질러 가장 먼 사이드라인까지 느긋하게 걸어 나가던 '작별 산책'은 이제 역사 속으로. 교체판이 올라오면 선수는 <strong>10초 안에</strong>, 그것도 <strong>가장 가까운 경계선 지점</strong>으로 나가야 한다.",
                    "꾸물거리면? 교체 선수는 곧바로 못 들어온다. 경기가 재개되고 <strong>1분이 지난 뒤 첫 데드볼</strong> 상황에서야 심판 신호를 받고 들어올 수 있다. 즉, 시간을 끌면 내 팀이 그동안 한 명 적게 뛴다. 자업자득 설계다.",
                ],
            },
            {
                "h": "③ 부상 1분 격리 룰 — 다섯 바퀴 구르면 손해",
                "gif": "roll.gif",
                "cap": "그라운드에서 의료진 치료를 받으면, 재개 후 1분간 들어올 수 없다. 구를수록 손해.",
                "body": [
                    "그 유명한 '데구르르' 장면. 살짝 스쳤을 뿐인데 잔디 위에서 옆으로 굴러가며 온 세상의 고통을 표현하던 그 연기 말이다. 이제는 비용이 따른다.",
                    "필드 플레이어가 <strong>그라운드 안에서 의료진의 치료</strong>를 받으면, 경기 재개 후 <strong>1분간 그라운드에 들어올 수 없다</strong>(몇 가지 예외 제외). 진짜 아프면 당연히 치료받아야 한다. 하지만 '전술적 부상'으로 시간을 벌려던 선수는 이제 1분 동안 팀을 수적 열세로 만든다. 굴러서 번 시간보다 잃는 게 크다.",
                ],
            },
        ],
        "bonus_h": "🎁 보너스 — 같이 들어온 규칙들",
        "bonus": [
            "<strong>골킥·스로인 카운트다운</strong>: 심판이 손을 들어 5초를 센다. 시간 안에 안 하면 상대에게 공을 넘긴다(골킥은 코너킥, 스로인은 상대 스로인).",
            "<strong>입 가리기 = 레드카드</strong>: 충돌 상황에서 입을 가리고 말하면 퇴장. 차별성 발언 방지 차원. 친구끼리 잡담은 예외.",
            "<strong>경기장 이탈 항의 = 레드카드</strong>: 판정에 항의하며 그라운드를 벗어나면 퇴장. 경기를 중단시킨 팀은 몰수패까지.",
            "<strong>VAR 확대</strong>: 명백히 잘못된 두 번째 옐로카드, 선수 오인, 세트피스 직전 반칙까지 검토 대상.",
            "<strong>수분 보충 브레이크</strong>: 전·후반 22분경 3분간 공식 급수 시간. 폭염 대회 대비책이자, 무질서한 시간끌기를 구조화한 장치.",
        ],
        "outro": [
            "정리하면, 이번 월드컵의 메시지는 한 줄이다. <strong>축구는 90분 내내 흘러야 한다.</strong> 골키퍼는 8초 안에, 교체 선수는 10초 안에, 부상 연기는 1분의 대가를 치른다. 규칙이 잘 굴러간다면, 우리가 추가시간에 리모컨을 던지는 일도 조금은 줄어들 것이다.",
            "물론, 선수들은 늘 새로운 빈틈을 찾는 데 천재적이다. 8초를 7초 9에 맞춰 쓰는 신공이 곧 등장하겠지. 그래도 방향은 분명하다. 침대는 집에서, 그라운드에서는 공을 굴리자.",
        ],
        "foot": "규칙 내용은 FIFA·IFAB 발표와 언론 보도(2026년 6월)를 토대로 정리했습니다. 적용 세부는 대회 운영·심판 재량에 따라 달라질 수 있습니다. 본문 일러스트(GIF)는 저작권 안전을 위해 직접 제작한 오리지널 애니메이션이며 특정 선수·실제 경기 장면이 아닙니다.",
        "nav_cat": "← 월드컵", "home": "🎮 GAMES",
        "bc": ["홈", "블로그", "침대축구 근절 규칙"],
        "og_title": "침대축구 끝장내기 — 2026 월드컵 시간끌기 근절 규칙",
        "og_desc": "8초 골키퍼 룰·교체 10초·부상 1분 격리. 그 유명한 장면들과 함께 유쾌하게.",
    },
    "en": {
        "slug": f"{SLUG}-en", "lang": "en", "og_locale": "en_US",
        "title": "The War on Time-Wasting — Every New 2026 World Cup Rule, Explained (and Mocked)",
        "desc": "The 8-second goalkeeper rule, the 10-second substitution rule, the 1-minute injury sit-out and more. A fun, accurate rundown of how the 2026 World Cup is hunting down time-wasting — illustrated with the scenes you already picture.",
        "kicker": "🛌 WORLD CUP 2026 · THE WAR ON TIME-WASTING",
        "h1": 'Time-wasting? You have <span class="hl">8 seconds</span>',
        "dek": "Hug the ball and lie down. Tie your boots three times while winning. Take a scenic stroll across the whole pitch when subbed off. Those days are numbered. The 2026 World Cup brought a stack of rules aimed straight at the stalling — let's walk through them with the scenes we all know.",
        "read": "6 min",
        "intro": [
            "We love football, but everyone has wanted to throw the remote at least once. One-nil, deep into stoppage time. The keeper cradles the ball and gazes at the sky. One... two... three. Over by the corner flag, a substitute drifts off the pitch slowly, channelling the energy of the universe. And somewhere, a player who got grazed on the shin rolls over five times. This is the dark art the polite world calls <em>time-wasting</em>.",
            "FIFA and the IFAB have finally taken a blade to the art form. The 2026 North American World Cup rolls out a run of rules aimed squarely at stalling. The logic is simple: <strong>dawdle, and it costs you.</strong> Here's how those familiar scenes change.",
        ],
        "rules": [
            {
                "h": "① The 8-second goalkeeper rule — hug the ball, concede a corner",
                "gif": "keeper8.gif",
                "cap": "Hold the ball more than 8 seconds and the other team gets a corner. The referee counts you down on their fingers.",
                "body": [
                    "A keeper can now hold the ball for <strong>8 seconds</strong>, full stop. The referee raises a hand for a visual five-second countdown, and if the ball isn't released in time, the opponents get a <strong>corner kick</strong>.",
                    "There was already a 'six-second rule.' The catch: the punishment was an indirect free kick inside the box, so dangerous to award that <em>referees essentially never called it</em>. A ghost rule. Swapping the penalty to a corner gives it real teeth, because a corner is genuinely scary.",
                ],
            },
            {
                "h": "② The 10-second substitution rule — no more farewell tour",
                "gif": "slowsub.gif",
                "cap": "Once the board goes up, leave within 10 seconds at the nearest point on the line. The cross-pitch stroll is dead.",
                "body": [
                    "The 'goodbye walk' across the entire field to the farthest touchline is history. When the substitution board goes up, the player must leave within <strong>10 seconds</strong>, and at the <strong>nearest point on the boundary line</strong>.",
                    "Dawdle and the substitute can't come straight on. They wait until the <strong>first stoppage one minute after play restarts</strong>, then enter on the referee's signal. Stall, and your own team plays a man short in the meantime. Beautifully self-defeating.",
                ],
            },
            {
                "h": "③ The 1-minute injury sit-out — rolling now has a price",
                "gif": "roll.gif",
                "cap": "Get treated on the pitch and you can't return for one minute after the restart. The more you roll, the more you lose.",
                "body": [
                    "The legendary 'roll.' Barely touched, yet tumbling across the grass expressing the suffering of all humankind. It now comes with a bill.",
                    "If an outfield player is <strong>treated by medical staff on the pitch</strong>, they cannot return for <strong>one minute after the restart</strong> (a few exceptions aside). If you're truly hurt, of course you get treated. But a 'tactical injury' to burn clock now leaves your team a player down for a minute. You lose more time than you stole.",
                ],
            },
        ],
        "bonus_h": "🎁 Bonus — the rules that came along",
        "bonus": [
            "<strong>Goal-kick & throw-in countdowns</strong>: the referee raises a hand and counts five. Run out of time and the ball goes to the opponents (a corner for a goal kick, a throw-in the other way).",
            "<strong>Covering the mouth = red card</strong>: speaking with a hand over your mouth in a confrontation is a sending-off, aimed at curbing abuse. Friendly chat is fine.",
            "<strong>Leaving the field to protest = red card</strong>: storming off the pitch to argue a decision is a red; a team that causes a match to be abandoned now forfeits.",
            "<strong>Expanded VAR</strong>: clearly wrong second yellows, mistaken identity, and fouls just before a set-piece restart are all reviewable.",
            "<strong>Hydration breaks</strong>: a three-minute official drinks break around the 22nd minute of each half — a heat measure, and a way to structure stoppages instead of leaving them to chance.",
        ],
        "outro": [
            "The message of this World Cup fits on one line: <strong>the ball should keep moving for 90 minutes.</strong> Keepers get 8 seconds, subs get 10, and faked injuries cost a minute. If it all works, we might throw the remote a little less often in stoppage time.",
            "Of course, players are geniuses at finding the next loophole — expect the art of using exactly 7.9 seconds to arrive soon. But the direction is clear: keep the bed at home, and keep the ball rolling on the pitch.",
        ],
        "foot": "Rules summarized from FIFA/IFAB announcements and news reporting (June 2026). Application details may vary with tournament operations and referee discretion. The in-article GIFs are original animations made in-house for copyright safety and do not depict any specific player or real match footage.",
        "nav_cat": "← WORLD CUP", "home": "🎮 GAMES",
        "bc": ["Home", "Blog", "Anti-Time-Wasting Rules"],
        "og_title": "The War on Time-Wasting — 2026 World Cup's New Rules",
        "og_desc": "8-second keepers, 10-second subs, 1-minute injury sit-outs — explained and mocked.",
    },
    "ja": {
        "slug": f"{SLUG}-ja", "lang": "ja", "og_locale": "ja_JP",
        "title": "遅延行為よ、さようなら — 2026年W杯の時間稼ぎ撲滅ルール総まとめ",
        "desc": "8秒キーパールール、交代10秒ルール、負傷1分の隔離まで。2026年北中米W杯が時間稼ぎを狩りにきた新ルールを、あの名場面とともに愉快に整理。",
        "kicker": "🛌 2026年W杯 · 時間稼ぎ撲滅特集",
        "h1": '時間稼ぎ？　あと<span class="hl">8秒</span>です',
        "dek": "ボールを抱えて寝転がり、勝っていれば靴ひもを三度結び、交代のときはピッチを一周お散歩。そんな時代に終止符。2026年W杯は時間稼ぎの総合セットに狙いを定めた新ルールを並べてきた。誰もが知るあの場面とともに見ていこう。",
        "read": "6分",
        "intro": [
            "サッカーは大好きだが、誰しも一度はリモコンを投げたくなる。1対0、後半アディショナルタイム。キーパーがボールを抱えて空を見上げる。1、2、3……。コーナーフラッグの方では交代選手が宇宙の気を受けながら、ゆっくり、とてもゆっくり歩いて出ていく。そしてどこかで、かすっただけの選手が五回転がる。これが上品に<em>time-wasting</em>と呼ばれる芸術だ。",
            "FIFAとIFABがついにこの芸術にメスを入れた。2026年北中米W杯では時間稼ぎを狙い撃ちするルールが続々導入される。理屈は単純。<strong>もたつけば損をする。</strong>あの場面がどう変わるのか、一つずつ見ていこう。",
        ],
        "rules": [
            {
                "h": "① 8秒キーパールール — ボール抱え込みはコーナーキック行き",
                "gif": "keeper8.gif",
                "cap": "キーパーがボールを8秒以上持つと相手コーナーキック。主審が指でカウントダウンする。",
                "body": [
                    "キーパーがボールを保持できる時間が<strong>8秒</strong>と明文化された。主審は手を挙げて5秒のカウントダウンを見せ、その間にボールを離さなければ<strong>相手のコーナーキック</strong>だ。",
                    "以前から「6秒ルール」はあった。ただ違反しても罰則はペナルティエリア内の間接FK。危険すぎて<em>主審が事実上一度も取らなかった</em>。あるのに幽霊のようなルールだったわけだ。今回は罰則をコーナーキックに変え、実効性を一気に高めた。コーナーは本当に怖いのだ。",
                ],
            },
            {
                "h": "② 交代10秒ルール — ピッチのお散歩はもう終わり",
                "gif": "slowsub.gif",
                "cap": "交代ボードが出たら10秒以内に、最も近いライン地点から外へ。逆サイドへの散歩は終了。",
                "body": [
                    "交代選手がピッチを横断して最も遠いタッチラインまでのんびり歩く「お別れ散歩」は過去のものに。ボードが上がったら選手は<strong>10秒以内</strong>に、しかも<strong>最も近い境界線の地点</strong>から出なければならない。",
                    "もたつけば？　交代選手はすぐには入れない。プレー再開後<strong>1分が経過した最初のデッドボール</strong>で、ようやく主審の合図を受けて入れる。つまり時間を稼げば、その間チームが一人少なく戦う。見事な自業自得設計だ。",
                ],
            },
            {
                "h": "③ 負傷1分の隔離 — 五回転がると損をする",
                "gif": "roll.gif",
                "cap": "ピッチ上で治療を受けると、再開後1分間は入れない。転がるほど損。",
                "body": [
                    "あの名物「ゴロゴロ」。かすっただけなのに芝の上を横に転がり、人類すべての痛みを表現するあの演技だ。これにコストがつく。",
                    "フィールドプレーヤーが<strong>ピッチ上で医療スタッフの治療</strong>を受けると、再開後<strong>1分間ピッチに入れない</strong>(いくつかの例外を除く)。本当に痛いなら当然治療を受けるべきだ。だが「戦術的負傷」で時間を稼ごうとした選手は、1分間チームを数的不利にする。転がって稼いだ時間より失うものが大きい。",
                ],
            },
        ],
        "bonus_h": "🎁 おまけ — 一緒に入ったルール",
        "bonus": [
            "<strong>ゴールキック・スローインのカウントダウン</strong>：主審が手を挙げて5秒を数える。間に合わなければ相手にボールが渡る(ゴールキックはコーナー、スローインは相手スローイン)。",
            "<strong>口を覆う＝レッドカード</strong>：衝突の場面で口を覆って話すと退場。差別的発言の防止が狙い。仲間内の雑談は例外。",
            "<strong>ピッチ外への抗議＝レッドカード</strong>：判定に抗議してピッチを離れると退場。試合を中断させたチームは没収負けも。",
            "<strong>VAR拡大</strong>：明らかに誤った2枚目の警告、人違い、セットプレー直前の反則まで検討対象に。",
            "<strong>給水ブレイク</strong>：前後半22分頃に3分間の公式給水。猛暑対策であり、無秩序な時間稼ぎを構造化する仕掛けでもある。",
        ],
        "outro": [
            "まとめると、今大会のメッセージは一行だ。<strong>サッカーは90分間流れ続けるべき。</strong>キーパーは8秒、交代は10秒、負傷の演技は1分の代償を払う。うまく回れば、アディショナルタイムにリモコンを投げる回数も少し減るだろう。",
            "もちろん選手は新しい抜け道を見つける天才だ。8秒を7秒9で使い切る神業がそのうち登場するはず。それでも方向は明確。ベッドは家で、ピッチではボールを転がそう。",
        ],
        "foot": "ルール内容はFIFA・IFABの発表と報道(2026年6月)を基に整理しました。適用の細部は大会運営・主審の裁量により異なる場合があります。本文のイラスト(GIF)は著作権安全のため自作したオリジナルアニメーションで、特定の選手・実際の試合映像ではありません。",
        "nav_cat": "← ワールドカップ", "home": "🎮 GAMES",
        "bc": ["ホーム", "ブログ", "時間稼ぎ撲滅ルール"],
        "og_title": "遅延行為よさようなら — 2026年W杯の新ルール",
        "og_desc": "8秒キーパー・交代10秒・負傷1分隔離。名場面とともに愉快に。",
    },
    "zh": {
        "slug": f"{SLUG}-zh", "lang": "zh-CN", "og_locale": "zh_CN",
        "title": "拖延战术再见 — 2026世界杯反拖延时间新规则全梳理",
        "desc": "8秒门将规则、换人10秒规则、受伤1分钟隔离……2026美加墨世界杯向拖延时间下手的新规则，配上你脑海里那些名场面，轻松讲清楚。",
        "kicker": "🛌 2026世界杯 · 反拖延时间专题",
        "h1": '拖延时间？你还有<span class="hl">8秒</span>',
        "dek": "抱着球躺下，领先时把鞋带系三遍，被换下时绕全场散个步。这些日子要到头了。2026世界杯端出一摞专治拖延的新规则——我们配着那些人人都懂的画面一条条看。",
        "read": "6分钟",
        "intro": [
            "我们爱足球，但谁都有想摔遥控器的时刻。1比0，补时阶段。门将抱着球仰望天空。一、二、三……角旗那边，替补球员吸收着宇宙的能量，慢慢地、非常慢地走出场。而某处，一名只是被蹭了一下的球员翻滚了五圈。这就是被文雅地称作<em>time-wasting</em>(拖延时间)的艺术。",
            "FIFA和国际足球理事会(IFAB)终于对这门艺术动刀了。2026美加墨世界杯接连推出专门针对拖延的规则。逻辑很简单：<strong>磨蹭就吃亏。</strong>来看那些熟悉的画面如何改变。",
        ],
        "rules": [
            {
                "h": "① 8秒门将规则 — 抱球不放，直接送角球",
                "gif": "keeper8.gif",
                "cap": "门将持球超过8秒 → 对方角球。裁判会用手指为你倒数。",
                "body": [
                    "门将持球时间被明确限定为<strong>8秒</strong>。裁判举手做出5秒的可视倒数，若不在时间内把球交出，对方获得<strong>角球</strong>。",
                    "其实早有“6秒规则”。问题是违例的处罚是禁区内的间接任意球，太危险，<em>裁判几乎从不吹罚</em>，等于一条幽灵规则。这次把处罚改成角球，威慑力立刻拉满——因为角球是真的可怕。",
                ],
            },
            {
                "h": "② 换人10秒规则 — 全场散步到此为止",
                "gif": "slowsub.gif",
                "cap": "换人牌一举，就要在10秒内从最近的边线点离场。绕去对侧散步的时代结束了。",
                "body": [
                    "被换下的球员横穿全场、慢悠悠走向最远边线的“告别散步”成为历史。换人牌举起后，球员必须在<strong>10秒内</strong>，并且从<strong>最近的边线点</strong>离场。",
                    "磨蹭怎么办？替补不能马上上。要等到比赛重新开始<strong>1分钟后的第一次死球</strong>，经裁判示意才能进场。也就是说，你拖时间，自己的球队这段时间就少打一人。堪称完美的自食其果设计。",
                ],
            },
            {
                "h": "③ 受伤1分钟隔离 — 翻滚五圈反而吃亏",
                "gif": "roll.gif",
                "cap": "在场内接受治疗，重新开始后1分钟内不能回场。越翻滚越吃亏。",
                "body": [
                    "那个著名的“满地打滚”。只是被蹭了一下，却在草皮上侧翻，演绎全人类的痛苦。如今它要付费了。",
                    "若场上球员<strong>在场内接受医疗组治疗</strong>，重新开始后<strong>1分钟内不得回到场内</strong>(少数例外除外)。真受伤当然该治疗。但想用“战术性受伤”拖时间的球员，会让球队少打一人长达一分钟。打滚赚到的时间，远不及失去的多。",
                ],
            },
        ],
        "bonus_h": "🎁 附赠 — 一并登场的规则",
        "bonus": [
            "<strong>球门球·掷界外球倒数</strong>：裁判举手数5秒。超时就把球交给对方(球门球判角球，界外球判对方掷)。",
            "<strong>捂嘴＝红牌</strong>：在冲突场面捂着嘴说话会被罚下，意在遏制歧视性言论。朋友间闲聊不算。",
            "<strong>离场抗议＝红牌</strong>：为抗议判罚而离开球场会被罚下；导致比赛中断的球队将被判负。",
            "<strong>VAR扩大</strong>：明显错误的第二张黄牌、认错人、定位球重启前的犯规，均纳入回看范围。",
            "<strong>补水暂停</strong>：上下半场约第22分钟各有3分钟官方补水时间。既是高温对策，也把零散的拖延变成有序安排。",
        ],
        "outro": [
            "总结起来，本届世界杯的信息只有一句：<strong>足球应当流畅地踢满90分钟。</strong>门将8秒，换人10秒，假摔付出1分钟代价。如果一切顺利，我们在补时阶段摔遥控器的次数也许会少一点。",
            "当然，球员总是寻找新漏洞的天才——把8秒精确用到7秒9的神技很快就会出现。但方向很明确：床留在家里，球场上让球滚起来。",
        ],
        "foot": "规则内容依据FIFA·IFAB公告及媒体报道(2026年6月)整理。具体适用可能因赛事运营与裁判裁量而不同。文中插图(GIF)为版权安全起见自制的原创动画，并非特定球员或真实比赛画面。",
        "nav_cat": "← 世界杯", "home": "🎮 GAMES",
        "bc": ["首页", "博客", "反拖延时间规则"],
        "og_title": "拖延战术再见 — 2026世界杯新规则",
        "og_desc": "8秒门将·换人10秒·受伤1分钟隔离，配名场面轻松讲。",
    },
}

CSS = """
  :root{--bg:#05140e;--surface:#0b211a;--surface2:#102b21;--border:#1c3b30;--green:#2dd4bf;--green2:#34d399;--gold:#fbbf24;--text:#cfe6dd;--dim:#6f8a80;--hot:#ff7a59;--white:#fff}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'Noto Sans KR',sans-serif;line-height:1.8;-webkit-font-smoothing:antialiased}
  .container{max-width:760px;margin:0 auto;background:var(--bg);min-height:100vh}
  .site-nav{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--border);background:rgba(5,20,14,.85);backdrop-filter:blur(8px);position:sticky;top:0;z-index:50}
  .site-nav a{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);text-decoration:none;letter-spacing:1px;transition:color .2s}
  .site-nav a:hover{color:var(--green)}
  .hero{padding:30px 18px 22px;border-bottom:1px solid var(--border);background:radial-gradient(ellipse at 80% 0%,rgba(45,212,191,.10),transparent 60%),radial-gradient(ellipse at 0% 100%,rgba(251,191,36,.06),transparent 55%)}
  .kicker{display:inline-flex;align-items:center;gap:7px;font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#04231a;background:linear-gradient(90deg,var(--green),var(--green2));padding:5px 11px;border-radius:20px;margin-bottom:16px}
  h1{font-size:30px;font-weight:900;color:var(--white);line-height:1.28;letter-spacing:-.02em;margin-bottom:14px}
  h1 .hl{color:var(--gold)}
  .dek{font-size:15px;color:#a9c6bc;line-height:1.7;margin-bottom:18px}
  .meta{display:flex;gap:14px;flex-wrap:wrap;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);letter-spacing:.5px}
  .meta b{color:var(--gold)}
  .body{padding:8px 18px 0}
  .body p{font-size:15.5px;line-height:1.9;color:var(--text);margin:16px 0}
  .body strong{color:var(--white)}
  .body em{color:var(--green2);font-style:normal;font-weight:700}
  h2{font-size:20px;font-weight:900;color:var(--white);margin:36px 0 6px;letter-spacing:-.01em;padding-top:18px;border-top:1px solid var(--border)}
  .giffig{margin:16px 0 6px;border:1px solid var(--border);border-radius:14px;overflow:hidden;background:#06140d}
  .giffig img{display:block;width:100%;height:auto}
  .giffig figcaption{font-size:12.5px;color:var(--dim);padding:9px 13px;line-height:1.55;border-top:1px solid var(--border)}
  .bonus{margin:14px 0;border:1px solid rgba(251,191,36,.3);border-radius:14px;background:linear-gradient(135deg,rgba(251,191,36,.07),rgba(45,212,191,.03));padding:6px 16px 10px}
  .bonus li{font-size:14.5px;line-height:1.7;color:#cfe6dd;margin:10px 0;list-style:none;padding-left:20px;position:relative}
  .bonus li::before{content:"▸";position:absolute;left:0;color:var(--gold)}
  .bonus b{color:var(--white)}
  .foot{margin:28px 18px 18px;padding:14px 16px;background:var(--surface);border:1px solid var(--border);border-radius:12px;font-size:11.5px;line-height:1.7;color:var(--dim)}
  .foot strong{color:var(--gold)}
  .src{margin-top:8px;display:flex;flex-wrap:wrap;gap:6px}
  .src a{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--green);text-decoration:none;border:1px solid var(--border);padding:3px 8px;border-radius:6px}
  @media(min-width:768px){h1{font-size:36px}}
"""

BUILD_CHECK = (
    '<!--lp-build-check:start-->\n'
    f'<meta name="lp-build" content="{STAMP}">\n'
    f'<script>(function(){{var B="{STAMP}";try{{fetch("/build.json?_="+Date.now(),{{cache:"no-store"}}).then(function(r){{return r.ok?r.json():null}}).then(function(d){{if(!d||!d.v||d.v===B)return;var k="lp_build_"+B;try{{if(sessionStorage.getItem(k))return;sessionStorage.setItem(k,"1");}}catch(e){{}}var u=new URL(location.href);u.searchParams.set("_b",d.v);location.replace(u.toString());}}).catch(function(){{}});}}catch(e){{}}}})();</script>\n'
    '<!--lp-build-check:end-->'
)

ALT_HL = [("ko", "ko"), ("en", "en"), ("ja", "ja"), ("zh", "zh")]


def build(lang):
    c = L[lang]
    alt_links = "\n".join(
        f'<link rel="alternate" hreflang="{hl}" href="https://luckyplz.com/blog/{L[k]["slug"]}/">'
        for hl, k in ALT_HL)

    intro = "\n".join(f"<p>{p}</p>" for p in c["intro"])

    rules_html = []
    for r in c["rules"]:
        alt = r["cap"]
        body = "\n".join(f"<p>{p}</p>" for p in r["body"])
        rules_html.append(
            f'<h2>{r["h"]}</h2>\n'
            f'<figure class="giffig"><img src="{GIF}/{r["gif"]}?v={STAMP}" alt="{alt}" '
            f'loading="lazy" width="480" height="300"><figcaption>{r["cap"]}</figcaption></figure>\n'
            f'{body}')
    rules_html = "\n".join(rules_html)

    bonus = "\n".join(f"<li>{b}</li>" for b in c["bonus"])
    outro = "\n".join(f"<p>{p}</p>" for p in c["outro"])

    ld_post = json.dumps({
        "@context": "https://schema.org", "@type": "BlogPosting",
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
    meta_lang = {"ko": "2026. 6. 12.", "en": "Jun 12, 2026", "ja": "2026.6.12", "zh": "2026.6.12"}[lang]

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
<meta property="article:published_time" content="2026-06-12T19:00:00+09:00">
<meta property="article:section" content="Sports">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{c['og_title']}">
<meta name="twitter:description" content="{c['og_desc']}">
<meta name="twitter:image" content="{og_img}">
<script type="application/ld+json">{ld_post}</script>
<script type="application/ld+json">{ld_bc}</script>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#05140e">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5370817769801923" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NZDPE3H3DQ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-NZDPE3H3DQ');</script>
<style>{CSS}</style>
</head>
<body>
<div class="container">

<nav class="site-nav">
  <a href="/blog/?cat=worldcup">{c['nav_cat']}</a>
  <a href="/">{c['home']}</a>
</nav>

<header class="hero">
  <span class="kicker">{c['kicker']}</span>
  <h1>{c['h1']}</h1>
  <p class="dek">{c['dek']}</p>
  <div class="meta"><span>{meta_lang}</span><span><b>{c['read']}</b></span><span>WORLD CUP 2026</span></div>
</header>

<div class="body">

{intro}

{rules_html}

<h2>{c['bonus_h']}</h2>
<ul class="bonus">
{bonus}
</ul>

{outro}

<div data-lp-ad="blog" style="margin:24px 0;"></div>

</div>

<footer class="foot">
  <strong>📌 Source &amp; Note</strong><br>
  {c['foot']}
  <div class="src">
    <a href="https://www.aljazeera.com/sports/2026/6/1/which-football-rule-changes-will-be-implemented-during-the-world-cup" target="_blank" rel="noopener">Al Jazeera</a>
    <a href="https://sports.yahoo.com/articles/rules-2026-fifa-world-cup-110430972.html" target="_blank" rel="noopener">Yahoo Sports</a>
    <a href="https://www.theifab.com/" target="_blank" rel="noopener">IFAB</a>
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
