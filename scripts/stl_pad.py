import sys,json,os
sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
CAT={'Geral Stelman':'/home/claude/alcoa/stelman.pdf'}
OUT='/home/claude/alcoa/stl/v1'
J=json.load(open('/home/claude/alcoa/stl/jobs.json'))
sel=sys.argv[1:] or list(J)
EXTRA={'CM-005':[('24.0',(467.3,453.8,489.2,462.4),False)],'CM-064':[('24.0',(199.8,422.9,221.6,431.3),False)],'CM-001_E-494':[('26.3',(521.5,181.8,543.6,190.4),False)],'CL-017':[('17.0',(61.4,698,82.6,706.6),False)]}
CLIPFIX={'CL-017':(58,636.4,255.2,729.9)}
BRANCO={'LG-026':[fitz.Rect(476,401.5,497,408)]}
REMOVER={'LG-026':[(439.1,404.7,479.2,439.7),(439.1,433.7,445.6,439.7),(479.2,404.7,493.5,404.7)]}   # LG-026: tirar seta e linha do raio (pedido do cliente)
fn=f'{OUT}/_cotas.json'; dados=json.load(open(fn)) if os.path.exists(fn) else {}
for nome in sel:
    j=J[nome]; SRC=CAT[j['cat']]; p=fitz.open(SRC)[j['pdf']-1]; R=fitz.Rect(CLIPFIX.get(nome,j['clip']))+(-1,-1,1,1)
    p.get_pixmap(dpi=130,clip=R).save(f'{OUT}/o_{nome}.png')
    lid=C.ler_cotas(p,R,dpi=400)
    tri=[d['rect'] for d in p.get_drawings() if d.get('fill') and R.intersects(d['rect']) and len(d['items'])<=4 and max(d['rect'].width,d['rect'].height)<9]
    lid=[(t,r,v) for t,r,v in lid if not (len(t.replace('.',''))==1 and any(r.intersects(q) for q in tri))]
    lid+=[(t,fitz.Rect(*rr),v) for t,rr,v in EXTRA.get(nome,[]) if not any(fitz.Rect(*rr).intersects(z[1]) for z in lid)]
    cs,fs=C.padronizar(SRC,j['pdf'],R,f'{OUT}/{nome}.svg',f'{OUT}/{nome}.png',cotas=lid,remover_texto=True,manter_rotulos=True,cinza_para_preto=True,setas=True,normalizar=True,apagar=[fitz.Rect(a) for a in j['apagar']],remover=REMOVER.get(nome),branco=BRANCO.get(nome))
    dados[nome]={'origem':f"{j['cat']} pág. PDF {j['pdf']}",'peso_kg_m':j['peso_lido'],'tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':(f'inclinada {v[1]:.0f}°' if isinstance(v,tuple) else {False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}[v])} for t,r,v in cs]}
    print(nome,j['pdf'],sorted(t for t,r,v in cs),flush=True)
json.dump(dados,open(fn,'w'),ensure_ascii=False,indent=1)
