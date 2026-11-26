import sys,json,os
sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
CAT={'Gold III':'/home/claude/alcoa/gold3.pdf','Gold IV':'/home/claude/alcoa/gold4.pdf'}
OUT='/home/claude/alcoa/gold/v1'
J=json.load(open('/home/claude/alcoa/gold/jobs.json'))
sel=sys.argv[1:] or list(J)
BRANCO={'LG-026':[fitz.Rect(476,401.5,497,408)]}
REMOVER={'LG-026':[(439.1,404.7,479.2,439.7),(439.1,433.7,445.6,439.7),(479.2,404.7,493.5,404.7)]}   # LG-026: tirar seta e linha do raio (pedido do cliente)
fn=f'{OUT}/_cotas.json'; dados=json.load(open(fn)) if os.path.exists(fn) else {}
for nome in sel:
    j=J[nome]; SRC=CAT[j['cat']]; p=fitz.open(SRC)[j['pdf']-1]; R=fitz.Rect(j['clip'])+(-1,-1,1,1)
    p.get_pixmap(dpi=130,clip=R).save(f'{OUT}/o_{nome}.png')
    cs,fs=C.padronizar(SRC,j['pdf'],R,f'{OUT}/{nome}.svg',f'{OUT}/{nome}.png',cotas=[],remover_texto=True,setas=True,normalizar=True,manter_rotulos=True,cinza_para_preto=True,apagar=[fitz.Rect(a) for a in j['apagar']],remover=REMOVER.get(nome),branco=BRANCO.get(nome))
    dados[nome]={'origem':f"{j['cat']} pág. PDF {j['pdf']}",'peso_kg_m':j['peso_lido'],'tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':(f'inclinada {v[1]:.0f}°' if isinstance(v,tuple) else {False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}[v])} for t,r,v in cs]}
    print(nome,j['pdf'],sorted(t for t,r,v in cs),flush=True)
json.dump(dados,open(fn,'w'),ensure_ascii=False,indent=1)
