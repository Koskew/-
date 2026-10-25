# -*- coding: utf-8 -*-
"""П3 группы 1 · Н17 на бухгалтерии ПАЙНА. Слой 2/2, девять лет часовика.

ЧТО ЭТО. Н17 (23.09.2026) — ревизия Н14: серия сломов выживает, но вдвое
слабее, а главный признак это РАССТОЯНИЕ до ближайших непробитых
уровней. Считалась скриптом research/rasstoyanie.py, у которого СВОЯ
бухгалтерия уровней на сырых фракталах.

ПОЧЕМУ ПЕРЕСЧЁТ, ЕСЛИ ДВИЖОК НЕ ПРИ ЧЁМ. Проверено трассировкой на
девяти годах: sl_near, sl_events и sl_leg ТОЖДЕСТВЕННЫ с включёнными и
выключенными ручками zguard/knee_seq/birth_lvl. Уровни и сломы живут
НИЖЕ тренда, и З40/З41/З42 их не трогают.

Пересчёт нужен за другим: Н17 никогда не мерилась бухгалтерией
ИНДИКАТОРА. Та отличается в трёх местах (см. docstring Levels в
dvizhok2.py): ничья с предыдущим пивотом той же стороны уровня не даёт,
первый пивот каждой стороны не даёт, а пивот, родившийся и тронутый на
одном баре, уходит сразу. Разрыв в штуках 0.04% (9656 против 9660), но
числа Н17 стоят в подсказках индикатора, и они обязаны быть его.

МЕТОД — слово в слово из Н17:
  · событие = бар слома; исход = сторона СЛЕДУЮЩЕГО слома;
  · r = (ближайший непробитый сверху − close) / (close − ближайший снизу),
    на закрытии бара слома, по ЖИВЫМ уровням после вычёркивания;
  · клетки r: <0.5 · 0.5-0.8 · 0.8-1.25 · 1.25-2 · >2;
  · надбавка считается ВНУТРИ клетки r, против базы ЭТОЙ клетки;
  · длина серии 1..5, пятёрка с упором (как галочка «без предела» выкл);
  · порог: клетка r от 50 случаев, подклетка серии от 40;
  · половины обе, знак обязан держаться.

    python3 research/p3_rasstoyanie29.py
"""
import csv, os, sys, statistics as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
import dvizhok2 as D

BUCKETS = [(0.0, 0.5, 'вверх НАМНОГО ближе  r<0.5'),
           (0.5, 0.8, 'вверх ближе   0.5-0.8'),
           (0.8, 1.25, 'РАВНО         0.8-1.25'),
           (1.25, 2.0, 'вниз ближе    1.25-2.0'),
           (2.0, 1e9, 'вниз НАМНОГО ближе  r>2')]
OUT = 'research/out/p3_rasstoyanie29.csv'


def sobytiya(res, rows):
    """(бар, сторона серии, длина серии, r, сторона СЛЕДУЮЩЕГО слома).

    Серия восстанавливается из sl_events ровно как f_slomOne: смена
    стороны сбрасывает счёт в 1, та же сторона прибавляет, упор на 5.
    Внутри бара порядок событий тот же, что в пайне: сперва вверх,
    потом вниз.
    """
    ev = res['sl_events']
    near = res['sl_near']
    by_bar = {}
    for i, d, p in ev:
        by_bar.setdefault(i, []).append(d)

    run_dir, run_len = 0, 0
    pend, out = [], []
    for i in sorted(by_bar):
        for s in by_bar[i]:
            for rec in pend:
                out.append(rec + (s,))
            pend = []
            run_len = run_len + 1 if s == run_dir else 1
            if run_len > 5:
                run_len = 5
            run_dir = s
        up, dn = near[i]
        if up is not None and dn is not None:
            c = rows[i][4]
            du, dd = up - c, c - dn
            if du > 0 and dd > 0:
                pend.append((i, run_dir, run_len, du / dd))
    return out


def q(a, b):
    return '%5.1f%%' % (100.0 * a / b) if b else '  —  '


