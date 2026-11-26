# ES-031: perfil só em contorno no Euroshow -> preenche as paredes e vetoriza (potrace), com setas/cotas já padronizadas
import sys,json; sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C, cv2, numpy as np
cl=json.load(open('euro/_clips.json')); pg,bb=cl['ES-031']; R=fitz.Rect(bb)
tmp='euro/tmp_ES-031.pdf'; lid=C.ler_cotas(fitz.open(tmp)[0],R)
cs0,fs0=C.padronizar(tmp,1,R,'euro/_v31.svg','euro/_v31.png',cotas=lid,cinza_para_preto=True,setas=True,normalizar=True)
cs,fs=C.padronizar(tmp,1,R,'euro/_e31.svg','euro/_e31.png',cotas=C.ler_cotas(fitz.open(tmp)[0],R),cinza_para_preto=True,setas=True,normalizar=True,enxugar=True)
s=fitz.open('euro/_v31.svg'); P=fitz.open('pdf',s.convert_to_pdf()); P[0].get_pixmap(dpi=300,colorspace=fitz.csGRAY).save('euro/_r31.png')
# só o contorno do perfil (traço 0,72) para achar as paredes; linhas de cota não podem fechar regiões
src=fitz.open(tmp)[0]; T=fitz.open(); q=T.new_page(width=src.rect.width,height=src.rect.height); sh=q.new_shape()
for d in src.get_drawings():
    if d['type']=='s' and (d.get('width') or 0)>0.6 and R.intersects(d['rect']):
        for it in d['items']:
            if it[0]=='l': sh.draw_line(it[1],it[2])
            elif it[0]=='c': sh.draw_bezier(it[1],it[2],it[3],it[4])
        sh.finish(color=(0,0,0),width=0.72,closePath=False)
sh.commit(); q.get_pixmap(dpi=300,clip=R,colorspace=fitz.csGRAY).save('euro/_c31.png')
gp=cv2.imread('euro/_c31.png',0); g=cv2.imread('euro/_r31.png',0)
gp=cv2.resize(gp,(g.shape[1],g.shape[0]))
bwp=(gp<200).astype(np.uint8); bw=(g<200).astype(np.uint8)
cl_=cv2.morphologyEx(bw,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))); white=1-cl_
n,lab,st,_=cv2.connectedComponentsWithStats(white,connectivity=4); dist=cv2.distanceTransform(white,cv2.DIST_L2,3)
H,W=g.shape; out=cl_.copy()
Kp=300/72; caixas=[(int((r.x0-R.x0)*Kp),int((r.y0-R.y0)*Kp),int((r.x1-R.x0)*Kp),int((r.y1-R.y0)*Kp)) for t,r,v in cs0]
for i in range(1,n):
    x,y,w,h,a=st[i]
    if x==0 or y==0 or x+w>=W or y+h>=H: continue
    m=lab==i
    if any(not (x+w<c[0] or x>c[2] or y+h<c[1] or y>c[3]) and m[max(0,c[1]):c[3],max(0,c[0]):c[2]].any() for c in caixas): continue   # região com número de cota = fora do perfil
    if a<=800 or dist[m].mean()<=7: out[m]=1
# paredes = regiões preenchidas + contorno encostado nelas; junta com o desenho já enxugado
cheio=(out>0)&(bw==0)
viz=cv2.dilate(cheio.astype(np.uint8),np.ones((7,7),np.uint8))>0
paredes=cheio|((bw>0)&viz)
s2=fitz.open('euro/_e31.svg'); P2=fitz.open('pdf',s2.convert_to_pdf()); P2[0].get_pixmap(dpi=300,colorspace=fitz.csGRAY).save('euro/_re31.png')
ge=cv2.imread('euro/_re31.png',0); ge=cv2.resize(ge,(W,H))
fim=paredes|(ge<200)
cv2.imwrite('euro/_p31.png',np.where(fim,0,255).astype(np.uint8))
cot=[(t,fitz.Rect(r)-(R.x0,R.y0,R.x0,R.y0),v) for t,r,v in cs]
C.padronizar_raster('euro/_p31.png','euro/ES-031.svg','euro/ES-031.png',dpi_img=300,cotas=cot)
