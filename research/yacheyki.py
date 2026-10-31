#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СВЕРКА ЯЧЕЕК ТАБЛО: что в них написано, БЕЗ ОГЛЯДКИ НА АДРЕС.

    python3 research/yacheyki.py было.pine стало.pine

Заведена 31.10.2026 при перестройке табло под З61, когда прежние сети
оказались слепы ровно на этой правке:

* `sverka.py` считает рисующие вызовы и цепочку их `if`. Перестановку
  ячеек она видит как «пропало 24, появилось 12» и не умеет сказать,
  ТО ЖЕ ли в них написано;
* `argumenty.py` сравнивает аргументы ПО ПАРАМ, а пары ищет по подписи
  вызова. У всех `table.cell` подпись одна, поэтому после удаления
  двенадцати вызовов выравнивание сбивается и сеть насчитала 154
  «изменивших значение» — почти все выдуманные.

ЧТО ДЕЛАЕТ ЭТА. Собирает из каждого `table.cell` ТРОЙКУ — текст, цвет
текста, фон — и сравнивает два файла как МНОЖЕСТВА, забыв про колонку и
строку. Перестановка адресов для неё невидима, а подмена текста или
цвета — видна сразу.

Правка чиста, когда каждая строка в «ИСЧЕЗЛИ» и «ПОЯВИЛИСЬ» объяснима
вслух. На v3.35: исчезли 14 (двенадцать дублей подписей и две старые
«2/2»), появились 2 (общая «2/2» и подпись запаса на две глубины).
"""

import io
import re
import sys
from collections import Counter


def cells(path):
    t = io.open(path, encoding='utf-8').read()
    out = []
    for m in re.finditer(r'table\.cell\(TBL,\s*(\d+),\s*(\d+),(.*)$', t, re.M):
        rest = m.group(3)
        txt = rest.split(', text_color')[0].strip().rstrip(')')
        tc = re.search(r'text_color = ([^,)]+)', rest)
        bg = re.search(r'bgcolor = ([^,)]+)', rest)
        out.append((txt, tc.group(1).strip() if tc else '-',
                    bg.group(1).strip() if bg else '-'))
    return out


if len(sys.argv) != 3:
    print(__doc__)
    sys.exit(2)

a, b = cells(sys.argv[1]), cells(sys.argv[2])
ca, cb = Counter(a), Counter(b)
print('ячеек было %d, стало %d' % (len(a), len(b)))

ush, poy = ca - cb, cb - ca
print('\n--- ИСЧЕЗЛИ (%d) ---' % sum(ush.values()))
for k, n in ush.items():
    print('  %-2d  %s' % (n, ' · '.join(k)[:120]))
print('--- ПОЯВИЛИСЬ (%d) ---' % sum(poy.values()))
for k, n in poy.items():
    print('  %-2d  %s' % (n, ' · '.join(k)[:120]))

if not ush and not poy:
    print('\nЯЧЕЙКИ СОШЛИСЬ: тексты, цвета и фоны те же, сменились только адреса')
    sys.exit(0)
print('\nНЕ ЧИСТО: каждую строку выше объяснить вслух.')
sys.exit(1)
