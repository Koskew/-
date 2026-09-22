# -*- coding: utf-8 -*-
"""Нисходящий = тот же движок на ПЕРЕВЁРНУТЫХ свечах. Девять лет часовика.

Идея владельца 22.09.2026: не переводить правила руками, а перевернуть
цены. Перевёрнутая свеча — знак меняется, максимум и минимум меняются
местами. Тогда пивот-вершина на перевёрнутых = пивот-низ на настоящих,
HH = LL, HL = LH, а ВОСХОДЯЩИЙ на перевёрнутых = НИСХОДЯЩИЙ на
настоящих.

Поэтому здесь ОДНА функция движка, вызванная дважды. Никакого второго
набора правил не существует — зеркало точное по построению, а не
потому, что я аккуратно переписал сорок условий.

Движок повторяет f_trend из indicator/metki_prosto.pine на 22.09.2026.
Не повторяется только подтверждение слома (флаг tBOK): он не влияет на
состояние тренда, только на толщину ноги при отрисовке.

Настройки взяты из индикатора, какими они стоят у владельца:
  глубина смерти      0.33 импульса
  правило смерти      «имп × 0.33»
  свечей подряд       4
  где искать ноль     ближайший LL, до 3 низов назад

    python3 research/zerkalo.py
"""
import csv, os, statistics as st
from core import load

FIB, NBAR, BACK, MAXK = 0.33, 4, 3, 100
OUT = 'research/out/zerkalo_9y.csv'


def pivots_d(rows, d):
    """core.pivots с глубиной d: слева >=, справа >. Ключ — бар подтверждения."""
    hi = [r[2] for r in rows]
    lo = [r[3] for r in rows]
    at = {}
    for i in range(d, len(rows) - d):
        if all(hi[i-k] <= hi[i] for k in range(1, d+1)) and all(hi[i+k] < hi[i] for k in range(1, d+1)):
            at.setdefault(i + d, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, d+1)) and all(lo[i+k] > lo[i] for k in range(1, d+1)):
            at.setdefault(i + d, []).append((i, lo[i], False))
    return at


class Knees:
    """f_push + f_relabel из metki_prosto.pine."""
    def __init__(self):
        self.P, self.B, self.H, self.L = [], [], [], []

    def relabel(self):
        self.L = []
        for i in range(len(self.P)):
            h = self.H[i]
            prev = None
            for j in range(i - 1, -1, -1):
                if self.H[j] == h:
                    prev = self.P[j]
                    break
            c = self.P[i]
            self.L.append('?' if prev is None else
                          ('HH' if c > prev else 'LH') if h else ('HL' if c > prev else 'LL'))

    def push(self, price, bar, isHi):
        same = self.P and self.H[-1] == isHi
        if same:
            better = price > self.P[-1] if isHi else price < self.P[-1]
            if better:
                self.P[-1] = price
                self.B[-1] = bar
        else:
            self.P.append(price); self.B.append(bar); self.H.append(isHi)
            if len(self.P) > MAXK:
                self.P.pop(0); self.B.pop(0); self.H.pop(0)
        self.relabel()
        return not same


class Trend:
    """f_trend: состояние одного слоя. Читает ОТКРЫТИЕ и ЗАКРЫТИЕ параметром,
    а не из свечи напрямую — это единственная правка, без которой ту же
    функцию нельзя позвать на перевёрнутом мире."""
    def __init__(self):
        self.tr = 0; self.zb = -1; self.zl = ''; self.zp = None
        self.lvl = None; self.lhl = False; self.cnt = -1; self.mx = -1
        self.imp = 0.0; self.bel = 0; self.pzb = -1
        self.born = -1
        self.trends = []          # (бар рождения, бар смерти, подпись нуля, докуда дошёл, цена нуля)
        self.alive_bars = 0

    def step(self, bar, o, c, K, nw, fr):
        if self.tr == 1:
            self.alive_bars += 1
        # 1. смерть — каждый бар
        if self.tr == 1 and self.lvl is not None:
            bLo = min(o, c)
            self.bel = self.bel + 1 if c < self.lvl else 0
            if bLo < self.lvl - self.imp * FIB:
                self.trends.append((self.born, bar, self.zl, self.mx, self.zp))
                self.tr = 0; self.cnt = -1; self.zb = -1; self.pzb = -1
                self.lvl = None; self.bel = 0
        # 2. новое колено
        n = len(K.P)
        if fr and n >= 2:
            lb, hiK, prK, bbK, ppK = K.L[-1], K.H[-1], K.P[-1], K.B[-1], K.P[-2]
            if prK > ppK:
                self.imp = prK - ppK
            if self.tr == 1:
                if nw and self.cnt >= 5 and not hiK and lb == 'HL':
                    self.pzb = self.zb; self.zb = bbK; self.zp = prK; self.zl = lb
                    self.cnt = 0; self.mx = 0; self.lvl = prK; self.lhl = True; self.bel = 0
                else:
                    if nw and self.cnt < 5:
                        self.cnt += 1; self.mx = max(self.mx, self.cnt)
                    if not hiK and lb == 'HL':
                        self.lvl = prK; self.lhl = True; self.bel = 0
            else:
                if hiK and lb == 'HH':
                    j, step_, q = -1, 0, n - 2
                    while q >= 0 and step_ < BACK:
                        if not K.H[q]:
                            step_ += 1
                            if K.L[q] == 'LL':
                                j = q
                                break
                        q -= 1
                    if j >= 0 and n - 1 - j <= 5:
                        self.tr = 1; self.born = bar
                        self.zb = K.B[j]; self.zp = K.P[j]; self.zl = K.L[j]
                        self.cnt = n - 1 - j; self.mx = self.cnt
                        self.lvl = K.P[j]; self.lhl = (self.zl == 'HL'); self.bel = 0


