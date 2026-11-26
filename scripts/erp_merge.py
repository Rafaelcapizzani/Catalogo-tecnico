import openpyxl, collections, json, re
ns={}; exec(open('/home/claude/cruzar.py').read(), ns)
norm, inv, tab = ns['norm'], ns['inv'], ns['tab']
site=json.load(open('cruzamento.json'))
ws=openpyxl.load_workbook('erp.xlsx',read_only=True,data_only=True).active
rows=list(ws.iter_rows(values_only=True)); h=rows[0]; R=[dict(zip(h,r)) for r in rows[1:] if r[0]]
erp=collections.defaultdict(list)
for r in R:
    k=norm(str(r['CÓDIGO_AUXILIAR'] or r['CÓDIGO_CIAZZANI']))
    erp[k].append(r)
erp_by_ciaz={norm(str(r['CÓDIGO_CIAZZANI'])):norm(str(r['CÓDIGO_AUXILIAR'] or r['CÓDIGO_CIAZZANI'])) for r in R}
def erpinfo(lst):
    if not lst: return ['Não','','','','','']
    forn=sorted({(r['FORNECEDOR'] or '(sem fornecedor)').title() for r in lst})
    sit='Ativo' if any(r['SITUAÇÃO']==1 for r in lst) else 'Inativo'
    cores=sorted({r['CÓDIGO_DA_COR'] for r in lst if r['CÓDIGO_DA_COR']})
    pe=sorted({f"{r['CÓDIGO_DA_COR']}: {r['TIPO']}" for r in lst})
    peso=lst[0]['PESO_TEÓRICO']
    return ['Sim',sit,'; '.join(forn),', '.join(cores),'; '.join(pe),peso]
def match(a,c,desc):
    na,nc=norm(a),norm(c)
    if any((desc or '').lower().startswith(t) for t in tab): return ['Tabelado (não precisa desenho individual)','','','','','']
    for k,via in ((na,'código Alplan'),(nc,'código equivalente')):
        if k in inv and inv[k]['cat']!='Standart':
            h=inv[k]; return ['Achado (vetor)' if h['vet'] else 'Achado',h['cat'],h['pag'],h['cod'],h['peso'],via]
    return ['Não achado','','','','','']
import openpyxl as _ox
_uw=_ox.load_workbook('user_cruz.xlsx',data_only=True)['Lista completa']
ucode={}
for _r in _uw.iter_rows(min_row=2,values_only=True):
    if _r[3]: ucode[str(_r[0])]=(str(_r[3]).replace(' ',''),_r[4] or '')
def umatch(a):
    if a not in ucode: return None
    k=norm(ucode[a][0])
    if k not in inv: k=re.sub(r'([0-9])[A-Z]$',r'\1',k)
    if k in inv and inv[k]['cat']!='Standart':
        h=inv[k]; return ['Achado (vetor)',h['cat'],h['pag'],h['cod'],h['peso'],'código informado ('+ucode[a][0]+')']
    return None
out=[]; used=set()
for r in site:
    a,c,desc=r[0],r[1],r[2]
    k=norm(a); lst=erp.get(k) or erp.get(erp_by_ciaz.get(norm(c),'#'),[])
    if lst: used.add(norm(str(lst[0]['CÓDIGO_AUXILIAR'] or lst[0]['CÓDIGO_CIAZZANI'])))
    res=r[3:9]
    if res[0]=='Não achado':
        u=umatch(a)
        if u: res=u
    out.append([a,c,desc,'Sim']+res+erpinfo(lst))
for k,lst in erp.items():
    if k in used: continue
    r0=lst[0]; a=str(r0['CÓDIGO_AUXILIAR'] or r0['CÓDIGO_CIAZZANI']); c=str(r0['CÓDIGO_CIAZZANI'])
    desc=re.sub(r'\s+(NATURAL|BRANCO|PRETO).*$','',str(r0['DESCRIÇÃO_CIAZZANI'] or r0['DESCRIÇÃO_DO_ITEM']))
    res=match(a,c,desc)
    if res[0]=='Não achado':
        u=umatch(a)
        if u: res=u
    out.append([a,c,desc,'Não']+res+erpinfo(lst))
