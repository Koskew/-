#!/usr/bin/env python3
"""Третье правило рождения (ВОСХОДЯЩИЙ.md §1): слом -> LH -> LL -> HH.

Только ЧАСТОТА, исходов не считает. Владелец не выбрал между строгим и
мягким прочтением, поэтому считаются все, и ни одно не выбрано за него.

  действующее  ноль = ближайший LL перед HH, про прошлое не спрашиваем
  A  строгий:  ПЕРВАЯ вершина после слома = LH, ПЕРВЫЙ низ после неё = LL
  B  мягкий:   где-то после слома была LH, и она РАНЬШЕ действующего нуля
  C  с уточнениями владельца 17.09.2026:
       * первая вершина после слома = LH, а низ после неё может быть и
         LL, и HL — «LH, потом HL, потом HH ... скорее да»;
       * вершины после слома нет вовсе — рождение годится, «только если
         под сломом есть LL», то есть низ подписан LL И стоит НИЖЕ цены
         слома.
     У C два подварианта нуля, потому что случай с HL спорит с §1
     («ноль это LL, HL только как продолжение после (5)»):
       C1  нулём становится сам этот HL
       C2  нулём остаётся LL, найденный дальше назад; нет такого — отказ
"""
import csv, sys
from collections import Counter

FIB=0.33; D=5

def load(path):
    rows=list(csv.DictReader(open(path)))
    return ([float(r['open']) for r in rows], [float(r['high']) for r in rows],
            [float(r['low']) for r in rows], [float(r['close']) for r in rows])

def run(path):
    O,H,L,C = load(path); N=len(O)
    def piv(i,hi):
        c=i-D
        if c-D<0 or c+D>=N: return None
        src=H if hi else L
        v=src[c]
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
    def push(price,bar,hi):
        same = bool(P) and Hi[-1]==hi
        if same:
            if (price>P[-1]) if hi else (price<P[-1]):
                P[-1]=price; B[-1]=bar
        else:
            P.append(price); B.append(bar); Hi.append(hi)
        relabel(); return not same

    tr=0; lvl=None; cnt=-1; imp=0.0; dBar=None; dPrice=None
    births=[]
    for i in range(N):
        nw=False
        for hi in (True,False):
            if piv(i,hi) is not None:
                nw = push((H if hi else L)[i-D], i-D, hi) or nw
        if tr==1 and lvl is not None and min(O[i],C[i]) < lvl - imp*FIB:
            dBar, dPrice = i, lvl
            tr=0; cnt=-1; lvl=None
        fr = piv(i,True) is not None or piv(i,False) is not None
        n=len(P)
        if fr and n>=2:
            lb,hi5,pr,pp = Lb[-1],Hi[-1],P[-1],P[-2]
            if pr>pp: imp=pr-pp
            if tr==1:
                if nw and cnt>=5 and (not hi5) and lb=='HL': cnt=0; lvl=pr
                else:
                    if nw and cnt<5: cnt+=1
                    if (not hi5) and lb=='HL': lvl=pr
            elif hi5 and lb=='HH':
                j=n-2
                while j>=0 and Hi[j]: j-=1
                if j>=0 and Lb[j]=='LL':
                    tr=1; cnt=1; lvl=P[j]
                    if dBar is not None:
                        births.append((n-1, j, dBar, dPrice))
    return P,B,Hi,Lb,births

def analyse(path, title):
    P,B,Hi,Lb,births = run(path)
    tot=len(births)
    okA=okB=okC=0; dA=dC1=0; c2_fail=0; why=Counter(); shape=Counter()
    for hh,z,dB,dP in births:
        s=[k for k in range(hh) if B[k] > dB]
        hs=[k for k in s if Hi[k]]
        # A
        aZero=None
        if hs and Lb[hs[0]]=='LH':
            ls=[k for k in s if (not Hi[k]) and k>hs[0]]
            if ls and Lb[ls[0]]=='LL': okA+=1; aZero=ls[0]
        if aZero is not None and aZero!=z: dA+=1
        # B
        if any(Hi[k] and Lb[k]=='LH' and k<z for k in s): okB+=1
        # C
        cZero=None
        if not hs:
            shape['после слома вершины нет'] += 1
            if Lb[z]=='LL' and P[z] < dP: okC+=1; cZero=z
            else: why['вершины нет, и низ не LL под сломом'] += 1
        elif Lb[hs[0]]=='LH':
            ls=[k for k in s if (not Hi[k]) and k>hs[0]]
            if ls:
                shape['LH, потом ' + Lb[ls[0]]] += 1
                okC+=1; cZero=ls[0]
                if Lb[ls[0]]=='HL':
                    back=[k for k in range(ls[0],-1,-1) if (not Hi[k]) and Lb[k]=='LL' and B[k]>dB]
                    if not back: c2_fail+=1
            else:
                shape['LH, но низа после неё нет'] += 1
                why['после LH нет низа до HH'] += 1
        else:
            shape['первая вершина после слома — ' + Lb[hs[0]]] += 1
            why['первая вершина после слома — ' + Lb[hs[0]]] += 1
        if cZero is not None and cZero!=z: dC1+=1
    print(f'\n╔══ {title} ══╗   рождений по действующему правилу: {tot}')
    for nm,ok in (('A  строгий', okA), ('B  мягкий', okB), ('C  с уточнениями', okC)):
        print(f'  {nm:18} проходит {ok:4} из {tot} ({100*ok/tot:5.1f}%)   запрещает {tot-ok:4}')
    print(f'  ноль отличается от действующего:  A {dA},  C1 {dC1}')
    print(f'  C2 невозможен (нет LL назад после слома): {c2_fail}')
    print('  как выглядит участок после слома:')
    for r,c in shape.most_common(): print(f'    {c:4}  {r}')
    print('  почему C отказывает:')
    for r,c in why.most_common(): print(f'    {c:4}  {r}')

analyse('data/XAUUSD_1h_2y.csv', 'XAUUSD 1H, 2 года, 12 189 баров')
analyse('data/XAUUSD_1h_9y.csv', 'XAUUSD 1H, 9 лет, 52 519 баров')
