# -*- coding: utf-8 -*-
"""Сверка реплики с CSV-экспортом индикатора из TradingView.

Экспорт содержит plotshape-колонки вердиктов. Они заполнены только ВНЕ окна
tooltip (последние v5_tip_bars баров): внутри окна точки рисуются метками,
а метки в CSV не выгружаются. Сверяем на заполненном участке.
"""
import itertools
import sys
import numpy as np
import pandas as pd
from replica import Cfg, run

COLMAP = {
    'ВХОД':             lambda v: v == 'ВХОД',
    'Запрет структуры': lambda v: v is not None and v.startswith('запрет'),
    'Против тренда':    lambda v: v == 'против тренда',
    'Слом':             lambda v: v == 'слом',
    'Заморозка':        lambda v: v == 'заморозка',
    'Бол.свеча':        lambda v: v == 'бол.свеча',
    'Нет RR':           lambda v: v == 'нет RR',
    'Стоп-неделя':      lambda v: v == 'стоп-неделя',
    'Фильтр БОК+LONG':  lambda v: v == 'режим БОК+LONG',
    'Прочее':           lambda v: v in ('нет меток', 'мало триггеров', 'стоп?'),
}


def load(path):
    d = pd.read_csv(path)
    cols = [c for c in COLMAP if c in d.columns]
    V = d[cols].apply(pd.to_numeric, errors='coerce').fillna(0) != 0
    idx = np.where(V.any(axis=1).values)[0]
    return d, V, (idx.min(), idx.max())


def score(d, V, span, cfg):
    verdicts, trades, meta = run(d, cfg)
    lo, hi = span
    ok = bad = 0
    conf = {}
    for i in range(lo, hi + 1):
        exp = [c for c in V.columns if V[c].iloc[i]]
        got = verdicts[i]
        exp_name = exp[0] if exp else None
        got_name = next((c for c, f in COLMAP.items() if got is not None and f(got)), None)
        if exp_name is None and got_name is None:
            continue
        if exp_name == got_name:
            ok += 1
        else:
            bad += 1
            conf[(exp_name, got_name)] = conf.get((exp_name, got_name), 0) + 1
    return ok, bad, conf, trades, meta


if __name__ == '__main__':
    files = [('5m', sys.argv[1]), ('1H', sys.argv[2])]
    grid = list(itertools.product(['fix', 'auto'], [False, True], [False, True]))
    for name, path in files:
        d, V, span = load(path)
        print(f"\n═══════ {name}: сверяемый участок бары {span[0]}–{span[1]} ═══════")
        best = None
        for mode, ws, rf in grid:
            cfg = Cfg(thr_mode=mode, use_ws=ws, use_regfilt=rf)
            ok, bad, conf, tr, meta = score(d, V, span, cfg)
            tag = f"порог={mode:<4} предохр={'вкл' if ws else 'выкл'} режфильтр={'вкл' if rf else 'выкл'}"
            pct = ok / (ok + bad) * 100 if ok + bad else 0
            print(f"  {tag}  совпало {ok:>5}/{ok+bad:<5} = {pct:6.2f}%")
            if best is None or ok - bad > best[0]:
                best = (ok - bad, cfg, ok, bad, conf, tr, meta, tag)
        _, cfg, ok, bad, conf, tr, meta, tag = best
        print(f"\n  ЛУЧШАЯ: {tag} → {ok}/{ok+bad} = {ok/(ok+bad)*100:.2f}%")
        if conf:
            print("  расхождения (ожидалось → получено):")
            for (e, g), n in sorted(conf.items(), key=lambda x: -x[1])[:12]:
                print(f"     {str(e):<20} → {str(g):<20} {n:>5}")
