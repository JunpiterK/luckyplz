#!/usr/bin/env python3
"""Build the 1200 × 630 game share cards using their published home tile art.

Run without arguments for the full catalog, or pass one or more game slugs.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "og" / "games"
TILES = ROOT / "public" / "assets" / "tiles"
FONTS = Path("C:/Windows/Fonts")

W, H = 1200, 630
WHITE = (245, 247, 250)
DIM = (165, 175, 192)
CHIP_BG = (10, 13, 22)
CHIP_BD = (52, 64, 90)

ART_LEFT, ART_TOP, ART_WIDTH, ART_HEIGHT = 694, 52, 472, 526
TEXT_LEFT = 76


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def vgrad(top, bot):
    base = Image.new("RGB", (W, H), top)
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), int(y / (H - 1) * 255))
    return Image.composite(Image.new("RGB", (W, H), bot), base, g.resize((W, H))).convert("RGBA")


def glow(img, cx, cy, r, color, alpha):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (alpha,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(r // 2)))


def draw_game_art(img, slug):
    with Image.open(TILES / f"toy-{slug}.webp") as source:
        tile = source.convert("RGBA")
    tile = tile.crop(tile.getchannel("A").getbbox())
    tile = ImageOps.contain(tile, (ART_WIDTH, ART_HEIGHT), Image.Resampling.LANCZOS)
    x = ART_LEFT + (ART_WIDTH - tile.width) // 2
    y = ART_TOP + (ART_HEIGHT - tile.height) // 2
    shadow = Image.new("RGBA", img.size)
    mask = tile.getchannel("A").point(lambda a: a * 2 // 5)
    shadow.paste((0, 0, 0, 255), (x, y + 8, x + tile.width, y + tile.height + 8), mask)
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(8)))
    img.alpha_composite(tile, (x, y))


def fitted_font(filename, text, preferred_size):
    available = ART_LEFT - TEXT_LEFT - 18
    face = font(filename, preferred_size)
    width = face.getlength(text)
    if width > available:
        face = font(filename, int(preferred_size * available / width))
    return face


GAMES = {
    "lots": dict(title="SCRATCH LOTS", sub="긁는 제비뽑기 — 긁어야 안다! 당첨·꽝·벌칙", cat="LUCKY", top=(36, 12, 30), bot=(13, 5, 14), accent=(255, 201, 77)),
    "janggi": dict(title="JANGGI", sub="장기 · 象棋 — AI·친구와 한 판, 두 규칙 모두", cat="BOARD", top=(30, 20, 10), bot=(10, 7, 3), accent=(232, 200, 114)),
    "omok": dict(title="GOMOKU", sub="오목 — 다섯 개를 먼저 잇는 사람이 이긴다", cat="BOARD", top=(34, 20, 10), bot=(12, 7, 3), accent=(232, 200, 114)),
    "mahjong-tw":      dict(title="TAIWAN MAHJONG", sub="대만 마작 台灣麻將 — 16장, 친구와 각자 폰으로", cat="BOARD", top=(52, 8, 12), bot=(16, 3, 4), accent=(233, 196, 106)),
    "mahjong-solitaire": dict(title="MAHJONG", sub="마작 솔리테어 — 같은 패 짝지어 144장 치우기", cat="SOLITAIRE", top=(40, 10, 12), bot=(14, 4, 5), accent=(233, 196, 106)),
    "prism-hex":       dict(title="PRISM HEX", sub="프리즘 헥스 — 보석 블록을 꼭짓점으로 잇기", cat="BOARD", top=(22, 12, 38), bot=(8, 5, 16), accent=(246, 211, 138)),
    "gummy":           dict(title="GUMMY CHAIN", sub="구미 체인 — 쫀득한 연쇄로 1:1 대결", cat="PUZZLE", top=(30, 12, 40), bot=(12, 5, 18), accent=(255, 111, 168)),
    "yut":             dict(title="YUT NORI", sub="윷놀이 — 여럿이 함께, 최대 4팀", cat="BOARD", top=(30, 18, 12), bot=(12, 7, 5), accent=(244, 195, 90)),
    "reversi":         dict(title="REVERSI", sub="리버시 — AI·친구와 한 판, 모서리를 잡아라", cat="BOARD", top=(8, 26, 18), bot=(3, 10, 7), accent=(232, 200, 114)),
    "yacht":           dict(title="YACHT DICE", sub="요트 다이스 — 주사위 5개, 세 번의 기회", cat="BOARD", top=(10, 26, 40), bot=(4, 10, 18), accent=(246, 200, 95)),
    "ludo":            dict(title="LUDO", sub="루도 — 친구와 온라인 보드게임", cat="BOARD", top=(24, 12, 20), bot=(9, 5, 10), accent=(255, 209, 102)),
    "bubble":          dict(title="BUBBLE BURST", sub="버블 버스트 — 같은 색 셋이면 펑", cat="RETRO", top=(22, 12, 34), bot=(8, 5, 16), accent=(255, 95, 162)),
    "balloon":         dict(title="BALLOON POP", sub="풍선 룰렛 — 터뜨린 사람이 벌칙", cat="LUCKY", top=(28, 10, 18), bot=(11, 4, 8), accent=(255, 92, 122)),
    "roulette":        dict(title="ROULETTE", sub="룰렛 — 돌려서 정하는 내기 한 판", cat="LUCKY", top=(26, 10, 16), bot=(10, 4, 8), accent=(255, 206, 92)),
    "ladder":          dict(title="LADDER GAME", sub="사다리타기 — 벌칙·내기 공정 결정", cat="LUCKY", top=(8, 16, 30), bot=(4, 7, 14), accent=(80, 200, 255)),
    "lotto":           dict(title="LOTTO", sub="로또 번호 생성기 — 오늘의 행운 번호", cat="LUCKY", top=(10, 22, 16), bot=(4, 9, 7), accent=(61, 214, 140)),
    "team":            dict(title="TEAM PICKER", sub="팀나누기 — 공정한 랜덤 팀 배정", cat="LUCKY", top=(10, 14, 30), bot=(5, 6, 13), accent=(93, 193, 255)),
    "dice":            dict(title="DICE ROLLER", sub="주사위 — 흔들어서 결정", cat="LUCKY", top=(18, 12, 30), bot=(8, 5, 13), accent=(167, 139, 250)),
    "snake":           dict(title="SNAKE", sub="스네이크 — 클래식 기록 갱신", cat="RETRO", top=(8, 20, 12), bot=(3, 8, 5), accent=(61, 214, 140)),
    "pacman":          dict(title="DOT RUNNER", sub="닷 러너 — 미로 속 추격전", cat="RETRO", top=(10, 10, 26), bot=(4, 4, 11), accent=(255, 221, 51)),
    "tetris":          dict(title="TETROMINO STACK", sub="테트로미노 쌓기 — 한 줄의 쾌감", cat="RETRO", top=(12, 10, 28), bot=(5, 4, 12), accent=(93, 193, 255)),
    "brick":           dict(title="BRICK BREAKER", sub="벽돌깨기 — 한 발의 각도 싸움", cat="RETRO", top=(24, 12, 10), bot=(10, 5, 4), accent=(255, 159, 64)),
    "burger":          dict(title="BURGER CHEF", sub="버거 셰프 — 주문 폭주 스택 쌓기", cat="RETRO", top=(24, 14, 8), bot=(10, 6, 3), accent=(240, 178, 92)),
    "car-racing":      dict(title="CAR RACE", sub="카레이싱 — 랜덤 레이스 내기", cat="RETRO", top=(20, 8, 12), bot=(8, 3, 5), accent=(235, 64, 84)),
    "glory-racing":    dict(title="BRAWL RUN", sub="Brawl Run — 달리고 빼앗는 내기", cat="RETRO", top=(20, 16, 6), bot=(8, 7, 3), accent=(255, 206, 92)),
    "dodge":           dict(title="SPACE-Z", sub="스페이스-Z — 레서판다 럭키와 우주 끝까지", cat="ARCADE", top=(6, 10, 24), bot=(3, 4, 10), accent=(0, 217, 255)),
    "starship-lander": dict(title="STARSHIP LANDER", sub="우주선 착륙 — 추력 조절의 미학", cat="RETRO", top=(8, 12, 24), bot=(3, 5, 10), accent=(255, 160, 60)),
    "lucky-merge":     dict(title="LUCKY MERGE", sub="행성 합체 — 우주 2048 퍼즐", cat="PUZZLE", top=(14, 10, 28), bot=(6, 4, 12), accent=(167, 139, 250)),
    "orbit":           dict(title="DELTA-V", sub="델타-브이 — 로켓 회사 연대기 6미션", cat="SIM", top=(4, 6, 14), bot=(1, 2, 5), accent=(56, 232, 200)),
    "bingo":           dict(title="BINGO", sub="빙고 — 친구와 실시간 한 판", cat="PARTY", top=(24, 10, 18), bot=(10, 4, 8), accent=(255, 99, 132)),
    "quiz":            dict(title="LIVE QUIZ", sub="라이브 퀴즈 — 같이 풀고 겨루기", cat="PARTY", top=(14, 10, 30), bot=(6, 4, 13), accent=(167, 139, 250)),
}


def build(slug, cfg):
    img = vgrad(cfg["top"], cfg["bot"])
    glow(img, 1050, 60, 330, cfg["accent"], 38)
    glow(img, 120, 600, 300, cfg["accent"], 26)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=cfg["accent"])

    draw_game_art(img, slug)
    d = ImageDraw.Draw(img)

    f_eyebrow = font("arialbd.ttf", 24)
    d.text((TEXT_LEFT, 96), f"LUCKY PLEASE · {cfg['cat']} GAME", font=f_eyebrow, fill=cfg["accent"])

    f_big = fitted_font("arialbd.ttf", cfg["title"], 88 if len(cfg["title"]) <= 12 else 70)
    d.text((TEXT_LEFT, 142), cfg["title"], font=f_big, fill=WHITE)

    f_sub = fitted_font("malgunbd.ttf", cfg["sub"], 31)
    d.text((TEXT_LEFT, 268), cfg["sub"], font=f_sub, fill=DIM)

    f_chip = font("arialbd.ttf", 23)
    chips = ["PLAY FREE", "NO LOGIN", "MOBILE · PC"]
    cx, cy = TEXT_LEFT, 352
    for c in chips:
        tb = d.textbbox((0, 0), c, font=f_chip)
        w = tb[2] - tb[0] + 50
        h = tb[3] - tb[1] + 20
        d.rounded_rectangle([cx, cy, cx + w, cy + h], h // 2, fill=CHIP_BG, outline=CHIP_BD, width=1)
        r = 5
        d.ellipse([cx + 16 - r + 5, cy + h // 2 - r, cx + 16 + r + 5, cy + h // 2 + r], fill=cfg["accent"])
        d.text((cx + 34, cy + 10 - tb[1]), c, font=f_chip, fill=WHITE)
        cx += w + 14

    f_brand = font("arialbd.ttf", 26)
    f_meta = font("arial.ttf", 21)
    d.text((TEXT_LEFT, H - 76), "luckyplz.com", font=f_brand, fill=WHITE)
    d.text((TEXT_LEFT, H - 44), "games that settle the bet", font=f_meta, fill=DIM)

    out = OUT / f"{slug}.png"
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"  wrote games/{out.name}  ({out.stat().st_size // 1024} KB)")


def main():
    import sys
    # 인자로 slug 를 주면 그 게임만 만든다 (예: python scripts/gen-og-games.py bubble)
    only = set(sys.argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    print("Generating per-game OG images:")
    for slug, cfg in GAMES.items():
        if only and slug not in only:
            continue
        build(slug, cfg)
    print("done.")


if __name__ == "__main__":
    main()
