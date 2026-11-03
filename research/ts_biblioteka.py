import csv, math, sys

tb=[12.6,14.7,17.0,32.0,20.2,4.1,23.0,27.9,30.7,35.2,24.5,41.9,26.0,25.9,11.6,23.3,49.3,14.0,18.3,25.4,27.9,45.7,29.2,40.6,41.9,10.4,41.5,23.6,32.2,18.8,35.5,32.2,54.2,10.8,47.3,16.0,21.6,19.8,9.9,27.5]
tu=[33.7,37.3,37.7,27.8,29.4,40.4,35.7,35.3,41.0,35.7,28.4,22.0,39.6,37.4,46.0,31.5,21.5,27.5,47.3,35.6,26.2,24.8,36.3,36.7,26.8,35.6,20.7,34.5,36.4,46.2,38.6,33.6,21.6,44.1,22.9,45.2,42.8,45.2,41.5,30.7]
tl=[53.7,48.0,45.3,40.2,50.4,55.5,41.3,36.8,28.3,29.1,47.1,36.0,34.5,36.7,42.5,45.2,29.2,58.5,34.4,39.0,46.0,29.5,34.5,22.6,31.3,54.0,37.9,41.9,31.4,34.9,25.8,34.2,24.2,45.1,29.8,38.8,35.5,35.0,48.6,41.8]
TOL=4.0

print("=== 1 · СУММА ТРЁХ ДОЛЕЙ У КАЖДОГО ШАБЛОНА ===")
bad=[]
for i in range(40):
    s=tb[i]+tu[i]+tl[i]
    if abs(s-100)>0.15: bad.append((i+1,round(s,1)))
print("шаблонов:",40,"  не дают 100:",bad if bad else "нет, все сошлись")

print()
print("=== 2 · РАЗБРОС САМИХ ШАБЛОНОВ ===")
for nm,a in (("тело",tb),("верхняя тень",tu),("нижняя тень",tl)):
    print("  %-14s от %5.1f до %5.1f   среднее %5.1f" % (nm,min(a),max(a),sum(a)/40))

print()
print("=== 3 · ПЕРЕКРЫТИЯ: сколько шаблонов стоят друг от друга ближе 2*TOL ===")
par=0; pary=[]
for i in range(40):
    for j in range(i+1,40):
        d=max(abs(tb[i]-tb[j]),abs(tu[i]-tu[j]),abs(tl[i]-tl[j]))
        if d<=TOL: par+=1; pary.append((i+1,j+1,round(d,1)))
print("  пар, чьи окна ПОЛНОСТЬЮ накрывают центр соседа (расст <= 4):",par)
for p in pary[:12]: print("     шаблоны",p[0],"и",p[1],"— расстояние",p[2])

print()
print("=== 4 · ДОЛЯ ТРЕУГОЛЬНИКА ФОРМ, КОТОРУЮ НАКРЫВАЮТ 40 ОКОН ===")
# сетка по симплексу tело+верх+низ=100, шаг 0.5
step=0.5; vsego=0; nakr=0
b=0.0
while b<=100.0001:
    u=0.0
    while u<=100.0001-b:
        l=100.0-b-u
        vsego+=1
        hit=False
        for i in range(40):
            if abs(b-tb[i])<=TOL and abs(u-tu[i])<=TOL and abs(l-tl[i])<=TOL:
                hit=True; break
        if hit: nakr+=1
        u+=step
    b+=step
print("  точек сетки в треугольнике: %d, накрыто: %d = %.1f%% площади" % (vsego,nakr,100.0*nakr/vsego))
import csv
tb=[12.6,14.7,17.0,32.0,20.2,4.1,23.0,27.9,30.7,35.2,24.5,41.9,26.0,25.9,11.6,23.3,49.3,14.0,18.3,25.4,27.9,45.7,29.2,40.6,41.9,10.4,41.5,23.6,32.2,18.8,35.5,32.2,54.2,10.8,47.3,16.0,21.6,19.8,9.9,27.5]
tu=[33.7,37.3,37.7,27.8,29.4,40.4,35.7,35.3,41.0,35.7,28.4,22.0,39.6,37.4,46.0,31.5,21.5,27.5,47.3,35.6,26.2,24.8,36.3,36.7,26.8,35.6,20.7,34.5,36.4,46.2,38.6,33.6,21.6,44.1,22.9,45.2,42.8,45.2,41.5,30.7]
tl=[53.7,48.0,45.3,40.2,50.4,55.5,41.3,36.8,28.3,29.1,47.1,36.0,34.5,36.7,42.5,45.2,29.2,58.5,34.4,39.0,46.0,29.5,34.5,22.6,31.3,54.0,37.9,41.9,31.4,34.9,25.8,34.2,24.2,45.1,29.8,38.8,35.5,35.0,48.6,41.8]
TOL=4.0

