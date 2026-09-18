#!/usr/bin/env python3
"""Какой ноль восходящего честнее — СТРУКТУРНО, без сделок и стопов.

Ноль это дно движения. Значит проверяем то, что видно на разметке:
  1. пробивают ли ноль — цена ушла НИЖЕ его цены до слома тренда;
  2. докуда доходит счёт;
  3. сколько тренд живёт в барах.

Три правила постановки нуля, движок гоняется целиком по каждому:

  old  ноль = ближайший низ перед HH, и он должен быть LL
  C1   после слома: ПЕРВАЯ вершина должна быть LH, и ПЕРВЫЙ низ после
       неё становится нулём, какая бы подпись у него ни была.
       Вершины после слома нет вовсе — ноль как в old, но он ещё и
       обязан стоять НИЖЕ цены слома
  C2   то же, но ноль обязан быть LL: если первый низ после LH оказался
       HL, ищем ближе всего стоящую LL назад (но после слома); нет
       такой — рождения нет

ОТКАТ НА СТАРОЕ ПРАВИЛО, согласовано с владельцем 18.09.2026. Если после
слома последовательность LH -> низ не сложилась — например, первой
пришла сразу HH, — работает старое правило: ноль на ближайший LL перед
HH. Без этого движок залипает: без рождения нет тренда, без тренда нет
слома, а без нового слома правило не перезапускается. На первом прогоне
C1 и C2 дали 9 трендов вместо 301 именно поэтому.
"""
import csv, sys, statistics
from collections import Counter

FIB=0.33; D=5
PATH = sys.argv[1] if len(sys.argv)>1 else 'data/XAUUSD_1h_9y.csv'
rows=list(csv.DictReader(open(PATH)))
O=[float(r['open']) for r in rows]; H=[float(r['high']) for r in rows]
L=[float(r['low']) for r in rows];  C=[float(r['close']) for r in rows]
N=len(O)

def piv(i,hi):
    c=i-D
    if c-D<0 or c+D>=N: return None
    src=H if hi else L
    v=src[c]
    for k in range(c-D,c+D+1):
        if k==c: continue
        if (src[k]>=v) if hi else (src[k]<=v): return None
    return v

def engine(rule):
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
            if (price>P[-1]) if hi else (price<P[-1]): P[-1]=price; B[-1]=bar
        else:
            P.append(price); B.append(bar); Hi.append(hi)
        relabel(); return not same

    REFUSE=[]
    tr=0; lvl=None; cnt=-1; imp=0.0
    dBar=None; dPrice=None          # последний слом
    zP=None; zB=None; bornBar=None; mx=-1; broke=None; zLab='?'
    out=[]
    for i in range(N):
        nw=False
        for hi in (True,False):
            if piv(i,hi) is not None:
                nw = push((H if hi else L)[i-D], i-D, hi) or nw
        if tr==1:
            if broke is None and L[i] < zP: broke = i - bornBar
            if lvl is not None and min(O[i],C[i]) < lvl - imp*FIB:
                out.append(dict(life=i-bornBar, mx=mx, broke=broke, zP=zP, zB=zB, zLab=zLab))
                dBar, dPrice = i, lvl
                tr=0; cnt=-1; lvl=None; broke=None
        fr = piv(i,True) is not None or piv(i,False) is not None
        n=len(P)
        if fr and n>=2:
            lb,hi5,pr,pp = Lb[-1],Hi[-1],P[-1],P[-2]
            if pr>pp: imp=pr-pp
            if tr==1:
                if nw and cnt>=5 and (not hi5) and lb=='HL': cnt=0; lvl=pr; zP=pr; zB=B[-1]
                else:
                    if nw and cnt<5: cnt+=1; mx=max(mx,cnt)
                    if (not hi5) and lb=='HL': lvl=pr
            elif hi5 and lb=='HH':
                j=n-2
                while j>=0 and Hi[j]: j-=1
                zi=None
                if rule=='old':
                    if j>=0 and Lb[j]=='LL': zi=j
                else:
                    if dBar is None:                       # до первого слома
                        if j>=0 and Lb[j]=='LL': zi=j
                    else:
                        s=[k for k in range(n-1) if B[k]>dBar]
                        hs=[k for k in s if Hi[k]]
                        done=False
                        if not hs:
                            if j>=0 and Lb[j]=='LL' and P[j]<dPrice: zi=j
                            done=True
                        elif Lb[hs[0]]=='LH':
                            ls=[k for k in s if (not Hi[k]) and k>hs[0]]
                            if ls:
                                cand=ls[0]
                                done=True
                                if rule=='C1': zi=cand
                                else:
                                    if Lb[cand]=='LL': zi=cand
                                    else:
                                        back=[k for k in range(cand,-1,-1)
                                              if (not Hi[k]) and Lb[k]=='LL' and B[k]>dBar]
                                        zi = back[0] if back else None
                        if not done:
                            # последовательность не сложилась — старое правило
                            if j>=0 and Lb[j]=='LL': zi=j
                if zi is None and dBar is not None:
                    REFUSE.append((i, dBar))
                if zi is not None:
                    tr=1; cnt=1; mx=1
                    zLab=Lb[zi]
                    zP=P[zi]; zB=B[zi]; lvl=zP; bornBar=i; broke=None
                    imp = pr - zP
    return out, REFUSE