OVR={'AP-619':['Achado (vetor)','Geral Stelman',85,'STL-619','0,369','código informado (STL-619, corrigido)'],
     'AP-006':['Achado (vetor)','Geral ASA',162,'79-125D','1,232','código informado (79-125D, confirmado: pág. impressa 144, 3º perfil)'],
     'AP-009':['Achado (vetor)','Geral ASA',162,'79-060D','1,464','código informado (79-060D, corrigido)']}
# --- ISA (Geral ISA, imagem; OCR 300 dpi) ---
import re as _re
def _nk(c):
    m=_re.match(r'^([A-Z]+)-?0*(\d+)([A-Z]?)$',str(c).replace(' ','').upper())
    return (m[1]+m[2]+m[3]) if m else str(c)
ISA=collections.defaultdict(list)
for k,v in json.load(open('isal_idx2.json')).items():
    if k.startswith('AP-'): continue   # AP-xxx da ISA = Linha Bike, coincidência com códigos Alplan
    ISA[_nk(k)]+=v
for o in out:
    if o[4]!='Não achado': continue
    cands=[(o[0],'código Alplan'),(o[1],'código equivalente')]+([(ucode[o[0]][0],'código informado')] if o[0] in ucode else [])
    for c,via in cands:
        k=_nk(c); h=ISA.get(k); extra=''
        if not h:
            for suf in 'LAE':
                if ISA.get(k+suf): h=ISA[k+suf]; extra=f' (só existe a variante {suf} — conferir)'; break
        if h:
            pg,cod,w,role=sorted(h,key=lambda x:x[3]!='principal')[0]
            via2=via+(' = equivalente impresso no catálogo ISA' if role!='principal' else '')+extra
            o[4:10]=['Achado (imagem)','Geral ISA',pg,cod,w,via2]; break
for o in out:
    if o[4]=='Achado (imagem)':
        try:
            q=float(str(o[15]).replace(',','.'))/float(str(o[8]).replace(',','.'))
            if not 5.2<q<6.9: o[4]='Possível (conferir)'; o[9]+=f' — peso não bate com o ERP (ERP {o[15]} kg/barra ≈ {float(str(o[15]).replace(",","."))/6:.3f} kg/m)'.replace('.',',',0)
        except Exception: pass
# AP-1234..1253 (Sistema Modular): mesmos perfis dos CX-973..992 da ISA; usar o vetor da Stelman STL-12xx (confirmado pelo cliente e conferido visualmente)
_stl16=json.load(open('stl16.json'))
for o in out:
    if _re.fullmatch(r'AP-12(3[4-9]|4\d|5[0-3])',o[0]):
        stl='STL-'+o[0][3:]; pg,w=_stl16[stl]
        isa=o[7] if o[5]=='Geral ISA' else ''
        o[4:10]=['Achado (vetor)','Geral Stelman',pg,stl,f'{w:.3f}'.replace('.',','),f'mesmo perfil do {isa} (ISA); vetor da Stelman Sistema Modular']
# Códigos informados pelo cliente em 24/11 (Geral Tera), conferidos no PDF
for o in out:
    _t=json.load(open('tera_user.json')).get(o[0])
    if _t:
        c,pg,w=_t
        q=float(str(o[15]).replace(',','.'))/6/float(w.replace(',','.'))
        nota='' if 0.85<q<1.15 else f' — peso Tera {w} × ERP ≈ {float(str(o[15]).replace(",","."))/6:.3f} kg/m (conferir)'.replace('.',',')
        o[4:10]=['Achado (vetor)','Geral Tera',pg,c,w,f'código informado ({c}, Geral Tera)'+nota]
# ===== rev. 14: códigos informados pelo cliente em 24/11 (11h) + catálogos novos =====
def _f(x):
    try: return float(str(x).replace(',','.'))
    except Exception: return None
