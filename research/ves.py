"""Вес разделов и настроек пайна — для поиска, что можно убрать под предел
80 000 токенов. Оценка: research/tokeny.py × 3.1 (калибровка 21.11.2026 по
v3.45: 26 657 → 82 741). Не закон, а прикидка.
    python3 research/ves.py indicator/metki_2x2.pine
"""
import re, sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
import tokeny
K = 3.1
L, T = tokeny.regions(sys.argv[1])
code = [re.sub(r'//.*$', '', l) if '"' not in l else l for l in L]
ind = [len(l) - len(l.lstrip()) if l.strip() else None for l in L]

def block_end(i):
    j = i + 1
    while j < len(L) and (ind[j] is None or ind[j] > ind[i]):
        j += 1
    return j

# 1 · разделы по заголовкам «// ══»
heads = [i for i, l in enumerate(L) if l.startswith('// ══')]
print('=== РАЗДЕЛЫ ===')
rows = []
for a, b in zip(heads, heads[1:] + [len(L)]):
    nm = L[a].strip('/ ═').strip() or (L[a + 1].strip('/ ═').strip() if a + 1 < len(L) else '')
    rows.append((sum(T[a:b]), a + 1, nm[:60]))
for t, a, nm in sorted(rows, reverse=True):
    print('%6d  строка %5d  %s' % (round(t * K), a, nm))
print('итого %d' % round(sum(T) * K))

# 2 · настройки: объявление + блоки if, чьё условие её читает, + строки, где она стоит
print('\n=== НАСТРОЙКИ ===')
inp = []
for i, l in enumerate(L):
    m = re.match(r'^(\w+)\s*=\s*input\.\w+\((.*)', l)
    if m:
        lab = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))
        first_str = m.group(2).lstrip().startswith('"')
        title = (lab[1] if len(lab) > 1 else '') if first_str else (lab[0] if lab else '')
        inp.append((m.group(1), i, title))
res = []
for v, i, lab in inp:
    lines = set([i])
    for j, c in enumerate(code):
        if j == i or not re.search(r'\b%s\b' % v, c):
            continue
        if re.match(r'\s*(if|else if|while)\b', c):
            lines.update(range(j, block_end(j)))
        else:
            lines.add(j)
    res.append((sum(T[j] for j in lines), v, lab, len(lines)))
for t, v, lab, n in sorted(res, reverse=True):
    print('%6d  %-8s %s' % (round(t * K), v, lab[:70]))
