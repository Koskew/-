# -*- coding: utf-8 -*-
"""ТРАССИРОВКА СЛУЧАЯ З1 — большая свеча ослепляет пивот (Н12).

Заведён 29.10.2026 при разборе З1 по правилу 8, шаг 2: проверить, что
индикатор делает НА САМОМ ДЕЛЕ, а не на глаз.

Повторяет его случай с 12 янв 2026 на НЫНЕШНЕМ коде и показывает, почему
настоящее дно коррекции не стало пивотом-низом слоя 2/2.

Результат: 16.550 пункта, дно на 10 баров раньше — ровно те числа, что он
назвал 22.09.2026. Промах по соседям ровно один: свеча за два бара до
дна держит минимум на 25.405 ниже, и это та же большая свеча, что дала
вершину.

Пивоты берутся из `dvizhok2.pivots_by_bar`, своей копии нет.
"""
import os, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(root, 'research'))
from core import load
import dvizhok2 as D

rows = load(os.path.join(root, 'data/XAUUSD_1h_2y.csv'))
H, L = D.pivots_by_bar(rows, 2)

# найти бар свечи 12 янв 02:00
idx = [i for i, r in enumerate(rows) if r[0].startswith('2026-01-12T02')][0]
print('бар свечи 12 янв 02:00 = %d   максимум %.3f  минимум %.3f'
      % (idx, rows[idx][2], rows[idx][3]))
print('она пивот-ВЕРШИНА 2/2? %s' % ('ДА' if idx in H else 'нет'))
print()
print('пивоты 2/2 в окне бар %d..%d:' % (idx - 2, idx + 20))
for i in range(idx - 2, idx + 21):
    t = rows[i][0][:16]
    m = []
    if i in H:
        m.append('ВЕРШИНА %.3f' % H[i])
    if i in L:
        m.append('НИЗ %.3f' % L[i])
    print('  %-6d %s   low %.3f   %s' % (i, t, rows[i][3], ' · '.join(m)))

# настоящее дно промежутка от свечи вершины до первого пивота-низа после неё
nxt = min([b for b in L if b > idx])
seg = range(idx + 1, nxt + 1)
dno = min(seg, key=lambda i: rows[i][3])
print()
print('первый пивот-НИЗ после вершины: бар %d, %s, цена %.3f'
      % (nxt, rows[nxt][0][:16], L[nxt]))
print('настоящее дно промежутка:       бар %d, %s, цена %.3f'
      % (dno, rows[dno][0][:16], rows[dno][3]))
print('разница: %.3f пункта, %d баров раньше'
      % (L[nxt] - rows[dno][3], nxt - dno))
print()
print('почему дно не стало пивотом — его соседи:')
for k in range(dno - 2, dno + 3):
    print('   бар %d  %s  low %.3f %s' % (k, rows[k][0][:16], rows[k][3],
          '<-- дно' if k == dno else ''))
import os, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(root, 'research'))
from core import load
import dvizhok2 as D

rows = load(os.path.join(root, 'data/XAUUSD_1h_2y.csv'))
H, L = D.pivots_by_bar(rows, 2)

# найти бар свечи 12 янв 02:00
idx = [i for i, r in enumerate(rows) if r[0].startswith('2026-01-12T02')][0]
print('бар свечи 12 янв 02:00 = %d   максимум %.3f  минимум %.3f'
      % (idx, rows[idx][2], rows[idx][3]))
print('она пивот-ВЕРШИНА 2/2? %s' % ('ДА' if idx in H else 'нет'))
print()
print('пивоты 2/2 в окне бар %d..%d:' % (idx - 2, idx + 20))
for i in range(idx - 2, idx + 21):
    t = rows[i][0][:16]
    m = []
    if i in H:
        m.append('ВЕРШИНА %.3f' % H[i])
    if i in L:
        m.append('НИЗ %.3f' % L[i])
    print('  %-6d %s   low %.3f   %s' % (i, t, rows[i][3], ' · '.join(m)))

# настоящее дно промежутка от свечи вершины до первого пивота-низа после неё
nxt = min([b for b in L if b > idx])
seg = range(idx + 1, nxt + 1)
dno = min(seg, key=lambda i: rows[i][3])
print()
print('первый пивот-НИЗ после вершины: бар %d, %s, цена %.3f'
      % (nxt, rows[nxt][0][:16], L[nxt]))
print('настоящее дно промежутка:       бар %d, %s, цена %.3f'
      % (dno, rows[dno][0][:16], rows[dno][3]))
print('разница: %.3f пункта, %d баров раньше'
      % (L[nxt] - rows[dno][3], nxt - dno))
print()
print('почему дно не стало пивотом — его соседи:')
for k in range(dno - 2, dno + 3):
    print('   бар %d  %s  low %.3f %s' % (k, rows[k][0][:16], rows[k][3],
          '<-- дно' if k == dno else ''))
