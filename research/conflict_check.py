# -*- coding: utf-8 -*-
"""Расхождение тренда и счёта: тренд ещё ВОСХОДЯЩИЙ, а счёт уже пошёл вниз.

Вопрос: это ранний сигнал смерти тренда или шум? Меряем вероятность
смерти тренда за N баров при согласии и при расхождении.
"""
import csv, statistics, bisect, sys

L = R = 5
H = 10

def load(path):
    return [(r['time'], float(r['open']), float(r['high']), float(r['low']), float(r['close']))
            for r in csv.DictReader(open(path, encoding='utf-8-sig'))]

up = lambda l: l in ("HH", "HL")

def run(rows, f=0.33, cut=None):
    n = len(rows) if cut is None else cut
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]
    at = {}
    for i in range(L, len(rows) - R):
        if all(hi[i-k] <= hi[i] for k in range(1, L+1)) and all(hi[i+k] < hi[i] for k in range(1, R+1)):
            at.setdefault(i + R, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, L+1)) and all(lo[i+k] > lo[i] for k in range(1, R+1)):
            at.setdefault(i + R, []).append((i, lo[i], False))

    K, KL, KN = [], [], []
    tr, lvl, impAmp, trFrom = 0, None, 0.0, None
    inTrans, marks, lastDeath = False, 0, None
    deaths, recs = [], []

    def relabel():
        KL.clear()
        for i in range(len(K)):
            h = K[i][2]; prev = None
            for j in range(i-1, -1, -1):
                if K[j][2] == h: prev = K[j][1]; break
            KL.append("?" if prev is None else
                      (("HH" if K[i][1] > prev else "LH") if h else ("HL" if K[i][1] > prev else "LL")))

    def recount():
        KN[:] = [-1]*len(KL)
        if len(KL) < 2: return
        o, d, g = 0, 1 if up(KL[1]) else -1, 0
        while g < 500:
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

    for b in range(n):
        o_, h_, l_, c_ = rows[b][1], rows[b][2], rows[b][3], rows[b][4]
        bLo, bHi = min(o_, c_), max(o_, c_)
        if lvl is not None and tr != 0:
            need = impAmp * f
            died = (tr == 1 and bLo < lvl - need) or (tr == -1 and bHi > lvl + need)
            if died and lastDeath is not None and abs(lvl - lastDeath) < 1e-9: died = False
            if died:
                deaths.append(b); lastDeath = lvl
                inTrans, marks, lvl = True, 0, None

        fresh = False
        for bar, price, isHi in at.get(b, []):
            if K and K[-1][2] == isHi:
                if (price > K[-1][1]) == isHi: K[-1] = (bar, price, isHi)
            else:
                K.append((bar, price, isHi)); fresh = True
        if fresh:
            relabel(); recount(); marks += 1

        if len(KL) >= 2 and fresh:
            l1, l2 = KL[-1], KL[-2]; p1, p2 = K[-1][1], K[-2][1]
            if tr != 0 and ((tr == 1) == (p1 > p2)): impAmp = abs(p1 - p2)
            u2, d2 = up(l1) and up(l2), (not up(l1)) and (not up(l2))
            if tr == 0:
                if u2 or d2: tr, trFrom, impAmp = (1 if u2 else -1), b, abs(p1-p2)
            elif inTrans and marks >= 2 and (u2 or d2):
                tr, trFrom, inTrans, lastDeath, impAmp = (1 if u2 else -1), b, False, None, abs(p1-p2)
            if tr == 1:
                if l1 == "HL": lvl = p1
                if lvl is None: lvl = next((K[j][1] for j in range(len(KL)-1,-1,-1) if KL[j]=="HL"), None)
            elif tr == -1:
                if l1 == "LH": lvl = p1
                if lvl is None: lvl = next((K[j][1] for j in range(len(KL)-1,-1,-1) if KL[j]=="LH"), None)

        if tr != 0 and not inTrans and KN:
            cs = next((i for i in range(len(KN)-1, -1, -1) if KN[i] == 0), -1)
            if cs >= 0:
                cd = (1 if up(KL[cs+1]) else -1) if cs+1 < len(KL) else (-1 if K[cs][2] else 1)
                recs.append((b, tr, cd, KN[-1]))

    return deaths, recs, K, KL, KN

rows = load('data/XAUUSD_1h_2y.csv')

# 1) сверка с экраном
CUT = 8370      # включая бар 2026-01-15T13:00, закрытие 4619.3
d, rc, K, KL, KN = run(rows, cut=CUT)
cs = next((i for i in range(len(KN)-1, -1, -1) if KN[i] == 0), -1)
cd = (1 if up(KL[cs+1]) else -1) if cs+1 < len(KL) else (-1 if K[cs][2] else 1)
print('последние колена на 15.01.2026 13:00:')
for i in range(len(K)-5, len(K)):
    print(f'   ({KN[i]}) {KL[i]:>2} {K[i][1]:>9.2f}  {rows[K[i][0]][0][:16]}{"   <- ноль" if i == cs else ""}')
frm = max(0, min(cs, len(KL)-4))
ch = "".join((" | " if j == cs and j > frm else ">" if j > frm else "") + KL[j] for j in range(frm, len(KL)))
print(f'\nцепочка   {ch}')
print(f'счёт      точка ({KN[-1]}), направление {"вверх" if cd==1 else "вниз"}')

# 2) расхождение тренда и счёта как ранний сигнал
d, rc, *_ = run(rows)
ds = sorted(d)
def dies(b, hor):
    i = bisect.bisect_right(ds, b)
    return i < len(ds) and ds[i] - b <= hor
print(f'\nРАСХОЖДЕНИЕ ТРЕНДА И СЧЁТА  ({len(rc)} баров в живом тренде)')
print(f'{"":>22} {"баров":>7}' + "".join(f'{"умер за "+str(h)+"б":>13}' for h in (5, 10, 20, 40)))
for name, sel in (("счёт СОГЛАСЕН с трендом", [x for x in rc if x[1] == x[2]]),
                  ("счёт ПРОТИВ тренда",      [x for x in rc if x[1] != x[2]]),
                  ("все бары",                rc)):
    line = f'{name:>22} {len(sel):>7}'
    for hor in (5, 10, 20, 40):
        line += f'{sum(1 for x in sel if dies(x[0], hor))/len(sel):>12.0%} ' if sel else f'{"—":>13}'
    print(line)
