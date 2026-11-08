#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПАРАМЕТРЫ ОДНОЙ СВЕЧИ ПО ВРЕМЕНИ С ГРАФИКА ВЛАДЕЛЬЦА.

    python3 research/svecha.py "2017-08-07 01:00"           # время ЕГО графика
    python3 research/svecha.py "2017-08-07 01:00" --cap 0.13 --okno 20 --sim 8 --por 2

Заведён 08.11.2026 по его вопросу: «как тебе передать данные, чтобы ты
сейчас собирал параметры этих свечей, и мы в конце посмотрели по этим
данным, как внести корректировки?»

ОТВЕТ ОКАЗАЛСЯ ПРОЩЕ, ЧЕМ ОЖИДАЛОСЬ: от него нужны только ДАТА И ВРЕМЯ.
Проверено на баре с его скрина — его шапка ОТКР 1257.850 МАКС 1258.112
МИН 1256.596 ЗАКР 1257.438 совпала с нашим `2017-08-06 23:00 UTC` ДО
ТЫСЯЧНОЙ, а все четыре числа табло пересчитались из неё точно.

ЕГО ГРАФИК ИДЁТ В UTC+2. Скрипт сам вычитает два часа.
"""
import csv, sys, os, datetime

SDVIG = 2  # его график = UTC + 2

def load(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append((r['time'][:19],
                         float(r['open']), float(r['high']),
                         float(r['low']),  float(r['close'])))
    return rows

def param(rows, i, okno):
    t, o, h, l, c = rows[i]
    rng = h - l
    if rng <= 0:
        return None
    bod = abs(c - o)
    up  = h - o if o > c else h - c
    lo  = c - l if o > c else o - l
    bodP, uppP, lowP = bod/rng*100, up/rng*100, lo/rng*100
    shk = rng/c*100 if c > 0 else 0.0
    # средняя по ПРЕДЫДУЩИМ okno свечам, как ta.sma(shk, okno)[1]
    sred = None
    if i >= okno:
        s = 0.0
        for k in range(i-okno, i):
            tk, ok, hk, lk, ck = rows[k]
            s += (hk-lk)/ck*100 if ck > 0 else 0.0
        sred = s/okno
    return dict(t=t, o=o, h=h, l=l, c=c, rng=rng, bodP=bodP,
                uppP=uppP, lowP=lowP, razn=abs(uppP-lowP),
                shk=shk, sred=sred)

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    kogda = sys.argv[1]
    a = sys.argv[2:]
    def opt(name, dflt):
        return float(a[a.index(name)+1]) if name in a else dflt
    cap  = opt('--cap', 0.40)
    okno = int(opt('--okno', 20))
    sim  = opt('--sim', 8.0)
    por  = opt('--por', 2.0)

    base = os.path.join(os.path.dirname(__file__), '..', 'data')
    rows = load(os.path.join(base, 'XAUUSD_1h_9y.csv'))

    kogda = kogda.replace('T', ' ')
    if len(kogda) == 16:
        kogda += ':00'
    dt = datetime.datetime.strptime(kogda, '%Y-%m-%d %H:%M:%S')
    utc = dt - datetime.timedelta(hours=SDVIG)
    klyuch = utc.strftime('%Y-%m-%d %H:%M:%S')

    idx = None
    for i, r in enumerate(rows):
        if r[0] == klyuch:
            idx = i; break
    if idx is None:
        print(u'НЕ НАЙДЕН бар %s (это %s UTC).' % (kogda, klyuch))
        print(u'Данные идут с %s по %s UTC.' % (rows[0][0], rows[-1][0]))
        return 1

    p = param(rows, idx, okno)
    if p is None:
        print(u'У бара нулевая высота.'); return 1

    print(u'БАР %s по его графику  =  %s UTC' % (kogda, klyuch))
    print(u'   O %.3f   H %.3f   L %.3f   C %.3f   высота %.3f' % (p['o'], p['h'], p['l'], p['c'], p['rng']))
    print()
    print(u'   тело %5.1f%%   верхний фитиль %5.1f%%   нижний %5.1f%%' % (p['bodP'], p['uppP'], p['lowP']))
    print()
    ok1 = p['razn'] <= sim
    print(u'   ФОРМА     фитили: разница %6.1f  из %.1f      %s' % (p['razn'], sim, u'прошла' if ok1 else u'НЕ прошла'))
    if p['sred'] is None:
        print(u'   РАЗМЕР    средней ещё нет: меньше %d баров истории' % okno)
        ok2 = False
    else:
        otn = p['shk']/p['sred'] if p['sred'] > 0 else 0.0
        ok2 = 0 < otn <= por
        print(u'   РАЗМЕР    %.3f%% при обычной %.3f%%  =  %.2fx из %.1fx   %s'
              % (p['shk'], p['sred'], otn, por, u'прошёл' if ok2 else u'НЕ прошёл'))
    ok3 = p['shk'] <= cap
    print(u'   ПОТОЛОК   %.3f%% из %.2f%%                     %s' % (p['shk'], cap, u'прошёл' if ok3 else u'НЕ прошёл'))
    print()
    if ok1 and ok2 and ok3:
        print(u'   ИТОГ: ТРИГГЕРНАЯ')
    elif ok1:
        print(u'   ИТОГ: срезана размером — форма подошла, не прошло: '
              + u', '.join([x for x, k in ((u'размер к соседям', ok2), (u'потолок', ok3)) if not k]))
    else:
        print(u'   ИТОГ: не триггерная, не прошла ФОРМА')
    return 0

if __name__ == '__main__':
    sys.exit(main())
