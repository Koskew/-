# -*- coding: utf-8 -*-
"""З8: встречная метка, пробившая НОЛЬ — это манипуляция или конец тренда?

Вопрос владельца 23.09.2026, слой 2/2, 31 декабря 2025. Нисходящий стоял
на счёте (2), и этой (2) оказалась HH 4353.445 — ВЫШЕ собственного нуля
LH 4337.480. Владелец: «это была не смерть нисходящего, он просто не
устоял, и получился восходящий». Движок оставил тренд живым: §2 говорит,
что встречная подпись счёт не обрывает.

Два правила владельца здесь расходятся, поэтому спрашиваем данные.

ПРИЗНАК. Внутри действующего счёта появилось колено, у которого
  · подпись ВСТРЕЧНАЯ (для восходящего низ LL, для нисходящего вершина HH);
  · цена ЗА НУЛЁМ этого счёта (ниже нуля у восходящего, выше у нисходящего).
Флаг держится до конца счёта и сбрасывается при перезапуске по §5:
новый ноль — новый отсчёт.

ЧТО МЕРИМ. В момент КАЖДОГО колена живого тренда записываем: слой,
направление, номер точки, стоит ли флаг. Дальше смотрим, что было ПОСЛЕ:
  · умер ли тренд, не дождавшись следующего колена / двух / трёх;
  · родился ли ВСТРЕЧНЫЙ тренд в те же сроки;
  · дошёл ли счёт до (5).

ПОЧЕМУ ТАК, А НЕ ПРОЩЕ. Флаг не может появиться раньше точки (1), а
длинные тренды успевают нахватать флагов просто потому, что длинные.
Поэтому сравнение идёт ВНУТРИ одной точки счёта: среди трендов, дошедших
до (c), сравниваются те, у кого флаг уже стоит, и те, у кого нет.

Нисходящий считается тем же движком на перевёрнутых свечах, поэтому
отдельного кода для него здесь нет.

    python3 research/vstrechnaya.py
"""
import csv, os
from core import load

src = open('research/zerkalo.py').read().split(chr(114) + 'ows = load(')[0]
exec(src)

OUT = 'research/out/vstrechnaya_9y.csv'
AHEAD = (1, 2, 3)


def progon(rows, d):
    """Возвращает события колен живого тренда и бары смерти."""
    at = pivots_d(rows, d)
    K, T = Knees(), Trend()
    ev = []          # (бар, id тренда, номер точки, флаг)
    live = []        # жив ли тренд на этом баре
    tid = 0
    flag = False
    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        nw = False
        for bar, price, isHi in at.get(i, []):
            nw = K.push(price, bar, isHi) or nw
        fr = i in at
        tr0, cnt0, zb0 = T.tr, T.cnt, T.zb
        T.step(i, o, c, K, nw, fr)
        if T.tr == 1 and tr0 != 1:                 # рождение
            tid += 1
            flag = False
        if T.tr == 1 and T.zb != zb0:              # перезапуск §5: новый ноль
            flag = False
        if T.tr == 1 and fr and len(K.P) >= 2 and (T.cnt != cnt0 or T.zb != zb0):
            # встречная подпись, ушедшая ЗА НОЛЬ
            if (not K.H[-1]) and K.L[-1] == 'LL' and T.zp is not None and K.P[-1] < T.zp:
                flag = True
            ev.append((i, tid, T.cnt, flag))
        live.append(T.tr == 1)
    return ev, live, T


def q(a, b):
    return '%5.1f%%' % (100.0 * a / b) if b else '  —  '


rows = load('data/XAUUSD_1h_9y.csv')
flip = [(r[0], -r[1], -r[3], -r[2], -r[4]) for r in rows]
N = len(rows)
print('баров %d   с %s по %s\n' % (N, rows[0][0][:10], rows[-1][0][:10]))

os.makedirs('research/out', exist_ok=True)
fh = open(OUT, 'w', newline='', encoding='utf-8')
w = csv.writer(fh)
w.writerow(['слой', 'направление', 'точка счёта', 'флаг', 'случаев',
            'умер до 1 колена', 'умер до 2', 'умер до 3',
            'встречный родился до 1', 'до 2', 'до 3', 'дошёл до (5)'])

for d, nm in ((5, '5/5'), (3, '3/3'), (2, '2/2')):
    evU, liveU, TU = progon(rows, d)
    evD, liveD, TD = progon(flip, d)
    for dirn, ev, own, opp in (('восходящий', evU, liveU, liveD),
                               ('нисходящий', evD, liveD, liveU)):
        # для каждого события — бары следующих колен того же тренда
        byid = {}
        for k, (b, t, c, f) in enumerate(ev):
            byid.setdefault(t, []).append(k)
        print('=' * 96)
        print('СЛОЙ %s · %s' % (nm, dirn))
        print('  точка   флаг      n     умер до 1/2/3 колена      встречный родился до 1/2/3     дошёл до (5)')
        for c in range(1, 6):
            for fl in (True, False):
                sel = [k for k, (b, t, cc, f) in enumerate(ev) if cc == c and f == fl]
                if not sel:
                    continue
                died = [0, 0, 0]
                born = [0, 0, 0]
                to5 = 0
                for k in sel:
                    b, t, cc, f = ev[k]
                    sib = byid[t]
                    pos = sib.index(k)
                    for ai, a in enumerate(AHEAD):
                        # бар a-го следующего колена этого же тренда, либо конец
                        nxt = ev[sib[pos + a]][0] if pos + a < len(sib) else None
                        end = nxt if nxt is not None else N - 1
                        if any(not own[x] for x in range(b + 1, end + 1)):
                            died[ai] += 1
                        if any(opp[x] for x in range(b + 1, end + 1)):
                            born[ai] += 1
                    if any(ev[x][2] >= 5 for x in sib[pos:]):
                        to5 += 1
                n = len(sel)
                print('   (%d)   %-5s %5d    %s %s %s     %s %s %s        %s'
                      % (c, 'ДА' if fl else 'нет', n,
                         q(died[0], n), q(died[1], n), q(died[2], n),
                         q(born[0], n), q(born[1], n), q(born[2], n), q(to5, n)))
                w.writerow([nm, dirn, c, 'да' if fl else 'нет', n,
                            died[0], died[1], died[2], born[0], born[1], born[2], to5])
        print()
fh.close()
print('построчно: ' + OUT)
