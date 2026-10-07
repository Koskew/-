# -*- coding: utf-8 -*-
"""ПЕРЕСЧЁТ ПОСЛЕ ПАЙНА v2.0 — блок, параметры которого НАСЛЕДУЮТСЯ.

Слово владельца 07.10.2026: «возьмись за реплики и пересчёт».

ЧТО ЗДЕСЬ И ЧЕГО ЗДЕСЬ НЕТ. Правило 1 проекта требует согласовать
параметры до прогона. Поэтому сюда вошло ТОЛЬКО то, где выбирать нечего:
те же вопросы, те же данные, те же определения, что в исходных Н, —
сменился один движок. Всё, где пришлось бы ЧТО-ТО ВЫБРАТЬ (например,
заново выводить порог смерти вместо проверки 0.20), сюда НЕ вошло и
выложено владельцу отдельным списком.

Движок: research/dvizhok2.py, то есть indicator/metki_prosto_v2.pine.
Эталон: доза 2 у 5/5, 1 у 3/3; донор только сосед; глубина 0.20.

    python3 research/pereschet.py > research/out/pereschet.txt
"""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
import dvizhok2 as D

PAT = ["LH·HL·HH·HL·HH", "LH·HL·HH·HL·LH", "HH·HL·HH·HL·HH", "HH·HL·HH·HL·LH",
       "HH·HL·LH·HL·HH", "LH·HL·LH·HL·HH", "HH·HL·LH·HL·LH", "LH·HL·LH·HL·LH"]
PNM = ["П1", "П5", "П6", "П12", "П16", "П20", "П25", "П29"]
SNM = ["С1", "С5", "С6", "С12", "С16", "С20", "С25", "С29"]
LAY = ('5/5', '3/3', '2/2')


def pct(a, b):
    return '—' if not b else '%.1f%%' % (100.0 * a / b)


def zero_index(C, zb):
    """Ноль всегда НИЗ — §11.1. Искать по бару И по стороне."""
    for k in range(len(C.P)):
        if C.B[k] == zb and not C.H[k]:
            return k
    return -1


def broke(rows, price, a, b, flip, below):
    """Что случилось с линией цены price на барах (a, b].
    below=True — ждём пробой ВНИЗ. 'закр' / 'тень' / 'цело'.
    Определение взято из forma.py слово в слово."""
    shad = False
    for i in range(max(a + 1, 0), min(b + 1, len(rows))):
        _, o, h, l, c = rows[i]
        if flip:
            hh, ll, cc = -l, -h, -c
        else:
            hh, ll, cc = h, l, c
        if below:
            if cc < price:
                return 'закр'
            if ll <= price:
                shad = True
        else:
            if cc > price:
                return 'закр'
            if hh >= price:
                shad = True
    return 'тень' if shad else 'цело'


def tails(res, li, rows, flip):
    """Разбор всех счётов слоя: хвост, форма, линии, исход."""
    C, T = res['C'][li], res['T'][li]
    out = []
    for ct in T.counts:
        zi = zero_index(C, ct['zb'])
        if zi < 0:
            continue
        last = min(zi + 5, len(C.P) - 1)
        tail = [C.L[k] for k in range(zi + 1, last + 1)]
        full = '·'.join(tail)
        inref = any(p.startswith(full) for p in PAT) if tail else True
        exact = full in PAT
        do5 = ct['mx'] >= 5
        # признак снимается СТРОГО ДО бара, где подтвердилось колено (3)
        i3 = zi + 3
        stop = C.C[i3] if i3 < len(C.P) else ct['end']
        z_state = broke(rows, C.P[zi], C.C[zi], stop, flip, True) if i3 < len(C.P) else None
        n2, v1 = zi + 2, zi + 1
        n2_state = broke(rows, C.P[n2], C.C[n2], stop, flip, True) if n2 < len(C.P) and i3 < len(C.P) else None
        v1_state = broke(rows, C.P[v1], C.C[v1], stop, flip, False) if v1 < len(C.P) and i3 < len(C.P) else None
        out.append({'zl': ct['zl'], 'tail': full, 'inref': inref, 'exact': exact,
                    'do5': do5, 'mx': ct['mx'], 'how': ct['how'], 'rst': ct['rst'],
                    'z': z_state, 'n2': n2_state, 'v1': v1_state, 'ntail': len(tail)})
    return out


