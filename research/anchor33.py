# -*- coding: utf-8 -*-
"""Проверка правки: номер точки живёт вместе с коленом.

Счёт идёт по коленам подряд 0..5 и снова 0. После слома отсчёт
начинается заново: первое появившееся колено становится точкой (0).
Номер присваивается при рождении колена и задним числом не меняется —
поэтому вся история остаётся пронумерованной.
"""
import sys, csv, collections, statistics as st
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

class Anch(Core):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.czWait = False
        self.curB = 0
        self.born = []        # (номер, бар) каждого созданного колена
        self.deaths = []

    def _recount(self):
        pass                  # счёт больше не пересчитывается

    def _push(self, bar, price, isHi):
        n = len(self.KP)
        same = n > 0 and self.KH[n-1] == isHi
        if same:
            old = self.KP[n-1]
            better = price > old if isHi else price < old
            self.KM[n-1] += 1
            if better: self.KP[n-1] = price; self.KB[n-1] = bar
            self._relabel()
            return False
        prevN = self.KN[-1] if self.KN else -1
        newN = 0
        if self.czWait:
            newN = 0; self.czWait = False
        elif 0 <= prevN < 5:
            newN = prevN + 1
        self.KP.append(price); self.KB.append(bar); self.KH.append(isHi)
        self.KM.append(1)
        self.KT.append(self.tr); self.KX.append(self.inTrans)
        self.KN.append(newN)
        self.born.append((newN, bar, self.curB))
        if len(self.KP) > core.MAXK:
            for a in (self.KP, self.KB, self.KH, self.KM, self.KT, self.KX, self.KN):
                a.pop(0)
        self._relabel()
        return True

    def step(self, b):
        self.curB = b
        super().step(b)
        if self.pDb == b:
            self.czWait = True
            self.deaths.append(b)

for tag, path in (('2 года', 'data/XAUUSD_1h_2y.csv'), ('9 лет', 'data/XAUUSD_1h_9y.csv')):
    rows = load(path)
    e = Anch(rows, fib=0.33, jump=0.5); e.at = pivots_n(rows, 3)
    for b in range(len(rows)):
        e.step(b)
    nums = [n for n, _, _ in e.born]
    c = collections.Counter(nums)
    tot = len(nums)
    # после каждого слома первое колено должно быть нулём
    ok = bad = 0
    for db in e.deaths:
        nxt = next(((n, cb) for n, _, cb in e.born if cb > db), None)
        if nxt is None: continue
        if nxt[0] == 0: ok += 1
        else: bad += 1
    print('══ %s · 3/3' % tag)
    print('   колен %d · без номера %d' % (tot, sum(1 for n in nums if n < 0)))
    print('   номера: ' + '  '.join('(%d) %d (%d%%)' % (k, c[k], round(c[k]/tot*100)) for k in sorted(c)))
    same = sum(1 for db in e.deaths if any(cb == db for _, _, cb in e.born))
    print('   сломов %d · первое колено ПОСЛЕ слома = (0): %d, не ноль: %d' % (len(e.deaths), ok, bad))
    print('   сломов, у которых колено родилось НА ТОМ ЖЕ баре: %d' % same)
    print()
