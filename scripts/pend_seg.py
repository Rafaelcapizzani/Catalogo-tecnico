# Segmentação genérica para os catálogos restantes: acha o rótulo do perfil na página e o grupo de desenhos mais próximo.
import sys,json,re
sys.path.insert(0,'/home/claude')
import pymupdf as fitz
U='/mnt/user-data/uploads/'; A='/home/claude/alcoa/'
PDF={'Geral Decamp':A+'decamp.pdf','SP20 Selta':A+'sp20.pdf','Geral Tera (OCR)':A+'tera.pdf','Geral Tera':A+'tera.pdf','Suprema Integrada':A+'integrada.pdf',
 'Geral Novaxx (OCR)':A+'novaxx.pdf','Geral Alumil':A+'alumil.pdf','Geral Império':A+'imperio.pdf','Novaxx Luxxor 2.5':A+'luxxor.pdf','Específica 3.2 (OCR)':A+'especifica.pdf',
 'Geral Hera':A+'hera_geral.pdf','Linha Gradil':A+'gradil.pdf','Geral Hyspex':A+'hyspex.pdf','Maximus 20 (Stelman)':A+'maximus.pdf','Sapa (Box padronizados)':U+'2b77edf3-sapa_420307.pdf',
 'Linha Portão II':A+'portao2.pdf','Nylkit (Perfis vitrine)':U+'28dcf9fd-Nylkit.pdf','Nylkit Perfis vitrine (ED03)':U+'a83974e6-ED03.PDF.pdf','Metal Centenário (Linha TMS)':U+'b10569c3-Centenario.pdf',
 'Binkafer (Linha 25 a 90°)':U+'64407a12-Binkafer.pdf','Alumax (Linha Suprema)':U+'a05eee7b-Alumax.pdf','Nylkit (Suprema)':U+'28dcf9fd-Nylkit.pdf'}
def variantes(c):
    c=re.sub(r'\s*\(.*\)','',str(c)).strip(); out={c}
    out|={c.replace('-',''),c.replace('-',' '),c.replace(' ',''),c.replace(' ','-'),c.replace('.',''),c.replace('-','.')}
    m=re.match(r'^([A-Z]+)(\d+)$',c)
    if m: out.add(m.group(1)+'-'+m.group(2)); out.add(m.group(1)+' '+m.group(2))
    return [v for v in out if len(v)>=3]
def rotulo(p,cod):
    best=None
    for v in sorted(variantes(cod),key=len,reverse=True):
        for r in p.search_for(v):
            # palavra inteira
            ws=[w for w in p.get_text('words',clip=r+(-1,-1,1,1))]
            txt=''.join(w[4] for w in ws)
            if not best: best=r
            return r
    return best
def rotulo_ocr(p,cod):
    import pytesseract,io
    from PIL import Image
    alvo=re.sub(r'[^A-Z0-9]','',re.sub(r'\s*\(.*\)','',str(cod)).upper())
    Z=250/72; pm=p.get_pixmap(dpi=250,colorspace=fitz.csGRAY); im=Image.open(io.BytesIO(pm.tobytes('png')))
    d=pytesseract.image_to_data(im,config='--psm 11',output_type=pytesseract.Output.DICT)
    W=[(re.sub(r'[^A-Z0-9]','',t.upper().replace('O','0') if False else t.upper()),d['left'][i],d['top'][i],d['width'][i],d['height'][i]) for i,t in enumerate(d['text']) if t.strip()]
    def fix(s): return s.replace('O','0') if re.search(r'\d',s) else s
    for i,(t,x,y,w,h) in enumerate(W):
        for k in range(1,4):
            seq=W[i:i+k]; jt=''.join(fix(q[0]) for q in seq)
            if jt==alvo or (len(alvo)>=5 and jt.endswith(alvo)):
                x0=min(q[1] for q in seq); y0=min(q[2] for q in seq); x1=max(q[1]+q[3] for q in seq); y1=max(q[2]+q[4] for q in seq)
                return fitz.Rect(x0/Z,y0/Z,x1/Z,y1/Z)
    return None
