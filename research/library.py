# -*- coding: utf-8 -*-
"""Библиотека всех трендов за два года: 5/5 и 2/2, восходящие и нисходящие.

Каждый тренд — от подтверждения до слома, со всеми обстоятельствами:
чем подтверждён, какой был импульс, докуда дошёл счёт, сколько мутных
колен внутри, сколько прошла цена. Для каждого тренда 5/5 отдельно
собирается, какие тренды 2/2 сформировались внутри него.

Пишет research/out/trends_55.csv, trends_22.csv, nested.csv
"""
import sys, os, csv, statistics
sys.path.insert(0, 'research')
from core import Core, load, up

def pivots_n(rows, N):
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
    for i in range(N, len(rows) - N):
        if all(hi[i-k] <= hi[i] for k in range(1, N+1)) and all(hi[i+k] < hi[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, N+1)) and all(lo[i+k] > lo[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, lo[i], False))
    return at

rows = load()
OUT = 'research/out'
os.makedirs(OUT, exist_ok=True)


def collect(lb, fib):
    """Прогон одного слоя с записью каждого тренда."""
    co = Core(rows, fib=fib); co.at = pivots_n(rows, lb)
    trends = []
    cur = None
    prevActive = False
    prevTr = 0
    for b in range(len(rows)):
        nlog = len(co.log)
        co.step(b)
        events = [e for _, e, _ in co.log[nlog:]]
        active = (co.tr != 0 and not co.inTrans)

        # закрытие: тренд умер на этом баре
        if cur is not None and 'СМЕРТЬ' in events:
            o, h, l, c = rows[b][1], rows[b][2], rows[b][3], rows[b][4]
            cur['end'] = b
            cur['dur'] = b - cur['start']
            cur['pEnd'] = c
            cur['deathLvl'] = co.pD
            imp = cur['imp'] if cur['imp'] > 0 else 1e-9
            cur['moveImp'] = (c - cur['pStart']) / imp * (1 if cur['dir'] == 1 else -1)
            cur['mfeImp'] = (cur['ext'] - cur['pStart']) / imp * (1 if cur['dir'] == 1 else -1)
            cur['maxKN'] = cur['maxKN']
            trends.append(cur)
            cur = None

        # открытие: тренд подтверждён на этом баре
        if active and not prevActive:
            zb = None
            cs = co.cstart()
            if cs >= 0: zb = co.KB[cs]
            cur = dict(layer=f'{lb}/{lb}', dir=co.tr, start=b, tStart=rows[b][0][:16],
                       born='рывок' if 'РЫВОК' in events else ('пауза' if 'ПАУЗА' in events else 'первый'),
                       pStart=rows[b][4], imp=co.imp, lvl=co.lvl if co.lvl is not None else float('nan'),
                       prov=co.lvlProv, zeroBar=zb if zb is not None else b,
                       ext=rows[b][4], maxKN=0, knees=0, mud=0, nk0=len(co.KP))
        if cur is not None:
            h, l = rows[b][2], rows[b][3]
            cur['ext'] = max(cur['ext'], h) if cur['dir'] == 1 else min(cur['ext'], l)
            # глубина ДЕЙСТВУЮЩЕГО счёта, а не максимум по всему окну колен
            if co.KN: cur['maxKN'] = max(cur['maxKN'], co.KN[-1])
        prevActive = active
        prevTr = co.tr
    # незакрытый тренд в конце данных не считаем
    return trends, co


T5, C5 = collect(5, 0.33)
T2, C2 = collect(2, 0.15)

for t in (T5 + T2):
    t['knees'] = 0
    t['mud'] = 0

# колена внутри тренда считаем отдельным проходом по коленам слоя
def fill_knees(T, lb, fib):
    co = Core(rows, fib=fib); co.at = pivots_n(rows, lb)
    seen = []
    for b in range(len(rows)):
        n0 = len(co.KP); co.step(b)
        if len(co.KP) > n0 or (co.KP and (not seen or seen[-1][0] != b)):
            pass
    # проще: собрать все колена одним проходом по пивотам
    at = pivots_n(rows, lb)
    K = []
    for b in sorted(at):
        for bar, price, isHi in at[b]:
            if K and K[-1][2] == isHi:
                K[-1] = (b, price, isHi, K[-1][3] + 1)
            else:
                K.append((b, price, isHi, 1))
    for t in T:
        ins = [k for k in K if t['start'] <= k[0] <= t['end']]
        t['knees'] = len(ins)
        t['mud'] = sum(1 for k in ins if k[3] >= 2)
fill_knees(T5, 5, 0.33)
fill_knees(T2, 2, 0.15)

# ── вложенность: какие тренды 2/2 внутри каждого тренда 5/5 ──
nested = []
for t in T5:
    ins = [x for x in T2 if t['start'] <= x['start'] <= t['end']]
    ag = [x for x in ins if x['dir'] == t['dir']]
    ag_ = [x for x in ins if x['dir'] != t['dir']]
    firstAg = min((x['start'] - t['start'] for x in ag), default=None)
    nested.append(dict(start=t['start'], tStart=t['tStart'], dir=t['dir'], dur=t['dur'],
                       moveImp=t['moveImp'], born=t['born'], maxKN=t['maxKN'],
                       n2=len(ins), n2ag=len(ag), n2ag_=len(ag_),
                       lagAg=firstAg if firstAg is not None else -1,
                       durAg=statistics.median([x['dur'] for x in ag]) if ag else -1,
                       durAg_=statistics.median([x['dur'] for x in ag_]) if ag_ else -1,
                       zeroToDeath=t['end'] - t['zeroBar']))

def dump(name, rowsd, cols):
    with open(f'{OUT}/{name}.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in rowsd: w.writerow(r)

cols = ['layer','dir','tStart','start','end','dur','born','prov','pStart','pEnd','imp',
        'moveImp','mfeImp','maxKN','knees','mud','zeroBar','deathLvl']
dump('trends_55', T5, cols)
dump('trends_22', T2, cols)
dump('nested', nested, ['tStart','start','dir','dur','moveImp','born','maxKN',
                        'n2','n2ag','n2ag_','lagAg','durAg','durAg_','zeroToDeath'])

print(f'трендов 5/5: {len(T5)}   трендов 2/2: {len(T2)}')
print(f'файлы: {OUT}/trends_55.csv, trends_22.csv, nested.csv')
