"""Сырые частоты по сломам для ВЫГРУЗКА-СЛОМЫ.md, раздел 5.

Его заказ 20.11.2026: «никаких выводов: только описание и сырые частоты».
Движок — как в пайне v3.43: zguard, knee_seq, birth_lvl, cont_touch.
Слой 2/2. Девять лет 1H. Train — бары до 2022-01-01, test — с него.
Ничего не трогает в движке: slom и trace — приборы.
"""
import os, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
import dvizhok2 as D

ALIVE = (D.ST_MAY, D.ST_LIVE)
SEEN = (D.ST_MAY, D.ST_LIVE, D.ST_ARC)   # правило показа режима «оба», пайн строка ~4066
NS = (10, 20, 50)                         # окна Н30

rows = load('data/XAUUSD_1h_9y.csv')
n = len(rows)
SPLIT = next(i for i, r in enumerate(rows) if r[0][:10] >= '2022-01-01')
part = lambda b: 'train' if b < SPLIT else 'test'
KW = dict(zguard=True, knee_seq=True, birth_lvl=True, cont_touch=True, slom=True, trace=True)
up = D.run_all(rows, **KW)
dn = D.run_all(rows, flip=True, **KW)
ev = up['sl_events']
assert ev == dn['sl_events'], 'сломы зеркалом не должны меняться'

print('баров', n, 'с', rows[0][0][:16], 'по', rows[-1][0][:16])
print('train баров', SPLIT, 'до', rows[SPLIT-1][0][:16], '| test баров', n-SPLIT, 'с', rows[SPLIT][0][:16])
print('событий слома', len(ev), 'train', sum(1 for e in ev if e[0] < SPLIT), 'test', sum(1 for e in ev if e[0] >= SPLIT))
print()

def pct(a, b): return '%.1f%%' % (100.0*a/b) if b else 'нет данных'

# ── 5а. серии ──
runs = []   # (start_bar, end_bar, dir, length, closed)
cur = None
for b, d, p in ev:
    if cur and cur[2] == d:
        cur[1] = b; cur[3] += 1
    else:
        if cur: cur[4] = True; runs.append(cur)
        cur = [b, b, d, 1, False]
if cur: runs.append(cur)
BINS = [('1', 1, 1), ('2', 2, 2), ('3', 3, 3), ('4–5', 4, 5), ('6–9', 6, 9), ('10+', 10, 10**9)]
print('5а. СЕРИИ (завершённые; последняя незавершённая — отдельно)')
for pt in ('train', 'test'):
    sel = [r for r in runs if r[4] and part(r[0]) == pt]
    cross = sum(1 for r in sel if part(r[0]) != part(r[1]))
    print(' ', pt, 'серий', len(sel), '| из них начались в одной части, кончились в другой:', cross)
    for nm, a, z in BINS:
        for dd, dnm in ((1, 'вверх'), (-1, 'вниз')):
            k = sum(1 for r in sel if a <= r[3] <= z and r[2] == dd)
            print('     длина %-4s %-6s %5d' % (nm, dnm, k), end='')
        k = sum(1 for r in sel if a <= r[3] <= z)
        print('   всего %5d  %s' % (k, pct(k, len(sel))))
print('  незавершённых серий:', sum(1 for r in runs if not r[4]), 'длина', [r[3] for r in runs if not r[4]])
print()

# ── 5б. два тренда видны ──
su = [t[1] for t in up['trace'][2]]; sd = [t[1] for t in dn['trace'][2]]
def both_stats(okset, lo, hi):
    bars = [i for i in range(lo, hi) if su[i] in okset and sd[i] in okset]
    eps = []; L = 0
    for i in range(lo, hi):
        if su[i] in okset and sd[i] in okset: L += 1
        elif L: eps.append(L); L = 0
    if L: eps.append(L)
    return len(bars), hi-lo, eps
print('5б. ДВА ТРЕНДА ОДНОВРЕМЕННО')
for nm, okset in (('видны по правилу показа (возможен/жив/архив у обоих)', SEEN), ('живы оба (возможен/жив)', ALIVE), ('подтверждены оба (жив)', (D.ST_LIVE,))):
    for pt, lo, hi in (('train', 0, SPLIT), ('test', SPLIT, n)):
        k, tot, eps = both_stats(okset, lo, hi)
        print('  %-55s %-5s баров %6d из %6d = %s | эпизодов %4d, длина средняя %.1f, медиана %s' %
              (nm, pt, k, tot, pct(k, tot), len(eps), (sum(eps)/len(eps)) if eps else 0, st.median(eps) if eps else '—'))
print()

# ── тренды: от рождения до конца ──
def trends(res, d):
    tr = res['trace'][2]; zb = res['sl_zb']; T = res['T'][2]
    out = []; i = 0
    while i < n:
        if tr[i][1] in ALIVE and (i == 0 or tr[i-1][1] not in ALIVE or zb[i][1] != zb[i-1][1]):
            born = zb[i][1]; j = i
            while j + 1 < n and tr[j+1][1] in ALIVE and zb[j+1][1] == born: j += 1
            end = j + 1 if j + 1 < n else None          # бар, на котором тренд перестал быть живым
            recs = [r for r in T.counts if born <= r['born'] < (end if end is not None else n + 1)]  # строго < end: новый тренд может родиться на баре смерти прежнего
            how = recs[-1]['how'] if recs else '?'
            if end is None: how = 'идёт'
            knees = sum(max(r['mx'], 0) for r in recs)
            lo, hi = born + 1, (end if end is not None else n - 1)
            e_in = [e for e in ev if lo <= e[0] <= hi]
            out.append(dict(born=born, end=end, how=how, knees=knees, conts=sum(1 for r in recs if r['how']=='продолжение'),
                            along=sum(1 for e in e_in if e[1] == d), against=sum(1 for e in e_in if e[1] == -d),
                            ev=e_in, recs=recs, d=d))
            i = j + 1
        else:
            i += 1
    return out
