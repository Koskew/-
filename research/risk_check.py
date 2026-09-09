# -*- coding: utf-8 -*-
"""Блок РИСК: что реально даёт движок по дням, неделям и месяцам.

Заодно проверка расхождений между тем, как считает таблица в Pine, и тем,
как считает эталонный движок.
"""
import sys, statistics as st
sys.path.insert(0, 'research')
import engine, pandas as pd

E = engine.build_engine('data/XAUUSD_1h_2y.csv', trig='auto')
t = engine.run(E, version=5)
t['dt'] = pd.to_datetime(t['dt'], utc=True)
print(f'сделок {len(t)},  {t.dt.min().date()} — {t.dt.max().date()},  сумма {t.R.sum():+.1f}R')
print(f'из них TP {(t.out=="TP").sum()} = {(t.out=="TP").mean():.0%},  SL {(t.out=="SL").sum()}')
print(f'медиана RR у выигрышей {t.loc[t.out=="TP","RR"].median():.2f}')

for freq, nm in (('D','ДЕНЬ'), ('W-MON','НЕДЕЛЯ'), ('MS','МЕСЯЦ')):
    g = t.set_index('dt').R.resample(freq).agg(['sum','count'])
    g = g[g['count'] > 0]
    s = g['sum']
    print(f'\n═══ {nm} ═══  периодов со сделками: {len(g)}')
    print(f'  сделок за период:  медиана {g["count"].median():.0f}   максимум {g["count"].max()}')
    print(f'  R за период:       медиана {s.median():+.1f}   среднее {s.mean():+.1f}')
    print(f'  лучший {s.max():+.1f}R   худший {s.min():+.1f}R')
    print(f'  в плюсе {(s>0).mean():.0%}   в нуле {(s==0).mean():.0%}   в минусе {(s<0).mean():.0%}')
    q = s.quantile([0.05, 0.25, 0.75, 0.95])
    print(f'  5% худших ниже {q[0.05]:+.1f}R   |   5% лучших выше {q[0.95]:+.1f}R')

# серия стопов подряд
streak = mx = 0
runs = []
for x in t.R:
    if x < 0:
        streak += 1; mx = max(mx, streak)
    else:
        if streak: runs.append(streak)
        streak = 0
if streak: runs.append(streak)
print(f'\n═══ СЕРИИ СТОПОВ ═══')
print(f'  серий {len(runs)},  медиана {st.median(runs):.0f},  '
      f'90-й перцентиль {sorted(runs)[int(len(runs)*0.9)]},  максимум {mx}')

# просадка по накопленному R
cum = t.R.cumsum()
dd = (cum.cummax() - cum)
print(f'\n═══ ПРОСАДКА ═══')
print(f'  максимальная {dd.max():.1f}R,  текущая {dd.iloc[-1]:.1f}R')

# расхождение: таблица считает неделю по времени ЗАКРЫТИЯ, движок — по входу
print(f'\n═══ РАСХОЖДЕНИЕ ВХОД / ЗАКРЫТИЕ ═══')
print('  Таблица в Pine относит сделку к неделе по бару ЗАКРЫТИЯ,')
print('  движок и этот отчёт — по бару ВХОДА. Сделки, живущие через')
print('  границу недели, попадут в разные недели.')
