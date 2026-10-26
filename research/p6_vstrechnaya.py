# -*- coding: utf-8 -*-
"""П6 · Н16 на ЧЕСТНОМ признаке. Встречная метка, пробившая ноль.

ЧТО ЭТО. Н16 (23.09.2026), случай владельца со слоя 2/2 от 31 дек 2025 —
«он просто не устоял». Флаг: внутри действующего счёта появилось колено
с ВСТРЕЧНОЙ подписью (у восходящего низ LL) И цена ушла ЗА НОЛЬ этого
счёта. Держится до конца счёта, сбрасывается новым нулём. Исход: дошёл
ли счёт до (5). Старый ответ на 2/2: −7.1 и −6.4 пп.

ПРАВИЛО ЗДЕСЬ УЖЕ РЕШЕНО и замером не трогается: §3 — «встречная
подпись счёт НЕ обрывает, она помечает точку как манипуляционную», и
Н16 этим же кончилась: «СЛАБОСТЬ, НЕ СМЕРТЬ». Замер нужен для возможной
строки табло «ноль пробит», которую Н16 предложила и которую не внесли.

ЧТО СКАЗАНО ВЛАДЕЛЬЦУ ДО ЗАМЕРА, чтобы потом не выглядело подгонкой:
этот замер скорее всего УМРЁТ или ОСЛЕПНЕТ. Признак состоит из двух
частей, и обе задеты: подпись — это то, что убило Н24 и Н35 (Н50), а
«цена за нулём» берётся у окончательного колена, как в линии нуля,
которая умерла в Н51. Плюс на 2/2 Н16 и так была на грани: −7.1 и −6.4
при шуме около 6.7. Плюс по §6 флаг у рождения может встать только
после того, как уровень съехал с нуля, то есть с точки (4).

ПАРАМЕТРЫ, согласованы 26.10.2026:
  · данные: девять лет часовика (как в Н16), два года, пятиминутка;
  · слой 2/2, движок v3.29;
  · подпись ЧЕСТНАЯ (при первом подтверждении), цена и ноль НА ТОТ БАР
    (вариант Б, как в Н51). Вариант А считается рядом;
  · сравнение ВНУТРИ одной точки счёта: среди счётов, дошедших до (c),
    флаг уже стоит против не стоит;
  · главная точка (2) — как в Н16; рядом точка (3);
  · точка (4) НЕ берётся: между признаком и исходом остаётся одно
    колено. Сказано владельцу, он согласился;
  · отдельно рождения и продолжения;
  · порог 50 случаев в меньшей группе, две сигмы по n каждой клетки;
  · половины девяти лет.

ДВЕ КОЛОНКИ Н16 ОСТАЮТСЯ ВЫБРОШЕННЫМИ, и не молча: «встречный тренд
родился» называет одно и то же колено дважды, «умер до 1 колена»
механически близко к порогу смерти. Довод Н16 от подписи не зависит.

ПЛАНКА ОБЪЯВЛЕНА ДО ЗАМЕРА:
  ВЫЖИЛ   — знак отрицательный во всех клетках, в большинстве > 2σ;
  ОСЛАБЕЛ — знак держится, эффект меньше;
  УМЕР    — знак скачет между выборками или половинами;
  СЛЕПО   — в группе с флагом меньше 50 случаев в большинстве клеток.

    python3 research/p6_vstrechnaya.py
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
import dvizhok2 as D
import obertka as O
from pereschet import zero_index

SETS = (('девять лет часовика', 'data/XAUUSD_1h_9y.csv'),
        ('два года часовика', 'data/XAUUSD_1h_2y.csv'),
        ('пятиминутка', 'data/XAUUSD_5m.csv'))
MIN_N = 50
KW = dict(zguard=True, knee_seq=True, birth_lvl=True)


def sigma2(p1, n1, p2, n2):
    if not n1 or not n2:
        return float('nan')
    p = (p1 * n1 + p2 * n2) / (n1 + n2)
    v = p * (1 - p) * (1.0 / n1 + 1.0 / n2)
    return 200.0 * math.sqrt(v) if v > 0 else 0.0


def sobral(res, c, lo=None, hi=None):
    """Счёты, стоявшие на точке c. Флаг снят ЧЕСТНО, до бара точки c."""
    C, T = res['C'][2], res['T'][2]
    out = []
    for ct in T.counts:
        zi = zero_index(C, ct['zb'])
        if zi < 0 or zi + c >= len(C.P):
            continue
        if lo is not None and not (lo <= ct['zb'] < hi):
            continue
        end = ct['end'] if ct['end'] is not None else 10 ** 9
        if ct['mx'] < c or C.FC[zi + c] > end:
            continue
        stop = C.FC[zi + c]
        flagB = flagA = False
        for k in range(zi + 1, zi + c + 1):
            if C.H[k]:
                continue                      # встречная подпись — только у НИЗА
            if C.FL[k] != 'LL':
                continue
            nol_b = O.cena(C.HIST[zi], C.FC[k])   # ноль НА ТОТ БАР
            if nol_b is not None and C.FP[k] < nol_b:
                flagB = True
            if C.FP[k] < C.FP[zi]:                # вариант А: ноль при появлении
                flagA = True
        out.append({'flagB': 'флаг' if flagB else 'нет',
                    'flagA': 'флаг' if flagA else 'нет',
                    'do5': ct['mx'] >= 5, 'rojd': ct['zl'] == 'LL',
                    'll2': zi + 2 < len(C.P) and C.FL[zi + 2] == 'LL'})
    return out


def dve(sel, key, zag):
    g = {}
    for lb in ('флаг', 'нет'):
        sub = [r for r in sel if r[key] == lb]
        g[lb] = (sum(1 for r in sub if r['do5']), len(sub))
    (a, na), (b, nb) = g['флаг'], g['нет']
    if not na or not nb:
        print('  %-32s  данных нет' % zag)
        return None
    pa, pb = a / na, b / nb
    d = 100.0 * (pa - pb)
    s2 = sigma2(pa, na, pb, nb)
    mk = '  СЛЕПО' if min(na, nb) < MIN_N else ('  ✔' if d < -s2 else '  в шуме')
    print('  %-32s  флаг %5.1f%% (%4d)   нет %5.1f%% (%4d)   разница %+6.1f   2σ %4.1f%s'
          % (zag, 100 * pa, na, 100 * pb, nb, d, s2, mk))
    return d, min(na, nb)


print('П6 · Н16 на ЧЕСТНОМ признаке · вариант Б · движок v3.29, слой 2/2')
print('планка объявлена в docstring ДО замера')

print('\n' + '=' * 112)
print('СЕТЬ · обёртка не имеет права менять движок')
print('=' * 112)
ok, _ = O.sverit(load('data/XAUUSD_1h_9y.csv'), **KW)
if not ok:
    print('\nЗАМЕР ОТМЕНЁН'); sys.exit(1)

itog = []
for setnm, path in SETS:
    rows = load(path)
    print('\n' + '=' * 112)
    print('%s — %d баров' % (setnm, len(rows)))
    print('=' * 112)
    store = {}
    for flip, dn in ((False, '↑'), (True, '↓')):
        O.patch(True)
        res = D.run_all(rows, flip=flip, **KW)
        store[dn] = res
        for c in (2, 3):
            sel = sobral(res, c)
            print('\n %s  точка (%d): счётов %d' % (dn, c, len(sel)))
            # ПРОВЕРКА СТРУКТУРЫ: на точке (2) флаг обязан совпасть с «низ (2) = LL»
            if c == 2:
                bad = sum(1 for r in sel if (r['flagB'] == 'флаг') != r['ll2'])
                print('    структура: флаг против «низ (2) = LL» — расхождений %d' % bad)
            r = dve(sel, 'flagB', 'вариант Б, все')
            if r:
                itog.append((setnm, dn, c, 'все', r[0], r[1]))
            dve(sel, 'flagA', 'вариант А, все')
            for nm, f in (('только РОЖДЕНИЯ', True), ('только ПРОДОЛЖЕНИЯ', False)):
                r2 = dve([x for x in sel if x['rojd'] == f], 'flagB', 'вариант Б, ' + nm)
                if r2:
                    itog.append((setnm, dn, c, nm, r2[0], r2[1]))

    if 'девять' in setnm:
        half = len(rows) // 2
        print('\n ПОЛОВИНЫ · вариант Б')
        for flip, dn in ((False, '↑'), (True, '↓')):
            for c in (2, 3):
                for pnm, a, b in (('первая', 0, half), ('вторая', half, len(rows))):
                    dve(sobral(store[dn], c, a, b), 'flagB', '%s (%d) %s половина' % (dn, c, pnm))

print('\n' + '=' * 112)
print('ИТОГ по планке')
print('=' * 112)
for c in (2, 3):
    for nm in ('все', 'только РОЖДЕНИЯ', 'только ПРОДОЛЖЕНИЯ'):
        v = [(d, n) for _, _, cc, k, d, n in itog if cc == c and k == nm]
        if v:
            slep = sum(1 for d, n in v if n < MIN_N)
            print('  точка (%d) %-20s клеток %d, отрицательных %d, разброс %+.1f … %+.1f, слепых %d'
                  % (c, nm, len(v), sum(1 for d, _ in v if d < 0),
                     min(d for d, _ in v), max(d for d, _ in v), slep))