TU = trends(up, 1); TD = trends(dn, -1)
def q(v):
    if not v: return 'нет данных'
    v = sorted(v); m = len(v)
    return 'ср %.1f · медиана %s · p25 %s · p75 %s · макс %s' % (sum(v)/m, st.median(v), v[m//4], v[(3*m)//4], v[-1])
print('5в. ТРЕНДЫ ОТ РОЖДЕНИЯ ДО КОНЦА (слом считается, если его бар > бара рождения и <= бара конца)')
for TT, nm in ((TU, 'восходящий'), (TD, 'нисходящий')):
    for pt in ('train', 'test'):
        sel = [t for t in TT if part(t['born']) == pt]
        hows = {}
        for t in sel: hows[t['how']] = hows.get(t['how'], 0) + 1
        print('  %s %s: трендов %d | исходы %s' % (nm, pt, len(sel), hows))
        for grp, gs in (('все', sel), ('без «не было»', [t for t in sel if t['how'] != 'не было'])):
            print('     [%s] n=%d' % (grp, len(gs)))
            print('        сломов по тренду   ', q([t['along'] for t in gs]))
            print('        сломов против      ', q([t['against'] for t in gs]))
            print('        колен (сумма max счёта по всем счётам тренда)', q([t['knees'] for t in gs]))
            print('        баров жизни        ', q([((t['end'] if t['end'] is not None else n-1) - t['born']) for t in gs]))
print()

# ── 5г. встречные серии внутри живого тренда ──
print('5г. ВСТРЕЧНЫЕ СЕРИИ ВНУТРИ ЖИВОГО ТРЕНДА (серия из подряд идущих сломов против тренда; что было дальше)')
for TT, nm in ((TU, 'восходящий'), (TD, 'нисходящий')):
    for pt in ('train', 'test'):
        cnt = {}
        for t in TT:
            if part(t['born']) != pt: continue
            es = t['ev']; d = t['d']; k = 0
            while k < len(es):
                if es[k][1] == -d:
                    m = k
                    while m + 1 < len(es) and es[m+1][1] == -d: m += 1
                    L = m - k + 1
                    if m + 1 < len(es): nxt = 'вернулась по тренду'
                    else: nxt = 'тренд кончился: ' + t['how']
                    key = ('1' if L == 1 else '2' if L == 2 else '3+', nxt)
                    cnt[key] = cnt.get(key, 0) + 1
                    k = m + 1
                else: k += 1
        print('  %s %s:' % (nm, pt))
        for L in ('1', '2', '3+'):
            items = sorted((kk[1], v) for kk, v in cnt.items() if kk[0] == L)
            print('     длина %-3s  всего %4d   %s' % (L, sum(v for _, v in items), '; '.join('%s %d' % x for x in items)))
print()

# ── 5д. базовые доли ──
print('5д. БАЗОВЫЕ ДОЛИ')
for TT, res, nm in ((TU, up, 'восходящий'), (TD, dn, 'нисходящий')):
    recs = res['T'][2].counts
    for pt in ('train', 'test'):
        rs = [r for r in recs if part(r['born']) == pt]
        line = []
        for kpt in range(0, 6):
            # счёт с цифрой kpt: дошёл ли до kpt+1 (для 5 — до продолжения)
            got = [r for r in rs if r['mx'] >= kpt and not (kpt == 0 and r['zl'] == 'LL')]
            if kpt == 0: got = [r for r in rs if r['zl'] == 'HL']      # счёт продолжения начинается с (0)
            if kpt < 5:
                ok = sum(1 for r in got if r['mx'] >= kpt + 1)
                cens = sum(1 for r in got if r['mx'] == kpt and r['how'] == 'идёт')
            else:
                ok = sum(1 for r in got if r['how'] == 'продолжение')
                cens = sum(1 for r in got if r['how'] == 'идёт')
            den = len(got) - cens
            line.append('(%d)→%s %s (n=%d)' % (kpt, '(%d)' % (kpt+1) if kpt < 5 else 'продолж.', pct(ok, den), den))
        print('  %s %s: %s' % (nm, pt, ' · '.join(line)))
    tr = res['trace'][2]
    # смерть за N баров: от каждого живого бара; концом считается «умер» и «не было»
    ends = {}
    for t in TT:
        if t['end'] is not None: ends[t['born']] = (t['end'], t['how'])
    for pt, lo, hi in (('train', 0, SPLIT), ('test', SPLIT, n)):
        out = []
        for N in NS:
            tot = dead = 0
            for t in TT:
                if t['end'] is None: continue
                for b in range(max(t['born'], lo), min(t['end'], hi)):
                    if b + N >= n: continue
                    tot += 1
                    if t['how'] in ('умер', 'не было') and t['end'] - b <= N: dead += 1
            out.append('N=%d: %s (баров-случаев %d)' % (N, pct(dead, tot), tot))
        print('  %s %s — от живого бара умер/отменён за N баров: %s' % (nm, pt, ' · '.join(out)))
        out = []
        for N in NS:
            sel = [t for t in TT if part(t['born']) == pt and t['end'] is not None and t['born'] + N < n]
            dead = sum(1 for t in sel if t['how'] in ('умер', 'не было') and t['end'] - t['born'] <= N)
            out.append('N=%d: %s (n=%d)' % (N, pct(dead, len(sel)), len(sel)))
        print('  %s %s — от рождения умер/отменён за N баров: %s' % (nm, pt, ' · '.join(out)))
