# -*- coding: utf-8 -*-
"""Реплика нового движка: тренд = счёт. Повторяет metki_33.pine шаг в шаг.

Порядок в подтверждённом баре:
  1  слом: тело прошло уровень на fib импульса -> счёт кончается
  2  новые колена
  3  счёт упёрся в maxPt и появилось лишнее колено -> счёт кончается
  4  закрываем счёт, запоминаем прошлый
  5  счёта нет — ищем законный ноль назад по коленам
  6  номера точек, уровень, импульс
"""
import csv, statistics as st, collections

MAXK = 80

def load(p):
    out = []
    for r in csv.DictReader(open(p, encoding='utf-8-sig')):
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

class Eng:
    def __init__(self, rows, N=3, fib=0.33, maxPt=5, contPt=3):
        self.rows = rows; self.N = N; self.fib = fib
        self.maxPt = maxPt; self.contPt = contPt
        self.at = pivots_n(rows, N)
        self.KP=[]; self.KB=[]; self.KH=[]; self.KL=[]; self.KM=[]; self.KA=[]; self.KN=[]; self.KD=[]
        self.cz=-1; self.czPrev=-1; self.cdir=0; self.lvl=None; self.imp=0.0
        self.pDir=0; self.pMax=0; self.pZeroP=None; self.pZeroB=None; self.pZeroL=''
        self.pEndP=None; self.pEndB=None; self.pWhy=''; self.pBars=0
        self.log=[]                 # завершённые счёта

    def _relabel(self):
        self.KL = []
        for i in range(len(self.KP)):
            h = self.KH[i]; prev = None
            for j in range(i-1, -1, -1):
                if self.KH[j] == h: prev = self.KP[j]; break
            c = self.KP[i]
            self.KL.append('?' if prev is None else
                           ('HH' if c > prev else 'LH') if h else ('HL' if c > prev else 'LL'))

    def _push(self, price, bar, isHi):
        n = len(self.KP)
        same = n > 0 and self.KH[n-1] == isHi
        fresh = trimmed = False
        if same:
            old = self.KP[n-1]
            better = price > old if isHi else price < old
            self.KM[n-1] += 1
            if self.KA[n-1] is None: self.KA[n-1] = old
            if better: self.KP[n-1] = price; self.KB[n-1] = bar
        else:
            self.KP.append(price); self.KB.append(bar); self.KH.append(isHi)
            self.KM.append(1); self.KA.append(None); fresh = True
            if len(self.KP) > MAXK:
                for a in (self.KP, self.KB, self.KH, self.KM, self.KA): a.pop(0)
                trimmed = True
        self._relabel()
        return fresh, trimmed

    def _renumber(self):
        n = len(self.KP)
        self.KN = [-1]*n
        if 0 <= self.cz < n:
            for i in range(self.cz, min(n, self.cz + self.maxPt + 1)):
                self.KN[i] = i - self.cz

    def _state(self):
        n = len(self.KP); L = None; I = 0.0
        if 0 <= self.cz < n and self.cdir != 0:
            want = 'HL' if self.cdir == 1 else 'LH'
            for j in range(min(n-1, self.cz + self.maxPt), self.cz, -1):
                if self.KL[j] == want: L = self.KP[j]; break
            if L is None: L = self.KP[self.cz]
            for k in range(min(n-1, self.cz + self.maxPt), self.cz, -1):
                p1, p0 = self.KP[k], self.KP[k-1]
                if (self.cdir == 1 and p1 > p0) or (self.cdir == -1 and p1 < p0):
                    I = abs(p1 - p0); break
            if I <= 0 and n > self.cz + 1:
                I = abs(self.KP[self.cz+1] - self.KP[self.cz])
        return L, I

    def _findZero(self):
        for i in range(len(self.KL)-1, self.czPrev, -1):
            if i < 0: break
            lb = self.KL[i]; dd = 0
            if lb == 'HH': dd = -1
            elif lb == 'LL': dd = 1
            elif self.pMax >= self.contPt and self.pDir == -1 and lb == 'LH': dd = -1
            elif self.pMax >= self.contPt and self.pDir == 1 and lb == 'HL': dd = 1
            if dd: return i, dd
        return -1, 0

    def step(self, b):
        o, h, l, c = self.rows[b][1], self.rows[b][2], self.rows[b][3], self.rows[b][4]
        endNow = False; why = ''; endMax = 0
        if self.cz >= 0 and self.cdir and self.lvl is not None and self.imp > 0:
            bLo, bHi = min(o, c), max(o, c); need = self.imp * self.fib
            if (self.cdir == 1 and bLo < self.lvl - need) or (self.cdir == -1 and bHi > self.lvl + need):
                endNow = True; why = 'слом'
                endMax = min(len(self.KP) - 1 - self.cz, self.maxPt)
        for (bar, price, isHi) in self.at.get(b, []):
            fr, tr = self._push(price, bar, isHi)
            if fr: self.KD.append(0)
            if tr:
                self.KD.pop(0)
                self.cz = self.cz - 1 if self.cz > 0 else (-1 if self.cz == 0 else self.cz)
                self.czPrev = self.czPrev - 1 if self.czPrev > 0 else (-1 if self.czPrev == 0 else self.czPrev)
        if self.cz >= 0 and not endNow and len(self.KP) - 1 > self.cz + self.maxPt:
            endNow = True; why = f'дошёл до ({self.maxPt})'; endMax = self.maxPt
        if endNow and 0 <= self.cz < len(self.KP):
            self.pDir = self.cdir; self.pMax = endMax
            self.pZeroP = self.KP[self.cz]; self.pZeroB = self.KB[self.cz]; self.pZeroL = self.KL[self.cz]
            self.pEndP = self.lvl if why == 'слом' else c
            self.pEndB = b; self.pBars = b - self.pZeroB; self.pWhy = why
            self.log.append(dict(dir=self.pDir, mx=self.pMax, zl=self.pZeroL,
                                 zb=self.pZeroB, eb=b, bars=self.pBars, why=why))
            self.czPrev = self.cz; self.cz = -1; self.cdir = 0
            self.lvl = None; self.imp = 0.0
        if self.cz < 0:
            z, d = self._findZero()
            if z >= 0: self.cz = z; self.cdir = d
        self._renumber()
        self.lvl, self.imp = self._state()
        if self.cz >= 0:
            for i in range(self.cz, min(len(self.KD), self.cz + self.maxPt + 1)):
                self.KD[i] = self.cdir

