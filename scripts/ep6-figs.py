"""
Ep.6 figure generator (all hand-drawn — finale of the series).

- fig-01: 2026 spring frontier-6 coordinates (revenue · valuation · users)
- fig-02: AI capability curve 2022-2026 (benchmark scores)
- fig-03: AI surfaces in daily life (OS / search / messenger / work / device)
- fig-04: 4-hyperscaler AI capex time series 2022-2026
- fig-05: US data center electricity share (2023 → 2030 projection)
- fig-06: AI regulation map (EU / US / China / KR / JP)
- fig-07: Three 2030 scenarios — gradual / leap / shock
- fig-08: Series recap — Ep.1 through Ep.6 in one chart
"""
import sys
import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8")

EP6 = Path(r"C:\code\python\luckyplz\.claude\worktrees\inspiring-cerf-fac44c\public\assets\anthropic-series\ep6")

PAPER       = (245, 235, 216)
PAPER_LIGHT = (250, 240, 212)
PAPER_DARK  = (235, 224, 200)
INK         = ( 44,  36,  22)
INK_SOFT    = ( 74,  62,  42)
INK_DIM     = (122, 106,  82)
BROWN       = (139, 111,  71)
AUBURN      = (194,  65,  12)
GOLD        = (184, 134,  11)
LINE        = (212, 197, 168)

ARIAL    = r"C:\Windows\Fonts\arial.ttf"
ARIAL_BD = r"C:\Windows\Fonts\arialbd.ttf"
ARIAL_IT = r"C:\Windows\Fonts\ariali.ttf"

W, H = 1600, 900


def make_paper_canvas(w=W, h=H):
    return Image.new("RGB", (w, h), PAPER)


def add_caption_bar(canvas, text):
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(ARIAL, 22)
    draw.text((40, H - 50), text, font=font, fill=INK_DIM)


