# -*- coding: utf-8 -*-
"""Макет таблицы «вход + риск» на одну жёлтую свечу. Утверждён им 17.11.2026 (РИ7.8).

    python3 research/maket.py research/out/maket/2017-08-15_1100.json

Читает JSON, пишет рядом .html и .png. Ничего не считает сам: все числа
в JSON приносит разбор свечи (журнал А). Это картинка для разговора, НЕ пайн.

JSON: title, sub, sdelka [[подпись, значение, "g"|"r"|""]], itog [текст, "g"|"r"],
check [[№ и имя, значение, "за"|"против"|"ничего", жёсткий 0/1]], tally, stats_head [..],
stats [[подпись, день, неделя, месяц, "g"|"r"|""]], note.
"""
import json, sys, os, html

CSS = """:root{--bg:#fff;--fg:#222;--mut:#777;--ln:#ddd;--g:#c8ecd2;--gt:#11663a;--r:#f8cfcf;--rt:#9b1c1c;--n:#eee;--h:#e4e4e4}
body{margin:0;background:var(--bg);color:var(--fg);font:13px Arial,sans-serif;padding:16px}
h1{font-size:17px;margin:0 0 4px}.sub{color:var(--mut);margin:0 0 12px;font-size:12px}
.wrap{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start}
table{border-collapse:collapse;min-width:360px}td,th{border:1px solid var(--ln);padding:4px 8px;text-align:left}
th{background:var(--h);font-size:12px}.blk td:first-child{color:var(--mut);white-space:nowrap}
.g{background:var(--g);color:var(--gt)}.r{background:var(--r);color:var(--rt)}.n{background:var(--n);color:var(--mut)}
.hard{font-weight:bold}.tag{font-size:11px;color:var(--mut)}
.bar{display:flex;gap:2px;margin:4px 0}.bar span{flex:1;height:16px;border-radius:2px}"""
CLS = {'за': 'g', 'против': 'r', 'ничего': 'n'}
e = html.escape


def build(d):
    o = ['<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Макет таблицы</title><style>%s</style></head><body>' % CSS,
         '<h1>%s</h1><p class="sub">%s</p><div class="wrap">' % (e(d['title']), e(d.get('sub', '')))]
    o.append('<table class="blk"><tr><th colspan="2">1 · СДЕЛКА</th></tr>')
    for lab, val, c in d['sdelka']:
        o.append('<tr><td>%s</td><td class="%s">%s</td></tr>' % (e(lab), c, e(val)))
    o.append('<tr><td>итог</td><td class="%s hard">%s</td></tr></table>' % (d['itog'][1], e(d['itog'][0])))
    o.append('<table class="blk"><tr><th colspan="3">2 · ЗА / ПРОТИВ — лист проверки</th></tr>')
    for name, val, v, hard in d['check']:
        o.append('<tr><td class="%s">%s</td><td class="%s">%s</td><td class="tag">%s</td></tr>' % ('hard' if hard else '', e(name), CLS[v.rstrip('*')], e(val), e(v)))
    bar = ''.join('<span class="%s"></span>' % CLS[v.rstrip('*')] for _, _, v, _ in d['check'])
    o.append('<tr><td colspan="3"><div class="bar">%s</div>%s</td></tr></table>' % (bar, d.get('tally', '')))
    o.append('<table><tr>%s</tr>' % ''.join('<th>%s</th>' % e(h) for h in d['stats_head']))
    for row in d['stats']:
        c = row[4] if len(row) > 4 else ''
        o.append('<tr><td>%s</td>%s</tr>' % (e(row[0]), ''.join('<td class="%s">%s</td>' % (c, e(str(x))) for x in row[1:4])))
    o.append('</table></div><p class="sub">%s</p></body></html>' % e(d.get('note', '')))
    return ''.join(o)


def main():
    src = sys.argv[1]
    d = json.load(open(src, encoding='utf-8'))
    base = os.path.splitext(src)[0]
    open(base + '.html', 'w', encoding='utf-8').write(build(d))
    # снимок — Playwright из Node, он стоит в среде; у Python его нет
    import subprocess
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
          "const p=await b.newPage({viewport:{width:1250,height:500},deviceScaleFactor:2});"
          "await p.setContent(require('fs').readFileSync(process.argv[1],'utf8'));"
          "await p.screenshot({path:process.argv[2],fullPage:true});await b.close();})()")
    subprocess.run(['node', '-e', js, os.path.abspath(base + '.html'), os.path.abspath(base + '.png')], check=True)
    print(base + '.png')


if __name__ == '__main__':
    main()
