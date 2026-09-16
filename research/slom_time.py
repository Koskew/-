# -*- coding: utf-8 -*-
"""Смерть тренда: глубина против времени.

Правила владельца для восходящего (зеркально для нисходящего):

  A   тело закрытой свечи ушло за уровень на имп x 0.33 — как в движке
  B   ЧЕТЫРЕ СВЕЧИ ПОДРЯД закрылись телом ниже уровня, считая от первой
      такой свечи

«Закрылись телом ниже уровня» читается двояко, поэтому оба прочтения:
  B1  закрытие ниже уровня            close < lvl
  B2  ВСЁ тело ниже уровня            max(open, close) < lvl

Уровень — ПОСЛЕДНИЙ появившийся HL, он заменяет предыдущий безусловно.
Поэтому ratchet=False: храповик правилу владельца противоречит.

Критерии те же, что в Н6. Первым идёт число сломов: критерий «отдано»
награждает торопливость, и сравнивать по нему можно только правила с
близким числом срабатываний.

Запуск: python3 research/slom_time.py
"""
import sys, csv, statistics as st
sys.path.insert(0, 'research')
import core
from core import Core

NBARS = 4          # свечей подряд, слово владельца


def load(path):
    out = []
    for r in csv.DictReader(open(path, encoding='utf-8-sig')):
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


class Smert(Core):
    def __init__(self, rows, rule='A', body='close', **kw):
        super().__init__(rows, **kw)
        self.rule, self.body = rule, body
        self.cnt = 0            # свечей подряд за уровнем
        self.lvlSeen = None     # на каком уровне идёт счёт
        self.latA = False
        self.latB = False
        self._hiMax = None; self._loMin = None
        self._lastFrom = None
        self.given = []; self.deaths = []; self.births = []

    def _diedNow(self, b, bLo, bHi, c):
        if self.inTrans or self.lvl is None:
            return False, None
        o = self.rows[b][1]
        # A — глубина
        need = self.imp * self.fib
        okA = (self.tr == 1 and bLo < self.lvl - need) or \
              (self.tr == -1 and bHi > self.lvl + need)
        if okA and self.lastD is not None and abs(self.lvl - self.lastD) < 1e-9:
            okA = False
        # B — время: свечи подряд за уровнем
        if self.lvlSeen is None or abs(self.lvlSeen - self.lvl) > 1e-9:
            self.lvlSeen = self.lvl
            self.cnt = 0
        if self.body == 'close':
            past = c < self.lvl if self.tr == 1 else c > self.lvl
        else:
            past = max(o, c) < self.lvl if self.tr == 1 else min(o, c) > self.lvl
        self.cnt = self.cnt + 1 if past else 0
        okB = self.cnt >= NBARS
        if okB and self.lastD is not None and abs(self.lvl - self.lastD) < 1e-9:
            okB = False

        if okA: self.latA = True
        if okB: self.latB = True
        if self.rule == 'A':    died = self.latA
        elif self.rule == 'B':  died = self.latB
        elif self.rule == 'И':  died = self.latA and self.latB
        else:                   died = self.latA or self.latB
        return (True, self.lvl) if died else (False, None)

    def _onDeath(self, b, c):
        self.deaths.append((b, self.pTr))
        if self.imp > 0 and self._hiMax is not None:
            g = (self._hiMax - c) if self.pTr == 1 else (c - self._loMin)
            self.given.append(max(0.0, g) / self.imp)

    def step(self, b):
        h, l = self.rows[b][2], self.rows[b][3]
        if self.tr != 0 and not self.inTrans:
            self._hiMax = h if self._hiMax is None else max(self._hiMax, h)
            self._loMin = l if self._loMin is None else min(self._loMin, l)
        super().step(b)
        if self.trFrom != self._lastFrom:
            if self._lastFrom is not None or self.tr != 0:
                self.births.append((b, self.tr))
            self._lastFrom = self.trFrom
            self.latA = False; self.latB = False
            self.cnt = 0; self.lvlSeen = None
            self._hiMax = h; self._loMin = l


def run(rows, rule, body, N):
    e = Smert(rows, rule=rule, body=body, fib=0.33, jump=0.5, ratchet=False)
    e.at = pivots_n(rows, N)
    for b in range(len(rows)):
        e.step(b)
    fake = tot = 0; bi = 0
    for db, dd in e.deaths:
        while bi < len(e.births) and e.births[bi][0] <= db:
            bi += 1
        if bi < len(e.births):
            tot += 1
            if e.births[bi][1] == dd: fake += 1
    g = sorted(e.given)
    return dict(n=len(e.deaths),
                med=g[len(g)//2] if g else float('nan'),
                p75=g[int(len(g)*.75)] if g else float('nan'),
                mean=st.mean(g) if g else float('nan'),
                fake=(fake / tot * 100) if tot else float('nan'),
                trans=e.trBars / len(rows) * 100,
                life=st.median(e.lives) if e.lives else float('nan'))


RULES = [('A  имп x 0.33',    'A',   'close'),
         ('B1 4 закрытия',    'B',   'close'),
         ('B2 4 тела целиком', 'B',   'body'),
         ('A или B1',         'ИЛИ', 'close'),
         ('A и B1',           'И',   'close')]


def table(tag, rows, N):
    print('\n══ %s · слой %d/%d · %d баров' % (tag, N, N, len(rows)))
    print('   %-17s %6s %7s %6s %7s %7s %8s %6s' %
          ('правило', 'сломов', 'отдано', '75%', 'среднее', 'фальшь', 'ПЕРЕХОД', 'жизнь'))
    for name, rule, body in RULES:
        r = run(rows, rule, body, N)
        print('   %-17s %6d %7.2f %6.2f %7.2f %6.0f%% %7.0f%% %6.0f' %
              (name, r['n'], r['med'], r['p75'], r['mean'], r['fake'], r['trans'], r['life']))


if __name__ == '__main__':
    h1 = load('data/XAUUSD_1h_9y.csv')
    mid = len(h1) // 2
    for N in (5, 3, 2):
        table('1H 9 лет', h1, N)
    table('1H первая половина', h1[:mid], 3)
    table('1H вторая половина', h1[mid:], 3)
