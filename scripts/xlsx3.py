import json, collections, openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
o=json.load(open('cruzamento2.json'))
_uw=openpyxl.load_workbook('user_cruz.xlsx',data_only=True)['Lista completa']
def _ox_load(p):
    import openpyxl as _o
    return list(_o.load_workbook(p,data_only=True)['Lista completa'].iter_rows(min_row=2,values_only=True))
UC={str(r[0]):(r[3],r[4]) for r in _uw.iter_rows(min_row=2,values_only=True) if r[3]}
for _k,_v in json.load(open('tera_user.json')).items(): UC[_k]=(_v[0],'Geral - Tera')
for _n in range(1234,1254): UC[f'AP-{_n}']=(f'STL-{_n}','Geral Stelman (Sistema Modular, pág. 81–84)')
_u2=_ox_load('/home/claude/alcoa/user_rev13.xlsx')
for _r in _u2:
    if _r[3] not in (None,''): UC[str(_r[0])]=(str(_r[3]),str(_r[4] or '').strip())
UC['DS-024']=('DS-024','ED03 (Nylkit)')
for _k,_v in {'AP-020':('MAC-0234','Geral - Hera'),'AP-021':('MAC-0235','Geral - Hera'),'BX-018':('STL-049','GERAL - Stelman 02'),'BX-019':('STL-046 A','GERAL - Stelman 02'),'BX-020':('STL-052','GERAL - Stelman 02'),'BX-021':('STL-048','GERAL - Stelman 02'),'BX-022':('STL-053','GERAL - Stelman 02'),'BX-039':('A6 L-006','Geral - Imperio')}.items(): UC[_k]=_v
UC['MM-010']=('MM-010','mega-32-lite')
UC.pop('39-182',None)
UC['AP-619']=('STL-619',UC['AP-619'][1]); UC['AP-009']=('79-060D',UC['AP-009'][1])
o=[r[:3]+[UC.get(r[0],('',''))[0],UC.get(r[0],('',''))[1]]+r[3:] for r in o]
# Geral Alcoa: página do PDF corrigida (índice antigo estava 2 páginas antes) + desenhos padronizados
_GJ=json.load(open('/home/claude/alcoa/ga/jobs.json'))
_GA={v['alplan']:v['pdf'] for v in _GJ.values()}
_PAD=set()
for _f_ in ['lote11','euro','ga/v1','padrao/pacote','lote10','lote9','lote12','su/v1','lote13','asa/v1','gold/v1','lote14','lote15','stl/v1','folhas','atl/v1','lote16','lote17','lote18','lote19','lote20','pend/v1']:
    try:
        for _k in json.load(open(f'/home/claude/alcoa/{_f_}/_cotas.json')): _PAD.add(_k.split('_')[0])
    except Exception: pass
for r in o:
    if r[7]=='Geral Alcoa' and r[0] in _GA: r[8]=_GA[r[0]]
# 25/11: o desenho "DV-055" da Geral Alcoa é o montante em cruz = DV-101 da Tera (Alplan DV-101); Alplan DV-055 (guia) = Tera DV-055
for r in o:
    if r[0]=='DV-101': r[7],r[8],r[9],r[10],r[11]='Geral Tera',171,'DV-101','0,659','código Alplan'
    if r[0]=='DV-055': r[7],r[8],r[9],r[10],r[11]='Geral Tera',172,'DV-055','0,276','código Alplan'
    if r[0]=='SU-043': r[3],r[4]='TMS-043','Metal Centenário Linha TMS (PDF do cliente, 25/11)'; r[7],r[8],r[9],r[10],r[11]='Metal Centenário Linha TMS',217,'TMS-043','0,960','informado pelo cliente'
_AJ=json.load(open('/home/claude/alcoa/asa/jobs.json'))
_AS={v['alplan']:v for v in _AJ.values()}
for r in o:
    if r[7]=='Geral ASA' and r[0] in _AS:
        r[8]=_AS[r[0]]['pdf']
        if _AS[r[0]].get('peso_lido'): r[10]=_AS[r[0]]['peso_lido']
_GD={v['alplan']:v for v in json.load(open('/home/claude/alcoa/gold/jobs.json')).values()}
_ST={v['alplan']:v for v in json.load(open('/home/claude/alcoa/stl/jobs.json')).values()}
for r in o:
    if r[7] in ('Gold III','Gold IV') and r[0] in _GD:
        r[8]=_GD[r[0]]['pdf']
        if _GD[r[0]].get('peso_lido'): r[10]=_GD[r[0]]['peso_lido']
    if r[7]=='Geral Stelman' and r[0] in _ST:
        r[8]=_ST[r[0]]['pdf']
        if _ST[r[0]].get('peso_lido'): r[10]=_ST[r[0]]['peso_lido']
    if r[0] in ('CM-093','SU-083') and r[0] in _GA:
        r[7],r[8]='Geral Alcoa',_GA[r[0]]
        r[10]={'CM-093':'0,765','SU-083':'0,144'}[r[0]]
