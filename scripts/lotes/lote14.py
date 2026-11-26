import sys,json;sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
f='up72/dp072.pdf'
d=fitz.open(f); pg=d[0]
pg.add_redact_annot(pg.rect)
pg.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE, graphics=fitz.PDF_REDACT_LINE_ART_NONE, text=fitz.PDF_REDACT_TEXT_NONE)
d.save('lote14/dp_sem_img.pdf')
p=fitz.open('lote14/dp_sem_img.pdf')[0]
area=fitz.Rect(70,300,300,480)
bb=fitz.Rect()
for x in p.get_drawings():
    if area.contains(x['rect']): bb|=x['rect']
R=bb+(-3,-3,3,3); print(R)
fitz.open(f)[0].get_pixmap(dpi=130,clip=R).save('lote14/o_AP-069_DP-072.png')
lidas=C.ler_cotas(p,R); print(sorted(t for t,r,v in lidas))
cs,fs=C.padronizar('lote14/dp_sem_img.pdf',1,R,'lote14/AP-069_DP-072.svg','lote14/AP-069_DP-072.png',cotas=lidas,cinza_para_preto=True,setas=True,normalizar=True)
json.dump({'AP-069_DP-072':{'origem':'Decamp Portões pág. 15.9 (PDF enviado pelo cliente)','peso_kg_m':'0,290','tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':{False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}.get(v,'inclinada')} for t,r,v in cs]}},open('lote14/_cotas.json','w'),ensure_ascii=False,indent=1)
print(sorted(t for t,r,v in cs))
