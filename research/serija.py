#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СЕРИЯ СЛОМОВ, ОБРЕЗАННАЯ НУЛЁМ ТРЕНДА. Замер В27, под строку З54.

Параметры согласованы владельцем 23.10.2026 словом «параметры для замера
супер». Спорные решены так:
  · обрезать от нуля ВСЕГО тренда (продолжение его не переписывает), а
    не от нуля текущего счёта — иначе серия обрубалась бы каждым
    продолжением;
  · «говорит громче» мерится ДВУМЯ предметами: (а) предсказывает
    следующий слом — это ровно то, что мерил Н14, значит числа
    сравнимы; (б) предсказывает судьбу самого тренда — дойдёт ли счёт
    до (5). Второе и есть работа строки З54.

ЗАЧЕМ. Строка З54 показывает третьей частью серию сломов и согласна ли
она с этим трендом. Серия сейчас считается ПО ВСЕМУ ГРАФИКУ, и часть её
может быть старше самого тренда. Владелец выбрал обрезку. Это НОВОЕ
ОПРЕДЕЛЕНИЕ, и до замера строка не вносится.

ЧЕСТНО ПРО СРАВНИМОСТЬ С Н14. Обрезанную серию можно посчитать только
пока тренд жив. Поэтому ОБА признака — глобальный и обрезанный —
считаются на ОДНОЙ И ТОЙ ЖЕ выборке: сломы на барах, где этот тренд жив.
Прямое сравнение с +11.8 пп из Н14 было бы сравнением разных выборок;
здесь сравниваются два признака между собой, на одних событиях.

НАДБАВКА считается от СОБСТВЕННОЙ доли сломов в эту сторону, а не от
50%: на растущем золоте иначе вывод выйдет про рост, а не про сломы.

ЗАЩИТА ОТ ТАВТОЛОГИИ в (б): признак берётся НА БАРЕ РОЖДЕНИЯ, исход
смотрится ПОСЛЕ. Иначе признак описал бы сам тренд — так в проекте уже
умерли мутность и глубина счёта.

Клетка меньше 100 наблюдений вердикта не даёт, и это печатается.

Движок: v3.27, slom=True.

    python3 research/serija.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dvizhok2 as D

RUN = dict(zguard=True, knee_seq=True, birth_lvl=True, trace=True, slom=True)
LIV = (D.ST_MAY, D.ST_LIVE)
MIN_N = 100


def zb0_by_bar(sl_zb):
    """Ноль ВСЕГО тренда для каждого бара.

    В реплике `born` ставится только рождением и продолжением не
    переписывается, а `zb` переписывается. Значит ноль всего тренда —
    это `zb` на ПЕРВОМ баре с этим же `born`. Так восстанавливается
    tZB0 пайна, не трогая движок.
    """
    out = []
    seen = {}
    for zb, born in sl_zb:
        if born < 0:
            out.append(-1)
            continue
        if born not in seen:
            seen[born] = zb
        out.append(seen[born])
    return out


def runs_at(events, bars, zb0, dn_side):
    """Для каждого слома — длина серии ДО него, двумя способами.

    Возвращает список (бар, сторона, глоб_серия, обрез_серия), где
    серия — сколько сломов ОДНОЙ стороны шло подряд включая этот.
    Обрезанная считает только сломы с бара zb0 этого бара и позже.
    """
    out = []
    g_dir, g_run = 0, 0
    hist = []                      # (бар, сторона) — все сломы
    for b, d, p in events:
        if d == g_dir:
            g_run += 1
        else:
            g_dir, g_run = d, 1
        hist.append((b, d))
        z = zb0[b] if b < len(zb0) else -1
        # обрезанная серия: тот же подсчёт, но только по сломам с z и позже
        s_run = 0
        if z >= 0:
            for bb, dd in reversed(hist):
                if bb < z or dd != d:
                    break
                s_run += 1
        out.append((b, d, g_run, s_run))
    return out


def cell(tab, k):
    a, n = tab.get(k, (0, 0))
    return a, n


