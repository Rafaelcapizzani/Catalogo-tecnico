# STL-221 (AP-221) — PDF enviado pelo cliente em 25/11 19h10
import sys,json; sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
f='/mnt/user-data/uploads/e0cfe273-STL-221_AP-221.pdf'; nome='STL-221_AP-221'
p=fitz.open(f)[0]; clip=fitz.Rect(110,145,490,330)
bb=fitz.Rect()
for x in p.get_drawings():
    if clip.contains(x['rect']): bb|=x['rect']
for b in p.get_text('dict',clip=clip)['blocks']:
    for l in b.get('lines',[]): bb|=fitz.Rect(l['bbox'])
R=(bb&clip)+(-3,-3,3,3)
p.get_pixmap(dpi=130,clip=R).save(f'lote19/o_{nome}.png')
cs,fs=C.padronizar(f,1,R,f'lote19/{nome}.svg',f'lote19/{nome}.png',cotas=[],remover_texto=True,cinza_para_preto=True,setas=True,normalizar=True)
json.dump({nome:{'origem':'STL-221_AP-221.pdf (PDF do cliente, 25/11)','peso_kg_m':'0,510','tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':{False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}.get(v,'inclinada')} for t,r,v in cs]}},open('lote19/_cotas.json','w'),ensure_ascii=False,indent=1)
print(nome,[round(v) for v in R],sorted(t for t,r,v in cs))