def _chk(o,w):
    e=_f(o[15]); c=_f(w)
    if not e or not c: return ''
    q=e/6/c
    return '' if 0.85<q<1.15 else f' — peso catálogo {w} × ERP ≈ {e/6:.3f} kg/m (conferir)'.replace('.',',')
INF={ # código Alplan: (catálogo, pág PDF, código no catálogo, peso, vetor?)
 '31-085':('Geral ASA',165,'31-085C','0,894',True),
 '37-005':('Sapa (Box padronizados)',1,'370005','0,086',True),
 'AP-026':('Geral Tera',124,'BX-876','0,054',True),
 'DS-028':('Geral ASA',189,'T-180','0,125',True),
 'E-725':('Geral ASA',220,'39-1271C','0,501',True),
 'PC-009':('Geral Tera',127,'D-080','1,697',True),
 'PC-011':('Geral Tera',126,'PC-026','0,778',True),
 'PMO-023':('Geral ASA',37,'MG20-107','',True),
 'PMO-024':('Geral ASA',37,'MG20-105','0,893',True),
 'PP-002':('Geral Hera',197,'MAC-0135','0,196',True),
 'PP-004':('Geral Hera',197,'MAC-0138','0,238',True),
 'PV-003':('Nylkit (Perfis vitrine)',1,'PV-003','0,160',True),
 'SU-270':('Alumax (Linha Suprema)',1,'SU-270','0,730',True),
 'PC-000':('Geral Hera',228,'MAC-1430','0,473',True),
 'MM-008':('Mega 32 Lite (ASA)',1,'MM-008','0,605',True),
 'MM-010':('Mega 32 Lite (ASA)',1,'MM-010','1,019',True),
 'ST-002':('SP20 Selta',35,'20SP-M20','0,352',True),
 'ST-027':('SP20 Selta',71,'SPI-M18','0,791',True),
 'ST-031':('SP20 Selta',71,'20SP-M59S','0,660',True),
 'SU-202':('Metal Centenário (Linha TMS)',1,'TMS-202','0,114',True),
 'SU-231':('Binkafer (Linha 25 a 90°)',1,'BKS-231','0,751',True),
 'ES-001':('Euroshow (Alushow)',25,'ES-001','1,386',True),
 'ES-002':('Euroshow (Alushow)',25,'ES-002','0,950',True),
 'ES-004':('Euroshow (Alushow)',26,'ES-004','0,501',True),
 'ES-006':('Euroshow (Alushow)',26,'ES-006','0,244',True),
 'ES-010':('Euroshow (Alushow)',27,'ES-010','0,450',True),
 'ES-016':('Euroshow (Alushow)',27,'ES-016','0,867',True),
 'ES-018':('Euroshow (Alushow)',28,'ES-018','1,498',True),
 'ES-019':('Euroshow (Alushow)',28,'ES-019','0,552',True),
 'ES-022':('Euroshow (Alushow)',30,'ES-022','0,326',True),
 'ES-024':('Euroshow (Alushow)',30,'ES-024','0,080',True),
 'ES-028':('Euroshow (Alushow)',31,'ES-028','1,330',True),
 'ES-030':('Euroshow (Alushow)',164,'ES-030','0,733',True),
 'ES-031':('Euroshow (Alushow)',164,'ES-031','0,843',True),
 'ES-033':('Euroshow (Alushow)',163,'ES-033','0,235',True),
 'ES-034':('Euroshow (Alushow)',163,'ES-034','0,295',True),
 'ES-040':('Euroshow (Alushow)',132,'ES-040','0,863',True),
 'ES-042R':('Euroshow (Alushow)',133,'ES-042R','1,458',True),
 'ES-046':('Euroshow (Alushow)',166,'ES-046','1,321',True),
 'ES-047':('Euroshow (Alushow)',167,'ES-047','1,277',True),
 '25-543':('Alplan Linha 25 (Porta de Abrir)',1,'25-543 (P-415)','0,810',True),
 'DV-105':('Alcoa Divisórias',1,'DV-129','0,435',True),
 'LG-060':('Alcoa Linha III Gold (baguetes)',1,'SI-330','0,195',True),
 'LG-570':('ASA Mega 32 (5 planos)',1,'MG32-126','2,794',True),
 'LG-571':('Folha própria (MG32-125 com cabeças do MG32-126)',1,'MG32-125/126','',True),
 'LG-572':('ASA Mega 32 (5 planos)',1,'MG32-127','1,468',True),
 'TSL-004':('Alplan Sala Limpa',1,'TSL-004','0,669',True),
 'TSL-006':('Alplan Sala Limpa',1,'TSL-006','0,283',True),
 'AP-046':('Geral Tera',238,'CX-158','0,385',True),
 'AP-047':('Geral Império',52,'A6 667','0,415',True),
 'AP-048':('Geral Império',52,'A6 230','0,438',True),
 'AP-049':('Geral Império',51,'A4 A-057','0,281',True),
 'AP-051':('Novaxx Lambri (brise)',2,'NX 4397','0,593',True),
 'AP-1589':('Tamboré Catálogo Industrial (Baús frigoríficos)',1,'TMR-1589','1,767',True),
 'D-143':('Geral Tera',135,'CX-085','1,128',True),
 'T-734':('Alplan Arremates',1,'CA-004','0,485',True),
 'TSL-002':('Alplan Sala Limpa',1,'TSL-002','0,657',True),
 'TSL-009':('Geral Tera',218,'DV-428','0,550',True),
 'DS-024':('Nylkit Perfis vitrine (ED03)',1,'DS-024','0,125',True),
 'AP-020':('Geral Hera',138,'MAC-0234','0,528',True),
 'AP-021':('Geral Hera',138,'MAC-0235','0,222',True),
 'BX-018':('Geral Stelman',30,'STL-049','0,172',True),
 'BX-019':('Geral Stelman',30,'STL-046 A','0,423',True),
 'BX-020':('Geral Stelman',30,'STL-052','0,148',True),
 'BX-021':('Geral Stelman',30,'STL-048','0,247',True),
 'BX-022':('Geral Stelman',30,'STL-053','0,209',True),
 'BX-039':('Geral Império',178,'A6 L-006','0,289',True),
 'CX-001':('Geral Império',162,'A5 CX-001','0,424',True),
 'CX-002':('Geral Tera',230,'CX-137','0,316',True),
 '42-178':('Geral Alumil',73,'P-1178','1,041',True),
 '42-307':('Sapa (Box padronizados)',1,'420307','0,372',True),
 'AL-089':('Perfil Master (Gradil de sacada)',1,'PSG 0089','0,610',True),
 'AL-090':('Perfil Master (Gradil de sacada)',1,'PSG 0090','0,180',True),
 'AL-091':('Perfil Master (Gradil de sacada)',1,'PSG 0091','0,490',True),
 'AP-002':('Geral Decamp',128,'PR-002','1,786',True),
 'AP-005':('Geral Império',73,'A6 RP-004','0,977',True),
 'AP-016':('Geral Império',194,'A6 U-900','5,697',True),
 'AP-028':('Geral ASA',219,'39-959','0,137',True),
 'AP-038':('Geral ASA',67,'MG25-509','',True),
 'AP-030':('Geral Hyspex',216,'76500','0,126',True),
 'AP-036':('Geral Hyspex',220,'76840','0,619',True),
 'AP-037':('Geral Hyspex',219,'76900','0,241',True),
 'DS-033':('Geral Hyspex',191,'72730','0,166',True),
 'DS-034':('Geral Hyspex',191,'72750','0,273',True),
 'AP-053':('Geral Império',164,'A5 1221','0,114',True),
 'AP-0601':('Geral Decamp',221,'PR-32.601','4,609',True),
 'AP-0603':('Geral Decamp',221,'PR-32.603','2,705',True),
 'AP-065':('Geral Império',194,'A6 U-901','4,504',True),
 'AP-066':('Geral Decamp',238,'PR-32.611','1,231',True),
 'AP-1046':('Maximus 20 (Stelman)',3,'STL-1046','0,610',True),
 'AP-1047':('Maximus 20 (Stelman)',4,'STL-1047','0,812',True),
 'AP-1057':('Maximus 20 (Stelman)',8,'STL-1057','0,412',True),
 'AP-1058':('Maximus 20 (Stelman)',8,'STL-1058','0,482',True),
 'AP-1059':('Maximus 20 (Stelman)',8,'STL-1059','0,397',True),
 'AP-1329':('Geral Decamp',214,'PR-30.001','1,103',True),
 'CM-065':('Geral Decamp',146,'DP-015','0,214',True),
 'DV-021':('Geral Tera',171,'DV-670','0,264',True),
 'DV-110':('Geral Tera',173,'DV-208','0,316',True),
 'LG-056R':('Geral Decamp',251,'PR-32.556','0,707',True),
 'PV-001':('Geral Tera',178,'AL-097','0,339',True),
 'PV-002':('Geral Tera',178,'AL-096','0,219',True),
 'SU-015':('Geral ASA',50,'MG25-015','',True),
 'SU-016':('Geral ASA',52,'MG25-016','',True),
 'SU-017':('Geral Alumil',75,'SU-017','0,323',True),
 'SU-023':('Geral Império',134,'A6 SU-023','0,950',True),
 'SU-224':('Nylkit (Suprema)',1,'NSU325','0,977',True),
 'SU-500':('Geral Alumil',89,'SU-102A','0,099',True),
 'SU-521':('Geral Hera',75,'MACF-0908','1,724',True),
 'SU-522':('Geral Hera',75,'MACF-0909','1,706',True),
 'SU-523':('Geral Hera',75,'MACF-0910','1,005',True),
}
PEND={}
for o in out:
    if o[0] in INF:
        cat,pg,c,w,vet=INF[o[0]]
        nota=' — desenho do catálogo em cinza: alterar para preto' if o[0] in ('SU-521','SU-522','SU-523','PP-002','PP-004') else ''
        alt={**{c:' (antes: ISA, imagem) — cotas padronizadas (lote-25-11-01h-vetor.zip)' for c in ['AP-020','AP-021','BX-018','BX-019','BX-020','BX-021','BX-022','BX-039']},'DS-024':' (antes: ISA BX-046, imagem) — cotas padronizadas (DS-024.svg)',**{c:' — cotas padronizadas (lote-24-11-23h50-vetor.zip)' for c in ['AP-046', 'AP-047', 'AP-048', 'AP-049', 'AP-051', 'AP-1589', 'D-143', 'T-734', 'TSL-002', 'TSL-009']},**{c:' — cotas padronizadas (lote-24-11-23h-vetor.zip)' for c in ['25-543','DV-105','LG-060','LG-570','LG-571','LG-572','TSL-004','TSL-006']},**{c:' — perfil preenchido e cotas padronizadas (euroshow-vetor.zip)' for c in ['ES-001', 'ES-002', 'ES-004', 'ES-006', 'ES-010', 'ES-016', 'ES-018', 'ES-019', 'ES-022', 'ES-024', 'ES-028', 'ES-030', 'ES-031', 'ES-033', 'ES-034', 'ES-040', 'ES-042R', 'ES-046', 'ES-047']},'MM-008':' — no catálogo é imagem só com contorno: preenchido e convertido em vetor (mega32-vetor.zip)','MM-010':' — confirmado pelo cliente (MM-010, não MM-009); imagem só com contorno: preenchido e convertido em vetor (desenhos-cotas-padronizadas.zip, MM-010_alternativa.svg)','AP-020':' (também na ISA: BX-114L, pág. 179)','AP-021':' (também na ISA: BX-195, pág. 179)','AP-022':' (também na ISA: BX-1236, pág. 180)'}.get(o[0],'')
        o[4:10]=['Achado (vetor)' if vet else 'Achado (imagem)',cat,pg,c,w,f'código informado ({c})'+alt+('' if o[0] in ('DS-033','DS-034') else _chk(o,w))+nota]
    elif o[0] in PEND:
        o[4:10]=['Não achado','','','','',f'informado {PEND[o[0]]} (Geral Hyspex) — catálogo ainda não recebido']
    elif o[0]=='39-182':
        o[4:10]=['Não achado','','','','','indicação anterior (31-085C) estava errada — cliente vai localizar']
    elif o[0] in ('DV-302','AP-052'):
        o[4:10]=['Não achado','','','','','']
