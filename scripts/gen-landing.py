# -*- coding: utf-8 -*-
"""영어 SEO 랜딩 생성기 — 메인 6종 각각의 검색 진입점.

배경 (2026-08-19):
    메인 게임 6종을 확정하면서, 각 게임에 영어 검색 진입점이 하나씩
    있어야 한다. 게임 본체(`/games/<id>/`)의 가시 콘텐츠는 한국어라
    영어 검색에는 잡히지 않는다. 랜딩은 게임을 iframe 으로 임베드하고
    영어 콘텐츠 + FAQ 스키마를 얹는다. 게임 본체는 건드리지 않는다.

    기존 3종(wheel-spinner / team-generator / dice-roller)은 손으로 쓴
    콘텐츠가 있어 여기서 재생성하지 않는다. 이 스크립트는 신규 3종만
    만든다: bingo-caller / race-picker / ladder-draw.

집필 원칙 — 정보 이득:
    "1) 이름을 넣는다 2) 버튼을 누른다" 식 조작 설명은 경쟁 사이트에도
    전부 있어 2026 기준으로는 저품질 판정을 받는다. 각 도구의 수학·역사·
    실제 운영 팁처럼 이 페이지에서만 얻는 내용을 반드시 넣는다.

    python scripts/gen-landing.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lp_clusters import CLUSTERS, hreflang_lines  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public"

# 6종 상호 링크 — 모든 랜딩이 나머지 5개를 가리킨다.
ALL = [
    ("/wheel-spinner/",  "Wheel Spinner",   "Type names, spin, and one is picked at random."),
    ("/team-generator/", "Team Generator",  "Split any roster into balanced random teams."),
    ("/dice-roller/",    "Dice Roller",     "Roll one to six dice with a real physical tumble."),
    ("/bingo-caller/",   "Bingo Caller",    "Call numbers without repeats and keep the history on screen."),
    ("/race-picker/",    "Race Picker",     "Turn a draw into a race with a full finishing order."),
    ("/ladder-draw/",    "Ladder Draw",     "Ghost leg / amidakuji — pick a line before the paths appear."),
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>

    <meta name="lp-ad-policy" content="off"><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="keywords" content="{keywords}">
<link rel="canonical" href="https://luckyplz.com{slug}">
{hreflang}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Lucky Please">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="https://luckyplz.com{slug}">
<meta property="og:image" content="https://luckyplz.com/og/games/{og_img}.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_desc}">
<meta name="twitter:image" content="https://luckyplz.com/og/games/{og_img}.png">
<script type="application/ld+json">{app_ld}</script>
<script type="application/ld+json">{faq_ld}</script>
<script type="application/ld+json">{crumb_ld}</script>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0A0A1A">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Noto+Sans+KR:wght@400;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NZDPE3H3DQ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-NZDPE3H3DQ');</script>
<style>
  :root{{--primary:#FF6B35;--secondary:#00D9FF;--accent:#FFE66D;--dark:#0A0A1A;--surface:#12122a;--border:rgba(255,255,255,.1);--text:#e8ecf4;--dim:#9aa6be}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--dark);color:var(--text);font-family:'Noto Sans KR',-apple-system,sans-serif;line-height:1.7;-webkit-font-smoothing:antialiased}}
  .wrap{{max-width:840px;margin:0 auto;padding:0 18px}}
  .nav{{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid var(--border);position:sticky;top:0;background:rgba(10,10,26,.85);backdrop-filter:blur(8px);z-index:50}}
  .nav a{{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--dim);text-decoration:none;letter-spacing:1px}}
  .nav a:hover{{color:var(--secondary)}}
  .hero{{text-align:center;padding:36px 0 18px}}
  h1{{font-size:30px;font-weight:900;line-height:1.25;letter-spacing:-.02em;background:linear-gradient(135deg,var(--primary),var(--accent),var(--secondary));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
  .lead{{font-size:16px;color:var(--dim);margin:14px auto 0;max-width:680px}}
  .cta-row{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:20px 0 6px}}
  .btn{{font-family:'Orbitron','Noto Sans KR',sans-serif;font-weight:700;font-size:14px;letter-spacing:.04em;padding:12px 22px;border-radius:10px;text-decoration:none;border:1px solid var(--border)}}
  .btn.primary{{background:linear-gradient(135deg,var(--primary),#ff8c42);color:#1a0d04;border:none}}
  .btn.ghost{{color:var(--text);background:rgba(255,255,255,.05)}}
  .embed{{margin:18px 0 6px;border:1px solid var(--border);border-radius:16px;overflow:hidden;background:#06061a;box-shadow:0 16px 50px rgba(0,0,0,.5)}}
  .embed iframe{{display:block;width:100%;height:660px;border:0}}
  .embed-cap{{font-size:12px;color:var(--dim);text-align:center;margin:8px 0 0}}
  h2{{font-size:21px;font-weight:800;color:#fff;margin:34px 0 10px;letter-spacing:-.01em}}
  h3{{font-size:16px;font-weight:700;color:#fff;margin:18px 0 6px}}
  p{{margin:10px 0;color:var(--text)}}
  .body p{{color:#cfd6e6}}
  ol,ul{{margin:10px 0 10px 22px;color:#cfd6e6}}
  li{{margin:6px 0}}
  .uses{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0}}
  .use{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:13px 14px}}
  .use b{{color:#fff;display:block;margin-bottom:3px;font-size:14px}}
  .use span{{font-size:13px;color:var(--dim)}}
  .faq{{margin:10px 0}}
  .faq details{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:0 14px;margin:8px 0}}
  .faq summary{{cursor:pointer;padding:13px 0;font-weight:700;color:#fff;font-size:15px;list-style:none}}
  .faq summary::-webkit-details-marker{{display:none}}
  .faq summary::after{{content:'+';float:right;color:var(--secondary);font-weight:900}}
  .faq details[open] summary::after{{content:'\\2013'}}
  .faq p{{padding:0 0 14px;margin:0;color:var(--dim);font-size:14px}}
  .more{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0}}
  .more a{{display:block;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px;text-decoration:none;color:#fff;font-weight:700;transition:border-color .2s}}
  .more a:hover{{border-color:var(--secondary)}}
  .more a span{{display:block;font-size:12px;color:var(--dim);font-weight:400;margin-top:3px}}
  @media(max-width:600px){{h1{{font-size:24px}}.uses,.more{{grid-template-columns:1fr}}.embed iframe{{height:560px}}}}
</style>
</head>
<body>

<nav class="nav">
  <a href="/">&larr; LUCKY PLEASE</a>
  <a href="/arcade/">ARCADE</a>
</nav>

<div class="wrap">

  <header class="hero">
    <h1>{h1}</h1>
    <p class="lead">{lead}</p>
    <div class="cta-row">
      <a class="btn primary" href="{game}">&#9654; Open Full Screen</a>
      <a class="btn ghost" href="#how">How it works</a>
    </div>
  </header>

  <div class="embed">
    <iframe src="{game}" title="{h1} &mdash; play here" loading="lazy"></iframe>
  </div>
  <p class="embed-cap">Running right above &#9757;&#65039; &mdash; or <a href="{game}" style="color:var(--secondary)">open it full screen</a>.</p>

  <div class="body">
{content}
    <h2>Frequently asked questions</h2>
    <div class="faq">
{faq_html}
    </div>

    <h2>The other five random pickers</h2>
    <div class="more">
{more_html}
    </div>

  </div>
</div>

<script src="/js/siteFooter.js?v=1" defer></script>
</body>
</html>
"""

