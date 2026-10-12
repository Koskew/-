# -*- coding: utf-8 -*-
"""Разбор места: восходящий «возможен», а цена уже под его нулём.
XAUUSD 1H, 2-3 октября 2017. Прибор снаружи, реплика не правится."""
import sys
sys.path.insert(0,'research')
import dvizhok2 as D
from core import load

rows = load('data/XAUUSD_1h_9y.csv')
tm=[r[0][:16] for r in rows]
lo = next(i for i,t in enumerate(tm) if t >= '2017-10-02 18:00')
hi = next(i for i,t in enumerate(tm) if t >= '2017-10-03 10:00')

res = D.run_all(rows, flip=False, trace=True)
tr = res['trace'][2]          # слой 2/2, восходящий
C  = res['C'][2]
NAME = {0:'нет',1:'возможен',2:'ВОСХ',3:'не свой',4:'архив',5:'не было',6:'умер'}

print('=== СЛОЙ 2/2 · ВОСХОДЯЩИЙ · бар за баром ===')
print('%-18s %9s %9s %9s %9s | %-10s %-11s %-6s' %
      ('время UTC','откр','макс','мин','закр','состояние','уровень','строго'))
for i in range(lo, hi):
    _,o,h,l,c = rows[i]
    lvl, st, onz = tr[i]
    mark = ''
    if lvl is not None and l <= lvl:
        mark = '   ← МИН ПОД УРОВНЕМ'
    print('%-18s %9.3f %9.3f %9.3f %9.3f | %-10s %-11s %-6s%s' %
          (tm[i], o, h, l, c, NAME.get(st,st),
           '—' if lvl is None else '%.3f'%lvl,
           'да' if onz else 'нет', mark))

print()
print('=== КОЛЕНА 2/2 в этом окне ===')
for k in range(len(C.B)):
    if lo-6 <= C.B[k] < hi:
        print('  бар %d  %s  %-9.3f %-8s %s' % (C.B[k], tm[C.B[k]], C.P[k], C.L[k],
              'ВЕРШИНА' if C.H[k] else 'низ'))
