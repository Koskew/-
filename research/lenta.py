# -*- coding: utf-8 -*-
"""Лента колен: каждое колено подряд, без единого сброса счёта.

Никаких правил тренда, смерти, уровня и запаса — только то, что реально
произошло на графике. Правила будем искать в этих данных, поэтому в них
самих правил быть не должно.

Колено записывается, когда оно ОКОНЧАТЕЛЬНО закрыто — то есть когда
началось следующее. До этого момента цена колена ещё может переписаться:
серия меток одной стороны схлопывается в свой экстремум.

  бар          — бар самого экстремума
  время        — время этого бара
  цена колена  — экстремум
  цена сейчас  — close бара, на котором пивот стал виден (бар + глубина)
  нога         — |цена колена − цена предыдущего колена|
  мутность     — сколько сырых меток слилось в это колено

CSV с разделителем «;» и запятой в дробях — открывается в Excel как есть.
"""
import sys, csv, os, statistics as st, collections
sys.path.insert(0, 'research')
from core import Core

OUT = 'research/out/lenta'
os.makedirs(OUT, exist_ok=True)

FILES = [('2y', 'data/XAUUSD_1h_2y.csv'), ('9y', 'data/XAUUSD_1h_9y.csv')]
LAYERS = [5, 3, 2]

# эталонная последовательность подписей, восходящая и её зеркало
ET_UP = ["LL", "LH", "HL", "HH", "HL", "HH"]
ET_DN = ["HH", "HL", "LH", "LL", "LH", "LL"]

def load(p):
    out = []
    for r in csv.DictReader(open(p, encoding='utf-8-sig')):
        o, h, l, c = float(r['open']), float(r['high']), float(r['low']), float(r['close'])
        c = min(max(c, l), h)          # десять свечей округлены на полутик
        o = min(max(o, l), h)
        out.append((r['time'], o, h, l, c))
    return out

def pivots_n(rows, N):
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
    for i in range(N, len(rows) - N):
        if all(hi[i-k] <= hi[i] for k in range(1, N+1)) and all(hi[i+k] < hi[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, N+1)) and all(lo[i+k] > lo[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, lo[i], False))
    return at

def num(x, nd=3):
    """число для русского Excel: запятая в дробной части"""
    return f'{x:.{nd}f}'.replace('.', ',')

def lenta(rows, N):
    """Все закрытые колена по порядку.

    Колено считается закрытым, когда создано следующее. Ведём счётчик
    созданных колен: на одном баре могут подтвердиться и вершина, и низ,
    тогда за шаг создаются два — прежняя версия одно из них теряла.
    Массив колен обрезается сверху на 80, поэтому номер создания
    переводим в индекс массива через сдвиг.
    """
    at = pivots_n(rows, N)
    co = Core(rows, fib=0.33); co.at = at
    out = []
    created = 0          # сколько колен создано за всю историю
    emitted = 0          # сколько уже выписано
    for b in range(len(rows)):
        # считаем, сколько новых колен создаст этот бар: метка той же
        # стороны, что последнее колено, сливается и нового не создаёт
        side = co.KH[-1] if co.KP else None
        for (_bar, _p, isHi) in at.get(b, []):
            if side is None or isHi != side:
                created += 1
            side = isHi
        co.step(b)
        shift = created - len(co.KP)          # номер создания первого в массиве
        while emitted < created - 1:          # последнее колено ещё живое
            i = emitted - shift
            if i < 0:                         # выпало из массива, восстановить нельзя
                emitted += 1
                continue
            bb = co.KB[i]
            conf = min(bb + N, len(rows) - 1)
            out.append(dict(bar=bb, time=rows[bb][0], lab=co.KL[i], hi=co.KH[i],
                            price=co.KP[i], now=rows[conf][4], mud=co.KM[i]))
            emitted += 1
    for i, r in enumerate(out):
        r['n'] = i
        r['leg'] = abs(r['price'] - out[i-1]['price']) if i else 0.0
        r['gap'] = r['bar'] - out[i-1]['bar'] if i else 0
    return out

def count_pattern(labels, pat):
    n = 0
    for i in range(len(labels) - len(pat) + 1):
        if labels[i:i+len(pat)] == pat: n += 1
    return n

summary = []
for tag, path in FILES:
    rows = load(path)
    print(f'\n{"="*78}\n{tag}: {len(rows)} баров, {rows[0][0][:10]} — {rows[-1][0][:10]}')
    for N in LAYERS:
        L = lenta(rows, N)
        name = f'{OUT}/lenta_{tag}_{N}-{N}.csv'
        with open(name, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(['слой','№','время','бар','подпись','сторона',
                        'цена колена','цена сейчас','нога','баров от предыдущего','мутность'])
            for r in L:
                w.writerow([f'{N}/{N}', r['n'], r['time'][:19], r['bar'], r['lab'],
                            'верх' if r['hi'] else 'низ',
                            num(r['price']), num(r['now']), num(r['leg']), r['gap'], r['mud']])
        labs = [r['lab'] for r in L]
        cnt = collections.Counter(labs)
        legs = [r['leg'] for r in L[1:]]
        gaps = [r['gap'] for r in L[1:]]
        mud = sum(1 for r in L if r['mud'] >= 2)
        eu = count_pattern(labs, ET_UP); ed = count_pattern(labs, ET_DN)
        summary.append(dict(tag=tag, N=N, n=len(L), cnt=cnt,
                            leg=st.median(legs) if legs else 0,
                            gap=st.median(gaps) if gaps else 0,
                            mud=mud/max(len(L),1)*100, eu=eu, ed=ed, file=name))
        print(f'  {N}/{N}: колен {len(L):>6} | '
              f'HH {cnt["HH"]:>5} LH {cnt["LH"]:>5} HL {cnt["HL"]:>5} LL {cnt["LL"]:>5} '
              f'? {cnt["?"]:>2} | медиана ноги {st.median(legs):>7.2f} | '
              f'медиана баров {st.median(gaps):>4.0f} | мутных {mud/len(L)*100:>4.1f}% | '
              f'эталон ↑{eu} ↓{ed}  -> {name}')

with open(f'{OUT}/сводка.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['файл','слой','колен','HH','LH','HL','LL','без подписи',
                'медиана ноги','медиана баров между коленами','мутных %',
                'эталон вверх','эталон вниз'])
    for s in summary:
        w.writerow([s['tag'], f'{s["N"]}/{s["N"]}', s['n'], s['cnt']['HH'], s['cnt']['LH'],
                    s['cnt']['HL'], s['cnt']['LL'], s['cnt']['?'],
                    num(s['leg'],2), num(s['gap'],0), num(s['mud'],1), s['eu'], s['ed']])
print(f'\nсводка -> {OUT}/сводка.csv')