PAGES = {}

# ─────────────────────────────────────────────────── Bingo caller
PAGES["/bingo-caller/"] = dict(
    game="/games/bingo/",
    og_img="bingo",
    h1="Free Online Bingo Caller",
    title="Free Online Bingo Caller — Random Number Caller | Lucky Please",
    description="A free online bingo number caller. Draws 1-75 or 1-90 at random with no repeats, keeps every called number on screen, and works on a phone or a projector. No sign-up.",
    keywords="bingo caller, online bingo caller, bingo number generator, random bingo numbers, free bingo caller, bingo number picker, virtual bingo caller, bingo 75, bingo 90",
    og_title="Free Online Bingo Caller — Random Number Caller",
    og_desc="Draws bingo numbers at random with no repeats and keeps the history on screen. Free, no sign-up.",
    lead="Draws numbers at random, never repeats one, and keeps every call visible so latecomers can catch up. Free, nothing to install, and readable from the back of a room.",
    content="""    <h2 id="how">How to run a game with it</h2>
    <ol>
      <li><b>Put it on the biggest screen you have.</b> A laptop on a projector, a tablet propped up, or a phone passed to whoever is calling. The called-number history stays on screen the whole time.</li>
      <li><b>Draw a number.</b> Each draw is taken from the numbers that have not come out yet, so a repeat is impossible &mdash; you never have to check by hand.</li>
      <li><b>Call it twice, then pause.</b> Say the number, say it again, wait. The single most common complaint at a live game is that calls come too fast; the pause is what people are actually asking for.</li>
      <li><b>Verify against the history.</b> When someone shouts, read their card back against the list on screen. That list is the record, which ends arguments before they start.</li>
    </ol>

    <h2>Where a bingo caller gets used</h2>
    <div class="uses">
      <div class="use"><b>Classrooms</b><span>Vocabulary and times-table bingo, where the teacher needs both hands free.</span></div>
      <div class="use"><b>Community halls</b><span>Charity and club nights that have cards but no machine.</span></div>
      <div class="use"><b>Office parties</b><span>End-of-year events and icebreakers with printed card sheets.</span></div>
      <div class="use"><b>Care homes</b><span>Large on-screen numbers matter more than any other feature.</span></div>
      <div class="use"><b>Family gatherings</b><span>The set is in the loft; the cards are not.</span></div>
      <div class="use"><b>Online calls</b><span>Share your screen and everyone sees the same draw at the same time.</span></div>
    </div>

    <h2>75-ball, 90-ball, and why the numbers differ</h2>
    <p>Two formats dominate and they are not interchangeable. <b>75-ball</b> bingo, standard in North America, uses a 5&times;5 card with a free centre square and the letters B-I-N-G-O mapped to number bands: B is 1&ndash;15, I is 16&ndash;30, N is 31&ndash;45, G is 46&ndash;60, O is 61&ndash;75. Because of that banding, the traditional call is a letter and a number together &mdash; "B-7" &mdash; which lets players scan a single column instead of the whole card.</p>
    <p><b>90-ball</b> bingo, standard in the UK, Ireland and Australia, uses a 9&times;3 ticket with fifteen numbers on it and is normally played in three stages: one line, two lines, then a full house. There are no letters. Sets are usually sold in strips of six tickets that between them contain all ninety numbers exactly once, which is why a strip guarantees you mark something on every single call.</p>
    <p>Decide the format before you start, because it changes how long the game runs. A 75-ball single-line game often ends inside twenty calls; a 90-ball full house usually needs somewhere in the fifties.</p>

    <h2>How long a game actually takes</h2>
    <p>This is the question people get wrong when planning an event. For 75-ball bingo with a normal room of players, a single horizontal line typically falls somewhere between the fifteenth and twenty-fifth call, and a blackout (every square) needs almost the whole ball set &mdash; expect the high sixties or beyond. For 90-ball, a first line usually lands in the twenties and a full house in the low-to-mid fifties.</p>
    <p>Two practical consequences. First, more players make games <i>shorter</i>, not longer: with more cards in play, someone hits the pattern sooner. Second, if you have a fixed slot to fill, control the length with the pattern rather than the pace &mdash; switching from full house to one line will halve a game far more reliably than calling faster.</p>

    <h2>Why draws without replacement matter</h2>
    <p>A bingo caller is not the same thing as a random number generator, and the difference is the whole point. A generator picks from 1&ndash;75 every time, so it will eventually repeat a number, which invalidates the game. A caller draws <i>without replacement</i>: each number leaves the pool once it is called.</p>
    <p>That has a consequence worth knowing. Early in a game each remaining number has a 1/75 chance; by the sixtieth call the fifteen survivors are each at 1/15. The odds move as the game goes, which is exactly why late-game bingo feels tense &mdash; that tension is real, not imagined.</p>""",
    faq=[
        ("Is the bingo caller free?",
         "Yes. It is free with no sign-up and nothing to install. Open the page and start calling."),
        ("Can it call the same number twice?",
         "No. Numbers are drawn without replacement, so a called number leaves the pool and cannot come out again in the same game. That is what separates a bingo caller from a plain random number generator."),
        ("Does it show which numbers have already been called?",
         "Yes. Every called number stays visible on screen, so players who lost track can catch up and you can verify a winning card against the record instead of relying on memory."),
        ("Can I use it with printed bingo cards?",
         "Yes. It replaces the cage and the balls, not the cards. Any standard printed card set works, and the caller is the only piece of equipment you need."),
        ("Does it work on a projector or a shared screen?",
         "Yes. It scales from a phone up to a projector, so you can put it on the biggest screen in the room or share it on a video call and everyone sees the same draw at the same moment."),
        ("How many calls does a typical game take?",
         "For 75-ball bingo a single line usually falls between the fifteenth and twenty-fifth call, while a blackout needs most of the ball set. For 90-ball, a first line tends to land in the twenties and a full house in the low fifties."),
    ],
)

