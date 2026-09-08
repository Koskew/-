# -*- coding: utf-8 -*-
"""Эталонная реплика ГДЕ МЫ v4. Порядок операций в баре повторяет Pine.

Расхождения реплики и индикатора уже дважды портили выводы, поэтому все
замеры должны идти отсюда, а не из отдельных копий логики.

Порядок в подтверждённом баре, как в gde_my_v4.pine:
  1  смерть тренда (нужен уровень, защита от повторного слома)
  1б досрочное подтверждение по рывку
  2  новые колена: слияние или новое, метки и счёт пересчитываются
  3  импульсное колено                     — только на новом колене
  4  рождение или подтверждение тренда     — только на новом колене
  5  уровень тренда                        — КАЖДЫЙ бар, но не в ПЕРЕХОДЕ
  6  тренд и флаг ПЕРЕХОДА у колена        — только на новом колене
"""
import csv

L = R = 5
MAXK = 80          # как в Pine: массив колен обрезается сверху
up = lambda l: l in ("HH", "HL")


def load(path='data/XAUUSD_1h_2y.csv'):
    return [(r['time'], float(r['open']), float(r['high']), float(r['low']), float(r['close']))
            for r in csv.DictReader(open(path, encoding='utf-8-sig'))]


def pivots(rows):
    """ta.pivothigh / ta.pivotlow: >= слева, > справа. Видно через R баров."""
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
    for i in range(L, len(rows) - R):
        if all(hi[i-k] <= hi[i] for k in range(1, L+1)) and all(hi[i+k] < hi[i] for k in range(1, R+1)):
            at.setdefault(i + R, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, L+1)) and all(lo[i+k] > lo[i] for k in range(1, R+1)):
            at.setdefault(i + R, []).append((i, lo[i], False))
    return at


