#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ВТОРОЙ КРУГ ПЕРЕСЧЁТА — НА ДВИЖОК v3.33.

Заказан владельцем 30.10.2026: «давай пересчёт старых Н на нынешний
движок». Параметры согласованы, спорный пункт закрыт его словом
«да, считай врозь».

ПОЧЕМУ НУЖЕН ВТОРОЙ КРУГ. Первый круг (`pereschet29.py` и соседи) считан
на движок v3.29 и дал Н44…Н55. Но v3.33 ТРОНУЛ ДВИЖОК — замечание З50,
ноль ПРОДОЛЖЕНИЯ рубится касанием с исходом «умер». Проверено
механически: ни один скрипт первого круга ручку `cont_touch` не
передаёт, то есть все двенадцать записей считаны БЕЗ неё.

ЧТО СЧИТАЕТ ЭТОТ ФАЙЛ. Только то, где выбирать нечего: тот же вопрос,
те же данные, то же определение, добавлена одна ручка. Старое и новое
число стоят рядом.

   Ш1 · Н44 — четыре конца тренда, было и стало
   Ш2 · РАЗДЕЛЕНИЕ СМЕРТЕЙ — по телу, по тени, и то и другое сразу

ПРО «ВРОЗЬ». До v3.33 смерть была одна и приходила по ТЕЛУ. Теперь их
два вида, и складывать их в одно число нельзя — это две разные вещи.
Бар при этом умеет удовлетворить ОБА условия сразу, поэтому считается
три столбца, а не два.

ДВИЖОК: `run_all(rows, zguard=True, knee_seq=True, birth_lvl=True,
cont_touch=…)`, слой 2/2.

    python3 research/pereschet33.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dvizhok2 as D
from core import load

ROOT = os.path.dirname(HERE)
BASE = dict(zguard=True, knee_seq=True, birth_lvl=True)
LAY = 2

DATA = (('data/XAUUSD_1h_9y.csv', 'ЧАСОВИК, девять лет'),
        ('data/XAUUSD_1h_2y.csv', 'ЧАСОВИК, два года'),
        ('data/XAUUSD_5m.csv',    'ПЯТИМИНУТКА'))

KONCY = ('умер', 'архив', 'не было', 'продолжение')


def pct(a, n):
    return '%d (%.1f%%)' % (a, 100.0 * a / n) if n else '—'


def prognat(rows, flip, ct):
    res = D.run_all(rows, flip=flip, cont_touch=ct, **BASE)
    return res['T'][LAY].counts


def konce(counts):
    c = dict.fromkeys(KONCY, 0)
    for ct in counts:
        c[ct['how']] = c.get(ct['how'], 0) + 1
    return c


print('=' * 78)
print('ВТОРОЙ КРУГ ПЕРЕСЧЁТА · ДВИЖОК v3.33 · слой 2/2')
print('его слово: «да, считай врозь»')
print('=' * 78)

for path, nm in DATA:
    rows = load(os.path.join(ROOT, path))
    print('\n' + '─' * 78)
    print('%s — %d баров' % (nm, len(rows)))
    print('─' * 78)

    for flip, dn in ((False, 'ВОСХОДЯЩИЙ'), (True, 'НИСХОДЯЩИЙ')):
        old = prognat(rows, flip, False)
        new = prognat(rows, flip, True)
        co, cn = konce(old), konce(new)

        print('\n  %s' % dn)
        print('    Ш1 · ЧЕТЫРЕ КОНЦА')
        print('      %-12s %22s %22s' % ('', 'БЫЛО (v3.29)', 'СТАЛО (v3.33)'))
        print('      %-12s %22s %22s' % ('счётов', len(old), len(new)))
        for k in KONCY:
            print('      %-12s %22s %22s'
                  % (k, pct(co[k], len(old)), pct(cn[k], len(new))))

        # ── Ш2 · раздельный счёт смертей ──
        telo = ten = oba = 0
        for ct in new:
            if ct['how'] != 'умер':
                continue
            c_ = ct.get('cdie', False)
            b_ = ct.get('bdie', False)
            if c_ and b_:
                oba += 1
            elif c_:
                ten += 1
            else:
                telo += 1
        vsego = telo + ten + oba
        print('    Ш2 · СМЕРТИ ВРОЗЬ, на v3.33')
        print('      всего «умер»        %d' % vsego)
        print('      по ТЕЛУ, глубиной   %s' % pct(telo, vsego))
        print('      по ТЕНИ, касание 0  %s' % pct(ten, vsego))
        print('      оба условия сразу   %s' % pct(oba, vsego))
        print('      прибавка смертей от правила: %+d' % (cn['умер'] - co['умер']))

print('\n' + '=' * 78)
print('«оба условия сразу» — бар, где тело ушло за порог И цена тронула')
print('ноль продолжения. Такая смерть случилась бы и без правила З50,')
print('поэтому в прибавку она не входит.')
