"""Грубая оценка «токенов» пайна по участкам. Предел TradingView — 80 000
на скомпилированный код. Счёт: каждое слово, число и знак — 1, строка —
1 + длина/14 (калибровка v3.30, CLAUDE.md). Комментарии не считаются.
    python3 research/tokeny.py файл.pine [метка-начала метка-конца ...]
"""
import re, sys
TOK = re.compile(r'"(?:[^"\\]|\\.)*"|[A-Za-z_][\w.]*|\d+\.?\d*|==|!=|<=|>=|:=|=>|[^\s\w]')
def tok(line):
    code = re.sub(r'//.*$', '', line) if '"' not in line else line
    if '"' in line:
        # срезать комментарий вне строк
        out, q = '', False
        for i, ch in enumerate(line):
            if ch == '"': q = not q
            if not q and line[i:i+2] == '//': break
            out += ch
        code = out
    n = 0
    for t in TOK.findall(code):
        n += 1 + (len(t) // 14 if t.startswith('"') else 0)
    return n
def regions(path):
    L = open(path, encoding='utf-8').read().split('\n')
    return L, [tok(l) for l in L]
if __name__ == '__main__':
    L, T = regions(sys.argv[1])
    print('всего', sum(T))
