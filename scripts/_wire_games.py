# -*- coding: utf-8 -*-
# Wire a ko-ONLY gaming-history post that now has agent-written -en/-ja/-zh.
# These older posts have NO hreflang block / no inLanguage / no og:locale.
# Usage: python _wire_games.py <base-slug>
import io, re, sys, json
SLUG = sys.argv[1]
BASE = "https://luckyplz.com/blog/" + SLUG
# cross-link family (links to these base slugs become -en in the en/ja/zh files)
GH = json.loads(sys.argv[2]) if len(sys.argv) > 2 else [
      "breakout-jobs-wozniak","burgertime-arcade-history","pacman-history-namco",
      "snake-history-nokia","tetris-history-soviet"]
def rd(p): return io.open(p, encoding="utf-8").read()
def wr(p, s): io.open(p, "w", encoding="utf-8", newline="\n").write(s)

CANON = f'<link rel="canonical" href="{BASE}/">'
def hreflang5(canon_indent=""):
    L=[f'<link rel="alternate" hreflang="ko" href="{BASE}/">',
       f'<link rel="alternate" hreflang="en" href="{BASE}-en/">',
       f'<link rel="alternate" hreflang="ja" href="{BASE}-ja/">',
       f'<link rel="alternate" hreflang="zh" href="{BASE}-zh/">',
       f'<link rel="alternate" hreflang="x-default" href="{BASE}-en/">']
    return ("\n"+canon_indent).join(L)
def insert_hreflang(s):
    if f'hreflang="en" href="{BASE}-en/"' in s: return s  # already
    # case (b): existing ko + x-default(->ko) pair -> replace with 5-line block
    m2=re.search(r'([ \t]*)<link rel="alternate" hreflang="ko" href="'+re.escape(BASE)+
                 r'/">\s*\n[ \t]*<link rel="alternate" hreflang="x-default" href="'+re.escape(BASE)+r'/">', s)
    if m2:
        indent=m2.group(1)
        return s.replace(m2.group(0), indent+hreflang5(indent), 1)
    # case (a): no hreflang -> insert after canonical
    m=re.search(r'([ \t]*)'+re.escape(CANON), s)
    if not m: return s
    indent=m.group(1)
    block = m.group(0) + "\n" + indent + hreflang5(indent)
    return s.replace(m.group(0), block, 1)

HMAP={"en":("en","en_US"),"ja":("ja","ja_JP"),"zh":("zh-Hans","zh_CN")}
GHRE=re.compile(r'href="/blog/('+"|".join(map(re.escape,GH))+r')/"')

def meta(html,name=None,prop=None):
    pat=(r'<meta name="'+name+r'" content="(.*?)">') if name else (r'<meta property="'+prop+r'" content="(.*?)">')
    m=re.search(pat,html,re.S); return m.group(1) if m else ""
def first_title(html):
    m=re.search(r'<title>(.*?)</title>',html,re.S); t=m.group(1) if m else ""
    return re.sub(r'\s*\|\s*Lucky Please\s*$','',t).strip()

rec={}
for L in ("en","ja","zh"):
    p=f"public/blog/{SLUG}-{L}/index.html"; s=rd(p)
    htmllang,loc=HMAP[L]; suf="-"+L
    s=s.replace('<html lang="ko">',f'<html lang="{htmllang}">',1)
    # inLanguage: replace if present else insert into BlogPosting
    if '"inLanguage":"ko"' in s:
        s=s.replace('"inLanguage":"ko"',f'"inLanguage":"{htmllang}"')
    else:
        s=s.replace('"@type":"BlogPosting",', f'"@type":"BlogPosting","inLanguage":"{htmllang}",',1)
    # og:locale insert after og:type
    if '<meta property="og:locale"' not in s:
        s=re.sub(r'(<meta property="og:type" content="article">)',
                 r'\1\n    <meta property="og:locale" content="'+loc+'">', s, count=1)
    s=insert_hreflang(s)
    s=s.replace(CANON, f'<link rel="canonical" href="{BASE}{suf}/">')
    s=s.replace(f'<meta property="og:url" content="{BASE}/">', f'<meta property="og:url" content="{BASE}{suf}/">')
    s=s.replace(f'"@id":"{BASE}/"', f'"@id":"{BASE}{suf}/"')
    s=s.replace(f'"item":"{BASE}/"', f'"item":"{BASE}{suf}/"')
    # gaming-history cross-links -> -en (siblings incremental); /games/ untouched
    s=GHRE.sub(lambda m: f'href="/blog/{m.group(1)}-en/"', s)
    s=s.replace('lang=ko','lang='+L)
    wr(p,s)
    vis=re.sub(r'<!--.*?-->','',s,flags=re.S)
    rec[L]=dict(title=first_title(s),excerpt=(meta(s,prop="og:description") or meta(s,name="description")),
                kw=meta(s,name="keywords"),kor=len(re.findall(r'[가-힣]',vis)))
    print(f"[{L}] patched; visible-Korean={rec[L]['kor']}")