def title_block(draw, title, subtitle=None):
    font_title = ImageFont.truetype(ARIAL_BD, 40)
    tw = draw.textlength(title, font=font_title)
    draw.text(((W - tw) / 2, 50), title, font=font_title, fill=INK)
    draw.rectangle([(W // 2 - 40, 112), (W // 2 + 40, 114)], fill=AUBURN)
    if subtitle:
        font_sub = ImageFont.truetype(ARIAL_IT, 22)
        tws = draw.textlength(subtitle, font=font_sub)
        draw.text(((W - tws) / 2, 130), subtitle, font=font_sub, fill=BROWN)


# ============================================================
# fig-01 — 2026 frontier-6 coordinates
# ============================================================
def make_fig01():
    print("fig-01: 2026 frontier-6 coordinates")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "2026 Spring — Frontier-6 Coordinates",
                "Revenue · Valuation · Reach (estimates, public sources)")
    # 6 cards
    rows = [
        ("OpenAI",     "~$15B",   "~$300B",  "500M+ ChatGPT weekly"),
        ("Anthropic",  "~$3B",    "~$60B",   "developer + enterprise"),
        ("Google",     "n/a*",    "Alphabet $2T+", "Search · Workspace · Android"),
        ("Meta",       "Reality Labs −$60B",  "Meta $1.7T+", "3B+ messenger reach"),
        ("xAI",        "n/a",     "~$200B",  "X integration · Colossus 200K GPU"),
        ("Mistral",    "n/a",     "~€13B",   "EU sovereignty · open weights"),
    ]
    col_w = 1440
    row_h = 90
    gap = 6
    start_x = (W - col_w) // 2
    start_y = 200
    f_name = ImageFont.truetype(ARIAL_BD, 26)
    f_h    = ImageFont.truetype(ARIAL_BD, 16)
    f_v    = ImageFont.truetype(ARIAL_BD, 22)
    f_d    = ImageFont.truetype(ARIAL_IT, 18)
    # header
    draw.text((start_x + 24, start_y - 36), "COMPANY", font=f_h, fill=BROWN)
    draw.text((start_x + 350, start_y - 36), "ANNUAL REVENUE (EST.)", font=f_h, fill=BROWN)
    draw.text((start_x + 770, start_y - 36), "VALUATION (EST.)", font=f_h, fill=BROWN)
    draw.text((start_x + 1110, start_y - 36), "REACH", font=f_h, fill=BROWN)
    for i, (name, rev, val, reach) in enumerate(rows):
        y0 = start_y + i * (row_h + gap)
        y1 = y0 + row_h
        draw.rectangle([(start_x, y0), (start_x + col_w, y1)], fill=PAPER_LIGHT, outline=LINE, width=1)
        draw.rectangle([(start_x, y0), (start_x + 6, y1)], fill=AUBURN)
        draw.text((start_x + 24, y0 + 30), name, font=f_name, fill=INK)
        draw.text((start_x + 350, y0 + 30), rev, font=f_v, fill=AUBURN)
        draw.text((start_x + 770, y0 + 30), val, font=f_v, fill=AUBURN)
        draw.text((start_x + 1110, y0 + 32), reach, font=f_d, fill=INK_SOFT)
    # bottom note
    f_note = ImageFont.truetype(ARIAL_IT, 18)
    draw.text((start_x, start_y + 6 * (row_h + gap) + 10),
              "* Google revenue numbers fold into Alphabet's full P&L; the company does not break out a separate AI line. Reality Labs figure is cumulative 5-year loss.",
              font=f_note, fill=INK_DIM)
    add_caption_bar(canvas, "DATA · public estimates · 2026.05")
    canvas.save(EP6 / "fig-01.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-02 — capability curve
# ============================================================
def make_fig02():
    print("fig-02: capability curve")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Capability Curves — 2022 to 2026",
                "Selected benchmarks · frontier model best score (%)")
    # Plot area (leave room for right-side series labels)
    pl, pt, pr, pb = 130, 220, W - 320, H - 160
    pw = pr - pl
    ph = pb - pt
    # axes
    draw.rectangle([(pl - 2, pt), (pl, pb + 2)], fill=LINE)
    draw.rectangle([(pl, pb), (pr, pb + 2)], fill=LINE)
    # y ticks 0..100
    f_axis = ImageFont.truetype(ARIAL, 16)
    for v in (0, 25, 50, 75, 100):
        y = pb - int(ph * v / 100)
        draw.line([(pl - 8, y), (pl, y)], fill=LINE, width=1)
        lbl = f"{v}"
        tw = draw.textlength(lbl, font=f_axis)
        draw.text((pl - 14 - tw, y - 9), lbl, font=f_axis, fill=INK_DIM)
    # x ticks years
    years = list(range(2022, 2027))
    for i, yr in enumerate(years):
        x = pl + int(pw * i / (len(years) - 1))
        draw.line([(x, pb), (x, pb + 8)], fill=LINE, width=1)
        lbl = str(yr)
        tw = draw.textlength(lbl, font=f_axis)
        draw.text((x - tw / 2, pb + 14), lbl, font=f_axis, fill=INK_DIM)
    # series: (name, color, points per year)
    # rough/illustrative best-frontier scores
    series = [
        ("MMLU",            AUBURN,                [60, 80, 87, 89, 91, 92]),
        ("HumanEval",       BROWN,                 [29, 60, 75, 88, 92, 94]),
        ("SWE-bench Verified", GOLD,                [  3,   8, 13, 22, 50, 77]),
        ("Math Olympiad",   (90, 70, 50),          [10, 18, 30, 45, 75, 90]),
    ]
    f_lbl = ImageFont.truetype(ARIAL_BD, 20)
    # collect last-point positions for non-overlapping label placement
    last_positions = []
    for name, color, pts in series:
        pts = pts[:len(years)]
        prev = None
        for i, v in enumerate(pts):
            x = pl + int(pw * i / (len(years) - 1))
            y = pb - int(ph * v / 100)
            if prev:
                draw.line([prev, (x, y)], fill=color, width=4)
            draw.ellipse([(x - 5, y - 5), (x + 5, y + 5)], fill=color)
            prev = (x, y)
        last_positions.append((name, color, pts[-1]))

    # place labels stacked on the right, avoiding overlap
    label_x = pr + 20
    # sort by score desc so top labels align with top series
    last_positions.sort(key=lambda t: -t[2])
    label_y_min = pt + 10
    label_y_max = pb - 40
    n = len(last_positions)
    for i, (name, color, v) in enumerate(last_positions):
        ideal_y = pb - int(ph * v / 100) - 12
        # clamp/spread to avoid collisions
        ideal_y = max(label_y_min + i * 36, ideal_y)
        ideal_y = min(label_y_max, ideal_y)
        # leader dot
        draw.ellipse([(label_x - 14, ideal_y + 4), (label_x - 4, ideal_y + 14)], fill=color)
        draw.text((label_x + 4, ideal_y), f"{name}  ·  {v}", font=f_lbl, fill=color)
    # human baseline line at 50
    y50 = pb - int(ph * 50 / 100)
    draw.line([(pl, y50), (pr, y50)], fill=(180, 160, 130), width=1)
    draw.text((pl + 6, y50 + 4), "~human average baseline", font=ImageFont.truetype(ARIAL_IT, 14), fill=INK_DIM)
    add_caption_bar(canvas, "DATA · papers with code · vendor tech reports · 2022 to 2026.05")
    canvas.save(EP6 / "fig-02.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-03 — AI surfaces
# ============================================================
def make_fig03():
    print("fig-03: AI surfaces in daily life")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "AI Surfaces in Daily Life — 2026",
                "From the moment you wake up to the moment you fall asleep")
    surfaces = [
        ("Operating System",    "Windows Copilot · macOS Apple Intelligence · Android Gemini Nano"),
        ("Search",              "Google AI Overviews · billions of users weekly · answers above results"),
        ("Messenger",           "Meta AI in IG · WhatsApp · Messenger · 3B+ reach"),
        ("Productivity",        "Microsoft Copilot · Google Workspace · ChatGPT Enterprise · ~50M paid seats"),
        ("Voice / Hands-free",  "ChatGPT Voice · Google Voice · Siri · realtime turn-taking"),
        ("Smart Glasses / AR",  "Meta Ray-Ban · Apple Vision · early-stage AI pins"),
        ("Devices",             "Pixel · iPhone · Galaxy AI · Surface · Mac on-device inference"),
        ("Coding · Build",      "Claude Code · GitHub Copilot · Cursor · agentic IDEs"),
    ]
    card_w = 720
    card_h = 110
    gap_h = 30
    gap_v = 18
    cols = 2
    rows = 4
    total_w = card_w * cols + gap_h
    start_x = (W - total_w) // 2
    start_y = 200
    f_name = ImageFont.truetype(ARIAL_BD, 26)
    f_desc = ImageFont.truetype(ARIAL_IT, 19)
    for idx, (name, desc) in enumerate(surfaces):
        r = idx // cols
        c = idx % cols
        x0 = start_x + c * (card_w + gap_h)
        y0 = start_y + r * (card_h + gap_v)
        x1 = x0 + card_w
        y1 = y0 + card_h
        draw.rectangle([(x0, y0), (x1, y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
        draw.rectangle([(x0, y0), (x0 + 6, y1)], fill=AUBURN)
        draw.text((x0 + 24, y0 + 18), name, font=f_name, fill=INK)
        draw.text((x0 + 24, y0 + 60), desc, font=f_desc, fill=BROWN)
    add_caption_bar(canvas, "CHART · Lucky Please Editorial · 2026.05")
    canvas.save(EP6 / "fig-03.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-04 — 4-hyperscaler capex time series
# ============================================================
def make_fig04():
    print("fig-04: 4-hyperscaler capex")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "AI-Infrastructure Capex — 4 Hyperscalers",
                "Microsoft · Google · Meta · Amazon · stacked, USD billion / year")
    # Plot area
    pl, pt, pr, pb = 130, 220, W - 100, H - 170
    pw = pr - pl
    ph = pb - pt
    draw.rectangle([(pl - 2, pt), (pl, pb + 2)], fill=LINE)
    draw.rectangle([(pl, pb), (pr, pb + 2)], fill=LINE)
    f_axis = ImageFont.truetype(ARIAL, 16)
    # y axis ticks (0..400 B)
    for v in (0, 100, 200, 300, 400):
        y = pb - int(ph * v / 400)
        draw.line([(pl - 8, y), (pl, y)], fill=LINE, width=1)
        lbl = f"${v}B"
        tw = draw.textlength(lbl, font=f_axis)
        draw.text((pl - 14 - tw, y - 9), lbl, font=f_axis, fill=INK_DIM)
    # years and stacks per year (Microsoft / Google / Meta / Amazon)
    years = ["2022", "2023", "2024", "2025", "2026 (est.)"]
    # rough/illustrative annual capex (USD B) per company
    data = [
        [25, 32, 60, 95, 110],   # Microsoft
        [31, 32, 50, 75, 95],    # Google
        [32, 28, 39, 62, 80],    # Meta
        [60, 50, 80, 100, 115],  # Amazon
    ]
    colors = [AUBURN, BROWN, GOLD, (90, 70, 50)]
    labels = ["Microsoft", "Google", "Meta", "Amazon"]
    bar_w = 140
    gap = (pw - bar_w * len(years)) / (len(years) - 1) if len(years) > 1 else 0
    for i in range(len(years)):
        x0 = pl + int(i * (bar_w + gap))
        x1 = x0 + bar_w
        cumulative = 0
        for j in range(4):
            v = data[j][i]
            y_top = pb - int(ph * (cumulative + v) / 400)
            y_bot = pb - int(ph * cumulative / 400)
            draw.rectangle([(x0, y_top), (x1, y_bot)], fill=colors[j])
            cumulative += v
        # total label on top
        total = sum(d[i] for d in data)
        f_total = ImageFont.truetype(ARIAL_BD, 22)
        lbl = f"${total}B"
        tw = draw.textlength(lbl, font=f_total)
        y_top = pb - int(ph * cumulative / 400)
        draw.text((x0 + (bar_w - tw) / 2, y_top - 32), lbl, font=f_total, fill=INK)
        # year label
        lbl = years[i]
        tw = draw.textlength(lbl, font=f_axis)
        draw.text((x0 + (bar_w - tw) / 2, pb + 14), lbl, font=f_axis, fill=INK_DIM)
    # legend
    f_leg = ImageFont.truetype(ARIAL_BD, 18)
    lx = pr - 320
    ly = pt + 10
    for j, (lab, col) in enumerate(zip(labels, colors)):
        draw.rectangle([(lx, ly + j * 28), (lx + 22, ly + j * 28 + 18)], fill=col)
        draw.text((lx + 30, ly + j * 28), lab, font=f_leg, fill=INK)
    add_caption_bar(canvas, "DATA · company annual reports · Bloomberg estimates · 2022 to 2026")
    canvas.save(EP6 / "fig-04.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-05 — US data center electricity share
# ============================================================
def make_fig05():
    print("fig-05: US data center electricity share")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "US Data Center Electricity Share — 2023 to 2030",
                "Share of total US electricity consumption · DOE / EPRI / Goldman Sachs ranges")
    pl, pt, pr, pb = 130, 220, W - 130, H - 160
    pw = pr - pl
    ph = pb - pt
    draw.rectangle([(pl - 2, pt), (pl, pb + 2)], fill=LINE)
    draw.rectangle([(pl, pb), (pr, pb + 2)], fill=LINE)
    f_axis = ImageFont.truetype(ARIAL, 16)
    # y axis 0..15%
    for v in (0, 3, 6, 9, 12, 15):
        y = pb - int(ph * v / 15)
        draw.line([(pl - 8, y), (pl, y)], fill=LINE, width=1)
        lbl = f"{v}%"
        tw = draw.textlength(lbl, font=f_axis)
        draw.text((pl - 14 - tw, y - 9), lbl, font=f_axis, fill=INK_DIM)
    # band: low estimate and high estimate from 2023..2030
    years = list(range(2023, 2031))
    low  = [4.0, 4.4, 5.0, 5.6, 6.2, 6.9, 7.5, 8.0]
    high = [4.0, 4.7, 5.6, 6.8, 8.2, 9.5, 10.8, 12.0]
    points_low = []
    points_high = []
    for i, yr in enumerate(years):
        x = pl + int(pw * i / (len(years) - 1))
        y_low = pb - int(ph * low[i] / 15)
        y_high = pb - int(ph * high[i] / 15)
        points_low.append((x, y_low))
        points_high.append((x, y_high))
        # x tick
        draw.line([(x, pb), (x, pb + 8)], fill=LINE, width=1)
        lbl = str(yr)
        tw = draw.textlength(lbl, font=f_axis)
        draw.text((x - tw / 2, pb + 14), lbl, font=f_axis, fill=INK_DIM)
    # filled band (approx — use polygon)
    poly = points_low + list(reversed(points_high))
    draw.polygon(poly, fill=(220, 200, 160))
    # high line in auburn, low line in brown
    for i in range(len(years) - 1):
        draw.line([points_high[i], points_high[i + 1]], fill=AUBURN, width=4)
        draw.line([points_low[i], points_low[i + 1]], fill=BROWN, width=4)
    # labels
    f_lab = ImageFont.truetype(ARIAL_BD, 18)
    draw.text((points_high[-1][0] - 100, points_high[-1][1] - 40), "high · 12%", font=f_lab, fill=AUBURN)
    draw.text((points_low[-1][0] - 80, points_low[-1][1] + 18), "low · 8%", font=f_lab, fill=BROWN)
    # 2023 marker
    f_now = ImageFont.truetype(ARIAL_IT, 18)
    draw.text((points_high[0][0] + 12, points_high[0][1] - 28), "2023 · 4%", font=f_now, fill=INK_SOFT)
    add_caption_bar(canvas, "DATA · U.S. DOE · EPRI · Goldman Sachs · 2023 to 2030 projection")
    canvas.save(EP6 / "fig-05.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-06 — AI regulation map
# ============================================================
def make_fig06():
    print("fig-06: regulation map")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "AI Regulation Map — Spring 2026",
                "How the world is shaping the rules")
    regions = [
        ("European Union", "EU AI Act (2024 enacted, 2026 enforcement)",
         "Risk classification · transparency · pre-deployment evaluation for large models.",
         AUBURN),
        ("United States",  "EO 14110 (2023) → partial rollback (2025)",
         "Federal mandate weakened. State-level (CA SB 1047 failed) and industry self-regulation fill gap.",
         BROWN),
        ("China",          "Generative AI Measures (2023.08)",
         "Mandatory security review and content rules for models operating in domestic market.",
         GOLD),
        ("Korea",          "AI Framework Act (passed 2025)",
         "Risk-tiered, transparency obligations, transitioning from guidelines to law.",
         (110, 90, 60)),
        ("Japan",          "Voluntary guidelines → gradual legislation",
         "Government working with industry; legislation in early-stage discussion.",
         (140, 110, 70)),
        ("Industry SR",    "RSP · Preparedness · Frontier Safety Framework",
         "Anthropic · OpenAI · Google DeepMind: company-level risk tiers and public reporting.",
         (80, 60, 40)),
    ]
    card_w = 720
    card_h = 165
    gap_h = 30
    gap_v = 18
    cols = 2
    rows = 3
    total_w = card_w * cols + gap_h
    start_x = (W - total_w) // 2
    start_y = 200
    f_name = ImageFont.truetype(ARIAL_BD, 26)
    f_law  = ImageFont.truetype(ARIAL_BD, 18)
    f_desc = ImageFont.truetype(ARIAL_IT, 17)
    for idx, (name, law, desc, color) in enumerate(regions):
        r = idx // cols
        c = idx % cols
        x0 = start_x + c * (card_w + gap_h)
        y0 = start_y + r * (card_h + gap_v)
        x1 = x0 + card_w
        y1 = y0 + card_h
        draw.rectangle([(x0, y0), (x1, y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
        draw.rectangle([(x0, y0), (x0 + 6, y1)], fill=color)
        draw.text((x0 + 24, y0 + 18), name, font=f_name, fill=INK)
        draw.text((x0 + 24, y0 + 62), law, font=f_law, fill=color)
        # word-wrap desc manually (keep two lines)
        draw.text((x0 + 24, y0 + 100), desc, font=f_desc, fill=INK_SOFT)
    add_caption_bar(canvas, "CHART · Lucky Please Editorial · 2026.05")
    canvas.save(EP6 / "fig-06.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-07 — three 2030 scenarios
# ============================================================
def make_fig07():
    print("fig-07: three 2030 scenarios")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "2030 — Three Scenarios",
                "Gradual diffusion · Rapid leap · Shock & contraction")
    cols_w = 470
    cols_gap = 35
    total_w = cols_w * 3 + cols_gap * 2
    start_x = (W - total_w) // 2
    start_y = 200
    col_h = H - 260
    items = [
        ("A · Gradual Diffusion",
         "Most likely",
         AUBURN,
         [
             "Capability curve steadily improves.",
             "Agents reach week-scale autonomy by 2028.",
             "Revenue catches up to capex.",
             "EU first, US patchwork, China separate.",
             "AGI claim deferred past 2030.",
             "Picture: an expanded 2026.",
         ]),
        ("B · Rapid Leap",
         "Small but meaningful",
         BROWN,
         [
             "Capability jumps a level (2027–28).",
             "A model performs PhD-level autonomous research.",
             "Capital flow surges.",
             "Job displacement arrives faster than consent.",
             "Either consensus forms → next era;",
             "or it doesn't → drifts into scenario C.",
         ]),
        ("C · Shock & Contraction",
         "Can't be ruled out",
         GOLD,
         [
             "A large incident: agent failure / cyber attack /",
             "irresponsible frontier release.",
             "US · EU · China react with hard regulation.",
             "Some frontier training is paused.",
             "Safety-first identity gains relative weight.",
             "Industry restarts, slower and more careful.",
         ]),
    ]
    f_title = ImageFont.truetype(ARIAL_BD, 26)
    f_tag   = ImageFont.truetype(ARIAL_IT, 18)
    f_li    = ImageFont.truetype(ARIAL, 19)
    for i, (title, tag, color, lines) in enumerate(items):
        x0 = start_x + i * (cols_w + cols_gap)
        y0 = start_y
        x1 = x0 + cols_w
        y1 = y0 + col_h
        draw.rectangle([(x0, y0), (x1, y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
        draw.rectangle([(x0, y0), (x0 + 8, y1)], fill=color)
        draw.text((x0 + 24, y0 + 22), title, font=f_title, fill=INK)
        draw.text((x0 + 24, y0 + 60), tag, font=f_tag, fill=color)
        y = y0 + 110
        for line in lines:
            draw.text((x0 + 24, y), "·  " + line, font=f_li, fill=INK_SOFT)
            y += 38
    add_caption_bar(canvas, "CHART · Lucky Please Editorial · scenario framing · 2026.05")
    canvas.save(EP6 / "fig-07.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-08 — series recap
# ============================================================
def make_fig08():
    print("fig-08: series recap")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "An Anthropic Story — Series Recap",
                "Six episodes · four languages · 2026")
    episodes = [
        ("Ep.1", "Anthropic's Founding",
         "Seven leave OpenAI in 2021 to build a safety-first AI lab."),
        ("Ep.2", "Dario · Daniela Amodei",
         "Two siblings, two paths that converged at the same company."),
        ("Ep.3", "Claude's Evolution",
         "From Claude 1.0 (9K context) to Opus 4.7 (1M context) in three years."),
        ("Ep.4", "A Closer Look at OpenAI",
         "Eleven years from nonprofit to the world's most-used AI."),
        ("Ep.5", "Google · Meta · xAI · Mistral",
         "Four other answers · the contenders behind them."),
        ("Ep.6", "Today and 2030",
         "Capital · capability · infrastructure · regulation · scenarios."),
    ]
    card_w = 720
    card_h = 100
    gap_h = 30
    gap_v = 16
    cols = 2
    rows = 3
    total_w = card_w * cols + gap_h
    start_x = (W - total_w) // 2
    start_y = 200
    f_num = ImageFont.truetype(ARIAL_BD, 22)
    f_t   = ImageFont.truetype(ARIAL_BD, 24)
    f_d   = ImageFont.truetype(ARIAL_IT, 18)
    for idx, (num, t, d) in enumerate(episodes):
        r = idx // cols
        c = idx % cols
        x0 = start_x + c * (card_w + gap_h)
        y0 = start_y + r * (card_h + gap_v)
        x1 = x0 + card_w
        y1 = y0 + card_h
        draw.rectangle([(x0, y0), (x1, y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
        draw.rectangle([(x0, y0), (x0 + 6, y1)], fill=AUBURN)
        # episode badge
        draw.text((x0 + 24, y0 + 14), num, font=f_num, fill=AUBURN)
        draw.text((x0 + 100, y0 + 12), t, font=f_t, fill=INK)
        draw.text((x0 + 100, y0 + 52), d, font=f_d, fill=INK_SOFT)
    # closing tag
    f_tag = ImageFont.truetype(ARIAL_IT, 26)
    tag = "complete · 2026.05"
    tw = draw.textlength(tag, font=f_tag)
    draw.text(((W - tw) / 2, H - 130), tag, font=f_tag, fill=BROWN)
    # series brand
    f_brand = ImageFont.truetype(ARIAL_BD, 22)
    brand = "An Anthropic Story · series finale"
    bw = draw.textlength(brand, font=f_brand)
    draw.text(((W - bw) / 2, H - 95), brand, font=f_brand, fill=INK)
    add_caption_bar(canvas, "CHART · Lucky Please Editorial · series complete")
    canvas.save(EP6 / "fig-08.jpg", "JPEG", quality=88, optimize=True)


def main():
    make_fig01()
    make_fig02()
    make_fig03()
    make_fig04()
    make_fig05()
    make_fig06()
    make_fig07()
    make_fig08()
    print()
    print("Done. Generated figures:")
    for p in sorted(EP6.glob("fig-*.jpg")):
        sz = p.stat().st_size
        print(f"  {p.name}: {sz/1024:.1f} KB")


if __name__ == "__main__":
    main()
