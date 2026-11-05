# -*- coding: utf-8 -*-
"""
ТРИГГЕРНАЯ СВЕЧА · замер согласованного правила. 03.11.2026.

Параметры согласованы владельцем словом «давай так»:
  окно соседей      20 предыдущих свечей
  порог «большая»   размер больше чем ВДВОЕ средней по окну  -> пропускаем
  симметрия         |верхняя тень - нижняя тень| <= 8 п.п.

Правило из двух условий, его слово 03.11.2026:
  ФОРМА  — симметричная, фитили одинаковые, тело ЛЮБОЕ, фитили могут быть короткими
  РАЗМЕР — не большая относительно цены и соседних свечей

Размер свечи считается как (high-low)/close*100, то есть в % от цены —
ровно как в его примере «средняя шкала 0.3%, а свеча 0.8%».
"""
import csv, sys

OKNO=20; POROG=2.0; SIMM=8.0
# ПОТОЛОК ПО ЦЕНЕ — третье условие, З65, внесён в пайн v0.3 05.11.2026.
# CAP=None в точности воспроизводит прежний прогон, то есть Н60.
CAP = 0.40 if '--cap' in sys.argv else None

# старая библиотека — только для сравнения, ничего из неё не берём
tb=[12.6,14.7,17.0,32.0,20.2,4.1,23.0,27.9,30.7,35.2,24.5,41.9,26.0,25.9,11.6,23.3,49.3,14.0,18.3,25.4,27.9,45.7,29.2,40.6,41.9,10.4,41.5,23.6,32.2,18.8,35.5,32.2,54.2,10.8,47.3,16.0,21.6,19.8,9.9,27.5]
tu=[33.7,37.3,37.7,27.8,29.4,40.4,35.7,35.3,41.0,35.7,28.4,22.0,39.6,37.4,46.0,31.5,21.5,27.5,47.3,35.6,26.2,24.8,36.3,36.7,26.8,35.6,20.7,34.5,36.4,46.2,38.6,33.6,21.6,44.1,22.9,45.2,42.8,45.2,41.5,30.7]
tl=[53.7,48.0,45.3,40.2,50.4,55.5,41.3,36.8,28.3,29.1,47.1,36.0,34.5,36.7,42.5,45.2,29.2,58.5,34.4,39.0,46.0,29.5,34.5,22.6,31.3,54.0,37.9,41.9,31.4,34.9,25.8,34.2,24.2,45.1,29.8,38.8,35.5,35.0,48.6,41.8]

def load(p):
    out=[]
    with open(p,encoding='utf-8') as f:
        for r in csv.DictReader(f):
            out.append((float(r['open']),float(r['high']),float(r['low']),float(r['close'])))
    return out

def forma(o,h,l,c):
    rng=h-l
    if rng<=0: return None
    upp=(h-o) if o>c else (h-c); lo=(c-l) if o>c else (o-l)
    return abs(c-o)/rng*100, upp/rng*100, lo/rng*100

def lib(f):
    b,u,l=f
    for i in range(40):
        if abs(b-tb[i])<=4.0 and abs(u-tu[i])<=4.0 and abs(l-tl[i])<=4.0: return True
    return False

for nm,p in (("1H, два года","data/XAUUSD_1h_2y.csv"),("5m, 3.5 месяца","data/XAUUSD_5m.csv")):
    rows=load(p); n=len(rows)
    shkala=[(h-l)/c*100.0 if c>0 else 0.0 for o,h,l,c in rows]

    schit=0; f_ok=0; oba=0; rezal=0; v_lib=0; lib_vsego=0
    tela=[]; otn=[]
    po_porogu={1.5:0,2.0:0,2.5:0,3.0:0}
    for i in range(n):
        if i<OKNO: continue
        f=forma(*rows[i])
        if f is None: continue
        schit+=1
        sred=sum(shkala[i-OKNO:i])/OKNO
        if sred<=0: continue
        k=shkala[i]/sred
        b,u,l=f
        simm = abs(u-l)<=SIMM
        if lib(f): lib_vsego+=1
        if simm:
            f_ok+=1
            otn.append(k)
            for por in po_porogu:
                if k<=por: po_porogu[por]+=1
            cap_ok = True if CAP is None else (shkala[i] <= CAP)
            if k<=POROG and cap_ok:
                oba+=1; tela.append(b)
                if lib(f): v_lib+=1
            else:
                rezal+=1

    print("="*66)
    print("%s — свечей в счёте %d (первые %d окна не имеют)" % (nm,schit,OKNO))
    print()
    print("  1 · ФОРМА, симметрия <= %.0f п.п.      %6d  %5.1f%% баров" % (SIMM,f_ok,100.0*f_ok/schit))
    print("  2 · и РАЗМЕР не больше %.0fx средней   %6d  %5.1f%% баров   <== ПРАВИЛО%s" % (POROG,oba,100.0*oba/schit,"" if CAP is None else "  (+ потолок %.2f%%)"%CAP))
    print("      фильтр размера отсёк               %6d  = %.1f%% формы" % (rezal,100.0*rezal/f_ok))
    print()
    print("  для сравнения: старая библиотека       %6d  %5.1f%% баров" % (lib_vsego,100.0*lib_vsego/schit))
    print("      из нашего правила лежит в ней      %6d  = %.1f%%" % (v_lib,100.0*v_lib/max(1,oba)))
    print()
    print("  цена выбора порога (из %d симметричных):" % f_ok)
    for por in (1.5,2.0,2.5,3.0):
        pom = "  <== согласовано" if por==POROG else ""
        print("      порог %.1fx  ->  %6d  %5.1f%% баров%s" % (por,po_porogu[por],100.0*po_porogu[por]/schit,pom))
    print()
    t=sorted(tela); m=len(t)
    print("  ТЕЛО у того, что прошло (его слово «любое»):")
    print("      от %.1f%% до %.1f%%, четверти %.1f / %.1f / %.1f" % (t[0],t[-1],t[m//4],t[m//2],t[3*m//4]))
    mal=sum(1 for x in t if x<30); sred_=sum(1 for x in t if 30<=x<60); bol=sum(1 for x in t if x>=60)
    print("      маленькое (<30%%) %d = %.0f%%   среднее (30-60%%) %d = %.0f%%   большое (>=60%%) %d = %.0f%%"
          % (mal,100.0*mal/m,sred_,100.0*sred_/m,bol,100.0*bol/m))
    o=sorted(otn); q=len(o)
    print("  отношение к средней у симметричных: медиана %.2fx, четверти %.2f / %.2f / %.2f, максимум %.1fx"
          % (o[q//2],o[q//4],o[q//2],o[3*q//4],o[-1]))
    print()
