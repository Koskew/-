#!/usr/bin/env python3
"""СПИСОК ВОСХОДЯЩИХ ТРЕНДОВ за девять лет, по каждому слою.

Восходящий = начинается с LL и КАЖДЫЙ СЛЕДУЮЩИЙ НИЗ ВЫШЕ ПРЕДЫДУЩЕГО.
Условие владельца, дословно: «но с условием что низы будут выше
предыдущего». Значит точки (2) и (4) обязаны быть HL. Вершины свободны:
(1), (3), (5) могут быть и HH, и LH.

Выход: research/out/trendy_5-5.csv, _3-3.csv, _2-2.csv — по одному файлу
на слой, отсортировано по дате. Чтобы открыть график на этой дате и
посмотреть глазами.
"""
import csv
PATH='data/XAUUSD_1h_9y.csv'
rows=list(csv.DictReader(open(PATH)))
T=[r['time'][:16] for r in rows]
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

# номера последовательностей — те же П, что в справочнике
SPR={r['последовательность']:r['№'] for r in csv.DictReader(open('research/out/spravochnik.csv'))}

FIELDS=['№','дата начала (0)','дата конца (5)','последовательность','№ посл.',
        'цена (0)','цена (1)','цена (2)','цена (3)','цена (4)','цена (5)',
        'ход в цене','ход % от нуля','баров','растут ли вершины',
        'что после (5)','перекрытие']

print('СПИСОК ВОСХОДЯЩИХ ТРЕНДОВ · XAUUSD 1H · 9 лет')
print('условие: старт LL, каждый следующий низ выше предыдущего\n')
for D,tag,fn in ((5,'5/5','5-5'),(3,'3/3','3-3'),(2,'2/2','2-2')):
    P,B,Hi,Lb=knees(D); n=len(P)
    out=[]; prevEnd=-1; num=0
    for z in range(n-6):
        if Hi[z] or Lb[z]!='LL': continue
        seq=[Lb[z+k] for k in range(1,6)]
        if seq[1]!='HL' or seq[3]!='HL':        # низы ОБЯЗАНЫ расти
            continue
        prs=[P[z+k] for k in range(1,6)]
        brs=[B[z+k] for k in range(1,6)]
        zp,zb=P[z],B[z]; end=brs[4]
        num+=1
        out.append({'№':num,'дата начала (0)':T[zb],'дата конца (5)':T[end],
            'последовательность':'·'.join(seq),'№ посл.':SPR.get('·'.join(seq),''),
            'цена (0)':round(zp,2),
            **{f'цена ({k+1})':round(prs[k],2) for k in range(5)},
            'ход в цене':round(max(prs[0],prs[2],prs[4])-zp,2),
            'ход % от нуля':round(100*(max(prs[0],prs[2],prs[4])-zp)/zp,2),
            'баров':end-zb,
            'растут ли вершины':'да' if prs[0]<prs[2]<prs[4] else 'нет',
            'что после (5)':Lb[z+6],
            'перекрытие':'да' if zb<=prevEnd else 'нет'})
        prevEnd=end
    with open(f'research/out/trendy_{fn}.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader()
        for r in out: w.writerow(r)
    ov=sum(1 for r in out if r['перекрытие']=='да')
    import statistics
    hod=[r['ход % от нуля'] for r in out]
    bars=[r['баров'] for r in out]
    print(f'── {tag} ──  восходящих трендов: {len(out)}   из них перекрываются: {ov}')
    print(f'   ход медиана {statistics.median(hod):.2f}% · длина медиана {statistics.median(bars):.0f} баров')
    print(f'   первый {out[0]["дата начала (0)"]}   последний {out[-1]["дата начала (0)"]}')
    from collections import Counter
    c=Counter(r['последовательность'] for r in out)
    print('   какие последовательности и сколько:')
    for s,k in c.most_common():
        print(f'     {SPR.get(s,"—"):>4}  {s:22} {k:5}  {100*k/len(out):5.1f}%')
    ca=Counter(r['что после (5)'] for r in out)
    print('   что приходило после (5):  ' + '  '.join(f'{k} {v} ({100*v/len(out):.0f}%)' for k,v in ca.most_common()))
    print(f'   файл: research/out/trendy_{fn}.csv\n')
