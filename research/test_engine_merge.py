# -*- coding: utf-8 -*-
"""Проверка, что engine.py эквивалентен связке engine_v3 + engine_v4 + engine_v5.

Оригиналы оставлены в репозитории только ради этой проверки. Рабочий файл —
engine.py.
"""
import importlib.util
import sys

import pandas as pd

import engine


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compare(path):
    e3 = _load('e3', 'engine_v3.py')
    e4 = _load('e4', 'engine_v4.py')
    e5 = _load('e5', 'engine_v5.py')

    E_old = e3.build_engine(path)
    E_new = engine.build_engine(path, trig='column')

    assert (E_old['TRIG'] == E_new['TRIG']).all(), 'разошлись триггеры'
    assert abs(E_old['size_thr_pct'] - E_new['size_thr_pct']) < 1e-12, 'разошёлся порог'
    assert E_old['fast'] == E_new['fast'], 'разошлись метки структуры'

    report = []
    for ver, old_run in ((4, lambda: e4.run_v4(E_old)), (5, lambda: e5.run_v5(E_old, e4))):
        a = old_run().reset_index(drop=True)
        b = engine.run(E_new, version=ver).reset_index(drop=True)
        same = len(a) == len(b)
        if same and len(a):
            cols = ['i', 'dir', 'last', 'entry', 'stop', 'tp', 'RR', 'out', 'R']
            same = a[cols].equals(b[cols])
        report.append((ver, len(a), len(b), same,
                       a['R'].sum() if len(a) else 0.0, b['R'].sum() if len(b) else 0.0))

    # повердиктная сверка, а не только по сделкам
    v_old = {int(i): e5.decide_v5(E_old, int(i), e4).get('decision')
             for i in range(E_old['N']) if E_old['TRIG'][i]}
    v_new = engine.verdicts(E_new, version=5)
    diff = [k for k in v_old if v_old[k] != v_new.get(k)]
    return report, len(v_old), diff


if __name__ == '__main__':
    ok = True
    for path in sys.argv[1:]:
        report, nverd, diff = compare(path)
        print(f"\n═══ {path} ═══")
        for ver, na_, nb, same, ra, rb in report:
            mark = 'совпало' if same else 'РАЗОШЛОСЬ'
            print(f"  v{ver}: старое {na_} сделок / {ra:+.1f}R | новое {nb} / {rb:+.1f}R → {mark}")
            ok &= same
        print(f"  вердиктов сверено {nverd}, расхождений {len(diff)}")
        ok &= not diff
    print('\nИТОГ:', 'эквивалентно' if ok else 'ЕСТЬ РАСХОЖДЕНИЯ')
    sys.exit(0 if ok else 1)
