#!/usr/bin/env python3
"""Н9, подготовка: сколько бывает МУТНЫХ НОГ по корзинам.

Мутная нога — нога, внутри которой слой 5/5 одолжил у более быстрого
слоя 2 и более колена. Порог со слов владельца: «точно больше одного,
2-4». Здесь только ПОДСЧЁТ ЧАСТОТЫ — хватит ли случаев в корзине,
чтобы замер вообще что-то мог увидеть. Никаких исходов не считается.

Почему не через core.py: core.py — реплика движка ОДНОГО слоя со
счётом и смертью. Дорисовки (одалживания колен у быстрого слоя) в нём
нет вовсе, это механизм индикатора. Здесь он воспроизведён из
indicator/metki_prosto.pine дословно: f_relabel, f_push, f_sub.
"""
import csv, sys
from collections import Counter

PATH = sys.argv[1] if len(sys.argv) > 1 else 'data/XAUUSD_1h_2y.csv'
rows = list(csv.DictReader(open(PATH)))
O = [float(r['open']) for r in rows]; H = [float(r['high']) for r in rows]
L = [float(r['low']) for r in rows];  C = [float(r['close']) for r in rows]
N = len(rows)

def piv(i, d, hi):
    """ta.pivothigh/low(d, d), подтверждается на баре i, центр i-d"""
    c = i - d
    if c - d < 0 or c + d >= N:
        return None
    src = H if hi else L
    v = src[c]
    for k in range(c - d, c + d + 1):
        if k == c:
            continue
        if (src[k] >= v) if hi else (src[k] <= v):
            return None
    return v

class Layer:
    """колена слоя: f_push + f_relabel из пайна, один в один"""
    def __init__(self, d):
        self.d = d
        self.P, self.B, self.Hi, self.Lb = [], [], [], []
    def relabel(self):
        self.Lb = []
        for i in range(len(self.P)):
            hi = self.Hi[i]
            prev = None
            j = i - 1
            while j >= 0:
                if self.Hi[j] == hi:
                    prev = self.P[j]; break
                j -= 1
            cur = self.P[i]
            if prev is None:
                self.Lb.append('?')
            elif hi:
                self.Lb.append('HH' if cur > prev else 'LH')
            else:
                self.Lb.append('HL' if cur > prev else 'LL')
    def push(self, price, bar, hi):
        same = bool(self.P) and self.Hi[-1] == hi
        if same:
            better = price > self.P[-1] if hi else price < self.P[-1]
            if better:
                self.P[-1] = price; self.B[-1] = bar
        else:
            self.P.append(price); self.B.append(bar); self.Hi.append(hi)
        self.relabel()
        return not same

def f_sub(sB, sHi, x1, x2, s1, s2):
    """подпуть быстрого слоя внутри ноги: только то, что ЧЕРЕДУЕТСЯ"""
    keep = []
    want = not s1
    for k in range(len(sB)):
        b = sB[k]
        if x1 < b < x2 and sHi[k] == want:
            keep.append(k); want = not want
    while keep and sHi[keep[-1]] == s2:
        keep.pop()
    return keep

l5, l3, l2 = Layer(5), Layer(3), Layer(2)
FIB = 0.33

tr = 0; zB = -1; lvl = None; lvlHL = False; cnt = -1; imp = 0.0
legs_cnt = []   # ноги ДЕЙСТВУЮЩЕГО счёта: (i-1, i, номер точки)
для_всех = []   # все ноги 5/5

