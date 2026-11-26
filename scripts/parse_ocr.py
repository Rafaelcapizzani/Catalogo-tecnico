import csv, re, json, glob, collections
def toks(f):
    R=[r for r in csv.DictReader(open(f),delimiter='\t',quoting=csv.QUOTE_NONE) if (r.get('text') or '').strip()]
    return [dict(t=r['text'].strip(),x=int(r['left']),y=int(r['top']),w=int(r['width']),h=int(r['height']),b=(r['block_num'],r['par_num'],r['line_num'])) for r in R]
# ---- Tera
tera={}
for f in glob.glob('ocr2_tera/*.tsv'):
    pg=int(re.search(r'p(\d+)',f).group(1)); T=toks(f)
    for t in T:
        s=t['t']
        m=re.fullmatch(r'([A-Z1]{1,3})-(\d{3,4})(/[A-Z])?',s)
        if not m: continue
        pre=m.group(1); pre='I' if pre=='1' else pre.replace('1','I')
        code=f"{pre}-{m.group(2)}{(m.group(3) or '').replace('/','')}"
        cx=t['x']+t['w']/2
        wt=[u for u in T if re.fullmatch(r'\d+,\d{3}',u['t']) and 0<u['y']-t['y']<120 and abs(u['x']-t['x'])<250]
        w=min(wt,key=lambda u:u['y'])['t'] if wt else ''
        tera.setdefault(code,(pg,w))
print('tera',len(tera),list(tera.items())[:8])
# ---- Novaxx
nx={}; eq={}
for f in glob.glob('ocr2_novaxx/*.tsv'):
    pg=int(re.search(r'p(\d+)',f).group(1)); T=toks(f)
    lines=collections.defaultdict(list)
    for t in T: lines[t['b']].append(t)
    heads=[]; eqs=[]
    for L in lines.values():
        L.sort(key=lambda t:t['x']); s=' '.join(t['t'] for t in L)
        for m in re.finditer(r'NX[- ]?(\d{3,4})',s):
            heads.append(dict(code='NX-'+m.group(1).zfill(4),x=L[0]['x'],y=L[0]['y']))
        for i,t in enumerate(L):
            if re.fullmatch(r'\d{5}',t['t']): eqs.append(dict(c=t['t'][:2]+'-'+t['t'][2:],x=t['x'],y=t['y']))
            if re.fullmatch(r'[A-Z]{1,3}',t['t']) and t['t'] not in ('NX','KG','LINHA') and i+1<len(L) and re.fullmatch(r'\d{3,4}',L[i+1]['t']) and L[i+1]['x']-t['x']<200:
                eqs.append(dict(c=t['t']+'-'+L[i+1]['t'],x=t['x'],y=t['y']))
    for h in heads:
        w=[t for t in T if re.fullmatch(r'\d+,\d{3}',t['t']) and 0<t['y']-h['y']<120 and abs(t['x']-h['x'])<150]
        nx.setdefault(h['code'],(pg,w[0]['t'] if w else ''))
    W=max([t['x']+t['w'] for t in T] or [2480])
    for e in eqs:
        side=lambda x: x<W*0.5
        cand=[h for h in heads if h['y']<e['y'] and (side(h['x'])==side(e['x']) or e['x']>W*0.75)]
        if not cand: continue
        h=max(cand,key=lambda h:h['y'])
        if e['y']-h['y']>1400: continue
        eq.setdefault(e['c'],(h['code'],pg))
print('novaxx codes',len(nx),'equivalencias',len(eq),list(eq.items())[:12])
json.dump({'tera':tera,'nx':nx,'nxeq':eq},open('tera_novaxx.json','w'))
