# -*- coding: utf-8 -*-
# Wire a ko-ONLY base post that now has agent-written -en/-ja/-zh siblings.
# Adds en/ja/zh hreflang to all 4 files, patches new heads, inserts 3 posts.js
# entries + 4-lang sitemap. Usage: python _wire_triple.py <base-slug>
import io, re, sys
SLUG = sys.argv[1]
BASE = "https://luckyplz.com/blog/" + SLUG
SERIES = SLUG.split("-")[0] + "-" + SLUG.split("-")[1] if SLUG.startswith(("space-evo","ai-evo")) else None
def rd(p): return io.open(p, encoding="utf-8").read()
def wr(p, s): io.open(p, "w", encoding="utf-8", newline="\n").write(s)

OLD2 = (f'<link rel="alternate" hreflang="ko" href="{BASE}/">\n'
        f'<link rel="alternate" hreflang="x-default" href="{BASE}/">')
NEW5 = "\n".join([
    f'<link rel="alternate" hreflang="ko" href="{BASE}/">',
    f'<link rel="alternate" hreflang="en" href="{BASE}-en/">',
    f'<link rel="alternate" hreflang="ja" href="{BASE}-ja/">',
    f'<link rel="alternate" hreflang="zh" href="{BASE}-zh/">',
    f'<link rel="alternate" hreflang="x-default" href="{BASE}-en/">'])

HMAP = {"en":("en","en_US","en"), "ja":("ja","ja_JP","ja"), "zh":("zh-Hans","zh_CN","zh-Hans")}
LINKS = {
 "en": {"/blog/how-to-buy-spacex-stock/":"-en","/blog/spacex-ipo-2026/":"-en","/blog/spacex-ipo-risks/":"-en"},
 "ja": {"/blog/how-to-buy-spacex-stock/":"-en","/blog/spacex-ipo-2026/":"-en","/blog/spacex-ipo-risks/":"-ja"},
 "zh": {"/blog/how-to-buy-spacex-stock/":"-en","/blog/spacex-ipo-2026/":"-zh","/blog/spacex-ipo-risks/":"-zh"},
}
def meta(html, name=None, prop=None):
    pat = (r'<meta name="'+name+r'" content="(.*?)">') if name else (r'<meta property="'+prop+r'" content="(.*?)">')
    m = re.search(pat, html, re.S); return m.group(1) if m else ""
def first_title(html):
    m = re.search(r'<title>(.*?)</title>', html, re.S); t = m.group(1) if m else ""
    return re.sub(r'\s*\|\s*Lucky Please\s*$', '', t).strip()

rec = {}
for L in ("en","ja","zh"):
    p = f"public/blog/{SLUG}-{L}/index.html"; s = rd(p)
    htmllang, loc, inlang = HMAP[L]; suf = "-"+L
    s = s.replace('<html lang="ko">', f'<html lang="{htmllang}">', 1)
    s = s.replace('"inLanguage":"ko"', f'"inLanguage":"{inlang}"')
    if '<meta property="og:locale"' not in s:
        s = s.replace('<meta property="og:type" content="article">',
                      f'<meta property="og:type" content="article">\n<meta property="og:locale" content="{loc}">', 1)
    if OLD2 in s: s = s.replace(OLD2, NEW5)
    s = s.replace(f'<link rel="canonical" href="{BASE}/">', f'<link rel="canonical" href="{BASE}{suf}/">')
    s = s.replace(f'<meta property="og:url" content="{BASE}/">', f'<meta property="og:url" content="{BASE}{suf}/">')
    s = s.replace(f'"@id":"{BASE}/"', f'"@id":"{BASE}{suf}/"')
    s = s.replace(f'"item":"{BASE}/"', f'"item":"{BASE}{suf}/"')
    for frm, sfx in LINKS[L].items():
        s = s.replace(f'href="{frm}"', f'href="{frm[:-1]}{sfx}/"')
    if SERIES:
        s = re.sub(r'href="/blog/('+re.escape(SERIES)+r'-\d+-[a-z0-9-]+?)/"',
                   lambda m: m.group(0) if m.group(1).endswith(('-en','-ja','-zh')) else f'href="/blog/{m.group(1)}-en/"', s)
    s = s.replace('lang=ko', 'lang='+L)
    wr(p, s)
    vis = re.sub(r'<!--.*?-->','',s,flags=re.S)
    rec[L] = dict(title=first_title(s), excerpt=(meta(s,prop="og:description") or meta(s,name="description")),
                  kw=meta(s,name="keywords"), kor=len(re.findall(r'[가-힣]',vis)))
    print(f"[{L}] head patched; visible-Korean={rec[L]['kor']}")

