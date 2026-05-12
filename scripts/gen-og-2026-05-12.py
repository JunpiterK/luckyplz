"""One-off OG generator for the 2026-05-12 (US close) + 2026-05-13 (KR open) posts."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_daily_og import make_og  # type: ignore

OUT = Path(__file__).resolve().parent.parent / "public" / "assets" / "blog"
OUT.mkdir(parents=True, exist_ok=True)

# ─── US Close Recap 5/12 ─────────────────────────────────────────────
us_close_og = {
    "card1": {"tick": "S&P 500", "val": "7,363", "sub": "-0.67%", "color": "down"},
    "card2": {"tick": "INTC", "val": "-10.0%", "sub": "PROFIT", "color": "down"},
    "card3": {"tick": "QCOM", "val": "-12.0%", "sub": "WORST", "color": "down"},
    "card4": {"tick": "NVDA", "val": "+2.0%", "sub": "ALONE", "color": "up"},
}
make_og(OUT / "og-us-tech-recap-2026-05-12.png", lang="ko",
        label="미국 테크 마감 리캡 · 2026-05-12",
        headline="CPI 쇼크에 차익실현 폭락",
        og_data=us_close_og)
make_og(OUT / "og-us-tech-recap-2026-05-12-en.png", lang="en",
        label="US TECH DAILY RECAP · MAY 12 2026",
        headline="Hot CPI Triggers Chip Sell-off",
        og_data=us_close_og)

# ─── KR Open Brief 5/13 ─────────────────────────────────────────────
kr_open_og = {
    "card1": {"tick": "005930", "val": "-2.0%", "sub": "GAP", "color": "down"},
    "card2": {"tick": "000660", "val": "-2.5%", "sub": "GAP", "color": "down"},
    "card3": {"tick": "373220", "val": "+2.0%", "sub": "TSLA", "color": "up"},
    "card4": {"tick": "096770", "val": "+3.0%", "sub": "OIL", "color": "gold"},
}
make_og(OUT / "og-kr-open-brief-2026-05-13.png", lang="ko",
        label="한국장 개장 브리핑 · 2026-05-13",
        headline="美 CPI 쇼크 여진",
        og_data=kr_open_og)
make_og(OUT / "og-kr-open-brief-2026-05-13-en.png", lang="en",
        label="KOREA OPEN BRIEF · MAY 13 2026",
        headline="Trading the CPI Aftershock",
        og_data=kr_open_og)

print("[ok] all 4 OG PNGs generated.")
