# -*- coding: utf-8 -*-
"""Четыре карточки входа на одном слое 3/3. Параметры согласованы.

Слой рабочий   3/3, глубина 0.33, рывок 0.5, пауза 2
Слой контекст  5/5, те же 0.33 / 0.5 / 2 — своей карточки не имеет
Сигнал         триггерная свеча, 40 шаблонов, допуск +-4%
Вход           по закрытию свечи
Стоп           за экстремум триггерной свечи, буфер 0.1%
Цель           магнит: ближайшее из последних 5 колен 3/3 нужной стороны
               с плечом не меньше 3.0
Ведение        до стопа или цели, оба в одном баре = стоп, ждём 1500 баров
Фильтры движка не берём — их место занимают карточки

Клетка карточки = точка счёта x направление счёта x сторона сделки x
контекст (5/5 согласен со стороной сделки / против либо не определён).
Числа: сырой R и надбавка к слепому входу в ту же сторону.
Вердикт ставится по надбавке: рынок за два года прошёл +79%, по сырому R
любой лонг вышел бы «можно».
"""
import sys, csv, math, os
sys.path.insert(0, 'research')
from core import Core

BUF   = 0.001
RRMIN = 3.0
POOL  = 5       # сколько последних колен 3/3 даёт магнит
FWD   = 1500
NMIN  = 30      # меньше — «мало данных»
OUT   = 'research/out'
os.makedirs(OUT, exist_ok=True)

TB = [12.6,14.7,17.0,32.0,20.2,4.1,23.0,27.9,30.7,35.2,24.5,41.9,26.0,25.9,11.6,23.3,49.3,14.0,18.3,25.4,27.9,45.7,29.2,40.6,41.9,10.4,41.5,23.6,32.2,18.8,35.5,32.2,54.2,10.8,47.3,16.0,21.6,19.8,9.9,27.5]
TU = [33.7,37.3,37.7,27.8,29.4,40.4,35.7,35.3,41.0,35.7,28.4,22.0,39.6,37.4,46.0,31.5,21.5,27.5,47.3,35.6,26.2,24.8,36.3,36.7,26.8,35.6,20.7,34.5,36.4,46.2,38.6,33.6,21.6,44.1,22.9,45.2,42.8,45.2,41.5,30.7]
TL = [53.7,48.0,45.3,40.2,50.4,55.5,41.3,36.8,28.3,29.1,47.1,36.0,34.5,36.7,42.5,45.2,29.2,58.5,34.4,39.0,46.0,29.5,34.5,22.6,31.3,54.0,37.9,41.9,31.4,34.9,25.8,34.2,24.2,45.1,29.8,38.8,35.5,35.0,48.6,41.8]
TOL = 4.0

def is_trig(r):
    o,h,l,c = r[1],r[2],r[3],r[4]
    rng = h - l
    if rng <= 0: return False
    b  = abs(c-o)/rng*100
    u  = ((h-o) if o > c else (h-c))/rng*100
    lo = ((c-l) if o > c else (o-l))/rng*100
    return any(abs(b-TB[i]) <= TOL and abs(u-TU[i]) <= TOL and abs(lo-TL[i]) <= TOL for i in range(40))

def load(p):
    return [(r['time'],float(r['open']),float(r['high']),float(r['low']),float(r['close']))
            for r in csv.DictReader(open(p, encoding='utf-8-sig'))]

def pivots_n(rows, N):
    hi=[r[2] for r in rows]; lo=[r[3] for r in rows]; at={}
    for i in range(N, len(rows)-N):
        if all(hi[i-k]<=hi[i] for k in range(1,N+1)) and all(hi[i+k]<hi[i] for k in range(1,N+1)):
            at.setdefault(i+N,[]).append((i,hi[i],True))
        if all(lo[i-k]>=lo[i] for k in range(1,N+1)) and all(lo[i+k]>lo[i] for k in range(1,N+1)):
            at.setdefault(i+N,[]).append((i,lo[i],False))
    return at

def build_work(rows):
    """3/3: точка счёта, направление счёта, последние 5 колен для магнита"""
    co = Core(rows, fib=0.33, jump=0.5); co.at = pivots_n(rows, 3)
    S=[None]*len(rows)
    for b in range(len(rows)):
        co.step(b)
        k = list(zip(co.KP[-POOL:], co.KH[-POOL:]))
        S[b] = (co.KN[-1] if co.KN else -1, co.cdir(), k)
    return S

def build_ctx(rows):
    """5/5: тренд, 0 если ПЕРЕХОД"""
    co = Core(rows, fib=0.33, jump=0.5); co.at = pivots_n(rows, 5)
    S=[0]*len(rows)
    for b in range(len(rows)):
        co.step(b)
        S[b] = 0 if co.inTrans else co.tr
    return S

def trade(rows, b, side, knees):
    o,h,l,c = rows[b][1],rows[b][2],rows[b][3],rows[b][4]
    sl = l*(1-BUF) if side == 1 else h*(1+BUF)
    risk = (c-sl) if side == 1 else (sl-c)
    if risk <= 0: return None
    cand = [p for p,isHi in knees if isHi == (side == 1) and (p > c if side == 1 else p < c)]
    cand.sort(reverse=(side == -1))
    tp = next((p for p in cand if abs(p-c)/risk >= RRMIN), None)
    if tp is None: return None
    rr = abs(tp-c)/risk
    for j in range(b+1, min(b+1+FWD, len(rows))):
        hh, ll = rows[j][2], rows[j][3]
        if (ll <= sl) if side == 1 else (hh >= sl): return -1.0
        if (hh >= tp) if side == 1 else (ll <= tp): return rr
    return None

