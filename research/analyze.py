# -*- coding: utf-8 -*-
"""Анализ библиотеки трендов. Читает research/out/*.csv"""
import csv, statistics as st

def rd(n):
    with open(f'research/out/{n}.csv', encoding='utf-8') as f:
        out = []
        for r in csv.DictReader(f):
            for k in ('dir','start','end','dur','maxKN','knees','mud','zeroBar',
                      'n2','n2ag','n2ag_','lagAg','durAg','durAg_','zeroToDeath'):
                if k in r and r[k] != '': r[k] = int(float(r[k]))
            for k in ('pStart','pEnd','imp','moveImp','mfeImp','deathLvl'):
                if k in r and r[k] != '': r[k] = float(r[k])
            out.append(r)
        return out

T5, T2, NS = rd('trends_55'), rd('trends_22'), rd('nested')
def q(v, p): return st.quantiles(v, n=10)[p] if len(v) > 9 else (max(v) if v else 0)

print('═══ 1. БИБЛИОТЕКА ТРЕНДОВ ═══\n')
print(f'{"группа":>16} {"шт":>4} {"жизнь, баров":>22} {"ход в импульсах":>22}')
print(f'{"":>16} {"":>4} {"мед":>6}{"90-й":>8}{"макс":>8} {"мед":>7}{"лучший":>8}{"доля +":>7}')
GR = [('5/5 восходящий', [t for t in T5 if t['dir'] == 1]),
      ('5/5 нисходящий', [t for t in T5 if t['dir'] == -1]),
      ('2/2 восходящий', [t for t in T2 if t['dir'] == 1]),
      ('2/2 нисходящий', [t for t in T2 if t['dir'] == -1])]
for nm, G in GR:
    d = [t['dur'] for t in G]; m = [t['moveImp'] for t in G]; f = [t['mfeImp'] for t in G]
    print(f'{nm:>16} {len(G):>4} {st.median(d):>6.0f}{q(d,8):>8.0f}{max(d):>8} '
          f'{st.median(m):>7.2f}{st.median(f):>8.2f}{sum(1 for x in m if x>0)/len(m):>7.0%}')

print('\n═══ 2. ЧЕМ ПОДТВЕРЖДЁН И ЧТО ИЗ ЭТОГО ВЫШЛО ═══\n')
print(f'{"группа":>16} {"подтверждение":>14} {"шт":>4} {"доля":>6} {"жизнь":>7} {"ход":>7} {"доля +":>7}')
for nm, G in GR:
    for born in ('пауза', 'рывок'):
        S = [t for t in G if t['born'] == born]
        if not S: continue
        m = [t['moveImp'] for t in S]
        print(f'{nm:>16} {born:>14} {len(S):>4} {len(S)/len(G):>5.0%} '
              f'{st.median([t["dur"] for t in S]):>6.0f}б {st.median(m):>7.2f} {sum(1 for x in m if x>0)/len(m):>7.0%}')

print('\n═══ 3. ГЛУБИНА СЧЁТА ВНУТРИ ТРЕНДА ═══\n')
print(f'{"группа":>16} {"докуда дошёл счёт":>18} {"шт":>4} {"доля":>6} {"жизнь":>7} {"ход":>7}')
for nm, G in GR:
    for lo, hi, t_ in ((0, 3, 'до (2)'), (3, 5, '(3)–(4)'), (5, 99, '(5) и дальше')):
        S = [t for t in G if lo <= t['maxKN'] < hi]
        if not S: continue
        print(f'{nm:>16} {t_:>18} {len(S):>4} {len(S)/len(G):>5.0%} '
              f'{st.median([t["dur"] for t in S]):>6.0f}б {st.median([t["moveImp"] for t in S]):>7.2f}')

print('\n═══ 4. МУТНОСТЬ ВНУТРИ ТРЕНДА ═══\n')
print(f'{"группа":>16} {"мутных колен":>14} {"шт":>4} {"жизнь":>7} {"ход":>7} {"доля +":>7}')
for nm, G in GR:
    for lo, hi, t_ in ((0, 1, 'ни одного'), (1, 2, 'одно'), (2, 99, 'два и больше')):
        S = [t for t in G if lo <= t['mud'] < hi]
        if not S: continue
        m = [t['moveImp'] for t in S]
        print(f'{nm:>16} {t_:>14} {len(S):>4} {st.median([t["dur"] for t in S]):>6.0f}б '
              f'{st.median(m):>7.2f} {sum(1 for x in m if x>0)/len(m):>7.0%}')

print('\n═══ 5. ТРЕНДЫ 2/2 ВНУТРИ ТРЕНДА 5/5 ═══\n')
print(f'всего трендов 5/5: {len(NS)}')
ag = [n['n2ag'] for n in NS]; agst = [n['n2ag_'] for n in NS]
print(f'внутри одного тренда 5/5 в среднем: {st.mean([n["n2"] for n in NS]):.1f} трендов 2/2, '
      f'из них {st.mean(ag):.1f} по направлению и {st.mean(agst):.1f} против')
L = [n['lagAg'] for n in NS if n['lagAg'] >= 0]
print(f'первый согласный тренд 2/2 появляется через {st.median(L):.0f} баров медианой '
      f'({sum(1 for x in L if x == 0)/len(L):.0%} — сразу в тот же бар)')
print(f'трендов 5/5 без единого согласного 2/2: {sum(1 for n in NS if n["n2ag"] == 0)} из {len(NS)}')
print()
print(f'{"сколько 2/2 ПРОТИВ":>20} {"шт":>4} {"жизнь 5/5":>10} {"ход 5/5":>9} {"доля +":>7}')
for lo, hi, t_ in ((0, 1, 'ни одного'), (1, 2, 'один'), (2, 3, 'два'), (3, 99, 'три и больше')):
    S = [n for n in NS if lo <= n['n2ag_'] < hi]
    if not S: continue
    m = [n['moveImp'] for n in S]
    print(f'{t_:>20} {len(S):>4} {st.median([n["dur"] for n in S]):>9.0f}б '
          f'{st.median(m):>9.2f} {sum(1 for x in m if x>0)/len(m):>7.0%}')

print('\n═══ 6. ОТ НУЛЯ СЧЁТА ДО СЛОМА ═══\n')
z = [n['zeroToDeath'] for n in NS]
d = [n['dur'] for n in NS]
print(f'от точки (0) счёта 5/5 до слома тренда: медиана {st.median(z):.0f} баров, 90-й {q(z,8):.0f}')
print(f'от подтверждения тренда до слома:       медиана {st.median(d):.0f} баров, 90-й {q(d,8):.0f}')
print(f'то есть счёт стартует в среднем за {st.median(z)-st.median(d):.0f} баров ДО подтверждения тренда')
