# -*- coding: utf-8 -*-
"""Проверка: ноль счёта ставится по подписи, совпадающей с трендом.

Восходящий тренд считается от LL, нисходящий от HH. Исключение на
продолжение: если прошлый счёт был того же направления и дошёл минимум
до (3), годится HL (вверх) или LH (вниз).

Проверяем главное, что владелец увидел на графике: не бывает ли
«тренд ВОСХОДЯЩИЙ, а ноль на HH».
"""
import sys, csv, collections
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
        self.czIdx = -1; self.lastTr = 0; self.lastTrans = False; self.pCdir = 0; self.pCmax = 0
        self.setz = []          # (бар, тренд, подпись нуля, продолжение?)
        self.fails = []

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
        want = 'LL' if d == 1 else 'HH'
        want2 = 'HL' if d == 1 else 'LH'
        if 0 <= self.czIdx < n:
            self.pCmax = self.KN[n-1]; self.pCdir = self.lastTr
        cont = self.pCdir == d and self.pCmax >= 3
        z = -1
        for i in range(n-1, -1, -1):
            lb = self.KL[i]
            if lb == want or (cont and lb == want2): z = i; break
        if z < 0:
            self.fails.append(b); return
        self.czIdx = z
        for k in range(n - z):
            self.KN[z + k] = k % 6
        self.setz.append((b, d, self.KL[z], cont))

    def step(self, b):
        super().step(b)
        if self.tr != 0 and not self.inTrans and (self.tr != self.lastTr or self.lastTrans):
            self._setZero(self.tr, b)
        self.lastTr = self.tr
        self.lastTrans = self.inTrans

for tag, path in (('2 года', 'data/XAUUSD_1h_2y.csv'), ('9 лет', 'data/XAUUSD_1h_9y.csv')):
    rows = load(path)
    e = Z(rows, fib=0.33, jump=0.5); e.at = pivots_n(rows, 3)
    bad = 0
    for b in range(len(rows)):
        e.step(b)
        if e.czIdx >= 0 and e.tr != 0 and not e.inTrans:
            lb = e.KL[e.czIdx]
            okUp = e.tr == 1 and lb in ('LL', 'HL')
            okDn = e.tr == -1 and lb in ('HH', 'LH')
            if not (okUp or okDn): bad += 1
    c = collections.Counter((d, lb) for _, d, lb, _ in e.setz)
    cont = sum(1 for _, _, _, k in e.setz if k)
    print('══ %s · 3/3' % tag)
    print('   постановок нуля %d · по продолжению %d (%d%%)' % (len(e.setz), cont, round(cont/max(len(e.setz),1)*100)))
    print('   подпись нуля: ' + '  '.join('%s %s %d' % ('восх' if d==1 else 'нисх', lb, v) for (d, lb), v in sorted(c.items(), key=lambda x:(-x[1]))))
    print('   баров, где ноль НЕ совпал с трендом: %d' % bad)
    print('   не нашли ноль: %d' % len(e.fails))
    print()
