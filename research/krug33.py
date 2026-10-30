#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ВТОРОЙ КРУГ, остаток: Н51, Н54, Н42 на движке v3.33.

ПОЧЕМУ ТАК, А НЕ КОПИЕЙ. Эти три записи считаны своими скриптами
(`n47_chestno.py`, `n27_novaya.py`, `blizhe.py`), и в каждом движок
зовётся одной строкой без `cont_touch`. Переписывать их нельзя — они
ЗАПИСЬ прежнего прогона. Копировать логику тоже нельзя: «две копии одной
механики расходятся всегда».

Поэтому ручка навешивается СНАРУЖИ: `run_all` оборачивается так, что
`cont_touch=True` подставляется, когда вызывающий о ней не сказал. Сами
файлы не меняются ни на байт.

    python3 research/krug33.py
"""

import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.chdir(ROOT)

import dvizhok2 as D

_orig = D.run_all


def _forced(rows, *a, **kw):
    kw.setdefault('cont_touch', True)
    return _orig(rows, *a, **kw)


D.run_all = _forced

SCRIPTS = (('Н51 · правило владельца про линии', 'n47_chestno.py'),
           ('Н54 · порог копает ниже предыдущего низа', 'n27_novaya.py'),
           ('Н42 · кто ближе к концу', 'blizhe.py'))

for nm, f in SCRIPTS:
    print('\n' + '=' * 78)
    print('%s   —   %s   НА ДВИЖКЕ v3.33' % (nm, f))
    print('=' * 78)
    sys.argv = [f]
    try:
        runpy.run_path(os.path.join(HERE, f), run_name='__main__')
    except SystemExit:
        pass
