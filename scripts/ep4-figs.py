"""
Ep.4 figure generator/composer.
- fig-01: 3-way collage (Altman + Sutskever + Brockman)
- fig-02: GPT-1/2/3 parameter scaling bar chart (PIL drawn)
- fig-03: 2-way collage (Altman + Nadella)
- fig-05: GPT-4 benchmark figure (resize, convert to JPG, add white margin if needed)
- fig-06: Pioneer Building exterior (resize)
- fig-08: 2026 OpenAI lineup chart (PIL drawn)
"""
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Force UTF-8 on Windows
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8")

EP4 = Path(r"C:\code\python\luckyplz\.claude\worktrees\inspiring-cerf-fac44c\public\assets\anthropic-series\ep4")

# Beige book palette (matches the series CSS)
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
TIMES    = r"C:\Windows\Fonts\times.ttf"
TIMES_BD = r"C:\Windows\Fonts\timesbd.ttf"
TIMES_IT = r"C:\Windows\Fonts\timesi.ttf"
CGM_BD   = r"C:\Windows\Fonts\timesbd.ttf"  # Cormorant Garamond이 없으면 Times Bold 로 대체

# Target output dimensions (1600x900 → 16:9 widescreen, looks good on phone & desktop)
W, H = 1600, 900


def square_crop_center(im, size):
    """Crop center square then resize to size×size."""
    w, h = im.size
    s = min(w, h)
    left = (w - s) // 2
    top = (h - s) // 2
    im = im.crop((left, top, left + s, top + s))
    return im.resize((size, size), Image.LANCZOS)


def make_paper_canvas(w=W, h=H):
    return Image.new("RGB", (w, h), PAPER)


def add_caption_bar(canvas, label_text):
    """Add a small monospace caption bar at the bottom-left."""
    draw = ImageDraw.Draw(canvas)
    font_label = ImageFont.truetype(ARIAL, 22)
    draw.text((40, H - 50), label_text, font=font_label, fill=INK_DIM)


