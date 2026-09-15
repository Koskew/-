# -*- coding: utf-8 -*-
"""Библиотека трендов на слое 3/3 с подтверждённым правилом слома.

Правило: тело закрытой свечи ушло за штрих-пунктир на имп x 0.33
(Н6, выбор владельца), храповик опоры включён, рывок 0.5, провизорный
уровень включён. Всё через research/core.py.

Чем отличается от старой библиотеки (5/5 и 2/2, два года, до храповика):
  * слой один — 3/3;
  * девять лет вместо двух, и каждая таблица повторена по половинам;
  * «ход» больше не показывается сырым. Золото за девять лет прошло
    +248%, в сыром виде любой лонг выигрывает. Считается НАДБАВКА к
    слепому удержанию той же длины в ту же сторону.

Пишет research/out/trends_33_*.csv — открывается в Excel.
"""
import sys, os, csv, statistics as st
sys.path.insert(0, 'research')
from core import Core, up

OUT = 'research/out'
os.makedirs(OUT, exist_ok=True)


def load(path):
    out = []
    for r in csv.DictReader(open(path, encoding='utf-8-sig')):
        o, h, l, c = float(r['open']), float(r['high']), float(r['low']), float(r['close'])
        out.append((r['time'], min(max(o, l), h), h, l, min(max(c, l), h)))
    return out


def pivots_n(rows, N):
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
    for i in range(N, len(rows) - N):
        if all(hi[i-k] <= hi[i] for k in range(1, N+1)) and all(hi[i+k] < hi[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, N+1)) and all(lo[i+k] > lo[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, lo[i], False))
    return at


class Blind:
    """Слепое удержание: средний ход рынка за D баров. Эталон для надбавки."""
    def __init__(self, rows):
        c = [r[4] for r in rows]
        self.c = c
        self.pref = [0.0]
        for x in c: self.pref.append(self.pref[-1] + x)
        self.n = len(c)

    def move(self, D):
        if D <= 0 or D >= self.n: return 0.0
        m = self.n - D
        tail = self.pref[self.n] - self.pref[D]        # сумма c[D:]
        head = self.pref[m] - self.pref[0]             # сумма c[:n-D]
        return (tail - head) / m


def collect(rows, lb=3, fib=0.33):
    """Каждый тренд от подтверждения до слома, со всеми обстоятельствами."""
    co = Core(rows, fib=fib, jump=0.5, ratchet=True)
    co.at = pivots_n(rows, lb)
    bl = Blind(rows)
    trends, cur, prevActive = [], None, False

    # колена слоя одним проходом — для подсчёта мутных внутри тренда
    K = []
    for b in sorted(co.at):
        for bar, price, isHi in co.at[b]:
            if K and K[-1][2] == isHi:
                if (price > K[-1][1]) == isHi: K[-1] = (b, price, isHi, K[-1][3] + 1)
                else: K[-1] = (K[-1][0], K[-1][1], isHi, K[-1][3] + 1)
            else:
                K.append((b, price, isHi, 1))

    for b in range(len(rows)):
        n0 = len(co.log)
        co.step(b)
        ev = [e for _, e, _ in co.log[n0:]]
        active = co.tr != 0 and not co.inTrans

        if cur is not None and 'СМЕРТЬ' in ev:
            c = rows[b][4]
            D = b - cur['start']
            imp = cur['imp'] if cur['imp'] > 0 else 1e-9
            gone = (c - cur['pStart']) * cur['dir']
            cur.update(end=b, dur=D, pEnd=c, deathLvl=co.pD,
                       moveImp=gone / imp,
                       addImp=(gone - bl.move(D) * cur['dir']) / imp,
                       mfeImp=(cur['ext'] - cur['pStart']) * cur['dir'] / imp)
            ins = [k for k in K if cur['start'] <= k[0] <= b]
            cur['knees'] = len(ins)
            cur['mud'] = sum(1 for k in ins if k[3] >= 2)
            # что было в первые 20 баров — для нормировки
            i20 = [k for k in K if cur['start'] <= k[0] <= cur['start'] + 20]
            cur['mud20'] = sum(1 for k in i20 if k[3] >= 2)
            trends.append(cur); cur = None

        if active and not prevActive:
            cs = co.cstart()
            cur = dict(dir=co.tr, start=b, tStart=rows[b][0][:16],
                       born='рывок' if 'РЫВОК' in ev else ('пауза' if 'ПАУЗА' in ev else 'первый'),
                       pStart=rows[b][4], imp=co.imp, prov=co.lvlProv,
                       zeroBar=co.KB[cs] if cs >= 0 else b,
                       ext=rows[b][4], maxKN=0, kn20=0)
        if cur is not None:
            h, l = rows[b][2], rows[b][3]
            cur['ext'] = max(cur['ext'], h) if cur['dir'] == 1 else min(cur['ext'], l)
            if co.KN:
                cur['maxKN'] = max(cur['maxKN'], co.KN[-1])
                if b <= cur['start'] + 20:
                    cur['kn20'] = max(cur['kn20'], co.KN[-1])
        prevActive = active
    return trends