# ─────────────────────────────────────────────────── Race picker
PAGES["/race-picker/"] = dict(
    game="/games/car-racing/",
    og_img="car-racing",
    h1="Random Race Picker",
    title="Random Race Picker — Draw a Full Order, Not Just a Winner | Lucky Please",
    description="A random picker that runs your entries as a race and gives you a complete finishing order. Free, no sign-up, works on any phone. Better than a wheel when you need a ranking.",
    keywords="random race picker, random order generator, random ranking generator, randomize order, random turn order, race random picker, pick order at random, random draw with ranking",
    og_title="Random Race Picker — Draw a Full Order, Not Just a Winner",
    og_desc="Runs your entries as a race and gives a complete finishing order. Free, no sign-up.",
    lead="Most random pickers answer &ldquo;who?&rdquo;. This one answers &ldquo;in what order?&rdquo; &mdash; every entry gets a lane, the race runs, and you end up with a full ranking instead of a single winner.",
    content="""    <h2 id="how">How it works</h2>
    <ol>
      <li><b>Enter the names.</b> Each one is assigned a lane. Lane position has no effect on the result &mdash; it is purely where the entry sits on screen.</li>
      <li><b>Start the race.</b> Positions swap the whole way down. Watching the lead change hands is the point, not a side effect.</li>
      <li><b>Read the finishing order.</b> You get first through last, not just a winner, so one run settles an entire schedule.</li>
      <li><b>Share the result.</b> A one-tap link reproduces the same finishing order for anyone who missed it.</li>
    </ol>

    <h2>When a ranking beats a single pick</h2>
    <div class="uses">
      <div class="use"><b>Presentation order</b><span>One run assigns every slot instead of spinning a wheel six times.</span></div>
      <div class="use"><b>Turn order</b><span>Board games, card games, and anything where seat order matters.</span></div>
      <div class="use"><b>Chore rotas</b><span>Rank the household and work down the list week by week.</span></div>
      <div class="use"><b>Draft picks</b><span>Fantasy leagues and pickup teams that need a full pick sequence.</span></div>
      <div class="use"><b>Queue position</b><span>Who goes first at karaoke, and who has to follow the good singer.</span></div>
      <div class="use"><b>Splitting the bill</b><span>Last place pays, or first place picks the restaurant next time.</span></div>
    </div>

    <h2>Why a race and not just a shuffled list</h2>
    <p>A shuffled list and a race produce statistically identical results. The difference is entirely in how a group receives them. A list appears fully formed and invites the question &ldquo;how did it decide that?&rdquo;. A race is watched from start to finish, so by the time the order exists, everyone has already seen it being produced. Nobody asks how it decided, because they were there.</p>
    <p>This matters most for the position people actually care about, which is usually last. Being told you are last on a list feels arbitrary. Watching yourself get overtaken on the final stretch feels like something that happened. Same outcome, very different reception &mdash; and reception is the only reason to use a random picker instead of just choosing.</p>

    <h2>The mathematics of a random order</h2>
    <p>With <i>n</i> entries there are <i>n</i>! possible finishing orders, and each is equally likely. That number grows faster than most people expect: five entries give 120 orders, eight give 40,320, and ten give more than three and a half million. In practice this means you can stop worrying about repeats &mdash; past about six entries, seeing the same complete order twice is effectively impossible.</p>
    <p>A subtler point is worth knowing if anyone accuses the race of being unfair. Every entry has a 1/<i>n</i> chance of finishing first, a 1/<i>n</i> chance of finishing last, and a 1/<i>n</i> chance of any position in between. Lane number, the order you typed names in, and name length all have zero effect. If a run looks suspicious &mdash; the same person last twice in a row &mdash; that is expected: with six people, the odds of one specific person finishing last on two consecutive runs are about 1 in 36, so across an evening it will happen to someone.</p>

    <h2>Getting the length right</h2>
    <p>A race takes roughly half a minute, which is deliberately slow compared with a wheel. That is the correct trade only when the group is watching together. If people are heads-down, or you just need a name for a form, use the wheel spinner instead &mdash; it answers in two seconds. Use the race when the audience is the point: a classroom, a table, a video call where everyone is already looking at the same screen.</p>""",
    faq=[
        ("Is the race picker free?",
         "Yes. It is free with no sign-up and nothing to install. Add your names and start the race."),
        ("Is the finishing order really random?",
         "Yes. Every entry has the same chance of any position. Lane number, the order you typed names in, and name length have no effect on the result."),
        ("How is this different from a wheel spinner?",
         "A wheel picks one winner in about two seconds. The race produces a complete ranking from first to last over about half a minute. Use the wheel when you need a name; use the race when you need an order."),
        ("How many people can race at once?",
         "Enough for a normal group or class. Each entry gets its own lane, and the finishing order lists every one of them from first to last."),
        ("Can I share the finishing order?",
         "Yes. After a race you get a one-tap share link, and anyone who opens it sees the same finishing order, which makes the result hard to dispute."),
        ("Does the same person keep finishing last?",
         "It can look that way, and it is expected. With six entries, one specific person finishing last twice in a row has odds of about 1 in 36, so over an evening it will happen to somebody. Each race is independent of the last."),
    ],
)

