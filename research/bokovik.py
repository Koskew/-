# -*- coding: utf-8 -*-
"""Гипотеза: «оба движка живы» = боковик. Девять лет часовика.

Движки те же, что в research/zerkalo.py: одна функция, два вызова,
нисходящий считается на ПЕРЕВЁРНУТЫХ свечах.

МЕРА — эффективность хода на куске:

    чистый ход / размах = |закрытие в конце − закрытие в начале|
                          / (максимум куска − минимум куска)

0.00 — цена вернулась туда же, откуда вышла: чистый боковик.
1.00 — прямая линия без откатов.

Одно число само по себе не читается, поэтому рядом стоят КОНТРОЛИ:
куски, где жив только восходящий; только нисходящий; ни одного; и
случайные окна той же длины из тех же данных (20 бросков на каждый
кусок, зерно фиксировано). Без случайного контроля вывод «боковик»
ничем не отличается от «так ведёт себя любой отрезок».

    python3 research/bokovik.py
"""
import csv, os, random, statistics as st
from core import load

exec(open('research/zerkalo.py').read().split('rows = load(')[0])

random.seed(20260922)
OUT = 'research/out/bokovik_9y.csv'


def eff(rows, a, b):
    """эффективность хода на куске [a, b]"""
    hi = max(r[2] for r in rows[a:b+1])
    lo = min(r[3] for r in rows[a:b+1])
    rng = hi - lo
    if rng <= 0:
        return None, 0.0
    net = abs(rows[b][4] - rows[a][4])
    return net / rng, 100.0 * net / rows[a][4]


def segments(mask):
    out, s = [], None
    for i, v in enumerate(mask):
        if v and s is None:
            s = i
        elif not v and s is not None:
            out.append((s, i - 1)); s = None
    if s is not None:
        out.append((s, len(mask) - 1))
    return out


def sl(v):
    if not v:
        return '—'
    v = sorted(v)
    g = lambda p: v[min(len(v)-1, int(p*len(v)))]
    return 'мед %.3f   25%% %.3f   75%% %.3f   доля кусков < 0.30: %.0f%%' % (
        g(.50), g(.25), g(.75), 100.0*sum(1 for x in v if x < 0.30)/len(v))


rows = load('data/XAUUSD_1h_9y.csv')
flip = [(r[0], -r[1], -r[3], -r[2], -r[4]) for r in rows]
N = len(rows)
print('баров %d   с %s по %s\n' % (N, rows[0][0][:10], rows[-1][0][:10]))

os.makedirs('research/out', exist_ok=True)
fh = open(OUT, 'w', newline='', encoding='utf-8')
w = csv.writer(fh)
w.writerow(['слой', 'состояние', 'начало', 'конец', 'баров', 'эффективность хода', 'чистый ход %'])

