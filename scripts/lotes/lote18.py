# CM-067 = MAC-0693 (Geral Hera, pág. 37) — indicado pelo cliente em 25/11 18h
import fitz,sys,json
sys.path.insert(0,'/home/claude'); import cotas as C
f='hera_geral.pdf'; pg=37; nome='CM-067_MAC-0693'
p=fitz.open(f)[pg-1]; clip=fitz.Rect(40,580,290,725)
bb=fitz.Rect()
for x in p.get_drawings():
    r=x['rect']
    if clip.contains(r) and not (r.width>0.95*clip.width): bb|=r
for b in p.get_text('dict',clip=clip)['blocks']:
    for l in b.get('lines',[]):
        if C.NUM.match(''.join(s['text'] for s in l['spans']).strip()): bb|=fitz.Rect(l['bbox'])
R=(bb&clip)+(-3,-3,3,3)
p.get_pixmap(dpi=130,clip=R).save(f'lote18/o_{nome}.png')
lidas=C.ler_cotas(p,R)
cs,fs=C.padronizar(f,pg,R,f'lote18/{nome}.svg',f'lote18/{nome}.png',cotas=lidas,remover_texto=True,cinza_para_preto=True,setas=True,normalizar=True)
json.dump({nome:{'origem':f'Geral Hera pág. {pg}','peso_kg_m':'0,277','tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':{False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}.get(v,'inclinada')} for t,r,v in cs]}},open('lote18/_cotas.json','w'),ensure_ascii=False,indent=1)
print(nome,[round(v) for v in R],sorted(t for t,r,v in cs))
