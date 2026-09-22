# -*- coding: utf-8 -*-
"""Идея владельца 22.09.2026: счёт вести не по коленам, а по СЛОМАМ.

Слово «слом» в проекте носят три разные вещи. Данные должны сказать,
какая из них годится в основу счёта.

  A  ЭКСТРЕМУМ. Цена взяла ближайший непробитый пивот слоя. Механизм
     живых уровней из индикатора: пивот лежит в списке, цена коснулась —
     вычёркивается навсегда. Уровень известен ЗАРАНЕЕ.
  B  УРОВЕНЬ ТРЕНДА. Цена убила тренд: пробила HL, на котором он стоял
     (вниз), или LH нисходящего (вверх). Это нынешний красный слом.
  C  СТРУКТУРА. Рождение тренда: от LL цена перебила вершину и сделала
     HH. Это нынешний зелёный слом и его зеркало.

По каждому определению считается:
  · сколько событий за девять лет и как часто;
  · сколько сломов подряд идёт в одну сторону — это ответ на вопрос,
    докуда вообще может дойти счёт по сломам;
  · сколько баров между сломами;
  · далеко ли до следующего слома в каждую сторону прямо сейчас;
  · ГЛАВНОЕ: говорит ли направление прошлых сломов что-нибудь про
    направление следующего. Сравнение идёт не с 50%, а с СОБСТВЕННОЙ
    долей сломов вверх — на растущем золоте она заведомо больше половины,
    и без этой поправки любой вывод будет про рост, а не про сломы.

    python3 research/slomy.py
"""
import statistics as st
from core import load

exec(open('research/zerkalo.py').read().split('rows = load(')[0])


def slomy_A(rows, d):
    """Слом = цена взяла ближайший НЕПРОБИТЫЙ пивот слоя.
    Уровень появляется в списке на баре подтверждения, не раньше."""
    at = pivots_d(rows, d)
    hs, ls = [], []              # непробитые пивот-вершины и пивот-низы
    ev = []                      # (бар, направление, цена уровня)
    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        # сначала пробития по уже известным уровням
        up = [p for p in hs if h >= p]
        dn = [p for p in ls if l <= p]
        if up:
            ev.append((i, +1, min(up)))          # ближайший сверху
            hs = [p for p in hs if p not in up]
        if dn:
            ev.append((i, -1, max(dn)))
            ls = [p for p in ls if p not in dn]
        # потом появляются новые уровни этого бара
        for bar, price, isHi in at.get(i, []):
            (hs if isHi else ls).append(price)
    return ev


def dist_to_next(rows, d):
    """Насколько цена далека от ближайшего непробитого уровня сверху и снизу,
    в процентах от цены. Меряется на каждом баре."""
    at = pivots_d(rows, d)
    hs, ls = [], []
    up_d, dn_d = [], []
    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        a = [p for p in hs if p > c]
        b = [p for p in ls if p < c]
        if a:
            up_d.append(100.0 * (min(a) - c) / c)
        if b:
            dn_d.append(100.0 * (c - max(b)) / c)
        hs = [p for p in hs if h < p]
        ls = [p for p in ls if l > p]
        for bar, price, isHi in at.get(i, []):
            (hs if isHi else ls).append(price)
    return up_d, dn_d


def runs_of(ev):
    """Длины серий сломов подряд в одну сторону."""
    out, k, prev = [], 0, None
    for _, s, _p in ev:
        if s == prev:
            k += 1
        else:
            if prev is not None:
                out.append(k)
            k, prev = 1, s
    if prev is not None:
        out.append(k)
    return out


def persist(ev):
    """P(следующий слом в ту же сторону | уже k подряд в эту сторону),
    против собственной базовой доли сломов вверх."""
    base_up = sum(1 for _, s, _p in ev if s > 0) / max(len(ev), 1)
    tab = {}
    k, prev = 0, None
    for idx in range(len(ev)):
        s = ev[idx][1]
        if s == prev:
            k += 1
        else:
            k, prev = 1, s
        if idx + 1 < len(ev):
            nxt = ev[idx+1][1]
            kk = min(k, 5)
            key = (prev, kk)
            a, b = tab.get(key, (0, 0))
            tab[key] = (a + (1 if nxt == prev else 0), b + 1)
    return base_up, tab


