# -*- coding: utf-8 -*-
"""В12: не объясняется ли Н14 просто РАССТОЯНИЕМ до ближайших уровней?

Н14 сказала: после k сломов подряд в одну сторону следующий идёт туда же
чаще собственной базовой доли на 7-20 процентных пунктов. Но я не
проверил очевидный конфаунд: после серии в одну сторону ближайший
непробитый уровень в ту же сторону может просто оказываться БЛИЖЕ, и
тогда я мерил географию, а не структуру.

Пример владельца, 2 янв 2026, слой 2/2: цена 4375.125, верхний слом в
7.0 пункта, нижний в 70.5. Куда пойдёт следующий слом — тут решает не
история.

МЕТОД. Сразу после каждого слома, по закрытию его бара, меряем:
  · длину серии k и её сторону;
  · расстояние до ближайшего непробитого уровня СВЕРХУ и СНИЗУ;
  · отношение r = (верх - close) / (close - низ).
Исход — сторона СЛЕДУЮЩЕГО слома.

Дальше разбиваем по клеткам r и ВНУТРИ каждой клетки считаем надбавку
от серии к собственной базе этой клетки. Клетка r = 0.8…1.25 — главная:
там расстояния примерно равны, география не мешает, и видно, что даёт
сама серия.

Слом и уровни считаются ровно как в research/slomy.py: сравнения пивота
из core.py, слом по КАСАНИЮ, уровень вычёркивается навсегда.

    python3 research/rasstoyanie.py
"""
import csv, os, statistics as st
from core import load

BUCKETS = [(0.0, 0.5, 'вверх НАМНОГО ближе  r<0.5'),
           (0.5, 0.8, 'вверх ближе   0.5-0.8'),
           (0.8, 1.25, 'РАВНО         0.8-1.25'),
           (1.25, 2.0, 'вниз ближе    1.25-2.0'),
           (2.0, 1e9, 'вниз НАМНОГО ближе  r>2')]
OUT = 'research/out/rasstoyanie_9y.csv'


def pivots_d(rows, d):
    hi = [r[2] for r in rows]
    lo = [r[3] for r in rows]
    at = {}
    for i in range(d, len(rows) - d):
        if all(hi[i-k] <= hi[i] for k in range(1, d+1)) and all(hi[i+k] < hi[i] for k in range(1, d+1)):
            at.setdefault(i + d, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, d+1)) and all(lo[i+k] > lo[i] for k in range(1, d+1)):
            at.setdefault(i + d, []).append((i, lo[i], False))
    return at


def sobytiya(rows, d):
    """(бар, сторона серии, длина серии, отношение расстояний, сторона СЛЕДУЮЩЕГО слома)"""
    at = pivots_d(rows, d)
    hs, ls = [], []
    run_dir, run_len = 0, 0
    pend = []          # ждут исхода
    out = []
    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        brk = []
        up = [p for p in hs if h >= p]
        dn = [p for p in ls if l <= p]
        if up:
            brk.append(+1)
            hs = [p for p in hs if p not in up]
        if dn:
            brk.append(-1)
            ls = [p for p in ls if p not in dn]
        for s in brk:
            # исход для всех, кто ждал
            for rec in pend:
                out.append(rec + (s,))
            pend = []
            run_len = run_len + 1 if s == run_dir else 1
            run_dir = s
        for bar, price, isHi in at.get(i, []):
            (hs if isHi else ls).append(price)
        if brk:
            a = [p for p in hs if p > c]
            b = [p for p in ls if p < c]
            if a and b:
                du = min(a) - c
                dd = c - max(b)
                if du > 0 and dd > 0:
                    pend.append((i, run_dir, run_len, du / dd))
    return out


def q(a, b):
    return '%5.1f%%' % (100.0 * a / b) if b else '  —  '


rows = load('data/XAUUSD_1h_9y.csv')
N = len(rows)
half = N // 2
print('баров %d   с %s по %s   граница половин %s\n'
      % (N, rows[0][0][:10], rows[-1][0][:10], rows[half][0][:10]))

os.makedirs('research/out', exist_ok=True)
fh = open(OUT, 'w', newline='', encoding='utf-8')
w = csv.writer(fh)
w.writerow(['слой', 'клетка отношения', 'сторона серии', 'длина серии',
            'случаев', 'следующий туда же', 'база клетки, %', 'надбавка, п.п.'])

svod = {}
for d, nm in ((5, '5/5'), (3, '3/3'), (2, '2/2')):
    ev = sobytiya(rows, d)
    print('=' * 100)
    print('СЛОЙ %s   всего пар «слом -> следующий слом»: %d' % (nm, len(ev)))
    for lo_, hi_, lab in BUCKETS:
        sel = [e for e in ev if lo_ <= e[3] < hi_]
        if len(sel) < 50:
            print('  %-24s   мало данных (n=%d)' % (lab, len(sel)))
            continue
        base_up = sum(1 for e in sel if e[4] > 0) / len(sel)
        print('  %-24s n=%5d   доля сломов ВВЕРХ в клетке: %.1f%%' % (lab, len(sel), 100 * base_up))
        for s, snm in ((+1, 'вверх'), (-1, 'вниз')):
            bd = base_up if s > 0 else 1 - base_up
            for k in range(1, 6):
                sub = [e for e in sel if e[1] == s and min(e[2], 5) == k]
                if len(sub) < 40:
                    continue
                same = sum(1 for e in sub if e[4] == s)
                add = 100.0 * same / len(sub) - 100 * bd
                print('       серия %d подряд %-5s  n=%4d   туда же %s   база %5.1f%%   надбавка %+5.1f'
                      % (k, snm, len(sub), q(same, len(sub)), 100 * bd, add))
                w.writerow([nm, lab, snm, k, len(sub), same, '%.1f' % (100*bd), '%.1f' % add])
                if lab.startswith('РАВНО'):
                    svod.setdefault(nm, []).append(add)
    print()

print('=' * 100)
print('ГЛАВНАЯ КЛЕТКА — расстояния примерно РАВНЫ (0.8-1.25)')
for nm in ('5/5', '3/3', '2/2'):
    v = svod.get(nm, [])
    if v:
        print('  %s: клеток %d, надбавка мед %+.1f, мин %+.1f, макс %+.1f, положительных %d/%d'
              % (nm, len(v), st.median(v), min(v), max(v), sum(1 for x in v if x > 0), len(v)))
    else:
        print('  %s: клеток не набралось' % nm)
fh.close()
print('\nпострочно: ' + OUT)
