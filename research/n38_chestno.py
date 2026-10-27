# -*- coding: utf-8 -*-
"""Н38 на ЧЕСТНОМ исходе · НАСКОЛЬКО МОЖНО ВЕРИТЬ СЛОВУ «УМЕР». Слой 2/2.

ЦЕЛЬ ПЕРЕОПРЕДЕЛЕНА ВЛАДЕЛЬЦЕМ 27.10.2026. Он спросил прямо: «в чём цель
этого замера? если он подтвердится или нет?» — и вопрос оказался
сильнее замера, который я выложил.

ЧЕМ БЫЛА ПЛОХА ПРЕЖНЯЯ ЦЕЛЬ. Подтвердится — поправится число в
документе, который он не читает, про настройку, которую он не меняет;
подсказки вынесены из пайна в v3.31, этих чисел нет нигде на экране.
НЕ подтвердится — то есть кривая перестанет быть монотонной и где-то
появится «лучший» порог — это прямая дорога к «поставим 0.25, там цифры
красивее», а это ровно то, что запрещает карточка Р57: замер, выбирающий
ПРАВИЛО по исходам, есть предсказание. Порог 0.20 стоит на слове
владельца как РУЧКА СТРОГОСТИ, и Н30 прямо сказала, что оптимума нет.

ЧТО МЕРИМ ВМЕСТО. Одно число — ПАСПОРТ ИНСТРУМЕНТА:

    при пороге 0.20 на слое 2/2 индикатор говорит «умер»
    преждевременно в N% случаев

Это не предсказание и не выбор: правило не трогается, а число говорит,
сколько доверия отмерять сигналу, который владелец и так видит каждый
день. Тот же класс, что «среднее колено 44.29» в табло.

Таблица по порогам считается ТОЛЬКО как проверка монотонности — что
оптимума по-прежнему нет и трогать порог незачем. Как выбор она не
подаётся.

РЕЗУЛЬТАТ ИДЁТ В `ДОКАЗАНО.md`, не в подсказку.

ОПРЕДЕЛЕНИЯ — слово в слово из Н28 и Н38:
  · ЗАХОД — следующий НИЗ пришёл LL, то есть оказался ниже сторожа;
  · ГЛУБИНА — самое глубокое захождение под сторож по ТЕЛУ,
    min(открытие, закрытие), в долях СКОЛЬЗЯЩЕГО среднего колена;
  · ОКНО — от первого подтверждения сторожа до первого подтверждения
    следующего низа;
  · ИСХОД — подпись ВЕРШИНЫ, идущей ПОСЛЕ следующего низа. HH —
    структура оправилась, LH — слабеет дальше;
  · убито(порог) = заходы глубже порога;
  · ПО ДЕЛУ = среди убитых доля слабеющих;
  · ЗРЯ = среди убитых доля оправившихся;  ← ГЛАВНОЕ ЧИСЛО
  · ПРОПУЩЕНО = среди слабеющих доля тех, кого порог не достал.

ЧЕСТНОСТЬ, два отличия от Н38:
  1. подпись вершины берётся при ПЕРВОМ подтверждении, а не
     окончательная из готовой цепочки (болезнь Н49). Грязный исход
     считается РЯДОМ, чтобы видеть, что именно сдвинула честность;
  2. цена сторожа берётся НА ТОТ БАР (вариант Б).

СЧЁТ ИЗ ЗАМЕРА УБРАН, как в Н53: берутся ВСЕ низы цепочки. У `porog3.py`
своя копия счёта на правилах до З40–З42, и вопрос «тело или тень» —
про структуру, а не про нумерацию. Разбивка по точкам (2) и (4) дана
рядом, где счёт движка есть.

СМЕРТЬ В ЗАМЕРЕ НЕ УЧАСТВУЕТ ВОВСЕ: считается по цепочке колен, движок
не спрашивается. Это и было условием Н38 — с включённой смертью порог
обрезал бы выборку на первом же глубоком заходе, и «убили зря»
наблюдать стало бы нечем.

ПЛАНКА ОБЪЯВЛЕНА ДО ЗАМЕРА:
  ВЫЖИЛ          — кривая монотонна, при 0.20 числа в пределах пары
                   пунктов от Н38;
  ПЕРЕПИСЫВАЕТСЯ — кривая монотонна, числа ушли заметно;
  НАХОДКА        — появился пик или перелом. Тогда это НЕ правка текста,
                   а разговор про сам порог, и решать его владельцу.

ОЖИДАНИЕ, названное ДО замера: ВЫЖИЛ или ПЕРЕПИСЫВАЕТСЯ. Монотонность —
свойство того, что глубже заход, тем хуже исход, и Н53 это подтвердила
с запасом. Чтобы появился пик, грязь должна была бы работать по-разному
на разных порогах, а причин для этого не видно.

    python3 research/n38_chestno.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
import dvizhok2 as D
import obertka as O

SETS = (('девять лет часовика', 'data/XAUUSD_1h_9y.csv'),
        ('два года часовика', 'data/XAUUSD_1h_2y.csv'),
        ('пятиминутка', 'data/XAUUSD_5m.csv'))
KW = dict(zguard=True, knee_seq=True, birth_lvl=True, slom=True)
POROGI = (0.10, 0.15, 0.20, 0.25, 0.30, 0.40)
ETALON = 0.20
MIN_N = 50


def glubina(rows, hist, a, b, flip):
    """Самое глубокое захождение под колено ПО ТЕЛУ на барах (a, b].
    Цена колена берётся НА КАЖДЫЙ БАР — вариант Б."""
    d = 0.0
    for i in range(max(a + 1, 0), min(b + 1, len(rows))):
        pr = O.cena(hist, i)
        if pr is None:
            continue
        _, o, h, l, c = rows[i]
        if flip:
            o, c = -o, -c
        telo = min(o, c)
        if telo < pr:
            d = max(d, pr - telo)
    return d


def sobral(res, rows, flip):
    """Заходы слоя 2/2 с честным исходом. Счёт не участвует."""
    C = res['C'][2]
    legs = res['sl_leg']
    TR = res['T'][2].TR
    n = len(C.P)
    out = []
    for k in range(n - 3):
        if C.H[k]:
            continue                       # сторож — НИЗ
        if not (C.H[k + 1] and (not C.H[k + 2]) and C.H[k + 3]):
            continue
        if C.FL[k + 2] != 'LL':
            continue                       # ЗАХОД по определению Н28/Н38
        fk, fn, fv = C.FC[k], C.FC[k + 2], C.FC[k + 3]
        if fn <= fk or fv <= fn or fv >= len(rows):
            continue
        leg = legs[fk] if fk < len(legs) else 0.0
        if leg <= 0:
            continue
        out.append({'d': glubina(rows, C.HIST[k], fk, fn, flip) / leg,
                    'slab': C.FL[k + 3] != 'HH',       # ЧЕСТНЫЙ исход
                    'slab_gr': C.L[k + 3] != 'HH',     # грязный, для сравнения
                    'cnt': TR[fk][2] if fk < len(TR) else -1})
    return out


def pasport(sel, key, porog):
    """Возвращает (убито, по делу %, зря %, пропущено %, база %)."""
    n = len(sel)
    if not n:
        return None
    slab = [r for r in sel if r[key]]
    ubito = [r for r in sel if r['d'] > porog]
    if not ubito or not slab:
        return None
    podelu = sum(1 for r in ubito if r[key])
    propusk = sum(1 for r in slab if r['d'] <= porog)
    return (len(ubito),
            100.0 * podelu / len(ubito),
            100.0 * (len(ubito) - podelu) / len(ubito),
            100.0 * propusk / len(slab),
            100.0 * len(slab) / n)


def tablica(sel, key, zag):
    print('   %s   заходов %d' % (zag, len(sel)))
    if len(sel) < MIN_N:
        print('      мало данных')
        return
    for p in POROGI:
        r = pasport(sel, key, p)
        if r is None:
            continue
        mark = '  ← эталон' if abs(p - ETALON) < 1e-9 else ''
        print('      %.2f   убито %5d   по делу %4.1f%%   ЗРЯ %4.1f%%   пропущено %4.1f%%%s'
              % (p, r[0], r[1], r[2], r[3], mark))
    b = pasport(sel, key, ETALON)
    print('      базовая доля ослаблений %.1f%%' % b[4])


def monotonno(sel, key):
    """Проверка: растёт ли «по делу» и «пропущено» с порогом без переломов."""
    vals = [pasport(sel, key, p) for p in POROGI]
    vals = [v for v in vals if v is not None]
    if len(vals) < 3:
        return None
    podelu = [v[1] for v in vals]
    propusk = [v[3] for v in vals]
    rost_p = all(podelu[i] <= podelu[i + 1] + 1e-9 for i in range(len(podelu) - 1))
    rost_pr = all(propusk[i] <= propusk[i + 1] + 1e-9 for i in range(len(propusk) - 1))
    return rost_p and rost_pr


print('Н38 на ЧЕСТНОМ исходе · ПАСПОРТ ИНСТРУМЕНТА · слой 2/2, движок v3.29')
print('цель: насколько можно верить слову «умер». Планка в docstring ДО замера')

print('\n' + '=' * 104)
print('СЕТЬ · обёртка не имеет права менять движок')
print('=' * 104)
ok, _ = O.sverit(load('data/XAUUSD_1h_9y.csv'), **KW)
if not ok:
    print('\nЗАМЕР ОТМЕНЁН')
    sys.exit(1)

glavnoe = []
mono = []
for setnm, path in SETS:
    rows = load(path)
    print('\n' + '=' * 104)
    print('%s — %d баров' % (setnm, len(rows)))
    print('=' * 104)
    for flip, dn in ((False, '↑'), (True, '↓')):
        O.patch(True)
        res = D.run_all(rows, flip=flip, **KW)
        sel = sobral(res, rows, flip)
        print('\n %s' % dn)
        tablica(sel, 'slab', 'ИСХОД ЧЕСТНЫЙ')
        tablica(sel, 'slab_gr', 'исход грязный, как мерила Н38')
        r = pasport(sel, 'slab', ETALON)
        rg = pasport(sel, 'slab_gr', ETALON)
        if r:
            glavnoe.append((setnm, dn, r, rg))
            mono.append(monotonno(sel, 'slab'))
        for c in (2, 4):
            sub = [x for x in sel if x['cnt'] == c]
            if len(sub) >= MIN_N:
                rr = pasport(sub, 'slab', ETALON)
                if rr:
                    print('      точка счёта (%d): заходов %d, по делу %.1f%%, ЗРЯ %.1f%%, пропущено %.1f%%'
                          % (c, len(sub), rr[1], rr[2], rr[3]))

print('\n' + '=' * 104)
print('ГЛАВНОЕ ЧИСЛО · при эталонном пороге %.2f' % ETALON)
print('=' * 104)
print('  %-22s %-4s %9s %9s %9s   %s' % ('набор', 'напр', 'по делу', 'ЗРЯ', 'пропущ', 'грязный исход дал ЗРЯ'))
for setnm, dn, r, rg in glavnoe:
    print('  %-22s %-4s %8.1f%% %8.1f%% %8.1f%%   %8.1f%%'
          % (setnm, dn, r[1], r[2], r[3], rg[2] if rg else float('nan')))
zrya = [r[2] for _, _, r, _ in glavnoe]
print('\n  ЗРЯ: от %.1f%% до %.1f%%  — то есть преждевременным оказывается'
      % (min(zrya), max(zrya)))
print('       примерно каждый %d-й … каждый %d-й «умер»'
      % (round(100.0 / max(zrya)), round(100.0 / min(zrya))))
print('\n  монотонность кривой во всех клетках: %s'
      % ('ДА — оптимума нет, порог трогать незачем' if all(m for m in mono if m is not None)
         else 'НЕТ — есть перелом, это НАХОДКА, нужен владелец'))
