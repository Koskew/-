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

for nm,p,DL in (("1H","data/XAUUSD_1h_2y.csv",500),("5m","data/XAUUSD_5m.csv",500)):
    rows=load(p); n=len(rows)
    shk=[(h-l)/c*100.0 if c>0 else 0.0 for o,h,l,c in rows]
    P=[]
    for i in range(max(OKNO,DL),n):
        f=forma(*rows[i])
        if f is None: continue
        sred=sum(shk[i-OKNO:i])/OKNO
        dolg=sum(shk[i-DL:i])/DL
        if sred<=0 or dolg<=0: continue
        if abs(f[1]-f[2])>SIMM: continue
        if shk[i]/sred>POROG: continue
        P.append((shk[i],sred,dolg))
    m=len(P)
    S=sorted(x[1] for x in P); gr=[S[int(m*q)] for q in (0.2,0.4,0.6,0.8)]
    def rezh(s):
        for j,g in enumerate(gr):
            if s<g: return j
        return 4
    NM=["спокойный 1","спокойный 2","обычный","бурный 1","САМЫЙ БУРНЫЙ"]

    print("="*70)
    print("%s · прошло правило сейчас: %d   (долгое окно %d баров)" % (nm,m,DL))
    print()
    print("ВАРИАНТ Б · потолок по ДОЛГОМУ окну: свеча не больше N× средней за %d баров" % DL)
    print("%-10s %-14s %-10s %s" % ("порог","останется","уйдёт","уходит из самого бурного"))
    for mn in (1.0,1.2,1.5,2.0,2.5):
        ost=sum(1 for a,s,d in P if a<=mn*d)
        po=[sum(1 for a,s,d in P if a>mn*d and rezh(s)==j) for j in range(5)]
        print("  %-8s %-14s %-10d %d из %d" % ("%.1fx"%mn,"%d (%.0f%%)"%(ost,100.0*ost/m),m-ost,po[4],m-ost))
    print()
    # что остаётся в самом бурном режиме при варианте Б
    print("  ЧТО ЭТО ДАЁТ ПО РЕЖИМАМ при пороге 1.5x долгой средней:")
    print("  %-16s %-10s %-12s %s" % ("режим","было","стало","срезано"))
    for j in range(5):
        g=[x for x in P if rezh(x[1])==j]
        ost=sum(1 for a,s,d in g if a<=1.5*d)
        print("  %-16s %-10d %-12d %d" % (NM[j],len(g),ost,len(g)-ost))
    print()