def qq(v, f='%.2f'):
    if not v:
        return '—'
    v = sorted(v)
    g = lambda p: v[min(len(v)-1, int(p*len(v)))]
    return ('мед ' + f + '   25%% ' + f + '   75%% ' + f + '   90%% ' + f + '   макс ' + f) % (
        g(.50), g(.25), g(.75), g(.90), v[-1])


rows = load('data/XAUUSD_1h_9y.csv')
flip = [(r[0], -r[1], -r[3], -r[2], -r[4]) for r in rows]
N = len(rows)
print('баров %d   с %s по %s' % (N, rows[0][0][:10], rows[-1][0][:10]))
print('доля баров, закрывшихся выше предыдущего: %.1f%%\n'
      % (100.0*sum(1 for i in range(1, N) if rows[i][4] > rows[i-1][4])/(N-1)))

for d, nm in ((5, '5/5'), (3, '3/3'), (2, '2/2')):
    print('=' * 84)
    print('СЛОЙ ' + nm)

    Tu, _ = run(rows, d)
    Td, _ = run(flip, d)
    A = slomy_A(rows, d)
    B = sorted([(e, -1, p) for _b, e, _z, _m, p in Tu.trends] +
               [(e, +1, -p) for _b, e, _z, _m, p in Td.trends])
    C = sorted([(b, +1, p) for b, _e, _z, _m, p in Tu.trends] +
               [(b, -1, -p) for b, _e, _z, _m, p in Td.trends])

    for name, ev in (('A  экстремум', A), ('B  уровень тренда', B), ('C  структура', C)):
        r = runs_of(ev)
        gaps = [float(ev[i+1][0] - ev[i][0]) for i in range(len(ev)-1)]
        upsh = 100.0*sum(1 for _b, s, _p in ev if s > 0)/max(len(ev), 1)
        print('  %-18s событий %5d   раз в %5.1f бара   вверх %.0f%%'
              % (name, len(ev), N/max(len(ev), 1), upsh))
        print('      серия в одну сторону, сломов: ' + qq([float(x) for x in r], '%.0f')
              + '   (серий %d)' % len(r))
        print('      между сломами, баров:         ' + qq(gaps, '%.0f'))

    up_d, dn_d = dist_to_next(rows, d)
    print('  ДО СЛЕДУЮЩЕГО СЛОМА (определение A), %% от цены:')
    print('      вверх: ' + qq(up_d, '%.2f'))
    print('      вниз:  ' + qq(dn_d, '%.2f'))

    print('  ГОВОРИТ ЛИ ПРОШЛОЕ ПРО БУДУЩЕЕ (определение A):')
    base, tab = persist(A)
    print('      базовая доля сломов вверх: %.1f%%' % (100*base))
    for s, lab in ((+1, 'вверх'), (-1, 'вниз')):
        basedir = base if s > 0 else 1-base
        for k in range(1, 6):
            a, b = tab.get((s, k), (0, 0))
            if b >= 50:
                print('      после %d подряд %-5s → следующий туда же: %5.1f%%  (n=%4d, база %.1f%%, надбавка %+.1f)'
                      % (k, lab, 100.0*a/b, b, 100*basedir, 100.0*a/b - 100*basedir))
    print()


# ──────────────────────────────────────────────────────────────────────
# ПРОВЕРКИ УСТОЙЧИВОСТИ (запускались отдельно 22.09.2026, результат в Н14)
#
#   · надбавка считается от СОБСТВЕННОЙ доли сломов вверх, а не от 50%:
#     на растущем золоте без этой поправки любой вывод был бы про рост;
#   · половины выборки, граница 2022-01-05 — знак обязан сохраниться;
#   · ПЕРЕМЕШАННЫЙ контроль: направления сломов тасуются, количество
#     сохраняется. Если арифметика базы верна, надбавка обязана сесть
#     в ноль. Села: медиана −0.6 … −1.2.
# ──────────────────────────────────────────────────────────────────────
