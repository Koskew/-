# -*- coding: utf-8 -*-
"""Разбор места, названного владельцем: слой 3/3, НИСХОДЯЩИЙ,
16 октября 2017. Реплика НЕ правится — прибор навешивается снаружи."""
import sys, os
sys.path.insert(0, 'research')
import dvizhok2 as D
from core import load

rows = load('data/XAUUSD_1h_9y.csv')
tm = [r[0][:16] for r in rows]

# ── ПРИБОР: журнал всех push в цепочку, без правки движка ──
LOG = []          # (объект Knees, бар, цена, сторона, действие, старая цена, старый бар)
_orig = D.Knees.push
def spy(self, price, bar, isHi):
    n = len(self.P)
    same = bool(self.P) and self.H[-1] == isHi
    oldP = self.P[-1] if same else None
    oldB = self.B[-1] if same else None
    r = _orig(self, price, bar, isHi)
    if same:
        moved = (self.P[-1] != oldP) or (self.B[-1] != oldB)
        act = 'ПЕРЕЕЗД' if moved else 'поглощено'
    else:
        act = 'новое'
    LOG.append((id(self), bar, price, isHi, act, oldP, oldB))
    return r
D.Knees.push = spy

res = D.run_all(rows, flip=True)          # НИСХОДЯЩИЙ
D.Knees.push = _orig

K3 = res['K'][1]                           # слой 3/3
C3 = res['C'][1]
mine = [e for e in LOG if e[0] == id(K3)]

# чьи пивоты где
H3, L3 = D.pivots_by_bar(rows, 3)
H2, L2 = D.pivots_by_bar(rows, 2)

# окно вокруг 16.10.2017
lo = next(i for i,t in enumerate(tm) if t >= '2017-10-15 00:00')
hi = next(i for i,t in enumerate(tm) if t >= '2017-10-18 00:00')

print('=' * 96)
print('СЛОЙ 3/3 · НИСХОДЯЩИЙ · журнал колен, 15–17 октября 2017')
print('=' * 96)
print('%-18s %-7s %-9s %-9s %-11s %-22s' % ('время пивота','бар','цена','сторона','действие','чей это пивот'))
for sid, bar, price, isHi, act, oldP, oldB in mine:
    if not (lo <= bar < hi):
        continue
    # в перевёрнутом мире цена отрицательная
    real = -price
    own = (bar in H3) or (bar in L3)
    nb  = (bar in H2) or (bar in L2)
    whose = 'СВОЙ 3/3' if own else ('ВСТАВКА с 2/2' if nb else '?')
    # сторона в перевёрнутом мире: isHi=True это настоящий НИЗ
    side = 'низ' if isHi else 'вершина'
    extra = ''
    if act == 'ПЕРЕЕЗД':
        extra = '  ← было %.3f на баре %d (%s)' % (-oldP, oldB, tm[oldB])
    print('%-18s %-7d %-9.3f %-9s %-11s %-22s%s' % (tm[bar], bar, real, side, act, whose, extra))

print()
print('=' * 96)
print('ТРЕНДЫ СЛОЯ 3/3 НИСХОДЯЩЕГО, рождённые 15–18 октября 2017')
print('=' * 96)
T3 = res['T'][1]
for ct in T3.counts:
    b = ct.get('born')
    if b is None or not (lo - 24 <= b < hi + 24):
        continue
    e = ct.get('end')
    zb = ct.get('zb')
    print('рождён бар %d (%s) · ноль бар %s (%s) · дошёл до (%s) · кончилось: %s · конец бар %s (%s)'
          % (b, tm[b], zb, tm[zb] if zb is not None else '-', ct.get('mx'),
             ct.get('how'), e, tm[e] if e is not None else '-'))
