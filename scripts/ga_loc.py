import json,re,difflib,collections
r=json.load(open('/home/claude/alcoa/cruzamento2.json'))
ga=[x for x in r if x[5]=='Geral Alcoa']
def words(p):
    try: L=open(f'/home/claude/alcoa/ga/ocr/p{p}.tsv').read().splitlines()[1:]
    except: return []
    out=[]
    for l in L:
        f=l.split('\t')
        if len(f)>11 and f[11].strip(): out.append((f[11].strip(),int(f[6]),int(f[7]),int(f[8]),int(f[9]),float(f[10])))
    return out
TR=str.maketrans({'O':'0','o':'0','l':'1','I':'1','!':'1','|':'1','S':'5','B':'8','Z':'2','—':'-','_':'-','–':'-'})
def nz(s): return re.sub(r'[^A-Z0-9-]','',s.upper()) 
res={}
for x in ga:
    cod=x[7]; best=None
    for p in range(x[6]-1,x[6]+5):
        for w in words(p):
            t=w[0]; 
            pre=re.match(r'[A-Z]+',cod)
            cand=[nz(t)]
            if not pre: cand.append(nz(t.translate(TR)))
            for c in cand:
                s=difflib.SequenceMatcher(None,c,cod).ratio()
                if c==cod: s=1.01
                if best is None or s>best[0]: best=(s,p,w)
    res[x[0]]=(cod,x[6],best)
bad=[k for k,v in res.items() if v[2][0]<0.99]
off=collections.Counter(v[2][1]-v[1] for v in res.values() if v[2][0]>=1)
print('offsets',off); print('não exato',len(bad))
for k in bad: print(k,res[k])
json.dump({k:[v[0],v[2][1],v[2][2][1:5],round(v[2][0],2)] for k,v in res.items()},open('/home/claude/alcoa/ga/loc.json','w'))
