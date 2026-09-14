# -*- coding: utf-8 -*-
"""Решающая проверка: убираем фору.

В первом прогоне цель стояла за УРОВНЕМ, поэтому свеча, закрывшаяся
дальше за уровень, была ближе к цели и выигрывала механически.

Здесь гонка считается ОТ ЗАКРЫТИЯ свечи касания и симметрично:
что раньше — цена пройдёт 0.5 импульса в сторону сноса или 0.5 импульса
обратно. Форы нет ни у кого: старт один и тот же, расстояния равны.

Если тело по-прежнему обгоняет фитиль — признак настоящий.
Если сравнялись — весь эффект был механикой.
"""
import sys, csv, math
sys.path.insert(0, 'research')
from core import Core

FWD, GO = 300, 0.5

def load(p):
    out = []
    for r in csv.DictReader(open(p, encoding='utf-8-sig')):
        o, h, l, c = float(r['open']), float(r['high']), float(r['low']), float(r['close'])
        out.append((r['time'], min(max(o, l), h), h, l, min(max(c, l), h)))
    return out

def pivots_n(rows, N):
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
    for i in range(N, len(rows) - N):
        if all(hi[i-k] <= hi[i] for k in range(1, N+1)) and all(hi[i+k] < hi[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, N+1)) and all(lo[i+k] > lo[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, lo[i], False))
    return at

def race_from_close(rows, b, tr, imp):
    """от закрытия свечи касания, симметрично: снос=1, отбой=0"""
    c = rows[b][4]
    down = c - GO * imp; up = c + GO * imp
    tgtB, tgtR = (down, up) if tr == 1 else (up, down)
    for j in range(b + 1, min(b + 1 + FWD, len(rows))):
        h, l = rows[j][2], rows[j][3]
        hitB = (l <= tgtB) if tr == 1 else (h >= tgtB)
        hitR = (h >= tgtR) if tr == 1 else (l <= tgtR)
        if hitB and hitR: return None
        if hitB: return 1
        if hitR: return 0
    return None

def wil(k, n):
    if n == 0: return 0.0, 0.0
    p = k / n
    return p, 2 * math.sqrt(p * (1 - p) / n)

rows = load('data/XAUUSD_1h_9y.csv'); half = len(rows) // 2
print('ГОНКА ОТ ЗАКРЫТИЯ, СИММЕТРИЧНАЯ — форы нет ни у кого')
print(f'снос = цена прошла {GO} импульса в сторону слома, '
      f'отбой = столько же обратно, ждём {FWD} баров\n')

for N in (5, 3, 2):
    co = Core(rows, fib=0.33, jump=0.5); co.at = pivots_n(rows, N)
    ev = []; seen = set()
    for b in range(len(rows)):
        co.step(b)
        if co.inTrans or co.tr == 0 or co.lvl is None or co.imp <= 0: continue
        key = (co.tr, co.trFrom, round(co.lvl, 4))
        h, l, c = rows[b][2], rows[b][3], rows[b][4]
        cross = (l < co.lvl) if co.tr == 1 else (h > co.lvl)
        if not cross or key in seen: continue
        seen.add(key)
        r = race_from_close(rows, b, co.tr, co.imp)
        if r is None: continue
        d = (co.lvl - c) / co.imp if co.tr == 1 else (c - co.lvl) / co.imp
        ev.append(dict(tr=co.tr, res=r, d=d, body=d > 0, half=0 if b < half else 1))

    def cell(nm, S):
        if len(S) < 30:
            print(f'   {nm:<30}{len(S):>5}  мало данных'); return
        p, e = wil(sum(x['res'] for x in S), len(S))
        h1 = [x for x in S if x['half'] == 0]; h2 = [x for x in S if x['half'] == 1]
        p1 = sum(x['res'] for x in h1)/len(h1) if h1 else 0
        p2 = sum(x['res'] for x in h2)/len(h2) if h2 else 0
        print(f'   {nm:<30}{len(S):>5}  снос {p:>4.0%} ± {e:.0%}   половины {p1:>3.0%} / {p2:>3.0%}')

    print(f'══ слой {N}/{N} · событий {len(ev)}')
    cell('ВСЕ', ev)
    cell('ТЕЛО', [x for x in ev if x['body']])
    cell('ФИТИЛЬ', [x for x in ev if not x['body']])
    print('   ── по направлению ──')
    for tr, nm in ((1, 'восх, снос вниз'), (-1, 'нисх, снос вверх')):
        S = [x for x in ev if x['tr'] == tr]
        cell(nm, S)
        cell('   ТЕЛО', [x for x in S if x['body']])
        cell('   ФИТИЛЬ', [x for x in S if not x['body']])
    print('   ── по глубине закрытия ──')
    for nm, t in [('фитиль глубже −0.10', lambda d: d < -0.10),
                  ('фитиль −0.10…0',      lambda d: -0.10 <= d < 0),
                  ('тело 0…0.05',         lambda d: 0 <= d < 0.05),
                  ('тело 0.05…0.15',      lambda d: 0.05 <= d < 0.15),
                  ('тело 0.15…0.33',      lambda d: 0.15 <= d < 0.33)]:
        cell(nm, [x for x in ev if t(x['d'])])
    print()
