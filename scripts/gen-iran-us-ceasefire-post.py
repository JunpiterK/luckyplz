#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the 4-language Iran-US ceasefire issue post (category: issue).

Serious, attributed, news-analysis tone — NOT entertainment. Accurate framing:
this is a FRAGILE, CONTESTED ceasefire (April 7-8, 2026, mediated by Pakistan
+ Qatar), not a finalized peace deal. June 7-8 saw Iran missiles at Israel
after Israeli strikes on Beirut; June 10-11 saw US strikes on Iranian radar/
drone sites, Iranian responses, and mutual ceasefire-violation accusations.
Talks continue on Hormuz, the nuclear/ballistic program, sanctions, and
regional conflicts. Every claim is hedged + sourced; an explicit "as of"
timestamp and a ceasefire-vs-peace-deal caveat sit up top.

Sources (public reporting, June 2026): CNN live blogs, Al Jazeera, Wikipedia
(2026 Iran war ceasefire), Britannica, UK House of Commons Library.

Indexed (manual analysis). Output:
public/blog/iran-us-ceasefire-2026-06[/-en/-ja/-zh]/index.html
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "public" / "blog"
SLUG = "iran-us-ceasefire-2026-06"
STAMP = json.loads((ROOT / "public" / "build.json").read_text())["v"]

SRC = [
    ("CNN (Jun 7–8, 2026)", "https://www.cnn.com/2026/06/07/world/live-news/iran-war-trump-israel-lebanon"),
    ("CNN (Jun 1, 2026)", "https://www.cnn.com/2026/06/01/world/live-news/iran-trump-lebanon-war-news"),
    ("Al Jazeera", "https://www.aljazeera.com/news/2026/5/25/rubio-says-us-will-find-another-way-if-iran-talks-fail"),
    ("UK Commons Library", "https://commonslibrary.parliament.uk/research-briefings/cbp-10637/"),
    ("Wikipedia · 2026 Iran war ceasefire", "https://en.wikipedia.org/wiki/2026_Iran_war_ceasefire"),
]

