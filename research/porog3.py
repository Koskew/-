# -*- coding: utf-8 -*-
"""Два замера на движке v2.1 — 08.10.2026.

**А · ЧЕТЫРЕ ПРОЦЕНТА Н30, пересчитанные на новой цепочке.** В подсказке
ручки «Глубина, долей колена» стоят числа со СТАРОЙ цепочки: убивает по
делу 77%, зря 23%, пропускает 34%, базовая доля ослаблений 63%. Это
правка моей ошибки, а не выбор: определения те же, сменился движок.

Определения взяты из `porog.py` слово в слово:
  · берутся НИЗЫ на позициях счёта (0), (2), (4) — те, что держат уровень;
  · только ЗАХОДЫ: следующий низ пришёл LL, то есть цена реально ушла ниже;
  · исход СТРУКТУРНЫЙ и от глубины не зависящий — следующая ВЕРШИНА после
    захода пришла HH (структура оправилась) или LH (слабеет дальше);
  · глубина по ТЕЛУ, между барами подтверждения двух низов.

**СМЕРТЬ ЗДЕСЬ ВЫКЛЮЧЕНА, и это не выбор, а условие задачи.** С
включённой смертью порог обрезает выборку на первом же глубоком заходе,
и «убили зря» наблюдать нечем — замер стал бы круговым. Поэтому счёт
ведётся по ЦЕПОЧКЕ, без правил смерти, отмены и отказа. Так же считала
и Н30.

**Б · ОПАСНОСТЬ РАЗВИЛКИ А.** §40 назвал её вслух: «если уровень уехал
на манипуляционный LL, а тот потом пропал, уровень прыгнет обратно
ВВЕРХ — и тренд может оказаться мёртвым по линии, которой уже нет».
Здесь это проверяется прибором: как часто уровень прыгает ВВЕРХ у живого
тренда и как часто тренд умирает сразу после такого прыжка.

    python3 research/porog3.py
"""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
import dvizhok2 as D

LEGWIN = D.LEGWIN


def counts_v21(K):
    """Счёт БЕЗ СМЕРТИ по правилам v2.1. Возвращает номер каждого колена
    или -1.

    Отличия от `porog.counts`, то есть от старого движка:
      · РОЖДЕНИЕ объявляет (1) — любая первая вершина после LL. Поиска
        нуля назад больше нет;
      · ПОСЛЕ (5) решает ПЕРВЫЙ новый низ: HL — продолжение с нуля,
        LL — счёт кончился (архив)."""
    n = len(K.P)
    num = [-1] * n
    cnt = -1
    for i in range(n):
        if cnt >= 0:
            if cnt >= 5 and not K.H[i]:
                if K.L[i] == 'HL':
                    cnt = 0                      # продолжение
                    num[i] = 0
                else:
                    cnt = -1                     # архив: счёт кончился
                continue
            if cnt < 5:
                cnt += 1
            num[i] = cnt
            continue
        # рождение на (1): вершина, перед ней низ LL
        if K.H[i] and i >= 1 and (not K.H[i - 1]) and K.L[i - 1] == 'LL':
            num[i - 1] = 0
            cnt = 1
            num[i] = 1
    return num


def roll_leg(K, upto):
    """Скользящее среднее колено, как его считает движок: последние
    LEGWIN ног на момент колена `upto`."""
    frm = max(1, upto + 1 - LEGWIN)
    legs = [abs(K.P[i] - K.P[i - 1]) for i in range(frm, upto + 1)]
    return sum(legs) / len(legs) if legs else 0.0


def collect(rows, flip, li):
    """Заходы на сторожевых низах. Возвращает список
    {глубина в долях колена, слабеет?}."""
    res = D.run_all(rows, flip=flip)
    C = res['C'][li]
    num = counts_v21(C)
    n = len(C.P)
    out = []
    for i in range(n):
        if C.H[i] or num[i] not in (0, 2, 4):
            continue
        nxt = -1
        for k in range(i + 1, n):
            if not C.H[k]:
                nxt = k
                break
        if nxt < 0 or C.L[nxt] != 'LL':
            continue                       # только ЗАХОДЫ
        a, b = C.C[i], C.C[nxt]
        if b <= a:
            continue
        vt = -1
        for k2 in range(nxt + 1, n):
            if C.H[k2]:
                vt = k2
                break
        if vt < 0:
            continue
        lv = C.P[i]
        deep = 0.0
        for t in range(a, min(b + 1, len(rows))):
            _, o, h, l, c = rows[t]
            body_low = -max(o, c) if flip else min(o, c)
            deep = max(deep, lv - body_low)
        leg = roll_leg(C, i)
        if leg <= 0:
            continue
        out.append({'d': max(deep, 0.0) / leg, 'weak': C.L[vt] != 'HH'})
    return out


