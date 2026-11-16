# Сверка логики бледной метки v3.44 (f_paleK, З78) с репликой dvizhok2: номер бледной == номер сплошной на следующем баре. Это САМОПРОВЕРКА кода, а не замер В35.
import sys; sys.path.insert(0,'research')
import dvizhok2 as D
rows=D.load('data/XAUUSD_1h_9y.csv')
hi=[r[2] for r in rows]; lo=[r[3] for r in rows]
def run(flip):
    snap={}
    orig=D.Trend.step
    def step(self,bar,o,h,l,c,K,*a,**k):
        r=orig(self,bar,o,h,l,c,K,*a,**k)
        snap.setdefault(id(self),{})[bar]=(list(K.P[-12:]),list(K.B[-12:]),list(K.H[-12:]),len(K.P),self.zb,self.st)
        return r
    D.Trend.step=step
    res=D.run_all(rows,flip=flip,zguard=True,knee_seq=True,birth_lvl=True,cont_touch=True)
    D.Trend.step=orig
    return snap[id(res['T'][2])]
U=run(False); Dn=run(True)
LIVE=(D.ST_MAY,D.ST_LIVE)
def zi_of(B,H,zb,dn):
    for q in range(len(B)):
        if B[q]>=zb and H[q]==dn: return q
    return -1
def paleK(P,B,H,zb,dn,cp,chi,hp=None):
    zx=zi_of(B,H,zb,dn) if zb>=0 else -1
    if zx<0: return -1
    if chi==dn and not (cp<P[zx] if dn else cp>P[zx]): return -1
    n=len(P)
    if not chi and hp is not None:
        if dn and hp>=P[zx]: return -1
        ne=n if H[-1] else n+1
        kh=ne-zx
        return kh if 1<=kh<=5 else -1
    if H[-1]==chi:
        bt= cp>P[-1] if chi else cp<P[-1]
        km=n-1-zx
        return km if bt and 1<=km<=5 else -1
    kn=n-zx
    return kn if 1<=kn<=5 else -1
def piv(i,d_right,isH):
    if i-2<0 or i+d_right>=len(rows): return False
    a=hi if isH else lo
    if isH: return all(a[i-k]<=a[i] for k in (1,2)) and all(a[i+k]<a[i] for k in range(1,d_right+1))
    return all(a[i-k]>=a[i] for k in (1,2)) and all(a[i+k]>a[i] for k in range(1,d_right+1))
stat={}; kinds={}; other=[]
for name,S,dn in (('восх',U,False),('нисх',Dn,True)):
    agree=dis=endz=0; ex=[]
    for t in range(3,len(rows)-1):
        if t not in S or t+1 not in S: continue
        P,B,H,n,zb,st=S[t]
        if st not in LIVE: continue
        # реальная цепочка нужна в настоящих ценах: у flip цены с минусом, стороны наоборот
        if dn: Pr=[-p for p in P]; Hr=[not h for h in H]
        else: Pr,Hr=P,H
        for isH in (False,True):
            c=t-1
            if not piv(c,1,isH): continue
            cp=hi[c] if isH else lo[c]
            # в мире нисх «вершина» настоящая = низ перевёрнутый; paleK считаем в настоящем мире
            hp=hi[c] if (not isH and piv(c,1,True)) else None
            k=paleK(Pr,B,Hr,zb,dn,cp,isH,hp)
            if k<0: continue
            if not piv(c,2,isH): continue      # не устояла — сверять номер не с чем
            P2,B2,H2,n2,zb2,st2=S[t+1]
            if dn: Pr2=[-p for p in P2]; Hr2=[not h for h in H2]
            else: Pr2,Hr2=P2,H2
            zx=zi_of(B2,Hr2,zb2,dn) if zb2>=0 else -1
            idx=[q for q in range(len(B2)) if B2[q]==c and Hr2[q]==isH]
            if zx>=0 and idx and idx[0]-zx==k: agree+=1
            elif zb2!=zb or st2 not in LIVE: endz+=1
            else:
                dis+=1
                cls='накрышка, вершина не устояла' if (not isH and piv(c,1,True) and not piv(c,2,True)) else 'ДРУГОЕ'
                kinds[name+' · '+cls]=kinds.get(name+' · '+cls,0)+1
                if cls=='ДРУГОЕ': other.append((rows[c][0],isH,k))
                if len(ex)<5: ex.append((rows[c][0],isH,k,(idx[0]-zx) if (idx and zx>=0) else None,st2))
    print(name,'совпало',agree,'· тот же бар сменил ноль или кончил тренд',endz,'· расхождений',dis); [print('   ',e) for e in ex]

print(kinds); print('ДРУГОЕ:',other[:10])
