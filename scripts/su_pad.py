import sys,json,os,re
sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
SRC='/home/claude/alcoa/suprema.pdf'; OUT='/home/claude/alcoa/su/v1'
J=json.load(open('/home/claude/alcoa/su/jobs.json'))
sel=sys.argv[1:] or list(J)
D=fitz.open(SRC)
fn=f'{OUT}/_cotas.json'
dados=json.load(open(fn)) if os.path.exists(fn) else {}
for nome in sel:
    j=J[nome]; p=D[j['pdf']-1]; R=fitz.Rect(j['clip'])+(-1,-1,1,1)
    R={'SU-043':fitz.Rect(264,97,336,199)}.get(nome,R)
    p.get_pixmap(dpi=130,clip=R).save(f'{OUT}/o_{nome}.png')
    # peso lido no texto logo abaixo do código
    cr=[fitz.Rect(l['bbox']) for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) if ''.join(s['text'] for s in l['spans']).strip().replace(' ','')==j['cod']]
    pw=None
    for c0 in cr:
        for b in p.get_text('dict')['blocks']:
            for l in b.get('lines',[]):
                t=''.join(s['text'] for s in l['spans']).strip(); r=fitz.Rect(l['bbox'])
                if 'kg/m' in t and 0<r.y0-c0.y0<20 and abs(r.x0-c0.x0)<15: pw=t.replace('kg/m','').strip()
    cs,fs=C.padronizar(SRC,j['pdf'],R,f'{OUT}/{nome}.svg',f'{OUT}/{nome}.png',cotas=[],remover_texto=True,setas=True,normalizar=True,manter_rotulos=True,branco=[fitz.Rect(a) for a in j.get('branco',[])] or None,apagar=[fitz.Rect(a) for a in j['apagar']])
    dados[nome]={'origem':f"Suprema pág. PDF {j['pdf']}",'peso_kg_m':pw,'peso_planilha':j['peso'],'tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':(f'inclinada {v[1]:.0f}°' if isinstance(v,tuple) else {False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}[v])} for t,r,v in cs]}
    print(nome,j['pdf'],pw,j['peso'],sorted(t for t,r,v in cs),flush=True)
json.dump(dados,open(fn,'w'),ensure_ascii=False,indent=1)
