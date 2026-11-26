import pymupdf as fitz, pytesseract, io, json, re, sys
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
SRC='/home/claude/alcoa/tera.pdf'
def one(i):
    d=fitz.open(SRC); p=d[i]; Z=200/72
    pm=p.get_pixmap(dpi=200,colorspace=fitz.csGRAY); im=Image.open(io.BytesIO(pm.tobytes('png')))
    D=pytesseract.image_to_data(im,config='--psm 11',output_type=pytesseract.Output.DICT)
    W=[(t.strip(),D['left'][k]/Z,D['top'][k]/Z,(D['left'][k]+D['width'][k])/Z,(D['top'][k]+D['height'][k])/Z) for k,t in enumerate(D['text']) if t.strip()]
    out=[]
    for t,x0,y0,x1,y1 in W:
        u=t.upper().replace('—','-')
        if re.match(r'^[A-Z]{1,4}-?[0-9O]{2,5}[A-Z]?$',u):
            # rótulo principal: tem "Kg/m" logo abaixo
            kg=any('kg' in q[0].lower() and 0<q[2]-y1<18 and abs(q[1]-x0)<60 for q in W)
            out.append((u,round(x0,1),round(y0,1),round(x1,1),round(y1,1),kg))
    return i,out
if __name__=='__main__':
    n=fitz.open(SRC).page_count
    with ProcessPoolExecutor(4) as ex: R=dict(ex.map(one,range(n)))
    json.dump(R,open('/home/claude/alcoa/pend/tera_idx.json','w'))
    print('ok',n)