for r in o:
    if r[0]=='AP-070': r[3],r[4]='Corrimão Edson','PDF do cliente (25/11)'; r[7],r[8],r[9],r[10],r[11]='Corrimão Edson (PDF do cliente)',1,'Corrimão Edson','','informado pelo cliente (desenho sem peso)'
    if r[0]=='AP-069': r[3],r[4]='DP-072','Decamp Portões (PDF do cliente, 25/11)'; r[7],r[8],r[9],r[10],r[11]='Decamp Portões','15.9','DP-072','0,290','informado pelo cliente'
_FO={'DV-302':'folha01','AP-099':'folha01','AP-100':'folha01','AP-033':'folha02','BX-218':'folha02','BX-219':'folha02','AP-035':'folha02','AP-1718':'folha03','AP-1717':'folha03','AP-032':'folha03','AP-034':'folha03'}
for r in o:
    if r[0] in _FO: r[3],r[4]=r[0],f'{_FO[r[0]]}.pdf (cliente, 25/11)'; r[6]='Achado (vetor)'; r[7],r[8],r[9],r[10],r[11]='Folha avulsa do cliente',_FO[r[0]],r[0],'','informado pelo cliente (desenho sem peso)'
_AT={v['alplan']:v for v in json.load(open('/home/claude/alcoa/atl/jobs.json')).values()}
for r in o:
    if r[7]=='Belmetal Atlanta' and r[0] in _AT:
        r[8]=_AT[r[0]]['pdf']
        if _AT[r[0]].get('peso_lido'): r[10]=_AT[r[0]]['peso_lido']
    if r[0]=='AP-0201' and r[7]=='Belmetal Atlanta': r[6]='Não achado'; r[11]='FA-201 só é citado no Atlanta (pág. 66 e 78), sem desenho próprio'
_L16={'AP-050':('AP-050','AP-050.pdf','','redesenho vetorial do RDP-001 (cliente)'),'AP-055':('AP-055','AP-055_AP-054.pdf','','redesenho das imagens originais (cliente)'),'AP-054':('AP-054','AP-055_AP-054.pdf','','redesenho das imagens originais (cliente)'),
 'AP-052':('TRN-009','TRN-009.pdf','','redesenho a partir do catálogo (cliente)'),'SU-048':('ISU-048','SU-048.pdf','','vetorização da imagem do catálogo (cliente)'),
 '39-182':('39-182','39-182.pdf','4,349','informado pelo cliente'),'AP-0201':('FA-201','fa-201.pdf','1,795','informado pelo cliente (imagem vetorizada)')}
_L16.update({'AP-022':('BX-1236','Perfis_BX_1-1.pdf','','informado pelo cliente (vetor)'),'AP-023':('BX-203','Perfis_BX_1-1.pdf','','informado pelo cliente (vetor)'),
 'AP-024':('BX-205','Perfis_BX_1-1.pdf','','informado pelo cliente (vetor)'),'AP-027':('BX-223','Perfis_BX_1-1.pdf','','informado pelo cliente (vetor)'),
 '39-144':('BX-316','Perfis_BX_1-1.pdf','','informado pelo cliente (vetor)'),'AP-029':('CB-266','CB-266_AP-056.pdf','','informado pelo cliente (vetor)'),
 'AP-056':('AP-056','CB-266_AP-056.pdf','','informado pelo cliente (vetor)'),'AP-057':('AP-056','CB-266_AP-056.pdf','','mesmo desenho do AP-056 (cliente)'),'STL-221':('STL-221','STL-221_AP-221.pdf','0,510','informado pelo cliente (vetor)'),'AP-6509':('AP-6509','muxarabi_1.pdf','','informado pelo cliente (vetor)'),'AP-6510':('AP-6510','muxarabi_1.pdf','','informado pelo cliente (vetor)')})
for r in o:
    if r[0]=='CM-067': r[6]='Achado (vetor)'; r[7],r[8],r[9],r[10],r[11]='Geral Hera',37,'MAC-0693','0,277','indicado pelo cliente (25/11)'
for r in o:
    if r[0] in _L16:
        c,f,pw,obs=_L16[r[0]]; r[6]='Achado (vetor)'; r[7],r[8],r[9],r[10],r[11]='PDF do cliente (25/11)',f,c,pw,obs
_PJ=json.load(open('/home/claude/alcoa/pend/jobs.json'))
for r in o:   # pendentes padronizados em 25/11: página conferida no desenho (rótulo principal)
    if r[0] in _PJ and r[7]==_PJ[r[0]]['cat']: r[8]=_PJ[r[0]]['pg']
    elif r[0] in _PJ and _PJ[r[0]]['cat']=='PDF do cliente (26/11)':   # desenho enviado pelo cliente em 26/11
        q=_PJ[r[0]]; r[6]='Achado (vetor)'; r[7],r[8],r[9],r[10],r[11]=q['cat'],1,q['cc'],q['peso'] or None,'desenho enviado pelo cliente'
    elif r[0] in _PJ and _PJ[r[0]]['cat']=='Geral ASA':   # BX: equivalente ASA (fabricante original), peso bate com o ERP
        q=_PJ[r[0]]; r[6]='Achado (vetor)'; r[7],r[8],r[9],r[10],r[11]='Geral ASA',q['pg'],q['cc'],q['peso'],'código equivalente (ASA)'
    elif r[0] in _PJ and _PJ[r[0]].get('manual') and r[7]!=_PJ[r[0]]['cat'] and r[0] in ('CG-080','CX-085','CL-009','CL-006'):   # 26/11: fornecedor informado pelo cliente
        q=_PJ[r[0]]; r[6]='Achado (vetor)'; r[7],r[8],r[9],r[10],r[11]=q['cat'],q['pg'],q['cc'],q['peso'],'fornecedor informado pelo cliente (planilha de pesos 26/11)'
