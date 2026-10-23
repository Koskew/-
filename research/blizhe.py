#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
КТО БЛИЖЕ К КОНЦУ, когда рисуются оба. Замер к мысли 5 аудита (Клод 4).

Параметры согласованы владельцем 23.10.2026 словом «параметры для замера
супер». Спорный пункт решён так: КОНЦОМ считается смерть по глубине и
отмена касанием — оба конца на своём пороге. АРХИВ концом НЕ считается:
счёт дошёл до (5), тренд отработал, это результат, а не поражение, и
такой случай уходит в отдельный исход.

ЧТО СКАЗАЛА БЫ ПРИПИСКА: из двух живых трендов ближе к концу тот, у кого
МЕНЬШЕ запас в процентах от цены — ровно те числа, что стоят в табло.

ДВА СЧЁТА, не смешиваются:
  А · по БАРАМ   — какую долю времени приписка называла бы каждого.
                   Про ЭКРАН, не про рынок: одна ситуация держится долго.
  Б · по СЛУЧАЯМ — сбылось ли. Случай = отрезок, пока живы оба. Слово
                   берётся в начале, исход — кто кончился первым.

ВЫРАВНИВАНИЕ ПО ВРЕМЕНИ, та же дисциплина, что в Н41: приписка читается
на ЗАКРЫТОМ баре, события проверяются СЛЕДУЮЩИМ.

КЛЕТКИ: ступени одинаковые и разные — ПОРОЗНЬ. На строгой ступени запас
меряется тенью до самой опоры, на мягкой телом до порога; трассировка
показала, что разные ступени случаются в 44.7% баров, где живы оба.

Движок: v3.27, zguard/knee_seq/birth_lvl включены.

    python3 research/blizhe.py