def table_a(rows, title):
    print()
    print('=' * 70)
    print('А · ЧЕТЫРЕ ПРОЦЕНТА. ' + title)
    print('=' * 70)
    allr = []
    for li, ln in ((0, '5/5'), (1, '3/3'), (2, '2/2')):
        for flip in (False, True):
            allr += collect(rows, flip, li)
    tot = len(allr)
    weak = sum(1 for r in allr if r['weak'])
    print('заходов всего: %d · из них слабеют: %d' % (tot, weak))
    print('БАЗОВАЯ ДОЛЯ ОСЛАБЛЕНИЙ: %.0f%%' % (100.0 * weak / tot))
    print()
    print('%-8s %8s %12s %10s %12s' % ('порог', 'убито', 'по делу', 'зря', 'пропущено'))
    for thr in (0.10, 0.15, 0.20, 0.25, 0.30, 0.40):
        kill = [r for r in allr if r['d'] > thr]
        kw = sum(1 for r in kill if r['weak'])
        missed = weak - kw
        mark = '  ← эталон' if abs(thr - 0.20) < 1e-9 else ''
        print('%-8.2f %8d %11.0f%% %9.0f%% %11.0f%%%s' % (
            thr, len(kill),
            100.0 * kw / len(kill) if kill else 0.0,
            100.0 * (len(kill) - kw) / len(kill) if kill else 0.0,
            100.0 * missed / weak if weak else 0.0, mark))
    return allr


def table_b(rows, title):
    """Опасность развилки А: прыгает ли уровень ВВЕРХ и умирает ли тренд
    сразу после."""
    print()
    print('=' * 70)
    print('Б · ПРЫЖОК УРОВНЯ ВВЕРХ. ' + title)
    print('=' * 70)
    print('%-5s %-5s %10s %12s %14s %14s' %
          ('слой', 'напр', 'прыжков', 'смертей', 'смерть ≤1 бар', 'смерть ≤3 бара'))
    for li, ln in ((0, '5/5'), (1, '3/3'), (2, '2/2')):
        for flip, ar in ((False, '↑'), (True, '↓')):
            res = D.run_all(rows, flip=flip, trace=True)
            tr = res['trace'][li]
            jumps, d1, d3 = [], 0, 0
            deaths = []
            for i in range(1, len(tr)):
                lv, st, onz = tr[i]
                pl, pst, _ = tr[i - 1]
                if st == D.ST_DEAD and pst != D.ST_DEAD:
                    deaths.append(i)
                # прыжок: уровень ВЫРОС у живого тренда
                if lv is not None and pl is not None and lv > pl + 1e-9 \
                   and st in (D.ST_MAY, D.ST_LIVE) and pst in (D.ST_MAY, D.ST_LIVE):
                    jumps.append(i)
            ds = set(deaths)
            for j in jumps:
                if any((j + k) in ds for k in (0, 1)):
                    d1 += 1
                if any((j + k) in ds for k in (0, 1, 2, 3)):
                    d3 += 1
            print('%-5s %-5s %10d %12d %13s %14s' % (
                ln, ar, len(jumps), len(deaths),
                '%d (%.1f%%)' % (d1, 100.0 * d1 / len(jumps)) if jumps else '—',
                '%d (%.1f%%)' % (d3, 100.0 * d3 / len(jumps)) if jumps else '—'))


def main():
    rows9 = load('data/XAUUSD_1h_9y.csv')
    table_a(rows9, 'девять лет часовика, все слои и оба направления')
    table_b(rows9, 'девять лет часовика')
    rows2 = load('data/XAUUSD_1h_2y.csv')
    table_b(rows2, 'два года часовика — проверка повторяемости')


if __name__ == '__main__':
    main()
