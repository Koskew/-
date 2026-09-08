# -*- coding: utf-8 -*-
"""Сколько времени индикатор проводит в ПЕРЕХОДЕ и почему он там застревает.

Пауза «жду 2 новые медленные метки» считает КОЛЕНА, а не пивоты. В
одностороннем обвале каждый новый минимум сливается в то же самое
колено, счётчик меток не растёт, и тренд не подтверждается сколько бы
цена ни прошла.
"""
import csv, statistics

L = R = 5
F = 0.33

rows = [(r['time'], float(r['open']), float(r['high']), float(r['low']), float(r['close']))
        for r in csv.DictReader(open('data/XAUUSD_1h_2y.csv', encoding='utf-8-sig'))]
hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
for i in range(L, len(rows) - R):
    if all(hi[i-k] <= hi[i] for k in range(1, L+1)) and all(hi[i+k] < hi[i] for k in range(1, R+1)):
        at.setdefault(i + R, []).append((i, hi[i], True))
    if all(lo[i-k] >= lo[i] for k in range(1, L+1)) and all(lo[i+k] > lo[i] for k in range(1, R+1)):
        at.setdefault(i + R, []).append((i, lo[i], False))

up = lambda l: l in ("HH", "HL")
K = []; KL = []
tr, lvl, imp, inTrans, marks, lastD = 0, None, 0.0, False, 0, None
trStart = None                      # бар входа в ПЕРЕХОД
trPrice = None                      # цена на входе
merges = 0                          # слияний за текущий ПЕРЕХОД
spans = []                          # (баров, ход в импульсах, слияний, новых колен)
newK = 0
inTransBars = 0

def relabel():
    KL.clear()
    for i in range(len(K)):
        h = K[i][2]; prev = None
        for j in range(i-1, -1, -1):
            if K[j][2] == h: prev = K[j][1]; break
        KL.append("?" if prev is None else
                  (("HH" if K[i][1] > prev else "LH") if h else ("HL" if K[i][1] > prev else "LL")))

for b in range(len(rows)):
    o, h, l, c = rows[b][1], rows[b][2], rows[b][3], rows[b][4]
    bLo, bHi = min(o, c), max(o, c)
    if inTrans: inTransBars += 1

    if lvl is not None and tr != 0:
        need = imp * F
        died = (tr == 1 and bLo < lvl - need) or (tr == -1 and bHi > lvl + need)
        if died and lastD is not None and abs(lvl - lastD) < 1e-9: died = False
        if died:
            lastD = lvl; inTrans = True; marks = 0; lvl = None
            trStart, trPrice, merges, newK = b, c, 0, 0

    fresh = False
    for bar, price, isHi in at.get(b, []):
        if K and K[-1][2] == isHi:
            if (price > K[-1][1]) == isHi:
                K[-1] = (bar, price, isHi)
            if inTrans: merges += 1
        else:
            K.append((bar, price, isHi)); fresh = True
            if inTrans: newK += 1
    if at.get(b): relabel()          # метки пересчитываются и при слиянии
    if fresh: marks += 1

    if len(KL) >= 2 and fresh:
        l1, l2 = KL[-1], KL[-2]; p1, p2 = K[-1][1], K[-2][1]
        if tr != 0 and ((tr == 1) == (p1 > p2)): imp = abs(p1 - p2)
        u2, d2 = up(l1) and up(l2), (not up(l1)) and (not up(l2))
        if tr == 0:
            if u2 or d2: tr, imp = (1 if u2 else -1), abs(p1 - p2)
        elif inTrans and marks >= 2 and (u2 or d2):
            if trStart is not None:
                spans.append((b - trStart, abs(c - trPrice) / max(imp, 1e-9), merges, newK))
            tr, inTrans, lastD, imp = (1 if u2 else -1), False, None, abs(p1 - p2)
        if tr == 1:
            if l1 == "HL": lvl = p1
            if lvl is None: lvl = next((K[j][1] for j in range(len(KL)-1, -1, -1) if KL[j] == "HL"), None)
        elif tr == -1:
            if l1 == "LH": lvl = p1
            if lvl is None: lvl = next((K[j][1] for j in range(len(KL)-1, -1, -1) if KL[j] == "LH"), None)

d = [x[0] for x in spans]
q = statistics.quantiles(d, n=10)
print(f'баров всего {len(rows)},  ПЕРЕХОДОВ завершилось {len(spans)}')
print(f'в ПЕРЕХОДЕ проведено {inTransBars} баров = {inTransBars/len(rows):.0%} всего времени\n')
print(f'длительность ПЕРЕХОДА, баров:  медиана {statistics.median(d):.0f}   '
      f'90-й перцентиль {q[8]:.0f}   максимум {max(d)}')
print(f'дольше 20 баров: {sum(1 for x in d if x > 20)} из {len(spans)} = {sum(1 for x in d if x > 20)/len(spans):.0%}')
print(f'дольше 40 баров: {sum(1 for x in d if x > 40)} из {len(spans)} = {sum(1 for x in d if x > 40)/len(spans):.0%}\n')

print('чем длиннее ПЕРЕХОД, тем больше в нём СЛИЯНИЙ вместо новых колен:')
print(f'{"длина":>12} {"случаев":>8} {"новых колен":>13} {"слияний":>9} {"ход в импульсах":>17}')
for lo_, hi_, nm in ((0, 11, 'до 10 баров'), (11, 21, '11-20'), (21, 41, '21-40'), (41, 9999, '41 и больше')):
    sel = [x for x in spans if lo_ <= x[0] < hi_]
    if not sel: continue
    print(f'{nm:>12} {len(sel):>8} {statistics.mean(x[3] for x in sel):>12.1f} '
          f'{statistics.mean(x[2] for x in sel):>9.1f} {statistics.median(x[1] for x in sel):>16.1f}')