# ============================================================
# fig-01 — 2-way founder portraits (Altman + Brockman)
#   + a roster panel listing the 11 co-founders by name
# ============================================================
def make_fig01():
    print("Building fig-01: Altman + Brockman portraits with founder roster")
    altman = Image.open(EP4 / "sam-altman-ted.jpg").convert("RGB")
    brockman = Image.open(EP4 / "greg-brockman.jpg").convert("RGB")

    panel_w = 480
    a_im = square_crop_center(altman, panel_w)
    b_im = square_crop_center(brockman, panel_w)

    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)

    # Title
    font_title = ImageFont.truetype(ARIAL_BD, 36)
    title = "OpenAI — Founded December 2015"
    tw = draw.textlength(title, font=font_title)
    draw.text(((W - tw) / 2, 36), title, font=font_title, fill=INK)
    draw.rectangle([(W // 2 - 30, 90), (W // 2 + 30, 92)], fill=AUBURN)

    # Layout: two photos on left, roster panel on right
    margin_y = 140
    gap = 20
    photos_x = 60
    canvas.paste(a_im, (photos_x, margin_y))
    canvas.paste(b_im, (photos_x + panel_w + gap, margin_y))

    # Names below photos
    font_name = ImageFont.truetype(ARIAL_BD, 28)
    font_role = ImageFont.truetype(ARIAL_IT, 22)
    name_y = margin_y + panel_w + 18
    for i, (n, r) in enumerate([
        ("Sam Altman", "CEO (2019–)"),
        ("Greg Brockman", "President · CTO"),
    ]):
        x = photos_x + i * (panel_w + gap) + panel_w // 2
        tw = draw.textlength(n, font=font_name)
        draw.text((x - tw / 2, name_y), n, font=font_name, fill=INK)
        tw2 = draw.textlength(r, font=font_role)
        draw.text((x - tw2 / 2, name_y + 38), r, font=font_role, fill=BROWN)

    # Right roster panel
    roster_x = photos_x + 2 * panel_w + gap + 40
    roster_w = W - roster_x - 60
    roster_y = margin_y
    roster_h = panel_w
    draw.rectangle([(roster_x, roster_y), (roster_x + roster_w, roster_y + roster_h)], fill=PAPER_LIGHT, outline=LINE, width=2)
    draw.rectangle([(roster_x, roster_y), (roster_x + 6, roster_y + roster_h)], fill=AUBURN)

    font_hdr = ImageFont.truetype(ARIAL_BD, 22)
    draw.text((roster_x + 28, roster_y + 22), "11 CO-FOUNDERS", font=font_hdr, fill=BROWN)

    roster = [
        "Sam Altman",
        "Greg Brockman",
        "Ilya Sutskever",
        "Elon Musk",
        "John Schulman",
        "Wojciech Zaremba",
        "Andrej Karpathy",
        "Durk Kingma",
        "Vicki Cheung",
        "Pamela Vagata",
        "Trevor Blackwell",
    ]
    font_item = ImageFont.truetype(ARIAL, 21)
    item_y = roster_y + 68
    for name in roster:
        draw.text((roster_x + 28, item_y), "·  " + name, font=font_item, fill=INK)
        item_y += 32

    add_caption_bar(canvas, "PHOTOS · Wikimedia Commons (CC BY 2.0 · CC BY 3.0) — roster from OpenAI 2015.12 announcement")
    canvas.save(EP4 / "fig-01.jpg", "JPEG", quality=88, optimize=True)
    print("  saved fig-01.jpg")


# ============================================================
# fig-02 — GPT-1/2/3 parameter scaling bar chart
# ============================================================
def make_fig02():
    print("Building fig-02: GPT-1 → GPT-2 → GPT-3 scaling bar chart")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)

    # Title
    font_title = ImageFont.truetype(ARIAL_BD, 44)
    title = "GPT — Parameter Scaling, 2018→2020"
    tw = draw.textlength(title, font=font_title)
    draw.text(((W - tw) / 2, 60), title, font=font_title, fill=INK)
    draw.rectangle([(W // 2 - 40, 122), (W // 2 + 40, 124)], fill=AUBURN)

    # Subtitle
    font_sub = ImageFont.truetype(ARIAL_IT, 24)
    sub = "117M → 1.5B → 175B parameters"
    tws = draw.textlength(sub, font=font_sub)
    draw.text(((W - tws) / 2, 140), sub, font=font_sub, fill=BROWN)

    # Bars (log scale visually because linear scale crushes GPT-1/2)
    # Use a stylized layout: rectangles whose heights map to log(B+1)
    import math
    params = [
        ("GPT-1",   "117M",  0.117, "2018.06"),
        ("GPT-2",   "1.5B",  1.5,   "2019.02"),
        ("GPT-3",   "175B",  175,   "2020.05"),
    ]
    chart_top = 240
    chart_bottom = H - 160
    chart_h = chart_bottom - chart_top
    n = len(params)
    bar_w = 220
    gap = 120
    total_w = bar_w * n + gap * (n - 1)
    start_x = (W - total_w) // 2

    # log mapping
    max_log = math.log10(175) + 0.3  # add some headroom
    min_log = math.log10(0.05)
    for i, (label, ptext, p, date) in enumerate(params):
        h = int(chart_h * (math.log10(p) - min_log) / (max_log - min_log))
        h = max(60, min(chart_h, h))
        x0 = start_x + i * (bar_w + gap)
        y0 = chart_bottom - h
        x1 = x0 + bar_w
        y1 = chart_bottom

        # Shadow
        for offset in range(0, 6):
            draw.rectangle([(x0 + offset, y0 + offset), (x1 + offset, y1)], fill=(0, 0, 0, 0))
        # Gradient-ish: solid auburn for GPT-3, brown for GPT-2, light brown for GPT-1
        colors = [BROWN, AUBURN, AUBURN]
        if i == 0:
            color = (175, 145, 100)
        elif i == 1:
            color = BROWN
        else:
            color = AUBURN
        draw.rectangle([(x0, y0), (x1, y1)], fill=color)

        # Label inside bar
        font_label = ImageFont.truetype(ARIAL_BD, 38)
        ptw = draw.textlength(ptext, font=font_label)
        # If too dark, put white text on bar; light label below bar
        draw.text((x0 + (bar_w - ptw) / 2, y0 - 60), ptext, font=font_label, fill=INK)

        # Model name below bar
        font_name = ImageFont.truetype(ARIAL_BD, 32)
        nw = draw.textlength(label, font=font_name)
        draw.text((x0 + (bar_w - nw) / 2, chart_bottom + 18), label, font=font_name, fill=INK)
        # Date
        font_date = ImageFont.truetype(ARIAL_IT, 22)
        dw = draw.textlength(date, font=font_date)
        draw.text((x0 + (bar_w - dw) / 2, chart_bottom + 60), date, font=font_date, fill=INK_DIM)

    # Axis baseline
    draw.rectangle([(start_x - 40, chart_bottom + 2), (start_x + total_w + 40, chart_bottom + 4)], fill=LINE)

    add_caption_bar(canvas, "DATA · OpenAI papers (2018, 2019, 2020) — log scale shown")
    canvas.save(EP4 / "fig-02.jpg", "JPEG", quality=90, optimize=True)
    print("  saved fig-02.jpg")


# ============================================================
# fig-03 — 2-way (Altman + Nadella)
# ============================================================
def make_fig03():
    print("Building fig-03: 2-way (Altman + Nadella)")
    altman = Image.open(EP4 / "sam-altman-ted.jpg").convert("RGB")
    nadella = Image.open(EP4 / "satya-nadella.jpg").convert("RGB")

    panel = 600
    a_im = square_crop_center(altman, panel)
    n_im = square_crop_center(nadella, panel)

    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)

    # Title
    font_title = ImageFont.truetype(ARIAL_BD, 40)
    title = "OpenAI × Microsoft Partnership"
    tw = draw.textlength(title, font=font_title)
    draw.text(((W - tw) / 2, 50), title, font=font_title, fill=INK)
    draw.rectangle([(W // 2 - 40, 110), (W // 2 + 40, 112)], fill=AUBURN)

    font_sub = ImageFont.truetype(ARIAL_IT, 24)
    sub = "Capped-profit, then $10B (2019.07), then $10B more (2023.01)"
    tws = draw.textlength(sub, font=font_sub)
    draw.text(((W - tws) / 2, 128), sub, font=font_sub, fill=BROWN)

    # Panels
    margin_y = 200
    gap = 80
    total_w = panel * 2 + gap
    start_x = (W - total_w) // 2
    canvas.paste(a_im, (start_x, margin_y))
    canvas.paste(n_im, (start_x + panel + gap, margin_y))

    # Names
    font_name = ImageFont.truetype(ARIAL_BD, 32)
    font_role = ImageFont.truetype(ARIAL_IT, 22)
    name_y = margin_y + panel + 22
    role_y = name_y + 44

    for i, (n, r, x_off) in enumerate([
        ("Sam Altman", "OpenAI · CEO", 0),
        ("Satya Nadella", "Microsoft · CEO", panel + gap),
    ]):
        x = start_x + x_off + panel // 2
        tw = draw.textlength(n, font=font_name)
        draw.text((x - tw / 2, name_y), n, font=font_name, fill=INK)
        tw2 = draw.textlength(r, font=font_role)
        draw.text((x - tw2 / 2, role_y), r, font=font_role, fill=BROWN)

    # Cross / × ornament between panels
    cx = start_x + panel + gap // 2
    cy = margin_y + panel // 2
    draw.line([(cx - 18, cy - 18), (cx + 18, cy + 18)], fill=AUBURN, width=4)
    draw.line([(cx - 18, cy + 18), (cx + 18, cy - 18)], fill=AUBURN, width=4)

    add_caption_bar(canvas, "PHOTOS · Wikimedia Commons (CC BY 2.0 · CC BY-SA 4.0)")
    canvas.save(EP4 / "fig-03.jpg", "JPEG", quality=88, optimize=True)
    print("  saved fig-03.jpg")


# ============================================================
# fig-05 — GPT-4 benchmark, hand-drawn in beige theme
# ============================================================
def make_fig05():
    print("Building fig-05: GPT-4 benchmark exam comparison (hand-drawn)")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)

    font_title = ImageFont.truetype(ARIAL_BD, 40)
    title = "GPT-4 — Exam Performance (Percentile)"
    tw = draw.textlength(title, font=font_title)
    draw.text(((W - tw) / 2, 50), title, font=font_title, fill=INK)
    draw.rectangle([(W // 2 - 40, 110), (W // 2 + 40, 112)], fill=AUBURN)

    font_sub = ImageFont.truetype(ARIAL_IT, 22)
    sub = "GPT-4 (auburn) vs GPT-3.5 (brown) · selected from arXiv:2303.08774, Table 1"
    tws = draw.textlength(sub, font=font_sub)
    draw.text(((W - tws) / 2, 128), sub, font=font_sub, fill=BROWN)

    # Data: (label, gpt35_pct, gpt4_pct)
    # All values are estimated percentiles or % scores from the GPT-4 paper.
    data = [
        ("Uniform Bar Exam",    10, 90),
        ("LSAT",                40, 88),
        ("SAT Math",            70, 89),
        ("GRE Quantitative",    25, 80),
        ("USABO Semifinal",     32, 87),
        ("AP Biology",          62, 85),
        ("AMC 10",               6, 30),
    ]

    # Layout
    chart_left = 380
    chart_right = W - 80
    chart_top = 200
    chart_bottom = H - 130
    row_h = (chart_bottom - chart_top) // len(data)
    bar_track = chart_right - chart_left

    font_lbl  = ImageFont.truetype(ARIAL_BD, 22)
    font_pct  = ImageFont.truetype(ARIAL_BD, 20)
    font_axis = ImageFont.truetype(ARIAL, 18)

    # Axis baseline (vertical) at chart_left
    draw.rectangle([(chart_left - 2, chart_top - 10), (chart_left, chart_bottom + 10)], fill=LINE)
    # Tick marks at 0/25/50/75/100
    for v in (0, 25, 50, 75, 100):
        x = chart_left + int(bar_track * v / 100)
        draw.line([(x, chart_top - 6), (x, chart_bottom + 6)], fill=LINE, width=1)
        tw_t = draw.textlength(str(v), font=font_axis)
        draw.text((x - tw_t/2, chart_bottom + 14), str(v), font=font_axis, fill=INK_DIM)

    bar_h = 22
    gap = 6

    for i, (label, g35, g4) in enumerate(data):
        cy = chart_top + i * row_h + row_h // 2
        # Label on left
        tw_l = draw.textlength(label, font=font_lbl)
        draw.text((chart_left - 20 - tw_l, cy - 30), label, font=font_lbl, fill=INK)

        # GPT-3.5 bar (top)
        y0_35 = cy - bar_h - gap // 2
        w35 = int(bar_track * g35 / 100)
        draw.rectangle([(chart_left, y0_35), (chart_left + w35, y0_35 + bar_h)], fill=BROWN)
        draw.text((chart_left + w35 + 8, y0_35), f"GPT-3.5 · {g35}", font=font_pct, fill=BROWN)

        # GPT-4 bar (bottom)
        y0_4 = cy + gap // 2
        w4 = int(bar_track * g4 / 100)
        draw.rectangle([(chart_left, y0_4), (chart_left + w4, y0_4 + bar_h)], fill=AUBURN)
        draw.text((chart_left + w4 + 8, y0_4), f"GPT-4 · {g4}", font=font_pct, fill=AUBURN)

    add_caption_bar(canvas, "SOURCE · OpenAI GPT-4 Technical Report (arXiv:2303.08774)")
    canvas.save(EP4 / "fig-05.jpg", "JPEG", quality=90, optimize=True)
    print("  saved fig-05.jpg")


# ============================================================
# fig-06 — Pioneer Building exterior
# ============================================================
def make_fig06():
    print("Building fig-06: Pioneer Building exterior")
    pb = Image.open(EP4 / "pioneer-building.jpg").convert("RGB")
    # Original is 5408x2717 (panoramic). Fit to W=1600, scale proportionally.
    bw, bh = pb.size
    scale = W / bw
    new_size = (W, int(bh * scale))
    pb = pb.resize(new_size, Image.LANCZOS)

    canvas = make_paper_canvas()
    # Center vertically
    paste_y = (H - new_size[1]) // 2 - 20
    canvas.paste(pb, (0, paste_y))

    draw = ImageDraw.Draw(canvas)
    # Label box at bottom
    font_label = ImageFont.truetype(ARIAL_BD, 28)
    font_sub = ImageFont.truetype(ARIAL_IT, 22)

    label = "Pioneer Building · 3180 18th St · San Francisco"
    sub = "OpenAI's HQ from 2016 to ~2024"
    tw = draw.textlength(label, font=font_label)
    tws = draw.textlength(sub, font=font_sub)
    box_top = H - 130
    draw.rectangle([(0, box_top), (W, H)], fill=PAPER_DARK)
    draw.text(((W - tw) / 2, box_top + 22), label, font=font_label, fill=INK)
    draw.text(((W - tws) / 2, box_top + 64), sub, font=font_sub, fill=BROWN)

    add_caption_bar(canvas, "PHOTO · Wikimedia Commons (CC BY-SA 4.0)")
    canvas.save(EP4 / "fig-06.jpg", "JPEG", quality=88, optimize=True)
    print("  saved fig-06.jpg")


# ============================================================
# fig-08 — 2026 OpenAI lineup chart
# ============================================================
def make_fig08():
    print("Building fig-08: 2026 OpenAI lineup chart")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)

    font_title = ImageFont.truetype(ARIAL_BD, 44)
    title = "OpenAI — 2026 Spring Lineup"
    tw = draw.textlength(title, font=font_title)
    draw.text(((W - tw) / 2, 50), title, font=font_title, fill=INK)
    draw.rectangle([(W // 2 - 40, 112), (W // 2 + 40, 114)], fill=AUBURN)

    font_sub = ImageFont.truetype(ARIAL_IT, 24)
    sub = "From a non-profit lab to the most-used AI in the world"
    tws = draw.textlength(sub, font=font_sub)
    draw.text(((W - tws) / 2, 128), sub, font=font_sub, fill=BROWN)

    # Six product cards in two rows
    products = [
        ("ChatGPT",     "~500M weekly users",     "consumer · web/app"),
        ("API",         "GPT-4o · GPT-5",         "developers"),
        ("Enterprise",  "Fortune 500",            "teams · workspaces"),
        ("Sora",        "video generation",       "media · creative"),
        ("o-series",    "o1 · o3 reasoning",      "deep thinking"),
        ("Voice Mode",  "GPT-4o · realtime",      "natural speech"),
    ]

    card_w = 420
    card_h = 200
    gap = 40
    cols = 3
    rows = 2
    total_w = card_w * cols + gap * (cols - 1)
    total_h = card_h * rows + gap * (rows - 1)
    start_x = (W - total_w) // 2
    start_y = 220

    font_pname = ImageFont.truetype(ARIAL_BD, 32)
    font_pdesc = ImageFont.truetype(ARIAL_BD, 22)
    font_pmeta = ImageFont.truetype(ARIAL_IT, 20)

    for idx, (name, desc, meta) in enumerate(products):
        r = idx // cols
        c = idx % cols
        x0 = start_x + c * (card_w + gap)
        y0 = start_y + r * (card_h + gap)
        x1 = x0 + card_w
        y1 = y0 + card_h
        # Card background
        draw.rectangle([(x0, y0), (x1, y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
        # Left auburn strip
        draw.rectangle([(x0, y0), (x0 + 6, y1)], fill=AUBURN)

        # Title
        draw.text((x0 + 28, y0 + 22), name, font=font_pname, fill=INK)
        draw.text((x0 + 28, y0 + 76), desc, font=font_pdesc, fill=BROWN)
        draw.text((x0 + 28, y0 + 120), meta, font=font_pmeta, fill=INK_DIM)

    # Bottom stats line
    font_stat = ImageFont.truetype(ARIAL_BD, 28)
    font_stat_sm = ImageFont.truetype(ARIAL, 20)
    stat_y = H - 160
    stats = [
        ("$15B+",   "annual revenue (est.)"),
        ("$300B",   "valuation (est.)"),
        ("500M+",   "weekly users"),
        ("11 yrs",  "since 2015 founding"),
    ]
    stat_w = W // 4
    for i, (val, desc) in enumerate(stats):
        x = i * stat_w + stat_w // 2
        vw = draw.textlength(val, font=font_stat)
        dw = draw.textlength(desc, font=font_stat_sm)
        draw.text((x - vw / 2, stat_y), val, font=font_stat, fill=AUBURN)
        draw.text((x - dw / 2, stat_y + 38), desc, font=font_stat_sm, fill=INK_SOFT)

    add_caption_bar(canvas, "ESTIMATES · 2026.05 · public sources (Bloomberg, The Information)")
    canvas.save(EP4 / "fig-08.jpg", "JPEG", quality=88, optimize=True)
    print("  saved fig-08.jpg")


def main():
    make_fig01()
    make_fig02()
    make_fig03()
    make_fig05()
    make_fig06()
    make_fig08()
    print()
    print("Done. Generated figures:")
    for p in sorted(EP4.glob("fig-*.jpg")):
        sz = p.stat().st_size
        print(f"  {p.name}: {sz/1024:.1f} KB")


if __name__ == "__main__":
    main()