class Core:
    def __init__(self, rows, fib=0.33, jump=0.5, prov=True, gateLvl=True):
        self.rows, self.at = rows, pivots(rows)
        self.fib, self.jump, self.prov, self.gateLvl = fib, jump, prov, gateLvl
        self.KP = []; self.KH = []; self.KL = []; self.KN = []
        self.KM = []; self.KT = []; self.KX = []; self.KB = []
        self.tr = 0; self.lvl = None; self.imp = 0.0; self.trFrom = None
        self.inTrans = False; self.marks = 0; self.lastD = None; self.lvlProv = False
        self.pTr = 0; self.pD = None; self.pDb = None
        self.log = []          # (бар, событие, текст)
        self.lives = []        # длительность жизни трендов
        self.spans = []        # длительность ПЕРЕХОДОВ
        self.trBars = 0        # баров в ПЕРЕХОДЕ
        self._trStart = None

    def _relabel(self):
        self.KL.clear()
        for i in range(len(self.KP)):
            h = self.KH[i]; prev = None
            for j in range(i-1, -1, -1):
                if self.KH[j] == h: prev = self.KP[j]; break
            self.KL.append("?" if prev is None else
                           (("HH" if self.KP[i] > prev else "LH") if h else
                            ("HL" if self.KP[i] > prev else "LL")))

    def _recount(self):
        n = len(self.KL)
        self.KN[:] = [-1] * n
        if n < 2: return
        o, d, g = 0, 1 if up(self.KL[1]) else -1, 0
        while g < 500:
            g += 1
            pts, i = 0, o + 1
            while i < n and pts < 5:
                if up(self.KL[i]) != (d > 0): break
                pts += 1; i += 1
            for k in range(pts + 1):
                if o + k < n: self.KN[o + k] = k
            e = o + pts; x = e + 1
            if x >= n: break
            nd = d if pts == 5 else (1 if up(self.KL[x]) else -1)
            j = next((q for q in range(x, -1, -1) if self.KH[q] == (nd < 0)), -1)
            if j <= o: j = x
            o, d = j, nd

    def _push(self, bar, price, isHi):
        """f_pushKnee: серия одной стороны схлопывается в свой экстремум."""
        n = len(self.KP)
        same = n > 0 and self.KH[n-1] == isHi
        fresh = False
        if same:
            better = (price > self.KP[n-1]) if isHi else (price < self.KP[n-1])
            self.KM[n-1] += 1
            if better:
                if self.KM[n-1] == 2: pass
                self.KP[n-1] = price; self.KB[n-1] = bar
        else:
            self.KP.append(price); self.KH.append(isHi); self.KB.append(bar)
            self.KM.append(1); self.KT.append(self.tr); self.KX.append(self.inTrans)
            fresh = True
            if len(self.KP) > MAXK:
                for a in (self.KP, self.KH, self.KB, self.KM, self.KT, self.KX):
                    a.pop(0)
        self._relabel(); self._recount()
        return fresh

    def step(self, b):
        rows = self.rows
        o, h, l, c = rows[b][1], rows[b][2], rows[b][3], rows[b][4]
        bLo, bHi = min(o, c), max(o, c)
        if self.inTrans: self.trBars += 1

        # 1. смерть
        if self.lvl is not None and self.tr != 0:
            need = self.imp * self.fib
            died = (self.tr == 1 and bLo < self.lvl - need) or \
                   (self.tr == -1 and bHi > self.lvl + need)
            if died and self.lastD is not None and abs(self.lvl - self.lastD) < 1e-9:
                died = False
            if died:
                self.log.append((b, 'СМЕРТЬ', f'{"восх" if self.tr==1 else "нисх"} на {self.lvl:.3f}'))
                if self.trFrom is not None: self.lives.append(b - self.trFrom)
                self.pTr, self.pD, self.pDb = self.tr, self.lvl, b
                self.lastD = self.lvl
                self.inTrans = True; self.marks = 0; self.lvl = None; self.lvlProv = False
                self._trStart = b

        # 1б. рывок
        if self.jump > 0 and self.inTrans and self.imp > 0 and self.lastD is not None and len(self.KL) >= 2:
            j1, j2 = self.KL[-1], self.KL[-2]
            ju = up(j1) and up(j2); jd = (not up(j1)) and (not up(j2))
            far = (jd and c < self.lastD - self.imp * self.jump) or \
                  (ju and c > self.lastD + self.imp * self.jump)
            if far:
                dl = self.lastD
                self.tr = 1 if ju else -1
                self.trFrom = b; self.inTrans = False; self.lastD = None; self.lvl = None
                if self._trStart is not None: self.spans.append(b - self._trStart)
                self.log.append((b, 'РЫВОК', f'{"восх" if self.tr==1 else "нисх"} по {c:.3f}'))
                if self.prov:
                    self.lvl = dl; self.lvlProv = True

        # 2. новые колена
        fresh = False
        for bar, price, isHi in self.at.get(b, []):
            if self._push(bar, price, isHi): fresh = True
        if fresh: self.marks += 1

        n = len(self.KL)
        if n >= 2:
            l1, l2 = self.KL[-1], self.KL[-2]
            p1, p2 = self.KP[-1], self.KP[-2]
            if fresh:
                # 3. импульсное колено
                if self.tr != 0 and ((self.tr == 1) == (p1 > p2)):
                    self.imp = abs(p1 - p2)
                # 4. рождение или подтверждение
                u2 = up(l1) and up(l2); d2 = (not up(l1)) and (not up(l2))
                if self.tr == 0:
                    if u2 or d2:
                        self.tr = 1 if u2 else -1; self.trFrom = b; self.imp = abs(p1 - p2)
                elif self.inTrans and self.marks >= 2 and (u2 or d2):
                    if self._trStart is not None: self.spans.append(b - self._trStart)
                    self.tr = 1 if u2 else -1
                    self.trFrom = b; self.inTrans = False; self.lastD = None
                    self.lvlProv = False; self.imp = abs(p1 - p2)
                    self.log.append((b, 'ПАУЗА', f'{"восх" if self.tr==1 else "нисх"}'))
            # 5. уровень — каждый бар, но не в ПЕРЕХОДЕ
            gate = (not self.inTrans) if self.gateLvl else True
            if gate and self.tr == 1:
                if l1 == "HL": self.lvl = p1; self.lvlProv = False
                if self.lvl is None:
                    self.lvl = next((self.KP[j] for j in range(n-1, -1, -1) if self.KL[j] == "HL"), None)
            elif gate and self.tr == -1:
                if l1 == "LH": self.lvl = p1; self.lvlProv = False
                if self.lvl is None:
                    self.lvl = next((self.KP[j] for j in range(n-1, -1, -1) if self.KL[j] == "LH"), None)
            # 6. тренд и флаг ПЕРЕХОДА у колена — один раз, на баре появления
            if fresh and self.KT:
                self.KT[-1] = self.tr; self.KX[-1] = self.inTrans

    def run(self, upto=None):
        for b in range(len(self.rows) if upto is None else upto + 1):
            self.step(b)
        return self

    # ── производные величины ──
    def cstart(self):
        return next((i for i in range(len(self.KN)-1, -1, -1) if self.KN[i] == 0), -1)

    def cdir(self):
        cs = self.cstart()
        if cs < 0: return 0
        if cs + 1 < len(self.KL): return 1 if up(self.KL[cs+1]) else -1
        return -1 if self.KH[cs] else 1

    def room(self, c):
        """оставшийся ход до порога смерти, в импульсах"""
        if self.lvl is None or self.tr == 0 or self.imp <= 0 or self.inTrans: return None
        thr = self.lvl - self.imp*self.fib if self.tr == 1 else self.lvl + self.imp*self.fib
        return max(0.0, (c - thr) if self.tr == 1 else (thr - c)) / self.imp


if __name__ == '__main__':
    rows = load()
    co = Core(rows).run()
    print(f'баров {len(rows)}, колен {len(co.KP)}')
    print(f'сломов {sum(1 for _,e,_ in co.log if e=="СМЕРТЬ")}, '
          f'рывков {sum(1 for _,e,_ in co.log if e=="РЫВОК")}, '
          f'подтверждений паузой {sum(1 for _,e,_ in co.log if e=="ПАУЗА")}')
    print(f'в ПЕРЕХОДЕ {co.trBars} баров = {co.trBars/len(rows):.0%}')
