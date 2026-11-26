import fitz,re
def lines(p):
    out=[]
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines',[]):
            t=''.join(s['text'] for s in l['spans']).strip()
            if t: out.append((t,fitz.Rect(l['bbox'])))
    return out
def peso(p,code_rx):
    L=lines(p); res=[]
    for t,r in L:
        if re.search(code_rx,t):
            best=None
            for t2,r2 in L:
                m=re.search(r'(\d+[,.]\d+)\s*k?g',t2,re.I)
                if m and r2!=r:
                    dx=abs((r2.x0+r2.x1)/2-(r.x0+r.x1)/2); dy=abs((r2.y0+r2.y1)/2-(r.y0+r.y1)/2)
                    if dy<40 and dx<120:
                        dd=dx+dy*2
                        if best is None or dd<best[0]: best=(dd,m[1])
            res.append((t,best[1] if best else ''))
    return res
