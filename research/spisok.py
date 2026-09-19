#!/usr/bin/env python3
"""СПИСОК ВОСХОДЯЩИХ ТРЕНДОВ за девять лет, по каждому слою, ЦЕПОЧКАМИ.

Правила владельца:
  · восходящий тренд ВСЕГДА начинается с LL — это ноль (0);
  · каждый следующий низ выше предыдущего: (2) и (4) обязаны быть HL;
  · если после точки (5) приходит HL — это ТРЕНД ПРОДОЛЖЕНИЕ, и этот HL
    становится нулём следующего блока. Цепочка идёт дальше;
  · если после (5) приходит LL — цепочка кончилась.

Одна цепочка = один тренд. Внутри неё блоки: №1 рождение, №2 и дальше —
продолжения.

Выход: research/out/trendy_5-5.csv, _3-3.csv, _2-2.csv
"""
import csv, statistics
from collections import Counter
PATH='data/XAUUSD_1h_9y.csv'
rows=list(csv.DictReader(open(PATH)))
T=[r['time'][:16] for r in rows]
H=[float(r['high']) for r in rows]; L=[float(r['low']) for r in rows]
N=len(H)

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

SPR={r['последовательность']:r['№'] for r in csv.DictReader(open('research/out/spravochnik.csv'))}
FIELDS=['тренд №','блок','тип блока','дата начала (0)','дата конца (5)',
        'последовательность','№ посл.','подпись нуля',
        'цена (0)','цена (1)','цена (2)','цена (3)','цена (4)','цена (5)',
        'ход блока %','ход тренда от рождения %','баров','что после (5)']

def block_ok(Lb,Hi,z):
    """можно ли взять пять колен от z: низы (2) и (4) обязаны быть HL"""
    if z+5 >= len(Lb) or Hi[z]: return None
    seq=[Lb[z+k] for k in range(1,6)]
    return seq if seq[1]=='HL' and seq[3]=='HL' else None

print('СПИСОК ВОСХОДЯЩИХ ТРЕНДОВ ЦЕПОЧКАМИ · XAUUSD 1H · 9 лет')
print('рождение — с LL. После (5) пришла HL — продолжение, цепочка идёт дальше\n')
for D,tag,fn in ((5,'5/5','5-5'),(3,'3/3','3-3'),(2,'2/2','2-2')):
    P,B,Hi,Lb=knees(D); n=len(P)
    out=[]; used=set(); tnum=0
    for z in range(n):
        if z in used or Hi[z] or Lb[z]!='LL': continue
        seq=block_ok(Lb,Hi,z)
        if seq is None: continue
        tnum+=1; blk=0; cur=z; born=P[z]
        while True:
            seq=block_ok(Lb,Hi,cur)
            if seq is None: break
            blk+=1
            prs=[P[cur+k] for k in range(1,6)]
            zp,zb=P[cur],B[cur]; end=B[cur+5]
            nxt=Lb[cur+6] if cur+6<n else ''
            out.append({'тренд №':tnum,'блок':blk,
                'тип блока':'рождение' if blk==1 else 'продолжение',
                'дата начала (0)':T[zb],'дата конца (5)':T[end],
                'последовательность':'·'.join(seq),'№ посл.':SPR.get('·'.join(seq),''),
                'подпись нуля':Lb[cur],'цена (0)':round(zp,2),
                **{f'цена ({k+1})':round(prs[k],2) for k in range(5)},
                'ход блока %':round(100*(max(prs[0],prs[2],prs[4])-zp)/zp,2),
                'ход тренда от рождения %':round(100*(max(prs[0],prs[2],prs[4])-born)/born,2),
                'баров':end-zb,'что после (5)':nxt})
            for k in range(cur,cur+6): used.add(k)
            if nxt!='HL': break
            cur=cur+6                        # HL после (5) становится нулём
    with open(f'research/out/trendy_{fn}.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader()
        for r in out: w.writerow(r)
    chains=Counter(r['тренд №'] for r in out)
    lens=Counter(chains.values())
    born=[r for r in out if r['блок']==1]
    cont=[r for r in out if r['блок']>1]
    print(f'── {tag} ──  трендов (цепочек): {len(chains)}   блоков всего: {len(out)}')
    print(f'   рождений {len(born)}  ·  продолжений {len(cont)}  ({100*len(cont)/len(out):.0f}% блоков)')
    print(f'   длина цепочки: ' + '  '.join(f'{k} блок{"" if k==1 else "а" if k<5 else "ов"} — {v}' for k,v in sorted(lens.items())))
    full=[max(r['ход тренда от рождения %'] for r in out if r['тренд №']==t) for t in chains]
    print(f'   ход всей цепочки: медиана {statistics.median(full):.2f}%  максимум {max(full):.2f}%')
    print(f'   файл: research/out/trendy_{fn}.csv\n')
