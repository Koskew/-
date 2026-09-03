# -*- coding: utf-8 -*-
"""
ДВИЖОК — единый файл вместо engine_v3.py + engine_v4.py + engine_v5.py.

Родословная (сохранена дословно, поведение не изменено):
    v3 — построение движка, пивоты, метки, перцентильный порог размера свечи,
         мягкая заморозка по слому, запрет входа против явного тренда.
    v4 — тот же каскад, но порог согласованности 3/5 вместо 4/5 ТОЛЬКО для
         шортов от HH. Плюс изменён порядок: заморозка проверяется ДО размера
         свечи (в v3 было наоборот).
    v5 — v4 плюс четыре запрета по хвосту структуры.

Эталон v5 на золоте 9 лет: 939 сделок, +53.2R (train +31.2 / test +22.0), WR 20%.
Эталон v4 там же: 1246 сделок, −38.5R.
ВНИМАНИЕ: на BTC и серебре пакет запретов НЕ работает. Не переносить без проверки.
НЕ сделано: контроль случайностью, помесячная развёртка, walk-forward.

Использование:
    import engine
    E = engine.build_engine('xau_1h_master.csv')
    trades = engine.run(E, version=5)      # DataFrame сделок

Что выброшено при слиянии (было мёртвым во всех трёх файлах):
    COST=0.20        объявлена, нигде не используется — спред и комиссия
                     не моделируются движком вообще;
    ATR_WIN/ATR_MULT помечены неиспользуемыми самим автором ещё в v3;
    decide_point()   логика поколения v3, из v4/v5 не вызывалась.
Поведение живого кода не тронуто. Сверка с оригинальной связкой трёх файлов —
в test_engine_merge.py, сделки совпадают один в один.
"""
import bisect

import numpy as np
import pandas as pd

# ── константы ────────────────────────────────────────────────────────────────
GRID = 5.0             # шаг сетки круглых уровней для варианта стопа «уровень»
HORIZON = 1500         # баров на резолв сделки; не разрешилась — сделка отброшена
BUF = 0.001            # буфер стопа за свечой, 0.1%
FRESH_MARKS = 5        # сколько последних меток образуют «структуру»
SIZE_PERCENTILE = 80   # свеча больше 80-го перцентиля триггеров считается большой
TREND_MARKS = 5
TREND_MIN = 4          # явный тренд: >= 4 из 5 меток в одну сторону

BANNED_TAILS = ('LL>HH', 'LL>LH>HL', 'HH>LH', 'HH>LL>LL')

# 40 шаблонов триггерных свечей — доли body/upper/lower от диапазона бара, %.
# ВАЖНО: шаблонов НЕТ в исходных engine_v3/v4/v5 — там триггеры приходили
# готовой колонкой «триггер» из мастер-файла. Это реконструкция из индикатора
# на Pine, нужна чтобы движок работал на любом OHLC-файле. Эталонные 939 сделок
# считались по колонке мастер-файла, а не по этим шаблонам.
# Шаблон #10 (24.5/28.4/71.6) недостижим: сумма долей всегда ровно 100, а тут
# 124.5. Оставлен как есть — правка изменила бы вердикты, см. research/README.md.
TPL_BODY = [12.6, 14.7, 17.0, 32.0, 20.2, 4.1, 23.0, 27.9, 30.7, 35.2,
            24.5, 41.9, 26.0, 25.9, 11.6, 23.3, 49.3, 14.0, 18.3, 25.4,
            27.9, 45.7, 29.2, 40.6, 41.9, 10.4, 41.5, 23.6, 32.2, 18.8,
            35.5, 32.2, 54.2, 10.8, 47.3, 16.0, 21.6, 19.8, 9.9, 27.5]
TPL_UPPER = [33.7, 37.3, 37.7, 27.8, 29.4, 40.4, 35.7, 35.3, 41.0, 35.7,
             28.4, 22.0, 39.6, 37.4, 46.0, 31.5, 21.5, 27.5, 47.3, 35.6,
             26.2, 24.8, 36.3, 36.7, 26.8, 35.6, 20.7, 34.5, 36.4, 46.2,
             38.6, 33.6, 21.6, 44.1, 22.9, 45.2, 42.8, 45.2, 41.5, 30.7]
