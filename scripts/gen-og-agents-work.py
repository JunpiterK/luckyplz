#!/usr/bin/env python3
"""OG images for the 'Agents at Work' deep report (4 langs) — workflow handoff motif."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT=Path(__file__).resolve().parent.parent; OG=ROOT/"public"/"og"; FONTS=Path("C:/Windows/Fonts")
W,H=1200,630
WHITE=(245,247,250);DIM=(158,168,186);GREEN=(95,224,168);GOLD=(255,206,92);AUB=(232,120,72);BLUE=(93,193,255)
CHIP_BG=(12,15,24);CHIP_BD=(48,60,86)
LANGS={
 "":   {"font":"malgunbd.ttf","sub":"실제 사례로 보는 에이전트의 일 대체 워크플로우"},
 "-en":{"font":"arialbd.ttf","sub":"How agents take over work, drawn from real cases"},
 "-ja":{"font":"YuGothB.ttc","sub":"実事例で見るエージェントの仕事代替ワークフロー"},
 "-zh":{"font":"msyhbd.ttc","sub":"用真实案例还原智能体的工作代替流程"},
}
def font(n,s): return ImageFont.truetype(str(FONTS/n),s)
def vgrad(t,b):
    base=Image.new("RGB",(W,H),t); g=Image.new("L",(1,H))
    for y in range(H): g.putpixel((0,y),int(y/(H-1)*255))
    return Image.composite(Image.new("RGB",(W,H),b),base,g.resize((W,H))).convert("RGBA")
def glow(img,cx,cy,r,c,a):
    l=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(l)
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=c+(a,)); img.alpha_composite(l.filter(ImageFilter.GaussianBlur(r//2)))
def chip(d,x,y,label,tag,acc):
    bx0,by0,bx1,by1=x,y,x+360,y+58
    d.rounded_rectangle([bx0,by0,bx1,by1],12,fill=(16,20,30),outline=(40,52,74),width=2)
    # tag pill
    fT=font("arialbd.ttf",18)
    tb=d.textbbox((0,0),tag,font=fT); tw=tb[2]-tb[0]
    d.rounded_rectangle([bx0+14,by0+14,bx0+14+tw+22,by1-14],8,fill=acc)
    tc=(255,255,255) if tag=="AGENT" else (60,42,10)
    d.text((bx0+25,by0+18-tb[1]),tag,font=fT,fill=tc)
    fL=font("malgunbd.ttf",21)
    d.text((bx0+14+tw+40,by0+16),label,font=fL,fill=WHITE)
    return by1
def build(suf,cfg):
    img=vgrad((10,9,22),(4,4,11))
    glow(img,1010,110,300,GREEN,32); glow(img,150,560,260,GOLD,24)
    d=ImageDraw.Draw(img)
    d.rectangle([0,0,W,6],fill=GREEN)
    # ---- right: workflow handoff column ----
    cx=970
    rows=[("AGENT",GREEN,"접수·분류"),("AGENT",GREEN,"조회·실행"),("HUMAN",GOLD,"검수·판단"),("HUMAN",GOLD,"책임·관계")]
    if suf:
        rows=[("AGENT",GREEN,"Intake"),("AGENT",GREEN,"Resolve"),("HUMAN",GOLD,"Review"),("HUMAN",GOLD,"Decide")]
    y=120
    prev=None
    for tag,acc,lab in rows:
        # connector
        if prev is not None:
            d.line([cx,prev,cx,y],fill=(70,82,108),width=4)
            d.polygon([(cx-7,y-12),(cx+7,y-12),(cx,y-2)],fill=(70,82,108))
        end=chip(d,cx-180,y,lab,tag,acc)
        prev=end; y=end+34
    # ---- left text ----
    LX=76
    d.text((LX,92),"AGENTS AT WORK · DEEP REPORT",font=font("arialbd.ttf",24),fill=GREEN)
    f1=font("arialbd.ttf",82)
    d.text((LX,140),"WHO DOES",font=f1,fill=WHITE)
    d.text((LX,224),"THE WORK?",font=f1,fill=GREEN)
    d.text((LX,346),cfg["sub"],font=font(cfg["font"],28),fill=DIM)
    f_chip=font("arialbd.ttf",22)
    chips=[("KLARNA  700",GREEN),("HARVEY  2wk\u21921d",GOLD),("ABRIDGE  150+",BLUE)]
    cxp,cy=LX,420
    for t,a in chips:
        tb=d.textbbox((0,0),t,font=f_chip); w=tb[2]-tb[0]+48; h=tb[3]-tb[1]+20
        d.rounded_rectangle([cxp,cy,cxp+w,cy+h],h//2,fill=CHIP_BG,outline=CHIP_BD,width=1)
        d.ellipse([cxp+15,cy+h//2-5,cxp+25,cy+h//2+5],fill=a)
        d.text((cxp+33,cy+10-tb[1]),t,font=f_chip,fill=WHITE)
        cxp+=w+13
    d.text((LX,H-76),"luckyplz.com",font=font("arialbd.ttf",26),fill=WHITE)
    meta="AI TECH · 2026.06.12"
    mb=d.textbbox((0,0),meta,font=font("arial.ttf",21))
    d.text((W-70-(mb[2]-mb[0]),H-72),meta,font=font("arial.ttf",21),fill=DIM)
    out=OG/f"ai-agents-replacing-work{suf}.png"
    img.convert("RGB").save(out,"PNG",optimize=True)
    print(f"  wrote {out.name} ({out.stat().st_size//1024} KB)")
OG.mkdir(parents=True,exist_ok=True)
print("Generating Agents-at-Work OG images:")
for suf,cfg in LANGS.items(): build(suf,cfg)
print("done.")
