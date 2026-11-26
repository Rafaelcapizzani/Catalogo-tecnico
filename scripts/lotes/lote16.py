# Perfis faltantes enviados pelo cliente em 25/11 15:57 (redesenhos vetoriais + FA-201 em imagem)
import sys,json,re,os; sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
U='/mnt/user-data/uploads/'; OUT='lote16'
fn=f'{OUT}/_cotas.json'; dados={}
def txtcotas(p,R):
    out=[]
    for b in p.get_text('dict',clip=R)['blocks']:
        for l in b.get('lines',[]):
            t=''.join(s['text'] for s in l['spans']).strip(); r=fitz.Rect(l['bbox'])
            if not re.match(r'^(\d|R\d|PASSO)',t) or C.NUM.match(t): continue   # números simples o padronizar já pega
            sz=l['spans'][0]['size']*0.716; dx,dy=l['dir']
            if abs(dx)>0.9: cy=(r.y0+r.y1)/2+r.height*0.05; rr=fitz.Rect(r.x0,cy-sz/2,r.x1,cy+sz/2); v=False
            else: cx=(r.x0+r.x1)/2; rr=fitz.Rect(cx-sz/2,r.y0,cx+sz/2,r.y1); v='up' if dy<0 else 'down'
            out.append((t.replace('.',','),rr,v))
    return out
J={'AP-050':('1d42f50e-AP-050.pdf',(200,200,372,630)),
   'AP-055':('225af015-AP-055_AP-054.pdf',(180,170,385,305)),
   'AP-054':('225af015-AP-055_AP-054.pdf',(180,425,385,558)),
   'AP-052_TRN-009':('e8afa452-TRN-009.pdf',(230,350,385,440)),
   'SU-048_ISU-048':('709cc81e-SU-048.pdf',(180,290,405,502)),
   '39-182':('76fc4211-39-182.pdf',(240,195,602,500))}
for nome,(f,clip) in J.items():
    R=fitz.Rect(clip); src=U+f; p=fitz.open(src)[0]
    p.get_pixmap(dpi=130,clip=R).save(f'{OUT}/o_{nome}.png')
    extra=txtcotas(p,R)
    if nome=='39-182':
        # números desenhados como contorno (vetor) + camada de texto invisível com lixo de OCR (A, 7, 1, J, V)
        t=fitz.open(); t.insert_pdf(fitz.open(src)); q=t[0]
        for b in q.get_text('dict')['blocks']:
            for l in b.get('lines',[]): q.add_redact_annot(l['bbox'])
        q.apply_redactions(images=0,graphics=0,text=0); src2=f'{OUT}/_39182.pdf'; t.save(src2)
        cot=[('153,0',fitz.Rect(244.5,337.6,263.5,343.4),False),('188,5',fitz.Rect(417.8,487.0,436.8,492.8),False)]
        cs,fs=C.padronizar(src2,1,R,f'{OUT}/{nome}.svg',f'{OUT}/{nome}.png',cotas=cot,setas=True,normalizar=True)
    else:
        cs,fs=C.padronizar(src,1,R,f'{OUT}/{nome}.svg',f'{OUT}/{nome}.png',cotas=extra,remover_texto=True,setas=True,normalizar=True)
    dados[nome]={'origem':f'{f[9:]} (PDF do cliente, 25/11)','tamanho_pt':round(fs,2),'cotas':[{'valor':t_.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':(f'inclinada {v[1]:.0f}°' if isinstance(v,tuple) else {False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}[v])} for t_,r,v in cs]}
    print(nome,sorted(t_ for t_,r,v in cs),flush=True)
json.dump(dados,open(fn,'w'),ensure_ascii=False,indent=1)
