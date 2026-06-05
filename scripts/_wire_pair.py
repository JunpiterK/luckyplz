# -*- coding: utf-8 -*-
# Reusable wiring for a ko-source post that already has agent-written -ja/-zh HTML.
# Edit SLUG + LINKS, then run. Idempotent-ish (skips if -ja already in posts.js).
import io, re, sys, json

SLUG = sys.argv[1] if len(sys.argv) > 1 else "spacex-ipo-risks"
# per-language internal-link rewrites: list of (from_path, to_path) applied as href="..."
CFG = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {
 "ja": [["/blog/how-to-buy-spacex-stock/","/blog/how-to-buy-spacex-stock-en/"],
        ["/blog/spacex-ipo-2026/","/blog/spacex-ipo-2026-en/"],
        ["/tools/spacex-countdown/","/tools/spacex-countdown-en/"],
        ["/tools/spacex-valuation/","/tools/spacex-valuation-en/"]],
 "zh": [["/blog/how-to-buy-spacex-stock/","/blog/how-to-buy-spacex-stock-en/"],
        ["/blog/spacex-ipo-2026/","/blog/spacex-ipo-2026-zh/"],
        ["/tools/spacex-countdown/","/tools/spacex-countdown-en/"],
        ["/tools/spacex-valuation/","/tools/spacex-valuation-en/"]],
}
BASE = "https://luckyplz.com/blog/" + SLUG
def rd(p): return io.open(p, encoding="utf-8").read()
def wr(p, s): io.open(p, "w", encoding="utf-8", newline="\n").write(s)

def patch_hreflang(html):
    en = f'<link rel="alternate" hreflang="en" href="{BASE}-en/">'
    ja = f'<link rel="alternate" hreflang="ja" href="{BASE}-ja/">'
    zh = f'<link rel="alternate" hreflang="zh" href="{BASE}-zh/">'
    if ja not in html:
        html = html.replace(en, en + "\n" + ja + "\n" + zh, 1)
    html = html.replace(
        f'<link rel="alternate" hreflang="x-default" href="{BASE}/">',
        f'<link rel="alternate" hreflang="x-default" href="{BASE}-en/">')
    return html

def meta(html, name=None, prop=None):
    if name: m = re.search(r'<meta name="'+name+r'" content="(.*?)">', html, re.S)
    else:    m = re.search(r'<meta property="'+prop+r'" content="(.*?)">', html, re.S)
    return m.group(1) if m else ""

def first_title(html):
    m = re.search(r'<title>(.*?)</title>', html, re.S)
    t = m.group(1) if m else ""
    return re.sub(r'\s*\|\s*Lucky Please\s*$', '', t).strip()

rec = {}
for lang in ("ja","zh"):
    p = f"public/blog/{SLUG}-{lang}/index.html"
    s = rd(p)
    htmllang = "ja" if lang=="ja" else "zh-Hans"
    loc = "ja_JP" if lang=="ja" else "zh_CN"
    suf = "-"+lang
    s = s.replace('<html lang="ko">', f'<html lang="{htmllang}">', 1)
    s = s.replace('"inLanguage":"ko"', f'"inLanguage":"{htmllang}"')
    if '<meta property="og:locale"' not in s:
        s = s.replace('<meta property="og:type" content="article">',
                      f'<meta property="og:type" content="article">\n<meta property="og:locale" content="{loc}">', 1)
    s = patch_hreflang(s)
    s = s.replace(f'<link rel="canonical" href="{BASE}/">', f'<link rel="canonical" href="{BASE}{suf}/">')
    s = s.replace(f'<meta property="og:url" content="{BASE}/">', f'<meta property="og:url" content="{BASE}{suf}/">')
    s = s.replace(f'"@id":"{BASE}/"', f'"@id":"{BASE}{suf}/"')
    s = s.replace(f'"item":"{BASE}/"', f'"item":"{BASE}{suf}/"')
    for a,b in CFG[lang]:
        s = s.replace(f'href="{a}"', f'href="{b}"')
    # same-series cross-episode links: fall back to -en (native ja/zh siblings may not all exist yet)
    if SLUG.startswith("ai-evo") or SLUG.startswith("space-evo"):
        pref = "ai-evo" if SLUG.startswith("ai-evo") else "space-evo"
        s = re.sub(r'href="/blog/('+pref+r'-\d+-[a-z0-9-]+?)/"',
                   lambda m: m.group(0) if m.group(1).endswith(('-en','-ja','-zh')) else f'href="/blog/{m.group(1)}-en/"', s)
    s = s.replace('lang=ko', 'lang='+lang)
    wr(p, s)
    kor = len(re.findall(r'[가-힣]', s))
    rec[lang] = dict(title=first_title(s), excerpt=(meta(s,prop="og:description") or meta(s,name="description")),
                     kw=meta(s,name="keywords"), kor=kor)
    print(f"[{lang}] head patched; real-Korean chars={kor}")

