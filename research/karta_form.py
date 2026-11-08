#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
КАРТА ВСЕХ ФОРМ СВЕЧИ ИЗ ДЕВЯТИЛЕТНЕГО ФАЙЛА.

    python3 research/karta_form.py > research/out/karta_form.svg

Заведена 08.11.2026 по его слову: «можешь проанализировать все свечи,
которые у нас есть, и сделать файл, как ты сделал выше схему свечей,
чтобы я разобрал все формы из 9-летнего файла».

ФОРМА СВЕЧИ ЗАДАЁТСЯ РОВНО ДВУМЯ ЧИСЛАМИ, и это не выбор, а следствие:
доли тела и двух фитилей в сумме дают 100, значит, зная ТЕЛО и ПЕРЕКОС
фитилей, третье число находится само. Поэтому сетка 10 x 9 по этим двум
числам покрывает ВСЕ возможные формы без исключения.

    строки  А-К  — тело, от 0-10% до 90-100% высоты свечи
    столбцы 1-9  — перекос: 1 = весь фитиль СНИЗУ, 5 = поровну,
                   9 = весь фитиль СВЕРХУ

В каждой клетке нарисована НАСТОЯЩАЯ свеча — медианная форма своей
клетки, а не середина диапазона. Высота у всех одна нарочно: сравнивать
надо форму, а размер проверяется отдельными условиями.
"""
import csv, os

ROWS, COLS = 10, 9
BUKVY = u'АБВГДЕЖЗИК'
SIM, POR, OKNO, CAP = 8.0, 2.0, 20, 0.40

base = os.path.join(os.path.dirname(__file__), '..', 'data')
raw = []
with open(os.path.join(base, 'XAUUSD_1h_9y.csv'), newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        raw.append((float(r['open']), float(r['high']), float(r['low']), float(r['close'])))

cell = [[[] for _ in range(COLS)] for _ in range(ROWS)]
shk = [0.0]*len(raw)
par = [None]*len(raw)
for i, (o, h, l, c) in enumerate(raw):
    rng = h - l
    if rng <= 0 or c <= 0:
        continue
    shk[i] = rng/c*100
    bod = abs(c-o); up = h-o if o > c else h-c; lo = c-l if o > c else o-l
    par[i] = (bod/rng*100, up/rng*100, lo/rng*100)

vsego = 0
for i in range(len(raw)):
    if par[i] is None:
        continue
    vsego += 1
    b, u_, d = par[i]
    w = u_ + d
    pk = 50.0 if w <= 0 else u_/w*100
    r = min(int(b//10), ROWS-1)
    k = min(int(pk//(100.0/COLS)), COLS-1)
    forma = abs(u_-d) <= SIM
    bere = False
    if forma and i >= OKNO:
        sred = sum(shk[i-OKNO:i])/OKNO
        if sred > 0 and shk[i]/sred <= POR and shk[i] <= CAP:
            bere = True
    cell[r][k].append((b, u_, d, forma, bere))

CW, CH = 128, 116
X0, Y0 = 150, 232
W = X0 + COLS*CW + 60
H = Y0 + ROWS*CH + 90
o = []
def t(x, y, s, sz=13, col='#333', an='start', w='400'):
    o.append(u'<text x="%g" y="%g" font-family="system-ui,Segoe UI,Arial" font-size="%g" fill="%s" text-anchor="%s" font-weight="%s">%s</text>' % (x,y,sz,col,an,w,s))
def ln(x1,y1,x2,y2,col='#ccc',w=1,dash=''):
    d = u' stroke-dasharray="%s"' % dash if dash else u''
    o.append(u'<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g"%s/>' % (x1,y1,x2,y2,col,w,d))

o.append(u'<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W,H,W,H))
o.append(u'<rect width="%d" height="%d" fill="#ffffff"/>' % (W,H))
t(40, 48, u'КАРТА ВСЕХ ФОРМ СВЕЧИ · XAUUSD 1H · девять лет, %s баров' % u'{:,}'.format(vsego).replace(',', u' '), 25, '#111', w='700')
t(40, 76, u'Форма задаётся двумя числами — ТЕЛО и ПЕРЕКОС фитилей. Третье находится само: доли в сумме дают 100.', 14, '#666')
t(40, 96, u'Поэтому эта сетка покрывает ВСЕ формы без исключения. В клетке нарисована медианная свеча своей клетки — настоящая.', 14, '#666')
t(40, 116, u'Высота у всех одна нарочно: здесь сравнивается только ФОРМА, размер проверяется отдельными условиями.', 14, '#666')
t(40, 150, u'Пиши адресами клеток: «Г4 да, К1 нет».', 15, '#111', w='700')
o.append(u'<rect x="332" y="136" width="22" height="16" fill="#dcfce7" stroke="#86efac"/>')
t(360, 150, u'зелёная — эту форму правило берёт сейчас', 14, '#555')
o.append(u'<rect x="700" y="136" width="22" height="16" fill="#ffffff" stroke="#ddd"/>')
t(728, 150, u'белая — не берёт', 14, '#555')

t(X0 + COLS*CW/2.0, 196, u'ПЕРЕКОС ФИТИЛЕЙ', 15, '#111', 'middle', '700')
t(X0, 216, u'◀ весь фитиль СНИЗУ', 13, '#777')
t(X0 + COLS*CW/2.0, 216, u'поровну', 13, '#777', 'middle')
t(X0 + COLS*CW, 216, u'весь фитиль СВЕРХУ ▶', 13, '#777', 'end')
t(44, 196, u'ТЕЛО', 15, '#111', w='700')
t(44, 216, u'доля высоты', 12, '#777')

for r in range(ROWS):
    yc = Y0 + r*CH
    t(132, yc + CH/2.0 - 4, u'%s' % BUKVY[r], 19, '#111', 'end', '700')
    t(132, yc + CH/2.0 + 14, u'%d-%d%%' % (r*10, r*10+10), 12, '#888', 'end')
    for k in range(COLS):
        xc = X0 + k*CW
        lst = cell[r][k]
        nn = len(lst)
        nb = sum(1 for x in lst if x[4])
        dolya = 100.0*nb/nn if nn else 0.0
        fill = '#dcfce7' if dolya >= 50 else ('#f0fdf4' if dolya > 0 else '#ffffff')
        o.append(u'<rect x="%g" y="%g" width="%g" height="%g" fill="%s" stroke="#e2e2e2"/>' % (xc, yc, CW, CH, fill))
        if r == 0:
            t(xc + CW/2.0, Y0 - 10, u'%d' % (k+1), 15, '#111', 'middle', '700')
        if nn:
            lst2 = sorted(lst, key=lambda x: x[0])
            b, u_, d = lst2[nn//2][0], lst2[nn//2][1], lst2[nn//2][2]
            s = b + u_ + d
            if s > 0:
                b, u_, d = b/s*100, u_/s*100, d/s*100
            hh, bw = 58.0, 17.0
            top = yc + 16
            cx = xc + CW/2.0 - 20
            ln(cx, top, cx, top + hh, '#222', 1.5)
            by = top + hh*u_/100.0
            bh = max(hh*b/100.0, 1.6)
            o.append(u'<rect x="%g" y="%g" width="%g" height="%g" fill="#2b2b2b" stroke="#222" stroke-width="1.2"/>' % (cx-bw/2.0, by, bw, bh))
            t(xc + CW - 10, top + 14, u'%s%d' % (BUKVY[r], k+1), 15, '#111', 'end', '700')
            t(xc + CW - 10, top + 32, u'%d шт' % nn, 12, '#666', 'end')
            t(xc + CW - 10, top + 48, u'%.1f%%' % (100.0*nn/vsego), 12, '#999', 'end')
            t(xc + CW - 10, top + 68, u'берёт %d' % nb, 12, '#166534' if nb else '#bbb', 'end', '600')
o.append(u'</svg>')
import sys
sys.stdout.write(u'\n'.join(o))
