# -*- coding: utf-8 -*-
"""В13 · ПРЕДОХРАНИТЕЛЬ: «цена по свою сторону своего уровня».

Идея владельца 23.09.2026: у каждого тренда есть линия, которую цена не
должна переходить. Перешла — тренд не рисуем (но из таблицы НЕ убираем,
а помечаем: «цена по свою сторону: нет»).

Проверяемое условие, на закрытии каждого бара:
    восходящий ЗДОРОВ, если close > его уровень (последний HL)
    нисходящий ЗДОРОВ, если close < его уровень (последняя LH)
Строгое неравенство. Равенство — «болен» (случаев почти нет).
В зеркальных координатах это одно и то же условие: sg*close > lvl.

Что меряем:
  1  как часто ответ однозначен (здоров ровно один тренд)
  2  предсказывает ли «болен» слабость: доходит ли счёт дальше
  3  сколько рисунка правило съедает зря
  4  ход цены ВПЕРЁД после выбора — единственная нетавтологичная проверка

Движок — из research/zerkalo.py (та же функция на перевёрнутых свечах),
своей копии логики здесь нет.

    python3 research/predohranitel.py
"""
import os, csv, math
from core import load
from zerkalo import Knees, Trend, events

OUT = 'research/out/predohranitel_9y.csv'
LAYERS = ((5, '5/5'), (3, '3/3'), (2, '2/2'))
FWD = (10, 20, 40)


def trace(rows, d, flip):
    """По бару: жив ли, номер эпизода счёта, счёт, здоров ли, уровень."""
    at = events(rows, d, flip)
    K, T = Knees(), Trend()
    sg = -1.0 if flip else 1.0
    out = []
    eps = []                      # эпизоды: [born, zb, last_bar, max_cnt, first_bar_of_cnt{}]
    cur = -1
    key = None
    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        nw = False
        for bar, price, isHi in at.get(i, []):
            nw = K.push(price, bar, isHi) or nw
        fr = i in at
        T.step(i, sg * o, sg * c, K, nw, fr)
        if T.tr == 1:
            k = (T.born, T.zb)
            if k != key:
                key = k
                eps.append({'born': i, 'end': i, 'mx': T.cnt, 'first': {}})
                cur = len(eps) - 1
            e = eps[cur]
            e['end'] = i
            if T.cnt > e['mx']:
                e['mx'] = T.cnt
            e['first'].setdefault(T.cnt, i)
            zd = sg * c > T.lvl
            out.append((True, cur, T.cnt, zd, T.lvl))
        else:
            key = None
            out.append((False, -1, -1, False, None))
    return out, eps


def sig(p, n):
    """две сигмы для доли"""
    return 2.0 * math.sqrt(max(p * (1 - p), 1e-9) / max(n, 1))


