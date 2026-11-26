import pymupdf as fitz, numpy as np, cv2
def cells(page, dpi=100):
    pix=page.get_pixmap(dpi=dpi,colorspace=fitz.csGRAY)
    g=np.frombuffer(pix.samples,np.uint8).reshape(pix.h,pix.w)
    b=(g<160).astype(np.uint8)
    kh=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(int(dpi*2.2),1)))
    kv=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,int(dpi*2.2))))
    lines=cv2.dilate(kh|kv,np.ones((3,3),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats((1-lines).astype(np.uint8),connectivity=4)
    s=72/dpi; out=[]
    for i in range(1,n):
        x,y,w,h,a=st[i]
        if x==0 or y==0 or x+w>=pix.w or y+h>=pix.h: continue
        if w*s<120 or h*s<90: continue
        out.append(fitz.Rect(x*s,y*s,(x+w)*s,(y+h)*s))
    out.sort(key=lambda r:(round(r.y0/20),r.x0))
    return out
if __name__=='__main__':
    import sys
    d=fitz.open('/home/claude/alcoa/geral.pdf')
    for p in map(int,sys.argv[1:]): print(p,[tuple(round(v) for v in r) for r in cells(d[p-1])])