_PV=json.load(open('/home/claude/catalogo/pesos-validados.json'))
o=[r+['Sim' if r[0] in _PAD else '',_PV.get(r[0],{}).get('peso_kg_m'),_PV.get(r[0],{}).get('obs')] for r in o]
C=collections.Counter
order=['Achado (vetor)','Achado (imagem)','Possível (conferir)','Tabelado (não precisa desenho individual)','Não achado']
wb=openpyxl.Workbook(); H=Font(bold=True,color='FFFFFF'); F=PatternFill('solid',fgColor='2F4396'); B=Font(bold=True)
def sheet(ws,head,rows,widths):
    ws.append(head)
    for c in ws[1]: c.font=H; c.fill=F
    for r in rows: ws.append(r)
    for i,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width=w
    ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
ws=wb.active; ws.title='Resumo'
ws.append(['Cruzamento: cadastro do site + ERP × desenhos dos catálogos (rev. 46, com ISA, Alumil, Império, Hyspex, Novaxx Luxxor 2.5, Maximus 20, Hera (geral), Alumax, Centenário, Binkafer, Mega 32 Lite, Euroshow, Tamboré, Sapa, Nylkit, Perfil Master, Stelman, Decamp, Específica 3.2 e códigos informados) — 25/11/2026']); ws['A1'].font=Font(bold=True,size=13,color='2F4396')
def bloco(t,cnt,keys=None):
    ws.append([]); ws.append([t,'Perfis']); [setattr(c,'font',B) for c in ws[ws.max_row]]
    for k,v in (((k,cnt[k]) for k in keys) if keys else cnt.most_common()): ws.append([k,v])
bloco('Situação do desenho (todos os códigos)',C(r[6] for r in o),order)
ws.append(['Total',len(o)])
bloco('Desenhos achados, por catálogo',C(r[7] for r in o if r[6].startswith('Achado')))
bloco('Origem do código',C('Site + ERP' if r[5]=='Sim' else 'Só no ERP' for r in o))
bloco('Faltando desenho × situação no ERP',C(r[13] for r in o if r[6]=='Não achado'))
bloco('Faltando desenho, por fornecedor (ERP)',C(r[14] or '(sem fornecedor)' for r in o if r[6]=='Não achado'))
ws.column_dimensions['A'].width=70
head=['Código Alplan','Código equivalente','Descrição','Código informado (Alplan)','Referenciado em (Alplan)','No cadastro do site','Situação do desenho','Catálogo','Página do PDF','Código no catálogo','Peso no catálogo (kg/m)','Achado pelo','No ERP','Situação no ERP','Fornecedor (ERP)','Cores cadastradas','Pronta entrega / encomenda por cor','Peso teórico ERP','Desenho recortado e cotas padronizadas','Peso validado pelo cliente (kg/m)','Fornecedor / observação do cliente']
full=sorted(o,key=lambda r:(order.index(r[6]),r[0]))
w=[14,16,38,16,20,10,34,18,9,14,12,16,8,10,40,22,40,10,14,12,40]
sheet(wb.create_sheet('Lista completa'),head,full,w)
falta=sorted([r for r in o if r[6]=='Não achado'],key=lambda r:(r[13]!='Ativo',r[14] or 'zz',r[0]))
sheet(wb.create_sheet('Faltando desenho'),head,falta,w)
def _f(v):
    try: return float(str(v).replace(',','.'))
    except Exception: return None
cp=[]
for r in o:
    pc=_f(r[10]); pe=_f(r[17])
    if r[6].startswith('Achado') and pc and pe and not (0.85 < (pe/6)/pc < 1.15):
        cp.append([r[0],r[2],r[7],r[9],pc,pe,round(pe/6,3),round(((pe/6)/pc-1)*100,1),r[14],r[13]])
cp.sort(key=lambda z:-abs(z[7]))
ws2=wb.create_sheet('Conferir peso no ERP')
sheet(ws2,['Código Alplan','Descrição','Catálogo','Código no catálogo','Peso no catálogo (kg/m)','Peso teórico ERP (kg por barra de 6 m)','ERP ÷ 6 (kg/m)','Diferença ERP × catálogo (%)','Fornecedor (ERP)','Situação no ERP'],cp,[14,34,30,18,14,16,12,14,40,10])
wb.save('cruzamento-perfis-desenhos.xlsx')
for r in ws.iter_rows(values_only=True):
    if r[0]: print(r)