# ─────────────────────────────────────────────────── Ladder draw
PAGES["/ladder-draw/"] = dict(
    game="/games/ladder/",
    og_img="ladder",
    h1="Ladder Draw (Ghost Leg / Amidakuji)",
    title="Ladder Draw Online — Ghost Leg &amp; Amidakuji Generator | Lucky Please",
    description="A free online ladder draw, also known as ghost leg or amidakuji. Pick a line before the paths are revealed, then follow it down to your result. No sign-up, works on any phone.",
    keywords="ladder draw, ghost leg, amidakuji, amidakuji online, ladder game online, ladder lottery, sadari game, random assignment tool, ladder picker, ghost leg generator",
    og_title="Ladder Draw Online — Ghost Leg &amp; Amidakuji Generator",
    og_desc="Pick a line before the paths appear, then follow it down. Free ghost leg and amidakuji generator.",
    lead="Everyone picks a line at the top before any of the rungs are shown. Then the paths appear and each line leads somewhere different. Known as ghost leg in English, <i>amidakuji</i> in Japan, and <i>sadari</i> in Korea.",
    content="""    <h2 id="how">How a ladder draw works</h2>
    <ol>
      <li><b>Set the outcomes.</b> Put whatever is being assigned at the bottom &mdash; prizes, chores, roles, who pays.</li>
      <li><b>Everyone claims a line first.</b> This is the part that matters. People commit to a starting position while the rungs are still hidden.</li>
      <li><b>Reveal the ladder.</b> The horizontal rungs appear, generated at random.</li>
      <li><b>Follow the path down.</b> Trace from a starting line; every time you meet a rung, you cross to the neighbouring line and keep descending. Where you land is your result.</li>
    </ol>

    <h2>What people use it for</h2>
    <div class="uses">
      <div class="use"><b>Assigning chores</b><span>Every person gets exactly one job and no job is doubled up.</span></div>
      <div class="use"><b>Secret Santa</b><span>Match givers to receivers in one pass.</span></div>
      <div class="use"><b>Splitting a bill unevenly</b><span>Put different amounts at the bottom instead of names.</span></div>
      <div class="use"><b>Classroom roles</b><span>Assign presentation topics or group jobs without argument.</span></div>
      <div class="use"><b>Who pays what</b><span>One person gets the bill, one gets the tip, everyone else walks.</span></div>
      <div class="use"><b>Team positions</b><span>Assign roles that have to be one-to-one, not randomly repeated.</span></div>
    </div>

    <h2>The property that makes it different from a wheel</h2>
    <p>A ladder draw is not just another way to pick at random. It produces a <b>bijection</b> &mdash; a strict one-to-one matching. Every person lands on exactly one outcome and every outcome is claimed by exactly one person. No result is doubled up and none is left over.</p>
    <p>A wheel cannot do this. Spin a wheel six times for six chores and you will very likely draw the same chore twice while another goes unassigned; you would have to remove each result manually between spins. The ladder handles it structurally, which is why it is the right tool whenever the outcomes are a set to be distributed rather than a pool to be sampled.</p>
    <p>The mathematical reason is neat: each horizontal rung swaps two adjacent lines, and no matter how many swaps you apply in sequence, the result is still a permutation. You cannot break the one-to-one property by adding rungs, only shuffle it further.</p>

    <h2>Why committing to a line first is the whole point</h2>
    <p>The ladder&rsquo;s real advantage over every other random picker is procedural rather than mathematical. Participants choose their starting line <i>before</i> the paths exist. That means each person made a real choice, and nobody &mdash; including whoever is running it &mdash; could have known where that choice would lead.</p>
    <p>This is what defuses the &ldquo;the draw was rigged&rdquo; objection that a wheel or a shuffled list will always attract. With a wheel, a suspicious person has to trust the tool. With a ladder, they only have to trust that the rungs were not visible when they picked, which they can verify with their own eyes. That is why the format has survived for centuries in Japan and Korea for exactly the decisions people are touchiest about.</p>

    <h2>Where the name comes from</h2>
    <p>In Japan the game is <i>amidakuji</i> (&#12354;&#12415;&#12384;&#12367;&#12376;), literally &ldquo;Amida lottery&rdquo;. The name refers to Amida Buddha, because early versions were drawn as lines radiating from a centre point like the halo in Buddhist paintings, and only later flattened into the parallel-lines-and-rungs form used today. In Korea the same game is <i>sadari-tagi</i> (&#49324;&#45796;&#47532;&#53440;&#44592;), &ldquo;ladder climbing&rdquo;, and it is a fixture of school trips and office outings. English-language software usually calls it <b>ghost leg</b>, a translation of the Chinese name.</p>
    <p>One consequence of that history is worth knowing when you use it with a mixed group: many East Asian participants will know the rules instantly and will expect to pick their line before seeing the rungs. Running it the other way round &mdash; showing the ladder first &mdash; removes the entire point and they will notice.</p>""",
    faq=[
        ("What is a ladder draw?",
         "It is a random assignment tool, known as ghost leg in English, amidakuji in Japan and sadari-tagi in Korea. Each person picks a line at the top before the horizontal rungs are shown, then follows the path down to whatever outcome it reaches."),
        ("Is it free?",
         "Yes. It is free with no sign-up and nothing to install. Set your outcomes, let everyone claim a line, and reveal the ladder."),
        ("How is it different from a wheel spinner?",
         "A ladder produces a strict one-to-one matching: every person gets exactly one outcome and every outcome is taken exactly once. A wheel samples with replacement, so spinning it repeatedly can give the same result twice while leaving another unassigned."),
        ("Is the result really random?",
         "Yes. The horizontal rungs are generated at random and are not shown until after everyone has claimed a starting line, so no starting position is better than another."),
        ("Why should people pick their line before the ladder is revealed?",
         "That order is what makes the draw convincing. Each participant makes a real choice at a moment when nobody, including the organiser, could know where it leads, which removes any suspicion that the draw was arranged."),
        ("Does it work on a phone?",
         "Yes. It is built mobile-first, so you can pass one phone around for everyone to claim a line and then reveal the ladder for the whole group to watch."),
    ],
)


