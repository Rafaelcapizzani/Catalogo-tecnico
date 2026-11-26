import pymupdf as fitz, subprocess, os, sys, numpy as np, cv2
from concurrent.futures import ThreadPoolExecutor
d=fitz.open('/home/claude/alcoa/geral.pdf'); od='/home/claude/alcoa/ga/ocr'; os.makedirs(od,exist_ok=True)
def run(i):
    out=f'{od}/p{i+1}.tsv'
    pix=d[i].get_pixmap(dpi=300,colorspace=fitz.csGRAY)
    g=np.frombuffer(pix.samples,np.uint8).reshape(pix.h,pix.w)
    b=(g<215).astype(np.uint8)
    b=cv2.dilate(b,np.ones((3,3),np.uint8),iterations=1)
    png=f'{od}/p{i+1}.png'; cv2.imwrite(png,255-255*b)
    r=subprocess.run(['tesseract',png,'-','--psm','11','tsv'],capture_output=True,text=True)
    open(out,'w').write(r.stdout); os.remove(png)
pages=sorted(set(int(x) for x in sys.argv[1:]))
with ThreadPoolExecutor(4) as ex: list(ex.map(run,[p-1 for p in pages if 0<p<=len(d)]))
