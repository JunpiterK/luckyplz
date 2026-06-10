#!/usr/bin/env python3
"""OG images for the Agentic AI deep report (4 langs) — orchestration graph motif."""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OG = ROOT / "public" / "og"
FONTS = Path("C:/Windows/Fonts")
W, H = 1200, 630
WHITE=(245,247,250); DIM=(158,168,186); PURPLE=(167,139,250); GREEN=(95,224,168); BLUE=(93,193,255); GOLD=(255,206,92)
CHIP_BG=(12,15,24); CHIP_BD=(48,60,86)
LANGS={
 "":   {"font":"malgunbd.ttf","sub":"묻고 답하는 챗봇에서, 맡기면 끝내는 에이전트로"},
 "-en":{"font":"arialbd.ttf","sub":"From chatbots that answer to agents that finish the job"},
 "-ja":{"font":"YuGothB.ttc","sub":"答えるチャットボットから、任せれば終わらせるエージェントへ"},
 "-zh":{"font":"msyhbd.ttc","sub":"从一问一答的聊天机器人，到交给它就能办完的智能体"},
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
    img=vgrad((10,9,24),(4,3,11))
    glow(img,1000,120,300,PURPLE,40); glow(img,140,580,280,BLUE,30)
    d=ImageDraw.Draw(img)
    d.rectangle([0,0,W,6],fill=PURPLE)
    # ---- orchestration graph (right side) ----
    ox,oy=965,250   # conductor node
    # two tiers of sub-agents
    tier1=[(835,120),(1105,110),(795,300),(1135,290)]
    tier2=[(755,200),(905,60),(1060,40),(1165,190),(820,420),(950,470),(1085,430),(1170,520),(870,540)]
    # edges conductor->tier1 (bright), tier1->tier2 (dim)
    for tx,ty in tier1:
        d.line([ox,oy,tx,ty],fill=(167,139,250,200),width=4)
    pair=[(0,0),(0,1),(1,2),(1,3),(2,4),(2,5),(3,6),(3,7),(2,8)]
    for a,b in pair:
        ax,ay=tier1[a%len(tier1)]; bx,by=tier2[b]
        d.line([ax,ay,bx,by],fill=(93,193,255,120),width=3)
    # tier2 nodes (small, green=done / blue=running)
    for i,(x,y) in enumerate(tier2):
        c=GREEN if i%3==0 else BLUE
        d.ellipse([x-13,y-13,x+13,y+13],fill=(14,18,30),outline=c,width=4)
        if i%3==0:  # check mark for done
            d.line([x-6,y,x-1,y+5],fill=GREEN,width=3); d.line([x-1,y+5,x+7,y-5],fill=GREEN,width=3)
    # tier1 nodes
    for x,y in tier1:
        d.ellipse([x-22,y-22,x+22,y+22],fill=(18,16,36),outline=PURPLE,width=5)
        d.ellipse([x-7,y-7,x+7,y+7],fill=PURPLE)
    # conductor node (big)
    glow(img,ox,oy,70,PURPLE,120)
    d=ImageDraw.Draw(img)
    d.ellipse([ox-44,oy-44,ox+44,oy+44],fill=(24,20,46),outline=PURPLE,width=6)
    f_n=font("arialbd.ttf",30)
    tb=d.textbbox((0,0),"AI",font=f_n)
    d.text((ox-(tb[2]-tb[0])/2,oy-(tb[3]-tb[1])/2-tb[1]),"AI",font=f_n,fill=WHITE)
    # ---- left text ----
    LX=76
    d.text((LX,92),"AI HOT TECH · DEEP REPORT",font=font("arialbd.ttf",24),fill=PURPLE)
    f1=font("arialbd.ttf",92)
    d.text((LX,138),"AGENTIC",font=f1,fill=WHITE)
    d.text((LX,232),"AI",font=f1,fill=PURPLE)
    d.text((LX,362),cfg["sub"],font=font(cfg["font"],29),fill=DIM)
    f_chip=font("arialbd.ttf",23)
    chips=[("5 MONTHS → DAYS",GREEN),("SWE-BENCH  80.3",PURPLE),("ADOPTION  40%",BLUE)]
    cx,cy=LX,436
    for t,acc in chips:
        tb=d.textbbox((0,0),t,font=f_chip); w=tb[2]-tb[0]+50; h=tb[3]-tb[1]+20
        d.rounded_rectangle([cx,cy,cx+w,cy+h],h//2,fill=CHIP_BG,outline=CHIP_BD,width=1)
        d.ellipse([cx+16,cy+h//2-5,cx+26,cy+h//2+5],fill=acc)
        d.text((cx+34,cy+10-tb[1]),t,font=f_chip,fill=WHITE)
        cx+=w+14
    d.text((LX,H-76),"luckyplz.com",font=font("arialbd.ttf",26),fill=WHITE)
    meta="AI TECH · 2026.06.11"
    mb=d.textbbox((0,0),meta,font=font("arial.ttf",21))
    d.text((W-70-(mb[2]-mb[0]),H-72),meta,font=font("arial.ttf",21),fill=DIM)
    out=OG/f"agentic-ai-explained{suf}.png"
    img.convert("RGB").save(out,"PNG",optimize=True)
    print(f"  wrote {out.name} ({out.stat().st_size//1024} KB)")
OG.mkdir(parents=True,exist_ok=True)
print("Generating Agentic AI OG images:")
for suf,cfg in LANGS.items(): build(suf,cfg)
print("done.")
