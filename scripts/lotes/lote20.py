# AP-6509 e AP-6510 (muxarabi) — PDF enviado pelo cliente em 25/11 19h38
import sys,json,re; sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
f='/mnt/user-data/uploads/059898ef-muxarabi_1.pdf'; p=fitz.open(f)[0]
J={'AP-6509':(325,140,470,320),'AP-6510':(325,400,425,505)}
dados={}
for nome,c in J.items():
    clip=fitz.Rect(c); bb=fitz.Rect()
    for x in p.get_drawings():
        if clip.contains(x['rect']): bb|=x['rect']
    for b in p.get_text('dict',clip=clip)['blocks']:
        for l in b.get('lines',[]):
            if re.match(r'^\d',''.join(s['text'] for s in l['spans']).strip()): bb|=fitz.Rect(l['bbox'])
    R=(bb&clip)+(-3,-3,3,3)
    p.get_pixmap(dpi=130,clip=R).save(f'lote20/o_{nome}.png')
    extra=[]
    for b in p.get_text('dict',clip=R)['blocks']:   # cota com tolerância (o número fica, a tolerância sai)
        for l in b.get('lines',[]):
            t=''.join(s['text'] for s in l['spans']).strip(); r=fitz.Rect(l['bbox'])
            if '±' in t:
                h=l['spans'][0]['size']*0.716; cy=(r.y0+r.y1)/2+r.height*0.05
                extra.append((t,fitz.Rect(r.x0,cy-h/2,r.x1,cy+h/2),False))
    cs,fs=C.padronizar(f,1,R,f'lote20/{nome}.svg',f'lote20/{nome}.png',cotas=extra,remover_texto=True,setas=True,normalizar=True)
    dados[nome]={'origem':'muxarabi_1.pdf (PDF do cliente, 25/11)','tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':{False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}.get(v,'inclinada')} for t,r,v in cs]}
    print(nome,[round(v) for v in R],sorted(t for t,r,v in cs))
json.dump(dados,open('lote20/_cotas.json','w'),ensure_ascii=False,indent=1)
