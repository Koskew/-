# -*- coding: utf-8 -*-
"""Может ли ГДЕ МЫ v5 + триггерная свеча дать сделки без каскада v8.

Правило: триггерная свеча, направление берём из счёта 2/2, входим только
на коррекционной точке счёта в сторону счёта, стоп за свечой, цель кратна
риску. Сравниваем с каскадом движка.
"""
import sys, statistics as st, math
sys.path.insert(0, 'research')
import engine
from core import Core, load
from library import pivots_n
from trigger_base import is_trig

rows = load()
c5 = Core(rows, fib=0.33); c5.at = pivots_n(rows, 5)
c2 = Core(rows, fib=0.15); c2.at = pivots_n(rows, 2)
ST = {}
for b in range(len(rows)):
    c5.step(b); c2.step(b)
    ST[b] = (0 if c5.inTrans else c5.tr, 0 if c2.inTrans else c2.tr, c5.room(rows[b][4]),
             c2.KN[-1] if c2.KN else -1, c2.cdir())

BUF = 0.001
def trade(b, side, rr, horizon=1500):
    o, h, l, c = rows[b][1], rows[b][2], rows[b][3], rows[b][4]
    sl = l * (1 - BUF) if side == 1 else h * (1 + BUF)
    risk = (c - sl) if side == 1 else (sl - c)
    if risk <= 0: return None
    tp = c + rr * risk if side == 1 else c - rr * risk
    for j in range(b + 1, min(b + 1 + horizon, len(rows))):
        hh, ll = rows[j][2], rows[j][3]
        hitS = (ll <= sl) if side == 1 else (hh >= sl)
        hitT = (hh >= tp) if side == 1 else (ll <= tp)
        if hitS: return -1.0
        if hitT: return float(rr)
    return None

def run(rule, rr):
    R = []
    for b in range(len(rows)):
        if is_trig(rows[b]) < 0: continue
        t5, t2, r5, cn2, cd2 = ST[b]
        if cd2 == 0: continue
        side = cd2
        if rule == 'коррекция счёта':
            if cn2 not in (2, 4): continue
        elif rule == 'коррекция + слои':
            if cn2 not in (2, 4) or t5 != side: continue
        elif rule == 'коррекция + запас':
            if cn2 not in (2, 4): continue
            if r5 is None or r5 <= 1.0: continue
        elif rule == 'балл 3 из 3':
            a = 1 if (t5 != 0 and t5 == t2) else 0
            bq = 1 if (cn2 in (2, 4) and cd2 == side) else 0
            cq = 1 if (r5 is not None and r5 > 1.0) else 0
            if a + bq + cq < 3: continue
        x = trade(b, side, rr)
        if x is not None: R.append(x)
    return R

print('Правило: триггерная свеча, направление по счёту 2/2, стоп за свечой.\n')
print(f'{"правило":>22} {"RR":>3} {"сделок":>7} {"TP":>6} {"сумма":>9} {"на сделку":>11} {"шум ±":>7}')
for rule in ('коррекция счёта', 'коррекция + слои', 'коррекция + запас', 'балл 3 из 3'):
    for rr in (2, 3, 4):
        R = run(rule, rr)
        if len(R) < 10: continue
        sd = st.pstdev(R) if len(R) > 1 else 0
        print(f'{rule:>22} {rr:>3} {len(R):>7} {sum(1 for x in R if x>0)/len(R):>5.0%} '
              f'{sum(R):>+8.1f}R {st.mean(R):>+10.2f}R {2*sd/math.sqrt(len(R)):>6.2f}')
print()
E = engine.build_engine('data/XAUUSD_1h_2y.csv', trig='auto')
T = engine.run(E, version=5)
sd = T.R.std()
print(f'{"каскад движка v8":>22} {"—":>3} {len(T):>7} {(T.out=="TP").mean():>5.0%} '
      f'{T.R.sum():>+8.1f}R {T.R.mean():>+10.2f}R {2*sd/math.sqrt(len(T)):>6.2f}')