def main():
    rows = load('data/XAUUSD_1h_9y.csv')
    N = len(rows)
    cl = [r[4] for r in rows]
    half = N // 2
    print('баров %d   с %s по %s' % (N, rows[0][0][:10], rows[-1][0][:10]))
    print('условие: восходящий здоров при close > своего HL, нисходящий — при close < своей LH')
    print('данные 9 лет часовика, три слоя, оба направления\n')

    # снос рынка на горизонт вперёд — база для надбавки
    drift = {}
    for f in FWD:
        v = [cl[i + f] - cl[i] for i in range(N - f)]
        drift[f] = sum(v) / len(v)
    print('снос рынка (средний ход вперёд, пункты): ' +
          '   '.join('%d баров %+.2f' % (f, drift[f]) for f in FWD))
    print()

    os.makedirs('research/out', exist_ok=True)
    fh = open(OUT, 'w', newline='', encoding='utf-8')
    w = csv.writer(fh)
    w.writerow(['слой', 'раздел', 'показатель', 'значение', 'n'])

    for d, nm in LAYERS:
        up, eu = trace(rows, d, False)
        dn, ed = trace(rows, d, True)
        print('=' * 78)
        print('СЛОЙ ' + nm)

        # ---------- 1. однозначность ----------
        st = lambda t: ('мёртв' if not t[0] else ('здоров' if t[3] else 'болен'))
        tab = {}
        for i in range(N):
            tab[(st(up[i]), st(dn[i]))] = tab.get((st(up[i]), st(dn[i])), 0) + 1
        names = ('здоров', 'болен', 'мёртв')
        print('\n  1 · КТО ЗДОРОВ (доля баров, %). строки — восходящий, столбцы — нисходящий')
        print('              ' + ''.join('%9s' % x for x in names))
        for a in names:
            print('    %-9s ' % a + ''.join('%8.1f ' % (100.0 * tab.get((a, b), 0) / N) for b in names))
        both = sum(v for (a, b), v in tab.items() if a != 'мёртв' and b != 'мёртв')
        one = sum(v for (a, b), v in tab.items()
                  if (a == 'здоров') != (b == 'здоров'))
        bb = tab.get(('здоров', 'здоров'), 0)
        nn = sum(v for (a, b), v in tab.items() if a != 'здоров' and b != 'здоров')
        print('    ответ однозначен (здоров ровно один): %.1f%%   оба здоровы: %.1f%%   ни один: %.1f%%'
              % (100.0 * one / N, 100.0 * bb / N, 100.0 * nn / N))
        # только спорные бары — где сейчас работает «авто»
        c_one = sum(v for (a, b), v in tab.items()
                    if a != 'мёртв' and b != 'мёртв' and (a == 'здоров') != (b == 'здоров'))
        c_bb = tab.get(('здоров', 'здоров'), 0)
        c_nn = sum(v for (a, b), v in tab.items()
                   if a == 'болен' and b == 'болен')
        print('    из баров, где ЖИВЫ ОБА (%.1f%% всех, n=%d):' % (100.0 * both / N, both))
        print('        ответ однозначен %.1f%%   оба здоровы %.1f%%   оба больны %.1f%%'
              % (100.0 * c_one / max(both, 1), 100.0 * c_bb / max(both, 1), 100.0 * c_nn / max(both, 1)))
        for k, v in (('однозначен', c_one), ('оба здоровы', c_bb), ('оба больны', c_nn)):
            w.writerow([nm, 'оба живы', k, '%.1f%%' % (100.0 * v / max(both, 1)), both])

        # ---------- 2. предсказывает ли «болен» слабость ----------
        print('\n  2 · ДОХОДИТ ЛИ СЧЁТ ДАЛЬШЕ. состояние в момент, когда счёт стал (k)')
        print('      сравниваем долю эпизодов, дошедших до (k+1)')
        for dirn, tr, eps in (('восходящий', up, eu), ('нисходящий', dn, ed)):
            print('    %s:' % dirn)
            for k in range(5):
                gr = {True: [0, 0], False: [0, 0]}
                gr2 = {True: [0, 0], False: [0, 0]}
                for e in eps:
                    i = e['first'].get(k)
                    if i is None:
                        continue
                    zd = tr[i][3]
                    gr[zd][1] += 1
                    gr2[zd][1] += 1
                    if e['mx'] >= k + 1:
                        gr[zd][0] += 1
                    if e['mx'] >= 5:
                        gr2[zd][0] += 1
                line = '      (%d)->(%d): ' % (k, k + 1)
                for zd, lab in ((True, 'здоров'), (False, 'болен ')):
                    g, n = gr[zd]
                    p = g / n if n else 0.0
                    line += '%s %5.1f%%±%.1f n=%-5d ' % (lab, 100.0 * p, 100.0 * sig(p, n), n)
                gh, nh = gr[True]
                gs, ns = gr[False]
                if nh >= 30 and ns >= 30:
                    dp = 100.0 * (gh / nh - gs / ns)
                    line += '  разница %+5.1f пп' % dp
                    w.writerow([nm, '2 счёт ' + dirn, '(%d)->(%d)' % (k, k + 1),
                                '%+.1f пп' % dp, '%d/%d' % (nh, ns)])
                print(line)

        # ---------- 3. цена правки ----------
        print('\n  3 · ЦЕНА ПРАВКИ — сколько рисунка предохранитель снимает')
        for dirn, tr, eps in (('восходящий', up, eu), ('нисходящий', dn, ed)):
            al = [t for t in tr if t[0]]
            sick = sum(1 for t in al if not t[3])
            big = [e for e in eps if e['mx'] >= 5]
            with_sick, shares = 0, []
            for e in big:
                s = sum(1 for i in range(e['born'], e['end'] + 1) if tr[i][0] and not tr[i][3])
                ln = e['end'] - e['born'] + 1
                if s:
                    with_sick += 1
                shares.append(s / ln)
            shares.sort()
            med = shares[len(shares) // 2] if shares else 0.0
            # длина приступов
            runs, r = [], 0
            for t in tr:
                if t[0] and not t[3]:
                    r += 1
                elif r:
                    runs.append(r); r = 0
            if r:
                runs.append(r)
            runs.sort()
            print('    %s: больных баров %.1f%% из живых (n=%d)' % (dirn, 100.0 * sick / max(len(al), 1), len(al)))
            print('        эпизодов, дошедших до (5): %d, из них хоть раз болели %d (%.0f%%), медиана доли больных баров %.0f%%'
                  % (len(big), with_sick, 100.0 * with_sick / max(len(big), 1), 100.0 * med))
            print('        приступов %d, длина в барах: мед %d  75%% %d  макс %d'
                  % (len(runs), runs[len(runs) // 2] if runs else 0,
                     runs[int(.75 * len(runs))] if runs else 0, runs[-1] if runs else 0))
            w.writerow([nm, '3 цена ' + dirn, 'больных баров', '%.1f%%' % (100.0 * sick / max(len(al), 1)), len(al)])

        # ---------- 4. ход цены вперёд ----------
        print('\n  4 · ЧТО БЫЛО ДАЛЬШЕ. бары, где живы оба и здоров ровно один.')
        print('      берём сторону здорового, считаем НАДБАВКУ к слепому входу в ту же сторону')
        for f in FWD:
            acc = {'все': [], '1-я половина': [], '2-я половина': []}
            accA = {'все': [], '1-я половина': [], '2-я половина': []}
            for i in range(N - f):
                a, b = up[i], dn[i]
                if not (a[0] and b[0]):
                    continue
                if a[3] == b[3]:
                    continue
                s = 1.0 if a[3] else -1.0
                ex = s * (cl[i + f] - cl[i]) - s * drift[f]
                alt = -s * (cl[i + f] - cl[i]) - (-s) * drift[f]
                for kk in ('все', '1-я половина' if i < half else '2-я половина'):
                    acc[kk].append(ex)
                    accA[kk].append(alt)
            for kk in ('все', '1-я половина', '2-я половина'):
                v = acc[kk]
                if not v:
                    continue
                m = sum(v) / len(v)
                sd = (sum((x - m) ** 2 for x in v) / max(len(v) - 1, 1)) ** .5
                ma = sum(accA[kk]) / len(accA[kk])
                print('      %2d баров · %-12s  здоровый %+7.2f ± %.2f   больной %+7.2f   n=%d'
                      % (f, kk, m, 2 * sd / len(v) ** .5, ma, len(v)))
                if kk == 'все':
                    w.writerow([nm, '4 вперёд', '%d баров, надбавка' % f, '%+.2f' % m, len(v)])
        print()
    fh.close()
    print('построчно: ' + OUT)
    print('\nОГОВОРКА: бары подряд не независимы, поэтому ±2σ в разделе 4 занижены.')
    print('Разделы 2 и 3 считают ЭПИЗОДЫ — там n честный.')


if __name__ == '__main__':
    main()