def moldura(d):
    r=d['rect']
    if min(r.width,r.height)<25: return False
    if d.get('fill') and max(d['fill'])<0.9: return False
    pts=[]
    for it in d['items']:
        if it[0]=='re': return True
        for q in it[1:]:
            if isinstance(q,fitz.Point): pts.append(q)
    if not pts: return False
    tol=max(4,0.06*min(r.width,r.height))
    return all(min(abs(q.x-r.x0),abs(q.x-r.x1),abs(q.y-r.y0),abs(q.y-r.y1))<tol for q in pts)
def grupos(p,ign=()):
    pr=p.rect; D=[]; M=[]
    for d in p.get_drawings():
        r=d['rect']
        if r.width>0.8*pr.width or r.height>0.8*pr.height: continue
        if d.get('fill') and min(d['fill'])>0.9 and not d.get('color'): continue   # fundos brancos
        if d.get('fill') and not d.get('color') and r.width*r.height>0.15*pr.width*pr.height: continue
        if moldura(d): continue
        if d.get('fill') and min(d['fill'])>0.78 and r.width*r.height>4000 and not (d.get('color') and max(d['color'])<0.3): continue   # painéis de fundo claros
        cor=d.get('fill') or d.get('color')
        if cor and max(cor)-min(cor)>0.15: continue                      # logos, marcas d'água e rótulos coloridos
        if d.get('fill') and len(d['items'])<=4 and all(it[0] in ('re','l') for it in d['items']) and r.width>40 and r.height<40 and r.width*r.height>600: continue   # faixas de título
        D.append(fitz.Rect(r.x0,r.y0,max(r.x1,r.x0+0.1),max(r.y1,r.y0+0.1))); M.append(d)
    n=len(D); pai=list(range(n))
    def f(i):
        while pai[i]!=i: pai[i]=pai[pai[i]]; i=pai[i]
        return i
    G=3.0
    idx=sorted(range(n),key=lambda i:D[i].x0)
    for a in range(n):
        i=idx[a]; ri=D[i]+(-G,-G,G,G)
        for b in range(a+1,n):
            j=idx[b]
            if D[j].x0>ri.x1: break
            if ri.intersects(D[j]): pai[f(i)]=f(j)
    C={}
    for i in range(n): C.setdefault(f(i),[]).append(i)
    out=[]
    for ids in C.values():
        R=fitz.Rect()
        for i in ids: R|=D[i]
        if R.width*R.height<=40 or max(R.width,R.height)<=30: continue
        glif=sum(1 for i in ids if M[i].get('fill') and max(D[i].width,D[i].height)<12)
        cotas=sum(1 for i in ids for it in M[i]['items'] if it[0]=='l' and abs(it[2]-it[1])>15 and (M[i].get('width') or 0)<0.8 and M[i]['type'] in ('s','fs') and (abs(it[1].x-it[2].x)<0.3 or abs(it[1].y-it[2].y)<0.3))
        grande=sum(1 for i in ids if max(D[i].width,D[i].height)>=15)
        texto= (cotas==0 and R.height<30) or (glif>=3 and grande<=1 and R.height<30) or (cotas==0 and R.height<28 and R.width>3*R.height) or (cotas==0 and glif>=12 and glif>0.6*len(ids))
        out.append({'r':R,'n':len(ids),'glif':glif,'cotas':cotas,'texto':texto})
    return out
def dist(a,b):
    dx=max(0,max(a.x0-b.x1,b.x0-a.x1)); dy=max(0,max(a.y0-b.y1,b.y0-a.y1)); return (dx*dx+dy*dy)**0.5
NUM=re.compile(r'^[\d.,]+$')
CODRE=re.compile(r'^[A-Z]{1,4}[- .]?\d{2,5}[A-Z]?$|^\d{5,6}$')
_ocr_cache={}
def rotulos_pagina(p):
    key=(p.parent.name,p.number)
    if key in _ocr_cache: return _ocr_cache[key]
    L=[]
    for w in p.get_text('words'):
        t=w[4].strip()
        if CODRE.match(t.upper()): L.append(fitz.Rect(w[:4]))
    if len(L)<2:
        import pytesseract,io
        from PIL import Image
        Z=250/72; pm=p.get_pixmap(dpi=250,colorspace=fitz.csGRAY); im=Image.open(io.BytesIO(pm.tobytes('png')))
        d=pytesseract.image_to_data(im,config='--psm 11',output_type=pytesseract.Output.DICT)
        for i,t in enumerate(d['text']):
            t=t.strip().upper()
            if CODRE.match(t) and re.search(r'\d{3}',t): L.append(fitz.Rect(d['left'][i]/Z,d['top'][i]/Z,(d['left'][i]+d['width'][i])/Z,(d['top'][i]+d['height'][i])/Z))
    _ocr_cache[key]=L; return L
