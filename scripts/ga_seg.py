import pymupdf as fitz, numpy as np, cv2, re, subprocess, difflib, json
D=fitz.open('/home/claude/alcoa/geral.pdf')
DPI=300; S=72/DPI
def grid(page):
    H=[];V=[];F=None
    for dr in page.get_drawings():
        for it in dr['items']:
            if it[0]=='l':
                a,b=it[1],it[2]
                if abs(a.y-b.y)<0.5 and abs(a.x-b.x)>100: H.append((a.y,min(a.x,b.x),max(a.x,b.x)))
                if abs(a.x-b.x)<0.5 and abs(a.y-b.y)>100: V.append((a.x,min(a.y,b.y),max(a.y,b.y)))
            elif it[0]=='re':
                r=it[1]
                if r.width>400 and r.height>600 and F is None: F=fitz.Rect(r)
    if F is None: F=page.rect+(28,28,-28,-28)
    ys=sorted(set([F.y0,F.y1]+[round(y,1) for y,x0,x1 in H if x1-x0>0.9*F.width]))
    ys2=[]
    for y in ys:
        if not ys2 or y-ys2[-1]>5: ys2.append(y)
    out=[]
    for y0,y1 in zip(ys2,ys2[1:]):
        if y1-y0<70: continue
        xs=[F.x0,F.x1]+[x for x,a,b in V if min(b,y1)-max(a,y0)>0.85*(y1-y0) and F.x0+20<x<F.x1-20]
        xs=sorted(set(round(x,1) for x in xs))
        for x0,x1 in zip(xs,xs[1:]):
            if x1-x0>60: out.append(fitz.Rect(x0,y0,x1,y1))
    return out
def tsv(pno):
    out=[]
    for l in open(f'/home/claude/alcoa/ga/ocr/p{pno}.tsv').read().splitlines()[1:]:
        f=l.split('\t')
        if len(f)>11 and f[11].strip(): out.append((f[11].strip(),int(f[6]),int(f[7]),int(f[8]),int(f[9]),float(f[10])))
    return out
CHK=('REGIONAL','SBA','TUB','ITS','FILIAL','SUL','NORDESTE','SEA','SAA','TUE','TUS')
def ocr(img,psm=7,wl=None):
    if img.size==0 or min(img.shape)<5: return ''
    cv2.imwrite('/tmp/_c.png',img)
    a=['tesseract','/tmp/_c.png','-','--psm',str(psm)]
    if wl: a+=['-c','tessedit_char_whitelist='+wl]
    return subprocess.run(a,capture_output=True,text=True).stdout.strip()
