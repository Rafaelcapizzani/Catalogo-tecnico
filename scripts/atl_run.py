import sys,json,re
sys.path.insert(0,'/home/claude')
import pymupdf as fitz
SRC='/home/claude/alcoa/atlanta.pdf'; D=fitz.open(SRC)
J=json.load(open('/home/claude/alcoa/cruzamento2.json'))
alvo=[x for x in J if x[5]=='Belmetal Atlanta']
NUM=re.compile(r'^\d{1,4}([.,]\d{1,2})?$')
def linhas(p):
    out=[]
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines',[]):
            t=' '.join(s['text'] for s in l['spans']).strip()
            if t: out.append((t,fitz.Rect(l['bbox'])))
    return out
jobs={}
for x in alvo:
    alp,cod,pg,codcat=x[0],x[1],x[6],x[7]
    pg={'FA-237':89,'FA-326':89}.get(codcat,pg)
    p=D[pg-1]; L=linhas(p)
    rot=[(t,r) for t,r in L if re.fullmatch(r'(FA|DC|D)-?\d{2,3}(-?A)?',t.replace(' ',''))]
    me=[r for t,r in rot if t.replace(' ','')==codcat]
    if not me: print('SEM ROTULO',alp,codcat,pg,[t for t,r in rot]); continue
    r0=me[0]
    kg=[r for t,r in L if 'kg/m' in t]
    lado=[r for r in kg+[q for t,q in rot] if abs(r.y0-r0.y0)<6 and r.x0>r0.x1+120]
    esq=[r for r in kg+[q for t,q in rot] if abs(r.y0-r0.y0)<6 and r.x1<r0.x0-20]
    sep=[d['rect'] for d in p.get_drawings() if d['rect'].y0>100 and d['rect'].y1<810 and d.get('color') and 0.4<min(d['color'])<0.8]
    sv=[r for r in sep if r.width<1.5 and r.height>120 and r.y0<r0.y1+40 and r.y1>r0.y1]
    x0=max([r.x1+4 for r in esq]+[r.x1+2 for r in sv if r.x1<r0.x0]+[20]) ; x1=min([r.x0-4 for r in lado]+[r.x0-2 for r in sv if r.x0>r0.x1]+[574])
    abaixo=[r for r in kg+[q for t,q in rot] if r.y0>r0.y1+25 and r.x1>x0 and r.x0<x1]
    sh_=[r for r in sep if r.height<1.5 and r.width>120 and r.y0>r0.y1+25 and r.x1>x0+20 and r.x0<x1-20 and r.x0>x0-60]
    db=max([r0.y1]+[r.y1 for t,r in L if r0.y1-2<r.y0<r0.y1+12 and not NUM.match(t) and r.x0<r0.x0+180]); caixa=fitz.Rect(x0,r0.y0-8,r0.x0+150,db+4); y0=r0.y0-4; y1=min([r.y0-6 for r in abaixo]+[r.y0-2 for r in sh_]+[805])
    for t,r in L:   # tabela Wx/Wy no topo
        if re.match(r'^(W|J)[xy]$',t) or re.search(r'\d cm$',t):
            if not fitz.Rect(x0,y0,x1,y1).intersects(r): continue
            if r.x0>470: x1=min(x1,r.x0-12)
            else: y0=max(y0,r.y1+3)
    reg=fitz.Rect(x0,y0,x1,y1)
    U=fitz.Rect()
    for d in p.get_drawings():
        rr=d['rect']; c=d.get('fill') or d.get('color')
        if not reg.contains(rr) or rr.width>560 or rr.height>600 or rr.intersects(caixa): continue
        if c is None or max(c)>0.55: continue
        U|=rr
    for t,r in L:
        if reg.contains(r) and NUM.match(t) and not r.intersects(caixa): U|=r
    peso=sorted([(r.x0-r0.x0,t) for t,r in L if 'kg/m' in t and abs(r.y0-r0.y0)<6 and r.x0>r0.x0]); peso=[t for _,t in peso]
    pk=re.search(r'\d+,\d+',peso[0]).group(0) if peso else ''
    k=alp+'_'+cod
    jobs[k]={'alplan':alp,'cod':cod,'cat':'Belmetal Atlanta','pdf':pg,'clip':list(U+(-3,-3,3,3)),'apagar':[],'peso':x[8],'peso_lido':pk}
    print(k,pg,[round(v) for v in U],x[8],pk,'' if x[8]==pk else '<<PESO')
import os; os.makedirs('/home/claude/alcoa/atl/v1',exist_ok=True)
json.dump(jobs,open('/home/claude/alcoa/atl/jobs.json','w'),indent=1)
print(len(jobs))
