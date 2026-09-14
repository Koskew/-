# -*- coding: utf-8 -*-
"""Проверка гипотез о сломе на 9 годах.

Гипотеза 1 — АСИММЕТРИЯ. Слом восходящего (вниз) подтверждается быстрее,
чем слом нисходящего (вверх): золото падает резко, растёт медленно.

Гипотеза 2 — УЗКАЯ ТЕЛО/ФИТИЛЬ. Снос именно уровня размеченного тренда
(последний HL для восходящего, последний LH для нисходящего), а не любых
вершин. Тело = закрытие за уровнем, фитиль = только тень.

Событие: ПЕРВОЕ касание уровня за жизнь тренда. По одному на тренд,
чтобы события не были зависимыми.

Исход — гонка без подгонки:
  СНОС   цена ушла за уровень ещё на 0.5 импульса
  ОТБОЙ  цена вернулась к последнему экстремуму тренда
что наступит раньше; ждём не дольше 300 баров.
"""
import sys, csv, math, collections
sys.path.insert(0, 'research')
from core import Core

FWD = 300
GO  = 0.5        # доля импульса, на которую цена должна уйти дальше

def load(p):
    out = []
    for r in csv.DictReader(open(p, encoding='utf-8-sig')):
        o, h, l, c = float(r['open']), float(r['high']), float(r['low']), float(r['close'])
        out.append((r['time'], min(max(o, l), h), h, l, min(max(c, l), h)))
    return out

def pivots_n(rows, N):
    hi = [r[2] for r in rows]; lo = [r[3] for r in rows]; at = {}
    for i in range(N, len(rows) - N):
        if all(hi[i-k] <= hi[i] for k in range(1, N+1)) and all(hi[i+k] < hi[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, hi[i], True))
        if all(lo[i-k] >= lo[i] for k in range(1, N+1)) and all(lo[i+k] > lo[i] for k in range(1, N+1)):
            at.setdefault(i + N, []).append((i, lo[i], False))
    return at

def race(rows, b, tr, lvl, imp, ext):
    """СНОС=1, ОТБОЙ=0, не решилось=None"""
    tgt = lvl - GO * imp if tr == 1 else lvl + GO * imp
    for j in range(b + 1, min(b + 1 + FWD, len(rows))):
        h, l = rows[j][2], rows[j][3]
        hitB = (l <= tgt) if tr == 1 else (h >= tgt)
        hitR = (h >= ext) if tr == 1 else (l <= ext)
        if hitB and hitR: return None          # оба в одном баре — не считаем
        if hitB: return 1
        if hitR: return 0
    return None

def wil(k, n):
    if n == 0: return 0.0, 0.0
    p = k / n
    return p, 2 * math.sqrt(p * (1 - p) / n)

rows = load('data/XAUUSD_1h_9y.csv')
half = len(rows) // 2
print(f'9 лет, {len(rows)} баров, {rows[0][0][:10]} — {rows[-1][0][:10]}')
print(f'исход: СНОС = цена ушла за уровень ещё на {GO} импульса, '
      f'ОТБОЙ = вернулась к экстремуму тренда, ждём {FWD} баров\n')

