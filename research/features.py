# -*- coding: utf-8 -*-
"""Признаки: три примера, разобранных до измеримого условия.

Для каждой триггерной свечи записываем состояние контекста и исход
сделки в обе стороны при RR=2. Дальше любой признак — это просто
фильтр по записанному состоянию.
"""
import sys, statistics as st
sys.path.insert(0, 'research')
from core import Core, load
from library import pivots_n
from trigger_base import is_trig, outcome

rows = load()
AT5, AT2 = pivots_n(rows, 5), pivots_n(rows, 2)
c5 = Core(rows, fib=0.33); c5.at = AT5
c2 = Core(rows, fib=0.15); c2.at = AT2

REC = []
for b in range(len(rows)):
    c5.step(b); c2.step(b)
    if is_trig(rows[b]) < 0: continue
    t5 = 0 if c5.inTrans else c5.tr
    t2 = 0 if c2.inTrans else c2.tr
    r5 = c5.room(rows[b][4])
    cn5 = c5.KN[-1] if c5.KN else -1
    cd5 = c5.cdir()
    ol = outcome(b, 1, 2); os_ = outcome(b, -1, 2)
    if ol is None or os_ is None: continue
    REC.append(dict(b=b, t5=t5, t2=t2, r5=r5, cn5=cn5, cd5=cd5, long=ol, short=os_))

print(f'триггерных свечей с полным контекстом: {len(REC)}\n')

def ev(sel, side):
    v = [r[side] for r in sel]
    return (st.mean(v), len(v)) if v else (0, 0)

print('НОЛЬ — все триггерные свечи, RR=2')
for side, nm in (('long','лонг'), ('short','шорт')):
    e, n = ev(REC, side)
    print(f'  {nm:>5}  {n:>5} сделок  {e:>+6.2f}R')

print('\nПРИЗНАК А — свеча в направлении тренда 5/5')
for d, side, nm in ((1,'long','лонг при восходящем 5/5'), (-1,'short','шорт при нисходящем 5/5')):
    sel = [r for r in REC if r['t5'] == d]
    e, n = ev(sel, side)
    print(f'  {nm:<28} {n:>5} сделок  {e:>+6.2f}R')
for d, side, nm in ((-1,'long','лонг ПРОТИВ тренда 5/5'), (1,'short','шорт ПРОТИВ тренда 5/5')):
    sel = [r for r in REC if r['t5'] == d]
    e, n = ev(sel, side)
    print(f'  {nm:<28} {n:>5} сделок  {e:>+6.2f}R')

print('\nПРИЗНАК Б — запас тренда 5/5 в момент свечи')
for lo, hi, nm in ((0,.5,'меньше 0.5 импульса'), (.5,1.,'0.5–1.0'), (1.,99,'больше 1.0')):
    for d, side, sn in ((1,'long','лонг'), (-1,'short','шорт')):
        sel = [r for r in REC if r['t5'] == d and r['r5'] is not None and lo <= r['r5'] < hi]
        e, n = ev(sel, side)
        if n < 20: continue
        print(f'  {nm:<22} {sn:>5} по тренду  {n:>5} сделок  {e:>+6.2f}R')

print('\nПРИЗНАК В — на какой точке счёта 5/5 стоит свеча')
for lo, hi, nm in ((0,1,'(0) начало'), (1,2,'(1) импульс'), (2,3,'(2) коррекция'),
                   (3,4,'(3) импульс'), (4,5,'(4) коррекция'), (5,9,'(5) импульс')):
    sel = [r for r in REC if lo <= r['cn5'] < hi and r['cd5'] != 0]
    if len(sel) < 20: continue
    up_ = [r for r in sel if r['cd5'] == 1]
    dn_ = [r for r in sel if r['cd5'] == -1]
    eu, nu = ev(up_, 'long'); ed, nd = ev(dn_, 'short')
    print(f'  {nm:<16} по счёту вверх {nu:>4} шт {eu:>+6.2f}R   |   по счёту вниз {nd:>4} шт {ed:>+6.2f}R')
