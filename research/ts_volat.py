import csv
OKNO=20; POROG=2.0; SIMM=8.0
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

P=[]   # прошедшие правило: (абсолютный размер %, средняя по 20, отношение)
for i in range(OKNO,n):
    f=forma(*rows[i])
    if f is None: continue
    sred=sum(shk[i-OKNO:i])/OKNO
    if sred<=0: continue
    if abs(f[1]-f[2])>SIMM: continue
    k=shk[i]/sred
    if k>POROG: continue
    P.append((shk[i],sred,k))

print("ЕГО ЖАЛОБА, ПРОВЕРКА НА 1H. Прошло правило: %d\n" % len(P))

# режимы волатильности — по средней соседей, пять равных долей
S=sorted(x[1] for x in P)
gr=[S[int(len(S)*q)] for q in (0.2,0.4,0.6,0.8)]
NM=["самый спокойный","спокойный","обычный","неспокойный","САМЫЙ БУРНЫЙ"]
def rezh(s):
    for j,g in enumerate(gr):
        if s<g: return j
    return 4

kl=[[] for _ in range(5)]
for a,s,k in P: kl[rezh(s)].append((a,s,k))

print("%-18s %-12s %-14s %-14s %-14s %s" % ("режим рынка","свечей","обычная высота","ПРОПУЩЕННАЯ свеча: медиана","её максимум","отношение"))
for j in range(5):
    g=kl[j]
    A=sorted(x[0] for x in g); Sr=sorted(x[1] for x in g); K=sorted(x[2] for x in g)
    m=len(A)
    print("%-18s %-12d %-14s %-26s %-14s %s" % (
        NM[j], m,
        "%.3f%%" % Sr[m//2],
        "%.3f%%" % A[m//2],
        "%.3f%%" % A[-1],
        "%.2fx" % K[m//2]))

print()
print("ВОТ ОНА, ДЫРА: число свечей в каждом режиме ПОЧТИ ОДИНАКОВОЕ,")
print("а их настоящий размер отличается в разы. Фильтр подстраивается")
print("под рынок и перестаёт ловить то, ради чего он сделан.")
print()
A=sorted(x[0] for x in P)
m=len(A)
print("РАЗМЕР ПРОПУЩЕННЫХ СВЕЧЕЙ, все %d:" % m)
for q,nm in ((0.5,"медиана"),(0.75,"три четверти"),(0.9,"девять из десяти"),(0.95,"девятнадцать из двадцати"),(1.0,"максимум")):
    i=min(m-1,int(m*q))
    print("   %-26s %.3f%%" % (nm,A[i]))

print()
print("ЕСЛИ ДОБАВИТЬ ПОТОЛОК ПО ЦЕНЕ — сколько уйдёт и откуда:")
print("%-14s %-10s %-10s %s" % ("потолок","останется","уйдёт","из какого режима уходит больше всего"))
for cap in (0.20,0.25,0.30,0.35,0.40,0.50):
    ost=sum(1 for a,s,k in P if a<=cap)
    ush=m-ost
    po=[sum(1 for a,s,k in kl[j] if a>cap) for j in range(5)]
    hud=NM[po.index(max(po))] if max(po)>0 else "—"
    print("  %-12s %-10s %-10s %s" % ("%.2f%% цены"%cap, "%d (%.0f%%)"%(ost,100.0*ost/m), "%d"%ush, "%s (%d из %d)"%(hud,max(po),ush) if ush else "—"))
