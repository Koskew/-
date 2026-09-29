# -*- coding: utf-8 -*-
"""С3 · СЧЁТ СО ВСТАВКАМИ: что меняется и цел ли справочник.

Замеряет В16. Проверяет ДВА утверждения владельца, записанных ДО замера:

  1. «так будет больше трендов, которые закончились на счёте 5»;
  2. «последовательности, которые мы используем для определения трендов,
     либо вообще не пострадают, либо минимально».

Как строится объединённая цепочка, по решениям владельца 29.09.2026:

  · вставка — колено ДОНОРА, которого у слоя нет. 5/5 берёт только у
    3/3, 3/3 только у 2/2, запасной донор в счёт не идёт;
  · показанное не переписывается: обрезки хвоста нет;
  · два колена одной стороны подряд СЛИВАЮТСЯ по худшему экстремуму —
    это делает сама f_push, отдельного кода не нужно;
  · порядок внутри бара: сперва событие слоя (оно старше по своему
    бару), потом вставка донора.

Движок колен и движок тренда берутся из research/zerkalo.py.

    python3 research/vstavki2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
import zerkalo
from zerkalo import Knees, Trend, events, pivots_d

PAT = ["LH·HL·HH·HL·HH","LH·HL·HH·HL·LH","HH·HL·HH·HL·HH","HH·HL·HH·HL·LH",
       "HH·HL·LH·HL·HH","LH·HL·LH·HL·HH","HH·HL·LH·HL·LH","LH·HL·LH·HL·LH"]


def stream(rows, dL, dD, flip, use_ins):
    """Объединённая цепочка, собранная ПО ПОРЯДКУ САМИХ КОЛЕН.

    ИЗЪЯН, найденный 29.09.2026 в первой сборке: события клались в
    цепочку по времени ПОДТВЕРЖДЕНИЯ. У слоя лаг 5 баров, у донора 3,
    поэтому колено слоя, случившееся РАНЬШЕ, попадало в зиг-заг ПОЗЖЕ
    вставки — и ломало чередование на ровном месте. Числа первой сборки
    выброшены.

    Здесь событие ждёт своей очереди: пушится не раньше, чем подтвердится
    само, и не раньше, чем встанут все колена с меньшим баром. Так
    зиг-заг остаётся зиг-загом, а запаздывание честное.
    """
    atL, atD = events(rows, dL, flip), events(rows, dD, flip)
    own = set()
    for ev in atL.values():
        for bar, price, isHi in ev:
            own.add((bar, isHi))
    ev = []
    for conf, lst in atL.items():
        for bar, price, isHi in lst:
            ev.append((bar, conf, price, isHi))
    ins = 0
    if use_ins:
        for conf, lst in atD.items():
            for bar, price, isHi in lst:
                if (bar, isHi) not in own:
                    ev.append((bar, conf, price, isHi))
                    ins += 1
    ev.sort(key=lambda e: (e[0], not e[3]))     # по бару колена, вершина первой
    K, T = Knees(), Trend()
    sg = -1.0 if flip else 1.0
    live = []
    q = 0
    ready = 0          # ни одно событие не пушится раньше своей очереди
    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        nw = False
        fr = False
        while q < len(ev) and ev[q][1] <= i:
            bar, conf, price, isHi = ev[q]
            nw = K.push(price, bar, isHi) or nw
            fr = True
            q += 1
        T.step(i, sg * o, sg * c, K, nw, fr)
        live.append(T.tr == 1)
    if T.tr == 1:
        T.trends.append((T.born, len(rows) - 1, T.zl, T.mx, T.zp))
    return T, live, ins, K


def seq_of(T, K):
    return None


def report(nm, T, live, N, extra=''):
    tr = T.trends
    mxs = [t[3] for t in tr]
    do5 = sum(1 for m in mxs if m >= 5)
    print('  %-14s трендов %4d   до (5) дошли %4d (%.1f%%)   баров под трендом %.1f%%%s'
          % (nm, len(tr), do5, 100.0 * do5 / max(len(tr), 1), 100.0 * sum(live) / N, extra))
    print('                 докуда счёт: ' + '  '.join('(%d) %d' % (k, mxs.count(k)) for k in range(6)))
    return len(tr), do5


def forms(rows, dL, dD, flip, use_ins):
    """формы счёта: доля тех, чей хвост из 5 подписей есть в справочнике.
    Цепочка собирается той же stream, второй копии логики нет."""
    atL, atD = events(rows, dL, flip), events(rows, dD, flip)
    own = set()
    for evx in atL.values():
        for bar, price, isHi in evx:
            own.add((bar, isHi))
    ev = []
    for conf, lst in atL.items():
        for bar, price, isHi in lst:
            ev.append((bar, conf, price, isHi))
    if use_ins:
        for conf, lst in atD.items():
            for bar, price, isHi in lst:
                if (bar, isHi) not in own:
                    ev.append((bar, conf, price, isHi))
    ev.sort(key=lambda e: (e[0], not e[3]))
    K, T = Knees(), Trend()
    sg = -1.0 if flip else 1.0
    seen, tails, q = {}, [], 0
    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        nw = False
        fr = False
        while q < len(ev) and ev[q][1] <= i:
            bar, conf, price, isHi = ev[q]
            nw = K.push(price, bar, isHi) or nw
            fr = True
            q += 1
        T.step(i, sg * o, sg * c, K, nw, fr)
        if T.tr == 1 and T.cnt == 5:
            key = (T.born, T.zb)
            if key not in seen:
                seen[key] = True
                zi = -1
                for k in range(len(K.P)):
                    if K.B[k] >= T.zb and not K.H[k]:
                        zi = k
                        break
                if zi >= 0 and zi + 5 < len(K.P):
                    tails.append('·'.join(K.L[zi + 1:zi + 6]))
    ok = sum(1 for t in tails if t in PAT)
    return tails, ok


def main():
    rows = load('data/XAUUSD_1h_9y.csv')
    N = len(rows)
    print('баров %d   с %s по %s\n' % (N, rows[0][0][:10], rows[-1][0][:10]))
    for flip, dirn in ((False, 'ВОСХОДЯЩИЙ'), (True, 'НИСХОДЯЩИЙ')):
        print('=' * 78)
        print(dirn)
        for dL, dD, nm in ((5, 3, '5/5'), (3, 2, '3/3')):
            T0, l0 = zerkalo.run(rows, dL, flip)
            Tp, lp, ins, _K = stream(rows, dL, dD, flip, True)
            Td, ld = zerkalo.run(rows, dD, flip)
            print('  --- слой %s, донор %s ---' % (nm, '3/3' if dD == 3 else '2/2'))
            a, a5 = report(nm + ' чистый', T0, l0, N)
            b, b5 = report(nm + ' + вставки', Tp, lp, N, '   вставок %d' % ins)
            c, c5 = report(('3/3' if dD == 3 else '2/2') + ' чистый', Td, ld, N)
            print('                 ДО (5): %s %.1f%%  →  со вставками %.1f%%  (донор сам: %.1f%%)'
                  % (nm, 100.0*a5/max(a,1), 100.0*b5/max(b,1), 100.0*c5/max(c,1)))
            t0, o0 = forms(rows, dL, dD, flip, False)
            t1, o1 = forms(rows, dL, dD, flip, True)
            print('                 СПРАВОЧНИК: чистый %d/%d форм в справочнике (%.1f%%), со вставками %d/%d (%.1f%%)'
                  % (o0, len(t0), 100.0*o0/max(len(t0),1), o1, len(t1), 100.0*o1/max(len(t1),1)))
        print()


if __name__ == '__main__':
    main()