TPL_LOWER = [53.7, 48.0, 45.3, 40.2, 50.4, 55.5, 41.3, 36.8, 28.3, 29.1,
             71.6, 36.0, 34.5, 36.7, 42.5, 45.2, 29.2, 58.5, 34.4, 39.0,
             46.0, 29.5, 34.5, 22.6, 31.3, 54.0, 37.9, 41.9, 31.4, 34.9,
             25.8, 34.2, 24.2, 45.1, 29.8, 38.8, 35.5, 35.0, 48.6, 41.8]
TPL_TOL = 4.0          # допуск формы, ±% по каждой из трёх осей


# ── триггерные свечи ─────────────────────────────────────────────────────────
def triggers_from_shape(O, H, L, C, tol=TPL_TOL):
    """Признак триггерной свечи по 40 шаблонам формы (реконструкция из Pine)."""
    rng = H - L
    body = np.abs(C - O)
    up = np.where(O > C, H - O, H - C)
    lo = np.where(O > C, C - L, O - L)
    with np.errstate(divide='ignore', invalid='ignore'):
        bp = np.where(rng > 0, body / rng * 100.0, 0.0)
        upp = np.where(rng > 0, up / rng * 100.0, 0.0)
        lop = np.where(rng > 0, lo / rng * 100.0, 0.0)
    hit = np.zeros(len(O), bool)
    for k in range(len(TPL_BODY)):
        hit |= ((np.abs(bp - TPL_BODY[k]) <= tol) &
                (np.abs(upp - TPL_UPPER[k]) <= tol) &
                (np.abs(lop - TPL_LOWER[k]) <= tol))
    return hit


# ── структура: пивоты и метки ────────────────────────────────────────────────
def fp(v, a, b, mode, N, H, L):
    """Бары-пивоты: строго больше (меньше) a баров слева и b справа.

    Отличие от Pine: ta.pivothigh допускает равенство слева (>=), здесь строго.
    На ничьих результаты расходятся — см. research/README.md.
    """
    out = []
    for i in range(a, N - b):
        cc = v[i]
        if mode == 'high':
            if cc > v[i - a:i].max() and cc > v[i + 1:i + b + 1].max():
                out.append(i)
        else:
            if cc < v[i - a:i].min() and cc < v[i + 1:i + b + 1].min():
                out.append(i)
    return out


def mk(a, b, N, H, L):
    """Метки HH/LH/HL/LL в порядке подтверждения.

    Первый пивот каждой стороны метки не получает (не с чем сравнивать).
    Пивот, равный предыдущему по цене, метки тоже не получает и выпадает из
    структуры — тот же дефект есть в Pine (vw1 == vw2), см. research/README.md.
    """
    rows = []
    prev = None
    for i in fp(H, a, b, 'high', N, H, L):
        if prev is not None and H[i] != prev:
            rows.append(dict(bar=i, conf=i + b, label='HH' if H[i] > prev else 'LH',
                             price=H[i], side='high'))
        prev = H[i]
    prev = None
    for i in fp(L, a, b, 'low', N, H, L):
        if prev is not None and L[i] != prev:
            rows.append(dict(bar=i, conf=i + b, label='HL' if L[i] > prev else 'LL',
                             price=L[i], side='low'))
        prev = L[i]
    rows.sort(key=lambda r: (r['conf'], r['bar']))
    return rows


