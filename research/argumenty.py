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

    python3 research/argumenty.py было.pine стало.pine
"""
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


def snimok(f):
    out = {}
    k = 0
    for l in io.open(f, encoding='utf-8').read().split('\n'):
        if l.lstrip().startswith('//'):
            continue
        for call in CALLS:
            if call not in l:
                continue
            k += 1
            for pos, p in enumerate(split_args(l, call)):
                m = re.match(r'(\w+)\s*=\s*(.*)$', p, re.S)
                if m and not p.startswith('"'):
                    out[(k, m.group(1))] = m.group(2).strip()
                else:
                    out[(k, 'поз%d' % pos)] = p
    return out


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    a, b = snimok(sys.argv[1]), snimok(sys.argv[2])
    ischez = sorted(k for k in a if k not in b)
    pojav = sorted(k for k in b if k not in a)
    izmen = sorted(k for k in a if k in b and a[k] != b[k])
    print('аргументов: было %d, стало %d' % (len(a), len(b)))
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
