# -*- coding: utf-8 -*-
"""Мутность колена как ПРЕДСКАЗАНИЕ, а не как описание.

Момент наблюдения один для всех колен: бар, на котором создано следующее
колено. В этот момент предыдущее закрыто окончательно — известны его
подпись, цена и мутность. Так меряется и чистое, и мутное: одинаково,
без перекоса по времени.

Исход — не подпись следующего колена (она известна в тот же миг и потому
ничего не опережает), а ЦЕНА: симметричная гонка от закрытия бара
наблюдения, по X в обе стороны. X — медианная нога слоя, одна и та же
для всех событий, чтобы размер события не влиял на дистанцию.

Направление гонки: сторона подписи закрывшегося колена.
HH и HL -> вверх, LH и LL -> вниз.
"""
import sys, csv, math, statistics as st
sys.path.insert(0, 'research')
from core import Core

FWD = 300
UP = {"HH", "HL"}

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

def race(rows, b, up, X):
    c = rows[b][4]
    tgt = c + X if up else c - X
    opp = c - X if up else c + X
    for j in range(b + 1, min(b + 1 + FWD, len(rows))):
        h, l = rows[j][2], rows[j][3]
        a = (h >= tgt) if up else (l <= tgt)
        o = (l <= opp) if up else (h >= opp)
        if a and o: return None
        if a: return 1
        if o: return 0
    return None

def wil(k, n):
    if n == 0: return 0.0, 0.0
    p = k / n
    return p, 2 * math.sqrt(p * (1 - p) / n)

def collect(path, N):
    rows = load(path); at = pivots_n(rows, N)
    co = Core(rows, fib=0.33); co.at = at
    created = 0; ev = []; prevdir = None; legs = []
    for b in range(len(rows)):
        side = co.KH[-1] if co.KP else None
        newk = 0
        for (_bar, _p, isHi) in at.get(b, []):
            if side is None or isHi != side: newk += 1
            side = isHi
        co.step(b)
        if newk and len(co.KP) >= 3:
            # закрылось предпоследнее колено: индекс -2
            i = len(co.KP) - 2
            lab = co.KL[i]
            if lab == '?': created += newk; continue
            up = lab in UP
            pd = None
            if co.KL[i-1] != '?': pd = co.KL[i-1] in UP
            legs.append(abs(co.KP[i] - co.KP[i-1]))
            ev.append(dict(b=b, up=up, km=co.KM[i],
                           counter=(pd is not None and pd != up),
                           lab=lab))
        created += newk
    X = st.median(legs)
    out = []
    half = len(rows) // 2
    for e in ev:
        r = race(rows, e['b'], e['up'], X)
        if r is None: continue
        e['res'] = r; e['half'] = 0 if e['b'] < half else 1
        out.append(e)
    return out, X, len(rows)

def show(nm, S, base=None):
    if len(S) < 40:
        print(f'   {nm:<32}{len(S):>6}  мало данных'); return None
    p, e = wil(sum(x['res'] for x in S), len(S))
    h1 = [x for x in S if x['half'] == 0]; h2 = [x for x in S if x['half'] == 1]
    p1 = sum(x['res'] for x in h1)/len(h1) if h1 else 0
    p2 = sum(x['res'] for x in h2)/len(h2) if h2 else 0
    d = f'{p-base:+.0%}' if base is not None else '    '
    print(f'   {nm:<32}{len(S):>6}  идёт по колену {p:>4.0%} ± {e:.0%}  '
          f'{d}   половины {p1:>3.0%} / {p2:>3.0%}')
    return p

print('МУТНОСТЬ КАК ПРЕДСКАЗАНИЕ')
print('Момент наблюдения: бар создания следующего колена — тогда предыдущее')
print('закрыто и мутность известна. Исход: цена прошла X в сторону подписи')
print('закрывшегося колена раньше, чем X против. X = медианная нога слоя.\n')

for tag, path in (('9 лет', 'data/XAUUSD_1h_9y.csv'), ('2 года', 'data/XAUUSD_1h_2y.csv')):
    for N in (5, 3, 2):
        ev, X, nb = collect(path, N)
        print(f'══ {tag} · слой {N}/{N} · событий {len(ev)} · X = {X:.2f}')
        base = show('ВСЕ', ev)
        show('чистое  KM=1', [x for x in ev if x['km'] == 1], base)
        show('мутное  KM=2', [x for x in ev if x['km'] == 2], base)
        show('мутное  KM=3', [x for x in ev if x['km'] == 3], base)
        show('мутное  KM>=4', [x for x in ev if x['km'] >= 4], base)
        C = [x for x in ev if x['counter']]
        if len(C) >= 40:
            print('   ── только встречные колена ──')
            bc = show('все встречные', C)
            show('   чистое', [x for x in C if x['km'] == 1], bc)
            show('   мутное', [x for x in C if x['km'] >= 2], bc)
        print()
