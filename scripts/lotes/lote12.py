import sys,json;sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
def aperta(p,clip):
    bb=fitz.Rect()
    for x in p.get_drawings():
        r=x['rect']
        if clip.contains(r) and not (r.width>0.95*clip.width or r.height>0.97*clip.height and r.width<1): bb|=r
    return (bb&clip)+(-3,-3,3,3)
jobs={'DV-101':('tera.pdf',171,(55,460,280,690)),'DV-055':('tera.pdf',172,(50,160,280,260))}
EXTRA={'DV-101':[('35.5',fitz.Rect(256.5,571.3,276,579.2),False)],'DV-055':[('10.2',fitz.Rect(60,205,79,213),False)]}
dados={}
for nome,(f,pg,clip) in jobs.items():
    p=fitz.open(f)[pg-1]; R=aperta(p,fitz.Rect(clip))
    p.get_pixmap(dpi=130,clip=R).save(f'lote12/o_{nome}.png')
    lidas=C.ler_cotas(p,R)
    lidas=[z for z in lidas if not any(z[1].intersects(e[1]) for e in EXTRA[nome])]+EXTRA[nome]
    cs,fs=C.padronizar(f,pg,R,f'lote12/{nome}.svg',f'lote12/{nome}.png',cotas=lidas,remover_texto=True,cinza_para_preto=True,setas=True,normalizar=True)
    dados[nome]={'origem':f'Geral Tera pág. PDF {pg}','tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':(f'inclinada {v[1]:.0f}°' if isinstance(v,tuple) else {False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}[v])} for t,r,v in cs]}
    print(nome,[round(v) for v in R],sorted(t for t,r,v in cs))
json.dump(dados,open('lote12/_cotas.json','w'),ensure_ascii=False,indent=1)
