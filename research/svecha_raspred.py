#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЧТО ИНДИКАТОР ОТБИРАЕТ СЕЙЧАС — распределение по телу и по фитилям.

    python3 research/svecha_raspred.py

Заведён 08.11.2026 по его слову «можем сразу сделать проверку, что
сейчас отбирается по индикатору».

ПАРАМЕТРЫ НЕ ВЫДУМАНЫ, это НЫНЕШНЕЕ правило:
    форма   разница фитилей <= 8 п.п.
    размер  высота <= 2.0 средней по 20 предыдущим
    потолок СЧИТАЕТСЯ ДВАЖДЫ: 0.40% (по умолчанию) и 0.13% (у него сейчас)
Данные: data/XAUUSD_1h_9y.csv, 1H.
"""
import csv, os

OKNO, SIM, POR = 20, 8.0, 2.0
CAPS = [0.40, 0.13]

base = os.path.join(os.path.dirname(__file__), '..', 'data')
rows = []
with open(os.path.join(base, 'XAUUSD_1h_9y.csv'), newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        rows.append((float(r['open']), float(r['high']), float(r['low']), float(r['close'])))

n = len(rows)
shk = [0.0]*n
par = [None]*n
for i, (o, h, l, c) in enumerate(rows):
    rng = h - l
    if rng <= 0 or c <= 0:
        continue
    shk[i] = rng/c*100
    bod = abs(c-o)
    up = h-o if o > c else h-c
    lo = c-l if o > c else o-l
    par[i] = (bod/rng*100, up/rng*100, lo/rng*100)

def vedro(b):
    return min(int(b//10), 9)

vsego = 0; forma = 0
telo_all = [0]*10
telo_sel = {c: [0]*10 for c in CAPS}
sel = {c: 0 for c in CAPS}
razn_all = [0]*8   # 0-5,5-10,...,35+

for i in range(n):
    if par[i] is None:
        continue
    vsego += 1
    bodP, uppP, lowP = par[i]
    telo_all[vedro(bodP)] += 1
    rz = abs(uppP-lowP)
    razn_all[min(int(rz//5), 7)] += 1
    if rz > SIM:
        continue
    forma += 1
    if i < OKNO:
        continue
    sred = sum(shk[i-OKNO:i])/OKNO
    if sred <= 0 or shk[i]/sred > POR:
        continue
    for cap in CAPS:
        if shk[i] <= cap:
            sel[cap] += 1
            telo_sel[cap][vedro(bodP)] += 1

print(u'ДАННЫЕ: XAUUSD 1H, %d баров с ненулевой высотой' % vsego)
print(u'ПРАВИЛО: фитили <= %g п.п. · размер <= %gx средней по %d · потолок — две колонки' % (SIM, POR, OKNO))
print()
print(u'  подошло по ФОРМЕ            %6d   %5.1f%% всех баров' % (forma, 100.0*forma/vsego))
for cap in CAPS:
    print(u'  прошло ВСЕ ТРИ, потолок %.2f%%  %6d   %5.1f%% всех баров   %5.1f%% формы'
          % (cap, sel[cap], 100.0*sel[cap]/vsego, 100.0*sel[cap]/forma))
print()
print(u'РАСПРЕДЕЛЕНИЕ ПО ТЕЛУ, в процентах высоты свечи')
print(u'  тело        все бары        отобрано 0.40%%     отобрано 0.13%%')
for k in range(10):
    a = 100.0*telo_all[k]/vsego
    s1 = 100.0*telo_sel[0.40][k]/sel[0.40] if sel[0.40] else 0
    s2 = 100.0*telo_sel[0.13][k]/sel[0.13] if sel[0.13] else 0
    print(u'  %2d-%3d%%   %6d %5.1f%%    %5d %5.1f%%      %5d %5.1f%%'
          % (k*10, k*10+10, telo_all[k], a, telo_sel[0.40][k], s1, telo_sel[0.13][k], s2))
print()
print(u'РАСПРЕДЕЛЕНИЕ ПО РАЗНИЦЕ ФИТИЛЕЙ, все бары')
for k in range(8):
    lo = k*5
    nm = u'%2d-%2d' % (lo, lo+5) if k < 7 else u'35+  '
    print(u'  %s п.п.  %6d  %5.1f%%%s' % (nm, razn_all[k], 100.0*razn_all[k]/vsego,
          u'   <- порог 8 п.п. режет здесь' if k == 1 else u''))
