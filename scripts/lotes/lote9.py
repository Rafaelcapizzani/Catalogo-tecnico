import fitz,sys,json
sys.path.insert(0,'/home/claude'); import cotas as C
jobs={ # alplan: (arquivo, clip aproximado em pt, remover_texto)
 'LG-060_SI-330':('lote9/baguete.pdf',(88,632,258,735),False),
 'DV-105_DV-129':('lote9/divi.pdf',(300,345,545,480),False),
 'TSL-004':('lote9/salalimpa.pdf',(30,118,292,305),False),
 'TSL-006':('lote9/salalimpa.pdf',(300,143,592,305),False),
 '25-543':('lote9/25543.pdf',(140,612,580,805),False),
 'LG-570_MG32-126':('lote9/5planos.pdf',(232,95,398,735),False),
 'LG-572_MG32-127':('lote9/5planos.pdf',(405,95,560,735),False),
 'LG-571':('lote9/lg571.pdf',(195,80,470,800),True),
}
def aperta(p,clip):
    bb=fitz.Rect()
    for x in p.get_drawings():
        r=x['rect']
        if clip.contains(r) and not (r.width>0.95*clip.width or r.height>0.97*clip.height and r.width<1): bb|=r
    return (bb&clip)+(-3,-3,3,3)
dados={}
for nome,(f,clip,rt) in jobs.items():
    ap=[(30,105,135,146)] if nome=='TSL-004' else None
    d0=fitz.open(f); p=d0[0]
    if ap:
        for a in ap: p.add_redact_annot(fitz.Rect(a))
        p.apply_redactions(images=0,graphics=1,text=0)
    R=fitz.Rect(clip) if nome in ('LG-060_SI-330','DV-105_DV-129') else aperta(p,fitz.Rect(clip))
    p.get_pixmap(dpi=130,clip=R).save(f'lote9/o_{nome}.png')
    if rt:
        import re as _re
        for w in p.get_text('words',clip=fitz.Rect(clip)):
            if _re.fullmatch(r'[\d.,]+',w[4]): R|=fitz.Rect(w[:4])+(-3,-3,3,3)
    FIX={('LG-060_SI-330','50.4'):'30.4'}
    lidas=None if rt else [(FIX.get((nome,t),t),r,v) for t,r,v in C.ler_cotas(p,R)]
    cs,fs=C.padronizar(f,1,R,f'lote9/{nome}.svg',f'lote9/{nome}.png',remover_texto=rt,apagar=ap,cotas=lidas,setas=True,normalizar=True)
    dados[nome]={'origem':f,'tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':(f'inclinada {v[1]:.0f}°' if isinstance(v,tuple) else {False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}[v])} for t,r,v in cs]}
    print(nome,[round(v) for v in R],sorted(t for t,r,v in cs))
json.dump(dados,open('lote9/_cotas.json','w'),ensure_ascii=False,indent=1)
from folha import folha
ks=list(jobs)
folha([(k,f'lote9/o_{k}.png',f'lote9/{k}.png') for k in ks[:5]],'lote9/conf1.png',larg=420)
folha([(k,f'lote9/o_{k}.png',f'lote9/{k}.png') for k in ks[5:]],'lote9/conf2.png',larg=300)
