#!/usr/bin/env python3
# 金沢まるっと：検索エンジン向けの静的ページ（カード1枚=1ページ）・sitemap.xml・robots.txt を作る
# 使い方: python3 tools/gen_seo.py  （リポジトリの一番上で実行。index.html を読んで c/ を作り直す）
import re, html, json, os, datetime
BASE='https://kanazawa-marutto.jp/'
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
s=open('index.html',encoding='utf-8').read()
today=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d')

def noruby(x): return re.sub(r'<rp>.*?</rp>|<rt>.*?</rt>','',x,flags=re.S)
def text(x):
    x=noruby(x)
    x=re.sub(r'<(br|/p|/div|/li|/h\d)[^>]*>',' ',x)
    x=re.sub(r'<[^>]+>','',x)
    return re.sub(r'\s+',' ',html.unescape(x)).strip()

cards=[]
for cid,body in re.findall(r'<script type="text/html" id="lazy-([^"]+)">(.*?)</script>',s,re.S):
    b=noruby(body)
    m=re.search(r'<h2[^>]*>(.*?)</h2>',b,re.S)
    title=text(m.group(1)) if m else cid
    note=re.search(r'<span class="note">(.*?)</span>',b,re.S)
    intro=re.search(r'<p class="rn-intro">(.*?)</p>',b,re.S) or re.search(r'<p[^>]*>(.*?)</p>',b,re.S)
    desc=text(intro.group(1)) if intro else ''
    if note: desc=text(note.group(1))+'。'+desc
    desc=(desc[:118]+'…') if len(desc)>120 else desc
    # タブの見出しを本文の見出しに置きかえる（タブは全部ひらいた形で載せる）
    labels={}
    for tm in re.finditer(r'<div class="rn-tabs"[^>]*>(.*?)</div>',b,re.S):
        for bm in re.finditer(r'<button[^>]*data-p="([^"]+)"[^>]*>(.*?)</button>',tm.group(1),re.S):
            labels[bm.group(1)]=text(bm.group(2))
    b=re.sub(r'<div class="rn-tabs"[^>]*>.*?</div>','',b,flags=re.S)
    def sec(mm):
        pid=mm.group(1); lab=labels.get(pid,'')
        return (f'<h2 class="tab-h">{html.escape(lab)}</h2>' if lab else '')+mm.group(0)
    b=re.sub(r'<section class="rn-panel[^"]*" id="([^"]+)"[^>]*>',sec,b)
    b=re.sub(r'<div class="sec-head[^"]*"[^>]*>.*?</div>','',b,count=1,flags=re.S)
    b=re.sub(r'<h2[^>]*>\s*'+re.escape(title)+r'\s*</h2>','',b,count=1)
    b=re.sub(r'<button[^>]*class="cat-close"[^>]*>.*?</button>','',b,flags=re.S)
    b=re.sub(r'\son[a-z]+="[^"]*"','',b)
    b=re.sub(r'<script.*?</script>','',b,flags=re.S)
    b=re.sub(r'href="#([A-Za-z0-9_-]+)"',lambda mm:f'href="{BASE}#{mm.group(1)}"',b)
    b=re.sub(r'(src|href)="(?!https?:|data:|#|/|mailto:|tel:)([^"]+)"',r'\1="../\2"',b)
    cards.append((cid,title,desc,b))

