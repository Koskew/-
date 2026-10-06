# -*- coding: utf-8 -*-
"""§40 · ПОРОГ СМЕРТИ, НАЙДЕННЫЙ РЫНКОМ.

Слово владельца 06.10.2026: «я как раз и хотел замерить, насколько цена
уходила от 2, 4, 5, чтобы вывести среднюю для тренда по 5\\5, 3\\3, 2\\2».

Он отказался от буфера «импульс × 0.33» — число 0.33 никто не проверял,
а Н27 показал, что буфер провален у четырёх трендов из пяти. Вместо
подобранного коэффициента порог берётся ИЗ РЫНКА, и свой у каждого слоя.

ЧТО СЧИТАЕМ. Для каждого СТОРОЖА — низа счёта — самое глубокое
захождение цены ниже него, от подтверждения этого колена до прихода
СЛЕДУЮЩЕГО низа счёта. Отдельно по тени (low) и по телу (min открытия и
закрытия).

ИСХОД. Следующий низ пришёл HL — сторож УСТОЯЛ, структура держится.
Пришёл LL — сторож НЕ УСТОЯЛ. Граница между глубинами этих двух групп и
есть искомый порог.

СМЕРТЬ ВЫКЛЮЧЕНА, и это главное в замере. Сегодняшний движок убивает
тренд на имп × 0.33, и всё, что глубже, в данные не попадает: мы мерили
бы свой же нынешний порог и получили его обратно. Поэтому счёт ведётся
по коленам без смерти вовсе.

ПРО ТОЧКУ (5). Владелец назвал (2), (4), (5). Но (5) в восходящем счёте —
ВЕРШИНА, ниже неё сторожа нет: пока счёт стоит на (5), в силе остаётся
сторож (4). Поэтому в таблице стоят сторожа (0), (2), (4), а состояние
«счёт дошёл до (5)» входит в окно сторожа (4).

ЕДИНИЦЫ — три сразу, чтобы владелец выбрал, в чём порогу жить:
пункты · проценты от цены сторожа · доли среднего колена слоя.

ДВИЖОК: доза 2 у 5/5 и 1 у 3/3, донор только сосед. Смерть ВЫКЛЮЧЕНА.
Правила, принятые 05–06.10, не входят.

    python3 research/porog.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
from zerkalo import events, BACK
# Knees из zerkalo ОБРЕЗАЕТ цепочку до 100 колен, как Пайн. Для замера
# нужна вся история, поэтому берётся необрезанная Chain из forma.py —
# правило слияния у них одно и то же.
from forma import Chain

LAYERS = (('5/5', 5, [3], 2), ('3/3', 3, [2], 1), ('2/2', 2, [], 0))


def chain(rows, dL, dDs, dose, flip):
    """Цепочка колен с дозой. Возвращает P, B, H, L и бар подтверждения C."""
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
    K = Chain()
    used = 0
    for b, cf, p, hh, mine in ev:
        if mine:
            used = 0
        else:
            if used >= dose:
                continue
            if K.H and K.H[-1] == hh:
                continue
            used += 1
        K.push(p, b, hh, cf)
    K.relabel()
    return K, K.C


def counts(K):
    """Счёт БЕЗ СМЕРТИ. Возвращает для каждого колена его номер или -1."""
    n = len(K.P)
    num = [-1] * n
    cnt = -1
    for i in range(n):
        if cnt >= 0:
            if cnt >= 5 and not K.H[i] and K.L[i] == 'HL':
                cnt = 0                       # §5: перезапуск
            elif cnt < 5:
                cnt += 1
            num[i] = cnt
            continue
        if K.H[i] and K.L[i] == 'HH':         # рождение
            j, step, q = -1, 0, i - 1
            while q >= 0 and step < BACK:
                if not K.H[q]:
                    step += 1
                    if K.L[q] == 'LL':
                        j = q
                        break
                q -= 1
            if j >= 0 and i - j <= 5:
                cnt = i - j
                num[j] = 0
                num[i] = cnt
    return num


def q(v, p):
    if not v:
        return 0.0
    v = sorted(v)
    k = (len(v) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def collect(rows, dL, dDs, dose, flip):
    K, C = chain(rows, dL, dDs, dose, flip)
    num = counts(K)
    n = len(K.P)
    sg = -1.0 if flip else 1.0
    # среднее колено слоя
    legs = [abs(K.P[i] - K.P[i - 1]) for i in range(1, n)]
    avg = sum(legs) / len(legs) if legs else 1.0
    res = []
    for i in range(n):
        if K.H[i] or num[i] not in (0, 2, 4):
            continue
        nxt = -1
        for k in range(i + 1, n):
            if not K.H[k]:
                nxt = k
                break
        if nxt < 0:
            continue
        a, b = C[i], C[nxt]
        if b <= a:
            continue
        lv = K.P[i]
        deepW = deepB = 0.0
        for t in range(a, min(b + 1, len(rows))):
            _, o, h, l, c = rows[t]
            if flip:
                low_w, low_b = -h, -max(o, c)
            else:
                low_w, low_b = l, min(o, c)
            deepW = max(deepW, lv - low_w)
            deepB = max(deepB, lv - low_b)
        # ИСХОД. Первая сборка брала «следующий низ HL или LL» — и это
        # оказалось ТАВТОЛОГИЕЙ: если следующий низ выше сторожа, то цена
        # по определению ниже сторожа не ходила, низшая точка окна и есть
        # этот низ. Группа «устоял» давала ровно 0.00 на всех процентилях.
        #
        # Поэтому берутся ТОЛЬКО заходы (следующий низ = LL), а исход —
        # СТРУКТУРНЫЙ и от глубины не зависящий: следующая ВЕРШИНА после
        # захода пришла HH (структура оправилась) или LH (слабеет дальше).
        if K.L[nxt] != 'LL':
            continue
        vt = -1
        for k2 in range(nxt + 1, n):
            if K.H[k2]:
                vt = k2
                break
        if vt < 0:
            continue
        # ИМПУЛЬС, как его считает движок: последняя ВЫРОСШАЯ нога.
        # Колено i — низ, значит нога i-1→i падающая, а последняя
        # растущая — это i-2→i-1.
        imp = (K.P[i - 1] - K.P[i - 2]) if i >= 2 and K.P[i - 1] > K.P[i - 2] else 0.0
        res.append({'k': num[i], 'lab': K.L[i], 'held': K.L[vt] == 'HH', 'imp': imp,
                    'w': max(deepW, 0.0), 'b': max(deepB, 0.0),
                    'px': abs(lv), 'avg': avg})
    return res


def show(res, title):
    """Считаются ТОЛЬКО заходы — случаи, когда цена реально ушла ниже
    сторожа. Исход: следующая ВЕРШИНА после захода пришла HH (структура
    оправилась) или LH (слабеет дальше)."""
    print('\n  ' + title)
    print('   %-18s %6s | %-23s | %-23s' % ('', '', 'ТЕНЬ', 'ТЕЛО'))
    print('   %-18s %6s | %7s %7s %7s | %7s %7s %7s'
          % ('заход ниже сторожа', 'шт', 'медиана', '75%', '90%', 'медиана', '75%', '90%'))
    for k in (0, 2, 4):
        for held, nm in ((True, 'оправился'), (False, 'СЛАБЕЕТ')):
            sub = [r for r in res if r['k'] == k and r['held'] == held]
            if len(sub) < 30:
                continue
            w = [r['w'] for r in sub]; b = [r['b'] for r in sub]
            print('   (%d) %-14s %6d | %7.2f %7.2f %7.2f | %7.2f %7.2f %7.2f'
                  % (k, nm, len(sub), q(w, .5), q(w, .75), q(w, .9),
                     q(b, .5), q(b, .75), q(b, .9)))
    ok = [r for r in res if r['held']]
    bad = [r for r in res if not r['held']]
    if len(ok) < 30 or len(bad) < 30:
        return
    # ПРОВЕРКА НЫНЕШНЕГО БУФЕРА: во что превращается имп × 0.33, если
    # мерить его той же линейкой — в долях среднего колена слоя
    iv = [r['imp'] / r['avg'] for r in res if r['imp'] > 0]
    print('   ' + '-' * 76)
    print('   ИМПУЛЬС в коленах: медиана %.2f, 25%% %.2f, 75%% %.2f, 90%% %.2f'
          % (q(iv, .5), q(iv, .25), q(iv, .75), q(iv, .9)))
    print('   НЫНЕШНИЙ БУФЕР имп x 0.33 в коленах: медиана %.2f, 25%% %.2f, 75%% %.2f, 90%% %.2f'
          % (q(iv, .5) * .33, q(iv, .25) * .33, q(iv, .75) * .33, q(iv, .9) * .33))
    for nm, key in (('ТЕНЬ', 'w'), ('ТЕЛО', 'b')):
        f = lambda v, g: q([g(r) for r in v], .5)
        print('   %s  оправился: %6.2f пункта · %5.3f%% · %4.2f колена   |   слабеет: %6.2f · %5.3f%% · %4.2f'
              % (nm, f(ok, lambda r: r[key]), f(ok, lambda r: 100.0 * r[key] / r['px']),
                 f(ok, lambda r: r[key] / r['avg']),
                 f(bad, lambda r: r[key]), f(bad, lambda r: 100.0 * r[key] / r['px']),
                 f(bad, lambda r: r[key] / r['avg'])))


def main():
    rows = load('data/XAUUSD_1h_9y.csv')
    print('=' * 86)
    print('§40 · НАСКОЛЬКО ЦЕНА УХОДИТ НИЖЕ СТОРОЖА. СМЕРТЬ ВЫКЛЮЧЕНА')
    print('ЗОЛОТО 1H · девять лет · %d баров' % len(rows))
    print('=' * 86)
    for nm, dL, dDs, dose in LAYERS:
        for flip, dirn in ((False, 'восходящий'), (True, 'нисходящий')):
            res = collect(rows, dL, dDs, dose, flip)
            show(res, '%s · %s   сторожей %d, среднее колено %.2f'
                 % (nm, dirn, len(res), res[0]['avg'] if res else 0))


if __name__ == '__main__':
    main()
