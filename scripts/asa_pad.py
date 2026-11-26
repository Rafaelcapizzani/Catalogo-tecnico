import sys,json,os,re
sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
SRC='/home/claude/alcoa/asa.pdf'; OUT='/home/claude/alcoa/asa/v1'
J=json.load(open('/home/claude/alcoa/asa/jobs.json'))
sel=sys.argv[1:] or list(J)
D=fitz.open(SRC)
fn=f'{OUT}/_cotas.json'
dados=json.load(open(fn)) if os.path.exists(fn) else {}
for nome in sel:
    j=J[nome]; p=D[j['pdf']-1]; R=fitz.Rect(j['clip'])+(-1,-1,1,1)
    p.get_pixmap(dpi=130,clip=R).save(f'{OUT}/o_{nome}.png')
    pw=j.get('peso_lido')
    if j.get('imgs'):
        # desenho em imagem: tira textos/rótulos, rasteriza o recorte e vetoriza (potrace); cotas vêm do texto do PDF
        tmpd=fitz.open(SRC); tp=tmpd[j['pdf']-1]
        cot=[]
        for b in tp.get_text('dict')['blocks']:
            for l in b.get('lines',[]):
                t=''.join(s['text'] for s in l['spans']).strip(); r=fitz.Rect(l['bbox'])
                if R.intersects(r):
                    if C.NUM.match(t):
                        h=r.height*0.62; cy=(r.y0+r.y1)/2+r.height*0.05
                        rr=fitz.Rect(r.x0,cy-h/2,r.x1,cy+h/2)-(R.x0,R.y0,R.x0,R.y0)
                        cot.append((t,rr,False if abs(l['dir'][0])>0.9 else ('up' if l['dir'][1]<0 else 'down')))
                    tp.add_redact_annot(r)
        for a in j['apagar']: tp.add_redact_annot(fitz.Rect(a))
        tp.apply_redactions(images=0,graphics=1,text=0)
        tp.get_pixmap(dpi=600,clip=R,colorspace=fitz.csGRAY).save(f'{OUT}/_r_{nome}.png')
        cs,fs=C.padronizar_raster(f'{OUT}/_r_{nome}.png',f'{OUT}/{nome}.svg',f'{OUT}/{nome}.png',dpi_img=600,cotas=cot)
        cs=[(t,r+(R.x0,R.y0,R.x0,R.y0),v) for t,r,v in cs]
    else:
      cs,fs=C.padronizar(SRC,j['pdf'],R,f'{OUT}/{nome}.svg',f'{OUT}/{nome}.png',cotas=[],remover_texto=True,setas=True,normalizar=True,manter_rotulos=True,apagar=[fitz.Rect(a) for a in j['apagar']])
    dados[nome]={'origem':f"Geral ASA pág. PDF {j['pdf']}",'peso_kg_m':pw,'peso_planilha':j['peso'],'tamanho_pt':round(fs,2),'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':(f'inclinada {v[1]:.0f}°' if isinstance(v,tuple) else {False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}[v])} for t,r,v in cs]}
    print(nome,j['pdf'],pw,j['peso'],sorted(t for t,r,v in cs),flush=True)
json.dump(dados,open(fn,'w'),ensure_ascii=False,indent=1)
