#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПЕРЕСЧЁТ НА ДВИЖОК v3.29. Группа 1, пункты П1 и П7.

Заказан владельцем 25.10.2026: «все старые замеры нужно перемерять
v3.28… все замеры делаем на v3.28 пока не выйдет новая версия», затем
«начинай группу 1». План — `indicator/ПРОВЕРИТЬ.md`, блок «ПЕРЕСЧЁТ НА
ДВИЖОК v3.29».

ЧТО ЗДЕСЬ. Только то, где ВЫБИРАТЬ НЕЧЕГО: тот же вопрос, те же данные,
то же определение, сменился один движок. Образец — `pereschet.py` от
07.10.2026, и его помощники берутся ИМПОРТОМ, а не копией: `tails()`,
`zero_index()`, `broke()` остаются в одном экземпляре на проект.

   П1 · Н36 — четыре конца тренда в числах
   П7 · Н39 — тождество «вне справочника» ⟺ «была манипуляция»
        Н40 — переехать может только последнее колено

ДВИЖОК: `run_all(rows, zguard=True, knee_seq=True, birth_lvl=True)`,
слой 2/2. Старые числа считались на эталоне v2.3, до З40, З41 и З42.

ПРО Н40 ОТДЕЛЬНО. Утверждение «переехать может только последнее колено,
и только в свою сторону» в реплике верно ПО ПОСТРОЕНИЮ: `Chain.push`
трогает только `[-1]` и только при `better`. Поэтому пересчёт тут — не
проверка истинности, а ПОДСЧЁТ: сколько переездов на нынешнем движке
против 10 792 у Н40. Счётчик вешается снаружи, обёрткой вокруг метода,
сам файл реплики НЕ правится.

    python3 research/pereschet29.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dvizhok2 as D
import pereschet as P

RUN = dict(zguard=True, knee_seq=True, birth_lvl=True)
LAY = 2                      # слой 2/2 — единственный в нынешнем пайне

DATA = (('data/XAUUSD_1h_9y.csv', 'ЧАСОВИК, девять лет'),
        ('data/XAUUSD_1h_2y.csv', 'ЧАСОВИК, два года'),
        ('data/XAUUSD_5m.csv', 'ПЯТИМИНУТКА'))

# ── счётчик переездов, вешается СНАРУЖИ ──
MOVES = {'всего': 0, 'не последний': 0, 'не в свою сторону': 0}
_orig_push = D.Chain.push


def _push(self, price, bar, isHi, conf):
    before = list(self.P)
    r = _orig_push(self, price, bar, isHi, conf)
    if not r and before and len(self.P) == len(before):
        # колено переехало: цена последнего изменилась
        if self.P[-1] != before[-1]:
            MOVES['всего'] += 1
            for k in range(len(before) - 1):
                if self.P[k] != before[k]:
                    MOVES['не последний'] += 1
                    break
            lucse = self.P[-1] > before[-1] if self.H[-1] else self.P[-1] < before[-1]
            if not lucse:
                MOVES['не в свою сторону'] += 1
    return r


D.Chain.push = _push


def pct(a, b):
    return '—' if not b else '%.1f%%' % (100.0 * a / b)


def p1(rows, name):
    """Н36 · четыре конца тренда в числах, слой 2/2."""
    print('  П1 · Н36 — ЧЕМ КОНЧАЮТСЯ СЧЁТА')
    print('     %-5s %7s %9s %9s %9s %9s' % ('напр', 'счётов', 'умер', 'архив', 'не было', 'продолж.'))
    out = {}
    for flip, nm in ((False, '↑'), (True, '↓')):
        res = D.run_all(rows, flip=flip, **RUN)
        T = res['T'][LAY]
        n = len(T.counts)
        c = {}
        for ct in T.counts:
            c[ct['how']] = c.get(ct['how'], 0) + 1
        print('     %-5s %7d %9s %9s %9s %9s'
              % (nm, n, pct(c.get('умер', 0), n), pct(c.get('архив', 0), n),
                 pct(c.get('не было', 0), n), pct(c.get('продолжение', 0), n)))
        out[nm] = (n, c)
    return out


def p7(rows, name):
    """Н39 · тождество справочника. Н40 · переезд только последнего."""
    print('  П7 · Н39 — ТОЖДЕСТВО «ВНЕ СПРАВОЧНИКА» ⟺ «БЫЛА МАНИПУЛЯЦИЯ»')
    bad1 = bad2 = 0
    for flip, nm in ((False, '↑'), (True, '↓')):
        res = D.run_all(rows, flip=flip, **RUN)
        rows_t = P.tails(res, LAY, rows, flip)
        # n5 обнуляется НА КАЖДОЕ НАПРАВЛЕНИЕ. Первая версия этого не
        # делала, и число ↓ выходило суммой обоих. Поймано на первом же
        # прогоне: 2141 = 1131 + 1010
        a = b = c = d = n5 = 0
        for t in rows_t:
            if not t['do5'] or t['ntail'] < 5:
                continue
            n5 += 1
            parts = t['tail'].split('·')
            # манипуляция — низ НЕ HL на чётных местах счёта (2) и (4),
            # то есть на 2-м и 4-м элементе хвоста
            manip = (parts[1] != 'HL') or (parts[3] != 'HL')
            inref = t['exact']
            if manip and inref:
                a += 1          # манипуляция, но В справочнике — нарушение
            if (not manip) and (not inref):
                b += 1          # чисто, но ВНЕ справочника — нарушение
            c += 1 if manip else 0
            d += 1 if inref else 0
        bad1 += a
        bad2 += b
        print('     %s  счётов до (5): %d,  с манипуляцией %d,  в справочнике %d'
              % (nm, n5, c, d))
        print('        нарушений тождества: «манипуляция И в справочнике» %d, '
              '«чисто И вне справочника» %d' % (a, b))
    print('     ИТОГ: %s' % ('ТОЖДЕСТВО ДЕРЖИТСЯ, 0 исключений'
                             if bad1 == 0 and bad2 == 0 else
                             'ТОЖДЕСТВО СЛОМАНО: %d + %d' % (bad1, bad2)))


def main():
    root = os.path.dirname(HERE)
    for path, nm in DATA:
        rows = D.load(os.path.join(root, path))
        print('=' * 70)
        print('%s — %d баров   ДВИЖОК v3.29, слой 2/2' % (nm, len(rows)))
        print('=' * 70)
        p1(rows, nm)
        print()
        p7(rows, nm)
        print()
    print('=' * 70)
    print('П7 · Н40 — ПЕРЕЕЗД КОЛЕНА, счётчик по всем прогонам выше')
    print('   переездов всего:        %d' % MOVES['всего'])
    print('   переехал НЕ последний:  %d' % MOVES['не последний'])
    print('   переехал НЕ в свою сторону: %d' % MOVES['не в свою сторону'])
    print('   (у Н40 было 10 792 переезда и 0 исключений в обе проверки;')
    print('    здесь число другое, потому что считаны все цепочки всех')
    print('    прогонов этого скрипта, а не один набор)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
