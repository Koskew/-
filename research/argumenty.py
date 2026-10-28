# -*- coding: utf-8 -*-
"""СВЕРКА АРГУМЕНТОВ ВЫЗОВОВ — сеть, которой не было до 26.10.2026.

ПОВОД. Первая сборка v3.31 не скомпилировалась: «Cannot call
'operator +' with argument 'expr0'='cBlkU'». Резак подсказок был на
шаблоне и брал только ПЕРВУЮ строку, а хвост `+ (…)` оставлял
приклеенным к соседнему аргументу `bgcolor = cBlkU`.

ПОЧЕМУ ЭТОГО НЕ ПОЙМАЛИ ПРЕЖНИЕ СЕТИ:
  · скобки и кавычки СОШЛИСЬ — склейка их не ломает;
  · `sverka.py` считает рисующие вызовы и условия показа — их 87 было
    и 87 стало, вызов никуда не делся;
  · адреса ячеек табло целы — 62 и 62.
Ломается не структура файла, а ЗНАЧЕНИЕ одного аргумента. Ни одна сеть
на него не смотрела.

ЧТО ДЕЛАЕТ. Для каждого вызова из CALLS разбирает аргументы по запятым
ВЕРХНЕГО уровня (скобки и строки не считаются разделителями) и строит
отпечаток {(номер вызова, имя аргумента): значение}. Потом сравнивает
два файла и печатает:
  · аргументы, которые ИСЧЕЗЛИ;
  · которые ПОЯВИЛИСЬ;
  · которые ИЗМЕНИЛИ ЗНАЧЕНИЕ.

Правка считается чистой, когда исчезло только то, что просили убрать,
а изменивших значение НОЛЬ.

⚠ ПОЧИНКА 28.10.2026, v3.32. ПЕРВАЯ РЕДАКЦИЯ СЕТИ ВРАЛА НА ВСТАВКЕ.
Вызовы сверялись по ПОРЯДКОВОМУ НОМЕРУ. Сеть писалась под УДАЛЕНИЕ (65
подсказок ушли, порядок не сдвинулся), и на первой же вставке — одна
новая `input.string` в группе ④ — весь хвост съехал на единицу: 75
ложных «исчезло» и десятки ложных «изменило значение», где на самом
деле сравнивались СОСЕДНИЕ вызовы.

Теперь вызовы СОПОСТАВЛЯЮТСЯ через `difflib`, по подписи «имя функции +
набор имён аргументов». Вставка видна как вставка, удаление как
удаление, а значения сравниваются только у СОПОСТАВЛЕННЫХ пар. Внутри
участков, где подпись изменилась (у вызова убрали или добавили
аргумент), пары берутся по порядку внутри участка.

    python3 research/argumenty.py было.pine стало.pine
"""
import difflib
import io, re, sys

CALLS = ('table.cell(', 'label.new(', 'line.new(', 'box.new(',
         'input.bool(', 'input.int(', 'input.float(', 'input.string(',
         'input.color(', 'input.timeframe(', 'input.source(')


def split_args(l, call):
    i = l.find(call)
    j = i + len(call)
    d = 0
    q = False
    parts = []
    cur = ''
    while j < len(l):
        ch = l[j]
        if q:
            cur += ch
            if ch == '\\':
                cur += l[j + 1]
                j += 2
                continue
            if ch == '"':
                q = False
        else:
            if ch == '"':
                q = True
                cur += ch
            elif ch in '([':
                d += 1
                cur += ch
            elif ch in ')]':
                if d == 0:
                    parts.append(cur)
                    break
                d -= 1
                cur += ch
            elif ch == ',' and d == 0:
                parts.append(cur)
                cur = ''
            else:
                cur += ch
        j += 1
    return [p.strip() for p in parts]


def vyzovy(f):
    """Список вызовов в порядке файла: (имя функции, {аргумент: значение})."""
    out = []
    for l in io.open(f, encoding='utf-8').read().split('\n'):
        if l.lstrip().startswith('//'):
            continue
        for call in CALLS:
            if call not in l:
                continue
            args = {}
            for pos, p in enumerate(split_args(l, call)):
                m = re.match(r'(\w+)\s*=\s*(.*)$', p, re.S)
                if m and not p.startswith('"'):
                    args[m.group(1)] = m.group(2).strip()
                else:
                    args['поз%d' % pos] = p
            out.append((call, args))
    return out


