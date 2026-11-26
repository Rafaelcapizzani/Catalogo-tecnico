import sys,json,re,difflib,subprocess
sys.path.insert(0,'/home/claude')
import pymupdf as fitz, numpy as np, cv2
import cotas as C
SRC='/home/claude/alcoa/asa.pdf'; D=fitz.open(SRC)
idx=json.load(open('/home/claude/alcoa/asa_idx.json'))
rows=[x for x in json.load(open('/home/claude/alcoa/cruzamento2.json')) if x[5]=='Geral ASA']
S=72/300
def nz(s): return re.sub(r'[^A-Z0-9]','',s.upper())
def ocr_box(page,r):
    pm=page.get_pixmap(dpi=400,clip=r+(-1,-1,1,1),colorspace=fitz.csGRAY)
    g=np.frombuffer(pm.samples,np.uint8).reshape(pm.height,pm.width)
    im=255-g; im=np.pad(im,20,constant_values=255) if im.mean()<128 else np.pad(g,20,constant_values=255)
    im=np.where(im<140,0,255).astype(np.uint8)
    cv2.imwrite('/tmp/_b.png',np.pad(255-g,20,constant_values=255))
    return subprocess.run(['tesseract','/tmp/_b.png','-','--psm','7','-c','tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- '],capture_output=True,text=True).stdout.strip()
