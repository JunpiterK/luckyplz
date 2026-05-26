"""
Ep.5 figure generator/composer (Google · Meta · xAI · Mistral).

- fig-01: Sundar Pichai + Demis Hassabis 2-way collage (Google)
- fig-02: Gemini lineup 4-card grid (Ultra · Pro · Nano · Flash)
- fig-03: Mark Zuckerberg + Yann LeCun 2-way collage (Meta)
- fig-04: Llama parameter scaling bar chart (LLaMA 1 → Llama 3.1 405B)
- fig-05: Elon Musk + Memphis Colossus stat card (xAI)
- fig-06: Arthur Mensch solo + Mistral context card (Mistral)
- fig-07: Frontier 6-company map card
- fig-08: 2026 landscape diagram — six answers + their backers
"""
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8")

EP5 = Path(r"C:\code\python\luckyplz\.claude\worktrees\inspiring-cerf-fac44c\public\assets\anthropic-series\ep5")

# Beige book palette
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


def square_crop_center(im, size):
    w, h = im.size
    s = min(w, h)
    left = (w - s) // 2
    top = (h - s) // 2
    im = im.crop((left, top, left + s, top + s))
    return im.resize((size, size), Image.LANCZOS)


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
        font_sub = ImageFont.truetype(ARIAL_IT, 24)
        tws = draw.textlength(subtitle, font=font_sub)
        draw.text(((W - tws) / 2, 130), subtitle, font=font_sub, fill=BROWN)


