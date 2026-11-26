import fitz,sys,json,re
sys.path.insert(0,'/home/claude'); import cotas as C
from folha import folha
jobs={ # nome: (arquivo, página, clip aproximado, apertar?)
 'AP-046_CX-158':('tera.pdf',238,(195,500,405,672),True),
 'D-143_CX-085':('tera.pdf',135,(125,505,425,748),True),
 'TSL-009_DV-428':('tera.pdf',218,(345,170,548,350),True),
 'AP-047_A6-667':('imperio.pdf',52,(370,500,520,750),True),
 'AP-048_A6-230':('imperio.pdf',52,(372,175,520,398),True),
 'AP-049_A4-A-057':('imperio.pdf',51,(365,600,500,760),True),
 'T-734_CA-004':('lote10/ca004.pdf',1,(355,408,585,495),True),
 'TSL-002':('lote10/salalimpa.pdf',1,(40,628,300,800),True),
 'AP-1589_TMR-1589':('lote10/ap1589.pdf',1,(290,185,520,712),True),
 'AP-051_NX-4397':('lote10/brise.pdf',2,(150,395,470,515),True),
}
FIX={}
def aperta(p,clip):
    bb=fitz.Rect()
    for x in p.get_drawings():
        r=x['rect']
        if clip.contains(r) and not (r.width>0.95*clip.width or r.height>0.97*clip.height and r.width<1): bb|=r
    return (bb&clip)+(-3,-3,3,3)
dados={}
for nome,(f,pg,clip,ap) in jobs.items():
    p=fitz.open(f)[pg-1]; R=aperta(p,fitz.Rect(clip)) if ap else fitz.Rect(clip)
    p.get_pixmap(dpi=130,clip=R).save(f'lote10/o_{nome}.png')
    lidas=[(FIX.get((nome,t),t),r,v) for t,r,v in C.ler_cotas(p,R)]
    cs,fs=C.padronizar(f,pg,R,f'lote10/{nome}.svg',f'lote10/{nome}.png',cotas=lidas,remover_texto=True,setas=True,normalizar=True)
    dados[nome]={'origem':f'{f} pág. {pg}','tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':(f'inclinada {v[1]:.0f}°' if isinstance(v,tuple) else {False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}[v])} for t,r,v in cs]}
    print(nome,[round(v) for v in R],sorted(t for t,r,v in cs))
json.dump(dados,open('lote10/_cotas.json','w'),ensure_ascii=False,indent=1)
ks=list(jobs)
folha([(k,f'lote10/o_{k}.png',f'lote10/{k}.png') for k in ks[:5]],'lote10/conf1.png',larg=420)
folha([(k,f'lote10/o_{k}.png',f'lote10/{k}.png') for k in ks[5:]],'lote10/conf2.png',larg=420)
