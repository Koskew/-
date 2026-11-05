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

for nm,p in (("1H","data/XAUUSD_1h_2y.csv"),("5m","data/XAUUSD_5m.csv")):
    rows=load(p); n=len(rows)
    shk=[(h-l)/c*100.0 if c>0 else 0.0 for o,h,l,c in rows]
    pro=0; med=0; byk=0; dodzh=0
    for i in range(OKNO,n):
        f=forma(*rows[i])
        if f is None: continue
        sred=sum(shk[i-OKNO:i])/OKNO
        if sred<=0: continue
        if abs(f[1]-f[2])>SIMM: continue
        if shk[i]/sred>POROG: continue
        pro+=1
        o,h,l,c=rows[i]
        if c<o: med+=1
        elif c>o: byk+=1
        else: dodzh+=1
    print("%s: правило ловит %d" % (nm,pro))
    print("    ТЁМНЫХ (закрытие НИЖЕ открытия): %d = %.1f%%" % (med,100.0*med/pro))
    print("    светлых (закрытие ВЫШЕ открытия): %d = %.1f%%" % (byk,100.0*byk/pro))
    print("    ровно (закрытие = открытию):      %d = %.1f%%" % (dodzh,100.0*dodzh/pro))
    print()
