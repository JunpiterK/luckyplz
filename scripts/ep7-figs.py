"""
Ep.7 figure generator (series finale, all hand-drawn).

- fig-01: Anthropic 2026 spring coordinates (Q1/Q2 revenue · valuation · customers)
- fig-02: ARR curve $87M → $30B (Jan 2024 → Apr 2026)
- fig-03: PBC structure vs OpenAI nonprofit+for-profit dual structure
- fig-04: IPO scenario card (timeline · underwriters · valuation history)
- fig-05: Claude 2026 lineup (Pro · Max · API · Code · Artifacts · 1M context)
- fig-06: Constitutional AI + RSP ASL-1..4 four-tier safety framework
- fig-07: Anthropic's seat across three 2030 scenarios
- fig-08: Series Ep.1 ~ Ep.7 full recap
"""
import sys
import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8")

EP7 = Path(r"C:\code\python\luckyplz\.claude\worktrees\inspiring-cerf-fac44c\public\assets\anthropic-series\ep7")

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
# fig-01 — Anthropic spring 2026 coordinates
# ============================================================
def make_fig01():
    print("fig-01: Anthropic spring 2026 coordinates")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Anthropic — Spring 2026 Coordinates",
                "Q1 revenue · Q2 outlook · valuation · enterprise reach")
    # 6 big stat cards
    stats = [
        ("$4.8B",   "Q1 2026 revenue"),
        ("$10.9B",  "Q2 2026 expected"),
        ("+130%",   "QoQ growth"),
        ("$559M",   "Q2 expected operating profit"),
        ("$900B",   "round-under-review valuation"),
        ("1,000+",  "enterprise customers · $1M+/year"),
    ]
    card_w = 450
    card_h = 180
    gap_h = 30
    gap_v = 30
    cols = 3
    rows = 2
    total_w = card_w * cols + gap_h * (cols - 1)
    start_x = (W - total_w) // 2
    start_y = 200
    f_val = ImageFont.truetype(ARIAL_BD, 64)
    f_lbl = ImageFont.truetype(ARIAL_IT, 22)
    for i, (val, lbl) in enumerate(stats):
        r = i // cols
        c = i % cols
        x0 = start_x + c * (card_w + gap_h)
        y0 = start_y + r * (card_h + gap_v)
        x1 = x0 + card_w
        y1 = y0 + card_h
        draw.rectangle([(x0, y0), (x1, y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
        draw.rectangle([(x0, y0), (x0 + 6, y1)], fill=AUBURN)
        # value centered
        vw = draw.textlength(val, font=f_val)
        draw.text((x0 + (card_w - vw) / 2, y0 + 30), val, font=f_val, fill=AUBURN)
        # label centered
        lw = draw.textlength(lbl, font=f_lbl)
        draw.text((x0 + (card_w - lw) / 2, y0 + 120), lbl, font=f_lbl, fill=INK_SOFT)
    add_caption_bar(canvas, "DATA · Bloomberg · CNBC · The Information · 2026.04 ~ 2026.05")
    canvas.save(EP7 / "fig-01.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-02 — ARR curve
# ============================================================
def make_fig02():
    print("fig-02: ARR curve")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Anthropic ARR — 80× in 18 Months",
                "Run rate curve, Jan 2024 → Apr 2026 (USD billions, log scale)")
    # log-scale plot
    pl, pt, pr, pb = 130, 230, W - 130, H - 170
    pw = pr - pl
    ph = pb - pt
    draw.rectangle([(pl - 2, pt), (pl, pb + 2)], fill=LINE)
    draw.rectangle([(pl, pb), (pr, pb + 2)], fill=LINE)
    f_axis = ImageFont.truetype(ARIAL, 16)
    # y log range: 0.05 to 50 (B)
    log_min = math.log10(0.05)
    log_max = math.log10(60)
    ticks_y = [0.05, 0.1, 0.5, 1, 5, 10, 50]
    ticks_lbl = ["$50M", "$100M", "$500M", "$1B", "$5B", "$10B", "$50B"]
    for v, lbl in zip(ticks_y, ticks_lbl):
        y = pb - int(ph * (math.log10(v) - log_min) / (log_max - log_min))
        draw.line([(pl - 8, y), (pl, y)], fill=LINE, width=1)
        tw = draw.textlength(lbl, font=f_axis)
        draw.text((pl - 14 - tw, y - 9), lbl, font=f_axis, fill=INK_DIM)
    # data points (month_label, USD B)
    pts = [
        ("2024.01",  0.087),
        ("2024.12",  1.0),
        ("2025.12",  9.0),
        ("2026.02",  14.0),
        ("2026.03",  19.0),
        ("2026.04",  30.0),
        ("2026.06\n(target)",  50.0),
    ]
    points = []
    f_lbl = ImageFont.truetype(ARIAL, 15)
    f_v = ImageFont.truetype(ARIAL_BD, 18)
    for i, (lbl, v) in enumerate(pts):
        x = pl + int(pw * i / (len(pts) - 1))
        y = pb - int(ph * (math.log10(v) - log_min) / (log_max - log_min))
        points.append((x, y))
        # x-axis label
        for j, line in enumerate(lbl.split("\n")):
            tw = draw.textlength(line, font=f_lbl)
            draw.text((x - tw / 2, pb + 14 + j * 18), line, font=f_lbl, fill=INK_DIM)
    # connect points
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=AUBURN, width=4)
    # draw dots and value above each point
    for i, (lbl, v) in enumerate(pts):
        x, y = points[i]
        draw.ellipse([(x - 7, y - 7), (x + 7, y + 7)], fill=AUBURN)
        vlbl = f"${v:.1f}B" if v >= 1 else f"${int(v*1000)}M"
        vw = draw.textlength(vlbl, font=f_v)
        draw.text((x - vw / 2, y - 32), vlbl, font=f_v, fill=INK)
    add_caption_bar(canvas, "DATA · CNBC · Bloomberg · VentureBeat · 2024.01 ~ 2026.05")
    canvas.save(EP7 / "fig-02.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-03 — PBC vs OpenAI dual structure
# ============================================================
def make_fig03():
    print("fig-03: PBC vs OpenAI structure")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Governance — PBC vs Dual Structure",
                "Anthropic's single-entity PBC, alongside OpenAI's nonprofit-over-for-profit")
    # Two side-by-side panels
    col_w = 700
    gap = 60
    total_w = col_w * 2 + gap
    start_x = (W - total_w) // 2
    start_y = 200
    col_h = H - 280
    # Anthropic panel
    a_x0 = start_x
    a_y0 = start_y
    a_x1 = a_x0 + col_w
    a_y1 = a_y0 + col_h
    draw.rectangle([(a_x0, a_y0), (a_x1, a_y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
    draw.rectangle([(a_x0, a_y0), (a_x0 + 8, a_y1)], fill=AUBURN)
    f_h = ImageFont.truetype(ARIAL_BD, 30)
    f_t = ImageFont.truetype(ARIAL_BD, 20)
    f_d = ImageFont.truetype(ARIAL_IT, 18)
    draw.text((a_x0 + 24, a_y0 + 24), "Anthropic", font=f_h, fill=INK)
    draw.text((a_x0 + 24, a_y0 + 68), "Public Benefit Corporation (PBC)", font=f_t, fill=AUBURN)
    # Single-entity diagram
    box_x = a_x0 + 100
    box_y = a_y0 + 130
    box_w = col_w - 200
    box_h = 220
    draw.rectangle([(box_x, box_y), (box_x + box_w, box_y + box_h)], fill=PAPER, outline=AUBURN, width=3)
    f_box_h = ImageFont.truetype(ARIAL_BD, 24)
    draw.text((box_x + 20, box_y + 16), "Anthropic, PBC", font=f_box_h, fill=INK)
    draw.text((box_x + 20, box_y + 56), "Delaware Public Benefit Corp.", font=f_d, fill=INK_SOFT)
    f_btxt = ImageFont.truetype(ARIAL, 17)
    txt_lines = [
        "·  Shareholders + public-benefit mission",
        "·  Charter: \"long-term safety of AI\"",
        "·  Single board, single governance",
        "·  IPO-ready structure",
    ]
    for i, line in enumerate(txt_lines):
        draw.text((box_x + 20, box_y + 92 + i * 28), line, font=f_btxt, fill=INK)
    # Notes
    note_lines = [
        "→ One entity holding both profit and mission.",
        "→ The 2023 OpenAI crisis cannot occur here.",
    ]
    for i, line in enumerate(note_lines):
        draw.text((a_x0 + 24, box_y + box_h + 30 + i * 30), line, font=f_d, fill=BROWN)

    # OpenAI panel
    o_x0 = start_x + col_w + gap
    o_y0 = start_y
    o_x1 = o_x0 + col_w
    o_y1 = o_y0 + col_h
    draw.rectangle([(o_x0, o_y0), (o_x1, o_y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
    draw.rectangle([(o_x0, o_y0), (o_x0 + 8, o_y1)], fill=BROWN)
    draw.text((o_x0 + 24, o_y0 + 24), "OpenAI", font=f_h, fill=INK)
    draw.text((o_x0 + 24, o_y0 + 68), "Nonprofit parent + for-profit subsidiary", font=f_t, fill=BROWN)
    # Dual diagram — parent box
    p_x = o_x0 + 100
    p_y = o_y0 + 130
    p_w = col_w - 200
    p_h = 90
    draw.rectangle([(p_x, p_y), (p_x + p_w, p_y + p_h)], fill=PAPER, outline=BROWN, width=3)
    draw.text((p_x + 20, p_y + 14), "OpenAI Inc. (Nonprofit Parent)", font=f_box_h, fill=INK)
    draw.text((p_x + 20, p_y + 52), "Controls subsidiary · mission-only board", font=f_d, fill=INK_SOFT)
    # Arrow
    arr_x = p_x + p_w // 2
    arr_y = p_y + p_h
    draw.line([(arr_x, arr_y), (arr_x, arr_y + 28)], fill=BROWN, width=4)
    draw.polygon([(arr_x - 8, arr_y + 28), (arr_x + 8, arr_y + 28), (arr_x, arr_y + 42)], fill=BROWN)
    # Child box
    c_x = p_x
    c_y = arr_y + 50
    c_w = p_w
    c_h = 90
    draw.rectangle([(c_x, c_y), (c_x + c_w, c_y + c_h)], fill=PAPER, outline=BROWN, width=3)
    draw.text((c_x + 20, c_y + 14), "OpenAI LP / OpenAI Global (For-Profit)", font=f_box_h, fill=INK)
    draw.text((c_x + 20, c_y + 52), "Operates products · receives capital · pays employees", font=f_d, fill=INK_SOFT)
    # Notes
    onote = [
        "→ Two entities, two priorities.",
        "→ The 2023 Nov board crisis exposed this seam.",
    ]
    for i, line in enumerate(onote):
        draw.text((o_x0 + 24, c_y + c_h + 30 + i * 30), line, font=f_d, fill=BROWN)

    add_caption_bar(canvas, "CHART · Lucky Please Editorial · 2026.05")
    canvas.save(EP7 / "fig-03.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-04 — IPO scenario card
# ============================================================
def make_fig04():
    print("fig-04: IPO scenario")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Anthropic IPO — Reported 2026 Outlook",
                "Timeline · underwriters · valuation history")
    # Left panel: valuation history line
    pl, pt, pr, pb = 120, 220, 900, H - 200
    pw = pr - pl
    ph = pb - pt
    draw.rectangle([(pl - 2, pt), (pl, pb + 2)], fill=LINE)
    draw.rectangle([(pl, pb), (pr, pb + 2)], fill=LINE)
    f_axis = ImageFont.truetype(ARIAL, 16)
    f_lbl = ImageFont.truetype(ARIAL_BD, 18)
    rounds = [
        ("2023 · Series C",   "$4B",     4),
        ("2024 · Series E",  "$18B",   18),
        ("2025 · Round",     "$60B",   60),
        ("2026.03 · Round", "$183B",  183),
        ("2026.05 · Under review", "$900B", 900),
    ]
    val_max = 1000
    for i, (lbl, vtxt, v) in enumerate(rounds):
        x = pl + int(pw * i / (len(rounds) - 1))
        y = pb - int(ph * v / val_max)
        # vertical bar
        draw.rectangle([(x - 14, y), (x + 14, pb)], fill=AUBURN if i == len(rounds) - 1 else BROWN)
        # value on top
        vw = draw.textlength(vtxt, font=f_lbl)
        draw.text((x - vw / 2, y - 32), vtxt, font=f_lbl, fill=INK)
        # label below — two lines
        f_xl = ImageFont.truetype(ARIAL, 14)
        for j, line in enumerate(lbl.split("·")):
            line = line.strip()
            tw = draw.textlength(line, font=f_xl)
            draw.text((x - tw / 2, pb + 14 + j * 18), line, font=f_xl, fill=INK_DIM)
    # y axis labels
    for v, lbl in [(100, "$100B"), (300, "$300B"), (600, "$600B"), (900, "$900B")]:
        y = pb - int(ph * v / val_max)
        draw.line([(pl - 8, y), (pl, y)], fill=LINE, width=1)
        tw = draw.textlength(lbl, font=f_axis)
        draw.text((pl - 14 - tw, y - 9), lbl, font=f_axis, fill=INK_DIM)

    # Right panel — IPO info card
    card_x = 960
    card_y = 220
    card_w = W - card_x - 80
    card_h = H - 380
    draw.rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], fill=PAPER_LIGHT, outline=LINE, width=2)
    draw.rectangle([(card_x, card_y), (card_x + 6, card_y + card_h)], fill=AUBURN)
    f_hdr = ImageFont.truetype(ARIAL_BD, 22)
    draw.text((card_x + 24, card_y + 22), "IPO OUTLOOK", font=f_hdr, fill=BROWN)
    f_k = ImageFont.truetype(ARIAL_BD, 21)
    f_v = ImageFont.truetype(ARIAL_IT, 18)
    rows = [
        ("Target timing",   "around October 2026"),
        ("Underwriters",    "Goldman Sachs · JPMorgan · Morgan Stanley"),
        ("Pre-IPO round",   "$900B (May 2026 review)"),
        ("Significance",    "first frontier-AI public listing"),
        ("Note",            "non-GAAP estimates · public filings TBD"),
    ]
    y = card_y + 70
    for k, v in rows:
        draw.text((card_x + 24, y), k, font=f_k, fill=INK)
        # word-wrap value
        max_w = card_w - 50
        words = v.split(" ")
        line = ""
        wy = y + 32
        for w in words:
            test = line + (" " if line else "") + w
            if draw.textlength(test, font=f_v) > max_w:
                draw.text((card_x + 24, wy), line, font=f_v, fill=INK_SOFT)
                wy += 26
                line = w
            else:
                line = test
        if line:
            draw.text((card_x + 24, wy), line, font=f_v, fill=INK_SOFT)
        y = wy + 44

    add_caption_bar(canvas, "DATA · Bloomberg · CNBC · TechCrunch · 2026.04 ~ 2026.05")
    canvas.save(EP7 / "fig-04.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-05 — Claude 2026 lineup
# ============================================================
def make_fig05():
    print("fig-05: Claude 2026 lineup")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Claude — 2026 Spring Lineup",
                "Pro · Max · API · Code · Artifacts · 1M context · Extended Thinking")
    cards = [
        ("Claude Pro",     "consumer subscription",     "Sonnet/Opus · ~$20/mo"),
        ("Claude Max",     "heavy-use tier",            "Opus 4.7 · ~$100~$200/mo"),
        ("API",            "developer platform",        "pay-per-token · enterprise"),
        ("Claude Code",    "terminal-integrated",       "hooks · plan mode · sub-agents"),
        ("Artifacts",      "side-panel workspace",      "live code · docs · charts"),
        ("Computer Use",   "screen + mouse / keyboard", "browser · spreadsheet · email"),
        ("1M Context",     "all tiers",                 "whole codebase · whole book"),
        ("Extended Thinking", "all tiers",              "deeper reasoning when on"),
    ]
    card_w = 360
    card_h = 140
    gap_h = 20
    gap_v = 16
    cols = 4
    rows = 2
    total_w = card_w * cols + gap_h * (cols - 1)
    start_x = (W - total_w) // 2
    start_y = 210
    f_name = ImageFont.truetype(ARIAL_BD, 22)
    f_desc = ImageFont.truetype(ARIAL_BD, 16)
    f_meta = ImageFont.truetype(ARIAL_IT, 15)
    for idx, (name, desc, meta) in enumerate(cards):
        r = idx // cols
        c = idx % cols
        x0 = start_x + c * (card_w + gap_h)
        y0 = start_y + r * (card_h + gap_v)
        x1 = x0 + card_w
        y1 = y0 + card_h
        draw.rectangle([(x0, y0), (x1, y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
        draw.rectangle([(x0, y0), (x0 + 6, y1)], fill=AUBURN)
        draw.text((x0 + 18, y0 + 14), name, font=f_name, fill=INK)
        draw.text((x0 + 18, y0 + 50), desc, font=f_desc, fill=BROWN)
        draw.text((x0 + 18, y0 + 82), meta, font=f_meta, fill=INK_DIM)
    # closing line
    f_close = ImageFont.truetype(ARIAL_IT, 22)
    closing = "All tiers run on Opus 4.7 (frontier) or Sonnet 4.5 (default) as of 2026.05"
    tw = draw.textlength(closing, font=f_close)
    draw.text(((W - tw) / 2, H - 110), closing, font=f_close, fill=AUBURN)
    add_caption_bar(canvas, "CHART · Lucky Please Editorial · 2026.05")
    canvas.save(EP7 / "fig-05.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-06 — Constitutional AI + RSP
# ============================================================
def make_fig06():
    print("fig-06: Constitutional AI + RSP")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Constitutional AI + RSP — the Two Backbones",
                "Anthropic's identity, since 2022")
    # Left column: Constitutional AI
    lc_x = 120
    lc_y = 220
    lc_w = 600
    lc_h = H - 350
    draw.rectangle([(lc_x, lc_y), (lc_x + lc_w, lc_y + lc_h)], fill=PAPER_LIGHT, outline=LINE, width=2)
    draw.rectangle([(lc_x, lc_y), (lc_x + 6, lc_y + lc_h)], fill=BROWN)
    f_h = ImageFont.truetype(ARIAL_BD, 26)
    f_t = ImageFont.truetype(ARIAL_IT, 18)
    f_b = ImageFont.truetype(ARIAL, 17)
    draw.text((lc_x + 24, lc_y + 22), "Constitutional AI", font=f_h, fill=INK)
    draw.text((lc_x + 24, lc_y + 60), "Bai et al., Anthropic, 2022", font=f_t, fill=BROWN)
    bullets = [
        "Model evaluates its own answers",
        "against a written set of principles.",
        "",
        "Reduces the need for large amounts",
        "of human-labeled data.",
        "",
        "Forms the training-time foundation",
        "of every Claude model since 2023.",
    ]
    for i, line in enumerate(bullets):
        draw.text((lc_x + 24, lc_y + 110 + i * 30), line, font=f_b, fill=INK)

    # Right column: RSP — 4-tier
    rc_x = 760
    rc_y = 220
    rc_w = 720
    rc_h = H - 350
    draw.rectangle([(rc_x, rc_y), (rc_x + rc_w, rc_y + rc_h)], fill=PAPER_LIGHT, outline=LINE, width=2)
    draw.rectangle([(rc_x, rc_y), (rc_x + 6, rc_y + rc_h)], fill=AUBURN)
    draw.text((rc_x + 24, rc_y + 22), "Responsible Scaling Policy", font=f_h, fill=INK)
    draw.text((rc_x + 24, rc_y + 60), "Anthropic, 2023 (v1) → 2024.10 (v2)", font=f_t, fill=BROWN)
    # 4 tiers as stacked bars
    tier_y = rc_y + 110
    tier_h = 80
    tier_gap = 8
    tiers = [
        ("ASL-1", "General-purpose tools", (200, 175, 130)),
        ("ASL-2", "Today's frontier models (Claude Opus 4.7 et al.)", (175, 145, 100)),
        ("ASL-3", "Misuse could cause large-scale harm", BROWN),
        ("ASL-4", "Beyond ASL-3 · most stringent controls", AUBURN),
    ]
    f_tn = ImageFont.truetype(ARIAL_BD, 24)
    f_td = ImageFont.truetype(ARIAL_IT, 16)
    for i, (name, desc, color) in enumerate(tiers):
        ty0 = tier_y + i * (tier_h + tier_gap)
        ty1 = ty0 + tier_h
        draw.rectangle([(rc_x + 24, ty0), (rc_x + rc_w - 24, ty1)], fill=color)
        draw.text((rc_x + 40, ty0 + 12), name, font=f_tn, fill=(255, 248, 230))
        draw.text((rc_x + 40, ty0 + 46), desc, font=f_td, fill=(255, 248, 230))

    add_caption_bar(canvas, "SOURCES · Anthropic, Constitutional AI (2022) · RSP v2 (2024.10)")
    canvas.save(EP7 / "fig-06.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-07 — Anthropic's seat across three scenarios
# ============================================================
def make_fig07():
    print("fig-07: Anthropic seat in three scenarios")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Anthropic in Each 2030 Scenario",
                "Standing across gradual diffusion · rapid leap · shock & contraction")
    items = [
        ("A · Gradual Diffusion",
         "Most likely",
         AUBURN,
         [
             "Revenue catches up with capex.",
             "Enterprise-trust position holds firm.",
             "Steady listed-company growth post-IPO.",
             "Est. 2030 revenue: ~$150B – $300B.",
             "Clear seat among the top 3.",
         ]),
        ("B · Rapid Leap",
         "Small but meaningful",
         BROWN,
         [
             "RSP becomes near-industry standard.",
             "Anthropic carries weight in regulation.",
             "Hub for safety-conscious capital.",
             "If consensus forms → next era leader.",
             "If not → drifts toward scenario C.",
         ]),
        ("C · Shock & Contraction",
         "Cannot be ruled out",
         GOLD,
         [
             "Strong regulatory backlash.",
             "Safety-first identity gains weight.",
             "PBC structure is a relative strength.",
             "Market share less central than influence.",
             "Industry restarts more carefully.",
         ]),
    ]
    cols_w = 470
    cols_gap = 35
    total_w = cols_w * 3 + cols_gap * 2
    start_x = (W - total_w) // 2
    start_y = 210
    col_h = H - 290
    f_title = ImageFont.truetype(ARIAL_BD, 24)
    f_tag   = ImageFont.truetype(ARIAL_IT, 18)
    f_li    = ImageFont.truetype(ARIAL, 18)
    for i, (title, tag, color, lines) in enumerate(items):
        x0 = start_x + i * (cols_w + cols_gap)
        y0 = start_y
        x1 = x0 + cols_w
        y1 = y0 + col_h
        draw.rectangle([(x0, y0), (x1, y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
        draw.rectangle([(x0, y0), (x0 + 8, y1)], fill=color)
        draw.text((x0 + 24, y0 + 22), title, font=f_title, fill=INK)
        draw.text((x0 + 24, y0 + 58), tag, font=f_tag, fill=color)
        y = y0 + 108
        for line in lines:
            draw.text((x0 + 24, y), "·  " + line, font=f_li, fill=INK_SOFT)
            y += 40
    add_caption_bar(canvas, "CHART · Lucky Please Editorial · 2026.05")
    canvas.save(EP7 / "fig-07.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-08 — Series Ep.1 ~ Ep.7 full recap
# ============================================================
def make_fig08():
    print("fig-08: full series recap Ep.1 ~ Ep.7")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "An Anthropic Story — Series Recap",
                "Seven episodes · four languages · 2026")
    episodes = [
        ("Ep.1", "Anthropic's Founding",
         "Seven leave OpenAI in 2021 to build a safety-first AI lab."),
        ("Ep.2", "Dario · Daniela Amodei",
         "Two siblings on two paths, converging at the same desk."),
        ("Ep.3", "Claude's Evolution",
         "From Claude 1.0 (9K context) to Opus 4.7 (1M context)."),
        ("Ep.4", "A Closer Look at OpenAI",
         "Eleven years from nonprofit to the world's most-used AI."),
        ("Ep.5", "Google · Meta · xAI · Mistral",
         "Four other seats, and the contenders behind them."),
        ("Ep.6", "Today and the 2030 Outlook",
         "Capital, capability, infrastructure, regulation, scenarios."),
        ("Ep.7", "Anthropic Today",
         "Profitability · IPO · the heavy user's seat (finale)."),
    ]
    card_w = 720
    card_h = 88
    gap_h = 30
    gap_v = 12
    cols = 2
    total_w = card_w * cols + gap_h
    start_x = (W - total_w) // 2
    start_y = 190
    f_num = ImageFont.truetype(ARIAL_BD, 22)
    f_t   = ImageFont.truetype(ARIAL_BD, 22)
    f_d   = ImageFont.truetype(ARIAL_IT, 17)
    # 7 episodes — 4 rows × 2 cols, last row has only one item (Ep.7) centered
    for idx, (num, t, d) in enumerate(episodes):
        if idx < 6:
            r = idx // cols
            c = idx % cols
            x0 = start_x + c * (card_w + gap_h)
        else:
            # Ep.7 centered
            r = 3
            x0 = (W - card_w) // 2
        y0 = start_y + r * (card_h + gap_v)
        x1 = x0 + card_w
        y1 = y0 + card_h
        # Ep.7 highlighted
        bg = PAPER_LIGHT if idx < 6 else (250, 235, 200)
        accent = AUBURN if idx < 6 else AUBURN
        draw.rectangle([(x0, y0), (x1, y1)], fill=bg, outline=LINE, width=2)
        draw.rectangle([(x0, y0), (x0 + 6, y1)], fill=accent)
        draw.text((x0 + 24, y0 + 14), num, font=f_num, fill=accent)
        draw.text((x0 + 100, y0 + 12), t, font=f_t, fill=INK)
        draw.text((x0 + 100, y0 + 48), d, font=f_d, fill=INK_SOFT)
    # closing tag
    f_tag = ImageFont.truetype(ARIAL_IT, 26)
    tag = "series complete · 2026.05.26"
    tw = draw.textlength(tag, font=f_tag)
    draw.text(((W - tw) / 2, H - 115), tag, font=f_tag, fill=BROWN)
    f_brand = ImageFont.truetype(ARIAL_BD, 22)
    brand = "An Anthropic Story · series finale (Ep.7)"
    bw = draw.textlength(brand, font=f_brand)
    draw.text(((W - bw) / 2, H - 82), brand, font=f_brand, fill=INK)
    add_caption_bar(canvas, "CHART · Lucky Please Editorial · series complete")
    canvas.save(EP7 / "fig-08.jpg", "JPEG", quality=88, optimize=True)


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
    for p in sorted(EP7.glob("fig-*.jpg")):
        sz = p.stat().st_size
        print(f"  {p.name}: {sz/1024:.1f} KB")


if __name__ == "__main__":
    main()
