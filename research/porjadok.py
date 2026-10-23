#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЧТО РАНЬШЕ — СЛОМ ИЛИ СМЕРТЬ. Замер к мысли 4 аудита (ЖПТ 3, Клод 3).

Заказан владельцем 23.10.2026: «нужно померить как часто какой порядок
бывает и посмотреть какие будут данные, тогда сможем ответить... может
по данным и ничего не нужно будет менять или что-то другое вскроется».
Параметры согласованы его словом «параметры норм».

ДВА СЧЁТА, НАРОЧНО РАЗНЫЕ, И ОНИ НЕ СМЕШИВАЮТСЯ:

  А · ЧТО УВИДИШЬ — по БАРАМ. Какую долю времени приписка говорила бы
      «слом раньше», какую «слом позже», какую молчала. Это про ЭКРАН,
      не про рынок: одна ситуация держится десятками баров.

  Б · СБЫЛОСЬ ЛИ — по СЛУЧАЯМ. Случай = отрезок, пока тренд жив и на
      опасной стороне есть непробитый уровень. Веду вперёд до первого
      из двух событий. Проценты вердикта берутся ТОЛЬКО отсюда.

ОПАСНАЯ СТОРОНА: у восходящего ВНИЗ, у нисходящего ВВЕРХ.

ПОРОГ, как в пайне:
  мягкая ступень (опора съехала с нуля) — уровень ∓ 0.20 × колено,
     рубит ТЕЛО свечи;
  строгая ступень (опора на самом нуле) — САМА опора, рубит ТЕНЬ.
Строгая считается ОТДЕЛЬНОЙ КЛЕТКОЙ: там буфера нет вовсе, и мешать её
с мягкой значило бы усреднить две разные геометрии.

ИСХОД СЛУЧАЯ один из пяти: слом · конец тренда · оба на одной свече ·
тренд кончился иначе (архив) · данные закончились.

Движок: v3.26, zguard=True, knee_seq=True, birth_lvl=True.
Сломы — ручка slom=True в dvizhok2, порт из пайна v3.26.

    python3 research/porjadok.py
