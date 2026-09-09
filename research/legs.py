# -*- coding: utf-8 -*-
"""Ноги счёта по номерам точек: сколько даёт каждая и чем рискуешь.

Торговля идёт от (2) к (3) и от (4) к (5). Считаем для каждой ноги:
  ход      — амплитуда ноги в медианных коленах слоя
  риск     — амплитуда ПРЕДЫДУЩЕЙ ноги: за неё пришлось бы ставить стоп
  отношение хода к риску — сколько R даёт нога, если стоп за точку входа
"""
import sys, statistics as st
sys.path.insert(0, 'research')
from core import load
from library import pivots_n

rows = load()
up = lambda l: l in ("HH", "HL")

def build(lb):
    at = pivots_n(rows, lb); K = []
    for b in sorted(at):
        for bar, price, isHi in at[b]:
            if K and K[-1][2] == isHi:
                if (price > K[-1][1]) == isHi: K[-1] = (bar, price, isHi)
            else:
                K.append((bar, price, isHi))
    KL = []
    for i in range(len(K)):
        h = K[i][2]; prev = None
        for j in range(i-1, -1, -1):
            if K[j][2] == h: prev = K[j][1]; break
        KL.append("?" if prev is None else (("HH" if K[i][1] > prev else "LH") if h else ("HL" if K[i][1] > prev else "LL")))
    KN = [-1]*len(KL)
    o, d, g = 0, 1 if up(KL[1]) else -1, 0
    while g < len(KL) + 10:
        g += 1
        pts, i = 0, o+1
        while i < len(KL) and pts < 5:
            if up(KL[i]) != (d > 0): break
            pts += 1; i += 1
        for k in range(pts+1):
            if o+k < len(KL): KN[o+k] = k
        e = o+pts; x = e+1
        if x >= len(KL): break
        nd = d if pts == 5 else (1 if up(KL[x]) else -1)
        j = next((q for q in range(x, -1, -1) if K[q][2] == (nd < 0)), -1)
        if j <= o: j = x
        o, d = j, nd
    return K, KL, KN

for lb, fib in ((5, 0.33), (2, 0.15)):
    K, KL, KN = build(lb)
    amps = [abs(K[i][1]-K[i-1][1]) for i in range(1, len(K))]
    med = st.median(amps)
    # направление счёта: сторона нуля
    def kd(i):
        z = next((j for j in range(i, -1, -1) if KN[j] == 0), -1)
        return 0 if z < 0 else (-1 if K[z][2] else 1)
    print(f'\n═══ СЛОЙ {lb}/{lb}   медианное колено {med:.1f}$ ═══\n')
    print(f'{"нога":>10} {"шт":>5} {"ход в коленах":>16} {"риск":>7} {"ход/риск":>10} {"доля >1R":>9}')
    print(f'{"":>10} {"":>5} {"мед":>7}{"90-й":>9} {"мед":>7} {"мед":>10} {"":>9}')
    for pt in (1, 2, 3, 4, 5):
        legs = []
        for i in range(2, len(K)):
            if KN[i] == pt and KN[i-1] == pt - 1:
                a = abs(K[i][1] - K[i-1][1])
                r = abs(K[i-1][1] - K[i-2][1])
                if r > 0: legs.append((a/med, a/r))
        if not legs: continue
        A = [x[0] for x in legs]; R = [x[1] for x in legs]
        q = st.quantiles(A, n=10)[8] if len(A) > 9 else max(A)
        tag = f'({pt-1})→({pt})'
        mark = '  ←' if pt in (3, 5) else ''
        print(f'{tag:>10} {len(legs):>5} {st.median(A):>7.2f}{q:>9.2f} '
              f'{st.median([abs(K[i][1]-K[i-1][1]) for i in range(2,len(K)) if KN[i]==pt and KN[i-1]==pt-1])/med:>7.2f} '
              f'{st.median(R):>10.2f} {sum(1 for x in R if x > 1)/len(R):>8.0%}{mark}')
    # доходимость: сколько счётов вообще добирается до каждой точки
    starts = [i for i, x in enumerate(KN) if x == 0]
    print(f'\n{"доходимость счёта":>20}')
    for pt in (1, 2, 3, 4, 5):
        c = 0
        for k, o in enumerate(starts):
            end = starts[k+1] if k+1 < len(starts) else len(KN)
            if max(KN[o:end]) >= pt: c += 1
        print(f'{"до ("+str(pt)+")":>20} {c:>5} из {len(starts)} = {c/len(starts):>4.0%}')

# ── честная оценка: входим на точке, а счёт может туда и не дойти ──
print('\n\n═══ ЧЕСТНАЯ ОЦЕНКА ВХОДА ПО ТОЧКАМ ═══')
print('Вход на подтверждённой точке (2) или (4), цель — следующая точка,')
print('стоп 1R = амплитуда предыдущей коррекционной ноги.')
print('Учтены счёты, которые до цели НЕ дошли.\n')
for lb in (5, 2):
    K, KL, KN = build(lb)
    starts = [i for i, x in enumerate(KN) if x == 0]
    print(f'слой {lb}/{lb}')
    print(f'{"вход":>10} {"счётов дошло":>14} {"дошло до цели":>15} {"ход, R":>9} {"матожидание":>13}')
    for entry in (2, 4):
        got_e = got_t = 0
        Rs = []
        for k, o in enumerate(starts):
            end = starts[k+1] if k+1 < len(starts) else len(KN)
            mx = max(KN[o:end])
            if mx >= entry:
                got_e += 1
                if mx >= entry + 1:
                    got_t += 1
                    i = next(j for j in range(o, end) if KN[j] == entry + 1)
                    a = abs(K[i][1] - K[i-1][1])
                    r = abs(K[i-1][1] - K[i-2][1])
                    if r > 0: Rs.append(a / r)
        if not Rs: continue
        p = got_t / got_e
        med = st.median(Rs)
        ev = p * med - (1 - p) * 1.0
        print(f'{"("+str(entry)+")→("+str(entry+1)+")":>10} {got_e:>14} '
              f'{got_t:>10} = {p:>3.0%} {med:>8.2f} {ev:>12.2f}R')
    print()
