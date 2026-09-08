# -*- coding: utf-8 -*-
"""Подбор правила рисования боковика.

Колени строятся так же, как в gde_my_v4.pine: сырые пивоты 5/5,
серия одинаковых по стороне меток схлопывается в свой экстремум.
Дальше проверяется скользящее окно: N подряд идущих колен,
размах которых <= K * медианы амплитуды колена.
"""
import csv, statistics, sys

L = R = 5

def load(path):
    rows = []
    with open(path, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rows.append((r['time'], float(r['high']), float(r['low'])))
    return rows

def pivots(rows):
    """ta.pivothigh/pivotlow: >= слева, > справа (правило Pine)."""
    hi = [r[1] for r in rows]
    lo = [r[2] for r in rows]
    out = []
    for i in range(L, len(rows) - R):
        v = hi[i]
        if all(hi[i-k] <= v for k in range(1, L+1)) and all(hi[i+k] < v for k in range(1, R+1)):
            out.append((i, v, True))
        v = lo[i]
        if all(lo[i-k] >= v for k in range(1, L+1)) and all(lo[i+k] > v for k in range(1, R+1)):
            out.append((i, v, False))
    out.sort()
    return out

def knees(pv):
    """Схлопывание серии одинаковых по стороне меток в экстремум."""
    K = []
    for bar, price, isHi in pv:
        if K and K[-1][2] == isHi:
            b, p, h = K[-1]
            if (isHi and price > p) or (not isHi and price < p):
                K[-1] = (bar, price, isHi)
        else:
            K.append((bar, price, isHi))
    return K

def scan(K, N, mult, med):
    """Окна из N колен с размахом <= mult*med. Перекрывающиеся сливаются."""
    boxes = []
    for i in range(len(K) - N + 1):
        w = K[i:i+N]
        top = max(k[1] for k in w)
        bot = min(k[1] for k in w)
        if top - bot <= mult * med:
            b0, b1 = w[0][0], w[-1][0]
            if boxes and b0 <= boxes[-1][1]:
                boxes[-1] = (boxes[-1][0], max(boxes[-1][1], b1),
                             max(boxes[-1][2], top), min(boxes[-1][3], bot))
            else:
                boxes.append((b0, b1, top, bot))
    return boxes

def eff(w):
    """КПД хода: размах окна / суммарный путь по коленам."""
    span = max(k[1] for k in w) - min(k[1] for k in w)
    path = sum(abs(w[i][1] - w[i-1][1]) for i in range(1, len(w)))
    return (span / path if path else 1.0), span

def hits(boxes, rows, lo_t, hi_t):
    """Попал ли хоть один бокс во временное окно разметки."""
    for b0, b1, top, bot in boxes:
        if rows[b1][0] >= lo_t and rows[b0][0] <= hi_t:
            return True
    return False

rows = load('data/XAUUSD_1h_2y.csv')
K = knees(pivots(rows))
amps = [abs(K[i][1] - K[i-1][1]) for i in range(1, len(K))]
med = statistics.median(amps)
total = len(rows)
print(f'баров {total}, колен {len(K)}, медиана амплитуды колена {med:.2f}')
print()
print(f'{"N":>3} {"K":>5} {"боксов":>7} {"покрытие":>9}  дек-2025  июль-2026')
for N in (5, 6, 7):
    for mult in (1.5, 2.0, 2.5, 3.0):
        B = scan(K, N, mult, med)
        cov = sum(b1 - b0 for b0, b1, _, _ in B) / total
        d = 'да ' if hits(B, rows, '2025-12-23', '2025-12-27') else 'нет'
        j = 'да ' if hits(B, rows, '2026-07-01', '2026-07-31') else 'нет'
        print(f'{N:>3} {mult:>5.1f} {len(B):>7} {cov:>8.0%}   {d:>7}   {j:>7}')


# ==== ПРОВЕРКА 2: КПД хода вместо чистой ширины ====

# точное окно декабрьской разметки: верх 4550.15, низ 4430.52
dec = [i for i, k in enumerate(K) if 4300 < k[1] < 4600 and '2025-12-23' <= rows[k[0]][0] <= '2025-12-27']
wd = K[dec[0]:dec[-1]+1]
e, s = eff(wd)
print(f'медиана колена {med:.2f}')
print(f'разметка дек-2025: {len(wd)} колен, КПД {e:.2f}, размах {s:.1f} = {s/med:.1f} медианы')
print(f'  верх {max(k[1] for k in wd):.2f}  низ {min(k[1] for k in wd):.2f}')
print()
print(f'{"N":>3} {"КПД<=":>6} {"W":>4} {"боксов":>7} {"покрытие":>9} {"медиана длины":>14}  дек')
for N in (5, 6, 7):
    for T in (0.22, 0.26, 0.30):
        for W in (3.0, 4.0):
            B = []
            for i in range(len(K) - N + 1):
                w = K[i:i+N]
                e, s = eff(w)
                if e <= T and s <= W * med:
                    b0, b1 = w[0][0], w[-1][0]
                    if B and b0 <= B[-1][1]:
                        B[-1] = (B[-1][0], max(B[-1][1], b1))
                    else:
                        B.append((b0, b1))
            cov = sum(b1-b0 for b0, b1 in B) / total
            ln = statistics.median([b1-b0 for b0, b1 in B]) if B else 0
            hit = any(rows[b1][0] >= '2025-12-23' and rows[b0][0] <= '2025-12-27' for b0, b1 in B)
            print(f'{N:>3} {T:>6.2f} {W:>4.1f} {len(B):>7} {cov:>8.0%} {ln:>13.0f}б  {"да" if hit else "нет"}')