# ── сборка ───────────────────────────────────────────────────────────────────
def build_engine(path, trig='auto'):
    """Собрать движок из CSV с колонками time, open, high, low, close.

    trig: 'auto'   — взять колонку «триггер», а если её нет, посчитать по
                     шаблонам формы (так работают выгрузки из TradingView);
          'column' — только колонка, иначе триггеров не будет (поведение v3);
          'shape'  — всегда считать по шаблонам.
    """
    df = pd.read_csv(path)
    df['time'] = pd.to_datetime(df['time'], utc=True, format='mixed')
    df['kyiv'] = df['time'].dt.tz_convert('Europe/Kyiv')
    O, H, L, C = df['open'].values, df['high'].values, df['low'].values, df['close'].values
    N = len(df)

    has_col = 'триггер' in df.columns
    if trig == 'column' or (trig == 'auto' and has_col):
        TRIG = (df['триггер'].values == 1) if has_col else np.zeros(N, bool)
        trig_src = 'колонка «триггер»' if has_col else 'нет (колонки не было)'
    else:
        TRIG = triggers_from_shape(O, H, L, C)
        trig_src = 'шаблоны формы (реконструкция из Pine)'

    csize = H - L
    # Перцентильный порог размера триггерной свечи, % от цены.
    # Считается по ВСЕЙ истории разом — это заглядывание вперёд, но так в v3.
    ti = np.where(TRIG)[0]
    sz = csize[ti] / C[ti] * 100 if len(ti) > 0 else np.array([1.0])
    size_thr_pct = np.percentile(sz, SIZE_PERCENTILE)

    fast = mk(2, 2, N, H, L)
    confs = [r['conf'] for r in fast]

    def stop_variants(i, is_long, entry, lastprice):
        """Четыре варианта стопа. decide_v4 берёт только «свеча»."""
        if is_long:
            lvl = np.floor(entry / GRID) * GRID
            while lvl >= L[i]:
                lvl -= GRID
            return {'свеча': L[i] * (1 - BUF), 'уровень': lvl * (1 - BUF),
                    'метка': lastprice * (1 - BUF), 'хвост': L[i] * (1 - BUF)}
        lvl = np.ceil(entry / GRID) * GRID
        while lvl <= H[i]:
            lvl += GRID
        return {'свеча': H[i] * (1 + BUF), 'уровень': lvl * (1 + BUF),
                'метка': lastprice * (1 + BUF), 'хвост': H[i] * (1 + BUF)}

    return dict(df=df, O=O, H=H, L=L, C=C, N=N, TRIG=TRIG, csize=csize,
                fast=fast, confs=confs, stop_variants=stop_variants,
                size_thr_pct=size_thr_pct, trig_src=trig_src)


# ── решение ──────────────────────────────────────────────────────────────────
def banned_tail(labels):
    """Имя запрета, если хвост последовательности меток запрещён, иначе None."""
    s = '>'.join(labels)
    for b in BANNED_TAILS:
        if s.endswith(b):
            return b
    return None


def decide(E, i, version=5):
    """Решение движка на триггерном баре i.

    version=4 — каскад v4; version=5 — он же плюс запреты по хвосту.
    Возвращает dict: decision ('ВХОД' или причина пропуска), dir, entry,
    stop, tp, RR, labels.
    """
    confs, fast = E['confs'], E['fast']
    csize, C, H, L = E['csize'], E['C'], E['H'], E['L']
    size_thr = E['size_thr_pct']

    k = bisect.bisect_right(confs, i)
    seq = fast[max(0, k - FRESH_MARKS):k]
    if not seq:
        return dict(decision='нет меток')
    labels = [r['label'] for r in seq]
    last = labels[-1]
    if last in ('HL', 'LL'):
        is_long = True
    elif last in ('LH', 'HH'):
        is_long = False
    else:
        return dict(decision='метка?')
    out = dict(dir='LONG' if is_long else 'SHORT', labels=labels)
    entry = C[i]
    lag = i - seq[-1]['conf']

    # 1) заморозка свежего экстремума (LL/HH, лаг 0-1)
    if last in ('LL', 'HH') and lag <= 1:
        out['decision'] = 'заморозка'
        return out
    # 2) большая свеча (перцентильный фильтр размера)
    if csize[i] / C[i] * 100 > size_thr:
        out['decision'] = 'бол.свеча'
        return out
    # 3) согласованность против тренда (v4: порог 3/5 только для шортов от HH)
    up = sum(1 for x in labels if x in ('HH', 'HL'))
    dn = sum(1 for x in labels if x in ('LH', 'LL'))
    had_slom = any((labels[j - 1] == 'HH' and labels[j] == 'LL') or
                   (labels[j - 1] == 'LL' and labels[j] == 'HL')
                   for j in range(1, len(labels)))
    if not had_slom:
        tmin = 3 if last == 'HH' else 4
        if up >= tmin and not is_long:
            out['decision'] = 'против тренда'
            return out
        if dn >= TREND_MIN and is_long:
            out['decision'] = 'против тренда'
            return out
    # 4) свежий слом (HH->LL / LL->HL на последних двух метках)
    if len(labels) >= 2 and ((labels[-2] == 'HH' and labels[-1] == 'LL') or
                             (labels[-2] == 'LL' and labels[-1] == 'HL')):
        out['decision'] = 'слом'
        return out
    # 5) стоп за триггерной свечой ±0.1%
    sl = L[i] * (1 - BUF) if is_long else H[i] * (1 + BUF)
    if (is_long and sl >= entry) or ((not is_long) and sl <= entry):
        out['decision'] = 'стоп?'
        return out
    risk = abs(entry - sl)
    # 6) магнит: первая метка нужной стороны с RR >= 3 (ближние с RR < 3 перепрыгиваются)
    side = 'high' if is_long else 'low'
    cand = [r for r in seq if r['side'] == side]
    tp = np.nan
    if is_long:
        for r in sorted([r for r in cand if r['price'] > entry], key=lambda r: r['price']):
            if (r['price'] - entry) / risk >= 3:
                tp = r['price']
                break
    else:
        for r in sorted([r for r in cand if r['price'] < entry], key=lambda r: -r['price']):
            if (entry - r['price']) / risk >= 3:
                tp = r['price']
                break
    if np.isnan(tp):
        out['decision'] = 'нет RR'
        return out
    out.update(decision='ВХОД', entry=entry, stop=sl, tp=tp, RR=abs(tp - entry) / risk)
    # 7) запреты по хвосту структуры (только v5)
    if version >= 5:
        b = banned_tail(labels)
        if b is not None:
            out['decision'] = 'запрет ' + b
    return out


