# -*- coding: utf-8 -*-
"""С1 · СЫРЫЕ ВСТАВКИ: что слой выбрасывает и что исчезает из хвоста.

Замеряет В15 и В20 одним проходом. Параметры согласованы владельцем
29.09.2026:

  данные       9 лет часовика, пятиминутка не трогается;
  пары         5/5 <- 3/3 и 3/3 <- 2/2. Запасного донора 2/2 для 5/5
               в счёте НЕТ — слово владельца. Он считается отдельной
               строкой только как факт про нынешнюю картинку;
  направления  восходящий и нисходящий (перевёрнутые колена);
  половины     история делится пополам, числа отдельно.

Движок колен берётся из research/zerkalo.py — своей копии нет.
Своя здесь только логика ОТРИСОВКИ (f_sub и f_subTail): в core.py её
нет, она живёт только в пайне. Переписана с metki_prosto.pine дословно.

    python3 research/vstavki.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
import zerkalo
from zerkalo import Knees, events

PAIRS = ((5, 3, '5/5 <- 3/3'), (3, 2, '3/3 <- 2/2'))


def f_sub(sB, sH, x1, x2, s1, s2):
    """дословно f_sub из metki_prosto.pine: чередование + обрезка хвоста"""
    keep = []
    want = not s1
    for k in range(len(sB)):
        b = sB[k]
        if x1 < b < x2 and sH[k] == want:
            keep.append(k)
            want = not want
    while keep and sH[keep[-1]] == s2:
        keep.pop()
    return keep


def f_sub_notrim(sB, sH, x1, x2, s1):
    """то же, но БЕЗ обрезки — так выглядит хвост до закрытия ноги"""
    keep = []
    want = not s1
    for k in range(len(sB)):
        b = sB[k]
        if x1 < b < x2 and sH[k] == want:
            keep.append(k)
            want = not want
    return keep


def run(rows, dL, dD, dX, flip):
    """dL слой, dD донор, dX запасной донор (только для отчёта)"""
    atL, atD, atX = events(rows, dL, flip), events(rows, dD, flip), events(rows, dX, flip)
    KL, KD, KX = Knees(), Knees(), Knees()
    N = len(rows)
    half = N // 2
    # счётчики: [вся история, 1-я половина, 2-я половина]
    z = lambda: [0, 0, 0]
    st = {k: z() for k in ('ног', 'вошло', 'взято', 'выброшено',
                           'чередование', 'обрезка', 'общее колено',
                           'столкновение', 'запасной 2/2')}
    gains = []
    for i in range(N):
        for bar, price, isHi in atD.get(i, []):
            KD.push(price, bar, isHi)
        for bar, price, isHi in atX.get(i, []):
            KX.push(price, bar, isHi)
        newL = False
        for bar, price, isHi in atL.get(i, []):
            newL = KL.push(price, bar, isHi) or newL
        if not newL or len(KL.P) < 2:
            continue
        x1, x2 = KL.B[-2], KL.B[-1]
        s1, s2 = KL.H[-2], KL.H[-1]
        sl = 0 if True else 0
        h = 1 if x2 < half else 2
        def add(k, v=1):
            st[k][0] += v
            st[k][h] += v
        add('ног')
        inside = [k for k in range(len(KD.B)) if x1 < KD.B[k] < x2]
        # НЕ потеря. Пивот 5/5 — это всегда и пивот 3/3, поэтому концы
        # ноги у слоя и у донора стоят на одних барах. Считается только
        # чтобы это было видно числом и никто больше не принял за потерю
        on_bar = [k for k in range(len(KD.B)) if KD.B[k] in (x1, x2)]
        add('вошло', len(inside))
        add('общее колено', len(on_bar))
        alt = f_sub_notrim(KD.B, KD.H, x1, x2, s1)
        keep = f_sub(KD.B, KD.H, x1, x2, s1, s2)
        add('чередование', len(inside) - len(alt))
        add('обрезка', len(alt) - len(keep))
        add('взято', len(keep))
        add('выброшено', len(inside) - len(keep))
        if alt and KD.H[alt[-1]] == s2:
            add('столкновение')
        if not keep:
            kx = f_sub(KX.B, KX.H, x1, x2, s1, s2)
            if kx:
                add('запасной 2/2', len(kx))
        for k in keep:
            gains.append((x2 + dL) - (KD.B[k] + dD))
    return st, gains


def qq(v):
    if not v:
        return '—'
    v = sorted(v)
    g = lambda p: v[min(len(v) - 1, int(p * len(v)))]
    return 'мин %d  25%% %d  мед %d  75%% %d  макс %d' % (v[0], g(.25), g(.5), g(.75), v[-1])


def main():
    zerkalo.MAXK = 100          # как в пайне
    rows = load('data/XAUUSD_1h_9y.csv')
    print('баров %d   с %s по %s' % (len(rows), rows[0][0][:10], rows[-1][0][:10]))
    print('пятиминутка не трогается, запасной донор 2/2 в счёт не идёт — слово владельца\n')
    for dL, dD, nm in PAIRS:
        print('=' * 74)
        print('ПАРА ' + nm)
        for flip, dirn in ((False, 'восходящий'), (True, 'нисходящий')):
            st, gains = run(rows, dL, dD, 2, flip)
            g = lambda k, h=0: st[k][h]
            vh = g('вошло') or 1
            print('  %s: ног %d, колен донора внутри них %d' % (dirn, g('ног'), g('вошло')))
            print('      ВЗЯТО на график %d (%.1f%%)   ВЫБРОШЕНО %d (%.1f%%)'
                  % (g('взято'), 100.0 * g('взято') / vh, g('выброшено'), 100.0 * g('выброшено') / vh))
            print('      из выброшенного: чередование %d (%.1f%%)   обрезка хвоста %d (%.1f%%)'
                  % (g('чередование'), 100.0 * g('чередование') / vh,
                     g('обрезка'), 100.0 * g('обрезка') / vh))
            print('      общих колен со слоем (НЕ потеря, концы ноги): %d' % g('общее колено'))
            print('      СТОЛКНОВЕНИЕ последней вставки с коленом слоя: %d ног из %d (%.1f%%)'
                  % (g('столкновение'), g('ног'), 100.0 * g('столкновение') / max(g('ног'), 1)))
            if dL == 5:
                print('      сейчас РИСУЕТСЯ с запасного 2/2 (в счёт не пойдёт): %d меток' % g('запасной 2/2'))
            print('      выигрыш в барах, на сколько раньше донор знает: ' + qq(gains))
            for h, hn in ((1, '1-я половина'), (2, '2-я половина')):
                v2 = st['вошло'][h] or 1
                print('      %s: взято %.1f%%, обрезка %.1f%%, столкновений %.1f%% ног'
                      % (hn, 100.0 * st['взято'][h] / v2, 100.0 * st['обрезка'][h] / v2,
                         100.0 * st['столкновение'][h] / max(st['ног'][h], 1)))
        print()


if __name__ == '__main__':
    main()
