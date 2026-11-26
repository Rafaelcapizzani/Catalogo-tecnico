import sys,json,re
sys.path.insert(0,'/home/claude')
import pymupdf as fitz, numpy as np, cv2
import ga_seg as G, cotas as C
CAT={'Gold III':'/home/claude/alcoa/gold3.pdf','Gold IV':'/home/claude/alcoa/gold4.pdf'}
DOC={k:fitz.open(v) for k,v in CAT.items()}
rows=[x for x in json.load(open('/home/claude/alcoa/cruzamento2.json')) if x[5] in CAT]
NUM=C.NUM; S=72/300
def nz(s): return re.sub(r'[^A-Z0-9]','',s.upper())
def linhas(page):
    out=[]
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines',[]):
            t=''.join(s['text'] for s in l['spans']).strip()
            if t: out.append((t,fitz.Rect(l['bbox']),l['dir']))
    return out
def dist(a,b):
    dx=max(0,a.x0-b.x1,b.x0-a.x1); dy=max(0,a.y0-b.y1,b.y0-a.y1); return (dx*dx+dy*dy)**.5
def numtok(t): return bool(t.split()) and (all(NUM.match(q) for q in t.split()) or bool(re.match(r'^[oøØ∅]\s?\d',t)))
def comps_of(page,zero,th,area=None):
    pm=page.get_pixmap(dpi=300,colorspace=fitz.csGRAY,clip=area)
    g=np.frombuffer(pm.samples,np.uint8).reshape(pm.height,pm.width).copy()
    ox,oy=(area.x0,area.y0) if area else (0,0)
    for r in zero:
        r=fitz.Rect(r); g[max(0,int((r.y0-oy)/S)-2):max(0,int((r.y1-oy)/S)+2),max(0,int((r.x0-ox)/S)-2):max(0,int((r.x1-ox)/S)+2)]=255
    m=(g<th).astype(np.uint8)
    return m,ox,oy
