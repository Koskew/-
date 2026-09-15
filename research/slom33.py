# -*- coding: utf-8 -*-
"""Правило слома тренда: линия, встречные сырые метки и их связки.

Слой 3/3. Проверяются два правила смерти и четыре их комбинации.

  Л — ЛИНИЯ. Тело закрытой свечи ушло за штрих-пунктир (последнее HL у
      восходящего, LH у нисходящего) на imp * D. Импульс здесь только
      линейка глубины: D = 0.00 — простое перебитие, D = 0.33 — как в
      действующем движке.

  М — МЕТКИ. Две последние СЫРЫЕ метки обе встречные тренду: для
      восходящего обе из {LH, LL}, для нисходящего обе из {HH, HL}.
      Сырые, а не колена: в одностороннем ходе метка сливается в то же
      колено и счётчик колен замирает — та самая дыра, ради которой в
      движке появился рывок.

      Сырой пивот на 3/3 виден только через 3 бара. Метки берутся из
      core.pivots, где ключ словаря — бар ПОДТВЕРЖДЕНИЯ, поэтому правило
      физически не может сработать раньше, чем стало известно. На этом
      уже сгорел признак «тело/фитиль», второй раз наступать не будем.

  Л и М — обе сработали за время жизни тренда, порядок любой (защёлки).
  Л или М — кто первый.

Четыре критерия, все структурные — ни стопа, ни цели, ни направления.
Значит сноса рынка тут нет и надбавку считать не от чего.

  1. ОТДАНО   — от экстремума, который тренд успел сделать, до цены на
                баре слома, в импульсах. Меньше — лучше.
  2. ФАЛЬШЬ   — доля сломов, после которых следующий тренд родился в ТУ ЖЕ
                сторону. Меньше — лучше.
  3. ПЕРЕХОД  — доля баров, когда движок не знает, где он.
  4. ЖИЗНЬ    — медиана жизни тренда, для контекста.

Запуск: python3 research/slom33.py
"""
import sys, csv, statistics as st
sys.path.insert(0, 'research')
import core
from core import Core, up


def load(path):
    out = []
    for r in csv.DictReader(open(path, encoding='utf-8-sig')):
        o, h, l, c = float(r['open']), float(r['high']), float(r['low']), float(r['close'])
        out.append((r['time'], min(max(o, l), h), h, l, min(max(c, l), h)))
    return out


def pivots_n(rows, N):
    """Те же правила, что в core.pivots, но с произвольной глубиной."""
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
    for i in range(N, len(rows) - N):
        if all(hi[i-k] <= hi[i] for k in range(1, N+1)) and all(hi[i+k] < hi[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, N+1)) and all(lo[i+k] > lo[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, lo[i], False))
    return at