def med(x): return st.median(x) if x else float('nan')
def sh(x):  return '%+.2f' % x if x == x else '  —  '


def раздел1(tag, T, n):
    print('\n══ %s · %d трендов на %d барах' % (tag, len(T), n))
    print('   %-12s %4s  %-16s %8s %9s %7s' %
          ('', 'шт', 'жизнь мед/90/макс', 'ход', 'НАДБАВКА', 'доля +'))
    for d, name in ((1, 'восходящий'), (-1, 'нисходящий')):
        g = [t for t in T if t['dir'] == d]
        if not g: continue
        L = sorted(t['dur'] for t in g)
        a = [t['addImp'] for t in g]
        print('   %-12s %4d  %5d %5d %5d %8s %9s %6.0f%%' %
              (name, len(g), L[len(L)//2], L[int(len(L)*.9)], L[-1],
               sh(med([t['moveImp'] for t in g])), sh(med(a)),
               sum(1 for x in a if x > 0) / len(a) * 100))


def раздел2(T):
    print('\n══ Чем подтверждён тренд')
    print('   %-12s %-8s %5s %7s %9s %7s' % ('', '', 'шт', 'жизнь', 'НАДБАВКА', 'доля +'))
    for d, name in ((1, 'восходящий'), (-1, 'нисходящий')):
        for born in ('пауза', 'рывок'):
            g = [t for t in T if t['dir'] == d and t['born'] == born]
            if not g: continue
            a = [t['addImp'] for t in g]
            print('   %-12s %-8s %5d %7.0f %9s %6.0f%%' %
                  (name, born, len(g), med([t['dur'] for t in g]), sh(med(a)),
                   sum(1 for x in a if x > 0) / len(a) * 100))


def раздел3(T):
    print('\n══ Докуда дошёл счёт и что это дало')
    print('   %-14s %5s %7s %9s %7s' % ('счёт дошёл до', 'шт', 'жизнь', 'НАДБАВКА', 'доля +'))
    for k in range(6):
        g = [t for t in T if t['maxKN'] == k]
        if not g: continue
        a = [t['addImp'] for t in g]
        print('   (%d)%-11s %5d %7.0f %9s %6.0f%%' %
              (k, '', len(g), med([t['dur'] for t in g]), sh(med(a)),
               sum(1 for x in a if x > 0) / len(a) * 100))


def раздел4(T):
    print('\n══ Нормировка на первые 20 баров — тавтология или признак')
    live = [t for t in T if t['dur'] > 20]
    print('   в выборке только дожившие до 20 баров: %d' % len(live))
    for key, name, groups in (('mud20', 'мутных колен за 20б', ((0, 0), (1, 9))),
                              ('kn20',  'счёт дошёл за 20б',   ((0, 2), (3, 5)))):
        print('   %s' % name)
        for lo, hi in groups:
            g = [t for t in live if lo <= t[key] <= hi]
            if not g: continue
            a = [t['addImp'] for t in g]
            print('      %-8s %5d шт · проживёт ЕЩЁ %4.0f б · НАДБАВКА за остаток %s' %
                  ('%d-%d' % (lo, hi) if lo != hi else str(lo), len(g),
                   med([t['dur'] - 20 for t in g]), sh(med(a))))


def раздел5(T):
    z = [t['end'] - t['zeroBar'] for t in T]
    p = [t['dur'] for t in T]
    z.sort(); p.sort()
    print('\n══ Опоздание')
    print('   от точки (0) счёта до слома : медиана %3d б, 90-й %3d б' % (z[len(z)//2], z[int(len(z)*.9)]))
    print('   от подтверждения до слома   : медиана %3d б, 90-й %3d б' % (p[len(p)//2], p[int(len(p)*.9)]))
    print('   счёт стартует раньше подтверждения на %d баров медианой' % (z[len(z)//2] - p[len(p)//2]))


def dump(name, T):
    cols = ['dir', 'tStart', 'start', 'end', 'dur', 'born', 'prov', 'pStart', 'pEnd',
            'imp', 'moveImp', 'addImp', 'mfeImp', 'maxKN', 'kn20', 'knees', 'mud', 'mud20',
            'zeroBar', 'deathLvl']
    with open('%s/%s.csv' % (OUT, name), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for t in T: w.writerow(t)


if __name__ == '__main__':
    h1 = load('data/XAUUSD_1h_9y.csv')
    m5 = load('data/XAUUSD_5m.csv')
    mid = len(h1) // 2

    T = collect(h1)
    раздел1('1H · 9 лет', T, len(h1))
    раздел1('1H · первая половина', collect(h1[:mid]), mid)
    раздел1('1H · вторая половина', collect(h1[mid:]), len(h1) - mid)
    T5 = collect(m5)
    раздел1('5m · 3.5 мес', T5, len(m5))

    раздел2(T)
    раздел3(T)
    раздел4(T)
    раздел5(T)

    dump('trends_33_9y', T)
    dump('trends_33_5m', T5)
    print('\nфайлы: %s/trends_33_9y.csv, trends_33_5m.csv' % OUT)
