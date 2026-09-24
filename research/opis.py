# -*- coding: utf-8 -*-
"""ОПИСЬ · механическая проверка, что ничего не потеряно.

Написан 24.09.2026 по опасению владельца: «у тебя было пару раз, что ты
говорил, что записал, но не делал этого».

Обещанию верить нельзя, проверке можно. Скрипт смотрит САМИ ФАЙЛЫ и
отвечает на три вопроса:

  1. какие З, Н, В вообще записаны и нет ли дыр в нумерации;
  2. все ли они упомянуты в описи вверху своего файла;
  3. не осталось ли чего-то незакоммиченным и неотправленным.

Гонять в конце каждого разговора, где что-то нашли.

    python3 research/opis.py
"""
import re, subprocess, sys, os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FILES = (
    ('З', 'indicator/ЗАМЕЧАНИЯ.md', r'^### З(\d+) · (.+)$'),
    ('Н', 'indicator/НАБЛЮДЕНИЯ.md', r'^### Н(\d+) · (.+)$'),
    # В живёт строкой в очереди: измеренный вопрос уезжает в Н, а здесь
    # остаётся строка со ссылкой. Поэтому ищем по таблице, а не по разделам.
    ('В', 'indicator/ПРОВЕРИТЬ.md', r'^\| \*\*В(\d+)\*\* \| ([^|]+)\|'),
    ('СИТ', 'indicator/СИТУАЦИИ.md', r'^### СИТ(\d+) · (.+)$'),
)


def nofence(t):
    """выкинуть блоки в ``` — там лежит ШАБЛОН записи, а не запись"""
    return re.sub(r'```.*?```', '', t, flags=re.S)

bad = 0
for tag, path, pat in FILES:
    txt = nofence(open(path, encoding='utf-8').read())
    got = {}
    for m in re.finditer(pat, txt, re.M):
        got.setdefault(int(m.group(1)), m.group(2).strip())
    nums = sorted(got)
    print('=' * 70)
    print('%s · %s — записей %d' % (tag, path, len(nums)))
    for n in nums:
        print('   %s%-3d %s' % (tag, n, got[n][:64]))
    if nums:
        holes = [k for k in range(min(nums), max(nums) + 1) if k not in got]
        if holes:
            bad += 1
            print('   !! ДЫРЫ В НУМЕРАЦИИ: ' + ', '.join(tag + str(h) for h in holes))
    # упомянут ли каждый номер в описи/очереди этого же файла
    head = txt.split('---', 1)[0] + txt[:6000]
    miss = [] if tag == 'СИТ' else [n for n in nums if not re.search(r'\*?\*?%s%d\b' % (tag, n), head)]
    if miss:
        bad += 1
        print('   !! НЕТ В ОПИСИ ВВЕРХУ ФАЙЛА: ' + ', '.join(tag + str(m) for m in miss))

print('=' * 70)
dirty = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True).stdout.strip()
if dirty:
    bad += 1
    print('!! НЕ ЗАКОММИЧЕНО:')
    print(dirty)
else:
    print('всё закоммичено')

try:
    ahead = subprocess.run(['git', 'rev-list', '--count', 'origin/HEAD..HEAD'],
                           capture_output=True, text=True).stdout.strip()
except Exception:
    ahead = ''
br = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    capture_output=True, text=True).stdout.strip()
up = subprocess.run(['git', 'rev-list', '--count', 'origin/%s..HEAD' % br],
                    capture_output=True, text=True)
if up.returncode == 0:
    n = up.stdout.strip()
    if n and n != '0':
        bad += 1
        print('!! НЕ ОТПРАВЛЕНО НА СЕРВЕР: %s коммит(ов) на ветке %s' % (n, br))
    else:
        print('всё отправлено на сервер, ветка %s' % br)
else:
    print('ветка %s: сравнить с сервером не вышло' % br)

print()
print('ИТОГ: ' + ('ВСЁ ЧИСТО' if bad == 0 else 'ПРОБЛЕМ: %d — разобрать выше' % bad))
sys.exit(1 if bad else 0)
