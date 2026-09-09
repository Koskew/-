# -*- coding: utf-8 -*-
"""Карта точек: что разрешено на каждой точке счёта.

Нечётная точка — конец импульса, впереди коррекция: торгуем ПРОТИВ счёта
с короткой целью 1:2. Чётная — конец коррекции, впереди импульс: торгуем
ПО счёту, цель — ближайшая непробитая метка нужной стороны, минимум 1:3.
"""
import sys, statistics as st, math
sys.path.insert(0, 'research')
from core import Core, load
from library import pivots_n
from trigger_base import is_trig

rows = load()
BUF = 0.001

def build(lb, fib):
    co = Core(rows, fib=fib); co.at = pivots_n(rows, lb)
    S = {}
    for b in range(len(rows)):
        co.step(b)
        # непробитые метки нужной стороны: цены колен-вершин и колен-низов
        hi = [co.KP[i] for i in range(len(co.KL)) if co.KL[i] in ("HH", "LH")]
        lo = [co.KP[i] for i in range(len(co.KL)) if co.KL[i] in ("LL", "HL")]
        S[b] = dict(cn=co.KN[-1] if co.KN else -1, cd=co.cdir(),
                    tr=0 if co.inTrans else co.tr, hi=hi, lo=lo)
    return S

S5 = build(5, 0.33)
S2 = build(2, 0.15)

def go(b, side, rrfix, minrr, S):
    """rrfix — фиксированная цель; иначе магнит: ближайшая метка с RR >= minrr"""
    o, h, l, c = rows[b][1], rows[b][2], rows[b][3], rows[b][4]
    sl = l * (1 - BUF) if side == 1 else h * (1 + BUF)
    risk = (c - sl) if side == 1 else (sl - c)
    if risk <= 0: return None
    if rrfix is not None:
        tp = c + rrfix * risk if side == 1 else c - rrfix * risk
        rr = rrfix
    else:
        pool = S[b]['hi'] if side == 1 else S[b]['lo']
        cand = [p for p in pool if (p > c if side == 1 else p < c)]
        cand.sort(reverse=(side == -1))
        tp = None
        for p in cand:
            if abs(p - c) / risk >= minrr:
                tp = p; break
        if tp is None: return None
        rr = abs(tp - c) / risk
    for j in range(b + 1, min(b + 1501, len(rows))):
        hh, ll = rows[j][2], rows[j][3]
        if (ll <= sl if side == 1 else hh >= sl): return -1.0
        if (hh >= tp if side == 1 else ll <= tp): return float(rr)
    return None

def run(S, nm):
    buckets = {}
    for b in range(len(rows)):
        if is_trig(rows[b]) < 0: continue
        st_ = S[b]
        cd, cn = st_['cd'], st_['cn']
        if cd == 0 or cn < 0: continue
        if cn in (1, 3):                    # конец импульса -> шорт коррекции
            side = -cd; r = go(b, side, 2.0, None, S); key = f'({cn}) против счёта, RR 2'
        elif cn in (2, 4):                  # конец коррекции -> вход по счёту
            side = cd;  r = go(b, side, None, 3.0, S); key = f'({cn}) по счёту, магнит ≥3'
        else:
            continue
        if r is not None: buckets.setdefault(key, []).append(r)
    print(f'\n═══ {nm} ═══')
    print(f'{"точка":>26} {"сделок":>7} {"TP":>5} {"сумма":>9} {"на сделку":>11} {"шум ±":>7}')
    tot = []
    for k in sorted(buckets):
        R = buckets[k]; tot += R
        sd = st.pstdev(R) if len(R) > 1 else 0
        print(f'{k:>26} {len(R):>7} {sum(1 for x in R if x>0)/len(R):>4.0%} '
              f'{sum(R):>+8.1f}R {st.mean(R):>+10.2f}R {2*sd/math.sqrt(len(R)):>6.2f}')
    if tot:
        sd = st.pstdev(tot)
        print(f'{"ВСЯ КАРТА":>26} {len(tot):>7} {sum(1 for x in tot if x>0)/len(tot):>4.0%} '
              f'{sum(tot):>+8.1f}R {st.mean(tot):>+10.2f}R {2*sd/math.sqrt(len(tot)):>6.2f}')

run(S5, 'КАРТА НА СЧЁТЕ 5/5')
run(S2, 'КАРТА НА СЧЁТЕ 2/2')

# ── магнит против фиксированной цели, с фильтром старшего и без ──
print('\n\n═══ ЧЁТНЫЕ ТОЧКИ: ЧЕМ ЗАКРЫВАТЬ И ЧЕМ ФИЛЬТРОВАТЬ ═══')
print(f'{"слой":>5} {"цель":>16} {"фильтр 5/5":>12} {"сделок":>7} {"TP":>5} {"сумма":>9} {"на сделку":>11} {"шум ±":>7}')
for lay, S in (('5/5', S5), ('2/2', S2)):
    for tgt in ('магнит ≥3', 'фикс 3R'):
        for flt in ('нет', 'тренд 5/5'):
            R = []
            for b in range(len(rows)):
                if is_trig(rows[b]) < 0: continue
                stt = S[b]
                if stt['cd'] == 0 or stt['cn'] not in (2, 4): continue
                side = stt['cd']
                if flt == 'тренд 5/5' and S5[b]['tr'] != side: continue
                r = go(b, side, None, 3.0, S) if tgt == 'магнит ≥3' else go(b, side, 3.0, None, S)
                if r is not None: R.append(r)
            if len(R) < 10: continue
            sd = st.pstdev(R)
            print(f'{lay:>5} {tgt:>16} {flt:>12} {len(R):>7} {sum(1 for x in R if x>0)/len(R):>4.0%} '
                  f'{sum(R):>+8.1f}R {st.mean(R):>+10.2f}R {2*sd/math.sqrt(len(R)):>6.2f}')
