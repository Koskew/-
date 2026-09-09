# -*- coding: utf-8 -*-
"""Оценка качества входа: складывается ли она из измеримых признаков.

Балл строится из трёх условий, каждое из которых уже мерилось отдельно:
  +1  слои 5/5 и 2/2 согласны
  +1  вход на коррекционной точке счёта 2/2, в сторону счёта
  +1  запас старшего больше импульса (не входим в умирающий тренд)

Дальше смотрим, разделяет ли балл реальный результат сделок движка.
"""
import sys, statistics as st
sys.path.insert(0, 'research')
import engine, pandas as pd
from core import Core, load
from library import pivots_n

E = engine.build_engine('data/XAUUSD_1h_2y.csv', trig='auto')
T = engine.run(E, version=5)
rows = load()
c5 = Core(rows, fib=0.33); c5.at = pivots_n(rows, 5)
c2 = Core(rows, fib=0.15); c2.at = pivots_n(rows, 2)

state = {}
for b in range(len(rows)):
    c5.step(b); c2.step(b)
    state[b] = (0 if c5.inTrans else c5.tr, 0 if c2.inTrans else c2.tr,
                c5.room(rows[b][4]),
                c2.KN[-1] if c2.KN else -1, c2.cdir())

recs = []
for _, r in T.iterrows():
    b = int(r['i'])
    if b not in state: continue
    t5, t2, r5, cn2, cd2 = state[b]
    side = 1 if r['dir'] == 'LONG' else -1
    a = 1 if (t5 != 0 and t5 == t2) else 0                       # слои согласны
    bq = 1 if (cn2 in (2, 4) and cd2 == side) else 0             # коррекционная точка по счёту
    c = 1 if (r5 is not None and r5 > 1.0) else 0                # запас старшего
    recs.append(dict(R=r['R'], score=a+bq+c, a=a, b=bq, c=c, side=side))

D = pd.DataFrame(recs)
print(f'сделок с полным контекстом: {len(D)} из {len(T)}\n')
print(f'{"балл":>6} {"сделок":>8} {"доля TP":>9} {"сумма R":>10} {"на сделку":>11}')
for s in (0, 1, 2, 3):
    g = D[D.score == s]
    if len(g) == 0: continue
    print(f'{s:>6} {len(g):>8} {(g.R>0).mean():>8.0%} {g.R.sum():>+9.1f}R {g.R.mean():>+10.2f}R')
print(f'{"все":>6} {len(D):>8} {(D.R>0).mean():>8.0%} {D.R.sum():>+9.1f}R {D.R.mean():>+10.2f}R')

print(f'\nкаждое условие по отдельности:')
print(f'{"условие":>34} {"сделок":>8} {"на сделку":>11}')
for k, nm in (('a','слои согласны'), ('b','коррекционная точка по счёту'), ('c','запас старшего > 1 импульса')):
    for v in (1, 0):
        g = D[D[k] == v]
        if len(g) < 10: continue
        print(f'{(nm if v else "НЕ " + nm):>34} {len(g):>8} {g.R.mean():>+10.2f}R')

# порог шума
import math
print(f'\nпорог шума: сделки дают от -1R до +{T.RR.max():.0f}R, разброс {D.R.std():.2f}R')
for n in (20, 50, 100, 200):
    print(f'  {n:>4} сделок -> две сигмы = ±{2*D.R.std()/math.sqrt(n):.2f}R')