cache={}
def pagina(pno):
    if pno in cache: return cache[pno]
    page=D[pno-1]
    boxes=[]
    for d in page.get_drawings():
        r=d['rect']; f=d.get('fill')
        if f and (all(abs(v-0.25)<0.03 for v in f) or max(f)-min(f)>0.3) and 45<r.width<120 and 11<r.height<21 and len(d['items'])==1: boxes.append(fitz.Rect(r))
    # textos
    L=[]
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines',[]):
            t=''.join(s['text'] for s in l['spans']).strip()
            if t: L.append((t,fitz.Rect(l['bbox'])))
    labs=[]
    for bx in boxes:
        tt=' '.join(t for t,r in L if bx.contains((r.tl+r.br)/2))
        oc=ocr_box(page,bx)
        blk=fitz.Rect(bx.x0-3,bx.y0-2,bx.x1+3,bx.y1+2)
        for t,r in L:   # peso e equivalência logo abaixo
            if r.y0>=bx.y1-1 and r.y0<bx.y1+48 and r.x1>bx.x0-10 and r.x0<bx.x1+10 and ('kg' in t.lower() or t.startswith('(')): blk|=r+(-1,-1,1,1)
        for d in page.get_drawings():   # caixa cinza do peso (atrás do rótulo)
            r=d['rect']; f=d.get('fill')
            if f and min(f)>0.6 and max(f)<0.9 and 30<r.width<125 and r.height<36 and r.intersects(bx+(-3,-3,3,20)): blk|=r+(-1,-1,1,1)
        blk|=fitz.Rect(bx.x0-4,bx.y1,bx.x1+4,max(blk.y1,bx.y1+13))
        # equivalência "(25-561)" em curvas logo abaixo
        pmq=page.get_pixmap(dpi=150,clip=fitz.Rect(bx.x0-10,blk.y1,bx.x1+10,blk.y1+22),colorspace=fitz.csGRAY)
        gq=np.frombuffer(pmq.samples,np.uint8).reshape(pmq.height,pmq.width)
        rows_=np.nonzero((gq<200).sum(1))[0]
        if len(rows_) and rows_[0]<22 and rows_[-1]-rows_[0]<26: blk|=fitz.Rect(bx.x0-10,blk.y1,bx.x1+10,blk.y1+(rows_[-1]+2)*72/150)
        eq=' '.join(t for t,r in L if t.startswith('(') and blk.contains((r.tl+r.br)/2))
        # equivalência à direita da caixa cinza
        wr=fitz.Rect(blk.x1,bx.y1,blk.x1+50,bx.y1+14)
        pmq=page.get_pixmap(dpi=150,clip=wr,colorspace=fitz.csGRAY)
        gq=np.frombuffer(pmq.samples,np.uint8).reshape(pmq.height,pmq.width)
        cols_=np.nonzero((gq<200).sum(0))[0]
        if len(cols_) and cols_[0]<12 and cols_[-1]-cols_[0]<95:
            blk|=fitz.Rect(blk.x1,bx.y1,blk.x1+(cols_[-1]+3)*72/150,bx.y1+14)
        labs.append(dict(box=bx,txt=tt,ocr=oc,blk=blk,eq=eq))
    cand=set(k for k,v in idx.items() if v[1]==pno)|set(x[7].split(' (')[0].strip() for x in rows if abs(int(x[6])-pno)<=1)
    sc=[]
    for k in cand:
        for i,l in enumerate(labs):
            s=max(difflib.SequenceMatcher(None,nz(l['txt']),nz(k)).ratio() if l['txt'] else 0,difflib.SequenceMatcher(None,nz(l['ocr']),nz(k)).ratio())
            if nz(l['txt'])==nz(k) or nz(l['ocr'])==nz(k) or nz(l['ocr'].replace('O','0'))==nz(k): s=1.01
            for t_ in (l['txt'],l['ocr'].replace('O','0')):
                if t_ and re.fullmatch(re.escape(nz(k))+r'[A-D]',nz(t_)): s=max(s,1.0)
            if re.search(r'\(\s*'+re.escape(k)+r'\b',l['eq']): s=1.02
            sc.append((s,k,i))
    sc.sort(reverse=True); ass={}; used=set()
    for s,k,i in sc:
        if k in ass or i in used or s<0.6: continue
        ass[k]=(i,round(s,2)); used.add(i)
    # agrupamento do desenho: máscara sem cabeçalho/rodapé e sem rótulos
    pm=page.get_pixmap(dpi=300,colorspace=fitz.csGRAY)
    g=np.frombuffer(pm.samples,np.uint8).reshape(pm.height,pm.width).copy()
    g[:int(75/S)]=255; g[int(788/S):]=255; g[int(762/S):,int(440/S):]=255
    for im in page.get_image_info():
        b=fitz.Rect(im['bbox'])
        if b.width<15 and b.height<15: g[max(0,int(b.y0/S)-3):int(b.y1/S)+3,max(0,int(b.x0/S)-3):int(b.x1/S)+3]=255
    for l in labs:
        b=l['blk']; g[int(b.y0/S):int(b.y1/S)+1,int(b.x0/S):int(b.x1/S)+1]=255
    m=(g<215).astype(np.uint8)
    gm=cv2.dilate(m,np.ones((29,29),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(gm,8)
    comps=[]
    for i in range(1,n):
        x,y,w,h,a=st[i]
        if w*S<8 and h*S<8: continue
        mm=(lab[y:y+h,x:x+w]==i)&(m[y:y+h,x:x+w]>0)
        ys,xs=np.nonzero(mm)
        comps.append(fitz.Rect((x+xs.min())*S,(y+ys.min())*S,(x+xs.max()+1)*S,(y+ys.max()+1)*S))
    cache[pno]=(labs,ass,comps,L); return cache[pno]
def dist(a,b):
    dx=max(0,a.x0-b.x1,b.x0-a.x1); dy=max(0,a.y0-b.y1,b.y0-a.y1); return (dx*dx+dy*dy)**.5
if __name__=='__main__':
    J={};prob=[]
    for x in rows:
        cod=x[7].split(' (')[0].strip(); pno=int(x[6]); pwo='texto'
        labs,ass,comps,L=pagina(pno)
        if cod not in ass:
            for p2 in (pno-1,pno+1):
                if cod in pagina(p2)[1]: pno=p2; labs,ass,comps,L=pagina(p2); break
        if cod not in ass: prob.append((x[0],cod,pno,'rótulo não achado',[l['ocr'] for l in labs])); continue
        i,s=ass[cod]; bx=labs[i]['box']
        # componentes: o mais próximo do rótulo + os que ficam mais perto deste rótulo que de outros
        # principal de cada rótulo = maior componente entre os mais próximos; demais vão para o principal mais perto
        mains={}
        for li,l in enumerate(labs):
            near=sorted([c for c in comps if c.width*c.height>150],key=lambda c:dist(c,l['box'])+(30 if c.y0>l['box'].y1-1 else 0))[:1]
            near=[c for c in near if dist(c,l['box'])<90]
            if near: mains[li]=near[0]
        if i not in mains: prob.append((x[0],cod,pno,'sem desenho')); continue
        own=[mains[i]]
        for c in comps:
            if c in mains.values(): continue
            dd={li:dist(c,mc) for li,mc in mains.items()}
            best=min(dd,key=dd.get)
            nb=int(np.argmin([dist(c,l['box']) for l in labs]))
            if best==i and dd[i]<45 and nb==i: own.append(c)
        if not own: prob.append((x[0],cod,pno,'sem desenho')); continue
        clip=fitz.Rect(own[0])
        for c in own[1:]: clip|=c
        clip=clip+(-2,-2,2,2)
        nome=x[0] if x[0]==cod else f'{x[0]}_{cod}'
        pw=next((re.sub(r'(?i)\s*kg/m','',t).strip() for t,r in L if 'kg' in t.lower() and labs[i]['blk'].contains((r.tl+r.br)/2)),None)
        imgs=[tuple(fitz.Rect(im['bbox'])) for im in D[pno-1].get_image_info() if fitz.Rect(im['bbox']).intersects(clip) and fitz.Rect(im['bbox']).width>15]
        if not pw:
            bx2=labs[i]['box']; rr=fitz.Rect(bx2.x0,bx2.y1,bx2.x1,bx2.y1+11)
            pm2=D[pno-1].get_pixmap(dpi=500,clip=rr,colorspace=fitz.csGRAY)
            g2=np.frombuffer(pm2.samples,np.uint8).reshape(pm2.height,pm2.width)
            cv2.imwrite('/tmp/_w.png',np.pad(np.where(g2<120,0,255).astype(np.uint8),25,constant_values=255))
            tw=subprocess.run(['tesseract','/tmp/_w.png','-','--psm','7'],capture_output=True,text=True).stdout
            mm_=re.search(r'(\d)[,.](\d{3})',tw)
            if mm_: pw=f'{mm_.group(1)},{mm_.group(2)}'; pwo='ocr'
        J[nome]=dict(imgs=imgs,alplan=x[0],cod=cod,pdf=pno,clip=tuple(clip),apagar=[tuple(l['blk']) for l in labs if l['blk'].intersects(clip)]+[(440,762,595,842)],peso=x[8],peso_lido=pw,peso_fonte=pwo,score=s,nown=len(own))
    json.dump(J,open('/home/claude/alcoa/asa/jobs.json','w'),indent=0)
    print(len(J)); [print('PROB',p) for p in prob]
    for k,v in J.items():
        if v['score']<1 or (v['peso_lido'] and v['peso'] and v['peso_lido']!=v['peso']): print('ver',k,v['score'],v['peso'],v['peso_lido'])