"""

import os
import sys
import statistics as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dvizhok2 as D

DEPTH = 0.20
RUN = dict(zguard=True, knee_seq=True, birth_lvl=True, trace=True, slom=True)
LIV = (D.ST_MAY, D.ST_LIVE)
ENDS = (D.ST_DEAD, D.ST_CAN)      # конец на своём пороге
ARC = D.ST_ARC                    # результат, не конец


def zapas(o, h, l, c, lvl, onz, leg, dn_side):
    """Запас ровно как его считает табло."""
    if dn_side:
        return (lvl - h) if onz else ((lvl + DEPTH * leg) - max(o, c))
    return (l - lvl) if onz else (min(o, c) - (lvl - DEPTH * leg))


def run(rows, name):
    up = D.run_all(rows, flip=False, **RUN)
    dn = D.run_all(rows, flip=True, **RUN)
    tu, td, legs = up['trace'][2], dn['trace'][2], up['sl_leg']

    A = {'ВОСХ': 0, 'НИСХ': 0, 'ровно': 0, 'живы не оба': 0}
    cases = []
    cur = None
    shown = None

    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        lu, su, ozu = tu[i]
        ld, sd, ozd = td[i]

        # ── события ЭТОГО бара по приписке, показанной ПРОШЛЫМ ──
        if shown is not None:
            u_end = su in ENDS
            d_end = sd in ENDS
            u_arc = su == ARC
            d_arc = sd == ARC
            if cur is None:
                cur = {'слово': shown[0], 'разные': shown[1],
                       'разрыв': shown[2], 'бар': i - 1,
                       'перевороты': 0, 'сейчас': shown[0]}
            elif shown[0] != cur['сейчас']:
                cur['перевороты'] += 1
                cur['сейчас'] = shown[0]
            ish = None
            if u_end and d_end:
                ish = 'оба на одной свече'
            elif u_end:
                ish = 'ВОСХ первым'
            elif d_end:
                ish = 'НИСХ первым'
            elif u_arc or d_arc:
                ish = 'ушёл в архив'
            if ish:
                cur['исход'] = ish
                cases.append(cur)
                cur = None

        # ── что показало бы табло на ЭТОМ баре ──
        ok = (su in LIV and sd in LIV and lu is not None and ld is not None)
        if not ok:
            A['живы не оба'] += 1
            if cur is not None:
                cur['исход'] = 'кончился иначе'
                cases.append(cur)
                cur = None
            shown = None
            continue

        leg = legs[i]
        zu = zapas(o, h, l, c, lu, ozu, leg, False)
        zd = zapas(o, h, l, c, -ld, ozd, leg, True)
        pu, pd = 100.0 * zu / c, 100.0 * zd / c
        if abs(pu - pd) < 1e-9:
            slovo = 'ровно'
        else:
            slovo = 'ВОСХ' if pu < pd else 'НИСХ'
        A[slovo] += 1
        shown = (slovo, ozu != ozd, abs(pu - pd))

    if cur is not None:
        cur['исход'] = 'данные закончились'
        cases.append(cur)

    # ── печать ──
    print('=' * 70)
    print('%s — %d баров' % (name, len(rows)))
    print('=' * 70)
    tot = sum(A.values())
    work = A['ВОСХ'] + A['НИСХ'] + A['ровно']
    print('  А · ЧТО УВИДИШЬ, по барам (про экран, не про рынок)')
    for k in ('ВОСХ', 'НИСХ', 'ровно', 'живы не оба'):
        print('     %-12s %7d   %5.1f%% от всех баров' % (k, A[k], 100.0 * A[k] / tot))
    if work:
        print('     из баров, где приписка ГОВОРИТ (%d): ВОСХ %.1f%%, НИСХ %.1f%%'
              % (work, 100.0 * A['ВОСХ'] / work, 100.0 * A['НИСХ'] / work))

    print('  Б · СБЫЛОСЬ ЛИ, по случаям — всего %d' % len(cases))
    for raz, gname in ((False, 'ступени ОДИНАКОВЫЕ'), (True, 'ступени РАЗНЫЕ')):
        sub = [x for x in cases if x['разные'] == raz]
        if not sub:
            continue
        print('     %s — случаев %d' % (gname, len(sub)))
        for slovo in ('ВОСХ', 'НИСХ'):
            ss = [x for x in sub if x['слово'] == slovo]
            if not ss:
                continue
            ish = {}
            for x in ss:
                ish[x['исход']] = ish.get(x['исход'], 0) + 1
            # СБЫЛОСЬ = назван тот, кто и кончился первым
            hit = ish.get(slovo + ' первым', 0)
            miss = ish.get(('НИСХ' if slovo == 'ВОСХ' else 'ВОСХ') + ' первым', 0)
            both = ish.get('оба на одной свече', 0)
            dec = hit + miss + both
            print('        сказала «%s»: %d случаев' % (slovo, len(ss)))
            for k in sorted(ish, key=lambda z: -ish[z]):
                print('           → %-20s %5d  %5.1f%%' % (k, ish[k], 100.0 * ish[k] / len(ss)))
            if dec:
                print('           ИЗ РЕШЁННЫХ (%d, без архива и прочего): СБЫЛОСЬ %.1f%%, '
                      'НЕ сбылось %.1f%%, ничья %.1f%%'
                      % (dec, 100.0 * hit / dec, 100.0 * miss / dec, 100.0 * both / dec))
            fl = [x['перевороты'] for x in ss]
            rz = [x['разрыв'] for x in ss]
            print('           слово переворачивалось: медиана %d, ни разу у %.1f%%; '
                  'разрыв между запасами в начале: медиана %.2f пп'
                  % (st.median(fl), 100.0 * sum(1 for q in fl if q == 0) / len(fl), st.median(rz)))
    print()
    return cases


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for path, nm in (('data/XAUUSD_1h_9y.csv', 'ЧАСОВИК, девять лет — ГЛАВНЫЙ ВЕРДИКТ'),
                     ('data/XAUUSD_1h_2y.csv', 'ЧАСОВИК, два года — повторяемость'),
                     ('data/XAUUSD_5m.csv', 'ПЯТИМИНУТКА — третья точка')):
        run(D.load(os.path.join(root, path)), nm)
    rows = D.load(os.path.join(root, 'data/XAUUSD_1h_9y.csv'))
    h = len(rows) // 2
    run(rows[:h], 'ПОЛОВИНЫ · первая')
    run(rows[h:], 'ПОЛОВИНЫ · вторая')
    return 0


if __name__ == '__main__':
    sys.exit(main())
