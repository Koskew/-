# -*- coding: utf-8 -*-
"""Реплика f_cstart / f_cdir / f_chainCur из gde_my_v4.pine."""
import csv, sys
L = R = 5
rows = [(r['time'], float(r['high']), float(r['low']))
        for r in csv.DictReader(open('data/XAUUSD_1h_2y.csv', encoding='utf-8-sig'))]
CUT = '2025-12-31T06'          # состояние на момент скрина
rows = [r for r in rows if r[0] < CUT]

hi = [r[1] for r in rows]; lo = [r[2] for r in rows]; pv = []
for i in range(L, len(rows) - R):
    if all(hi[i-k] <= hi[i] for k in range(1, L+1)) and all(hi[i+k] < hi[i] for k in range(1, R+1)):
        pv.append((i, hi[i], True))
    if all(lo[i-k] >= lo[i] for k in range(1, L+1)) and all(lo[i+k] > lo[i] for k in range(1, R+1)):
        pv.append((i, lo[i], False))
pv.sort()

K = []                                   # (bar, price, isHi, merged)
for bar, price, isHi in pv:
    if K and K[-1][2] == isHi:
        b, p, h, m = K[-1]
        K[-1] = ((bar, price, isHi, m + 1) if (price > p) == isHi else (b, p, h, m + 1))
    else:
        K.append((bar, price, isHi, 1))

def lab(i):
    h = K[i][2]; prev = None
    for j in range(i - 1, -1, -1):
        if K[j][2] == h:
            prev = K[j][1]; break
    if prev is None: return "?"
    return ("HH" if K[i][1] > prev else "LH") if h else ("HL" if K[i][1] > prev else "LL")

KL = [lab(i) for i in range(len(K))]
isUp = lambda l: l in ("HH", "HL")

KN = [-1] * len(KL)                      # f_recount
if len(KL) >= 2:
    o, d, guard = 0, 1 if isUp(KL[1]) else -1, 0
    while guard < 500:
        guard += 1
        pts, i = 0, o + 1
        while i < len(KL) and pts < 5:
            if isUp(KL[i]) != (d > 0): break
            pts += 1; i += 1
        for k in range(pts + 1):
            if o + k < len(KL): KN[o + k] = k
        e = o + pts; x = e + 1
        if x >= len(KL): break
        nd = d if pts == 5 else (1 if isUp(KL[x]) else -1)
        needHi = nd < 0
        j = next((q for q in range(x, -1, -1) if K[q][2] == needHi), -1)
        if j <= o: j = x          # гарантия движения вперёд, как в Pine
        o, d = j, nd

cs = next((i for i in range(len(KN) - 1, -1, -1) if KN[i] == 0), -1)
cd = 0 if cs < 0 or cs + 1 >= len(KL) else (1 if isUp(KL[cs + 1]) else -1)
cnt = len(KL) - cs
mud = sum(1 for q in range(cs, len(KL)) if K[q][3] >= 2)

print(f'колен всего {len(K)}, последнее {rows[K[-1][0]][0]}')
print(f'счёт        точка ({KN[-1]}) из 5')
print(f'колено      {"импульсное" if KN[-1] % 2 else "корректирующее"} ({KN[-1]})'
      f'{" восходящего счёта" if cd == 1 else " нисходящего счёта" if cd == -1 else ""}')
print(f'цепочка     {">".join(KL[cs:])}   ({cnt} колен от нуля)')
print(f'чистота     мутных в счёте: {mud} из {cnt}')
print()
print('колена действующего счёта:')
for i in range(cs, len(KL)):
    print(f'   ({KN[i]}) {KL[i]:>2}  {K[i][1]:>9.2f}  {rows[K[i][0]][0][:16]}  '
          f'{"МУТНОЕ x" + str(K[i][3]) if K[i][3] >= 2 else "чистое"}')
