# -*- coding: utf-8 -*-
"""В39 · граница «поровну» и «явный» перевес уровней. Пункт 1 документа
«Сломы: три решения перед пайном». Параметры согласованы 21.11.2026 его
словом «да, бери так» — список в indicator/СЛОМЫ-ВНЕШНИЙ-РАЗБОР.md §6.

  · 1H, девять лет; train до 2022-01-01, test с него;
  · уровни и сломы — бухгалтерия пайна v3.43 через реплику;
  · каждый закрытый бар, где есть оба уровня; контроль — бары слома (Н48);
  · мера = ближнее / дальнее на закрытии бара, корзины по 0.1;
  · исход = сторона СЛЕДУЮЩЕГО слома (первый бар со сломом после этого);
    оба слома на том бару — строка «оба», в долю не входят;
  · ближний сверху и снизу — раздельно;
  · пороги ДО прогона: поровну 45–55% · явный от 65% · слабый между 55 и 65;
    ниже 45 порога нет — пишется «к дальнему»;
  · держится: класс корзины тот же в train и test, граница сдвинулась
    не больше чем на одну корзину;
  · мало данных: меньше 100 разных сломов-исходов в корзине;
    шум 2σ считается по числу сломов, а не баров.

    python3 research/perevess_v39.py
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
import dvizhok2 as D

rows = load('data/XAUUSD_1h_9y.csv')
N = len(rows)
SPLIT = next(i for i, r in enumerate(rows) if r[0][:10] >= '2022-01-01')
res = D.run_all(rows, zguard=True, knee_seq=True, birth_lvl=True,
                cont_touch=True, slom=True)
ev, near = res['sl_events'], res['sl_near']

by_bar = {}
for i, d, p in ev:
    by_bar.setdefault(i, []).append(d)
sl_bars = sorted(by_bar)

# для каждого бара — первый бар со сломом ПОСЛЕ него
nxt = [None] * N
j = len(sl_bars) - 1
cur = None
k = len(sl_bars)
for i in range(N - 1, -1, -1):
    while k > 0 and sl_bars[k - 1] > i:
        k -= 1
        cur = sl_bars[k]
    nxt[i] = cur

def outcome(i):
    b = nxt[i]
    if b is None:
        return None, None
    ds = set(by_bar[b])
    return b, ('оба' if len(ds) == 2 else ds.pop())

def cls(share):
    if share >= 65: return 'явный'
    if share > 55: return 'слабый'
    if share >= 45: return 'поровну'
    return 'к дальнему'

part = lambda i: 'train' if i < SPLIT else 'test'
NB = 10
cell = {}      # (part, side, bucket) -> [bars, to_near, both, set(outcome bars)]
skipped = {'нет пары уровней': 0, 'ровно посередине (сторона не определена)': 0,
           'нет следующего слома': 0}
for i in range(N):
    up, dn = near[i]
    if up is None or dn is None:
        skipped['нет пары уровней'] += 1
        continue
    c = rows[i][4]
    du, dd = up - c, c - dn
    if du <= 0 or dd <= 0:
        skipped['нет пары уровней'] += 1
        continue
    if du == dd:
        skipped['ровно посередине (сторона не определена)'] += 1
        continue
    side = 1 if du < dd else -1
    ratio = min(du, dd) / max(du, dd)
    b = min(int(ratio * NB), NB - 1)
    ob, od = outcome(i)
    if ob is None:
        skipped['нет следующего слома'] += 1
        continue
    key = (part(i), side, b)
    x = cell.setdefault(key, [0, 0, 0, set()])
    if od == 'оба':
        x[2] += 1
        continue
    x[0] += 1
    x[1] += (od == side)
    x[3].add(ob)

print('баров %d · train %d · test %d · событий слома %d' % (N, SPLIT, N - SPLIT, len(ev)))
print('вне замера:', skipped)
print()
SIDE = {1: 'ближний СВЕРХУ', -1: 'ближний СНИЗУ'}
classes = {}
for side in (1, -1):
    for pt in ('train', 'test'):
        print('%s · %s' % (SIDE[side], pt))
        print('   корзина     баров   сломов  к ближнему   2σ      оба    класс')
        for b in range(NB):
            x = cell.get((pt, side, b), [0, 0, 0, set()])
            nb, nn, both, s = x[0], x[1], x[2], len(x[3])
            if nb == 0:
                print('   %.1f–%.1f   %6d   %6d     —' % (b / NB, (b + 1) / NB, nb, s))
                classes[(side, pt, b)] = None
                continue
            sh = 100.0 * nn / nb
            sg = 200.0 * math.sqrt(max(sh / 100 * (1 - sh / 100), 1e-9) / s) if s else 0
            c = cls(sh) if s >= 100 else 'мало данных'
            classes[(side, pt, b)] = c
            print('   %.1f–%.1f   %6d   %6d    %5.1f%%   ±%4.1f   %5d    %s'
                  % (b / NB, (b + 1) / NB, nb, s, sh, sg, both, c))
        print()

# границы: первая корзина (снизу вверх), где класс перестал быть «явный»,
# и первая, где стал «поровну»
def bound(side, pt, test):
    for b in range(NB):
        c = classes.get((side, pt, b))
        if c is not None and test(c):
            return b
    return None

print('ГРАНИЦЫ (номер корзины 0…9, снизу вверх)')
rows_b = []
for side in (1, -1):
    for pt in ('train', 'test'):
        b1 = bound(side, pt, lambda c: c != 'явный' and c != 'мало данных')
        b2 = bound(side, pt, lambda c: c == 'поровну')
        rows_b.append((side, pt, b1, b2))
        f = lambda b: '—' if b is None else '%d (%.1f–%.1f)' % (b, b / NB, (b + 1) / NB)
        print('   %s %-5s  конец «явный»: %-14s  начало «поровну»: %s' % (SIDE[side], pt, f(b1), f(b2)))
print()
same = 0; tot = 0
for side in (1, -1):
    for b in range(NB):
        a, z = classes.get((side, 'train', b)), classes.get((side, 'test', b))
        if a in (None, 'мало данных') or z in (None, 'мало данных'):
            continue
        tot += 1; same += (a == z)
print('классы корзин train = test: %d из %d' % (same, tot))
for idx, nm in ((2, 'конец «явный»'), (3, 'начало «поровну»')):
    vals = [r[idx] for r in rows_b]
    if None in vals:
        print('   %s: у части клеток границы нет — %s' % (nm, vals))
    else:
        print('   %s: от %d до %d, размах %d корзин(ы) — %s'
              % (nm, min(vals), max(vals), max(vals) - min(vals),
                 'держится (≤1)' if max(vals) - min(vals) <= 1 else 'НЕ держится (>1)'))
print()

# КОНТРОЛЬ: бары слома, метод Н48 буква в букву (исход — первый слом
# следующего бара со сломом, вверх раньше вниз), r = до верхнего / до нижнего
up_n = up_s = dn_n = dn_s = 0
for i in sl_bars:
    u, d = near[i]
    if u is None or d is None:
        continue
    c = rows[i][4]; du, dd = u - c, c - d
    if du <= 0 or dd <= 0:
        continue
    ob = nxt[i]
    if ob is None:
        continue
    first = by_bar[ob][0]
    r = du / dd
    if r < 0.5:
        up_n += 1; up_s += first > 0
    elif r > 2:
        dn_n += 1; dn_s += first > 0
print('КОНТРОЛЬ Н48 (бары слома): доля следующего слома ВВЕРХ')
print('   вверх намного ближе r<0.5 : %.1f%% (n=%d)   [Н48: 72.8%%]' % (100.0 * up_s / up_n, up_n))
print('   вниз намного ближе r>2    : %.1f%% (n=%d)   [Н48: 31.1%%]' % (100.0 * dn_s / dn_n, dn_n))