def hdr(t):
    print()
    print('=' * 72)
    print(t)
    print('=' * 72)


def main():
    rows9 = load('data/XAUUSD_1h_9y.csv')
    rows2 = load('data/XAUUSD_1h_2y.csv')
    rows5 = load('data/XAUUSD_5m.csv')

    print('ПЕРЕСЧЁТ НА ДВИЖКЕ v2.0 (metki_prosto_v2.pine)')
    print('эталон: доза 5/5=2, 3/3=1, донор только сосед, глубина 0.20 колена')

    runs = {}
    for nm, rws in (('9y', rows9), ('2y', rows2), ('5m', rows5)):
        for flip in (False, True):
            runs[(nm, flip)] = D.run_all(rws, flip=flip)

    # ── П1 · ЦЕПОЧКИ И ВСТАВКИ (на месте Н19, Н20, Н22) ──
    hdr('П1 · ЦЕПОЧКИ И ВСТАВКИ. Что стало со слоями при эталонной дозе')
    print('%-6s %-5s %8s %8s %8s %8s' % ('данные', 'слой', 'колен', 'вставок', 'доля вст.', 'зеркало'))
    for nm, rws in (('9y', rows9), ('2y', rows2), ('5m', rows5)):
        u, d = runs[(nm, False)], runs[(nm, True)]
        for li in range(3):
            same = 'цело' if (len(u['C'][li].P) == len(d['C'][li].P) and u['ins'][li] == d['ins'][li]) else 'РАЗОШЛОСЬ'
            print('%-6s %-5s %8d %8d %8s %8s' % (nm, LAY[li], len(u['C'][li].P), u['ins'][li],
                                                 pct(u['ins'][li], len(u['C'][li].P)), same))
    print()
    print('Н22 говорила: при дозе «без ограничения» все три слоя — одна цепочка.')
    print('Теперь доза 2/1 и донор только сосед, поэтому слои обязаны РАСХОДИТЬСЯ.')

    # ── П2 · ОТКАЗ СЛОЯ по дозам (на месте Н25, Н26) ──
    hdr('П2 · ОТКАЗ СЛОЯ. Чем платим за каждую дозу, два года часовика')
    print('%-10s %-5s %8s %8s %8s %9s' % ('доза 5/5-3/3', 'слой', 'колен', 'счётов', 'отказов', 'дошли (5)'))
    for d5, d3 in ((0, 0), (1, 1), (2, 1), (2, 2)):
        r = D.run_all(rows2, flip=False, dose5=d5, dose3=d3)
        for li in range(3):
            T = r['T'][li]
            cn = collections.Counter(ct['how'] for ct in T.counts)
            do5 = sum(1 for ct in T.counts if ct['mx'] >= 5)
            print('%-10s %-5s %8d %8d %8s %9s' % ('%d / %d' % (d5, d3), LAY[li], len(r['C'][li].P),
                                                  len(T.counts), pct(cn['не свой'], len(T.counts)),
                                                  pct(do5, len(T.counts))))
        print()

    # ── П3 · ЛИНИИ НУЛЯ, НИЗА (2) И ВЕРШИНЫ (1) (на месте Н21) ──
    hdr('П3 · ПРАВИЛО ВЛАДЕЛЬЦА ПРО ШТРИХ-ПУНКТИР. Девять лет часовика')
    print('Признак снимается СТРОГО ДО бара, где подтвердилось колено (3).')
    print('Исход — дошёл ли счёт ПОТОМ до (5). Доля дошедших, в скобках выборка.')
    for key, title in (('z', 'ЛИНИЯ НУЛЯ — должна ДЕРЖАТЬСЯ'),
                       ('n2', 'ЛИНИЯ НИЗА (2) — должна ДЕРЖАТЬСЯ'),
                       ('v1', 'ЛИНИЯ ВЕРШИНЫ (1) — контроль, должна ПРОБИВАТЬСЯ')):
        print()
        print('  ' + title)
        print('  %-5s %-5s %16s %16s %16s' % ('слой', 'напр', 'цело', 'тенью', 'закр. за линию'))
        for li in range(3):
            for flip, arrow in ((False, '↑'), (True, '↓')):
                ts = tails(runs[('9y', flip)], li, rows9, flip)
                cells = []
                for state in ('цело', 'тень', 'закр'):
                    g = [t for t in ts if t[key] == state]
                    cells.append('%s (%d)' % (pct(sum(1 for t in g if t['do5']), len(g)), len(g)))
                print('  %-5s %-5s %16s %16s %16s' % (LAY[li], arrow, *cells))

    # ── П4 · СПРАВОЧНИК: внутри против «вне справ.» (на месте Н24) ──
    hdr('П4 · ФОРМА СЧЁТА. «Вне справочника» против формы из справочника')
    print('Доля дошедших до (5), девять лет часовика.')
    print('%-5s %-5s %18s %18s' % ('слой', 'напр', 'форма в справ.', 'вне справ.'))
    for li in range(3):
        for flip, arrow in ((False, '↑'), (True, '↓')):
            ts = [t for t in tails(runs[('9y', flip)], li, rows9, flip) if t['ntail'] >= 2]
            a = [t for t in ts if t['inref']]
            b = [t for t in ts if not t['inref']]
            print('%-5s %-5s %18s %18s' % (LAY[li], arrow,
                  '%s (%d)' % (pct(sum(1 for t in a if t['do5']), len(a)), len(a)),
                  '%s (%d)' % (pct(sum(1 for t in b if t['do5']), len(b)), len(b))))

    # ── П5 · ЧАСТОТЫ СПРАВОЧНИКОВ П и С (замечание З27) ──
    hdr('П5 · СПРАВОЧНИКИ П и С. Пересчёт частот — замечание З27')
    print('Считаются ПОЛНЫЕ счёты (хвост из пяти колен), девять лет часовика.')
    print('рожд = ноль LL, прод = ноль HL. В пайне это массивы PFR и SFR.')
    for flip, nmset, title in ((False, PNM, 'П — ВОСХОДЯЩИЙ'), (True, SNM, 'С — НИСХОДЯЩИЙ')):
        print()
        print('  ' + title)
        print('  %-5s %-6s %6s %6s %6s %6s %6s %6s %6s %6s' % ('слой', 'какой', *nmset))
        new = []
        for li in range(3):
            ts = [t for t in tails(runs[('9y', flip)], li, rows9, flip) if t['exact']]
            for zl, znm in (('LL', 'рожд'), ('HL', 'прод')):
                cnt = collections.Counter(t['tail'] for t in ts if t['zl'] == zl)
                row = [cnt.get(p, 0) for p in PAT]
                new.append((li, znm, row))
                print('  %-5s %-6s %6d %6d %6d %6d %6d %6d %6d %6d' % (LAY[li], znm, *row))
        print()
        print('  строкой для пайна (порядок как в PFR/SFR: рожд 5/5,3/3,2/2, потом прод):')
        order = [(0, 'рожд'), (1, 'рожд'), (2, 'рожд'), (0, 'прод'), (1, 'прод'), (2, 'прод')]
        flat = []
        for li, znm in order:
            for a, b, r in new:
                if a == li and b == znm:
                    flat.extend(r)
        print('  ' + ', '.join(str(x) for x in flat))

    # ── П6 · ЧЕМ КОНЧАЮТСЯ СЧЁТЫ — нового движка раньше не было ──
    hdr('П6 · ЧЕТЫРЕ КОНЦА. Чем кончаются счёты на новом движке')
    print('Такого разреза раньше не существовало: движок знал один конец.')
    print('%-6s %-5s %-5s %7s %8s %8s %8s %8s %9s' %
          ('данные', 'слой', 'напр', 'счётов', 'умер', 'архив', 'не было', 'не свой', 'продолж.'))
    for nm in ('9y', '2y', '5m'):
        for li in range(3):
            for flip, arrow in ((False, '↑'), (True, '↓')):
                T = runs[(nm, flip)]['T'][li]
                cn = collections.Counter(ct['how'] for ct in T.counts)
                tot = len(T.counts)
                print('%-6s %-5s %-5s %7d %8s %8s %8s %8s %9s' %
                      (nm, LAY[li], arrow, tot, pct(cn['умер'], tot), pct(cn['архив'], tot),
                       pct(cn['не было'], tot), pct(cn['не свой'], tot), pct(cn['продолжение'], tot)))
        print()


if __name__ == '__main__':
    main()
