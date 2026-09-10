# -*- coding: utf-8 -*-
"""Четыре карты входа: слой x направление сделки, отдельно 1H и 5m.

Карта отвечает на один вопрос: стоя на точке счёта N при направлении
счёта D, что даёт вход в сторону S. Ничего не предполагаем зеркальным —
лонги и шорты меряются отдельно.

Стоп и цель — не одна штука, а варианты. Пока свой стоп не задан,
меряем три и показываем, насколько от него зависит карта.
"""
import sys, csv, math, os
sys.path.insert(0, 'research')
from core import Core

BUF = 0.001
FWD = 1500
OUT = 'research/out'
os.makedirs(OUT, exist_ok=True)

TB = [12.6,14.7,17.0,32.0,20.2,4.1,23.0,27.9,30.7,35.2,24.5,41.9,26.0,25.9,11.6,23.3,49.3,14.0,18.3,25.4,27.9,45.7,29.2,40.6,41.9,10.4,41.5,23.6,32.2,18.8,35.5,32.2,54.2,10.8,47.3,16.0,21.6,19.8,9.9,27.5]
TU = [33.7,37.3,37.7,27.8,29.4,40.4,35.7,35.3,41.0,35.7,28.4,22.0,39.6,37.4,46.0,31.5,21.5,27.5,47.3,35.6,26.2,24.8,36.3,36.7,26.8,35.6,20.7,34.5,36.4,46.2,38.6,33.6,21.6,44.1,22.9,45.2,42.8,45.2,41.5,30.7]
TL = [53.7,48.0,45.3,40.2,50.4,55.5,41.3,36.8,28.3,29.1,47.1,36.0,34.5,36.7,42.5,45.2,29.2,58.5,34.4,39.0,46.0,29.5,34.5,22.6,31.3,54.0,37.9,41.9,31.4,34.9,25.8,34.2,24.2,45.1,29.8,38.8,35.5,35.0,48.6,41.8]
TOL = 4.0

def is_trig(r):
    o, h, l, c = r[1], r[2], r[3], r[4]
    rng = h - l
    if rng <= 0: return -1
    b = abs(c - o) / rng * 100
    u = ((h - o) if o > c else (h - c)) / rng * 100
    lo = ((c - l) if o > c else (o - l)) / rng * 100
    for i in range(40):
        if abs(b - TB[i]) <= TOL and abs(u - TU[i]) <= TOL and abs(lo - TL[i]) <= TOL:
            return i
    return -1

def load(path):
    return [(r['time'], float(r['open']), float(r['high']), float(r['low']), float(r['close']))
            for r in csv.DictReader(open(path, encoding='utf-8-sig'))]

def pivots_n(rows, N):
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
    for i in range(N, len(rows) - N):
        if all(hi[i-k] <= hi[i] for k in range(1, N+1)) and all(hi[i+k] < hi[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, N+1)) and all(lo[i+k] > lo[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, lo[i], False))
    return at

def build(rows, lb, fib):
    """Состояние слоя на каждом баре: точка счёта, направление, тренд,
    запас, уровень, последние колена каждой стороны, метки-магниты."""
    co = Core(rows, fib=fib); co.at = pivots_n(rows, lb)
    S = [None] * len(rows)
    for b in range(len(rows)):
        co.step(b)
        hi = [co.KP[i] for i in range(len(co.KL)) if co.KL[i] in ("HH", "LH")]
        lo = [co.KP[i] for i in range(len(co.KL)) if co.KL[i] in ("LL", "HL")]
        kHi = kLo = None
        for i in range(len(co.KP) - 1, -1, -1):
            if kHi is None and co.KH[i]: kHi = co.KP[i]
            if kLo is None and not co.KH[i]: kLo = co.KP[i]
            if kHi is not None and kLo is not None: break
        tr = 0 if co.inTrans else co.tr
        S[b] = dict(cn=co.KN[-1] if co.KN else -1, cd=co.cdir(), tr=tr,
                    room=co.room(co.cstart()) if hasattr(co, 'room') else None,
                    lvl=None if co.inTrans else co.lvl,
                    kHi=kHi, kLo=kLo, hi=hi, lo=lo)
    return S

