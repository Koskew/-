# -*- coding: utf-8 -*-
"""П5 группы 1 · Н24 на движке v3.29. Слой 2/2.

ЧТО ЭТО. Н24 (02.10.2026) мерила правило владельца про низы — «штрих-
пунктир от низов держится, а от верхов пробивается» — через ПОДПИСЬ
низа в точке (2). HL значит низ встал выше нуля, LL значит ушёл под
ноль. Исход: дошёл ли счёт потом до (5). Старый ответ: разрыв +14…+33 пп,
двенадцать клеток из двенадцати.

ПРЕДМЕТ ДВИЖКОМ ЗАТРОНУТ, в отличие от П3. Трассировка на девяти годах:
группа «LL на (2)» у РОЖДЕНИЙ усохла вдвое (128→61 и 144→60), у
ПРОДОЛЖЕНИЙ не изменилась (169→184 и 128→124). Причина названа
правилом, а не догадкой: сторож нуля (З40) и уровень на нуле (З42) есть
только у рождения, у продолжения строгой ступени нет вовсе —
ПРАВИЛА-ПРОДОЛЖЕНИЕ.md, решение У10. Поэтому рождения и продолжения
СЧИТАЮТСЯ ОТДЕЛЬНО: мешать их больше нельзя.

ЧТО СЧИТАЕТСЯ, параметры согласованы 25.10.2026:
  · данные: девять лет часовика (как в Н24), плюс два года и
    пятиминутка — независимо;
  · слой 2/2, движок v3.29 (zguard, knee_seq, birth_lvl);
  · выборка: счёты, РЕАЛЬНО дошедшие до (2) — защита от тавтологии;
  · признак: подпись низа в точке (2), HL против LL;
  · исход: дошёл ли счёт ПОТОМ до (5);
  · порог: клетка считается от 50 случаев в меньшей группе;
  · две сигмы считаются ДЛЯ КАЖДОЙ клетки по её n, а не одним общим
    числом, как было в Н24;
  · половины девяти лет — знак обязан держаться;
  · ОТДЕЛЬНО: рождения и продолжения;
  · КОЛОНКА-ЗАГАДКА: у выживших «LL на (2)» у РОЖДЕНИЙ — касался ли
    минимум какой-нибудь свечи цены нуля между рождением и приходом
    этой точки. По правилу §6 такой тренд должен был стереться.

ПРАВИЛА A и B рождения тут НЕ МЕРЯЮТСЯ. Они отклонены в Н24, и
перепроверять отклонённое без заранее объявленного порога значит
смотреть второй раз, пока не понравится. Решение владельца 25.10.2026.

    python3 research/p5_niz2.py
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
import dvizhok2 as D
from pereschet import zero_index

SETS = (('девять лет часовика', 'data/XAUUSD_1h_9y.csv'),
        ('два года часовика', 'data/XAUUSD_1h_2y.csv'),
        ('пятиминутка', 'data/XAUUSD_5m.csv'))
MIN_N = 50


def sobral(res, rows, flip, bar_lo=None, bar_hi=None):
    """Счёты слоя 2/2, дошедшие до (2). Отдаёт список словарей."""
    C, T = res['C'][2], res['T'][2]
    out = []
    for ct in T.counts:
        zi = zero_index(C, ct['zb'])
        if zi < 0 or ct['mx'] < 2 or zi + 2 >= len(C.P):
            continue
        if bar_lo is not None and not (bar_lo <= ct['zb'] < bar_hi):
            continue
        lab = C.L[zi + 2]
        if lab not in ('HL', 'LL'):
            continue
        end = ct['end'] if ct['end'] is not None else 10 ** 9
        rec = {'lab': lab, 'do5': ct['mx'] >= 5,
               'rojd': ct['zl'] == 'LL',
               'zp': C.P[zi], 'np': C.P[zi + 2],
               'born': ct['born'], 'cb': C.C[zi + 2],
               # СВОЁ ли это колено: подтвердилось ДО конца счёта.
               # Без этой проверки в группу LL попадают колена, пришедшие
               # ПОСЛЕ смерти или отмены счёта, — а они по построению
               # никогда не доходят до (5). Круг, см. docstring
               'svoe': C.C[zi + 2] <= end}
        out.append(rec)
    return out


def sigma2(p1, n1, p2, n2):
    """Две сигмы разности двух долей, в процентных пунктах."""
    if not n1 or not n2:
        return float('nan')
    p = (p1 * n1 + p2 * n2) / (n1 + n2)
    v = p * (1 - p) * (1.0 / n1 + 1.0 / n2)
    return 200.0 * math.sqrt(v) if v > 0 else 0.0


def klet(sel, zag, shirina=True):
    """Печатает одну строку: HL против LL."""
    g = {}
    for lab in ('HL', 'LL'):
        sub = [r for r in sel if r['lab'] == lab]
        g[lab] = (sum(1 for r in sub if r['do5']), len(sub))
    (a, na), (b, nb) = g['HL'], g['LL']
    if not na or not nb:
        print('  %-34s  данных нет' % zag)
        return None
    pa, pb = a / na, b / nb
    d = 100.0 * (pa - pb)
    s2 = sigma2(pa, na, pb, nb)
    mark = '  мало' if min(na, nb) < MIN_N else ('  ✔' if abs(d) > s2 else '  в шуме')
    print('  %-34s  HL %5.1f%% (%4d)   LL %5.1f%% (%4d)   разрыв %+6.1f пп   2σ %4.1f%s'
          % (zag, 100 * pa, na, 100 * pb, nb, d, s2, mark))
    return d


print('П5 · Н24 на движке v3.29 · слой 2/2')
print('признак: подпись низа в точке (2). HL — низ выше нуля, LL — ушёл под ноль')
print('исход: дошёл ли счёт ПОТОМ до (5). Считаются только дошедшие до (2)')

itog = []
for setnm, path in SETS:
    rows = load(path)
    print('\n' + '=' * 104)
    print('%s — %d баров' % (setnm, len(rows)))
    print('=' * 104)
    store = {}
    for flip, dn in ((False, '↑'), (True, '↓')):
        res = D.run_all(rows, flip=flip, zguard=True, knee_seq=True, birth_lvl=True)
        store[dn] = (res, rows, flip)
        sel = sobral(res, rows, flip)
        print('\n %s  всего счётов, дошедших до (2): %d' % (dn, len(sel)))
        svo = [r for r in sel if r['svoe']]
        print('   из них колено (2) — СВОЁ (подтвердилось до конца счёта): %d, чужих %d'
              % (len(svo), len(sel) - len(svo)))
        print('   ── как мерила Н24, без проверки «своё ли колено» ──')
        d = klet(sel, 'ВСЕ')
        if d is not None:
            itog.append((setnm, dn, 'Н24 все', d))
        for nm, f in (('только РОЖДЕНИЯ', True), ('только ПРОДОЛЖЕНИЯ', False)):
            klet([r for r in sel if r['rojd'] == f], nm)
        print('   ── ЧЕСТНО: только СВОИ колена ──')
        d = klet(svo, 'ВСЕ')
        if d is not None:
            itog.append((setnm, dn, 'своё все', d))
        for nm, f in (('только РОЖДЕНИЯ', True), ('только ПРОДОЛЖЕНИЯ', False)):
            d2 = klet([r for r in svo if r['rojd'] == f], nm)
            if d2 is not None:
                itog.append((setnm, dn, 'своё ' + nm, d2))

    # ── половины, только девять лет ──
    if 'девять' in setnm:
        half = len(rows) // 2
        print('\n ПОЛОВИНЫ — знак обязан держаться')
        for flip, dn in ((False, '↑'), (True, '↓')):
            res, rws, fl = store[dn]
            for nm, lo, hi in (('первая', 0, half), ('вторая', half, len(rows))):
                klet([r for r in sobral(res, rws, fl, lo, hi) if r['svoe']],
                     '%s %s половина (свои)' % (dn, nm))

        # ── КОЛОНКА-ЗАГАДКА ──
        print('\n' + '=' * 104)
        print('ЗАГАДКА · выжившие «LL на (2)» у РОЖДЕНИЙ')
        print('по правилу §6 уровень на нуле рубится КАСАНИЕМ, значит такой тренд')
        print('должен был стереться. Смотрю, касался ли минимум свечи цены нуля')
        print('в окне от бара рождения до бара подтверждения точки (2)')
        print('=' * 104)
        for flip, dn in ((False, '↑'), (True, '↓')):
            res, rws, fl = store[dn]
            sel = [r for r in sobral(res, rws, fl) if r['lab'] == 'LL' and r['rojd']]
            kas = net = 0
            for r in sel:
                hit = False
                for i in range(max(r['born'], 0), min(r['cb'] + 1, len(rws))):
                    lo = -rws[i][2] if fl else rws[i][3]
                    if lo <= r['zp']:
                        hit = True
                        break
                if hit:
                    kas += 1
                else:
                    net += 1
            print('  %s  всего %4d   КАСАЛСЯ нуля %4d   не касался %4d' % (dn, len(sel), kas, net))

print('\n' + '=' * 104)
print('ИТОГ — знак разрыва по всем клеткам')
print('=' * 104)
for nm in ('Н24 все', 'своё все', 'своё только РОЖДЕНИЯ', 'своё только ПРОДОЛЖЕНИЯ'):
    v = [d for _, _, k, d in itog if k == nm]
    if v:
        print('  %-20s клеток %d, положительных %d, разброс %+.1f … %+.1f'
              % (nm, len(v), sum(1 for x in v if x > 0), min(v), max(v)))
