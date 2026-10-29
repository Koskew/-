# -*- coding: utf-8 -*-
"""ТРАССИРОВКА СЛУЧАЯ З3 — «восходящий пропал с экрана».

Заведён 29.10.2026 при разборе З3 по правилу 8, шаг 2.

Повторяет его случай 6 янв 2026 06:00 на НЫНЕШНЕМ движке и считает, на
скольких барах у обоих направлений есть счёт — то есть когда режим по
умолчанию «оба, пока у обоих есть счёт» рисует обе разметки.

Находка: его пример на нынешнем движке читается ИНАЧЕ, чем 23.09.2026.
Тогда были «восходящий жив (5)/5» и «нисходящий жив (1)/5», и восходящий
уходил с экрана. Сейчас восходящий в архиве, а нисходящий там вообще НЕ
РОЖДАЕТСЯ — подменять восходящего нечем. Движок с тех пор пережил З40,
З41, З42, З50, смену дозы и смену правила смерти.
"""
import os, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(root, 'research'))

from core import load
import dvizhok2 as D

rows = load(os.path.join(root, 'data/XAUUSD_1h_2y.csv'))
idx = [i for i, r in enumerate(rows) if r[0].startswith('2026-01-06T06')][0]

# «есть счёт» в пайне — это hasU / hasD: состояние MAY, LIVE или ARC
HAS = {D.ST_MAY, D.ST_LIVE, D.ST_ARC}

res = {}
for flip, nm in ((False, 'ВОСХОДЯЩИЙ'), (True, 'НИСХОДЯЩИЙ')):
    r = D.run_all(rows, flip=flip, zguard=True, knee_seq=True,
                  birth_lvl=True, cont_touch=True, trace=True)
    res[nm] = r['trace'][2]           # слой 2/2

print('ЕГО СЛУЧАЙ: бар %d   %s   закрытие %.3f\n'
      % (idx, rows[idx][0][:16], rows[idx][4]))
for nm in ('ВОСХОДЯЩИЙ', 'НИСХОДЯЩИЙ'):
    lvl, st, onz = res[nm][idx]
    print('   %-12s состояние «%s»   есть счёт: %s'
          % (nm, D.ST_NAME.get(st, st), 'ДА' if st in HAS else 'нет'))

both = sum(1 for i in range(len(rows))
           if res['ВОСХОДЯЩИЙ'][i][1] in HAS and res['НИСХОДЯЩИЙ'][i][1] in HAS)
one = sum(1 for i in range(len(rows))
          if (res['ВОСХОДЯЩИЙ'][i][1] in HAS) != (res['НИСХОДЯЩИЙ'][i][1] in HAS))
print('\nЗА ДВА ГОДА, %d баров:' % len(rows))
print('   у ОБОИХ есть счёт — %d баров (%.1f%%). Режим по умолчанию рисует ОБЕ разметки'
      % (both, 100.0 * both / len(rows)))
print('   счёт у ОДНОГО     — %d баров (%.1f%%). Рисуется он один, и спорить не с кем'
      % (one, 100.0 * one / len(rows)))
