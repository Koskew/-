# -*- coding: utf-8 -*-
"""Пересчёт всех ключевых замеров на эталонной реплике.

Прошлые цифры считались копиями логики, в которых блок уровня работал
только на новом колене, а уровень воскресал в ПЕРЕХОДЕ и плодил
фантомные сломы. Здесь всё считается из research/core.py, который
воспроизводит экран индикатора строка в строку.
"""
import sys, statistics, bisect
sys.path.insert(0, 'research')
from core import Core, load, pivots, up

rows = load()
AT = pivots(rows)                       # пивоты считаем один раз

def run(**kw):
    co = Core(rows, **kw); co.at = AT
    return co.run()

def med(x): return statistics.median(x) if x else 0

print(f'данные: {len(rows)} баров, {rows[0][0][:10]} — {rows[-1][0][:10]}\n')

# ── 1. фильтр глубины слома ──
print('1. ФИЛЬТР ГЛУБИНЫ СЛОМА  (рывок 0.5, провизорный уровень включён)')
print(f'{"fibDepth":>9} {"сломов":>8} {"медиана жизни":>15}')
for f in (0.0, 0.15, 0.33, 0.5, 0.75):
    co = run(fib=f)
    d = sum(1 for _, e, _ in co.log if e == 'СМЕРТЬ')
    print(f'{f:>9.2f} {d:>8} {med(co.lives):>13.0f}б')

# ── 2. пауза после смерти ──
print('\n2. ПАУЗА ПОСЛЕ СМЕРТИ')
print(f'{"вариант":>22} {"ПЕРЕХОДОВ":>10} {"медиана":>8} {">20б":>6} {"время в":>8} {"жизнь":>7} {"умерли":>8}')
print(f'{"":>22} {"":>10} {"длина":>8} {"":>6} {"переходе":>8} {"тренда":>7} {"за 10б":>8}')
for jp, pv, nm in ((0.0, False, 'только пауза'), (0.5, False, 'рывок 0.5'),
                   (0.5, True, 'рывок 0.5 + провиз'), (1.0, True, 'рывок 1.0 + провиз')):
    co = run(jump=jp, prov=pv)
    sp, li = co.spans, co.lives
    early = sum(1 for x in li if x <= 10) / len(li) if li else 0
    print(f'{nm:>22} {len(sp):>10} {med(sp):>7.0f}б {sum(1 for x in sp if x>20)/len(sp):>5.0%} '
          f'{co.trBars/len(rows):>7.0%} {med(li):>6.0f}б {early:>7.0%}')

# ── 3 и 4. один проход с записью состояния по барам ──
co = Core(rows); co.at = AT
recs = []                               # (бар, запас в импульсах, тренд, счёт)
deaths = []
for b in range(len(rows)):
    before = len(co.log)
    co.step(b)
    for _, e, _ in co.log[before:]:
        if e == 'СМЕРТЬ': deaths.append(b)
    if not co.inTrans and co.tr != 0:
        r = co.room(rows[b][4])
        if r is not None: recs.append((b, r, co.tr, co.cdir()))
ds = sorted(deaths)
def dies(b, hor):
    i = bisect.bisect_right(ds, b)
    return i < len(ds) and ds[i] - b <= hor

print(f'\n3. ЗАПАС ДО ПОРОГА СМЕРТИ  ({len(recs)} баров в живом тренде)')
print(f'{"запас / импульс":>16} {"баров":>7} {"умер за 10 бар":>16}')
for lo_, hi_ in ((0, .25), (.25, .5), (.5, 1.), (1., 2.), (2., 1e9)):
    sel = [x for x in recs if lo_ <= x[1] < hi_]
    if not sel: continue
    lbl = f'{lo_:.2f}–{hi_:.2f}' if hi_ < 1e9 else f'{lo_:.2f} и больше'
    print(f'{lbl:>16} {len(sel):>7} {sum(1 for x in sel if dies(x[0],10))/len(sel):>15.0%}')
print(f'{"в среднем":>16} {len(recs):>7} {sum(1 for x in recs if dies(x[0],10))/len(recs):>15.0%}')

print(f'\n4. РАСХОЖДЕНИЕ ТРЕНДА И СЧЁТА')
print(f'{"":>24} {"баров":>7}' + ''.join(f'{"за "+str(h)+"б":>9}' for h in (5,10,20,40)))
for nm, sel in (('счёт СОГЛАСЕН с трендом', [x for x in recs if x[2] == x[3]]),
                ('счёт ПРОТИВ тренда',      [x for x in recs if x[3] != 0 and x[2] != x[3]]),
                ('все бары',                recs)):
    line = f'{nm:>24} {len(sel):>7}'
    for hor in (5, 10, 20, 40):
        line += f'{sum(1 for x in sel if dies(x[0],hor))/len(sel):>8.0%} ' if sel else f'{"—":>9}'
    print(line)