class Slom(Core):
    """Движок с подменённым правилом смерти. Всё остальное — из эталона."""

    def __init__(self, rows, rule='Л', D=0.33, **kw):
        super().__init__(rows, **kw)
        self.rule, self.D = rule, D
        self.rawH = []          # сторона сырой метки
        self.rawL = []          # её подпись
        self.latL = False       # защёлка: линия уже сработала
        self.latM = False       # защёлка: метки уже сработали
        self._hiMax = None; self._loMin = None
        self._lastFrom = None
        self.given = []         # отдано, в импульсах
        self.deaths = []        # (бар, направление умершего)
        self.births = []        # (бар, направление родившегося)

    # ── сырые метки, без слияния в колена ──
    def _rawPush(self, price, isHi):
        prev = next((self.rawP[j] for j in range(len(self.rawP)-1, -1, -1)
                     if self.rawH[j] == isHi), None)
        if prev is None:
            lab = "?"
        elif isHi:
            lab = "HH" if price > prev else "LH"
        else:
            lab = "HL" if price > prev else "LL"
        self.rawP.append(price); self.rawH.append(isHi); self.rawL.append(lab)

    def _markSays(self):
        """Куда показывают две последние сырые метки: +1 вверх, -1 вниз, 0 нет."""
        if len(self.rawL) < 2:
            return 0
        a, b = self.rawL[-1], self.rawL[-2]
        if a == "?" or b == "?":
            return 0
        if up(a) and up(b):
            return 1
        if (not up(a)) and (not up(b)):
            return -1
        return 0

    # ── правило смерти ──
    def _diedNow(self, b, bLo, bHi, c):
        if self.inTrans:
            return False, None
        okL = False
        if self.lvl is not None:
            need = self.imp * self.D
            okL = (self.tr == 1 and bLo < self.lvl - need) or \
                  (self.tr == -1 and bHi > self.lvl + need)
            if okL and self.lastD is not None and abs(self.lvl - self.lastD) < 1e-9:
                okL = False
        okM = self._markSays() == -self.tr

        if okL: self.latL = True
        if okM: self.latM = True

        if self.rule == 'Л':   died = self.latL
        elif self.rule == 'М': died = self.latM
        elif self.rule == 'И': died = self.latL and self.latM
        else:                  died = self.latL or self.latM

        if not died:
            return False, None
        # цена слома: линия, если она есть — иначе закрытие
        return True, (self.lvl if self.lvl is not None else c)

    def _onDeath(self, b, c):
        self.deaths.append((b, self.pTr))
        if self.imp > 0 and self._hiMax is not None:
            g = (self._hiMax - c) if self.pTr == 1 else (c - self._loMin)
            self.given.append(max(0.0, g) / self.imp)

    def step(self, b):
        for bar, price, isHi in self.at.get(b, []):
            self._rawPush(price, isHi)
        h, l = self.rows[b][2], self.rows[b][3]
        if self.tr != 0 and not self.inTrans:
            self._hiMax = h if self._hiMax is None else max(self._hiMax, h)
            self._loMin = l if self._loMin is None else min(self._loMin, l)
        super().step(b)
        if self.trFrom != self._lastFrom:          # родился новый тренд
            if self._lastFrom is not None or self.tr != 0:
                self.births.append((b, self.tr))
            self._lastFrom = self.trFrom
            self.latL = False; self.latM = False
            self._hiMax = h; self._loMin = l


# rawP объявляем на классе, чтобы не трогать __init__ эталона
Slom.rawP = None


def run(rows, rule, D, N=3):
    e = Slom(rows, rule=rule, D=D, fib=D, jump=0.5)
    e.at = pivots_n(rows, N)
    e.rawP = []
    for b in range(len(rows)):
        e.step(b)
    # фальшь: следующее рождение в ту же сторону, что умерший тренд
    fake = tot = 0
    bi = 0
    for db, dd in e.deaths:
        while bi < len(e.births) and e.births[bi][0] <= db:
            bi += 1
        if bi < len(e.births):
            tot += 1
            if e.births[bi][1] == dd:
                fake += 1
    return dict(
        n=len(e.deaths),
        given=st.median(e.given) if e.given else float('nan'),
        fake=(fake / tot * 100) if tot else float('nan'),
        trans=e.trBars / len(rows) * 100,
        life=st.median(e.lives) if e.lives else float('nan'),
    )


RULES = [('Л 0.00', 'Л', 0.00), ('Л 0.33', 'Л', 0.33), ('М', 'М', 0.33),
         ('Л и М 0.00', 'И', 0.00), ('Л и М 0.33', 'И', 0.33),
         ('Л или М 0.00', 'ИЛИ', 0.00), ('Л или М 0.33', 'ИЛИ', 0.33)]


def table(title, rows):
    print('\n══ %s' % title)
    print('   %-13s %6s %9s %8s %9s %8s' % ('правило', 'сломов', 'отдано', 'фальшь', 'ПЕРЕХОД', 'жизнь'))
    for name, rule, D in RULES:
        r = run(rows, rule, D)
        print('   %-13s %6d %8.2f и %7.0f%% %8.0f%% %8.0f' %
              (name, r['n'], r['given'], r['fake'], r['trans'], r['life']))


if __name__ == '__main__':
    h1 = load('data/XAUUSD_1h_9y.csv')
    m5 = load('data/XAUUSD_5m.csv')
    table('1H · 9 лет · %d баров' % len(h1), h1)
    mid = len(h1) // 2
    table('1H · первая половина', h1[:mid])
    table('1H · вторая половина', h1[mid:])
    table('5m · 3.5 мес · %d баров' % len(m5), m5)
