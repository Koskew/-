# -*- coding: utf-8 -*-
"""Каким получается уровень тренда сразу после подтверждения.

Подтверждение по рывку приходит раньше, чем формируется новая метка
LH или HL. Код уходит назад по коленам и берёт последнюю подходящую —
а она может быть на вершине прошлого движения, за сотни долларов.
"""
import csv, statistics

L = R = 5; F = 0.33; JUMP = 0.5
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
pend = None          # ждём появления настоящей метки после рывка
res = {'рывок': [], 'пауза': []}
wait = []

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
    if lvl is not None and tr != 0:
        need = imp * F
        died = (tr == 1 and bLo < lvl - need) or (tr == -1 and bHi > lvl + need)
        if died and lastD is not None and abs(lvl - lastD) < 1e-9: died = False
        if died:
            lastD = lvl; inTrans = True; marks = 0; lvl = None; pend = None

    if inTrans and len(KL) >= 2 and imp > 0:
        l1, l2 = KL[-1], KL[-2]
        u2, d2 = up(l1) and up(l2), (not up(l1)) and (not up(l2))
        if (d2 and c < lastD - imp*JUMP) or (u2 and c > lastD + imp*JUMP):
            tr, inTrans = (1 if u2 else -1), False; lastD = None
            want = "HL" if tr == 1 else "LH"
            lvl = next((K[j][1] for j in range(len(KL)-1, -1, -1) if KL[j] == want), None)
            if lvl is not None and imp > 0:
                res['рывок'].append(abs(c - lvl) / imp)
            pend = (b, tr)

    fresh = False; anyM = False
    for bar, price, isHi in at.get(b, []):
        anyM = True
        if K and K[-1][2] == isHi:
            if (price > K[-1][1]) == isHi: K[-1] = (bar, price, isHi)
        else:
            K.append((bar, price, isHi)); fresh = True
    if anyM: relabel()
    if fresh: marks += 1

    if len(KL) >= 2 and fresh:
        l1, l2 = KL[-1], KL[-2]; p1, p2 = K[-1][1], K[-2][1]
        if tr != 0 and ((tr == 1) == (p1 > p2)): imp = abs(p1 - p2)
        u2, d2 = up(l1) and up(l2), (not up(l1)) and (not up(l2))
        if tr == 0:
            if u2 or d2: tr, imp = (1 if u2 else -1), abs(p1 - p2)
        elif inTrans and marks >= 2 and (u2 or d2):
            tr, inTrans, lastD, imp = (1 if u2 else -1), False, None, abs(p1 - p2)
            want = "HL" if tr == 1 else "LH"
            lv = next((K[j][1] for j in range(len(KL)-1, -1, -1) if KL[j] == want), None)
            if lv is not None and imp > 0: res['пауза'].append(abs(c - lv) / imp)
            pend = None
        # свежая метка нужной стороны закрывает ожидание после рывка
        if pend is not None and tr != 0:
            want = "HL" if tr == 1 else "LH"
            if l1 == want:
                wait.append(b - pend[0]); pend = None
        if tr == 1:
            if l1 == "HL": lvl = p1
            if lvl is None: lvl = next((K[j][1] for j in range(len(KL)-1, -1, -1) if KL[j] == "HL"), None)
        elif tr == -1:
            if l1 == "LH": lvl = p1
            if lvl is None: lvl = next((K[j][1] for j in range(len(KL)-1, -1, -1) if KL[j] == "LH"), None)

print('расстояние от цены до уровня в момент подтверждения, в импульсах:\n')
print(f'{"путь":>8} {"случаев":>8} {"медиана":>9} {"90-й":>7} {"доля > 1.5":>12}')
for k in ('пауза', 'рывок'):
    v = res[k]
    if not v: continue
    q = statistics.quantiles(v, n=10)
    print(f'{k:>8} {len(v):>8} {statistics.median(v):>8.2f} {q[8]:>7.2f} '
          f'{sum(1 for x in v if x > 1.5)/len(v):>11.0%}')
print(f'\nпосле рывка новая метка нужной стороны появляется через')
if wait:
    print(f'  медиана {statistics.median(wait):.0f} баров, 90-й перцентиль {statistics.quantiles(wait,n=10)[8]:.0f}, максимум {max(wait)}')
    print(f'  случаев {len(wait)} из {len(res["рывок"])} подтверждений по рывку')