def stolbik(ev, zag, w=None, tag=''):
    svod = []
    print('=' * 100)
    print('%s   пар «слом → следующий слом»: %d' % (zag, len(ev)))
    for lo_, hi_, lab in BUCKETS:
        sel = [e for e in ev if lo_ <= e[3] < hi_]
        if len(sel) < 50:
            print('  %-26s   мало данных (n=%d)' % (lab, len(sel)))
            continue
        base_up = sum(1 for e in sel if e[4] > 0) / len(sel)
        print('  %-26s n=%5d   доля сломов ВВЕРХ в клетке: %.1f%%'
              % (lab, len(sel), 100 * base_up))
        for s, snm in ((+1, 'вверх'), (-1, 'вниз')):
            bd = base_up if s > 0 else 1 - base_up
            for k in range(1, 6):
                sub = [e for e in sel if e[1] == s and e[2] == k]
                if len(sub) < 40:
                    continue
                same = sum(1 for e in sub if e[4] == s)
                add = 100.0 * same / len(sub) - 100 * bd
                print('       серия %d подряд %-5s  n=%4d   туда же %s   база %5.1f%%   надбавка %+5.1f'
                      % (k, snm, len(sub), q(same, len(sub)), 100 * bd, add))
                if w is not None:
                    w.writerow([tag, lab, snm, k, len(sub), same,
                                '%.1f' % (100 * bd), '%.1f' % add])
                if lab.startswith('РАВНО'):
                    svod.append(add)
    print()
    return svod


rows = load('data/XAUUSD_1h_9y.csv')
N = len(rows)
half = N // 2
print('баров %d   с %s по %s   граница половин %s'
      % (N, rows[0][0][:10], rows[-1][0][:10], rows[half][0][:10]))

res = D.run_all(rows, zguard=True, knee_seq=True, birth_lvl=True, slom=True)
print('сломов всего %d, баров с расстоянием %d\n'
      % (len(res['sl_events']), sum(1 for u, d in res['sl_near']
                                    if u is not None and d is not None)))

ev = sobytiya(res, rows)

os.makedirs('research/out', exist_ok=True)
fh = open(OUT, 'w', newline='', encoding='utf-8')
w = csv.writer(fh)
w.writerow(['выборка', 'клетка отношения', 'сторона серии', 'длина серии',
            'случаев', 'следующий туда же', 'база клетки, %', 'надбавка, п.п.'])

svod = stolbik(ev, 'СЛОЙ 2/2 · девять лет · бухгалтерия ПАЙНА', w, 'вся')

print('=' * 100)
print('ГЛАВНАЯ КЛЕТКА — расстояния примерно РАВНЫ (0.8-1.25)')
if svod:
    print('  клеток %d, надбавка мед %+.1f, мин %+.1f, макс %+.1f, положительных %d/%d'
          % (len(svod), st.median(svod), min(svod), max(svod),
             sum(1 for x in svod if x > 0), len(svod)))
else:
    print('  клеток не набралось')
print()

# ── половины: знак обязан держаться ──
for nm, sel in (('ПЕРВАЯ половина', [e for e in ev if e[0] < half]),
                ('ВТОРАЯ половина', [e for e in ev if e[0] >= half])):
    s2 = stolbik(sel, nm + ' · 2/2', w, nm)
    if s2:
        print('  %s: главная клетка, мед %+.1f, положительных %d/%d'
              % (nm, st.median(s2), sum(1 for x in s2 if x > 0), len(s2)))
    print()

# ── объединённая надбавка по всей главной клетке, как в Н17 ──
print('=' * 100)
print('ОБЪЕДИНЁННАЯ надбавка по ВСЕЙ главной клетке (как в Н17, таблица половин)')
for nm, sel in (('вся выборка', ev),
                ('первая половина', [e for e in ev if e[0] < half]),
                ('вторая половина', [e for e in ev if e[0] >= half])):
    sel = [e for e in sel if 0.8 <= e[3] < 1.25]
    if len(sel) < 50:
        print('  %-18s мало данных (n=%d)' % (nm, len(sel)))
        continue
    base_up = sum(1 for e in sel if e[4] > 0) / len(sel)
    tot_n = tot_s = 0
    for s in (+1, -1):
        bd = base_up if s > 0 else 1 - base_up
        sub = [e for e in sel if e[1] == s and e[2] >= 2]
        if sub:
            same = sum(1 for e in sub if e[4] == s)
            tot_n += len(sub)
            tot_s += same - bd * len(sub)
    print('  %-18s n=%5d   надбавка серии (2 и дольше) %+5.1f п.п.'
          % (nm, tot_n, 100.0 * tot_s / tot_n if tot_n else 0))

fh.close()
print('\nпострочно: ' + OUT)
