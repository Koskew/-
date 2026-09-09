# -*- coding: utf-8 -*-
"""Нормированная проверка двух находок.

Связь «мутных колен больше — тренд живёт дольше» может быть тавтологией:
в длинном тренде колен больше, значит и мутных больше. То же с числом
встречных трендов 2/2.

Честная проверка: берём ТОЛЬКО первые W баров тренда, считаем признак
там, и смотрим, что будет ДАЛЬШЕ. В выборке только тренды, дожившие до W.
"""
import sys, csv, statistics as st
sys.path.insert(0, 'research')
from core import load
from library import pivots_n

rows = load()
W = 20

def knees(lb):
    at = pivots_n(rows, lb); K = []
    for b in sorted(at):
        for bar, price, isHi in at[b]:
            if K and K[-1][2] == isHi:
                K[-1] = (b, price, isHi, K[-1][3] + 1)
            else:
                K.append((b, price, isHi, 1))
    return K
K5, K2 = knees(5), knees(2)

def rd(n):
    with open(f'research/out/{n}.csv', encoding='utf-8') as f:
        out = []
        for r in csv.DictReader(f):
            for k in ('dir','start','end','dur','maxKN','knees','mud','zeroBar'):
                if k in r and r[k] != '': r[k] = int(float(r[k]))
            for k in ('pStart','pEnd','imp','moveImp','mfeImp','deathLvl'):
                if k in r and r[k] != '': r[k] = float(r[k])
            out.append(r)
        return out
T5, T2 = rd('trends_55'), rd('trends_22')

def early(T, K, nm):
    S = [t for t in T if t['dur'] >= W]
    print(f'\n{nm}   ({len(S)} трендов из {len(T)} дожили до {W} баров)')
    print(f'{"мутных за первые "+str(W)+"б":>22} {"шт":>4} {"проживёт ЕЩЁ":>13} {"ход ПОСЛЕ "+str(W)+"б":>18}')
    for lo, hi, t_ in ((0, 1, 'ни одного'), (1, 2, 'одно'), (2, 99, 'два и больше')):
        G = []
        for t in S:
            ins = [k for k in K if t['start'] <= k[0] <= t['start'] + W]
            m = sum(1 for k in ins if k[3] >= 2)
            if lo <= m < hi: G.append(t)
        if not G: continue
        rest = [t['dur'] - W for t in G]
        # ход после W баров, в импульсах
        mv = []
        for t in G:
            b0 = t['start'] + W
            if b0 < len(rows):
                imp = t['imp'] if t['imp'] > 0 else 1e-9
                mv.append((t['pEnd'] - rows[b0][4]) / imp * (1 if t['dir'] == 1 else -1))
        print(f'{t_:>22} {len(G):>4} {st.median(rest):>12.0f}б {st.median(mv):>17.2f}')

print('═══ МУТНОСТЬ В НАЧАЛЕ ТРЕНДА — ЧТО БУДЕТ ДАЛЬШЕ ═══')
early([t for t in T5 if t['dir'] == 1], K5, '5/5 восходящий')
early([t for t in T5 if t['dir'] == -1], K5, '5/5 нисходящий')
early([t for t in T2 if t['dir'] == 1], K2, '2/2 восходящий')
early([t for t in T2 if t['dir'] == -1], K2, '2/2 нисходящий')

print('\n\n═══ ВСТРЕЧНЫЕ 2/2 В НАЧАЛЕ ТРЕНДА 5/5 ═══')
S = [t for t in T5 if t['dur'] >= W]
print(f'({len(S)} трендов 5/5 из {len(T5)} дожили до {W} баров)')
print(f'{"встречных 2/2 за "+str(W)+"б":>22} {"шт":>4} {"проживёт ЕЩЁ":>13} {"ход ПОСЛЕ":>12}')
for lo, hi, t_ in ((0, 1, 'ни одного'), (1, 99, 'один и больше')):
    G = []
    for t in S:
        c = sum(1 for x in T2 if x['dir'] != t['dir'] and t['start'] <= x['start'] <= t['start'] + W)
        if lo <= c < hi: G.append(t)
    if not G: continue
    rest = [t['dur'] - W for t in G]
    mv = []
    for t in G:
        b0 = t['start'] + W
        imp = t['imp'] if t['imp'] > 0 else 1e-9
        mv.append((t['pEnd'] - rows[b0][4]) / imp * (1 if t['dir'] == 1 else -1))
    print(f'{t_:>22} {len(G):>4} {st.median(rest):>12.0f}б {st.median(mv):>11.2f}')

# ── та же ловушка возможна и со счётом: глубокий счёт требует времени ──
print('\n\n═══ ГЛУБИНА СЧЁТА В НАЧАЛЕ ТРЕНДА — ЧТО БУДЕТ ДАЛЬШЕ ═══')
from core import Core
def depth_early(lb, fib, T, nm):
    co = Core(rows, fib=fib); co.at = pivots_n(rows, lb)
    seq = []
    for b in range(len(rows)):
        co.step(b)
        seq.append(co.KN[-1] if co.KN else -1)
    S = [t for t in T if t['dur'] >= W]
    print(f'\n{nm}   ({len(S)} трендов из {len(T)} дожили до {W} баров)')
    print(f'{"счёт дошёл за "+str(W)+"б до":>22} {"шт":>4} {"проживёт ЕЩЁ":>13} {"ход ПОСЛЕ":>12}')
    for lo, hi, t_ in ((0, 3, 'точки (2)'), (3, 5, 'точек (3)-(4)'), (5, 99, 'точки (5)')):
        G = [t for t in S if lo <= max(seq[t['start']:t['start']+W+1]) < hi]
        if not G: continue
        rest = [t['dur'] - W for t in G]
        mv = []
        for t in G:
            b0 = t['start'] + W
            imp = t['imp'] if t['imp'] > 0 else 1e-9
            mv.append((t['pEnd'] - rows[b0][4]) / imp * (1 if t['dir'] == 1 else -1))
        print(f'{t_:>22} {len(G):>4} {st.median(rest):>12.0f}б {st.median(mv):>11.2f}')
depth_early(5, 0.33, [t for t in T5 if t['dir'] == 1],  '5/5 восходящий')
depth_early(5, 0.33, [t for t in T5 if t['dir'] == -1], '5/5 нисходящий')
depth_early(2, 0.15, [t for t in T2 if t['dir'] == 1],  '2/2 восходящий')
depth_early(2, 0.15, [t for t in T2 if t['dir'] == -1], '2/2 нисходящий')
