import sys,json,re,os
sys.path.insert(0,'/home/claude')
import pymupdf as fitz, numpy as np, cv2, cotas as C
OUT='/home/claude/alcoa/folhas'
MAP={'AP-1818':'AP-1718'}
S=72/150
jobs={}
for f in ('folha01','folha02','folha03'):
    src=f'/home/claude/alcoa/upf/{f}.pdf'; p=fitz.open(src)[0]
    labs=[(''.join(s['text'] for s in l['spans']).strip(),fitz.Rect(l['bbox'])) for b in p.get_text('dict')['blocks'] if b['type']==0 for l in b['lines']]
    pm=p.get_pixmap(dpi=150,colorspace=fitz.csGRAY); g=np.frombuffer(pm.samples,np.uint8).reshape(pm.height,pm.width).copy()
    for t,r in labs: g[int(r.y0/S)-2:int(r.y1/S)+3,int(r.x0/S)-2:int(r.x1/S)+3]=255
    m=(g<200).astype(np.uint8); gm=cv2.dilate(m,np.ones((25,25),np.uint8))
    n,l,st,_=cv2.connectedComponentsWithStats(gm,8)
    comps=[fitz.Rect(x*S,y*S,(x+w)*S,(y+h)*S) for x,y,w,h,a in st[1:] if w*S>15 and h*S>15]
    def dist(a,b):
        dx=max(0,a.x0-b.x1,b.x0-a.x1); dy=max(0,a.y0-b.y1,b.y0-a.y1); return (dx*dx+dy*dy)**.5
    for t,r in labs:
        c=min(comps,key=lambda c:dist(c,r))
        jobs[MAP.get(t,t)]=dict(src=src,clip=tuple(c+(-2,-2,2,2)),lab=t)
json.dump(jobs,open(f'{OUT}/jobs.json','w'),indent=0)
for k,v in jobs.items(): print(k,[round(x) for x in v['clip']])
