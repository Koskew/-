# -*- coding: utf-8 -*-
"""Второй срез: чем настоящий слом серии отличается от разового встречного.

Откат от всей серии = насколько встречное колено вернуло ход, который
серия прошла целиком. Серия [i..j] прошла от цены колена i-1 до цены
колена j; встречное колено j+1 откатывает часть этого хода.
"""
import csv, glob, statistics as st, collections, math

UP = {"HH", "HL"}

def load(p):
    out = []
    for r in csv.DictReader(open(p, encoding='utf-8-sig'), delimiter=';'):
        if r['подпись'] == '?': continue
        out.append(dict(lab=r['подпись'], up=r['подпись'] in UP,
                        leg=float(r['нога'].replace(',', '.')),
                        gap=int(r['баров от предыдущего']),
                        mud=int(r['мутность']),
                        price=float(r['цена колена'].replace(',', '.'))))
    return out

def runs(K):
    out = []; i = 0
    while i < len(K):
        j = i
        while j + 1 < len(K) and K[j+1]['up'] == K[i]['up']: j += 1
        out.append((i, j)); i = j + 1
    return out

def wilson(k, n):
    """2 сигмы на долю"""
    if n == 0: return 0.0, 0.0
    p = k / n
    return p, 2 * math.sqrt(p * (1 - p) / n)

print('ЧТО ОТЛИЧАЕТ НАСТОЯЩИЙ СЛОМ ОТ РАЗОВОГО ВСТРЕЧНОГО\n')
print('База: доля сломов среди всех обрывов. Ниже — как она меняется.\n')

for p in sorted(glob.glob('research/out/lenta/lenta_9y_*.csv')):
    lay = p.split('_')[2].replace('.csv','').replace('-','/')
    K = load(p); R = runs(K)
    rec = []
    for a in range(len(R) - 1):
        i, j = R[a]; ni, nj = R[a+1]
        if i == 0: continue                      # нет цены до серии
        move = abs(K[j]['price'] - K[i-1]['price'])
        if move <= 0: continue
        back = abs(K[ni]['price'] - K[j]['price'])
        rec.append(dict(slom=(nj - ni + 1) > 1,
                        ln=j - i + 1,
                        ret=back / move,
                        mud=K[ni]['mud'] >= 2,
                        mudprev=K[j]['mud'] >= 2))
    n = len(rec); base, e = wilson(sum(r['slom'] for r in rec), n)
    print(f'── 9 лет · {lay} · обрывов {n} · база слома {base:.0%} ± {e:.0%}')

    def cut(name, keyf, buckets):
        print(f'   {name}')
        for lbl, test in buckets:
            S = [r for r in rec if test(keyf(r))]
            if len(S) < 40: continue
            pr, ee = wilson(sum(r['slom'] for r in S), len(S))
            d = pr - base
            mark = ' ←' if abs(d) > ee + e else ''
            print(f'      {lbl:<22}{len(S):>6} сд   слом {pr:>4.0%} ± {ee:.0%}   '
                  f'{d:+.0%} к базе{mark}')

    cut('мутность встречного колена', lambda r: r['mud'],
        [('чистое', lambda v: not v), ('мутное', lambda v: v)])
    cut('мутность последнего колена серии', lambda r: r['mudprev'],
        [('чистое', lambda v: not v), ('мутное', lambda v: v)])
    cut('длина оборвавшейся серии', lambda r: r['ln'],
        [('1 колено', lambda v: v == 1), ('2', lambda v: v == 2),
         ('3', lambda v: v == 3), ('4', lambda v: v == 4),
         ('5 и больше', lambda v: v >= 5)])
    cut('откат от всей серии', lambda r: r['ret'],
        [('до 25%', lambda v: v < .25), ('25-50%', lambda v: .25 <= v < .5),
         ('50-75%', lambda v: .5 <= v < .75), ('75-100%', lambda v: .75 <= v < 1.0),
         ('больше 100%', lambda v: v >= 1.0)])
    print()