# busca automática nos catálogos novos (só faltantes; validada pelo peso do ERP)
NEWIDX=[]
for k,v in json.load(open('alumil_idx.json')).items(): NEWIDX.append((k,'Geral Alumil',v[0][0],v[0][1],True))
for k,v in json.load(open('imperio_idx.json')).items(): NEWIDX.append((k,'Geral Império',v[0][0],v[0][1],True))
for k,v in json.load(open('luxxor_idx.json')).items(): NEWIDX.append((k,'Novaxx Luxxor 2.5',v[0],v[1],True))
for k,v in json.load(open('hera_idx.json')).items():
    if v[0]:
        NEWIDX.append((k,'Geral Hera',v[0],v[1],True))
        if v[2]: NEWIDX.append((v[2],'Geral Hera',v[0],v[1],True,k))
for k,v in json.load(open('maximus_idx.json')).items(): NEWIDX.append((k,'Maximus 20 (Stelman)',v[0],v[1],True))
for k,v in json.load(open('laf_idx.json')).items(): NEWIDX.append((k,'Geral LAF (Nals)',v[0],v[1],False))
for k,w in (('PSG 0092','0,880'),('PSG 0093','0,180')): NEWIDX.append((k,'Perfil Master (Gradil de sacada)',2,w,True))
for k,w in (('NSU225','0,944'),('NSU326','0,308')): NEWIDX.append((k,'Nylkit (Suprema)',1,w,True))
for k,w in (('370005','0,086'),('420308','0,324'),('420306','0,215'),('340803','0,146'),('340806','0,177')): NEWIDX.append((k,'Sapa (Box padronizados)',1,w,True))
NI=collections.defaultdict(list)
for e in NEWIDX:
    k,cat,pg,w,vet=e[:5]; NI[_nk(k)].append((e[5] if len(e)>5 else k,cat,pg,w,vet,k if len(e)>5 else ''))
