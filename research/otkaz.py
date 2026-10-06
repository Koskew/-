# -*- coding: utf-8 -*-
"""§33 · СКОЛЬКО СТОИТ ПРАВИЛО «СЛОЙ ОТКАЗЫВАЕТСЯ ОТ ТРЕНДА».

Решение владельца 06.10.2026, ВОСХОДЯЩИЙ §33:

    слою разрешена ОДНА одолженная метка. Пока она не израсходована —
    счёт обязан её взять. Как только понадобилась ВТОРАЯ — слой
    перестаёт считать этот тренд.

Его слова: «нужно, чтобы он просто перестал искать этот тренд или убрал
его счёт из таблицы до момента следующих критериев тренда 5\\5».

ВОПРОС ОДИН: как часто это будет случаться. Если слой сдаётся редко —
правило отличное. Если часто — владелец будет смотреть на пустую
колонку, и правило надо смягчать.

ЧТО СЧИТАЕТСЯ, по слову владельца 06.10:
    5/5 — дозы 0, 1, 2 и от скольких отказался
    3/3 — дозы 0, 1, 2 и от скольких отказался
    2/2 — только свои, донора у него нет

ПРАВИЛА ЗАМЕРА — СЕГОДНЯШНИЕ, движок не трогаю:
  · смерть — имп × 0.33, как в Н19 и Н20, иначе числа не сравнить;
  · донор 5/5 — «3/3, а если пусто — 2/2» (эталон), 3/3 — 2/2;
  · чередование З22 в силе: вставка той же стороны пропускается и
    СПРОСОМ не считается;
  · ничего из принятого 05–06.10 (возврат уровня, запасное
    подтверждение, смерть по точкам счёта) в замер НЕ входит — этого
    нет ни в пайне, ни в реплике.

ЧТО ТАКОЕ ОТКАЗ В КОДЕ. Пришло колено донора, слой своего здесь не
имеет, чередование не нарушено — но доза израсходована. Это и есть
спрос на вторую метку. Если в этот момент тренд ЖИВ — он снимается с
счёта (не смерть: красной чёрточки нет), и слой ждёт СВОЕГО колена,
чтобы вернуться к работе.

    python3 research/otkaz.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
from zerkalo import Knees, Trend, events


def run_refuse(rows, dL, dDs, flip, dose):
    """Прогон слоя с дозой и правилом отказа. Возвращает список исходов.

    Исход счёта: {'mx': докуда дошёл, 'ins': одолженных колен за жизнь,
                  'how': 'умер' | 'отказ' | 'конец данных'}
    """
    atL = events(rows, dL, flip)
    own = {(b, h) for lst in atL.values() for b, p, h in lst}
    ev = [(b, cf, p, h, True) for cf, lst in atL.items() for b, p, h in lst]
    seen = set(own)
    for dD in dDs:
        for cf, lst in events(rows, dD, flip).items():
            for b, p, h in lst:
                if (b, h) not in seen:
                    seen.add((b, h))
                    ev.append((b, cf, p, h, False))
    # порядок внутри бара — настоящий в обоих мирах, см. forma.py
    ev.sort(key=lambda e: (e[0], e[3] if flip else not e[3]))

    K, T = Knees(), Trend()
    sg = -1.0 if flip else 1.0
    used = 0            # одолженных подряд, сбрасывается своим коленом
    blocked = False     # слой отказался, ждёт своего колена
    ins = 0             # одолженных за жизнь текущего счёта
    out = []
    q = 0
    was = 0             # tr на прошлом баре
    seen_tr = len(T.trends)
    for i in range(len(rows)):
        _, o, hgh, low, c = rows[i]
        nw = fr = False
        demand = False
        while q < len(ev) and ev[q][1] <= i:
            b, cf, p, hh, mine = ev[q]; q += 1
            if mine:
                blocked = False
                used = 0
                nw = K.push(p, b, hh) or nw
                fr = True
                continue
            if blocked:
                continue
            if K.H and K.H[-1] == hh:      # З22: та же сторона — не спрос
                continue
            if used >= dose:
                demand = True              # спрос на лишнюю метку
                continue
            nw = K.push(p, b, hh) or nw
            fr = True
            used += 1
            if T.tr == 1:
                ins += 1

        T.step(i, sg * o, sg * c, K, nw, fr)

        # смерть по движку — её Trend кладёт в T.trends
        if len(T.trends) > seen_tr:
            for tr in T.trends[seen_tr:]:
                out.append({'mx': tr[3], 'ins': ins, 'how': 'умер'})
            seen_tr = len(T.trends)
            ins = 0

        # ОТКАЗ — после шага: тренд был жив и понадобилась лишняя метка
        if demand:
            blocked = True
            if T.tr == 1:
                out.append({'mx': T.mx, 'ins': ins, 'how': 'отказ'})
                T.tr = 0; T.cnt = -1; T.zb = -1; T.pzb = -1
                T.lvl = None; T.bel = 0; T.mx = -1
                ins = 0
        if T.tr == 0:
            ins = 0
        was = T.tr
    if T.tr == 1:
        out.append({'mx': T.mx, 'ins': ins, 'how': 'конец данных'})
    return out


def block(rows, title):
    print('\n' + '=' * 74)
    print(title + '   ·   баров ' + str(len(rows)))
    print('=' * 74)
    for name, dL, dDs in (('5/5', 5, [3, 2]), ('3/3', 3, [2]), ('2/2', 2, [])):
        doses = [0] if not dDs else [0, 1, 2]
        print('\n  слой %s' % name)
        print('  %-8s %7s %7s %7s %7s %9s %9s' %
              ('доза', 'счётов', '0 одол', '1 одол', '2+ одол', 'ОТКАЗОВ', 'дошли (5)'))
        for dose in doses:
            agg = {}
            for flip in (False, True):
                for r in run_refuse(rows, dL, dDs, flip, dose):
                    agg.setdefault(r['how'], []).append(r)
            allr = [r for v in agg.values() for r in v]
            n = len(allr)
            if n == 0:
                continue
            i0 = sum(1 for r in allr if r['ins'] == 0)
            i1 = sum(1 for r in allr if r['ins'] == 1)
            i2 = sum(1 for r in allr if r['ins'] >= 2)
            otk = len(agg.get('отказ', []))
            fin = sum(1 for r in allr if r['mx'] >= 5)
            f = lambda k: '%d (%.0f%%)' % (k, 100.0 * k / n)
            print('  %-8s %7d %7s %7s %7s %9s %9s' %
                  (dose, n, f(i0).split(' ')[1], f(i1).split(' ')[1],
                   f(i2).split(' ')[1], f(otk), f(fin)))


def main():
    for path, title in (('data/XAUUSD_1h_9y.csv', 'ЗОЛОТО 1H · ДЕВЯТЬ ЛЕТ'),
                        ('data/XAUUSD_1h_2y.csv', 'ЗОЛОТО 1H · ДВА ГОДА (проверка повторяемости)')):
        block(load(path), title)
    print('\nСчёты обоих направлений сложены: движок один, зеркало точное.')
    print('«Отказов» у дозы 0 — это спрос на ПЕРВУЮ чужую метку.')


if __name__ == '__main__':
    main()
