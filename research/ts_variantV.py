# -*- coding: utf-8 -*-
"""ВАРИАНТ В — его мысль 05.11.2026: сравнивать свечу не со ВСЕМИ соседями,
а с теми, что САМИ были отнесены к триггерным.

ПАРАМЕТРЫ, которые пришлось выбрать мне — они спорные и названы:
  N  — сколько ПРЕДЫДУЩИХ триггерных свечей брать в среднее
  П  — во сколько раз больше этой средней уже «большая»
  чьё среднее: тех, кто прошёл ФОРМУ (симметрию), или тех, кто прошёл ВСЁ.
     Беру ФОРМУ: иначе фильтр кормит сам себя и в бурю разгоняется.
"""
import csv
OKNO=20; POROG=2.0; SIMM=8.0; DOLG=500
def load(p):
    out=[]
    with open(p,encoding='utf-8') as f:
        for r in csv.DictReader(f): out.append((float(r['open']),float(r['high']),float(r['low']),float(r['close'])))
    return out
def forma(o,h,l,c):
    rng=h-l
    if rng<=0: return None
    upp=(h-o) if o>c else (h-c); lo=(c-l) if o>c else (o-l)
    return abs(c-o)/rng*100, upp/rng*100, lo/rng*100

rows=load("data/XAUUSD_1h_2y.csv"); n=len(rows)
shk=[(h-l)/c*100.0 if c>0 else 0.0 for o,h,l,c in rows]

# один проход: собираем кандидатов и историю размеров ФОРМЕННЫХ свечей
ist=[]      # размеры свечей, прошедших ФОРМУ, по порядку
KAND=[]     # (i, абс.размер, средняя20, долгая500, средняя по N триггерам)
for i in range(max(OKNO,DOLG),n):
    f=forma(*rows[i])
    if f is None: continue
    s20=sum(shk[i-OKNO:i])/OKNO
    s500=sum(shk[i-DOLG:i])/DOLG
    if s20<=0 or s500<=0: continue
    if abs(f[1]-f[2])<=SIMM:
        sredN={}
        for N in (10,20,30,50):
            sredN[N]=sum(ist[-N:])/len(ist[-N:]) if len(ist)>=N else None
        if shk[i]/s20<=POROG:
            KAND.append((i,shk[i],s20,s500,dict(sredN)))
        ist.append(shk[i])

m=len(KAND)
S=sorted(x[2] for x in KAND); gr=[S[int(m*q)] for q in (0.2,0.4,0.6,0.8)]
def rezh(s):
    for j,g in enumerate(gr):
        if s<g: return j
    return 4
def med(a):
    a=sorted(a); return a[len(a)//2] if a else 0.0

def otchet(nm, ost):
    """ost — список оставшихся записей"""
    k=len(ost)
    po=[[x[1] for x in ost if rezh(x[2])==j] for j in range(5)]
    sp=med(po[0]); bu=med(po[4])
    raz = bu/sp if sp>0 else 0
    print("  %-34s осталось %-12s спокойный %.3f%%  бурный %.3f%%  РАЗРЫВ %.2fx" %
          (nm, "%d (%.0f%%)"%(k,100.0*k/m), sp, bu, raz))

print("1H. Кандидатов после формы и фильтра 2x по соседям: %d\n" % m)
print("ЧЕМ МЕНЬШЕ «РАЗРЫВ», ТЕМ ЛУЧШЕ ПОЧИНЕНА ДЫРА.")
print("Разрыв — во сколько раз пропущенная свеча в бурю больше, чем в штиль.\n")
otchet("СЕЙЧАС (ничего не добавлено)", KAND)
print()
print("ВАРИАНТ А · потолок в % от цены:")
for cap in (0.30,0.40,0.50):
    otchet("  не больше %.2f%% цены" % cap, [x for x in KAND if x[1]<=cap])
print()
print("ВАРИАНТ Б · долгая средняя, 500 баров:")
for mn in (1.2,1.5,2.0):
    otchet("  не больше %.1fx долгой средней" % mn, [x for x in KAND if x[1]<=mn*x[3]])
print()
print("ВАРИАНТ В · ЕГО МЫСЛЬ — средняя по предыдущим ТРИГГЕРНЫМ свечам:")
for N in (10,20,30,50):
    for mn in (1.2,1.5,2.0):
        ost=[x for x in KAND if x[4][N] is None or x[1]<=mn*x[4][N]]
        otchet("  N=%-2d триггеров, не больше %.1fx" % (N,mn), ost)
    print()