autos=[]
for o in out:
    if o[4]!='Não achado' or o[9] or o[0] in ('DV-302','AP-052','39-182'): continue
    for c,via in ((o[0],'código Alplan'),(o[1],'código equivalente')):
        hs=NI.get(_nk(c))
        if not hs: continue
        ok=[h for h in hs if not _chk(o,h[3])]
        h=(ok or hs)[0]; k,cat,pg,w,vet,mk=h
        st=('Achado (vetor)' if vet else 'Achado (imagem)') if ok else 'Possível (conferir)'
        o[4:10]=[st,cat,pg,k,w,via+(f' = código de mercado {mk} no índice Hera' if mk else '')+_chk(o,w)]; autos.append((o[0],st,cat,k,mk)); break
json.dump(autos,open('autos_rev14.json','w'))
TABU={'TG-000','TG-017','PU-005','PU-006'}
EXCL={'SUCATA','TARUGO','5062'}
out=[o for o in out if o[0] not in EXCL and not any(w in (o[2] or '').upper() for w in ('SUCATA','TARUGO','PERFIS DIVERSOS'))]
for o in out:
    if o[0] in OVR: o[4:10]=OVR[o[0]]
    if o[0] in TABU: o[4:10]=['Tabelado (não precisa desenho individual)','','','','','informado pelo usuário']
json.dump(out,open('cruzamento2.json','w'),ensure_ascii=False,default=str)
C=collections.Counter
print(len(out), C((o[3],o[10]) for o in out))
print(C(o[4] for o in out))
print(C(o[4] for o in out if o[3]=='Não'))
print(C(o[12] for o in out if o[4]=='Não achado').most_common(15))
