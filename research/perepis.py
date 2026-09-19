#!/usr/bin/env python3
"""ПЕРЕПИСЬ последовательностей после LL. Никаких правил тренда.

Идея владельца 19.09.2026: не выдумывать правило рождения, а достать его
из истории. От КАЖДОГО колена-низа с подписью LL берём следующие пять
колен и записываем, что там реально было. Ничего не обрываем и ничего не
фильтруем — это перепись, а не движок.

Главный вопрос, на который отвечает замер: обрывает ли LL внутри
последовательности восходящую структуру, или это «манипуляция», после
которой счёт идёт дальше. §2 ВОСХОДЯЩИЙ.md говорит одно, владелец
19.09 сказал обратное. Делим по подписи низа на (2) и сравниваем.
"""
import csv, sys, statistics
from collections import Counter

PATH = 'data/XAUUSD_1h_9y.csv'
rows = list(csv.DictReader(open(PATH)))
O=[float(r['open']) for r in rows]; H=[float(r['high']) for r in rows]
L=[float(r['low']) for r in rows];  C=[float(r['close']) for r in rows]
N=len(O)

def knees(D):
    def piv(i,hi):
        c=i-D
        if c-D<0 or c+D>=N: return None
        src=H if hi else L; v=src[c]
        for k in range(c-D,c+D+1):
            if k==c: continue
            if (src[k]>=v) if hi else (src[k]<=v): return None
        return v
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
    for i in range(N):
        for hi in (True,False):
            if piv(i,hi) is not None:
                pr=(H if hi else L)[i-D]; b=i-D
                same = bool(P) and Hi[-1]==hi
                if same:
                    if (pr>P[-1]) if hi else (pr<P[-1]): P[-1]=pr; B[-1]=b
                else:
                    P.append(pr); B.append(b); Hi.append(hi)
                relabel()
    return P,B,Hi,Lb

def perepis(D, tag):
    P,B,Hi,Lb = knees(D)
    n=len(P)
    recs=[]
    for z in range(n-5):
        if Hi[z] or Lb[z]!='LL':      # старт только с колена-низа LL
            continue
        seq  = [Lb[z+k] for k in range(1,6)]
        prs  = [P[z+k]  for k in range(1,6)]
        brs  = [B[z+k]  for k in range(1,6)]
        zp, zb = P[z], B[z]
        imp = prs[0]-zp if prs[0]>zp else 0.0
        top = max(prs[0], prs[2], prs[4])
        hod = (top-zp)/imp if imp>0 else float('nan')
        # уходила ли цена ниже нуля за окно
        lo = min(L[zb:brs[4]+1]) if brs[4]>zb else zp
        below = lo < zp
        recs.append(dict(seq='·'.join(seq), s=seq, zp=zp, zb=zb,
                         low2=seq[1], low4=seq[3],
                         hiAll=all(seq[k] in ('HH',) for k in (0,2,4)),
                         loAll=all(seq[k]=='HL' for k in (1,3)),
                         nCounter=sum(1 for x in seq if x in ('LH','LL')),
                         hod=hod, hodAbs=top-zp, imp=imp, bars=brs[4]-zb, below=below,
                         depth=(zp-lo)/imp if imp>0 else float('nan')))
    print(f'\n{"="*66}\nСЛОЙ {tag}   колен всего {n}   стартов с LL: {len(recs)}')
    cnt=Counter(r['seq'] for r in recs)
    tot=len(recs)
    print(f'\n  все последовательности, топ-12 из {len(cnt)} встретившихся:')
    acc=0
    for s,c in cnt.most_common(12):
        acc+=c
        print(f'    {s:26} {c:5}  {100*c/tot:5.1f}%   накоплено {100*acc/tot:5.1f}%')
    # ── ГЛАВНОЕ: обрывает ли LL на (2) ──
    gHL=[r for r in recs if r['low2']=='HL']
    gLL=[r for r in recs if r['low2']=='LL']
    print(f'\n  ── низ на (2): HL против LL ──')
    for nm,g in (('(2) = HL  «чисто»', gHL), ('(2) = LL  «манипуляция»', gLL)):
        if not g: continue
        hod=[r['hod'] for r in g if r['hod']==r['hod']]
        bel=[r for r in g if r['below']]
        print(f'    {nm:26} n={len(g):5} ({100*len(g)/tot:4.1f}%)  '
              f'ход медиана {statistics.median(hod):5.2f} имп  ·  '
              f'цена уходила ниже нуля {100*len(bel)/len(g):5.1f}%  ·  '
              f'баров медиана {statistics.median([r["bars"] for r in g]):4.0f}  ·  имп {statistics.median([r["imp"] for r in g if r["imp"]>0]):6.1f}  ·  ход в цене {statistics.median([r["hodAbs"] for r in g]):6.1f}')
    # то же для (4)
    g4HL=[r for r in recs if r['low4']=='HL']
    g4LL=[r for r in recs if r['low4']=='LL']
    print(f'  ── низ на (4): HL против LL ──')
    for nm,g in (('(4) = HL', g4HL), ('(4) = LL', g4LL)):
        if not g: continue
        hod=[r['hod'] for r in g if r['hod']==r['hod']]
        bel=[r for r in g if r['below']]
        print(f'    {nm:26} n={len(g):5} ({100*len(g)/tot:4.1f}%)  '
              f'ход медиана {statistics.median(hod):5.2f} имп  ·  '
              f'цена уходила ниже нуля {100*len(bel)/len(g):5.1f}%  ·  '
              f'баров медиана {statistics.median([r["bars"] for r in g]):4.0f}')
    # восемь «чистых по низам» последовательностей
    clean=[r for r in recs if r['loAll']]
    print(f'\n  ── оба низа HL (то, что переживает правило «LL обрывает») ──')
    print(f'    таких {len(clean)} из {tot}  ({100*len(clean)/tot:.1f}%)')
    cc=Counter(r['seq'] for r in clean)
    for s,c in cc.most_common():
        g=[r for r in clean if r['seq']==s]
        hod=[r['hod'] for r in g if r['hod']==r['hod']]
        bel=[r for r in g if r['below']]
        ia=[r['imp'] for r in g if r['imp']>0]
        ha=[r['hodAbs'] for r in g]
        print(f'    {s:26} {c:5}  {100*c/len(clean):5.1f}%   ход {statistics.median(hod):5.2f} имп  ·  первый импульс {statistics.median(ia):7.1f}  ·  ход в цене {statistics.median(ha):7.1f}')
    return recs

for D,tag in ((5,'5/5'),(3,'3/3'),(2,'2/2')):
    perepis(D,tag)