SLUG2TOOL = {c["en"]: k for k, c in CLUSTERS.items()}


def build(slug, cfg):
    name = cfg["h1"].split(" (")[0]
    app_ld = json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": "Lucky Please " + name, "url": "https://luckyplz.com" + slug,
        "applicationCategory": "GameApplication", "operatingSystem": "Any (web browser)",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": cfg["og_desc"],
        "publisher": {"@type": "Organization", "name": "Lucky Please", "url": "https://luckyplz.com/"},
    }, ensure_ascii=False, separators=(",", ":"))
    faq_ld = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in cfg["faq"]],
    }, ensure_ascii=False, separators=(",", ":"))
    crumb_ld = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://luckyplz.com/"},
            {"@type": "ListItem", "position": 2, "name": name, "item": "https://luckyplz.com" + slug},
        ],
    }, ensure_ascii=False, separators=(",", ":"))

    faq_html = "\n".join(
        "      <details><summary>%s</summary><p>%s</p></details>" % (q, a) for q, a in cfg["faq"])
    more_html = "\n".join(
        '      <a href="%s">%s<span>%s</span></a>' % (u, t, d) for u, t, d in ALL if u != slug)

    hreflang = hreflang_lines(SLUG2TOOL[slug], indent="")
    return TEMPLATE.format(slug=slug, hreflang=hreflang, app_ld=app_ld, faq_ld=faq_ld, crumb_ld=crumb_ld,
                           faq_html=faq_html, more_html=more_html, **cfg)


def main():
    for slug, cfg in PAGES.items():
        out = OUT / slug.strip("/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        html = build(slug, cfg)
        out.write_text(html, encoding="utf-8")
        body = html[html.index('<div class="body">'):html.index("</body>")]
        words = len(re.sub(r"<[^>]+>", " ", body).split())
        print("%-18s -> %s  (본문 %d단어)" % (slug, out.relative_to(ROOT), words))


if __name__ == "__main__":
    main()
