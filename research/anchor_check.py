# -*- coding: utf-8 -*-
"""Как часто ноль счёта НЕ совпадает с правилом:
нисходящий счёт стартует с HH, восходящий с LL."""
import csv, collections
L = R = 5
rows = [(r['time'], float(r['high']), float(r['low']))
        for r in csv.DictReader(open('data/XAUUSD_1h_2y.csv', encoding='utf-8-sig'))]
hi = [r[1] for r in rows]; lo = [r[2] for r in rows]; pv = []
for i in range(L, len(rows) - R):
    if all(hi[i-k] <= hi[i] for k in range(1, L+1)) and all(hi[i+k] < hi[i] for k in range(1, R+1)):
        pv.append((i, hi[i], True))
    if all(lo[i-k] >= lo[i] for k in range(1, L+1)) and all(lo[i+k] > lo[i] for k in range(1, R+1)):
        pv.append((i, lo[i], False))
pv.sort()
K = []
for bar, price, isHi in pv:
    if K and K[-1][2] == isHi:
        b, p, h, m = K[-1]
        K[-1] = ((bar, price, isHi, m+1) if (price > p) == isHi else (b, p, h, m+1))
    else:
        K.append((bar, price, isHi, 1))
def lab(i):
    h = K[i][2]; prev = None
    for j in range(i-1, -1, -1):
        if K[j][2] == h: prev = K[j][1]; break
    if prev is None: return "?"
    return ("HH" if K[i][1] > prev else "LH") if h else ("HL" if K[i][1] > prev else "LL")
KL = [lab(i) for i in range(len(K))]
up = lambda l: l in ("HH", "HL")
KN = [-1]*len(KL); starts = []
o, d, g = 0, 1 if up(KL[1]) else -1, 0
while g < 5000:
    g += 1
    pts, i = 0, o+1
    while i < len(KL) and pts < 5:
        if up(KL[i]) != (d > 0): break
        pts += 1; i += 1
    starts.append((o, d, pts))
    for k in range(pts+1):
        if o+k < len(KL): KN[o+k] = k
    e = o+pts; x = e+1
    if x >= len(KL): break
    nd = d if pts == 5 else (1 if up(KL[x]) else -1)
    needHi = nd < 0
    j = next((q for q in range(x, -1, -1) if K[q][2] == needHi), -1)
    if j <= o: j = x
    o, d = j, nd

c = collections.Counter()
bad = []
for o, d, pts in starts:
    want = "LL" if d == 1 else "HH"
    ok = KL[o] == want
    c[(('вверх' if d == 1 else 'вниз'), KL[o])] += 1
    if not ok: bad.append((o, d, KL[o], pts))
tot = len(starts)
print(f'счётов всего: {tot}')
for (dr, l), n in sorted(c.items(), key=lambda x: -x[1]):
    want = "LL" if dr == 'вверх' else "HH"
    print(f'  счёт {dr:>5}, ноль = {l:>2}  {n:>4}  {n/tot:>5.0%}  {"по правилу" if l == want else "НАРУШЕНИЕ"}')
print(f'\nнарушений {len(bad)} из {tot} = {len(bad)/tot:.0%}')
print('глубина счёта при нарушении vs всего:')
import statistics
print(f'  все счёты: медиана {statistics.median([p for _,_,p in starts])} точек')
if bad:
    print(f'  нарушения: медиана {statistics.median([p for *_ ,p in bad])} точек')

print()
print('разбивка по глубине счёта:')
print(f'{"точек":>6} {"счётов":>7} {"по правилу":>11} {"доля":>6}')
for depth in range(0, 6):
    grp = [(o, d, p) for o, d, p in starts if p == depth]
    if not grp: continue
    ok = sum(1 for o, d, p in grp if KL[o] == ("LL" if d == 1 else "HH"))
    print(f'{depth:>6} {len(grp):>7} {ok:>11} {ok/len(grp):>5.0%}')