def resolve(E, i, is_long, sl, tp):
    """Исход сделки: TP / SL / NONE.
    Одновременное касание SL и TP в одном баре = SL (консервативно)."""
    H, L, n = E['H'], E['L'], E['N']
    for j in range(i + 1, min(i + HORIZON, n)):
        hit_sl = (L[j] <= sl) if is_long else (H[j] >= sl)
        hit_tp = (H[j] >= tp) if is_long else (L[j] <= tp)
        if hit_sl and hit_tp:
            return 'SL'
        if hit_tp:
            return 'TP'
        if hit_sl:
            return 'SL'
    return 'NONE'


def run(E, version=5):
    """Полный прогон: DataFrame сделок (dt, i, dir, last, entry, stop, tp, RR, out, R).

    Сделка, не разрешившаяся за HORIZON баров, отбрасывается — так в v4/v5.
    Число одновременных позиций не ограничено.
    """
    df = E['df']
    rows = []
    for i in np.where(E['TRIG'])[0]:
        d = decide(E, i, version)
        if d.get('decision') != 'ВХОД':
            continue
        is_long = d['dir'] == 'LONG'
        o = resolve(E, i, is_long, d['stop'], d['tp'])
        if o not in ('TP', 'SL'):
            continue
        rows.append(dict(dt=df['time'].iloc[i], i=i, dir=d['dir'], last=d['labels'][-1],
                         entry=d['entry'], stop=d['stop'], tp=d['tp'],
                         RR=round(d['RR'], 2), out=o, R=d['RR'] if o == 'TP' else -1.0))
    return pd.DataFrame(rows)


def verdicts(E, version=5):
    """Вердикт на каждом триггерном баре — для сверки с индикатором."""
    return {int(i): decide(E, int(i), version).get('decision')
            for i in np.where(E['TRIG'])[0]}


if __name__ == '__main__':
    import sys
    E = build_engine(sys.argv[1] if len(sys.argv) > 1 else 'xau_1h_master.csv')
    print(f"баров {E['N']} | триггеры: {E['trig_src']} | их {int(E['TRIG'].sum())}")
    print(f"порог размера свечи ({SIZE_PERCENTILE}-й перцентиль): {E['size_thr_pct']:.3f}% от цены")
    for v in (4, 5):
        tr = run(E, v)
        if tr.empty:
            print(f"v{v}: сделок нет")
            continue
        print(f"v{v}: {len(tr)} сделок, {tr['R'].sum():+.1f}R, WR {(tr['out'] == 'TP').mean() * 100:.1f}%")
