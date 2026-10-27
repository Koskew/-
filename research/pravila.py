#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СВЕРКА ПРАВИЛ — то же, что sverka.py и slepok.py, только для сводов
правил, а не для пайна.

Заведено 21.10.2026, слово владельца: «но только перед тем как править
правило ты его тоже фиксируй как с пайном чтобы потом не оказалось что
ты что-то упустил».

ЗАЧЕМ. У пайна есть три сети: sverka.py ловит пропавшие условия показа,
slepok.py — сдвиг поведения по умолчанию, dvizhok2.py — зеркало и
инварианты. У сводов правил не было НИ ОДНОЙ. А правила правятся так же
часто, и потерять строку там дороже: по ним потом сверяются замечания.

ЧТО ДЕЛАЕТ. Берёт из каждого файла правил все СТРОКИ ПРАВИЛ — строки
таблиц, пункты списков и заголовки — и сравнивает с отпечатком. Печатает
ПРОПАЛО и ПОЯВИЛОСЬ. Каждую строку из «ПРОПАЛО» надо объяснить вслух,
ровно как у sverka.py.

КАК ПОЛЬЗОВАТЬСЯ:

    python3 research/pravila.py          сверить с отпечатком
    python3 research/pravila.py --snap   снять новый отпечаток

ПОРЯДОК ПРИ ЛЮБОЙ ПРАВКЕ ПРАВИЛА:

    1) python3 research/pravila.py        — убедиться, что чисто
    2) внести правку
    3) python3 research/pravila.py        — объяснить КАЖДУЮ строку
    4) python3 research/pravila.py --snap — закрепить
    5) коммит

Возвращает 1 при любом расхождении.
"""

import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'research', 'out', 'pravila.json')

# своды, по которым сверяются замечания (правило 8)
FILES = [
    'indicator/ПРАВИЛА-ВОСХОДЯЩИЙ.md',
    'indicator/ПРАВИЛА-НИСХОДЯЩИЙ.md',
    'indicator/ПРАВИЛА-ПРОДОЛЖЕНИЕ.md',
    'indicator/ПРАВИЛА-СЛОМ.md',
    'indicator/РЕШЕНИЯ-ИТОГ.md',
]

SEP = re.compile(r'^\|[\s|:-]+\|$')


def norm(s):
    """Схлопнуть пробелы: перенос строки правилом не считается."""
    return re.sub(r'\s+', ' ', s).strip()


def rules_of(path):
    """ДВА ведра.

    «правил» — строки таблиц, пункты списков и заголовки. Это и есть
    правила в узком смысле, по ним сверяются замечания.

    «прочее» — ВСЕ остальные непустые строки, то есть абзацы доводов.

    Второе ведро заведено сразу после первой же проверки 21.10.2026:
    правка §3 нисходящего легла в АБЗАЦ, и по одному ведру сеть сказала
    только «сумма не та», не назвав строки. Дыра в сети хуже, чем её
    отсутствие — на неё полагаются.

    Цена второго ведра: перенабор абзаца показывает все его строки
    разом. Это шум, но шум ЧЕСТНЫЙ: лучше объяснить лишнее, чем
    пропустить нужное.
    """
    pravil, proch = [], []
    with io.open(path, encoding='utf-8') as f:
        for raw in f:
            s = raw.rstrip('\n').strip()
            if not s:
                continue
            if s.startswith('|'):
                if SEP.match(s):
                    continue
                pravil.append(norm(s))
            elif s.startswith('#') or re.match(r'^([*\-+]|\d+\.)\s', s):
                pravil.append(norm(s))
            else:
                proch.append(norm(s))
    return pravil, proch


def state():
    st = {}
    for rel in FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            st[rel] = {'нет файла': True}
            continue
        data = io.open(p, 'rb').read()
        pravil, proch = rules_of(p)
        st[rel] = {
            'сумма': hashlib.md5(data).hexdigest(),
            'строк': data.decode('utf-8').count('\n'),
            'правил': pravil,
            'прочее': proch,
        }
    return st


def main():
    cur = state()

    if '--snap' in sys.argv:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with io.open(OUT, 'w', encoding='utf-8') as f:
            f.write(json.dumps(cur, ensure_ascii=False, indent=1))
        print('ОТПЕЧАТОК СНЯТ:', OUT)
        for rel in FILES:
            d = cur[rel]
            if 'нет файла' in d:
                print('  %-42s НЕТ ФАЙЛА' % rel.split('/')[-1])
            else:
                print('  %-42s %s  строк %d  правил %d  текста %d'
                      % (rel.split('/')[-1], d['сумма'], d['строк'],
                         len(d['правил']), len(d['прочее'])))
        return 0

    if not os.path.exists(OUT):
        print('ОТПЕЧАТКА НЕТ. Снять: python3 research/pravila.py --snap')
        return 1

    old = json.loads(io.open(OUT, encoding='utf-8').read())
    beda = 0

    for rel in FILES:
        name = rel.split('/')[-1]
        o = old.get(rel)
        n = cur.get(rel)
        if o is None:
            print('%s — НОВЫЙ ФАЙЛ, в отпечатке его нет' % name)
            beda += 1
            continue
        if 'нет файла' in n:
            print('%s — ФАЙЛ ПРОПАЛ' % name)
            beda += 1
            continue
        if o['сумма'] == n['сумма']:
            continue

        print('=' * 68)
        print('%s   %s → %s' % (name, o['сумма'][:8], n['сумма'][:8]))
        print('   строк %d → %d, правил %d → %d, текста %d → %d'
              % (o['строк'], n['строк'], len(o['правил']), len(n['правил']),
                 len(o.get('прочее', [])), len(n.get('прочее', []))))

        tihо = True
        for vedro, titul in (('правил', 'ПРАВИЛА'), ('прочее', 'ТЕКСТ ВНЕ ПРАВИЛ')):
            oo = o.get(vedro, [])
            nn = n.get(vedro, [])
            so, sn = set(oo), set(nn)
            ushlo = [x for x in oo if x not in sn]
            prish = [x for x in nn if x not in so]
            if not ushlo and not prish:
                continue
            tihо = False
            print('\n### %s' % titul)
            if ushlo:
                print('--- ПРОПАЛО (%d) ---' % len(ushlo))
                for x in ushlo:
                    print('  ' + (x if len(x) <= 160 else x[:157] + '...'))
            if prish:
                print('--- ПОЯВИЛОСЬ (%d) ---' % len(prish))
                for x in prish:
                    print('  ' + (x if len(x) <= 160 else x[:157] + '...'))
        if tihо:
            print('\n  ни одна строка не изменилась — правка в пустых строках')
        beda += 1

    print('=' * 68)
    if beda == 0:
        print('ПРАВИЛА СОШЛИСЬ: все своды совпали с отпечатком')
        return 0

    print('РАСХОЖДЕНИЙ: %d файл(ов).' % beda)
    print('Каждую строку из «ПРОПАЛО» надо объяснить вслух: это то,')
    print('о чём просили, или молчаливая потеря. Если второе — вернуть.')
    print('Разобрали и всё верно — закрепить: python3 research/pravila.py --snap')
    return 1


if __name__ == '__main__':
    sys.exit(main())
