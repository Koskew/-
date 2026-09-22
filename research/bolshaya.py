# -*- coding: utf-8 -*-
"""Н12: как часто большая свеча вырезает коррекцию.

Вопрос владельца 22.09.2026 после разбора 12 января 2026 на слое 2/2:
счёт дошёл до (5) HH 4601.695, дальше коррекция, а слой поставил низ
только через 12 баров и на 16.55 пункта выше настоящего дна. Причина —
минимум ТОЙ ЖЕ большой свечи, что дала вершину, оказался глубже всей
коррекции и закрыл окно пивота.

СЛУЧАЙ = нога вниз слоя (колено-вершина -> колено-низ), у которой
реальный минимум внутри промежутка НИЖЕ, чем цена поставленного колена.
Окно берётся СТРОГО ПОСЛЕ бара вершины: минимум на самой свече вершины
к коррекции не относится (12 янв он был на 4536.53 ещё до того, как
свеча ушла вверх на 4601.695).

Порогов нет нигде. Выкладывается распределение целиком, «большая свеча»
отдельным порогом НЕ определяется — вместо этого по каждому случаю
пишется, кто именно помешал настоящему дну стать пивотом и какой у той
свечи размах в медианах. Любой порог навешивается потом на CSV, без
перезапуска.

Пивот считается ровно теми сравнениями, что в research/core.py:
слева >=, справа >. core.pivots зашит на глубину 5, здесь она нужна
параметром, поэтому тот же код повторён с d вместо L/R.

    python3 research/bolshaya.py
"""
import csv, os, statistics as st
from core import load

OUT = 'research/out/bolshaya_9y.csv'


def pivots_d(rows, d):
    """core.pivots с глубиной d. Ключ — бар подтверждения (i + d)."""
    hi = [r[2] for r in rows]
    lo = [r[3] for r in rows]
    at = {}
    for i in range(d, len(rows) - d):
        if all(hi[i-k] <= hi[i] for k in range(1, d+1)) and all(hi[i+k] < hi[i] for k in range(1, d+1)):
            at.setdefault(i + d, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, d+1)) and all(lo[i+k] > lo[i] for k in range(1, d+1)):
            at.setdefault(i + d, []).append((i, lo[i], False))
    return at


def knees(rows, d):
    """f_push из metki_prosto.pine: подряд идущие одной стороны
    схлопываются в свой экстремум, колено переезжает на новый бар."""
    at = pivots_d(rows, d)
    P, B, H = [], [], []
    for i in range(len(rows)):
        for bar, price, isHi in at.get(i, []):
            if P and H[-1] == isHi:
                better = price > P[-1] if isHi else price < P[-1]
                if better:
                    P[-1] = price
                    B[-1] = bar
            else:
                P.append(price)
                B.append(bar)
                H.append(isHi)
    return P, B, H


def blockers(rows, m, d):
    """Почему бар m не стал пивот-низом: кто из соседей мешает.
    Слева мешает более низкий, справа — более низкий ИЛИ равный."""
    lo = [r[3] for r in rows]
    out = []
    for k in range(1, d+1):
        if m-k >= 0 and lo[m-k] < lo[m]:
            out.append(m-k)
        if m+k < len(rows) and lo[m+k] <= lo[m]:
            out.append(m+k)
    return out


def q(v):
    if not v:
        return '—'
    v = sorted(v)
    f = lambda p: v[min(len(v)-1, int(p*len(v)))]
    return 'мин %.2f  25%% %.2f  мед %.2f  75%% %.2f  90%% %.2f  макс %.2f' % (
        v[0], f(.25), f(.50), f(.75), f(.90), v[-1])


rows = load('data/XAUUSD_1h_9y.csv')
rng = [r[2] - r[3] for r in rows]
medRng = st.median(rng)
print('баров: %d   с %s по %s   медианный размах свечи %.3f'
      % (len(rows), rows[0][0][:10], rows[-1][0][:10], medRng))

os.makedirs('research/out', exist_ok=True)
fh = open(OUT, 'w', newline='', encoding='utf-8')
w = csv.writer(fh)
w.writerow(['слой', 'время вершины', 'цена вершины', 'время колена-низа', 'цена колена-низа',
            'время настоящего дна', 'цена настоящего дна', 'глубина пунктов', 'глубина в импульсах',
            'баров раньше', 'баров без колена', 'кто помешал', 'размах помехи в медианах'])

for d, nm in ((5, '5/5'), (3, '3/3'), (2, '2/2')):
    P, B, H = knees(rows, d)
    legs = 0
    cases = []
    for i in range(1, len(P)):
        if not (H[i-1] and not H[i]):
            continue                      # нужна нога вниз: вершина -> низ
        legs += 1
        b1, b2 = B[i-1], B[i]
        if b2 <= b1:
            continue
        seg = range(b1 + 1, b2 + 1)       # строго после свечи вершины
        m = min(seg, key=lambda x: rows[x][3])
        real = rows[m][3]
        if real >= P[i]:
            continue                      # колено стоит на самом дне
        imp = abs(P[i-1] - P[i-2]) if i >= 2 else 0.0
        bl = blockers(rows, m, d)
        if not bl:
            kind = 'никто (слияние)'
            bigg = 0.0
        else:
            deep = min(bl, key=lambda x: rows[x][3])
            bigg = (rows[deep][2] - rows[deep][3]) / medRng
            if deep == b1:
                kind = 'свеча вершины'
            elif deep < m:
                kind = 'другая слева'
            else:
                kind = 'справа'
        cases.append(dict(dep=P[i] - real, depI=(P[i] - real) / imp if imp else None,
                          early=b2 - m, gap=b2 - b1, kind=kind, big=bigg))
        w.writerow([nm, rows[b1][0][:16], '%.3f' % P[i-1], rows[b2][0][:16], '%.3f' % P[i],
                    rows[m][0][:16], '%.3f' % real, '%.3f' % (P[i] - real),
                    '%.3f' % ((P[i] - real) / imp) if imp else '', b2 - m, b2 - b1, kind, '%.2f' % bigg])

    print('\n' + '=' * 78)
    print('СЛОЙ %s   ног вниз всего %d   из них с перепрыгнутым дном %d  (%.1f%%)'
          % (nm, legs, len(cases), 100.0 * len(cases) / max(legs, 1)))
    print('  глубина, пунктов      ', q([c['dep'] for c in cases]))
    print('  глубина, в импульсах  ', q([c['depI'] for c in cases if c['depI'] is not None]))
    print('  дно было раньше, баров', q([float(c['early']) for c in cases]))
    print('  слой без колена, баров', q([float(c['gap']) for c in cases]))
    print('  кто помешал настоящему дну:')
    kinds = {}
    for c in cases:
        kinds[c['kind']] = kinds.get(c['kind'], 0) + 1
    for k in sorted(kinds, key=lambda x: -kinds[x]):
        sub = [c for c in cases if c['kind'] == k]
        bigs = sorted(c['big'] for c in sub)
        med = bigs[len(bigs)//2] if bigs else 0
        print('    %-16s %5d  (%4.1f%%)   размах помехи, медиана %.2f медианы свечи'
              % (k, kinds[k], 100.0*kinds[k]/len(cases), med))
    print('  размах помехи в медианах', q([c['big'] for c in cases if c['big'] > 0]))

fh.close()
print('\nпострочно: ' + OUT)