for i in range(N):
    nw5 = False
    for d, lay in ((5, l5), (3, l3), (2, l2)):
        v = piv(i, d, True)
        if v is not None:
            n = lay.push(H[i - d], i - d, True)
            if d == 5: nw5 = nw5 or n
        v = piv(i, d, False)
        if v is not None:
            n = lay.push(L[i - d], i - d, False)
            if d == 5: nw5 = nw5 or n
    # смерть
    if tr == 1 and lvl is not None:
        if min(O[i], C[i]) < lvl - imp * FIB:
            tr = 0; cnt = -1; zB = -1; lvl = None; lvlHL = False
    fr = any(piv(i, 5, s) is not None for s in (True, False))
    n5 = len(l5.P)
    if fr and n5 >= 2:
        lb, hi5, pr5, bb5, pp5 = l5.Lb[-1], l5.Hi[-1], l5.P[-1], l5.B[-1], l5.P[-2]
        if pr5 > pp5:
            imp = pr5 - pp5
        if tr == 1:
            restart = nw5 and cnt >= 5 and (not hi5) and lb == 'HL'
            if restart:
                zB = bb5; cnt = 0; lvl = pr5; lvlHL = True
            else:
                if nw5 and cnt < 5:
                    cnt += 1
                    legs_cnt.append((n5 - 2, n5 - 1, cnt))
                if (not hi5) and lb == 'HL':
                    lvl = pr5; lvlHL = True
        else:
            if hi5 and lb == 'HH':
                j = n5 - 2
                while j >= 0 and l5.Hi[j]:
                    j -= 1
                if j >= 0 and l5.Lb[j] == 'LL':      # trCont = «только LL»
                    tr = 1; zB = l5.B[j]; cnt = 1
                    lvl = l5.P[j]; lvlHL = False
                    legs_cnt.append((j, n5 - 1, 1))

for i in range(1, len(l5.P)):
    для_всех.append((i - 1, i, None))

def borrowed(a, b):
    x1, x2 = l5.B[a], l5.B[b]
    s1, s2 = l5.Hi[a], l5.Hi[b]
    k = f_sub(l3.B, l3.Hi, x1, x2, s1, s2)
    src = '3/3'
    if not k:
        k = f_sub(l2.B, l2.Hi, x1, x2, s1, s2)
        src = '2/2'
    return len(k), src

# Подпуть ВСЕГДА чётной длины, и это следствие самого f_sub, а не
# свойство рынка. Цепочка начинается со стороны, противоположной началу
# ноги, строго чередуется, и с хвоста снимается всё, что совпадает со
# стороной конца ноги. Значит нечётная длина невозможна: корзины 1, 3, 5
# пусты структурно. Реальные корзины — 0, 2, 4, 6 и больше.
def report(legs, title):
    c = Counter(); by_pt = {}
    for a, b, pt in legs:
        nk, _ = borrowed(a, b)
        key = nk if nk < 6 else 6
        c[key] += 1
        if pt is not None:
            by_pt.setdefault(pt, Counter())[key] += 1
    tot = sum(c.values())
    print(f'\n═══ {title} ═══   всего ног: {tot}')
    print('  одолжено колен   ног      доля   хватает ли на замер')
    for k in (0, 2, 4, 6):
        nm = '6 и больше' if k == 6 else str(k)
        n = c[k]
        mark = 'да' if n >= 100 else ('впритык' if n >= 50 else 'СЛЕПАЯ')
        print(f'  {nm:>14}   {n:5}   {100*n/tot if tot else 0:5.1f}%   {mark}')
    mut = sum(c[k] for k in (2, 4, 6))
    print(f'  ИТОГО мутных (2 и более): {mut}  ({100*mut/tot if tot else 0:.1f}%)')
    return by_pt

bp = report(legs_cnt, 'НОГИ ДЕЙСТВУЮЩЕГО СЧЁТА (0)-(5)')
report(для_всех,   'ВСЕ НОГИ СЛОЯ 5/5, вне зависимости от счёта')

print('\n═══ мутные ноги по номеру точки счёта ═══')
print('  точка    всего    мутных   доля')
for pt in sorted(bp):
    cc = bp[pt]
    t = sum(cc.values()); m = sum(cc[k] for k in range(2, 6))
    print(f'  ({pt})    {t:5}    {m:5}   {100*m/t if t else 0:5.1f}%')
