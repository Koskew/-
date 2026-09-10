# -*- coding: utf-8 -*-
"""Описание слоя 3/3 рядом с 2/2, 4/4 и 5/5. Ни сделок, ни R.

Часть А — метки, колена и счёт. От глубины пробоя не зависят: KP/KH/KL/KN
считаются до всякой смерти тренда, так что здесь одна прогонка на слой.
Колена считаются по стороне сырой метки (сверено вручную: новых колен +
слияний = сырых меток, ровно). Счёт режется по падению номера точки —
внутри счёта номер не убывает, значит падение = начался новый счёт.

Часть Б — тренд. Зависит от глубины пробоя, поэтому перебор значений.
Рывок держим на 0.5 у всех, как сейчас в индикаторе.
"""
import sys, csv, statistics as st
sys.path.insert(0, 'research')
from core import Core

def load(p):
    return [(r['time'], float(r['open']), float(r['high']), float(r['low']), float(r['close']))
            for r in csv.DictReader(open(p, encoding='utf-8-sig'))]

def pivots_n(rows, N):
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
    for i in range(N, len(rows) - N):
        if all(hi[i-k] <= hi[i] for k in range(1, N+1)) and all(hi[i+k] < hi[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, N+1)) and all(lo[i+k] > lo[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, lo[i], False))
    return at

def med(v): return st.median(v) if v else float('nan')

def partA(rows, at):
    co = Core(rows, fib=0.33); co.at = at
    raw = sum(len(v) for v in at.values())
    new = 0; finals = []                      # колена и их итоговая мутность
    segs = []; cur = None                     # отрезки счёта: [макс точка, первый бар, последний бар]
    prev_cn = -1
    for b in range(len(rows)):
        for (_bar, _price, isHi) in at.get(b, []):
            n = len(co.KP)
            if n > 0 and co.KH[n-1] == isHi:
                pass                          # слияние: колено то же
            else:
                if n > 0: finals.append(co.KM[n-1])
                new += 1
        co.step(b)
        cn = co.KN[-1] if co.KN else -1
        if cn < 0:
            prev_cn = -1; continue
        if cur is None or cn < prev_cn:       # номер упал — начался новый счёт
            cur = [cn, b, b]; segs.append(cur)
        else:
            cur[0] = max(cur[0], cn); cur[2] = b
        prev_cn = cn
    if co.KP: finals.append(co.KM[-1])
    mud = sum(1 for x in finals if x >= 2)
    depth = [s[0] for s in segs]; span = [s[2] - s[1] for s in segs]
    return dict(raw=raw, knees=new, mudpct=mud / max(len(finals), 1) * 100,
                ncounts=len(segs), depth=depth, span=span)

def partB(rows, at, fib):
    co = Core(rows, fib=fib); co.at = at; co.run()
    return dict(n=len(co.lives), life=med(co.lives), transpct=co.trBars / len(rows) * 100)

FIBS = [0.10, 0.15, 0.20, 0.25, 0.33, 0.40, 0.50]
for tf, path in (('1H', 'data/XAUUSD_1h_2y.csv'), ('5m', 'data/XAUUSD_5m.csv')):
    rows = load(path)
    print(f'\n{"="*88}\n{tf}: {len(rows)} баров, {rows[0][0][:10]} — {rows[-1][0][:10]}')
    piv = {N: pivots_n(rows, N) for N in (2, 3, 4, 5)}

    print(f'\n─── А · МЕТКИ, КОЛЕНА И СЧЁТ (от глубины пробоя не зависят) ' + '─'*28)
    print(f'{"слой":6}{"сырых":>8}{"колен":>8}{"баров/колено":>14}{"мутных":>9}'
          f'{"счётов":>9}{"баров/счёт":>12}{"медиана точек":>15}{"дошли до (5)":>14}{"глубина 0":>11}')
    for N in (2, 3, 4, 5):
        a = partA(rows, piv[N]); d = a['depth']
        print(f'{f"{N}/{N}":6}{a["raw"]:>8}{a["knees"]:>8}{len(rows)/max(a["knees"],1):>14.1f}'
              f'{a["mudpct"]:>8.0f}%{a["ncounts"]:>9}{med(a["span"]):>12.0f}'
              f'{med(d):>15.0f}{sum(1 for x in d if x>=5)/max(len(d),1)*100:>13.0f}%'
              f'{sum(1 for x in d if x==0)/max(len(d),1)*100:>10.0f}%')

    print(f'\n─── Б · ТРЕНД ПРИ РАЗНОЙ ГЛУБИНЕ ПРОБОЯ (рывок 0.5 у всех) ' + '─'*28)
    print(f'{"глубина":9}' + ''.join(f'{f"{N}/{N}":>26}' for N in (2, 3, 4, 5)))
    print(f'{"":9}' + ''.join(f'{"трендов жизнь переход":>26}' for _ in (2, 3, 4, 5)))
    for fib in FIBS:
        line = f'{fib:<9.2f}'
        for N in (2, 3, 4, 5):
            b = partB(rows, piv[N], fib)
            line += f'{b["n"]:>10}{b["life"]:>8.0f}б{b["transpct"]:>6.0f}%'
        print(line)