def job(x):
    cat=x[5]; D=DOC[cat]; pno=int(x[6]); page=D[pno-1]; L=linhas(page)
    cod=x[7]
    def achar(L):
        cc=[(t,r) for t,r,d in L for cc_ in (cod,x[0]) if nz(t)==nz(cc_) or nz(t).startswith(nz(cc_)) and len(nz(t))<=len(nz(cc_))+1]
        return [(t,r) for t,r in cc if any('kg/m' in t2.lower() and (0<r2.y0-r.y0<24 and abs(r2.x0-r.x0)<20 or abs(r2.y0-r.y0)<4 and 0<r2.x0-r.x1<40) for t2,r2,d2 in L)]
    cand=achar(L)
    if not cand:
        for p2 in list(range(pno-3,pno+4))+list(range(1,len(D)+1)):
            if 1<=p2<=len(D) and p2!=pno:
                L2=linhas(D[p2-1]); c2=achar(L2)
                if c2: pno=p2; page=D[p2-1]; L=L2; cand=c2; break
    if not cand: return None,'código não achado (com peso) no catálogo'
    t,cr=cand[0]
    txt=[r for tt,r,d in L if not numtok(tt)]          # todo texto não numérico (código, peso, títulos)
    marks=[]
    for dr in page.get_drawings():                      # ● ■ junto do código / caixa azul do código
        r=dr['rect']; f=dr.get('fill')
        if f and 5<=r.width<12 and 5<=r.height<12 and dist(r,cr)<32: marks.append(fitz.Rect(r)+(-1,-1,1,1))
        if f and max(f)-min(f)>0.3 and r.intersects(cr) and r.width<120 and r.height<25: marks.append(fitz.Rect(r))
        if f and min(f)>0.6 and max(f)<0.95 and r.width<130 and r.height<25 and dist(r,cr)<40 and abs(r.y0-cr.y0)<15: marks.append(fitz.Rect(r))
    if cat=='Gold III':
        cells=[c for c in G.grid(page) if c.contains(cr)]
        if not cells: return None,'sem célula'
        c=cells[0]
        m,ox,oy=comps_of(page,txt+marks,215,area=c+(-0,-0,0,0))
        m[:8,:]=0;m[-8:,:]=0;m[:,:8]=0;m[:,-8:]=0
        ys,xs=np.nonzero(m)
        if not len(xs): return None,'célula vazia'
        clip=fitz.Rect(ox+xs.min()*S-2,oy+ys.min()*S-2,ox+(xs.max()+1)*S+2,oy+(ys.max()+1)*S+2)&c
        ap=[r for r in txt+marks if r.intersects(clip)]
    else:
        zero=txt+marks+[fitz.Rect(0,0,page.rect.width,95),fitz.Rect(0,805,page.rect.width,page.rect.height),fitz.Rect(page.rect.width-45,0,page.rect.width,page.rect.height)]
        m,ox,oy=comps_of(page,zero,150)
        gm=cv2.dilate(m,np.ones((15,15),np.uint8))
        for dr in page.get_drawings():   # separadores cinza entre perfis: corta o agrupamento
            col=dr.get('color')
            if not col or abs(col[0]-0.616)>0.05: continue
            for it in dr['items']:
                if it[0]!='l': continue
                a_,b_=it[1],it[2]
                if abs(a_.x-b_.x)<0.5 and abs(a_.y-b_.y)>60: gm[int(min(a_.y,b_.y)/S):int(max(a_.y,b_.y)/S),max(0,int(a_.x/S)-9):int(a_.x/S)+9]=0
                if abs(a_.y-b_.y)<0.5 and abs(a_.x-b_.x)>60: gm[max(0,int(a_.y/S)-9):int(a_.y/S)+9,int(min(a_.x,b_.x)/S):int(max(a_.x,b_.x)/S)]=0
        n,lab,st,_=cv2.connectedComponentsWithStats(gm,8)
        comps=[]
        for i in range(1,n):
            x_,y_,w_,h_,a_=st[i]
            if w_*S<6 and h_*S<6: continue
            mm=(lab[y_:y_+h_,x_:x_+w_]==i)&(m[y_:y_+h_,x_:x_+w_]>0); yy,xx=np.nonzero(mm)
            comps.append(fitz.Rect((x_+xx.min())*S,(y_+yy.min())*S,(x_+xx.max()+1)*S,(y_+yy.max()+1)*S))
        # rótulos de todos os perfis da página
        labs=[r for tt,r,d in L if re.match(r'^[A-Z]{2,4}-?\d{3,4}[A-Z]?$',tt.replace(' ','')) and any('kg/m' in t2 for t2,r2,d2 in L if abs(r2.y0-r.y0)<4 and 0<r2.x0-r.x1<40)]
        if not any(l==cr for l in labs): labs.append(cr)
        def sc(c,l): return dist(c,l)+(150 if c.y1<l.y0+2 else 0)+0.6*max(0,abs((c.x0+c.x1)/2-(l.x0+110))-90)
        mains={}
        for li,l in enumerate(labs):
            nb=sorted([c for c in comps if c.width*c.height>150],key=lambda c:sc(c,l))[:1]
            if nb and sc(nb[0],l)<260: mains[li]=nb[0]
        i=labs.index(cr)
        if i not in mains: return None,'sem desenho'
        own=[mains[i]]
        for c in comps:
            if c in mains.values(): continue
            dd={li:dist(c,mc) for li,mc in mains.items()}; b=min(dd,key=dd.get)
            nl=min(range(len(labs)),key=lambda q:sc(c,labs[q]))
            if b==i and dd[i]<45 and nl==i: own.append(c)
        clip=fitz.Rect(own[0])
        for c in own[1:]: clip|=c
        clip=clip+(-2,-2,2,2)
        ap=[r for r in txt+marks if r.intersects(clip)]
    for tt,r,d in L:
        if numtok(tt) and r.intersects(clip): clip|=r+(-1,-1,1,1)
    pw=next((re.sub(r'(?i)\s*kg/m','',tt).strip().replace('.',',') for tt,r,d in L if 'kg/m' in tt.lower() and (0<r.y0-cr.y0<24 and abs(r.x0-cr.x0)<20 or abs(r.y0-cr.y0)<4 and 0<r.x0-cr.x1<40)),None)
    return dict(alplan=x[0],cod=cod,cat=cat,pdf=pno,clip=tuple(clip),apagar=[tuple(a) for a in ap],peso=x[8],peso_lido=pw),None
if __name__=='__main__':
    J={};prob=[]
    for x in rows:
        j,e=job(x)
        if e: prob.append((x[0],x[5],x[7],x[6],e)); continue
        J[x[0] if x[0]==x[7] else f'{x[0]}_{x[7]}']=j
    json.dump(J,open('/home/claude/alcoa/gold/jobs.json','w'),indent=0)
    print(len(J)); [print('PROB',p) for p in prob]
    for k,v in J.items():
        pl=(v['peso_lido'] or '').replace('.',','); pp=(v['peso'] or '').replace('.',',')
        if pl!=pp: print('peso',k,pp,pl)
