import pymupdf as fitz, numpy as np, cv2
DPI=300; TH=215
NW,NH=16,24
def render(page,clip):
    pm=page.get_pixmap(dpi=DPI,clip=clip,colorspace=fitz.csGRAY)
    return np.frombuffer(pm.samples,np.uint8).reshape(pm.height,pm.width)
def comps(g):
    b=(g<TH).astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(b,8)
    return b,lab,st,n
def isdig(w,h): return 20<=h<=52 and 4<=w<=44 and w<=1.1*h
def isdot(w,h,a): return w<=8 and h<=8 and a>=3
def norm(mask):
    ys,xs=np.nonzero(mask)
    m=mask[ys.min():ys.max()+1,xs.min():xs.max()+1].astype(np.float32)
    return cv2.resize(m,(NW,NH),interpolation=cv2.INTER_AREA).flatten(), m.shape[1]/m.shape[0]
def groups(st,n,vert):
    c=[]
    for i in range(1,n):
        x,y,w,h,a=st[i]
        if vert: w,h=h,w
        if isdig(w,h): c.append(i)
    used=set(); out=[]
    for i in c:
        if i in used: continue
        g=[i]; used.add(i); ch=True
        while ch:
            ch=False
            for j in c:
                if j in used: continue
                for e in g:
                    X=st[e];Y=st[j]
                    if not vert:
                        ok=abs((X[1]+X[3]/2)-(Y[1]+Y[3]/2))<6 and abs(X[3]-Y[3])<6 and (Y[0]-(X[0]+X[2]))<16 and (X[0]-(Y[0]+Y[2]))<16
                    else:
                        ok=abs((X[0]+X[2]/2)-(Y[0]+Y[2]/2))<6 and abs(X[2]-Y[2])<6 and (Y[1]-(X[1]+X[3]))<16 and (X[1]-(Y[1]+Y[3]))<16
                    if ok: g.append(j); used.add(j); ch=True; break
        out.append(g)
    return out

# ---------- classificador (kNN sobre amostras rotuladas por cluster) ----------
import json as _json, os as _os
_MODEL='/home/claude/dig_alcoa_model.npz'
_M=None
def _model():
    global _M
    if _M is None:
        z=np.load(_MODEL); _M=(z['X'],z['y'])
    return _M
def classify(mask):
    f,ar=norm(mask); v=np.append(f,ar*2)
    X,y=_model(); d=np.linalg.norm(X-v,axis=1); o=np.argsort(d)[:5]
    lab=[y[i] for i in o]; best=max(set(lab),key=lab.count)
    return best, float(np.mean([d[i] for i in o if y[i]==best]))
def _rot(mask,how):
    if how=='up': return np.rot90(mask,-1)   # texto de baixo p/ cima -> gira horário
    if how=='down': return np.rot90(mask,1)
    return mask
