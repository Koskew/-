# -*- coding: utf-8 -*-
"""Что даёт фильтр глубины слома (fibDepth) на истории.

Реплика тренда из gde_my_v4.pine: колена 5/5, метка по предыдущему
колену той же стороны, тренд рождается на двух подряд метках одной
стороны, уровень = последний HL (вверх) / LH (вниз), смерть — когда
тело закрытого бара уходит за уровень глубже impAmp * f.
"""
import csv, statistics, sys

L = R = 5

def load(path):
    return [(r['time'], float(r['open']), float(r['high']), float(r['low']), float(r['close']))
            for r in csv.DictReader(open(path, encoding='utf-8-sig'))]

def pivots(rows):
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; out = []
    for i in range(L, len(rows) - R):
        if all(hi[i-k] <= hi[i] for k in range(1, L+1)) and all(hi[i+k] < hi[i] for k in range(1, R+1)):
            out.append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, L+1)) and all(lo[i+k] > lo[i] for k in range(1, R+1)):
            out.append((i, lo[i], False))
    out.sort(); return out

up = lambda l: l in ("HH", "HL")

def run(rows, f):
    """Прогон по барам, как в Pine: колено видно через R баров после пивота."""
    pv = pivots(rows)
    at = {}
    for bar, price, isHi in pv:
        at.setdefault(bar + R, []).append((bar, price, isHi))

    K = []                       # (bar, price, isHi)
    KL = []
    tr, lvl, impAmp, trFrom = 0, None, 0.0, None
    inTrans, marks, lastDeath = False, 0, None
    deaths, lives, gaps = [], [], []

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

        # 1. слом
        if lvl is not None and tr != 0:
            need = impAmp * f
            died = (tr == 1 and bLo < lvl - need) or (tr == -1 and bHi > lvl + need)
            if died and lastDeath is not None and abs(lvl - lastDeath) < 1e-9:
                died = False
            if died:
                deaths.append(b)
                if trFrom is not None: lives.append(b - trFrom)
                lastDeath = lvl
                inTrans, marks, lvl = True, 0, None

        # 2. новые колена
        fresh = False
        for bar, price, isHi in at.get(b, []):
            if K and K[-1][2] == isHi:
                if (price > K[-1][1]) == isHi:
                    K[-1] = (bar, price, isHi)
            else:
                K.append((bar, price, isHi)); fresh = True
        if fresh:
            relabel(); marks += 1

        if len(KL) >= 2 and fresh:
            l1, l2 = KL[-1], KL[-2]
            p1, p2 = K[-1][1], K[-2][1]
            if tr != 0 and ((tr == 1) == (p1 > p2)):
                impAmp = abs(p1 - p2)
            u2, d2 = up(l1) and up(l2), (not up(l1)) and (not up(l2))
            if tr == 0:
                if u2 or d2:
                    tr, trFrom, impAmp = (1 if u2 else -1), b, abs(p1 - p2)
            elif inTrans and marks >= 2 and (u2 or d2):
                tr, trFrom, inTrans, lastDeath, impAmp = (1 if u2 else -1), b, False, None, abs(p1 - p2)
            if tr == 1:
                if l1 == "HL": lvl = p1
                if lvl is None:
                    lvl = next((K[j][1] for j in range(len(KL)-1, -1, -1) if KL[j] == "HL"), None)
            elif tr == -1:
                if l1 == "LH": lvl = p1
                if lvl is None:
                    lvl = next((K[j][1] for j in range(len(KL)-1, -1, -1) if KL[j] == "LH"), None)

        # запас: сколько ещё есть хода до порога смерти
        if lvl is not None and tr != 0 and not inTrans:
            thr = lvl - impAmp * f if tr == 1 else lvl + impAmp * f
            gaps.append((b, tr, abs(c - thr), impAmp * f, impAmp))

    return deaths, lives, gaps

rows = load(sys.argv[1] if len(sys.argv) > 1 else 'data/XAUUSD_1h_2y.csv')
print(f'баров {len(rows)}   {rows[0][0][:10]} — {rows[-1][0][:10]}\n')
print(f'{"fibDepth":>9} {"сломов":>7} {"медиана жизни":>14} {"порог, $":>10}')
base = None
for f in (0.0, 0.15, 0.33, 0.5, 0.75):
    d, li, g = run(rows, f)
    if base is None: base = len(d)
    med = statistics.median(li) if li else 0
    thr = statistics.median([x[3] for x in g]) if g else 0
    print(f'{f:>9.2f} {len(d):>7} {med:>12.0f}б {thr:>10.1f}   '
          f'{"" if f == 0 else f"отсеяно {1 - len(d)/base:.0%} сломов"}')

# ── предсказывает ли запас скорую смерть тренда ──
import bisect
d, li, g = run(rows, 0.33)
ds = sorted(d)
H = 10                                   # горизонт: умрёт ли тренд за 10 баров

print(f'\nЗАПАС ДО ПОРОГА СМЕРТИ — предсказывает ли он что-нибудь')
print(f'({len(g)} баров в живом тренде, горизонт {H} баров)\n')
med_imp = statistics.median([x[4] for x in g])
print(f'медиана импульсного колена {med_imp:.1f}$   медиана порога {statistics.median([x[3] for x in g]):.1f}$')
print(f'медиана ОСТАВШЕГОСЯ хода до порога {statistics.median([x[2] for x in g]):.1f}$\n')

def dies(b):
    i = bisect.bisect_right(ds, b)
    return i < len(ds) and ds[i] - b <= H

# доля запаса от импульсного колена — величина без размерности
buckets = [(0, .25), (.25, .5), (.5, 1.0), (1.0, 2.0), (2.0, 99)]
print(f'{"запас / импульс":>16} {"баров":>7} {"умер за 10 бар":>16}')
for lo_, hi_ in buckets:
    sel = [x for x in g if lo_ <= x[2] / x[4] < hi_] if True else []
    if not sel: continue
    p = sum(1 for x in sel if dies(x[0])) / len(sel)
    print(f'{lo_:>7.2f}–{hi_ if hi_ < 99 else float("inf"):<8.2f} {len(sel):>7} {p:>15.0%}')
base_p = sum(1 for x in g if dies(x[0])) / len(g)
print(f'{"в среднем":>16} {len(g):>7} {base_p:>15.0%}')

# размер импульсного колена относительно рынка — про волатильность
print(f'\n{"импульс / медиану":>18} {"баров":>7} {"умер за 10 бар":>16}')
for lo_, hi_ in [(0, .6), (.6, 1.0), (1.0, 1.6), (1.6, 99)]:
    sel = [x for x in g if lo_ <= x[4] / med_imp < hi_]
    if not sel: continue
    p = sum(1 for x in sel if dies(x[0])) / len(sel)
    print(f'{lo_:>8.2f}–{hi_ if hi_ < 99 else float("inf"):<8.2f} {len(sel):>7} {p:>15.0%}')