def load(p):
    rows=[]
    with open(p,encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append((float(r['open']),float(r['high']),float(r['low']),float(r['close'])))
    return rows

def forma(o,h,l,c):
    rng=h-l
    if rng<=0: return None
    bod=abs(c-o)
    upp=(h-o) if o>c else (h-c)
    lo =(c-l) if o>c else (o-l)
    return bod/rng*100, upp/rng*100, lo/rng*100

def match(b,u,l):
    for i in range(40):
        if abs(b-tb[i])<=TOL and abs(u-tu[i])<=TOL and abs(l-tl[i])<=TOL: return i
    return -1

itog={}
for nm,p in (("1H, 2 года","data/XAUUSD_1h_2y.csv"),("5m, 3.5 мес","data/XAUUSD_5m.csv")):
    rows=load(p)
    n=0; hit=0; po=[0]*40; nol=0
    telo=[]; teni=[]
    for o,h,l,c in rows:
        f=forma(o,h,l,c)
        if f is None: nol+=1; continue
        n+=1
        b,u,lo=f
        telo.append(b); teni.append(min(u,lo))
        i=match(b,u,lo)
        if i>=0: hit+=1; po[i]+=1
    itog[nm]=(n,hit,po,nol,telo,teni)
    print("### %s — баров с диапазоном %d (нулевых %d)" % (nm,n,nol))
    print("    СОВПАЛО: %d = %.1f%%" % (hit,100.0*hit/n))
    mert=[i+1 for i in range(40) if po[i]==0]
    print("    мёртвых шаблонов (ноль попаданий): %d %s" % (len(mert),mert if mert else ""))
    top=sorted(range(40),key=lambda i:-po[i])[:5]
    print("    самые частые: "+", ".join("№%d=%d" % (i+1,po[i]) for i in top))
    print("    самые редкие (из живых): "+", ".join("№%d=%d" % (i+1,po[i]) for i in sorted([i for i in range(40) if po[i]>0],key=lambda i:po[i])[:5]))
    print()

print("=== ЧТО БИБЛИОТЕКА ОТСЕКАЕТ ПО ПОСТРОЕНИЮ ===")
print("  тело шаблонов: %.1f … %.1f  →  с допуском проходит тело %.1f … %.1f" % (min(tb),max(tb),min(tb)-TOL,max(tb)+TOL))
print("  верх. тень:    %.1f … %.1f  →  проходит %.1f … %.1f" % (min(tu),max(tu),min(tu)-TOL,max(tu)+TOL))
print("  нижн. тень:    %.1f … %.1f  →  проходит %.1f … %.1f" % (min(tl),max(tl),min(tl)-TOL,max(tl)+TOL))
print()
for nm in itog:
    n,hit,po,nol,telo,teni=itog[nm]
    v1=sum(1 for x in telo if x>max(tb)+TOL)
    v2=sum(1 for x in teni if x<min(min(tu),min(tl))-TOL)
    print("  %s: тело больше %.1f%% — %d баров (%.1f%%); МЕНЬШАЯ тень меньше %.1f%% — %d баров (%.1f%%)"
          % (nm,max(tb)+TOL,v1,100.0*v1/n,min(min(tu),min(tl))-TOL,v2,100.0*v2/n))
import csv
tb=[12.6,14.7,17.0,32.0,20.2,4.1,23.0,27.9,30.7,35.2,24.5,41.9,26.0,25.9,11.6,23.3,49.3,14.0,18.3,25.4,27.9,45.7,29.2,40.6,41.9,10.4,41.5,23.6,32.2,18.8,35.5,32.2,54.2,10.8,47.3,16.0,21.6,19.8,9.9,27.5]
tu=[33.7,37.3,37.7,27.8,29.4,40.4,35.7,35.3,41.0,35.7,28.4,22.0,39.6,37.4,46.0,31.5,21.5,27.5,47.3,35.6,26.2,24.8,36.3,36.7,26.8,35.6,20.7,34.5,36.4,46.2,38.6,33.6,21.6,44.1,22.9,45.2,42.8,45.2,41.5,30.7]
tl=[53.7,48.0,45.3,40.2,50.4,55.5,41.3,36.8,28.3,29.1,47.1,36.0,34.5,36.7,42.5,45.2,29.2,58.5,34.4,39.0,46.0,29.5,34.5,22.6,31.3,54.0,37.9,41.9,31.4,34.9,25.8,34.2,24.2,45.1,29.8,38.8,35.5,35.0,48.6,41.8]
TOL=4.0
def load(p):
    rows=[]
    with open(p,encoding='utf-8') as f:
        for r in csv.DictReader(f): rows.append((float(r['open']),float(r['high']),float(r['low']),float(r['close'])))
    return rows
def forma(o,h,l,c):
    rng=h-l
    if rng<=0: return None
    upp=(h-o) if o>c else (h-c); lo=(c-l) if o>c else (o-l)
    return abs(c-o)/rng*100, upp/rng*100, lo/rng*100
def lib(b,u,l):
    for i in range(40):
        if abs(b-tb[i])<=TOL and abs(u-tu[i])<=TOL and abs(l-tl[i])<=TOL: return True
    return False

for nm,p in (("1H","data/XAUUSD_1h_2y.csv"),("5m","data/XAUUSD_5m.csv")):
    rows=load(p); F=[]
    for o,h,l,c in rows:
        f=forma(o,h,l,c)
        if f: F.append(f)
    n=len(F)
    L=[lib(*f) for f in F]
    nL=sum(L)
    print("=== %s · баров %d · библиотека ловит %d (%.1f%%) ===" % (nm,n,nL,100.0*nL/n))

    # фраза-кандидат: тело небольшое И обе тени заметные
    best=None
    for tmax in (50,55,58,60,65):
        for smin in (14,16,17,18,20):
            S=[(f[0]<=tmax and min(f[1],f[2])>=smin) for f in F]
            vmeste=sum(1 for i in range(n) if S[i] and L[i])
            tochn = 100.0*vmeste/max(1,sum(S))     # из пойманных фразой — сколько в библиотеке
            polnot= 100.0*vmeste/max(1,nL)         # из библиотеки — сколько поймала фраза
            if best is None or polnot+tochn>best[0]:
                best=(polnot+tochn,tmax,smin,sum(S),tochn,polnot)
    _,tmax,smin,nS,tochn,polnot=best
    print("    ЛУЧШАЯ ОДНА ФРАЗА: тело <= %d%% И обе тени >= %d%%" % (tmax,smin))
    print("      ловит %d баров (%.1f%%) против %d у библиотеки" % (nS,100.0*nS/n,nL))
    print("      из библиотеки покрывает %.1f%%, из своих попаданий в библиотеке %.1f%%" % (polnot,tochn))

    # сколько шаблонов несут основную нагрузку
    po=[0]*40
    for f in F:
        for i in range(40):
            if abs(f[0]-tb[i])<=TOL and abs(f[1]-tu[i])<=TOL and abs(f[2]-tl[i])<=TOL:
                po[i]+=1; break
    por=sorted(range(40),key=lambda i:-po[i]); nak=0; k=0
    for i in por:
        nak+=po[i]; k+=1
        if nak>=0.9*sum(po): break
    print("    90%% попаданий дают %d шаблона из 40; шаблонов с <=3 попаданиями: %d" % (k,sum(1 for x in po if x<=3)))
    print()
import csv
tb=[12.6,14.7,17.0,32.0,20.2,4.1,23.0,27.9,30.7,35.2,24.5,41.9,26.0,25.9,11.6,23.3,49.3,14.0,18.3,25.4,27.9,45.7,29.2,40.6,41.9,10.4,41.5,23.6,32.2,18.8,35.5,32.2,54.2,10.8,47.3,16.0,21.6,19.8,9.9,27.5]
tu=[33.7,37.3,37.7,27.8,29.4,40.4,35.7,35.3,41.0,35.7,28.4,22.0,39.6,37.4,46.0,31.5,21.5,27.5,47.3,35.6,26.2,24.8,36.3,36.7,26.8,35.6,20.7,34.5,36.4,46.2,38.6,33.6,21.6,44.1,22.9,45.2,42.8,45.2,41.5,30.7]
tl=[53.7,48.0,45.3,40.2,50.4,55.5,41.3,36.8,28.3,29.1,47.1,36.0,34.5,36.7,42.5,45.2,29.2,58.5,34.4,39.0,46.0,29.5,34.5,22.6,31.3,54.0,37.9,41.9,31.4,34.9,25.8,34.2,24.2,45.1,29.8,38.8,35.5,35.0,48.6,41.8]
def load(p):
    rows=[]
    with open(p,encoding='utf-8') as f:
        for r in csv.DictReader(f): rows.append((float(r['open']),float(r['high']),float(r['low']),float(r['close'])))
    return rows
def forma(o,h,l,c):
    rng=h-l
    if rng<=0: return None
    upp=(h-o) if o>c else (h-c); lo=(c-l) if o>c else (o-l)
    return abs(c-o)/rng*100, upp/rng*100, lo/rng*100

rows=load("data/XAUUSD_1h_2y.csv")
F=[f for f in (forma(*r) for r in rows) if f]
n=len(F)
print("=== ЧУВСТВИТЕЛЬНОСТЬ К ДОПУСКУ, 1H, %d баров ===" % n)
print("  ручка допуска в настройках ходит от 1 до 15")
pred=None
for T in (1,2,3,4,5,6,8,10,15):
    c=0
    for b,u,l in F:
        for i in range(40):
            if abs(b-tb[i])<=T and abs(u-tu[i])<=T and abs(l-tl[i])<=T: c+=1; break
    izm = "" if pred is None else "   (x%.2f к предыдущему)" % (c/pred if pred else 0)
    print("    допуск ±%-2d  →  %5d срабатываний  %5.1f%% баров%s" % (T,c,100.0*c/n,izm))
    pred=c

fraza=sum(1 for b,u,l in F if b<=58 and min(u,l)>=18)
print()
print("  ОДНА ФРАЗА «тело <= 58%% и обе тени >= 18%%»  →  %d  %.1f%% баров" % (fraza,100.0*fraza/n))
print("  то есть библиотека догоняет фразу где-то между допуском 5 и 6")
import csv
tb=[12.6,14.7,17.0,32.0,20.2,4.1,23.0,27.9,30.7,35.2,24.5,41.9,26.0,25.9,11.6,23.3,49.3,14.0,18.3,25.4,27.9,45.7,29.2,40.6,41.9,10.4,41.5,23.6,32.2,18.8,35.5,32.2,54.2,10.8,47.3,16.0,21.6,19.8,9.9,27.5]
tu=[33.7,37.3,37.7,27.8,29.4,40.4,35.7,35.3,41.0,35.7,28.4,22.0,39.6,37.4,46.0,31.5,21.5,27.5,47.3,35.6,26.2,24.8,36.3,36.7,26.8,35.6,20.7,34.5,36.4,46.2,38.6,33.6,21.6,44.1,22.9,45.2,42.8,45.2,41.5,30.7]
tl=[53.7,48.0,45.3,40.2,50.4,55.5,41.3,36.8,28.3,29.1,47.1,36.0,34.5,36.7,42.5,45.2,29.2,58.5,34.4,39.0,46.0,29.5,34.5,22.6,31.3,54.0,37.9,41.9,31.4,34.9,25.8,34.2,24.2,45.1,29.8,38.8,35.5,35.0,48.6,41.8]

print("=== ЕГО СЛОВО: «длина фитилей ОДИНАКОВЫЕ» ===")
print("    смотрю разницу |верхняя тень - нижняя тень| у 40 его шаблонов\n")
raz=sorted(abs(tu[i]-tl[i]) for i in range(40))
print("    самая симметричная: %.1f п.п.   самая кривая: %.1f п.п." % (raz[0],raz[-1]))
print("    медиана: %.1f п.п.   среднее: %.1f п.п." % (raz[20],sum(raz)/40))
for por in (5,10,15,20):
    k=sum(1 for x in raz if x<=por)
    print("      разница не больше %2d п.п.: %2d шаблонов из 40 (%.0f%%)" % (por,k,100.0*k/40))
print()
print("    КТО СИММЕТРИЧНЕЕ ВСЕХ (тело / верх / низ / разница):")
por=sorted(range(40),key=lambda i:abs(tu[i]-tl[i]))
for i in por[:8]:
    print("      №%-2d  тело %5.1f  верх %5.1f  низ %5.1f   разница %4.1f" % (i+1,tb[i],tu[i],tl[i],abs(tu[i]-tl[i])))
print("    КТО КРИВЕЕ ВСЕХ:")
for i in por[-5:]:
    print("      №%-2d  тело %5.1f  верх %5.1f  низ %5.1f   разница %4.1f" % (i+1,tb[i],tu[i],tl[i],abs(tu[i]-tl[i])))

def load(p):
    rows=[]
    with open(p,encoding='utf-8') as f:
        for r in csv.DictReader(f): rows.append((float(r['open']),float(r['high']),float(r['low']),float(r['close'])))
    return rows
def forma(o,h,l,c):
    rng=h-l
    if rng<=0: return None
    upp=(h-o) if o>c else (h-c); lo=(c-l) if o>c else (o-l)
    return abs(c-o)/rng*100, upp/rng*100, lo/rng*100

print()
print("=== А ТЕПЕРЬ СРАВНЕНИЕ С ОБЫЧНЫМИ СВЕЧАМИ ===")
for nm,p in (("1H","data/XAUUSD_1h_2y.csv"),("5m","data/XAUUSD_5m.csv")):
    F=[f for f in (forma(*r) for r in load(p)) if f]
    n=len(F)
    vse=sorted(abs(f[1]-f[2]) for f in F)
    print("  %s, %d баров: медиана разницы теней %.1f п.п." % (nm,n,vse[n//2]))
    for por in (5,10,15,20):
        k=sum(1 for x in vse if x<=por)
        print("      разница не больше %2d п.п.: %5d баров (%.1f%%)" % (por,k,100.0*k/n))
import csv
tb=[12.6,14.7,17.0,32.0,20.2,4.1,23.0,27.9,30.7,35.2,24.5,41.9,26.0,25.9,11.6,23.3,49.3,14.0,18.3,25.4,27.9,45.7,29.2,40.6,41.9,10.4,41.5,23.6,32.2,18.8,35.5,32.2,54.2,10.8,47.3,16.0,21.6,19.8,9.9,27.5]
tu=[33.7,37.3,37.7,27.8,29.4,40.4,35.7,35.3,41.0,35.7,28.4,22.0,39.6,37.4,46.0,31.5,21.5,27.5,47.3,35.6,26.2,24.8,36.3,36.7,26.8,35.6,20.7,34.5,36.4,46.2,38.6,33.6,21.6,44.1,22.9,45.2,42.8,45.2,41.5,30.7]
tl=[53.7,48.0,45.3,40.2,50.4,55.5,41.3,36.8,28.3,29.1,47.1,36.0,34.5,36.7,42.5,45.2,29.2,58.5,34.4,39.0,46.0,29.5,34.5,22.6,31.3,54.0,37.9,41.9,31.4,34.9,25.8,34.2,24.2,45.1,29.8,38.8,35.5,35.0,48.6,41.8]
TOL=4.0
def load(p):
    rows=[]
    with open(p,encoding='utf-8') as f:
        for r in csv.DictReader(f): rows.append((float(r['open']),float(r['high']),float(r['low']),float(r['close'])))
    return rows
def forma(o,h,l,c):
    rng=h-l
    if rng<=0: return None
    upp=(h-o) if o>c else (h-c); lo=(c-l) if o>c else (o-l)
    return abs(c-o)/rng*100, upp/rng*100, lo/rng*100
def lib(f):
    b,u,l=f
    for i in range(40):
        if abs(b-tb[i])<=TOL and abs(u-tu[i])<=TOL and abs(l-tl[i])<=TOL: return True
    return False

print("=== ЧТО БИБЛИОТЕКА ДЕЛАЕТ С «МАЛЕНЬКИМИ ФИТИЛЯМИ» ===")
print("  границы библиотеки: верхняя тень не меньше 16.7%, нижняя не меньше 18.6%")
print("  значит свеча с ДВУМЯ короткими фитилями в неё не попадает НИКОГДА\n")

for nm,p in (("1H","data/XAUUSD_1h_2y.csv"),("5m","data/XAUUSD_5m.csv")):
    F=[f for f in (forma(*r) for r in load(p)) if f]
    n=len(F); L=[lib(f) for f in F]; nL=sum(L)
    print("--- %s, %d баров, библиотека ловит %d ---" % (nm,n,nL))

    # симметрия одна
    for por in (5,8,10):
        S=[abs(f[1]-f[2])<=por for f in F]
        vm=sum(1 for i in range(n) if S[i] and L[i])
        print("  симметрия одна, разница теней <= %2d п.п.: %5d баров (%4.1f%%) | из библиотеки покрывает %4.1f%%"
              % (por,sum(S),100.0*sum(S)/n,100.0*vm/nL))

    # симметричные, но С КОРОТКИМИ фитилями — их библиотека теряет
    sim=[i for i in range(n) if abs(F[i][1]-F[i][2])<=8]
    kor=[i for i in sim if max(F[i][1],F[i][2])<16.7]
    kor_v_lib=sum(1 for i in kor if L[i])
    print("  из них с ОБОИМИ фитилями короче 16.7%%: %d баров — в библиотеке %d" % (len(kor),kor_v_lib))

    # тело у симметричных: правда ли «любое»
    tela=sorted(F[i][0] for i in sim)
    m=len(tela)
    print("  тело у симметричных: от %.1f до %.1f, четверти %.1f / %.1f / %.1f"
          % (tela[0],tela[-1],tela[m//4],tela[m//2],tela[3*m//4]))
    print()
