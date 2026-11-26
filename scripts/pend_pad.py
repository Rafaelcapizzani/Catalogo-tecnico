import sys,json,os,re
sys.path.insert(0,'/home/claude')
import pymupdf as fitz, cotas as C
OUT='/home/claude/alcoa/pend/v1'; os.makedirs(OUT,exist_ok=True)
J=json.load(open('/home/claude/alcoa/pend/jobs.json'))
sel=sys.argv[1:] or list(J)
fn=f'{OUT}/_cotas.json'; dados=json.load(open(fn)) if os.path.exists(fn) else {}
IMG={'Geral Alumil','Maximus 20 (Stelman)','Específica 3.2 (OCR)'}
def sem_marca(src,pg):
    # Decamp: a marca d'água vem num bloco de conteúdo opcional (/OC ... BDC ... EMC) só com cor saturada.
    # Remover pela redação reescreve o perfil e perde o preenchimento par-ímpar (câmaras ficavam pretas).
    d=fitz.open(src); p=d[pg-1]; p.clean_contents(); c=p.read_contents().decode('latin1'); cort=[]
    for m in re.finditer(r'/OC/\w+ BDC',c):
        i=m.end(); n=1; j=None
        for t in re.finditer(r'\bBDC\b|\bBMC\b|\bEMC\b',c[i:]):
            n+= -1 if t.group()=='EMC' else 1
            if n==0: j=i+t.end(); break
        if j is None: continue
        cores=[tuple(map(float,x)) for x in re.findall(r'(?<![\d.])([\d.]+) ([\d.]+) ([\d.]+) scn',c[m.start():j])]
        if len(c[m.start():j])>50000 and cores and all(max(k)-min(k)>0.3 for k in cores): cort.append((m.start(),j))
    if not cort: return src,pg
    for a,b in reversed(cort): c=c[:a]+c[b:]
    n=fitz.open(); n.insert_pdf(d,from_page=pg-1,to_page=pg-1); q=n[0]
    n.update_stream(q.get_contents()[0],c.encode('latin1'))
    for x in q.get_contents()[1:]: n.update_stream(x,b'')
    fn=f'/tmp/semmarca_{os.path.basename(src)}_{pg}.pdf'; n.save(fn); return fn,1
