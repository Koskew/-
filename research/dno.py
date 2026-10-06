# -*- coding: utf-8 -*-
"""§38 · ЕСТЬ ЛИ ДНО У ИМПУЛЬСА — проверка СУЩЕСТВОВАНИЯ проблемы.

Интуиция владельца 06.10.2026: «должен быть какой-то предел этого
импульса или правило, которое такую сильную манипуляцию будет
останавливать».

ПАТОЛОГИЯ, названная в §38:

    порог смерти = уровень − импульс × 0.33

Импульс ничем не ограничен. После сильной ноги порог уходит так глубоко,
что под ним оказываются прошлые низы, — и тренд остаётся жив, хотя цена
провалилась ниже них.

ЧТО СЧИТАЕМ. Не пользу от лекарства, а наличие болезни:

    как часто порог смерти оказывается НИЖЕ предыдущего низа счёта

Предыдущий низ — тот, что в цепочке стоит перед низом, на котором сидит
уровень. Если порог ушёл под него, буфер манипуляции накрыл целое колено
структуры.

РАЗБИВКА ПО ТОЧКАМ СЧЁТА, и почему владелец был прав.

Он просил считать только (2), (4) и, возможно, (5). Я расширил на все
точки — и первый прогон показал, что он прав, а я нет:

    на (0) и (1) уровень стоит на НУЛЕ, а ноль по определению LL, то
    есть он УЖЕ ниже предыдущего низа. Условие «порог ниже предыдущего
    низа» там выполняется само собой и не значит ничего.

Поэтому доля трендов с провалом считается ТОЛЬКО по точкам (2) и дальше.
Разбивка по барам показана по всем точкам — чтобы артефакт был виден, а
не спрятан.

ДВИЖОК: сегодняшний. Доза 2 у 5/5 и 1 у 3/3, донор только сосед,
смерть «имп × 0.33». Правила, принятые 05–06.10, НЕ входят — их в коде
нет. Оба направления считаются и показываются отдельно.

    python3 research/dno.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
from zerkalo import Knees, Trend, events, FIB

LAYERS = (('5/5', 5, [3], 2), ('3/3', 3, [2], 1), ('2/2', 2, [], 0))


def prev_low(K, lv):
    """Цена низа, стоящего в цепочке ПЕРЕД низом-уровнем.

    Trend не хранит бар уровня, поэтому колено ищется по ЦЕНЕ: уровень
    всегда ставится ровно на цену колена-низа, и ближайший с конца низ с
    такой ценой — он и есть."""
    idx = -1
    for k in range(len(K.P) - 1, -1, -1):
        if not K.H[k] and K.P[k] == lv:
            idx = k
            break
    if idx <= 0:
        return None
    for k in range(idx - 1, -1, -1):
        if not K.H[k]:
            return K.P[k]
    return None


def run(rows, dL, dDs, dose, flip):
    atL = events(rows, dL, flip)
    own = {(b, h) for lst in atL.values() for b, p, h in lst}
    ev = [(b, cf, p, h, True) for cf, lst in atL.items() for b, p, h in lst]
    seen = set(own)
    for dD in dDs:
        for cf, lst in events(rows, dD, flip).items():
            for b, p, h in lst:
                if (b, h) not in seen:
                    seen.add((b, h))
                    ev.append((b, cf, p, h, False))
    ev.sort(key=lambda e: (e[0], e[3] if flip else not e[3]))

    K, T = Knees(), Trend()
    sg = -1.0 if flip else 1.0
    used = 0
    q = 0
    bars = {}
    nTr = nBad = 0
    cur_bad = False
    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        nw = fr = False
        while q < len(ev) and ev[q][1] <= i:
            b, cf, p, hh, mine = ev[q]; q += 1
            if mine:
                used = 0
            else:
                if used >= dose:
                    continue
                if K.H and K.H[-1] == hh:
                    continue
                used += 1
            nw = K.push(p, b, hh) or nw
            fr = True
        was = T.tr
        T.step(i, sg * o, sg * c, K, nw, fr)
        if T.tr == 1 and was == 0:
            nTr += 1
            cur_bad = False
        if was == 1 and T.tr == 0:
            if cur_bad:
                nBad += 1
            cur_bad = False
        if T.tr == 1 and T.lvl is not None and T.cnt >= 0:
            pl = prev_low(K, T.lvl)
            if pl is not None:
                por = T.lvl - T.imp * FIB
                k = min(T.cnt, 5)
                st = bars.setdefault(k, [0, 0])
                st[0] += 1
                if por < pl:
                    st[1] += 1
                    # ТОЛЬКО с (2). На (0) и (1) уровень стоит на НУЛЕ, а
                    # ноль — это LL, то есть он УЖЕ ниже предыдущего низа
                    # по определению. Там условие выполняется само собой и
                    # ничего не означает. Владелец сказал «только для счёта
                    # 2 и 4» — он был прав, я зря расширил.
                    if k >= 2:
                        cur_bad = True
    if T.tr == 1 and cur_bad:
        nBad += 1
    return bars, nTr, nBad


def main():
    rows = load('data/XAUUSD_1h_9y.csv')
    print('=' * 78)
    print('§38 · КАК ЧАСТО ПОРОГ СМЕРТИ УХОДИТ НИЖЕ ПРЕДЫДУЩЕГО НИЗА')
    print('ЗОЛОТО 1H · девять лет · %d баров' % len(rows))
    print('=' * 78)
    for nm, dL, dDs, dose in LAYERS:
        for flip, dirn in ((False, 'восходящий'), (True, 'нисходящий')):
            bars, nTr, nBad = run(rows, dL, dDs, dose, flip)
            tot = sum(v[0] for v in bars.values())
            bad = sum(v[1] for v in bars.values())
            print('\n  %s · %s   трендов %d, из них с провалом %d (%.0f%%)'
                  % (nm, dirn, nTr, nBad, 100.0 * nBad / nTr if nTr else 0))
            print('    %-16s %9s %9s %8s' % ('счёт стоит на', 'баров', 'провал', 'доля'))
            for k in sorted(bars):
                t, b = bars[k]
                print('    %-16s %9d %9d %7.1f%%' % ('(%d)' % k, t, b, 100.0 * b / t if t else 0))
            print('    %-16s %9d %9d %7.1f%%' % ('ВСЕГО', tot, bad, 100.0 * bad / tot if tot else 0))


if __name__ == '__main__':
    main()
