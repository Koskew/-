# -*- coding: utf-8 -*-
"""
Python-реплика каскада индикатора «Тренажёр v8» (Pine v5).

Назначение: измерять последствия правок на реальных данных до того, как
они попадут в Pine. Реплика намеренно повторяет ПОВЕДЕНИЕ индикатора,
включая известные дефекты, — они выключаются флагами в Cfg.

Сверка: verify.py сравнивает вердикты реплики с колонками CSV-экспорта
самого индикатора из TradingView.
"""
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

# 40 шаблонов триггерных свечей: доли body/upper/lower от диапазона, %
TB = [12.6,14.7,17.0,32.0,20.2,4.1,23.0,27.9,30.7,35.2,24.5,41.9,26.0,25.9,11.6,23.3,49.3,14.0,18.3,25.4,
      27.9,45.7,29.2,40.6,41.9,10.4,41.5,23.6,32.2,18.8,35.5,32.2,54.2,10.8,47.3,16.0,21.6,19.8,9.9,27.5]
TU = [33.7,37.3,37.7,27.8,29.4,40.4,35.7,35.3,41.0,35.7,28.4,22.0,39.6,37.4,46.0,31.5,21.5,27.5,47.3,35.6,
      26.2,24.8,36.3,36.7,26.8,35.6,20.7,34.5,36.4,46.2,38.6,33.6,21.6,44.1,22.9,45.2,42.8,45.2,41.5,30.7]
TL = [53.7,48.0,45.3,40.2,50.4,55.5,41.3,36.8,28.3,29.1,71.6,36.0,34.5,36.7,42.5,45.2,29.2,58.5,34.4,39.0,
      46.0,29.5,34.5,22.6,31.3,54.0,37.9,41.9,31.4,34.9,25.8,34.2,24.2,45.1,29.8,38.8,35.5,35.0,48.6,41.8]

# Шаблон #10 недостижим: 24.5+28.4+71.6 = 124.5, а сумма долей всегда 100.
TL_FIXED = list(TL)
TL_FIXED[10] = round(100.0 - TB[10] - TU[10], 1)   # 47.1

BANNED_TAILS = ('LL>HH', 'HH>LH', 'LL>LH>HL', 'HH>LL>LL')


@dataclass
class Cfg:
    tol: float = 4.0
    thr_mode: str = 'fix'          # 'fix' | 'auto'
    thr_fix: float = 0.317
    pctl: float = 80.0
    min_smpl: int = 20
    rr_min: float = 3.0
    buf_pct: float = 0.1
    buf_mode: str = 'pct_price'    # 'pct_price' (как сейчас) | 'pct_range' (доля диапазона бара)
    pivot_mode: str = 'pine'       # 'pine' (>= слева, > справа) | 'engine' (> с обеих сторон, как fp() в engine_v3)
    horizon: int = 0               # 0 = держать до исхода (Pine); 1500 = как resolve() в engine_v4
    buf_k: float = 0.10            # для 'pct_range': буфер = k * (high-low)
    use_ws: bool = True
    ws_r: float = 3.0
    use_regfilt: bool = False
    # переключатели дефектов: False = как в индикаторе сейчас
    fix_template10: bool = False   # починить недостижимый шаблон #10
    fix_equal_pivots: bool = False # равный пивот наследует тип предыдущего, а не исчезает
    fix_d3_restart: bool = False   # тренд не перезапускается без новой пары меток 5/5


def shape_flags(o, h, l, c, cfg):
    """Матрица совпадений с шаблонами и итоговый признак триггерной свечи."""
    rng = h - l
    body = np.abs(c - o)
    up = np.where(o > c, h - o, h - c)
    lo = np.where(o > c, c - l, o - l)
    with np.errstate(divide='ignore', invalid='ignore'):
        bp = np.where(rng > 0, body / rng * 100.0, 0.0)
        upp = np.where(rng > 0, up / rng * 100.0, 0.0)
        lop = np.where(rng > 0, lo / rng * 100.0, 0.0)
    tl = TL_FIXED if cfg.fix_template10 else TL
    m = np.zeros((len(o), 40), bool)
    for i in range(40):
        m[:, i] = ((np.abs(bp - TB[i]) <= cfg.tol) &
                   (np.abs(upp - TU[i]) <= cfg.tol) &
                   (np.abs(lop - tl[i]) <= cfg.tol))
    return m, m.any(axis=1)


def pivot_bars(x, left, right, mode='pine'):
    """Пивоты. mode='pine' — правило ta.pivothigh: >= слева, > справа.
    mode='engine' — правило fp() из engine_v3: строго > с обеих сторон."""
    n = len(x)
    out = np.zeros(n, bool)
    for i in range(left, n - right):
        v = x[i]
        left_ok = all(v > x[j] for j in range(i - left, i)) if mode == 'engine' \
            else all(v >= x[j] for j in range(i - left, i))
        if left_ok and all(v > x[j] for j in range(i + 1, i + right + 1)):
            out[i] = True
    return out


