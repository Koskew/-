# -*- coding: utf-8 -*-
"""Карты из research/out/maps_grid.csv, очищенные от сноса рынка.

За два года золото прошло +79%, поэтому на 1H в сыром виде выигрывает
любой лонг и проигрывает любой шорт — карта в этом не участвует. На 5m
за 3.5 месяца снос -2.9%, картина зеркальная. Поэтому каждая клетка
показывается как ОТКЛОНЕНИЕ от базы той же стороны: сколько точка
добавляет к тому, что и так даёт вход в эту сторону вслепую.
"""
import csv, math, collections
G = list(csv.DictReader(open('research/out/maps_grid.csv', encoding='utf-8-sig')))
for r in G:
    r['точка'] = int(r['точка']); r['счёт'] = int(r['счёт']); r['сделок'] = int(r['сделок'])
    for k in ('EV','шум2s','EV_1половина','EV_2половина'): r[k] = float(r[k])
    r['n1'] = int(r['n1']); r['n2'] = int(r['n2'])

# база: та же сторона, тот же стоп и цель, все точки вместе
base = collections.defaultdict(lambda: [0.0, 0])
for r in G:
    k = (r['тф'], r['слой'], r['сторона'], r['стоп'], r['цель'])
    base[k][0] += r['EV'] * r['сделок']; base[k][1] += r['сделок']
BASE = {k: (v[0] / v[1] if v[1] else 0.0, v[1]) for k, v in base.items()}

def cellf(r, bs):
    if r is None or r['сделок'] < 25: return f'{"—":>17}'
    d = r['EV'] - bs
    mark = ''
    if abs(d) > r['шум2s'] and r['шум2s'] > 0:
        h1 = r['EV_1половина'] - bs; h2 = r['EV_2половина'] - bs
        mark = '**' if (h1 > 0 and h2 > 0) or (h1 < 0 and h2 < 0) else ' *'
    return f"{r['сделок']:>4} {d:+.2f}±{r['шум2s']:.2f}{mark:>2}"

def show(tf, layer, stop, tgt):
    sel = {(r['счёт'], r['точка'], r['сторона']): r for r in G
           if r['тф']==tf and r['слой']==layer and r['стоп']==stop and r['цель']==tgt}
    bl = BASE.get((tf, layer, 'LONG', stop, tgt), (0,0))
    bs = BASE.get((tf, layer, 'SHORT', stop, tgt), (0,0))
    print(f'\n╔═ {tf} · метки {layer} · стоп «{stop}» · цель «{tgt}» ' + '═'*22)
    print(f'║  база вслепую:  LONG {bl[0]:+.2f}R ({bl[1]} сд)   '
          f'SHORT {bs[0]:+.2f}R ({bs[1]} сд)   — от неё и считаем')
    print(f'{"точка":>6} │{"счёт ВВЕРХ ↑":^36}│{"счёт ВНИЗ ↓":^36}')
    print(f'{"":>6} │{"LONG":^18}{"SHORT":^18}│{"LONG":^18}{"SHORT":^18}')
    print('─'*7 + '┼' + '─'*36 + '┼' + '─'*36)
    for cn in range(6):
        line = f'  ({cn})  │'
        for cd in (1, -1):
            line += cellf(sel.get((cd, cn, 'LONG')),  bl[0])
            line += cellf(sel.get((cd, cn, 'SHORT')), bs[0])
            if cd == 1: line += '│'
        print(line)

for tf in ('1H', '5m'):
    for layer in ('5/5', '2/2'):
        for stop, tgt in (('колено', '3R'), ('уровень', '3R')):
            show(tf, layer, stop, tgt)
print('\n  Числа — НАДБАВКА точки к слепому входу в ту же сторону, в R на сделку.')
print('  * — надбавка больше двух сигм.  ** — и знак тот же в обеих половинах истории.')
print('  «—» — меньше 25 сделок.')

# ── качество пары «стоп + цель» без сноса рынка ────────────────────
# снос добавляет +d лонгам и -d шортам, поэтому полусумма его убирает.
print('\n\n' + '='*78)
print('КАЧЕСТВО ПАРЫ «СТОП + ЦЕЛЬ», ОЧИЩЕННОЕ ОТ СНОСА  =  (лонг + шорт) / 2')
print('='*78)
acc = collections.defaultdict(list)
for r in G:
    acc[(r['тф'], r['слой'], r['сторона'], r['стоп'], r['цель'])].append(r)
def side_stat(k):
    rs = acc.get(k, [])
    n = sum(x['сделок'] for x in rs)
    if n == 0: return 0.0, 0, 0.0
    m = sum(x['EV'] * x['сделок'] for x in rs) / n
    v = sum((x['шум2s'] / 2) ** 2 * x['сделок'] ** 2 for x in rs if x['сделок'] > 1)
    return m, n, math.sqrt(v) / n * 2
for tf in ('1H', '5m'):
    for layer in ('5/5', '2/2'):
        print(f'\n── {tf} · слой {layer}')
        print(f'{"":10}' + ''.join(f'{t:>20}' for t in ('магнит', '3R', '2R')))
        for stop in ('свеча', 'колено', 'уровень'):
            line = f'{stop:10}'
            for tgt in ('магнит', '3R', '2R'):
                lm, ln, le = side_stat((tf, layer, 'LONG', stop, tgt))
                sm, sn, se = side_stat((tf, layer, 'SHORT', stop, tgt))
                q = (lm + sm) / 2; e = math.sqrt(le**2 + se**2) / 2
                line += f'{ln+sn:>6} {q:+.3f}±{e:.3f}'
            print(line)
print('\n  Это то, что стоп и цель дают САМИ, независимо от того, куда шёл рынок.')
