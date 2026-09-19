#!/usr/bin/env python3
"""СПРАВОЧНИК последовательностей после LL. Номер на каждую, как у
шаблонов триггерной свечи.

Никакого выбора «это тренд, а это нет». Каждая встретившаяся
последовательность получает НОМЕР и свою статистику. Решать, что с ней
делать, можно потом — номер уже есть.

Номер привязан к СТРОКЕ и одинаков на всех трёх слоях: «П7» значит одно
и то же на 5/5, 3/3 и 2/2. Порядок — по суммарной частоте.

Ход считается в ПРОЦЕНТАХ от цены нуля, а не в долларах и не в долях
импульса. Доллары несравнимы за девять лет (золото 1200 -> 4500), доли
импульса врут: у слабого старта импульс меньше и отношение раздувается.
"""
import csv, statistics
from collections import Counter, defaultdict

PATH='data/XAUUSD_1h_9y.csv'
rows=list(csv.DictReader(open(PATH)))
O=[float(r['open']) for r in rows]; H=[float(r['high']) for r in rows]
L=[float(r['low']) for r in rows];  C=[float(r['close']) for r in rows]
N=len(O)

def knees(D):
    P=[];B=[];Hi=[];Lb=[]
    def relabel():
        Lb.clear()
        for i in range(len(P)):
            prev=None; j=i-1
            while j>=0:
                if Hi[j]==Hi[i]: prev=P[j]; break
                j-=1
            Lb.append('?' if prev is None else
                      ('HH' if P[i]>prev else 'LH') if Hi[i] else
                      ('HL' if P[i]>prev else 'LL'))
    def piv(i,hi):
        c=i-D
        if c-D<0 or c+D>=N: return None
        src=H if hi else L; v=src[c]
        for k in range(c-D,c+D+1):
            if k==c: continue
            if (src[k]>=v) if hi else (src[k]<=v): return None
        return v
    for i in range(N):
        for hi in (True,False):
            if piv(i,hi) is not None:
                pr=(H if hi else L)[i-D]; b=i-D
                if P and Hi[-1]==hi:
                    if (pr>P[-1]) if hi else (pr<P[-1]): P[-1]=pr; B[-1]=b
                else:
                    P.append(pr); B.append(b); Hi.append(hi)
                relabel()
    return P,B,Hi,Lb

LAYERS=((5,'5/5'),(3,'3/3'),(2,'2/2'))
recs=defaultdict(list)     # (seq, tag) -> список записей
for D,tag in LAYERS:
    P,B,Hi,Lb = knees(D)
    for z in range(len(P)-6):
        if Hi[z] or Lb[z]!='LL': continue
        seq=[Lb[z+k] for k in range(1,6)]
        prs=[P[z+k] for k in range(1,6)]
        brs=[B[z+k] for k in range(1,6)]
        zp,zb=P[z],B[z]
        top=max(prs[0],prs[2],prs[4])
        lo=min(L[zb:brs[4]+1])
        nxt=P[z+6]                              # колено ПОСЛЕ (5)
        recs['·'.join(seq)+'|'+tag].append(dict(
            hod=100*(top-zp)/zp,                # ход вверх, % от нуля
            imp=100*(prs[0]-zp)/zp,             # первый импульс, %
            prov=100*(zp-lo)/zp,                # глубина ухода ниже нуля, %
            bars=brs[4]-zb,
            after=nxt>prs[4] if not Hi[z+6] else nxt>prs[4],  # следующее колено выше (5)
            up50=100*(max(H[brs[4]:min(brs[4]+50,N)])-C[brs[4]])/zp if brs[4]+1<N else 0.0,
            dn50=100*(C[brs[4]]-min(L[brs[4]:min(brs[4]+50,N)]))/zp if brs[4]+1<N else 0.0))

seqs=sorted({k.split('|')[0] for k in recs},
            key=lambda s:-sum(len(recs.get(s+'|'+t,[])) for _,t in LAYERS))
tot={t:sum(len(v) for k,v in recs.items() if k.endswith('|'+t)) for _,t in LAYERS}

print(f'СПРАВОЧНИК ПОСЛЕДОВАТЕЛЬНОСТЕЙ · XAUUSD 1H · 9 лет · {N} баров')
print(f'стартов с LL:  5/5 {tot["5/5"]}   3/3 {tot["3/3"]}   2/2 {tot["2/2"]}')
print(f'встретилось последовательностей: {len(seqs)} из 1024 возможных\n')
hdr=f'{"№":>4} {"последовательность":22} {"вст":>4} {"низы":>4} | ' + ' | '.join(f'{t:^22}' for _,t in LAYERS)
print(hdr)
print(f'{"":>4} {"":22} {"":>4} {"":>4} | ' + ' | '.join(f'{"n":>5} {"доля":>5} {"ход%":>5} {"пров%":>4}' for _ in LAYERS))
print('-'*len(hdr))
out=[]
for i,s in enumerate(seqs,1):
    lab=s.split('·')
    nC=sum(1 for x in lab if x in ('LH','LL'))
    loAll='HL' if all(lab[k]=='HL' for k in (1,3)) else ('LL' if all(lab[k]=='LL' for k in (1,3)) else 'мкс')
    line=f'П{i:<3} {s:22} {nC:>4} {loAll:>4} |'
    row={'№':f'П{i}','последовательность':s,'встречных':nC,'низы':loAll}
    for _,t in LAYERS:
        g=recs.get(s+'|'+t,[])
        if g:
            h=statistics.median([r['hod'] for r in g])
            p=statistics.median([r['prov'] for r in g])
            line+=f' {len(g):>5} {100*len(g)/tot[t]:>4.1f}% {h:>5.2f} {p:>4.2f} |'
            row[t+' n']=len(g); row[t+' доля%']=round(100*len(g)/tot[t],2)
            row[t+' ход%']=round(h,3); row[t+' провал%']=round(p,3)
            row[t+' после+%']=round(statistics.median([r['up50'] for r in g]),3)
            row[t+' после-%']=round(statistics.median([r['dn50'] for r in g]),3)
        else:
            line+=f' {"—":>5} {"—":>5} {"—":>5} {"—":>4} |'
    print(line)
    out.append(row)

with open('research/out/spravochnik.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0].keys()))
    w.writeheader()
    for r in out: w.writerow(r)
print('\nполная таблица: research/out/spravochnik.csv')
