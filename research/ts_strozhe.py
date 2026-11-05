import csv
OKNO=20
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
F=[]
for i in range(OKNO,n):
    f=forma(*rows[i])
    if f is None: continue
    sred=sum(shk[i-OKNO:i])/OKNO
    if sred<=0: continue
    F.append((abs(f[1]-f[2]), shk[i]/sred))
N=len(F)
print("1H, свечей в счёте %d. Сейчас: симметрия 8, размер 2.0x\n" % N)

def schet(s,p):
    k=sum(1 for razn,otn in F if razn<=s and otn<=p)
    return k

baz=schet(8.0,2.0)
print("СЕЙЧАС:                       %4d  %5.1f%% баров   примерно 1 свеча из %.0f" % (baz,100.0*baz/N,N/baz))
print()
print("--- ЖМЁМ ТОЛЬКО СИММЕТРИЮ (размер остаётся 2.0x) ---")
for s in (6,5,4,3,2):
    k=schet(float(s),2.0)
    print("  фитили до %d п.п.            %4d  %5.1f%% баров   1 из %-4.0f   осталось %.0f%% от нынешних" % (s,k,100.0*k/N,N/max(1,k),100.0*k/baz))
print()
print("--- ЖМЁМ ТОЛЬКО РАЗМЕР (симметрия остаётся 8) ---")
for p in (1.5,1.2,1.0,0.8):
    k=schet(8.0,p)
    print("  не больше %.1fx средней      %4d  %5.1f%% баров   1 из %-4.0f   осталось %.0f%% от нынешних" % (p,k,100.0*k/N,N/max(1,k),100.0*k/baz))
print()
print("--- ЖМЁМ ОБА ---")
for s,p in ((5,1.5),(5,1.2),(4,1.5),(4,1.2),(3,1.0)):
    k=schet(float(s),p)
    print("  фитили %d + размер %.1fx       %4d  %5.1f%% баров   1 из %-4.0f   осталось %.0f%% от нынешних" % (s,p,k,100.0*k/N,N/max(1,k),100.0*k/baz))