if __name__ == '__main__':
    for tag, path in (('9 лет', 'data/XAUUSD_1h_9y.csv'), ('2 года', 'data/XAUUSD_1h_2y.csv')):
        rows = load(path)
        for N in (5, 3, 2):
            e = Eng(rows, N=N)
            noCount = 0
            for b in range(len(rows)):
                e.step(b)
                if e.cz < 0: noCount += 1
            L = e.log
            zl = collections.Counter(x['zl'] for x in L)
            why = collections.Counter(x['why'] for x in L)
            mx = collections.Counter(x['mx'] for x in L)
            bars = [x['bars'] for x in L]
            print(f'══ {tag} · {N}/{N} · счётов {len(L)} · без счёта {noCount/len(rows):.1%} баров')
            print(f'   подпись нуля : ' + '  '.join(f'{k} {v} ({v/len(L):.0%})' for k, v in zl.most_common()))
            print(f'   чем кончился : ' + '  '.join(f'{k} {v} ({v/len(L):.0%})' for k, v in why.most_common()))
            print(f'   дошёл до     : ' + '  '.join(f'({k}) {mx[k]} ({mx[k]/len(L):.0%})' for k in sorted(mx)))
            print(f'   прожил баров : медиана {st.median(bars):.0f}  среднее {st.mean(bars):.0f}  '
                  f'максимум {max(bars)}')
            print()
