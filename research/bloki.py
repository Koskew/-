import sys,re
def count(p):
    n=0; per=[]
    for i,l in enumerate(open(p).read().split('\n'),1):
        s=l.split('//')[0].rstrip()
        if not s.strip(): continue
        t=s.strip()
        if re.match(r'^(if|else if|else|for|while|switch)\b',t) or re.search(r'=>\s*$',t) or re.match(r'^[a-zA-Z_][\w.]*\s*\(.*\)\s*=>',t) or re.search(r'=\s*if\b',t) or re.search(r'=\s*switch\b',t):
            n+=1; per.append(i)
    return n,per
for p in sys.argv[1:]:
    n,per=count(p); print(p.split('/')[-1], n)
