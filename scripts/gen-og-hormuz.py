#!/usr/bin/env python3
"""OG images for the Strait of Hormuz deep report (4 langs)."""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OG = ROOT / "public" / "og"
FONTS = Path("C:/Windows/Fonts")
W, H = 1200, 630
WHITE=(245,247,250); DIM=(158,168,186); GOLD=(255,206,92); RED=(239,90,110); BLUE=(93,193,255)
CHIP_BG=(12,15,24); CHIP_BD=(48,60,86)
LANGS={
 "":   {"font":"malgunbd.ttf","sub":"세계 석유 20%가 지나는 폭 33km 바닷길"},
 "-en":{"font":"arialbd.ttf","sub":"The 33km waterway carrying 20% of the world's oil"},
 "-ja":{"font":"YuGothB.ttc","sub":"世界の石油の20%が通る幅33kmの海峡"},
 "-zh":{"font":"msyhbd.ttc","sub":"承载全球20%石油的33公里水道"},
}
def font(n,s): return ImageFont.truetype(str(FONTS/n),s)
def vgrad(t,b):
    base=Image.new("RGB",(W,H),t); g=Image.new("L",(1,H))
    for y in range(H): g.putpixel((0,y),int(y/(H-1)*255))
    return Image.composite(Image.new("RGB",(W,H),b),base,g.resize((W,H))).convert("RGBA")
def glow(img,cx,cy,r,c,a):
    l=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(l)
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=c+(a,)); img.alpha_composite(l.filter(ImageFilter.GaussianBlur(r//2)))
def build(suf,cfg):
    img=vgrad((6,12,26),(3,5,12))
    d=ImageDraw.Draw(img)
    # ---- map motif (right side): two landmasses + narrow strait + tanker ----
    land=(34,30,26); land_hi=(52,46,38)
    # north landmass (Iran side) — upper right blob
    d.polygon([(700,40),(1200,20),(1200,240),(1050,250),(960,210),(880,230),(800,180),(720,140)],fill=land)
    d.polygon([(760,70),(1150,50),(1150,160),(1000,190),(900,170),(820,130)],fill=land_hi)
    # south landmass (Arabian peninsula) — lower right blob with Musandam tip
    d.polygon([(760,630),(1200,630),(1200,420),(1080,400),(1010,330),(970,360),(920,440),(820,500)],fill=land)
    d.polygon([(850,610),(1150,610),(1150,470),(1040,440),(990,400),(950,470),(880,540)],fill=land_hi)
    # strait water glow between
    glow(img,985,295,150,(40,120,200),70)
    d=ImageDraw.Draw(img)
    # shipping lanes (dashed)
    for off,col in [(-14,(93,193,255,150)),(14,(93,193,255,90))]:
        for i in range(9):
            x0=780+i*46
            d.line([(x0,300+off+int(i*4)),(x0+26,298+off+int(i*4))],fill=col,width=5)
    # red pulse at narrowest point
    glow(img,985,295,46,(239,90,110),150)
    d=ImageDraw.Draw(img)
    d.ellipse([985-10,295-10,985+10,295+10],fill=RED)
    # tanker silhouette in the lane
    tx,ty=870,332
    d.polygon([(tx,ty),(tx+120,ty),(tx+138,ty+18),(tx+112,ty+34),(tx+8,ty+34),(tx-8,ty+18)],fill=(16,22,34))
    d.rectangle([tx+78,ty-18,tx+108,ty],fill=(16,22,34))
    d.rectangle([tx+84,ty-14,tx+96,ty-4],fill=(120,180,235))
    for i in range(4):
        d.rectangle([tx+10+i*16,ty+6,tx+22+i*16,ty+16],fill=(60,72,96))
    # ---- left text block ----
    d.rectangle([0,0,W,6],fill=GOLD)
    LX=76
    d.text((LX,92),"GLOBAL HOT ISSUE · DEEP REPORT",font=font("arialbd.ttf",24),fill=GOLD)
    f1=font("arialbd.ttf",84)
    d.text((LX,138),"STRAIT OF",font=f1,fill=WHITE)
    d.text((LX,226),"HORMUZ",font=f1,fill=GOLD)
    d.text((LX,356),cfg["sub"],font=font(cfg["font"],30),fill=DIM)
    f_chip=font("arialbd.ttf",23)
    chips=[("BRENT  $96 · +31%",RED),("OIL  20M b/d",GOLD),("LNG  20%+",BLUE)]
    cx,cy=LX,430
    for t,acc in chips:
        tb=d.textbbox((0,0),t,font=f_chip); w=tb[2]-tb[0]+50; h=tb[3]-tb[1]+20
        d.rounded_rectangle([cx,cy,cx+w,cy+h],h//2,fill=CHIP_BG,outline=CHIP_BD,width=1)
        d.ellipse([cx+16,cy+h//2-5,cx+26,cy+h//2+5],fill=acc)
        d.text((cx+34,cy+10-tb[1]),t,font=f_chip,fill=WHITE)
        cx+=w+14
    d.text((LX,H-76),"luckyplz.com",font=font("arialbd.ttf",26),fill=WHITE)
    meta="INDUSTRY · 2026.06.11"
    mb=d.textbbox((0,0),meta,font=font("arial.ttf",21))
    d.text((W-70-(mb[2]-mb[0]),H-72),meta,font=font("arial.ttf",21),fill=DIM)
    out=OG/f"strait-of-hormuz-economy{suf}.png"
    img.convert("RGB").save(out,"PNG",optimize=True)
    print(f"  wrote {out.name} ({out.stat().st_size//1024} KB)")
OG.mkdir(parents=True,exist_ok=True)
print("Generating Hormuz OG images:")
for suf,cfg in LANGS.items(): build(suf,cfg)
print("done.")