L = {
    "ko": {
        "lang": "ko", "slug": SLUG, "og_locale": "ko_KR",
        "title": "이란-미국 휴전 어디까지 왔나 — 종전 협상의 현주소와 5가지 쟁점",
        "desc": "2026년 4월 휴전 이후 깨지기 쉬운 정전 상태가 이어지는 이란-미국. 6월 10~11일 상호 공격과 휴전 위반 공방, 파키스탄·카타르 중재 협상, 호르무즈·핵·제재 등 5가지 쟁점을 공신력 있는 보도를 토대로 정리했다. (6월 12일 기준)",
        "kicker": "📰 이슈 · 중동 정세 브리핑",
        "h1": '이란-미국 휴전, <span class="hl">종전</span>으로 가나',
        "dek": "결론부터: 지금은 ‘종전 합의 완료’가 아니라 <strong>4월 휴전이 위태롭게 유지되는 가운데 종전을 향한 협상이 진행 중</strong>인 단계다. 6월 10~11일에도 양측의 공격과 ‘휴전 위반’ 공방이 오갔다. 공신력 있는 보도를 토대로 현재 상황과 핵심 쟁점만 정리한다.",
        "asof": "이 글은 <strong>2026년 6월 12일(한국시간)</strong> 기준 공개 보도를 정리한 것입니다. 사안이 빠르게 바뀌므로, 관전 전 원문 보도를 다시 확인하세요.",
        "read": "7분",
        "secs": [
            ("지금 상황 — 한 문단 요약",
             ["<strong>휴전은 존재하지만 깨지기 쉽다.</strong> 2026년 4월 7~8일, 5주 넘는 교전 끝에 이란과 미국은 이스라엘을 포함한 휴전에 합의했고, 트럼프 대통령은 이를 사실상 무기한 연장했다고 밝혔다. 그러나 6월 7~8일 이스라엘의 베이루트 남부 공습 이후 이란이 이스라엘을 향해 탄도미사일을 발사하며 4월 휴전 이후 처음으로 직접 충돌이 재발했고, 6월 10일에는 미국이 이란의 레이더·드론 시설을 타격하자 이란이 걸프 해역에서 미사일로 응수했다. 이란 외무부는 미국이 휴전을 위반했다고 비난했다. <em>즉, ‘정전 합의’는 살아 있으나 ‘종전’과는 거리가 있다.</em>"]),
            ("어떻게 여기까지 왔나 — 짧은 타임라인",
             ["<strong>2~3월:</strong> 핵·미사일 프로그램과 역내 갈등을 둘러싼 긴장이 무력 충돌로 비화(‘2026 이란 전쟁’).",
              "<strong>4월 7~8일:</strong> 5주여 교전 끝에 <strong>이스라엘을 포함한 휴전</strong> 성립. 이후 트럼프 대통령은 휴전을 무기한 연장한다고 발표.",
              "<strong>5월:</strong> 양측이 광범위한 평화 협정에 근접했다는 보도. 트럼프는 양해각서(MOU) 마무리가 가깝고 호르무즈 해협이 곧 재개될 수 있다고 언급. 다만 이란은 ‘미국의 진정성이 확인돼야 한다’는 입장.",
              "<strong>6월 7~8일:</strong> 이스라엘의 베이루트 남부 공습 → 이란의 대이스라엘 탄도미사일 발사. 4월 이후 첫 직접 충돌.",
              "<strong>6월 10~11일:</strong> 미국의 이란 레이더·드론 시설 타격 → 이란의 걸프 해역 미사일 응수. 이란 외무부, 미국의 휴전 위반·모순된 메시지 비난. 협상은 계속되는 것으로 보도."]),
            ("누가 중재하나",
             ["보도에 따르면 <strong>파키스탄</strong>이 1차 중재자로, 이슬라마바드(세레나 호텔)에서 협상을 주선해 왔다. <strong>카타르</strong>는 5월 22일부터 보조 중재자로 합류했다. 의제는 호르무즈의 항행 자유, 이란의 핵·탄도미사일 프로그램, 제재·동결자산·전후 복구, 그리고 장기 평화 협정이다."]),
            ("핵심 쟁점 5가지",
             ["<strong>① 호르무즈 해협.</strong> 휴전 조건에는 해협 재개가 포함됐지만, 보도상 사실상 닫혀 있는 상태가 이어진다. 세계 원유의 길목이라 재개 여부가 에너지 가격과 직결된다.",
              "<strong>② 핵·탄도미사일.</strong> 미국은 이란 핵 능력에 대한 제약을, 이란은 그에 상응하는 제재 완화를 요구한다. 검증 방식이 핵심 난제다.",
              "<strong>③ 제재·자산·배상.</strong> 이란의 ‘10개 항’에는 제재 해제, 동결자산 반환, 전쟁 배상, 이라크·레바논·예멘 분쟁 종식 요구가 담긴 것으로 전해진다.",
              "<strong>④ 역내 전선.</strong> 이스라엘-레바논(베이루트) 충돌이 휴전을 흔드는 최대 변수다. 레바논을 합의에 포함할지가 쟁점으로 남아 있다.",
              "<strong>⑤ 신뢰·검증.</strong> 양측이 서로 ‘휴전 위반’을 주장하는 상황에서 합의 이행을 누가 어떻게 보증하느냐가 종전의 관건이다. 트럼프는 평화 협정을 아브라함 협정 확대와 연계하려는 것으로 알려졌다."]),
            ("왜 중요한가",
             ["가장 직접적인 파급은 <strong>에너지와 시장</strong>이다. 호르무즈가 막히면 원유·LNG 운송이 흔들리고, 유가 변동성은 인플레이션과 증시로 번진다. 둘째는 <strong>역내 안정</strong>이다. 이스라엘-레바논 전선이 다시 불붙으면 휴전 전체가 위태로워진다. 셋째는 <strong>외교의 신뢰</strong>다. 위반 공방이 반복될수록 ‘종전’이라는 단어는 멀어진다."]),
            ("앞으로 — 불확실성",
             ["현재 양측은 휴전 연장을 위한 초안을 주고받는 것으로 보도된다. 협상이 ‘종전 평화 협정’으로 굳어질지, 아니면 위반과 재협상이 반복되는 불안정한 정전이 길어질지는 아직 단정하기 어렵다. 분명한 건 하나다 — <strong>지금은 끝이 아니라 과정이며, 시간 단위로 상황이 바뀐다.</strong>"]),
        ],
        "foot": "본 글은 2026년 6월 12일(한국시간) 기준 <strong>공개 보도·기관 자료를 종합·정리</strong>한 것으로, 특정 입장을 옹호하지 않습니다. 전황과 협상은 빠르게 변하며, 일부 세부는 보도 간 차이가 있을 수 있습니다(특히 중재국·휴전 연장 기간). 군사·외교 사안의 성격상 추정·재구성이 포함될 수 있으니, 원문 보도와 공식 발표로 교차 확인하시기 바랍니다.",
        "nav_cat": "← 이슈", "home": "🎮 GAMES",
        "bc": ["홈", "블로그", "이란-미국 휴전 현황"],
        "og_title": "이란-미국 휴전, 종전으로 가나 — 5가지 쟁점 (6/12 기준)",
        "og_desc": "확정 종전 아님 — 깨지기 쉬운 4월 휴전 + 진행 중 협상. 호르무즈·핵·제재 등 쟁점 정리.",
        "label": "이슈", "asof_badge": "2026.6.12 기준 · 빠르게 변하는 사안",
    },
    "en": {
        "lang": "en", "slug": f"{SLUG}-en", "og_locale": "en_US",
        "title": "Iran–US Ceasefire: How Close Is a Real Peace Deal? — 5 Sticking Points",
        "desc": "Since the April 2026 truce, Iran and the US remain in a fragile, contested ceasefire. June 10–11 brought fresh strikes and mutual violation claims. A sourced rundown of the Pakistan/Qatar-mediated talks and the five sticking points — Hormuz, nuclear, sanctions and more. (As of June 12.)",
        "kicker": "📰 ISSUE · MIDDLE EAST BRIEF",
        "h1": 'Iran–US Ceasefire: How Close Is <span class="hl">Peace</span>?',
        "dek": "Bottom line first: this is <strong>not a finished peace deal</strong>. It's a shaky April ceasefire holding while talks toward an actual settlement continue. As recently as June 10–11, both sides traded strikes and accusations of violating the truce. Here is the state of play and the key sticking points, from credible reporting.",
        "asof": "This summarizes public reporting <strong>as of June 12, 2026 (KST)</strong>. The situation moves fast — re-check primary sources before relying on it.",
        "read": "7 min",
        "secs": [
            ("Where things stand — in one paragraph",
             ["<strong>The ceasefire exists, but it is fragile.</strong> On April 7–8, 2026, after more than five weeks of fighting, Iran and the US agreed to a ceasefire that included Israel, and President Trump said he had extended it indefinitely. But after Israeli strikes on southern Beirut on June 7–8, Iran fired ballistic missiles at Israel — the first direct clash since the April truce — and on June 10 the US struck Iranian radar and drone sites, prompting Iranian missile responses in the Gulf. Iran's foreign ministry accused Washington of violating the ceasefire. <em>In short: the truce is alive, but 'peace' it is not.</em>"]),
            ("How we got here — a short timeline",
             ["<strong>Feb–Mar:</strong> Tensions over the nuclear/missile program and regional conflicts escalate into open war (the '2026 Iran war').",
              "<strong>Apr 7–8:</strong> After ~5 weeks of fighting, a <strong>ceasefire including Israel</strong> takes hold. Trump later says he has extended it indefinitely.",
              "<strong>May:</strong> Reports say the sides are nearing a broader peace agreement; Trump says a memorandum of understanding is close and the Strait of Hormuz could reopen. Iran says it needs to be sure Washington is sincere.",
              "<strong>Jun 7–8:</strong> Israeli strikes on southern Beirut → Iranian ballistic missiles at Israel, the first direct confrontation since April.",
              "<strong>Jun 10–11:</strong> US strikes on Iranian radar/drone sites → Iranian missile responses in the Gulf. Iran's foreign ministry accuses the US of violating the truce and sending contradictory signals. Talks reportedly continue."]),
            ("Who is mediating",
             ["Per reporting, <strong>Pakistan</strong> has been the primary mediator, hosting talks in Islamabad. <strong>Qatar</strong> joined as a secondary mediator from May 22. The agenda spans freedom of navigation through Hormuz, Iran's nuclear and ballistic programs, sanctions, frozen assets and reconstruction, and a long-term peace agreement."]),
            ("The five sticking points",
             ["<strong>① The Strait of Hormuz.</strong> Reopening the strait is part of the ceasefire terms, yet reporting says it remains functionally closed. As a chokepoint for global oil, its status feeds straight into energy prices.",
              "<strong>② Nuclear & missiles.</strong> The US wants constraints on Iran's nuclear capability; Iran wants matching sanctions relief. Verification is the hard part.",
              "<strong>③ Sanctions, assets, reparations.</strong> Iran's reported 'ten points' include lifting sanctions, returning frozen assets, war reparations, and ending conflicts in Iraq, Lebanon and Yemen.",
              "<strong>④ The regional fronts.</strong> The Israel–Lebanon (Beirut) clashes are the biggest threat to the truce; whether Lebanon is folded into the deal remains disputed.",
              "<strong>⑤ Trust & verification.</strong> With each side accusing the other of breaches, who guarantees compliance — and how — is the crux of any real end to the war. Trump is reported to want a peace deal tied to expanding the Abraham Accords."]),
            ("Why it matters",
             ["The most direct impact is on <strong>energy and markets</strong>. A blocked Hormuz disrupts oil and LNG shipping, and oil volatility bleeds into inflation and equities. Second is <strong>regional stability</strong>: if the Israel–Lebanon front reignites, the whole truce is at risk. Third is <strong>diplomatic trust</strong>: the more both sides trade violation claims, the further 'peace' recedes."]),
            ("What's next — the uncertainty",
             ["The two sides are reported to be exchanging drafts to extend the truce. Whether that hardens into a peace agreement or drags on as an unstable ceasefire of repeated breaches and renegotiation is not yet clear. One thing is: <strong>this is a process, not an ending, and it shifts by the hour.</strong>"]),
        ],
        "foot": "This article compiles <strong>public reporting and institutional briefings as of June 12, 2026 (KST)</strong> and advocates no side. The military and diplomatic picture changes quickly, and some details differ across outlets (notably the mediators and the truce's duration). Given the nature of the topic, some elements may be estimated or reconstructed — cross-check primary reporting and official statements.",
        "nav_cat": "← ISSUES", "home": "🎮 GAMES",
        "bc": ["Home", "Blog", "Iran–US Ceasefire"],
        "og_title": "Iran–US Ceasefire: How Close Is Peace? — 5 Sticking Points",
        "og_desc": "Not a finished deal — a fragile April truce plus ongoing talks. Hormuz, nuclear, sanctions, and more.",
        "label": "Issue", "asof_badge": "As of Jun 12, 2026 · fast-moving",
    },
    "ja": {
        "lang": "ja", "slug": f"{SLUG}-ja", "og_locale": "ja_JP",
        "title": "イラン・米国の停戦はどこまで来たか — 終戦交渉の現在地と5つの争点",
        "desc": "2026年4月の停戦以降、イランと米国は脆い停戦状態が続く。6月10〜11日にも双方の攻撃と停戦違反の応酬。パキスタン・カタール仲介の交渉、ホルムズ・核・制裁など5つの争点を信頼できる報道に基づき整理。（6月12日時点）",
        "kicker": "📰 時事 · 中東情勢ブリーフ",
        "h1": 'イラン・米国の停戦は<span class="hl">終戦</span>へ向かうか',
        "dek": "結論から言えば、これは<strong>「終戦合意の完了」ではない</strong>。4月の停戦が綱渡りで維持される中、終戦に向けた交渉が進行中という段階だ。6月10〜11日にも双方の攻撃と「停戦違反」の応酬があった。信頼できる報道に基づき、現状と核心の争点だけを整理する。",
        "asof": "本記事は<strong>2026年6月12日（日本時間）</strong>時点の公開報道を整理したものです。事態は急速に変化するため、原典の報道を再確認してください。",
        "read": "7分",
        "secs": [
            ("現状 — 一段落で要約",
             ["<strong>停戦は存在するが脆い。</strong> 2026年4月7〜8日、5週間超の戦闘の末にイランと米国はイスラエルを含む停戦で合意し、トランプ大統領はこれを事実上無期限に延長したとした。だが6月7〜8日のイスラエルによるベイルート南部空爆の後、イランがイスラエルへ弾道ミサイルを発射し、4月の停戦以降初の直接衝突が再発。6月10日には米国がイランのレーダー・ドローン施設を攻撃し、イランが湾岸でミサイルで応酬した。イラン外務省は米国の停戦違反を非難した。<em>つまり「停戦」は生きているが「終戦」には程遠い。</em>"]),
            ("ここまでの経緯 — 短い時系列",
             ["<strong>2〜3月:</strong> 核・ミサイル計画と域内対立を巡る緊張が武力衝突に発展（「2026年イラン戦争」）。",
              "<strong>4月7〜8日:</strong> 5週間余りの戦闘の末、<strong>イスラエルを含む停戦</strong>が成立。後にトランプ大統領が無期限延長を表明。",
              "<strong>5月:</strong> 両者が広範な和平協定に近づいたとの報道。トランプは覚書（MOU）の最終化が近く、ホルムズ海峡が再開しうると言及。イランは「米国の誠実さの確認が必要」との立場。",
              "<strong>6月7〜8日:</strong> イスラエルのベイルート南部空爆 → イランの対イスラエル弾道ミサイル。4月以降初の直接衝突。",
              "<strong>6月10〜11日:</strong> 米国のイラン・レーダー・ドローン施設攻撃 → イランの湾岸ミサイル応酬。イラン外務省が米国の停戦違反と矛盾したメッセージを非難。交渉は継続と報道。"]),
            ("誰が仲介しているか",
             ["報道によれば<strong>パキスタン</strong>が一次仲介者として、イスラマバードで交渉を仲介してきた。<strong>カタール</strong>は5月22日から補助的仲介者として加わった。議題はホルムズの航行自由、イランの核・弾道ミサイル計画、制裁・凍結資産・戦後復興、そして長期和平協定だ。"]),
            ("核心の争点5つ",
             ["<strong>① ホルムズ海峡。</strong> 停戦条件には海峡再開が含まれるが、報道上は事実上閉鎖が続く。世界の原油の要衝であり、再開の可否がエネルギー価格に直結する。",
              "<strong>② 核・弾道ミサイル。</strong> 米国はイランの核能力への制約を、イランは相応の制裁緩和を求める。検証方法が最大の難所だ。",
              "<strong>③ 制裁・資産・賠償。</strong> イランの「10項目」には制裁解除、凍結資産の返還、戦争賠償、イラク・レバノン・イエメンの紛争終結要求が含まれるとされる。",
              "<strong>④ 域内の戦線。</strong> イスラエル・レバノン（ベイルート）衝突が停戦を揺るがす最大の変数だ。レバノンを合意に含めるかが争点として残る。",
              "<strong>⑤ 信頼・検証。</strong> 双方が互いに「停戦違反」を主張する中、合意履行を誰がどう保証するかが終戦の鍵だ。トランプは和平協定をアブラハム合意の拡大と結びつけたい意向と伝えられる。"]),
            ("なぜ重要か",
             ["最も直接的な波及は<strong>エネルギーと市場</strong>だ。ホルムズが塞がれば原油・LNG輸送が揺らぎ、原油のボラティリティはインフレと株式に波及する。第二は<strong>域内の安定</strong>。イスラエル・レバノン戦線が再燃すれば停戦全体が危うくなる。第三は<strong>外交の信頼</strong>。違反の応酬が続くほど「終戦」という言葉は遠のく。"]),
            ("今後 — 不確実性",
             ["現在、両者は停戦延長に向けた草案を交わしていると報じられる。これが「終戦の和平協定」に固まるのか、違反と再交渉が繰り返される不安定な停戦が長引くのかは、まだ断定できない。確かなのは一つ — <strong>今は終わりではなく過程であり、状況は時間単位で変わる。</strong>"]),
        ],
        "foot": "本記事は2026年6月12日（日本時間）時点の<strong>公開報道・機関資料を総合・整理</strong>したもので、特定の立場を擁護しません。戦況と交渉は急速に変化し、一部の細部は報道間で異なる場合があります（特に仲介国・停戦延長期間）。軍事・外交の性格上、推定・再構成を含みうるため、原典の報道と公式発表で相互確認してください。",
        "nav_cat": "← 時事", "home": "🎮 GAMES",
        "bc": ["ホーム", "ブログ", "イラン・米国停戦"],
        "og_title": "イラン・米国の停戦は終戦へ向かうか — 5つの争点（6/12時点）",
        "og_desc": "終戦合意ではない — 脆い4月停戦＋進行中の交渉。ホルムズ・核・制裁など整理。",
        "label": "時事", "asof_badge": "2026.6.12時点 · 急速に変化",
    },
    "zh": {
        "lang": "zh-CN", "slug": f"{SLUG}-zh", "og_locale": "zh_CN",
        "title": "伊朗-美国停火走到哪一步 — 通向终战的现状与5大焦点",
        "desc": "2026年4月停火以来，伊朗与美国维持着脆弱、争议不断的停火。6月10–11日双方再度交火并互指违反停火。基于权威报道，梳理巴基斯坦·卡塔尔斡旋的谈判与霍尔木兹、核、制裁等5大焦点。（截至6月12日）",
        "kicker": "📰 时事 · 中东局势简报",
        "h1": '伊朗-美国停火，能走向<span class="hl">终战</span>吗',
        "dek": "先说结论：这<strong>不是已经达成的终战和平协议</strong>，而是4月停火艰难维持、通向终战的谈判仍在进行的阶段。就在6月10–11日，双方仍有交火并互指违反停火。下面基于权威报道，只梳理现状与核心焦点。",
        "asof": "本文整理截至<strong>2026年6月12日（北京时间）</strong>的公开报道。事态变化很快，请在引用前核对原始报道。",
        "read": "7分钟",
        "secs": [
            ("当前状况 — 一段话概括",
             ["<strong>停火存在，但很脆弱。</strong> 2026年4月7–8日，经过五周多的战斗，伊朗与美国达成包含以色列在内的停火，特朗普总统称已将其无限期延长。但6月7–8日以色列空袭贝鲁特南郊后，伊朗向以色列发射弹道导弹，为4月停火以来首次直接冲突；6月10日美国打击伊朗雷达与无人机设施，伊朗在海湾以导弹回应。伊朗外交部指责美国违反停火。<em>简言之：“停火”仍在，但离“终战”尚远。</em>"]),
            ("如何走到今天 — 简短时间线",
             ["<strong>2–3月：</strong> 围绕核·导弹计划与地区对抗的紧张升级为武装冲突（“2026年伊朗战争”）。",
              "<strong>4月7–8日：</strong> 经五周多战斗，<strong>包含以色列的停火</strong>达成。特朗普随后表示已无限期延长。",
              "<strong>5月：</strong> 有报道称双方接近达成更广泛的和平协议；特朗普称谅解备忘录（MOU）接近完成、霍尔木兹海峡可能重开。伊朗表示需确认美方的诚意。",
              "<strong>6月7–8日：</strong> 以色列空袭贝鲁特南郊 → 伊朗对以发射弹道导弹，为4月以来首次直接冲突。",
              "<strong>6月10–11日：</strong> 美国打击伊朗雷达·无人机设施 → 伊朗在海湾以导弹回应。伊朗外交部指责美国违反停火并发出矛盾信号。据报道谈判仍在继续。"]),
            ("谁在斡旋",
             ["据报道，<strong>巴基斯坦</strong>是主要斡旋方，在伊斯兰堡主持谈判。<strong>卡塔尔</strong>自5月22日起作为次要斡旋方加入。议题涵盖霍尔木兹的航行自由、伊朗的核与弹道导弹计划、制裁·冻结资产·战后重建，以及长期和平协议。"]),
            ("五大焦点",
             ["<strong>① 霍尔木兹海峡。</strong> 重开海峡是停火条款之一，但据报道仍处于事实上的关闭状态。作为全球原油咽喉，其状态直接牵动能源价格。",
              "<strong>② 核与导弹。</strong> 美国要求约束伊朗核能力，伊朗要求相应的制裁缓解。核查方式是最大难点。",
              "<strong>③ 制裁·资产·赔偿。</strong> 据称伊朗的“十点”包含解除制裁、归还冻结资产、战争赔偿，以及结束伊拉克、黎巴嫩、也门的冲突。",
              "<strong>④ 地区战线。</strong> 以色列-黎巴嫩（贝鲁特）冲突是动摇停火的最大变量；是否将黎巴嫩纳入协议仍有争议。",
              "<strong>⑤ 信任与核查。</strong> 在双方互指违反停火之际，由谁、如何保证协议履行，是真正终战的关键。据报道特朗普希望将和平协议与扩大《亚伯拉罕协议》挂钩。"]),
            ("为何重要",
             ["最直接的影响是<strong>能源与市场</strong>。霍尔木兹受阻会扰动原油与LNG运输，油价波动会传导至通胀与股市。其次是<strong>地区稳定</strong>：若以色列-黎巴嫩战线重燃，整个停火都将岌岌可危。第三是<strong>外交信任</strong>：互指违反越频繁，“终战”二字就越遥远。"]),
            ("展望 — 不确定性",
             ["目前据报道双方正就延长停火交换草案。这会固化为“终战和平协议”，还是演变为违约与再谈判反复、长期不稳的停火，目前尚难断定。可以确定的是：<strong>这是过程而非结局，且以小时为单位变化。</strong>"]),
        ],
        "foot": "本文综合整理截至2026年6月12日（北京时间）的<strong>公开报道与机构资料</strong>，不为任何一方背书。战况与谈判变化迅速，部分细节在不同媒体间存在差异（尤其是斡旋国与停火延长期限）。鉴于军事与外交议题的性质，部分内容可能为推测或重构，请以原始报道与官方声明交叉核对。",
        "nav_cat": "← 时事", "home": "🎮 GAMES",
        "bc": ["首页", "博客", "伊朗-美国停火"],
        "og_title": "伊朗-美国停火能走向终战吗 — 5大焦点（截至6/12）",
        "og_desc": "并非已达成终战 — 脆弱的4月停火＋进行中的谈判。梳理霍尔木兹·核·制裁等焦点。",
        "label": "时事", "asof_badge": "截至2026.6.12 · 快速变化",
    },
}

