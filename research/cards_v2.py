# -*- coding: utf-8 -*-
"""Четыре карточки, заход второй. Отличия от cards.py — два, согласованы:

 1. разреза по контексту 5/5 в карточке НЕТ: клеток 12 вместо 24;
    контекст меряется отдельно, одной строкой на карточку;
 2. магнит берёт ВСЕ непробитые колена 3/3, а не последние пять.
    Непробитое — то, чью цену рынок с момента подтверждения не проходил
    (правило движка: уровень живёт, пока не пробит).

Остальное как договорились: слой 3/3 при 0.33 / 0.5 / 2, вход по закрытию
триггерной свечи, стоп за её экстремум с буфером 0.1%, цель — ближайшее
непробитое колено нужной стороны с плечом не меньше 3, ведение до стопа
или цели, оба в одном баре = стоп, ждём 1500 баров. Фильтры движка сняты.
"""
import sys, csv, math, os
sys.path.insert(0, 'research')
from core import Core

BUF, RRMIN, FWD, NMIN = 0.001, 3.0, 1500, 30
OUT = 'research/out'; os.makedirs(OUT, exist_ok=True)

TB = [12.6,14.7,17.0,32.0,20.2,4.1,23.0,27.9,30.7,35.2,24.5,41.9,26.0,25.9,11.6,23.3,49.3,14.0,18.3,25.4,27.9,45.7,29.2,40.6,41.9,10.4,41.5,23.6,32.2,18.8,35.5,32.2,54.2,10.8,47.3,16.0,21.6,19.8,9.9,27.5]
TU = [33.7,37.3,37.7,27.8,29.4,40.4,35.7,35.3,41.0,35.7,28.4,22.0,39.6,37.4,46.0,31.5,21.5,27.5,47.3,35.6,26.2,24.8,36.3,36.7,26.8,35.6,20.7,34.5,36.4,46.2,38.6,33.6,21.6,44.1,22.9,45.2,42.8,45.2,41.5,30.7]
TL = [53.7,48.0,45.3,40.2,50.4,55.5,41.3,36.8,28.3,29.1,47.1,36.0,34.5,36.7,42.5,45.2,29.2,58.5,34.4,39.0,46.0,29.5,34.5,22.6,31.3,54.0,37.9,41.9,31.4,34.9,25.8,34.2,24.2,45.1,29.8,38.8,35.5,35.0,48.6,41.8]

def is_trig(r):
    o,h,l,c = r[1],r[2],r[3],r[4]; rng = h-l
    if rng <= 0: return False
    b = abs(c-o)/rng*100
    u = ((h-o) if o>c else (h-c))/rng*100
    lo = ((c-l) if o>c else (o-l))/rng*100
    return any(abs(b-TB[i])<=4 and abs(u-TU[i])<=4 and abs(lo-TL[i])<=4 for i in range(40))

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

def build(rows):
    """3/3 — точка счёта, направление, и живой список непробитых колен."""
    co = Core(rows, fib=0.33, jump=0.5); co.at = pivots_n(rows, 3)
    S=[None]*len(rows); liveH=[]; liveL=[]; nk=0
    for b in range(len(rows)):
        h, l = rows[b][2], rows[b][3]
        liveH = [p for p in liveH if p > h]        # пробитые сверху умирают
        liveL = [p for p in liveL if p < l]        # пробитые снизу умирают
        co.step(b)
        if len(co.KP) != nk or (co.KP and co.KM[-1] > 1):
            nk = len(co.KP)
            p, isHi = co.KP[-1], co.KH[-1]
            tgt = liveH if isHi else liveL
            if p not in tgt: tgt.append(p)
        S[b] = (co.KN[-1] if co.KN else -1, co.cdir(), list(liveH), list(liveL))
    return S

def build_ctx(rows):
    co = Core(rows, fib=0.33, jump=0.5); co.at = pivots_n(rows, 5)
    S=[0]*len(rows)
    for b in range(len(rows)):
        co.step(b); S[b] = 0 if co.inTrans else co.tr
    return S

def trade(rows, b, side, liveH, liveL):
    h, l, c = rows[b][2], rows[b][3], rows[b][4]
    sl = l*(1-BUF) if side==1 else h*(1+BUF)
    risk = (c-sl) if side==1 else (sl-c)
    if risk <= 0: return None
    pool = liveH if side==1 else liveL
    cand = sorted([p for p in pool if (p>c if side==1 else p<c)], reverse=(side==-1))
    tp = next((p for p in cand if abs(p-c)/risk >= RRMIN), None)
    if tp is None: return None
    rr = abs(tp-c)/risk
    for j in range(b+1, min(b+1+FWD, len(rows))):
        hh, ll = rows[j][2], rows[j][3]
        if (ll <= sl) if side==1 else (hh >= sl): return -1.0
        if (hh >= tp) if side==1 else (ll <= tp): return rr
    return None

def stat(v):
    n=len(v)
    if n==0: return 0,0.0,0.0
    m=sum(v)/n
    if n<2: return n,m,0.0
    sd=math.sqrt(sum((x-m)**2 for x in v)/(n-1))
    return n,m,2*sd/math.sqrt(n)

def verdict(n,d,e,h1,h2):
    if n < NMIN: return 'мало данных'
    if e>0 and abs(d)>e and ((h1>0 and h2>0) or (h1<0 and h2<0)):
        return 'МОЖНО' if d>0 else 'НЕЛЬЗЯ'
    return 'нейтрально'