def recorte(p,cod,cat='',lab0=None):
    lab=lab0 or rotulo(p,cod) or rotulo_ocr(p,cod)
    G=grupos(p)
    if lab is None: return None,None
    G=[g for g in G if not (g['r']+(-2,-2,2,2)).intersects(lab) and g['r'].width*g['r'].height>150 and not g['texto']]
    if not G: return None,lab
    acima_ok=any(k in cat for k in ('Integrada','Tera','Específica'))   # rótulo embaixo do desenho
    def sc(g):
        r=g['r']; abaixo=(r.y1<=lab.y0+20) if acima_ok else r.y0>=lab.y1-6; sob=min(r.x1,lab.x1+150)-max(r.x0,lab.x0-150)>0
        return dist(r,lab)+(0 if abaixo else 80)+(0 if sob else 30)-(15 if g['cotas']>=2 else 0)
    todos=[r for r in rotulos_pagina(p) if not (r+(-3,-3,3,3)).intersects(lab)]
    def sc_l(g,l):
        r=g['r']; abaixo=(r.y1<=l.y0+20) if acima_ok else r.y0>=l.y1-6; sob=min(r.x1,l.x1+150)-max(r.x0,l.x0-150)>0
        return dist(r,l)+(0 if abaixo else 80)+(0 if sob else 30)
    meus=[g for g in G if all(sc_l(g,lab)<=sc_l(g,o)+5 for o in todos)]
    cand=sorted(meus or G,key=sc)
    g=cand[0]['r']
    # junta grupos vizinhos pequenos (cotas soltas) muito próximos
    R=fitz.Rect(g)
    for h in G:
        h=h['r']
        if h==g: continue
        if dist(h,R)<6 and h.width*h.height<0.5*R.width*R.height: R|=h
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines',[]):
            t=''.join(s['text'] for s in l['spans']).strip(); r=fitz.Rect(l['bbox'])
            if NUM.match(t) and dist(r,R)<8: R|=r
    return R+(-3,-3,3,3),lab
