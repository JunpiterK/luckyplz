#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""장기·象棋 OG 이미지(1200×630) — gen-og-games.py 와 같은 틀(그라데이션·제목·칩·브랜드)에 장기 모티프만 얹는다 (2026-10-02).

gen-og-games.py 는 다른 작업이 함께 고치는 파일이라 건드리지 않고 build()/glow() 를 가져다 쓴다(gen_og_omok.py 와 같은 방식).
메인 통합 때 그쪽 GAMES 표로 옮기려면 아래 m_janggi 와 CFG 를 그대로 복사하면 된다.
제목 글꼴(arialbd)에는 한자가 없어 제목은 JANGGI, 부제(맑은 고딕 굵게)에 '장기 · 象棋'를 넣는다.

원본(둘 다 Blender):
  public/assets/tiles/toy-janggi.webp   (blender -b -P scripts/blender/tile_janggi.py → python scripts/build_tiles.py janggi)
  scripts/og-assets/mascot/cheer.png     (레서판다 만세 — 기존 마스코트 렌더)
실행: python scripts/gen_og_janggi.py → public/og/games/janggi.png
"""
import importlib.util
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("gen_og_games", HERE / "gen-og-games.py")
OG = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(OG)


def m_janggi(d, img):
    """장기 — 홈 타일과 같은 장난감(궁성 귀퉁이 판 + 楚 팔각 말 + 帥 둥근 말) + 레서판다 만세. 초록·빨강 후광."""
    OG.glow(img, OG.MCX - 30, OG.MCY + 30, 260, (40, 150, 90), 60)
    OG.glow(img, OG.MCX + 90, OG.MCY - 100, 180, (210, 60, 50), 50)

    def load(path):
        im = Image.open(HERE / "og-assets" / path).convert("RGBA")
        a = im.getchannel("A").point(lambda v: 255 if v > 40 else 0)
        return im.crop(a.getbbox())
    # 원본 렌더는 그림자 캐처의 옅은 알파가 네모나게 남는다 → build_tiles.py 가 정리한 타일 webp 를 쓴다
    toy = Image.open(HERE.parent / "public" / "assets" / "tiles" / "toy-janggi.webp").convert("RGBA")
    toy = toy.crop(toy.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())
    w = 440
    h = round(toy.height * w / toy.width)
    toy = toy.resize((w, h), Image.LANCZOS)
    img.alpha_composite(toy, (OG.MCX - w // 2 + 10, OG.MCY - h // 2 + 6))
    pd = load("mascot/cheer.png")
    pw = 200
    ph = round(pd.height * pw / pd.width)
    pd = pd.resize((pw, ph), Image.LANCZOS)
    img.alpha_composite(pd, (OG.MX - 90, OG.MY + OG.MH - ph + 60))


CFG = dict(title="JANGGI", sub="장기 · 象棋 — AI·친구와 한 판, 두 규칙 모두", cat="BOARD",
           top=(30, 20, 10), bot=(10, 7, 3), accent=(232, 200, 114), motif=m_janggi)

if __name__ == "__main__":
    OG.OUT.mkdir(parents=True, exist_ok=True)
    OG.build("janggi", CFG)
