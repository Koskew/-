# -*- coding: utf-8 -*-
"""В1 · ФОРМА СЧЁТА: статистика или прямое влияние.

Мысль владельца 01.10.2026: «ощущение, что это не просто статистический
показатель, а он напрямую влияет».

Его правило, дословно: «штрих-пунктир от низов ДЕРЖИТСЯ, а от верхов
ПРОБИВАЕТСЯ. Манипуляции допускаются».

Он же назвал приоритет: «главное это от LL(0); 1 неважно LH или HH;
2 HL — важно; 3 HH или LH; 4 HL; 5 HH или LH».

ПОЧЕМУ СПРАВОЧНИК НА ЭТО ОТВЕТИТЬ НЕ МОЖЕТ. Все восемь эталонов имеют
HL на местах (2) и (4). Низы в справочнике не варьируются ВООБЩЕ, значит
про них внутри справочника узнать нечего. Всё, что владельца интересует,
лежит в клетке «вне справочника».

ЧТО СЧИТАЕТСЯ:
  А. пересчёт справочников П и С по коленам СО ВСТАВКАМИ — замечание З27;
  Б. исход «дошёл до (5)» по форме, считая и УМЕРШИЕ счёты;
  В. правило владельца: что стало с линиями низов и вершин;
  Г. его гипотеза «чем мельче слой, тем больше манипуляций».

ЗАЩИТА ОТ ТАВТОЛОГИИ. Уровень тренда — последний HL, и смерть считается
от него. Поэтому «низ пробит закрытием» частично и есть условие смерти.
Чтобы не мерить сам себя, признак снимается СТРОГО ДО того, как счёт
дошёл до (3), а исходом служит «дошёл ли потом до (5)».

Настройки: эталонные, кроме правила смерти — реплика умеет только
«имп × 0.33», как и замеры Н19, Н20. Доза вставок «без ограничения»,
5/5 берёт у 3/3 И 2/2, 3/3 у 2/2, 2/2 только свои.

    python3 research/forma.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import load
from zerkalo import Knees, Trend, events

PAT = ["LH·HL·HH·HL·HH", "LH·HL·HH·HL·LH", "HH·HL·HH·HL·HH", "HH·HL·HH·HL·LH",
       "HH·HL·LH·HL·HH", "LH·HL·LH·HL·HH", "HH·HL·LH·HL·LH", "LH·HL·LH·HL·LH"]
PNM = ["П1", "П5", "П6", "П12", "П16", "П20", "П25", "П29"]


def merged_events(rows, dL, dDs, flip):
    """Колена слоя плюс вставки донора: любое колено донора, которого у
    слоя нет. Доза без ограничения. Порядок — по бару САМОГО колена."""
    atL = events(rows, dL, flip)
    own = {(b, h) for lst in atL.values() for b, p, h in lst}
    ev = [(b, cf, p, h) for cf, lst in atL.items() for b, p, h in lst]
    seen = set(own)
    ins = 0
    for dD in dDs:
        for cf, lst in events(rows, dD, flip).items():
            for b, p, h in lst:
                if (b, h) not in seen:
                    seen.add((b, h))
                    ev.append((b, cf, p, h))
                    ins += 1
    # ПОРЯДОК ВНУТРИ БАРА. Одна большая свеча умеет сделать и вершину, и
    # низ сразу — §11.1. Пайн кладёт их в НАСТОЯЩЕМ порядке в обоих мирах:
    # сперва real-вершина (в перевёрнутом мире это -high, флаг false),
    # потом real-низ. Первая сборка этого замера сортировала по вершине
    # ТОГО мира — и зеркало расходилось на 12 колен из 2569 на 2/2 и на 2
    # из 1829 на 3/3. Ошибка была моя, индикатор правильный.
    ev.sort(key=lambda e: (e[0], e[3] if flip else not e[3]))
    return ev, ins


class Chain:
    """Полная, необрезанная копия цепочки колен: нужна, чтобы после
    прогона достать хвост любого счёта. Правило слияния то же, что в
    Knees.push, поэтому последний элемент всегда совпадает."""
    def __init__(self):
        self.B, self.P, self.H, self.C, self.L = [], [], [], [], []

    def push(self, price, bar, isHi, conf):
        same = self.P and self.H[-1] == isHi
        if same:
            better = price > self.P[-1] if isHi else price < self.P[-1]
            if better:
                self.P[-1] = price; self.B[-1] = bar; self.C[-1] = conf
            return False
        self.P.append(price); self.B.append(bar); self.H.append(isHi); self.C.append(conf)
        return True

    def relabel(self):
        self.L = []
        for i in range(len(self.P)):
            h = self.H[i]; prev = None
            for j in range(i - 1, -1, -1):
                if self.H[j] == h:
                    prev = self.P[j]; break
            c = self.P[i]
            self.L.append('?' if prev is None else
                          ('HH' if c > prev else 'LH') if h else ('HL' if c > prev else 'LL'))


def run_layer(rows, dL, dDs, flip):
    """Прогон одного слоя. Возвращает полную цепочку и список СЧЁТОВ.

    Счёт — не то же, что тренд: §5 даёт перезапуск, при котором внутри
    живого тренда появляется новый ноль. Форму имеет именно счёт.
    """
    ev, ins = merged_events(rows, dL, dDs, flip)
    K, T, FC = Knees(), Trend(), Chain()
    sg = -1.0 if flip else 1.0
    counts = []          # {zb, zl, mx, born, end}
    cur = None
    q = 0
    for i in range(len(rows)):
        _, o, h, l, c = rows[i]
        nw = fr = False
        while q < len(ev) and ev[q][1] <= i:
            bar, conf, price, isHi = ev[q]
            nw = K.push(price, bar, isHi) or nw
            FC.push(price, bar, isHi, conf)
            fr = True
            q += 1
        prev_zb = T.zb
        T.step(i, sg * o, sg * c, K, nw, fr)
        if T.zb != prev_zb:
            if cur is not None:
                cur['end'] = i
                counts.append(cur)
            cur = None if T.zb < 0 else {'zb': T.zb, 'zl': T.zl, 'born': i, 'mx': T.mx, 'end': None}
        if cur is not None:
            cur['mx'] = max(cur['mx'], T.mx)
    if cur is not None:
        cur['end'] = len(rows) - 1
        counts.append(cur)
    FC.relabel()
    return FC, counts, ins


def zero_index(FC, zb):
    """Ноль всегда НИЗ — правка 11.1. Искать по бару И по стороне."""
    for k in range(len(FC.P)):
        if FC.B[k] == zb and not FC.H[k]:
            return k
    return -1


def broke(rows, price, a, b, flip, below):
    """Что случилось с линией цены price на барах (a, b].
    below=True — ждём пробой ВНИЗ (линия низа), иначе ВВЕРХ.
    Возвращает 'закр' / 'тень' / 'цело'. Касание считается как в сломе."""
    sg = -1.0 if flip else 1.0
    shad = False
    for i in range(max(a + 1, 0), min(b + 1, len(rows))):
        _, o, h, l, c = rows[i]
        hh, ll, cc = (sg * h, sg * l, sg * c) if not flip else (-l, -h, -c)
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


def analyse(rows, name, dL, dDs, flip):
    FC, counts, ins = run_layer(rows, dL, dDs, flip)
    tails, res = {}, []
    for ct in counts:
        zi = zero_index(FC, ct['zb'])
        if zi < 0:
            continue
        last = min(zi + 5, len(FC.P) - 1)
        tail = [FC.L[k] for k in range(zi + 1, last + 1)]
        full = '·'.join(tail)
        inref = any(p.startswith(full) for p in PAT) if tail else True
        ex = full in PAT
        do5 = ct['mx'] >= 5
        if do5 and ex:
            key = (ct['zl'], full)
            tails[key] = tails.get(key, 0) + 1
        # признак снимается ДО (3): смотрим ноль и низ (2)
        i3 = zi + 3
        stop = FC.C[i3] if i3 < len(FC.P) else ct['end']
        z_state = broke(rows, FC.P[zi], FC.C[zi], stop, flip, True)
        n2 = zi + 2
        n2_state = broke(rows, FC.P[n2], FC.C[n2], stop, flip, True) if n2 < len(FC.P) and i3 < len(FC.P) else None
        v1 = zi + 1
        v1_state = broke(rows, FC.P[v1], FC.C[v1], stop, flip, False) if v1 < len(FC.P) and i3 < len(FC.P) else None
        lows_ll = sum(1 for k in range(zi + 2, last + 1, 2) if FC.L[k] == 'LL')
        res.append({'zl': ct['zl'], 'tail': full, 'inref': inref, 'exact': ex, 'do5': do5,
                    'mx': ct['mx'], 'z': z_state, 'n2': n2_state, 'v1': v1_state,
                    'lows_ll': lows_ll, 'ntail': len(tail), 'born': ct['born']})
    return res, tails, ins, len(FC.P)


def pct(a, b):
    return '—' if b == 0 else '%.1f%%' % (100.0 * a / b)


def block(title, rows_):
    print('\n' + title)
    print('  ' + '─' * 74)


def main():
    rows = load('data/XAUUSD_1h_2y.csv')
    print('В1 · ФОРМА СЧЁТА.  %d баров, два года часовика.' % len(rows))
    print('Колена СО ВСТАВКАМИ, доза без ограничения. Смерть «имп × 0.33», как Н19 и Н20.')

    layers = [('5/5', 5, [3, 2]), ('3/3', 3, [2]), ('2/2', 2, [])]
    store = {}
    for nm, dL, dDs in layers:
        for flip, dirn in ((False, '↑'), (True, '↓')):
            res, tails, ins, nk = analyse(rows, nm, dL, dDs, flip)
            store[(nm, dirn)] = (res, tails, ins, nk)

    # ── А. ПЕРЕСЧЁТ СПРАВОЧНИКА, З27 ────────────────────────────────
    block('А · СПРАВОЧНИК ПЕРЕСЧИТАН ПО КОЛЕНАМ СО ВСТАВКАМИ  (З27)', None)
    for dirn, lett in (('↑', 'П'), ('↓', 'С')):
        print('\n  %s — %s, счёты, дошедшие до (5):' % (dirn, lett))
        print('  %-22s %-18s %8s %8s' % ('форма', 'имя', 'рождения', 'продолж'))
        for nm, _, _ in layers:
            res, tails, ins, nk = store[(nm, dirn)]
            print('  слой %s:' % nm)
            tot_r = tot_c = 0
            for p, pn in zip(PAT, PNM):
                r = tails.get(('LL', p), 0)
                c = tails.get(('HL', p), 0)
                tot_r += r; tot_c += c
                print('  %-22s %-18s %8d %8d' % (p, lett + pn[1:], r, c))
            print('  %-22s %-18s %8d %8d' % ('ИТОГО', '', tot_r, tot_c))

    # ── Б. ИСХОД ПО ФОРМЕ, включая умершие ──────────────────────────
    block('Б · ДОШЁЛ ЛИ ДО (5) — считая УМЕРШИЕ счёты  (разрез 1)', None)
    print('  %-6s %-4s %8s %10s %10s %10s' % ('слой', 'напр', 'счётов', 'в справ.', 'вне справ.', 'разница'))
    for nm, _, _ in layers:
        for dirn in ('↑', '↓'):
            res, _, _, _ = store[(nm, dirn)]
            a = [r for r in res if r['inref']]
            b = [r for r in res if not r['inref']]
            pa = 100.0 * sum(1 for r in a if r['do5']) / max(len(a), 1)
            pb = 100.0 * sum(1 for r in b if r['do5']) / max(len(b), 1)
            print('  %-6s %-4s %8d %10s %10s %+9.1f пп'
                  % (nm, dirn, len(res), '%.1f%% (%d)' % (pa, len(a)), '%.1f%% (%d)' % (pb, len(b)), pa - pb))

    # ── В. ПРАВИЛО ВЛАДЕЛЬЦА: линии низов и вершин ──────────────────
    block('В · ПРАВИЛО ВЛАДЕЛЬЦА. Признак снят ДО (3), исход — дошёл ли до (5)', None)
    print('  Линия НУЛЯ до прихода (3):')
    print('  %-6s %-4s %10s %10s %10s' % ('слой', 'напр', 'цело', 'тень', 'закр'))
    for nm, _, _ in layers:
        for dirn in ('↑', '↓'):
            res, _, _, _ = store[(nm, dirn)]
            cells = []
            for st in ('цело', 'тень', 'закр'):
                g = [r for r in res if r['z'] == st and r['n2'] is not None]
                cells.append('%s (%d)' % (pct(sum(1 for r in g if r['do5']), len(g)), len(g)))
            print('  %-6s %-4s %10s %10s %10s' % (nm, dirn, *cells))

    print('\n  Линия низа (2) до прихода (3):')
    print('  %-6s %-4s %10s %10s %10s' % ('слой', 'напр', 'цело', 'тень', 'закр'))
    for nm, _, _ in layers:
        for dirn in ('↑', '↓'):
            res, _, _, _ = store[(nm, dirn)]
            cells = []
            for st in ('цело', 'тень', 'закр'):
                g = [r for r in res if r['n2'] == st]
                cells.append('%s (%d)' % (pct(sum(1 for r in g if r['do5']), len(g)), len(g)))
            print('  %-6s %-4s %10s %10s %10s' % (nm, dirn, *cells))

    print('\n  КОНТРОЛЬ — линия вершины (1), её владелец ждёт ПРОБИТОЙ:')
    print('  %-6s %-4s %10s %10s %10s' % ('слой', 'напр', 'цело', 'тень', 'закр'))
    for nm, _, _ in layers:
        for dirn in ('↑', '↓'):
            res, _, _, _ = store[(nm, dirn)]
            cells = []
            for st in ('цело', 'тень', 'закр'):
                g = [r for r in res if r['v1'] == st]
                cells.append('%s (%d)' % (pct(sum(1 for r in g if r['do5']), len(g)), len(g)))
            print('  %-6s %-4s %10s %10s %10s' % (nm, dirn, *cells))

    # ── Г. ГИПОТЕЗА ВЛАДЕЛЬЦА ПРО СЛОИ ──────────────────────────────
    block('Г · «чем мельче слой, тем больше манипуляций» — гипотеза владельца', None)
    print('  Манипуляция = низ счёта получил подпись LL вместо HL.')
    print('  %-6s %-4s %8s %12s %12s' % ('слой', 'напр', 'счётов', 'с манипул.', 'манип/счёт'))
    for nm, _, _ in layers:
        for dirn in ('↑', '↓'):
            res, _, _, _ = store[(nm, dirn)]
            g = [r for r in res if r['ntail'] >= 4]
            wm = sum(1 for r in g if r['lows_ll'] > 0)
            av = sum(r['lows_ll'] for r in g) / max(len(g), 1)
            print('  %-6s %-4s %8d %12s %12.2f' % (nm, dirn, len(g), pct(wm, len(g)), av))

    print('\n  Он же по линии: доля счётов, где линия нуля проколота ТЕНЬЮ (не закрытием):')
    print('  %-6s %-4s %8s %12s' % ('слой', 'напр', 'счётов', 'тень'))
    for nm, _, _ in layers:
        for dirn in ('↑', '↓'):
            res, _, _, _ = store[(nm, dirn)]
            g = [r for r in res if r['n2'] is not None]
            print('  %-6s %-4s %8d %12s' % (nm, dirn, len(g), pct(sum(1 for r in g if r['z'] == 'тень'), len(g))))

    # ── ЗЕРКАЛО ─────────────────────────────────────────────────────
    print('\n  ЗЕРКАЛО: вставок ↑ против ↓ (обязаны совпасть) и колен в цепочке')
    for nm, _, _ in layers:
        _, _, iu, ku = store[(nm, '↑')]
        _, _, idn, kdn = store[(nm, '↓')]
        print('  %-6s вставок ↑%-6d ↓%-6d %s   колен ↑%-6d ↓%-6d %s'
              % (nm, iu, idn, 'OK' if iu == idn else 'РАЗОШЛОСЬ', ku, kdn,
                 'OK' if ku == kdn else 'РАЗОШЛОСЬ'))


if __name__ == '__main__':
    main()