def analisa(pno):
    page=D[pno-1]
    pix=page.get_pixmap(dpi=DPI,colorspace=fitz.csGRAY)
    g=np.frombuffer(pix.samples,np.uint8).reshape(pix.h,pix.w).copy()
    W=tsv(pno); res=[]
    dots=[]; sq=[]; mk=[]
    for dr in page.get_drawings():
        r=dr['rect']
        if 7<r.width<12 and 7<r.height<12 and abs(r.width-r.height)<1 and dr['type']=='s' and any(i[0]=='re' for i in dr['items']): sq.append(fitz.Rect(r))
        if 3<r.width<14 and 3<r.height<14 and not any(i[0]=='re' for i in dr['items']): mk.append(fitz.Rect(r))
        r=dr['rect']
        if dr['fill'] and 5<r.width<13 and 5<r.height<13 and abs(r.width-r.height)<1.5 and len(dr['items'])>=6: dots.append(fitz.Rect(r))
    for c in grid(page):
        px=lambda v:int(v/S)
        inn=lambda w:c.x0/S<w[1]+w[3]/2<c.x1/S and c.y0/S<w[2]+w[4]/2<c.y1/S
        ws=[w for w in W if inn(w)]
        kg=[w for w in ws if re.search(r'k[gq9]/?m',w[0],re.I)]
        ck=[w for w in ws if any(difflib.SequenceMatcher(None,w[0].upper().strip('[]|'),k).ratio()>0.75 for k in CHK) and w[1]>(c.x0+0.3*c.width)/S]
        lab=[];
        for k in kg:
            kcy=k[2]+k[4]/2
            wl=[w for w in ws if abs(w[2]+w[4]/2-kcy)<22 and w[1]<=k[1]]
            x0L=min(w[1] for w in wl)
            cl=sorted([w for w in ws if k[2]-80<w[2]+w[4]/2<k[2]-12 and w[1]>=x0L-45 and w not in ck],key=lambda w:w[1])
            chain=[];xe=None
            for w in cl:
                if xe is None:
                    if w[1]>x0L+45: break
                    chain.append(w); xe=w[1]+w[3]
                elif w[1]-xe<130: chain.append(w); xe=w[1]+w[3]
            allw=wl+chain
            if chain: y0=min(w[2] for w in chain)-14
            else: y0=k[2]-80
            y1=max(w[2]+w[4] for w in allw)+14
            x1=max(w[1]+w[3] for w in allw)+14
            if not chain: x1=max(x1,x0L+560)
            lab.append((min(px(c.x0)+4,x0L-14),y0,x1,y1,k))
        ckrs=[]
        sqc=sorted([q for q in sq if c.contains(q) and q.x0>c.x0+0.45*c.width],key=lambda q:q.y0)
        cls=[]
        for q in sqc:
            if cls and q.y0-cls[-1][-1].y1<25: cls[-1].append(q)
            else: cls.append([q])
        for ii,cl_ in enumerate(cls):
            bot=px(cls[ii+1][0].y0)-40 if ii+1<len(cls) else px(c.y1)-1
            ckrs.append((px(min(q.x0 for q in cl_))-14,px(min(q.y0 for q in cl_))-34,px(c.x1)-1,bot))
        ckc=[]
        for w in sorted(ck,key=lambda w:w[2]):
            if ckc and w[2]-ckc[-1][-1][2]<130: ckc[-1].append(w)
            else: ckc.append([w])
        for cw_ in ckc:
            if len(cw_)>=2: ckrs.append((min(w[1] for w in cw_)-90,min(w[2] for w in cw_)-50,px(c.x1)-1,min(px(c.y1)-1,max(w[2]+w[4] for w in cw_)+60)))
        # marcadores (bolinha/triângulo/estrela) no topo direito da célula
        for q in mk:
            if c.contains(q) and q.x1>c.x1-40 and q not in dots: dots.append(q)
        dots=[q for q in dots if not c.intersects(q) or (q.y0<c.y0+30 and q.x1>c.x1-40)] if False else dots
        lab.sort(key=lambda L:L[1])
        subs=[]
        if len(lab)<=1: subs=[(c,lab)]
        else:
            # divide a célula pelas maiores faixas horizontais vazias (sem desenho fora dos rótulos)
            mm=(g[px(c.y0)+6:px(c.y1)-6,px(c.x0)+6:px(c.x1)-6]<200).astype(np.uint8)
            oy0=px(c.y0)+6; ox0=px(c.x0)+6
            for L in lab: mm[max(0,L[1]-oy0):max(0,L[3]-oy0),max(0,L[0]-ox0):max(0,L[2]-ox0)]=0
            for ckr in ckrs: mm[max(0,ckr[1]-oy0):max(0,ckr[3]-oy0),max(0,ckr[0]-ox0):]=0
            for dt in dots:
                if dt.intersects(c) and dt.x1>c.x1-40 and any(abs(dt.y0-(L[3]*S))<300 for L in lab): mm[max(0,px(dt.y0)-8-oy0):max(0,px(dt.y1)+8-oy0),max(0,px(dt.x0)-8-ox0):max(0,px(dt.x1)+8-ox0)]=0
            rowsum=mm.sum(1)>0
            gaps=[];i=0
            while i<len(rowsum):
                if not rowsum[i]:
                    j=i
                    while j<len(rowsum) and not rowsum[j]: j+=1
                    if i>0 and j<len(rowsum): gaps.append((j-i,(i+j)//2))
                    i=j
                else: i+=1
            cuts=sorted(m for _,m in sorted(gaps,reverse=True)[:len(lab)-1])
            ys=[c.y0]+[(oy0+m)*S for m in cuts]+[c.y1]
            subs=[]
            for a,b in zip(ys,ys[1:]):
                sl=[L for L in lab if a/S<=(L[1]+L[3])/2<=b/S]
                subs.append((fitz.Rect(c.x0,a,c.x1,b),sl))
        if not lab: res.append(dict(cell=tuple(c),vazio=True,nlab=0)); continue
        for sc,sl in subs:
            m=(g[px(sc.y0)+6:px(sc.y1)-6,px(sc.x0)+6:px(sc.x1)-6]<200).astype(np.uint8)
            ox,oy=px(sc.x0)+6,px(sc.y0)+6
            def zero(x0,y0,x1,y1): m[max(0,y0-oy):max(0,y1-oy),max(0,x0-ox):max(0,x1-ox)]=0
            for L in lab: zero(*L[:4])
            for ckr in ckrs: zero(*ckr)
            cd=[dt for dt in dots if dt.intersects(sc) and dt.y0<sc.y0+55 and dt.x1>c.x1-40]
            for dt in cd: zero(px(dt.x0)-6,px(dt.y0)-6,px(dt.x1)+6,px(dt.y1)+6)
            n,_,st,_=cv2.connectedComponentsWithStats(m,8)
            bx=[st[i] for i in range(1,n) if st[i][4]>25]
            if not bx: res.append(dict(cell=tuple(sc),vazio=True,nlab=len(sl))); continue
            x0=min(b[0] for b in bx)+ox; y0=min(b[1] for b in bx)+oy
            x1=max(b[0]+b[2] for b in bx)+ox; y1=max(b[1]+b[3] for b in bx)+oy
            clip=fitz.Rect(x0*S-2,y0*S-2,x1*S+2,y1*S+2)&sc
            labs=[]
            for L in sl:
                k=L[4]
                cod=ocr(g[L[1]:k[2]-6,L[0]:L[2]],7)
                pes=ocr(g[k[2]-8:k[2]+k[4]+8,L[0]:k[1]+8],7,'0123456789.,')
                labs.append(dict(cod=cod,peso=pes,rect=[L[0]*S,L[1]*S,L[2]*S,L[3]*S]))
            ap=[fitz.Rect(*[v*S for v in L[:4]]) for L in lab]+[fitz.Rect(*[v*S for v in ckr]) for ckr in ckrs]+[dt+(-1,-1,1,1) for dt in cd]
            res.append(dict(cell=tuple(sc),clip=tuple(clip),labs=labs,apagar=[tuple(a) for a in ap if a.intersects(clip)]))
    return res
if __name__=='__main__':
    import sys
    for p in map(int,sys.argv[1:]):
        for r in analisa(p): print(p,{k:(v if k!='cell' else [round(x) for x in v]) for k,v in r.items() if k in('cell','labs','vazio')}, [round(x) for x in r.get('clip',[])],len(r.get('apagar',[])))