def run(rows, d):
    at = pivots_d(rows, d)
    K, T = Knees(), Trend()
    live = []
    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        nw = False
        for bar, price, isHi in at.get(i, []):
            nw = K.push(price, bar, isHi) or nw
        fr = i in at
        T.step(i, o, c, K, nw, fr)
        live.append(T.tr == 1)
    if T.tr == 1:
        T.trends.append((T.born, len(rows) - 1, T.zl, T.mx, T.zp))
    return T, live


def qq(v, f='%.0f'):
    if not v:
        return '—'
    v = sorted(v)
    g = lambda p: v[min(len(v)-1, int(p*len(v)))]
    return ('мин ' + f + '  25%% ' + f + '  мед ' + f + '  75%% ' + f + '  90%% ' + f + '  макс ' + f) % (
        v[0], g(.25), g(.50), g(.75), g(.90), v[-1])


rows = load('data/XAUUSD_1h_9y.csv')
flip = [(r[0], -r[1], -r[3], -r[2], -r[4]) for r in rows]   # максимум и минимум местами
print('баров %d   с %s по %s' % (len(rows), rows[0][0][:10], rows[-1][0][:10]))
print('настройки: глубина смерти 0.33 импульса, правило «имп × 0.33», ноль — ближайший назад, до 3 колен\n')

os.makedirs('research/out', exist_ok=True)
fh = open(OUT, 'w', newline='', encoding='utf-8')
w = csv.writer(fh)
w.writerow(['направление', 'слой', 'рождение', 'смерть', 'баров жил', 'ноль', 'докуда дошёл счёт'])

SW = {'LL': 'HH', 'HL': 'LH', 'HH': 'LL', 'LH': 'HL'}
res = {}
for d, nm in ((5, '5/5'), (3, '3/3'), (2, '2/2')):
    for src, dirn in ((rows, 'восходящий'), (flip, 'нисходящий')):
        T, live = run(src, d)
        res[(nm, dirn)] = (T, live)
        for b, e, zl, mx, zp in T.trends:
            z = zl if dirn == 'восходящий' else SW.get(zl, zl)
            w.writerow([dirn, nm, rows[b][0][:16], rows[e][0][:16], e - b, z, mx])
fh.close()

for d, nm in ((5, '5/5'), (3, '3/3'), (2, '2/2')):
    print('=' * 78)
    print('СЛОЙ ' + nm)
    for dirn in ('восходящий', 'нисходящий'):
        T, live = res[(nm, dirn)]
        tr = T.trends
        lifes = [e - b for b, e, _, _, _ in tr]
        rojd = sum(1 for t in tr if t[2] == 'LL')
        prod = len(tr) - rojd
        mxs = [t[3] for t in tr]
        do5 = sum(1 for m in mxs if m >= 5)
        print('  %s: трендов %4d   рождений %4d  продолжений %4d   дошли до (5) %4d (%.0f%%)'
              % (dirn, len(tr), rojd, prod, do5, 100.0*do5/max(len(tr), 1)))
        print('      жизнь, баров   ' + qq([float(x) for x in lifes]))
        print('      докуда счёт    ' + '  '.join('(%d) %d' % (k, mxs.count(k)) for k in range(6)))
        print('      баров под трендом %d из %d  (%.1f%%)' % (sum(live), len(rows), 100.0*sum(live)/len(rows)))
    # покрытие
    _, lu = res[(nm, 'восходящий')]
    _, ld = res[(nm, 'нисходящий')]
    both = sum(1 for a, b in zip(lu, ld) if a and b)
    only_u = sum(1 for a, b in zip(lu, ld) if a and not b)
    only_d = sum(1 for a, b in zip(lu, ld) if b and not a)
    none = sum(1 for a, b in zip(lu, ld) if not a and not b)
    N = len(rows)
    print('  ПОКРЫТИЕ: только восх %.1f%%   только нисх %.1f%%   ОБА сразу %.1f%%   ни одного %.1f%%'
          % (100.0*only_u/N, 100.0*only_d/N, 100.0*both/N, 100.0*none/N))
    print('            хоть какой-то тренд %.1f%%  (один восходящий давал %.1f%%)'
          % (100.0*(N-none)/N, 100.0*sum(lu)/N))
    holes, run_ = [], 0
    for a, b in zip(lu, ld):
        if not a and not b:
            run_ += 1
        elif run_:
            holes.append(float(run_)); run_ = 0
    if run_:
        holes.append(float(run_))
    print('            дыр %d, длина в барах: %s' % (len(holes), qq(holes)))
    print()
print('построчно: ' + OUT)
