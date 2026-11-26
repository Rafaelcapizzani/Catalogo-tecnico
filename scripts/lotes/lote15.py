import sys,json;sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
f='up70/corrimao.pdf'; R=fitz.Rect(140,279,428,584)
fitz.open(f)[0].get_pixmap(dpi=130,clip=R).save('lote15/o_AP-070.png')
cs,fs=C.padronizar(f,1,R,'lote15/AP-070.svg','lote15/AP-070.png',cotas=[('5 ±0.16',fitz.Rect(268.2,513.5,298.5,519.9),False)],remover_texto=True,cinza_para_preto=True,setas=True,normalizar=True)
json.dump({'AP-070':{'origem':'Corrimão Edson (PDF enviado pelo cliente, 25/11), escala 1:1','peso_kg_m':None,'tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':{False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}.get(v,'inclinada')} for t,r,v in cs]}},open('lote15/_cotas.json','w'),ensure_ascii=False,indent=1)
print(sorted(t for t,r,v in cs),fs)
