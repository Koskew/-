# -*- coding: utf-8 -*-
"""От каких меток открывать сделки: 2/2, 5/5 или оба, и с чем согласовывать.

Вход на коррекционной точке счёта (2) или (4), в сторону счёта, стоп за
свечой. Проверяем: чей счёт даёт направление, с чем согласуется быстрый
слой — с ТРЕНДОМ 5/5 или со СЧЁТОМ 5/5 — и какой риск-реворд.
"""
import sys, statistics as st, math
sys.path.insert(0, 'research')
from core import Core, load
from library import pivots_n
from trigger_base import is_trig

rows = load()
c5 = Core(rows, fib=0.33); c5.at = pivots_n(rows, 5)
c2 = Core(rows, fib=0.15); c2.at = pivots_n(rows, 2)
ST = {}
for b in range(len(rows)):
    c5.step(b); c2.step(b)
    ST[b] = dict(t5=0 if c5.inTrans else c5.tr, t2=0 if c2.inTrans else c2.tr,
                 r5=c5.room(rows[b][4]),
                 n5=c5.KN[-1] if c5.KN else -1, d5=c5.cdir(),
                 n2=c2.KN[-1] if c2.KN else -1, d2=c2.cdir())

BUF = 0.001
def trade(b, side, rr, horizon=1500):
    o, h, l, c = rows[b][1], rows[b][2], rows[b][3], rows[b][4]
    sl = l * (1 - BUF) if side == 1 else h * (1 + BUF)
    risk = (c - sl) if side == 1 else (sl - c)
    if risk <= 0: return None
    tp = c + rr * risk if side == 1 else c - rr * risk
    for j in range(b + 1, min(b + 1 + horizon, len(rows))):
        hh, ll = rows[j][2], rows[j][3]
        if (ll <= sl) if side == 1 else (hh >= sl): return -1.0
        if (hh >= tp) if side == 1 else (ll <= tp): return float(rr)
    return None

def run(src, agree, rr):
    R = []
    for b in range(len(rows)):
        if is_trig(rows[b]) < 0: continue
        s = ST[b]
        cands = []
        if src in ('2/2', 'оба') and s['d2'] != 0 and s['n2'] in (2, 4):
            cands.append(('2/2', s['d2']))
        if src in ('5/5', 'оба') and s['d5'] != 0 and s['n5'] in (2, 4):
            cands.append(('5/5', s['d5']))
        for who, side in cands:
            if who == '2/2':
                if agree == 'тренд 5/5' and s['t5'] != side: continue
                if agree == 'счёт 5/5'  and s['d5'] != side: continue
                if agree == 'оба'       and (s['t5'] != side or s['d5'] != side): continue
            x = trade(b, side, rr)
            if x is not None: R.append(x)
    return R

print('Вход на точке (2) или (4) счёта, в сторону счёта, стоп за свечой.\n')
print(f'{"откуда":>7} {"2/2 согласуется с":>18} {"RR":>3} {"сделок":>7} {"TP":>5} {"сумма":>9} {"на сделку":>11} {"шум ±":>7}')
for src, agree in (('2/2','ничем'), ('2/2','тренд 5/5'), ('2/2','счёт 5/5'), ('2/2','оба'),
                   ('5/5','—'), ('оба','тренд 5/5'), ('оба','счёт 5/5'), ('оба','оба')):
    for rr in (2, 3):
        R = run(src, agree, rr)
        if len(R) < 10: continue
        sd = st.pstdev(R)
        print(f'{src:>7} {agree:>18} {rr:>3} {len(R):>7} {sum(1 for x in R if x>0)/len(R):>4.0%} '
              f'{sum(R):>+8.1f}R {st.mean(R):>+10.2f}R {2*sd/math.sqrt(len(R)):>6.2f}')
