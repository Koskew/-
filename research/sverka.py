#!/usr/bin/env python3
"""Сверка двух версий пайна ПО УСЛОВИЯМ ПОКАЗА, а не по тексту.

Обычный diff и подсчёт line.new ловят УДАЛЁННОЕ. Они не ловят
СПРЯТАННОЕ: код на месте, но ушёл под новое условие и на графике
пропал. Так 17.09.2026 у слоя 5/5 молча исчезли штрих-пунктирные
линии, поглощённые метки и одолженные сырые метки.

Скрипт для каждого рисующего вызова собирает цепочку объемлющих
if по отступам и печатает её как подпись. Разница подписей и есть
ответ на вопрос «что стало показываться при других условиях».

    python3 research/sverka.py старый.pine новый.pine
"""
import re, sys

DRAW = re.compile(r'\b(line\.new|label\.new|box\.new|table\.cell|plot|plotshape|bgcolor)\b')
# вызовы СВОИХ рисующих функций: их тело здесь не видно, поэтому
# сравниваем сам вызов целиком — вместе с аргументами. Флаг, переданный
# аргументом (как _labK), гасит рисование не хуже объемлющего if
CALL = re.compile(r'=\s*(f_draw|f_lvlLayer|f_drawAbs|f_lvlHTF)\s*\(')

def indent(s):
    return len(s) - len(s.lstrip(' '))

def signatures(path):
    lines = open(path, encoding='utf-8').read().split('\n')
    out = []
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith('//'):
            continue
        mcall = CALL.search(ln)
        if not DRAW.search(ln) and not mcall:
            continue
        # цепочка условий вверх по отступам
        chain, lvl = [], indent(ln)
        for j in range(i - 1, -1, -1):
            prev = lines[j]
            if not prev.strip() or prev.lstrip().startswith('//'):
                continue
            pi = indent(prev)
            if pi < lvl:
                head = prev.strip()
                if head.startswith(('if ', 'else if ')):
                    chain.append(head)
                elif head == 'else':
                    chain.append('else')
                elif head.startswith(('for ', 'while ')):
                    chain.append(head.split('=')[0].strip() + ' …')
                lvl = pi
                if lvl == 0:
                    break
        if mcall:
            what = mcall.group(1)
            # весь вызов с аргументами: меняется аргумент — меняется показ
            tag = re.sub(r'\s+', ' ', ln.strip().split('=', 1)[1].strip())
        else:
            what = DRAW.search(ln).group(1)
            tag = ''
            m = re.search(r'"([^"]{0,40})"', ln)
            if m:
                tag = m.group(1)[:24]
        out.append((what, tag, ' ◂ '.join(reversed(chain))))
    return out

def show(rows, title):
    print(f'\n=== {title}: {len(rows)} рисующих вызовов ===')

a, b = sys.argv[1], sys.argv[2]
A, B = signatures(a), signatures(b)
show(A, 'было'); show(B, 'стало')

sa = {(w, t, c) for w, t, c in A}
sb = {(w, t, c) for w, t, c in B}

gone = [r for r in A if r not in sb]
new  = [r for r in B if r not in sa]

if not gone and not new:
    print('\nУсловия показа не менялись.')
else:
    if gone:
        print('\n--- ПРОПАЛО или сменило условие показа ---')
        for w, t, c in gone:
            print(f'  {w:11} ⟵ {c}\n      {t}')
    if new:
        print('\n--- ПОЯВИЛОСЬ или под новым условием ---')
        for w, t, c in new:
            print(f'  {w:11} ⟵ {c}\n      {t}')
    print('\nКаждую строку из «ПРОПАЛО» надо объяснить: это то, о чём')
    print('просили, или молчаливая потеря. Если второе — не отдавать.')
