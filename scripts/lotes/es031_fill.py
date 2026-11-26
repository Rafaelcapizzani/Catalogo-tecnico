import sys,json; sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
cl=json.load(open('euro/_clips.json')); pg,bb=cl['ES-031']; R=fitz.Rect(bb)
tmp='euro/tmp_ES-031.pdf'; d=fitz.open(tmp); q=d[0]
lid=C.ler_cotas(q,R)
cs,fs=C.padronizar(tmp,1,R,'euro/_v31.svg','euro/_v31.png',cotas=lid,cinza_para_preto=True,setas=True,normalizar=True)
# versão sem números, para preencher e vetorizar
C.padronizar(tmp,1,R,'euro/_n31.svg',None,cotas=lid,cinza_para_preto=True,setas=True,normalizar=False)
s=fitz.open('euro/_n31.svg'); pdfb=s.convert_to_pdf(); s2=fitz.open('pdf',pdfb)
print(s2[0].rect, R)
s=fitz.open('euro/_v31.svg'); P=fitz.open('pdf',s.convert_to_pdf())
P[0].get_pixmap(dpi=300,colorspace=fitz.csGRAY).save('euro/_r31.png')
C.preencher('euro/_r31.png','euro/_p31.png')
cot=[(t,fitz.Rect(r)-(R.x0,R.y0,R.x0,R.y0),v) for t,r,v in cs]
print(cot)
cs2,fs2=C.padronizar_raster('euro/_p31.png','euro/ES-031.svg','euro/ES-031.png',dpi_img=300,cotas=cot)
print(sorted(t for t,r,v in cs2))
