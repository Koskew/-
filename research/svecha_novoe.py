#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЗАМЕР НОВОГО ПРАВИЛА ФОРМЫ ПРОТИВ СТАРОГО, по его разметке 90 клеток.

    python3 research/svecha_novoe.py

Параметры СОГЛАСОВАНЫ до прогона, его слово «мерь» 08.11.2026:

  СТАРОЕ условие формы   разница фитилей <= 8 п.п. высоты
  НОВОЕ  условие формы   перекос 33.3-66.7%  И  тело < 70% высоты
  размер к соседям       <= 2.0 средней по 20 предыдущим  — НЕ ТРОГАЕТСЯ
  потолок по цене        считается НЕСКОЛЬКИМИ значениями, потому что
                         он сам его крутит вручную: его слово «у меня
                         ещё есть фильтр высоты, который тоже обрежет
                         часть свечей, который я вношу вручную»

Эталон для оценки — ЕГО РАЗМЕТКА 90 клеток от 08.11.2026.
"""
import csv, os, sys

BUK = u'АБВГДЕЖЗИК'
DA  = u'А5 Б5 В4 В5 В6 Г5 Д4 Д5 Д6 Е4 Е5 Е6'.split()
SKD = u'А4 А6 Б4 Б6 В3 Г4 Г6 Ж4 Ж5 Ж6'.split()
TYA = u'Е3 З5 И5'.split()
SKN = u'З4 З6 З7'.split()
GRP = {}
for g, lst in ((u'да', DA), (u'скорее да', SKD), (u'тяжело', TYA), (u'скорее нет', SKN)):
    for a in lst:
        GRP[a] = g
for b in BUK:
    for k in range(1, 10):
        GRP.setdefault(b+str(k), u'нет')

SIM, POR, OKNO = 8.0, 2.0, 20
NIZ, VERH, TELO = 100.0/3.0, 200.0/3.0, 70.0
CAPS = [None, 1.00, 0.60, 0.40, 0.30, 0.20, 0.13]

def load(p):
    r = []
    with open(p, newline='', encoding='utf-8') as f:
        for x in csv.DictReader(f):
            r.append((float(x['open']), float(x['high']), float(x['low']), float(x['close'])))
    return r

def adres(b, up, lo):
    w = up+lo
    pk = 50.0 if w <= 0 else max(0.0, min(100.0, up/w*100.0))
    return BUK[min(int(b//10.0), 9)] + str(min(int(pk//(100.0/9.0)), 8)+1)

def prognon(rows, imya):
    n = len(rows)
    shk = [0.0]*n; par = [None]*n
    for i in range(n):
        o, h, l, c = rows[i]
        rng = h-l
        if rng <= 0 or c <= 0:
            continue
        shk[i] = rng/c*100.0
        bod = abs(c-o)
        up = h-o if o > c else h-c
        lo = c-l if o > c else o-l
        par[i] = (bod/rng*100.0, up/rng*100.0, lo/rng*100.0)
    sred = [None]*n
    for i in range(OKNO, n):
        s = sum(shk[i-OKNO:i])/OKNO
        sred[i] = s if s > 0 else None
    dlg = []
    for i in range(n):
        if par[i] is not None:
            dlg.append(shk[i])
    srDlg = sum(dlg)/len(dlg) if dlg else 0.0

    hoch = set(DA) | set(SKD)
    itog = {}
    for star in (True, False):
        for cap in CAPS:
            vz = 0; vz_h = 0; vz_n = 0
            for i in range(n):
                if par[i] is None:
                    continue
                b, up, lo = par[i]
                if star:
                    f = abs(up-lo) <= SIM
                else:
                    w = up+lo
                    pk = 50.0 if w <= 0 else up/w*100.0
                    f = (NIZ <= pk <= VERH) and b < TELO
                if not f:
                    continue
                if sred[i] is None or shk[i]/sred[i] > POR:
                    continue
                if cap is not None and shk[i] > cap:
                    continue
                vz += 1
                a = adres(b, up, lo)
                if a in hoch:
                    vz_h += 1
                elif GRP[a] == u'нет':
                    vz_n += 1
            itog[(star, cap)] = (vz, vz_h, vz_n)

    vsego = sum(1 for p in par if p is not None)
    hoch_n = 0
    for i in range(n):
        if par[i] is None:
            continue
        if adres(*par[i]) in hoch:
            hoch_n += 1
    print()
    print(u'═' * 94)
    print(u'%s · %d баров с высотой · средняя высота %.3f%% цены' % (imya, vsego, srDlg))
    print(u'в его «да + скорее да» лежит %d свечей (%.1f%% баров) — это ЦЕЛЬ' % (hoch_n, 100.0*hoch_n/vsego))
    print()
    print(u'  потолок      СТАРОЕ правило                     НОВОЕ правило')
    print(u'   %% цены   взято   из цели   лишних            взято   из цели   лишних')
    for cap in CAPS:
        s = itog[(True, cap)]; nn = itog[(False, cap)]
        cp = u'  нет  ' if cap is None else u' %5.2f ' % cap
        print(u'  %s  %6d  %5.1f%%   %5d %4.1f%%      %6d  %5.1f%%   %5d %4.1f%%'
              % (cp, s[0], 100.0*s[1]/hoch_n, s[2], 100.0*s[2]/s[0] if s[0] else 0,
                 nn[0], 100.0*nn[1]/hoch_n, nn[2], 100.0*nn[2]/nn[0] if nn[0] else 0))
    print()
    print(u'  «из цели» — сколько процентов его «да+скорее да» правило нашло')
    print(u'  «лишних»  — сколько из взятого лежит в его «нет»')

base = os.path.join(os.path.dirname(__file__), '..', 'data')
prognon(load(os.path.join(base, 'XAUUSD_1h_9y.csv')), u'XAUUSD 1H · девять лет')
prognon(load(os.path.join(base, 'XAUUSD_5m.csv')),    u'XAUUSD 5m · 3.5 месяца')
