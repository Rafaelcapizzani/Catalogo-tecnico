import sys,json,re,difflib,itertools,os
sys.path.insert(0,'/home/claude')
import pymupdf as fitz, numpy as np
import ga_seg as G, cotas as C
from folha import folha
OFF=13
EXTRA_GA={'CM-093','SU-083'}   # vinham da Gold III, mas o desenho com peso está na Geral Alcoa
PAGEFIX={'FC-246':292}
idx=json.load(open('/home/claude/alcoa/geral_idx.json'))
rows=[x for x in json.load(open('/home/claude/alcoa/cruzamento2.json')) if x[5]=='Geral Alcoa' or x[0] in EXTRA_GA]
TR=str.maketrans({'O':'0','o':'0','l':'1','I':'1','!':'1','|':'1','/':'1','S':'5','B':'8','Z':'2','—':'-','_':'-','–':'-','U':'0','D':'0','Q':'0'})
def nz(s): return re.sub(r'[^A-Z0-9]','',s.upper())
def nnum(s): return re.sub(r'[^0-9]','',s.translate(TR))
def score(code,peso,lab,tsvtxt):
    best=0
    for t in (lab['cod'],tsvtxt):
        t1=t.split('(')[0]
        a=difflib.SequenceMatcher(None,nz(t1),nz(code)).ratio()
        b=difflib.SequenceMatcher(None,nnum(t1),nnum(code)).ratio()
        best=max(best,a,b)
    pw=nnum(lab['peso']); cw=nnum(peso)
    w=difflib.SequenceMatcher(None,pw[:len(cw)+1],cw).ratio() if pw else 0
    return best+0.8*w
cache={}
def pagina(pno):
    if pno in cache: return cache[pno]
    an=[a for a in G.analisa(pno) if not a.get('vazio')]
    W=G.tsv(pno)
    labs=[]
    for ci,a in enumerate(an):
        for li,l in enumerate(a['labs']):
            r=[v/G.S for v in l['rect']]
            txt=' '.join(w[0] for w in W if r[0]<=w[1]+w[3]/2<=r[2] and r[1]<=w[2]+w[4]/2<=r[1]+60)
            labs.append((ci,li,l,txt))
    pr=G.D[pno-1]  # candidates
    cand=[(k,v[0]) for k,v in idx.items() if PAGEFIX.get(k,v[1]+OFF)==pno]
    # greedy assignment by score
    sc=sorted(((score(k,pw,l,t),k,ci,li) for k,pw in cand for ci,li,l,t in labs),reverse=True)
    used=set();ass={}
    for s,k,ci,li in sc:
        if k in ass or (ci,li) in used: continue
        ass[k]=(ci,li,round(s,2)); used.add((ci,li))
    cache[pno]=(an,ass); return cache[pno]
def jobs(sel=None):
    J={};prob=[]
    for x in rows:
        if sel and x[0] not in sel: continue
        cod=x[7]
        if cod not in idx: prob.append((x[0],cod,'fora do índice')); continue
        pno=PAGEFIX.get(cod,idx[cod][1]+OFF)
        an,ass=pagina(pno)
        if cod not in ass: prob.append((x[0],cod,'sem célula',pno)); continue
        ci,li,s=ass[cod]; a=an[ci]
        nome=x[0] if x[0]==cod else f'{x[0]}_{cod}'
        J[nome]=dict(alplan=x[0],cod=cod,pdf=pno,clip=a['clip'],apagar=a['apagar'],peso=idx[cod][0],score=s,nlab=len(a['labs']),ocr=a['labs'][li]['cod'],ocrpeso=a['labs'][li]['peso'])
    return J,prob
if __name__=='__main__':
    J,prob=jobs()
    json.dump(J,open('/home/claude/alcoa/ga/jobs.json','w'),indent=0)
    print(len(J),'jobs'); [print('PROB',p) for p in prob]
    for k,v in J.items():
        if v['score']<1.2 or v['nlab']>1: print('baixo',k,v['pdf'],v['score'],v['nlab'],v['ocr'],v['ocrpeso'],v['peso'])