def stop_of(rows, b, side, kind, st):
    o, h, l, c = rows[b][1], rows[b][2], rows[b][3], rows[b][4]
    if kind == 'свеча':
        p = l if side == 1 else h
    elif kind == 'колено':
        p = st['kLo'] if side == 1 else st['kHi']
    else:                                     # уровень тренда
        p = st['lvl']
        if p is None: return None
        if side == 1 and not (st['tr'] == 1 and p < c): return None
        if side == -1 and not (st['tr'] == -1 and p > c): return None
    if p is None: return None
    p = p * (1 - BUF) if side == 1 else p * (1 + BUF)
    if (side == 1 and p >= c) or (side == -1 and p <= c): return None
    return p

def sim(rows, b, side, sl, tgt_kind, st):
    c = rows[b][4]
    risk = (c - sl) if side == 1 else (sl - c)
    if risk <= 0: return None
    if tgt_kind == 'магнит':
        pool = st['hi'] if side == 1 else st['lo']
        cand = sorted([p for p in pool if (p > c if side == 1 else p < c)],
                      reverse=(side == -1))
        tp = None
        for p in cand:
            if abs(p - c) / risk >= 3.0: tp = p; break
        if tp is None: return None
        rr = abs(tp - c) / risk
    else:
        rr = float(tgt_kind[:-1])            # '3R' / '2R'
        tp = c + rr * risk if side == 1 else c - rr * risk
    for j in range(b + 1, min(b + 1 + FWD, len(rows))):
        hh, ll = rows[j][2], rows[j][3]
        hitS = (ll <= sl) if side == 1 else (hh >= sl)
        hitT = (hh >= tp) if side == 1 else (ll <= tp)
        if hitS: return -1.0
        if hitT: return rr
    return None

def stat(v):
    n = len(v)
    if n == 0: return 0, 0.0, 0.0
    m = sum(v) / n
    if n < 2: return n, m, 0.0
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1))
    return n, m, 2 * sd / math.sqrt(n)

STOPS = ['свеча', 'колено', 'уровень']
TGTS  = ['магнит', '3R', '2R']

def run(tf, path, out):
    rows = load(path)
    trig = [b for b in range(len(rows)) if is_trig(rows[b]) >= 0]
    print(f'\n{"="*72}\n{tf}: баров {len(rows)}, триггерных свечей {len(trig)} '
          f'({len(trig)/len(rows):.1%}), {rows[0][0][:10]} — {rows[-1][0][:10]}')
    half = len(rows) // 2
    for lname, (lb, fib) in (('5/5', (5, 0.33)), ('2/2', (2, 0.15))):
        S = build(rows, lb, fib)
        # cell[(cd, cn, side, stop, tgt)] = [R, ...]; отдельно половины
        cell = {}
        for b in trig:
            st = S[b]
            if st['cn'] < 0 or st['cd'] == 0: continue
            for side in (1, -1):
                for sk in STOPS:
                    sl = stop_of(rows, b, side, sk, st)
                    if sl is None: continue
                    for tk in TGTS:
                        r = sim(rows, b, side, sl, tk, st)
                        if r is None: continue
                        key = (st['cd'], st['cn'], side, sk, tk)
                        cell.setdefault(key, [[], []])[0 if b < half else 1].append(r)
        for k, v in cell.items():
            out.append((tf, lname) + k + tuple(stat(v[0] + v[1])) + (stat(v[0])[1], stat(v[1])[1], len(v[0]), len(v[1])))
        # сводка стоп x цель по всему слою
        print(f'\n─── {tf} · слой {lname} · какой стоп и какая цель ' + '─' * 22)
        print(f'{"":10}' + ''.join(f'{t:>18}' for t in TGTS))
        for sk in STOPS:
            line = f'{sk:10}'
            for tk in TGTS:
                v = [x for k, vv in cell.items() if k[3] == sk and k[4] == tk for x in vv[0] + vv[1]]
                n, m, e = stat(v)
                line += f'{n:>6} {m:+.2f}±{e:.2f}'
            print(line)
    return out

out = []
run('1H', 'data/XAUUSD_1h_2y.csv', out)
run('5m', 'data/XAUUSD_5m.csv', out)

with open(f'{OUT}/maps_grid.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['тф','слой','счёт','точка','сторона','стоп','цель','сделок','EV','шум2s','EV_1половина','EV_2половина','n1','n2'])
    for r in out: w.writerow([r[0],r[1],r[2],r[3],'LONG' if r[4]==1 else 'SHORT',r[5],r[6],r[7],f'{r[8]:.4f}',f'{r[9]:.4f}',f'{r[10]:.4f}',f'{r[11]:.4f}',r[12],r[13]])
print(f'\nполная сетка -> {OUT}/maps_grid.csv  ({len(out)} строк)')
