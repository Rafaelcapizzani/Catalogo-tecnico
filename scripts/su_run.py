import sys,json,re,os
sys.path.insert(0,'/home/claude')
import pymupdf as fitz, numpy as np, cv2
import ga_seg as G, cotas as C
SRC='/home/claude/alcoa/suprema.pdf'; OUT='/home/claude/alcoa/su/v1'
D=fitz.open(SRC)
rows=[x for x in json.load(open('/home/claude/alcoa/cruzamento2.json')) if x[5]=='Suprema']
NUM=C.NUM
def linhas(page):
    out=[]
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines',[]):
            tx=''.join(s['text'] for s in l['spans']).strip()
            if tx: out.append((tx,fitz.Rect(l['bbox'])))
    return out
def job(x):
    cod=x[7]; pno=int(x[6]); page=D[pno-1]; L=linhas(page)
    cand=[(t,r) for t,r in L if t.replace(' ','')==cod]
    if not cand:
        cand=[(t,r) for t,r in L if t.replace(' ','').startswith(cod)]
    if not cand: return None,'código não achado na página'
    def temkg(r): return any('kg/m' in tt and 0<rr.y0-r.y0<20 and abs(rr.x0-r.x0)<15 for tt,rr in L)
    cand=sorted(cand,key=lambda z:not temkg(z[1]))
    t,cr=cand[0]
    cells=[c for c in G.grid(page) if c.contains(cr)]
    if not cells: return None,'sem célula'
    c=cells[0]
    codes_in=[1 for tt,rr in L if c.contains(rr) and re.match(r'^[A-Z]{2,3}-\d{3,4}$',tt.replace(' ','')) and fitz.Rect(rr).y0>c.y0+0.55*c.height]
    lab=fitz.Rect(c.x0,cr.y0-2,max(cr.x1,c.x0+60)+6,c.y1)
    icon=fitz.Rect()
    # textos não numéricos (título etc.)
    txt=[r for tt,r in L if c.intersects(r) and not NUM.match(tt) and not re.match(r'^[A-Z]{1,4}-?\d{2,4}[A-Z]?$',tt.replace(' ',''))]
    S=72/300
    pm=page.get_pixmap(dpi=300,clip=c,colorspace=fitz.csGRAY)
    g=np.frombuffer(pm.samples,np.uint8).reshape(pm.height,pm.width).copy()
    def z(r):
        r=fitz.Rect(r)&c
        if r.is_empty: return
        g[int((r.y0-c.y0)/S)-3:int((r.y1-c.y0)/S)+3,max(0,int((r.x0-c.x0)/S)-3):int((r.x1-c.x0)/S)+3]=255
    ic=[]; cand=[]
    for dr in page.get_drawings():
        r=dr['rect']; cols=[tuple(round(v,2) for v in q) for q in (dr.get('fill'),dr.get('color')) if q]
        if c.contains(r) and cols and all(q in ((0.14,0.12,0.13),(0.0,0.0,0.0)) or (0.5<q[0]<0.75 and abs(q[0]-q[2])<0.05) for q in cols) and r.x0>c.x1-115 and r.y1<c.y0+150 and r.width<60 and r.height<60 and len(dr['items'])!=3:
            cand.append([fitz.Rect(r),len(dr['items']),dr['type']])
    def tri(r,ni,ty): return ty!='s' and ni==7 and 4<r.width<13 and 4<r.height<13
    def frame(r,ni,ty): return ty=='s' and ni>=8 and r.width>=10 and r.height>=15
    grupos=[]
    for r,ni,ty in cand:
        alvo=[g_ for g_ in grupos if (g_[0]+(-13,-8,13,8)).intersects(r)]
        nt=1 if tri(r,ni,ty) else 0; fr=frame(r,ni,ty)
        if alvo:
            g0=alvo[0]; g0[0]|=r; g0[1]+=nt; g0[2]=g0[2] or fr
            for g_ in alvo[1:]: g0[0]|=g_[0]; g0[1]+=g_[1]; g0[2]=g0[2] or g_[2]; grupos.remove(g_)
        else: grupos.append([fitz.Rect(r),nt,fr])
    # componentes do raster (moldura do pictograma) junto do grupo de triângulos
    n0,l0,s0,_=cv2.connectedComponentsWithStats((g<215).astype(np.uint8),8)
    for gr,nt,fr in grupos:
        ok=(nt>=2) or (nt>=1 and fr) or (nt>=1 and gr.x1>c.x1-25 and gr.y0<c.y0+70)
        if not ok or gr.width>125 or gr.height>75: continue
        box=fitz.Rect(gr)
        ex=gr+(-12,-12,12,12)
        for i in range(1,n0):
            x_,y_,w_,h_,a_=s0[i]
            rr=fitz.Rect(c.x0+x_*S,c.y0+y_*S,c.x0+(x_+w_)*S,c.y0+(y_+h_)*S)
            if ex.contains(rr): box|=rr
        ic.append(box+(-1,-1,1,1))
    icon=fitz.Rect(icon)
    for dr in page.get_drawings():   # marcador ▲/● junto do código
        r=dr['rect']
        if dr.get('fill') and c.contains(r) and len(dr['items'])>=3 and 5.5<=r.width<12 and 5.5<=r.height<12 and r.x0<c.x0+30 and cr.y0-48<r.y0<cr.y0: ic.append(fitz.Rect(r)+(-1,-1,1,1))
    for r in [lab,icon]+txt+ic: z(r)
    m=(g[8:-8,8:-8]<215).astype(np.uint8)
    # agrupa o que está perto (até ~5 pt) e descarta grupos soltos no canto superior direito (pictogramas, setas)
    gm=cv2.dilate(m,np.ones((41,41),np.uint8))
    ng,lg,sg,_=cv2.connectedComponentsWithStats(gm,8)
    H,W=m.shape; big=max(range(1,ng),key=lambda i:sg[i][4])
    numr=[r for tt,r in L if c.intersects(r) and NUM.match(tt)]
    extra=[]
    for i in range(1,ng):
        if i==big: continue
        gx,gy,gw,gh,ga_=sg[i]
        rr=fitz.Rect(c.x0+(gx+8)*S,c.y0+(gy+8)*S,c.x0+(gx+gw+8)*S,c.y0+(gy+gh+8)*S)
        if gx>0.45*W and gy+gh<0.5*H and gw*S<110 and gh*S<110 and not any(rr.intersects(q) for q in numr):
            m[lg==i]=0; extra.append(rr)
    n,_,st,_=cv2.connectedComponentsWithStats(m,8)
    bx=[st[i] for i in range(1,n) if st[i][4]>15]
    x0=min(b[0] for b in bx)+8;y0=min(b[1] for b in bx)+8;x1=max(b[0]+b[2] for b in bx)+8;y1=max(b[1]+b[3] for b in bx)+8
    clip=fitz.Rect(c.x0+x0*S-2,c.y0+y0*S-2,c.x0+x1*S+2,c.y0+y1*S+2)&c
    for tt,r in L:
        if tt.split() and all(NUM.match(q) for q in tt.split()) and r.intersects(clip) and not r.intersects(lab): clip|=r+(-1,-1,1,1)
    return dict(alplan=x[0],cod=cod,pdf=pno,clip=tuple(clip),apagar=[tuple(lab),tuple(icon)]+[tuple(r) for r in txt]+[tuple(r) for r in extra],peso=x[8],ncod=len(codes_in),branco=[tuple(r) for r in ic]),None
if __name__=='__main__':
    J={};prob=[]
    for x in rows:
        j,e=job(x)
        if e: prob.append((x[0],x[7],x[6],e)); continue
        nome=x[0] if x[0]==x[7] else f'{x[0]}_{x[7]}'
        J[nome]=j
    json.dump(J,open('/home/claude/alcoa/su/jobs.json','w'),indent=0)
    print(len(J)); [print('PROB',p) for p in prob]
    print('multi',[k for k,v in J.items() if v['ncod']>1])
