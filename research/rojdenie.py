#!/usr/bin/env python3
"""Третье правило рождения (ВОСХОДЯЩИЙ.md §1): слом -> LH -> LL -> HH.

Только ЧАСТОТА расхождений с действующим правилом. Исходов не считает.

Владелец не уточнил, первые ли это LH и LL после слома или любые,
поэтому считаются ОБА прочтения, и ни одно не выбрано за него:

  действующее  ноль = ближайший LL перед HH, про прошлое не спрашиваем
  вариант A    строгий: ПЕРВАЯ вершина после слома должна быть LH,
               ПЕРВЫЙ низ после неё должен быть LL, он и есть ноль
  вариант B    мягкий: где-то после слома была LH, и она стоит РАНЬШЕ
               того LL, который действующее правило взяло нулём

Колено считается «после слома», если его БАР позже бара слома. Колено
подтверждается на 5 баров позже своего бара, поэтому есть и второе
прочтение — по бару подтверждения; оно тоже посчитано, строкой ниже.
"""
import csv, sys
PATH = sys.argv[1] if len(sys.argv) > 1 else 'data/XAUUSD_1h_2y.csv'
rows = list(csv.DictReader(open(PATH)))
O=[float(r['open']) for r in rows]; H=[float(r['high']) for r in rows]
L=[float(r['low'])  for r in rows]; C=[float(r['close']) for r in rows]
N=len(rows); FIB=0.33; D=5

def piv(i, hi):
    c=i-D
    if c-D<0 or c+D>=N: return None
    src=H if hi else L
    v=src[c]
    for k in range(c-D, c+D+1):
        if k==c: continue
        if (src[k]>=v) if hi else (src[k]<=v): return None
    return v

P=[];B=[];Hi=[];Lb=[];Cf=[]          # Cf — бар ПОДТВЕРЖДЕНИЯ колена
def relabel():
    global Lb
    Lb=[]
    for i in range(len(P)):
        prev=None; j=i-1
        while j>=0:
            if Hi[j]==Hi[i]: prev=P[j]; break
            j-=1
        if prev is None: Lb.append('?')
        elif Hi[i]:      Lb.append('HH' if P[i]>prev else 'LH')
        else:            Lb.append('HL' if P[i]>prev else 'LL')
def push(price,bar,hi,conf):
    same = bool(P) and Hi[-1]==hi
    if same:
        better = price>P[-1] if hi else price<P[-1]
        if better: P[-1]=price; B[-1]=bar; Cf[-1]=conf
    else:
        P.append(price); B.append(bar); Hi.append(hi); Cf.append(conf)
    relabel()
    return not same

tr=0; lvl=None; cnt=-1; imp=0.0
deathBar=None; deathCf=None
births=[]        # (индекс HH, индекс нуля по действующему, бар слома, бар подтв. слома)
no_death=0

for i in range(N):
    nw=False
    for hi in (True, False):
        if piv(i,hi) is not None:
            nw = push((H if hi else L)[i-D], i-D, hi, i) or nw
    if tr==1 and lvl is not None:
        if min(O[i],C[i]) < lvl - imp*FIB:
            tr=0; cnt=-1; lvl=None
            deathBar=i; deathCf=i
    fr = piv(i,True) is not None or piv(i,False) is not None
    n=len(P)
    if fr and n>=2:
        lb,hi5,pr,bb,pp = Lb[-1],Hi[-1],P[-1],B[-1],P[-2]
        if pr>pp: imp=pr-pp
        if tr==1:
            if nw and cnt>=5 and (not hi5) and lb=='HL':
                cnt=0; lvl=pr
            else:
                if nw and cnt<5: cnt+=1
                if (not hi5) and lb=='HL': lvl=pr
        else:
            if hi5 and lb=='HH':
                j=n-2
                while j>=0 and Hi[j]: j-=1
                if j>=0 and Lb[j]=='LL':
                    tr=1; cnt=1; lvl=P[j]
                    if deathBar is None: no_death+=1
                    else: births.append((n-1, j, deathBar, deathCf))

def seq_after(idx_hh, cut, usecf):
    """индексы колен строго после слома и строго до HH"""
    out=[]
    for k in range(idx_hh):
        t = Cf[k] if usecf else B[k]
        if t > cut: out.append(k)
    return out

def check(usecf):
    okA=okB=diff=0; badA=[]
    for hh, z, dB, dCf in births:
        cut = dCf if usecf else dB
        s = seq_after(hh, cut, usecf)
        # вариант A: первая вершина после слома = LH, первый низ после неё = LL
        a_ok=False; a_zero=None
        hs=[k for k in s if Hi[k]]
        if hs and Lb[hs[0]]=='LH':
            ls=[k for k in s if (not Hi[k]) and k>hs[0]]
            if ls and Lb[ls[0]]=='LL':
                a_ok=True; a_zero=ls[0]
        # вариант B: была LH после слома и раньше действующего нуля
        b_ok = any(Hi[k] and Lb[k]=='LH' and k < z for k in s)
        if a_ok: okA+=1
        if b_ok: okB+=1
        if a_ok and a_zero!=z: diff+=1
        if not a_ok:
            if not hs:            badA.append('после слома вообще нет вершины до HH')
            elif Lb[hs[0]]!='LH': badA.append('первая вершина после слома — ' + Lb[hs[0]] + ', не LH')
            else:
                ls=[k for k in s if (not Hi[k]) and k>hs[0]]
                if not ls:        badA.append('после этой LH нет низа до HH')
                else:             badA.append('первый низ после LH — ' + Lb[ls[0]] + ', не LL')
    return okA, okB, diff, badA

tot=len(births)
print(f'рождений всего: {tot}   (плюс {no_death} до первого слома, они вне разбора)')
for usecf,nm in ((False,'по бару колена'), (True,'по бару подтверждения')):
    okA,okB,diff,badA = check(usecf)
    print(f'\n═══ {nm} ═══')
    print(f'  вариант A, строгий   проходит {okA:4} из {tot}  ({100*okA/tot:.1f}%)   запрещает {tot-okA}')
    print(f'  вариант B, мягкий    проходит {okB:4} из {tot}  ({100*okB/tot:.1f}%)   запрещает {tot-okB}')
    print(f'  ноль ОТЛИЧАЕТСЯ от действующего: {diff} из {okA} прошедших вариант A')
    from collections import Counter
    print('  почему вариант A не проходит:')
    for r, c in Counter(badA).most_common():
        print(f'    {c:3}  {r}')
