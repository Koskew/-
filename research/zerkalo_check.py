# -*- coding: utf-8 -*-
"""ПРОВЕРКА ЗЕРКАЛА НА НОВЫХ ПРАВИЛАХ — 07.10.2026.

Правило проекта (НАСТРОЙКИ-ПАНЕЛЬ, решение 01.10.2026):

    зеркало как УСТРОЙСТВО — один движок, ему подают перевёрнутые свечи.
                             Не ломается никогда.
    зеркало как ТОЖДЕСТВО  — нисходящий в точности равен восходящему на
                             перевёрнутых. Держится, пока значения равны.

    Отличие — это ЗНАЧЕНИЕ, а не новое условие. Вторая ветка кода
    зеркало убивает.

ЧТО ПРОВЕРЯЕТСЯ ЗДЕСЬ. Все правила, принятые 05–07.10.2026, работают по
ЦЕПОЧКЕ КОЛЕН. Значит достаточно доказать одно:

    цепочка перевёрнутого мира — это В ТОЧНОСТИ цепочка настоящего мира
    с перевёрнутыми ценами и сторонами

Если это держится, любое правило, читающее цепочку, зеркалится само, и
проверять каждое по отдельности не нужно.

ПРОВЕРЯЕМ НА НОВЫХ ПРАВИЛАХ: доза 2 у 5/5 и 1 у 3/3, донор только сосед,
чередование З22 — то есть ровно на той дозе и том доноре, которые
владелец выбрал 06.10.

ПОВОД НЕ ТЕОРЕТИЧЕСКИЙ. Замер Н20 в первой сборке разошёлся на 12 колен
из 2569 именно здесь: порядок событий внутри бара был отсортирован по
вершине ТОГО мира, а Пайн кладёт их в НАСТОЯЩЕМ порядке в обоих.

    python3 research/zerkalo_check.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
from porog import chain

LAYERS = (('5/5', 5, [3], 2), ('3/3', 3, [2], 1), ('2/2', 2, [], 0))
SWAP = {'HH': 'LL', 'LL': 'HH', 'HL': 'LH', 'LH': 'HL', '?': '?'}


def check(rows, nm, dL, dDs, dose):
    A, _ = chain(rows, dL, dDs, dose, False)
    B, _ = chain(rows, dL, dDs, dose, True)
    bad = []
    if len(A.P) != len(B.P):
        bad.append('ДЛИНА: %d против %d' % (len(A.P), len(B.P)))
        return bad, len(A.P), 0, 0
    nb = np_ = nh = nl = 0
    for i in range(len(A.P)):
        if A.B[i] != B.B[i]:
            nb += 1
        if abs(A.P[i] + B.P[i]) > 1e-9:
            np_ += 1
        if A.H[i] == B.H[i]:
            nh += 1
        if SWAP.get(A.L[i], '?') != B.L[i]:
            nl += 1
    if nb: bad.append('БАРЫ разошлись: %d' % nb)
    if np_: bad.append('ЦЕНЫ не противоположны: %d' % np_)
    if nh: bad.append('СТОРОНЫ не перевёрнуты: %d' % nh)
    if nl: bad.append('ПОДПИСИ не зеркальны: %d' % nl)
    legA = [abs(A.P[i] - A.P[i - 1]) for i in range(1, len(A.P))]
    legB = [abs(B.P[i] - B.P[i - 1]) for i in range(1, len(B.P))]
    avgA = sum(legA) / len(legA) if legA else 0
    avgB = sum(legB) / len(legB) if legB else 0
    if abs(avgA - avgB) > 1e-9:
        bad.append('СРЕДНЕЕ КОЛЕНО разошлось: %.6f против %.6f' % (avgA, avgB))
    return bad, len(A.P), avgA, avgB


def main():
    ok = True
    for path, title in (('data/XAUUSD_1h_9y.csv', 'ДЕВЯТЬ ЛЕТ'),
                        ('data/XAUUSD_1h_2y.csv', 'ДВА ГОДА'),
                        ('data/XAUUSD_5m.csv', 'ПЯТИМИНУТКА')):
        rows = load(path)
        print('\n' + '=' * 72)
        print('%s · %d баров · доза 2/1, донор только сосед' % (title, len(rows)))
        print('=' * 72)
        for nm, dL, dDs, dose in LAYERS:
            bad, n, a, b = check(rows, nm, dL, dDs, dose)
            if bad:
                ok = False
                print('  %-4s колен %5d   ✗ %s' % (nm, n, ' · '.join(bad)))
            else:
                print('  %-4s колен %5d   ✓ зеркало цело   среднее колено %.4f = %.4f'
                      % (nm, n, a, b))
    print('\n' + ('ИТОГ: ЗЕРКАЛО ЦЕЛО на всех слоях и всех данных'
                  if ok else 'ИТОГ: ЗЕРКАЛО СЛОМАНО — разобрать выше'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
