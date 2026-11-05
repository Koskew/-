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
P=[]
for i in range(OKNO,n):
    f=forma(*rows[i])
    if f is None: continue
    sred=sum(shk[i-OKNO:i])/OKNO
    if sred<=0: continue
    if abs(f[1]-f[2])>SIMM: continue
    k=shk[i]/sred
    if k>POROG: continue
    P.append((f[0],f[1],f[2],k))
print("прошло правило: %d\n" % len(P))

def telo_gr(b):
    if b<30: return 0
    if b<60: return 1
    return 2
def razm_gr(k):
    if k<0.8: return 0
    if k<=1.2: return 1
    return 2
TN=["тело МАЛЕНЬКОЕ <30%","тело СРЕДНЕЕ 30-60%","тело БОЛЬШОЕ >=60%"]
RN=["МЕЛЬЧЕ обычной <0.8x","как обычная 0.8-1.2x","КРУПНЕЕ обычной >1.2x"]

kl={}
for b,u,l,k in P:
    kl.setdefault((telo_gr(b),razm_gr(k)),[]).append((b,u,l,k))

print("%-24s %-22s %-22s %-22s %s" % ("","МЕЛЬЧЕ <0.8x","как обычная","КРУПНЕЕ >1.2x","ВСЕГО"))
for t in range(3):
    stroka="%-24s" % TN[t]
    vsego=0
    for r in range(3):
        c=len(kl.get((t,r),[]))
        vsego+=c
        stroka+=" %-22s" % ("%d  (%.1f%%)" % (c,100.0*c/len(P)))
    stroka+=" %d (%.0f%%)" % (vsego,100.0*vsego/len(P))
    print(stroka)
stroka="%-24s" % "ВСЕГО"
for r in range(3):
    c=sum(len(kl.get((t,r),[])) for t in range(3))
    stroka+=" %-22s" % ("%d (%.0f%%)" % (c,100.0*c/len(P)))
print(stroka)

print()
print("ПРЕДСТАВИТЕЛЬ КАЖДОЙ ГРУППЫ — медиана по телу внутри группы:")
import statistics
OUT=[]
nom=0
for t in range(3):
    for r in range(3):
        g=kl.get((t,r),[])
        if not g: continue
        g2=sorted(g,key=lambda x:x[0])
        b,u,l,k=g2[len(g2)//2]
        nom+=1
        OUT.append((nom,TN[t],RN[r],len(g),b,u,l,k))
        print("  %d · %-24s %-22s n=%-5d  тело %5.1f  верх %5.1f  низ %5.1f  размер %.2fx"
              % (nom,TN[t],RN[r],len(g),b,u,l,k))
import json
json.dump(OUT,open('/tmp/claude-0/-home-user--/62594223-2ada-5a8a-adb8-b4ea549e588d/scratchpad/gruppy.json','w'))
