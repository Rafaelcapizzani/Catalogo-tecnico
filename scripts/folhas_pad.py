import sys,json;sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
OUT='/home/claude/alcoa/folhas'; J=json.load(open(f'{OUT}/jobs.json'))
sel=sys.argv[1:] or list(J); DPI=600
dados=json.load(open(f'{OUT}/_cotas.json')) if __import__('os').path.exists(f'{OUT}/_cotas.json') else {}
FIX={'DV-302':{'10':'30'},'AP-100':{'58':'38'},'AP-033':{'50':'30'},'BX-218':{'90':'50'},'BX-219':{'73':'75'},'AP-035':{'58':'38'},
     'AP-1718':{'55':'35'},'AP-1717':{'58':'38'},'AP-032':{'50':'30'},'AP-034':{'5':None,'8':None}}
ADD={'AP-035':[('8.5',(30,52.5,40,59),False)],'AP-099':[('5',(146.5,4.5,157.5,14.5),'up')],'AP-100':[('50',(209,0.5,221,7.5),False)],'BX-218':[('9',(75.5,153.5,80.5,160.5),False)],'BX-219':[('9',(111.5,231,116.5,237),False)],'AP-034':[('58',(134.6,98,140.6,111.5),'up')]}
for k in sel:
    j=J[k]; d=fitz.open(j['src']); p=d[0]; R=fitz.Rect(j['clip'])&p.rect
    # tira o rótulo (código) antes de rasterizar
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines',[]): p.add_redact_annot(fitz.Rect(l['bbox']))
    p.apply_redactions(images=0,graphics=0,text=0)
    p.get_pixmap(dpi=130,clip=R).save(f'{OUT}/o_{k}.png')
    p.get_pixmap(dpi=DPI,clip=R,colorspace=fitz.csGRAY).save(f'{OUT}/_r_{k}.png')
    C.preencher(f'{OUT}/_r_{k}.png',f'{OUT}/_p_{k}.png')
    import cv2
    gimg=cv2.imread(f'{OUT}/_p_{k}.png',0); H,W=gimg.shape; kk=72/DPI
    dd=fitz.open(); pp=dd.new_page(width=W*kk,height=H*kk); pp.insert_image(pp.rect,filename=f'{OUT}/_p_{k}.png')
    cot=C.ler_cotas(pp,pp.rect,dpi=DPI)
    fx=FIX.get(k,{})
    cot=[(fx.get(t,t),r,v) for t,r,v in cot if fx.get(t,t) is not None]
    import numpy as np
    for t,rr,v in ADD.get(k,[]):
        A=fitz.Rect(*rr)+(-9,-9,9,9)
        x0,y0,x1,y1=[max(0,int(z/kk)) for z in A]
        sub=(gimg[y0:y1,x0:x1]<160).astype(np.uint8)
        n_,l_,st_,_=cv2.connectedComponentsWithStats(sub,8)
        cand=[s for s in st_[1:] if 2.0/kk<max(s[2],s[3])<12/kk and s[4]>30]
        cx,cy=(rr[0]+rr[2])/2/kk-x0,(rr[1]+rr[3])/2/kk-y0
        cand.sort(key=lambda s:(s[0]+s[2]/2-cx)**2+(s[1]+s[3]/2-cy)**2)
        bb=None
        for s in cand[:len(t.replace('.',''))]:
            r_=fitz.Rect((x0+s[0])*kk,(y0+s[1])*kk,(x0+s[0]+s[2])*kk,(y0+s[1]+s[3])*kk)
            bb=r_ if bb is None else bb|r_
        cot.append((t,bb if bb is not None else fitz.Rect(*rr),v))
    cot=[(t,r,('up' if v=='down' else v)) for t,r,v in cot]   # leitura normal: vertical sempre de baixo para cima
    cs,fs=C.padronizar_raster(f'{OUT}/_p_{k}.png',f'{OUT}/{k}.svg',f'{OUT}/{k}.png',dpi_img=DPI,cotas=cot)
    dados[k]={'origem':f"folha avulsa do cliente ({j['src'].split('/')[-1]})",'tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2,2),'y':round((r.y0+r.y1)/2,2),'direcao':{False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}.get(v,'inclinada')} for t,r,v in cs]}
    print(k,sorted(t for t,r,v in cs),flush=True)
json.dump(dados,open(f'{OUT}/_cotas.json','w'),ensure_ascii=False,indent=1)
