# -*- coding: utf-8 -*-
"""Перекрываются ли тренды по времени.

Ноль нового счёта ищется НАЗАД по коленам до первого HH (вниз) или LL
(вверх). Такое колено может оказаться СТАРШЕ, чем смерть предыдущего
тренда. Тогда «возраст тренда» перестаёт быть временем его жизни и
становится расстоянием до нуля, а два тренда перекрываются.

Здесь считается, как часто так выходит и насколько далеко.
"""
import sys, csv, statistics as st
sys.path.insert(0, 'research')
import core
from core import Core

def load(p):
    out = []
    for r in csv.DictReader(open(p, encoding='utf-8-sig')):
        o, h, l, c = float(r['open']), float(r['high']), float(r['low']), float(r['close'])
        out.append((r['time'], min(max(o, l), h), h, l, min(max(c, l), h)))
    return out

def pivots_n(rows, N):
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
    for i in range(N, len(rows) - N):
        if all(hi[i-k] <= hi[i] for k in range(1, N+1)) and all(hi[i+k] < hi[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, N+1)) and all(lo[i+k] > lo[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, lo[i], False))
    return at

class Z(Core):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.czIdx = -1; self.czBar = None; self.czLab = ''
        self.lastTr = 0; self.lastTrans = False
        self.pCdir = 0; self.pCmax = 0
        self.ev = []            # (бар постановки, бар нуля, бар смерти прошлого)

    def _recount(self): pass

    def _push(self, bar, price, isHi):
        n = len(self.KP)
        same = n > 0 and self.KH[n-1] == isHi
        if same:
            old = self.KP[n-1]
            better = price > old if isHi else price < old
            self.KM[n-1] += 1
            if better: self.KP[n-1] = price; self.KB[n-1] = bar
            self._relabel(); return False
        prevN = self.KN[-1] if self.KN else -1
        newN = prevN + 1 if 0 <= prevN < 5 else 0
        self.KP.append(price); self.KB.append(bar); self.KH.append(isHi)
        self.KM.append(1); self.KT.append(self.tr); self.KX.append(self.inTrans)
        self.KN.append(newN)
        if len(self.KP) > core.MAXK:
            for a in (self.KP, self.KB, self.KH, self.KM, self.KT, self.KX, self.KN): a.pop(0)
            self.czIdx = self.czIdx - 1 if self.czIdx > 0 else (-1 if self.czIdx == 0 else self.czIdx)
        self._relabel(); return True

    def _setZero(self, d, b):
        n = len(self.KL)
        if 0 <= self.czIdx < n:
            self.pCmax = self.KN[n-1]; self.pCdir = self.lastTr
        want = 'LL' if d == 1 else 'HH'
        want2 = 'HL' if d == 1 else 'LH'
        cont = self.pCdir == d and self.pCmax >= 3
        z = -1
        for i in range(n-1, -1, -1):
            if self.KL[i] == want or (cont and self.KL[i] == want2): z = i; break
        if z < 0: return
        self.czIdx = z; self.czBar = self.KB[z]; self.czLab = self.KL[z]
        self.ev.append((b, self.czBar, self.pDb))

    def step(self, b):
        super().step(b)
        if self.tr != 0 and not self.inTrans and (self.tr != self.lastTr or self.lastTrans):
            self._setZero(self.tr, b)
        self.lastTr = self.tr
        self.lastTrans = self.inTrans

for tag, path in (('1H 9 лет', 'data/XAUUSD_1h_9y.csv'), ('5m 3.5 мес', 'data/XAUUSD_5m.csv')):
    rows = load(path)
    e = Z(rows, fib=0.33, jump=0.5); e.at = pivots_n(rows, 3)
    for b in range(len(rows)): e.step(b)
    ev = [x for x in e.ev if x[2] is not None]
    before = [x for x in ev if x[1] < x[2]]
    depth = [x[2] - x[1] for x in before]
    ageAtSet = [x[0] - x[1] for x in ev]
    print('══ %s · 3/3' % tag)
    print('   постановок нуля с известной смертью прошлого: %d' % len(ev))
    print('   ноль СТАРШЕ смерти прошлого тренда: %d (%.0f%%)'
          % (len(before), len(before) / max(len(ev), 1) * 100))
    if depth:
        depth.sort()
        print('      насколько старше, баров: медиана %d, три четверти до %d, максимум %d'
              % (depth[len(depth)//2], depth[int(len(depth)*.75)], max(depth)))
    ageAtSet.sort()
    print('   «возраст тренда» сразу в момент постановки нуля: медиана %d, максимум %d'
          % (ageAtSet[len(ageAtSet)//2], max(ageAtSet)))
    print()