def podpis(v):
    """Чем вызов узнаётся при сопоставлении.

    ПОДПИСЬ ОБЯЗАНА ПЕРЕЖИВАТЬ ПРАВКУ АРГУМЕНТОВ, иначе сеть расцепит
    пары там, где вызов остался тем же. Первая попытка брала НАБОР ИМЁН
    аргументов — и на эталонном прогоне v3.29 → v3.31 (65 подсказок
    убраны) сцепилось лишь 101 из 129 вызовов, а «изменили значение»
    выросло с нуля до 120. Подпись менялась у каждого вызова, потерявшего
    подсказку, и difflib переставал их узнавать.

    Берётся ИМЯ ФУНКЦИИ, а у настроек — ещё и ЗАГОЛОВОК. Заголовок у
    настройки уникален и его не правят: он и отличает одну `input.string`
    от другой, когда рядом вставляют третью."""
    call, args = v
    if call.startswith('input.'):
        return (call, args.get('поз1', ''))
    return (call,)


def pary(A, B):
    """Сопоставить два списка вызовов. Возвращает (пары, только_в_A, только_в_B)."""
    sm = difflib.SequenceMatcher(None, [podpis(v) for v in A], [podpis(v) for v in B], autojunk=False)
    par, lishA, lishB = [], [], []
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == 'equal':
            par += [(a1 + i, b1 + i) for i in range(a2 - a1)]
        elif op == 'delete':
            lishA += list(range(a1, a2))
        elif op == 'insert':
            lishB += list(range(b1, b2))
        else:
            # подпись изменилась: пары по порядку внутри участка,
            # хвост более длинной стороны — как исчезнувшее/появившееся
            n = min(a2 - a1, b2 - b1)
            par += [(a1 + i, b1 + i) for i in range(n)]
            lishA += list(range(a1 + n, a2))
            lishB += list(range(b1 + n, b2))
    return par, lishA, lishB


def snimok(f):
    """Плоский отпечаток — оставлен для совместимости со старыми прогонами."""
    out = {}
    for k, (_, args) in enumerate(vyzovy(f), 1):
        for name, val in args.items():
            out[(k, name)] = val
    return out


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    A, B = vyzovy(sys.argv[1]), vyzovy(sys.argv[2])
    par, lishA, lishB = pary(A, B)
    a, b = {}, {}
    ischez, pojav, izmen = [], [], []
    for ia, ib in par:
        da, db = A[ia][1], B[ib][1]
        for nm in da:
            a[(ia + 1, nm)] = da[nm]
            if nm not in db:
                ischez.append((ia + 1, nm))
            elif da[nm] != db[nm]:
                izmen.append((ia + 1, nm))
                b[(ia + 1, nm)] = db[nm]
        for nm in db:
            if nm not in da:
                pojav.append((ib + 1, nm))
    for ia in lishA:
        for nm in A[ia][1]:
            ischez.append((ia + 1, nm + '  [вызов целиком убран]'))
    for ib in lishB:
        for nm in B[ib][1]:
            pojav.append((ib + 1, nm + '  [вызов целиком новый]'))
    ischez, pojav, izmen = sorted(ischez), sorted(pojav), sorted(izmen)
    na = sum(len(v[1]) for v in A)
    nb = sum(len(v[1]) for v in B)
    print('вызовов: было %d, стало %d · сопоставлено пар %d' % (len(A), len(B), len(par)))
    print('аргументов: было %d, стало %d' % (na, nb))
    print()
    print('ИСЧЕЗЛО: %d' % len(ischez))
    for k in ischez[:40]:
        print('   − вызов %d, %s' % k)
    print('ПОЯВИЛОСЬ: %d' % len(pojav))
    for k in pojav[:40]:
        print('   + вызов %d, %s' % k)
    print('ИЗМЕНИЛИ ЗНАЧЕНИЕ: %d' % len(izmen))
    for k in izmen[:40]:
        print('   ! вызов %d, %s:' % k)
        print('       было:  %s' % a[k][:110])
        print('       стало: %s' % b[k][:110])
    print()
    if izmen or pojav:
        print('НЕ ЧИСТО: каждую строку выше объяснить вслух.')
        return 1
    print('ЧИСТО: значения аргументов не менялись, только исчезли названные.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