# ko + en hreflang
for p in (f"public/blog/{SLUG}/index.html", f"public/blog/{SLUG}-en/index.html"):
    s = rd(p); s2 = patch_hreflang(s)
    if s2 != s: wr(p, s2); print("[head] +ja/zh hreflang ->", p)

# posts.js
PJ = "public/blog/posts.js"; s = rd(PJ)
en_obj = re.search(r"\{[^{}]*slug: '"+re.escape(SLUG)+r"-en'[^{}]*\}", s, re.S).group(0)
def field(obj, key):
    m = re.search(key+r":\s*'([^']*)'", obj); return m.group(1) if m else ""
emoji = field(en_obj, "coverEmoji"); date = field(en_obj, "date")
cat = field(en_obj, "category"); rm = re.search(r"readMinutes:\s*(\d+)", en_obj)
rm = rm.group(1) if rm else "8"
def tags_of(kw):
    parts = [t.strip() for t in kw.split(",") if t.strip() and t.strip().lower()!="lucky please"]
    return parts[:7]
def esc(v): return v.replace("\\","\\\\").replace("'","\\'")
def obj_for(lang):
    r = rec[lang]
    tg = ", ".join("'"+esc(t)+"'" for t in tags_of(r["kw"]))
    return ("    {\n"
        f"        slug: '{SLUG}-{lang}',\n        lang: '{lang}',\n        category: '{cat}',\n"
        f"        date: '{date}',\n        readMinutes: {rm},\n        coverEmoji: '{emoji}',\n"
        f"        tags: [{tg}],\n        title: '{esc(r['title'])}',\n        excerpt: '{esc(r['excerpt'])}',\n"
        f"        alt: '{SLUG}',\n    }}")
if SLUG+"-ja'" in s:
    print("[posts.js] ja present — skip")
else:
    i = s.index("slug: '"+SLUG+"-en'"); close = s.index("},", i); ins = close+2
    s = s[:ins] + "\n" + obj_for("ja") + ",\n" + obj_for("zh") + "," + s[ins:]
    assert s.count(SLUG+"-ja'")==1 and s.count(SLUG+"-zh'")==1
    # validate JS
    import subprocess
    wr(PJ, s); print("[posts.js] inserted ja + zh")

# sitemap
SM = "public/sitemap.xml"; s = rd(SM)
def xh(c,h): return f'        <xhtml:link rel="alternate" hreflang="{c}" href="{h}"/>'
NEW5 = "\n".join([xh("ko",BASE+"/"),xh("en",BASE+"-en/"),xh("ja",BASE+"-ja/"),xh("zh",BASE+"-zh/"),xh("x-default",BASE+"-en/")])
if BASE+"-ja/</loc>" in s:
    print("[sitemap] ja present — skip")
else:
    found = 0
    for xdef in (BASE+"-en/", BASE+"/"):
        OLD3 = "\n".join([xh("ko",BASE+"/"),xh("en",BASE+"-en/"),xh("x-default",xdef)])
        c = s.count(OLD3)
        if c: s = s.replace(OLD3, NEW5); found += c
    def blk(suf):
        return ("\n    <url>\n"
            f"        <loc>{BASE}{suf}/</loc>\n        <lastmod>2026-06-06</lastmod>\n"
            "        <changefreq>weekly</changefreq>\n        <priority>0.85</priority>\n"+NEW5+"\n    </url>\n")
    j = s.index(BASE+"-en/</loc>"); endurl = s.index("</url>", j)+len("</url>")
    s = s[:endurl] + "\n" + blk("-ja") + blk("-zh").rstrip("\n") + s[endurl:]
    assert s.count(BASE+"-ja/</loc>")==1 and s.count(BASE+"-zh/</loc>")==1
    wr(SM, s); print(f"[sitemap] OLD3 replaced={found}; inserted ja+zh blocks")
print("DONE", SLUG)
