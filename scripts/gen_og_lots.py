#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""긁는 제비뽑기 OG 이미지(1200×630) — gen-og-games.py 와 같은 틀(그라데이션·제목·칩·브랜드)에 제비 모티프만 얹는다.

gen-og-games.py 는 다른 작업이 함께 고치는 파일이라 건드리지 않고 build()/glow() 를 가져다 쓴다(gen_og_omok.py 와 같은 방식).
메인 통합 때 그쪽 GAMES 표로 옮기려면 아래 m_lots 와 CFG 를 그대로 복사하면 된다.

원본(둘 다 Blender):
  scripts/og-assets/tiles3d/lots.png   (blender -b -P scripts/blender/tile_lots.py)
  scripts/og-assets/mascot/cheer.png   (레서판다 만세 — 기존 마스코트 렌더)
실행: python scripts/gen_og_lots.py → public/og/games/lots.png
"""
import importlib.util
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("gen_og_games", HERE / "gen-og-games.py")
OG = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(OG)


def m_lots(d, img):
    """긁는 제비뽑기 — 홈 타일과 같은 장난감 제비 세 장(맨 앞은 반쯤 긁혀 당첨 별) + 금화 + 레서판다 만세. 금빛·산호빛 후광."""
    OG.glow(img, OG.MCX - 10, OG.MCY + 20, 270, (255, 150, 90), 70)
    OG.glow(img, OG.MCX + 60, OG.MCY - 110, 170, (255, 214, 110), 50)

    def load(path):
        im = Image.open(HERE / "og-assets" / path).convert("RGBA")
        a = im.getchannel("A").point(lambda v: 255 if v > 40 else 0)
        return im.crop(a.getbbox())
    toy = load("tiles3d/lots.png")
    w = 420
    h = round(toy.height * w / toy.width)
    if h > 470:
        h = 470
        w = round(toy.width * h / toy.height)
    toy = toy.resize((w, h), Image.LANCZOS)
    img.alpha_composite(toy, (OG.MCX - w // 2 + 24, OG.MCY - h // 2 + 14))
    pd = load("mascot/cheer.png")
    pw = 210
    ph = round(pd.height * pw / pd.width)
    pd = pd.resize((pw, ph), Image.LANCZOS)
    img.alpha_composite(pd, (OG.MX - 86, OG.MY + OG.MH - ph + 54))


CFG = dict(title="SCRATCH LOTS", sub="긁는 제비뽑기 — 긁어야 안다! 당첨·꽝·벌칙", cat="LUCKY",
           top=(36, 12, 30), bot=(13, 5, 14), accent=(255, 201, 77), motif=m_lots)

if __name__ == "__main__":
    OG.OUT.mkdir(parents=True, exist_ok=True)
    OG.build("lots", CFG)
