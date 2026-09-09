# -*- coding: utf-8 -*-
"""Нулевая точка: что делает ГОЛАЯ триггерная свеча, без единого условия.

Форма свечи в долях диапазона: тело, верхняя тень, нижняя тень.
Совпадение с одним из 40 шаблонов при допуске ±4% — свеча триггерная.

Меряем исход без всякого контекста: вход по закрытию триггерной свечи,
стоп за её экстремум, цель — кратные стопа. Это тот ноль, относительно
которого любой признак должен доказывать, что он что-то добавляет.
"""
import sys, statistics as st
sys.path.insert(0, 'research')
from core import load

TB = [12.6,14.7,17.0,32.0,20.2,4.1,23.0,27.9,30.7,35.2,24.5,41.9,26.0,25.9,11.6,23.3,49.3,14.0,18.3,25.4,27.9,45.7,29.2,40.6,41.9,10.4,41.5,23.6,32.2,18.8,35.5,32.2,54.2,10.8,47.3,16.0,21.6,19.8,9.9,27.5]
TU = [33.7,37.3,37.7,27.8,29.4,40.4,35.7,35.3,41.0,35.7,28.4,22.0,39.6,37.4,46.0,31.5,21.5,27.5,47.3,35.6,26.2,24.8,36.3,36.7,26.8,35.6,20.7,34.5,36.4,46.2,38.6,33.6,21.6,44.1,22.9,45.2,42.8,45.2,41.5,30.7]
TL = [53.7,48.0,45.3,40.2,50.4,55.5,41.3,36.8,28.3,29.1,47.1,36.0,34.5,36.7,42.5,45.2,29.2,58.5,34.4,39.0,46.0,29.5,34.5,22.6,31.3,54.0,37.9,41.9,31.4,34.9,25.8,34.2,24.2,45.1,29.8,38.8,35.5,35.0,48.6,41.8]
TOL = 4.0

rows = load()

def shape(r):
    o, h, l, c = r[1], r[2], r[3], r[4]
    rng = h - l
    if rng <= 0: return None
    body = abs(c - o)
    up_ = (h - o) if o > c else (h - c)
    lo_ = (c - l) if o > c else (o - l)
    return body/rng*100, up_/rng*100, lo_/rng*100

def is_trig(r):
    s = shape(r)
    if s is None: return -1
    b, u, l = s
    for i in range(40):
        if abs(b - TB[i]) <= TOL and abs(u - TU[i]) <= TOL and abs(l - TL[i]) <= TOL:
            return i
    return -1

trigs = [(b, is_trig(rows[b])) for b in range(len(rows))]
trigs = [(b, t) for b, t in trigs if t >= 0]
print(f'баров {len(rows)}, триггерных свечей {len(trigs)} = {len(trigs)/len(rows):.1%}')

def outcome(b, side, rr, maxbars=60):
    """стоп за экстремум триггерной свечи, цель rr*риск. -1 стоп, +rr цель, 0 не дошло"""
    o, h, l, c = rows[b][1], rows[b][2], rows[b][3], rows[b][4]
    if side == 1:
        stop = l; risk = c - stop
    else:
        stop = h; risk = stop - c
    if risk <= 0: return None
    tgt = c + rr*risk if side == 1 else c - rr*risk
    for j in range(b+1, min(b+1+maxbars, len(rows))):
        hh, ll = rows[j][2], rows[j][3]
        hitS = (ll <= stop) if side == 1 else (hh >= stop)
        hitT = (hh >= tgt) if side == 1 else (ll <= tgt)
        if hitS and hitT: return -1.0          # оба в одном баре — считаем стопом
        if hitS: return -1.0
        if hitT: return float(rr)
    return 0.0

print()
print(f'{"направление":>12} {"RR":>4} {"сделок":>8} {"цель":>7} {"стоп":>7} {"вышло время":>13} {"матожидание":>13}')
for side, nm in ((1, 'лонг'), (-1, 'шорт')):
    for rr in (1, 2, 3):
        res = [outcome(b, side, rr) for b, _ in trigs]
        res = [x for x in res if x is not None]
        w = sum(1 for x in res if x > 0); s = sum(1 for x in res if x < 0); t = sum(1 for x in res if x == 0)
        ev = st.mean(res)
        print(f'{nm:>12} {rr:>4} {len(res):>8} {w/len(res):>6.0%} {s/len(res):>6.0%} {t/len(res):>12.0%} {ev:>12.2f}R')