# ============================================================
# fig-01 — Google: Pichai + Hassabis
# ============================================================
def make_fig01():
    print("fig-01: Pichai + Hassabis")
    a = Image.open(EP5 / "pichai.jpg").convert("RGB")
    b = Image.open(EP5 / "hassabis.jpg").convert("RGB")
    panel = 540
    a_im = square_crop_center(a, panel)
    b_im = square_crop_center(b, panel)
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Google — Two Labs, One Company", "DeepMind + Brain merged April 2023")
    margin_y = 220
    gap = 80
    total_w = panel * 2 + gap
    start_x = (W - total_w) // 2
    canvas.paste(a_im, (start_x, margin_y))
    canvas.paste(b_im, (start_x + panel + gap, margin_y))
    font_name = ImageFont.truetype(ARIAL_BD, 30)
    font_role = ImageFont.truetype(ARIAL_IT, 22)
    for i, (n, r, x_off) in enumerate([
        ("Sundar Pichai", "Alphabet · CEO", 0),
        ("Demis Hassabis", "Google DeepMind · CEO", panel + gap),
    ]):
        x = start_x + x_off + panel // 2
        tw = draw.textlength(n, font=font_name)
        draw.text((x - tw / 2, margin_y + panel + 22), n, font=font_name, fill=INK)
        tw2 = draw.textlength(r, font=font_role)
        draw.text((x - tw2 / 2, margin_y + panel + 62), r, font=font_role, fill=BROWN)
    # + ornament between
    cx = start_x + panel + gap // 2
    cy = margin_y + panel // 2
    draw.line([(cx - 16, cy), (cx + 16, cy)], fill=AUBURN, width=4)
    draw.line([(cx, cy - 16), (cx, cy + 16)], fill=AUBURN, width=4)
    add_caption_bar(canvas, "PHOTOS · Wikimedia Commons (CC BY-SA 4.0 / CC BY 2.0)")
    canvas.save(EP5 / "fig-01.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-02 — Gemini lineup 4-card grid
# ============================================================
def make_fig02():
    print("fig-02: Gemini lineup")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Gemini — Google DeepMind's Model Family", "Ultra · Pro · Nano · Flash — multi-tier from 2023.12")
    cards = [
        ("Ultra",  "frontier · deep reasoning",  "highest capability"),
        ("Pro",    "everyday default",           "balanced cost · speed"),
        ("Nano",   "on-device",                  "Android · Pixel"),
        ("Flash",  "fast · light",               "high-throughput tasks"),
    ]
    card_w = 320
    card_h = 360
    gap = 30
    total_w = card_w * 4 + gap * 3
    start_x = (W - total_w) // 2
    start_y = 240
    f_name = ImageFont.truetype(ARIAL_BD, 38)
    f_desc = ImageFont.truetype(ARIAL_BD, 22)
    f_meta = ImageFont.truetype(ARIAL_IT, 20)
    for i, (name, desc, meta) in enumerate(cards):
        x0 = start_x + i * (card_w + gap)
        y0 = start_y
        x1 = x0 + card_w
        y1 = y0 + card_h
        draw.rectangle([(x0, y0), (x1, y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
        draw.rectangle([(x0, y0), (x0 + 6, y1)], fill=AUBURN)
        draw.text((x0 + 26, y0 + 30), name, font=f_name, fill=INK)
        draw.text((x0 + 26, y0 + 100), desc, font=f_desc, fill=BROWN)
        draw.text((x0 + 26, y0 + 150), meta, font=f_meta, fill=INK_DIM)
        # bottom label
        f_tag = ImageFont.truetype(ARIAL, 18)
        draw.text((x0 + 26, y1 - 50), "Gemini 1.0 → 3", font=f_tag, fill=INK_DIM)
    # context bar at bottom
    font_b = ImageFont.truetype(ARIAL_BD, 28)
    label = "1.5 generation: 1M-token context window (industry-leading)"
    lw = draw.textlength(label, font=font_b)
    draw.text(((W - lw) / 2, start_y + card_h + 50), label, font=font_b, fill=AUBURN)
    add_caption_bar(canvas, "DATA · Google DeepMind announcements, 2023.12 — 2026.05")
    canvas.save(EP5 / "fig-02.jpg", "JPEG", quality=90, optimize=True)


# ============================================================
# fig-03 — Meta: Zuckerberg + LeCun
# ============================================================
def make_fig03():
    print("fig-03: Zuckerberg + LeCun")
    a = Image.open(EP5 / "zuckerberg.jpg").convert("RGB")
    b = Image.open(EP5 / "lecun.jpg").convert("RGB")
    panel = 540
    a_im = square_crop_center(a, panel)
    b_im = square_crop_center(b, panel)
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Meta — FAIR and the Open-Weight Bet", "Yann LeCun · Mark Zuckerberg · the Llama line")
    margin_y = 220
    gap = 80
    total_w = panel * 2 + gap
    start_x = (W - total_w) // 2
    canvas.paste(a_im, (start_x, margin_y))
    canvas.paste(b_im, (start_x + panel + gap, margin_y))
    font_name = ImageFont.truetype(ARIAL_BD, 30)
    font_role = ImageFont.truetype(ARIAL_IT, 22)
    for i, (n, r, x_off) in enumerate([
        ("Mark Zuckerberg", "Meta · CEO", 0),
        ("Yann LeCun", "Meta Chief AI Scientist · 2018 Turing Award", panel + gap),
    ]):
        x = start_x + x_off + panel // 2
        tw = draw.textlength(n, font=font_name)
        draw.text((x - tw / 2, margin_y + panel + 22), n, font=font_name, fill=INK)
        tw2 = draw.textlength(r, font=font_role)
        draw.text((x - tw2 / 2, margin_y + panel + 62), r, font=font_role, fill=BROWN)
    add_caption_bar(canvas, "PHOTOS · Wikimedia Commons (CC BY-SA · CC BY)")
    canvas.save(EP5 / "fig-03.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-04 — Llama scaling bar chart
# ============================================================
def make_fig04():
    print("fig-04: Llama scaling")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Llama — Open-Weight Models from 7B to 405B",
                "Parameter scaling, 2023.02 → 2024.07 (log shown)")
    import math
    params = [
        ("LLaMA 1",   "65B",   65,   "2023.02"),
        ("Llama 2",   "70B",   70,   "2023.07"),
        ("Llama 3",   "70B",   70,   "2024.04"),
        ("Llama 3.1", "405B",  405,  "2024.07"),
    ]
    chart_top = 240
    chart_bottom = H - 160
    chart_h = chart_bottom - chart_top
    n = len(params)
    bar_w = 200
    gap = 80
    total_w = bar_w * n + gap * (n - 1)
    start_x = (W - total_w) // 2
    max_log = math.log10(420) + 0.05
    min_log = math.log10(50)
    for i, (label, ptext, p, date) in enumerate(params):
        h = int(chart_h * (math.log10(p) - min_log) / (max_log - min_log))
        h = max(80, min(chart_h, h))
        x0 = start_x + i * (bar_w + gap)
        y0 = chart_bottom - h
        x1 = x0 + bar_w
        y1 = chart_bottom
        if i < 2:
            color = (175, 145, 100)
        elif i == 2:
            color = BROWN
        else:
            color = AUBURN
        draw.rectangle([(x0, y0), (x1, y1)], fill=color)
        f_label = ImageFont.truetype(ARIAL_BD, 36)
        ptw = draw.textlength(ptext, font=f_label)
        draw.text((x0 + (bar_w - ptw) / 2, y0 - 56), ptext, font=f_label, fill=INK)
        f_name = ImageFont.truetype(ARIAL_BD, 28)
        nw = draw.textlength(label, font=f_name)
        draw.text((x0 + (bar_w - nw) / 2, chart_bottom + 18), label, font=f_name, fill=INK)
        f_date = ImageFont.truetype(ARIAL_IT, 20)
        dw = draw.textlength(date, font=f_date)
        draw.text((x0 + (bar_w - dw) / 2, chart_bottom + 56), date, font=f_date, fill=INK_DIM)
    draw.rectangle([(start_x - 40, chart_bottom + 2), (start_x + total_w + 40, chart_bottom + 4)], fill=LINE)
    add_caption_bar(canvas, "DATA · Meta AI publications, 2023.02 → 2024.07")
    canvas.save(EP5 / "fig-04.jpg", "JPEG", quality=90, optimize=True)


# ============================================================
# fig-05 — xAI: Elon Musk + Colossus stat card
# ============================================================
def make_fig05():
    print("fig-05: xAI Musk + Colossus")
    a = Image.open(EP5 / "musk.jpg").convert("RGB")
    panel = 520
    a_im = square_crop_center(a, panel)
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "xAI — 17 Months from Founding to Frontier",
                "Elon Musk · Memphis Colossus · 200,000 H100 GPUs")
    margin_y = 220
    # photo on left
    photo_x = 80
    canvas.paste(a_im, (photo_x, margin_y))
    # name caption below photo
    f_name = ImageFont.truetype(ARIAL_BD, 30)
    f_role = ImageFont.truetype(ARIAL_IT, 22)
    cx = photo_x + panel // 2
    tw = draw.textlength("Elon Musk", font=f_name)
    draw.text((cx - tw / 2, margin_y + panel + 22), "Elon Musk", font=f_name, fill=INK)
    tw2 = draw.textlength("xAI · Founder", font=f_role)
    draw.text((cx - tw2 / 2, margin_y + panel + 62), "xAI · Founder", font=f_role, fill=BROWN)
    # Stat card on right
    card_x = photo_x + panel + 60
    card_y = margin_y
    card_w = W - card_x - 80
    card_h = panel
    draw.rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], fill=PAPER_LIGHT, outline=LINE, width=2)
    draw.rectangle([(card_x, card_y), (card_x + 6, card_y + card_h)], fill=AUBURN)
    f_hdr = ImageFont.truetype(ARIAL_BD, 22)
    draw.text((card_x + 28, card_y + 22), "MEMPHIS COLOSSUS", font=f_hdr, fill=BROWN)
    stats = [
        ("100,000",   "NVIDIA H100 GPUs at launch"),
        ("122 days",  "to bring cluster online"),
        ("200,000",   "GPUs after 2× expansion"),
        ("$6B",       "Series B (2024.05)"),
        ("~$200B",    "valuation by 2026"),
    ]
    f_v = ImageFont.truetype(ARIAL_BD, 34)
    f_d = ImageFont.truetype(ARIAL_IT, 20)
    y = card_y + 64
    for val, desc in stats:
        draw.text((card_x + 28, y), val, font=f_v, fill=AUBURN)
        draw.text((card_x + 28, y + 44), desc, font=f_d, fill=INK_SOFT)
        y += 88
    add_caption_bar(canvas, "PHOTO · Wikimedia Commons (CC BY 2.0) · DATA · xAI/NVIDIA 2024 press")
    canvas.save(EP5 / "fig-05.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-06 — Mistral: Arthur Mensch + context card
# ============================================================
def make_fig06():
    print("fig-06: Mistral / Arthur Mensch")
    a = Image.open(EP5 / "mensch.jpg").convert("RGB")
    panel = 520
    a_im = square_crop_center(a, panel)
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "Mistral — Europe's Frontier AI",
                "Arthur Mensch · Guillaume Lample · Timothée Lacroix · Paris, 2023.04")
    margin_y = 220
    photo_x = 80
    canvas.paste(a_im, (photo_x, margin_y))
    f_name = ImageFont.truetype(ARIAL_BD, 30)
    f_role = ImageFont.truetype(ARIAL_IT, 22)
    cx = photo_x + panel // 2
    tw = draw.textlength("Arthur Mensch", font=f_name)
    draw.text((cx - tw / 2, margin_y + panel + 22), "Arthur Mensch", font=f_name, fill=INK)
    tw2 = draw.textlength("Mistral AI · Co-founder · CEO", font=f_role)
    draw.text((cx - tw2 / 2, margin_y + panel + 62), "Mistral AI · Co-founder · CEO", font=f_role, fill=BROWN)
    card_x = photo_x + panel + 60
    card_y = margin_y
    card_w = W - card_x - 80
    card_h = panel
    draw.rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], fill=PAPER_LIGHT, outline=LINE, width=2)
    draw.rectangle([(card_x, card_y), (card_x + 6, card_y + card_h)], fill=AUBURN)
    f_hdr = ImageFont.truetype(ARIAL_BD, 22)
    draw.text((card_x + 28, card_y + 22), "EUROPEAN AI SOVEREIGNTY", font=f_hdr, fill=BROWN)
    rows = [
        ("Mistral 7B",        "2023.09 · Apache 2.0 · open weights"),
        ("Mixtral 8x7B",      "2023.12 · Mixture of Experts"),
        ("Mistral Large",     "2024.02 · frontier closed model"),
        ("Le Chat",           "2025 · consumer assistant"),
        ("~€13B valuation",   "2026 · ex-DeepMind / Meta founders"),
    ]
    f_v = ImageFont.truetype(ARIAL_BD, 24)
    f_d = ImageFont.truetype(ARIAL_IT, 19)
    y = card_y + 64
    for val, desc in rows:
        draw.text((card_x + 28, y), val, font=f_v, fill=AUBURN)
        draw.text((card_x + 28, y + 34), desc, font=f_d, fill=INK_SOFT)
        y += 76
    add_caption_bar(canvas, "PHOTO · Wikimedia Commons (CC BY-SA 4.0) · DATA · mistral.ai")
    canvas.save(EP5 / "fig-06.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-07 — Frontier 6-company map
# ============================================================
def make_fig07():
    print("fig-07: Frontier 6-company map")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "The Frontier Six — Spring 2026",
                "OpenAI · Anthropic · Google · Meta · xAI · Mistral")
    cards = [
        ("OpenAI",    "USA · for-profit",        "ChatGPT · GPT-4o · o3 · Sora"),
        ("Anthropic", "USA · PBC",                "Claude Opus 4.7 · safety-first"),
        ("Google",    "USA · Alphabet",          "Gemini Ultra/Pro/Nano · TPU stack"),
        ("Meta",      "USA · open-weight",       "Llama 3.1 405B · Llama 4 · 5"),
        ("xAI",       "USA · Musk",              "Grok 4 · Colossus · X integration"),
        ("Mistral",   "France · EU sovereignty", "Mistral Large · Mixtral · Le Chat"),
    ]
    card_w = 460
    card_h = 200
    gap = 40
    cols = 3
    rows = 2
    total_w = card_w * cols + gap * (cols - 1)
    start_x = (W - total_w) // 2
    start_y = 220
    f_name = ImageFont.truetype(ARIAL_BD, 34)
    f_meta = ImageFont.truetype(ARIAL_BD, 20)
    f_desc = ImageFont.truetype(ARIAL_IT, 19)
    for idx, (name, meta, desc) in enumerate(cards):
        r = idx // cols
        c = idx % cols
        x0 = start_x + c * (card_w + gap)
        y0 = start_y + r * (card_h + gap)
        x1 = x0 + card_w
        y1 = y0 + card_h
        draw.rectangle([(x0, y0), (x1, y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
        draw.rectangle([(x0, y0), (x0 + 6, y1)], fill=AUBURN)
        draw.text((x0 + 26, y0 + 22), name, font=f_name, fill=INK)
        draw.text((x0 + 26, y0 + 78), meta, font=f_meta, fill=BROWN)
        draw.text((x0 + 26, y0 + 122), desc, font=f_desc, fill=INK_SOFT)
    add_caption_bar(canvas, "CHART · Lucky Please Editorial · 2026.05")
    canvas.save(EP5 / "fig-07.jpg", "JPEG", quality=88, optimize=True)


# ============================================================
# fig-08 — 2026 landscape — six answers + others
# ============================================================
def make_fig08():
    print("fig-08: 2026 landscape")
    canvas = make_paper_canvas()
    draw = ImageDraw.Draw(canvas)
    title_block(draw, "2026 Landscape — Six Answers and Many More",
                "Frontier six on top · the rest growing behind")
    # Top row: frontier 6
    top_label = "FRONTIER SIX"
    f_band = ImageFont.truetype(ARIAL_BD, 22)
    draw.text((90, 200), top_label, font=f_band, fill=BROWN)
    six = ["OpenAI", "Anthropic", "Google", "Meta", "xAI", "Mistral"]
    six_w = 220
    six_h = 80
    gap = 16
    total_w = six_w * 6 + gap * 5
    start_x = (W - total_w) // 2
    start_y = 240
    f_six = ImageFont.truetype(ARIAL_BD, 26)
    for i, name in enumerate(six):
        x0 = start_x + i * (six_w + gap)
        y0 = start_y
        x1 = x0 + six_w
        y1 = y0 + six_h
        draw.rectangle([(x0, y0), (x1, y1)], fill=AUBURN)
        tw = draw.textlength(name, font=f_six)
        # white text on auburn
        draw.text((x0 + (six_w - tw) / 2, y0 + (six_h - 32) / 2), name, font=f_six, fill=(255, 248, 220))
    # Bottom: contenders
    contender_label = "CONTENDERS · regions · open weights · enterprise"
    draw.text((90, 380), contender_label, font=f_band, fill=BROWN)
    contenders = [
        ("Cohere",        "Toronto · enterprise"),
        ("AI21",          "Israel · Jurassic · Jamba"),
        ("Reka",          "Singapore · multimodal"),
        ("DeepSeek",      "China · V3 · R1 reasoning"),
        ("Qwen (Alibaba)","China · open weights"),
        ("Kimi (Moonshot)","China · long context"),
        ("Zhipu / GLM",   "China"),
        ("MiniMax",       "China"),
        ("HyperCLOVA X",  "Korea · Naver"),
        ("Hugging Face",  "model hub · meeting point"),
    ]
    card_w = 290
    card_h = 80
    gap_h = 12
    gap_v = 14
    cols = 5
    total_cw = card_w * cols + gap_h * (cols - 1)
    cs_x = (W - total_cw) // 2
    cs_y = 420
    f_n = ImageFont.truetype(ARIAL_BD, 21)
    f_d = ImageFont.truetype(ARIAL_IT, 16)
    for idx, (name, desc) in enumerate(contenders):
        r = idx // cols
        c = idx % cols
        x0 = cs_x + c * (card_w + gap_h)
        y0 = cs_y + r * (card_h + gap_v)
        x1 = x0 + card_w
        y1 = y0 + card_h
        draw.rectangle([(x0, y0), (x1, y1)], fill=PAPER_LIGHT, outline=LINE, width=2)
        draw.rectangle([(x0, y0), (x0 + 4, y1)], fill=BROWN)
        draw.text((x0 + 16, y0 + 12), name, font=f_n, fill=INK)
        draw.text((x0 + 16, y0 + 42), desc, font=f_d, fill=INK_SOFT)
    # bottom note
    f_note = ImageFont.truetype(ARIAL_IT, 22)
    note = "No single champion. Several seats. Several answers."
    nw = draw.textlength(note, font=f_note)
    draw.text(((W - nw) / 2, H - 110), note, font=f_note, fill=AUBURN)
    add_caption_bar(canvas, "CHART · Lucky Please Editorial · 2026.05")
    canvas.save(EP5 / "fig-08.jpg", "JPEG", quality=88, optimize=True)


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
    for p in sorted(EP5.glob("fig-*.jpg")):
        sz = p.stat().st_size
        print(f"  {p.name}: {sz/1024:.1f} KB")


if __name__ == "__main__":
    main()