"""

import os
import sys
import statistics as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dvizhok2 as D

MINTICK = 0.01          # допуск клетки «совпали»
DEPTH = 0.20
RUN = dict(zguard=True, knee_seq=True, birth_lvl=True, trace=True, slom=True)
LIV = (D.ST_MAY, D.ST_LIVE)
# конец тренда НА СВОЁМ ПОРОГЕ: смерть по глубине или отмена касанием
ENDS = (D.ST_DEAD, D.ST_CAN)


def one_side(rows, tr, near, legs, dn_side):
    """Один проход по барам для ОДНОГО направления.

    dn_side=False — восходящий: опасность вниз, цены настоящие.
    dn_side=True  — нисходящий: тот же код на перевёрнутом мире, уровень
    из трассировки меняет знак. Сломы не зеркалятся, они в настоящих
    ценах — как и в пайне, где f_slom вызывается один раз.

    ВЫРАВНИВАНИЕ ПО ВРЕМЕНИ, и это главное место этого замера.
    Границы, которые владелец видит в табло, посчитаны по ЗАКРЫТОМУ
    бару: `near[i]` — список живых уровней ПОСЛЕ того, как бар i
    вычеркнул пробитое. Значит проверять их надо СЛЕДУЮЩИМ баром.

    Первая моя попытка сравнивала границы бара i с диапазоном того же
    бара i — и уровень, переживший вычёркивание на баре i, по
    построению уже не мог быть пробит баром i. Сломов не находилось
    вовсе, и все случаи кончались «концом тренда». Ошибка найдена по
    этому симптому и здесь исправлена: показ берётся с бара i, события
    с бара i+1.

    Возвращает (счёт А, счёт А только строгая, список случаев).
    """
    sg = -1.0 if dn_side else 1.0
    A = {'слом раньше': 0, 'слом позже': 0, 'совпали': 0,
         'уровня нет': 0, 'тренда нет': 0}
    As = dict(A)
    cases = []
    cur = None
    shown = None        # что стояло в табло на ПРЕДЫДУЩЕМ закрытом баре

    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        lvl, stt, onz = tr[i]
        up, dn = near[i]
        leg = legs[i]

        # ── СОБЫТИЯ ЭТОГО БАРА по границам, показанным ПРОШЛЫМ баром ──
        if shown is not None:
            p_lvl, p_thr, p_slovo, p_onz, p_leg = shown
            slom = (l <= p_lvl) if not dn_side else (h >= p_lvl)
            kon = stt in ENDS
            if cur is None:
                cur = {'бар': i - 1, 'слово': p_slovo, 'строгая': p_onz,
                       'перевороты': 0, 'слово_сейчас': p_slovo,
                       'зазор': abs(p_lvl - p_thr),
                       'зазор_кол': abs(p_lvl - p_thr) / p_leg if p_leg > 0 else None}
            elif p_slovo != cur['слово_сейчас']:
                cur['перевороты'] += 1
                cur['слово_сейчас'] = p_slovo
            if slom or kon:
                cur['исход'] = ('оба на одной свече' if (slom and kon)
                                else 'слом' if slom else 'конец тренда')
                cur['бар_конца'] = i
                cases.append(cur)
                cur = None

        # ── ЧТО ПОКАЗЫВАЕТ ТАБЛО НА ЭТОМ БАРЕ ──
        alive = stt in LIV and lvl is not None
        if not alive:
            A['тренда нет'] += 1
            if cur is not None:
                cur['исход'] = 'кончился иначе'
                cur['бар_конца'] = i
                cases.append(cur)
                cur = None
            shown = None
            continue

        lvl = sg * lvl
        bar_lvl = dn if not dn_side else up
        thr = lvl if onz else (lvl - DEPTH * leg if not dn_side
                               else lvl + DEPTH * leg)

        if bar_lvl is None:
            A['уровня нет'] += 1
            if onz:
                As['уровня нет'] += 1
            if cur is not None:
                cur['исход'] = 'уровень исчез'
                cur['бар_конца'] = i
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
        A[slovo] += 1
        if onz:
            As[slovo] += 1
        shown = (bar_lvl, thr, slovo, onz, leg)

    if cur is not None:
        cur['исход'] = 'данные закончились'
        cur['бар_конца'] = len(rows) - 1
        cases.append(cur)
    return A, As, cases


def pct(a, b):
    return '—' if b == 0 else '%.1f%%' % (100.0 * a / b)


def report(name, rows):
    up = D.run_all(rows, flip=False, **RUN)
    dn = D.run_all(rows, flip=True, **RUN)
    print('=' * 70)
    print('%s — %d баров' % (name, len(rows)))
    print('=' * 70)

    for dn_side, nm in ((False, 'ВОСХОДЯЩИЙ, опасность ВНИЗ'),
                        (True, 'НИСХОДЯЩИЙ, опасность ВВЕРХ')):
        res = up if not dn_side else dn
        A, As, cases = one_side(rows, res['trace'][2], res['sl_near'],
                                res['sl_leg'], dn_side)
        tot = sum(A.values())
        work = A['слом раньше'] + A['слом позже'] + A['совпали']
        print()
        print('  %s' % nm)
        print('  ── А · ЧТО УВИДИШЬ, по барам (про экран, не про рынок) ──')
        for k in ('слом раньше', 'слом позже', 'совпали', 'уровня нет', 'тренда нет'):
            print('     %-14s %7d  %7s от всех баров' % (k, A[k], pct(A[k], tot)))
        if work:
            print('     из баров, где приписка ГОВОРИТ (%d):' % work)
            for k in ('слом раньше', 'слом позже', 'совпали'):
                print('        %-12s %7s' % (k, pct(A[k], work)))

        print('  ── Б · СБЫЛОСЬ ЛИ, по случаям ──')
        print('     случаев всего: %d' % len(cases))
        for grp, gname in ((False, 'МЯГКАЯ ступень'), (True, 'СТРОГАЯ ступень')):
            sub = [x for x in cases if x['строгая'] == grp]
            if not sub:
                continue
            print('     %s — случаев %d' % (gname, len(sub)))
            for slovo in ('слом раньше', 'слом позже', 'совпали'):
                ss = [x for x in sub if x['слово'] == slovo]
                if not ss:
                    continue
                ish = {}
                for x in ss:
                    ish[x['исход']] = ish.get(x['исход'], 0) + 1
                print('        сказала «%s»: %d случаев' % (slovo, len(ss)))
                for k in sorted(ish, key=lambda z: -ish[k] if False else -ish[z]):
                    print('           → %-20s %5d  %7s' % (k, ish[k], pct(ish[k], len(ss))))
                fl = [x['перевороты'] for x in ss]
                z = [x['зазор'] for x in ss]
                zk = [x['зазор_кол'] for x in ss if x['зазор_кол'] is not None]
                print('           перевернулось слово за случай: медиана %d, максимум %d, ни разу у %s'
                      % (st.median(fl), max(fl), pct(sum(1 for q in fl if q == 0), len(fl))))
                if z:
                    print('           зазор между границами: медиана %.2f пт%s'
                          % (st.median(z),
                             ', %.2f колена' % st.median(zk) if zk else ''))


def main():
    for path, nm in (('data/XAUUSD_1h_9y.csv', 'ЧАСОВИК, девять лет — ГЛАВНЫЙ ВЕРДИКТ'),
                     ('data/XAUUSD_1h_2y.csv', 'ЧАСОВИК, два года — повторяемость'),
                     ('data/XAUUSD_5m.csv', 'ПЯТИМИНУТКА — третья точка')):
        full = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path)
        report(nm, D.load(full))
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