def stat(v):
    n = len(v)
    if n == 0: return 0, 0.0, 0.0
    m = sum(v)/n
    if n < 2: return n, m, 0.0
    sd = math.sqrt(sum((x-m)**2 for x in v)/(n-1))
    return n, m, 2*sd/math.sqrt(n)

def verdict(n, d, e, h1, h2):
    if n < NMIN: return 'мало данных'
    if e > 0 and abs(d) > e and ((h1 > 0 and h2 > 0) or (h1 < 0 and h2 < 0)):
        return 'МОЖНО' if d > 0 else 'НЕЛЬЗЯ'
    return 'нейтрально'

grid = []
for tf, path in (('1H','data/XAUUSD_1h_2y.csv'), ('5m','data/XAUUSD_5m.csv')):
    rows = load(path); half = len(rows)//2
    W = build_work(rows); C = build_ctx(rows)
    trig = [b for b in range(len(rows)) if is_trig(rows[b])]
    cell = {}; base = {}
    skipped = 0
    for b in trig:
        cn, cd, knees = W[b]
        for side in (1, -1):
            r = trade(rows, b, side, knees)
            if r is None:
                skipped += 1; continue
            bk = (side, 0 if b < half else 1)
            base.setdefault(bk, []).append(r)
            if cn < 0 or cd == 0: continue
            ctx = 1 if C[b] == side else 0
            cell.setdefault((cd, cn, side, ctx), [[], []])[0 if b < half else 1].append(r)
    print(f'\n{"="*92}\n{tf}: баров {len(rows)}, триггерных свечей {len(trig)}, '
          f'сделок без магнита отброшено {skipped}')
    for side in (1, -1):
        v = base.get((side,0),[]) + base.get((side,1),[])
        n, m, e = stat(v)
        print(f'   слепой вход {"LONG " if side==1 else "SHORT"}: {n:>5} сделок, {m:+.2f}R ± {e:.2f}')
    for k, v in cell.items():
        cd, cn, side, ctx = k
        allv = v[0]+v[1]
        n, m, e = stat(allv)
        bs = stat(base.get((side,0),[])+base.get((side,1),[]))[1]
        b1 = stat(base.get((side,0),[]))[1]; b2 = stat(base.get((side,1),[]))[1]
        h1 = stat(v[0])[1]-b1 if v[0] else 0.0
        h2 = stat(v[1])[1]-b2 if v[1] else 0.0
        grid.append(dict(tf=tf, cd=cd, cn=cn, side=side, ctx=ctx, n=n, raw=m, err=e,
                         base=bs, d=m-bs, h1=h1, h2=h2,
                         vd=verdict(n, m-bs, e, h1, h2)))

def card(tf, side):
    nm = 'ЛОНГ' if side == 1 else 'ШОРТ'
    print(f'\n╔══ КАРТОЧКА · {tf} · {nm} · слой 3/3 ' + '═'*46)
    bs = next((g['base'] for g in grid if g['tf']==tf and g['side']==side), 0.0)
    print(f'║  слепой вход в эту сторону {bs:+.2f}R — от него считается надбавка')
    print(f'{"точка":>7} {"счёт":>5} {"контекст 5/5":<14}{"сделок":>8}{"сырой":>9}{"надбавка":>11}{"шум":>8}   вердикт')
    print('─'*92)
    for cn in range(6):
        for cd in (1, -1):
            for ctx in (1, 0):
                g = next((x for x in grid if x['tf']==tf and x['side']==side
                          and x['cn']==cn and x['cd']==cd and x['ctx']==ctx), None)
                if g is None: continue
                print(f'{"("+str(cn)+")":>7} {"↑" if cd==1 else "↓":>5} '
                      f'{"согласен" if ctx else "против / нет":<14}'
                      f'{g["n"]:>8}{g["raw"]:>+9.2f}{g["d"]:>+11.2f}{g["err"]:>8.2f}   {g["vd"]}')
        print('─'*92)

for tf in ('1H','5m'):
    for side in (1,-1): card(tf, side)

with open(f'{OUT}/cards.csv','w',newline='',encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['тф','счёт','точка','сторона','контекст5/5','сделок','сыройR','надбавка','шум2s','база','половина1','половина2','вердикт'])
    for g in grid:
        w.writerow([g['tf'], 'вверх' if g['cd']==1 else 'вниз', g['cn'],
                    'LONG' if g['side']==1 else 'SHORT', 'согласен' if g['ctx'] else 'против/нет',
                    g['n'], f'{g["raw"]:.4f}', f'{g["d"]:.4f}', f'{g["err"]:.4f}',
                    f'{g["base"]:.4f}', f'{g["h1"]:.4f}', f'{g["h2"]:.4f}', g['vd']])
print(f'\n{len(grid)} клеток -> {OUT}/cards.csv')