for nome in sel:
    j=J[nome]; R=fitz.Rect(j['clip']); src,pg=sem_marca(j['pdf'],j['pg']) if 'Decamp' in j['cat'] else (j['pdf'],j['pg']); p=fitz.open(src)[pg-1]
    p.get_pixmap(dpi=130,clip=R).save(f'{OUT}/o_{nome}.png')
    A=R.width*R.height; rem=[]
    escuros0=[d['rect'] for d in p.get_drawings() if d.get('fill') and max(d['fill'])<0.35 and R.intersects(d['rect'])]
    for d in p.get_drawings():
        r=d['rect']; f=d.get('fill'); c=d.get('color')
        if not f or not R.intersects(r): continue
        if c and max(c)<0.3: continue
        if max(f)-min(f)>0.3 and r.width*r.height>0.5*A and not (c and max(c)<0.5): rem.append(list(r)); continue   # marca d'água colorida (Decamp)
        if max(f)-min(f)>0.15 and not R.contains(r): rem.append(list(r)); continue   # faixa colorida de cabeçalho cortada pela borda
        claro=0.6<min(f)<0.97   # branco puro fica (câmara/máscara do perfil)
        colorido=max(f)-min(f)>(0.07 if claro else 0.1)
        if claro and not colorido and any(q.contains(r) for q in escuros0): continue   # câmara clara (cinza neutro) dentro do perfil: fica
        if claro and (r.width*r.height>0.25*A or (colorido and max(r.width,r.height)>8)): rem.append(list(r))   # painéis, degradês e marcas d'água
    if j.get('sem_cinza'):   # peça de referência em cinza (ex. baguete) + chamada: sai, a pedido do cliente
        for d in p.get_drawings():
            c=d.get('fill') or d.get('color')
            if c and R.intersects(d['rect']) and 0.4<min(c) and max(c)<0.85 and max(c)-min(c)<0.08: rem.append(list(d['rect']))
    if 'Integrada' in j['cat']:   # linhas tracejadas (peça vizinha) saem, a pedido do cliente
        rem+=[list(d['rect']) for d in p.get_drawings() if R.intersects(d['rect']) and d.get('dashes') and not d['dashes'].startswith('[]')]
    rem+=j.get('rem',[])   # desenho específico a tirar (caixa de rótulo cinza que viraria preta)
    for a in j.get('apagar',[]):   # contorno de caixa de rótulo que a redação não tira
        rem+=[list(d['rect']) for d in p.get_drawings() if fitz.Rect(a).contains(d['rect']) and d.get('color') and not d.get('fill')]
    # Tera: perfil já é preto e as peças de referência (vizinhas) vêm em cinza -> não converter o cinza
    escuros=[d for d in p.get_drawings() if d.get('fill') and max(d['fill'])<0.15 and R.intersects(d['rect']) and d['rect'].width*d['rect'].height>0.02*A]
    cinza=not ('Tera' in j['cat'] and escuros)
    kgl=[fitz.Rect(l['bbox']) for b in p.get_text('dict',clip=R)['blocks'] for l in b.get('lines',[]) if re.search(r'kg',''.join(sp['text'] for sp in l['spans']),re.I)]   # linha de peso (0,624 kg/m) não é cota
    nums=[w for w in p.get_text('words',clip=R) if not any(fitz.Rect(w[:4]).intersects(q) for q in kgl) and re.match(r'^[\d.,]+$',w[4]) and not re.match(r'^0\d',w[4]) and not any(fitz.Rect(a).intersects(fitz.Rect(w[:4])) for a in j.get('apagar',[]))]
    cot=[] if nums else None
    if cot is not None: cot=[(t,fitz.Rect(r),v) for t,r,v in j.get('add',[])]   # cota que o texto do PDF traz quebrada
    if cot is None:   # OCR: "11.98" às vezes sai como "11" e "98" (ponto pequeno some) -> junta com vírgula
        lid=[]; extra=set()   # extra: 1 algarismo lido só em outra resolução (seta vira '4'): só vale se juntar com vizinho
        for dpi in (300,400,250):   # a leitura muda com a resolução: junta as três, fica com o texto mais longo em cada lugar
            for t,r,v in C.ler_cotas(p,R,dpi=dpi):
                o=[i for i,x in enumerate(lid) if x for (t0,r0,v0) in [x] if (r0&r).get_area()>0.3*min(r0.get_area(),r.get_area())]
                if not o: lid.append((t,r,v)); extra.add(len(lid)-1) if dpi!=300 and len(re.sub(r'\D','',t))<2 else None
                elif len(re.sub(r'\D','',t))>max(len(re.sub(r'\D','',lid[i][0])) for i in o):   # leitura mais completa substitui todas as que ela cobre
                    lid[o[0]]=(t,r,v)
                    for i in o[1:]: lid[i]=None
        usados=set(); cot=[]
        for i,x in enumerate(lid):
            if x is None or i in usados: continue
            t,r,v=x
            juntou=False
            for k2,x2 in enumerate(lid):
                if x2 is None: continue
                t2,r2,v2=x2
                if k2<=i or k2 in usados or v or v2: continue
                h=max(r.height,r2.height)
                if re.match(r'^\d+$',t) and re.match(r'^[.,]?\d{1,2}$',t2) and abs((r.y0+r.y1)/2-(r2.y0+r2.y1)/2)<0.3*h and (0.15*h if t2[0].isdigit() else -0.3*h)<r2.x0-r.x1<1.2*h:
                    t=t+','+t2.lstrip('.,'); r=r|r2; usados.add(k2); juntou=True
            if i in extra and not juntou: continue
            t=re.sub(r'\s','',t); t=j.get('fix',{}).get(t,t)   # correções de leitura conferidas no original
            if t: cot.append((t,r,v))   # fix com '' = descartar (pedaço de rótulo)
        cot+=[(t,fitz.Rect(r),(v[0],v[1],tuple(v[2]),v[3],v[4]) if isinstance(v,list) else v) for t,r,v in j.get('add',[])]   # cota que a leitura não achou (conferida no original)
        if len(cot)>=3:   # ponta de seta lida como '7'/'1': altura bem menor que a dos números de verdade
            hs=sorted(min(r.width,r.height) for t,r,v in cot); hm=hs[len(hs)//2]
            cot=[(t,r,v) for t,r,v in cot if min(r.width,r.height)>=0.6*hm]
    try:
        cs,fs=C.padronizar(src,pg,R,f'{OUT}/{nome}.svg',f'{OUT}/{nome}.png',cotas=cot,remover_texto=True,manter_rotulos=False,cinza_para_preto=cinza,
            setas=True,normalizar=True,remover=rem or None,apagar=[fitz.Rect(a) for a in j.get('apagar',[])] or None,
            encher='Integrada' in j['cat'],sem_imagens=j['cat'] in IMG,apagar_num=len(j.get('apagar',[])) or 1,branco=j.get('branco'),costura=j.get('costura',False))
    except Exception as e:
        print('ERRO',nome,e); continue
    dados[nome]={'origem':f"{j['cat']} pág. PDF {j['pg']}",'codigo_catalogo':j['cc'],'peso_kg_m':j['peso'],'tamanho_pt':round(fs,2),
        'cotas':[{'valor':t.replace('.',','),'x':round((r.x0+r.x1)/2-R.x0,2),'y':round((r.y0+r.y1)/2-R.y0,2),'direcao':{False:'horizontal','up':'vertical (baixo→cima)','down':'vertical (cima→baixo)'}.get(v,'inclinada')} for t,r,v in cs]}
    print(nome,len(rem),'txt' if nums else 'ocr',sorted(t for t,r,v in cs),flush=True)
json.dump(dados,open(fn,'w'),ensure_ascii=False,indent=1)
if 'LG-129E' in sel:   # frestas das tiras: rasteriza, fecha e vetoriza
    import subprocess; subprocess.run(['python3','-W','ignore','/home/claude/lg129e_post.py'],check=True)