CSS='''body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif;background:#f7f4ec;color:#1e2733;line-height:1.8}
.w{max-width:760px;margin:0 auto;padding:16px}
a{color:#9a7420}
header.top{background:#123a5c;color:#fff;padding:10px 16px}header.top a{color:#fff;text-decoration:none;font-weight:800}
h1{font-size:24px;line-height:1.4;margin:16px 0 6px}
.lead{color:#5a6675;font-size:14px}
.open{display:inline-block;margin:10px 0 18px;background:#c9a24b;color:#fff;border-radius:999px;padding:8px 16px;font-weight:800;text-decoration:none}
.tab-h{font-size:19px;border-left:5px solid #c9a24b;padding-left:8px;margin:28px 0 8px}
details{background:#fff;border:1px solid #e2dccd;border-radius:10px;margin:8px 0;padding:6px 10px}
summary{cursor:pointer;font-weight:700}
img{max-width:100%;height:auto}
table{border-collapse:collapse;max-width:100%;display:block;overflow-x:auto}td,th{border:1px solid #e2dccd;padding:4px 6px}
nav.all{margin-top:32px;border-top:2px dashed #e2dccd;padding-top:12px;font-size:14px}nav.all a{display:inline-block;margin:3px 10px 3px 0}
footer{color:#5a6675;font-size:12px;margin:24px 0}'''

def page(cid,title,desc,body,nav):
    url=f'{BASE}c/{cid}.html'
    ld={"@context":"https://schema.org","@type":"Article","headline":title,"description":desc,"inLanguage":"ja","dateModified":today,
        "mainEntityOfPage":url,"isPartOf":{"@type":"WebSite","name":"金沢まるっと","url":BASE},
        "publisher":{"@type":"Organization","name":"金沢まるっと","url":BASE}}
    bc={"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"金沢まるっと","item":BASE},
        {"@type":"ListItem","position":2,"name":"カード一覧","item":BASE+"c/"},
        {"@type":"ListItem","position":3,"name":title,"item":url}]}
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}｜金沢まるっと</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<link rel="icon" href="../favicon.png">
<meta property="og:type" content="article"><meta property="og:site_name" content="金沢まるっと">
<meta property="og:title" content="{html.escape(title)}｜金沢まるっと"><meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}marutto.jpg">
<script type="application/ld+json">{json.dumps(ld,ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(bc,ensure_ascii=False)}</script>
<style>{CSS}</style></head>
<body><header class="top"><a href="{BASE}">金沢まるっと</a>｜金沢のこと、まるっとわかるサイト</header>
<main class="w"><h1>{html.escape(title)}</h1><p class="lead">{html.escape(desc)}</p>
<a class="open" href="{BASE}#{cid}">▶ 金沢まるっとで、このカードをひらく</a>
{body}
<nav class="all"><b>ほかのカード</b><br>{nav}</nav>
<footer>金沢まるっと（{BASE}）｜公に公表されている資料をもとに、金沢のことをわかりやすくまとめた市民のための情報サイトです。最終更新：{today}</footer>
</main></body></html>
'''
os.makedirs('c',exist_ok=True)
nav=' '.join(f'<a href="{cid}.html">{html.escape(t)}</a>' for cid,t,_,_ in cards)
keep=set()
for cid,t,d,b in cards:
    open(f'c/{cid}.html','w',encoding='utf-8').write(page(cid,t,d,b,nav)); keep.add(f'{cid}.html')
lst=''.join(f'<li><a href="{cid}.html">{html.escape(t)}</a>　<span class="lead">{html.escape(d[:60])}</span></li>' for cid,t,d,_ in cards)
open('c/index.html','w',encoding='utf-8').write(page('index','金沢まるっと カード一覧','金沢の議会・予算・税金・歴史・文化・くらしを、カードごとにまとめた一覧です。',f'<ul>{lst}</ul>',nav).replace(f'{BASE}c/index.html',f'{BASE}c/').replace(f'{BASE}#index',BASE))
keep.add('index.html')
for f in os.listdir('c'):
    if f.endswith('.html') and f not in keep: os.remove(os.path.join('c',f))
urls=[BASE,BASE+'c/']+[f'{BASE}c/{cid}.html' for cid,_,_,_ in cards]
open('sitemap.xml','w',encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls)+'</urlset>\n')
open('robots.txt','w',encoding='utf-8').write(f'User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n')
print('cards',len(cards),'urls',len(urls))
