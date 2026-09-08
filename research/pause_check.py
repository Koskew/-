# -*- coding: utf-8 -*-
"""Пауза после смерти тренда: считать КОЛЕНА или сырые МЕТКИ.

Правило было сформулировано как «жду 2 следующие медленные метки».
Сейчас индикатор считает колена: в одностороннем движении новый минимум
сливается в то же колено, метка есть, колена нет, счётчик стоит.

вариант «колена» — как сейчас
вариант «метки»  — пауза считает сырые пивоты, и подтверждение тренда
                   проверяется на любой новой метке, а не только на новом колене
"""
import csv, statistics, bisect

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

def run(mode, jump=0.0, prov=False):
    K = []; KL = []
    tr, lvl, imp, inTrans, marks, lastD = 0, None, 0.0, False, 0, None
    trStart, trFrom = None, None
    spans, lives, conf, inTransBars = [], [], [], 0

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
                if trFrom is not None: lives.append(b - trFrom)
                lastD = lvl; inTrans = True; marks = 0; lvl = None; trStart = b

        # ── досрочное подтверждение: цена ушла от уровня смерти дальше
        # чем jump импульсов в сторону, противоположную умершему тренду ──
        if jump > 0 and inTrans and len(KL) >= 2 and imp > 0:
            l1, l2 = KL[-1], KL[-2]
            u2, d2 = up(l1) and up(l2), (not up(l1)) and (not up(l2))
            far = (d2 and c < lastD - imp * jump) or (u2 and c > lastD + imp * jump)
            if far:
                if trStart is not None: spans.append(b - trStart)
                tr, trFrom, inTrans, imp = (1 if u2 else -1), b, False, imp
                dl = lastD
                lastD = None
                conf.append(b)
                if prov:
                    # провизорный уровень: тот самый, что убил прошлый тренд
                    lvl = dl
                elif tr == 1:
                    lvl = next((K[j][1] for j in range(len(KL)-1, -1, -1) if KL[j] == "HL"), None)
                else:
                    lvl = next((K[j][1] for j in range(len(KL)-1, -1, -1) if KL[j] == "LH"), None)

        fresh = False; anyMark = False
        for bar, price, isHi in at.get(b, []):
            anyMark = True
            if K and K[-1][2] == isHi:
                if (price > K[-1][1]) == isHi: K[-1] = (bar, price, isHi)
            else:
                K.append((bar, price, isHi)); fresh = True
        if anyMark: relabel()
        if mode == 'колена':
            if fresh: marks += 1
        else:
            if anyMark: marks += 1
        act = fresh if mode == 'колена' else anyMark

        if len(KL) >= 2 and act:
            l1, l2 = KL[-1], KL[-2]; p1, p2 = K[-1][1], K[-2][1]
            if tr != 0 and ((tr == 1) == (p1 > p2)): imp = abs(p1 - p2)
            u2, d2 = up(l1) and up(l2), (not up(l1)) and (not up(l2))
            if tr == 0:
                if u2 or d2: tr, trFrom, imp = (1 if u2 else -1), b, abs(p1 - p2)
            elif inTrans and marks >= 2 and (u2 or d2):
                if trStart is not None: spans.append(b - trStart)
                tr, trFrom, inTrans, lastD, imp = (1 if u2 else -1), b, False, None, abs(p1 - p2)
                conf.append(b)
            if tr == 1:
                if l1 == "HL": lvl = p1
                if lvl is None: lvl = next((K[j][1] for j in range(len(KL)-1, -1, -1) if KL[j] == "HL"), None)
            elif tr == -1:
                if l1 == "LH": lvl = p1
                if lvl is None: lvl = next((K[j][1] for j in range(len(KL)-1, -1, -1) if KL[j] == "LH"), None)
    return spans, lives, conf, inTransBars

print(f'{"":>10} {"ПЕРЕХОДОВ":>10} {"медиана":>9} {">20б":>6} {"время в":>9} {"жизнь":>8} {"умерли за":>11}')
print(f'{"":>10} {"":>10} {"длина":>9} {"":>6} {"ПЕРЕХОДЕ":>9} {"тренда":>8} {"10 баров":>11}')
VAR = (('колена',0.0,False,'колена'), ('колена',0.5,False,'рывок 0.5'),
       ('колена',0.5,True, 'рывок 0.5 + провиз'), ('колена',1.0,True,'рывок 1.0 + провиз'))
for mode, jp, pv, nm in VAR:
    sp, li, cf, tb = run(mode, jp, pv)
    mode = nm
    dead = sorted(li)
    # сколько подтверждений умерло в пределах 10 баров
    early = sum(1 for x in li if x <= 10)
    print(f'{mode:>10} {len(sp):>10} {statistics.median(sp):>8.0f}б '
          f'{sum(1 for x in sp if x > 20)/len(sp):>5.0%} {tb/len(rows):>8.0%} '
          f'{statistics.median(li):>7.0f}б {early/len(li):>10.0%}')
