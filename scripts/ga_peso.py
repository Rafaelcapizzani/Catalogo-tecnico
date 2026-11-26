import sys,json,re;sys.path.insert(0,'/home/claude')
import pymupdf as fitz, dig_alcoa as A, ga_seg as G
J=json.load(open('/home/claude/alcoa/ga/jobs.json')); D=fitz.open('/home/claude/alcoa/geral.pdf')
out={};dif=[]
for k,j in J.items():
    page=D[j['pdf']-1]
    an=[a for a in G.analisa(j['pdf']) if not a.get('vazio') and tuple(a['clip'])==tuple(j['clip'])]
    lr=None
    if an:
        lr=fitz.Rect(an[0]['labs'][0]['rect'])
    if lr is None: out[k]=None; continue
    lr=lr+(-2,-2,2,2)
    rs=[(t,r) for t,r,h,s in A.ler(page,lr) if h is False]
    rs.sort(key=lambda z:-z[1].y0)
    w=next((t for t,r in rs if re.match(r'^\d\.\d{3}$',t)),None)
    out[k]=w
    if w is None or w.replace('.',',')!=j['peso']: dif.append((k,j['peso'],w,[t for t,r in rs]))
json.dump(out,open('/home/claude/alcoa/ga/peso_lido.json','w'))
print(len(dif)); [print(d) for d in dif]
