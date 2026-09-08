# -*- coding: utf-8 -*-
"""Проверка двух правил про 2/2, сформулированных для быстрого слоя.

A. «Искать смену тренда через 2/2 только после третьей точки на 5/5».
   Проверяем: когда 2/2 разворачивается ПРОТИВ 5/5, как часто следом
   ломается сам 5/5 — и зависит ли это от того, на какой точке счёта
   находится старший.

B. «На 2/2 смерть по касанию, фильтр глубины не нужен».
   Проверяем, во что превращается тренд 2/2 без фильтра.
"""
import sys, statistics, bisect
sys.path.insert(0, 'research')
from core import Core, load, up

rows = load()

def pivots_n(rows, N):
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
    for i in range(N, len(rows) - N):
        if all(hi[i-k] <= hi[i] for k in range(1, N+1)) and all(hi[i+k] < hi[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, N+1)) and all(lo[i+k] > lo[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, lo[i], False))
    return at

AT5, AT2 = pivots_n(rows, 5), pivots_n(rows, 2)

if __name__ == '__main__':
    # ── A. разворот 2/2 против 5/5 ──
    c5 = Core(rows); c5.at = AT5
    c2 = Core(rows); c2.at = AT2
    d5 = []            # бары смерти 5/5
    flips = []         # (бар, точка счёта 5/5, согласен ли 2/2 с 5/5 после разворота)
    prev2 = 0
    for b in range(len(rows)):
        n5 = len(c5.log); c5.step(b)
        for _, e, _ in c5.log[n5:]:
            if e == 'СМЕРТЬ': d5.append(b)
        c2.step(b)
        t2 = 0 if c2.inTrans else c2.tr
        if t2 != 0 and t2 != prev2 and prev2 != 0:          # 2/2 перевернулся
            t5 = 0 if c5.inTrans else c5.tr
            pt = c5.KN[-1] if c5.KN else -1
            if t5 != 0:
                flips.append((b, pt, t2 == t5))
        if t2 != 0: prev2 = t2
    ds = sorted(d5)
    def dies5(b, hor):
        i = bisect.bisect_right(ds, b)
        return i < len(ds) and ds[i] - b <= hor

    against = [x for x in flips if not x[2]]
    print(f'A. РАЗВОРОТ 2/2 ПРОТИВ 5/5   ({len(against)} случаев из {len(flips)} разворотов 2/2)')
    print(f'   вопрос: ломается ли следом сам 5/5?\n')
    print(f'{"точка счёта 5/5":>18} {"случаев":>8} {"5/5 сломался за":>17}')
    print(f'{"в момент разворота":>18} {"":>8} {"10б":>6} {"20б":>6} {"40б":>6}')
    for lo_, hi_, nm in ((0, 3, '(0)–(2)'), (3, 6, '(3)–(5)')):
        sel = [x for x in against if lo_ <= x[1] < hi_]
        if not sel: continue
        line = f'{nm:>18} {len(sel):>8}'
        for hor in (10, 20, 40):
            line += f'{sum(1 for x in sel if dies5(x[0], hor))/len(sel):>5.0%} '
        print(line)
    line = f'{"все":>18} {len(against):>8}'
    for hor in (10, 20, 40):
        line += f'{sum(1 for x in against if dies5(x[0], hor))/len(against):>5.0%} '
    print(line)
    agree = [x for x in flips if x[2]]
    line = f'{"для сравнения:":>18}\n{"2/2 развернулся ПО 5/5":>18} {len(agree):>8}'
    for hor in (10, 20, 40):
        line += f'{sum(1 for x in agree if dies5(x[0], hor))/len(agree):>5.0%} '
    print(line)

    # ── B. смерть 2/2 по касанию ──
    class Touch(Core):
        """смерть по касанию тенью, без фильтра глубины"""
        def step(self, b):
            o, h, l, c = self.rows[b][1], self.rows[b][2], self.rows[b][3], self.rows[b][4]
            if self.lvl is not None and self.tr != 0:
                died = (self.tr == 1 and l < self.lvl) or (self.tr == -1 and h > self.lvl)
                if died and self.lastD is not None and abs(self.lvl - self.lastD) < 1e-9: died = False
                if died:
                    self.log.append((b, 'СМЕРТЬ', ''))
                    if self.trFrom is not None: self.lives.append(b - self.trFrom)
                    self.pTr, self.pD, self.pDb = self.tr, self.lvl, b
                    self.lastD = self.lvl; self.inTrans = True; self.marks = 0
                    self.lvl = None; self.lvlProv = False; self._trStart = b
            # дальше — как в базе, но смерть уже обработана
            save = self.lvl
            self.lvl = None if save is None else save
            Core.step_rest(self, b)

    def rest(self, b):
        """всё, кроме блока смерти"""
        o, h, l, c = self.rows[b][1], self.rows[b][2], self.rows[b][3], self.rows[b][4]
        if self.inTrans: self.trBars += 1
        if self.jump > 0 and self.inTrans and self.imp > 0 and self.lastD is not None and len(self.KL) >= 2:
            j1, j2 = self.KL[-1], self.KL[-2]
            ju = up(j1) and up(j2); jd = (not up(j1)) and (not up(j2))
            if (jd and c < self.lastD - self.imp*self.jump) or (ju and c > self.lastD + self.imp*self.jump):
                dl = self.lastD
                self.tr = 1 if ju else -1; self.trFrom = b; self.inTrans = False
                self.lastD = None; self.lvl = None
                if self._trStart is not None: self.spans.append(b - self._trStart)
                if self.prov: self.lvl = dl; self.lvlProv = True
        fresh = False
        for bar, price, isHi in self.at.get(b, []):
            if self._push(bar, price, isHi): fresh = True
        if fresh: self.marks += 1
        n = len(self.KL)
        if n >= 2:
            l1, l2 = self.KL[-1], self.KL[-2]; p1, p2 = self.KP[-1], self.KP[-2]
            if fresh:
                if self.tr != 0 and ((self.tr == 1) == (p1 > p2)): self.imp = abs(p1 - p2)
                u2 = up(l1) and up(l2); d2 = (not up(l1)) and (not up(l2))
                if self.tr == 0:
                    if u2 or d2: self.tr = 1 if u2 else -1; self.trFrom = b; self.imp = abs(p1-p2)
                elif self.inTrans and self.marks >= 2 and (u2 or d2):
                    if self._trStart is not None: self.spans.append(b - self._trStart)
                    self.tr = 1 if u2 else -1; self.trFrom = b; self.inTrans = False
                    self.lastD = None; self.lvlProv = False; self.imp = abs(p1-p2)
            if not self.inTrans and self.tr == 1:
                if l1 == "HL": self.lvl = p1; self.lvlProv = False
                if self.lvl is None: self.lvl = next((self.KP[j] for j in range(n-1,-1,-1) if self.KL[j]=="HL"), None)
            elif not self.inTrans and self.tr == -1:
                if l1 == "LH": self.lvl = p1; self.lvlProv = False
                if self.lvl is None: self.lvl = next((self.KP[j] for j in range(n-1,-1,-1) if self.KL[j]=="LH"), None)
            if fresh and self.KT: self.KT[-1] = self.tr; self.KX[-1] = self.inTrans
    Core.step_rest = rest

    print(f'\nB. СМЕРТЬ 2/2: КАСАНИЕ ТЕНЬЮ ПРОТИВ ТЕЛА С ФИЛЬТРОМ')
    print(f'{"правило":>34} {"сломов":>8} {"медиана жизни":>15}')
    for cls, fib, nm in ((Core, 0.33, 'тело, глубже трети импульса'),
                         (Core, 0.0,  'тело, любой пробой'),
                         (Touch, 0.0, 'касание тенью')):
        co = cls(rows, fib=fib); co.at = AT2; co.run()
        d = sum(1 for _, e, _ in co.log if e == 'СМЕРТЬ')
        print(f'{nm:>34} {d:>8} {statistics.median(co.lives):>13.0f}б')
