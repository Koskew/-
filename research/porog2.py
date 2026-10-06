# -*- coding: utf-8 -*-
"""§40б · ДВЕ ДЫРЫ В ПРЕДЛОЖЕНИИ: окно N и сам порог.

Замер заказан владельцем 06.10.2026 после того, как я назвал в своём же
предложении две непроверенные вещи:

  1. N — сколько последних колен усреднять. Я написал «20» из головы.
     Это тот самый грех, за который мы осудили коэффициент 0.33;
  2. 0.15 — моё ПРОЧТЕНИЕ двух распределений Н28, а не измеренный
     оптимум.

ОТЛИЧИЕ ОТ Н28: там среднее колено бралось за ВСЮ историю — одно число
на девять лет. Здесь оно СКОЛЬЗЯЩЕЕ: у каждого сторожа своё, по N
последним коленам перед ним. Только так мерка едет вместе с рынком.

ЧТО СЧИТАЕТСЯ:

  А. чувствительность к N — порог при N = 10, 20, 50;
  Б. развёртка порога: для каждого t от 0.05 до 0.60 колена —
     сколько заходов глубже t (их мы убьём), какая доля из них
     действительно слабела (попали), и какая доля слабеющих осталась
     жить (пропустили).

ИСХОД, как в Н28: следующая ВЕРШИНА после захода пришла HH (структура
оправилась) или LH (слабеет). От глубины не зависит, тавтологии нет.

ДВИЖОК: смерть ВЫКЛЮЧЕНА, доза 2 у 5/5 и 1 у 3/3, донор только сосед.

    python3 research/porog2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
from porog import chain, counts

LAYERS = (('5/5', 5, [3], 2), ('3/3', 3, [2], 1), ('2/2', 2, [], 0))
NS = (10, 20, 50)
TS = [round(0.05 * k, 2) for k in range(1, 13)]


def collect(rows, dL, dDs, dose, flip, N):
    """Заходы ниже сторожа, глубина — в долях СКОЛЬЗЯЩЕГО среднего колена."""
    K, C = chain(rows, dL, dDs, dose, flip)
    num = counts(K)
    n = len(K.P)
    legs = [0.0] + [abs(K.P[i] - K.P[i - 1]) for i in range(1, n)]
    res = []
    for i in range(n):
        if K.H[i] or num[i] not in (0, 2, 4) or i < N + 1:
            continue
        nxt = -1
        for k in range(i + 1, n):
            if not K.H[k]:
                nxt = k
                break
        if nxt < 0 or K.L[nxt] != 'LL':
            continue
        vt = -1
        for k in range(nxt + 1, n):
            if K.H[k]:
                vt = k
                break
        if vt < 0:
            continue
        a, b = C[i], C[nxt]
        if b <= a:
            continue
        # СКОЛЬЗЯЩЕЕ среднее колено: N последних ног ПЕРЕД сторожем
        win = legs[i - N + 1:i + 1]
        avg = sum(win) / len(win)
        if avg <= 0:
            continue
        lv = K.P[i]
        deep = 0.0
        for t in range(a, min(b + 1, len(rows))):
            _, o, h, l, c = rows[t]
            low_b = -max(o, c) if flip else min(o, c)
            deep = max(deep, lv - low_b)
        res.append({'d': max(deep, 0.0) / avg, 'held': K.L[vt] == 'HH', 'avg': avg})
    return res


def main():
    rows = load('data/XAUUSD_1h_9y.csv')
    print('=' * 80)
    print('§40б · ОКНО N И ПОРОГ. Глубина по ТЕЛУ, в долях СКОЛЬЗЯЩЕГО колена')
    print('ЗОЛОТО 1H · девять лет · %d баров · смерть выключена' % len(rows))
    print('=' * 80)

    # ── А. чувствительность к N ──
    print('\nА · ЧУВСТВИТЕЛЬНОСТЬ К ОКНУ N — медианы глубины захода')
    print('  %-14s %22s | %22s' % ('', 'структура ОПРАВИЛАСЬ', 'структура СЛАБЕЕТ'))
    print('  %-14s %7s %7s %7s | %7s %7s %7s' % ('слой · напр', 'N=10', 'N=20', 'N=50', 'N=10', 'N=20', 'N=50'))
    store = {}
    for nm, dL, dDs, dose in LAYERS:
        for flip, dirn in ((False, '↑'), (True, '↓')):
            cells = []
            for N in NS:
                r = collect(rows, dL, dDs, dose, flip, N)
                store[(nm, dirn, N)] = r
                ok = sorted(x['d'] for x in r if x['held'])
                bad = sorted(x['d'] for x in r if not x['held'])
                cells.append((ok[len(ok) // 2] if ok else 0, bad[len(bad) // 2] if bad else 0))
            print('  %-14s %7.2f %7.2f %7.2f | %7.2f %7.2f %7.2f'
                  % (nm + ' ' + dirn, cells[0][0], cells[1][0], cells[2][0],
                     cells[0][1], cells[1][1], cells[2][1]))

    # ── Б. развёртка порога, N=20, все слои и направления вместе ──
    for N in NS:
        allr = [x for k, v in store.items() if k[2] == N for x in v]
        ok = sum(1 for x in allr if x['held'])
        bad = len(allr) - ok
        print('\nБ · РАЗВЁРТКА ПОРОГА при N=%d   ·   заходов %d, из них слабели %d (%.0f%%)'
              % (N, len(allr), bad, 100.0 * bad / len(allr)))
        print('  %6s %8s %10s %10s %10s' % ('порог', 'убьём', 'из них', 'убито', 'пропущено'))
        print('  %6s %8s %10s %10s %10s' % ('колен', 'шт', 'слабели', 'ЗРЯ', 'слабеющих'))
        for t in TS:
            kill = [x for x in allr if x['d'] > t]
            if not kill:
                continue
            hit = sum(1 for x in kill if not x['held'])
            miss = bad - hit
            print('  %6.2f %8d %9.0f%% %9.0f%% %9.0f%%'
                  % (t, len(kill), 100.0 * hit / len(kill),
                     100.0 * (len(kill) - hit) / len(kill), 100.0 * miss / bad))


if __name__ == '__main__':
    main()
