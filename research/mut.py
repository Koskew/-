# -*- coding: utf-8 -*-
"""Мутность встречного колена: когда она становится известна.

Колено считается мутным, если в него слилось 2+ сырых метки. Слияние
прекращается, когда приходит метка другой стороны — то есть когда
создаётся следующее колено. Значит окончательная мутность колена
известна ровно в тот момент, когда появилось следующее.

А исход, который мерился в obryv.py, — это направление следующего
колена. Если оба узнаются на одном баре, признак не опережает событие
и в торговле бесполезен.

Здесь это проверяется, а не предполагается.
"""
import sys, csv, collections
sys.path.insert(0, 'research')
from core import Core

def load(p):
    out = []
    for r in csv.DictReader(open(p, encoding='utf-8-sig')):
        o, h, l, c = float(r['open']), float(r['high']), float(r['low']), float(r['close'])
        out.append((r['time'], min(max(o, l), h), h, l, min(max(c, l), h)))
    return out

def pivots_n(rows, N):
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
    for i in range(N, len(rows) - N):
        if all(hi[i-k] <= hi[i] for k in range(1, N+1)) and all(hi[i+k] < hi[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, N+1)) and all(lo[i+k] > lo[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, lo[i], False))
    return at

rows = load('data/XAUUSD_1h_9y.csv')
print('КОГДА СТАНОВИТСЯ ИЗВЕСТНА МУТНОСТЬ КОЛЕНА\n')
for N in (5, 3, 2):
    at = pivots_n(rows, N)
    co = Core(rows, fib=0.33); co.at = at
    # для каждого колена: бар последнего слияния и бар создания следующего
    lastMerge = {}      # номер создания -> бар, когда мутность стала окончательной
    born = {}           # номер создания -> бар создания
    created = 0
    for b in range(len(rows)):
        side = co.KH[-1] if co.KP else None
        for (_bar, _p, isHi) in at.get(b, []):
            if side is None or isHi != side:
                created += 1
                born[created - 1] = b
            else:
                lastMerge[created - 1] = b     # слияние в текущее колено
            side = isHi
        co.step(b)
    same = 0; ahead = 0; d = []
    for k in sorted(lastMerge):
        if k + 1 not in born: continue
        nb = born[k + 1]                        # бар создания следующего колена
        lm = lastMerge[k]                       # бар последнего слияния в это
        if lm == nb: same += 1
        else: ahead += 1; d.append(nb - lm)
    tot = same + ahead
    print(f'── слой {N}/{N}: мутных колен {tot}')
    print(f'   последнее слияние на том же баре, что и создание следующего: '
          f'{same} ({same/tot:.0%})')
    print(f'   стало известно раньше:                                      '
          f'{ahead} ({ahead/tot:.0%})')
    if d:
        d.sort()
        print(f'   если раньше — медиана опережения {d[len(d)//2]} баров, '
              f'четверть случаев больше {d[int(len(d)*.75)]}')
    print()
