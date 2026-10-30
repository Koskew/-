#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Н41 НА ДВИЖКЕ v3.33 — слом против смерти, СЧИТАНО ВРОЗЬ.

Заказан владельцем 30.10.2026, его слово: «да, считай врозь».

ЗАЧЕМ. Н41 утверждала: «слом рубит ТЕНЬ, смерть — ТЕЛО, поэтому когда
слом стоит ВЫШЕ порога, конец тренда первым — 0.0%, и это не округление,
а ноль случаев». Вывод стоял на том, что смерть тенью не рубит.

В v3.33 (замечание З50) появилась СМЕРТЬ ПО ТЕНИ: касание нуля
ПРОДОЛЖЕНИЯ. Значит у довода пропала опора, и число надо считать заново.

ДВЕ ПРАВКИ ПРОТИВ `porjadok.py`, обе вынужденные:

1. `cont_touch=True`;
2. **ступень.** `porjadok.py` берёт строгую ступень только при `on_zero`
   — это ноль РОЖДЕНИЯ. У нуля ПРОДОЛЖЕНИЯ своя пометка `cont_zero`, и
   при `cont_touch` он тоже рубится касанием, то есть порог стоит на
   самом уровне, а не на `уровень − 0.20 × колено`. Без этой правки
   замер сравнивал бы слом с порогом, которого в v3.33 нет. Ровно эту
   болезнь чинила и v3.33 в табло — «сведено к одному источнику
   ступени, иначе строка „запас" завысила бы число на 0.20 колена».

ВРОЗЬ. Исход «конец тренда» разделён на смерть ПО ТЕЛУ и смерть ПО
ТЕНИ. Складывать их нельзя: это две разные механики.

    python3 research/n41_33.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dvizhok2 as D
from core import load

ROOT = os.path.dirname(HERE)
DEPTH = 0.20
MINTICK = 0.001
LAY = 2
LIV = {D.ST_MAY, D.ST_LIVE}
ENDS = {D.ST_DEAD, D.ST_CAN, D.ST_ARC}

DATA = (('data/XAUUSD_1h_9y.csv', 'ЧАСОВИК, девять лет'),
        ('data/XAUUSD_1h_2y.csv', 'ЧАСОВИК, два года'),
        ('data/XAUUSD_5m.csv',    'ПЯТИМИНУТКА'))


def progon(rows, dn_side, ct):
    res = D.run_all(rows, flip=dn_side, zguard=True, knee_seq=True,
                    birth_lvl=True, cont_touch=ct, trace=True, slom=True)
    tr = res['trace'][LAY]
    cz = res['trace_cz'][LAY]
    near = res['sl_near']
    legs = res['sl_leg']
    # бар конца -> каким был конец
    kind = {}
    for c in res['T'][LAY].counts:
        if c['how'] == 'умер':
            kind[c['end']] = 'тень' if (c.get('cdie') and not c.get('bdie')) \
                             else 'тело'
    return tr, cz, near, legs, kind


def schitat(rows, dn_side, ct):
    tr, cz, near, legs, kind = progon(rows, dn_side, ct)
    sg = -1.0 if dn_side else 1.0
    cases, cur, shown = [], None, None

    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        lvl, stt, onz = tr[i]
        czi = cz[i]
        up, dn = near[i]
        leg = legs[i]

        if shown is not None:
            p_lvl, p_slovo = shown
            slom = (l <= p_lvl) if not dn_side else (h >= p_lvl)
            kon = stt in ENDS
            if cur is None:
                cur = {'слово': p_slovo}
            if slom or kon:
                if slom and kon:
                    ish = 'оба на одной свече'
                elif slom:
                    ish = 'слом'
                else:
                    ish = 'конец ' + kind.get(i, 'иначе')
                cur['исход'] = ish
                cases.append(cur)
                cur = None

        alive = stt in LIV and lvl is not None
        if not alive:
            if cur is not None:
                cur['исход'] = 'кончился иначе'
                cases.append(cur)
                cur = None
            shown = None
            continue

        lvl = sg * lvl
        bar_lvl = dn if not dn_side else up
        # ── ТА САМАЯ ПРАВКА: ноль продолжения тоже строгий ──
        strog = onz or (ct and czi)
        thr = lvl if strog else (lvl - DEPTH * leg if not dn_side
                                 else lvl + DEPTH * leg)
        if bar_lvl is None:
            if cur is not None:
                cur['исход'] = 'уровень исчез'
                cases.append(cur)
                cur = None
            shown = None
            continue

        if abs(bar_lvl - thr) <= MINTICK:
            slovo = 'совпали'
        elif (bar_lvl > thr) if not dn_side else (bar_lvl < thr):
            slovo = 'слом раньше'
        else:
            slovo = 'слом позже'
        shown = (bar_lvl, slovo)

    return cases


def pct(a, n):
    return '—' if not n else '%.1f%%' % (100.0 * a / n)


ISH = ('слом', 'конец тело', 'конец тень', 'оба на одной свече')

print('=' * 92)
print('Н41 НА ДВИЖКЕ v3.33 · слом против смерти · СЧИТАНО ВРОЗЬ')
print('его слово: «да, считай врозь»')
print('=' * 92)

for path, nm in DATA:
    rows = load(os.path.join(ROOT, path))
    print('\n' + '─' * 92)
    print('%s — %d баров' % (nm, len(rows)))
    print('─' * 92)
    for dn_side, dn in ((False, 'ВОСХ'), (True, 'НИСХ')):
        for ct, tag in ((False, 'БЫЛО v3.29'), (True, 'СТАЛО v3.33')):
            cs = schitat(rows, dn_side, ct)
            for slovo in ('слом раньше', 'слом позже'):
                sel = [x for x in cs if x['слово'] == slovo]
                n = len(sel)
                if not n:
                    continue
                cnt = {}
                for x in sel:
                    cnt[x['исход']] = cnt.get(x['исход'], 0) + 1
                print('  %-4s %-12s %-13s n=%-5d  слом %-7s  конец·ТЕЛО %-7s  '
                      'конец·ТЕНЬ %-7s  оба %-7s'
                      % (dn, tag, slovo, n,
                         pct(cnt.get('слом', 0), n),
                         pct(cnt.get('конец тело', 0), n),
                         pct(cnt.get('конец тень', 0), n),
                         pct(cnt.get('оба на одной свече', 0), n)))
        print()