def percentile_lin(arr, p):
    """Аналог Pine array.percentile_linear_interpolation."""
    return float(np.percentile(np.asarray(arr, float), p, method='linear'))


def label_high(prev, cur, fix_equal):
    """Метка вершины относительно предыдущей вершины."""
    if prev is None:
        return None                      # первый пивот: valuewhen(...,1) = na
    if cur > prev:
        return 'HH'
    if cur < prev:
        return 'LH'
    return 'LH' if fix_equal else None    # равенство: сейчас метка теряется


def label_low(prev, cur, fix_equal):
    """Метка впадины относительно предыдущей впадины."""
    if prev is None:
        return None
    if cur > prev:
        return 'HL'
    if cur < prev:
        return 'LL'
    return 'HL' if fix_equal else None


def run(df, cfg=None):
    """Прогон каскада по барам. Возвращает (verdicts, trades, meta).

    verdicts — список длиной len(df): None на нетриггерных барах, иначе строка
    вердикта в терминах индикатора. trades — DataFrame закрытых сделок.
    """
    cfg = cfg or Cfg()
    o, h, l, c = (df[x].astype(float).values for x in ('open', 'high', 'low', 'close'))
    t = pd.to_datetime(df['time'], format='ISO8601', utc=True)
    n = len(df)

    _, trig = shape_flags(o, h, l, c, cfg)
    sz_pct = np.where(c > 0, (h - l) / c * 100.0, 0.0)

    pm = cfg.pivot_mode
    ph2, pl2 = pivot_bars(h, 2, 2, pm), pivot_bars(-l, 2, 2, pm)
    ph5, pl5 = pivot_bars(h, 5, 5, pm), pivot_bars(-l, 5, 5, pm)

    # очередь быстрых меток: (label, price, side, confirm_bar), максимум 5
    q = []
    prev_h2 = prev_l2 = None
    prev_h5 = prev_l5 = None

    d3_state, d3_lvl, d3_lastH, d3_lastL, d3_lastHp, d3_lastLp = 0, None, '', '', None, None
    d3_armed = True          # для fix_d3_restart: перезапуск разрешён только после новой метки

    trig_sz, verdicts = [], [None] * n
    pos, closed = [], []
    wk_key, wk_r = None, 0.0

    for i in range(n):
        # ── 1. быстрые метки 2/2 (подтверждение через 2 бара) ──────────────
        j = i - 2
        newH = newL = False
        if j >= 0 and ph2[j]:
            lab = label_high(prev_h2, h[j], cfg.fix_equal_pivots)
            prev_h2 = h[j]
            if lab:
                q.append((lab, h[j], 'high', i)); newH = True
        if j >= 0 and pl2[j]:
            lab = label_low(prev_l2, l[j], cfg.fix_equal_pivots)
            prev_l2 = l[j]
            if lab:
                q.append((lab, l[j], 'low', i)); newL = True
        del q[:-5]

        # ── 2. медленные метки 5/5 и тренд D3 ─────────────────────────────
        k = i - 5
        n5H = n5L = False
        if k >= 0 and ph5[k]:
            lab = label_high(prev_h5, h[k], cfg.fix_equal_pivots)
            prev_h5 = h[k]
            if lab:
                d3_lastH, d3_lastHp, n5H = lab, h[k], True
                d3_armed = True
                if d3_state == -1 and lab == 'LH':
                    d3_lvl = h[k]
        if k >= 0 and pl5[k]:
            lab = label_low(prev_l5, l[k], cfg.fix_equal_pivots)
            prev_l5 = l[k]
            if lab:
                d3_lastL, d3_lastLp, n5L = lab, l[k], True
                d3_armed = True
                if d3_state == 1 and lab == 'HL':
                    d3_lvl = l[k]
        if d3_state == 0 and (d3_armed or not cfg.fix_d3_restart):
            if d3_lastH == 'HH' and d3_lastL == 'HL':
                d3_state, d3_lvl = 1, d3_lastLp
                d3_armed = False
            elif d3_lastH == 'LH' and d3_lastL == 'LL':
                d3_state, d3_lvl = -1, d3_lastHp
                d3_armed = False
        body_lo, body_hi = min(o[i], c[i]), max(o[i], c[i])
        if d3_state == 1 and d3_lvl is not None and body_lo < d3_lvl:
            d3_state, d3_lvl, d3_armed = 0, None, False
        elif d3_state == -1 and d3_lvl is not None and body_hi > d3_lvl:
            d3_state, d3_lvl, d3_armed = 0, None, False

        # ── 3. порог размера свечи (текущий бар входит в собственный порог) ─
        if trig[i]:
            trig_sz.append(sz_pct[i])
        if cfg.thr_mode == 'fix':
            thr = cfg.thr_fix
        else:
            thr = percentile_lin(trig_sz, cfg.pctl) if len(trig_sz) >= cfg.min_smpl else None

        # ── 4. неделя ──────────────────────────────────────────────────────
        iso = t.iloc[i].isocalendar()
        key = iso[0] * 100 + iso[1]
        if key != wk_key:
            wk_key, wk_r = key, 0.0

        # ── 5. закрытие позиций (до решения — как в Pine) ──────────────────
        for p in list(pos):
            if i <= p['bar']:
                continue
            if cfg.horizon and i - p['bar'] >= cfg.horizon:
                pos.remove(p)          # engine_v4: не разрешилось за HORIZON — сделка отброшена
                continue
            hit_sl = (l[i] <= p['sl']) if p['long'] else (h[i] >= p['sl'])
            hit_tp = (h[i] >= p['tp']) if p['long'] else (l[i] <= p['tp'])
            if hit_sl or hit_tp:
                R = -1.0 if hit_sl else abs(p['tp'] - p['en']) / abs(p['en'] - p['sl'])
                closed.append(dict(dt_in=t.iloc[p['bar']], dt_out=t.iloc[i], dir='LONG' if p['long'] else 'SHORT',
                                   entry=p['en'], stop=p['sl'], tp=p['tp'], out='SL' if hit_sl else 'TP',
                                   R=R, bars=i - p['bar']))
                wk_r += R
                pos.remove(p)

        # ── 6. решение ─────────────────────────────────────────────────────
        if not trig[i]:
            continue
        if cfg.use_ws and wk_r <= -cfg.ws_r:
            verdicts[i] = 'стоп-неделя'
            continue
        vd, dd, en, sl, tp = decide(q, i, sz_pct[i], thr, c[i], h[i], l[i], cfg)
        if vd == 'ВХОД' and cfg.use_regfilt and dd == 'LONG' and d3_state == 0:
            vd = 'режим БОК+LONG'
        verdicts[i] = vd
        if vd == 'ВХОД':
            pos.append(dict(long=dd == 'LONG', en=en, sl=sl, tp=tp, bar=i))

    return verdicts, pd.DataFrame(closed), dict(n_trig=int(trig.sum()))