grid=[]; ctxrows=[]
for tf, path in (('1H','data/XAUUSD_1h_2y.csv'), ('5m','data/XAUUSD_5m.csv')):
    rows = load(path); half = len(rows)//2
    W = build(rows); C = build_ctx(rows)
    trig = [b for b in range(len(rows)) if is_trig(rows[b])]
    cell={}; base={}; ctx={}; skip=0
    for b in trig:
        cn, cd, lh, ll = W[b]
        for side in (1,-1):
            r = trade(rows, b, side, lh, ll)
            if r is None: skip += 1; continue
            hf = 0 if b < half else 1
            base.setdefault((side,hf),[]).append(r)
            ctx.setdefault((side, 1 if C[b]==side else 0, hf),[]).append(r)
            if cn < 0 or cd == 0: continue
            cell.setdefault((cd,cn,side),[[],[]])[hf].append(r)
    tot = sum(len(v) for v in base.values())
    print(f'\n{"="*88}\n{tf}: триггерных свечей {len(trig)}, попыток {len(trig)*2}, '
          f'без магнита отброшено {skip} ({skip/(len(trig)*2):.0%}), сделок {tot}')
    for side in (1,-1):
        bv = base.get((side,0),[])+base.get((side,1),[]); n,m,e = stat(bv)
        print(f'   слепой вход {"LONG " if side==1 else "SHORT"}: {n:>5} сделок, {m:+.2f}R ± {e:.2f}')
        b1 = stat(base.get((side,0),[]))[1]; b2 = stat(base.get((side,1),[]))[1]
        for cx in (1,0):
            v = ctx.get((side,cx,0),[])+ctx.get((side,cx,1),[]); cn_,cm,ce = stat(v)
            h1 = stat(ctx.get((side,cx,0),[]))[1]-b1 if ctx.get((side,cx,0)) else 0.0
            h2 = stat(ctx.get((side,cx,1),[]))[1]-b2 if ctx.get((side,cx,1)) else 0.0
            ctxrows.append((tf,'LONG' if side==1 else 'SHORT',
                            'согласен' if cx else 'против/нет', cn_, cm, cm-m, ce,
                            verdict(cn_, cm-m, ce, h1, h2)))
    for (cd,cn,side), v in cell.items():
        allv = v[0]+v[1]; n,m,e = stat(allv)
        bs = stat(base.get((side,0),[])+base.get((side,1),[]))[1]
        b1 = stat(base.get((side,0),[]))[1]; b2 = stat(base.get((side,1),[]))[1]
        h1 = stat(v[0])[1]-b1 if v[0] else 0.0
        h2 = stat(v[1])[1]-b2 if v[1] else 0.0
        grid.append(dict(tf=tf,cd=cd,cn=cn,side=side,n=n,raw=m,err=e,base=bs,d=m-bs,
                         h1=h1,h2=h2,vd=verdict(n,m-bs,e,h1,h2)))

for tf in ('1H','5m'):
    for side in (1,-1):
        nm = 'ЛОНГ' if side==1 else 'ШОРТ'
        bs = next((g['base'] for g in grid if g['tf']==tf and g['side']==side), 0.0)
        print(f'\n╔══ КАРТОЧКА · {tf} · {nm} · слой 3/3 ' + '═'*40)
        print(f'║  слепой вход в эту сторону {bs:+.2f}R — от него надбавка')
        print(f'{"точка":>7} {"счёт":>6}{"сделок":>9}{"сырой":>9}{"надбавка":>11}{"шум":>8}   вердикт')
        print('─'*74)
        for cn in range(6):
            for cd in (1,-1):
                g = next((x for x in grid if x['tf']==tf and x['side']==side
                          and x['cn']==cn and x['cd']==cd), None)
                if g is None: continue
                print(f'{"("+str(cn)+")":>7} {"вверх ↑" if cd==1 else "вниз ↓":>6}'
                      f'{g["n"]:>9}{g["raw"]:>+9.2f}{g["d"]:>+11.2f}{g["err"]:>8.2f}   {g["vd"]}')
        print('─'*74)

print(f'\n\n═══ КОНТЕКСТ 5/5 ОТДЕЛЬНО (все точки вместе) ' + '═'*28)
print(f'{"тф":>4}{"сторона":>8}{"тренд 5/5":>16}{"сделок":>9}{"сырой":>9}{"надбавка":>11}{"шум":>8}   вердикт')
for r in ctxrows:
    print(f'{r[0]:>4}{r[1]:>8}{r[2]:>16}{r[3]:>9}{r[4]:>+9.2f}{r[5]:>+11.2f}{r[6]:>8.2f}   {r[7]}')

with open(f'{OUT}/cards_v2.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f)
    w.writerow(['тф','счёт','точка','сторона','сделок','сыройR','надбавка','шум2s','база','половина1','половина2','вердикт'])
    for g in grid:
        w.writerow([g['tf'],'вверх' if g['cd']==1 else 'вниз',g['cn'],
                    'LONG' if g['side']==1 else 'SHORT',g['n'],f'{g["raw"]:.4f}',
                    f'{g["d"]:.4f}',f'{g["err"]:.4f}',f'{g["base"]:.4f}',
                    f'{g["h1"]:.4f}',f'{g["h2"]:.4f}',g['vd']])
print(f'\n{len(grid)} клеток -> {OUT}/cards_v2.csv')