DMAX=3.5
def ler(page,clip):
    g=render(page,clip); b,lab,st,n=comps(g); k=72/DPI
    res=[]
    dots=[i for i in range(1,n) if st[i][2]<=12 and st[i][3]<=12 and st[i][4]>=3]
    for vert in (False,True):
        for grp in groups(st,n,vert):
            opts=['up','down'] if vert else [False]
            if len(grp)==1: opts=[False,'up','down']
            best=None
            for how in opts:
                ax=(lambda i:st[i][0]) if not how else ((lambda i:-st[i][1]) if how=='up' else (lambda i:st[i][1]))
                gg=sorted(grp,key=ax)
                sub=lab[min(st[i][1] for i in gg):max(st[i][1]+st[i][3] for i in gg),min(st[i][0] for i in gg):max(st[i][0]+st[i][2] for i in gg)]
                cl=[classify(_rot((lab==i)[st[i][1]:st[i][1]+st[i][3],st[i][0]:st[i][0]+st[i][2]],how)) for i in gg]
                if any(c[0]=='X' for c in cl): sc=99
                else: sc=float(np.mean([c[1] for c in cl]))
                if best is None or sc<best[0]: best=(sc,how,gg,cl)
            sc,how,gg,cl=best
            if sc>DMAX:
                if sc>=99 or len(grp)<2: continue
                import cotas as _C
                from PIL import Image as _I
                gg=sorted(grp,key=lambda i:st[i][0])
                X0=min(st[i][0] for i in gg)-4;Y0=min(st[i][1] for i in gg)-4;X1=max(st[i][0]+st[i][2] for i in gg)+4;Y1=max(st[i][1]+st[i][3] for i in gg)+4
                crop=255-255*cv2.dilate(b[max(0,Y0-6):Y1+6,max(0,X0-6):X1+6],np.ones((2,2),np.uint8))
                crop=np.pad(crop.astype(np.uint8),20,constant_values=255)
                _C.SHEAR=0.2; t_,c_=_C._ocr1(_I.fromarray(crop)); _C.SHEAR=0.0
                import re as _re
                if not (_re.match(r'^\d{1,4}([.,]\d{1,2})?$',t_) and c_>60): continue
                ws_=[st[i][2] for i in gg]
                if '.' not in t_ and len(t_)==len(gg) and len(gg)>=2 and ws_[-1]>1.15*sorted(ws_[:-1])[len(ws_[:-1])//2] and ws_[-1]>26: t_=t_[:-1]+'.'+t_[-1]
                res.append((t_,fitz.Rect(clip.x0+X0*k,clip.y0+Y0*k,clip.x0+X1*k,clip.y0+Y1*k),False,sc)); continue
            if len(grp)==1 and vert: continue   # singletons tratados só na passada horizontal
            # rótulo de peça (ex.: 25-560): hífen entre algarismos -> não é cota
            if not how and len(gg)>=2:
                yy0=min(st[i][1] for i in gg); yy1=max(st[i][1]+st[i][3] for i in gg)
                hif=[q for q in range(1,n) if 6<=st[q][2]<=18 and st[q][3]<=5 and yy0+(yy1-yy0)*0.3<st[q][1]<yy1-(yy1-yy0)*0.25 and min(st[i][0] for i in gg)<st[q][0]<max(st[i][0] for i in gg)]
                if hif: continue
            t=''.join(c[0] for c in cl)
            x0=min(st[i][0] for i in gg); y0=min(st[i][1] for i in gg); x1=max(st[i][0]+st[i][2] for i in gg); y1=max(st[i][1]+st[i][3] for i in gg)
            # ponto decimal
            for dI in dots:
                dx,dy=st[dI][0]+st[dI][2]/2, st[dI][1]+st[dI][3]/2
                if not (x0-4<=dx<=x1+4 and y0-4<=dy<=y1+4): continue
                if not how: pos=sum(1 for i in gg if st[i][0]+st[i][2]/2<dx)
                elif how=='up': pos=sum(1 for i in gg if st[i][1]+st[i][3]/2>dy)
                else: pos=sum(1 for i in gg if st[i][1]+st[i][3]/2<dy)
                if 0<pos<len(gg) and '.' not in t:
                    t=t[:pos]+'.'+t[pos:]
                    x0=min(x0,st[dI][0]);y0=min(y0,st[dI][1]);x1=max(x1,st[dI][0]+st[dI][2]);y1=max(y1,st[dI][1]+st[dI][3])
            res.append((t,fitz.Rect(clip.x0+x0*k,clip.y0+y0*k,clip.x0+x1*k,clip.y0+y1*k),how,sc))
    # junta "28 . 3" (ponto afastado)
    mud=True
    while mud:
        mud=False
        hz=[z for z in res if z[2] is False and '.' not in z[0]]
        for a in hz:
            for bb in hz:
                if a is bb: continue
                h=a[1].height
                if abs((a[1].y0+a[1].y1)/2-(bb[1].y0+bb[1].y1)/2)<0.3*h and 0<bb[1].x0-a[1].x1<1.4*h and len(bb[0])<=2:
                    dd=[q for q in dots if a[1].x1<clip.x0+(st[q][0]+st[q][2]/2)*k<bb[1].x0 and a[1].y1-0.45*h<clip.y0+(st[q][1]+st[q][3]/2)*k<a[1].y1+0.15*h]
                    if dd:
                        res.remove(a); res.remove(bb); res.append((a[0]+'.'+bb[0],a[1]|bb[1],False,max(a[3],bb[3]))); mud=True; break
            if mud: break
    return res
