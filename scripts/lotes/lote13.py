import sys,json;sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
def aperta(p,clip):
    bb=fitz.Rect()
    for x in p.get_drawings():
        r=x['rect']
        if clip.contains(r): bb|=r
    return (bb&clip)+(-3,-3,3,3)
f='up43/su043.pdf'; p=fitz.open(f)[0]
R=aperta(p,fitz.Rect(40,95,296,330)); print(R)
p.get_pixmap(dpi=130,clip=R).save('lote13/o_SU-043_TMS-043.png')
lidas=C.ler_cotas(p,R); print(sorted(t for t,r,v in lidas))
d=fitz.open(f); pg=d[0]
pg.add_redact_annot(pg.rect)
pg.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE, graphics=fitz.PDF_REDACT_LINE_ART_NONE, text=fitz.PDF_REDACT_TEXT_NONE)
# marca d'água vetorial rosada, se houver
d.save('lote13/tms_sem_img.pdf')
lidas=[(t,(fitz.Rect(r)+(0,0,0,3) if t=='22' and v else (fitz.Rect(r)+(0,0,3,0) if t=='22' else r)),v) for t,r,v in lidas]
print([(t,r,v) for t,r,v in lidas if t=='22'])
R=fitz.Rect(R.x0,R.y0,282.4,R.y1)
cs,fs=C.padronizar('lote13/tms_sem_img.pdf',1,R,'lote13/SU-043_TMS-043.svg','lote13/SU-043_TMS-043.png',cotas=lidas,apagar=[fitz.Rect(279.3,189.2,281.2,191.8)],setas=True,normalizar=True)
dados={'SU-043_TMS-043':{'origem':'Metal Centenário Linha TMS pág. 217 (PDF enviado pelo cliente)','peso_kg_m':'0,960','tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':{False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}.get(v,'inclinada')} for t,r,v in cs]}}
json.dump(dados,open('lote13/_cotas.json','w'),ensure_ascii=False,indent=1)
print(sorted(t for t,r,v in cs))
