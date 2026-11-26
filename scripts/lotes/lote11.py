import fitz,sys,json
sys.path.insert(0,'/home/claude'); import cotas as C
from folha import folha
jobs={
 'AP-020_MAC-0234':('hera_geral.pdf',138,(55,480,275,712),True,(58,495,262,712)),
 'AP-021_MAC-0235':('hera_geral.pdf',138,(370,490,520,712),True,(395,500,505,705)),
 'BX-018_STL-049':('stelman.pdf',30,(55,395,265,520),False,(70,400,275,515)),
 'BX-019_STL-046A':('stelman.pdf',30,(40,125,280,315),False),
 'BX-020_STL-052':('stelman.pdf',30,(80,612,240,735),False,(90,620,232,745)),
 'BX-021_STL-048':('stelman.pdf',30,(325,125,560,265),False),
 'BX-022_STL-053':('stelman.pdf',30,(365,365,520,525),False),
 'BX-039_A6-L-006':('imperio.pdf',178,(70,155,230,300),False,(72,170,215,300)),
}
def aperta(p,clip):
    bb=fitz.Rect()
    for x in p.get_drawings():
        r=x['rect']
        if clip.contains(r) and not (r.width>0.95*clip.width or r.height>0.97*clip.height and r.width<1): bb|=r
    return (bb&clip)+(-3,-3,3,3)
dados={}
for nome,(f,pg,clip,cinza,*fixo) in jobs.items():
    p=fitz.open(f)[pg-1]; R=fitz.Rect(fixo[0]) if fixo else aperta(p,fitz.Rect(clip))
    p.get_pixmap(dpi=130,clip=R).save(f'lote11/o_{nome}.png')
    lidas=C.ler_cotas(p,R)
    cs,fs=C.padronizar(f,pg,R,f'lote11/{nome}.svg',f'lote11/{nome}.png',cotas=lidas,remover_texto=True,cinza_para_preto=cinza,setas=True,normalizar=True)
    dados[nome]={'origem':f'{f} pág. {pg}','tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':(f'inclinada {v[1]:.0f}°' if isinstance(v,tuple) else {False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}[v])} for t,r,v in cs]}
    print(nome,[round(v) for v in R],sorted(t for t,r,v in cs))
json.dump(dados,open('lote11/_cotas.json','w'),ensure_ascii=False,indent=1)
ks=list(jobs)
folha([(k,f'lote11/o_{k}.png',f'lote11/{k}.png') for k in ks[:4]],'lote11-conferencia-1.png',larg=420)
folha([(k,f'lote11/o_{k}.png',f'lote11/{k}.png') for k in ks[4:]],'lote11-conferencia-2.png',larg=420)