for d, nm in ((5, '5/5'), (3, '3/3'), (2, '2/2')):
    _, lu = run(rows, d)
    _, ld = run(flip, d)
    states = {
        'ОБА живы':        [a and b for a, b in zip(lu, ld)],
        'только восходящий': [a and not b for a, b in zip(lu, ld)],
        'только нисходящий': [b and not a for a, b in zip(lu, ld)],
        'ни одного':       [(not a) and (not b) for a, b in zip(lu, ld)],
    }
    print('=' * 82)
    print('СЛОЙ ' + nm)
    both_lens = []
    for st_name, mask in states.items():
        segs = segments(mask)
        es, ns, ls = [], [], []
        for a, b in segs:
            if b - a < 3:                      # куски короче 4 баров не меряем
                continue
            e, netp = eff(rows, a, b)
            if e is None:
                continue
            es.append(e); ns.append(netp); ls.append(b - a + 1)
            w.writerow([nm, st_name, rows[a][0][:16], rows[b][0][:16], b - a + 1,
                        '%.4f' % e, '%.3f' % netp])
        if st_name == 'ОБА живы':
            both_lens = ls
        print('  %-18s кусков %4d  медиана длины %3d баров   эффективность: %s'
              % (st_name, len(es), st.median(ls) if ls else 0, sl(es)))
    # случайный контроль: окна той же длины, что у кусков «оба живы»
    ctrl = []
    for L in both_lens:
        for _ in range(20):
            a = random.randint(0, N - L - 1)
            e, _n = eff(rows, a, a + L - 1)
            if e is not None:
                ctrl.append(e)
    print('  %-18s бросков %5d  (длины взяты у кусков «оба живы»)   эффективность: %s'
          % ('СЛУЧАЙНОЕ ОКНО', len(ctrl), sl(ctrl)))
    # разбивка «оба живы» по длине
    segs = [s for s in segments(states['ОБА живы']) if s[1] - s[0] >= 3]
    print('  «оба живы» по длине куска:')
    for lo, hi_ in ((4, 9), (10, 19), (20, 39), (40, 10**9)):
        sub = [eff(rows, a, b)[0] for a, b in segs if lo <= b - a + 1 <= hi_]
        sub = [x for x in sub if x is not None]
        cc = []
        for a, b in segs:
            L = b - a + 1
            if lo <= L <= hi_:
                for _ in range(20):
                    s0 = random.randint(0, N - L - 1)
                    e, _n = eff(rows, s0, s0 + L - 1)
                    if e is not None:
                        cc.append(e)
        if sub:
            print('     %-8s кусков %4d   медиана %.3f   случайное окно той же длины %.3f'
                  % ('%d-%d' % (lo, hi_) if hi_ < 10**8 else '40+', len(sub),
                     st.median(sub), st.median(cc) if cc else 0))
    print()
fh.close()
print('построчно: ' + OUT)


# ──────────────────────────────────────────────────────────────────────
# ПРОВЕРКА НА ТАВТОЛОГИЮ
#
# Обратная мера выше врёт по построению: кусок «оба живы» длинный ИМЕННО
# потому, что ни один уровень не пробили, а «не пробили» и «цена никуда
# не ушла» — это одно и то же. Признак описывает сам себя.
#
# Дисциплина проекта требует нормировать на первые бары и смотреть, что
# будет ПОСЛЕ. Здесь: флаг снимается по первым 20 барам куска,
# эффективность меряется на СЛЕДУЮЩИХ 20.
#
#     python3 research/bokovik.py --vpered
# ──────────────────────────────────────────────────────────────────────
import sys

if '--vpered' in sys.argv:
    H = F = 20
    print('\nПРОВЕРКА НА ТАВТОЛОГИЮ: флаг по первым %d барам, замер на следующих %d\n' % (H, F))
    for d, nm in ((5, '5/5'), (3, '3/3'), (2, '2/2')):
        _, lu = run(rows, d)
        _, ld = run(flip, d)
        print('=== %s ===' % nm)
        for label, mask in (('ОБА живы', [a and b for a, b in zip(lu, ld)]),
                            ('только восходящий', [a and not b for a, b in zip(lu, ld)]),
                            ('только нисходящий', [b and not a for a, b in zip(lu, ld)])):
            out, k, fired = [], 0, False
            for i, v in enumerate(mask):
                if v:
                    k += 1
                    if k == H and not fired:
                        fired = True
                        if i + F < N:
                            e, _ = eff(rows, i, i + F)
                            if e is not None:
                                out.append(e)
                else:
                    k, fired = 0, False
            print('  %-18s n=%4d   медиана %.3f   доля < 0.30: %.0f%%'
                  % (label, len(out), st.median(out) if out else 0,
                     100.0*sum(1 for x in out if x < 0.30)/max(len(out), 1)))
        ctrl = []
        for _ in range(4000):
            a = random.randint(0, N - F - 1)
            e, _n = eff(rows, a, a + F)
            if e is not None:
                ctrl.append(e)
        print('  %-18s n=%4d   медиана %.3f   доля < 0.30: %.0f%%\n'
              % ('СЛУЧАЙНОЕ ОКНО', len(ctrl), st.median(ctrl),
                 100.0*sum(1 for x in ctrl if x < 0.30)/len(ctrl)))
