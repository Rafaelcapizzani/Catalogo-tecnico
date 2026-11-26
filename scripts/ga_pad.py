import sys,json,os
sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C, dig_alcoa as A
from folha import folha
J=json.load(open('/home/claude/alcoa/ga/jobs.json'))
sel=sys.argv[1:] or list(J)
OUT='/home/claude/alcoa/ga/v1'; os.makedirs(OUT,exist_ok=True)
D=fitz.open('/home/claude/alcoa/geral.pdf')
dados=json.load(open(f'{OUT}/_cotas.json')) if os.path.exists(f'{OUT}/_cotas.json') else {}
for nome in sel:
    j=J[nome]; p=D[j['pdf']-1]; R=fitz.Rect(j['clip'])+(-1,-1,1,1)
    import ga_manual as GM
    MAN=GM.M.get(nome)
    if MAN:
        MAN=dict(dict(c=None,a=[],add=[],fix={},clip=None),**MAN)
        j=dict(j); j['apagar']=list(j['apagar'])+[list(a) for a in MAN['a']]
        if MAN['clip']: R=fitz.Rect(MAN['clip'])
    p.get_pixmap(dpi=130,clip=R).save(f'{OUT}/o_{nome}.png')
    AP=[fitz.Rect(a) for a in j['apagar']]
    lidas=[(t,r,h) for t,r,h,sc in A.ler(p,R) if not any(r.intersects(a) for a in AP)]
    # complementa com o OCR da página (fonte monoespaçada / ponto afastado)
    import re as _re, ga_seg as G
    for w in G.tsv(j['pdf']):
        tx=w[0].replace('Ø','0').replace('O','0').replace(',','.')
        if not _re.match(r'^\d{1,4}(\.\d{1,2})?$',tx) or w[5]<55: continue
        wr=fitz.Rect(w[1]*G.S,w[2]*G.S,(w[1]+w[3])*G.S,(w[2]+w[4])*G.S)
        if not R.contains(wr) or any(wr.intersects(a) for a in AP) or wr.height>wr.width*1.6 and len(tx)>1: continue
        cov=[z for z in lidas if z[1].intersects(wr)]
        if not cov: lidas.append((tx,wr,False))
        elif all(z[2] is False for z in cov):
            dig=''.join(z[0] for z in sorted(cov,key=lambda z:z[1].x0)).replace('.','')
            if (dig==tx.replace('.','') and (len(cov)>=2 or '.' in tx) and ('.' in tx or not any('.' in z[0] for z in cov))) or (len(cov)==1 and '.' in tx and tx.replace('.','').startswith(dig) and '.' not in cov[0][0]):
                rr=fitz.Rect(wr)
                for z in cov: rr|=z[1]; lidas.remove(z)
                lidas.append((tx,rr,False))
    if MAN:
        if MAN['c']: lidas=[(t,fitz.Rect(x0,y0,x1,y1),False) for t,x0,y0,x1,y1 in MAN['c']]
        lidas=[(MAN['fix'].get(t,t),r,h) for t,r,h in lidas if R.intersects(r)]+[(t,fitz.Rect(x0,y0,x1,y1),False) for t,x0,y0,x1,y1 in MAN['add']]
    cs,fs=C.padronizar('/home/claude/alcoa/geral.pdf',j['pdf'],R,f'{OUT}/{nome}.svg',f'{OUT}/{nome}.png',cotas=lidas,remover_texto=True,setas=True,normalizar=True,solidificar=True,branco=([fitz.Rect(a) for a in MAN['a']] if MAN and MAN['a'] else None),apagar=[fitz.Rect(a) for a in j['apagar']])
    dados[nome]={'origem':f"Geral Alcoa pág. PDF {j['pdf']}",'peso_kg_m':j['peso'],'tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':(f'inclinada {v[1]:.0f}°' if isinstance(v,tuple) else {False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}[v])} for t,r,v in cs]}
    print(nome,j['pdf'],sorted(t for t,r,v in cs),flush=True)
json.dump(dados,open(f'{OUT}/_cotas.json','w'),ensure_ascii=False,indent=1)
