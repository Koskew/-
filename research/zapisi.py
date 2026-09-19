#!/usr/bin/env python3
"""ПОЛНАЯ ТАБЛИЦА ЗАПИСЕЙ переписи — все пятнадцать полей, как обещано.

Одна строка = один старт с колена-низа LL. Никаких правил тренда, ничего
не фильтруется: записи, которым не хватило пяти колен до конца данных,
тоже попадают в таблицу с пометкой.

Выход: research/out/zapisi.csv
"""
import csv
PATH='data/XAUUSD_1h_9y.csv'
rows=list(csv.DictReader(open(PATH)))
T=[r['time'] for r in rows]
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

FIELDS=(['слой','бар нуля','дата нуля','цена нуля','последовательность']
        + [f'цена ({k})' for k in range(1,6)]
        + [f'бар ({k})'  for k in range(1,6)]
        + ['все низы выше','все вершины выше','чистая','встречных',
           'ход в цене','ход в импульсах','ход % от нуля','первый импульс',
           'баров','ниже нуля','глубина ниже нуля %',
           'хватило данных','перекрытие'])

out=[]
for D,tag in ((5,'5/5'),(3,'3/3'),(2,'2/2')):
    P,B,Hi,Lb=knees(D); n=len(P)
    prevEnd=-1
    for z in range(n):
        if Hi[z] or Lb[z]!='LL': continue
        have = min(5, n-1-z)                    # сколько колен реально есть
        ks   = list(range(z+1, z+1+have))
        seq  = [Lb[k] for k in ks]
        prs  = [P[k]  for k in ks]
        brs  = [B[k]  for k in ks]
        zp,zb = P[z],B[z]
        full = have == 5
        r={'слой':tag,'бар нуля':zb,'дата нуля':T[zb][:16],'цена нуля':round(zp,3),
           'последовательность':'·'.join(seq)}
        for k in range(5):
            r[f'цена ({k+1})']=round(prs[k],3) if k<have else ''
            r[f'бар ({k+1})'] =brs[k]          if k<have else ''
        lows =[seq[k] for k in (1,3) if k<have]
        highs=[seq[k] for k in (0,2,4) if k<have]
        r['все низы выше']   ='да' if lows  and all(x=='HL' for x in lows)  else 'нет'
        r['все вершины выше']='да' if highs and all(x=='HH' for x in highs) else 'нет'
        r['чистая']='да' if '·'.join(seq)=='HH·HL·HH·HL·HH' else 'нет'
        r['встречных']=sum(1 for x in seq if x in ('LH','LL'))
        top=max([prs[k] for k in (0,2,4) if k<have], default=zp)
        imp=prs[0]-zp if have>=1 and prs[0]>zp else 0.0
        end=brs[-1] if brs else zb
        lo=min(L[zb:end+1]) if end>zb else zp
        r['ход в цене']=round(top-zp,3)
        r['ход в импульсах']=round((top-zp)/imp,3) if imp>0 else ''
        r['ход % от нуля']=round(100*(top-zp)/zp,4)
        r['первый импульс']=round(imp,3)
        r['баров']=end-zb
        r['ниже нуля']='да' if lo<zp else 'нет'
        r['глубина ниже нуля %']=round(100*(zp-lo)/zp,4) if lo<zp else 0.0
        r['хватило данных']='да' if full else 'нет'
        r['перекрытие']='да' if zb<=prevEnd else 'нет'
        prevEnd=end
        out.append(r)

with open('research/out/zapisi.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader()
    for r in out: w.writerow(r)

from collections import Counter
print(f'записей всего: {len(out)}')
for D,tag in ((5,'5/5'),(3,'3/3'),(2,'2/2')):
    g=[r for r in out if r['слой']==tag]
    ov=sum(1 for r in g if r['перекрытие']=='да')
    nf=sum(1 for r in g if r['хватило данных']=='нет')
    print(f'  {tag}: {len(g):5}  перекрытий {ov:5} ({100*ov/len(g):4.1f}%)  '
          f'неполных {nf}')
print('\nresearch/out/zapisi.csv')
