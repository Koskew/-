# -*- coding: utf-8 -*-
"""В28 · ЧЕСТНЫЙ ПРИЗНАК: подпись и цена колена при ПЕРВОМ подтверждении.

ПОВОД — запись Н49. Хвост счёта читается из ГОТОВОЙ цепочки колен, а
колено имеет право переехать (Н40) и записано своей ОКОНЧАТЕЛЬНОЙ
подписью, ценой и баром подтверждения. У счёта, умершего рано, часть
хвоста дописана ПОСЛЕ его смерти: таких подписей у дошедших до (5) — 9 и
4, у всех счётов — 45.6% и 53.3%. А замеры сравнивают ровно эти группы.

ВАРИАНТ А, выбран владельцем 25.10.2026: признак берётся таким, КАКИМ
ОН БЫЛ НА ГРАФИКЕ в момент появления колена. Его слово: «вариант А будет
честным». Довод, названный до замера: признак, который становится
известен через три бара после смерти тренда, в торговле бесполезен.

ЦЕНА ВАРИАНТА А названа заранее: числа станут СЛАБЕЕ, возможно сильно.

КАК. Движок НЕ ТРОГАЕТСЯ. Цепочка оборачивается снаружи: на каждом
появлении НОВОГО колена записывается его цена, подпись (против
предыдущего колена той же стороны, каким оно было В ТОТ МОМЕНТ) и бар
подтверждения. Переезды считаются отдельно.

СЕТЬ. Обёртка не имеет права менять движок. Проверяется в этом же
прогоне: run_all с обёрткой и без обёртки обязаны дать тождественную
цепочку. Не сошлось — замер отменяется.

МОЯ ОШИБКА, НАЙДЕННАЯ В ХОДЕ ЗАМЕРА И ПОЧИНЕННАЯ ЗДЕСЬ. В списке
параметров я написал «справочник, построенный из честных подписей». Так
считать НЕЛЬЗЯ: честный хвост у рано умершего счёта КОРОЧЕ, а короткий
хвост почти всегда оказывается началом какой-нибудь эталонной формы и
попадает «в справочник». Проверено: хвосты длины 2, 3 и 4 встречаются
ТОЛЬКО у счётов, не дошедших до (5), и из 428 таких 428 попали «в
справ.» в 121+253+54 случаях против 16+32+53 «вне». То есть ДЛИНА
ХВОСТА и есть исход, и сравнение превращается в сравнение исхода с
самим собой. Первый прогон дал из-за этого разрыв МИНУС 18.8 пп.

ПОЧИНКА: длина начала ФИКСИРУЕТСЯ. Берётся ровно k подписей в момент,
когда счёт стоит на точке (k), и спрашивается, продолжает ли это начало
подходить справочнику. Выборка — счёты, дошедшие до (k). Исход —
(5) — целиком в будущем. Считается k = 3 и k = 4.

ПЛАНКА ОБЪЯВЛЕНА ДО ЗАМЕРА:
  ВЫЖИЛ   — знак держится во всех клетках, в большинстве эффект > 2σ;
  ОСЛАБЕЛ — знак держится, эффект меньше: число переписывается;
  УМЕР    — знак скачет между выборками или половинами.

    python3 research/v28_chestno.py
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
import dvizhok2 as D
from pereschet import zero_index, PAT

SETS = (('девять лет часовика', 'data/XAUUSD_1h_9y.csv'),
        ('два года часовика', 'data/XAUUSD_1h_2y.csv'),
        ('пятиминутка', 'data/XAUUSD_5m.csv'))
MIN_N = 50

# ════════════════════════════════════════════════════════════════════
# ОБЁРТКА ЦЕПОЧКИ. Движок не тронут: _orig вызывается как есть, всё
# записанное лежит в полях, которых движок не читает.
# ════════════════════════════════════════════════════════════════════
_orig = D.Chain.push


def _push(self, price, bar, isHi, conf):
    if not hasattr(self, 'FP'):
        self.FP, self.FL, self.FC, self.MOV = [], [], [], []
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
        self.MOV.append(0)
    elif same and self.P and self.P[-1] != before:
        if self.MOV:
            self.MOV[-1] += 1
    return r


def set_patch(on):
    D.Chain.push = _push if on else _orig


# ════════════════════════════════════════════════════════════════════
def sigma2(p1, n1, p2, n2):
    if not n1 or not n2:
        return float('nan')
    p = (p1 * n1 + p2 * n2) / (n1 + n2)
    v = p * (1 - p) * (1.0 / n1 + 1.0 / n2)
    return 200.0 * math.sqrt(v) if v > 0 else 0.0


def dve(sel, key, a_lab, b_lab, zag):
    g = {}
    for lb in (a_lab, b_lab):
        sub = [r for r in sel if r[key] == lb]
        g[lb] = (sum(1 for r in sub if r['do5']), len(sub))
    (a, na), (b, nb) = g[a_lab], g[b_lab]
    if not na or not nb:
        print('  %-30s  данных нет' % zag)
        return None
    pa, pb = a / na, b / nb
    d = 100.0 * (pa - pb)
    s2 = sigma2(pa, na, pb, nb)
    mk = '  мало' if min(na, nb) < MIN_N else ('  ✔' if abs(d) > s2 else '  в шуме')
    print('  %-30s  %s %5.1f%% (%4d)   %s %5.1f%% (%4d)   разрыв %+6.1f   2σ %4.1f%s'
          % (zag, a_lab, 100 * pa, na, b_lab, 100 * pb, nb, d, s2, mk))
    return d


def sobral(res, lo=None, hi=None):
    """Счёты слоя 2/2 с ЧЕСТНЫМ признаком."""
    C, T = res['C'][2], res['T'][2]
    FL, FP, FC, MOV = C.FL, C.FP, C.FC, C.MOV
    out = []
    for ct in T.counts:
        zi = zero_index(C, ct['zb'])
        if zi < 0 or zi + 2 >= len(C.P):
            continue
        if lo is not None and not (lo <= ct['zb'] < hi):
            continue
        end = ct['end'] if ct['end'] is not None else 10 ** 9
        # колено (2) должно было подтвердиться ДО конца счёта — иначе
        # счёт на нём никогда не стоял
        if FC[zi + 2] > end:
            continue
        chest, fin = FL[zi + 2], C.L[zi + 2]
        if chest not in ('HL', 'LL'):
            continue
        # честный хвост: колена, подтвердившиеся до конца счёта
        rec = {'n2': chest, 'n2fin': fin,
               'do5': ct['mx'] >= 5, 'mx': ct['mx'],
               'rojd': ct['zl'] == 'LL',
               'mov2': MOV[zi + 2], 'smena': chest != fin}
        # НАЧАЛО ФИКСИРОВАННОЙ ДЛИНЫ: ровно k подписей, снятых в момент,
        # когда счёт стоит на (k). Длину фиксируем нарочно — см. docstring
        for k in (3, 4):
            rec['sp%d' % k] = None
            if ct['mx'] >= k and zi + k < len(C.P) and FC[zi + k] <= end:
                pre = '·'.join(FL[zi + 1:zi + k + 1])
                rec['sp%d' % k] = 'в справ.' if any(p.startswith(pre) for p in PAT) else 'вне справ.'
        out.append(rec)
    return out


# ════════════════════════════════════════════════════════════════════
print('В28 · ЧЕСТНЫЙ ПРИЗНАК, вариант А — подпись при ПЕРВОМ подтверждении')
print('движок v3.29, слой 2/2. Планка объявлена в docstring ДО замера')

print('\n' + '=' * 110)
print('СЕТЬ · обёртка не имеет права менять движок')
print('=' * 110)
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
    if len(b.FL) != len(b.P):
        print('  РАСХОЖДЕНИЕ: слой %d, длина записи %d против %d' % (li, len(b.FL), len(b.P))); ok = False
    ac, bc = clean['T'][li].counts, wrapt['T'][li].counts
    if len(ac) != len(bc) or any(x != y for x, y in zip(ac, bc)):
        print('  РАСХОЖДЕНИЕ: слой %d, история счётов' % li); ok = False
if not ok:
    print('\nЗАМЕР ОТМЕНЁН: обёртка влезла в движок')
    sys.exit(1)
print('  цепочки, подписи и история счётов ТОЖДЕСТВЕННЫ на всех трёх слоях')
C2 = wrapt['C'][2]
sm = sum(1 for k in range(len(C2.P)) if C2.FL[k] != C2.L[k])
pz = sum(C2.MOV)
print('  колен %d | переездов %d | подпись СМЕНИЛАСЬ у %d колен (%.1f%%)'
      % (len(C2.P), pz, sm, 100.0 * sm / max(len(C2.P), 1)))

itog = []
for setnm, path in SETS:
    rows = load(path)
    print('\n' + '=' * 110)
    print('%s — %d баров' % (setnm, len(rows)))
    print('=' * 110)
    store = {}
    for flip, dn in ((False, '↑'), (True, '↓')):
        res = D.run_all(rows, flip=flip, zguard=True, knee_seq=True, birth_lvl=True)
        store[dn] = (res, rows, flip)
        sel = sobral(res)
        sm = sum(1 for r in sel if r['smena'])
        print('\n %s  счётов в выборке %d   | у %d (%.1f%%) подпись низа (2) ПОТОМ сменилась'
              % (dn, len(sel), sm, 100.0 * sm / max(len(sel), 1)))

        print('   ЗАМЕР 1 · Н24 — подпись низа (2), ЧЕСТНАЯ')
        d = dve(sel, 'n2', 'HL', 'LL', 'все')
        if d is not None:
            itog.append((setnm, dn, 'Н24 все', d))
        for nm, f in (('только РОЖДЕНИЯ', True), ('только ПРОДОЛЖЕНИЯ', False)):
            d2 = dve([r for r in sel if r['rojd'] == f], 'n2', 'HL', 'LL', nm)
            if d2 is not None:
                itog.append((setnm, dn, 'Н24 ' + nm, d2))

        print('   ЗАМЕР 2 · Н35/Н46 — справочник на НАЧАЛЕ фиксированной длины')
        for k in (3, 4):
            sub = [r for r in sel if r['sp%d' % k] is not None]
            d = dve(sub, 'sp%d' % k, 'в справ.', 'вне справ.',
                    'начало из %d, счёт стоит на (%d)' % (k, k))
            if d is not None:
                itog.append((setnm, dn, 'Н46 начало %d' % k, d))

    if 'девять' in setnm:
        half = len(rows) // 2
        print('\n ПОЛОВИНЫ — знак обязан держаться')
        for flip, dn in ((False, '↑'), (True, '↓')):
            res, rws, fl = store[dn]
            for nm, a, b in (('первая', 0, half), ('вторая', half, len(rows))):
                s = sobral(res, a, b)
                dve(s, 'n2', 'HL', 'LL', '%s %s · низ (2)' % (dn, nm))
                dve([r for r in s if r['sp3'] is not None], 'sp3', 'в справ.', 'вне справ.',
                    '%s %s · начало из 3' % (dn, nm))

print('\n' + '=' * 110)
print('ИТОГ по планке')
print('=' * 110)
for nm in ('Н24 все', 'Н24 только РОЖДЕНИЯ', 'Н24 только ПРОДОЛЖЕНИЯ',
           'Н46 начало 3', 'Н46 начало 4'):
    v = [d for _, _, k, d in itog if k == nm]
    if v:
        print('  %-26s клеток %d, положительных %d, разброс %+.1f … %+.1f'
              % (nm, len(v), sum(1 for x in v if x > 0), min(v), max(v)))
