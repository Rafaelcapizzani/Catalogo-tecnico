import pymupdf as fitz, re, csv, sys
def norm(c):
    c=c.strip().upper().replace(' ','')
    c=re.sub(r'(\d)-([A-Z])$',r'\1\2',c)
    m=re.match(r'^([A-Z]{1,4})-?0*(\d+)([A-Z]?)$',c)
    if m: return f'{m.group(1)}{int(m.group(2))}{m.group(3)}'
    m=re.match(r'^(\d{2})-0*(\d+)$',c)
    if m: return f'{m.group(1)}-{int(m.group(2))}'
    return c
cats={'gradil.pdf':'Linha Gradil','portao.pdf':'Linha Portão','portao2.pdf':'Linha Portão II','integrada.pdf':'Suprema Integrada','gold3.pdf':'Gold III','gold4.pdf':'Gold IV','suprema.pdf':'Suprema','sp20.pdf':'SP20 Selta','asa.pdf':'Geral ASA','atlanta.pdf':'Belmetal Atlanta','stelman.pdf':'Geral Stelman','decamp.pdf':'Geral Decamp','standart.pdf':'Standart'}
codere=re.compile(r'\b([A-Z]{2}-\d{3}-?[A-Z](?![A-Z0-9])|20SP-\s?[A-Z]\d{2,3}[A-Z]?|SP[AIE]-\s?[A-Z]?\d{2,3}[A-Z]?|[A-Z]{1,2}\d{2}-\d{3}[A-Z]?|[A-Z]-\d{3,4}[A-Z]?|[A-Z]{2,3}\s?-?\s?\d{2,4}|\d{2}-\d{3})\b')
wt=re.compile(r'(\d+[.,]\d{2,3})\s*kg/m',re.I)
hw={'PAR','GUA','NYL','FEC','CHU','DOB','FRA','MAC','FIT','ROL','REB','PUX','SUP','TAM','ANC','ARR','BUC','CAN','POR','CB','FT','CON','BRA','PIV','HAS','ALA','EST','MAQ','KIT','REC','TRA','CAL','SKT','VZP','VZC','PRE','RBN','SIL','LIG','BT'}
inv={}
for f,name in cats.items():
    d=fitz.open(f)
    for i,p in enumerate(d):
        _t=p.get_text()
        if 'Cod. Per' in _t or 'ndice de Perfis' in _t or 'NDICE' in _t.upper(): continue
        lines=[l for l in _t.split('\n') if l.strip()]
        vec=len(p.get_drawings())>20
        pk=('kg/m' in p.get_text().lower()) and 'NDICE' not in p.get_text().upper()
        for j,l in enumerate(lines):
            for c in codere.findall(l):
                pre=re.match(r'[A-Z]+',c.replace(' ',''))
                if pre and pre.group(0) in hw: continue
                n=norm(c)
                w=wt.search(' '.join(lines[j:j+3]))
                key=n
                rec=inv.get(key)
                score=(2 if w else 0)+(1 if name!='Standart' else 0)+(4 if vec else 0)+(3 if pk else 0)
                LOW=('Geral Stelman','Geral Decamp')
                if rec is not None and name in LOW and rec['cat'] not in LOW: continue
                if rec is None or (score>rec['score'] and not (rec['cat'] not in LOW and name in LOW)) or (rec['cat'] in LOW and name not in LOW):
                    inv[key]={'cod':c.replace(' ',''),'cat':name,'pag':i+1,'peso':w.group(1) if w else '','vet':vec,'score':score}
import json as _j
for _c,(_w,_p) in _j.load(open('geral_idx.json')).items():
    _n=norm(_c)
    if _n not in inv or inv[_n]['cat'] in ('Standart','Geral Stelman','Geral Decamp'):
        inv[_n]={'cod':_c,'cat':'Geral Alcoa','pag':_p+11,'peso':_w,'vet':True,'score':9}
for _c,(_w,_p) in _j.load(open('asa_idx.json')).items():
    _n=norm(_c)
    if _n not in inv or inv[_n]['cat'] in ('Standart','Geral Stelman','Geral Decamp'):
        inv[_n]={'cod':_c,'cat':'Geral ASA','pag':_p,'peso':_w,'vet':True,'score':8}