for N in (5, 3, 2):
    co = Core(rows, fib=0.33, jump=0.5); co.at = pivots_n(rows, N)
    ev = []
    trkey = None; seen = set()
    for b in range(len(rows)):
        co.step(b)
        if co.inTrans or co.tr == 0 or co.lvl is None or co.imp <= 0: continue
        key = (co.tr, co.trFrom, round(co.lvl, 4))
        h, l, c = rows[b][2], rows[b][3], rows[b][4]
        cross = (l < co.lvl) if co.tr == 1 else (h > co.lvl)
        if not cross or key in seen: continue
        seen.add(key)
        body = (c < co.lvl) if co.tr == 1 else (c > co.lvl)
        # последний экстремум тренда — колено нужной стороны
        ext = None
        for i in range(len(co.KP) - 1, -1, -1):
            if co.KH[i] == (co.tr == 1): ext = co.KP[i]; break
        if ext is None: continue
        r = race(rows, b, co.tr, co.lvl, co.imp, ext)
        if r is None: continue
        ev.append(dict(tr=co.tr, body=body, res=r, half=0 if b < half else 1,
                       depth=abs(c - co.lvl) / co.imp))

    print(f'══ слой {N}/{N} · событий {len(ev)}')
    def cell(name, S):
        if len(S) < 30:
            print(f'   {name:<34}{len(S):>5}  мало данных'); return None
        p, e = wil(sum(x['res'] for x in S), len(S))
        h1 = [x for x in S if x['half'] == 0]; h2 = [x for x in S if x['half'] == 1]
        p1 = sum(x['res'] for x in h1) / len(h1) if h1 else 0
        p2 = sum(x['res'] for x in h2) / len(h2) if h2 else 0
        print(f'   {name:<34}{len(S):>5}  снос {p:>4.0%} ± {e:.0%}   '
              f'половины {p1:>3.0%} / {p2:>3.0%}')
        return p, e
    base = cell('ВСЕ касания', ev)
    print()
    for tr, nm in ((1, 'восходящий тренд, снос ВНИЗ'), (-1, 'нисходящий тренд, снос ВВЕРХ')):
        S = [x for x in ev if x['tr'] == tr]
        cell(nm, S)
        cell('   из них ТЕЛО', [x for x in S if x['body']])
        cell('   из них ФИТИЛЬ', [x for x in S if not x['body']])
    print()

# ── контроль форы ──────────────────────────────────────────────────
# У ТЕЛА закрытие уже за уровнем, значит до цели 0.5 импульса ему
# осталось меньше. Проверяем, не в этом ли весь эффект: берём только те
# ТЕЛА, что ушли за уровень совсем чуть-чуть, и сравниваем с ФИТИЛЯМИ.
print('\n' + '='*78)
print('КОНТРОЛЬ ФОРЫ: сколько закрытие ушло за уровень, в долях импульса')
print('='*78)
for N in (5, 3, 2):
    co = Core(rows, fib=0.33, jump=0.5); co.at = pivots_n(rows, N)
    ev = []; seen = set()
    for b in range(len(rows)):
        co.step(b)
        if co.inTrans or co.tr == 0 or co.lvl is None or co.imp <= 0: continue
        key = (co.tr, co.trFrom, round(co.lvl, 4))
        h, l, c = rows[b][2], rows[b][3], rows[b][4]
        cross = (l < co.lvl) if co.tr == 1 else (h > co.lvl)
        if not cross or key in seen: continue
        seen.add(key)
        ext = None
        for i in range(len(co.KP) - 1, -1, -1):
            if co.KH[i] == (co.tr == 1): ext = co.KP[i]; break
        if ext is None: continue
        r = race(rows, b, co.tr, co.lvl, co.imp, ext)
        if r is None: continue
        # знак: + закрытие за уровнем (тело), − закрытие вернулось (фитиль)
        d = (co.lvl - c) / co.imp if co.tr == 1 else (c - co.lvl) / co.imp
        ev.append(dict(res=r, d=d))
    print(f'\n── слой {N}/{N}')
    B = [('ФИТИЛЬ глубже −0.10',      lambda d: d < -0.10),
         ('ФИТИЛЬ от −0.10 до 0',     lambda d: -0.10 <= d < 0),
         ('ТЕЛО от 0 до 0.05',        lambda d: 0 <= d < 0.05),
         ('ТЕЛО от 0.05 до 0.15',     lambda d: 0.05 <= d < 0.15),
         ('ТЕЛО от 0.15 до 0.33',     lambda d: 0.15 <= d < 0.33),
         ('ТЕЛО глубже 0.33',         lambda d: d >= 0.33)]
    for nm, t in B:
        S = [x for x in ev if t(x['d'])]
        if len(S) < 30:
            print(f'   {nm:<26}{len(S):>5}  мало данных'); continue
        p, e = wil(sum(x['res'] for x in S), len(S))
        print(f'   {nm:<26}{len(S):>5}  снос {p:>4.0%} ± {e:.0%}')