# ko head: insert hreflang after canonical
kp=f"public/blog/{SLUG}/index.html"; s=rd(kp)
s2=insert_hreflang(s)
if s2!=s: wr(kp,s2); print("[ko] hreflang inserted")
else: print("[ko] hreflang present/skip")

# posts.js
PJ="public/blog/posts.js"; s=rd(PJ)
ko_obj=re.search(r"\{[^{}]*slug: '"+re.escape(SLUG)+r"'[^{}]*\}",s,re.S).group(0)
def f1(o,k):
    m=re.search(k+r":\s*'([^']*)'",o); return m.group(1) if m else ""
emoji=f1(ko_obj,"coverEmoji"); date=f1(ko_obj,"date"); cat=f1(ko_obj,"category")
rmm=re.search(r"readMinutes:\s*(\d+)",ko_obj); rm=rmm.group(1) if rmm else "6"
def tags_of(kw): return [t.strip() for t in kw.split(",") if t.strip() and t.strip().lower()!="lucky please"][:7]
def esc(v): return v.replace("\\","\\\\").replace("'","\\'")
def objfor(L):
    r=rec[L]; tg=", ".join("'"+esc(t)+"'" for t in tags_of(r["kw"]))
    return ("    {\n"
        f"        slug: '{SLUG}-{L}',\n        lang: '{L}',\n        category: '{cat}',\n"
        f"        date: '{date}',\n        readMinutes: {rm},\n        coverEmoji: '{emoji}',\n"
        f"        tags: [{tg}],\n        title: '{esc(r['title'])}',\n        excerpt: '{esc(r['excerpt'])}',\n"
        f"        alt: '{SLUG}',\n    }}")
if SLUG+"-en'" in s:
    print("[posts.js] present — skip")
else:
    i=s.index("slug: '"+SLUG+"'"); close=s.index("},",i); ins=close+2
    s=s[:ins]+"\n"+objfor("en")+",\n"+objfor("ja")+",\n"+objfor("zh")+","+s[ins:]
    for L in ("en","ja","zh"): assert s.count(f"{SLUG}-{L}'")==1
    wr(PJ,s); print("[posts.js] inserted en+ja+zh")

# sitemap (ko block may have no alternates)
SM="public/sitemap.xml"; s=rd(SM)
def xh(c,h): return f'        <xhtml:link rel="alternate" hreflang="{c}" href="{h}"/>'
ALT5="\n".join([xh("ko",BASE+"/"),xh("en",BASE+"-en/"),xh("ja",BASE+"-ja/"),xh("zh",BASE+"-zh/"),xh("x-default",BASE+"-en/")])
if BASE+"-en/</loc>" in s:
    print("[sitemap] present — skip")
elif f"<loc>{BASE}/</loc>" in s:
    loc=f"<loc>{BASE}/</loc>"; i=s.index(loc)
    if "<xhtml:link" in s[i:s.index("</url>",i)]:
        # already has alternates somehow; just append blocks
        pass
    else:
        endurl=s.index("</url>",i); s=s[:endurl]+ALT5+"\n    "+s[endurl:]
    def blk(suf):
        return ("\n    <url>\n"
            f"        <loc>{BASE}{suf}/</loc>\n        <lastmod>2026-06-06</lastmod>\n"
            "        <changefreq>monthly</changefreq>\n        <priority>0.7</priority>\n"+ALT5+"\n    </url>\n")
    endurl2=s.index("</url>", s.index(loc))+len("</url>")
    s=s[:endurl2]+"\n"+blk("-en")+blk("-ja")+blk("-zh").rstrip("\n")+s[endurl2:]
    for L in ("en","ja","zh"): assert s.count(f"{BASE}-{L}/</loc>")==1
    wr(SM,s); print("[sitemap] ko alternates + en/ja/zh blocks")
else:
    print("[sitemap] WARN: ko loc not found — manual sitemap needed")
print("DONE",SLUG)
