# -*- coding: utf-8 -*-
"""§42 · ПРАВИЛО «N ЗАКРЫТИЙ ПОДРЯД» — даёт ли оно что-то сверх глубины.

Заказано владельцем 06.10.2026 после того, как глубина была заменена на
0.20 скользящего колена: «4 закрытия давай проверим».

ДВА ПРАВИЛА УСТРОЕНЫ ПО-РАЗНОМУ:

    ГЛУБИНА   — цена ушла далеко. Время не важно
    ЗАКРЫТИЯ  — цена сидит под линией долго. Глубина не важна

Правило закрытий ловит МЕДЛЕННОЕ СПОЛЗАНИЕ, которого глубина не видит.
Вопрос — бывает ли оно и означает ли что-нибудь.

ТРИ КОЛОНКИ, и третья добавлена по требованию владельца:

    глубина              от ПОРОГА = уровень − 0.20 × колено
    закрытия от УРОВНЯ   как сейчас в индикаторе
    закрытия от ПОРОГА   с ТОЙ ЖЕ линии, что глубина — честное сравнение

Зачем третья. Закрытия считаются от уровня, а глубина от порога НИЖЕ
него. Линия закрытий ближе к цене, поэтому при сползании она сработает
первой почти всегда — не потому что правило чутче, а потому что оно
посажено выше. Третья колонка разделяет эти две вещи:

    закрытия от ПОРОГА против глубины  — добавляет ли что-то ВРЕМЯ
    от УРОВНЯ против от ПОРОГА         — сколько даёт сама посадка

ВЫБОРКА И ИСХОД — те же, что в Н28 и Н30, чтобы числа были сравнимы:
заходы ниже сторожа (следующий низ = LL), исход — следующая ВЕРШИНА
пришла HH (оправилась) или LH (слабеет).

ДВИЖОК: смерть ВЫКЛЮЧЕНА, доза 2 у 5/5 и 1 у 3/3, донор только сосед.

    python3 research/zakrytiya.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
from porog import chain, counts

LAYERS = (('5/5', 5, [3], 2), ('3/3', 3, [2], 1), ('2/2', 2, [], 0))
WIN, DEPTH = 20, 0.20
NS = (2, 3, 4, 5, 6, 8)


def collect(rows, dL, dDs, dose, flip):
    K, C = chain(rows, dL, dDs, dose, flip)
    num = counts(K)
    n = len(K.P)
    legs = [0.0] + [abs(K.P[i] - K.P[i - 1]) for i in range(1, n)]
    out = []
    for i in range(n):
        if K.H[i] or num[i] not in (0, 2, 4) or i < WIN + 1:
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
        avg = sum(legs[i - WIN + 1:i + 1]) / WIN
        if avg <= 0:
            continue
        lv = K.P[i]
        por = lv - DEPTH * avg
        deepBar = -1                 # бар, где сработала ГЛУБИНА
        runL = runP = 0
        barL = {}; barP = {}         # N -> бар срабатывания закрытий
        for t in range(a, min(b + 1, len(rows))):
            _, o, h, l, c = rows[t]
            body = -max(o, c) if flip else min(o, c)
            cl = -c if flip else c
            if deepBar < 0 and body < por:
                deepBar = t
            runL = runL + 1 if cl < lv else 0
            runP = runP + 1 if cl < por else 0
            for N in NS:
                if runL >= N and N not in barL:
                    barL[N] = t
                if runP >= N and N not in barP:
                    barP[N] = t
        out.append({'held': K.L[vt] == 'HH', 'dep': deepBar, 'L': barL, 'P': barP})
    return out


def cell(rows_, cond):
    sub = [r for r in rows_ if cond(r)]
    if not sub:
        return '—', 0
    bad = sum(1 for r in sub if not r['held'])
    return '%.0f%%' % (100.0 * bad / len(sub)), len(sub)


def main():
    rows = load('data/XAUUSD_1h_9y.csv')
    allr = []
    per = {}
    for nm, dL, dDs, dose in LAYERS:
        for flip, dirn in ((False, '↑'), (True, '↓')):
            r = collect(rows, dL, dDs, dose, flip)
            per[(nm, dirn)] = r
            allr += r
    base = 100.0 * sum(1 for r in allr if not r['held']) / len(allr)
    print('=' * 84)
    print('§42 · «N ЗАКРЫТИЙ ПОДРЯД» ПРОТИВ ГЛУБИНЫ 0.20 КОЛЕНА')
    print('ЗОЛОТО 1H · девять лет · заходов %d · базовая доля ослаблений %.0f%%' % (len(allr), base))
    print('смерть выключена · доза 2/1 · донор сосед · глубина по телу')
    print('=' * 84)

    dfire = lambda r: r['dep'] >= 0
    print('\nГЛУБИНА одна:  сработала у %d заходов, из них слабели %s'
          % (sum(1 for r in allr if dfire(r)), cell(allr, dfire)[0]))
    print('               не сработала у %d, из них слабели %s'
          % (sum(1 for r in allr if not dfire(r)), cell(allr, lambda r: not dfire(r))[0]))

    for key, nm in (('L', 'от УРОВНЯ — как сейчас'), ('P', 'от ПОРОГА — одна линия с глубиной')):
        print('\nЗАКРЫТИЯ %s' % nm)
        print('  %3s | %-26s | %-26s | %s' % ('N', 'закрытия БЕЗ глубины', 'глубина БЕЗ закрытий', 'оба'))
        print('  %3s | %8s %16s | %8s %16s | %8s %8s' % ('', 'шт', 'слабели', 'шт', 'слабели', 'шт', 'слабели'))
        for N in NS:
            f = lambda r: N in r[key]
            c1, n1 = cell(allr, lambda r: f(r) and not dfire(r))
            c2, n2 = cell(allr, lambda r: dfire(r) and not f(r))
            c3, n3 = cell(allr, lambda r: f(r) and dfire(r))
            print('  %3d | %8d %16s | %8d %16s | %8d %8s' % (N, n1, c1, n2, c2, n3, c3))

    # кто раньше, когда сработали оба
    print('\nКТО РАНЬШЕ, когда сработали оба (медиана разницы в барах, + = закрытия раньше)')
    for key, nm in (('L', 'от УРОВНЯ'), ('P', 'от ПОРОГА')):
        line = []
        for N in NS:
            d = sorted(r['dep'] - r[key][N] for r in allr if dfire(r) and N in r[key])
            line.append('%+.0f' % (d[len(d) // 2] if d else 0))
        print('  %-12s ' % nm + '   '.join('N=%d %s' % (N, v) for N, v in zip(NS, line)))


if __name__ == '__main__':
    main()
