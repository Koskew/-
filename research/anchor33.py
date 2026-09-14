# -*- coding: utf-8 -*-
"""Проверка правки: после слома счёт всегда начинается с нуля.

Берём прежний движок (core.py) и добавляем ровно то, что внесено в
metki_33.pine: якорь счёта. После смерти тренда первое появившееся
колено становится точкой (0), нумерация идёт от него.
"""
import sys, csv, statistics as st, collections
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
        self.cz = -1; self.czWait = False
        self.pZb = None; self.pZp = None; self.pZl = ''
        self.zeros = []          # бары, на которых вставал ноль
        self.deaths = []         # бары смертей

    def _recount(self):
        n = len(self.KL)
        self.KN[:] = [-1] * n
        if 0 <= self.cz < n:
            for k in range(6):
                if self.cz + k < n:
                    self.KN[self.cz + k] = k
        elif n >= 2:
            super()._recount()

    def _push(self, bar, price, isHi):
        before = len(self.KP)
        fresh = super()._push(bar, price, isHi)
        if fresh:
            if self.czWait:
                self.cz = len(self.KP) - 1
                self.czWait = False
                self.zeros.append(bar)
            if len(self.KP) == core.MAXK and before == core.MAXK:
                self.cz = self.cz - 1 if self.cz > 0 else (-1 if self.cz == 0 else self.cz)
            self._recount()
        return fresh

    def step(self, b):
        was = self.tr
        lvlBefore = self.lvl
        super().step(b)
        # смерть определяем по переходу в inTrans на этом баре
        if self.pDb == b:
            zi = -1
            for q in range(len(self.KN) - 1, -1, -1):
                if self.KN[q] == 0: zi = q; break
            if zi >= 0:
                self.pZb, self.pZp, self.pZl = self.KB[zi], self.KP[zi], self.KL[zi]
            self.czWait = True
            self.cz = -1
            self.deaths.append(b)
            self._recount()

for tag, path in (('2 года', 'data/XAUUSD_1h_2y.csv'), ('9 лет', 'data/XAUUSD_1h_9y.csv')):
    rows = load(path)
    for N in (3,):
        e = Anch(rows, fib=0.33, jump=0.5); e.at = pivots_n(rows, N)
        depth = []; cur = None
        for b in range(len(rows)):
            e.step(b)
            cn = e.KN[-1] if e.KN else -1
            if cn >= 0:
                if cur is None or cn < cur: 
                    if cur is not None: depth.append(cur)
                    cur = cn
                else: cur = max(cur, cn)
        if cur is not None: depth.append(cur)
        d = collections.Counter(depth)
        # сколько смертей получили свой ноль
        print(f'══ {tag} · {N}/{N}')
        print(f'   сломов {len(e.deaths)} · нулей поставлено {len(e.zeros)} · '
              f'разница {len(e.deaths) - len(e.zeros)}')
        print(f'   глубина счёта: ' + '  '.join(f'({k}) {d[k]} ({d[k]/max(len(depth),1):.0%})' for k in sorted(d)))
        lag = []
        zi = 0
        for db in e.deaths:
            while zi < len(e.zeros) and e.zeros[zi] < db: zi += 1
            if zi < len(e.zeros): lag.append(e.zeros[zi] - db)
        if lag:
            print(f'   ноль появляется после слома через: медиана {st.median(lag):.0f} баров, '
                  f'максимум {max(lag)}')
        print()