CSS = """
  :root{--bg:#0b0f17;--surface:#141a26;--surface2:#1b2433;--border:#283246;--amber:#f59e0b;--amber2:#fbbf24;--red:#ef4444;--text:#d6deea;--dim:#8896ab;--white:#fff}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'Noto Sans KR',sans-serif;line-height:1.85;-webkit-font-smoothing:antialiased}
  .container{max-width:760px;margin:0 auto;background:var(--bg);min-height:100vh}
  .site-nav{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--border);background:rgba(11,15,23,.85);backdrop-filter:blur(8px);position:sticky;top:0;z-index:50}
  .site-nav a{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);text-decoration:none;letter-spacing:1px;transition:color .2s}
  .site-nav a:hover{color:var(--amber)}
  .hero{padding:30px 18px 22px;border-bottom:1px solid var(--border);background:radial-gradient(ellipse at 80% 0%,rgba(245,158,11,.10),transparent 60%),radial-gradient(ellipse at 0% 100%,rgba(239,68,68,.06),transparent 55%)}
  .kicker{display:inline-flex;align-items:center;gap:7px;font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#1a1206;background:linear-gradient(90deg,var(--amber),var(--amber2));padding:5px 11px;border-radius:20px;margin-bottom:14px}
  h1{font-size:30px;font-weight:900;color:var(--white);line-height:1.3;letter-spacing:-.02em;margin-bottom:14px}
  h1 .hl{color:var(--amber)}
  .dek{font-size:15.5px;color:#aebccd;line-height:1.75;margin-bottom:16px}
  .dek strong{color:var(--white)}
  .dek em{color:var(--amber2);font-style:normal;font-weight:700}
  .meta{display:flex;gap:14px;flex-wrap:wrap;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);letter-spacing:.5px}
  .meta b{color:var(--amber2)}
  .asof{margin:14px 18px 0;padding:11px 14px;border:1px solid rgba(239,68,68,.3);border-left:3px solid var(--red);border-radius:8px;background:rgba(239,68,68,.05);font-size:12.5px;color:#c7b3b3;line-height:1.6}
  .asof strong{color:#f0d5d5}
  .body{padding:8px 18px 0}
  .body p{font-size:15.5px;line-height:1.9;color:var(--text);margin:14px 0}
  .body strong{color:var(--white)}
  .body em{color:var(--amber2);font-style:normal;font-weight:700}
  h2{font-size:20px;font-weight:900;color:var(--white);margin:34px 0 4px;letter-spacing:-.01em;padding-top:18px;border-top:1px solid var(--border)}
  ul.tl{margin:10px 0;padding:0;list-style:none}
  ul.tl li{font-size:15px;line-height:1.8;color:#c4d0de;margin:9px 0;padding-left:18px;position:relative}
  ul.tl li::before{content:"▸";position:absolute;left:0;color:var(--amber)}
  ul.tl b{color:var(--white)}
  .foot{margin:30px 18px 18px;padding:14px 16px;background:var(--surface);border:1px solid var(--border);border-radius:12px;font-size:11.5px;line-height:1.75;color:var(--dim)}
  .foot strong{color:var(--amber2)}
  .src{margin-top:8px;display:flex;flex-wrap:wrap;gap:6px}
  .src a{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--amber);text-decoration:none;border:1px solid var(--border);padding:3px 8px;border-radius:6px}
  @media(min-width:768px){h1{font-size:35px}}
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

    secs_html = []
    for title, paras in c["secs"]:
        if len(paras) > 1 and any(p.startswith("<strong>") and ":" in p[:40] for p in paras):
            # timeline-style list
            items = "\n".join(f"<li>{p}</li>" for p in paras)
            secs_html.append(f'<h2>{title}</h2>\n<ul class="tl">\n{items}\n</ul>')
        else:
            body = "\n".join(f"<p>{p}</p>" for p in paras)
            secs_html.append(f"<h2>{title}</h2>\n{body}")
    secs_html = "\n".join(secs_html)

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
<meta property="article:published_time" content="2026-06-12T20:00:00+09:00">
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