def predict_next(sample, name):
    """(а) Предсказывает ли серия СЛЕДУЮЩИЙ слом. Два признака рядом."""
    # sample: список (глоб, обрез, сторона, сторона_следующего)
    if not sample:
        print('     %s: пусто' % name)
        return
    up = sum(1 for g, s, d, nx in sample if d > 0)
    base_up = 100.0 * up / len(sample)
    print('     %s — событий %d, доля сломов ВВЕРХ %.1f%% (это и есть база)'
          % (name, len(sample), base_up))
    for tag, idx in (('ГЛОБАЛЬНАЯ', 0), ('ОБРЕЗАННАЯ', 1)):
        print('        %s серия:' % tag)
        for k in (1, 2, 3, 4):
            for d, dn in ((1, 'вверх'), (-1, 'вниз')):
                ss = [x for x in sample if x[idx] == k and x[2] == d]
                if not ss:
                    continue
                same = sum(1 for x in ss if x[3] == d)
                p = 100.0 * same / len(ss)
                b = base_up if d > 0 else 100.0 - base_up
                flag = '' if len(ss) >= MIN_N else '   ← МАЛО, вердикта нет'
                print('           k=%d %-6s n=%5d: следующий туда же %.1f%%, '
                      'база %.1f%%, надбавка %+.1f пп%s'
                      % (k, dn, len(ss), p, b, p - b, flag))
        ss = [x for x in sample if x[idx] >= 5]
        if ss:
            same = sum(1 for x in ss if x[3] == x[2])
            print('           k≥5        n=%5d: туда же %.1f%%%s'
                  % (len(ss), 100.0 * same / len(ss),
                     '' if len(ss) >= MIN_N else '   ← МАЛО'))


def run(rows, name):
    print('=' * 70)
    print('%s — %d баров' % (name, len(rows)))
    print('=' * 70)
    for dn_side, side in ((False, 'ВОСХОДЯЩИЙ'), (True, 'НИСХОДЯЩИЙ')):
        res = D.run_all(rows, flip=dn_side, **RUN)
        tr = res['trace'][2]
        ev = res['sl_events']
        zb0 = zb0_by_bar(res['sl_zb'])
        rr = runs_at(ev, rows, zb0, dn_side)

        # ── 1. отличается ли обрезанная серия от глобальной ВООБЩЕ ──
        alive = [x for x in rr if x[0] < len(tr) and tr[x[0]][1] in LIV]
        if not alive:
            print('  %s: живых баров со сломами нет' % side)
            continue
        same = sum(1 for b, d, g, s in alive if g == s)
        print('  %s' % side)
        print('     сломов на барах, где тренд жив: %d' % len(alive))
        print('     обрезанная серия СОВПАЛА с глобальной: %d  (%.1f%%)'
              % (same, 100.0 * same / len(alive)))
        shorter = [g - s for b, d, g, s in alive if g != s]
        if shorter:
            shorter.sort()
            print('     когда короче — короче на: медиана %d, максимум %d'
                  % (shorter[len(shorter) // 2], max(shorter)))

        # ── 2а. предсказание следующего слома ──
        nxt = {}
        for i in range(len(ev) - 1):
            nxt[ev[i][0]] = ev[i + 1][1]
        sample = [(g, s, d, nxt[b]) for b, d, g, s in alive if b in nxt]
        predict_next(sample, '(а) следующий слом, выборка «тренд жив»')

        # ── 2б. предсказание судьбы ТРЕНДА, признак на баре рождения ──
        T = res['T'][2]
        births = [c for c in T.counts if c.get('rst', 0) == 0 and c.get('born', -1) >= 0]
        if births:
            byb = {}
            for b, d, g, s in rr:
                byb.setdefault(b, (d, g, s))
            rows_b = []
            for c in births:
                bb = c['born']
                # последний слом НЕ ПОЗЖЕ бара рождения
                last = None
                for b, d, g, s in rr:
                    if b <= bb:
                        last = (b, d, g, s)
                    else:
                        break
                if last is None:
                    continue
                b, d, g, s = last
                za = (d > 0) != dn_side        # слом в сторону тренда?
                rows_b.append((s, za, c.get('mx', -1) >= 5))
            if rows_b:
                base = 100.0 * sum(1 for s, za, ok in rows_b if ok) / len(rows_b)
                print('     (б) судьба тренда, признак НА БАРЕ РОЖДЕНИЯ — рождений %d, '
                      'доходит до (5) вообще %.1f%%' % (len(rows_b), base))
                for za, zn in ((True, 'ЗА тренд'), (False, 'ПРОТИВ тренда')):
                    for k in (0, 1, 2, 3):
                        ss = [x for x in rows_b if x[1] == za and x[0] == k]
                        if not ss:
                            continue
                        p = 100.0 * sum(1 for x in ss if x[2]) / len(ss)
                        flag = '' if len(ss) >= MIN_N else '   ← МАЛО, вердикта нет'
                        print('        обрезанная серия %-14s k=%d n=%4d: до (5) %.1f%%, '
                              'надбавка %+.1f пп%s'
                              % (zn, k, len(ss), p, p - base, flag))
    print()


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for path, nm in (('data/XAUUSD_1h_9y.csv', 'ЧАСОВИК, девять лет — ГЛАВНЫЙ ВЕРДИКТ'),
                     ('data/XAUUSD_1h_2y.csv', 'ЧАСОВИК, два года — повторяемость'),
                     ('data/XAUUSD_5m.csv', 'ПЯТИМИНУТКА — третья точка')):
        run(D.load(os.path.join(root, path)), nm)
    return 0


if __name__ == '__main__':
    sys.exit(main())
