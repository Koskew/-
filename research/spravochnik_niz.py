# -*- coding: utf-8 -*-
"""Справочник последовательностей для НИСХОДЯЩЕГО — переписью, тем же
методом, каким считался восходящий.

МЕТОД. От КАЖДОГО колена-низа берём следующие пять колен и записываем
подписи. Никаких правил тренда: это перепись, а не движок. Ноль пишется
первым и делит выборку надвое — LL значит рождение, HL продолжение.

Нисходящий считается тем же кодом на ПЕРЕВЁРНУТЫХ свечах (идея
владельца 22.09.2026), после чего подписи переводятся обратно:
LL->HH, HL->LH. Отдельного набора правил не существует.

Восходящий пересчитывается заново, чтобы сверить метод с числами,
которые уже вморожены в индикатор (PFR в metki_prosto.pine).

ВОСЕМЬ ЧИСТЫХ ФОРМ. У восходящего низы всегда HL, иначе это не
восходящий, поэтому свободны только вершины и вариантов ровно восемь.
У нисходящего зеркально: вершины всегда LH, свободны низы.

    python3 research/spravochnik_niz.py
"""
import csv, os
from collections import Counter
from core import load

src = open('research/zerkalo.py').read().split(chr(114) + 'ows = load(')[0]
exec(src)

OUT = 'research/out/spravochnik_niz.csv'
SW = {'LL': 'HH', 'HL': 'LH', 'HH': 'LL', 'LH': 'HL', '?': '?'}
# порядок восьми форм — как в PAT индикатора, чтобы числа сверялись строка в строку
PAT_UP = ['LH·HL·HH·HL·HH', 'LH·HL·HH·HL·LH', 'HH·HL·HH·HL·HH', 'HH·HL·HH·HL·LH',
          'HH·HL·LH·HL·HH', 'LH·HL·LH·HL·HH', 'HH·HL·LH·HL·LH', 'LH·HL·LH·HL·LH']
PNM_UP = ['П1', 'П5', 'П6', 'П12', 'П16', 'П20', 'П25', 'П29']
# то, что стоит в индикаторе: [рождения 5/5,3/3,2/2, продолжения 5/5,3/3,2/2]
PFR_IND = [99, 74, 58, 44, 30, 28, 13, 2,  134, 95, 97, 65, 69, 39, 31, 12,
           187, 114, 127, 104, 94, 63, 37, 26,  9, 3, 16, 18, 8, 0, 5, 0,
           10, 9, 23, 20, 17, 2, 5, 1,  14, 10, 35, 22, 18, 3, 4, 1]


def perepis(rows, d, flip=False):
    """Все колена слоя разом, без обрезки массива: это перепись, а не движок.
    rows — ВСЕГДА настоящие свечи; flip=True считает нисходящий. Порядок
    событий внутри бара берётся из events() — см. ошибку 23.09.2026."""
    at = events(rows, d, flip)
    P, B, H, L = [], [], [], []

    def relabel():
        L.clear()
        for i in range(len(P)):
            prev = None
            for j in range(i - 1, -1, -1):
                if H[j] == H[i]:
                    prev = P[j]
                    break
            L.append('?' if prev is None else
                     ('HH' if P[i] > prev else 'LH') if H[i] else
                     ('HL' if P[i] > prev else 'LL'))

    for i in range(len(rows)):
        for bar, price, isHi in at.get(i, []):
            if P and H[-1] == isHi:
                if (price > P[-1]) if isHi else (price < P[-1]):
                    P[-1] = price
                    B[-1] = bar
            else:
                P.append(price); B.append(bar); H.append(isHi)
    relabel()
    out = []
    for i in range(len(P)):
        if H[i]:
            continue                       # стартуем только с НИЗА
        if i + 5 >= len(P):
            break
        out.append((L[i], tuple(L[i+1:i+6])))
    return out


rows = load('data/XAUUSD_1h_9y.csv')
flip = [(r[0], -r[1], -r[3], -r[2], -r[4]) for r in rows]
print('баров %d   с %s по %s\n' % (len(rows), rows[0][0][:10], rows[-1][0][:10]))

data = {}
for d, nm in ((5, '5/5'), (3, '3/3'), (2, '2/2')):
    data[(nm, 'восходящий')] = perepis(rows, d)
    data[(nm, 'нисходящий')] = [(SW[z], tuple(SW[x] for x in s))
                                for z, s in perepis(rows, d, True)]

os.makedirs('research/out', exist_ok=True)
fh = open(OUT, 'w', newline='', encoding='utf-8')
w = csv.writer(fh)
w.writerow(['направление', 'номер', 'последовательность', 'слой', 'вид', 'сколько раз'])

PAT_DN = ['·'.join(SW[x] for x in p.split('·')) for p in PAT_UP]

for dirn, pats, zb, zc in (('восходящий', PAT_UP, 'LL', 'HL'),
                           ('нисходящий', PAT_DN, 'HH', 'LH')):
    print('=' * 92)
    print('%s   ноль рождения %s, ноль продолжения %s' % (dirn.upper(), zb, zc))
    tot = {}
    for nm in ('5/5', '3/3', '2/2'):
        raw = data[(nm, dirn)]
        for kind, zlab in (('рождение', zb), ('продолжение', zc)):
            tot[(nm, kind)] = Counter(s for z, s in raw if z == zlab)
        print('  слой %s: стартов с %s — %d, с %s — %d, разных форм всего %d'
              % (nm, zb, sum(tot[(nm, 'рождение')].values()),
                 zc, sum(tot[(nm, 'продолжение')].values()),
                 len(set(s for z, s in raw))))
    print()
    print('  %-4s %-18s %18s %20s' % ('', '', 'РОЖДЕНИЕ 5/5·3/3·2/2', 'ПРОДОЛЖЕНИЕ 5/5·3/3·2/2'))
    got = []
    for idx, ps in enumerate(pats):
        t = tuple(ps.split('·'))
        r = [tot[(nm, 'рождение')][t] for nm in ('5/5', '3/3', '2/2')]
        p = [tot[(nm, 'продолжение')][t] for nm in ('5/5', '3/3', '2/2')]
        got += r + p
        print('  %-4s %-18s %5d %5d %5d   %7d %5d %5d   всего %4d'
              % (PNM_UP[idx] if dirn == 'восходящий' else '?', ps,
                 r[0], r[1], r[2], p[0], p[1], p[2], sum(r) + sum(p)))
        for j, nm in enumerate(('5/5', '3/3', '2/2')):
            w.writerow([dirn, PNM_UP[idx] if dirn == 'восходящий' else '?', ps, nm, 'рождение', r[j]])
            w.writerow([dirn, PNM_UP[idx] if dirn == 'восходящий' else '?', ps, nm, 'продолжение', p[j]])
    if dirn == 'восходящий':
        mine = []
        for grp in range(6):
            nm = ('5/5', '3/3', '2/2')[grp % 3]
            kind = 'рождение' if grp < 3 else 'продолжение'
            mine += [tot[(nm, kind)][tuple(ps.split('·'))] for ps in pats]
        ok = sum(1 for a, b in zip(mine, PFR_IND) if a == b)
        print('\n  СВЕРКА С ИНДИКАТОРОМ: совпало %d из %d клеток' % (ok, len(PFR_IND)))
        if ok != len(PFR_IND):
            for i, (a, b) in enumerate(zip(mine, PFR_IND)):
                if a != b:
                    print('     клетка %2d: в индикаторе %4d, пересчёт %4d' % (i, b, a))
    print()
fh.close()
print('построчно: ' + OUT)
