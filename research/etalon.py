# -*- coding: utf-8 -*-
"""Эталонность счёта: ведёт ли себя эталонный набор подписей иначе.

Эталон вверх:  LL LH HL HH HL HH
Эталон вниз:   HH HL LH LL LH LL

Окно — шесть подряд идущих колен. Наблюдаем в момент, когда шестое
колено ЗАКРЫТО, то есть когда создано седьмое: только тогда вся
последовательность известна целиком.

Исход — симметричная гонка от закрытия бара наблюдения: цена прошла X
в сторону эталона раньше, чем X против. X — медианная нога слоя, одна
на все события, чтобы размер окна не влиял на дистанцию.

Три группы для каждой стороны:
  ЭТАЛОН     — вся шестёрка совпала
  ХВОСТ      — последние две подписи как у эталона, начало другое
  ВСЕ ОКНА   — база
Сравнение с ХВОСТОМ отвечает на главный вопрос: добавляет ли форма
начала что-то сверх очевидной концовки.
"""
import sys, csv, math, statistics as st
sys.path.insert(0, 'research')
from core import Core

FWD = 300
ET_UP = ["LL", "LH", "HL", "HH", "HL", "HH"]
ET_DN = ["HH", "HL", "LH", "LL", "LH", "LL"]

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

def knees(rows, N):
    """закрытые колена: подпись, цена, бар закрытия (создания следующего)"""
    at = pivots_n(rows, N)
    co = Core(rows, fib=0.33); co.at = at
    out = []; created = 0; emitted = 0
    for b in range(len(rows)):
        side = co.KH[-1] if co.KP else None
        for (_bar, _p, isHi) in at.get(b, []):
            if side is None or isHi != side: created += 1
            side = isHi
        co.step(b)
        shift = created - len(co.KP)
        while emitted < created - 1:
            i = emitted - shift
            if i < 0: emitted += 1; continue
            out.append(dict(lab=co.KL[i], price=co.KP[i], closed=b))
            emitted += 1
    return out

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

UP = {"HH", "HL"}

for tag, path in (('9 лет', 'data/XAUUSD_1h_9y.csv'), ('2 года', 'data/XAUUSD_1h_2y.csv')):
    rows = load(path); half = len(rows) // 2
    for N in (5, 3, 2):
        K = knees(rows, N)
        K = [k for k in K if k['lab'] != '?']
        legs = [abs(K[i]['price'] - K[i-1]['price']) for i in range(1, len(K))]
        X = st.median(legs)
        labs = [k['lab'] for k in K]
        ev = []
        for i in range(len(K) - 6):
            w = labs[i:i+6]
            b = K[i+5]['closed']
            for et, up, nm in ((ET_UP, True, '↑'), (ET_DN, False, '↓')):
                grp = None
                if w == et: grp = 'ЭТАЛОН'
                elif w[-2:] == et[-2:]: grp = 'ХВОСТ'
                else: continue
                # сколько ещё колен подряд в ту же сторону после окна
                cont = 0
                for j in range(i+6, len(K)):
                    if (labs[j] in UP) == up: cont += 1
                    else: break
                ev.append(dict(grp=grp, up=up, nm=nm, b=b, cont=cont,
                               half=0 if b < half else 1))
        for e in ev:
            e['res'] = race(rows, e['b'], e['up'], X)
        ev = [e for e in ev if e['res'] is not None]

        print(f'══ {tag} · слой {N}/{N} · X = {X:.2f}')
        for nm, up in (('↑ вверх', True), ('↓ вниз', False)):
            S = [e for e in ev if e['up'] == up]
            if not S: continue
            print(f'   {nm}')
            for grp in ('ЭТАЛОН', 'ХВОСТ'):
                G = [e for e in S if e['grp'] == grp]
                if len(G) < 40:
                    print(f'      {grp:<10}{len(G):>6}  мало данных'); continue
                p, e = wil(sum(x['res'] for x in G), len(G))
                h1 = [x for x in G if x['half'] == 0]; h2 = [x for x in G if x['half'] == 1]
                p1 = sum(x['res'] for x in h1)/len(h1) if h1 else 0
                p2 = sum(x['res'] for x in h2)/len(h2) if h2 else 0
                cm = st.median([x['cont'] for x in G])
                print(f'      {grp:<10}{len(G):>6}  идёт по эталону {p:>4.0%} ± {e:.0%}   '
                      f'половины {p1:>3.0%} / {p2:>3.0%}   колен дальше {cm:.0f}')
        print()
