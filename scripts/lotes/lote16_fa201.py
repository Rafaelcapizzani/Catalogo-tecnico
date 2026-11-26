# FA-201 (imagem azul no PDF do cliente): perfil vetorizado da imagem; cotas redesenhadas no padrão a partir da geometria lida
import sys,json; sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C, numpy as np, cv2
src='/mnt/user-data/uploads/a669d6cb-fa-201.pdf'; p=fitz.open(src)[0]
R=fitz.Rect(268,80,575,262); OUT='lote16'; nome='AP-0201_FA-201'; DPI=300
p.get_pixmap(dpi=130,clip=R).save(f'{OUT}/o_{nome}.png')
pm=p.get_pixmap(dpi=DPI,clip=R); a=np.frombuffer(pm.samples,np.uint8).reshape(pm.height,pm.width,pm.n)[:,:,:3].astype(int)
r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
dark=(((b-r>40)&(r<170))|((r+g+b)/3<90)).astype(np.uint8)
grosso=cv2.morphologyEx(dark,cv2.MORPH_OPEN,np.ones((7,7),np.uint8))     # só as paredes do perfil (linhas de cota finas saem)
cv2.imwrite(f'{OUT}/_fa201.png',np.where(grosso>0,0,255).astype(np.uint8))
# geometria (pt da página, medida na imagem): esquerda 311,2 · degrau 423,8 · parede direita 499,2 · fim da aba 543,3 · topo 120,6 · base 240,2 · topo da parte baixa 179,1
X=lambda x: x-R.x0; Y=lambda y: y-R.y0
FS=6.2; cot=[]
def extra(q,fs):
    cot.append(C.cota_manual(q,'H',X(311.2),X(423.8),Y(94.3),'55',fs,ch_a=Y(120.6),ch_b=Y(120.6)))
    cot.append(C.cota_manual(q,'H',X(423.8),X(499.2),Y(94.3),'37',fs,ch_a=None,ch_b=Y(179.1)))
    cot.append(C.cota_manual(q,'H',X(311.2),X(543.3),Y(254.1),'113',fs,ch_a=Y(240.2),ch_b=Y(240.2),lado=1))
    cot.append(C.cota_manual(q,'V',Y(120.6),Y(240.2),X(280.5),'58,5',fs,ch_a=X(311.2),ch_b=X(311.2)))
    cot.append(C.cota_manual(q,'V',Y(179.1),Y(240.2),X(561.6),'30',fs,ch_a=X(499.2),ch_b=X(543.3),lado=1))
    for t,rr,v in cot:   # número na leitura normal
        s=t; tw=C._font.text_length(s,fs); cx,cy=(rr.x0+rr.x1)/2,(rr.y0+rr.y1)/2
        if v is False: q.insert_text((cx-tw/2,cy+C.CAP*fs/2),s,fontsize=fs,fontname='bahn',fontfile=C.FONT)
        else: q.insert_text((cx+C.CAP*fs/2,cy+tw/2),s,fontsize=fs,fontname='bahn',fontfile=C.FONT,rotate=90)
cs,fs=C.padronizar_raster(f'{OUT}/_fa201.png',f'{OUT}/{nome}.svg',f'{OUT}/{nome}.png',dpi_img=DPI,cotas=[],extra=extra,fs=FS)
D=json.load(open(f'{OUT}/_cotas.json'))
D[nome]={'origem':'fa-201.pdf (PDF do cliente, 25/11; desenho em imagem, vetorizado; cotas redesenhadas)','peso_kg_m':'1,795','tamanho_pt':FS,'cotas':[{'valor':t,'x':round((q.x0+q.x1)/2,2),'y':round((q.y0+q.y1)/2,2),'direcao':'horizontal' if v is False else 'vertical (baixo→cima)'} for t,q,v in cot]}
json.dump(D,open(f'{OUT}/_cotas.json','w'),ensure_ascii=False,indent=1)
print([t for t,q,v in cot])