def show(name, res):
    tr, REFUSE = res
    n=len(tr)
    if not n:
        print(f'{name}: трендов нет'); return
    br=[t for t in tr if t['broke'] is not None]
    to5=[t for t in tr if t['mx']>=5]; to3=[t for t in tr if t['mx']>=3]
    print(f'\n{name}')
    print(f'  трендов                       {n}')
    print(f'  НОЛЬ ПРОБИТ до слома          {len(br):4}  ({100*len(br)/n:5.1f}%)')
    if br:
        d=[t["broke"] for t in br]
        print(f'    через сколько баров         медиана {statistics.median(d):.0f}, четверть быстрее {sorted(d)[len(d)//4]}')
    print(f'  счёт дошёл до (3)             {len(to3):4}  ({100*len(to3)/n:5.1f}%)')
    print(f'  счёт дошёл до (5)             {len(to5):4}  ({100*len(to5)/n:5.1f}%)')
    life=[t['life'] for t in tr]
    print(f'  жизнь тренда, баров           медиана {statistics.median(life):.0f}, среднее {statistics.mean(life):.0f}')
    by=Counter(t['zLab'] for t in tr)
    if len(by)>1:
        print('  в разбивке по ПОДПИСИ нуля:')
        for lab in sorted(by):
            g=[t for t in tr if t['zLab']==lab]
            gb=[t for t in g if t['broke'] is not None]
            med = statistics.median([t['broke'] for t in gb]) if gb else float('nan')
            g5=len([t for t in g if t['mx']>=5])
            print(f'    ноль {lab}: {len(g):4} трендов · пробит {100*len(gb)/len(g):5.1f}% (медиана {med:.0f} баров) · до (5) {100*g5/len(g):5.1f}% · жизнь {statistics.median([t["life"] for t in g]):.0f}')

from collections import Counter
_o, _r = engine('C1')
print(f'ДИАГНОСТИКА C1: отказов в рождении {len(_r)}')
_c = Counter(d for _, d in _r).most_common(3)
print('  три слома, на которых залипли дольше всего (бар слома -> сколько раз отказали):')
for b, k in _c:
    print(f'    бар {b}: {k} отказов')

print(f'данные: {PATH}, {N} баров')
for rule,name in (('old','═══ OLD — ближайший LL перед HH ═══'),
                  ('C1', '═══ C1 — первый низ после первой LH, хоть HL ═══'),
                  ('C2', '═══ C2 — то же, но ноль обязан быть LL ═══')):
    show(name, engine(rule))
