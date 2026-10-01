#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""오목 OG 이미지(1200×630) — gen-og-games.py 와 같은 틀(그라데이션·제목·칩·브랜드)에 오목 모티프만 얹는다.

gen-og-games.py 는 다른 작업이 함께 고치는 파일이라 건드리지 않고 build()/glow() 를 가져다 쓴다.
메인 통합 때 그쪽 GAMES 표로 옮기려면 아래 m_omok 와 CFG 를 그대로 복사하면 된다.

원본(둘 다 Blender):
  scripts/og-assets/tiles3d/omok.png   (blender -b -P scripts/blender/tile_omok.py)
  scripts/og-assets/mascot/cheer.png   (레서판다 만세 — 기존 마스코트 렌더)
실행: python scripts/gen_og_omok.py → public/og/games/omok.png
"""
import importlib.util
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("gen_og_games", HERE / "gen-og-games.py")
OG = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(OG)


def m_omok(d, img):
    """오목 — 홈 타일과 같은 장난감 오목판(흑 다섯 + 금빛 고리) + 레서판다 만세. 비자나무 금빛 후광."""
    OG.glow(img, OG.MCX - 10, OG.MCY + 20, 270, (214, 150, 70), 72)
    OG.glow(img, OG.MCX + 70, OG.MCY - 120, 170, (246, 214, 120), 46)

    def load(path):
        im = Image.open(HERE / "og-assets" / path).convert("RGBA")
        a = im.getchannel("A").point(lambda v: 255 if v > 40 else 0)
        return im.crop(a.getbbox())
    toy = load("tiles3d/omok.png")
    w = 430
    h = round(toy.height * w / toy.width)
    toy = toy.resize((w, h), Image.LANCZOS)
    img.alpha_composite(toy, (OG.MCX - w // 2 + 18, OG.MCY - h // 2 + 16))
    pd = load("mascot/cheer.png")
    pw = 220
    ph = round(pd.height * pw / pd.width)
    pd = pd.resize((pw, ph), Image.LANCZOS)
    img.alpha_composite(pd, (OG.MX - 80, OG.MY + OG.MH - ph + 50))


CFG = dict(title="GOMOKU", sub="오목 — 다섯 개를 먼저 잇는 사람이 이긴다", cat="BOARD",
           top=(34, 20, 10), bot=(12, 7, 3), accent=(232, 200, 114), motif=m_omok)

if __name__ == "__main__":
    OG.OUT.mkdir(parents=True, exist_ok=True)
    OG.build("omok", CFG)