if __name__=='__main__':
    P=json.load(open('/home/claude/catalogo/pendentes.json')); TIDX=json.load(open('/home/claude/alcoa/pend/tera_idx.json'))
    jobs={}; falta=[]
    for r in P:
        cod,cat,pg,cc=r[0],r[7],r[8],r[9]
        if cat not in PDF or cat=='Belmetal Atlanta': falta.append((cod,cat,'sem pdf')); continue
        try: pg=int({'BX-105':160,'CG-087':134,'CM-063':141,'CX-071':140,'CX-085':135,'DV-108':172,'DV-112':163}.get(cod,pg))
        except: falta.append((cod,cat,'pg?')); continue
        d=fitz.open(PDF[cat])
        if pg>d.page_count: falta.append((cod,cat,'pg>')); continue
        p=d[pg-1]
        lab0=None
        if 'Tera' in cat:   # rótulo principal (com Kg/m embaixo) do índice OCR da Tera; o texto do código também aparece em chamadas de peças vizinhas
            nc=re.sub(r'[^A-Z0-9]','',str(cc).upper().replace('O','0'))
            h=[t for t in TIDX.get(str(pg-1),[]) if t[5] and re.sub(r'[^A-Z0-9]','',t[0].replace('O','0'))==nc]
            if h: lab0=fitz.Rect(h[0][1:5])
        R,lab=recorte(p,cc,cat,lab0)
        if R is not None and lab0 is not None:   # Tera (texto em curvas): números de cota ficam fora dos grupos -> folga, sem chegar ao rótulo
            R=R+(-20,-9,20,14); R.y1=min(R.y1,lab.y0-3)
        if R is None: falta.append((cod,cat,pg,cc,'rotulo' if lab is None else 'grupo')); continue
        jobs[cod]={'cat':cat,'pdf':PDF[cat],'pg':pg,'cc':cc,'clip':[round(v,1) for v in R],'lab':[round(v,1) for v in lab],'peso':r[10],'situacao':r[13]}
    MAN={'AP-005':(75,572,525,738),'AP-016':(95,180,560,365),'AP-053':(75,185,190,272),'AP-061':(340,135,555,200),'AP-066':(55,78,274,395),'42-178':(372,300,540,568),'AP-2771':(115,95,497,238),'AP-2769':(111.2,96,493.7,366.8),'AP-2770':(144.4,437.0,502.6,695.6),'AP-2774':(140.0,173.4,487.7,313.9),'AP-2775':(132.6,465.7,495.5,627.5),'AP-2773':(115,546,497,698),'AP-044':(100,626,495,781),'37-005':(130,118,245,228),'25-539':(332,384,556,530),'AP-060':(103,118,302,348),'AP-072':(188,628,360,768),'AP-074':(405,370,540,752),'AP-073':(129,486,365,603),'AP-068':(380,352,512,458),'AP-1413':(92.8,581.4,238,757),'AP-025':(126,583,220,708),'LB-050':(28,458,570,566),'LG-071':(355,152,545,746),'ST-031':(234.5,455,535,590),'SU-202':(118,112,250,200),'SU-231':(160,524,470,684),'SU-017':(55,172,146,320),'MN-002':(136,540,482,622),'LB-038':(27.4,203.2,567.9,400),'FC-258':(300,738,556,802),'FC-087':(72,346,535,516),'CL-009':(90,548,300,768),
         'AP-064':(330,60,555,480),'AP-1057':(200,140,386,240),'AP-002':(85,170,200,705),'LG-129E':(345,449,515,762),'AP-004':(95,280,515,425),'SU-500':(238,436,388,545),'MN-005':(190,105,556,440),'MN-006':(252,445,525,792),'MN-003':(70,170,500,285),'MN-015':(170,465,370,695)}
    for k,c in MAN.items():
        if k in jobs: jobs[k]['clip']=list(c); jobs[k]['manual']=True
    for k,j in jobs.items():   # Integrada: cotas ficam fora do grupo do desenho -> folga (rótulo fica embaixo, longe)
        if 'Integrada' in j['cat'] and k not in ('MN-002','MN-005','MN-006'):
            c=j['clip']; j['clip']=[round(c[0]-26,1),round(c[1]-18,1),round(c[2]+26,1),round(c[3]+5,1)]
    if 'MN-007' in jobs: jobs['MN-007']['clip'][1]-=8; jobs['MN-007']['clip'][0]-=14
    if 'MN-008' in jobs: jobs['MN-008']['clip'][1]-=26
    if 'MN-010' in jobs: jobs['MN-010']['add']=[['56,83',[499.8,217.8,520.7,225.2],False]]
    if 'MN-015' in jobs: jobs['MN-015']['clip'][2]+=22
    if 'MN-039' in jobs: jobs['MN-039']['clip'][0]-=10
    if 'MN-032' in jobs: jobs['MN-032']['clip'][1]-=20
    if 'MN-032' in jobs: jobs['MN-032']['clip'][3]+=35
    for k,j in jobs.items():   # perfil em tiras de triângulos: fecha as frestas
        if any(c in j['cat'] for c in ('Alumil','Binkafer')): j['costura']=True
    if 'AP-064' in jobs: jobs['AP-064']['apagar']=[[334,65,404,104]]
    if 'AP-060' in jobs: jobs['AP-060']['branco']=[[100,116,112,150]]
    if 'AP-060' in jobs: jobs['AP-060']['fix']={'6.6':'56,6','6,6':'56,6','1':''}
    if 'CL-009' in jobs: jobs['CL-009']['apagar']=[[228,670,300,704]]
    if 'FC-258' in jobs: jobs['FC-258']['apagar']=[[364,728,445,758]]
    if 'FC-087' in jobs: jobs['FC-087']['apagar']=[[266,448,332,478],[382,350,442,381],[98,290,256,389.5]]
    if 'FC-087' in jobs: jobs['FC-087']['branco']=[[98,290,256,389.5]]
    if 'LG-129E' in jobs: jobs['LG-129E'].update(branco=[[334,434,395,465]],fix={'13,7':'43,7','3,7':'43,7'})
    if 'MN-002' in jobs: jobs['MN-002']['fix']={'1':''}
    if 'MN-005' in jobs: jobs['MN-005']['fix']={'005':''}
    if 'ST-031' in jobs: jobs['ST-031'].update(apagar=[[190,448,245,471]],branco=[[200,448,245,470]])
    for k in ('BX-102','BX-205'):
        if k in jobs: jobs[k]['fix']={'411':'11'}
    if 'TSL-003' in jobs: jobs['TSL-003'].update(fix={'7':''},add=[['71,41',[312,544,334,564],['ang',-45.0,[322.5,554.2],22.0,7.13]]])
    if 'BX-099' in jobs: jobs['BX-099'].update(sem_cinza=True,branco=[[259,104,306,152]])
    if 'SU-500' in jobs: jobs['SU-500']['branco']=[[218,436,292,474]]
    if 'ST-027' in jobs: jobs['ST-027']['rem']=[[87.9,620.8,233.7,640.7]]
    if 'MN-031' in jobs: jobs['MN-031']['fix']={'164':'167'}
    if 'DV-110' in jobs: jobs['DV-110']['fix']={'201':'20'}
    if 'AP-066' in jobs: jobs['AP-066']['apagar']=[[42,70,129,107]]
    for k in ('TG-084','TG-280'): jobs.pop(k,None)   # tubos: linha de tabela (TABELADO), sem desenho próprio
    # BX (box): o equivalente do cadastro é ASA (fabricante original) e o peso do ERP bate com o ASA; o BX-xxx da Tera era só coincidência de código
    ASA={'BX-006':(214,'Y-107','0,262',(86,556,176,699)),'BX-102':(210,'U-1002','0,213',(55,618,160,733)),'BX-105':(210,'I-154','0,306',(310,612,402,733)),
         'BX-108':(211,'Y-308','0,278',(60,162,186,268)),'BX-109':(210,'U-655','0,645',(60,80,258,256)),'BX-111':(211,'44-018 (I-155)','0,389',(215,98,352,268))}
    ASA['BX-003']=(214,'U-1056','0,228',(80,362,192,470))
    for k,(pg,cc,pw,cl) in ASA.items():
        if k in jobs: jobs[k].update(cat='Geral ASA',pdf='/home/claude/alcoa/asa.pdf',pg=pg,cc=cc,clip=list(cl),peso=pw,lab=[0,0,0,0]); jobs[k].pop('fix',None); jobs[k].pop('apagar',None)
    # 26/11: desenhos enviados pelo cliente
    CLI={'BX-029':('BX-029','0,223',(266,386,328,492),{}),
         'AP-004':('AP-004','',(106,148,238,728),{'add':[['15,2',[174,707,193,717],False]]}),
         'AP-002':('PR-003E','',(268,356,348,432),{})}
    for k,(cc,pw,cl,ex) in CLI.items():
        if k in jobs:
            jobs[k]={'cat':'PDF do cliente (26/11)','pdf':f'/home/claude/alcoa/cliente26/{cc if k=="AP-002" else k}.pdf','pg':1,'cc':cc,'clip':list(cl),'peso':pw,'lab':[0,0,0,0],'manual':True,**ex}
    # 26/11 (planilha de pesos do cliente): fornecedor real informado -> desenho do fornecedor (peso confere)
    FORN={'CG-080':('Geral Stelman','/home/claude/alcoa/stelman.pdf',186,'STL-424','1,388',(128,118,465,410)),
          'CX-085':('Geral Stelman','/home/claude/alcoa/stelman.pdf',174,'STL-421','1,130',(160,119,440,330)),
          'CL-009':('Geral Império','/home/claude/alcoa/imperio.pdf',30,'A6 L-468','1,646',(20,165,275,402)),
          'CL-006':('Geral Império','/home/claude/alcoa/imperio.pdf',30,'A6 CL-006','1,004',(30,525,255,716))}
    for k,(cat,pdf,pg,cc,pw,cl) in FORN.items():
        jobs[k]={'cat':cat,'pdf':pdf,'pg':pg,'cc':cc,'clip':list(cl),'peso':pw,'lab':[0,0,0,0],'manual':True}
    json.dump(jobs,open('/home/claude/alcoa/pend/jobs.json','w'),ensure_ascii=False,indent=1)
    print(len(jobs),'ok'); print(len(falta),'falta')
    for x in falta: print(' ',x)