# ko head: add 5-line hreflang
kp = f"public/blog/{SLUG}/index.html"; s = rd(kp)
if OLD2 in s: wr(kp, s.replace(OLD2, NEW5)); print("[ko] hreflang -> 5 langs")
else: print("[ko] hreflang anchor not found (already patched?)")

# posts.js: derive shared fields from ko entry, add en/ja/zh
PJ = "public/blog/posts.js"; s = rd(PJ)
ko_obj = re.search(r"\{[^{}]*slug: '"+re.escape(SLUG)+r"'[^{}]*\}", s, re.S).group(0)
def f1(obj,k):
    m=re.search(k+r":\s*'([^']*)'",obj); return m.group(1) if m else ""
emoji=f1(ko_obj,"coverEmoji"); date=f1(ko_obj,"date"); cat=f1(ko_obj,"category")
rmm=re.search(r"readMinutes:\s*(\d+)",ko_obj); rm=rmm.group(1) if rmm else "8"
def tags_of(kw):
    return [t.strip() for t in kw.split(",") if t.strip() and t.strip().lower()!="lucky please"][:7]
def esc(v): return v.replace("\\","\\\\").replace("'","\\'")
def objfor(L):
    r=rec[L]; tg=", ".join("'"+esc(t)+"'" for t in tags_of(r["kw"]))
    return ("    {\n"
        f"        slug: '{SLUG}-{L}',\n        lang: '{L}',\n        category: '{cat}',\n"
        f"        date: '{date}',\n        readMinutes: {rm},\n        coverEmoji: '{emoji}',\n"
        f"        tags: [{tg}],\n        title: '{esc(r['title'])}',\n        excerpt: '{esc(r['excerpt'])}',\n"
        f"        alt: '{SLUG}',\n    }}")
if SLUG+"-en'" in s:
    print("[posts.js] already present — skip")
else:
    i=s.index("slug: '"+SLUG+"'"); close=s.index("},",i); ins=close+2
    add="\n"+objfor("en")+",\n"+objfor("ja")+",\n"+objfor("zh")+","
    s=s[:ins]+add+s[ins:]
    for L in ("en","ja","zh"): assert s.count(f"{SLUG}-{L}'")==1
    wr(PJ,s); print("[posts.js] inserted en+ja+zh")

# sitemap: add alternates to ko block (no alternates currently) + 3 url blocks
SM="public/sitemap.xml"; s=rd(SM)
def xh(c,h): return f'        <xhtml:link rel="alternate" hreflang="{c}" href="{h}"/>'
ALT5="\n".join([xh("ko",BASE+"/"),xh("en",BASE+"-en/"),xh("ja",BASE+"-ja/"),xh("zh",BASE+"-zh/"),xh("x-default",BASE+"-en/")])
if BASE+"-en/</loc>" in s:
    print("[sitemap] already present — skip")
else:
    # insert ALT5 before </url> of the ko block
    loc=f"<loc>{BASE}/</loc>"; i=s.index(loc); endurl=s.index("</url>",i)
    s=s[:endurl]+ALT5+"\n    "+s[endurl:]
    def blk(suf):
        return ("\n    <url>\n"
            f"        <loc>{BASE}{suf}/</loc>\n        <lastmod>2026-06-06</lastmod>\n"
            "        <changefreq>monthly</changefreq>\n        <priority>0.85</priority>\n"+ALT5+"\n    </url>\n")
    endurl2=s.index("</url>", s.index(loc))+len("</url>")
    s=s[:endurl2]+"\n"+blk("-en")+blk("-ja")+blk("-zh").rstrip("\n")+s[endurl2:]
    for L in ("en","ja","zh"): assert s.count(f"{BASE}-{L}/</loc>")==1
    wr(SM,s); print("[sitemap] ko alternates + en/ja/zh blocks")
print("DONE", SLUG)
