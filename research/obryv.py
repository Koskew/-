# -*- coding: utf-8 -*-
"""Что обрывает серию колен. Только лента, никаких правил движка.

Направление колена: HH и HL -> вверх, LH и LL -> вниз.
Серия: подряд идущие колена одного направления.
Обрыв: появилось встречное колено.

Главный вопрос: встречное колено — разовый шум или начало встречной
серии. И чем эти два случая отличаются по данным ленты.
"""
import csv, glob, statistics as st, collections

UP = {"HH", "HL"}

def load(p):
    rows = list(csv.DictReader(open(p, encoding='utf-8-sig'), delimiter=';'))
    out = []
    for r in rows:
        if r['подпись'] == '?': continue
        out.append(dict(lab=r['подпись'], up=r['подпись'] in UP,
                        leg=float(r['нога'].replace(',', '.')),
                        gap=int(r['баров от предыдущего']),
                        mud=int(r['мутность']),
                        price=float(r['цена колена'].replace(',', '.'))))
    return out

def runs(K):
    """список серий: (направление, индекс начала, длина)"""
    out = []; i = 0
    while i < len(K):
        j = i
        while j + 1 < len(K) and K[j+1]['up'] == K[i]['up']: j += 1
        out.append((K[i]['up'], i, j - i + 1)); i = j + 1
    return out

def med(v): return st.median(v) if v else float('nan')

print('ЧТО ОБРЫВАЕТ СЕРИЮ КОЛЕН\n')
for p in sorted(glob.glob('research/out/lenta/lenta_*.csv')):
    tag = p.split('_')[1]; lay = p.split('_')[2].replace('.csv','').replace('-','/')
    K = load(p); R = runs(K)
    lens = [r[2] for r in R]
    dist = collections.Counter(lens)
    tot = len(R)
    print(f'── {tag} · {lay} · колен {len(K)} · серий {tot}')
    print(f'   длина серии: ' + '  '.join(
        f'{k}:{dist[k]/tot*100:.0f}%' for k in sorted(dist)[:7]) +
        f'   медиана {med(lens):.0f}  максимум {max(lens)}')

    # разовый встречный против настоящего слома
    odin = []; slom = []
    for a in range(len(R) - 1):
        d, i, ln = R[a]
        nd, ni, nln = R[a+1]
        k = K[ni]                       # первое встречное колено
        rec = dict(leg=k['leg'], gap=k['gap'], mud=k['mud'],
                   prev=K[ni-1]['leg'] if ni else 0.0, ln=ln)
        (odin if nln == 1 else slom).append(rec)
    mg = med([k['leg'] for k in K])
    def show(name, S):
        if not S: return
        print(f'   {name:<22} {len(S):>5} ({len(S)/(len(odin)+len(slom))*100:>4.0f}%) · '
              f'нога {med([x["leg"] for x in S]):>7.2f} = {med([x["leg"] for x in S])/mg:>4.2f} медианы · '
              f'нога/предыдущая {med([x["leg"]/x["prev"] for x in S if x["prev"]>0]):>5.2f} · '
              f'баров {med([x["gap"] for x in S]):>4.0f} · '
              f'мутных {sum(1 for x in S if x["mud"]>=2)/len(S)*100:>4.0f}%')
    show('встречное разовое', odin)
    show('встречное = слом', slom)
    print()
