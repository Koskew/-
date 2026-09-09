# -*- coding: utf-8 -*-
"""Ступень «против тренда»: голоса в пятёрке сырых меток против настоящего тренда.

Каскад движка отсекает вход, считая, сколько меток в пятёрке смотрят вверх
и сколько вниз. Это грубая замена тренду. Теперь тренд считается честно —
проверяем, что будет, если ступень заменить.
"""
import sys, bisect, math, statistics as st
sys.path.insert(0, 'research')
import numpy as np, pandas as pd
import engine
from engine import FRESH_MARKS, TREND_MIN, BUF, banned_tail, resolve
from core import Core, load
from library import pivots_n

E = engine.build_engine('data/XAUUSD_1h_2y.csv', trig='auto')
rows = load()
c5 = Core(rows, fib=0.33); c5.at = pivots_n(rows, 5)
c2 = Core(rows, fib=0.15); c2.at = pivots_n(rows, 2)
ST = {}
for b in range(len(rows)):
    c5.step(b); c2.step(b)
    ST[b] = (0 if c5.inTrans else c5.tr, 0 if c2.inTrans else c2.tr, c5.room(rows[b][4]))

def decide(i, mode):
    confs, fast = E['confs'], E['fast']
    csize, C, H, L = E['csize'], E['C'], E['H'], E['L']
    k = bisect.bisect_right(confs, i)
    seq = fast[max(0, k - FRESH_MARKS):k]
    if not seq: return None
    labels = [r['label'] for r in seq]
    last = labels[-1]
    if last in ('HL', 'LL'): is_long = True
    elif last in ('LH', 'HH'): is_long = False
    else: return None
    entry = C[i]; lag = i - seq[-1]['conf']
    if last in ('LL', 'HH') and lag <= 1: return None
    if csize[i] / C[i] * 100 > E['size_thr_pct']: return None

    # ── ступень «против тренда» ──
    up = sum(1 for x in labels if x in ('HH', 'HL'))
    dn = sum(1 for x in labels if x in ('LH', 'LL'))
    had_slom = any((labels[j-1] == 'HH' and labels[j] == 'LL') or
                   (labels[j-1] == 'LL' and labels[j] == 'HL') for j in range(1, len(labels)))
    sd = 1 if is_long else -1
    t5, t2, r5 = ST.get(i, (0, 0, None))
    if mode == 'голоса':
        if not had_slom:
            if up >= (3 if last == 'HH' else 4) and not is_long: return None
            if dn >= TREND_MIN and is_long: return None
    elif mode == 'тренд 5/5':
        if t5 != 0 and t5 != sd: return None
    elif mode == 'оба слоя':
        if t5 != 0 and t2 != 0 and t5 == t2 and t5 != sd: return None
    elif mode == 'голоса + 5/5':
        if not had_slom:
            if up >= (3 if last == 'HH' else 4) and not is_long: return None
            if dn >= TREND_MIN and is_long: return None
        if t5 != 0 and t5 != sd: return None
    elif mode == 'без ступени':
        pass

    if len(labels) >= 2 and ((labels[-2] == 'HH' and labels[-1] == 'LL') or
                             (labels[-2] == 'LL' and labels[-1] == 'HL')): return None
    sl = L[i] * (1 - BUF) if is_long else H[i] * (1 + BUF)
    if (is_long and sl >= entry) or ((not is_long) and sl <= entry): return None
    risk = abs(entry - sl)
    side = 'high' if is_long else 'low'
    cand = [r for r in seq if r['side'] == side]
    tp = np.nan
    if is_long:
        for r in sorted([r for r in cand if r['price'] > entry], key=lambda r: r['price']):
            if (r['price'] - entry) / risk >= 3: tp = r['price']; break
    else:
        for r in sorted([r for r in cand if r['price'] < entry], key=lambda r: -r['price']):
            if (entry - r['price']) / risk >= 3: tp = r['price']; break
    if np.isnan(tp): return None
    if banned_tail(labels) is not None: return None
    return dict(i=i, is_long=is_long, entry=entry, sl=sl, tp=tp,
                RR=abs(tp - entry) / risk)

trig = list(np.where(E['TRIG'])[0])
print(f'{"ступень против тренда":>18} {"сделок":>8} {"TP":>6} {"сумма R":>10} {"на сделку":>11} {"просадка":>10}')
for mode in ('голоса', 'тренд 5/5', 'оба слоя', 'голоса + 5/5', 'без ступени'):
    R = []
    for i in trig:
        d = decide(i, mode)
        if d is None: continue
        out = resolve(E, int(d['i']), d['is_long'], d['sl'], d['tp'])
        if out not in ('TP','SL'): continue
        if out == 'TP': R.append(d['RR'])
        elif out == 'SL': R.append(-1.0)
    if not R: continue
    cum = np.cumsum(R); dd = float(np.max(np.maximum.accumulate(cum) - cum))
    print(f'{mode:>18} {len(R):>8} {sum(1 for x in R if x>0)/len(R):>5.0%} '
          f'{sum(R):>+9.1f}R {st.mean(R):>+10.2f}R {dd:>9.1f}R')
