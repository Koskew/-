# -*- coding: utf-8 -*-
"""Н47 на ЧЕСТНОМ признаке. Вариант Б по слову владельца 26.10.2026.

ЧТО ЭТО. Н21 (01.10.2026), пересчитанная как Н47 (25.10.2026) — правило
владельца про линии: «штрих-пунктир от низов ДЕРЖИТСЯ, а от верхов
ПРОБИВАЕТСЯ». Линия нуля и линия низа (2) смотрятся до прихода колена
(3); три состояния — цело, проколото тенью, закрыто за линией. Исход:
дошёл ли счёт ПОТОМ до (5). Вершина (1) — КОНТРОЛЬ, у неё пробой ждём.

ЗАЧЕМ ЗАНОВО. Запись Н50: на честном признаке Н24 и Н35 умерли обе.
Н47 — единственный оставшийся сильный вывод, не проверенный честно. Он
устроен иначе: берёт ЦЕНУ линии по сырым свечам, а не подпись. Но цена
берётся у ОКОНЧАТЕЛЬНОГО колена, а колено переезжает (Н40).

ПЕРЕКОС ТУТ МОЖЕТ РАБОТАТЬ В ДРУГУЮ СТОРОНУ, и это сказано ДО замера:
колено нуля переехало вниз → линия нарисована НИЖЕ → пробить труднее →
случай выглядит «цело». А вниз колено едет, когда цена падает, то есть
когда тренд умирает. Значит грязная версия пихает умирающие тренды в
«цело» и эффект ЗАНИЖАЕТ. Куда сдвинется число — неизвестно заранее.

ВАРИАНТ Б, выбран владельцем: цена линии берётся ТАКОЙ, КАКОЙ ОНА БЫЛА
НА ТОТ БАР. Линия двигалась — значит и прокол считается против той цены,
что стояла в этот момент. Довод: линия существует ровно для того, чтобы
её пробили или она удержала.

ВАРИАНТ А считается рядом — цена при появлении, окно от первого
подтверждения. Расхождение между А и Б само по себе число.

РИСК ВАРИАНТА Б, назван до замера: переезд колена нуля вниз означает,
что цена ушла под ноль, то есть это сам по себе пробой. Если линии
двигаются часто, вариант Б скажет банальность. Частота переездов внутри
окна считается и печатается — если она велика, вердикт по Б не выносится.

ПЛАНКА ОБЪЯВЛЕНА ДО ЗАМЕРА:
  ВЫЖИЛ   — знак держится во всех клетках, в большинстве эффект > 2σ,
            И КОНТРОЛЬ по вершине (1) остаётся ОБРАТНЫМ;
  ОСЛАБЕЛ — знак держится, эффект меньше: число переписывается;
  УМЕР    — знак скачет между выборками или половинами, либо контроль
            сплющился.

СЕТЬ. Прогон с обёрткой и без обязаны дать тождественные цепочки,
подписи и историю счётов. Движок НЕ трогается.

    python3 research/n47_chestno.py
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
import dvizhok2 as D
from pereschet import zero_index

SETS = (('девять лет часовика', 'data/XAUUSD_1h_9y.csv'),
        ('два года часовика', 'data/XAUUSD_1h_2y.csv'),
        ('пятиминутка', 'data/XAUUSD_5m.csv'))
MIN_N = 50
SOST = ('цело', 'тень', 'закр')

# ════════════════════════════════════════════════════════════════════
# ОБЁРТКА. К первой цене добавляется ИСТОРИЯ ПЕРЕЕЗДОВ: (бар
# подтверждения, цена) на каждом шаге. Движок не читает этих полей.
# ════════════════════════════════════════════════════════════════════
_orig = D.Chain.push


def _push(self, price, bar, isHi, conf):
    if not hasattr(self, 'FP'):
        self.FP, self.FL, self.FC, self.HIST = [], [], [], []
    same = bool(self.P) and self.H[-1] == isHi
    before = self.P[-1] if self.P else None
    prev = None
    if not same:
        for j in range(len(self.P) - 1, -1, -1):
            if self.H[j] == isHi:
                prev = self.P[j]
                break
    r = _orig(self, price, bar, isHi, conf)
    if r:
        self.FP.append(price)
        self.FL.append(D.lab(isHi, price, prev))
        self.FC.append(conf)
        self.HIST.append([(conf, price)])
    elif same and self.P and self.P[-1] != before:
        if self.HIST:
            self.HIST[-1].append((conf, self.P[-1]))
    return r


def set_patch(on):
    D.Chain.push = _push if on else _orig


# ════════════════════════════════════════════════════════════════════
def lineprice(hist, i):
    """Цена линии, какой она была НА БАР i. None — линии ещё нет."""
    p = None
    for cb, pr in hist:
        if cb <= i:
            p = pr
        else:
            break
    return p


def broke_b(rows, hist, a, b, flip, below):
    """Вариант Б: цена линии берётся на каждый бар отдельно.
    Возвращает (состояние, сколько раз линия переехала внутри окна)."""
    shad = False
    dvig = sum(1 for cb, _ in hist[1:] if a < cb <= b)
    for i in range(max(a + 1, 0), min(b + 1, len(rows))):
        price = lineprice(hist, i)
        if price is None:
            continue
        _, o, h, l, c = rows[i]
        hh, ll, cc = (-l, -h, -c) if flip else (h, l, c)
        if below:
            if cc < price:
                return 'закр', dvig
            if ll <= price:
                shad = True
        else:
            if cc > price:
                return 'закр', dvig
            if hh >= price:
                shad = True
    return ('тень' if shad else 'цело'), dvig


def broke_a(rows, price, a, b, flip, below):
    """Вариант А: одна цена — та, что была при появлении."""
    shad = False
    for i in range(max(a + 1, 0), min(b + 1, len(rows))):
        _, o, h, l, c = rows[i]
        hh, ll, cc = (-l, -h, -c) if flip else (h, l, c)
        if below:
            if cc < price:
                return 'закр'
            if ll <= price:
                shad = True
        else:
            if cc > price:
                return 'закр'
            if hh >= price:
                shad = True
    return 'тень' if shad else 'цело'


def sigma2(p1, n1, p2, n2):
    if not n1 or not n2:
        return float('nan')
    p = (p1 * n1 + p2 * n2) / (n1 + n2)
    v = p * (1 - p) * (1.0 / n1 + 1.0 / n2)
    return 200.0 * math.sqrt(v) if v > 0 else 0.0


def sobral(res, rows, flip, lo=None, hi=None):
    C, T = res['C'][2], res['T'][2]
    out = []
    for ct in T.counts:
        zi = zero_index(C, ct['zb'])
        if zi < 0 or zi + 3 >= len(C.P):
            continue
        if lo is not None and not (lo <= ct['zb'] < hi):
            continue
        end = ct['end'] if ct['end'] is not None else 10 ** 9
        # счёт обязан был РЕАЛЬНО стоять на (3)
        if ct['mx'] < 3 or C.FC[zi + 3] > end:
            continue
        stop = C.FC[zi + 3]
        rec = {'do5': ct['mx'] >= 5, 'rojd': ct['zl'] == 'LL', 'dvig': 0}
        for nm, k, below in (('ноль', 0, True), ('низ2', 2, True), ('верх1', 1, False)):
            st, dv = broke_b(rows, C.HIST[zi + k], C.FC[zi + k], stop, flip, below)
            rec['b_' + nm] = st
            rec['a_' + nm] = broke_a(rows, C.FP[zi + k], C.FC[zi + k], stop, flip, below)
            rec['gr_' + nm] = broke_a(rows, C.P[zi + k], C.C[zi + k], C.C[zi + 3], flip, below)
            rec['dvig'] += dv
        out.append(rec)
    return out


def tri(sel, key, zag, obratno=False):
    """Три состояния линии. Возвращает разрыв «цело минус закр»."""
    g = {}
    for st in SOST:
        sub = [r for r in sel if r[key] == st]
        g[st] = (sum(1 for r in sub if r['do5']), len(sub))
    out = []
    for st in SOST:
        a, n = g[st]
        out.append('%s %5.1f%% (%4d)' % (st, 100.0 * a / n if n else 0, n))
    (ac, nc), (az, nz) = g['цело'], g['закр']
    if not nc or not nz:
        print('  %-30s  %s   —' % (zag, '  '.join(out)))
        return None
    pc_, pz = ac / nc, az / nz
    d = 100.0 * (pc_ - pz)
    s2 = sigma2(pc_, nc, pz, nz)
    good = (d < -s2) if obratno else (d > s2)
    mk = '  мало' if min(nc, nz) < MIN_N else ('  ✔' if good else '  НЕ ТАК')
    print('  %-30s  %s   цело−закр %+6.1f   2σ %4.1f%s'
          % (zag, '  '.join(out), d, s2, mk))
    return d


# ════════════════════════════════════════════════════════════════════
print('Н47 на ЧЕСТНОМ признаке · вариант Б · движок v3.29, слой 2/2')
print('планка объявлена в docstring ДО замера')

print('\n' + '=' * 118)
print('СЕТЬ · обёртка не имеет права менять движок')
print('=' * 118)
rows9 = load('data/XAUUSD_1h_9y.csv')
set_patch(False)
clean = D.run_all(rows9, zguard=True, knee_seq=True, birth_lvl=True)
set_patch(True)
wrapt = D.run_all(rows9, zguard=True, knee_seq=True, birth_lvl=True)
ok = True
for li in range(3):
    a, b = clean['C'][li], wrapt['C'][li]
    for fld in ('P', 'B', 'H', 'C', 'L'):
        if getattr(a, fld) != getattr(b, fld):
            print('  РАСХОЖДЕНИЕ: слой %d, поле %s' % (li, fld)); ok = False
    if len(b.HIST) != len(b.P):
        print('  РАСХОЖДЕНИЕ: слой %d, длина истории' % li); ok = False
    if clean['T'][li].counts != wrapt['T'][li].counts:
        print('  РАСХОЖДЕНИЕ: слой %d, история счётов' % li); ok = False
if not ok:
    print('\nЗАМЕР ОТМЕНЁН: обёртка влезла в движок')
    sys.exit(1)
print('  цепочки, подписи и история счётов ТОЖДЕСТВЕННЫ на всех трёх слоях')

itog = []
for setnm, path in SETS:
    rows = load(path)
    print('\n' + '=' * 118)
    print('%s — %d баров' % (setnm, len(rows)))
    print('=' * 118)
    store = {}
    for flip, dn in ((False, '↑'), (True, '↓')):
        res = D.run_all(rows, flip=flip, zguard=True, knee_seq=True, birth_lvl=True)
        store[dn] = (res, rows, flip)
        sel = sobral(res, rows, flip)
        dv = sum(1 for r in sel if r['dvig'])
        print('\n %s  счётов, стоявших на (3): %d   | у %d (%.1f%%) хоть одна линия ПЕРЕЕХАЛА внутри окна'
              % (dn, len(sel), dv, 100.0 * dv / max(len(sel), 1)))
        for nm, zag, obr in (('ноль', 'ЛИНИЯ НУЛЯ', False),
                             ('низ2', 'ЛИНИЯ НИЗА (2)', False),
                             ('верх1', 'ВЕРШИНА (1) — КОНТРОЛЬ', True)):
            print('   %s' % zag)
            dg = tri(sel, 'gr_' + nm, 'как мерила Н47 (грязно)', obr)
            da = tri(sel, 'a_' + nm, 'вариант А — цена при появл.', obr)
            db = tri(sel, 'b_' + nm, 'вариант Б — цена на тот бар', obr)
            if db is not None:
                itog.append((setnm, dn, nm, 'Б', db))
            if da is not None:
                itog.append((setnm, dn, nm, 'А', da))

    if 'девять' in setnm:
        half = len(rows) // 2
        print('\n ПОЛОВИНЫ · вариант Б — знак обязан держаться')
        for flip, dn in ((False, '↑'), (True, '↓')):
            res, rws, fl = store[dn]
            for pnm, a, b in (('первая', 0, half), ('вторая', half, len(rows))):
                s = sobral(res, rws, fl, a, b)
                for nm, zz, obr in (('ноль', 'ноль', False), ('низ2', 'НИЗ (2)', False),
                                   ('верх1', 'верх1 контроль', True)):
                    tri(s, 'b_' + nm, '%s %s · %s' % (dn, pnm, zz), obr)

print('\n' + '=' * 118)
print('ИТОГ по планке · разрыв «цело минус закрыто»')
print('=' * 118)
for nm, zag in (('ноль', 'ЛИНИЯ НУЛЯ'), ('низ2', 'ЛИНИЯ НИЗА (2)'), ('верх1', 'ВЕРШИНА (1) контроль')):
    for v_ in ('Б', 'А'):
        v = [d for _, _, k, vv, d in itog if k == nm and vv == v_]
        if v:
            print('  %-22s вариант %s: клеток %d, положительных %d, разброс %+.1f … %+.1f'
                  % (zag, v_, len(v), sum(1 for x in v if x > 0), min(v), max(v)))
