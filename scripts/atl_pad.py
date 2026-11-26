import sys,json,os
sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
SRC='/home/claude/alcoa/atlanta.pdf'; OUT='/home/claude/alcoa/atl/v1'
J=json.load(open('/home/claude/alcoa/atl/jobs.json'))
sel=sys.argv[1:] or list(J)
fn=f'{OUT}/_cotas.json'; dados=json.load(open(fn)) if os.path.exists(fn) else {}
for nome in sel:
    j=J[nome]; R=fitz.Rect(j['clip'])
    if R.width<10: continue
    p=fitz.open(SRC)[j['pdf']-1]
    p.get_pixmap(dpi=130,clip=R).save(f'{OUT}/o_{nome}.png')
    # triângulos/fundos cinza decorativos da página
    rem=[list(d['rect']) for d in p.get_drawings() if d.get('fill') and min(d['fill'])>0.6 and max(d['fill'])<0.97 and R.intersects(d['rect']) and max(d['rect'].width,d['rect'].height)>40]
    cs,fs=C.padronizar(SRC,j['pdf'],R,f'{OUT}/{nome}.svg',f'{OUT}/{nome}.png',cotas=[],remover_texto=True,manter_rotulos=True,cinza_para_preto=True,setas=True,normalizar=True,remover=rem or None,enxugar=True)
    dados[nome]={'origem':f"Belmetal Atlanta pág. PDF {j['pdf']}",'peso_kg_m':j['peso_lido'],'tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':(f'inclinada {v[1]:.0f}°' if isinstance(v,tuple) else {False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}[v])} for t,r,v in cs]}
    print(nome,j['pdf'],len(rem),sorted(t for t,r,v in cs),flush=True)
json.dump(dados,open(fn,'w'),ensure_ascii=False,indent=1)