for _e,(_c,_p,_w) in _j.load(open('asa_eq.json')).items():
    _n=norm(_e)
    if _n not in inv or inv[_n]['cat'] in ('Standart','Geral Stelman','Geral Decamp'):
        inv[_n]={'cod':f'{_c} (equiv. {_e})','cat':'Geral ASA','pag':_p,'peso':_w,'vet':True,'score':7}
_tn=_j.load(open('tera_novaxx.json'))
for _c,(_p,_w) in _tn['tera'].items():
    _n=norm(_c)
    if _n not in inv or inv[_n]['cat'] in ('Standart','Geral Stelman','Geral Decamp'):
        inv[_n]={'cod':_c,'cat':'Geral Tera (OCR)','pag':_p,'peso':_w,'vet':True,'score':6}
for _c,(_p,_w) in _tn['nx'].items():
    _n=norm(_c)
    if _n not in inv: inv[_n]={'cod':_c,'cat':'Geral Novaxx (OCR)','pag':_p,'peso':_w,'vet':True,'score':6}
for _e,(_c,_p) in _tn['nxeq'].items():
    _n=norm(_e)
    if _n not in inv or inv[_n]['cat'] in ('Standart','Geral Stelman','Geral Decamp'):
        inv[_n]={'cod':f'{_c} (equiv. {_e})','cat':'Geral Novaxx (OCR)','pag':_p,'peso':_tn['nx'].get(_c,('',''))[1],'vet':True,'score':5}
for _c,_p in _j.load(open('especifica.json')).items():
    _n=norm(_c)
    if _n not in inv: inv[_n]={'cod':_c,'cat':'Específica 3.2 (OCR)','pag':_p,'peso':'','vet':True,'score':6}
for _k in list(inv):
    _b=re.sub(r'([0-9])[A-Z]$',r'\1',_k)
    if _b!=_k and _b not in inv: inv[_b]=inv[_k]
sup="25-548 CL-006 CL-009 CL-010 CL-011 CM-004 CM-006 CM-007 CM-013 CM-014 CM-060 CM-098 CM-099 CM-110 CM-111 CM-113 CM-126 CM-125 CM-130 CM-151 CM-169 CM-175 CM-200 CX-1226 ME-013 ME-092 MN-014 MP-347 TQ-006 US-285 US-294 VZ-006 VZ-051".split()
sup+=['SU-%03d'%n for n in [1,2,3,4,5,6,7,9,10,11,12,13,14,18,19,24,25,26,28,29,30,36,39,40,41,42,44,47,49,50,53,55,56,57,58,60,61,68,69,70,71,72,73,74,79,80,81,82,84,85,86,88,90,91,93,94,96,97,98,99,100,101,102,103,107,108,110,111,120,121,122,123,186,187,188,200,203,225,226,227,228,230,238,239,241,242,243,245,250,251,260,271,272,276,279,280,289,290,291,292]]
supset={norm(c) for c in sup}
tab=('barra chata','cantoneira','tubo redondo','tubo quadrado','tubo retangular','vergalhao','perfil "t"','perfil "u"')
rows=list(csv.reader(open('itens.csv',encoding='utf-8-sig'),delimiter=';'))[1:]
seen=set(); out=[]
for r in rows:
    if len(r)<3: continue
    a,c,desc=[x.strip() for x in r[:3]]
    if a in seen: continue
    seen.add(a)
    na,nc=norm(a),norm(c)
    istab=any(desc.lower().startswith(t) for t in tab)
    hit=None
    for k,via in ((na,'código Alplan'),(nc,'código equivalente')):
        if k in inv and inv[k]['cat']!='Standart': hit=(inv[k],via,k); break
    if istab:
        out.append([a,c,desc,'Tabelado (não precisa desenho individual)','','','','',''])
    elif hit:
        h=hit[0]; st='Achado (vetor)' if h['vet'] else 'Achado'
        out.append([a,c,desc,st,h['cat'],h['pag'],h['cod'],h['peso'],hit[1]])
    elif istab:
        out.append([a,c,desc,'Tabelado (não precisa desenho individual)','','','','',''])
    elif False:
        k=na if na in supset else nc
        out.append([a,c,desc,'Está na Suprema — falta o PDF original','Suprema','','',' ','código Alplan' if na in supset else 'código equivalente'])
    else:
        out.append([a,c,desc,'Não achado','','','','',''])
import collections
print(collections.Counter(o[3] for o in out), len(out))
import json; json.dump(out,open('cruzamento.json','w'),ensure_ascii=False)