def decide(q, i, sz, thr, close_, high_, low_, cfg):
    """Каскад decide_v4 + запреты v5. Возвращает (вердикт, направление, entry, stop, tp)."""
    if not q:
        return 'нет меток', None, None, None, None
    last = q[-1][0]
    is_long = last in ('HL', 'LL')
    dd = 'LONG' if is_long else 'SHORT'
    lag = i - q[-1][3]
    up = sum(1 for x in q if x[0] in ('HH', 'HL'))
    dn = sum(1 for x in q if x[0] in ('LH', 'LL'))
    had_slom = any((q[j - 1][0] == 'HH' and q[j][0] == 'LL') or (q[j - 1][0] == 'LL' and q[j][0] == 'HL')
                   for j in range(1, len(q)))
    prev = q[-2][0] if len(q) >= 2 else ''
    fresh_slom = (prev == 'HH' and last == 'LL') or (prev == 'LL' and last == 'HL')

    if last in ('LL', 'HH') and lag <= 1:
        return 'заморозка', dd, None, None, None
    if thr is None:
        return 'мало триггеров', dd, None, None, None
    if sz > thr:
        return 'бол.свеча', dd, None, None, None
    if not had_slom and not is_long and up >= (3 if last == 'HH' else 4):
        return 'против тренда', dd, None, None, None
    if not had_slom and is_long and dn >= 4:
        return 'против тренда', dd, None, None, None
    if fresh_slom:
        return 'слом', dd, None, None, None

    en = close_
    if cfg.buf_mode == 'pct_range':
        buf = (high_ - low_) * cfg.buf_k
        sl = (low_ - buf) if is_long else (high_ + buf)
    else:
        sl = low_ * (1 - cfg.buf_pct / 100) if is_long else high_ * (1 + cfg.buf_pct / 100)
    if (is_long and sl >= en) or (not is_long and sl <= en):
        return 'стоп?', dd, None, None, None
    risk = abs(en - sl)
    want = 'high' if is_long else 'low'
    cand = [x[1] for x in q if x[2] == want and ((x[1] > en) if is_long else (x[1] < en))]
    cand.sort(reverse=not is_long)
    tp = next((p for p in cand if abs(p - en) / risk >= cfg.rr_min), None)
    if tp is None:
        return 'нет RR', dd, None, None, None

    s5 = '>'.join(x[0] for x in q)
    for b in BANNED_TAILS:
        if s5.endswith(b):
            return 'запрет ' + b, dd, en, sl, tp
    return 'ВХОД', dd, en, sl, tp
