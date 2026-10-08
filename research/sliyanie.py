# -*- coding: utf-8 -*-
"""Правильная сторона вопроса: сколько колен МЛАДШЕГО слоя повторил
СТАРШИЙ. 100% значит «старший слой — это и есть младший», то есть
слои слились. Глазом это видно как метки друг на друге."""
import sys, os
sys.path.insert(0, 'research')
from dvizhok2 import run_all
from core import load

def keys(ch):
    return set(zip(ch.B, ch.H))

for path, title in (('data/XAUUSD_1h_2y.csv', 'ЧАСОВИК 2 года'),
                    ('data/XAUUSD_1h_9y.csv', 'ЧАСОВИК 9 лет'),
                    ('data/XAUUSD_5m.csv', 'ПЯТИМИНУТКА 3.5 мес')):
    if not os.path.exists(path):
        continue
    rows = load(path)
    print('=' * 76)
    print('%s — %d баров' % (title, len(rows)))
    print('=' * 76)
    print('  %-9s %6s %6s %6s | %-16s %-16s' %
          ('доза 5/3', 'к.5/5', 'к.3/3', 'к.2/2',
           '3/3 повторил 2/2', '5/5 повторил 3/3'))
    for d5, d3 in ((0, 0), (1, 1), (2, 1), (2, 2), (3, 3)):
        res = run_all(rows, flip=False, dose5=d5, dose3=d3)
        c5, c3, c2 = (keys(res['C'][i]) for i in range(3))
        a = len(c2 & c3) / len(c2) * 100
        b = len(c3 & c5) / len(c3) * 100
        print('  %-9s %6d %6d %6d | %13.1f%%    %13.1f%%' %
              ('%d / %d' % (d5, d3), len(c5), len(c3), len(c2), a, b))
    print()
