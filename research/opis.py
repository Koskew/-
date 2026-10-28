# -*- coding: utf-8 -*-
"""ОПИСЬ · механическая проверка, что ничего не потеряно.

Написан 24.09.2026 по опасению владельца: «у тебя было пару раз, что ты
говорил, что записал, но не делал этого».

Обещанию верить нельзя, проверке можно. Скрипт смотрит САМИ ФАЙЛЫ и
отвечает на три вопроса:

  1. какие З, Н, В, СИТ и Р вообще записаны и нет ли дыр в нумерации;
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
    # Р заведён 14.10.2026, слово владельца: «может собирать базу вопросов
    # и ответов на них + решение». Карточка — заголовок второго уровня, и
    # каждая обязана быть названа в таблице «КАК ИСКАТЬ» вверху файла,
    # иначе база перестанет искаться — то есть перестанет быть базой.
    ('Р', 'indicator/БАЗА-РЕШЕНИЙ.md', r'^## Р(\d+) · (.+)$'),
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
    # 06.10.2026: окно расширено с 6000 до 20000. Опись НАБЛЮДЕНИЙ выросла
    # — добавилась колонка «движок» и легенда под таблицей, — и последние
    # строки уехали за старое окно. Скрипт ругался на Н30, который в описи
    # был. Ложная тревога от собственной линейки, а не от файла.
    #
    # 28.10.2026: ТО ЖЕ САМОЕ ПОВТОРИЛОСЬ на З58 — опись доросла до знака
    # 20561 при окне 20000. Подкручивать число в третий раз нельзя: сеть,
    # которая врёт по собственной мерке, хуже отсутствующей.
    #
    # Окно теперь СТРУКТУРНОЕ: опись лежит ВЫШЕ первой записи, а запись —
    # это заголовок с номером. Значит голова файла кончается там, где
    # начинается первая запись, сколько бы опись ни выросла.
    #
    # НО БЕРЁТСЯ МАКСИМУМ ИЗ ДВУХ, и вот почему. Одно структурное окно
    # вышло УЖЕ прежнего у `ПРОВЕРИТЬ.md` и `БАЗА-РЕШЕНИЙ.md`: там таблица
    # «ОЧЕРЕДЬ» и «КАК ИСКАТЬ» стоит НИЖЕ первой записи, и сеть разом
    # наврала на 27 номерах, которые в описи есть. Максимум оставляет
    # прежние 20000 как пол: сеть от правки только строже, никогда слабее.
    first = re.search(pat, txt, re.M)
    head = txt.split('---', 1)[0] + txt[:max(first.start() if first else 0, 20000)]
    miss = [] if tag == 'СИТ' else [n for n in nums if not re.search(r'\*?\*?%s%d\b' % (tag, n), head)]
    if miss:
        bad += 1
        print('   !! НЕТ В ОПИСИ ВВЕРХУ ФАЙЛА: ' + ', '.join(tag + str(m) for m in miss))

# ── ДЛИНА БЛОКОВ `if barstate.islast`. Заведено 15.10.2026, З46 ──
# v3.9 не скомпилировалась: «The if statement is too long». В v3.8 в
# одном блоке было 281 строка кода и 40 346 символов и компилировалось,
# в v3.9 стало 302 и 44 360 — не стало. Предел лежит между, точного
# числа TradingView не называет. Поэтому порог здесь КОНСЕРВАТИВНЫЙ:
# ругаемся с 260 строк, то есть раньше, чем станет поздно.
LIMIT_LINES = 260
print('=' * 70)
try:
    pine = open('indicator/metki_2x2.pine', encoding='utf-8').read().split('\n')
except IOError:
    pine = []
blocks = []
for i, ln in enumerate(pine):
    if ln == 'if barstate.islast':
        j = i + 1
        while j < len(pine) and (not pine[j].strip() or pine[j].startswith(' ') or pine[j].startswith('\t')):
            j += 1
        body = [x for x in pine[i + 1:j] if x.strip() and not x.strip().startswith('//')]
        blocks.append((i + 1, len(body), sum(len(x) for x in body)))
if blocks:
    print('БЛОКИ «if barstate.islast» в metki_2x2.pine — предел TradingView, З46')
    for n, (ln, cnt, ch) in enumerate(blocks, 1):
        mark = ' !! БЛИЗКО К ПРЕДЕЛУ' if cnt >= LIMIT_LINES else ''
        print('   блок %d, строка %-5d кода %3d строк, %6d символов%s' % (n, ln, cnt, ch, mark))
        if cnt >= LIMIT_LINES:
            bad += 1
    if not any(c >= LIMIT_LINES for _, c, _ in blocks):
        print('   все блоки с запасом (порог %d строк)' % LIMIT_LINES)

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
