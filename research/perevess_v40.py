# -*- coding: utf-8 -*-
"""В40 · сетка «перевес × серия». Задание владельца 21.11.2026, параметры
его словами (НАБЛЮДЕНИЯ.md Н65). Всё как в В39 (perevess_v39.py):
1H, 9 лет, train до 2022-01-01 / test после, реплика v3.43, каждый
закрытый бар с парой уровней, исход = сторона следующего слома, «оба» вне
доли, 2σ по числу сломов, меньше 100 сломов-исходов = «мало данных».

Новое:
  · перевес по границам Н64: явный < 0.3 · слабый 0.3–0.8 · поровну ≥ 0.8;
  · серия на закрытии бара: согласна (сторона серии = сторона ближнего)
    или спорит; бары без серии — вне замера;
  · клетки: перевес × серия × сторона ближнего × train/test;
  · цвет ДО прогона: к ближнему ≥ 65% → «за ближний»; к дальнему ≥ 65% →
    «за дальний»; иначе «серый». Держится — цвет одинаковый в train и test.

    python3 research/perevess_v40.py
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


part = lambda i: 'train' if i < SPLIT else 'test'

# сторона серии на закрытии бара: последний слом до бара включительно
# (на баре с двумя сломами — записанный вторым, вниз, как в пайне)
ser = [0] * N
cur = 0
for i in range(N):
    if i in by_bar:
        cur = by_bar[i][-1]
    ser[i] = cur

def per(r):
    return 'явный' if r < 0.3 else ('поровну' if r >= 0.8 else 'слабый')

def color(sh):
    if sh >= 65: return 'за ближний'
    if 100 - sh >= 65: return 'за дальний'
    return 'серый'

cell = {}
skip = {'нет пары уровней': 0, 'ровно посередине': 0, 'нет серии': 0,
        'нет следующего слома': 0}
for i in range(N):
    up, dn = near[i]
    if up is None or dn is None:
        skip['нет пары уровней'] += 1; continue
    c = rows[i][4]; du, dd = up - c, c - dn
    if du <= 0 or dd <= 0:
        skip['нет пары уровней'] += 1; continue
    if du == dd:
        skip['ровно посередине'] += 1; continue
    if ser[i] == 0:
        skip['нет серии'] += 1; continue
    side = 1 if du < dd else -1
    pv = per(min(du, dd) / max(du, dd))
    sr = 'согласна' if ser[i] == side else 'спорит'
    ob, od = outcome(i)
    if ob is None:
        skip['нет следующего слома'] += 1; continue
    x = cell.setdefault((pv, sr, side, part(i)), [0, 0, 0, set()])
    if od == 'оба':
        x[2] += 1; continue
    x[0] += 1; x[1] += (od == side); x[3].add(ob)

print('баров %d · train %d · test %d · событий слома %d' % (N, SPLIT, N - SPLIT, len(ev)))
print('вне замера:', skip)
print()
COLS = [(1, 'train'), (1, 'test'), (-1, 'train'), (-1, 'test')]
CN = {1: 'ближний сверху', -1: 'ближний снизу'}
col = {}
for pv in ('явный', 'слабый', 'поровну'):
    for sr in ('согласна', 'спорит'):
        print('%s · серия %s' % (pv.upper(), sr))
        for side, pt in COLS:
            x = cell.get((pv, sr, side, pt), [0, 0, 0, set()])
            nb, nn, both, s = x[0], x[1], x[2], len(x[3])
            if nb == 0:
                print('   %-15s %-5s  нет баров' % (CN[side], pt)); col[(pv, sr, side, pt)] = None; continue
            sh = 100.0 * nn / nb
            sg = 200.0 * math.sqrt(max(sh / 100 * (1 - sh / 100), 1e-9) / s) if s else 0
            cl = color(sh) if s >= 100 else 'мало данных'
            col[(pv, sr, side, pt)] = cl
            print('   %-15s %-5s  баров %5d  сломов %5d  к ближнему %5.1f%%  ±%4.1f  оба %3d  → %s'
                  % (CN[side], pt, nb, s, sh, sg, both, cl))
        print()
print('ЦВЕТ РАЗОШЁЛСЯ МЕЖДУ TRAIN И TEST:')
bad = 0
for pv in ('явный', 'слабый', 'поровну'):
    for sr in ('согласна', 'спорит'):
        for side in (1, -1):
            a, z = col.get((pv, sr, side, 'train')), col.get((pv, sr, side, 'test'))
            if a != z:
                bad += 1
                print('   %s · серия %s · %s: train %s, test %s' % (pv, sr, CN[side], a, z))
print('   итого %d из 12' % bad if bad else '   нет — все 12 держатся')
